#!/usr/bin/env python3
"""Score every S108 run and decompose by scene, window, arm and seed.

Metric math is copied verbatim from the contract-bound scorer (SHA 18e82e47...).
DEVELOPMENT scope.
"""
import io, json, math, statistics as st, sys
from collections import defaultdict
from pathlib import Path
import numpy as np, torch
from PIL import Image

RUNDIR = Path(sys.argv[1])
DATA = Path("/home/yliutz/datasets")
REL = {"scene_13": "heldout_3dmatch_scene13/extracted/rgbd-scenes-v2-scene_13",
       "scene_14": "heldout_3dmatch_scene14/extracted/rgbd-scenes-v2-scene_14"}

def require(v, m):
    if not v: raise RuntimeError(m)

def ref_grid(path):
    with Image.open(io.BytesIO(Path(path).read_bytes())) as im:
        rgb = np.asarray(im.convert("RGB"), dtype=np.uint8)
    require(rgb.shape == (480, 640, 3), f"native shape {rgb.shape}")
    t = torch.from_numpy(rgb.transpose(2, 0, 1).copy()).float().unsqueeze(0) / 255.0
    t = torch.nn.functional.interpolate(t, size=(576, 768), mode="area", antialias=False)[:, :, :, 96:672]
    return np.clip(t[0].permute(1, 2, 0).numpy() * 255.0, 0, 255).astype(np.uint8)

def pred_u8(frame):
    img = frame.transpose(1, 2, 0)
    if float(img.min()) < -0.1: img = (img + 1.0) / 2.0
    return np.clip(img * 255.0, 0, 255).astype(np.uint8)

receipt = json.loads((RUNDIR / "NMS_RECEIPT.json").read_text())
cache, rows = {}, []
for run in receipt["runs"]:
    scene, tgts = run["scene"], run["target_frame_ids"]
    seq = DATA / REL[scene] / "seq-01"
    arr = np.load(RUNDIR / f'{run["tag"]}.npy')
    require(arr.shape == (4, 3, 576, 576), f'{run["tag"]}: shape {arr.shape}')
    a = s = n = 0
    for i, fid in enumerate(tgts):
        key = (scene, fid)
        if key not in cache:
            cache[key] = ref_grid(seq / f"frame-{fid:06d}.color.png")
        d = pred_u8(arr[i]).astype(np.int64) - cache[key].astype(np.int64)
        a += int(np.abs(d).sum()); s += int((d * d).sum()); n += int(d.size)
    mse = s / (n * 255 * 255)
    rows.append({**{k: run[k] for k in ("tag", "scene", "window_start", "arm", "seed",
                                        "unique_context_frames")},
                 "mae_0_1": a / (n * 255), "mse_0_1": mse, "psnr_db": -10.0 * math.log10(mse)})

by_arm = defaultdict(list)
for r in rows: by_arm[r["arm"]].append(r["psnr_db"])
print(f"{'arm':20} {'n':>3} {'mean':>8} {'sd':>7} {'min':>8} {'max':>8}")
arm_stats = {}
for arm, v in sorted(by_arm.items(), key=lambda kv: -st.mean(kv[1])):
    arm_stats[arm] = {"n": len(v), "mean_psnr_db": st.mean(v),
                      "sd_db": st.stdev(v) if len(v) > 1 else 0.0,
                      "min": min(v), "max": max(v)}
    print(f"{arm:20} {len(v):3d} {st.mean(v):8.3f} {arm_stats[arm]['sd_db']:7.3f} {min(v):8.3f} {max(v):8.3f}")

# Paired within (scene, window, seed) so window difficulty cancels.
paired = defaultdict(dict)
for r in rows: paired[(r["scene"], r["window_start"], r["seed"])][r["arm"]] = r["psnr_db"]
print("\npaired contrasts within the same scene/window/seed:")
contrasts = {}
base = "static"
for arm in sorted(by_arm):
    if arm == base: continue
    diffs = [v[arm] - v[base] for v in paired.values() if arm in v and base in v]
    if not diffs: continue
    m = st.mean(diffs); sd = st.stdev(diffs) if len(diffs) > 1 else 0.0
    pos = sum(1 for d in diffs if d > 0)
    contrasts[f"{arm}_minus_{base}"] = {"n_pairs": len(diffs), "mean_db": m, "sd_db": sd,
                                        "n_positive": pos, "consistent_sign": pos in (0, len(diffs))}
    print(f"  {arm:20} - {base}: {m:+7.3f} dB  sd {sd:6.3f}  n={len(diffs):3d}  "
          f"positive {pos}/{len(diffs)}{'  CONSISTENT' if pos in (0, len(diffs)) else ''}")

out = {"schema": "s111-nms-scores-v1", "n_runs": len(rows),
       "scope": "development only; RGB only; no geometry; exposed development data",
       "per_arm": arm_stats, "paired_contrasts_vs_content_recent": contrasts, "rows": rows,
       "new_method_validated": False, "novelty_authorization": "NONE"}
(RUNDIR / "NMS_SCORES.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
print(f"\nscored {len(rows)} runs")
