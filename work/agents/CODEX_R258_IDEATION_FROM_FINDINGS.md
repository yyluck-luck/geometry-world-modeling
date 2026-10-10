# R258 — Ideation from the measured failures

Workspace: local Mac checkout, verified as MacBook-Pro-M3-MAX.local. Date: 2026-10-10. This is a repository-grounded ideation review, not a new GPU experiment.

**Run source-fitted multiscale residual fusion first.** Use predictions of withheld, already observed bank images to decide which generated corrections to trust at future cameras. Retain a second experiment on geometry-targeted bank replay into LoRA weights. Do not spend the next trial on ordinary best-of-four selection: the archived scores already put a restrictive ceiling on that route.

The proposed contributions are **UNVERIFIED**. Generic frequency fusion, geometry-based sample selection, and scene-specific LoRA all have close published precedents. The potential contribution is narrower: learning the *signed usefulness* of a correction from permissible scene observations, or specifically storing appearance absent from immediate context. Neither has been demonstrated here. Keep **new_method_validated=false; novelty_authorization=NONE**.

Only this file is authored by R258. No GPU, training, model inference, weight/dataset download, SSH, cluster query, submission, or external contact was performed. Three read-only sub-agents checked overlapping literature and implementation questions; this is team-assisted review, not independent experimental replication. S141's remote adapters, completed steps, caches, and outcomes were not verified, and neither retained experiment depends on its result.

Evidence notation throughout: **MEASURED (archived)** = prior experiment's saved measurements; **DERIVED** = arithmetic on inspected records; **ANALYTICAL** = proposed mechanism, threshold, recipe, or budget; **UNVERIFIED** = unavailable evidence or an untested explanation. All future numbers are ANALYTICAL unless explicitly stated otherwise. Source citations are repository-relative file:line references. Links to result files identify measurement provenance. Exact substantive CPU commands and complete outputs are in Appendices A–B.

## 1. What the findings actually suggest

| Evidence | Verified scope | Method implication, not an established result |
|---|---|---|
| **MEASURED (archived):** the retrieved-view warp beats the recent-view warp by **+1.46 dB**, while generated memory-minus-recent is **−0.181 dB**. | Same selected contexts, different consumers; one chess scene. [S139 baseline contrasts](../S139_crossseq_revisit/results/S139_BASELINE_CONTRASTS.json), [S139 generation analysis](../S139_crossseq_revisit/results/S139_ANALYSIS.json); interpretation at work/S139_crossseq_revisit/RESULT.md:17–51. | Move useful evidence into a route whose benefit can be tested directly: output correction, independent verification, or fast weights. This does not prove retrieval is optimal or generation is invariant to memory. |
| **MEASURED (archived):** on chess, warp PSNR **14.57** exceeds VMem **11.36**, but warp SSIM **0.432** is below VMem **0.470**. | Aggregate metric ordering; not a measured decomposition into correct geometry and correct texture. [S140 confirmation analysis](../S140_warp_guided/results/CONFIRM_ANALYSIS.json); work/S140_warp_guided/RESULT.md:20–41. | Test residual covariance and multiscale fusion. Do **not** assume the generator's high frequencies are correct merely because SSIM is higher. |
| **MEASURED (archived):** WGS-minus-warp is **+0.244 dB covered**, **−0.241 dB uncovered**, but only **+0.020 dB overall** on the eight-seed chess panel. | Masks mean covered/uncovered by this estimated warp. They do not certify observed/disoccluded scene content. [S140 confirmation scores](../S140_warp_guided/results/confirm_tacc/S140_SCORES_confirm_tacc.json), [analysis](../S140_warp_guided/results/CONFIRM_ANALYSIS.json); work/S140_warp_guided/RESULT.md:24–37. | A useful correction may exist even when the complete generated image loses. Learn whether a correction helps; do not default to letting generation fill every hole. |
| **MEASURED (archived):** target-pose warped context gives approximately zero added PSNR; the naive warp-covered/generator-hole hybrid loses about **1.3 dB** on the development panel. | A copying-compatible outcome, not proof of pixel identity. [S137c analysis](../S137_geometry_baselines/results_c/S137C_ANALYSIS.json); work/S137_geometry_baselines/RESULT.md:40–55; the qualification is explicit in work/agents/CODEX_R256_S142_DRAFT_REJECTION.md:39–40. | Canonicalizing coordinates can remove transport difficulty, but a useful method must add something beyond copying and nearest fill. |
| **MEASURED (archived):** KPS improves a downstream warp by about **1.75 dB** over the threshold repair. | Better estimated geometry in the tested configuration, not perfect depth or an independently established scale-estimation novelty claim. [S137 corrected-map summary](../S137_geometry_baselines/SUMMARY_s136ref_v2map.json); docs/report/TECHNICAL_REPORT_20261010.md:90–107. | Geometry can support a fallible verifier or reliability feature; it should not be treated as exact target supervision. |

Two implementation facts matter. WGS replaces **latent** blocks using pooled coverage, then decodes them; it does not clamp every covered RGB pixel exactly (work/S140_warp_guided/gen_s140.py:155–179,199–206). The scorer uses the original RGB-resolution validity mask and pooled squared error across the target frames (work/S140_warp_guided/score_s140.py:30–50). A latent intervention and an RGB fusion rule therefore have different attainable outputs.

The brief's asset list also needs qualification. The manifest contains **DERIVED: 2,000 training plus 32 monitor clips**, not 2,032 training clips (Appendix B; work/S141_finetune/train_s141.py:27). This review verified source code and that manifest, not the remote completeness of the stated frame caches or final adapters. The local directories inspected contain warp arrays and score records but no generation RGB arrays; Appendix B records the exact scope. Consequently no frequency-error analysis, fusion SSIM, or image-level oracle is claimed.

### A new, cheap headroom check

The following are **DERIVED from the archived RTX 3090 seed block {3,4,5,6}**, not new image predictions. Each seed produces an entire four-target clip; selecting a seed selects the whole clip. The random-selection baseline is the expected score under uniformly choosing one of those four seeds, not their image average. Source: [S140 WGS scores](../S140_warp_guided/results/confirm_tacc/S140_SCORES_confirm_tacc.json), [matched VMem scores](../S140_warp_guided/results/confirm_tacc/S139_VMEM_SSIM_tacc.json), exact calculation in [Appendix A](#appendix-a--cpu-headroom-calculation).

| Restricted operation | Mean PSNR or gain |
|---|---:|
| VMem, expected random seed | 11.274894 dB |
| VMem, ground-truth oracle best of four | 11.713744 dB |
| That VMem oracle minus warp | **−2.858644 dB** |
| WGS, expected random seed | 14.568249 dB |
| WGS, ground-truth oracle best of four | 14.773982 dB |
| WGS oracle headroom over random seed | +0.205733 dB |
| WGS oracle minus warp | **+0.201594 dB** |
| Fixed RGB composite: WGS covered, warp uncovered, minus warp | **+0.122799 dB**, descriptive window-bootstrap interval **[+0.093323,+0.149847]**, positive in **23/24** windows |
| Ground-truth oracle choosing WGS or warp separately for each of the two whole regions, averaged over seeds, minus warp | **+0.193955 dB** |

The fixed composite PSNR is reconstructible without images: convert each stored regional PSNR to normalized MSE, weight by its pixel fraction, add, and convert back. Reconstructing the original WGS PSNR from its two regions agrees within **DERIVED: 3.56×10^-15 dB** (Appendix A). Fusion SSIM cannot be recovered this way because its local neighborhoods cross the composite boundary.

These calculations change the ranking:

- Choosing among the existing four raw VMem clips cannot make them competitive with the warp under PSNR, even with target access.
- Choosing among four WGS clips could help relative to random selection, but its *oracle* only just reaches the existing gain bar over warp. A blind verifier has little margin. This does not rule out a different candidate generator, more samples, or a perceptual objective.
- The fixed paste is a mandatory strong baseline for the first experiment. Its advantage is a new exploratory arithmetic finding on an already exposed panel, not a confirmed new method.
- The two-region oracle is an upper bound **only for that binary region-switching family**. It does not bound continuous blending, frequency-dependent residuals, or pixelwise switching. Those families need their own development-only headroom check.

## 2. Divergence: sixteen distinct intervention ideas

All entries below are ANALYTICAL proposals. “Keep” means a bounded experiment is specified later, not that novelty or performance is established. The five marked **P1–P5** receive the detailed prior-art check in §3.

| # | Point in pipeline | Idea and connection to the findings | What would make it substantive; cheapest falsifier |
|---|---|---|---|
| **1 / P1** | Output estimator | **Source-fitted multiscale residual fusion.** Predict withheld bank views; fit how much of each generated-minus-warp frequency component to retain, separately for covered/uncovered pixels. | Bank-specific coefficients must beat an equally expressive global fusion rule and simple smoothing. If the global rule matches it, keep the baseline and reject the adaptive-memory claim. **Keep first.** |
| **2 / P2** | Parameter memory | **Geometry-targeted bank replay.** Store historical appearance in LoRA, emphasizing pseudo-target regions supported by donor bank views but missing from that episode's immediate context. | With runtime context fixed, outperform equal-step ordinary bank LoRA and a mask-shuffled control. Generic scene personalization is already published. **Keep second.** |
| **3 / P3** | Sample acceptance | **Withheld-witness verification.** Score complete generated clips against independently withheld observed bank views projected into target cameras; abstain when support is weak. | Must beat ordinary conditioning-warp agreement and exhibit useful ranking headroom. Existing four-seed ceilings and direct prior art demote it. |
| **4** | Joint output selection | **Trajectory-consistent seed assignment.** Choose seed identities jointly across successive clips by source-geometry correspondence costs, avoiding independent frame switches. | Gains must survive a whole-clip medoid/mean control and a held-out temporal metric. Current short panels do not validate long-rollout consistency; defer. This optimizes cross-clip coherence, unlike #3's reference fidelity. |
| **5** | Deterministic output baseline | **Reverse the usual hole-filling assignment.** Use WGS only on covered pixels and retain nearest fill in uncovered pixels. | Directly follows the regional sign reversal. The derived gain is below the project bar and the operation is simple compositing. Include as a control, not a method claim. |
| **6 / P4** | Retrieval objective | **Predict marginal reprojection error reduction.** Score whether adding a view improves a source-held-out reconstruction, rather than counting projected pixels or minimizing pose distance. | Must beat marginal-coverage selection and improve the final consumer, not only the warp. Generic selector tuning is a retired project line; this audit does not reopen it. |
| **7 / P5** | Sampling operator | **Uncertainty-weighted observation projection.** Restrict denoising corrections along directions contradicted by reliable projected observations; allow freedom elsewhere. | Must outperform S140 at identical sampling cost and remain robust to erroneous geometry. Null-space consistency and NVS guidance are established; estimating the observation-error model is the unresolved part. |
| **8** | Geometric estimation | **Propagate scale uncertainty into appearance.** Use the KPS residual profile to render a small fixed scale ensemble; identify pixels whose appearance is stable across plausible scales. | Must beat the single KPS estimate and a constant depth-jitter ensemble. A sharp residual minimum is not automatically a calibrated scale posterior; first inspect source-only uncertainty versus held-out warp error. |
| **9** | Visibility representation | **Retain a second depth layer.** Preserve multiple source-supported surfaces where the front layer becomes invalid, instead of filling every gap by 2D nearest neighbor. | Must beat a multi-source z-buffer plus a better deterministic fill at equal inputs. Requires evidence that missing layers, rather than erroneous depth or crop mapping, dominate failures. |
| **10** | Attention address | **Transport source features to target coordinates before TimeMix.** Make the easy same-location path carry matched scene content, with a fallback where correspondence is uncertain. | Must beat the same parameter budget spent on ordinary adaptation and RGB warp conditioning. New attention machinery is a larger engineering risk; not one of the two short trials. Existing conditioning mechanics are at data/S134_tacc/vmem_src/modeling/modules/transformer.py:146–155. |
| **11** | Training objective | **Counterfactual useful-memory margin.** On training clips, require the correct historical evidence to reduce error more than a matched wrong-bank alternative, only on source-supported regions. | Must beat ordinary denoising plus the same extra data/compute. A contrastive loss can learn scene identity or generic corruption detection without improving future prediction. |
| **12** | Training target representation | **Learn a small residual restorer around a fixed warp.** Predict residual RGB/latent corrections directly, keeping the warp as an explicit skip connection. | Compare with a tiny non-generative restoration network, VAE round-trip, and ordinary smoothing. If those match it, diffusion is unnecessary. This changes the prediction problem, unlike #1's fusion of existing outputs. |
| **13** | Noise schedule | **Allocate denoising effort by support reliability.** Spend additional updates on uncertain spatial regions while preserving the global camera-conditioned trajectory. | Must beat a uniform lower-cost sampler at equal network evaluations, including seams and temporal artifacts. Existing loops update all latent positions together (work/S140_warp_guided/gen_s140.py:174–179); this is new implementation work, not a free mask change. |
| **14** | Decoder correction | **Estimate the VAE contribution explicitly.** Model the warp-to-VAE-round-trip residual and subtract only source-validated decoder bias before invoking generative correction. | If the apparent covered-region improvement is matched by VAE round-trip or denoising alone, use that cheaper predictor. Useful diagnosis; no decoder-calibration novelty established. |
| **15** | Memory representation | **Canonical target-view patch memory.** Cache pose-indexed, source-attributed warped patches, then retrieve aligned patches rather than entire displaced frames. | Must beat direct multi-view rendering and the trained warp-context package, without hiding new images in a larger token budget. Not synonymous with S142, which replaces the complete context input package (work/S142_followup/PROTOCOL.md:34–46). |
| **16** | Budget allocation | **Selective computation with warp fallback.** Predict from source-only tests whether a query merits generation, adaptation, or only deterministic warp. | Must improve the quality–compute curve over a fixed generation schedule and coverage threshold. A useful scheduler would be a systems result; it does not establish a novel scene-generation mechanism. |

The hidden assumption worth attacking is that all useful memory must pass through a small set of runtime context frames. There are at least three alternatives: memory can supervise a correction policy, verify proposals, or update temporary weights. These are research directions, not claims that those categories are new.

## 3. Prior-art check for the five strongest starting candidates

The IDs and exact titles below were checked on arxiv.org in this run, with full-text method sections inspected. “Already published” here includes a public arXiv preprint; it does not assert peer-review status. Search coverage is bounded, and an unlocated exact combination is not proof of novelty. Queries included scene/test-time LoRA for NVS and world models, reference-grounded diffusion candidate selection, frequency fusion, geometry-confidence gating, null-space restoration, and visibility/utility retrieval.

### P1. Source-fitted multiscale residual fusion

**Closest mechanism:** arXiv:2603.14965, **“GeoNVS: Geometry Grounded Video Diffusion for Novel View Synthesis,” §3.2, Eqs. (8)–(9), §3.3**. It learns a spatial residual gate between geometry-derived and diffusion features. That rules out presenting adaptive geometry/generation fusion as new. [Record](https://arxiv.org/abs/2603.14965), [method](https://arxiv.org/html/2603.14965v1#S3.SS2).

**Closest frequency operation:** arXiv:2108.02938, **“ILVR: Conditioning Method for Denoising Diffusion Probabilistic Models,” §3.1, Eq. (8), Algorithm 1**. It replaces low-frequency proposal content with reference content during diffusion. A final RGB warp/generator blend differs in placement, but the low/high-frequency principle is established. [Record](https://arxiv.org/abs/2108.02938), [method](https://arxiv.org/html/2108.02938v1).

**Precise proposed difference:** a frozen generator; a small output-space estimator of *signed reconstruction improvement*; parameters fitted anew from held-out predictions of the allowed scene bank; shrinkage to a global estimator and source-only accept/fallback. The bank supplies calibration labels, not just conditioning features. This is more specific than “uncertainty-aware fusion,” and differs from R255's global learned pixel gate (work/agents/CODEX_R255_IDEATION_AFTER_S141.md:70–78).

**Novelty risk:** high. Empirical model combination and source self-validation are ordinary tools. The contribution would require transferable prediction of useful corrections and gains beyond identical global coefficients, not simply an unfamiliar combination of familiar components. No formal calibration or risk guarantee is proposed.

### P2. Geometry-targeted bank replay into weights

**Closest world-model precedent:** arXiv:2610.04920, **“PWM: Personalized World Models with Online Reinforcement Learning,” §§3.2–3.3, 5.2–5.3**. It adapts a scene-specific LoRA from a support trajectory, evaluates held-out continuation, and includes matched supervised adaptation. “Scene memory in weights instead of context” is therefore already published. Its arXiv submission precedes this brief. [Record](https://arxiv.org/abs/2610.04920), [method](https://arxiv.org/html/2610.04920v1).

**Closest geometric self-supervision:** arXiv:2507.12646, **“Reconstruct, Inpaint, Test-Time Finetune: Dynamic Novel-view Synthesis from Monocular Videos,” §§3.2–3.3**. CogNVS constructs geometry-structured masked/source pairs and adapts a video diffusion model on the input video. Source-only adaptation plus geometry-structured hiding is already established. [Record](https://arxiv.org/abs/2507.12646), [method](https://arxiv.org/html/2507.12646v2#S3.SS2).

**Additional direct collision:** arXiv:2609.23436, **“GAPS: Generative Active Pseudo-view Selection for Sparse-View 3D Gaussian Splatting,” §3.3** explicitly uses scene-specific LoRA memory fitted to observed images together with geometric conditioning. Its downstream task is Gaussian reconstruction, but the broad memory mechanism is not available for a new claim. [Record](https://arxiv.org/abs/2609.23436), [method](https://arxiv.org/html/2609.23436v1#S3.SS3).

**Precise proposed difference:** train the temporary weights specifically on *historically supported content missing from the current four-view context*, and evaluate with the same runtime static context so history can enter only through the adapter. The target is conditional scene recall, not generic style/domain adaptation. A matched plain bank-LoRA arm and area-matched mask control must isolate this difference.

**Novelty risk:** high. A coverage-weighted loss alone is unlikely to be a strong paper contribution. Retain it as a falsifiable candidate because it tests a materially different memory route from S141/S142, not because LoRA personalization is new.

### P3. Withheld-witness selection across seeds

**Closest work:** arXiv:2604.04576, **“PR-IQA: Partial-Reference Image Quality Assessment for Diffusion-Based Novel View Synthesis,” §§3.2–3.4 and §4**. It obtains partial quality maps by geometrically aligning observed-reference features with generated views, completes those maps, and explicitly selects among multiple diffusion candidates using reference-based scores. Generic “warp as a verifier” and target-GT-free best-of-N NVS are already published. [Record](https://arxiv.org/abs/2604.04576), [candidate selection](https://arxiv.org/html/2604.04576v1#S4).

A second direct precedent is arXiv:2309.16668, **“RealFill: Reference-Driven Generation for Authentic Image Completion,” §3.4, “Correspondence-Based Seed Selection.”** It ranks generated completions by matches to reference images. [Record](https://arxiv.org/abs/2309.16668), [method](https://arxiv.org/html/2309.16668v1).

**Precise proposed difference:** withhold witness frames from generation, estimate geometry from observations alone, freeze it across candidates, and abstain outside trustworthy witness support rather than infer whole-image correctness. Disjoint frames are not statistically independent: adjacent views and common geometry errors still correlate.

**Decision:** not a retained execution experiment for the current four-seed pool. Appendix A shows weak practical headroom, while PR-IQA establishes close overlap. If a future, already completed generator supplies a materially different candidate pool, reassess its ceiling once; do not enlarge N or change the objective after a failed frozen test. A plain warp-agreement selector remains a useful baseline.

### P4. Retrieval by predicted reprojection utility

**Closest retrieval objective:** arXiv:2602.14941, **“AnchorWeave: World-Consistent Video Generation with Retrieved Local Spatial Memories,” §3.3 and Appendix B** greedily selects memories adding visible target coverage. Marginal coverage retrieval is already published. [Record](https://arxiv.org/abs/2602.14941), [method](https://arxiv.org/html/2602.14941v1#S3.SS3).

arXiv:2506.18903, **“VMem: Consistent Interactive Video Scene Generation with Surfel-Indexed View Memory,” §3.1**, already uses target-visible surfels to identify memory views. arXiv:2604.19747, **“AnyRecon: Arbitrary-View 3D Reconstruction with Video Diffusion Model,” §3.4**, also attributes visible points to reference views for selection. [VMem record](https://arxiv.org/abs/2506.18903), [VMem method](https://arxiv.org/html/2506.18903v3#S3.SS1); [AnyRecon record](https://arxiv.org/abs/2604.19747), [AnyRecon method](https://arxiv.org/html/2604.19747v1#S3.SS4).

**Precise proposed difference:** estimate *reduction in reprojection error*, accounting for reliability and redundancy, from source-held-out prediction tasks. Coverage alone cannot measure incorrect color, depth, or magnification. But this difference is only useful if it beats coverage retrieval and changes downstream prediction quality.

**Decision:** do not reopen the retired generic-selector line (CURRENT_STATUS.md:72–74). S139 already demonstrates useful retrieved evidence; improving its upstream score need not repair consumption. This is a legitimate divergent idea that does not survive the resource/novelty ranking.

### P5. Observation-preserving or null-space denoising

**Closest mathematical mechanism:** arXiv:2212.00490, **“Zero-Shot Image Restoration Using Denoising Diffusion Null-Space Model,” §3.1, Eqs. (9), (13), and §3.3**. DDNM uses range/null-space decomposition for known linear observations and provides a noisy-observation extension. Preserving measured components while generating the complement is established. [Record](https://arxiv.org/abs/2212.00490), [method](https://arxiv.org/html/2212.00490v1#S3.SS1).

**Closer NVS application:** arXiv:2405.15364, **“NVS-Solver: Video Diffusion Model as Zero-Shot Novel View Synthesizer,” §§4.1–4.3**, uses warped observations to guide denoising/posterior sampling. [Record](https://arxiv.org/abs/2405.15364), [method](https://arxiv.org/html/2405.15364v2).

**Precise proposed difference:** estimate a source-conditioned error model for unreliable geometric constraints, rather than enforce the full CUT3R warp as an observation. However, source visibility, estimated depth and nearest-filled pixels do not satisfy an exact known linear observation equation for the true target. A masked warp is a fallible predictor.

**Decision:** defer. The unimplemented uncertainty model is the meaningful part, and P1 tests its essential question with fewer moving parts. Calling S140 a failed null-space theorem or treating exact clamping as a new mechanism would both be wrong.

## 4. Convergence: two concrete experiments

This is a new generative brief. R255's preference to write up and S142's conditional stopping policy are management decisions, not evidence that new mechanisms are impossible. These proposals do not alter S141/S142's frozen arms or outputs; any execution belongs in a new dated stage protocol. None is executed by this review.

### Shared evidence contract

- Use original VMem and fixed S140 WGS initially. S141 A/B can later be separate comparators after their actual checkpoints and outputs are verified; do not assume either wins.
- Preserve original target cameras, context identities, preprocessing, source/weight hashes, scorer, and same-hardware generation seeds. Existing sampler/adapter entry points are work/S140_warp_guided/gen_s140.py:109–127,139–180 and work/S141_finetune/gen_s141.py:134–154,169–198.
- At final evaluation use chess windows and seeds **3–6**, with the original coverage masks. Aggregate four-target pooled RGB SSE into clip PSNR, then average seed scores within each window. Do not average image outputs unless that is a separately named baseline. The score contract is work/S140_warp_guided/score_s140.py:30–50.
- Report a fixed **10,000-replicate window bootstrap**, all three history/current-pair means, and descriptive pair-cluster uncertainty. There are only three history-bank adaptation units, not twenty-four independent scenes. A confidence interval over windows is not a population claim.
- Chess is held out from S141 global training but exposed to method development; RGB-D Scenes 13/14 are exposed too (work/S141_finetune/PROTOCOL.md:93–99; docs/report/TECHNICAL_REPORT_20261010.md:184–192). Neither becomes untouched merely because a new protocol is written.
- Query RGB/depth must be unavailable to predictors and bank adaptation. Known bank RGB may serve as pseudo-target supervision. Exclude a pseudo-target from its own conditioning, geometry reconstruction/state, retrieval evidence and VAE/CLIP inference inputs. Raw query poses remain permitted.
- No primary can be replaced by covered-only PSNR, SSIM, a favorable pair, or training loss after results arrive. Frame PSNR/SSIM do not establish better temporal video.
- Record actual preparation/adaptation/generation latency, including amortization across bank reuse. GPU-hours below are planning estimates, not measured future runtimes.

### Experiment 1 — Source-fitted multiscale residual fusion

**Question and hypothesis.** Can predictions of already observed history estimate which generated corrections improve an unseen query? Specifically, source-fitted multiscale coefficients should outperform equally expressive coefficients fitted globally, because the covered/uncovered error pattern varies by scene. That last causal explanation is UNVERIFIED.

**Estimator.** Let W be the nearest-filled B2 warp, G the fixed S140 W2, strength 0.5 output, and M the original RGB validity mask. Use float RGB in [0,1], reflect-padded Gaussian filters L2 and L8 with fixed standard deviations of 2 and 8 RGB pixels. Define P0=L8, P1=L2−L8, P2=I−L2. Fit six coefficients in [0,1]:

    F = clip[ W + sum_b {M*a_covered,b + (1-M)*a_uncovered,b} P_b(G-W), 0, 1 ].

This does not assume that generated high frequencies are useful: any coefficient can go to zero. The filters are not orthogonal, and spatial masks mix their frequencies. Fit against the complete reconstructed RGB error, including cross terms; do not independently minimize each band's MSE and claim an optimum for the final image. The output is a composite predictor, not evidence that the frozen generator internally learned to consume memory.

**Global fitting and a fixed development gate.**

1. Select the lowest five training-clip IDs in each of the six-scene × static/memory strata: **60 S141 training clips**, excluding monitor targets. Preserve each existing clip's source/target contract. Generate G with seeds 3 and 4 and reuse its corresponding W. These are new predictions, not already cached just because the latent cache exists.
2. Fit the global six-coefficient rule and every learned trivial baseline on those clips, weighting clips equally. Use all **32 fixed S141 monitor clips**, seeds 3 and 4, once for selection of the strongest trivial baseline B*. Freeze the baseline menu and tie-break toward the simpler rule before generation.
3. Before constructing chess bank calibration outputs, compute development-only family oracle fits using monitor GT for *diagnosis only*, never for deployable coefficients. Stop if the proposed fusion family cannot reach +0.2 dB above B* on that monitor panel. A pass establishes headroom only; it does not validate the bank predictor. Report the test as an optimistic spending gate.

The clip split is explicit in work/S141_finetune/PROTOCOL.md:17–31 and work/S141_finetune/train_s141.py:27–38. Verify the selected-stratum counts in the future implementation instead of silently reducing them.

**Bank fitting without query labels.**

For each of the three permitted twenty-frame historical traversals H, sort the permitted refs. Use bank indices **{0,5,10,15}** as the fitting pseudo-target clip, **{2,7,12,17}** as a validation pseudo-target clip, and the remaining twelve as the donor bank. Exclude all eight pseudo-targets from **both** clips' source reconstruction and generation. Select four donor contexts with the smallest mean distance to the four pseudo-target cameras, using rotation geodesic angle in radians plus 0.1 times Euclidean camera-center distance in dataset meters, computed in float64 with a clipped arccos argument, and lexical ref tie-breaking. Keep the real camera poses; convert to GL only through the existing conditioning convention. This is the frozen proposed selector, not a claim of exact equivalence to VMem retrieval. All geometry is recomputed from those allowed source contexts with KPS; no persistent state containing held-out images is reused.

Generate each pseudo-clip with seeds 3 and 4. Fit bank coefficients on the first clip's known RGB with normalized mean RGB MSE plus **0.001 times the squared distance to the global six-vector**. A coefficient vector is accepted only if, on the second pseudo-clip averaged over the two seeds, it improves global-fusion PSNR by **at least 0.05 dB** and SSIM declines by **no more than 0.005**. Otherwise use the global vector. There is one vector/fallback decision per history bank, frozen before any final query score. This is an empirical adaptation policy, not a calibrated-probability guarantee.

The historical bank is common to eight current windows, so it can be reused without reading their future RGB (work/S139_crossseq_revisit/PROTOCOL.md:19–22,57–59). The pseudo-clips span larger viewpoint changes than the final target clips; that distribution mismatch is disclosed, not tuned away after failure.

For RGB-D Scenes 13/14, evaluate **global coefficients only** on their original inputs. Their existing panel does not have this twenty-frame history-bank contract. That secondary block tests global fusion transfer, not transfer of the complete bank-adaptation policy.

**Minimal implementation: proposed new files only.**

In a newly allocated stage directory, add:
- build_source_holdouts.py: exact source/pseudo-target manifests and disjointness checks;
- fit_residual_fusion.py: six-parameter constrained fitting, fixed comparator menu and source-only fallback;
- apply_residual_fusion.py: receipt-matched composition and deterministic wrong-bank controls;
- analyze_fusion.py: paired contrasts using the existing score contract.

Reuse the sampler behavior at work/S140_warp_guided/gen_s140.py:139–180 and rendering logic at work/S141_finetune/warps_s141.py:44–66,79–97. Do not import the executable scripts blindly: they contain top-level model loading/output work (gen_s140.py:85–93,182–185; warps_s141.py:73–101). Reuse/refactor the needed pure functions only in the new stage. No changes to frozen source scripts are required.

The present warp cache stores filled RGB, validity, latent and pooled coverage, not contributor-count or per-source disagreement maps (work/S141_finetune/warps_s141.py:91–99). Accordingly those uncomputed features are excluded from this minimal experiment.

**Primary contrast and required threshold.**

Primary: bank-policy F minus the development-selected strongest trivial predictor B*, mean window PSNR **≥+0.2 dB**, lower descriptive window-bootstrap bound **>0**, and no negative mean in two of the three sequence pairs. Also require F−W **≥+0.2 dB** and no mean SSIM decline exceeding **0.01** against either comparator.

For the *source-fitted adaptation mechanism* claim, additionally require F minus global six-coefficient fusion **≥+0.2 dB**, lower interval bound >0. If only the overall fusion criterion passes, report improved fusion and reject the claimed value of scene-specific fitting. Also require the same gain and SSIM criteria against the equally informed multi-source warp defined below; otherwise the extra bank images have a simpler, competitive use.

**Controls, with the strongest trivial baseline included.**

The fixed B* menu is: W; G; the derived covered-G/uncovered-W paste; globally fitted constant alpha; globally fitted two-region alphas; the fixed L8(W)+(I−L8)(G) composite; the global six-coefficient rule; and fixed sigma-1 Gaussian/3×3 median smoothing of W. Report VAE round-trip W as a separate decoder control, included in B* if generated before monitor selection. Every candidate is clipped/scored identically.

Add equally informed deterministic controls on chess: nearest-view copy and a KPS multi-source warp over the unique union of **H and the original four query-conditioning references**, with the same target cameras, plus fixed sigma-1 smoothing of that warp. Final-query geometry may use all those allowed observations, but its cache is separate from the strictly excluded pseudo-target calibration caches. Require the candidate to exceed these controls under the stated criteria; extra history cannot be credited to a clever coefficient fit if direct rendering uses it as well.

Also use both cyclic permutations of the three bank policies, averaging their **scores**, not images. Compare accepted vectors and fallback decisions separately; exchanging policies changes both. All three traversals observe the same chess room (work/S139_crossseq_revisit/PROTOCOL.md:17–21), so matching swapped policies can reflect valid shared scene information. This only limits traversal-specific attribution; it does not automatically refute source fitting or scene adaptation. A simple, well-tuned global combination and the equally informed renderer are the principal opponents, not raw VMem.

**Kill criteria.**

Stop for failed development headroom, non-finite fitting, a source/query boundary violation, all three banks falling back to global, or a final primary miss. If the global rule or equally informed deterministic controls explain the gain, keep the simpler predictor and abandon this adaptive-memory claim. Interpret same-room bank swapping as the limited attribution control described above. Do not change filter scales, ridge, pseudo-target split or thresholds on chess. Failure of this small policy does not refute every possible reliability estimator.

**Budget and 1–2-day execution.**

New generation count is **ANALYTICAL: 60×2 + 32×2 + 3×2×2 + 16×4 = 260 clips**, assuming the final chess WGS outputs are reusable after receipt matching; the last term regenerates the RGB-D transfer block on RTX 3090 seeds 3–6. Archived base-generation timing gives about **DERIVED/ANALYTICAL: 2.61 baseline-equivalent GPU-hours** for those calls; WGS, geometry, encoding and contention can differ. Allow **4–8 RTX 3090 GPU-hours total**, summed across cards, with a hard cap of **8**, plus CPU fitting/scoring. The cap includes source-only depth preparation for the equally informed multi-source renderer; measure that preparation before committing the remaining budget. If reused output arrays are inaccessible or required preparation cannot fit the cap, stop and report that resource dependency; do not claim a zero-cost trial. One day for manifests/compositor and a small timing check, one day for the fixed run is plausible, not guaranteed.

**A genuinely interesting result.** Source-only fitting predicts beneficial corrections on future views, exceeds global/region/frequency/smoothing controls, and avoids transferring the adverse uncovered-region effect. It would justify a candidate method built around empirical scene-specific correction reliability. A gain reproduced by constant alpha is a useful baseline, not that contribution.

### Experiment 2 — Store context-missing historical appearance in temporary weights

**Question and hypothesis.** Can a small adapter retain factual historical appearance that the four runtime contexts do not supply? The method candidate is a geometry-targeted replay loss; plain bank adaptation is its strongest matched control.

**Scope and inputs.** Start from original VMem, not a pending S141 checkpoint. Train three independent adapters, one for each permitted H traversal, using only its twenty refs. Reuse each adapter across that pair's current windows, with the **unchanged static_recent runtime context** for the primary. Do not train a single chess adapter from the union of all window banks: a later window's recent frames can expose an earlier query's future. The permitted frames and target exclusion are at work/S139_crossseq_revisit/PROTOCOL.md:19–22,33–38,57–59.

**Minimal replay construction.**

Create a fixed **64-episode** manifest per H with seed 258. Each episode has disjoint sets S (four context images), T (four real bank images used as supervised pseudo-targets), and D (the other twelve observed donor images). Preserve actual cameras; no fake camera offsets. Build geometry from S and D with T excluded from every reconstruction call/state. At each T camera compute a visibility-support mask:

    U = support(D -> T) AND NOT support(S -> T).

U is estimated donor support missing from immediate context, not certified visibility. Pool it to the latent grid. Let e be squared target epsilon prediction error. Use:

    loss = mean(e on all target latent values)
           + sum(U * e) / max(sum(U broadcast across channels), 1).

The additional term is zero for an empty mask. Record empty-mask episodes and the mask-area distribution. This targets memory-dependent appearance while retaining the ordinary full-frame objective; it does not provide target RGB at query time. Donor RGB is available to the adapter through other replay episodes and its bank-target supervision, not secretly concatenated into that episode's four conditioning slots.

Fix rank/alpha **16**, **1,000 steps**, learning rate **1e-5**, **100-step warm-up**, seed **0**, final checkpoint only. Keep S141's noise schedule, ordinary conditional-drop behavior and base freezing. Loss weighting is the intended intervention; do not simultaneously change the sampler or add a warp branch. Existing primitives: work/S141_finetune/s141_common.py:82–94,109–126; work/S141_finetune/train_s141.py:54–68,115–121. The objective is a proposal, not present in that trainer.

**Four equal-budget training arms.**

1. Ordinary bank replay, full-frame epsilon MSE.
2. The proposed donor-supported/missing-context weighting.
3. Same weighted objective with U's flattened pixels permuted by a frozen per-episode permutation, preserving area. This controls extra gradient weight and sparse supervision without correct spatial placement.
4. The same normalized weighted loss with **U0 = NOT support(S at T)**, ignoring donor support. This is the strongest trivial weighting control: otherwise the proposed benefit could be ordinary emphasis on poorly covered pixels rather than learning specifically from historical support.

Use identical episodes, noise draws, optimizer steps and initial LoRA for all arms. Each has three bank adapters. Do not select the best checkpoint or mask magnitude by query scores. A validation-loss reduction is only an optimization diagnostic.

**Minimal implementation: proposed new files only.**

Add bank_manifest.py, train_bank_replay.py, gen_bank_replay.py and analyze_bank_replay.py in a new stage. Cache source-only masks and bank VAE/CLIP once. Reuse s141_common's base/adapter/conditioning code. The stock trainer deliberately asserts that scenes belong to its training-scene allowlist (work/S141_finetune/train_s141.py:27–34); do not weaken that protection. The new trainer must require the exact per-bank reference allowlist. The existing generator loads one adapter before jobs (work/S141_finetune/gen_s141.py:114–125,158–190); the new path must reset to the same base and load the adapter identified by H, with no optimizer or adapter state carried across banks.

**Primary contrast and scientific hurdle.**

Primary: weighted-bank adapter with static runtime contexts minus **ordinary bank-LoRA with those identical contexts**, mean PSNR **≥+0.2 dB**, lower descriptive window-bootstrap bound >0, and no negative pair mean in two of three pairs. Also require ≥+0.2 dB over the area-shuffled weighting, donor-agnostic uncovered-region weighting and frozen-static, with mean SSIM decline no worse than **0.01**.

Those conditions identify a useful weighting intervention, not yet a competitive predictor. To retain it as a generation-method candidate, require it also to exceed the stronger of B2(mem_vmem) and the equal-available-observation deterministic renderer by **≥+0.2 dB**, with the same uncertainty and SSIM checks. The latter renderer uses the **twenty H frames plus the same four static contexts**, so extra historical information in weights is not compared only against a weaker four-image warp. Also include nearest-view copy over those same twenty-four observations.

If adaptation improves the weak frozen generator but remains dominated by deterministic geometry, report a narrow adaptation finding and do not sell it as a successful new generator.

**Additional controls and attribution.**

Generate a secondary weighted-adapter/mem_vmem arm to test complementarity with runtime retrieval, but do not replace the fixed-context primary with it. Include frozen mem_vmem. Apply each of the three learned bank adapters to the next bank under a single fixed cyclic permutation as a descriptive cross-traversal control. The traversals depict the same chess room, so matching performance may be legitimate shared scene memory and is not a general kill criterion. Only an independently established difference in source-supported content could make a swap diagnostic of specific-bank recall. Fix the query diagnostic mask as support(H at query pose) AND NOT support(static_recent at query pose), using source-only geometry before scoring. Report its area and weighted-minus-ordinary errors inside and outside it alongside full-frame metrics. If improvement is not demonstrated in that region, remove the claim of recalling context-missing content while retaining any valid whole-frame adaptation result. Do not replace the primary with this region or call estimated support ground-truth visibility.

The strongest matched mechanism control is ordinary H-LoRA; the strongest cheap predictive control is the multi-source warp. If only adaptation helps but geometry weighting does not, the result belongs to existing personalization practice. Do not claim compression or latency superiority without counting adapter training, storage and how often H is reused.

**Kill criteria.**

Stop on any target leakage, insufficient masks (pre-freeze rule: fewer than **16 of 64** episodes in any bank with at least **5%** U coverage), non-finite training, unintended base-weight changes, or runtime beyond budget. Complete the frozen valid evaluation once; a primary miss, shuffled-mask match, donor-agnostic weighting match, or deterministic-baseline domination kills the corresponding method claim. A same-room adapter swap alone does not. Do not rescue it by switching to S141 A, extending steps, enlarging rank or training on all chess frames.

**Budget and 1–2-day execution.**

Four arms × three banks × 1,000 steps = **12,000 steps**. The protocol's short smoke rate gives **ANALYTICAL: 4.60 GPU-hours** of optimization before extra work; it is not verified full-run throughput. The primary static arms require **384 generations**, the weighted/memory arm **96**, and the cross-traversal static arm **96**: **576 generations**, about **DERIVED/ANALYTICAL: 5.78 baseline-equivalent GPU-hours**. Allow **12–16 RTX 3090 GPU-hours total** for encoding, mask construction, training and generation, with a hard cap of **16**. Time the new mask preparation on a training-scene bank first. Both cards can run equal-budget arms or banks independently; no H800 speedup is assumed. Appendix C updates the arithmetic for this final control set.

This is a two-day pilot-scale experiment, not a promise of a publishable result in two days. It does not include a new RGB-D adaptation panel, a full PWM/CogNVS reproduction, or a second global training run.

**A genuinely interesting result.** With the same runtime static context, the geometrically targeted adapter recalls historical content better than ordinary bank SFT and spatially shuffled weighting, beats an equally informed renderer, and retains the effect across all reported bank pairs. That would motivate investigating *what memory should be written into weights*. A basic LoRA gain alone is already anticipated by the literature.

## 5. Which one to run first, and the remaining claim gap

**Experiment 1 is first.** It targets the directly measured regional asymmetry, reuses the fixed generator, and tests whether permissible source observations can predict the sign of a correction. It can fail cheaply against global fusion. It needs neither S141's outcome nor a new architecture.

Experiment 2 is the second candidate because it changes where memory resides. It is a more substantial departure from the present context-only route, but its generic form is already occupied by PWM, CogNVS and GAPS. The targeted replay loss must earn its place against ordinary bank adaptation and deterministic geometry.

I am deliberately retaining **two**, not filling three slots with a weaker variant. The first next-session deliverable should be the frozen implementation/protocol and the development headroom result for Experiment 1. If it fails, keep its negative result and evaluate whether Experiment 2 still answers a distinct question within the remaining budget; do not rename the same fusion rule and restart.

A positive result on these panels would still be an exposed-panel candidate. A strong method paper would subsequently need an untouched scene-level test, a close published comparator, and temporal evaluation if claiming video improvement. This review does not claim those assets or evaluations already exist.

**Changed file:** work/agents/CODEX_R258_IDEATION_FROM_FINDINGS.md only. **Follow-up worth a new session:** implement Experiment 1 under a new dated stage; verify access to original prediction arrays and their receipts; preserve S141/S142 execution and analysis independently.

## Appendix A — CPU headroom calculation

This read-only CPU calculation was executed from the repository root. It uses existing scalar score records and does not read generated RGB or create predictions. All oracle choices use scoring ground truth and are diagnostic ceilings only. The final complete command/output below uses full sequence-pair labels; an earlier display shortened those labels without changing any numerical result.

Exact command:

```bash
python3 -B - <<'PY'
import json, math, random, statistics as st
from pathlib import Path
from collections import defaultdict
root=Path('work/S140_warp_guided/results/confirm_tacc')
wgs=json.loads((root/'S140_SCORES_confirm_tacc.json').read_text())
vmem=json.loads((root/'S139_VMEM_SSIM_tacc.json').read_text())
def grouped(obj):
 d=defaultdict(dict)
 for r in obj['runs'].values():
  w,s=r['window_id'],r['seed']; assert s in (3,4,5,6) and s not in d[w]
  d[w][s]=r
 assert len(d)==24 and all(set(v)=={3,4,5,6} for v in d.values())
 return d
gw,gv=grouped(wgs),grouped(vmem)
assert set(gw)==set(gv)==set(wgs['warps'])
mean=lambda x:st.mean(list(x))
def boot(v):
 rng=random.Random(258); v=list(v)
 a=sorted(mean(rng.choices(v,k=len(v))) for _ in range(10000))
 return (a[249],a[9749])
print('scope: archived chess RTX 3090 scores, seeds 3,4,5,6; 24 windows; no RGB regeneration')
for label,g in [('VMem',gv),('WGS',gw)]:
 av=[]; best=[]; gap=[]
 for w in sorted(g):
  p=[r['psnr_db'] for r in g[w].values()]; av.append(mean(p));best.append(max(p));gap.append(max(p)-mean(p))
 print(label,'random_seed_expected_PSNR',format(mean(av),'.6f'),'GT_oracle_best4_PSNR',format(mean(best),'.6f'),'GT_oracle_headroom_dB',format(mean(gap),'.6f'),'GT_oracle_minus_warp_dB',format(mean(best)-mean(r['psnr'] for r in wgs['warps'].values()),'.6f'))
fixed=[];oracle=[];errs=[];cov=[];hole=[];perpair=defaultdict(list)
for w in sorted(gw):
 f=[];o=[]
 for r in gw[w].values():
  h=r['hole_fraction'];gc=10**(-r['psnr_covered']/10);gh=10**(-r['psnr_holes']/10);wc=10**(-r['warp_psnr_covered']/10);wh=10**(-r['warp_psnr_holes']/10)
  errs.append(abs(-10*math.log10((1-h)*gc+h*gh)-r['psnr_db']))
  f.append(-10*math.log10((1-h)*gc+h*wh))
  o.append(-10*math.log10((1-h)*min(gc,wc)+h*min(gh,wh)))
  cov.append(r['psnr_covered']-r['warp_psnr_covered']);hole.append(r['psnr_holes']-r['warp_psnr_holes'])
 d=mean(f)-wgs['warps'][w]['psnr'];fixed.append(d);oracle.append(mean(o)-wgs['warps'][w]['psnr']);perpair[w.rsplit('_s',1)[0]].append(d)
print('region_reconstruction_max_abs_PSNR_error',format(max(errs),'.12g'))
print('covered_WGS_minus_warp_dB',format(mean(cov),'.6f'),'uncovered_WGS_minus_warp_dB',format(mean(hole),'.6f'))
print('fixed_RGB_paste_WGS_covered_warp_uncovered_minus_warp_dB',format(mean(fixed),'.6f'),'window_bootstrap95',*[format(x,'.6f') for x in boot(fixed)],'positive_windows',sum(x>0 for x in fixed))
print('fixed_paste_per_pair',json.dumps({k:round(mean(v),6) for k,v in sorted(perpair.items())},sort_keys=True))
print('GT_oracle_two_region_choice_minus_warp_dB',format(mean(oracle),'.6f'))
print('SSIM_fusion_and_frequency_error_covariance: unavailable from these scalar scores; not inferred')
print('All selection oracles use scorer ground truth and are diagnostic upper bounds, not deployable methods.')
PY
```

Complete output (exit code 0):

```text
scope: archived chess RTX 3090 scores, seeds 3,4,5,6; 24 windows; no RGB regeneration
VMem random_seed_expected_PSNR 11.274894 GT_oracle_best4_PSNR 11.713744 GT_oracle_headroom_dB 0.438849 GT_oracle_minus_warp_dB -2.858644
WGS random_seed_expected_PSNR 14.568249 GT_oracle_best4_PSNR 14.773982 GT_oracle_headroom_dB 0.205733 GT_oracle_minus_warp_dB 0.201594
region_reconstruction_max_abs_PSNR_error 3.5527136788e-15
covered_WGS_minus_warp_dB 0.231158 uncovered_WGS_minus_warp_dB -0.274957
fixed_RGB_paste_WGS_covered_warp_uncovered_minus_warp_dB 0.122799 window_bootstrap95 0.093323 0.149847 positive_windows 23
fixed_paste_per_pair {"seq-02_from_seq-01": 0.063695, "seq-03_from_seq-04": 0.168876, "seq-05_from_seq-06": 0.135826}
GT_oracle_two_region_choice_minus_warp_dB 0.193955
SSIM_fusion_and_frequency_error_covariance: unavailable from these scalar scores; not inferred
All selection oracles use scorer ground truth and are diagnostic upper bounds, not deployable methods.
```

## Appendix B — Snapshot, asset scope and resource arithmetic

This read-only CPU command records identities and existing timing logs. It does not establish remote checkpoint, cache, free-space, or GPU availability. The training-step rate is taken from work/S141_finetune/PROTOCOL.md:43–49, where it is a short engineering smoke measurement; future costs are extrapolations. The inspected uncommitted changes belong to concurrent work and were left alone.

Exact command:

```bash
python3 -B - <<'PY'
import hashlib,json,statistics,subprocess
from pathlib import Path
print('workspace',Path.cwd())
print('host',subprocess.check_output(['hostname'],text=True).strip())
print('head',subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
files=['CURRENT_STATUS.md','docs/report/TECHNICAL_REPORT_20261010.md','work/S139_crossseq_revisit/RESULT.md','work/S140_warp_guided/RESULT.md','work/S141_finetune/PROTOCOL.md','work/S142_followup/PROTOCOL.md','work/agents/CODEX_R253_RETRIEVAL_S141.md','work/agents/CODEX_R255_IDEATION_AFTER_S141.md','work/agents/CODEX_R256_S142_DRAFT_REJECTION.md','work/S140_warp_guided/gen_s140.py','work/S140_warp_guided/score_s140.py','work/S141_finetune/train_s141.py','work/S141_finetune/gen_s141.py','work/S141_finetune/s141_common.py','work/S141_finetune/warps_s141.py','work/S139_crossseq_revisit/results/stepB_tacc/S139_SCORES_tacc.json','work/S140_warp_guided/results/confirm_tacc/S140_SCORES_confirm_tacc.json','work/S140_warp_guided/results/confirm_tacc/S139_VMEM_SSIM_tacc.json']
for name in files: print(hashlib.sha256(Path(name).read_bytes()).hexdigest(),name)
j=json.loads(Path('work/S141_finetune/clips_s141.json').read_text())
print('clip_counts',len(j['clips']),{s:sum(c['split']==s for c in j['clips']) for s in ['train','val']})
logs=sorted(Path('work/S139_crossseq_revisit/results/stepB_tacc').glob('RUNS_*.jsonl'))
r=[json.loads(l) for p in logs for l in p.read_text().splitlines() if l.strip()]
t=statistics.mean(x['seconds'] for x in r)
print('timing_paths',[str(p) for p in logs])
print('archived_generation_count',len(r),'mean_seconds',format(t,'.6f'))
for n in [24,96,128,192,288,384,480]: print('generation_count',n,'baseline_equivalent_GPU_hours',format(n*t/3600,'.6f'))
print('6000_steps_at_reported_smoke_1.38_seconds_GPU_hours',format(6000*1.38/3600,'.6f'))
for d in ['data/S140_warps_chess','work/S140_warp_guided/results/confirm_tacc','work/S139_crossseq_revisit/results/stepB_tacc']:
 p=Path(d);print('local_arrays',d,'npy',sum(1 for _ in p.glob('*.npy')),'npz',sum(1 for _ in p.glob('*.npz')))
print('output_preexists',Path('work/agents/CODEX_R258_IDEATION_FROM_FINDINGS.md').exists())
print('git_status_begin');print(subprocess.check_output(['git','status','--short'],text=True),end='');print('git_status_end')
PY
```

Complete output (exit code 0):

```text
workspace /Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling
host MacBook-Pro-M3-MAX.local
head ddb6b6c56685b5650621be2fc57e1996fcfb7624
60c4f4a245bbda05fd9be464c5fba81393904e666f1cb15f7aefb090428bb0fe CURRENT_STATUS.md
a9e437e9fd5619070cad5eb38c50f4157c88afcedb5c64c98f66bc405c90b16f docs/report/TECHNICAL_REPORT_20261010.md
a09a20a359acc31755a511b8b81ad56747f6046a2c750c5287ef6ab07e4e0f05 work/S139_crossseq_revisit/RESULT.md
2db2f7ed6d3184a5cdc5b39c369d98bd2c558e55f56e0513fc3f86292f58634c work/S140_warp_guided/RESULT.md
0b5c3aab9809f851ee476b2a54eae781c7c286bbe1e047ac89388b40d3051fdc work/S141_finetune/PROTOCOL.md
d4358e4acfc64d8bd9f1d2e29742a2f5facbb67bdecc33f5852dcc74d4a1b692 work/S142_followup/PROTOCOL.md
7e17d1600d0b0ab8019ff38fc3ba928f2075f500e72181755fb8770e0ade31de work/agents/CODEX_R253_RETRIEVAL_S141.md
62fc97aed343bde1f684140f70bba7cd1281522c34c86d8fe8589cc7965b2a2a work/agents/CODEX_R255_IDEATION_AFTER_S141.md
c0bc379db9f9fe847c744c5c51baee85dc5bdbba27ae629632c9db1f92594d0b work/agents/CODEX_R256_S142_DRAFT_REJECTION.md
119904b368eefe4f7bd99e1aed0ba91d7a9250aad5e97a0fb298d7007c0a46c9 work/S140_warp_guided/gen_s140.py
61f093cb2e40eeec2d862562dc6e28e98076447cde5819a2384536937cb00a79 work/S140_warp_guided/score_s140.py
6ba0419e5ceb39406bbd1894ffae90398c27daedbc2eea56b18e537ba6187c0a work/S141_finetune/train_s141.py
c903be28ffea8c359c79d927ebdcf782e1d9ac21b81d0b159439e1566fac8121 work/S141_finetune/gen_s141.py
459549706fb3a965fc4f7c5021f4d49cc626158e94a7c9cdc94cf8784cccb6cc work/S141_finetune/s141_common.py
72d8f66fb4439ef3cf626d973a594b182bf30b04d89cb0af221c1208fb048470 work/S141_finetune/warps_s141.py
3c42e2c3658f1115bda23b5bb1ecef673a824bbc51166137bffe19a32340bd5f work/S139_crossseq_revisit/results/stepB_tacc/S139_SCORES_tacc.json
429dfcb6e777ffa9797bdc8466253332c353580336ff1968a6647377d9a72fc6 work/S140_warp_guided/results/confirm_tacc/S140_SCORES_confirm_tacc.json
7c38f0d5a646b151600d96e2c5264723813be130e56de09ae1a725b600e650b5 work/S140_warp_guided/results/confirm_tacc/S139_VMEM_SSIM_tacc.json
clip_counts 2032 {'train': 2000, 'val': 32}
timing_paths ['work/S139_crossseq_revisit/results/stepB_tacc/RUNS_gpu13_2110672.jsonl', 'work/S139_crossseq_revisit/results/stepB_tacc/RUNS_gpu13_2110673.jsonl', 'work/S139_crossseq_revisit/results/stepB_tacc/RUNS_gpu13_2218137.jsonl', 'work/S139_crossseq_revisit/results/stepB_tacc/RUNS_gpu13_2227306.jsonl']
archived_generation_count 288 mean_seconds 36.114410
generation_count 24 baseline_equivalent_GPU_hours 0.240763
generation_count 96 baseline_equivalent_GPU_hours 0.963051
generation_count 128 baseline_equivalent_GPU_hours 1.284068
generation_count 192 baseline_equivalent_GPU_hours 1.926102
generation_count 288 baseline_equivalent_GPU_hours 2.889153
generation_count 384 baseline_equivalent_GPU_hours 3.852204
generation_count 480 baseline_equivalent_GPU_hours 4.815255
6000_steps_at_reported_smoke_1.38_seconds_GPU_hours 2.300000
local_arrays data/S140_warps_chess npy 0 npz 96
local_arrays work/S140_warp_guided/results/confirm_tacc npy 0 npz 0
local_arrays work/S139_crossseq_revisit/results/stepB_tacc npy 0 npz 0
output_preexists False
git_status_begin
 M AGENTS.md
?? work/S141_finetune/fetch_results_s141.sh
?? work/S142_followup/gen_s142.py
?? work/agents/prompts/R257_FULL.md
?? work/agents/prompts/R257_PROMPT.md
?? work/agents/prompts/R258_FULL.md
?? work/agents/prompts/R258_PROMPT.md
?? work/agents/prompts/R259_FULL.md
?? work/agents/prompts/R259_PROMPT.md
git_status_end
```

No repository test suite or linter was run: this deliverable changes no executable code. The CPU arithmetic above is an evidence check, not a model test or image-level validation.

## Appendix C — Final control-set arithmetic and document check

The final read-only check below covers the revised control set, citation line ranges, local artifact links, and hashes of the inspected inputs. It is not a model test. The byte count precedes this appendix. Concurrent R257/R259 reports appeared while R258 was being prepared; they were not authored, modified or used as evidence by this review.

Exact command:

```bash
python3 -B - <<'PY'
import re,hashlib,json,subprocess
from pathlib import Path
p=Path('work/agents/CODEX_R258_IDEATION_FROM_FINDINGS.md');s=p.read_text();body=s.split('## Appendix A')[0]
refs=re.findall(r'((?:work|data|docs)/[A-Za-z0-9_./-]+\.(?:py|md|json)):(\d+)(?:[\u2013-](\d+))?',body)
bad=[]
for name,lo,hi in refs:
 q=Path(name);lo=int(lo);hi=int(hi or lo)
 if not q.is_file() or not 1<=lo<=hi<=len(q.read_text().splitlines()):bad.append([name,lo,hi])
links=re.findall(r'\]\(([^)]+)\)',body);missing=[]
for url in links:
 if url.startswith(('https:','#')):continue
 q=p.parent/url.split('#')[0]
 if not q.exists():missing.append(url)
print('report_exists',p.is_file())
print('bytes_before_QA_append',p.stat().st_size)
print('divergent_idea_rows',len(re.findall(r'^\| \*\*(?:\d+)(?: / P\d)?\*\* \|',body,re.M)))
print('prior_art_sections',len(re.findall(r'^### P[1-5]\.',body,re.M)))
print('retained_experiments',len(re.findall(r'^### Experiment [12] ',body,re.M)))
print('file_line_citations_checked',len(refs),'invalid',bad)
print('missing_relative_artifact_links',missing)
print('markdown_fences_balanced',s.count(chr(96)*3)%2==0)
print('replacement_characters',s.count(chr(65533)))
expected={"CURRENT_STATUS.md":"60c4f4a245bbda05fd9be464c5fba81393904e666f1cb15f7aefb090428bb0fe","docs/report/TECHNICAL_REPORT_20261010.md":"a9e437e9fd5619070cad5eb38c50f4157c88afcedb5c64c98f66bc405c90b16f","work/S139_crossseq_revisit/RESULT.md":"a09a20a359acc31755a511b8b81ad56747f6046a2c750c5287ef6ab07e4e0f05","work/S140_warp_guided/RESULT.md":"2db2f7ed6d3184a5cdc5b39c369d98bd2c558e55f56e0513fc3f86292f58634c","work/S141_finetune/PROTOCOL.md":"0b5c3aab9809f851ee476b2a54eae781c7c286bbe1e047ac89388b40d3051fdc","work/S142_followup/PROTOCOL.md":"d4358e4acfc64d8bd9f1d2e29742a2f5facbb67bdecc33f5852dcc74d4a1b692","work/agents/CODEX_R253_RETRIEVAL_S141.md":"7e17d1600d0b0ab8019ff38fc3ba928f2075f500e72181755fb8770e0ade31de","work/agents/CODEX_R255_IDEATION_AFTER_S141.md":"62fc97aed343bde1f684140f70bba7cd1281522c34c86d8fe8589cc7965b2a2a","work/agents/CODEX_R256_S142_DRAFT_REJECTION.md":"c0bc379db9f9fe847c744c5c51baee85dc5bdbba27ae629632c9db1f92594d0b","work/S140_warp_guided/gen_s140.py":"119904b368eefe4f7bd99e1aed0ba91d7a9250aad5e97a0fb298d7007c0a46c9","work/S140_warp_guided/score_s140.py":"61f093cb2e40eeec2d862562dc6e28e98076447cde5819a2384536937cb00a79","work/S141_finetune/train_s141.py":"6ba0419e5ceb39406bbd1894ffae90398c27daedbc2eea56b18e537ba6187c0a","work/S141_finetune/gen_s141.py":"c903be28ffea8c359c79d927ebdcf782e1d9ac21b81d0b159439e1566fac8121","work/S141_finetune/s141_common.py":"459549706fb3a965fc4f7c5021f4d49cc626158e94a7c9cdc94cf8784cccb6cc","work/S141_finetune/warps_s141.py":"72d8f66fb4439ef3cf626d973a594b182bf30b04d89cb0af221c1208fb048470","work/S139_crossseq_revisit/results/stepB_tacc/S139_SCORES_tacc.json":"3c42e2c3658f1115bda23b5bb1ecef673a824bbc51166137bffe19a32340bd5f","work/S140_warp_guided/results/confirm_tacc/S140_SCORES_confirm_tacc.json":"429dfcb6e777ffa9797bdc8466253332c353580336ff1968a6647377d9a72fc6","work/S140_warp_guided/results/confirm_tacc/S139_VMEM_SSIM_tacc.json":"7c38f0d5a646b151600d96e2c5264723813be130e56de09ae1a725b600e650b5"}
changed=[name for name,h in expected.items() if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=h]
print('reviewed_input_hash_changes',changed)
logs=sorted(Path('work/S139_crossseq_revisit/results/stepB_tacc').glob('RUNS_*.jsonl'))
r=[json.loads(line) for f in logs for line in f.read_text().splitlines() if line.strip()]
t=sum(x['seconds'] for x in r)/len(r)
print('experiment1_260_generations_baseline_GPU_hours',format(260*t/3600,'.6f'))
print('experiment2_576_generations_baseline_GPU_hours',format(576*t/3600,'.6f'))
print('experiment2_12000_steps_at_smoke_rate_GPU_hours',format(12000*1.38/3600,'.6f'))
print('git_status_begin');print(subprocess.check_output(['git','status','--short'],text=True),end='');print('git_status_end')
assert not bad and not missing and s.count(chr(96)*3)%2==0
PY
```

Complete output (exit code 0):

```text
report_exists True
bytes_before_QA_append 59562
divergent_idea_rows 16
prior_art_sections 5
retained_experiments 2
file_line_citations_checked 30 invalid []
missing_relative_artifact_links []
markdown_fences_balanced True
replacement_characters 0
reviewed_input_hash_changes []
experiment1_260_generations_baseline_GPU_hours 2.608263
experiment2_576_generations_baseline_GPU_hours 5.778306
experiment2_12000_steps_at_smoke_rate_GPU_hours 4.600000
git_status_begin
 M AGENTS.md
?? work/S141_finetune/fetch_results_s141.sh
?? work/S142_followup/gen_s142.py
?? work/agents/CODEX_R257_IDEATION_MECHANISMS.md
?? work/agents/CODEX_R258_IDEATION_FROM_FINDINGS.md
?? work/agents/CODEX_R259_IDEATION_EVALUATION.md
?? work/agents/prompts/R257_FULL.md
?? work/agents/prompts/R257_PROMPT.md
?? work/agents/prompts/R258_FULL.md
?? work/agents/prompts/R258_PROMPT.md
?? work/agents/prompts/R259_FULL.md
?? work/agents/prompts/R259_PROMPT.md
git_status_end
```
