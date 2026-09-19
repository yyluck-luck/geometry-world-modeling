"""Independent finite published-control-plane review; no authorization or model."""
from pathlib import Path
from datetime import datetime, timezone
import copy
import hashlib
import importlib.util
import json
import os
import stat
import sys

ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
BASE=ROOT/'work/S47_c2_confirmation_generation'
ROLE='/root/c1_v8_binding_review'
EXPECTED={
    'manifest_sha256':'3b46f3016ac3755ac96bd8c955dee0a577f6a5b83ebf039343a799a6f55e2217',
    'core_file_sha256':'99f62b480a9dbead14a79eadafad43a520a110501e224e56702bcdc8ede10b07',
    'core_sha256':'a577d2a9cbcd5217b531fec06e531fb81bd4c679bc99866d41bedf13c168540a',
    'prepare_receipt_sha256':'a71ad6ad30a43f3ff655f2d6da6f14bf4f9a0e2d1b648375350f12178b5187f6',
    'attachment_receipt_sha256':'50f5c99ac2ded49a5d203cb802e72051fe955266b3d98ae4983073c50d7c5f66',
    'metadata_gate_sha256':'cb76b3ee72be087811507b6ef7784f8d2f95a5e66da26cda70096014fa948f1f',
}
FILES={
    'manifest_sha256':BASE/'review_attachment_01/manifest.json',
    'core_file_sha256':BASE/'freeze_attempt_01/manifest_core.json',
    'prepare_receipt_sha256':BASE/'freeze_attempt_01/receipt.json',
    'attachment_receipt_sha256':BASE/'review_attachment_01/receipt.json',
    'metadata_gate_sha256':BASE/'review_attachment_01/metadata_gate.json',
}
snapshots={}
def read(path):
    path=Path(path);raw=path.read_bytes();s=path.stat()
    snapshots[str(path)]={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'mode':stat.S_IMODE(s.st_mode)}
    return raw
def sha(path):return hashlib.sha256(read(path)).hexdigest()
def canonical_core(d):
    return hashlib.sha256(json.dumps({k:v for k,v in d.items() if k!='review_receipts'},sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
def utc(s):return datetime.fromisoformat(s.replace('Z','+00:00'))

started=datetime.now(timezone.utc).isoformat()
assert sha(BASE/'generation_gate.py')=='5add4e5b6170f42ff75cdede7f40a061cd1b98a253f0fb6411444990155255ec'
assert sha(BASE/'FREEZE_PROTOCOL.md')=='122f840d3be68d813bb911445590e3b2c00a7428de92020fe1624933df4d9faf'
assert sha(BASE/'create_launch_authorization.py')=='209d6b141e154574d8ddd59e252839c27c911e4ec6fba4b18da5a9aca16ec89e'
for name,path in FILES.items():assert sha(path)==EXPECTED[name],name
spec=importlib.util.spec_from_file_location('c2_final_attachment_gate',BASE/'generation_gate.py')
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
manifest=gate.read_frozen(FILES['manifest_sha256'],EXPECTED['manifest_sha256'])
attachment=gate.require_published_attachment(FILES['manifest_sha256'],EXPECTED['manifest_sha256'],manifest)
observed,attached=gate.launch_review_bindings(manifest,EXPECTED['manifest_sha256'])
assert observed==EXPECTED
prepared=gate.require_successful_prepare_bundle(core_file_sha256_value=EXPECTED['core_file_sha256'],core_sha256_value=EXPECTED['core_sha256'],receipt_sha256_value=EXPECTED['prepare_receipt_sha256'])
core=json.loads(read(FILES['core_file_sha256']))
stripped=copy.deepcopy(manifest);stripped['review_receipts']={}
assert core==stripped and canonical_core(core)==canonical_core(manifest)==EXPECTED['core_sha256']
parent=gate.read_base_s40()
common_changed=sorted(k for k in parent.keys()&manifest.keys() if parent[k]!=manifest[k])
assert common_changed==sorted(['schema','review_receipts','controls','input_image','freeze_preparation','source_identities','config','output_root','status','created_utc'])
assert parent.keys()-manifest.keys()=={'scope'}
assert manifest.keys()-parent.keys()=={'derivation_policy','parent_bindings'}
assert {k:v for k,v in parent['controls'].items() if k!='seed'}=={k:v for k,v in manifest['controls'].items() if k!='seed'}
assert parent['controls']['seed']==42 and manifest['controls']['seed']==44
assert Path(parent['input_image']['path']).name=='changi.jpg'
assert Path(manifest['input_image']['path']).name=='living_room.jpg'
source_bytes=0
for path,digest in manifest['source_identities'].items():
    assert sha(path)==digest,path
    source_bytes+=snapshots[path]['bytes']
source_overlap=parent['source_identities'].keys()&manifest['source_identities'].keys()
assert not [k for k in source_overlap if parent['source_identities'][k]!=manifest['source_identities'][k]]
assert sha(manifest['input_image']['path'])==manifest['input_image']['sha256']
assert snapshots[manifest['input_image']['path']]['bytes']==manifest['input_image']['size_bytes']==536341
assert sha(manifest['config']['path'])==manifest['config']['sha256']
reviews={}
for kind,item in manifest['review_receipts'].items():
    assert sha(item['path'])==item['sha256']
    r=json.loads(read(item['path']))
    assert r['schema']=='s47-c2-generation-core-review-v1'
    assert r['status']==gate.REVIEW_STATUSES[kind]
    assert r['row']=='C2' and r['variant']==manifest['variant']
    assert r['core_file_sha256']==EXPECTED['core_file_sha256']
    assert r['core_sha256']==EXPECTED['core_sha256']
    assert r['prepare_receipt_sha256']==EXPECTED['prepare_receipt_sha256']
    assert r['author_role']=='/root' and r['reviewer_role'] not in ['/root',ROLE,'/root/c2_generation_builder']
    assert r['executed'] is False and r['blocking_findings']==[]
    assert r['model_or_scientific_imports']==0 and r['pixels_decoded']==0
    assert utc(prepared['receipt']['completed_utc'])<utc(r['reviewed_utc'])<utc(attached)
    reviews[kind]={'path':item['path'],'sha256':item['sha256'],'reviewer_role':r['reviewer_role'],'reviewed_utc':r['reviewed_utc'],'status':r['status']}
assert len({r['reviewer_role'] for r in reviews.values()})==2
reserved={str(p):os.path.lexists(p) for p in [gate.LAUNCH_AUTHORIZATION,gate.AUTHORIZATION_ATTEMPT,BASE/'execution_01',gate.C2_OUTPUT]}
assert not any(reserved.values())
forbidden_imports=[name for name in ['torch','numpy','PIL','cv2','diffusers','transformers','scipy'] if name in sys.modules]
assert forbidden_imports==[]
for path,item in snapshots.items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==item['sha256']
now=datetime.now(timezone.utc).isoformat()
review={
    'schema':'s47-c2-final-launch-review-v1',
    'review_kind':'final_attachment',
    'status':'PASS_S47_C2_FINAL_ATTACHMENT_REVIEW',
    'started_utc':started,'reviewed_utc':now,
    'time_basis':'Actual UTC after independent final published-bundle review; no historical work duration inferred.',
    'author_role':'/root','reviewer_role':ROLE,'reviewer_task_id':ROLE,
    'reviewer_turn_id':'c2-v7-final-attachment-review-'+now,
    'bindings':EXPECTED,
    'attachment_completed_utc':attached,
    'row':'C2','variant':manifest['variant'],
    'blocking_findings':[],
    'executed':False,'model_or_scientific_imports':0,'pixels_decoded':0,'generation_calls':0,
    'quality_status':'NOT_EVALUATED','method_or_novelty_status':'NOT_EVALUATED',
    'review_scope':'Independent ordinary published control-plane and allowed-difference review. No new security mechanism or attack test; no model/scientific import, image decode, generation, authorization or launcher call.',
    'checks':{
        'six_exact_sha_bindings_recomputed':'PASS',
        'original_gate_read_frozen_and_published_attachment_helpers':'PASS',
        'successful_prepare_exact_two_read_only_files':'PASS',
        'successful_attach_exact_three_read_only_files':'PASS',
        'prepare_attach_sentinel_inode_time_and_receipt_chain':'PASS',
        'published_manifest_equals_core_except_review_receipts':'PASS',
        'independent_canonical_core_hash_excludes_only_review_receipts':'PASS',
        'both_core_review_hashes_schemas_identities_and_time_order':'PASS',
        'c2_input_and_seed_only_scientific_changes_from_s40':'PASS',
        'all_manifest_source_identities_recomputed':'PASS',
        'single_seed_yaml_substitution_plus_one_lf':'PASS',
        'source_and_control_bytes_unchanged_at_close':'PASS',
    },
    'prepare_directory_identity':prepared['directory_identity'],
    'attachment_directory_identity':attachment['directory_identity'],
    'core_review_chain':reviews,
    's40_derivation':{
        'allowed_scientific_changes':{'input':'changi.jpg to living_room.jpg','seed':'42 to 44'},
        'other_controls_components_runtime_limits_and_loading_chain_equal':True,
        'common_changed_top_level_keys':common_changed,
        's40_only_key':'scope','c2_only_keys':['derivation_policy','parent_bindings'],
        'overlapping_source_hash_mismatches':[],
        'metadata_gate_is_preflight_only_and_not_execution_authorization':True,
    },
    'read_boundary':{
        'manifest_source_files_hashed':len(manifest['source_identities']),
        'source_file_bytes_hashed':source_bytes,
        'unique_source_control_and_input_files_hashed':len(snapshots),
        'c2_jpeg_body_bytes_hashed_without_decoding':536341,
        'component_body_bytes_read':0,'model_or_scientific_imports':0,
        'images_viewed':0,'pixels_decoded':0,'generation_calls':0,
        'prepare_attach_authorization_or_launcher_calls':0,
        'production_source_or_existing_bundle_files_modified':0,
    },
    'reserved_launch_paths_observed_before_review_publication':reserved,
    'source_control_and_input_snapshots':snapshots,
    'authorization_effect':'FINAL_ATTACHMENT_REVIEW_ONLY. A distinct fresh launch-readiness review and the separately reviewed authorization tool remain required before the single launch. This is not a generation or research result.',
}
gate.validate_launch_review(review,'final_attachment',EXPECTED,attached)
out=BASE/'FINAL_ATTACHMENT_REVIEW.json'
raw=(json.dumps(review,ensure_ascii=False,indent=2)+'\n').encode()
with out.open('xb') as f:f.write(raw)
print(json.dumps({'path':str(out),'sha256':hashlib.sha256(raw).hexdigest(),'reviewed_utc':now,'source_files_hashed':len(manifest['source_identities'])},indent=2))
