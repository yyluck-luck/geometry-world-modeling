# S75 independent saved-result review

PASS for saved-result identities and arithmetic: 202/202 checks, no blockers. Reviewed by `/root/c2_v9_source_primary` at 2026-09-09T08:34:58.252282+00:00.

The single bounded verifier ran 2026-09-09T08:31:05.734361+00:00–2026-09-09T08:31:08.630294+00:00; return 0, no timeout, 2.895733 s under a 60 s external limit. Identity pins and tolerances were frozen before this run. The source review is post-execution and does not claim a retroactive prelaunch review.

Python scalar differences and `math.fsum` independently recomputed unclipped raw MSE/MAE; scalar quantization reproduced every decoded PNG pixel byte. All five reference tensor body hashes match S68. Maximum raw-score discrepancy was 6.938893903907228e-18, and the largest saved-coordinate/statistic discrepancy was 4.440892098500626e-16. Frozen tolerances: raw absolute 1e-12 / relative 1e-10; coordinate absolute 1e-9 / relative 1e-12. Identities, quantized bytes, counts and fractions were exact.

| History | Raw MSE | Raw MAE | Matches / source features | Availability | Median displacement px | p95 px | Matches >10 px |
|---|---:|---:|---:|---:|---:|---:|---:|
| 12 | 0.0030294796 | 0.0351155172 | 331 / 864 | 38.31% | 0.538384 | 2.246750 | 2 |
| 13 | 0.0023554933 | 0.0315610440 | 368 / 710 | 51.83% | 0.473497 | 2.185670 | 4 |
| 14 | 0.0040734555 | 0.0386592239 | 487 / 1447 | 33.66% | 0.538518 | 2.279993 | 7 |
| 18 | 0.0044893037 | 0.0400692812 | 463 / 1468 | 31.54% | 0.523430 | 2.256433 | 4 |
| 19 | 0.0040323075 | 0.0380160334 | 389 / 1234 | 31.52% | 0.498168 | 2.435359 | 8 |

All five outcomes, full coordinate displacements, 25/50/75/95 percentiles, cutoff counts and coverage comparisons are retained in `receipt.json`; the JSON review preserves per-row range and out-of-range counts. Raw reconstructions contain values outside [-1,1], retained in the raw errors and clipped only for PNG. Availability is 31.52%–51.83%; small median displacement among matches does not certify the rest of the image.

Actual read scope: 44 unique files / 45,430,184 file bytes, including ten saved FP32 arrays and ten saved PNGs. Decoded scientific bodies total 49,766,400 bytes (39,813,120 FP32 + 9,953,280 RGB). No original photos, latent bodies, weights, model or feature extraction were read or rerun. PNG decoding was for byte verification, not visual QA.

Source, worker and progress records consistently report five decode calls and one weight-byte load. This is receipt/source corroboration, not independent live observation. The loaded variant remains declared ft-mse; original SD2.1 VAE identity remains UNKNOWN.

Raw errors use the declared [-1,1] scale and no clipping; fixed nearest PNG quantization differs from S70’s truncation-based uint8/255 appearance definition. Do not directly compare these error numbers to S70. One scene’s five cached mean-latent roundtrips do not test generated-latent behavior, prove full-pipeline compatibility, identify the cause of S70 framing mismatch, or validate a new method. Saved match truth was not independently verified.

Verification receipt SHA256: `3ca87db455613ea0a87c3420055f6add467ceb513b9065c9ad64e90e83f2aa16`.
External receipt SHA256: `862b09d31d41fd1c8e90f4adb351f79389d44ecbac6f6b6a48fedd1608015b89`.
Machine-readable result review SHA256: `da1fa65336f2a50dfde9034ffdb06b89dadbd3f434684944b7a83fabca211aff`.
