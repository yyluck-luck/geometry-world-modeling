#!/usr/bin/env python3
"""Run S0. This is NOT an end-to-end VMem benchmark."""
import argparse
import csv
import hashlib
import itertools
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np
from memory_diagnostic import make_scene, corrupt, run_sequence, measure, render, as_surfels


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/memory_recovery_pilot.json")
    parser.add_argument("--out", type=Path, default=ROOT / "results/S0_memory_recovery")
    args = parser.parse_args()
    args.config = args.config.resolve()
    args.out = args.out.resolve()
    cfg = json.loads(args.config.read_text())
    args.out.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    rows = []
    factors = itertools.product(cfg["scenes"], cfg["corruptions"], cfg["levels"],
                                cfg["seeds"], cfg["orders"], cfg["extra_clean_reobservations"])
    for scene, kind, level, seed, order, repeats in factors:
        clean = make_scene(scene)
        noisy = corrupt(clean, kind, cfg[kind][level], seed, cfg["seed_jitter_fraction"])
        memory, provenance, trace = run_sequence(
            clean, noisy, order, repeats, cfg["surfel_radius_m"], cfg["normal_threshold"],
            cfg.get("max_points_per_node", 10)
        )
        row = dict(scene=scene, corruption=kind, level=level, seed=seed, order=order,
                   extra_clean_reobservations=repeats, input_count=len(clean) * (repeats + 2),
                   input_displacement_m=float(np.linalg.norm(noisy-clean, axis=1).mean()),
                   max_points_per_node=cfg.get("max_points_per_node", 10))
        row.update(measure(memory, clean, cfg["error_threshold_m"]))
        row["max_source_ids_per_surfel"] = max(map(len, provenance.values()))
        row["initial_surfel_max_position_change_m"] = float(np.max(np.linalg.norm(
            np.array([s.position for s in memory[:len(clean)]]) -
            (noisy if order == "noisy_first" else clean), axis=1)))
        rows.append(row)
        # Store full evidence for one representative pair, including the known GT.
        if scene == "plane" and kind == "depth_scale" and level == "small" and seed == 0 and repeats == 12:
            rendered = render(memory)
            gt_rendered = render(as_surfels(clean, cfg["surfel_radius_m"]))
            common = (rendered["depth"] > 0) & (gt_rendered["depth"] > 0)
            summary = {"render_coverage": float((rendered["depth"] > 0).mean()),
                       "reference_coverage": float((gt_rendered["depth"] > 0).mean()),
                       "common_pixels": int(common.sum()),
                       "common_depth_mae_m": float(np.abs(rendered["depth"][common]-gt_rendered["depth"][common]).mean()) if common.any() else None,
                       "caution": "Same upstream renderer; secondary diagnostic, not independent image-geometry GT or matched coverage proof."}
            np.savez_compressed(args.out / f"example_{order}.npz", gt_points=clean,
                                noisy_points=noisy, memory_points=np.array([s.position for s in memory]),
                                rendered_depth=rendered["depth"], reference_depth=gt_rendered["depth"],
                                memory_count_trace=np.array(trace))
            (args.out / f"example_{order}.json").write_text(json.dumps(summary, indent=2)+"\n")
    with (args.out / "runs.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    keys = ["corruption", "level", "order", "extra_clean_reobservations"]
    grouped = []
    for group in itertools.product(cfg["corruptions"], cfg["levels"], cfg["orders"], cfg["extra_clean_reobservations"]):
        selected = [r for r in rows if all(r[k] == v for k,v in zip(keys, group))]
        result = dict(zip(keys, group))
        result["n_synthetic_scene_seed_cells"] = len(selected)
        for metric in ["memory_count", "mean_memory_to_gt_m", "wrong_memory_fraction", "gt_landmark_recall_at_1cm"]:
            values = np.array([r[metric] for r in selected])
            result[metric] = float(values.mean())
            result[metric + "_min"] = float(values.min())
            result[metric + "_max"] = float(values.max())
        grouped.append(result)
    (args.out / "summary.json").write_text(json.dumps(grouped, indent=2)+"\n")
    sources = [*ROOT.glob("src/*.py"), Path(__file__), args.config,
               ROOT/"docs/S0_PROTOCOL.md", ROOT/"docs/S0b_AMENDMENT.md"]
    metadata = {"experiment_id": cfg["experiment_id"], "evidence_type": cfg["evidence_type"],
                "completed_utc": datetime.now(timezone.utc).isoformat(), "elapsed_seconds": time.perf_counter()-start,
                "python": sys.version, "platform": platform.platform(), "machine": platform.machine(),
                "numpy": np.__version__, "rows": len(rows), "config": cfg,
                "source_sha256": {str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p): sha(p) for p in sources},
                "upstream": json.loads((ROOT/"vendor/provenance.json").read_text()),
                "no_model_weights_loaded": True, "no_real_world_data_used": True}
    (args.out / "run_metadata.json").write_text(json.dumps(metadata, indent=2)+"\n")
    print(json.dumps({"rows": len(rows), "seconds": metadata["elapsed_seconds"], "out": str(args.out)}))


if __name__ == "__main__":
    main()
