# R42 innovation decision: pivot from CRR to RCA/BRD

Date: 2026-09-23

This decision follows the R40 hostile update and R41 mechanism search. It is a candidate ranking, not
a novelty claim or authorization. The project remains `new_method_validated=false` and
`novelty_authorization=NONE`.

## Why CRR is no longer the main novelty axis

Residual transfer, correspondence-guided editing, fixed-seed local diffusion, counterfactual masking,
selective occlusion update, persistent 3D state, and generic belief revision all have close prior art.
Therefore CRR is retained as an **evaluation operator and control**, not the primary contribution.

## Primary candidate: RCA — Revealed-Contradiction Attribution

When a delayed RGB-D reveal contradicts a hidden prediction, route the residual among:

1. scene-surface/appearance mismatch;
2. camera gauge, pose, or metric-scale mismatch;
3. transient, sensor, or association corruption.

Only the scene branch can write to the hidden generative belief. The gauge branch updates a diagnostic
state or rejects the event; the transient branch remains uncertainty. The corrected scene branch must
improve at least two future camera-conditioned RGB/depth queries. This candidate directly uses the
measured C8 slot-0 confound, instead of treating every residual as scene evidence.

Strongest threats are robust SLAM switchable constraints and pose-aware mapping. RCA survives only if
its typed attribution lowers false scene writes and improves future generated views beyond those
controls.

## Secondary candidate: BRD — Bidirectional Reveal Deletion

Represent predicted-only hidden surfaces with signed hypotheses. A positive reveal reinforces or
corrects a matched hypothesis; a negative reveal (free space or a different measured surface) deletes
or downweights a ghost hypothesis. Measured evidence remains immutable. The method target is the
reduction of hallucinated hidden surfaces in future generated views, not generic free-space mapping.

SceneSense, GEM-Occ, ORCA, and occupancy completion are strong threats. BRD survives only if delayed
negative evidence removes a ghost from a generative hidden branch and transfers to future cameras
without erasing valid hidden alternatives.

## Bounded zero-GPU contracts

Before any model execution, build two CPU contracts:

- **RCA routing benchmark:** eight held-out episodes with labels for real surface reveal, pose/gauge
  perturbation, transient object, and depth corruption; report a routing confusion matrix and false
  scene-write rate.
- **BRD positive/negative reveal contract:** eight occluder episodes with matched positive and
  negative reveals; report ghost-surface precision/recall, future-camera depth/RGB, and untouched
  drift.

Both contracts require independent geometry masks, immutable evidence, C8 RS canonicalization, and
append-only/generic/global controls. They do not authorize Slurm, diffusion, adapter training, or new
weights.

## Ranking

1. **RCA:** highest information gain because it tests whether the apparent failure is scene evidence
   or the already-measured camera/gauge confound.
2. **BRD:** potentially cleaner geometric mechanism, but free-space/occupancy prior-art risk is high.
3. **CRR:** retain as a paired causal evaluation operator; do not present as a standalone novelty.

## Fallback setting: DCR

If RCA and BRD collapse into robust belief/occupancy prior art, the defensible contribution becomes a
new-problem/evaluation setting rather than an architecture: **DCR (Delayed Contradictory Reveal)**
episodes with **static geometry**, hidden prediction → delayed positive or negative RGB-D reveal →
two future-camera queries. The benchmark would freeze support masks, evidence provenance,
anti-leakage checks, proper scoring, and positive/negative reveal controls. It must explicitly differ
from WRBench/MemoBench dynamic event persistence and 3D-Belief object permanence. A method would be
optional and reported only as a capacity-matched baseline. This fallback avoids overclaiming an
architecture novelty while retaining the measured C8 failure mode.

If RCA cannot separate known perturbations or if BRD reduces to occupancy completion, close the hidden-
surface method search for this pipeline and report the infrastructure/evaluation explanation.
