#!/usr/bin/env python3
"""Aggregate C8 B/C/J masks by development window and join sealed scores."""
import argparse, json
from collections import defaultdict
from pathlib import Path
import numpy as np

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--scores", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    records = json.loads(Path(args.manifest).read_text())
    scores = json.loads(Path(args.scores).read_text())
    score_groups = defaultdict(list)
    for row in scores.get("rows", []):
        key = (row.get("scene"), int(row.get("window_start")), row.get("arm"))
        if row.get("psnr_db") is not None:
            score_groups[key].append(float(row["psnr_db"]))
    grouped = defaultdict(list)
    for rec in records:
        key = (rec.get("scene"), int(rec.get("window_start")), rec.get("arm"))
        grouped[key].append(rec)
    out = []
    for (scene, window_start, arm), rows in sorted(grouped.items()):
        def mean_mask(name):
            vals = [float(np.asarray(r[name], dtype=float).mean()) for r in rows if name in r]
            return float(np.mean(vals)) if vals else None
        b, c, j = (mean_mask(x) for x in ("B", "C", "J"))
        ps = score_groups.get((scene, window_start, arm), [])
        psnr = float(np.mean(ps)) if ps else None
        score_status = "JOINED" if ps else "UNTESTABLE_MISSING_SCORE"
        if len(rows) != 4:
            decision = "UNTESTABLE_INCOMPLETE_TARGETS"
        elif None in (b, c, j):
            decision = "UNTESTABLE_MISSING_MASK"
        elif b < .20:
            decision = "LOW_B_TRUE_SCARCITY"
        elif b >= .50 and j < .20:
            decision = "HIGH_B_LOW_J_INDEXING"
        elif b >= .50 and c < .20:
            decision = "HIGH_B_LOW_C_DELIVERY"
        elif c >= .50 and psnr is not None and psnr <= 16.0:
            decision = "HIGH_C_POOR_CONSUMPTION"
        else:
            decision = "INTERMEDIATE_OR_UNRESOLVED"
        out.append({"scene": scene, "window_start": window_start, "arm": arm,
                    "n_target_records": len(rows), "B_fraction": b,
                    "C_fraction": c, "J_fraction": j,
                    "sealed_psnr_db_mean": psnr, "n_score_rows": len(ps),
                    "score_status": score_status, "decision": decision})
    payload = {"schema": "c8-support-analysis-v2", "records": out,
               "new_method_validated": False, "novelty_authorization": "NONE"}
    Path(args.out).write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({"records": len(out), "out": args.out,
                      "new_method_validated": False,
                      "novelty_authorization": "NONE"}, indent=2))

if __name__ == "__main__":
    main()
