"""Review completed S14B outputs and byte identities; never load input arrays."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import json
import math
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
P = ROOT / 'results/S14B_observation_disagreement'
V = ROOT / 'results/S14B_independent_verification'
SCHEMA = 's14b-observation-disagreement-v1'
checks = []

def check(name, condition):
    if not condition:
        raise AssertionError(name)
    checks.append(name)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_text())

manifest_path = ROOT / 'docs/S14B_EXECUTION_MANIFEST.json'
mf = read(manifest_path)
meta = read(P / 'metadata.json')
ver = read(V / 'verification.json')
callers = {s: read(ROOT / f'work/S14B_execution/{s}/caller_receipt.json')
           for s in ('measurement', 'verification')}
check('manifest_schema', mf['schema'] == SCHEMA)
check('frozen_state', mf['status'] == 'FROZEN_FOR_DESCRIPTIVE_EXECUTION')
check('24_unique_inputs', len(mf['inputs']) == len({x['path'] for x in mf['inputs']}) == 24)
check('25_unique_controls', len(mf['controls']) == len({x['path'] for x in mf['controls']}) == 25)
expected = {x['path']: x['sha256'] for x in mf['inputs'] + mf['controls']}
check('49_disjoint_controls_inputs', len(expected) == 49)
expected['docs/S14B_EXECUTION_MANIFEST.json'] = sha(manifest_path)
current = {name: sha(ROOT/name) for name in expected}
check('50_current_frozen_identities', current == expected)
inp = {x['path']: x['sha256'] for x in mf['inputs']}
for stage, caller in callers.items():
    check(stage+'_caller_success', caller['status'] == 'PASS' and caller['exit_code'] == 0)
    check(stage+'_before_after_50', caller['identity_before'] == expected == caller['identity_after'])
    check(stage+'_unchanged', caller['identity_unchanged'] is True)
    check(stage+'_timeout_600', caller['external_timeout_seconds'] == mf['external_timeout_seconds'] == 600)
check('pre_run_precedes_freeze', read(ROOT/'work/S14B_pre_run_review/review.json')['completed_utc'] < mf['frozen_utc'])
check('freeze_before_actual_measurement', mf['frozen_utc'] < meta['started_utc'])
check('independent_after_actual_measurement', meta['finished_utc'] < ver['started_utc'])
check('metadata_success_schema', meta['schema'] == SCHEMA and meta['status'] == 'SUCCESS')
check('verification_success_schema', ver['schema'] == 's14b-independent-verification-v1' and ver['status'] == 'PASS')
check('production_input_before_after', meta['input_sha256_before'] == inp == meta['input_sha256_after'])
check('independent_input_before_after', ver['input_hashes_before'] == inp == ver['input_hashes_after'])
check('source_snapshot_current_and_frozen', sha(P/'source_snapshot.py') == mf['source_sha256'] == meta['source_sha256_before'] == meta['source_sha256_after'])
check('verifier_snapshot_current_and_frozen', sha(V/'verifier_source_snapshot.py') == mf['independent_verifier_sha256'] == ver['source_sha256_before'] == ver['source_sha256_after'])
check('execution_manifest_exact_copy', (P/'execution_manifest.json').read_bytes() == manifest_path.read_bytes())
check('manifest_metadata_identity', meta['manifest_sha256_before'] == meta['manifest_sha256_after'] == sha(manifest_path))
check('frozen_environment_production', meta['environment'] == mf['environment'])
check('frozen_environment_verifier', all(ver[k] == mf['environment'][k] for k in ('python','numpy','platform')))
check('frozen_tolerance', mf['tolerance'] == meta['tolerances'] == {'atol': 1e-12, 'rtol': 1e-10} and ver['atol'] == 1e-12 and ver['rtol'] == 1e-10)
check('empty_errors_and_identity_success', meta['identity_errors'] == [] and meta['identity_unchanged'] and ver['errors'] == [])
outputs = {p.name: sha(p) for p in P.iterdir() if p.is_file()}
check('metadata_output_hashes', {k:outputs[k] for k in meta['output_sha256']} == meta['output_sha256'])
check('all_seven_production_outputs_preserved', len(outputs) == 7 and callers['verification']['production_files_before'] == outputs == callers['verification']['production_files_after'])
check('caller_metadata_receipt_identity', callers['measurement']['result_receipt_sha256'] == outputs['metadata.json'])
check('caller_verification_receipt_identity', callers['verification']['result_receipt_sha256'] == sha(V/'verification.json'))
check('verifier_result_before_after', ver['result_hashes_before'] == ver['result_hashes_after'] == {k:outputs[k] for k in ver['result_hashes_before']})
summary = read(P/'summary.json')
association = read(P/'association_indices.json')
check('summary_schema_exact', set(summary) == {'schema','quantile_method','blocks'} and summary['schema'] == SCHEMA and summary['quantile_method'] == 'linear')
check('association_schema_exact', set(association) == {'schema','blocks'} and association['schema'] == SCHEMA)
point_cols = 'phase block stride point_id m n_obs single_source birth_frame birth_flat_index birth_u birth_v mem_x mem_y mem_z radius W B A D W_over_radius2 B_over_radius2 A_over_radius2 D_over_radius2'.split()
frame_cols = 'phase block stride point_id frame n_obs c_x c_y c_z within_variance'.split()
with (P/'points.csv').open(newline='') as stream:
    reader=csv.DictReader(stream); check('23_point_fields_exact', reader.fieldnames == point_cols)
    points=list(reader)
with (P/'frame_centroids.csv').open(newline='') as stream:
    reader=csv.DictReader(stream); check('10_frame_fields_exact', reader.fieldnames == frame_cols)
    frames=list(reader)
check('all_rows_rectangular', all(None not in r and all(v is not None for v in r.values()) for r in points+frames))
blocks=[(s,b) for s in ('S7','S8') for b in range(3)]
check('six_summary_blocks_exact', [(b['phase'],b['block']) for b in summary['blocks']] == blocks)
check('six_association_blocks_exact', [(b['phase'],b['block']) for b in association['blocks']] == blocks)
check('all_point_blocks', set((r['phase'],int(r['block'])) for r in points) == set(blocks))
check('all_frame_blocks', set((r['phase'],int(r['block'])) for r in frames) == set(blocks))
check('positive_radius_all_finite_nonnegative_metrics', all(float(r['radius'])>0 and all(math.isfinite(float(r[k])) and float(r[k])>=0 for k in point_cols[-8:]) for r in points))
check('actual_point_frame_count', len(points)==meta['counters']['points']==ver['points']==16164 and len(frames)==meta['counters']['frame_groups']==ver['frame_groups']==64896)
totals=Counter()
table=[]
for key,s,a in zip(blocks,summary['blocks'],association['blocks']):
    ps=[r for r in points if (r['phase'],int(r['block']))==key]
    fs=[r for r in frames if (r['phase'],int(r['block']))==key]
    check(str(key)+'_summary_fields',set(s)=={'phase','block','stride','n_points','n_observations','n_frame_groups','single_source_points','multi_source_points','by_m'})
    check(str(key)+'_stride8', s['stride']==a['stride']==8 and all(int(r['stride'])==8 for r in ps+fs))
    check(str(key)+'_point_ids', [int(r['point_id']) for r in ps]==list(range(s['n_points'])))
    single=[r for r in ps if int(r['m'])==1]
    multi=[r for r in ps if int(r['m'])>1]
    check(str(key)+'_single_source',len(single)==s['single_source_points'] and all(int(r['single_source'])==1 and int(r['n_obs'])==1 and all(float(r[k])==0 for k in point_cols[-8:]) for r in single))
    check(str(key)+'_multi_source',len(multi)==s['multi_source_points'] and all(int(r['single_source'])==0 for r in multi))
    check(str(key)+'_groups_obs_counts',len(fs)==len(a['groups'])==s['n_frame_groups']==sum(int(r['m']) for r in ps) and sum(int(r['n_obs']) for r in ps)==sum(int(r['n_obs']) for r in fs)==s['n_observations'])
    check(str(key)+'_association_unique_covers_outputs',sorted(i for g in a['groups'] for i in g['flat_indices'])==list(range(s['n_observations'])))
    check(str(key)+'_association_matches_frame_rows',[(g['point_id'],g['frame'],len(g['flat_indices'])) for g in a['groups']]==[(int(r['point_id']),int(r['frame']),int(r['n_obs'])) for r in fs])
    mc=Counter(int(r['m']) for r in ps)
    check(str(key)+'_m_counts', [(g['m'],g['n_points']) for g in s['by_m']]==sorted(mc.items()))
    totals.update({k:s[k] for k in ('n_points','n_observations','n_frame_groups','single_source_points','multi_source_points')})
    table.append({k:s[k] for k in ('phase','block','n_points','n_observations','n_frame_groups','single_source_points','multi_source_points')} | {'multi_source_positive_B':sum(float(r['B'])>0 for r in multi)})
check('totals_equal_runtime', totals['n_points']==16164 and totals['n_observations']==meta['counters']['observations']==ver['observations']==88088 and totals['n_frame_groups']==64896)
check('actual_input_counts', all(meta['counters'][k]==v for k,v in {'input_files_cached':24,'input_bytes_cached':8926362,'npz_files_decoded':12,'numerical_arrays_decoded':42,'prediction_json_files_decoded':12,'completed_blocks':6,'gt_scoring_query_feature_reads':0,'model_runs':0}.items()))
check('independent_check_totals', ver['exact_checks']==1983074 and ver['float_checks']==472500 and ver['max_abs_difference']==8.348877145181177e-14)
record={'schema':'s14b-completion-machine-evidence-v1','completed_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS','checks_count':len(checks),'checks':checks,'frozen_identities_current':current,'production_outputs_current':outputs,'verifier_output_sha256':sha(V/'verification.json'),'totals':dict(totals),'blocks':table,'metadata_counters':meta['counters'],'real_run_times':{'measurement_started_utc':meta['started_utc'],'measurement_finished_utc':meta['finished_utc'],'measurement_elapsed_seconds':meta['elapsed_seconds'],'peak_rss_bytes':meta['peak_rss_bytes'],'peak_rss_MiB':meta['peak_rss_bytes']/1048576,'verification_started_utc':ver['started_utc'],'verification_ended_utc':ver['ended_utc']},'independent_checks':{k:ver[k] for k in ('exact_checks','float_checks','max_abs_difference')},'review_scope':'Completed CSV/JSON outputs and compressed byte SHA only. No NPZ input arrays decoded and no production or verification entry rerun.'}
(OUT/'machine_evidence.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:record[k] for k in ('status','checks_count','totals','blocks','real_run_times','independent_checks')},ensure_ascii=False,indent=2))
