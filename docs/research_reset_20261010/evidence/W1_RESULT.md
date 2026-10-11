# Week 1 result: complete geometry candidates versus single geometry

**Verdict: GO_TO_CONSUMER_PILOT under the frozen protocol.** The tested candidate family has an offline geometric upper bound worth testing further. There is no validated deployable selector, video improvement, or new-method claim.

## What actually ran

MEASURED: four complete CUT3R + KPS reconstructions for each of sixteen previously exposed RGB-D Scenes v2 windows, covering scenes 13 and 14. The same four source RGB frames and known optical poses were supplied in four cyclic orders, then restored to canonical frame identity. All sixty-four reconstructions completed successfully. Each candidate includes all four source depth maps; the oracle selects one candidate jointly for all four target views in that window.

TACC was inspected first. gpu13 GPUs 3 and 4 were already running S141 A/B with evaluation chains waiting; no final A/B adapter or score was present at the final read-only check (2026-10-10T12:10:13Z). Other devices had resident services. gpu14 returned an NVML driver/library mismatch. Those tasks and services were left untouched. This geometry-only gate ran in two local CPU workers, using the existing environment and weights; no new GPU or training task was launched. Evidence: `receipts/TACC_INITIAL_STATE.json`, `receipts/TACC_FINAL_STATUS.txt`, `logs/baseline.log`, `logs/alternatives.log`, and per-candidate receipts.

Protocol frozen: 2026-10-10T12:04:04.002913+00:00. All predictions sealed: 2026-10-10T12:11:05.888118+00:00. Scoring completed: 2026-10-10T12:11:18.499171+00:00. No sensor depth or target RGB was read by the predictor. All candidate files were sealed before scoring opened sensor measurements.

## Primary measured result

MEASURED endpoint: equal-window mean capped correspondence error in native-image pixel equivalents; lower is better. Invalid predictions remain in the denominator with the maximum penalty. All arms share sensor-defined interior/visibility support. This is not PSNR, generation quality, or error against perfect geometric truth. Values below come from `scores/RESULTS.json` (`primary`); relative improvements are DERIVED from those measured errors.

| Arm | Capped correspondence error, px |
|---|---:|
| Canonical c0, also the best aggregate fixed order | 8.2272 |
| Fixed c1 | 8.4966 |
| Fixed c2 | 11.6692 |
| Fixed c3 | 11.0226 |
| Source-only inverse-depth median fusion | 8.4104 |
| Source-only medoid selection | 9.6200 |
| Complete-candidate oracle | 5.9868 |
| Scale-only oracle | 6.6570 |
| Scale-normalized complete-candidate oracle | 6.9340 |

| Frozen gate | Observed, DERIVED | Requirement | Outcome |
|---|---:|---:|---|
| Whole-window oracle improvement over c0 | 27.23% | at least 10% | PASS |
| Improvement positive in both scenes | 36.41% / 14.75% | both positive | PASS |
| Gain over best aggregate fixed order | 27.23% | at least 5% | PASS |
| Gain over better fusion/medoid single map | 28.82% | at least 5% | PASS |
| Gain over scale-only oracle | 10.07% | at least 5% | PASS |
| Normalized-candidate headroom over c0 | 15.72% | at least 10% | PASS |

The secondary stratum without the interior-neighbour exclusion agrees descriptively: 26.57% headroom. The primary support contains 1,802,797 source-target tuples, but these are correlated measurements, not that many independent samples. The windows overlap; only two scenes were tested. No population significance or independent-window confidence interval is claimed.

## What is encouraging, and what is weak

The candidate selected with GT varies by window, while c0 remains the strongest globally fixed order. Consequently, the measured opportunity is not explained by choosing a single universally better processing order. Scale variation explains part, but not all, of the aggregate upper bound. Selecting one complete candidate per window is almost as effective as permitting a separate candidate per target (5.9868 versus 5.9381 px); allowing a separate choice for each tuple lowers the ceiling further (4.2032 px). These are oracle diagnostics, not deployable algorithms.

The practical controls are negative: source-only fusion raises error by 2.23%, and the source-only medoid raises it by 16.93%, relative to c0. The offline oracle sees the scoring answer. It proves that a useful choice exists within this panel, not that a consumer can identify or exploit that choice.

DERIVED, explicitly post-score concentration analysis (`scores/DERIVED_DIAGNOSTICS.json`): 71.63% of summed window improvement comes from scene_13 w0150 and w0000. No windows were removed and no gate was retuned. This concentration makes broad claims weak. Also, scene_14 alone has only 7.06% normalized headroom and 3.92% advantage over its scale oracle. Those per-scene nuisance results are weaker than the aggregate; the registered nuisance thresholds applied to the aggregate only.

## Verification and bounded decision

Implementation checks passed: repository unittest suite 114/114 (after populating sparse-checkout dependencies and using the existing general environment), and stage tests 23/23. Initial environment/sparse-checkout failures are retained in the earlier test logs; no unrelated repository source was changed. No configured root linter was found.

Independent numerical check: another implementation, without importing the scorer, reconstructed the preselected scene_13 w0000 support and all four candidate errors. It matched all support counts and the measured errors within the predeclared tolerance, and independently recomputed aggregate/scenario gates. See `INDEPENDENT_RECHECK.json` and `independent_recheck.py`. This is team-internal independent implementation verification, not external replication.

The stopping conditions did not trigger. The authorized first-week gate is complete. The next justified step is one small, separately frozen consumer or source-only selection pilot, with unseen-scene evaluation and compute-matched single-mode controls. Do not launch a large training sweep from this result. Existing S141 jobs continue independently; consume their final evaluation once available instead of duplicating them.

`new_method_validated=false`; `novelty_authorization=NONE`.

## Files, rerun and preservation

Worktree: `/Users/rocket/Documents/Codex/2026-10-10/i-m-sharing-my-github-repo/work/week1-wt`; branch `codex/week1-geometry-modes`; base commit `7cefe20ede81597b32517b49a9f0bbdf35278b10`. The primary checkout and its pre-existing dirty files were not modified. Continuity files were updated only in this isolated worktree, after saving backups.

`RUN_COMMANDS.sh` records the exact original execution. Completed candidate predictions have checksum-verified resume support; score/seal publication refuses to overwrite previous outputs. For a new full reproduction, use a fresh output directory and a new execution receipt while retaining the scientific protocol. The scored result is never overwritten in place.

Raw predicted arrays remain under `/Users/rocket/Documents/Codex/2026-10-10/i-m-sharing-my-github-repo/work/week1-wt/work/W1_joint_geometry_20261010_codex/candidates` and are excluded from Git to avoid enlarging the repository. Candidate JSON receipts, source/checkpoint hashes, protocol, code, tests, logs, full per-window scores, and independent check are included in the user-facing evidence bundle. Existing source images and the existing CUT3R checkpoint are reused, not copied into that bundle.
