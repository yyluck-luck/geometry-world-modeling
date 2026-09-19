"""Continue this live S24 experiment after its existing dispatcher completes.

One bounded dependent job, not a recurring scheduler. Never restarts a model.
Figures still require human/agent visual inspection before delivery.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
W = ROOT / 'work/S24_postprocess'
sys.path.append(str(ROOT / 'work/S17C_environment/site-packages'))
import psutil


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def write(p, value):
    p.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def prepare():
    W.mkdir(exist_ok=True)
    assert not (W / 'contract.json').exists()
    matches = []
    for proc in psutil.process_iter(['pid', 'create_time', 'cmdline']):
        args = proc.info['cmdline'] or []
        if any('scripts/s24_baseline_expansion.py' in a for a in args) and 'dispatch' in args:
            matches.append(dict(pid=proc.pid, create_time=proc.info['create_time'], cmdline=args))
    assert len(matches) == 1, 'Require the one verified live S24 dispatcher'
    identities = [Path(__file__).resolve(), ROOT / 'scripts/s24_horizon_diagnostic.py',
                  ROOT / 'scripts/plot_s24_baseline.py',
                  ROOT / 'work/S24_horizon_preparation/run_manifest.json',
                  ROOT / 'work/S24_baseline_expansion/run_manifest.json']
    for p in identities:
        assert p.exists(), str(p)
    contract = dict(created_utc=utc(), target=matches[0],
                    identities={str(p): sha(p) for p in identities},
                    max_wait_seconds=11000, poll_seconds=10,
                    phase_seconds=360, phase_rss_bytes=2*1024**3,
                    commands=[['scripts/s24_horizon_diagnostic.py', 'run', '--manifest-sha256', sha(ROOT / 'work/S24_horizon_preparation/run_manifest.json')],
                              ['scripts/plot_s24_baseline.py']],
                    model_restarts=0, visual_review='required after plotting')
    write(W / 'contract.json', contract)
    print(json.dumps(contract))


def run():
    assert not (W / 'receipt.json').exists(), 'Do not duplicate a dependent job'
    contract = json.loads((W / 'contract.json').read_text())
    for p, h in contract['identities'].items():
        assert sha(p) == h, p
    receipt = dict(started_utc=utc(), status='WAITING_ON_VERIFIED_DISPATCHER',
                   target=contract['target'], contract_sha256=sha(W / 'contract.json'), phases=[])
    write(W / 'receipt.json', receipt)
    start = time.monotonic()
    missing_count = 0
    try:
        while True:
            dispatcher = ROOT / 'work/S24_execution/dispatch_receipt.json'
            final = None
            if dispatcher.exists():
                try:
                    final = json.loads(dispatcher.read_text())
                except json.JSONDecodeError:
                    pass  # A just-started write may be observed once; bounded below.
            if final is not None:
                if final['status'] != 'PASS':
                    raise RuntimeError('S24 dispatcher terminated without complete scoring: ' + final['status'])
                break
            try:
                proc = psutil.Process(contract['target']['pid'])
                live = proc.create_time() == contract['target']['create_time'] and proc.is_running()
            except psutil.NoSuchProcess:
                live = False
            missing_count = 0 if live else missing_count+1
            if missing_count >= 3:
                raise RuntimeError('S24 dispatcher is no longer live and has no PASS result')
            if time.monotonic()-start > contract['max_wait_seconds']:
                raise RuntimeError('Bounded dependent-job wait expired; do not restart S24')
            receipt.update(last_checked_utc=utc(), target_verified_live=live,
                           wait_elapsed_seconds=time.monotonic()-start)
            write(W / 'receipt.json', receipt)
            time.sleep(contract['poll_seconds'])

        for p, h in contract['identities'].items():
            assert sha(p) == h, 'Input or code changed while waiting: ' + p
        for index, command in enumerate(contract['commands']):
            phase = dict(started_utc=utc(), command=[sys.executable, *command],
                         status='RUNNING', peak_tree_rss_bytes=0)
            receipt.update(status='PROCESSING', active_phase=index)
            write(W / 'receipt.json', receipt)
            phase_start = time.monotonic()
            with (W / f'phase_{index}_stdout.txt').open('w') as out, (W / f'phase_{index}_stderr.txt').open('w') as err:
                process = subprocess.Popen(phase['command'], cwd=ROOT, stdout=out, stderr=err)
                phase['pid'] = process.pid
                while process.poll() is None:
                    try:
                        parent = psutil.Process(process.pid)
                        rss = sum(p.memory_info().rss for p in [parent, *parent.children(recursive=True)])
                        phase['peak_tree_rss_bytes'] = max(phase['peak_tree_rss_bytes'], rss)
                    except psutil.NoSuchProcess:
                        continue
                    if time.monotonic()-phase_start > contract['phase_seconds'] or phase['peak_tree_rss_bytes'] > contract['phase_rss_bytes']:
                        phase['failure'] = 'phase resource limit'
                        process.terminate()
                        try:
                            process.wait(timeout=10)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait()
                        break
                    time.sleep(.5)
                phase.update(returncode=process.wait(), completed_utc=utc(),
                             elapsed_seconds=time.monotonic()-phase_start)
            phase['status'] = 'PASS' if phase['returncode'] == 0 and 'failure' not in phase else 'FAILED'
            receipt['phases'].append(phase)
            write(W / 'receipt.json', receipt)
            if phase['status'] != 'PASS':
                raise RuntimeError('Dependent phase failed; preserve outputs and stderr')
        receipt.update(status='COMPLETED_PENDING_VISUAL_REVIEW', completed_utc=utc(),
                       figures_are_not_yet_visually_verified=True)
        write(W / 'receipt.json', receipt)
        print(receipt['status'])
    except BaseException as error:
        receipt.update(status='FAILED', error=repr(error), completed_utc=utc())
        write(W / 'receipt.json', receipt)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'run'])
    args = parser.parse_args()
    prepare() if args.action == 'prepare' else run()
