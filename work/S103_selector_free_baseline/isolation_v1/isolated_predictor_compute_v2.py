#!/usr/bin/env python3
"""Run an offline predictor in a user/mount/PID/network namespace and a read whitelist.

No models or datasets are selected by this wrapper. It mounts only policy-listed
paths, creates a private /proc, drops capabilities, closes extra inherited file
descriptors, and execs the exact supplied command. Run on a compute node within
the existing persistent tmux -> Slurm launcher for actual GPU jobs.
"""
import argparse
import ctypes
import datetime as dt
import glob
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import socket
import subprocess
import sys
import tempfile

SYSTEM_READ = ('/usr', '/bin', '/sbin', '/lib', '/lib64')
BASE_DEVICES = ('/dev/null', '/dev/zero', '/dev/random', '/dev/urandom')

def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def checked(cmd):
    subprocess.run(cmd, check=True, stdin=subprocess.DEVNULL)

def resolve_policy(policy):
    if policy.get('schema') != 'gwm-predictor-isolation-v1':
        raise ValueError('unsupported policy schema')
    for name in ('predictor_inputs_sha256', 'scorer_inputs_sha256', 'runtime_binding_sha256'):
        if len(policy.get(name, '')) != 64:
            raise ValueError('missing binding: ' + name)
    readonly = []
    readwrite = []
    forbidden_roots = {'/', '/home', str(Path.home()), '/tmp', '/var', '/proc', '/dev', '/sys'}
    for key, target in (('readonly_paths', readonly), ('readwrite_paths', readwrite)):
        for value in policy.get(key, []):
            p = Path(value).resolve(strict=True)
            if str(p) in forbidden_roots:
                raise ValueError('overbroad mount: ' + str(p))
            target.append(p)
    denied = [Path(x).resolve(strict=True) for x in policy.get('denied_paths', [])]
    if not denied:
        raise ValueError('explicit denied outcome/archive probes required')
    for d in denied:
        for allowed in readonly + readwrite + [Path(x).resolve() for x in SYSTEM_READ]:
            if d == allowed or (allowed.is_dir() and d.is_relative_to(allowed)):
                raise ValueError('denied path lies inside allowed mount: ' + str(d))
    command = policy.get('command', [])
    if not command or not Path(command[0]).is_absolute():
        raise ValueError('command executable must be absolute')
    return readonly, readwrite, denied

def mount_into(root, source, readonly=True):
    source = Path(source)
    dest = root / str(source).lstrip('/')
    if source.is_dir():
        dest.mkdir(parents=True, exist_ok=True)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.touch(exist_ok=True)
    checked(['/usr/bin/mount', '--bind', str(source), str(dest)])
    if readonly:
        checked(['/usr/bin/mount', '-o', 'remount,bind,ro,nosuid,nodev', str(dest)])

def drop_capabilities():
    libc = ctypes.CDLL(None, use_errno=True)
    PR_CAPBSET_DROP, PR_SET_NO_NEW_PRIVS = 24, 38
    for cap in range(64):
        ret = libc.prctl(PR_CAPBSET_DROP, cap, 0, 0, 0)
        if ret != 0 and ctypes.get_errno() not in (22,):  # EINVAL beyond last kernel capability
            raise OSError(ctypes.get_errno(), 'cannot drop capability bounding set')
    class Header(ctypes.Structure):
        _fields_ = [('version', ctypes.c_uint32), ('pid', ctypes.c_int)]
    class Data(ctypes.Structure):
        _fields_ = [('effective', ctypes.c_uint32), ('permitted', ctypes.c_uint32), ('inheritable', ctypes.c_uint32)]
    header = Header(0x20080522, 0)
    data = (Data * 2)()
    if libc.capset(ctypes.byref(header), ctypes.byref(data)) != 0:
        raise OSError(ctypes.get_errno(), 'capset failed')
    if libc.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), 'no_new_privs failed')

def inner(policy, root):
    readonly, readwrite, denied = resolve_policy(policy)
    checked(['/usr/bin/mount', '--make-rprivate', '/'])
    checked(['/usr/bin/mount', '-t', 'tmpfs', '-o', 'nosuid,nodev,mode=755', 'tmpfs', str(root)])
    for name in SYSTEM_READ:
        if Path(name).exists():
            mount_into(root, name)
    for name in ('/etc/ld.so.cache', '/etc/ld.so.conf', '/etc/nsswitch.conf', '/etc/passwd', '/etc/group'):
        if Path(name).is_file():
            mount_into(root, name)
    for path in readonly:
        mount_into(root, path)
    for path in readwrite:
        mount_into(root, path, readonly=False)
    # Device files alone: no host /dev tree or host /proc is exposed.
    for name in BASE_DEVICES:
        if Path(name).exists():
            mount_into(root, name, readonly=False)
    if policy.get('allow_nvidia_devices'):
        for name in sorted(glob.glob('/dev/nvidia*')):
            mount_into(root, name, readonly=False)
        if policy.get('allow_sys_mount', False) and Path('/sys').is_dir():
            mount_into(root, '/sys')
    for name in ('proc', 'tmp', 'dev/shm'):
        (root / name).mkdir(parents=True, exist_ok=True)
    checked(['/usr/bin/mount', '-t', 'proc', '-o', 'nosuid,nodev,noexec', 'proc', str(root / 'proc')])
    checked(['/usr/bin/mount', '-t', 'tmpfs', '-o', 'nosuid,nodev,mode=1777', 'tmpfs', str(root / 'tmp')])
    checked(['/usr/bin/mount', '-t', 'tmpfs', '-o', 'nosuid,nodev,mode=1777', 'tmpfs', str(root / 'dev/shm')])
    (root / 'dev/fd').symlink_to('/proc/self/fd')
    # Close nonstandard descriptors before chroot; none can retain an outer directory.
    max_fd = resource.getrlimit(resource.RLIMIT_NOFILE)[0]
    os.closerange(3, min(max_fd if max_fd != resource.RLIM_INFINITY else 1048576, 1048576))
    os.chroot(root)
    os.chdir(policy.get('working_directory', '/'))
    drop_capabilities()
    env = {key: os.environ[key] for key in ('PATH', 'LANG', 'LC_ALL', 'CUDA_VISIBLE_DEVICES',
           'SLURM_JOB_ID', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS') if key in os.environ}
    env.update({'PYTHONDONTWRITEBYTECODE': '1', 'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1',
                'TMPDIR': '/tmp', 'HOME': '/tmp', 'NO_PROXY': '*', 'PYTHONNOUSERSITE': '1'})
    env.update(policy.get('environment', {}))
    os.write(2, (json.dumps({'event': 'ISOLATION_ENTERED', 'pid': os.getpid(),
                            'execution_boundary_id': policy['execution_boundary_id'],
                            'capabilities_dropped': True, 'private_proc': True,
                            'network_namespace': True}) + '\n').encode())
    os.execve(policy['command'][0], policy['command'], env)

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--policy', required=True)
    ap.add_argument('--receipt')
    ap.add_argument('--inner-root')
    args = ap.parse_args()
    policy_path = Path(args.policy).resolve()
    policy = json.loads(policy_path.read_text())
    resolve_policy(policy)
    if args.inner_root:
        inner(policy, Path(args.inner_root))
        return 99
    if not args.receipt:
        ap.error('--receipt is required for outer launch')
    started = now()
    wrapper = Path(__file__).resolve()
    root = Path(tempfile.mkdtemp(prefix='gwm-predictor-root-'))
    command = ['/usr/bin/unshare', '--user', '--map-root-user', '--mount', '--pid', '--net',
               '--fork', '--kill-child=SIGKILL', sys.executable, str(wrapper),
               '--policy', str(policy_path), '--inner-root', str(root)]
    try:
        result = subprocess.run(command, stdin=subprocess.DEVNULL, text=True, capture_output=True)
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        receipt = {'schema': 'gwm-isolation-launch-receipt-v1', 'scope': policy.get('scope'),
                   'execution_boundary_id': policy['execution_boundary_id'], 'started_at_utc': started,
                   'finished_at_utc': now(), 'hostname': socket.gethostname(), 'kernel': os.uname().release,
                   'slurm_job_id': os.environ.get('SLURM_JOB_ID'), 'method': 'linux_namespace',
                   'predictor_wrapper_sha256': sha(wrapper), 'policy_sha256': sha(policy_path),
                   'predictor_inputs_sha256': policy['predictor_inputs_sha256'],
                   'scorer_inputs_sha256': policy['scorer_inputs_sha256'],
                   'runtime_binding_sha256': policy['runtime_binding_sha256'],
                   'raw_command': command, 'exit_code': result.returncode,
                   'stdout': result.stdout, 'stderr': result.stderr,
                   'opens_real_model_or_data': False if policy.get('scope') == 'synthetic_fixture_login_node_only' else None,
                   'production_acceptance': False}
        Path(args.receipt).write_text(json.dumps(receipt, indent=2) + '\n')
        return result.returncode
    finally:
        # Namespace mounts disappear with child; the outer mountpoint stays empty.
        shutil.rmtree(root)

if __name__ == '__main__':
    raise SystemExit(main())
