#!/usr/bin/env python3
"""Check complete report transcriptions; never reconstruct geometry or correlation."""
from pathlib import Path
import json,csv,hashlib,datetime
R=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling'); O=R/'work/S14C_completion_review'
def load(p):return json.loads((R/p).read_text())
def sha(p):return hashlib.sha256((R/p).read_bytes()).hexdigest()
checks=[]
def check(ok,name):
 checks.append(name)
 if not ok:raise AssertionError(name)
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
j=load('results/S14C_exploratory_association/joined_rows.json');a=load('results/S14C_exploratory_association/associations.json')['rows'];v=load('results/S14C_independent_verification/verification.json');m=load('docs/S14C_EXECUTION_MANIFEST.json');machine=load('work/S14C_completion_review/machine_receipt.json')
inputs=['docs/S14C_RESULTS.md','work/S14C_reporting/all_24_queries.csv','work/S14C_reporting/all_32_correlations.csv','work/S14C_reporting/repeats_and_coverage.json','work/S14C_reporting/receipt.json','results/S12_matched_budget_independent_audit/audited_result_sha256.json']
before={p:sha(p) for p in inputs}
def csvcheck(p,cols,expected):
 with (R/p).open() as f:
  r=csv.DictReader(f);check(r.fieldnames==cols,p+'/columns');rows=list(r)
 check(len(rows)==len(expected),p+'/row_count')
 for i,(x,y) in enumerate(zip(rows,expected)):
  for c in cols:
   if type(y[c]) is float:check(float(x[c])==y[c],f'{p}/{i}/{c}')
   else:check(x[c]==('' if y[c] is None else str(y[c])),f'{p}/{i}/{c}')
csvcheck(inputs[1],j['columns'],j['rows'])
csvcheck(inputs[2],['stage','block','metric','n_total','n_usable','n_missing','rho','reason'],a)
repeat=load(inputs[3]);check(len(repeat)==6,'six complete repeat groups')
mapping={'rows':'query_count','selection_groups':'selected_pair_distinct','selection_duplicate_extra_rows':'selected_repeated_rows','selection_equal_query_pairs':'selected_equal_query_pairs','x_values':'x_distinct','x_duplicate_extra_rows':'x_repeated_rows','x_equal_query_pairs':'x_equal_query_pairs','y_values':'y_distinct'}
for x,y in zip(repeat,machine['block_duplicate_counts']):
 check((x['stage'],x['block'])==(y['stage'],y['block']),'repeat identity')
 for src,dest in mapping.items():check(x[dest]==y[src],'repeat/'+src)
 rr=[r for r in j['rows'] if r['stage']==x['stage'] and r['block']==x['block']]
 check(x['common_min']==min(r['common_points'] for r in rr),'repeat common min')
 check(x['common_max']==max(r['common_points'] for r in rr),'repeat common max')
text=(R/inputs[0]).read_text();rho_rows=[];repeat_rows=[]
for line in text.splitlines():
 if line.startswith('| S7 /') or line.startswith('| S8 /'):
  cells=[x.strip() for x in line.strip('|').split('|')]
  if len(cells)==6:rho_rows.append(cells)
  if len(cells)==5:repeat_rows.append(cells)
check(len(rho_rows)==8,'all eight Markdown correlation groups')
lookup={(x['stage'],x['block'],x['metric']):x for x in a}
metrics=['disagreement_g_minus_p','source_count_p_minus_g','camera_pair_p_minus_g','query_distance_g_minus_p']
for cells in rho_rows:
 s,block=map(str.strip,cells[0].split('/'));block=None if block=='全场景' else int(block)
 for met,cell in zip(metrics,cells[1:5]):
  val=lookup[s,block,met]['rho']
  check(cell==('不可算' if val is None else f'{val:.4f}'),'Markdown rho/'+str((s,block,met)))
 check(int(cells[5])==(12 if block is None else 4),'Markdown group n')
check(len(repeat_rows)==6,'six Markdown repeated groups')
for cells,x in zip(repeat_rows,repeat):
 check(cells[0]==f"{x['stage']} / {x['block']}",'Markdown repeat identity')
 for cell,k in zip(cells[1:4],['selected_pair_distinct','x_distinct','y_distinct']):check(int(cell)==x[k],'Markdown repeat/'+k)
 check(cells[4]==f"{x['common_min']}–{x['common_max']}",'Markdown common range')
rr=[r for r in j['rows'] if r['stage']=='S8' and r['block']==1]
check(f"{rr[0]['disagreement_g_minus_p']:.10f}".replace('-','−') in text,'posthoc x')
for r in rr:
 val=r['y_pose_minus_geometry_pp'];printed=f'{val:+.6f}' if val>0 else f'{val:.6f}'
 check(printed.replace('-','−') in text,'posthoc y')
for s in ['S7','S8']:
 val=lookup[s,None,'disagreement_g_minus_p']['rho']
 check(('REFUTED_BY_S7' if lookup['S7',None,'disagreement_g_minus_p']['rho']<=0 else 'NOT_REFUTED')=='REFUTED_BY_S7','limited pre-specified direction is refuted')
for word in ['64,656','10,743','60,435','288','269–577','8.2062%–26.9859%','803,179','82,684','7.1054273576010019e-15','2.22e−16','13条','25对','14条','27对',m['frozen_utc'],sha('docs/S14C_EXECUTION_MANIFEST.json')]:
 check(word in text,'reported factual value/'+word)
for mdp in ['results/S14C_selection_disagreement/run_metadata.json','results/S14C_exploratory_association/run_metadata.json','results/S14C_independent_verification/verification.json']:
 x=load(mdp)
 for k in ['started_utc','completed_utc']:check(x[k] in text,'actual time/'+k)
check(load(inputs[5])['records.json']==m['score_input']['sha256'],'S12 original audit binds current score hash')
for phrase in ['不是在证明所有几何一致性方法无效','普通代理量','没有考虑当前目标像素的可见性或遮挡','不是学习算法胜负比较','不扩大裁定到原C2','解释发生在结果之后','没有计算p值','没有拟合/翻转符号','位置与朝向','人工CLI漏传--root']:
 check(phrase in text,'scientific scope/'+phrase)
receipt=load(inputs[4]);check(receipt['report_sha256']==before[inputs[0]],'report SHA receipt')
for p,h in receipt['source_sha256'].items():check(sha(p)==h,'report input SHA/'+p)
check(receipt['query_rows']==24 and receipt['correlation_rows']==32,'report full row counts')
check(receipt['repeat_summary']==repeat,'report duplicate summary')
for p,h in before.items():check(sha(p)==h,'review input stable/'+p)
out={'schema':'s14c-report-transcription-review-v1','status':'PASS','started_utc':started,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'check_count':len(checks),'input_sha256':before,'checks':checks,'scope':'All saved24-row/32-rho CSV fields, eight Markdown groups, six repeat groups, factual prose, scientific scope, source identities; no geometry or rank recomputation.'}
with (O/'transcription_receipt.json').open('x') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({k:out[k] for k in ['status','completed_utc','check_count']}))

