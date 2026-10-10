# What a Frozen Surfel-Memory Video World Model Actually Does: Integration Defects, a Known-Pose Scale Fix, and Geometric Baselines

Technical report v2, 2026-10-10. HKUST CSIT6910 independent project.
Supersedes the interpretation, not the record, of `TECHNICAL_REPORT_20260918.md`, which is kept unchanged.
Project flags: `new_method_validated=false`, `novelty_authorization=NONE`.

---

## Summary

We audit a frozen VMem configuration (arXiv:2506.18903; repository `runjiali-rl/vmem` @ 39291e4f) that uses CUT3R
(arXiv:2501.12387) to build a surfel memory and retrieve four context frames for a camera-conditioned video diffusion
model. On exposed windows from two RGB-D Scenes v2 sequences:

1. **Three integration defects** (two in the released code path, one in this project's own harness). (a) dust3r's MST initialisation silently replaces failed PnP solves with identity
   poses. The similarity registration then scales the surfel cloud ×300–900 or ×0.02–0.08 in 8 of 14 windows.
   (b) The project's priming schedule never put 3 of 12 bank frames into memory. (c) VMem's CUT3R fork detaches the
   depth maps, so its 400-iteration global alignment never optimises depth.
2. **KPS, a known-pose dense scale initialisation,** fixes (a). The median stage-1 |log scale ratio| drops from 0.410 to
   0.055 (median relative error ≈ 33.5% → 5.4%). It gives +1.75 dB [+0.85, +2.82] over the threshold fix in a
   downstream warp predictor. Re-enabling depth optimisation (fixing (c)) hurts.
3. **Retrieval is pose-distance NMS.** Surfels only define a visibility candidate set. On a correct map, pose-only NMS
   reproduces VMem's selection 14/14 on an RTX 3090. The H800's different selections are reproduced only when TF32
   rounding is emulated (CUT3R enables TF32 globally).
4. **The camera convention matters more than the memory.** Converting the dataset's OpenCV poses to the OpenGL input VMem
   expects improves static generation by +0.89 dB [+0.25, +1.47] (8 seeds). Even with every defect repaired, memory
   shows no detectable gain over a fixed static context: −0.06 dB [−1.15, +0.94].
5. **Training-free geometry beats the frozen generator in PSNR.** A CUT3R + KPS forward warp (RGB + poses) is
   +5.7 dB (native) / +4.8 dB (gl) above VMem's static output, 16/16 windows; SSIM agrees on this panel but not on
   held-out chess (§7). Copying the nearest history frame is
   +1.2 dB above native static. Given aligned target-pose warps as context, VMem reproduces them (+0.000 dB) and adds no
   refinement.

6. **On held-out cross-sequence revisits (7-Scenes chess, pre-registered), retrieval finds useful views, but the
   generator does not turn them into a detectable gain.**
   VMem retrieves history-sequence frames (88.5%) whose warp is +1.46 dB [+0.91, +2.05] better than the recent static
   frames' warp. Yet VMem's generation from them is −0.18 dB [−0.52, +0.15] vs static. A warp of the same contexts
   beats VMem by +3.21 dB in 24/24 windows. By SSIM, generating from retrieved history is even worse than from
   recent frames (−0.019 [−0.032, −0.006]).
7. **A training-free consumption fix does not replicate.** Warp-guided sampling (RePaint-style, §7.2) gains +0.79 dB
   over the warp on the development panel, but +0.02 dB [−0.10, +0.13] on held-out chess. It reliably polishes pixels
   the warp covers (+0.24 dB); in pixels the warp does not cover it helps on the development panel and hurts on chess
   (why is an untested hypothesis).
8. **Fine-tuning the generator (§7.3): domain adaptation helps, memory still does not, warp conditioning failed.** An
   attention LoRA trained on six other 7-Scenes rooms improves held-out chess by +0.33 dB [+0.08, +0.59] (memory contexts)
   and RGB-D Scenes by +1.16 dB. After adaptation, retrieved memory is still worse than recent frames (−0.33 dB). Adding
   the target-pose warp as an extra input (established warp+mask conditioning) did not work: −3.56 dB below the warp.

Items 1–5 come from an exposed development panel (2 scenes, 14–16 windows, 4 targets each). Item 6 comes from a scene
held out from this project's design decisions (§7).

---

## 1. Setup

**Consumer.** VMem inference as released: CUT3R (512 DPT) surfels, `get_context_info` retrieval (NMS on), 4 context +
4 target frames, 50 sampling steps, cfg 2.0 / cfg_min 1.2, 576×576. Weights verified by SHA-256 against the transfer
receipt. The sealed runs used the SuperPOD source transport; it differs from the pinned tree only in device handling.

**Panel.** RGB-D Scenes v2 scene_13/14 (3DMatch packaging), windows w ∈ {0 (static only), 50, …, 350}. Bank = 12 frames
w…w+55 step 5. Targets w+60, +75, +90, +105. Static context = w+0, +15, +30, +45. PSNR uses the contract scorer
(integer RGB, 576×576 crop). Unit = window mean over seeds. 95% CIs come from a window-cluster bootstrap (10k).
Verdicts: IMPROVES / WORSENS at |Δ| ≥ 0.2 dB with the CI excluding 0; NO_MATERIAL_CHANGE at |Δ| < 0.2 with the CI
covering 0; otherwise INCONCLUSIVE.

**Compute.** SuperPOD H800 (Slurm, Apptainer, digest-pinned image) and TACC RTX 3090 (exact SuperPOD environment
freeze). Generation is split by seed block (H800: 42, 7, 1, 2; 3090: 3, 4, 5, 6), so every window–seed cell is
produced on one site. Byte-identity with sealed outputs is checked on H800 (32/32 manifest matches).

## 2. Integration defects

### 2.1 Silent PnP identity fallback → scale blow-up/collapse (S133)
VMem pairs every frame with frame 0 and runs dust3r global alignment with `init="mst"`, although all poses are preset.
MST recovers views 1–4 with PnP on pixels whose CUT3R confidence exceeds 3. On these frames confidence is often 1–2,
so the mask is empty, `fast_pnp` returns None, and `minimum_spanning_tree` substitutes the identity
(`init_im_poses.py:239–249`). With coincident centres, the similarity registration returns s ≈ 300–700 (blow-up) or
≈ 0.02–0.08 when only some views fail (collapse). The PnP success count separates the catastrophic classes on this
panel: 0/4 → blow-up 5/5, 2/4 → collapse 3/3. The H800 C8 log confirms both. An adaptive mask threshold
(min(3, median confidence)) removes every catastrophe, leaving a low bias (median ratio 0.668).

### 2.2 Priming holes (S135)
`construct_and_store_scene` creates surfels only for the last `target_num_frames = 4` frames of each call. The project's
priming (5 frames, then 7 at once) therefore never gave bank offsets 25/30/35 any surfels. Those frames could never be
retrieved. The static context's offset 30 was unreachable for every sealed memory arm. Chunked priming (5, 4, 3)
restores 12/12 coverage.

### 2.3 Depth is never optimised (S138; found in external review)
The fork keeps `im_depthmaps` as a ParameterList and re-stacks it with `ParameterStack(is_param=False)`, which detaches
(`optimizer.py:245–249, 303–317`). After 50 iterations depth is bit-identical to initialisation and every depth
gradient is None. Only pairwise poses are updated. Making depth optimisable *worsens* scale in 12/14 windows (the
absolute-distance loss shrinks the scene) and costs −0.20 dB [−0.36, −0.06] downstream. Initialisation alone determines
the map, and it should be good.

## 3. KPS: known-pose dense scale initialisation (S135)
With all poses known, view j's CUT3R points P (in view 0's frame, CUT3R units) satisfy x_j ∝ R_j0·P + σ·t_j0.
Projection is scale-invariant, so σ is the only unknown. The focal length is solved in closed form for each σ.
KPS chooses σ by minimising the median dense reprojection residual over ~10^5 points (log-grid search plus
golden-section refinement). It then sets metric depths with respect to the known poses. Synthetic tests (3–8 cm
baselines, σ from 0.02 to 40) recover σ within 15%. With zero baseline the residual curve is flat, which flags
unidentifiability.

| stage-1 init (14 windows, pixel-aligned vs dataset depth) | in [0.5, 2] | in [0.8, 1.25] | median ratio | median \|log r\| |
|---|---|---|---|---|
| VMem as is | 5/14 | 1/14 | 0.72 (5 blow-ups) | 2.90 |
| adaptive PnP threshold (S133) | 12/14 | 3/14 | 0.665 | 0.410 |
| **KPS (fitted focal)** | **14/14** | **13/14** | **0.946** | **0.055** |
| KPS with true intrinsics | 13/14 | 10/14 | 0.926 | 0.130 |

A fitted focal beats the true K because CUT3R's pointmaps carry their own implicit focal. KPS's residual also acts as a
pose-convention detector. The minimum residual is lower with gl poses in 14/14 RGB-D Scenes windows and 3/3 7-Scenes
pairs. With native poses σ collapses to the grid floor.

## 4. What retrieval does (S135)
`get_context_info` renders surfels at the target pose and counts visible surfels per bank frame. Those counts only form a
candidate multiset (n = min(14, #frames)). Candidates are then **sorted by pose geodesic distance** (rotation angle +
0.1 × translation in m), and four are chosen by pose-distance NMS. With a correct map every memory frame is a candidate
in 13/14 windows, so the render adds nothing. A ×300–700 blow-up leaves most selections unchanged because distant
surfels keep every frame "visible". The fix changes NMS-on contexts in only 4/14 windows. Computed in fp32 or fp64,
pose-only NMS equals the RTX 3090 selection 14/14. The H800 selection differs in 5/14 windows and is reproduced 14/14
when TF32 input rounding is emulated in the 3×3 rotation product. CUT3R's `croco.py` sets
`torch.backends.cuda.matmul.allow_tf32 = True` on import. Computing the geodesic in fp64 makes retrieval
hardware-independent.

## 5. Convention and memory at 8 seeds (S136; 568 generations)
| contrast | Δ PSNR (dB) | 95% CI | windows + | verdict |
|---|---|---|---|---|
| static: gl − native (16 windows) | **+0.890** | [+0.248, +1.469] | 12/16 | IMPROVES (H800 +0.83, 3090 +0.95) |
| repaired memory (gl + KPS + chunked) − static (gl) | −0.059 | [−1.153, +0.942] | 8/14 | NO_MATERIAL_CHANGE |
| repaired − original memory (gl) | −0.145 | [−0.580, +0.153] | 4/13 | NO_MATERIAL_CHANGE |
| original memory − static (native; the sealed setting) | −0.219 | [−0.820, +0.391] | 6/14 | INCONCLUSIVE |

The repaired map passes every gate: scale 14/14 within [0.5, 2], own-render correlation 0.785, full coverage. The
memory still shows no detectable gain. The 2026-09-18 report's memory − static = −0.485 dB (2 seeds) does not survive
8 seeds. The convention effect is measured for the static arm; the sealed static numbers understate VMem by ~0.9 dB.

## 6. Geometric baselines (S137)
Same four static context frames and targets, same scorer. B2 uses CUT3R depth from RGB and known poses only.
| predictor | input | PSNR (dB) |
|---|---|---|
| VMem static, native / gl (S136, 8 seeds) | RGB + poses, frozen generator | 14.36 / 15.25 |
| B0: copy nearest context frame | RGB + poses | 15.52 |
| B2: CUT3R + VMem alignment as is, forward warp | RGB + poses | 15.68 |
| B2: CUT3R + adaptive threshold, forward warp | RGB + poses | 18.33 |
| **B2: CUT3R + KPS, forward warp** | **RGB + poses** | **20.09** |
| B1: dataset depth, forward warp (RGB-D upper bound) | RGB-D + poses | 22.05 |

B2-KPS − static is +5.73 [+4.70, +6.69] (native) and +4.84 [+3.81, +5.88] (gl), both 16/16. SSIM agrees
(+0.11 / +0.14). Feeding VMem the B2 warps rendered at the target poses as its four contexts yields +0.000 dB
[−0.044, +0.053] relative to the warps themselves: VMem reproduces same-pose context. With uncovered pixels set to grey it
reproduces the grey (−5.4 dB). Filling uncovered pixels with VMem's own output is worse than nearest-neighbour fill
(−1.3 dB, also in SSIM). B2 is a direct geometric predictor, not a capacity-matched generator control. These contrasts
are diagnostic.

## 7. Cross-sequence revisits on 7-Scenes chess (S139)
Pre-registered (`work/S139_crossseq_revisit/PROTOCOL.md`, committed before any content was read). Three history →
current sequence pairs, 24 windows. Bank = 20 frames from another traversal + 12 recent frames; targets 2–3.5 s ahead.
Repaired memory (gl, KPS, full coverage). Arms: static_recent, mem_vmem, mem_pose (pose-only NMS). 8 seeds, both sites;
576 generations. The KPS residual selects gl in 3/3 pairs. 16/24 windows are history-favourable by pose.

| contrast | Δ PSNR (dB) | 95% CI | windows + | verdict |
|---|---|---|---|---|
| **mem_vmem − static_recent** (primary) | **−0.181** | [−0.518, +0.145] | 10/24 | NO_MATERIAL_CHANGE |
| — history-favourable / recent-favourable | −0.334 / +0.126 | | | prediction not supported |
| mem_vmem − mem_pose | −0.182 | [−0.405, +0.038] | 9/24 | NO_MATERIAL_CHANGE |
| mem_pose − static_recent | +0.002 | [−0.363, +0.324] | 13/24 | NO_MATERIAL_CHANGE |

Used geometrically, the same contexts tell a different story. A B2 warp from mem_vmem contexts beats one from static
contexts by +1.46 [+0.91, +2.05] (history-favourable +1.95 [+1.24, +2.68]). In history-favourable windows the
surfel-visibility selection beats pose-only selection (+0.46 [+0.02, +0.94]). The warp beats VMem's own generation from
the same contexts by +3.21 [+2.84, +3.58] (24/24). With a 32-frame bank, retrieval finds genuinely useful long-range
history, which it did not need to on the 12-frame panel. The generator does not turn it into better frames. A
re-check in SSIM over the same 576 outputs gives mem_vmem − static_recent = −0.019 [−0.032, −0.006] (8/24), so the
conclusion survives a second metric. On chess, however, VMem's own frames have higher SSIM (0.470) than the warp
(0.432): nearest-fill streaks in 45% disoccluded area hurt structure. The geometric baseline's advantage is a PSNR
(pixel-alignment) advantage.

### 7.2 Warp-guided sampling (S140)
A sampling-loop intervention with the model unchanged. The target latents start from the noised warp (SDEdit); with
RePaint, the covered latent blocks are reset to the noised warp after every step, so the denoiser only generates the
holes. A re-implemented loop with no intervention reproduces VMem's sampler byte-for-byte. Six variants were screened
on the development panel (2 seeds). RePaint s = 0.5 was selected by a pre-registered rule: +0.785 dB [+0.56, +1.00]
over the warp, 15/16 windows, almost all from holes (+1.85 dB). On held-out chess (24 windows, 8 seeds, mem_vmem
contexts) it gives **+0.020 dB [−0.095, +0.134]** (PSNR, primary: no material change) and +0.025 SSIM. Covered pixels
improve (+0.24 dB, 23/24); pixels the warp does not cover get worse (−0.24 dB). One hypothesis, not tested: uncovered
pixels on the development panel are mostly crop bands that the contexts do show, while on chess they are regions no
context observed. "Uncovered" means uncovered by this warp, not a certified disocclusion label.

### 7.3 Fine-tuning the generator (S141)
Two LoRA variants (rank 16 on every attention projection; base frozen) trained in parallel on two RTX 3090s, 10000 steps
each, on 2000 fixed clips from 7-Scenes fire, heads, office, pumpkin, redkitchen and stairs (chess and RGB-D Scenes
excluded). A: LoRA only. B: A plus a zero-initialised convolution that feeds the VAE latent of the B2 warp and its coverage
at the target frames into the first UNet layer (a ViewCrafter/MultiDiff-style recipe; no method novelty is claimed).
With adapters at initialisation both reproduce the base model byte-for-byte. Evaluation on the S139 chess windows,
seeds 3–6, RTX 3090, against the base outputs of the same seeds:

| contrast | Δ PSNR (dB) | 95% CI | windows + | verdict | Δ SSIM |
|---|---|---|---|---|---|
| **A_mem − base_mem** (primary A) | **+0.330** | [+0.078, +0.585] | 17/24 | IMPROVES | +0.018 |
| A_static − base_static | +0.448 | [+0.096, +0.822] | 17/24 | IMPROVES | +0.007 |
| A_mem − A_static | −0.332 | [−0.669, +0.006] | 5/24 | INCONCLUSIVE | −0.008 |
| **B_mem − B2 warp** (primary B) | **−3.558** | [−3.913, −3.201] | 0/24 | WORSENS | +0.073 |
| RGB-D Scenes A_static − base (exposed, 16 windows) | +1.162 | [+0.612, +1.729] | 13/16 | IMPROVES | +0.039 |
| RGB-D Scenes B_static − base | −2.617 | [−3.425, −1.828] | 0/16 | WORSENS | −0.057 |

Domain mismatch is a real factor: adaptation on other rooms of the same sensor improves the held-out room and transfers to
a different dataset. It does not make retrieved history useful: after adaptation the recent-frame context still wins.
B neither copies nor refines its warp. Its outputs are no closer to the warp than the base model's, and its loss is in
low-frequency layout and colour. On chess it has the highest SSIM of all arms (smoother outputs), while on RGB-D it is
worse than the base model in both metrics. The monitor denoising loss stayed flat for both variants, so the A gain shows
up in sampling, not in the training objective's validation curve. One run per variant; chess was examined in S139/S140.

## 8. Limitations
One frozen consumer. Two exposed scenes for §2–6; one held-out scene (three sequence pairs sharing history banks) for §7. 14–24 windows, 4 targets each.
Chess is held out from design decisions up to S139, but S140/S141 reuse its windows, so it is no longer an untouched set.
"No detectable gain" (NO_MATERIAL_CHANGE) is not equivalence, and "no benefit" is not "no use": conditioning can change
outputs without improving them. Shared intrinsics across arms do not guarantee that all arms are equally affected by
calibration error. S140 rejects one sampling intervention; it does not show that only fine-tuning can help.
PSNR, plus SSIM in §6–7 (the two metrics disagree on chess for warp vs generator). Seed blocks are confounded with hardware. CPU stage-1 evidence (§2.1, §3) is not byte-identical
to GPU runs. Forward splatting leaves cracks. The 7-Scenes RGB focal (585, documented) is approximate. Pretraining
exposure of CUT3R/VMem to these datasets is not verified.

## 9. Corrections to the 2026-09-18 report
- Its memory-arm retrievals ran on a surfel map broken in 8/14 windows, with 3/12 bank frames unreachable. The
  retrieval itself was mostly pose-determined (§4).
- Every sealed run used the native camera convention, about 0.9 dB below gl for the static arm (§5).
- `memory_nms_on_clean − static = −0.485 dB` is not supported at 8 seeds (−0.22 dB, inconclusive).
- Its duplicate-slot repair result (−0.016 dB vs a +0.20 dB bar) and the slot-0 coordinate/scale finding stand.

## 10. Artifact index
`work/S133_scale_debug`, `work/S134_tacc_fixed_map`, `work/S135_scale_init`, `work/S136_repaired_memory`,
`work/S137_geometry_baselines`, `work/S138_depth_opt`, `work/S139_crossseq_revisit`, `work/S140_warp_guided`, `work/S141_finetune`. Each holds PROTOCOL.md, RESULT.md,
scripts and receipts. External review: `work/agents/CODEX_R250_S133_S137_AUDIT.md`; self-audit (owner-approved): `work/agents/SELF_AUDIT_S139.md`. One-page state: `CURRENT_STATUS.md`.

## Related work found by retrieval (codex R253; independently re-verified)
The S139 pattern is partly precedented. MemLearner (arXiv:2606.31734) reports a memory-query module whose conditioning is
ignored. Spatia (arXiv:2512.15716, Table 4) finds reference frames alone do not help while projections do. VMem's own
paper (arXiv:2506.18903, Table 4, RealEstate10K cycle trajectories, K = 4) reports 14.82 dB PSNR with surfel retrieval vs
13.27 dB with camera-distance selection, unlike our chess result (mem_vmem − mem_pose −0.18 dB). The regimes differ
(regenerating its own imagined frames on cycle trajectories vs predicting real frames on cross-sequence revisits with a
32-frame bank); the difference is not explained here. IDs, titles and the quoted table values were re-checked against
arXiv by the main agent. Warp-conditioned generation itself is established
(ViewCrafter arXiv:2409.02048, MultiDiff arXiv:2406.18524, GEN3C arXiv:2503.03751, AnyRecon arXiv:2604.19747).

## References
- VMem: Consistent Interactive Video Scene Generation with Surfel-Indexed View Memory. arXiv:2506.18903.
- Continuous 3D Perception Model with Persistent State (CUT3R). arXiv:2501.12387.
- DUSt3R: Geometric 3D Vision Made Easy. arXiv:2312.14132.
- Cameras as Relative Positional Encoding (PRoPE). arXiv:2507.10496.
- Datasets: RGB-D Scenes v2 (3DMatch packaging); Microsoft 7-Scenes (chess).
