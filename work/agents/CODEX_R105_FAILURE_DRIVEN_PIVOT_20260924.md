# R105 failure-driven innovation pivot

Date: 2026-09-24 (Asia/Shanghai)  
Scope: read-only design/prior-art audit. No runner or fixture execution, no GPU/
Slurm, no protected C8/evaluation reads, and no flag or frozen-contract change.

## Decision

**No defensible new geometry-aware method remains. Recommend END-LINE for the
hidden-surface method search.** One final candidate was considered below as a
failure-driven pivot, but it is a robustness/evaluation gate with strong prior
art, not a publishable mechanism under the current evidence.

## Last candidate considered: Gauge-Separated Contradiction Router (GSCR)

GSCR would route a delayed RGB-D residual into three typed causes before any
world-model write:

1. scene-surface residual in canonical world coordinates;
2. camera/gauge residual (pose, ray-reference, or metric-scale error); or
3. transient/sensor residual (motion, depth failure, or non-repeatable colour).

Only a scene residual that survives bidirectional pose/scale identity checks and
predicts an independently held-out camera could update the predictive hidden
branch. Gauge evidence would update a convention/gauge state; transient
evidence would be held as uncertainty. This directly targets the unresolved
C8 H1/H2 failure: the evaluator joins raw-frame points to maps rendered with a
y/z-flipped pose, while the CUT3R input convention remains open
(`work/agents/CODEX_R46_POSE_CONVENTION_DCR_AUDIT_20260924.md:7-10,37-54`).

## Why GSCR is rejected as innovation

The mechanism is already described as RCA in the prior innovation record:
typed scene/camera/transient hypotheses, likelihood routing, and future-view
evaluation (`work/agents/CODEX_R39_REDTEAM_PIVOT_20260923.md:26-53`). That
record names robust SLAM/data association, 3D-Belief, and INGRID as the closest
prior families and calls the gap only a hypothesis. A generic robust
pose/data-association filter can implement the same gate without a new
camera-conditioned world-model state. SceneSense/SC-Explorer already reconcile
measured and predicted geometry; selective exposed-surface updates are also
occupied. Thus GSCR changes attribution and validation hygiene, but does not
establish a distinct generator information path.

The C8 prerequisite is also absent. R45 closes RCA and BRD on this panel as
`CLOSED_UNSUPPORTED_SUPPORT` because bank/context support is high and low `J`
is pose-uninterpretable; it says a CPU routing exercise would be disconnected
from the observed VMem failure
(`work/agents/CODEX_R45_SUPPORT_IMPLICATIONS_20260924.md:8-23,42-56`). R46
keeps H2 unresolved and permits DCR only as a convention-controlled benchmark
(`work/agents/CODEX_R46_POSE_CONVENTION_DCR_AUDIT_20260924.md:50-66,79-103`).

## Falsifier

On a source-pinned CPU fixture with known plane/cube geometry, explicit poses,
`T_cv` and `T_cv F`, and labelled scene/pose/transient/depth perturbations,
GSCR is falsified if a matched generic robust SLAM/data-association gate has no
higher false-scene-write rate and no worse held-out third-camera RGB/depth
error. It is also falsified immediately if it cannot separate the pose/gauge
perturbation from a true scene residual after H2 identity is fixed. Routing
accuracy alone is insufficient; equal future-view performance closes the
mechanism.

## Minimum synthetic prerequisite

Before any method or GPU claim, an owner-reviewed CPU packet would need:

* an independent metric plane/cube fixture with three or more cameras, sealed
  target views, known RGB-D units, and both pose conventions;
* four labelled perturbation arms (true scene change, pose/gauge error,
  transient object, depth corruption) generated without target RGB;
* an independent H2 source/boundary artifact proving which frame reaches the
  CUT3R pointmap boundary, then frozen scale/intrinsics and camera-keyed
  visibility hashes;
* a confusion matrix, false-scene-write denominator, and two future-camera
  RGB/depth scores against append-only and a generic robust-gate control;
* the R62 owner gate and supported CPU runner. Missing/ambiguous H2 must stop
  before any score as `H2_UNIDENTIFIABLE`.

This packet is currently absent; R100 still reports `NO_COMMAND_AVAILABLE` and
no owner/H2/fixture/runner artifacts.

## GPU cost and kill condition

The minimum routing/identity check is CPU-only (zero GPU cost). A later frozen
denoiser or H800 pilot would be justified only after the packet passes, C8
support scarcity is independently established, and owner review authorizes it;
none is authorized now.

Kill GSCR and end the method search if H2 remains unresolved, the C8 support
precondition remains absent, a generic robust gate matches it, scene writes are
not lower than append-only, gains occur only on the reveal camera, target data
leaks into routing/masks, or future RGB/depth is unchanged. These are the
existing RCA/DCR stop conditions, not new evidence
(`work/agents/CODEX_R39_REDTEAM_PIVOT_20260923.md:74-79`; `work/agents/CODEX_R45_SUPPORT_IMPLICATIONS_20260924.md:86-100`).

## Final recommendation

Keep DCR as a conditional benchmark/evaluation setting only. Report the C8
pose/convention and delivery/indexing limitation, retain
`new_method_validated=false` and `novelty_authorization=NONE`, and stop seeking
another hidden-surface mechanism unless the owner supplies the complete H2 and
synthetic packet. No GPU experiment should be scheduled from this pivot.

