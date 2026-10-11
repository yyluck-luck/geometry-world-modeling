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
