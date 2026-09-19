# S103 implementation-only contract reconciliation (2026-09-16)

## Scope and decision

This report reconciles the current staged v2 validator with the available 3DMatch adapter, weight-integrity, and isolation evidence. It is an implementation gate only. It does not authorize SSH/Slurm, model inference, scoring, a held-out claim, or a method claim.

Current status: **BLOCKED**. A new `gwm-gate0-staged-v2` contract is required. The legacy `gate0_contract_candidate_v3.json` (SHA-256 `322ae57017f36a1fc309c481164a37b1817124cb27be746aad294842e5e749fa`) must remain historical evidence; it cannot be promoted by changing its status.

Validator reviewed: `work/S102_gate0_tum/validate_gate0_v2.py` (SHA-256 `dbae13a507088d8aca422ee9191f2c41f377d8b125c8c28ffe6b569336ae9d97`). It returns `PRE_RUN_READY` only for a complete implementation contract; it does not establish scientific validity.

## Fields still required for PRE_RUN_READY

### 1. Protocol identity and independent review

Required:

- `schema: "gwm-gate0-staged-v2"`
- `protocol.status: "FROZEN"`
- non-empty `run_id`, `author`, and `scope: "development_baseline"`
- `development_data_exposed: true` with the development-only claim boundary
- `review_ref: {path, sha256, bytes}`
- review JSON with `verdict: "PRE_RUN_APPROVED"`, a reviewer different from `protocol.author`, and `protocol_sha256 = SHA256(canonical(protocol))`

The review must bind the final protocol after all paths, frame windows, adapter fields, and boundary IDs are filled. A template or the blocked v3 contract is not a review.

### 2. Effective VMem configuration and code binding

Required:

- `effective_config_ref` to the exact runtime YAML/JSON and its byte count/SHA
- `expected_config` values for height, width, context frames, target frames, total frames, inference steps, and seed
- `source_manifest_ref` listing every code/config file used by the predictor, with individual `{path, sha256, bytes}` references
- `runtime_binding_ref` binding effective-config SHA, source-manifest SHA, checkpoint paths, predictor-wrapper SHA, and execution-boundary ID
- `predictor_wrapper_ref`, `scorer_ref`, and `verifier_ref`

The reusable effective configuration is 576x576, 4 context + 4 target, 50 steps, seed 42. Reuse only with a fresh manifest: `work/S103_selector_free_baseline/PRE_RUN_READY_MANIFEST_TEMPLATE_v1.json` (SHA-256 `6b10531ce18508a12be189cd607f67be287b1dd44e444dd239d8fcb418a4bc9d`). The source config `work/S102_gate0_3dmatch/adapter_v1/sources/vmem_inference.yaml` has SHA-256 `8d849588016935573a22ef6aaee567f71125ca4d3bdf18f51e3552a64be9fea3`.

The VAE choice must remain explicit as `original_verified` or `declared_substitute`; it must not be silently treated as the original VAE.

### 3. 3DMatch dataset adapter

Use separate dataset contracts:

- `dataset_id: rgbd-scenes-v2`
- `scene_13`: development/calibration only
- `scene_14`: independent-scene candidate, still not PRE_RUN_READY

Current qualification is only one previously exposed scene-13 frame:

- `work/S102_gate0_3dmatch/adapter_v1/QUALIFICATION_RESULT.json`
- SHA-256 `dc06e1d8afc3bd0c844c64df0ef204c3dc67794fb050d6d295112929fce64ccd`
- status `PASS_QUALIFICATION_ONLY`; it explicitly excludes full-scene windows and VMem inference.

The new contract still needs:

- adapter source and review refs; current adapter source `adapter_v1/rgbd_scenes_v2.py` SHA-256 `8be9af8716bb5452963e06e67bcd31704611d13c75b5d7c96e5cdf1bfcdd8d24`
- full frame-identity manifest for every development window, not only frame 000000
- scene-specific K, RGB/depth registration, half-pixel convention, resize/crop K transform, pose association, depth invalid rule `raw==0`, and `z_m=raw/1000`
- explicit pose role: RGB-D Mapping camera-to-world estimate, not mocap ground truth
- adapter review JSON with `status: "ADAPTER_ACCEPTED"` and the exact adapter SHA

### 4. Predictor/scorer manifests and window identity

For every window, provide:

- `dataset_id`, `scene_id`, `sequence_id`
- exact `history_ids` and `target_ids`
- `chronological: true`
- predictor records whose full identities exactly equal the declared history set
- scorer records whose full identities exactly equal the declared target set
- four history/context records and four target/output records for the current VMem configuration
- one command-camera record per target identity when `target_camera_policy: "predeclared_command"`

The command camera must be a separately staged, predeclared conditioning input with its own hash and provenance. It must not be relabelled future pose data. Scorer-only future RGB/depth/pose/GT paths remain outside the predictor staging root.

Required refs: `predictor_inputs_ref`, `scorer_inputs_ref`, `metric_definition_ref`; each must point to an existing file with matching bytes and SHA-256.

### 5. Enforced isolation

The protocol must provide `isolation.predictor_root`, `isolation.execution_boundary_id`, and `isolation.receipt_ref`. The receipt method must be `container_mount_whitelist`, `linux_namespace`, or `separate_user_acl`, and record `allowed_history_probe_passed`, `denied_outcome_probe_passed`, `full_archive_unavailable`, predictor/scorer/runtime/wrapper SHAs, the boundary ID, and exact staging root.

Reusable evidence:

- Apptainer/Pyxis capability: `work/S102_gate0_3dmatch/adapter_v1/container_probe_receipt/RECEIPT.json`, SHA-256 `498769c4a2646b158149f2d105d9d1c5679825d10e0c4d2757dd532186d06b49`
- login-node feasibility: `work/S103_selector_free_baseline/NAMESPACE_FEASIBILITY_20260916.json`, SHA-256 `f3f73800f644bb64ee9ce177bd5ef99417428eddae1062e12ba2cbebaae265a1`
- synthetic namespace probe: `work/S103_selector_free_baseline/isolation_v1/FIXTURE_PROBE_RECEIPT.json`, SHA-256 `62d6dd441c36b3a69c3ae59520d8f9bd767436697aeba0583583e6722ac59695`
- synthetic launch receipt: `work/S103_selector_free_baseline/isolation_v1/FIXTURE_LAUNCH_RECEIPT.json`, SHA-256 `adeec2aa1b4c84152b7820f95afb027722ff0e03457c64f492fa28cb3b5aee01`

These prove capability and a synthetic boundary only. They do not prove the exact compute-node predictor boundary. Before PRE_RUN_READY, run the same fixture through the intended compute-node wrapper and bind its returned boundary ID, wrapper SHA, runtime binding SHA, and input-manifest SHAs. The recorded remote wrapper SHA (`80522a400ad01f71f5745e31b4efce918ef3e273ec3d39679a7ad056828e6849`) must be reconciled with the local wrapper bytes before binding.

### 6. Checkpoint integrity

Reusable integrity evidence:

- `work/S101_env_bootstrap/WEIGHT_TRANSFER_STATUS_20260915.json`, SHA-256 `061cdb850c68dc026cffd3861026adced0d0b0a539f33987adeb784184e44aa9`
- Metadata-only binding patch: `work/S103_H800_VMEM_BASELINE_PREFLIGHT_METADATA_PATCH_20260916.json`, SHA-256 `3c92edeb7ca64d402b16f76a41956ca2c6858861f5d337c0f5a61266c0ccd84a`; it preserves the formal baseline as BLOCKED.
- VMem SHA `675dc486a02ea06ecf8b6ab0cf4ef88c92298751b2daacf9f65c59871fcb7fe4`
- CUT3R SHA `45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103`
- OpenCLIP SHA `0084e75319a50ad85ef45377bad5bc38f2f58824459eb690048d51c9f8863be5`
- VAE SHA `a1d993488569e928462932c8c38a0760b874d166399b14414135bd9c42df5815`

The H800 model-load receipt `work/S103_h800_model_load_smoke/remote_receipts_588611/RECEIPT.json` (SHA-256 `06496c106824ad591bd6a19637bc0e7cd61b3313bd576a50033eb9f289a7bbfa`) proves load-only success with no data, forward, or GT access. It does not replace a full source/config/runtime binding.

The contract must use current remote filenames and exact paths, bind all four weight descriptors to runtime bindings, and state the substitute-VAE limitation explicitly.

## Acceptance and stop criteria

### Accept PRE_RUN_READY only if

1. v2 validator SHA is recorded in the independent review and dispatch manifest.
2. Every artifact ref exists with matching bytes and SHA on the execution filesystem.
3. Review binds the canonical frozen protocol and is by a different reviewer.
4. 3DMatch adapter fields and full window manifests agree exactly with predictor/scorer records.
5. Effective VMem config and all checkpoint/source/wrapper/runtime hashes agree.
6. The command-camera role is predeclared and separately staged; future outcome files are not predictor inputs.
7. The compute-node isolation receipt proves allowed-history access and denied outcome/archive/symlink access for the exact boundary and manifests.
8. Validator returns `PRE_RUN_READY`, `pre_run_ready: true`, and no errors.

### Stop and retain BLOCKED if

- only frame-0 qualification is available;
- scene-14 adapter/window evidence is incomplete;
- any hash or runtime path is stale or ambiguous;
- wrapper SHA differs between local and remote receipts;
- isolation test is login-only or synthetic-only;
- command-camera provenance is mixed with future pose outcomes;
- manifest uses placeholders, legacy v1 schema, or an unreviewed post-run claim.

A PRE_RUN_READY result permits only the declared selector-free development baseline. It does not validate held-out performance, GRC/SOCF benefit, geometry quality, novelty, or paper claims.
