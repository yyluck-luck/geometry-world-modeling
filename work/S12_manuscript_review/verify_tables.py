"""Standard-library report/CSV audit; never loads NPZ or numerical packages."""
import argparse
import csv
from datetime import datetime, timezone, timedelta
import hashlib
import io
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
checks = []


def check(condition, label):
    checks.append(dict(label=label, passed=bool(condition)))
    if not condition:
        raise AssertionError(label)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    paths = ['docs/S12_RESULTS.md', 'docs/S12_MATCHED_BUDGET_INDEPENDENT_AUDIT.md',
             'docs/S12_MATCHED_BUDGET_INDEPENDENT_AUDIT.json',
             'results/S12_matched_budget/run_metadata.json', 'results/S12_matched_budget/summary.json',
             'results/S12_matched_budget/records.json',
             'results/S12_matched_budget_independent_audit/verification.json',
             'reports/S12/report_provenance.json', 'reports/S12/all_strata.csv',
             'reports/S12/all_blocks.csv', 'reports/S12/all_192_paired_conditions.csv',
             'reports/S12/all_24_queries_primary_setting.csv']
    payload = {name: (ROOT/name).read_bytes() for name in paths}
    identities = {name: hashlib.sha256(value).hexdigest() for name, value in payload.items()}
    (args.output/'report_snapshot.md').write_bytes(payload['docs/S12_RESULTS.md'])
    load = lambda name: json.loads(payload[name])
    meta = load('results/S12_matched_budget/run_metadata.json')
    summary = load('results/S12_matched_budget/summary.json')
    records = load('results/S12_matched_budget/records.json')
    audit = load('results/S12_matched_budget_independent_audit/verification.json')
    audit_doc = load('docs/S12_MATCHED_BUDGET_INDEPENDENT_AUDIT.json')
    provenance = load('reports/S12/report_provenance.json')
    report = payload['docs/S12_RESULTS.md'].decode()
    try:
        check(meta['status'] == 'completed' and audit['status'] == 'PASS', 'completed experiment and independent audit')
        check(audit_doc['audit_receipt'] == audit, 'Independent audit prose receipt matches actual JSON')
        check(audit_doc['report_md_sha256'] == identities['docs/S12_MATCHED_BUDGET_INDEPENDENT_AUDIT.md'], 'Independent audit MD SHA')
        for name in ('run_metadata.json', 'records.json', 'summary.json'):
            path = 'results/S12_matched_budget/'+name
            check(identities[path] == audit_doc['actual_result_core_sha256'][path], 'Audited source '+name)
        for name, digest in {**provenance['inputs'], **provenance['outputs']}.items():
            check(identities[name] == digest, 'Report provenance SHA '+name)
        check(provenance['report_sha256'] == identities['docs/S12_RESULTS.md'], 'Report provenance final MD SHA')
        check(len(records) == 192 and len(summary['strata']) == 24 and len(summary['blocks']) == 48, 'Saved record and summary domains')
        check(meta['new_decision_trace_calls'] == 24 and meta['original_selection_calls'] == 0,
              'Exactly 24 new recording selectors and no old selector')
        check(meta['renderer_calls'] == meta['model_calls'] == 0, 'No renderer/model run')
        check(meta['reproduced_old_readout_scores'] == 768 and meta['reproduced_all20_upper_bounds'] == 48,
              'Old readout and separate upper-bound counts')

        def compare_csv(name, expected):
            rows = list(csv.DictReader(io.StringIO(payload['reports/S12/'+name].decode('utf-8-sig'))))
            check(len(rows) == len(expected), name+' row count')
            for index, (row, want) in enumerate(zip(rows, expected)):
                check(set(row) == set(want), name+f' row {index} column domain')
                for key, value in want.items():
                    if isinstance(value, bool):
                        actual = row[key] == 'True'
                        check(row[key] in ('True', 'False'), name+f' row {index} {key} bool syntax')
                    elif isinstance(value, int):
                        actual = int(row[key])
                    elif isinstance(value, float):
                        actual = float(row[key])
                    elif isinstance(value, list):
                        actual = list(map(int, row[key].split()))
                    else:
                        actual = row[key]
                    check(actual == value, name+f' row {index} {key}')
            return rows

        flat = []
        for row in records:
            geometry = row['old_readouts']['official']
            flat.append({**{k: row[k] for k in ('stage', 'split', 'block', 'query', 'stride', 'arm', 'main_comparison')},
                'geometry14_ids': geometry['selected'], 'pose14_ids': row['pose14']['selected'],
                'geometry14_candidates': row['geometry14_candidates'], 'pose14_ranked_candidates': row['pose14_ranked_candidates'],
                'valid_pixels': geometry['valid_pixels'], 'geometry14_supported_pixels': geometry['supported_pixels'],
                'pose14_supported_pixels': row['pose14']['supported_pixels'], 'geometry14_support': geometry['support'],
                'pose14_support': row['pose14']['support'],
                **{k: row[k] for k in ('geometry14_minus_pose14_pp', 'candidate_intersection_count', 'same_candidate_set',
                                       'selected_intersection_count', 'selected_set_changed', 'selected_order_changed',
                                       'pose14_same_order_as_all20_nms')}})
        compare_csv('all_192_paired_conditions.csv', flat)
        primary = [r for r in flat if r['stride'] == 8 and r['arm'] == 'A0P0']
        compare_csv('all_24_queries_primary_setting.csv', primary)
        for key, name in [('strata', 'all_strata.csv'), ('blocks', 'all_blocks.csv')]:
            compare_csv(name, [{k: v for k, v in row.items() if k != 'old_readout_mean_support'} for row in summary[key]])
        check(len({(r['stage'], r['block'], r['query']) for r in primary}) == 24, '24 unique seen primary queries')
        check(sum(r['pose14_same_order_as_all20_nms'] for r in primary) == 8, '8 of 24 pose14 equal old all20 order')
        for stage, split, count, equal_old in [('S7', 'development', 4, 0), ('S7', 'test', 8, 0), ('S8', 'test', 12, 8)]:
            subset = [r for r in primary if r['stage'] == stage and r['split'] == split]
            check(len(subset) == count and sum(r['pose14_same_order_as_all20_nms'] for r in subset) == equal_old,
                  f'Primary stratum {stage}/{split} count and equal-old count')

        max_mean_difference = 0.0
        for key in ('strata', 'blocks'):
            for index, group in enumerate(summary[key]):
                dimensions = ('stage', 'split', 'stride', 'arm') + (('block',) if key == 'blocks' else ())
                subset = [r for r in records if all(r[k] == group[k] for k in dimensions)]
                check(len(subset) == group['n_queries'], key+f' group {index} count')
                for field, values in [
                    ('geometry14_mean_support', [r['old_readouts']['official']['support'] for r in subset]),
                    ('pose14_mean_support', [r['pose14']['support'] for r in subset]),
                    ('geometry14_minus_pose14_mean_pp', [r['geometry14_minus_pose14_pp'] for r in subset])]:
                    difference = abs(math.fsum(values)/len(values)-group[field])
                    max_mean_difference = max(difference, max_mean_difference)
                    check(difference <= 1e-12, key+f' group {index} independently summed {field}')
                for field, calc in [('geometry_higher', sum(r['geometry14_minus_pose14_pp'] > 0 for r in subset)),
                                    ('pose_higher', sum(r['geometry14_minus_pose14_pp'] < 0 for r in subset)),
                                    ('equal', sum(r['geometry14_minus_pose14_pp'] == 0 for r in subset)),
                                    ('selected_set_changed', sum(r['selected_set_changed'] for r in subset))]:
                    check(group[field] == calc, key+f' group {index} independently counted {field}')
        # Compare the report's exact six-decimal display strings, not loose tolerances.
        mdrows = [[c.strip() for c in line.strip().strip('|').split('|')]
                  for line in report.splitlines() if re.match(r'^\| S[78] \|', line)]
        mainrows = [r for r in mdrows if len(r) == 6]
        stratarows = [r for r in mdrows if len(r) == 9]
        check(len(mainrows) == 2 and len(stratarows) == 24, 'Report main and full stratum table row counts')
        for row, group in zip(stratarows, summary['strata']):
            expected = [group['stage'], group['split'], str(group['stride']), group['arm'], str(group['n_queries']),
                        f"{100*group['geometry14_mean_support']:.6f}", f"{100*group['pose14_mean_support']:.6f}",
                        f"{group['geometry14_minus_pose14_mean_pp']:+.6f}",
                        f"{group['geometry_higher']}/{group['pose_higher']}/{group['equal']}"]
            check(row == expected, 'Report stratum '+str(expected[:4]))
        for row in mainrows:
            group = next(r for r in summary['strata'] if r['stage'] == row[0] and r['split'] == 'test' and r['main_comparison'])
            check(row == [group['stage'], str(group['n_queries']), f"{100*group['geometry14_mean_support']:.6f}%",
                          f"{100*group['pose14_mean_support']:.6f}%", f"{group['geometry14_minus_pose14_mean_pp']:+.6f}",
                          f"{group['geometry_higher']}/{group['pose_higher']}/{group['equal']}"], 'Report main '+row[0])
        timestamps = {}
        for field in ('started_utc', 'selections_sealed_utc', 'first_scoring_field_decode_utc', 'completed_utc'):
            local = datetime.fromisoformat(meta[field]).astimezone(timezone(timedelta(hours=8))).isoformat(timespec='milliseconds')
            check(local in report, 'Report recorded timestamp '+field)
            timestamps[field] = dict(recorded_utc=meta[field], display_local_millisecond_truncation=local)
        check(str(meta['peak_rss_bytes']) in report, 'Report recorded peak memory')
        check(audit['fixed_derived_float_tolerance'] == 1e-12 and audit['max_derived_float_difference'] <= 1e-12,
              'Independent audit tolerance applies to derived means/pp')
        prohibited = ['innovative', 'pioneering', 'revolutionary paradigm', 'transformative framework', 'superior',
                      'surpass', 'excel', 'remarkable', 'unprecedented', 'achieves SOTA', 'breakthrough performance',
                      'general-purpose', 'is capable of', 'notably', 'yet', 'yielding', 'at its essence', 'encompass',
                      'differentiate', 'reveal', 'underscore', 'exhibit superior capability', 'exceed', 'pave the way for',
                      'highlight the potential of', 'profound challenges', 'stems from', 'rigid', 'impede']
        matches = [{'line': i+1, 'phrase': word} for i, line in enumerate(report.splitlines())
                   for word in prohibited if word.lower() in line.lower()]
        dashes = [i+1 for i, line in enumerate(report.splitlines()) if '\u2014' in line]
        check(not matches and not dashes, 'Full report vocabulary/em-dash scan')
        links = re.findall(r'\]\(([^)]+)\)', report)
        check(all((ROOT/'docs'/link).resolve().is_file() for link in links), 'All relative report evidence links exist')
        check(all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest for name, digest in identities.items()),
              'All read-only source/report files unchanged during this review computation')
        check('numpy' not in sys.modules and 'torch' not in sys.modules and 'scipy' not in sys.modules,
              'Standard-library-only execution')
        result = dict(status='PASS', started_utc=started, completed_utc=datetime.now(timezone.utc).isoformat(),
                      scope='Report/CSV transcription and JSON aggregate arithmetic only; not a new underlying result audit',
                      reviewer_role='S12 runner author; distinct from report author; not distinct from runner author',
                      reviewed_sha256=identities, check_count=len(checks), csv_rows=[192, 24, 48, 24],
                      report_table_rows=[2, 24], checks=checks, timestamps=timestamps,
                      max_json_mean_recalculation_difference=max_mean_difference,
                      derived_summary_comparison_tolerance=1e-12, original_audit_max_derived_difference=audit['max_derived_float_difference'],
                      new_nms_calls=0, distance_calls=0, renderer_calls=0, model_calls=0, npz_files_read=0,
                      vocabulary_matches=matches, em_dash_lines=dashes)
    except BaseException as error:
        result = dict(status='FAILED', started_utc=started, failed_utc=datetime.now(timezone.utc).isoformat(),
                      reviewed_sha256=identities, checks=checks, error=str(error))
        (args.output/'checks.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
        raise
    (args.output/'checks.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k: result[k] for k in ('status', 'check_count', 'started_utc', 'completed_utc', 'max_json_mean_recalculation_difference')}))


if __name__ == '__main__':
    main()
