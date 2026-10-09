# R38 method mechanism candidates: information-pathway search

Date: 2026-09-23

This memo proposes three bounded mechanisms for the camera-conditioned generative 3D world
model. None is a validated method. The project flags remain
`new_method_validated=false` and `novelty_authorization=NONE`.

## What is already occupied

The following are not sufficient contributions by themselves: a persistent 3D map, an unseen
region completion head, a confidence or uncertainty map, generic sequential belief updating,
occlusion consistency, a depth/pointmap adapter, a persistent latent 3D scene state, and a
frame-selection or retrieval policy.
SceneSense already performs probabilistic 3D occupancy completion while preserving observed
space ([project page](https://arpg.colorado.edu/scenesense/)); VisHall3D explicitly separates
visible-frontier reconstruction from invisible-region hallucination
([paper](https://arxiv.org/abs/2507.19188)); 3D-Belief claims explicit 3D beliefs and online
updates ([paper](https://arxiv.org/abs/2605.11367)); and camera-conditioned generative NVS with
geometry conditioning is established by GEN3C, MVGD, and GeNVS
([GEN3C](https://openaccess.thecvf.com/content/CVPR2025/papers/Ren_GEN3C_3D-Informed_World-Consistent_Video_Generation_with_Precise_Camera_Control_CVPR_2025_paper.pdf),
[MVGD](https://mvgd.github.io/), [GeNVS](https://nvlabs.github.io/genvs/)), and persistent latent
3D scene simulation such as PERSIST ([project](https://francelico.github.io/persist.github.io/)).

The candidate unit must therefore be the *information transition* from a hidden prediction to a
later contradictory observation and then to a future generated view, with a measurable locality
and anti-leakage guarantee.

## Candidate A — Reveal-Residual Surface Transport (RRST)

### Mechanism

Maintain two typed state spaces:

* `E`: measured evidence, containing only RGB-D observations and their camera poses;
* `H(q)`: a query-conditioned hidden-surface belief for a future ray bundle `q`, containing a
  predicted surface geometry/appearance, uncertainty, and an auditable provenance ID.

Before the reveal, the model predicts `H(q)` without writing it to `E`. When a delayed RGB-D
reveal arrives, project it into the same canonical surface coordinates as `H`. Compute a residual
between the observed surface and the pre-reveal prediction, then transport only this residual
along a visibility/geodesic correspondence field attached to the predicted surface:

```text
delta_e(x) = M_e(x) K_e(x, x_e) [phi(observation_e) - H_pre(x_e)]
H_post = H_pre + delta_e
E_post = E_pre union observation_e
```

`M_e` is the independently computed newly-visible support; `K_e` does not diffuse the correction
to unrelated surfaces. The generator receives `E_post` and `H_post`; it never receives the raw
reveal frame through the hypothesis branch. This is a state transition for a predictive surface
belief, not append-only frame retrieval or a generic completion input.

### Closest prior and separation

The closest priors are SceneSense's map reconciliation (predicted occupancy is inpainted without
overwriting measured occupancy), online 3D belief update, fixed-lag state estimation, and
**Boosting View Synthesis with Residual Transfer** (CVPR 2022), which already computes residual
colors and transfers them through 3D correspondences and visibility/angular weights
([paper](https://openaccess.thecvf.com/content/CVPR2022/papers/Rong_Boosting_View_Synthesis_With_Residual_Transfer_CVPR2022_paper.pdf),
[project](https://boosting-view-synth.github.io/)). Therefore residual transport or 3D residual
warping alone is **not** an innovation. RRST survives only as a narrow state-semantic hypothesis:
(i) an auditable pre-reveal *generative* surface hypothesis, (ii) a delayed contradictory reveal
updates that same hypothesis while measured evidence remains immutable, and (iii) the update
improves a later camera-conditioned RGB/geometry generation. If an existing system is found with
this exact three-stage target, RRST must be retired.

### Falsifiable predictions

1. On hidden -> reveal -> reappearance episodes, RRST improves reappearance-region RGB and depth
   over an append-only context control and a parameter/capacity-matched generic completion or
   depth-adapter control.
2. The improvement is concentrated on the reveal support `M_e`; an untouched region with no
   contradictory evidence changes by at most a predeclared drift tolerance.
3. The correction magnitude tracks the pre-reveal residual: matched reveals with larger residuals
   produce larger local updates, while unrelated reveals do not change the queried surface.
4. The effect survives camera-order and slot-0 gauge canonicalization from C8. If it disappears
   under RS, the earlier effect was a conditioning confound, not RRST.

### Minimum experiment

Construct at least eight independent RGB-D episodes from held-out scenes. Use four delivered
context frames, one target surface hidden from them, a delayed reveal frame, and a later held-out
reappearance camera. Compare the same frozen denoiser under: (a) append-only reveal, (b)
capacity-matched generic completion/depth adapter, and (c) RRST. Keep the denoising seed and
target camera fixed. Measure pre/post surface error, reappearance RGB/depth error, update support
overlap with `M_e`, untouched-region drift, and the provenance ledger (`E` must not contain
predictions). A first feasibility pass can use a lightweight zero-initialized residual adapter;
it must not be described as a validated method.

### Kill condition

Kill RRST if its gain is explained by extra reveal pixels, parameter count, or generic completion;
if the update is global rather than support-local; if untouched regions drift beyond tolerance;
if the gain vanishes after RS canonicalization; if a raw append-only control matches it; or if a
prior paper has the same residual-to-predictive-belief-to-reappearance pathway.

## Candidate B — Causal Reveal Residual (CRR)

### Mechanism

Treat a reveal as a persistent, localized intervention on the world-model state rather than as
another conditioning frame or a one-off image repair. The event produces a state token `u_e` that
is reused for multiple future cameras. For each future camera and the same diffusion noise, run a
pre-reveal trajectory and a post-reveal trajectory. Inject a learned residual branch only on rays
that intersect newly revealed geometry:

```text
eps_post(z_t, q) = eps_pre(z_t, q) + M_e(q) * R_theta(delta_e, q, t)
```

Outside `M_e`, the branch is exactly zero and the two trajectories share the same latent. The
training objective includes a paired counterfactual term: the post-reveal output should improve
on `M_e`, while the pre/post difference outside `M_e` should be zero up to the declared numerical
tolerance. The event token carries the reveal camera rays, canonical surface residual, support mask,
and a provenance ID; a raw RGB frame is not simply concatenated to context. The same `u_e` must
produce a coherent correction on a reveal camera and on a third held-out camera that sees the
corrected surface from a different pose.

### Closest prior and separation

Closest priors are masked diffusion/inpainting, SceneSense occupancy inpainting, pointmap or
depth ControlNet adapters, test-time geometric consistency refinement, **Counterfactual World
Modeling** (structured masking and counterfactual prompting; [CWM](https://arxiv.org/abs/2306.01828)),
and correspondence-guided fixed-seed diffusion editing such as **Edicho**
([paper](https://openaccess.thecvf.com/content/ICCV2025/papers/Bai_Edicho_Consistent_Image_Editing_in_the_Wild_ICCV2025_paper.pdf)).
Thus same-seed comparison, explicit correspondence, or an outside-mask edit is not novel alone.
The surviving delta must be a *persistent* event state produced by a delayed RGB-D reveal, reused
across future cameras, with a strict geometry-derived support and an independent third-camera
test. This causal locality plus cross-camera state persistence is the method claim; the mask alone
is not.

### Falsifiable predictions

1. The same-noise post/pre output difference has high overlap with `M_e` (predeclare a support
   precision/recall threshold) and low energy outside `M_e`.
2. On `M_e`, post-reveal depth and RGB improve over pre-reveal and append-only controls; outside
   `M_e`, quality and feature identity remain statistically unchanged.
3. A deliberately contradictory but spatially unrelated reveal produces no correction to the
   queried surface, showing that CRR uses geometry support rather than event count.
4. The improvement must be separated into (a) a camera that directly sees the reveal and (b) a
   third held-out camera that only benefits through the updated hidden belief. If only the reveal
   camera improves, the effect is ordinary image repair rather than world-model state correction.
5. Reusing `u_e` for two or more held-out cameras gives a coherent direction of improvement; a
   fresh one-off repair branch that sees only the reveal camera should fail this cross-camera test.

### Minimum experiment

Use eight held-out episodes and paired same-seed inference. For each episode produce five outputs:
pre-reveal, CRR post-reveal, append-only post-reveal, generic completion post-reveal, and a
no-reveal counterfactual. Compute
per-pixel depth/RGB errors, `M_e` overlap, outside-mask drift, and latent trajectory divergence
versus denoising time. Add a no-reveal counterfactual (same target cameras and seeds) and evaluate
both the reveal camera and a third held-out camera. Reuse the same event token across at least two
future queries. This can be implemented first with a frozen denoiser and a zero-initialized
residual adapter; no new evidence may be written to the measured map.

### Kill condition

Kill CRR if support-local intervention cannot be measured, if pre/post divergence is global, if
same-seed paired gains are no larger than append-only or generic completion, if improvement occurs
only on the reveal camera but not a third camera, or if the no-reveal counterfactual changes the
same pixels. Kill it if the effect is only an auxiliary geometry-head improvement without generated
RGB/depth improvement, or if the same causal pair and support-gated denoising operator is found in
prior camera-conditioned NVS work.

## Candidate C — Surface-Lifecycle Query Tokens (SLQT)

### Mechanism

Represent an unseen surface by an event token rather than by a dense global completion map. A token
stores `(surface provenance, occlusion boundary, visibility cone/interval over future cameras,
pre-reveal geometry/appearance belief, uncertainty)`. A target camera retrieves tokens whose
visibility cones intersect its rays. A delayed reveal updates only the matching token via the
surface residual; the update is then decoded into the requested camera through the stored
visibility transform. The ledger keeps measured observations and predictive tokens separate.

The information path is therefore surface-lifecycle -> camera-ray query -> generated view, rather
than frame list -> pooled context -> generated view. The key prediction is about *which future
camera rays will expose which hidden surface*, not only what geometry might exist somewhere in a
global map.

### Closest prior and separation

Closest priors include visibility-aware NVS, frontier-based scene completion, persistent 3D maps,
and explicit 3D beliefs. Frontier representations and occlusion masks are already known; a token
or map by itself is not novel. SLQT survives only if the token's pre-reveal visibility interval
and reveal residual are necessary for future camera-conditioned generation, and if the same gain
cannot be obtained by a dense map plus generic retrieval.

### Falsifiable predictions

1. Reappearance gains are largest for query cameras inside the token's predicted visibility cone
   and vanish for matched cameras outside it.
2. Token updates commute with permutation of context frames after the C8 RS gauge fix; raw frame
   retrieval does not provide this invariance.
3. Token-level uncertainty predicts reveal error and calibrates future-view depth confidence better
   than a global completion confidence map.

### Minimum experiment

On the same eight held-out episodes, build tokens from the four context frames using independent
geometry masks. Evaluate target cameras sampled inside/outside each token's predicted visibility
cone. Compare SLQT against a dense generic completion map and append-only retrieval with matched
memory size. Report view-conditioned gain, cone selectivity, context-order commutativity, and
calibration. This is initially a representation/evaluation pilot, not a training claim.

### Kill condition

Kill SLQT if visibility-cone selectivity is absent, if dense completion plus retrieval matches it,
if tokens collapse into ordinary frame IDs, or if uncertainty is not calibrated. Treat it as an
implementation detail of RRST rather than a paper contribution unless the query-conditioned
selectivity survives independent scenes.

## Ranking and decision rule

1. **CRR** is the primary candidate: it is the only mechanism that adds a potentially defensible
   information-pathway delta beyond residual transfer, namely a delayed reveal as a same-noise,
   support-local intervention with an outside-mask conservation test.
2. **RRST** is a subordinate state representation for CRR. Its residual transport is prior art;
   only the predictive-belief semantics and delayed reveal target may survive.
3. **SLQT** is a lower-priority representation variant. Do not run a large implementation before
   CRR feasibility; it is most exposed to prior-art overlap.

The next research action should be a zero-GPU data-contract and paired-evaluation prototype for
RRST + CRR. No architecture claim or training run is authorized until C8 support/delivery/index
diagnostics pass and the owner accepts the preregistration. If C8 shows that the failure is
delivery/indexing rather than support scarcity, retire all three candidates for this pipeline.
