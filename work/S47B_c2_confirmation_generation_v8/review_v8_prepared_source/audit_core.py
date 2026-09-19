"""Bounded prepared-core source/contract review, without model or formal calls."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, importlib.util, json, os, stat, sys

ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
BASE=ROOT/'work/S47B_c2_confirmation_generation_v8'
ROLE='/root/c1_v8_binding_review'
snapshots={}
def sha(path):
    path=Path(path);raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
    snapshots[str(path)]={'sha256':digest,'bytes':len(raw)}
    return digest
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def utc(s):return datetime.fromisoformat(s.replace('Z','+00:00'))

started=datetime.now(timezone.utc).isoformat()
assert sha(BASE/'FROZEN_SOURCE_SET_V8.json')=='3cd9fdaa24be3021672678da66d3c56a8705e36485a396832aa9c74de1ff306b'
freeze=json.loads((BASE/'FROZEN_SOURCE_SET_V8.json').read_text())
for name,value in freeze['production_candidate_sha256'].items():assert sha(BASE/name)==value,name
gate=load('c2_v8_core_review_gate',BASE/'generation_gate.py')
tool=load('c2_v8_core_review_freeze',BASE/'freeze_c2_manifest.py')
cp=BASE/'freeze_attempt_01/manifest_core.json';rp=BASE/'freeze_attempt_01/receipt.json'
core_file_sha=sha(cp);receipt_sha=sha(rp)
assert core_file_sha=='7f3a6a068c7e6c67ccbbd441cfa530366ba778d69ce8fa8a3781f5b7c15c6383'
core=json.loads(cp.read_text())
canonical=hashlib.sha256(json.dumps({k:v for k,v in core.items() if k!='review_receipts'},sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
assert canonical=='e6c5c983a539d00162f42ec93fb9aa8c7a24b1d1f790896191799d1f874e5247'
verified,prepared=tool.verify_unreviewed_core(gate,core,core_file_sha,canonical,receipt_sha)
assert verified==canonical and prepared['core']==core and core['review_receipts']=={}
base=gate.read_base_s40()
for key in ['variant','components','runtime','generation_limits','s39_loading_manifest','s39_resource_core_sha256','s39_loading_evidence','s39_loading_review']:
    assert core[key]==base[key],key
assert {k:v for k,v in core['controls'].items() if k!='seed'}=={k:v for k,v in base['controls'].items() if k!='seed'}
assert core['controls']['seed']==44 and base['controls']['seed']==42
assert core['controls']['device']=='cpu' and core['controls']['dtype']=='float32' and core['controls']['threads']==8
assert core['controls']['height']==core['controls']['width']==576 and core['controls']['inference_num_steps']==50
assert core['controls']['context_num_frames']==core['controls']['target_num_frames']==4 and core['controls']['num_frames']==8
assert core['controls']['operations']==['turn_left(5)','turn_right(5)']
assert Path(core['input_image']['path']).name=='living_room.jpg'
assert core['output_root']==str(ROOT/'results/S47B_C2_confirmation_generation_v8')
for path,value in core['source_identities'].items():assert sha(path)==value,path
assert len(core['source_identities'])==219
assert sha(core['input_image']['path'])==core['input_image']['sha256']
gate.require_single_seed_config_derivation(base)
original_reviews={}
for kind in ['PRIMARY','ADVERSARIAL']:
    p=BASE/f'SOURCE_REVIEW_{kind}_V8.json';digest=sha(p);r=json.loads(p.read_text())
    assert r['status']==f'PASS_S47_C2_V8_{kind}_SOURCE_REVIEW'
    assert r['author_role']=='/root/c2_final_launch_readiness' and r['reviewer_role'] not in ['/root',ROLE,r['author_role']]
    assert {name:v['sha256'] for name,v in r['reviewed_files'].items()}==freeze['production_candidate_sha256']
    assert r['blocking_findings']==[]
    if kind=='PRIMARY':
        assert all(r['execution_boundary'][key]==0 for key in ['prepare_calls','attach_calls','authorization_main_calls','launcher_main_calls','model_or_scientific_imports','pixels_decoded','generation_calls'])
    else:
        assert r['executed'] is False and r['model_or_scientific_imports']==r['pixels_decoded']==r['generation_calls']==0
    reviewed=r.get('reviewed_utc') or r['completed_utc'];assert utc(reviewed)<utc(prepared['receipt']['started_utc'])
    original_reviews[kind.lower()]={'path':str(p),'sha256':digest,'reviewer_role':r['reviewer_role'],'reviewed_utc':reviewed}
assert len({x['reviewer_role'] for x in original_reviews.values()})==2
reserved={str(p):os.path.lexists(p) for p in [gate.ATTACHMENT_ROOT,gate.LAUNCH_AUTHORIZATION,gate.AUTHORIZATION_ATTEMPT,BASE/'execution_01',gate.C2_OUTPUT]}
assert not any(reserved.values())
assert not [k for k in ['torch','numpy','PIL','diffusers','transformers','scipy','cv2'] if k in sys.modules]
for path,item in snapshots.items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==item['sha256']
now=datetime.now(timezone.utc).isoformat();assert utc(prepared['receipt']['completed_utc'])<utc(now)
review={
    'schema':'s47-c2-generation-core-review-v1','status':'PASS_S47_C2_GENERATION_SOURCE_REVIEW',
    'started_utc':started,'reviewed_utc':now,'completed_utc':now,'row':'C2','variant':core['variant'],
    'core_path':str(cp),'core_file_sha256':core_file_sha,'core_sha256':canonical,'prepare_receipt_sha256':receipt_sha,
    'author_role':'/root','source_implementation_author_role':'/root/c2_final_launch_readiness',
    'reviewer_role':ROLE,'reviewer_task_id':ROLE,'reviewer_turn_id':'c2-v8-prepared-core-source-'+now,
    'executed':False,'model_or_scientific_imports':0,'pixels_decoded':0,'generation_calls':0,'blocking_findings':[],
    'quality_status':'NOT_EVALUATED','method_or_novelty_status':'NOT_EVALUATED',
    'checks':{'successful_prepare_exact_two_readonly_files':'PASS','exact_builder_reconstruction':'PASS','independent_review_excluded_canonical_core_sha':'PASS','all_219_source_identities_recomputed':'PASS','eight_current_sources_match_fresh_two_reviewed_sets':'PASS','source_reviews_precede_successful_prepare':'PASS','scientific_controls_equal_s40_except_predeclared_input_and_seed':'PASS','single_seed_yaml_byte_derivation':'PASS','no_future_attach_authorization_or_execution_state':'PASS'},
    'source_identities':core['source_identities'],
    'source_review_chain':original_reviews,
    'prepare_directory_identity':prepared['directory_identity'],
    'prepare_receipt_status':prepared['receipt']['status'],
    'scientific_contract':{'two_batches':True,'cache_history':[1,5,9],'device':'cpu','dtype':'float32','threads':8,'seed':44,'input':'living_room.jpg','size':[576,576],'steps':50,'s40_components_runtime_limits_and_loading_chain_equal':True,'no_scoring_or_visual_access':True},
    'evidence_boundary':{'source_files_hashed':219,'c2_jpeg_body_bytes_hashed_without_decode':536341,'component_body_bytes_read':0,'scientific_imports':0,'models_loaded':0,'new_test_matrix_runs':0,'formal_prepare_attach_authorization_or_launcher_calls':0,'source_or_old_artifacts_modified':0},
    'source_and_control_snapshots':snapshots,
    'reserved_paths_observed':reserved,
    'authorization_effect':'PREPARED_CORE_SOURCE_REVIEW_ONLY; distinct runtime core review, unique attach, two postpublication reviews and separate authorization remain required. This is not generation or scientific evidence.'
}
raw=(json.dumps(review,ensure_ascii=False,indent=2)+'\n').encode();out=BASE/'SOURCE_REVIEW.json'
with out.open('xb') as f:f.write(raw)
out.chmod(0o444)
assert stat.S_IMODE(out.stat().st_mode)==0o444
print(json.dumps({'path':str(out),'sha256':hashlib.sha256(raw).hexdigest(),'reviewed_utc':now,'prepare_receipt_sha256':receipt_sha,'mode':'0444'}))
