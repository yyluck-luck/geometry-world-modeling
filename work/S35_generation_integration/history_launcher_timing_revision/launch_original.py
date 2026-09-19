"""S35 bounded original-run launcher; preparation only until separately frozen.

The parent uses standard-library metadata checks before importing psutil. No
successful process exit, archive close, or trace close certifies generation.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
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

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PYTHON = ROOT / '.venv-cut3r/bin/python'
PYTHONPATH = [HERE, ROOT/'src', ROOT/'work/S20_environment/site-packages',
              ROOT/'work/S17C_environment/site-packages']
POLL_SECONDS = 0.5
BATCH_SECONDS = 1800.0
TOTAL_SECONDS = 3600.0
RSS_BYTES = 45 * 1024**3
MIN_FREE_BYTES = 10 * 1024**3


def utc():
    return datetime.now(timezone.utc).isoformat()


def require(ok, why):
    if not ok:
        raise RuntimeError(why)


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


def write_new(path, value):
    with Path(path).open('x') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())


def load_bound(path, identities):
    path = Path(path).resolve()
    require(identities.get(str(path)) == sha(path), 'Unbound or changed source: '+str(path))
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_frozen(path, expected):
    path = Path(path).resolve()
    require(path.is_file() and sha(path) == expected, 'Manifest missing or changed')
    m = json.loads(path.read_text())
    require(m.get('schema') == 's35-original-generation-run-v1' and
            m.get('status') == 'FROZEN_REAL_EXECUTION', 'A frozen real-run manifest is required')
    runtime = m.get('runtime', {})
    require(runtime.get('python_executable') == str(PYTHON), 'Only frozen original virtualenv is supported')
    require(runtime.get('pythonpath') == [str(p) for p in PYTHONPATH], 'Frozen import-path order differs')
    require(PYTHON.is_file() and all(p.is_dir() for p in PYTHONPATH), 'Original runtime paths unavailable')
    require(m.get('source_identities', {}).get(str(Path(__file__).resolve())) == sha(__file__),
            'Launcher source is not bound by the manifest')
    return m


class TraceBoundary:
    """Budget boundary from actual S20 hash-chained events, not stdout.

    This is deliberately not the scientific/offline full trace verifier. It
    does not decode arrays, validate model calls, or establish cache causality.
    """
    def __init__(self, path, manifest_sha256):
        self.path = Path(path)
        self.manifest_sha256 = manifest_sha256
        self.offset = 0
        self.pending = b''
        self.seq = 0
        self.previous = '0'*64
        self.batches = {}
        self.completed = []
        self.closed = False
        self.seen_failure = False

    def poll(self):
        if not self.path.exists():
            return
        require(self.path.stat().st_size >= self.offset, 'Trace was truncated')
        with self.path.open('rb') as handle:
            handle.seek(self.offset)
            chunk = handle.read()
            self.offset = handle.tell()
        lines = (self.pending+chunk).split(b'\n')
        self.pending = lines.pop()
        for line in lines:
            row = json.loads(line)
            digest = row.pop('sha256')
            require(row['schema'] == 's20-generation-trace-v1' and row['seq'] == self.seq
                    and row['previous_sha256'] == self.previous
                    and digest == hashlib.sha256(canonical(row)).hexdigest(), 'Trace boundary hash chain differs')
            require(row['evidence_kind'] == 'recorded_execution', 'Synthetic trace cannot start a real budget phase')
            event, bid, payload = row['event'], row['batch_id'], row['payload']
            require(not self.closed, 'Events after trace closure')
            if self.seq == 0:
                require(event == 'session' and payload['manifest_sha256'] == self.manifest_sha256,
                        'Trace session does not bind this launch manifest')
            if event == 'batch_begin':
                require(isinstance(bid, str) and bid and bid not in self.batches and len(self.batches) < 2,
                        'Unexpected batch identity/count')
                self.batches[bid] = {'ordinal':len(self.batches), 'map_history':None, 'retained':None}
            elif event == 'cache_commit':
                require(bid in self.batches, 'Cache boundary before batch begin')
                self.batches[bid]['retained'] = [x['frame_id'] for x in payload['retained']]
            elif event == 'map_commit':
                require(bid in self.batches, 'Map boundary before batch begin')
                self.batches[bid]['map_history'] = payload['history_length']
            elif event == 'batch_complete':
                require(bid in self.batches and bid not in [x['batch_id'] for x in self.completed],
                        'Unmatched/duplicate completed batch')
                item = self.batches[bid]
                ordinal = item['ordinal']
                ids = list(range(1+4*ordinal, 5+4*ordinal))
                require(ordinal == len(self.completed) and item['map_history'] == 5+4*ordinal
                        and item['retained'] == ids and payload['retained_frame_ids'] == ids,
                        'Original committed 1-to-5-to-9 boundary is absent')
                self.completed.append(dict(batch_id=bid, ordinal=ordinal, event_seq=self.seq,
                    event_sha256=digest, event_utc=row['utc'], retained_frame_ids=ids))
            elif event in ('failure', 'operation_failure'):
                self.seen_failure = True
            elif event == 'session_end':
                self.closed = True
            self.seq += 1
            self.previous = digest


def kill_tree(process, tracked, psutil):
    """Stop the fresh session plus known descendants; retain kill/wait evidence."""
    result = {'started_utc':utc(), 'actions':[], 'survivors':[]}
    try:
        parent = psutil.Process(process.pid)
        for p in [parent]+parent.children(recursive=True):
            tracked[(p.pid, p.create_time())] = p
    except psutil.NoSuchProcess:
        pass
    except psutil.Error as exc:
        result['actions'].append({'discovery_error':str(exc)})
    for sig, delay in ((signal.SIGTERM, 2.0), (signal.SIGKILL, 2.0)):
        deadline = time.monotonic()+delay
        try:
            os.killpg(process.pid, sig)
            result['actions'].append({'target':'worker_process_group', 'pgid':process.pid, 'signal':int(sig)})
        except ProcessLookupError:
            pass
        except OSError as exc:
            result['actions'].append({'killpg_error':str(exc), 'signal':int(sig)})
        live = []
        for (pid, created), p in list(tracked.items()):
            try:
                if p.is_running() and p.create_time() == created:
                    p.send_signal(sig)
                    if pid != process.pid:
                        live.append(p)
            except psutil.NoSuchProcess:
                pass
            except psutil.Error as exc:
                result['actions'].append({'pid':pid, 'signal':int(sig), 'error':str(exc)})
        # Only Popen reaps its direct child, preserving the actual signal/exit
        # code; psutil.wait_procs must not consume that waitpid result.
        _, alive = psutil.wait_procs(live, timeout=max(0, deadline-time.monotonic()))
        try:
            process.wait(timeout=max(0, deadline-time.monotonic()))
        except subprocess.TimeoutExpired:
            pass
        if not alive and process.poll() is not None:
            break
    for (pid, created), p in tracked.items():
        try:
            if p.is_running() and p.create_time() == created and p.status() != psutil.STATUS_ZOMBIE:
                result['survivors'].append({'pid':pid, 'created':created})
        except psutil.NoSuchProcess:
            pass
        except psutil.Error as exc:
            result['survivors'].append({'pid':pid, 'inspection_error':str(exc)})
    try:
        result['returncode'] = process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        result['wait_timeout'] = True
    result['completed_utc'] = utc()
    return result


def worker(args):
    execution = Path(args.execution_directory).resolve()
    record = dict(schema='s35-original-worker-v1', status='CHECKING_FULL_RESOURCE_IDENTITIES',
        started_utc=utc(), manifest_sha256=args.manifest_sha256, source_sha256=sha(__file__),
        scientific_status='NOT_EVALUATED', full_resource_checks=0, full_resource_checks_attempted=0,
        runtime_factory_calls=0)
    archive = None
    phase = 'full_resource_gate'
    try:
        ticket = json.loads((execution/'launch_ticket.json').read_text())
        require(ticket['parent_pid'] == os.getppid() and ticket['manifest_sha256']==args.manifest_sha256
                and ticket['launcher_sha256']==record['source_sha256'],
                'Internal worker requires its live original parent launch ticket')
        require(Path(sys.prefix).resolve() == (ROOT/'.venv-cut3r').resolve(), 'Worker is outside the frozen virtualenv')
        m = read_frozen(args.manifest, args.manifest_sha256)
        require(ticket['output_root']==m['output_root'], 'Worker output differs from launch ticket')
        gate_module = load_bound(HERE/'resource_gate.py', m['source_identities'])
        record['full_resource_checks_attempted'] = 1
        gate = gate_module.check_manifest(args.manifest, args.manifest_sha256)
        record['full_resource_checks'] = 1
        write_new(execution/'full_resource_gate.json', gate)
        # No scientific module, image or model import precedes the full gate.
        phase = 'load_prepared_modules'
        trace_module = load_bound(ROOT/'src/s20_generation_trace.py', m['source_identities'])
        archive_module = load_bound(HERE/'archive_outputs.py', m['source_identities'])
        runtime_module = load_bound(HERE/'runtime_factory.py', m['source_identities'])
        integration_module = load_bound(HERE/'integrate_original.py', m['source_identities'])
        output = Path(m['output_root'])
        source_manifest = dict(identities=m['source_identities'],
            pipeline_source=str(ROOT/'work/S20_environment/isolated_vmem_source/modeling/pipeline.py'))
        def create_trace(checked):
            gate_module.validate_gate(checked)
            return trace_module.TraceWriter(output/'trace', evidence_kind='recorded_execution',
                source_identities=m['source_identities'], manifest_sha256=args.manifest_sha256)
        def create_archive(checked):
            nonlocal archive
            gate_module.validate_gate(checked)
            archive = archive_module.FullOutputArchive(output/'archive', evidence_kind='recorded_execution',
                source_identities=m['source_identities'], manifest_sha256=args.manifest_sha256,
                required_events={'initial_input':1, 'initial_output':1, 'context_output':2,
                    'condition_input':2, 'condition_output':2, 'sampler_input':2, 'sampler_output':2,
                    'sample_output':2, 'cache_commit':2, 'geometry_output':2, 'map_commit':2,
                    'navigator_begin':3, 'navigator_return':3, 'integration_return':1})
            return archive
        def create_runtime(checked):
            record['runtime_factory_calls'] += 1
            require(record['runtime_factory_calls'] == 1, 'Never recreate runtime or retry a batch')
            return runtime_module.create_runtime(checked)
        phase = 'original_two_batch_route'
        result = integration_module.run_original(create_runtime, resource_gate=gate,
            check_resource_gate=gate_module.validate_gate, create_trace=create_trace,
            create_archive=create_archive, source_manifest=source_manifest, evidence_kind='recorded_execution')
        require(result['archive'] is archive and result['trace'].closed, 'Original route did not close its own trace')
        summary = result['observation_summary']
        require(summary['status']=='OBSERVED_ROUTE_RETURNED_NOT_QUALITY_VERIFIED', 'Unexpected route status')
        write_new(output/'observation_summary.json', summary)
        phase = 'archive_finalize'
        archive_receipt = archive.finalize(status='COMPLETE', metadata=dict(
            observation_summary_path=str(output/'observation_summary.json'),
            observation_summary_sha256=sha(output/'observation_summary.json'),
            scope='Caller returned; raw archive coverage only; independent scientific review pending'))
        gate_module.validate_gate(gate)  # Cheap stat/source rebind; no second weight hash.
        record.update(status='ORIGINAL_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW',
            archive_receipt=archive_receipt, observation_summary_sha256=sha(output/'observation_summary.json'),
            trace_events_sha256=sha(output/'trace/events.jsonl'),
            scope='Two original calls returned under observation; no independent raw-output or quality verification here')
    except BaseException as exc:
        record.update(status='NOT_READY_IN_WORKER_BEFORE_SCIENTIFIC_IMPORT' if phase=='full_resource_gate'
                      else 'FAILED_OR_PARTIAL_ORIGINAL_RUN', phase=phase,
                      error_type=type(exc).__name__, error=str(exc), traceback=traceback.format_exc())
        if archive is not None and not archive.closed:
            try:
                record['archive_failure_receipt'] = archive.fail(exc, phase=phase)
            except BaseException as secondary:
                record['archive_failure_closure_error'] = str(secondary)
    finally:
        record['completed_utc'] = utc()
        record['source_unchanged_at_close'] = sha(__file__)==record['source_sha256']
        if not record['source_unchanged_at_close']:
            record['status'] = 'FAILED_SOURCE_CHANGED'
        write_new(execution/'worker_receipt.json', record)
    return 0 if record['status']=='ORIGINAL_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW' else 1


def parent(args):
    execution = Path(args.execution_directory).resolve()
    execution.mkdir(parents=True, exist_ok=False)
    record = dict(schema='s35-original-launch-v1', status='CHECKING_METADATA', started_utc=utc(),
        source_sha256=sha(__file__), manifest_path=str(Path(args.manifest).resolve()),
        manifest_sha256=args.manifest_sha256, scientific_status='NOT_EVALUATED',
        limits=dict(poll_seconds=POLL_SECONDS, seconds_per_batch=BATCH_SECONDS,
                    total_seconds=TOTAL_SECONDS, rss_bytes=RSS_BYTES, minimum_free_bytes=MIN_FREE_BYTES),
        worker_spawned=False, sampled_peak_process_tree_rss_bytes=0, samples=0)
    process = None
    tracked = {}
    psutil = None
    t0 = None
    trace = None
    try:
        m = read_frozen(args.manifest, args.manifest_sha256)
        gate_module = load_bound(HERE/'resource_gate.py', m['source_identities'])
        metadata_gate = gate_module.check_manifest(args.manifest, args.manifest_sha256, metadata_only=True)
        require(metadata_gate['status'] == 'PASS_METADATA_ONLY', 'Real resources are not ready')
        output = Path(m['output_root'])
        require(output.is_absolute() and not output.exists(), 'Require a fresh absolute output_root')
        require(execution != output and not execution.is_relative_to(output),
                'External receipt directory must not occupy the fresh output root')
        free = shutil.disk_usage(output.parent).free
        record['disk_free_before_bytes'] = free
        require(free >= MIN_FREE_BYTES, 'Insufficient free disk before worker')
        write_new(execution/'metadata_gate.json', metadata_gate)
    except BaseException as exc:
        record.update(status='NOT_READY_BEFORE_SCIENTIFIC_IMPORT', error_type=type(exc).__name__,
                      error=str(exc), worker_spawned=False, completed_utc=utc(), scientific_imports=0)
        write_new(execution/'receipt.json', record)
        return 2
    try:
        # Existing base environment only; no dependency install or download.
        sys.path[:0] = [str(p) for p in PYTHONPATH]
        import psutil as psutil_module
        psutil = psutil_module
        record['psutil_version'] = psutil.__version__
        output.mkdir(parents=False, exist_ok=False)
        env = os.environ.copy()
        env.update(PYTHONPATH=os.pathsep.join(str(p) for p in PYTHONPATH),
            PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='8', MKL_NUM_THREADS='8',
            OPENBLAS_NUM_THREADS='8', VECLIB_MAXIMUM_THREADS='8', NUMEXPR_NUM_THREADS='8',
            HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_HUB_DISABLE_IMPLICIT_TOKEN='1',
            MPLBACKEND='Agg', KORNIA_CHECK_VERSION='0')
        command = [str(PYTHON), '-B', str(Path(__file__).resolve()), '--worker',
            '--manifest', str(Path(args.manifest).resolve()), '--manifest-sha256', args.manifest_sha256,
            '--execution-directory', str(execution)]
        record['command'] = command
        trace = TraceBoundary(output/'trace/events.jsonl', args.manifest_sha256)
        write_new(execution/'launch_ticket.json', dict(parent_pid=os.getpid(),
            manifest_sha256=args.manifest_sha256, launcher_sha256=record['source_sha256'],
            output_root=str(output), created_utc=utc()))
        with (execution/'worker.stdout.txt').open('x') as so, (execution/'worker.stderr.txt').open('x') as se, \
                (execution/'monitor.jsonl').open('x') as monitor:
            t0 = time.monotonic()
            previous_poll = t0
            phase2_start = None
            process = subprocess.Popen(command, cwd=str(ROOT), env=env, stdout=so, stderr=se, start_new_session=True)
            record.update(worker_spawned=True, pid=process.pid, worker_started_utc=utc())
            while True:
                now = time.monotonic()
                record['maximum_poll_gap_seconds'] = max(record.get('maximum_poll_gap_seconds',0), now-previous_poll)
                trace.poll()
                now = time.monotonic()
                if trace.completed and phase2_start is None:
                    require(now-t0 <= BATCH_SECONDS, 'First committed batch observed after first 1800-second limit')
                    # Conservatively no later than actual completion; nominally
                    # at most one polling interval earlier. No wall-clock reset.
                    phase2_start = previous_poll
                    record['phase2_start_elapsed_seconds'] = phase2_start-t0
                    record['first_batch_completion_event'] = trace.completed[0]
                rss = 0
                try:
                    p = psutil.Process(process.pid)
                    for q in [p]+p.children(recursive=True):
                        tracked[(q.pid,q.create_time())] = q
                except psutil.NoSuchProcess:
                    pass
                for key,q in list(tracked.items()):
                    try:
                        if q.is_running() and q.create_time() == key[1]:
                            rss += q.memory_info().rss
                    except psutil.NoSuchProcess:
                        pass
                free = shutil.disk_usage(output).free
                now = time.monotonic()
                elapsed = now-t0
                phase_elapsed = elapsed if phase2_start is None else now-phase2_start
                record['samples'] += 1
                record['sampled_peak_process_tree_rss_bytes'] = max(record['sampled_peak_process_tree_rss_bytes'],rss)
                sample = dict(utc=utc(), elapsed_seconds=elapsed, budget_phase=1 if phase2_start is None else 2,
                    phase_elapsed_seconds=phase_elapsed, process_tree_rss_bytes=rss, disk_free_bytes=free,
                    completed_batches=len(trace.completed), trace_sequence_count=trace.seq)
                monitor.write(json.dumps(sample,sort_keys=True)+'\n');monitor.flush();os.fsync(monitor.fileno())
                reasons = []
                if elapsed > TOTAL_SECONDS: reasons.append('total_wall_time')
                if phase_elapsed > BATCH_SECONDS: reasons.append('batch_wall_time')
                if rss > RSS_BYTES: reasons.append('process_tree_rss')
                if free < MIN_FREE_BYTES: reasons.append('disk_free')
                if reasons:
                    record['limit_exceeded'] = reasons
                    record['termination'] = kill_tree(process,tracked,psutil)
                    break
                if process.poll() is not None:
                    break
                previous_poll = now
                time.sleep(POLL_SECONDS)
        if process.poll() is None:
            record['termination'] = kill_tree(process,tracked,psutil)
        record['returncode'] = process.poll()
        trace.poll()
        # A returned parent is not allowed to leave detached work running.
        living = [q for q in tracked.values() if q.is_running() and q.status()!=psutil.STATUS_ZOMBIE]
        if living:
            record['unexpected_live_descendants'] = [q.pid for q in living]
            record['termination'] = kill_tree(process,tracked,psutil)
        worker_receipt = execution/'worker_receipt.json'
        require(worker_receipt.is_file(), 'Worker did not write a terminal receipt')
        wr = json.loads(worker_receipt.read_text())
        require(wr.get('manifest_sha256') == args.manifest_sha256
                and wr.get('source_sha256') == record['source_sha256']
                and wr.get('source_unchanged_at_close') is True, 'Worker receipt identity differs')
        record['worker_receipt_sha256'] = sha(worker_receipt)
        record['worker_status'] = wr.get('status')
        eligible = (record['returncode'] == 0 and 'limit_exceeded' not in record
            and 'unexpected_live_descendants' not in record and len(trace.completed) == 2
            and trace.closed and not trace.pending and not trace.seen_failure
            and wr.get('status') == 'ORIGINAL_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW')
        record['status'] = 'COMPLETED_EXTERNAL_RUN_PENDING_INDEPENDENT_REVIEW' if eligible else 'FAILED_OR_PARTIAL_ORIGINAL_RUN'
    except BaseException as exc:
        record.update(status='FAILED_LAUNCH_OR_MONITOR', error_type=type(exc).__name__, error=str(exc),
                      traceback=traceback.format_exc())
        if process is not None and psutil is not None:
            record['termination'] = kill_tree(process,tracked,psutil)
            record['returncode'] = process.poll()
    finally:
        record['completed_utc'] = utc()
        if t0 is not None:
            record['elapsed_seconds_including_termination'] = time.monotonic()-t0
        if trace is not None:
            record['trace_budget_boundary'] = dict(completed=trace.completed, session_closed=trace.closed,
                seen_failure=trace.seen_failure, parsed_events=trace.seq, pending_bytes=len(trace.pending),
                scope='Budget boundary only; no complete scientific or raw-output validation')
        record['source_unchanged_at_close'] = sha(__file__) == record['source_sha256']
        if not record['source_unchanged_at_close']:
            record['status'] = 'FAILED_SOURCE_CHANGED'
        write_new(execution/'receipt.json', record)
    return 0 if record['status']=='COMPLETED_EXTERNAL_RUN_PENDING_INDEPENDENT_REVIEW' else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--execution-directory', required=True)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    def interrupted(signum, frame):
        raise KeyboardInterrupt('Launcher/worker received signal '+str(signum))
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    return worker(args) if args.worker else parent(args)


if __name__ == '__main__':
    raise SystemExit(main())
