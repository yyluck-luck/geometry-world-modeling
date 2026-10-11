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
# Brief R270 — IMPLEMENTATION follow-up to R269 figures (2026-10-11)

You MAY modify only files under docs/report/figures/ (make_figures.py, its outputs, README.md). Use the committed snapshot at
HEAD (the S139/S140 result files are now committed: work/S139_crossseq_revisit/results/*.json and subfolders,
work/S140_warp_guided/results/*.json and subfolders). Same rules as R269 (trace every number to a file/key; print values;
CPU only; verify exports).
1. Add Figure 1 (S139/S140 chess): arm means for PSNR and SSIM — VMem static_recent, mem_vmem, mem_pose; B2 warp (from
   static and from mem_vmem contexts); S140 WGS — plus the key contrasts with CIs (mem_vmem − static_recent, B2(mem_vmem) −
   VMem(mem_vmem), WGS − B2). Check the JSON schemas first and report exactly which keys you used.
2. Redesign fig04 (S144 development): plot each arm/control as a difference from B2 (dB) on a zoomed axis (dot plot, no bars
   from zero), mark the +0.20 dB gate line relative to A_R where relevant, and show A_none (context-only, ~11.19 dB) as an
   annotated off-scale value rather than squashing the axis. Keep the "blends fitted on development, optimistic" note.
3. fig02a: move value labels so they never overlap the zero line or markers.
Rerun the script and update README.md. Output summary in docs/report/figures/README.md (overwrite).
