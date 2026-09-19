"""Runtime-only transport retry, retaining the original total600s deadline."""
from pathlib import Path
import datetime as dt
import hashlib,json,os,signal,subprocess,time
BASE=Path(__file__).parent;D=BASE/'retry_02'
first=json.loads((BASE/'external_receipt.json').read_text());prior=json.loads((BASE/'receipt.json').read_text());assert prior['archive_body_bytes']==0
assert json.loads((BASE/'retry_01/receipt.json').read_text())['archive_body_bytes']==0
first_start=dt.datetime.fromisoformat(first['started_utc'])
remaining=600-(dt.datetime.now(dt.timezone.utc)-first_start).total_seconds();assert remaining>0
argv=['/opt/homebrew/opt/python@3.13/bin/python3.13','-B',str(BASE/'fetch_and_probe_asset_retry.py')]
env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',NUMEXPR_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
start=time.monotonic();r={'started_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'original_window_started_utc':first['started_utc'],'remaining_external_timeout_seconds':remaining,'total_external_window_seconds':600,'argv':argv,'source_sha256':hashlib.sha256((BASE/'fetch_and_probe_asset_retry.py').read_bytes()).hexdigest(),'wrapper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'timeout':False}
with (D/'stdout.txt').open('xb') as out,(D/'stderr.txt').open('xb') as err:
 p=subprocess.Popen(argv,stdout=out,stderr=err,env=env,start_new_session=True);r['pid']=p.pid
 (D/'started.json').write_text(json.dumps(r,indent=2)+'\n')
 try:r['returncode']=p.wait(timeout=remaining)
 except subprocess.TimeoutExpired:
  r['timeout']=True;os.killpg(p.pid,signal.SIGKILL);r['returncode']=p.wait()
r.update(completed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),elapsed_seconds=time.monotonic()-start,elapsed_from_first_start_seconds=(dt.datetime.now(dt.timezone.utc)-first_start).total_seconds())
with (D/'external_receipt.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r));raise SystemExit(0 if r['returncode']==0 and not r['timeout'] else 1)
