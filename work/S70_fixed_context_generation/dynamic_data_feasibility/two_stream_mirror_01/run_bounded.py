"""New independent600-second process-group window, without touching S70's processes."""
from pathlib import Path
import datetime as dt
import hashlib,json,os,signal,subprocess,time
D=Path(__file__).parent
argv=['/opt/homebrew/opt/python@3.13/bin/python3.13','-B',str(D/'download_mirror_and_probe.py')]
env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',NUMEXPR_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
r={'started_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'argv':argv,'timeout_seconds':600,'timeout':False,'source_sha256':hashlib.sha256((D/'download_mirror_and_probe.py').read_bytes()).hexdigest(),'wrapper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()};start=time.monotonic()
with (D/'stdout.txt').open('xb') as out,(D/'stderr.txt').open('xb') as err:
 p=subprocess.Popen(argv,stdout=out,stderr=err,env=env,start_new_session=True);r['pid']=p.pid
 with (D/'started.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
 try:r['returncode']=p.wait(timeout=600)
 except subprocess.TimeoutExpired:r['timeout']=True;os.killpg(p.pid,signal.SIGKILL);r['returncode']=p.wait()
r.update(completed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),elapsed_seconds=time.monotonic()-start)
with (D/'external_receipt.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r));raise SystemExit(0 if r['returncode']==0 and not r['timeout'] else 1)
