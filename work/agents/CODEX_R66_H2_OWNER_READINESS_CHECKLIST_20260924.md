# R66 H2 provenance and owner-acceptance readiness checklist

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only readiness checklist. No provenance is fabricated and no synthetic fixture, real C8 data, replay, GPU/Slurm job, receipt, or validation flag is executed or changed.

## Purpose

R65 marked the schema owner-ready. This checklist defines the concrete evidence that must be supplied before the first synthetic CPU conformance run. It separates provenance and owner authorization from the later fixture result. A checklist item is not satisfied by a placeholder, a source-path citation alone, or an assistant assertion.

## 1. Owner-acceptance artifact

Supply one independently reviewable JSON artifact with these exact fields:

```json
{
  "owner_gate": {
    "status": "OWNER_ACCEPTED",
    "review_artifact_sha256": "actual 64-character lowercase SHA-256",
    "accepted_protocol": "R62_R60_TWO_PHASE_OWNER_GATE_CORRECTION",
    "accepted_manifest": "R64_R62_H2_PRECEDENCE_CORRECTION",
    "decision_scope": "synthetic_cpu_conformance_only",
    "decision_time_utc": "actual ISO-8601 timestamp",
    "reviewer_role": "actual independent reviewer identity or approved institutional role"
  }
}
```

Readiness checks:

* `status` must be exactly `OWNER_ACCEPTED`; otherwise stop with `OWNER_REVIEW_REQUIRED`.
* `review_artifact_sha256` must be recomputed from the exact review artifact bytes and match.
* `accepted_protocol` and `accepted_manifest` must match the R62/R64 design being reviewed.
* Scope must be limited to the synthetic CPU contract. It cannot authorize C8 replay, learned-model claims, novelty claims, GPU/Slurm, or receipt edits.
* The artifact must identify an independent reviewer and an actual UTC decision time. Do not infer either value.

The review artifact should include the R65 verdict, the reviewed file list and hashes, the R64 H2 precedence check, the ten-arm mapping check, and an explicit statement that expected visibility sets are not run-time masks.

## 2. H2 provenance object

Supply a second owner-reviewed object with no placeholders:

```json
{
  "h2_provenance": {
    "frame_label": "optical_cv" or "vmem_gl",
    "source_manifest_sha256": "actual 64-character lowercase SHA-256",
    "boundary_artifact_sha256": "actual 64-character lowercase SHA-256",
    "identity_formula": "inv(T_frame) @ X == p_frame",
    "max_abs_error": "actual finite value <= 1e-6",
    "status": "PASS"
  }
}
```

Any missing, marker-valued, malformed, ambiguous, or failed field returns `H2_UNIDENTIFIABLE` before H2-dependent hash extraction or any arm score. The frame label is evidence about the producer pointmap convention, not a choice made by the synthetic fixture.

## 3. Source-manifest identity evidence

Compute `source_manifest_sha256` over the exact bytes of the source files used to establish the producer/boundary convention. The manifest must list path, byte length, SHA-256, repository commit or immutable source identifier, and retrieval time for each file:

* `work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py`
* `work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R/src/dust3r/utils/geometry.py`
* `work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R/cloud_opt/dust3r_opt/optimizer.py`

The reviewer must confirm:

1. the files are the exact producer and boundary code used for the declared artifact;
2. no path is a stale backup, generated copy, or uncommitted replacement;
3. the manifest hash is recomputed independently from the listed bytes;
4. the source code lines used for frame labels, `c2w`, pointmap conversion, and inverse transform are recorded as path-plus-line references in the review artifact.

A source path without byte hashes and line-level identity evidence is insufficient.

## 4. Boundary artifact contents and identity check

The boundary artifact must be a self-contained, immutable CPU-checkable record containing:

* producer frame label and boundary frame label;
* one known camera-frame point `p_frame` with units and numeric precision;
* one exact `T_frame`/`c2w` matrix with convention, shape, and numeric values;
* the expected world point `X_world` computed by the declared operation;
* the exact operation sequence used at the CUT3R/VMem boundary, including inverse/forward direction;
* a per-component error table for all coordinates;
* the computed `max_abs_error` and comparison threshold `1e-6`;
* artifact schema version, source-manifest hash, creation timestamp, and artifact hash.

The independent reviewer must recompute, without learned weights or target RGB/depth:

```text
X_world_recomputed = inv(T_frame) @ p_frame
error = max(abs(X_world_recomputed - X_world_recorded))
```

The reviewer records the raw vectors, matrix convention, operation direction, error, and PASS/FAIL decision. A helper-function test without a producer pointmap-frame declaration is not sufficient. A frame-label mismatch, inverse/forward mismatch, non-finite value, or error above `1e-6` is `H2_UNIDENTIFIABLE`.

## 5. Independent-review evidence

The review packet must contain, at minimum:

* the owner-gate artifact hash and accepted protocol/manifest IDs;
* source-manifest table with recomputed hashes and line references;
* boundary artifact hash and the independently recomputed identity table;
* explicit confirmation that no real C8 target RGB/depth, future camera answer, or learned weight was used;
* explicit confirmation that scene_13/scene_14 are not being treated as independent held-out evidence;
* reviewer identity/role, decision time, tool/runtime used for the CPU identity check, and PASS/FAIL rationale;
* a statement that a synthetic `PASS_CONTRACT_REPLAY` can establish only contract conformance, not novelty or learned-model benefit.

The reviewer should be independent of the person who authored the synthetic arm rules. If institutional policy allows one reviewer, independence and scope must still be documented; otherwise obtain the required second sign-off. Do not invent names, timestamps, hashes, or signatures.

## 6. Minimal synthetic CPU-conformance entry conditions

Only after sections 1–5 are satisfied may an owner consider a fixture-only CPU run. The pre-run gate must report:

1. `owner_gate.status=OWNER_ACCEPTED` and review hash equality;
2. H2 object `status=PASS`, valid frame label, source/boundary hashes, exact identity formula, and `max_abs_error <= 1e-6`;
3. phase-0 static preflight passes with no forbidden markers outside the H2 subtree;
4. phase-1 computed envelope is materialized from world points, camera poses, K, normals, and the R56/R64 visibility predicate;
5. expected visibility declarations are excluded from computed masks, query separation, denominators, and all arm hashes;
6. all computed, manifest, context, per-event base, per-arm rule, and per-event/arm input hashes are recomputed and equal to their supplied values;
7. all ten arm IDs/rules/typed parameters match the closed R62 table;
8. all arms for an event share the recomputed base input hash;
9. the run is synthetic-only, CPU-only, deterministic, and has no real C8 or target-sensor inputs;
10. the run has a predeclared output directory and immutable input snapshot, with no receipt or validation-flag mutation.

If any condition fails, stop before arm score. The appropriate terminal is `OWNER_REVIEW_REQUIRED`, `H2_UNIDENTIFIABLE`, or `REJECT_FIXTURE`; do not downgrade a missing prerequisite to a partial pass.

## 7. What the first CPU run may and may not establish

The first run may test computed visibility consistency, hash integrity, arm invariants, event signatures, and strong-control identifiability on the synthetic state machine. It may produce `REJECT_CONTRACT`, `REJECT_NON_IDENTIFIABLE`, `UNTESTABLE_NO_DENOMINATOR`, or `PASS_CONTRACT_REPLAY` according to R52/R64.

It may not establish a learned world-model improvement, real C8 support, literature novelty, hidden-surface scarcity, or paper acceptance. GPU/Slurm, real-data replay, and validation-flag changes remain separate decisions requiring their own evidence.

## Decision

**R66 status: READINESS CHECKLIST COMPLETE / DESIGN-ONLY.** No H2 provenance, owner signature, hash, or reviewer identity has been fabricated. The next permissible action is owner/reviewer completion of this packet; only then can a synthetic CPU-only conformance run be considered.
