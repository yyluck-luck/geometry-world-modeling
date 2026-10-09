# R40 hostile update: residual transport is a substrate, not the novelty

Date: 2026-09-23

This update supersedes the novelty interpretation of RRST while preserving it as an implementation
option. The project remains `new_method_validated=false` and `novelty_authorization=NONE`.

## New killer prior

[Boosting View Synthesis with Residual Transfer (CVPR 2022)](https://openaccess.thecvf.com/content/CVPR2022/papers/Rong_Boosting_View_Synthesis_With_Residual_Transfer_CVPR2022_paper.pdf)
already computes residuals in observed views and transfers them to novel views using 3D
correspondence, visibility, and angular weighting. Therefore `RRST`—residual transport through 3D
correspondence—is not a method novelty. It may be used as plumbing, but the paper cannot claim it.

## Surviving candidate: CRR as a falsification operator

The only remaining candidate is **CRR (Causal Reveal Residual)**, and even it is only a hypothesis:

1. materialize a pre-reveal hidden-surface hypothesis;
2. receive a delayed contradictory RGB-D reveal;
3. run a same-noise pre/post generation pair;
4. inject a residual branch only on the independently registered reveal support;
5. require the third-camera output to improve while the no-reveal counterfactual and all pixels outside
   the reveal support remain unchanged.

The differentiator is not residual transfer, a mask, a belief state, or a diffusion adapter alone. It
is a causal intervention contract: the delayed reveal must be the only new cause of a support-local
change, and the effect must transfer to a camera that did not provide the reveal.

## Remaining threats

- masked diffusion/inpainting may implement the same support-gated change;
- [Edicho](https://arxiv.org/abs/2412.21079) is a threat to fixed-seed correspondence-guided local
  diffusion editing;
- [Counterfactual World Modeling](https://arxiv.org/abs/2306.01828) is a threat to counterfactual
  masking and pre/post prediction comparisons;
- [PERSIST](https://francelico.github.io/persist.github.io/) is a threat to claims of persistent
  latent 3D scene state plus a renderer;
- [INGRID](https://twjhlee.github.io/projects/INGRID) is a threat to claims of selective geometry
  update after newly exposed occluded surfaces while preserving observed regions;
- 3D-Belief already covers generic belief update;
- WRBench already covers hide-and-return persistence;
- GEM-Occ already covers visibility-aware causal occupancy memory;
- SC-Explorer covers measured/predicted completion fusion;
- slot-0 coordinate/scale effects can mimic order or temporal effects.

CRR must therefore beat append-only reveal retrieval, capacity-matched generic completion, global
update, no-transport, and no-reveal controls. Its remaining distinction is only the combination of a
real delayed contradictory RGB-D event, a persistent event token reused across future
camera-conditioned generative views, and a third-camera same-noise causal test. If same-noise locality
cannot be measured in generated RGB/depth, close this route.

## Decision

Downgrade RRST from candidate contribution to engineering substrate. Promote CRR to the sole candidate
for a zero-GPU paired-episode contract. The contract must explicitly separate reveal-camera and
third-camera outcomes, keep measured evidence immutable, and report outside-mask drift. No GPU or
training run is justified before C8 support scarcity survives delivery/indexing controls.
