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
# Brief R268 — CODE REVIEW (urgent) of the S146 operational implementation before it runs (2026-10-11)

The S146 operational chain starts on TACC in about one hour (after S145). Review the implementation for bugs that would
waste the run or silently corrupt the result. Protocol: work/S146_fresh12/PROTOCOL.md, Amendment 3 (adopting your R267
§3). Files: work/S146_fresh12/s146op_chain.sh, run_retrieval_s146op.py (derived from work/S139_crossseq_revisit/
run_retrieval_s139.py), kps_orig_obs.py (vs work/S139_crossseq_revisit/kps.py), pool_op_s146.py, build_plans_s146.py,
score_gen_s146.py (vs work/S140_warp_guided/score_s140.py), analyze_s146.py (mode op-primary), gen_s141.py, s141_common.py,
PARITY_MANIFEST_chess_w0.json, plan_s143_replay.json; staging/manifests: stage_12scenes_s146.py. VMem source:
data/S134_tacc/vmem_src. Remote paths in the chain are TACC paths; you cannot access them.

Check concretely, citing file:line, and run CPU unit tests where possible (no GPU, no weights): (1) does the chain follow
Amendment 3 exactly (order of gates, namespace freshness, parity check semantics, availability gate, replay, seeds, seal
before scoring, scorer, analysis)? any bash pitfalls (set -e with pipes/subshells/background jobs, wait status, grep
exit codes on no match killing the pipeline, timeout, quoting, python heredocs with $ variables)? (2) run_retrieval_s146op.py:
the selector-validation patch (types of context_time_indices, the target-collision check, exceptions caught and recorded,
SELECTION_RECEIPT before render), KPS_MODULE import, that observer logging cannot change state or RNG (kps_orig_obs vs
original: diff them); (3) pool_op_s146.py: kps_log length check [4,19,31] — is that what the observer emits per construct
call (does initialize() or the 5-frame init also log?), bank equality check against the receipt, rule 2/4 arithmetic,
native-order package handling; (4) score_gen_s146.py vs score_s140 metric equality; (5) analyze_s146.py op-primary:
table() expected keys (does it include the nat3 package and every set?), pkg() native lookup, matrix weights, gates.
Fix nothing in place: output a findings table (issue | severity | evidence | exact patch as a unified diff) so the main
agent can apply verified patches. Output: write exactly one file, work/agents/CODEX_R268_S146OP_CODE_REVIEW.md.
