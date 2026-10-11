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
# Brief R274 — CODE REVIEW of the S147 implementation before it runs (2026-10-11)

Review work/S147_anchor_a/ against its frozen protocol work/S147_anchor_a/PROTOCOL.md (binding text = your R273 §7 plus the
implementation notes at the end). Files: train_s147.py, gen_s147.py (diff it against work/S144_A_wgs/gen_s144.py),
eng_s147.py, prep_dev_s147.py, score_s147.py, score_s144_functions.py (must be a verbatim block of
work/S144_A_wgs/score_s144.py), analyze_s147.py, make_inputs_s147.py, s147_chain.sh, INVALID_GEOMETRY.json, plan_*.json.
The chain will run on TACC gpu13 as soon as S146 ends (in about an hour). A GPU smoke test already passed eng_s147.py
(values in PROTOCOL.md) and ran train_s147.py for 12 attempts on F_geo and A_cont.

Find bugs that would make the run invalid or the analysis wrong. In particular check: RNG/schedule alignment across arms and
across resume (train_s147.py), the trainable allowlists and that F arms cannot change A LoRA, warm-up in valid updates, the
skip logic, checkpoint contents, prototype construction and its use at inference, the true bypass for invalid packages and
its byte-identity with A, the S145 permutation reuse, COPY / fallback / BL_AC / BL_A0 definitions versus §D–E, sequence-equal
aggregation and every gate condition in analyze_s147.py versus §E, completeness assertions, and fail-closed behaviour of the
chain under `set -euo pipefail` with background jobs. Report each finding with file:line, severity (blocking / should-fix /
note) and a minimal patch (unified diff). Do not edit the files.

Output: write exactly one file, work/agents/CODEX_R274_S147_CODE_REVIEW.md. I prefer a correct negative to an encouraging answer.
