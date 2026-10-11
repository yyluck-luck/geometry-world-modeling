# Operating instructions (read before the brief below)

You are running inside a checkout of the project repository with read access and network. **Verify, do not trust.** Every factual claim below is checkable from this repo or the public literature. Where you cannot check something, say so explicitly.

## What you can verify here (updated 2026-10-11)

- One-page state: CURRENT_STATUS.md. Ledger: RESEARCH_MEMORY.md (NEWEST entries at the TOP; written in Chinese, read it anyway). Current report: docs/report/TECHNICAL_REPORT_20261010.md (S133-S141, S143; S144-S146 not yet written in).
- VMem source used by all GPU runs (mirror of the SuperPOD transport): data/S134_tacc/vmem_src (modeling/pipeline.py, modeling/network.py, modeling/modules/transformer.py, modeling/sampling.py, utils/util.py). Older pinned copies (SHA-256 90a45f45...) are at work/S17C_interface_preparation/isolated_vmem_source.
- Stage folders with PROTOCOL.md (frozen before runs), code, RESULT.md: work/S133_* ... work/S141_finetune, work/S143_context_ranking, work/S144_A_wgs, work/S145_B_diagnosis (all finished); work/S146_fresh12 (operational assay running on TACC; no S146 generation scores exist yet).
- Self-audits: work/agents/SELF_AUDIT_S139.md ... SELF_AUDIT_S145.md. Earlier codex rounds: work/agents/CODEX_R250_S133_S137_AUDIT.md and others.
- Large GPU artifacts (adapters, generated frames) live on the TACC cluster; score files, receipts and analyses are in each stage's results/.

## Hard constraints for THIS run
- No GPU, no training, no weight or dataset downloads, no Slurm submissions, no SSH to clusters. Read, compute on CPU, search the web.
- No contact with anyone. No messages, issues, PRs, emails.
- Write only the output file(s) or directory the brief names. Modify no other file.
- `new_method_validated=false`, `novelty_authorization=NONE`. Nothing you write changes them.

## Concurrency
Other codex processes and the main agent work in this checkout at the same time. Do not delete, revert or "clean up" any file you did not create. Report anomalies; leave them alone.

## Evidence standard
Cite file:line for every code claim and arXiv ID + exact title (+ section) for every literature claim. Every "I ran this" claim must include the exact command and its complete output. I prefer a correct negative to an encouraging answer; you are expected to reject my ideas when they are wrong, redundant with prior work, or untestable.

## Language
Work entirely in English and write your output entirely in English.
# Brief R271 — IDEATION after S141–S145: new ways to make a fine-tuned generator use geometric memory (2026-10-11)

The owner wants new ideas and is willing to spend GPU time on fine-tuning the generator. Resources: two RTX 3090 (24 GB)
on TACC gpu13, about 1–2 days per experiment; no H800 access at present. Generate genuinely new options, then reject
hard.

## Findings to verify first (each stage folder has PROTOCOL.md + RESULT.md + results/)
- S139: VMem retrieves geometrically better history frames (their warp +1.46 dB over static frames), yet generation from
  them ties static (−0.18 dB). S140: training-free warp-guided sampling does not replicate on held-out chess (+0.02 dB).
- S141 (`work/S141_finetune/`): adapter A (LoRA r16 on all attention projections, 10k steps on six other 7-Scenes rooms)
  improves held-out chess +0.33 dB and RGB-D Scenes +1.16 dB, but memory is still not useful after adaptation
  (A_mem − A_static −0.33 dB). Adapter B (A + zero-init warp-latent/coverage input conv) is −3.56 dB below the raw warp.
  Read how training clips were built (build_clips_s141.py, s141_common.py, train_s141.py): which context frames did
  training show the model, and how do they differ from retrieved memory contexts at test time?
- S143 (`work/S143_context_ranking/`, exposed chess): for the frozen generator, nearest-4 contexts beat VMem's own surfel
  retrieval by +0.74 dB on fresh seeds; the warp prefers coverage-greedy sets; within-window Spearman(Q_W, Q_G) = 0.16.
- S144 (`work/S144_A_wgs/`): terminal release null; a development-fitted global blend of generated output and warp
  (α ≈ 0.55–0.6) beats A + warp-guided sampling by ~0.2 dB (optimistic, never tested on a case panel).
- S145 (`work/S145_B_diagnosis/`): under B's own LoRA the warp branch helps (B_off −0.42 dB; target-only −0.33 dB, 0/24
  windows), so the context-bias explanation fails; B's deficit to A (−0.59 dB) sits in its co-trained LoRA.
- S146 (`work/S146_fresh12/`, running): operational nearest-4 vs original-KPS VMem retrieval on three untouched 12-Scenes
  rooms with the frozen generator. No outcome exists. Condition your plan on both outcomes.

## Tasks
1. Diagnose in one paragraph why fine-tuning fixed the domain gap but not memory use. Use the training code: is there
   any training signal that rewards using non-adjacent, retrieved, partially overlapping context? What does S145 imply
   for any warp-conditioned retraining?
2. Diverge: at least 12 distinct ideas, spanning training data (e.g. revisit-structured clips with retrieved contexts),
   objectives (e.g. context-dropout contrast, consistency to warped evidence on covered pixels only), architecture
   (anchored branches, frozen-A LoRA plus a small branch), sampling, evaluation, and at least two ideas that abandon the
   VMem framing for a different contribution. For each: one-line mechanism, why it could work here, the quickest
   falsification, cost on 2×3090.
3. Prior-art check for the 5 most promising, with verified arXiv IDs and exact titles (2025–2026 work on memory-
   conditioned or warp-conditioned video/multiview diffusion fine-tuning, revisit consistency, retrieval for world models).
   Mark each idea new / incremental / already done.
4. Data exposure: list what is exposed or already used (read RESEARCH_MEMORY.md, docs/, stage protocols): 3DMatch
   scenes, 7-Scenes (chess evaluation; six rooms S141 training), RGB-D Scenes panel, the three S146 12-Scenes rooms. Propose
   training and evaluation data that keep evaluation untouched (e.g. the remaining 12-Scenes rooms, other public posed
   indoor RGB-D sets); check availability, size and licence on official pages.
5. Converge to at most 3 experiments for 2×3090, ranked, the first named, each with: hypothesis, primary contrast and
   practical threshold, required controls (including an A-only and a same-compute control), kill criteria, GPU-hours,
   data, and what changes if S146 replicates vs fails. "Write up now" is an acceptable answer.

Output: write exactly one file, work/agents/CODEX_R271_IDEATION_AFTER_S145.md. I prefer a correct negative to an
encouraging answer.
