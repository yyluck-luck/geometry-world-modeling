import hashlib
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
PREP=ROOT/'work/S31_scale_shape_preparation'
OUT=ROOT/'work/S31_execution'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text())
def write(p,x): Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def utc(): return datetime.now(timezone.utc).isoformat()

candidate=PREP/'contract_candidate.json'
assert sha(candidate)=='26aea19b3dc2379af08de7987250a13416fe140c14722fd7e1568009f42a9b94'
assert not OUT.exists() and not (PREP/'contract.json').exists()
bindings={
ROOT/'work/S31_independent_pre_review/final_pre_review.json':'616c4f896091df2c747aa2c23de2b9d97f0ed4633d1664aa104659c7651b8793',
ROOT/'work/S31_reference_static_review/review.json':'803e3f4d0e379dfcf9ce7a3e4127d8679d281d1a116f81c1558bf5217f1b085f',
ROOT/'work/S31_root_numeric_review/recompute.py':'42e2314f010e6d04a880a15d8a05bf342b13a8f92b599e6bc97bcad270532365',
ROOT/'work/S31_root_numeric_review/protocol.md':'937d608e13cf809170b389ef7b7cd8b1540234221a99e51f25aaea4887bdd2f6',
ROOT/'scripts/s26b_consumer_baseline.py':'61e00503829dad7e9d1260fb408b81e8b281198e3cbf4bcab8367a493f982834'}
for p,s in bindings.items(): assert sha(p)==s,str(p)
assert read(ROOT/'work/S31_independent_pre_review/final_pre_review.json')['passed'] is True
c=read(candidate)
for p,s in c['identities'].items(): assert sha(p)==s,p
c['status']='FROZEN';c['root_freeze']={'utc':utc(),'candidate_sha256':sha(candidate),'reviewed_before_real_execution':True}
for p,s in bindings.items(): c['identities'][str(p)]=s
review=ROOT/'work/S31_root_pre_review/review.json';c['identities'][str(review)]=sha(review)
write(PREP/'contract.json',c);contract_sha=sha(PREP/'contract.json')
OUT.mkdir()
sys.path.insert(0,str(ROOT/'scripts'));from research_log import append_event
append_event('S31单标量保存量分解审后冻结并启动',
    '主任务与不同作者全文前审通过，正式合同SHA'+contract_sha+'。全4帧每臂一个只来自预测自身的k，先两臂D*封存再GT，8新评分/原16行导入。另式scalar/fsum参考已预先准备及静态审过；两阶段各CPU1/180秒/2GiB，0模型/GA/MST/backward。',
    evidence=['work/S31_scale_shape_preparation/contract.json','work/S31_independent_pre_review/final_pre_review.json','work/S31_root_pre_review/review.json'],
    next_step='单次保存量执行和独立复核；保留负结果，之后结束本窗口的调整。')
launch=dict(status='RUNNING',started_utc=utc(),contract_sha256=contract_sha)
write(OUT/'dispatch_receipt.json',launch)
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
spec=importlib.util.spec_from_file_location('s31_parent_resource_gate',ROOT/'scripts/s26b_consumer_baseline.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b);b.WORK=OUT
try:
    cmd=[sys.executable,str(PREP/'run_s31.py'),'--contract',str(PREP/'contract.json'),'--sha256',contract_sha]
    b.supervised(cmd,'diagnostic',180,2*1024**3)
    ref=ROOT/'work/S31_root_numeric_review'
    cmd=[sys.executable,str(ref/'recompute.py'),'--contract',str(PREP/'contract.json'),'--contract-sha',contract_sha,
         '--script-sha',bindings[ref/'recompute.py'],'--protocol-sha',bindings[ref/'protocol.md']]
    b.supervised(cmd,'independent_review',180,2*1024**3)
    assert sha(PREP/'contract.json')==contract_sha
    launch.update(status='PASS',completed_utc=utc(),contract_unchanged=True)
except BaseException as e:
    launch.update(status='FAILED',failed_utc=utc(),error=repr(e));write(OUT/'dispatch_receipt.json',launch);raise
write(OUT/'dispatch_receipt.json',launch)
print(json.dumps(launch))
