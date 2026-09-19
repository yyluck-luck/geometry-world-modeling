# Error Attribution in Conditional Generation — Literature Survey

**Scope:** root-cause attribution of "ghosting / smearing" in geometry-conditioned novel-view generation; whether the cause is geometry error, conditional averaging, condition conflict, or the generator itself.
**Date of survey:** September 2026.

**Method note / honesty note.** Every paper below was retrieved by me from an arXiv abstract page, a CVF Open Access page, an ICML/NeurIPS page, or an author project page. URLs given are the pages I actually fetched. Where I could not fetch a page, I mark it **UNVERIFIED**. I separate *"the paper claims X"* from *"X is true"*, and I flag synthetic-only / single-scene evidence explicitly.

---

## 1. Table of works

| Work | Venue / Year | URL | Causal factor it addresses | Evidence strength |
|---|---|---|---|---|
| Blau & Michaeli, *The Perception-Distortion Tradeoff* | CVPR 2018 / IEEE TPAMI 2020 | https://ar5iv.labs.arxiv.org/html/1711.06077 | **Why MSE minimization produces blur off the data manifold.** Proves distortion ↔ perceptual quality are fundamentally at odds; MMSE estimate = posterior mean = averaging over explanations | **Theory** (theorem, general over distortion measures) + synthetic MNIST demo |
| Ohayon, Michaeli, Elad, *Posterior-Mean Rectified Flow (PMRF)* | ICLR 2025 (arXiv 2410.00418) | https://ar5iv.labs.arxiv.org/html/2410.00418 ; https://github.com/reuvenperetz/PMRF | **The posterior mean is the wrong target even when you want minimum MSE.** Shows posterior sampling has MSE = 2×MMSE; the MSE-optimal *perfect-perceptual* estimator is "posterior mean → optimal transport to data distribution" | Theory + **real** benchmarks (CelebA-Test blind face restoration, denoising, SR, inpainting, colorization) |
| Aithal, Maini, Lipton, Kolter, *Understanding Hallucinations in Diffusion Models through Mode Interpolation* | arXiv 2406.09358 | https://ar5iv.labs.arxiv.org/html/2406.09358 | **Direct cause of double-image / out-of-support artifacts.** Smooth score approximation at disjoint modes ⇒ model interpolates *between* modes; hallucinated samples have **high variance in predicted x̂₀ over the last ~20–200 steps** | Theory (why smooth approximation is unavoidable) + **synthetic** (1D/2D Gaussian mixtures, Simple Shapes) + **real** (hands dataset, 5k images) |
| Jin, Shi, Gu, *Stage-wise Dynamics of Classifier-Free Guidance in Diffusion Models* | arXiv 2509.22007 | https://ar5iv.labs.arxiv.org/html/2509.22007 | **CFG under multimodal conditionals.** Three-stage structure: early guidance drags trajectories to the *weighted mean* (initialization bias), mid is mode-neutral, late guidance over-contracts within a mode. Directly explains why **late** guidance ≠ early guidance | Theory (Gaussian-mixture conditionals, theorems) + real-model validation |
| Wu, Chen, Li, Wang, Wei, *Theoretical Insights for Diffusion Guidance: A Case Study for Gaussian Mixture Models* | arXiv 2403.01639 | https://arxiv.org/abs/2403.01639 | Guidance raises class confidence while **reducing differential entropy** of the output distribution — guidance itself destroys diversity/modes | Theory (DDPM + DDIM, Fokker–Planck) |
| Pavasovic, Verbeek, Biroli, Mezard, *Classifier-Free Guidance: From High-Dimensional Analysis to Generalized Guidance Forms* | arXiv 2502.07849 (v2 May 2025) | https://arxiv.org/abs/2502.07849 | CFG **distributional distortion vanishes in high dimension**; large family of generalized (incl. non-linear) guidances reproduce the target | Theory (high-dimensional) + real class-conditional and text-to-image experiments |
| Wang, Shen, Ge, Chen, Li, Chen, *Text-Anchored Score Composition (TASC)* | arXiv 2306.14408 (v3 2024) | https://arxiv.org/abs/2306.14408 | **What happens when conditions disagree:** "the final output could be either dominated by one condition, or ambiguity may arise". Fixes it by *separating* conditions into aligned pairs and realigning via cross-attention | Real (qualitative + quantitative on T2I), training-free |
| Sun et al., *Minimal Impact ControlNet* | arXiv 2506.01672 (ICLR 2025) | https://arxiv.org/abs/2506.01672 | **Multi-ControlNet conflict**: each control is trained to influence the whole image; "silent" low-frequency controls suppress texture elsewhere. Names an **asymmetry in the score Jacobian induced by ControlNet** | Real (image generation experiments) |
| Liu et al., *Blend-Aware Latent Diffusion: Mitigating Stitched Seams in Image Inpainting* | CVPR 2026 (Findings) | https://openaccess.thecvf.com/content/CVPR2026F/html/Liu_Blend-Aware_Latent_Diffusion_Mitigating_Stitched_Seams_in_Image_Inpainting_CVPRF_2026_paper.html | **Blending itself is a cause, independent of geometry.** "Latent blending of the two regions in inference, which is unaccounted for in training, creates a piece-wise latent manifold" → boundary discontinuity + content inconsistency | Real (BrushBench, MISATO) |
| Seo et al., *GenWarp: Single Image to Novel Views with Semantic-Preserving Generative Warping* | arXiv 2405.17251 (NeurIPS 2024) | https://ar5iv.labs.arxiv.org/html/2405.17251 | **Geometry-error attribution in NVS.** States explicit warping is "sensitive to errors in the depth map"; "the subsequent inpainting model only takes as input the warped image... thus showing limited performance at large view changes". Alternative: warp implicitly in attention | Real (RealEstate10K, ScanNet, in-the-wild) |
| Ye, Liu, Li, Pollefeys, Yang, *Synthesizing Consistent Novel Views via 3D Epipolar Attention without Re-Training* | 3DV 2025 (arXiv 2502.18219) | https://arxiv.org/abs/2502.18219 | **Conditioning on the *right* subset of context.** Claims the key cause of view inconsistency is "limited utilization of contextual information from reference views"; epipolar geometry localizes overlapping info, no training | Real (multi-view consistency + downstream 3D reconstruction) |
| Reu, Dromigny, Bronstein, Vargas, *Gradient Variance Reveals Failure Modes in Flow-Based Generative Models* | NeurIPS 2025 (arXiv 2510.18118) | https://ar5iv.labs.arxiv.org/html/2510.18118 | **Whether the model averages or commits at trajectory crossings.** Proves the straight-path objective admits a *memorizing* vector field and that **deterministic numerical integration "jumps over" intersections** — so averaging is not the only possible behavior at an ambiguous point | Theory (propositions) + synthetic MoG + real (CelebA) |
| Bose et al., *Uncertainty-Aware Diffusion-Guided Refinement of 3D Scenes* | ICCV 2025 | https://openaccess.thecvf.com/content/ICCV2025/html/Bose_Uncertainty-Aware_Diffusion-Guided_Refinement_of_3D_Scenes_ICCV_2025_paper.html | **Uncertainty-gated use of a generative prior.** Per-pixel entropy maps decide which pixels to trust during diffusion-guided 3D refinement; discards high-uncertainty pixels rather than blending them | Real (RealEstate-10K in-domain, KITTI-v2 out-of-domain) |
| Thawatdamrongkit, Seripanitkarn, Suwajanakorn, *Diffusion Mental Averages* | CVPR 2026 | https://openaccess.thecvf.com/content/CVPR2026/html/Thawatdamrongkit_Diffusion_Mental_Averages_CVPR_2026_paper.html | **Why averaging samples gives blur, and where averaging *should* happen.** Data-centric averaging of diffusion samples is blurry; averaging must be done *inside the model's evolving semantic space* by aligning denoising trajectories | Real (image generation) |
| Wang et al., *DUSt3R: Geometric 3D Vision Made Easy* | arXiv 2312.14132 (CVPR 2024) | https://arxiv.org/abs/2312.14132 | Geometry estimator itself (project's CUT3R/DUSt3R family): pairwise **pointmap regression** + global alignment; no camera calibration needed | Real (MVS/depth/pose benchmarks) |
| Wang et al., *Continuous 3D Perception Model with Persistent State (CUT3R)* | arXiv 2501.12387 (CVPR 2025) | https://arxiv.org/abs/2501.12387 | Geometry estimator: stateful recurrent pointmap prediction in a **common coordinate system**; can "infer unseen regions by probing at virtual, unobserved views" | Real (3D/4D tasks) |
| Cao, Rockwell, Johnson, *FWD: Real-Time Novel View Synthesis With Forward Warping and Depth* | CVPR 2022 | https://openaccess.thecvf.com/content/CVPR2022/html/Cao_FWD_Real-Time_Novel_View_Synthesis_With_Forward_Warping_and_Depth_CVPR_2022_paper.html | **Recorded paper #1** — see §2.6 | Real, **with explicit depth ablation** |
| Johari, Lepoittevin, Fleuret, *GeoNeRF: Generalizing NeRF With Geometry Priors* | CVPR 2022 | https://openaccess.thecvf.com/content/CVPR2022/html/Johari_GeoNeRF_Generalizing_NeRF_With_Geometry_Priors_CVPR_2022_paper.html | **Recorded paper #2** — see §2.6 | Real + synthetic benchmarks |
| Kwak, Song, Kim, *GeCoNeRF: Few-shot Neural Radiance Fields via Geometric Consistency* | ICML 2023 | https://arxiv.org/abs/2301.10941 ; https://cvlab-kaist.github.io/GeCoNeRF/ | **Recorded paper #3** — see §2.6 | Real (LLFF) + synthetic (NeRF-Synthetic), 3-view |
| Daras et al., *A Survey on Diffusion Models for Inverse Problems* | arXiv 2410.00083 (38pp, work in progress) | https://arxiv.org/abs/2410.00083 | **Background on posterior mean / Tweedie.** 𝔼[X₀|Xₜ] — the quantity a diffusion denoiser is trained to output *is* the posterior mean, hence averaging-prone | Survey (no new evidence) |

**Explicitly not verified.** I saw search-result references to a "Resolving Conflicting Multi-Control Constraints" section and to several 2026 world-model papers (e.g. `AnchorWeave`, `WorldPlay`, `GeoFlow`, `DiffusionHarmonic`-adjacent items) but did **not** fetch their primary pages, so I make **no claims** about them. Likewise, for *calibrated depth uncertainty* and for *"does better geometry help generation?"* as a deliberate ablation, I did **not** find and verify a paper that answers the question head-on. That gap is reported as a gap in §3.

---

## 2. The five most relevant: what they establish, and the limit

### 2.1 Aithal et al., *Mode Interpolation* (arXiv 2406.09358)

**What it establishes.**
- Defines a hallucination as a sample outside the training support, and identifies **mode interpolation**: the model generates θx+(1−θ)y for x,y in-support, landing out of support.
- Gives a *mechanism*, not just a symptom: the **true score function has sharp jumps between disjoint modes**, but a neural network can only learn a **smooth approximation**, so there is a finite-probability "region of uncertainty" between modes. Sanity check: substituting the *true* score yields **zero** interpolations.
- The interpolation happens in the **representation space** (t-SNE of U-Net bottleneck shows a new region between the two shape regions), not only pixel space. This is important: it means blending can occur in latent space and still decode to a sharp-but-impossible image.
- **The model "knows" when it hallucinates**: hallucinated samples have high variance of the predicted x̂₀ over the final sampling steps. A simple trajectory-variance metric filters **>95%** of hallucinations while retaining ~95–98% of in-support samples (synthetic setups). On the real Hands dataset, it separates 88 non-hallucinated from 40 hallucinated images.

**Limit of that.**
- Quantitative separation (95%/92% sensitivity & specificity) is demonstrated on **synthetic** mixtures and Simple Shapes; the real-data (hands) evaluation is on **130 manually labeled images**, i.e. small and single-domain.
- The claim "only nearest modes are interpolated" is an **empirical observation**, not proven.
- It says nothing about *conditioning*: this is an **unconditional** model. Whether an external geometry condition fixes or amplifies mode interpolation is not tested.
- The "high variance late" signal is a *detector*, not a proof that variance causes the artifact; the causal direction (uncertain score region → variance → out-of-support sample) is argued from the smooth-approximation argument.

> **Why this matters most for the project.** This is the closest thing in the verified literature to a root-cause account of "two copies of the same structure smeared together, and MSE still looks fine." It also hands the project a **cheap, mechanistic, falsifiable diagnostic**: measure the variance of the predicted x̂₀ across the last ~20–200 denoising steps, restricted to the ghosted region. If ghosting is mode interpolation under a corrupt condition, that variance should be elevated there relative to clean regions of the same frame. If it is *not* elevated, the cause is more likely geometric mis-warping than conditional averaging. Either outcome is informative.

### 2.2 Blau & Michaeli, *The Perception-Distortion Tradeoff* (CVPR 2018/TPAMI)

**What it establishes.**
- Theorem: in any **non-invertible** degradation, no distortion measure is *stably distribution-preserving*. Minimizing average distortion (MSE) does not make p_X̂ ≈ p_X.
- The MMSE estimator is exactly the **posterior mean** 𝔼[X|Y=y], "an average over all possible explanations to the measured data, weighted by their likelihoods." **"The average of valid images is not necessarily a valid image, so the MMSE estimate frequently 'falls off' the natural image manifold"** → unnatural blurry reconstructions.
- The tradeoff is **monotone** and holds **for all distortion measures**, not only PSNR/SSIM.
- Worked counterexample: a 3-point discrete X observed through additive Gaussian noise. MMSE estimates take any value in (−1,1) although X ∈ {−1,0,1} — i.e. the estimator *invents* intermediate values that never occur. This is precisely the "average of two modes" pathology in its simplest form.

**Limit of that.**
- It is a statement about the **optimal estimator**, hence about *any* method's achievable region — but it does not predict *how much* of a given artifact is averaging vs. other error sources.
- The illustration is a **toy** (MNIST digits with blanks, Gaussian noise) plus super-resolution benchmarks; it is not about 3D-conditioned generation.
- Crucially, it does **not** say MSE is meaningless. It says MSE-optimal and perceptually-natural coincide only in the limit of invertible problems. In the project's setting the map (old frames, geometry) → novel view is aggressively non-invertible, so the theorem applies with full force.

### 2.3 Ohayon, Michaeli, Elad, *PMRF* (ICLR 2025)

**What it establishes.**
- Posterior sampling gives a perfect perceptual index but its **MSE is exactly 2× the MMSE**. So "sample from the posterior" is *not* the MSE-optimal way to get realistic output.
- The MSE-optimal estimator under a perfect-perceptual-index constraint is obtained by **posterior mean → optimal transport** to the ground-truth distribution. PMRF approximates this: stage 1 regress the posterior mean, stage 2 learn a rectified flow from posterior-mean predictions to ground-truth images.
- Empirically PMRF achieves **best FID, KID, PSNR and SSIM simultaneously** on CelebA-Test blind face restoration (Table 1 of the paper), i.e. sharp *and* low-distortion.

**Limit of that.**
- The explicit result "posterior mean is over-smooth" is inherited from Blau & Michaeli; PMRF's own contribution is the constructive fix.
- All experiments are **2D image restoration**. There is no 3D/multi-view conditioning, and no guarantee the optimal-transport stage can be extended to a condition set that is itself corrupted.
- It presumes access to the ground-truth target distribution to learn the transport map. In novel-view synthesis the target distribution is exactly what is uncertain.

> **Implication for the project, stated plainly.** The project's two flagship numbers — MSE down 0.131→0.052, yet visible ghosting — are **exactly the behaviour predicted by combining Blau–Michaeli with PMRF**. Lower MSE does not mean the output moved toward the data manifold; under a multimodal conditional posterior it can mean the output moved *toward the posterior mean*, which is *off-manifold by construction*. A geometry injection that makes the conditioning sharper can lower MSE while leaving (or worsening) the averaging artifact. **MSE is therefore not a valid progress metric for this project.** This is the single most important transferable conclusion in this survey.

### 2.4 Jin, Shi, Gu, *Stage-wise Dynamics of CFG* (arXiv 2509.22007)

**What it establishes.** Models the conditional as a Gaussian mixture and proves a three-stage picture:
1. **Direction Shift (early, high noise):** the guided trajectory is pulled toward the **class-weighted mean** ω·μ̄ and its norm inflates. This is a *structural bias at the very beginning of sampling*.
2. **Mode Separation (mid):** CFG is essentially **neutral** — the weaker mode keeps an ω-independent basin of attraction. Theorems 3.3 and 3.4: weaker modes are *not destroyed* by guidance, they are simply **never reached**, because stage 1 displaced most trajectories.
3. **Concentration (late):** guidance amplifies the within-mode restoring force → **stronger within-mode contraction**, i.e. less fine-grained variation, sharper-looking samples.
4. Their own practical by-product: a **time-varying guidance schedule** improves the quality–diversity trade-off. Early-strong guidance erodes global diversity; late-strong guidance suppresses fine detail.

**Limit of that.**
- The theorems are for **Gaussian-mixture conditionals** with a specific noise schedule (α = 1/(1−t), β = t/(1−t)); the paper calls this "for technical convenience" and argues reparameterization transfers it, but that transfer is not proven.
- Validation is on diffusion models with prompts, not on geometric conditioning.
- The paper is a 2025 arXiv preprint; I did not verify a venue acceptance.

> **Why this is directly relevant to the project's second finding.** The project found **multi-step guidance unnecessary; a single terminal-step guidance at strength 0.75 beat the multi-step variant**. The stage-wise theory predicts an asymmetry that matches: guidance is (a) actively harmful in the high-noise regime — it biases trajectories toward the *mean* of the conditional modes, and (b) merely a *contraction* in the late regime. Applying guidance only at the terminal step therefore avoids the mode-averaging bias and keeps only the sharpening/alignment effect. So the project's second finding is **not** an implementation quirk — it is predicted behaviour, and it is the same mechanism that would *cause* ghosting if guidance were applied multi-step. Conversely: if the project's multi-step variant was ghosting worse than the terminal-step variant, that is evidence that **mode-averaging is a live contributor**.

### 2.5 Wang et al., *TASC* (arXiv 2306.14408)

**What it establishes.**
- States the conflict phenomenon concretely: existing controllable models are trained "on the premise of perfect alignment between the text and extra conditions. If this alignment is not satisfied, the final output could be either **dominated by one condition, or ambiguity may arise**."
- Their fix is structural, not a scalar reweighting: **separate** the conditions into mutually aligned pairs, compute each pair independently (so each computation has no internal conflict), then **realign** the independent results via cross-attention to avoid new conflicts during recombination.

**Limit of that.**
- Text-to-image with depth/bbox conditions. No multi-view, no epipolar geometry.
- It is a *training-free inference-time* fix; it does not identify which of "dominated" vs "ambiguous" output happens as a function of condition-corruption level.
- The claim that separation-then-realignment is better is empirical on T2I benchmarks.

> **Relation to the project.** The project's generator is conditioned on *both* a warped/geometric signal *and* (implicitly) the source frames / prompt. TASC's dichotomy ("dominated by one condition, or ambiguity") is exactly the fork the project needs to distinguish: is the ghost a **per-pixel superposition of two geometric hypotheses** (ambiguity) or is one condition silently **dominating** while the other is ignored? TASC says these are the two observable regimes; it also says the fix for ambiguity is to **not** let the conflicting pair be scored jointly.

### 2.6 The four recorded papers — verified statements

**FWD (Cao, Rockwell, Johnson; CVPR 2022, pp. 15713–15724).** URL: CVF page above (abstract fetched).
- **What it does:** generalizable NVS from *sparse* inputs in real time, using **explicit depth + differentiable forward warping**. Achieves results competitive with SOTA at 130–1000× speedup and "better perceptual quality". Can integrate **sensor depth** during training *or* inference to improve quality.
- **What this establishes for the project:** FWD is a *depth-and-warp* system, and it is candid that depth is the load-bearing signal — it reports that *supplying better depth helps*, which is the pro-"better geometry" side of the project's question, at least in the rasterization regime.
- **What it does NOT establish:** (i) no claim about diffusion generators; (ii) no causal decomposition of artifacts into geometry vs. blending vs. network; (iii) "better perceptual quality" is against NeRF baselines, not a study of ghosting. It does **not** address conditional averaging.
- **Caveat:** the CVPR abstract page I fetched does not expose the per-dataset numbers for the sensor-depth ablation (e.g. exact depth-quality vs quality curve), so the *strength* of the geometry→quality causal claim is **UNVERIFIED from the abstract alone**; I did not download the PDF.

**GeoNeRF (Johari, Lepoittevin, Fleuret; CVPR 2022, pp. 18365–18375; arXiv 2111.13539).** URL: CVF page above.
- **What it does:** generalizable NeRF with a two-stage design — a **geometry reasoner** (cascaded cost volumes per nearby source view) and a **renderer** (Transformer attention over cost volumes) — with "sophisticated occlusion reasoning, gathering information from consistent source views", and an RGBD variant that "directly exploits the depth information".
- **What this establishes:** that **cost-volume/attention-based occlusion-aware fusion** is a mechanism for resolving disagreement between multiple source views, and that injecting *sensor* depth is an available modification. It performs well on synthetic *and* real datasets, and fine-tunes to a single scene cheaply.
- **What it does NOT establish:** nothing about diffusion or ghosting; no ablation isolating *depth quality* from *fusion quality*; "occlusion reasoning" is architectural, not a validated attribution of artifacts. It does not test what happens when source views genuinely disagree.

**GeCoNeRF (Kwak, Song, Kim; ICML 2023; arXiv 2301.10941).** URLs: arXiv page + project page (both fetched).
- **What it does:** few-shot NeRF regularization. Warps sparse input images to an *unobserved* viewpoint using the **rendered depth map**, uses them as pseudo-ground-truths, and — this is the key design choice — enforces consistency **at the feature level rather than pixel-level**, "while allowing for modeling view-dependent radiance", plus a method to **filter out erroneous warped solutions** and occlusion-aware handling.
- **What this establishes, and it is important:** the field's own workaround for bad warps is (a) **do not supervise in pixel space**, (b) **filter/mask the bad warps** rather than average them. The ablation on their page reports that "without the consistency modeling loss, our model suffers a sharp decrease in reconstruction fidelity", and validates the **occlusion mask** and progressive modeling.
- **What it does NOT establish:** no diffusion; no generative artifact analysis; the filtering rule is not characterized as calibrated uncertainty. Evidence is 3-view LLFF (real) + NeRF-Synthetic (synthetic) — small view counts, and the qualitative claims are single-scene illustrations (`materials`, `lego`, `mic`).

**PMRF (Ohayon, Michaeli, Elad; ICLR 2025; arXiv 2410.00418).** Verified — see §2.3. Note the project's record lists PMRF under ICLR 2025; the official implementation repo is `reuvenperetz/PMRF` and the arXiv page confirms the title and content. **It is a 2D image-restoration paper and says nothing about 3D, NVS, or ghosting**; its value to the project is purely the *theory of why the MSE-optimal target is not the spatially correct target*.

**Summary judgement on the four recorded papers.** None of them diagnoses ghosting, and none of them separates geometry error from generator/averaging error. FWD and GeoNeRF are *pro-geometry* (better depth / better occlusion reasoning helps), GeCoNeRF is *anti-pixel-supervision* (feature-level consistency + filtering bad warps), and PMRF is the theoretical bridge showing why low MSE is the wrong success criterion. Treating any of them as an explanation of the project's ghosting would be a misreading.

---

## 3. ESTABLISHED VS OPEN

### Established (with the strength of the establishing evidence)

1. **Low MSE and geometric/perceptual correctness are provably not the same objective.** Blau–Michaeli (theorem, general). The MMSE estimator is the posterior mean; the average of valid images need not be a valid image; no distortion measure is stably distribution-preserving under non-invertible degradation. **This alone dissolves the project's apparent paradox** — it is not a paradox.
2. **The quantity a diffusion denoiser regresses is the posterior mean** (Tweedie / 𝔼[X₀|Xₜ], per the Daras et al. survey), so averaging is built into the training target, not a bug in the sampler.
3. **Conditional averaging has a concrete, mechanical, and detectable signature.** Aithal et al.: smooth score approximation at disjoint modes ⇒ interpolation between them; hallucinated samples exhibit elevated variance in predicted x̂₀ in the final sampling steps; a trajectory-variance statistic separates them at >92% sensitivity and specificity. Demonstrated on synthetic mixtures (strong) and on 130 labeled real hand images (weak).
4. **Guidance has stage-dependent effects, and early guidance is the mode-averaging one.** Jin et al. (Gaussian-mixture theory + real-model validation): early guidance drags to the weighted mean and reduces access to weaker modes; late guidance only contracts within a mode. Corroborated in spirit by Wu et al. (guidance raises confidence and *lowers* differential entropy) and by Pavasovic et al. (CFG distorts the distribution, though distortion → 0 in high dimension).
5. **Multi-condition conflict is a recognized failure mode with two named regimes — domination or ambiguity** (TASC), and multi-ControlNet conflicts have an identified score-Jacobian asymmetry (Minimal Impact ControlNet). Both are real-data findings.
6. **Blending is an independent cause of seams, separable from geometry.** Blend-Aware Latent Diffusion: inference-time latent blending creates a piece-wise latent manifold unaccounted for in training, producing boundary discontinuity (VAE/mask misalignment) and content inconsistency (regions follow distinct distributions). Real benchmarks.
7. **NVS practitioners already attribute large-view-change artifacts to depth error, not to the generator** — GenWarp states this explicitly ("sensitive to errors in the depth map"; the inpainting model "only takes as input the warped image... limited performance at large view changes"). This is a *claim by the paper*, supported by their own qualitative comparison, not an independent causal experiment.
8. **Uncertainty-gated selection beats blending on real multi-view data.** Uncertainty-Aware Diffusion-Guided Refinement of 3D Scenes uses per-pixel entropy to refine only from high-confidence pixels and discard the rest (real: RealEstate-10K, KITTI-v2).
9. **Under deterministic ODE integration, the model need not average at an ambiguous point** — it can "jump over" intersections (Reu et al., proposition + CelebA). So averaging is a *possible* regime, not a forced one.

### Genuinely open

1. **No verified paper performs the decisive experiment for this project:** inject geometry at *controlled, graded* error levels into a *diffusion* generator and decompose the resulting artifact into (a) geometric misalignment, (b) conditional averaging, (c) latent blending, (d) guidance-induced bias. GenWarp comes closest but does not decompose. **The project's core attribution question is unanswered in the literature I could verify.**
2. **Nobody has established whether depth-error propagation or conditional averaging dominates ghosting specifically.** The two accounts make different, distinguishable predictions (see §4) but no verified work adjudicates them.
3. **Calibrated uncertainty for depth *as a predictor of downstream generation quality*.** I found no verified paper showing that calibrated depth uncertainty predicts NVS/generation artifact severity. (Uncertainty-Aware Refinement uses entropy as a *gate*; that is not the same as calibration or predictive validity.)
4. **"Does better geometry help generation?" as an explicit ablation.** FWD's abstract implies supplying better depth helps *in an explicit-warping system*, but I found **no verified diffusion paper** that sweeps geometry quality and reports generation quality. This is an open gap, and it is exactly the ablation the project should run.
5. **Whether soft blending is ever the correct posterior mean.** The theory is clear for a *single* Gaussian posterior; for a mixture posterior the correct object is the mixture, not its mean. What is open is the *practical* case: when the condition is a warped image that is itself a superposition of several depth hypotheses, what **is** the correct conditional distribution, and does any existing sampler estimate it? No verified paper answers this.
6. **Why the multi-step guidance variant underperformed.** The stage-wise CFG theory *predicts* late guidance is better, so a terminal-step-only scheme beating multi-step is consistent — but no verified paper tests this in a geometry-conditioned NVS setting, and the paper's validation is prompt-conditioned. **The project's own result may be a new empirical confirmation of a theoretical prediction.**
7. **Mode interpolation has never been tested under external conditioning.** Aithal et al. is unconditional. Whether conditioning on corrupted geometry *creates* mode-interpolation behaviour, or mitigates it, is untested.

---

## 4. MECHANISM IDEAS THAT FALL OUT

Each is stated as a **falsifiable hypothesis** with a **measurement**. All go beyond "use better geometry."

**M1 — Ghosting is mode interpolation over ambiguous geometry (not depth error per se).**
The warped condition, where depth is multi-modal (thin structures, textureless regions, reflective/transparent surfaces, occlusion boundaries), places the sample in a region where the conditional score is smooth and multi-modal. The denoiser's posterior-mean target then returns a superposition.
*Test:* compute the Aithal trajectory-variance statistic Var(x̂₀) over the final ~20–200 steps, per pixel. Predict: ghosted pixels show significantly higher late-trajectory variance than non-ghosted pixels *within the same frame* (this within-frame control neutralizes global MSE). Also apply their detector at generation time and check whether the surviving samples are the non-ghosted ones.
*Falsified if:* late-trajectory variance in ghosted regions is indistinguishable from clean regions. Then the cause is deterministic mis-warping, not averaging.

**M2 — The ghost is in the conditioning signal, not in the generator: depth-hypothesis superposition.**
If the geometry estimator emits an ambiguous depth (e.g. two plausible surfaces), the *warped condition itself* is a superposition of two consistent images. The generator faithfully renders the superposition, so no amount of generator improvement helps.
*Test:* do **not** feed the warped image. Feed the raw source frames + explicit per-pixel depth **with a hard selection** (choose one hypothesis, e.g. by argmax confidence) and compare ghosting. Predict: hard selection reduces ghosting but may introduce a *single* wrong-but-sharp structure, whereas soft blending produces two faint structures.
*Falsified if:* hard selection produces the same ghosting — then the ambiguity is introduced downstream, inside the generator.

**M3 — Averaging is a late-stage / terminal-step phenomenon, and guidance placement controls it.**
Combine Jin et al. (stage-wise CFG) with Aithal et al. (late-trajectory variance identifies hallucination). Prediction: terminal-step-only guidance avoids the early "pull to the weighted mean" and therefore should reduce ghosting relative to multi-step guidance at the *same* final strength.
*Test:* re-run the 4-arm experiment with (a) terminal-only at 0.75, (b) multi-step at matched total guidance "dose", (c) no guidance, and measure *both* MSE and the late-trajectory-variance statistic. The theory predicts MSE may be similar across (a)/(b) while ghosting differs — which would be a clean dissociation of MSE from correctness.
*Falsified if:* ghosting tracks MSE monotonically across all arms. Then MSE is a valid proxy after all and the project's premise is wrong.

**M4 — Soft blending is the wrong estimator because blending is performed in a space where the mean is not the decode of the mean.**
Averages are only meaningful in a *linear* space. The VAE/latent space is nonlinear, so blend-then-decode ≠ decode-then-blend; the blend lands off the latent manifold, and the decoder produces a sharp but inconsistent image. This predicts ghosting can be *sharp* (not blurry) — matching the project's "visibly ghost / smear" observation.
*Test:* ablate blending location — blend in pixel space pre-encode, in latent space, and in a feature/attention space (as GenWarp does, concatenating keys/values instead of averaging pixels). Predict: latent-space blending is worst; attention-level selection (GenWarp-style) is best; pixel-space blending changes the *type* of artifact (seam vs ghost).
*Supporting precedent:* Blend-Aware Latent Diffusion (piece-wise latent manifold) and GenWarp (attention-level implicit warping instead of explicit warped-image conditioning).

**M5 — Hard selection / uncertainty gating beats soft blending, and should be applied at the depth level, not the image level.**
Precedent: GeCoNeRF filters erroneous warps; Uncertainty-Aware Diffusion-Guided Refinement discards high-entropy pixels; TASC separates conflicting condition pairs. None of these are "better geometry" — they are **selection and routing** mechanisms.
*Test:* replace soft blending with a per-pixel hard selection gated by a *calibrated* confidence (from CUT3R/DUSt3R confidence heads), and separately test a "no-conditioning-in-low-confidence-regions" arm where the generator is left free rather than forced to satisfy a bad condition.
*Falsified if:* gating degrades output — indicating the generator needs dense (even wrong) conditioning to stay on-manifold.

**M6 — MSE should be replaced by a manifold-relative metric, or the project will keep optimizing the wrong thing.**
Precedent: Blau–Michaeli (MSE ↔ perception anti-correlated at the bound), PMRF (posterior-sampling MSE = 2×MMSE; MSE-optimal-perceptual estimator is posterior-mean → OT).
*Test:* define a **disagreement metric** — e.g. re-render the generated novel view back to a source viewpoint under the *ground-truth* depth and measure reprojection error, or measure cross-view feature consistency of the ghosted region — and report it alongside MSE. Predict: MSE keeps improving while the disagreement metric plateaus. This directly tests whether the project is in the anti-correlated regime.
*This is arguably the highest-value single change*: it converts the project's unexplained 0.131→0.052 result from an anomaly into a measurement.

**M7 — Do not supervise/condition in pixel space; supervise at feature level.**
Precedent: GeCoNeRF's central design choice ("feature-level instead of pixel-level reconstruction loss... while allowing for modeling view-dependent radiance"), motivated by exactly the same class of warping error.
*Test:* swap the pixel-space geometric conditioning for feature-level consistency (perceptual/LPIPS-like or attention-key/value conditioning) and measure ghosting. Predict: reduces the *superposition* artifact because feature-space means tolerate multi-modality better than pixel-space means — but may increase geometric drift, which the disagreement metric of M6 would catch.

**M8 — Prefer single-hypothesis commitment (deterministic integration) over posterior sampling where the condition is ambiguous.**
Precedent: Reu et al. — deterministic ODE integration "jumps over" interpolant intersections, reproducing exact pairings rather than averaging; and small injected noise restores generalization. So **stochasticity and determinism have opposite effects on averaging**, and the right regime depends on whether you want commitment or diversity.
*Test:* vary sampler stochasticity (η in DDIM, or SDE vs ODE) and measure ghosting. Predict: more stochasticity → more averaging/blur; fully deterministic → sharper but possibly mode-locked. There should be a non-monotonic optimum.
*Caveat to flag:* the Reu et al. result is about rectified-flow training and Gaussian-to-Gaussian transport; extending it to a latent diffusion NVS pipeline is an extrapolation, not an established fact.

### The blunt answer to "do we need a new mechanism?"

**Yes — but not a "better geometry" mechanism, and not necessarily a new architecture.** The verified literature says the project's framing is the problem:

- The 0.131→0.052 MSE drop **cannot** by itself be evidence that geometry injection worked, because minimizing MSE provably drives the output toward the conditional mean, which is off-manifold and non-geometric (Blau–Michaeli; PMRF). The project already has the observation that proves this. It does not need a paper to tell it MSE is untrustworthy; it needs the *mechanism*.
- The two live candidate mechanisms are **(i) conditional averaging / mode interpolation under an ambiguous or self-contradictory geometry condition** and **(ii) blending in a space where the mean is not decodable** — and the stage-wise CFG theory plus the terminal-step result point at (i) as the more likely of the two, because the project's single strongest empirical clue (terminal-step guidance beats multi-step) is *predicted* by the mode-averaging account and is not predicted by the geometry-error account.
- Neither mechanism is addressed by improving depth. Both are addressed by **selection/routing** (M2, M5), **moving the averaging into a space where averaging is meaningful** (M4, M7), and **changing the objective from MSE to a manifold-relative disagreement metric** (M6). Those are genuinely new mechanisms relative to the project's current plan.

The literature does **not** already answer the project's root-cause question. It supplies the theory and two ready-made diagnostics, and it clearly says "lower MSE" is the wrong headline. The attribution experiment remains to be run.

---

## 5. Search queries used

Discovery searches:
1. `FWD CVPR 2022 novel view synthesis depth-guided warping`
2. `PMRF ICLR 2025 posterior matching rectified flow`
3. `GeoNeRF CVPR 2022 generalizable neural radiance fields`
4. `GeCoNeRF ICML 2023 few-shot neural radiance fields`
5. `conditional averaging regression to the mean diffusion models blur`
6. `diffusion model posterior collapse mode averaging average of two modes`
7. `ghosting artifact 3D consistent video generation novel view synthesis diagnosis`
8. `multi-view condition conflict diffusion model epipolar visibility occlusion aware`
9. `arXiv survey "multi-condition" diffusion models conflict guidance compose multiple conditions`
10. `"when to use which" conditional diffusion regression to the mean multimodality paper arXiv`
11. `diffusion model blurry output conditional expectation pixel MSE ill-posed inverse problem theory`
12. `arXiv "Beyond Perceptual Distortion Tradeoff" generative models fidelity diversity`
13. `arXiv classifier-free guidance theory conditional distribution overestimation`
14. `NVS artifact "double image" ghosting cause diagnosis warping vs network`
15. `"Diffusion Mental Averages" CVPR 2026 abstract`
16. `Perceptual Distortion Tradeoff Blau Michaeli 2018 arXiv 1611.05095`
17. `monocular depth estimation calibrated uncertainty aleatoric epistemic predict error arXiv`
18. `arXiv "condition conflict" OR "condition mismatch" diffusion model conditioning gap generative`
19. `SV4D 2.0 spatio-temporal consistency multi-view video diffusion arXiv 2503.16396`
20. `arXiv survey 3D consistency video diffusion models artifacts taxonomy`
21. `"epipolar" attention feature matching novel view synthesis resolve conflicts softmax`
22. `arXiv "double image" OR "ghosting" artifact stereo warping disocclusion blending cause`
23. `arXiv hard selection vs soft blending multi-view conditioning attention conflict diffusion`
24. `arXiv "occlusion-aware" diffusion conditioning novel view synthesis visibility mask`
25. `arXiv depth uncertainty calibrated metrics predict downstream performance monocular depth`
26. `"Resolving Conflicting Multi-Control Constraints" arXiv diffusion multi-control`
27. `"gradient variance reveals failure modes" flow-based generative models NeurIPS 2025 arXiv`
28. `arXiv survey multi-control image generation unified framework conflict unresolved conditions 2024 2025`
29. `arXiv "we find that" artifacts caused by diffusion rather than geometry ablation novel view synthesis controlled`
30. `arXiv "geometric conditioning" video diffusion "depth error" propagate amplify analysis`
31. `arXiv "Theoretical Insights for Diffusion Guidance" Gaussian Mixture Models arXiv number`
32. `"Uncertainty-Aware Diffusion-Guided Refinement of 3D Scenes" ICCV 2025 arXiv`
33. `ReCamMaster arXiv 2503.11647 camera-controlled generative rendering abstract`
34. `arXiv 2025 novel view synthesis "artifacts" "caused by" "inaccurate depth" versus "diffusion prior" analysis quantify`
35. `arXiv CUT3R continuous updating transformer 3D reconstruction uncertainty confidence`
36. `DUSt3R confidence-aware global alignment pointmap confidence head paper`
37. `arXiv paper quantify monocular depth error propagates to novel view synthesis rendering error bound sensitivity`
38. `arXiv "depth error" "rendering artifacts" distorted geometry novel view synthesis analysis paper`
39. `"spurious" MSE improvement image quality diffusion "regression to the mean" evaluation metric misleading arXiv`
40. `arXiv 2025 mode averaging in diffusion intermediate latent "average" two plausible images failure`
41. `"average of two" images diffusion model artifact double exposure explanation arXiv`
42. `arXiv video diffusion temporal flicker cause denoising trajectory inconsistency analysis`
43. `locuslab diffusion model hallucination paper arXiv "hallucination" diffusion posterior sampling theory`
44. `arXiv "hallucination" diffusion models uncertainty theory "when do diffusion models hallucinate"`
45. `arXiv 2025 2026 "ghosting" artifact generative novel view synthesis camera controlled diffusion cause`
46. `arXiv "temporal inconsistency" video diffusion "attention" "ghosting" smear artifact analysis 2026`
47. `arXiv "geometry-aware" video generation world model ghosting double image failure analysis`
48. `arXiv "depth quality" ablation "generation quality" novel view synthesis not monotonic geometric accuracy`
49. `arXiv 2025 sparse view Gaussian splatting depth regularization "over-regularization" artifacts trade-off geometry appearance`
50. `arXiv "depth-conditioned" ControlNet "depth map quality" generation degradation mismatch noisy depth`
51. `arXiv softmax attention averages multiple candidate correspondences blur novel view synthesis multi-view`
52. `arXiv 2025 2026 "world model" geometry memory long video generation "drift" "ghosting" cause study`
53. `"Uncertainty-Aware" "Novel View" "low confidence" mask discard pixels geometry generation arXiv`

Fetch/verification targets (primary pages retrieved):
`openaccess.thecvf.com` CVPR2022 FWD, CVPR2022 GeoNeRF, ICCV2025 Uncertainty-Aware, CVPR2026F Blend-Aware, CVPR2026 Diffusion Mental Averages; `arxiv.org/abs/` 2410.00083, 2502.07849, 2206.07275, 2410.00418, 2405.17251, 2301.10941, 2502.18219, 2404.04526, 2506.01672, 2306.14408, 2403.01639, 2501.12387, 2312.14132, 2503.11647, 2602.24096, 2512.21734; `ar5iv.labs.arxiv.org/html/` 1711.06077, 2410.00418, 2405.17251, 2510.18118, 2509.22007, 2406.09358; `cvlab-kaist.github.io/GeCoNeRF/`; `github.com/reuvenperetz/PMRF`; `cvpr.thecvf.com/virtual/2026/poster/36742`.

**Tooling note.** The arXiv Atom API (`export.arxiv.org/api/query`) returned HTTP 429 for every attempt in this session and could not be used as a structured search backend; all discovery therefore went through web search followed by direct page fetches, and every citation above corresponds to a page I fetched.
