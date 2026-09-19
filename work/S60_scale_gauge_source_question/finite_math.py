"""One artificial source-formula counterexample; no real arrays or model imports."""
from datetime import datetime, timezone
import json
from pathlib import Path
import numpy as np


def center_and_z(centers, axes):
    distances = [np.linalg.norm(a - b) for i, a in enumerate(centers)
                 for b in centers[i + 1:]]
    eps = max(float(np.median(distances)) / 100, 1e-6)
    return np.concatenate((centers, centers + eps * axes)), eps


angles = np.deg2rad(np.array([0, 1.25, 2.5, 3.75, 5.0]))
axes = np.stack((np.sin(angles), np.zeros(5), np.cos(angles)), axis=1)
source_centers = np.stack((0.001 * np.arange(5), np.zeros(5), np.zeros(5)), axis=1)
target_centers = np.zeros((5, 3))
source, source_eps = center_and_z(source_centers, axes)
target, target_eps = center_and_z(target_centers, axes)
a, b = source - source.mean(axis=0), target - target.mean(axis=0)
u, singular, vt = np.linalg.svd(a.T @ b)
sign = np.diag([1.0, 1.0, np.linalg.det(u @ vt)])
rotation_row = u @ sign @ vt
scale = float(np.sum(singular * np.diag(sign)) / np.sum(a * a))
translation = target.mean(axis=0) - scale * source.mean(axis=0) @ rotation_row
residual = scale * source @ rotation_row + translation - target

# Source l1_dist is weighted Euclidean point distance, homogeneous of degree 1.
x = np.array([[1.0, 0.0, 2.0], [-0.2, 0.1, 1.0]])
y = np.array([[0.8, 0.1, 1.9], [-0.1, 0.0, 1.2]])
weights = np.array([2.0, 3.0])
base_loss = float(np.sum(np.linalg.norm(x - y, axis=1) * weights))
half_loss = float(np.sum(np.linalg.norm(0.5 * x - 0.5 * y, axis=1) * weights))
assert np.isclose(half_loss, 0.5 * base_loss, atol=1e-14, rtol=0)
record = {
    "schema": "s60-finite-artificial-scale-math-v1",
    "completed_utc": datetime.now(timezone.utc).isoformat(),
    "evidence_kind": "ARTIFICIAL_NUMPY_FORMULA_COUNTEREXAMPLE_NOT_C2_REPLAY",
    "source_center_x": source_centers[:, 0].tolist(),
    "source_and_target_yaws_degrees": np.rad2deg(angles).tolist(),
    "target_centers_all_zero": True,
    "source_epsilon": source_eps,
    "target_epsilon": target_eps,
    "least_squares_similarity_scale_before_source_fallback": scale,
    "source_fallback_abs_s_lt_1e_6_would_trigger": abs(scale) < 1e-6,
    "least_squares_fit_RMSE": float(np.sqrt(np.mean(residual ** 2))),
    "joint_euclidean_loss": base_loss,
    "joint_half_scale_loss": half_loss,
    "joint_half_scale_loss_ratio": half_loss / base_loss,
    "scope": "Demonstrates that epsilon-based initialization can choose a tiny scale without triggering its fallback, and an all-depth-free homogeneous objective permits common shrinkage. Neither proves C2's actual scale, optimizer trajectory, or cause.",
    "real_payload_or_pixels_read": 0,
    "model_or_torch_calls": 0,
}
Path(__file__).with_name("FINITE_MATH_RECEIPT.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record, indent=2))
