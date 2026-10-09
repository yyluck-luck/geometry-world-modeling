# R39 red-team pivot: mechanisms after residual/counterfactual prior-art checks

Date: 2026-09-23

This is a candidate search memo, not a method authorization. The red-team pass found that several
apparently distinctive components are already occupied: residual transfer through 3D visibility
correspondence (CVPR 2022 [Boosting View Synthesis with Residual Transfer](https://openaccess.thecvf.com/content/CVPR2022/papers/Rong_Boosting_View_Synthesis_With_Residual_Transfer_CVPR2022_paper.pdf)),
counterfactual prompting and structured masking (CWM, [arXiv:2306.01828](https://arxiv.org/abs/2306.01828)),
correspondence-guided fixed-seed diffusion editing (ICCV 2025 [Edicho](https://openaccess.thecvf.com/content/ICCV2025/papers/Bai_Edicho_Consistent_Image_Editing_in_the_Wild_ICCV2025_paper.pdf)),
persistent 3D state (ICML 2026 [PERSIST](https://francelico.github.io/persist.github.io/)), and selective
newly-visible geometry updates (RSS 2026 workshop [INGRID](https://twjhlee.github.io/projects/INGRID)).
The following candidates therefore move the novelty unit away from residual transport, masks, and
generic persistence.

Benchmark overlap is also substantial: WRBench ([arXiv:2606.20545](https://arxiv.org/abs/2606.20545))
tests camera-leave, off-screen event, and return-state correctness; MemoBench (ECCV 2026) tests
disappear/reappear dynamic memory; and 3D-Belief's 3D-CORE includes object permanence. A static
geometry benchmark would need positive and negative RGB-D reveal events, an independent third-camera
query, and support/locality/anti-leakage accounting to be distinct from those evaluations.

An additional current threat is *World in World* (arXiv:2609.11548), which routes camera/time-labelled
visual states, geometry renderings for newly exposed regions, and retrieved generated states for
revisits through a frozen video model ([paper summary](https://huggingface.co/papers/2609.11548)).
The candidate must not claim geometry-guided exposed-region completion or revisit retrieval alone.

## A. Revealed Contradiction Attribution (RCA)

### Mechanism

When a delayed RGB-D observation conflicts with a hidden-surface prediction, do not immediately
write the residual into scene memory. Route it through three typed hypotheses:

* **scene-surface residual:** a real surface/appearance correction in canonical world coordinates;
* **camera/gauge residual:** an error in pose, reference ray, or metric scale;
* **transient/sensor residual:** moving content, depth failure, or non-repeatable appearance.

Each hypothesis predicts the delayed observation and its reprojection into at least one additional
camera. A likelihood-ratio gate writes only the scene component into the hidden generative belief;
the camera component is sent to a gauge state, and the transient component is rejected or held as
uncertainty. The generator is conditioned on the typed state, so an observation cannot silently
turn a camera error into hallucinated geometry.

This is a different information path from “new frame -> append context” and from a generic robust
SLAM update: the output of the gate determines which hidden-surface hypothesis the camera-conditioned
generator is allowed to consume.

### Closest prior and risk

Closest prior-art families are robust SLAM/data association, C8's slot-0 reference/scale confound,
3D-Belief online belief updates, and INGRID's selective geometry finetuning. The claim must not be
“we detect outliers” or “we keep pose and geometry separate.” It is specifically a typed
contradiction router whose scene branch is evaluated through future generated RGB/depth views.
The prior-art gap is a hypothesis only and requires a focused search before a paper claim.

### Falsifiable predictions

1. Under synthetic perturbations with known labels (true hidden-surface change, pose/gauge error,
   transient object, and depth corruption), RCA routes the residual to the correct type more often
   than an append-only update or a single generic belief update.
2. On true reveal episodes, only the scene branch improves a third held-out camera; pose and
   transient branches do not create geometry drift.
3. After C8 RS canonicalization, RCA rejects residuals that disappear under a gauge change. This
   prevents slot-0 effects from being reported as hidden-surface learning.

### Minimum experiment

Before diffusion, build a CPU/cheap-GPU routing benchmark from eight held-out RGB-D episodes. For
each episode create four sealed perturbations: a real reveal, a known pose perturbation, a temporal
transient, and a depth corruption. Use independent geometry and poses to score scene/gauge/transient
likelihoods, then report a confusion matrix and false scene-write rate. Only if the scene branch
passes the routing threshold should the same event be fed to a frozen denoiser plus zero-initialized
adapter and evaluated on reveal and third cameras.

### Kill condition

Kill RCA if routing cannot distinguish a scene residual from a pose/gauge residual, if the scene
write rate is not lower than append-only, if a generic robust filter matches it, if gains occur
only on the reveal camera, or if the future RGB/depth output is unchanged. No routing accuracy
alone is a method result.

## B. Bidirectional Reveal Deletion (BRD)

### Mechanism

Represent the hidden branch with signed occupancy/appearance hypotheses, including surfaces that
are predicted but not measured. A reveal event can be positive (the predicted surface is observed)
or negative (the camera ray reaches free space or a different surface where the hidden hypothesis
predicted occupancy). Positive evidence corrects the matched hypothesis; negative evidence prunes
or downweights the hallucinated hypothesis through a geometry-derived support mask. The measured
evidence ledger is immutable and the deletion is restricted to predicted-only state.

The information path is therefore **negative geometric evidence -> hypothesis deletion -> future
camera generation**. It tests whether a world model can remove a confident but wrong hidden surface,
not only add geometry or inpaint holes.

### Closest prior and risk

SceneSense already reconciles predicted occupancy with observed free/occupied space
([project](https://arpg.colorado.edu/scenesense/)); ORCA handles occlusion-aware local repair
([arXiv:2609.17450](https://arxiv.org/abs/2609.17450)); and generic 3D completion models use
free-space constraints. Therefore BRD cannot claim “we respect free space” or “we update locally.”
The surviving claim is a delayed negative-reveal transition on a *predictive generative hidden
branch*, measured through reduction of ghost surfaces in future RGB/depth views while preserving
measured and untouched regions.

### Falsifiable predictions

1. In episodes where the pre-reveal model hallucinates a surface, a negative reveal lowers false
   positive occupancy and depth error in a third held-out view more than append-only context and a
   capacity-matched completion adapter.
2. Positive and negative reveals have opposite signed effects on the same hidden belief; the model
   does not simply increase uncertainty or erase the entire region.
3. Measured surfaces and regions with no contradictory evidence remain unchanged within a fixed
   drift tolerance.

### Minimum experiment

Create eight held-out occluder episodes with known RGB-D geometry. For each, construct a positive
   reveal and a matched negative reveal by selecting a target ray bundle whose measured depth is
   free space or a different surface. Compare append-only, generic completion, and BRD under the
   same target cameras and denoising seeds. Measure occupancy precision/recall, ghost-surface rate,
   depth error, third-camera RGB/depth, and untouched-region drift. Do not use the target RGB to
   construct the support masks.

### Kill condition

Kill BRD if negative evidence cannot be identified independently of target RGB, if it merely
   erases all hidden content, if SceneSense/ORCA controls match it, if measured geometry changes,
   or if ghost-surface reduction does not transfer to a third camera.

## C. Shared-Latent Reveal Posterior (SLRP)

### Mechanism

Instead of averaging hidden geometry, maintain a small set of shared latent surface hypotheses
`{h_k, p_k}`. The same `h_k` renders all future camera queries. A delayed reveal scores each
hypothesis by RGB-D reprojection likelihood and reweights `p_k`; it does not synthesize a new mean
that may be inconsistent across cameras. Future views sample from the reweighted posterior, so
the reveal can remove a wrong explanation while preserving calibrated ambiguity.

### Closest prior and risk

GeNVS already samples diverse geometry-consistent views, and 3D-Belief already uses multi-hypothesis
belief inference. SLRP is therefore high risk. It survives only if the shared latent identity,
delayed RGB-D likelihood update, and future-view calibration outperform a mean completion and a
generic multi-hypothesis control under the same sample budget.

### Falsifiable predictions

1. Before reveal, uncertainty calibration and cross-camera identity consistency are better than a
   single mean completion.
2. A reveal reweights hypotheses coherently for both reveal and third cameras, improving proper
   scoring without collapsing all diversity.
3. If a single mean completion matches proper scoring and reappearance error, SLRP adds no value.

### Minimum experiment and kill condition

Use eight held-out episodes, four shared latent hypotheses, and fixed denoising seeds. Compare
SLRP with mean completion, append-only retrieval, and 3D-Belief-like generic particles. Report
proper score, calibration, cross-camera identity consistency, and reappearance RGB/depth. Kill
immediately if it reduces to ordinary multi-hypothesis belief inference or fails to improve a third
camera.

## Decision

RCA and BRD are the only new mechanisms worth bounded feasibility work. SLRP is a reserve because
generic multi-hypothesis 3D belief is already strongly occupied. The next zero-GPU artifact should
be the RCA routing benchmark plus a BRD positive/negative reveal contract. If either cannot beat
the matched generic controls on a third camera, end the method search for this pipeline.
