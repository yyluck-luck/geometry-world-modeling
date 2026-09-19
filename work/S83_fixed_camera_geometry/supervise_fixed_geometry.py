"""One local S83 process, fixed budget; never overwrites science outputs."""
import argparse, hashlib, json, os, signal, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path
import psutil
W = Path(__file__).resolve().parent
R = W.parents[1]
def utc(): return datetime.now(timezone.utc).isoformat()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--runner-sha256', required=True)
    ap.add_argument('--contract-sha256', required=True)
    a = ap.parse_args()
    runner, contract = W/'run_fixed_geometry.py', W/'CONTRACT.json'
    assert sha(runner) == a.runner_sha256 and sha(contract) == a.contract_sha256
    assert not (W/'execution_01').exists()
    control = W/'supervision_01'; control.mkdir(exist_ok=False)
    limits = {'wall_seconds':300, 'rss_bytes':8*1024**3, 'poll_seconds':0.1}
    command = [str(R/'.venv-cut3r/bin/python'), '-I', str(runner)]
    state = dict(started_utc=utc(), status='RUNNING', runner_sha256=a.runner_sha256,
                 contract_sha256=a.contract_sha256, supervisor_sha256=sha(Path(__file__)),
                 command=command, limits=limits, actual_signals_sent=[], peak_tree_rss_bytes=0)
    def save():
        tmp=control/'SUPERVISION.tmp';tmp.write_text(json.dumps(state,indent=2)+'\n')
        tmp.replace(control/'SUPERVISION.json')
    save(); proc=None; started=time.monotonic()
    try:
        with (control/'STDOUT.txt').open('x') as out, (control/'STDERR.txt').open('x') as err:
            proc=subprocess.Popen(command,stdout=out,stderr=err,start_new_session=True)
            state['pid']=proc.pid
            while proc.poll() is None:
                try:
                    parent=psutil.Process(proc.pid)
                    rss=sum(p.memory_info().rss for p in [parent]+parent.children(recursive=True))
                    state['peak_tree_rss_bytes']=max(state['peak_tree_rss_bytes'],rss)
                except psutil.NoSuchProcess: pass
                if time.monotonic()-started > 300 or state['peak_tree_rss_bytes'] > 8*1024**3:
                    state['limit_rejection']='wall_or_sampled_tree_RSS'
                    try:
                        os.killpg(proc.pid,signal.SIGTERM);state['actual_signals_sent'].append('SIGTERM')
                    except ProcessLookupError: pass
                    try: proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(proc.pid,signal.SIGKILL);state['actual_signals_sent'].append('SIGKILL');proc.wait()
                    break
                save();time.sleep(.1)
            state['returncode']=proc.wait()
        receipt=W/'execution_01/RECEIPT.json'
        worker=json.loads(receipt.read_text()) if receipt.exists() else {}
        state['worker_receipt_sha256']=sha(receipt) if receipt.exists() else None
        state['worker_status']=worker.get('status','NO_RECEIPT')
        if time.monotonic()-started > 300: state['limit_rejection']='wall_at_exit'
        if worker.get('peak_self_rss_bytes',0) > 8*1024**3: state['limit_rejection']='self_RSS_at_exit'
        state['status']='COMPLETE' if state['returncode']==0 and 'limit_rejection' not in state and state['worker_status']=='COMPLETED_FIXED_BUDGET_DIAGNOSTIC' else 'FAILED'
    except BaseException as exc:
        state.update(status='FAILED',supervisor_error=repr(exc))
        if proc is not None and proc.poll() is None:
            os.killpg(proc.pid,signal.SIGKILL);state['actual_signals_sent'].append('SIGKILL');proc.wait()
        raise
    finally:
        state.update(completed_utc=utc(),elapsed_seconds=time.monotonic()-started);save()
    print(json.dumps(state));return 0 if state['status']=='COMPLETE' else 1
if __name__=='__main__': raise SystemExit(main())
