
# Brief R250 — hostile audit of S133–S137 (2026-10-09)

Correction to the preamble: RESEARCH_MEMORY.md now has the NEWEST entries at the TOP. The pinned VMem copy used by
all sealed GPU runs is the SuperPOD transport, mirrored locally at data/S134_tacc/vmem_src (gitignored; it differs from
isolated_vmem_source only in device handling in modeling/pipeline.py and utils/util.py).

Audit these result files and their evidence. Try to break each claim.
- work/S133_scale_debug/RESULT.md (+ repro_stage1.py, STAGE1_*.json, remote_support_609623/support-609623.out in work/S130_C8_diagnostics)
- work/S134_tacc_fixed_map/RESULT.md (+ results/, run_retrieval_s134.py, eval_map_s134.py, build_plan_s134.py)
- work/S135_scale_init/RESULT.md (+ kps.py, test_kps.py, repro_kps.py, ARM_*.json, pose_only_retrieval.py, POSE_ONLY_*.json)
- work/S136_repaired_memory/RESULT.md (+ PROTOCOL.md, results/, analyze_s136.py, build_plan_s136.py, plan_v2.json)
- work/S137_geometry_baselines/RESULT.md (+ PROTOCOL.md, geometry_baselines.py, geometry_b2.py, B2_*.json, SUMMARY_*.json, analyze_s137c.py, results_c/)

Specific checks (cite file:line; rerun on CPU where feasible with
`PYTHONPATH=work/S17C_environment/site-packages .venv-cut3r/bin/python ...`; data lives in data/S134_tacc/datasets):
1. S133 mechanism: does `minimum_spanning_tree` (work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R/cloud_opt/dust3r_opt/init_im_poses.py) really fall back to identity on PnP failure, and do the STAGE1 JSONs support "PnP success count separates the failure classes 14/14"?
2. KPS (kps.py): is the model x_j ∝ R_j0·P + σ·t_j0 correct for dust3r star-graph pointmaps (are pts3d[j] really in view 0's frame)? Any sign/convention error? Run test_kps.py.
3. Pixel-aligned depth metric (repro_kps.py depth_on_cut3r_grid, cut3r_K): does it match VMem rgb() and CUT3R's 512 resize + 512x384 crop?
4. Pose-NMS equivalence and TF32 (pose_only_retrieval.py vs get_context_info in data/S134_tacc/vmem_src/modeling/pipeline.py; croco.py allow_tf32): rerun POSE_ONLY on results/stepA_superpod/native_fix1 and the TF32 emulation described in S135 RESULT §3. Is the "14/14 with TF32" claim reproducible and is the explanation sound?
5. S136: recompute Q1–Q4 independently from results/stepB_*/S136_SCORES_*.json and plan_v2.json. Check plan construction (consumer contexts, static offsets 0,15,30,45, conventions) and the harness gate claim (32/32).
6. S137: any leakage of target depth/RGB into B0/B1/B2 or the warps? Is the scorer identical to C9's? Is the CUT3R-grid → 640x480 inverse mapping in geometry_b2.py correct? Recompute the headline contrasts.
7. Overclaiming: list every sentence in the five RESULT.md files that the evidence does not support, and every needed caveat that is missing.

Output: write exactly one file, work/agents/CODEX_R250_S133_S137_AUDIT.md: a verdict table (claim | verified / refuted / unverifiable | evidence), then the details. I prefer a correct negative to an encouraging answer.
