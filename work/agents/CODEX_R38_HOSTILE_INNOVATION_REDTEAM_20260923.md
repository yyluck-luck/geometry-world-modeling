# R38 hostile innovation red-team: delayed-observation correction (2026-09-23)

## Scope and verdict

This memo stress-tests the current candidate:

> A generative 3D world model predicts a hidden surface, receives a later contradictory reveal,
> applies a local posterior correction to the same belief, and improves a later reappearance while
> preserving an untouched region.

**Verdict: the broad claim is occupied.** The only defensible residual is a much narrower mechanism:
**surface-local, residual-gated, provenance-preserving belief revision with a conservation guarantee**
inside a camera-conditioned generative novel-view model. This is a candidate only; there is no
novelty authorization or validated method.

## Strongest prior-art counterexamples

| Threat | What it already covers | Why it attacks our wording | Required narrowing |
|---|---|---|---|
| [3D-Belief (2026)](https://arxiv.org/abs/2605.11367) | Explicit 3D beliefs from partial observations; multi-hypothesis sampling; sequential belief updating; unseen-region imagination; online updates. The project page says observed Gaussians absorb new evidence while imagined regions are resampled consistently. | “Maintain/update a belief about hidden 3D space after later observations” is already the paper's central framing. | Do not claim belief maintenance, unseen completion, online update, or uncertainty-aware imagination. Require a **contradictory reveal residual**, a **same pre-reveal hypothesis**, and a **local untouched-region conservation test**. |
| [Model-Based RL under Random Observation Delays (2025/2026)](https://arxiv.org/abs/2509.20869) | Out-of-sequence observations in a POMDP; a time-stamped buffer; sequential latent belief updates when delayed observations arrive; Dreamer integration. | “Delayed observation causes posterior correction” is generic filtering/world-model machinery even when the observation arrives after later steps. | Separate camera-scene surface revision from delay compensation. The contribution must be spatially localized and evaluated in generated RGB/depth reappearance, not policy return or latent-state filtering. |
| [SC-Explorer (2022)](https://arxiv.org/abs/2208.08307) | Incremental scene completion, predicted-vs-measured hierarchical maps, temporal fusion of completions, and explicit handling of completion uncertainty for later planning. | Predicting hidden geometry and fusing it with later measured geometry is already an incremental completion pattern. | Do not claim predictive geometry plus a measured/evidence split. Require that a later *contradiction* changes only the implicated belief slots and changes the generator's future view. |
| [Generative NVS with 3D-aware diffusion (GeNVS)](https://openaccess.thecvf.com/content/ICCV2023/papers/Chan_Generative_Novel_View_Synthesis_with_3D-Aware_Diffusion_Models_ICCV2023_paper.pdf) and [3DiM](https://arxiv.org/abs/2210.04628) | Geometry-aware 3D feature fields, ambiguous hidden-region sampling, and consistent multi-view generation. | “Hidden geometry conditions a diffusion renderer” is a standard architecture move. | Geometry conditioning is only an implementation substrate; it cannot be the contribution. |
| [Neural Rays](https://arxiv.org/abs/2107.13421) and [SC-Explorer](https://arxiv.org/abs/2208.08307) | Explicit visibility/occlusion reasoning and local map/completion fusion. | A visibility mask or support mask can be read as the same idea under a new name. | A support mask must be tied to a reveal residual and a no-write provenance rule; a mask-only gain is an infrastructure result. |
| [Boosting View Synthesis with Residual Transfer (CVPR 2022)](https://openaccess.thecvf.com/content/CVPR2022/papers/Rong_Boosting_View_Synthesis_With_Residual_Transfer_CVPR_2022_paper.pdf) | Computes reconstruction residual colors at observed views and transfers/blends them to novel views through 3D point correspondences, visibility and angular weighting. | “Compute a view residual and transport it through 3D correspondence to improve a novel view” is already a published rendering operation. | RRST/CGLR cannot claim residual transport alone. It must add a **delayed contradictory reveal**, a pre-reveal predictive hypothesis with provenance, an intervention/no-reveal counterfactual, and a strict support-local conservation rule. |
| [Edicho: Consistent Image Editing in the Wild](https://ant-research.github.io/edicho/) | Fixed-seed, correspondence-guided diffusion editing with local and global modes. | Same-noise paired generation and correspondence-guided local intervention are not novel by themselves. | The causal pair must be tied to a delayed RGB-D reveal and a future third-camera improvement; report no-reveal and unrelated-reveal counterfactuals. |
| [Counterfactual World Modeling](https://arxiv.org/abs/2306.01828) | Structured masking plus counterfactual input/output comparisons expose occlusion, depth and other visual properties; counterfactual prediction is a general interface. | “Use a counterfactual branch and compare pre/post predictions” is a known world-model pattern. | The counterfactual must be an actual delayed RGB-D intervention on a registered hidden surface, with a causal third-camera generation target and conservation outside the reveal support. |
| Fixed-lag/OOSM smoothing, e.g. [Ranganathan et al.](https://www.cs.cmu.edu/~kaess/pub/Ranganathan07iros.pdf) | Delayed measurements inserted at their acquisition time and corrections propagated through a retained state window. | “Retrodictive smoothing” by itself is not new. | State explicitly that camera pose/trajectory smoothing is excluded; the state being revised is a predictive surface hypothesis consumed by a generative renderer. |

## What remains plausibly new (and what does not)

### Surviving mechanism (candidate, not claim)

Use a two-track state with explicit provenance:

* `E`: immutable measured evidence (RGB-D and cameras), never overwritten by predictions;
* `B`: a queryable distribution of hidden-surface hypotheses, with per-surface support and uncertainty;
* `R`: a reveal event registered to the same surface/ray coordinates.

At reveal time compute a calibrated residual between `R` and the pre-reveal rendering of `B`. Apply a
**minimal-change, residual-gated update** only to the hypothesis slots whose projected support overlaps
the revealed surface and whose residual exceeds the pre-registered uncertainty threshold. All other
slots are copied exactly. The updated `B` is rendered into a held-out reappearance query and the
same earlier query can be re-rendered to test retrodictive correction.

The differentiator is the conjunction, not any single ingredient:

1. A hidden prediction is materialized before reveal and carries provenance.
2. A contradictory, registered RGB-D reveal selects the update support.
3. The update is local and conservative by construction (`B' = B` outside the reveal support).
4. The corrected belief is consumed by a generative RGB/depth view renderer.
5. A no-reveal counterfactual must leave the belief unchanged.

Residual transport itself is explicitly occupied by *Boosting View Synthesis with Residual Transfer*;
the only possible delta is the causal **event** and the constrained belief revision around that event,
not the residual warp or the 3D correspondence.

The closest papers above provide subsets, but the subset intersection has not been verified as an
existing method. This statement is **an unverified search result, not a novelty proof**.

### Claims to reject

Do not claim any of the following:

* posterior update, belief state, scene memory, unseen completion, or multi-hypothesis prediction;
* occlusion persistence, re-entry continuity, or out-of-sight evolution;
* delayed observation handling, fixed-lag smoothing, or out-of-sequence measurement correction;
* a depth/geometry adapter, visibility/support mask, extra conditioning channel, or retrieval change;
* “first to update hidden surfaces after a reveal.”

## Minimal method specification

Let `B_t = {(h_i, u_i, q_i)}` be hidden-surface hypotheses, with geometry/appearance `h_i`, uncertainty
`u_i`, and provenance/support `q_i`. Let `\mathcal{M}_r` be the registered reveal mask and
`e(x) = ||z_r(x) - render(B_t)(x)||` the RGB-D residual. Define

```text
g(x) = 1[e(x) > tau(u(x), sensor_noise)] * 1[x in M_r] * 1[q(x) == predictive]
B_{t+1}(x) = Update(B_t(x), z_r(x)) if g(x)=1
             B_t(x)                         otherwise
```

The update can be particle reweight/resample or a learned residual-to-latent transport; the exact
parameterization is secondary. The non-negotiable property is the **conservation rule outside the
registered reveal support**. A global latent update fails the proposed method definition.

If a trainable method is eventually justified, the method-level signal should be a paired objective,
not an extra depth channel:

```text
L = L_reveal
  + lambda_cons ||(B_post - B_pre) * (1 - M_reveal)||
  + lambda_cf   ||B_post(no_reveal) - B_pre||
  + lambda_mono monotonicity_penalty(residual, correction)
```

The conservation and no-reveal terms are the part that could distinguish this route from ordinary
completion. They still require a paper-level prior-art check; CWM and local diffusion editing already
occupy counterfactual and masked-generation components separately.

## Minimum evidence contract (before any novelty wording)

Use independent held-out scenes and paired three-stage episodes: hidden context → delayed RGB-D reveal
with nonzero pre-reveal residual → future reappearance. Report:

1. Pre-reveal hidden-surface RGB/depth error and calibration of `u`.
2. Post-reveal error reduction on the revealed region.
3. Difference-in-differences against an untouched region and a no-reveal counterfactual.
4. Future reappearance RGB and depth metrics from the corrected generator.
5. Correction locality: fraction of update mass inside/outside `M_r`.
6. Provenance ablation: predicted geometry is forbidden from entering `E`.
7. Matched controls:
   * append-only context/retrieval (new frame added, no belief rewrite);
   * capacity-matched generic completion/depth adapter;
   * global online belief update (3D-Belief-style control);
   * reveal mask shuffled or residual threshold removed.

### Suggested primary estimand

```text
Delta = [Err_pre(reveal) - Err_post(reveal)]
        - [Err_pre(untouched) - Err_post(untouched)]
```

Require `Delta > 0` with a pre-registered confidence interval, positive RGB and depth direction, and
no material untouched-region drift. Also require monotone improvement as the reveal residual increases
within the calibrated range. A single PSNR gain is insufficient.

### Kill conditions

Kill the candidate if any of the following holds:

* append-only retrieval or generic completion matches the gain;
* a global update explains the gain as well as the local rule;
* the update changes unsupported or untouched regions materially;
* the result vanishes after slot-0 reference/scale canonicalization;
* the gain appears only in an auxiliary depth head, not generated RGB/depth views;
* an existing paper is found with the same residual-gated local revision and conservation test;
* C8 attributes the apparent failure to delivery/indexing rather than missing support.

## Decision

The current broad Candidate 1 should be renamed internally to **CGLR: conservative reveal-event
belief revision** only as a working label. It should not be presented as a novel method until the
minimum contract is passed. If the first pilot cannot show a causal local correction over all matched
controls, close this route and report the infrastructure or evaluation failure.

## Source notes

The literature search was run on 2026-09-23 against primary/arXiv/CVF pages. Search snippets and
abstracts establish occupancy threats; they do not establish that the exact CGLR subset is absent.
The project remains `new_method_validated=false` and `novelty_authorization=NONE`.
