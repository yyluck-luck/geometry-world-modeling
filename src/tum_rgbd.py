"""Small, auditable TUM RGB-D reader; no learned depth or confidence is implied.

Conventions follow the official file-format documentation:
https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats
Registered PNG depth / 5000 is optical Z in metres; 0 is missing. The dataset
already applies Freiburg depth scale correction. ROS-default intrinsics and no
additional undistortion are used. Colour and depth remain different timestamps.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
from scipy.spatial.transform import Rotation, Slerp


@dataclass(frozen=True)
class CameraIntrinsics:
    fx: float = 525.0
    fy: float = 525.0
    cx: float = 319.5
    cy: float = 239.5
    width: int = 640
    height: int = 480

    def __post_init__(self):
        if not np.isfinite([self.fx, self.fy, self.cx, self.cy]).all():
            raise ValueError("Camera intrinsics must be finite")
        if min(self.fx, self.fy, self.width, self.height) <= 0:
            raise ValueError("Focal lengths and image dimensions must be positive")

    @property
    def K(self) -> np.ndarray:
        return np.array([[self.fx, 0, self.cx], [0, self.fy, self.cy], [0, 0, 1]], dtype=float)


DEFAULT_INTRINSICS = CameraIntrinsics()


@dataclass(frozen=True)
class TimestampEntry:
    timestamp: float
    path: str


@dataclass(frozen=True)
class RGBDMatch:
    rgb: TimestampEntry
    depth: TimestampEntry

    @property
    def rgb_timestamp(self) -> float:
        return self.rgb.timestamp

    @property
    def depth_timestamp(self) -> float:
        return self.depth.timestamp

    @property
    def offset_seconds(self) -> float:
        """Signed RGB timestamp minus depth timestamp."""
        return self.rgb.timestamp - self.depth.timestamp


@dataclass(frozen=True)
class PoseInterpolation:
    c2w: np.ndarray
    timestamp: float
    lower_timestamp: float
    upper_timestamp: float
    alpha: float

    @property
    def gap_seconds(self) -> float:
        return self.upper_timestamp - self.lower_timestamp


@dataclass(frozen=True)
class PoseTrajectory:
    timestamps: np.ndarray
    translations: np.ndarray
    quaternions_xyzw: np.ndarray

    def __post_init__(self):
        t = np.asarray(self.timestamps, dtype=np.float64)
        xyz = np.asarray(self.translations, dtype=np.float64)
        quat = np.asarray(self.quaternions_xyzw, dtype=np.float64)
        if t.ndim != 1 or len(t) == 0 or xyz.shape != (len(t), 3) or quat.shape != (len(t), 4):
            raise ValueError("Trajectory requires N timestamps, N x 3 translations, N x 4 xyzw quaternions")
        if not all(np.isfinite(a).all() for a in (t, xyz, quat)) or np.any(np.diff(t) <= 0):
            raise ValueError("Trajectory must be finite and timestamps strictly increasing")
        norms = np.linalg.norm(quat, axis=1)
        if np.any(norms < 1e-12):
            raise ValueError("Quaternion has zero norm")
        object.__setattr__(self, "timestamps", t.copy())
        object.__setattr__(self, "translations", xyz.copy())
        object.__setattr__(self, "quaternions_xyzw", quat / norms[:, None])

    def interpolate(self, timestamp: float, max_gap_seconds: float | None = None) -> PoseInterpolation:
        """Translation lerp and shortest-path quaternion SLERP; never extrapolate.

        Exact endpoints are valid. An optional maximum bracket gap rejects
        interpolation across tracking gaps. Exact samples do not span a gap.
        """
        t = float(timestamp)
        if not np.isfinite(t) or t < self.timestamps[0] or t > self.timestamps[-1]:
            raise ValueError("Requested timestamp is outside trajectory support")
        if max_gap_seconds is not None and (not np.isfinite(max_gap_seconds) or max_gap_seconds <= 0):
            raise ValueError("max_gap_seconds must be positive and finite")
        hi = int(np.searchsorted(self.timestamps, t))
        if self.timestamps[hi] == t:
            lo = hi
            alpha = 0.0
            rotation = Rotation.from_quat(self.quaternions_xyzw[lo])
            position = self.translations[lo]
        else:
            lo = hi - 1
            gap = self.timestamps[hi] - self.timestamps[lo]
            if max_gap_seconds is not None and gap > max_gap_seconds:
                raise ValueError(f"Trajectory bracket gap {gap:.6f}s exceeds limit")
            alpha = float((t - self.timestamps[lo]) / gap)
            position = (1 - alpha) * self.translations[lo] + alpha * self.translations[hi]
            # Work in normalized [0, 1] time to avoid large Unix epoch conditioning.
            rotation = Slerp([0., 1.], Rotation.from_quat(self.quaternions_xyzw[[lo, hi]]))(alpha)
        matrix = np.eye(4)
        matrix[:3, :3] = rotation.as_matrix()
        matrix[:3, 3] = position
        return PoseInterpolation(matrix, t, float(self.timestamps[lo]), float(self.timestamps[hi]), alpha)

    def pose_at(self, timestamp: float, max_gap_seconds: float | None = None) -> np.ndarray:
        return self.interpolate(timestamp, max_gap_seconds).c2w


def _rows(path: str | Path):
    for lineno, line in enumerate(Path(path).read_text().splitlines(), 1):
        line = line.partition("#")[0].strip()
        if line:
            yield lineno, line.split()


def read_timestamp_file(path: str | Path) -> list[TimestampEntry]:
    """Read a TUM rgb.txt/depth.txt; reject duplicate/non-finite timestamps."""
    rows = []
    for lineno, fields in _rows(path):
        if len(fields) != 2:
            raise ValueError(f"{path}:{lineno}: expected timestamp and image path")
        rows.append(TimestampEntry(float(fields[0]), fields[1]))
    rows.sort(key=lambda row: row.timestamp)
    _validate_entries(rows)
    return rows


def _validate_entries(rows: Sequence[TimestampEntry]):
    stamps = [row.timestamp for row in rows]
    if not np.isfinite(stamps).all() or len(set(stamps)) != len(stamps):
        raise ValueError("Image timestamps must be finite and unique")


def read_trajectory(path: str | Path) -> PoseTrajectory:
    """Read TUM timestamp tx ty tz qx qy qz qw, sorted by timestamp."""
    rows = []
    for lineno, fields in _rows(path):
        if len(fields) != 8:
            raise ValueError(f"{path}:{lineno}: expected 8 trajectory columns")
        rows.append([float(value) for value in fields])
    if not rows:
        raise ValueError("Trajectory file contains no poses")
    array = np.array(sorted(rows, key=lambda row: row[0]), dtype=np.float64)
    return PoseTrajectory(array[:, 0], array[:, 1:4], array[:, 4:8])


def associate_rgb_depth(rgb: Sequence[TimestampEntry], depth: Sequence[TimestampEntry],
                        max_difference: float = 0.02) -> list[RGBDMatch]:
    """Unique greedy matching, like TUM associate.py (not global assignment).

    Enumerate pairs with |t_rgb - t_depth| strictly below max_difference;
    sort by (absolute time difference, RGB time, depth time); accept pairs only
    if neither frame has been used. Return in RGB-time order. Equal-difference
    ties are deterministic. The maximum accepted match count is not guaranteed.
    """
    if not np.isfinite(max_difference) or max_difference <= 0:
        raise ValueError("max_difference must be positive and finite")
    _validate_entries(rgb)
    _validate_entries(depth)
    rgb = sorted(rgb, key=lambda row: row.timestamp)
    depth = sorted(depth, key=lambda row: row.timestamp)
    dt = np.array([row.timestamp for row in depth])
    candidates = []
    for i, row in enumerate(rgb):
        lo = np.searchsorted(dt, row.timestamp - max_difference, side="left")
        hi = np.searchsorted(dt, row.timestamp + max_difference, side="right")
        for j in range(int(lo), int(hi)):
            difference = abs(row.timestamp - depth[j].timestamp)
            if difference < max_difference:
                candidates.append((difference, row.timestamp, depth[j].timestamp, i, j))
    used_rgb, used_depth, matches = set(), set(), []
    for _, _, _, i, j in sorted(candidates):
        if i not in used_rgb and j not in used_depth:
            used_rgb.add(i)
            used_depth.add(j)
            matches.append(RGBDMatch(rgb[i], depth[j]))
    return sorted(matches, key=lambda pair: pair.rgb.timestamp)


def backproject_depth(depth_raw: np.ndarray, intrinsics: CameraIntrinsics = DEFAULT_INTRINSICS,
                      stride: int = 1) -> tuple[np.ndarray, np.ndarray]:
    """Return (pixels_uv Nx2, optical camera points Nx3) for nonzero PNG depths.

    Sampling starts at pixel (0, 0) and uses a fixed grid; there is no depth
    range filter, confidence filter, scale correction, or image undistortion.
    """
    raw = np.asarray(depth_raw)
    if raw.shape != (intrinsics.height, intrinsics.width):
        raise ValueError("Depth dimensions do not match intrinsics")
    if not np.issubdtype(raw.dtype, np.integer) or np.any(raw < 0) or np.any(raw > 65535):
        raise ValueError("Expected unsigned 16-bit PNG depth values (integer array)")
    if not isinstance(stride, (int, np.integer)) or isinstance(stride, bool) or stride < 1:
        raise ValueError("stride must be a positive integer")
    v, u = np.mgrid[0:intrinsics.height:stride, 0:intrinsics.width:stride]
    z = raw[::stride, ::stride].astype(np.float64) / 5000.0
    valid = z > 0
    u, v, z = u[valid], v[valid], z[valid]
    pixels = np.column_stack((u, v))
    points = np.column_stack(((u - intrinsics.cx) * z / intrinsics.fx,
                              (v - intrinsics.cy) * z / intrinsics.fy, z))
    return pixels, points


@dataclass(frozen=True)
class SparseFrame:
    match: RGBDMatch
    intrinsics: CameraIntrinsics
    stride: int
    rgb_image: np.ndarray
    depth_m: np.ndarray
    pixels_uv: np.ndarray
    points_camera: np.ndarray
    points_world: np.ndarray
    colors_rgb: np.ndarray
    c2w_optical: np.ndarray
    pose: PoseInterpolation
    pose_time: str

    @property
    def valid_depth_fraction(self) -> float:
        return float(np.count_nonzero(self.depth_m) / self.depth_m.size)


def load_sparse_frame(root: str | Path, match: RGBDMatch, trajectory: PoseTrajectory,
                      stride: int = 8, intrinsics: CameraIntrinsics = DEFAULT_INTRINSICS,
                      pose_time: str = "depth", max_pose_gap_seconds: float | None = 0.1) -> SparseFrame:
    """Load one pair, using the depth timestamp for geometry by default.

    RGB colours are taken at the matched pixel without temporal compensation.
    depth_m retains 0 for missing observations; colors_rgb is uint8 in [0,255].
    Neither Kinect depths nor resulting world points are noiseless ground truth.
    """
    from PIL import Image
    root = Path(root)
    with Image.open(root / match.rgb.path) as im:
        rgb = np.asarray(im.convert("RGB")).copy()
    with Image.open(root / match.depth.path) as im:
        raw = np.asarray(im).copy()
    if rgb.shape != (intrinsics.height, intrinsics.width, 3):
        raise ValueError("RGB dimensions do not match intrinsics")
    if pose_time not in ("depth", "rgb"):
        raise ValueError("pose_time must be 'depth' or 'rgb'")
    timestamp = match.depth.timestamp if pose_time == "depth" else match.rgb.timestamp
    pose = trajectory.interpolate(timestamp, max_pose_gap_seconds)
    pixels, camera = backproject_depth(raw, intrinsics, stride)
    world = camera @ pose.c2w[:3, :3].T + pose.c2w[:3, 3]
    colors = rgb[pixels[:, 1], pixels[:, 0]]
    return SparseFrame(match, intrinsics, stride, rgb, raw.astype(np.float64) / 5000.0,
                       pixels, camera, world, colors, pose.c2w, pose, pose_time)


def optical_to_vmem_c2w(c2w_optical: np.ndarray) -> np.ndarray:
    """Convert x-right/y-down/z-forward camera axes to VMem camera convention."""
    matrix = np.asarray(c2w_optical, dtype=float)
    if matrix.shape != (4, 4) or not np.isfinite(matrix).all():
        raise ValueError("Expected a finite 4 x 4 camera-to-world matrix")
    return matrix @ np.diag([1., -1., -1., 1.])
