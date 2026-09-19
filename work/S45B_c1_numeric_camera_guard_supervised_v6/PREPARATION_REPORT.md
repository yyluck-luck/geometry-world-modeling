# S45B C1 numeric camera guard V6 source-only preparation report

Status: `FROZEN_SOURCE_ONLY_AWAITING_TWO_FRESH_V6_REVIEWS`.

Version: `S45B-supervised-held-fd-no-fork-exit-gated-v6.0.0`.

The exact five-file V6 candidate was frozen at `2026-09-08T08:34:36Z`.
The final dual-interpreter matrix was completed at `2026-09-08T08:36:33Z`.
These are observed UTC milestones, not an inferred work-duration claim.

No formal binding, governance attestation, attempt lock, or `execution_01` was
created. No real C1 manifest, receipt, event, tensor, image, or pixel body was
opened. No scientific array was mapped and no model or renderer was imported or
run. Every dynamic test used generated values and disposable OS temporary
directories.

## Frozen candidate identities

| File | SHA-256 |
|---|---|
| `camera_guard.py` | `5a4c327f52800da456cb7f6292ed9c2864e2d4c44f0988e38cadfc7972248d0c` |
| `supervise_camera_guard.py` | `bf6a9d79b2ae4015b2452af3fc711964418921ce0f3bfcd31f5a11e28947db92` |
| `PROTOCOL.md` | `8ba86240ba1fe8352230dd8b1739604e7392bb32fe5bbfcdfe088b0cde678977` |
| `C1_CAMERA_GUARD_BINDING_TEMPLATE.json` | `f3be3fb84b4f5c07b82d7d2266ee8517852f9b41301220f4e90a7b6b1af092e8` |
| `synthetic_selftest.py` | `0b616d626ee170efcbff2b4fcaf24ab53e8f1d3dfea8d59e034f38084385b413` |

The source-set receipt is `FROZEN_SOURCE_SET.json`, SHA-256
`4156b62c26e57c0717914859901053fbf4967779337b4cd6d3401bd6be53d26d`.
The final test receipt is `FINAL_SYNTHETIC_SELFTEST_RECEIPT.json`; its digest
must be computed after this report is written and is reported separately rather
than self-referenced inside the receipt.

## Preserved V5 correction history

V5 was not overwritten. Its five source hashes remain exactly:

- worker `37951063262505ef18bb62e0544c31cfb5a460434e9a67b489f58fab9315dbdb`;
- supervisor `98084f2a7806b4f88a52a6599edeba9633c066f3bb2b128c4fba2ba70577b3bd`;
- protocol `29915a117a561c73e32e30ae3f85d09d7466adb4a1a247fcda1b9da1f3366139`;
- template `12045c57d99fbaa3275f2023bef04847bcbea5825a5dac67a1be7cfb4382bd52`;
- self-test `c95331c14d2d17256da42efb94f86c636a468e33918d4db48a639c7129749593`.

The preserved V5 primary review is
`ad062bf954faeaaaf754d5ed554d0cdda0778da9e5ed1f70090c6340b060d55e`.
The preserved three-CRITICAL adversarial BLOCKED review is
`92950952b3fe260f441fe555d94a18dee589a036749035204c926ea8fe14b640`.
Neither review authorizes V6.

## How V6 addresses the three CRITICAL findings

### 1. The macOS address-space preexec failure

V6 removes the failing V5 address-space/RSS limit calls. Before consuming the
single formal attempt it runs a fresh child through the exact production
launcher, `preexec_fn`, sandbox profile, pipe monitor, Darwin libproc memory
sampling, and exact-PID `wait4` reap path. That child verifies the CPU and file
limits, touches 8 MiB, and actually launches all three forbidden process-escape
attempts. The exact resolved Python binary and `/usr/bin/sandbox-exec` identities
are hashed across the probe and checked again before a formal worker could be
launched. Any capability failure occurs before the permanent lock exists.

The 2 GiB memory condition is now an exact-PID fail-closed observation and kill
gate using live resident size, physical footprint, lifetime maximum physical
footprint, and `wait4.ru_maxrss`. It is explicitly not described as a kernel
allocation reservation.

### 2. The final path replacement window

The canonical file is now `terminal_pass_candidate.json`. It always contains
`passed=false` and `terminal_authority=false`. The supervisor holds the
candidate inode and every evidence inode across staging unlink, then rechecks
the permanent lock, canonical execution directory, report, worker receipt,
supervisor receipt, barrier, and candidate for exact device, inode, link count,
type/mode, size, bytes, and SHA.

Only after all evidence/candidate leases, directory syncs, and output/lock/parent
control FDs close successfully does the supervisor construct a truthy terminal
PASS document. That document is emitted as one exact stdout JSON record and
requires independently observed supervisor exit zero. A path alone, complete
stdout with nonzero exit, exit zero without complete exact JSON, or any later
inode mismatch blocks. Signal, fsync, and close fault tests confirm that
interrupted filesystem states contain no truthy PASS document.

### 3. The detached `setsid` descendant

V6 enforces the narrower reviewed claim that the exact worker may create no
process. The worker AST has no process-creation modules or fork/spawn/exec/system
calls, and the exact Darwin sandbox profile denies process creation. Before any
attempt, the capability child actually tries:

1. fork → setsid while keeping stdio;
2. fork → setsid after closing stdio;
3. `posix_spawn(..., setsid=True)`.

All three returned kernel `EPERM` under both required interpreters. V6 no longer
uses process-group emptiness as evidence and does not claim to find descendants
after allowing forks.

## MAJOR findings closed

Source-review JSON files are excluded from the formal-path prohibition, so the
same canonical independent suite remains runnable after reviews exist. The suite
also creates dummy completed review filenames in a temporary directory and
verifies that they are not mistaken for a formal attempt.

Role strings and UTC ordering remain structural inside candidate Python. Formal
launch additionally requires an exact post-binding
`GOVERNANCE_ATTESTATION_V6.json` whose external issuer binds source, review,
binding, task, turn, role, and UTC records. The protocol states that trusting
that issuer is an external orchestration boundary. The one-read capability SHA
and full runtime preflight are written into the permanent default-failure lock
before the worker is launched.

## Final synthetic evidence

Both CPython 3.13.0 and project CPython 3.12.14 were run with `-I -B -S` from
`/tmp`. On each interpreter:

- the worker math suite returned `PASS_SYNTHETIC_ONLY`;
- the supervisor returned
  `PASS_SUPERVISOR_SYNTHETIC_AND_FAULT_INJECTION_ONLY` with 50 checks;
- the independent suite returned
  `PASS_V6_STATIC_SYNTHETIC_AND_ATTACK_TESTS_ONLY` with 15 top-level checks.

The 50 supervisor checks include actual sandbox attacks; exact-PID memory,
wall, and stdio gates; signals before and after staging unlink; directory fsync;
candidate, evidence, and control-FD close faults; candidate commit replacement;
post-return identical-byte inode replacement; 16 combinations across four
evidence artifacts and four path attacks; four permanent-lock attacks; and
canonical output directory attacks. The independent suite also binds the B0
function-source segments, verifies planned-yaw math and the inclusive `1e-6`
boundary, checks worker pending-only publication, checks terminal truth
construction order, preserves V5 history, and rejects pixel-shaped input before
any body open.

## Formal state at freeze

All of these paths were observed absent after the final matrix:

- `execution_01`;
- `.c1_numeric_camera_guard.lock`;
- `.c1_numeric_camera_guard.lock.staging`;
- `C1_CAMERA_GUARD_BINDING_V6.json`;
- `BINDING_REVIEW_V6.json`;
- `GOVERNANCE_ATTESTATION_V6.json`;
- `SOURCE_REVIEW_PRIMARY_V6.json`;
- `SOURCE_REVIEW_ADVERSARIAL_V6.json`.

## Remaining gates

V6 cannot inherit either V5 review. The next legal sequence is:

1. fresh primary review of all five exact V6 source hashes;
2. fresh adversarial review by another reviewer, including the stated macOS and
   external-orchestration limits;
3. a different-role binding of the 15 future hashes;
4. independent no-body binding review;
5. external governance attestation;
6. one separately authorized formal supervisor run;
7. independent result review binding complete supervisor stdout, observed exit
   zero, pending candidate identity, permanent lock, and every evidence record.

This source freeze establishes no real C1 pose/K validity, rendered-camera
obedience, pixel score, visual quality, method gain, causal result, novelty, or
publication level.
