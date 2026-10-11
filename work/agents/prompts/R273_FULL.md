# Operating instructions (read before the brief below)

You are running inside a checkout of the project repository with read access and network. **Verify, do not trust.** Every factual claim below is checkable from this repo or the public literature. Where you cannot check something, say so explicitly.

## What you can verify here (updated 2026-10-11)

- One-page state: CURRENT_STATUS.md. Ledger: RESEARCH_MEMORY.md (NEWEST entries at the TOP; written in Chinese, read it anyway). Current report: docs/report/TECHNICAL_REPORT_20261010.md (S133-S141, S143; S144-S146 not yet written in).
- VMem source used by all GPU runs (mirror of the SuperPOD transport): data/S134_tacc/vmem_src (modeling/pipeline.py, modeling/network.py, modeling/modules/transformer.py, modeling/sampling.py, utils/util.py). Older pinned copies (SHA-256 90a45f45...) are at work/S17C_interface_preparation/isolated_vmem_source.
- Stage folders with PROTOCOL.md (frozen before runs), code, RESULT.md: work/S133_* ... work/S141_finetune, work/S143_context_ranking, work/S144_A_wgs, work/S145_B_diagnosis (all finished); work/S146_fresh12 (operational assay running on TACC; no S146 generation scores exist yet).
- Self-audits: work/agents/SELF_AUDIT_S139.md ... SELF_AUDIT_S145.md. Earlier codex rounds: work/agents/CODEX_R250_S133_S137_AUDIT.md and others.
- Large GPU artifacts (adapters, generated frames) live on the TACC cluster; score files, receipts and analyses are in each stage's results/.

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
# Brief R273 — REJECTION round on the S147 (Anchor-A) protocol draft (2026-10-11)

Read work/S147_anchor_a/PROTOCOL_DRAFT.md, your own R271 recommendation (work/agents/CODEX_R271_IDEATION_AFTER_S145.md
§5 Rank 1), and the code it will reuse: work/S141_finetune/train_s141.py, s141_common.py, clips_s141.json,
work/S141_finetune/results/tacc/logs/WARP_LOG_*.jsonl, work/S144_A_wgs/gen_s144.py, score_s144.py, analyze_s144.py,
build_plans_s144.py, results/ (DEV_GATE.json, ALPHA.json, SCORES_dev.json), work/S145_B_diagnosis/RESULT.md.
S146 is still running; do not assume its outcome.

Attack the draft. In particular:
1. Can each arm be implemented exactly as written on this code (frozen A LoRA with a trainable input conv whose gradient
   must pass through the whole UNet under activation checkpointing; resume logic; RNG alignment across arms when invalid
   clips are skipped; adapter save/load with the existing variant checks)? List concrete pitfalls with file:line.
2. Is F_null (per-channel constant prototype latent, true coverage) a fair content-free control for F_geo? Would a
   different null (e.g. shuffled warp from another clip, mean spatial map) be more informative or leak content?
3. Are the development-gate comparators and thresholds coherent with the S144 numbers (A_none 11.19, B2 13.19, V 13.26,
   BL_AC 13.61 dB)? Is the practical bar so high that the experiment is predetermined to fail, and if so is it still worth
   16+ GPU-h for the PRIMARY/mechanism answer? Should the gate be split (mechanism vs practical) with explicit wording?
4. Leakage and exposure: the development panel is S141's monitor set and S144's development panel; chess is exposed;
   office1 is untouched. Anything else that breaks the claimed boundary (e.g. S144 blend α fitted on the same clips)?
5. Missing controls, missing fidelity checks, budget realism (S141 timing receipts), and whether running two training
   processes per RTX 3090 is acceptable for comparability.
6. Write a corrected minimal specification (binding text I can adopt verbatim), including exact gate wording and the
   claim wording for each outcome. "Do not run S147" is an acceptable answer if you can show it cannot be informative.

Output: write exactly one file, work/agents/CODEX_R273_S147_REJECTION.md. I prefer a correct negative to an encouraging
answer.
