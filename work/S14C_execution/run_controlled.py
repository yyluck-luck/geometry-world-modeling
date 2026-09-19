#!/usr/bin/env python3
"""Run one frozen S14C stage with external identity, timeout and seal guards."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[2]

def now():
    return datetime.now(timezone.utc).isoformat()

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def files(directory):
    return {p.name:sha(p) for p in directory.iterdir() if p.is_file()}

def seal_check(directory, manifest_path, manifest):
    seal = json.loads((directory/'measure_seal.json').read_text())
    actual = files(directory)
    assert set(actual) == set(seal['files']) | {'measure_seal.json'}
    assert all(actual[name] == value for name,value in seal['files'].items())
    meta = json.loads((directory/'run_metadata.json').read_text())
    assert meta['status'] == 'SUCCESS' and meta['stage'] == 'measure'
    assert meta['counters']['score_json_decoded'] == 0
    assert meta['counters']['score_hash_reads'] == 0
    assert meta['counters']['measurement_rows'] == 24
    assert meta['source_sha256'] == manifest['source_sha256']
    assert meta['manifest_sha256'] == sha(manifest_path)
    assert datetime.fromisoformat(meta['completed_utc']) <= datetime.fromisoformat(seal['sealed_utc'])
    return actual

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage',choices=['measure','associate','verify'],required=True)
    args = parser.parse_args()
    manifest_path = ROOT/'docs/S14C_EXECUTION_MANIFEST.json'
    manifest = json.loads(manifest_path.read_text())
    stage = manifest['stages'][args.stage]
    output = ROOT/stage['output']
    assert not output.exists(), 'Existing output must be preserved'
    receipt_dir = ROOT/'work/S14C_execution'/args.stage
    receipt_dir.mkdir(exist_ok=False)
    receipt_path = receipt_dir/'caller_receipt.json'
    receipt = dict(status='RUNNING',stage=args.stage,started_utc=now(),timeout_seconds=600,
                   score_access='Caller hashes score bytes for identity only; does not decode score JSON')
    save(receipt_path,receipt)
    expected = {i['path']:i['sha256'] for i in manifest['inputs']+manifest['controls']+[manifest['score_input']]}
    expected['docs/S14C_EXECUTION_MANIFEST.json'] = sha(manifest_path)
    measure_dir = ROOT/manifest['stages']['measure']['output']
    associate_dir = ROOT/manifest['stages']['associate']['output']
    try:
        receipt['identity_before'] = {p:sha(ROOT/p) for p in expected}
        assert receipt['identity_before'] == expected, 'Frozen input/control identity mismatch'
        receipt['bound_file_count'] = len(expected)
        command = [str(ROOT/'.venv/bin/python'),str(ROOT/stage['script'])]
        if args.stage != 'measure':
            receipt['measure_files_before'] = seal_check(measure_dir,manifest_path,manifest)
            receipt['measure_seal_verified_utc'] = now()
        if args.stage == 'verify':
            assert json.loads((associate_dir/'run_metadata.json').read_text())['status']=='SUCCESS'
            receipt['associate_files_before'] = files(associate_dir)
            command += ['--manifest',str(manifest_path),'--measure',str(measure_dir),
                        '--associate',str(associate_dir),'--output',str(output)]
        else:
            command += ['--stage',args.stage,'--manifest',str(manifest_path),'--output',str(output)]
            if args.stage == 'associate':
                command += ['--input-result',str(measure_dir)]
        receipt.update(command=command,spawned_utc=now())
        save(receipt_path,receipt)
        with (receipt_dir/'stdout.txt').open('x') as stdout,(receipt_dir/'stderr.txt').open('x') as stderr:
            process = subprocess.Popen(command,cwd=ROOT,stdout=stdout,stderr=stderr,start_new_session=True)
            try:
                receipt['exit_code'] = process.wait(timeout=600)
            except subprocess.TimeoutExpired:
                receipt['timed_out'] = True
                os.killpg(process.pid,signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid,signal.SIGKILL)
                    process.wait()
                receipt['exit_code'] = process.returncode
                raise
        receipt['child_finished_utc'] = now()
        rss = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
        receipt['child_peak_rss_bytes'] = int(rss if sys.platform == 'darwin' else rss*1024)
        assert receipt['exit_code'] == 0, 'Stage failed; preserve all available output'
        record_path = output/('verification.json' if args.stage == 'verify' else 'run_metadata.json')
        result = json.loads(record_path.read_text())
        assert result['status'] == ('PASS' if args.stage == 'verify' else 'SUCCESS')
        if args.stage == 'measure':
            receipt['measure_files_after'] = seal_check(output,manifest_path,manifest)
            assert result['counters']['measurement_csv_decoded'] == 2
            assert result['counters']['measurement_json_decoded'] == 30
        elif args.stage == 'associate':
            assert result['counters']['score_json_decoded'] == 1
            assert result['counters']['joined_rows'] == 24 and result['counters']['correlations'] == 32
            assert datetime.fromisoformat(result['measurement_seal_verified_utc']) <= datetime.fromisoformat(result['score_first_read_utc'])
        if args.stage != 'measure':
            receipt['measure_files_after'] = files(measure_dir)
            assert receipt['measure_files_after'] == receipt['measure_files_before']
        if args.stage == 'verify':
            receipt['associate_files_after'] = files(associate_dir)
            assert receipt['associate_files_after'] == receipt['associate_files_before']
        receipt.update(status='PASS',result_receipt_sha256=sha(record_path))
    except BaseException as exc:
        receipt.update(status='FAIL',exception=repr(exc),traceback=traceback.format_exc())
    finally:
        receipt['identity_after'] = {p:sha(ROOT/p) if (ROOT/p).is_file() else None for p in expected}
        receipt['identity_unchanged'] = receipt.get('identity_before') == expected == receipt['identity_after']
        if not receipt['identity_unchanged']:
            receipt['status'] = 'FAIL'
        receipt['ended_utc'] = now()
        save(receipt_path,receipt)
    print(json.dumps({k:receipt[k] for k in ['stage','status','started_utc','ended_utc','identity_unchanged']}))
    if receipt['status'] != 'PASS':
        sys.exit(1)

if __name__ == '__main__':
    main()
