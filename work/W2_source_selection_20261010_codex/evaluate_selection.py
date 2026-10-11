#!/usr/bin/env python3
"""Evaluate already sealed source-only decisions; reuse unchanged W1 geometry metric."""
import argparse
import json
from pathlib import Path

import numpy as np
import score_candidates as geometry
from generate_candidates import sha_file, publish_json, require, validate_manifest


def verify_selection(stage, manifest, candidate_seal):
    seal_path = stage / 'selection/SELECTION_SEAL.json'
    seal = json.loads(seal_path.read_text())
    for name, key in [('PROTOCOL.md', 'protocol_sha256'), ('MANIFEST.json', 'manifest_sha256'),
                      ('FREEZE.json', 'freeze_sha256')]:
        require(seal[key] == sha_file(stage / name), 'Selection seal mismatch: ' + name)
    expected = {w['window_id']: w for w in manifest['windows']}
    records = seal['records']
    require(len(records) == len(expected) and {r['window_id'] for r in records} == set(expected),
            'Incomplete/duplicate selection records')
    candidate_sha = {r['npz']: r['npz_sha256'] for r in candidate_seal['records']}
    freeze = json.loads((stage / 'FREEZE.json').read_text())
    choices = {}
    for record in records:
        for key, digest_key in [('receipt', 'receipt_sha256'), ('matches', 'matches_sha256')]:
            require(Path(record[key]).name == record[key], 'Unsafe selection filename')
            require(sha_file(stage / 'selection' / record[key]) == record[digest_key], 'Changed selection output')
        value = json.loads((stage / 'selection' / record['receipt']).read_text())
        wid = record['window_id']
        require(value['status'] == 'OK' and value['window_id'] == wid, 'Bad selection status/identity')
        require(value['window'] == expected[wid], 'Selection window differs from manifest')
        for key in ['protocol_sha256', 'manifest_sha256', 'freeze_sha256']:
            require(value[key] == seal[key], 'Selection receipt identity mismatch')
        require(value['selector_sha256'] == freeze['files']['select_candidates.py'], 'Unfrozen selector')
        require(value['started_utc'] >= freeze['frozen_utc'] and value['finished_utc'] <= seal['sealed_utc'],
                'Selection outside freeze/seal boundary')
        for candidate in manifest['candidates']:
            cid = candidate['candidate_id']
            require(value['candidate_hashes'][cid] == candidate_sha[wid + '__' + cid + '.npz'],
                    'Selector used another candidate')
        reference = json.loads((stage / 'candidates' / (wid + '__c0.json')).read_text())
        require(value['source_files'] == reference['source_files'], 'Selector/predictor source inputs differ')
        index = value['selected_candidate_index']
        require(type(index) is int and 0 <= index < len(manifest['candidates']), 'Invalid chosen index')
        require(value['selected_candidate_id'] == manifest['candidates'][index]['candidate_id'], 'Chosen ID mismatch')
        if value['abstained']:
            require(index == 0 and value['abstention_reason'], 'Invalid fallback')
        else:
            scores = np.asarray(value['candidate_scores'], dtype=float)
            require(scores.shape == (len(manifest['candidates']),) and np.isfinite(scores).all(), 'Invalid selector scores')
            expected_index = int(np.flatnonzero(scores <= scores.min() + 1e-12)[0])
            require(index == expected_index, 'Choice does not follow frozen score rule')
        require(value['matches_file'] == record['matches'] and value['matches_sha256'] == record['matches_sha256'],
                'Match record identity mismatch')
        choices[wid] = value
    return seal, choices


def equal_scene_mean(rows, arm, stratum='primary'):
    scenes = sorted({r['scene'] for r in rows})
    require(scenes, 'No scene rows')
    return float(np.mean([np.mean([r['arms'][stratum][arm] for r in rows if r['scene'] == scene])
                          for scene in scenes]))


def gain(baseline, selected):
    require(np.isfinite(baseline) and baseline > 0, 'Undefined relative gain')
    return float(1. - selected / baseline)


def comparison(rows, comparator, stratum='primary'):
    baseline = equal_scene_mean(rows, comparator, stratum)
    selected = equal_scene_mean(rows, 'selected', stratum)
    scenes = sorted({r['scene'] for r in rows})
    per_scene = {}
    contributions = []
    for scene in scenes:
        subset = [r for r in rows if r['scene'] == scene]
        b = float(np.mean([r['arms'][stratum][comparator] for r in subset]))
        s = float(np.mean([r['arms'][stratum]['selected'] for r in subset]))
        per_scene[scene] = {'comparator_error': b, 'selected_error': s, 'relative_gain': gain(b, s)}
        for row in subset:
            delta = row['arms'][stratum][comparator] - row['arms'][stratum]['selected']
            contributions.append({'window_id': row['window_id'], 'scene': scene,
                                  'weighted_gain': delta / (len(scenes) * len(subset))})
    positive = sorted([c for c in contributions if c['weighted_gain'] > 0],
                      key=lambda c: (-c['weighted_gain'], c['window_id']))
    top = positive[:2]
    excluded = {c['window_id'] for c in top}
    remainder = [r for r in rows if r['window_id'] not in excluded]
    require({r['scene'] for r in remainder} == set(scenes), 'Robustness removal would remove a scene')
    rb = equal_scene_mean(remainder, comparator, stratum)
    rs = equal_scene_mean(remainder, 'selected', stratum)
    top_sum = sum(c['weighted_gain'] for c in top)
    net = sum(c['weighted_gain'] for c in contributions)
    positive_sum = sum(c['weighted_gain'] for c in positive)
    return {'comparator': comparator, 'comparator_error': baseline, 'selected_error': selected,
            'relative_gain': gain(baseline, selected), 'by_scene': per_scene,
            'positive_windows': len(positive), 'window_contributions': contributions,
            'top_two': top, 'net_weighted_gain': net,
            'top_two_share_of_net_gain': top_sum / net if net > 0 else None,
            'top_two_share_of_positive_gain': top_sum / positive_sum if positive_sum > 0 else None,
            'leave_top_two': {'excluded_window_ids': sorted(excluded), 'remaining_windows': len(remainder),
                             'comparator_error': rb, 'selected_error': rs,
                             'relative_gain': gain(rb, rs), 'weighting': 'equal scenes, equal remaining windows within scene'}}


def decide(comparisons, abstention_fraction):
    failures = []
    for name in ['c0', 'fusion']:
        result = comparisons[name]
        if result['relative_gain'] < .05:
            failures.append(name + ':aggregate_gain_below_5_percent')
        if any(x['relative_gain'] <= 0 for x in result['by_scene'].values()):
            failures.append(name + ':nonpositive_gain_in_a_scene')
        if result['leave_top_two']['relative_gain'] < .025:
            failures.append(name + ':leave_top_two_gain_below_2.5_percent')
        share = result['top_two_share_of_net_gain']
        if share is None or share > .50:
            failures.append(name + ':top_two_dominate_net_gain_or_nonpositive_net')
    if abstention_fraction > .25:
        failures.append('abstention_above_25_percent')
    return ('STOP_TESTED_SELECTOR' if failures else 'GO_TO_NEXT_SMALL_PILOT'), failures


def evaluate(stage, data_root):
    manifest_path, protocol = stage / 'MANIFEST.json', stage / 'PROTOCOL.md'
    manifest = json.loads(manifest_path.read_text())
    candidates, windows = validate_manifest(manifest)
    candidate_seal = geometry.verify_seal(stage / 'CANDIDATE_SEAL.json', stage / 'candidates', manifest_path, protocol)
    freeze = geometry.validate_freeze(stage / 'FREEZE.json', candidate_seal['freeze_sha256'])
    require(sha_file(__file__) == freeze['files']['evaluate_selection.py'], 'Unfrozen evaluator')
    selection_seal, choices = verify_selection(stage, manifest, candidate_seal)
    # All identities verified before the first measured-depth decoder is called below.
    provenance, rows = {}, []
    grid = geometry.sampling_grid(manifest['scoring']['stride'])
    for window in windows:
        raw = geometry.score_window(window, candidates, stage / 'candidates', data_root, grid, provenance)
        decision = choices[window['window_id']]
        index = decision['selected_candidate_index']
        raw.update(selected_candidate_id=decision['selected_candidate_id'], selected_candidate_index=index,
                   abstained=decision['abstained'], abstention_reason=decision['abstention_reason'],
                   source_only_scores=decision['candidate_scores'])
        raw['arms'] = {}
        for stratum in ['primary', 'secondary']:
            values = raw[stratum]
            raw['arms'][stratum] = {'selected': values['candidate']['fixed_errors'][index],
                                    'c0': values['candidate']['fixed_errors'][0],
                                    'fusion': values['single_controls']['fixed_errors'][0],
                                    'medoid': values['single_controls']['fixed_errors'][1],
                                    'oracle': values['candidate']['complete_oracle']}
        rows.append(raw)
        print('[scored] ' + window['window_id'], flush=True)
    summary = {stratum: {arm: equal_scene_mean(rows, arm, stratum)
                         for arm in ['selected', 'c0', 'fusion', 'medoid', 'oracle']}
               for stratum in ['primary', 'secondary']}
    comparisons = {stratum: {arm: comparison(rows, arm, stratum) for arm in ['c0', 'fusion']}
                   for stratum in ['primary', 'secondary']}
    abstention = float(np.mean([r['abstained'] for r in rows]))
    verdict, failures = decide(comparisons['primary'], abstention)
    return {'status': 'COMPLETE', 'evidence_label': 'MEASURED', 'scored_utc': geometry.now(),
            'manifest_sha256': sha_file(manifest_path), 'protocol_sha256': sha_file(protocol),
            'freeze_sha256': sha_file(stage / 'FREEZE.json'),
            'candidate_seal_sha256': sha_file(stage / 'CANDIDATE_SEAL.json'),
            'selection_seal_sha256': sha_file(stage / 'selection/SELECTION_SEAL.json'),
            'candidate_sealed_utc': candidate_seal['sealed_utc'], 'selection_sealed_utc': selection_seal['sealed_utc'],
            'evaluator_sha256': sha_file(__file__), 'measurement_input_hashes': provenance,
            'summary': summary, 'summary_capped_epe_pixels': {k: {a: v * 800 for a, v in x.items()} for k, x in summary.items()},
            'comparisons': comparisons, 'abstention_fraction': abstention,
            'verdict': verdict, 'failed_gates': failures, 'rows': rows,
            'new_method_validated': False, 'novelty_authorization': 'NONE'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage', type=Path, required=True)
    p.add_argument('--data-root', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    require(not args.out.exists(), 'Refusing to overwrite outcome')
    result = evaluate(args.stage.resolve(), args.data_root.resolve())
    publish_json(args.out, result)
    print(json.dumps({k: result[k] for k in ['verdict', 'failed_gates', 'summary_capped_epe_pixels', 'abstention_fraction']}, indent=2))


if __name__ == '__main__':
    main()
