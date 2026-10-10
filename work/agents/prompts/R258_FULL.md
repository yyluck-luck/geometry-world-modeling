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
# Brief R258 — IDEATION (turn the findings into a method): what new method do our own measurements suggest? (2026-10-10)

Context you must read first (verify, do not trust): CURRENT_STATUS.md; docs/report/TECHNICAL_REPORT_20261010.md; work/S139_crossseq_revisit/RESULT.md; work/S140_warp_guided/RESULT.md; work/S141_finetune/PROTOCOL.md (S141 = LoRA fine-tuning A and warp-conditioned B; results pending, do not wait for them); work/S142_followup/PROTOCOL.md; your earlier rounds work/agents/CODEX_R253_RETRIEVAL_S141.md, CODEX_R255_IDEATION_AFTER_S141.md, CODEX_R256_S142_DRAFT_REJECTION.md.

The owner explicitly asked for NEW ideas and NEW ways, not only conservative closure. Earlier rounds leaned to "write up"; this round is generative. Still be honest: an idea that is already published must be labelled so (arXiv ID + exact title, verified on arxiv.org).

Assets that can be reused at zero cost: VMem weights and a byte-faithful sampler (work/S140_warp_guided/gen_s140.py, work/S141_finetune/gen_s141.py); VAE latents + CLIP embeddings for every 5th frame of 7-Scenes fire/heads/office/pumpkin/redkitchen/stairs (7400 frames); 2032 fixed training clips with CUT3R+KPS forward warps, VAE warp latents and coverage; LoRA training code (work/S141_finetune/train_s141.py, 1.4 s/step on one RTX 3090, 8.7 GB); S141 adapters A and B (10000 steps); CUT3R+KPS depth/warp pipeline; held-out chess panel (24 windows, S139 contexts, base outputs for seeds 3-6) and RGB-D Scenes panel (16 windows); scorer with PSNR/SSIM and covered/uncovered split. Compute: 2 RTX 3090 (TACC) + 1 H800 job slot (SuperPOD), about 1-2 weeks left.

Process required: (1) diverge: at least 12 distinct ideas, spanning different points of the pipeline; (2) for the 5 most promising, run a prior-art check (verify IDs and titles; state closest work and the precise difference); (3) converge: pick at most 3, and for each give a concrete experiment that can be implemented and run in 1-2 days on the assets above: hypothesis, minimal implementation (which files change), primary contrast with threshold, controls (including the strongest trivial baseline), kill criterion, GPU-hour estimate, and what result would be genuinely interesting to report. (4) Say plainly which single idea you would run first and why.

Lens for THIS round: start from what the project measured and look for a method that exploits it. Examples of measured facts: retrieved history is geometrically better than recent frames (+1.46 dB for a warp) but generation does not convert it; the warp wins PSNR while VMem wins SSIM on chess (complementary errors); the frozen generator polishes covered pixels (+0.24 dB) but hurts uncovered ones on chess; VMem copies aligned same-pose context; KPS fixes the CUT3R scale. Candidate directions to consider and extend (not limited to): memory as weights instead of context (test-time adaptation / per-scene LoRA fitted on the bank frames themselves, then generate); using the warp as a verifier to select among several generated samples (best-of-N by agreement with geometry in covered regions); frequency- or structure-aware fusion that takes low frequencies from the warp and high-frequency structure from generation; retrieval scored by predicted reprojection utility; geometry-consistency reranking across seeds. For each, think about what would make it a real contribution rather than a trick.

Output: write exactly one file, work/agents/CODEX_R258_IDEATION_FROM_FINDINGS.md.
