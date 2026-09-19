"""Publish the existing C2 attachment after both genuine prepared-core reviews."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import subprocess
import sys
R=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
D=R/'work/S47B_c2_confirmation_generation_v9'
OUT=R/'work/resumption_20260909/C2_V9_ATTACH_ORCHESTRATION.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not OUT.exists()
source=D/'SOURCE_REVIEW.json';runtime=D/'RUNTIME_FRESHNESS_REVIEW.json'
assert sha(source)==sys.argv[1]
assert sha(runtime)==sys.argv[2]
s=json.loads(source.read_text());r=json.loads(runtime.read_text())
assert s['status']=='PASS_S47_C2_GENERATION_SOURCE_REVIEW'
assert r['status']=='READY_TO_ATTEMPT_S47_C2_BASELINE_GENERATION'
assert s['reviewer_role']!=r['reviewer_role']
for k in ('core_path','core_file_sha256','core_sha256','prepare_receipt_sha256','variant'):
    assert s[k]==r[k],k
assert s['blocking_findings']==r['blocking_findings']==[]
argv=['/opt/homebrew/bin/python3','-I','-B','-S',str(D/'freeze_c2_manifest.py'),'--mode','attach','--out',str(D/'review_attachment_01'),'--core',s['core_path'],'--core-file-sha256',s['core_file_sha256'],'--core-sha256',s['core_sha256'],'--prepare-receipt-sha256',s['prepare_receipt_sha256'],'--source-review',str(source),'--source-review-sha256',sha(source),'--runtime-review',str(runtime),'--runtime-review-sha256',sha(runtime)]
start=datetime.now(timezone.utc).isoformat()
run=subprocess.run(argv,cwd='/private/tmp',capture_output=True,text=True,timeout=600)
receipt=dict(started_utc=start,completed_utc=datetime.now(timezone.utc).isoformat(),argv=argv,returncode=run.returncode,stdout=run.stdout,stderr=run.stderr,scope='PREPARED_CORE_REVIEW_ATTACHMENT_ONLY_NOT_GENERATION',model_runs=0)
with OUT.open('x') as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
sys.path.insert(0,str(R/'scripts'))
from research_log import append_event
append_event('C2 V9两份真实核心票后执行既定附件发布',f'精确核source/runtime两个独立核心票与core/prepare身份，调用既有attach工具，returncode={run.returncode}。未加载模型、生成或评分；此结果不替代后续附件及launch readiness审查。',[str(OUT.relative_to(R)),'work/S47B_c2_confirmation_generation_v9/review_attachment_01'],'若成功，按既定两项发布后审查及独立授权工具接续；若失败保留现场。')
print(json.dumps(dict(returncode=run.returncode,stdout=run.stdout[-2200:],stderr=run.stderr[-1500:],receipt=str(OUT)),ensure_ascii=False))
