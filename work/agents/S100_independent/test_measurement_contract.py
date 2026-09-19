"""Independent analytic counterexamples, not real-data/production-code tests."""
from fractions import Fraction
from itertools import combinations
from pathlib import Path
from datetime import datetime, timezone
import io
import json
import math
import time
import unittest


def full_gt_losses(gt, predicted, cap=1.0):
    if len(gt) != len(predicted) or cap <= 0:
        raise ValueError("Invalid shape or cap")
    losses = []
    for truth, estimate in zip(gt, predicted):
        if not math.isfinite(truth) or truth <= 0:
            continue
        if estimate is None or not math.isfinite(estimate) or estimate <= 0:
            losses.append(float(cap))
        else:
            losses.append(min(abs(estimate / truth - 1.0), cap))
    if not losses:
        raise ValueError("No valid GT pixels; cannot report a zero loss")
    return losses


def mean(values):
    return math.fsum(values) / len(values)


def fractional_worst5(values):
    """Exact 5% empirical mass; boundary pixel contributes fractional weight."""
    ordered = sorted(values, reverse=True)
    mass = Fraction(len(ordered), 20)
    if mass <= 0:
        raise ValueError("Empty evaluation domain")
    total = 0.0
    for value in ordered:
        weight = min(Fraction(1), mass)
        total += float(weight) * value
        mass -= weight
        if mass == 0:
            break
    return total / (len(ordered) / 20)


def conditions(background, low, conf):
    if len(background) != 155 or low in background or conf in background:
        raise ValueError("Candidates must both be outside the 155-block context")
    if low == conf or low[0] != conf[0]:
        raise ValueError("Distinct candidates must have the same source")
    left, right = background | {low}, background | {conf}
    for condition in (left, right):
        if len(condition) != 156 or any(sum(s == k for s, _ in condition) != 39 for k in range(4)):
            raise ValueError("Each source must have exactly 39 blocks")
    return left, right


class MeasurementCounterexamples(unittest.TestCase):
    def test_01_deleting_any_prediction_never_improves_mean_or_tail(self):
        gt, pred = [1.0] * 5, [1.0, 1.2, 1.9, 3.0, 10.0]
        for cap in (0.5, 1.0, 2.0):
            before = full_gt_losses(gt, pred, cap)
            for size in range(6):
                for dropped in combinations(range(5), size):
                    after = full_gt_losses(gt, [None if k in dropped else p for k, p in enumerate(pred)], cap)
                    self.assertGreaterEqual(mean(after) + 1e-14, mean(before))
                    self.assertGreaterEqual(fractional_worst5(after) + 1e-14, fractional_worst5(before))
        # Capping permits ties, not strict worsening, for already saturated errors.
        self.assertEqual(full_gt_losses([1], [10]), full_gt_losses([1], [None]))

    def test_02_invalid_prediction_stays_in_gt_denominator(self):
        losses = full_gt_losses([2] * 5 + [0, math.nan], [2, 0, math.nan, math.inf, -1, 99, 99])
        self.assertEqual(losses, [0, 1, 1, 1, 1])
        self.assertEqual(mean(losses), 0.8)
        with self.assertRaises(ValueError):
            full_gt_losses([0, math.nan], [1, 1])
        # Changing a correct prediction into a hole increases loss at every cap.
        for cap in (0.5, 1, 2):
            self.assertEqual(mean(full_gt_losses([1], [None], cap)), cap)

    def test_03_fractional_tail_does_not_round_pixel_count(self):
        # 30 pixels -> top mass 1.5: (10 + 0.5*4)/1.5 = 8, not top-2 mean 7.
        self.assertEqual(fractional_worst5([10, 4] + [0] * 28), 8)
        self.assertEqual(fractional_worst5([4, 3, 2, 1]), 4)
        self.assertAlmostEqual(fractional_worst5([7] * 31), 7, places=14)

    def test_04_signed_pair_gain_and_tail_order(self):
        low = full_gt_losses([10, 10], [12, 14])
        conf = full_gt_losses([10, 10], [11, 11])
        gain = mean(low) - mean(conf)
        self.assertAlmostEqual(gain, 0.2)
        self.assertGreater(gain, 0)
        self.assertAlmostEqual(mean(conf) - mean(low), -gain)
        self.assertAlmostEqual(mean([a-b for a, b in zip(low, conf)]), gain)
        # Tail comparison is CVaR(low)-CVaR(conf), not CVaR(pixelwise gain).
        a, b = [1.0, 0.0], [0.0, 0.9]
        self.assertAlmostEqual(fractional_worst5(a)-fractional_worst5(b), 0.1)
        self.assertEqual(fractional_worst5([x-y for x, y in zip(a, b)]), 1.0)

    def test_05_per_source_budget_and_background_identity(self):
        context = {(s, k) for s in range(4) for k in range(38 if s == 0 else 39)}
        low, conf = (0, 80), (0, 90)
        left, right = conditions(context, low, conf)
        self.assertEqual(left & right, context)
        self.assertEqual(left ^ right, {low, conf})
        with self.assertRaises(ValueError):
            conditions(context, low, (1, 90))
        with self.assertRaises(ValueError):
            conditions(context, low, (0, 1))

    def test_06_occlusion_breaks_additivity_and_reverses_gain(self):
        # Toy one-ray z-buffer with GT=10; fallback depth=20.
        # Candidate low=12 and confidence=9: conf wins without other geometry.
        loss = lambda candidates: abs(min([20.0] + candidates) / 10 - 1)
        low, conf = 12.0, 9.0
        no_context_gain = loss([low]) - loss([conf])
        fixed_context_gain = loss([10.5, low]) - loss([10.5, conf])
        self.assertGreater(no_context_gain, 0)
        self.assertLess(fixed_context_gain, 0)
        sum_single_gain = (loss([])-loss([low])) + (loss([])-loss([conf]))
        actual_joint_gain = loss([])-loss([low, conf])
        self.assertAlmostEqual(sum_single_gain, 1.7)
        self.assertAlmostEqual(actual_joint_gain, 0.9)
        self.assertNotEqual(sum_single_gain, actual_joint_gain)


if __name__ == "__main__":
    start = datetime.now(timezone.utc)
    tick = time.perf_counter()
    output = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(MeasurementCounterexamples)
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
    report = {"started_utc": start.isoformat(), "completed_utc": datetime.now(timezone.utc).isoformat(),
              "elapsed_seconds": time.perf_counter()-tick, "evidence_type": "SYNTHETIC_ANALYTIC_CHECKS_ONLY",
              "real_gt_or_scores_read": False, "production_code_imported": False,
              "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
              "passed": result.wasSuccessful(), "output": output.getvalue()}
    Path(__file__).with_name("ANALYTIC_TEST_RECEIPT.json").write_text(json.dumps(report, indent=2)+"\n")
    print(output.getvalue(), end="")
    raise SystemExit(0 if result.wasSuccessful() else 1)
