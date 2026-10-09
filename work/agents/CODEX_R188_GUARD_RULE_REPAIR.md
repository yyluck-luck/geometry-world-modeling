# R188 Structured guard-rule repair delta

Applies conceptually to R186/R187; prior files remain unchanged. This is a non-executable specification. No parser is run and no commitment is resolved.

## Structured fail-closed rules

```yaml
guard_rules:
  - rule_id: "BRANCH_STATIC"
    condition_field: "branch"
    operator: "equals"
    expected_value: "B_STATIC_ONLY"
    on_violation: "reject"
  - rule_id: "NO_NEXT_BRANCH"
    condition_field: "allowed_next_branch"
    operator: "equals"
    expected_value: null
    on_violation: "reject"
  - rule_id: "NO_EXEC"
    condition_field: "execution_authorization"
    operator: "equals"
    expected_value: false
    on_violation: "reject"
  - rule_id: "NO_MODEL"
    condition_field: "model_access"
    operator: "equals"
    expected_value: "prohibited"
    on_violation: "reject"
  - rule_id: "NO_WRITES"
    condition_field: "result_writes"
    operator: "equals"
    expected_value: "prohibited"
    on_violation: "reject"
  - rule_id: "NO_DEREFERENCE"
    condition_field: "commitments.resolved"
    operator: "equals"
    expected_value: false
    on_violation: "reject"
```

Unknown fields, unknown operators, and missing guard fields are rejection conditions.

## Explicit missing-evidence allowlist

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
missing_evidence_token: "MISSING_EVIDENCE"
missing_evidence_policy:
  if_any_required_field_equals_token: "reject_and_remain_static"
  audit_metadata_excluded_from_required_list: true
```

## Synthetic commitment status

```yaml
commitments:
  value_status: "synthetic_placeholder"
  resolved: false
  dereference_policy: "prohibited"
```

Non-empty synthetic strings never imply resolved evidence.

## Parser-audit promotion blocker

```yaml
promotion_gate:
  parser_audit_ref: "MISSING_EVIDENCE"
  promotion_allowed_if: "parser_audit_ref_resolved_and_independent"
  otherwise: "remain_B_STATIC_ONLY"
```

## Status invariant

`method_status=END-LINE`; `benchmark_only=true`; `new_method_validated=false`; `novelty_authorization=NONE`. This delta grants no execution, model access, commitment resolution, evaluation, or result mutation.
