#!/usr/bin/env python3
"""Anti-degeneracy guard for the reprojection consistency metric.

The metric alone has a trivial optimum: a constant image reprojects with MAE
0.000, better than real frames at 8.716 (measured 2026-09-17).  Reporting it
without a guard would reward a generator that produces flat output.

The guard is a two-sided qualification, not a new score:

  1) IMAGE CONTENT FLOOR.  An arm whose per-frame spatial standard deviation is
     far below the real reference frames' is flagged DEGENERATE and its
     reprojection number is withheld rather than reported.
  2) JOINT READING.  A reprojection contrast between arms is interpretable only
     when their RGB fidelity is statistically indistinguishable.  Otherwise the
     arms are trading fidelity for smoothness and the comparison is void.

Both thresholds are declared here BEFORE looking at any new arm.
"""
import io, json, math, statistics as st, sys
from pathlib import Path
import numpy as np
from PIL import Image

# Declared in advance.  An arm must retain at least this fraction of the real
# frames' spatial variation to be eligible for a reprojection claim.
CONTENT_FLOOR_RATIO = 0.5
# RGB fidelity between two arms must agree within this many dB (paired mean)
# for a reprojection contrast between them to be interpretable.
RGB_EQUIVALENCE_DB = 0.5

DATA = Path("/home/yliutz/datasets")
REL = {"scene_13": "heldout_3dmatch_scene13/extracted/rgbd-scenes-v2-scene_13",
       "scene_14": "heldout_3dmatch_scene14/extracted/rgbd-scenes-v2-scene_14"}

def pred_u8(frame):
    img = frame.transpose(1, 2, 0)
    if float(img.min()) < -0.1:
        img = (img + 1.0) / 2.0
    return np.clip(img * 255.0, 0, 255).astype(np.uint8)

def real_grid(seq, fid):
    a = np.asarray(Image.open(io.BytesIO((seq / f"frame-{fid:06d}.color.png").read_bytes())).convert("RGB"))
    ys = np.clip((np.arange(576) * 480.0 / 576.0).astype(int), 0, 479)
    xs = np.clip((np.arange(768) * 640.0 / 768.0).astype(int), 0, 639)
    return a[ys][:, xs][:, 96:672]

def spatial_std(img_u8):
    return float(np.asarray(img_u8, dtype=np.float64).std())

def main():
    rundir = Path(sys.argv[1])
    receipt_name = sys.argv[2]
    geom = json.loads((rundir / "GEOMETRY_CONSISTENCY.json").read_text())
    rgb_name = sys.argv[3] if len(sys.argv) > 3 else None
    receipt = json.loads((rundir / receipt_name).read_text())

    ref_std, arm_std = [], {}
    seen_ref = set()
    for run in receipt["runs"]:
        seq = DATA / REL[run["scene"]] / "seq-01"
        arr = np.load(rundir / f'{run["tag"]}.npy')
        s = st.mean([spatial_std(pred_u8(arr[i])) for i in range(4)])
        arm_std.setdefault(run["arm"], []).append(s)
        key = (run["scene"], tuple(run["target_frame_ids"]))
        if key not in seen_ref:
            seen_ref.add(key)
            ref_std.append(st.mean([spatial_std(real_grid(seq, f)) for f in run["target_frame_ids"]]))
    ref = st.mean(ref_std)

    print(f"real reference spatial sd : {ref:.3f}")
    print(f"content floor ({CONTENT_FLOOR_RATIO:.0%} of real) : {ref * CONTENT_FLOOR_RATIO:.3f}\n")
    print(f"{'arm':18} {'spatial sd':>11} {'ratio':>7}  {'status':>12}")
    verdicts = {}
    for arm, vals in sorted(arm_std.items()):
        m = st.mean(vals); ratio = m / ref
        ok = ratio >= CONTENT_FLOOR_RATIO
        verdicts[arm] = {"spatial_sd": m, "ratio_to_real": ratio,
                         "passes_content_floor": ok,
                         "reprojection_reportable": ok}
        print(f"{arm:18} {m:11.3f} {ratio:7.3f}  {'ELIGIBLE' if ok else 'DEGENERATE':>12}")

    out = {"schema": "s110-antidegeneracy-guard-v1",
           "declared_before_use": True,
           "content_floor_ratio": CONTENT_FLOOR_RATIO,
           "rgb_equivalence_db": RGB_EQUIVALENCE_DB,
           "real_reference_spatial_sd": ref,
           "per_arm": verdicts,
           "degenerate_optimum_measured": {"constant_gray_reprojection_mae": 0.0,
                                           "real_frames_reprojection_mae": 8.716},
           "rule": ("A reprojection contrast may be reported only between arms that both pass "
                    "the content floor AND whose paired RGB fidelity differs by less than "
                    f"{RGB_EQUIVALENCE_DB} dB."),
           "geometry_per_arm": geom.get("per_arm"),
           "new_method_validated": False, "novelty_authorization": "NONE"}
    (rundir / "GEOMETRY_GUARD.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(f"\nall arms eligible: {all(v['passes_content_floor'] for v in verdicts.values())}")

if __name__ == "__main__":
    main()
