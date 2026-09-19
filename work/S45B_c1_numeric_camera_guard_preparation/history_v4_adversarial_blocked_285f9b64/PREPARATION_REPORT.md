# S45B C1 numeric requested-camera guard — revised source preparation

Completed UTC: `2026-09-08T04:49:21Z`  
Author role: `/root/c1_blind_score_builder`  
Status: `SOURCE_ONLY_UNBOUND_PENDING_FRESH_DUAL_REVIEW`

## Purpose and exact boundary

S45 proved saved-output identity propagation and cache consumption, but its
independent result review deliberately left
`row_validity_assertions.requested_pose_K_guard_pass=false`. This S45B
candidate prepares the separate numeric check required by S42 section 5(3).
It may eventually determine whether the archived **requested c2w/K input
conditions** match the frozen out-and-return path.

It cannot determine whether rendered pixels obey those inputs, whether the
images look good, whether C1 beats B0, whether a natural failure exists, or
whether any method, causal mechanism, novelty claim, or publication claim is
supported. It performs no causal intervention. Any later total-effect study
must follow project principles v1.8: freeze only pre-intervention exogenous
controls and non-target initial state, then recompute every descendant of the
target memory source.

The source binds the exact S45 independent result review:

`work/S45_c1_result_readback/supervision_01/independent_result_review.json`  
SHA-256 `2b5e4bc3dcf28f60b320ae4d3af2b4949b60a526cacc62b2deacd87ac6ddad4c`.

That review still means only
`PASS_SAVED_OUTPUT_IDENTITIES_AND_CACHE_CONSUMPTION_ONLY`; this candidate never
uses identity propagation as a substitute for the missing numeric pose/K pass.

## Frozen numeric decision

- Row is exactly `C1`; IDs are exactly `ID0` through `ID8`.
- Planned yaw in degrees is
  `[0, 1.25, 2.5, 3.75, 5, 3.75, 2.5, 1.25, 0]`.
- The exact reviewed B0 convention is used: left-multiply ID0's 3x3 c2w
  rotation by `[[cos,0,sin],[0,1,0],[-sin,0,cos]]`, preserve the ID0
  translation, and require homogeneous row `[0,0,0,1]`.
- Every required comparison uses finite binary64 arithmetic and inclusive
  maximum absolute elementwise error `<= 1e-6`.
- `batch_input` occurrence 0 has exactly four requested targets mapped to cache
  slots `1:5`; occurrence 1 has exactly four targets mapped to slots `5:9`.
  The first-batch padding request is not assigned a new ID.
- The two `cache_commit` occurrences must contain exactly 5 and 9 camera/K
  entries. The second commit's slots `0:5` must preserve the first commit's
  slots `0:5`. ID8 c2w and K must close to ID0 within the same tolerance.
- Only raw archived requested-camera descriptors are eligible. Transformed
  condition/sampler camera tensors are outside this guard.

## Revised frozen source identities

| File | SHA-256 |
|---|---|
| `camera_guard.py` | `285f9b64f6ad53f14c21f725ff1884b632ef7766d63bf6e43af780b716160bb4` |
| `PROTOCOL.md` | `514fb18d5b2446ac50393fbe6c5fda34dd7b771356c037ff789e20710f49abcb` |
| `C1_CAMERA_GUARD_BINDING_TEMPLATE.json` | `a2d8aa4e686523db15044f28c1d7f39e1ff50f73f4485b303bd7b31247b2dc1a` |
| `synthetic_selftest.py` | `2d3674998103073fc3e884b3432f7d385bf432d4bfc7b8d51c4477ebaefc81aa` |

The binding template remains `UNBOUND_TEMPLATE_NOT_EXECUTABLE`. It contains 14
deliberate null hashes: six future source/review identities and eight exact
terminal/readback/archive identities. Null is never a wildcard. The exact
generation-manifest and S45 result-review constants do not make the template
executable.

The runner also binds the complete reviewed B0 scorer file SHA-256
`f36be25001f5138bd985ca186d49c6d44e66b5b9c599b8c0dfc6e8691a4719de`
and version-independent exact source-segment hashes
`5b19516bcaa6d650b7259d4e806266ab40762a358989190f2d3327fbaceb3fd4`
for `max_abs` and
`7dfa29e4bdaca569cf485b8c575f1d48f5dbcabb61011f6ab1998fea79b9a8e3`
for `verify_requested_camera_conditions`.

## Primary-review blockers and their correction

The former exact source set remains withdrawn after primary blocked-review
SHA-256
`05cb17b6974c404568a1b45ba65422ea4ca15ce593b18682527a4e327a258d3b`.
It was not overwritten: its seven files are preserved under
`history_v3_primary_blocked_23a3318e/`, with manifest SHA-256
`9f5d5bc9c23e332c22fa1ba26771e22ec9a6cb8bad9c1e2b36080d43e7d9c5f6`.

The revision fixes both blockers:

1. Canonical output, static source, two source reviews, binding, binding review,
   upstream identities, event selection, and start/end identity checks now run
   as a **non-consuming preflight**. During that phase the permanent lock,
   fixed staging path, and `execution_01` must remain absent. A command or
   metadata failure before commit therefore does not burn the sole scientific
   attempt.
2. After preflight, a full JSON default failure record is written and fsynced
   through a create-only, no-follow staging FD. The runner hard-links that inode
   to the permanent lock path; this atomic link is the attempt commit point.
   After commit, even interruption before output creation leaves a parseable
   fail-closed record with `attempt_consumed=true`, zero initial body/pixel
   counts, supplied identities, and no retry authorization.
3. The held permanent lock FD is compared with the no-follow pathname at every
   trust boundary. The checks cover regular-file type, device/inode identity,
   `st_nlink==1`, exact byte length, exact held-FD SHA-256 and EOF, plus the held
   parent-directory identity. The runner checks at commit, before output,
   before camera bodies, after tensor close, before and after report write, at
   terminal receipt write, and after terminal receipt before close.
4. The source directory is held under a transient advisory exclusive lock for
   the entire preflight and committed attempt. A synthetic unlink/recreate of
   the lock pathname is rejected against the still-held original inode. The
   fixed `execution_01` directory is also a permanent second attempt sentinel
   for cooperating invocations.
5. A failure detected before terminal receipt forces a failure receipt. A lock
   mismatch detected after receipt publication creates the fixed
   `lock_close_failure.json`; its presence invalidates any earlier PASS field.
   An independent result reviewer must check both the lock record and absence
   of this failure marker.

The detailed correction record is
`PRIMARY_LOCK_LIFECYCLE_CORRECTION_HISTORY.json`, SHA-256
`a5c58966c6713c6011257af4550bd29f53df60c74ec1e628404eafadcd9fe451`.

## Reader and publication safeguards retained

The future formal reader uses only the Python standard library. JSON metadata
and event-chain records are hashed and parsed from the same held
`O_NOFOLLOW` file-descriptor snapshot. It selects only `kind=tensor`
descriptors for `target_c2ws`, `target_Ks`, `cache.c2ws`, and `cache.Ks` from
the two required `batch_input` and two required `cache_commit` occurrences.
It rejects pixel-shaped tensors before any body open, permits only fixed
camera/K shapes and finite float32/float64 values, and caps each eligible body
at 4096 bytes.

Every opened camera body and sidecar is checked against the archive registry
and manifest, read and rehashed through one held FD, and rechecked at close.
Separate counters record successful body opens, bytes actually read, and bodies
that passed close validation. A numeric report is published with pending status
only after tensor-close and source/upstream revalidation. Only a later canonical
receipt may carry the narrow numeric PASS, and that receipt still requires an
independent result review.

## Preserved correction evidence

| Evidence | SHA-256 | Meaning |
|---|---|---|
| `SOURCE_REVIEW_ADVERSARIAL_BLOCKED.json` | `04f8500d21bd92fa05ae843965c60797e29c9d042ce96197c3ab9f9500143cdd` | Earlier four source-chain blockers; history only |
| `ROOT_CROSS_VERSION_CORRECTION_HISTORY.json` | `2008c714c353d26d0d157a43ad867828502bcaf22e05c21902d41ee896047cbc` | Python 3.12/3.13 AST-hash failure and source-segment correction |
| `SOURCE_REVIEW_PRIMARY_BLOCKED.json` | `05cb17b6974c404568a1b45ba65422ea4ca15ce593b18682527a4e327a258d3b` | Non-consuming-preflight and repeated-lock-identity blockers |
| `PRIMARY_LOCK_LIFECYCLE_CORRECTION_HISTORY.json` | `a5c58966c6713c6011257af4550bd29f53df60c74ec1e628404eafadcd9fe451` | Exact old/new identities and implemented correction |
| `history_v3_primary_blocked_23a3318e/MANIFEST.json` | `9f5d5bc9c23e332c22fa1ba26771e22ec9a6cb8bad9c1e2b36080d43e7d9c5f6` | Immutable inventory of the withdrawn source set |

None of these files is a PASS review or execution authorization.

## Static and synthetic verification

`FINAL_CANDIDATE_SELFTEST_RECEIPT.json`, SHA-256
`9dc7ddf19f6e45aa7f27b906caadfd844d0e5a002a9dae3977f7b130da0e4b13`,
records four isolated `-I -B -S` passes over the exact revised source set:

| Python | Built-in numeric self-test | Independent static/synthetic test |
|---|---|---|
| system CPython 3.13.0 | `PASS_SYNTHETIC_ONLY` | `PASS_STATIC_AND_SYNTHETIC_ONLY` |
| project CPython 3.12.14 | `PASS_SYNTHETIC_ONLY` | `PASS_STATIC_AND_SYNTHETIC_ONLY` |

Both independent runs produced maximum reference error `0.0`. They checked the
reviewed yaw sign and multiplication side, tolerance boundary and rejection
cases, list/tuple/raw-tensor provenance, pixel exclusion before body open,
preflight-before-commit order, atomic default failure receipt, duplicate-attempt
rejection, repeated lock identity checks, and unlink/recreate detection.

For audit completeness, the receipt also records a harmless shell setup error:
two first project-Python commands used a relative venv path from the candidate
subdirectory and returned shell status 127 before Python or candidate code ran.
The final matrix used the exact absolute venv path and passed both tests. No C1
or formal path was accessed by either failed shell lookup.

## Exact observed non-execution state

After the final tests, all of the following still had `lexists=false`:

- `execution_01`
- `.c1_numeric_camera_guard.lock`
- `.c1_numeric_camera_guard.lock.staging`
- `C1_CAMERA_GUARD_BINDING.json`
- `SOURCE_REVIEW_PRIMARY.json`
- `SOURCE_REVIEW_ADVERSARIAL.json`
- `BINDING_REVIEW.json`
- local `__pycache__`

This preparation performed zero formal runner calls, opened zero real C1
manifest/receipt/archive-event/tensor/image files, opened zero C1 tensor or
pixel bodies, mapped zero real scientific arrays, decoded zero pixels, viewed
zero images, and ran zero model/renderer/generation calls. All dynamic tests
used in-memory synthetic matrices and isolated temporary directories outside
the formal project paths.

## Required gates before any real array access

1. A new primary reviewer, distinct from the source author, must review the
   exact four revised hashes and create the fixed primary PASS file only if no
   blockers remain.
2. A second, distinct adversarial reviewer must independently review the same
   exact hashes and create the fixed adversarial PASS file only if no blockers
   remain. Old reviews cannot be reused.
3. Only after both PASS files exist may a separate binding author replace every
   deliberate null with exact terminal/readback/archive/source-review hashes.
   A distinct binding reviewer must then check path, role, UTC order, schema,
   status, verdict, and all hashes.
4. Only that reviewed binding may authorize the single canonical formal run.
   There are no automatic retries and no alternate output path.
5. A different result reviewer must verify the permanent attempt record,
   report, receipt, counters, source/upstream close identities, and absence of
   `lock_close_failure.json`. Only then may the narrow requested-pose/K gate be
   used for C1 row validity and allow the separately frozen blind scorer to
   proceed.

Current result: revised source candidate prepared and author-tested. No source
PASS, binding, formal camera result, C1 score, pixel view, method gain, causal
result, novelty claim, or PhD/CCF-A-level result has been established.
