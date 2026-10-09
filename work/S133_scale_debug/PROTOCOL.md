# S133 protocol — root cause of the VMem surfel scale blow-up (owner-authorized 2026-10-09)

Authorization: owner approval in conversation, 2026-10-09 ("ok do it"; GPU on gpu13/gpu14 also allowed),
recorded under the AGENTS.md owner authorization rule. Debugging protocol, not a method claim.
`new_method_validated=false`, `novelty_authorization=NONE`.

## Question
Why do five C8/C9 windows (scene_13 w150/w250/w300/w350, scene_14 w150) render surfel depth roughly
400–960× the dataset depth under both pose conventions, and what minimal change removes it?

## Timeline (honest ordering)
1. Before this file (2026-10-09 ~22:00–22:35 Asia/Shanghai): read-only evidence from the existing C8 job
   609623 log showed the blow-up already present after the **first** surfel construction (5 frames).
   A CPU reproduction (`repro_stage1.py`, smoke on scene_13 w150 and w50) reproduced it (s=707, depth ratio
   877 vs C8's ~769) and located the mechanism:
   - VMem's pairwise graph is a star (0–j); MST init fixes view 0 and obtains views 1–4 by `fast_pnp`
     with mask `im_conf > 3`;
   - in scene_13 w150 views 1–4 have median CUT3R confidence ≈1.66, so **0 pixels pass**, PnP returns None,
     and `minimum_spanning_tree` silently falls back to identity poses;
   - all five MST camera centres coincide, `align_multiple_poses` (similarity with scaling, centre-dominated)
     returns s≈707, the point cloud is scaled up, and 400 fixed-pose iterations do not undo it;
   - stage 2 inherits the depths through `preset_depth`.
2. After this file: the 14-window evaluation below.

## Inputs
- Source: `work/S17C_interface_preparation/isolated_vmem_source` (VMem 39291e4f…, CUT3R 8bc15dc9…);
  `surfel_inference.py` 8a348645…, `init_im_poses.py` b3f59fbf…, `optimizer.py` f78f52ee…, `pipeline.py` 90a45f45….
- Weights: `data/cut3r/cut3r_512_dpt_4_64.pth`, SHA-256 45f7e98a…f8103 (same as SuperPOD transfer receipt).
- Data: bank frames start+{0..55 step 5} for the 14 C8 windows (color, pose, depth), copied read-only from
  SuperPOD `/home/yliutz/datasets` to `data/S133_scale_debug/datasets` (gitignored). Depth is used only by
  the CPU diagnostic, never by the model call.
- Device: local CPU (M3 Max), FP32. Not byte-identical to the H800 runs (CPU vs CUDA kernels).

## Arms (stage 1 only: 5 frames, niter 400, lr 0.01, exactly as VMem)
2×2: pose convention {native (C8), gl (C9)} × PnP mask {original thr=3, fix}.
Fix: MST PnP threshold = min(3, min over views of median CUT3R confidence). Windows whose views all have
median confidence > 3 are unchanged by construction.

## Primary metric
Per window, median over the 5 bank frames of (median optimized depth / median dataset depth), same centre crop.
Secondary: `align_multiple_poses` scale s, median pairwise distance of MST centres, PnP mask sizes.

## Decision rule (fixed before the 14-window run)
- Blow-up removed: fix arms have no window with depth ratio > 10 (originals have 5 windows > 100).
- Scale certified for downstream use: depth ratio in [0.5, 2] in ≥ 12/14 windows in one arm.
- If the fix removes the blow-up but scale is not certified, report that the remaining mis-scale is a
  separate small-baseline registration problem; do not tune further in this protocol.
- Stop after this run; any GPU follow-up (stage 2 / retrieval / generation with the fix) needs a new protocol.

## Outputs
`work/S133_scale_debug/STAGE1_{native,gl}_fix{0,1}.json`, logs, `RESULT.md`.
