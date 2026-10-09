# R38 innovation search: from posterior correction to residual transport

Date: 2026-09-23

This is a continuation of R37. It is a literature and method-design record, not authorization. The project remains `new_method_validated=false` and `novelty_authorization=NONE`.

## New occupancy findings

Two recent sources further narrow the space:

- [WRBench / Current World Models Lack a Persistent State Core](https://arxiv.org/abs/2606.20545) already isolates camera-away, hidden-event, and return-state consistency. Therefore “preserve an off-screen event until re-observation” is a benchmark-level problem, not a sufficient method claim.
- [GEM-Occ](https://arxiv.org/abs/2607.05543) already fuses occupied-surface evidence and free-space ray evidence into an uncertainty-aware causal occupancy memory. Therefore “add free-space evidence,” “visibility-aware occupancy,” or “causal occupancy update” is not a clean novelty axis.

The remaining distinction must be static or quasi-static hidden-surface *appearance/geometry belief revision inside a camera-conditioned generator*, and must be tested with a counterfactual camera. A dynamic off-screen state benchmark, occupancy mapper, or generic belief model is a required baseline, not a contribution.

## Candidate CRRT — Counterfactual Reveal-Residual Transport

### Mechanism

The model keeps three typed quantities for a hidden surface patch:

1. measured evidence, which is append-only;
2. a pre-reveal predictive field in a query-independent 3D coordinate system;
3. a residual field that says how the prediction differs from the first revealing RGB-D observation.

When the reveal arrives, the method does not append the new frame and regenerate globally. It projects the reveal residual through the existing 3D correspondence into a *third, counterfactual camera* and injects only that transported residual into the generator conditioning. The predicted field is changed only on the connected reveal component; measured evidence is never overwritten.

The proposed information pathway is therefore:

`delayed RGB-D contradiction → 3D residual transport → counterfactual novel-view correction`.

This is narrower than posterior update, scene completion, or persistent memory. It is also different from WRBench's dynamic endpoint persistence: the target is a static hidden surface's geometry/appearance posterior and the test camera is not the reveal camera.

### Why this might be substantive

An append-only control can use the revealing image at the reveal camera. A generic completion control can improve the third view with extra capacity. Neither is forced to transport the *measured correction* through a shared 3D correspondence into a camera that did not provide the correction. The causal claim is that the third-view improvement comes from the transported residual, not from extra context or a fresh hallucination.

### Strongest prior-art objections

- [3D-Belief](https://arxiv.org/abs/2605.11367) occupies explicit 3D belief and sequential update.
- [Geometry-as-context](https://openaccess.thecvf.com/content/CVPR2026/html/Hu_Geometry-as-context_Modulating_Explicit_3D_in_Scene-consistent_Video_Generation_to_Geometry_CVPR_2026_paper.html) and [WorldStereo](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_WorldStereo_Bridging_Camera-Guided_Video_Generation_and_Scene_Reconstruction_via_3D_CVPR_2026_paper.html) occupy geometry feedback and cross-view correspondence.
- [GEM-Occ](https://arxiv.org/abs/2607.05543) occupies causal visibility-aware occupancy memory.
- [WRBench](https://arxiv.org/abs/2606.20545) occupies hide-and-return persistence evaluation.

Therefore CRRT survives only if the paper claims the *counterfactual reveal residual transport operator* and demonstrates a third-camera gain after matched controls. Calling it a “belief memory,” “re-observation consistency,” or “geometry adapter” kills the distinction.

## Minimum falsification experiment

Use a held-out static RGB-D scene and construct one episode:

`four-frame context → hidden target camera prediction → first reveal camera RGB-D → third counterfactual camera query`.

Pre-register a patch mask from geometry, not target RGB. Report:

- pre-reveal depth/appearance error and calibrated uncertainty;
- reveal residual error at the reveal camera;
- third-camera RGB and depth error before/after residual transport;
- untouched-region change and measured-evidence byte identity;
- comparison with (a) append-only reveal-frame retrieval, (b) generic completion/depth adapter with equal trainable parameters, (c) no-transport local update, and (d) global update;
- a camera-order permutation control with slot 0 canonicalized.

The candidate is rejected if the third-camera gain disappears under the no-transport control, if append-only retrieval matches it, if the effect is confined to the reveal camera, or if untouched regions change beyond the preregistered tolerance.

## Decision

CRRT is the only new candidate currently worth a zero-GPU data-contract pilot. It is a hypothesis, not an innovation claim. First requirement is still C8: establish that the current failure contains true support scarcity after delivery and indexing are separated. If C8 does not show that condition, stop CRRT and document the infrastructure explanation.

