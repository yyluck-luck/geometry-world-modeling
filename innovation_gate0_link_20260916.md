# Innovation evidence required from Gate0

Recorded 2026-09-16, Asia/Shanghai. This is a source review and experiment-design note, not a model result. It uses the Supervisor idea-evaluator's nearest-work/fatal-flaw checks without generating another subjective score table.

## What the 2025–2026 papers actually force us to test

| Primary work read this round | Occupied idea | Evidence our candidate would need |
|---|---|---|
| [Video World Models with Long-term Spatial Memory, NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/467655d26fcc207bca08915dc91964c6-Abstract-Conference.html) | Geometry-grounded storage/retrieval for revisit consistency. This round verified its formal proceedings record and abstract; no fresh full-paper claim. | The frozen VMem consumer must actually use the named source, and a source replacement must change a later geometric error rather than only retrieval IDs. |
| [ReWorld, August 2026 preprint, Section 2.3](https://arxiv.org/html/2608.23565v1) | Pose-indexed bounded landmark memory, spatial redundancy eviction and pose-proximity retrieval. | Match candidate pool, coverage, pose diversity, active memory and off-device storage. Test whether conflict adds information beyond pose/redundancy; count the selector's extra forward passes. |
| [Future Forcing, May 2026 preprint, Sections 5.1–5.4](https://arxiv.org/html/2605.30083v1) | Future-aware KV selection/merging; evaluation includes full-cache similarity and long-video perceptual consistency. | Use an externally supplied, held-out future depth reference, held out from selection decisions, not full-cache output as truth. A VMem history-utility proxy is a local control, not a faithful reproduction of this KV policy unless the actual interface and implementation match. |
| [WorldRoamBench, June/July 2026 preprint, Appendix F.1](https://arxiv.org/html/2606.31672v3) | Generated-video scene memory is already measured with monocular geometry, transition localization, point-cloud registration and retention/hallucination. | FGB-SI must add an auditable source intervention and external sensor geometry. Retain errors in the fixed commanded coordinate frame; report post-registration errors separately because registration can remove rigid drift. This distinction is an inference from the compared protocols, not proof of novelty. |

These sources do not establish that SOCF-A is new. They narrow its possible contribution to **history-only prediction of the signed effect of replacing one named memory source on externally referenced future geometry, followed by useful abstention under an equal cost budget**. FGB-SI remains the measurement route if the selector fails.

## Minimum data witness for a discriminating experiment

1. **A usable geometric reference.** Registered RGB-depth, metric depth semantics, invalid mask, K, pose convention, and stable frame identity must be bound to the actual bytes. Sensor depth is external to CUT3R; a pose reconstructed from the same RGB-D stream is an estimated reference, not an independent motion-capture measurement. Generated-depth estimates require a frozen estimator and an honest estimator-error limitation.
2. **A real source intervention.** Retain source IDs through every consumer path. Replace one source with a predeclared pose/support-matched candidate to preserve k. Deletion is a separate arm unless a fixed-cost missing-slot control is implemented. All descendants of the changed source must be recomputed with common noise, not held artificially constant.
3. **Future outcomes isolated from decisions.** Source score, source identity, fallback choice, budgets and output hashes precede future RGB/depth scoring. Known query-camera commands are legitimate inputs to camera-conditioned generation; label the estimand conditional future-view consistency. They cannot simultaneously be called unseen pose predictions.
4. **History that tests more than recency.** Predeclare short-gap and leave/revisit queries with overlapping source support and varying pose/coverage. Select those conditions using allowed history/command metadata, not future loss. A dataset with no suitable revisit cannot demonstrate long-horizon memory just because it contains RGB-D frames.
5. **Independent scenes for later confirmation.** Two sequences from one physical scene do not supply two independent scenes. A single untouched scene may support a falsification pilot. It does not support population-level scene bootstrap intervals or a generalization claim. Freeze a larger independent-scene confirmation batch before tuning to this pilot.

Use paired source-replacement deltas against recent, pose, coverage and confidence controls; then test SOCF-A at matched acceptance and total cost. First select the decisive minimal comparison, rather than running many named proxies with incompatible architectures. Report valid-pixel and valid-frame denominators; invalid predictions must not silently improve scores by reducing coverage.

## A specific falsifier, not another method name

Pairwise source agreement alone cannot detect a shared geometric bias. If all source point sets are transformed by the same rigid transform, pairwise Euclidean disagreements are unchanged. When the target command/reference frame is held fixed, the projected future prediction can still be wrong. Transforming the target frame too is merely a harmless coordinate change and must not be counted as failure.

Consequently, compare a common-history-bias stress arm with an independent-source-perturbation arm and a no-op replay, under a fixed target command. This is a proposed controlled diagnostic, not a run or an established property of SOCF-A. If SOCF's signal already uses a reliable current anchor, test that anchor ablation. The decision is whether there is information beyond source agreement, pose and coverage, not whether a risk formula sounds plausible.

## Concrete Gate0 findings and next source

The [official raw 7-Scenes page](https://www.microsoft.com/en-us/research/project/rgb-d-dataset-7-scenes/) explicitly says RGB/depth images are uncalibrated and that the listed 585/585/320/240 values were default depth-camera intrinsics in KinectFusion. Those defaults cannot certify RGB-depth calibration. Chess acquisition remains useful provenance work, but it cannot be promoted to calibrated metric RGB-D solely from that page.

The [3DMatch author page](https://3dmatch.cs.princeton.edu/) documents a converted format with depth aligned to color, millimeter depth, invalid zero, intrinsics file and camera-to-world poses. Root requested a **source-only scene_13 acquisition proposal**; its exact official archive href, terms scope, and unresolved details are frozen in `work/S102_gate0_3dmatch/SOURCE_ONLY_ACQUISITION_PROPOSAL_20260916.json`. No ZIP request, listing, image/depth decoding, or pose-value read was performed by this agent.

The [UW v2 README](https://rgbd-dataset.cs.washington.edu/dataset/rgbd-scenes-v2/README.txt) identifies mapping-estimated poses, while the [3DMatch split](https://3dvision.princeton.edu/projects/2016/3DMatch/downloads/rgbd-datasets/split.txt) puts scene_13 in its training set. Thus project-held-out and pretrained-model-unseen are distinct claims. Public size metadata was seen during discovery; the proposal does not claim metadata blindness or score-based selection.

**Decision:** retain SOCF-A as unvalidated; FGB-SI as a falsification protocol. Advance the scene_13 source qualification without pretending its documented format, estimated poses, or archive existence already satisfies Gate0. No new approval or arbitrary accuracy threshold is introduced.

## Tool boundary

Available-tool discovery in this agent found web retrieval, node_repl and Computer History but no callable CUA/browser-control tool. The primary-source work above used web retrieval and source-only local HTTP fetches. It must not be reported as computer use or a Gemini answer. No model, training run, future score, or scientific result was produced.


## 2026-09-16 — FGB-SI distinction narrowed by primary-source review

**Design-only candidate:** FGB-SI (source-intervention future-geometry measurement) estimates the signed effect of retaining versus replacing one named history source on an externally supplied, held-out future RGB-D/pose state in a fixed commanded coordinate frame, with complete consumer-descendant recomputation and source-to-pixel provenance.

Closest occupied mechanisms include ReWorld pose-indexed bounded memory/redundancy retrieval, Future Forcing future-aware KV selection/merging, and WorldRoamBench geometry/retention metrics. Generic future-aware fixed-budget memory or KV importance is therefore not a novelty basis. The scoped distinction is the auditable named-source intervention plus externally supplied, held-out future RGB-D/pose reference and provenance.

Falsify if the effect adds no held-out future value beyond pose/coverage/confidence/utility, disappears under source/common-bias controls or registration checks, cannot be traced to external geometry, or appears only in one scene/horizon. If so, retain FGB-SI only as a negative/evaluation protocol. No experiment or novelty validation is authorized.


Pose limitation: the current 3DMatch evidence documents mapping-estimated camera-to-world poses, not independent motion-capture truth. FGB-SI must therefore say “externally supplied, held-out future RGB-D/pose reference” until sensor/reference independence is separately verified.
