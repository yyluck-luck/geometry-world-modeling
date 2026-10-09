# R193 Rule-pair completeness audit of R192

## State coverage

| `field_state` | Rule 1 (`== explicit_null`) | Rule 2 (`== missing`) | Combined outcome |
|---|---|---|---|
| `explicit_null` | match → `continue_static` | mismatch → `continue_static` | Continue static |
| `missing` | mismatch → reject | match → reject | Reject and remain static |
| `present_value` | mismatch → reject | mismatch → continue | **Ambiguous unless rules are conjunctive/ordered** |

## Findings

- **PASS (explicit null):** both rules continue only for the intended static explicit-null state.
- **PASS (missing):** both rules reject missing state.
- **FAIL (present value):** the pair does not state whether rules are conjunctive, ordered, or first-match. Under a first-match evaluator, present value is rejected by Rule 1; under a “last rule wins” or independent-action interpretation, Rule 2 could permit it. The prose does not define composition.
- **PASS (evidence allowlist fail-closed):** any missing or `MISSING_EVIDENCE` required field rejects and remains static. No listed field grants authorization.
- **PASS (commitment status):** `resolved: false` and synthetic status prevent treating placeholder strings as resolved evidence. Promotion remains blocked by missing resolution/audit fields.

## Exact repair / stop condition

Define one rule-composition operator, preferably `all_rules_must_match` with an explicit default reject. Add a third explicit rule for `present_value` with `on_match: reject_and_remain_static`, or state that any state other than `explicit_null` is rejected. Stop and remain `B_STATIC_ONLY` if composition is unspecified, any required evidence field resolves unexpectedly, `resolved` is not exactly boolean false, or any parser treats a mismatch/unknown as continuation.

Status remains `method_status=END-LINE`, `benchmark_only=true`, `new_method_validated=false`, `novelty_authorization=NONE`; no parser or execution is authorized.
