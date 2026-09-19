#!/usr/bin/env python3
"""Independent checks for the synthetic CVaR/DLV pre-Gate pilots."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work" / "cvar_dlv_prep_20260916"


def check(condition, label):
    if not condition:
        raise AssertionError(label)
    print("PASS", label)


def main():
    data = json.loads((OUT / "results.json").read_text())
    c = data["cvar_pilot"]
    d = data["dlv_pilot"]
    check(data["status"] == "PILOT_IMPLEMENTATION_CHECK_ONLY", "evidence boundary")
    check(data["data_access"]["project_predictions_read"] is False, "no project predictions")
    check(data["data_access"]["future_gt_read"] is False, "no future GT")
    check(c["mean_selector"]["total_cost"] == c["cvar_selector"]["total_cost"] == 3, "equal budget")
    check(c["selected_sets_differ"], "objectives produce different selections")
    check(c["tail_improves_cvar"], "CVaR improves on heavy-tail fixture")
    check(d["not_invalidated_after_one_conflict"], "one conflict tolerated")
    check(d["invalidated_after_two_conflicts"], "two conflicts invalidate")
    check(d["not_reactivated_after_one_consistent_revisit"], "one revisit does not revive")
    check(d["reactivated_after_two_consistent_revisits"], "two revisits revive")
    print("ALL_CHECKS_PASS")


if __name__ == "__main__":
    main()
