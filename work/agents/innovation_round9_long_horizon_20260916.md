# Innovation Round 9 — Exact-contract audit for SIFG-DEV-01

**Recorded:** 2026-09-16 (Asia/Shanghai; file-writing time is the authoritative record)  
**Role:** bounded 2025–2026 primary-source audit.  
**Question frozen before search:** Has a primary paper already implemented the *full* SIFG contract: (i) one fixed world-model consumer, (ii) complete matched replacement of one historical source tuple, (iii) identical candidate pool, denoising budget, camera controls and replayed noise, and (iv) an independently registered RGB-D/pose future outcome opened only after prediction sealing?

**Evidence boundary:** only official arXiv, OpenReview or CVF/PMLR pages were used. Search and reading do not access the project’s future outcomes, run VMem, or alter Gate0. This is a novelty audit, not method validation. `new_method_validated=false`; `novelty_authorization=NONE`.

## Result in one sentence

I found no primary source that documents all four SIFG elements together. The individual axes are substantially occupied: geometry-indexed memory, fixed-budget retrieval, source/evidence routing, RGB/XYZ consistency and long-horizon revisit benchmarks all exist. The remaining claim is therefore a **conditional evaluation protocol** (source-level intervention plus answer-isolated sensor geometry), not a new memory architecture. Absence in this bounded search is not proof of global nonexistence; the protocol still needs a wider citation sweep before paper submission.

## Closest methods and exact differences

| Primary source (year) | What is actually tested or introduced | Which SIFG element it overlaps | What is still different from SIFG-DEV-01 | Reviewer risk |
|---|---|---|---|---|
| **Video World Models with Long-term Spatial Memory** (NeurIPS 2025, arXiv:2506.05284) | Geometry-grounded point-map memory plus episodic keyframes for revisits; reports long-horizon consistency and video metrics. | Long-term spatial memory and retrieval. | No documented complete one-source tuple replacement with the same frozen consumer and independently registered future RGB-D/pose answer. Reported metrics are not the SIFG source effect estimand. | High overlap for “geometry memory improves revisit consistency.” |
| **GIM-World** (arXiv:2606.02436, 2026) | Fixed-size implicit memory tokens, camera-queryable geometry head and information-guided pruning; evaluated on MIND. | Geometry-aware pruning under bounded memory. | No evidence of paired source replacement, exact-noise replay, or future sensor-answer isolation. It is a learned method, whereas SIFG is a measurement contract. | Very high for “geometry + fixed-budget pruning.” |
| **WorldTrace / Addressable Memory** (arXiv:2608.07408, 2026) | Assigns virtual in-distribution positions and canonicalizes compressed KV keys; compares cache policies under fixed cache settings and extended rollouts. | Fixed cache budget and controlled memory-policy comparison. | Controls addressability/content compression, not historical RGB-D source identity; no registered RGB-D future metric outcome or source-level intervention is documented. | High for fixed-budget memory claims. |
| **ReWorld** (arXiv:2608.23565, 2026) | Bounded KV cache with pose-indexed landmark bank, redundancy eviction, chunk-drop training and long-horizon palindrome revisits; ablates cache policy. | Bounded memory, pose-indexed retrieval and revisit evaluation. | It evaluates cache policies and recall/action/video axes, not complete source-tuple replacement with an unchanged VMem consumer and sealed registered sensor outcome. | High for “bounded pose-indexed memory” and long-horizon recall. |
| **Mem-World** (arXiv:2606.18960, 2026) | Surfel-indexed 4D wrist-view memory; geometry-aware retrieval conditioned on future actions for manipulation. | Geometry-aware source retrieval. | Dynamic robot manipulation setting; no evidence for matched source replacement, fixed-noise paired generation, or independent registered RGB-D/pose scoring. | Medium-high; source-aware retrieval is occupied. |
| **World in World** (arXiv:2609.11548, submitted 10 Sep 2026) | Training-free camera/time-labelled evidence interface, token support, correspondence routing and evidence-wise attention CFG on a frozen causal video model. | Frozen consumer, per-source evidence and source routing. | Evidence channels are selected/routed for rerendering; the paper does not document SIFG's complete tuple swap, replayed sampler noise, or answer-isolated registered RGB-D future estimand. Its perceptual/temporal/camera evaluation differs. | Very high for “source-labelled evidence + frozen model.” |
| **World-consistent Video Diffusion (WVD)** (CVPR 2025) | Joint RGB and XYZ diffusion; uses XYZ to support multi-view/video generation and depth/pose tasks. | Explicit geometry output and geometric evaluation. | No long-horizon source-memory intervention; no matched source tuple or future-window answer isolation. | High for “RGB+3D supervision improves consistency.” |
| **Geometry-guided Online 3D Video Synthesis** (CVPR 2025) | RGB-D/pose inputs, TSDF fusion and temporal geometric filtering guide blending for novel-view synthesis. | Registered RGB-D and temporal geometry consistency. | Geometry is fused/filtered as the method; not a VMem historical-memory source intervention, and no exact replayed paired source effect. | Medium-high for RGB-D temporal consistency. |
| **Aether: Geometric-Aware Unified World Modeling** (ICCV 2025) | Joint 4D reconstruction, action-conditioned prediction and visual planning in one framework. | Geometry-aware world modelling and multi-task evaluation. | Does not establish SIFG's source-level intervention or answer-isolated registered RGB-D/pose scoring contract. | Medium for broad geometry-aware world-model framing. |
| **What-If World** (arXiv:2605.27589, 2026) | Paired prompt interventions from a shared initial state; scores adherence, physics, environment preservation and outcome divergence. | Paired intervention logic and fixed starting state. | Intervention is prompt/condition level, not a complete historical memory source tuple; no sensor-registered future RGB-D answer. | Medium; “counterfactual” wording is already occupied. |

## What the audit supports

1. **Do not claim novelty for a geometry-aware memory selector, fixed-budget cache, source routing, or a perceptual consistency metric by itself.** Each has strong 2025–2026 neighbours.
2. **SIFG can remain a narrowly distinguishable evaluation problem only if every contract element is explicit.** The novelty is the *estimand and evidence boundary*: a complete source-bundle intervention is replayed through the same consumer, then evaluated against a future registered sensor answer that was inaccessible during selection.
3. **SOCF-A is a policy hypothesis, not yet a method.** A history-only conflict score plus abstention should be promoted only if it predicts the signed source-swap effect after controlling for pose, support, coverage, landmark/edge density and uncertainty, on independent scenes and horizons.
4. **A negative result is scientifically useful.** If source swaps do not change future sensor geometry, or if pose/coverage controls explain the effect, SIFG remains a diagnostic protocol and SOCF-A must not be promoted.

## Falsifiable prediction for SIFG-DEV-01

For a fixed qualified development episode with context tuple `C`, selected source `i`, matched replacement `j`, four target cameras `Q`, and exactly replayed initial noise `u`, define

`Delta_q = L_q(E_phi(G_theta(C,j,Q,u)), D_q) - L_q(E_phi(G_theta(C,i,Q,u)), D_q)`.

The pre-registered prediction is:

> When `r(j) < r(i)` under the history-only discrepancy and matching rule, the mean `Delta_q` across the four target views will be negative and larger in magnitude than the observed replay spread, while the risk-neutral matched replacement `j0` will not show the same directional improvement.

This is a **conditional development prediction**, not a population claim. It becomes informative only after the outputs are sealed, the evaluator and sensor target are opened under the Gate0 contract, and all three arms (`A`, `B`, `P`) preserve four active sources, identical model/configuration, camera controls, noise and denoising budget.

## Kill rule

Terminate method promotion (retain only a diagnostic/negative result) if **any** of the following is observed:

- `B-A` is non-negative beyond replay variability, or its sign reverses across independent scenes/horizons;
- the neutral matched replacement `P` produces the same improvement as `B`;
- pose, field-of-view, support coverage, landmark/edge density or uncertainty-matched placebos explain the contrast;
- future RGB-D/pose values influence selection, thresholds, gauge/scale fitting or intervention construction;
- a different active-context count, stale downstream state, incomplete tuple, changed noise or changed NFE makes the arms non-comparable;
- the registered sensor evaluator is not metrically identifiable, or outcomes are censored by evaluator failure;
- RGB/visual quality improves while future metric geometry worsens.

No amount of additional qualitative examples can override this rule. A failed prediction should be reported as evidence against the proposed mechanism.

## Recommended next literature action (bounded)

Before submission, perform one targeted citation-chain search from GIM-World, ReWorld, WorldTrace and World in World for terms `source ablation`, `leave-one-memory-out`, `counterfactual memory`, `RGB-D ground truth`, `registered depth`, and `paired intervention`. Add a work only if its primary paper explicitly documents the contract elements above. Do not broaden the method claim while that search is pending.

## Primary links checked (2026-09-16)

- [Video World Models with Long-term Spatial Memory, NeurIPS 2025](https://arxiv.org/abs/2506.05284)
- [GIM-World](https://arxiv.org/abs/2606.02436)
- [Addressable Memory / WorldTrace](https://arxiv.org/abs/2608.07408)
- [ReWorld](https://arxiv.org/abs/2608.23565)
- [Mem-World](https://arxiv.org/abs/2606.18960)
- [World in World](https://arxiv.org/abs/2609.11548)
- [World-consistent Video Diffusion](https://openaccess.thecvf.com/content/CVPR2025/html/Zhang_World-consistent_Video_Diffusion_with_Explicit_3D_Modeling_CVPR_2025_paper.html)
- [Geometry-guided Online 3D Video Synthesis](https://openaccess.thecvf.com/content/CVPR2025/html/Ha_Geometry-guided_Online_3D_Video_Synthesis_with_Multi-View_Temporal_Consistency_CVPR_2025_paper.html)
- [Aether](https://openaccess.thecvf.com/content/ICCV2025/html/Zhu_Aether_Geometric-Aware_Unified_World_Modeling_ICCV_2025_paper.html)
- [What-If World](https://arxiv.org/abs/2605.27589)

**Audit disposition:** `NO_EXACT_FULL_CONTRACT_FOUND_IN_BOUNDED_PRIMARY_SOURCE_SCAN`; this is a search result with explicit limits, not a proof of absence.
