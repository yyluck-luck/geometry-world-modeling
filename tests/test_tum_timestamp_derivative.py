"""Timestamp-only derivative fixtures; no real TUM data, images or pose math."""
import contextlib
import io
import json
import math
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import prepare_tum_timestamp_derivative as derivative


def gt(t, ending=b'\n', pose=b'not a parsed pose value at all'):
    # Seven deliberately nonnumeric pose tokens. Only time may be parsed.
    assert len(pose.split()) == 7
    return format(t, '.17g').encode() + b' ' + pose + ending


class TestTimestampDerivative(unittest.TestCase):
    def test_all_duplicate_groups_union_and_original_line_bytes(self):
        lines = [b'# untouched comment\r\n', gt(-.2, b'\r\n'), b'\r\n', gt(0.),
                 gt(0., pose=b'other pose tokens are also never parsed'), gt(.04), gt(.04), gt(.09), gt(.2)]
        payload = b''.join(lines)
        result, report = derivative.derive_gt(payload)
        self.assertEqual([x['timestamp'] for x in report['duplicate_groups']], [0., .04])
        self.assertEqual(result, lines[0]+lines[1]+lines[2]+lines[-1])
        self.assertEqual([x['original_line'] for x in report['excluded_rows']], [4, 5, 6, 7, 8])
        self.assertTrue(report['validation']['all_passed'])
        self.assertTrue(all(x['gap_seconds'] > .1 for x in report['barriers']))
        self.assertEqual([x['original_line'] for x in report['retained_line_mapping']], [1, 2, 3, 9])
        self.assertEqual([x['derived_line'] for x in report['retained_line_mapping']], [1, 2, 3, 4])
        self.assertEqual(report['retained_line_mapping'][0]['raw_line_sha256'], derivative.byte_sha(lines[0]))

    def test_closed_binary64_membership_does_not_use_isclose(self):
        left = math.nextafter(-.051, -math.inf)
        right = math.nextafter(.051, math.inf)
        times = [left, -.051, 0., 0., .051, right]
        result, report = derivative.derive_gt(b''.join(gt(t) for t in times))
        self.assertEqual([x['timestamp'] for x in report['retained_gt_rows']], [left, right])
        self.assertEqual(result, gt(left)+gt(right))
        self.assertTrue(report['validation']['all_passed'])
        self.assertGreater(report['barriers'][0]['gap_seconds'], .100)

    def test_trajectory_boundary_and_global_scan(self):
        result, report = derivative.derive_gt(gt(0.)+gt(1.)+gt(100.)+gt(100.))
        self.assertEqual(result, gt(0.)+gt(1.))
        self.assertEqual(report['barriers'][0]['boundary'], 'right_trajectory_boundary')
        self.assertTrue(report['validation']['all_passed'])
        self.assertEqual(report['duplicate_groups'][0]['timestamp'], 100.)

    def test_bad_structure_nonfinite_and_output_order_fail(self):
        for payload in (b'nan a b c d e f g\n', b'inf a b c d e f g\n', b'0 only two\n'):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                derivative.derive_gt(payload)
        _, unsorted = derivative.derive_gt(gt(1.)+gt(0.))
        self.assertFalse(unsorted['validation']['all_passed'])
        self.assertFalse(unsorted['validation']['timestamps_strictly_increasing_and_unique'])
        _, empty = derivative.derive_gt(gt(0.)+gt(0.))
        self.assertFalse(empty['validation']['all_passed'])
        self.assertFalse(empty['validation']['nonempty_gt'])

    def fixture(self, base, payload):
        source = base / 'original' / derivative.DATASET
        source.mkdir(parents=True)
        (source / 'groundtruth.txt').write_bytes(payload)
        (source / 'rgb').mkdir(); (source / 'depth').mkdir(); (source / 'empty').mkdir()
        # Intentionally not image bytes: the entire real preparation must treat them as opaque.
        (source / 'rgb/test.png').write_bytes(b'RGB fixture bytes, never image decoded')
        (source / 'depth/test.png').write_bytes(b'Depth fixture bytes, never decoded')
        (source / 'rgb.txt').write_bytes(b'0 rgb/test.png\n')
        (source / 'depth.txt').write_bytes(b'0 depth/test.png\n')
        protocol = base / 'protocol.md'; protocol.write_bytes(b'Frozen synthetic protocol, not a real experiment')
        freeze = base / 'freeze.json'
        freeze.write_text(json.dumps(dict(protocol_sha256=derivative.sha(protocol), frozen_utc='2026-01-01T00:00:00+00:00',
            original_gt_sha256=derivative.sha(source / 'groundtruth.txt'),
            source_sha256={'scripts/prepare_tum_timestamp_derivative.py': derivative.sha(ROOT / 'scripts/prepare_tum_timestamp_derivative.py')})))
        return SimpleNamespace(source=source, output=base / 'derived', protocol=protocol, design_freeze=freeze)

    def test_full_synthetic_tree_independent_copy_and_source_unchanged(self):
        with tempfile.TemporaryDirectory() as temp:
            args = self.fixture(Path(temp), gt(-.2)+gt(0.)+gt(0.)+gt(.2))
            before = derivative.tree_inventory(args.source)
            with contextlib.redirect_stdout(io.StringIO()): derivative.run(args)
            report = json.loads((args.output / 'derivation_metadata.json').read_text())
            self.assertEqual(report['status'], 'completed')
            self.assertEqual(report['non_gt_copies_verified'], 4)
            self.assertTrue(report['source_tree_unchanged'])
            self.assertEqual(before, derivative.tree_inventory(args.source))
            root = args.output / derivative.DATASET
            self.assertEqual((root / 'groundtruth.txt').read_bytes(), gt(-.2)+gt(.2))
            for name in ('rgb/test.png', 'depth/test.png', 'rgb.txt', 'depth.txt'):
                self.assertEqual((root / name).read_bytes(), (args.source / name).read_bytes())
                self.assertNotEqual((root / name).stat().st_ino, (args.source / name).stat().st_ino)
            previous = (args.output / 'derivation_metadata.json').read_bytes()
            with self.assertRaisesRegex(ValueError, 'fresh'): derivative.run(args)
            self.assertEqual((args.output / 'derivation_metadata.json').read_bytes(), previous)

    def test_symlink_and_malformed_gt_keep_failed_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp); args = self.fixture(base, gt(0.))
            (args.source / 'rgb/link').symlink_to(args.source / 'rgb/test.png')
            with self.assertRaisesRegex(ValueError, 'Symbolic link'): derivative.run(args)
            report = json.loads((args.output / 'derivation_metadata.json').read_text())
            self.assertEqual(report['status'], 'failed')
            self.assertFalse(report['images_decoded'])
            self.assertFalse(report['gt_pose_values_parsed'])
        with tempfile.TemporaryDirectory() as temp:
            args = self.fixture(Path(temp), b'0 too few\n')
            with self.assertRaisesRegex(ValueError, '8 columns'): derivative.run(args)
            report = json.loads((args.output / 'derivation_metadata.json').read_text())
            self.assertEqual(report['status'], 'failed')
            self.assertEqual(report['phase_failed'], 'timestamp_only_derivation')
            self.assertIn('尚未完成', (args.output / 'README.md').read_text())


if __name__ == '__main__': unittest.main()
