"""Analytic geometry/occlusion checks for measured RGB-D metrics."""
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from rgbd_metrics import project_points, depth_consistency, measurement_support, valid_depth_interior


def frame(depth=None, pose=None):
    return dict(depth=np.full((9, 9), 2.) if depth is None else depth,
                c2w_optical=np.eye(4) if pose is None else pose,
                intrinsics=np.array([[4., 0, 4], [0, 4., 4], [0, 0, 1.]]))


def camera_point(u, v, z):
    return [(u - 4) * z / 4, (v - 4) * z / 4, z]


class RGBDMetricsTests(unittest.TestCase):
    def test_optical_projection_with_rotation_and_translation(self):
        pose = np.array([[0., -1, 0, 1], [1., 0, 0, 2], [0., 0, 1, 3], [0., 0, 0, 1]])
        camera_points = np.array([[0., 0, 2], [2., 1, 2], [0., 0, -1], [100., 0, 1]])
        world = camera_points @ pose[:3, :3].T + pose[:3, 3]
        uv, z, bounds = project_points(world, pose, (2, 2, 4, 3), width=9, height=7)
        np.testing.assert_allclose(uv[:2], [[4, 3], [6, 4]])
        np.testing.assert_allclose(z, camera_points[:, 2])
        np.testing.assert_array_equal(bounds, [True, True, False, False])
        self.assertTrue(np.isnan(uv[2]).all())

    def test_zbuffer_grid_uses_zero_origin_and_nearest_surface(self):
        # Both projections round to grid (1, 1) at original pixel (4, 4).
        points = np.array([camera_point(3.1, 4.7, 2), camera_point(4.1, 3.3, 1), [0, 0, -2]])
        result = depth_consistency(points, frame(), stride=4)
        self.assertEqual(result["pred_depth"].shape, (3, 3))
        self.assertEqual(result["pred_mask"].sum(), 1)
        self.assertEqual(result["pred_depth"][1, 1], 1)
        self.assertEqual(result["target_depth"][1, 1], 2)
        self.assertTrue(result["common_mask"][1, 1])
        # A full metre of prediction error remains in the mask.
        self.assertEqual(abs(result["pred_depth"][1, 1] - result["target_depth"][1, 1]), 1)

    def test_projection_to_final_pixel_cannot_overflow_rounded_grid(self):
        result = depth_consistency(np.array([camera_point(8.9, 4, 2)]), frame(), stride=1)
        self.assertFalse(result["pred_mask"].any())

    def test_missing_predictions_remain_missing_not_zero_error(self):
        result = depth_consistency(np.empty((0, 3)), frame(), stride=2)
        self.assertFalse(result["pred_mask"].any())
        self.assertFalse(result["common_mask"].any())
        self.assertTrue(np.isnan(result["pred_depth"]).all())
        self.assertEqual(result["target_valid"].sum(), 9)

    def test_invalid_and_depth_discontinuities_are_masked_natively(self):
        depth = np.full((9, 9), 2.)
        depth[4, 4] = 0
        depth[:, 7:] = 3
        valid = valid_depth_interior(depth)
        for v, u in [(4, 4), (3, 4), (5, 4), (4, 3), (4, 5), (2, 6), (2, 7), (0, 3)]:
            self.assertFalse(valid[v, u])
        self.assertTrue(valid[2, 2])

    def test_identical_plane_has_complete_measurement_support(self):
        masks, valid = measurement_support([frame()], frame(), stride=2)
        self.assertEqual(masks.shape, (1, 5, 5))
        np.testing.assert_array_equal(masks[0], valid)
        self.assertEqual(valid.sum(), 9)

    def test_history_occluder_and_far_surface_do_not_support_target(self):
        occluded = np.full((9, 9), 2.)
        occluded[:, :5] = 1.
        masks, valid = measurement_support([frame(occluded), frame(np.full((9, 9), 3.))], frame(), stride=2)
        self.assertEqual(valid.sum(), 9)
        # Only source pixel u=6 remains both unoccluded and off the depth edge.
        self.assertEqual(masks[0].sum(), 3)
        self.assertTrue(masks[0][2, 3])
        self.assertFalse(masks[0][2, 1])
        self.assertFalse(masks[1].any())

    def test_support_uses_history_camera_z_and_its_field_of_view(self):
        pose = np.eye(4)
        pose[2, 3] = 1.
        masks, valid = measurement_support([frame(np.ones((9, 9)), pose)], frame(), stride=2)
        # Target plane z=2 is at source camera z=1, with a narrower field of view.
        self.assertEqual(valid.sum(), 9)
        self.assertEqual(masks.sum(), 1)
        self.assertTrue(masks[0, 2, 2])

    def test_empty_history_and_invalid_target_have_explicit_masks(self):
        target = frame(np.zeros((9, 9)))
        masks, valid = measurement_support([], target, stride=4)
        self.assertEqual(masks.shape, (0, 3, 3))
        self.assertFalse(valid.any())
        masks, valid = measurement_support([frame()], target, stride=4)
        self.assertFalse(masks.any())

    def test_equivalent_array_api_and_no_input_mutation(self):
        target = frame()
        before = {k: v.copy() for k, v in target.items()}
        points = np.array([camera_point(4, 4, 2)])
        a = depth_consistency(points, target, stride=2)
        b = depth_consistency(points, stride=2, depth=target["depth"], c2w_optical=target["c2w_optical"], intrinsics=target["intrinsics"])
        for key in a:
            np.testing.assert_array_equal(a[key], b[key])
        measurement_support([target], target, stride=2)
        for key in before:
            np.testing.assert_array_equal(before[key], target[key])


if __name__ == "__main__":
    unittest.main()
