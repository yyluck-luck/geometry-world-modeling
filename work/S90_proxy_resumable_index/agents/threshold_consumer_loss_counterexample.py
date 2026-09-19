#!/usr/bin/env python3
"""Minimal synthetic counterexample: risk-threshold tightening need not
monotonically improve the consumer's future loss. Not a model/data experiment.
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "threshold_consumer_loss_counterexample_results.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    started = datetime.now(timezone.utc)
    # k=1. A has more utility/information but larger estimated geometry risk;
    # B is lower-risk yet is a worse match for the held-out future state.
    candidates = {
        "A": {"estimated_risk": 0.20, "utility": 1.0, "future_loss": 0.10},
        "B": {"estimated_risk": 0.05, "utility": 0.6, "future_loss": 0.60},
    }
    # Loose threshold admits A; tight threshold rejects A and admits B.
    loose_tau = 0.20
    tight_tau = 0.05

    def select(tau: float) -> str:
        eligible = [
            name for name, row in candidates.items() if row["estimated_risk"] <= tau
        ]
        if not eligible:
            raise AssertionError("empty eligible set")
        return max(eligible, key=lambda name: candidates[name]["utility"])

    loose_choice = select(loose_tau)
    tight_choice = select(tight_tau)
    loose_loss = candidates[loose_choice]["future_loss"]
    tight_loss = candidates[tight_choice]["future_loss"]
    assert loose_choice == "A"
    assert tight_choice == "B"
    assert tight_loss > loose_loss
    result = {
        "status": "PASS",
        "evidence_type": "人工合成数学反例；不是GRC失败，不是模型运行，不是现实数据结果",
        "k": 1,
        "candidates": candidates,
        "loose_threshold": loose_tau,
        "tight_threshold": tight_tau,
        "loose_choice": loose_choice,
        "tight_choice": tight_choice,
        "loose_consumer_future_loss": loose_loss,
        "tight_consumer_future_loss": tight_loss,
        "consumer_loss_change_after_tightening": tight_loss - loose_loss,
        "interpretation": (
            "A tighter estimated-risk threshold can change the selected item and increase "
            "the consumer's future loss. Threshold/risk-score monotonicity is therefore "
            "not a theorem about downstream world-model loss."
        ),
        "rejection_rule": (
            "Do not claim threshold tightening improves consumer loss without prospective "
            "held-out evaluation under the same selection policy."
        ),
        "python": sys.version,
        "platform": platform.platform(),
        "started_utc": started.isoformat(),
        "completed_utc": datetime.now(timezone.utc).isoformat(),
    }
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    result["script_sha256"] = sha256(Path(__file__))
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
