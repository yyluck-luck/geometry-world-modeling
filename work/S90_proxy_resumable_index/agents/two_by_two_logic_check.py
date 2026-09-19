#!/usr/bin/env python3
"""Synthetic logic checks: a 2x2 interaction is neither necessary nor sufficient for GRC benefit."""
import hashlib, json, subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "two_by_two_logic_results.json"

def interaction(table):
    # table[memory][appearance], with geometry rows 0/1 and appearance cols 0/1
    return table[1][1] - table[1][0] - table[0][1] + table[0][0]

def main():
    # Table convention: table[geometry_condition][appearance_condition].
    # Scenario A: low-risk memory B has lower future loss in every appearance arm,
    # while geometry x appearance interaction is exactly zero for both memories.
    # Rows are geometry condition; columns are appearance condition.
    no_interaction = {
        "low_risk_memory": [[0.20, 0.30], [0.10, 0.20]],
        "high_risk_memory": [[0.60, 0.70], [0.50, 0.60]],
    }
    # Scenario B: a memory choice changes the geometry/appearance interaction,
    # but both memories have the same mean loss, so there is no GRC memory benefit.
    interaction_no_benefit = {
        "memory_A": [[0.30, 0.30], [0.30, 0.30]],
        "memory_B": [[0.10, 0.50], [0.50, 0.10]],
    }
    results = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "type": "synthetic_logic_only",
        "scenario_A": {
            "tables": no_interaction,
            "interactions": {k: interaction(v) for k, v in no_interaction.items()},
            "mean_loss": {k: sum(sum(row) for row in v)/4 for k, v in no_interaction.items()},
            "claim": "A lower-risk memory can improve future loss with zero 2x2 interaction.",
        },
        "scenario_B": {
            "tables": interaction_no_benefit,
            "interactions": {k: interaction(v) for k, v in interaction_no_benefit.items()},
            "mean_loss": {k: sum(sum(row) for row in v)/4 for k, v in interaction_no_benefit.items()},
            "claim": "A nonzero 2x2 interaction can occur without a memory-level mean-loss benefit.",
        },
        "assertions": {
            "scenario_A_interactions_zero": all(abs(interaction(v)) < 1e-12 for v in no_interaction.values()),
            "scenario_A_low_risk_better": sum(sum(row) for row in no_interaction["low_risk_memory"]) < sum(sum(row) for row in no_interaction["high_risk_memory"]),
            "scenario_B_interaction_exists": interaction(interaction_no_benefit["memory_B"]) != 0,
            "scenario_B_no_memory_mean_benefit": sum(sum(row) for row in interaction_no_benefit["memory_A"]) == sum(sum(row) for row in interaction_no_benefit["memory_B"]),
        },
        "interpretation": "A 2x2 interaction is a controlled diagnostic contrast. It is neither necessary nor sufficient for a memory policy to lower held-out future geometry loss.",
        "not_scientific_evidence": True,
    }
    if not all(results["assertions"].values()):
        raise AssertionError(results["assertions"])
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": str(OUT), "sha256": hashlib.sha256(OUT.read_bytes()).hexdigest(), "assertions": results["assertions"]}, ensure_ascii=False))

if __name__ == "__main__":
    main()
