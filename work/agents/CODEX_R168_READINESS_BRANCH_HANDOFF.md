# R168 Readiness-Branch Handoff for the Synthetic-Only Benchmark Packet

**Access date:** 2026-09-24  
**Evidence boundary:** R167/R164 only. This is a protocol handoff; no broader search, code/data/fixture/runner execution, GPU, Slurm, evaluation replay, receipt, or flag mutation.

## Invariants

- Method direction remains END-LINE.
- `new_method_validated=false` and `novelty_authorization=NONE` remain unchanged.
- A signed packet is readiness evidence only. It does not authorize implementation, scoring, GPU/Slurm work, or access to protected evaluation assets.
- Every branch preserves failures and uses the exact R164 stop labels.

## Branch A — signed owner/reviewer packet with instantiated P2/P3/P4 schemas arrives

### Exact next actions

1. **Ingest and hash the packet.** Verify packet ID/revision/content hash, owner signature, independent reviewer identity, synthetic-only scope, and the requested readiness decision. Do not accept prose-only placeholders for P2/P3/P4.
2. **Validate P2.** Parse the metadata-sanitization instance; check public/oracle manifest hashes, complete surface inventory, `oracle_fields_absent=true` for every public surface, retained evidence hashes, and independent sign-off. Cross-check that no public path, header, log, exception, or hash convention reveals `h` or stratum.
3. **Validate P3.** Parse the chronology/access log; verify oracle and scorer custodian identities, raw event evidence, event hashes, and strict order `oracle_commit < scorer_freeze < prediction_seal < oracle_release`. Verify no scorer-role pre-release oracle read and no prediction regeneration after release.
4. **Validate P4.** Parse the trusted-wrapper/oracle instance; verify wrapper/transform source hashes, pre-call commit time/hash, producer call ID, hidden `h`/`H`/strata fields, `producer_declared_tag_role=comparator_only`, and all reviewer checks.
5. **Cross-check the full R164 packet.** Every owner/reviewer checklist item must have an instantiated evidence object, responsible custodian, pre-score timestamp, and passing reviewer check. Unknown source API, frame tag, units, schema, or revision remains a hard stop.
6. **Record readiness.** If all checks pass, record `READY_FOR_SEPARATE_BENCHMARK_CONSTRUCTION` as a readiness state only. Do not implement or execute the benchmark.
7. **Run one bounded Innovation Agent review.** Assign an Innovation Agent a 4-minute packet-only adversarial cycle: try to find one residual leakage path or non-circularity failure in the instantiated P2/P3/P4 evidence, using only R164 and the packet. Deliver one review artifact and stop. No code, data, fixture, runner, GPU, Slurm, evaluation, receipt, or flag access.

### Branch-A acceptance criteria

- Packet hash/signatures and scope pass.
- P2, P3, and P4 instances parse with every required field populated and SHA-256/timestamp syntax valid.
- P2 independent reviewer signs a complete surface audit with no public label leak.
- P3 raw events prove custody and release order; all chronology checks pass.
- P4 proves oracle truth comes from the trusted wrapper before the producer call and producer tags are comparator-only.
- All R164 checklist sections pass, including held-out asymmetric geometry design, scorer freeze, four strata, denominators, confidence intervals, and independent rerun plan.
- No current validation flags change and no execution job is submitted.

### Branch-A failure branches

- P2 missing/failed or any public leak => `LEAKAGE_STOP`.
- P3 missing chronology/access evidence or pre-release access => `HIDDEN_LABEL_CUSTODY_STOP`.
- P4 missing wrapper/pre-call evidence or oracle dependence on producer tags => `ORACLE_INDEPENDENCE_STOP`.
- Unknown source API/frame/units/schema/revision => `NOT_READY_SOURCE_PINNING`.
- Map/call-count/hash failure => `MAP_IMMUTABILITY_STOP`.
- Geometry/split/denominator failure => `GEOMETRY_SPLIT_STOP`, `ESTIMAND_STOP`, or `STRATUM_STOP`.
- Scorer mutation or post-hoc threshold/query change => `SCORER_FREEZE_STOP`.
- Independent rerun discrepancy => `RERUN_STOP`.
- Any other missing owner/reviewer/packet field => `NOT_READY_OWNER_PACKET`.

## Branch B — packet remains absent or incomplete

### Exact next actions

1. Verify absence/incompleteness from the current repository evidence and retain the observed status; do not infer readiness from a filename, partial manifest, or an unsigned draft.
2. Record `NOT_READY_OWNER_PACKET` when the owner/reviewer packet or any required P2/P3/P4 instance is absent.
3. If a partial artifact identifies a specific failure, preserve the corresponding branch (`LEAKAGE_STOP`, `HIDDEN_LABEL_CUSTODY_STOP`, `ORACLE_INDEPENDENCE_STOP`, `NOT_READY_SOURCE_PINNING`, or the relevant R164 branch) instead of silently collapsing it to ready/not-ready.
4. Keep the critical path waiting for a complete signed packet. Do not implement, execute, schedule, or dispatch the benchmark.
5. Do not assign an Innovation Agent in Branch B. Waiting remains the next action until a signed, instantiated packet arrives.

### Branch-B acceptance criteria

- The recorded state names the missing packet/schema or exact failed field.
- No hidden labels are accessed, no scorer is run, and no fixture/map/runner is created.
- `new_method_validated=false` and `novelty_authorization=NONE` remain unchanged.
- No C8/evaluation replay, S103/S132/GRC, GPU/Slurm work, receipt mutation, or validation-flag change occurs.

## Handoff decision

At the next checkpoint choose exactly one branch from evidence: Branch A only after all signed instantiated P2/P3/P4 schemas and R164 fields pass; otherwise Branch B. The handoff does not authorize benchmark execution or a method claim.
