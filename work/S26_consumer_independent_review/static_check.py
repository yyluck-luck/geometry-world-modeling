"""Independent source/metadata-only S26 checks; no adapter import or data reads."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json

ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
W=ROOT/'work/S26_consumer_baseline_preparation'
OUT=ROOT/'work/S26_consumer_independent_review'
ORIGINAL=Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem')

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read_json(p): return json.loads(Path(p).read_text())
def dump(n): return ast.dump(n,include_attributes=False)
def top_functions(p): return {n.name:n for n in ast.parse(Path(p).read_text()).body if isinstance(n,ast.FunctionDef)}

binding=read_json(W/'source_binding.json')
prep=read_json(W/'preparation_receipt.json')
candidate=read_json(W/'candidate_inputs.json')
embedded=Path(binding['embedded_root'])
source_root=Path(binding['source_root'])
checks=[]

def check(name,passed,evidence):
    checks.append({'id':name,'passed':bool(passed),'evidence':evidence})

check('preparation_artifacts_current',all(sha(p)==h for p,h in prep['identities'].items()),'Source and metadata artifacts only; no archived prediction bytes hashed.')
source_mismatches=[p for p,h in binding['source_identities'].items() if sha(p)!=h]
check('bound_source_and_metadata_identities',not source_mismatches,{'count':len(binding['source_identities']),'mismatches':source_mismatches})
relevant=['extern/CUT3R/surfel_inference.py','extern/CUT3R/cloud_opt/dust3r_opt/optimizer.py','extern/CUT3R/cloud_opt/dust3r_opt/base_opt.py','extern/CUT3R/cloud_opt/dust3r_opt/init_im_poses.py','extern/CUT3R/src/dust3r/utils/image.py','modeling/pipeline.py']
parity={r:sha(ORIGINAL/r)==sha(source_root/r) for r in relevant}
check('reviewed_original_and_actual_isolated_source_match',all(parity.values()),parity)
original=top_functions(embedded/'surfel_inference.py')
derived=top_functions(W/'derived_original_functions.py')
for name in ('listify','collate_with_cat','prepare_input_from_pil','prepare_output'):
    check('derived_original_function_'+name,dump(original[name])==dump(derived[name]),'Entire AST, excluding source locations, equal; no function imported or executed.')
body=original['run_inference_from_pil'].body
start=next(i for i,n in enumerate(body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='output' for t in n.targets))
end=next(i for i,n in enumerate(body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='total_time' for t in n.targets))
region=body[start:end]
removed=[]; remaining=[]
for node in region:
    if isinstance(node,ast.Assign) and ast.unparse(node)=='outputs, state_args = inference(views, model, device)': removed.append(node)
    else: remaining.append(node)
assembled=derived['build_original_output']
check('only_network_call_removed',len(removed)==1 and len(remaining)==11,{'removed_statements':len(removed),'preserved_statements':len(remaining)})
check('star_assembly_exact_ast',list(map(dump,remaining))==list(map(dump,assembled.body[:-1])) and isinstance(assembled.body[-1],ast.Return) and isinstance(assembled.body[-1].value,ast.Name) and assembled.body[-1].value.id=='output','All remaining original assembly statements plus return output; no copied math edited.')
check('candidate_intact_eight_prefix',[x['index'] for x in candidate['frames']]==list(range(8)) and candidate['prefix_length']==4 and candidate['new_frame_indices']==[4,5,6,7],'Frame indices and timestamps only, not RGB bytes or camera coordinates.')
check('candidate_archive_counts', {k:len(v) for k,v in candidate['archives'].items()}=={'common_old_depth_original4':4,'cut3r':8,'ttt3r':8,'filt3r':8},'Only archive records read; no NPZ bytes or headers opened.')
check('old_packet_original_mode',candidate['producer_receipts']['common_old_depth_original4']['mode']=='original4','Source metadata identifies original4, not the alternative source cut3r-mode prefix.')
check('all_archive_indices_intact',all([x['index'] for x in v]==list(range(len(v))) for v in candidate['archives'].values()),'No skipped metadata indices.')
check('camera_oracle_explicit',candidate['given_pose_condition']['role']=='common oracle camera condition, not blinded/deployable pose estimation' and candidate['given_pose_condition']['coordinates_read_now'] is False,'No groundtruth file opened by this review.')
check('depth_scoring_only_explicit','scoring-only' in candidate['depth_input_prohibition'] and 'never used as common old depth' in candidate['depth_input_prohibition'],'Metadata policy checked; future runner enforcement is still required.')
for p in (W/'saved_heads_adapter.py',W/'prepare_metadata.py',W/'derived_original_functions.py'):
    ast.parse(p.read_text(),filename=str(p))
check('python_ast_parse_only',True,'AST parse, no import, no compiled module execution.')
source_import_reads=[str(W/name) for name in ('saved_heads_adapter.py','prepare_metadata.py','derived_original_functions.py','plan.md','source_binding.json','candidate_inputs.json','preparation_receipt.json')]
source_import_reads += [str(source_root/r) for r in relevant]
report={'schema':'s26-independent-source-metadata-check-v1','recorded_utc':datetime.now(timezone.utc).isoformat(),'passed':all(c['passed'] for c in checks),'check_count':len(checks),'checks':checks,'reviewed_identities':{p:sha(p) for p in source_import_reads},'scope':{'source_metadata_only':True,'adapter_imported':False,'real_npz_or_image_bytes_opened':False,'gt_coordinates_parsed':False,'model_or_ga_run':False,'new_numerical_compatibility_test':False},'not_execution_ready':'This static check does not supply the missing supervisor runner, observer, scorer, frozen runtime contract or real preprocessing checks.'}
(OUT/'static_check_receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':report['passed'],'check_count':len(checks),'failed':[c['id'] for c in checks if not c['passed']],'recorded_utc':report['recorded_utc']},ensure_ascii=False))
