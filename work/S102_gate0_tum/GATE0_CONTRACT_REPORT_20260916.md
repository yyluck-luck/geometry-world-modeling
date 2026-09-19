# Gate0 contract v1 report (2026-09-16)

This artifact turns the current Gate0 decision into a machine-readable pre-run contract. It is a protocol gate, not a model experiment and not evidence that GRC/SOCF works.

## What is captured

- Camera convention: image dimensions, intrinsics, distortion, pixel-center convention, and transform direction.
- Depth semantics: raw type, invalid value, scale, optical-axis/radial interpretation, and the depth-to-metric equation.
- Deterministic RGB-D pairing: tolerance, tie rule, one-to-one enforcement, and complete drop/duplicate counts.
- Pose semantics: source, timestamp/frame identity, quaternion order, units, and transform direction.
- Future-answer isolation: history/calibration/query windows, selector-visible inputs, scorer-only inputs, and the requirement to hash predictions before opening future GT.
- Independent held-out identity: archive and manifest hashes plus zero pre-freeze exposure.
- Fair budget: candidate pool, `k`, context/output limits, sampling, seed/RNG, resolution, dtype, and runtime.
- Checkpoint and source identity: verified VMem/CUT3R hashes plus unresolved source/config binding.
- Independent readback: verifier identity, metric recomputation, and output seal.

## Current decision

`gate0_contract_v1.json` is intentionally `BLOCKED`. The TUM archive has useful qualification evidence (2,488 of 2,585 RGB rows paired within 20 ms), but its camera/depth/pose rules, future-GT split, and independent held-out identity are not frozen. The ICL-NUIM candidate has prior metadata exposure and remains development-only. Verified checkpoint hashes do not by themselves authorize a baseline.

Run:

```bash
python work/S102_gate0_tum/validate_gate0_contract.py
```

The validator reads only the contract JSON; it never opens RGB, depth, pose, prediction, or GT files. Exit code `2` means a readable but intentionally blocked contract; exit code `3` means malformed contract. A future signed revision must set every section to `PASS`, top-level `status` to `PASS`, and `formal_experiment_eligibility` to `PASS` before S103 may be submitted.

## Evidence inputs

- `remote_receipts_588524/RESULTS.json`
- `GATE0_CURRENT_DECISION_20260916.json`
- `IMPLEMENTATION_AND_DATA_CONTRACT_AUDIT_20260916.md`
- `../S103_h800_model_load_smoke/remote_receipts_588459/RECEIPT.json`
- `../S104_h800_cut3r_calibration/remote_receipts_586719/RECEIPT.json`
