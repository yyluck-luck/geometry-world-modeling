"""Exact transcription/report checks against completed outputs; no NPZ reads."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import json
import re

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
checks=[]
def check(name,value):
    if not value: raise AssertionError(name)
    checks.append(name)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(name): return json.loads((ROOT/name).read_text())

summary=read('results/S14B_observation_disagreement/summary.json')
meta=read('results/S14B_observation_disagreement/metadata.json')
ver=read('results/S14B_independent_verification/verification.json')
manifest=read('docs/S14B_EXECUTION_MANIFEST.json')
report=(ROOT/'docs/S14B_RESULTS.md').read_text()
reporting=read('work/S14B_reporting/receipt.json')
for p,digest in reporting['sources'].items(): check('report_source:'+p,sha(ROOT/p)==digest)
check('report_frozen_in_reporting_receipt',sha(ROOT/'docs/S14B_RESULTS.md')==reporting['report_sha256'])
check('strata_frozen_in_reporting_receipt',sha(ROOT/'work/S14B_reporting/all_m_strata.csv')==reporting['all_strata_sha256'])
metrics=['W','B','A','D','W_over_radius2','B_over_radius2','A_over_radius2','D_over_radius2']
columns=['phase','block','stride','m','n_points']+[m+'_'+s for m in metrics for s in ('mean','median','p90')]
expected=[]
for b in summary['blocks']:
    for g in b['by_m']:
        e={k:b[k] for k in ('phase','block','stride')}
        e.update({k:g[k] for k in ('m','n_points')})
        e.update({m+'_'+s:g['metrics'][m][s] for m in metrics for s in ('mean','median','p90')})
        expected.append(e)
with (ROOT/'work/S14B_reporting/all_m_strata.csv').open(newline='') as f:
    reader=csv.DictReader(f)
    check('strata_29_columns_exact',reader.fieldnames==columns)
    rows=list(reader)
check('116_rows_all_nonempty_m_strata',len(rows)==len(expected)==reporting['m_strata_rows']==116)
for i,(r,e) in enumerate(zip(rows,expected)):
    for k in columns:
        v=r[k] if k=='phase' else int(r[k]) if k in columns[1:5] else float(r[k])
        check(f'transcription:{i}:{k}',v==e[k])
table_lines=[line for line in report.splitlines() if re.match(r'^\| S[78] / [012] \|',line)]
check('six_report_table_rows',len(table_lines)==6)
for line,b in zip(table_lines,summary['blocks']):
    cells=[x.strip() for x in line.strip('|').split('|')]
    check('report_table_identity:'+cells[0],cells[0]==f"{b['phase']} / {b['block']}")
    for v,k in zip(cells[1:],('n_observations','n_points','single_source_points','multi_source_points')):
        check('report_table_count:'+cells[0]+':'+k,int(v.replace(',',''))==b[k])
totals=[sum(b[k] for b in summary['blocks']) for k in ('n_observations','n_points','single_source_points','multi_source_points')]
total_line=next(l for l in report.splitlines() if l.startswith('| 合计'))
check('report_table_total',[int(x.strip().replace(',','')) for x in total_line.strip('|').split('|')[1:]]==totals)
phrases=[manifest['frozen_utc'],sha(ROOT/'docs/S14B_EXECUTION_MANIFEST.json'),meta['started_utc'],meta['finished_utc'],ver['started_utc'],ver['ended_utc'],f"{meta['elapsed_seconds']:.6f}秒",f"{meta['peak_rss_bytes']:,}字节",'13:51:59–13:52:00','13:52:28–13:52:30',f"{meta['counters']['input_files_cached']}份固定输入",f"{meta['counters']['input_bytes_cached']:,}字节",f"{meta['counters']['npz_files_decoded']}份NPZ的{meta['counters']['numerical_arrays_decoded']}个必要数组",f"{meta['counters']['prediction_json_files_decoded']}份事件/来源JSON",f"{meta['counters']['frame_groups']:,}个点/帧组",f"{ver['exact_checks']:,}项精确检查",f"{ver['float_checks']:,}项浮点检查",'atol=1e-12、rtol=1e-10','25控制文件','全部116个非空m层','8种原值/归一化量']
for text in phrases: check('report_numeric_phrase:'+text,text in report)
difference=re.search(r'最大绝对差([0-9.e+-]+)',report)
check('report_max_difference_exact',difference is not None and float(difference.group(1))==ver['max_abs_difference'])
check('report_zero_reads_runs_match',meta['counters']['gt_scoring_query_feature_reads']==meta['counters']['model_runs']==0 and 'GT/评分/query/特征读取和模型运行均为0' in report)
constraints=['没有重新运行模型','没有训练或生成视频','人工测试只用于检查程序','不能当成预测准确','不是独立样景','不是实验样本数','不是模型推理、训练或视频耗时','不能写成米²或毫米²','尚不能推出分散就是错误','数学性质','两个已见场景','新颖性和算法有效性仍待验证']
# Check actual report wording, retaining the scientific review below separately.
constraints[4]='不是独立样本数'
for text in constraints: check('scope_phrase:'+text,text in report)
stdout=read('work/S14B_execution/measurement/stdout.txt')
check('production_stdout_matches_metadata',stdout['status']==meta['status'] and stdout['counters']==meta['counters'])
for stage in ('measurement','verification'):
    check(stage+'_stderr_empty',(ROOT/f'work/S14B_execution/{stage}/stderr.txt').read_bytes()==b'')
result={'schema':'s14b-completion-report-checks-v1','completed_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS','checks_count':len(checks),'checks':checks,'report_sha256':sha(ROOT/'docs/S14B_RESULTS.md'),'all_strata_sha256':sha(ROOT/'work/S14B_reporting/all_m_strata.csv'),'all_strata_rows':116,'strata_metadata_cells':116*5,'strata_numeric_cells':116*24,'scope':'Only completed result transcription and report consistency; no raw prediction array decoding or production/verifier rerun.'}
(OUT/'report_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('status','checks_count','report_sha256','all_strata_rows','strata_metadata_cells','strata_numeric_cells')},indent=2))
