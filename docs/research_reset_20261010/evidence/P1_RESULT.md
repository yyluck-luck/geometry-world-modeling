# P1 completed: stop the tested region-by-frequency residual policy

Date: 2026-10-10, America/Los_Angeles. Decision: **STOP_TESTED_POLICY**. This candidate was frozen, implemented, actually executed and independently checked. It was not stopped at a plan. Do not tune or rename this policy to rescue it.

## What was tested

A six-coefficient bounded linear policy combined existing geometric warp W with residuals from frozen S140 generation G, separately in covered/hole regions and three spatial frequency bands. Coefficients were trained on two sequence pairs with seeds 3,4 and applied to the held-out pair with seeds 5,6, rotating all three folds. Eleven fixed simpler controls received the same training supervision where applicable. This is an exploratory cross-traversal test in the previously exposed chess room, not source-only adaptation, unseen-scene generalization, or a new memory mechanism claim.

No query depth was used. Fold-local held-out RGB was excluded from fitting; all predicted outputs were sealed before final scoring. Earlier access to each pair's RGB for other folds is explicitly disclosed in AMENDMENTS.md.

## Main finding

The two existing image sources have useful complementary errors, but almost all of this policy's benefit is already captured by simple fusion. The extra region-by-frequency complexity is not supported as a worthwhile method advance.

All numbers below are **DERIVED** from actual stored predictions scored in `collection-20261010T180045Z/results/SCORES.json`; complete bootstrap and per-pair values are in `RESULT.json` in that directory.

| Method | Mean PSNR, dB | Mean SSIM |
|---|---:|---:|
| Original geometric warp W | 14.572388 | 0.431766 |
| Archived generation G | 14.554733 | 0.454274 |
| One learned constant coefficient | 14.977950 | 0.473655 |
| Two region coefficients | 14.992694 | 0.473281 |
| Three shared frequency coefficients | 15.020443 | 0.479312 |
| Candidate: six region × frequency coefficients | 15.026185 | 0.476948 |

Candidate versus W: +0.453797 dB, descriptive window CI [0.374947, 0.533770], all 24 windows positive. Constant fusion alone gains +0.405562 dB versus W. Candidate versus the strongest control (three shared frequency coefficients): only +0.005742 dB, CI [0.003310, 0.008218], with SSIM **-0.002363**. A tiny positive interval does not satisfy the preregistered practical threshold.

Three frozen gates fail: at least +0.2 dB over every simpler control; no SSIM loss against the strongest control; and at least +0.1 dB after removing the best two windows. The remaining three gates pass. The two best windows contribute 20.55% of positive gains; removing them leaves only +0.004829 dB. The problem is insufficient extra benefit, not domination by those two windows. Pair-level gains over the strongest control are +0.002181, +0.007192 and +0.007852 dB.

A separate fixed Gaussian control also yields higher SSIM than this candidate; full control results remain in the JSON. We do not select a new metric or claim a rescued success. A failure of this preclip-MSE-fit policy is not a theorem against all adaptive fusion families.

## Execution and independent verification

MEASURED execution: job `codexp1_20261010` on gpu13 exited 0. Runtime was 258.625 seconds with two CPU threads and CUDA hidden; GPU use was 0 GPU-hours. It produced all 48 held-out cells, each with all 12 methods. Original S141 jobs were untouched; B and W2 remain stopped. S143 context-ranking was not duplicated.

All 96 archived generation hashes matched their historical run receipts before dispatch. Every input was rehashed at execution. Recomputed original W/G baselines agree with historical scoring within 3.56e-15 dB PSNR and 1.50e-7 SSIM. All predictions and coefficients were hashed before scoring. Predictions occupy 2,293,241,856 bytes remotely and are preserved under `/mnt/gluster_dcpu/yiyangliu/gwm_codex_p1_20261010/results/predictions`.

Independent checks used a separate Cholesky/BVLS optimizer and independent aggregation code, not the pilot optimizer/analyzer. Fit coefficients agree within 1.45e-15; every final gate agrees, and the largest aggregation discrepancy is 5.33e-15. Exact cells, finite values, fold exclusion and score/seal/hash binding passed. The independent reviewer did not reread all remote prediction pixels; it checked stored score arithmetic and metadata, while the execution scorer checked prediction hashes and baseline agreement.

Evidence: `DISPATCH_INTENT.json`, `DISPATCH_RECEIPT.json`, `INPUT_PROVENANCE_CHECK.json`, `INDEPENDENT_FIT_CHECK.json`, `INDEPENDENT_RESULT_CHECK.json`, and the final collection directory. Reproducibility uses the saved code/protocol/input fingerprint. The original `dispatch.py` refuses a duplicate intent; never rerun it against the existing job path.

## Research decision and continuity

Retire this exact supervised region-by-frequency policy. Do not spend GPU time developing it from this result or report simple blending as a novel memory contribution. No further experiment is authorized within this completed cycle. The next scheduled cycle may consider one genuinely different mechanism under the existing owner's authorization, after checking newer repository work and active jobs. It must not duplicate S143, revive B or W2, or simply rename this fusion policy. Keep `new_method_validated=false` and `novelty_authorization=NONE`.

Prior-art checks and exact verified arXiv titles/IDs are retained in PROTOCOL.md. Broad adaptive fusion and frequency guidance are already known. This negative gate is the useful output of this cycle; it does not meet a CCF-A innovation bar.

## Changed files and follow-through

- New isolated stage `work/P1_residual_bands_20261010_codex/`: frozen protocol/amendment, CPU implementation, numerical tests, one-shot dispatch, read-only collection and provenance.
- Updated `work/S141_autonomous_workflow/WORKFLOW_STATE.json` and `CHECK_LEDGER.jsonl`: S141 final; P1 completed and stopped; no active pilot.
- Updated isolated `RESEARCH_MEMORY.md`, `RESEARCH_LOG.md`, `research_events.jsonl`: concise continuity. Primary checkout unchanged.
- Deliverables: this report, S141 FINAL_REVIEW.md, preserved results and receipts. Validation: 114 repository tests and four numerical pilot tests passed; no repository linter configured. Tests are not experimental evidence.

Follow-through is automatic; no owner decision is currently required. Next wake resumes from the stopped candidate, not from S141 monitoring or a new audit round.
