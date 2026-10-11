# Self-audit S145 (B branch ablations under B's fixed LoRA) — verification by the main agent

Ideation/rejection: codex gpt-6-astra (ultra) R262 E2 (idea), R263 (rejection; its §4 is the binding spec). This file
verifies execution. Machine-readable checks: `work/S145_B_diagnosis/results/SELF_AUDIT_CHECKS.json` (75/75 pass),
produced by `self_audit_s145.py`.
| check | result |
|---|---|
| protocol frozen (56785b92) and implementation committed (205a682c) before any S145 output | pass |
| B checkpoint SHA 0dd40c86… = S141 adapter check; recorded in all 384 new receipts | pass |
| local gen_s144.py / s141_common.py / plans = hashes recorded next to every arm on TACC | pass |
| deployed analyze_s145.py, probe_s145.py, POSE_ARMS.json, plan_score_B.json, score_s140.py, S141 B/A score files = local | pass |
| replay gate: BRANCH=orig reproduces S141 B (window 0, seed 3) byte-for-byte, 68c5e197… | pass |
| each arm: 96 cells = 24 windows × seeds 3–6, branch label correct, RTX 3090, scores finite | pass |
| permutation moved fraction mean 0.988, min > 0.5 | pass |
| generation 4.27 GPU-h < 6 GPU-h cap | pass |
| independent recomputation (own window-id pair labels, own bootstrap draw): all means, wins, pair means for PSNR, SSIM, covered, holes | match (max error 1.8e-15); CIs agree |
| probe: 2,880 rows (32 clips × 6 σ × 5 conditions × c/uc/guided); clean-latent MSE = σ²·ε-MSE on every row | pass |
Limits: exposed room, one checkpoint, inference-time only. Self-audit; no codex repository-level review of the executed run.
