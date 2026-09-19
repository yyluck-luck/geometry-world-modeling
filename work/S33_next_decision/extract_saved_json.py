"""S33 decision support: read sealed JSON metadata/scalars only, never arrays/GT."""
from pathlib import Path
import datetime
import hashlib
import json

ROOT = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
WS = Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip')
OUT = Path(__file__).resolve().parent

def sha(path):
    path=Path(path)
    if path.suffix.lower() in {'.npz','.npy','.png','.jpg','.jpeg','.pth','.pt'}:
        raise ValueError('This task must not read scientific array/image/model bytes')
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(rel):
    path=ROOT/rel
    assert path.suffix == '.json'
    return json.loads(path.read_text())

def save(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

started=datetime.datetime.now(datetime.timezone.utc).isoformat()
m=read('results/S33_pair_scale_scoring/metrics.json')
assert (m['prespecified_windows'],m['prespecified_groups'],m['prespecified_rows'],m['scored_rows'],m['unavailable_rows']) == (4,16,64,48,16)
keys=('absrel','rmse_m','delta1','aggregation','all_four_rows_scored','scored_frames','unavailable_frames')
groups={wid:{ep:{key:group.get(key) for key in keys} for ep,group in eps.items()} for wid,eps in m['window_groups'].items()}
comparison={}
for wid,eps in groups.items():
    x=eps['common_pair_scale_400']
    if x['absrel'] is None:
        comparison[wid]={'status':'NA_PRESERVED'}
        continue
    comparison[wid]={name:{'absrel_lower':x['absrel']<eps[name]['absrel'],
                          'rmse_lower':x['rmse_m']<eps[name]['rmse_m'],
                          'delta1_higher':x['delta1']>eps[name]['delta1']} for name in ('initial_0step','global_rescaled_400')}
old=read('results/S29_scale_control/C2a/inputs_seal.json')
control=read('work/S26B_execution/control_receipt.json')
parent=read('work/S26B_preparation/run_manifest.json')
cut=parent['candidate']['archives']['cut3r']
head_identity=[{'frame':i,'old4_source_path':old['saved_heads'][i]['path'],'old4_saved_sha':old['saved_heads'][i]['sha256'],
               'eight_source_path':cut[i]['path'],'eight_saved_sha':cut[i]['sha256'],
               'same_archive_sha':old['saved_heads'][i]['sha256']==cut[i]['sha256']} for i in range(4)]
assert not any(row['same_archive_sha'] for row in head_identity)
assert old['control_sha256']==control['output_sha256']
assert old['parent_manifest_sha256']==sha(ROOT/'work/S26B_preparation/run_manifest.json')
excerpt={'created_utc':started,'scope':'Saved JSON scalar/metadata extraction only; no independent numerical scoring',
 'metrics_sha256':sha(ROOT/'results/S33_pair_scale_scoring/metrics.json'),
 'window_groups':groups,'ordinary_control_vs_strong_baselines':comparison,
 'denominators':{k:m[k] for k in ('prespecified_windows','prespecified_groups','prespecified_rows','imported_rows','new_rows','scored_rows','unavailable_rows')},
 'independent_S33_numeric_review':'PENDING_AT_TASK_ASSIGNMENT_NOT_RECHECKED_HERE',
 'head_archive_provenance_comparison':head_identity,
 'same_camera_file_identity':{'old4_reference':old['control_sha256'],'eight_reference':control['output_sha256'],
  'equality':True,'scope':'receipt metadata equality; runtime must check bytes and prefix decoded camera tolerance'},
 'S29_to_S30_actual_initial_state_gate':read('results/S30_scale_optimization/C2a/s29_reference_gate.json'),
 'S26B_actual_assembly_preprocess_compatibility':read('work/S26B_execution/compatibility_receipt.json'),
 'proposed_common_old_source_receipt':read('results/S29_scale_control/C2a/receipt.json'),
 'array_bytes_read':0,'GT_bytes_read':0,'model_calls':0,'GA_runs':0,'MST_runs':0}
save('evidence_excerpt.json',excerpt)
base=ROOT/'work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R'
specs=[
(ROOT/'AGENTS.md',None,'Project task rules'),
(ROOT/'RESEARCH_PRINCIPLES.md',None,'Continuing user constraints'),
(ROOT/'RESEARCH_MEMORY.md',None,'Current project context; source snapshot only'),
(ROOT/'RESEARCH_LOG.md',None,'Latest S33 producer/scoring events at read time'),
(ROOT/'results/S33_pair_scale_scoring/metrics.json',None,'Saved primary scores'),
(ROOT/'results/S33_pair_scale_scoring/receipt.json',None,'Main scoring scope and producer seals'),
(ROOT/'work/S33_preparation/contract.json',None,'Frozen producer contract'),
(ROOT/'work/S33_preparation/PROTOCOL_CANDIDATE.md',None,'S33 exact all-trainable intervention'),
(ROOT/'work/S33_preparation/run_s33.py',None,'Previously authored fixed implementation'),
(ROOT/'work/S32_next_decision/review.md',None,'Existing DUSt3R/Scal3R/LASER and skill reasoning'),
(ROOT/'work/S25_consumer_relevance/consumer_relevance.md',None,'Original consumer and fresh state audit'),
(ROOT/'work/S26_commit_consistency_source/audit.md',None,'Old map and focal cache semantics'),
(ROOT/'work/S26_consumer_baseline_preparation/plan.md',None,'Existing eight-frame saved-head semantics'),
(ROOT/'work/S26_consumer_baseline_preparation/saved_heads_adapter.py',[32,205],'Original adapters and old provenance hard-coded gate'),
(ROOT/'work/S26B_preparation/plan.md',None,'Original continuation scope'),
(ROOT/'work/S26B_preparation/run_manifest.json',None,'Exact old input/archive/control source identity'),
(ROOT/'work/S26B_execution/control_receipt.json',None,'Identical eight-frame optical camera file'),
(ROOT/'work/S26B_execution/compatibility_receipt.json',None,'Actual existing preprocessing and star compatibility'),
(ROOT/'results/S26B_consumer_baseline/cut3r/receipt.json',None,'Historical eight-image runtime and fixed parameter flags'),
(ROOT/'results/S29_scale_control/C2a/inputs_seal.json',None,'Original4 source and camera reference'),
(ROOT/'results/S29_scale_control/C2a/receipt.json',None,'Saved initialization output identities, not array reads'),
(ROOT/'results/S29_scale_control/C2a/initial_raw_metadata.json',None,'Stored raw confidence/depth and parameter schema'),
(ROOT/'results/S30_scale_optimization/C2a/s29_reference_gate.json',None,'Actual historical 33 raw state identity gate'),
(ROOT/'work/S29_scale_control_preparation/run_s29.py',[168,194],'Saved initial decoded schema and no-update boundary'),
(base/'surfel_inference.py',[174,218],'Preset order; GA and original clean'),
(base/'cloud_opt/dust3r_opt/init_im_poses.py',[78,139],'MST all-frame set-depth and pose initialization'),
(base/'cloud_opt/dust3r_opt/optimizer.py',[206,261],'First4 preset/freeze, setter write guard, depth decoding'),
(base/'cloud_opt/dust3r_opt/base_opt.py',[349,359],'Original class clean wrapper'),
(WS/'work/vmem/modeling/pipeline.py',[633,765],'Render/vote/NMS and true context dependencies'),
(WS/'work/vmem/modeling/pipeline.py',[770,1082],'Original merge, pointmap and append/cache routing'),
(WS/'work/vmem/configs/inference/inference.yaml',None,'Original consumer defaults'),
(ROOT/'src/s18_original_kernels.py',None,'Original pointmap and storage kernels'),
(ROOT/'src/vmem_memory_kernel.py',None,'Existing original surfel memory kernels'),
(ROOT/'src/vmem_retrieval_kernel.py',[244,335],'Existing context retains NMS/latent dependencies'),
(ROOT/'docs/S18_RESULTS.md',None,'Actual existing original two-frame consumer experiment; limited scope'),
(ROOT/'docs/S18_EXECUTION_MANIFEST.json',None,'Existing kernel provenance'),
(ROOT/'work/S25_official_resource_recheck/report.md',None,'Last checked generator/VAE resource status; not live check'),
(WS/'work/Supervisor-Skills/handbook/02_Idea_Generation/2.2_想Idea的思路_更高更快更强.md',None,'Applied baseline failure to consumer hypothesis'),
(Path('/Users/rocket/.codex/skills/idea-evaluator/SKILL.md'),None,'Previously read: fatal flaws before novelty commitment'),
(Path('/Users/rocket/.claude/skills/sci-scientific-critical-thinking/SKILL.md'),None,'Previously read: confounds, stronger controls, evidence bounds')]
sources=[]
for path,lines,reason in specs:
 sources.append({'path':str(path),'sha256':sha(path),'relevant_lines':lines,'use':reason})
save('sources.json',{'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'source_commit':'39291e4f272f6b4f270691d930926ab5930f942e','commit_basis':'Existing frozen S26B manifest binding; no live remote recheck',
 'Supervisor_commit':'207bc6f7a1aa107e544099c2c7cc86816fba9628',
 'read_scope':'This bounded audit and previously read exact source/skills reused; hashes acquired now. No scientific arrays or GT opened.',
 'sources':sources})
completed=datetime.datetime.now(datetime.timezone.utc).isoformat()
save('completion_receipt.json',{'status':'DESIGN_COMPLETE_NOT_EXECUTION_READY','recorded_utc':completed,
 'artifact_metadata_extraction_started_utc':started,'artifact_metadata_extraction_completed_utc':completed,
 'audit_duration':'NOT_RECONSTRUCTED; timestamps above measure only final artifact extraction and identity recording',
 'parent_decision':'Parent accepted reused S26B first8 direction in conversation; actual implementation/execution remains unapproved by parent at this stage',
 'selected_next_task':'One shared old4 map -> eight-frame fixed-old-depth consumer pilot, zero/free400/common-scale400',
 'minimum_new_counts_if_frozen':{'model':0,'MST':2,'PnP':14,'Adam':800,'backward':800,'clean':4,'objective':806},
 'actual_this_audit_counts':{'scientific_array_bytes_read':0,'GT_bytes_read':0,'model':0,'MST':0,'GA':0,'backward':0,'new_web_search':0},
 'default_final_context_IDs':'NOT_EXECUTED; no legal NMS/cache history for cold 4->8',
 'full_video':'NOT_EXECUTED; resources not provided by geometry component success',
 'minor_read_error':'First scalar inspection treated window_groups as list; KeyError before any data extraction. Corrected to documented dict. No scientific computation failed or retried.',
 'canonical_files_changed':False,'old_frozen_files_changed':False,
 'outputs':{p.name:sha(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='completion_receipt.json'}})
print(json.dumps({'completed_utc':completed,'outputs':{p.name:sha(p) for p in sorted(OUT.iterdir()) if p.is_file()}},ensure_ascii=False,indent=2))
