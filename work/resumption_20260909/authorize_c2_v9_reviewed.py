"""Invoke the existing unique authorization after exact post-attachment reviews."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import subprocess
import sys
R=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
D=R/'work/S47B_c2_confirmation_generation_v9'
OUT=R/'work/resumption_20260909/C2_V9_AUTHORIZATION_ORCHESTRATION.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not OUT.exists()
paths=[D/'FINAL_ATTACHMENT_REVIEW.json',D/'LAUNCH_READINESS_REVIEW.json']
assert len(sys.argv)==3
reviews=[]
for path,pin in zip(paths,sys.argv[1:]):
    assert sha(path)==pin
    reviews.append(json.loads(path.read_text()))
assert reviews[0]['reviewer_role']!=reviews[1]['reviewer_role']
assert all(x['blocking_findings']==[] for x in reviews)
attach=json.loads((D/'review_attachment_01/receipt.json').read_text())
bindings={
 'manifest_sha256':sha(D/'review_attachment_01/manifest.json'),
 'core_file_sha256':sha(D/'freeze_attempt_01/manifest_core.json'),
 'core_sha256':attach['core_sha256'],
 'prepare_receipt_sha256':sha(D/'freeze_attempt_01/receipt.json'),
 'attachment_receipt_sha256':sha(D/'review_attachment_01/receipt.json'),
 'metadata_gate_sha256':sha(D/'review_attachment_01/metadata_gate.json'),
 'final_attachment_review_sha256':sha(paths[0]),
 'launch_readiness_review_sha256':sha(paths[1]),
}
assert sha(D/'create_launch_authorization.py')=='34666995d93a4e9a4629ac31b75b7c65e3fc989a0efe10732113c358284053a5'
argv=['/opt/homebrew/bin/python3','-I','-B','-S',str(D/'create_launch_authorization.py')]
for k,v in bindings.items():argv.extend(['--'+k.replace('_','-'),v])
start=datetime.now(timezone.utc).isoformat()
run=subprocess.run(argv,cwd=str(R),capture_output=True,text=True,timeout=120)
rec=dict(started_utc=start,completed_utc=datetime.now(timezone.utc).isoformat(),argv=argv,returncode=run.returncode,stdout=run.stdout,stderr=run.stderr,scope='REVIEWED_LAUNCH_AUTHORIZATION_ONLY_NOT_GENERATION')
with OUT.open('x') as f:json.dump(rec,f,ensure_ascii=False,indent=2);f.write('\n')
sys.path.insert(0,str(R/'scripts'))
from research_log import append_event
append_event('C2两项发布后独立审查完成后调用既定授权工具',f'root核两份精确新审查及六个包身份，唯一授权工具return{run.returncode}；尚不是模型运行或科学结果。',[str(OUT.relative_to(R))],'仅当既有授权成功时启动一次原定CPU两批生成；失败保留不自动重试。')
print(json.dumps(rec,ensure_ascii=False))
