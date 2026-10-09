"""Synthetic checks for KPS sigma recovery (run: python -m pytest work/S135_scale_init/test_kps.py -q)."""
import sys
from pathlib import Path
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent))
from kps import estimate_sigma, pixel_grid


def rot(axis, deg):
    a = np.deg2rad(deg); axis = np.asarray(axis, float); axis /= np.linalg.norm(axis)
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K


def make_view(sigma_true, baseline, depth, deg, noise_px, rng, H=96, W=128, f=110.0):
    """Points seen by view j at given metric depth; returned in view-0 frame scaled by sigma_true (CUT3R units)."""
    pix = pixel_grid(H, W).reshape(-1, 2)
    pp = np.array([W / 2, H / 2])
    z = depth * (1 + 0.3 * rng.random(len(pix)))
    xj = np.c_[(pix - pp) / f * z[:, None], z]                    # metric, camera j
    R = rot([0.3, 1, 0.1], deg); t = rng.normal(size=3); t = baseline * t / np.linalg.norm(t)
    # x_j = R X0 + t  ->  X0 = R^T (x_j - t)
    X0 = (xj - t) @ R
    P = sigma_true * X0 + rng.normal(scale=noise_px / f * depth * sigma_true, size=X0.shape)
    return {'P': P, 'pix': pix, 'R': R, 't': t, 'pp': pp}


@pytest.mark.parametrize('sigma_true', [0.02, 0.7, 1.5, 40.0])
@pytest.mark.parametrize('baseline', [0.03, 0.08])
def test_recovers_sigma_short_baseline(sigma_true, baseline):
    rng = np.random.default_rng(1)
    views = [make_view(sigma_true, baseline, 1.5, d, 1.0, rng) for d in (2, 4, 6, 8)]
    sigma, focals, err, _ = estimate_sigma(views)
    assert abs(np.log(sigma / sigma_true)) < np.log(1.15), (sigma, sigma_true)
    assert all(abs(f - 110.0) / 110.0 < 0.1 for f in focals)


def test_pure_rotation_is_flagged_by_flat_curve():
    rng = np.random.default_rng(2)
    views = [make_view(1.0, 1e-6, 1.5, d, 1.0, rng) for d in (2, 4)]
    _, _, _, curve = estimate_sigma(views, refine=False)
    # with no baseline the scale is unidentifiable: the residual curve is flat over the small-sigma range
    assert np.ptp(curve[:150]) < 0.05 * np.median(curve[:150]) + 1e-3
