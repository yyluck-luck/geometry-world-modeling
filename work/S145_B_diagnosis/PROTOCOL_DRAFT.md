# S145 protocol DRAFT — why did S141 B fail? Branch ablations with B's own LoRA (codex R262 E2)

Draft 2026-10-10 ≈ 19:45 UTC, to pass a codex rejection round before freezing. Training-free diagnosis, not a method.
Design adopted from `work/agents/CODEX_R262_IDEATION_AFTER_S141_RESULTS.md` §7.
Arms (chess, S139 mem_vmem contexts, S140 warps, seeds 3–6, RTX 3090, B's final adapter 0dd40c86…):
B_original (= S141 B_mem outputs, reused after a replay); B_target_only (extra-branch output incl. bias multiplied by the
target-frame indicator, both CFG halves); B_off (whole added branch zeroed, B's LoRA kept); B_bias_only (extra input
channels zeroed, branch bias kept on all frames); B_permuted (warp latent cells permuted within coverage strata, fixed
seed, both CFG halves; coverage and scoring masks unchanged). Plus a teacher-forced monitor probe (correct / zero /
permuted warp under c and uc separately; ε-MSE per σ index and derived clean-latent MSE).
Primary: B_target_only − B_original ≥ +0.20 dB with lower bound > 0 and pair rule. Strongest trivial baselines: B_off and
unmodified A (S141 A_mem). Interpretation bounded as in R262 §7; one pass, then stop. Budget ≤ 6 GPU-hours.
