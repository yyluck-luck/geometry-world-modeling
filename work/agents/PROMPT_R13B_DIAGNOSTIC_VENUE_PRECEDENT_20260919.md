# Round 13-B — What is the publication precedent for a diagnostic/forensic contribution?

This is a **precedent investigation**, not a novelty review of my project. Do not propose
methods, do not issue a funding verdict, do not tell me whether to continue.

## Why I am asking

Two prior review rounds concluded END-LINE: no method contribution is available under this
project's constraints, and no relaxation of the technical constraints (no-training,
no-fine-tuning, no-new-weights, no-upstream-modification, one-frozen-consumer) reaches an
unoccupied, non-degenerate direction that is also executable in the remaining term.

The binding constraint may therefore not be technical at all. It may be the requirement that
**the contribution be a method**. Before the owner decides whether to relax that requirement, I
need to know what such a contribution would actually have to look like to be publishable — as a
matter of observed precedent, not opinion.

## What this project actually has (take as given; verify in-repo if you wish)

- A located state-dependency defect in a published, publicly released camera-conditioned video
  memory system: an `initial_threshold` value written by one branch, not cleared by `reset()`,
  and inherited by later calls.
- An **order-invariance qualification gate**: 11/11 pass including non-vacuity checks.
- A **three-regime census** classifying every window *before any score existed*:
  NULL 2 / PERMUTATION 4 / CONTENT 8, with slot-0 invariant 14/14.
- A **byte-identity gate**: the NULL stratum produced byte-identical outputs, sha256-verified 4/4,
  which is what licensed reuse of sealed outputs instead of regeneration.
- Effect sizes on a 14-window × 2-seed panel with a frozen generator:
  `nms_on_clean − nms_on(leaked) = +0.245 dB`, stratified NULL `+0.000` / PERM `−0.015` /
  CONTENT `+0.436`, reconciling exactly to the weighted mean.
- A **source-level confound**: the retrieval query and the camera normalization are driven by the
  same `target_c2ws`, so any query-side intervention has two confounded causal paths.
- A **pre-declared repair that failed and was discarded**: threshold `+0.20 dB` declared in
  advance, measured `−0.016 dB` over 8 of 10 affected windows, discarded under the spec.
- Honest limitations: 14 exposed development windows, one dependency group, one frozen consumer,
  RGB PSNR, **not held-out**, SD across windows ≈ 5× the mean.

## Questions

### Q1 — Find the precedent, with citations
Identify published papers whose primary contribution is diagnostic, forensic, or analytical work
on an existing released system or an existing evaluation protocol — **not** a new method. For
each: arXiv ID, exact title, venue and year if determinable, and one sentence on what form the
contribution took (bug identification + effect quantification / protocol flaw / leakage audit /
reproduction failure / hidden-state dependency / benchmark invalidation).

Search across areas, not just video generation — the relevant precedent may be in RL
reproducibility, retrieval/RAG evaluation, dataset contamination, metric critiques, or ML
reproducibility studies.

### Q2 — What distinguishes the ones that got in?
From the papers you found, extract the **observable properties** that separate accepted
diagnostic work from a technical report nobody published. Candidates to test against the
evidence: scale of the affected system's usage; whether the defect changes published conclusions;
whether the paper supplies a general lesson beyond one codebase; whether it provides a test or
protocol others can adopt; sample size and held-out status. Say which of these actually
discriminate in the papers you found, and which do not.

### Q3 — The honest gap analysis
Against those properties, assess what this project **has** and what it **lacks**. Be specific
about the lacks. In particular address: a panel of 14 exposed development windows; a single
consumer; RGB PSNR only; effect sizes under 0.5 dB with SD ≈ 5× the mean; no held-out set.
State plainly whether the existing material clears the bar you derived in Q2, falls short, or
falls short but is closable — and if closable, what specifically would have to be added.

### Q4 — The venue reality
What venues actually publish this form? Main conference tracks, workshops, journals, or
registered-report/reproducibility tracks. Be concrete and current. If the honest answer is that
this form usually lands at workshops rather than main tracks, say that.

### Q5 — The negative answer, if that is the answer
If your finding is that this material cannot reach a publishable diagnostic contribution even
with the constraint relaxed, say that **first and plainly**. I prefer a correct negative to an
encouraging one. The owner is deciding whether to spend remaining term time on this.

## Output
Write to exactly one new file: `work/agents/CODEX_R13B_VENUE_PRECEDENT_20260919.md`.
Do not modify any existing file. Do not run GPU jobs, training, or generation.
Every paper: arXiv ID and exact title — I check every one. Mark anything you could not verify
as UNVERIFIED rather than asserting it.
