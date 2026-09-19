"""3DMatch RGB-D Scenes v2 adapter for the declared scene13 development run.

This is a data adapter, not an OS sandbox or a scientific acceptance decision.
All data reads require an exact relative-path, byte-count, SHA-256 and role
allowlist. Callers must additionally run the predictor under enforced isolation.
Only the exposed frame 000000 is used by this directory's qualification runner.

Source contract and the 3DMatch training/fusion pixel-convention discrepancy are
documented in SOURCE_EVIDENCE.md. Default half-pixel centres match 3DMatch's
training/match.hpp and pinned VMem utils.get_image_grid. They are an explicit
development convention, not a claim of universal sensor calibration.
"""
from __future__ import annotations

import hashlib
import io
import re
import struct
from pathlib import Path, PurePosixPath
from typing import Mapping, Sequence

import numpy as np
from PIL import Image

SCENE_ID = "rgbd-scenes-v2-scene_13"
SEQUENCE_ID = "seq-01"
HISTORY_IDS = (0, 15, 30, 45)
COMMAND_IDS = (60, 75, 90, 105)
SOURCE_HW = (480, 640)
OUTPUT_HW = (576, 576)
PIXEL_CENTER_OFFSET = 0.5
DEPTH_DIVISOR = 1000.0
EXPECTED_K = np.array([[540.021232, 0.0, 320.0],
                       [0.0, 540.021232, 240.0],
                       [0.0, 0.0, 1.0]], dtype=np.float64)
FRAME_RE = re.compile(r"^seq-01/frame-\d{6}\.(color\.png|depth\.png|pose\.txt)$")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_bound(root: Path | str, relative: str,
               manifest: Mapping[str, Mapping], role: str) -> bytes:
    """Read one exact role-bound file. Does not glob, list, or open an archive."""
    rel = PurePosixPath(relative)
    if rel.is_absolute() or ".." in rel.parts or str(rel) != relative:
        raise ValueError("non-canonical relative input path")
    if relative != "camera-intrinsics.txt" and not FRAME_RE.fullmatch(relative):
        raise ValueError("path is not an explicitly supported scene file")
    binding = manifest.get(relative)
    if not isinstance(binding, Mapping) or binding.get("role") != role:
        raise PermissionError("input absent from exact requested-role allowlist: " + relative)
    if role not in {"calibration_intrinsics", "history_rgb", "history_pose",
                    "command_camera", "exposed_qualification_rgb",
                    "exposed_qualification_depth", "exposed_qualification_pose"}:
        raise PermissionError("unsupported adapter role: " + role)
    root = Path(root).resolve(strict=True)
    path = root.joinpath(*rel.parts)
    for i in range(1, len(rel.parts) + 1):
        if root.joinpath(*rel.parts[:i]).is_symlink():
            raise PermissionError("symlinks are not allowed in staged inputs")
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise PermissionError("input is outside its stage")
    expected_sha = binding.get("sha256")
    if not isinstance(expected_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_sha):
        raise ValueError("missing concrete SHA-256 binding")
    if resolved.stat().st_size != binding.get("bytes"):
        raise ValueError("input size changed: " + relative)
    data = resolved.read_bytes()
    if sha256_bytes(data) != expected_sha:
        raise ValueError("input hash changed: " + relative)
    return data


def png_header(data: bytes) -> dict:
    if len(data) < 33 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError("not a PNG with leading IHDR")
    w, h, bits, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", data[16:29])
    if compression != 0 or filtering != 0:
        raise ValueError("unsupported PNG header")
    return dict(width=w, height=h, bit_depth=bits, color_type=color, interlace=interlace)


def decode_rgb(data: bytes) -> np.ndarray:
    info = png_header(data)
    if (info["height"], info["width"]) != SOURCE_HW or (info["bit_depth"], info["color_type"]) != (8, 2):
        raise ValueError("expected scene13 640x480 24-bit RGB PNG")
    with Image.open(io.BytesIO(data)) as im:
        if im.mode != "RGB":
            raise ValueError("RGB PNG decoder mode mismatch")
        image = np.array(im, dtype=np.uint8, copy=True)
    return image


def decode_depth_mm(data: bytes) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return raw uint16 mm, optical-axis Z in metres, and explicit valid mask.

    Keep source invalid zeros; no range cut, fill, or bilinear depth mixing.
    3DMatch's fusion-specific six-metre filter is deliberately not a data rule.
    """
    info = png_header(data)
    if (info["height"], info["width"]) != SOURCE_HW or (info["bit_depth"], info["color_type"]) != (16, 0):
        raise ValueError("expected scene13 640x480 16-bit greyscale depth PNG")
    with Image.open(io.BytesIO(data)) as im:
        decoded = np.array(im, copy=True)
    if decoded.ndim != 2 or not np.issubdtype(decoded.dtype, np.integer):
        raise ValueError("depth decoder did not preserve integer pixels")
    if np.any(decoded < 0) or np.any(decoded > 65535):
        raise ValueError("depth pixel outside uint16 range")
    raw = decoded.astype(np.uint16)
    valid = raw != 0
    z_m = raw.astype(np.float64) / DEPTH_DIVISOR
    return raw, z_m, valid


def parse_K(data: bytes) -> np.ndarray:
    k = np.loadtxt(io.StringIO(data.decode("ascii")), dtype=np.float64)
    if k.shape != (3, 3) or not np.isfinite(k).all():
        raise ValueError("K must be a finite 3x3 matrix")
    if not np.allclose(k, EXPECTED_K, rtol=0, atol=1e-8):
        raise ValueError("scene13 K differs from frozen exposed metadata")
    return k


def parse_c2w(data: bytes) -> np.ndarray:
    """Read converted C2W in metres, without inventing hardware timestamps."""
    pose = np.loadtxt(io.StringIO(data.decode("ascii")), dtype=np.float64)
    if pose.shape != (4, 4) or not np.isfinite(pose).all():
        raise ValueError("pose must be finite 4x4")
    if not np.allclose(pose[3], [0, 0, 0, 1], rtol=0, atol=1e-6):
        raise ValueError("invalid homogeneous pose row")
    r = pose[:3, :3]
    if np.max(np.abs(r.T @ r - np.eye(3))) > 1e-4 or abs(np.linalg.det(r) - 1) > 1e-4:
        raise ValueError("pose rotation is not proper orthonormal within 1e-4")
    return pose


def preprocessing_geometry(source_hw=SOURCE_HW, output_hw=OUTPUT_HW) -> dict:
    """Match pinned VMem transform_img_and_K size=(W,H), scale=1, mode=crop.

    For scene13: 640x480 -> 768x576, then left=96/top=0 crop to 576².
    This has the same continuous map as source centre crop left=80, width=480
    followed by scale=1.2. The actual RGB order is resize, then crop.
    """
    h, w = map(int, source_hw)
    out_h, out_w = map(int, output_hw)
    if min(h, w, out_h, out_w) <= 0:
        raise ValueError("image dimensions must be positive")
    factor = max(out_h / h, out_w / w)
    rh, rw = int(np.ceil(factor * h)), int(np.ceil(factor * w))
    top = min(max(0, int(0.5 * rh) - out_h // 2), rh - out_h)
    left = min(max(0, int(0.5 * rw) - out_w // 2), rw - out_w)
    return dict(source_hw=[h, w], resized_hw=[rh, rw], output_hw=[out_h, out_w],
                scale_xy=[rw / w, rh / h], crop_left_top=[left, top],
                pixel_center_offset=PIXEL_CENTER_OFFSET, rgb_resampling="torch_area")


def transform_K(k: np.ndarray, geometry: Mapping) -> np.ndarray:
    sx, sy = geometry["scale_xy"]
    left, top = geometry["crop_left_top"]
    affine = np.array([[sx, 0, -left], [0, sy, -top], [0, 0, 1]], dtype=np.float64)
    return affine @ np.asarray(k, dtype=np.float64)


def preprocess_rgb(rgb: np.ndarray, k: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict]:
    """Return float32 CHW RGB [-1,1], absolute-pixel K576, and transform record."""
    import torch
    import torch.nn.functional as F
    rgb = np.asarray(rgb)
    if rgb.shape != (*SOURCE_HW, 3) or rgb.dtype != np.uint8:
        raise ValueError("expected native uint8 HWC RGB")
    geometry = preprocessing_geometry()
    # Match VMem's conversion to [0,1], area resize, centre crop, then [-1,1].
    tensor = torch.from_numpy(rgb.astype(np.float32) / np.float32(255.0)).permute(2, 0, 1)[None]
    tensor = F.interpolate(tensor, size=geometry["resized_hw"], mode="area", antialias=False)
    left, top = geometry["crop_left_top"]
    h, w = geometry["output_hw"]
    tensor = tensor[:, :, top:top + h, left:left + w]
    result = (tensor[0] * 2.0 - 1.0).contiguous().numpy()
    return result, transform_K(k, geometry), geometry


def resize_depth_nearest(raw: np.ndarray, geometry: Mapping) -> tuple[np.ndarray, np.ndarray]:
    """Nearest cell-center sample; returns raw mm and source [v,u] indices.

    This is a declared evaluation adapter rule, not an upstream RGB rule.
    Depth is not consumed by load_history. Keep masks/zeros and no clipping.
    """
    h, w = geometry["source_hw"]
    out_h, out_w = geometry["output_hw"]
    if raw.shape != (h, w) or raw.dtype != np.uint16:
        raise ValueError("raw depth shape/dtype mismatch")
    sx, sy = geometry["scale_xy"]
    left, top = geometry["crop_left_top"]
    source_x = np.floor((np.arange(out_w) + 0.5 + left) / sx).astype(np.int64)
    source_y = np.floor((np.arange(out_h) + 0.5 + top) / sy).astype(np.int64)
    if source_x.min() < 0 or source_x.max() >= w or source_y.min() < 0 or source_y.max() >= h:
        raise ValueError("preprocessing maps outside native depth")
    vv, uu = np.meshgrid(source_y, source_x, indexing="ij")
    return raw[vv, uu].copy(), np.stack([vv, uu], axis=-1)


def unproject(z_m: np.ndarray, k: np.ndarray, center_offset=PIXEL_CENTER_OFFSET) -> np.ndarray:
    """Optical coordinates: +X right, +Y down, +Z forward; zeros -> NaNs."""
    z_m = np.asarray(z_m, dtype=np.float64)
    if z_m.ndim != 2:
        raise ValueError("Z must be HxW")
    v, u = np.indices(z_m.shape, dtype=np.float64)
    pixels = np.stack([u + center_offset, v + center_offset, np.ones_like(u)], axis=-1)
    rays = pixels @ np.linalg.inv(np.asarray(k, dtype=np.float64)).T
    xyz = rays * z_m[..., None]
    xyz[~(np.isfinite(z_m) & (z_m > 0))] = np.nan
    return xyz


def project(xyz: np.ndarray, k: np.ndarray, center_offset=PIXEL_CENTER_OFFSET) -> np.ndarray:
    """Return continuous zero-based pixel indices; no raster rounding here."""
    xyz = np.asarray(xyz, dtype=np.float64)
    projected = xyz @ np.asarray(k, dtype=np.float64).T
    with np.errstate(invalid="ignore", divide="ignore"):
        uv = projected[..., :2] / projected[..., 2:3] - center_offset
    return np.where((np.isfinite(xyz).all(axis=-1) & (xyz[..., 2] > 0))[..., None], uv, np.nan)


def optical_c2w_to_vmem_input(c2w: np.ndarray) -> np.ndarray:
    """VMem input convention only: right-multiply diag(1,-1,-1,1).

    Original VMem get_cond flips camera Y/Z columns before producing rays.
    The original metric optical C2W is returned separately and never replaced.
    """
    return np.asarray(c2w, dtype=np.float64) @ np.diag([1.0, -1.0, -1.0, 1.0])


def _checked_ids(frame_ids: Sequence[int], expected: tuple[int, ...]) -> tuple[int, ...]:
    ids = tuple(frame_ids)
    if ids != expected or any(type(x) is not int for x in ids):
        raise ValueError("IDs differ from frozen development window")
    return ids


def load_history(scene_root: Path | str, file_manifest: Mapping[str, Mapping],
                 frame_ids: Sequence[int] = HISTORY_IDS) -> dict:
    """Load exactly frozen four history RGB+poses; never reads depth or target RGB."""
    ids = _checked_ids(frame_ids, HISTORY_IDS)
    k = parse_K(read_bound(scene_root, "camera-intrinsics.txt", file_manifest, "calibration_intrinsics"))
    rgbs, poses, ks = [], [], []
    for frame_id in ids:
        stem = f"{SEQUENCE_ID}/frame-{frame_id:06d}"
        rgb = decode_rgb(read_bound(scene_root, stem + ".color.png", file_manifest, "history_rgb"))
        pose = parse_c2w(read_bound(scene_root, stem + ".pose.txt", file_manifest, "history_pose"))
        transformed, k576, geometry = preprocess_rgb(rgb, k)
        rgbs.append(transformed); poses.append(pose); ks.append(k576)
    return dict(rgb=np.stack(rgbs), K576=np.stack(ks), c2w_optical=np.stack(poses),
                frame_ids=list(ids), scene_id=SCENE_ID, sequence_id=SEQUENCE_ID,
                geometry=geometry, clock="frame_order_only_no_hardware_timestamp", depth_reads=0)


def load_camera_commands(scene_root: Path | str, file_manifest: Mapping[str, Mapping],
                         frame_ids: Sequence[int] = COMMAND_IDS) -> dict:
    """Load predeclared query C2W commands only; outcome pose roles are rejected."""
    ids = _checked_ids(frame_ids, COMMAND_IDS)
    k = parse_K(read_bound(scene_root, "camera-intrinsics.txt", file_manifest, "calibration_intrinsics"))
    poses = []
    for frame_id in ids:
        path = f"{SEQUENCE_ID}/frame-{frame_id:06d}.pose.txt"
        poses.append(parse_c2w(read_bound(scene_root, path, file_manifest, "command_camera")))
    k576 = transform_K(k, preprocessing_geometry())
    return dict(c2w_optical=np.stack(poses), K576=np.repeat(k576[None], len(ids), axis=0),
                frame_ids=list(ids), role="command_camera", outcome_pose_prediction=False,
                rgb_reads=0, depth_reads=0,
                claim="camera-conditioned future-view generation, not prediction of future camera pose")
