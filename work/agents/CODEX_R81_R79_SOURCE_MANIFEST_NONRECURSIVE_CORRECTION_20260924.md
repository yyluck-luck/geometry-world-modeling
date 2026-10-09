# R81 non-recursive source-manifest correction for the future CGLR runner

Date: 2026-09-24 (Asia/Shanghai)  
Scope: future-only design addendum to R79. No runner, manifest, fixture, owner/H2 artifact, receipt, real C8 input, GPU/Slurm job, or validation flag was created or accessed.

## Decision and boundary

This addendum applies the single R80 correction. The four-root policy, role-logged
opens, atomic output, R62 phase order, and R70/R72 gates remain unchanged.
source_code_manifest.json is still a proposed future file and remains absent.
The command remains NO_COMMAND_AVAILABLE and all formal execution remains blocked.

## Canonical source-code manifest

The future code_root contains the source-pinned runner modules, README, and exactly
one source_code_manifest.json. The manifest is a structural metadata file, not a
member of its own files[] coverage set.

The manifest must contain exactly these top-level fields:

    schema: "gwm-cglr-source-code-manifest-v1"
    manifest_path: "source_code_manifest.json"
    code_root_role: "cglr_runner_code"
    files: [ ... ]
    manifest_sha256: "lowercase 64-hex hash"

The canonical manifest subject is the canonical JSON object with the top-level
manifest_sha256 field removed. The subject includes schema, manifest_path,
code_root_role, and the complete ordered files[] list. No other field is omitted.
manifest_sha256 is the SHA-256 of this subject; it is the only supplied hash field
excluded from its own subject.

## files[] coverage and self validation

files[] must enumerate every other regular file under code_root exactly once,
including every runner module and README, with:

    path: relative POSIX path below code_root
    size_bytes: exact byte length
    sha256: lowercase 64-hex SHA-256 of the file bytes

The manifest itself is checked structurally and is never recursively listed in
files[]. Its schema, manifest_path, code_root_role, and files[] order are included
in the canonical subject, so changing any manifest metadata changes
manifest_sha256 without creating a self-hash cycle.

The runner must reject before phase 0:

* a missing code-root file or an extra regular file not listed in files[];
* duplicate file paths, duplicate canonical paths, case/normalization aliases,
  absolute paths, parent traversal, or paths resolving outside code_root;
* any symlink, non-regular file, mount escape, or file with multiple hard links;
* a path, byte length, or SHA-256 mismatch;
* missing, stale, uppercase, non-hex, marker-valued, or recursive manifest fields;
* a second source_code_manifest.json or any alternate manifest name.

The code root is read-only. The runner records the canonical code-root path,
manifest_path, ordered files[], and recomputed manifest_sha256 in the launch
boundary receipt.

## Source binding to R70 and owner gate

R70 h2_provenance.source_manifest_sha256 is defined as the recomputed
manifest_sha256 of this canonical subject, not the raw hash of a self-referential
file. fixture.owner_gate.source_code_manifest_sha256 must equal the same value.
The runner verifies both values and the source manifest before reading any
fixture-role, H2, mask, or review bytes.

An absent or mismatched source manifest returns OWNER_REVIEW_REQUIRED. A malformed
manifest, path-set mismatch, marker, link, or file-hash discrepancy returns
REJECT_FIXTURE. No phase-1 materialization, H2 hash extraction, arm hash, or arm
score follows either failure.

The separate protocol_manifest.json remains the R52/R62/R64/R68/R70/R72/S131
design-chain manifest. It is not part of code_root and is not included in
source_code_manifest.files[].

## Four-root and phase compatibility

* stdlib_root remains read-only and outside code-root coverage.
* code_root is read-only and source-pinned by the non-recursive manifest above.
* input_root remains role-limited synthetic JSON/text.
* output_root remains absent before launch, atomically created, and writable only
  for launch/phase/terminal/boundary receipts.

After source-manifest verification, preserve:

    phase_0_static_preflight
      -> phase_1_materialize
      -> phase_2_H2_gate
      -> phase_3_hash_verification
      -> phase_4_arm_score

The correction changes only source-manifest self-binding. It does not authorize
real C8 data, replay, learned-model imports, GPU/Slurm work, receipt edits, or
validation-flag changes.

## Owner-review acceptance checklist

Before any future implementation is accepted, the reviewer must confirm:

1. files[] equals the complete regular-file set of code_root minus exactly one
   structural file, source_code_manifest.json.
2. Every files[] entry has a relative POSIX path, exact size, lowercase SHA-256,
   and no duplicate or alias.
3. The canonical subject removes only top-level manifest_sha256.
4. The manifest_path/schema/version fields are fixed and included in the subject.
5. R70 H2 and fixture.owner_gate bind the recomputed manifest_sha256.
6. Symlink, hard-link, extra, missing, path-escape, marker, and stale-hash cases
   fail before phase 0.

**R81 status: NON-RECURSIVE SOURCE-MANIFEST CORRECTION COMPLETE / FUTURE-ONLY /
NO EXECUTION.** All proposed paths remain absent. NO_COMMAND_AVAILABLE remains in
force, and project flags remain new_method_validated=false and
novelty_authorization=NONE.
