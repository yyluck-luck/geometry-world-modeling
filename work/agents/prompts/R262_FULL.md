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
# Brief R262 — IDEATION after the actual S141 results: what new method or experiment do they suggest? (2026-10-10)

Read work/S141_finetune/RESULT.md and results/S141_ANALYSIS.json (S141 finished), CURRENT_STATUS.md, and your earlier
ideation rounds R255, R257, R258, R259 (work/agents/CODEX_R25*.md). The owner explicitly wants NEW ideas and ways and
wants the GPUs used (2 RTX 3090 on TACC; SuperPOD H800 currently refusing SSH; about 1-2 weeks left).

Facts to start from (verify in the files): attention-LoRA adapter A (10000 steps on 6 other 7-Scenes rooms) improves VMem
on held-out chess (+0.33 dB memory contexts, +0.45 static) and on RGB-D Scenes (+1.16 dB); the monitor denoising loss did
not move. Warp-conditioned B (zero-init conv on warp latent+coverage) is ~3.6 dB below the warp it receives, base-level
PSNR but the highest chess SSIM, and worse than base on RGB-D. After adaptation, retrieved memory contexts are still worse
than recent ones (-0.33 dB). Training-free warp-guided RePaint (S140) was +0.02 dB over the warp on chess with the frozen
model. Adapters A and B, the sampler, warps (chess/RGB-D, static and memory contexts) and the S140 WGS code all exist.

Process: (1) diverge, at least 12 ideas, including ones that combine what worked (A) with what nearly worked (WGS, warp
covered-region polish), diagnoses of why B failed (with cheap tests), and genuinely new directions; (2) prior-art check of
the 5 most promising (verify arXiv IDs and exact titles); (3) converge to at most 3 experiments runnable in 1-2 days on
the existing assets, each with hypothesis, minimal implementation (files), primary contrast and threshold, strongest
trivial baseline, kill criterion, GPU-hours; (4) name the one to run first. Note that chess is an exposed panel now:
say what a fresh confirmation set would have to be (e.g. other 7-Scenes rooms are training data; which held-out data
remain?).

Output: write exactly one file, work/agents/CODEX_R262_IDEATION_AFTER_S141_RESULTS.md.
