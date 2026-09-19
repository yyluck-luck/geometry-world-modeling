"""Bounded saved-JSON/report verification; no experiment or numeric-library imports."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[2]
START = datetime.now(timezone.utc).isoformat()
IDENTITIES = {}
CHECKS = []

def read(rel):
    b = (ROOT / rel).read_bytes()
    IDENTITIES[rel] = hashlib.sha256(b).hexdigest()
    return b.decode()

def js(rel):
    return json.loads(read(rel))

def ck(name, actual, expected, category):
    CHECKS.append(dict(name=name, actual=actual, expected=expected,
                       passed=actual == expected, category=category))

report = read('docs/S11_RESULTS.md')
bs = js('results/S11_renderer_regression/summary.json')
ss = js('results/S11_source_regression/summary.json')
bm = js('results/S11_renderer_regression/run_metadata.json')
sm = js('results/S11_source_regression/run_metadata.json')
bf = js('docs/S11_RENDERER_REGRESSION_EXECUTION_FREEZE.json')
sf = js('docs/S11_SOURCE_REGRESSION_EXECUTION_FREEZE.json')
ba = js('docs/S11_RENDERER_REGRESSION_INDEPENDENT_AUDIT.json')
sa = js('docs/S11_SOURCE_REGRESSION_INDEPENDENT_AUDIT.json')
aa = js('docs/S11_RENDERER_REGRESSION_RESULT_AUDIT.json')
rows = js('results/S11_source_regression/conditions.json')
independent_rows = js('results/S11_source_regression_independent_audit_v2/independent_conditions.json')
independent_summary = js('results/S11_renderer_regression_audit/recomputed_summary.json')
ck('broad_saved_recomputed_summary', bs, independent_summary, 'saved_evidence')
ck('source_saved_independent_conditions', rows, independent_rows, 'saved_evidence')
for stem, audit in [('S11_RENDERER_REGRESSION_INDEPENDENT_AUDIT', ba),
                    ('S11_SOURCE_REGRESSION_INDEPENDENT_AUDIT', sa),
                    ('S11_RENDERER_REGRESSION_RESULT_AUDIT', aa)]:
    read('docs/' + stem + '.md')
    ck(stem + '/bound_markdown', IDENTITIES['docs/' + stem + '.md'], audit['report_sha256'], 'identity')

names = {'append_min_missing':'追加一个缺失来源', 'drop_last':'删除最后一个来源',
         'reverse':'反转来源顺序', 'only_0':'全部只保留来源0',
         'only_0_1_2':'全部只保留来源0/1/2'}
fields = ['conditions', 'exact_pass', 'stale_trace_rejected', 'selected_order_changed']
for key, label in names.items():
    line = next(line for line in report.splitlines() if line.startswith('| ' + label + ' |'))
    cells = [int(v.strip()) for v in line.strip('|').split('|')[1:]]
    selected_rows = [r for r in rows if r['variant'] == key]
    grouped = dict(conditions=len(selected_rows),
        exact_pass=sum(r['exact_render_and_full_trace'] for r in selected_rows),
        stale_trace_rejected=sum(r['stale_original_mapping_trace_rejected'] for r in selected_rows),
        selected_order_changed=sum(r['selected_order_changed_from_original'] for r in selected_rows))
    ck(key + '/saved_row_recount', grouped, ss['groups'][key], 'saved_row_recount')
    ck(key + '/audit_group', sa['groups'][key], ss['groups'][key], 'saved_evidence')
    for field, cell in zip(fields, cells, strict=True):
        ck(key + '/' + field, cell, grouped[field], 'table_cell')

tz = timezone(timedelta(hours=8))
def millis(value):
    dt = datetime.fromisoformat(value).astimezone(tz) + timedelta(microseconds=500)
    return dt.strftime('%H:%M:%S.') + f'{dt.microsecond // 1000:03d}'
for label, vals in [('已有地图执行冻结',[bf['frozen_utc']]),
                    ('已有地图新候选运行',[bm['started_utc'], bm['completed_utc']]),
                    ('来源控制执行冻结',[sf['frozen_utc']]),
                    ('来源控制运行',[sm['started_utc'], sm['completed_utc']])]:
    line = next(line for line in report.splitlines() if line.startswith('| ' + label + ' |'))
    printed = re.findall(r'\d\d:\d\d:\d\d\.\d{3}', line)
    for i, (actual, val) in enumerate(zip(printed, vals, strict=True)):
        ck(label + '/time' + str(i), actual, millis(val), 'table_time')

for key, value in [('execution_source_sha256',13),('input_sha256',316),('s10_evidence_sha256',682)]:
    ck('broad_freeze/' + key,len(bf[key]),value,'saved_evidence')
for key, value in [('execution_source_sha256',13),('input_sha256',52),('review_evidence_sha256',7)]:
    ck('source_freeze/' + key,len(sf[key]),value,'saved_evidence')
for label, meta, field in [('broad',bm,'wall_elapsed_for_budget_seconds'),('source',sm,'total_elapsed_seconds')]:
    printed = str(Decimal(str(meta[field])).quantize(Decimal('0.000001'),rounding=ROUND_HALF_UP))
    ck(label + '/budget_seconds_in_report',printed in report,True,'prose_numeric')
    ck(label + '/rss_in_report',str(meta['process_peak_rss_bytes']) in report,True,'prose_numeric')
    ck(label + '/run_completed',meta['status'],'completed','saved_evidence')
    ck(label + '/no_original_renderer',meta['original_renderer_calls'],0,'saved_evidence')

for field, value in [('full_conditions',192),('new_candidate_invocations',168),
                     ('inherited_conditions',24),('distinct_seen_queries',24),
                     ('physical_scenes',2),('original_map_variants',48)]:
    ck('broad_summary/' + field,bs[field],value,'saved_evidence')
for field, value in [('exact_array_pairs',576),('new_state_identities_reconstructed',168),
                     ('original_map_variants_decoded',48),('original_input_files',316),('inherited_evidence_files',682)]:
    ck('broad_audit/' + field,ba[field],value,'saved_evidence')
for field, value in [('actual_render_npz',60),('render_arrays_checked',180),('actual_context_npz',60),
                     ('context_arrays_against_rebuilt_expected',300),('baselines_against_old_trace',6),
                     ('guard_negatives',18),('stale18_rejected',12),('archive_members_verified',75)]:
    ck('source_audit/' + field,sa[field],value,'saved_evidence')
ck('different_script_same_author', aa['same_author_as_runner'], True, 'scope')
ck('broad_performance_not_measured',bs['performance_measured'],False,'scope')
ck('source_performance_not_measured',ss['speed_measurement'],False,'scope')
ck('placeholder_explained',bool(re.search(r'(占位.*(?:latent|embedding)|(?:latent|embedding).*占位)',report)),True,'scope')

links = re.findall(r'\[[^\]]+\]\(([^)]+)\)',report)
required_links = ['S11_RENDERER_REGRESSION_INDEPENDENT_AUDIT.md',
                  'S11_RENDERER_REGRESSION_RESULT_AUDIT.md',
                  'S11_SOURCE_REGRESSION_INDEPENDENT_AUDIT.md',
                  '../results/S11_renderer_regression/summary.json',
                  '../results/S11_renderer_regression/run_metadata.json',
                  '../results/S11_source_regression/summary.json',
                  '../results/S11_source_regression/run_metadata.json']
for rel in required_links:
    target=(ROOT/'docs'/rel).resolve()
    normalized=[(ROOT/'docs'/link.split('#')[0].strip('<>')).resolve() for link in links if '://' not in link]
    ck('link_present/' + rel,target in normalized,True,'evidence_link')
    ck('link_target_exists/' + rel,target.is_file(),True,'evidence_link')
for rel, expected in IDENTITIES.copy().items():
    ck('unchanged/' + rel,hashlib.sha256((ROOT/rel).read_bytes()).hexdigest(),expected,'identity')
counts={c:sum(r['category']==c for r in CHECKS) for c in sorted({r['category'] for r in CHECKS})}
out=dict(status='PASS' if all(r['passed'] for r in CHECKS) else 'FAIL',
         started_utc=START,completed_utc=datetime.now(timezone.utc).isoformat(),
         report_sha256=IDENTITIES['docs/S11_RESULTS.md'],checks_count=len(CHECKS),
         checks_by_category=counts,checks=CHECKS,input_sha256=IDENTITIES,
         scope='Saved JSON and report cross-check only; no NPZ/PNG/GT decoding, renderer/selector/NMS/model or full numerical audit.')
output=ROOT/'work/S11_manuscript_review/final_numeric_checks.json'
if output.exists(): raise FileExistsError(output)
output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ('checks','input_sha256')},ensure_ascii=False))
raise SystemExit(0 if out['status']=='PASS' else 1)
