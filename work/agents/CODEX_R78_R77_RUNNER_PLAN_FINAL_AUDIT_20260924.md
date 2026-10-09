# R78 final hostile audit of the R77 CGLR runner plan

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only hostile review. No runner, fixture, owner artifact, H2 packet, manifest, receipt, real C8 input, GPU/Slurm job, or validation flag was created or accessed.

## Decision

**REVISE ONCE BEFORE IMPLEMENTATION.**

R77 closes the R76 gaps in the fixture/owner binding, S131 role and cardinality
checks, source-code versus protocol manifests, atomic output handling, marker
rejection, and the nine named R62 hash domains. One concrete boundary contradiction
remains in the audit-hook specification.

## Checks that pass

* The canonical fixture contains owner_gate and binds the exact fixture subject;
  expected values remain in that owner subject while R62 hash domains exclude them.
* S131 scene/episode/role fields, cardinalities, frame and camera hashes, JSON mask
  paths, sealed target fields, and future-query role restrictions are explicit.
* source_code_manifest and protocol_manifest are distinct, non-recursive domains;
  R70 H2 source_manifest_sha256 is bound to the reviewed code manifest subject.
* Output creation is new-path-only and atomic, with a launch sentinel and preserved
  partial receipts after phase-0 failures.
* The R62 order is preserved, H2 is read only in phase 2, and no H2-dependent hash
  or arm score follows H2_UNIDENTIFIABLE.
* All nine R62 hash names are enumerated, the excluded set is stated, and
  pre-canonicalization marker rejection is required. The implementation still must
  materialize the exact pointer lists and prefixes from R58; R77 correctly makes
  that a review deliverable rather than authorizing a guessed list.

## One remaining concrete flaw

### Audit-hook roots cannot start the proposed runner

R77 lines 205-218 say the audit hook rejects **every** open outside the resolved
input-role or new output-role roots. The same plan requires the runner to read its
source_code_manifest and import its own modules from the future package directory,
and to load Python standard-library modules. Those reads occur outside input_root
and output_root. A literal implementation would reject its own code/stdlib reads
before phase 0, while allowing the runner to bypass the hook would violate the
stated no-data boundary.

This is a source-boundary contradiction, not a reason to use an existing generic
checker.

## Minimal correction

Replace the single two-root rule with a closed four-role allowlist installed before
the first fixture-role open:

1. interpreter/standard-library root, read-only and resolved to the active Python
   installation;
2. immutable code_root containing only the source-pinned runner modules and
   source_code_manifest.json;
3. input_root containing only the role-bound fixture, review, H2, boundary,
   protocol, and referenced numeric mask files;
4. newly-created output_root containing launch/phase/terminal receipts.

The audit hook must record an allowed_root_role for every successful open and deny
all other absolute paths, symlinks, traversal, aliases, hard-linked external files,
sockets, process creation, dynamic imports, GPU/device APIs, and subprocesses.
code_root and the standard-library root are read-only; neither may contain
scientific data or an output path. The source manifest must hash every code-root
file except its own supplied hash field. This correction preserves R77's
input/output role boundaries and makes the no-data guard executable.

## Terminal

Until this four-root rule is incorporated and independently reviewed, the runner
remains unimplemented and the command remains NO_COMMAND_AVAILABLE. No fixture,
real C8 input, replay, GPU/Slurm job, receipt edit, or validation-flag change is
authorized.

**R78 status: REVISE ONCE / FINAL GATE AUDIT INCOMPLETE / DESIGN-ONLY.**
Project flags remain new_method_validated=false and novelty_authorization=NONE.
