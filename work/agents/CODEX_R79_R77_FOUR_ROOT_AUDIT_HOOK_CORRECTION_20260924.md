# R79 four-root audit-hook correction for the future CGLR runner

Date: 2026-09-24 (Asia/Shanghai)  
Scope: future-only design addendum to R77. No runner, fixture, source manifest, protocol manifest, receipt, real C8 input, GPU/Slurm job, or validation flag was created or accessed.

## Decision and scope

This addendum applies the single R78 correction to the R77 plan. The audit boundary
now has four closed roots: standard library, source-pinned code, synthetic input,
and newly-created output. Every path below is a proposed future path and is absent.
The result remains NO_COMMAND_AVAILABLE; owner/H2/fixture/hash gates and all formal
execution remain blocked.

The R62 order is unchanged:

    phase_0_static_preflight
      -> phase_1_materialize
      -> phase_2_H2_gate
      -> phase_3_hash_verification
      -> phase_4_arm_score

## Four closed roots

### 1. stdlib_root (read-only)

stdlib_root is the resolved standard-library directory of the active interpreter,
including its platform-standard-library companion only when recorded by the runner
bootstrap. It is selected before the audit hook and is read-only. Only standard
library modules on the closed import allowlist may be imported from this root.
Third-party site-packages, user site directories, virtual-environment packages,
working-directory modules, and extension modules are not implicitly allowed.

The bootstrap records the interpreter identity, resolved stdlib roots, and
read-only role. Any standard-library path that resolves outside these roots is a
boundary failure.

### 2. code_root (read-only and source-pinned)

code_root contains only the future CGLR runner modules, its README, and
source_code_manifest.json. It is read-only and cannot contain data, masks,
checkpoints, receipts, output paths, or symlinks.

source_code_manifest.json covers every regular file under code_root, including all
runner modules and documentation, while excluding only its own supplied
manifest_sha256 field from its canonical subject. It records relative path, file
size, and lowercase SHA-256 for every file. A missing, extra, modified, symlinked,
or hard-linked code-root file is a phase-0 failure. The manifest's own hash is
recomputed from the ordered file list and canonical bytes; no other field is
excluded.

R70 h2_provenance.source_manifest_sha256 and fixture.owner_gate.source_code_manifest_sha256
must equal this recomputed source_code_manifest subject. A source-manifest mismatch
returns OWNER_REVIEW_REQUIRED before any fixture-role read.

### 3. input_root (read-only synthetic roles only)

input_root contains the canonical fixture envelope, review artifact, H2 packet,
boundary artifact, protocol manifest, and only the numeric JSON/text mask files
explicitly referenced by fixture.json. Each successful input open is role-labeled:
fixture, review, h2, boundary, protocol, reveal_mask, or untouched_mask.

Input paths must be relative to input_root after canonical resolution; absolute
paths, parent traversal, aliases, symlinks, non-regular files, and files with
multiple hard links are rejected. The role allowlist rejects RGB/depth arrays,
target sensors, future-query answers, scene archives, checkpoints, learned
weights, real C8 paths, and existing receipts. Future-query camera IDs and pose
metadata remain permitted because they are non-sensor episode declarations.

### 4. output_root (new and writable)

The caller supplies an absent output path outside input_root, stdlib_root, and
code_root. After CLI, root, and source-manifest checks but before phase 0, the
runner creates output_root atomically with a launch sentinel and immutable run ID.
Only launch, phase, terminal, and boundary-audit receipts may be written there.
Output files are never followed through symlinks, and an existing path or creation
race is a boundary failure; the runner never chooses a replacement path.

## Audit-hook installation and open logging

The bootstrap installs the audit hook before opening any input-role file. Every
successful filesystem event is resolved to one of the four roles and logged with:
event type, canonical path, root role, read/write mode, process ID, and phase.
Reads from stdlib_root and code_root must be read-only; reads from input_root must
be read-only; writes are allowed only under the newly-created output_root.

The hook rejects:

* any path outside stdlib_root, code_root, input_root, or output_root;
* symlink components, parent traversal, normalized aliases, mount/working-directory
  escapes, non-regular files, and hard-linked external inputs;
* sockets, network connect/listen, process creation, os.system, subprocess,
  multiprocessing, fork/exec, or shell commands;
* dynamic imports, import paths outside the closed stdlib/code allowlist, model
  packages, CUDA/device APIs, and extension modules;
* writes to stdlib_root, code_root, or input_root, and reads of output files before
  the corresponding phase record exists;
* CLI switches for GPU, Slurm, real C8, replay, model loading, or arbitrary roots.

Any denied event aborts before scientific input access and records a boundary
violation in the new output receipt. The audit log is a process-boundary check,
not evidence of model accuracy or novelty.

## Gate ordering with the four roots

1. Bootstrap resolves and records stdlib_root and code_root, verifies the
   source-code manifest, installs the closed import/audit policy, and checks the
   absent output path.
2. The runner atomically creates output_root and writes the launch sentinel.
3. Phase 0 reads only role-allowed fixture/review/protocol bytes, verifies the
   canonical fixture subject, complete S131 schema, owner gate, ten-arm mapping,
   and pre-canonicalization marker/type/path rules. H2 and boundary contents are
   not opened.
4. Phase 1 materializes computed geometry from synthetic JSON only.
5. Phase 2 opens h2_packet and boundary_artifact, performs exact R70/R72 H2 checks,
   and returns H2_UNIDENTIFIABLE before any H2-dependent hash on failure.
6. Phases 3 and 4 retain R77's nine hash domains, computed-only query separation,
   arm invariants, and terminal mapping.

A phase failure leaves only the partial receipt in the new output_root. It never
mutates input, code, protocol, project flags, or existing receipts.

## Owner-review checklist for this correction

Before implementation can be accepted, the reviewer must confirm:

1. The four roots are explicit, resolved once, role-logged, and pairwise disjoint.
2. stdlib_root and code_root are read-only; code_root has complete manifest coverage
   except its own supplied manifest_sha256 field.
3. input_root allows only the S131 synthetic JSON/text roles and rejects sensors,
   scientific archives, target answers, symlinks, aliases, and hard links.
4. output_root is absent before launch, created atomically, and cannot overwrite
   existing data.
5. The audit hook is installed before input-role reads and rejects network,
   process, dynamic-import, GPU, and unlisted-path escapes.
6. The R62 five-phase order and owner/H2/hash gates remain unchanged.

**R79 status: FOUR-ROOT AUDIT-HOOK CORRECTION COMPLETE / FUTURE-ONLY / NO EXECUTION.**
NO_COMMAND_AVAILABLE remains in force. Project flags remain
new_method_validated=false and novelty_authorization=NONE.
