# R88 final hostile audit of the R87 canonical owner hash

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only audit. No runner, fixture, review artifact, manifest, H2
packet, boundary artifact, receipt, real C8 input, GPU/Slurm job, or validation
flag was created, opened, or modified.

## Decision

**REVISE ONCE before owner acceptance.** R87 closes pointer uniqueness,
duplicate-key handling, self-hash removal, owner-subject scope, and phase
precedence. One parser-level ambiguity remains: “one JSON escaping form” and
“shortest round-trippable decimal” still allow implementation-dependent choices
for control/unicode escapes and numeric serialization. An owner hash must not
depend on the language JSON library.

## Checks that pass

* Raw UTF-8, BOM, trailing-byte, non-standard-token, and duplicate-key rejection
  are explicit.
* `/manifest_identity` is unique and top-level; it has exactly the seven R85
  fields, fixed values, and no alias tuple.
* `owner_gate.review_artifact_sha256` is the sole owner hash, with exactly that
  self field removed from the subject and no recursive self-hash.
* Phase 0 validates parsing, tuple, owner subject, code identity, and code/H2
  inequality before H2 files or H2-dependent hashes are opened.
* Phase 2 independently recomputes code/source/boundary identities, compares
  them with the tuple and H2 packet, and returns `H2_UNIDENTIFIABLE` before
  context, hash, or arm operations on any H2 mismatch.

## Remaining concrete ambiguity

R87 does not say whether a non-ASCII scalar is emitted literally or as `\\uXXXX`,
which escape is used for `/`, whether control escapes use short forms or
lowercase `\\u00xx`, or how unpaired surrogates are handled. Its “shortest
round-trippable decimal” also depends on the host number type and serializer;
`1`, `1.0`, and `1e0` can be treated differently by different runtimes.

Thus two implementations can accept the same valid review artifact, produce
different canonical bytes, and disagree on `review_artifact_sha256` without
violating the current prose.

## One minimal correction

Replace R87's escaping/number prose with one normative `canonical_json_v2`
profile used for every owner-subject hash:

```text
Strings: emit Unicode scalar values directly as UTF-8 except `"`, `\\`, and
U+0000..U+001F. Use only `\\"`, `\\\\`, `\\b`, `\\f`, `\\n`, `\\r`, `\\t`, and
lowercase-hex `\\u00xx` for the remaining controls. Never escape `/`; reject
unpaired UTF-16 surrogates. This is the sole accepted string spelling.

Numbers: parse with arbitrary-precision decimal, reject NaN/Infinity/-0, then
emit exact plain decimal with no exponent: one `0` or a nonzero integer with no
leading zeros, optional fractional digits with trailing zeros removed, and no
trailing decimal point. (For a value below one, emit `0.` followed by the
necessary zeros and significant digits.) This is the sole accepted number
spelling; no exponent token is accepted in canonical output.
```

Keep R87's recursive Unicode-code-point key ordering, `,`/`:` separators, array
order, duplicate-key rejection, UTF-8/no-BOM final encoding, and removal of
only `/owner_gate/review_artifact_sha256`. Phase 0 must recompute the owner hash
with `canonical_json_v2` and reject any alternate spelling before H2 opens;
phase 2 keeps the existing independent identity comparisons and
`H2_UNIDENTIFIABLE` precedence.

This correction only makes the owner-subject bytes deterministic. It does not
authorize producer-source access, fixture execution, replay, GPU/Slurm, receipt
updates, or validation-flag changes.

## Terminal condition

Until this normative serialization profile is owner-reviewed and implemented,
the runner remains unimplemented and the command remains `NO_COMMAND_AVAILABLE`.
Project flags remain `new_method_validated=false` and
`novelty_authorization=NONE`.

**R88 status: REVISE ONCE / FINAL CANONICAL-HASH AUDIT / DESIGN-ONLY.**
