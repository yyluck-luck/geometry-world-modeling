#!/usr/bin/env python3
"""Pure-standard-library reference evaluator for the RAIMA V4 primary gate.

This module evaluates typed metadata receipts only.  It does not import a
scientific package, open an image, map a tensor, call a model, or discover a
data roster.  Scientific endpoint states must be supplied by a separately
reviewed and exactly bound S48 contract; V4 currently has no active S48
contract and therefore cannot authorize an experiment.
"""

from __future__ import annotations

from decimal import Decimal, localcontext
from fractions import Fraction
from math import comb
from typing import Any, Mapping, Sequence


COHORT_SCHEMA = "raima-v4-cohort-evidence-v1"
STAGE_C1 = "stage_c1_10"
STAGE_C2 = "stage_c2_20"
TRAJECTORY_IDS = ("return_short", "return_long")
ENDPOINT_IDS = ("AOIG", "HARMFUL_SEM", "NEGATIVE_STABLE_RCSU")

SCENE_RATE_THRESHOLD = Fraction(1, 5)
GLOBAL_MEAN_THRESHOLD = Fraction(1, 5)
LOSO_MEAN_THRESHOLD = Fraction(3, 20)
STAGE_C1_FUTILITY_MAX_POSITIVES = 2
STAGE_C2_MIN_POSITIVES = 8

ACCESS_STATES = frozenset(("PASS", "FAIL", "MISSING"))
COMMON_ENDPOINT_STATES = frozenset(("POSITIVE", "NEGATIVE", "TECHNICAL_MISSING"))
RCSU_ENDPOINT_STATES = COMMON_ENDPOINT_STATES | frozenset(("REFERENCE_INELIGIBLE",))
NOT_EVALUATED = "NOT_EVALUATED"
INCOMPLETE_ENDPOINT_STATES = frozenset(("TECHNICAL_MISSING", "REFERENCE_INELIGIBLE"))


class ProtocolError(ValueError):
    """Raised when typed evidence is incomplete, ambiguous, or malformed."""


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ProtocolError(f"{label} must be a mapping")
    return value


def _exact_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ProtocolError(f"{label} keys mismatch; missing={missing}; extra={extra}")


def _identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise ProtocolError(f"{label} must be a non-empty canonical string")
    if any(ord(char) < 33 or ord(char) > 126 for char in value):
        raise ProtocolError(f"{label} must use visible ASCII without spaces")
    return value


def _sequence(value: Any, label: str) -> Sequence[Any]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        raise ProtocolError(f"{label} must be a sequence")
    return value


def _fraction(value: Any, label: str) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, Fraction):
        raise ProtocolError(f"{label} must be fractions.Fraction")
    if value < 0 or value > 1:
        raise ProtocolError(f"{label} must lie in [0,1]")
    return value


def _decimal(value: Fraction, places: int = 18) -> str:
    with localcontext() as context:
        context.prec = max(places + 12, 40)
        result = Decimal(value.numerator) / Decimal(value.denominator)
        return format(result, f".{places}f")


def fraction_record(value: Fraction) -> dict[str, Any]:
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "decimal": _decimal(value),
    }


def _validate_endpoint_states(
    endpoint_states: Any,
    access_status: str,
    label: str,
) -> dict[str, str]:
    states = _mapping(endpoint_states, label)
    _exact_keys(states, set(ENDPOINT_IDS), label)
    normalized: dict[str, str] = {}
    for endpoint in ENDPOINT_IDS:
        state = states[endpoint]
        if not isinstance(state, str):
            raise ProtocolError(f"{label}.{endpoint} must be a string enum")
        if access_status != "PASS":
            if state != NOT_EVALUATED:
                raise ProtocolError(
                    f"{label}.{endpoint} must be NOT_EVALUATED when access is not PASS"
                )
        else:
            allowed = RCSU_ENDPOINT_STATES if endpoint == "NEGATIVE_STABLE_RCSU" else COMMON_ENDPOINT_STATES
            if state not in allowed:
                raise ProtocolError(f"{label}.{endpoint} has invalid state {state!r}")
        normalized[endpoint] = state
    return normalized


def evaluate_unit(unit: Any, label: str = "unit") -> dict[str, Any]:
    record = _mapping(unit, label)
    _exact_keys(
        record,
        {"unit_id", "source_id", "target_id", "access_status", "endpoint_states"},
        label,
    )
    unit_id = _identifier(record["unit_id"], f"{label}.unit_id")
    source_id = _identifier(record["source_id"], f"{label}.source_id")
    target_id = _identifier(record["target_id"], f"{label}.target_id")
    access_status = record["access_status"]
    if not isinstance(access_status, str) or access_status not in ACCESS_STATES:
        raise ProtocolError(f"{label}.access_status must be one of {sorted(ACCESS_STATES)}")
    endpoint_states = _validate_endpoint_states(
        record["endpoint_states"], access_status, f"{label}.endpoint_states"
    )

    access_pass = access_status == "PASS"
    endpoint_positive = tuple(
        endpoint for endpoint in ENDPOINT_IDS if endpoint_states[endpoint] == "POSITIVE"
    )
    incomplete_endpoints = tuple(
        endpoint for endpoint in ENDPOINT_IDS if endpoint_states[endpoint] in INCOMPLETE_ENDPOINT_STATES
    )
    complete = access_pass and not incomplete_endpoints
    union_positive = access_pass and bool(endpoint_positive)

    return {
        "unit_id": unit_id,
        "source_id": source_id,
        "target_id": target_id,
        "access_status": access_status,
        "endpoint_states": {endpoint: endpoint_states[endpoint] for endpoint in ENDPOINT_IDS},
        "positive_endpoints": list(endpoint_positive),
        "incomplete_endpoints": list(incomplete_endpoints),
        "endpoint_complete": complete,
        "union_positive": union_positive,
        "planned_lower_positive": int(union_positive),
        "planned_upper_positive": int(union_positive or not complete),
    }


def evaluate_trajectory(trajectory: Any, label: str = "trajectory") -> dict[str, Any]:
    record = _mapping(trajectory, label)
    _exact_keys(record, {"trajectory_id", "planned_units"}, label)
    trajectory_id = _identifier(record["trajectory_id"], f"{label}.trajectory_id")
    if trajectory_id not in TRAJECTORY_IDS:
        raise ProtocolError(f"{label}.trajectory_id is not registered")
    units = _sequence(record["planned_units"], f"{label}.planned_units")
    if len(units) != 1:
        raise ProtocolError(f"{label} must contain exactly one preplanned source-target unit")
    evaluated = evaluate_unit(units[0], f"{label}.planned_units[0]")
    evaluable = evaluated["access_status"] == "PASS" and evaluated["endpoint_complete"]
    conditional_rate = Fraction(int(evaluated["union_positive"]), 1) if evaluable else None
    return {
        "trajectory_id": trajectory_id,
        "planned_unit": evaluated,
        "evaluable": evaluable,
        "conditional_rate": fraction_record(conditional_rate) if conditional_rate is not None else None,
        "planned_lower_rate": fraction_record(Fraction(evaluated["planned_lower_positive"], 1)),
        "planned_upper_rate": fraction_record(Fraction(evaluated["planned_upper_positive"], 1)),
    }


def evaluate_scene(scene: Any, label: str = "scene") -> dict[str, Any]:
    record = _mapping(scene, label)
    _exact_keys(record, {"scene_id", "independence_cluster_id", "trajectories"}, label)
    scene_id = _identifier(record["scene_id"], f"{label}.scene_id")
    cluster_id = _identifier(record["independence_cluster_id"], f"{label}.independence_cluster_id")
    trajectories = _sequence(record["trajectories"], f"{label}.trajectories")
    if len(trajectories) != 2:
        raise ProtocolError(f"{label} must contain exactly two trajectories")
    by_id: dict[str, dict[str, Any]] = {}
    for index, trajectory in enumerate(trajectories):
        evaluated = evaluate_trajectory(trajectory, f"{label}.trajectories[{index}]")
        trajectory_id = evaluated["trajectory_id"]
        if trajectory_id in by_id:
            raise ProtocolError(f"{label} contains duplicate trajectory_id {trajectory_id!r}")
        by_id[trajectory_id] = evaluated
    if set(by_id) != set(TRAJECTORY_IDS):
        raise ProtocolError(f"{label} must contain the exact registered trajectory roster")

    ordered = [by_id[trajectory_id] for trajectory_id in TRAJECTORY_IDS]
    unit_ids = [item["planned_unit"]["unit_id"] for item in ordered]
    if len(set(unit_ids)) != len(unit_ids):
        raise ProtocolError(f"{label} contains duplicate unit_id")

    evaluable = all(item["evaluable"] for item in ordered)
    lower = sum(
        (Fraction(item["planned_unit"]["planned_lower_positive"], 1) for item in ordered),
        Fraction(0, 1),
    ) / 2
    upper = sum(
        (Fraction(item["planned_unit"]["planned_upper_positive"], 1) for item in ordered),
        Fraction(0, 1),
    ) / 2
    rate = lower if evaluable else None
    scene_positive = bool(evaluable and rate is not None and rate >= SCENE_RATE_THRESHOLD)
    return {
        "scene_id": scene_id,
        "independence_cluster_id": cluster_id,
        "trajectories": ordered,
        "evaluable": evaluable,
        "scene_rate": fraction_record(rate) if rate is not None else None,
        "planned_lower_rate": fraction_record(lower),
        "planned_upper_rate": fraction_record(upper),
        "scene_positive": scene_positive,
    }


def _mean(values: Sequence[Fraction]) -> Fraction:
    if not values:
        raise ProtocolError("cannot average an empty sequence")
    return sum(values, Fraction(0, 1)) / len(values)


def _minimum_loso_mean(values: Sequence[Fraction]) -> Fraction:
    if len(values) < 2:
        raise ProtocolError("leave-one-out mean requires at least two scenes")
    total = sum(values, Fraction(0, 1))
    return min((total - value) / (len(values) - 1) for value in values)


def composite_gate_from_scene_rates(
    scene_rates: Sequence[Fraction], stage: str
) -> dict[str, Any]:
    expected_n = 10 if stage == STAGE_C1 else 20 if stage == STAGE_C2 else None
    if expected_n is None:
        raise ProtocolError("unregistered stage")
    if len(scene_rates) != expected_n:
        raise ProtocolError(f"{stage} requires exactly {expected_n} scene rates")
    rates = [_fraction(value, f"scene_rates[{index}]") for index, value in enumerate(scene_rates)]
    positive_count = sum(value >= SCENE_RATE_THRESHOLD for value in rates)
    mean_rate = _mean(rates)
    minimum_loso = _minimum_loso_mean(rates)

    if stage == STAGE_C1:
        if positive_count <= STAGE_C1_FUTILITY_MAX_POSITIVES:
            decision = "STOP_CONFIRMATION_FOR_FUTILITY"
        else:
            decision = "CONTINUE_TO_STAGE_C2_MAX20"
        pass_conditions = {
            "not_early_futility": positive_count > STAGE_C1_FUTILITY_MAX_POSITIVES,
            "no_early_efficacy_claim": True,
        }
    else:
        pass_conditions = {
            "positive_scene_count_at_least_8": positive_count >= STAGE_C2_MIN_POSITIVES,
            "equal_scene_mean_at_least_0.20": mean_rate >= GLOBAL_MEAN_THRESHOLD,
            "minimum_loso_mean_at_least_0.15": minimum_loso >= LOSO_MEAN_THRESHOLD,
        }
        decision = (
            "PASS_RAIMA_V4_COMPOSITE_CONFIRMATION_GATE"
            if all(pass_conditions.values())
            else "FAIL_RAIMA_V4_COMPOSITE_CONFIRMATION_GATE"
        )
    return {
        "stage": stage,
        "scene_count": expected_n,
        "scene_positive_count": positive_count,
        "equal_scene_mean": fraction_record(mean_rate),
        "minimum_leave_one_scene_out_mean": fraction_record(minimum_loso),
        "pass_conditions": pass_conditions,
        "decision": decision,
    }


def evaluate_cohort(cohort: Any) -> dict[str, Any]:
    record = _mapping(cohort, "cohort")
    _exact_keys(record, {"schema", "stage", "scenes"}, "cohort")
    if record["schema"] != COHORT_SCHEMA:
        raise ProtocolError("cohort.schema mismatch")
    stage = record["stage"]
    expected_n = 10 if stage == STAGE_C1 else 20 if stage == STAGE_C2 else None
    if expected_n is None:
        raise ProtocolError("cohort.stage is not registered")
    scenes = _sequence(record["scenes"], "cohort.scenes")
    if len(scenes) != expected_n:
        raise ProtocolError(f"cohort.scenes must contain exactly {expected_n} scenes")

    evaluated_scenes = [
        evaluate_scene(scene, f"cohort.scenes[{index}]") for index, scene in enumerate(scenes)
    ]
    scene_ids = [scene["scene_id"] for scene in evaluated_scenes]
    cluster_ids = [scene["independence_cluster_id"] for scene in evaluated_scenes]
    unit_ids = [
        trajectory["planned_unit"]["unit_id"]
        for scene in evaluated_scenes
        for trajectory in scene["trajectories"]
    ]
    for values, label in (
        (scene_ids, "scene_id"),
        (cluster_ids, "independence_cluster_id"),
        (unit_ids, "unit_id"),
    ):
        if len(set(values)) != len(values):
            raise ProtocolError(f"cohort contains duplicate {label}")

    evaluated_scenes.sort(key=lambda item: item["scene_id"])
    all_evaluable = all(scene["evaluable"] for scene in evaluated_scenes)
    if all_evaluable:
        rates = [
            Fraction(scene["scene_rate"]["numerator"], scene["scene_rate"]["denominator"])
            for scene in evaluated_scenes
        ]
        gate = composite_gate_from_scene_rates(rates, stage)
    else:
        lower_rates = [
            Fraction(scene["planned_lower_rate"]["numerator"], scene["planned_lower_rate"]["denominator"])
            for scene in evaluated_scenes
        ]
        upper_rates = [
            Fraction(scene["planned_upper_rate"]["numerator"], scene["planned_upper_rate"]["denominator"])
            for scene in evaluated_scenes
        ]
        gate = {
            "stage": stage,
            "scene_count": expected_n,
            "decision": "BLOCKED_INCOMPLETE_OR_INELIGIBLE_EVIDENCE",
            "planned_lower_equal_scene_mean": fraction_record(_mean(lower_rates)),
            "planned_upper_equal_scene_mean": fraction_record(_mean(upper_rates)),
            "evaluable_scene_count": sum(scene["evaluable"] for scene in evaluated_scenes),
        }
    return {
        "schema": "raima-v4-primary-endpoint-evaluation-v1",
        "input_schema": COHORT_SCHEMA,
        "stage": stage,
        "scene_roster_sorted": scene_ids == sorted(scene_ids),
        "all_scenes_evaluable": all_evaluable,
        "scenes": evaluated_scenes,
        "gate": gate,
    }


def binomial_tail(n: int, minimum_successes: int, probability: Fraction) -> Fraction:
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ProtocolError("n must be a positive integer")
    if (
        isinstance(minimum_successes, bool)
        or not isinstance(minimum_successes, int)
        or minimum_successes < 0
        or minimum_successes > n + 1
    ):
        raise ProtocolError("minimum_successes is outside its integer domain")
    p = _fraction(probability, "probability")
    return sum(
        (
            Fraction(comb(n, successes), 1)
            * p**successes
            * (1 - p) ** (n - successes)
            for successes in range(minimum_successes, n + 1)
        ),
        Fraction(0, 1),
    )


def two_stage_success_probability(probability: Fraction) -> Fraction:
    """Count-gate probability for n1=10, futility <=2, Nmax=20, final >=8.

    The actual composite gate is a subset of this count gate, so under the
    independent/exchangeable Bernoulli premise this value is an exact type-I
    error upper bound.  It is an upper bound on power until a joint scene-rate
    distribution is justified.
    """

    p = _fraction(probability, "probability")
    total = Fraction(0, 1)
    for stage1_successes in range(3, 11):
        stage1_mass = (
            Fraction(comb(10, stage1_successes), 1)
            * p**stage1_successes
            * (1 - p) ** (10 - stage1_successes)
        )
        needed = max(0, STAGE_C2_MIN_POSITIVES - stage1_successes)
        total += stage1_mass * binomial_tail(10, needed, p)
    return total


def two_stage_expected_scene_count(probability: Fraction) -> Fraction:
    p = _fraction(probability, "probability")
    continue_probability = binomial_tail(10, 3, p)
    return Fraction(10, 1) + Fraction(10, 1) * continue_probability


def operating_characteristics(probability: Fraction) -> dict[str, Any]:
    p = _fraction(probability, "probability")
    return {
        "probability": fraction_record(p),
        "v3_fixed_n8_count_gate_probability": fraction_record(binomial_tail(8, 5, p)),
        "v4_two_stage_count_gate_probability": fraction_record(two_stage_success_probability(p)),
        "v4_expected_scene_count": fraction_record(two_stage_expected_scene_count(p)),
        "interpretation": "count-gate exact under independent exchangeable Bernoulli scenes; composite power is no larger",
    }


__all__ = [
    "COHORT_SCHEMA",
    "ENDPOINT_IDS",
    "ProtocolError",
    "STAGE_C1",
    "STAGE_C2",
    "TRAJECTORY_IDS",
    "binomial_tail",
    "composite_gate_from_scene_rates",
    "evaluate_cohort",
    "evaluate_scene",
    "evaluate_trajectory",
    "evaluate_unit",
    "fraction_record",
    "operating_characteristics",
    "two_stage_expected_scene_count",
    "two_stage_success_probability",
]
