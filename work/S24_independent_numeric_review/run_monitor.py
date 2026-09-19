#!/usr/bin/env python3
"""Bounded CPU1/180sec/1GiB execution of this directory's numeric review."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone
import psutil

D=Path(__file__).resolve().parent
target=D/'caller_receipt.json'
if target.exists(): raise FileExistsError('Refuse existing caller receipt')
env=dict(os.environ)
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):env[key]='1'
now=lambda:datetime.now(timezone.utc).isoformat()
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
command=[sys.executable,str(D/'recompute.py')]
r={'status':'RUNNING','started_utc':now(),'command':command,'cpu_threads':1,'timeout_seconds':180,'rss_limit_bytes':1024**3,'peak_tree_rss_bytes':0,'source_sha256':digest(D/'recompute.py'),'monitor_sha256':digest(Path(__file__))}
target.write_text(json.dumps(r,indent=2)+'\n')
t0=time.monotonic()
with (D/'stdout.txt').open('x') as stdout,(D/'stderr.txt').open('x') as stderr:
 p=subprocess.Popen(command,cwd=D.parents[1],env=env,stdout=stdout,stderr=stderr)
 r['pid']=p.pid; failure=None
 while p.poll() is None:
  try:
   process=psutil.Process(p.pid); processes=[process]+process.children(recursive=True)
   rss=sum(x.memory_info().rss for x in processes if x.is_running())
   r['peak_tree_rss_bytes']=max(r['peak_tree_rss_bytes'],rss)
   if rss>1024**3:failure='RSS exceeded 1 GiB'
  except psutil.NoSuchProcess:pass
  if time.monotonic()-t0>180:failure='Wall time exceeded 180 seconds'
  if failure:
   for x in reversed(processes):
    try:x.kill()
    except psutil.NoSuchProcess:pass
   p.wait();break
  time.sleep(.02)
 r.update(returncode=p.wait(),completed_utc=now(),elapsed_seconds=time.monotonic()-t0)
 if failure:r['failure']=failure
 r['status']='PASS' if r['returncode']==0 and not failure else 'FAIL'
 r['source_unchanged']=r['source_sha256']==digest(D/'recompute.py')
 if not r['source_unchanged']:r['status']='FAIL'
 r['outputs']={q.name:digest(q) for q in (D/'receipt.json',D/'stdout.txt',D/'stderr.txt') if q.exists()}
 target.write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2))
sys.exit(0 if r['status']=='PASS' else 1)
