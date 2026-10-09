# R192 Rule-semantics repair delta

Applies conceptually to R190/R191; prior files remain unchanged. Non-executable specification; all values are synthetic or `MISSING_EVIDENCE`.

## Explicit match/mismatch guards

```yaml
guard_semantics:
  predicate_result_values: ["match", "mismatch"]
  mismatch_action: "reject_and_remain_static"
  unknown_or_missing_predicate: "reject_and_remain_static"

guard_rules:
  - rule_id: "ALLOW_ONLY_EXPLICIT_NULL_NEXT_BRANCH"
    condition_field: "allowed_next_branch"
    predicate: "field_state == explicit_null"
    on_match: "continue_static"
    on_mismatch: "reject_and_remain_static"
  - rule_id: "REJECT_MISSING_NEXT_BRANCH"
    condition_field: "allowed_next_branch"
    predicate: "field_state == missing"
    on_match: "reject_and_remain_static"
    on_mismatch: "continue_static"
```

The first rule permits only an explicit null static value; the second ensures a missing field is rejected. No `on_violation` field is used.

## Expanded required-evidence allowlist

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
  - "promotion_gate.sealed_reference_policy_ref"
  - "commitments.resolution_status"
  - "commitments.resolution_actor"
  - "commitments.access_actor"
missing_evidence_token: "MISSING_EVIDENCE"
missing_evidence_policy:
  if_any_required_field_is_missing_or_equals_token: "reject_and_remain_static"
```

## Synthetic commitment fields

```yaml
commitments:
  resolution_status: "MISSING_EVIDENCE"
  resolution_actor: "MISSING_EVIDENCE"
  access_actor: "MISSING_EVIDENCE"
  resolved: false
  value_status: "synthetic_placeholder"
```

## Status

`method_status=END-LINE`; `benchmark_only=true`; `new_method_validated=false`; `novelty_authorization=NONE`. This delta authorizes no parser run, commitment resolution, model/data access, execution, evaluation, or result mutation.
