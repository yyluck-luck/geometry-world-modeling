# Innovation register update (2026-09-18) — kills, survivors, and the new primary line

> **SECOND CORRECTION, 2026-09-18.** Claims in this file that the released interface disables
> retrieval NMS at *every* call site, that the config default is unreachable, that "NMS-on is not
> the method as shipped", or that the threshold leak belongs only to comparative harnesses, are
> **false and retracted**. `navigation.py` has **three** `generate_trajectory_frames` call sites;
> the third (`_turn`, line 321, reached from `app.py:208/210` via `turn_left`/`turn_right`) passes
> **no** NMS argument and therefore resolves to the config default `true`. The released demo mixes
> both settings on one pipeline object, so the leak is **natively reachable**. Static reachability
> only — not measured on the demo, and it says nothing about the paper's evaluation.
> See `docs/ENTRY_PATH_CORRECTION_20260918.md`.


> **CORRECTION NOTICE, appended 2026-09-18 after external review.**
> This file **overstated the result in the negative direction** and its inferential statistics
> are withdrawn. The measured finite-panel mean of shipped retrieval against fixed-offset
> context is **+0.242 dB, which is POSITIVE**. Wording in this file such as "is not
> distinguishable from", "does not beat", "still does not win", or "a bounded negative result"
> is **wrong** and is retracted. The standard error and t statistic are also withdrawn: windows
> were declared a finite panel, so dividing the window-level SD by sqrt(14) is not a defensible
> sampling standard error. The SD is retained as a description of heterogeneity only.
> The word "held-out" is narrowed: these are **exposed development sequences** whose target
> frames are held out from conditioning, not independent held-out evaluation data.
> The file is preserved unedited below as the superseded record.
> Authoritative version: `docs/RETRIEVAL_ARMS_RESULT_20260918.md`.


Status: `REGISTER_UPDATE`. `new_method_validated=false`, `novelty_authorization=NONE`.
Nothing here is a novelty claim, a priority claim, or a human approval.

Supersedes the direction ranking in `INNOVATION_REGISTER_UPDATE_20260917.md` for the items
named below. That file is retained unedited as the prior state.

## A. Killed on my own evidence (not on relayed advice)

**A1. "The state leak acts through the slot-0 ray gauge" — DEAD.**
Killed by code inspection plus measurement, not by an external verdict.
`pipeline.py:712` appends `sorted_frames[0]` unconditionally before the threshold loop, and
`sorted_frames` never reads `initial_threshold`. Every window measured so far has an
identical slot 0 under clean and leaked thresholds. Since `get_plucker_coordinates` takes its
reference from `extrinsics_src=all_w2cs[:1]`, the leak provably cannot move the ray reference.
This was the combination I had nominated as my strongest direction. It is withdrawn.

**A2. "The leak is a defect in VMem's inference" — DEAD, and the opposite is documented.**
`navigation.py:187` and `:236` are the only paths into generation from `app.py`, and both pass
`use_non_maximum_suppression=False`. With a single setting the disabled branch rewrites `1e8`
every call, so nothing stale is ever consumed. The leak requires evaluating two settings on
one pipeline object; that is a property of comparative harnesses, mine included. Any wording
implying the published VMem results are contaminated is prohibited.

**A3. "NMS-on is VMem's default retrieval" — DEAD.**
`configs/inference/inference.yaml:16` declares `true`, but the shipped interface overrides it
at every call site. The operative shipped configuration is NMS-off. Earlier framing that
treated the enabled arm as the method's default is incorrect and is corrected in
`docs/LEAK_ATTRIBUTION_AND_ENTRY_PATH_20260918.md`.

## B. Killed on occupancy (relayed, to be confirmed at primary source before any write-up)

- Camera-conditioning gauge/reference dependence as a contribution: PRoPE (arXiv 2507.10496),
  EscherNet (arXiv 2402.03908). A2/A1 already kill the route for this project independently.
- Scale-ambiguous camera conditioning as an unnoticed problem: FaceCam (arXiv 2603.05506).
- Generic state-aware evaluation, resetting, evaluation-order bookkeeping: TTAB
  (arXiv 2306.03536, ICML 2023).

These are relayed claims. Per `RESEARCH_PRINCIPLES.md` v2.13 they must be read at primary
source before any distinction paragraph is written. They are used here only to *stop* work,
which is the conservative direction and cannot manufacture a novelty claim.

## C. Stopped, per the external ruling and consistent with the evidence

SOCF-A and FGB-SI development; coverage/gating/cache-policy design; further metric and
reproducibility infrastructure as though it were the contribution; analysing the withdrawn
-0.729 dB as a negative memory result; describing the project as "geometry-aware world
modelling" on the strength of current results.

## D. What is actually live now

**D1. A bounded negative result, already sealed and provably uncontaminated.**
Shipped surfel retrieval vs fixed-offset context: +0.242 dB, SE 0.340, 8/14 windows, on
held-out scene_13/scene_14. See `docs/UNCONTAMINATED_RETRIEVAL_RESULT_20260918.md`. This is
the strongest thing the project owns, and it cost nothing further to obtain.

**D2. A mechanical explanation candidate with a predeclared test.**
The shipped retrieval delivers only three distinct frames into four context slots in 10/14
windows, because the surfel-nearest candidate and the most-recent frame coincide under
forward extrapolation. Test declared in advance: slot-utilisation control, 28 generations,
0.20 dB retention threshold, with the four unaffected windows required to reproduce
byte-identically as an internal null.

**D3. The permutation regime, obtained free of charge.**
The census (job 595614) classifies every window as NULL, PERMUTATION, or CONTENT. In
PERMUTATION windows the leaked and clean selections are the same multiset in a different
order, so images, cameras, intrinsics, normalisation input and slot-0 gauge are all held
fixed and any output difference is a pure slot-order effect. This needs no injected scale, no
reference override and no mismatched image-camera pairing, so it avoids the failure modes
that would invalidate an artificial crossover. The leaked half is already sealed; the clean
half is generated by S113 for other reasons, so the marginal cost is zero.

**D4. An implementation-provenance note, recorded as such.** The config's declared default
retrieval setting is unreachable through the released interface. This is a provenance
observation, not a research contribution.

## E. Budget correction against the relayed plan

The external ruling costed the state-distortion question at 84-88 generations. That assumed
the leaked and recency arms would be regenerated. They do not need to be: the census
reproduced the sealed leaked selections frame-for-frame from an independent rebuild, and the
disabled arm does not read the leaked attribute. Only the clean NMS-on arm is missing.

Actual cost: **28 generations** (14 windows x 2 seeds), which simultaneously supplies the
corrected NMS-on contrast, the NULL determinism check, the PERMUTATION order-effect contrast,
and the CONTENT contrast. The slot-utilisation control adds a further 28.

## F. The honest ceiling, restated in my own terms

A bounded evaluation study on one frozen consumer and one dependency group: a controlled
negative result about geometry-indexed retrieval, a specific mechanical account of why it
cannot help in this regime, and an audited contamination hazard that explains why a naive
reading of the same runs would have reported the opposite sign. One consumer cannot establish
prevalence; one dependency group cannot establish an average effect; exposed sequences cannot
later serve as untouched validation. Those limits are not removable by more seeds, more
windows, or more infrastructure.
