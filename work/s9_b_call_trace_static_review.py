"""Read-only verification of saved synthetic records; never invokes the trace."""
import ast
import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PRE=ROOT/'results/S9_B_call_trace/pre_run.json'
REC=ROOT/'results/S9_B_call_trace/verification.json'
SCRIPT=ROOT/'scripts/audit_s9_b_call_trace.py'
pre=json.loads(PRE.read_text()); rec=json.loads(REC.read_text())
checks=0
def check(value, label):
    global checks
    assert value,label
    checks+=1
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def f32(x): return struct.unpack('<f',struct.pack('<f',x))[0]
check(pre['source_sha256']==rec['sources'],'pre/results source identity')
for p,h in rec['sources'].items(): check(sha(Path(p))==h,'source '+p)
check(rec['sources'][str(SCRIPT)]==sha(SCRIPT),'audit script identity')
check(pre['cases']==[{k:c[k] for k in ('initial_frames','motion','target_frames')} for c in rec['cases']],'all case identities')
pipeline=next(Path(p) for p in rec['sources'] if p.endswith('/modeling/pipeline.py'))
util=next(Path(p) for p in rec['sources'] if p.endswith('/utils/util.py'))
check(sha(pipeline)==sha(ROOT/'vendor/vmem_snapshot/modeling/pipeline.py'),'vendor/local official source identity')
ptree=ast.parse(pipeline.read_text()); utree=ast.parse(util.read_text())
def function(tree,name):
    nodes=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name]
    check(len(nodes)==1,'unique function '+name)
    return nodes[0]
gen=function(ptree,'_generate_frames_for_trajectory')
avg=function(utree,'average_camera_pose')
check(rec['original_function_lines']['generation_loop']=={'start':gen.lineno,'end':gen.end_lineno},'loop source lines')
check(rec['original_function_lines']['average_camera_pose']=={'start':avg.lineno,'end':avg.end_lineno},'average source lines')
context=function(ptree,'get_context_info')
calls=[n for n in ast.walk(context) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='average_camera_pose']
check(len(calls)==1 and calls[0].lineno==rec['original_function_lines']['average_call_line'],'active average expression')
check(ast.unparse(calls[0].args[0])=='target_c2ws[-self.config.model.context_num_frames // 4:]','exact slice precedence')
stree=ast.parse(SCRIPT.read_text())
lift=function(stree,'lift')
check('ast.Module(body=[node], type_ignores=[])' in ast.unparse(lift),'lift compiles original node')
check(not any(isinstance(n,ast.Attribute) and n.attr in ('NodeTransformer','fix_missing_locations') for n in ast.walk(lift)),'no transformer in lift')
for c in rec['cases']:
    initial=c['initial_frames']; moving=c['motion']=='translation'
    # Independent declarative expected partitions from the read original source;
    # no import or invocation of the audited script, original loop, Torch or SciPy.
    slots=([list(range(1,8)),list(range(8,12)),[12,13,13,13]] if initial==1 else
           [list(range(1,5)),list(range(5,9)),list(range(9,13))])
    before=[1,8,12] if initial==1 else [9,13,17]
    after=[8,12,14] if initial==1 else [13,17,21]
    check(len(c['events'])==6,'six events')
    check([e['event'] for e in c['events']]==['context','reconstruction_stub']*3,'event ordering')
    for i,(cx,re) in enumerate(zip(c['events'][::2],c['events'][1::2])):
        check(cx['history_count']==before[i] and re['history_count']==after[i],'history progression')
        xs=[f32(f32(j)*f32(.025)) if moving else 0. for j in slots[i]]
        check(cx['target_x']==xs,'float32 constructed target inputs')
        needed=not(initial==1 and i==0)
        check(cx['retrieval_needed']==needed,'initial bypass declaration')
        check(cx['average_input_count']==int(needed),'single-pose average or bypass')
        if needed:
            q=[[1.,0.,0.,xs[-1]],[0.,1.,0.,0.],[0.,0.,1.,0.],[0.,0.,0.,1.]]
            check(cx['query_pose']==q,'saved pre-axis-transform average pose')
        else: check(cx['query_pose'] is None,'first bypass has no query')
    check(c['adjacent_equal_query_pose']==[not moving]*(1 if initial==1 else 2),'constructed equal flags')
    check(c['not_checked']==['actual map changes','renderer intrinsics','source memberships','cache eligibility','latency'],'unmeasured fields declared')

now=datetime.now(timezone.utc).isoformat()
objects=[SCRIPT,PRE,REC,pipeline,util]+[Path(p) for p in rec['sources'] if p.endswith('/inference.yaml')]
report={
 'status':'PASS_WITH_REPORT_SCOPE_CLARIFICATION', 'review_completed_utc':now,
 'review_first_observed_clock_utc':'2026-09-05T20:31:34+00:00',
 'scope':'Independent static AST/source and saved JSON verification only; no rerun of original functions, audited script, model, rendering or reconstruction.',
 'checks_passed':checks,
 'artifacts':[{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in objects],
 'functions':{'loop_lines':[gen.lineno,gen.end_lineno],'average_lines':[avg.lineno,avg.end_lineno],'average_call_line':calls[0].lineno},
 'expected_cases':[
  {'initial_frames':1,'target_frames':13,'motions':['translation','stationary'],'context_history':[1,8,12],'post_store_history':[8,12,14],'batch_target_lengths_with_padding':[7,4,4],'actual_appends':[7,4,2],'retrieval_declared':[False,True,True]},
  {'initial_frames':9,'target_frames':12,'motions':['translation','stationary'],'context_history':[9,13,17],'post_store_history':[13,17,21],'batch_target_lengths_with_padding':[4,4,4],'actual_appends':[4,4,4],'retrieval_declared':[True,True,True]}],
 'required_report_clarification':[
  'List all substituted operations: get_context_info, get_translation_scaling_factor, get_cond, do_sample, tensor_to_pil, encode_image, construct_and_store_scene. The saved scope shorthand names only sampling/reconstruction. Preserve original records; disclose the full boundary in the applicability report.',
  'query_pose is the averaged pose before get_transformed_c2ws. No renderer K, geometry, source voting, candidate expansion, sorting or NMS ran. retrieval_needed is a fixture branch label, not observed renderer execution.',
  'Stationary equal poses are imposed by input construction; moving inequalities are properties of these fixtures. Neither measures real navigation frequency, cache eligibility/hit rate nor acceleration. Run wall-clock metadata is not real VMem latency.'
 ],
 'static_findings':[
  {'lines':'950–955','fact':'get_transformed_c2ws deep-copies and flips columns 1/2; a fixed axis-convention transform, independent of map contents. Same raw average pose has same transformed pose.'},
  {'lines':'635–645, 995','fact':'Default context_num_frames=4 makes the exact slice select only the last padded target pose. target_K is the mean of accumulating surfel_Ks and render receives mean×0.65; identical camera pose alone does not freeze intrinsics.'},
  {'lines':'820–827','fact':'The active merge path appends a new source timestep on a matching existing surfel; unmatched surfels are returned. It does not assign an old surfel position, normal or radius.'},
  {'lines':'1026–1056, 1082','fact':'Construction converts initial/all or last target_num_frames point maps into surfels, merges memberships, assigns sources to unmatched births and extends the global surfel list. Ordinary writes need not preserve group/source/candidate identities even if an old position is unchanged.'},
  {'lines':'1337–1401','fact':'The separate undo branch removes frames, source memberships and surfels, then reindexes survivors. Not executed in this synthetic trace; another explicit invalidation case for any later cache.'},
  {'lines':'1195–1316','fact':'Every nonempty generation batch calls context once, appends generated frame state, then calls reconstruction once. This is the original AST body; its external operations were stubbed.'}
 ],
 'limitations':['Config assertions support the pinned default 4/4/8 only, not arbitrary configs.', 'The fixtures do not validate get_context_info results or real reconstruction state mutations.', 'Old positions are unchanged in the inspected merge/write path; do not call this an experiment testing coordinate-update caching.']
}
(ROOT/'docs/S9_B_CALL_TRACE_REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
md=['# S9 B 调用轨迹独立只读核对','',f'完成时间：{now}。状态：**PASS，须在适用性报告补齐桩替换范围**。完成 {checks} 项静态/保存记录检查；没有重跑原函数、轨迹脚本、模型、渲染或重建。','',
 '## 核查结论','',
 '原脚本将唯一匹配的 FunctionDef 节点直接编译，未变更生成循环 AST。原生成函数 1195–1316 行及平均函数 601–637 行、635 行的完整切片表达式均与记录一致；pre_run、verification 和当前四份来源 SHA 全匹配，工作副本 pipeline 与固定 vendor 快照相同。','',
 '| 人工输入 | context 调用前历史数 | 重建桩调用时历史数 | 填充后目标帧数 | 实际追加帧数 |','|---|---|---|---|---|',
 '| 初始 1 帧，目标 13；平移/静止各一例 | 1, 8, 12 | 8, 12, 14 | 7, 4, 4 | 7, 4, 2 |',
 '| 初始 9 帧，目标 12；平移/静止各一例 | 9, 13, 17 | 13, 17, 21 | 4, 4, 4 | 4, 4, 4 |','',
 '四例均每批 context→追加帧→重建桩，共 12 次 context/12 次重建桩；初始单帧的两例首批绕过检索，留下 10 个“需要检索”的桩标签。默认切片仅取末位姿；逐项核全部 float32 人工坐标、保存均值矩阵和相邻相等标志。平移 3 个相邻比较全不同，静止 3 个全相同，这些是构造输入的结果。','',
 '## 适用性报告必须明确的范围','']
md += [f'{i}. {s}' for i,s in enumerate(report['required_report_clarification'],1)]
md += ['', '## 固定查询/固定组假设的源码核对','', '| 固定来源行号 | 结论 |','|---|---|']
md += [f'| {x["lines"]} | {x["fact"]} |' for x in report['static_findings']]
md += ['', '原点没有在该合并路径中移动，不等于记忆不变；来源追加、新点、内参均值和导航相机变化足以破坏第一版证书条件。S7/S8 对同一查询的多次离线干预不是官方正常导航的重复消费证据。','', '## SHA 绑定','']
md += [f'- `{x["path"]}`：`{x["sha256"]}`' for x in report['artifacts']]
md += ['', '以上要求只需在新适用性报告说明，不应回写修改已保存的 pre_run/verification。未发现需重跑本次人工调用轨迹的数值或抽取错误。','']
(ROOT/'docs/S9_B_CALL_TRACE_REVIEW.md').write_text('\n'.join(md))
print(json.dumps({'status':report['status'],'checks':checks,'completed_utc':now,'md_sha256':sha(ROOT/'docs/S9_B_CALL_TRACE_REVIEW.md'),'json_sha256':sha(ROOT/'docs/S9_B_CALL_TRACE_REVIEW.json')},indent=2))
