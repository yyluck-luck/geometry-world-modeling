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
# Brief R264 — IDEATION after the S143 discovery result (2026-10-10)

Read work/S143_context_ranking/PROTOCOL.md (with Amendments 1-3), results/S143_ANALYSIS.json, results/WARP_SCORES.json,
POOL.json, and the S141 result (work/S141_finetune/RESULT.md). Fresh-seed (42,7,1,2) generation for S143 is running; its
scores are not available to you or to me.

Discovery facts (verify): on 24 exposed chess windows, R_2seed_hindsight = +0.320 dB [+0.19, +0.46] (above the frozen
panel-null 95th percentile 0.291; panel tail p 0.035); window-specific structure +0.275 over the best single rule.
Per-rule mean generated PSNR: nearest-4 (four bank frames with the smallest mean pose distance to the targets, no NMS)
11.94; coverage-greedy (union forward-splat support over 32-frame-bank CUT3R depth) 11.92; mem_pose 11.58; static 11.49;
random 11.38; VMem's own surfel retrieval (mem_vmem) 11.19 - the lowest. The warp prefers coverage-greedy (best in 14/24
windows; mean warp PSNR 15.41 vs 14.38 for mem_vmem). Within-window Spearman(Q_W, Q_G) = 0.16. Sorting mem_vmem's frames
into bank order lowered its warp from 14.57 to 14.38 dB (CUT3R depends on frame order).

Tasks:
1. Reconcile with VMem's own Table 4 (arXiv 2506.18903: surfel retrieval 14.82 vs camera distance 13.27 dB, K=4, cycle
   trajectories on RealEstate10K). Read the paper's retrieval definitions closely: is their "camera distance" baseline the
   same as our nearest-4, and is our mem_vmem the same as their surfel retrieval (NMS, candidate filtering, last-target vs
   all-target query)? Which differences in regime could produce opposite orderings? Verify in the source
   (data/S134_tacc/vmem_src/modeling/pipeline.py get_context_info) and the paper.
2. Diverge (>= 10 ideas) on what this suggests: e.g. diversity-NMS hurts a generator that copies aligned content;
   generator-aware retrieval (proximity) vs geometry-aware retrieval (coverage); combining nearest-4 contexts with adapter A;
   a hybrid retriever that uses coverage for the warp and proximity for the generator; slot-order effects; etc. Prior-art
   check the 5 most promising (verify IDs and titles).
3. Fresh confirmation: chess is exposed, the other 7-Scenes rooms are S141 training data. Identify genuinely untouched,
   downloadable posed RGB(-D) data with revisits suitable for this assay (e.g. RGB-D Scenes v2 scenes other than 13/14,
   TUM RGB-D sequences not used before, ScanNet test scenes, 12-Scenes, Cambridge Landmarks...). Check the project's
   exposure records (docs/, RESEARCH_MEMORY.md) and the datasets' availability/size/licence from their official pages.
   Propose ONE fresh-scene confirmation design (rooms, windows, banks, which contrasts, seeds) that could run in about
   a day on 2 RTX 3090, with the frozen choices from S143.
4. Converge to at most 3 experiments, name the first, with primary contrasts, thresholds, controls, kill criteria,
   GPU-hours. "Write up now" remains an acceptable answer for any candidate.

Output: write exactly one file, work/agents/CODEX_R264_IDEATION_AFTER_S143.md. I prefer a correct negative to an
encouraging answer.
