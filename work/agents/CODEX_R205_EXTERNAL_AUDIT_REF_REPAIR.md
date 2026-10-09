# R205 External-audit-reference repair delta

Applies conceptually to R203/R204; prior files remain unchanged. Non-executable schema only. No consumer/parser execution or commitment resolution; all observations remain `MISSING_EVIDENCE`.

## External reference requirements

```yaml
external_reference_policy:
  reference_id_format: "MISSING_EVIDENCE"
  same_record_reference: "reject"
  self_reference: "reject"
  unresolved_placeholder_reference: "reject"
  external_auditor_record_required: true
  reference_resolution_status: "MISSING_EVIDENCE"
```

## Audit fields with external-only refs

```yaml
independent_audit:
  auditor_identity_commitment: "SYNTHETIC_AUDITOR_COMMITMENT"
  auditor_count: "MISSING_EVIDENCE"
  conflict_policy: "MISSING_EVIDENCE"
  adjudication_record_ref: "MISSING_EVIDENCE"
  audit_record_ref: "MISSING_EVIDENCE"
  audit_record_ref_scope: "external_record_only"
  self_reference_policy: "reject"

parser_audit:
  status: "MISSING_EVIDENCE"
  parser_run: false
  audit_ref: "MISSING_EVIDENCE"
  audit_ref_scope: "external_record_only"
  self_reference_policy: "reject"
```

A non-empty synthetic string is not a resolved external reference; the reference must be independently verified before promotion.

## Preserved no-transition gates

```yaml
branch: "B_STATIC_ONLY"
allowed_next_branch_state: "explicit_null"
allowed_next_branch_value: null
transition_policy: "prohibited"
execution_authorization: false
model_access: "prohibited"
result_writes: "prohibited"
```

## Status

`method_status=END-LINE`; `benchmark_only=true`; `new_method_validated=false`; `novelty_authorization=NONE`. This delta authorizes no parser, consumer execution, commitment resolution, evaluation, or result mutation.
