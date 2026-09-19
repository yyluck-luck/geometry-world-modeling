"""Count saved S7/S8 candidate traces only; no selection or rendering execution."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import csv
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/S9_B_candidate_semantics'
OUT.mkdir(exist_ok=False)
began=datetime.now(timezone.utc).isoformat()
files=[]; rows=[]; visible=[]; checks=0
def check(x,label):
    global checks
    assert x,label
    checks+=1
def digest(p):
    b=p.read_bytes()
    return {'path':str(p.relative_to(ROOT)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
types=['official','candidate_no_nms','all20_nms','all20_no_nms']
maps=['A0P0','A0P1','A1P0','A1P1']
for stage,dirname in [('S7','S7_event_replay'),('S8','S8_event_replay_v2')]:
    base=ROOT/'results'/dirname
    rp=base/'records.json'; records=json.loads(rp.read_text());files.append(digest(rp))
    look={(r['block'],r['stride'],r['frame']):r for r in records}
    paths=sorted(base.glob('block*_stride*/prediction_only_selection.json'))
    check(len(paths)==6,stage+' six case files')
    for path in paths:
        files.append(digest(path)); d=json.loads(path.read_text())
        check(len(d['queries'])==4,'four queries/case')
        for q in d['queries']:
            check(sorted(q['maps'])==sorted(maps),'four maps')
            for mapid,m in q['maps'].items():
                key={'stage':stage,'block':d['block'],'split':d['split'],'stride':d['stride'],'frame':q['frame'],'map':mapid}
                trace=m['official_trace']; k=trace['visible_sources']
                weights=trace['weights']; counts=trace['candidate_counts']
                check(k==len(weights)==len(counts),'saved visible-source counts agree')
                check(len(set(x[0] for x in weights))==k,'unique weight source IDs')
                check([x[0] for x in counts]==[x[0] for x in weights],'count/weight source identities')
                check(all(c in (0,1) for _,c in counts),'active quota counts binary')
                counted=[fid for fid,c in counts for _ in range(c)]
                check(len(counted)==min(14,k),'quota length from saved counts')
                check(counted==trace['candidates'],'saved official expansion identity')
                visible.append({**key,'visible_sources':k,'nonzero_candidate_sources':len(counted),'quota_zero_entries':sum(c==0 for _,c in counts),'quota_one_entries':sum(c==1 for _,c in counts)})
                check(set(m['readouts'])==set(types),'four readouts')
                for kind,r in m['readouts'].items():
                    ids=r['expanded_candidates']; hist=Counter(ids)
                    duplicates=sum(v-1 for v in hist.values())
                    check(Counter(ids)==Counter(r['sorted_frames']),'saved sorting is permutation')
                    check(r['selected']==look[(d['block'],d['stride'],q['frame'])]['readouts'][mapid][kind]['selected'],'selected records agree')
                    if kind in ('official','candidate_no_nms'):
                        check(ids==counted,'geometry candidates agree with saved quota')
                    else:
                        check(ids==list(range(20)),'all20 bypass has twenty unique IDs')
                    dist=r['distances_float32']
                    check(len(dist)==len(ids),'saved distance length')
                    ties=sum(v-1 for v in Counter(dist).values())
                    check(ties==r['expanded_adjacent_pose_ties'],'saved tie count')
                    rows.append({**key,'readout':kind,'candidate_basis':'saved_geometry_quota' if kind in ('official','candidate_no_nms') else 'all20_bypass',
                       'visible_sources_in_shared_render':k,'visible_sources_used_by_readout':k if kind in ('official','candidate_no_nms') else '',
                       'expanded_count':len(ids),'unique_count':len(hist),'duplicate_extra_entries':duplicates,'repeated_ids':sum(v>1 for v in hist.values()),'maximum_multiplicity':max(hist.values()),'expanded_adjacent_pose_ties':ties})
    check(sum(r['stage']==stage for r in rows)==384,stage+' 384 readouts')
    check(sum(r['stage']==stage for r in visible)==96,stage+' 96 rendering/map-query rows')

def hist(rs,field): return {str(k):v for k,v in sorted(Counter(r[field] for r in rs).items())}
def aggregate(rs):
    return {'n':len(rs),'rows_with_duplicate_ids':sum(r['duplicate_extra_entries']>0 for r in rs),'duplicate_extra_entries_total':sum(r['duplicate_extra_entries'] for r in rs),
      'expanded_count_distribution':hist(rs,'expanded_count'),'unique_count_distribution':hist(rs,'unique_count'),
      'saved_pose_tie_count_distribution':hist(rs,'expanded_adjacent_pose_ties'),'saved_pose_tie_total':sum(r['expanded_adjacent_pose_ties'] for r in rs)}

groups=[]
for stage in ['S7','S8']:
    for kind in types:
        subsets=[('all',{}),('stride8',{'stride':8}),('stride12',{'stride':12})]
        subsets += [('block'+str(b),{'block':b}) for b in range(3)]
        subsets += [(f'block{b}_stride{s}',{'block':b,'stride':s}) for b in range(3) for s in [8,12]]
        subsets += [('split_'+sp,{'split':sp}) for sp in sorted({r['split'] for r in rows if r['stage']==stage})]
        for label,filters in subsets:
            rr=[r for r in rows if r['stage']==stage and r['readout']==kind and all(r[k]==v for k,v in filters.items())]
            groups.append({'stage':stage,'readout':kind,'subset':label,'filters':filters,**aggregate(rr)})
sourcegroups=[]
for stage in ['S7','S8']:
    for label,filters in [('all',{}),('stride8',{'stride':8}),('stride12',{'stride':12})]+[(f'block{b}_stride{s}',{'block':b,'stride':s}) for b in range(3) for s in [8,12]]:
        vv=[r for r in visible if r['stage']==stage and all(r[k]==v for k,v in filters.items())]
        sourcegroups.append({'stage':stage,'subset':label,'n_map_queries':len(vv),'visible_source_distribution':hist(vv,'visible_sources'),'quota_candidate_distribution':hist(vv,'nonzero_candidate_sources'),'quota_zero_entries_total':sum(r['quota_zero_entries'] for r in vv),'quota_one_entries_total':sum(r['quota_one_entries'] for r in vv)})

for name,data in [('all_768_saved_candidate_readouts.csv',rows),('all_192_saved_source_counts.csv',visible)]:
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
for p in [ROOT/'vendor/vmem_snapshot/modeling/pipeline.py',ROOT/'src/s7_event_replay.py',Path(__file__)]+[ROOT/'docs'/n for n in ['S7_RESULTS.md','S7_INDEPENDENT_AUDIT.md','S7_PRE_RUN_REVIEW.md','S8_AUDIT_PREPARATION.md','S8_INDEPENDENT_AUDIT.md']]:files.append(digest(p))
for f in files:check(digest(ROOT/f['path'])==f,'input unchanged '+f['path'])
done=datetime.now(timezone.utc).isoformat()
summary={'status':'PASS_SAVED_TRACE_AUDIT_ONLY','started_utc':began,'completed_utc':done,'checks_passed':checks,
 'scope':'Counts from all twelve saved prediction_only_selection JSONs and their saved official traces; no selector, renderer, PNG, GT, model, or score recomputation. Saved selected IDs cross-checked to existing records.json.',
 'unit':'Each stage has 96 map-query renders and four readouts each=384 saved decisions. Each readout denominator is96; these are correlated conditions, not96 or384 independent scene samples.',
 'readout_aggregates':groups,'source_aggregates':sourcegroups,'input_files':files,
 'semantics':'Official n=min(context+10,k); default context4 gives n=min(14,k)<=k. The active distribution call yields only0/1 candidate counts. The helper/expansion syntax can express repetition for other inputs but none is implied for this path.',
 'all20_boundary':'all20_nms and all20_no_nms bypass geometry quota and use IDs0..19 once; both still select four frames. Report separately; never include their 192 rows in the96 official denominator.',
 'tie_boundary':'Candidate identity repetition and equal float32 distance are distinct. A saved tie between distinct IDs alone does not establish floating-point quantization as its cause.',
 'unchanged':'All historical source files and saved numbers remain unchanged; this is a later semantic correction, not a fresh experiment.'}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
(ROOT/'docs/S9_B_CANDIDATE_QUOTA_CORRECTION.json').write_text(json.dumps({'summary':str((OUT/'summary.json').relative_to(ROOT)),'summary_sha256':digest(OUT/'summary.json')['sha256'],**summary},ensure_ascii=False,indent=2)+'\n')
md=['# S9 附记：候选展开语义更正','',f'实际检查时间：{began} 至 {done}。状态：**PASS**，{checks} 项保存记录/完整性检查。只读 S7/S8 全部12份保存选择 JSON、其中的192份地图查询来源/配额记录和768条读出，不重跑选择、渲染、模型或测量。','',
 '更正：**代码中的展开结构能够表示重复，不等于当前原调用或既有 S7/S8 记录实际含有重复候选。** 原493行的分配入参由492行给出 n=min(context+10,k)，默认即 n=min(14,k)。所以只可能走“来源多于名额时选前 n 个各1次”或“名额等于来源数时全部各1次”；不能进入剩余额度产生大于1次数的分支。', '',
 '## 全部已保存读出的实际计数','', '| 阶段 | 读出 | 记录数 | 有重复ID的记录 | 多余重复条目总数 | 候选数分布 | 已保存距离并列数总和 |','|---|---|---:|---:|---:|---|---:|']
for g in groups:
    if g['subset']=='all':md.append(f'| {g["stage"]} | {g["readout"]} | {g["n"]} | {g["rows_with_duplicate_ids"]} | {g["duplicate_extra_entries_total"]} | {g["expanded_count_distribution"]} | {g["saved_pose_tie_total"]} |')
md += ['', '每阶段 official 的分母为96：3块×2密度×4查询×4地图。candidate_no_nms 另96，两个 all20 控制各96，不能把384统称为官方检索样本。all20控制绕过几何配额，使用20个不同历史ID，最后仍只选4张。所有条件相关，不增加独立场景样本数。','', '## 来源数与配额分布','', '| 阶段/范围 | 地图查询数 | 可见来源数分布 | 几何候选数分布 | 配额0条目总数 | 配额1条目总数 |','|---|---:|---|---|---:|---:|']
for g in sourcegroups:
    if g['subset'] in ('all','stride8','stride12'):md.append(f'| {g["stage"]}/{g["subset"]} | {g["n_map_queries"]} | {g["visible_source_distribution"]} | {g["quota_candidate_distribution"]} | {g["quota_zero_entries_total"]} | {g["quota_one_entries_total"]} |')
md += ['', '来源数取每个地图查询的 official_trace.visible_sources，并与 weights 和 candidate_counts 的唯一来源数交叉核；不是把all20控制的候选数当成几何可见来源数。来源统计只计192份共享地图查询一次，不按四读出重复四倍。完整block/stride/split分组在JSON，逐项在两个CSV。','',
 '## 对旧文的影响','',
 '旧 S7_RESULTS、S7_INDEPENDENT_AUDIT、S7_PRE_RUN_REVIEW，以及 S8_AUDIT_PREPARATION/S8_INDEPENDENT_AUDIT 中关于“保留重复候选”或“展开并列含同一ID副本”的措辞，应理解为实现没有自行预先去重的结构性描述，不能据此声称本轮曾观测到重复。若旧句读起来是在断言实际重复，应以本附记的全数记录核查为准。','',
 '保持原语义是正确复现原则，但本次已查到的活跃调用无重复；因此不能以“重复副本触发并列”解释 S7/S8 的结果。不同ID的相等距离也不能仅凭相等就归因于量化。原票权首项双加、几何候选截断和姿态排序/NMS仍是另外的真实依赖。','',
 '旧源码、旧JSON、旧指标及报告快照均未改，也没有重新挑选样本。本更正不改变已保存的最终ID、支持率、几何指标或既有结论；只修正对候选机制的叙述。','',
 '归档：`results/S9_B_candidate_semantics/summary.json`、`all_768_saved_candidate_readouts.csv`、`all_192_saved_source_counts.csv`。同名文档JSON绑定完整输入SHA与统计。','']
(ROOT/'docs/S9_B_CANDIDATE_QUOTA_CORRECTION.md').write_text('\n'.join(md))
print(json.dumps({'started_utc':began,'completed_utc':done,'checks':checks,'readouts':[g for g in groups if g['subset']=='all'],'sources':[g for g in sourcegroups if g['subset']=='all']},ensure_ascii=False,indent=2))
