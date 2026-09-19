from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,subprocess,time
R=Path(__file__).resolve().parents[3];D=R/'work/S45B_c1_numeric_camera_guard_supervised_v11';E=Path(__file__).resolve().parent
pythons=[('py313','/opt/homebrew/opt/python@3.13/bin/python3.13'),('py312',str(R/'.venv-cut3r/bin/python'))]
entries=[('worker','camera_guard.py',['--synthetic-self-test']),('supervisor','supervise_camera_guard.py',['--synthetic-self-test']),('integration','synthetic_selftest.py',[])]
def run(item):
 label,python,entry,name,args=item; start=datetime.now(timezone.utc).isoformat();t0=time.monotonic();argv=[python,'-I','-B','-S',str(D/name),*args]
 with (E/(label+'_'+entry+'.stdout.json')).open('xb') as out,(E/(label+'_'+entry+'.stderr.txt')).open('xb') as err:
  p=subprocess.run(argv,cwd=R,stdout=out,stderr=err,timeout=120)
 result={'python_label':label,'entry':entry,'argv':argv,'started_utc':start,'completed_utc':datetime.now(timezone.utc).isoformat(),'elapsed_seconds':time.monotonic()-t0,'returncode':p.returncode}
 for key,suffix in [('stdout','stdout.json'),('stderr','stderr.txt')]:
  q=E/(label+'_'+entry+'.'+suffix);body=q.read_bytes();result[key]={'path':str(q.relative_to(R)),'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body)}
 print(json.dumps(result),flush=True);return result
items=[(label,python,entry,name,args) for label,python in pythons for entry,name,args in entries]
with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(run,items))
with (E/'FINITE_CHECK_RESULTS.json').open('x') as f:json.dump(results,f,indent=2);f.write('\n')
raise SystemExit(0 if all(x['returncode']==0 for x in results) else 2)
