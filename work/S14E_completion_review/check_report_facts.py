"""Check saved report transcription; never decode NPZ, trajectory, or sensor data."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import io
import json
import re

ROOT = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
OUT = ROOT / 'work/S14E_completion_review'
started = datetime.now(timezone.utc).isoformat()
checks = []
evidence = {}

def sha(path):
    value = hashlib.sha256(path.read_bytes()).hexdigest()
    evidence[str(path)] = value
    return value

def read(rel):
    p = ROOT / rel
    sha(p)
    return json.loads(p.read_text())

def check(name, passed):
    checks.append({'name': name, 'passed': bool(passed)})

def dt(value):
    return datetime.fromisoformat(value)

report_path = ROOT / 'docs/S14E_RESULTS.md'
report_hash = sha(report_path)
report = report_path.read_text()
pre = read('results/S14E_known_camera_prepare/run_metadata.json')
model = read('results/S14E_known_camera_queries/run_metadata.json')
score = read('results/S14E_known_camera_score/run_metadata.json')
verification = read('results/S14E_known_camera_independent/verification.json')
metrics = read('results/S14E_known_camera_score/metrics.json')
alignment = read('results/S14E_known_camera_prepare/alignment.json')
fig = read('work/S14E_reporting/figure_receipt.json')
prior = read('work/S14E_pre_run_review/final_review_receipt.json')
condition = read('results/S14E_known_camera_prepare/condition_seal.json')

for name, data in [('prepare', pre), ('model', model), ('score', score), ('figure', fig)]:
    check(name + ' success', data['status'] == 'SUCCESS')
    check(name + ' before/after identities', data['before_after_identity_pass'] is True)
    check(name + ' time ordered', dt(data['started_utc']) < dt(data['completed_utc']))
    for field in ['started_utc', 'completed_utc']:
        china = dt(data[field]).astimezone(timezone(__import__('datetime').timedelta(hours=8)))
        check(name + ' report ' + field, china.strftime('%H:%M:%S.%f') in report)

for path, expected in prior['sources'].items():
    check('pre-reviewed unchanged ' + path, sha(Path(path)) == expected)
check('pre-review before real prepare', dt(prior['completed_utc']) < dt(pre['started_utc']))
check('pre-review actual artificial check count', prior['checks']['total'] == 218)
for name, data in [('prepare', pre), ('queries', model), ('score', score)]:
    check(name + ' frozen manifest identity', sha(ROOT / ('results/S14E_known_camera_' + name) / 'frozen_manifest.json') == data['manifest_sha256'])

check('prepare NPZ whitelist count', pre['counters']['npz_arrays_decoded'] == 41)
check('prepare trajectory count', pre['counters']['trajectory_rows_decoded'] == 20926)
check('prepare history byte parity', pre['history_pose_byte_parity_pass'] is True)
check('prepare no target images', pre['target_rgb_decoded'] == pre['target_depth_decoded'] == 0)
check('prepare GT camera explicitly allowed', pre['known_camera_gt_allowed'] is True)
check('prepare sealed before model', dt(pre['completed_utc']) <= dt(condition['sealed_utc']) < dt(model['started_utc']))
check('model five queries', len(model['query_runs']) == model['counters']['query_calls'] == 5)
check('model restored five fields', len(model['state_before']) == 5)
check('model zero parity exact six outputs', model['parity_all_six_outputs_exact'] and len(model['parity_output_ids']) == 6)
for run in model['query_runs']:
    n = run['call']
    check(f'query {n} saved success', run['status'] == 'PASS' and run['output_saved'])
    check(f'query {n} unchanged state', run['state_ids_after'] == model['state_before'])
    check(f'query {n} flags', run['dummy'] == 'zero' and run['flags'] == {'img_mask':[False], 'ray_mask':[True], 'update':[False], 'reset':[False]})
check('model 17 arrays', model['counters']['npz_arrays_decoded'] == 17)
for key in ['history_rgb_decoded','target_rgb_decoded','target_depth_decoded','image_open_attempts','history_forward_calls','query_image_encoder_batches']:
    check('model zero ' + key, model['counters'][key] == 0)
check('model five ray encoder calls', model['counters']['query_ray_encoder_calls'] == 5)
check('model GT camera explicitly allowed', model['known_camera_conditions_are_authorized_inputs'] is True)
check('score four depths only', score['counters']['depths_decoded'] == 4 and score['counters']['target_rgb_decoded'] == score['counters']['model_calls'] == 0)
check('prediction sealed before first target hash/read', dt(model['completed_utc']) <= dt(score['prediction_sealed_utc']) < dt(score['first_target_depth_hash_utc']) <= dt(score['first_depth_open_attempt_utc']))
check('seal verified before target hash', dt(score['seal_verified_utc']) <= dt(score['first_target_depth_hash_utc']))
check('same scale report and data', str(alignment['s_model_per_metric']) in report and alignment['s_model_per_metric'] == metrics['s_model_per_metric'] == score['s_model_per_metric'])
check('history only alignment', alignment['history_count'] == 20 and alignment['fit_includes_targets'] is False)
check('RMS report model units', f"{alignment['rms_model']:.10f}模型单位" in report)
check('verification 868 actually passing entries', verification['status'] == 'PASS' and verification['check_count'] == len(verification['checks']) == 868 and all(x['passed'] is True for x in verification['checks']))
check('verification recorded input counts', verification['checked_identities'] == 166 and verification['npz_arrays_decoded'] == 106 and verification['depths_decoded'] == 4 and verification['model_calls'] == 0)
check('verification after score', dt(score['completed_utc']) < dt(verification['started_utc']))
for field in ['started_utc','completed_utc']:
    china = dt(verification[field]).astimezone(timezone(__import__('datetime').timedelta(hours=8)))
    check('verification report ' + field, china.strftime('%H:%M:%S.%f') in report)

for stage in ['prepare','model']:
    caller = read('work/S14E_execution/' + stage + '/caller_receipt.json')
    check(stage + ' caller success', caller['status'] == 'PASS' and caller['returncode'] == 0 and caller['monitor_ok'])
    check(stage + ' caller RSS transcription', str(caller['maxrss']) + '字节' in report)
    check(stage + ' caller elapsed transcription', f"{caller['elapsed_seconds']:.6f}秒" in report)
    check(stage + ' caller invokes S14E', any('s14e_' in part for part in caller['command']))

csv_path = ROOT / 'work/S14E_reporting/all_12_scores.csv'
csv_hash = sha(csv_path)
check('reporting CSV unchanged copy', csv_hash == sha(ROOT / 'results/S14E_known_camera_score/metrics.csv'))
csv_rows = list(csv.DictReader(io.StringIO(csv_path.read_text())))
check('all 12 rows present', len(csv_rows) == len(metrics['rows']) == 12)
for rownum, (written, original) in enumerate(zip(csv_rows, metrics['rows'])):
    check(f'CSV row {rownum} fields', set(written) == set(original))
    for key, value in original.items():
        if isinstance(value, int): same = int(written[key]) == value
        elif isinstance(value, float): same = float(written[key]) == value
        elif value is None: same = written[key] == ''
        else: same = written[key] == value
        check(f'CSV row {rownum} {key}', same)

labels = {'ray':'CUT3R记忆查询','history_zbuffer':'20帧历史点云重投影','history_constant':'历史深度中位常数'}
summary = {x['method']:x['means'] for x in metrics['equal_query_means']}
for method, mean in summary.items():
    line = f"| {labels[method]} | {mean['delta1_all_gt']*100:.4f}% | {mean['coverage']*100:.4f}% | {mean['common_mae_m']*100:.4f} | {mean['common_abs_rel']:.6f} |"
    check(method + ' summary report row with meter to cm conversion', line in report)
for q in metrics['query_order']:
    rows = {row['method']:row for row in metrics['rows'] if row['query_index'] == q}
    ray, warp, constant = (rows[x] for x in metrics['method_order'])
    difference = (ray['delta1_all_gt']-warp['delta1_all_gt'])*100
    line = f"| {q} | {ray['gt_valid_count']} | {ray['common_valid_count']} | {ray['delta1_all_gt']*100:.4f}% | {warp['delta1_all_gt']*100:.4f}% | {constant['delta1_all_gt']*100:.4f}% | +{difference:.4f}个百分点 |"
    check(f'query {q} report row', line in report)
    check(f'query {q} main metric model exceeds baseline', difference > 0)
check('mean improvement percentage points', f"{(summary['ray']['delta1_all_gt']-summary['history_zbuffer']['delta1_all_gt'])*100:.4f}个百分点" in report)
check('all GT visits explicitly related', all(x['gt_valid_pixel_visits']==167400 for x in metrics['equal_query_means']) and '不能当167400次独立试验或4个独立场景' in report)

for filename, expected in fig['output_sha256'].items():
    check('figure output identity ' + filename, sha(ROOT / 'work/S14E_reporting' / filename) == expected)
check('figure source score binding', fig['score_metadata_sha256'] == sha(ROOT/'results/S14E_known_camera_score/run_metadata.json'))
check('figure includes all targets and all methods', fig['queries_shown'] == [20,21,22,23] and fig['methods_shown'] == metrics['method_order'] and (fig['gt_panels'],fig['prediction_panels'],fig['rgb_panels']) == (4,12,4))
check('figure no clipped depth range', fig['depth_range']['display_range_m'] == fig['depth_range']['data_range_m'] and fig['depth_clipping'] is False)
check('figure no smoothing/per-panel color', fig['depth_smoothing'] is False and fig['depth_per_panel_scaling'] is False)
check('figure range report in meters', '—'.join(f'{n:.10f}' for n in fig['depth_range']['data_range_m']) + '米' in report)
photo_reads = [x for x in fig['reads'] if x.get('query_index') in [20,21,22,23]]
check('four RGB only after score success', len(photo_reads)==4 and all(dt(x['opened_utc'])>dt(score['completed_utc']) for x in photo_reads))
check('figure not additional experiment', fig['metrics_recomputed'] is False and fig['model_calls']==fig['depth_png_decoded']==0)
for target in re.findall(r'\]\(([^)]+)\)',report):
    if target.startswith('https://'): continue
    check('report local link exists ' + target, (report_path.parent / target).resolve().exists())
check('report unchanged during fact check', sha(report_path) == report_hash)

receipt = {'schema':'s14e-completion-report-factcheck-v1','status':'PASS' if all(c['passed'] for c in checks) else 'FAIL',
    'started_utc':started,'completed_utc':datetime.now(timezone.utc).isoformat(),
    'checks':checks,'check_count':len(checks),'evidence':evidence,
    'report_sha256':report_hash,'scope':'Saved JSON/CSV transcription, source identities, report links, time chain and figure receipts; no numerical experiment rerun',
    'actual_access':{'npz_arrays_decoded':0,'sensor_depth_png_decoded':0,'raw_rgb_png_decoded':0,'raw_trajectory_read':0,'model_calls':0},
    'derived_operations':'Only formatting and arithmetic on already published per-query scalar results for report comparison.'}
(OUT/'factcheck_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':receipt['status'],'checks':len(checks),'failed':[x for x in checks if not x['passed']],'report_sha256':report_hash},ensure_ascii=False))
