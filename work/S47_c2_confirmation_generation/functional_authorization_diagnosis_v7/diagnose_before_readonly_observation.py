"""Read-only real producer-consumer diagnosis. No launch, writes to formal paths, or scientific bodies."""
import ast
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import types

ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
HERE=ROOT/'work/S47_c2_confirmation_generation'
OUT=HERE/'functional_authorization_diagnosis_v7'
SOURCE=HERE/'generation_gate.py'
started_at=datetime.now(timezone.utc).isoformat()
source_bytes=SOURCE.read_bytes(); assert hashlib.sha256(source_bytes).hexdigest()=='5add4e5b6170f42ff75cdede7f40a061cd1b98a253f0fb6411444990155255ec'
def load_gate(name):
    mod=types.ModuleType(name);mod.__file__=str(SOURCE);sys.modules[name]=mod
    exec(compile(source_bytes,str(SOURCE),'exec'),mod.__dict__)
    return mod
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
formal=[HERE/'launch_authorization_01.json',HERE/'launch_authorization_attempt_01/attempt_started.json',HERE/'launch_authorization_attempt_01/success_receipt.json',HERE/'review_attachment_01/manifest.json',HERE/'review_attachment_01/receipt.json',HERE/'review_attachment_01/metadata_gate.json',HERE/'freeze_attempt_01/manifest_core.json',HERE/'freeze_attempt_01/receipt.json',HERE/'generation_gate.py',HERE/'create_launch_authorization.py',HERE/'launch_generation.py',HERE/'FINAL_ATTACHMENT_REVIEW.json',HERE/'LAUNCH_READINESS_REVIEW.json']
before={str(p):sha(p) for p in formal}
reserved=[HERE/'execution_01',HERE/'.execution_01.watchdog_failure.json',HERE/'.execution_01.supervisor_failure.json',ROOT/'results/S47_C2_confirmation_generation']
assert not any(os.path.lexists(p) for p in reserved)
orig=load_gate('_c2_v7_actual_schema_diagnosis')
manifest_path=orig.PUBLISHED_MANIFEST; manifest=orig.read_frozen(manifest_path,before[str(manifest_path)])
auth,auth_sha,identity=orig.read_json_snapshot(orig.LAUNCH_AUTHORIZATION,'diagnostic exact authorization')
start=json.loads((HERE/'launch_authorization_attempt_01/attempt_started.json').read_text())
receipt=json.loads((HERE/'launch_authorization_attempt_01/success_receipt.json').read_text())
try:
    orig.require_launch_authorization(manifest,before[str(manifest_path)])
    raise AssertionError('Unmodified validator unexpectedly passed')
except RuntimeError as exc:
    original_error={'type':type(exc).__name__,'message':str(exc)}
    assert str(exc)=='C2 authorization attempt lease is incomplete, conflicting, or unsealed'
# Evaluate each ordinary existing conjunct against actual producer data; no fabricated file or receipt.
tree=ast.parse(source_bytes)
function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='require_successful_authorization_attempt')
target=next(n for n in ast.walk(function) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='require' and len(n.args)>1 and isinstance(n.args[1],ast.Constant) and n.args[1].value=='C2 authorization attempt lease is incomplete, conflicting, or unsealed')
assert isinstance(target.args[0],ast.BoolOp) and isinstance(target.args[0].op,ast.And)
directory=orig.DirectoryBinding.open(orig.AUTHORIZATION_ATTEMPT)
context=dict(orig.__dict__);context.update({'started':start,'lease':receipt,'started_utc':orig.parse_utc(start['started_utc'],'start'),'completed_utc':orig.parse_utc(receipt['completed_utc'],'end'),'tool_sha':sha(orig.AUTHORIZATION_TOOL),'expected':before[str(manifest_path)],'attempt_directory':directory,'started_sha':before[str(orig.AUTHORIZATION_ATTEMPT_STARTED)],'authorization_sha':auth_sha,'authorization_identity':identity})
predicates=[]
try:
    for i,expression in enumerate(target.args[0].values):
        val=eval(compile(ast.Expression(expression),str(SOURCE),'eval'),context)
        predicates.append({'index':i,'expression':ast.unparse(expression),'passed':bool(val)})
finally:directory.close()
failed=[p for p in predicates if not p['passed']]
assert len(failed)==1 and failed[0]['expression']=="lease.get('authorization_identity') == authorization_identity"
# In-memory adaptation only, limited to one contract normalization in the actual reader function.
patched=load_gate('_c2_v7_inmemory_contract_projection_only')
fn=copy.deepcopy(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='require_launch_authorization'))
assert isinstance(fn.body[0],ast.Expr) and isinstance(fn.body[1],ast.Assign)
normalization=ast.parse("authorization_identity = {key: authorization_identity[key] for key in ('device', 'inode', 'size', 'mode')}").body[0]
fn.body.insert(2,normalization)
module=ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[]))
exec(compile(module,'<DIAGNOSTIC_IN_MEMORY_FOUR_FIELD_IDENTITY_ONLY>','exec'),patched.__dict__)
patched_authorization=patched.require_launch_authorization(manifest,before[str(manifest_path)])
control=patched.open_launch_control_lease(manifest_path,before[str(manifest_path)])
try:
    held_summary=control.validate()
    metadata=patched.check_manifest(manifest_path,before[str(manifest_path)],metadata_only=True)
    assert metadata['status']=='PASS_METADATA_ONLY'
    namespace={'__file__':str(HERE/'launch_generation.py'),'PYTHON':Path(manifest['runtime']['python_executable']),'PYTHONPATH':[Path(p) for p in manifest['runtime']['pythonpath']]}
    assert 'GATE' not in patched.__dict__
    try:
        control.frozen_manifest(manifest_path,before[str(manifest_path)],namespace)
        raise AssertionError('Missing GATE name unexpectedly passed')
    except NameError as exc:
        downstream_error={'type':type(exc).__name__,'message':str(exc)}
        assert str(exc)=="name 'GATE' is not defined"
    # One in-memory name binding proves the intended existing path check; source and real controls stay unchanged.
    patched.GATE=HERE/'generation_gate.py'
    frozen=control.frozen_manifest(manifest_path,before[str(manifest_path)],namespace)
    assert frozen==manifest
    control.validate()
finally:control.close()
assert control.closed
assert {str(p):sha(p) for p in formal}==before
fresh={str(p):not os.path.lexists(p) for p in reserved};assert all(fresh.values())
scientific=[n for n in sys.modules if n.split('.')[0] in {'torch','numpy','PIL','cv2','diffusers','transformers','safetensors'}];assert scientific==[]
result={'schema':'s47-c2-functional-authorization-diagnostic-evidence-v1','started_utc':started_at,'completed_utc':datetime.now(timezone.utc).isoformat(),'unmodified_validator_error':original_error,'actual_producer_authorization_identity':receipt['authorization_identity'],'actual_reader_snapshot_identity':identity,'missing_from_producer_keys':sorted(set(identity)-set(receipt['authorization_identity'])),'shared_fields_all_equal':all(receipt['authorization_identity'][k]==identity[k] for k in receipt['authorization_identity']),'existing_conjuncts_evaluated':predicates,'failed_conjunct_count':len(failed),'minimal_inmemory_projection':'Normalize the existing durable authorization identity to device/inode/size/mode once in require_launch_authorization after read_json_snapshot; keep complete six-field live descriptor identity validation in read_regular_snapshot and RegularBinding.','after_identity_projection':{'require_launch_authorization':'PASS_DIAGNOSTIC_READ_ONLY','open_launch_control_lease':'PASS_DIAGNOSTIC_READ_ONLY','held_directories':len(held_summary['directories']),'held_files':len(held_summary['files']),'control_validate':'PASS_DIAGNOSTIC_READ_ONLY','metadata_only_check':'PASS_DIAGNOSTIC_READ_ONLY','frozen_manifest_before_Gate_binding':downstream_error,'frozen_manifest_after_inmemory_Gate_binding':'PASS_DIAGNOSTIC_READ_ONLY'},'second_minimal_fix_candidate':'Bind GATE to HERE / generation_gate.py in generation_gate.py, or replace only the two uses within frozen_manifest with that already frozen path. No relaxation of source hash checks.','formal_artifact_sha256_before_and_after':before,'formal_reserved_paths_still_absent':fresh,'scientific_modules_present':scientific,'execution_boundary':{'formal_launcher_calls':0,'authorization_tool_calls':0,'prepare_attach_calls':0,'new_attempts_created':0,'frozen_source_or_bundle_edits':0,'models_loaded':0,'scientific_imports':0,'component_bodies_read':0,'input_bodies_read':0,'pixels_decoded':0,'generation_calls':0,'real_pipeline_executed':False,'tests_rerun':0},'limitations':['The two in-memory adaptations are diagnostic evidence only. They are not executable production authority, a new source freeze, a new authorized attempt, or generation.','No scientific body was opened and no full-resource gate was invoked; later model/runtime behavior remains untested.','The sole public launcher failure is preserved. The metadata checks cannot determine policy for any future retry or source rebase; root must preserve all frozen control artifacts and use a separately recorded repair path.']}
path=OUT/'evidence.json'
with path.open('x') as out:json.dump(result,out,indent=2);out.write('\n')
print(json.dumps({'path':str(path),'sha256':sha(path),'failed_predicates':failed,'subsequent_read_only_chain':result['after_identity_projection'],'formal_paths_unchanged':True},indent=2))
