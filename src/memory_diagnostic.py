"""Synthetic, post-filter diagnostics using the pinned VMem merge kernel."""
from contextlib import redirect_stdout
from io import StringIO
import numpy as np
from vmem_memory_kernel import MemoryKernel, Surfel


def make_scene(name):
    x, y = np.meshgrid(np.linspace(-0.75, 0.75, 6), np.linspace(-0.6, 0.6, 5))
    z = np.full_like(x, 4.0)
    if name == "depth_step":
        z[x > 0] = 4.6
    elif name != "plane":
        raise ValueError(f"Unknown scene: {name}")
    return np.stack([x, y, z], axis=-1).reshape(-1, 3)


def corrupt(points, kind, magnitude, seed, jitter_fraction):
    """Known sensor perturbation; GT is used only to construct this test fixture."""
    rng = np.random.default_rng(seed)
    displacement = magnitude * (1.0 + jitter_fraction * rng.uniform(-1, 1, len(points)))
    if kind == "depth_scale":
        return points * (1.0 + displacement[:, None])
    if kind == "pose_translation_x":
        # One coherent pose translation per frame, with seed-dependent magnitude.
        out = points.copy()
        out[:, 0] += displacement[0]
        return out
    raise ValueError(f"Unknown corruption: {kind}")


def as_surfels(points, radius):
    return [Surfel(p.copy(), np.array([0.0, 0.0, 1.0]), radius) for p in points]


def run_sequence(clean, noisy, order, extra_reobservations, radius, normal_threshold,
                 max_points_per_node=10):
    if order not in {"noisy_first", "clean_first"}:
        raise ValueError(order)
    frames = [noisy, clean] if order == "noisy_first" else [clean, noisy]
    frames += [clean] * extra_reobservations
    kernel, memory, provenance = MemoryKernel(), [], {}
    trace = []
    for timestep, points in enumerate(frames):
        candidates = as_surfels(points, radius)
        if memory:
            with redirect_stdout(StringIO()):
                candidates, provenance = kernel.merge_surfels(
                    candidates, timestep, memory, provenance,
                    normal_threshold=normal_threshold,
                    max_points_per_node=max_points_per_node,
                )
        start = len(memory)
        for i in range(len(candidates)):
            provenance[start + i] = [timestep]
        memory.extend(candidates)
        trace.append(len(memory))
    return memory, provenance, trace


def measure(memory, gt_points, threshold):
    points = np.array([s.position for s in memory])
    distances = np.linalg.norm(points[:, None, :] - gt_points[None, :, :], axis=-1)
    nearest_gt = distances.min(axis=1)
    nearest_memory = distances.min(axis=0)
    return {
        "memory_count": len(memory),
        "mean_memory_to_gt_m": float(nearest_gt.mean()),
        "max_memory_to_gt_m": float(nearest_gt.max()),
        "mean_gt_to_memory_m": float(nearest_memory.mean()),
        "wrong_memory_fraction": float((nearest_gt > threshold).mean()),
        "gt_landmark_recall_at_1cm": float((nearest_memory <= threshold).mean()),
    }


def render(memory):
    # Diagnostic view only: +8 cm camera translation, +z camera convention.
    pose = np.eye(4)
    pose[0, 3] = 0.08
    return MemoryKernel().render_surfels_to_image(
        memory, pose, [90.0, 90.0], [24.0, 18.0], 48, 36
    )
