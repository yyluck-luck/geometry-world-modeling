# S45B C1 numeric requested-camera guard protocol

Status: `SOURCE_ONLY_UNBOUND_NOT_EXECUTABLE`.

This stage closes only S42 baseline preregistration section 5, guard 3, for row
`C1`.  S45 verifies that saved quantities propagate through the two-batch cache,
but it deliberately does not compute the requested camera trajectory.  S45B is
therefore a separate numeric precondition for later C1 scoring.

No real C1 tensor body, pixel, image, score, or quality result was opened while
preparing this source.  `execution_01` must remain an absent filesystem entry
until all source and post-result binding reviews below exist.  The unbound JSON
template is descriptive only and can never authorize execution.

## 1. Frozen scientific question

The guard asks whether the archived **requested input condition** follows the
predeclared out-and-return path.  It does not ask whether the rendered pixels
visually obey that request.

The only authoritative fields are selected from the full archive event chain:

- `batch_input`, occurrence 0: `target_c2ws[:4]`, `target_Ks[:4]` for IDs 1-4;
- `batch_input`, occurrence 1: `target_c2ws[:4]`, `target_Ks[:4]` for IDs 5-8;
- `cache_commit`, occurrence 0: `cache.c2ws/Ks[0:5]`;
- `cache_commit`, occurrence 1: `cache.c2ws/Ks[0:9]`.

The first batch's padding positions after the first four targets receive no ID
and are never evaluated.  `condition_input`, `condition_output`, sampler fields,
PNG files, PIL bodies, and every pixel tensor are outside this guard.

The frozen ID-to-yaw sequence in degrees is:

`[0, 1.25, 2.5, 3.75, 5, 3.75, 2.5, 1.25, 0]`.

For yaw `a` in radians, the exact left-positive Y-axis rotation is

```text
R_y(a) = [[ cos(a), 0,  sin(a)],
          [      0, 1,       0],
          [-sin(a), 0,  cos(a)]]
```

Let `C0` be ID0's archived c2w from `cache_commit` occurrence 0, slot 0.
For every ID, the expected pose is formed exactly as follows:

```text
expected[:3,:3] = R_y(a) @ C0[:3,:3]
expected[:3, 3] = C0[:3, 3]
expected[3, :]  = [0, 0, 0, 1]
```

This is left multiplication.  Neither the sign pattern nor multiplication side
may be inferred again from an observed C1 tensor.  They are copied from and
independently compared with the reviewed B0 implementation:

- `work/S42_baseline_failure_preregistration/score_b0_blind.py`
  SHA-256 `f36be25001f5138bd985ca186d49c6d44e66b5b9c599b8c0dfc6e8691a4719de`;
- exact UTF-8 source segment of `max_abs` (complete lines 806-808) SHA-256
  `5b19516bcaa6d650b7259d4e806266ab40762a358989190f2d3327fbaceb3fd4`;
- exact UTF-8 source segment of `verify_requested_camera_conditions` (complete
  lines 811-864) SHA-256
  `7dfa29e4bdaca569cf485b8c575f1d48f5dbcabb61011f6ab1998fea79b9a8e3`;
- primary B0 source review SHA-256
  `befb1af9c498a1423320cbd59011c56bdd4218ac56b4bb63667f4696b31184b0`;
- adversarial B0 source review SHA-256
  `a2874380d0cd62c68a1c9e5749d55bc6af37d47efde5726315db80c8d3b0abeb`.

The function-level identities deliberately hash exact source bytes rather than
`ast.dump`: CPython 3.12 and 3.13 serialize parts of the AST differently.  The
whole-file SHA and complete-line function segments jointly keep the check exact
while producing the same identities in both frozen local interpreters.

All pose, K, target-to-cache, and closure errors use the maximum absolute
elementwise difference after conversion to binary64.  Every operand must be
finite.  The frozen acceptance comparison is inclusive: `max_abs <= 1e-6`.

The following must all pass:

1. occurrence 0 and occurrence 1 cache lengths are exactly 5 and 9;
2. occurrence 1 slots 0-4 equal occurrence 0 slots 0-4 for c2w and K;
3. each batch's first four target c2w/K matrices equal its assigned cache slots
   1-4 or 5-8;
4. ID0's homogeneous row equals `[0,0,0,1]`;
5. every ID0-ID8 c2w equals its planned-yaw matrix and every K equals ID0 K;
6. ID8 and ID0 c2w/K separately close within `1e-6`.

Any numeric failure produces `NO_VALID_REVISIT_REQUESTED_CAMERA_CONDITION_FAILED`.
It cannot be converted into a high or low C1 score.

## 2. Minimal body-read scope and provenance

The future runner reads the complete archive manifest and event-chain metadata,
because those files establish capture occurrence and hash-chain closure.  It may
open tensor bodies only for the c2w/K descriptors selected by the four captures
above.  It must never open a PNG, PIL body, `pil_frames[*].pixels`, generated
image body, or any other tensor body.

Every JSON source, receipt, manifest, and the event chain is hashed and parsed
from one `O_NOFOLLOW` file-descriptor snapshot.  The same snapshot supplies both
the verified SHA and parsed bytes; no hash-then-reopen path is permitted.

The reader preserves raw metadata provenance with an internal
`TensorDescriptor` type that can be created only from a raw `kind=tensor` node.
A descriptor-shaped ordinary dictionary is not accepted.  Before opening a
body, the complete descriptor must equal the entry in
`archive/manifest.json:tensor_descriptors`; its body and sidecar identities must
match `manifest.files`; the path must be canonical, regular, non-symlinked, and
under `archive/tensors`.  The reader then snapshots the small body through one
open file descriptor, checks the body and descriptor hashes, rechecks the same
descriptor at close, and supports only finite float32/float64 matrices of the
fixed camera/K shapes.  The fixed shape and byte limits reject pixel tensors
before any body open.

The implementation uses only the Python standard library.  It decodes the small
float bodies with `struct`, performs the matrix calculation with explicit loops,
and imports no NumPy, Torch, PIL, OpenCV, renderer, model, or generation code.

## 3. Exact upstream identity gate

The C1 generation manifest path is fixed at
`work/S44_c1_confirmation_generation/review_attachment_01/manifest.json`,
SHA-256
`1e86e8279c608995a03d6675a8636c354d6d4d046b7c8faea9611d6e6a9fd93b`.

Before any tensor body can be opened, a future frozen binding must identify and
the runner must hash and cross-check all of the following:

1. the fixed C1 generation manifest;
2. the clean terminal external and worker generation receipts;
3. S45 `terminal_binding_01.json`;
4. S45 supervisor receipt, worker receipt, and report;
5. S45 independent result review at
   `work/S45_c1_result_readback/supervision_01/independent_result_review.json`;
6. the complete full-archive manifest and `archive/events.jsonl`.

The S45 result review must have schema
`s45-c1-readback-result-review-v1`, status
`PASS_S45_C1_READBACK_RESULT_REVIEW`, and verdict
`PASS_SAVED_OUTPUT_IDENTITIES_AND_CACHE_CONSUMPTION_ONLY`.  Its exact supervisor,
worker, and report identities must equal the binding.  It must explicitly retain
`row_validity_assertions.requested_pose_K_guard_pass=false`; no field in
`report_checks` is accepted as a substitute for this numeric guard.

During source preparation the independent reviewer sealed that review at SHA-256
`2b5e4bc3dcf28f60b320ae4d3af2b4949b60a526cacc62b2deacd87ac6ddad4c`.
This preparation verified that file identity and only its named schema, status,
receipt/report binding, and missing-pose-guard fields; it did not inspect
`report_checks`, open an array, or observe a scientific value.  The runner now
requires that exact review SHA.  The remaining terminal/readback identities are still unbound, so
`C1_CAMERA_GUARD_BINDING_TEMPLATE.json` retains `null` for them, has status
`UNBOUND_TEMPLATE_NOT_EXECUTABLE`, and is rejected by the runner.

## 4. Reviews required before the single formal attempt

The final `camera_guard.py`, this protocol, `synthetic_selftest.py`, the binding
template, the S42 baseline protocol, and the exact B0 reference source plus both
B0 source reviews require two different-author source reviews:

- schema `s45b-c1-numeric-camera-guard-source-review-v1`;
- kinds `primary` and `adversarial`;
- status `PASS_S45B_C1_NUMERIC_CAMERA_GUARD_SOURCE_REVIEW`;
- verdict `PASS_SOURCE_NOT_EXECUTED`;
- `executed=false`, `c1_tensor_bodies_read=0`, `pixels_decoded=0`,
  `images_viewed=0`, and empty `blocking_findings`.

After the S45 result review exists, a separate role creates
`C1_CAMERA_GUARD_BINDING.json` from actual hashes and a different role creates
`BINDING_REVIEW.json`:

- binding schema `s45b-c1-numeric-camera-guard-binding-v1`, status
  `FROZEN_C1_NUMERIC_CAMERA_GUARD_INPUT_BINDING`, `placeholder_hashes=0`;
- review schema `s45b-c1-numeric-camera-guard-binding-review-v1`, status
  `PASS_S45B_C1_NUMERIC_CAMERA_GUARD_BINDING_REVIEW`, verdict
  `PASS_BINDING_ONLY_NO_TENSOR_BODIES`;
- the binding review must bind the exact runner, protocol, both source reviews,
  binding SHA, and all upstream identities while recording zero tensor-body and
  pixel access.

The source author, two source reviewers, binding author, and binding reviewer
must satisfy the role-separation checks in the runner.  No review or template by
itself grants execution authority.

## 5. Single-use execution and retained failure

The only formal path is this directory's `execution_01`; it must be completely
absent, including as a broken symlink.  The runner accepts no arbitrary output
path and no alternative archive path.  An advisory exclusive lease on the
source-directory file descriptor serializes cooperating runners, but it is not
the permanent scientific attempt lease.

The runner first completes a **non-consuming preflight**: canonical output,
source identities, two source reviews, binding and binding review, all upstream
receipts, the S45 result review, archive manifest, complete event-chain parsing,
and a second identity scan.  A validation error during this phase creates
neither `.c1_numeric_camera_guard.lock` nor `execution_01`; correcting a command
or incomplete review therefore does not burn the sole scientific attempt.

Only after that preflight passes does the runner prepare a fully written,
fsynced JSON failure receipt at the single fixed staging name
`.c1_numeric_camera_guard.lock.staging`.  It atomically hard-links that inode to
`.c1_numeric_camera_guard.lock`, then removes the staging link.  The link is the
commit point.  Before it, no attempt is consumed; after it, the permanent lock
already contains the structured status
`FAIL_CLOSED_ATTEMPT_COMMITTED_NO_VALID_TERMINAL_RECEIPT`, start time, supplied
hashes, zero-body counters, and the rule that absence of a valid independently
reviewed terminal receipt is a failure.  A crash can therefore never leave an
authoritatively empty consumed lock.  The staging name is fixed, so failure
cannot switch names to create a second attempt.

After commit, the runner creates `execution_01` once and catches every ordinary
post-commit failure into its create-new `receipt.json`.  It records the exact
failed phase and truthful opened/read/close-verified body counts.  The permanent
lock FD, its pathname, device/inode/mode, `st_nlink==1`, byte length, and JSON
hash are revalidated immediately after commit, before output creation, after
output creation and post-commit identity checks, before tensor reads, after
tensor close, before and after the report write, before the terminal receipt
write, and at the final close boundary.  The source and output directory inode
leases are checked at the corresponding boundaries.  A pathname unlink or
replacement is terminal failure; a detected mismatch at final close creates
`lock_close_failure.json`, whose presence invalidates any earlier receipt PASS.
The directory-wide advisory lease prevents a second cooperating runner from
entering while these checks and final close are in progress.

A numerically successful `report.json` remains explicitly
`C1_REQUESTED_CAMERA_INPUT_CONDITION_RESULT_PENDING_TERMINAL_RECEIPT`; its
`numeric_verdict` records the narrow result.  Only the final `receipt.json` may
carry `PASS_C1_REQUESTED_CAMERA_INPUT_CONDITION_GUARD_ONLY`, after tensor-close,
source/upstream revalidation, and report hashing.  Thus interruption or a late
verification failure cannot leave a standalone PASS report.  The receipt keeps
separate counts for bodies opened/read and bodies whose close verification
succeeded, including on failure.  A receipt PASS is usable only when the atomic
lock receipt is unchanged, `lock_close_failure.json` is absent, and an
independent result review accepts the complete canonical bundle.

The strongest success status is
`PASS_C1_REQUESTED_CAMERA_INPUT_CONDITION_GUARD_ONLY`.  It means only that the
archived requested c2w/K input path numerically closed.  It does not establish a
pixel score, image quality, rendered-pixel camera obedience, model correctness,
method gain, cohort completion, causal attribution, or novelty.  A later,
independent result review must inspect the S45B receipt before C1 scoring may use
this precondition.

## 6. Preparation-time synthetic tests

Synthetic tests may use in-memory numeric matrices, source/AST hashes, and an
isolated temporary directory that is outside every formal path.  They must cover
the positive 0→5°→0° path, the exact B0 sign/multiplication convention,
target-to-cache mismatch, wrong rotation sign, K drift, closure failure,
nonfinite values, and the inclusive `1e-6` boundary.  They must also prove that a
preflight rejection leaves no permanent lease, lease commit atomically exposes
a parseable fail-closed receipt, a second commit is rejected, and unlink/recreate
of the lock pathname is detected against the held inode.  They may not open the
C1 manifest, terminal receipts, archive, tensor files, result review, images, or
any formal attempt path.
