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

## Required order

Review 1 must finish first. Bind its immutable JSON descriptor into
`protocol.datasets.rgbd-scenes-v2.adapter_review_ref`, then recompute the canonical
protocol SHA. Any protocol approval written before that binding is stale by
construction and must be rejected.

## Review 2: final adapter-bound Gate0 protocol

Use v7 only as the pre-review base. Review the `protocol` object in the new
adapter-bound candidate emitted after Review 1. Do not approve the pre-adapter v7
SHA `ec7530ce949a80a944178515c6505d05d1bc425adc0574776f5e2ec80b088b9f`.
Confirm or reject the exposed-development scope, exact window, predeclared camera
commands, source/runtime/checkpoint identities, isolation receipt, fixed compute
budget, RGB-only metric claim boundary, and the prohibition on held-out, geometry,
method-comparison, or novelty claims. Approval must be an evidence-backed JSON
artifact with `verdict: PRE_RUN_APPROVED`, the exact `protocol_sha256`, a reviewer
identity different from the author, findings, and limitations.

## Current machine result

The Gate0 validator verified 217 non-review artifacts. It remains `BLOCKED`; the
only remaining categories are the two independent reviews above. Do not authorize
or launch the model merely because hashes match.

The post-review execution chain is available for optional inspection:
`seal_predictions_s103.py`, `prepare_formal_bundle_s103.py`, and
`run_s103_vmem_base.slurm`. Its synthetic/static regression is 11/11 PASS, but the
real candidate correctly refuses to create a formal bundle while the reviews are
missing. This software result must not influence the substantive review verdict.

The reviewer must use the final adapter-bound descendant of v7, not archived
v4/v5/v6. v7 includes both the corrected shared history/query intrinsics transform
and the official all-eight-camera common centering rule. Exact-boundary job
591500 passed on H800 with predictor SHA
`75af8cad1de25ea7e43ad90c6c7bd89de33d7aa86da50afe8735da612a11189f`.
Earlier contracts and jobs 589826/590696 are retained only as superseded evidence.
