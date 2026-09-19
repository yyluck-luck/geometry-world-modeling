"""Supervise exactly one S86 process tree; no automatic repeat."""
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

W = Path(__file__).resolve().parent
R = W.parents[1]
def utc(): return datetime.now(timezone.utc).isoformat()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--contract-sha256',required=True)
    args=ap.parse_args()
    contract=W/'CONTRACT.json'
    assert sha(contract)==args.contract_sha256
    cfg=json.loads(contract.read_text())
    runner=W/'generate_with_fixed_warp.py'
    assert sha(runner)==cfg['runner_sha256']
    assert sha(Path(__file__))==cfg['supervisor_sha256']
    assert not (W/'execution_01').exists()
    control=W/'supervision_01';control.mkdir(exist_ok=False)
    command=[str(R/'.venv-cut3r/bin/python'),'-I',str(runner)]
    limits=cfg['budget']
    state=dict(status='RUNNING',started_utc=utc(),contract_sha256=args.contract_sha256,
               command=command,supervisor_sha256=sha(Path(__file__)),limits=limits,
               signals=[],peak_tree_rss_bytes=0)
    started=time.monotonic();proc=None
    def save():
        temp=control/'SUPERVISION.tmp'
        temp.write_text(json.dumps(state,indent=2)+'\n')
        temp.replace(control/'SUPERVISION.json')
    def stop():
        if proc is None or proc.poll() is not None:return
        try:
            os.killpg(proc.pid,signal.SIGTERM);state['signals'].append(dict(utc=utc(),signal='SIGTERM'))
        except ProcessLookupError:return
        try:proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGKILL);state['signals'].append(dict(utc=utc(),signal='SIGKILL'));proc.wait()
    save()
    try:
        with (control/'STDOUT.txt').open('x') as out,(control/'STDERR.txt').open('x') as err,(control/'monitor.jsonl').open('x',buffering=1) as monitor:
            proc=subprocess.Popen(command,stdout=out,stderr=err,cwd=R,start_new_session=True)
            state['pid']=proc.pid;save()
            while proc.poll() is None:
                elapsed=time.monotonic()-started
                rss=0
                try:
                    parent=psutil.Process(proc.pid)
                    for p in [parent]+parent.children(recursive=True):
                        try:rss+=p.memory_info().rss
                        except psutil.NoSuchProcess:pass
                except psutil.NoSuchProcess:pass
                state['peak_tree_rss_bytes']=max(state['peak_tree_rss_bytes'],rss)
                row=dict(utc=utc(),elapsed_seconds=elapsed,tree_rss_bytes=rss,free_disk_bytes=shutil.disk_usage(W).free)
                progress=W/'execution_01/progress.jsonl'
                if progress.exists():
                    lines=progress.read_text().splitlines()
                    if lines:
                        try:row['worker']=json.loads(lines[-1])
                        except json.JSONDecodeError:pass
                reason=None
                if elapsed>limits['total_seconds']:reason='total_wall_seconds'
                elif rss>limits['rss_bytes']:reason='sampled_tree_RSS'
                elif row['free_disk_bytes']<limits['minimum_free_bytes']:reason='disk_reserve'
                w=row.get('worker',{})
                if w.get('arm_elapsed_seconds') is not None:
                    arm_elapsed=w['arm_elapsed_seconds']+max(0,elapsed-w['elapsed_seconds'])
                    if arm_elapsed>limits['per_arm_seconds']:reason='arm_wall_seconds'
                monitor.write(json.dumps(row)+'\n')
                state['last_poll']=row;save()
                if reason:
                    state['limit_rejection']=reason;stop();break
                time.sleep(5)
            state['returncode']=proc.wait()
        receipt=W/'execution_01/RECEIPT.json'
        worker=json.loads(receipt.read_text()) if receipt.exists() else {}
        state['worker_receipt_sha256']=sha(receipt) if receipt.exists() else None
        state['worker_status']=worker.get('status','NO_RECEIPT')
        if worker.get('elapsed_seconds',0)>limits['total_seconds']:state['limit_rejection']='total_wall_at_exit'
        if worker.get('peak_self_rss_bytes',0)>limits['rss_bytes']:state['limit_rejection']='self_RSS_at_exit'
        state['status']='COMPLETE' if state['returncode']==0 and 'limit_rejection' not in state and state['worker_status']=='COMPLETE_FOUR_FIXED_CONSUMER_ARMS_PENDING_REVIEW' else 'FAILED'
    except BaseException as e:
        state.update(status='FAILED',supervisor_error=repr(e));stop()
    finally:
        state.update(completed_utc=utc(),elapsed_seconds=time.monotonic()-started);save()
    print(json.dumps(state),flush=True)
    return 0 if state['status']=='COMPLETE' else 1

if __name__=='__main__':raise SystemExit(main())
