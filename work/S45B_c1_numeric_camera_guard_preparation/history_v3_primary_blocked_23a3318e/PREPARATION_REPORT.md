# S45B C1 numeric requested-camera guard — source preparation report

Completed UTC: `2026-09-08T04:02:29Z`  
Author role: `/root/c1_blind_score_builder`  
Status: `SOURCE_ONLY_UNBOUND_NOT_EXECUTABLE`

## What this candidate is for

S45 proved a narrow saved-output identity and cache-consumption chain, but its
independent result review explicitly left
`row_validity_assertions.requested_pose_K_guard_pass=false`.  S45B prepares the
separate numeric guard required by S42 section 5(3).  It can eventually decide
only whether the archived **requested c2w/K input condition** follows the frozen
out-and-return trajectory.  It cannot decide whether generated pixels obey the
camera, whether images look good, whether C1 beats B0, or whether a method is
novel.

The source binds the exact S45 independent result review:

`work/S45_c1_result_readback/supervision_01/independent_result_review.json`  
SHA-256 `2b5e4bc3dcf28f60b320ae4d3af2b4949b60a526cacc62b2deacd87ac6ddad4c`.

That review's permitted meaning remains
`PASS_SAVED_OUTPUT_IDENTITIES_AND_CACHE_CONSUMPTION_ONLY`; it is never treated
as the missing numeric pose/K PASS.

## Frozen numeric decision

- Row: `C1`; IDs: `0` through `8`.
- Planned yaw in degrees:
  `[0, 1.25, 2.5, 3.75, 5, 3.75, 2.5, 1.25, 0]`.
- Rotation convention: left multiply ID0's c2w rotation by
  `[[cos,0,sin],[0,1,0],[-sin,0,cos]]`; retain ID0 translation and set the
  homogeneous row to `[0,0,0,1]`.
- Numeric rule: finite binary64 maximum absolute elementwise error
  `<= 1e-6`.
- `batch_input` occurrence 0 first four targets map to cache IDs 1-4;
  occurrence 1 first four targets map to IDs 5-8.  First-batch padding has no ID.
- Cache history must be exactly 5 then 9; the second cache's slots 0-4 must
  preserve the first cache's slots 0-4; ID8 c2w and K must close to ID0.
- The source never compares transformed condition/sampler camera tensors with
  the requested plan.

## Final source candidate identities

| File | SHA-256 |
|---|---|
| `camera_guard.py` | `23a3318e5cfb5b8c44f14a1bc2d3e4f72222ac78213eac2d9aedf35c1575f178` |
| `PROTOCOL.md` | `5055ff532a6a91d6c46e517835b5921d90dec339867c66d95721db6b333c7712` |
| `C1_CAMERA_GUARD_BINDING_TEMPLATE.json` | `1808f64275885ef4cd30f9119fb86f0a183dce150ae97bd334a447de46faa7c1` |
| `synthetic_selftest.py` | `02f881c7d3bfb3c50728e6c0128ed1f282f4a74f437abd3252d78a1ff7e4aae0` |

The template has status `UNBOUND_TEMPLATE_NOT_EXECUTABLE` and 14 deliberate
null hashes: six final source/review identities and eight terminal/readback/
archive identities.  The generation manifest and S45 result-review hashes are
already exact constants, but they do not make the template executable.

## Reader and publication safeguards

The future formal reader is standard-library only.  Every JSON or event-chain
file is hashed and parsed from one `O_NOFOLLOW` file-descriptor snapshot.  It
selects only the raw `kind=tensor` descriptors for `target_c2ws`, `target_Ks`,
`cache.c2ws`, and `cache.Ks`; rejects pixel-shaped tensors before opening a
body; and allows only fixed camera/K shapes, finite float32/float64 values, and
at most 4096 bytes per body.  Tensor bodies and sidecars are rechecked through
held file descriptors before sealing.

The formal lock, source directory, and output directory use held inode leases.
The lock and every artifact use create-new semantics.  A successful numeric
report is published only after tensor-close and source/upstream revalidation,
and its status remains
`C1_REQUESTED_CAMERA_INPUT_CONDITION_RESULT_PENDING_TERMINAL_RECEIPT`.  Only the
subsequently written receipt can carry
`PASS_C1_REQUESTED_CAMERA_INPUT_CONDITION_GUARD_ONLY`.  Failure receipts keep
separate actual body-open, byte-read, and successfully close-verified counts.

## Correction history retained

The first candidate was withdrawn rather than silently overwritten.

- `SOURCE_REVIEW_ADVERSARIAL_BLOCKED.json`, SHA-256
  `04f8500d21bd92fa05ae843965c60797e29c9d042ce96197c3ab9f9500143cdd`,
  preserves four blockers: early PASS publication, hash-to-parse TOCTOU,
  unstable lock/output paths, and possible underreporting after close failure.
- `ROOT_CROSS_VERSION_CORRECTION_HISTORY.json`, SHA-256
  `2008c714c353d26d0d157a43ad867828502bcaf22e05c21902d41ee896047cbc`,
  preserves the root check showing that `ast.dump` identities differed between
  Python 3.13.0 and 3.12.14.  The revision binds the whole B0 file plus exact
  UTF-8 function-source segments, which have identical hashes in both versions.

These files are failure/correction evidence.  Neither is a PASS source review.

## Static and synthetic verification

All four runs used isolated Python (`-I -B -S`) and created no bytecode or
project output:

| Interpreter | Built-in test | Independent test |
|---|---|---|
| system CPython 3.13.0 | `PASS_SYNTHETIC_ONLY` | `PASS_STATIC_AND_SYNTHETIC_ONLY` |
| `.venv-cut3r` CPython 3.12.14 | `PASS_SYNTHETIC_ONLY` | `PASS_STATIC_AND_SYNTHETIC_ONLY` |

The tests cover AST compilation; exact protocol/template/self-test binding;
cross-version B0 function source identities; independent left-multiply sign
calculation; the positive trajectory; target/cache mismatch; wrong yaw sign;
K drift; ID8 closure failure; nonfinite values; inclusive `1e-6`; strictly
over-tolerance rejection; list/tuple and raw-tensor provenance; selective
non-traversal of a synthetic PIL/pixel subtree; and pixel-shape rejection before
body open.

## Preparation access ledger and absent formal paths

- real C1 tensor bodies read: `0`;
- real C1 scientific arrays mapped or numerically inspected: `0`;
- pixel/image bodies opened or decoded: `0`;
- images viewed: `0`;
- model, renderer, generation, readback, or formal guard runs: `0`;
- formal attempt paths created: `0`.

The preparation inspected only source/protocol material, exact metadata
identities, and the named non-scientific gate fields of the S45 result review.
It did not inspect `report_checks` or any scientific result values.

At report completion all of these entries were absent:

- `execution_01`;
- `.c1_numeric_camera_guard.lock`;
- `C1_CAMERA_GUARD_BINDING.json`;
- `SOURCE_REVIEW_PRIMARY.json`;
- `SOURCE_REVIEW_ADVERSARIAL.json`;
- `BINDING_REVIEW.json`.

## Gates still required

1. A primary source reviewer and a different adversarial source reviewer must
   review this exact four-file source set and issue the two frozen review
   schemas with zero C1 body/pixel/formal access.
2. A fourth role must copy the template into
   `C1_CAMERA_GUARD_BINDING.json`, fill all 14 exact hashes, set placeholder
   count to zero, and change to the executable binding schema/status without
   changing any mathematics or source.
3. A fifth role must independently review that exact binding and all upstream
   identities, again with zero tensor-body or pixel access.
4. Only then may the single formal C1 numeric camera guard run.  Its terminal
   receipt still requires an independent result review before any C1 scorer can
   use the pose/K precondition.

Until those gates complete, this directory contains a reviewed-preparation
candidate only.  No C1 numeric pose/K result has been produced.
