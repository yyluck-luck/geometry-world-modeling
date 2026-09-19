#!/usr/bin/env python3
"""Rdist / Tdist: the standard camera-alignment metric for this task line.

Adopted, not invented.  Definition follows VMem (arXiv 2506.18903v3, Sec. 4.1),
which in turn follows CameraCtrl (arXiv 2404.02101):

  * extract camera poses from the GENERATED views with a geometry model
    (VMem uses DUSt3R, CVPR 2024; this stack has CUT3R, its successor)
  * express every pose RELATIVE TO THE FIRST FRAME
  * NORMALIZE TRANSLATION BY THE FURTHEST FRAME
  * Rdist = arccos(0.5 * (trace(R_gen @ R_gt^T) - 1))
  * Tdist = || t_gt - t_gen ||_2

Why this is the primary geometric metric and the project's own reprojection
consistency is only secondary (principle v2.13):

  - it is comparable with published numbers; the reprojection metric is not
  - it has no trivial optimum; a flat image yields meaningless poses rather
    than a perfect score (the reprojection metric scores a constant grey image
    0.000, better than real frames at 8.716)
  - it measures whether the generator OBEYED the commanded camera, which is the
    defining task of camera-conditioned generation

Declared weakness of the standard metric, kept explicit per principle v2.13
item 5: it runs a geometry estimator on generated frames.  Because CUT3R is
also inside this project's memory arm, a shared-source bias is possible and any
memory-versus-static comparison on this metric must state it.  VMem's own use
of DUSt3R carries the same class of dependence.
"""
import json, math, sys
from pathlib import Path
import numpy as np


def relative_to_first(c2ws):
    """Express every pose relative to frame 0 (CameraCtrl / VMem convention)."""
    inv0 = np.linalg.inv(c2ws[0])
    return np.stack([inv0 @ c for c in c2ws])


def normalize_by_furthest(rel):
    """Scale translations so the furthest frame sits at unit distance."""
    t = rel[:, :3, 3]
    scale = float(np.max(np.linalg.norm(t, axis=1)))
    if scale <= 1e-9:
        return rel.copy(), 0.0
    out = rel.copy()
    out[:, :3, 3] = t / scale
    return out, scale


def rdist_deg(R_gen, R_gt):
    c = (np.trace(R_gen @ R_gt.T) - 1.0) / 2.0
    return float(np.degrees(np.arccos(np.clip(c, -1.0, 1.0))))


def pose_alignment(gen_c2ws, gt_c2ws):
    """Return per-frame Rdist (deg) and Tdist after the declared normalisation."""
    gen = np.asarray(gen_c2ws, dtype=np.float64)
    gt = np.asarray(gt_c2ws, dtype=np.float64)
    if gen.shape != gt.shape:
        raise ValueError(f"pose count mismatch: {gen.shape} vs {gt.shape}")
    gen_n, gen_scale = normalize_by_furthest(relative_to_first(gen))
    gt_n, gt_scale = normalize_by_furthest(relative_to_first(gt))
    rd = [rdist_deg(gen_n[i, :3, :3], gt_n[i, :3, :3]) for i in range(len(gen_n))]
    td = [float(np.linalg.norm(gt_n[i, :3, 3] - gen_n[i, :3, 3])) for i in range(len(gen_n))]
    return {"per_frame_rdist_deg": rd, "per_frame_tdist": td,
            "rdist_deg": float(np.mean(rd[1:])) if len(rd) > 1 else float(rd[0]),
            "tdist": float(np.mean(td[1:])) if len(td) > 1 else float(td[0]),
            "gen_normalisation_scale": gen_scale, "gt_normalisation_scale": gt_scale,
            "note": "frame 0 is the gauge origin and is excluded from the means"}


def self_test():
    """Controls declared before use, mirroring the evaluator control discipline."""
    rng = np.random.RandomState(0)
    gt = []
    for i in range(4):
        a = 0.2 * i
        R = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
        T = np.eye(4); T[:3, :3] = R; T[:3, 3] = [0.5 * i, 0.1 * i, 0.0]
        gt.append(T)
    gt = np.stack(gt)

    exact = pose_alignment(gt, gt)
    # A rigid change of world frame must not alter the metric: it is gauge-free.
    G = np.eye(4); G[:3, 3] = [3.0, -2.0, 1.0]
    ang = 0.7
    G[:3, :3] = np.array([[math.cos(ang), 0, math.sin(ang)], [0, 1, 0], [-math.sin(ang), 0, math.cos(ang)]])
    moved = pose_alignment(np.stack([G @ c for c in gt]), gt)
    # A uniform scale change must not alter it either, because of the declared
    # furthest-frame normalisation.
    S = gt.copy(); S[:, :3, 3] *= 7.3
    scaled = pose_alignment(S, gt)
    noisy = gt.copy(); noisy[:, :3, 3] += rng.normal(0, 0.25, (4, 3))
    noise = pose_alignment(noisy, gt)

    checks = [
        ("identical poses give zero error", exact["rdist_deg"] < 1e-9 and exact["tdist"] < 1e-9),
        ("invariant to a rigid world transform", moved["rdist_deg"] < 1e-6 and moved["tdist"] < 1e-6),
        ("invariant to uniform scale after normalisation", scaled["tdist"] < 1e-9),
        ("perturbed poses score worse than exact", noise["tdist"] > exact["tdist"] + 1e-6),
    ]
    for name, ok in checks:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    print(json.dumps({"exact": {k: exact[k] for k in ('rdist_deg', 'tdist')},
                      "rigid_moved": {k: moved[k] for k in ('rdist_deg', 'tdist')},
                      "scaled": {k: scaled[k] for k in ('rdist_deg', 'tdist')},
                      "noisy": {k: noise[k] for k in ('rdist_deg', 'tdist')}}, indent=2))
    return 0 if all(ok for _, ok in checks) else 1


if __name__ == "__main__":
    raise SystemExit(self_test())
