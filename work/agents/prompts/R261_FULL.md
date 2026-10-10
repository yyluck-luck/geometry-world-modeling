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
# Brief R261 — REJECTION of S143 Amendment 1 (fresh-seed confirmation) before any S143 result exists (2026-10-10)

Read work/S143_context_ranking/PROTOCOL.md (Amendment 1 at the end), analyze_s143_confirm.py, s143_confirm_chain.sh,
analyze_s143.py, and your R260 (work/agents/CODEX_R260_S143_DRAFT_REJECTION.md §3.4). Discovery generation (seeds 3-6) is
running; nothing has been scored. The confirmation uses fresh seeds 42,7,1,2 on the same RTX 3090s, selections frozen
from discovery (c_W from warps; c_G_disc = argmax of the 4-seed discovery mean; r_disc = best discovery rule).

Attack it, briefly and concretely: (1) is C = mean_w[Q_G_fresh(c_G_disc) - Q_G_fresh(c_W)] the right confirmatory
estimand, and is "C >= 0.20, window-bootstrap lower > 0, >= 3/4 fresh seed panels positive, no negative pair mean in 2/3"
a sensible rule given that the unit of seed replication is the seed panel and the windows are shared? (2) Does using
all four discovery seeds for c_G_disc (rather than the 2-seed folds of the discovery primary) create any inconsistency?
(3) Any bug in analyze_s143_confirm.py (ties, aliases between rules 4/5, key parsing of "<window>__<set_id>__s<seed>"
files by score_s140.py's rsplit('__s', 1), seeds 1/2 vs set ids "s1"/"s2")? Verify by reading code and, where useful,
running it on synthetic CPU inputs. (4) Anything that must change before discovery results are opened.

Output: write exactly one file, work/agents/CODEX_R261_S143_AMENDMENT_REJECTION.md: findings table (issue | severity |
evidence | concrete change), then verdict. I prefer a correct negative to an encouraging answer.
