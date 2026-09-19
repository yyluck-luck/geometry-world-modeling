#!/usr/bin/env python3
"""Synthetic boundary tests for s48_analysis_reference_v1.

The tests create arrays in memory only.  They do not enumerate or read C1/C2
artifacts and do not import or run a model.
"""

from __future__ import annotations

import math
from pathlib import Path
import sys
import unittest

import numpy as np


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import s48_analysis_reference_v1 as ref  # noqa: E402


def _roster_record(source_id: str, insertion_event: int, **changes: object) -> dict[str, object]:
    record: dict[str, object] = {
        "insertion_event": insertion_event,
        "source_id": source_id,
        "file_sha256": (source_id.encode("utf-8").hex() + "0" * 64)[:64],
        "active": True,
        "selected": False,
        "is_target": False,
        "is_reference": False,
        "provenance_complete": True,
        "artifacts_complete": True,
        "renderable_all_targets": True,
    }
    record.update(changes)
    return record


class TestTopologyAndHistograms(unittest.TestCase):
    def test_four_connectivity_keeps_diagonal_pixels_separate(self) -> None:
        weight = np.asarray([[1.0, 0.0], [0.0, 0.5]], dtype=np.float64)
        self.assertEqual(ref.connected_components4(weight), 2)

    def test_exposed_edge_perimeter_and_scale(self) -> None:
        single = np.asarray([[1.0]], dtype=np.float64)
        pair = np.asarray([[1.0, 1.0]], dtype=np.float64)
        self.assertEqual(ref.exposed_edge_perimeter(single), 4)
        self.assertEqual(ref.exposed_edge_perimeter(pair), 6)
        self.assertEqual(ref.normalized_perimeter(single), 4.0)
        self.assertAlmostEqual(ref.normalized_perimeter(pair), 6.0 / math.sqrt(2.0))

    def test_positive_histogram_excludes_zeros_and_fixes_edges(self) -> None:
        weight = np.asarray([[0.0, 0.05, 0.10], [0.95, 1.0, 0.0]], dtype=np.float64)
        histogram = ref.positive_weight_histogram(weight)
        expected = np.zeros(10, dtype=np.float64)
        expected[0] = 0.25
        expected[1] = 0.25
        expected[9] = 0.50
        np.testing.assert_array_equal(histogram, expected)

    def test_centroid_pixel_centers_and_grid_boundary(self) -> None:
        weight = np.zeros((4, 4), dtype=np.float64)
        weight[0, 0] = 1.0
        self.assertEqual(ref.weighted_centroid_normalized(weight), (0.125, 0.125))
        self.assertEqual(ref.centroid_grid4_cell(weight), (0, 0))

    def test_mask_hash_and_caliper_equalities_are_deterministic(self) -> None:
        rows, cols = np.indices((8, 8), dtype=np.float64)
        depth = 1.0 + 0.01 * rows + 0.02 * cols
        confidence = (rows + cols) / 14.0
        reference = np.zeros((8, 8), dtype=np.float64)
        candidate = np.zeros((8, 8), dtype=np.float64)
        reference[1:3, 1:3] = 0.5
        candidate[1:3, 5:7] = 0.5
        self.assertEqual(ref.weight_map_sha256(reference), ref.weight_map_sha256(reference.copy()))
        negative_zero = reference.copy()
        negative_zero[0, 0] = -0.0
        self.assertEqual(ref.weight_map_sha256(reference), ref.weight_map_sha256(negative_zero))
        metrics = ref.mask_caliper_metrics(reference, candidate, depth, confidence)
        self.assertTrue(metrics.same_centroid_grid4_cell is False)
        self.assertEqual(metrics.binary_iou, 0.0)
        self.assertEqual(metrics.weighted_area_relative_error, 0.0)

    def test_mask_caliper_threshold_equalities_pass(self) -> None:
        metrics = ref.MaskCaliperMetrics(0.02, 2, 2, 0.10, True, 0.10, 0.05, True, 0.0)
        self.assertEqual(ref.mask_caliper_decision(metrics), (True, ()))
        over = ref.MaskCaliperMetrics(0.02, 2, 2, 0.10, True, 0.10, 0.0500000001, True, 0.0)
        passed, reasons = ref.mask_caliper_decision(over)
        self.assertFalse(passed)
        self.assertEqual(reasons, ("POSITIVE_WEIGHT_HISTOGRAM_L1_ABOVE_MAX",))

    def test_empty_support_is_explicitly_invalid(self) -> None:
        empty = np.zeros((2, 2), dtype=np.float64)
        with self.assertRaisesRegex(ref.SpecError, "empty support"):
            ref.normalized_perimeter(empty)
        with self.assertRaisesRegex(ref.SpecError, "empty support"):
            ref.positive_weight_histogram(empty)


class TestDepthAndStrata(unittest.TestCase):
    def test_planar_metric_depth_has_exact_gradient_including_edges(self) -> None:
        rows, cols = np.indices((5, 6), dtype=np.float64)
        depth = 1.0 + rows + 2.0 * cols
        gradient, valid = ref.metric_depth_gradient(depth)
        self.assertTrue(valid.all())
        np.testing.assert_allclose(gradient, math.sqrt(5.0), atol=0.0, rtol=0.0)

    def test_invalid_depth_emits_zero_plus_false_not_nan(self) -> None:
        depth = np.ones((5, 5), dtype=np.float64)
        depth[2, 2] = np.nan
        gradient, valid = ref.metric_depth_gradient(depth)
        self.assertFalse(valid[2, 2])
        self.assertEqual(gradient[2, 2], 0.0)
        self.assertTrue(np.isfinite(gradient).all())

    def test_relative_depth_boundary_is_strict_and_density_is_finite(self) -> None:
        # |50-49|/50 is the same float64 value as the frozen 0.02 threshold.
        at_boundary = np.asarray([[49.0, 50.0], [49.0, 50.0]], dtype=np.float64)
        above_boundary = np.asarray([[48.999, 50.0], [48.999, 50.0]], dtype=np.float64)
        boundary_equal, _ = ref.depth_discontinuity_map(at_boundary)
        boundary_above, _ = ref.depth_discontinuity_map(above_boundary)
        self.assertFalse(boundary_equal.any())
        self.assertTrue(boundary_above.any())
        density, valid = ref.local_boundary_density(above_boundary)
        self.assertTrue(valid.all())
        self.assertTrue(np.isfinite(density).all())
        self.assertGreater(float(density.max()), 0.0)

    def test_weighted_median_and_repeated_quartile_ties_are_fixed(self) -> None:
        value = ref.weighted_quantile_lower([0.0, 1.0, 2.0], [0.5, 0.5, 9.0], 0.5)
        self.assertEqual(value, 2.0)
        cuts = ref.type7_quantiles([0.0, 0.0, 0.0, 1.0])
        np.testing.assert_array_equal(cuts, np.asarray([0.0, 0.0, 0.25]))
        self.assertEqual(ref.quartile_stratum(0.0, cuts), 2)
        self.assertEqual(ref.quartile_stratum(0.25, cuts), 3)

    def test_context_strata_use_full_target_population_and_mask_weighted_median(self) -> None:
        rows, cols = np.indices((7, 7), dtype=np.float64)
        depth = 1.0 + 0.01 * rows + 0.02 * cols
        confidence = (rows + cols) / 12.0
        weight = np.zeros((7, 7), dtype=np.float64)
        weight[2:5, 2:5] = 0.75
        descriptors = ref.mask_context_strata(weight, depth, confidence)
        self.assertEqual(
            set(descriptors),
            {
                "visible_metric_depth",
                "metric_depth_gradient",
                "projection_confidence",
                "local_depth_boundary_density",
            },
        )
        for descriptor in descriptors.values():
            self.assertIn(descriptor["stratum"], range(4))
            self.assertTrue(math.isfinite(descriptor["summary"]))
            self.assertEqual(descriptor["valid_weight_fraction"], 1.0)

    def test_descriptor_rejects_insufficient_valid_weight(self) -> None:
        values = np.ones((2, 2), dtype=np.float64)
        valid = np.asarray([[True, False], [False, False]])
        weight = np.ones((2, 2), dtype=np.float64)
        with self.assertRaisesRegex(ref.SpecError, "valid-weight coverage"):
            ref.context_descriptor(values, valid, weight)


class TestSourceEditsAndGates(unittest.TestCase):
    def test_exposure_formula_and_texture_constant_fixed_point(self) -> None:
        rgb = np.full((5, 5, 3), 0.5, dtype=np.float64)
        exposure = ref.apply_source_edit(rgb, "exposure_log_gain", 1, ref.EXPOSURE_DOSES[0])
        np.testing.assert_allclose(
            exposure,
            0.5 * math.pow(2.0, ref.EXPOSURE_DOSES[0]),
            atol=0.0,
            rtol=0.0,
        )
        for sign in (-1, 1):
            texture = ref.apply_source_edit(rgb, "texture_highpass", sign, ref.TEXTURE_DOSES[-1])
            np.testing.assert_allclose(texture, rgb, atol=1e-15, rtol=0.0)

    def test_minimum_dose_requires_both_signs_and_inclusive_gate_boundaries(self) -> None:
        rgb = np.full((5, 5, 3), 0.5, dtype=np.float64)
        external = {
            (dose, sign): {"clip_cosine": ref.SOURCE_CLIP_COSINE_MIN, "lpips": ref.SOURCE_LPIPS_MAX}
            for dose in ref.EXPOSURE_DOSES
            for sign in (-1, 1)
        }
        dose, by_sign = ref.select_minimum_source_dose(rgb, "exposure_log_gain", external)
        self.assertEqual(dose, ref.EXPOSURE_DOSES[0])
        self.assertTrue(all(ref.source_edit_gate(metrics)[0] for metrics in by_sign.values()))
        exact = ref.SourceEditMetrics(
            ref.SOURCE_MAD_MIN,
            ref.SOURCE_CLIPPED_CHANNEL_FRACTION_MAX,
            ref.SOURCE_EDGE_IOU_MIN,
            ref.SOURCE_CLIP_COSINE_MIN,
            ref.SOURCE_LPIPS_MAX,
        )
        self.assertEqual(ref.source_edit_gate(exact), (True, ()))

    def test_invalid_nan_and_non_ladder_dose_are_rejected(self) -> None:
        rgb = np.full((5, 5, 3), 0.5, dtype=np.float64)
        with self.assertRaises(ref.SpecError):
            ref.apply_source_edit(rgb, "exposure_log_gain", 1, 0.123)
        bad = rgb.copy()
        bad[0, 0, 0] = np.nan
        with self.assertRaises(ref.SpecError):
            ref.apply_source_edit(bad, "exposure_log_gain", 1, ref.EXPOSURE_DOSES[0])


class TestRoster(unittest.TestCase):
    def test_complete_flow_and_utf8_byte_order(self) -> None:
        records = [
            _roster_record("z", 1),
            _roster_record("a", 1),
            _roster_record("selected", 0, selected=True),
            _roster_record("bad", 2, provenance_complete=False, artifacts_complete=False),
        ]
        roster = ref.build_unselected_source_roster(records)
        self.assertEqual(
            tuple(record["source_id"] for record in roster["all_records"]),
            ("selected", "a", "z", "bad"),
        )
        self.assertEqual(roster["eligible_source_ids"], ("a", "z"))
        bad_record = roster["all_records"][-1]
        self.assertEqual(
            bad_record["exclusion_reasons"],
            ("PROVENANCE_INCOMPLETE", "SCIENTIFIC_ARTIFACTS_INCOMPLETE"),
        )
        self.assertRegex(roster["canonical_sha256"], r"^[0-9a-f]{64}$")

    def test_duplicate_source_id_and_truthy_integer_boolean_fail(self) -> None:
        with self.assertRaisesRegex(ref.SpecError, "unique"):
            ref.build_unselected_source_roster([_roster_record("x", 0), _roster_record("x", 1)])
        invalid = _roster_record("x", 0, active=1)
        with self.assertRaisesRegex(ref.SpecError, "boolean"):
            ref.build_unselected_source_roster([invalid])


class TestArmGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        rng = np.random.default_rng(481701)
        cls.native_rgb = rng.uniform(0.1, 0.9, size=(576, 576, 3)).astype(np.float64)
        cls.support = np.zeros((576, 576), dtype=np.float64)
        cls.support[240:336, 240:336] = 1.0

    def test_identical_native_frames_have_many_zero_displacement_matches(self) -> None:
        metrics = ref.arm_guard_metrics(self.native_rgb, self.native_rgb.copy(), self.support)
        self.assertGreaterEqual(metrics.match_count, ref.PATCH_MIN_MUTUAL_MATCHES)
        self.assertEqual(metrics.median_displacement_px, 0.0)
        self.assertEqual(metrics.p95_displacement_px, 0.0)
        self.assertEqual(metrics.outside_brightness_difference, 0.0)
        self.assertAlmostEqual(metrics.sharpness_ratio_deviation, 0.0)
        self.assertEqual(metrics.saturation_increase_pp, 0.0)
        self.assertEqual(metrics.tear_excess, 0.0)

    def test_known_one_pixel_translation_is_recovered(self) -> None:
        shifted = np.empty_like(self.native_rgb)
        shifted[:, 0, :] = self.native_rgb[:, 0, :]
        shifted[:, 1:, :] = self.native_rgb[:, :-1, :]
        metrics = ref.patch_displacement_metrics(self.native_rgb, shifted)
        self.assertGreaterEqual(metrics.match_count, ref.PATCH_MIN_MUTUAL_MATCHES)
        self.assertEqual(metrics.median_px, 1.0)
        self.assertEqual(metrics.p95_px, 1.0)

    def test_guard_thresholds_are_inclusive_and_each_failure_is_named(self) -> None:
        floors = ref.ArmGuardFloors(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        exact = ref.ArmGuardMetrics(
            ref.PATCH_MIN_MUTUAL_MATCHES,
            ref.GUARD_MEDIAN_FLOOR_PX,
            ref.GUARD_P95_FLOOR_PX,
            ref.GUARD_BRIGHTNESS_FLOOR,
            ref.GUARD_SHARPNESS_RATIO_FLOOR,
            ref.GUARD_SATURATION_FLOOR_PP,
            ref.GUARD_TEAR_FLOOR,
        )
        self.assertEqual(ref.arm_guard_decision(exact, floors), (True, ()))
        failed = ref.ArmGuardMetrics(
            ref.PATCH_MIN_MUTUAL_MATCHES - 1,
            ref.GUARD_MEDIAN_FLOOR_PX + 1e-9,
            ref.GUARD_P95_FLOOR_PX + 1e-9,
            ref.GUARD_BRIGHTNESS_FLOOR + 1e-9,
            ref.GUARD_SHARPNESS_RATIO_FLOOR + 1e-9,
            ref.GUARD_SATURATION_FLOOR_PP + 1e-9,
            ref.GUARD_TEAR_FLOOR + 1e-9,
        )
        passed, reasons = ref.arm_guard_decision(failed, floors)
        self.assertFalse(passed)
        self.assertEqual(len(reasons), 7)

    def test_replay_floors_are_componentwise_maxima(self) -> None:
        first = ref.ArmGuardMetrics(100, 1.0, 2.0, 0.01, 0.02, -1.0, 0.03)
        second = ref.ArmGuardMetrics(100, 0.5, 4.0, 0.02, 0.01, 2.0, 0.01)
        records = [first, second, first, second, first, second]
        floors = ref.replay_guard_floors(records, replay_instance_count=4)
        self.assertEqual(
            floors,
            ref.ArmGuardFloors(1.0, 4.0, 0.02, 0.02, 2.0, 0.03),
        )

    def test_replay_floor_requires_every_unordered_pair(self) -> None:
        metric = ref.ArmGuardMetrics(100, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        with self.assertRaisesRegex(ref.SpecError, "expected 6"):
            ref.replay_guard_floors([metric], replay_instance_count=4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
