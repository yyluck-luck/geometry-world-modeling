# R49 identifiability review of Reveal-Intervention / CGLR

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only hostile review using R38 prior-art memos and the R47/R48 H2 provenance constraints. No replay, real-data rescoring, GPU/Slurm submission, receipt mutation, or validation-flag change.

## Decision

**REVISE as a causal evaluation operator; reject the current standalone-method novelty claim.** CGLR is not identifiable as a new method from the present wording. Its components are separately occupied, and H2 is still unresolved: without a producer pointmap-frame declaration and CPU-checkable CUT3R boundary artifact, a delayed residual can be a camera/gauge/scale error rather than a scene contradiction. A narrow event contract can remain useful if it is explicitly an evaluation operator inside a DCR setting and passes the synthetic discriminating test below. Keep new_method_validated=false and novelty_authorization=NONE.

## 1. Closest prior mechanisms

The following evidence is already recorded in the R38 memos and must be treated as prior-art coverage, not as proposed contributions:

| Prior mechanism | Already covers | CGLR consequence |
|---|---|---|
| 3D-Belief | Explicit 3D beliefs, multi-hypothesis unseen-region imagination, and sequential online updates | “Update a hidden 3D belief after a reveal” is generic. |
| SceneSense / SC-Explorer | Predicted-versus-measured scene maps, occupancy completion, and incremental fusion | Measured evidence plus predicted completion is not a delta. |
| GEM-Occ | Occupied/free-space evidence and uncertainty-aware causal occupancy memory | Positive/negative reveal or visibility-aware occupancy is occupied. |
| WRBench | Camera-away, hidden-event, and return-state consistency as a benchmark | Hide/reveal/reappearance is a problem setting, not a method by itself. |
| GeNVS, 3DiM, GEN3C, Geometry-as-context, WorldStereo | Geometry-conditioned generative novel-view/video synthesis and cross-view feedback | Geometry conditioning, camera control, and cross-view correspondence are substrates. |
| Boosting View Synthesis with Residual Transfer | Residual colors transferred through 3D correspondence, visibility, and angular weighting | Residual transport/warping is explicitly occupied. |
| Edicho | Fixed-seed correspondence-guided local diffusion editing | Same-noise local intervention and correspondence guidance are occupied. |
| Counterfactual World Modeling | Masked counterfactual branches and pre/post comparisons | A counterfactual branch alone is not new. |
| Fixed-lag/OOSM smoothing | Delayed measurements and state correction | Delayed observation correction is generic unless the state/write semantics are distinctive. |

Anchors: R38 hostile red-team lines 16-29, 32-59, 61-99; R38 mechanism candidates lines 55-67; R38 search lines 38-45, 47-62.

## 2. Precise residual that may still be distinguishable

The only potentially distinct information pathway is a typed, provenance-gated commit:

1. E is immutable measured RGB-D evidence; predictions never enter E.
2. B_pre is a materialized hidden-surface hypothesis with a declared frame, support, uncertainty, and provenance predicted.
3. A delayed reveal R is registered in the same canonical 3D frame and must be contradictory to B_pre under calibrated sensor noise.
4. The update gate is the conjunction of residual threshold, 3D support intersection, and predictive provenance. Only those slots are changed.
5. B_post is byte-identical to B_pre outside the registered support; a no-reveal branch is byte-identical everywhere.
6. The updated state is rendered from a third camera whose queried surface is not the reveal camera's image plane.

This conjunction is potentially a causal measurement operator. It is not enough to call it belief update, residual transport, masked editing, local diffusion, or counterfactual generation; each of those descriptions has close prior art. The claimed distinction would have to be the auditable event-to-write transition plus the third-camera consequence under exact conservation and provenance rules.

## 3. Strongest confounds

1. **H2 gauge/scale confound.** R47/R48 show that VMem renders use T_cv F, while the CUT3R pointmap frame is not yet proven. A residual may be pose, axis, focal, or metric-scale mismatch. No CGLR scene write is interpretable until H2 is PASS.
2. **Append-only extra evidence.** Adding the reveal frame and regenerating can improve the third view without any belief revision. Match reveal pixels, camera count, budget, and consumer path.
3. **Generic completion.** A capacity-matched local masked adapter can produce the same region-local change and conservation rule. If it ties CGLR, provenance-gated residual commit is not identifiable.
4. **Residual-transfer prior.** A 3D residual correspondence path can explain the third-camera gain without a new event mechanism.
5. **Local diffusion prior.** Fixed-seed correspondence-guided editing can explain locality and paired changes.
6. **Counterfactual prior.** CWM-style masking and pre/post branches can explain a reveal/no-reveal comparison.
7. **Occupancy/belief prior.** 3D-Belief, SceneSense, SC-Explorer, and GEM-Occ can explain sequential measured/predicted fusion.
8. **Camera overlap.** If the third camera sees the reveal pixels, the result is a reveal-camera copy rather than counterfactual transport. The test camera must have disjoint queried rays or a declared 3D overlap mask.
9. **Stochastic drift.** No-reveal changes may come from mutable state or diffusion noise. The no-reveal branch needs exact byte identity or a pre-measured replay envelope.
10. **Leakage.** Target RGB/depth, future poses, or oracle hidden masks can leak into the gate, residual threshold, support, or third-camera query.
11. **Support premise.** C8 B/C are high and old J is uninterpretable. The current panel does not establish hidden-surface scarcity needed to motivate a corrective method.

## 4. One CPU/synthetic discriminating test

Build a deterministic static scene with three 3D patches:

* patch A: first visible only at the delayed reveal camera;
* patch B: unrelated visible geometry used for a negative reveal;
* patch C: queried by a third camera and disjoint from the reveal image plane.

Freeze an explicit pointmap frame label (optical_cv or vmem_gl) and verify R47/R48 H2 identities before running the operator. Use a known K, metric depth, camera poses, and an oracle 3D correspondence. The fixture is a contract test, not model validation.

Run the same initial state and reveal residual under six abstract CPU arms:

1. typed CGLR commit;
2. append-only reveal (new evidence, no B rewrite);
3. capacity-matched generic global update;
4. local mask-only update with the same support but no residual/provenance gate;
5. residual transport without typed provenance/conservation;
6. no-reveal control.

Add a negative reveal on patch B and a shuffled-correspondence placebo. Pre-register these outputs:

* exact hash equality of E before and after, except the append-only reveal record;
* exact outside-support hash of B_post versus B_pre;
* no-reveal hash equality everywhere;
* local write precision/recall against the oracle patch A;
* third-camera depth/appearance surrogate error on patch C;
* reveal-camera and unrelated-reveal effects separately;
* all denominators and frame/scale metadata.

The candidate is discriminated only if CGLR changes patch C after the matched contradictory reveal, does not change C for no-reveal or unrelated patch B, preserves outside-support state exactly, and beats both append-only and mask-only controls under the same information/budget. If mask-only local update ties CGLR, the residual/provenance mechanism is not identifiable. If the pointmap frame cannot be declared and checked, return H2_UNIDENTIFIABLE before scoring any arm.

This test can establish an information-pathway contract. It cannot establish literature novelty or end-to-end generative benefit because no learned world-model consumer is exercised.

## 5. Required wording and kill conditions

Use only: “a candidate reveal-event causal operator with typed evidence, residual gating, and conservation.” Do not claim a new belief state, first delayed correction, residual transport, local diffusion, unseen completion, causal occupancy, or general camera-away persistence.

Kill or downgrade the mechanism if:

* H2 provenance remains unresolved;
* append-only, generic completion, residual transport, or mask-only local update matches the third-camera effect;
* outside-support state is not exact or no-reveal is not identical;
* the effect occurs only at the reveal camera;
* source/gauge/scale controls explain the residual;
* the candidate needs target RGB/depth/future camera data to select its gate;
* the C8 exposed-development panel is used as independent generalization evidence.

## Final ranking

CGLR should be retained as a DCR evaluation operator/control, with a possible future method only after an independent H2 provenance artifact and the synthetic discriminating test. The standalone method direction is rejected for now; the defensible research contribution remains a convention-controlled evaluation setting rather than an architecture novelty.

