"""Invoke the reviewed camera-only guard after genuine delegated binding review."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone

ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
D=ROOT/'work/S45B_c1_numeric_camera_guard_supervised_v10'
OUT=ROOT/'work/resumption_20260908/C1_V10_FORMAL_ORCHESTRATION.json'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(name, digest=None):
    p=D/name
    if digest is not None: assert sha(p)==digest, name
    return json.loads(p.read_text()), sha(p)
assert not OUT.exists()
primary, psha=read('SOURCE_REVIEW_PRIMARY_V10.json',sys.argv[1])
second, ssha=read('SOURCE_REVIEW_ADVERSARIAL_V10.json',sys.argv[2])
binding,bsha=read('C1_CAMERA_GUARD_BINDING_V10.json',sys.argv[3])
review,rsha=read('BINDING_REVIEW_V10.json',sys.argv[4])
assert primary['reviewer_role']=='/root/c2_generation_builder'
assert second['reviewer_role']=='/root/c1_v8_binding_review'
assert binding['author_role']=='/root'
assert review['reviewer_role']=='/root/c2_final_launch_readiness'
assert review['status']=='PASS_S45B_C1_NUMERIC_CAMERA_GUARD_SUPERVISED_BINDING_REVIEW_V10'
assert review['blocking_findings']==[]
assert primary['reviewed_identities']==second['reviewed_identities']
for name in ('camera_guard.py','supervise_camera_guard.py','PROTOCOL.md','C1_CAMERA_GUARD_BINDING_TEMPLATE.json','synthetic_selftest.py'):
    assert sha(D/name)==binding['source_set'][name], name
for item in binding['upstream'].values(): assert sha(Path(item['path']))==item['sha256']
events={'source_author':{'role':'/root/c2_v5_lifecycle_review','task_id':'/root/c2_v5_lifecycle_review'}}
for name, doc, digest in [('primary_source_review',primary,psha),('adversarial_source_review',second,ssha),('binding_review',review,rsha)]:
    events[name]={'role':doc['reviewer_role'],'task_id':doc['reviewer_task_id'],'turn_id':doc['reviewer_turn_id'],'completed_utc':doc['completed_utc'],'artifact_sha256':digest}
events['binding_author']={'role':binding['author_role'],'task_id':binding['author_task_id'],'turn_id':binding['author_turn_id'],'completed_utc':binding['created_utc'],'artifact_sha256':bsha}
now=datetime.now(timezone.utc).isoformat()
attestation=dict(schema='s45b-c1-numeric-camera-guard-governance-attestation-v1',status='PASS_EXTERNAL_ORCHESTRATOR_PROVENANCE_GATE_V10',trust_boundary='EXTERNAL_ORCHESTRATOR_PROVENANCE_NOT_SELF_AUTHENTICATED_BY_CANDIDATE',artifact_identities={**primary['reviewed_identities'],'primary_source_review':psha,'adversarial_source_review':ssha,'C1_CAMERA_GUARD_BINDING_V10.json':bsha,'BINDING_REVIEW_V10.json':rsha,'v6_primary_blocked_review':'0b30345a8546cd2e89036b118b12b75825cf7662b133d2bac380b4f9904aeb16'},role_time_events=events,issuer={'role':'/root','task_id':'/root','turn_id':'c1-v10-external-orchestration-'+now},blocking_findings=[],authorizes_exact_source_binding_only=True,formal_execution_completed=False,created_utc=now,provenance_note='Root actually bound V10 after Linnaeus authored it and two different agents reviewed its source. The separate c2_final_launch_readiness agent independently reviewed the root C1 binding. All roles were dispatched through actual collaboration tools. Turn labels are task-local record labels, not cryptographic service identity. No self-authentication by candidate is claimed.')
gp=D/'GOVERNANCE_ATTESTATION_V10.json'
with gp.open('x') as f: json.dump(attestation,f,ensure_ascii=False,indent=2);f.write('\n')
argv=['/opt/homebrew/bin/python3','-I','-B','-S',str(D/'supervise_camera_guard.py'),'--self-sha256',sha(D/'supervise_camera_guard.py'),'--worker-sha256',sha(D/'camera_guard.py'),'--primary-source-review-sha256',psha,'--adversarial-source-review-sha256',ssha,'--binding-sha256',bsha,'--binding-review-sha256',rsha,'--governance-attestation-sha256',sha(gp),'--out',str(D/'execution_01')]
started=datetime.now(timezone.utc).isoformat()
run=subprocess.run(argv,cwd='/private/tmp',capture_output=True,timeout=300)
stdout=ROOT/'work/resumption_20260908/C1_V10_FORMAL_STDOUT.json'
stderr=ROOT/'work/resumption_20260908/C1_V10_FORMAL_STDERR.txt'
with stdout.open('xb') as f:f.write(run.stdout)
with stderr.open('xb') as f:f.write(run.stderr)
receipt=dict(started_utc=started,completed_utc=datetime.now(timezone.utc).isoformat(),argv=argv,returncode=run.returncode,stdout_path=str(stdout),stdout_sha256=sha(stdout),stderr_path=str(stderr),stderr_sha256=sha(stderr),governance_sha256=sha(gp),scope='REAL_SAVED_C1_CAMERA_ARRAY_VALIDATION_ONLY_NO_PIXELS_NO_NEW_MODEL')
with OUT.open('x') as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
sys.path.insert(0,str(ROOT/'scripts'))
from research_log import append_event
append_event('C1 V10按双源码票与独立绑定执行真实保存相机数值核验',f'源码作者、两名源码审查者、root绑定作者和另一绑定审查者完成真实五角色分工后，root发布精确外部编排回执并运行既有监督入口，进程返回{run.returncode}。完整stdout/退出码已保留，终端结果仍需独立核对；未运行新模型或查看像素。',[str(OUT.relative_to(ROOT)),str(stdout.relative_to(ROOT)),str(gp.relative_to(ROOT))],'按实际终端封口和数值报告核结果；通过后再接既定盲评分。')
print(json.dumps(dict(returncode=run.returncode,stdout=run.stdout.decode()[-3500:],stderr=run.stderr.decode()[-1500:],receipt=str(OUT)),ensure_ascii=False))
