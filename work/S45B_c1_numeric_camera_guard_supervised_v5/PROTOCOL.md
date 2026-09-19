# S45B supervised C1 numeric requested-camera guard protocol, v5.0.0

Status: `SOURCE_ONLY_UNBOUND_REQUIRES_FRESH_DUAL_REVIEW_NOT_EXECUTABLE`.

This revision replaces the withdrawn v4 candidate after adversarial review
`006a89e504c4f5ef8ff88c529a0e8486ddc626b2f521dbb7c8ee4ea0996c13dd`.
The prior source and both prior reviews remain immutable under
`work/S45B_c1_numeric_camera_guard_preparation/history_v4_adversarial_blocked_285f9b64/`.
The v4 primary PASS never authorizes v5.  V5 requires two new, different-author
source reviews over the complete five-file source set, then a separately
authored and reviewed terminal-identity binding.

Preparation and tests for this source open zero real C1 manifests, receipts,
events, tensors, images, or pixels.  They create no formal binding, permanent
lock, staging lock, or `execution_01`.  All execution and fault tests use only
generated matrices and isolated operating-system temporary directories.

## 1. Frozen question and math

This guard answers one narrow question required by S42 section 5(3): does the
archived **requested camera input condition** for row C1 follow the frozen
out-and-return path?  It does not test whether rendered pixels obey the camera,
and it establishes no score, visual quality, model gain, causal result, or
novelty.

The future worker may select only:

- `batch_input` occurrence 0: `target_c2ws[:4]` and `target_Ks[:4]` for ID1-ID4;
- `batch_input` occurrence 1: `target_c2ws[:4]` and `target_Ks[:4]` for ID5-ID8;
- `cache_commit` occurrence 0: `cache.c2ws/Ks[0:5]`;
- `cache_commit` occurrence 1: `cache.c2ws/Ks[0:9]`.

The required cache history is exactly 1→5→9 camera/K entries.  The first
batch's padding positions receive no identity and are never evaluated.

The frozen yaw sequence, in degrees, is
`[0, 1.25, 2.5, 3.75, 5, 3.75, 2.5, 1.25, 0]`.  Given ID0 c2w `C0`, yaw `a` in
radians, and

```text
R_y(a) = [[ cos(a), 0,  sin(a)],
          [      0, 1,       0],
          [-sin(a), 0,  cos(a)]]
```

the expected pose is fixed as:

```text
expected[:3,:3] = R_y(a) @ C0[:3,:3]
expected[:3, 3] = C0[:3, 3]
expected[3, :]  = [0, 0, 0, 1]
```

This left multiplication and sign are copied from the already reviewed B0
implementation; they are never inferred from C1.  The fixed references are:

- S42 protocol SHA-256
  `89fb44e0b77a85a66fe611cd2f885fed0288229cbb027e04da25fc0631507b3f`;
- B0 source SHA-256
  `f36be25001f5138bd985ca186d49c6d44e66b5b9c599b8c0dfc6e8691a4719de`;
- exact complete-line `max_abs` source segment SHA-256
  `5b19516bcaa6d650b7259d4e806266ab40762a358989190f2d3327fbaceb3fd4`;
- exact complete-line `verify_requested_camera_conditions` source segment
  SHA-256
  `7dfa29e4bdaca569cf485b8c575f1d48f5dbcabb61011f6ab1998fea79b9a8e3`;
- B0 primary/adversarial source-review SHA-256 values
  `befb1af9c498a1423320cbd59011c56bdd4218ac56b4bb63667f4696b31184b0`
  and
  `a2874380d0cd62c68a1c9e5749d55bc6af37d47efde5726315db80c8d3b0abeb`.

Exact source-line hashing is independent of CPython 3.12/3.13 AST formatting.
All numeric operands are converted to binary64 and must be finite.  Every error
uses elementwise maximum absolute difference with the inclusive threshold
`<= 1e-6`.  All of these checks must pass:

1. cache lengths are exactly 5 and 9, and occurrence 1 slots 0-4 equal
   occurrence 0 slots 0-4 for both c2w and K;
2. each batch target c2w/K equals its assigned cache slot, ID1-ID4 then
   ID5-ID8;
3. ID0's homogeneous row is `[0,0,0,1]`;
4. every ID0-ID8 c2w equals the planned-yaw pose and every K equals ID0 K;
5. ID8 and ID0 raw c2w and K separately close within `1e-6`.

Any failure yields
`NO_VALID_REVISIT_REQUESTED_CAMERA_CONDITION_FAILED`.  It cannot be converted
to a favorable or unfavorable pixel score.

## 2. Body-read and provenance boundary

The future formal process reads the complete archive manifest and event-chain
metadata to verify capture occurrence and hash-chain closure.  It may open body
files only for the small selected c2w/K descriptors above.  It never traverses
or opens `condition_input`, `condition_output`, sampler payloads, PNG files,
PIL nodes, `pil_frames[*].pixels`, generated images, or other tensor bodies.

Every JSON, source, receipt, manifest, and event chain is hashed and parsed from
the same `O_NOFOLLOW` file-descriptor snapshot.  A raw tensor descriptor can
enter the body reader only through the internal `TensorDescriptor` marker made
from a raw `kind=tensor` event node.  Its complete descriptor must match
`archive/manifest.json:tensor_descriptors`; body and sidecar identities must
match `manifest.files`; paths must be canonical single-link regular files under
`archive/tensors`.  Fixed shapes and byte caps reject pixel-sized tensors before
body open.  The held body FD, pathname, descriptor, size, and SHA are checked
again at close.

The implementation uses only the Python standard library and explicit binary64
loops.  It imports no NumPy, Torch, PIL, OpenCV, model, renderer, or generation
entrypoint.

## 3. Exact source and upstream gate

The reviewed source domain is all of:

1. `camera_guard.py`;
2. `supervise_camera_guard.py`;
3. this `PROTOCOL.md`;
4. `C1_CAMERA_GUARD_BINDING_TEMPLATE.json`;
5. `synthetic_selftest.py`;
6. the frozen S42/B0/S45 readback references named in the worker;
7. two fresh v5 source reviews.

The later executable binding is fixed to
`C1_CAMERA_GUARD_BINDING_V5.json`; its review is
`BINDING_REVIEW_V5.json`.  Before any tensor body open, the worker requires exact
hashes and contracts for the fixed generation manifest, clean S44 terminal and
worker receipts, S45 terminal binding, S45 supervisor/worker/report, S45
independent result review, archive manifest, and complete archive events.

The fixed S45 independent result review SHA-256 is
`2b5e4bc3dcf28f60b320ae4d3af2b4949b60a526cacc62b2deacd87ac6ddad4c`.
It must retain schema `s45-c1-readback-result-review-v1`, status
`PASS_S45_C1_READBACK_RESULT_REVIEW`, verdict
`PASS_SAVED_OUTPUT_IDENTITIES_AND_CACHE_CONSUMPTION_ONLY`, and
`row_validity_assertions.requested_pose_K_guard_pass=false`.  Identity
propagation is not accepted as numeric pose/K PASS.

The template deliberately has 15 null SHA fields: seven future source/review
identities and eight future upstream identities.  Null is never a wildcard.
The worker rejects the template and all v4 binding/review names.

Fresh source reviews use schema
`s45b-c1-numeric-camera-guard-source-review-v2`, kinds `primary` and
`adversarial`, status
`PASS_S45B_C1_NUMERIC_CAMERA_GUARD_SUPERVISED_SOURCE_REVIEW_V5`, verdict
`PASS_SUPERVISED_SOURCE_NOT_EXECUTED`, empty blockers, and zero real C1 body,
pixel, image, and execution counters.  Author plus two reviewers are pairwise
distinct.

The later binding uses schema `s45b-c1-numeric-camera-guard-binding-v2`, status
`FROZEN_C1_NUMERIC_CAMERA_GUARD_SUPERVISED_INPUT_BINDING_V5`, and zero
placeholders.  Its independent review uses schema
`s45b-c1-numeric-camera-guard-binding-review-v2`, status
`PASS_S45B_C1_NUMERIC_CAMERA_GUARD_SUPERVISED_BINDING_REVIEW_V5`, and verdict
`PASS_SUPERVISED_BINDING_ONLY_NO_TENSOR_BODIES`.  Source author, both source
reviewers, binding author, and binding reviewer are pairwise distinct and their
UTC order is enforced.

## 4. Non-consuming preflight and permanent attempt

The only formal output is this directory's `execution_01`, and the only formal
entrypoint is `supervise_camera_guard.py` under `python -I -B -S`.  The worker's
formal mode additionally requires inherited parent/lock/output/capability FDs,
the supervisor PID, and all exact identities; it cannot be invoked as a
standalone terminal authority.

The supervisor first takes an advisory exclusive lease on the source-directory
FD and runs the complete metadata/source/review/binding/upstream/event preflight.
This harmless phase occurs before a scientific attempt exists.  A failure leaves
no lock and no formal output.

Only after preflight does it write and fsync a structured default-failure JSON
at the fixed staging name, hard-link that inode to the permanent lock name,
fsync the parent, remove staging, fsync again, and retain the locked FD.  The
permanent status is
`FAIL_CLOSED_ATTEMPT_COMMITTED_NO_VALID_TERMINAL_SEAL`.  The link is the
one-use commit point; no automatic retry is allowed.  If output creation fails,
the permanent structured default-failure lock remains sufficient fail-closed
evidence even when no output-side detail can be written.

After commit, the lock and canonical source/output directories are checked from
both held FDs and canonical pathnames.  Device, inode, mode/type, link count,
size, and hash are checked at every trust boundary.  Unlink/recreate, rename,
symlink, hardlink, inventory, or content changes fail closed.

## 5. Pending worker, independent supervisor, terminal seal

The supervisor launches the exact worker in a new process group and gives it a
one-read 32-byte random pipe capability plus the already held FDs.  The worker
repeats the complete post-commit identity preflight before any tensor body open.
On numeric success it writes only:

- `report.json`, status
  `C1_REQUESTED_CAMERA_INPUT_CONDITION_RESULT_PENDING_EXTERNAL_SUPERVISOR_SEAL`,
  `passed=false`, `terminal_authority=false`;
- `worker_receipt.json`, status
  `C1_NUMERIC_CAMERA_WORKER_EVIDENCE_WRITTEN_PENDING_PROCESS_EXIT_AND_SUPERVISOR_SEAL`,
  `passed=false`, `terminal_authority=false`.

The worker source contains no `passed=true` publication.  A failure writes a
pending/failure receipt when possible, with truthful tensor opened/read/verified
counts.  It can never create `terminal_pass_seal.json`.

The supervisor drains stdout/stderr with hard byte caps, enforces wall time,
CPU, file-size and address-space limits, waits for exit code zero, and requires
the worker process group to be empty.  Nonempty stdout/stderr, overflow, timeout,
signal, surviving descendants, resource excess, or malformed pending evidence
fails closed.  It reopens report and worker receipt as single-link regular-file
leases, hashes their exact bytes, rechecks all source/binding/upstream identities,
and writes a non-authoritative `supervisor_receipt.json` plus a non-authoritative
`terminalization_barrier.json`.  Both remain `passed=false`.

Before terminal publication, the supervisor records full evidence bundles for
the permanent lock, canonical output directory, report, worker receipt,
supervisor receipt, and barrier.  Each boundary records lstat device, inode,
mode/type, link count, size, timestamps, SHA-256, and a canonical inventory
SHA-256.  Directory size/link count/inventory legitimately change as fixed
entries are added, so cross-boundary equality uses stable device/inode/mode/type
while each complete boundary record still validates its then-current size and
link count.

The sole possible `passed=true` record is staged and fsynced by the supervisor.
Publication is deliberately two-phase:

1. create, write, fsync, close, and directory-fsync
   `.terminal_pass_seal.staging`;
2. hard-link that exact inode as `terminal_pass_seal.json`; while both names
   exist, `st_nlink==2`, so the state is explicitly non-authoritative;
3. revalidate both seal names and all held lock/output/report/worker/supervisor/
   barrier evidence, fsync, successfully close every regular-artifact lease,
   and fsync again;
4. unlink the staging name as the sole atomic authority transition.

An authoritative seal must be a single-link regular file with exact schema and
status; seal staging, worker failure, and terminal failure entries must be
absent.  SIGTERM, SIGKILL, close failure, or directory-fsync failure before the
authority transition leaves either no final seal or the invalid two-link state.
Once the atomic unlink has occurred, all fallible evidence checks, file closes,
and required pre-commit fsyncs have already succeeded.  No later write is needed
to interpret that transition.

A post-commit ordinary failure is recorded as `supervisor_receipt.json` when
that name is still free, otherwise as `terminal_seal_failure.json`, when the
filesystem state permits.  The permanent default-failure lock remains the
fallback evidence if an output directory or failure write is unavailable.

Even a structurally authoritative terminal seal is pending an independent
result review of its exact canonical bundle.  Only that review may expose the
narrow row-validity precondition to the later blind scorer.

## 6. Synthetic and fault-injection acceptance

Both CPython 3.12 and 3.13 must run the following with `-I -B -S`:

- the worker's in-memory positive, negative, sign, cache, closure, nonfinite,
  and inclusive-boundary suite;
- the independent source/contract suite;
- the supervisor's nominal atomic terminal publication;
- injected staging/close/directory-fsync failures;
- isolated SIGTERM and SIGKILL at the invalid two-link boundary;
- canonical output rename/recreate and report hardlink/symlink attacks;
- stdout/stderr overflow and wall-time termination;
- permanent lock duplicate, hardlink, symlink, and unlink/recreate rejection.

Every test receipt must explicitly record zero real C1 file access, zero formal
execution, zero pixels/images, and no model or renderer calls.  Passing these
tests freezes source behavior only; it is not a C1 pose/K result.
