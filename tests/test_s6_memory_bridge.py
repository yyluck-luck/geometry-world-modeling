from copy import deepcopy
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from s6_memory_bridge import (build_memory, crop_intrinsics, make_selector,
                              make_surfels, memory_digest, normalize_predictions)
from rgbd_retrieval import optical_to_vmem, select, initial_nms_threshold


def plane(depth=1.):
    return (np.full((224, 224), depth), np.ones((224, 224)),
            np.full((224, 224, 3), [128, 64, 32], dtype=np.uint8), np.eye(4))


def raw_prediction(depths, poses):
    result = {}
    for i, (depth, pose) in enumerate(zip(depths, poses)):
        xyz = np.full((1, 224, 224, 3), np.nan)
        xyz[..., 2] = depth
        result[f'frame{i}_pts3d_in_self_view'] = xyz
        result[f'frame{i}_camera_c2w'] = pose[None]
    return result


class TestS6MemoryBridge(unittest.TestCase):
    def test_crop_pixel_centers_and_ray(self):
        fx, fy, cx, cy = crop_intrinsics()
        self.assertEqual((fx, fy, cx, cy), (245.2734375, 245., 112., 111.5))
        # A crop pixel maps back to the same ray in the original sensor image.
        for u, v in [(0, 0), (112, 111.5), (223, 223)]:
            source_u = (u + 37 + .5) * 640 / 299 - .5
            source_v = (v + .5) * 480 / 224 - .5
            np.testing.assert_allclose([(u-cx)/fx, (v-cy)/fy],
                                       [(source_u-319.5)/525, (source_v-239.5)/525])

    def test_normalization_prediction_only_and_relative_pose(self):
        a = np.eye(4); a[:3, :3] = [[0, -1, 0], [1, 0, 0], [0, 0, 1]]
        a[:3, 3] = [9, 8, 7]
        b = a.copy(); b[:3, 3] += [0, 4, 0]
        depths = [np.full((224, 224), 2.), np.full((224, 224), 6.)]
        depths[0][0, :3] = [0, np.nan, -2]
        arrays = raw_prediction(depths, [a, b])
        z, poses, scale = normalize_predictions(arrays)
        self.assertEqual(scale, .5)
        self.assertEqual(z[0][1, 1], 1.)
        self.assertEqual(z[1][1, 1], 3.)
        np.testing.assert_allclose(poses[0], np.eye(4), atol=1e-15)
        np.testing.assert_allclose(poses[1][:3, 3], [2, 0, 0], atol=1e-15)
        self.assertTrue(np.isnan(arrays['frame0_pts3d_in_self_view'][0, 1, 1, 0]))
        # Units changed everywhere: normalized depths and poses must be invariant.
        arrays2 = raw_prediction([d*7 for d in depths], [a.copy(), b.copy()])
        for i in range(2):
            arrays2[f'frame{i}_camera_c2w'][0, :3, 3] *= 7
        z2, p2, n2 = normalize_predictions(arrays2)
        for x, y in zip(z, z2):
            np.testing.assert_allclose(x, y, equal_nan=True)
        np.testing.assert_allclose(poses, p2, atol=1e-14)
        self.assertAlmostEqual(n2, scale/7)

    def test_plane_normals_radius_and_transform(self):
        depth, conf, rgb, pose = plane()
        surfels, counts = make_surfels(depth, conf, rgb, pose, 8)
        self.assertEqual(len(surfels), 28*28)
        self.assertEqual(counts['accepted_surfels'], counts['sampled_grid_points'])
        fx, fy, cx, cy = crop_intrinsics()
        first = surfels[0]
        expected = np.array([-cx/fx, -cy/fy, 1.])
        np.testing.assert_allclose(first.position, expected)
        np.testing.assert_allclose(first.normal, [0, 0, 1])
        cosine = 1. / np.linalg.norm(expected)
        self.assertAlmostEqual(first.radius, .5/((fx+fy)/2/8)/(.2+.8*cosine))
        np.testing.assert_allclose(first.color, [128/255, 64/255, 32/255])
        pose[:3, :3] = [[0, 0, 1], [0, 1, 0], [-1, 0, 0]]
        pose[:3, 3] = [1, 2, 3]
        transformed, _ = make_surfels(depth, conf, rgb, pose)
        np.testing.assert_allclose(transformed[0].position, pose[:3, :3]@expected + pose[:3, 3])
        np.testing.assert_allclose(transformed[0].normal, [1, 0, 0])
        self.assertAlmostEqual(transformed[0].radius, first.radius)
        coarse, _ = make_surfels(depth, conf, rgb, np.eye(4), 12)
        self.assertAlmostEqual(coarse[0].radius / first.radius, 1.5)

    def test_neighbor_confidence_far_cutoff_and_accounting(self):
        depth, conf, rgb, pose = plane()
        conf[0, 1] = .5       # Center (0,0) valid, its right neighbor is not.
        depth[8, 8] = 100.   # Far cutoff from all positive finite pixels.
        depth[16, 17] = .94  # Right neighbor crosses the .05 normalized jump.
        depth[24, 24] = 0
        conf[32, 32] = np.nan
        surfels, counts = make_surfels(depth, conf, rgb, pose)
        self.assertEqual(counts['far_cutoff_normalized'], 1.)
        self.assertEqual(counts['rejected_sample_neighbor'], 1)
        self.assertEqual(counts['rejected_sample_neighbor_jump'], 1)
        self.assertEqual(counts['rejected_sample_center'], 3)
        categories = [v for k, v in counts.items() if k.startswith('rejected_sample_')]
        self.assertEqual(sum(categories) + len(surfels), counts['sampled_grid_points'])
        self.assertEqual(counts['rejected_pixel_depth'] +
                         counts['rejected_pixel_confidence_after_depth'] +
                         counts['rejected_pixel_far_after_depth_confidence'] +
                         counts['eligible_pixels'], 224*224)
        self.assertTrue(all(np.isfinite(s.position).all() for s in surfels))

    def test_empty_valid_pixels_and_bad_inputs(self):
        depth, conf, rgb, pose = plane()
        depth[:] = np.nan
        surfels, counts = make_surfels(depth, conf, rgb, pose)
        self.assertEqual(surfels, [])
        self.assertIsNone(counts['far_cutoff_normalized'])
        with self.assertRaises(ValueError):
            normalize_predictions(raw_prediction([depth], [pose]))
        with self.assertRaises(ValueError):
            make_surfels(*plane(), stride=16)
        with self.assertRaises(ValueError):
            make_surfels(plane()[0], conf, rgb.astype(float), pose)
        pose[0, 0] = 2
        with self.assertRaises(ValueError):
            normalize_predictions(raw_prediction([plane()[0]], [pose]))

    def test_history_only_units_and_matching_reuse(self):
        depth, conf, rgb, pose = plane()
        args = ([depth, depth + .002], [conf, conf], [rgb, rgb], [pose, pose])
        first, filters = build_memory(*args, method='first_write')
        mean, _ = build_memory(*args, method='frame_mean')
        np.testing.assert_allclose(first.points[0], [-112/245.2734375, -111.5/245, 1.])
        self.assertGreater(mean.points[0, 2], first.points[0, 2])
        self.assertEqual(filters[1]['frame_id'], 1)
        self.assertTrue(all(0 <= t < 2 for ids in first.mapping.values() for t in ids))
        self.assertIn('position_threshold_normalized', first.records[0])
        self.assertIn('radius_normalized_quantiles', first.records[0])
        self.assertNotIn('position_threshold_m', first.records[0])
        self.assertNotIn('radius_m_quantiles', first.records[0])
        with self.assertRaises(ValueError):
            build_memory([depth]*21, [conf]*21, [rgb]*21, [pose]*21)

    def test_selector_full_path_square_crop_and_query_immutability(self):
        depth, conf, rgb, _ = plane()
        poses = []
        for i in range(20):
            p = np.eye(4); p[:3, 3] = [i*.004, i*.001, 0]
            poses.append(p)
        memory, _ = build_memory([depth]*20, [conf]*20, [rgb]*20, poses)
        digest = memory_digest(memory)
        for width in (160, 320):
            obj = make_selector(memory, poses, width)
            self.assertEqual(obj.config.surfel.height, width)
            self.assertEqual(obj.config.surfel.width, width)
            fx, fy, cx, cy = crop_intrinsics()
            np.testing.assert_allclose(obj.Ks[0], [[fx*width/224, 0, cx*width/224],
                                                  [0, fy*width/224, cy*width/224], [0, 0, 1]])
            self.assertAlmostEqual(obj.surfel_Ks[0], (fx+fy)/2*width/224)
            self.assertAlmostEqual(obj.initial_threshold, initial_nms_threshold(poses))
            np.testing.assert_allclose(obj.get_transformed_c2ws(), poses)
            np.testing.assert_allclose(optical_to_vmem(optical_to_vmem(poses[0])), poses[0])
            result = select(obj, poses[-1])
            self.assertEqual(len(set(result['selected'])), 4)
            self.assertTrue(all(0 <= i < 20 for i in result['selected']))
            self.assertEqual(memory_digest(memory), digest)
        with self.assertRaises(ValueError):
            make_selector(memory, poses + [np.eye(4)])
        memory.mapping[0].append(20)
        with self.assertRaises(ValueError):
            make_selector(memory, poses)

    def test_digest_covers_every_requested_field(self):
        depth, conf, rgb, pose = plane()
        memory, _ = build_memory([depth], [conf], [rgb], [pose])
        baseline = memory_digest(memory)
        for field in ('position', 'normal', 'radius', 'color', 'counts', 'mapping'):
            altered = deepcopy(memory)
            if field in ('position', 'normal', 'color'):
                getattr(altered.surfels[0], field)[0] += .01
            elif field == 'radius':
                altered.surfels[0].radius += .01
            elif field == 'counts':
                altered.counts[0] += 1
            else:
                altered.mapping[0].append(1)
            self.assertNotEqual(memory_digest(altered), baseline, field)


if __name__ == '__main__':
    unittest.main()
