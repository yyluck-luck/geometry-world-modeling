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
- Write only the output file named in the brief. Modify no other file.
- `new_method_validated=false`, `novelty_authorization=NONE`. Nothing you write changes them.

## Concurrency
Other codex processes and the main agent work in this checkout at the same time. Do not delete, revert or "clean up" any file you did not create. Report anomalies; leave them alone.

## Evidence standard
Cite file:line for every code claim and arXiv ID + exact title (+ section) for every literature claim. Every "I ran this" claim must include the exact command and its complete output. I prefer a correct negative to an encouraging answer; you are expected to reject my ideas when they are wrong, redundant with prior work, or untestable.

## Language
Work entirely in English and write your output entirely in English.
# Brief R266 — REJECTION of S146 Amendment 2 (robust KPS, "KPS-R") before any S146 step-A run (2026-10-11)

Read work/S146_fresh12/PROTOCOL.md (Amendment 2 at the end), work/S146_fresh12/kps.py (KPS-R) versus
work/S139_crossseq_revisit/kps.py (original), and where KPS is used: run_retrieval_s139.py (copied into work/S146_fresh12,
VMem repaired memory via kps.install), build_pool_s146.py (rule 5), warps_s146.py. The trigger: a 32-frame 12-Scenes bank
star had one view with < 50 valid points vs the root view -> infinite residual -> KPS objective infinite for every scale.

Attack it briefly and concretely: (1) is "mean over finite-residual views, defined only if >= half are finite" a sound,
minimal fix, or does it bias the scale (e.g. selection of views whose residual is finite only at some scales — the set of
finite views can change with sigma; does the objective become discontinuous / favour scales that push views to infinity?)
Check _proj_residual's behaviour (ok.sum() < 50 -> inf; frac_bad penalty) and propose the exact correct variant (e.g. fix the
view set at the scale grid's first pass, or count views finite at ANY scale); (2) what happens downstream in kps_init for
excluded views (depth via world points from pts3d/sigma, rigid registration, _set_focal skipped for non-finite focal) —
is their depth still usable for VMem's surfels, coverage and warps? (3) are the gates sufficient; (4) any interaction with
VMem's surfel memory (step A grows the bank 5 -> 20 -> 32 frames; KPS runs per construct call). Verify by reading code and
with synthetic CPU tests (no model weights needed). Output: write exactly one file,
work/agents/CODEX_R266_KPSR_REJECTION.md: findings table (issue | severity | evidence | concrete change) and the exact
recommended KPS-R definition. I prefer a correct negative to an encouraging answer.
