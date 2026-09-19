#!/usr/bin/env python3
"""Finite NumPy reference for the source-only parts of the S48 V1 contract.

This module does not import, load, or run VMem (or any other model).  It does
not read experiment images.  It implements only deterministic array/statistic
definitions that can be checked with synthetic inputs.  See
S48_NORMATIVE_ANALYSIS_SPEC_V1.md for the normative domain and the explicit
parts that remain BLOCKED.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import math
import re
from typing import Any, Iterable, Mapping, Sequence

import numpy as np


NATIVE_HEIGHT = 576
NATIVE_WIDTH = 576
EPS = 1.0e-12
DEPTH_RELATIVE_BOUNDARY_THRESHOLD = 0.02
BOUNDARY_DENSITY_RADIUS = 2
CONTEXT_VALID_WEIGHT_FRACTION_MIN = 0.95

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
PATCH_MIN_RMS = 2.0 / 255.0
PATCH_MAX_NORMALIZED_SSD = 0.25
PATCH_MIN_MUTUAL_MATCHES = 50

GUARD_MEDIAN_FLOOR_PX = 1.0
GUARD_P95_FLOOR_PX = 3.0
GUARD_BRIGHTNESS_FLOOR = 2.0 / 255.0
GUARD_SHARPNESS_RATIO_FLOOR = 0.10
GUARD_SATURATION_FLOOR_PP = 1.0
GUARD_TEAR_FLOOR = 2.0 / 255.0

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class SpecError(ValueError):
    """Raised when an input is outside the normative finite domain."""


@dataclass(frozen=True)
class SourceEditMetrics:
    mean_absolute_rgb_difference: float
    clipped_channel_fraction: float
    edge_iou: float
    clip_cosine: float
    lpips: float


@dataclass(frozen=True)
class PatchDisplacementMetrics:
    match_count: int
    median_px: float
    p95_px: float


@dataclass(frozen=True)
class ArmGuardMetrics:
    match_count: int
    median_displacement_px: float
    p95_displacement_px: float
    outside_brightness_difference: float
    sharpness_ratio_deviation: float
    saturation_increase_pp: float
    tear_excess: float


@dataclass(frozen=True)
class ArmGuardFloors:
    median_displacement_px: float
    p95_displacement_px: float
    outside_brightness_difference: float
    sharpness_ratio_deviation: float
    saturation_increase_pp: float
    tear_excess: float


@dataclass(frozen=True)
class MaskCaliperMetrics:
    weighted_area_relative_error: float
    reference_component_count: int
    candidate_component_count: int
    normalized_perimeter_relative_error: float
    same_centroid_grid4_cell: bool
    binary_iou: float
    positive_weight_histogram_l1: float
    same_context_strata: bool
    centroid_distance_pixels: float


def _finite_float(value: Any, name: str) -> float:
    if isinstance(value, (bool, np.bool_)):
        raise SpecError(f"{name} must be a finite real number, not bool")
    try:
        out = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise SpecError(f"{name} must be a finite real number") from exc
    if not math.isfinite(out):
        raise SpecError(f"{name} must be finite")
    return out


def _validate_weight_map(weight: Any, name: str = "weight") -> np.ndarray:
    arr = np.asarray(weight, dtype=np.float64)
    if arr.ndim != 2 or arr.size == 0:
        raise SpecError(f"{name} must be a non-empty 2-D array")
    if not np.isfinite(arr).all():
        raise SpecError(f"{name} contains non-finite values")
    if np.any(arr < 0.0) or np.any(arr > 1.0):
        raise SpecError(f"{name} must lie in [0, 1]")
    return arr


def _validate_rgb(rgb: Any, *, native: bool = False, name: str = "rgb") -> np.ndarray:
    arr = np.asarray(rgb, dtype=np.float64)
    if arr.ndim != 3 or arr.shape[2] != 3 or arr.size == 0:
        raise SpecError(f"{name} must have shape H x W x 3")
    if native and arr.shape[:2] != (NATIVE_HEIGHT, NATIVE_WIDTH):
        raise SpecError(
            f"{name} must be native {NATIVE_HEIGHT}x{NATIVE_WIDTH}, got {arr.shape[:2]}"
        )
    if not np.isfinite(arr).all():
        raise SpecError(f"{name} contains non-finite values")
    if np.any(arr < 0.0) or np.any(arr > 1.0):
        raise SpecError(f"{name} must lie in [0, 1]")
    return arr


def _validate_sign(sign: Any) -> int:
    if isinstance(sign, (bool, np.bool_)) or sign not in (-1, 1):
        raise SpecError("sign must be the integer -1 or +1")
    return int(sign)


def _validate_boolean(value: Any, name: str) -> bool:
    if type(value) is not bool:
        raise SpecError(f"{name} must be a JSON/Python boolean")
    return value


def binary_support(weight: Any) -> np.ndarray:
    """Return the frozen binary topology 1{W > 0}."""
    return _validate_weight_map(weight) > 0.0


def connected_components4(weight: Any) -> int:
    """Count positive-weight components using edge adjacency only."""
    support = binary_support(weight)
    height, width = support.shape
    visited = np.zeros_like(support, dtype=bool)
    count = 0
    for row in range(height):
        for col in range(width):
            if not support[row, col] or visited[row, col]:
                continue
            count += 1
            stack = [(row, col)]
            visited[row, col] = True
            while stack:
                rr, cc = stack.pop()
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and support[nr, nc]
                        and not visited[nr, nc]
                    ):
                        visited[nr, nc] = True
                        stack.append((nr, nc))
    return count


def exposed_edge_perimeter(weight: Any) -> int:
    """Count unit lattice edges separating support from non-support/outside."""
    support = binary_support(weight)
    perimeter = 0
    perimeter += int(np.count_nonzero(support[0, :]))
    perimeter += int(np.count_nonzero(support[-1, :]))
    perimeter += int(np.count_nonzero(support[:, 0]))
    perimeter += int(np.count_nonzero(support[:, -1]))
    perimeter += int(np.count_nonzero(support[1:, :] != support[:-1, :]))
    perimeter += int(np.count_nonzero(support[:, 1:] != support[:, :-1]))
    return perimeter


def normalized_perimeter(weight: Any) -> float:
    """Return exposed-edge perimeter divided by sqrt(binary support area)."""
    support = binary_support(weight)
    area = int(np.count_nonzero(support))
    if area == 0:
        raise SpecError("normalized perimeter is undefined for empty support")
    out = exposed_edge_perimeter(weight) / math.sqrt(float(area))
    return _finite_float(out, "normalized_perimeter")


def weighted_area_fraction(weight: Any) -> float:
    arr = _validate_weight_map(weight)
    return _finite_float(np.sum(arr, dtype=np.float64) / arr.size, "weighted_area_fraction")


def positive_weight_histogram(weight: Any) -> np.ndarray:
    """Ten bins on W>0, normalized by positive-pixel count.

    Bins are [0,.1), [.1,.2), ..., [.8,.9), [.9,1].  Zero-weight
    pixels are excluded from both counts and denominator.
    """
    arr = _validate_weight_map(weight)
    positive = arr[arr > 0.0]
    if positive.size == 0:
        raise SpecError("positive-weight histogram is undefined for empty support")
    bins = np.linspace(0.0, 1.0, 11, dtype=np.float64)
    counts, _ = np.histogram(positive, bins=bins)
    out = counts.astype(np.float64) / float(positive.size)
    if not np.isfinite(out).all() or not math.isclose(float(out.sum()), 1.0, abs_tol=1e-15):
        raise SpecError("histogram normalization failed")
    return out


def weighted_centroid_normalized(weight: Any) -> tuple[float, float]:
    """Return (row, col) centroid of pixel centers, normalized to [0,1]."""
    arr = _validate_weight_map(weight)
    total = float(np.sum(arr, dtype=np.float64))
    if total <= 0.0:
        raise SpecError("weighted centroid is undefined for zero total weight")
    height, width = arr.shape
    row_coord = (np.arange(height, dtype=np.float64) + 0.5) / float(height)
    col_coord = (np.arange(width, dtype=np.float64) + 0.5) / float(width)
    row = float(np.sum(arr * row_coord[:, None], dtype=np.float64) / total)
    col = float(np.sum(arr * col_coord[None, :], dtype=np.float64) / total)
    return (_finite_float(row, "centroid_row"), _finite_float(col, "centroid_col"))


def centroid_grid4_cell(weight: Any) -> tuple[int, int]:
    row, col = weighted_centroid_normalized(weight)
    return (min(3, int(math.floor(4.0 * row))), min(3, int(math.floor(4.0 * col))))


def binary_iou(weight_a: Any, weight_b: Any) -> float:
    a = binary_support(weight_a)
    b = binary_support(weight_b)
    if a.shape != b.shape:
        raise SpecError("IoU inputs must have the same shape")
    union = int(np.count_nonzero(a | b))
    if union == 0:
        raise SpecError("binary IoU is undefined when both supports are empty")
    return _finite_float(np.count_nonzero(a & b) / float(union), "binary_iou")


def weight_map_sha256(weight: Any) -> str:
    """Hash shape plus canonical little-endian float64 C-order weight bytes."""
    arr = _validate_weight_map(weight)
    header = f"S48_WEIGHT_MAP_V1\n{arr.shape[0]}\t{arr.shape[1]}\n".encode("ascii")
    canonical = np.array(arr, dtype="<f8", order="C", copy=True)
    canonical[canonical == 0.0] = 0.0  # collapse IEEE-754 negative zero
    payload = canonical.tobytes(order="C")
    return sha256(header + payload).hexdigest()


def _axis_finite_difference(
    depth: np.ndarray, valid: np.ndarray, axis: int
) -> tuple[np.ndarray, np.ndarray]:
    derivative = np.zeros_like(depth, dtype=np.float64)
    derivative_valid = np.zeros_like(valid, dtype=bool)
    if depth.shape[axis] < 2:
        return derivative, derivative_valid

    previous = np.zeros_like(depth, dtype=np.float64)
    following = np.zeros_like(depth, dtype=np.float64)
    previous_valid = np.zeros_like(valid, dtype=bool)
    following_valid = np.zeros_like(valid, dtype=bool)

    if axis == 1:
        previous[:, 1:] = depth[:, :-1]
        previous_valid[:, 1:] = valid[:, :-1]
        following[:, :-1] = depth[:, 1:]
        following_valid[:, :-1] = valid[:, 1:]
    elif axis == 0:
        previous[1:, :] = depth[:-1, :]
        previous_valid[1:, :] = valid[:-1, :]
        following[:-1, :] = depth[1:, :]
        following_valid[:-1, :] = valid[1:, :]
    else:
        raise SpecError("axis must be 0 or 1")

    central = valid & previous_valid & following_valid
    forward = valid & ~previous_valid & following_valid
    backward = valid & previous_valid & ~following_valid
    derivative[central] = (following[central] - previous[central]) / 2.0
    derivative[forward] = following[forward] - depth[forward]
    derivative[backward] = depth[backward] - previous[backward]
    derivative_valid[central | forward | backward] = True
    return derivative, derivative_valid


def metric_depth_gradient(depth: Any) -> tuple[np.ndarray, np.ndarray]:
    """Metric finite-difference gradient magnitude and explicit validity mask."""
    arr = np.asarray(depth, dtype=np.float64)
    if arr.ndim != 2 or arr.size == 0:
        raise SpecError("depth must be a non-empty 2-D array")
    valid_depth = np.isfinite(arr) & (arr > 0.0)
    finite_depth = np.where(valid_depth, arr, 0.0)
    dx, valid_x = _axis_finite_difference(finite_depth, valid_depth, axis=1)
    dy, valid_y = _axis_finite_difference(finite_depth, valid_depth, axis=0)
    valid = valid_depth & valid_x & valid_y
    magnitude = np.zeros_like(finite_depth, dtype=np.float64)
    magnitude[valid] = np.hypot(dx[valid], dy[valid])
    if not np.isfinite(magnitude).all():
        raise SpecError("depth gradient produced a non-finite value")
    return magnitude, valid


def depth_discontinuity_map(
    depth: Any, threshold: float = DEPTH_RELATIVE_BOUNDARY_THRESHOLD
) -> tuple[np.ndarray, np.ndarray]:
    """Return a 4-neighbor metric-depth discontinuity map and depth validity."""
    threshold = _finite_float(threshold, "threshold")
    if threshold < 0.0:
        raise SpecError("threshold must be nonnegative")
    arr = np.asarray(depth, dtype=np.float64)
    if arr.ndim != 2 or arr.size == 0:
        raise SpecError("depth must be a non-empty 2-D array")
    valid = np.isfinite(arr) & (arr > 0.0)
    z = np.where(valid, arr, 0.0)
    boundary = np.zeros_like(valid, dtype=bool)

    pair_valid = valid[:, :-1] & valid[:, 1:]
    rel = np.zeros_like(z[:, :-1], dtype=np.float64)
    denom = np.maximum(np.maximum(z[:, :-1], z[:, 1:]), 1.0e-6)
    rel[pair_valid] = np.abs(z[:, :-1][pair_valid] - z[:, 1:][pair_valid]) / denom[pair_valid]
    hit = pair_valid & (rel > threshold)
    boundary[:, :-1] |= hit
    boundary[:, 1:] |= hit

    pair_valid = valid[:-1, :] & valid[1:, :]
    rel = np.zeros_like(z[:-1, :], dtype=np.float64)
    denom = np.maximum(np.maximum(z[:-1, :], z[1:, :]), 1.0e-6)
    rel[pair_valid] = np.abs(z[:-1, :][pair_valid] - z[1:, :][pair_valid]) / denom[pair_valid]
    hit = pair_valid & (rel > threshold)
    boundary[:-1, :] |= hit
    boundary[1:, :] |= hit
    return boundary, valid


def _window_sum(array: np.ndarray, radius: int) -> np.ndarray:
    if radius < 0 or isinstance(radius, bool):
        raise SpecError("radius must be a nonnegative integer")
    height, width = array.shape
    padded = np.pad(array.astype(np.float64), ((1, 0), (1, 0)), mode="constant")
    integral = np.cumsum(np.cumsum(padded, axis=0), axis=1)
    out = np.zeros((height, width), dtype=np.float64)
    for row in range(height):
        top = max(0, row - radius)
        bottom = min(height, row + radius + 1)
        for col in range(width):
            left = max(0, col - radius)
            right = min(width, col + radius + 1)
            out[row, col] = (
                integral[bottom, right]
                - integral[top, right]
                - integral[bottom, left]
                + integral[top, left]
            )
    return out


def local_boundary_density(
    depth: Any,
    *,
    threshold: float = DEPTH_RELATIVE_BOUNDARY_THRESHOLD,
    radius: int = BOUNDARY_DENSITY_RADIUS,
) -> tuple[np.ndarray, np.ndarray]:
    """5x5-by-default density of valid depth-discontinuity pixels.

    Invalid positions are represented by value 0 and validity False; this
    function never emits NaN as a missing-value sentinel.
    """
    if type(radius) is not int or radius < 0:
        raise SpecError("radius must be a nonnegative integer")
    boundary, valid_depth = depth_discontinuity_map(depth, threshold)
    numerator = _window_sum(boundary, radius)
    denominator = _window_sum(valid_depth, radius)
    valid = denominator > 0.0
    density = np.zeros_like(numerator, dtype=np.float64)
    density[valid] = numerator[valid] / denominator[valid]
    if not np.isfinite(density).all() or np.any(density < 0.0) or np.any(density > 1.0):
        raise SpecError("boundary density produced an invalid value")
    return density, valid


def weighted_quantile_lower(values: Any, weights: Any, probability: float) -> float:
    """Smallest value whose positive-weight empirical CDF reaches probability."""
    probability = _finite_float(probability, "probability")
    if probability < 0.0 or probability > 1.0:
        raise SpecError("probability must lie in [0, 1]")
    value_arr = np.asarray(values, dtype=np.float64).reshape(-1)
    weight_arr = np.asarray(weights, dtype=np.float64).reshape(-1)
    if value_arr.size == 0 or value_arr.shape != weight_arr.shape:
        raise SpecError("values and weights must have the same non-empty shape")
    if not np.isfinite(value_arr).all() or not np.isfinite(weight_arr).all():
        raise SpecError("values and weights must be finite")
    if np.any(weight_arr < 0.0):
        raise SpecError("weights must be nonnegative")
    positive = weight_arr > 0.0
    if not np.any(positive):
        raise SpecError("weighted quantile requires positive total weight")
    value_arr = value_arr[positive]
    weight_arr = weight_arr[positive]
    order = np.argsort(value_arr, kind="stable")
    sorted_values = value_arr[order]
    sorted_weights = weight_arr[order]
    total = float(np.sum(sorted_weights, dtype=np.float64))
    if not math.isfinite(total) or total <= 0.0:
        raise SpecError("weighted quantile total weight is invalid")
    if probability == 0.0:
        return float(sorted_values[0])
    threshold = probability * total
    cumulative = np.cumsum(sorted_weights, dtype=np.float64)
    index = int(np.searchsorted(cumulative, threshold, side="left"))
    index = min(index, sorted_values.size - 1)
    return _finite_float(sorted_values[index], "weighted_quantile")


def type7_quantiles(values: Any, probabilities: Sequence[float] = (0.25, 0.5, 0.75)) -> np.ndarray:
    """R/NumPy type-7 linear quantiles, implemented without version defaults."""
    arr = np.asarray(values, dtype=np.float64).reshape(-1)
    if arr.size == 0 or not np.isfinite(arr).all():
        raise SpecError("quantile population must be non-empty and finite")
    ordered = np.sort(arr, kind="stable")
    output: list[float] = []
    for raw_probability in probabilities:
        probability = _finite_float(raw_probability, "probability")
        if probability < 0.0 or probability > 1.0:
            raise SpecError("probability must lie in [0, 1]")
        location = (ordered.size - 1) * probability
        lower = int(math.floor(location))
        upper = min(lower + 1, ordered.size - 1)
        fraction = location - lower
        value = (1.0 - fraction) * ordered[lower] + fraction * ordered[upper]
        output.append(_finite_float(value, "type7_quantile"))
    return np.asarray(output, dtype=np.float64)


def quartile_stratum(value: Any, cutpoints: Any) -> int:
    """Assign [−inf,Q1), [Q1,Q2), [Q2,Q3), [Q3,+inf).

    A value equal to a cutpoint goes to the higher-index stratum.  Repeated
    cutpoints therefore create explicit empty strata rather than jittering ties.
    """
    value_float = _finite_float(value, "value")
    cuts = np.asarray(cutpoints, dtype=np.float64).reshape(-1)
    if cuts.shape != (3,) or not np.isfinite(cuts).all() or np.any(cuts[1:] < cuts[:-1]):
        raise SpecError("cutpoints must be three finite nondecreasing values")
    return int(np.searchsorted(cuts, value_float, side="right"))


def context_descriptor(
    values: Any,
    valid: Any,
    weight: Any,
    *,
    minimum_valid_weight_fraction: float = CONTEXT_VALID_WEIGHT_FRACTION_MIN,
) -> dict[str, Any]:
    """Freeze one mask-weighted median and its full-target quartile stratum."""
    value_arr = np.asarray(values, dtype=np.float64)
    valid_arr = np.asarray(valid, dtype=bool)
    weight_arr = _validate_weight_map(weight)
    if value_arr.shape != weight_arr.shape or valid_arr.shape != weight_arr.shape:
        raise SpecError("descriptor values, validity, and weight must share shape")
    finite_valid = valid_arr & np.isfinite(value_arr)
    population = value_arr[finite_valid]
    if population.size == 0:
        raise SpecError("descriptor has no finite full-target population")
    total_weight = float(np.sum(weight_arr, dtype=np.float64))
    if total_weight <= 0.0:
        raise SpecError("descriptor support has zero total weight")
    valid_weight = float(np.sum(weight_arr[finite_valid], dtype=np.float64))
    valid_fraction = valid_weight / total_weight
    minimum = _finite_float(minimum_valid_weight_fraction, "minimum_valid_weight_fraction")
    if minimum < 0.0 or minimum > 1.0:
        raise SpecError("minimum valid weight fraction must lie in [0, 1]")
    if valid_fraction < minimum:
        raise SpecError("descriptor support lacks the required valid-weight coverage")
    positive_overlap = finite_valid & (weight_arr > 0.0)
    summary = weighted_quantile_lower(
        value_arr[positive_overlap], weight_arr[positive_overlap], 0.5
    )
    cutpoints = type7_quantiles(population)
    return {
        "summary": summary,
        "cutpoints": cutpoints,
        "stratum": quartile_stratum(summary, cutpoints),
        "valid_weight_fraction": _finite_float(valid_fraction, "valid_weight_fraction"),
        "population_count": int(population.size),
    }


def mask_context_strata(weight: Any, depth: Any, confidence: Any) -> dict[str, dict[str, Any]]:
    """Return the four frozen pre-treatment context descriptors for one mask."""
    weight_arr = _validate_weight_map(weight)
    depth_arr = np.asarray(depth, dtype=np.float64)
    confidence_arr = np.asarray(confidence, dtype=np.float64)
    if depth_arr.shape != weight_arr.shape or confidence_arr.shape != weight_arr.shape:
        raise SpecError("weight, depth, and confidence must share shape")
    depth_valid = np.isfinite(depth_arr) & (depth_arr > 0.0)
    gradient, gradient_valid = metric_depth_gradient(depth_arr)
    boundary_density, boundary_valid = local_boundary_density(depth_arr)
    confidence_valid = (
        depth_valid
        & np.isfinite(confidence_arr)
        & (confidence_arr >= 0.0)
        & (confidence_arr <= 1.0)
    )
    return {
        "visible_metric_depth": context_descriptor(depth_arr, depth_valid, weight_arr),
        "metric_depth_gradient": context_descriptor(gradient, gradient_valid, weight_arr),
        "projection_confidence": context_descriptor(
            np.where(confidence_valid, confidence_arr, 0.0), confidence_valid, weight_arr
        ),
        "local_depth_boundary_density": context_descriptor(
            boundary_density, boundary_valid, weight_arr
        ),
    }


def mask_caliper_metrics(
    reference_weight: Any,
    candidate_weight: Any,
    depth: Any,
    confidence: Any,
) -> MaskCaliperMetrics:
    """Compute every deterministic pre-output mask matching quantity."""
    reference = _validate_weight_map(reference_weight, "reference_weight")
    candidate = _validate_weight_map(candidate_weight, "candidate_weight")
    if candidate.shape != reference.shape:
        raise SpecError("reference and candidate weight maps must share shape")
    reference_area = float(np.sum(reference, dtype=np.float64))
    candidate_area = float(np.sum(candidate, dtype=np.float64))
    if reference_area <= 0.0 or candidate_area <= 0.0:
        raise SpecError("mask calipers require non-empty positive-weight supports")
    area_error = abs(candidate_area - reference_area) / reference_area
    reference_perimeter = normalized_perimeter(reference)
    candidate_perimeter = normalized_perimeter(candidate)
    perimeter_error = abs(candidate_perimeter - reference_perimeter) / reference_perimeter
    reference_centroid = weighted_centroid_normalized(reference)
    candidate_centroid = weighted_centroid_normalized(candidate)
    height, width = reference.shape
    centroid_distance = math.hypot(
        (candidate_centroid[0] - reference_centroid[0]) * height,
        (candidate_centroid[1] - reference_centroid[1]) * width,
    )
    histogram_l1 = float(
        np.sum(
            np.abs(
                positive_weight_histogram(candidate) - positive_weight_histogram(reference)
            ),
            dtype=np.float64,
        )
    )
    reference_context = mask_context_strata(reference, depth, confidence)
    candidate_context = mask_context_strata(candidate, depth, confidence)
    same_context = all(
        reference_context[name]["stratum"] == candidate_context[name]["stratum"]
        for name in reference_context
    )
    return MaskCaliperMetrics(
        _finite_float(area_error, "weighted_area_relative_error"),
        connected_components4(reference),
        connected_components4(candidate),
        _finite_float(perimeter_error, "normalized_perimeter_relative_error"),
        centroid_grid4_cell(reference) == centroid_grid4_cell(candidate),
        binary_iou(reference, candidate),
        _finite_float(histogram_l1, "positive_weight_histogram_l1"),
        bool(same_context),
        _finite_float(centroid_distance, "centroid_distance_pixels"),
    )


def mask_caliper_decision(metrics: MaskCaliperMetrics) -> tuple[bool, tuple[str, ...]]:
    failures: list[str] = []
    numeric = (
        metrics.weighted_area_relative_error,
        metrics.normalized_perimeter_relative_error,
        metrics.binary_iou,
        metrics.positive_weight_histogram_l1,
        metrics.centroid_distance_pixels,
    )
    if not all(math.isfinite(float(value)) for value in numeric):
        raise SpecError("all mask caliper metrics must be finite")
    if (
        type(metrics.reference_component_count) is not int
        or type(metrics.candidate_component_count) is not int
        or metrics.reference_component_count < 1
        or metrics.candidate_component_count < 1
    ):
        raise SpecError("mask caliper component counts must be positive integers")
    if not all(
        isinstance(value, (bool, np.bool_))
        for value in (metrics.same_centroid_grid4_cell, metrics.same_context_strata)
    ):
        raise SpecError("mask caliper equality flags must be boolean")
    if (
        metrics.weighted_area_relative_error < 0.0
        or metrics.normalized_perimeter_relative_error < 0.0
        or metrics.binary_iou < 0.0
        or metrics.binary_iou > 1.0
        or metrics.positive_weight_histogram_l1 < 0.0
        or metrics.positive_weight_histogram_l1 > 2.0
        or metrics.centroid_distance_pixels < 0.0
    ):
        raise SpecError("mask caliper metric lies outside its mathematical domain")
    if metrics.weighted_area_relative_error > 0.02:
        failures.append("WEIGHTED_AREA_RELATIVE_ERROR_ABOVE_MAX")
    if metrics.reference_component_count != metrics.candidate_component_count:
        failures.append("COMPONENT_COUNT_MISMATCH")
    if metrics.normalized_perimeter_relative_error > 0.10:
        failures.append("NORMALIZED_PERIMETER_RELATIVE_ERROR_ABOVE_MAX")
    if not metrics.same_centroid_grid4_cell:
        failures.append("CENTROID_GRID4_CELL_MISMATCH")
    if metrics.binary_iou > 0.10:
        failures.append("BINARY_IOU_ABOVE_MAX")
    if metrics.positive_weight_histogram_l1 > 0.05:
        failures.append("POSITIVE_WEIGHT_HISTOGRAM_L1_ABOVE_MAX")
    if not metrics.same_context_strata:
        failures.append("CONTEXT_STRATUM_MISMATCH")
    return (not failures, tuple(failures))


def _blur_binomial5_reflect101(rgb: np.ndarray) -> np.ndarray:
    if rgb.shape[0] < 5 or rgb.shape[1] < 5:
        raise SpecError("texture edit requires image height and width at least 5")
    horizontal_pad = np.pad(rgb, ((0, 0), (2, 2), (0, 0)), mode="reflect")
    horizontal = np.zeros_like(rgb, dtype=np.float64)
    for offset, coefficient in enumerate(TEXTURE_KERNEL):
        horizontal += coefficient * horizontal_pad[:, offset : offset + rgb.shape[1], :]
    vertical_pad = np.pad(horizontal, ((2, 2), (0, 0), (0, 0)), mode="reflect")
    output = np.zeros_like(rgb, dtype=np.float64)
    for offset, coefficient in enumerate(TEXTURE_KERNEL):
        output += coefficient * vertical_pad[offset : offset + rgb.shape[0], :, :]
    return output


def edit_preclip(rgb: Any, family: str, sign: int, dose: Any) -> np.ndarray:
    """Return the exact unclipped source edit in float64 sRGB."""
    arr = _validate_rgb(rgb)
    sign = _validate_sign(sign)
    dose_float = _finite_float(dose, "dose")
    if family == "exposure_log_gain":
        if dose_float not in EXPOSURE_DOSES:
            raise SpecError("dose is not in the frozen exposure ladder")
        output = arr * math.pow(2.0, sign * dose_float)
    elif family == "texture_highpass":
        if dose_float not in TEXTURE_DOSES:
            raise SpecError("dose is not in the frozen texture ladder")
        lowpass = _blur_binomial5_reflect101(arr)
        output = arr + sign * dose_float * (arr - lowpass)
    else:
        raise SpecError("unknown edit family")
    if not np.isfinite(output).all():
        raise SpecError("edit produced a non-finite value")
    return output


def apply_source_edit(rgb: Any, family: str, sign: int, dose: Any) -> np.ndarray:
    return np.clip(edit_preclip(rgb, family, sign, dose), 0.0, 1.0)


def _gray_bt601(rgb: np.ndarray) -> np.ndarray:
    return 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]


def _conv3_reflect101(gray: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    if gray.shape[0] < 3 or gray.shape[1] < 3:
        raise SpecError("3x3 convolution requires height and width at least 3")
    padded = np.pad(gray, ((1, 1), (1, 1)), mode="reflect")
    output = np.zeros_like(gray, dtype=np.float64)
    for row in range(3):
        for col in range(3):
            output += kernel[row, col] * padded[row : row + gray.shape[0], col : col + gray.shape[1]]
    return output


def sobel_edge_support(rgb: Any) -> np.ndarray:
    arr = _validate_rgb(rgb)
    gray = _gray_bt601(arr)
    kernel_x = np.asarray(
        [[-1.0, 0.0, 1.0], [-2.0, 0.0, 2.0], [-1.0, 0.0, 1.0]], dtype=np.float64
    ) / 8.0
    kernel_y = kernel_x.T
    grad_x = _conv3_reflect101(gray, kernel_x)
    grad_y = _conv3_reflect101(gray, kernel_y)
    magnitude = np.hypot(grad_x, grad_y)
    return magnitude >= SOBEL_EDGE_THRESHOLD


def edge_support_iou(rgb_a: Any, rgb_b: Any) -> float:
    edge_a = sobel_edge_support(rgb_a)
    edge_b = sobel_edge_support(rgb_b)
    if edge_a.shape != edge_b.shape:
        raise SpecError("edge IoU inputs must share shape")
    union = int(np.count_nonzero(edge_a | edge_b))
    if union == 0:
        return 1.0
    return _finite_float(np.count_nonzero(edge_a & edge_b) / float(union), "edge_iou")


def source_edit_metrics(
    original_rgb: Any,
    edited_rgb: Any,
    preclip_rgb: Any,
    *,
    clip_cosine: Any,
    lpips: Any,
) -> SourceEditMetrics:
    original = _validate_rgb(original_rgb, name="original_rgb")
    edited = _validate_rgb(edited_rgb, name="edited_rgb")
    preclip = np.asarray(preclip_rgb, dtype=np.float64)
    if edited.shape != original.shape or preclip.shape != original.shape:
        raise SpecError("original, edited, and preclip RGB arrays must share shape")
    if not np.isfinite(preclip).all():
        raise SpecError("preclip RGB contains a non-finite value")
    mad = float(np.mean(np.abs(edited - original), dtype=np.float64))
    clipped = float(np.mean((preclip < 0.0) | (preclip > 1.0), dtype=np.float64))
    return SourceEditMetrics(
        _finite_float(mad, "mean_absolute_rgb_difference"),
        _finite_float(clipped, "clipped_channel_fraction"),
        edge_support_iou(original, edited),
        _finite_float(clip_cosine, "clip_cosine"),
        _finite_float(lpips, "lpips"),
    )


def source_edit_gate(metrics: SourceEditMetrics) -> tuple[bool, tuple[str, ...]]:
    values = (
        metrics.mean_absolute_rgb_difference,
        metrics.clipped_channel_fraction,
        metrics.edge_iou,
        metrics.clip_cosine,
        metrics.lpips,
    )
    if not all(math.isfinite(float(value)) for value in values):
        raise SpecError("all source edit metrics must be finite")
    if (
        metrics.mean_absolute_rgb_difference < 0.0
        or not 0.0 <= metrics.clipped_channel_fraction <= 1.0
        or not 0.0 <= metrics.edge_iou <= 1.0
        or not -1.0 <= metrics.clip_cosine <= 1.0
        or metrics.lpips < 0.0
    ):
        raise SpecError("source edit metric lies outside its mathematical domain")
    failures: list[str] = []
    if metrics.mean_absolute_rgb_difference < SOURCE_MAD_MIN:
        failures.append("MAD_BELOW_MIN")
    if metrics.mean_absolute_rgb_difference > SOURCE_MAD_MAX:
        failures.append("MAD_ABOVE_MAX")
    if metrics.clipped_channel_fraction > SOURCE_CLIPPED_CHANNEL_FRACTION_MAX:
        failures.append("CLIPPED_FRACTION_ABOVE_MAX")
    if metrics.edge_iou < SOURCE_EDGE_IOU_MIN:
        failures.append("EDGE_IOU_BELOW_MIN")
    if metrics.clip_cosine < SOURCE_CLIP_COSINE_MIN:
        failures.append("CLIP_COSINE_BELOW_MIN")
    if metrics.lpips > SOURCE_LPIPS_MAX:
        failures.append("LPIPS_ABOVE_MAX")
    return (not failures, tuple(failures))


def select_minimum_source_dose(
    rgb: Any,
    family: str,
    external_semantic_metrics: Mapping[tuple[float, int], Mapping[str, Any]],
) -> tuple[float, dict[int, SourceEditMetrics]]:
    """Choose the first dose for which both signs pass every source-only gate.

    CLIP cosine and LPIPS are supplied by a separately bound implementation;
    this function refuses missing values rather than guessing them.
    """
    arr = _validate_rgb(rgb)
    doses = EXPOSURE_DOSES if family == "exposure_log_gain" else TEXTURE_DOSES
    if family not in ("exposure_log_gain", "texture_highpass"):
        raise SpecError("unknown edit family")
    for dose in doses:
        by_sign: dict[int, SourceEditMetrics] = {}
        both_pass = True
        for sign in (-1, 1):
            key = (dose, sign)
            if key not in external_semantic_metrics:
                raise SpecError(f"missing external semantic metrics for dose={dose}, sign={sign}")
            external = external_semantic_metrics[key]
            if set(external) != {"clip_cosine", "lpips"}:
                raise SpecError("external semantic metric record must contain only clip_cosine and lpips")
            preclip = edit_preclip(arr, family, sign, dose)
            edited = np.clip(preclip, 0.0, 1.0)
            metrics = source_edit_metrics(arr, edited, preclip, **external)
            by_sign[sign] = metrics
            if not source_edit_gate(metrics)[0]:
                both_pass = False
        if both_pass:
            return (dose, by_sign)
    raise SpecError("NO_DOSE_PASSES_BOTH_SIGNS")


def _normalized_patch(patch: np.ndarray) -> tuple[np.ndarray, float]:
    centered = patch - float(np.mean(patch, dtype=np.float64))
    rms = math.sqrt(float(np.mean(centered * centered, dtype=np.float64)))
    if not math.isfinite(rms):
        raise SpecError("patch RMS is non-finite")
    return centered / (rms + EPS), rms


def _best_patch_location(
    source_gray: np.ndarray,
    target_gray: np.ndarray,
    source_row: int,
    source_col: int,
    target_center_row: int,
    target_center_col: int,
) -> tuple[int, int, float] | None:
    radius = PATCH_RADIUS
    source_patch = source_gray[
        source_row - radius : source_row + radius + 1,
        source_col - radius : source_col + radius + 1,
    ]
    normalized_source, source_rms = _normalized_patch(source_patch)
    if source_rms < PATCH_MIN_RMS:
        return None
    best: tuple[int, int, float] | None = None
    for delta_row in range(-PATCH_SEARCH_RADIUS, PATCH_SEARCH_RADIUS + 1):
        row = target_center_row + delta_row
        if row - radius < 0 or row + radius >= target_gray.shape[0]:
            continue
        for delta_col in range(-PATCH_SEARCH_RADIUS, PATCH_SEARCH_RADIUS + 1):
            col = target_center_col + delta_col
            if col - radius < 0 or col + radius >= target_gray.shape[1]:
                continue
            target_patch = target_gray[
                row - radius : row + radius + 1,
                col - radius : col + radius + 1,
            ]
            normalized_target, target_rms = _normalized_patch(target_patch)
            if target_rms < PATCH_MIN_RMS:
                continue
            score = float(np.mean((normalized_source - normalized_target) ** 2, dtype=np.float64))
            if best is None or score < best[2]:
                best = (row, col, score)
    if best is None or best[2] > PATCH_MAX_NORMALIZED_SSD:
        return None
    return best


def patch_displacement_metrics(rgb_reference: Any, rgb_candidate: Any) -> PatchDisplacementMetrics:
    """Deterministic mutual grid-patch displacement on native RGB frames."""
    reference = _validate_rgb(rgb_reference, native=True, name="rgb_reference")
    candidate = _validate_rgb(rgb_candidate, native=True, name="rgb_candidate")
    ref_gray = _gray_bt601(reference)
    cand_gray = _gray_bt601(candidate)
    displacements: list[float] = []
    for row in range(PATCH_GRID_OFFSET, NATIVE_HEIGHT - PATCH_GRID_OFFSET, PATCH_GRID_STRIDE):
        for col in range(PATCH_GRID_OFFSET, NATIVE_WIDTH - PATCH_GRID_OFFSET, PATCH_GRID_STRIDE):
            forward = _best_patch_location(ref_gray, cand_gray, row, col, row, col)
            if forward is None:
                continue
            candidate_row, candidate_col, _ = forward
            reverse = _best_patch_location(
                cand_gray,
                ref_gray,
                candidate_row,
                candidate_col,
                candidate_row,
                candidate_col,
            )
            if reverse is None or reverse[0] != row or reverse[1] != col:
                continue
            displacement = math.hypot(candidate_row - row, candidate_col - col)
            displacements.append(_finite_float(displacement, "displacement"))
    if not displacements:
        return PatchDisplacementMetrics(0, 0.0, 0.0)
    ordered = np.sort(np.asarray(displacements, dtype=np.float64), kind="stable")
    median, p95 = type7_quantiles(ordered, probabilities=(0.5, 0.95))
    return PatchDisplacementMetrics(len(displacements), float(median), float(p95))


def outside_brightness_difference(rgb_reference: Any, rgb_candidate: Any, support: Any) -> float:
    reference = _validate_rgb(rgb_reference, native=True, name="rgb_reference")
    candidate = _validate_rgb(rgb_candidate, native=True, name="rgb_candidate")
    weight = _validate_weight_map(support, "support")
    if weight.shape != reference.shape[:2] or candidate.shape != reference.shape:
        raise SpecError("RGB and support shapes are inconsistent")
    outside = weight == 0.0
    if not np.any(outside):
        raise SpecError("outside brightness is undefined for full-screen support")
    difference = np.abs(_gray_bt601(candidate)[outside] - _gray_bt601(reference)[outside])
    return _finite_float(np.mean(difference, dtype=np.float64), "outside_brightness_difference")


def laplacian_sharpness(rgb: Any) -> float:
    arr = _validate_rgb(rgb, native=True)
    gray = _gray_bt601(arr)
    kernel = np.asarray([[0.0, 1.0, 0.0], [1.0, -4.0, 1.0], [0.0, 1.0, 0.0]])
    response = _conv3_reflect101(gray, kernel)
    return _finite_float(np.var(response, dtype=np.float64), "laplacian_sharpness")


def saturation_fraction(rgb: Any) -> float:
    arr = _validate_rgb(rgb, native=True)
    saturated = np.any((arr == 0.0) | (arr == 1.0), axis=2)
    return _finite_float(np.mean(saturated, dtype=np.float64), "saturation_fraction")


def tear_excess(rgb_reference: Any, rgb_candidate: Any) -> float:
    reference = _validate_rgb(rgb_reference, native=True, name="rgb_reference")
    candidate = _validate_rgb(rgb_candidate, native=True, name="rgb_candidate")
    ref_gray = _gray_bt601(reference)
    cand_gray = _gray_bt601(candidate)
    ref_rows = np.mean(np.abs(np.diff(ref_gray, axis=0)), axis=1, dtype=np.float64)
    cand_rows = np.mean(np.abs(np.diff(cand_gray, axis=0)), axis=1, dtype=np.float64)
    ref_cols = np.mean(np.abs(np.diff(ref_gray, axis=1)), axis=0, dtype=np.float64)
    cand_cols = np.mean(np.abs(np.diff(cand_gray, axis=1)), axis=0, dtype=np.float64)
    row_excess = float(np.max(cand_rows - ref_rows, initial=0.0))
    col_excess = float(np.max(cand_cols - ref_cols, initial=0.0))
    return _finite_float(max(0.0, row_excess, col_excess), "tear_excess")


def arm_guard_metrics(rgb_reference: Any, rgb_candidate: Any, support: Any) -> ArmGuardMetrics:
    reference = _validate_rgb(rgb_reference, native=True, name="rgb_reference")
    candidate = _validate_rgb(rgb_candidate, native=True, name="rgb_candidate")
    displacement = patch_displacement_metrics(reference, candidate)
    reference_sharpness = laplacian_sharpness(reference)
    if reference_sharpness <= EPS:
        raise SpecError("sharpness ratio is undefined for a near-zero-sharpness reference")
    candidate_sharpness = laplacian_sharpness(candidate)
    sharpness_deviation = abs(candidate_sharpness / reference_sharpness - 1.0)
    saturation_increase_pp = 100.0 * (
        saturation_fraction(candidate) - saturation_fraction(reference)
    )
    return ArmGuardMetrics(
        displacement.match_count,
        displacement.median_px,
        displacement.p95_px,
        outside_brightness_difference(reference, candidate, support),
        _finite_float(sharpness_deviation, "sharpness_ratio_deviation"),
        _finite_float(saturation_increase_pp, "saturation_increase_pp"),
        tear_excess(reference, candidate),
    )


def _validate_arm_guard_metric_domains(metrics: ArmGuardMetrics) -> None:
    if type(metrics.match_count) is not int or metrics.match_count < 0:
        raise SpecError("arm guard match_count must be a nonnegative integer")
    values = (
        metrics.median_displacement_px,
        metrics.p95_displacement_px,
        metrics.outside_brightness_difference,
        metrics.sharpness_ratio_deviation,
        metrics.saturation_increase_pp,
        metrics.tear_excess,
    )
    if not all(math.isfinite(float(value)) for value in values):
        raise SpecError("arm guard inputs must be finite")
    if (
        metrics.median_displacement_px < 0.0
        or metrics.p95_displacement_px < 0.0
        or metrics.outside_brightness_difference < 0.0
        or metrics.outside_brightness_difference > 1.0
        or metrics.sharpness_ratio_deviation < 0.0
        or metrics.saturation_increase_pp < -100.0
        or metrics.saturation_increase_pp > 100.0
        or metrics.tear_excess < 0.0
        or metrics.tear_excess > 1.0
    ):
        raise SpecError("arm guard metric lies outside its mathematical domain")


def replay_guard_floors(
    metrics: Sequence[ArmGuardMetrics], *, replay_instance_count: int
) -> ArmGuardFloors:
    if type(replay_instance_count) is not int or replay_instance_count < 4:
        raise SpecError("replay_instance_count must be an integer at least 4")
    expected_pair_count = replay_instance_count * (replay_instance_count - 1) // 2
    if len(metrics) != expected_pair_count:
        raise SpecError(
            f"expected {expected_pair_count} unordered replay-pair records, got {len(metrics)}"
        )
    for record in metrics:
        _validate_arm_guard_metric_domains(record)
        if record.match_count < PATCH_MIN_MUTUAL_MATCHES:
            raise SpecError("every replay pair must pass the mutual-match count floor")
    numeric_fields = (
        "median_displacement_px",
        "p95_displacement_px",
        "outside_brightness_difference",
        "sharpness_ratio_deviation",
        "saturation_increase_pp",
        "tear_excess",
    )
    maxima: dict[str, float] = {}
    for field in numeric_fields:
        values = [_finite_float(getattr(record, field), field) for record in metrics]
        maxima[field] = max(values)
    return ArmGuardFloors(**maxima)


def arm_guard_decision(
    metrics: ArmGuardMetrics, replay_floors: ArmGuardFloors
) -> tuple[bool, tuple[str, ...]]:
    _validate_arm_guard_metric_domains(metrics)
    failures: list[str] = []
    if metrics.match_count < PATCH_MIN_MUTUAL_MATCHES:
        failures.append("TOO_FEW_MUTUAL_PATCH_MATCHES")
    comparisons = (
        (
            metrics.median_displacement_px,
            max(GUARD_MEDIAN_FLOOR_PX, replay_floors.median_displacement_px),
            "MEDIAN_DISPLACEMENT_ABOVE_MAX",
        ),
        (
            metrics.p95_displacement_px,
            max(GUARD_P95_FLOOR_PX, replay_floors.p95_displacement_px),
            "P95_DISPLACEMENT_ABOVE_MAX",
        ),
        (
            metrics.outside_brightness_difference,
            max(GUARD_BRIGHTNESS_FLOOR, replay_floors.outside_brightness_difference),
            "OUTSIDE_BRIGHTNESS_ABOVE_MAX",
        ),
        (
            metrics.sharpness_ratio_deviation,
            max(GUARD_SHARPNESS_RATIO_FLOOR, replay_floors.sharpness_ratio_deviation),
            "SHARPNESS_RATIO_DEVIATION_ABOVE_MAX",
        ),
        (
            metrics.saturation_increase_pp,
            max(GUARD_SATURATION_FLOOR_PP, replay_floors.saturation_increase_pp),
            "SATURATION_INCREASE_ABOVE_MAX",
        ),
        (
            metrics.tear_excess,
            max(GUARD_TEAR_FLOOR, replay_floors.tear_excess),
            "TEAR_EXCESS_ABOVE_MAX",
        ),
    )
    for value, threshold, code in comparisons:
        if not math.isfinite(float(value)) or not math.isfinite(float(threshold)):
            raise SpecError("arm guard inputs must be finite")
        if value > threshold:
            failures.append(code)
    return (not failures, tuple(failures))


_ROSTER_BOOLEAN_FIELDS = (
    "active",
    "selected",
    "is_target",
    "is_reference",
    "provenance_complete",
    "artifacts_complete",
    "renderable_all_targets",
)


def build_unselected_source_roster(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Produce the complete deterministic all-record flow and eligible order."""
    normalized: list[dict[str, Any]] = []
    seen_source_ids: set[str] = set()
    for raw in records:
        required = {"insertion_event", "source_id", "file_sha256", *_ROSTER_BOOLEAN_FIELDS}
        if set(raw) != required:
            missing = sorted(required - set(raw))
            extra = sorted(set(raw) - required)
            raise SpecError(f"roster record schema mismatch; missing={missing}, extra={extra}")
        insertion_event = raw["insertion_event"]
        if type(insertion_event) is not int or insertion_event < 0:
            raise SpecError("insertion_event must be a nonnegative integer")
        source_id = raw["source_id"]
        if (
            type(source_id) is not str
            or not source_id
            or any(ord(character) < 32 or ord(character) == 127 for character in source_id)
        ):
            raise SpecError("source_id must be a non-empty string without ASCII control characters")
        if source_id in seen_source_ids:
            raise SpecError("source_id must be unique in the complete pre-selection roster")
        seen_source_ids.add(source_id)
        digest = raw["file_sha256"]
        if type(digest) is not str or _SHA256_RE.fullmatch(digest) is None:
            raise SpecError("file_sha256 must be 64 lowercase hexadecimal characters")
        booleans = {field: _validate_boolean(raw[field], field) for field in _ROSTER_BOOLEAN_FIELDS}

        reasons: list[str] = []
        if not booleans["active"]:
            reasons.append("INACTIVE_OR_TOMBSTONED")
        if booleans["selected"]:
            reasons.append("SELECTED_IN_ORDINARY_RUN")
        if booleans["is_target"]:
            reasons.append("TARGET_OBSERVATION")
        if booleans["is_reference"]:
            reasons.append("HELD_OUT_REFERENCE")
        if not booleans["provenance_complete"]:
            reasons.append("PROVENANCE_INCOMPLETE")
        if not booleans["artifacts_complete"]:
            reasons.append("SCIENTIFIC_ARTIFACTS_INCOMPLETE")
        if not booleans["renderable_all_targets"]:
            reasons.append("NOT_RENDERABLE_FOR_ALL_PREREGISTERED_TARGETS")

        record = {
            "insertion_event": insertion_event,
            "source_id": source_id,
            "file_sha256": digest,
            **booleans,
            "eligible_unselected": not reasons,
            "exclusion_reasons": tuple(reasons),
        }
        normalized.append(record)

    normalized.sort(
        key=lambda record: (
            record["insertion_event"],
            record["source_id"].encode("utf-8"),
            record["file_sha256"],
        )
    )
    eligible = [record for record in normalized if record["eligible_unselected"]]
    canonical_lines = []
    for record in normalized:
        reasons = ",".join(record["exclusion_reasons"])
        canonical_lines.append(
            "\t".join(
                (
                    str(record["insertion_event"]),
                    record["source_id"],
                    record["file_sha256"],
                    "1" if record["eligible_unselected"] else "0",
                    reasons,
                )
            )
        )
    canonical_bytes = ("\n".join(canonical_lines) + ("\n" if canonical_lines else "")).encode("utf-8")
    return {
        "all_records": tuple(normalized),
        "eligible_records": tuple(eligible),
        "eligible_source_ids": tuple(record["source_id"] for record in eligible),
        "canonical_sha256": sha256(canonical_bytes).hexdigest(),
    }


__all__ = [name for name in globals() if not name.startswith("_")]
