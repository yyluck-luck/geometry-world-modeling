#!/usr/bin/env python3
"""Finite report-to-saved-JSON audit. No ndarray, GT, model or scoring imports."""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

ROOT = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
OUT = ROOT / 'work/S33_reporting'
EXPECTED_REPORT = '381ba2bbbbaf36a707db09d8ec494fba586e950abf3937d58ef572ee1a6aa3aa'
started = datetime.now(timezone.utc).isoformat()
sources = {}
checks = []

def read(rel):
    p = ROOT / rel
    assert p.suffix in ('.json', '.md', '.py', '.csv')
    b = p.read_bytes()
    sources[str(p)] = hashlib.sha256(b).hexdigest()
    return b

def load(rel):
    return json.loads(read(rel))

def check(name, condition, details=None):
    checks.append(dict(name=name, passed=bool(condition), details=details))
    assert condition, name

report_bytes = read('docs/S33_RESULTS.md')
assert hashlib.sha256(report_bytes).hexdigest() == EXPECTED_REPORT
report = report_bytes.decode()
m = load('results/S33_pair_scale_scoring/metrics.json')
receipt = load('results/S33_pair_scale_scoring/receipt.json')
contract = load('work/S33_preparation/contract.json')
manifest = load('work/S33_scoring_preparation/manifest.json')
old = load('results/S33_pair_scale_scoring/imported_s32_metrics.json')
old_bytes = read('results/S33_pair_scale_scoring/imported_s32_per_frame.csv')
csv_bytes = read('results/S33_pair_scale_scoring/per_frame.csv')
read('work/S33_preparation/run_s33.py')
runner_sha = sources[contract['runner']]
check('published_source_contract_manifest_identities', runner_sha in report and
      sources[str(ROOT/'work/S33_preparation/contract.json')] in report and
      sources[str(ROOT/'work/S33_scoring_preparation/manifest.json')] in report and
      contract['identities'][contract['runner']] == runner_sha and
      len(contract['identities']) == 47)
check('score_PASS_and_saved_metrics_CSV_hash', receipt['status'] == 'PASS' and
      receipt['output_sha256']['metrics.json'] == sources[str(ROOT/'results/S33_pair_scale_scoring/metrics.json')] and
      receipt['output_sha256']['per_frame.csv'] == sources[str(ROOT/'results/S33_pair_scale_scoring/per_frame.csv')])
check('old48_JSON_and_CSV_import', m['per_frame'][:48] == old['per_frame'] and csv_bytes.startswith(old_bytes))
check('full64_48scored_16NA_16groups', len(m['per_frame']) == 64 and m['scored_rows'] == 48 and m['unavailable_rows'] == 16 and m['prespecified_groups'] == 16)
windows = ['fr2_desk_j2','fr1_xyz_j1','fr1_xyz_j2']
ends = ['initial_0step','corrected_getter_400','global_rescaled_400','common_pair_scale_400']
table_cells = 0
for w in windows:
    expected = '| ' + w + ' | ' + ' | '.join(f"{m['window_groups'][w][e]['absrel']*100:.5f}%" for e in ends) + ' |'
    check(w+'_four_AbsRel_table_cells', expected in report, expected)
    table_cells += 4
means = m['endpoint_summaries']
expected = '| 三个预定相机完整窗的描述均值 | ' + ' | '.join(f"{means[e]['three_preselected_pose_eligible']['absrel']*100:.5f}%" for e in ends) + ' |'
check('four_descriptive_AbsRel_cells', expected in report, expected)
table_cells += 4
check('all_four_window_means_NA', all(means[e]['all_four_prespecified']['absrel'] is None for e in ends) and
      '| **全部四个预定窗均值** | **NA** | **NA** | **NA** | **NA** |' in report)
labels = [('initial_0step','零步'),('global_rescaled_400','事后k'),('common_pair_scale_400','训练内尺度约束')]
deltas = []
comparisons = []
for w in windows:
    g = m['window_groups'][w]
    delta = 100*(g['initial_0step']['absrel']-g['common_pair_scale_400']['absrel'])
    deltas.append(delta)
    check(w+'_AbsRel_improvement_pp', f'{delta:.5f}' in report, delta)
    for e,label in labels:
        expected = f"| {w} {label} | {g[e]['rmse_m']:.9f} | {g[e]['delta1']*100:.6f}% |"
        check(w+'_'+e+'_RMSE_delta1_table', expected in report, expected)
        table_cells += 2
    for e in ends[:-1]:
        for metric,direction in [('absrel',-1),('rmse_m',-1),('delta1',1)]:
            gain = direction*(g['common_pair_scale_400'][metric]-g[e][metric])
            comparisons.append(dict(window=w,reference=e,metric=metric,gain_in_metric_units=gain))
            check(w+'_'+e+'_'+metric+'_strict_group_advantage', gain>0)
    check(w+'_same_full_GT_counts_no_invalid', all(
        g[e]['gt_valid_pixels_sum_descriptive']==g[ends[-1]]['gt_valid_pixels_sum_descriptive'] and
        g[e]['gt_invalid_pixels_sum_descriptive']==g[ends[-1]]['gt_invalid_pixels_sum_descriptive'] and
        g[e]['prediction_invalid_all_pixels_sum_descriptive']==0 for e in ends))
mean_delta=100*(means[ends[0]]['three_preselected_pose_eligible']['absrel']-means[ends[-1]]['three_preselected_pose_eligible']['absrel'])
check('descriptive_AbsRel_improvement_pp', f'{mean_delta:.5f}' in report, mean_delta)
check('published_valid_and_missing_denominators', '642877/625608/594549' in report and '143555/160824/191883' in report)

launch=load('work/S33_launch/receipt.json')
check('published_launch_time_and_wall', launch['started_utc'][11:26] in report and launch['completed_utc'][11:26] in report and f"{launch['wall_seconds']:.6f}" in report and launch['returncode']==0)
for w in windows:
    producer=load(f'results/S33_pair_scale_control/{w}/receipt.json')
    ga=load(f'results/S33_pair_scale_control/{w}/GA/C2a/receipt.json')
    gate=load(f'results/S33_pair_scale_control/{w}/GA/C2a/s33_initial_gate.json')
    external=load(f'work/S33_execution/{w}/receipt.json')
    obs=ga['observer']
    check(w+'_published_receipt_counts', producer['status']=='PASS' and producer['new_Adam']==400 and producer['new_backward']==400 and producer['new_MST']==1 and producer['new_PnP']==3 and producer['original_clean_calls']==1 and producer['new_model_forwards']==0 and producer['contract_sha256']==launch['contract_sha256'])
    check(w+'_saved_initial_and_internal_gate_claims', gate['initial_raw_count']==33 and all(gate[k] is True for k in ['raw_bytes_exact','decoded_exact','objective_exact','alignment_exact','initial_factor_exact_one']) and obs['s32_objective_forward_counts']['total']==403 and obs['s33_scale_constraint']['trace_rows']==400 and obs['independent_clean_mismatch_pixels']==0)
    check(w+'_published_objectives_and_world_error', f"{obs['s32_initialization']['initial_objective']:.7f}" in report and f"{obs['postfinal_objective']:.9f}" in report and f"{ga['independent_backprojection_max_abs']:.4e}".replace('e-0','e-') in report)
    check(w+'_published_time_resource', f"{external['wall_seconds']:.6f}" in report and str(external['peak_rss_bytes']) in report)
    check(w+'_m0_exact_saved_scalar', str(obs['s33_scale_constraint']['initial_mean_log_scale']).replace('e-0','e-') in report)
barrier=load('work/S33_scoring_freeze/endpoint_barrier.json')
check('83_sealed_files_count_only_not_rehashed', len(barrier['verified_sha256'])==83)
external=load('work/S33_scoring_execution/scoring/receipt.json')
check('score_time_resource_and_GT_use', f"{external['wall_seconds']:.6f}" in report and str(external['peak_rss_bytes']) in report and receipt['GT_images_decoded']==12 and receipt['new_k_computations']==0 and receipt['old_endpoint_array_reads']==0 and receipt['sensor_GT_byte_start_utc'][11:26] in report)
check('interpretive_boundaries_retained', all(x in report for x in ['独立数值复核尚在准备','完整预测像素的mu独立分析尚待完成','不能将其改名宣称创新方法','没有将帧/像素当独立样本','不能称无损纯坐标规范变换','本轮未核每个实际输入或计算实例C','完整VMem生成视频仍未执行']))
check('reviewed_sources_unchanged', all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in sources.items()))
out=dict(status='PASS_METADATA_ONLY_REPORT_FACT_REVIEW',started_utc=started,completed_utc=datetime.now(timezone.utc).isoformat(),reviewer='/root/research_novelty_routes',report_author='/root',role_disclosure='Different from report author; this reviewer also authored the S33 primary scorer. This is NOT independent underlying scoring replication.',report_sha256=EXPECTED_REPORT,checks=checks,displayed_numeric_table_cells=table_cells,group_metric_comparisons=comparisons,zero_step_improvements_percentage_points=deltas,descriptive_improvement_percentage_points=mean_delta,source_sha256=sources,required_corrections=[],limits=['Snapshot-specific preliminary manuscript review; future report revisions are not automatically covered.','No NPZ, NPY, RGB, sensor-depth bytes, model, GA, or original scoring executed.','Receipt-only claims about 33 states, gradients, scale gates, clean/world and 83 sealed payloads were not rederived from arrays.','No independent-review PASS or depth-mu conclusion is granted by this review.','No paper survey or novelty verification was repeated.'])
for name in ['report_metadata_review.json','reviewed_report_381ba2.md.source.txt']:
    assert not (OUT/name).exists()
(OUT/'reviewed_report_381ba2.md.source.txt').write_bytes(report_bytes)
(OUT/'report_metadata_review.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':out['status'],'checks':len(checks),'table_cells':table_cells,'pairwise_metric_comparisons':len(comparisons),'receipt_sha256':hashlib.sha256((OUT/'report_metadata_review.json').read_bytes()).hexdigest()},ensure_ascii=False))
