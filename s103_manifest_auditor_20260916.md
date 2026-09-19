# S103 manifest audit (2026-09-16)

## Scope

This audit checks the S103 H800 VMem preflight and S101 source-transport records before any formal VMem forward. The audit follows the project evidence rule: metadata, model-load smoke, and component forward are not scientific baseline results.

## Findings

| Severity | Finding | Evidence | Minimal action |
|---|---|---|---|
| MAJOR (gate blocker) | The preflight does not bind a signed implementation/data contract for camera, depth, pose, pairing, future-GT visibility, and independent held-out identity. | `work/S102_gate0_tum/GATE0_CURRENT_DECISION_20260916.json` | Keep S103 blocked; add the contract fields to the signed pre-run manifest before submission. |
| MAJOR (gate blocker) | The TUM qualification output reports nearest timestamp matches but does not report duplicate-match and dropped-row counts, so one-to-one pairing is not independently established. | `work/S102_gate0_tum/run_tum_gate0_metadata.py`, `remote_receipts_588524/RESULTS.json` | Add duplicate/drop counters to the next qualification manifest; do not reinterpret current 96.25% rate. |
| MAJOR (reproducibility) | S103 preflight lists checkpoint hashes but omits source-bundle/config/script/environment hashes and a formal output/seal contract. | `work/S103_H800_VMEM_BASELINE_PREFLIGHT_20260915.json` | Use the metadata sidecar patch and require these fields in the signed run manifest. |
| MODERATE (record freshness) | `WEIGHT_TRANSFER_STATUS_20260915.json` retains its historical `IN_PROGRESS_PARTIAL` status and pending hashes even though later receipts show completed transfer/load. | `work/S101_env_bootstrap/WEIGHT_TRANSFER_STATUS_20260915.json`, `work/S103_h800_model_load_smoke/remote_receipts_588459/RECEIPT.json` | Preserve the historical file; use the dated current-status sidecar rather than rewriting history. |
| MODERATE (reproducibility) | Formal receipt does not yet declare deterministic-algorithm setting or capture RNG states. | `work/S103_h800_model_load_smoke/remote_receipts_588459/RECEIPT.json` | Record deterministic setting and RNG-state hashes in S103 formal receipt. |
| MINOR (clarity) | The preflight says `heldout_target_ids` are sealed but does not specify the scorer process and seal input list. | `work/S103_H800_VMEM_BASELINE_PREFLIGHT_20260915.json` | Add scorer-only access and seal-input fields; no data is opened by this audit. |

## Minimal patch applied

Added [`S103_H800_VMEM_BASELINE_PREFLIGHT_METADATA_PATCH_20260916.json`](../S103_H800_VMEM_BASELINE_PREFLIGHT_METADATA_PATCH_20260916.json). It is a sidecar so the original preflight and historical transfer record remain intact. The sidecar binds current artifact hashes, source bundle/config/script/environment metadata, and the formal output/seal contract. It explicitly leaves all scientific blockers unresolved.

## Checklist before formal S103

- [ ] Sign camera model, intrinsics, distortion, pixel center, and pose transform convention.
- [ ] Sign depth dtype, invalid value, scale, and metric-z equation.
- [ ] Recompute deterministic one-to-one RGB-D matching with duplicate/drop counters and tie rule.
- [ ] Freeze history/calibration/future query windows and scorer-only future GT access.
- [ ] Acquire and hash an independent held-out scene with no pre-freeze metadata exposure.
- [ ] Freeze candidate pool, context/output counts, steps, seed/RNG policy, resolution, dtype, checkpoints/config, and runtime budget.
- [ ] Generate signed `RUN_MANIFEST.json`; only then submit selector-free S103 VMem baseline.

## Decision

`BLOCKED_FORMAL_BASELINE_PENDING_CONTRACT_FREEZE` remains unchanged. No VMem forward or GRC/SOCF scoring was submitted by this audit.
