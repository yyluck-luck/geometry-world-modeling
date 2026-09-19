"""Independent bounded V9 source delta audit and one existing selftest per runtime."""
import ast
from datetime import datetime, timezone
import difflib
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import time

HERE = Path(__file__).resolve().parent.parent
EVIDENCE = Path(__file__).resolve().parent
V8 = HERE.parent / 'S47B_c2_confirmation_generation_v8'
ROOT = HERE.parents[1]
ROLE = '/root/c2_v9_source_primary'

def utc():
    return datetime.now(timezone.utc).isoformat()

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(name, value):
    path = EVIDENCE / name
    payload = (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()
    with path.open('xb') as stream:
        stream.write(payload)
    path.chmod(0o444)
    return sha(path)

def state(path):
    current = path.lstat()
    assert stat.S_ISREG(current.st_mode), path
    return {'sha256': sha(path), 'bytes': current.st_size,
            'mode': oct(stat.S_IMODE(current.st_mode)), 'mtime_ns': current.st_mtime_ns}

started = utc()
assert sha(HERE / 'FROZEN_SOURCE_SET_V9.json') == '33e2a733735e959b8e912f18e3476b521fa7ee15f4d893f763ecb87a436afa6f'
assert sha(HERE / 'SOURCE_ONLY_AUTHOR_RECEIPT_V9.json') == '9ad5123790d469a5cdbca807210e0aecacf00816025a0db4e65dc9660f669f4b'
frozen = json.loads((HERE / 'FROZEN_SOURCE_SET_V9.json').read_text())
author = json.loads((HERE / 'SOURCE_ONLY_AUTHOR_RECEIPT_V9.json').read_text())
old_frozen = json.loads((V8 / 'FROZEN_SOURCE_SET_V8.json').read_text())
assert sha(V8 / 'FROZEN_SOURCE_SET_V8.json') == frozen['legacy_v8_frozen_source_set_sha256']
candidate = frozen['production_candidate_sha256']
assert len(candidate) == 8 and author['production_candidate_sha256'] == candidate
initial = {name: state(HERE / name) for name in [*candidate, 'static_selftest.py']}
assert all(initial[name]['sha256'] == digest and initial[name]['mode'] == '0o444'
           for name, digest in candidate.items())
assert initial['static_selftest.py']['sha256'] == frozen['static_selftest_sha256']
assert all(sha(HERE / name) == digest for name, digest in author['evidence_sha256'].items())
paths = list(frozen['formal_paths_lexists'])
assert all(not os.path.lexists(path) for path in paths)

old_preservation = json.loads((HERE / 'V8_PRESERVATION_AFTER.json').read_text())['files']
v8_before = {name: state(V8 / name) for name in old_preservation}
assert v8_before == old_preservation
assert set(str(p.relative_to(V8)) for p in V8.rglob('*') if p.is_file()) == set(old_preservation)

old_sha = {name: sha(V8 / name) for name in candidate}
reverse = [(digest, old_sha[name]) for name, digest in candidate.items() if digest != old_sha[name]]
files = {}
diff = []
for name in candidate:
    old = (V8 / name).read_bytes()
    new = (HERE / name).read_bytes()
    row = {'v8_sha256': old_sha[name], 'v9_sha256': sha(HERE / name), 'byte_identical': old == new}
    if name.endswith('.py'):
        old_tree, new_tree = ast.parse(old), ast.parse(new)
        old_nodes = [ast.dump(n, include_attributes=False) for n in old_tree.body
                     if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
        new_nodes = [ast.dump(n, include_attributes=False) for n in new_tree.body
                     if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
        row['all_top_level_function_and_class_AST_identical'] = old_nodes == new_nodes
        row['top_level_function_and_class_count'] = len(new_nodes)
        normalized = new.decode().replace('results/S47B_C2_confirmation_generation_v9',
                                         'results/S47B_C2_confirmation_generation_v8')
        for new_hash, old_hash in reverse:
            normalized = normalized.replace(new_hash, old_hash)
        row['whole_source_after_only_output_path_and_actual_source_hash_reversal_equals_v8'] = normalized.encode() == old
        assert old_nodes == new_nodes and normalized.encode() == old, name
    elif name.endswith('.yaml'):
        assert old == new
    files[name] = row
    diff.extend(difflib.unified_diff(old.decode().splitlines(True), new.decode().splitlines(True),
                                   fromfile='V8/' + name, tofile='V9/' + name))
selftest_old = (V8 / 'static_selftest.py').read_text()
selftest_new = (HERE / 'static_selftest.py').read_text()
assert selftest_new == selftest_old.replace('V8', 'V9').replace('v8', 'v9')
with (EVIDENCE / 'independently_derived_source_diff.patch').open('x') as stream:
    stream.write(''.join(diff))
(EVIDENCE / 'independently_derived_source_diff.patch').chmod(0o444)

def literal_assignments(name):
    result = {}
    for node in ast.parse((HERE / name).read_bytes()).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                result[node.targets[0].id] = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                pass
    return result
gate = literal_assignments('generation_gate.py')
freeze = literal_assignments('freeze_c2_manifest.py')
assert gate['C2_PROTOCOL_SHA256'] == candidate['PROTOCOL.md']
assert gate['FREEZE_PROTOCOL_SHA256'] == candidate['FREEZE_PROTOCOL.md']
assert gate['C2_CONFIG_SHA256'] == candidate['inference_seed44.yaml']
assert freeze['FREEZE_PROTOCOL_SHA256'] == candidate['FREEZE_PROTOCOL.md']
assert all(candidate[name] == digest for name, digest in freeze['SOURCE_HASHES'].items())
assert all(literal_assignments(name)['GATE_SHA256'] == candidate['generation_gate.py']
           for name in ['launch_generation.py', 'create_launch_authorization.py'])
audit = {'reviewer_role': ROLE, 'started_utc': started, 'completed_utc': utc(),
         'status': 'PASS_INDEPENDENT_MINIMAL_SOURCE_DELTA_AUDIT',
         'files': files, 'candidate_sha256': candidate,
         'selftest_exactly_v8_with_only_version_labels_changed': True,
         'source_hash_pins_rederived_without_importing_candidate': True,
         'v8_all_66_files_match_author_preservation_snapshot': len(v8_before) == 66,
         'new_test_cases': 0, 'formal_paths_lexists': {p: os.path.lexists(p) for p in paths},
         'scientific_controls_changed': False, 'scientific_bodies_read': 0}
save('independent_static_audit.json', audit)

runs = []
for name, runtime in [('python312', str(ROOT / '.venv-cut3r/bin/python')),
                      ('python313', '/opt/homebrew/bin/python3')]:
    argv = [runtime, '-I', '-B', '-S', str(HERE / 'static_selftest.py')]
    start_utc = utc()
    monotonic_start = time.monotonic()
    completed = subprocess.run(argv, cwd='/private/tmp', capture_output=True, timeout=60, check=False)
    elapsed = time.monotonic() - monotonic_start
    end_utc = utc()
    for kind, payload in [('stdout.json', completed.stdout), ('stderr.txt', completed.stderr)]:
        path = EVIDENCE / (name + '.' + kind)
        with path.open('xb') as stream:
            stream.write(payload)
        path.chmod(0o444)
    parsed = json.loads(completed.stdout) if completed.returncode == 0 else None
    record = {'name': name, 'argv': argv, 'cwd': '/private/tmp',
              'resolved_executable': str(Path(runtime).resolve()),
              'resolved_executable_sha256': sha(Path(runtime).resolve()),
              'started_utc': start_utc, 'completed_utc': end_utc,
              'elapsed_seconds': elapsed, 'returncode': completed.returncode,
              'stdout_sha256': sha(EVIDENCE / (name + '.stdout.json')),
              'stderr_sha256': sha(EVIDENCE / (name + '.stderr.txt')),
              'stdout_bytes': len(completed.stdout), 'stderr_bytes': len(completed.stderr),
              'reported_status': parsed['status'] if parsed else None,
              'reported_python': parsed['python'] if parsed else None}
    runs.append(record)
    assert completed.returncode == 0 and completed.stderr == b'', record
    assert parsed['status'] == 'PASS_S47_C2_V9_CANDIDATE_STATIC_SELFTEST'
    assert parsed['candidate_sha256'] == candidate
    assert parsed['static_selftest_sha256'] == frozen['static_selftest_sha256']
    assert all(not present for present in parsed['formal_lexists'].values())
    assert parsed['model_or_scientific_imports'] == parsed['generation_calls'] == parsed['pixels_decoded'] == 0
after = {name: state(HERE / name) for name in initial}
assert after == initial
v8_after = {name: state(V8 / name) for name in old_preservation}
assert v8_after == v8_before
assert all(not os.path.lexists(path) for path in paths)
receipt = {'reviewer_role': ROLE, 'status': 'PASS_EXISTING_FINITE_SELFTEST_ONCE_PER_REQUIRED_RUNTIME',
           'completed_utc': utc(), 'runs': runs, 'total_selftest_runs': 2, 'new_test_cases': 0,
           'all_candidate_bytes_modes_mtimes_preserved': after == initial,
           'all_66_v8_bytes_modes_mtimes_preserved': v8_after == v8_before,
           'candidate_final_snapshot': after,
           'formal_paths_lexists': {p: os.path.lexists(p) for p in paths},
           'prepare_calls': 0, 'attach_calls': 0, 'authorization_calls': 0,
           'formal_launch_calls': 0, 'scientific_body_reads': 0, 'pixels_decoded': 0,
           'execution_authority': 'NONE', 'new_method_validated': False}
receipt_sha = save('fresh_test_runs.json', receipt)
print(json.dumps({'static_audit_sha256': sha(EVIDENCE / 'independent_static_audit.json'),
                  'fresh_test_runs_sha256': receipt_sha, 'runs': runs,
                  'candidate_and_v8_preserved': True, 'formal_paths_all_absent': True}, indent=2))
