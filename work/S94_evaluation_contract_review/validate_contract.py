#!/usr/bin/env python3
"""Offline completeness check for S94-v1; does not load data or run a model."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = json.loads((ROOT / "EVALUATION_CONTRACT.json").read_text())
required = {
    "gate0": ["required_modalities", "history_candidates_min", "future_queries_min_per_trajectory", "test_trajectories_confirmatory_min", "future_inputs_to_selector_forbidden"],
    "source_identity": ["fields", "traceability_min", "identity_match_required"],
    "budget": ["k_primary", "same_candidate_pool", "same_consumer", "track_separately"],
    "metrics": ["primary", "tail", "statistical_unit", "pixel_as_independent_sample", "ci"],
}
errors = []
for section, fields in required.items():
    if section not in spec:
        errors.append(f"missing section: {section}")
        continue
    for field in fields:
        if field not in spec[section]:
            errors.append(f"missing {section}.{field}")
if spec.get("status") != "PROTOCOL_ONLY_NOT_RUN":
    errors.append("contract status must remain PROTOCOL_ONLY_NOT_RUN")
if spec.get("source_identity", {}).get("traceability_min", 0) < 0.95:
    errors.append("traceability threshold below 0.95")
if spec.get("metrics", {}).get("pixel_as_independent_sample") is not False:
    errors.append("pixels must not be independent statistical units")
if errors:
    print("S94_CONTRACT_FAIL")
    for error in errors:
        print(error)
    raise SystemExit(1)
print("S94_CONTRACT_OFFLINE_PASS")
print(f"methods={len(spec['methods'])} metrics={len(spec['metrics']['primary']) + len(spec['metrics']['tail'])}")
