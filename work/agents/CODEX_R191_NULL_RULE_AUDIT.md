# R191 Null-rule semantics audit of R190

## PASS/FAIL

| Check | Result | Finding |
|---|---|---|
| State vocabulary | **PASS** | `present_value`, `explicit_null`, and `missing` are distinct; token is named. |
| Predicate/prose consistency | **FAIL** | Rules say `operator: is_explicit_null`, `expected_value: true`, `on_violation: reject`. Under ordinary guard semantics, a true predicate may be treated as a violation and rejected, contradicting the prose that explicit null is the required static value. The intended policy is “accept only explicit null; reject otherwise,” which needs an explicit `on_match`/`on_mismatch` convention. |
| Missing handling | **PASS (prose), FAIL (machine clarity)** | Prose says absent fields reject, and a separate missing rule exists, but the rule format does not state whether `on_violation` means predicate mismatch or predicate match. |
| Allowlist coverage | **FAIL** | Includes access policy ref, access log, parser audit, canonicalization, comparison, and review refs. It omits `promotion_gate.sealed_reference_policy_ref` and any explicit commitment-resolution status/access actor field. |
| Promotion gate | **PASS (fail-closed intent)** | Missing required evidence keeps Branch B static. Machine semantics still depend on resolving the predicate ambiguity above. |

## Exact repair / stop condition

Repair by replacing each guard with an unambiguous form, for example: `condition: field_state(allowed_next_branch) != explicit_null`, `on_condition: reject`; and a separate `condition: field_state(...) == missing`, `on_condition: reject`. Add `promotion_gate.sealed_reference_policy_ref` and commitment-resolution/access-actor fields to the required allowlist.

Stop and remain `B_STATIC_ONLY` if rule semantics are not normalized to an explicit match/mismatch convention, if any required allowlist field is absent or `MISSING_EVIDENCE`, or if a consumer treats explicit null as permission to advance. Status remains `END-LINE`, `benchmark_only=true`, `new_method_validated=false`, `novelty_authorization=NONE`.
