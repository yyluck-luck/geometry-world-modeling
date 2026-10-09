# R80 final hostile audit of the R79 four-root runner plan

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only final audit. No runner, fixture, manifest, receipt, real C8 input, GPU/Slurm job, or validation flag was created or accessed.

## Decision

**REVISE ONCE BEFORE IMPLEMENTATION.**

R79 closes the root-resolution, role-logging, output-atomicity, and no-data escape
boundary at the directory-role level. One concrete self-hash ambiguity remains in
the source-code manifest. This is the only correction requested by this audit.

## Checks that pass

* Four roots are explicit and pairwise disjoint in the owner checklist:
  resolved read-only stdlib_root, resolved read-only code_root, role-limited
  read-only input_root, and new writable output_root.
* The proposed open log records event, canonical path, root role, mode, process ID,
  and phase. Denied symlink, traversal, alias, hard-link, socket, process, dynamic
  import, GPU, and unlisted-path events abort before scientific input access.
* output_root is checked absent, created atomically with a launch sentinel, never
  replaced automatically, and used for partial receipts only.
* Source and protocol manifest identities are distinct; R70 H2 source-manifest
  binding and the R62 five-phase gate order remain unchanged.

## Remaining concrete flaw

### Source manifest self-hash is not fully defined

R79 says source_code_manifest.json covers every regular file under code_root,
including the manifest itself, while excluding only its supplied manifest_sha256
field. It also requires each file's relative path, size, and SHA-256. If the
manifest's own file record contains its size or digest, changing the supplied
manifest_sha256 changes the file bytes and therefore its own record. The plan
does not define a canonical self-entry or a non-recursive calculation, so two
independent implementations could produce different source-manifest subjects.
This is a source identity ambiguity before phase 0, not a reason to weaken the
four-root boundary.

## Minimal correction

Define source_code_manifest.json as a manifest **of code files**, with the manifest
file itself excluded from the files[] coverage set. The canonical subject must:

1. enumerate every other regular file under code_root exactly once, including all
   runner modules and README files, with relative path, byte length, and lowercase
   SHA-256;
2. reject any missing, extra, symlinked, or hard-linked code-root file;
3. include a fixed manifest_path and schema/version field;
4. exclude only the top-level supplied manifest_sha256 field from the manifest
   subject; no code file or metadata field is silently omitted;
5. require the ordered files[] subject to equal the source_manifest_sha256 value
   recorded in R70 H2 and fixture.owner_gate.

The manifest file remains inside the read-only code_root and is structurally
validated, but it is not recursively listed as one of the files it hashes. This
is the smallest deterministic rule that preserves complete code coverage without
a self-hash cycle.

## Terminal

After this correction, the four-root path policy, role logging, atomic output,
source binding, and no-data escape policy are owner-reviewable. Until the
correction is incorporated and the owner supplies actual artifacts, the runner
remains unimplemented and the command remains NO_COMMAND_AVAILABLE. No fixture,
real C8, replay, GPU/Slurm, receipt edit, or validation-flag change is authorized.

**R80 status: REVISE ONCE / FINAL AUDIT COMPLETE / DESIGN-ONLY.**
Project flags remain new_method_validated=false and novelty_authorization=NONE.
