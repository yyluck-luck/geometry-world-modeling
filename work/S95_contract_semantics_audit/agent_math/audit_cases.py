#!/usr/bin/env python3
"""Small exact counterexamples for S94 semantics; no project data or models."""
from __future__ import annotations

from fractions import Fraction
from itertools import product
from math import comb


def worst5(xs: list[Fraction]) -> Fraction:
    n = len(xs)
    m = max(1, (n + 19) // 20)  # smallest integer set containing 5 percent
    return sum(sorted(xs, reverse=True)[:m], Fraction(0)) / m


def cvar_strict(xs: list[Fraction], alpha: Fraction = Fraction(95, 100)):
    ys = sorted(xs)
    q = ys[(len(ys) - 1) * alpha.numerator // alpha.denominator]
    tail = [x for x in xs if x > q]
    return None if not tail else sum(tail, Fraction(0)) / len(tail), q


def trajectory_bootstrap_ci(delta: list[Fraction]):
    """Percentile CI over 5 clustered trajectories, with exact enumeration."""
    vals = []
    for draw in product(delta, repeat=len(delta)):
        vals.append(sum(draw, Fraction(0)) / len(draw))
    vals.sort()
    return vals[int(Fraction(25, 100) * (len(vals) - 1))], vals[int(Fraction(975, 1000) * (len(vals) - 1))]


def main() -> None:
    # CVaR with ties: worst-5% is defined over the top 5%; strict exceedance
    # can be empty or return a different mass. Both are legal-looking readings.
    ties = [Fraction(0)] * 94 + [Fraction(1)] * 5 + [Fraction(10)]
    strict, q = cvar_strict(ties)
    assert worst5(ties) == Fraction(14, 5)  # (10 + 4*1) / 5
    assert strict == Fraction(10) and q == Fraction(1)
    all_equal = [Fraction(1)] * 20
    strict_equal, q_equal = cvar_strict(all_equal)
    assert strict_equal is None and q_equal == Fraction(1)

    # Five trajectories are clustered observations, not 15 future queries.
    # With all paired differences negative, a two-sided exact sign test is
    # 2 / 2**5 = 0.0625, so n=5 cannot support a generic 0.05 claim by itself.
    sign_p = Fraction(2, 2**5)
    assert sign_p == Fraction(1, 16)
    ci = trajectory_bootstrap_ci([Fraction(-1)] * 5)
    assert ci == (Fraction(-1), Fraction(-1))

    # k=8 sensitivity is undefined when the Gate-0 candidate minimum is six.
    assert comb(6, 8) == 0

    # A calibrated marginal risk bound need not be safe after selection.
    # Let subgroup B occupy 5% of the population and always fail while A
    # never fails. A fixed q=0 has 95% marginal coverage, but selecting B
    # from a covariate can have 100% conditional failure.
    marginal_error = Fraction(5, 100)
    subgroup_B_error = Fraction(100, 100)
    assert marginal_error == Fraction(1, 20)
    assert subgroup_B_error == 1

    # Unit/scale non-invariance of q=Q(r_i) for a vector of unlike residuals.
    # The same physical observation changes rank when depth is represented in
    # metres versus millimetres, unless component normalization is frozen.
    risk_m = Fraction(1, 1) + Fraction(1, 10) + Fraction(1, 1)
    risk_mm = Fraction(1, 1) + Fraction(100, 1) + Fraction(1, 1)
    assert risk_m != risk_mm

    print("S95_CONTRACT_SEMANTICS_AUDIT_PASS")
    print({
        "worst5_tie_case": str(worst5(ties)),
        "strict_cvar_tie_case": str(strict),
        "strict_cvar_all_equal": strict_equal,
        "five_trajectory_sign_p": str(sign_p),
        "five_trajectory_percentile_bootstrap_ci": [str(x) for x in ci],
        "choose_8_from_6": comb(6, 8),
        "marginal_error": str(marginal_error),
        "selected_subgroup_error": str(subgroup_B_error),
        "risk_m_vs_mm": [str(risk_m), str(risk_mm)],
    })


if __name__ == "__main__":
    main()
