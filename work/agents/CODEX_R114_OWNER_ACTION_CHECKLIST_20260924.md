# R114 owner action checklist after the END-LINE decision

Date: 2026-09-24 (Asia/Shanghai)  
Scope: read-only handoff audit. No implementation, fixture execution, GPU/
Slurm job, protected C8/evaluation read, receipt update, or flag change.

## Handoff verdict: PASS with explicit status split

R113's `NO_REOPEN` decision can be handed to the owner as a finite checklist.
R106 supplies the complete evidence packet, R109/R110 supply the owner and
provenance fields, and R112 closes the owner-hash alias ambiguity. One status
ambiguity must be made explicit before implementation: R110 groups all owner
failures under `OWNER_REVIEW_REQUIRED`, while R89 reserves `REJECT_FIXTURE` for
malformed canonical/type/hash/alias input. The owner-facing split below keeps
both rules and removes the contradiction.

## Required packet, before any command is exposed

The owner must provide one independently reviewed, content-addressed packet
containing every item below. A partial packet remains `NO_COMMAND_AVAILABLE`:

1. **Immutable provenance:** R98 final frozen root, fresh sync nonce,
   `local:<nonce>:<final_manifest_sha256>`, post-rename `O_NOFOLLOW` reopen, and
   full digest immediately before readiness.
2. **Owner review artifact:** R70 fields `status=OWNER_ACCEPTED`, accepted
   protocol, accepted manifest, complete R52→R62→R64→R68→R70 chain,
   `decision_scope=synthetic_cpu_conformance_only`, UTC decision time, and
   independent reviewer role.
3. **Single canonical owner hash:** exactly one lowercase
   `owner_gate.review_artifact_sha256`, computed by R89 after removing only that
   JSON Pointer. Do not add `owner_subject_sha256` or any copied/alias hash.
4. **R85 identity tuple:** exactly seven `manifest_identity` fields, fixed
   schemas/roles/paths, independently recomputed code/H2/boundary hashes, and
   `runner_code_manifest_sha256 != h2_source_manifest_sha256`.
5. **H2 provenance:** `h2_source_manifest`, `h2_packet`, and
   `boundary_artifact`, with typed `T_c2w`/camera-to-world convention, explicit
   formulas, numeric bidirectional error and threshold `<=1e-6`, and matching
   source/boundary hashes.
6. **Synthetic contract:** sealed metric plane/cube fixture, known cameras and
   `K`, depth units, crop/rounding, independent identity fixture, calibration
   and held-out scale, camera-keyed computed visibility, and all R62/S131 arm
   and denominator fields. Target RGB/depth must remain sealed until commits.
7. **Runner and controls:** source-pinned CPU-only runner. Provide the supported CPU command **text and discovery evidence for review only**. Until the complete packet and every gate are independently accepted, do not execute, dispatch, schedule, or expose the command as runnable. Include access-matched append-only, generic-completion, robust-gate, no-reveal,
   wrong-component, and no-transport controls, plus reveal-camera versus
   third-camera scores and the R104 primary-paper comparison.

R106 requires these as one packet; a conformance result alone is not novelty
evidence (`work/agents/CODEX_R106_ENDLINE_REOPEN_CRITERIA_20260924.md:29-55`).

## Canonical gate and status order

Apply the checks in this order:

| Order | Check | Failure status and action |
|---|---|---|
| 0 | Final frozen snapshot, nonce, inode/link, roles, sizes, hashes, and digest | `STALE` or `REMOTE_PROVENANCE_UNVERIFIED`; abandon snapshot and restart with a new nonce. Do not inspect owner/H2. |
| 1 | Strict JSON/canonical types, duplicate keys, exact R85 tuple shape, no aliases/markers, valid lowercase hash syntax | `REJECT_FIXTURE` before materialization. |
| 2 | Well-formed owner artifact is missing, stale, replayed, semantically mismatched, or its single supplied hash does not match the R89 subject | `OWNER_REVIEW_REQUIRED` before materialization/H2. |
| 3 | Owner passes; open only role-allowed H2 files and independently recompute code/H2/boundary hashes and typed transform error | `H2_UNIDENTIFIABLE` before fixture-context/hash/score. |
| 4 | H2 passes; validate visibility, arm rules, denominators, target sealing, and negative controls | `REJECT_FIXTURE` for ambiguity/leakage or `UNTESTABLE_NO_DENOMINATOR` for zero denominator. |
| 5 | Compare the CGLR signature with access-matched controls | `REJECT_NON_IDENTIFIABLE` if `mask_only_local` or `residual_transport_untyped` reproduces it; keep END-LINE. |

This split reconciles R89's malformed-input rule with R110's owner-review rule:
syntax/type/alias failures are fixture rejection; a valid artifact that is
missing, stale, replayed, or semantically mismatched requires owner review.
R112's one-field owner procedure is used at step 2
(`work/agents/CODEX_R112_CANONICAL_OWNER_HASH_CLOSURE_20260924.md:26-58`).

## Owner decision and stop condition

The owner action is to assemble and independently review the packet, then
provide the supported CPU command **text and discovery evidence for review
only**. Until the complete packet and every gate are independently accepted, do
not execute, dispatch, schedule, or expose the command as runnable. This action
is not permission to run CPU, GPU, Slurm, C8, or evaluation work. Until every
item exists and the gate order passes, retain `NO_REOPEN`,
`NO_COMMAND_AVAILABLE`, `new_method_validated=false`,
`novelty_authorization=NONE`, and END-LINE. Even if the synthetic benchmark
later passes, method novelty still requires the matched-control improvement and
independent prior-art comparison specified by R106/R113.

**R114 status: PASS / owner checklist complete / status precedence explicit /
NO EXECUTION.**

