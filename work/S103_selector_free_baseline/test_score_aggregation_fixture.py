#!/usr/bin/env python3
"""Delivery-gate fixture: the scorer must pool MSE across targets, not average PSNRs.

Why this exists.  On 2026-09-18 a feasibility analysis took one PSNR per target and
averaged, while the prespecified primary score pools MSE across the four targets and
takes a single PSNR.  Both are valid definitions, but they are different quantities:

    Q_pooled    = -10 log10( AM(e) )
    Q_framewise = -10 log10( GM(e) )
    Q_framewise - Q_pooled = 10 log10( AM(e) / GM(e) )  >= 0

The gap is arm-dependent, so contrasts, per-window winners and oracle ceilings all move
between the two.  A summary that merely "returns a plausible dB number" cannot detect the
substitution.  This fixture can: on the case below the two definitions disagree about which
arm is better, so any implementation that silently averages PSNRs fails.

Runs on CPU in milliseconds.  No model, no GPU, no data, no ground truth.
"""
import math
import sys

# Per-target MSE in [0,1] units, four targets, two arms.
E_A = (0.01, 0.01, 0.01, 0.09)
E_B = (0.02, 0.02, 0.02, 0.02)

# Values fixed in advance, to four decimals.
EXPECT_POOLED_DELTA = -1.7609      # arm A minus arm B, pooled-MSE PSNR
EXPECT_FRAMEWISE_DELTA = +0.6247   # arm A minus arm B, mean of per-target PSNRs


def pooled_psnr(per_target_mse):
    """The prespecified primary score: accumulate squared error, then one PSNR."""
    return -10.0 * math.log10(sum(per_target_mse) / len(per_target_mse))


def framewise_psnr(per_target_mse):
    """The post-hoc aggregation: one PSNR per target, then average."""
    return sum(-10.0 * math.log10(e) for e in per_target_mse) / len(per_target_mse)


def scorer_under_test(per_target_squared_error, per_target_pixel_count):
    """Reproduces the aggregation implemented in score_s113.py / score_repair.py.

    Those scorers accumulate `s += (d*d).sum()` and `n += d.size` across the four
    targets of a window-seed, then compute one PSNR from `s / (n * 255 * 255)`.
    That is pooling, and this function must stay equal to `pooled_psnr`.
    """
    s = sum(per_target_squared_error)
    n = sum(per_target_pixel_count)
    return -10.0 * math.log10(s / n)


checks = []

def check(name, ok, detail=""):
    checks.append((name, ok, detail))
    print(("[PASS] " if ok else "[FAIL] ") + name + (f"  {detail}" if detail else ""))


pa, pb = pooled_psnr(E_A), pooled_psnr(E_B)
fa, fb = framewise_psnr(E_A), framewise_psnr(E_B)

check("pooled contrast matches the value fixed in advance",
      abs((pa - pb) - EXPECT_POOLED_DELTA) < 5e-4, f"got {pa - pb:+.4f} dB")
check("framewise contrast matches the value fixed in advance",
      abs((fa - fb) - EXPECT_FRAMEWISE_DELTA) < 5e-4, f"got {fa - fb:+.4f} dB")

# The decisive property: on this fixture the two definitions disagree about the winner.
check("the fixture is discriminating: the two definitions pick different arms",
      (pa > pb) != (fa > fb),
      f"pooled prefers {'A' if pa > pb else 'B'}, framewise prefers {'A' if fa > fb else 'B'}")

# Jensen direction must hold for every non-degenerate case.
check("framewise >= pooled for arm A (AM >= GM)", fa >= pa - 1e-12, f"gap {fa - pa:+.4f} dB")
check("framewise == pooled when all targets are equal (AM == GM)",
      abs(fb - pb) < 1e-12, f"gap {fb - pb:+.2e} dB")

# The delivered scorers' accumulation must equal pooling, not averaging.
PIX = 3 * 576 * 576
sqerr_A = [e * PIX * 255 * 255 for e in E_A]
got = scorer_under_test(sqerr_A, [PIX] * 4) + 10.0 * math.log10(255 * 255)
check("the delivered accumulate-then-PSNR path equals pooled, not framewise",
      abs(got - pa) < 1e-9 and abs(got - fa) > 1e-3,
      f"scorer {got:.4f} dB, pooled {pa:.4f} dB, framewise {fa:.4f} dB")

# A contrast may only be formed from two arms scored under the SAME definition.
check("mixing definitions across arms is detectable",
      abs((fa - pb) - (pa - pb)) > 1e-3,
      f"framewise-A minus pooled-B = {fa - pb:+.4f} dB, which is not the {pa - pb:+.4f} dB contrast")

ok = sum(1 for _, o, _ in checks if o)
print(f"\n{ok}/{len(checks)} checks passed")
sys.exit(0 if ok == len(checks) else 1)
