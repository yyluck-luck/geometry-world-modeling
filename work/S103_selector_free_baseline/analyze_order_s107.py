#!/usr/bin/env python3
"""Decompose the S107 arm scores into multiset effect and slot-order variance.

The question job 594717 raised: is a multiset contrast larger than the spread
produced by reordering the same multiset?  This reports both on the same scale
so the comparison is explicit rather than asserted.
"""
import json, math, statistics as st, sys
from pathlib import Path

scores = json.loads((Path(sys.argv[1]) / "ARM_SCORES.json").read_text())["arms"]
groups = {}
for arm, v in scores.items():
    ms = arm.split("__o")[0]
    groups.setdefault(ms, []).append((arm, v["aggregate"]["psnr_db"]))

print(f"{'multiset':18} {'n':>2} {'mean':>8} {'min':>8} {'max':>8} {'spread':>8} {'sd':>7}")
summary = {}
for ms, rows in sorted(groups.items()):
    vals = [p for _, p in rows]
    spread = max(vals) - min(vals)
    sd = st.stdev(vals) if len(vals) > 1 else 0.0
    summary[ms] = {"n": len(vals), "mean_psnr_db": st.mean(vals), "min": min(vals),
                   "max": max(vals), "order_spread_db": spread, "order_sd_db": sd,
                   "orderings": {a: p for a, p in sorted(rows)}}
    print(f"{ms:18} {len(vals):2d} {st.mean(vals):8.3f} {min(vals):8.3f} {max(vals):8.3f} {spread:8.3f} {sd:7.3f}")

print()
print("multiset contrasts on order-averaged values, judged against order spread:")
names = sorted(summary)
verdicts = {}
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        a, b = names[i], names[j]
        diff = summary[a]["mean_psnr_db"] - summary[b]["mean_psnr_db"]
        worst = max(summary[a]["order_spread_db"], summary[b]["order_spread_db"])
        ok = abs(diff) > worst
        verdicts[f"{a}_vs_{b}"] = {"mean_diff_db": diff, "max_order_spread_db": worst,
                                   "exceeds_order_spread": ok}
        print(f"  {a:18} - {b:18} = {diff:+7.3f} dB   order spread {worst:6.3f}   "
              f"{'EXCEEDS' if ok else 'within order noise'}")

out = {"schema": "s107-order-decomposition-v1",
       "scope": "development only; one window, one scene, one seed, RGB only",
       "per_multiset": summary, "contrasts": verdicts,
       "interpretation_rule": ("A multiset contrast is reportable only if its order-averaged "
                               "difference exceeds the largest slot-order spread among the "
                               "multisets being compared."),
       "new_method_validated": False, "novelty_authorization": "NONE"}
(Path(sys.argv[1]) / "ORDER_DECOMPOSITION.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
