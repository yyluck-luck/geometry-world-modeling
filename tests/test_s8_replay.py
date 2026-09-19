"""S8 orchestration boundary checks, using tiny temporary bytes only."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import run_s8_replay as s8


class TestS8ReplayBoundaries(unittest.TestCase):
    def test_protocol_does_not_allow_retuning_or_double_depth_correction(self):
        def fence(value):
            return '```s8-replay-json\n' + json.dumps(value) + '\n```\n'
        contract = deepcopy(s8.REPLAY_CONTRACT)
        self.assertEqual(s8.parse_replay_contract(fence(contract)), contract)
        for key, value in (('extra_depth_scale', 1.031), ('width', 320),
                           ('splits', ['development', 'test', 'test']),
                           ('gt_pose_timestamp', 'depth'), ('measurement_after_all_selections_sealed', False)):
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, key):
                s8.parse_replay_contract(fence(dict(contract, **{key: value})))
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            s8.parse_replay_contract(fence(contract) * 2)

    def test_seal_checks_root_normalization_and_every_case_file(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            (out / 'normalization.npz').write_bytes(b'normalized prediction')
            (out / 'case').mkdir()
            (out / 'case/events.json').write_bytes(b'events')
            meta = dict(sealed_root_files={'normalization.npz': s8.sha(out / 'normalization.npz')},
                cases=[dict(directory='case', sealed_files={'events.json': s8.sha(out / 'case/events.json')})])
            s8.assert_sealed(out, meta)
            (out / 'case/events.json').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'Sealed prediction changed'):
                s8.assert_sealed(out, meta)
            (out / 'case/events.json').write_bytes(b'events')
            (out / 'normalization.npz').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'Sealed normalized input changed'):
                s8.assert_sealed(out, meta)

    def test_external_archive_names_are_safe_and_noncolliding(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            paths = [root / name / 'groundtruth.txt' for name in ('one', 'two')]
            for path in paths:
                path.parent.mkdir()
                path.write_bytes(b'groundtruth')
            names = [s8.archive_name(path) for path in paths]
            self.assertNotEqual(*names)
            self.assertTrue(all(not Path(name).is_absolute() and '..' not in Path(name).parts for name in names))
            self.assertEqual(s8.archive_name(ROOT / 'scripts/run_s8_replay.py'), 'scripts/run_s8_replay.py')

    def test_preflight_failure_is_preserved_without_measurement_access(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'failed_attempt'
            args = SimpleNamespace(output=out)
            with patch.object(s8, 'validate_freeze', side_effect=ValueError('frozen source changed')), \
                 patch.object(s8, 'read_trajectory', side_effect=AssertionError('GT decoded')) as gt, \
                 patch.object(s8.Image, 'open', side_effect=AssertionError('image decoded')) as image:
                with self.assertRaisesRegex(ValueError, 'frozen source changed'):
                    s8.run(args)
            metadata = json.loads((out / 'run_metadata.json').read_text())
            self.assertEqual(metadata['status'], 'failed')
            self.assertEqual(metadata['phase_failed'], 'preflight')
            self.assertIn('frozen source changed', metadata['traceback'])
            self.assertEqual(gt.call_count, 0)
            self.assertEqual(image.call_count, 0)
            original = (out / 'run_metadata.json').read_bytes()
            with self.assertRaisesRegex(ValueError, 'fresh output'):
                s8.run(args)
            self.assertEqual((out / 'run_metadata.json').read_bytes(), original)

    def test_empty_common_pixels_remain_missing_not_perfect_scores(self):
        target = np.ones((2, 2))
        prediction = np.full((2, 2), np.nan)
        result = s8.residual_stats(prediction, target, np.zeros((2, 2), dtype=bool))
        self.assertEqual(result['n'], 0)
        self.assertIsNone(result['mae_mm'])
        self.assertIsNone(result['median_abs_mm'])
        self.assertIsNone(result['within_30mm'])
        self.assertNotIn('NaN', json.dumps(result, allow_nan=False))


if __name__ == '__main__':
    unittest.main()
