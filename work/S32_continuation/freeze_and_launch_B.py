"""Root freezes the reviewed B source and launches one bounded fixed matrix."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime,timezone
ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
PREP=ROOT/'work/S32_preparation';OUT=ROOT/'work/S32_B_launch'
def now():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
candidate=PREP/'B_contract_candidate.json';assert sha(candidate)=='80419e5911a5840e2c8e1bef018c3754e34a531bfcfa1dc2b92786bf60a539d8';c=read(candidate)
review=ROOT/'work/S32_independent_review/B_final_pre_review.json';assert sha(review)=='7ea4778451b39fe01fad664f6a6b49b47667da6a6b653066db527a6b63019864';r=read(review)
assert r['status']=='PASS_B_SOURCE_PRE_REVIEW' and r['passed'] is True and r['candidate_sha256']==sha(candidate)
assert r['runner_sha256']==sha(c['runner'])=='7552b65cf9913eafecec781437bc898f962e00df1d845a57130abe4c82d4cfcd'
rootreview=ROOT/'work/S32_continuation/B_root_pre_review.json';assert read(rootreview)['runner_sha256']==r['runner_sha256']
for p,h in c['identities'].items():assert sha(p)==h,p
assert not Path(c['output_root']).exists() and not Path(c['execution_root']).exists()
target=PREP/'B_contract.json';assert not target.exists();OUT.mkdir(exist_ok=False)
c.update(status='FROZEN',frozen_utc=now(),candidate_sha256=sha(candidate),independent_review=str(review),root_review=str(rootreview))
c['identities'].update({str(review):sha(review),str(rootreview):sha(rootreview)})
write(target,c)
receipt=dict(status='FROZEN',frozen_utc=c['frozen_utc'],contract_sha256=sha(target),launcher_sha256=sha(__file__),independent_review_sha256=sha(review),root_review_sha256=sha(rootreview),new_sensor_depth_reads=0)
write(OUT/'receipt.json',receipt)
sys.path.insert(0,str(ROOT/'scripts'));from research_log import append_event
append_event('S32B 同窗三对照经两作者前审后冻结启动','四预定窗完整保留，一窗缺pose写NA，另三窗各一次C2a初始化/原400Adam及自身公共尺度恢复。外控每窗CPU8/120秒/4GiB；每窗同内存零步，0新模型/sensor-depth读取。所有终态封存前不评分。',evidence=[str(target),str(review),str(OUT/'receipt.json')],next_step='核实际终态与输出，再封存评分GT字节及执行原固定指标。',occurred_at=c['frozen_utc'],time_source='actual local root freeze before process launch')
env=os.environ.copy()
for k in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS']:env[k]='8'
command=[str(ROOT/'.venv-cut3r/bin/python'),c['runner'],'dispatch','--contract',str(target),'--sha256',sha(target)]
receipt.update(status='RUNNING',started_utc=now(),command=command);write(OUT/'receipt.json',receipt)
print(json.dumps({'status':'RUNNING','started_utc':receipt['started_utc'],'B_contract_sha256':sha(target)}),flush=True)
with (OUT/'stdout.txt').open('w') as so,(OUT/'stderr.txt').open('w') as se:
    p=subprocess.Popen(command,cwd=ROOT,env=env,stdout=so,stderr=se);receipt['pid']=p.pid;write(OUT/'receipt.json',receipt);code=p.wait()
receipt.update(status='DISPATCH_EXITED' if code==0 else 'FAILED_DISPATCH',returncode=code,completed_utc=now())
if code==0:
    d=read(Path(c['execution_root'])/'dispatch_receipt.json');assert d['status']=='COMPLETE_FIXED_WINDOW_MATRIX_SEALED';receipt.update(window_statuses=d['windows'],success_windows=d['success_windows'])
write(OUT/'receipt.json',receipt)
append_event('S32B 固定窗口矩阵实际进程退出',f'外层退出码{code}；可用PASS窗数{receipt.get("success_windows","尚未获得")}，完整各窗终态见回执。运行成功不表示算法提升，尚未评分。',evidence=[str(OUT/'receipt.json'),str(Path(c['execution_root'])/'dispatch_receipt.json')],next_step='检查全部终态与已有失败，随后仅对完整PASS窗封存GT并评分，全48行保留。',occurred_at=receipt['completed_utc'],time_source='actual subprocess completion and terminal receipts')
print(json.dumps(receipt,ensure_ascii=False),flush=True);sys.exit(code)
