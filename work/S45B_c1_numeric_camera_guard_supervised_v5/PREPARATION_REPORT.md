# S45B supervised C1 numeric camera guard v5.0.0 — preparation report

Status: **source candidate frozen; fresh dual review required; no formal execution authorized**.

## Purpose and exact boundary

S42 requires a numeric check that the requested C1 camera/K inputs followed the
predeclared ID0→ID8 out-and-return path.  S45 proved saved-output identity and
cache-consumption propagation, but its independent result review deliberately
left `requested_pose_K_guard_pass=false`.  This candidate supplies the missing
numeric precondition without scoring or viewing pixels.

The strongest future result is limited to archived c2w/K **input-condition
validity**.  It cannot establish a pixel score, image quality, rendered-camera
obedience, model correctness, method gain, causal effect, novelty, or CCF-A/PhD
claim.

No real C1 manifest, receipt, event file, tensor body, image, or pixel was opened
while creating or testing v5.  No model, renderer, generation worker, readback,
formal numeric guard, binding, permanent lock, or `execution_01` was run or
created.

## Why v4 was withdrawn

V4 primary review passed, then adversarial review SHA-256
`006a89e504c4f5ef8ff88c529a0e8486ddc626b2f521dbb7c8ee4ea0996c13dd`
found two blockers:

1. a worker-local receipt could already say `passed=true` before the process
   returned and before late close/fsync/identity checks completed;
2. the canonical output directory and report/receipt inodes were not retained
   and revalidated through terminal publication.

All exact v4 source, preparation evidence, primary PASS, and adversarial BLOCKED
files remain under
`work/S45B_c1_numeric_camera_guard_preparation/history_v4_adversarial_blocked_285f9b64/`.
Its new history manifest has SHA-256
`666c317e9fb0975a59f770b13d11a7018055915c04adce14297c71f28e9f8b3c`.
Neither the v4 PASS nor the v4 BLOCKED receipt grants any v5 authority.

## V5 correction

V5 separates scientific computation from terminal authority:

- `camera_guard.py` is a capability-gated child worker.  It performs the fixed
  c2w/K check and can write only `passed=false`, `terminal_authority=false`
  pending report/receipt evidence.  It contains no `passed=true` constructor.
- `supervise_camera_guard.py` owns the one-use attempt.  It runs all harmless
  identity/review/binding/upstream/event checks before committing the permanent
  default-failure lock, then starts the exact worker with inherited held FDs and
  a one-read random pipe capability.
- The supervisor hard-bounds stdout/stderr capture, wall time, CPU, address
  space, output-file size, and requires child exit 0 plus an empty process group.
- After child exit it retains and rechecks the permanent lock, canonical output
  directory, report, worker receipt, supervisor receipt, and terminalization
  barrier using held FDs plus canonical path lstat.  Evidence records include
  device, inode, mode/type, link count, size, timestamps, byte length, SHA-256,
  and a directory-inventory SHA-256.
- A PASS seal is first a closed and fsynced single staging inode.  Hard-linking
  it to the final name makes an explicitly invalid two-name, `st_nlink==2`
  state.  After all fallible evidence checks, artifact closes, and directory
  fsyncs succeed, deleting the staging name is the sole authority transition.
  Before that deletion, SIGTERM, SIGKILL, close/fsync failure, aliasing, or
  replacement leaves no structurally valid PASS.
- A valid seal still requires an independent result review before downstream C1
  scoring can use the pose/K precondition.

The scientific math and evidence selection did not change: IDs 0–8, yaw
`[0,1.25,2.5,3.75,5,3.75,2.5,1.25,0]` degrees, reviewed B0 positive-sign
left Y multiplication, binary64 maximum absolute error, inclusive `<=1e-6`,
exact cache history 1→5→9, batch-target/cache equality, constant K, and separate
ID8→ID0 raw c2w/K closure.

## Frozen source candidate

Frozen at `2026-09-08T06:21:32Z`:

| File | SHA-256 | Bytes | Links at freeze |
|---|---|---:|---:|
| `camera_guard.py` | `37951063262505ef18bb62e0544c31cfb5a460434e9a67b489f58fab9315dbdb` | 77,961 | 1 |
| `supervise_camera_guard.py` | `98084f2a7806b4f88a52a6599edeba9633c066f3bb2b128c4fba2ba70577b3bd` | 55,956 | 1 |
| `PROTOCOL.md` | `29915a117a561c73e32e30ae3f85d09d7466adb4a1a247fcda1b9da1f3366139` | 13,278 | 1 |
| `C1_CAMERA_GUARD_BINDING_TEMPLATE.json` | `12045c57d99fbaa3275f2023bef04847bcbea5825a5dac67a1be7cfb4382bd52` | 6,676 | 1 |
| `synthetic_selftest.py` | `c95331c14d2d17256da42efb94f86c636a468e33918d4db48a639c7129749593` | 22,885 | 1 |

`FROZEN_SOURCE_SET.json` SHA-256:
`4be945c0daa344ef767be6d30efe1269eaa7f82474d8d5cce1a783edff11401f`.

The worker binds the exact protocol, binding template, and independent selftest.
The worker and source-review schemas additionally bind the exact supervisor at
future review/binding time, avoiding a circular embedded self-hash.

## Final cross-version synthetic evidence

The final frozen source was tested between `2026-09-08T06:21:31Z` and
`2026-09-08T06:21:32Z`.  Every command used `-I -B -S`.

| Interpreter | Worker numeric suite | Supervisor fault suite | Independent full suite |
|---|---|---|---|
| CPython 3.13.0 | PASS | PASS | PASS |
| project CPython 3.12.14 | PASS | PASS | PASS |

The direct worker and supervisor outputs were byte-identical across the two
interpreters.  The independent output differed only because it records the
interpreter's full version string; all five source hashes and verdicts matched.

Covered cases include positive/negative yaw math, wrong sign, nonfinite values,
the exact inclusive threshold, raw tensor/list/tuple provenance, pixel-shape
pre-open rejection, non-consuming preflight, structured permanent default
failure, duplicate attempt, lock hardlink/symlink/unlink-recreate, canonical
output rename-recreate, report hardlink/symlink, staged-seal close/fsync
boundaries, SIGTERM/SIGKILL in the invalid two-link state, terminal failure
marker invalidation, stdout/stderr overflow, wall-time termination, and formal
path absence before and after.

`FINAL_SYNTHETIC_SELFTEST_RECEIPT.json` SHA-256:
`14da9ce1cdc3d671f96bd8917981c79630e2b42b84c7c7f135370d1c7d4cefd6`.

These are source/static/synthetic tests.  They are not a simulated C1 result and
not a real C1 experiment.

## Formal paths observed absent

At `2026-09-08T06:21:32Z`, each was absent, including as a symlink:

- `execution_01`;
- `.c1_numeric_camera_guard.lock`;
- `.c1_numeric_camera_guard.lock.staging`;
- `C1_CAMERA_GUARD_BINDING_V5.json`;
- `BINDING_REVIEW_V5.json`;
- `SOURCE_REVIEW_PRIMARY_V5.json`;
- `SOURCE_REVIEW_ADVERSARIAL_V5.json`.

## Required gates; do not skip

1. A new primary reviewer, distinct from the author, must review all five exact
   source identities and the fixed reference identities.  V4 review files are
   invalid for this source.
2. A new adversarial reviewer, distinct from both author and primary reviewer,
   must repeat static and temporary-directory attack review.  Both reviews must
   use schema `s45b-c1-numeric-camera-guard-source-review-v2`, exact v5 status
   and verdict, empty blockers, `executed=false`, and zero C1 body/pixel/image
   counters.
3. Only after both PASS may a fourth role create
   `C1_CAMERA_GUARD_BINDING_V5.json` from the 15 real missing hashes.  A fifth
   role must independently review it into `BINDING_REVIEW_V5.json`.  Null or
   wildcard identities remain forbidden.
4. Only the exact frozen supervisor may then consume the single formal attempt.
   A worker receipt is never terminal evidence.
5. After a structurally valid terminal seal, another independent result review
   must validate the full canonical evidence bundle before row C1 can be scored.

Until gates 1–3 pass, this directory is deliberately non-executable.  The
correct current state is “prepared source candidate,” not “camera guard passed.”
