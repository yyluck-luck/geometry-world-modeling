# R112 canonical owner-hash closure audit

Date: 2026-09-24 (Asia/Shanghai)  
Scope: read-only closure review. No implementation, fixture execution, GPU/
Slurm job, protected C8/evaluation read, receipt update, or flag change.

## Verdict: PASS

R111's one-field correction is consistent with R89 and closes the remaining
alias/alternate-subject branch. R89 already defines the only supplied owner
hash (`/owner_gate/review_artifact_sha256`) and the only subject operation:
remove exactly that JSON Pointer, then run `canonical_json_v2` over the whole
remaining review artifact. R111 now states that `owner_subject_sha256` is an
internal recomputed variable only. It is not a JSON field, pointer, alias, or
second supplied value. Therefore no extra schema field is needed.

Evidence:

* R111's internal-only rule and no-second-subject wording:
  `work/agents/CODEX_R111_OWNER_GATE_FINAL_AUDIT_20260924.md:24-44`.
* R89's exact deletion and single supplied hash:
  `work/agents/CODEX_R89_R88_CANONICAL_JSON_V2_CORRECTION_20260924.md:31-41`.
* R89's phase-0 recomputation and alias rejection:
  `work/agents/CODEX_R89_R88_CANONICAL_JSON_V2_CORRECTION_20260924.md:79-97`.

## Closed canonical procedure

The owner-facing contract is exactly:

```text
supplied = review_artifact["owner_gate"]["review_artifact_sha256"]
subject = canonical_json_v2(
    review_artifact with exactly
    /owner_gate/review_artifact_sha256 removed)
require supplied == SHA256(subject)
```

The computed digest may be held in memory or an implementation-local variable
named `owner_subject_sha256`; it must not be serialized or accepted as an
alternate input. Any duplicate owner hash, unknown alias, second subject,
filtered projection, marker, or non-canonical encoding is rejected before H2
access. This gives one hash subject and one rejection path without changing the
R89 schema.

## Exact owner action

When the missing artifacts become available, the owner should supply the
existing `review_artifact.json` shape with:

1. the R70 owner-gate fields and accepted manifest chain;
2. the R85 `manifest_identity` object with exactly its seven fields;
3. exactly one lowercase 64-hex `review_artifact_sha256`, computed by the
   procedure above; and
4. no `owner_subject_sha256` field and no alias or copied hash field.

The owner must bind that artifact to the R98 final frozen snapshot and pass the
R85/R89 phase-0 checks before any materialization or H2 read. This is a review
and artifact-supply action; it does not authorize execution by itself.

## Terminal boundary

The owner/H2/fixture/runner artifacts and supported command remain absent in
the audited local project, so `NO_COMMAND_AVAILABLE` remains in force. Keep
`new_method_validated=false`, `novelty_authorization=NONE`, and END-LINE. Do
not read protected C8/evaluation data, submit GPU/Slurm work, or change flags.

**R112 status: PASS / canonical owner-hash branch closed / no schema-field
addition / NO EXECUTION.**
