# R190 Explicit-null / evidence-allowlist correction delta

Applies conceptually to R188/R189; prior files remain unchanged. Non-executable specification only. No parser runs and no commitment is resolved.

## Explicit-null versus missing semantics

```yaml
field_state_model:
  states: ["present_value", "explicit_null", "missing"]
  missing_token: "MISSING_EVIDENCE"
  null_operator: "is_explicit_null"
  missing_operator: "is_missing"
```

Corrected branch rule:

```yaml
- rule_id: "NO_NEXT_BRANCH_EXPLICIT_NULL"
  condition_field: "allowed_next_branch"
  operator: "is_explicit_null"
  expected_value: true
  on_violation: "reject"
- rule_id: "NO_NEXT_BRANCH_MISSING"
  condition_field: "allowed_next_branch"
  operator: "is_missing"
  expected_value: true
  on_violation: "reject"
```

An absent field cannot satisfy the explicit-null rule; both states reject in this static branch.

## Complete required-evidence allowlist

```yaml
required_evidence_fields:
  - "canonicalization.whitespace_policy"
  - "canonicalization.field_order"
  - "canonicalization.excluded_fields"
  - "canonicalization.numeric_format"
  - "canonicalization.serialization_format"
  - "canonicalization.recipe_content"
  - "canonicalization.reproducibility_check"
  - "comparison.comparison_operator"
  - "comparison.tie_break_rule"
  - "comparison.independent_audit_ref"
  - "independent_review.review_record_ref"
  - "sealed_reference_policy.access_policy_ref"
  - "sealed_reference_policy.access_log_ref"
  - "promotion_gate.parser_audit_ref"
missing_evidence_token: "MISSING_EVIDENCE"
missing_evidence_policy:
  if_any_required_field_equals_token: "reject_and_remain_static"
  if_any_required_field_is_missing: "reject_and_remain_static"
  audit_metadata_excluded_from_required_list: true
```

## Fail-closed promotion rule

```yaml
promotion_gate:
  parser_audit_ref: "MISSING_EVIDENCE"
  sealed_reference_policy_ref: "MISSING_EVIDENCE"
  promotion_allowed_if: "all_required_evidence_present_and_independently_audited"
  otherwise: "remain_B_STATIC_ONLY"
```

## Status

`method_status=END-LINE`; `benchmark_only=true`; `new_method_validated=false`; `novelty_authorization=NONE`. This delta authorizes no execution, model/data access, commitment resolution, evaluation, or result mutation.
