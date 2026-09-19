# Independent Gate0 candidate-v2 evidence audit

Audit date: 2026-09-16, Asia/Shanghai. Auditor: `gate0_independent_audit`, a different agent from the contract author; this is team-internal independent review, not external replication.

**Verdict: REVISE. No formal Gate0 PASS is supported by candidate-v2.** The archive acquisition itself is real and independently rehashed. The main defects are a mismatch between the declared datasets and their camera contracts, an incompatible effective VMem configuration, an unenforced future-data boundary, and a circular pre-run gate. Correcting the circular gate can enable a properly scoped development baseline without inventing held-out validation.

The reviewed candidate SHA-256 is `ae19108f624e030bfcba791aef5012757915b56c2cddbf42ed5334212e9d1b1c`. Its top-level status remains BLOCKED, which is appropriate. Seven internal PASS labels are draft claims, not accepted findings. This audit changes no production contract or scheduler and launches no model, training, or scoring job.

## What was actually checked

- Read the current project principles, memory, recent append-only events, candidate-v2, its validator, future-path guard, source provenance, archived no-data GPU receipts, and TUM pairing implementation.
- Applied the methodology, measurement-validity, confounding, and evidence-strength sections of `/Users/rocket/.claude/skills/sci-scientific-critical-thinking/SKILL.md`. No unrelated schematic generation was needed for this code/data qualification audit.
- Retrieved the official [Microsoft 7-Scenes documentation](https://www.microsoft.com/en-us/research/project/rgb-d-dataset-7-scenes/) and checked its calibration limitation directly.
- Reconnected to SuperPOD using the authorized SSH identity and independently recomputed the Chess archive SHA-256. Read only the outer ZIP directory, already-declared split text, exit receipts, and file metadata. No nested sequence frame/depth/pose payload was opened or decoded by this auditor.
- Executed three small synthetic contract/guard checks. Their outputs demonstrate implementation limitations, not model performance or real-data leakage.

Evidence files: `INPUT_FILE_HASHES.json`, `REMOTE_ARCHIVE_READBACK.json`, `SYNTHETIC_GUARD_CHECKS.json`, and reproducible `audit_checks.py` in this directory.

## Accepted acquisition facts

The remote archive is 3,079,608,937 bytes and independently rehashes to `d00b5b8f904123ec136768ee0ebd8f72aebb5473630fb5d8ec352e70ae4859d0`, matching the acquisition evidence. The outer ZIP has ten entries: its directory, one preview image, six nested sequence ZIPs, and two split files. The train split is sequences 1/2/4/6; the test split is sequences 3/5. Both split hashes match the recorded values. Download, hash, and outer extraction receipts each contain exit code 0.

The directory does **not** itself provide a manifest of all RGB/depth/pose frame triples. The recorded `outer_zip_listing_sha256` is currently used as `manifest_sha256` in candidate-v2, but the exact serialized listing file and its canonicalization rule are absent from the cited local evidence. This audit independently verifies the outer entry content, not that specific listing serialization hash. A nested sequence ZIP is not an audited frame manifest. Do not use the ten outer entries as proof of frame completeness, pairing, validity, or frozen evaluation windows.

## Findings and minimum corrections

### 1. CRITICAL — 7-Scenes does not supply the calibrated, registered RGB-D contract being claimed

Microsoft documents 640×480 RGB-D recordings, millimetre depth with invalid value 65535, and camera-to-world poses. It also explicitly says the RGB and depth cameras were not calibrated; 585/585/320/240 are default **depth** intrinsics used by KinectFusion. Its released camera tracks are reconstructed with KinectFusion, not independent motion-capture measurements. [Official dataset description](https://www.microsoft.com/en-us/research/project/rgb-d-dataset-7-scenes/)

Candidate-v2's camera/depth/pose PASS fields instead contain TUM Freiburg3 intrinsics and a raw-depth divisor of 5000 with invalid value 0. Those values cannot be applied to Chess, whose raw-depth divisor is 1000 and invalid sentinel is 65535. Matching image dimensions does not prove RGB/depth registration or supply the missing RGB-depth extrinsics.

**Minimum correction:** bind a separate adapter/contract to each dataset and intended metric. Keep Chess as an acquired candidate or explicitly approximate depth-only diagnostic until its camera/registration limitations are resolved. Do not manufacture RGB calibration from the KinectFusion depth defaults. An acquired dataset need not be discarded because it cannot support this particular metric.

### 2. CRITICAL — The pre-run gate requires post-run outputs and therefore cannot be satisfied legitimately

The validator requires `prediction_output_hash_before_gt_open=true`, `post_run_manifest_recompute=true`, `metric_recompute=true`, and `output_seal_check=true` before formal eligibility can become PASS. The isolation protocol also explicitly says the pre-run gate stays blocked until a real prediction and readback exist. At the same time, the launcher refuses the prediction until Gate0 passes. This is a dependency cycle.

**Minimum correction:** use separate stages:

1. `PRE_RUN_READY`: the run purpose, effective configuration, declared inputs, executable data adapters, access policy, prediction-sealing implementation, scoring implementation, and required hashes are frozen and reviewed. Future **outcomes** are still unopened; no claim is made that predictions or metrics already exist.
2. `PREDICTION_SEALED`: after actual inference, record output hashes, runtime input-access evidence, seed/RNG state, job exit, and source/config identity.
3. `POST_RUN_ACCEPTED`: only after the scorer opens permitted outcome files, verifies the seal, records full denominators/missing cases, and independently recomputes the metrics.

Only stage 1 enables model execution; only stages 2 and 3 enable scientific result acceptance. Remove post-run booleans from the pre-run requirement rather than setting them true. This is a correction to orchestration, not a reduction in evidence standards.

### 3. CRITICAL — The future-path guard is a text filter, not an input boundary

The synthetic `unlabelled_future_path` fixture contains a test-sequence frame path under `seq-03` without the English word `future`; it passes with exit 0. Conversely, a harmless `future_data_visible:false` field fails with exit 2. The script neither resolves real paths/symlinks nor checks membership in an allowed-input manifest. It does not prevent code from constructing another path or reading a whole archive. No separate runtime mount/container/permission evidence accompanies its claim that future files are inaccessible.

**Minimum correction:** provide an explicit input allowlist keyed by dataset/sequence/frame/modality and its hash; resolve actual paths and reject any undeclared input. Stage only permitted inputs into the predictor's runtime filesystem (or use equivalent enforced isolation), without the full held-out archive mounted. Keep scorer-only files outside that runtime. Retain access traces and test a known denied path. A substring filter may remain a warning helper but cannot satisfy isolation.

The target camera trajectory needs an explicit role: if VMem is evaluated as camera-conditioned generation, the predeclared target camera is a shared conditioning input. Future RGB/depth remain outcomes. Blanket denial of every target pose would change the task; do not recover a needed target camera covertly from future GT.

### 4. MAJOR — The effective VMem config disagrees with the supposedly frozen budget

The cited configuration SHA `8d849588016935573a22ef6aaee567f71125ca4d3bdf18f51e3552a64be9fea3` independently matches `work/S20_environment/isolated_vmem_source/configs/inference/inference.yaml`. That actual file specifies **576×576**, four context plus four target frames (eight total), 50 inference steps, and seed 42. The draft budget instead says native 224×224, one output, and seed 20260916. The no-data model-load receipt likewise records seed 42. A CUT3R component resolution must not be presented as VMem's resolution.

**Minimum correction:** freeze and hash the actual merged runtime configuration, including all overrides. Specify which generated frames are scored and retain unscored outputs. Bind the exact resize/crop/depth-resampling and intrinsic-matrix transformation from source resolution to model and metric coordinates. Reserve the same stochastic input stream across paired conditions, not just an unverified equal seed. Treat runtime 1500 seconds as a timeout/resource bound unless its measured role is otherwise specified; equal caps alone do not prove equal computation.

### 5. MAJOR — The held-out label mixes different independence claims

Chess is a new acquisition relative to the exposed TUM/ICL development materials. If Chess sequences 1/2/4/6 become calibration/history inputs, sequences 3/5 remain **sequence-held-out within the same scene**, not a scene held out from calibration. Official train/test splits support their original relocalization evaluation; they do not automatically define the project's chronological future-prediction task. Candidate-v2 says train sequences are calibration/history; the isolation prose alternatively says TUM is calibration. These routes are not yet one frozen experiment.

**Minimum correction:** name the intended role precisely. For a scene-held-out claim, fit all method parameters on other scenes; permit only the frozen online-history policy on Chess. Define chronological history and future windows within each continuous sequence. For a sequence-held-out claim, allow Chess calibration but report it as such. One new scene cannot demonstrate broad cross-scene reliability or dynamic-object prediction.

### 6. MAJOR — Seven section PASS labels exceed the evidence

| Candidate section | Evidence-supported scope | What remains before this run can claim readiness |
|---|---|---|
| Camera | Published TUM constants; project raster convention named | Per-dataset binding, actual preprocessing/K mapping, projection convention exercised on allowed development inputs |
| Depth | TUM decoding rule documented | Dataset-specific adapter and invalid rules; history-side checks; future invalid counts belong to post-seal scoring |
| RGB-depth pairing | TUM deterministic greedy one-to-one rule and aggregate receipt agree: 2488 pairs, 97 RGB drops, 21 depth drops, no duplicate assigned depth | Save identity-level paired manifest and hash; this is not a 7-Scenes pairing audit |
| Pose | TUM field/unit/direction declarations | Exact timestamp match/interpolation rule, tolerance, tie/boundary/missing-pose policy, executable adapter; pose metadata alone is insufficient |
| Held-out identity | Real new archive and official sequence split | Exposure claim scope, corrected time provenance, frame/window manifest, calibration-role consistency, calibrated adapter |
| Fair budget | Proposed k=4 and 50-step policy | Concrete candidate IDs/windows, valid effective configuration, actual consumer and metric output definition |
| Checkpoints/code | Archived VMem/CUT3R hash receipts; actual base-config hash | Bind full source snapshot, current compatibility edits, actual effective config, tokenizer/CLIP/VAE identity and the already-declared substitute-VAE limitation into the run manifest |

The TUM pairing implementation is global greedy selection over sorted candidate edges, not a proved optimal bipartite assignment; describe it accurately. Its aggregate counts are accepted as pairing-only evidence. The script does not export the accepted frame-identity list, so counts alone cannot freeze the model's candidate pool.

### 7. MAJOR — Validator PASS proves declarations are consistent, not that evidence exists

In a temporary synthetic fixture only, the auditor filled missing strings with a nonexistent placeholder, set post-run booleans true, and declared all sections PASS. The production validator returned exit 0 and `formal_status=PASS` without a real verifier, prediction, or metric file. No real contract was altered and the fixture was deleted.

**Minimum correction:** preserve schema validation as a distinct result, require a referenced independent pre-run review artifact and effective manifest hash, and verify evidence-file existence/content hashes where applicable. Do not describe JSON structural validation as scientific clearance. This need not become an elaborate signature infrastructure: a reviewed manifest plus exact hash binding is sufficient for the next bounded run.

### 8. MAJOR — Handwritten creation times are wrong; actual evidence supports a different order

The acquisition protocol claims creation at 01:40 and candidate-v2 claims 01:48. Both are later than their real file birth times. The author independently acknowledged that these were manually written incorrect future times. Observed local file birth time and research-event creation put the acquisition protocol at **01:24:47**; remote download exit is **01:26:04**, archive hash receipt **01:26:59**, and outer extraction exit **01:27:35**. The archive evidence file was created at **01:29:00**, candidate-v2 at **01:30:37**. All are 2026-09-16 Asia/Shanghai.

**Minimum correction:** preserve the erroneous originals and add a dated correction citing file-stat and append-only-event evidence. File timestamps support this observed ordering but are not a tamper-proof proof of universal non-access. Replace `zero_exposure_before_freeze=true` with a precisely scoped and evidenced claim: no documented pre-protocol semantic frame/depth/pose inspection. Archive download and hashing necessarily handle raw archive bytes; they are distinct from opening decoded outcomes in prediction or analysis. Do not claim literally no bytes were read while also claiming a full archive SHA.

### 9. MINOR — Persistent execution evidence should preserve launch context

Remote download/hash/extraction exit files exist and all are zero. At this audit's live check no tmux server was running; that is compatible with a completed short-lived tmux session, and is not evidence it was never used. The cited acquisition evidence does not preserve the exact launcher/session identifier.

**Minimum correction:** keep the existing tool execution record or launcher command plus session name in the acquisition receipt. For long GPU jobs preserve the remote tmux/screen launcher, Slurm job ID, output log and terminal exit status. Do not require a completed session to remain alive merely for inspection.

## Fastest justified continuation

1. Correct the circular contract into pre-run readiness and post-run acceptance.
2. Freeze one **TUM development selector-free VMem baseline** with the actual 576-based effective configuration and known TUM adapter. Exposed development data is legitimate for debugging/baseline characterization when explicitly labelled. It cannot supply held-out method confirmation.
3. Execute the ready development baseline through persistent remote tmux/screen plus Slurm. Keep future scoring out until prediction is sealed; retain failures and all planned outputs.
4. In parallel, resolve a calibrated independent dataset/adapter and only then authorize a held-out formal comparison. Chess's uncalibrated RGB-D limitation is a data-design issue, not an environment failure. Do not repeatedly download models or rerun no-data model loading to substitute for these steps.

No innovation claim changes. This audit supplies no new VMem inference, video, geometry score, GRC/SOCF benefit, or cross-scene result.
