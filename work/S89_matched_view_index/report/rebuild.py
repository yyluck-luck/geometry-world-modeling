from pathlib import Path
import datetime,hashlib,json,subprocess,sys,time
D=Path(__file__).resolve().parent; R=D.parents[2]
base='S88_S89_从重影到可信几何参照'
S86=R/'work/S86_fixed_warp_consumer'; S87=R/'work/S87_terminal_strength_audit'; S88=R/'work/S88_independent_geometry_data'; S89=D.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=[R/'AGENTS.md',R/'RESEARCH_PRINCIPLES.md',S86/'ROOT_RESULT_ACCEPTANCE.json',S86/'scoring_01/ARM_SUMMARY.json',S87/'S87_RESULTS.md',S87/'scoring_01/ARM_SUMMARY.json',S87/'ROOT_VISUAL_ACCEPTANCE.json',S87/'ROOT_RESULT_ACCEPTANCE.json',S87/'result_report/images/target_22_comparison.png',D/'images/target_22_comparison.png',S88/'S88_RESULTS.md',S88/'ROOT_METADATA_ACCEPTANCE.json',S88/'NEXT_MATCHED_VIEW_INDEX_PLAN.md',S88/'DATA_GATE_DRAFT.md',S88/'INNOVATION_COMPETING_EXPLANATIONS.md',S88/'RTMV_EXPORT_SEMANTICS.md',S88/'CAMERA_METADATA_CHECK.json',S88/'review/RANGE_ACTUAL_REVIEW.json',S89/'index_01/RECEIPT.json',S89/'index_02/RECEIPT.json',S89/'index_02/MATCHED_VIEWS.json',S89/'review/INDEX_SOURCE_REVIEW.json',S89/'review/OPENSSL_SOURCE_REVIEW.json',S89/'review/INDEX_ACTUAL_REVIEW.json',S89/'review/INDEX_OPENSSL_ACTUAL_REVIEW.json']
a=json.loads((S86/'scoring_01/ARM_SUMMARY.json').read_text());b=json.loads((S87/'scoring_01/ARM_SUMMARY.json').read_text())
expected86=[('G0',.13116666776908745),('Gpaste',.09096801252375357),('Gterminal',.09819160239669339),('Gguide',.05242222252907684)]
expected87=[('Gpaste_l050',.06503335766940749),('Gterminal_l050',.0675577687885135),('Gpaste_l075',.05336066672505866),('Gterminal_l075',.05116758166201706),('Gpaste_l100',.05605979087391255),('Gterminal_l100',.05253204588523472)]
for src,expected in [(a,expected86),(b,expected87)]:
 for name,value in expected:
  assert src[name]['full']['equal_frame_mean_mse']==value
  assert src[name]['full']['total_channels']==3981312
accept=json.loads((S88/'ROOT_METADATA_ACCEPTANCE.json').read_text());assert accept['accepted'] and accept['actual_body_bytes']==193483 and accept['independent_checks']==106
for batch in ['index_01','index_02']:
 r89=json.loads((S89/batch/'RECEIPT.json').read_text())
 assert r89['status']=='STOPPED' and len(r89['requests'])==1 and r89['downloaded_body_bytes']==0
 assert r89['new_members']==[] and len(r89['previous_members'])==7 and r89['complete_view_ids']==[] and r89['selected_development_view'] is None
 assert r89['image_or_depth_payloads_requested']==0 and r89['json_payloads_requested']==0 and r89['new_model_runs']==0
assert len(json.loads((S89/'index_02/MATCHED_VIEWS.json').read_text())['all_views'])==6
inp={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scientific_cutoff_utc':'2026-09-11T01:32:50Z','status':'S89_TWO_ACTUAL_TRANSPORT_FAILURES_RECORD_REVIEWS_PASS','evidence':[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in paths],'skills':['/Users/rocket/.codex/plugins/cache/openai-primary-runtime/pdf/26.909.12148/skills/pdf/SKILL.md','/Users/rocket/.claude/skills/sci-scientific-critical-thinking/SKILL.md'],'skill_use':'Local PDF compile/render/visual QA; scientific construct and evidence boundaries. Native TikZ teaching schematic, no image generation/model call.','artifact_marker':'Successfully executed once immediately before first authoring command, expected-output-count 1, operation create, output-format pdf; exit 0, no stdout.','numeric_readback':'10 means and full denominators matched original score summaries; S88 acceptance values and both S89 failure receipts/partial manifest checked; no score recomputation'}
(D/'SOURCE_BUILD_INPUTS.json').write_text(json.dumps(inp,ensure_ascii=False,indent=2)+'\n')
build=D/'build';build.mkdir(exist_ok=True);runs=sorted(build.glob('run_*'));run=build/f'run_{len(runs)+1:02d}';run.mkdir()
import shutil
shutil.copy2(D/(base+'.tex'),run/'source.tex');shutil.copy2(D/'SOURCE_BUILD_INPUTS.json',run/'SOURCE_BUILD_INPUTS.json')
rec={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha256':sha(D/(base+'.tex')),'commands':[],'status':'RUNNING'};t=time.perf_counter()
try:
 for k in [1,2]:
  cmd=['/opt/homebrew/bin/xelatex','-interaction=nonstopmode','-halt-on-error',f'-output-directory={run}',base+'.tex']
  p=subprocess.run(cmd,cwd=D,capture_output=True,text=True);(run/f'compile_{k}.stdout').write_text(p.stdout);(run/f'compile_{k}.stderr').write_text(p.stderr);rec['commands'].append({'argv':cmd,'returncode':p.returncode})
  if p.returncode:raise RuntimeError('LaTeX failed; preserved logs')
 from pypdf import PdfReader
 pdf=run/(base+'.pdf');reader=PdfReader(pdf);rec['pages']=len(reader.pages)
 log=(run/(base+'.log')).read_text(errors='replace');rec['layout_warnings']=[x for x in log.splitlines() if any(q in x for q in ['Overfull','Missing character','undefined references'])]
 (run/'page_texts.json').write_text(json.dumps([p.extract_text() for p in reader.pages],ensure_ascii=False,indent=2)+'\n')
 cmd=['/opt/homebrew/bin/pdftoppm','-scale-to','1500','-png',str(pdf),str(run/'page')];p=subprocess.run(cmd,capture_output=True,text=True);rec['commands'].append({'argv':cmd,'returncode':p.returncode});(run/'render.stderr').write_text(p.stderr)
 if p.returncode:raise RuntimeError('render failed')
 rec['status']='COMPILED_RENDERED_AWAITING_ACTUAL_VISUAL_REVIEW';rec['pdf_sha256']=sha(pdf);rec['rendered_pages']=[{'path':str(x),'sha256':sha(x)} for x in sorted(run.glob('page-*.png'))]
except Exception as e:rec['status']='FAILED';rec['error']=repr(e);raise
finally:
 rec['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();rec['elapsed_seconds']=time.perf_counter()-t;(run/'BUILD_RECEIPT.json').write_text(json.dumps(rec,ensure_ascii=False,indent=2)+'\n');print(json.dumps(rec,ensure_ascii=False,indent=2))
