import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import score_candidates as s


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.K = np.array([[100., 0, 320.], [0, 100., 240.], [0, 0, 1.]])
        self.I = np.eye(4)
        self.grid = (np.array([320, 324]), np.array([240, 240]), np.array([0, 1]), np.array([0, 0]))

    def test_translation_has_analytic_parallax(self):
        pose = self.I.copy()
        pose[0, 3] = 1
        uv, z, inside = s.project(np.array([320]), np.array([240]), np.array([2.]), self.I, pose, self.K)
        np.testing.assert_allclose(uv, [[270, 240]])
        np.testing.assert_allclose(z, [2])
        self.assertTrue(inside.all())

    def test_identity_perfect_depth_has_zero_loss(self):
        uv = np.stack(self.grid[:2], axis=-1)
        loss, invalid = s.tuple_losses(np.array([[2., 2.]]), np.array([0, 1]), uv, self.I, self.I, self.K, self.grid)
        np.testing.assert_allclose(loss, 0)
        self.assertFalse(invalid.any())

    def test_invalid_and_behind_keep_denominator(self):
        uv = np.stack(self.grid[:2], axis=-1)
        loss, invalid = s.tuple_losses(np.array([[2., np.nan], [-1., 0.]]), np.array([0, 1]), uv, self.I, self.I, self.K, self.grid)
        np.testing.assert_allclose(loss, [[0, 1], [1, 1]])
        self.assertEqual(loss[0].mean(), .5)
        self.assertEqual(invalid.sum(), 3)

    def test_out_of_image_is_maximum_penalty(self):
        pose = self.I.copy()
        pose[0, 3] = 10
        uv = np.stack(self.grid[:2], axis=-1)
        loss, _ = s.tuple_losses(np.ones((1, 2)), np.array([0, 1]), uv, self.I, pose, self.K, self.grid)
        np.testing.assert_allclose(loss, 1)

    def test_sensor_support_occlusion_and_boundary(self):
        source = np.ones((480, 640)) * 2
        target = source.copy()
        target[240, 320] = 1  # Occluding measured surface; rejects this correspondence.
        ids, _ = s.fixed_support(source, target, self.I, self.I, self.K, self.grid, False)
        np.testing.assert_array_equal(ids, [1])
        target[240, 325] = 0  # Neighbour missing: rejects remaining point only in primary.
        ids, _ = s.fixed_support(source, target, self.I, self.I, self.K, self.grid, True)
        self.assertEqual(len(ids), 0)
        ids, _ = s.fixed_support(source, target, self.I, self.I, self.K, self.grid, False)
        np.testing.assert_array_equal(ids, [1])

    def test_oracle_requires_one_candidate_for_whole_window(self):
        out = s.oracle_summary(np.array([[0., 1.], [1., 0.]]), np.array([0, 1]))
        self.assertEqual(out['complete_oracle'], .5)
        self.assertEqual(out['per_tuple_oracle'], 0)
        self.assertEqual(out['per_target_oracle'], 0)
        self.assertEqual(out['complete_oracle_index'], 0)

    def test_scale_only_candidates_collapse_when_normalized(self):
        depths = np.array([[[1., 2., 4.]], [[2., 4., 8.]], [[.5, 1., 2.]]])
        out = s.controls(depths)
        np.testing.assert_allclose(out['scales'], [1, 2, .5])
        np.testing.assert_allclose(out['normalized_family'], np.repeat(depths[:1], 3, axis=0))
        np.testing.assert_allclose(out['scale_family'], depths)
        np.testing.assert_allclose(out['fusion'], depths[0])
        self.assertEqual(out['medoid_index'], 0)

    def test_fusion_does_not_make_all_invalid_pixels_valid(self):
        depths = np.array([[[1., np.nan]], [[2., -1.]], [[4., 0.]]])
        out = s.controls(depths)
        self.assertTrue(np.isnan(out['fusion'][0, 1]))
        self.assertEqual(out['fusion'][0, 0], 2.)

    def test_sampling_maps_native_center(self):
        u, v, x, y = s.sampling_grid()
        index = np.flatnonzero((u == 320) & (v == 240))[0]
        self.assertEqual((x[index], y[index]), (256, 192))
        self.assertTrue(((u % 4 == 0) & (v % 4 == 0)).all())

    def test_seal_rejects_missing_and_changed_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / 'manifest.json'
            manifest.write_text(json.dumps({'windows': [{'window_id': 'w'}], 'candidates': [{'candidate_id': 'c0'}]}))
            protocol = root / 'protocol.md'
            protocol.write_text('fixed')
            seal = root / 'seal.json'
            record = {'manifest_sha256': s.sha_file(manifest), 'protocol_sha256': s.sha_file(protocol), 'records': []}
            seal.write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, 'Incomplete seal'):
                s.verify_seal(seal, root, manifest, protocol)
            npz = root / 'w__c0.npz'
            npz.write_bytes(b'original')
            receipt = root / 'w__c0.json'
            receipt.write_bytes(b'{}')
            record['records'] = [{'npz': npz.name, 'npz_sha256': s.sha_file(npz), 'receipt': receipt.name, 'receipt_sha256': s.sha_file(receipt)}]
            seal.write_text(json.dumps(record))
            s.verify_seal(seal, root, manifest, protocol)
            npz.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'Sealed output changed'):
                s.verify_seal(seal, root, manifest, protocol)

    def test_gate_stops_on_nuisance_failure(self):
        scores = dict(headroom_vs_c0=.2, gain_vs_better_single_control=.08,
                      gain_vs_scale_oracle=.01, normalized_headroom_vs_c0=.15,
                      gain_vs_best_fixed_order=.08)
        result, reasons = s.verdict(scores, {'a': scores, 'b': scores})
        self.assertEqual(result, 'STOP_TESTED_FAMILY')
        self.assertEqual(reasons, ['gain_over_scale_oracle_below_5_percent'])

    def test_gate_stops_when_one_fixed_order_explains_oracle(self):
        scores = dict(headroom_vs_c0=.2, gain_vs_better_single_control=.08,
                      gain_vs_scale_oracle=.08, normalized_headroom_vs_c0=.15,
                      gain_vs_best_fixed_order=0.)
        result, reasons = s.verdict(scores, {'a': scores, 'b': scores})
        self.assertEqual(result, 'STOP_TESTED_FAMILY')
        self.assertEqual(reasons, ['gain_over_best_fixed_order_below_5_percent'])

    def test_freeze_rejects_changed_scorer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            code = root / 'score_candidates.py'
            code.write_bytes(Path(s.__file__).read_bytes())
            freeze = root / 'FREEZE.json'
            freeze.write_text(json.dumps({'files': {'score_candidates.py': s.sha_file(code)}}))
            s.validate_freeze(freeze)
            code.write_text('changed')
            with self.assertRaisesRegex(ValueError, 'Frozen file changed'):
                s.validate_freeze(freeze)

    def test_runtime_rejects_wrong_weights_and_predictor(self):
        freeze = {'files': {'generate_candidates.py': 'a', 'kps.py': 'b'}}
        pins = {'files': [{'path': '/model.pth', 'sha256': 'weight'}]}
        receipt = {'code_hashes': {'generate_candidates.py': 'a', 'kps.py': 'b'},
                   'weight_sha256': 'wrong'}
        with self.assertRaisesRegex(ValueError, 'Unpinned model weights'):
            s.validate_runtime(receipt, freeze, pins)
        receipt['code_hashes']['generate_candidates.py'] = 'wrong'
        with self.assertRaisesRegex(ValueError, 'Unfrozen predictor code'):
            s.validate_runtime(receipt, freeze, pins)


if __name__ == '__main__':
    unittest.main()
