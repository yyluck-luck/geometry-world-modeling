"""End-to-end interface test in a new artificial root; never opens real data.

Production is an external CLI process from a byte-copied snapshot, never imported.
Only this independent module is imported, with ROOT redirected to artificial data.
"""
import importlib.util
import copy
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = Path(__file__).resolve().parent
SOURCE = ROOT / 'scripts/verify_s14c_selection_disagreement_independent.py'
spec = importlib.util.spec_from_file_location('s14c_independent', SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
parent_fixture = ROOT / 'work/S14C_implementation/artificial_v2'
target = WORK / 'integration_v3'
target.mkdir(exist_ok=False)
synthetic = target / 'synthetic_root'
synthetic.mkdir()
record = {'started_utc': m.now(), 'status': 'RUNNING', 'real_input_files_read': 0,
          'production_imported_or_functions_read': False, 'production_execution': 'separate CLI on artificial-only root',
          'independent_source_sha256': m.sha(SOURCE)}
try:
    old_manifest = m.decode((parent_fixture / 'synthetic_root/manifest.json').read_bytes())
    for entry in old_manifest['inputs'] + [old_manifest['score_input']]:
        source = parent_fixture / 'synthetic_root' / entry['path']
        output = synthetic / entry['path']
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, output)
        m.require(m.sha(output) == entry['sha256'], 'original artificial input SHA ' + entry['path'])
    script = synthetic / 'scripts/measure_s14c_selection_disagreement.py'
    script.parent.mkdir()
    shutil.copyfile(parent_fixture / 'successful_artificial_measure/source_snapshot.py', script)
    m.require(m.sha(script) == old_manifest['source_sha256'], 'artificial production snapshot SHA')
    # Producer's original software fixture only has 24 main records; reproduce
    # the frozen real writer's 192-condition shape without changing those 24.
    old_records = m.decode((synthetic / m.LABEL_PATH).read_bytes())
    m.require(len(old_records) == 24, 'artificial 24 main fixture records')
    records = []
    for rec in old_records:
        for stride in [8, 12]:
            for arm in ['A0P0', 'A0P1', 'A1P0', 'A1P1']:
                extra = copy.deepcopy(rec)
                extra.update(stride=stride, arm=arm, main_comparison=(stride == 8 and arm == 'A0P0'))
                records.append(extra)
    m.dump(synthetic / m.LABEL_PATH, records)
    manifest = dict(old_manifest, independent_verifier_sha256=m.sha(SOURCE), group_contract=m.GROUP_CONTRACT,
                    score_input={'path': m.LABEL_PATH, 'sha256': m.sha(synthetic / m.LABEL_PATH)})
    manifest_path = synthetic / 'manifest.json'
    m.dump(manifest_path, manifest)
    for stage, extra in [('measure', []), ('associate', ['--input-result', str(target / 'measure')])]:
        command = [sys.executable, str(script), '--stage', stage, '--root', str(synthetic), '--manifest', str(manifest_path),
                   '--output', str(target / stage)] + extra
        completed = subprocess.run(command, capture_output=True, text=True, timeout=30)
        (target / (stage + '.stdout.txt')).write_text(completed.stdout)
        (target / (stage + '.stderr.txt')).write_text(completed.stderr)
        m.require(completed.returncode == 0, stage + ' artificial external CLI')
    m.ROOT = synthetic
    m.run(manifest_path, target / 'measure', target / 'associate', target / 'verification')
    verified = m.decode((target / 'verification/verification.json').read_bytes())
    record.update(status='PASS', verification_status=verified['status'], exact_checks=verified['exact_checks'],
                  float_checks=verified['float_checks'], max_abs_difference=verified['max_abs_difference'])
except BaseException as exc:
    record.update(status='FAIL', exception=repr(exc))
    raise
finally:
    record['completed_utc'] = m.now()
    m.dump(target / 'integration_receipt.json', record)
print(record)
