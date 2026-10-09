# R217 Unknown-token repair delta

Static schema delta only. No owner artifact is consumed; no parser, consumer, data/model access, evaluation, commitment resolution, or result mutation occurs.

## Exact result semantics

```yaml
result_semantics:
  allowed_enum: ["pass", "fail", "pending"]
  unknown_token_policy: "reject_and_remain_B_STATIC_ONLY"
  missing_token_policy: "reject_and_remain_B_STATIC_ONLY"
  implicit_coercion: false
  default_success: false
  acceptance_condition: "all_required_result_fields_exactly_equal_pass"
```

Every result-bearing field must be present and exactly one of the three enum values. Empty strings, booleans, arbitrary truthy values, and unrecognized strings are invalid.

## Preserved fail-closed branch

```yaml
branch:
  name: "B_STATIC_ONLY"
  allowed_next_branch_state: "explicit_null"
  allowed_next_branch_value: null
  transition_policy: "prohibited"
  execution_authorization: false
```

## Exact stop condition

If any required field is missing, `MISSING_EVIDENCE`, `pending`, `fail`, unknown, or coercible only by implicit conversion, reject and remain `B_STATIC_ONLY`; do not transition, parse, execute, resolve commitments, access data/models, evaluate, or write results.
