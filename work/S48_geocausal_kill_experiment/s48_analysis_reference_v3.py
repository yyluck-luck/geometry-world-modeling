#!/usr/bin/env python3
"""Finite source-only reference implementation for the S48 V7 contract.

This module uses NumPy arrays supplied by synthetic tests.  It never opens an
experiment payload, imports a model stack, or runs a generation arm.  See
S48_NORMATIVE_ANALYSIS_SPEC_V3.md for the normative scope and blocked gates.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from hashlib import sha256
import math
from numbers import Real
import re
from typing import Any, Iterable, Mapping, Sequence
import zlib

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
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (Real, np.integer, np.floating)):
        raise SpecError(f"{name} must be a finite real scalar, not a coercible object")
    out = float(value)
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


def _canonical_lines_sha(domain: str, lines: Sequence[str]) -> str:
    if type(domain) is not str or not domain or "\n" in domain:
        raise SpecError("canonical hash domain must be a non-empty single line")
    if any(type(line) is not str or "\n" in line for line in lines):
        raise SpecError("canonical hash lines must be strings without embedded newlines")
    payload = (domain + "\n" + "\n".join(lines) + "\n").encode("utf-8")
    return sha256(payload).hexdigest()


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


@dataclass(frozen=True, order=True)
class CellKey:
    source_id: str
    target: str
    seed: str
    family: str
    sign: int


def _validate_cell_key(key: CellKey) -> None:
    if not isinstance(key, CellKey):
        raise SpecError("cell key must be a typed CellKey")
    for name in ("source_id", "target", "seed"):
        value = getattr(key, name)
        if type(value) is not str or not value or "\n" in value:
            raise SpecError(f"cell key {name} must be a non-empty single-line string")
    if key.family not in ("exposure_log_gain", "texture_highpass"):
        raise SpecError("cell key family is invalid")
    if type(key.sign) is not int or key.sign not in (-1, 1):
        raise SpecError("cell key sign must be exact -1 or +1")


@dataclass(frozen=True)
class ArmIdentityReceipt:
    state_sha256: str
    noise_sha256: str
    rng_state_sha256: str
    snapshot_sha256: str
    target_roster_sha256: str
    source_adapter_sha256: str
    consumer_trace_schema_sha256: str
    slot: int
    canonical_sha256: str


def build_arm_identity(
    *, state_sha256: str, noise_sha256: str, rng_state_sha256: str,
    snapshot_sha256: str, target_roster_sha256: str, source_adapter_sha256: str,
    consumer_trace_schema_sha256: str, slot: int,
) -> ArmIdentityReceipt:
    digests = tuple(
        _sha(value, name)
        for value, name in (
            (state_sha256, "state_sha256"), (noise_sha256, "noise_sha256"),
            (rng_state_sha256, "rng_state_sha256"), (snapshot_sha256, "snapshot_sha256"),
            (target_roster_sha256, "target_roster_sha256"), (source_adapter_sha256, "source_adapter_sha256"),
            (consumer_trace_schema_sha256, "consumer_trace_schema_sha256"),
        )
    )
    slot_value = _strict_int(slot, "slot", minimum=0)
    digest = _canonical_lines_sha("S48_ARM_IDENTITY_V3", (*digests, str(slot_value)))
    return ArmIdentityReceipt(*digests, slot_value, digest)


def validate_arm_identity(receipt: ArmIdentityReceipt) -> None:
    if not isinstance(receipt, ArmIdentityReceipt):
        raise SpecError("arm identity must be typed")
    digests = tuple(
        _sha(getattr(receipt, name), name)
        for name in (
            "state_sha256", "noise_sha256", "rng_state_sha256", "snapshot_sha256",
            "target_roster_sha256", "source_adapter_sha256", "consumer_trace_schema_sha256",
        )
    )
    slot = _strict_int(receipt.slot, "slot", minimum=0)
    if receipt.canonical_sha256 != _canonical_lines_sha("S48_ARM_IDENTITY_V3", (*digests, str(slot))):
        raise SpecError("arm identity canonical hash mismatch")


@dataclass(frozen=True)
class InfluenceReceipt:
    key: CellKey
    arm_identity: ArmIdentityReceipt
    replay: "ReplayLedger"
    arm_identity_sha256: str
    replay_ledger_sha256: str
    outputs_u8: tuple[np.ndarray, ...]
    target_edit_sha256: str
    target_zero_sha256: str
    negative_edit_sha256: str
    negative_zero_sha256: str
    positive_edit_sha256: str
    positive_zero_sha256: str
    target_effect_sha256: str
    negative_effect_sha256: str
    positive_effect_sha256: str
    target_effect_mean: float
    negative_effect_mean: float
    positive_effect_mean: float
    tau_output: float
    target_d: float
    positive_d: float
    target_observable: bool
    positive_control_passed: bool
    canonical_sha256: str


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


def _strict_f64_weight(value: Any, name: str, shape: tuple[int, int] | None = None) -> np.ndarray:
    if not isinstance(value, np.ndarray) or value.dtype != np.dtype(np.float64):
        raise SpecError(f"{name} must be a numpy.ndarray with dtype exactly float64")
    return _weights(value, name, shape)


def _readonly_f64_weight(value: Any, name: str, shape: tuple[int, int] | None = None) -> np.ndarray:
    arr = np.array(_strict_f64_weight(value, name, shape), dtype=np.float64, order="C", copy=True)
    arr.setflags(write=False)
    return arr


@dataclass(frozen=True)
class PlaceboMaskLedger:
    family: str
    generator_sha256: str
    shape: tuple[int, int]
    compressed_masks: tuple[bytes, ...]
    mask_sha256s: tuple[str, ...]
    compressed_sha256s: tuple[str, ...]
    canonical_sha256: str


def _placebo_ledger_hash(
    family: str, generator_sha256: str, shape: tuple[int, int],
    mask_sha256s: Sequence[str], compressed_sha256s: Sequence[str],
) -> str:
    return _canonical_lines_sha(
        "S48_PLACEBO_MASK_LEDGER_V3",
        (family, generator_sha256, f"{shape[0]},{shape[1]}", *(f"{a}:{b}" for a, b in zip(mask_sha256s, compressed_sha256s))),
    )


def build_placebo_mask_ledger(
    placebo_supports: Sequence[Any], *, family: str, generator_sha256: str,
) -> PlaceboMaskLedger:
    if family not in ("shape", "camera", "source"):
        raise SpecError("placebo family must be shape, camera, or source")
    generator_digest = _sha(generator_sha256, "generator_sha256")
    if isinstance(placebo_supports, (str, bytes)):
        raise SpecError("placebo mask ledger requires an indexable mask sequence")
    try:
        count = len(placebo_supports)
    except TypeError as exc:
        raise SpecError("placebo mask ledger requires an indexable mask sequence") from exc
    if count == 0:
        raise SpecError("placebo mask ledger must contain at least one mask")
    first = _strict_f64_weight(placebo_supports[0], "placebo_support[0]")
    shape = first.shape
    hashes_list: list[str] = []
    compressed_list: list[bytes] = []
    for index in range(count):
        mask = _strict_f64_weight(placebo_supports[index], f"placebo_support[{index}]", shape)
        area = float(np.mean(mask))
        if not 0.0 < area < 1.0:
            raise SpecError(f"placebo_support[{index}] area must lie strictly in (0,1)")
        canonical = np.asarray(mask, dtype="<f8", order="C")
        hashes_list.append(_canonical_array_sha(f"S48_{family.upper()}_PLACEBO_MASK_V3", canonical))
        compressed_list.append(zlib.compress(canonical.tobytes(order="C"), level=9))
    hashes = tuple(hashes_list)
    if len(set(hashes)) != len(hashes):
        raise SpecError("placebo mask ledger contains duplicate masks")
    compressed = tuple(compressed_list)
    compressed_hashes = tuple(sha256(blob).hexdigest() for blob in compressed)
    return PlaceboMaskLedger(
        family, generator_digest, shape, compressed, hashes, compressed_hashes,
        _placebo_ledger_hash(family, generator_digest, shape, hashes, compressed_hashes),
    )


def _decode_placebo_mask(blob: bytes, shape: tuple[int, int], name: str) -> np.ndarray:
    if type(blob) is not bytes:
        raise SpecError(f"{name} compressed mask must be bytes")
    try:
        raw = zlib.decompress(blob)
    except zlib.error as exc:
        raise SpecError(f"{name} compressed mask is invalid") from exc
    expected = shape[0] * shape[1] * 8
    if len(raw) != expected:
        raise SpecError(f"{name} decompressed byte length mismatch")
    arr = np.frombuffer(raw, dtype="<f8").reshape(shape)
    return _strict_f64_weight(arr, name, shape)


def validate_placebo_mask_ledger(ledger: PlaceboMaskLedger, *, family: str, shape: tuple[int, int]) -> None:
    if not isinstance(ledger, PlaceboMaskLedger) or ledger.family != family:
        raise SpecError(f"{family} placebo ledger has wrong type or family")
    _sha(ledger.generator_sha256, f"{family}.generator_sha256")
    if ledger.shape != shape or not isinstance(ledger.compressed_masks, tuple) or not isinstance(ledger.mask_sha256s, tuple) or not isinstance(ledger.compressed_sha256s, tuple):
        raise SpecError(f"{family} placebo ledger shape/container mismatch")
    if len(ledger.compressed_masks) == 0 or len(ledger.compressed_masks) != len(ledger.mask_sha256s) or len(ledger.compressed_masks) != len(ledger.compressed_sha256s):
        raise SpecError(f"{family} placebo ledger count mismatch")
    recomputed: list[str] = []
    compressed_hashes: list[str] = []
    for index, blob in enumerate(ledger.compressed_masks):
        arr = _decode_placebo_mask(blob, shape, f"{family}.masks[{index}]")
        area = float(np.mean(arr))
        if not 0.0 < area < 1.0:
            raise SpecError(f"{family}.masks[{index}] area must lie strictly in (0,1)")
        recomputed.append(_canonical_array_sha(f"S48_{family.upper()}_PLACEBO_MASK_V3", arr))
        compressed_hashes.append(sha256(blob).hexdigest())
    hashes = tuple(recomputed)
    compressed_digests = tuple(compressed_hashes)
    if hashes != ledger.mask_sha256s or compressed_digests != ledger.compressed_sha256s or len(set(hashes)) != len(hashes):
        raise SpecError(f"{family} placebo mask hashes are stale, reordered, or duplicated")
    expected_hash = _placebo_ledger_hash(family, ledger.generator_sha256, shape, hashes, compressed_digests)
    if ledger.canonical_sha256 != expected_hash:
        raise SpecError(f"{family} placebo ledger canonical hash mismatch")


@dataclass(frozen=True)
class TailReceipt:
    family: str
    ledger_sha256: str
    effect_sha256: str
    true_support_sha256: str
    count: int
    true_mass: float
    lower_median: float
    tail_rank: float
    placebo_masses_sha256: str


def tail_from_mask_ledger(effect: Any, true_support: Any, ledger: PlaceboMaskLedger, *, family: str) -> TailReceipt:
    e = _strict_f64_weight(effect, "effect")
    support = _strict_f64_weight(true_support, "true_support", e.shape)
    validate_placebo_mask_ledger(ledger, family=family, shape=e.shape)
    effect_hash = _canonical_array_sha("S48_TARGET_EFFECT_MAP_V3", e)
    support_hash = _canonical_array_sha("S48_TRUE_SUPPORT_V3", support)
    true_mass = localization_metrics(e, support).mass
    masses_list: list[float] = []
    for index, blob in enumerate(ledger.compressed_masks):
        candidate = _decode_placebo_mask(blob, e.shape, f"{family}.masks[{index}]")
        if _canonical_array_sha("S48_TRUE_SUPPORT_V3", candidate) == support_hash:
            raise SpecError(f"{family} placebo ledger contains the true support")
        masses_list.append(localization_metrics(e, candidate).mass)
    masses = np.asarray(masses_list, dtype="<f8")
    ordered = np.sort(masses, kind="stable")
    median = float(ordered[(ordered.size - 1) // 2])
    rank = (1 + int(np.count_nonzero(ordered >= true_mass))) / float(ordered.size + 1)
    return TailReceipt(
        family, ledger.canonical_sha256, effect_hash, support_hash, len(ledger.compressed_masks), true_mass,
        median, rank, _canonical_array_sha(f"S48_{family.upper()}_PLACEBO_MASSES_V3", masses),
    )


@dataclass(frozen=True)
class SupportEffectReceipt:
    key: CellKey
    influence: InfluenceReceipt
    support: np.ndarray
    shape_ledger: PlaceboMaskLedger
    camera_ledger: PlaceboMaskLedger
    influence_sha256: str
    effect_sha256: str
    negative_effect_sha256: str
    support_sha256: str
    shape_tail: TailReceipt
    camera_tail: TailReceipt
    target_area: float
    target_mass: float
    target_l_area: float
    target_er: float
    negative_l_area_same_support: float
    negative_full_effect_ratio: float
    target_observable: bool
    positive_control_passed: bool
    alignment_passed: bool
    reasons: tuple[str, ...]
    canonical_sha256: str


def _support_effect_hash_lines(receipt: SupportEffectReceipt) -> tuple[str, ...]:
    return (
        receipt.key.source_id, receipt.key.target, receipt.key.seed, receipt.key.family, str(receipt.key.sign),
        receipt.influence_sha256, receipt.effect_sha256, receipt.negative_effect_sha256, receipt.support_sha256,
        receipt.shape_tail.ledger_sha256, receipt.shape_tail.placebo_masses_sha256,
        receipt.camera_tail.ledger_sha256, receipt.camera_tail.placebo_masses_sha256,
        receipt.target_area.hex(), receipt.target_mass.hex(), receipt.target_l_area.hex(), receipt.target_er.hex(),
        receipt.negative_l_area_same_support.hex(), receipt.negative_full_effect_ratio.hex(),
        str(int(receipt.target_observable)), str(int(receipt.positive_control_passed)),
        str(int(receipt.alignment_passed)), ",".join(receipt.reasons),
    )


def support_effect_decision(
    support: Any,
    *,
    influence: InfluenceReceipt,
    shape_ledger: PlaceboMaskLedger,
    camera_ledger: PlaceboMaskLedger,
) -> SupportEffectReceipt:
    validate_influence_receipt(influence)
    target = direct_effect_map(influence.outputs_u8[0], influence.outputs_u8[1])
    negative = direct_effect_map(influence.outputs_u8[2], influence.outputs_u8[3])
    w = _readonly_f64_weight(support, "support", target.shape)
    if not np.array_equal(w, influence.replay.support):
        raise SpecError("support-effect support differs from the bound replay/guard support")
    target_hash = _canonical_array_sha("S48_TARGET_EFFECT_MAP_V3", target)
    negative_hash = _canonical_array_sha("S48_NEGATIVE_EFFECT_MAP_V3", negative)
    if target_hash != influence.target_effect_sha256 or negative_hash != influence.negative_effect_sha256:
        raise SpecError("support-effect maps do not match the bound Influence receipt")
    target_metrics = localization_metrics(target, w)
    negative_total = float(np.sum(negative))
    if negative_total <= EPS:
        area = target_metrics.area
        negative_metrics = LocalizationMetrics(area, 0.0, 0.0, -area, 0.0)
    else:
        negative_metrics = localization_metrics(negative, w)
    if target_metrics.effect_mean <= EPS:
        raise SpecError("target effect mean is zero")
    negative_ratio = negative_metrics.effect_mean / target_metrics.effect_mean
    shape_tail = tail_from_mask_ledger(target, w, shape_ledger, family="shape")
    camera_tail = tail_from_mask_ledger(target, w, camera_ledger, family="camera")
    support_hash = _canonical_array_sha("S48_TRUE_SUPPORT_V3", w)
    if shape_tail.true_support_sha256 != support_hash or camera_tail.true_support_sha256 != support_hash:
        raise SpecError("tail receipt support identity mismatch")
    failures: list[str] = []
    if not influence.target_observable:
        failures.append("TARGET_OBSERVABLE_INFLUENCE_NOT_PASSED")
    if not influence.positive_control_passed:
        failures.append("POSITIVE_CONTROL_NOT_PASSED")
    if target_metrics.enrichment_ratio <= 1.0:
        failures.append("TARGET_ER_NOT_ABOVE_ONE")
    if target_metrics.l_area < LOCALIZATION_L_AREA_MIN:
        failures.append("TARGET_L_AREA_BELOW_MIN")
    if negative_ratio > NEGATIVE_FULL_EFFECT_RATIO_MAX:
        failures.append("NEGATIVE_FULL_EFFECT_RATIO_ABOVE_MAX")
    if negative_metrics.l_area > NEGATIVE_SUPPORT_L_AREA_MAX:
        failures.append("NEGATIVE_SUPPORT_LOCALIZATION_ABOVE_MAX")
    for label, tail in (("SHAPE", shape_tail), ("CAMERA", camera_tail)):
        if tail.count < 199:
            failures.append(f"{label}_PLACEBO_COUNT_BELOW_199")
        if tail.true_mass <= tail.lower_median:
            failures.append(f"{label}_TRUE_MASS_NOT_ABOVE_MEDIAN")
        if tail.tail_rank > 0.05:
            failures.append(f"{label}_TAIL_RANK_ABOVE_005")
    provisional = SupportEffectReceipt(
        influence.key, influence, w, shape_ledger, camera_ledger,
        influence.canonical_sha256, target_hash, negative_hash, support_hash,
        shape_tail, camera_tail, target_metrics.area, target_metrics.mass, target_metrics.l_area,
        target_metrics.enrichment_ratio, negative_metrics.l_area, negative_ratio,
        influence.target_observable, influence.positive_control_passed,
        not failures, tuple(failures), "0" * 64,
    )
    digest = _canonical_lines_sha("S48_SUPPORT_EFFECT_RECEIPT_V3", _support_effect_hash_lines(provisional))
    return SupportEffectReceipt(**{**provisional.__dict__, "canonical_sha256": digest})


def validate_support_effect_receipt(receipt: SupportEffectReceipt) -> None:
    if not isinstance(receipt, SupportEffectReceipt):
        raise SpecError("support-effect receipt must be typed")
    _validate_cell_key(receipt.key)
    validate_influence_receipt(receipt.influence)
    if receipt.influence.key != receipt.key or receipt.influence_sha256 != receipt.influence.canonical_sha256:
        raise SpecError("support-effect receipt does not bind its exact Influence receipt")
    support = _strict_f64_weight(receipt.support, "support-effect support", (NATIVE_HEIGHT, NATIVE_WIDTH))
    if support.flags.writeable:
        raise SpecError("support-effect support must be frozen read-only evidence")
    if not np.array_equal(support, receipt.influence.replay.support):
        raise SpecError("support-effect support differs from the bound replay/guard support")
    support_hash = _canonical_array_sha("S48_TRUE_SUPPORT_V3", support)
    if receipt.support_sha256 != support_hash:
        raise SpecError("support-effect support hash mismatch")
    validate_placebo_mask_ledger(receipt.shape_ledger, family="shape", shape=support.shape)
    validate_placebo_mask_ledger(receipt.camera_ledger, family="camera", shape=support.shape)
    if receipt.shape_tail.ledger_sha256 != receipt.shape_ledger.canonical_sha256 or receipt.camera_tail.ledger_sha256 != receipt.camera_ledger.canonical_sha256:
        raise SpecError("support-effect tails do not bind the stored mask ledgers")
    for name in ("influence_sha256", "effect_sha256", "negative_effect_sha256", "support_sha256"):
        _sha(getattr(receipt, name), name)
    for name in ("target_area", "target_mass", "target_l_area", "target_er", "negative_l_area_same_support", "negative_full_effect_ratio"):
        _finite(getattr(receipt, name), name)
    for family, tail in (("shape", receipt.shape_tail), ("camera", receipt.camera_tail)):
        if not isinstance(tail, TailReceipt) or tail.family != family:
            raise SpecError(f"{family} tail is untyped or has the wrong family")
        for name in ("ledger_sha256", "effect_sha256", "true_support_sha256", "placebo_masses_sha256"):
            _sha(getattr(tail, name), f"{family}_tail.{name}")
        if tail.effect_sha256 != receipt.effect_sha256 or tail.true_support_sha256 != receipt.support_sha256:
            raise SpecError(f"{family} tail is not bound to the receipt effect/support")
        count = _strict_int(tail.count, f"{family}_tail.count", minimum=1)
        for name in ("true_mass", "lower_median", "tail_rank"):
            value = _finite(getattr(tail, name), f"{family}_tail.{name}")
            if not 0.0 <= value <= 1.0:
                raise SpecError(f"{family} tail {name} must lie in [0,1]")
        if tail.tail_rank < 1.0 / (count + 1.0):
            raise SpecError(f"{family} tail rank is outside its finite-sample domain")
    target_effect = direct_effect_map(receipt.influence.outputs_u8[0], receipt.influence.outputs_u8[1])
    negative_effect = direct_effect_map(receipt.influence.outputs_u8[2], receipt.influence.outputs_u8[3])
    if receipt.effect_sha256 != _canonical_array_sha("S48_TARGET_EFFECT_MAP_V3", target_effect) or receipt.negative_effect_sha256 != _canonical_array_sha("S48_NEGATIVE_EFFECT_MAP_V3", negative_effect):
        raise SpecError("support-effect maps do not derive from the bound Influence outputs")
    expected_shape_tail = tail_from_mask_ledger(target_effect, support, receipt.shape_ledger, family="shape")
    expected_camera_tail = tail_from_mask_ledger(target_effect, support, receipt.camera_ledger, family="camera")
    if receipt.shape_tail != expected_shape_tail or receipt.camera_tail != expected_camera_tail:
        raise SpecError("support-effect tail values were injected or are stale")
    target_metrics = localization_metrics(target_effect, support)
    if float(np.sum(negative_effect)) <= EPS:
        negative_l_area = -target_metrics.area
        negative_mean = 0.0
    else:
        negative_metrics = localization_metrics(negative_effect, support)
        negative_l_area = negative_metrics.l_area
        negative_mean = negative_metrics.effect_mean
    negative_ratio = negative_mean / target_metrics.effect_mean
    expected_scalars = (
        target_metrics.area, target_metrics.mass, target_metrics.l_area, target_metrics.enrichment_ratio,
        negative_l_area, negative_ratio,
    )
    recorded_scalars = (
        receipt.target_area, receipt.target_mass, receipt.target_l_area, receipt.target_er,
        receipt.negative_l_area_same_support, receipt.negative_full_effect_ratio,
    )
    if any(not math.isclose(recorded, expected_value, rel_tol=0.0, abs_tol=1e-15) for recorded, expected_value in zip(recorded_scalars, expected_scalars)):
        raise SpecError("support-effect scalars are not derived from bound evidence")
    if not 0.0 < receipt.target_area < 1.0 or not 0.0 <= receipt.target_mass <= 1.0 or receipt.target_er <= 0.0:
        raise SpecError("support-effect target scalar domain invalid")
    if not -1.0 <= receipt.target_l_area <= 1.0 or not -1.0 <= receipt.negative_l_area_same_support <= 1.0 or receipt.negative_full_effect_ratio < 0.0:
        raise SpecError("support-effect localization scalar domain invalid")
    if type(receipt.target_observable) is not bool or type(receipt.positive_control_passed) is not bool:
        raise SpecError("support-effect Influence flags must be bool")
    expected_reasons: list[str] = []
    if not receipt.target_observable:
        expected_reasons.append("TARGET_OBSERVABLE_INFLUENCE_NOT_PASSED")
    if not receipt.positive_control_passed:
        expected_reasons.append("POSITIVE_CONTROL_NOT_PASSED")
    if receipt.target_er <= 1.0:
        expected_reasons.append("TARGET_ER_NOT_ABOVE_ONE")
    if receipt.target_l_area < LOCALIZATION_L_AREA_MIN:
        expected_reasons.append("TARGET_L_AREA_BELOW_MIN")
    if receipt.negative_full_effect_ratio > NEGATIVE_FULL_EFFECT_RATIO_MAX:
        expected_reasons.append("NEGATIVE_FULL_EFFECT_RATIO_ABOVE_MAX")
    if receipt.negative_l_area_same_support > NEGATIVE_SUPPORT_L_AREA_MAX:
        expected_reasons.append("NEGATIVE_SUPPORT_LOCALIZATION_ABOVE_MAX")
    for label, tail in (("SHAPE", receipt.shape_tail), ("CAMERA", receipt.camera_tail)):
        if tail.count < 199:
            expected_reasons.append(f"{label}_PLACEBO_COUNT_BELOW_199")
        if tail.true_mass <= tail.lower_median:
            expected_reasons.append(f"{label}_TRUE_MASS_NOT_ABOVE_MEDIAN")
        if tail.tail_rank > 0.05:
            expected_reasons.append(f"{label}_TAIL_RANK_ABOVE_005")
    if type(receipt.alignment_passed) is not bool or not isinstance(receipt.reasons, tuple):
        raise SpecError("support-effect decision fields are untyped")
    if receipt.reasons != tuple(expected_reasons) or receipt.alignment_passed != (len(expected_reasons) == 0):
        raise SpecError("support-effect decision and reasons disagree")
    expected = _canonical_lines_sha("S48_SUPPORT_EFFECT_RECEIPT_V3", _support_effect_hash_lines(receipt))
    if receipt.canonical_sha256 != expected:
        raise SpecError("support-effect receipt canonical hash mismatch")


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
class ReplayInstanceEvidence:
    seed: str
    target: str
    replay_index: int
    state_sha256: str
    noise_sha256: str
    rng_state_sha256: str
    snapshot_sha256: str
    target_roster_sha256: str
    output_u8: np.ndarray
    output_sha256: str


@dataclass(frozen=True)
class ReplayPairReceipt:
    seed: str
    target: str
    replay_i: int
    replay_j: int
    output_i_sha256: str
    output_j_sha256: str
    full_frame_distance: float
    metrics: ArmGuardMetrics
    canonical_sha256: str


@dataclass(frozen=True)
class ReplayLedger:
    seed: str
    target: str
    state_sha256: str
    noise_sha256: str
    rng_state_sha256: str
    snapshot_sha256: str
    target_roster_sha256: str
    support: np.ndarray
    support_sha256: str
    instances: tuple[ReplayInstanceEvidence, ...]
    pairs: tuple[ReplayPairReceipt, ...]
    tau_output: float
    canonical_sha256: str


def _output_sha(value: Any, domain: str) -> str:
    return _canonical_array_sha(domain, _u8_rgb(value, domain, native=True))


def _replay_pair_lines(pair: ReplayPairReceipt) -> tuple[str, ...]:
    metric_lines = tuple(f"{field.name}={getattr(pair.metrics, field.name)!r}" for field in fields(ArmGuardMetrics))
    return (
        pair.seed, pair.target, str(pair.replay_i), str(pair.replay_j), pair.output_i_sha256,
        pair.output_j_sha256, pair.full_frame_distance.hex(), *metric_lines,
    )


def build_replay_ledger(
    outputs: Sequence[Any], support: Any, *, seed: str, target: str,
    state_sha256: str, noise_sha256: str, rng_state_sha256: str,
    snapshot_sha256: str, target_roster_sha256: str,
) -> ReplayLedger:
    if type(seed) is not str or not seed or type(target) is not str or not target:
        raise SpecError("replay seed and target must be non-empty strings")
    if not isinstance(outputs, (tuple, list)) or len(outputs) != 4:
        raise SpecError("replay ledger requires exactly four output instances")
    identities = tuple(
        _sha(value, name)
        for value, name in (
            (state_sha256, "state_sha256"), (noise_sha256, "noise_sha256"),
            (rng_state_sha256, "rng_state_sha256"), (snapshot_sha256, "snapshot_sha256"),
            (target_roster_sha256, "target_roster_sha256"),
        )
    )
    support_arr = _readonly_f64_weight(support, "replay_support", (NATIVE_HEIGHT, NATIVE_WIDTH))
    support_hash = _canonical_array_sha("S48_REPLAY_SUPPORT_V3", support_arr)
    instances: list[ReplayInstanceEvidence] = []
    for index, output in enumerate(outputs):
        array = np.array(_u8_rgb(output, f"replay_output[{index}]", native=True), dtype=np.uint8, order="C", copy=True)
        array.setflags(write=False)
        output_hash = _canonical_array_sha("S48_REPLAY_OUTPUT_V3", array)
        instances.append(ReplayInstanceEvidence(seed, target, index, *identities, array, output_hash))
    pairs: list[ReplayPairReceipt] = []
    for i in range(4):
        for j in range(i + 1, 4):
            distance = float(np.mean(direct_effect_map(instances[i].output_u8, instances[j].output_u8)))
            metrics = arm_guard_metrics(instances[i].output_u8, instances[j].output_u8, support_arr)
            provisional = ReplayPairReceipt(seed, target, i, j, instances[i].output_sha256, instances[j].output_sha256, distance, metrics, "0" * 64)
            digest = _canonical_lines_sha("S48_REPLAY_PAIR_V3", _replay_pair_lines(provisional))
            pairs.append(ReplayPairReceipt(**{**provisional.__dict__, "canonical_sha256": digest}))
    tau = max(1.0e-6, max(pair.full_frame_distance for pair in pairs))
    lines = (
        seed, target, *identities, support_hash,
        *(instance.output_sha256 for instance in instances),
        *(pair.canonical_sha256 for pair in pairs), tau.hex(),
    )
    return ReplayLedger(seed, target, *identities, support_arr, support_hash, tuple(instances), tuple(pairs), tau, _canonical_lines_sha("S48_REPLAY_LEDGER_V3", lines))


def validate_replay_ledger(ledger: ReplayLedger) -> None:
    if not isinstance(ledger, ReplayLedger):
        raise SpecError("replay evidence must be a typed ReplayLedger")
    if type(ledger.seed) is not str or not ledger.seed or type(ledger.target) is not str or not ledger.target:
        raise SpecError("replay ledger seed/target invalid")
    identity_values = tuple(
        _sha(getattr(ledger, name), name)
        for name in ("state_sha256", "noise_sha256", "rng_state_sha256", "snapshot_sha256", "target_roster_sha256")
    )
    support = _strict_f64_weight(ledger.support, "replay support", (NATIVE_HEIGHT, NATIVE_WIDTH))
    if support.flags.writeable:
        raise SpecError("replay support must be frozen read-only evidence")
    if ledger.support_sha256 != _canonical_array_sha("S48_REPLAY_SUPPORT_V3", support):
        raise SpecError("replay support hash mismatch")
    if not isinstance(ledger.instances, tuple) or len(ledger.instances) != 4:
        raise SpecError("replay ledger must bind exactly four instances")
    instances: dict[int, ReplayInstanceEvidence] = {}
    for instance in ledger.instances:
        if not isinstance(instance, ReplayInstanceEvidence):
            raise SpecError("replay instance is untyped")
        index = _strict_int(instance.replay_index, "replay_index", minimum=0)
        if index > 3 or index in instances:
            raise SpecError("replay instance index is duplicate or outside 0..3")
        if instance.seed != ledger.seed or instance.target != ledger.target:
            raise SpecError("replay instance seed/target mismatch")
        if tuple(getattr(instance, name) for name in ("state_sha256", "noise_sha256", "rng_state_sha256", "snapshot_sha256", "target_roster_sha256")) != identity_values:
            raise SpecError("replay instance state identity mismatch")
        output = _u8_rgb(instance.output_u8, "replay instance output", native=True)
        if output.flags.writeable:
            raise SpecError("replay instance output must be frozen read-only evidence")
        expected_output_hash = _canonical_array_sha("S48_REPLAY_OUTPUT_V3", output)
        if instance.output_sha256 != expected_output_hash:
            raise SpecError("replay instance output hash mismatch")
        instances[index] = instance
    if set(instances) != set(range(4)):
        raise SpecError("replay instance set must be exactly 0..3")
    expected_pairs = {(i, j) for i in range(4) for j in range(i + 1, 4)}
    if not isinstance(ledger.pairs, tuple) or len(ledger.pairs) != 6:
        raise SpecError("replay ledger must bind exactly six pairs")
    seen: set[tuple[int, int]] = set()
    expected_pair_order = tuple((i, j) for i in range(4) for j in range(i + 1, 4))
    for position, pair in enumerate(ledger.pairs):
        if not isinstance(pair, ReplayPairReceipt) or pair.seed != ledger.seed or pair.target != ledger.target:
            raise SpecError("replay pair type or seed/target mismatch")
        key = (_strict_int(pair.replay_i, "replay_i", minimum=0), _strict_int(pair.replay_j, "replay_j", minimum=0))
        if key not in expected_pairs or key in seen:
            raise SpecError("replay pair is reversed, extra, or duplicate")
        if key != expected_pair_order[position]:
            raise SpecError("replay pairs are not in canonical lexicographic order")
        seen.add(key)
        left, right = instances[key[0]], instances[key[1]]
        if pair.output_i_sha256 != left.output_sha256 or pair.output_j_sha256 != right.output_sha256:
            raise SpecError("replay pair output identity mismatch")
        actual_distance = float(np.mean(direct_effect_map(left.output_u8, right.output_u8)))
        distance = _finite(pair.full_frame_distance, "full_frame_distance")
        if not 0.0 <= distance <= 1.0 or not math.isclose(distance, actual_distance, rel_tol=0.0, abs_tol=1e-15):
            raise SpecError("replay pair full-frame distance is not derived from bound outputs")
        _validate_guard_metrics(pair.metrics)
        if pair.metrics != arm_guard_metrics(left.output_u8, right.output_u8, support):
            raise SpecError("replay guard metrics are not derived from bound outputs/support")
        expected_pair_hash = _canonical_lines_sha("S48_REPLAY_PAIR_V3", _replay_pair_lines(pair))
        if pair.canonical_sha256 != expected_pair_hash:
            raise SpecError("replay pair canonical hash mismatch")
    if seen != expected_pairs:
        raise SpecError("replay pair set is incomplete")
    actual_tau = max(1.0e-6, max(pair.full_frame_distance for pair in ledger.pairs))
    tau = _finite(ledger.tau_output, "tau_output")
    if not math.isclose(tau, actual_tau, rel_tol=0.0, abs_tol=1e-15):
        raise SpecError("tau_output is not derived from all six replay distances")
    lines = (
        ledger.seed, ledger.target, *identity_values, ledger.support_sha256,
        *(instances[index].output_sha256 for index in range(4)),
        *(pair.canonical_sha256 for pair in ledger.pairs), tau.hex(),
    )
    if ledger.canonical_sha256 != _canonical_lines_sha("S48_REPLAY_LEDGER_V3", lines):
        raise SpecError("replay ledger canonical hash mismatch")


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


def replay_guard_floors(ledger: ReplayLedger) -> GuardFloors:
    validate_replay_ledger(ledger)
    maxima = {name: max(_finite(getattr(receipt.metrics, name), name) for receipt in ledger.pairs) for name in _FLOOR_FIELDS}
    floors = GuardFloors(**maxima)
    for prefix in ("global", "support", "neighborhood"):
        if getattr(floors, f"{prefix}_p95_px") < getattr(floors, f"{prefix}_median_px"):
            raise SpecError("replay floor p95 must be >= median")
    return floors


def _influence_hash_lines(receipt: InfluenceReceipt) -> tuple[str, ...]:
    return (
        receipt.key.source_id, receipt.key.target, receipt.key.seed, receipt.key.family, str(receipt.key.sign),
        receipt.arm_identity_sha256, receipt.replay_ledger_sha256, receipt.target_edit_sha256, receipt.target_zero_sha256,
        receipt.negative_edit_sha256, receipt.negative_zero_sha256, receipt.positive_edit_sha256,
        receipt.positive_zero_sha256, receipt.target_effect_sha256, receipt.negative_effect_sha256,
        receipt.positive_effect_sha256, receipt.target_effect_mean.hex(), receipt.negative_effect_mean.hex(),
        receipt.positive_effect_mean.hex(), receipt.tau_output.hex(), receipt.target_d.hex(),
        receipt.positive_d.hex(), str(int(receipt.target_observable)), str(int(receipt.positive_control_passed)),
    )


def build_influence_receipt(
    target_edit_u8: Any, target_zero_u8: Any,
    negative_edit_u8: Any, negative_zero_u8: Any,
    positive_edit_u8: Any, positive_zero_u8: Any,
    *, key: CellKey, replay: ReplayLedger, arm_identity: ArmIdentityReceipt,
) -> InfluenceReceipt:
    _validate_cell_key(key)
    validate_replay_ledger(replay)
    validate_arm_identity(arm_identity)
    if replay.seed != key.seed or replay.target != key.target:
        raise SpecError("Influence key does not match replay ledger")
    replay_identity = (replay.state_sha256, replay.noise_sha256, replay.rng_state_sha256, replay.snapshot_sha256, replay.target_roster_sha256)
    arm_state = (arm_identity.state_sha256, arm_identity.noise_sha256, arm_identity.rng_state_sha256, arm_identity.snapshot_sha256, arm_identity.target_roster_sha256)
    if replay_identity != arm_state:
        raise SpecError("arm state/noise/RNG/snapshot/target roster does not match exact replay")
    arrays = tuple(
        np.array(_u8_rgb(value, name, native=True), dtype=np.uint8, order="C", copy=True)
        for value, name in (
            (target_edit_u8, "target_edit_u8"), (target_zero_u8, "target_zero_u8"),
            (negative_edit_u8, "negative_edit_u8"), (negative_zero_u8, "negative_zero_u8"),
            (positive_edit_u8, "positive_edit_u8"), (positive_zero_u8, "positive_zero_u8"),
        )
    )
    for array in arrays:
        array.setflags(write=False)
    target_effect = direct_effect_map(arrays[0], arrays[1])
    negative_effect = direct_effect_map(arrays[2], arrays[3])
    positive_effect = direct_effect_map(arrays[4], arrays[5])
    target_mean = float(np.mean(target_effect))
    negative_mean = float(np.mean(negative_effect))
    positive_mean = float(np.mean(positive_effect))
    target_d = target_mean - max(replay.tau_output, negative_mean)
    positive_d = positive_mean - max(replay.tau_output, negative_mean)
    output_domains = (
        "S48_TARGET_EDIT_OUTPUT_V3", "S48_TARGET_ZERO_OUTPUT_V3", "S48_NEGATIVE_EDIT_OUTPUT_V3",
        "S48_NEGATIVE_ZERO_OUTPUT_V3", "S48_POSITIVE_EDIT_OUTPUT_V3", "S48_POSITIVE_ZERO_OUTPUT_V3",
    )
    output_hashes = tuple(_canonical_array_sha(domain, array) for domain, array in zip(output_domains, arrays))
    provisional = InfluenceReceipt(
        key, arm_identity, replay, arm_identity.canonical_sha256, replay.canonical_sha256, arrays, *output_hashes,
        _canonical_array_sha("S48_TARGET_EFFECT_MAP_V3", target_effect),
        _canonical_array_sha("S48_NEGATIVE_EFFECT_MAP_V3", negative_effect),
        _canonical_array_sha("S48_POSITIVE_EFFECT_MAP_V3", positive_effect),
        target_mean, negative_mean, positive_mean, replay.tau_output, target_d, positive_d,
        target_d >= DELTA_I, positive_d >= DELTA_I, "0" * 64,
    )
    digest = _canonical_lines_sha("S48_INFLUENCE_RECEIPT_V3", _influence_hash_lines(provisional))
    return InfluenceReceipt(**{**provisional.__dict__, "canonical_sha256": digest})


def validate_influence_receipt(receipt: InfluenceReceipt) -> None:
    if not isinstance(receipt, InfluenceReceipt):
        raise SpecError("Influence evidence must be a typed InfluenceReceipt")
    _validate_cell_key(receipt.key)
    validate_arm_identity(receipt.arm_identity)
    validate_replay_ledger(receipt.replay)
    if receipt.arm_identity_sha256 != receipt.arm_identity.canonical_sha256 or receipt.replay_ledger_sha256 != receipt.replay.canonical_sha256:
        raise SpecError("Influence receipt does not bind its typed arm/replay evidence")
    if receipt.replay.seed != receipt.key.seed or receipt.replay.target != receipt.key.target:
        raise SpecError("Influence replay identity does not match the cell key")
    replay_state = tuple(getattr(receipt.replay, name) for name in ("state_sha256", "noise_sha256", "rng_state_sha256", "snapshot_sha256", "target_roster_sha256"))
    arm_state = tuple(getattr(receipt.arm_identity, name) for name in ("state_sha256", "noise_sha256", "rng_state_sha256", "snapshot_sha256", "target_roster_sha256"))
    if replay_state != arm_state:
        raise SpecError("Influence arm state does not match its replay ledger")
    for name in (
        "arm_identity_sha256", "replay_ledger_sha256", "target_edit_sha256", "target_zero_sha256", "negative_edit_sha256",
        "negative_zero_sha256", "positive_edit_sha256", "positive_zero_sha256", "target_effect_sha256",
        "negative_effect_sha256", "positive_effect_sha256",
    ):
        _sha(getattr(receipt, name), name)
    if not isinstance(receipt.outputs_u8, tuple) or len(receipt.outputs_u8) != 6:
        raise SpecError("Influence receipt must bind exactly six output arrays")
    arrays = tuple(_u8_rgb(value, f"Influence.outputs_u8[{index}]", native=True) for index, value in enumerate(receipt.outputs_u8))
    if any(array.flags.writeable for array in arrays):
        raise SpecError("Influence output evidence must be frozen read-only")
    output_domains = (
        "S48_TARGET_EDIT_OUTPUT_V3", "S48_TARGET_ZERO_OUTPUT_V3", "S48_NEGATIVE_EDIT_OUTPUT_V3",
        "S48_NEGATIVE_ZERO_OUTPUT_V3", "S48_POSITIVE_EDIT_OUTPUT_V3", "S48_POSITIVE_ZERO_OUTPUT_V3",
    )
    expected_output_hashes = tuple(_canonical_array_sha(domain, array) for domain, array in zip(output_domains, arrays))
    recorded_output_hashes = tuple(
        getattr(receipt, name) for name in (
            "target_edit_sha256", "target_zero_sha256", "negative_edit_sha256",
            "negative_zero_sha256", "positive_edit_sha256", "positive_zero_sha256",
        )
    )
    if recorded_output_hashes != expected_output_hashes:
        raise SpecError("Influence output hashes are not derived from bound outputs")
    target_effect = direct_effect_map(arrays[0], arrays[1])
    negative_effect = direct_effect_map(arrays[2], arrays[3])
    positive_effect = direct_effect_map(arrays[4], arrays[5])
    expected_effect_hashes = (
        _canonical_array_sha("S48_TARGET_EFFECT_MAP_V3", target_effect),
        _canonical_array_sha("S48_NEGATIVE_EFFECT_MAP_V3", negative_effect),
        _canonical_array_sha("S48_POSITIVE_EFFECT_MAP_V3", positive_effect),
    )
    if (receipt.target_effect_sha256, receipt.negative_effect_sha256, receipt.positive_effect_sha256) != expected_effect_hashes:
        raise SpecError("Influence effect hashes are not derived from bound outputs")
    derived_means = tuple(float(np.mean(effect)) for effect in (target_effect, negative_effect, positive_effect))
    target_mean = _finite(receipt.target_effect_mean, "target_effect_mean")
    negative_mean = _finite(receipt.negative_effect_mean, "negative_effect_mean")
    positive_mean = _finite(receipt.positive_effect_mean, "positive_effect_mean")
    if any(not math.isclose(recorded, derived, rel_tol=0.0, abs_tol=1e-15) for recorded, derived in zip((target_mean, negative_mean, positive_mean), derived_means)):
        raise SpecError("Influence means are not derived from bound outputs")
    tau = _finite(receipt.tau_output, "tau_output")
    if not math.isclose(tau, receipt.replay.tau_output, rel_tol=0.0, abs_tol=1e-15):
        raise SpecError("Influence tau is not derived from its replay ledger")
    for value in (target_mean, negative_mean, positive_mean, tau):
        if not 0.0 <= value <= 1.0:
            raise SpecError("Influence components must lie in [0,1]")
    target_d = target_mean - max(tau, negative_mean)
    positive_d = positive_mean - max(tau, negative_mean)
    if not math.isclose(receipt.target_d, target_d, rel_tol=0.0, abs_tol=1e-15) or not math.isclose(receipt.positive_d, positive_d, rel_tol=0.0, abs_tol=1e-15):
        raise SpecError("Influence D values are inconsistent")
    if type(receipt.target_observable) is not bool or receipt.target_observable != (target_d >= DELTA_I):
        raise SpecError("target observable decision is inconsistent")
    if type(receipt.positive_control_passed) is not bool or receipt.positive_control_passed != (positive_d >= DELTA_I):
        raise SpecError("positive-control decision is inconsistent")
    if receipt.canonical_sha256 != _canonical_lines_sha("S48_INFLUENCE_RECEIPT_V3", _influence_hash_lines(receipt)):
        raise SpecError("Influence receipt canonical hash mismatch")


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
class ObservationIdentity:
    capture_id: str
    file_sha256: str


@dataclass(frozen=True)
class ObservationExclusionLedger:
    target: ObservationIdentity
    memory_observations: tuple[ObservationIdentity, ...]
    conditioning_observations: tuple[ObservationIdentity, ...]
    canonical_sha256: str


def _validate_observation_identity(value: ObservationIdentity, name: str) -> None:
    if not isinstance(value, ObservationIdentity) or type(value.capture_id) is not str or not value.capture_id or "\n" in value.capture_id:
        raise SpecError(f"{name} must have a non-empty single-line capture_id")
    _sha(value.file_sha256, f"{name}.file_sha256")


def _observation_ledger_lines(
    target: ObservationIdentity,
    memory: Sequence[ObservationIdentity],
    conditioning: Sequence[ObservationIdentity],
) -> tuple[str, ...]:
    return (
        f"TARGET\t{target.capture_id}\t{target.file_sha256}",
        *(f"MEMORY\t{item.capture_id}\t{item.file_sha256}" for item in memory),
        *(f"CONDITIONING\t{item.capture_id}\t{item.file_sha256}" for item in conditioning),
    )


def build_observation_exclusion_ledger(
    target: ObservationIdentity,
    memory_observations: Sequence[ObservationIdentity],
    conditioning_observations: Sequence[ObservationIdentity],
) -> ObservationExclusionLedger:
    _validate_observation_identity(target, "target")
    if not isinstance(memory_observations, (tuple, list)) or not isinstance(conditioning_observations, (tuple, list)):
        raise SpecError("observation rosters must be explicit tuples or lists")
    memory = tuple(memory_observations)
    conditioning = tuple(conditioning_observations)
    for label, roster in (("memory", memory), ("conditioning", conditioning)):
        seen_capture: set[str] = set()
        seen_file: set[str] = set()
        for index, item in enumerate(roster):
            _validate_observation_identity(item, f"{label}[{index}]")
            if item.capture_id in seen_capture or item.file_sha256 in seen_file:
                raise SpecError(f"{label} roster contains duplicate capture or file identity")
            seen_capture.add(item.capture_id)
            seen_file.add(item.file_sha256)
    all_model_inputs = (*memory, *conditioning)
    if any(item.capture_id == target.capture_id or item.file_sha256 == target.file_sha256 for item in all_model_inputs):
        raise SpecError("target answer capture/file cannot appear in memory or conditioning")
    lines = _observation_ledger_lines(target, memory, conditioning)
    return ObservationExclusionLedger(target, memory, conditioning, _canonical_lines_sha("S48_OBSERVATION_EXCLUSION_LEDGER_V3", lines))


def validate_observation_exclusion_ledger(ledger: ObservationExclusionLedger) -> None:
    if not isinstance(ledger, ObservationExclusionLedger):
        raise SpecError("reference exclusion evidence must be a typed ledger")
    _validate_observation_identity(ledger.target, "target")
    for label, roster in (("memory", ledger.memory_observations), ("conditioning", ledger.conditioning_observations)):
        if not isinstance(roster, tuple):
            raise SpecError(f"{label} roster must be an immutable tuple")
        seen_capture: set[str] = set()
        seen_file: set[str] = set()
        for index, item in enumerate(roster):
            _validate_observation_identity(item, f"{label}[{index}]")
            if item.capture_id in seen_capture or item.file_sha256 in seen_file:
                raise SpecError(f"{label} roster contains duplicate capture or file identity")
            seen_capture.add(item.capture_id)
            seen_file.add(item.file_sha256)
    if any(
        item.capture_id == ledger.target.capture_id or item.file_sha256 == ledger.target.file_sha256
        for item in (*ledger.memory_observations, *ledger.conditioning_observations)
    ):
        raise SpecError("target answer capture/file appears in memory or conditioning")
    expected = _canonical_lines_sha(
        "S48_OBSERVATION_EXCLUSION_LEDGER_V3",
        _observation_ledger_lines(ledger.target, ledger.memory_observations, ledger.conditioning_observations),
    )
    if ledger.canonical_sha256 != expected:
        raise SpecError("observation exclusion ledger canonical hash mismatch")


@dataclass(frozen=True)
class ReferenceCandidate:
    candidate_id: str
    capture_id: str
    file_sha256: str
    scene_id: str
    sensor_timestamp_ns: int
    camera: Camera
    calibration: SyncCalibration
    identity_receipt: "IdentityAgreement"
    view_pair_receipts: tuple["ViewPairReceipt", ...]
    domain_receipts: Mapping[str, "ValidDomainReceipt"]


@dataclass(frozen=True)
class ReferenceFlowRecord:
    candidate_id: str
    capture_id: str
    file_sha256: str
    dt_ns: int
    metrics: CameraMatchMetrics
    eligible: bool
    reasons: tuple[str, ...]
    sort_key: tuple[Any, ...]


@dataclass(frozen=True)
class ReferenceRosterReceipt:
    candidates: tuple[ReferenceCandidate, ...]
    target_timestamp_ns: int
    target_calibration: SyncCalibration
    target_scene_id: str
    target_camera: Camera
    ordinary_camera: Camera
    exclusion_ledger: ObservationExclusionLedger
    exclusion_ledger_sha256: str
    flow: tuple[ReferenceFlowRecord, ...]
    eligible_candidate_ids: tuple[str, ...]
    eligible_capture_ids: tuple[str, ...]
    eligible_file_sha256s: tuple[str, ...]
    canonical_sha256: str


def select_reference_roster(
    candidates: Sequence[ReferenceCandidate], *, target_timestamp_ns: int,
    target_calibration: SyncCalibration, target_scene_id: str,
    target_camera: Camera, ordinary_camera: Camera,
    exclusion_ledger: ObservationExclusionLedger,
) -> ReferenceRosterReceipt:
    target_time = _strict_int(target_timestamp_ns, "target_timestamp_ns")
    if type(target_scene_id) is not str or not target_scene_id:
        raise SpecError("target_scene_id must be a non-empty string")
    validate_observation_exclusion_ledger(exclusion_ledger)
    memory_capture = {item.capture_id for item in exclusion_ledger.memory_observations}
    memory_file = {item.file_sha256 for item in exclusion_ledger.memory_observations}
    conditioning_capture = {item.capture_id for item in exclusion_ledger.conditioning_observations}
    conditioning_file = {item.file_sha256 for item in exclusion_ledger.conditioning_observations}
    flow: list[ReferenceFlowRecord] = []
    seen_ids: set[str] = set()
    seen_captures: set[str] = set()
    seen_files: set[str] = set()
    for candidate in candidates:
        if not isinstance(candidate, ReferenceCandidate):
            raise SpecError("reference roster entries must be typed ReferenceCandidate objects")
        if type(candidate.candidate_id) is not str or not candidate.candidate_id or "\n" in candidate.candidate_id:
            raise SpecError("candidate_id must be non-empty and single-line")
        if type(candidate.capture_id) is not str or not candidate.capture_id or "\n" in candidate.capture_id:
            raise SpecError("capture_id must be non-empty and single-line")
        digest = _sha(candidate.file_sha256, "file_sha256")
        if candidate.candidate_id in seen_ids or candidate.capture_id in seen_captures or digest in seen_files:
            raise SpecError("reference roster contains duplicate candidate, capture, or file identity")
        seen_ids.add(candidate.candidate_id)
        seen_captures.add(candidate.capture_id)
        seen_files.add(digest)
        candidate_time = calibrated_timestamp_ns(candidate.sensor_timestamp_ns, candidate.calibration)
        target_time_calibrated = calibrated_timestamp_ns(target_time, target_calibration)
        dt = abs(candidate_time - target_time_calibrated)
        metrics = camera_match_metrics(target_camera, ordinary_camera, candidate.camera)
        reasons: list[str] = []
        if candidate.capture_id == exclusion_ledger.target.capture_id or digest == exclusion_ledger.target.file_sha256:
            reasons.append("TARGET_CAPTURE_OR_FILE_REUSE")
        if candidate.capture_id in memory_capture or digest in memory_file:
            reasons.append("REFERENCE_ENTERED_MEMORY")
        if candidate.capture_id in conditioning_capture or digest in conditioning_file:
            reasons.append("REFERENCE_ENTERED_CONDITIONING")
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
        try:
            identity_ok = isinstance(candidate.identity_receipt, IdentityAgreement) and identity_decision(candidate.identity_receipt)[0]
        except SpecError:
            identity_ok = False
        if not identity_ok:
            reasons.append("IDENTITY_CONTRACT_FAILED")
        if not isinstance(candidate.view_pair_receipts, tuple) or validate_view_pair_receipts(candidate.view_pair_receipts, include_replacement=False)[0] is False:
            reasons.append("VIEW_PAIR_CONTRACT_FAILED")
        if set(candidate.domain_receipts) != {"support", "outside"}:
            reasons.append("DOMAIN_CONTRACT_FAILED")
        else:
            try:
                domain_ok = all(
                    isinstance(receipt, ValidDomainReceipt)
                    and receipt.domain == domain_name
                    and valid_domain_decision(receipt, required_roles=("O", "R"))[0]
                    for domain_name, receipt in candidate.domain_receipts.items()
                )
            except SpecError:
                domain_ok = False
            if not domain_ok:
                reasons.append("DOMAIN_CONTRACT_FAILED")
            elif not np.array_equal(candidate.identity_receipt.support > 0.0, candidate.domain_receipts["support"].domain_mask):
                reasons.append("IDENTITY_SUPPORT_DOMAIN_MISMATCH")
            elif not np.array_equal(candidate.domain_receipts["outside"].domain_mask, ~candidate.domain_receipts["support"].domain_mask):
                reasons.append("SUPPORT_OUTSIDE_DOMAIN_NOT_COMPLEMENTARY")
        key = (dt, metrics.angle_microdegrees, metrics.position_ratio_ppm, metrics.fov_microdegrees, digest, candidate.candidate_id.encode("utf-8"))
        flow.append(ReferenceFlowRecord(candidate.candidate_id, candidate.capture_id, digest, dt, metrics, not reasons, tuple(reasons), key))
    eligible = tuple(sorted((record for record in flow if record.eligible), key=lambda record: record.sort_key))
    if len(eligible) < 3:
        raise SpecError("reference roster requires at least three eligible held-out observations")
    lines = [exclusion_ledger.canonical_sha256]
    lines.extend(
        f"{record.candidate_id}\t{record.capture_id}\t{record.file_sha256}\t{record.dt_ns}\t{record.metrics.angle_microdegrees}\t{record.metrics.position_ratio_ppm}\t{record.metrics.fov_microdegrees}\t{int(record.eligible)}\t{','.join(record.reasons)}"
        for record in flow
    )
    return ReferenceRosterReceipt(
        tuple(candidates), target_time, target_calibration, target_scene_id, target_camera, ordinary_camera,
        exclusion_ledger, exclusion_ledger.canonical_sha256, tuple(flow), tuple(record.candidate_id for record in eligible),
        tuple(record.capture_id for record in eligible), tuple(record.file_sha256 for record in eligible),
        _canonical_lines_sha("S48_REFERENCE_ROSTER_V3", lines),
    )


def select_reference(*args: Any, **kwargs: Any) -> None:
    raise SpecError("V7 forbids a single unbound reference; use select_reference_roster with at least three held-out observations")


@dataclass(frozen=True)
class IdentityAgreement:
    roles: tuple[str, ...]
    support: np.ndarray
    identities: tuple[tuple[str, np.ndarray], ...]
    validities: tuple[tuple[str, np.ndarray], ...]
    support_sha256: str
    identity_sha256s: tuple[tuple[str, str], ...]
    validity_sha256s: tuple[tuple[str, str], ...]
    support_weight: float
    valid_weight: float
    valid_weight_coverage: float
    agreement_weight: float
    agreement: float
    nonbackground_sets_equal: bool
    canonical_sha256: str


def _identity_hash_lines(receipt: IdentityAgreement) -> tuple[str, ...]:
    return (
        ",".join(receipt.roles), receipt.support_sha256,
        *(f"ID:{role}:{digest}" for role, digest in receipt.identity_sha256s),
        *(f"VALID:{role}:{digest}" for role, digest in receipt.validity_sha256s),
        receipt.support_weight.hex(), receipt.valid_weight.hex(), receipt.valid_weight_coverage.hex(),
        receipt.agreement_weight.hex(), receipt.agreement.hex(), str(int(receipt.nonbackground_sets_equal)),
    )


def identity_agreement(
    identities: Mapping[str, Any], validities: Mapping[str, Any], support: Any,
    *, roles: tuple[str, ...],
) -> IdentityAgreement:
    if roles not in (("O", "R"), ("O", "R", "P")) or set(identities) != set(roles) or set(validities) != set(roles):
        raise SpecError("identity roles must be exactly O/R or O/R/P")
    w = _readonly_f64_weight(np.asarray(support, dtype=np.float64), "support")
    if float(np.sum(w)) <= 0.0:
        raise SpecError("identity support is empty")
    ids: dict[str, np.ndarray] = {}
    valids: dict[str, np.ndarray] = {}
    for role in roles:
        identity = np.array(_identity(identities[role], f"identity_{role}", w.shape), order="C", copy=True)
        identity.setflags(write=False)
        valid = np.array(_bool_mask(validities[role], f"valid_{role}", w.shape), dtype=bool, order="C", copy=True)
        valid.setflags(write=False)
        ids[role] = identity
        valids[role] = valid
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
    provisional = IdentityAgreement(
        roles, w, tuple((role, ids[role]) for role in roles), tuple((role, valids[role]) for role in roles),
        _canonical_array_sha("S48_IDENTITY_SUPPORT_V3", w),
        tuple((role, _canonical_array_sha(f"S48_IDENTITY_{role}_V3", ids[role])) for role in roles),
        tuple((role, _canonical_array_sha(f"S48_IDENTITY_VALID_{role}_V3", valids[role])) for role in roles),
        support_weight, valid_weight, valid_weight / support_weight,
        agreement_weight, agreement_weight / valid_weight, sets_equal, "0" * 64,
    )
    return IdentityAgreement(**{**provisional.__dict__, "canonical_sha256": _canonical_lines_sha("S48_IDENTITY_AGREEMENT_V3", _identity_hash_lines(provisional))})


def identity_decision(receipt: IdentityAgreement) -> tuple[bool, tuple[str, ...]]:
    if not isinstance(receipt, IdentityAgreement):
        raise SpecError("identity receipt must be typed")
    if receipt.roles not in (("O", "R"), ("O", "R", "P")):
        raise SpecError("identity receipt roles are invalid")
    support = _strict_f64_weight(receipt.support, "identity support")
    if support.flags.writeable or receipt.support_sha256 != _canonical_array_sha("S48_IDENTITY_SUPPORT_V3", support):
        raise SpecError("identity support is mutable or hash-mismatched")
    if tuple(role for role, _ in receipt.identities) != receipt.roles or tuple(role for role, _ in receipt.validities) != receipt.roles:
        raise SpecError("identity/validity arrays do not cover the exact roles")
    ids: dict[str, np.ndarray] = {}
    valids: dict[str, np.ndarray] = {}
    for role, raw in receipt.identities:
        array = _identity(raw, f"identity {role}", support.shape)
        if array.flags.writeable:
            raise SpecError("identity arrays must be frozen read-only")
        ids[role] = array
    for role, raw in receipt.validities:
        array = _bool_mask(raw, f"identity validity {role}", support.shape)
        if array.flags.writeable:
            raise SpecError("identity validity arrays must be frozen read-only")
        valids[role] = array
    expected_identity_hashes = tuple((role, _canonical_array_sha(f"S48_IDENTITY_{role}_V3", ids[role])) for role in receipt.roles)
    expected_validity_hashes = tuple((role, _canonical_array_sha(f"S48_IDENTITY_VALID_{role}_V3", valids[role])) for role in receipt.roles)
    if receipt.identity_sha256s != expected_identity_hashes or receipt.validity_sha256s != expected_validity_hashes:
        raise SpecError("identity evidence hashes are not derived from bound arrays")
    common = np.logical_and.reduce([valids[role] for role in receipt.roles]) & (support > 0.0)
    actual_support_weight = float(np.sum(support))
    actual_valid_weight = float(np.sum(support[common]))
    equal = np.ones(support.shape, dtype=bool)
    for role in receipt.roles[1:]:
        equal &= ids[role] == ids[receipt.roles[0]]
    actual_agreement_weight = float(np.sum(support[common & equal]))
    sets = [set(int(value) for value in np.unique(ids[role][common]) if int(value) != 0) for role in receipt.roles]
    actual_sets_equal = all(item == sets[0] for item in sets[1:])
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
        or not math.isclose(support_weight, actual_support_weight, rel_tol=0.0, abs_tol=1e-15)
        or not math.isclose(valid_weight, actual_valid_weight, rel_tol=0.0, abs_tol=1e-15)
        or not math.isclose(agreement_weight, actual_agreement_weight, rel_tol=0.0, abs_tol=1e-15)
        or receipt.nonbackground_sets_equal != actual_sets_equal
    ):
        raise SpecError("identity receipt fields are inconsistent")
    if receipt.canonical_sha256 != _canonical_lines_sha("S48_IDENTITY_AGREEMENT_V3", _identity_hash_lines(receipt)):
        raise SpecError("identity receipt canonical hash mismatch")
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
    roles: tuple[str, ...]
    domain_mask: np.ndarray
    validity_masks: tuple[tuple[str, np.ndarray], ...]
    domain_sha256: str
    validity_sha256s: tuple[tuple[str, str], ...]
    domain_denominator: int
    common_valid_numerator: int
    hole_numerator: int
    hole_denominator: int
    coverage: float
    hole_ratio: float
    canonical_sha256: str


_VALID_DOMAIN_ROLE_SETS = (("O", "R"), ("O", "R", "P"), ("O", "R", "A"))


def _valid_domain_hash_lines(receipt: ValidDomainReceipt) -> tuple[str, ...]:
    return (
        receipt.domain, ",".join(receipt.roles), receipt.domain_sha256,
        *(f"{role}={digest}" for role, digest in receipt.validity_sha256s),
        str(receipt.domain_denominator), str(receipt.common_valid_numerator), str(receipt.hole_numerator),
        str(receipt.hole_denominator), receipt.coverage.hex(), receipt.hole_ratio.hex(),
    )


def valid_domain_receipt(
    domain_name: str, domain: Any, validities: Mapping[str, Any], *, roles: tuple[str, ...],
) -> ValidDomainReceipt:
    if domain_name not in ("support", "outside"):
        raise SpecError("domain_name must be support or outside")
    if roles not in _VALID_DOMAIN_ROLE_SETS or set(validities) != set(roles):
        raise SpecError("valid-domain roles must be exactly O/R, O/R/P, or O/R/A")
    domain_mask = np.array(_bool_mask(domain, "domain"), dtype=bool, order="C", copy=True)
    domain_mask.setflags(write=False)
    masks = [np.array(_bool_mask(validities[role], f"valid_{role}", domain_mask.shape), dtype=bool, order="C", copy=True) for role in roles]
    for mask in masks:
        mask.setflags(write=False)
    common = np.logical_and.reduce(masks)
    denominator = int(np.count_nonzero(domain_mask))
    if denominator == 0:
        raise SpecError("declared valid domain is empty")
    common_count = int(np.count_nonzero(domain_mask & common))
    holes = denominator - common_count
    domain_hash = _canonical_array_sha(f"S48_{domain_name.upper()}_DOMAIN_BOOL_V3", domain_mask)
    validity_hashes = tuple((role, _canonical_array_sha(f"S48_VALIDITY_{role}_BOOL_V3", masks[index])) for index, role in enumerate(roles))
    provisional = ValidDomainReceipt(
        domain_name, roles, domain_mask, tuple(zip(roles, masks)), domain_hash, validity_hashes, denominator, common_count, holes,
        denominator, common_count / denominator, holes / denominator, "0" * 64,
    )
    digest = _canonical_lines_sha("S48_VALID_DOMAIN_RECEIPT_V3", _valid_domain_hash_lines(provisional))
    return ValidDomainReceipt(**{**provisional.__dict__, "canonical_sha256": digest})


def valid_domain_decision(receipt: ValidDomainReceipt, *, required_roles: tuple[str, ...]) -> tuple[bool, tuple[str, ...]]:
    if not isinstance(receipt, ValidDomainReceipt):
        raise SpecError("valid-domain receipt must be typed")
    if receipt.domain not in ("support", "outside"):
        raise SpecError("valid-domain receipt has unknown domain")
    if required_roles not in _VALID_DOMAIN_ROLE_SETS or receipt.roles != required_roles:
        raise SpecError("valid-domain receipt does not cover the exact required roles")
    domain_mask = _bool_mask(receipt.domain_mask, "bound domain mask")
    if domain_mask.flags.writeable:
        raise SpecError("bound domain mask must be frozen read-only")
    if not isinstance(receipt.validity_masks, tuple) or tuple(role for role, _ in receipt.validity_masks) != required_roles:
        raise SpecError("bound validity masks do not cover required roles in order")
    masks: list[np.ndarray] = []
    for role, mask_raw in receipt.validity_masks:
        mask = _bool_mask(mask_raw, f"bound validity {role}", domain_mask.shape)
        if mask.flags.writeable:
            raise SpecError("bound validity masks must be frozen read-only")
        masks.append(mask)
    expected_domain_sha = _canonical_array_sha(f"S48_{receipt.domain.upper()}_DOMAIN_BOOL_V3", domain_mask)
    expected_validity_sha = tuple((role, _canonical_array_sha(f"S48_VALIDITY_{role}_BOOL_V3", masks[index])) for index, role in enumerate(required_roles))
    if receipt.domain_sha256 != expected_domain_sha or receipt.validity_sha256s != expected_validity_sha:
        raise SpecError("valid-domain mask hashes are not derived from bound masks")
    _sha(receipt.domain_sha256, "domain_sha256")
    if not isinstance(receipt.validity_sha256s, tuple) or tuple(role for role, _ in receipt.validity_sha256s) != required_roles:
        raise SpecError("valid-domain validity identities do not cover required roles in order")
    for role, digest in receipt.validity_sha256s:
        if type(role) is not str:
            raise SpecError("valid-domain role label must be a string")
        _sha(digest, f"validity_sha256[{role}]")
    denominator = _strict_int(receipt.domain_denominator, "domain_denominator", minimum=1)
    common = _strict_int(receipt.common_valid_numerator, "common_valid_numerator", minimum=0)
    holes = _strict_int(receipt.hole_numerator, "hole_numerator", minimum=0)
    hole_denominator = _strict_int(receipt.hole_denominator, "hole_denominator", minimum=1)
    coverage = _finite(receipt.coverage, "coverage")
    hole_ratio = _finite(receipt.hole_ratio, "hole_ratio")
    actual_denominator = int(np.count_nonzero(domain_mask))
    actual_common = int(np.count_nonzero(domain_mask & np.logical_and.reduce(masks)))
    actual_holes = actual_denominator - actual_common
    if (
        common + holes != denominator
        or hole_denominator != denominator
        or not math.isclose(coverage, common / denominator, rel_tol=0.0, abs_tol=1e-15)
        or not math.isclose(hole_ratio, holes / denominator, rel_tol=0.0, abs_tol=1e-15)
        or not 0.0 <= coverage <= 1.0
        or not 0.0 <= hole_ratio <= 1.0
        or (denominator, common, holes) != (actual_denominator, actual_common, actual_holes)
    ):
        raise SpecError("valid-domain receipt fields are inconsistent")
    if receipt.canonical_sha256 != _canonical_lines_sha("S48_VALID_DOMAIN_RECEIPT_V3", _valid_domain_hash_lines(receipt)):
        raise SpecError("valid-domain receipt canonical hash mismatch")
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


def local_edit_preference(edit_u8: Any, zero_u8: Any, reference_u8: Any, valid: Any, support: Any) -> float:
    return normalized_rgb_mse(edit_u8, reference_u8, valid, support) - normalized_rgb_mse(zero_u8, reference_u8, valid, support)


def matched_replacement_utility(replacement_u8: Any, ordinary_reinsert_u8: Any, reference_u8: Any, valid: Any, support: Any) -> float:
    return normalized_rgb_mse(replacement_u8, reference_u8, valid, support) - normalized_rgb_mse(ordinary_reinsert_u8, reference_u8, valid, support)


def source_absence_utility(absent_u8: Any, ordinary_reinsert_u8: Any, reference_u8: Any, valid: Any, support: Any) -> float:
    """Positive favors O; negative means absence is better for this reference/protocol."""
    return normalized_rgb_mse(absent_u8, reference_u8, valid, support) - normalized_rgb_mse(ordinary_reinsert_u8, reference_u8, valid, support)


@dataclass(frozen=True)
class ReferenceUncertaintyReceipt:
    reference_roster: ReferenceRosterReceipt
    support: np.ndarray
    reference_images_u8: tuple[tuple[str, np.ndarray], ...]
    validity_masks: tuple[tuple[str, np.ndarray], ...]
    reference_roster_sha256: str
    support_sha256: str
    reference_capture_ids: tuple[str, ...]
    decoded_rgb_sha256s: tuple[tuple[str, str], ...]
    validity_sha256s: tuple[tuple[str, str], ...]
    pairwise_losses: tuple[tuple[str, str, float], ...]
    delta_ref: float
    delta_u: float
    eligible_for_primary_rcsu: bool
    canonical_sha256: str


def validate_reference_roster_receipt(roster: ReferenceRosterReceipt) -> None:
    if not isinstance(roster, ReferenceRosterReceipt):
        raise SpecError("reference roster receipt must be typed")
    if not isinstance(roster.candidates, tuple) or len(roster.candidates) < 3:
        raise SpecError("reference roster must bind the complete candidate tuple")
    validate_observation_exclusion_ledger(roster.exclusion_ledger)
    _sha(roster.exclusion_ledger_sha256, "exclusion_ledger_sha256")
    if roster.exclusion_ledger_sha256 != roster.exclusion_ledger.canonical_sha256:
        raise SpecError("reference roster does not bind its exclusion ledger")
    if not isinstance(roster.flow, tuple) or not isinstance(roster.eligible_candidate_ids, tuple) or not isinstance(roster.eligible_capture_ids, tuple) or not isinstance(roster.eligible_file_sha256s, tuple):
        raise SpecError("reference roster containers must be tuples")
    eligible = tuple(sorted((record for record in roster.flow if record.eligible), key=lambda record: record.sort_key))
    if len(eligible) < 3:
        raise SpecError("reference roster has fewer than three eligible observations")
    if roster.eligible_candidate_ids != tuple(record.candidate_id for record in eligible) or roster.eligible_capture_ids != tuple(record.capture_id for record in eligible) or roster.eligible_file_sha256s != tuple(record.file_sha256 for record in eligible):
        raise SpecError("reference roster eligible identities are inconsistent")
    if len(set(roster.eligible_capture_ids)) != len(roster.eligible_capture_ids) or len(set(roster.eligible_file_sha256s)) != len(roster.eligible_file_sha256s):
        raise SpecError("reference roster repeats a capture or file")
    target = roster.exclusion_ledger.target
    forbidden_captures = {target.capture_id, *(item.capture_id for item in roster.exclusion_ledger.memory_observations), *(item.capture_id for item in roster.exclusion_ledger.conditioning_observations)}
    forbidden_files = {target.file_sha256, *(item.file_sha256 for item in roster.exclusion_ledger.memory_observations), *(item.file_sha256 for item in roster.exclusion_ledger.conditioning_observations)}
    lines = [roster.exclusion_ledger_sha256]
    seen_candidates: set[str] = set()
    seen_captures: set[str] = set()
    seen_files: set[str] = set()
    for record in roster.flow:
        if not isinstance(record, ReferenceFlowRecord):
            raise SpecError("reference flow record is untyped")
        if type(record.candidate_id) is not str or not record.candidate_id or "\n" in record.candidate_id or type(record.capture_id) is not str or not record.capture_id or "\n" in record.capture_id:
            raise SpecError("reference flow identities are invalid")
        _sha(record.file_sha256, "reference flow file_sha256")
        if record.candidate_id in seen_candidates or record.capture_id in seen_captures or record.file_sha256 in seen_files:
            raise SpecError("reference flow repeats a candidate, capture, or file")
        seen_candidates.add(record.candidate_id)
        seen_captures.add(record.capture_id)
        seen_files.add(record.file_sha256)
        _strict_int(record.dt_ns, "reference flow dt_ns", minimum=0)
        if not isinstance(record.metrics, CameraMatchMetrics) or record.sort_key != (
            record.dt_ns, record.metrics.angle_microdegrees, record.metrics.position_ratio_ppm,
            record.metrics.fov_microdegrees, record.file_sha256, record.candidate_id.encode("utf-8"),
        ):
            raise SpecError("reference flow sort key is inconsistent")
        if type(record.eligible) is not bool or not isinstance(record.reasons, tuple) or record.eligible != (len(record.reasons) == 0):
            raise SpecError("reference flow decision is inconsistent")
        if record.eligible and (record.capture_id in forbidden_captures or record.file_sha256 in forbidden_files):
            raise SpecError("eligible reference reuses target, memory, or conditioning evidence")
        lines.append(
            f"{record.candidate_id}\t{record.capture_id}\t{record.file_sha256}\t{record.dt_ns}\t{record.metrics.angle_microdegrees}\t{record.metrics.position_ratio_ppm}\t{record.metrics.fov_microdegrees}\t{int(record.eligible)}\t{','.join(record.reasons)}"
        )
    if roster.canonical_sha256 != _canonical_lines_sha("S48_REFERENCE_ROSTER_V3", lines):
        raise SpecError("reference roster canonical hash mismatch")
    rebuilt = select_reference_roster(
        roster.candidates,
        target_timestamp_ns=roster.target_timestamp_ns,
        target_calibration=roster.target_calibration,
        target_scene_id=roster.target_scene_id,
        target_camera=roster.target_camera,
        ordinary_camera=roster.ordinary_camera,
        exclusion_ledger=roster.exclusion_ledger,
    )
    if (
        rebuilt.exclusion_ledger_sha256 != roster.exclusion_ledger_sha256
        or rebuilt.flow != roster.flow
        or rebuilt.eligible_candidate_ids != roster.eligible_candidate_ids
        or rebuilt.eligible_capture_ids != roster.eligible_capture_ids
        or rebuilt.eligible_file_sha256s != roster.eligible_file_sha256s
        or rebuilt.canonical_sha256 != roster.canonical_sha256
    ):
        raise SpecError("reference roster flow is not derived from bound candidates")


def _reference_uncertainty_lines(receipt: ReferenceUncertaintyReceipt) -> tuple[str, ...]:
    return (
        receipt.reference_roster_sha256, receipt.support_sha256, ",".join(receipt.reference_capture_ids),
        *(f"RGB:{capture}:{digest}" for capture, digest in receipt.decoded_rgb_sha256s),
        *(f"VALID:{capture}:{digest}" for capture, digest in receipt.validity_sha256s),
        *(f"PAIR:{left}:{right}:{loss.hex()}" for left, right, loss in receipt.pairwise_losses),
        receipt.delta_ref.hex(), receipt.delta_u.hex(), str(int(receipt.eligible_for_primary_rcsu)),
    )


def build_reference_uncertainty(
    roster: ReferenceRosterReceipt,
    reference_images: Mapping[str, Any],
    validities: Mapping[str, Any],
    support: Any,
) -> ReferenceUncertaintyReceipt:
    validate_reference_roster_receipt(roster)
    captures = roster.eligible_capture_ids
    if set(reference_images) != set(captures) or set(validities) != set(captures):
        raise SpecError("reference image/validity mappings must cover the exact eligible capture roster")
    w = _readonly_f64_weight(support, "reference_support", (NATIVE_HEIGHT, NATIVE_WIDTH))
    if not 0.0 < float(np.mean(w)) < 1.0:
        raise SpecError("reference support must be nonempty and nonfull")
    images: dict[str, np.ndarray] = {}
    masks: dict[str, np.ndarray] = {}
    for capture in captures:
        image = np.array(_u8_rgb(reference_images[capture], f"reference_images[{capture}]", native=True), dtype=np.uint8, order="C", copy=True)
        image.setflags(write=False)
        mask = np.array(_bool_mask(validities[capture], f"validities[{capture}]", (NATIVE_HEIGHT, NATIVE_WIDTH)), dtype=bool, order="C", copy=True)
        mask.setflags(write=False)
        images[capture] = image
        masks[capture] = mask
    decoded_hashes = tuple((capture, _canonical_array_sha("S48_REFERENCE_DECODED_RGB_V3", images[capture])) for capture in captures)
    validity_hashes = tuple((capture, _canonical_array_sha("S48_REFERENCE_VALIDITY_BOOL_V3", masks[capture])) for capture in captures)
    losses: list[tuple[str, str, float]] = []
    for i, left in enumerate(captures):
        for right in captures[i + 1 :]:
            common = masks[left] & masks[right]
            losses.append((left, right, normalized_rgb_mse(images[left], images[right], common, w)))
    delta_ref = max(loss for _, _, loss in losses)
    delta_u = max(DELTA_B, 2.0 * delta_ref)
    provisional = ReferenceUncertaintyReceipt(
        roster, w, tuple((capture, images[capture]) for capture in captures), tuple((capture, masks[capture]) for capture in captures),
        roster.canonical_sha256, _canonical_array_sha("S48_RCSU_SUPPORT_V3", w), captures,
        decoded_hashes, validity_hashes, tuple(losses), delta_ref, delta_u,
        delta_ref <= DELTA_B, "0" * 64,
    )
    digest = _canonical_lines_sha("S48_REFERENCE_UNCERTAINTY_V3", _reference_uncertainty_lines(provisional))
    return ReferenceUncertaintyReceipt(**{**provisional.__dict__, "canonical_sha256": digest})


def validate_reference_uncertainty(receipt: ReferenceUncertaintyReceipt) -> None:
    if not isinstance(receipt, ReferenceUncertaintyReceipt):
        raise SpecError("reference uncertainty must be a typed receipt")
    validate_reference_roster_receipt(receipt.reference_roster)
    _sha(receipt.reference_roster_sha256, "reference_roster_sha256")
    if receipt.reference_roster_sha256 != receipt.reference_roster.canonical_sha256:
        raise SpecError("reference uncertainty does not bind its exact roster")
    _sha(receipt.support_sha256, "support_sha256")
    if not isinstance(receipt.reference_capture_ids, tuple) or len(receipt.reference_capture_ids) < 3 or len(set(receipt.reference_capture_ids)) != len(receipt.reference_capture_ids):
        raise SpecError("reference uncertainty requires at least three unique captures")
    if tuple(capture for capture, _ in receipt.decoded_rgb_sha256s) != receipt.reference_capture_ids or tuple(capture for capture, _ in receipt.validity_sha256s) != receipt.reference_capture_ids:
        raise SpecError("reference uncertainty identities are incomplete or reordered")
    if tuple(capture for capture, _ in receipt.reference_images_u8) != receipt.reference_capture_ids or tuple(capture for capture, _ in receipt.validity_masks) != receipt.reference_capture_ids:
        raise SpecError("reference uncertainty arrays are incomplete or reordered")
    support = _strict_f64_weight(receipt.support, "reference uncertainty support", (NATIVE_HEIGHT, NATIVE_WIDTH))
    if support.flags.writeable or receipt.support_sha256 != _canonical_array_sha("S48_RCSU_SUPPORT_V3", support):
        raise SpecError("reference uncertainty support is mutable or hash-mismatched")
    images: dict[str, np.ndarray] = {}
    masks: dict[str, np.ndarray] = {}
    for capture, image_raw in receipt.reference_images_u8:
        image = _u8_rgb(image_raw, f"reference image {capture}", native=True)
        if image.flags.writeable:
            raise SpecError("reference image evidence must be frozen read-only")
        images[capture] = image
    for capture, mask_raw in receipt.validity_masks:
        mask = _bool_mask(mask_raw, f"reference validity {capture}", (NATIVE_HEIGHT, NATIVE_WIDTH))
        if mask.flags.writeable:
            raise SpecError("reference validity evidence must be frozen read-only")
        masks[capture] = mask
    expected_rgb_hashes = tuple((capture, _canonical_array_sha("S48_REFERENCE_DECODED_RGB_V3", images[capture])) for capture in receipt.reference_capture_ids)
    expected_valid_hashes = tuple((capture, _canonical_array_sha("S48_REFERENCE_VALIDITY_BOOL_V3", masks[capture])) for capture in receipt.reference_capture_ids)
    if receipt.decoded_rgb_sha256s != expected_rgb_hashes or receipt.validity_sha256s != expected_valid_hashes:
        raise SpecError("reference evidence hashes are not derived from bound arrays")
    for _, digest in (*receipt.decoded_rgb_sha256s, *receipt.validity_sha256s):
        _sha(digest, "reference evidence sha256")
    expected_pairs = {(receipt.reference_capture_ids[i], receipt.reference_capture_ids[j]) for i in range(len(receipt.reference_capture_ids)) for j in range(i + 1, len(receipt.reference_capture_ids))}
    seen: set[tuple[str, str]] = set()
    losses: list[float] = []
    for left, right, loss_raw in receipt.pairwise_losses:
        if (left, right) not in expected_pairs or (left, right) in seen:
            raise SpecError("reference pairwise-loss roster is duplicate, reversed, or extra")
        seen.add((left, right))
        loss = _finite(loss_raw, "reference pairwise loss")
        if not 0.0 <= loss <= 1.0:
            raise SpecError("reference pairwise loss outside [0,1]")
        losses.append(loss)
        common = masks[left] & masks[right]
        actual_loss = normalized_rgb_mse(images[left], images[right], common, support)
        if not math.isclose(loss, actual_loss, rel_tol=0.0, abs_tol=1e-15):
            raise SpecError("reference pairwise loss is not derived from bound observations")
    if seen != expected_pairs:
        raise SpecError("reference pairwise-loss roster is incomplete")
    delta_ref = max(losses)
    delta_u = max(DELTA_B, 2.0 * delta_ref)
    if not math.isclose(receipt.delta_ref, delta_ref, rel_tol=0.0, abs_tol=1e-15) or not math.isclose(receipt.delta_u, delta_u, rel_tol=0.0, abs_tol=1e-15):
        raise SpecError("reference uncertainty thresholds are inconsistent")
    if type(receipt.eligible_for_primary_rcsu) is not bool or receipt.eligible_for_primary_rcsu != (delta_ref <= DELTA_B):
        raise SpecError("reference uncertainty eligibility is inconsistent")
    if receipt.canonical_sha256 != _canonical_lines_sha("S48_REFERENCE_UNCERTAINTY_V3", _reference_uncertainty_lines(receipt)):
        raise SpecError("reference uncertainty canonical hash mismatch")


@dataclass(frozen=True, order=True)
class UtilityKey:
    source_id: str
    target: str
    seed: str
    reference_capture_id: str
    estimand: str
    family: str
    sign: int
    replacement_id: str


_UTILITY_ESTIMANDS = ("LOCAL_EDIT_PREFERENCE", "MATCHED_REPLACEMENT_RCSU", "SOURCE_ABSENCE_RCSU")


def _validate_utility_key(key: UtilityKey) -> None:
    if not isinstance(key, UtilityKey) or key.estimand not in _UTILITY_ESTIMANDS:
        raise SpecError("utility key or estimand is invalid")
    for name in ("source_id", "target", "seed", "reference_capture_id"):
        value = getattr(key, name)
        if type(value) is not str or not value or "\n" in value:
            raise SpecError(f"utility key {name} must be a non-empty single-line string")
    if key.estimand == "LOCAL_EDIT_PREFERENCE":
        if key.family not in ("exposure_log_gain", "texture_highpass") or type(key.sign) is not int or key.sign not in (-1, 1) or key.replacement_id != "":
            raise SpecError("local-edit utility key fields are invalid")
    elif key.estimand == "MATCHED_REPLACEMENT_RCSU":
        if key.family != "" or key.sign != 0 or type(key.replacement_id) is not str or not key.replacement_id:
            raise SpecError("matched-replacement utility key fields are invalid")
    else:
        if key.family != "" or key.sign != 0 or key.replacement_id != "ABSENT":
            raise SpecError("source-absence utility key fields are invalid")


@dataclass(frozen=True)
class UtilityReceipt:
    key: UtilityKey
    reference_uncertainty: ReferenceUncertaintyReceipt
    outputs_u8: tuple[np.ndarray, np.ndarray, np.ndarray]
    valid_mask: np.ndarray
    support: np.ndarray
    reference_uncertainty_sha256: str
    treatment_output_sha256: str
    comparator_output_sha256: str
    reference_output_sha256: str
    valid_sha256: str
    support_sha256: str
    outside_sha256: str
    support_utility: float
    outside_difference: float
    delta_u: float
    outside_tolerance: float
    signed_class: int
    outside_guard_passed: bool
    canonical_sha256: str


def _utility_hash_lines(receipt: UtilityReceipt) -> tuple[str, ...]:
    key = receipt.key
    return (
        key.source_id, key.target, key.seed, key.reference_capture_id, key.estimand,
        key.family, str(key.sign), key.replacement_id, receipt.reference_uncertainty_sha256,
        receipt.treatment_output_sha256, receipt.comparator_output_sha256, receipt.reference_output_sha256,
        receipt.valid_sha256, receipt.support_sha256, receipt.outside_sha256,
        receipt.support_utility.hex(), receipt.outside_difference.hex(), receipt.delta_u.hex(),
        receipt.outside_tolerance.hex(), str(receipt.signed_class), str(int(receipt.outside_guard_passed)),
    )


def build_utility_receipt(
    treatment_u8: Any, comparator_u8: Any, reference_u8: Any,
    valid: Any, support: Any, *, key: UtilityKey,
    reference_uncertainty: ReferenceUncertaintyReceipt,
) -> UtilityReceipt:
    _validate_utility_key(key)
    validate_reference_uncertainty(reference_uncertainty)
    if not reference_uncertainty.eligible_for_primary_rcsu:
        raise SpecError("reference uncertainty exceeds the primary RCSU limit")
    if key.reference_capture_id not in reference_uncertainty.reference_capture_ids:
        raise SpecError("utility reference capture is outside the frozen reference roster")
    treatment = _u8_rgb(treatment_u8, "treatment_u8", native=True)
    comparator = _u8_rgb(comparator_u8, "comparator_u8", native=True)
    reference = _u8_rgb(reference_u8, "reference_u8", native=True)
    bound_outputs = tuple(np.array(array, dtype=np.uint8, order="C", copy=True) for array in (treatment, comparator, reference))
    for array in bound_outputs:
        array.setflags(write=False)
    treatment, comparator, reference = bound_outputs
    valid_mask = np.array(_bool_mask(valid, "valid", (NATIVE_HEIGHT, NATIVE_WIDTH)), dtype=bool, order="C", copy=True)
    valid_mask.setflags(write=False)
    w = _readonly_f64_weight(support, "support", (NATIVE_HEIGHT, NATIVE_WIDTH))
    if _canonical_array_sha("S48_RCSU_SUPPORT_V3", w) != reference_uncertainty.support_sha256:
        raise SpecError("utility support differs from the reference-uncertainty support")
    outside = 1.0 - w
    if float(np.sum(w)) <= 0.0 or float(np.sum(outside)) <= 0.0:
        raise SpecError("utility support and outside must both be nonempty")
    support_value = normalized_rgb_mse(treatment, reference, valid_mask, w) - normalized_rgb_mse(comparator, reference, valid_mask, w)
    outside_value = normalized_rgb_mse(treatment, reference, valid_mask, outside) - normalized_rgb_mse(comparator, reference, valid_mask, outside)
    delta_u = reference_uncertainty.delta_u
    signed_class = 1 if support_value >= delta_u else (-1 if support_value <= -delta_u else 0)
    outside_tolerance = max(DELTA_OUT, 2.0 * reference_uncertainty.delta_ref)
    outside_passed = abs(outside_value) <= outside_tolerance
    domains = ("TREATMENT", "COMPARATOR", "REFERENCE")
    output_hashes = tuple(_canonical_array_sha(f"S48_UTILITY_{domain}_OUTPUT_V3", array) for domain, array in zip(domains, (treatment, comparator, reference)))
    provisional = UtilityReceipt(
        key, reference_uncertainty, bound_outputs, valid_mask, w,
        reference_uncertainty.canonical_sha256, *output_hashes,
        _canonical_array_sha("S48_UTILITY_VALID_BOOL_V3", valid_mask),
        _canonical_array_sha("S48_UTILITY_SUPPORT_V3", w),
        _canonical_array_sha("S48_UTILITY_OUTSIDE_V3", outside),
        support_value, outside_value, delta_u, outside_tolerance, signed_class,
        outside_passed, "0" * 64,
    )
    digest = _canonical_lines_sha("S48_UTILITY_RECEIPT_V3", _utility_hash_lines(provisional))
    return UtilityReceipt(**{**provisional.__dict__, "canonical_sha256": digest})


def validate_utility_receipt(receipt: UtilityReceipt) -> None:
    if not isinstance(receipt, UtilityReceipt):
        raise SpecError("utility evidence must be a typed UtilityReceipt")
    _validate_utility_key(receipt.key)
    validate_reference_uncertainty(receipt.reference_uncertainty)
    if receipt.reference_uncertainty_sha256 != receipt.reference_uncertainty.canonical_sha256 or receipt.key.reference_capture_id not in receipt.reference_uncertainty.reference_capture_ids:
        raise SpecError("utility receipt does not bind the exact eligible reference evidence")
    if not isinstance(receipt.outputs_u8, tuple) or len(receipt.outputs_u8) != 3:
        raise SpecError("utility receipt must bind treatment/comparator/reference outputs")
    outputs = tuple(_u8_rgb(value, f"utility.outputs_u8[{index}]", native=True) for index, value in enumerate(receipt.outputs_u8))
    if any(array.flags.writeable for array in outputs):
        raise SpecError("utility output evidence must be frozen read-only")
    valid_mask = _bool_mask(receipt.valid_mask, "utility valid_mask", (NATIVE_HEIGHT, NATIVE_WIDTH))
    support = _strict_f64_weight(receipt.support, "utility support", (NATIVE_HEIGHT, NATIVE_WIDTH))
    if valid_mask.flags.writeable or support.flags.writeable:
        raise SpecError("utility valid/support evidence must be frozen read-only")
    if _canonical_array_sha("S48_RCSU_SUPPORT_V3", support) != receipt.reference_uncertainty.support_sha256:
        raise SpecError("utility support differs from bound reference uncertainty")
    for name in (
        "reference_uncertainty_sha256", "treatment_output_sha256", "comparator_output_sha256",
        "reference_output_sha256", "valid_sha256", "support_sha256", "outside_sha256",
    ):
        _sha(getattr(receipt, name), name)
    expected_output_hashes = tuple(
        _canonical_array_sha(f"S48_UTILITY_{domain}_OUTPUT_V3", array)
        for domain, array in zip(("TREATMENT", "COMPARATOR", "REFERENCE"), outputs)
    )
    if (receipt.treatment_output_sha256, receipt.comparator_output_sha256, receipt.reference_output_sha256) != expected_output_hashes:
        raise SpecError("utility output hashes are not derived from bound outputs")
    outside_weight = 1.0 - support
    if receipt.valid_sha256 != _canonical_array_sha("S48_UTILITY_VALID_BOOL_V3", valid_mask) or receipt.support_sha256 != _canonical_array_sha("S48_UTILITY_SUPPORT_V3", support) or receipt.outside_sha256 != _canonical_array_sha("S48_UTILITY_OUTSIDE_V3", outside_weight):
        raise SpecError("utility domain hashes are not derived from bound masks")
    value = _finite(receipt.support_utility, "support_utility")
    outside = _finite(receipt.outside_difference, "outside_difference")
    delta_u = _finite(receipt.delta_u, "delta_u")
    tolerance = _finite(receipt.outside_tolerance, "outside_tolerance")
    expected_value = normalized_rgb_mse(outputs[0], outputs[2], valid_mask, support) - normalized_rgb_mse(outputs[1], outputs[2], valid_mask, support)
    expected_outside = normalized_rgb_mse(outputs[0], outputs[2], valid_mask, outside_weight) - normalized_rgb_mse(outputs[1], outputs[2], valid_mask, outside_weight)
    expected_delta_u = receipt.reference_uncertainty.delta_u
    expected_tolerance = max(DELTA_OUT, 2.0 * receipt.reference_uncertainty.delta_ref)
    if not math.isclose(value, expected_value, rel_tol=0.0, abs_tol=1e-15) or not math.isclose(outside, expected_outside, rel_tol=0.0, abs_tol=1e-15) or not math.isclose(delta_u, expected_delta_u, rel_tol=0.0, abs_tol=1e-15) or not math.isclose(tolerance, expected_tolerance, rel_tol=0.0, abs_tol=1e-15):
        raise SpecError("utility scalars are not derived from bound evidence")
    if not -1.0 <= value <= 1.0 or not -1.0 <= outside <= 1.0 or delta_u < DELTA_B or tolerance < DELTA_OUT:
        raise SpecError("utility receipt scalar domain invalid")
    signed_class = 1 if value >= delta_u else (-1 if value <= -delta_u else 0)
    if type(receipt.signed_class) is not int or receipt.signed_class != signed_class:
        raise SpecError("utility signed class is inconsistent")
    if type(receipt.outside_guard_passed) is not bool or receipt.outside_guard_passed != (abs(outside) <= tolerance):
        raise SpecError("utility outside guard is inconsistent")
    if receipt.canonical_sha256 != _canonical_lines_sha("S48_UTILITY_RECEIPT_V3", _utility_hash_lines(receipt)):
        raise SpecError("utility receipt canonical hash mismatch")


def local_benefit(*args: Any, **kwargs: Any) -> None:
    raise SpecError("V7 renamed this estimand LOCAL_EDIT_PREFERENCE; use build_utility_receipt")


def matched_benefit(*args: Any, **kwargs: Any) -> None:
    raise SpecError("V7 renamed this estimand MATCHED_REPLACEMENT_RCSU; use build_utility_receipt")


def benefit_decision(*args: Any, **kwargs: Any) -> None:
    raise SpecError("V7 forbids free utility scalars; use a typed UtilityReceipt")


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


@dataclass(frozen=True)
class QualityCalibrationReceipt:
    metric_name: str
    cal_manifest_sha256: str
    sorted_values: tuple[float, ...]
    cutpoints: tuple[float, float, float]
    canonical_sha256: str


def _quality_calibration_lines(receipt: QualityCalibrationReceipt) -> tuple[str, ...]:
    return (
        receipt.metric_name, receipt.cal_manifest_sha256,
        *(value.hex() for value in receipt.sorted_values),
        *(value.hex() for value in receipt.cutpoints),
    )


def build_quality_calibration(values: Sequence[Any], *, cal_manifest_sha256: str) -> QualityCalibrationReceipt:
    if not isinstance(values, (tuple, list)) or len(values) < 8:
        raise SpecError("quality CAL requires at least eight frozen values")
    digest = _sha(cal_manifest_sha256, "cal_manifest_sha256")
    ordered = tuple(sorted(_finite(value, "quality CAL value") for value in values))
    if any(value < 0.0 or value > 1.0 for value in ordered):
        raise SpecError("quality CAL values must lie in [0,1]")
    n = len(ordered)
    cutpoints = tuple(ordered[max(0, math.ceil(fraction * n) - 1)] for fraction in (0.25, 0.50, 0.75))
    provisional = QualityCalibrationReceipt("CAL_SOURCE_REPROJECTION_RGB_MSE_V1", digest, ordered, cutpoints, "0" * 64)
    return QualityCalibrationReceipt(**{**provisional.__dict__, "canonical_sha256": _canonical_lines_sha("S48_QUALITY_CALIBRATION_V3", _quality_calibration_lines(provisional))})


def validate_quality_calibration(receipt: QualityCalibrationReceipt) -> None:
    if not isinstance(receipt, QualityCalibrationReceipt) or receipt.metric_name != "CAL_SOURCE_REPROJECTION_RGB_MSE_V1":
        raise SpecError("quality calibration type or metric mismatch")
    _sha(receipt.cal_manifest_sha256, "cal_manifest_sha256")
    if not isinstance(receipt.sorted_values, tuple) or len(receipt.sorted_values) < 8:
        raise SpecError("quality calibration has too few values")
    values = tuple(_finite(value, "quality calibration value") for value in receipt.sorted_values)
    if values != tuple(sorted(values)) or any(value < 0.0 or value > 1.0 for value in values):
        raise SpecError("quality calibration values are unsorted or outside [0,1]")
    n = len(values)
    expected_cuts = tuple(values[max(0, math.ceil(fraction * n) - 1)] for fraction in (0.25, 0.50, 0.75))
    if receipt.cutpoints != expected_cuts:
        raise SpecError("quality calibration cutpoints are not nearest-rank Q1/Q2/Q3")
    if receipt.canonical_sha256 != _canonical_lines_sha("S48_QUALITY_CALIBRATION_V3", _quality_calibration_lines(receipt)):
        raise SpecError("quality calibration canonical hash mismatch")


def quality_quartile(value: Any, calibration: QualityCalibrationReceipt) -> int:
    validate_quality_calibration(calibration)
    number = _finite(value, "source quality")
    if not 0.0 <= number <= 1.0:
        raise SpecError("source quality must lie in [0,1]")
    return int(np.searchsorted(np.asarray(calibration.cutpoints, dtype=np.float64), number, side="right"))


def binary_support_iou(first: Any, second: Any) -> float:
    a = _strict_f64_weight(first, "first_support") > 0.0
    b = _strict_f64_weight(second, "second_support", a.shape) > 0.0
    union = int(np.count_nonzero(a | b))
    if union == 0:
        raise SpecError("support IoU union is empty")
    return float(np.count_nonzero(a & b) / union)


def weighted_area_ratio(candidate: Any, ordinary: Any) -> float:
    p = _strict_f64_weight(candidate, "candidate_support")
    o = _strict_f64_weight(ordinary, "ordinary_support", p.shape)
    denominator = float(np.sum(o))
    if denominator <= EPS:
        raise SpecError("ordinary support weighted area is zero")
    return float(np.sum(p) / denominator)


@dataclass(frozen=True)
class ReplacementCandidate:
    source_id: str
    file_sha256: str
    insertion_event: int
    scene_id: str
    camera: Camera
    support: np.ndarray
    support_sha256: str
    source_quality: float
    identity_receipt: IdentityAgreement
    view_pair_receipts: tuple[ViewPairReceipt, ...]
    domain_receipts: Mapping[str, ValidDomainReceipt]


def build_replacement_candidate(
    *, source_id: str, file_sha256: str, insertion_event: int, scene_id: str,
    camera: Camera, support: Any, source_quality: Any,
    identity_receipt: IdentityAgreement, view_pair_receipts: tuple[ViewPairReceipt, ...],
    domain_receipts: Mapping[str, ValidDomainReceipt],
) -> ReplacementCandidate:
    if type(source_id) is not str or not source_id or "\n" in source_id or type(scene_id) is not str or not scene_id or "\n" in scene_id:
        raise SpecError("replacement source and scene IDs must be non-empty single-line strings")
    digest = _sha(file_sha256, "replacement file_sha256")
    event = _strict_int(insertion_event, "replacement insertion_event", minimum=0)
    _validate_camera(camera, "replacement camera")
    support_arr = _readonly_f64_weight(support, "replacement support")
    quality = _finite(source_quality, "replacement source_quality")
    if not 0.0 <= quality <= 1.0:
        raise SpecError("replacement source_quality must lie in [0,1]")
    return ReplacementCandidate(
        source_id, digest, event, scene_id, camera, support_arr,
        _canonical_array_sha("S48_REPLACEMENT_SUPPORT_V3", support_arr), quality,
        identity_receipt, view_pair_receipts, domain_receipts,
    )


@dataclass(frozen=True)
class ReplacementFlowRecord:
    source_id: str
    file_sha256: str
    insertion_event: int
    camera_metrics: CameraMatchMetrics
    support_iou: float
    weighted_area_ratio: float
    ordinary_quality_quartile: int
    candidate_quality_quartile: int
    eligible: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class ReplacementRosterReceipt:
    candidates: tuple[ReplacementCandidate, ...]
    ordinary_source_id: str
    ordinary_insertion_event: int
    ordinary_scene_id: str
    target_camera: Camera
    ordinary_camera: Camera
    ordinary_support: np.ndarray
    ordinary_source_quality: float
    quality_calibration: QualityCalibrationReceipt
    quality_calibration_sha256: str
    ordinary_support_sha256: str
    flow: tuple[ReplacementFlowRecord, ...]
    eligible_source_ids: tuple[str, ...]
    canonical_sha256: str


def build_replacement_roster(
    candidates: Sequence[ReplacementCandidate], *, ordinary_source_id: str,
    ordinary_insertion_event: int, ordinary_scene_id: str,
    target_camera: Camera, ordinary_camera: Camera, ordinary_support: Any,
    ordinary_source_quality: Any, quality_calibration: QualityCalibrationReceipt,
) -> ReplacementRosterReceipt:
    if type(ordinary_source_id) is not str or not ordinary_source_id or type(ordinary_scene_id) is not str or not ordinary_scene_id:
        raise SpecError("ordinary source and scene IDs must be non-empty strings")
    event_o = _strict_int(ordinary_insertion_event, "ordinary_insertion_event", minimum=0)
    validate_quality_calibration(quality_calibration)
    support_o = _readonly_f64_weight(ordinary_support, "ordinary_support")
    if not 0.0 < float(np.mean(support_o)) < 1.0:
        raise SpecError("ordinary support must be nonempty and nonfull")
    support_o_hash = _canonical_array_sha("S48_ORDINARY_SUPPORT_V3", support_o)
    quality_o = _finite(ordinary_source_quality, "ordinary_source_quality")
    quartile_o = quality_quartile(quality_o, quality_calibration)
    seen_sources: set[str] = set()
    seen_files: set[str] = set()
    flow: list[ReplacementFlowRecord] = []
    if not isinstance(candidates, (tuple, list)) or any(not isinstance(item, ReplacementCandidate) for item in candidates):
        raise SpecError("replacement roster entries must be typed ReplacementCandidate objects")
    ordered = sorted(candidates, key=lambda item: (item.insertion_event, item.source_id.encode("utf-8"), item.file_sha256))
    for candidate in ordered:
        if not isinstance(candidate, ReplacementCandidate):
            raise SpecError("replacement roster entries must be typed")
        if candidate.source_id in seen_sources or candidate.file_sha256 in seen_files:
            raise SpecError("replacement roster contains duplicate source or file identity")
        seen_sources.add(candidate.source_id)
        seen_files.add(candidate.file_sha256)
        _sha(candidate.file_sha256, "replacement file_sha256")
        _strict_int(candidate.insertion_event, "replacement insertion_event", minimum=0)
        support_p = _strict_f64_weight(candidate.support, "replacement support", support_o.shape)
        if support_p.flags.writeable or candidate.support_sha256 != _canonical_array_sha("S48_REPLACEMENT_SUPPORT_V3", support_p):
            raise SpecError("replacement support is mutable or hash-mismatched")
        metrics = camera_match_metrics(target_camera, ordinary_camera, candidate.camera)
        iou = binary_support_iou(support_p, support_o)
        area_ratio = weighted_area_ratio(support_p, support_o)
        quartile_p = quality_quartile(candidate.source_quality, quality_calibration)
        reasons: list[str] = []
        if candidate.source_id == ordinary_source_id:
            reasons.append("ORDINARY_SOURCE_REUSED")
        if candidate.scene_id != ordinary_scene_id:
            reasons.append("SCENE_ID_MISMATCH")
        if not replacement_recency_eligible(event_o, candidate.insertion_event):
            reasons.append("MEMORY_RECENCY_ABOVE_2")
        if metrics.angle_microdegrees > 2_000_000:
            reasons.append("TARGET_ANGLE_ABOVE_2DEG")
        if metrics.position_ratio_ppm > 100_000:
            reasons.append("TARGET_POSITION_RATIO_ABOVE_010")
        if metrics.fov_microdegrees > 1_000_000:
            reasons.append("FOV_DIFFERENCE_ABOVE_1DEG")
        if iou < 0.80:
            reasons.append("BINARY_SUPPORT_IOU_BELOW_080")
        if area_ratio < 0.90 or area_ratio > 1.10:
            reasons.append("WEIGHTED_AREA_RATIO_OUTSIDE_090_110")
        if quartile_p != quartile_o:
            reasons.append("CAL_SOURCE_QUALITY_QUARTILE_MISMATCH")
        try:
            if not isinstance(candidate.identity_receipt, IdentityAgreement) or candidate.identity_receipt.roles != ("O", "R", "P") or not identity_decision(candidate.identity_receipt)[0]:
                reasons.append("IDENTITY_CONTRACT_FAILED")
            if not isinstance(candidate.view_pair_receipts, tuple) or not validate_view_pair_receipts(candidate.view_pair_receipts, include_replacement=True)[0]:
                reasons.append("VIEW_PAIR_CONTRACT_FAILED")
            if set(candidate.domain_receipts) != {"support", "outside"} or any(
                receipt.domain != domain or not valid_domain_decision(receipt, required_roles=("O", "R", "P"))[0]
                for domain, receipt in candidate.domain_receipts.items()
            ):
                reasons.append("DOMAIN_CONTRACT_FAILED")
            elif not np.array_equal(candidate.identity_receipt.support > 0.0, support_p > 0.0) or not np.array_equal(candidate.domain_receipts["support"].domain_mask, support_p > 0.0):
                reasons.append("P_IDENTITY_SUPPORT_DOMAIN_MISMATCH")
            elif not np.array_equal(candidate.domain_receipts["outside"].domain_mask, ~(support_p > 0.0)):
                reasons.append("P_SUPPORT_OUTSIDE_DOMAIN_NOT_COMPLEMENTARY")
        except SpecError:
            reasons.append("TYPED_EVIDENCE_INVALID")
        flow.append(ReplacementFlowRecord(candidate.source_id, candidate.file_sha256, candidate.insertion_event, metrics, iou, area_ratio, quartile_o, quartile_p, not reasons, tuple(reasons)))
    eligible = tuple(record.source_id for record in flow if record.eligible)
    if not eligible:
        raise SpecError("replacement roster has no eligible candidate")
    lines = [quality_calibration.canonical_sha256, support_o_hash]
    lines.extend(
        f"{record.insertion_event}\t{record.source_id}\t{record.file_sha256}\t{record.camera_metrics.angle_microdegrees}\t{record.camera_metrics.position_ratio_ppm}\t{record.camera_metrics.fov_microdegrees}\t{record.support_iou.hex()}\t{record.weighted_area_ratio.hex()}\t{record.ordinary_quality_quartile}\t{record.candidate_quality_quartile}\t{int(record.eligible)}\t{','.join(record.reasons)}"
        for record in flow
    )
    return ReplacementRosterReceipt(
        tuple(ordered), ordinary_source_id, event_o, ordinary_scene_id, target_camera, ordinary_camera,
        support_o, quality_o, quality_calibration, quality_calibration.canonical_sha256, support_o_hash,
        tuple(flow), eligible, _canonical_lines_sha("S48_REPLACEMENT_ROSTER_V3", lines),
    )


def validate_replacement_roster_receipt(receipt: ReplacementRosterReceipt) -> None:
    if not isinstance(receipt, ReplacementRosterReceipt):
        raise SpecError("replacement roster receipt must be typed")
    if not isinstance(receipt.candidates, tuple) or not receipt.candidates:
        raise SpecError("replacement roster must bind its candidate tuple")
    validate_quality_calibration(receipt.quality_calibration)
    if receipt.quality_calibration_sha256 != receipt.quality_calibration.canonical_sha256:
        raise SpecError("replacement roster does not bind its quality calibration")
    support = _strict_f64_weight(receipt.ordinary_support, "bound ordinary support")
    if support.flags.writeable:
        raise SpecError("bound ordinary support must be frozen read-only")
    _sha(receipt.quality_calibration_sha256, "quality_calibration_sha256")
    _sha(receipt.ordinary_support_sha256, "ordinary_support_sha256")
    if receipt.ordinary_support_sha256 != _canonical_array_sha("S48_ORDINARY_SUPPORT_V3", support):
        raise SpecError("replacement roster ordinary-support hash mismatch")
    if not isinstance(receipt.flow, tuple) or not receipt.flow:
        raise SpecError("replacement roster flow must be a non-empty tuple")
    seen: set[str] = set()
    lines = [receipt.quality_calibration_sha256, receipt.ordinary_support_sha256]
    eligible: list[str] = []
    previous_key: tuple[int, bytes, str] | None = None
    for record in receipt.flow:
        if not isinstance(record, ReplacementFlowRecord) or record.source_id in seen:
            raise SpecError("replacement flow record is untyped or duplicated")
        seen.add(record.source_id)
        _sha(record.file_sha256, "replacement flow file_sha256")
        event = _strict_int(record.insertion_event, "replacement flow insertion_event", minimum=0)
        order_key = (event, record.source_id.encode("utf-8"), record.file_sha256)
        if previous_key is not None and order_key < previous_key:
            raise SpecError("replacement flow is not in canonical order")
        previous_key = order_key
        iou = _finite(record.support_iou, "support_iou")
        ratio = _finite(record.weighted_area_ratio, "weighted_area_ratio")
        if not 0.0 <= iou <= 1.0 or ratio < 0.0:
            raise SpecError("replacement support metric domain invalid")
        _strict_int(record.ordinary_quality_quartile, "ordinary_quality_quartile", minimum=0)
        _strict_int(record.candidate_quality_quartile, "candidate_quality_quartile", minimum=0)
        if record.ordinary_quality_quartile > 3 or record.candidate_quality_quartile > 3:
            raise SpecError("replacement quartile outside 0..3")
        if type(record.eligible) is not bool or not isinstance(record.reasons, tuple) or record.eligible != (len(record.reasons) == 0):
            raise SpecError("replacement eligibility decision is inconsistent")
        if record.eligible:
            eligible.append(record.source_id)
        lines.append(
            f"{record.insertion_event}\t{record.source_id}\t{record.file_sha256}\t{record.camera_metrics.angle_microdegrees}\t{record.camera_metrics.position_ratio_ppm}\t{record.camera_metrics.fov_microdegrees}\t{record.support_iou.hex()}\t{record.weighted_area_ratio.hex()}\t{record.ordinary_quality_quartile}\t{record.candidate_quality_quartile}\t{int(record.eligible)}\t{','.join(record.reasons)}"
        )
    if not eligible or receipt.eligible_source_ids != tuple(eligible):
        raise SpecError("replacement eligible roster is empty or inconsistent")
    if receipt.canonical_sha256 != _canonical_lines_sha("S48_REPLACEMENT_ROSTER_V3", lines):
        raise SpecError("replacement roster canonical hash mismatch")
    rebuilt = build_replacement_roster(
        receipt.candidates,
        ordinary_source_id=receipt.ordinary_source_id,
        ordinary_insertion_event=receipt.ordinary_insertion_event,
        ordinary_scene_id=receipt.ordinary_scene_id,
        target_camera=receipt.target_camera,
        ordinary_camera=receipt.ordinary_camera,
        ordinary_support=support,
        ordinary_source_quality=receipt.ordinary_source_quality,
        quality_calibration=receipt.quality_calibration,
    )
    if (
        rebuilt.quality_calibration_sha256 != receipt.quality_calibration_sha256
        or rebuilt.ordinary_support_sha256 != receipt.ordinary_support_sha256
        or rebuilt.flow != receipt.flow
        or rebuilt.eligible_source_ids != receipt.eligible_source_ids
        or rebuilt.canonical_sha256 != receipt.canonical_sha256
    ):
        raise SpecError("replacement roster flow is not derived from bound candidates")


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


# ---------------------------------------------------------------------------
# Exact sequential S48 ledger: AOIG -> support/effect screen -> RCSU


@dataclass(frozen=True)
class ExperimentPlan:
    source_id: str
    targets: tuple[str, ...]
    seeds: tuple[str, ...]
    families: tuple[str, str]
    signs: tuple[int, int]
    replacement_ids: tuple[str, ...]
    reference_capture_ids: tuple[str, ...]
    reference_uncertainty_sha256: str
    replacement_roster_sha256: str
    include_source_absence: bool
    canonical_sha256: str


def _validate_unique_strings(values: tuple[str, ...], name: str, *, minimum: int) -> None:
    if not isinstance(values, tuple) or len(values) < minimum or len(set(values)) != len(values):
        raise SpecError(f"{name} must be a tuple of at least {minimum} unique strings")
    if any(type(value) is not str or not value or "\n" in value for value in values):
        raise SpecError(f"{name} contains an invalid string")


def _experiment_plan_lines(plan: ExperimentPlan) -> tuple[str, ...]:
    return (
        plan.source_id, ",".join(plan.targets), ",".join(plan.seeds), ",".join(plan.families),
        ",".join(str(value) for value in plan.signs), ",".join(plan.replacement_ids),
        ",".join(plan.reference_capture_ids), plan.reference_uncertainty_sha256,
        plan.replacement_roster_sha256, str(int(plan.include_source_absence)),
    )


def build_experiment_plan(
    *, source_id: str, targets: tuple[str, ...], seeds: tuple[str, ...],
    replacement_ids: tuple[str, ...], reference_capture_ids: tuple[str, ...],
    reference_uncertainty_sha256: str, replacement_roster_sha256: str,
    include_source_absence: bool,
) -> ExperimentPlan:
    if type(source_id) is not str or not source_id or "\n" in source_id:
        raise SpecError("experiment source_id must be a non-empty single-line string")
    _validate_unique_strings(targets, "targets", minimum=1)
    _validate_unique_strings(seeds, "seeds", minimum=5)
    if len(seeds) != 5:
        raise SpecError("RAIMA V3 cell plan requires exactly five paired seeds")
    _validate_unique_strings(replacement_ids, "replacement_ids", minimum=1)
    _validate_unique_strings(reference_capture_ids, "reference_capture_ids", minimum=3)
    if source_id in replacement_ids:
        raise SpecError("ordinary source cannot also be a replacement")
    reference_digest = _sha(reference_uncertainty_sha256, "reference_uncertainty_sha256")
    replacement_digest = _sha(replacement_roster_sha256, "replacement_roster_sha256")
    absence = _strict_bool(include_source_absence, "include_source_absence")
    provisional = ExperimentPlan(
        source_id, targets, seeds, ("exposure_log_gain", "texture_highpass"), (-1, 1),
        replacement_ids, reference_capture_ids, reference_digest, replacement_digest, absence, "0" * 64,
    )
    return ExperimentPlan(**{**provisional.__dict__, "canonical_sha256": _canonical_lines_sha("S48_EXPERIMENT_PLAN_V3", _experiment_plan_lines(provisional))})


def validate_experiment_plan(plan: ExperimentPlan) -> None:
    if not isinstance(plan, ExperimentPlan):
        raise SpecError("experiment plan must be typed")
    _validate_unique_strings(plan.targets, "targets", minimum=1)
    _validate_unique_strings(plan.seeds, "seeds", minimum=5)
    if len(plan.seeds) != 5 or plan.families != ("exposure_log_gain", "texture_highpass") or plan.signs != (-1, 1):
        raise SpecError("experiment plan grid differs from the frozen RAIMA V3 grid")
    _validate_unique_strings(plan.replacement_ids, "replacement_ids", minimum=1)
    _validate_unique_strings(plan.reference_capture_ids, "reference_capture_ids", minimum=3)
    _sha(plan.reference_uncertainty_sha256, "reference_uncertainty_sha256")
    _sha(plan.replacement_roster_sha256, "replacement_roster_sha256")
    if type(plan.include_source_absence) is not bool:
        raise SpecError("include_source_absence must be bool")
    if plan.canonical_sha256 != _canonical_lines_sha("S48_EXPERIMENT_PLAN_V3", _experiment_plan_lines(plan)):
        raise SpecError("experiment plan canonical hash mismatch")


@dataclass(frozen=True)
class SequentialLedgerDecision:
    plan_sha256: str
    terminal_action: str
    influence_count: int
    support_effect_count: int
    utility_count: int
    reasons: tuple[str, ...]
    canonical_sha256: str


def _expected_cell_keys(plan: ExperimentPlan) -> set[CellKey]:
    return {
        CellKey(plan.source_id, target, seed, family, sign)
        for target in plan.targets for seed in plan.seeds for family in plan.families for sign in plan.signs
    }


def _expected_utility_keys(plan: ExperimentPlan) -> set[UtilityKey]:
    keys: set[UtilityKey] = set()
    for target in plan.targets:
        for seed in plan.seeds:
            for reference in plan.reference_capture_ids:
                for family in plan.families:
                    for sign in plan.signs:
                        keys.add(UtilityKey(plan.source_id, target, seed, reference, "LOCAL_EDIT_PREFERENCE", family, sign, ""))
                for replacement in plan.replacement_ids:
                    keys.add(UtilityKey(plan.source_id, target, seed, reference, "MATCHED_REPLACEMENT_RCSU", "", 0, replacement))
                if plan.include_source_absence:
                    keys.add(UtilityKey(plan.source_id, target, seed, reference, "SOURCE_ABSENCE_RCSU", "", 0, "ABSENT"))
    return keys


def _sequential_decision(
    plan: ExperimentPlan, action: str, influence_count: int, support_count: int,
    utility_count: int, reasons: Sequence[str],
) -> SequentialLedgerDecision:
    reason_tuple = tuple(reasons)
    lines = (plan.canonical_sha256, action, str(influence_count), str(support_count), str(utility_count), *reason_tuple)
    return SequentialLedgerDecision(plan.canonical_sha256, action, influence_count, support_count, utility_count, reason_tuple, _canonical_lines_sha("S48_SEQUENTIAL_DECISION_V3", lines))


def _rcsu_stability_failures(plan: ExperimentPlan, utilities: Mapping[UtilityKey, UtilityReceipt]) -> list[str]:
    groups: dict[tuple[str, str, str, int, str], list[UtilityReceipt]] = {}
    for receipt in utilities.values():
        key = receipt.key
        group_key = (key.estimand, key.target, key.family, key.sign, key.replacement_id)
        groups.setdefault(group_key, []).append(receipt)
    failures: list[str] = []
    for group_key, receipts in groups.items():
        reference_signs: list[int] = []
        for reference in plan.reference_capture_ids:
            by_reference = [receipt for receipt in receipts if receipt.key.reference_capture_id == reference]
            if len(by_reference) != 5 or {receipt.key.seed for receipt in by_reference} != set(plan.seeds):
                failures.append(f"RCSU_GROUP_INCOMPLETE:{group_key}:{reference}")
                continue
            signs = [receipt.signed_class for receipt in by_reference]
            positive = sum(sign == 1 for sign in signs)
            negative = sum(sign == -1 for sign in signs)
            majority = 1 if positive >= 4 else (-1 if negative >= 4 else 0)
            median_abs = float(np.median(np.asarray([abs(receipt.support_utility) for receipt in by_reference], dtype=np.float64)))
            threshold = max(receipt.delta_u for receipt in by_reference)
            if majority == 0 or median_abs < threshold:
                failures.append(f"RCSU_SEED_SIGN_OR_MAGNITUDE_UNSTABLE:{group_key}:{reference}")
            reference_signs.append(majority)
        if not reference_signs or 0 in reference_signs or len(set(reference_signs)) != 1:
            failures.append(f"RCSU_REFERENCE_SIGN_UNSTABLE:{group_key}")
    return failures


def evaluate_sequential_ledger(
    plan: ExperimentPlan,
    influences: Sequence[InfluenceReceipt],
    support_effects: Sequence[SupportEffectReceipt] = (),
    utilities: Sequence[UtilityReceipt] = (),
    *,
    reference_uncertainty: ReferenceUncertaintyReceipt,
    replacement_roster: ReplacementRosterReceipt,
) -> SequentialLedgerDecision:
    validate_experiment_plan(plan)
    validate_reference_uncertainty(reference_uncertainty)
    validate_replacement_roster_receipt(replacement_roster)
    if reference_uncertainty.canonical_sha256 != plan.reference_uncertainty_sha256 or reference_uncertainty.reference_capture_ids != plan.reference_capture_ids:
        raise SpecError("plan does not bind the exact reference uncertainty roster")
    if replacement_roster.canonical_sha256 != plan.replacement_roster_sha256 or replacement_roster.eligible_source_ids != plan.replacement_ids:
        raise SpecError("plan does not bind the exact eligible replacement roster")
    expected_cells = _expected_cell_keys(plan)
    influence_by_key: dict[CellKey, InfluenceReceipt] = {}
    for receipt in influences:
        validate_influence_receipt(receipt)
        if receipt.key in influence_by_key:
            raise SpecError("sequential ledger contains duplicate Influence cells")
        influence_by_key[receipt.key] = receipt
    if set(influence_by_key) != expected_cells:
        raise SpecError("sequential ledger Influence grid is missing, extra, or substituted")
    for target in plan.targets:
        for seed in plan.seeds:
            subset = [receipt for key, receipt in influence_by_key.items() if key.target == target and key.seed == seed]
            if len({receipt.replay_ledger_sha256 for receipt in subset}) != 1 or len({receipt.arm_identity_sha256 for receipt in subset}) != 1:
                raise SpecError("same target/seed cells do not share replay and arm-state identity")
            if len({receipt.target_zero_sha256 for receipt in subset}) != 1 or len({receipt.negative_zero_sha256 for receipt in subset}) != 1 or len({receipt.positive_zero_sha256 for receipt in subset}) != 1:
                raise SpecError("same target/seed cells do not share exact same-path zero outputs")
    if any(not receipt.positive_control_passed for receipt in influence_by_key.values()):
        if support_effects or utilities:
            raise SpecError("later-stage evidence is forbidden after positive-control failure")
        return _sequential_decision(plan, "STOP_POSITIVE_CONTROL_INVALID", len(influences), 0, 0, ("POSITIVE_CONTROL_FAILED",))
    target_flags = [receipt.target_observable for receipt in influence_by_key.values()]
    if not any(target_flags):
        if support_effects or utilities:
            raise SpecError("later-stage evidence is forbidden after AOIG stopping decision")
        return _sequential_decision(plan, "AOIG_CANDIDATE_STOP", len(influences), 0, 0, ("ALL_REGISTERED_TARGET_EDITS_BELOW_DELTA_I",))
    if not all(target_flags):
        if support_effects or utilities:
            raise SpecError("later-stage evidence is forbidden after mixed intervention sensitivity")
        return _sequential_decision(plan, "INTERVENTION_SENSITIVITY_STOP", len(influences), 0, 0, ("TARGET_INFLUENCE_MIXED_ACROSS_REGISTERED_CELLS",))
    support_by_key: dict[CellKey, SupportEffectReceipt] = {}
    for receipt in support_effects:
        validate_support_effect_receipt(receipt)
        if receipt.key in support_by_key:
            raise SpecError("sequential ledger contains duplicate support-effect cells")
        support_by_key[receipt.key] = receipt
    if set(support_by_key) != expected_cells:
        raise SpecError("support-effect grid is missing, extra, or substituted")
    for key, receipt in support_by_key.items():
        if receipt.influence_sha256 != influence_by_key[key].canonical_sha256:
            raise SpecError("support-effect cell does not bind its exact Influence receipt")
        if receipt.target_observable != influence_by_key[key].target_observable or receipt.positive_control_passed != influence_by_key[key].positive_control_passed:
            raise SpecError("support-effect cell copied inconsistent Influence decisions")
    if any(not receipt.alignment_passed for receipt in support_by_key.values()):
        if utilities:
            raise SpecError("RCSU evidence is forbidden after support-effect screen failure")
        return _sequential_decision(plan, "SEM_DESCRIPTIVE_STOP", len(influences), len(support_effects), 0, ("SUPPORT_EFFECT_ALIGNMENT_FAILED;HARMFUL_MISLOCALIZATION_NOT_IDENTIFIED",))
    expected_utilities = _expected_utility_keys(plan)
    utility_by_key: dict[UtilityKey, UtilityReceipt] = {}
    for receipt in utilities:
        validate_utility_receipt(receipt)
        if receipt.key in utility_by_key:
            raise SpecError("sequential ledger contains duplicate utility cells")
        utility_by_key[receipt.key] = receipt
    if set(utility_by_key) != expected_utilities:
        raise SpecError("utility grid is missing, extra, or substituted")
    if any(receipt.reference_uncertainty_sha256 != plan.reference_uncertainty_sha256 for receipt in utility_by_key.values()):
        raise SpecError("utility cell reference uncertainty does not match the plan")
    if any(not receipt.outside_guard_passed for receipt in utility_by_key.values()):
        return _sequential_decision(plan, "STOP_OUTSIDE_EFFECT_TOO_LARGE", len(influences), len(support_effects), len(utilities), ("OUTSIDE_GUARD_FAILED",))
    stability_failures = _rcsu_stability_failures(plan, utility_by_key)
    if stability_failures:
        return _sequential_decision(plan, "RCSU_UNSTABLE_STOP", len(influences), len(support_effects), len(utilities), stability_failures)
    action = "RCSU_STABLE_WITH_ABSENCE_CONTRAST_COMPLETE" if plan.include_source_absence else "RCSU_STABLE_COMPARATOR_RELATIVE_ONLY_COMPLETE"
    return _sequential_decision(plan, action, len(influences), len(support_effects), len(utilities), ())
