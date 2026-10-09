# R200 Duplicate-null repair delta

Applies conceptually to R198/R199; prior files remain unchanged. Non-executable specification only. No parser or commitment resolution; all observations remain `MISSING_EVIDENCE`.

## Single authoritative null representation

```yaml
branch_control:
  branch: "B_STATIC_ONLY"
  allowed_next_branch_state: "explicit_null"
  allowed_next_branch_value: null
  transition_policy: "prohibited"
  transition_observed: "MISSING_EVIDENCE"
```

The bare `allowed_next_branch: null` field is removed. Consumers must reject any packet that contains the deprecated bare field or lacks the state/value pair.

## Preserved specification-only cases

```yaml
conformance_cases:
  explicit_null:
    case_status: "specification_only"
    expected: "continue_static"
    observed: "MISSING_EVIDENCE"
  missing:
    case_status: "specification_only"
    expected: "reject_and_remain_static"
    observed: "MISSING_EVIDENCE"
  present_value:
    case_status: "specification_only"
    expected: "reject_and_remain_static"
    observed: "MISSING_EVIDENCE"
  unknown:
    case_status: "specification_only"
    expected: "reject_and_remain_static"
    observed: "MISSING_EVIDENCE"
```

## Fail-closed no-transition rule

```yaml
no_transition_guard:
  required_state_field: "allowed_next_branch_state"
  required_state: "explicit_null"
  required_value_field: "allowed_next_branch_value"
  required_value: null
  on_missing_or_mismatch: "reject_and_remain_static"
  deprecated_bare_field_policy: "reject"
```

## Status

`method_status=END-LINE`; `benchmark_only=true`; `new_method_validated=false`; `novelty_authorization=NONE`. This delta authorizes no parser, execution, evaluation, data/model access, commitment resolution, or result mutation.
