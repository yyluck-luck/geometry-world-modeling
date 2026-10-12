# W2 source-only candidate selection: execution incomplete

**Verdict: INCOMPLETE_DATA_ACQUISITION. No scientific outcome has been measured.**

The protocol, implementation, controls and stop rules were frozen before new-scene payload access at 2026-10-10T14:07:36.817279+00:00. Data acquisition then failed on both the local Mac and a bounded TACC fallback. No CUT3R candidate was generated, no selection was made, and no sensor-depth image was decoded. Consequently this run does not support either a positive or a negative claim about source-only selection or concentration of its benefits. Evidence: `FREEZE.json`, `receipts/FINAL_EXECUTION_STATE.json`.

## Frozen experiment

ANALYTICAL design choices: RGB-D Scenes v2 scenes 01–04, four non-overlapping windows per scene, starts 0/120/240/360. Four cyclic CUT3R+KPS reconstructions per window are shared by the candidate selector and inverse-depth median fusion; canonical c0 is the single-mode baseline. Two local CPU workers were prepared because TACC GPUs were already occupied by existing tasks. They were not launched.

The selector uses mutual SIFT correspondences, supplied source camera poses/intrinsics, fixed epipolar/parallax checks, and source-to-source reprojection residuals. It selects one complete geometry candidate for the whole window and falls back to c0 when source support is insufficient. It never reads sensor depth or target appearance. Choices and predictions must be sealed before measured-depth scoring. This is a classical diagnostic selector, not an established novel method. Evidence: `PROTOCOL.md`, `MANIFEST.json`, `select_candidates.py`, `PROTOCOL_REVIEW.md`.

ANALYTICAL pass rule: at least 5% aggregate reduction against BOTH c0 and fusion, positive gain in every scene, at least 2.5% gain after removing the two largest beneficial windows, those two contributing at most 50% of net gain, and at most 25% fallback. Every gate is required. Failure stops this exact selector; missing data is an execution failure instead. The baseline needs one reconstruction; selection and fusion each use four. No equal-cost claim is made. Evidence: `PROTOCOL.md`, `evaluate_selection.py`.

## What actually ran

MEASURED execution inventory, verified by SHA-256 and ZIP CRC without image decoding:

| Scene | Required members | Verified members | Still missing |
|---|---:|---:|---:|
| 01 | 81 | 81 | 0 |
| 02 | 81 | 81 | 0 |
| 03 | 81 | 31 | 50 |
| 04 | 81 | 0 | 81 |

Evidence: `receipts/FINAL_EXECUTION_STATE.json`, which also lists every missing member and preserved acquisition receipt. No target RGB was requested. Downloaded depth PNGs remain uninterpreted.

The original local download completed scene01 and part of scene02, then failed with `[SSL] record layer failure (_ssl.c:2580)`. An explicitly recorded serial transport repair failed similarly. One subsequent remote transport attempt, using the same official archives, TLS verification and pinned identities, completed the remaining scene02 members and part of scene03. It then stopped on `RemoteDisconnected('Remote end closed connection without response')`. Scene04 was not attempted. No further automatic retries remain active. These transport changes were recorded before inference or scoring and did not change the scientific protocol. Evidence: `AMENDMENT_01.json`, `AMENDMENT_02.json`, `acquisition/*/receipt.json`, `remote_import/acquisition/*/receipt.json`.

MEASURED execution counts: candidate outputs 0, selections 0, sensor-depth decodes 0, new GPU jobs 0. No partial-scene score was substituted for the planned panel. Evidence: `receipts/FINAL_EXECUTION_STATE.json`.

## S141 status and duplication check

MEASURED at 2026-10-10T14:13:56Z on TACC gpu13: A training had completed 10,000 steps and its pre-existing evaluation chain was generating evaluation outputs; B's latest logged training step was 9,160. Only the old baseline score files existed. Final A/B comparison was not available. The existing jobs were neither restarted nor interrupted. GPU3/4 remained assigned to those tasks; other GPUs contained resident workloads. Evidence: `receipts/TACC_FINAL_STATUS.txt`, `receipts/TACC_140801_STATUS.json`, `receipts/TACC_INITIAL_STATE.json`.

## Validation and limits

MEASURED implementation checks: root repository unittest suite 114 passed; W2 stage tests 46 passed; acquisition helper boundary tests 8 passed. No root linter was configured. Independent selector and geometry-metric checkers were prepared and synthetically checked (10 and 8 checks respectively, reported by their agents); neither was run on real W2 outputs because those outputs do not exist. Tests establish implementation checks, not model effectiveness. Evidence: `logs/repo_tests.log`, `logs/stage_tests.log`, `receipts/HELPER_BOUNDARY_TESTS.json`, `independent/PREPARATION.json`.

## Continuation after data access recovers

Resume only the missing members listed in `receipts/FINAL_EXECUTION_STATE.json`, preserving archive identity and already verified files. Record the transport continuation before new acquisition; do not alter scene IDs, windows, thresholds or controls. Verify the entire fixed panel, then run `RUN_worker0.sh` and `RUN_worker1.sh` concurrently, followed by `RUN_SCORE.sh`. The latter seals candidates, computes and seals source-only decisions, and only then opens measured depth for scoring. Do not blindly rerun `RUN_COMMANDS.sh`: its original acquisition step correctly refuses to overwrite existing files.

After actual scores exist, run both saved independent checkers and apply the unchanged stop rules. Inspect the existing S141 outputs separately; do not launch duplicate training or evaluation. The raw partial data are retained in this isolated worktree and in the task-owned TACC acquisition directory. No work was written over the primary research checkout.

Changed in the isolated branch: new `work/W2_source_selection_20261010_codex/` stage; append-only continuity updates to `RESEARCH_MEMORY.md`, `RESEARCH_LOG.md`, and `research_events.jsonl`. User-facing evidence is exported separately. No commit or push was made. Keep `new_method_validated=false` and `novelty_authorization=NONE`.
