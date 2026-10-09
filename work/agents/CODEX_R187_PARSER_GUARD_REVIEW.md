# R187 Parser-guard review of R186

## Findings

| Area | Result | Issue / exact fix |
|---|---|---|
| Branch and execution gates | **PASS (declarative)** | Values are fail-closed. Add a single enum field (`branch: B_STATIC_ONLY`) in any consumer schema; reject unknown values. |
| Guard syntax | **FAIL** | YAML keys such as `reject_if_branch != "B_STATIC_ONLY"` are not portable predicate syntax and may parse as literal keys. Replace with structured rules: `condition_field`, `operator`, `expected_value`, `on_violation: reject`. |
| `MISSING_EVIDENCE` handling | **FAIL** | `reject_if_any_required_field == MISSING_EVIDENCE` includes `parser_audit_ref`, potentially making the schema permanently self-blocking. Define an explicit allowlist of evidence fields and exclude audit metadata. |
| Synthetic commitments | **PASS with risk** | Names are clearly synthetic, but a consumer could mistake non-empty strings for resolved commitments. Add `value_status: synthetic_placeholder` and require a separate `resolved: false` boolean. |
| Recipe/comparison claims | **PASS** | Text explicitly forbids hash/equality claims while fields are missing. Keep `comparison_result` invalid unless recipe and audit fields are resolved in an authorized branch. |
| Parser audit reference | **FAIL for promotion** | `parser_audit_ref: MISSING_EVIDENCE` provides no evidence that guards are enforced. This is acceptable for static-only status, but blocks any promotion. |

## Exact stop conditions

Stop immediately if: (1) a guard is parsed as a literal key rather than a predicate; (2) a synthetic commitment is marked resolved or dereferenced; (3) any hash/control result is asserted while recipe/comparison fields are missing; (4) `MISSING_EVIDENCE` is auto-filled or treated as false/empty; or (5) guard enforcement is claimed without a resolved parser audit in an authorized branch.

Status remains `method_status=END-LINE`, `benchmark_only=true`, `new_method_validated=false`, and `novelty_authorization=NONE`. No parser or benchmark execution is authorized by this review.
