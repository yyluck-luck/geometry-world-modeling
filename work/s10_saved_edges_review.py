"""Independently audit saved synthetic arrays and restore candidate AST."""
import ast
import hashlib
import json
import textwrap
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np
from src.s10_vectorized_renderer import renderer_function

OUT=ROOT/'results/S10_renderer_edges_candidate_review'
OUT.mkdir(exist_ok=False)
began=datetime.now(timezone.utc).isoformat()
count=0
def check(x,label):
    global count
    assert x,label
    count+=1
def digest(p):
    b=p.read_bytes();return {'path':str(p.relative_to(ROOT)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
freeze=ROOT/'docs/S10_RENDERER_DESIGN_FREEZE.json'
f=json.loads(freeze.read_text());files=[digest(freeze)]
check(sha:=digest(freeze)['sha256']=='2a954d70c0a6ae91c495fcaa422d69f40aab2f5c4b07e4ae2f3f7182a1f784b6','freeze hash')
for p,h in f['source_sha256'].items():
    check(digest(ROOT/p)['sha256']==h,'frozen '+p);files.append(digest(ROOT/p))
base=ROOT/'results/S10_renderer_edges_candidate'
report=json.loads((base/'verification.json').read_text());pre=json.loads((base/'pre_run.json').read_text())
files.extend([digest(base/'verification.json'),digest(base/'pre_run.json')])
check(report['status']=='passed_candidate_exact_edges','candidate completed')
check(report['fixtures']==pre['fixtures'],'frozen artificial inputs')
check(len(report['cases'])==60 and len(report['fixtures'])==60,'all planned fixtures')
check([c['name'] for c in report['cases']]==[s['name'] for s in pre['fixtures']],'fixture identity/order')
check(len({c['name'] for c in report['cases']})==60,'unique fixture names')
fields=['depth','surfel_index_map','cos_value_map'];dtypes=['float32','int32','float32']
pair_rows=[]
for case in report['cases']:
    name=case['name'];rp=base/(name+'_reference.npz');cp=base/(name+'_candidate.npz')
    files.extend([digest(rp),digest(cp)])
    with np.load(rp,allow_pickle=False) as ref,np.load(cp,allow_pickle=False) as cand:
        check(ref.files==fields and cand.files==fields,name+' saved fields')
        for k,dtype in zip(fields,dtypes):
            a,b=ref[k],cand[k]
            check(str(a.dtype)==str(b.dtype)==dtype,name+k+' dtype')
            check(a.shape==b.shape==tuple(case['reference_arrays'][k]['shape']),name+k+' shape')
            check(a.tobytes()==b.tobytes(),name+k+' byte equality')
            check(hashlib.sha256(a.tobytes()).hexdigest()==case['reference_arrays'][k]['sha256'],name+k+' reference receipt')
            pair_rows.append({'fixture':name,'field':k,'elements':a.size,'bytes_equal':True,'sha256':hashlib.sha256(a.tobytes()).hexdigest()})
        check(int((ref['surfel_index_map']>=0).sum())==case['visible_pixels'],name+' visibility receipt')
    check(case['exact_arrays_equal'] and all(v==0 for v in case['differing_elements'].values()),name+' exact recorded flag')
check(len(report['negative_controls'])==5 and all(x['detected'] for x in report['negative_controls']),'five mutation controls')
check(len(report['polygon_scalar_probes'])==6,'six original polygon groups')

# Recreate only the transformation factory, not a renderer call; independently
# put the original pixel loop back into the emitted method and compare full AST.
fn=renderer_function();meta=fn.s10_transformation
old=ast.parse(textwrap.dedent(meta['original_method']))
new=ast.parse(meta['transformed_method'])
loops=[n for n in ast.walk(old) if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='py_']
check(len(loops)==1,'one original outer pixel loop')
replacements=[]
class Restore(ast.NodeTransformer):
    def visit_Expr(self,node):
        if isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='_s10_raster_patch':
            replacements.append(node);return loops[0]
        return self.generic_visit(node)
restored=Restore().visit(new)
check(len(replacements)==1,'one helper invocation')
check(ast.dump(restored,include_attributes=False)==ast.dump(old,include_attributes=False),'full AST restored identical')
for r in files:check(digest(ROOT/r['path'])==r,'saved file unchanged '+r['path'])
result={'status':'PASS','started_utc':began,'completed_utc':datetime.now(timezone.utc).isoformat(),'checks_passed':count,
 'scope':'Independent reread of saved synthetic NPZ arrays plus transformation-factory AST inspection; no rerun of renderer, real map, selector, model or timing.',
 'candidate_gate_started_utc':report['started_utc'],'candidate_gate_completed_utc':report['completed_utc'],
 'fixtures':60,'reference_npz':60,'candidate_npz':60,'exact_array_pairs':180,
 'nonempty_reference_fixtures':sum(c['visible_pixels']>0 for c in report['cases']),
 'negative_controls_detected':report['negative_controls'],'original_polygon_probe_groups':6,
 'all_other_original_ast_statements_unchanged':True,'input_files':files,'array_pairs':pair_rows,
 'limits':['Finite fixtures are not an all-input proof.','Six extra polygon probes inspect the original scalar helper; candidate parity is checked by the60 full-render fixtures.','Warning behavior is outside the equality contract; observed warnings were zero for both implementations in these60 cases.','No real-map or performance result is established.']}
(OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
(ROOT/'docs/S10_RENDERER_EDGE_AUDIT.json').write_text(json.dumps({'saved_review':digest(OUT/'verification.json'),**{k:v for k,v in result.items() if k not in ('input_files','array_pairs')}},indent=2)+'\n')
md=['# S10 独立人工边界门与保存数组审查','',
 '**PASS。** 冻结后的候选通过全部60个人工完整渲染用例，三数组逐字节相同；5种已知错误实现均被测试拒绝。随后只读重开120份NPZ，核180对数组的shape/dtype/bytes与回执，且独立恢复候选输出AST后与原方法完全相同。','',
 f'候选实际执行：{report["started_utc"]} 至 {report["completed_utc"]}。独立保存数组复核：{began} 至 {result["completed_utc"]}，{count}项检查通过。时点用于记录先后，不是速度或科研工时。','',
 '## 先后与固定来源','',
 '独立设计先于读取/运行候选；baseline_v2已通过后，根任务于UTC21:08:55.878852冻结候选、基准、测试脚本、设计及回执。候选开跑前先核freeze自身及全部6项SHA；完成后再次核对不变。首轮baseline只含4个负对照；补上同一diamond用例对删除epsilon的反证后另存v2，旧结果保留。','',
 '- 候选SHA：`3e079d0bbbaed962b24bce599a5cf7198b6bbc2891ac3c91761f4ea5c4f0e521`。',
 '- 基准SHA：`35825a3989f368906cba08808616f0c6922ff08d0a92c7205fddb4822652e2b3`。',
 '- 测试SHA：`cfe755492a3639ff74ee5ce43165d2f1630097a9b99e0c179735c50b2ccc99d7`。','',
 '## 检查确实能发现什么','',
 '60例包括36个人工边界和24份固定种子小混合输入，其中42例有可见像素。覆盖逐surfel顺序、同深度、同一float32舍入区间与跨区间深度、polygon整数/半像素边界、1e-15 epsilon、退化圆盘/法向、背面、near/far及margin不等号、部分顶点非正深度、float32几何、Torch参数与非方图像。','',
 '强制float64深度比较、非严格<=深度、像素中心+.5、删除1e-15 epsilon、包含near边界的五种内存错误变体，各被指定用例拒绝。原局部polygon另有6组探针；这6组本身不宣称是候选helper直接测试，候选通过完整renderer比较。','',
 '固定NumPy2.3.5的真实弱标量探针表明：原Python float与float32格比较，以及与float32数组比较，采用同一舍入行为。强行将深度或缓存提升为float64可能改变覆盖ID，不能当成“更精确所以等价”。四份NumPy官方原文及实际探针归档在S10_NUMPY_PROMOTION_REVIEW。','',
 '## 范围','',
 '本轮没有读取真实地图/RGB/depth/GT，没有模型、选择器或性能测量。逐字节结果只针对固定环境与有限人工输入；不是全域证明、跨NumPy版本保证或新方法创新。普通向量化仍是工程对照。','',
 '本轮告警文本/次数不在等价合同内，但60例两边观测告警均为0。原缓冲dtype、像素整数位置、polygon epsilon和严格比较不改；仅外层逐surfel内部的像素循环换为网格处理。','',
 '归档：`results/S10_renderer_edges_candidate/`含实际输入、原/候选120份NPZ与运行回执；`results/S10_renderer_edges_candidate_review/verification.json`含独立复核全部文件SHA和180对数组；`docs/S10_RENDERER_EDGE_AUDIT_DESIGN.md`保留测试设计。','']
(ROOT/'docs/S10_RENDERER_EDGE_AUDIT.md').write_text('\n'.join(md))
print(json.dumps({k:result[k] for k in ['status','checks_passed','fixtures','exact_array_pairs','all_other_original_ast_statements_unchanged','completed_utc']},indent=2))
