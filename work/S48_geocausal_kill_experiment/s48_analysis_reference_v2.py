#!/usr/bin/env python3
"""Finite source-only reference implementation for the S48 V6 contract.

This module uses NumPy arrays supplied by synthetic tests.  It never opens an
experiment payload, imports a model stack, or runs a generation arm.  See
S48_NORMATIVE_ANALYSIS_SPEC_V2.md for the normative scope and blocked gates.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from hashlib import sha256
import math
import re
from typing import Any, Iterable, Mapping, Sequence

import numpy as np


NATIVE_HEIGHT = 576
NATIVE_WIDTH = 576
EPS = 1.0e-12
DELTA_I = 0.5 / 255.0
DELTA_B = 0.001
DELTA_OUT = 0.0005

EXPOSURE_DOSES = (1.0 / 64.0, 1.0 / 32.0, 1.0 / 16.0, 1.0 / 8.0)
TEXTURE_DOSES = (0.05, 0.10, 0.20, 0.30)
TEXTURE_KERNEL = np.asarray([1.0, 4.0, 6.0, 4.0, 1.0], dtype=np.float64) / 16.0
SOURCE_MAD_MIN = 0.5 / 255.0
SOURCE_MAD_MAX = 8.0 / 255.0
SOURCE_CLIPPED_CHANNEL_FRACTION_MAX = 0.005
SOURCE_EDGE_IOU_MIN = 0.95
SOURCE_CLIP_COSINE_MIN = 0.995
SOURCE_LPIPS_MAX = 0.05
SOBEL_EDGE_THRESHOLD = 8.0 / 255.0

PATCH_RADIUS = 4
PATCH_SEARCH_RADIUS = 8
PATCH_GRID_OFFSET = 16
PATCH_GRID_STRIDE = 32
PATCH_NEIGHBORHOOD_RADIUS = 32
PATCH_MIN_RMS = 2.0 / 255.0
PATCH_MAX_NORMALIZED_SSD = 0.25
PATCH_MIN_MUTUAL_MATCHES = 50
PATCH_GLOBAL_COVERAGE_MIN = 0.75
PATCH_LOCAL_COVERAGE_MIN = 0.50

GUARD_MEDIAN_FLOOR_PX = 1.0
GUARD_P95_FLOOR_PX = 3.0
GUARD_RGB_FLOOR = 2.0 / 255.0
GUARD_CHROMA_FLOOR = 2.0 / 255.0
GUARD_SHARPNESS_FLOOR = 0.10
GUARD_SATURATION_FLOOR_PP = 1.0
GUARD_TEAR_FLOOR = 2.0 / 255.0

LOCALIZATION_L_AREA_MIN = 0.02
NEGATIVE_FULL_EFFECT_RATIO_MAX = 0.25
NEGATIVE_SUPPORT_L_AREA_MAX = 0.01
SYNC_TOLERANCE_NS = 10_000_000
IDENTITY_AGREEMENT_MIN = 0.95
IDENTITY_VALID_WEIGHT_COVERAGE_MIN = 0.70
DOMAIN_COVERAGE_MIN = 0.70
DOMAIN_HOLE_RATIO_MAX = 0.10

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SOURCE_STAGE_ORDER = (
    "decode_uint8",
    "family_edit",
    "clip_0_1",
    "multiply_255_round_half_even_uint8",
    "reencode",
    "semantic_consumer",
    "latent_consumer",
)


class SpecError(ValueError):
    """Raised when an input lies outside the frozen finite domain."""


def _finite(value: Any, name: str) -> float:
    if isinstance(value, (bool, np.bool_)):
        raise SpecError(f"{name} must be a finite real, not bool")
    try:
        out = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise SpecError(f"{name} must be a finite real") from exc
    if not math.isfinite(out):
        raise SpecError(f"{name} must be finite")
    return out


def _strict_int(value: Any, name: str, *, minimum: int | None = None) -> int:
    if type(value) is not int:
        raise SpecError(f"{name} must be an exact integer")
    if minimum is not None and value < minimum:
        raise SpecError(f"{name} must be >= {minimum}")
    return value


def _strict_bool(value: Any, name: str) -> bool:
    if type(value) is not bool:
        raise SpecError(f"{name} must be a JSON/Python boolean")
    return value


def _sha(value: Any, name: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise SpecError(f"{name} must be 64 lowercase hexadecimal characters")
    return value


def _u8_rgb(value: Any, name: str, *, native: bool = False) -> np.ndarray:
    if not isinstance(value, np.ndarray):
        raise SpecError(f"{name} must be a numpy.ndarray")
    if value.dtype != np.dtype(np.uint8):
        raise SpecError(f"{name} dtype must be exactly uint8")
    if value.ndim != 3 or value.shape[2] != 3 or value.shape[0] == 0 or value.shape[1] == 0:
        raise SpecError(f"{name} must have non-empty shape H x W x 3")
    if native and value.shape != (NATIVE_HEIGHT, NATIVE_WIDTH, 3):
        raise SpecError(f"{name} must have shape {NATIVE_HEIGHT} x {NATIVE_WIDTH} x 3")
    return value


def _output_x(value: Any, name: str, *, native: bool = False) -> np.ndarray:
    """The sole saved-output conversion: uint8 -> float64 / 255."""
    return _u8_rgb(value, name, native=native).astype(np.float64) / 255.0


def _bool_mask(value: Any, name: str, shape: tuple[int, int] | None = None) -> np.ndarray:
    if not isinstance(value, np.ndarray) or value.dtype != np.dtype(np.bool_):
        raise SpecError(f"{name} must be a numpy.ndarray with dtype exactly bool")
    if value.ndim != 2 or value.size == 0:
        raise SpecError(f"{name} must be a non-empty 2-D bool array")
    if shape is not None and value.shape != shape:
        raise SpecError(f"{name} has wrong shape")
    return value


def _weights(value: Any, name: str = "weight", shape: tuple[int, int] | None = None) -> np.ndarray:
    arr = np.asarray(value, dtype=np.float64)
    if arr.ndim != 2 or arr.size == 0:
        raise SpecError(f"{name} must be a non-empty 2-D array")
    if shape is not None and arr.shape != shape:
        raise SpecError(f"{name} has wrong shape")
    if not np.isfinite(arr).all() or np.any(arr < 0.0) or np.any(arr > 1.0):
        raise SpecError(f"{name} must be finite and in [0,1]")
    return arr


def _identity(value: Any, name: str, shape: tuple[int, int]) -> np.ndarray:
    if not isinstance(value, np.ndarray) or value.ndim != 2 or value.shape != shape:
        raise SpecError(f"{name} must be an integer ndarray with the required 2-D shape")
    if value.dtype.kind not in "iu" or value.dtype == np.dtype(np.bool_):
        raise SpecError(f"{name} must have integer dtype")
    if np.any(value < 0):
        raise SpecError(f"{name} IDs must be nonnegative")
    return value


def _canonical_array_sha(domain: str, array: np.ndarray) -> str:
    if type(domain) is not str or not domain or "\n" in domain:
        raise SpecError("canonical hash domain must be a non-empty single line")
    canonical = np.ascontiguousarray(array)
    header = f"{domain}\n{canonical.dtype.str}\n{','.join(map(str, canonical.shape))}\n".encode("ascii")
    return sha256(header + canonical.tobytes(order="C")).hexdigest()


# ---------------------------------------------------------------------------
# Weight-map primitives


def binary_support(weight: Any) -> np.ndarray:
    return _weights(weight) > 0.0


def connected_components4(weight: Any) -> int:
    support = binary_support(weight)
    visited = np.zeros_like(support)
    count = 0
    for row, col in zip(*np.nonzero(support)):
        if visited[row, col]:
            continue
        count += 1
        visited[row, col] = True
        stack = [(int(row), int(col))]
        while stack:
            rr, cc = stack.pop()
            for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                if 0 <= nr < support.shape[0] and 0 <= nc < support.shape[1]:
                    if support[nr, nc] and not visited[nr, nc]:
                        visited[nr, nc] = True
                        stack.append((nr, nc))
    return count


def exposed_edge_perimeter(weight: Any) -> int:
    support = binary_support(weight)
    return int(
        np.count_nonzero(support[0])
        + np.count_nonzero(support[-1])
        + np.count_nonzero(support[:, 0])
        + np.count_nonzero(support[:, -1])
        + np.count_nonzero(support[1:] != support[:-1])
        + np.count_nonzero(support[:, 1:] != support[:, :-1])
    )


def normalized_perimeter(weight: Any) -> float:
    support = binary_support(weight)
    area = int(np.count_nonzero(support))
    if area == 0:
        raise SpecError("normalized perimeter is undefined for empty support")
    return _finite(exposed_edge_perimeter(weight) / math.sqrt(area), "normalized_perimeter")


def positive_weight_histogram(weight: Any) -> np.ndarray:
    positive = _weights(weight)
    positive = positive[positive > 0.0]
    if positive.size == 0:
        raise SpecError("positive-weight histogram is undefined for empty support")
    indices = np.minimum(np.floor(10.0 * positive).astype(np.int64), 9)
    counts = np.bincount(indices, minlength=10).astype(np.float64)
    out = counts / float(positive.size)
    if not np.isfinite(out).all() or not math.isclose(float(out.sum()), 1.0, abs_tol=1e-15):
        raise SpecError("histogram normalization failed")
    return out


def weight_map_sha256(weight: Any) -> str:
    arr = np.array(_weights(weight), dtype="<f8", order="C", copy=True)
    arr[arr == 0.0] = 0.0
    return _canonical_array_sha("S48_WEIGHT_MAP_V2", arr)


def context_descriptor(values: Any, valid: Any, weight: Any) -> dict[str, float]:
    value_arr = np.asarray(values, dtype=np.float64)
    weight_arr = _weights(weight)
    valid_arr = _bool_mask(valid, "valid", weight_arr.shape)
    if value_arr.shape != weight_arr.shape:
        raise SpecError("values and weight must share shape")
    finite_valid = valid_arr & np.isfinite(value_arr)
    population = value_arr[finite_valid]
    if population.size == 0:
        raise SpecError("descriptor has no finite population")
    total = float(np.sum(weight_arr))
    if total <= 0.0:
        raise SpecError("descriptor support is empty")
    valid_weight = float(np.sum(weight_arr[finite_valid]))
    fraction = valid_weight / total
    if fraction < 0.95:
        raise SpecError("descriptor support lacks required valid-weight coverage")
    values_valid = value_arr[finite_valid]
    weights_valid = weight_arr[finite_valid]
    positive = weights_valid > 0.0
    order = np.argsort(values_valid[positive], kind="stable")
    vv = values_valid[positive][order]
    ww = weights_valid[positive][order]
    threshold = 0.5 * float(np.sum(ww))
    index = int(np.searchsorted(np.cumsum(ww), threshold, side="left"))
    summary = float(vv[min(index, vv.size - 1)])
    cuts = np.quantile(np.sort(population, kind="stable"), (0.25, 0.5, 0.75), method="linear")
    stratum = int(np.searchsorted(cuts, summary, side="right"))
    return {"summary": _finite(summary, "summary"), "valid_weight_fraction": fraction, "stratum": stratum}


# ---------------------------------------------------------------------------
# One-path source edit and consumer receipt


def _blur_binomial5_reflect101(rgb: np.ndarray) -> np.ndarray:
    if rgb.shape[0] < 3 or rgb.shape[1] < 3:
        raise SpecError("texture edit requires source height and width >= 3")
    radius = 2
    padded = np.pad(rgb, ((0, 0), (radius, radius), (0, 0)), mode="reflect")
    horizontal = sum(TEXTURE_KERNEL[i] * padded[:, i : i + rgb.shape[1], :] for i in range(5))
    padded = np.pad(horizontal, ((radius, radius), (0, 0), (0, 0)), mode="reflect")
    return sum(TEXTURE_KERNEL[i] * padded[i : i + rgb.shape[0], :, :] for i in range(5))


def _validate_family_sign_dose(family: Any, sign: Any, dose: Any) -> tuple[str, int, float]:
    if type(family) is not str or family not in ("exposure_log_gain", "texture_highpass"):
        raise SpecError("unknown source edit family")
    sign_value = _strict_int(sign, "sign")
    if sign_value not in (-1, 1):
        raise SpecError("sign must be -1 or +1")
    dose_value = _finite(dose, "dose")
    ladder = EXPOSURE_DOSES if family == "exposure_log_gain" else TEXTURE_DOSES
    if dose_value != 0.0 and dose_value not in ladder:
        raise SpecError("dose must be exact zero or a frozen ladder value")
    return family, sign_value, dose_value


@dataclass(frozen=True)
class SourceBundle:
    family: str
    sign: int
    dose: float
    encoded_u8: np.ndarray
    semantic_tensor: np.ndarray
    latent_tensor: np.ndarray
    encoded_sha256: str
    semantic_tensor_sha256: str
    latent_tensor_sha256: str
    stage_order: tuple[str, ...]
    consumer_order: tuple[str, str]
    quantization: str


def quantize_unit_float_ties_to_even(value: Any) -> np.ndarray:
    """Clip finite floats to [0,1], multiply by 255, and round ties to even."""
    arr = np.asarray(value, dtype=np.float64)
    if arr.size == 0 or not np.isfinite(arr).all():
        raise SpecError("quantization input must be non-empty and finite")
    quantized = np.rint(255.0 * np.clip(arr, 0.0, 1.0))
    if np.any(quantized < 0.0) or np.any(quantized > 255.0):
        raise SpecError("quantization left the uint8 domain")
    return quantized.astype(np.uint8)


def apply_source_bundle(source_u8: Any, family: Any, sign: Any, dose: Any) -> SourceBundle:
    """Run the exact same decode/edit/clip/quantize/reencode path, including dose 0."""
    source = _u8_rgb(source_u8, "source_u8")
    family_value, sign_value, dose_value = _validate_family_sign_dose(family, sign, dose)
    x = source.astype(np.float64) / 255.0
    if family_value == "exposure_log_gain":
        preclip = x * math.pow(2.0, sign_value * dose_value)
    else:
        highpass = x - _blur_binomial5_reflect101(x)
        preclip = x + sign_value * dose_value * highpass
    encoded = quantize_unit_float_ties_to_even(preclip)
    consumer_x = encoded.astype(np.float64) / 255.0
    semantic = np.ascontiguousarray(np.transpose(consumer_x, (2, 0, 1)), dtype="<f4")
    latent = np.ascontiguousarray(np.transpose(2.0 * consumer_x - 1.0, (2, 0, 1)), dtype="<f4")
    return SourceBundle(
        family_value,
        sign_value,
        dose_value,
        encoded,
        semantic,
        latent,
        _canonical_array_sha("S48_REENCODED_UINT8_V2", encoded),
        _canonical_array_sha("S48_SEMANTIC_INPUT_TENSOR_V2", semantic),
        _canonical_array_sha("S48_LATENT_INPUT_TENSOR_V2", latent),
        SOURCE_STAGE_ORDER,
        ("semantic", "latent"),
        "clip_[0,1];multiply_255;rint_ties_to_even;uint8",
    )


@dataclass(frozen=True)
class SourceEditMetrics:
    mean_absolute_rgb_difference: float
    clipped_channel_fraction: float
    edge_iou: float
    clip_cosine: float
    lpips: float


def _gray(x: np.ndarray) -> np.ndarray:
    return 0.299 * x[..., 0] + 0.587 * x[..., 1] + 0.114 * x[..., 2]


def _conv3(gray: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    padded = np.pad(gray, ((1, 1), (1, 1)), mode="reflect")
    out = np.zeros_like(gray)
    for row in range(3):
        for col in range(3):
            out += kernel[row, col] * padded[row : row + gray.shape[0], col : col + gray.shape[1]]
    return out


def _edge_support_u8(u: np.ndarray) -> np.ndarray:
    x = u.astype(np.float64) / 255.0
    gray = _gray(x)
    gx = _conv3(gray, np.asarray([[1, 0, -1], [2, 0, -2], [1, 0, -1]], dtype=np.float64) / 8.0)
    gy = _conv3(gray, np.asarray([[1, 2, 1], [0, 0, 0], [-1, -2, -1]], dtype=np.float64) / 8.0)
    return np.hypot(gx, gy) > SOBEL_EDGE_THRESHOLD


def source_edit_metrics(source_u8: Any, bundle: SourceBundle, clip_cosine: Any, lpips: Any) -> SourceEditMetrics:
    source = _u8_rgb(source_u8, "source_u8")
    edited = _u8_rgb(bundle.encoded_u8, "bundle.encoded_u8")
    if source.shape != edited.shape:
        raise SpecError("source and edit shape mismatch")
    x = source.astype(np.float64) / 255.0
    y = edited.astype(np.float64) / 255.0
    a = _edge_support_u8(source)
    b = _edge_support_u8(edited)
    union = int(np.count_nonzero(a | b))
    edge_iou = 1.0 if union == 0 else np.count_nonzero(a & b) / union
    return SourceEditMetrics(
        float(np.mean(np.abs(y - x))),
        float(np.mean((edited == 0) | (edited == 255))),
        _finite(edge_iou, "edge_iou"),
        _finite(clip_cosine, "clip_cosine"),
        _finite(lpips, "lpips"),
    )


def source_edit_gate(metrics: SourceEditMetrics) -> tuple[bool, tuple[str, ...]]:
    values = tuple(_finite(getattr(metrics, field.name), field.name) for field in fields(metrics))
    mad, clipped, edge, cosine, lpips = values
    if not 0.0 <= mad <= 1.0 or not 0.0 <= clipped <= 1.0 or not 0.0 <= edge <= 1.0:
        raise SpecError("source RGB gate quantities must lie in [0,1]")
    if not -1.0 <= cosine <= 1.0 or lpips < 0.0:
        raise SpecError("source perceptual gate quantities are outside their domains")
    failures: list[str] = []
    if mad < SOURCE_MAD_MIN or mad > SOURCE_MAD_MAX:
        failures.append("SOURCE_MAD_OUTSIDE_RANGE")
    if clipped > SOURCE_CLIPPED_CHANNEL_FRACTION_MAX:
        failures.append("SOURCE_CLIPPING_ABOVE_MAX")
    if edge < SOURCE_EDGE_IOU_MIN:
        failures.append("SOURCE_EDGE_IOU_BELOW_MIN")
    if cosine < SOURCE_CLIP_COSINE_MIN:
        failures.append("SOURCE_CLIP_COSINE_BELOW_MIN")
    if lpips > SOURCE_LPIPS_MAX:
        failures.append("SOURCE_LPIPS_ABOVE_MAX")
    return not failures, tuple(failures)


def select_minimum_source_dose(
    source_u8: Any,
    family: str,
    external_metrics: Mapping[tuple[float, int], Mapping[str, Any]],
) -> tuple[float, Mapping[int, SourceBundle], Mapping[int, SourceEditMetrics]]:
    source = _u8_rgb(source_u8, "source_u8")
    if family not in ("exposure_log_gain", "texture_highpass"):
        raise SpecError("unknown source edit family")
    ladder = EXPOSURE_DOSES if family == "exposure_log_gain" else TEXTURE_DOSES
    expected_keys = {(dose, sign) for dose in ladder for sign in (-1, 1)}
    if set(external_metrics) != expected_keys:
        raise SpecError("external source-gate metrics must cover the exact dose/sign ladder")
    for dose in ladder:
        bundles: dict[int, SourceBundle] = {}
        metrics: dict[int, SourceEditMetrics] = {}
        passed = True
        for sign in (-1, 1):
            external = external_metrics[(dose, sign)]
            if set(external) != {"clip_cosine", "lpips"}:
                raise SpecError("external source-gate metric schema mismatch")
            bundle = apply_source_bundle(source, family, sign, dose)
            measured = source_edit_metrics(source, bundle, external["clip_cosine"], external["lpips"])
            bundles[sign] = bundle
            metrics[sign] = measured
            passed = passed and source_edit_gate(measured)[0]
        if passed:
            return dose, bundles, metrics
    raise SpecError("NO_DOSE_PASSES_BOTH_SIGNS")


# ---------------------------------------------------------------------------
# Influence and localization


def direct_effect_map(edit_u8: Any, zero_u8: Any) -> np.ndarray:
    edit = _output_x(edit_u8, "edit_u8", native=True)
    zero = _output_x(zero_u8, "zero_u8", native=True)
    if edit.shape != zero.shape:
        raise SpecError("direct-effect outputs must share shape")
    out = np.mean(np.abs(edit - zero), axis=2, dtype=np.float64)
    if not np.isfinite(out).all() or np.any(out < 0.0) or np.any(out > 1.0):
        raise SpecError("direct effect left [0,1]")
    return out


def influence_value(target_effect: Any, replay_floor: Any, negative_effect: Any) -> float:
    target = _weights(target_effect, "target_effect")
    negative = _weights(negative_effect, "negative_effect", target.shape)
    replay = _finite(replay_floor, "replay_floor")
    if replay < 0.0 or replay > 1.0:
        raise SpecError("replay_floor must lie in [0,1]")
    return float(np.mean(target) - max(replay, float(np.mean(negative))))


@dataclass(frozen=True)
class LocalizationMetrics:
    area: float
    effect_mean: float
    mass: float
    l_area: float
    enrichment_ratio: float


def localization_metrics(effect: Any, support: Any) -> LocalizationMetrics:
    e = _weights(effect, "effect")
    w = _weights(support, "support", e.shape)
    area = float(np.mean(w))
    if not 0.0 < area < 1.0:
        raise SpecError("support area must lie strictly in (0,1)")
    total = float(np.sum(e))
    if total <= EPS:
        raise SpecError("effect mass is not identifiable")
    mass = float(np.sum(w * e) / (total + EPS))
    l_area = mass - area
    enrichment = mass / area
    return LocalizationMetrics(area, float(np.mean(e)), mass, l_area, enrichment)


def descriptive_tail(effect: Any, true_support: Any, placebo_supports: Sequence[Any]) -> dict[str, float | int]:
    e = _weights(effect, "effect")
    true_mass = localization_metrics(e, true_support).mass
    if len(placebo_supports) == 0:
        raise SpecError("placebo library must be non-empty")
    masses = [localization_metrics(e, candidate).mass for candidate in placebo_supports]
    ordered = np.sort(np.asarray(masses, dtype=np.float64), kind="stable")
    median = float(ordered[(ordered.size - 1) // 2])  # lower median
    rank = (1 + int(np.count_nonzero(ordered >= true_mass))) / float(ordered.size + 1)
    return {"count": len(masses), "true_mass": true_mass, "lower_median": median, "tail_rank": rank}


def localization_decision(
    target_effect: Any,
    negative_effect: Any,
    support: Any,
    *,
    influence_passed: Any,
    shape_tail: Mapping[str, Any],
    camera_tail: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...], dict[str, float]]:
    if type(influence_passed) is not bool:
        raise SpecError("influence_passed must be bool")
    target = _weights(target_effect, "target_effect")
    negative = _weights(negative_effect, "negative_effect", target.shape)
    target_metrics = localization_metrics(target, support)
    negative_total = float(np.sum(negative))
    if negative_total <= EPS:
        area = target_metrics.area
        negative_metrics = LocalizationMetrics(area, 0.0, 0.0, -area, 0.0)
    else:
        negative_metrics = localization_metrics(negative, support)
    target_mean = target_metrics.effect_mean
    if target_mean <= EPS:
        raise SpecError("target effect mean is zero")
    negative_ratio = negative_metrics.effect_mean / target_mean
    failures: list[str] = []
    if not influence_passed:
        failures.append("INFLUENCE_NOT_PASSED")
    if target_metrics.enrichment_ratio <= 1.0:
        failures.append("TARGET_ER_NOT_ABOVE_ONE")
    if target_metrics.l_area < LOCALIZATION_L_AREA_MIN:
        failures.append("TARGET_L_AREA_BELOW_MIN")
    if negative_ratio > NEGATIVE_FULL_EFFECT_RATIO_MAX:
        failures.append("NEGATIVE_FULL_EFFECT_RATIO_ABOVE_MAX")
    if negative_metrics.l_area > NEGATIVE_SUPPORT_L_AREA_MAX:
        failures.append("NEGATIVE_SUPPORT_LOCALIZATION_ABOVE_MAX")
    for label, tail in (("SHAPE", shape_tail), ("CAMERA", camera_tail)):
        if set(tail) != {"count", "true_mass", "lower_median", "tail_rank"}:
            raise SpecError(f"{label} tail schema mismatch")
        count = _strict_int(tail["count"], f"{label}.count", minimum=0)
        true_mass = _finite(tail["true_mass"], f"{label}.true_mass")
        median = _finite(tail["lower_median"], f"{label}.lower_median")
        rank = _finite(tail["tail_rank"], f"{label}.tail_rank")
        if not 0.0 <= true_mass <= 1.0 or not 0.0 <= median <= 1.0 or not 0.0 <= rank <= 1.0:
            raise SpecError(f"{label} tail values must lie in [0,1]")
        if count < 199:
            failures.append(f"{label}_PLACEBO_COUNT_BELOW_199")
        if true_mass <= median:
            failures.append(f"{label}_TRUE_MASS_NOT_ABOVE_MEDIAN")
        if rank > 0.05:
            failures.append(f"{label}_TAIL_RANK_ABOVE_005")
    evidence = {
        "target_l_area": target_metrics.l_area,
        "target_er": target_metrics.enrichment_ratio,
        "negative_l_area_same_support": negative_metrics.l_area,
        "negative_full_effect_ratio": negative_ratio,
    }
    return not failures, tuple(failures), evidence


# ---------------------------------------------------------------------------
# Symmetric output guard and typed replay receipts


def _patch_descriptor(gray: np.ndarray, row: int, col: int) -> np.ndarray | None:
    patch = gray[row - PATCH_RADIUS : row + PATCH_RADIUS + 1, col - PATCH_RADIUS : col + PATCH_RADIUS + 1]
    centered = patch - float(np.mean(patch))
    rms = float(np.sqrt(np.mean(centered * centered)))
    if rms < PATCH_MIN_RMS:
        return None
    return centered / rms


def _grid_centers() -> tuple[tuple[int, int], ...]:
    return tuple(
        (row, col)
        for row in range(PATCH_GRID_OFFSET, NATIVE_HEIGHT - PATCH_RADIUS, PATCH_GRID_STRIDE)
        for col in range(PATCH_GRID_OFFSET, NATIVE_WIDTH - PATCH_RADIUS, PATCH_GRID_STRIDE)
    )


def _best_patch(gray: np.ndarray, descriptor: np.ndarray, row: int, col: int) -> tuple[int, int, float] | None:
    best: tuple[float, int, int] | None = None
    for dr in range(-PATCH_SEARCH_RADIUS, PATCH_SEARCH_RADIUS + 1):
        rr = row + dr
        if rr - PATCH_RADIUS < 0 or rr + PATCH_RADIUS >= gray.shape[0]:
            continue
        for dc in range(-PATCH_SEARCH_RADIUS, PATCH_SEARCH_RADIUS + 1):
            cc = col + dc
            if cc - PATCH_RADIUS < 0 or cc + PATCH_RADIUS >= gray.shape[1]:
                continue
            candidate = _patch_descriptor(gray, rr, cc)
            if candidate is None:
                continue
            score = float(np.mean((descriptor - candidate) ** 2))
            key = (score, rr, cc)
            if best is None or key < best:
                best = key
    if best is None or best[0] > PATCH_MAX_NORMALIZED_SSD:
        return None
    return best[1], best[2], best[0]


def _directional_mutual_matches(a: np.ndarray, b: np.ndarray) -> tuple[tuple[int, int, float], ...]:
    matches: list[tuple[int, int, float]] = []
    for row, col in _grid_centers():
        descriptor = _patch_descriptor(a, row, col)
        if descriptor is None:
            continue
        forward = _best_patch(b, descriptor, row, col)
        if forward is None:
            continue
        rr, cc, _ = forward
        reverse_descriptor = _patch_descriptor(b, rr, cc)
        if reverse_descriptor is None:
            continue
        reverse = _best_patch(a, reverse_descriptor, rr, cc)
        if reverse is not None and reverse[:2] == (row, col):
            matches.append((row, col, math.hypot(rr - row, cc - col)))
    return tuple(matches)


def _dilate(mask: np.ndarray, radius: int) -> np.ndarray:
    rows, cols = np.nonzero(mask)
    out = np.zeros_like(mask)
    for row, col in zip(rows, cols):
        out[max(0, row - radius) : min(mask.shape[0], row + radius + 1), max(0, col - radius) : min(mask.shape[1], col + radius + 1)] = True
    return out


def _region_summary(
    matches_ab: Sequence[tuple[int, int, float]],
    matches_ba: Sequence[tuple[int, int, float]],
    region: np.ndarray,
) -> tuple[int, int, float, float, float]:
    centers = _grid_centers()
    expected = sum(bool(region[row, col]) for row, col in centers)
    distances = [distance for row, col, distance in matches_ab if region[row, col]]
    distances += [distance for row, col, distance in matches_ba if region[row, col]]
    matched_centers = {(row, col) for row, col, _ in matches_ab if region[row, col]}
    matched_centers |= {(row, col) for row, col, _ in matches_ba if region[row, col]}
    count = len(matched_centers)
    coverage = count / expected if expected else 0.0
    if not distances:
        return expected, count, coverage, 0.0, 0.0
    values = np.sort(np.asarray(distances, dtype=np.float64), kind="stable")
    median = float(np.quantile(values, 0.5, method="linear"))
    p95 = float(np.quantile(values, 0.95, method="linear"))
    return expected, count, coverage, median, p95


def _laplacian_sharpness(x: np.ndarray) -> float:
    gray = _gray(x)
    lap = _conv3(gray, np.asarray([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float64))
    return float(np.mean(lap * lap))


def _tear_score(x: np.ndarray) -> float:
    gray = _gray(x)
    row = float(np.max(np.mean(np.abs(gray[1:] - gray[:-1]), axis=1))) if gray.shape[0] > 1 else 0.0
    col = float(np.max(np.mean(np.abs(gray[:, 1:] - gray[:, :-1]), axis=0))) if gray.shape[1] > 1 else 0.0
    return max(row, col)


@dataclass(frozen=True)
class ArmGuardMetrics:
    global_expected: int
    global_matches: int
    global_coverage: float
    global_median_px: float
    global_p95_px: float
    support_expected: int
    support_matches: int
    support_coverage: float
    support_median_px: float
    support_p95_px: float
    neighborhood_expected: int
    neighborhood_matches: int
    neighborhood_coverage: float
    neighborhood_median_px: float
    neighborhood_p95_px: float
    outside_rgb_difference: float
    outside_chroma_difference: float
    sharpness_deviation: float
    saturation_difference_pp: float
    tear_difference: float


@dataclass(frozen=True)
class GuardFloors:
    global_median_px: float
    global_p95_px: float
    support_median_px: float
    support_p95_px: float
    neighborhood_median_px: float
    neighborhood_p95_px: float
    outside_rgb_difference: float
    outside_chroma_difference: float
    sharpness_deviation: float
    saturation_difference_pp: float
    tear_difference: float


@dataclass(frozen=True)
class ReplayPairReceipt:
    seed: str
    target: str
    replay_i: int
    replay_j: int
    metrics: ArmGuardMetrics


def arm_guard_metrics(reference_u8: Any, candidate_u8: Any, support: Any) -> ArmGuardMetrics:
    a = _output_x(reference_u8, "reference_u8", native=True)
    b = _output_x(candidate_u8, "candidate_u8", native=True)
    w = _weights(support, "support", (NATIVE_HEIGHT, NATIVE_WIDTH))
    inside = w > 0.0
    outside = ~inside
    if not inside.any() or not outside.any():
        raise SpecError("guard support and outside domains must both be non-empty")
    neighborhood = _dilate(inside, PATCH_NEIGHBORHOOD_RADIUS) & ~inside
    gray_a = _gray(a)
    gray_b = _gray(b)
    ab = _directional_mutual_matches(gray_a, gray_b)
    ba = _directional_mutual_matches(gray_b, gray_a)
    global_region = np.ones_like(inside)
    g = _region_summary(ab, ba, global_region)
    s = _region_summary(ab, ba, inside)
    n = _region_summary(ab, ba, neighborhood)
    outside_rgb = float(np.mean(np.abs(a[outside] - b[outside])))
    chroma_a = np.stack((a[..., 0] - a[..., 1], a[..., 2] - a[..., 1]), axis=2)
    chroma_b = np.stack((b[..., 0] - b[..., 1], b[..., 2] - b[..., 1]), axis=2)
    outside_chroma = float(0.5 * np.mean(np.abs(chroma_a[outside] - chroma_b[outside])))
    sharp_a = _laplacian_sharpness(a)
    sharp_b = _laplacian_sharpness(b)
    if max(sharp_a, sharp_b) <= EPS:
        sharpness = 0.0
    else:
        sharpness = abs(sharp_a - sharp_b) / max(sharp_a, sharp_b)
    saturation_a = float(np.mean((reference_u8 == 0) | (reference_u8 == 255)) * 100.0)
    saturation_b = float(np.mean((candidate_u8 == 0) | (candidate_u8 == 255)) * 100.0)
    tear = abs(_tear_score(a) - _tear_score(b))
    return ArmGuardMetrics(
        g[0], g[1], g[2], g[3], g[4],
        s[0], s[1], s[2], s[3], s[4],
        n[0], n[1], n[2], n[3], n[4],
        outside_rgb, outside_chroma, sharpness, abs(saturation_a - saturation_b), tear,
    )


def _validate_guard_metrics(metrics: ArmGuardMetrics) -> None:
    for name in ("global_expected", "global_matches", "support_expected", "support_matches", "neighborhood_expected", "neighborhood_matches"):
        _strict_int(getattr(metrics, name), name, minimum=0)
    for prefix in ("global", "support", "neighborhood"):
        expected = getattr(metrics, f"{prefix}_expected")
        matches = getattr(metrics, f"{prefix}_matches")
        coverage = _finite(getattr(metrics, f"{prefix}_coverage"), f"{prefix}_coverage")
        median = _finite(getattr(metrics, f"{prefix}_median_px"), f"{prefix}_median_px")
        p95 = _finite(getattr(metrics, f"{prefix}_p95_px"), f"{prefix}_p95_px")
        expected_coverage = matches / expected if expected else 0.0
        if (
            matches > expected
            or not 0.0 <= coverage <= 1.0
            or not math.isclose(coverage, expected_coverage, rel_tol=0.0, abs_tol=1e-15)
            or median < 0.0
            or p95 < median
        ):
            raise SpecError(f"invalid {prefix} guard metric domain")
    for name in ("outside_rgb_difference", "outside_chroma_difference", "sharpness_deviation", "tear_difference"):
        value = _finite(getattr(metrics, name), name)
        if not 0.0 <= value <= 1.0:
            raise SpecError(f"{name} must lie in [0,1]")
    saturation = _finite(metrics.saturation_difference_pp, "saturation_difference_pp")
    if not 0.0 <= saturation <= 100.0:
        raise SpecError("saturation_difference_pp must lie in [0,100]")


_FLOOR_FIELDS = tuple(field.name for field in fields(GuardFloors))


def replay_guard_floors(receipts: Sequence[ReplayPairReceipt], *, seed: str, target: str) -> GuardFloors:
    if type(seed) is not str or not seed or type(target) is not str or not target:
        raise SpecError("seed and target must be non-empty strings")
    expected = {(i, j) for i in range(4) for j in range(i + 1, 4)}
    seen: set[tuple[int, int]] = set()
    for receipt in receipts:
        if not isinstance(receipt, ReplayPairReceipt):
            raise SpecError("replay receipts must be typed ReplayPairReceipt objects")
        if receipt.seed != seed or receipt.target != target:
            raise SpecError("replay receipt seed/target mismatch")
        i = _strict_int(receipt.replay_i, "replay_i", minimum=0)
        j = _strict_int(receipt.replay_j, "replay_j", minimum=0)
        if i >= j or (i, j) not in expected or (i, j) in seen:
            raise SpecError("replay receipt has reversed, extra, or duplicate pair")
        seen.add((i, j))
        _validate_guard_metrics(receipt.metrics)
    if seen != expected or len(receipts) != 6:
        raise SpecError("replay receipts must contain each of the exact six canonical pairs once")
    maxima = {name: max(_finite(getattr(receipt.metrics, name), name) for receipt in receipts) for name in _FLOOR_FIELDS}
    floors = GuardFloors(**maxima)
    for prefix in ("global", "support", "neighborhood"):
        if getattr(floors, f"{prefix}_p95_px") < getattr(floors, f"{prefix}_median_px"):
            raise SpecError("replay floor p95 must be >= median")
    return floors


def arm_guard_decision(metrics: ArmGuardMetrics, floors: GuardFloors) -> tuple[bool, tuple[str, ...]]:
    _validate_guard_metrics(metrics)
    for name in _FLOOR_FIELDS:
        value = _finite(getattr(floors, name), f"floor.{name}")
        upper = 100.0 if name == "saturation_difference_pp" else (math.inf if name.endswith("_px") else 1.0)
        if value < 0.0 or value > upper:
            raise SpecError(f"floor.{name} outside domain")
    for prefix in ("global", "support", "neighborhood"):
        if getattr(floors, f"{prefix}_p95_px") < getattr(floors, f"{prefix}_median_px"):
            raise SpecError("floor p95 must be >= median")
    failures: list[str] = []
    if metrics.global_matches < PATCH_MIN_MUTUAL_MATCHES:
        failures.append("GLOBAL_MATCH_COUNT_BELOW_MIN")
    if metrics.global_coverage < PATCH_GLOBAL_COVERAGE_MIN:
        failures.append("GLOBAL_GRID_COVERAGE_BELOW_MIN")
    if metrics.support_expected == 0 or metrics.support_coverage < PATCH_LOCAL_COVERAGE_MIN:
        failures.append("SUPPORT_GRID_COVERAGE_BELOW_MIN")
    if metrics.neighborhood_expected == 0 or metrics.neighborhood_coverage < PATCH_LOCAL_COVERAGE_MIN:
        failures.append("NEIGHBORHOOD_GRID_COVERAGE_BELOW_MIN")
    comparisons = (
        ("global_median_px", GUARD_MEDIAN_FLOOR_PX), ("global_p95_px", GUARD_P95_FLOOR_PX),
        ("support_median_px", GUARD_MEDIAN_FLOOR_PX), ("support_p95_px", GUARD_P95_FLOOR_PX),
        ("neighborhood_median_px", GUARD_MEDIAN_FLOOR_PX), ("neighborhood_p95_px", GUARD_P95_FLOOR_PX),
        ("outside_rgb_difference", GUARD_RGB_FLOOR), ("outside_chroma_difference", GUARD_CHROMA_FLOOR),
        ("sharpness_deviation", GUARD_SHARPNESS_FLOOR),
        ("saturation_difference_pp", GUARD_SATURATION_FLOOR_PP), ("tear_difference", GUARD_TEAR_FLOOR),
    )
    for name, fixed in comparisons:
        if getattr(metrics, name) > max(fixed, getattr(floors, name)):
            failures.append(f"{name.upper()}_ABOVE_MAX")
    return not failures, tuple(failures)


# ---------------------------------------------------------------------------
# Reference, domains, identity and Benefit


def _round_ratio_half_even(numerator: int, denominator: int) -> int:
    if type(numerator) is not int or type(denominator) is not int or denominator <= 0:
        raise SpecError("round_half_even requires integer numerator and positive denominator")
    sign = -1 if numerator < 0 else 1
    q, r = divmod(abs(numerator), denominator)
    twice = 2 * r
    if twice > denominator or (twice == denominator and q % 2 == 1):
        q += 1
    return sign * q


def stable_scaled_integer(value: Any, scale: int, name: str) -> int:
    number = _finite(value, name)
    if number < 0.0:
        raise SpecError(f"{name} must be nonnegative")
    scale_value = _strict_int(scale, "scale", minimum=1)
    numerator, denominator = number.as_integer_ratio()
    return _round_ratio_half_even(numerator * scale_value, denominator)


@dataclass(frozen=True)
class SyncCalibration:
    t0_sensor_ns: int
    offset_ns: int
    drift_ppb: int
    measured_residuals_ns: tuple[int, ...]


def validate_sync_calibration(calibration: SyncCalibration) -> None:
    _strict_int(calibration.t0_sensor_ns, "t0_sensor_ns")
    _strict_int(calibration.offset_ns, "offset_ns")
    _strict_int(calibration.drift_ppb, "drift_ppb")
    if not isinstance(calibration.measured_residuals_ns, tuple) or not calibration.measured_residuals_ns:
        raise SpecError("measured residuals must be a non-empty tuple")
    residuals = [_strict_int(value, "measured_residual_ns") for value in calibration.measured_residuals_ns]
    if max(abs(value) for value in residuals) > SYNC_TOLERANCE_NS:
        raise SpecError("synchronization calibration residual exceeds 10 ms")


def calibrated_timestamp_ns(sensor_timestamp_ns: Any, calibration: SyncCalibration) -> int:
    timestamp = _strict_int(sensor_timestamp_ns, "sensor_timestamp_ns")
    validate_sync_calibration(calibration)
    drift = _round_ratio_half_even((timestamp - calibration.t0_sensor_ns) * calibration.drift_ppb, 1_000_000_000)
    return timestamp + calibration.offset_ns + drift


@dataclass(frozen=True)
class Camera:
    center: tuple[float, float, float]
    rotation: np.ndarray
    fov_degrees: float


def _validate_camera(camera: Camera, name: str) -> tuple[np.ndarray, np.ndarray, float]:
    center = np.asarray(camera.center, dtype=np.float64)
    rotation = np.asarray(camera.rotation, dtype=np.float64)
    fov = _finite(camera.fov_degrees, f"{name}.fov_degrees")
    if center.shape != (3,) or not np.isfinite(center).all():
        raise SpecError(f"{name}.center must be a finite 3-vector")
    if rotation.shape != (3, 3) or not np.isfinite(rotation).all():
        raise SpecError(f"{name}.rotation must be a finite 3x3 matrix")
    if not np.allclose(rotation.T @ rotation, np.eye(3), rtol=0.0, atol=1e-9) or not math.isclose(float(np.linalg.det(rotation)), 1.0, rel_tol=0.0, abs_tol=1e-9):
        raise SpecError(f"{name}.rotation must be orthonormal with determinant +1")
    if not 0.0 < fov < 180.0:
        raise SpecError(f"{name}.fov_degrees must lie in (0,180)")
    return center, rotation, fov


@dataclass(frozen=True)
class CameraMatchMetrics:
    target_angle_degrees: float
    target_position_ratio: float
    fov_difference_degrees: float
    angle_microdegrees: int
    position_ratio_ppm: int
    fov_microdegrees: int


def camera_match_metrics(target: Camera, ordinary: Camera, candidate: Camera) -> CameraMatchMetrics:
    target_c, target_r, target_fov = _validate_camera(target, "target")
    ordinary_c, _, _ = _validate_camera(ordinary, "ordinary")
    candidate_c, candidate_r, candidate_fov = _validate_camera(candidate, "candidate")
    baseline = float(np.linalg.norm(ordinary_c - target_c))
    if baseline <= 1.0e-6:
        raise SpecError("ordinary-target baseline is not identifiable")
    ratio = float(np.linalg.norm(candidate_c - target_c) / baseline)
    cosine = float(np.clip((np.trace(target_r.T @ candidate_r) - 1.0) / 2.0, -1.0, 1.0))
    angle = math.degrees(math.acos(cosine))
    fov_difference = abs(candidate_fov - target_fov)
    return CameraMatchMetrics(
        angle, ratio, fov_difference,
        stable_scaled_integer(angle, 1_000_000, "angle"),
        stable_scaled_integer(ratio, 1_000_000, "position_ratio"),
        stable_scaled_integer(fov_difference, 1_000_000, "fov_difference"),
    )


@dataclass(frozen=True)
class ReferenceCandidate:
    candidate_id: str
    file_sha256: str
    scene_id: str
    sensor_timestamp_ns: int
    camera: Camera
    calibration: SyncCalibration
    identity_receipt: "IdentityAgreement"
    view_pair_receipts: tuple["ViewPairReceipt", ...]
    domain_receipts: Mapping[str, "ValidDomainReceipt"]


def select_reference(
    candidates: Sequence[ReferenceCandidate], *, target_timestamp_ns: int,
    target_calibration: SyncCalibration, target_scene_id: str,
    target_camera: Camera, ordinary_camera: Camera,
) -> dict[str, Any]:
    target_time = _strict_int(target_timestamp_ns, "target_timestamp_ns")
    if type(target_scene_id) is not str or not target_scene_id:
        raise SpecError("target_scene_id must be a non-empty string")
    flow: list[dict[str, Any]] = []
    for candidate in candidates:
        if type(candidate.candidate_id) is not str or not candidate.candidate_id:
            raise SpecError("candidate_id must be non-empty")
        digest = _sha(candidate.file_sha256, "file_sha256")
        candidate_time = calibrated_timestamp_ns(candidate.sensor_timestamp_ns, candidate.calibration)
        target_time_calibrated = calibrated_timestamp_ns(target_time, target_calibration)
        dt = abs(candidate_time - target_time_calibrated)
        metrics = camera_match_metrics(target_camera, ordinary_camera, candidate.camera)
        reasons: list[str] = []
        if candidate.scene_id != target_scene_id:
            reasons.append("SCENE_ID_MISMATCH")
        if dt > SYNC_TOLERANCE_NS:
            reasons.append("TARGET_TIME_ABOVE_10MS")
        if metrics.angle_microdegrees > 2_000_000:
            reasons.append("TARGET_ANGLE_ABOVE_2DEG")
        if metrics.position_ratio_ppm > 100_000:
            reasons.append("TARGET_POSITION_RATIO_ABOVE_010")
        if metrics.fov_microdegrees > 1_000_000:
            reasons.append("FOV_DIFFERENCE_ABOVE_1DEG")
        if not isinstance(candidate.identity_receipt, IdentityAgreement) or identity_decision(candidate.identity_receipt)[0] is False:
            reasons.append("IDENTITY_CONTRACT_FAILED")
        if not isinstance(candidate.view_pair_receipts, tuple) or validate_view_pair_receipts(candidate.view_pair_receipts, include_replacement=False)[0] is False:
            reasons.append("VIEW_PAIR_CONTRACT_FAILED")
        if set(candidate.domain_receipts) != {"support", "outside"} or any(
            not isinstance(receipt, ValidDomainReceipt)
            or receipt.domain != domain_name
            or valid_domain_decision(receipt)[0] is False
            for domain_name, receipt in candidate.domain_receipts.items()
        ):
            reasons.append("DOMAIN_CONTRACT_FAILED")
        key = (dt, metrics.angle_microdegrees, metrics.position_ratio_ppm, metrics.fov_microdegrees, digest, candidate.candidate_id.encode("utf-8"))
        flow.append({"candidate": candidate, "metrics": metrics, "dt_ns": dt, "eligible": not reasons, "reasons": tuple(reasons), "sort_key": key})
    eligible = sorted((record for record in flow if record["eligible"]), key=lambda record: record["sort_key"])
    if not eligible:
        raise SpecError("reference roster has no eligible candidate")
    return {"selected": eligible[0]["candidate"], "flow": tuple(flow), "eligible_order": tuple(record["candidate"].candidate_id for record in eligible)}


@dataclass(frozen=True)
class IdentityAgreement:
    roles: tuple[str, ...]
    support_weight: float
    valid_weight: float
    valid_weight_coverage: float
    agreement_weight: float
    agreement: float
    nonbackground_sets_equal: bool


def identity_agreement(
    identities: Mapping[str, Any], validities: Mapping[str, Any], support: Any,
    *, roles: tuple[str, ...],
) -> IdentityAgreement:
    if roles not in (("O", "R"), ("O", "R", "P")) or set(identities) != set(roles) or set(validities) != set(roles):
        raise SpecError("identity roles must be exactly O/R or O/R/P")
    w = _weights(support, "support")
    if float(np.sum(w)) <= 0.0:
        raise SpecError("identity support is empty")
    ids = {role: _identity(identities[role], f"identity_{role}", w.shape) for role in roles}
    valids = {role: _bool_mask(validities[role], f"valid_{role}", w.shape) for role in roles}
    common = np.logical_and.reduce([valids[role] for role in roles]) & (w > 0.0)
    support_weight = float(np.sum(w))
    valid_weight = float(np.sum(w[common]))
    if valid_weight <= 0.0:
        raise SpecError("identity common-valid denominator is zero")
    equal = np.ones(w.shape, dtype=bool)
    for role in roles[1:]:
        equal &= ids[role] == ids[roles[0]]
    agreement_weight = float(np.sum(w[common & equal]))
    sets = [set(int(value) for value in np.unique(ids[role][common]) if int(value) != 0) for role in roles]
    sets_equal = all(item == sets[0] for item in sets[1:])
    return IdentityAgreement(
        roles, support_weight, valid_weight, valid_weight / support_weight,
        agreement_weight, agreement_weight / valid_weight, sets_equal,
    )


def identity_decision(receipt: IdentityAgreement) -> tuple[bool, tuple[str, ...]]:
    if receipt.roles not in (("O", "R"), ("O", "R", "P")):
        raise SpecError("identity receipt roles are invalid")
    support_weight = _finite(receipt.support_weight, "support_weight")
    valid_weight = _finite(receipt.valid_weight, "valid_weight")
    agreement_weight = _finite(receipt.agreement_weight, "agreement_weight")
    valid_coverage = _finite(receipt.valid_weight_coverage, "valid_weight_coverage")
    agreement = _finite(receipt.agreement, "agreement")
    if (
        support_weight <= 0.0
        or valid_weight <= 0.0
        or valid_weight > support_weight
        or agreement_weight < 0.0
        or agreement_weight > valid_weight
        or not math.isclose(valid_coverage, valid_weight / support_weight, rel_tol=0.0, abs_tol=1e-15)
        or not math.isclose(agreement, agreement_weight / valid_weight, rel_tol=0.0, abs_tol=1e-15)
        or not 0.0 <= valid_coverage <= 1.0
        or not 0.0 <= agreement <= 1.0
        or type(receipt.nonbackground_sets_equal) is not bool
    ):
        raise SpecError("identity receipt fields are inconsistent")
    failures: list[str] = []
    if receipt.valid_weight_coverage < IDENTITY_VALID_WEIGHT_COVERAGE_MIN:
        failures.append("IDENTITY_VALID_WEIGHT_COVERAGE_BELOW_MIN")
    if receipt.agreement < IDENTITY_AGREEMENT_MIN:
        failures.append("IDENTITY_AGREEMENT_BELOW_MIN")
    if not receipt.nonbackground_sets_equal:
        failures.append("NONBACKGROUND_ID_SETS_DIFFER")
    return not failures, tuple(failures)


@dataclass(frozen=True)
class ViewPairReceipt:
    pair: str
    valid_pixels: int
    median_abs_rgb_by_channel: tuple[float, float, float]


def build_view_pair_receipt(pair: str, first_u8: Any, second_u8: Any, valid: Any) -> ViewPairReceipt:
    if type(pair) is not str or not pair:
        raise SpecError("view pair label must be non-empty")
    first = _output_x(first_u8, "first_u8", native=True)
    second = _output_x(second_u8, "second_u8", native=True)
    if first.shape != second.shape:
        raise SpecError("view pair RGB shapes differ")
    mask = _bool_mask(valid, "valid", first.shape[:2])
    count = int(np.count_nonzero(mask))
    if count == 0:
        raise SpecError("view pair has no valid pixels")
    medians = tuple(float(np.median(np.abs(first[..., channel][mask] - second[..., channel][mask]))) for channel in range(3))
    return ViewPairReceipt(pair, count, medians)


def validate_view_pair_receipts(receipts: Sequence[ViewPairReceipt], *, include_replacement: bool) -> tuple[bool, tuple[str, ...]]:
    required = {"O_R", "R_PREV_R", "R_R_NEXT"} | ({"P_R"} if include_replacement else set())
    seen: set[str] = set()
    failures: list[str] = []
    for receipt in receipts:
        if not isinstance(receipt, ViewPairReceipt) or receipt.pair not in required or receipt.pair in seen:
            raise SpecError("view-pair receipts contain duplicate, extra, or untyped pair")
        seen.add(receipt.pair)
        _strict_int(receipt.valid_pixels, "valid_pixels", minimum=1)
        if len(receipt.median_abs_rgb_by_channel) != 3:
            raise SpecError("view-pair receipt requires exactly three channel medians")
        values = tuple(_finite(value, "median_abs_rgb") for value in receipt.median_abs_rgb_by_channel)
        if any(value < 0.0 or value > 1.0 for value in values):
            raise SpecError("view-pair RGB median must lie in [0,1]")
        if any(value > 2.0 / 255.0 for value in values):
            failures.append(f"{receipt.pair}_RGB_MEDIAN_ABOVE_2_CODES")
    if seen != required or len(receipts) != len(required):
        raise SpecError("view-pair receipt set is incomplete")
    return not failures, tuple(failures)


@dataclass(frozen=True)
class ValidDomainReceipt:
    domain: str
    domain_denominator: int
    common_valid_numerator: int
    hole_numerator: int
    hole_denominator: int
    coverage: float
    hole_ratio: float


def valid_domain_receipt(domain_name: str, domain: Any, validities: Mapping[str, Any]) -> ValidDomainReceipt:
    if domain_name not in ("support", "outside"):
        raise SpecError("domain_name must be support or outside")
    domain_mask = _bool_mask(domain, "domain")
    if not validities:
        raise SpecError("validity mapping must be non-empty")
    masks = [_bool_mask(mask, f"valid_{role}", domain_mask.shape) for role, mask in sorted(validities.items())]
    common = np.logical_and.reduce(masks)
    denominator = int(np.count_nonzero(domain_mask))
    if denominator == 0:
        raise SpecError("declared valid domain is empty")
    common_count = int(np.count_nonzero(domain_mask & common))
    holes = denominator - common_count
    return ValidDomainReceipt(domain_name, denominator, common_count, holes, denominator, common_count / denominator, holes / denominator)


def valid_domain_decision(receipt: ValidDomainReceipt) -> tuple[bool, tuple[str, ...]]:
    if receipt.domain not in ("support", "outside"):
        raise SpecError("valid-domain receipt has unknown domain")
    denominator = _strict_int(receipt.domain_denominator, "domain_denominator", minimum=1)
    common = _strict_int(receipt.common_valid_numerator, "common_valid_numerator", minimum=0)
    holes = _strict_int(receipt.hole_numerator, "hole_numerator", minimum=0)
    hole_denominator = _strict_int(receipt.hole_denominator, "hole_denominator", minimum=1)
    coverage = _finite(receipt.coverage, "coverage")
    hole_ratio = _finite(receipt.hole_ratio, "hole_ratio")
    if (
        common + holes != denominator
        or hole_denominator != denominator
        or not math.isclose(coverage, common / denominator, rel_tol=0.0, abs_tol=1e-15)
        or not math.isclose(hole_ratio, holes / denominator, rel_tol=0.0, abs_tol=1e-15)
        or not 0.0 <= coverage <= 1.0
        or not 0.0 <= hole_ratio <= 1.0
    ):
        raise SpecError("valid-domain receipt fields are inconsistent")
    failures: list[str] = []
    if receipt.coverage < DOMAIN_COVERAGE_MIN:
        failures.append("COMMON_VALID_COVERAGE_BELOW_MIN")
    if receipt.hole_ratio > DOMAIN_HOLE_RATIO_MAX:
        failures.append("WARPING_HOLE_RATIO_ABOVE_MAX")
    return not failures, tuple(failures)


def normalized_rgb_mse(output_u8: Any, reference_u8: Any, valid: Any, weight: Any | None = None) -> float:
    output = _output_x(output_u8, "output_u8", native=True)
    reference = _output_x(reference_u8, "reference_u8", native=True)
    if output.shape != reference.shape:
        raise SpecError("output and reference RGB shapes differ")
    mask = _bool_mask(valid, "valid", output.shape[:2])
    spatial_weight = np.ones(mask.shape, dtype=np.float64) if weight is None else _weights(weight, "weight", mask.shape)
    effective = spatial_weight * mask.astype(np.float64)
    denominator = float(np.sum(effective))
    if denominator <= 0.0:
        raise SpecError("RGB loss denominator is zero")
    pixel_loss = np.mean((output - reference) ** 2, axis=2, dtype=np.float64)
    loss = float(np.sum(effective * pixel_loss) / denominator)
    if not 0.0 <= loss <= 1.0 or not math.isfinite(loss):
        raise SpecError("RGB loss left [0,1]")
    return loss


def local_benefit(edit_u8: Any, zero_u8: Any, reference_u8: Any, valid: Any, support: Any) -> float:
    return normalized_rgb_mse(edit_u8, reference_u8, valid, support) - normalized_rgb_mse(zero_u8, reference_u8, valid, support)


def matched_benefit(replacement_u8: Any, ordinary_reinsert_u8: Any, reference_u8: Any, valid: Any, support: Any) -> float:
    return normalized_rgb_mse(replacement_u8, reference_u8, valid, support) - normalized_rgb_mse(ordinary_reinsert_u8, reference_u8, valid, support)


def benefit_decision(benefit: Any, outside_loss_difference: Any) -> tuple[bool, tuple[str, ...]]:
    benefit_value = _finite(benefit, "benefit")
    outside_value = _finite(outside_loss_difference, "outside_loss_difference")
    if benefit_value < -1.0 or benefit_value > 1.0 or outside_value < -1.0 or outside_value > 1.0:
        raise SpecError("Benefit quantities must lie in [-1,1]")
    failures: list[str] = []
    if benefit_value < DELTA_B:
        failures.append("BENEFIT_BELOW_DELTA_B")
    if outside_value > DELTA_OUT:
        failures.append("OUTSIDE_NONINFERIORITY_FAILED")
    return not failures, tuple(failures)


@dataclass(frozen=True)
class ReinsertReceipt:
    role: str
    source_id: str
    source_content_sha256: str
    encoded_source_sha256: str
    attempt_id: str
    process_id: int
    fresh_process: bool
    process_isolation_spec_sha256: str
    source_adapter_sha256: str
    base_snapshot_sha256: str
    injection_point_sha256: str
    slot: int
    tensor_shape: tuple[int, ...]
    position_interface_sha256: str
    source_id_interface_sha256: str
    context_length: int
    quantization: str
    consumer_order: tuple[str, str]
    semantic_calls: int
    latent_calls: int
    semantic_tensor_sha256: str
    latent_tensor_sha256: str
    initial_noise_sha256: str
    rng_state_sha256: str
    target_roster_sha256: str
    trace_schema_sha256: str


_REINSERT_INVARIANTS = (
    "process_isolation_spec_sha256", "source_adapter_sha256", "base_snapshot_sha256", "injection_point_sha256",
    "slot", "tensor_shape", "position_interface_sha256", "source_id_interface_sha256",
    "context_length", "quantization", "consumer_order", "semantic_calls", "latent_calls",
    "initial_noise_sha256", "rng_state_sha256", "target_roster_sha256", "trace_schema_sha256",
)


def validate_matched_reinsert(ordinary: ReinsertReceipt, replacement: ReinsertReceipt) -> tuple[bool, tuple[str, ...]]:
    failures: list[str] = []
    if ordinary.role != "O_REINSERT" or replacement.role != "P_REPLACEMENT":
        failures.append("ROLE_MISMATCH")
    if not _strict_bool(ordinary.fresh_process, "ordinary.fresh_process") or not _strict_bool(replacement.fresh_process, "replacement.fresh_process"):
        failures.append("FRESH_PROCESS_REQUIRED")
    if ordinary.attempt_id == replacement.attempt_id or ordinary.process_id == replacement.process_id:
        failures.append("ATTEMPT_OR_PROCESS_NOT_DISTINCT")
    if (
        ordinary.source_id == replacement.source_id
        or ordinary.source_content_sha256 == replacement.source_content_sha256
        or ordinary.encoded_source_sha256 == replacement.encoded_source_sha256
    ):
        failures.append("SOURCE_CONTENT_NOT_DISTINCT")
    for receipt, prefix in ((ordinary, "ordinary"), (replacement, "replacement")):
        if type(receipt.source_id) is not str or not receipt.source_id or type(receipt.attempt_id) is not str or not receipt.attempt_id:
            raise SpecError(f"{prefix} source_id and attempt_id must be non-empty strings")
        _strict_int(receipt.process_id, f"{prefix}.process_id", minimum=1)
        _strict_int(receipt.slot, f"{prefix}.slot", minimum=0)
        _strict_int(receipt.context_length, f"{prefix}.context_length", minimum=1)
        _strict_int(receipt.semantic_calls, f"{prefix}.semantic_calls", minimum=0)
        _strict_int(receipt.latent_calls, f"{prefix}.latent_calls", minimum=0)
        if (
            not isinstance(receipt.tensor_shape, tuple)
            or not receipt.tensor_shape
            or any(type(value) is not int or value <= 0 for value in receipt.tensor_shape)
        ):
            raise SpecError(f"{prefix}.tensor_shape must be a non-empty tuple of positive integers")
        if receipt.quantization != "clip_[0,1];multiply_255;rint_ties_to_even;uint8":
            failures.append(f"{prefix.upper()}_QUANTIZATION_MISMATCH")
        for name in (
            "source_content_sha256", "encoded_source_sha256", "process_isolation_spec_sha256", "source_adapter_sha256", "base_snapshot_sha256",
            "injection_point_sha256", "position_interface_sha256", "source_id_interface_sha256",
            "semantic_tensor_sha256", "latent_tensor_sha256", "initial_noise_sha256",
            "rng_state_sha256", "target_roster_sha256", "trace_schema_sha256",
        ):
            _sha(getattr(receipt, name), f"{prefix}.{name}")
        if receipt.consumer_order != ("semantic", "latent") or receipt.semantic_calls != 1 or receipt.latent_calls != 1:
            failures.append(f"{prefix.upper()}_CONSUMER_TRACE_MISMATCH")
    for name in _REINSERT_INVARIANTS:
        if getattr(ordinary, name) != getattr(replacement, name):
            failures.append(f"INVARIANT_{name.upper()}_MISMATCH")
    return not failures, tuple(failures)


def replacement_recency_eligible(ordinary_insertion_event: Any, replacement_insertion_event: Any) -> bool:
    ordinary = _strict_int(ordinary_insertion_event, "ordinary_insertion_event", minimum=0)
    replacement = _strict_int(replacement_insertion_event, "replacement_insertion_event", minimum=0)
    return abs(replacement - ordinary) <= 2


def build_unselected_source_roster(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    boolean_fields = ("active", "selected", "is_target", "is_reference", "provenance_complete", "artifacts_complete", "renderable_all_targets")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    required = {"insertion_event", "source_id", "file_sha256", *boolean_fields}
    for raw in records:
        if set(raw) != required:
            raise SpecError("roster record schema mismatch")
        event = _strict_int(raw["insertion_event"], "insertion_event", minimum=0)
        source_id = raw["source_id"]
        if type(source_id) is not str or not source_id or source_id in seen:
            raise SpecError("source_id must be non-empty and unique")
        seen.add(source_id)
        digest = _sha(raw["file_sha256"], "file_sha256")
        flags = {name: _strict_bool(raw[name], name) for name in boolean_fields}
        reasons: list[str] = []
        if not flags["active"]: reasons.append("INACTIVE_OR_TOMBSTONED")
        if flags["selected"]: reasons.append("SELECTED_IN_ORDINARY_RUN")
        if flags["is_target"]: reasons.append("TARGET_OBSERVATION")
        if flags["is_reference"]: reasons.append("HELD_OUT_REFERENCE")
        if not flags["provenance_complete"]: reasons.append("PROVENANCE_INCOMPLETE")
        if not flags["artifacts_complete"]: reasons.append("SCIENTIFIC_ARTIFACTS_INCOMPLETE")
        if not flags["renderable_all_targets"]: reasons.append("NOT_RENDERABLE_FOR_ALL_TARGETS")
        normalized.append({"insertion_event": event, "source_id": source_id, "file_sha256": digest, **flags, "eligible_unselected": not reasons, "exclusion_reasons": tuple(reasons)})
    normalized.sort(key=lambda record: (record["insertion_event"], record["source_id"].encode("utf-8"), record["file_sha256"]))
    eligible = tuple(record for record in normalized if record["eligible_unselected"])
    lines = [f"{r['insertion_event']}\t{r['source_id']}\t{r['file_sha256']}\t{int(r['eligible_unselected'])}\t{','.join(r['exclusion_reasons'])}" for r in normalized]
    canonical = ("\n".join(lines) + ("\n" if lines else "")).encode("utf-8")
    return {"all_records": tuple(normalized), "eligible_records": eligible, "eligible_source_ids": tuple(r["source_id"] for r in eligible), "canonical_sha256": sha256(canonical).hexdigest()}
