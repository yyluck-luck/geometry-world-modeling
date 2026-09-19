"""Independent NumPy/SciPy references. Does not import producer, Torch or PIL."""
import math
import numpy as np
from scipy.spatial.transform import Rotation


def camera_matrices(rotation, translation):
    result = np.repeat(np.eye(4)[None], len(rotation), axis=0)
    result[:, :3, :3] = rotation
    result[:, :3, 3] = translation
    return result


def reconstruct_world(depth, focal, pp, rotation, translation):
    depth = np.asarray(depth, dtype=np.float64)
    n, height, width = depth.shape
    rows, columns = np.indices((height, width), dtype=np.float64)
    result = np.empty((n, height, width, 3), dtype=np.float64)
    for i in range(n):
        camera = np.stack(((columns - pp[i, 0]) * depth[i] / float(focal[i, 0]),
                           (rows - pp[i, 1]) * depth[i] / float(focal[i, 0]), depth[i]), axis=-1)
        result[i] = np.einsum('ab,hwb->hwa', rotation[i].astype(np.float64), camera) + translation[i]
    return result


def clean_reference(confidence, depth, world, focal, pp, rotation, translation):
    """Separate FP32 component path; exact confidence match is the fixed gate."""
    result = np.array(confidence, dtype=np.float32, copy=True)
    depth = np.asarray(depth, dtype=np.float32)
    world = np.asarray(world, dtype=np.float32)
    cameras = camera_matrices(rotation, translation).astype(np.float32)
    focal, pp = np.asarray(focal, dtype=np.float32), np.asarray(pp, dtype=np.float32)
    visits = []
    margins = {}
    for i in range(len(result)):
        for j in range(len(result)):
            if i == j:
                continue
            inverse = np.linalg.inv(cameras[j])
            cam = np.stack([((world[i, ..., 0] * inverse[k, 0] + world[i, ..., 1] * inverse[k, 1]) +
                              world[i, ..., 2] * inverse[k, 2]) + inverse[k, 3]
                            for k in range(3)], axis=-1)
            z = cam[..., 2]
            with np.errstate(divide='ignore', invalid='ignore'):
                x = (focal[j, 0] * cam[..., 0] + pp[j, 0] * z) / z
                y = (focal[j, 0] * cam[..., 1] + pp[j, 1] * z) / z
            finite = np.isfinite(x) & np.isfinite(y)
            xx = np.rint(np.where(finite, x, -1)).astype(np.int64)
            yy = np.rint(np.where(finite, y, -1)).astype(np.int64)
            height, width = result[j].shape
            valid = finite & (z > 0) & (xx >= 0) & (xx < width) & (yy >= 0) & (yy < height)
            source_row, source_col = np.nonzero(valid)
            target_row, target_col = yy[valid], xx[valid]
            depth_margin = z[valid] - np.float32(.999) * depth[j, target_row, target_col]
            confidence_margin = result[i, source_row, source_col] - result[j, target_row, target_col]
            front = depth_margin < 0
            weaker = confidence_margin < 0
            bad = front & weaker
            rr, cc = source_row[bad], source_col[bad]
            before = result[i, rr, cc].copy()
            result[i, rr, cc] = np.minimum(result[i, rr, cc], 0.)
            prefix = f'{i}_to_{j}_'
            margins[prefix + 'projected_xy'] = np.stack((x, y), axis=-1)
            margins[prefix + 'positive_z_margin'] = z.copy()
            with np.errstate(invalid='ignore'):
                margins[prefix + 'half_pixel_distance_xy'] = np.stack((abs(x - (np.floor(x) + .5)),
                                                                      abs(y - (np.floor(y) + .5))), axis=-1)
            margins[prefix + 'paired_valid'] = valid
            for label, values in [('depth_margin', depth_margin), ('confidence_margin', confidence_margin)]:
                full = np.full(valid.shape, np.nan, dtype=np.float32)
                full[valid] = values
                margins[prefix + label] = full
            visits.append(dict(source=i, target=j, projected_valid=int(valid.sum()),
                               behind_or_zero=int((z <= 0).sum()),
                               outside_or_nonfinite=int((~valid & ~(z <= 0)).sum()),
                               front=int(front.sum()), front_and_weaker=int(bad.sum()),
                               actually_changed=int(np.count_nonzero(before != result[i, rr, cc]))))
    return result, visits, margins


def raw_pose_scipy(encodings):
    encodings = np.asarray(encodings, dtype=np.float64)
    # CUT3R seven head values use xyz translation followed by wxyz quaternion.
    rot = Rotation.from_quat(encodings[:, [4, 5, 6, 3]]).as_matrix()
    return camera_matrices(rot, encodings[:, :3])


def pair_objective(world, pred_i, pred_j, conf_i, conf_j, scaled_pair_pose, adaptor):
    """One directed edge. Original name l1 means 3D Euclidean norm, not Manhattan."""
    total = 0.
    for image_index, prediction, confidence in ((0, pred_i, conf_i), (1, pred_j, conf_j)):
        adjusted = np.asarray(prediction, dtype=np.float64) * np.asarray(adaptor, dtype=np.float64)
        aligned = adjusted @ np.asarray(scaled_pair_pose[:3, :3], dtype=np.float64).T + scaled_pair_pose[:3, 3]
        norm = np.linalg.norm(world[image_index].astype(np.float64) - aligned, axis=-1)
        weighted = norm * np.log(np.asarray(confidence, dtype=np.float64))
        total += math.fsum(weighted.ravel().tolist()) / weighted.size
    return total


def normalized_input_colors(input_images):
    return np.clip(np.asarray(input_images).transpose(0, 2, 3, 1) * .5 + .5, 0., 1.)


def expected_learning_rates():
    return np.array([.01 + (1e-6 - .01) * (i / 400) for i in range(400)])
