"""Pure S6 predicted geometry bridge; no measurements, files, or model calls.

Depth, pose translation, radius and matching thresholds use a prediction-only
normalized unit. This is the frozen 224 self-depth component experiment, not
the VMem 512 reconstruction/optimization/cleaning pipeline.
"""
import hashlib
import json
import re
from types import SimpleNamespace as NS

import numpy as np
import torch

from rgbd_memory import Memory
from rgbd_retrieval import initial_nms_threshold, optical_to_vmem, select
from retrieval_diagnostic import ObservedKernel
from vmem_memory_kernel import Surfel


def crop_intrinsics():
    """Known 640x480 calibration after pixel-center resize and the 224 crop."""
    return (525. * 299 / 640, 525. * 224 / 480,
            (319.5 + .5) * 299 / 640 - .5 - 37,
            (239.5 + .5) * 224 / 480 - .5)


def _pose(value):
    p = np.asarray(value, dtype=np.float64)
    if p.shape == (1, 4, 4):
        p = p[0]
    if p.shape != (4, 4) or not np.isfinite(p).all():
        raise ValueError('Expected finite 4x4 optical camera pose')
    if not np.allclose(p[3], [0, 0, 0, 1], atol=1e-6, rtol=0):
        raise ValueError('Invalid homogeneous pose row')
    r = p[:3, :3]
    if (not np.allclose(r.T @ r, np.eye(3), atol=1e-4, rtol=0)
            or not np.isclose(np.linalg.det(r), 1., atol=1e-4, rtol=0)):
        raise ValueError('Pose rotation is not a proper rotation')
    return p.copy()


def _image(value, name):
    a = np.asarray(value, dtype=np.float64)
    if a.shape == (1, 224, 224):
        a = a[0]
    if a.shape != (224, 224):
        raise ValueError(f'{name} must have shape 224x224 (optional batch=1)')
    return a


def normalize_predictions(raw_arrays):
    """Return (depths_normalized, poses_normalized, normalization_scale).

    Input is an already loaded mapping with official frame{i}_... NPZ keys.
    Only self-view Z and camera_c2w are read. X/Y, other points, confidences,
    measured depths, and reference trajectories cannot affect normalization.
    All frames are normalized from the first frame's positive finite Z median.
    """
    ids = sorted(int(m.group(1)) for key in raw_arrays
                 if (m := re.fullmatch(r'frame(\d+)_pts3d_in_self_view', key)))
    if not ids or ids != list(range(len(ids))) or len(ids) > 24:
        raise ValueError('Expected contiguous prediction frame IDs 0..N-1, 1<=N<=24')
    depths, poses = [], []
    for i in ids:
        xyz = np.asarray(raw_arrays[f'frame{i}_pts3d_in_self_view'])
        if xyz.shape == (1, 224, 224, 3):
            xyz = xyz[0]
        if xyz.shape != (224, 224, 3):
            raise ValueError('Self pointmap must have shape 224x224x3 (optional batch=1)')
        depths.append(xyz[..., 2].astype(np.float64, copy=True))
        poses.append(_pose(raw_arrays[f'frame{i}_camera_c2w']))
    valid = np.isfinite(depths[0]) & (depths[0] > 0)
    if not valid.any():
        raise ValueError('First prediction has no positive finite depth')
    scale = 1. / float(np.median(depths[0][valid]))
    if not np.isfinite(scale) or scale <= 0:
        raise ValueError('Prediction normalization scale must be positive finite')
    first_inverse = np.linalg.inv(poses[0])
    relative = []
    for p in poses:
        q = first_inverse @ p
        q[:3, 3] *= scale
        relative.append(q)
    return [d * scale for d in depths], relative, scale


def make_surfels(depth_normalized, conf_self, rgb, pose_normalized, stride=8):
    """Return surfels and staged filter counts for one already-normalized frame.

    RGB must be the uint8 official 224 crop. Confidence/far-depth validity is
    applied to the original center, right, and down pixels before constructing
    the finite-difference normal. Sample rejection counts are disjoint.
    """
    if stride not in (8, 12):
        raise ValueError('S6 frozen strides are 8 and 12')
    z = _image(depth_normalized, 'Depth')
    conf = _image(conf_self, 'Self confidence')
    rgb = np.asarray(rgb)
    if rgb.shape != (224, 224, 3) or rgb.dtype != np.uint8:
        raise ValueError('RGB must be the uint8 224x224x3 crop')
    pose = _pose(pose_normalized)
    positive = np.isfinite(z) & (z > 0)
    conf_ok = np.isfinite(conf) & (conf >= 1.)
    cutoff = float(np.quantile(z[positive], .999)) if positive.any() else None
    near = z <= cutoff if cutoff is not None else np.zeros(z.shape, dtype=bool)
    pixel_valid = positive & conf_ok & near
    # The masked depth is used for all three rays, not just the sampled center.
    filtered = np.where(pixel_valid, z, np.nan)
    vv, uu = np.mgrid[0:224:stride, 0:224:stride]
    u, v = uu.ravel(), vv.ravel()
    counts = dict(
        total_pixels=int(z.size), positive_finite_depth_pixels=int(positive.sum()),
        rejected_pixel_depth=int((~positive).sum()),
        rejected_pixel_confidence_after_depth=int((positive & ~conf_ok).sum()),
        rejected_pixel_far_after_depth_confidence=int((positive & conf_ok & ~near).sum()),
        eligible_pixels=int(pixel_valid.sum()), far_cutoff_normalized=cutoff,
        sampled_grid_points=int(len(u)), stride=int(stride),
        neighbor_jump_threshold_normalized=.05)
    inside = (u < 223) & (v < 223)
    counts['rejected_sample_boundary'] = int((~inside).sum())
    u, v = u[inside], v[inside]
    center = pixel_valid[v, u]
    counts['rejected_sample_center'] = int((~center).sum())
    u, v = u[center], v[center]
    neighbor = pixel_valid[v, u+1] & pixel_valid[v+1, u]
    counts['rejected_sample_neighbor'] = int((~neighbor).sum())
    u, v = u[neighbor], v[neighbor]
    zz, zr, zd = filtered[v, u], filtered[v, u+1], filtered[v+1, u]
    smooth = (np.abs(zr-zz) <= .05) & (np.abs(zd-zz) <= .05)
    counts['rejected_sample_neighbor_jump'] = int((~smooth).sum())
    u, v, zz, zr, zd = [a[smooth] for a in (u, v, zz, zr, zd)]
    fx, fy, cx, cy = crop_intrinsics()
    p = np.column_stack(((u-cx)*zz/fx, (v-cy)*zz/fy, zz))
    right = np.column_stack(((u+1-cx)*zr/fx, (v-cy)*zr/fy, zr))
    down = np.column_stack(((u-cx)*zd/fx, (v+1-cy)*zd/fy, zd))
    normals = np.cross(right-p, down-p)
    lengths = np.linalg.norm(normals, axis=1)
    nondegenerate = np.isfinite(lengths) & (lengths > 1e-12)
    counts['rejected_sample_degenerate_normal'] = int((~nondegenerate).sum())
    p, normals, zz, u, v = [a[nondegenerate] for a in (p, normals, zz, u, v)]
    normals /= lengths[nondegenerate, None]
    rays = p / np.linalg.norm(p, axis=1)[:, None]
    cosine = np.sum(normals * rays, axis=1)
    normals[cosine < 0] *= -1
    radii = .5 * zz / ((fx+fy)/2/stride) / (.2 + .8*np.abs(cosine))
    points_normalized = p @ pose[:3, :3].T + pose[:3, 3]
    normals = normals @ pose[:3, :3].T
    surfels = [Surfel(point.copy(), normal.copy(), float(radius), color.astype(float)/255.)
               for point, normal, radius, color in zip(points_normalized, normals, radii, rgb[v, u])]
    counts['accepted_surfels'] = len(surfels)
    return surfels, counts


def build_memory(depths_normalized, confs, rgbs, poses_normalized,
                 stride=8, method='first_write'):
    """Build only ordered history IDs 0..19; return (Memory, filter_records)."""
    n = len(depths_normalized)
    if n == 0 or n > 20:
        raise ValueError('Memory accepts only 1..20 historical frames; queries cannot be added')
    if any(len(values) != n for values in (confs, rgbs, poses_normalized)):
        raise ValueError('Depth, confidence, RGB, and pose history lengths must match')
    if method not in ('first_write', 'frame_mean'):
        raise ValueError(f'Unknown S6 memory method {method}')
    memory, filters = Memory(method), []
    for frame_id, (depth, conf, rgb, pose) in enumerate(
            zip(depths_normalized, confs, rgbs, poses_normalized)):
        surfels, counts = make_surfels(depth, conf, rgb, pose, stride)
        counts['frame_id'] = frame_id
        filters.append(counts)
        memory.add(surfels, frame_id, normal_threshold=.6)
        # Matching is unchanged; only externally reported unit names differ.
        row = memory.records[-1]
        row['position_threshold_normalized'] = row.pop('position_threshold_m')
        row['radius_normalized_quantiles'] = row.pop('radius_m_quantiles')
    return memory, filters


def _check_history(memory, pose_count=None):
    n = len(memory.surfels)
    if len(memory.counts) != n or set(memory.mapping) != set(range(n)):
        raise ValueError('Memory geometry, counts, and mapping disagree')
    limit = 20 if pose_count is None else min(pose_count, 20)
    for ids in memory.mapping.values():
        if not ids or len(ids) != len(set(ids)) or any(
                not isinstance(i, (int, np.integer)) or not 0 <= i < limit for i in ids):
            raise ValueError('Memory has duplicate or nonhistorical source IDs')


def make_selector(memory, poses_normalized, width=160, threshold=None):
    """Initialize the unchanged full VMem selector with a square crop geometry.

    Call rgbd_retrieval.select(obj, optical_query_normalized) for retrieval.
    Its renderer retains the upstream focal*0.65 and centered-principal-point
    approximation; Ks preserves the explicitly scaled crop K.
    """
    if width not in (160, 320):
        raise ValueError('S6 frozen render widths are 160 and 320')
    if not 4 <= len(poses_normalized) <= 20:
        raise ValueError('Selector requires 4..20 historical poses only')
    _check_history(memory, len(poses_normalized))
    poses = [_pose(p) for p in poses_normalized]
    if threshold is None:
        threshold = initial_nms_threshold(poses, weight=.1)
    if not np.isfinite(threshold) or threshold < 0:
        raise ValueError('NMS threshold must be finite and nonnegative')
    obj = ObservedKernel()
    obj.config = NS(model=NS(context_num_frames=4, translation_distance_weight=.1),
                    surfel=NS(width=width, height=width), inference=NS(visualize=False))
    obj.device, obj.dtype = 'cpu', torch.float64
    obj.use_non_maximum_suppression = True
    obj.initial_threshold = float(threshold)
    obj.c2ws = [optical_to_vmem(p) for p in poses]
    n = len(poses)
    obj.pil_frames = [None] * n
    obj.latents = [np.asarray([i], dtype=np.float64) for i in range(n)]
    obj.encoder_embeddings = [np.asarray([i+.25], dtype=np.float64) for i in range(n)]
    fx, fy, cx, cy = crop_intrinsics()
    scale = width / 224.
    k = np.array([[fx*scale, 0, cx*scale], [0, fy*scale, cy*scale], [0, 0, 1.]])
    obj.Ks = [k.copy() for _ in poses]
    obj.surfel_Ks = [(fx+fy)/2*scale] * n
    obj.surfels, obj.surfel_to_timestep = memory.surfels, memory.mapping
    return obj


def memory_digest(memory):
    """Hash every position, normal, radius, color, count and source association."""
    _check_history(memory)
    h = hashlib.sha256()
    h.update(b'S6 normalized memory digest v1\0')
    for surfel in memory.surfels:
        for value in (surfel.position, surfel.normal, [surfel.radius]):
            a = np.asarray(value, dtype='<f8')
            h.update(np.asarray(a.shape, dtype='<i8').tobytes())
            h.update(a.tobytes())
        if surfel.color is None:
            h.update(b'color:none\0')
        else:
            color = np.asarray(surfel.color, dtype='<f8')
            h.update(b'color:array\0')
            h.update(np.asarray(color.shape, dtype='<i8').tobytes())
            h.update(color.tobytes())
    h.update(np.asarray(memory.counts, dtype='<i8').tobytes())
    h.update(json.dumps([[i, [int(t) for t in memory.mapping[i]]]
                         for i in range(len(memory.surfels))], separators=(',', ':')).encode())
    return h.hexdigest()
