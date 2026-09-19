# S45B supervised C1 numeric requested-camera guard protocol, V6.0.0

Status: `SOURCE_ONLY_UNBOUND_REQUIRES_FRESH_DUAL_REVIEW_NOT_EXECUTABLE`.

V6 replaces the blocked V5 source candidate. The exact V5 adversarial review is
`92950952b3fe260f441fe555d94a18dee589a036749035204c926ea8fe14b640`.
V5 source, its primary review, and its BLOCKED review remain unchanged in
`work/S45B_c1_numeric_camera_guard_supervised_v5/`. No V5 PASS transfers to V6.

This preparation opens no real C1 manifest, receipt, event, tensor, image, or
pixel. It creates no formal binding, governance attestation, permanent lock, or
`execution_01`, and it imports or runs no model. All dynamic tests use generated
matrices and disposable operating-system temporary directories.

## 1. Threat model fixed before implementation

V6 must fail closed against these source-level and same-user concurrent faults:

1. a nonportable `preexec_fn` fails only after the permanent one-use lock;
2. report, receipt, lock, output directory, staging candidate, or final candidate is
   replaced by symlink, hardlink, rename/recreate, or unlink/recreate;
3. a child forks, calls `setsid`, closes inherited stdio, and survives the
   original process group;
4. stdout/stderr overflow, wall timeout, CPU/file/memory excess, signal,
   `fsync`, or required close failure occurs near terminalization;
5. worker success is mistaken for terminal success;
6. role names, timestamps, or a one-use token are accepted only because the
   same JSON document asserts them.

The enforced process claim is deliberately narrow: the exact reviewed worker is
one process and may not create another process. Its AST is rejected if it imports
process-creation modules or calls fork/spawn/exec/system APIs. On the reviewed
macOS host the production command is wrapped by `/usr/bin/sandbox-exec` with
`(deny process-fork)`. Before a permanent attempt exists, the same production
launcher actually attempts fork→setsid with stdio kept open, fork→setsid with
stdio closed, and `posix_spawn(..., setsid=True)`; all must fail with `EPERM`.
V6 does not claim to discover every descendant after allowing forks.

The candidate cannot authenticate Codex task identity inside one Unix account.
Therefore unequal role strings and ordered timestamps are structural checks,
not identity proof. Formal launch additionally requires a separate exact
`GOVERNANCE_ATTESTATION_V6.json`, created after both source reviews, binding, and
binding review by the external orchestration layer. The candidate validates its
cross-document artifact, task, turn, role, and UTC consistency. Trust in that
external issuer remains an explicit governance boundary.

Root/kernel compromise and malicious changes already accepted by both fresh
source reviewers are outside this source-only guard. A later canonical pathname
is also mutable: it can match a held observation, but never creates authority by
itself.

## 2. Frozen scientific question and math

The guard answers only S42 section 5(3): did archived **requested camera input**
for row C1 follow the frozen out-and-return path? It does not show that rendered
pixels obeyed those cameras and establishes no pixel score, visual quality,
method gain, causal result, novelty, or publication level.

The future worker may select only:

- `batch_input` occurrence 0: `target_c2ws[:4]`, `target_Ks[:4]` for ID1–ID4;
- `batch_input` occurrence 1: `target_c2ws[:4]`, `target_Ks[:4]` for ID5–ID8;
- `cache_commit` occurrence 0: `cache.c2ws/Ks[0:5]`;
- `cache_commit` occurrence 1: `cache.c2ws/Ks[0:9]`.

Cache history is exactly 1→5→9 entries. First-batch padding is not assigned an
identity and is not evaluated.

Frozen yaw in degrees is `[0,1.25,2.5,3.75,5,3.75,2.5,1.25,0]`. For ID0 c2w
`C0` and yaw `a` in radians:

```text
R_y(a) = [[ cos(a), 0,  sin(a)],
          [      0, 1,       0],
          [-sin(a), 0,  cos(a)]]
expected[:3,:3] = R_y(a) @ C0[:3,:3]
expected[:3, 3] = C0[:3, 3]
expected[3, :]  = [0,0,0,1]
```

The sign and left multiplication are copied from reviewed B0, never inferred
from C1. Fixed references are:

- S42 protocol `89fb44e0b77a85a66fe611cd2f885fed0288229cbb027e04da25fc0631507b3f`;
- B0 source `f36be25001f5138bd985ca186d49c6d44e66b5b9c599b8c0dfc6e8691a4719de`;
- `max_abs` complete-line segment
  `5b19516bcaa6d650b7259d4e806266ab40762a358989190f2d3327fbaceb3fd4`;
- requested-camera function segment
  `7dfa29e4bdaca569cf485b8c575f1d48f5dbcabb61011f6ab1998fea79b9a8e3`;
- B0 primary/adversarial reviews
  `befb1af9c498a1423320cbd59011c56bdd4218ac56b4bb63667f4696b31184b0`
  and `a2874380d0cd62c68a1c9e5749d55bc6af37d47efde5726315db80c8d3b0abeb`.

All operands become finite binary64 values. Every matrix comparison is maximum
absolute element error with inclusive threshold `<=1e-6`. All checks pass only
when cache overlap, batch→cache mapping, homogeneous row, planned yaw, fixed K,
and raw ID8→ID0 c2w/K closure pass. Failure is
`NO_VALID_REVISIT_REQUESTED_CAMERA_CONDITION_FAILED` and cannot become a score.

## 3. Body and provenance boundary

The future formal worker reads complete metadata and event hashes, then opens
only the selected small c2w/K tensor bodies. It never traverses or opens
`condition_input`, `condition_output`, sampler payloads, `pil_frames[*].pixels`,
PNG/PIL/image bodies, other tensors, model, renderer, or generation entrypoints.

Tensor bodies require an internal marker built from an exact raw
`kind=tensor` node, a complete match to the archive descriptor, a canonical
single-link regular file under `archive/tensors`, a fixed camera shape, a small
byte cap, and same-FD SHA/identity revalidation at close. Pixel-sized shapes are
rejected before any body open. Implementation uses Python standard library and
explicit binary64 loops, without NumPy, Torch, PIL, OpenCV, or model libraries.

## 4. Source, binding, and governance gates

The reviewed V6 source set is exactly:

1. `camera_guard.py`;
2. `supervise_camera_guard.py`;
3. this `PROTOCOL.md`;
4. `C1_CAMERA_GUARD_BINDING_TEMPLATE.json`;
5. `synthetic_selftest.py`.

Two fresh reviews use schema
`s45b-c1-numeric-camera-guard-source-review-v3`, kinds `primary` and
`adversarial`, status
`PASS_S45B_C1_NUMERIC_CAMERA_GUARD_SUPERVISED_SOURCE_REVIEW_V6`, exact five-file
identities, zero real C1/model/formal counters, and empty blockers. They also
record externally matchable reviewer task and turn IDs. Review files are not
formal attempt paths, so the canonical full synthetic suite remains runnable
after a primary review exists.

The later binding is `C1_CAMERA_GUARD_BINDING_V6.json`, schema
`s45b-c1-numeric-camera-guard-binding-v3`, status
`FROZEN_C1_NUMERIC_CAMERA_GUARD_SUPERVISED_INPUT_BINDING_V6`. Its independent
review is `BINDING_REVIEW_V6.json`, schema
`s45b-c1-numeric-camera-guard-binding-review-v3`, status
`PASS_S45B_C1_NUMERIC_CAMERA_GUARD_SUPERVISED_BINDING_REVIEW_V6`. Both include
task/turn provenance fields. The unbound template has 15 future source/upstream
hash nulls. Null is never a wildcard.

After binding review, external orchestration creates
`GOVERNANCE_ATTESTATION_V6.json`. It binds the five sources, both source reviews,
binding, binding review, V5 BLOCKED evidence, role/task/turn/UTC events, and its
issuer task/turn. Its SHA is supplied separately to the formal command. This
extra receipt avoids treating each artifact's own role/time fields as sole
evidence while preserving the explicit external trust boundary.

The fixed S45 result review remains
`2b5e4bc3dcf28f60b320ae4d3af2b4949b60a526cacc62b2deacd87ac6ddad4c`,
with `requested_pose_K_guard_pass=false`. Identity propagation is not numeric
pose/K PASS.

## 5. Pre-attempt resource and containment capability

`supervise_camera_guard.py` under `python -I -B -S` first runs all source,
review, binding, governance, upstream, and event metadata gates. It then runs an
exact production-launcher capability probe before creating a lock or output.

Darwin rejects the V5 `RLIMIT_AS=2 GiB` preexec call. V6 never calls
`RLIMIT_AS`, `RLIMIT_RSS`, or `RLIMIT_DATA`. The shared production `preexec_fn`
sets only successfully probed `RLIMIT_CPU=120 s` and `RLIMIT_FSIZE=64 MiB`.
Memory uses the exact supervised PID: `proc_pid_rusage(RUSAGE_INFO_V4)` is sampled
every 20 ms and the exact PID is reaped by `wait4`; live physical footprint,
resident size, lifetime high-water, and `wait4.ru_maxrss` are all recorded. Any
monitor error, zero sample, or maximum above 2 GiB prevents PASS and terminates
the PID. `wait4` also supplies per-child CPU evidence, avoiding unrelated-child
aggregation.

The capability probe uses that same sandbox wrapper, `preexec_fn`, pipe drain,
wall/output monitor, libproc memory monitor, and `wait4` path. It touches 8 MiB,
verifies actual CPU/file limits, and runs all three fork/setsid/spawn attacks.
Any failure occurs before the one-use attempt. The exact sandbox executable
identity, profile SHA, worker no-process AST audit, kernel attack observations,
interpreter, resource observations, and UTC interval enter the permanent lock.

## 6. Permanent attempt and worker capability

Only after both harmless gates pass does the supervisor generate the 32-byte
one-read capability, create its pipe, and atomically commit a structured default
failure lock. The lock includes the capability SHA, governance SHA, exact source
and review identities, and full runtime capability record. Therefore the worker
cannot choose both token and expected digest after commit.

The lock is staged, fully written, fsynced, hard-linked to the permanent name,
parent-fsynced, staging-unlinked, parent-fsynced, and retained by FD and flock.
Its default status is
`FAIL_CLOSED_ATTEMPT_COMMITTED_NO_VALID_TERMINAL_SEAL`; attempt 1 is permanently
consumed and automatic retry count is zero. Every later trust boundary checks
the lock, source directory, canonical execution directory, report, worker
receipt, supervisor receipt, and terminalization barrier by held FD and pathname
for device, inode, type/mode, link count, size, exact bytes, and SHA.

The worker verifies the capability pipe and separately verifies that its digest,
runtime-preflight status, and governance digest are inside the exact held lock.
Before any tensor body, it repeats every source/binding/governance/upstream/event
gate. Worker numeric success writes only pending artifacts with `passed=false`
and `terminal_authority=false`. The worker has no `passed=true` constructor.

## 7. No-fork worker supervision

The exact formal worker launches only through the reviewed sandbox profile. The
same source AST has no process-creation/exec calls. Because fork and posix_spawn
are denied by the kernel, process-group emptiness is neither used nor claimed.
The supervisor tracks and reaps the exact PID, drains both pipes with hard byte
limits, and accepts only exit 0, empty stdout/stderr, no timeout, no monitor
failure, CPU within 120 seconds, file size within 64 MiB, and maximum memory no
greater than 2 GiB.

This closes the V5 setsid+stdio-closure escape by preventing descendant creation.
If a future worker needs subprocesses, it requires a new containment design,
new source version, and two new reviews; V6 cannot simply relax the sandbox.

## 8. Held-FD candidate and exit-gated terminal authority

The supervisor opens pending report and worker receipt as held leases, verifies
them, then writes pending-only supervisor receipt and barrier. It stages the full
V6 **pending terminal candidate**, fsyncs it, hard-links the same inode to
`terminal_pass_candidate.json`, and verifies the invalid two-link state. Both
candidate names contain `passed=false` and `terminal_authority=false`; no
filesystem path written by the publication routine contains a truthy PASS.

Unlike V5, it does not close evidence/candidate FDs before unlinking staging. After
the unlink it:

1. directory-fsyncs and requires staging absent;
2. proves the still-held final/stage FDs identify the same now-single-link inode;
3. rechecks canonical final pathname against that held inode and exact bytes;
4. rechecks the permanent lock, canonical execution directory, and every held
   evidence FD/path/SHA;
5. parses the complete expected V6 pending candidate, not selected fields;
6. creates an in-memory candidate observation containing candidate SHA, byte count,
   inode identity, and evidence-projection SHA while all core FDs are held;
7. performs required evidence/candidate closes and a final output-directory
   fsync, then fsyncs and successfully closes the output, permanent-lock, and
   parent-directory control FDs;
8. only then constructs and emits one complete
   `s45b-c1-numeric-camera-guard-terminal-pass-seal-v3` JSON record with
   `passed=true` on supervisor stdout and exits 0.

Rename/recreate or unlink/recreate immediately after staging unlink is detected
before the observation can return. Signal, directory-fsync, or close failure
may leave a one-link candidate, but that file is explicitly pending and false;
it produces no terminal stdout/exit pair. A later result review must bind the
complete captured supervisor stdout JSON, independently observed exit 0, exact
candidate SHA and inode, permanent lock, all evidence, and confirm the current
canonical candidate still matches; mismatch blocks rather than adopting
replacement bytes. Complete stdout without exit 0, exit 0 without one complete
exact stdout JSON, or a canonical candidate by itself has no authority.

## 9. Synthetic acceptance and known limits

Both CPython 3.12 and 3.13 run under `-I -B -S`:

- worker math positive/negative/sign/cache/closure/nonfinite/boundary cases;
- exact production capability preflight and three kernel-denied escape attacks;
- exact-PID libproc/wait4 memory gate, wall timeout, stdout/stderr overflow;
- nominal held-FD pending-candidate observation and exit-gated PASS construction;
- identical-byte final-inode swaps before and after the commit boundary;
- SIGTERM/SIGKILL both before and after staging unlink;
- staging, directory-fsync, and actual required-close error paths;
- actual output/lock/parent control-FD close failures before PASS construction;
- lock/output/evidence symlink, hardlink, rename, and unlink-recreate attacks;
- source suite with completed source-review filenames present;
- V5 source, primary review, and three-CRITICAL BLOCKED review immutability;
- tensor list/tuple/scalar provenance and pixel-shape pre-open rejection.

Known platform limit: V6 formal containment is macOS-specific and depends on
`sandbox-exec` and libproc behavior proven at runtime. Missing/changed behavior
blocks before attempt; there is no fallback. Memory is a fail-closed acceptance
and kill monitor, not a kernel allocation reservation. The external governance
issuer and capture of supervisor stdout/exit remain orchestration trust
boundaries. These limits must appear in both new source reviews.

Passing every synthetic test freezes source behavior only. It does not create a
C1 pose/K result or authorize a binding, formal attempt, score, image inspection,
method claim, or novelty claim.
