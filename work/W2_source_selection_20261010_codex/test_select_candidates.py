"""Synthetic geometry, support, leakage-boundary and receipt tests only."""
import importlib.util
import io
import itertools
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import numpy as np
from PIL import Image

SPEC = importlib.util.spec_from_file_location("selector", Path(__file__).with_name("select_candidates.py"))
selector = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(selector)


def fixture():
    K = np.array([[500., 0, 319.5], [0, 500., 239.5], [0, 0, 1.]])
    poses = np.repeat(np.eye(4)[None], 4, axis=0)
    poses[:, 0, 3] = np.arange(4) * 0.1
    x, y = np.meshgrid(np.linspace(-0.3, 0.3, 6), np.linspace(-0.2, 0.2, 4))
    world = np.column_stack([x.ravel(), y.ravel(), np.full(x.size, 2.)])
    points = []
    for pose in poses:
        camera = world - pose[:3, 3]
        projected = camera @ K.T
        points.append(projected[:, :2] / projected[:, 2:3])
    pairs = [{"source_i": i, "source_j": j, "uv_i": points[i], "uv_j": points[j],
              "mutual_ratio_count": len(points[i]), "filtered_count": len(points[i]), "eligible": True}
             for i, j in itertools.combinations(range(4), 2)]
    return K, poses, points, pairs


class GeometryTests(unittest.TestCase):
    def setUp(self):
        self.K, self.poses, self.points, self.pairs = fixture()

    def test_analytic_projection_and_native_mapping(self):
        q, valid = selector.project(self.points[0], np.full(24, 2.), self.poses[0], self.poses[1], self.K)
        np.testing.assert_allclose(q, self.points[1], atol=1e-12)
        self.assertTrue(valid.all())
        indices, crop = selector.native_to_grid(np.array([[319.5, 239.5], [0, 0], [639, 479]]))
        np.testing.assert_array_equal(indices[0], [256, 192])
        np.testing.assert_array_equal(crop, [True, False, False])

    def test_epipolar_parallax_and_positive_triangulation(self):
        accepted, epipolar, parallax, z = selector.geometric_match_filter(
            self.points[0], self.points[1], self.poses[0], self.poses[1], self.K)
        self.assertTrue(accepted.all())
        np.testing.assert_allclose(epipolar, 0, atol=1e-12)
        self.assertTrue((parallax > 1).all())
        np.testing.assert_allclose(z, 2., atol=1e-10)
        wrong = self.points[1].copy()
        wrong[:, 1] += 1.01
        accepted, *_ = selector.geometric_match_filter(self.points[0], wrong, self.poses[0], self.poses[1], self.K)
        self.assertFalse(accepted.any())

    def test_negative_triangulation_filtered(self):
        impossible = self.points[0].copy()
        impossible[:, 0] += 25  # disparity sign contradicts the positive camera baseline
        accepted, epipolar, parallax, z = selector.geometric_match_filter(
            self.points[0], impossible, self.poses[0], self.poses[1], self.K)
        self.assertFalse(accepted.any())
        self.assertTrue((parallax > 1).all())
        self.assertTrue((z < 0).all())
        np.testing.assert_allclose(epipolar, 0, atol=1e-12)

    def test_symmetric_epipolar_uses_maximum_not_mean(self):
        target = np.eye(4)
        angle = np.deg2rad(20)
        target[:3, :3] = [[np.cos(angle), 0, np.sin(angle)], [0, 1, 0],
                          [-np.sin(angle), 0, np.cos(angle)]]
        target[0, 3] = 0.1
        uv = np.array([[390., 239.5]])
        observed, _ = selector.project(uv, np.array([2.]), self.poses[0], target, self.K)
        observed[:, 1] += 1.01
        accepted, epipolar, parallax, z = selector.geometric_match_filter(uv, observed, self.poses[0], target, self.K)
        # Distances are 1.01 and about 0.981 px: the mean would incorrectly pass.
        self.assertAlmostEqual(float(epipolar[0]), 1.01, places=10)
        self.assertFalse(accepted[0])
        self.assertGreater(parallax[0], 1)
        self.assertTrue((z > 0).all())

    def test_pure_rotation_and_low_parallax_abstain(self):
        accepted, *_ = selector.geometric_match_filter(self.points[0], self.points[0], self.poses[0], self.poses[0], self.K)
        self.assertFalse(accepted.any())
        tiny = self.poses[1].copy()
        tiny[0, 3] = 0.001
        observed, _ = selector.project(self.points[0], np.full(24, 2.), self.poses[0], tiny, self.K)
        accepted, *_ = selector.geometric_match_filter(self.points[0], observed, self.poses[0], tiny, self.K)
        self.assertFalse(accepted.any())

    def test_invalid_depth_and_projection_get_maximum_penalty(self):
        depth = np.full(selector.GRID, 2.)
        for invalid in (np.nan, np.inf, 0., -1.):
            depth[:] = invalid
            loss, _, valid = selector.directed_loss(depth, self.points[0], self.points[1], self.poses[0], self.poses[1], self.K)
            np.testing.assert_array_equal(loss, np.ones(24))
            self.assertFalse(valid.any())
        depth[:] = 0.001  # enormous off-image displacement
        loss, _, valid = selector.directed_loss(depth, self.points[0], self.points[1], self.poses[0], self.poses[1], self.K)
        np.testing.assert_array_equal(loss, np.ones(24))
        target = self.poses[1].copy()
        target[2, 3] = 3
        depth[:] = 2
        loss, _, valid = selector.directed_loss(depth, self.points[0], self.points[1], self.poses[0], target, self.K)
        np.testing.assert_array_equal(loss, np.ones(24))
        self.assertFalse(valid.any())

    def test_all_candidate_scores_share_support_and_choose_whole_candidate(self):
        depths = np.empty((4, 4, *selector.GRID))
        depths[0], depths[1], depths[2], depths[3] = 1., 2., 4., np.nan
        result, residuals = selector.score_candidates(depths, self.pairs, self.poses, self.K)
        self.assertEqual(result["selected_candidate_id"], "c1")
        self.assertFalse(result["abstained"])
        self.assertAlmostEqual(result["scores"]["c1"], 0., places=12)
        self.assertEqual(result["scores"]["c3"], 1.)
        for c in range(4):
            for i, j in itertools.combinations(range(4), 2):
                self.assertEqual(len(residuals[f"c{c}_pair_{i}_{j}_loss_i_to_j"]), 24)

    def test_pair_weighting_is_equal_not_match_count_weighted(self):
        pairs = [dict(pair) for pair in self.pairs]
        pairs[0]["uv_i"] = np.tile(pairs[0]["uv_i"], (100, 1))
        pairs[0]["uv_j"] = np.tile(pairs[0]["uv_j"], (100, 1))
        depths = np.ones((4, 4, *selector.GRID))
        old, _ = selector.score_candidates(depths, self.pairs, self.poses, self.K)
        new, _ = selector.score_candidates(depths, pairs, self.poses, self.K)
        np.testing.assert_allclose(list(old["scores"].values()), list(new["scores"].values()), atol=1e-14)

    def test_insufficient_or_disconnected_pairs_fall_back_without_drop(self):
        depths = np.full((4, 4, *selector.GRID), 2.)
        for pairs, reason in ((self.pairs[:2], "fewer_than_three_eligible_pairs"),
                              ([self.pairs[i] for i in (0, 1, 3)], "eligible_graph_not_connected_over_all_four_sources"),
                              ([], "fewer_than_three_eligible_pairs")):
            result, _ = selector.score_candidates(depths, pairs, self.poses, self.K)
            self.assertEqual(result["selected_candidate_id"], "c0")
            self.assertTrue(result["abstained"])
            self.assertEqual(result["abstention_reason"], reason)

    def test_tie_chooses_smallest_candidate_with_fixed_tolerance(self):
        self.assertEqual(selector.choose_candidate([.1 + .5e-12, .1, .4, .5]), 0)
        self.assertEqual(selector.choose_candidate([.1 + 2e-12, .1, .4, .5]), 1)

    def test_mutual_strict_ratio(self):
        import cv2
        # Exact unique identities with nonzero distance to the second neighbour.
        d = np.eye(4, dtype=np.float32)
        np.testing.assert_array_equal(selector.mutual_ratio_matches(d, d, cv2), np.column_stack([np.arange(4)] * 2))
        self.assertEqual(selector.mutual_ratio_matches(d[:1], d, cv2).shape, (0, 2))
        self.assertEqual(selector.mutual_ratio_matches(np.zeros_like(d), np.zeros_like(d), cv2).shape, (0, 2))

    def test_ratio_exact_boundary_is_rejected(self):
        import cv2
        first = np.array([[0.], [10.]], dtype=np.float32)
        second = np.array([[.75], [1.], [10.2]], dtype=np.float32)
        matched = selector.mutual_ratio_matches(first, second, cv2)
        np.testing.assert_array_equal(matched, [[1, 2]])


class IOTests(unittest.TestCase):
    def fixture_directory(self, root):
        window = {"window_id": "synthetic", "scene": "synthetic", "scene_rel": "synthetic",
                  "source_refs": [f"seq-01/{i:06d}" for i in range(4)],
                  "target_refs": ["seq-01/000004"]}
        scene = root / "synthetic"
        (scene / "seq-01").mkdir(parents=True)
        K, poses, _, _ = fixture()
        np.savetxt(scene / "camera-intrinsics.txt", K)
        for i, ref in enumerate(window["source_refs"]):
            base = scene / ref.split("/")[0] / ("frame-" + ref.split("/")[1])
            Image.fromarray(np.zeros((480, 640, 3), dtype=np.uint8)).save(str(base) + ".color.png")
            np.savetxt(str(base) + ".pose.txt", poses[i])
            Path(str(base) + ".depth.png").write_bytes(b"FORBIDDEN SENSOR DATA")
        (scene / "seq-01/frame-000004.color.png").write_bytes(b"FORBIDDEN TARGET DATA")
        return window

    def test_source_loader_never_opens_sensor_or_target_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            window = self.fixture_directory(root)
            original = Path.read_bytes
            read_paths = []

            def guarded(path):
                self.assertNotIn("depth", path.name)
                self.assertNotIn("000004", path.name)
                read_paths.append(path)
                return original(path)

            with mock.patch.object(Path, "read_bytes", guarded):
                rgbs, poses, K, hashes = selector.load_sources(root, window)
            self.assertEqual(len(read_paths), 9)
            self.assertEqual(len(hashes), 9)
            self.assertEqual(len(rgbs), 4)

    def test_source_path_escape_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "escapes"):
                selector.inside(Path(tmp), "../outside")

    def test_atomic_outputs_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.json"
            selector.publish_json(path, {"a": 1})
            with self.assertRaises(FileExistsError):
                selector.publish_json(path, {"a": 2})
            self.assertEqual(json.loads(path.read_text()), {"a": 1})

    def test_cli_selection_seal_and_resume_hash_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            window = self.fixture_directory(root)
            cs = [{"candidate_id": f"c{i}", "order": list(np.roll(np.arange(4), -i).astype(int).tolist())} for i in range(4)]
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"candidates": cs, "windows": [window]}))
            freeze = root / "freeze.json"
            freeze.write_text('{"frozen":true}')
            candidates, output = root / "candidates", root / "selection"
            candidates.mkdir()
            rgbs, poses, K, hashes = selector.load_sources(root, window)
            for i, candidate in enumerate(cs):
                path = candidates / f"synthetic__c{i}.npz"
                np.savez_compressed(path, depths=np.full((4, *selector.GRID), 2. if i == 2 else 1.),
                                    poses=poses.astype(np.float32), K=K, source_refs=np.array(window["source_refs"]))
                receipt = {"status": "OK", "window": window, "candidate": candidate, "candidate_sha256": selector.sha_file(path),
                           "protocol_sha256": "a" * 64, "manifest_sha256": selector.sha_file(manifest), "source_files": hashes}
                path.with_suffix(".json").write_text(json.dumps(receipt))
            args = ["--manifest", str(manifest), "--freeze", str(freeze), "--data-root", str(root),
                    "--candidates", str(candidates), "--out", str(output), "--protocol-sha", "a" * 64]
            pairs = fixture()[3]
            with mock.patch.object(selector, "source_matches", return_value=(pairs, {}, {"synthetic": True})):
                self.assertEqual(selector.main(args), 0)
                self.assertEqual(selector.main(args), 0)
            result = json.loads((output / "synthetic.json").read_text())
            self.assertEqual(result["selected_candidate_id"], "c2")
            self.assertEqual(result["candidate_scores"], [result["scores"][f"c{i}"] for i in range(4)])
            with mock.patch.object(selector, "load_sources", side_effect=AssertionError("seal must not read RGB or depth")):
                self.assertEqual(selector.main(args + ["--seal"]), 0)
                self.assertEqual(selector.main(args + ["--seal"]), 0)
            seal = json.loads((output / "SELECTION_SEAL.json").read_text())
            self.assertEqual(seal["records"][0]["window_id"], "synthetic")
            (output / "synthetic.npz").write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "checksum"):
                selector.main(args + ["--seal"])


if __name__ == "__main__":
    unittest.main()
