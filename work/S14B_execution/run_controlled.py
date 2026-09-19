#!/usr/bin/env python3
"""External time/identity guard for the two frozen S14B stages."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[2]

def now():
    return datetime.now(timezone.utc).isoformat()

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', choices=['measurement', 'verification'], required=True)
    args = parser.parse_args()
    manifest_path = ROOT / 'docs/S14B_EXECUTION_MANIFEST.json'
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    stage = manifest['stages'][args.stage]
    output = ROOT / stage['output']
    assert not output.exists(), 'Existing output must be preserved'
    receipt_dir = ROOT / 'work/S14B_execution' / args.stage
    receipt_dir.mkdir(exist_ok=False)
    receipt_path = receipt_dir / 'caller_receipt.json'
    receipt = dict(status='RUNNING', started_utc=now(), stage=args.stage,
                   external_timeout_seconds=600, output=str(output))
    save(receipt_path, receipt)
    expected = {item['path']: item['sha256'] for item in manifest['inputs'] + manifest['controls']}
    expected['docs/S14B_EXECUTION_MANIFEST.json'] = hashlib.sha256(manifest_bytes).hexdigest()
    proc = None
    try:
        before = {name: digest(ROOT / name) for name in expected}
        receipt['identity_before'] = before
        assert before == expected, 'Pre-execution identity mismatch'
        if args.stage == 'verification':
            prior = ROOT / manifest['stages']['measurement']['output']
            assert json.loads((prior / 'metadata.json').read_text())['status'] == 'SUCCESS'
            receipt['production_files_before'] = {p.name: digest(p) for p in prior.iterdir() if p.is_file()}
            command = [str(ROOT / '.venv/bin/python'), str(ROOT / stage['script']),
                       '--result', str(prior), '--output', str(output)]
        else:
            command = [str(ROOT / '.venv/bin/python'), str(ROOT / stage['script']),
                       '--manifest', str(manifest_path), '--output', str(output)]
        receipt['command'] = command
        receipt['spawned_utc'] = now()
        save(receipt_path, receipt)
        with (receipt_dir / 'stdout.txt').open('x') as out, (receipt_dir / 'stderr.txt').open('x') as err:
            proc = subprocess.Popen(command, cwd=ROOT, stdout=out, stderr=err, start_new_session=True)
            try:
                receipt['exit_code'] = proc.wait(timeout=600)
            except subprocess.TimeoutExpired:
                receipt['timed_out'] = True
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait()
                receipt['exit_code'] = proc.returncode
                raise
        receipt['child_finished_utc'] = now()
        assert receipt['exit_code'] == 0, 'Child exited unsuccessfully; retain failure'
        result_file = output / ('metadata.json' if args.stage == 'measurement' else 'verification.json')
        result = json.loads(result_file.read_text())
        assert result['status'] == ('SUCCESS' if args.stage == 'measurement' else 'PASS')
        if args.stage == 'measurement':
            assert result['identity_unchanged']
            assert result['counters']['completed_blocks'] == 6
            for name, sha in result['output_sha256'].items():
                assert digest(output / name) == sha, 'Output differs from metadata'
        else:
            receipt['production_files_after'] = {p.name: digest(p) for p in prior.iterdir() if p.is_file()}
            assert receipt['production_files_before'] == receipt['production_files_after']
        receipt['result_receipt_sha256'] = digest(result_file)
        receipt['status'] = 'PASS'
    except BaseException as exc:
        receipt.update(status='FAIL', exception=repr(exc), traceback=traceback.format_exc())
    finally:
        receipt['identity_after'] = {name: digest(ROOT / name) if (ROOT / name).is_file() else None for name in expected}
        receipt['identity_unchanged'] = receipt.get('identity_before') == expected == receipt['identity_after']
        if not receipt['identity_unchanged']:
            receipt['status'] = 'FAIL'
        receipt['ended_utc'] = now()
        save(receipt_path, receipt)
    print(json.dumps({key: receipt[key] for key in ['stage', 'status', 'started_utc', 'ended_utc', 'identity_unchanged']}))
    if receipt['status'] != 'PASS':
        sys.exit(1)

if __name__ == '__main__':
    main()
