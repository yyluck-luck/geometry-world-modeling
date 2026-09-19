#!/usr/bin/env python3
"""Source-only adversarial tests for RAIMA V4's pure endpoint evaluator."""

from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
import unittest
from decimal import Decimal
from fractions import Fraction
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("primary_endpoint_reference.py")
PACKAGE_DIR = MODULE_PATH.parent
SPEC = importlib.util.spec_from_file_location("raima_v4_primary_endpoint_reference", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("unable to load frozen reference module")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def endpoint_states(
    aoig: str = "NEGATIVE",
    sem: str = "NEGATIVE",
    rcsu: str = "NEGATIVE",
) -> dict[str, str]:
    return {"AOIG": aoig, "HARMFUL_SEM": sem, "NEGATIVE_STABLE_RCSU": rcsu}


def make_unit(prefix: str, positive: int = 0) -> dict[str, object]:
    states = endpoint_states()
    if positive == 1:
        states["AOIG"] = "POSITIVE"
    elif positive == 2:
        states["AOIG"] = "POSITIVE"
        states["HARMFUL_SEM"] = "POSITIVE"
    elif positive == 3:
        states = endpoint_states("POSITIVE", "POSITIVE", "POSITIVE")
    return {
        "unit_id": f"unit_{prefix}",
        "source_id": f"source_{prefix}",
        "target_id": f"target_{prefix}",
        "access_status": "PASS",
        "endpoint_states": states,
    }


def make_scene(index: int, positive_units: int = 0) -> dict[str, object]:
    return {
        "scene_id": f"scene_{index:02d}",
        "independence_cluster_id": f"cluster_{index:02d}",
        "trajectories": [
            {
                "trajectory_id": "return_short",
                "planned_units": [make_unit(f"{index:02d}_short", int(positive_units >= 1))],
            },
            {
                "trajectory_id": "return_long",
                "planned_units": [make_unit(f"{index:02d}_long", int(positive_units >= 2))],
            },
        ],
    }


def make_cohort(stage: str, positive_scene_count: int, double_positive: bool = False) -> dict[str, object]:
    n = 10 if stage == MODULE.STAGE_C1 else 20
    scenes = [
        make_scene(index, 2 if double_positive and index <= positive_scene_count else int(index <= positive_scene_count))
        for index in range(1, n + 1)
    ]
    return {"schema": MODULE.COHORT_SCHEMA, "stage": stage, "scenes": scenes}


class UnitContractTests(unittest.TestCase):
    def test_all_three_positive_count_once_in_union(self) -> None:
        result = MODULE.evaluate_unit(make_unit("x", 3))
        self.assertTrue(result["union_positive"])
        self.assertEqual(result["planned_lower_positive"], 1)
        self.assertEqual(len(result["positive_endpoints"]), 3)

    def test_one_positive_is_union_positive(self) -> None:
        result = MODULE.evaluate_unit(make_unit("x", 1))
        self.assertTrue(result["union_positive"])
        self.assertTrue(result["endpoint_complete"])

    def test_reference_ineligible_is_incomplete(self) -> None:
        unit = make_unit("x")
        unit["endpoint_states"]["NEGATIVE_STABLE_RCSU"] = "REFERENCE_INELIGIBLE"
        result = MODULE.evaluate_unit(unit)
        self.assertFalse(result["endpoint_complete"])
        self.assertEqual(result["planned_lower_positive"], 0)
        self.assertEqual(result["planned_upper_positive"], 1)

    def test_missing_endpoint_is_incomplete_even_if_other_positive(self) -> None:
        unit = make_unit("x", 1)
        unit["endpoint_states"]["HARMFUL_SEM"] = "TECHNICAL_MISSING"
        result = MODULE.evaluate_unit(unit)
        self.assertTrue(result["union_positive"])
        self.assertFalse(result["endpoint_complete"])

    def test_non_rcsu_reference_ineligible_rejected(self) -> None:
        unit = make_unit("x")
        unit["endpoint_states"]["AOIG"] = "REFERENCE_INELIGIBLE"
        with self.assertRaises(MODULE.ProtocolError):
            MODULE.evaluate_unit(unit)

    def test_access_fail_requires_not_evaluated(self) -> None:
        unit = make_unit("x")
        unit["access_status"] = "FAIL"
        with self.assertRaises(MODULE.ProtocolError):
            MODULE.evaluate_unit(unit)
        unit["endpoint_states"] = endpoint_states("NOT_EVALUATED", "NOT_EVALUATED", "NOT_EVALUATED")
        result = MODULE.evaluate_unit(unit)
        self.assertFalse(result["endpoint_complete"])

    def test_access_missing_requires_not_evaluated(self) -> None:
        unit = make_unit("x")
        unit["access_status"] = "MISSING"
        unit["endpoint_states"] = endpoint_states("NOT_EVALUATED", "NOT_EVALUATED", "NOT_EVALUATED")
        result = MODULE.evaluate_unit(unit)
        self.assertEqual(result["planned_upper_positive"], 1)

    def test_extra_key_rejected(self) -> None:
        unit = make_unit("x")
        unit["free_text"] = "choose-after-results"
        with self.assertRaises(MODULE.ProtocolError):
            MODULE.evaluate_unit(unit)

    def test_bad_identifier_rejected(self) -> None:
        unit = make_unit("x")
        unit["unit_id"] = "not canonical"
        with self.assertRaises(MODULE.ProtocolError):
            MODULE.evaluate_unit(unit)

    def test_non_string_endpoint_rejected(self) -> None:
        unit = make_unit("x")
        unit["endpoint_states"]["AOIG"] = True
        with self.assertRaises(MODULE.ProtocolError):
            MODULE.evaluate_unit(unit)


class RosterAndAggregationTests(unittest.TestCase):
    def test_exactly_one_unit_per_trajectory(self) -> None:
        trajectory = make_scene(1)["trajectories"][0]
        trajectory["planned_units"].append(make_unit("extra"))
        with self.assertRaises(MODULE.ProtocolError):
            MODULE.evaluate_trajectory(trajectory)

    def test_exact_trajectory_roster_required(self) -> None:
        scene = make_scene(1)
        scene["trajectories"][1]["trajectory_id"] = "return_short"
        with self.assertRaises(MODULE.ProtocolError):
            MODULE.evaluate_scene(scene)

    def test_scene_rate_one_half_at_single_discrepancy(self) -> None:
        scene = MODULE.evaluate_scene(make_scene(1, 1))
        self.assertEqual(scene["scene_rate"]["numerator"], 1)
        self.assertEqual(scene["scene_rate"]["denominator"], 2)
        self.assertTrue(scene["scene_positive"])

    def test_scene_rate_zero(self) -> None:
        scene = MODULE.evaluate_scene(make_scene(1, 0))
        self.assertEqual(scene["scene_rate"]["numerator"], 0)
        self.assertFalse(scene["scene_positive"])

    def test_ineligible_reference_blocks_scene(self) -> None:
        scene = make_scene(1, 1)
        scene["trajectories"][1]["planned_units"][0]["endpoint_states"]["NEGATIVE_STABLE_RCSU"] = "REFERENCE_INELIGIBLE"
        result = MODULE.evaluate_scene(scene)
        self.assertFalse(result["evaluable"])
        self.assertIsNone(result["scene_rate"])

    def test_access_failure_blocks_scene_without_replacement(self) -> None:
        scene = make_scene(1)
        unit = scene["trajectories"][0]["planned_units"][0]
        unit["access_status"] = "FAIL"
        unit["endpoint_states"] = endpoint_states("NOT_EVALUATED", "NOT_EVALUATED", "NOT_EVALUATED")
        result = MODULE.evaluate_scene(scene)
        self.assertFalse(result["evaluable"])

    def test_duplicate_unit_within_scene_rejected(self) -> None:
        scene = make_scene(1)
        scene["trajectories"][1]["planned_units"][0]["unit_id"] = scene["trajectories"][0]["planned_units"][0]["unit_id"]
        with self.assertRaises(MODULE.ProtocolError):
            MODULE.evaluate_scene(scene)

    def test_stage1_exact_count_required(self) -> None:
        cohort = make_cohort(MODULE.STAGE_C1, 3)
        cohort["scenes"].pop()
        with self.assertRaises(MODULE.ProtocolError):
            MODULE.evaluate_cohort(cohort)

    def test_duplicate_scene_rejected(self) -> None:
        cohort = make_cohort(MODULE.STAGE_C1, 3)
        cohort["scenes"][1]["scene_id"] = cohort["scenes"][0]["scene_id"]
        with self.assertRaises(MODULE.ProtocolError):
            MODULE.evaluate_cohort(cohort)

    def test_duplicate_cluster_rejected(self) -> None:
        cohort = make_cohort(MODULE.STAGE_C1, 3)
        cohort["scenes"][1]["independence_cluster_id"] = cohort["scenes"][0]["independence_cluster_id"]
        with self.assertRaises(MODULE.ProtocolError):
            MODULE.evaluate_cohort(cohort)

    def test_duplicate_unit_across_scenes_rejected(self) -> None:
        cohort = make_cohort(MODULE.STAGE_C1, 3)
        cohort["scenes"][1]["trajectories"][0]["planned_units"][0]["unit_id"] = (
            cohort["scenes"][0]["trajectories"][0]["planned_units"][0]["unit_id"]
        )
        with self.assertRaises(MODULE.ProtocolError):
            MODULE.evaluate_cohort(cohort)

    def test_input_order_does_not_change_gate(self) -> None:
        cohort = make_cohort(MODULE.STAGE_C1, 4)
        forward = MODULE.evaluate_cohort(cohort)
        reversed_cohort = copy.deepcopy(cohort)
        reversed_cohort["scenes"].reverse()
        for scene in reversed_cohort["scenes"]:
            scene["trajectories"].reverse()
        reverse = MODULE.evaluate_cohort(reversed_cohort)
        self.assertEqual(forward["gate"], reverse["gate"])
        self.assertEqual(forward["scenes"], reverse["scenes"])


class DecisionBoundaryTests(unittest.TestCase):
    def test_stage1_two_positive_stops_for_futility(self) -> None:
        result = MODULE.evaluate_cohort(make_cohort(MODULE.STAGE_C1, 2))
        self.assertEqual(result["gate"]["decision"], "STOP_CONFIRMATION_FOR_FUTILITY")

    def test_stage1_three_positive_continues(self) -> None:
        result = MODULE.evaluate_cohort(make_cohort(MODULE.STAGE_C1, 3))
        self.assertEqual(result["gate"]["decision"], "CONTINUE_TO_STAGE_C2_MAX20")

    def test_stage1_never_emits_success(self) -> None:
        result = MODULE.evaluate_cohort(make_cohort(MODULE.STAGE_C1, 10, True))
        self.assertEqual(result["gate"]["decision"], "CONTINUE_TO_STAGE_C2_MAX20")

    def test_stage2_eight_single_discrepancy_scenes_passes_exactly(self) -> None:
        result = MODULE.evaluate_cohort(make_cohort(MODULE.STAGE_C2, 8))
        self.assertEqual(result["gate"]["scene_positive_count"], 8)
        self.assertEqual(result["gate"]["equal_scene_mean"]["numerator"], 1)
        self.assertEqual(result["gate"]["equal_scene_mean"]["denominator"], 5)
        self.assertEqual(result["gate"]["decision"], "PASS_RAIMA_V4_COMPOSITE_CONFIRMATION_GATE")

    def test_stage2_seven_positive_fails_even_with_large_rates(self) -> None:
        result = MODULE.evaluate_cohort(make_cohort(MODULE.STAGE_C2, 7, True))
        self.assertGreaterEqual(
            Fraction(result["gate"]["equal_scene_mean"]["numerator"], result["gate"]["equal_scene_mean"]["denominator"]),
            Fraction(1, 5),
        )
        self.assertEqual(result["gate"]["decision"], "FAIL_RAIMA_V4_COMPOSITE_CONFIRMATION_GATE")

    def test_arbitrary_rates_count_alone_cannot_pass(self) -> None:
        rates = [Fraction(1, 5)] * 8 + [Fraction(0, 1)] * 12
        result = MODULE.composite_gate_from_scene_rates(rates, MODULE.STAGE_C2)
        self.assertEqual(result["scene_positive_count"], 8)
        self.assertFalse(result["pass_conditions"]["equal_scene_mean_at_least_0.20"])
        self.assertTrue(result["decision"].startswith("FAIL"))

    def test_fraction_type_is_mandatory(self) -> None:
        rates = [Fraction(1, 2)] * 20
        rates[0] = 0.5
        with self.assertRaises(MODULE.ProtocolError):
            MODULE.composite_gate_from_scene_rates(rates, MODULE.STAGE_C2)

    def test_incomplete_evidence_never_reaches_gate(self) -> None:
        cohort = make_cohort(MODULE.STAGE_C2, 20, True)
        unit = cohort["scenes"][0]["trajectories"][0]["planned_units"][0]
        unit["endpoint_states"]["AOIG"] = "TECHNICAL_MISSING"
        result = MODULE.evaluate_cohort(cohort)
        self.assertFalse(result["all_scenes_evaluable"])
        self.assertEqual(result["gate"]["decision"], "BLOCKED_INCOMPLETE_OR_INELIGIBLE_EVIDENCE")


class PowerTests(unittest.TestCase):
    def test_v3_tail_exact(self) -> None:
        value = MODULE.binomial_tail(8, 5, Fraction(1, 5))
        self.assertEqual(value, Fraction(6504, 625000))
        self.assertEqual(MODULE.fraction_record(value)["decimal"], "0.010406400000000000")

    def test_v3_power_at_half_is_low(self) -> None:
        self.assertEqual(MODULE.binomial_tail(8, 5, Fraction(1, 2)), Fraction(93, 256))

    def test_v4_type_one_upper_bound(self) -> None:
        value = MODULE.two_stage_success_probability(Fraction(1, 5))
        self.assertLess(value, Fraction(1, 20))
        self.assertEqual(MODULE.fraction_record(value)["decimal"], "0.029978782278531154")

    def test_v4_count_power_at_half(self) -> None:
        value = MODULE.two_stage_success_probability(Fraction(1, 2))
        self.assertGreater(value, Fraction(4, 5))
        self.assertEqual(MODULE.fraction_record(value)["decimal"], "0.850114822387695312")

    def test_expected_n_under_null(self) -> None:
        value = MODULE.two_stage_expected_scene_count(Fraction(1, 5))
        self.assertEqual(MODULE.fraction_record(value)["decimal"], "13.222004736000000000")

    def test_expected_n_at_half(self) -> None:
        value = MODULE.two_stage_expected_scene_count(Fraction(1, 2))
        self.assertEqual(value, Fraction(1245, 64))

    def test_invalid_probability_rejected(self) -> None:
        for value in (0.2, "0.2", True, Fraction(-1, 10), Fraction(11, 10)):
            with self.subTest(value=value), self.assertRaises(MODULE.ProtocolError):
                MODULE.two_stage_success_probability(value)

    def test_randomized_composite_invariants_512_cases(self) -> None:
        rng = random.Random(440031)
        for _ in range(512):
            rates = [Fraction(rng.randrange(0, 1001), 1000) for _ in range(20)]
            result = MODULE.composite_gate_from_scene_rates(rates, MODULE.STAGE_C2)
            passed = result["decision"] == "PASS_RAIMA_V4_COMPOSITE_CONFIRMATION_GATE"
            self.assertEqual(passed, all(result["pass_conditions"].values()))
            expected_count = sum(rate >= Fraction(1, 5) for rate in rates)
            self.assertEqual(result["scene_positive_count"], expected_count)
            exact_mean = sum(rates, Fraction(0, 1)) / 20
            self.assertEqual(
                Fraction(result["equal_scene_mean"]["numerator"], result["equal_scene_mean"]["denominator"]),
                exact_mean,
            )


class PackageContractTests(unittest.TestCase):
    @staticmethod
    def load_json(name: str) -> dict[str, object]:
        with (PACKAGE_DIR / name).open("r", encoding="utf-8") as handle:
            value = json.load(handle)
        if not isinstance(value, dict):
            raise AssertionError(f"{name} must contain a JSON object")
        return value

    def test_estimand_roster_and_claim_boundary(self) -> None:
        spec = self.load_json("ESTIMAND_TABLE.json")
        self.assertEqual(spec["method_status"], "NO_METHOD_SELECTED")
        self.assertEqual(spec["novelty_status"], "NONE")
        self.assertEqual([item["id"] for item in spec["estimands"]], list(MODULE.ENDPOINT_IDS))
        self.assertEqual(spec["primary_composite"]["planned_denominator"], "exactly two units per scene, one return_short and one return_long")

    def test_reference_binding_is_fail_closed_on_blocked_v6(self) -> None:
        binding = self.load_json("REFERENCE_CONTRACT_BINDING.json")
        self.assertFalse(binding["execution_eligible"])
        self.assertIsNone(binding["active_contract"])
        self.assertEqual(binding["blocked_predecessor"]["fresh_review_verdict"], "BLOCKED")
        self.assertEqual(
            binding["blocked_predecessor"]["fresh_review_sha256"],
            "9c6900e18388519d9b274ce60c2d42c66c6694eb24290f4e1903b83fb3aef09a",
        )
        self.assertEqual(binding["future_binding_gate"]["required_status"], "PASS_S48_V7_FRESH_NON_AUTHOR_SOURCE_REVIEW")

    def test_scene_sampling_frame_is_unpopulated_and_fixed(self) -> None:
        sampling = self.load_json("SCENE_SAMPLING_MANIFEST.json")
        slots = sampling["scene_slots"]
        self.assertEqual(len(slots), 20)
        self.assertEqual([item["slot_id"] for item in slots], [f"C{index:02d}" for index in range(1, 21)])
        self.assertTrue(all(item["actual_scene_id"] is None for item in slots))
        self.assertEqual(sampling["per_scene_contract"]["trajectory_roster"], list(MODULE.TRAJECTORY_IDS))
        self.assertEqual(sampling["per_scene_contract"]["seed_roster"], [101, 211, 307, 401, 503])
        self.assertEqual(sampling["sampling_frame_contract"]["candidate_registry_minimum"], 40)

    def test_current_tum_reference_metadata_gate_is_bound_and_blocked(self) -> None:
        sampling = self.load_json("SCENE_SAMPLING_MANIFEST.json")
        gate = sampling["current_local_dataset_gate"]
        self.assertTrue(gate["status"].startswith("BLOCKED_CURRENT_TUM"))
        self.assertEqual(
            gate["external_metadata_report_sha256"],
            "02dd1b304fc9e84bc4f99cd3b3ccfcf0fdee0685f7f14907edaa21959e07c8eb",
        )
        self.assertIn("cannot populate", gate["decision"])
        self.assertIn("do not relax", gate["forbidden_resolution"])
        self.assertTrue(any("same capture stream" in item for item in gate["observations"]))

    def test_power_manifest_matches_pure_functions(self) -> None:
        power = self.load_json("POWER_AND_SENSITIVITY.json")
        operating = power["v4_two_stage_design"]["exact_count_operating_characteristics"]
        self.assertEqual(
            operating["type_one_upper_bound_at_p0_0_20"],
            MODULE.fraction_record(MODULE.two_stage_success_probability(Fraction(1, 5))),
        )
        self.assertEqual(
            operating["count_power_upper_bound_at_p1_0_50"],
            MODULE.fraction_record(MODULE.two_stage_success_probability(Fraction(1, 2))),
        )
        self.assertEqual(
            operating["expected_n_at_p0_0_20"],
            MODULE.fraction_record(MODULE.two_stage_expected_scene_count(Fraction(1, 5))),
        )

    def test_hypothesis_registry_is_finite_and_nonadaptive(self) -> None:
        registry = self.load_json("FINITE_HYPOTHESIS_REGISTRY.json")
        self.assertEqual(len(registry["confirmatory_hypotheses"]), 1)
        self.assertEqual(registry["multiplicity_policy"]["confirmatory_family_size"], 1)
        self.assertEqual(registry["multiplicity_policy"]["alpha_recycling"], "none")
        retired = {item["id"]: item["status"] for item in registry["retired_or_deferred"]}
        self.assertEqual(retired["V3_SECONDARY_HOLM"], "NOT_CARRIED_FORWARD")
        self.assertEqual(retired["METHOD_GAIN"], "NOT_REGISTERED_FOR_V4")

    def test_compute_budget_matches_registered_process_formula(self) -> None:
        compute = self.load_json("COMPUTE_MANIFEST.json")
        accounting = compute["arm_accounting"]
        stages = {item["stage"]: item for item in compute["stage_budgets"]}
        for scene_count, stage_name in ((10, "Stage C1 futility look"), (20, "Stage C2 maximum")):
            groups = scene_count * accounting["trajectories_per_scene"] * accounting["seeds_per_unit"]
            self.assertEqual(stages[stage_name]["scene_trajectory_seed_groups"], groups)
            self.assertEqual(stages[stage_name]["minimum_target_processes"], groups * accounting["minimum_target_processes_per_seed_unit"])
            self.assertEqual(stages[stage_name]["expanded_target_processes"], groups * accounting["expanded_target_processes_per_seed_unit"])

        expected = compute["expected_two_stage_budget"]
        stage2 = stages["Stage C2 maximum"]
        per_scene_min_hours = Decimal(stage2["minimum_serial_hours"]) / Decimal(20)
        per_scene_expanded_hours = Decimal(stage2["expanded_serial_hours"]) / Decimal(20)
        for label, expected_n in (("under_p0_0_20", Decimal("13.222004736")), ("under_p1_0_50", Decimal("19.453125"))):
            self.assertEqual(Decimal(expected[label]["minimum_serial_days"]), per_scene_min_hours * expected_n / Decimal(24))
            self.assertEqual(Decimal(expected[label]["expanded_serial_days"]), per_scene_expanded_hours * expected_n / Decimal(24))

    def test_novelty_matrix_contains_required_collision_boundaries(self) -> None:
        text = (PACKAGE_DIR / "NOVELTY_MATRIX.md").read_text(encoding="utf-8")
        for required in (
            "NO_METHOD_SELECTED",
            "新颖性授权：`NONE`",
            "WorldTrace / LoopBench",
            "Spatia",
            "Plenoptic Video Generation",
            "GIM-World",
            "Addressing divergent representations from causal interventions",
            "Outputs of generative diffusion models are often unattributable",
            "ordinary-selected runtime source",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)

    def test_all_source_only_execution_counters_are_zero(self) -> None:
        compute = self.load_json("COMPUTE_MANIFEST.json")
        self.assertEqual(set(compute["current_counts"].values()), {0})
        self.assertEqual(compute["execution_authorization"], "NONE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
