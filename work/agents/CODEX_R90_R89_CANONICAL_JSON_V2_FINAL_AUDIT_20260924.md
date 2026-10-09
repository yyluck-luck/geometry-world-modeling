# R90 final hostile audit of the R89 canonical_json_v2 contract

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only audit. No runner, fixture, review artifact, manifest, H2
packet, boundary artifact, receipt, real C8 input, GPU/Slurm job, or validation
flag was created, opened, or modified.

## Decision

**PASS.** R89 closes the R88 serialization ambiguity and preserves the R85
identity and H2 precedence contract. No concrete parser, owner-subject, or
manifest-substitution flaw remains in the design. This is an audit pass only;
it does not authorize implementation or execution.

## Audit results

* **Bytes and ingress:** strict UTF-8, no BOM, comments, trailing bytes,
  non-standard tokens, or duplicate object keys at any depth. The result is
  emitted as UTF-8 with no BOM or trailing bytes.
* **Tuple uniqueness:** there is exactly one top-level `/manifest_identity`
  object with exactly seven fixed fields. Missing, duplicate, unknown, marker,
  wrong-type, alternate, or alias fields are rejected before H2 files open.
  A second tuple in an array or another role is not accepted.
* **String determinism:** only Unicode scalar values are accepted; quote and
  backslash have fixed escapes, controls use the specified short/lowercase
  `\\u00xx` forms, slash escaping is forbidden, and unpaired surrogates are
  rejected. Each accepted scalar has one canonical spelling.
* **Number determinism:** arbitrary-precision decimal parsing rejects
  non-finite values, negative zero, leading-zero integers, and exponent tokens.
  Canonical output is one normalized plain-decimal spelling with no exponent,
  `+`, trailing point, or trailing fractional zeros.
* **Structure and bytes:** object keys are recursively sorted by Unicode code
  point; array order is preserved; separators are exactly `,` and `:` with no
  whitespace. These rules determine one `canonical_json_v2` byte string.
* **Self-hash subject:** only `/owner_gate/review_artifact_sha256` is removed;
  duplicate-key rejection makes the removal unique, and the lower-case 64-hex
  SHA-256 is compared to those exact bytes without recursive self-inclusion.
* **Phase ordering:** phase 0 performs parse, tuple, owner-hash, and code
  checks before opening H2 artifacts or extracting context. Phase 2 independently
  recomputes code/source/boundary hashes and compares them with the tuple and
  H2 packet. Any H2 mismatch returns `H2_UNIDENTIFIABLE` before context,
  hash-domain, or arm-score operations.

## Substitution and precedence conclusion

The owner hash cannot silently omit or replace a tuple field because its subject
is the complete self-field-removed artifact under the fixed serializer. The
code/H2 identities cannot silently substitute because each is independently
recomputed, code and H2 hashes must differ, schemas/roles/roots/paths are fixed,
and the packet must match the H2 source and boundary hashes. Phase-0 owner/code
failures remain `OWNER_REVIEW_REQUIRED` or `REJECT_FIXTURE`; they are not
downgraded by a later H2 result.

## Terminal condition

R89 is owner-reviewable as a design contract, but the future runner and command
remain absent: `NO_COMMAND_AVAILABLE`. No synthetic fixture execution, real C8
access, replay, GPU/Slurm submission, receipt update, or validation-flag change
is authorized. Project flags remain `new_method_validated=false` and
`novelty_authorization=NONE`.

**R90 status: PASS / FINAL CANONICAL_JSON_V2 AUDIT / DESIGN-ONLY.**
