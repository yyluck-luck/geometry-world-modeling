# S145 protocol — why did S141 B fail? Inference-time branch ablations under B's fixed LoRA (frozen)

Frozen 2026-10-10 ≈ 20:00 UTC, before any S145 output. Supersedes `PROTOCOL_DRAFT.md`. Idea: codex R262 E2; corrected by
rejection round R263 — its §4 "Corrected minimal S145 specification" is adopted in full and is part of this protocol.
Training-free diagnosis, not a method. `new_method_validated=false`, `novelty_authorization=NONE`. Runs after S144's
development gate (S144 has priority per R263 §5) on TACC RTX 3090.

Binding points (R263 §4 governs): B checkpoint 0dd40c86… with all LoRA tensors kept; arms B_original (W(e)+b), B_off (0),
B_target_only (g·(W(e)+b), g = ~input_masks = [0,0,0,0,1,1,1,1] repeated per CFG half, applied after the convolution),
B_bias_only (b), B_permuted (W([perm(z_w), cov]) + b; per-target joint 4-channel permutation within exact coverage strata
k = round(64·cov), private PCG64 seeded by SHA-256("S145|145|window_id|target_ref")[:8] little-endian; identical in c/uc).
extend_concat applied to c and uc separately before packing; shape assertions (extra (4,5,72,72), concat (8,12,72,72),
wrapped-conv input (16,16,72,72)). **Primary: B_off − B_original**; key secondary: B_target_only − B_original; practical
references A (S141 A_mem) and raw B2. Chess 24 windows, mem_vmem, S140 CPU warps, seeds 3–6; reused B_original/A only after
an intervention-disabled exact replay. Teacher-forced monitor probe as R263 §4.3 (diagnostic only; cannot prune arms).
Same thresholds/bootstrap/pair reporting as S144. Cap 6 GPU-hours. One pass; no retraining or branch-strength sweep.
