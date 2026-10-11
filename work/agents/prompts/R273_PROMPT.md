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
