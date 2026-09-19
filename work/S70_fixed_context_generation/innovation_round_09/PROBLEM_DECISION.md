# Batch 09 — Does the current consumer represent a synchronized dynamic future?

Decision: **stop the extra three-camera dynamic-future experiment on the current VMem consumer.** Preserve its legitimate image-set novel-view-synthesis task. This is a task/input mismatch, not evidence that VMem fails its stated task, and not a newly established method.

Actual review: 2026-09-09 03:42:36 UTC to 2026-09-09T03:48:37.265153+00:00. Source text and previously read primary papers only; no scientific arrays, weights, images or models were opened or executed.

## What the exact consumer supports

VMem's paper §3.2 describes a camera-conditioned image-set generator based on SEVA. It is adapted to four reference and four target views and coherent target camera trajectories; §4.1 reports RealEstate10K training with randomly sampled context views. The temporal subscripts enumerate views and autoregressive generation. These statements do not specify a separately controllable physical time for each requested view. This is primarily scene exploration/NVS, not an established past-only model of future human actions. [VMem author manuscript, §§3–4.1](https://arxiv.org/html/2506.18903v1).

The pinned local source confirms the narrower interface:

- `modeling/pipeline.py:1124–1193`: `get_cond` consumes reference latents, cameras, intrinsics, translation scale, appearance embeddings and input masks. Its four conditioning fields contain appearance, latent replacement/masks and Plücker geometry. It has no independent acquisition/query-time argument.
- `pipeline.py:1251–1309`: retrieved `context_time_indices` are omitted from `get_cond` and sampling; they are passed to subsequent scene reconstruction. Context slots precede target slots. Slot order, first-reference camera normalization, masks and reference appearance still matter; omitting explicit time is not absence of all temporal information.
- `utils/util.py:673–737`: `T=8` sets sample grouping and latent shape; the denoiser receives `num_frames`. `modeling/sampling.py:139–183` obtains network `t` from noise sigma. `network.py:178–237` embeds this diffusion index. It is not elapsed physical time.
- `modeling/modules/transformer.py:114–255` performs attention across the frame dimension; no explicit frame timestamp/position embedding occurs in this inspected block. **This is not a proof of whole-pipeline permutation equivariance**, given camera anchoring, noise-slot identity, other layers and training. An ordered tensor is not automatically an ordinary causal video axis either.

Thus one call can jointly sample several camera views of an intended static scene. It cannot expressly request “these four cameras all observe the same future at +0.5 seconds” versus “they observe +0.5, +1, +1.5, +2 seconds,” with an otherwise identical bundle. Inserting untrained metadata, reordering slots or sharing seeds cannot supply that distinction. Joint sampling is necessary provenance for a joint sample, not proof of synchronized dynamic world-state semantics. Different camera-conditioned calls with the same seed need not depict one world.

## The nearest solution is already known

4DiM (ICLR 2025) explicitly conditions a joint distribution on per-image cameras **and scalar relative timestamps**. Its §3/Eq.1 footnote states permutation equivariance over frames; Masked FiLM separately represents diffusion noise, rays and video timestamps, distinguishing missing from zero. It therefore has a declared time×camera contract that the inspected VMem lacks. This does not prove perfect dynamic consistency or that its weights/data are locally available. [4DiM §3](https://arxiv.org/html/2407.07860v2).

4Real-Video (CVPR 2025) instead represents a time×view grid with synchronized temporal/view streams. Its §3 setup supplies a fixed-view video and a freeze-time video. The temporal input can supply the motion realization, so its task must not be relabeled unknown-action future forecasting from past frames. No new paper was necessary. [4Real-Video §§3–3.2](https://arxiv.org/html/2412.04462v1).

## Cheapest decisive check and stopping rule

At 03:46:53.891426 UTC, a stdlib-only AST inspection independently enumerated the actual `get_cond` signature and generation call arguments; the timestamp is absent at that boundary, while the later reconstruction call consumes `context_time_indices`. No project module was imported. This source check is enough to reject the proposed timestamp intervention on this unchanged consumer; another generation is unnecessary.

A symbolic counterexample clarifies the limit: hold **the complete consumed bundle**, model state and random stream fixed, and change only an external annotation from synchronized to staggered physical query times. Since that annotation is not consumed, the conditional mapping is unchanged. This is a known missing-variable argument, not an assertion that two different histories, slot assignments or conditions are equal, or a measured output result.

Do not acquire a third camera or launch an extra VMem arm for that claim. Reopen only for an available dynamic consumer whose documented and trained interface actually separates physical time and camera, or a separately declared static-snapshot NVS question. Timestamp conditioning and synchronization already have close precedents; adding either is not automatic novelty. S70 remains a comparison of two complete fixed conditioning bundles; it does not isolate the effect of moving source 13 to another slot, physical time, memory compression or dynamic consistency.
