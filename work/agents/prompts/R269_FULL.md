# Operating instructions (read before the brief below)

You are running inside a checkout of the project repository with read access and network. **Verify, do not trust.** Every factual claim below is checkable from this repo or the public literature. Where you cannot check something, say so explicitly.

## What you can verify here (updated 2026-10-10)

- One-page state: CURRENT_STATUS.md. Ledger: RESEARCH_MEMORY.md (NEWEST entries at the TOP; written in Chinese, read it anyway). Current report: docs/report/TECHNICAL_REPORT_20261010.md (S133-S140).
- VMem source used by all GPU runs (mirror of the SuperPOD transport): data/S134_tacc/vmem_src (modeling/pipeline.py, modeling/network.py, modeling/modules/transformer.py, modeling/sampling.py, utils/util.py). Older pinned copies (SHA-256 90a45f45...) are at work/S17C_interface_preparation/isolated_vmem_source.
- Stage folders with PROTOCOL.md (frozen before runs), code, RESULT.md: work/S133_* ... work/S140_warp_guided, work/S141_finetune (running now).
- Self-audits: work/agents/SELF_AUDIT_S139.md, SELF_AUDIT_S140.md. Earlier codex rounds: work/agents/CODEX_R250_S133_S137_AUDIT.md and others.
- GPU run artifacts for S141 live on the TACC cluster, not in this checkout (training is in progress); review the code and the protocol.

## Hard constraints for THIS run
- No GPU, no training, no weight or dataset downloads, no Slurm submissions, no SSH to clusters. Read, compute on CPU, search the web.
- No contact with anyone. No messages, issues, PRs, emails.
- Write only the output file(s) or directory the brief names. Modify no other file.
- `new_method_validated=false`, `novelty_authorization=NONE`. Nothing you write changes them.

## Concurrency
Other codex processes and the main agent work in this checkout at the same time. Do not delete, revert or "clean up" any file you did not create. Report anomalies; leave them alone.

## Evidence standard
Cite file:line for every code claim and arXiv ID + exact title (+ section) for every literature claim. Every "I ran this" claim must include the exact command and its complete output. I prefer a correct negative to an encouraging answer; you are expected to reject my ideas when they are wrong, redundant with prior work, or untestable.

## Language
Work entirely in English and write your output entirely in English.
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
