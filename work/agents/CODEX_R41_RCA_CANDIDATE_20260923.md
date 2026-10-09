# R41 candidate: Revealed-Contradiction Attribution (RCA)

Date: 2026-09-23

This is a new candidate generated from the C8 slot-0 confound. It is not validated and does not
authorize implementation or GPU work. The flags remain `new_method_validated=false` and
`novelty_authorization=NONE`.

## Problem

A delayed RGB-D reveal can disagree with a hidden-surface prediction for at least three different
causes:

1. the hidden scene surface was predicted incorrectly;
2. the camera reference, translation scale, or pose is wrong;
3. the observation is transient/noisy or the surface association is wrong.

Writing every residual into a scene belief turns a conditioning or sensor error into a persistent
hallucination. The current C8 slot-0 result makes this alternative explanation measurable.

## Mechanism

RCA adds a causal attribution gate before revision. Given pre-reveal belief `B`, reveal `R`, camera
pose covariance `Σ_pose`, and a registered surface correspondence, evaluate three residual likelihoods:

```text
L_scene   = p(R | B, fixed pose)
L_gauge   = p(R | B, pose/scale perturbations drawn from Σ_pose)
L_trans   = p(R | transient/association corruption model)
```

Only the scene-attributed component can update the hidden generative belief. A gauge-attributed
component updates the camera/gauge diagnostic or is rejected; a transient-attributed component is
discarded. The event token stores the attribution, residual, and provenance. The corrected token is
queried by at least two future cameras; measured evidence remains immutable.

This is not a generic robust loss. The method claim would be a *cause-aware reveal intervention* that
prevents camera-gauge contradictions from becoming persistent scene content.

## Closest prior and risk

Robust SLAM uses switchable constraints and pose-hypothesis routing; pose-aware topological mapping
also maintains multi-hypothesis pose/map beliefs. Dynamic reconstruction decomposes observation
errors. These are direct threats. RCA survives only if its attribution is tied to a hidden-surface
generative belief and improves future camera-conditioned RGB/depth after a real delayed reveal.

## Falsifiable experiment

Build held-out episodes with three controlled perturbations before any real reveal: (a) a known surface
depth/appearance change, (b) a slot-0 reference/scale or pose perturbation, and (c) a transient outlier.
Require a pre-registered routing confusion matrix. Then run the real hidden → reveal → two future-camera
episode and compare:

- blind local revision;
- robust global update;
- append-only reveal retrieval;
- RCA-gated revision.

Measure attribution accuracy, third-camera RGB/depth error, outside-support drift, and the fraction of
gauge/transient residual written into the scene belief. The C8 RS canonicalization must be applied.

## Kill conditions

Kill RCA if a standard switchable-constraint/pose-correction baseline routes the same residuals and
matches future-camera quality; if attribution cannot separate scene and gauge perturbations; if the
candidate only improves pose metrics; if future-camera RGB/depth does not improve; or if a delayed
reveal is not required for the gain. If C8 finds no real support scarcity, close RCA with the rest of
the hidden-surface family.

## Decision

RCA is a secondary candidate worth a CPU-only routing-contract sketch because it directly uses the
measured C8 confound. It does not replace the CGLR/CRR contract yet. The primary decision remains to
first validate the support/delivery boundary and then choose between CRR and RCA by expected
information gain per GPU-hour.

