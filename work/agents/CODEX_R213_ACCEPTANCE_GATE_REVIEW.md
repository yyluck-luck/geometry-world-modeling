# R213 Acceptance-gate semantics review of R212

## PASS/FAIL findings

| Check | Result | Finding |
|---|---|---|
| Pending → reject | **PASS** | `pending_policy` and `missing_evidence_policy` both keep the packet static; every required gate needs `pass`. |
| Decision enum | **PASS** | `accept/reject/pending` is explicit; accept requires all required gates to pass, otherwise static. |
| Issuer/verifier distinctness | **PASS (static)** | Distinctness and independence each require `pass`; identities remain missing, so no acceptance is possible. |
| Digest/canonicalization gates | **PASS** | Local recomputation, digest match, and canonicalization each require explicit pass; pending blocks promotion. |
| No-transition fields | **PASS** | Branch is static, explicit null is encoded with state/value, transition prohibited, execution/model/writes prohibited. |
| Residual promotion blocker | **FAIL for promotion** | All gate results are currently `pending`, and identities/evidence are missing. This correctly blocks acceptance but means no audit result exists. |

## Exact stop conditions

Remain `B_STATIC_ONLY` if any gate is `pending`, `fail`, missing, or non-enum; if `accept` is selected without every required gate equal to `pass`; if issuer/verifier identity or independence is unresolved; if digest/canonicalization checks are inferred rather than independently passed; or if any transition, external retrieval, parser/consumer execution, commitment resolution, model/data access, evaluation, or result write occurs.

Status remains `method_status=END-LINE`, `benchmark_only=true`, `new_method_validated=false`, `novelty_authorization=NONE`.
