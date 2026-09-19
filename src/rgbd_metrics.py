"""NumPy metrics for measured RGB-D consistency, not error to geometric truth.

Frames are mappings with ``depth`` in metres, ``c2w_optical`` (camera to world,
x right, y down, z forward), and ``intrinsics`` as (fx, fy, cx, cy) or a 3x3 K.
``c2w``/``pose`` and ``K`` are accepted aliases. Intrinsics default to the TUM
ROS recommendation only when a frame does not supply them.

Evaluation samples original pixels (u, v) = (0, stride, 2*stride, ...), never
block centres. Depth is neither resized nor bilinearly interpolated. Target
measurements are only evaluation inputs; these functions do not change memory.
"""
from collections.abc import Mapping
import numpy as np


DEFAULT_INTRINSICS = (525.0, 525.0, 319.5, 239.5)


def _intrinsics(value):
    if isinstance(value, Mapping):
        out = np.asarray([value[k] for k in ("fx", "fy", "cx", "cy")], dtype=float)
    else:
        a = np.asarray(value, dtype=float)
        out = np.array([a[0, 0], a[1, 1], a[0, 2], a[1, 2]]) if a.shape == (3, 3) else a
    if out.shape != (4,) or not np.isfinite(out).all() or np.any(out[:2] <= 0):
        raise ValueError("Intrinsics must be finite (fx, fy, cx, cy), with positive focal lengths")
    return out


def _pose(value):
    pose = np.asarray(value, dtype=float)
    if pose.shape != (4, 4) or not np.isfinite(pose).all():
        raise ValueError("c2w_optical must be a finite 4x4 matrix")
    r = pose[:3, :3]
    if not np.allclose(pose[3], [0, 0, 0, 1], atol=1e-7) or not np.allclose(r.T @ r, np.eye(3), atol=1e-6) or not np.isclose(np.linalg.det(r), 1, atol=1e-6):
        raise ValueError("c2w_optical must be a rigid camera-to-world transform")
    return pose


def _frame(frame=None, *, depth=None, c2w_optical=None, intrinsics=None):
    if frame is not None:
        if not isinstance(frame, Mapping):
            raise TypeError("Frame must be a mapping, or supply depth/c2w_optical/intrinsics arrays")
        if depth is None:
            depth = frame.get("depth")
        if c2w_optical is None:
            c2w_optical = frame.get("c2w_optical", frame.get("c2w", frame.get("pose")))
        if intrinsics is None:
            intrinsics = frame.get("intrinsics", frame.get("K", DEFAULT_INTRINSICS))
    if depth is None or c2w_optical is None:
        raise ValueError("A depth image in metres and an optical camera-to-world pose are required")
    depth = np.asarray(depth, dtype=float)
    if depth.ndim != 2 or not all(depth.shape):
        raise ValueError("Depth must be a nonempty HxW array in metres")
    return depth, _pose(c2w_optical), _intrinsics(DEFAULT_INTRINSICS if intrinsics is None else intrinsics)


def _stride(value):
    if isinstance(value, bool) or int(value) != value or value < 1:
        raise ValueError("stride must be a positive integer")
    return int(value)


def valid_depth_interior(depth, edge_threshold=0.05):
    """Finite positive depth with valid four-neighbours and no >threshold jump.

    Reject image borders and both sides of missing-data/depth boundaries at the
    native resolution. The threshold is a fixed evaluation mask, not a filter
    on prediction errors. Gross prediction errors therefore remain measurable.
    """
    depth = np.asarray(depth, dtype=float)
    if depth.ndim != 2:
        raise ValueError("Depth must be HxW")
    if not np.isfinite(edge_threshold) or edge_threshold < 0:
        raise ValueError("edge_threshold must be finite and nonnegative")
    good = np.isfinite(depth) & (depth > 0)
    out = np.zeros(depth.shape, dtype=bool)
    if min(depth.shape) < 3:
        return out
    center = depth[1:-1, 1:-1]
    inside = good[1:-1, 1:-1].copy()
    for neighbor, valid in ((depth[:-2, 1:-1], good[:-2, 1:-1]),
                            (depth[2:, 1:-1], good[2:, 1:-1]),
                            (depth[1:-1, :-2], good[1:-1, :-2]),
                            (depth[1:-1, 2:], good[1:-1, 2:])):
        with np.errstate(invalid="ignore"):
            inside &= valid & (np.abs(center - neighbor) <= edge_threshold)
    out[1:-1, 1:-1] = inside
    return out


def project_points(points_world, c2w_optical, intrinsics, width=640, height=480):
    """Return (uv[N,2], camera_z[N], continuous_image_in_bounds[N]).

    Nonfinite/behind-camera points have NaN uv and false in_bounds. Image
    bounds are 0<=u<width, 0<=v<height; callers must also check rounded indices.
    """
    points = np.asarray(points_world, dtype=float)
    if points.ndim != 2 or points.shape[1] != 3:
        raise ValueError("points_world must have shape Nx3")
    if width <= 0 or height <= 0:
        raise ValueError("Image dimensions must be positive")
    pose, (fx, fy, cx, cy) = _pose(c2w_optical), _intrinsics(intrinsics)
    cam = (points - pose[:3, 3]) @ pose[:3, :3]
    z = cam[:, 2]
    valid = np.isfinite(cam).all(axis=1) & (z > 0)
    uv = np.full((len(points), 2), np.nan)
    uv[valid] = cam[valid, :2] / z[valid, None] * [fx, fy] + [cx, cy]
    in_bounds = valid & np.isfinite(uv).all(axis=1) & (uv[:, 0] >= 0) & (uv[:, 0] < width) & (uv[:, 1] >= 0) & (uv[:, 1] < height)
    return uv, z, in_bounds


def depth_consistency(points_world, target_frame=None, stride=4, *, depth=None,
                      c2w_optical=None, intrinsics=None, edge_threshold=0.05):
    """Centre-point nearest-pixel z-buffer and masks for measured-depth checks.

    Return pred_depth (NaN when absent), pred_mask, sampled target_depth,
    target_valid, and common_mask. The runner should intersect both methods'
    pred_masks with the same target_valid for a paired primary comparison.
    Rounding uses NumPy round-to-nearest-even, including exact half-pixel ties.
    """
    depth, pose, k = _frame(target_frame, depth=depth, c2w_optical=c2w_optical, intrinsics=intrinsics)
    stride = _stride(stride)
    height, width = depth.shape
    target_depth = depth[::stride, ::stride].copy()
    gh, gw = target_depth.shape
    uv, z, inside = project_points(points_world, pose, k, width, height)
    ids = np.flatnonzero(inside)
    bins = np.rint(uv[ids] / stride).astype(np.int64)
    usable = (bins[:, 0] >= 0) & (bins[:, 0] < gw) & (bins[:, 1] >= 0) & (bins[:, 1] < gh)
    bins, ids = bins[usable], ids[usable]
    buffer = np.full(gh * gw, np.inf)
    np.minimum.at(buffer, bins[:, 1] * gw + bins[:, 0], z[ids])
    pred_depth = buffer.reshape(gh, gw)
    pred_mask = np.isfinite(pred_depth)
    pred_depth[~pred_mask] = np.nan
    target_valid = valid_depth_interior(depth, edge_threshold)[::stride, ::stride]
    return dict(pred_depth=pred_depth, pred_mask=pred_mask, target_depth=target_depth,
                target_valid=target_valid, common_mask=pred_mask & target_valid)


def measurement_support(history_frames, target_frame, stride=4, tolerance=0.05,
                        *, edge_threshold=0.05):
    """Return (per_history_support[N,Hs,Ws], target_valid[Hs,Ws]).

    Target measured surface points are projected into each history image. A
    source supports a target sample only when its nearest native pixel is a
    valid depth interior and its measured z agrees within tolerance. A nearer
    source occluder and a farther source surface are both rejected. There is no
    dependence on a method's memory, source labels, or predicted depth.
    """
    if not np.isfinite(tolerance) or tolerance < 0:
        raise ValueError("tolerance must be finite and nonnegative")
    depth, pose, (fx, fy, cx, cy) = _frame(target_frame)
    stride = _stride(stride)
    target_valid = valid_depth_interior(depth, edge_threshold)[::stride, ::stride]
    vv, uu = np.meshgrid(np.arange(0, depth.shape[0], stride), np.arange(0, depth.shape[1], stride), indexing="ij")
    z = depth[::stride, ::stride][target_valid]
    camera_points = np.stack([(uu[target_valid] - cx) * z / fx,
                              (vv[target_valid] - cy) * z / fy, z], axis=1)
    world_points = camera_points @ pose[:3, :3].T + pose[:3, 3]
    history_frames = list(history_frames)
    masks = np.zeros((len(history_frames),) + target_valid.shape, dtype=bool)
    target_indices = np.flatnonzero(target_valid)
    for frame_index, frame in enumerate(history_frames):
        source_depth, source_pose, source_k = _frame(frame)
        sh, sw = source_depth.shape
        uv, projected_z, in_bounds = project_points(world_points, source_pose, source_k, sw, sh)
        selected = np.flatnonzero(in_bounds)
        pixel = np.rint(uv[selected]).astype(np.int64)
        rounded_valid = (pixel[:, 0] >= 0) & (pixel[:, 0] < sw) & (pixel[:, 1] >= 0) & (pixel[:, 1] < sh)
        selected, pixel = selected[rounded_valid], pixel[rounded_valid]
        source_valid = valid_depth_interior(source_depth, edge_threshold)
        measured = source_depth[pixel[:, 1], pixel[:, 0]]
        support = source_valid[pixel[:, 1], pixel[:, 0]] & (np.abs(measured - projected_z[selected]) <= tolerance)
        masks[frame_index].ravel()[target_indices[selected[support]]] = True
    return masks, target_valid
