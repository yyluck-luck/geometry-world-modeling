# Top-two candidate prioritization (reviewer-style, 2026-09-15)

**Status:** Both candidates are falsifiable research hypotheses only. This note
does not establish novelty, method validity, or a positive result:
`NO_METHOD_SELECTED`, `novelty_authorization=NONE`, and
`new_method_validated=false` remain unchanged.

## Priority 1: IDEA-1, inconsistency/error-correlation weighting

**Claim to test.** Repeated access is not a reliable proxy for geometric
correctness when observations share systematic estimator errors. A memory item
or subset selected using cross-observation inconsistency should outperform
access-count selection under the same pool, budget, and target views.

**Why it deserves first test.** It has the clearest mechanism-level distinction
from coverage, redundancy, and future-aware selection: it tests correlated error
structure rather than merely input diversity. It also has a cheap precursor
test and can be run from saved predictions if the surfel-to-error linkage is
auditable. The main reviewer concern is confounding by scene structure,
visibility, and coverage; any positive correlation must therefore survive
within-region and coverage-matched stratification.

**Minimum falsification protocol.**

1. Freeze one candidate pool, target set, geometry/error definition, and memory
   budget. Do not tune the selector on future held-out outcomes.
2. Test the association between visit count `|I_k|` and the same item's
   geometric error, with confidence intervals and coverage-matched strata.
3. Only if the association passes the gate, compare count selection with
   inconsistency selection at equal memory size and equal compute, then score
   held-out future geometry and revisit metrics.

**Exact kill criteria.**

- **Kill immediately** if the predeclared association between `|I_k|` and
  geometric error is zero or negative in the primary analysis, or if its
  uncertainty interval includes the null and the prespecified minimum effect
  is not met. This removes the proposed “repeated confirmation reinforces
  systematic error” premise.
- **Kill the selector** if inconsistency weighting does not beat count/coverage
  selection on the primary held-out future-error metric at equal budget, or if
  the difference is not reproducible across the predeclared target strata.
- **Kill the candidate as a standalone contribution** if any apparent gain
  disappears after matching coverage, source identity, confidence, pose, and
  region composition, or if it is explained by AnchorWeave-style global
  cross-view misalignment.
- **Do not promote** on a saved-data correlation alone: without a legal
  held-out revisit evaluation, the result remains a diagnostic signal.

## Priority 2: IDEA-2, CVaR tail-risk selection

**Claim to test.** Selection that optimizes the upper tail of future error
(CVaR) can reduce confident catastrophic failures, even when mean-oriented
coverage selection has similar average performance.

**Why it deserves second test.** It directly targets the project's failure mode
of confidently wrong retained geometry and supplies a precise decision objective.
It is also a clean comparison against existing expectation-oriented selectors.
The reviewer risks are substantial: CVaR can be vacuous when the error
distribution is not heavy-tailed, and an apparent tail gain can simply trade
away coverage or average quality.

**Minimum falsification protocol.**

1. Freeze the same candidate pool, target set, compute/memory budget, and
   held-out revisit split for coverage-greedy and CVaR-sequential-greedy.
2. Predeclare the tail level (for example, 90%), report the full error
   distribution, mean, coverage, and the CVaR value, plus the curvature or
   approximation term used by the optimization.
3. Compare paired target views and report uncertainty, not only the best
   scene-level number.

**Exact kill criteria.**

- **Kill immediately** if the primary 90th-percentile/CVaR future-error
  reduction is absent, non-reproducible across the predeclared strata, or
  favors coverage-greedy under equal budget.
- **Kill as a mechanism** if the error distribution is not meaningfully
  heavy-tailed under the frozen protocol and CVaR is empirically
  indistinguishable from mean optimization.
- **Kill the candidate as a standalone contribution** if its tail improvement
  requires lower coverage, higher compute, or worse mean/revisit performance
  beyond predeclared tolerances, or if a simpler inconsistency-weighted
  selector explains the same gain.
- **Do not promote** from a synthetic or retrospective saved-data tail plot;
  require held-out future geometry plus an open-domain revisit probe such as
  MemoryGain/NMR.

## Reviewer decision

Run IDEA-1's association gate first. If it dies, stop both the
“visit-count reinforces shared error” story and any attempt to present IDEA-2
as its direct continuation. If it survives, test IDEA-1 against the frozen
coverage/count baselines, then test whether CVaR adds a distinct tail benefit.
A null result is a valid research outcome; neither candidate should be called
novel or effective before independent source de-duplication and held-out
evaluation.
