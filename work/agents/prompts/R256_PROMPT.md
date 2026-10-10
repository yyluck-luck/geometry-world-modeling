# Brief R256 — REJECTION of the S142 follow-up draft before it is frozen (2026-10-10)

Read work/S142_followup/PROTOCOL_DRAFT.md. It pre-registers one follow-up chosen mechanically by the S141 PRIMARY_B
verdict: E1 (alignment test of B: deranged warp content) if B beats the warp; E2 (challenger C: target-pose warps as
the four clean context slots, LoRA, same recipe as S141 A) otherwise. It follows your R255
(work/agents/CODEX_R255_IDEATION_AFTER_S141.md). S141 code: work/S141_finetune (train_s141.py, gen_s141.py,
s141_common.py, PROTOCOL.md with Amendment 1). VMem source: data/S134_tacc/vmem_src. S137c (frozen VMem given aligned
target-pose warps as context copies them): work/S137_geometry_baselines/RESULT.md. S141 results are not available to
you or to me yet.

Attack the draft. In particular:
1. E2 mechanics in this codebase: if the context slots carry warps at exactly the target poses, what do
   get_translation_scaling_factor, the Plücker reference (slot 0), MultiviewScaleRule (close_frame -> cfg_min for
   targets that coincide with a context pose) and the replace mask do? Does cfg_min = 1.2 at every target make CFG
   nearly irrelevant, and does that matter? Is "context pose = target pose" degenerate for the network (identical
   rays) in a way that makes copying the trivially optimal solution even after training? Would a small fixed pose
   offset, or keeping the original context poses, be a better minimal design? Cite file:line.
2. Is the train-only gate (>= 10% fixed-noise target eps-MSE reduction in 500 steps on 8 clips) meaningful, or will it
   pass trivially because conditioning on an aligned warp makes eps prediction easy at low sigma?
3. E1: is a within-coverage-class pixel permutation the right derangement (it destroys low-frequency colour layout
   too)? Would a spatial shift of the warp by k pixels be a cleaner "misaligned but natural" control? Which one answers
   "does B use aligned geometry" with fewer confounds?
4. Is the branch selection rule sound (e.g. INCONCLUSIVE routed to E2)? Is there a better single follow-up for any
   branch given about 10 RTX 3090 GPU-hours and one H800 job slot?
5. Anything that would make E1/E2 results uninterpretable or unreportable.

Output: write exactly one file, work/agents/CODEX_R256_S142_DRAFT_REJECTION.md: findings table (issue | severity |
evidence | concrete change to the draft), then a corrected minimal E1 and E2 specification. I prefer a correct
negative to an encouraging answer; "do not run E2, write up instead" is an acceptable conclusion.
