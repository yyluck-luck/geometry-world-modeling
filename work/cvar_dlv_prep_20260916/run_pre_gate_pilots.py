#!/usr/bin/env python3
"""Run deterministic, synthetic, pre-Gate pilots for CVaR and DLV."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work" / "cvar_dlv_prep_20260916"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cvar(losses: np.ndarray, alpha: float) -> float:
    if losses.ndim != 1 or not len(losses):
        raise ValueError("loss vector must be non-empty and one-dimensional")
    threshold = float(np.quantile(losses, alpha, method="higher"))
    return float(losses[losses >= threshold].mean())


def select(candidates, objective: str, k: int, alpha: float):
    chosen = []
    remaining = list(candidates)
    for _ in range(k):
        scored = []
        for item in remaining:
            trial = chosen + [item]
            losses = np.sum([x["losses"] for x in trial], axis=0)
            gain = sum(x["gain"] for x in trial)
            risk = float(losses.mean()) if objective == "mean" else cvar(losses, alpha)
            # Same deterministic tie-breaking for both selectors.
            scored.append((gain - risk, -sum(x["cost"] for x in trial),
                           item["id"], trial, losses, gain, risk))
        best = max(scored, key=lambda row: (row[0], row[1], row[2]))
        chosen = best[3]
        remaining = [x for x in remaining if x["id"] != best[2]]
    losses = np.sum([x["losses"] for x in chosen], axis=0)
    return {
        "objective": objective,
        "selected_ids": [x["id"] for x in chosen],
        "total_cost": int(sum(x["cost"] for x in chosen)),
        "total_gain": float(sum(x["gain"] for x in chosen)),
        "mean_loss": float(losses.mean()),
        "cvar_loss_alpha_0.80": cvar(losses, alpha),
        "worst_loss": float(losses.max()),
        "scenario_losses": [float(x) for x in losses],
    }


def run_cvar():
    # C and D are attractive on average but share a severe failure scenario.
    candidates = [
        {"id": "A", "cost": 1, "gain": 1.00, "losses": [0.05, 0.05, 0.05, 0.05, 0.05]},
        {"id": "B", "cost": 1, "gain": 0.95, "losses": [0.06, 0.06, 0.06, 0.06, 0.06]},
        {"id": "C", "cost": 1, "gain": 1.20, "losses": [0.02, 0.02, 0.02, 0.02, 0.95]},
        {"id": "D", "cost": 1, "gain": 1.15, "losses": [0.03, 0.03, 0.03, 0.03, 0.90]},
        {"id": "E", "cost": 1, "gain": 0.80, "losses": [0.08, 0.08, 0.08, 0.08, 0.08]},
    ]
    for item in candidates:
        item["losses"] = np.asarray(item["losses"], dtype=float)
    mean = select(candidates, "mean", 3, 0.80)
    tail = select(candidates, "cvar", 3, 0.80)
    return {
        "candidate_ids": [x["id"] for x in candidates],
        "budget_k": 3,
        "alpha": 0.80,
        "mean_selector": mean,
        "cvar_selector": tail,
        "selected_sets_differ": mean["selected_ids"] != tail["selected_ids"],
        "tail_improves_cvar": tail["cvar_loss_alpha_0.80"] < mean["cvar_loss_alpha_0.80"],
        "fixture_is_heavy_tailed": True,
    }


def run_dlv():
    tau = 0.05
    expected = 1.00
    events = [
        ("initial_consistent", 1.01),
        ("contradiction_1", 1.20),
        ("contradiction_2", 1.19),
        ("consistent_revisit_1", 1.02),
        ("noisy_revisit", 1.07),
        ("consistent_revisit_2", 0.99),
        ("consistent_revisit_3", 1.01),
    ]
    state = "active"
    contradictory_streak = 0
    consistent_streak = 1
    trace = []
    for label, observed in events:
        residual = abs(observed - expected)
        consistent = residual <= tau
        if consistent:
            contradictory_streak = 0
            consistent_streak += 1
            if state == "invalidated" and consistent_streak >= 2:
                state = "active"
        else:
            consistent_streak = 0
            contradictory_streak += 1
            if state == "active" and contradictory_streak >= 2:
                state = "invalidated"
        trace.append({
            "event": label, "observed_depth": observed, "residual": residual,
            "consistent": consistent, "state": state,
            "contradictory_streak": contradictory_streak,
            "consistent_streak": consistent_streak,
        })
    return {
        "threshold": tau,
        "events": trace,
        "invalidated_after_two_conflicts": trace[2]["state"] == "invalidated",
        "not_invalidated_after_one_conflict": trace[1]["state"] == "active",
        "not_reactivated_after_one_consistent_revisit": trace[3]["state"] == "invalidated",
        "reactivated_after_two_consistent_revisits": trace[-1]["state"] == "active",
        "final_state": state,
    }


def main():
    protocol = OUT / "PROTOCOL.md"
    result = {
        "schema": "pre-gate-cvar-dlv-pilots-v1",
        "status": "PILOT_IMPLEMENTATION_CHECK_ONLY",
        "data_access": {
            "project_predictions_read": False,
            "future_gt_read": False,
            "held_out_manifest_read": False,
            "synthetic_fixture_generated_in_runner": True,
        },
        "cvar_pilot": run_cvar(),
        "dlv_pilot": run_dlv(),
        "kill_criteria": {
            "cvar": "reject if tail selector fails to lower CVaR on this heavy-tail fixture",
            "dlv": "reject if one conflict invalidates or one consistent revisit reactivates",
        },
        "limitations": [
            "synthetic development fixture only",
            "no VMem forward or RGB-D/pose data",
            "no future answer scoring",
            "no evidence of novelty or method effectiveness",
        ],
    }
    (OUT / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    receipt = {
        "status": result["status"],
        "results_sha256": sha(OUT / "results.json"),
        "protocol_sha256": sha(protocol),
        "cvar_pass": result["cvar_pilot"]["selected_sets_differ"] and result["cvar_pilot"]["tail_improves_cvar"],
        "dlv_pass": all([
            result["dlv_pilot"]["invalidated_after_two_conflicts"],
            result["dlv_pilot"]["not_invalidated_after_one_conflict"],
            result["dlv_pilot"]["not_reactivated_after_one_consistent_revisit"],
            result["dlv_pilot"]["reactivated_after_two_consistent_revisits"],
        ]),
    }
    (OUT / "RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
