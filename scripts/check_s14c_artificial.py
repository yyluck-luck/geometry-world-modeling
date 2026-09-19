#!/usr/bin/env python3
"""Deterministic artificial S14C counterexamples. Never read project result data."""
import argparse
import copy
import importlib.util
import io
import json
from pathlib import Path

import numpy as np

SCRIPT = Path(__file__).with_name('measure_s14c_selection_disagreement.py')
spec = importlib.util.spec_from_file_location('s14c_artificial_production', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def main(output):
    m.require(not output.exists(), 'Artificial output exists; choose another directory')
    output.mkdir(parents=True)
    started = m.now()
    checks = []

    def check(name, condition):
        m.require(condition, name)
        checks.append(dict(name=name, passed=True))

    def rejects(name, action):
        try:
            action()
        except (ValueError, KeyError, FileNotFoundError):
            checks.append(dict(name=name, passed=True))
        else:
            raise AssertionError(name)

    def point(values, radius=1):
        return dict(radius=radius, m=len(values), frames={
            i: dict(xyz=np.array([v, 0., 0.]), n_obs=i+1) for i, v in enumerate(values)})

    def action(selected):
        return dict(selected=selected, candidates=list(range(14)), ranked_candidates=list(range(14)),
                    camera_pair=2., query_distance=3.)

    meta = dict(stage='S7', block=0, query=20, split='development', arm='A0P0', stride=8)
    a = action([0, 1, 2, 3])
    b = action([0, 1, 2, 4])
    pts = {0: point([0., 2., 5., 8., 9.], 2.)}
    r, d = m.measure_query(meta, pts, a, a)
    check('same selected set x exact zero', r['disagreement_g_minus_p'] == 0 and r['same_selected_set'])
    reverse = copy.deepcopy(a)
    reverse['selected'].reverse()
    r2, d2 = m.measure_query(meta, pts, reverse, a)
    check('selected frame order invariant', r2['disagreement_g_minus_p'] == 0)
    changed_counts = copy.deepcopy(pts)
    for frame in changed_counts[0]['frames'].values():
        frame['n_obs'] *= 99
    r3, _ = m.measure_query(meta, changed_counts, a, a)
    check('fixed centroid pixel duplication no reweighting', r3 == r)
    two = point([0., 2.])
    ids, val, pairs = m.point_disagreement(two, [0, 1, 2, 3])
    check('k2 single pair and centered variance identity', val == 4. and val == 4 * np.var([0., 2.]))
    # All three vertices of an equilateral triangle have the same pair distance.
    triangle = dict(radius=1., frames={0: dict(xyz=np.array([0., 0., 0.])),
        1: dict(xyz=np.array([2., 0., 0.])), 2: dict(xyz=np.array([1., np.sqrt(3.), 0.]))})
    v2 = m.point_disagreement(triangle, [0, 1])[1]
    v3 = m.point_disagreement(triangle, [0, 1, 2])[1]
    check('unequal k uses per-point pair mean', abs(v2-v3) < 1e-14)
    empty = {0: point([0.])}
    er, ed = m.measure_query(meta, empty, a, b)
    check('empty common domain remains null', er['disagreement_g_minus_p'] is None and
          er['source_count_p_minus_g'] is None and er['status'] == 'NO_COMMON_MULTISOURCE_POINTS')
    check('empty common denominator null', er['common_fraction_of_g'] is None and er['common_fraction_of_p'] is None)
    check('all 25 coverage cells retained', len(ed['source_count_grid']) == 25 and
          sum(c['n_points'] for c in ed['source_count_grid']) == 1)
    aa, bb = copy.deepcopy(a), copy.deepcopy(b)
    aa.update(camera_pair=2., query_distance=7.)
    bb.update(camera_pair=5., query_distance=3.)
    br, _ = m.measure_query(meta, pts, aa, bb)
    check('fixed camera baseline directions', br['camera_pair_p_minus_g'] == 3. and br['query_distance_g_minus_p'] == 4.)
    check('average exact ties', m.tied_ranks([2., 1., 2., 4.]).tolist() == [2.5, 1., 2.5, 4.])
    check('signed Spearman negative', abs(m.spearman([1., 2., 3.], [3., 2., 1.])['rho'] + 1) < 1e-14)
    check('constant rho null', m.spearman([1., 1., 1.], [1., 2., 3.])['reason'] == 'constant_x_or_y')
    check('n below three null', m.spearman([1., 2.], [1., 2.])['reason'] == 'fewer_than_three_usable')
    rejects('out of range frame rejected', lambda: m.frame_ids([0, 1, 2, 20], 4))
    rejects('duplicate frame rejected', lambda: m.frame_ids([0, 1, 1, 2], 4))

    # Construct all inputs from literals in this file, not historical experiment files.
    synth = output/'synthetic_root'
    synth.mkdir()
    point_text = 'phase,block,stride,point_id,m,radius\n'
    frame_text = 'phase,block,stride,point_id,frame,n_obs,c_x,c_y,c_z\n'
    for stage in ('S7', 'S8'):
        for block in range(3):
            point_text += f'{stage},{block},8,0,5,2\n'
            for frame, x in enumerate([0., 2., 5., 8., 9.]):
                frame_text += f'{stage},{block},8,0,{frame},{frame+1},{x},0,0\n'
    parsed = m.parse_maps(point_text.encode(), frame_text.encode())
    check('six artificial maps parse', len(parsed) == 6)
    rejects('zero radius rejected', lambda: m.parse_maps(point_text.replace(',5,2\n', ',5,0\n').encode(), frame_text.encode()))
    rejects('negative radius rejected', lambda: m.parse_maps(point_text.replace(',5,2\n', ',5,-2\n').encode(), frame_text.encode()))
    rejects('duplicate point frame rejected', lambda: m.parse_maps(point_text.encode(), (frame_text+frame_text.splitlines(True)[1]).encode()))
    rejects('missing point frame rejected', lambda: m.parse_maps(point_text.encode(), '\n'.join(frame_text.splitlines()[:-1]).encode()))

    def trace(chosen):
        steps = []
        for index, frame in enumerate(chosen[1:], 1):
            steps.append(dict(frame=frame, accepted=True, comparisons=[[other, float(frame-other)] for other in chosen[:index]]))
        return dict(selected=chosen, expanded_candidates=list(range(14)), nms=True,
                    sorted_frames=list(range(14)), distances_float32=list(map(float, range(14))), steps=steps)

    def encoded(obj):
        return (json.dumps(obj, sort_keys=True, allow_nan=False)+'\n').encode()

    payloads = {m.POINT_PATH: point_text.encode(), m.FRAME_PATH: frame_text.encode()}
    score_rows = []
    for stage in ('S7', 'S8'):
        for block in range(3):
            split = 'development' if stage == 'S7' and block == 0 else 'test'
            source = dict(block=block, stride=8, split=split, queries=[])
            for query in range(20, 24):
                gt, pt = trace([0, 1, 2, 3]), trace([0, 1, 2, 4])
                source['queries'].append(dict(frame=query, maps={'A0P0': dict(
                    official_trace=dict(selected=gt['selected'], candidates=list(range(14)),
                                        candidate_counts=[[i, int(i < 14)] for i in range(20)]),
                    readouts=dict(official=gt))}))
                pose = dict(stage=stage, block=block, query=query, split=split, trace=pt,
                    full20_frame_order=list(range(20)), full20_sorted_frames=list(range(20)),
                    full20_distances_float32=list(map(float, range(20))), pose14_ranked_candidates=list(range(14)))
                payloads[m.pose_path(stage, block, query)] = encoded(pose)
                score_rows.append(dict(stage=stage, block=block, query=query, split=split, arm='A0P0', stride=8,
                    main_comparison=True, old_readouts=dict(official=dict(selected=gt['selected'],
                    supported_pixels=1, valid_pixels=3, support=1/3)),
                    pose14=dict(selected=pt['selected'], supported_pixels=2, valid_pixels=3, support=2/3),
                    geometry14_candidates=list(range(14)), pose14_ranked_candidates=list(range(14)),
                    geometry14_minus_pose14_pp=100*(1/3-2/3)))
            payloads[m.prediction_path(stage, block)] = encoded(source)
    for rel, data in payloads.items():
        target = synth/rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    score_bytes = encoded(score_rows)
    source_sha = m.sha(SCRIPT.read_bytes())
    manifest = dict(schema=m.SCHEMA, source_sha256=source_sha,
        inputs=[dict(path=p, sha256=m.sha(data)) for p, data in sorted(payloads.items())],
        score_input=dict(path=m.SCORE_PATH, sha256=m.sha(score_bytes)))
    manifest_path = synth/'manifest.json'
    m.save(manifest_path, manifest)
    check('score path absent before full measure', not (synth/m.SCORE_PATH).exists())
    result = output/'successful_artificial_measure'
    metadata = m.run('measure', synth, manifest_path, result)
    check('32 inputs sealed without score reads', metadata['status'] == 'SUCCESS' and
          metadata['counters']['input_hash_reads_before'] == 32 and metadata['counters']['score_hash_reads'] == 0 and
          metadata['counters']['measurement_rows'] == 24 and not (synth/m.SCORE_PATH).exists())
    check('source and manifest before after identity', metadata['source_sha256'] == metadata['source_sha256_after'] and
          metadata['manifest_sha256'] == metadata['manifest_sha256_after'])
    rows = m.decode((result/'rows.json').read_bytes())['rows']
    details = m.decode((result/'point_details.json').read_bytes())['rows']
    check('saved label operation order retained', m.join_labels(rows, details, score_rows)[0]['y_pose_minus_geometry_pp'] ==
          -score_rows[0]['geometry14_minus_pose14_pp'])
    wrong = copy.deepcopy(score_rows)
    wrong[0]['pose14']['valid_pixels'] = 4
    rejects('label denominator mismatch rejected', lambda: m.join_labels(rows, details, wrong))
    wrong = copy.deepcopy(score_rows)
    wrong[0]['geometry14_candidates'].reverse()
    rejects('label candidate order mismatch rejected', lambda: m.join_labels(rows, details, wrong))
    wrong = copy.deepcopy(score_rows)
    wrong[0]['pose14']['selected'].reverse()
    rejects('label selected order mismatch rejected', lambda: m.join_labels(rows, details, wrong))
    wrong = copy.deepcopy(score_rows)
    wrong[1]['query'] = wrong[0]['query']
    rejects('duplicate query labels rejected', lambda: m.join_labels(rows, details, wrong))
    rejects('missing query label rejected', lambda: m.join_labels(rows, details, score_rows[:-1]))
    bad_result = output/'missing_seal_measurement'
    bad_result.mkdir()
    rejects('unsealed result rejected before score read', lambda: m.run('associate', synth, manifest_path,
            output/'expected_failed_unsealed_associate', bad_result))
    failed_meta = m.decode((output/'expected_failed_unsealed_associate/run_metadata.json').read_bytes())
    check('unsealed rejection score count zero', failed_meta['counters']['score_hash_reads'] == 0)
    (synth/m.SCORE_PATH).write_bytes(score_bytes)
    associated = m.run('associate', synth, manifest_path, output/'successful_artificial_associate', result)
    check('associate gated score read after seal', associated['status'] == 'SUCCESS' and
          associated['measurement_seal_verified_utc'] < associated['score_first_read_utc'] and
          associated['counters']['score_json_decoded'] == 1 and associated['counters']['correlations'] == 32)
    changed = copy.deepcopy(manifest)
    changed['source_sha256'] = '0'*64
    changed_path = synth/'bad_source_manifest.json'
    m.save(changed_path, changed)
    rejects('changed source hash rejected', lambda: m.run('measure', synth, changed_path, output/'expected_failed_source'))
    original = (synth/m.POINT_PATH).read_bytes()
    (synth/m.POINT_PATH).write_bytes(original+b'changed')
    rejects('changed input rejected before decoding', lambda: m.run('measure', synth, manifest_path, output/'expected_failed_input'))
    badmeta = m.decode((output/'expected_failed_input/run_metadata.json').read_bytes())
    check('hash rejection decoded no CSV or JSON', badmeta['counters']['measurement_csv_decoded'] == 0 and
          badmeta['counters']['measurement_json_decoded'] == 0)
    (synth/m.POINT_PATH).write_bytes(original)
    rejects('existing successful output preserved', lambda: m.run('measure', synth, manifest_path, result))
    result_rows = (result/'rows.json').read_bytes()
    (result/'rows.json').write_bytes(result_rows+b' ')
    rejects('tampered measurement seal rejected before score read', lambda: m.run('associate', synth, manifest_path,
            output/'expected_failed_tampered_associate', result))
    (result/'rows.json').write_bytes(result_rows)
    check('successful artificial source snapshot restored', m.sha((result/'source_snapshot.py').read_bytes()) == source_sha)
    # Missing x excludes the same row for every ordinary comparator.
    joined = m.join_labels(rows, details, score_rows)
    for i, row in enumerate(joined):
        row['y_pose_minus_geometry_pp'] = float(i % 4)
        for k in m.METRICS:
            row[k] = float(i % 4)
    joined[0]['disagreement_g_minus_p'] = None
    corr = m.associations(joined)
    first_block = [r for r in corr if r['stage'] == 'S7' and r['block'] == 0]
    check('all four metrics share query domain', len(first_block) == 4 and
          all(r['n_usable'] == 3 and r['n_missing'] == 1 for r in first_block) and
          all(r['usable_keys'] == first_block[0]['usable_keys'] for r in first_block))
    receipt = dict(status='PASS', started_utc=started, completed_utc=m.now(), n_checks=len(checks), checks=checks,
                   source_sha256=source_sha, checker_sha256=m.sha(Path(__file__).read_bytes()),
                   real_npz_reads=0, real_feature_reads=0, real_label_reads=0,
                   explanation='All data below synthetic_root were constructed from literals; expected failure directories retained.')
    m.save(output/'receipt.json', receipt)
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    main(parser.parse_args().output.absolute())
