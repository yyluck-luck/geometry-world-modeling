import ast
import hashlib
import json
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from memory_diagnostic import as_surfels, make_scene, run_sequence, measure, render


def definitions(path):
    tree = ast.parse(path.read_text())
    found = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            found[node.name] = node
            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    found[child.name] = child
    return found


class MemoryDiagnosticTests(unittest.TestCase):
    def test_extracted_kernel_ast_is_identical(self):
        extracted = definitions(ROOT/"src/vmem_memory_kernel.py")
        for path, names in [("utils/util.py", ["Surfel", "Octree"]),
                            ("modeling/pipeline.py", ["merge_surfels", "render_surfels_to_image"])]:
            original = definitions(ROOT/"vendor/vmem_snapshot"/path)
            for name in names:
                self.assertEqual(ast.dump(extracted[name]), ast.dump(original[name]))

    def test_upstream_snapshot_hashes(self):
        metadata = json.loads((ROOT/"vendor/provenance.json").read_text())
        for path, expected in metadata["files"].items():
            self.assertEqual(hashlib.sha256((ROOT/"vendor/vmem_snapshot"/path).read_bytes()).hexdigest(), expected)

    def test_clean_reobservation_preserves_geometry(self):
        clean = make_scene("plane")
        memory, sources, _ = run_sequence(clean, clean, "clean_first", 12, 0.045, 0.6)
        self.assertEqual(len(memory), len(clean))
        self.assertEqual(measure(memory, clean, 0.01)["mean_memory_to_gt_m"], 0)
        self.assertEqual(len(sources[0]), 14)

    def test_subthreshold_error_persists_after_clean_observations(self):
        clean = np.array([[0.0, 0.0, 4.0]])
        noisy = clean + np.array([0.0, 0.0, 0.02])
        memory, sources, _ = run_sequence(clean, noisy, "noisy_first", 12, 0.045, 0.6)
        np.testing.assert_array_equal(memory[0].position, noisy[0])
        self.assertEqual(len(memory), 1)
        self.assertEqual(sources[0], list(range(14)))

    def test_reversed_order_changes_geometry_with_same_inputs(self):
        clean = np.array([[0.0, 0.0, 4.0]])
        noisy = clean + np.array([0.0, 0.0, 0.02])
        memory, _, _ = run_sequence(clean, noisy, "clean_first", 12, 0.045, 0.6)
        np.testing.assert_array_equal(memory[0].position, clean[0])

    def test_large_error_retains_two_layers(self):
        clean = np.array([[0.0, 0.0, 4.0]])
        noisy = clean + np.array([0.0, 0.0, 0.10])
        memory, _, _ = run_sequence(clean, noisy, "noisy_first", 12, 0.045, 0.6)
        self.assertEqual(len(memory), 2)
        self.assertAlmostEqual(measure(memory, clean, 0.01)["wrong_memory_fraction"], 0.5)

    def test_numpy_render_depth_has_analytic_value(self):
        memory = as_surfels(np.array([[0.08, 0.0, 4.0]]), 0.15)
        result = render(memory)
        self.assertAlmostEqual(float(result["depth"][18, 24]), 4.0)
        self.assertEqual(int(result["surfel_index_map"][18, 24]), 0)

    def test_octree_merges_spatial_grid_without_missing_points(self):
        clean = make_scene("depth_step")
        memory, sources, trace = run_sequence(clean, clean, "noisy_first", 4, 0.045, 0.6)
        self.assertEqual(trace, [30]*6)
        self.assertTrue(all(len(ids) == 6 for ids in sources.values()))

    def test_single_leaf_control_retains_only_two_copies(self):
        from memory_diagnostic import corrupt
        clean = make_scene("plane")
        noisy = corrupt(clean, "pose_translation_x", 0.1, 0, 0.1)
        memory, _, trace = run_sequence(clean, noisy, "noisy_first", 12, 0.045, 0.6, 100000)
        self.assertEqual(trace, [30]+[60]*13)

    def test_order_dependence_survives_index_control(self):
        clean = make_scene("depth_step")
        noisy = clean + np.array([0.0, 0.0, 0.02])
        first, _, _ = run_sequence(clean, noisy, "noisy_first", 12, 0.045, 0.6, 100000)
        reverse, _, _ = run_sequence(clean, noisy, "clean_first", 12, 0.045, 0.6, 100000)
        self.assertAlmostEqual(measure(first, clean, 0.01)["mean_memory_to_gt_m"], 0.02)
        self.assertEqual(measure(reverse, clean, 0.01)["mean_memory_to_gt_m"], 0)

    def test_cli_relative_config_writes_complete_provenance(self):
        import os
        import subprocess
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            config = json.loads((ROOT/"configs/memory_recovery_pilot.json").read_text())
            for field in ["scenes", "corruptions", "levels", "seeds", "orders", "extra_clean_reobservations"]:
                config[field] = config[field][:1]
            config_file = Path(tmp)/"config.json"
            config_file.write_text(json.dumps(config))
            output = Path(tmp)/"result"
            subprocess.run([sys.executable, str(ROOT/"scripts/run_memory_pilot.py"),
                            "--config", os.path.relpath(config_file, ROOT),
                            "--out", os.path.relpath(output, ROOT)],
                           cwd=ROOT, check=True, capture_output=True)
            metadata = json.loads((output/"run_metadata.json").read_text())
            self.assertEqual(metadata["rows"], 1)
            self.assertTrue(metadata["no_model_weights_loaded"])


if __name__ == "__main__":
    unittest.main()
