# R91 owner/H2 readiness and substitution-attack matrix

Date: 2026-09-24 (Asia/Shanghai)  
Scope: read-only readiness inspection and adversarial design matrix. No runner,
fixture, owner artifact, H2 packet, boundary artifact, real C8 input, replay,
GPU/Slurm job, receipt, or validation flag was created, opened, or modified.

## Readiness result

**NO_COMMAND_AVAILABLE.** The exact role-bound artifacts required by R90 are
absent from the repository:

| Required artifact | Expected role | Inspection result |
|---|---|---|
| `review_artifact.json` with `OWNER_ACCEPTED` and the seven-field `manifest_identity` | owner/review input | **ABSENT** |
| `source_code_manifest.json` for the dedicated runner | immutable code root | **ABSENT** |
| `h2_source_manifest.json` | independently reviewed producer/boundary identity | **ABSENT** |
| `h2_packet.json` with measured R70/R72 fields and `status=PASS` | H2 input | **ABSENT** |
| `boundary_artifact.json` | H2 boundary input | **ABSENT** |
| canonical `fixture.json` with computed envelope and ten access-matched arms | synthetic input | **ABSENT** |
| source-pinned CGLR runner and supported CPU command | executable entry point | **ABSENT** |

The S131 directory contains only `work/S131_CGLR_contract/episode_schema.json`
and `DESIGN_AND_PREREGISTRATION.md`; its schema is `CONTRACT_ONLY`, not a
runner or executable fixture. The earlier R74 command discovery independently
found no R62/R70/R72 runner, owner artifact, measured H2 packet, or supported
command. Existing generic synthetic checkers and unrelated runner snapshots are
not substitutions for this protocol and were not executed.

The required next state is therefore still `NO_COMMAND_AVAILABLE`, with
`OWNER_REVIEW_REQUIRED`/`H2_UNIDENTIFIABLE` reserved for a future attempt after
the corresponding inputs exist. No real C8, target RGB/depth, checkpoint,
learned weight, GPU, Slurm, existing receipt, or validation flag may be opened.

## Substitution-attack matrix

The matrix assumes the passed R90 contract and names the earliest rejection
phase. “Stop” means no later phase, context extraction, hash-domain creation,
arm score, or output receipt is permitted.

| Attack scenario | Earliest detection | Required result | Stop condition |
|---|---|---|---|
| Replace `h2_source_manifest.json` bytes while leaving owner tuple and H2 packet unchanged | Phase 2 independent H2-source recomputation | `H2_UNIDENTIFIABLE` | Stop before `fixture_context_paths`, context/base/rule/arm hashes, and scoring |
| Replace `boundary_artifact.json` bytes while leaving tuple/packet unchanged | Phase 2 boundary-byte hash comparison | `H2_UNIDENTIFIABLE` | Stop before all H2-dependent hashes and arm score |
| Replace source and boundary, then edit tuple/packet but not owner review hash | Phase 0 canonical owner-subject hash | `REJECT_FIXTURE` (or `OWNER_REVIEW_REQUIRED` if owner status/hash is missing/stale) | Stop before any H2 file open |
| Present code manifest at H2 path, or H2 source manifest at code path | Bootstrap/phase-0 fixed schema, role, root, and path checks; code hash comparison | `REJECT_FIXTURE` or `OWNER_REVIEW_REQUIRED` for stale code binding | Stop before H2 phase; no cross-role fallback |
| Symlink, hard-link, traversal, alias, socket, unlisted path, or output-root path substituted for a role file | Four-root audit hook before role read | `REJECT_FIXTURE` / boundary violation abort | Stop before input bytes are consumed |
| Replay an older valid owner artifact against a changed runner code manifest | Phase 0 recomputed bootstrap code hash vs tuple and owner subject | `OWNER_REVIEW_REQUIRED` or `REJECT_FIXTURE` | Stop before H2 open and materialization |
| Replay an older valid owner artifact against changed H2 source/boundary bytes | Phase 2 independent H2 recomputation vs tuple/packet | `H2_UNIDENTIFIABLE` | Stop before context/hash/arm operations |
| Duplicate top-level `manifest_identity`, duplicate tuple key, or duplicate `owner_gate.review_artifact_sha256` | Strict UTF-8 parser before phase-0 field access | `REJECT_FIXTURE` | Stop before owner hash and before H2 files open |
| Add a second tuple under an array, alias pointer, fixture, or H2 packet | Phase-0 exact top-level pointer/exact-seven-field and alias scan | `REJECT_FIXTURE` | Stop before owner hash/H2 |
| Use invalid UTF-8, BOM, trailing bytes, comments, or unpaired surrogate | Strict ingress parser | `REJECT_FIXTURE` | Stop before canonicalization and owner hash |
| Use a valid alternate string escape that canonicalizes to the same scalar value | `canonical_json_v2` canonicalization | Accepted only if canonical owner hash and all identity checks still match; no semantic substitution occurs | Continue only through normal gates; no alternate bytes enter owner subject |
| Use `\\/`, uppercase `\\u`, non-fixed control escapes, or surrogate escapes in canonical output | `canonical_json_v2` fixed-string spelling check | `REJECT_FIXTURE` | Stop before owner hash |
| Use exponent number, `NaN`, `Infinity`, `-0`, leading-zero integer, trailing point, or trailing fractional zero in canonical output | Arbitrary-precision decimal ingress/canonical-number check | `REJECT_FIXTURE` | Stop before owner hash |
| Use `1.00` or `0.0100` as input | Canonical decimal normalization | Canonicalizes to `1`/`0.01`; accepted only if resulting owner hash is the reviewed one | No substitution: canonical bytes are unique; continue normal owner/H2 gates |
| Change any schema/role/root/path label while preserving hashes | Phase-0 fixed label check, repeated in phase 2 for H2 | `REJECT_FIXTURE` (phase 0) or `H2_UNIDENTIFIABLE` (phase 2) | Stop at the detecting phase; no fallback to another role |

## Readiness stop rules

Until all absent artifacts in the readiness table are independently supplied,
owner-reviewed, and source-pinned, a command cannot be selected from generic
scripts. A future attempt must stop at the first applicable status:

* missing runner, fixture, owner artifact, or H2 artifacts: `NO_COMMAND_AVAILABLE`;
* missing/stale owner status or review hash: `OWNER_REVIEW_REQUIRED`;
* malformed tuple, canonical subject, role/path, or code identity: `REJECT_FIXTURE`;
* any missing, replaced, stale, or mismatched H2 source/packet/boundary: `H2_UNIDENTIFIABLE`;
* any real-data, network, target-sensor, learned-weight, GPU, Slurm, receipt, or
  flag access attempt: abort as a boundary violation before input read.

**R91 status: READINESS CHECK COMPLETE / NO_COMMAND_AVAILABLE / DESIGN-ONLY.**
Project flags remain `new_method_validated=false` and
`novelty_authorization=NONE`.
