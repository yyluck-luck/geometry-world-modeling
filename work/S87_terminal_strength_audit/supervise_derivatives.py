"""Run the sealed S87 generator once with bounded process-tree supervision."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time
import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
def utc(): return datetime.now(timezone.utc).isoformat()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze-sha256', required=True)
    args = parser.parse_args()
    freeze_path = HERE/'ROOT_EXECUTION_FREEZE.json'
    assert sha(freeze_path) == args.freeze_sha256
    freeze = json.loads(freeze_path.read_text())
    assert freeze['accepted'] is True
    assert sha(Path(__file__)) == freeze['supervisor_sha256']
    contract_path = HERE/'GENERATION_CONTRACT.json'
    assert sha(contract_path) == freeze['generation_contract_sha256']
    cfg = json.loads(contract_path.read_text())
    runner = HERE/'generate_terminal_controls.py'
    assert sha(runner) == cfg['runner_sha256'] == freeze['runner_sha256']
    assert not (HERE/'execution_01').exists()
    assert shutil.disk_usage(HERE).free >= cfg['budget']['initial_free_bytes']
    out = HERE/'supervision_01'; out.mkdir(exist_ok=False)
    command = [str(ROOT/'.venv-cut3r/bin/python'), '-I', str(runner),
               '--contract-sha256', freeze['generation_contract_sha256']]
    state = dict(status='RUNNING', started_utc=utc(), freeze_sha256=args.freeze_sha256,
                 command=command, signals=[], peak_tree_rss_bytes=0)
    began=time.monotonic();proc=None
    def save():
        p=out/'SUPERVISION.tmp';p.write_text(json.dumps(state,indent=2)+'\n')
        p.replace(out/'SUPERVISION.json')
    def stop():
        if proc is None or proc.poll() is not None:return
        try:os.killpg(proc.pid,signal.SIGTERM)
        except ProcessLookupError:return
        state['signals'].append(dict(utc=utc(),signal='SIGTERM'))
        try:proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGKILL)
            state['signals'].append(dict(utc=utc(),signal='SIGKILL'));proc.wait()
    save()
    try:
        with (out/'STDOUT.txt').open('x') as stdout,(out/'STDERR.txt').open('x') as stderr, \
             (out/'monitor.jsonl').open('x',buffering=1) as monitor:
            proc=subprocess.Popen(command,stdout=stdout,stderr=stderr,cwd=ROOT,start_new_session=True)
            state['pid']=proc.pid;save()
            while proc.poll() is None:
                elapsed=time.monotonic()-began;rss=0
                try:
                    parent=psutil.Process(proc.pid)
                    for child in [parent]+parent.children(recursive=True):
                        try:rss+=child.memory_info().rss
                        except psutil.NoSuchProcess:pass
                except psutil.NoSuchProcess:pass
                state['peak_tree_rss_bytes']=max(state['peak_tree_rss_bytes'],rss)
                row=dict(utc=utc(),elapsed_seconds=elapsed,tree_rss_bytes=rss)
                progress=HERE/'execution_01/progress.jsonl'
                if progress.exists():
                    lines=progress.read_text().splitlines()
                    if lines:
                        try:row['worker']=json.loads(lines[-1])
                        except json.JSONDecodeError:pass
                reason=None
                if elapsed>600:reason='total_wall_seconds'
                elif rss>16*1024**3:reason='sampled_tree_RSS'
                worker=row.get('worker',{})
                if str(worker.get('arm','')).startswith('Gterminal') and worker.get('arm_elapsed_seconds') is not None:
                    terminal_elapsed=worker['arm_elapsed_seconds']+max(0,elapsed-worker['elapsed_seconds'])
                    if terminal_elapsed>120:reason='terminal_wall_seconds'
                monitor.write(json.dumps(row)+'\n');state['last_poll']=row;save()
                if reason:state['limit_rejection']=reason;stop();break
                time.sleep(2)
            state['returncode']=proc.wait()
        receipt=HERE/'execution_01/RECEIPT.json'
        worker=json.loads(receipt.read_text()) if receipt.exists() else {}
        state['worker_receipt_sha256']=sha(receipt) if receipt.exists() else None
        state['worker_status']=worker.get('status','NO_RECEIPT')
        if worker.get('elapsed_seconds',0)>600:state['limit_rejection']='total_wall_at_exit'
        if worker.get('peak_self_rss_bytes',0)>16*1024**3:state['limit_rejection']='RSS_at_exit'
        if worker.get('output_bytes_before_final_receipt',0)>1024**3:state['limit_rejection']='output_at_exit'
        state['status']='COMPLETE' if state['returncode']==0 and 'limit_rejection' not in state and \
            state['worker_status']=='COMPLETE_SIX_DERIVED_CONTROLS_PENDING_REVIEW' else 'FAILED'
    except BaseException as exc:
        state.update(status='FAILED',error=repr(exc));stop()
    finally:
        state.update(completed_utc=utc(),elapsed_seconds=time.monotonic()-began);save()
    print(json.dumps(state),flush=True)
    return 0 if state['status']=='COMPLETE' else 1

if __name__=='__main__':raise SystemExit(main())
