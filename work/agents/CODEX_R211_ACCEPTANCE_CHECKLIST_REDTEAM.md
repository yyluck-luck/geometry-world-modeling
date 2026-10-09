# R211 Red-team review of R210 acceptance checklist

## PASS/FAIL findings

| Gate | Result | Finding |
|---|---|---|
| Synthetic / `MISSING_EVIDENCE` rejection | **PASS (intent)** | Header states no artifact exists and acceptance requires all fields resolved; current status is static. |
| Self-reference prevention | **FAIL for promotion** | `self_reference_check` and `self_reference_rejected` are unresolved booleans, but no explicit rule says a missing/false value rejects. A consumer could treat absence as pass. |
| Integrity/SHA gate | **FAIL for promotion** | Digest fields are unresolved, but acceptance lacks a machine-readable requirement that `digest_recomputed_locally` and `digest_match` must be explicit true and non-missing. |
| Independent verifier gate | **FAIL for promotion** | `verifier_identity` and independence basis are missing; issuer/verifier distinctness is not required. |
| Acceptance decision semantics | **FAIL for promotion** | `acceptance_decision` is a free field with no allowed enum or fail-closed rule; a synthetic checklist could set `accept` prematurely. |
| Branch/no-transition restrictions | **PASS** | Static branch, explicit null state/value, prohibited transition/execution/model/writes are explicit. |

## Exact stop conditions

Remain `B_STATIC_ONLY` if any mandatory field is missing, any gate is not explicit boolean pass, issuer and verifier independence is unresolved, acceptance decision is not a fail-closed enum, or a synthetic/MISSING_EVIDENCE checklist is treated as an accepted audit. Stop on any external retrieval, parser/consumer execution, commitment resolution, model/data access, evaluation, transition, or result write.

Required repair before acceptance: define explicit `pass/fail/pending` enums, require `pass` for self-reference, digest recomputation/match, provenance, and independent verification, and require issuer/verifier distinctness with an auditable basis. Status remains END-LINE and benchmark-only.
