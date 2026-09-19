#!/usr/bin/env python3
"""Contrast-invariant form of the cross-view consistency metric.

An external review (2026-09-17) gave a counterexample: for a fixed valid mask
and linear warping, replacing every prediction by  I' = a*I + b  scales the warp
error by |a|, so lowering contrast lowers the error with no geometric change.

Measured on real frames, the counterexample holds to 0.2%:
    a=1.00 -> 8.716   a=0.80 -> 6.984   a=0.60 -> 5.218   a=0.25 -> 2.170
and the previously declared 0.5 spatial-sd floor PASSED a=0.6, i.e. it let a
40% spurious improvement through.

The invariant form divides by the predictions' own spatial standard deviation:
    a=1.00 -> 0.1638  a=0.80 -> 0.1638  a=0.60 -> 0.1634  a=0.25 -> 0.1635
which is stable to 0.3% across a 4x contrast range.

Reported as `reproj_mae_per_sd`.  The raw MAE and the spatial sd are both kept
so nothing is hidden and the raw number stays auditable.
"""
import json, statistics as st, sys
from collections import defaultdict
from pathlib import Path
import numpy as np


def pred_u8(frame):
    img = frame.transpose(1, 2, 0)
    if float(img.min()) < -0.1:
        img = (img + 1.0) / 2.0
    return np.clip(img * 255.0, 0, 255).astype(np.uint8)


def main():
    rundir = Path(sys.argv[1])
    receipt_name = sys.argv[2]
    geom = json.loads((rundir / "GEOMETRY_CONSISTENCY.json").read_text())
    receipt = json.loads((rundir / receipt_name).read_text())

    sd_by_tag = {}
    for run in receipt["runs"]:
        arr = np.load(rundir / f'{run["tag"]}.npy')
        sd_by_tag[run["tag"]] = st.mean(
            [float(np.asarray(pred_u8(arr[i]), dtype=np.float64).std()) for i in range(4)])

    rows = []
    for r in geom["rows"]:
        sd = sd_by_tag.get(r["tag"])
        mae = r.get("reprojection_mae_0_255")
        if sd is None or mae is None or sd <= 1e-9:
            continue
        rows.append({**r, "spatial_sd": sd, "reproj_mae_per_sd": mae / sd})

    by_arm = defaultdict(list)
    for r in rows:
        by_arm[r["arm"]].append(r)
    print(f"{'arm':18} {'n':>3} {'raw MAE':>9} {'sd':>8} {'MAE/sd':>9}   (lower = better)")
    per_arm = {}
    for arm, v in sorted(by_arm.items(), key=lambda kv: st.mean([x["reproj_mae_per_sd"] for x in kv[1]])):
        raw = st.mean([x["reprojection_mae_0_255"] for x in v])
        sd = st.mean([x["spatial_sd"] for x in v])
        norm = st.mean([x["reproj_mae_per_sd"] for x in v])
        nsd = st.stdev([x["reproj_mae_per_sd"] for x in v]) if len(v) > 1 else 0.0
        per_arm[arm] = {"n": len(v), "raw_mae": raw, "spatial_sd": sd,
                        "reproj_mae_per_sd": norm, "sd_of_normalised": nsd}
        print(f"{arm:18} {len(v):3d} {raw:9.3f} {sd:8.3f} {norm:9.4f}")

    paired = defaultdict(dict)
    for r in rows:
        paired[(r["scene"], r["window_start"], r["seed"])][r["arm"]] = r["reproj_mae_per_sd"]
    arms = sorted(by_arm)
    contrasts = {}
    print("\npaired, contrast-invariant:")
    for i in range(len(arms)):
        for j in range(len(arms)):
            if i >= j: continue
            a, b = arms[i], arms[j]
            d = [v[a] - v[b] for v in paired.values() if a in v and b in v]
            if not d: continue
            m = st.mean(d); s = st.stdev(d) if len(d) > 1 else 0.0
            neg = sum(1 for x in d if x < 0)
            contrasts[f"{a}_minus_{b}"] = {"n_pairs": len(d), "mean": m, "sd": s,
                                           "se": s / (len(d) ** 0.5) if len(d) > 1 else None,
                                           "n_first_better": neg}
            print(f"  {a:18} - {b:18} = {m:+.4f}  sd {s:.4f}  n={len(d):3d}  first better {neg}/{len(d)}")

    out = {"schema": "s110-contrast-invariant-consistency-v1",
           "reason": ("raw warp MAE scales linearly with image contrast; an external review's "
                      "counterexample was reproduced to 0.2% and the 0.5 spatial-sd floor passed "
                      "a 0.6 contrast scaling that improved the raw metric by 40%"),
           "invariant_definition": "reprojection MAE divided by the predictions' spatial standard deviation",
           "measured_invariance": {"a=1.00": 0.1638, "a=0.80": 0.1638, "a=0.60": 0.1634, "a=0.25": 0.1635},
           "per_arm": per_arm, "paired_contrasts": contrasts, "rows": rows,
           "still_not_a_physical_geometry_truth_metric": True,
           "new_method_validated": False, "novelty_authorization": "NONE"}
    (rundir / "GEOMETRY_CONTRAST_INVARIANT.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
