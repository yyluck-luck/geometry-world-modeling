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
# Brief R265 — REJECTION of the S146 draft (fresh-room 12-Scenes replication) before freezing (2026-10-10)

Read work/S146_fresh12/PROTOCOL_DRAFT.md; it adopts your R264 E1 (work/agents/CODEX_R264_IDEATION_AFTER_S143.md) with
concrete choices made from metadata only (no 12-Scenes image has been viewed): rooms apt1/kitchen, apt2/luke (apt2/bed,
kitchen, living have invalid poses in sequence0/1; replacement rule stated), office2/5a; resize 1296x968 -> 640x480 with
per-axis scaled intrinsics so the existing 640x480 pipeline runs unchanged; H = sequence0, C = sequence1.
Code to be reused: work/S139_crossseq_revisit (run_retrieval_s139.py, pose_arms_s139.py, convention_check_s139.py,
baselines_s139.py, kps.py), work/S143_context_ranking (build_pool_s143.py, warps_s143.py, score_warps_s143.py,
analyze_s143.py), work/S141_finetune/gen_s141.py, work/S140_warp_guided/score_s140.py.

Attack it concretely: (1) the room-substitution rule and whether it is legitimate before freezing; (2) the resize +
intrinsics transform (pixel-centre map; anisotropic factors 640/1296 vs 480/968; VMem's own rgb() then resizes 640x480
to 768x576 and crops 96 px: any hidden assumption on aspect or K in the pipeline, CUT3R crop, depth mapping, KPS,
retrieval code, scorer?) — cite file:line; (3) whether H = sequence0 / C = sequence1 gives genuine cross-traversal
revisits and whether the 8 start formula and 106-frame span fit (N_C = 358, 593, 534); 12-Scenes frame rate vs 7-Scenes
for the 60-105 frame target offsets; (4) the primary (nearest-4 vs bank-sorted mem_vmem on evaluation seeds, room-equal,
3/3 rooms, 3/4 seed panels) and whether discovery seeds should be used at all; (5) anything in step-A retrieval
(run_retrieval_s139.py) that depends on chess/7-Scenes specifics (priming chunks, NMS threshold init at 5 frames, frame
id parsing, K usage); (6) budget and the order relative to S144/S145; (7) anything else that would make the replication
uninterpretable.

Output: write exactly one file, work/agents/CODEX_R265_S146_DRAFT_REJECTION.md: findings table (issue | severity |
evidence | concrete change), then a corrected minimal specification. I prefer a correct negative to an encouraging answer.
