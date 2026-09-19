"""Bounded loading-only entry for the declared VMem/official-ft-mse variant.

No initialize/turn/sample/encode/decode is called. Reuses the pinned S35 factory
with one gate-import change and explicit evidence labels, checked by AST reversal.
The unchanged S35 process-tree termination helper supervises one fresh worker.
"""
from __future__ import annotations
import argparse
import ast
import copy
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import traceback

import s39_variant_gate as gate_api

HERE, ROOT, S35 = gate_api.HERE, gate_api.ROOT, gate_api.S35
require, sha = gate_api.require, gate_api.sha
LABELS = {
    'LOADING_REAL_COMPONENTS': 'LOADING_DECLARED_COMPONENT_VARIANT',
    'PASS_ORIGINAL_COMPONENT_LOADING_ONLY': 'LOADED_PENDING_VARIANT_INVARIANT_CHECKS',
    'original_vae_local_directory': 'declared_official_ft_mse_local_directory',
    'recorded_execution': 'recorded_component_variant_loading',
}


def utc():
    return datetime.now(timezone.utc).isoformat()


def write_new(path, payload):
    with Path(path).open('x') as h:
        json.dump(payload, h, ensure_ascii=False, indent=2, allow_nan=False); h.write('\n')
        h.flush(); os.fsync(h.fileno())


def derive_factory():
    path = S35/'runtime_factory.py'
    require(sha(path) == gate_api.FACTORY_SHA, 'Factory source changed')
    original = ast.parse(path.read_text(), filename=str(path))
    derived = copy.deepcopy(original)
    counts = {x: 0 for x in LABELS}; imports = 0
    for node in ast.walk(derived):
        if isinstance(node, ast.ImportFrom) and node.module == 'resource_gate':
            require([(x.name, x.asname) for x in node.names] == [('validate_gate', None), ('require', None)],
                    'Unexpected original gate import')
            node.module = 's39_variant_gate'; imports += 1
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in LABELS:
            counts[node.value] += 1; node.value = LABELS[node.value]
    require(imports == 1 and all(n == 1 for n in counts.values()), 'Unexpected factory derivation domain')
    restored = copy.deepcopy(derived); inverse = {v:k for k,v in LABELS.items()}
    for node in ast.walk(restored):
        if isinstance(node, ast.ImportFrom) and node.module == 's39_variant_gate':
            node.module = 'resource_gate'
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in inverse:
            node.value = inverse[node.value]
    require(ast.dump(restored, include_attributes=False) == ast.dump(original, include_attributes=False),
            'Changes beyond the reviewed gate/label edits')
    namespace = dict(__file__=str(path), __name__='_s39_derived_runtime_factory')
    exec(compile(derived, str(path)+'[S39 declared gate/labels]', 'exec'), namespace)
    return namespace['create_runtime'], dict(parent_sha256=gate_api.FACTORY_SHA,
        gate_import_changes=imports, label_changes=counts, restored_ast_equal=True,
        scientific_operations_changed=False)


def load_termination_helper():
    path = S35/'launch_original.py'
    require(sha(path) == gate_api.LAUNCHER_SHA, 'Pinned process supervisor helper changed')
    spec = importlib.util.spec_from_file_location('_s39_s35_termination', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module.kill_tree


def worker(args):
    execution = Path(args.execution_directory).resolve()
    record = dict(schema='s39-variant-loading-worker-v1', status='CHECKING_FULL_RESOURCE_IDENTITIES',
        started_utc=utc(), variant=gate_api.VARIANT, manifest_sha256=args.manifest_sha256,
        source_sha256=sha(__file__), generation_calls=0, encode_decode_calls_requested=0,
        runtime_factory_calls=0, scientific_quality='NOT_EVALUATED')
    phase = 'resource_gate'; loading_path = None
    try:
        ticket = json.loads((execution/'launch_ticket.json').read_text())
        require(ticket['parent_pid'] == os.getppid() and ticket['manifest_sha256'] == args.manifest_sha256
                and ticket['source_sha256'] == record['source_sha256'], 'Live supervised parent ticket required')
        require(Path(sys.prefix).resolve() == (ROOT/'.venv-cut3r').resolve(), 'Wrong scientific environment')
        gate = gate_api.check_manifest(args.manifest, args.manifest_sha256)
        write_new(execution/'full_resource_gate.json', gate)
        m = json.loads(Path(args.manifest).read_text())
        require(ticket['output_root'] == m['output_root'], 'Parent/worker output mismatch')
        phase = 'component_loading'
        factory, proof = derive_factory()
        write_new(execution/'factory_derivation.json', proof)
        loading_path = Path(m['output_root'])/'runtime_loading.json'
        record['runtime_factory_calls'] += 1
        runtime = factory(gate)
        phase = 'variant_invariants'
        # Attribute inspection only. No additional forward, codec call, or RNG sample.
        import diffusers
        vae = runtime['pipeline'].vae
        module = vae.module
        checks = dict(diffusers_version=diffusers.__version__, use_tiling=module.use_tiling,
                      use_slicing=module.use_slicing, sample_size=module.config.sample_size,
                      latent_channels=module.config.latent_channels, wrapper_chunk_size=vae.chunk_size,
                      wrapper_scale_factor=vae.scale_factor, wrapper_downsample=vae.downsample)
        require(checks == dict(diffusers_version='0.32.2', use_tiling=False, use_slicing=False,
                sample_size=256, latent_channels=4, wrapper_chunk_size=1,
                wrapper_scale_factor=0.18215, wrapper_downsample=8), 'Unexpected declared VAE compute path')
        gate_api.validate_gate(gate)
        loading = json.loads(loading_path.read_text())
        require(loading['status'] == 'LOADED_PENDING_VARIANT_INVARIANT_CHECKS', 'Factory did not finish loading')
        # Original CUT3R may catch a checked_state_load rejection and retry a
        # filtered checkpoint. Inspect every recorded attempt after it returns.
        state_loads = loading.get('state_dict_loads')
        record['state_dict_loads'] = state_loads  # Preserve all strict_requested values.
        require(isinstance(state_loads, list) and bool(state_loads), 'No actual state_dict load records')
        require(all(isinstance(item, dict) and item.get('missing_keys') == [] and
                    item.get('unexpected_keys') == [] and 'strict_requested' in item
                    for item in state_loads), 'At least one recorded state_dict load was incomplete')
        loading.update(status='PASS_DECLARED_VARIANT_COMPONENT_LOADING_ONLY', variant=gate_api.VARIANT,
                       variant_invariants=checks, codec_numerics_verified=False,
                       original_sd21_equivalence_verified=False, generation_completed=False)
        temp = loading_path.with_suffix('.s39.tmp')
        temp.write_text(json.dumps(loading, ensure_ascii=False, indent=2)+'\n'); temp.replace(loading_path)
        record.update(status='VARIANT_LOADING_RETURNED_PENDING_INDEPENDENT_REVIEW',
                      variant_invariants=checks, runtime_loading_sha256=sha(loading_path),
                      scope='Constructor/state_dict/eval/device checks only; no codec numeric or generation validation')
    except BaseException as exc:
        record.update(status='NOT_READY_BEFORE_COMPONENT_LOADING' if phase == 'resource_gate'
                      else 'FAILED_OR_PARTIAL_VARIANT_LOADING', phase=phase,
                      error_type=type(exc).__name__, error=str(exc), traceback=traceback.format_exc())
        if phase == 'variant_invariants' and loading_path is not None and loading_path.exists():
            # Preserve the returned factory evidence before recording a failed postcondition.
            write_new(execution/'returned_factory_receipt_before_failed_invariants.json',
                      json.loads(loading_path.read_text()))
    finally:
        record['completed_utc'] = utc(); record['source_unchanged_at_close'] = sha(__file__) == record['source_sha256']
        if not record['source_unchanged_at_close']: record['status'] = 'FAILED_SOURCE_CHANGED'
        write_new(execution/'worker_receipt.json', record)
    return 0 if record['status'] == 'VARIANT_LOADING_RETURNED_PENDING_INDEPENDENT_REVIEW' else 1


def parent(args):
    execution = Path(args.execution_directory).resolve(); execution.mkdir(parents=True, exist_ok=False)
    record = dict(schema='s39-variant-loading-launch-v1', started_utc=utc(), status='CHECKING_METADATA',
        variant=gate_api.VARIANT, manifest_sha256=args.manifest_sha256, source_sha256=sha(__file__),
        worker_spawned=False, loading_limits=gate_api.LIMITS, sampled_peak_process_tree_rss_bytes=0,
        scientific_quality='NOT_EVALUATED')
    process = None; tracked = {}; psutil = None; kill_tree = None; start = None
    try:
        metadata = gate_api.check_manifest(args.manifest, args.manifest_sha256, metadata_only=True)
        _, m = gate_api.read_manifest(args.manifest, args.manifest_sha256)
        output = Path(m['output_root'])
        require(not output.exists() and output.parent.is_dir(), 'Output must be fresh with an existing parent')
        require(execution != output and not execution.is_relative_to(output), 'External receipts must be separate')
        require(shutil.disk_usage(output.parent).free >= gate_api.LIMITS['minimum_free_bytes'], 'Insufficient disk')
        require(Path(gate_api.RUNTIME['python_executable']).is_file() and
                all(Path(p).is_dir() for p in gate_api.RUNTIME['pythonpath']), 'Missing runtime paths')
        write_new(execution/'metadata_gate.json', metadata)
        # All metadata, review bindings and local availability precede this import.
        sys.path[:0] = gate_api.RUNTIME['pythonpath']
        import psutil as psutil_module
        psutil = psutil_module; kill_tree = load_termination_helper()
        output.mkdir(exist_ok=False)
        env = os.environ.copy()
        env.update(PYTHONPATH=os.pathsep.join(gate_api.RUNTIME['pythonpath']), PYTHONDONTWRITEBYTECODE='1',
            OMP_NUM_THREADS='8', MKL_NUM_THREADS='8', OPENBLAS_NUM_THREADS='8', VECLIB_MAXIMUM_THREADS='8',
            NUMEXPR_NUM_THREADS='8', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
            HF_HUB_DISABLE_IMPLICIT_TOKEN='1', MPLBACKEND='Agg', KORNIA_CHECK_VERSION='0')
        command = [gate_api.RUNTIME['python_executable'], '-B', str(Path(__file__).resolve()), '--worker',
                   '--manifest', str(Path(args.manifest).resolve()), '--manifest-sha256', args.manifest_sha256,
                   '--execution-directory', str(execution)]
        write_new(execution/'launch_ticket.json', dict(parent_pid=os.getpid(), source_sha256=record['source_sha256'],
            manifest_sha256=args.manifest_sha256, output_root=str(output), created_utc=utc()))
        record['command'] = command
        with (execution/'stdout.txt').open('x') as so, (execution/'stderr.txt').open('x') as se, \
                (execution/'monitor.jsonl').open('x') as monitor:
            start = time.monotonic()
            process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=so, stderr=se, start_new_session=True)
            record.update(worker_spawned=True, worker_pid=process.pid)
            previous = start
            while True:
                rss = 0
                try:
                    p = psutil.Process(process.pid)
                    for q in [p]+p.children(recursive=True): tracked[(q.pid, q.create_time())] = q
                except psutil.NoSuchProcess:
                    pass
                for (pid, created), q in tracked.items():
                    try:
                        if q.is_running() and q.create_time() == created: rss += q.memory_info().rss
                    except psutil.NoSuchProcess:
                        pass
                now = time.monotonic(); elapsed = now-start; free = shutil.disk_usage(output).free
                record['sampled_peak_process_tree_rss_bytes'] = max(record['sampled_peak_process_tree_rss_bytes'], rss)
                record['maximum_poll_gap_seconds'] = max(record.get('maximum_poll_gap_seconds', 0), now-previous)
                previous = now
                monitor.write(json.dumps(dict(utc=utc(), elapsed_seconds=elapsed, rss_bytes=rss, disk_free_bytes=free))+'\n')
                monitor.flush(); os.fsync(monitor.fileno())
                reasons = []
                if elapsed > gate_api.LIMITS['seconds']: reasons.append('wall_time')
                if rss > gate_api.LIMITS['rss_bytes']: reasons.append('process_tree_rss')
                if free < gate_api.LIMITS['minimum_free_bytes']: reasons.append('disk_free')
                if reasons:
                    record['limit_exceeded'] = reasons; record['termination'] = kill_tree(process, tracked, psutil); break
                if process.poll() is not None: break
                time.sleep(gate_api.LIMITS['poll_seconds'])
        record['returncode'] = process.wait(timeout=2)
        living = []
        for (_, created), q in tracked.items():
            try:
                if q.is_running() and q.create_time() == created and q.status() != psutil.STATUS_ZOMBIE: living.append(q.pid)
            except psutil.NoSuchProcess:
                pass
        if living:
            record['unexpected_live_descendants'] = living; record['termination'] = kill_tree(process, tracked, psutil)
        wrpath = execution/'worker_receipt.json'; wr = json.loads(wrpath.read_text())
        require(wr['source_sha256'] == record['source_sha256'] and wr['manifest_sha256'] == args.manifest_sha256 and
                wr['variant'] == gate_api.VARIANT and wr['source_unchanged_at_close'], 'Worker binding differs')
        record['worker_receipt_sha256'] = sha(wrpath); record['worker_status'] = wr['status']
        ok = (record['returncode'] == 0 and 'limit_exceeded' not in record and 'unexpected_live_descendants' not in record
              and wr['status'] == 'VARIANT_LOADING_RETURNED_PENDING_INDEPENDENT_REVIEW')
        record['status'] = 'VARIANT_LOADING_RETURNED_PENDING_INDEPENDENT_REVIEW' if ok else 'FAILED_OR_PARTIAL_VARIANT_LOADING'
    except BaseException as exc:
        record.update(status='FAILED_OR_PARTIAL_VARIANT_LOADING' if record['worker_spawned'] else 'NOT_READY_BEFORE_SCIENTIFIC_IMPORT',
                      error_type=type(exc).__name__, error=str(exc), traceback=traceback.format_exc())
        if process is not None and psutil is not None and kill_tree is not None:
            record['termination'] = kill_tree(process, tracked, psutil); record['returncode'] = process.poll()
    finally:
        record['completed_utc'] = utc()
        if start is not None: record['elapsed_seconds_including_termination'] = time.monotonic()-start
        record['source_unchanged_at_close'] = sha(__file__) == record['source_sha256']
        if not record['source_unchanged_at_close']: record['status'] = 'FAILED_SOURCE_CHANGED'
        write_new(execution/'receipt.json', record)
    return 0 if record['status'] == 'VARIANT_LOADING_RETURNED_PENDING_INDEPENDENT_REVIEW' else 2


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', required=True); p.add_argument('--manifest-sha256', required=True)
    p.add_argument('--execution-directory', required=True); p.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = p.parse_args()
    def interrupted(signum, frame):
        raise KeyboardInterrupt('S39 loading received signal '+str(signum))
    signal.signal(signal.SIGTERM, interrupted); signal.signal(signal.SIGINT, interrupted)
    return worker(args) if args.worker else parent(args)


if __name__ == '__main__':
    sys.exit(main())
