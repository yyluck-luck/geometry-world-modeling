"""Independent clean formula with the original CPU FP32 numerical contract.

No producer or model code is imported. Matrix inverse and matrix multiplication
use Torch like the producer because discrete pixel/depth predicates can change
under other IEEE-754 operation orders. This is not a cross-library exact check.
"""
import numpy as np
import torch


def clean_reference(confidence, depth, world, focal, pp, rotation, translation):
    tensors = [torch.from_numpy(np.array(a, dtype=np.float32, copy=True))
               for a in (confidence, depth, world, focal, pp, rotation, translation)]
    conf, dep, points, foc, principal, rot, trans = tensors
    n, height, width = conf.shape
    poses = torch.eye(4, dtype=torch.float32).repeat(n, 1, 1)
    poses[:, :3, :3], poses[:, :3, 3] = rot, trans
    inverse = torch.linalg.inv(poses)  # Batched, not n separate NumPy inverses.
    intrinsics = torch.zeros((n, 3, 3), dtype=torch.float32)
    intrinsics[:, 0, 0] = intrinsics[:, 1, 1] = foc.reshape(n)
    intrinsics[:, :2, 2], intrinsics[:, 2, 2] = principal, 1
    visits, margins = [], {}
    # Dense gather plus a full-grid logical predicate is independent of the
    # producer's compact valid-pixel selection and boolean scatter update.
    with torch.no_grad():
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                affine = points[i] @ inverse[j].T[:3, :] + inverse[j].T[3:4, :]
                camera = affine[..., :3]
                homogeneous = camera @ intrinsics[j].T
                xy = (homogeneous / homogeneous[..., 2:3])[..., :2]
                uv = xy.round().to(torch.int64)
                u, v = uv[..., 0], uv[..., 1]
                z = camera[..., 2]
                valid = (z > 0) & (u >= 0) & (u < width) & (v >= 0) & (v < height)
                address = v.clamp(0, height - 1) * width + u.clamp(0, width - 1)
                target_depth = dep[j].reshape(-1)[address]
                target_conf = conf[j].reshape(-1)[address]
                depth_margin = z - .999 * target_depth
                confidence_margin = conf[i] - target_conf
                front, weaker = z < .999 * target_depth, conf[i] < target_conf
                bad = valid & front & weaker
                revised = torch.where(bad, torch.minimum(conf[i], torch.zeros_like(conf[i])), conf[i])
                visits.append({'source': i, 'target': j, 'projected_valid': int(valid.sum()),
                               'front': int((valid & front).sum()), 'front_and_weaker': int(bad.sum()),
                               'actually_changed': int((revised != conf[i]).sum())})
                conf[i] = revised
                prefix = f'{i}_to_{j}_'
                margins[prefix + 'projected_xy'] = xy.numpy().copy()
                margins[prefix + 'positive_z_margin'] = z.numpy().copy()
                margins[prefix + 'paired_valid'] = valid.numpy().copy()
                for key, values in [('depth_margin', depth_margin), ('confidence_margin', confidence_margin)]:
                    masked = torch.where(valid, values, torch.full_like(values, torch.nan))
                    margins[prefix + key] = masked.numpy().copy()
    return conf.numpy().copy(), visits, margins
