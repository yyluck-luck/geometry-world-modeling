#!/usr/bin/env python3
"""Deterministic sanity tests for the current GRC-Memory proposal.

These are synthetic mathematical counterexamples and an execution of one pinned
official Conformal Risk Control helper.  They are not world-model experiments,
not real-data results, and not evidence that GRC-Memory works.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy


HERE = Path(__file__).resolve().parent
SOURCES = HERE / "sources"
CRC_ROOT = SOURCES / "conformal-risk"
CRC_FILE = CRC_ROOT / "core" / "get_lhat.py"
EXPECTED_CRC_COMMIT = "3eff946390a8f188b1e5ab700fce21a66a215e7c"
EXPECTED_CRC_REMOTE = "https://github.com/aangelopoulos/conformal-risk.git"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_head(path: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(path), "rev-parse", "HEAD"], text=True
    ).strip()


def git_remote(path: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(path), "remote", "get-url", "origin"], text=True
    ).strip()


def load_crc_get_lhat():
    spec = importlib.util.spec_from_file_location("pinned_crc_get_lhat", CRC_FILE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {CRC_FILE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.get_lhat


def crc_global_parameter_test() -> dict:
    assert git_head(CRC_ROOT) == EXPECTED_CRC_COMMIT
    assert git_remote(CRC_ROOT) == EXPECTED_CRC_REMOTE
    get_lhat = load_crc_get_lhat()
    losses = np.array(
        [
            [0.05, 0.10, 0.20, 0.40, 0.70],
            [0.10, 0.15, 0.25, 0.45, 0.75],
            [0.00, 0.10, 0.20, 0.50, 0.80],
            [0.05, 0.20, 0.30, 0.55, 0.90],
        ],
        dtype=np.float64,
    )
    lambdas = np.array([0.0, 0.1, 0.2, 0.3, 0.4], dtype=np.float64)
    alpha = 0.5
    bound = 1.0
    corrected_risk = (len(losses) / (len(losses) + 1)) * losses.mean(axis=0) + (
        bound / (len(losses) + 1)
    )
    selected = float(get_lhat(losses, lambdas, alpha=alpha, B=bound))
    assert selected == 0.2
    return {
        "status": "PASS",
        "purpose": "Execute the pinned official helper and show that it returns one global policy parameter.",
        "loss_table_shape": list(losses.shape),
        "alpha": alpha,
        "B": bound,
        "corrected_empirical_risk": corrected_risk.tolist(),
        "selected_lambda": selected,
        "interpretation_limit": (
            "This execution checks code semantics only. It does not establish a guarantee "
            "for GRC, a per-memory risk bound, or a probability guarantee."
        ),
    }


def selection_shift_test() -> dict:
    query_count = 100
    safe_per_query = 9
    safe_error = 0.05
    risky_error = 0.90
    pooled = np.array(
        [[safe_error] * safe_per_query + [risky_error] for _ in range(query_count)],
        dtype=np.float64,
    )
    utility = np.array(
        [list(np.linspace(0.0, 0.8, safe_per_query)) + [1.0] for _ in range(query_count)],
        dtype=np.float64,
    )
    pooled_q90 = float(np.quantile(pooled.reshape(-1), 0.90, method="linear"))
    selected_index = np.argmax(utility, axis=1)
    selected_errors = pooled[np.arange(query_count), selected_index]
    selected_q90 = float(np.quantile(selected_errors, 0.90, method="linear"))
    selected_exceedance = float(np.mean(selected_errors > pooled_q90))
    assert pooled_q90 < risky_error
    assert selected_q90 == risky_error
    assert selected_exceedance == 1.0
    return {
        "status": "PASS",
        "purpose": "Construct a selection-induced distribution shift counterexample.",
        "queries": query_count,
        "candidates_per_query": safe_per_query + 1,
        "pooled_candidate_q90": pooled_q90,
        "post_selection_q90": selected_q90,
        "post_selection_exceedance_of_pooled_q90": selected_exceedance,
        "interpretation": (
            "A threshold calibrated over all candidates can fail after a utility policy "
            "systematically selects the risky subgroup. The deployed policy itself must be "
            "represented in calibration."
        ),
    }


def vector_scalarization_test() -> dict:
    residuals = {
        "A": np.array([0.9, 0.1, 0.1], dtype=np.float64),
        "B": np.array([0.5, 0.5, 0.5], dtype=np.float64),
    }
    mean_scores = {name: float(value.mean()) for name, value in residuals.items()}
    max_scores = {name: float(value.max()) for name, value in residuals.items()}
    safer_by_mean = min(mean_scores, key=mean_scores.get)
    safer_by_max = min(max_scores, key=max_scores.get)
    assert safer_by_mean == "A"
    assert safer_by_max == "B"
    return {
        "status": "PASS",
        "purpose": "Show that a three-component residual vector has no unique scalar quantile or ranking.",
        "residual_order": ["reprojection", "depth", "visibility"],
        "residuals": {name: value.tolist() for name, value in residuals.items()},
        "mean_scalarization": mean_scores,
        "max_scalarization": max_scores,
        "safer_by_mean": safer_by_mean,
        "safer_by_max": safer_by_max,
        "interpretation": (
            "The proposal must freeze units, normalization, and a scalar nonconformity or "
            "joint set loss before taking a quantile."
        ),
    }


def set_utility(selected: frozenset[str]) -> float:
    value = float(len(selected.intersection({"C", "D"})))
    value += 0.1 * float(len(selected.intersection({"A", "B"})))
    if {"A", "B"}.issubset(selected):
        value += 3.8
    return value


def greedy(items: list[str], budget: int) -> tuple[list[str], float]:
    selected: list[str] = []
    for _ in range(budget):
        current = set_utility(frozenset(selected))
        remaining = [item for item in items if item not in selected]
        best = max(
            remaining,
            key=lambda item: (set_utility(frozenset(selected + [item])) - current, item),
        )
        selected.append(best)
    return selected, set_utility(frozenset(selected))


def non_submodular_greedy_test() -> dict:
    items = ["A", "B", "C", "D"]
    budget = 2
    all_sets = [
        frozenset(combo)
        for size in range(len(items) + 1)
        for combo in itertools.combinations(items, size)
    ]
    monotonicity_checks = 0
    for selected in all_sets:
        for item in items:
            if item not in selected:
                assert set_utility(selected | {item}) >= set_utility(selected)
                monotonicity_checks += 1
    greedy_set, greedy_value = greedy(items, budget)
    candidates = [
        (list(combo), set_utility(frozenset(combo)))
        for combo in itertools.combinations(items, budget)
    ]
    exact_set, exact_value = max(candidates, key=lambda pair: (pair[1], pair[0]))
    marginal_b_empty = set_utility(frozenset({"B"})) - set_utility(frozenset())
    marginal_b_after_a = set_utility(frozenset({"A", "B"})) - set_utility(
        frozenset({"A"})
    )
    ratio = greedy_value / exact_value
    canonical_submodular_bound = 1.0 - np.exp(-1.0)
    assert marginal_b_after_a > marginal_b_empty
    assert set(exact_set) == {"A", "B"}
    assert ratio < canonical_submodular_bound
    return {
        "status": "PASS",
        "purpose": "Give a monotone but non-submodular utility where greedy misses a synergistic memory pair.",
        "budget": budget,
        "greedy_set": greedy_set,
        "greedy_value": greedy_value,
        "exact_set": exact_set,
        "exact_value": exact_value,
        "greedy_over_exact": ratio,
        "one_minus_one_over_e": float(canonical_submodular_bound),
        "marginal_B_from_empty": marginal_b_empty,
        "marginal_B_after_A": marginal_b_after_a,
        "exhaustive_monotonicity_checks": monotonicity_checks,
        "interpretation": (
            "A 1-1/e claim is unavailable unless the actual learned set objective is proven "
            "monotone submodular under the deployed constraints. Small budgets should use "
            "exact enumeration as a reference."
        ),
    }


def joint_risk_test() -> dict:
    synergy = {"risk_A": 0.1, "risk_B": 0.1, "sum": 0.2, "joint": 0.8}
    redundancy = {"risk_A": 0.4, "risk_B": 0.4, "sum": 0.8, "joint": 0.45}
    assert synergy["sum"] < synergy["joint"]
    assert redundancy["sum"] > redundancy["joint"]
    return {
        "status": "PASS",
        "purpose": "Show that summing item risks is not a generally valid set-risk model.",
        "synergistic_failure_case": synergy,
        "redundant_failure_case": redundancy,
        "interpretation": (
            "Memory interactions can make a sum either optimistic or pessimistic; a set-level "
            "loss/predictor or a proven structural assumption is required."
        ),
    }


def counterfactual_sign_test() -> dict:
    ground_truth = 0.0
    cases = {
        "helpful_memory": {"without": -2.0, "with": 0.0},
        "harmful_memory": {"without": 0.0, "with": 2.0},
    }
    output = {}
    for name, values in cases.items():
        sensitivity = abs(values["with"] - values["without"])
        loss_without = (values["without"] - ground_truth) ** 2
        loss_with = (values["with"] - ground_truth) ** 2
        helpfulness = loss_without - loss_with
        output[name] = {
            **values,
            "output_distance_sensitivity": sensitivity,
            "loss_without": loss_without,
            "loss_with": loss_with,
            "ground_truth_loss_reduction": helpfulness,
        }
    assert output["helpful_memory"]["output_distance_sensitivity"] == output[
        "harmful_memory"
    ]["output_distance_sensitivity"]
    assert output["helpful_memory"]["ground_truth_loss_reduction"] > 0
    assert output["harmful_memory"]["ground_truth_loss_reduction"] < 0
    return {
        "status": "PASS",
        "purpose": "Refute output-distance sensitivity as a signed measure of memory usefulness.",
        "ground_truth": ground_truth,
        "cases": output,
        "correct_effect_definition": (
            "tau_i(S)=E_xi[L_geo(Yhat(S\\{i},xi),Y_true)-"
            "L_geo(Yhat(S,xi),Y_true)]; positive means removal hurts."
        ),
        "interpretation": (
            "Matched-seed output change measures sensitivity only. A usefulness claim needs "
            "held-out ground truth loss, fixed target/query, fixed other memories, and fixed random seed."
        ),
    }


def future_leakage_test() -> dict:
    history_predictions = np.array([0.0, 1.0], dtype=np.float64)
    oracle_selection = {}
    for future in [0.0, 1.0]:
        losses = (history_predictions - future) ** 2
        oracle_selection[str(future)] = int(np.argmin(losses))
    assert oracle_selection["0.0"] != oracle_selection["1.0"]
    return {
        "status": "PASS",
        "purpose": "Expose target leakage when selection directly evaluates the realized future.",
        "identical_past_only_scores": [0.5, 0.5],
        "history_predictions": history_predictions.tolist(),
        "oracle_selected_history_by_unseen_future": oracle_selection,
        "interpretation": (
            "A deployable selector may use a predictor trained on past training targets, but at "
            "test time it cannot query the realized Y_future to score candidates."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=HERE / "GRC_MATH_SANITY_RESULTS.json"
    )
    args = parser.parse_args()
    started = datetime.now(timezone.utc)
    tests = {
        "official_crc_global_parameter": crc_global_parameter_test(),
        "selection_induced_shift": selection_shift_test(),
        "vector_scalarization_ambiguity": vector_scalarization_test(),
        "non_submodularity_and_greedy_failure": non_submodular_greedy_test(),
        "non_additive_set_risk": joint_risk_test(),
        "counterfactual_sensitivity_sign": counterfactual_sign_test(),
        "future_target_leakage": future_leakage_test(),
    }
    completed = datetime.now(timezone.utc)
    record = {
        "schema": "s90.grc_math_sanity.v1",
        "status": "PASS" if all(t["status"] == "PASS" for t in tests.values()) else "FAIL",
        "classification": "synthetic_math_and_pinned_source_execution_not_scientific_validation",
        "started_utc": started.isoformat(),
        "completed_utc": completed.isoformat(),
        "elapsed_seconds": (completed - started).total_seconds(),
        "source": {
            "script": str(Path(__file__).resolve()),
            "script_sha256_before_result_write": sha256(Path(__file__).resolve()),
            "official_crc_file": str(CRC_FILE.resolve()),
            "official_crc_file_sha256": sha256(CRC_FILE),
            "official_crc_commit": git_head(CRC_ROOT),
            "official_crc_expected_commit": EXPECTED_CRC_COMMIT,
            "official_crc_remote": git_remote(CRC_ROOT),
            "official_crc_expected_remote": EXPECTED_CRC_REMOTE,
        },
        "runtime": {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
        "test_count": len(tests),
        "tests": tests,
        "claim_boundary": (
            "These seven deterministic checks falsify several mathematical shortcuts in the "
            "draft. They do not show that the corrected GRC method improves any real video, "
            "geometry metric, scene, or world model."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
