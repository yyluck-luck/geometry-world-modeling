# Amendments

## 2026-10-10T17:55Z — pre-execution clarification, no result viewed

Cross-fitting necessarily reads a pair's RGB when that pair is training data for other folds. The target-read restriction is fold-local: the held-out pair contributes no sufficient statistics, fitting loss, coefficient selection or prediction inputs to its own fold. After all coefficients and predictions are sealed, the scoring phase may use all held-out RGB. The implementation accumulates pair-separated training statistics using seeds 3,4 and excludes the held-out pair when fitting each fold. This clarifies the original protocol's overly broad wording; data, model, baselines, gates and budgets are unchanged.

Baseline identity agreement allows PSNR absolute error <1e-8 dB and SSIM <2e-6 for CPU batching roundoff; this is an integrity tolerance, not a gain threshold. No outcome has been computed.
