"""Fixed two-frame diagnostics; no model imports or parameter fitting on frame 1."""
import numpy as np
from PIL import Image


def crop_geometry(width, height):
    long_edge = round(224 * max(width / height, height / width))
    resized = tuple(round(v * long_edge / max(width, height)) for v in (width, height))
    cx, cy = (v // 2 for v in resized)
    half = min(cx, cy)
    return dict(original=[width, height], resized=list(resized), crop=[cx-half, cy-half, cx+half, cy+half])


def resize_crop(image, resample):
    geometry = crop_geometry(*image.size)
    return image.resize(geometry['resized'], resample=resample).crop(geometry['crop']), geometry


def measured_target(depth_m):
    depth = np.asarray(depth_m, dtype=np.float64)
    h, w = depth.shape
    valid = np.isfinite(depth) & (depth > 0)
    interior = np.zeros_like(valid)
    interior[2:-2, 2:-2] = True
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            shifted = np.roll(depth, (dy, dx), axis=(0, 1))
            interior &= np.roll(valid, (dy, dx), axis=(0, 1)) & (np.abs(shifted-depth) <= .05)
    sampled, geometry = resize_crop(Image.fromarray(depth.astype(np.float32)), Image.Resampling.NEAREST)
    mask, _ = resize_crop(Image.fromarray(interior.astype(np.uint8)), Image.Resampling.NEAREST)
    return np.asarray(sampled, dtype=np.float64), np.asarray(mask, dtype=bool), geometry


def valid_prediction(pred, target, mask):
    pred, target, mask = np.asarray(pred), np.asarray(target), np.asarray(mask)
    if pred.shape != target.shape or mask.shape != target.shape:
        raise ValueError('Shape mismatch; broadcasting is not permitted')
    return mask & np.isfinite(target) & (target > 0) & np.isfinite(pred) & (pred > 0)


def first_frame_scale(pred, target, mask):
    good = valid_prediction(pred, target, mask)
    if good.sum() < 100:
        raise ValueError('Fewer than 100 valid calibration pixels')
    scale = float(np.median(np.asarray(target)[good]/np.asarray(pred)[good]))
    if not np.isfinite(scale) or scale <= 0:
        raise ValueError('Invalid calibration scale')
    return scale, int(good.sum())


def depth_metrics(pred, target, mask, scale):
    good = valid_prediction(pred, target, mask)
    if good.sum() == 0:
        raise ValueError('No valid predicted depth for evaluation')
    residual = np.asarray(pred)[good] * scale - np.asarray(target)[good]
    absolute = np.abs(residual)
    return dict(n=int(good.sum()), target_valid=int(mask.sum()), prediction_coverage=float(good.sum()/mask.sum()),
                mae_mm=float(absolute.mean()*1000), median_abs_mm=float(np.median(absolute)*1000),
                p90_abs_mm=float(np.percentile(absolute, 90)*1000), signed_mean_mm=float(residual.mean()*1000),
                within_30mm=float(np.mean(absolute<=.03)), abs_rel=float(np.mean(absolute/np.asarray(target)[good])))


def validate_pose(pose):
    pose = np.asarray(pose, dtype=np.float64)
    if pose.shape != (4, 4) or not np.all(np.isfinite(pose)):
        raise ValueError('Invalid pose shape or values')
    r = pose[:3, :3]
    if not np.allclose(r.T@r, np.eye(3), atol=1e-4, rtol=1e-4) or not np.isclose(np.linalg.det(r), 1, atol=1e-4):
        raise ValueError('Pose rotation is not proper and orthogonal')
    if not np.allclose(pose[3], [0, 0, 0, 1], atol=1e-6, rtol=0):
        raise ValueError('Invalid homogeneous last row')
    return pose


def rotation_degrees(rotation):
    return float(np.degrees(np.arccos(np.clip((np.trace(rotation)-1)/2, -1, 1))))


def relative_pose_metrics(pred0, pred1, gt0, gt1, scale):
    p0, p1, g0, g1 = [validate_pose(p) for p in (pred0, pred1, gt0, gt1)]
    pred = np.linalg.inv(p0)@p1
    truth = np.linalg.inv(g0)@g1
    pred[:3, 3] *= scale
    return dict(rotation_error_deg=rotation_degrees(truth[:3,:3].T@pred[:3,:3]),
                translation_vector_error_mm=float(np.linalg.norm(pred[:3,3]-truth[:3,3])*1000),
                ground_truth_translation_mm=float(np.linalg.norm(truth[:3,3])*1000),
                ground_truth_rotation_deg=rotation_degrees(truth[:3,:3]),
                predicted_relative_c2w=pred.tolist(), ground_truth_relative_c2w=truth.tolist())
