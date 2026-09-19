#!/usr/bin/env python3
"""Audit the pinned Octree against a brute-force neighbor oracle on S0 inputs."""
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"src"))
from memory_diagnostic import make_scene, corrupt, run_sequence
from vmem_memory_kernel import Octree

rows = []
for scene in ["plane", "depth_step"]:
    for seed in [0, 1, 2]:
        clean = make_scene(scene)
        noisy = corrupt(clean, "pose_translation_x", 0.1, seed, 0.1)
        for max_points in [10, 100000]:
            memory, _, trace = run_sequence(clean, noisy, "noisy_first", 12, 0.045, 0.6, max_points)
            points = np.array([s.position for s in memory])
            tree = Octree(points, max_points=max_points)
            missing_self, mismatch = [], []
            for i, point in enumerate(points):
                expected = set(np.flatnonzero(np.linalg.norm(points-point, axis=1) <= 0.045).tolist())
                actual = set(tree.query_ball_point(point, 0.045))
                if i not in actual:
                    missing_self.append(i)
                if actual != expected:
                    mismatch.append(i)
            rows.append(dict(scene=scene, seed=seed, max_points_per_node=max_points,
                             memory_count_trace=trace, final_memory_count=len(memory),
                             missing_self_count=len(missing_self), neighbor_mismatch_count=len(mismatch)))
out = ROOT/"results/spatial_index_audit.json"
out.write_text(json.dumps({"scope":"synthetic diagnostic; brute-force oracle; no production prevalence claim",
                           "upstream_commit":"39291e4f272f6b4f270691d930926ab5930f942e", "cases":rows},indent=2)+"\n")
print(json.dumps({"cases":len(rows), "out":str(out)}))
