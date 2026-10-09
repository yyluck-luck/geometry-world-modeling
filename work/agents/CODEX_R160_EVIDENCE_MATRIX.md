# R160 Evidence Matrix for R158 Owner/Reviewer Packet

**Access date:** 2026-09-24  
**Evidence boundary:** R158 only. No broader search, code/data/fixture/runner execution, GPU, Slurm, evaluation replay, receipt, or flag mutation.

## Matrix conventions

“Pre-score” means the object must exist and be hash-committed before scorer release or any hidden-label reveal. A reviewer may verify an object after scoring, but cannot repair a missing pre-score object. `Owner` denotes the packet owner; `Oracle` denotes the hidden-label custodian; `Scorer` denotes the scorer custodian; `Rerun` denotes the independent reviewer.

| ID | R158 requirement | Non-circular evidence object | Custodian / reviewer | Pre-score timing | Exact stop branch | Object status |
|---|---|---|---|---|---|---|
| P1 | Packet identity, owner, reviewer, synthetic-only scope | Signed packet metadata, revision hash, owner/reviewer identities, scope declaration | Owner; Rerun verifies hash | Before readiness decision | `NOT_READY_OWNER_PACKET` | Defined; reviewer hash check required |
| P2 | Public/oracle manifest split and metadata sanitization | Public manifest hash plus separately sealed oracle-manifest hash; independent metadata-leak audit covering paths, headers, logs, exceptions, and hashes | Public custodian + Oracle; Rerun audits both | Before scorer release | `LEAKAGE_STOP` | Partly defined; audit report schema is still unspecified |
| P3 | Two-custodian hidden-label custody | Oracle commit hash/time, scorer config hash, prediction hash, access log, and release-order record | Oracle + Scorer; Rerun checks chronology | Oracle commit before scorer freeze; release after prediction seal | `HIDDEN_LABEL_CUSTODY_STOP` | Defined if logs are retained |
| P4 | Oracle independent of producer self-description | Trusted synthetic-wrapper source hash, controlled-transform manifest, pre-call oracle commit, and proof producer tags are comparator inputs only | Oracle + Owner; Rerun verifies wrapper hash | Before producer call and scorer freeze | `ORACLE_INDEPENDENCE_STOP` | Partly defined; wrapper evidence format is unspecified |
| P5 | Source and producer manifests | Immutable source URL/revision/hash, invocation record, convention/API/schema/units manifest, and known-vs-unknown field ledger | Owner/H2; Rerun verifies source hash | Before scorer freeze | `NOT_READY_SOURCE_PINNING` | Defined; unknown fields remain hard stops |
| P6 | One immutable map per case | Producer call trace, call count, content-addressed map hash, map metadata hash, and per-cell hash references | Map custodian; Rerun recomputes hashes | Map and trace committed before scoring | `MAP_IMMUTABILITY_STOP` | Defined; call-trace retention must be explicit |
| P7 | Multiple asymmetric geometries and held-out split | Fixture-generator revision/hash, split manifest, case IDs, control-case ledger, and pre-outcome split commit | Geometry custodian/Owner; Rerun checks IDs | Before any outcome is read | `GEOMETRY_SPLIT_STOP` | Defined; generator source must be retained |
| P8 | Scorer/query/tolerance freeze | Scorer version/hash, equations, tolerance/rounding/unit-conversion config, acceptance rule, freeze timestamp, and prediction seal | Scorer; Rerun verifies timestamp/hash | Before oracle release | `SCORER_FREEZE_STOP` | Defined if timestamp is trusted |
| P9 | Four disjoint strata and FUP/AReject estimands | Oracle stratum ledger, fixed denominators, case-level numerator/exclusion ledger, CI-method manifest, and per-stratum aggregate report | Oracle + Stats custodian; Rerun recomputes after release | Strata and denominators committed before scoring | `ESTIMAND_STOP` or `STRATUM_STOP` | Defined; requires label release only after seal |
| P10 | Independent rerun and discrepancy handling | Public rerun bundle, reviewer prediction hash, map/scorer hash checks, per-case tables, discrepancy ledger, and signed resolution report | Rerun reviewer; Owner cannot edit discrepancies | Rerun input sealed before oracle reveal | `RERUN_STOP` | Defined if discrepancy ledger is append-only |
| P11 | Unresolved limits and no field-wide novelty claim | Evidence-boundary memo stating cited-source limit, unknown semantics, incomplete `H`, and prohibited inference; owner decision records protocol-only status | Owner; Rerun checks claim wording | Before any public benchmark claim | `NOT_READY_OWNER_PACKET` | No object can prove absence of external benchmarks; limitation must remain explicit |

## Non-circularity audit

1. **Public metadata audit gap.** R158 requires a metadata-sanitization audit but does not define its artifact schema, independent signer, or test inventory. A prose assertion is circular. Until a hashed audit report with reviewer sign-off exists, P2 is not complete and the branch is `LEAKAGE_STOP`.
2. **Trusted-wrapper evidence gap.** R158 requires oracle truth from a synthetic wrapper but does not define the wrapper manifest/source-hash format or pre-call commit record. Producer self-description cannot fill this gap. Until those objects exist, P4 is incomplete and the branch is `ORACLE_INDEPENDENCE_STOP`.
3. **Chronology evidence.** Commit hashes alone do not prove release order. P3 needs auditable timestamps/access logs; without them, hidden-label custody is an assertion and the branch is `HIDDEN_LABEL_CUSTODY_STOP`.
4. **Field-wide novelty.** No packet object can prove that no external benchmark reports the same estimands. P11 must remain a limitation; any stronger claim is blocked by `NOT_READY_OWNER_PACKET`.

## Decision

The R158 packet is auditable in principle, but P2 and P4 still lack fully specified, non-circular evidence-object schemas. Treat the packet as **not ready** until the owner adds those schemas and preserves the stated stop branches. This is protocol QA only; do not implement or execute the benchmark. Preserve method END-LINE, `new_method_validated=false`, and `novelty_authorization=NONE`.
