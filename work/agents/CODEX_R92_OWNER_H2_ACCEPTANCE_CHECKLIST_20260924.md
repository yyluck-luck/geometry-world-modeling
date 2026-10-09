# R92 owner/H2 acceptance checklist for the first executable step

Date: 2026-09-24 (Asia/Shanghai)  
Scope: readiness decision and owner checklist only. No runner, fixture, owner
artifact, H2 packet, boundary artifact, real C8 input, replay, GPU/Slurm job,
receipt, or validation flag was created, opened, or modified.

## Current decision

**NO_COMMAND_AVAILABLE.** R91 found none of the role-bound execution artifacts
and no supported CGLR runner. S131 is explicitly `CONTRACT_ONLY` with
`new_method_validated=false` and `novelty_authorization=NONE`; R70/R89 define
acceptance contracts, not executable inputs. The first executable step, if all
gates later pass, is a synthetic CPU conformance run only.

## Ranked prerequisites

The order below is dependency order for constructing an owner-reviewable packet,
followed by the execution gate. “Evidence” names the contract that the owner
must inspect; “owner action” is a missing artifact or review action, not an
authorization already granted.

### 0. Freeze scope and reviewer

* **Evidence:** `work/S131_CGLR_contract/episode_schema.json:2-5,23-35`,
  `work/S131_CGLR_contract/DESIGN_AND_PREREGISTRATION.md:5-7,98-102`,
  `work/agents/CODEX_R70_R66_R68_CANONICAL_H2_PACKET_CORRECTION_20260924.md:87-126`,
  `work/agents/CODEX_R89_R88_CANONICAL_JSON_V2_CORRECTION_20260924.md:79-117`.
* **Owner action:** appoint an independent reviewer and record the exact scope
  `synthetic_cpu_conformance_only`, latest R70 manifest chain, R89 serializer,
  and no-real-data boundary. Do not treat this acknowledgement as acceptance.
* **Stop:** any scope drift, missing reviewer, or stale protocol is
  `OWNER_REVIEW_REQUIRED`; S131 remains contract-only.

### 1. Source-pin the dedicated runner and code manifest

* **Evidence:** R91 readiness table and R74 discovery
  (`work/agents/CODEX_R91_OWNER_H2_READINESS_SUBSTITUTION_MATRIX_20260924.md:10-28`,
  `work/agents/CODEX_R74_SYNTHETIC_CPU_COMMAND_DISCOVERY_20260924.md:8-23`).
* **Owner action:** implement or supply a dedicated R62/R70/R89 runner under
  the closed stdlib/code/input/output roots; freeze its source; generate the
  non-recursive `source_code_manifest.json` and its lowercase
  `runner_code_manifest_sha256`; document the supported CPU entry point.
* **Stop:** absent runner or code manifest is `NO_COMMAND_AVAILABLE`; stale or
  mismatched code identity is `OWNER_REVIEW_REQUIRED`/`REJECT_FIXTURE` before
  H2 files open. Generic synthetic scripts cannot substitute.

### 2. Materialize the canonical synthetic fixture

* **Evidence:** `work/S131_CGLR_contract/episode_schema.json:6-21`,
  `work/S131_CGLR_contract/DESIGN_AND_PREREGISTRATION.md:24-72`,
  R91 matrix rows for tuple/fixture substitution.
* **Owner action:** create one immutable `fixture.json` with the four disjoint
  camera roles, sealed target references, computed geometry/visibility envelope,
  event and threshold fields, all ten typed arms, access-matched inputs, and
  no target RGB/depth or post-state leakage. Expected fields remain excluded
  from computed/hash domains.
* **Stop:** missing fixture is `NO_COMMAND_AVAILABLE`; schema, marker, computed,
  arm, leakage, or hash failure is `REJECT_FIXTURE`.

### 3. Create the measured H2 boundary artifact

* **Evidence:** R70 boundary requirements
  (`work/agents/CODEX_R70_R66_R68_CANONICAL_H2_PACKET_CORRECTION_20260924.md:47-73`).
* **Owner action:** independently record exact `T_c2w`, `p_frame`, `X_world`,
  units, frame declaration, operation direction, and both recomputed vectors;
  measure `err_forward`, `err_inverse`, and their maximum. Hash the exact
  `boundary_artifact.json` bytes.
* **Stop:** missing, stale, mixed-direction, malformed, or above-threshold
  boundary evidence is `H2_UNIDENTIFIABLE`; do not replace it with a helper
  algebra check.

### 4. Create the independent H2 source manifest

* **Evidence:** R82/R83 split as recorded in
  `work/agents/CODEX_R83_R81_CODE_H2_MANIFEST_SPLIT_20260924.md`, and R91 rows
  15-19.
* **Owner action:** write `h2_source_manifest.json` containing the fixed H2
  schema, producer/boundary provenance entries, and its independently
  recomputed subject hash. It must bind the measured producer/boundary
  declaration, never the runner code manifest; listed producer paths are
  identity records only and are not opened by the synthetic runner.
* **Stop:** absent or role/path/schema/hash mismatch is `H2_UNIDENTIFIABLE` in
  phase 2; code/H2 cross-labeling is `REJECT_FIXTURE`/`OWNER_REVIEW_REQUIRED`
  at the earlier code gate.

### 5. Produce and independently measure the canonical H2 packet

* **Evidence:** R70 exact fields and entry conditions
  (`work/agents/CODEX_R70_R66_R68_CANONICAL_H2_PACKET_CORRECTION_20260924.md:22-45,114-126`).
* **Owner action:** create `h2_packet.json` with `pose_name=T_c2w`,
  `pose_direction=camera_to_world`, exact formulas, numeric
  `max_abs_error=max(err_forward,err_inverse)`, `error_threshold=1e-6`, exact
  lowercase source/boundary hashes, and `status=PASS`.
* **Stop:** missing, marker-valued, stale, direction-conflicting, nonnumeric,
  or above-threshold H2 returns `H2_UNIDENTIFIABLE` before fixture context,
  hash extraction, or arm score.

### 6. Assemble and owner-accept the review artifact/identity tuple

* **Evidence:** R70 owner gate (`...R70...:87-112`), R89 phase-0 owner hash
  (`...R89...:79-97`), and R91 tuple rows 15-21.
* **Owner action:** after hashes from steps 1-5 exist, create exactly one
  owner-bound `review_artifact.json` with `OWNER_ACCEPTED`, the latest manifest
  chain, and the R85/R89 seven-field `manifest_identity` binding code, H2
  source, and boundary hashes. Recompute `review_artifact_sha256` using the
  exact R89 `canonical_json_v2` subject (remove only its self-hash field), and
  have the independent reviewer verify the tuple and fixture subject.
* **Stop:** absent/stale owner status or review hash is
  `OWNER_REVIEW_REQUIRED`; malformed tuple, canonical bytes, cross-role label,
  or code/H2 identity equality is `REJECT_FIXTURE`. Phase 0 must reject these
  before opening H2 files.

### 7. Provide command text and discovery evidence for review only

* **Evidence:** R74 command discovery
  (`work/agents/CODEX_R74_SYNTHETIC_CPU_COMMAND_DISCOVERY_20260924.md:66-107`)
  and R91 stop rules (`...R91...:59-70`).
* **Owner action:** source-pin the actual runner path and config, verify closed
  roots/audit hooks, CPU-only/no-network/no-real-C8 guards, disposable new
  output root, and atomic receipt behavior. Record the exact command only after
  steps 1-6 are independently accepted.
* **Stop:** any missing prerequisite remains `NO_COMMAND_AVAILABLE`; any data,
  network, target-sensor, GPU, Slurm, receipt, or flag access attempt aborts as
  a boundary violation before input read.

## Non-authorization and first-step boundary

Completing this checklist would support a later owner decision; it does not authorize execution. It does not validate CGLR, establish a new method, authorize real C8 replay, train or run an adapter, submit GPU/Slurm work, modify receipts, or change
`new_method_validated=false` / `novelty_authorization=NONE`.

**R92 status: ACCEPTANCE CHECKLIST / NO_COMMAND_AVAILABLE / DESIGN-ONLY.**
