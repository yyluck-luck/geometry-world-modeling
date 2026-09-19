# Fitted epipolar reward does not identify requested motion

**Answer:** a fitted-F reward can assign ideal consistency to a physically coherent but wrong camera trajectory. A penalty against static output alone does not remove this ambiguity: wrong motion can be fully nonstatic. This is a symbolic identifiability result about the signal, not an observed failure of the authors' trained model or a claim that their stated task promises exact trajectory control.

**Version and status verified now.** *Epipolar Geometry Improves Video Generation Models* has arXiv v1 dated24October2025 and v2 dated17June2026. The current six authors are Orest Kupyn, Théo Uscidda, Marta Tintore Gazulla, Fabian Manhardt, Federico Tombari and Christian Rupprecht. The project still presents the four-author v1 list and labels the work an arXiv preprint. No conference/journal acceptance was established by the primary pages inspected; “accepted to arXiv” in the repository is not a peer-reviewed venue claim. [arXiv version record](https://arxiv.org/abs/2510.21615), [official project](https://epipolar-dpo.github.io/)

**Exact current mechanism.** v2 §3.1 conditions on text and optionally a first image. §3.2 matches SIFT features, estimatesF using normalized eight-point/RANSAC, computes mean Sampson error over correspondences for consecutive uniformly subsampled frame pairs, and ranks same-prompt videos for Flow-DPO. The requested numerical camera trajectory is not an input to this described preference score. §3.1 adds `−λ E[Var_t(x̂0)]`, λ0.001, to discourage static solutions. §3.3 uses static-scene training plus LoRA, KL regularization and timestep weighting; AppendixE explicitly retains matching false positives/negatives and independent-object/nonrigid-motion limitations. This updates the preceding note's deliberately v1-bound reading; v2 has AppendixE, while v1 limitations are AppendixF. [v2 method and limitations](https://arxiv.org/html/2510.21615v2)

**One elementary counterexample — assumptions explicit.** Assume ideal pinhole K=I, identical orientations R=I, a textured static nonplanar scene, noiseless correct visible correspondences sufficient for nondegenerate F estimation, and b≠0. Define relative point coordinates by `X′=X+t`; requested translation is `t_req=(b,0,0)`, but generated views follow `t_alt=(0,b,0)`. Both share the same first view. For a visible point `(X,Y,Z)`, Z>0, the actual correspondence is

`(u,v)=(X/Z,Y/Z)` and `(u′,v′)=(u,v+b/Z)`.

With `F_alt=[t_alt]×`, the fitted epipolar constraint reduces to `u′=u`, so every ideal match has zero Sampson numerator. Yet the requested `F_req=[t_req]×` yields

`x′ᵀ F_req x = b(v−v′) = −b²/Z ≠ 0`.

Thus a nonstatic wrong direction can receive the best fitted-F consistency value while violating the requestedF. Choose nonconstant texture so this moving sequence has positive temporal variation; under ideal clean predictions the static penalty has no criterion selecting the requested direction over the alternative. This does **not** assert that the entire trained DPO model is equally likely to generate both: the prompt, base prior and other objective terms can matter. It proves only that fitted epipolar consistency plus nonstaticness is insufficient to certify requested motion. No samples or numeric experiment were created.

| Contract | Epipolar-DPO preference score | S72 fixed requested geometry |
|---|---|---|
| Inputs available to geometric measurement | Generated frame matches;F fitted to those observations | Real19 anchor and real20–23 controls, accepted physical GT poses, actual cropK and matched points |
| Question | Does the output admit an internally consistent pairwise projective relation? | Do observed correspondences agree with this declared relative pose/imaging approximation? |
| Output/use | Video ranking for model post-training | Observer qualification only at this stage; generated comparison is later |
| Main unresolved inference | Internal consistency cannot certify obeying a separately requested trajectory | High residual rejects a joint scene/match/calibration/timing/pose hypothesis, not camera alone; low residual is not proof |

S72 has additional reference and numerical-camera information, so it is not an equal-input competing method. FreezingF prevents fitting away the specific violation in the example, but does not resolve all epipolar degeneracies, metric translation-scale ambiguity, calibration or scene-change ambiguity. This is conventional geometry, not a new reward or method claim.

**Code availability boundary.** The project links the public official `KupynOrest/epipolar-dpo` repository. Its visible tree includes metrics, model_training, video_generation and wan; metrics includes projective_geometry and video_evaluation. README calls it work in progress and contains a placeholder clone command and inconsistent release dating. Availability is confirmed at page/tree level; this audit neither pins an executable commit nor verifies implementation completeness, paper/code equivalence, checkpoint access or CPU feasibility. No model or repository was installed. [Official repository](https://github.com/KupynOrest/epipolar-dpo)

Source-only conclusion: retain S72 as a bounded diagnostic. Generic epipolar reward plus a static penalty is an existing approach; the identified requested-motion ambiguity motivates careful interpretation, not a validated innovation.
