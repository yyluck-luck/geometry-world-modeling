"""Finite independent text-identity review; never invokes the camera guard."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import json

ROOT = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
BASE = ROOT / 'work/S45B_c1_numeric_camera_guard_supervised_v8'
ROLE = '/root/c1_v8_binding_review'
EXPECTED_BINDING = '4a71cb5620a4164bd681ce7d844d26c018c1e7597586e7339f1c1f2afed58ae9'
EXPECTED_FREEZE = 'cc277bb79babb14e2a3b6b20b88d1552155b2ae9616440f4d8a67910f52962a2'
REVIEW_HASHES = {
    'primary': '916319349f8bb85ef2dad55b8c55e4ae87b091e359541383588386708dcf17f6',
    'adversarial': 'afdd2c13eaa8e89e021e0fd4312257cb68b180ace7f3dbcfcd00784896111b83',
}
FIXED = {
    'generation_manifest': 'work/S44_c1_confirmation_generation/review_attachment_01/manifest.json',
    'generation_terminal_receipt': 'work/S44_c1_confirmation_generation/execution_01/receipt.json',
    'generation_worker_receipt': 'work/S44_c1_confirmation_generation/execution_01/worker_receipt.json',
    's45_terminal_binding': 'work/S45_c1_result_readback/terminal_binding_01.json',
    's45_supervisor_receipt': 'work/S45_c1_result_readback/supervision_01/receipt.json',
    's45_worker_receipt': 'work/S45_c1_result_readback/executed_01/receipt.json',
    's45_report': 'work/S45_c1_result_readback/executed_01/report.json',
    's45_result_review': 'work/S45_c1_result_readback/supervision_01/independent_result_review.json',
    'archive_manifest': 'results/S44_C1_confirmation_generation/archive/manifest.json',
    'archive_events': 'results/S44_C1_confirmation_generation/archive/events.jsonl',
}
STATIC = {
    's42_baseline_protocol': ('work/S42_baseline_failure_preregistration/PROTOCOL.md', 'S42_PROTOCOL_SHA256'),
    'b0_camera_reference': ('work/S42_baseline_failure_preregistration/score_b0_blind.py', 'B0_REFERENCE_SHA256'),
    'b0_primary_source_review': ('work/S42_baseline_failure_preregistration/B0_SCORER_SOURCE_REVIEW.json', 'B0_PRIMARY_REVIEW_SHA256'),
    'b0_adversarial_source_review': ('work/S42_baseline_failure_preregistration/B0_SCORER_SOURCE_REVIEW_ADVERSARIAL.json', 'B0_ADVERSARIAL_REVIEW_SHA256'),
    's45_readback_source': ('work/S45_c1_result_readback/readback.py', 'S45_READBACK_SOURCE_SHA256'),
    's45_supervisor_source': ('work/S45_c1_result_readback/supervise_readback.py', 'S45_SUPERVISOR_SOURCE_SHA256'),
    's45_result_review_expected': ('work/S45_c1_result_readback/supervision_01/independent_result_review.json', 'S45_RESULT_REVIEW_SHA256'),
}
snapshots = {}

def read(path):
    path = Path(path)
    raw = path.read_bytes()
    snapshots[str(path)] = {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    return raw

def digest(path):
    return hashlib.sha256(read(path)).hexdigest()

def utc(s):
    d = datetime.fromisoformat(s.replace('Z', '+00:00'))
    assert d.tzinfo is not None and d.utcoffset().total_seconds() == 0
    return d

assert digest(BASE/'FROZEN_SOURCE_SET.json') == EXPECTED_FREEZE
freeze = json.loads(read(BASE/'FROZEN_SOURCE_SET.json'))
assert digest(BASE/'C1_CAMERA_GUARD_BINDING_V8.json') == EXPECTED_BINDING
binding = json.loads(read(BASE/'C1_CAMERA_GUARD_BINDING_V8.json'))
template = json.loads(read(BASE/'C1_CAMERA_GUARD_BINDING_TEMPLATE.json'))
sources = freeze['source_identities']
assert len(sources) == 5
for name, value in sources.items():
    assert digest(BASE/name) == value, name
source_text = read(BASE/'camera_guard.py').decode()
constants = {}
for node in ast.parse(source_text).body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        try:
            constants[node.targets[0].id] = ast.literal_eval(node.value)
        except (ValueError, TypeError):
            pass
expected_reviewed = dict(sources)
for name, (rel, constant) in STATIC.items():
    actual = digest(ROOT/rel)
    assert actual == constants[constant], name
    expected_reviewed[name] = actual
assert constants['AUTHOR_ROLE'] == '/root'
reviews = []
for kind, expected in REVIEW_HASHES.items():
    path = BASE/f'SOURCE_REVIEW_{kind.upper()}_V8.json'
    assert digest(path) == expected
    r = json.loads(read(path))
    assert r['schema'] == 's45b-c1-numeric-camera-guard-source-review-v4'
    assert r['review_kind'] == kind
    assert r['status'] == 'PASS_S45B_C1_NUMERIC_CAMERA_GUARD_SUPERVISED_SOURCE_REVIEW_V8'
    assert r['verdict'] == 'PASS_SUPERVISED_SOURCE_NOT_EXECUTED'
    assert r['reviewed_identities'] == expected_reviewed
    assert r['author_role'] == '/root' and r['blocking_findings'] == []
    assert r['executed'] is False
    assert all(r[k] == 0 for k in ['c1_tensor_bodies_read','pixels_decoded','images_viewed'])
    assert all(isinstance(r[k],str) and r[k] for k in ['reviewer_role','reviewer_task_id','reviewer_turn_id'])
    reviews.append(r)
source_set = {**sources, **{k+'_source_review':v for k,v in REVIEW_HASHES.items()}}
assert binding['schema'] == 's45b-c1-numeric-camera-guard-binding-v4'
assert binding['status'] == 'FROZEN_C1_NUMERIC_CAMERA_GUARD_SUPERVISED_INPUT_BINDING_V8'
assert binding['row'] == 'C1' and binding['placeholder_hashes'] == 0
assert binding['source_set'] == source_set
assert binding['author_role'] == binding['author_task_id'] == '/root/heldout_reference_metadata'
assert isinstance(binding['author_turn_id'],str) and binding['author_turn_id']
assert set(binding['upstream']) == set(FIXED)
for name, rel in FIXED.items():
    item = binding['upstream'][name]
    assert set(item) == {'path','sha256'} and item['path'] == str(ROOT/rel)
    raw = read(ROOT/rel)
    assert hashlib.sha256(raw).hexdigest() == item['sha256'], name
    if rel.endswith('.jsonl'):
        for line in raw.splitlines():
            if line.strip(): json.loads(line)
    else:
        json.loads(raw)
assert binding['upstream']['generation_manifest']['sha256'] == constants['C1_MANIFEST_SHA256']
assert binding['upstream']['s45_result_review']['sha256'] == constants['S45_RESULT_REVIEW_SHA256']
for key in ['version','known_static_identities','attempt_lifecycle','supervision_lifecycle','governance_attestation_requirement','formal_output_path']:
    assert binding[key] == template[key], key
assert binding['governance_attestation_requirement']['sha256'] is None
assert len({'/root',ROLE,binding['author_role'],*[r['reviewer_role'] for r in reviews]}) == 5
assert len({ROLE,binding['author_task_id'],*[r['reviewer_task_id'] for r in reviews]}) == 4
created = utc(binding['created_utc'])
assert all(utc(r['completed_utc']) <= created for r in reviews)
assert constants['EXPECTED_YAW'] == (0.0,1.25,2.5,3.75,5.0,3.75,2.5,1.25,0.0)
assert constants['TOLERANCE'] == 1e-6
assert 'base_pose = cache_commits[1]["c2ws"][0]' in source_text
assert 'base_k = cache_commits[1]["Ks"][0]' in source_text
formal_state = {name:(BASE/name).exists() for name in ['execution_01','.c1_numeric_camera_guard.lock','.c1_numeric_camera_guard.lock.staging','GOVERNANCE_ATTESTATION_V8.json']}
assert not any(formal_state.values()), formal_state
now = datetime.now(timezone.utc).isoformat()
assert created <= utc(now)
reviewed = {**source_set, 'C1_CAMERA_GUARD_BINDING_V8.json':EXPECTED_BINDING,
            **{name:item['sha256'] for name,item in binding['upstream'].items()}}
receipt = {
    'schema':'s45b-c1-numeric-camera-guard-binding-review-v4',
    'status':'PASS_S45B_C1_NUMERIC_CAMERA_GUARD_SUPERVISED_BINDING_REVIEW_V8',
    'verdict':'PASS_SUPERVISED_BINDING_ONLY_NO_TENSOR_BODIES',
    'completed_utc':now,
    'time_basis':'Actual UTC captured after independent text identity and binding checks; no historical duration inferred.',
    'author_role':binding['author_role'],
    'reviewer_role':ROLE,
    'reviewer_task_id':ROLE,
    'reviewer_turn_id':'c1-v8-independent-binding-review-'+now,
    'reviewed_identities':reviewed,
    'blocking_findings':[],
    'checks':{
        'five_source_hashes_and_frozen_manifest':'PASS',
        'two_exact_fresh_source_reviews_full_12_identity_domain':'PASS',
        'ten_fixed_upstream_text_paths_and_actual_hashes':'PASS',
        'fifteen_prior_placeholders_resolved':'PASS',
        'lifecycle_and_limits_unchanged_from_reviewed_template':'PASS',
        'five_distinct_actual_roles_and_four_distinct_review_binding_tasks':'PASS',
        'source_reviews_before_binding_before_this_review':'PASS',
        'final_cache_id0_anchor_and_sealed_yaw_tolerance':'PASS_SOURCE_BINDING_ONLY',
        'formal_execution_lock_and_governance_absent_at_review':'PASS',
    },
    'mathematical_binding_scope':'Exact frozen worker uses final cache ID0 for planned yaw, fixed K and ID8 closure, matching sealed S42. Yaw sequence and inclusive 1e-6 tolerance are unchanged. Actual C1 c2w/K tensor values were not read or recomputed by this binding review.',
    'governance_boundary':'Distinct role and task labels correspond to this actual collaboration assignment; external root must attest provenance separately. The deliberately null future governance SHA is outside the fifteen resolved source/upstream identities.',
    'text_identity_snapshots':snapshots,
    'formal_state_at_review':formal_state,
    'executed':False,
    'c1_tensor_bodies_read':0,
    'pixels_decoded':0,
    'images_viewed':0,
    'access_ledger':{
        'candidate_functions_called':0,'formal_runner_calls':0,'model_calls':0,
        'real_tensor_or_array_body_files_opened':0,'image_body_files_opened':0,
        'source_binding_or_prior_review_files_modified':0,
        'unique_source_and_text_identity_files_hashed':len(snapshots),
    },
    'authorization_effect':'BINDING_REVIEW_ONLY; external governance, reviewed supervisor launch and exact exit-gated result review remain necessary. No model or visual-quality result is authorized by this receipt.',
}
out = BASE/'BINDING_REVIEW_V8.json'
raw = (json.dumps(receipt,ensure_ascii=False,indent=2)+'\n').encode()
with out.open('xb') as handle:
    handle.write(raw)
print(json.dumps({'path':str(out),'sha256':hashlib.sha256(raw).hexdigest(),'completed_utc':now,'unique_identity_files':len(snapshots)},indent=2))
