# R196 Enforcement-audit memo schema

**Scope:** schema only. No implementation, parser run, commitment resolution, execution, or benchmark result. All values are synthetic or `MISSING_EVIDENCE`.

## Audit gate metadata

```yaml
memo_id: "R196-SYNTHETIC-001"
branch: "B_STATIC_ONLY"
allowed_next_branch: null
execution_authorization: false
parser_run: false
model_access: "prohibited"
result_writes: "prohibited"
audit_status: "MISSING_EVIDENCE"
```

## Consumer under audit (descriptive only)

```yaml
consumer_ref: "MISSING_EVIDENCE"
consumer_version: "MISSING_EVIDENCE"
implementation_digest: "MISSING_EVIDENCE"
independent_auditor_ref: "MISSING_EVIDENCE"
```

No consumer implementation is included or invoked by this memo.

## Required enforcement assertions

```yaml
enforcement_assertions:
  all_rules_must_match:
    observed: "MISSING_EVIDENCE"
    evidence_ref: "MISSING_EVIDENCE"
  terminal_rejection:
    observed: "MISSING_EVIDENCE"
    evidence_ref: "MISSING_EVIDENCE"
  fixed_rule_order:
    declared_order: ["STATE_EXPLICIT_NULL_ONLY", "STATE_MISSING_REJECT", "STATE_PRESENT_VALUE_REJECT"]
    observed: "MISSING_EVIDENCE"
    evidence_ref: "MISSING_EVIDENCE"
  unknown_state_default_reject:
    observed: "MISSING_EVIDENCE"
    evidence_ref: "MISSING_EVIDENCE"
  no_branch_transition:
    allowed_next_branch: null
    transition_observed: "MISSING_EVIDENCE"
    evidence_ref: "MISSING_EVIDENCE"
```

## Synthetic conformance cases

```yaml
conformance_cases:
  explicit_null:
    expected: "continue_static"
    observed: "MISSING_EVIDENCE"
  missing:
    expected: "reject_and_remain_static"
    observed: "MISSING_EVIDENCE"
  present_value:
    expected: "reject_and_remain_static"
    observed: "MISSING_EVIDENCE"
  unknown:
    expected: "reject_and_remain_static"
    observed: "MISSING_EVIDENCE"
```

These are test specifications only; no cases are executed.

## Independent audit fields and promotion blocker

```yaml
independent_audit:
  auditor_count: "MISSING_EVIDENCE"
  audit_method_ref: "MISSING_EVIDENCE"
  conflict_resolution: "MISSING_EVIDENCE"
  audit_record_ref: "MISSING_EVIDENCE"
promotion_gate:
  parser_audit_ref: "MISSING_EVIDENCE"
  promotion_allowed_if: "all_assertions_and_cases_independently_verified"
  otherwise: "remain_B_STATIC_ONLY"
```

## Status

`method_status=END-LINE`; `benchmark_only=true`; `new_method_validated=false`; `novelty_authorization=NONE`. This memo authorizes no parser, implementation, model/data access, execution, evaluation, commitment resolution, or result mutation.
