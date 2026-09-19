from datetime import datetime,timezone
import hashlib,json,os,sys,time,types
from pathlib import Path
ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling');HERE=ROOT/'work/S45B_c1_numeric_camera_guard_supervised_v10'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
started=datetime.now(timezone.utc).isoformat();deadline=time.monotonic()+120
binding_path=HERE/'C1_CAMERA_GUARD_BINDING_V10.json';assert sha(binding_path)=='c229639c45955fd84447dcdcab7e5d0dbe1a15af458220806d46692dc82c769c'
binding=json.loads(binding_path.read_text());source_set=binding['source_set']
assert source_set['primary_source_review']=='670d153216f0b1a426b569c4df83efd6b34895c5dd7d8dcfa5f9d7fa0bdf3d21'
assert source_set['adversarial_source_review']=='a1b73c112878f5592e112bc70f50c200130d1357b8f40681ab3e137a11571031'
for name in ['camera_guard.py','supervise_camera_guard.py','PROTOCOL.md','C1_CAMERA_GUARD_BINDING_TEMPLATE.json','synthetic_selftest.py']:assert sha(HERE/name)==source_set[name]
module=types.ModuleType('_c1_v10_independent_binding_readonly');module.__file__=str(HERE/'camera_guard.py');sys.modules[module.__name__]=module
exec(compile(Path(module.__file__).read_bytes(),module.__file__,'exec'),module.__dict__)
args=types.SimpleNamespace(self_sha256=source_set['camera_guard.py'],supervisor_sha256=source_set['supervise_camera_guard.py'],primary_source_review_sha256=source_set['primary_source_review'],adversarial_source_review_sha256=source_set['adversarial_source_review'],binding_sha256=sha(binding_path))
source_records=module.verify_static_reference(args.self_sha256,args.supervisor_sha256,deadline)
reviews,review_records=module.verify_source_reviews(args,datetime.now(timezone.utc),deadline)
assert set(binding['upstream'])==set(module.fixed_upstream_paths())
for name,p in module.fixed_upstream_paths().items():
 assert binding['upstream'][name]['path']==str(p)
 assert p.suffix in ('.json','.jsonl')
 assert sha(p)==binding['upstream'][name]['sha256']
upstream_docs,upstream_records=module.verify_upstream(binding,deadline)
expected={**source_set,'C1_CAMERA_GUARD_BINDING_V10.json':args.binding_sha256,**{k:v['sha256'] for k,v in binding['upstream'].items()}}
assert len(expected)==18
roles=[module.AUTHOR_ROLE,reviews[0]['reviewer_role'],reviews[1]['reviewer_role'],binding['author_role'],'/root/c2_final_launch_readiness']
assert roles==['/root/c2_v5_lifecycle_review','/root/c2_generation_builder','/root/c1_v8_binding_review','/root','/root/c2_final_launch_readiness']
assert len(set(roles))==5 and binding['author_role']==binding['author_task_id']=='/root'
assert len({reviews[0]['reviewer_task_id'],reviews[1]['reviewer_task_id'],binding['author_task_id'],'/root/c2_final_launch_readiness'})==4
assert max(datetime.fromisoformat(r['completed_utc']) for r in reviews)<=datetime.fromisoformat(binding['created_utc'])
fresh={str(p):not os.path.lexists(p) for p in [module.FORMAL_OUT,module.LOCK,module.LOCK_STAGING,module.GOVERNANCE_ATTESTATION]};assert all(fresh.values())
completed=datetime.now(timezone.utc).isoformat()
report={'schema':'s45b-c1-numeric-camera-guard-binding-review-v4','status':'PASS_S45B_C1_NUMERIC_CAMERA_GUARD_SUPERVISED_BINDING_REVIEW_V10','verdict':'PASS_SUPERVISED_BINDING_ONLY_NO_TENSOR_BODIES','author_role':'/root','reviewer_role':'/root/c2_final_launch_readiness','reviewer_task_id':'/root/c2_final_launch_readiness','reviewer_turn_id':'c1-v10-binding-review-'+completed,'started_utc':started,'completed_utc':completed,'row':'C1','reviewed_identities':expected,'executed':False,'c1_tensor_bodies_read':0,'pixels_decoded':0,'images_viewed':0,'model_or_scientific_imports':0,'blocking_findings':[],'checks':{'five_frozen_source_hashes_verified':True,'two_exact_source_review_hash_status_identity_sets_verified':True,'ten_canonical_upstream_text_path_hashes_verified':True,'actual_v10_upstream_status_and_cross_reference_checks_passed':True,'static_b0_s42_s45_reference_identity_checks_passed':True,'source_reviews_precede_binding_precede_this_review':True,'five_pairwise_distinct_declared_roles':roles,'four_pairwise_distinct_review_binding_task_ids':True,'formal_and_governance_paths_absent':fresh,'source_test_matrix_rerun':False,'camera_tensor_store_constructed':False,'formal_guard_or_governance_called':False},'role_time_evidence':{'source_author':module.AUTHOR_ROLE,'source_primary':{'role':reviews[0]['reviewer_role'],'task_id':reviews[0]['reviewer_task_id'],'turn_id':reviews[0]['reviewer_turn_id'],'completed_utc':reviews[0]['completed_utc']},'source_adversarial':{'role':reviews[1]['reviewer_role'],'task_id':reviews[1]['reviewer_task_id'],'turn_id':reviews[1]['reviewer_turn_id'],'completed_utc':reviews[1]['completed_utc']},'binding_author':{'role':binding['author_role'],'task_id':binding['author_task_id'],'turn_id':binding['author_turn_id'],'created_utc':binding['created_utc']}},'upstream_observed_statuses':{k:({'schema':v.get('schema'),'status':v.get('status')} if k!='s45_report' else {'saved_quantity_consumption_status':v.get('saved_quantity_consumption_status'),'pixel_identity_status':v.get('pixel_identity_status'),'quality_status':v.get('png_decode_or_visual_quality_status')}) for k,v in upstream_docs.items()},'verified_text_records':{**source_records,**review_records,**upstream_records},'review_tool':{'path':str(Path(__file__)),'sha256':sha(Path(__file__))},'governance_boundary':'Actual distinct tasks were assigned by root. This report checks declared role/time/artifact consistency; the separately required external orchestration attestation has not been created or validated by this reviewer.','scope':'Only the exact binding and text identity/status/order contract pass. The camera tensor bodies, numeric camera result, pixels, image quality and method novelty have not been evaluated.'}
p=HERE/'BINDING_REVIEW_V10.json';payload=(json.dumps(report,indent=2,ensure_ascii=False)+'\n').encode();fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o444)
try:os.write(fd,payload);os.fsync(fd)
finally:os.close(fd)
args.binding_review_sha256=sha(p)
# Validate the complete actual emitted binding/review using the existing read-only function.
validated=module.verify_binding(args,reviews,datetime.now(timezone.utc),deadline)
assert validated[0]==binding and validated[1]==report
for name in ['camera_guard.py','supervise_camera_guard.py','PROTOCOL.md','C1_CAMERA_GUARD_BINDING_TEMPLATE.json','synthetic_selftest.py']:assert sha(HERE/name)==source_set[name]
assert all(not os.path.lexists(p) for p in fresh)
assert not any(n.split('.')[0] in {'numpy','torch','PIL','cv2','diffusers','safetensors'} for n in sys.modules)
receipt={'schema':'s45b-c1-binding-review-output-validation-v1','completed_utc':datetime.now(timezone.utc).isoformat(),'binding_review_path':str(p),'binding_review_sha256':sha(p),'actual_verify_binding_returned':True,'source_tests_rerun':0,'formal_guard_calls':0,'tensor_bodies_read':0,'pixels_decoded':0}
rp=HERE/'binding_review_evidence/OUTPUT_VALIDATION.json'
with rp.open('x') as h:json.dump(receipt,h,indent=2);h.write('\n')
log=types.ModuleType('_research_log');log.__file__=str(ROOT/'scripts/research_log.py');exec(compile(Path(log.__file__).read_bytes(),log.__file__,'exec'),log.__dict__)
log.append_event(action='C1 V10输入绑定的不同作者独立审查完成',outcome='独立复核五源码、两fresh源审和十上游文本路径/SHA/实际状态链，确认五角色及四审查/绑定task彼此独立、时间先后正确。实际verify_upstream与最终emit后的verify_binding只读核验均通过，票为PASS_SUPERVISED_BINDING_ONLY_NO_TENSOR_BODIES。0新源码矩阵重跑/治理/正式guard/相机tensor正文/像素/模型；仍待root外部治理与唯一原入口数值执行。',evidence=[str(p.relative_to(ROOT))+' sha256='+sha(p),str(rp.relative_to(ROOT))+' sha256='+sha(rp)],next_step='root核实际角色事件后建立外部治理票，按原监督入口进行一次相机数值核验；本绑定票不代表相机或图像结果。',occurred_at=completed,event_id='s45b-c1-v10-binding-review-20260908')
print(json.dumps({'path':str(p),'sha256':sha(p),'completed_utc':completed,'status':report['status'],'exact_reviewed_identities':len(expected),'output_validation_sha256':sha(rp)},indent=2))
