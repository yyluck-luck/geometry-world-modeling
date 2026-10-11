# Where a geometry-memory method could still contribute

Research synthesis, searched 2026-10-10 America/Los_Angeles. Claims about proposed mechanisms are **ANALYTICAL / UNVERIFIED**, not new experimental findings.

## Abstract

The repository provides a useful falsification chain: repair geometry, test historical information, compare its geometric and generative consumption, then demand stronger simple controls. Its results do not establish a new generalizable video-memory method. Recent work already covers most obvious next steps: learned retrieval, local geometric memories, geometry-supervised latent memories, reliability filters and memory-conditioned guidance. A defensible next investigation must change a specific causal property of the system, with matched controls that separate that property from adaptation, extra context, data augmentation or post-hoc blending. A spatially correct response to memory interventions is more directly grounded in the project's measured consumer failures than a new long-rollout ancestry hypothesis. Neither is established novel by this search.

## Questions and search method

The frozen brief asks: RQ1 which repository conclusions survive their controls; RQ2 which mechanism gaps remain after recent literature; RQ3 which one falsifiable study merits a six-week investment. RQ1 is answered in [the experiment map](EXPERIMENT_MAP.md). RQ2 and RQ3 are addressed below.

Three independent search perspectives covered explicit geometry memory, critics of historical conditioning/retrieval, and adjacent uncertainty/data-assimilation methods. A subsequent adversarial synthesis checked exact collisions in counterfactual conditioning. Primary arXiv pages and relevant method/experiment sections were opened; the coordinator independently retrieved exact metadata for the references in LITERATURE_METADATA.json. This is a targeted broad web review, not a claim to have exhaustively searched the entire web. Publication venue labels are not inferred from preprints. Older direct antecedents are retained where they materially constrain novelty.

## 1. Representation and the geometry-to-generator interface

[VMem](https://arxiv.org/abs/2506.18903) uses visible surfels to index historical RGB views; [CUT3R](https://arxiv.org/abs/2501.12387) supplies persistent-state reconstruction, not guaranteed globally correct geometry. The project's scale and bank failures therefore expose a vulnerable interface rather than invalidate all geometric memory.

[AnchorWeave](https://arxiv.org/abs/2602.14941) already avoids globally fused geometry by retaining local spatial anchors and combining their evidence; [I3DM](https://arxiv.org/abs/2603.23413) instead uses implicit 3D features for retrieval and aligned, reliability-aware injection. Merely replacing a global surfel map with local maps, or adding a reliability gate to cross-view features, has direct predecessors. Their regimes and backbones differ from VMem, so a fair comparison requires a scoped adaptation or official implementation, not a paper-level score copied into the repository.

[SPMem](https://arxiv.org/abs/2506.05284) combines long-term spatial memory with other temporal memory; [OctWorld](https://arxiv.org/abs/2609.03919) develops adaptive octree mapping and spatial-condition augmentation. Both constrain a proposed 'robust fusion' story. [Mirage](https://arxiv.org/abs/2606.09828) places memory directly in latent space, whereas [GIM-World](https://arxiv.org/abs/2606.02436) distills geometry into implicit memory. [Geometry-as-context](https://arxiv.org/abs/2602.21929) couples geometry and RGB with camera-aware conditioning. Consequently a latent bridge, auxiliary geometry loss, camera gate or generic joint geometry/video objective is insufficient novelty on its own.

## 2. Which history should a consumer read?

[CaR](https://arxiv.org/abs/2606.23105) learns implicit retrieval from compressed history and [MemLearner](https://arxiv.org/abs/2606.31734) queries context through pretrained generator layers. [FAR](https://arxiv.org/abs/2609.34677) supervises retrieval utility using realized-future predictive likelihood while keeping deployment retrieval future-blind. Together they directly cover the broad motivation that geometric relevance and generator usefulness differ. S143 is valuable project evidence for that mismatch, but cannot by itself establish a new concept of consumer-aware retrieval.

[History-Guided Video Diffusion](https://arxiv.org/abs/2502.06764) combines histories and noise levels at the score level. [No Training, No Problem](https://arxiv.org/abs/2407.02687) analyzes an independent-condition approximation to unconditional guidance. P2's observed-source condition is not independent of the sample, so the latter's justification cannot simply be transferred to P2. P2 remains an interface diagnostic, even if its frozen empirical gates pass.

## 3. Writing, reliability and correlated information

[Keepsake](https://arxiv.org/abs/2610.06588) already changes retention using pose/appearance redundancy while holding the host generator and reader fixed; [Spatial Memory Intelligence](https://arxiv.org/abs/2610.02521) filters unreliable generated chunks at write time. [ID-Forcing](https://arxiv.org/abs/2610.03120) explicitly studies cache provenance and constrains self-caching. Thus 'remember fewer frames', 'reject bad frames' and 'track provenance' are not empty niches.

[3D-Belief](https://arxiv.org/abs/2605.11367) separates observed and imagined 3D state and updates beliefs with observations, while [Trust3R](https://arxiv.org/abs/2605.19539) models reconstruction uncertainty. An ancestry-aware fusion rule would need to isolate cross-observation correlation, not just add uncertainty or observed/generated labels. Conservative treatment of correlated map information is older robotics knowledge, including [TSDF merging with Kalman filtering and covariance intersection](https://doi.org/10.1007/s11370-025-00586-1). The publication page notes a correction; no detailed numerical claim from that article is used here.

This is a potentially meaningful second direction, but the repository's real-history-bank results do not establish recursive self-reinforcement. It also risks confusing consistency within an imagined world with knowledge of a real world: refusing every generated write can destroy useful scene continuity. First establish an actual consumer-relevant failure at fixed content, coverage and budget; stop if ordinary deduplication or observed-first memory solves it. [Diffusion data assimilation](https://arxiv.org/abs/2604.21180) further cautions that observations already included in conditioning are not automatically new independent evidence when reused in an inference correction.

## 4. Response to interventions and how to evaluate memory

[CWM](https://arxiv.org/abs/2312.06721) uses appearance interventions to interrogate predictive models, and [Point Prompting](https://arxiv.org/abs/2510.11715) propagates a local appearance marker through counterfactual video conditioning. A colored-patch propagation test is therefore established instrumentation, not a new method. [ARGUS](https://arxiv.org/abs/2606.11670) uses counterfactual identity-reference training; [CAER](https://arxiv.org/abs/2608.30897) uses action-versus-null prediction differences to redistribute ordinary training loss. They are close enough that any proposed response-training objective must be compared explicitly, not described as the first counterfactual video learning method.

The narrower possible distinction is **directly supervising the signed, spatially transported change in generated content when remembered evidence changes**, with the rest of the output invariant, at fixed retrieval and geometry. This is different from using a response magnitude merely as a detached loss weight, but that distinction alone does not prove sufficient novelty or usefulness. It must beat equal-data paired supervised fine-tuning, matched ordinary LoRA, inference-only counterfactual guidance, and shuffled-correspondence controls. A loss can cheat by reading the changed target through its noisy latent; paired-response evaluation must remove that shortcut.

[Echo-Memory](https://arxiv.org/abs/2606.09803) shows why replay and return behavior should be separated, while [R2M-Bench](https://arxiv.org/abs/2608.27328) controls revisit comparisons for temporal gap and non-revisit behavior. Average RGB PSNR alone can reward copying or stillness. The next study must preserve camera following, unrelated regions and ordinary unedited image quality while measuring its intended memory response.

## Cross-branch conclusion

RQ1: the project has credible source-level failures, real-data repairs and informative negative generation results, but no validated new method. RQ2: the broad representation/retrieval/reliability recipes are substantially occupied; a narrow causal training or write-update property remains a hypothesis, not an established gap. RQ3: first test a spatial-response learning mechanism grounded in S139/S141, then decide whether it deserves the remaining weeks. An ancestry-aware writer remains a reserve hypothesis, not a parallel project. The decisive criteria and resource boundary belong in [the executable plan](NEXT_DIRECTION_AND_PLAN.md).

The strongest objection is that any apparent response-training improvement may be explained by extra paired data or an existing guidance method. If those controls match it, terminate the proposed method; retain the scientific negative. A second objection is that the project-specific VMem setup may be unusually weak. Before a CCF-A claim, repeat the supported mechanism on another suitable backbone and untouched scenes. Failure to do so limits the contribution even if the local pilot improves.

## Verified reference registry

Exact titles below are taken from retrieved arXiv metadata. Relevant primary sections were read by the search team, not every page of every appendix. The ledger records retrieval dates; no absence-of-search-result argument is used as novelty evidence.

- **VMem: Consistent Interactive Video Scene Generation with Surfel-Indexed View Memory**. arXiv:2506.18903 (2025/06/23). [Primary record](https://arxiv.org/abs/2506.18903).
- **Continuous 3D Perception Model with Persistent State**. arXiv:2501.12387 (2025/01/21). [Primary record](https://arxiv.org/abs/2501.12387).
- **AnchorWeave: World-Consistent Video Generation with Retrieved Local Spatial Memories**. arXiv:2602.14941 (2026/02/16). [Primary record](https://arxiv.org/abs/2602.14941).
- **MemLearner: Learning to Query Context memory for Video World Models**. arXiv:2606.31734 (2026/06/30). [Primary record](https://arxiv.org/abs/2606.31734).
- **Keepsake: Selective Spatial Memory for Long-Horizon Video Generation**. arXiv:2610.06588 (2026/10/05). [Primary record](https://arxiv.org/abs/2610.06588).
- **Video World Models with Long-term Spatial Memory**. arXiv:2506.05284 (2025/06/05). [Primary record](https://arxiv.org/abs/2506.05284).
- **Latent Spatial Memory for Video World Models**. arXiv:2606.09828 (2026/06/08). [Primary record](https://arxiv.org/abs/2606.09828).
- **Geometry-Aware Implicit Memory for Video World Models**. arXiv:2606.02436 (2026/06/01). [Primary record](https://arxiv.org/abs/2606.02436).
- **Spatial Memory Intelligence: Endowing World Models with Understanding-Driven Long-Term Memory**. arXiv:2610.02521 (2026/10/01). [Primary record](https://arxiv.org/abs/2610.02521).
- **OctWorld: Long-Range World-Consistent Video Generation with Octree-Based 3D Mapping**. arXiv:2609.03919 (2026/09/03). [Primary record](https://arxiv.org/abs/2609.03919).
- **Geometry-as-context: Modulating Explicit 3D in Scene-consistent Video Generation to Geometry Context**. arXiv:2602.21929 (2026/02/25). [Primary record](https://arxiv.org/abs/2602.21929).
- **History-Guided Video Diffusion**. arXiv:2502.06764 (2025/02/10). [Primary record](https://arxiv.org/abs/2502.06764).
- **No Training, No Problem: Rethinking Classifier-Free Guidance for Diffusion Models**. arXiv:2407.02687 (2024/07/02). [Primary record](https://arxiv.org/abs/2407.02687).
- **Compression and Retrieval: Implicit Memory Retrieval for Video World Models**. arXiv:2606.23105 (2026/06/22). [Primary record](https://arxiv.org/abs/2606.23105).
- **Echo-Memory: A Controlled Study of Memory in Action World Models**. arXiv:2606.09803 (2026/06/08). [Primary record](https://arxiv.org/abs/2606.09803).
- **R2M-Bench: Evaluating Revisit Memory via Relative Consistency in Interactive Video World Models**. arXiv:2608.27328 (2026/08/27). [Primary record](https://arxiv.org/abs/2608.27328).
- **In-Distribution Forcing for Long Video Generation at Test Time**. arXiv:2610.03120 (2026/10/02). [Primary record](https://arxiv.org/abs/2610.03120).
- **3D-Belief: Embodied Belief Inference via Generative 3D World Modeling**. arXiv:2605.11367 (2026/05/12). [Primary record](https://arxiv.org/abs/2605.11367).
- **I3DM: Implicit 3D-aware Memory Retrieval and Injection for Consistent Video Scene Generation**. arXiv:2603.23413 (2026/03/24). [Primary record](https://arxiv.org/abs/2603.23413).
- **Learning What to Recall: Adaptive Multi-Cue Episodic Memory for World Models**. arXiv:2609.34677 (2026/09/28). [Primary record](https://arxiv.org/abs/2609.34677).
- **Trust It or Not: Evidential Uncertainty for Feed-Forward 3D Reconstruction with Trust3R**. arXiv:2605.19539 (2026/05/19). [Primary record](https://arxiv.org/abs/2605.19539).
- **Uncertainty-Aware Spatiotemporal Super-Resolution Data Assimilation with Diffusion Models**. arXiv:2604.21180 (2026/04/23). [Primary record](https://arxiv.org/abs/2604.21180).
- **ARGUS: Stacked Multi-View Identity Mosaic Injection for Subject-Preserving Video Generation**. arXiv:2606.11670 (2026/06/10). [Primary record](https://arxiv.org/abs/2606.11670).
- **CAER: Causal Action Effect Reweighting for World Model Training**. arXiv:2608.30897 (2026/08/31). [Primary record](https://arxiv.org/abs/2608.30897).
- **Point Prompting: Counterfactual Tracking with Video Diffusion Models**. arXiv:2510.11715 (2025/10/13). [Primary record](https://arxiv.org/abs/2510.11715).
- **Understanding Physical Dynamics with Counterfactual World Modeling**. arXiv:2312.06721 (2023/12/11). [Primary record](https://arxiv.org/abs/2312.06721).
