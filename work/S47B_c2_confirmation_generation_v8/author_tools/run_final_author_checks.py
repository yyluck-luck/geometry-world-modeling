from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,subprocess,os
base=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def run(name,exe):
 start=datetime.now(timezone.utc).isoformat();cmd=[exe,'-I','-B','-S',str(base/'static_selftest.py')]
 result=subprocess.run(cmd,cwd='/private/tmp',capture_output=True,timeout=120)
 end=datetime.now(timezone.utc).isoformat();out=base/'author_tools'/('final_'+name+'.stdout.json');err=base/'author_tools'/('final_'+name+'.stderr.txt')
 with out.open('xb') as h:h.write(result.stdout)
 with err.open('xb') as h:h.write(result.stderr)
 item={'name':name,'argv':cmd,'cwd':'/private/tmp','started_utc':start,'completed_utc':end,'returncode':result.returncode,'stdout_path':str(out),'stdout_sha256':sha(out),'stderr_path':str(err),'stderr_sha256':sha(err)}
 if result.returncode==0:
  reported=json.loads(result.stdout);item['reported_status']=reported['status'];item['python']=reported['python'];item['candidate_sha256']=reported['candidate_sha256'];item['static_selftest_sha256']=reported['static_selftest_sha256'];item['metadata_fixture']=reported['checks']['actual_v7_metadata_producer_consumer_chain']
 return item
start=datetime.now(timezone.utc).isoformat()
with ThreadPoolExecutor(max_workers=2) as pool:
 futures=[pool.submit(run,'py313','/opt/homebrew/bin/python3'),pool.submit(run,'py312','/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/.venv-cut3r/bin/python')]
 results=[f.result() for f in futures]
p=base/'AUTHOR_TEST_RUNS_V8.json'
with p.open('x') as h:json.dump({'started_utc':start,'completed_utc':datetime.now(timezone.utc).isoformat(),'author_role':'/root/c2_final_launch_readiness','runs':results},h,indent=2);h.write('\n')
print(json.dumps({'path':str(p),'sha256':sha(p),'runs':[{'name':r['name'],'returncode':r['returncode'],'status':r.get('reported_status'),'started_utc':r['started_utc'],'completed_utc':r['completed_utc']} for r in results]},indent=2))
assert all(r['returncode']==0 for r in results)
