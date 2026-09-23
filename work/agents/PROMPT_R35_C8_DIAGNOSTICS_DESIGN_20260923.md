# Round 35 — Design and implement the two owner-approved GPU diagnostics (decision C8)

The owner approved GPU use for exactly two diagnostic experiments (RESEARCH_MEMORY.md, "OWNER DECISION C8"). Working cap: 20 H800-hours total. You will DESIGN and IMPLEMENT them and write the pre-registration. **You do not run anything on a GPU and do not submit Slurm jobs** — I will deploy and run them on the cluster after reviewing your work. You may and should run CPU tests.

## Write permissions for this round (overrides the one-file rule)
Create files only inside a NEW directory `work/S130_C8_diagnostics/`, plus one summary file `work/agents/CODEX_R35_C8_DESIGN_20260923.md`. Modify no existing file. Never modify the three pinned VMem copies.

## Read first
- The C8 decision and the entries before it in RESEARCH_MEMORY.md (R32, R33, R34, three-source review).
- Existing harness scripts you must reuse rather than rewrite: `work/S103_selector_free_baseline/nms_s111.py`, `nms_on_clean_s113.py`, `stage_bank_s105.py`, `geom_eval_s110.py`, `slot_utilisation_control.py`, and whatever scripts produced S106 (context arms, job 594717) and S107 (order-balanced, job 594733) — find them under work/.
- How previous GPU jobs were launched on SuperPOD: sbatch templates, the Python/conda environment actually used, module loads, checkpoint paths, and receipt format (search work/S101*, work/S103*, run_receipts*, *MANIFEST*). Reuse the exact working launch recipe.
- Cluster facts: repo at /home/yliutz/geometry-world-modeling; data under /home/yliutz/datasets/ (NOTE: the directories named heldout_3dmatch_scene13/14 contain the EXPOSED development sequences, not held-out data); Slurm account mscitspod2026, partition normal, 8x H800 per node. All jobs must run inside tmux and write receipts.

## Experiment 1 — Slot-0 factor separation (ray reference vs translation scale vs tensor order)

Verified code facts (pinned pipeline.py): Plucker rays use `extrinsics_src=all_w2cs[:1]` (slot 0 is the ray reference); `get_translation_scaling_factor` centers on the mean of all context+target cameras, then sets scale = camera_scale / norm(camera_dists[0]) + 0.01 (slot 0 sets global scale); encoder embeddings are mean-pooled; the transformer has no slot embedding but processes frames along a time axis. Measured: at a fixed multiset, changing slot 0 moves PSNR by 0.55 dB ({55,55,40,40}) and 0.87 dB ({50,50,45,45}) (S107, job 594733); at a fixed multiset with slot 0 fixed, reordering slots 1-3 changes PSNR by about 0 (four PERMUTATION windows, S113_SCORES.json, -0.015 dB).

Design a factorial on the S107 multisets (same scene, window, targets, seeds as S107; find them):
- order A vs order B (different frame in slot 0), crossed with
- conditioning convention: (N) native; (R) reference fixed — both orders use the SAME physical camera as `extrinsics_src`, namely the camera that is slot 0 in order A; (S) scale fixed — both orders compute the translation scale from that same physical camera's centered position; (RS) both fixed.
Under RS the conditioning of order A and order B must be identical up to a permutation of the context slots. **Prove this on CPU before any GPU run**: with the real conditioning code path (get_cond / get_translation_scaling_factor / get_plucker_coordinates, CPU tensors, random latents and the saved real context poses from the receipts), show that under RS the per-slot conditioning tensors of order B are exactly a permutation of those of order A, and that under N they are not. Include the test code and its output; I will rerun it verbatim.
Implement the conventions as a thin wrapper / subclass in the new directory, not as edits to the pinned source.
Report the estimand: for each convention, the slot-0 swap effect = mean PSNR(order B) - mean PSNR(order A), over seeds, per multiset, plus MAE. Also report RGB of reference frames unchanged.

## Experiment 2 — Support audit (physical scarcity vs indexing vs delivery vs consumption)

For each of the 14 panel windows and each target camera, compute per-target-pixel masks using INDEPENDENT evaluation geometry (the dataset's own depth and poses — only in the evaluator, never fed to the model):
- B(u): the target surface point is observed (visible, passes a depth-consistency test with a stated tolerance) in at least one of the 12 bank frames;
- C(u): observed in at least one of the 4 frames actually delivered as context (use the saved context lists for static / NMS-off / clean NMS-on / leaked NMS-on arms);
- J(u): exposed by VMem's own surfel index. Note VMem renders retrieval at the AVERAGED target pose with intrinsics scaled by 0.65 (pipeline.py ~:635-647); state exactly how you map that to per-target-pixel J, or define J at the retrieval render and say so.
The GPU part should be minimal: rebuild the surfel memory per window and save the retrieval render maps (index/cosine/depth) and frame counts WITHOUT running diffusion. The rest is CPU.
Then relate per-window support fractions to the already-sealed per-window PSNR/MAE (S113_SCORES.json, S106/S107 scores) — descriptively; 14 windows is a finite panel, no population inference.

## Pre-registration (write it BEFORE any result exists; I will commit it before running)
For each experiment: the exact arms, seeds, windows; the primary estimand; the predictions with numeric thresholds; and what each outcome would mean. For Experiment 1 at minimum: the hypothesis "the slot-0 effect is mainly coordinate/scale" predicts that under RS the swap effect is below 0.15 dB for both multisets, and state the alternative outcomes (e.g. R alone removes it; S alone removes it; neither removes it => genuine tensor-order / temporal-position effect). For Experiment 2: the decision table (high B low J = indexing failure; high B low C = delivery failure; high C but poor PSNR = consumption failure; low B = true scarcity), the numeric cut-offs you will use, and the depth tolerance.

## Deliverables in work/S130_C8_diagnostics/
- DESIGN_AND_PREREGISTRATION.md
- the wrapper/implementation code, the CPU equivalence test (with its captured output), the analysis scripts
- sbatch files + a RUNBOOK.md with the exact commands, expected runtime per job, total H800-hour estimate (must be well under 20), receipt fields, and which outputs to copy back
Then the summary file work/agents/CODEX_R35_C8_DESIGN_20260923.md: what you built, the GPU-hour estimate, anything that blocks execution, and every assumption you could not verify from the repo.

## Rules
Write in English. Every "I ran this" claim must include the exact command and its full output — a previous round printed code that could not have produced its output, so I will rerun everything. Do not invent file paths, environment names or checkpoint names: cite where you found each. If something needed is missing from the repo, say so plainly.
