"""Boundary checks only; no checkpoint loading or model inference."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import numpy as np
from PIL import Image

SPEC = importlib.util.spec_from_file_location("w1_generator", Path(__file__).with_name("generate_candidates.py"))
G = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(G)


def manifest():
    return {"candidates": [{"candidate_id": "c0", "order": [0, 1, 2, 3]}],
            "windows": [{"window_id": "scene13_w0", "scene": "scene_13", "scene_rel": "scene",
                         "source_refs": [f"seq-01/{i:06d}" for i in (0, 15, 30, 45)],
                         "target_refs": ["seq-01/000060"]}]}


class GeneratorBoundaryTests(unittest.TestCase):
    def test_target_overlap_and_bad_permutations_are_rejected(self):
        G.validate_manifest(manifest())
        bad = manifest()
        bad["windows"][0]["target_refs"] = ["seq-01/000015"]
        with self.assertRaisesRegex(ValueError, "overlap"):
            G.validate_manifest(bad)
        bad = manifest()
        bad["candidates"][0]["order"] = [0, 1, 1, 3]
        with self.assertRaisesRegex(ValueError, "permute"):
            G.validate_manifest(bad)

    def test_source_loader_opens_only_allowlisted_bytes(self):
        window = manifest()["windows"][0]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            scene = root / "scene"
            (scene / "seq-01").mkdir(parents=True)
            K = np.array([[540., 0, 320], [0, 540., 240], [0, 0, 1]])
            np.savetxt(scene / "camera-intrinsics.txt", K)
            expected = {scene / "camera-intrinsics.txt"}
            for reference in window["source_refs"]:
                seq, frame = reference.split("/")
                color = scene / seq / f"frame-{frame}.color.png"
                pose = scene / seq / f"frame-{frame}.pose.txt"
                Image.fromarray(np.zeros((480, 640, 3), np.uint8)).save(color)
                np.savetxt(pose, np.eye(4))
                expected.update((color, pose))
                # These data are deliberately unusable; the predictor must never read them.
                (scene / seq / f"frame-{frame}.depth.png").write_bytes(b"FORBIDDEN DEPTH")
            (scene / "seq-01/frame-000060.color.png").write_bytes(b"FORBIDDEN TARGET")
            opened = []
            original = Path.read_bytes

            def recording(path):
                self.assertIn(path, expected)
                opened.append(path)
                return original(path)

            with mock.patch.object(Path, "read_bytes", recording):
                rgb, poses, returned_K, hashes = G.load_sources(root, window)
            self.assertEqual(set(opened), expected)
            self.assertEqual(len(opened), 9)
            self.assertEqual(len(rgb), 4)
            np.testing.assert_array_equal(poses, np.repeat(np.eye(4)[None], 4, axis=0))
            np.testing.assert_array_equal(K, returned_K)
            self.assertEqual(len(hashes), 9)

    def test_source_symlink_cannot_escape_root(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "root"
            root.mkdir()
            outside = Path(temp) / "outside"
            outside.write_text("outside")
            (root / "escape").symlink_to(outside)
            with self.assertRaisesRegex(ValueError, "escapes"):
                G.contained_path(root, "escape")

    def geometry(self, order):
        return {"depths": [np.full((1, 2, 3), index + 1., np.float32) for index in order],
                "confidences": [np.full((1, 2, 3), 10. + index, np.float32) for index in order],
                "point_clouds": [np.full((1, 2, 3, 3), 20. + index, np.float32) for index in order]}

    def test_cyclic_candidate_restores_source_identity(self):
        order = [2, 3, 0, 1]
        with mock.patch.object(G, "GRID", (2, 3)):
            restored = G.restore_geometry(self.geometry(order), order)
        np.testing.assert_array_equal(restored["depths"][:, 0, 0], [1, 2, 3, 4])
        np.testing.assert_array_equal(restored["confidences"][:, 0, 0], [10, 11, 12, 13])
        np.testing.assert_array_equal(restored["point_clouds"][:, 0, 0, 0], [20, 21, 22, 23])

    def test_local_invalid_predictions_are_preserved(self):
        values = self.geometry([0, 1, 2, 3])
        values["depths"][0][0, 0] = [np.nan, -1, 0]
        values["confidences"][1][0, 0, 0] = np.inf
        with mock.patch.object(G, "GRID", (2, 3)):
            restored = G.restore_geometry(values, [0, 1, 2, 3])
        self.assertTrue(np.isnan(restored["depths"][0, 0, 0]))
        np.testing.assert_array_equal(restored["depths"][0, 0, 1:], [-1, 0])
        self.assertTrue(np.isinf(restored["confidences"][1, 0, 0]))

    def test_all_invalid_and_incomplete_candidates_are_rejected(self):
        values = self.geometry([0, 1, 2, 3])
        values["depths"] = [np.full((1, 2, 3), np.nan) for _ in range(4)]
        with mock.patch.object(G, "GRID", (2, 3)):
            with self.assertRaisesRegex(ValueError, "All candidate depths"):
                G.restore_geometry(values, [0, 1, 2, 3])
            del values["confidences"]
            with self.assertRaisesRegex(ValueError, "Missing complete"):
                G.restore_geometry(values, [0, 1, 2, 3])

    def test_publication_and_resume_refuse_mismatch_or_corruption(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "candidate.npz"
            receipt = path.with_suffix(".json")
            self.assertFalse(G.existing_matches(path, receipt, "fingerprint"))
            G.atomic_publish(path, lambda fh: fh.write(b"candidate bytes"))
            with self.assertRaisesRegex(ValueError, "Incomplete"):
                G.existing_matches(path, receipt, "fingerprint")
            G.publish_json(receipt, {"status": "OK", "fingerprint": "fingerprint",
                                     "candidate_sha256": G.sha_file(path)})
            self.assertTrue(G.existing_matches(path, receipt, "fingerprint"))
            with self.assertRaisesRegex(ValueError, "fingerprints differ"):
                G.existing_matches(path, receipt, "changed")
            with self.assertRaises(FileExistsError):
                G.atomic_publish(path, lambda fh: fh.write(b"replacement"))
            self.assertEqual(path.read_bytes(), b"candidate bytes")
            path.write_bytes(b"corruption")
            with self.assertRaisesRegex(ValueError, "checksum"):
                G.existing_matches(path, receipt, "fingerprint")

    def test_failure_receipt_can_record_nonfinite_kps_diagnostics(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "error.json"
            G.publish_json(path, {"sigma": np.inf, "error": "Nonfinite scale"})
            self.assertIsNone(json.loads(path.read_text())["sigma"])

    def test_trusted_checkpoint_override_is_scoped_and_restored(self):
        calls = []

        class FakeTorch:
            @staticmethod
            def load(path, **kwargs):
                calls.append((path, kwargs))

        original = FakeTorch.load
        with G.trusted_checkpoint_load(FakeTorch, Path("trusted.pth")):
            FakeTorch.load("trusted.pth")
            FakeTorch.load("other.pth")
        self.assertIs(FakeTorch.load, original)
        self.assertFalse(calls[0][1]["weights_only"])
        self.assertNotIn("weights_only", calls[1][1])


if __name__ == "__main__":
    unittest.main()
