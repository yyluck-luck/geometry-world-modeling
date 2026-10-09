# R43 innovation adjudication: RCA versus BRD versus CGLR

Date: 2026-09-23  
Scope: bounded CPU-only decision cycle; no GPU, Slurm job, weight update, or validation-flag change.  
Status: `new_method_validated=false`; `novelty_authorization=NONE`.

## Decision

**RCA (Revealed-Contradiction Attribution) is the strongest surviving mechanism candidate.** Its
narrow information-pathway claim is that a delayed registered RGB-D contradiction is first routed as
scene-surface, camera/gauge, or transient/sensor evidence; only the scene branch may write to a hidden
generative surface state, and the effect must transfer to future camera-conditioned RGB/depth views.
This is a more specific test than appending the reveal or applying a generic belief update.

**BRD (Bidirectional Reveal Deletion) is a secondary candidate.** Its signed positive/negative
reveal transition is useful, but free-space, visibility-aware occupancy, and causal evidence fusion
are already strongly occupied by GEM-Occ, SceneSense, and related mapping/completion systems. BRD
therefore survives only as a delayed negative-reveal test on a predictive generative hidden branch.

**CGLR/CRR is demoted to a causal evaluation operator and control.** Its conservation and paired
same-noise tests remain valuable, but its components are individually occupied: residual transfer
(CVPR 2022 BVS), correspondence-guided editing (Edicho), counterfactual masking (CWM), persistent
3D state (PERSIST/3D-Belief), selective geometry updates (INGRID), and geometry-guided exposed-region
completion/revisit retrieval (World in World). The exact conjunction is still a hypothesis, not a
novelty claim.

## Adjudication against the latest reports and prior art

| Candidate | Information path that could remain distinctive | Main prior-art threat | R43 ruling |
|---|---|---|---|
| CGLR/CRR | reveal residual -> local hidden-state revision -> third-camera generation, with exact outside-support conservation | BVS, CWM, Edicho, PERSIST, INGRID, World in World, generic belief update | Keep as paired causal contract/control; do not lead with it |
| RCA | delayed contradiction -> typed scene/gauge/transient attribution -> scene-only generative write -> future RGB/depth | switchable-constraint robust SLAM, pose-aware mapping, 3D-Belief | **Primary bounded mechanism**; survives only with future-view and false-write evidence |
| BRD | positive/negative reveal -> signed hidden-surface reinforce/delete -> future RGB/depth | GEM-Occ, SceneSense, ORCA, free-space/occupancy completion | Secondary; test after RCA or in the same CPU dataset |

The R38 hostile review already found broad delayed posterior correction and generic persistent state
occupied. R39 narrowed the search to RCA/BRD after residual/counterfactual checks. R40 explicitly
killed residual transport as a novelty axis, and R42 ranked RCA above BRD above CRR. R43 preserves
that ranking while making the causal boundary explicit: RCA must not be described as outlier
rejection, occupancy fusion, generic memory, or pose estimation.

## One falsifiable CPU-only contract for RCA

Build a sealed set of **at least eight held-out static RGB-D episodes**. For each episode, create four
labelled delayed contradictions from the same pre-reveal state: (a) true hidden-surface reveal, (b)
C8 rolling-shutter/reference/metric-gauge perturbation, (c) transient object or association change,
and (d) depth corruption. Keep measured evidence `E` immutable and keep hidden hypotheses `B`
provenance-tagged.

On CPU, independently register geometry and poses, compute residual likelihoods under the three RCA
types, and output a route plus confidence for every event. Pre-register the following acceptance
rule before looking at results (thresholds are a feasibility contract, not measured evidence):

* true-reveal scene-route recall `>= 0.75`;
* false scene-write rate on gauge/transient/corruption controls `<= 0.10`;
* for a scene route, only the independently computed reveal support may change; outside-support
  state difference `<= 1e-6` (exact identity where the representation permits it);
* no-reveal and gauge/transient routes leave the hidden scene state unchanged.

Compare against append-only context, a generic robust/switchable-constraint filter, an untyped global
update, and shuffled support. Use a deterministic CPU geometry renderer or proxy for a third-camera
check: scene-routed events must reduce held-out geometry error relative to append-only on at least
6/8 episodes, while non-scene routes must not change the predicted support. This contract tests
information routing before any denoiser, adapter, or GPU run.

## Precise CGLR kill condition

Kill CGLR/CRR as a method candidate if the preregistered CPU proxy fails **any** of these conditions:

1. third-camera geometry gain over append-only occurs on fewer than 6 of 8 episodes;
2. outside-support state change exceeds `1e-6` in any episode;
3. false scene-write rate is above `0.10` on gauge/transient/corruption controls in the RCA route;
4. the apparent gain disappears after C8 rolling-shutter/reference canonicalization; or
5. a focused prior-art check finds the exact residual-gated local revision plus conservation and
   delayed third-camera transfer already published.

The first three are CPU-testable falsifiers; the fourth blocks a slot-0/gauge confound; the fifth
closes the novelty claim even if the operator works. A routing score alone is insufficient: if RCA
cannot pass this contract, CGLR is closed rather than promoted to a GPU pilot.

## Updated shortlist

1. **RCA — narrow generative contradiction attribution** (bounded CPU feasibility).
2. **BRD — signed delayed negative-reveal deletion** (secondary, high occupancy prior-art risk).
3. **CGLR/CRR — paired causal evaluation operator/control only**.
4. **DCR — Delayed Contradictory Reveal benchmark** as the fallback contribution if both mechanisms
   collapse into robust belief/occupancy prior art.
5. Retire RRST/SLQT/SLRP as primary novelty axes for this cycle; their residual-transfer,
   multi-hypothesis, or generic belief components are already too close to prior work.

No method is authorized or validated by this memo. The next action is the CPU RCA routing contract;
if it fails, close the hidden-surface method search and move to the DCR evaluation setting or a
negative infrastructure result.

## Exact prior-art links used

- [Boosting View Synthesis with Residual Transfer (CVPR 2022)](https://openaccess.thecvf.com/content/CVPR2022/papers/Rong_Boosting_View_Synthesis_With_Residual_Transfer_CVPR2022_paper.pdf)
- [CWM](https://arxiv.org/abs/2306.01828) and [Edicho (ICCV 2025)](https://openaccess.thecvf.com/content/ICCV2025/papers/Bai_Edicho_Consistent_Image_Editing_in_the_Wild_ICCV2025_paper.pdf)
- [3D-Belief](https://arxiv.org/abs/2605.11367), [WRBench](https://arxiv.org/abs/2606.20545), and [World in World](https://huggingface.co/papers/2609.11548)
- [GEM-Occ](https://arxiv.org/abs/2607.05543), [SceneSense](https://arpg.colorado.edu/scenesense/), and [ORCA](https://arxiv.org/abs/2609.17450)
- [Switchable Constraints for Robust SLAM](https://nikosuenderhauf.github.io/assets/papers/IROS12-switchableConstraints.pdf)

