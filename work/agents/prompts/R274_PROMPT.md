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
