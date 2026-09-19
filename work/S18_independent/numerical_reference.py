"""Independent NumPy S18 formulas; no producer or Torch imports.

NumPy 1.26 scalar promotions are explicit where NumPy 2.x differs.
These functions only compute arrays supplied by their caller.
"""
import itertools
import math
import numpy as np


def resize_point05(a):
    """NHW[C], original scale .05, align_corners=False, no recomputed scale."""
    a = np.asarray(a, dtype=np.float32)
    h, w = a.shape[1:3]
    oh, ow = math.floor(h * .05), math.floor(w * .05)
    # Scale comes from the given .05, never from h/oh or w/ow.
    y = np.maximum((np.arange(oh, dtype=np.float64) + .5) * 20 - .5, 0)
    x = np.maximum((np.arange(ow, dtype=np.float64) + .5) * 20 - .5, 0)
    iy, ix = np.floor(y).astype(np.int64), np.floor(x).astype(np.int64)
    jy, jx = np.minimum(iy + 1, h - 1), np.minimum(ix + 1, w - 1)
    wy, wx = (y - iy).astype(np.float32), (x - ix).astype(np.float32)
    shape = (1, oh, ow) + (() if a.ndim == 3 else (1,))
    wy = np.broadcast_to(wy[:, None], (oh, ow)).reshape(shape)
    wx = np.broadcast_to(wx[None, :], (oh, ow)).reshape(shape)
    p00, p01 = a[:, iy[:, None], ix], a[:, iy[:, None], jx]
    p10, p11 = a[:, jy[:, None], ix], a[:, jy[:, None], jx]
    top = np.float32(1 - wx) * p00 + wx * p01
    bottom = np.float32(1 - wx) * p10 + wx * p11
    out = np.float32(1 - wy) * top + wy * bottom
    return out.astype(np.float32), dict(y=y, x=x, y0=iy, x0=ix, y1=jy, x1=jx)


def norm32(a):
    a = np.asarray(a, dtype=np.float32)
    return np.sqrt(np.sum(a * a, axis=-1, dtype=np.float32)).astype(np.float32)


def cross_components(a, b):
    return np.stack((a[..., 1] * b[..., 2] - a[..., 2] * b[..., 1],
                     a[..., 2] * b[..., 0] - a[..., 0] * b[..., 2],
                     a[..., 0] * b[..., 1] - a[..., 1] * b[..., 0]), axis=-1)


def normal_map(pointmap):
    p = np.asarray(pointmap, dtype=np.float32)
    result = np.zeros_like(p)
    right, down = p[:-1, 1:] - p[:-1, :-1], p[1:, :-1] - p[:-1, :-1]
    with np.errstate(divide='ignore', invalid='ignore'):
        right = right / norm32(right)[..., None]
        down = down / norm32(down)[..., None]
        cross = cross_components(right, down)
        length = norm32(cross)
        # NaN < 1e-8 is false in original; retain failure instead of filling it.
        n = cross / length[..., None]
    n[length < np.float32(1e-8)] = 0
    result[:-1, :-1] = n
    return result


def quantile999(values):
    a = np.sort(np.asarray(values, dtype=np.float32).reshape(-1))
    if not len(a) or not np.isfinite(a).all():
        raise ValueError('quantile requires nonempty finite input')
    rank = np.float32(np.float32(.999) * np.float32(len(a) - 1))
    lo, hi = int(np.floor(rank)), int(np.ceil(rank))
    w = np.float32(rank - np.float32(lo))
    # Torch's lerp uses the nearer endpoint; arithmetic stays FP32.
    if w < np.float32(.5):
        return np.float32(a[lo] + np.float32(w * np.float32(a[hi] - a[lo])))
    return np.float32(a[hi] - np.float32(np.float32(a[hi] - a[lo]) * np.float32(1 - w)))


def candidates(points, depths, confs, focal, c2w, supplied_normal=None):
    p, d, c = (np.asarray(x, dtype=np.float32) for x in (points, depths, confs))
    nm = normal_map(p) if supplied_normal is None else np.asarray(supplied_normal, dtype=np.float32)
    threshold = quantile999(d)
    mask = (d <= threshold) & (c >= np.float32(1))
    ids = np.flatnonzero(mask).astype(np.int64)
    pos, n = p[mask].copy(), nm[mask].copy()
    view = pos - np.asarray(c2w[:3, 3], dtype=np.float32)
    view = view / np.maximum(norm32(view), np.float32(1e-12))[:, None]
    dot = np.sum(view * n, axis=-1, dtype=np.float32)
    flip = dot < 0
    n[flip] *= np.float32(-1)
    cosine = np.abs(np.sum(view * n, axis=-1, dtype=np.float32))
    adjustment = np.float32(.2) + np.float32(.8) * cosine
    f = np.asarray(focal, dtype=np.float32).reshape(-1)
    f = np.mean(f, dtype=np.float32) if len(f) == 2 else f[0]
    radius = (np.float32(.5) * d[mask] / f) / adjustment
    return dict(normal_map=nm, depth_threshold=np.asarray(threshold), valid_mask=mask,
                candidate_flat_ids=ids, candidate_positions=pos, candidate_normals=n,
                candidate_radii=radius, preflip_dot=dot, flip_mask=flip,
                view_direction=view, postflip_dot=cosine)


def merge_threshold(old_radii, new_radii):
    a = np.concatenate((np.asarray(old_radii, dtype=np.float32), np.asarray(new_radii, dtype=np.float32)))
    if not len(a):
        return .025
    # scalar32 + Python(.5) * scalar32 is float64 in NumPy 1.26.
    return float(np.float64(np.mean(a, dtype=np.float32)) + np.float64(.5) * np.float64(np.std(a, dtype=np.float32)))


class LegacyTree:
    """Independent explicit tree; preserve overlap, order, and legacy root rounding."""
    def __init__(self, points):
        self.points = np.asarray(points, dtype=np.float32)
        self.nodes = []
        if not len(points):
            self.root = None
            return
        low, high = self.points.min(0), self.points.max(0)
        center = ((low + high) / np.float32(2)).astype(np.float32)
        half = np.float64(np.max(high - low)) / np.float64(2)
        self.root = self.build(np.arange(len(points), dtype=np.int64), center, half, 0)

    def build(self, ids, center, half, depth):
        if depth > 96 or len(self.nodes) > 200000:
            raise ValueError('original tree degeneracy: refused unbounded duplicate subdivision')
        node = len(self.nodes)
        self.nodes.append(dict(center=np.asarray(center), half=float(half), ids=ids, children=[]))
        if len(ids) > 10:
            hs = np.float64(half) / np.float64(2)
            for signs in itertools.product((-1, 1), repeat=3):
                child_center = np.asarray(center, dtype=np.float64) + np.asarray(signs, dtype=np.float64) * hs
                selected = ids[np.all(np.abs(self.points[ids].astype(np.float64) - child_center) <= hs, axis=1)]
                if len(selected):
                    self.nodes[node]['children'].append(self.build(selected, child_center, hs, depth + 1))
            self.nodes[node]['ids'] = None
        return node

    def query(self, position, radius):
        found, visited = [], []
        if self.root is None:
            return found, visited
        p = np.asarray(position, dtype=np.float32)
        def walk(index):
            node = self.nodes[index]
            center = node['center']
            if center.dtype == np.float32:
                delta = np.maximum(np.abs(p - center) - np.float32(node['half']), np.float32(0))
                distance2 = np.sum(delta * delta, dtype=np.float32)
            else:
                delta = np.maximum(np.abs(p.astype(np.float64) - center) - np.float64(node['half']), 0.)
                distance2 = np.sum(delta * delta, dtype=np.float64)
            hit = np.float64(distance2) <= np.float64(radius) * np.float64(radius)
            visited.append([index, bool(hit)])
            if not hit:
                return
            if node['children']:
                for child in node['children']:
                    walk(child)
            elif node['ids'] is not None:
                for i in node['ids']:
                    # Match the old FP32 norm, then promote both scalar operands.
                    dist = norm32(self.points[i] - p)
                    if np.float64(dist) <= np.float64(radius):
                        found.append(int(i))
        walk(self.root)
        return found, visited


def merge_decisions(old_positions, old_normals, old_radii, new_positions, new_normals, new_radii, threshold=None):
    r = merge_threshold(old_radii, new_radii)
    use_r = r if threshold is None else float(threshold)
    tree = LegacyTree(old_positions)
    rows = []
    for p, n in zip(new_positions, new_normals):
        neighbors, visited = tree.query(p, use_r)
        dots = [float(np.dot(np.asarray(old_normals[i], dtype=np.float32), np.asarray(n, dtype=np.float32))) for i in neighbors]
        eligible = [i for i, value in zip(neighbors, dots) if np.float64(value) > np.float64(.6)]
        rows.append(dict(neighbor_indices=neighbors, normal_dots=dots,
                         chosen_old_id=eligible[0] if eligible else None, visited=visited))
    return r, rows, tree


def render_reference(positions, normals, radii, pose, focal, pp, width=512, height=288):
    """Independent component projection and vectorized parity rasterization.

    Original average vertex depth (not plane intersection), integer pixels, and
    legacy float64-vs-FP32 strict comparison are all intentionally retained.
    """
    positions = np.asarray(positions, dtype=np.float32)
    normals = np.asarray(normals, dtype=np.float32)
    radii = np.asarray(radii, dtype=np.float32)
    pose = np.asarray(pose, dtype=np.float32)
    result = dict(depth=np.zeros((height, width), dtype=np.float32),
                  surfel_index_map=np.full((height, width), -1, dtype=np.int32),
                  cos_value_map=np.zeros((height, width), dtype=np.float32))
    if not len(positions):
        return result, []
    z = np.full((height, width), np.inf, dtype=np.float32)
    inv = np.linalg.inv(pose[:3, :3]).astype(np.float32)
    translation = (-inv @ pose[:3, 3]).astype(np.float32)
    inv, translation = inv.astype(np.float64), translation.astype(np.float64)
    fx, fy = (np.float64(x) for x in focal)
    cx, cy = (np.float64(x) for x in pp)
    def transform(p):
        p = np.asarray(p, dtype=np.float64)
        return np.stack([p[..., 0] * inv[i, 0] + p[..., 1] * inv[i, 1] + p[..., 2] * inv[i, 2] + translation[i] for i in range(3)], axis=-1)
    cam = transform(positions)
    with np.errstate(divide='ignore', invalid='ignore'):
        u, v = fx * (cam[:, 0] / cam[:, 2]) + cx, fy * (cam[:, 1] / cam[:, 2]) + cy
    visible = (cam[:, 2] > .1) & (cam[:, 2] < 1000) & (u >= -50) & (u < width + 50) & (v >= -50) & (v < height + 50)
    angles = np.arange(16, dtype=np.float64) * (2 * math.pi / 16)
    cos_a, sin_a = np.cos(angles), np.sin(angles)
    diagnostics = []
    for sid in np.flatnonzero(visible):
        p = positions[sid]
        n = normals[sid].astype(np.float64)
        length = np.linalg.norm(n)
        row = dict(surfel_id=int(sid), center_z=float(cam[sid, 2]), normal_length=float(length))
        if length < 1e-12:
            row['status'] = 'ZERO_NORMAL'; diagnostics.append(row); continue
        n /= length
        view = p - pose[:3, 3]
        view /= norm32(view)
        cosine = float(np.dot(view.astype(np.float64), n))
        row['cosine'] = cosine
        if cosine < 0:
            row['status'] = 'BACKFACE'; diagnostics.append(row); continue
        up = np.array([0., 1., 0.]) if abs(n[2]) > .9 else np.array([0., 0., 1.])
        axis_x = cross_components(n, up); axis_x /= np.linalg.norm(axis_x)
        axis_y = cross_components(n, axis_x); axis_y /= np.linalg.norm(axis_y)
        offsets = np.float64(radii[sid]) * (cos_a[:, None] * axis_x + sin_a[:, None] * axis_y)
        circle = transform(p.astype(np.float64) + offsets)
        valid = circle[:, 2] > 0
        if np.count_nonzero(valid) < 3:
            row['status'] = 'FEWER_THAN_THREE_VERTICES'; diagnostics.append(row); continue
        vertices = np.column_stack((fx * (circle[valid, 0] / circle[valid, 2]) + cx,
                                    fy * (circle[valid, 1] / circle[valid, 2]) + cy))
        x0, y0 = np.maximum(np.floor(vertices.min(0)), 0).astype(np.int64)
        x1, y1 = np.minimum(np.ceil(vertices.max(0)), [width - 1, height - 1]).astype(np.int64)
        mean_depth = float(np.mean(circle[valid, 2], dtype=np.float64))
        row.update(status='RASTERIZED', average_depth=mean_depth, bbox=[int(x0), int(y0), int(x1), int(y1)])
        if x0 > x1 or y0 > y1:
            row['covered_pixels'] = row['written_pixels'] = 0; diagnostics.append(row); continue
        yy, xx = np.mgrid[y0:y1 + 1, x0:x1 + 1]
        inside = np.zeros_like(xx, dtype=bool)
        previous = vertices[-1]
        for current in vertices:
            crossing = (current[1] > yy) != (previous[1] > yy)
            edge = (previous[0] - current[0]) * (yy - current[1]) / (previous[1] - current[1] + 1e-15) + current[0]
            inside ^= crossing & (xx < edge)
            previous = current
        old = z[y0:y1 + 1, x0:x1 + 1]
        # Explicit NumPy1.26 *scalar* comparison semantics, not NumPy2 array promotion.
        update = inside & (np.float64(mean_depth) < old.astype(np.float64))
        old[update] = np.float32(mean_depth)
        result['surfel_index_map'][y0:y1 + 1, x0:x1 + 1][update] = sid
        result['cos_value_map'][y0:y1 + 1, x0:x1 + 1][update] = np.float32(cosine)
        row.update(covered_pixels=int(inside.sum()), written_pixels=int(update.sum()))
        diagnostics.append(row)
    z[np.isinf(z)] = 0
    result['depth'] = z
    return result, diagnostics


def vote_reference(render, sources):
    ids = np.asarray(render['surfel_index_map']).reshape(-1)
    depth = np.asarray(render['depth']).reshape(-1)
    cos = np.asarray(render['cos_value_map']).reshape(-1)
    weights, visits = {}, {}
    for i in np.flatnonzero(ids >= 0):
        if cos[i] < 0:
            continue
        value = np.float64(cos[i]) / (np.float64(1) + np.float64(depth[i]))
        for source in sources[int(ids[i])]:
            source = int(source)
            if source not in weights:
                weights[source] = value
                visits[source] = 0
            weights[source] = np.float64(weights[source]) + value
            visits[source] += 1
    if not weights:
        return dict(raw=[], weights=[], counts=[], pixel_visits=[], insertion_order=[])
    total = np.sum(np.asarray(list(weights.values()), dtype=np.float64), dtype=np.float64)
    if not np.isfinite(total) or total <= 0:
        raise ValueError('visible source weight sum is nonpositive or nonfinite')
    # Exactly 2 input sources => k<=2, original n=min(14,k)=k, one each.
    if len(weights) > 2:
        raise ValueError('S18 source domain exceeds frozen two frames')
    return dict(raw=[[i, float(weights[i])] for i in sorted(weights)],
                weights=[[i, float(weights[i] / total)] for i in sorted(weights)],
                counts=[[i, 1] for i in sorted(weights)],
                pixel_visits=[[i, visits[i]] for i in sorted(visits)],
                insertion_order=list(weights))
