# R85 manifest-identity tuple correction for the future CGLR runner

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only correction to R83/R84. No runner, fixture, manifest,
review artifact, H2 packet, boundary artifact, receipt, real C8 input,
GPU/Slurm job, or validation flag was created, opened, or modified.

## Decision and boundary

Apply exactly the one correction required by R84: make the independently
reviewed separation between runner code identity and H2 producer/boundary
identity machine-readable. This memo is a future-only contract addendum. All
paths and JSON objects below are proposed; they are not present artifacts.

`NO_COMMAND_AVAILABLE` remains in force until an owner-reviewed implementation
exists. The correction does not authorize opening producer source paths or
performing a real-data replay.

## Canonical owner-reviewed tuple

The owner-bound `review_artifact.json` must contain exactly one canonical
`manifest_identity` object with these required fields:

```json
{
  "manifest_identity": {
    "runner_code_manifest_sha256": "<lowercase 64-hex>",
    "h2_source_manifest_sha256": "<lowercase 64-hex>",
    "h2_boundary_artifact_sha256": "<lowercase 64-hex>",
    "runner_code_schema": "gwm-cglr-source-code-manifest-v1",
    "h2_source_schema": "gwm-cglr-h2-source-manifest-v1",
    "runner_code_role": "cglr_runner_code",
    "h2_source_role": "h2_source_manifest"
  }
}
```

The angle-bracket values above are template notation only. A materialized
artifact must contain no angle brackets, placeholders, descriptive substitutes,
or non-string values. All three hash fields are lowercase `[0-9a-f]{64}`.
The owner review binds this tuple as a whole; a partial tuple or a tuple copied
from fixture input is not an owner review.

The tuple has three independent identity subjects:

* `runner_code_manifest_sha256`: recomputed from the non-recursive code-root
  source manifest defined by R81; it binds executable runner code only.
* `h2_source_manifest_sha256`: recomputed from the exact
  `input_root/h2_source_manifest.json` subject defined by R83; it binds the
  producer/boundary provenance declaration only.
* `h2_boundary_artifact_sha256`: recomputed from the exact bytes of the
  role-allowed `input_root/boundary_artifact.json`.

The first two hashes must be unequal. The schemas, role names, canonical roots,
and manifest paths must be distinct and fixed by the protocol:

| identity | schema | role | canonical root/path |
|---|---|---|---|
| runner code | `gwm-cglr-source-code-manifest-v1` | `cglr_runner_code` | read-only `code_root/source_code_manifest.json` |
| H2 source | `gwm-cglr-h2-source-manifest-v1` | `h2_source_manifest` | read-only `input_root/h2_source_manifest.json` |
| H2 boundary | boundary artifact bytes | `h2_boundary_artifact` | read-only `input_root/boundary_artifact.json` |

Cross-labeling is a hard failure: a code manifest presented at the H2 path, an
H2 source manifest presented as the code manifest, a role/schema/root/path
combination copied from the other identity, or a tuple whose first two hashes
are equal is rejected. Filesystem alias, symlink, traversal, hard-link, socket,
and unlisted-path checks from R79/R81 still apply; the inequality check is also
performed on content hashes so disjoint roots alone are not treated as proof of
identity separation.

## Phase-0 owner and type gate

Phase 0 runs after the bootstrap code-manifest check and before phase 1/2
scientific materialization. It reads only the owner/review/protocol roles; it
does not open `h2_source_manifest.json`, `h2_packet.json`, or
`boundary_artifact.json`. It must reject before any fixture-context extraction
or H2-dependent hash operation when:

1. `review_artifact.manifest_identity` is missing, duplicated, malformed, or
   contains a marker, placeholder, uppercase/non-hex hash, wrong JSON type, or
   unknown field that changes the tuple;
2. the owner review status/hash does not bind the exact canonical tuple bytes;
3. any required schema, role, root, or path is missing, cross-labeled, or not
   the fixed value in this memo;
4. `runner_code_manifest_sha256 == h2_source_manifest_sha256`;
5. the tuple's runner-code hash does not equal the already independently
   recomputed bootstrap code identity, or the tuple is substituted by a value
   from `fixture.json`, `h2_packet.json`, or a non-owner input role.

Code identity failures remain `OWNER_REVIEW_REQUIRED` or `REJECT_FIXTURE`.
They do not become `H2_UNIDENTIFIABLE`, and phase 0 never uses the tuple to
authorize producer-source access.

## Phase-2 independent recomputation and H2 comparison

After phase 1 materialization, phase 2 opens only the role-allowed H2 source,
packet, and boundary files. It independently recomputes:

```text
code_hash       = bootstrap recomputed source_code_manifest subject
h2_source_hash  = h2_source_manifest subject
boundary_hash   = boundary_artifact.json exact bytes
```

It then requires all comparisons below to pass:

* `code_hash == manifest_identity.runner_code_manifest_sha256`;
* `h2_source_hash == manifest_identity.h2_source_manifest_sha256`;
* `boundary_hash == manifest_identity.h2_boundary_artifact_sha256`;
* `h2_packet.source_manifest_sha256 == h2_source_hash`;
* `h2_packet.boundary_artifact_sha256 == boundary_hash`;
* `code_hash != h2_source_hash`;
* the H2 source schema/role/path and the boundary role/path equal the fixed
  protocol values and cannot be cross-labeled.

Any missing, marker-valued, malformed, stale, role-disallowed, recomputation,
tuple, packet, inequality, or cross-label failure returns
`H2_UNIDENTIFIABLE`. This return is emitted before extracting
`fixture_context_paths`, calculating `fixture_context_sha256`, computing any
base/rule/arm hash, or scoring an arm. A passing H2 gate is the only route to
phase 3 hash verification and phase 4 arm scoring.

## Acceptance and terminal condition

The owner must review the tuple schema, exact bytes/hash binding, fixed role/root
table, phase-0 precedence, and phase-2 recomputation comparisons as one change.
Until that review and a future implementation are available, the proposed
runner command remains `NO_COMMAND_AVAILABLE`; no synthetic fixture execution,
real C8 access, replay, GPU/Slurm submission, receipt update, or validation-flag
change is permitted.

Project flags remain `new_method_validated=false` and
`novelty_authorization=NONE`.

**R85 status: MANIFEST-IDENTITY TUPLE CORRECTION / FUTURE-ONLY / NO EXECUTION.**
