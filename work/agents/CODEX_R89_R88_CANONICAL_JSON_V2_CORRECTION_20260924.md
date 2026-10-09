# R89 canonical_json_v2 correction for the future CGLR runner

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only correction to R88. No runner, fixture, review artifact,
manifest, H2 packet, boundary artifact, receipt, real C8 input, GPU/Slurm job,
or validation flag was created, opened, or modified.

## Decision and boundary

Apply only R88's normative serialization correction. The owner-hash subject now
has one deterministic byte representation independent of the host JSON library.
This contract does not authorize producer-source access, synthetic execution,
replay, or real-data scoring. All artifacts and paths below remain proposed and
absent.

`NO_COMMAND_AVAILABLE` remains in force. Project flags remain
`new_method_validated=false` and `novelty_authorization=NONE`.

## canonical_json_v2 byte contract

`canonical_json_v2(x)` returns a byte string, not a language-native string:

1. Parse the source as strict UTF-8 JSON with no BOM, comments, trailing bytes,
   non-standard tokens, or duplicate object keys at any depth.
2. Require every string to contain Unicode scalar values only; reject unpaired
   UTF-16 surrogates.
3. Recursively sort object keys by Unicode code point; preserve array order.
4. Emit object/array separators exactly `,` and `:` with no whitespace.
5. Emit the resulting JSON text as UTF-8 with no BOM and no trailing bytes.

The owner subject is exactly:

```text
owner_subject_bytes = canonical_json_v2(
    review_artifact with exactly /owner_gate/review_artifact_sha256 removed)
```

No other field is removed, projected, copied from another role, or allowed to
enter a second subject. `owner_gate.review_artifact_sha256` is the lowercase
64-hex SHA-256 of these exact bytes; its supplied value is never included in
the bytes it hashes.

## Fixed string spelling

For each string, emit Unicode scalar values directly as UTF-8 except:

* `"` is emitted as `\\"`;
* `\\` is emitted as `\\\\`;
* U+0008, U+000C, U+000A, U+000D, and U+0009 are emitted only as `\\b`, `\\f`,
  `\\n`, `\\r`, and `\\t`, respectively;
* every other U+0000..U+001F control is emitted as lowercase-hex `\\u00xx`.

`/` is never escaped. No other `\\u` escape, uppercase hex digit, alternate
short escape, or surrogate escape is accepted in canonical output. This gives
each accepted scalar exactly one output spelling.

## Fixed number spelling

Numbers are parsed as arbitrary-precision decimal values, never binary floats.
The input number token must be finite, contain no `NaN`/`Infinity`, have no
exponent marker, and must not represent negative zero. A number with an
exponent, `-0`, a leading-zero integer, or a non-finite value is rejected before
owner hashing.

Canonical output is plain decimal only:

* zero is exactly `0`;
* a nonzero integer has an optional leading `-` and no leading zeros;
* a fractional value has one integer digit sequence, a single `.`, and a
  fractional sequence with trailing zeros removed;
* omit the decimal point when the fractional sequence becomes empty;
* values between -1 and 1 use `0.` or `-0.` followed by the significant digits;
* no exponent, `+` sign, `-0`, leading-zero integer, trailing decimal point,
  or trailing fractional zero may appear in canonical bytes.

Thus `1.00` canonicalizes to `1`, `0.0100` to `0.01`, and `-0.0` is rejected.
The canonical output has one plain-decimal spelling for every accepted value.

## Phase-0 owner-hash gate

After the independent code-root bootstrap check, phase 0 performs these checks
before opening any H2 file:

1. strict UTF-8/no-BOM parse, duplicate-key rejection, exact top-level
   `/manifest_identity` pointer, exact seven-field tuple, marker/alias/type
   rejection, and the canonical string/number ingress rules above;
2. `canonical_json_v2` recomputation of `owner_subject_bytes` after removing
   only `/owner_gate/review_artifact_sha256`, followed by SHA-256 comparison to
   the supplied owner hash and owner-gate status/protocol;
3. comparison of the tuple's runner-code hash with the bootstrap code identity
   and enforcement of `runner_code_manifest_sha256 != h2_source_manifest_sha256`.

Missing/stale owner binding returns `OWNER_REVIEW_REQUIRED`; malformed tuple,
canonicalization, hash, alias, or code identity input returns
`REJECT_FIXTURE`. Phase 0 does not read `h2_source_manifest.json`,
`h2_packet.json`, or `boundary_artifact.json`, and does not extract fixture
context or calculate H2-dependent hashes.

## Phase-2 H2 gate and precedence

Only after phase 1 materialization, phase 2 opens the role-allowed H2 source,
packet, and boundary files. It independently recomputes code, H2-source, and
boundary hashes and requires equality with both `manifest_identity` and the H2
packet, plus the fixed schema/role/root/path labels and code/H2 inequality.

Missing, marker-valued, malformed, role-disallowed, replaced, cross-labeled,
or hash-mismatched H2 artifacts return `H2_UNIDENTIFIABLE`. This result is
returned before `fixture_context_paths`, `fixture_context_sha256`, any
base/rule/arm hash, or arm score. A phase-2 failure cannot downgrade a phase-0
owner/code failure or authorize source-manifest substitution.

## Terminal condition

The future runner remains unimplemented and `NO_COMMAND_AVAILABLE` until an
owner accepts this exact `canonical_json_v2` contract and an implementation
passes it. No fixture execution, real C8 access, replay, GPU/Slurm submission,
receipt update, or validation-flag change is permitted.

**R89 status: CANONICAL_JSON_V2 CORRECTION / FUTURE-ONLY / NO EXECUTION.**
