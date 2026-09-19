#!/usr/bin/env python3
"""Deterministic synthetic counterexamples; no model/data/GT file access."""
import hashlib
import json
import math
import random
from datetime import datetime, timezone
from pathlib import Path


def mean(values):
    return sum(values) / len(values)


def run():
    # Equal-key attention surrogate including one query/anchor value of zero.
    # Every historical item is identical, so no source is specially harmful.
    identical_history = [1.0] * 4
    full = mean([0.0] + identical_history)
    removed = mean([0.0] + identical_history[:-1])
    replaced = mean([0.0] + identical_history[:-1] + [1.0])
    synthetic_target = 0.5
    removal_benefit = (full - synthetic_target) ** 2 - (removed - synthetic_target) ** 2
    replacement_benefit = (full - synthetic_target) ** 2 - (replaced - synthetic_target) ** 2
    assert removal_benefit > 0 and replacement_benefit == 0

    # An independently specified truth is not the shared biased pseudo-answer.
    true_depth, biased_peer_depth = 10.0, 12.0
    candidate_low_conflict, candidate_high_conflict = 12.0, 10.0
    pred_original = mean([biased_peer_depth] * 3 + [candidate_low_conflict])
    pred_replaced = mean([biased_peer_depth] * 3 + [candidate_high_conflict])
    absrel = lambda prediction, target: abs(prediction - target) / target
    true_benefit = absrel(pred_original, true_depth) - absrel(pred_replaced, true_depth)
    biased_proxy_benefit = absrel(pred_original, biased_peer_depth) - absrel(pred_replaced, biased_peer_depth)
    assert true_benefit > 0 and biased_proxy_benefit < 0

    # Identical integer seeds do not force identical noise after differing draws.
    rng_a, rng_b = random.Random(42), random.Random(42)
    noise_a = rng_a.random()
    _extra_branch_draw = rng_b.random()
    noise_b = rng_b.random()
    assert noise_a != noise_b
    fixed_noise = noise_a
    exact_replay_delta = (1.0 + fixed_noise) - (1.0 + fixed_noise)
    assert exact_replay_delta == 0

    # Freezing a descendant suppresses an otherwise deterministic total effect.
    old_source, new_source = 1.0, 2.0
    original_mediator = old_source
    full_total_effect = 2.0 * new_source - 2.0 * old_source
    frozen_mediator_effect = 2.0 * original_mediator - 2.0 * old_source
    assert full_total_effect == 2.0 and frozen_mediator_effect == 0

    return {
        "evidence_type": "SYNTHETIC_NUMERICAL_COUNTEREXAMPLES_ONLY",
        "scientific_validation": False,
        "model_calls": 0,
        "dataset_files_read": 0,
        "future_gt_files_read": 0,
        "checks_passed": 4,
        "budget_confound": {
            "consumer": "mean([query_anchor=0]+history)",
            "synthetic_target": synthetic_target,
            "full_context_count": 4,
            "removed_context_count": 3,
            "matched_replacement_context_count": 4,
            "full_output": full,
            "removed_output": removed,
            "matched_replacement_output": replaced,
            "remove_loss_improvement": removal_benefit,
            "matched_replace_loss_improvement": replacement_benefit,
            "interpretation": "Deletion improves squared error although every memory item is identical; the contrast includes active-count/normalization change.",
        },
        "shared_bias": {
            "true_depth": true_depth,
            "biased_peer_and_pseudo_target_depth": biased_peer_depth,
            "low_conflict_risk": abs(candidate_low_conflict - biased_peer_depth),
            "high_conflict_risk": abs(candidate_high_conflict - biased_peer_depth),
            "original_prediction": pred_original,
            "replacement_prediction": pred_replaced,
            "original_true_absrel": absrel(pred_original, true_depth),
            "replacement_true_absrel": absrel(pred_replaced, true_depth),
            "true_replacement_benefit": true_benefit,
            "biased_proxy_replacement_benefit": biased_proxy_benefit,
            "interpretation": "A low-conflict but commonly biased source looks best under shared pseudo-GT and worse under independently specified truth.",
        },
        "seed_replay": {
            "seed": 42,
            "branch_a_noise": noise_a,
            "branch_b_noise_after_extra_draw": noise_b,
            "same_seed_noise_delta": noise_b - noise_a,
            "explicit_noise_replay_delta": exact_replay_delta,
            "interpretation": "Save and inject the actual noise tensor and restore RNG states; equal integer seeds alone are not an exact replay contract.",
        },
        "descendant_recomputation": {
            "structural_equations": "mediator=source; output=2*mediator",
            "fully_recomputed_total_effect": full_total_effect,
            "effect_with_mediator_frozen": frozen_mediator_effect,
            "interpretation": "Freezing post-intervention descendants changes the estimand and can erase the total downstream effect.",
        },
    }


if __name__ == "__main__":
    directory = Path(__file__).resolve().parent
    result = run()
    result_path = directory / "RESULTS.json"
    result_path.write_text(json.dumps(result, indent=2) + "\n")
    receipt = {
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS_SYNTHETIC_COUNTEREXAMPLES",
        "input_origin": "constants inside run_diagnostic.py",
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "results_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
        "method_validated": False,
    }
    (directory / "RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(result, indent=2))
