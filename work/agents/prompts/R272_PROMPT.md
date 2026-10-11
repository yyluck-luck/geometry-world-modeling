# Brief R272 — IMPLEMENTATION: figures for S145 and S146, and fill the Figure 1 gap (2026-10-11)

You MAY modify only files under docs/report/figures/ (make_figures.py, its outputs, README.md). Use the committed snapshot
at HEAD. Same rules as R269/R270: trace every plotted number to a file and JSON key, print the values you plot, CPU only,
verify every export by reading the PNG back, keep the existing figures' style and the r269_snapshot/ folder.

1. Figure 1 (S139/S140 chess): the B2(static_recent) SSIM cell is currently N/A. A scored source now exists:
   work/S141_finetune/results/tacc/eval/SCORES_chess_Bstatic.json, key /warps/<window_id>/{psnr,ssim} (24 windows; the
   static-context warp scored by the S140 scorer during S141). Before using it, assert that its per-window PSNR equals
   work/S139_crossseq_revisit/BASE_b2_static.json /rows/*/psnr for every window (report the max absolute difference). Only
   if they match, replace N/A with the window-mean SSIM and update the caption, README and limitation text accordingly.
2. New Figure 6 (S145, work/S145_B_diagnosis/results/S145_ANALYSIS.json): a forest plot like fig02a with the four
   branch-ablation contrasts versus B_original (primary B_off − B_original marked as primary; key secondary
   B_target_only − B_original) and the practical references B_off − A and B_off − B2, PSNR and SSIM panels, archived 95%
   window-bootstrap CIs, windows-positive counts, and the ±0.20 dB / ±0.01 SSIM practical thresholds as dashed lines.
   Optionally a small inset/side panel with covered/hole-region PSNR deltas for the primary and secondary contrasts.
   Caption must say: inference-time ablations under B's fixed LoRA; chess is exposed; B's LoRA kept in every arm.
3. New Figure 7 (S146 operational assay; only if work/S146_fresh12/results/operational_v1/S146_OP_PRIMARY.json exists at
   HEAD): per-room × per-seed matrix (heatmap with numbers) of nearest-4 − mem_vmem(sorted) PSNR, plus a dot plot of D for the
   five contrasts with D_room points, the 0.20 dB gate line, and the SSIM D values in a separate panel. Caption must use the
   claim wording of work/agents/CODEX_R267_S146_PATH_DECISION.md §4 that matches DECISION in that file (do not shorten to
   "nearest-4 beats VMem on fresh rooms"). If the file is absent, skip Figure 7 and say so in the README.
Rerun the script and overwrite docs/report/figures/README.md with the summary (sources, keys, checks, limitations).
