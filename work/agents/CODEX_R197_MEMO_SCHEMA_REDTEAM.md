# R197 Red-team review of R196 memo schema

## PASS/FAIL findings

| Surface | Result | Risk / required interpretation |
|---|---|---|
| Synthetic conformance cases | **PASS for text; FAIL for promotion** | `observed: MISSING_EVIDENCE` and prose say cases are not executed. A consumer could still treat `expected` values as measured outcomes unless a `case_status: specification_only` marker is required. |
| `allowed_next_branch: null` | **FAIL for parser portability** | Null may deserialize as absent, default, or a wildcard. The memo does not include an explicit field-state marker, so a consumer could misread it as an authorization or unconstrained transition. |
| `MISSING_EVIDENCE` observed fields | **PASS (fail-closed intent)** | Promotion gate requires independent verification and all observed fields remain missing. Any substitution or coercion would be a gate violation. |
| Static branch / execution flags | **PASS** | `B_STATIC_ONLY`, `parser_run:false`, prohibited access/writes, and status invariants clearly deny execution. |
| Independent audit fields | **PASS for blocker** | All audit references are missing and promotion remains blocked; no audit result is implied. |

## Exact stop conditions

Stop and remain `B_STATIC_ONLY` if: (1) any conformance `expected` value is reported as an observed result; (2) null is accepted without an explicit `explicit_null` state marker; (3) `MISSING_EVIDENCE` is coerced to false, empty, or success; (4) any parser/model/data access or branch transition occurs; or (5) promotion proceeds without independently verified assertions and cases.

Required repair before promotion: add `case_status: specification_only` to every conformance case and explicit null-state encoding (`allowed_next_branch_state: explicit_null`, `allowed_next_branch_value: null`). Status remains `END-LINE`, `benchmark_only=true`, `new_method_validated=false`, `novelty_authorization=NONE`.
