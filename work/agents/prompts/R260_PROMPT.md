# Brief R260 — REJECTION of the S143 draft (context-ranking audit) before freezing (2026-10-10)

Read work/S143_context_ranking/PROTOCOL_DRAFT.md. It adopts your R259 §6 Experiment 1 (work/agents/CODEX_R259_IDEATION_EVALUATION.md)
with concrete choices. Relevant code: work/S139_crossseq_revisit (WINDOW_MANIFEST.json, plan.json, pose_arms_s139.py,
baselines_s139.py, kps.py), work/S137_geometry_baselines/geometry_baselines.py, work/S140_warp_guided/score_s140.py,
work/S141_finetune/gen_s141.py (zero-init = base, fidelity verified), VMem source data/S134_tacc/vmem_src. Chess data:
data/S139_chess/chess (do not read target frames beyond what the existing scores already used).

Attack it:
1. Is R (seed-fold cross-fitted consumer oracle minus warp-selected set) a sound estimand, or is it biased upward by
   selection among 6 noisy arms even after seed splitting (winner's curse within a window)? Compute, on CPU, the null
   distribution of R expected from pure seed noise using the archived S139 per-seed scores (e.g. permute arm labels
   within window or simulate with the measured seed variance) and report what R would look like if the generator were
   indifferent among sets. Recommend a threshold or a null-calibrated test if +0.20 dB is not safe.
2. Rule 5 (coverage-greedy with CUT3R+KPS on all 32 bank frames, star rooted at bank frame 0): is it implementable with
   the existing kps.install (star edges, known poses) and is the depth from a 32-frame star comparable to the 4-frame
   B2 depth? Any cheaper, equally valid coverage proxy (e.g. the surfel visibility VMem already computes in step A)?
3. Sorting sets by bank index changes context order relative to S139 (slot 0 sets the Plücker reference and scale).
   Does this confound the comparison with the archived S139 outputs, and is regenerating all six sets the right call?
4. Warp scores per (window, set): score_s140.py keeps one warp score per window id (first context seen). Confirm from
   the code and specify the fix.
5. What result would actually be new relative to MBench (2606.00793), MIND (2602.08025), R2M-Bench (2608.27328),
   RolloutFaith (2609.36843), Twin Rollouts (2608.08982), FAR? Is "geometric utility vs consumer utility on the same
   evidence" already measured there? Verify by reading those papers.
6. Anything else that would make the result uninterpretable or unreportable.

Output: write exactly one file, work/agents/CODEX_R260_S143_DRAFT_REJECTION.md: findings table (issue | severity |
evidence | concrete change), the null-distribution computation (exact command + full output), then a corrected
minimal specification. I prefer a correct negative to an encouraging answer.
