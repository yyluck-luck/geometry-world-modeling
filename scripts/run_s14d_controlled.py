#!/usr/bin/env python3
"""Single external CPU probe caller with wall-clock/RSS limits and identity checks."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time
import traceback


def sha(path):
    with Path(path).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()


def utc(): return datetime.now(timezone.utc).isoformat()


def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--control',type=Path,required=True)
    a=p.parse_args(); assert not a.output.exists() and not a.control.exists()
    a.control.mkdir(parents=True)
    m=json.loads(a.manifest.read_text()); hashes=m['identities']; msh=sha(a.manifest)
    assert hashes[str(Path(__file__).resolve())]==sha(__file__)
    cmd=[m['python'],m['runner'],'--manifest',str(a.manifest),'--output',str(a.output)]
    receipt=dict(schema='s14d-caller-v1',started_utc=utc(),manifest_sha256=msh,command=cmd,
                 status='RUNNING',timed_out=False,rss_limit_exceeded=False,
                 limits=dict(seconds=600,rss_bytes=32*1024**3),maxrss=0,
                 before_after_identity_pass=False,monitor_ok=False,returncode=None)
    def save(): (a.control/'caller_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    def stop():
        if process is not None and process.poll() is None:
            process.terminate()
            try:process.wait(timeout=10)
            except subprocess.TimeoutExpired:process.kill();process.wait()
    start=time.monotonic()
    process=None;save()
    try:
        before={path:sha(path) for path in hashes}; assert before==hashes
        with (a.control/'stdout.txt').open('w') as out,(a.control/'stderr.txt').open('w') as err:
            process=subprocess.Popen(cmd,stdout=out,stderr=err)
            receipt['pid']=process.pid;save()
            while process.poll() is None:
                sample=subprocess.run(['/bin/ps','-o','rss=','-p',str(process.pid)],capture_output=True,text=True,timeout=5)
                value=sample.stdout.strip()
                if value:
                    if sample.returncode!=0 or not value.isdecimal():raise RuntimeError('RSS monitor failed')
                    receipt['maxrss']=max(receipt['maxrss'],int(value)*1024)
                elif process.poll() is None:raise RuntimeError('Live process has no RSS sample')
                if time.monotonic()-start>600:receipt['timed_out']=True
                if receipt['maxrss']>32*1024**3:receipt['rss_limit_exceeded']=True
                if receipt['timed_out'] or receipt['rss_limit_exceeded']:
                    stop();break
                time.sleep(.5)
            receipt['returncode']=process.wait()
        receipt['monitor_ok']=receipt['maxrss']>0
        after={path:sha(path) for path in hashes}
        receipt['before_after_identity_pass']=before==after==hashes and sha(a.manifest)==msh
        receipt['status']='PASS' if receipt['returncode']==0 and receipt['monitor_ok'] and not receipt['timed_out'] and not receipt['rss_limit_exceeded'] and receipt['before_after_identity_pass'] else 'FAILED'
    except BaseException as error:
        receipt.update(status='FAILED',error=repr(error),traceback=traceback.format_exc())
    finally:
        stop()
        if process is not None:receipt['returncode']=process.returncode
        receipt['elapsed_seconds']=time.monotonic()-start
        receipt['completed_utc']=utc();save()
    print(json.dumps(receipt));return int(receipt['status']!='PASS')


if __name__=='__main__':raise SystemExit(main())
