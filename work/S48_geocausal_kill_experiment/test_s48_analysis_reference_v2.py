#!/usr/bin/env python3
"""Synthetic tests for the S48 V6 source-only normative candidate.

No test enumerates or opens C1/C2 artifacts, imports a model, or runs an arm.
The randomized section uses 256 deterministic in-memory property cases.
"""

from __future__ import annotations

from dataclasses import replace
import math
from pathlib import Path
import sys
import unittest

import numpy as np


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s48_analysis_reference_v2 as ref  # noqa: E402


PROPERTY_CASES = 256
OUTPUT_PROPERTY_CASES = 16
ZERO_SHA = "0" * 64
ONE_SHA = "1" * 64
TWO_SHA = "2" * 64


def _support() -> np.ndarray:
    support = np.zeros((ref.NATIVE_HEIGHT, ref.NATIVE_WIDTH), dtype=np.float64)
    support[192:384, 192:384] = 1.0
    return support


def _native_textured(seed: int = 481701) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.integers(32, 224, size=(ref.NATIVE_HEIGHT, ref.NATIVE_WIDTH, 3), dtype=np.uint8)


def _native_constant(value: int) -> np.ndarray:
    return np.full((ref.NATIVE_HEIGHT, ref.NATIVE_WIDTH, 3), value, dtype=np.uint8)


def _tail(*, count: int = 199, true_mass: float = 0.30, median: float = 0.20, rank: float = 0.005) -> dict[str, float | int]:
    return {"count": count, "true_mass": true_mass, "lower_median": median, "tail_rank": rank}


def _guard_metrics(**changes: object) -> ref.ArmGuardMetrics:
    base: dict[str, object] = {
        "global_expected": 324,
        "global_matches": 324,
        "global_coverage": 1.0,
        "global_median_px": 0.0,
        "global_p95_px": 0.0,
        "support_expected": 36,
        "support_matches": 36,
        "support_coverage": 1.0,
        "support_median_px": 0.0,
        "support_p95_px": 0.0,
        "neighborhood_expected": 28,
        "neighborhood_matches": 28,
        "neighborhood_coverage": 1.0,
        "neighborhood_median_px": 0.0,
        "neighborhood_p95_px": 0.0,
        "outside_rgb_difference": 0.0,
        "outside_chroma_difference": 0.0,
        "sharpness_deviation": 0.0,
        "saturation_difference_pp": 0.0,
        "tear_difference": 0.0,
    }
    base.update(changes)
    return ref.ArmGuardMetrics(**base)


def _floors(**changes: float) -> ref.GuardFloors:
    base = {name: 0.0 for name in ref._FLOOR_FIELDS}
    base.update(changes)
    return ref.GuardFloors(**base)


def _replay_receipts(metric: ref.ArmGuardMetrics | None = None) -> list[ref.ReplayPairReceipt]:
    chosen = _guard_metrics() if metric is None else metric
    return [ref.ReplayPairReceipt("seed-1", "target-1", i, j, chosen) for i in range(4) for j in range(i + 1, 4)]


def _camera(center: tuple[float, float, float] = (0.0, 0.0, 0.0), *, angle_degrees: float = 0.0, fov: float = 60.0) -> ref.Camera:
    radians = math.radians(angle_degrees)
    rotation = np.asarray(
        [[math.cos(radians), -math.sin(radians), 0.0], [math.sin(radians), math.cos(radians), 0.0], [0.0, 0.0, 1.0]],
        dtype=np.float64,
    )
    return ref.Camera(center, rotation, fov)


def _calibration(**changes: object) -> ref.SyncCalibration:
    values: dict[str, object] = {"t0_sensor_ns": 0, "offset_ns": 0, "drift_ppb": 0, "measured_residuals_ns": (0, 1, -1)}
    values.update(changes)
    return ref.SyncCalibration(**values)


def _candidate(candidate_id: str, digest: str, **changes: object) -> ref.ReferenceCandidate:
    small_support = np.asarray([[1.0, 0.0], [0.0, 0.0]], dtype=np.float64)
    valid = np.ones((2, 2), dtype=bool)
    identity = np.zeros((2, 2), dtype=np.int16)
    identity_receipt = ref.identity_agreement(
        {"O": identity, "R": identity.copy()},
        {"O": valid, "R": valid.copy()},
        small_support,
        roles=("O", "R"),
    )
    view_receipts = tuple(ref.ViewPairReceipt(label, 4, (0.0, 0.0, 0.0)) for label in ("O_R", "R_PREV_R", "R_R_NEXT"))
    domain_receipts = {
        "support": ref.valid_domain_receipt("support", small_support > 0.0, {"O": valid, "R": valid}),
        "outside": ref.valid_domain_receipt("outside", small_support == 0.0, {"O": valid, "R": valid}),
    }
    values: dict[str, object] = {
        "candidate_id": candidate_id,
        "file_sha256": digest,
        "scene_id": "scene",
        "sensor_timestamp_ns": 1_000_000_000,
        "camera": _camera(),
        "calibration": _calibration(),
        "identity_receipt": identity_receipt,
        "view_pair_receipts": view_receipts,
        "domain_receipts": domain_receipts,
    }
    values.update(changes)
    return ref.ReferenceCandidate(**values)


def _reinsert(role: str, source: str, content_sha: str, attempt: str, pid: int) -> ref.ReinsertReceipt:
    return ref.ReinsertReceipt(
        role=role,
        source_id=source,
        source_content_sha256=content_sha,
        encoded_source_sha256=content_sha,
        attempt_id=attempt,
        process_id=pid,
        fresh_process=True,
        process_isolation_spec_sha256=ZERO_SHA,
        source_adapter_sha256=TWO_SHA,
        base_snapshot_sha256=ONE_SHA,
        injection_point_sha256=TWO_SHA,
        slot=0,
        tensor_shape=(1, 3, 16, 16),
        position_interface_sha256=ZERO_SHA,
        source_id_interface_sha256=ONE_SHA,
        context_length=9,
        quantization="clip_[0,1];multiply_255;rint_ties_to_even;uint8",
        consumer_order=("semantic", "latent"),
        semantic_calls=1,
        latent_calls=1,
        semantic_tensor_sha256=content_sha,
        latent_tensor_sha256=content_sha,
        initial_noise_sha256=TWO_SHA,
        rng_state_sha256=ZERO_SHA,
        target_roster_sha256=ONE_SHA,
        trace_schema_sha256=TWO_SHA,
    )


class TestTypedOutputAndUnits(unittest.TestCase):
    def test_output_functions_reject_float_list_and_wrong_integer_dtype(self) -> None:
        u8 = _native_constant(0)
        for bad in (u8.astype(np.float64), u8.astype(np.uint16), u8.tolist()):
            with self.assertRaisesRegex(ref.SpecError, "uint8|numpy"):
                ref.direct_effect_map(bad, u8)
            with self.assertRaisesRegex(ref.SpecError, "uint8|numpy"):
                ref.normalized_rgb_mse(
                    bad,
                    u8,
                    np.ones((ref.NATIVE_HEIGHT, ref.NATIVE_WIDTH), dtype=bool),
                )

    def test_exact_one_code_effect_has_no_second_division(self) -> None:
        zero = _native_constant(0)
        one_all = np.ones_like(zero)
        one_channel = zero.copy()
        one_channel[..., 0] = 1
        np.testing.assert_allclose(ref.direct_effect_map(one_all, zero), 1.0 / 255.0, rtol=0.0, atol=0.0)
        np.testing.assert_allclose(ref.direct_effect_map(one_channel, zero), 1.0 / (3.0 * 255.0), rtol=0.0, atol=1e-18)

    def test_exact_one_code_mse_and_benefit_domain(self) -> None:
        reference = _native_constant(0)
        one = np.ones_like(reference)
        valid = np.ones((ref.NATIVE_HEIGHT, ref.NATIVE_WIDTH), dtype=bool)
        support = np.ones((ref.NATIVE_HEIGHT, ref.NATIVE_WIDTH), dtype=np.float64)
        expected = 1.0 / (255.0 * 255.0)
        self.assertAlmostEqual(ref.normalized_rgb_mse(one, reference, valid), expected, places=18)
        self.assertAlmostEqual(ref.local_benefit(one, reference, reference, valid, support), expected, places=18)
        self.assertAlmostEqual(ref.matched_benefit(one, reference, reference, valid, support), expected, places=18)

    def test_benefit_and_outside_boundary_equalities_pass(self) -> None:
        self.assertEqual(ref.benefit_decision(ref.DELTA_B, ref.DELTA_OUT), (True, ()))
        passed, reasons = ref.benefit_decision(ref.DELTA_B - 1e-12, ref.DELTA_OUT + 1e-12)
        self.assertFalse(passed)
        self.assertEqual(reasons, ("BENEFIT_BELOW_DELTA_B", "OUTSIDE_NONINFERIORITY_FAILED"))

    def test_public_native_guard_rejects_non_native_or_float(self) -> None:
        support = _support()
        with self.assertRaises(ref.SpecError):
            ref.arm_guard_metrics(np.zeros((32, 32, 3), dtype=np.uint8), np.zeros((32, 32, 3), dtype=np.uint8), support)
        with self.assertRaises(ref.SpecError):
            ref.arm_guard_metrics(np.zeros((576, 576, 3), dtype=np.float64), np.zeros((576, 576, 3), dtype=np.uint8), support)


class TestHistogramAndValidity(unittest.TestCase):
    def test_histogram_formula_places_every_decimal_boundary_in_upper_bin(self) -> None:
        for index in range(1, 10):
            histogram = ref.positive_weight_histogram(np.asarray([[index / 10.0]], dtype=np.float64))
            expected = np.zeros(10, dtype=np.float64)
            expected[index] = 1.0
            np.testing.assert_array_equal(histogram, expected)
        histogram = ref.positive_weight_histogram(np.asarray([[1.0]], dtype=np.float64))
        expected = np.zeros(10, dtype=np.float64)
        expected[9] = 1.0
        np.testing.assert_array_equal(histogram, expected)

    def test_histogram_excludes_zero(self) -> None:
        values = np.asarray([[0.0, 0.05, 0.1, 1.0]], dtype=np.float64)
        expected = np.zeros(10)
        expected[0] = expected[1] = expected[9] = 1.0 / 3.0
        np.testing.assert_allclose(ref.positive_weight_histogram(values), expected, atol=0.0, rtol=0.0)

    def test_validity_is_strict_bool(self) -> None:
        values = np.ones((2, 2), dtype=np.float64)
        weight = np.ones((2, 2), dtype=np.float64)
        for bad in (np.ones((2, 2), dtype=np.uint8), np.ones((2, 2), dtype=np.float64), [[True, True], [True, True]]):
            with self.assertRaisesRegex(ref.SpecError, "dtype exactly bool"):
                ref.context_descriptor(values, bad, weight)

    def test_topology_stays_four_connected(self) -> None:
        weight = np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=np.float64)
        self.assertEqual(ref.connected_components4(weight), 2)
        self.assertEqual(ref.exposed_edge_perimeter(np.asarray([[1.0, 1.0]])), 6)


class TestSourceEditPath(unittest.TestCase):
    def test_zero_dose_uses_same_api_for_every_family_and_sign(self) -> None:
        source = np.arange(9 * 11 * 3, dtype=np.uint16).reshape(9, 11, 3).astype(np.uint8)
        for family in ("exposure_log_gain", "texture_highpass"):
            for sign in (-1, 1):
                bundle = ref.apply_source_bundle(source, family, sign, 0.0)
                np.testing.assert_array_equal(bundle.encoded_u8, source)
                self.assertEqual(bundle.stage_order, ref.SOURCE_STAGE_ORDER)
                self.assertEqual(bundle.consumer_order, ("semantic", "latent"))
                self.assertRegex(bundle.semantic_tensor_sha256, r"^[0-9a-f]{64}$")
                self.assertRegex(bundle.latent_tensor_sha256, r"^[0-9a-f]{64}$")

    def test_repeated_zero_is_bitwise_deterministic(self) -> None:
        source = np.random.default_rng(7).integers(0, 256, size=(7, 8, 3), dtype=np.uint8)
        first = ref.apply_source_bundle(source, "texture_highpass", -1, 0.0)
        second = ref.apply_source_bundle(source.copy(), "texture_highpass", -1, 0)
        np.testing.assert_array_equal(first.encoded_u8, second.encoded_u8)
        np.testing.assert_array_equal(first.semantic_tensor.view(np.uint8), second.semantic_tensor.view(np.uint8))
        np.testing.assert_array_equal(first.latent_tensor.view(np.uint8), second.latent_tensor.view(np.uint8))
        self.assertEqual(first.semantic_tensor_sha256, second.semantic_tensor_sha256)
        self.assertEqual(first.latent_tensor_sha256, second.latent_tensor_sha256)

    def test_quantization_clips_then_rounds_half_to_even(self) -> None:
        values = np.asarray([-1.0, 0.5 / 255.0, 1.5 / 255.0, 2.5 / 255.0, 254.5 / 255.0, 2.0])
        np.testing.assert_array_equal(ref.quantize_unit_float_ties_to_even(values), np.asarray([0, 0, 2, 2, 254, 255], dtype=np.uint8))

    def test_nonzero_edit_changes_both_consumer_hashes(self) -> None:
        source = np.random.default_rng(9).integers(32, 224, size=(9, 9, 3), dtype=np.uint8)
        zero = ref.apply_source_bundle(source, "exposure_log_gain", 1, 0.0)
        edit = ref.apply_source_bundle(source, "exposure_log_gain", 1, ref.EXPOSURE_DOSES[-1])
        self.assertNotEqual(zero.encoded_sha256, edit.encoded_sha256)
        self.assertNotEqual(zero.semantic_tensor_sha256, edit.semantic_tensor_sha256)
        self.assertNotEqual(zero.latent_tensor_sha256, edit.latent_tensor_sha256)
        self.assertEqual(zero.stage_order, edit.stage_order)

    def test_minimum_dose_requires_exact_ladder_and_both_signs(self) -> None:
        source = np.random.default_rng(77).integers(64, 192, size=(32, 32, 3), dtype=np.uint8)
        external = {
            (dose, sign): {"clip_cosine": 1.0, "lpips": 0.0}
            for dose in ref.EXPOSURE_DOSES
            for sign in (-1, 1)
        }
        dose, bundles, metrics = ref.select_minimum_source_dose(source, "exposure_log_gain", external)
        self.assertEqual(dose, ref.EXPOSURE_DOSES[0])
        self.assertEqual(set(bundles), {-1, 1})
        self.assertTrue(all(ref.source_edit_gate(metrics[sign])[0] for sign in (-1, 1)))
        incomplete = dict(external)
        incomplete.pop((ref.EXPOSURE_DOSES[-1], 1))
        with self.assertRaisesRegex(ref.SpecError, "exact dose/sign ladder"):
            ref.select_minimum_source_dose(source, "exposure_log_gain", incomplete)

    def test_nonladder_and_noninteger_sign_fail(self) -> None:
        source = np.zeros((5, 5, 3), dtype=np.uint8)
        with self.assertRaises(ref.SpecError):
            ref.apply_source_bundle(source, "exposure_log_gain", 1, 0.123)
        with self.assertRaises(ref.SpecError):
            ref.apply_source_bundle(source, "exposure_log_gain", True, 0.0)


class TestInfluenceAndLocalization(unittest.TestCase):
    def test_uniform_direct_effect_returns_to_area_baseline(self) -> None:
        effect = np.full((64, 64), 8.0 / 255.0, dtype=np.float64)
        support = np.zeros((64, 64), dtype=np.float64)
        support[:16] = 1.0
        metrics = ref.localization_metrics(effect, support)
        self.assertAlmostEqual(metrics.mass, metrics.area, places=12)
        self.assertAlmostEqual(metrics.l_area, 0.0, places=12)
        self.assertAlmostEqual(metrics.enrichment_ratio, 1.0, places=12)

    def test_v5_actual_8bit_false_localization_counterexample_permanently_fails(self) -> None:
        height = width = 576
        rows, cols = np.indices((height, width))
        base_gray = (80 + ((17 * rows + 31 * cols) % 96)).astype(np.uint8)
        zero = np.repeat(base_gray[..., None], 3, axis=2)
        edit = zero.astype(np.int16)
        edit += np.asarray([8, -5, 4], dtype=np.int16)
        edit = edit.astype(np.uint8)
        negative_zero = zero.copy()
        negative_edit = negative_zero.astype(np.int16)
        outside = np.ones((height, width), dtype=bool)
        outside[:86] = False
        negative_edit[outside] += np.asarray([1, -1, 1], dtype=np.int16)
        negative_edit = negative_edit.astype(np.uint8)
        support = np.zeros((height, width), dtype=np.float64)
        support[:86] = 1.0
        target_effect = ref.direct_effect_map(edit, zero)
        negative_effect = ref.direct_effect_map(negative_edit, negative_zero)
        passed, reasons, evidence = ref.localization_decision(
            target_effect, negative_effect, support,
            influence_passed=True, shape_tail=_tail(), camera_tail=_tail(),
        )
        self.assertFalse(passed)
        self.assertIn("TARGET_L_AREA_BELOW_MIN", reasons)
        self.assertAlmostEqual(evidence["target_l_area"], 0.0, places=12)

    def test_negative_is_independent_veto_and_never_changes_target_map(self) -> None:
        effect = np.full((32, 32), 1.0 / 255.0)
        effect[:8] = 8.0 / 255.0
        support = np.zeros((32, 32))
        support[:8] = 1.0
        negative = np.zeros((32, 32))
        negative[:8] = 4.0 / 255.0
        passed, reasons, evidence = ref.localization_decision(effect, negative, support, influence_passed=True, shape_tail=_tail(), camera_tail=_tail())
        self.assertFalse(passed)
        self.assertIn("NEGATIVE_SUPPORT_LOCALIZATION_ABOVE_MAX", reasons)
        self.assertGreater(evidence["negative_l_area_same_support"], 0.01)

    def test_influence_uses_full_frame_negative_and_replay_only(self) -> None:
        target = np.full((4, 4), 4.0 / 255.0)
        negative = np.full((4, 4), 1.0 / 255.0)
        self.assertAlmostEqual(ref.influence_value(target, 1e-6, negative), 3.0 / 255.0)


class TestReplayReceipts(unittest.TestCase):
    def test_exact_six_canonical_pairs_produce_componentwise_floors(self) -> None:
        receipts = _replay_receipts()
        receipts[-1] = replace(receipts[-1], metrics=_guard_metrics(global_median_px=1.0, global_p95_px=2.0, outside_rgb_difference=0.01))
        floors = ref.replay_guard_floors(receipts, seed="seed-1", target="target-1")
        self.assertEqual(floors.global_median_px, 1.0)
        self.assertEqual(floors.global_p95_px, 2.0)
        self.assertEqual(floors.outside_rgb_difference, 0.01)

    def test_duplicate_missing_reversed_and_mixed_identity_fail(self) -> None:
        receipts = _replay_receipts()
        attacks = (
            receipts[:-1] + [receipts[0]],
            receipts[:-1],
            [replace(receipts[0], replay_i=1, replay_j=0)] + receipts[1:],
            [replace(receipts[0], seed="other")] + receipts[1:],
            [replace(receipts[0], target="other")] + receipts[1:],
        )
        for attack in attacks:
            with self.assertRaises(ref.SpecError):
                ref.replay_guard_floors(attack, seed="seed-1", target="target-1")

    def test_nan_domain_and_p95_below_median_fail(self) -> None:
        for metric in (
            _guard_metrics(outside_rgb_difference=float("nan")),
            _guard_metrics(global_median_px=2.0, global_p95_px=1.0),
        ):
            receipts = _replay_receipts(metric)
            with self.assertRaises(ref.SpecError):
                ref.replay_guard_floors(receipts, seed="seed-1", target="target-1")


class TestAdversarialArmGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.base = _native_textured()
        cls.support = _support()

    def test_identical_uint8_outputs_pass_and_metrics_are_symmetric(self) -> None:
        ab = ref.arm_guard_metrics(self.base, self.base.copy(), self.support)
        ba = ref.arm_guard_metrics(self.base.copy(), self.base, self.support)
        self.assertEqual(ab, ba)
        self.assertEqual(ref.arm_guard_decision(ab, _floors()), (True, ()))

    def test_support_local_shift_is_caught(self) -> None:
        shifted = self.base.copy()
        shifted[192:384, 192:384] = np.roll(self.base[192:384, 192:384], 6, axis=1)
        metrics = ref.arm_guard_metrics(self.base, shifted, self.support)
        self.assertEqual(metrics, ref.arm_guard_metrics(shifted, self.base, self.support))
        passed, reasons = ref.arm_guard_decision(metrics, _floors())
        self.assertFalse(passed)
        self.assertTrue(any("SUPPORT" in reason for reason in reasons), reasons)

    def test_periodic_tile_with_local_shift_is_caught(self) -> None:
        tile = np.random.default_rng(11).integers(48, 208, size=(32, 32, 3), dtype=np.uint8)
        periodic = np.tile(tile, (18, 18, 1))
        shifted = periodic.copy()
        shifted[192:384, 192:384] = np.roll(periodic[192:384, 192:384], 6, axis=0)
        metrics = ref.arm_guard_metrics(periodic, shifted, self.support)
        passed, reasons = ref.arm_guard_decision(metrics, _floors())
        self.assertFalse(passed)
        self.assertTrue(any("SUPPORT" in reason for reason in reasons), reasons)

    def test_pure_chroma_outside_change_is_caught(self) -> None:
        base = self.base.copy()
        candidate = base.astype(np.int16)
        outside = self.support == 0.0
        candidate[..., 0][outside] += 3
        candidate[..., 1][outside] -= 3
        candidate = np.clip(candidate, 0, 255).astype(np.uint8)
        metrics = ref.arm_guard_metrics(base, candidate, self.support)
        self.assertLessEqual(metrics.outside_rgb_difference, ref.GUARD_RGB_FLOOR + 1e-12)
        self.assertGreater(metrics.outside_chroma_difference, ref.GUARD_CHROMA_FLOOR)
        passed, reasons = ref.arm_guard_decision(metrics, _floors())
        self.assertFalse(passed)
        self.assertIn("OUTSIDE_CHROMA_DIFFERENCE_ABOVE_MAX", reasons)

    def test_low_texture_frame_fails_match_coverage(self) -> None:
        flat = np.full((576, 576, 3), 128, dtype=np.uint8)
        metrics = ref.arm_guard_metrics(flat, flat.copy(), self.support)
        passed, reasons = ref.arm_guard_decision(metrics, _floors())
        self.assertFalse(passed)
        self.assertIn("GLOBAL_MATCH_COUNT_BELOW_MIN", reasons)
        self.assertIn("SUPPORT_GRID_COVERAGE_BELOW_MIN", reasons)


class TestSynchronizationCameraAndReference(unittest.TestCase):
    def test_sensor_sync_formula_uses_exact_half_even_integer_rounding(self) -> None:
        even = _calibration(drift_ppb=500_000_000)
        odd = _calibration(drift_ppb=500_000_000, t0_sensor_ns=0)
        self.assertEqual(ref.calibrated_timestamp_ns(1, even), 1)
        self.assertEqual(ref.calibrated_timestamp_ns(3, odd), 5)
        with self.assertRaisesRegex(ref.SpecError, "residual"):
            ref.calibrated_timestamp_ns(1, _calibration(measured_residuals_ns=(10_000_001,)))

    def test_exact_target_camera_and_boundary_equalities_pass(self) -> None:
        target = _camera()
        ordinary = _camera((10.0, 0.0, 0.0))
        exact = ref.camera_match_metrics(target, ordinary, _camera())
        self.assertEqual(exact.position_ratio_ppm, 0)
        boundary = ref.camera_match_metrics(target, ordinary, _camera((1.0, 0.0, 0.0), angle_degrees=2.0, fov=61.0))
        self.assertEqual(boundary.position_ratio_ppm, 100_000)
        self.assertEqual(boundary.angle_microdegrees, 2_000_000)
        self.assertEqual(boundary.fov_microdegrees, 1_000_000)
        candidate = _candidate(
            "boundary",
            ONE_SHA,
            camera=_camera((1.0, 0.0, 0.0), angle_degrees=2.0, fov=61.0),
        )
        selected = ref.select_reference(
            [candidate],
            target_timestamp_ns=1_000_000_000,
            target_calibration=_calibration(),
            target_scene_id="scene",
            target_camera=target,
            ordinary_camera=ordinary,
        )
        self.assertEqual(selected["selected"].candidate_id, "boundary")

    def test_reference_tie_is_broken_by_file_sha_then_id(self) -> None:
        candidates = [_candidate("z", TWO_SHA), _candidate("a", ONE_SHA), _candidate("b", ONE_SHA)]
        result = ref.select_reference(candidates, target_timestamp_ns=1_000_000_000, target_calibration=_calibration(), target_scene_id="scene", target_camera=_camera(), ordinary_camera=_camera((10.0, 0.0, 0.0)))
        self.assertEqual(result["selected"].candidate_id, "a")
        self.assertEqual(result["eligible_order"], ("a", "b", "z"))

    def test_reference_rejects_time_and_scene_failures(self) -> None:
        bad = _candidate("bad", ONE_SHA, scene_id="other", sensor_timestamp_ns=1_020_000_000)
        with self.assertRaisesRegex(ref.SpecError, "no eligible"):
            ref.select_reference([bad], target_timestamp_ns=1_000_000_000, target_calibration=_calibration(), target_scene_id="scene", target_camera=_camera(), ordinary_camera=_camera((10.0, 0.0, 0.0)))


class TestIdentityDomainsAndViewPairs(unittest.TestCase):
    def test_exact_triad_identity_passes_and_swapped_identity_fails(self) -> None:
        support = np.ones((4, 4), dtype=np.float64)
        valid = np.ones((4, 4), dtype=bool)
        identity = np.tile(np.asarray([[0, 1, 1, 2]], dtype=np.int32), (4, 1))
        receipt = ref.identity_agreement({"O": identity, "R": identity.copy(), "P": identity.copy()}, {"O": valid, "R": valid.copy(), "P": valid.copy()}, support, roles=("O", "R", "P"))
        self.assertEqual(ref.identity_decision(receipt), (True, ()))
        swapped = identity.copy()
        swapped[identity == 1] = 2
        swapped[identity == 2] = 1
        attack = ref.identity_agreement({"O": identity, "R": identity, "P": swapped}, {"O": valid, "R": valid, "P": valid}, support, roles=("O", "R", "P"))
        passed, reasons = ref.identity_decision(attack)
        self.assertFalse(passed)
        self.assertIn("IDENTITY_AGREEMENT_BELOW_MIN", reasons)

    def test_invalid_identity_pixels_are_excluded_and_coverage_reported(self) -> None:
        support = np.ones((10, 10), dtype=np.float64)
        ids = np.ones((10, 10), dtype=np.int16)
        valid = np.ones((10, 10), dtype=bool)
        valid[:2] = False
        receipt = ref.identity_agreement({"O": ids, "R": ids}, {"O": valid, "R": valid}, support, roles=("O", "R"))
        self.assertEqual(receipt.valid_weight, 80.0)
        self.assertEqual(receipt.valid_weight_coverage, 0.8)
        self.assertEqual(receipt.agreement, 1.0)
        with self.assertRaisesRegex(ref.SpecError, "inconsistent"):
            ref.identity_decision(replace(receipt, agreement=0.5))

    def test_partial_visibility_records_exact_hole_counts(self) -> None:
        domain = np.ones((10, 10), dtype=bool)
        valid = np.ones((10, 10), dtype=bool)
        valid[:2] = False
        receipt = ref.valid_domain_receipt("support", domain, {"O": valid, "R": np.ones_like(valid)})
        self.assertEqual((receipt.domain_denominator, receipt.common_valid_numerator, receipt.hole_numerator, receipt.hole_denominator), (100, 80, 20, 100))
        self.assertEqual(ref.valid_domain_decision(receipt)[0], False)
        valid[:2] = True
        valid[0, :9] = False
        passing = ref.valid_domain_receipt("support", domain, {"O": valid, "R": np.ones_like(valid)})
        self.assertEqual(ref.valid_domain_decision(passing), (True, ()))
        with self.assertRaisesRegex(ref.SpecError, "inconsistent"):
            ref.valid_domain_decision(replace(passing, hole_numerator=10))

    def test_empty_outside_domain_is_invalid(self) -> None:
        full_support = np.ones((4, 4), dtype=bool)
        outside = ~full_support
        with self.assertRaisesRegex(ref.SpecError, "empty"):
            ref.valid_domain_receipt("outside", outside, {"O": np.ones_like(outside), "R": np.ones_like(outside)})

    def test_required_view_pair_set_and_channel_boundary(self) -> None:
        zero = _native_constant(0)
        two = np.full_like(zero, 2)
        valid = np.ones((ref.NATIVE_HEIGHT, ref.NATIVE_WIDTH), dtype=bool)
        receipts = [ref.build_view_pair_receipt(label, zero, two, valid) for label in ("O_R", "R_PREV_R", "R_R_NEXT", "P_R")]
        self.assertEqual(ref.validate_view_pair_receipts(receipts, include_replacement=True), (True, ()))
        with self.assertRaises(ref.SpecError):
            ref.validate_view_pair_receipts(receipts[:-1], include_replacement=True)
        three = ref.build_view_pair_receipt("O_R", zero, np.full_like(zero, 3), valid)
        failed, reasons = ref.validate_view_pair_receipts([three] + receipts[1:3], include_replacement=False)
        self.assertFalse(failed)
        self.assertIn("O_R_RGB_MEDIAN_ABOVE_2_CODES", reasons)


class TestMatchedReinsertAndRoster(unittest.TestCase):
    def test_o_reinsert_and_p_share_every_noncontent_invariant(self) -> None:
        ordinary = _reinsert("O_REINSERT", "O", ONE_SHA, "attempt-o", 100)
        replacement = _reinsert("P_REPLACEMENT", "P", TWO_SHA, "attempt-p", 101)
        self.assertEqual(ref.validate_matched_reinsert(ordinary, replacement), (True, ()))

    def test_ordinary_f00_or_rng_mismatch_cannot_be_comparator(self) -> None:
        ordinary = _reinsert("ORDINARY_F00", "O", ONE_SHA, "attempt-o", 100)
        replacement = _reinsert("P_REPLACEMENT", "P", TWO_SHA, "attempt-p", 101)
        passed, reasons = ref.validate_matched_reinsert(ordinary, replacement)
        self.assertFalse(passed)
        self.assertIn("ROLE_MISMATCH", reasons)
        ordinary = replace(ordinary, role="O_REINSERT")
        replacement = replace(replacement, rng_state_sha256=ONE_SHA)
        self.assertFalse(ref.validate_matched_reinsert(ordinary, replacement)[0])

    def test_every_noncontent_reinsert_invariant_is_fail_closed(self) -> None:
        ordinary = _reinsert("O_REINSERT", "O", ONE_SHA, "attempt-o", 100)
        replacement = _reinsert("P_REPLACEMENT", "P", TWO_SHA, "attempt-p", 101)
        for name in ref._REINSERT_INVARIANTS:
            value = getattr(replacement, name)
            if isinstance(value, str):
                alternate = "f" * 64 if name.endswith("sha256") else value + "_different"
            elif type(value) is int:
                alternate = value + 1
            elif name == "consumer_order":
                alternate = tuple(reversed(value))
            else:
                alternate = value + (999,)
            attacked = replace(replacement, **{name: alternate})
            passed, reasons = ref.validate_matched_reinsert(ordinary, attacked)
            self.assertFalse(passed, name)
            self.assertTrue(any(name.upper() in reason for reason in reasons), (name, reasons))

    def test_replacement_time_is_only_integer_insertion_recency(self) -> None:
        self.assertTrue(ref.replacement_recency_eligible(10, 12))
        self.assertFalse(ref.replacement_recency_eligible(10, 13))
        with self.assertRaises(ref.SpecError):
            ref.replacement_recency_eligible(10, 12.0)

    def test_roster_uses_exact_integer_then_utf8_then_sha_order(self) -> None:
        def record(source: str, event: object, **changes: object) -> dict[str, object]:
            out: dict[str, object] = {"insertion_event": event, "source_id": source, "file_sha256": (source.encode().hex() + "0" * 64)[:64], "active": True, "selected": False, "is_target": False, "is_reference": False, "provenance_complete": True, "artifacts_complete": True, "renderable_all_targets": True}
            out.update(changes)
            return out
        roster = ref.build_unselected_source_roster([record("z", 1), record("a", 1), record("old", 0, selected=True)])
        self.assertEqual(roster["eligible_source_ids"], ("a", "z"))
        with self.assertRaises(ref.SpecError):
            ref.build_unselected_source_roster([record("bad", 1.0)])


class TestDeterministicRandomProperties(unittest.TestCase):
    def test_random_native_uint8_effect_and_loss_properties(self) -> None:
        rng = np.random.default_rng(480206)
        valid = np.ones((ref.NATIVE_HEIGHT, ref.NATIVE_WIDTH), dtype=bool)
        for _ in range(OUTPUT_PROPERTY_CASES):
            first = rng.integers(0, 256, size=(ref.NATIVE_HEIGHT, ref.NATIVE_WIDTH, 3), dtype=np.uint8)
            second = rng.integers(0, 256, size=(ref.NATIVE_HEIGHT, ref.NATIVE_WIDTH, 3), dtype=np.uint8)
            observed = ref.direct_effect_map(first, second)
            expected = np.mean(
                np.abs(first.astype(np.float64) / 255.0 - second.astype(np.float64) / 255.0),
                axis=2,
            )
            np.testing.assert_array_equal(observed, expected)
            np.testing.assert_array_equal(observed, ref.direct_effect_map(second, first))
            loss_ab = ref.normalized_rgb_mse(first, second, valid)
            loss_ba = ref.normalized_rgb_mse(second, first, valid)
            self.assertGreaterEqual(loss_ab, 0.0)
            self.assertLessEqual(loss_ab, 1.0)
            self.assertEqual(loss_ab, loss_ba)

    def test_256_random_zero_edits_are_exact_and_deterministic(self) -> None:
        rng = np.random.default_rng(480207)
        families = ("exposure_log_gain", "texture_highpass")
        signs = (-1, 1)
        for index in range(PROPERTY_CASES):
            source = rng.integers(0, 256, size=(3, 3, 3), dtype=np.uint8)
            family = families[index % 2]
            sign = signs[(index // 2) % 2]
            first = ref.apply_source_bundle(source, family, sign, 0.0)
            second = ref.apply_source_bundle(source.copy(), family, sign, 0)
            np.testing.assert_array_equal(first.encoded_u8, source)
            self.assertEqual(first.encoded_sha256, second.encoded_sha256)
            self.assertEqual(first.semantic_tensor_sha256, second.semantic_tensor_sha256)
            self.assertEqual(first.latent_tensor_sha256, second.latent_tensor_sha256)

    def test_256_stable_integer_conversions_are_repeatable(self) -> None:
        rng = np.random.default_rng(480208)
        for _ in range(PROPERTY_CASES):
            value = float(rng.random() * 100.0)
            first = ref.stable_scaled_integer(value, 1_000_000, "value")
            second = ref.stable_scaled_integer(value, 1_000_000, "value")
            self.assertEqual(first, second)
            self.assertGreaterEqual(first, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
