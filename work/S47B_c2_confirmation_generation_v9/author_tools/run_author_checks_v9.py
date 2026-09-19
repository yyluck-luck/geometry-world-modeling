from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,os,subprocess,time
D=Path(__file__).resolve().parents[1];R=D.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
now=lambda:datetime.now(timezone.utc).isoformat()
results=[]
for name,exe in [('py312',R/'.venv-cut3r/bin/python'),('py313',Path('/opt/homebrew/bin/python3'))]:
    stdout=D/'author_tools'/f'{name}.stdout.json';stderr=D/'author_tools'/f'{name}.stderr.txt'
    argv=[str(exe),'-I','-B','-S',str(D/'static_selftest.py')]
    started=now();t0=time.monotonic()
    with stdout.open('xb') as out,stderr.open('xb') as err:
        proc=subprocess.run(argv,cwd='/private/tmp',stdout=out,stderr=err,timeout=60)
    completed=now();elapsed=time.monotonic()-t0
    reported=json.loads(stdout.read_text()) if proc.returncode==0 else None
    result={'name':name,'argv':argv,'cwd':'/private/tmp','started_utc':started,'completed_utc':completed,'elapsed_seconds':elapsed,'returncode':proc.returncode,'stdout_path':str(stdout),'stdout_sha256':sha(stdout),'stderr_path':str(stderr),'stderr_sha256':sha(stderr),'reported_status':None if reported is None else reported['status'],'reported_python':None if reported is None else reported['python'],'candidate_sha256':None if reported is None else reported['candidate_sha256'],'static_selftest_sha256':sha(D/'static_selftest.py')}
    results.append(result)
with (D/'AUTHOR_TEST_RUNS_V9.json').open('x') as f:json.dump({'author_role':'/root/c2_v9_recovery_author','completed_utc':now(),'runs':results,'new_test_cases':0,'repeat_runs':0,'model_calls':0,'scientific_image_or_tensor_reads':0,'formal_prepare_attach_authorization_launch_calls':0},f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps([{k:r[k] for k in ['name','returncode','reported_status','elapsed_seconds']} for r in results],indent=2))
assert all(r['returncode']==0 and r['reported_status']=='PASS_S47_C2_V9_CANDIDATE_STATIC_SELFTEST' for r in results)
