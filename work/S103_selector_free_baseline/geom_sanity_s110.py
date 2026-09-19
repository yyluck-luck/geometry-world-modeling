#!/usr/bin/env python3
"""Positive/negative controls for the reprojection evaluator.

An evaluator that cannot separate real frames from shuffled ones is useless.
  REAL      : the actual dataset frames at the target poses -> should be LOW
  SHUFFLED  : the same frames assigned to the wrong poses   -> should be HIGH
If REAL is not clearly lower than SHUFFLED, the metric is not measuring geometry.
"""
import io, json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, "/home/yliutz/geometry-world-modeling/work/S103_selector_free_baseline")
from geom_eval_s110 import model_grid_K, depth_to_model_grid, load_pose, reproject_pair  # noqa
from PIL import Image

DATA = Path("/home/yliutz/datasets")
SEQ = DATA / "heldout_3dmatch_scene13/extracted/rgbd-scenes-v2-scene_13/seq-01"
ROOT = SEQ.parent
TGTS = [60, 75, 90, 105]

K = np.loadtxt(io.StringIO((ROOT / "camera-intrinsics.txt").read_text()), dtype=np.float64).reshape(3, 3)
Kg = model_grid_K(K)

def real_rgb(fid):
    a = np.asarray(Image.open(io.BytesIO((SEQ / f"frame-{fid:06d}.color.png").read_bytes())).convert("RGB"))
    ys = np.clip((np.arange(576) * 480.0 / 576.0).astype(int), 0, 479)
    xs = np.clip((np.arange(768) * 640.0 / 768.0).astype(int), 0, 639)
    return a[ys][:, xs][:, 96:672]

imgs = [real_rgb(f) for f in TGTS]
poses = [load_pose(SEQ, f) for f in TGTS]
depths = [depth_to_model_grid(SEQ / f"frame-{f:06d}.depth.png") for f in TGTS]

def run(image_list, label):
    maes, covs = [], []
    for a in range(4):
        for b in range(4):
            if a == b: continue
            r = reproject_pair(image_list[a], image_list[b], depths[b], Kg, poses[a], poses[b])
            if r["mae_0_255"] is not None:
                maes.append(r["mae_0_255"]); covs.append(r["coverage"])
    m = float(np.mean(maes)); c = float(np.mean(covs))
    print(f"{label:28} MAE {m:8.3f}   coverage {c:.3f}   pairs {len(maes)}")
    return m, c

real_mae, cov = run(imgs, "REAL frames at true poses")
shuf_mae, _ = run([imgs[2], imgs[3], imgs[0], imgs[1]], "SHUFFLED frame-pose pairing")
noise = [np.random.RandomState(0).randint(0, 256, imgs[0].shape, dtype=np.uint8) for _ in range(4)]
noise_mae, _ = run(noise, "RANDOM noise images")

ok = real_mae < shuf_mae and real_mae < noise_mae
print(f"\nseparation real<shuffled: {real_mae:.3f} < {shuf_mae:.3f} = {real_mae < shuf_mae}")
print(f"separation real<noise   : {real_mae:.3f} < {noise_mae:.3f} = {real_mae < noise_mae}")
print(f"\nEVALUATOR CONTROL: {'PASS' if ok else 'FAIL'}")
json.dump({"real_mae": real_mae, "shuffled_mae": shuf_mae, "noise_mae": noise_mae,
           "mean_coverage": cov, "control_passed": bool(ok),
           "note": "real frames must reproject more consistently than mismatched or random ones"},
          open("/home/yliutz/gwm_probe_receipts/EVALUATOR_CONTROL.json", "w"), indent=2)
