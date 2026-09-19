#!/usr/bin/env python3
"""Independent hand-calculated renderer diagnosis; artificial arrays only.

This imports classify/compose/diagnose from root's runner. It never calls main,
layer, load, or np.load; no real experiment input is opened.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
import traceback
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runner', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=False)
    receipt = dict(started_utc=datetime.now(timezone.utc).isoformat(),
                   type='artificial software verification; no real data reads',
                   runner_sha256=sha(args.runner), checker_sha256=sha(__file__),
                   experiment_rgb_reads=0, experiment_npz_reads=0,
                   sensor_depth_reads=0, model_calls=0, checks=[])
    try:
        spec = importlib.util.spec_from_file_location('s16_under_review', args.runner)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        # Four identical artificial targets; each has three valid GT pixels.
        old_1 = np.array([[2., 2., 2.], [2., 2., 1.], [0., 0., 0.], [0., 0., 0.]])
        new_1 = np.array([[1., 1., .7], [.7, .7, 1.], [0., 0., 0.], [0., 0., 0.]])
        old = np.repeat(old_1[:, None, None, :], 4, axis=1)
        new = np.repeat(new_1[:, None, None, :], 4, axis=1)
        ids = np.full(old.shape, -1, dtype=np.int64)
        for source in range(2):
            ids[source, :, 0, :] = source * 224 * 224 + np.arange(3)
        gt = np.ones((4, 1, 3))
        z_base, id_base = module.compose(old, ids)
        assert np.array_equal(z_base, np.tile([[[2., 2., 1.]]], (4, 1, 1)))
        assert np.array_equal(id_base, np.tile([[[0, 1, 224 * 224 + 2]]], (4, 1, 1)))
        classes = module.classify(old, new, ids, ids)
        assert classes['fixed_candidates_depth_competition'].all()
        assert not classes['source_pixel_routing'].any()
        assert not classes['coverage_change'].any()
        report, maps = module.diagnose(old, new, ids, ids, 1., gt)
        expected_counts = {0: 1, 1: 2, 2: 1, 4: 1, 8: 1, 15: 0, 14: 1, 13: 2, 11: 0, 7: 0}
        for row in report['subsets']:
            assert row['correct_counts'] == [expected_counts[row['subset']]] * 4
        assert report['interaction_correct_counts'] == [-2] * 4
        assert np.allclose(report['interaction_delta1'], [-2. / 3] * 4, rtol=0, atol=1e-15)
        assert report['frozen_owner_exact_zero'] is True
        assert np.array_equal(maps['interaction'], np.tile([[[-1, -1, 0]]], (4, 1, 1)))
        marginal_a = report['marginals'][0]
        assert marginal_a['single_correct_delta'] == [1] * 4
        assert marginal_a['joint_marginal_correct_delta'] == [-1] * 4
        assert marginal_a['target_sign_reversals'] == [True] * 4
        assert marginal_a['mean_sign_reversal'] is True
        assert marginal_a['solo_old_correct_counts'] == [0] * 4
        assert marginal_a['solo_new_correct_counts'] == [2] * 4
        assert marginal_a['solo_correct_delta'] == [2] * 4
        assert np.isclose(marginal_a['solo_mean_delta1'], 2. / 3, rtol=0, atol=1e-15)
        # Direct frozen-owner calculation independent of diagnose's bool.
        baseline_owner = np.tile([[[0, 0, 1]]], (4, 1, 1))
        frozen_counts = {}
        for subset in module.SUBSETS:
            selected = old.copy()
            for source in range(4):
                if subset & (1 << source):
                    selected[source] = new[source]
            fz, _ = module.compose(selected, ids, baseline_owner)
            # Values are positive in this fixture; criterion is evaluated here,
            # independently of module.correct.
            hits = np.maximum(fz / gt, gt / fz) < 1.25
            frozen_counts[subset] = hits.sum(axis=(1, 2)).tolist()
        assert frozen_counts[0] == [1] * 4
        assert frozen_counts[1] == [3] * 4
        assert frozen_counts[15] == [3] * 4
        fj = np.array(frozen_counts[15]) - np.array(frozen_counts[0])
        for source in range(4):
            fj -= np.array(frozen_counts[1 << source]) - np.array(frozen_counts[0])
        assert not fj.any()
        for row in report['frozen_owner_subsets']:
            assert row['correct_counts'] == frozen_counts[row['subset']]
            assert np.isclose(row['equal_four_frame_delta1'],
                              frozen_counts[row['subset']][0] / 3, rtol=0, atol=1e-15)
        for row in report['subsets']:
            assert np.isclose(row['equal_four_frame_delta1'],
                              expected_counts[row['subset']] / 3, rtol=0, atol=1e-15)
        receipt['checks'].append('Hand calculation: J=-2 per target, I=-2/3, source A marginal +1 -> -1, frozen-owner J=0')

        routed = ids.copy()
        routed[0, :, 0, 1] = 42  # validity unchanged; source-pixel identity changes
        mixed_new = new.copy()
        mixed_new[2, :, 0, 2] = .9
        routed[2, :, 0, 2] = 2 * 224 * 224 + 2
        three = module.classify(old, mixed_new, ids, routed)
        for key, position in [('fixed_candidates_depth_competition', 0),
                              ('source_pixel_routing', 1), ('coverage_change', 2)]:
            expected = np.zeros((4, 1, 3), bool)
            expected[:, 0, position] = True
            assert np.array_equal(three[key], expected)
        mixed_report, _ = module.diagnose(old, mixed_new, ids, routed, 1., gt)
        assert np.array_equal(sum(np.array(row['interaction_correct_count_contribution'])
                                  for row in mixed_report['components']),
                              mixed_report['interaction_correct_counts'])
        receipt['checks'].append('Three exclusive GT-independent classes partition pixels; integer contributions add exactly')

        invalid_new = new.copy()
        invalid_ids = ids.copy()
        invalid_new[0, :, 0, 0] = 0
        invalid_ids[0, :, 0, 0] = -1
        fz, fi = module.compose(invalid_new, invalid_ids, baseline_owner)
        assert np.all(fz[:, 0, 0] == 0) and np.all(fi[:, 0, 0] == -1)
        assert np.all(module.compose(invalid_new, invalid_ids)[0][:, 0, 0] == .7)
        invalid_report, _ = module.diagnose(old, invalid_new, ids, invalid_ids, 1., gt)
        assert invalid_report['frozen_owner_exact_zero'] is True
        receipt['checks'].append('Frozen owner becoming invalid stays missing despite an available other source; exact zero interaction remains')

        noop_report, _ = module.diagnose(old, old, ids, ids, 1., gt)
        assert noop_report['interaction_correct_counts'] == [0] * 4
        assert not any(x['mean_sign_reversal'] for x in noop_report['marginals'])
        receipt['checks'].append('No-op policy has zero interaction and no strict sign reversals')
        (out / 'expected_and_actual.json').write_text(json.dumps(dict(
            fixture_old=old_1.tolist(), fixture_new=new_1.tolist(), gt=[1, 1, 1],
            expected_correct_count_per_target=expected_counts,
            expected_interaction_count_per_target=-2,
            expected_interaction_delta1=-2 / 3,
            frozen_correct_counts=frozen_counts, actual=report), indent=2) + '\n')
        receipt['status'] = 'PASS'
    except BaseException as exc:
        receipt.update(status='FAIL', error=repr(exc), traceback=traceback.format_exc())
    receipt['completed_utc'] = datetime.now(timezone.utc).isoformat()
    receipt['runner_sha256_after'] = sha(args.runner)
    assert receipt['runner_sha256'] == receipt['runner_sha256_after'], 'runner changed during check'
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))
    return int(receipt['status'] != 'PASS')


if __name__ == '__main__':
    raise SystemExit(main())
