# S103 independent pre-run review request

This package is for a reviewer who is different from `codex-root-20260916`.
It is not a request to inspect any future RGB, depth, or pose payload.

## Review 1: dataset adapter

Review `work/S102_gate0_3dmatch/adapter_v1/rgbd_scenes_v2.py` at SHA-256
`8be9af8716bb5452963e06e67bcd31704611d13c75b5d7c96e5cdf1bfcdd8d24`.
Confirm or reject the declared RGB/depth units, invalid-depth rule, camera matrix,
resize/crop transformation, pose convention, frame identity binding, and path/role
allowlist. Acceptance must be an evidence-backed JSON artifact with
`status: ADAPTER_ACCEPTED`, the exact `adapter_sha256`, reviewer identity, findings,
and limitations.

## Review 2: frozen Gate0 protocol

Review the `protocol` object in
`work/S103_selector_free_baseline/window_scene13_w001_20260916/GATE0_CONTRACT_CANDIDATE_v5.json`.
Its canonical protocol SHA-256 is
`bfc3e843957ad6e3e0b26302d2ca47be1b67a9d93767e86acf18d4b2f7721df8`.
Confirm or reject the exposed-development scope, exact window, predeclared camera
commands, source/runtime/checkpoint identities, isolation receipt, fixed compute
budget, RGB-only metric claim boundary, and the prohibition on held-out, geometry,
method-comparison, or novelty claims. Approval must be an evidence-backed JSON
artifact with `verdict: PRE_RUN_APPROVED`, the exact `protocol_sha256`, a reviewer
identity different from the author, findings, and limitations.

## Current machine result

The Gate0 validator verified 216 non-review artifacts. It remains `BLOCKED`; the
only remaining categories are the two independent reviews above. Do not authorize
or launch the model merely because hashes match.

The post-review execution chain is available for optional inspection:
`seal_predictions_s103.py`, `prepare_formal_bundle_s103.py`, and
`run_s103_vmem_base.slurm`. Its synthetic/static regression is 11/11 PASS, but the
real candidate correctly refuses to create a formal bundle while the reviews are
missing. This software result must not influence the substantive review verdict.

The reviewer must use v5, not archived v4. v5 includes the corrected shared
history/query intrinsics transform and exact-boundary job 590696. Historical v4
and job 589826 are retained only as superseded evidence.
