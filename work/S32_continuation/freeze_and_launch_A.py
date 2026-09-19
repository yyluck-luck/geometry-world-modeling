"""Root freeze and single bounded A dispatch after two source reviews."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
PREP = ROOT/'work/S32_preparation'
OUT = ROOT/'work/S32_A_launch'

def now(): return datetime.now(timezone.utc).isoformat()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text())
def write(p,x): Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

candidate = PREP/'contract_candidate.json'
assert sha(candidate)=='7c9612253d32d18bb3da09f51212c33ade65b3255c460e80770b08e31be226a6'
c=read(candidate)
review=ROOT/'work/S32_independent_review/A_final_pre_review.json'
assert sha(review)=='493faa306701194d5be3932bee956ca3eaf9680890da8b47202f1db018039058'
r=read(review)
assert r['status']=='PASS_A_SOURCE_PRE_REVIEW' and r['passed'] is True
assert r['runner_sha256']==sha(c['runner'])=='6246b7255a324653279429be770dcc7c07a478729bea9d172b182cb35fb7851d'
assert r['candidate_sha256']==sha(candidate)
root_review=ROOT/'work/S32_continuation/root_pre_review.json'
assert read(root_review)['runner_sha256']==r['runner_sha256']
for path,h in c['identities'].items(): assert sha(path)==h,path
contract=PREP/'contract.json'
assert not contract.exists() and not Path(c['output_root']).exists() and not Path(c['execution_root']).exists()
OUT.mkdir(exist_ok=False)
c.update(status='FROZEN',frozen_utc=now(),candidate_sha256=sha(candidate),independent_review=str(review),root_review=str(root_review))
c['identities'].update({str(review):sha(review),str(root_review):sha(root_review)})
write(contract,c)
receipt=dict(status='FROZEN_BEFORE_DISPATCH',frozen_utc=c['frozen_utc'],contract=str(contract),contract_sha256=sha(contract),launcher_sha256=sha(__file__),independent_review_sha256=sha(review),root_review_sha256=sha(root_review),scientific_execution_completed=False)
write(OUT/'receipt.json',receipt)
sys.path.insert(0,str(ROOT/'scripts'))
from research_log import append_event
append_event('S32A 两作者前审后冻结并启动真实推理','固定四窗16RGB，原VMem embedded inference/PIL/eval，一窗一个新进程；复用已有CPU RoPE，CPU8/外控180秒与16GiB每窗。模型结果和准确性尚未完成；0GA/0sensor-depth评分。缺pose窗仍执行A，B保持NA。',evidence=[str(contract),str(review),str(OUT/'receipt.json')],next_step='检查实际四窗完整头存档与进程退出，再冻结B三个共同初态对照。',occurred_at=c['frozen_utc'],time_source='actual root freeze UTC immediately before launch')
env=os.environ.copy()
for key in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS']: env[key]='8'
command=[str(ROOT/'.venv-cut3r/bin/python'),c['runner'],'dispatch','--contract',str(contract),'--sha256',sha(contract)]
receipt.update(status='RUNNING',started_utc=now(),command=command,thread_environment={k:env[k] for k in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS']})
write(OUT/'receipt.json',receipt)
print(json.dumps({'status':'RUNNING','contract_sha256':sha(contract),'started_utc':receipt['started_utc']}),flush=True)
with (OUT/'stdout.txt').open('w') as out,(OUT/'stderr.txt').open('w') as err:
    process=subprocess.Popen(command,cwd=ROOT,env=env,stdout=out,stderr=err)
    receipt['pid']=process.pid;write(OUT/'receipt.json',receipt)
    returncode=process.wait()
receipt.update(status='PASS_A_INFERENCE_ONLY' if returncode==0 else 'FAILED',completed_utc=now(),returncode=returncode,scientific_execution_completed=returncode==0)
write(OUT/'receipt.json',receipt)
append_event('S32A 实际推理进程退出',f'实际dispatch退出码{returncode}；状态{receipt["status"]}。详情以各窗head与外控回执为准；尚未进行B几何优化或sensor-depth评分。',evidence=[str(OUT/'receipt.json'),str(Path(c['execution_root'])/'dispatch_receipt.json')],next_step='核验全部结果/失败，再接B，不重复成功窗口。',occurred_at=receipt['completed_utc'],time_source='actual subprocess wait and local UTC clock')
print(json.dumps(receipt,ensure_ascii=False),flush=True)
sys.exit(returncode)
