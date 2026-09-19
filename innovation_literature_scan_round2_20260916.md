# Primary-Source Innovation Scan (Round 2)

**Date:** 2026-09-16 (Asia/Shanghai)  
**Scope:** 2024-2026 conference methods relevant to long-horizon geometric consistency, memory retention/invalidation, uncertainty calibration, and causal evaluation.  
**Status:** literature-derived design guidance only. No method is validated and no novelty authorization is granted.

## Frozen questions

1. Which recent mechanisms already cover geometry-grounded memory or informative-token retention, and therefore must be explicit controls for FGB-Future/SOCF-A?
2. What uncertainty/selective-prediction mechanisms provide stronger alternatives to a source-conflict score?
3. Which falsification tests can distinguish a genuinely source-level, future-geometric signal from coverage, pose, scene identity, or model-surprise confounding?

## Verified primary sources and mechanism extraction

| Primary source | Venue/status | Mechanism actually claimed | Consequence for this project |
|---|---|---|---|
| Wu et al., *Video World Models with Long-term Spatial Memory* | NeurIPS 2025 Main Conference | A geometry-grounded long-term spatial memory with explicit storage/retrieval; custom data and evaluation target revisits and long-horizon consistency. The authors report quality, consistency, and context-length gains. [NeurIPS record](https://papers.nips.cc/paper_files/paper/2025/hash/467655d26fcc207bca08915dc91964c6-Abstract-Conference.html) | Geometry-aware memory itself is no longer a novelty claim. FGB-Future must evaluate future RGB-D/pose outcomes with this family represented as a strong control, and SOCF must isolate source-conflict/abstention rather than storage/retrieval.
| Park et al., *VideoTitans: Scalable Video Prediction with Integrated Short- and Long-term Memory* | NeurIPS 2025 Main Conference | Combines sliding-window attention, episodic memory that retains tokens using a gradient-based surprise signal, and persistent task tokens; reports compute/fidelity trade-offs and component ablations. [NeurIPS record](https://papers.nips.cc/paper_files/paper/2025/hash/905202e21386913d8eac637c2b50f590-Abstract-Conference.html) | A surprise/informativeness retention baseline is mandatory. If SOCF-A cannot beat surprise after matching coverage, pose, and FLOPs, the source-conflict claim is not supported. Include equal-token and equal-FLOP controls.
| Thiagarajan et al., *PAGER: Accurate Failure Characterization in Deep Regression Models* | ICML 2024 | Shows epistemic uncertainty alone is insufficient; combines anchored uncertainty with manifold non-conformity to organize samples into risk regimes. [PMLR record](https://proceedings.mlr.press/v235/j-thiagarajan24a.html) | A single confidence or conformal score is an incomplete comparator. Build a PAGER-style two-axis risk control where feasible (uncertainty + geometry/manifold non-conformity), then test whether source conflict adds incremental out-of-sample information. If it does not, SOCF should be downgraded to an application of existing failure detection.
| Goren et al., *Hierarchical Selective Classification* | NeurIPS 2024 | Extends selective prediction by backing off to a less-specific but still useful hierarchical output under uncertainty; formalizes risk/coverage and calibration-coverage curves, with a high-probability threshold algorithm. [NeurIPS PDF](https://proceedings.neurips.cc/paper_files/paper/2024/file/c8b100b376a7b338c84801b699935098-Paper-Conference.pdf) | SOCF abstention should not be evaluated only as binary keep/drop. Add a partial-state action (retain only low-conflict support, or emit coarse geometry) and report risk-coverage/calibration curves. A binary gate matching this partial-output control is insufficient novelty.
| Park et al., *Test-Time Adaptation for Depth Completion* | CVPR 2024 | Uses a source-trained embedding map and sparse-depth features to adapt auxiliary parameters online under domain shift; reports indoor/outdoor transfer gains. [CVPR record](https://openaccess.thecvf.com/content/CVPR2024/html/Park_Test-Time_Adaptation_for_Depth_Completion_CVPR_2024_paper.html) | Online correction can improve depth without changing memory selection. FGB-Future/SOCF must separate retrieval-only gains from test-time adaptation; otherwise a method may appear geometric while merely adapting to target statistics. Add a no-memory online-adaptation control if computationally feasible.
| Zhou et al., *Taming Teacher Forcing for Masked Autoregressive Video Generation* | CVPR 2025 | Complete Teacher Forcing conditions masked-frame training on complete observed frames, reducing train/test mismatch and improving long autoregressive generation. [CVPR record](https://openaccess.thecvf.com/content/CVPR2025/html/Zhou_Taming_Teacher_Forcing_for_Masked_Autoregressive_Video_Generation_CVPR_2025_paper.html) | Future benefit must be measured under the actual autoregressive consumer. Report teacher-forced and self-rollout conditions separately; a history score that predicts only teacher-forced loss is not evidence for long-horizon world-state consistency.
| Kang et al., *Continual Learning for Motion Prediction Model via Meta-Representation Learning and Optimal Memory Buffer Retention Strategy* | CVPR 2024 | Detects distribution shift from representation similarity between current data and memory, then updates a finite buffer; motivates non-stationary retention rather than uniform reservoir sampling. [CVPR PDF](https://openaccess.thecvf.com/content/CVPR2024/papers/Kang_Continual_Learning_for_Motion_Prediction_Model_via_Meta-Representation_Learning_and_CVPR_2024_paper.pdf) | DLV/invalidation must be compared with a representation-shift trigger and uniform/recent baselines. If DLV only detects scene/domain shift, it is not a distinct geometric invalidation mechanism.

## Mechanism-level comparison to the current candidates

### FGB-Future (evaluation/problem candidate)

FGB-Future is potentially distinct because its target is an *externally supplied, held-out future RGB-D/pose reference* under a frozen candidate pool and fixed computation budget. Existing NeurIPS 2025 work evaluates long-term consistency using geometry-grounded memory, while VideoTitans optimizes informative token retention using surprise. Therefore the contribution cannot be “memory improves consistency” or “retain informative history.” The discriminating object is a pre-registered, future-only benefit/harm label and a budget-normalized comparison across relevance, coverage, surprise, confidence, and source-conflict scores.

**Required controls:** geometry-grounded retrieval, gradient-surprise retention, pose-distance, visibility/coverage, confidence, random (fixed seeds), and recent-frame policies; teacher-forced versus self-rollout; online depth-adaptation control where available.

### SOCF-A (source-conflict abstention candidate)

PAGER establishes that uncertainty must be complemented by a non-conformity signal; HSC establishes that selective systems can preserve partial information rather than reject wholesale. SOCF-A is only potentially new if its *source-level correlated conflict* predicts future geometry errors after controlling for (i) PAGER-style uncertainty/non-conformity, (ii) overlap/visibility, (iii) gradient surprise, (iv) pose and scene identity, and (v) candidate cost. The deployable action should be source-local abstention or partial support retention, not an unexplained scalar penalty.

**Required controls:** PAGER-like two-axis risk score, HSC-like partial-output policy, surprise retention, visibility gate, and an oracle conflict mask as an upper bound (never as a deployable method).

### DLV / disagreement-weighted invalidation

CVPR 2024 continual-learning retention already uses representation similarity to detect distribution shifts and update a bounded memory. DLV must show a stricter geometric claim: repeated evidence is trusted only when reprojection/depth/visibility agreement holds, while leave-change-return events trigger stale-landmark invalidation and later re-admission after re-observation. Static scenes or one-way trajectories cannot support this claim.

### Counterfactual source intervention

Counterfactual deletion/replacement with fixed exogenous state remains a measurement protocol rather than a method. Its value is causal attribution: if replacing one source changes future geometry while all other states and random seeds are replay-identical, the source has a measurable downstream effect. The protocol must use held-out future targets and quantify replay noise before interpreting effect direction.

## New falsification matrix

| Test ID | Falsification test (pre-register before held-out access) | What a pass would mean | Kill criterion |
|---|---|---|---|
| F1 | **Surprise-versus-conflict residual test:** regress future AbsRel/pose error on VideoTitans-style surprise, pose distance, visibility/coverage, confidence, scene/trajectory fixed effects, then add SOCF conflict. Use trajectory bootstrap and held-out calibration. | Conflict carries incremental out-of-sample information beyond an established informative-token signal and geometry relevance controls. | Partial AUROC gain < 0.05 or bootstrap interval crosses zero; SOCF is no better than surprise/visibility.
| F2 | **Source-ID permutation negative control:** permute source identities within each candidate pool while retaining geometry values and timing; rerun conflict computation. | A genuine source-level mechanism should lose predictive power when identity relationships are destroyed. | Predictive power survives permutation, indicating scene/coverage leakage; kill source-level claim.
| F3 | **Temporal-shuffle control:** shuffle history order while preserving marginal frames and candidate count; evaluate future prediction. | Future benefit should depend on valid temporal/geometric relations, not only candidate composition. | Similar performance after shuffle; downgrade to set-level retrieval or kill temporal claim.
| F4 | **Partial-abstention dominance test:** compare binary keep/drop with HSC-like partial support retention at equal slots/FLOPs. | Source-local abstention should reduce tail geometry error without collapsing coverage and should beat coarse fallback. | Binary gate is matched by partial-output baseline, or abstention only raises coverage at unchanged error; no SOCF novelty.
| F5 | **Autoregressive exposure test:** evaluate teacher-forced and self-rollout consumers with identical selected memories. | A useful history score should predict/improve self-rollout future state, not only teacher-forced reconstruction. | Gain appears only under teacher forcing; restrict claim to supervised prediction or kill.
| F6 | **Leave-change-return event test for DLV:** predefine dynamic change and later re-observation; compare count-weighted, representation-shift, disagreement-weighted, and DLV invalidation. | DLV specifically reduces stale-landmark tail error while recovering after valid re-observation. | No auditable event, or representation-shift/recent baseline matches DLV; kill dynamic invalidation claim.
| F7 | **Online-adaptation separation test:** compare memory selector with and without test-time depth adaptation, holding update steps and target observations fixed. | Improvement attributable to memory policy persists after adaptation is controlled. | Selector gain disappears with adaptation control; classify as adaptation effect, not memory innovation.
| F8 | **Counterfactual replay-noise test:** repeat source deletion/replacement with fixed seed and multiple replay runs; compare intervention effect to no-op perturbation. | Effect exceeds replay noise and is spatially localized to the source support. | Effect magnitude ≤ no-op replay noise or sign unstable on most trajectories; downgrade causal protocol.

## Suggested pre-registered scorecard

Before opening held-out future GT, freeze:

- candidate pool and source IDs;
- camera intrinsics/extrinsics, coordinate convention, depth units, timestamp tolerance;
- calibration versus held-out trajectory split and future-GT isolation manifest;
- selectors and controls listed above;
- exact slot/token/FLOP/forward-step budget and random seeds;
- primary outcomes: trajectory-level future capped AbsRel, pose/reprojection error, worst-5% and CVaR tail loss, ghost-area rate, and valid-support coverage;
- secondary outcomes: partial AUROC, calibration/coverage curves, intervention effect size, and compute/latency.

Screening thresholds are not publication guarantees. A practical stop rule is: if no candidate beats the strongest control on the primary future metric with a trajectory-bootstrap lower bound above zero, preserve FGB-Future as a negative-result/evaluation contribution and do not force a method claim.

## Bottom-line research judgment (non-validated)

The literature makes the novelty boundary narrower but clearer. Geometry-grounded memory, surprise-based retention, uncertainty-plus-nonconformity risk characterization, selective partial outputs, and representation-shift buffer updates are all established mechanisms. The most defensible remaining hypothesis is conditional:

> **A source-correlated geometry conflict signal, with calibrated partial abstention, predicts and reduces held-out future geometric harm after matching surprise, pose/coverage, uncertainty, adaptation, and compute controls.**

This hypothesis is unverified. If F1/F2/F4/F5 fail, SOCF-A should be killed as a method and retained only as a diagnostic. If FGB-Future remains measurable but all selectors tie, the negative result is still scientifically useful because it tests whether retrospective geometry relevance transfers to future world-state prediction.

## References

1. Wu, T. et al. (2025). *Video World Models with Long-term Spatial Memory*. NeurIPS 2025 Main Conference. https://papers.nips.cc/paper_files/paper/2025/hash/467655d26fcc207bca08915dc91964c6-Abstract-Conference.html
2. Park, Y.-J. et al. (2025). *VideoTitans: Scalable Video Prediction with Integrated Short- and Long-term Memory*. NeurIPS 2025 Main Conference. https://papers.nips.cc/paper_files/paper/2025/hash/905202e21386913d8eac637c2b50f590-Abstract-Conference.html
3. Thiagarajan, J. J. et al. (2024). *PAGER: Accurate Failure Characterization in Deep Regression Models*. ICML 2024, PMLR 235:21069-21082. https://proceedings.mlr.press/v235/j-thiagarajan24a.html
4. Goren, S. et al. (2024). *Hierarchical Selective Classification*. NeurIPS 2024. https://proceedings.neurips.cc/paper_files/paper/2024/file/c8b100b376a7b338c84801b699935098-Paper-Conference.pdf
5. Park, H. et al. (2024). *Test-Time Adaptation for Depth Completion*. CVPR 2024. https://openaccess.thecvf.com/content/CVPR2024/html/Park_Test-Time_Adaptation_for_Depth_Completion_CVPR_2024_paper.html
6. Zhou, D. et al. (2025). *Taming Teacher Forcing for Masked Autoregressive Video Generation*. CVPR 2025. https://openaccess.thecvf.com/content/CVPR2025/html/Zhou_Taming_Teacher_Forcing_for_Masked_Autoregressive_Video_Generation_CVPR_2025_paper.html
7. Kang, J. et al. (2024). *Continual Learning for Motion Prediction Model via Meta-Representation Learning and Optimal Memory Buffer Retention Strategy*. CVPR 2024. https://openaccess.thecvf.com/content/CVPR2024/papers/Kang_Continual_Learning_for_Motion_Prediction_Model_via_Meta-Representation_Learning_and_CVPR_2024_paper.pdf

## Additional ICLR 2025 geometry controls

Two ICLR 2025 papers tighten the comparator set further:

- **LoRA3D: Low-Rank Self-Calibration of 3D Geometric Foundation Models** jointly refines multi-view point maps and reweights prediction confidence through robust global optimization, then uses calibrated confidence for pseudo-labeling and LoRA specialization. The pipeline is designed for target-scene adaptation from sparse RGB and reports evaluation on Replica, TUM, and Waymo. [ICLR record](https://proceedings.iclr.cc/paper_files/paper/2025/hash/6db7c49b14da8006892fda7350d76b6a-Abstract-Conference.html)
- **STORM: Spatio-Temporal Reconstruction Model for Large-Scale Outdoor Scenes** aggregates 3D Gaussians and self-supervised scene flows from all frames, transports them to a target time, and evaluates dynamic-region reconstruction and scene-flow accuracy. [ICLR record](https://proceedings.iclr.cc/paper_files/paper/2025/hash/7dee643a6c5abcdafee51496420c84dc-Abstract-Conference.html)

These works imply two extra safeguards. First, a confidence-calibration or target-scene adaptation baseline must be separated from memory selection when RGB-D data are used. Second, DLV claims should be restricted to auditable dynamic events with motion/flow evidence; static TUM sequences cannot establish dynamic invalidation. Neither paper validates SOCF-A or FGB-Future; they only narrow the space of plausible controls.

Addendum references:

8. Lu, Z. et al. (2025). *LoRA3D: Low-Rank Self-Calibration of 3D Geometric Foundation Models*. ICLR 2025. https://proceedings.iclr.cc/paper_files/paper/2025/hash/6db7c49b14da8006892fda7350d76b6a-Abstract-Conference.html
9. Yang, J. et al. (2025). *STORM: Spatio-Temporal Reconstruction Model for Large-Scale Outdoor Scenes*. ICLR 2025. https://proceedings.iclr.cc/paper_files/paper/2025/hash/7dee643a6c5abcdafee51496420c84dc-Abstract-Conference.html
