"""One external600s wall-clock cap; kills only this new worker process group."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import signal
import subprocess
import time
D=Path(__file__).parent
argv=['/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/.venv-cut3r/bin/python','-B',str(D/'fetch_and_probe.py')]
env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',NUMEXPR_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
start=time.monotonic();r={'started_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'argv':argv,'external_timeout_seconds':600,'source_sha256':hashlib.sha256((D/'fetch_and_probe.py').read_bytes()).hexdigest(),'wrapper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'timeout':False}
with (D/'stdout.txt').open('xb') as out,(D/'stderr.txt').open('xb') as err:
 p=subprocess.Popen(argv,stdout=out,stderr=err,env=env,start_new_session=True);r['pid']=p.pid
 (D/'started.json').write_text(json.dumps(r,indent=2)+'\n')
 try:r['returncode']=p.wait(timeout=600)
 except subprocess.TimeoutExpired:
  r['timeout']=True;os.killpg(p.pid,signal.SIGTERM)
  try:r['returncode']=p.wait(timeout=5)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);r['returncode']=p.wait()
r.update(completed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),elapsed_seconds=time.monotonic()-start)
with (D/'external_receipt.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r))
raise SystemExit(0 if r['returncode']==0 and not r['timeout'] else 1)
