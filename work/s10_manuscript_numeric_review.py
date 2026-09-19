"""Independent final-table/CSV/SVG checks; no experiment or original audit imports."""
import csv, hashlib, json, re
from collections import Counter
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/S10_manuscript_review_v3'
OUT.mkdir(exist_ok=False)
START = datetime.now(timezone.utc).isoformat()
C = Counter()
def check(ok, category, message):
    if not ok:
        raise AssertionError(message)
    C[category] += 1
def readj(p):
    return json.loads((ROOT / p).read_text())
def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
def csvrows(name):
    with (ROOT / 'reports/S10' / name).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))
def compare_rows(got, wanted, category):
    check(len(got) == len(wanted), category, 'row count')
    for i, (row, expected) in enumerate(zip(got, wanted)):
        check(set(row) == set(expected), category, f'columns {i}')
        for k, v in expected.items():
            if v is None:
                ok = row[k] == ''
            elif isinstance(v, bool):
                ok = row[k] == str(v)
            elif isinstance(v, int):
                ok = int(row[k]) == v
            elif isinstance(v, float):
                ok = float(row[k]) == v
            else:
                ok = row[k] == v
            check(ok, category, f'row {i} field {k}')

try:
    own = readj('results/S10_renderer_comparison_independent_review/independent_summary.json')
    calls = [json.loads(x) for x in (ROOT / 'results/S10_renderer_comparison/invocations.jsonl').read_text().splitlines()]
    metadata = readj('results/S10_renderer_comparison/run_metadata.json')
    md = (ROOT / 'docs/S10_RENDERER_COMPARISON_RESULTS.md').read_text()
    tex = (ROOT / 'reports/S10/保持选图结果的本机提速实验.tex').read_text()
    groups = [dict(group=k, pairs=v['pairs'], queries=v['distinct_queries'], original_mean_ms=v['original']['mean_ms'], candidate_mean_ms=v['candidate']['mean_ms'], ratio_of_totals=v['ratio_of_total_times'], median_paired_ratio=v['median_paired_ratio']) for k, v in own['groups'].items()]
    compare_rows(csvrows('五组耗时汇总.csv'), groups, 'group_csv')
    compare_rows(csvrows('24查询中位数.csv'), own['per_query'], 'query_csv')
    compare_rows(csvrows('120个正式配对.csv'), own['pairs'], 'pair_csv')
    compare_rows(csvrows('全部逐次记录.csv'), calls, 'invocation_csv')
    figures = []
    for method in ('original', 'candidate'):
        for q in own['per_query']:
            values = sorted(x['elapsed_ns'] for x in calls if x['phase'] == 'measured' and x['label'] == q['label'] and x['method'] == method)
            check(len(values) == 5, 'figure_raw', q['label'])
            figures.append(dict(label=q['label'], method=method, median_ms=values[2]/1e6, min_ms=values[0]/1e6, max_ms=values[-1]/1e6, repeats=5))
    figure_rows=csvrows('绘图数据.csv')
    row_key=lambda r:(r['label'],r['method'])
    check(len(set(map(row_key,figure_rows)))==48,'figure_identity','unique query/method pairs')
    compare_rows(sorted(figure_rows,key=row_key), sorted(figures,key=row_key), 'figure_csv')
    for g in groups:
        fields=[str(g['pairs'])]+[format(g[k], '.6f') for k in ('original_mean_ms','candidate_mean_ms','ratio_of_totals','median_paired_ratio')]
        row=next(x for x in md.splitlines() if x.startswith('| '+g['group']+' |'))
        got=[x.strip() for x in row.split('|')[2:-1]]
        for x,y in zip(got,fields):
            check(x == y, 'md_numeric_table', row)
        check(len(got)==len(fields), 'md_table_shape', row)
        label='合并' if g['group']=='all' else g['group']
        row=next(x for x in tex.splitlines() if x.startswith(label+' &'))
        got=[x.strip().rstrip('\\').strip() for x in row.split('&')[1:]]
        fields=[str(g['pairs'])]+[format(g[k],'.3f') for k in ('original_mean_ms','candidate_mean_ms','ratio_of_totals')]
        check(len(got)==len(fields), 'tex_table_shape', row)
        for x,y in zip(got,fields):
            check(x==y, 'tex_numeric_table', row)
    for q in own['per_query']:
        row=next(x for x in md.splitlines() if x.startswith('| '+q['label']+' |'))
        got=[x.strip() for x in row.split('|')[2:-1]]
        check(len(got)==3, 'md_table_shape', row)
        for text, key in zip(got,('original_median_ms','candidate_median_ms','ratio_of_medians')):
            check(text==format(q[key],'.6f'), 'md_numeric_table', row)
    allg = own['groups']['all']
    reduction=(1-allg['candidate']['total_ns']/allg['original']['total_ns'])*100
    for arm in ('original','candidate'):
        for key in ('median_ms','min_ms','max_ms'):
            # Report decimal half-up rounding: an exact half-nanosecond median
            # must not inherit an accidental downward binary-float formatting tie.
            printed=str(Decimal(str(allg[arm][key])).quantize(Decimal('.000001'),rounding=ROUND_HALF_UP))
            check(printed in md,'prose_number',arm+key)
    for val in (allg['ratio_of_total_times'],min(q['ratio_of_medians'] for q in own['per_query']), max(q['ratio_of_medians'] for q in own['per_query'])):
        check(format(val,'.6f') in md,'prose_number',str(val))
    check(format(reduction,'.3f') in md and format(reduction,'.3f') in tex,'prose_number','reduction')
    prov=readj('reports/S10/report_input_provenance.json')
    for p, h in prov['sources'].items():
        check(sha(p)==h,'provenance_sha',p)
    check(prov['derived_time_reduction_percent']==reduction,'provenance_value','reduction')
    check(prov['figure_points']==48,'provenance_value','points')
    check(prov['figure_range_definition']=='min/max of five repeated timings; not confidence interval','provenance_value','range')
    # Check actual SVG coordinates, rather than trusting only the source CSV.
    ns={'s':'http://www.w3.org/2000/svg'}
    svg=ET.parse(ROOT/'reports/S10/figures/all_queries.svg').getroot()
    def g_id(element, id):
        return next(x for x in element.iter() if x.get('id')==id)
    def nums(path):
        return list(map(float,re.findall(r'-?\d+(?:\.\d+)?',path.get('d'))))
    svg_errors=[]
    scales=[]
    for axn, stage, cols, markers in [(1,'S7',(1,2),(29,30)),(2,'S8',(5,6),(67,68))]:
        ax=g_id(svg,f'axes_{axn}')
        ticks=[x for x in ax.iter() if x.get('id','').startswith('ytick_')]
        tick_values=[float(next(x.iterfind('.//s:text',ns)).text) for x in ticks]
        ys=[nums(next(x.iterfind('.//s:path',ns)))[1] for x in ticks]
        check(tick_values==[0,400,800,1200,1600],'svg_axis','tick values')
        scale=(ys[-1]-ys[0])/(tick_values[-1]-tick_values[0]); scales.append(scale)
        xticks=[x for x in ax.iter() if x.get('id','').startswith('xtick_')]
        check(len(xticks)==12,'svg_axis','query labels')
        for i, x in enumerate(xticks):
            texts=[t.text for t in x.iterfind('.//s:text',ns)]
            check(texts==[f'B{i//4}',f'Q{20+i%4}'],'svg_axis','query identity')
        for method,col,marker in zip(('original','candidate'),cols,markers):
            fs=[r for r in figures if r['method']==method and r['label'].startswith(stage)]
            paths=list(g_id(ax,f'LineCollection_{col}').iterfind('s:path',ns))
            uses=list(g_id(ax,f'line2d_{marker}').iterfind('.//s:use',ns))
            check(len(paths)==len(uses)==len(fs)==12,'svg_shape','48 data points')
            for path,use,f in zip(paths,uses,fs):
                x1,ymin,x2,ymax=nums(path)
                check(x1==x2==float(use.get('x')),'svg_x','alignment')
                for actual,key in [(ymin,'min_ms'),(ymax,'max_ms'),(float(use.get('y')),'median_ms')]:
                    error=abs(actual-(ys[0]+scale*f[key])); svg_errors.append(error)
                    check(error<=2e-6,'svg_y_numeric',f['label']+' '+key)
        # Zero is exactly the bottom of the axes rectangle; scale extends to 1800 ms.
        patch=next(ax.iterfind('s:g/s:path',ns))
        bound=nums(patch)
        check(bound[1]==ys[0],'svg_axis','zero bottom')
        check(abs((bound[5]-ys[0])/scale-1800)<3e-5,'svg_axis','same upper bound')
    check(abs(scales[0]-scales[1])<1e-12,'svg_axis','shared y scale')
    # Times in manuscripts are rounded to milliseconds in Asia/Shanghai.
    design=readj('docs/S10_RENDERER_DESIGN_FREEZE.json')
    freeze=readj('docs/S10_RENDERER_COMPARISON_EXECUTION_FREEZE.json')
    edge=readj('results/S10_renderer_edges_candidate/verification.json')
    pre=readj('docs/S10_RENDERER_PRE_RUN_REVIEW.json')
    def fmt_time(t):
        dt=datetime.fromisoformat(t)+timedelta(hours=8,microseconds=500)
        return dt.strftime('%H:%M:%S.')+f'{dt.microsecond//1000:03d}'
    times=[design['frozen_utc'],edge['started_utc'],pre['reviewed_utc'],freeze['frozen_utc'],metadata['started_utc'],metadata['all_initial_correctness_passed_utc'],metadata['measurement_started_utc'],metadata['completed_utc']]
    for t in times:
        check(fmt_time(t) in md,'time_prose',t)
    for t in (times[0],times[3],times[5],times[6],times[7]):
        check(fmt_time(t) in tex,'time_prose',t)
    check(format(metadata['total_elapsed_seconds'],'.6f') in md,'time_prose','wall seconds MD')
    check(format(metadata['total_elapsed_seconds'],'.3f') in tex,'time_prose','wall seconds TEX')
    check(str(metadata['process_peak_rss_bytes']) in md,'prose_number','process peak')
    check('S10_RENDERER_COMPARISON_INDEPENDENT_REVIEW.md' not in md,'resolved_link','wrong file removed')
    check('若文件名不同' not in md,'resolved_link','fallback removed')
    for p in ('S10_RENDERER_COMPARISON_INDEPENDENT_AUDIT.md','S10_RENDERER_RESULT_AUDIT.md','S10_NUMPY_PROMOTION_REVIEW.md'):
        check((ROOT/'docs'/p).exists() and p in md,'resolved_link',p)
    reviewed=['docs/S10_RENDERER_COMPARISON_RESULTS.md','reports/S10/保持选图结果的本机提速实验.tex','reports/S10/保持选图结果的本机提速实验.pdf','reports/S10/report_input_provenance.json']+[str(p.relative_to(ROOT)) for p in sorted((ROOT/'reports/S10').glob('*.csv'))]+[str(p.relative_to(ROOT)) for p in sorted((ROOT/'reports/S10/figures').glob('all_queries.*'))]
    receipt=dict(status='PASS',started_utc=START,completed_utc=datetime.now(timezone.utc).isoformat(),checks_passed=sum(C.values()),checks_by_category=dict(C),scope='Saved raw timing and independent previously audited summary to final CSV, Markdown/TeX tables and actual SVG coordinates; no renderer/model/timing rerun. PDF/PNG hashes bound only, visual QA is root-owned.',figure_max_svg_coordinate_error_points=max(svg_errors),figure_svg_tolerance_points=2e-6,figure_tolerance_reason='SVG coordinates serialized to six decimal places; no relaxation of original raw numeric equality gates.',reviewed_sha256={p:sha(p) for p in reviewed},independent_raw_audit_verification_sha256=sha('results/S10_renderer_comparison_independent_review/verification.json'),original_audit_documents_untouched=True)
except Exception as e:
    receipt=dict(status='FAIL',started_utc=START,completed_utc=datetime.now(timezone.utc).isoformat(),checks_passed=sum(C.values()),checks_by_category=dict(C),error=repr(e))
(OUT/'verification.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
(OUT/'reviewer_snapshot.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps(receipt,ensure_ascii=False,indent=2))
if receipt['status']!='PASS':
    raise SystemExit(1)
