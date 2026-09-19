from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from tum_rgbd import (CameraIntrinsics, DEFAULT_INTRINSICS, PoseTrajectory,
                      RGBDMatch, TimestampEntry, associate_rgb_depth,
                      backproject_depth, load_sparse_frame, optical_to_vmem_c2w,
                      read_timestamp_file, read_trajectory)


class TumRGBDTests(unittest.TestCase):
    def test_text_parse_comments_sorting_and_xyzw_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "rgb.txt").write_text("# images\n2 rgb/b.png\n1 rgb/a.png # note\n")
            entries = read_timestamp_file(root / "rgb.txt")
            self.assertEqual([entry.timestamp for entry in entries], [1., 2.])
            (root / "gt.txt").write_text("# poses\n2 1 2 3 0 0 1 0\n1 0 0 0 0 0 0 1\n")
            gt = read_trajectory(root / "gt.txt")
            np.testing.assert_allclose(gt.pose_at(1), np.eye(4))
            np.testing.assert_allclose(gt.pose_at(2)[:3, :3], np.diag([-1, -1, 1]), atol=1e-14)
            np.testing.assert_allclose(gt.pose_at(2)[:3, 3], [1, 2, 3])

    def test_duplicate_and_nonfinite_timestamps_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rgb.txt"
            for text in ("1 a\n1 b\n", "nan a\n"):
                path.write_text(text)
                with self.assertRaises(ValueError):
                    read_timestamp_file(path)

    def test_association_uses_smallest_difference_before_chronology(self):
        rgb = [TimestampEntry(0., "r0"), TimestampEntry(.016, "r1")]
        depth = [TimestampEntry(.011, "d0")]
        matches = associate_rgb_depth(rgb, depth)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].rgb.path, "r1")
        self.assertAlmostEqual(matches[0].offset_seconds, .005)

    def test_association_is_unique_and_boundary_is_strict(self):
        rgb = [TimestampEntry(0., "r0"), TimestampEntry(.01, "r1")]
        depth = [TimestampEntry(.009, "d0"), TimestampEntry(.019, "d1")]
        matches = associate_rgb_depth(rgb, depth)
        self.assertEqual([(m.rgb.path, m.depth.path) for m in matches], [("r0", "d1"), ("r1", "d0")])
        self.assertEqual(len({m.depth.path for m in matches}), 2)
        self.assertEqual(associate_rgb_depth([rgb[0]], [TimestampEntry(.02, "boundary")]), [])
        self.assertEqual(associate_rgb_depth([], depth), [])

    def test_slerp_translation_and_exact_support_endpoints(self):
        gt = PoseTrajectory(np.array([10., 12.]), np.array([[0, 0, 0], [2, 4, 6]]),
                            np.array([[0, 0, 0, 1], [0, 0, 1, 0]]))
        mid = gt.interpolate(11.)
        np.testing.assert_allclose(mid.c2w[:3, 3], [1, 2, 3])
        np.testing.assert_allclose(mid.c2w[:3, :3] @ [1, 0, 0], [0, 1, 0], atol=1e-14)
        self.assertEqual((mid.lower_timestamp, mid.upper_timestamp, mid.alpha), (10., 12., .5))
        self.assertEqual(gt.interpolate(10.).gap_seconds, 0.)
        self.assertEqual(gt.interpolate(12.).gap_seconds, 0.)
        for t in (9.99999, 12.00001, float("nan")):
            with self.assertRaises(ValueError):
                gt.pose_at(t)
        with self.assertRaises(ValueError):
            gt.pose_at(11., max_gap_seconds=1.)

    def test_quaternion_sign_and_large_epoch_do_not_change_interpolation(self):
        gt = PoseTrajectory(np.array([1_300_000_000., 1_300_000_002.]),
                            np.array([[0, 0, 0], [2, 0, 0]]),
                            np.array([[0, 0, 0, 1], [0, 0, 0, -1]]))
        pose = gt.pose_at(1_300_000_001.)
        np.testing.assert_allclose(pose[:3, :3], np.eye(3))
        np.testing.assert_allclose(pose[:3, 3], [1, 0, 0])

    def test_depth_is_optical_z_without_second_freiburg_scale(self):
        intrinsics = CameraIntrinsics(fx=2, fy=2, cx=1, cy=0, width=3, height=2)
        raw = np.array([[0, 5000, 10000], [5000, 0, 5000]], dtype=np.uint16)
        uv, xyz = backproject_depth(raw, intrinsics)
        np.testing.assert_array_equal(uv, [[1, 0], [2, 0], [0, 1], [2, 1]])
        np.testing.assert_allclose(xyz, [[0, 0, 1], [1, 0, 2], [-.5, .5, 1], [.5, .5, 1]])
        self.assertEqual(xyz[0, 2], 1.)
        uv_stride, _ = backproject_depth(raw, intrinsics, stride=2)
        np.testing.assert_array_equal(uv_stride, [[2, 0]])
        np.testing.assert_array_equal(DEFAULT_INTRINSICS.K,
                                      [[525, 0, 319.5], [0, 525, 239.5], [0, 0, 1]])

    def test_load_frame_uses_depth_time_and_preserves_pixel_color(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rgb = np.arange(12, dtype=np.uint8).reshape(2, 2, 3)
            raw = np.array([[5000, 0], [10000, 5000]], dtype=np.uint16)
            Image.fromarray(rgb).save(root / "rgb.png")
            Image.fromarray(raw).save(root / "depth.png")
            gt = PoseTrajectory(np.array([0., .02]), np.array([[0, 0, 0], [2, 0, 0]]),
                                np.array([[0, 0, 0, 1], [0, 0, 0, 1]]))
            match = RGBDMatch(TimestampEntry(0., "rgb.png"), TimestampEntry(.01, "depth.png"))
            intrinsics = CameraIntrinsics(fx=2, fy=2, cx=.5, cy=.5, width=2, height=2)
            frame = load_sparse_frame(root, match, gt, stride=1, intrinsics=intrinsics)
            self.assertEqual(frame.pose.timestamp, .01)
            self.assertEqual(frame.valid_depth_fraction, .75)
            np.testing.assert_allclose(frame.points_world, frame.points_camera + [1, 0, 0])
            np.testing.assert_array_equal(frame.colors_rgb, rgb[[0, 1, 1], [0, 0, 1]])
            np.testing.assert_array_equal(frame.depth_m, [[1, 0], [2, 1]])
            frame_rgb_time = load_sparse_frame(root, match, gt, stride=1,
                                               intrinsics=intrinsics, pose_time="rgb")
            np.testing.assert_allclose(frame_rgb_time.points_world, frame_rgb_time.points_camera)

    def test_optical_to_vmem_changes_axes_but_not_camera_center(self):
        optical = np.eye(4)
        optical[:3, 3] = [1, 2, 3]
        vmem = optical_to_vmem_c2w(optical)
        np.testing.assert_allclose(vmem[:3, 3], optical[:3, 3])
        np.testing.assert_allclose(vmem @ [1, -2, -3, 1], optical @ [1, 2, 3, 1])


if __name__ == "__main__":
    unittest.main()
