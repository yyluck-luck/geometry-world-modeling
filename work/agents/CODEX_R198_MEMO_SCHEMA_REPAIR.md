# R198 Memo-schema repair delta

Applies conceptually to R196/R197; prior files remain unchanged. Non-executable specification only. No parser runs or commitment resolution; all evidence remains `MISSING_EVIDENCE`.

## Explicit null branch encoding

```yaml
branch_control:
  allowed_next_branch_state: "explicit_null"
  allowed_next_branch_value: null
  transition_observed: "MISSING_EVIDENCE"
  transition_policy: "prohibited"
```

`allowed_next_branch_state` is authoritative; null value alone must never be interpreted as wildcard, absent, or authorization.

## Specification-only conformance cases

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

`expected` is a test specification, never an observed result. Any case without `case_status: specification_only` is invalid and remains static.

## Preserved no-transition gates

```yaml
execution_authorization: false
parser_run: false
model_access: "prohibited"
result_writes: "prohibited"
branch: "B_STATIC_ONLY"
allowed_next_branch: null
```

## Status

`method_status=END-LINE`; `benchmark_only=true`; `new_method_validated=false`; `novelty_authorization=NONE`. This delta authorizes no parser, execution, evaluation, data/model access, commitment resolution, or result mutation.
