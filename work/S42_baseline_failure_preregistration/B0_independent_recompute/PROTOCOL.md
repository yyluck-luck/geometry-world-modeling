# B0 attempt01 independent numeric recomputation protocol

Status: source preparation only; execution is forbidden until a different author has issued the exact source-review PASS described below.

## Purpose and evidence boundary

This program independently recomputes the already sealed B0 attempt01 RGB statistics. It does not import or call `score_b0_blind.py`, any model, renderer, generation worker, readback worker, archive decoder, PNG reader, PIL, or display API. It may read only the two sealed JSON records listed below and the nine authoritative pixel tensor bodies named by `report.score.authoritative_pixel_identities`.

The recomputation can establish numeric agreement with the sealed B0 report. It cannot establish visual quality, rendered camera obedience, whole-video correctness, repeatability, C1/C2 cohort confirmation, method gain, causal attribution, or novelty. No tensor is converted to a visible image and no image or montage is emitted.

## Frozen inputs

- Sealed receipt: `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S42_baseline_failure_preregistration/B0_score_attempt_01/receipt.json`
- Receipt SHA-256: `93c90e24e404aa1f87e111ed3a7c79d51de9d9bf35babd060ac807af9d99f2ad`
- Sealed report: `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S42_baseline_failure_preregistration/B0_score_attempt_01/report.json`
- Report SHA-256: `13b190b126e925ae18f43728781c323d5cece8d9a591b73e6e9bf3a865aa8a8e`

The receipt must identify attempt 1 as technically valid, carry status `PASS_B0_MACHINE_SCORE_SINGLE_ROW_COHORT_INCOMPLETE`, and bind the exact report path and SHA above. The report must have schema `s42-b0-blind-score-report-v1`, row `B0`, attempt 1, and exactly nine authoritative pixel identities with IDs 0 through 8.

Each pixel identity supplies the only permitted tensor path and body SHA. The tensor descriptor SHA is used only to require the canonical filename `tensors/<descriptor_sha256>.bin`; no sidecar, archive manifest, event stream, alternate cache, PNG, or other payload may be opened. Every path must be a canonical absolute regular non-symlink file under the sealed report's archive `tensors` directory. Each file must be exactly `576 * 576 * 3 = 995328` bytes and match its report-bound body SHA-256.

## Independent source-review gate

Before reading any pixel body, the program must verify its caller-bound self SHA, this protocol SHA, both sealed JSON SHAs, and a create-only review at `SOURCE_REVIEW.json`. The review must have schema `s42-b0-independent-recompute-source-review-v1`, status `PASS_S42_B0_INDEPENDENT_RECOMPUTE_SOURCE_REVIEW`, bind the exact source, protocol, receipt, and report identities, state `executed=false`, `images_viewed=false`, and `tensor_or_image_payload_bodies_read=false`, list no blockers, and name a reviewer role different from the current source author `/root`.

## Tensor identity and immutable numeric input

Each of the nine bodies is opened once with `O_RDONLY`, `O_CLOEXEC`, and `O_NOFOLLOW` where available. The implementation records `fstat`, proves the opened inode equals the canonical path inode, reads exact bytes with `pread`, computes SHA-256 over those same bytes, and creates a read-only NumPy view from the resulting immutable `bytes` snapshot. All nine file descriptors remain open until a closing `fstat`, same-FD rehash, and path-inode check succeeds. Only then may a terminal recomputation result be published.

NumPy must be version `1.26.4`. Every snapshot is interpreted as little-endian `uint8` with shape `[576,576,3]`. The program never uses a live path-backed memmap.

## Frozen numeric definitions

The primary pair is `(ID0, ID8)`. Values are converted independently per region by `uint8 -> float64 / 255.0`; squared differences are summed in float64. `M_outer4` is the disjoint union of these zero-based half-open regions:

- `R1 = [0:192, 0:192]`
- `R2 = [0:192, 384:576]`
- `R3 = [192:384, 0:192]`
- `R4 = [192:384, 384:576]`

The authoritative denominator is 442368 RGB scalars, corresponding to 147456 pixels. The single-row event is the strict comparison `unrounded_float64_MSE_M > 0.01`; equality is not an event. Display PSNR is `-10 * log10(MSE_M)`, with `+inf` represented by the sealed report's zero convention. Fixed generated-only diagnostic pairs are `(ID1,ID7)`, `(ID2,ID6)`, and `(ID3,ID5)` and never replace the primary endpoint.

The sealed full-frame diagnostic is also recomputed for `(ID0, ID8)` over all `576 * 576 * 3 = 995328` RGB scalars. It remains diagnostic and never replaces `M_outer4` as the primary endpoint.

The copy guard fails if every ID1-ID8 body SHA equals ID0, or if ID1-ID8 are all mutually identical. It is evaluated from the same report-bound snapshot hashes used for numeric computation.

## Exact comparison with the sealed report

The recomputer independently constructs the primary metric record, four region records, the full-frame diagnostic, three fixed pair records, strict event boolean, equality boolean, `row_event`, and the expected B0 row status. It compares integer counts and booleans exactly. MSE values are compared by Python float hexadecimal representation; each sealed numeric MSE must also agree with its own sealed `mse_float64_hex`. Finite PSNR values are compared by parsed float hexadecimal representation, while the zero case must preserve `None` plus the sealed `+inf` display marker.

Any difference is retained as a named mismatch. A mismatch is a completed audit outcome, not permission to rerun or change the ROI, pair, normalization, threshold, accumulation, or sealed B0 report.

## One-shot create-only output

The only result directory is `execution_01` beside this protocol. A fixed nonblocking lock is acquired before checking output state. An existing destination entry of any kind, including a broken symlink, or any hidden execution staging entry blocks a new run. Complete audit output is written create-only as `report.json` and `receipt.json` inside one mode-0700 same-parent staging directory; both files and the staging directory are fsynced before one macOS `renamex_np(..., RENAME_EXCL)` publication and parent fsync. `RENAME_EXCL` supplies atomic no-replace semantics even if a destination entry appears after the precheck.

Only a completed exact-match or completed mismatch audit is published as `execution_01`. An input, identity, source-review, runtime, or closing-FD failure writes its terminal failure receipt only inside the hidden staging directory, returns nonzero, and leaves that staging evidence in place to block automatic retry. It never promotes the failed staging directory to `execution_01`.

`PASS_EXACT_B0_NUMERIC_RECOMPUTE` means every frozen comparison agrees. `MISMATCH_B0_NUMERIC_RECOMPUTE` records all differences without altering the sealed report. An input, identity, source-review, runtime, or closing-FD failure publishes no numeric report; residual staging evidence remains fail-closed.

Every receipt, including a hidden failure receipt, records that zero images were viewed or emitted, zero model/generation/render/readback calls occurred, and the result is numeric recomputation only. It explicitly forbids interpreting that receipt as evidence of visual quality, rendered camera obedience, repeatability, cohort confirmation, causal attribution, method gain, or novelty.

## Execution rule

This preparation turn must stop after writing and hashing the source and protocol. Do not import or execute the recomputer, do not read any pixel body, and do not create `execution_01`. A different author must statically review the exact frozen source and protocol and write the required PASS before any later execution.
