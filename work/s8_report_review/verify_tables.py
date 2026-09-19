#!/usr/bin/env python3
"""Independent post-run S8 table audit; stdlib only, never imports the analyzer."""
import csv
import hashlib
import itertools
import json
import math
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/S8_report_audit'
MAPS = ('A0P0', 'A0P1', 'A1P0', 'A1P1')
READOUTS = ('official', 'candidate_no_nms', 'all20_nms', 'all20_no_nms')
METRICS = ('mae_mm', 'median_abs_mm', 'p90_abs_mm')
PAIRS = {'P_at_A0': (0, 1), 'P_at_A1': (2, 3), 'A_at_P0': (0, 2),
         'A_at_P1': (1, 3), 'diagonal': (0, 3)}
COUNTS = {}
MAX_ERROR = {}
EPS = Fraction(1, 10**12)
STARTED = datetime.now(timezone.utc).isoformat()


def check(ok, label, category):
    COUNTS[category] = COUNTS.get(category, 0) + 1
    if not ok:
        raise ValueError(label)


def close(got, wanted, label, category, tol=1e-10):
    diff = abs(float(got) - float(wanted))
    MAX_ERROR[category] = max(MAX_ERROR.get(category, 0), diff)
    check(math.isfinite(float(got)) and diff <= tol, label, category)


def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def read(p):
    return json.loads((ROOT / p).read_text())


def avg(xs):
    xs = [x for x in xs if x is not None]
    return math.fsum(xs) / len(xs) if xs else None


def support(row, m, mode='official'):
    return Fraction(row['readouts'][m][mode]['supported_pixels'], row['valid_pixels'])


def signs(values, eps=EPS):
    return dict(increased=sum(x > eps for x in values), decreased=sum(x < -eps for x in values),
                unchanged=sum(abs(x) <= eps for x in values))


def contrast(rows, a, b, amode='official', bmode='official'):
    diffs = [support(r, b, bmode) - support(r, a, amode) for r in rows]
    left = [r['readouts'][a][amode]['selected'] for r in rows]
    right = [r['readouts'][b][bmode]['selected'] for r in rows]
    return dict(delta_pp=[float(100*x) for x in diffs],
                mean_delta_pp=float(100*sum(diffs)/len(diffs)), **signs(diffs),
                selection_set_changed=sum(set(x) != set(y) for x, y in zip(left, right)),
                ordered_selection_changed=sum(x != y for x, y in zip(left, right)),
                order_only_changed=sum(x != y and set(x) == set(y) for x, y in zip(left, right)))


def summarize(rows):
    contrasts = {name: contrast(rows, MAPS[a], MAPS[b]) for name, (a, b) in PAIRS.items()}
    did = [support(r, MAPS[3])-support(r, MAPS[2])-support(r, MAPS[1])+support(r, MAPS[0]) for r in rows]
    cancels = []
    if rows[0]['stride'] == 12:
        for r in rows:
            v = [r['readouts'][m]['official'] for m in (MAPS[0], MAPS[2], MAPS[3])]
            ids = v[0]['selected'] == v[2]['selected'] and v[0]['selected'] != v[1]['selected']
            ds = [Fraction(x['supported_pixels'], r['valid_pixels']) for x in v]
            s = abs(ds[0]-ds[2]) <= EPS and abs(ds[0]-ds[1]) > EPS
            cancels.append(dict(block=r['block'], frame=r['frame'], ordered_id_cancellation=ids,
                                support_cancellation=s, both=ids and s))
    geometry = {}
    geo_extra = {}
    for m in MAPS:
        geometry[m] = {}
        geo_extra[m] = {}
        for mask, key in [('common_four', 'common_four'), ('own', 'own'), ('common_diagonal', 'diagonal')]:
            if mask == 'common_diagonal' and m not in (MAPS[0], MAPS[3]):
                geometry[m][key] = None
                geo_extra[m][mask] = None
                continue
            stats = [r['geometry'][m][mask] for r in rows]
            geometry[m][key] = {k: avg([v[k] for v in stats]) for k in METRICS}
            geo_extra[m][mask] = dict(queries_total=len(rows),
                queries_with_pixels=sum(v['n'] > 0 for v in stats), zero_pixel_queries=sum(v['n'] == 0 for v in stats),
                pixels=[v['n'] for v in stats], min_pixels=min(v['n'] for v in stats), max_pixels=max(v['n'] for v in stats),
                coverage_percent_per_query=[100*v['n']/r['valid_pixels'] for r, v in zip(rows, stats)],
                mean_coverage_percent=avg([100*v['n']/r['valid_pixels'] for r, v in zip(rows, stats)]),
                metric_valid_query_counts={k: sum(v[k] is not None for v in stats) for k in METRICS},
                metric_mean=geometry[m][key])
        geometry[m].update(zero_common_queries=sum(r['common_four_pixels'] == 0 for r in rows),
            zero_own_queries=sum(r['geometry'][m]['own']['n'] == 0 for r in rows),
            own_coverage_percent=avg([100*r['geometry'][m]['own']['n']/r['valid_pixels'] for r in rows]))
    expected = dict(query_ids=[[r['block'], r['frame']] for r in rows], queries=len(rows),
        support_percent={mode: {m: float(100*sum(support(r, m, mode) for r in rows)/len(rows)) for m in MAPS} for mode in READOUTS},
        contrasts=contrasts, interaction=dict(delta_pp=[float(100*x) for x in did], mean_delta_pp=float(100*sum(did)/len(did))),
        nms_removal={m: contrast(rows, m, m, 'official', 'candidate_no_nms') for m in MAPS},
        all20_nms_removal=contrast(rows, MAPS[0], MAPS[0], 'all20_nms', 'all20_no_nms'),
        concrete_S7_P_sign_pattern=(contrasts['P_at_A0']['mean_delta_pp'] < -1e-10 and contrasts['P_at_A1']['mean_delta_pp'] > 1e-10) if rows[0]['stride'] == 8 else None,
        predefined_cancellation_path='A0P0 -> A1P0 -> A1P1' if rows[0]['stride'] == 12 else None,
        cancellation_checks=cancels,
        simultaneous_id_and_support_cancellation_count=sum(v['both'] for v in cancels) if rows[0]['stride'] == 12 else None,
        common_four_coverage_percent=avg([100*r['common_four_pixels']/r['valid_pixels'] for r in rows]),
        common_four_pixels=[r['common_four_pixels'] for r in rows], geometry=geometry)
    extra = dict(query_ids=expected['query_ids'], interaction={**expected['interaction'], **signs(did),
        'selection_change_count': None, 'selection_change_note': 'DiD is a four-arm support contrast; use the four direct pair comparisons for selection-set/order changes.'},
        geometry=geo_extra, per_query_support_delta_fraction_tolerance=1e-12,
        position_mean_signs={k: ('positive' if contrasts[k]['mean_delta_pp'] > 1e-10 else 'negative' if contrasts[k]['mean_delta_pp'] < -1e-10 else 'zero') for k in ('P_at_A0', 'P_at_A1')})
    return expected, extra


def compare_tree(got, expected, path='summary'):
    if isinstance(expected, dict):
        check(set(got) == set(expected), path+' keys', 'summary_structure')
        for k in expected:
            compare_tree(got[k], expected[k], path+'.'+k)
    elif isinstance(expected, list):
        check(len(got) == len(expected), path+' length', 'summary_structure')
        for i, (x, y) in enumerate(zip(got, expected)):
            compare_tree(x, y, f'{path}[{i}]')
    elif isinstance(expected, float):
        close(got, expected, path, 'summary_values')
    else:
        check(got == expected and type(got) == type(expected), path, 'summary_values')


def main():
    check(not OUT.exists(), 'New output directory required', 'setup')
    paths = [Path('docs/S8_EXTERNAL_SCENE_PROTOCOL_V2.md'), Path('scripts/analyze_s8_results.py'),
             Path('scripts/run_s8_replay.py'), Path('results/S8_event_replay_v2/records.json'),
             Path('results/S8_event_replay_v2/run_metadata.json'), Path('results/S8_analysis_v2/summary.json'),
             Path('results/S8_analysis_v2/all_384_readouts.csv'), Path('results/S8_results_audit_v2/aggregate.json'),
             Path('results/S8_results_audit_v2/aggregate_by_block.json')]
    hashes = {str(p): sha(ROOT/p) for p in paths}
    meta = read(paths[4]); records = read(paths[3]); summary = read(paths[5])
    check(meta['status'] == 'completed' and meta['phase'] == 'complete', 'Completed run gate', 'setup')
    expected_keys = set(itertools.product((8, 12), range(3), range(20, 24)))
    bykey = {(r['stride'], r['block'], r['frame']): r for r in records}
    check(len(records) == 24 and len(bykey) == 24 and set(bykey) == expected_keys, 'Exact 24 case-query keys', 'record_shape')
    check(len({(r['block'], r['frame']) for r in records}) == 12, '12 distinct queries', 'record_shape')
    for key, r in bykey.items():
        check(r['split'] == 'test', str(key)+' split', 'record_shape')
        check(type(r['valid_pixels']) is int and r['valid_pixels'] > 0, str(key)+' positive valid target', 'record_shape')
        check(set(r['readouts']) == set(MAPS) and set(r['geometry']) == set(MAPS), str(key)+' four maps', 'record_shape')
        for m in MAPS:
            check(set(r['readouts'][m]) == set(READOUTS), str(key)+m+' four readouts', 'record_shape')
            for mode in READOUTS:
                v = r['readouts'][m][mode]; label = str(key)+m+mode
                check(len(v['selected']) == 4 and len(set(v['selected'])) == 4 and all(type(x) is int and 0 <= x < 20 for x in v['selected']), label+' history selection', 'readout_records')
                check(type(v['supported_pixels']) is int and 0 <= v['supported_pixels'] <= r['valid_pixels'], label+' integer support bounds', 'readout_records')
                close(v['support'], support(r, m, mode), label+' rational support', 'readout_records', 1e-15)
                if mode.startswith('all20_'):
                    check(v == r['readouts'][MAPS[0]][mode], label+' identical all20 control', 'readout_records')
            for mask in ('common_four', 'own', 'common_diagonal'):
                if mask not in r['geometry'][m]:
                    check(mask == 'common_diagonal' and m in (MAPS[1], MAPS[2]), 'Only off-diagonal mask absent', 'geometry_records')
                    continue
                v = r['geometry'][m][mask]
                check(type(v['n']) is int and 0 <= v['n'] <= r['valid_pixels'], str(key)+m+mask+' n', 'geometry_records')
                for metric in METRICS:
                    check((v[metric] is None) == (v['n'] == 0), str(key)+m+mask+metric+' missing iff empty', 'geometry_records')
                    if v[metric] is not None:
                        check(math.isfinite(v[metric]) and v[metric] >= 0, 'Finite nonnegative error', 'geometry_records')
                if mask != 'own':
                    check(v['n'] == r[mask+'_pixels'], str(key)+m+mask+' mask count', 'geometry_records')
                    check(v['n'] <= r['geometry'][m]['own']['n'], 'Common subset own', 'geometry_records')
            close(r['geometry'][m]['coverage'], Fraction(r['geometry'][m]['own']['n'], r['valid_pixels']), 'Own coverage integer fraction', 'geometry_records', 1e-15)
        check(r['common_four_pixels'] <= r['common_diagonal_pixels'], 'Four intersection subset diagonal', 'geometry_records')
        close(r['all20_support'], Fraction(r['all20_supported_pixels'], r['valid_pixels']), 'All 20 union support ratio', 'readout_records', 1e-15)
        check(max(r['readouts'][m][mode]['supported_pixels'] for m in MAPS for mode in READOUTS) <= r['all20_supported_pixels'] <= r['valid_pixels'], 'Four selections bounded by all 20 union', 'readout_records')
    with (ROOT/paths[6]).open(newline='') as f:
        reader = csv.DictReader(f); csv_rows = list(reader)
        check(reader.fieldnames == ['block', 'frame', 'stride', 'map', 'readout', 'selected', 'supported_pixels', 'valid_pixels', 'support_percent'], 'CSV nine columns', 'csv_structure')
    seen = set()
    for v in csv_rows:
        key = (int(v['stride']), int(v['block']), int(v['frame'])); r = bykey[key]
        uid = key+(v['map'], v['readout'])
        check(uid not in seen, 'Unique CSV row', 'csv_structure'); seen.add(uid)
        raw = r['readouts'][v['map']][v['readout']]
        expected = dict(block=r['block'], frame=r['frame'], stride=r['stride'], map=v['map'], readout=v['readout'],
                        selected=' '.join(map(str, raw['selected'])), supported_pixels=raw['supported_pixels'], valid_pixels=r['valid_pixels'])
        for k, wanted in expected.items():
            check(v[k] == str(wanted), uid.__str__()+k, 'csv_fields')
        close(float(v['support_percent']), 100*support(r, v['map'], v['readout']), str(uid)+' support_percent', 'csv_fields', 1e-12)
    check(len(csv_rows) == 384 and seen == {k+(m, q) for k in expected_keys for m in MAPS for q in READOUTS}, 'Exact 384 rows', 'csv_structure')
    for p, digest in summary['source_sha256'].items():
        close_path = Path(p) if Path(p).is_absolute() else ROOT/p
        check(sha(close_path) == digest, 'Summary source hash '+p, 'source_integrity')
    independent = {}; additions = {}; geometry_csv = []
    for stride in (8, 12):
        rows = [bykey[k] for k in sorted(bykey) if k[0] == stride]
        result, extra = summarize(rows)
        independent[str(stride)] = {'all': result, 'blocks': {}}
        additions[str(stride)] = {'all': extra, 'blocks': {}}
        for b in range(3):
            v, x = summarize([r for r in rows if r['block'] == b])
            independent[str(stride)]['blocks'][str(b)] = v
            additions[str(stride)]['blocks'][str(b)] = x
        for r in rows:
            for m in MAPS:
                item = dict(stride=stride, block=r['block'], frame=r['frame'], map=m, valid_pixels=r['valid_pixels'])
                for mask in ('common_four', 'own', 'common_diagonal'):
                    v = r['geometry'][m].get(mask)
                    item[mask+'_applicable'] = v is not None
                    item[mask+'_pixels'] = v['n'] if v is not None else None
                    item[mask+'_coverage_percent'] = 100*v['n']/r['valid_pixels'] if v is not None else None
                    item[mask+'_zero_pixels'] = v['n'] == 0 if v is not None else None
                    for metric in METRICS:
                        item[mask+'_'+metric] = v[metric] if v is not None else None
                geometry_csv.append(item)
    compare_tree(summary['per_stride'], independent)
    for r in read(paths[7])+read(paths[8]):
        scope = independent[str(r['stride'])]['all'] if 'block' not in r else independent[str(r['stride'])]['blocks'][str(r['block'])]
        check(r['unique_queries'] == scope['queries'], 'Other independent audit query count', 'cross_audit')
        for m in MAPS:
            for mode in READOUTS:
                close(r['support_percent'][m][mode], scope['support_percent'][mode][m], 'Cross audit support', 'cross_audit')
            for metric in METRICS:
                close(r['geometry'][m][metric], scope['geometry'][m]['common_four'][metric], 'Cross audit geometry', 'cross_audit')
            close(r['geometry'][m]['mean_own_coverage_percent'], scope['geometry'][m]['own_coverage_percent'], 'Cross audit own coverage', 'cross_audit')
        close(r['common_four_mean_coverage_percent'], scope['common_four_coverage_percent'], 'Cross audit common coverage', 'cross_audit')
    for p, digest in hashes.items():
        check(sha(ROOT/p) == digest, 'Source unchanged '+p, 'source_integrity')
    OUT.mkdir(parents=True)
    for name, value in [('independent_summary.json', independent), ('report_completeness_additions.json', additions), ('per_query_geometry.json', geometry_csv)]:
        (OUT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    with (OUT/'per_query_geometry.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(geometry_csv[0])); writer.writeheader(); writer.writerows(geometry_csv)
    receipt = dict(status='PASS', started_utc=STARTED, completed_utc=datetime.now(timezone.utc).isoformat(),
        audit_scope='Read-only records/CSV/summary audit after completed-run authorization. Integer/Fraction support arithmetic; stdlib means; no production analyzer imports. Geometry summaries reaggregated, no PNG/GT reconstruction or model execution.',
        counts=COUNTS, total_checks=sum(COUNTS.values()), max_abs_difference_by_category=MAX_ERROR,
        csv_rows=384, csv_fields_checked=384*9, original_records=24, unique_queries=12, geometry_rows=96,
        scope_note='Two strides repeat the same 12 correlated queries from one new physical scene. No outcome selection or threshold tuning.',
        source_sha256=hashes, audit_script_sha256=sha(Path(__file__)),
        output_sha256={p.name: sha(p) for p in OUT.iterdir() if p.is_file()},
        pre_result_static_review_utc='2026-09-05T19:45:28+00:00',
        result_read_authorized_after='2026-09-05T19:46:37+00:00',
        limitations=['No raw PNG/GT reconstruction here; another independent audit covers that scope.',
                     'Post-run report completeness additions present prespecified metrics; frozen analyzer and source results remain unchanged.',
                     'DiD selection-change counts are not well-defined; direct paired selection counts remain separate.'])
    (OUT/'verification.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
