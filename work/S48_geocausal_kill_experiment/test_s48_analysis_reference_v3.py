#!/usr/bin/env python3
"""Synthetic tests for the S48 V7 source-only normative candidate.

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
import s48_analysis_reference_v3 as ref  # noqa: E402


PROPERTY_CASES = 256
OUTPUT_PROPERTY_CASES = 16
ZERO_SHA = "0" * 64
ONE_SHA = "1" * 64
TWO_SHA = "2" * 64
THREE_SHA = "3" * 64
FOUR_SHA = "4" * 64
FIVE_SHA = "5" * 64


def _support() -> np.ndarray:
    support = np.zeros((ref.NATIVE_HEIGHT, ref.NATIVE_WIDTH), dtype=np.float64)
    support[192:384, 192:384] = 1.0
    return support


def _native_textured(seed: int = 481701) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.integers(32, 224, size=(ref.NATIVE_HEIGHT, ref.NATIVE_WIDTH, 3), dtype=np.uint8)


def _native_constant(value: int) -> np.ndarray:
    return np.full((ref.NATIVE_HEIGHT, ref.NATIVE_WIDTH, 3), value, dtype=np.uint8)


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


def _replay_ledger(seed: str = "seed-1", target: str = "target-1", outputs: tuple[np.ndarray, ...] | None = None, support: np.ndarray | None = None) -> ref.ReplayLedger:
    chosen = outputs if outputs is not None else tuple(_native_constant(100) for _ in range(4))
    return ref.build_replay_ledger(
        chosen, _support() if support is None else support, seed=seed, target=target, state_sha256=ZERO_SHA,
        noise_sha256=ONE_SHA, rng_state_sha256=TWO_SHA, snapshot_sha256=THREE_SHA,
        target_roster_sha256=FOUR_SHA,
    )


def _arm_identity() -> ref.ArmIdentityReceipt:
    return ref.build_arm_identity(
        state_sha256=ZERO_SHA, noise_sha256=ONE_SHA, rng_state_sha256=TWO_SHA,
        snapshot_sha256=THREE_SHA, target_roster_sha256=FOUR_SHA,
        source_adapter_sha256=FIVE_SHA, consumer_trace_schema_sha256=ZERO_SHA, slot=0,
    )


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
        "support": ref.valid_domain_receipt("support", small_support > 0.0, {"O": valid, "R": valid}, roles=("O", "R")),
        "outside": ref.valid_domain_receipt("outside", small_support == 0.0, {"O": valid, "R": valid}, roles=("O", "R")),
    }
    values: dict[str, object] = {
        "candidate_id": candidate_id,
        "capture_id": "capture-" + candidate_id,
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


def _exclusion() -> ref.ObservationExclusionLedger:
    return ref.build_observation_exclusion_ledger(
        ref.ObservationIdentity("target-capture", FIVE_SHA),
        (ref.ObservationIdentity("memory-capture", FOUR_SHA),),
        (ref.ObservationIdentity("conditioning-capture", THREE_SHA),),
    )


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


class _SparseMaskSequence:
    """Indexable native masks generated one at a time to keep the test finite."""

    def __init__(self, count: int = 199, row: int = 0) -> None:
        self.count = count
        self.row = row

    def __len__(self) -> int:
        return self.count

    def __getitem__(self, index: int) -> np.ndarray:
        if not 0 <= index < self.count:
            raise IndexError(index)
        out = np.zeros((ref.NATIVE_HEIGHT, ref.NATIVE_WIDTH), dtype=np.float64)
        out[self.row, index] = 1.0
        return out


def _placebo_ledgers(count: int = 199) -> tuple[ref.PlaceboMaskLedger, ref.PlaceboMaskLedger]:
    return (
        ref.build_placebo_mask_ledger(_SparseMaskSequence(count, 0), family="shape", generator_sha256=ONE_SHA),
        ref.build_placebo_mask_ledger(_SparseMaskSequence(count, 1), family="camera", generator_sha256=TWO_SHA),
    )


def _influence(key: ref.CellKey, *, observable: bool = True, positive: bool = True) -> ref.InfluenceReceipt:
    zero = _native_constant(100)
    edit = zero.copy()
    if observable:
        edit[192:384, 192:384] = 108
    positive_edit = zero.copy()
    if positive:
        positive_edit[:] = 104
    replay = _replay_ledger(key.seed, key.target)
    return ref.build_influence_receipt(
        edit, zero, zero.copy(), zero.copy(), positive_edit, zero.copy(),
        key=key, replay=replay, arm_identity=_arm_identity(),
    )


def _reference_roster(extra: tuple[ref.ReferenceCandidate, ...] = ()) -> ref.ReferenceRosterReceipt:
    candidates = (
        _candidate("r0", ZERO_SHA),
        _candidate("r1", ONE_SHA),
        _candidate("r2", TWO_SHA),
        *extra,
    )
    return ref.select_reference_roster(
        candidates,
        target_timestamp_ns=1_000_000_000,
        target_calibration=_calibration(),
        target_scene_id="scene",
        target_camera=_camera(),
        ordinary_camera=_camera((10.0, 0.0, 0.0)),
        exclusion_ledger=_exclusion(),
    )


def _reference_uncertainty() -> ref.ReferenceUncertaintyReceipt:
    roster = _reference_roster()
    references = {capture: _native_constant(0) for capture in roster.eligible_capture_ids}
    validities = {capture: np.ones((ref.NATIVE_HEIGHT, ref.NATIVE_WIDTH), dtype=bool) for capture in roster.eligible_capture_ids}
    return ref.build_reference_uncertainty(roster, references, validities, _support())


def _replacement_evidence() -> tuple[ref.QualityCalibrationReceipt, ref.ReplacementCandidate, ref.ReplacementRosterReceipt]:
    support = _support()
    valid = np.ones((ref.NATIVE_HEIGHT, ref.NATIVE_WIDTH), dtype=bool)
    ids = np.zeros((ref.NATIVE_HEIGHT, ref.NATIVE_WIDTH), dtype=np.int16)
    identity = ref.identity_agreement(
        {"O": ids, "R": ids.copy(), "P": ids.copy()},
        {"O": valid, "R": valid.copy(), "P": valid.copy()},
        support,
        roles=("O", "R", "P"),
    )
    views = tuple(
        ref.ViewPairReceipt(label, ref.NATIVE_HEIGHT * ref.NATIVE_WIDTH, (0.0, 0.0, 0.0))
        for label in ("O_R", "R_PREV_R", "R_R_NEXT", "P_R")
    )
    domains = {
        "support": ref.valid_domain_receipt("support", support > 0.0, {"O": valid, "R": valid.copy(), "P": valid.copy()}, roles=("O", "R", "P")),
        "outside": ref.valid_domain_receipt("outside", support == 0.0, {"O": valid, "R": valid.copy(), "P": valid.copy()}, roles=("O", "R", "P")),
    }
    candidate = ref.build_replacement_candidate(
        source_id="P1", file_sha256=ONE_SHA, insertion_event=11, scene_id="scene",
        camera=_camera(), support=support, source_quality=0.35,
        identity_receipt=identity, view_pair_receipts=views, domain_receipts=domains,
    )
    calibration = ref.build_quality_calibration([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8], cal_manifest_sha256=TWO_SHA)
    roster = ref.build_replacement_roster(
        [candidate], ordinary_source_id="O", ordinary_insertion_event=10,
        ordinary_scene_id="scene", target_camera=_camera(), ordinary_camera=_camera((10.0, 0.0, 0.0)),
        ordinary_support=support, ordinary_source_quality=0.35, quality_calibration=calibration,
    )
    return calibration, candidate, roster


def _clone_influence(base: ref.InfluenceReceipt, key: ref.CellKey) -> ref.InfluenceReceipt:
    provisional = replace(base, key=key, canonical_sha256=ZERO_SHA)
    return replace(
        provisional,
        canonical_sha256=ref._canonical_lines_sha(
            "S48_INFLUENCE_RECEIPT_V3", ref._influence_hash_lines(provisional)
        ),
    )


def _influence_grid(*, observable: bool = False) -> tuple[ref.InfluenceReceipt, ...]:
    out: list[ref.InfluenceReceipt] = []
    for seed in ("s0", "s1", "s2", "s3", "s4"):
        base_key = ref.CellKey("O", "T", seed, "exposure_log_gain", -1)
        base = _influence(base_key, observable=observable)
        for family in ("exposure_log_gain", "texture_highpass"):
            for sign in (-1, 1):
                key = ref.CellKey("O", "T", seed, family, sign)
                out.append(base if key == base_key else _clone_influence(base, key))
    return tuple(out)


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

    def test_exact_one_code_mse_and_three_distinct_utility_estimands(self) -> None:
        reference = _native_constant(0)
        one = np.ones_like(reference)
        valid = np.ones((ref.NATIVE_HEIGHT, ref.NATIVE_WIDTH), dtype=bool)
        support = np.ones((ref.NATIVE_HEIGHT, ref.NATIVE_WIDTH), dtype=np.float64)
        expected = 1.0 / (255.0 * 255.0)
        self.assertAlmostEqual(ref.normalized_rgb_mse(one, reference, valid), expected, places=18)
        self.assertAlmostEqual(ref.local_edit_preference(one, reference, reference, valid, support), expected, places=18)
        self.assertAlmostEqual(ref.matched_replacement_utility(one, reference, reference, valid, support), expected, places=18)
        self.assertAlmostEqual(ref.source_absence_utility(one, reference, reference, valid, support), expected, places=18)

    def test_free_benefit_scalar_and_numeric_string_are_rejected(self) -> None:
        with self.assertRaisesRegex(ref.SpecError, "forbids free utility"):
            ref.benefit_decision(ref.DELTA_B, ref.DELTA_OUT)
        with self.assertRaisesRegex(ref.SpecError, "finite real scalar"):
            ref._finite("0.001", "attack")

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
    @classmethod
    def setUpClass(cls) -> None:
        cls.shape_ledger, cls.camera_ledger = _placebo_ledgers()
        cls.key = ref.CellKey("O", "target-1", "seed-1", "exposure_log_gain", 1)
        cls.influence = _influence(cls.key)
        cls.receipt = ref.support_effect_decision(
            _support(), influence=cls.influence,
            shape_ledger=cls.shape_ledger, camera_ledger=cls.camera_ledger,
        )

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
        key = ref.CellKey("O", "uniform-target", "seed-u", "exposure_log_gain", 1)
        influence = ref.build_influence_receipt(
            edit, zero, negative_edit, negative_zero, np.clip(zero.astype(np.int16) + 4, 0, 255).astype(np.uint8), zero,
            key=key, replay=_replay_ledger(key.seed, key.target, support=support), arm_identity=_arm_identity(),
        )
        receipt = ref.support_effect_decision(
            support, influence=influence,
            shape_ledger=self.shape_ledger, camera_ledger=self.camera_ledger,
        )
        self.assertFalse(receipt.alignment_passed)
        self.assertIn("TARGET_L_AREA_BELOW_MIN", receipt.reasons)
        self.assertAlmostEqual(receipt.target_l_area, 0.0, places=12)

    def test_negative_is_independent_veto_and_never_changes_target_map(self) -> None:
        effect = np.full((32, 32), 1.0 / 255.0)
        effect[:8] = 8.0 / 255.0
        support = np.zeros((32, 32))
        support[:8] = 1.0
        negative = np.zeros((32, 32))
        negative[:8] = 4.0 / 255.0
        zero = _native_constant(100)
        edit = zero.copy()
        edit[192:384, 192:384] = 108
        negative_edit = zero.copy()
        negative_edit[192:384, 192:384] = 104
        key = ref.CellKey("O", "negative-target", "seed-n", "exposure_log_gain", 1)
        influence = ref.build_influence_receipt(
            edit, zero, negative_edit, zero, _native_constant(104), zero,
            key=key, replay=_replay_ledger(key.seed, key.target), arm_identity=_arm_identity(),
        )
        receipt = ref.support_effect_decision(
            _support(), influence=influence,
            shape_ledger=self.shape_ledger, camera_ledger=self.camera_ledger,
        )
        self.assertFalse(receipt.alignment_passed)
        self.assertIn("NEGATIVE_SUPPORT_LOCALIZATION_ABOVE_MAX", receipt.reasons)
        self.assertGreater(receipt.negative_l_area_same_support, 0.01)

    def test_influence_is_derived_from_bound_outputs_and_replay(self) -> None:
        self.assertFalse(hasattr(ref, "influence_value"))
        self.assertAlmostEqual(self.influence.target_effect_mean, (1.0 / 9.0) * 8.0 / 255.0)
        self.assertAlmostEqual(self.influence.target_d, self.influence.target_effect_mean - 1.0e-6)
        attacked = replace(self.influence, target_d=1.0)
        with self.assertRaisesRegex(ref.SpecError, "inconsistent"):
            ref.validate_influence_receipt(attacked)

    def test_tail_is_recomputed_from_bound_mask_ledger(self) -> None:
        self.assertTrue(self.receipt.alignment_passed, self.receipt.reasons)
        forged_tail = replace(self.receipt.shape_tail, true_mass=0.0)
        attacked = replace(self.receipt, shape_tail=forged_tail)
        with self.assertRaisesRegex(ref.SpecError, "injected|stale|scalars"):
            ref.validate_support_effect_receipt(attacked)

    def test_placebo_mask_bytes_and_order_are_bound(self) -> None:
        blobs = list(self.shape_ledger.compressed_masks)
        blobs[0], blobs[1] = blobs[1], blobs[0]
        attacked = replace(self.shape_ledger, compressed_masks=tuple(blobs))
        with self.assertRaises(ref.SpecError):
            ref.validate_placebo_mask_ledger(attacked, family="shape", shape=(ref.NATIVE_HEIGHT, ref.NATIVE_WIDTH))

    def test_too_few_placebos_fail_closed(self) -> None:
        short_shape, short_camera = _placebo_ledgers(19)
        receipt = ref.support_effect_decision(
            _support(), influence=self.influence,
            shape_ledger=short_shape, camera_ledger=short_camera,
        )
        self.assertFalse(receipt.alignment_passed)
        self.assertIn("SHAPE_PLACEBO_COUNT_BELOW_199", receipt.reasons)


class TestReplayReceipts(unittest.TestCase):
    def test_exact_six_canonical_pairs_produce_componentwise_floors(self) -> None:
        ledger = _replay_ledger()
        floors = ref.replay_guard_floors(ledger)
        self.assertEqual(len(ledger.instances), 4)
        self.assertEqual(len(ledger.pairs), 6)
        self.assertEqual(floors.global_median_px, 0.0)
        self.assertEqual(ledger.tau_output, 1.0e-6)

    def test_duplicate_missing_reversed_and_mixed_identity_fail(self) -> None:
        ledger = _replay_ledger()
        pairs = ledger.pairs
        attacks = (
            replace(ledger, pairs=pairs[:-1] + (pairs[0],)),
            replace(ledger, pairs=pairs[:-1]),
            replace(ledger, pairs=(replace(pairs[0], replay_i=1, replay_j=0),) + pairs[1:]),
            replace(ledger, pairs=(replace(pairs[0], seed="other"),) + pairs[1:]),
            replace(ledger, pairs=(pairs[1], pairs[0], *pairs[2:])),
        )
        for attack in attacks:
            with self.assertRaises(ref.SpecError):
                ref.replay_guard_floors(attack)

    def test_full_frame_distance_cannot_be_forged(self) -> None:
        ledger = _replay_ledger(outputs=(_native_constant(100), _native_constant(101), _native_constant(100), _native_constant(100)))
        pair = replace(ledger.pairs[0], full_frame_distance=0.0)
        with self.assertRaisesRegex(ref.SpecError, "bound outputs"):
            ref.validate_replay_ledger(replace(ledger, pairs=(pair, *ledger.pairs[1:])))

    def test_output_identity_and_read_only_evidence_cannot_be_swapped(self) -> None:
        ledger = _replay_ledger(outputs=(_native_constant(100), _native_constant(101), _native_constant(102), _native_constant(103)))
        attacked_pair = replace(ledger.pairs[0], output_i_sha256=ledger.instances[2].output_sha256)
        with self.assertRaisesRegex(ref.SpecError, "output identity"):
            ref.validate_replay_ledger(replace(ledger, pairs=(attacked_pair, *ledger.pairs[1:])))
        mutable = ledger.instances[0].output_u8.copy()
        attacked_instance = replace(ledger.instances[0], output_u8=mutable)
        with self.assertRaisesRegex(ref.SpecError, "read-only"):
            ref.validate_replay_ledger(replace(ledger, instances=(attacked_instance, *ledger.instances[1:])))

    def test_guard_metric_and_support_attacks_fail_recomputation(self) -> None:
        ledger = _replay_ledger()
        forged_metric = replace(ledger.pairs[0].metrics, outside_rgb_difference=0.01)
        forged_pair = replace(ledger.pairs[0], metrics=forged_metric)
        with self.assertRaises(ref.SpecError):
            ref.validate_replay_ledger(replace(ledger, pairs=(forged_pair, *ledger.pairs[1:])))
        mutable_support = ledger.support.copy()
        with self.assertRaisesRegex(ref.SpecError, "read-only"):
            ref.validate_replay_ledger(replace(ledger, support=mutable_support))


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
        candidates = [
            _candidate("boundary", ZERO_SHA, camera=_camera((1.0, 0.0, 0.0), angle_degrees=2.0, fov=61.0)),
            _candidate("r1", ONE_SHA),
            _candidate("r2", TWO_SHA),
        ]
        selected = ref.select_reference_roster(
            candidates,
            target_timestamp_ns=1_000_000_000,
            target_calibration=_calibration(),
            target_scene_id="scene",
            target_camera=target,
            ordinary_camera=ordinary,
            exclusion_ledger=_exclusion(),
        )
        self.assertIn("boundary", selected.eligible_candidate_ids)
        self.assertEqual(len(selected.eligible_candidate_ids), 3)

    def test_reference_order_is_stable_and_duplicate_file_is_rejected(self) -> None:
        candidates = [_candidate("z", TWO_SHA), _candidate("a", ZERO_SHA), _candidate("b", ONE_SHA)]
        result = ref.select_reference_roster(candidates, target_timestamp_ns=1_000_000_000, target_calibration=_calibration(), target_scene_id="scene", target_camera=_camera(), ordinary_camera=_camera((10.0, 0.0, 0.0)), exclusion_ledger=_exclusion())
        self.assertEqual(result.eligible_candidate_ids, ("a", "b", "z"))
        with self.assertRaisesRegex(ref.SpecError, "duplicate"):
            ref.select_reference_roster([*candidates, _candidate("copy", ONE_SHA)], target_timestamp_ns=1_000_000_000, target_calibration=_calibration(), target_scene_id="scene", target_camera=_camera(), ordinary_camera=_camera((10.0, 0.0, 0.0)), exclusion_ledger=_exclusion())

    def test_reference_rejects_time_and_scene_failures(self) -> None:
        bad = _candidate("bad", ONE_SHA, scene_id="other", sensor_timestamp_ns=1_020_000_000)
        with self.assertRaisesRegex(ref.SpecError, "at least three"):
            ref.select_reference_roster([bad], target_timestamp_ns=1_000_000_000, target_calibration=_calibration(), target_scene_id="scene", target_camera=_camera(), ordinary_camera=_camera((10.0, 0.0, 0.0)), exclusion_ledger=_exclusion())

    def test_reference_target_memory_and_conditioning_leakage_are_excluded(self) -> None:
        extra = (
            _candidate("target-copy", FIVE_SHA, capture_id="different-capture"),
            _candidate("memory-copy", FOUR_SHA),
            _candidate("conditioning-copy", THREE_SHA),
        )
        roster = _reference_roster(extra)
        reasons = {record.candidate_id: record.reasons for record in roster.flow}
        self.assertIn("TARGET_CAPTURE_OR_FILE_REUSE", reasons["target-copy"])
        self.assertIn("REFERENCE_ENTERED_MEMORY", reasons["memory-copy"])
        self.assertIn("REFERENCE_ENTERED_CONDITIONING", reasons["conditioning-copy"])
        self.assertEqual(roster.eligible_candidate_ids, ("r0", "r1", "r2"))

    def test_single_reference_api_is_permanently_forbidden(self) -> None:
        with self.assertRaisesRegex(ref.SpecError, "at least three"):
            ref.select_reference([_candidate("one", ONE_SHA)])

    def test_roster_validator_binds_exclusion_ledger(self) -> None:
        roster = _reference_roster()
        attacked = replace(roster, exclusion_ledger_sha256=THREE_SHA)
        with self.assertRaisesRegex(ref.SpecError, "bind"):
            ref.validate_reference_roster_receipt(attacked)


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
        receipt = ref.valid_domain_receipt("support", domain, {"O": valid, "R": np.ones_like(valid)}, roles=("O", "R"))
        self.assertEqual((receipt.domain_denominator, receipt.common_valid_numerator, receipt.hole_numerator, receipt.hole_denominator), (100, 80, 20, 100))
        self.assertEqual(ref.valid_domain_decision(receipt, required_roles=("O", "R"))[0], False)
        valid[:2] = True
        valid[0, :9] = False
        passing = ref.valid_domain_receipt("support", domain, {"O": valid, "R": np.ones_like(valid)}, roles=("O", "R"))
        self.assertEqual(ref.valid_domain_decision(passing, required_roles=("O", "R")), (True, ()))
        with self.assertRaisesRegex(ref.SpecError, "inconsistent"):
            ref.valid_domain_decision(replace(passing, hole_numerator=10), required_roles=("O", "R"))

    def test_arbitrary_one_role_receipt_is_rejected(self) -> None:
        domain = np.ones((4, 4), dtype=bool)
        with self.assertRaisesRegex(ref.SpecError, "exactly"):
            ref.valid_domain_receipt("support", domain, {"UNRELATED": domain}, roles=("UNRELATED",))

    def test_bound_validity_mask_cannot_be_replaced(self) -> None:
        domain = np.ones((4, 4), dtype=bool)
        receipt = ref.valid_domain_receipt("support", domain, {"O": domain, "R": domain.copy()}, roles=("O", "R"))
        masks = list(receipt.validity_masks)
        mutable = masks[0][1].copy()
        masks[0] = ("O", mutable)
        with self.assertRaisesRegex(ref.SpecError, "read-only"):
            ref.valid_domain_decision(replace(receipt, validity_masks=tuple(masks)), required_roles=("O", "R"))

    def test_empty_outside_domain_is_invalid(self) -> None:
        full_support = np.ones((4, 4), dtype=bool)
        outside = ~full_support
        with self.assertRaisesRegex(ref.SpecError, "empty"):
            ref.valid_domain_receipt("outside", outside, {"O": np.ones_like(outside), "R": np.ones_like(outside)}, roles=("O", "R"))

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


class TestReplacementEligibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.calibration, cls.candidate, cls.roster = _replacement_evidence()

    def _select(self, candidates: list[ref.ReplacementCandidate]) -> ref.ReplacementRosterReceipt:
        return ref.build_replacement_roster(
            candidates, ordinary_source_id="O", ordinary_insertion_event=10,
            ordinary_scene_id="scene", target_camera=_camera(), ordinary_camera=_camera((10.0, 0.0, 0.0)),
            ordinary_support=_support(), ordinary_source_quality=0.35, quality_calibration=self.calibration,
        )

    def test_full_p_contract_selects_and_binds_candidate(self) -> None:
        self.assertEqual(self.roster.eligible_source_ids, ("P1",))
        ref.validate_replacement_roster_receipt(self.roster)
        self.assertEqual(self.roster.flow[0].support_iou, 1.0)
        self.assertEqual(self.roster.flow[0].weighted_area_ratio, 1.0)

    def test_cal_nearest_rank_cutpoints_and_ties_are_frozen(self) -> None:
        self.assertEqual(self.calibration.cutpoints, (0.2, 0.4, 0.6))
        self.assertEqual(ref.quality_quartile(0.199, self.calibration), 0)
        self.assertEqual(ref.quality_quartile(0.2, self.calibration), 1)
        with self.assertRaises(ref.SpecError):
            ref.build_quality_calibration([0.1] * 7, cal_manifest_sha256=ONE_SHA)

    def test_binary_iou_and_weighted_area_are_distinct(self) -> None:
        ordinary = np.asarray([[1.0, 0.0], [0.0, 0.0]], dtype=np.float64)
        candidate = np.asarray([[0.5, 0.0], [0.0, 0.0]], dtype=np.float64)
        self.assertEqual(ref.binary_support_iou(ordinary, candidate), 1.0)
        self.assertEqual(ref.weighted_area_ratio(candidate, ordinary), 0.5)

    def test_scene_and_quality_failures_are_preserved_in_full_flow(self) -> None:
        bad_scene = replace(self.candidate, source_id="Pbad-scene", file_sha256=THREE_SHA, scene_id="other")
        bad_quality = replace(self.candidate, source_id="Pbad-quality", file_sha256=FOUR_SHA, source_quality=0.75)
        roster = self._select([bad_quality, self.candidate, bad_scene])
        reasons = {record.source_id: record.reasons for record in roster.flow}
        self.assertIn("SCENE_ID_MISMATCH", reasons["Pbad-scene"])
        self.assertIn("CAL_SOURCE_QUALITY_QUARTILE_MISMATCH", reasons["Pbad-quality"])
        self.assertEqual(roster.eligible_source_ids, ("P1",))

    def test_p_support_cannot_disagree_with_identity_or_domain(self) -> None:
        shifted = np.roll(_support(), 250, axis=1)
        shifted.setflags(write=False)
        bad = replace(
            self.candidate, source_id="Pbad", file_sha256=THREE_SHA, support=shifted,
            support_sha256=ref._canonical_array_sha("S48_REPLACEMENT_SUPPORT_V3", shifted),
        )
        roster = self._select([self.candidate, bad])
        reasons = {record.source_id: record.reasons for record in roster.flow}["Pbad"]
        self.assertTrue(
            "BINARY_SUPPORT_IOU_BELOW_080" in reasons or "P_IDENTITY_SUPPORT_DOMAIN_MISMATCH" in reasons,
            reasons,
        )

    def test_every_eligible_p_is_retained_in_canonical_order(self) -> None:
        second = replace(self.candidate, source_id="P2", file_sha256=TWO_SHA, insertion_event=12)
        roster = self._select([second, self.candidate])
        self.assertEqual(roster.eligible_source_ids, ("P1", "P2"))


class TestReferenceUncertaintyAndUtility(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.uncertainty = _reference_uncertainty()
        cls.valid = np.ones((ref.NATIVE_HEIGHT, ref.NATIVE_WIDTH), dtype=bool)
        cls.reference = _native_constant(0)
        cls.ordinary = _native_constant(0)
        cls.ordinary[192:384, 192:384] = 10
        cls.worse = _native_constant(0)
        cls.worse[192:384, 192:384] = 20

    def _utility(self, estimand: str, treatment: np.ndarray, *, family: str = "", sign: int = 0, replacement: str = "") -> ref.UtilityReceipt:
        key = ref.UtilityKey("O", "T", "s0", self.uncertainty.reference_capture_ids[0], estimand, family, sign, replacement)
        return ref.build_utility_receipt(
            treatment, self.ordinary, self.reference, self.valid, _support(),
            key=key, reference_uncertainty=self.uncertainty,
        )

    def test_three_references_define_delta_ref_and_delta_u(self) -> None:
        self.assertEqual(len(self.uncertainty.reference_capture_ids), 3)
        self.assertEqual(self.uncertainty.delta_ref, 0.0)
        self.assertEqual(self.uncertainty.delta_u, 0.001)
        ref.validate_reference_uncertainty(self.uncertainty)

    def test_local_matched_and_absence_estimands_are_not_conflated(self) -> None:
        local = self._utility("LOCAL_EDIT_PREFERENCE", self.worse, family="exposure_log_gain", sign=1)
        matched = self._utility("MATCHED_REPLACEMENT_RCSU", self.worse, replacement="P1")
        absence = self._utility("SOURCE_ABSENCE_RCSU", self.reference, replacement="ABSENT")
        self.assertGreater(local.support_utility, 0.0)
        self.assertGreater(matched.support_utility, 0.0)
        self.assertLess(absence.support_utility, 0.0)
        self.assertEqual((local.signed_class, matched.signed_class, absence.signed_class), (1, 1, -1))
        self.assertNotEqual(local.key.estimand, absence.key.estimand)

    def test_forged_utility_scalar_is_rejected_against_bound_arrays(self) -> None:
        receipt = self._utility("MATCHED_REPLACEMENT_RCSU", self.worse, replacement="P1")
        attacked = replace(receipt, support_utility=-receipt.support_utility)
        with self.assertRaisesRegex(ref.SpecError, "bound evidence"):
            ref.validate_utility_receipt(attacked)

    def test_outside_change_is_an_absolute_veto(self) -> None:
        treatment = self.worse.copy()
        treatment[_support() == 0.0] = 20
        receipt = self._utility("MATCHED_REPLACEMENT_RCSU", treatment, replacement="P1")
        self.assertFalse(receipt.outside_guard_passed)

    def test_large_reference_disagreement_blocks_primary_rcsu(self) -> None:
        roster = _reference_roster()
        values = (0, 16, 32)
        images = {capture: _native_constant(values[index]) for index, capture in enumerate(roster.eligible_capture_ids)}
        masks = {capture: np.ones((ref.NATIVE_HEIGHT, ref.NATIVE_WIDTH), dtype=bool) for capture in roster.eligible_capture_ids}
        uncertain = ref.build_reference_uncertainty(roster, images, masks, _support())
        self.assertFalse(uncertain.eligible_for_primary_rcsu)
        key = ref.UtilityKey("O", "T", "s0", roster.eligible_capture_ids[0], "MATCHED_REPLACEMENT_RCSU", "", 0, "P1")
        with self.assertRaisesRegex(ref.SpecError, "uncertainty"):
            ref.build_utility_receipt(self.worse, self.ordinary, self.reference, self.valid, _support(), key=key, reference_uncertainty=uncertain)

    def test_reference_pairwise_scalar_cannot_be_injected(self) -> None:
        pairs = list(self.uncertainty.pairwise_losses)
        left, right, _ = pairs[0]
        pairs[0] = (left, right, 0.5)
        with self.assertRaisesRegex(ref.SpecError, "bound observations"):
            ref.validate_reference_uncertainty(replace(self.uncertainty, pairwise_losses=tuple(pairs)))


class TestSequentialLedger(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.uncertainty = _reference_uncertainty()
        _, _, cls.replacements = _replacement_evidence()
        cls.plan = ref.build_experiment_plan(
            source_id="O", targets=("T",), seeds=("s0", "s1", "s2", "s3", "s4"),
            replacement_ids=cls.replacements.eligible_source_ids,
            reference_capture_ids=cls.uncertainty.reference_capture_ids,
            reference_uncertainty_sha256=cls.uncertainty.canonical_sha256,
            replacement_roster_sha256=cls.replacements.canonical_sha256,
            include_source_absence=True,
        )
        cls.aoig_grid = _influence_grid(observable=False)

    def test_exact_grid_emits_typed_aoig_terminal_action(self) -> None:
        decision = ref.evaluate_sequential_ledger(
            self.plan, self.aoig_grid,
            reference_uncertainty=self.uncertainty, replacement_roster=self.replacements,
        )
        self.assertEqual(decision.terminal_action, "AOIG_CANDIDATE_STOP")
        self.assertEqual(decision.influence_count, 20)

    def test_missing_duplicate_and_extra_cells_fail_closed(self) -> None:
        attacks = (
            self.aoig_grid[:-1],
            (*self.aoig_grid[:-1], self.aoig_grid[0]),
            (*self.aoig_grid, replace(self.aoig_grid[0], key=ref.CellKey("O", "EXTRA", "s0", "exposure_log_gain", -1))),
        )
        for attack in attacks:
            with self.assertRaises(ref.SpecError):
                ref.evaluate_sequential_ledger(self.plan, attack, reference_uncertainty=self.uncertainty, replacement_roster=self.replacements)

    def test_later_stage_evidence_after_aoig_stop_is_rejected(self) -> None:
        with self.assertRaisesRegex(ref.SpecError, "forbidden"):
            ref.evaluate_sequential_ledger(
                self.plan, self.aoig_grid, support_effects=(object(),),
                reference_uncertainty=self.uncertainty, replacement_roster=self.replacements,
            )

    def test_plan_requires_exactly_five_seeds_and_three_references(self) -> None:
        with self.assertRaises(ref.SpecError):
            ref.build_experiment_plan(
                source_id="O", targets=("T",), seeds=("s0", "s1", "s2", "s3"),
                replacement_ids=("P1",), reference_capture_ids=("r0", "r1"),
                reference_uncertainty_sha256=ONE_SHA, replacement_roster_sha256=TWO_SHA,
                include_source_absence=True,
            )


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
