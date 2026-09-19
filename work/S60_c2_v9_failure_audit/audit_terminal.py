"""Bounded read-only terminal audit; never opens a C2 image or tensor payload."""
import collections
import datetime
import hashlib
import json
import os
import pathlib
import stat
import subprocess

ROOT = pathlib.Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
BASE = ROOT / 'work/S47B_c2_confirmation_generation_v9'
EXEC = BASE / 'execution_01'
OUT = ROOT / 'results/S47B_C2_confirmation_generation_v9'
EXT = ROOT / 'work/resumption_20260909/C2_V9_EXTERNAL_LAUNCH'
DEST = ROOT / 'work/S60_c2_v9_failure_audit'
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
read_snapshots = {}

def snapshot(path):
    path = pathlib.Path(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(fd)
        assert stat.S_ISREG(before.st_mode), str(path)
        with os.fdopen(os.dup(fd), 'rb') as handle:
            raw = handle.read()
        after = os.fstat(fd)
        fields = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns', 'st_mode')
        assert all(getattr(before, k) == getattr(after, k) for k in fields)
        read_snapshots[str(path)] = dict(sha256=hashlib.sha256(raw).hexdigest(),
            device=after.st_dev, inode=after.st_ino, size=after.st_size,
            mtime_ns=after.st_mtime_ns, ctime_ns=after.st_ctime_ns,
            mode=oct(stat.S_IMODE(after.st_mode)))
        return raw
    finally:
        os.close(fd)

def read(path):
    return json.loads(snapshot(path))

def digest(path):
    return hashlib.sha256(snapshot(path)).hexdigest()

def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode()

def events(path):
    raw = snapshot(path)
    assert raw.endswith(b'\n')
    rows = [json.loads(line) for line in raw.splitlines()]
    previous = '0' * 64
    for seq, row in enumerate(rows):
        assert row['seq'] == seq and row['previous_sha256'] == previous
        assert hashlib.sha256(canon({k:v for k,v in row.items() if k != 'sha256'})).hexdigest() == row['sha256']
        previous = row['sha256']
    return rows

def small_tree(tree):
    kind = tree['kind']
    if kind == 'scalar':
        return tree['value']
    if kind in ('list', 'tuple'):
        return [small_tree(i) for i in tree['items']]
    if kind == 'dict':
        return {small_tree(i['key']): small_tree(i['value']) for i in tree['items']}
    return {'descriptor_only': kind}

external = read(EXT / 'receipt.json')
parent = read(EXEC / 'receipt.json')
worker = read(EXEC / 'worker_receipt.json')
watchdog = read(EXEC / 'watchdog_receipt.json')
commit = read(EXEC / 'supervisor_terminal_commit.json')
provisional = read(EXEC / 'supervisor_terminal_provisional.json')
ticket = read(EXEC / 'launch_ticket.json')
manifest = read(BASE / 'review_attachment_01/manifest.json')
frozen = read(BASE / 'FROZEN_SOURCE_SET_V9.json')
archive = read(OUT / 'archive/manifest.json')
trace_rows = events(OUT / 'trace/events.jsonl')
archive_rows = events(OUT / 'archive/events.jsonl')
monitor = [json.loads(x) for x in snapshot(EXEC / 'monitor.jsonl').splitlines()]
snapshot(EXEC / 'worker.stdout.txt')
snapshot(EXEC / 'worker.stderr.txt')
for name in ('stdout', 'stderr'):
    assert digest(EXT / (name + '.txt')) == external[name + '_sha256']

assert external['returncode'] == parent['returncode'] == watchdog['worker_returncode'] == commit['parent_returncode'] == 1
assert external['external_timeout'] is False
assert parent['status'] == worker['status'] == 'FAILED_OR_PARTIAL_C2_BASELINE_RUN'
assert commit['outcome_status'] == 'FAILED_OR_PARTIAL_ATTEMPT' and commit['standalone_success'] is False
assert provisional['standalone_success'] is False
assert worker['error_type'] == 'IndexError'
assert 'pipeline.py", line 711' in worker['traceback'] and 'sorted_frames[0]' in worker['traceback']
for key, path in {
    'parent_receipt_sha256': EXEC/'receipt.json',
    'worker_receipt_sha256': EXEC/'worker_receipt.json',
    'watchdog_receipt_sha256': EXEC/'watchdog_receipt.json',
    'attempt_started_sha256': EXEC/'supervisor_attempt_started.json',
    'terminal_provisional_sha256': EXEC/'supervisor_terminal_provisional.json',
    'manifest_sha256': BASE/'review_attachment_01/manifest.json',
    'launcher_sha256': BASE/'launch_generation.py',
}.items():
    assert commit[key] == digest(path), key
assert parent['worker_receipt_sha256'] == digest(EXEC/'worker_receipt.json')

source_observations = {}
for path, expected in manifest['source_identities'].items():
    actual = digest(path)
    source_observations[path] = dict(expected_sha256=expected, actual_sha256=actual, matches=actual == expected)
assert len(source_observations) == 219 and all(v['matches'] for v in source_observations.values())
assert archive['source_identities'] == trace_rows[0]['payload']['source_identities'] == manifest['source_identities']
frozen_observations = {}
for name, expected in frozen['production_candidate_sha256'].items():
    actual = digest(BASE / name)
    frozen_observations[name] = dict(expected_sha256=expected, actual_sha256=actual,
        mode=read_snapshots[str(BASE/name)]['mode'])
    assert actual == expected and frozen_observations[name]['mode'] == '0o444'

batch_complete = [v for v in trace_rows if v['event'] == 'batch_complete']
trace_counts = collections.Counter(v['event'] for v in trace_rows)
assert len(trace_rows) == 167 and len(batch_complete) == 1
assert batch_complete[0]['seq'] == 164
assert batch_complete[0]['sha256'] == parent['first_batch_completion_event']['event_sha256']
assert batch_complete[0]['payload']['retained_frame_ids'] == [1, 2, 3, 4]
assert trace_counts['denoiser_call'] == 50 and trace_counts['sample_call'] == trace_counts['batch_begin'] == 1
assert {r['batch_id'] for r in trace_rows if r['batch_id'] is not None} == {'batch_1'}
assert trace_rows[-1]['event'] == 'session_end' and trace_rows[-1]['payload']['batches'] == 1
failure = [v for v in trace_rows if v['event'] == 'operation_failure']
assert len(failure) == 1 and failure[0]['payload']['phase'] == 'turn_right'
retrieval = [v for v in archive_rows if v['event'] == 'capture_complete' and v['payload']['name'] == 'retrieval_output']
assert len(retrieval) == 1
retrieval_metadata = small_tree(retrieval[0]['payload']['tree'])
assert retrieval_metadata['result'] == [[], []]
assert retrieval_metadata['metadata']['operation_name'] == 'turn_right'
assert archive['status'] == 'ARCHIVE_PARTIAL'
assert archive['event_count'] == len(archive_rows) == 67
assert archive['last_event_sha256'] == archive_rows[-1]['sha256']
capture_counts = collections.Counter(v['payload']['name'] for v in archive_rows if v['event'] == 'capture_complete')
assert dict(capture_counts) == archive['archived_name_counts']
assert archive['failed_captures'] == 0 and archive['missing_required_names']['integration_return']['archived'] == 0

# File identities and sizes only for scientific payloads, never their bodies.
listed_files = {}
for relative, desc in archive['files'].items():
    path = OUT / 'archive' / relative
    assert not pathlib.Path(relative).is_absolute() and '..' not in pathlib.Path(relative).parts
    s = path.lstat()
    listed_files[relative] = dict(size=s.st_size, expected_size=desc['bytes'], regular=stat.S_ISREG(s.st_mode))
assert all(v['regular'] and v['size'] == v['expected_size'] for v in listed_files.values())
assert set(archive['files']) == {str(p.relative_to(OUT/'archive')) for p in (OUT/'archive').rglob('*') if p.is_file()} - {'manifest.json'}

fallbacks = {str(BASE / name): os.path.lexists(BASE/name) for name in
    ('.execution_01.supervisor_failure.json', '.execution_01.watchdog_failure.json')}
identity_checks = []
for record_name, record in [('parent',parent),('worker',worker),('ticket',ticket),('watchdog',watchdog),('commit',commit)]:
    for key, path in [('execution_identity',EXEC),('output_identity',OUT)]:
        if key in record:
            s = path.lstat()
            matches = stat.S_ISDIR(s.st_mode) and record[key]['device'] == s.st_dev and record[key]['inode'] == s.st_ino
            identity_checks.append(dict(record=record_name, path=str(path), matches=matches))
assert all(v['matches'] for v in identity_checks)
assert watchdog['all_registered_descendants_gone'] and watchdog['cleanup_complete'] and watchdog['worker_status_relayed']
pids = sorted({watchdog['supervisor_pid'], watchdog['watchdog_pid'], watchdog['worker_pid']} |
              {v['pid'] for v in watchdog['descendant_identity_ledger']})
argv = ['ps','-p',','.join(map(str,pids)),'-o','pid=,ppid=,lstart=,command=']
ps_result = subprocess.run(argv, text=True, capture_output=True)
process_observation = dict(observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    argv=argv, returncode=ps_result.returncode, stdout=ps_result.stdout, stderr=ps_result.stderr,
    all_requested_pids_absent=ps_result.returncode == 1 and not ps_result.stdout and not ps_result.stderr)
assert process_observation['all_requested_pids_absent']

# Recheck snapshots so the report describes one unchanged set of read files.
for path, observed in list(read_snapshots.items()):
    current = digest(path)
    assert current == observed['sha256'] and read_snapshots[path] == observed

result = dict(schema='s60-c2-v9-terminal-failure-audit-v1',
    status='INDEPENDENTLY_VERIFIED_FAILED_PARTIAL_ATTEMPT',
    reviewer_role='/root/c2_v9_source_primary', execution_author_role='/root',
    started_utc=started, completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    scope='Read-only terminal text, source bytes, event hash chains, payload filenames/sizes and registered process absence. No C2 image/tensor payload body read, model execution or scoring.',
    external_receipt=external,
    terminal=dict(parent_status=parent['status'],worker_status=worker['status'],
        commit_status=commit['status'],commit_outcome=commit['outcome_status'],
        commit_standalone_success=commit['standalone_success'],parent_returncode=parent['returncode'],
        worker_returncode=watchdog['worker_returncode'],commit_parent_returncode=commit['parent_returncode'],
        worker_error_type=worker['error_type'],worker_error=worker['error'],traceback=worker['traceback'],
        parent_completed_utc=parent['completed_utc'],worker_completed_utc=worker['completed_utc'],
        commit_completed_utc=commit['completed_utc'],watchdog_completed_utc=watchdog['completed_utc'],
        all_cross_receipt_hash_bindings_match=True,fixed_failure_paths_lexists=fallbacks,
        interpretation='Fallback absence means no fallback receipt was found; the explicit nonzero return and failure outcome remain decisive.'),
    trace=dict(event_count=len(trace_rows),event_counts=dict(trace_counts),event_chain_verified=True,
        last_event_sha256=trace_rows[-1]['sha256'],completed_batches=1,required_batches=2,
        completed_batch_event=batch_complete[0],second_sample_call_recorded=False,
        operation_failure={k:v for k,v in failure[0].items() if k!='payload'} | {'payload':{k:v for k,v in failure[0]['payload'].items() if k!='rng'}},
        history_length_at_last_cache_commit=[r['payload']['history_after_length'] for r in trace_rows if r['event']=='cache_commit'][-1],
        phase2_interpretation='Parent budget phase 2 starts after batch_1 completion; it does not establish second-batch sampling.'),
    archive=dict(status=archive['status'],event_count=len(archive_rows),event_chain_verified=True,
        last_event_sha256=archive_rows[-1]['sha256'],capture_counts=dict(capture_counts),
        missing_required_names=archive['missing_required_names'],failed_captures=archive['failed_captures'],
        metadata_only_retrieval_result=dict(event_seq=retrieval[0]['seq'],event_sha256=retrieval[0]['sha256'],utc=retrieval[0]['utc'],decoded_metadata= retrieval_metadata),
        listed_file_count=len(listed_files),listed_files_present_regular_size_match=True,
        payload_hashes_recomputed=False,payloads_decoded=False),
    process=dict(watchdog_status=watchdog['status'],descendant_identity_ledger=watchdog['descendant_identity_ledger'],
        cleanup_actions=watchdog['cleanup_actions'],cleanup_complete=watchdog['cleanup_complete'],
        supervisor_liveness_lost=watchdog['supervisor_liveness_lost'],
        all_registered_descendants_gone=watchdog['all_registered_descendants_gone'],fresh_observation=process_observation,
        scope='Only ticket supervisor/watchdog/worker and five registered descendant identities; no claim about never-observed escaping processes.'),
    monitoring=dict(samples=len(monitor),first=monitor[0],last=monitor[-1],
        maximum_sampled_rss_bytes=max(v['process_tree_rss_bytes'] for v in monitor),
        minimum_sampled_free_disk_bytes=min(v['disk_free_bytes'] for v in monitor),
        timeout_observed=False,termination_interpretation='Recorded IndexError; no external timeout or watchdog liveness-loss termination in these receipts.'),
    source_integrity=dict(source_count=len(source_observations),all_match=True,
        runtime_trace_archive_source_tables_match=True,source_observations=source_observations,
        frozen_eight_sources=frozen_observations,current_directory_identity_checks=identity_checks,
        all_read_snapshots_unchanged_at_close=True),
    evidence_files=read_snapshots,
    boundaries=dict(scientific_status='NOT_EVALUATED',quality_status='NOT_EVALUATED',
        c2_complete=False,cohort_complete=False,success_readback_authorization='NONE',
        retry_authorization='NONE',novelty_authorization='NONE',new_method_validated=False,
        explanation='One completed first batch followed by a runtime context-selection failure. This is no C2 success, nine-frame archive, image-quality failure, scoring result or model-method gain.'),
    ledger_note='The later-recorded 17:11 stale running/second-phase observation cannot override the external completed_utc 17:08:45.362273Z return 1. Root owns append-only correction; this audit edits no ledger or prior evidence.')
for name, value in [('TERMINAL_FAILURE_AUDIT.json', result)]:
    path=DEST/name
    with path.open('x') as f:
        f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    path.chmod(0o444)
print(json.dumps({'audit':str(DEST/'TERMINAL_FAILURE_AUDIT.json'),
    'sha256':hashlib.sha256((DEST/'TERMINAL_FAILURE_AUDIT.json').read_bytes()).hexdigest(),
    'completed_utc':result['completed_utc'],'completed_batches':1,'source_count':len(source_observations),
    'process_observation':process_observation},ensure_ascii=False))
