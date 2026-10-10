# R256 — Rejection review of the S142 follow-up draft

Date: 2026-10-10. Workspace: local Mac checkout. Scope: pre-freeze rejection; S141 outcomes remain unavailable and **UNVERIFIED**.

**Verdict: reject the draft as written. Retain a revised E1 if B improves. Do not automatically launch E2 for every other verdict.** E2 is a legitimate, narrow restoration experiment, but neither identical rays nor CFG 1.2 makes it mathematically incapable of learning. Its decisive comparison is trained C against **both** the raw warp and a frozen generator with the identical C inputs. An eight-clip training-loss decrease is insufficient justification for spending the remaining budget.

The two claim-level defects are an E1 intervention that cannot isolate the claimed mechanism, and an E2 comparison that cannot attribute any gain to training. Both are fixable within this case study. They do not establish that E2 will succeed, that it is novel, or that learned consumption is exhausted.

This review leaves new_method_validated=false and novelty_authorization=NONE unchanged. Only this output file is a deliverable. No GPU, model inference, training, weights/dataset downloads, SSH, submissions, or outside contact is part of this review. Source inspection, public-paper retrieval, and small CPU probes support it. The actual remote S141 source, weights, launch environment, final adapters, and measurements were not verified.

Evidence notation: **ANALYTICAL** covers deductions and every proposed threshold, allocation, or future design constant below; these are not measured performance. **DERIVED** covers arithmetic from inspected records. **MEASURED (synthetic CPU)** covers only the small camera/schedule probe in Appendix A; **MEASURED (archived report)** denotes prior reported results, not a new reproduction. All S142 performance predictions are **UNVERIFIED**. Source hashes and exact probe commands with complete outputs are in the appendices. The recorded checkout commit plus file hashes identify this local snapshot; they do not certify the remote transport or an upstream VMem commit.

Source aliases used in file:line citations:

- Draft = work/S142_followup/PROTOCOL_DRAFT.md.
- R255 = work/agents/CODEX_R255_IDEATION_AFTER_S141.md.
- S141/ = work/S141_finetune/; S140/ = work/S140_warp_guided/; S137/ = work/S137_geometry_baselines/.
- V/ = data/S134_tacc/vmem_src/. In particular pipeline.py, sampling.py, network.py are under V/modeling/; transformer.py is V/modeling/modules/transformer.py; util.py is V/utils/util.py. These names always resolve to this inspected mirror, not the older pinned copy.

## Findings

CRITICAL means the identified implementation or attribution mistake would invalidate the intended result if carried into the run. MAJOR means revise before freezing. LIMITATION means retain a bounded claim and disclose it.

| Issue | Severity | Evidence | Concrete change to the draft |
|---|---|---|---|
| **F1. Pixel permutation tests destructive corruption as well as alignment.** Preserving regional RGB histograms does not preserve local texture, spatial color layout, or cross-frame correspondence. | MAJOR | Draft:16–20; R255:50–54 already admits the out-of-distribution intervention. B encodes the altered RGB with the VAE before combining it with coverage, S141/gen_s141.py:177–182. ANALYTICAL: response to scrambled appearance is not selective evidence for geometry. | Replace the primary intervention with coherent, opposite spatial shifts. Limit the conclusion to registration sensitivity of the warp-appearance path. Keep pixel permutation out of the minimal trial. |
| **F2. An unsuccessful positive test is not rejection of all alignment dependence.** A wide CI can contain the proposed effect. | MAJOR | Draft:19–20; the actual four-way rule is S141/analyze_s141.py:33–40. | Replace “otherwise ... rejected” with “not supported by this intervention”; separately identify when the interval excludes the prespecified practical effect. Do not call uncertainty equivalence or non-use. |
| **F3. A shifted RGB image with an unchanged coverage map has a residual reliability mismatch.** Shifting coverage instead changes a second model input. Neither choice is perfectly selective. | MAJOR | Coverage is a separate averaged input channel, S141/gen_s141.py:178–182; extension appears in both CFG branches, :145–147 and S141/s141_common.py:157–164. | For the minimal appearance-path experiment, keep coverage fixed and explicitly disclose the mismatch. Report a predetermined interior region with stable coverage labels under both shifts. Do not describe the test as confound-free or a physical alternative camera view. |
| **F4. Reusing the intervention warp directory in scoring silently changes the reference.** | CRITICAL implementation hazard | S140/score_s140.py:35–43 reads warp RGB and masks from its warp directory to define B2 and region errors; :46–50 reports those comparisons. | Perturb RGB only in the generation input path. Every arm must be scored against the original immutable warp RGB and original masks. Otherwise the two arms answer different questions. |
| **F5. Correct-arm reuse needs more than adapter SHA, plan and seed.** Cached or stale outputs can invalidate pairing. | MAJOR | Draft:21–22; S141/gen_s141.py:134–154 builds the sampler; :164–165 skips existing filenames; :195–198 records output/adapter hashes. | Carry forward the Amendment-1 identity/completeness checks, plus base weights, source/config, preprocessing, warp/cache, dtype/backend and sampler identities. Use fresh output directories and reproduce an unchanged cell before enabling the intervention. |
| **F6. E2 changes the camera normalization and reference frame.** Duplicate cameras are not automatically singular, but the context distribution and slot-0 radius change. | MAJOR | pipeline.py:1099–1120 centers the whole stack and uses the first centered camera to set scale; :1136–1140 uses the first camera as the Plücker reference. S141/s141_common.py:150–154 forms that stack. | Freeze ordering, actual target cameras/K, original normalization and convention handling. Record scale, slot-0 radius, validity mask and finite transformed cameras. State that C is a complete input-package change. |
| **F7. Every matched target gets effective CFG 1.2, but CFG is not necessarily negligible.** | MAJOR omission | V/configs/inference/inference.yaml:19–23; sampling.py:205–218,238–247,279–299,450–453. C's unconditional dictionary removes warp replacement and CLIP, pipeline.py:1153–1157,1170–1185. B retains its warp branch in both dictionaries, S141/gen_s141.py:145–147. | State effective target CFG=1.2 and use it for both C and C0. The expression is c+0.2(c−u); its effect depends on c−u. Do not call C and B a guidance-matched channel-placement comparison. |
| **F8. Identical rays do not clamp the target to the warp or make copying the universal training optimum.** | MAJOR reasoning correction | pipeline.py:1143–1156 gives clean replacement only to contexts; sampling.py:179–185 applies it. The context indicator also enters the network, network.py:226–235. TimeMix mixes frames at a common spatial index, transformer.py:146–155. S141/train_s141.py:117–119 supervises real target ε. | Describe an accessible copying shortcut and a pretrained behavior to test, not a mathematical impossibility of refinement. Keep target replacement masks zero. |
| **F9. Fake camera offsets or retaining source cameras for target-view images would introduce inconsistent geometry.** | MAJOR if adopted | Plücker maps are built from the supplied cameras/K, pipeline.py:1136–1179; util.py:154–175. A small rotation with unchanged center may still satisfy the close-frame rule, sampling.py:205–213. | Keep the actual camera/K at which each warp was rendered. To study a real offset, rerender at the offset camera in a separate protocol; do not add such an arm here. If the issue were CFG alone, an explicit guidance override would be clearer than falsified camera metadata, but no override is needed for C versus C0. |
| **F10. The “easy at low sigma” explanation has the noise dependence backwards for imperfect copying.** | MAJOR | S141/train_s141.py:61–68; sampling.py:79–87,174–185. ANALYTICAL: copy-warp ε-MSE equals latent warp error divided by σ². Appendix A verifies the actual schedule on CPU. | Correct the explanation; report per-sigma losses and corresponding latent reconstruction errors. Do not predict that the gate necessarily passes. |
| **F11. An eight-clip training gate tests fitting/wiring, not generalizable refinement.** | MAJOR | Draft:32–33; fixed monitor-noise evaluation exists at S141/train_s141.py:75–85; training samples fresh noise and uniform indices at :118–119. | Do not use a training-loss percentage as the sole spending gate. Use one bounded pilot on the ordinary training stream and a prespecified small monitor generation comparison against C0 and W, as specified below. |
| **F12. A partial C implementation would leak the old raw-source representation into unconditional training.** | CRITICAL implementation hazard | S141/train_s141.py:54–58 returns original source latents in z separately from conditioning. With unconditional replacement zero, :61–67,117 exposes these noisy source slots. pipeline.py:1157,1181–1185 defines that unconditional dictionary. | Change both conditioning **and z[:4]** to warp latents. Context CLIP and camera/K must also come from the warped target-view representation. Audit conditional and unconditional inputs separately. This is a representation-boundary violation, not a finding of chess-target leakage in existing S141. |
| **F13. C loses original views, explicit coverage, source-derived CLIP, and B's always-present warp conditioning.** These changes accompany the new clean-context route. | MAJOR attribution limitation | Draft:27–31; S141/s141_common.py:157–164; pipeline.py:1125,1143–1185; S141/train_s141.py:117. All pixels, including nearest-filled holes, receive the context-slot clean mask. | Rewrite the hypothesis as rendered-image restoration by this complete package. Coverage remains evaluation metadata. Do not say a C win shows replace adapts more readily than concat, or a loss rejects replace. |
| **F14. C−B2 alone cannot establish that training helped. Old S137c is not the matched frozen comparator.** | CRITICAL attribution gap | Draft:35–38; S137/RESULT.md:3–8,40–55 describes a different panel and v1-map warp reference. | Generate frozen C0 on the actual C inputs, same panel, seeds, hardware and guidance. Require C to beat both W and C0 before claiming useful trained refinement. Include a deterministic VAE warp round-trip as a cheap descriptive control. |
| **F15. Similar PSNR-to-GT does not certify literal copying.** | MAJOR evidence correction | MEASURED (archived report): S137/RESULT.md:44 reports warp4_fill−B2 at +0.000 dB, CI [−0.044,+0.053]; :52–54 calls this copying. Those scores alone do not prove identical output pixels. | Treat S137c as evidence of no measured added PSNR on its panel and a copying hypothesis. Report direct C0-to-W and C0-to-VAE-round-trip residuals on the new panel before using literal-copy language. |
| **F16. C is not an executable variant yet; default/resume behavior can violate the recipe.** | MAJOR | S141/train_s141.py:18–21 accepts A/B and defaults to 3000 steps; :89–101 resumes checkpoint/optimizer/RNG state. S141/gen_s141.py:119–124 checks variant/rank. | Implement and hash an explicit C path before execution; export STEPS=10000 explicitly. Gate and full-run directories must be separate and fresh. Verify step zero and final step, exact adapter tensor schema, finiteness and cache identities. Preserve S141/PROTOCOL.md:78–84 hardening. |
| **F17. The branch rule is deterministic but conflates “not demonstrated” with failure and overcommits compute.** | MAJOR | Draft:7–12; S141/analyze_s141.py:38–40 gives INCONCLUSIVE a distinct meaning. R255:18–21 says complete missing registered cells, then report uncertainty. | Deterministic allocation is not itself statistically invalid, but INCONCLUSIVE is not evidence B failed. Use the explicit conservative branch table below; do not add seeds until significance or rescue an execution failure with C. |
| **F18. Part of R255 is now stale: the memory-versus-static experiment is already in Amendment 1.** | MAJOR continuity correction | R255:54 calls it missing; S141/PROTOCOL.md:85–89 adds B_static and difference-in-differences; S141/analyze_s141.py:70–78 implements them. | Analyze those already specified exploratory cells. Do not repeat the block as a new follow-up or promote it to a primary. E1 still only intervenes on one path. |
| **F19. Uncertainty and exposure limit both experiments.** Windows share history; seeds do not create new scenes; branch choice uses an exposed panel. | LIMITATION | S141/PROTOCOL.md:93–99; work/agents/SELF_AUDIT_S139.md:33–34; work/S139_crossseq_revisit/PROTOCOL.md:40–42; Draft:42–44. | Keep window-level analysis for continuity, report all pair means and descriptive pair-cluster uncertainty, and label it an exposed-panel follow-up. No population, novelty, untouched-confirmation or temporal-quality claim follows. |
| **F20. The budget omits necessary C0 inference and lacks a hard total stop. An unused H800 slot is acceptable.** | MAJOR | Draft:23,30–37; S141/PROTOCOL.md:43–49 gives only a short smoke timing; archived timing arithmetic is independently reproduced in Appendix B. | Budget pilot, caching, C and C0 inference, validation and failures together. Cap the follow-up at the stated total RTX GPU-hours, summed across cards. Do not add a second training seed or another model merely because a device is free. |
| **F21. “Failure ends learned-consumer work” must be a management rule.** | MAJOR wording | Draft:39; R255:64–68 already limits the scientific inference. | State “end this project's current learned-consumer search under this budget and write up.” A failed early pilot, full recipe or negative C result does not prove all learned consumption mechanisms fail. |

## Mechanics and gate analysis

### True target-pose context is an easy correspondence, not an invalid network input

Let the ordered target cameras be q0…q3. C supplies the stack [q0,q1,q2,q3,q0,q1,q2,q3], with matching intrinsics in corresponding slots. The original history cameras disappear from normalization. The code centers the retained positions using its median/quantile filter and then returns scale 2.0 when the first centered camera is sufficiently near zero, otherwise 2.0/r0+0.01. With ordinary retained cameras, duplicated target positions center on the target mean; they do not all collapse just because the stack is duplicated. If the whole trajectory is stationary, the fallback handles zero center radius. A first camera very near, but outside, the tolerance can instead produce a large scale. No inspected data establish that this happens in the proposed clips. (pipeline.py:1099–1120; S141/s141_common.py:148–154.)

The first context camera is now q0, so it also defines the Plücker reference. Corresponding qj slots have equal ray maps when their K agrees; different qj need not share rays. The reference camera's ray moments vanish in exact arithmetic, but its ray directions remain present. These are coordinate facts, not singular attention or missing target identity. (pipeline.py:1129–1141; util.py:154–175.)

The multiview guidance rule uses minimum rotation distance, minimum translation distance and an exact K match. It does not require those three minima to come from the same reference, although C has an exact corresponding reference and therefore satisfies all three anyway. All targets receive 1.2 in the inspected configuration. The scalar guidance is

    D_guided = D_u + 1.2 (D_c − D_u)
             = D_c + 0.2 (D_c − D_u).

Thus extrapolation beyond the conditional output is smaller than with scale 2.0; the conditional information itself has not been switched off. Whether the remaining correction is small is unmeasured. C's u branch drops clean warp contexts/CLIP, whereas B's warp branch survives there. This difference matters to C–B attribution, but is controlled by comparing C and C0 under the same rule. (sampling.py:205–218,238–247; pipeline.py:1153–1185; S141/gen_s141.py:145–147.)

Replacement acts on context inputs before denoising, not on target outputs: its mask is [1,1,1,1,0,0,0,0]. Noisy targets and clean contexts also have different mask channels. A same-location temporal path makes transferring aligned evidence straightforward, but neither the attention code nor the mask forces copying. An imperfect warp incurs target-label error and can be corrected by a trainable network. Whether this small LoRA can learn that correction is precisely unknown. (pipeline.py:1143–1167; sampling.py:179–185; transformer.py:146–155; S141/train_s141.py:119.)

**Keep physically correct target cameras.** A metadata-only offset or original source pose would make target-view RGB inconsistent with its ray map. A genuinely rerendered offset would be a different input-quality experiment. It is unnecessary to introduce either just to evade the CFG rule.

### The loss shortcut is cheap at high sigma

Write a target latent as z, its input-derived warp latent as w, and the training input as x=z+σε. The unpreconditioned denoised estimate is x−σε̂. A predictor that exactly returns w therefore has

    ε̂_copy = (x−w)/σ
    ε̂_copy−ε = (z−w)/σ
    MSE(ε̂_copy, ε) = MSE(z,w)/σ².

This is an **ANALYTICAL** identity for this implementation, not a claim that the network learns that function. Imperfect copying is cheap in ε units at high sigma; it becomes expensive at low sigma. If w=z exactly, copying solves noise prediction at any nonzero sigma. Here w is an imperfect input-derived rendering, not the target label. For arbitrary predictions, σ² times ε-MSE equals denoised latent MSE for the same noisy target and sigma. Neither quantity alone is an end-to-end generated RGB quality measurement. (S141/train_s141.py:61–68,118–119; sampling.py:79–87,174–185.)

The inspected fixed evaluation indices [50,200,400,600,800,950] are not six equally spaced noise magnitudes. **MEASURED (synthetic CPU)**, Appendix A: their sigmas range from approximately 0.407 to 63.640 under the actual extracted discretizer. This makes a single average particularly poor evidence for the proposed explanation. Low-noise target inputs themselves also carry target signal; lower loss need not arise from better use of the warp.

The familiar ε-prediction training objective is supported by Ho, Jain and Abbeel, **arXiv:2006.11239, “Denoising Diffusion Probabilistic Models,” §3.4, Eq. (14)**. The scaling identity above follows from this repository's implementation, not an assumption that its schedule matches that paper. [Verified paper](https://arxiv.org/html/2006.11239v2#S3.SS4)

The original eight-clip check is meaningful as an optimization check if its noise, indices and aggregation are frozen. It can pass by overfitting or fail because a good initial model has little reducible loss; neither outcome settles C's useful refinement ability. “It will pass trivially” is unsupported. Do not use it as the sole full-run spending gate.

## Corrected branch selection

Freeze this policy before opening S141 outcomes. These are **ANALYTICAL project allocation choices**, not claims that A success is mathematically necessary for C.

| Valid completed S141 outcome | Single action |
|---|---|
| Execution invalid or registered cells missing | Repair/complete only the original S141 contract; do not interpret missing cells as a negative result and do not start S142. |
| PRIMARY_B=IMPROVES, any A verdict | Run corrected E1 only. Report S141 SSIM/trade-offs and its already specified exploratory memory contrasts alongside it. |
| PRIMARY_B=INCONCLUSIVE | Report uncertainty and write up. No E2 and no significance-driven extra seeds. |
| PRIMARY_B=WORSENS, any A verdict | Prefer stop/write. Preserve any A gain. Fusion was R255's optional choice when A improved, but adding its training outputs and new gate is not part of this S142 branch. Do not serially open E3 after rejecting E2. |
| PRIMARY_B=NO_MATERIAL_CHANGE and PRIMARY_A=IMPROVES | Permit the corrected E2 pilot below as the sole remaining challenger; continue only if its spending gate and total budget pass. |
| PRIMARY_B=NO_MATERIAL_CHANGE and A has any other verdict | Stop/write. Neither registered label proves equivalence or universal failure. |

This is deliberately narrower than R255's “one last trial if required” allowance. It spends on mechanistic clarification of a success, and on one alternative input package only when there is already positive evidence that this adaptation budget can help the consumer. Choosing stop/write in every nonpositive-B branch is also defensible. The revised policy is a recommendation in this review, not an amendment to the existing S141 experiment.

The H800 slot need not be used. If a later separately fixed transfer block is worth doing, it must generate every compared model control on that same hardware; it cannot substitute an H800 C output into a comparison with a 3090 C0/B output. Keep that block outside this minimal S142 plan rather than leaving an unspecified expansion.

## Corrected minimal E1 specification

**Question.** For the fixed final B that beat the original B2 warp, does modest coherent misregistration of warp RGB reduce its measured reconstruction quality? The target claim is registration sensitivity of this appearance-conditioning path.

1. **Eligibility and identities.** Use valid complete S141 PRIMARY_B=IMPROVES, the final B adapter, the original chess mem_vmem plan and S140 warps, all target slots, RTX 3090 and seeds 3,4,5,6. Freeze source/config/weight/adapter/input hashes and the original scorer. Reuse B(correct) only after complete receipt matching and one exact unchanged generation replay. Fresh intervention directories; no filename-only reuse. This extends S141/PROTOCOL.md:78–84 and S141/gen_s141.py:164–198.

2. **Two fixed intervention arms.** At the 576×576 RGB model grid, shift every nearest-filled warp horizontally by +16 pixels in one arm and −16 pixels in the other. Use the same sign/magnitude across the four target frames of each clip, all windows and all generation seeds. Define positive shift by W_plus[y,x]=W[y,reflect(x−16)]. For width L, reflect(t)=−t when t<0, t when 0≤t<L, and 2L−2−t when t≥L; this suffices for these offsets. Negative shift uses x+16. No circular wrap, interpolation, per-frame random transform or parameter sweep.

3. **Paths held fixed.** Apply the shift before the same VAE encoding. Keep the original coverage tensor, raw contexts, their CLIP, camera/K, masks, adapter and noise fixed. Supply changed warp latents to both CFG dictionaries. Transform before per-context caching or include the intervention identity and warp list in the cache key; the current generator caches by ctx_group, S141/gen_s141.py:170–184. Re-encode changed RGB; do not reuse the original latent or merely roll latent pixels.

4. **Scoring and estimand.** All arms use the **original** warp directory and original masks in the scorer. Preserve S140's four-target pooled-SSE PSNR per generation, then average the four seeds per window. Primary effect:
   
       d_window = mean_seed[PSNR(B_correct)
                    − (PSNR(B_shift_plus)+PSNR(B_shift_minus))/2].
   
   Average scores, not generated images and not latent predictions. Keep the proposed mean ≥+0.2 dB and lower window-bootstrap CI >0 rule, with 10,000 replicates and rng 0. Report both directions separately. Restore R255's retention guard: no negative mean effect in two of the three trajectory pairs. These constants are proposed decision rules, not measured effects. Scoring aggregation is at S140/score_s140.py:30–45; window/seed aggregation and bootstrap at S141/analyze_s141.py:22–40.

5. **Required diagnostics.** Report SSIM, original covered/uncovered PSNR, every pair mean, and descriptive pair-cluster uncertainty. Add a secondary common interior region: pixels at least 32 pixels from all image boundaries whose original coverage label equals the labels at x−16 and x+16. Compute separate stable-covered/stable-uncovered effects there, using masks determined from inputs alone. Report their pixel counts and undefined cases; do not exclude windows from the primary based on this diagnostic. This reduces direct boundary/label-crossing explanations; it cannot remove the VAE's wider receptive-field effects or make the perturbation physically valid.

6. **Interpretation and stop.** A positive result supports “B's output quality depends on registration of warp appearance under this fixed perturbation.” It does not distinguish aligned copying from geometric reasoning, isolate all mask effects, prove benefit from retrieved history, or establish novelty. A threshold miss is absence of supporting evidence from this intervention. If the CI upper bound is below +0.2 dB, it excludes that practical effect size for this intervention and panel only. The original B−W gain remains whatever S141 measured. Do not tune the shift or add a permutation after seeing the result.

7. **Budget.** ANALYTICAL count: two new arms ×24 windows ×4 seeds =192 generations, plus the single unchanged replay. DERIVED baseline-equivalent time is approximately 1.93 GPU-hours for the two arms (Appendix B), with a **2–4 GPU-hour planning allowance** including overhead; this is not measured B timing. Stop after this experiment and write up.

A joint shift of RGB and coverage would instead test misregistration of the complete warp condition. That is a reasonable different estimand, but changes availability as well as appearance. The fixed-mask version above is the smaller revision of the current E1 question. Neither version warrants the stronger phrase “B uses aligned geometry” without qualifications.

## Corrected minimal E2 specification

**Question.** Can a trained, source-derived target-view restoration package improve over both the renderer and the same package with frozen weights? C is a challenger baseline, not a proposed novel method or a causal replace-versus-concat experiment.

### Inputs, cameras and conditioning

Use the exact hashed S141 clip list and its existing input-derived nearest-filled warp RGB/latent caches. Original source images may enter warp construction only. Target **poses** are permitted conditioning; target RGB appears only as the supervised training target or in the scorer. The inspected warp constructor reads context RGB/depth estimates and target poses, S141/warps_s141.py:79–97. Verify cache identity and source/target disjointness per clip before reuse; the local script cannot establish remote cache provenance.

For each clip j, let w0…w3 be VAE latents of its four warped RGBs and z0…z3 its ground-truth training target latents:

    clean training stack = [w0,w1,w2,w3,z0,z1,z2,z3]
    context RGB/CLIP      = the four warped RGBs, in target order
    camera stack          = [q0,q1,q2,q3,q0,q1,q2,q3]
    K stack               = matching rendered target intrinsics
    conditional replace  = [w0,w1,w2,w3,0,0,0,0]
    replacement mask     = [1,1,1,1,0,0,0,0].

Preserve the existing convention transformation, normalization, target ordering and CLIP aggregation. Supply per-warp CLIP embeddings to get_cond, which averages them (pipeline.py:1125,1150). No extra branch; no coverage channel; the whole nearest-filled image is treated as clean context. Retain S141 A's conditional-drop probability: on an unconditional training example, first noised slots are **warp latents**, with zero replace/CLIP/indicator and retained camera features. They must never revert to original-source latents. At generation, initialize the sampler as usual; do not put GT target latents anywhere in inference. The inherited unconditional training/sampling context-trajectory mismatch remains disclosed (S141/PROTOCOL.md:95–96; util.py:712–729).

Use rank/alpha 16 LoRA on all existing Attention q/k/v/out projections, with the S141 A optimizer, warmup, fresh-noise distribution, bf16 and seed 0 recipe; trainable tensors and scaling are specified in S141/s141_common.py:82–94,109–122 and S141/train_s141.py:21–24,44–49,117–121. Implement an explicit C variant before running. Retain effective target CFG 1.2 for both C and C0; no fake pose offsets and no CFG sweep.

### Fidelity and one bounded spending gate

Before training, verify zero-init C against an adapter-free model with the **same C inputs**, not against base_mem. Verify condition tensors, matching ray pairs, target masks, finite normalization and input isolation in both c and uc separately. Byte-identical outputs do not excuse two implementations sharing the same wrong inputs. The zero-init LoRA identity is implemented in S141/s141_common.py:89–94.

**Replace the eight-clip/500-step overfit gate with one disposable pilot on the normal training stream.** Use the first 500 optimization steps of the seed-0 full-data recipe, with fresh training noise. No eight-clip training restriction. Record fixed-noise diagnostic loss at step 0 and 500 on eight deterministic training clips encountered in those steps, selected by sorted clip ID; freeze those IDs before training. Use indices [50,200,400,600,800,950] and evaluation-noise seed 1000*k+j for ordered clip k and index j, in a separate RNG so diagnostics do not change training draws. Report conditional per-index ε-MSE, σ²ε-MSE, and the analytical warp-copy residual. An arbitrary aggregate 10% reduction is neither required nor sufficient to proceed.

At pilot step 500, use the exact final-evaluation sampler to generate C500 and C0 with generation seed 3 on **eight fixed monitor clips**. Choose two static and two memory clips from each held-out current sequence, lowest clip IDs in each stratum. Appendix C verifies that the frozen manifest supplies these:

- office/seq-10 static: c02006, c02016; memory: c02000, c02003.
- redkitchen/seq-14 static: c02001, c02002; memory: c02009, c02010.

The monitor subset becomes development data for S142. Do not call it untouched validation. Use the scorer's four-target aggregate per clip and original warp coverage.

**ANALYTICAL spending rule:** continue only if both mean PSNR(C500−W) and mean PSNR(C500−C0) are ≥+0.2 dB; each contrast is positive in at least five of eight clips; and each corresponding mean SSIM difference is >−0.01. Require finite losses, gradients, parameters and outputs, intended adapters changing, and frozen weights unchanged. All conditions are conjunctive. One pilot, one checkpoint, one scoring pass; no adjustment or retry because the scores disappoint. Loss diagnostics cannot override the generation gate.

Report W, its VAE round-trip D(E(W)), C0 and C500 against GT and direct RGB residuals to W/round-trip, plus covered/uncovered results. These descriptive checks separate VAE effects, frozen-generator changes and trained changes. They do not add gate exceptions.

This is intentionally conservative budget triage. It can falsely reject a recipe that would learn later; failure means **insufficient early evidence to justify this budget**, not that a full 10,000-step run failed or C cannot learn. A pass on this small development subset is not generalization evidence.

### One full run and required comparisons

If and only if the pilot and budget gates pass, discard the pilot's training state and restart from the base in a fresh full-run directory. Explicitly set 10,000 steps. Do not resume the pilot's adapter, optimizer, scheduler, RNG or data position. Record step-zero and final-adapter identities. Preserve the final-adapter-only policy; no checkpoint selection.

Generate trained C and frozen C0 on the original 24 chess windows, seeds 3–6, RTX 3090, identical C input representation and sampler. C0 is a required full-panel comparator, not a selected monitor visualization. Raw W is deterministic; B_mem, A_mem and base_mem use verified existing same-site outputs. Require exact unique planned window/seed cells and output receipts; missing cells abort analysis rather than shrinking the panel.

For **useful trained refinement**, require both paired window-mean contrasts C−W and C−C0 to satisfy mean ≥+0.2 dB and lower 95% window-bootstrap CI >0, with the same fixed bootstrap and no pair-sign reversal in two of three pairs for either contrast. Both must pass; neither can replace the other. The joint rule is intentionally stronger than merely detecting any positive C−C0 effect. If C beats W but does not demonstrably beat C0, report only a useful complete input package, with training contribution unresolved.

Report C−B_mem, C−A_mem and C−base_mem as secondary comparisons, with their input/guidance differences disclosed. Report SSIM, original covered/uncovered effects, per-pair results, descriptive pair-cluster uncertainty, and C/C0 distances to W and its VAE round-trip. A material SSIM decline (mean ≤−0.01 and upper CI <0 against either W or C0) restricts any PSNR success to a reconstruction trade-off. No claim about temporal consistency follows from these frame metrics.

End this budgeted search and write up after the final evaluation, regardless of sign. No rank, CFG, loss, offset-pose, larger-context or architecture rescue.

### Total resource boundary

ANALYTICAL count for the revised E2: 16 pilot generations plus 192 final C/C0 generations, with an additional unchanged fidelity comparison and inexpensive VAE/control work. **DERIVED** baseline-equivalent inference for those 208 generations is about 2.09 GPU-hours; **DERIVED, UNVERIFIED extrapolation** of 10,500 steps at the protocol's short-smoke rate is 4.025 GPU-hours. Their approximately 6.11-hour sum excludes validation, cache preparation, I/O, contention and fidelity work. It is not a measured C runtime. Timing sources and arithmetic are in Appendix B; the smoke report is S141/PROTOCOL.md:43–49.

Reserve about one GPU-hour for the disposable pilot and about three for paired final inference/control work, leaving about six for full training and its overhead inside a hard **10 RTX 3090 GPU-hour total**, summed across cards. Before full training, use the pilot's recorded component times to verify that the complete fixed run and all controls fit. If they do not, stop before the full run; do not silently shorten it or drop C0. If the hard cap interrupts a full run, report a budget-truncated execution, not the registered final scientific verdict. No second training seed or H800 expansion is included.

### Literature and interpretation boundary

Warp-conditioned learned view refinement has prior art. **arXiv:2409.02048, “ViewCrafter: Taming Video Diffusion Models for High-fidelity Novel View Synthesis,” §III-C, Eq. (3)** conditions a video diffusion model on encoded point-cloud renders and reference imagery, using channel concatenation of render latents. C's clean-context route and removal of raw references differ from that implementation; this establishes a comparison axis, not novelty. The current review does not claim an exhaustive prior-art search or exact equivalence. [Verified paper](https://arxiv.org/html/2409.02048v1#S3.SS3)

The reportable contribution of these follow-ups is narrower: a measured sensitivity test of a successful fixed predictor, or a controlled case study of whether one restoration recipe improves over its own frozen and geometric controls. Those questions are worth reporting even when the answer is negative.

## Verification scope and handoff

The camera probe executes extracted repository functions on synthetic CPU tensors; it does not import the full pipeline, load models or exercise attention/sampling. It confirms the matched-ray/mask/CFG mechanics and schedule, not training dynamics or GPU numerical fidelity. Two initial probe attempts failed for local harness dependencies; their exact commands and full errors are retained below. No package was installed.

No repository test suite or linter was run: the only change is this prose review, with isolated CPU checks for disputed source behavior. The initial untracked work/agents/prompts/R256_FULL.md belongs to the concurrent workflow and is left alone.

Changed file: work/agents/CODEX_R256_S142_DRAFT_REJECTION.md only. Follow-up for the main session: revise/freeze S142 before opening results, verify S141 artifacts, apply the chosen branch once, and keep the manuscript claims within the measured comparisons. This review does not modify the draft, research ledger or any existing deliverable.

## Appendix A — CPU mechanics and schedule verification

### A1. Initial environment failure; no model or experiment ran

Exact command (repository root):

```bash
.venv/bin/python -B - <<'PY'
import ast, math
from pathlib import Path
from types import SimpleNamespace
from typing import Union
import numpy as np
import torch
from einops import repeat
root = Path('data/S134_tacc/vmem_src')
ns = dict(torch=torch, np=np, repeat=repeat, Union=Union, DEFAULT_FOV_RAD=math.pi/3)
def extract(path, names, cls=None):
    tree = ast.parse(path.read_text())
    nodes = tree.body if cls is None else next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == cls).body
    selected = [n for n in nodes if getattr(n, 'name', None) in names]
    assert len(selected) == len(names)
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), 'exec'), ns)
extract(root/'modeling/sampling.py', ['get_camera_dist', 'append_zero', 'make_betas', 'generate_roughly_equally_spaced_steps', 'EpsScaling', 'DDPMDiscretization', 'DiscreteDenoiser', 'MultiviewScaleRule'])
extract(root/'utils/util.py', ['to_hom', 'to_hom_pose', 'get_image_grid', 'img2cam', 'cam2world', 'get_center_and_ray', 'get_plucker_coordinates'])
extract(root/'modeling/pipeline.py', ['get_translation_scaling_factor', 'get_cond'], 'VMemPipeline')
carrier = SimpleNamespace(camera_scale=2.0, device=torch.device('cpu'), dtype=torch.float32, config=SimpleNamespace(model=SimpleNamespace(num_frames=8)))
poses = torch.eye(4).repeat(4, 1, 1)
poses[:, 0, 3] = torch.tensor([0., .1, .2, .3])
scale, centered = ns['get_translation_scaling_factor'](carrier, torch.cat([poses, poses]).clone())
print('device', centered.device, 'torch', torch.__version__)
print('duplicate_pose_scale', round(float(scale), 6))
K = torch.tensor([[702., 0., 288.], [0., 702., 288.], [0., 0., 1.]]).repeat(8, 1, 1)
mask = torch.tensor([True]*4 + [False]*4)
lat = torch.arange(4*4*2*2, dtype=torch.float32).reshape(4,4,2,2)
# Use intrinsics scaled to the synthetic 16x16 image grid (latent 2x2).
Ksmall = K.clone(); Ksmall[:, :2] *= 16/576
cond = ns['get_cond'](carrier, lat, centered, Ksmall, scale, torch.ones(4, 8), mask)
print('paired_plucker_max_abs', float((cond['c']['dense_vector'][:4] - cond['c']['dense_vector'][4:]).abs().max()))
print('cfg_per_slot', ns['MultiviewScaleRule'](1.2)(2.0, cond['all_c2ws'], cond['all_Ks'], mask).tolist())
print('conditional_replace_mask', cond['c']['replace'][:, -1, 0, 0].tolist())
print('unconditional_replace_nonzero', int(torch.count_nonzero(cond['uc']['replace'])))
print('unconditional_clip_nonzero', int(torch.count_nonzero(cond['uc']['crossattn'])))
coincident = torch.eye(4).repeat(8,1,1)
s0, p0 = ns['get_translation_scaling_factor'](carrier, coincident)
print('coincident_scale', float(s0), 'finite', bool(torch.isfinite(p0).all()))
den = ns['DiscreteDenoiser'](ns['DDPMDiscretization'](), device='cpu')
for i in [50,200,400,600,800,950]:
    s = float(den.sigmas[i])
    print('sigma_index', i, 'sigma', format(s,'.8f'), 'copy_eps_mse_per_unit_latent_mse', format(1/s**2,'.8f'))
print('No model, weights, images, training, or sampler trajectory executed.')
PY
```

Complete output; exit code 1:

```text
Traceback (most recent call last):
  File "<stdin>", line 7, in <module>
ModuleNotFoundError: No module named 'einops'
```

### A2. Harness annotation dependency failure; no model or experiment ran

Exact command (repository root):

```bash
.venv-cut3r/bin/python -B - <<'PY'
import ast, math
from pathlib import Path
from types import SimpleNamespace
from typing import Union
import numpy as np
import torch
from einops import repeat
root = Path('data/S134_tacc/vmem_src')
ns = dict(torch=torch, np=np, repeat=repeat, Union=Union, DEFAULT_FOV_RAD=math.pi/3)
def extract(path, names, cls=None):
    tree = ast.parse(path.read_text())
    nodes = tree.body if cls is None else next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == cls).body
    selected = [n for n in nodes if getattr(n, 'name', None) in names]
    assert len(selected) == len(names)
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), 'exec'), ns)
extract(root/'modeling/sampling.py', ['get_camera_dist', 'append_zero', 'make_betas', 'generate_roughly_equally_spaced_steps', 'EpsScaling', 'DDPMDiscretization', 'DiscreteDenoiser', 'MultiviewScaleRule'])
extract(root/'utils/util.py', ['to_hom', 'to_hom_pose', 'get_image_grid', 'img2cam', 'cam2world', 'get_center_and_ray', 'get_plucker_coordinates'])
extract(root/'modeling/pipeline.py', ['get_translation_scaling_factor', 'get_cond'], 'VMemPipeline')
carrier = SimpleNamespace(camera_scale=2.0, device=torch.device('cpu'), dtype=torch.float32, config=SimpleNamespace(model=SimpleNamespace(num_frames=8)))
poses = torch.eye(4).repeat(4, 1, 1)
poses[:, 0, 3] = torch.tensor([0., .1, .2, .3])
scale, centered = ns['get_translation_scaling_factor'](carrier, torch.cat([poses, poses]).clone())
print('device', centered.device, 'torch', torch.__version__)
print('duplicate_pose_scale', round(float(scale), 6))
K = torch.tensor([[702., 0., 288.], [0., 702., 288.], [0., 0., 1.]]).repeat(8, 1, 1)
mask = torch.tensor([True]*4 + [False]*4)
lat = torch.arange(4*4*2*2, dtype=torch.float32).reshape(4,4,2,2)
# Use intrinsics scaled to the synthetic 16x16 image grid (latent 2x2).
Ksmall = K.clone(); Ksmall[:, :2] *= 16/576
cond = ns['get_cond'](carrier, lat, centered, Ksmall, scale, torch.ones(4, 8), mask)
print('paired_plucker_max_abs', float((cond['c']['dense_vector'][:4] - cond['c']['dense_vector'][4:]).abs().max()))
print('cfg_per_slot', ns['MultiviewScaleRule'](1.2)(2.0, cond['all_c2ws'], cond['all_Ks'], mask).tolist())
print('conditional_replace_mask', cond['c']['replace'][:, -1, 0, 0].tolist())
print('unconditional_replace_nonzero', int(torch.count_nonzero(cond['uc']['replace'])))
print('unconditional_clip_nonzero', int(torch.count_nonzero(cond['uc']['crossattn'])))
coincident = torch.eye(4).repeat(8,1,1)
s0, p0 = ns['get_translation_scaling_factor'](carrier, coincident)
print('coincident_scale', float(s0), 'finite', bool(torch.isfinite(p0).all()))
den = ns['DiscreteDenoiser'](ns['DDPMDiscretization'](), device='cpu')
for i in [50,200,400,600,800,950]:
    s = float(den.sigmas[i])
    print('sigma_index', i, 'sigma', format(s,'.8f'), 'copy_eps_mse_per_unit_latent_mse', format(1/s**2,'.8f'))
print('No model, weights, images, training, or sampler trajectory executed.')
PY
```

Complete output; exit code 1:

```text
Traceback (most recent call last):
  File "<stdin>", line 16, in <module>
  File "<stdin>", line 15, in extract
  File "data/S134_tacc/vmem_src/modeling/sampling.py", line 138, in <module>
    class DiscreteDenoiser(object):
  File "data/S134_tacc/vmem_src/modeling/sampling.py", line 168, in DiscreteDenoiser
    network: nn.Module,
             ^^
NameError: name 'nn' is not defined. Did you mean: 'np'?
```

### A3. Corrected CPU extraction harness; source functions unchanged

Exact command (repository root):

```bash
.venv-cut3r/bin/python -B - <<'PY'
import ast, math
from pathlib import Path
from types import SimpleNamespace
from typing import Union
import numpy as np
import torch
from einops import repeat
root = Path('data/S134_tacc/vmem_src')
ns = dict(nn=torch.nn, torch=torch, np=np, repeat=repeat, Union=Union, DEFAULT_FOV_RAD=math.pi/3)
def extract(path, names, cls=None):
    tree = ast.parse(path.read_text())
    nodes = tree.body if cls is None else next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == cls).body
    selected = [n for n in nodes if getattr(n, 'name', None) in names]
    assert len(selected) == len(names)
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), 'exec'), ns)
extract(root/'modeling/sampling.py', ['get_camera_dist', 'append_zero', 'make_betas', 'generate_roughly_equally_spaced_steps', 'EpsScaling', 'DDPMDiscretization', 'DiscreteDenoiser', 'MultiviewScaleRule'])
extract(root/'utils/util.py', ['to_hom', 'to_hom_pose', 'get_image_grid', 'img2cam', 'cam2world', 'get_center_and_ray', 'get_plucker_coordinates'])
extract(root/'modeling/pipeline.py', ['get_translation_scaling_factor', 'get_cond'], 'VMemPipeline')
carrier = SimpleNamespace(camera_scale=2.0, device=torch.device('cpu'), dtype=torch.float32, config=SimpleNamespace(model=SimpleNamespace(num_frames=8)))
poses = torch.eye(4).repeat(4, 1, 1)
poses[:, 0, 3] = torch.tensor([0., .1, .2, .3])
scale, centered = ns['get_translation_scaling_factor'](carrier, torch.cat([poses, poses]).clone())
print('device', centered.device, 'torch', torch.__version__)
print('duplicate_pose_scale', round(float(scale), 6))
K = torch.tensor([[702., 0., 288.], [0., 702., 288.], [0., 0., 1.]]).repeat(8, 1, 1)
mask = torch.tensor([True]*4 + [False]*4)
lat = torch.arange(4*4*2*2, dtype=torch.float32).reshape(4,4,2,2)
# Use intrinsics scaled to the synthetic 16x16 image grid (latent 2x2).
Ksmall = K.clone(); Ksmall[:, :2] *= 16/576
cond = ns['get_cond'](carrier, lat, centered, Ksmall, scale, torch.ones(4, 8), mask)
print('paired_plucker_max_abs', float((cond['c']['dense_vector'][:4] - cond['c']['dense_vector'][4:]).abs().max()))
print('cfg_per_slot', ns['MultiviewScaleRule'](1.2)(2.0, cond['all_c2ws'], cond['all_Ks'], mask).tolist())
print('conditional_replace_mask', cond['c']['replace'][:, -1, 0, 0].tolist())
print('unconditional_replace_nonzero', int(torch.count_nonzero(cond['uc']['replace'])))
print('unconditional_clip_nonzero', int(torch.count_nonzero(cond['uc']['crossattn'])))
coincident = torch.eye(4).repeat(8,1,1)
s0, p0 = ns['get_translation_scaling_factor'](carrier, coincident)
print('coincident_scale', float(s0), 'finite', bool(torch.isfinite(p0).all()))
den = ns['DiscreteDenoiser'](ns['DDPMDiscretization'](), device='cpu')
for i in [50,200,400,600,800,950]:
    s = float(den.sigmas[i])
    print('sigma_index', i, 'sigma', format(s,'.8f'), 'copy_eps_mse_per_unit_latent_mse', format(1/s**2,'.8f'))
print('No model, weights, images, training, or sampler trajectory executed.')
PY
```

Complete output; exit code 0:

```text
device cpu torch 2.7.0
duplicate_pose_scale 13.343333
paired_plucker_max_abs 0.0
cfg_per_slot [1.2000000476837158, 1.2000000476837158, 1.2000000476837158, 1.2000000476837158, 1.2000000476837158, 1.2000000476837158, 1.2000000476837158, 1.2000000476837158]
conditional_replace_mask [1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0]
unconditional_replace_nonzero 0
unconditional_clip_nonzero 0
coincident_scale 2.0 finite True
sigma_index 50 sigma 0.40706900 copy_eps_mse_per_unit_latent_mse 6.03481477
sigma_index 200 sigma 2.27375650 copy_eps_mse_per_unit_latent_mse 0.19342477
sigma_index 400 sigma 6.36547565 copy_eps_mse_per_unit_latent_mse 0.02467961
sigma_index 600 sigma 13.58374691 copy_eps_mse_per_unit_latent_mse 0.00541952
sigma_index 800 sigma 30.11506653 copy_eps_mse_per_unit_latent_mse 0.00110264
sigma_index 950 sigma 63.63996887 copy_eps_mse_per_unit_latent_mse 0.00024691
No model, weights, images, training, or sampler trajectory executed.
```

## Appendix B — Source identities and archived timing arithmetic

### B1. Snapshot and resource calculation

Exact command (repository root):

```bash
python3 -B - <<'PY'
import hashlib, json, statistics, subprocess
from pathlib import Path
print('head', subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip())
print('git_status_begin')
print(subprocess.check_output(['git','status','--short'], text=True), end='')
print('git_status_end')
files = [
'work/S142_followup/PROTOCOL_DRAFT.md',
'work/agents/CODEX_R255_IDEATION_AFTER_S141.md',
'work/S141_finetune/PROTOCOL.md',
'work/S141_finetune/train_s141.py',
'work/S141_finetune/gen_s141.py',
'work/S141_finetune/s141_common.py',
'work/S141_finetune/analyze_s141.py',
'work/S141_finetune/warps_s141.py',
'work/S141_finetune/clips_s141.json',
'work/S140_warp_guided/score_s140.py',
'work/S137_geometry_baselines/RESULT.md',
'data/S134_tacc/vmem_src/modeling/pipeline.py',
'data/S134_tacc/vmem_src/modeling/sampling.py',
'data/S134_tacc/vmem_src/modeling/network.py',
'data/S134_tacc/vmem_src/modeling/modules/transformer.py',
'data/S134_tacc/vmem_src/utils/util.py',
'data/S134_tacc/vmem_src/configs/inference/inference.yaml']
for name in files:
    print(hashlib.sha256(Path(name).read_bytes()).hexdigest(), name)
rows=[]
for p in sorted(Path('work/S139_crossseq_revisit/results/stepB_tacc').glob('RUNS_*.jsonl')):
    rows.extend(json.loads(s) for s in p.read_text().splitlines() if s.strip())
secs=[r['seconds'] for r in rows]
print('archived_timing_rows', len(secs), 'mean_seconds', format(statistics.mean(secs),'.6f'))
for n in [16,96,192,208]:
    print('generations',n,'baseline_extrapolated_gpu_hours',format(n*statistics.mean(secs)/3600,'.6f'))
print('10500_steps_at_protocol_smoke_1.38_seconds_gpu_hours',format(10500*1.38/3600,'.6f'))
print('output_exists',Path('work/agents/CODEX_R256_S142_DRAFT_REJECTION.md').exists())
PY
```

Complete output; exit code 0:

```text
head a5b12a829b1e3d087fae4bc7e023b144ddd1ae2a
git_status_begin
?? work/agents/prompts/R256_FULL.md
git_status_end
8c2d3e97538e3db734cb647f7f36a9c9417c43799cd6cd6047a0f1143e860213 work/S142_followup/PROTOCOL_DRAFT.md
62fc97aed343bde1f684140f70bba7cd1281522c34c86d8fe8589cc7965b2a2a work/agents/CODEX_R255_IDEATION_AFTER_S141.md
0b5c3aab9809f851ee476b2a54eae781c7c286bbe1e047ac89388b40d3051fdc work/S141_finetune/PROTOCOL.md
6ba0419e5ceb39406bbd1894ffae90398c27daedbc2eea56b18e537ba6187c0a work/S141_finetune/train_s141.py
c903be28ffea8c359c79d927ebdcf782e1d9ac21b81d0b159439e1566fac8121 work/S141_finetune/gen_s141.py
459549706fb3a965fc4f7c5021f4d49cc626158e94a7c9cdc94cf8784cccb6cc work/S141_finetune/s141_common.py
b0cdce6c5fa8fb95cc3d2742c8f1b55924b9410beb0903791d6c6553a2066087 work/S141_finetune/analyze_s141.py
72d8f66fb4439ef3cf626d973a594b182bf30b04d89cb0af221c1208fb048470 work/S141_finetune/warps_s141.py
c2fbdd49e87426d837aa5e90a8e694cddd9032864079cef53c29a66991740f36 work/S141_finetune/clips_s141.json
61f093cb2e40eeec2d862562dc6e28e98076447cde5819a2384536937cb00a79 work/S140_warp_guided/score_s140.py
6249f52b7b0076841df896075e48ba40d7a54ccd34728680524f4a45f83286f6 work/S137_geometry_baselines/RESULT.md
680da1c14db8a6780a37fca3a8bac5bb59f0aa7d395db96d4360b352eb7f2255 data/S134_tacc/vmem_src/modeling/pipeline.py
dc07ca0ba571ba5fb48f9856515d2cb7dea25254008a6f8b315538817f352b24 data/S134_tacc/vmem_src/modeling/sampling.py
9ed21c2d804734d7ca2d81b1e596858835ca70a4a04abb9b5540b872515d4c9b data/S134_tacc/vmem_src/modeling/network.py
5f0d152a2f6464076cb0ee5aca725b3445420a5f37ac571d3daa77e580e65764 data/S134_tacc/vmem_src/modeling/modules/transformer.py
30a97451f7a895e99ab881e97249f564e6b97eca2b5ea4d8f83953c26c4cf65e data/S134_tacc/vmem_src/utils/util.py
8d849588016935573a22ef6aaee567f71125ca4d3bdf18f51e3552a64be9fea3 data/S134_tacc/vmem_src/configs/inference/inference.yaml
archived_timing_rows 288 mean_seconds 36.114410
generations 16 baseline_extrapolated_gpu_hours 0.160508
generations 96 baseline_extrapolated_gpu_hours 0.963051
generations 192 baseline_extrapolated_gpu_hours 1.926102
generations 208 baseline_extrapolated_gpu_hours 2.086610
10500_steps_at_protocol_smoke_1.38_seconds_gpu_hours 4.025000
output_exists False
```

## Appendix C — Monitor-subset selection from the frozen manifest

### C1. Input-only, deterministic selection; no scores read

Exact command (repository root):

```bash
python3 -B - <<'PY'
import json
from pathlib import Path
j=json.loads(Path('work/S141_finetune/clips_s141.json').read_text())
v=[c for c in j['clips'] if c['split']=='val']
print(json.dumps(v[0],sort_keys=True))
print('keys',sorted(v[0]))
from collections import Counter
print('monitor_strata',sorted(Counter(('/'.join(c['tgt'][0].split('/')[:2]), c['kind']) for c in v).items()))
print('proposed_monitor_ids')
for seq in ['office/seq-10','redkitchen/seq-14']:
    for kind in ['static','memory']:
        a=sorted((c for c in v if '/'.join(c['tgt'][0].split('/')[:2])==seq and c['kind']==kind),key=lambda c:c['id'])[:2]
        assert len(a)==2
        print(seq,kind,[c['id'] for c in a])
PY
```

Complete output; exit code 0:

```text
{"C": "seq-10", "H": "seq-01", "ctx": ["office/seq-01/000100", "office/seq-10/000380", "office/seq-01/000550", "office/seq-01/000300"], "hist_frac": 0.75, "id": "c02000", "kind": "memory", "nms_threshold": 0.9554200172424316, "s": 365, "scene": "office", "split": "val", "tgt": ["office/seq-10/000425", "office/seq-10/000440", "office/seq-10/000455", "office/seq-10/000470"]}
keys ['C', 'H', 'ctx', 'hist_frac', 'id', 'kind', 'nms_threshold', 's', 'scene', 'split', 'tgt']
monitor_strata [(('office/seq-10', 'memory'), 13), (('office/seq-10', 'static'), 3), (('redkitchen/seq-14', 'memory'), 10), (('redkitchen/seq-14', 'static'), 6)]
proposed_monitor_ids
office/seq-10 static ['c02006', 'c02016']
office/seq-10 memory ['c02000', 'c02003']
redkitchen/seq-14 static ['c02001', 'c02002']
redkitchen/seq-14 memory ['c02009', 'c02010']
```

## Appendix D — Post-write integrity check

This checks citation ranges and unchanged inspected inputs, not the truth of every interpretation. The byte count is explicitly before adding this transcript.

Exact command:

```bash
python3 -B - <<'PY'
import hashlib, re, subprocess
from pathlib import Path
expected = {"work/S142_followup/PROTOCOL_DRAFT.md":"8c2d3e97538e3db734cb647f7f36a9c9417c43799cd6cd6047a0f1143e860213","work/agents/CODEX_R255_IDEATION_AFTER_S141.md":"62fc97aed343bde1f684140f70bba7cd1281522c34c86d8fe8589cc7965b2a2a","work/S141_finetune/PROTOCOL.md":"0b5c3aab9809f851ee476b2a54eae781c7c286bbe1e047ac89388b40d3051fdc","work/S141_finetune/train_s141.py":"6ba0419e5ceb39406bbd1894ffae90398c27daedbc2eea56b18e537ba6187c0a","work/S141_finetune/gen_s141.py":"c903be28ffea8c359c79d927ebdcf782e1d9ac21b81d0b159439e1566fac8121","work/S141_finetune/s141_common.py":"459549706fb3a965fc4f7c5021f4d49cc626158e94a7c9cdc94cf8784cccb6cc","work/S141_finetune/analyze_s141.py":"b0cdce6c5fa8fb95cc3d2742c8f1b55924b9410beb0903791d6c6553a2066087","work/S141_finetune/warps_s141.py":"72d8f66fb4439ef3cf626d973a594b182bf30b04d89cb0af221c1208fb048470","work/S141_finetune/clips_s141.json":"c2fbdd49e87426d837aa5e90a8e694cddd9032864079cef53c29a66991740f36","work/S140_warp_guided/score_s140.py":"61f093cb2e40eeec2d862562dc6e28e98076447cde5819a2384536937cb00a79","work/S137_geometry_baselines/RESULT.md":"6249f52b7b0076841df896075e48ba40d7a54ccd34728680524f4a45f83286f6","data/S134_tacc/vmem_src/modeling/pipeline.py":"680da1c14db8a6780a37fca3a8bac5bb59f0aa7d395db96d4360b352eb7f2255","data/S134_tacc/vmem_src/modeling/sampling.py":"dc07ca0ba571ba5fb48f9856515d2cb7dea25254008a6f8b315538817f352b24","data/S134_tacc/vmem_src/modeling/network.py":"9ed21c2d804734d7ca2d81b1e596858835ca70a4a04abb9b5540b872515d4c9b","data/S134_tacc/vmem_src/modeling/modules/transformer.py":"5f0d152a2f6464076cb0ee5aca725b3445420a5f37ac571d3daa77e580e65764","data/S134_tacc/vmem_src/utils/util.py":"30a97451f7a895e99ab881e97249f564e6b97eca2b5ea4d8f83953c26c4cf65e","data/S134_tacc/vmem_src/configs/inference/inference.yaml":"8d849588016935573a22ef6aaee567f71125ca4d3bdf18f51e3552a64be9fea3"}
out = Path('work/agents/CODEX_R256_S142_DRAFT_REJECTION.md')
text = out.read_text()
print('review_exists', out.is_file())
print('review_bytes_before_qa_append', out.stat().st_size)
changed = [p for p,h in expected.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
print('reviewed_input_hash_changes', changed)
roots = {'S141/':'work/S141_finetune/', 'S140/':'work/S140_warp_guided/', 'S137/':'work/S137_geometry_baselines/', 'V/':'data/S134_tacc/vmem_src/'}
short = {n:'data/S134_tacc/vmem_src/modeling/'+n for n in ['pipeline.py','sampling.py','network.py']}
short.update({'transformer.py':'data/S134_tacc/vmem_src/modeling/modules/transformer.py','util.py':'data/S134_tacc/vmem_src/utils/util.py'})
pat = r'\b((?:S141/|S140/|S137/|V/)[\w/.-]+|pipeline\.py|sampling\.py|network\.py|transformer\.py|util\.py):(\d+)(?:[–-](\d+))?'
refs = list(re.finditer(pat, text.split('## Appendix A')[0]))
bad = []
for m in refs:
    name,lo,hi = m.groups(); hi = int(hi or lo); lo = int(lo)
    path = short.get(name, name)
    for prefix,root in roots.items():
        if name.startswith(prefix): path=root+name[len(prefix):]
    p=Path(path)
    if not p.is_file() or not 1<=lo<=hi<=len(p.read_text().splitlines()): bad.append(m.group())
print('source_citation_ranges_checked', len(refs))
print('invalid_source_citation_ranges', bad)
print('markdown_fences_balanced', text.count(chr(96)*3)%2==0)
print('replacement_characters', text.count(chr(65533)))
print('git_status_begin')
print(subprocess.check_output(['git','status','--short'], text=True), end='')
print('git_status_end')
assert not changed and not bad
PY
```

Complete output; exit code 0:

```text
review_exists True
review_bytes_before_qa_append 53930
reviewed_input_hash_changes []
source_citation_ranges_checked 64
invalid_source_citation_ranges []
markdown_fences_balanced True
replacement_characters 0
git_status_begin
?? work/agents/CODEX_R256_S142_DRAFT_REJECTION.md
?? work/agents/prompts/R256_FULL.md
git_status_end
```

