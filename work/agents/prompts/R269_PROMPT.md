# Brief R269 — IMPLEMENTATION: report figures from committed results (2026-10-11)

Owner allows codex for implementation work. Create a figure script and the figures for the final technical report.
You MAY create files only under docs/report/figures/ (new directory): make_figures.py and PNG/PDF outputs it produces, plus
docs/report/figures/README.md listing each figure, its source file(s) and the exact numbers plotted. Do not modify any
other file. CPU only (matplotlib/numpy are available in the project venv: .venv-cut3r/bin/python). Read only committed
result JSONs (no images, no target frames). Every plotted number must be traceable to a file and key; print a table of
plotted values when the script runs.

Figures (publication quality, colour-blind-safe palette, readable at slide size, 300 dpi PNG + PDF):
1. S139/S140 chess: per-arm mean PSNR and SSIM (VMem static_recent, mem_vmem, mem_pose; B2 warp; WGS) — sources:
   work/S139_crossseq_revisit/results/S139_ANALYSIS.json, results/S139_BASELINE_CONTRASTS.json,
   work/S140_warp_guided/results/CONFIRM_ANALYSIS.json, results/s139_ssim/S139_SSIM_ANALYSIS.json.
2. S141 fine-tuning: contrasts with 95% CIs (PSNR and SSIM) for the registered and exploratory contrasts and the RGB-D panel
   — work/S141_finetune/results/S141_ANALYSIS.json.
3. S143: per-rule mean warp PSNR vs mean generated PSNR (scatter, labelled rules) and the discovery/fresh contrasts with
   seed-panel points — work/S143_context_ranking/results/S143_ANALYSIS.json, S143_FRESH.json, WARP_SCORES.json, POOL.json.
4. S144 development gate: bar chart of development PSNR per arm/control — work/S144_A_wgs/results/SCORES_dev.json,
   DEV_GATE.json.
5. S146 KPS diagnostic: per room and construction size, fraction of non-finite objectives and minimum positive-depth
   fraction — work/S146_fresh12/diag/KPS_DIAG_{0,1,2}.json.
Run the script and confirm all outputs exist. Output summary of what was produced in docs/report/figures/README.md.
