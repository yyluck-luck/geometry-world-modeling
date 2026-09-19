"""Frozen bounded wheel acquisition/install; isolated import only, never a model.

Invoked only after root's explicit authorization. No writes to either old venv.
"""
from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
ENV = ROOT / 'work/S17C_environment'
WHEELS = ENV / 'wheelhouse'
OVERLAY = ENV / 'site-packages'
START = time.perf_counter()
UTC = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
REPORT = {'status': 'RUNNING', 'started_utc': UTC(), 'requests': [], 'wheels': [],
          'model_instantiations': 0, 'real_image_reads': 0, 'weight_reads': 0,
          'package_target': str(OVERLAY), 'network_response_bytes': 0}

def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def save(name, obj):
    (ENV / name).write_text(json.dumps(obj, indent=2) + '\n')

def tree_state(path):
    # File metadata, plus distribution metadata/bin hashes; not gigabytes of torch.
    rows, strong = [], {}
    for p in sorted(path.rglob('*')):
        if p.is_file() or p.is_symlink():
            rel = str(p.relative_to(path))
            if '__pycache__' in p.parts or p.suffix == '.pyc':
                continue
            s = p.lstat()
            rows.append([rel, s.st_size, s.st_mtime_ns, os.readlink(p) if p.is_symlink() else None])
            if not p.is_symlink() and (p.name in ('METADATA', 'RECORD', 'pyvenv.cfg') or p.parent.name == 'bin'):
                strong[rel] = sha(p)
    return {'path': str(path), 'files_count': len(rows),
            'file_metadata_sha256': hashlib.sha256(json.dumps(rows).encode()).hexdigest(),
            'distribution_and_executable_sha256': strong,
            'excludes': 'pyc/__pycache__ only; no claim of full source-byte hash'}

try:
    assert not ENV.exists(), 'New environment directory required; preserve any earlier attempt'
    ENV.mkdir()
    WHEELS.mkdir()
    plan = json.loads((HERE / 'overlay_wheel_plan.json').read_text())
    assert plan['wheel_count'] == 22 and plan['total_download_bytes'] == 29513889
    contract = {'schema': 's17c-isolated-overlay-acquisition-v1', 'created_utc': UTC(),
                'source_plan_sha256': sha(HERE / 'source_plan.json'),
                'wheel_plan_sha256': sha(HERE / 'overlay_wheel_plan.json'),
                'requirements_sha256': sha(HERE / 'overlay_requirements.txt'),
                'script_sha256': sha(__file__), 'expected_wheel_count': 22,
                'expected_wheel_bytes': 29513889, 'max_response_bytes': 104857600,
                'max_request_attempts': 60, 'max_attempts_per_wheel': 3,
                'wall_seconds': 600, 'package_target': str(OVERLAY),
                'python': sys.executable, 'plan': plan}
    save('access_contract.json', contract)
    prior = {str(p): tree_state(p) for p in [ROOT / '.venv-cut3r', ROOT / '.venv']}
    save('original_environment_before.json', prior)
    for wheel in plan['wheels']:
        assert time.perf_counter() - START < 600
        dest = WHEELS / wheel['filename']
        assert wheel['url'].startswith('https://files.pythonhosted.org/')
        for attempt in range(1, 4):
            assert len(REPORT['requests']) < 60
            part = WHEELS / (wheel['filename'] + f'.attempt{attempt}.part')
            start = time.perf_counter()
            process = subprocess.run(['curl', '--max-time', '25', '--connect-timeout', '12',
                '--max-filesize', str(wheel['bytes']), '--silent', '--show-error',
                '--output', str(part), '--write-out', '%{http_code}|%{size_download}|%{time_total}',
                wheel['url']], capture_output=True, text=True)
            fields = process.stdout.strip().split('|')
            got_bytes = int(float(fields[1])) if len(fields) == 3 else (part.stat().st_size if part.exists() else 0)
            REPORT['network_response_bytes'] += got_bytes
            entry = {'filename': wheel['filename'], 'attempt': attempt, 'url': wheel['url'],
                     'ended_utc': UTC(), 'curl_exit_code': process.returncode,
                     'http_code': fields[0] if fields else None, 'response_bytes': got_bytes,
                     'elapsed_seconds': time.perf_counter() - start, 'stderr': process.stderr}
            REPORT['requests'].append(entry)
            save('acquisition_progress.json', REPORT)
            assert REPORT['network_response_bytes'] <= 104857600 and time.perf_counter() - START < 600
            if process.returncode:
                if process.returncode in (18, 28, 35, 52, 55, 56) and attempt < 3:
                    continue
                raise RuntimeError('Wheel transport failed: ' + wheel['filename'])
            assert fields[0] == '200', 'Unexpected wheel HTTP status'
            assert part.stat().st_size == wheel['bytes'], 'Wheel byte size mismatch'
            assert sha(part) == wheel['sha256'], 'Wheel SHA mismatch'
            part.rename(dest)
            REPORT['wheels'].append({**wheel, 'local_path': str(dest), 'verified_utc': UTC()})
            break
    assert len(REPORT['wheels']) == 22
    remaining = max(1, int(600 - (time.perf_counter() - START)))
    install_env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PIP_DISABLE_PIP_VERSION_CHECK='1', PIP_NO_INDEX='1')
    command = [sys.executable, '-m', 'pip', 'install', '--no-index', '--no-deps', '--no-compile',
               '--require-hashes', '--only-binary=:all:', '--find-links', str(WHEELS),
               '--target', str(OVERLAY), '-r', str(HERE / 'overlay_requirements.txt')]
    process = subprocess.run(command, env=install_env, capture_output=True, text=True, timeout=remaining)
    (ENV / 'pip_install.stdout.txt').write_text(process.stdout)
    (ENV / 'pip_install.stderr.txt').write_text(process.stderr)
    REPORT['install'] = {'command': command, 'exit_code': process.returncode, 'ended_utc': UTC()}
    assert process.returncode == 0, 'Isolated install failed'
    after = {str(p): tree_state(p) for p in [ROOT / '.venv-cut3r', ROOT / '.venv']}
    save('original_environment_after.json', after)
    REPORT['original_environments_unchanged'] = after == prior
    assert after == prior, 'Original venv non-bytecode files or metadata changed'
    REPORT['status'] = 'OVERLAY_INSTALLED_PENDING_IMPORT_SMOKE'
except BaseException as exc:
    REPORT['status'] = 'FAILED'
    REPORT['failure'] = {'type': type(exc).__name__, 'message': str(exc), 'traceback': traceback.format_exc()}
finally:
    REPORT['ended_utc'] = UTC()
    REPORT['elapsed_seconds'] = time.perf_counter() - START
    if ENV.exists():
        save('install_receipt.json', REPORT)
    print(json.dumps({'status': REPORT['status'], 'wheel_count': len(REPORT['wheels']),
                      'response_bytes': REPORT['network_response_bytes'],
                      'elapsed_seconds': REPORT['elapsed_seconds'], 'failure': REPORT.get('failure')}))
