"""One bounded original-weight transfer; existing CLIP must finish first."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import queue
import signal
import subprocess
import threading
import time
from download_original import ROOT, HERE, TARGET, SIZE, SHA, REVISION, safe

OUT = HERE / 'vmem_low_concurrency_attempt3'
BUDGET = 1800
SETTINGS = dict(HF_HUB_DISABLE_XET='0', HF_XET_HIGH_PERFORMANCE='0',
    HF_XET_FIXED_DOWNLOAD_CONCURRENCY='1', HF_XET_DATA_MAX_CONCURRENT_FILE_DOWNLOADS='1',
    HF_XET_CLIENT_RETRY_MAX_ATTEMPTS='1')

def utc():
    return datetime.now(timezone.utc).isoformat()

def main():
    OUT.mkdir(exist_ok=False)
    receipt = dict(started_utc=utc(), status='PRECHECK', attempt=3,
        repo='liguang0115/vmem', revision=REVISION, target=str(TARGET),
        expected_bytes=SIZE, expected_sha256=SHA, external_total_seconds=BUDGET,
        settings=SETTINGS, no_outer_retry=True, scientific_execution=False,
        internal_retry_scope='first plus at most one retry per wrapped request, not per whole file',
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        imported_helper_sha256=hashlib.sha256((HERE/'download_original.py').read_bytes()).hexdigest())
    def save():
        temp=OUT/'receipt.tmp';temp.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');temp.replace(OUT/'receipt.json')
    save(); child=None; reader=None; start=None
    try:
        companion=json.loads((HERE/'companion_download_receipt.json').read_text())
        if companion['status']!='ALL_COMPANIONS_VERIFIED':
            raise RuntimeError('Current companion transfer not verified terminal; do not start concurrent large transfer')
        for asset in companion['assets']:
            p=Path(asset['path'])
            if not p.is_file() or p.stat().st_size!=asset['bytes'] or asset['actual_sha256']!=asset['sha256']:
                raise RuntimeError('Companion completed evidence or current file size changed')
        receipt['companion_receipt_sha256']=hashlib.sha256((HERE/'companion_download_receipt.json').read_bytes()).hexdigest()
        env=os.environ.copy(); env.update(SETTINGS)
        env.update(HF_HOME='/Users/rocket/.cache/huggingface-research-s39',HF_HUB_DISABLE_TELEMETRY='1',
            HF_HUB_DISABLE_UPDATE_CHECK='1',HTTPS_PROXY='http://127.0.0.1:7897',HTTP_PROXY='http://127.0.0.1:7897')
        command=[str(HERE/'cli-env/bin/hf'),'download','liguang0115/vmem','vmem_weights.pth',
            '--revision',REVISION,'--local-dir',str(TARGET.parent),'--max-workers','1']
        start=time.monotonic(); receipt.update(status='RUNNING',download_started_utc=utc())
        child=subprocess.Popen(command,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
            text=True,bufsize=1,start_new_session=True)
        receipt['child_pid']=child.pid; receipt['process_group']=child.pid;save()
        q=queue.Queue()
        def collect():
            try:
                for line in child.stdout:q.put(safe(line))
            finally:q.put(None)
        reader=threading.Thread(target=collect,daemon=True);reader.start(); eof=False
        with (OUT/'download_redacted.log').open('x') as log:
            while not (eof and child.poll() is not None):
                if time.monotonic()-start>=BUDGET:
                    raise TimeoutError('External total deadline reached; no automatic restart')
                try: line=q.get(timeout=0.25)
                except queue.Empty: continue
                if line is None:eof=True;continue
                log.write(line);log.flush();print(line,end='',flush=True)
        code=child.wait();receipt.update(download_exit_code=code,download_finished_utc=utc(),
            download_wall_seconds=time.monotonic()-start,status='DOWNLOAD_FAILED')
        if code!=0: return 1
        if not TARGET.is_file():raise RuntimeError('CLI exited successfully but target absent')
        before=TARGET.stat();receipt['actual_bytes']=before.st_size;digest=hashlib.sha256()
        with TARGET.open('rb') as f:
            for chunk in iter(lambda:f.read(8*1024*1024),b''):
                if time.monotonic()-start>=BUDGET:raise TimeoutError('Total deadline during full hash; complete-file identity still pending')
                digest.update(chunk)
        after=TARGET.stat();receipt.update(actual_sha256=digest.hexdigest(),hash_finished_utc=utc())
        stable=(before.st_size,before.st_mtime_ns,before.st_ino,before.st_ctime_ns)==(after.st_size,after.st_mtime_ns,after.st_ino,after.st_ctime_ns)
        receipt['file_stable_during_hash']=stable
        receipt['status']='VERIFIED_COMPLETE_ORIGINAL_WEIGHT' if stable and before.st_size==SIZE and digest.hexdigest()==SHA else 'FILE_IDENTITY_MISMATCH'
        return 0 if receipt['status']=='VERIFIED_COMPLETE_ORIGINAL_WEIGHT' else 1
    except BaseException as exc:
        receipt.update(status='TIMED_OUT' if isinstance(exc,TimeoutError) else 'INTERRUPTED' if isinstance(exc,KeyboardInterrupt) else 'FAILED',
            error_type=type(exc).__name__,error=safe(str(exc)))
        return 1
    finally:
        if child is not None:
            def group_alive():
                try:os.killpg(child.pid,0);return True
                except ProcessLookupError:return False
            signals=[]
            for sig, wait in [(signal.SIGTERM,5),(signal.SIGKILL,10)]:
                child.poll()  # Reap an exited leader independently of remaining group members.
                if not group_alive():break
                try:os.killpg(child.pid,sig);signals.append(signal.Signals(sig).name)
                except ProcessLookupError:break
                until=time.monotonic()+wait
                while time.monotonic()<until:
                    child.poll()
                    if not group_alive():break
                    time.sleep(0.1)
            receipt.update(cleanup_signals=signals,child_exit_code=child.poll(),
                child_still_alive=child.poll() is None,group_still_alive=group_alive())
        if reader is not None:reader.join(timeout=1)
        receipt.update(finished_utc=utc(),total_wall_seconds=time.monotonic()-start if start else 0)
        if receipt.get('group_still_alive') or receipt.get('child_still_alive'):
            receipt['status_before_cleanup_failure']=receipt['status'];receipt['status']='CLEANUP_FAILED'
        save();print(json.dumps(receipt,ensure_ascii=False),flush=True)
        if receipt['status']=='CLEANUP_FAILED':return 1

if __name__=='__main__':
    raise SystemExit(main())
