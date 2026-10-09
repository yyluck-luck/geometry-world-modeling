# R87 canonical owner-hash correction for the future CGLR runner

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only correction to R85/R86. No runner, fixture, review artifact,
manifest, H2 packet, boundary artifact, receipt, real C8 input, GPU/Slurm job,
or validation flag was created, opened, or modified.

## Decision and boundary

Apply only R86's minimal serialization/binding fix. The owner-reviewed
`manifest_identity` is now a single canonical JSON object whose bytes and owner
hash are unambiguous. This does not authorize producer-source access, synthetic
fixture execution, replay, or real-data scoring. Every path and artifact below
is proposed and absent.

`NO_COMMAND_AVAILABLE` remains in force until an owner-reviewed implementation
passes these gates. Project flags remain `new_method_validated=false` and
`novelty_authorization=NONE`.

## Strict JSON input contract

`review_artifact.json` must be raw UTF-8 JSON. Parsing is strict and rejects:

* invalid UTF-8, a UTF-8 byte-order mark, comments, trailing bytes, NaN,
  Infinity, or any non-standard JSON token;
* duplicate object keys at any depth, including duplicate `manifest_identity`,
  duplicate tuple fields, or duplicate `owner_gate` fields;
* unknown or alias fields that could provide a second identity or owner hash.

There is exactly one JSON Pointer `/manifest_identity` at the top level. It is
an object with exactly these seven fields and no others:

```text
runner_code_manifest_sha256
h2_source_manifest_sha256
h2_boundary_artifact_sha256
runner_code_schema
h2_source_schema
runner_code_role
h2_source_role
```

The three hash fields are strings matching lowercase `[0-9a-f]{64}`. The four
schema/role strings are the fixed R85 values. A second tuple in an array,
`fixture.json`, `h2_packet.json`, or another JSON Pointer is not accepted as an
alias. Any missing, duplicate, unknown, marker, placeholder, wrong-type,
uppercase, or alternate string representation is `REJECT_FIXTURE` before H2
files are opened.

## Canonical owner-hash subject

The only owner-review hash is `owner_gate.review_artifact_sha256`. Its supplied
self field is removed from the parsed review artifact before hashing; no other
field is removed, projected, reordered by hand, or taken from another role.

Define the subject exactly as:

```text
owner_subject = canonical_json(review_artifact
                               with exactly
                               /owner_gate/review_artifact_sha256 removed)
review_hash   = SHA256(owner_subject)
```

`canonical_json` is a deterministic UTF-8 encoding with all of these rules:

1. recursively sort every object key by Unicode code point;
2. emit separators `,` and `:` with no insignificant whitespace;
3. emit strings using one JSON escaping form (UTF-8 source text, no alternate
   escaped/unescaped spelling for the same character);
4. emit only finite JSON numbers, using one shortest round-trippable decimal
   representation; reject `-0`, exponent aliases, excess leading zeros, NaN,
   and Infinity;
5. preserve array order and preserve the exact seven tuple field values;
6. encode the final text as UTF-8 with no BOM and no trailing bytes.

The implementation must recompute `review_hash` from these bytes and compare it
with the supplied lowercase 64-hex `owner_gate.review_artifact_sha256` and the
owner-gate status/protocol fields. The self-hash field is never included in its
own subject, so no recursive hash is permitted. A supplied hash is never used
as an input to recompute itself.

## Phase-0 checks and precedence

After the independent code-root bootstrap check, phase 0 performs, in order:

1. strict UTF-8 parse, duplicate-key rejection, fixed `/manifest_identity`
   location, exact seven-field/type/value check, and marker/alias rejection;
2. owner-gate status/protocol validation and canonical `review_hash`
   recomputation from the self-field-removed artifact;
3. comparison of tuple
   `runner_code_manifest_sha256` with the bootstrap code identity, and the
   required inequality with `h2_source_manifest_sha256`.

Any failure returns `OWNER_REVIEW_REQUIRED` for missing/stale owner binding or
`REJECT_FIXTURE` for malformed/schema/hash/alias input. Phase 0 does not open
`h2_source_manifest.json`, `h2_packet.json`, or `boundary_artifact.json` and
does not extract fixture context or compute H2-dependent hashes.

## Phase-2 checks and H2 precedence

Only after phase 1 materialization, phase 2 opens the role-allowed H2 source,
packet, and boundary files. It independently recomputes code, H2-source, and
boundary identities and requires:

```text
code_hash      == manifest_identity.runner_code_manifest_sha256
h2_source_hash == manifest_identity.h2_source_manifest_sha256
boundary_hash  == manifest_identity.h2_boundary_artifact_sha256
h2_packet.source_manifest_sha256   == h2_source_hash
h2_packet.boundary_artifact_sha256 == boundary_hash
code_hash != h2_source_hash
```

The fixed H2 schema/role/root/path labels are checked again; cross-labeling,
alias paths, replacement files, markers, malformed values, or any tuple/H2
packet mismatch is `H2_UNIDENTIFIABLE`. This result is emitted before
`fixture_context_paths`, `fixture_context_sha256`, base/rule/arm hashes, or arm
score. A phase-2 H2 failure cannot downgrade a phase-0 owner/code failure or
authorize a manifest substitution.

## Terminal condition

The future runner remains unimplemented and `NO_COMMAND_AVAILABLE` until an
owner accepts this exact canonical-subject contract and an implementation
passes it. No fixture execution, real C8 access, replay, GPU/Slurm submission,
receipt update, or validation-flag change is permitted.

**R87 status: CANONICAL OWNER-HASH CORRECTION / FUTURE-ONLY / NO EXECUTION.**
