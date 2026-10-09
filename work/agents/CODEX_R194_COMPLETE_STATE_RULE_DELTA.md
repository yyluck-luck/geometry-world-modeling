# R194 Complete-state rule-composition delta

Applies conceptually to R192/R193; prior files remain unchanged. Non-executable specification only. Values are synthetic or `MISSING_EVIDENCE`.

## Rule composition and default

```yaml
guard_composition:
  operator: "all_rules_must_match"
  evaluation_order: "fixed_rule_id_lexicographic"
  default_on_unknown_or_missing: "reject_and_remain_static"
  default_on_unlisted_state: "reject_and_remain_static"
```

All guard rules must be evaluated; any rejection is terminal. No last-rule-wins behavior is permitted.

## Complete state rules

```yaml
guard_rules:
  - rule_id: "STATE_EXPLICIT_NULL_ONLY"
    condition_field: "allowed_next_branch"
    predicate: "field_state == explicit_null"
    on_match: "continue_static"
    on_mismatch: "reject_and_remain_static"
  - rule_id: "STATE_MISSING_REJECT"
    condition_field: "allowed_next_branch"
    predicate: "field_state == missing"
    on_match: "reject_and_remain_static"
    on_mismatch: "continue_static"
  - rule_id: "STATE_PRESENT_VALUE_REJECT"
    condition_field: "allowed_next_branch"
    predicate: "field_state == present_value"
    on_match: "reject_and_remain_static"
    on_mismatch: "continue_static"
```

Because composition is `all_rules_must_match`, only explicit null can pass the first rule, and missing/present values are terminally rejected. Any unknown state is rejected by default.

## Status

`method_status=END-LINE`; `benchmark_only=true`; `new_method_validated=false`; `novelty_authorization=NONE`. This delta authorizes no parser run, commitment resolution, model/data access, execution, evaluation, or result mutation.
