"""Static source and existing JSON receipt audit only. No model/array loading."""
from pathlib import Path
from datetime import datetime,timezone
import ast
import hashlib
import json
import subprocess

ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
SOURCE=Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem')
OUT=ROOT/'work/S19_feedback_path'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()
started=utc()
expected={'modeling/pipeline.py':'90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e','utils/util.py':'0b71dcf6d4a43109d785f49d9c6def37b1256c4d189ab9438bfb185f3099f013','configs/inference/inference.yaml':'8d849588016935573a22ef6aaee567f71125ca4d3bdf18f51e3552a64be9fea3'}
for p,h in expected.items():assert sha(SOURCE/p)==h
assert subprocess.check_output(['/usr/bin/git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip()=='39291e4f272f6b4f270691d930926ab5930f942e'
assert not subprocess.check_output(['/usr/bin/git','-C',str(SOURCE),'status','--porcelain','--untracked-files=no'],text=True).strip()
tree=ast.parse((SOURCE/'modeling/pipeline.py').read_text())
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='VMemPipeline')
methods={n.name:n for n in cls.body if isinstance(n,ast.FunctionDef)}
scope=['initialize','reset','merge_surfels','construct_and_store_scene','render_surfels_to_image','process_retrieved_spatial_information','get_context_info','get_cond','_generate_frames_for_trajectory','generate_trajectory_frames','undo_latest_move','__call__']
geometry_targets=[];threshold_targets=[];mutating_list_calls=[]
for name in scope:
 for node in ast.walk(methods[name]):
  if isinstance(node,ast.Attribute) and isinstance(node.ctx,ast.Store):
   if node.attr in {'position','normal','radius','color'}:geometry_targets.append(dict(method=name,line=node.lineno,target=ast.unparse(node)))
   if node.attr=='initial_threshold':threshold_targets.append(dict(method=name,line=node.lineno,target=ast.unparse(node)))
  if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and ast.unparse(node.func).startswith('self.surfels.'):
   mutating_list_calls.append(dict(method=name,line=node.lineno,call=ast.unparse(node.func)))
unused=[n.lineno for n in ast.walk(methods['construct_and_store_scene']) if isinstance(n,ast.Name) and n.id=='time_indices' and isinstance(n.ctx,ast.Load)]
assert geometry_targets==[] and unused==[]
assert sorted(v['line'] for v in threshold_targets)==[698,700,705]
assert mutating_list_calls==[{'method':'construct_and_store_scene','line':1082,'call':'self.surfels.extend'}]
observations=dict(method_spans={name:[methods[name].lineno,methods[name].end_lineno] for name in scope},direct_geometry_attribute_store_targets=geometry_targets,construct_time_indices_parameter_loads=unused,initial_threshold_store_targets=threshold_targets,surfel_list_method_calls=mutating_list_calls,
 limitations='Attribute-store AST results supplement manual reading of aliases, constructors, render copies and list/map mutation. This is not whole-program theorem proving or executed inference.')
text_files=[ROOT/'AGENTS.md',ROOT/'RESEARCH_PRINCIPLES.md',ROOT/'RESEARCH_MEMORY.md',ROOT/'RESEARCH_LOG.md',ROOT/'docs/S19_RESEARCH_QUESTION_TRIAGE.md',ROOT/'docs/S19_FEEDBACK_PATH_AUDIT.md',ROOT/'results/S18_s17c_memory_bridge/run_metadata.json',ROOT/'results/S18_independent/verification.json',ROOT/'results/S17C_embedded_geometry/run_metadata.json',ROOT/'docs/S17_FULL_VIDEO_BASELINE_FEASIBILITY.md',ROOT/'docs/S17_FULL_VIDEO_BASELINE_FEASIBILITY_ADDENDUM.md']
source_files=[SOURCE/p for p in expected]+[SOURCE/'navigation.py',SOURCE/'app.py']
run=json.loads((ROOT/'results/S18_s17c_memory_bridge/run_metadata.json').read_text())
verify=json.loads((ROOT/'results/S18_independent/verification.json').read_text())
assert run['status']=='SUCCESS' and run['model_calls']==run['full_context_calls']==0 and run['video_generated'] is False and verify['status']=='PASS'
receipt=dict(schema='s19-feedback-static-audit-v1',status='COMPLETE_STATIC_AUDIT_ORIGINAL_COORDINATE_OVERWRITE_VERSION_REJECTED',
 script_started_utc=started,recorded_utc=utc(),timestamp_scope='Static read/grep/manual reasoning occurred before this receipt in the same turn; no exact earlier timestamps or elapsed research labor invented.',source_commit='39291e4f272f6b4f270691d930926ab5930f942e',
 identities={str(p):sha(p) for p in source_files+text_files+[Path(__file__)]},observations=observations,
 verdict=dict(original_question='Reject and Pivot: existing Surfel geometry field overwrite by generated descendants',fatal_flaw='F6 / CRITICAL construct-to-experiment mismatch, based on the fixed source, not baseline performance data',append_competition='Static path exists, not a verified generated-error effect',source_association='Static path exists and is distinct from coordinate overwrite',latent_embedding_feedback='Static original sampler-cache-conditioning path exists; no actual generated parent log in audited project evidence',new_narrow_question='Source-association effects on later conditioning with fixed existing geometry and query pixel provenance; unverified and not approved as novel method'),
 runtime_evidence=dict(s18_run_status=run['status'],s18_new_model_calls=run['model_calls'],s18_full_context_calls=run['full_context_calls'],s18_video_generated=run['video_generated'],s18_verifier_status=verify['status'],interpretation='Actual two-real-photo component evidence does not contain generated descendants or a generation dependency DAG.'),
 static_entry_cases=[dict(case='default app/Navigator 4 target request',model_target_slots=7,padding_slots=3,actual_append_if_call_completes=4,history_after_first_call=5,next_NMS_len5_gate=True),dict(case='direct long first trajectory with >=7 actual targets',model_target_slots=7,padding_slots=0,actual_append_if_call_completes=7,history_after_first_call=8,next_NMS_len5_gate=False,limitation='Uninitialized-threshold risk only if later nonempty candidate path reaches enabled-NMS read without earlier initialization; no observed AttributeError.')],
 audit_scope=dict(model_calls=0,numerical_algorithm_calls=0,NPZ_array_decodes=0,NPZ_byte_reads=0,raw_RGB_reads=0,GT_reads=0,checkpoint_reads=0,new_algorithm_implementations=0,original_frozen_files_changed=False,canonical_ledger_changed=False),
 skills=[dict(path='/Users/rocket/.codex/skills/idea-evaluator/SKILL.md',use='Fatal-flaw gate and CRITICAL short-circuit; no high scores after source-refuted original premise'),dict(path='/Users/rocket/.claude/skills/sci-scientific-critical-thinking/SKILL.md',use='Construct validity, causal-path separation, and limits of source versus experimental evidence')],
 preparations=['One source nl command used the project cwd instead of VMem checkout and returned file-not-found; repeated only the needed source reads in the correct checkout. No model/data operation was attempted.'])
(OUT/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(status=receipt['status'],recorded_utc=receipt['recorded_utc'],doc_sha256=sha(ROOT/'docs/S19_FEEDBACK_PATH_AUDIT.md'),receipt_sha256=sha(OUT/'receipt.json')),ensure_ascii=False))
