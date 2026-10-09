# R86 final hostile audit of the R85 manifest-identity tuple

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only audit. No runner, fixture, review artifact, manifest, H2
packet, boundary artifact, receipt, real C8 input, GPU/Slurm job, or validation
flag was created, opened, or modified.

## Decision

**REVISE ONCE before owner acceptance.** R85 closes the content-substitution
gap at the field and recomputation level, but its phrase “exact canonical tuple
bytes” is not an executable serialization or owner-hash contract. Without a
strict duplicate-key and canonical-subject rule, two JSON byte streams can parse
to different tuples or an implementation can bind the owner review to a
representation that omits/reorders `manifest_identity`.

## Checks that pass

* R85 has one required `manifest_identity` object with all three hashes and the
  fixed schema/role values.
* The first two identities must be unequal, and phase 0 compares the tuple's
  runner-code hash with the independently checked bootstrap identity.
* Phase 2 independently recomputes code, H2-source, and boundary identities and
  compares each with both the tuple and the H2 packet before any
  `fixture_context`, hash, or arm score operation.
* Cross-role schema/root/path labels, marker values, aliases, links, traversal,
  hard links, sockets, and unlisted paths remain rejection conditions.
* Code failures remain owner/schema failures; H2 failures return
  `H2_UNIDENTIFIABLE` with the required precedence.

## Remaining concrete ambiguity

R85 requires that the owner review bind “the exact canonical tuple bytes” and
rejects an unknown field that changes the tuple, but it does not define:

1. duplicate-key rejection (including duplicate `manifest_identity` members);
2. the fixed JSON Pointer and exact seven-key set for the tuple subject;
3. the canonical serialization used by `owner_gate.review_artifact_sha256`.

An implementation could therefore accept a parser-dependent duplicate key,
bind a review hash over a projection that silently drops one tuple field, or
hash a noncanonical byte ordering. That leaves a hidden owner-binding
substitution even though the hash recomputation comparisons are otherwise
correct.

## One minimal correction

Add this strict subject rule to R85 and require it at phase 0:

```text
review_artifact.json is UTF-8 JSON parsed with duplicate-key rejection.
There is exactly one top-level member at JSON Pointer /manifest_identity.
That object contains exactly the seven R85 fields (no missing, duplicate,
unknown, or alias fields). Its owner-bound subject bytes are

  canonical_json(review_artifact with the supplied
  owner_gate.review_artifact_sha256 field removed)

where canonical_json is UTF-8 JSON with recursively sorted object keys,
separators ',' and ':', no insignificant whitespace, no NaN/Inf, and no
alternate numeric or string encodings. The resulting subject is the sole input
to the recomputed owner_gate.review_artifact_sha256.
```

Phase 0 must perform duplicate-key/UTF-8/canonical-subject validation before
reading H2 files and reject any mismatch as `OWNER_REVIEW_REQUIRED` or
`REJECT_FIXTURE`. The tuple field checks, code/H2 inequality, fixed role/root/
path checks, and phase-2 independent recomputation then operate on this one
canonical parsed object. No second tuple from `fixture.json`, `h2_packet.json`,
or an alternate JSON pointer is permitted.

This is a serialization/binding clarification only; it does not authorize
producer-source access or change R85's H2 precedence.

## Terminal condition

Until this canonical-subject rule is owner-reviewed and implemented, the
runner remains unimplemented and the command remains `NO_COMMAND_AVAILABLE`.
No synthetic fixture, real C8 access, replay, GPU/Slurm submission, receipt
update, or validation-flag change is authorized. Project flags remain
`new_method_validated=false` and `novelty_authorization=NONE`.

**R86 status: REVISE ONCE / FINAL MANIFEST-IDENTITY AUDIT / DESIGN-ONLY.**
