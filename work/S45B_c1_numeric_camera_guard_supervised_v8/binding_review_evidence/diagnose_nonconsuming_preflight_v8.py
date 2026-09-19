"""Read-only metadata diagnosis; hypothetical repairs exist only in memory."""
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime, timezone
import ast
import fcntl
import hashlib
import importlib.util
import json
import os
import traceback

ROOT = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
BASE = ROOT/'work/S45B_c1_numeric_camera_guard_supervised_v8'
ROLE = '/root/c1_v8_binding_review'
started = datetime.now(timezone.utc).isoformat()
identities = {}

def read(path):
    raw = Path(path).read_bytes()
    identities[str(path)] = {'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
    return raw

def load(name, path):
    spec = importlib.util.spec_from_file_location(name,path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

supervisor_path = BASE/'supervise_camera_guard.py'
worker_path = BASE/'camera_guard.py'
assert hashlib.sha256(read(supervisor_path)).hexdigest() == '2f9b64ecf8fe262f46d1cf7e4c5b823aa6d6498f6fec70d7d5f66a62ebafa752'
assert hashlib.sha256(read(worker_path)).hexdigest() == 'fce7afb1a74bdc8c590c1470b0a53740b83dc295cd9571ccb91cda078f3ddf0e'
original = json.loads(read(ROOT/'work/resumption_20260908/C1_V8_FORMAL_ORCHESTRATION.json'))
argv = original['argv']; first=argv.index('--self-sha256')
args=SimpleNamespace(**{argv[i][2:].replace('-','_'):argv[i+1] for i in range(first,len(argv),2)})
binding=json.loads(read(BASE/'C1_CAMERA_GUARD_BINDING_V8.json'))
for name in ['SOURCE_REVIEW_PRIMARY_V8.json','SOURCE_REVIEW_ADVERSARIAL_V8.json','BINDING_REVIEW_V8.json','GOVERNANCE_ATTESTATION_V8.json']:
    read(BASE/name)
docs={}
for name,item in binding['upstream'].items():
    raw=read(item['path'])
    assert hashlib.sha256(raw).hexdigest()==item['sha256']
    if name!='archive_events':docs[name]=json.loads(raw)
sup=load('s45b_v8_diagnostic_supervisor',supervisor_path)
worker,worker_record=sup.load_worker_same_fd(args.worker_sha256)
formal_names=['execution_01','.c1_numeric_camera_guard.lock','.c1_numeric_camera_guard.lock.staging']
before={name:(BASE/name).exists() for name in formal_names}
assert not any(before.values())
fd=os.open(BASE,os.O_RDONLY|os.O_DIRECTORY|os.O_CLOEXEC|os.O_NOFOLLOW)
parent_identity=worker.inode_identity(os.fstat(fd))
fail={}
try:
    worker.verify_directory_lease(fd,BASE,parent_identity)
    fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
    try:
        worker.formal_preflight(sup.worker_namespace(args),fd,parent_identity)
        raise AssertionError('Exact original V8 unexpectedly passed')
    except ValueError as error:
        fail={'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()}
    assert fail['message']=='S45 terminal binding does not bind this C1 terminal/archive set'
    tree=ast.parse(read(worker_path).decode())
    upstream_fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='verify_upstream')
    env=dict(worker.__dict__);env.update({'binding':binding,'upstream':binding['upstream'],'docs':docs})
    active=False;predicate_audit=[]
    for stmt in upstream_fn.body:
        if isinstance(stmt,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='manifest' for t in stmt.targets):
            active=True
        if not active:continue
        if isinstance(stmt,ast.Assign):
            exec(compile(ast.Module([stmt],type_ignores=[]),'<original-metadata-assignment>','exec'),env)
        elif isinstance(stmt,ast.Expr) and isinstance(stmt.value,ast.Call) and isinstance(stmt.value.func,ast.Name) and stmt.value.func.id=='require':
            call=stmt.value;expr=call.args[0]
            operands=expr.values if isinstance(expr,ast.BoolOp) and isinstance(expr.op,ast.And) else [expr]
            bad=[]
            for operand in operands:
                value=eval(compile(ast.Expression(operand),'<ordinary-metadata-schema-predicate>','eval'),env)
                if value is not True:bad.append({'condition':ast.unparse(operand),'actual_evaluation':value})
            predicate_audit.append({'message':ast.literal_eval(call.args[1]),'predicate_count':len(operands),'false_conditions':bad})
    assert sum(bool(row['false_conditions']) for row in predicate_audit)==2
    text=ast.unparse(upstream_fn)
    changes=[
        ("refs = terminal.get('references', {})", 'refs = terminal'),
        ("report.get('schema') == 's45-c1-real-saved-output-readback-v1'", "report.get('saved_quantity_consumption_status') == 'VERIFIED_BY_IDENTITY_BOUND_ARCHIVED_ARRAY_CHAIN_IF_THIS_REPORT_PASSES'"),
        ("report.get('status') == 'PASS_SAVED_C1_IDENTITIES_AND_CACHE_CONSUMPTION_ONLY'", "report.get('pixel_identity_status') == 'ARCHIVED_PIL_PIXEL_TENSORS_AND_ARCHIVE_FILE_BYTES_IDENTITY_ONLY'"),
    ]
    for old,new in changes:
        assert text.count(old)==1
        text=text.replace(old,new)
    isolated=dict(worker.__dict__)
    exec(compile(text,'<diagnostic-only-two-schema-adaptations>','exec'),isolated)
    preflight_fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='formal_preflight')
    exec(compile(ast.Module([preflight_fn],type_ignores=[]),'<diagnostic-only-readonly-preflight>','exec'),isolated)
    corrected=isolated['formal_preflight'](sup.worker_namespace(args),fd,parent_identity)
    correction={
        'status':'PASS_DIAGNOSTIC_IN_MEMORY_READ_ONLY_PREFLIGHT_ONLY',
        'changes':[{'old':a,'new':b} for a,b in changes],
        'patched_function_sha256':hashlib.sha256(text.encode()).hexdigest(),
        'bound_text_record_count':len(corrected['records']),
        'event_summary':corrected['event_summary'],
        'capture_group_names':list(corrected['captures']),
        'same_records_complete':True,
        'runtime_capability_preflight_called':False,
        'formal_supervision_called':False,
    }
finally:
    os.close(fd)
    sup.close_loaded_worker_lease(worker)
after={name:(BASE/name).exists() for name in formal_names}
assert after==before
for path,record in identities.items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==record['sha256']
completed=datetime.now(timezone.utc).isoformat()
receipt={
    'schema':'s45b-c1-nonconsuming-preflight-diagnosis-v8',
    'status':'BLOCKED_V8_FROZEN_SOURCE_UPSTREAM_SCHEMA_ADAPTATION',
    'started_utc':started,'completed_utc':completed,
    'reviewer_role':ROLE,'reviewer_task_id':ROLE,
    'reviewer_turn_id':'c1-v8-nonconsuming-preflight-diagnosis-'+completed,
    'original_orchestration_returncode':original['returncode'],
    'original_stdout_and_stderr_empty':original['stdout_sha256']==original['stderr_sha256']=='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    'original_readonly_preflight_failure':fail,
    'upstream_predicate_audit':predicate_audit,
    'blocking_findings':[
        {'id':'V8_SCHEMA_01','source':'camera_guard.py:706','finding':'The already frozen S45 terminal binding stores external_receipt, worker_receipt and archive_manifest at top level. V8 mistakenly reads a nonexistent references wrapper, causing six exact path/hash predicates to fail.','minimal_fix':'In a new source version, bind refs to terminal itself. Preserve all existing paths and digests.'},
        {'id':'V8_SCHEMA_02','source':'camera_guard.py:758','finding':'The already frozen report has no schema or status keys. Those are worker-receipt fields. The original S45 report instead emits saved_quantity_consumption_status and pixel_identity_status; its SHA is already bound by worker/supervisor/result-review.','minimal_fix':'In a new source version, validate the two actual report sentinel fields and retain all row, manifest, cache-count, no-quality, hash and review checks. Do not insert invented fields into historical report.'},
    ],
    'original_schema_evidence':{
        'terminal_binding_has_references': 'references' in docs['s45_terminal_binding'],
        'terminal_binding_top_level_reference_keys':[k for k in ['external_receipt','worker_receipt','archive_manifest'] if k in docs['s45_terminal_binding']],
        'report_has_schema':'schema' in docs['s45_report'],'report_has_status':'status' in docs['s45_report'],
        'report_saved_quantity_consumption_status':docs['s45_report']['saved_quantity_consumption_status'],
        'report_pixel_identity_status':docs['s45_report']['pixel_identity_status'],
        'original_emitter_source':'work/S45_c1_result_readback/readback.py:170-201',
    },
    'diagnostic_in_memory_repair':correction,
    'source_and_input_identities':identities,
    'formal_paths_before':before,'formal_paths_after':after,
    'execution_boundary':{
        'new_formal_supervision_calls':0,'runtime_capability_calls':0,
        'attempt_lock_or_output_directory_created':False,
        'real_camera_tensor_or_array_bodies_read':0,'image_body_files_opened':0,
        'pixels_decoded':0,'images_viewed':0,'model_calls':0,
        'frozen_source_or_input_files_modified':0,
    },
    'interpretation':'The input binding hashes and role/time links are correct, but source-level V8 parsing is incompatible with two existing upstream document schemas. The earlier binding review remains a preserved identity-only PASS; it does not establish executable preflight. V8 currently cannot execute. The hypothetical in-memory metadata fix passes to the existing precommit text/event boundary, not to tensor reads, runtime capability, numeric results, or visual scoring.',
    'next_step':'Create the smallest new source version adapting only the two documented upstream schemas and required version identities; reuse the observed text fixtures for an ordinary metadata integration regression, then follow existing fresh review/binding rules. Preserve V8 and all original failure artifacts. No additional security mechanism is needed.',
}
out=BASE/'NONCONSUMING_PREFLIGHT_DIAGNOSIS_V8.json'
raw=(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n').encode()
with out.open('xb') as f:f.write(raw)
print(json.dumps({'path':str(out),'sha256':hashlib.sha256(raw).hexdigest(),'completed_utc':completed,'diagnostic_repair':correction},indent=2))
