# Pre-Gate Ghosting Mechanism Diagnostic

Date: 2026-09-16 (Asia/Shanghai)

## Question

Does the lower RGB MSE observed in the sealed S86/S87 outputs coincide with
edge instability or high-frequency excess that is visually compatible with
ghosting and smearing?

## Evidence boundary

This is a saved-output-only reanalysis of one already-seen static scene and
four already-seen target views (20--23). It reads the sealed S86 `G0` and
`Gguide` outputs, the sealed S87 `Gpaste_l075` and `Gterminal_l075` outputs,
and the four sealed same-scene reference PNGs. It performs no model inference,
does not read held-out future ground truth, and does not change any generation
output or historical score.

The output is an exploratory mechanism diagnostic. Edge F1, gradient ratio,
and second-difference energy are image proxies. They are not perceptual
judgments, geometric accuracy, causal effects, or evidence that a proposed
memory selector works.

## Measured results

All arms contain four complete targets. The table reports the mean over the
four targets. `edge F1` uses a threshold fixed by the reference image's 90th
gradient percentile. `HF ratio` is generated second-difference energy divided
by reference second-difference energy. `edge-band excess` is the positive
gradient excess on reference high-gradient pixels.

| arm | RGB MSE | edge F1 | gradient ratio | HF ratio | edge-band excess |
|---|---:|---:|---:|---:|---:|
| G0 | 0.13116667 | 0.1295 | 1.0733 | 1.2229 | 0.004521 |
| Gguide | 0.05242222 | 0.1644 | 1.0946 | 2.5887 | 0.003412 |
| Gpaste l075 | 0.05336067 | 0.2449 | 2.2011 | 19.5367 | 0.027432 |
| Gterminal l075 | 0.05116758 | 0.2297 | 1.4824 | 6.7826 | 0.010747 |

## Interpretation

Within this narrow, retrospective setting, Gterminal l075 has the lowest
RGB MSE, while its high-frequency energy remains substantially above the
reference. Gpaste l075 has a slightly higher MSE but a much larger
high-frequency excess. This is compatible with a mixture of sharp
disagreement, duplicated edges, and local ringing, but the proxy cannot tell
which visual cause dominates.

Gguide has lower MSE than G0 and a higher high-frequency ratio than G0. Thus
the existing result supports the already-recorded warning: lower pixel error
can coexist with edge or shape defects. The numbers do not establish that
geometry injection causes ghosting, nor do they show that terminal fusion is
better overall. Target-level values remain in `RESULTS.json`; no target was
dropped.

## Scientific decision

This result is useful for designing the next experiment, not for selecting a
method. It supports a pre-registered held-out diagnostic with:

1. an independent RGB-D and pose-qualified split;
2. the same candidate pool and fixed compute budget;
3. a perceptual or human edge/ghosting assessment in addition to RGB MSE;
4. a geometry metric evaluated against isolated future ground truth;
5. fixed image-resolution, blur, and edge thresholds decided before scoring.

Until those conditions are available, `novelty_authorization=NONE` and
`new_method_validated=false` remain unchanged. The formal GRC experiment
remains blocked by the project's Gate 0.

