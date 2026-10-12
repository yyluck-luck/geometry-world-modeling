# W2 completed: measured improvement, failed concentration gate

Status: **COMPLETE — STOP_TESTED_SELECTOR**. Recorded 2026-10-10 UTC.

The frozen source-only rule reduces geometric correspondence error on the fixed new-scene panel, but does not pass the predeclared robustness requirement. The two largest beneficial windows account for too much of the net gain against canonical c0. Stop this tested selector: no threshold adjustment, replacement scene, additional selector or training run was launched after scoring. Keep `new_method_validated=false` and `novelty_authorization=NONE`.

This report supersedes the execution status, not the contents, of the preserved `RESULT.md`, which documented the earlier incomplete download. The protocol and scientific implementation were not changed.

## Measured results

MEASURED: RGB-D Scenes v2 scenes 01–04, four disjoint windows per scene, 16 windows and 64 real CUT3R+KPS candidate reconstructions. Each window has the same four source frames and four future target frames for every arm. Primary error is capped sensor-relative correspondence endpoint error in native pixels; lower is better. Means weight scenes equally and windows equally within scenes. Source: `MANIFEST.json`, `CANDIDATE_SEAL.json`, `scores/RESULTS.json`.

| Arm | Primary error, px | Secondary non-interior error, px |
|---|---:|---:|
| Default single mode c0 | 7.893042 | 8.074738 |
| Simple median inverse-depth fusion | 7.883958 | 8.081737 |
| Source-only selected complete candidate | **5.714834** | **5.939057** |
| Source medoid, diagnostic | 8.132468 | 8.354285 |
| Whole-window GT oracle, diagnostic only | 5.330932 | 5.546773 |

Source for every table value: `scores/RESULTS.json`, `summary_capped_epe_pixels`. The oracle uses sensor depth after selection is sealed and is not a deployable arm.

DERIVED from those measured errors, with ANALYTICAL thresholds frozen in `PROTOCOL.md`:

| Required gate | Against c0 | Against fusion | Decision |
|---|---:|---:|---|
| Aggregate reduction ≥5% | 27.5966% | 27.5131% | Pass |
| Positive mean reduction in every scene | All four | All four | Pass |
| Reduction after removing comparator-specific top two windows ≥2.5% | 14.8515% | 23.3941% | Pass |
| Top-two contribution / net signed improvement ≤50% | **59.6497%** | 31.4863% | **Fail against c0** |
| Abstention ≤25%, shared across comparisons | 6.25% | 6.25% | Pass |

Source: `scores/RESULTS.json`, `comparisons.primary`, `abstention_fraction` and `failed_gates`. The sole failure is `c0:top_two_dominate_net_gain_or_nonpositive_net`; here net gain is positive, so concentration is the reason. The two c0 windows are `scene_02__w0120` and `scene_03__w0360`. The fusion pair is `scene_03__w0120` and `scene_03__w0360`. Deletion analysis preserves equal scene weighting among remaining windows. The main result retains every planned window.

Benefits do not disappear after deletion and are not confined to two windows. Nevertheless, the protocol requires both the deletion test and the concentration test, so the positive deletion result cannot override STOP. The denominator is net signed improvement including harmful windows; the descriptive positive-gain-only denominator gives 52.7096% against c0 and must not replace the frozen one. These percentages are DERIVED from `scores/RESULTS.json`.

MEASURED primary scene means, from `scores/DERIVED_DIAGNOSTICS.json`, `scene_errors`:

| Scene | c0, px | Fusion, px | Selected, px |
|---|---:|---:|---:|
| 01 | 6.336566 | 6.148432 | 5.303481 |
| 02 | 8.650061 | 7.245823 | 5.727841 |
| 03 | 9.439197 | 9.443353 | 5.930608 |
| 04 | 7.146345 | 8.698225 | 5.897407 |

DERIVED window outcomes: selected improves over c0 in 11 windows, ties in four and is worse in one; against fusion the counts are 13 improved and three worse. `scene_04__w0000` is a useful failure example: selected c1 has 9.08082 px versus c0 4.49200 px. Source: `scores/WINDOWS.csv` and `scores/DERIVED_DIAGNOSTICS.json`. No window was removed to hide this failure.

MEASURED selection counts: c0 four, c1 eight, c2 three and c3 one. The sole abstention is `scene_02__w0000`, with insufficient eligible source pairs; it falls back to c0 and remains in every analysis. Matching coverage for every pair/window is preserved in `selection/*.json` (`pair_records`) and summarized in `scores/MATCH_COVERAGE.json`. Source: `selection/SELECTION_SEAL.json`, `scores/DERIVED_DIAGNOSTICS.json`.

MEASURED fixed-order primary errors are c0 7.893042, c1 6.521084, c2 9.366520 and c3 14.020217 px. DERIVED: the selector matches the whole-window oracle identity in 13 of 16 windows and captures 85.0162% of the oracle improvement over c0. These are post-selection diagnostics, not alternate success gates. Source: `scores/DERIVED_DIAGNOSTICS.json`.

## Execution and data separation

Only the missing files in scenes 03 and 04 were acquired: MEASURED 50 and 81 members respectively, 131 new files total. All 324 required files were checked against the frozen archive metadata and receipt hashes, including preservation of previously acquired bytes. Source: `resume_20261010/DATA_COMPLETE.json`, `curl_acquisition/scene_03/receipt.json` and `curl_acquisition/scene_04/receipt.json` under that resume directory.

The original Python HTTP path still failed on a bounded remote retry. The exact failed range succeeded with system curl, so the dated `AMENDMENT_04.json` changed only transport to bounded curl requests with TLS verification, exact ranges, identity checks, CRC and SHA checks. `AMENDMENT_03.json` records the preceding remote attempt. Original failures and receipts remain saved. This demonstrates a working transport repair, not a proven diagnosis of the underlying network failure. No scene, frame, seed, camera convention, selector constant, support rule or decision threshold changed.

Verified chronology, all on 2026-10-10 UTC:

| Artifact | Recorded time |
|---|---|
| Protocol/code freeze | 14:07:36.817279 |
| Complete acquired-data verification | 14:28:50.532010 |
| Candidate seal | 14:34:51.844534 |
| Selection seal | 14:34:57.647343 |
| Completed evaluation | 14:35:04.032282 |

Sources: `FREEZE.json`, `resume_20261010/DATA_COMPLETE.json`, `CANDIDATE_SEAL.json`, `selection/SELECTION_SEAL.json`, `scores/RESULTS.json`. Selection reads source RGB, supplied source cameras and predicted candidates. Sensor-depth images are decoded for evaluation only after both candidate and selection seals. Target RGB was not acquired. Candidate and selector artifact hashes, and every original frozen file hash, were rechecked independently.

The frozen execution ran on the local CPU in two disjoint shards, with fixed seed 0, FP32 and TF32 disabled. Existing TACC GPU jobs were not duplicated. MEASURED summed selection runtime is 5.586814 seconds, including source/candidate loading, matching, scoring and saving but excluding startup and sealing. Source: `scores/DERIVED_DIAGNOSTICS.json` and worker logs. Selector and fusion require four reconstructions, while c0 requires one; this is not an equal-compute or speed claim.

## Independent verification and limitations

- Independent implementation recalculated the saved-match candidate projections, residuals and decisions for every window, then independently aggregated saved evaluator rows and all stop gates. It agrees with the recorded verdict. Scope excludes re-extracting SIFT and independently measuring sensor-depth error on every window. Evidence: `independent/INDEPENDENT_CHECK_RIGID_V2_20261010.json`.
- The original independent checker initially failed its tight numerical tolerance because it used a full matrix inverse whereas the frozen implementation uses the rigid rotation transpose. DERIVED maximum pose orthogonality residual is 1.31e-9; maximum projection difference is 7.12e-7 px. No selected identity, abstention, validity mask or gate changed. The original failure is preserved; only a separately named checker was corrected to the frozen convention, with tolerances unchanged. Its maximum residual difference is 1.41e-14. Evidence: `independent/INDEPENDENT_ORIGINAL_FAILURE_20261010.json`, `INDEPENDENT_FULL_NUMERIC_COMPARISON_20261010.json` and `INDEPENDENT_RIGID_V2_EXECUTION_RECEIPT_20261010.json` in the same directory.
- A separate sensor-depth metric implementation remeasured the predeclared first window `scene_01__w0000`: all 57 checks agree, including all pair support counts and 105146 correspondence tuples, with maximum absolute difference 7.03e-17. This validates one window, not an independent full-panel rerun. Evidence: `independent/INDEPENDENT_METRIC_CHECK.json`.
- The bounded post-result reviewer independently verified frozen/sealed hashes and aggregate arithmetic and confirmed the same interpretation. Evidence: `POST_RESULT_REVIEW.md`.

Implementation tests are not research findings. Preserved pre-run receipts show 114 repository tests and 46 stage tests passing (`logs/repo_tests.log`, `logs/stage_tests.log`). This resume added 11 passing transport boundary checks (`resume_20261010/CURL_HELPER_BOUNDARY_TESTS.json`) and 10 passing tests of the independent checker repair (`independent/INDEPENDENT_RIGID_V2_EXECUTION_RECEIPT_20261010.json`). These are distinct scopes; the repository suite was not needlessly rerun after unchanged scientific code. No root linter is configured.

Only four new-to-project scenes were tested, with supplied dataset camera poses; those poses can themselves depend on RGB-D estimation. Thus source-only selection does not establish completely depth-independent monocular deployment. New-to-project does not establish absence from model pretraining. The endpoint is geometric correspondence on sensor-defined visible support, not generated-video quality, calibrated uncertainty, population significance or CCF-A novelty. Many pixels do not create many independent scenes. These limitations remain despite the positive measured mean.

## S141 and handoff

MEASURED remote state as of **2026-10-10 14:40:21 UTC**: both final A/B adapters exist and both training chains have reached their planned completion; the existing A and B evaluations are progressing, with a separate A scoring session also present. Final `SCORES_chess_A.json`, `SCORES_chess_B.json` and final analysis were not present in the inspected evaluation tree. Both adapter check receipts and the baseline verification file exist; existence alone is not a verified score or final scientific conclusion. Evidence: `resume_20261010/TACC_INITIAL_STATUS.txt`, `TACC_FINAL_STATUS.txt` and `TACC_DELIVERY_STATUS.txt`. The attempted `chainA.log` pathname in the final snapshot was absent; the earlier training-completion and adapter evidence, not that absent file, supports the A status.

No S141 run, evaluation or scoring task was resubmitted, modified or interrupted. The inspection shell was closed while the existing sessions continued. The useful follow-up is to read and verify the existing S141 final outputs when available, not repeat them. Do not resume this W2 selector automatically after its stop.

Raw stage retained at `/Users/rocket/Documents/Codex/2026-10-10/i-m-sharing-my-github-repo/work/week1-wt/work/W2_source_selection_20261010_codex`. Exact model/selection/scoring commands are in the frozen `RUN_worker0.sh`, `RUN_worker1.sh` and `RUN_SCORE.sh`; actual transport resume command is `resume_20261010/RUN_CURL_ACQUIRE.sh`. Runtime source/checkpoint hashes are in `PINNED_INPUTS.json`, `FROZEN_CUT3R_CODE.json` and `resume_20261010/RUNTIME_PREFLIGHT.json`. Existing outputs must be retained; these command records are for reproduction in a separate output location, not an instruction to rerun this stopped experiment.

Changed files are confined to the isolated branch: the W2 resume helper, dated transport amendments, execution receipts, predictions, selections, measurements, independent checks and this new report; plus `RESEARCH_MEMORY.md`, `RESEARCH_LOG.md`, `research_events.jsonl` and `workflow_checks.jsonl` for continuity. The primary checkout and the earlier incomplete deliverable snapshot were preserved. No commit or push was made. The completed export includes code, all original frozen files, score tables, seals and audit receipts; bulky raw data and candidate arrays remain in the retained raw stage and are explicitly excluded in the export manifest.
