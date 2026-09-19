"""Write this peer review after final source identity is checked; no renderer calls."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import ast,hashlib,json,re
root=Path(__file__).resolve().parents[2]
script=root/'scripts/run_s10_renderer_comparison.py'
protocol=root/'docs/S10_RENDERER_COMPARISON_PROTOCOL.md'
code=script.read_text();ptext=protocol.read_text()
assert '不把它冒称本门已强制验证' not in ptext, 'Contradictory pre-byte-gate paragraph remains'
assert "expected_buffer.tobytes(order='C')" in code
names=['src/vmem_retrieval_kernel.py','src/s10_vectorized_renderer.py','scripts/profile_s9_components.py','scripts/run_s10_renderer_comparison.py','docs/S10_RENDERER_COMPARISON_PROTOCOL.md','src/s6_memory_bridge.py','src/retrieval_diagnostic.py','docs/S10_RENDERER_DESIGN_FREEZE.json','docs/S10_RENDERER_EDGE_AUDIT_DESIGN.md','scripts/s10_renderer_edge_audit.py','work/s10_numpy_promotion_sources/REVIEW.md','work/s10_numpy_promotion_sources/review.json','work/S10_renderer_pre_run_review/pure_schedule_check.json']
sha={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in names}
assert sha['src/s10_vectorized_renderer.py']=='3e079d0bbbaed962b24bce599a5cf7198b6bbc2891ac3c91761f4ea5c4f0e521'
assert sha['scripts/run_s10_renderer_comparison.py']=='00dbae5db3c7a09dca78a428951db2074103b54d8f2c23a4daea17b7e6a96554'
selected=[]
for n in ast.parse(code).body:
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CONTRACT' for t in n.targets): selected.append(n)
    if isinstance(n,ast.FunctionDef) and n.name in ('pair_order','schedule'): selected.append(n)
ns={};exec(compile(ast.Module(body=selected,type_ignores=[]),'<S10 pure contract/schedule only>','exec'),ns)
rows=ns['schedule']();block=re.findall(r'```s10-comparison-json\s*\n(.*?)\n```',ptext,re.S)
checks={'protocol_contract_exact':len(block)==1 and json.loads(block[0])==ns['CONTRACT'],'pairs_168':len(rows)==168,'phase_pairs':Counter(r['phase'] for r in rows)=={'correctness':24,'warmup':24,'measured':120},'measured_AB60_BA60':Counter('AB' if r['methods'][0]=='original' else 'BA' for r in rows if r['phase']=='measured')=={'AB':60,'BA':60}}
queries={}
for r in rows:
    if r['phase']=='measured': queries.setdefault(r['query_index'],[]).append(r)
checks['24_queries_each_5_pairs']=len(queries)==24 and all(len(q)==5 for q in queries.values())
checks['per_query_three_two_orders']=all(sorted(Counter(x['methods'] for x in q).values())==[2,3] for q in queries.values())
checks['every_pair_one_each_method']=all(set(r['methods'])=={'original','candidate'} and len(r['methods'])==2 for r in rows)
checks['each_round_fixed_query_order']=all([r['query_index'] for r in rows if r['phase']==phase and r['round']==repeat]==list(range(24)) for phase,n in [('correctness',1),('warmup',1),('measured',5)] for repeat in range(n))
assert all(checks.values())
now=datetime.now(timezone.utc).isoformat()
receipt={'checked_utc':now,'scope':'Only isolated AST CONTRACT, pair_order and schedule executed; no runner imports, map data, NumPy, Torch, renderer or timings','source_sha256':sha['scripts/run_s10_renderer_comparison.py'],'protocol_sha256':sha['docs/S10_RENDERER_COMPARISON_PROTOCOL.md'],'checks':checks,'passed':True}
p=root/'work/S10_renderer_pre_run_review/pure_schedule_check_final.json';p.write_text(json.dumps(receipt,indent=2)+'\n');sha[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest()
for n in ['scripts/run_s10_renderer_comparison.py','docs/S10_RENDERER_COMPARISON_PROTOCOL.md']:
    p=root/'work/S10_renderer_pre_run_review'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((root/n).read_bytes())
text=(root/'work/S10_renderer_pre_run_review/review_body.md').read_text()
for key,value in {'REVIEW_TIME':now,'CANDIDATE_SHA':sha['src/s10_vectorized_renderer.py'],'RUNNER_SHA':sha['scripts/run_s10_renderer_comparison.py'],'PROTOCOL_SHA':sha['docs/S10_RENDERER_COMPARISON_PROTOCOL.md'],'ORIGINAL_SHA':sha['src/vmem_retrieval_kernel.py']}.items(): text=text.replace(key,value)
md=root/'docs/S10_RENDERER_PRE_RUN_REVIEW.md';md.write_text(text)
report={'schema':'s10-independent-pre-run-review-v1','status':'PASS','verdict_scope':'Static candidate semantics and fair comparison design only; no execution approval, actual renderer parity or speed result','reviewed_utc':now,'start_time_precision':'First source-review start was not separately recorded; no historical duration claimed','reviewer':'independent survey_evaluation agent','major_issues':[],'minor_issues':[],'closed_issues':[{'id':'array_equal_signed_zero','finding':'Inherited S9 array_equal does not distinguish signed zero','resolution':'Root added C-order bytes comparison after original shape/dtype/value equality and aligned final protocol'},{'id':'stale_identity_guard','finding':'Finalization detected intentional root source update from runner 23fb691d/protocol b7932810 after prior author final notice','resolution':'No stale PASS was written; new bytes gate/protocol reread; old pure scheduling receipt kept and final-version receipt separately created'}],'static_review_categories':['camera_and_culling_AST','disk_geometry_mean_depth','integer_pixel_polygon_order_epsilon','short_circuit_xor_repeated_rows','Python_float_FP32_depth_compare','sequential_zbuffer','no_cache_reference_reads','module_transformation_identity','paired_state_common_observer','correctness_all_call_byte_trace_regression','schedule_descriptive_estimators','freeze_source_input_integrity_soft_limits'],'executed_checks':{'pure_contract_schedule':8,'passed':8,'renderer_calls':0,'real_map_reads':0,'new_model_runs':0,'actual_speed_measurements':0},'pure_check_receipt':'work/S10_renderer_pre_run_review/pure_schedule_check_final.json','source_sha256':sha,'report_sha256':hashlib.sha256(md.read_bytes()).hexdigest(),'limitations':['No candidate factory/renderer invocation by this reviewer','No formal all-input equivalence proof','NumPy2.3.5 scoped; no cross-version parity claim','No real maps/PNG/depth/GT/model files loaded in this review','Independent edge runtime is separate evidence owned by other reviewer','Actual real-call parity and timing remain gated by root execution freeze','24 seen queries/two scenes/six maps including S7 development; repeats not independent','Placeholder context and shared observer; not full VMem/video/model latency','Python I/O and budgets are soft guards, not OS isolation'],'execution_freeze_created_by_this_reviewer':False,'research_ledger_modified':False}
out=root/'docs/S10_RENDERER_PRE_RUN_REVIEW.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
assert all(hashlib.sha256((root/p).read_bytes()).hexdigest()==v for p,v in sha.items())
print(json.dumps({'status':'PASS','completed_utc':now,'source_sha256':{n:sha[n] for n in ['src/s10_vectorized_renderer.py','scripts/run_s10_renderer_comparison.py','docs/S10_RENDERER_COMPARISON_PROTOCOL.md']},'md_sha256':report['report_sha256'],'json_sha256':hashlib.sha256(out.read_bytes()).hexdigest()},indent=2))
