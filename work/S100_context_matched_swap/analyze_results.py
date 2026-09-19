#!/usr/bin/env python3
"""Analyze sealed S100 score rows without reading any new GT bytes."""
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
src = ROOT / "score_01/SCORES.json"
out = ROOT / "score_01/MECHANISM_ANALYSIS.json"
data = json.loads(src.read_text())
rows = data["rows"]

# Each condition has an arm and each pair/context/target has both arms.
by_key = defaultdict(dict)
for r in rows:
    key = (r["pair_id"], r["source"], r["context"], r["target"])
    by_key[key][r["arm"]] = r

caps = ["0.5", "1.0", "2.0"]
benefits = defaultdict(list)
for key, arms in by_key.items():
    if set(arms) != {"low", "conf"}:
        continue
    for cap in caps:
        benefits[cap].append({
            "pair_id": key[0], "source": key[1], "context": key[2], "target": key[3],
            "benefit": arms["low"]["caps"][cap]["mean"] - arms["conf"]["caps"][cap]["mean"],
        })

source_summary = {}
for cap in caps:
    groups = defaultdict(list)
    for row in benefits[cap]:
        groups[row["source"]].append(row["benefit"])
    source_summary[cap] = {
        str(source): {
            "n_pair_context_target": len(vals),
            "mean_benefit": sum(vals) / len(vals),
            "positive_count": sum(v > 0 for v in vals),
            "negative_count": sum(v < 0 for v in vals),
            "zero_count": sum(v == 0 for v in vals),
        }
        for source, vals in sorted(groups.items())
    }

out.write_text(json.dumps({
    "schema": "S100-mechanism-analysis-v1",
    "created_utc": datetime.now(timezone.utc).isoformat(),
    "input_scores": str(src),
    "rows_used": len(rows),
    "benefit_rows": {cap: len(benefits[cap]) for cap in caps},
    "source_summary": source_summary,
    "interpretation": "Descriptive analysis of sealed, previously scored data; no new GT read, no new model inference, no claim of causal interaction or method validation.",
}, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"status": "PASS", "rows_used": len(rows), "benefit_rows": {c: len(benefits[c]) for c in caps}}))
