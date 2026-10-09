# R154 Owner-Review Packet Checklist for a Future Synthetic-Only Benchmark

**Access date:** 2026-09-24  
**Evidence boundary:** R152 and its cited-source boundary only. Protocol preparation; no code, data, fixture/runner, GPU, Slurm, evaluation replay, receipt, or flag mutation.

## Purpose and decision boundary

This checklist turns the R152 prerequisites into a reviewable owner packet. It can authorize a separate synthetic-only benchmark construction project only after every required field is source-pinned and signed. It cannot reopen the method END-LINE and does not change `new_method_validated=false` or `novelty_authorization=NONE`.

## Packet identity and ownership

- [ ] Packet ID, revision, creation date, and content hash are recorded.
- [ ] A named owner signs the packet and accepts responsibility for manifest immutability, hidden-label custody, scorer freeze, and release of complete denominators.
- [ ] A separate reviewer is named for independent rerun and has no access to hidden labels during scoring.
- [ ] Scope is explicitly synthetic-only; protected project data, real evaluation data, GPU/Slurm jobs, and current R140 runner paths are excluded.
- [ ] The owner records the exact decision requested: readiness review only, not benchmark results or a method claim.

**Stop branch:** missing owner, reviewer, scope, packet hash, or requested decision => `NOT_READY_OWNER_PACKET`.

## Source and producer manifests

- [ ] Each producer family has a source URL/revision or immutable source hash, license/access note, and reproducible invocation description.
- [ ] The manifest records producer input pose convention, output frame label, depth units, ID/depth schema, intrinsics, image size, pixel-center rule, rounding, z-buffer, and any crop/resize.
- [ ] The hidden true frame label `h` and declared hypothesis set `H` are generated and stored separately from the scorer-visible manifest.
- [ ] Canonical/common-frame cases are labelled explicitly as out-of-hypothesis; they are not forced into `RAW_CV` or `TRANSFORMED_G`.
- [ ] The source manifest states which fields are measured from the producer contract and which are synthetic-generator truth.

**Stop branch:** any unknown API, frame tag, units/schema, or source revision => `NOT_READY_SOURCE_PINNING`; no scorer tuning may infer the missing field.

## Hidden labels and leakage controls

- [ ] Hidden labels are generated before scorer freeze and inaccessible to scorer code, logs, and query selection.
- [ ] Case IDs bind hidden `h`, producer family, geometry split, and map hash without revealing `h`.
- [ ] A leakage audit confirms no branch condition, filename, directory, exception, or metric output encodes `h`.
- [ ] Out-of-hypothesis labels are retained, including canonical-frame and intentionally misdeclared-contract cases.

**Stop branch:** scorer can read, infer, or select on `h` or hidden-case metadata => `LEAKAGE_STOP`.

## Immutable map evidence

- [ ] Exactly one producer call is recorded per case; call count is independently auditable.
- [ ] The producer output map has one content hash and immutable ID map, depth map, dimensions, intrinsics, units, and frame metadata.
- [ ] Every scorer query cell references the same map hash; branch-specific map regeneration is prohibited.
- [ ] A deliberate regeneration sentinel is kept as a negative control and excluded from valid FUP/AReject denominators.
- [ ] The packet defines the map write/read boundary and preserves raw evidence needed for independent hash verification.

**Stop branch:** unequal map hashes, call count other than one, missing map metadata, or regeneration contamination => `MAP_IMMUTABILITY_STOP`.

## Geometry and split design

- [ ] Fixture suite contains multiple asymmetric geometries and nontrivial camera poses; the single R140 fixture is not the benchmark distribution.
- [ ] Intrinsics, image sizes, pixel centers, depth units, and rounding are varied only according to a pre-registered matrix.
- [ ] Held-out geometries and poses are fixed before outcomes; no fixture is selected after seeing pass/fail.
- [ ] Every case has a fixed ID denominator and records positive-z, in-bounds, exact-ID, depth-residual, and missing-output failures.
- [ ] Symmetry, zero-depth, out-of-bounds, and non-finite negative controls are labelled and retained.

**Stop branch:** one fixture only, no held-out split, outcome-based case selection, or variable denominator => `GEOMETRY_SPLIT_STOP`.

## Scorer and controls freeze

- [ ] Query equations, `RAW_CV`/`TRANSFORMED_G` hypotheses, tolerance, rounding, depth conversion, pass rule, and `H2_UNIDENTIFIABLE` rule are frozen before hidden labels are revealed.
- [ ] Compare ordinary declared-convention round trips, residual minimization, and the same-map 2x2 scorer.
- [ ] Include threshold-sensitivity values fixed independently of outcomes; no best-residual threshold search is permitted.
- [ ] Include unit/schema perturbation, branch-regeneration, canonical-frame, and both-pass/both-fail controls.
- [ ] Scorer outputs are sealed before aggregation and cannot modify manifests, hidden labels, or maps.

**Stop branch:** post-hoc threshold, query, hypothesis, unit conversion, scorer code, or map change => `SCORER_FREEZE_STOP`.

## Estimands, denominators, and uncertainty

- [ ] Define `FUP` as the conditional probability of exactly one convention certified on hidden wrong/undocumented/out-of-hypothesis cases.
- [ ] Define `AReject` as the conditional probability of `H2_UNIDENTIFIABLE` on hidden out-of-hypothesis cases.
- [ ] Publish case-level numerators, denominators, exclusions, failures, and missing outputs for each producer family and held-out split.
- [ ] Denominators are fixed before scoring and are not reduced when a query fails or a case is missing.
- [ ] Confidence intervals and the interval method are pre-registered for both estimands and all primary strata.
- [ ] Report in-hypothesis unique-identification accuracy and both-pass/both-fail rates alongside FUP/AReject.

**Stop branch:** undefined conditioning population, hidden denominator changes, dropped failures, or no uncertainty interval => `ESTIMAND_STOP`.

## Independent rerun and review

- [ ] Reviewer receives only source manifests, visible case manifests, scorer version/hash, and map hashes required for rerun.
- [ ] Reviewer cannot access hidden labels until all predictions are sealed.
- [ ] Rerun checks map call count/hash, per-case table, denominators, and aggregate intervals.
- [ ] Discrepancies are preserved as failures with case IDs; they cannot be repaired by relabelling or deletion.
- [ ] Release criteria require agreement on packet fields and a documented explanation for every discrepancy.

**Stop branch:** no independent reviewer, hidden-label custody failure, or irreconcilable rerun discrepancy => `RERUN_STOP`.

## Remaining ambiguity or impossible requirement

- The cited evidence does not establish that no external benchmark already reports FUP/AReject-like quantities; a field-wide novelty claim therefore remains impossible from this bounded packet alone.
- A producer with genuinely undocumented semantics cannot supply a trustworthy `h` from its own output. Such cases must be generated by a source-pinned synthetic wrapper or excluded as `UNKNOWN`; inferring `h` from scorer residuals is invalid.
- The two-label hypothesis `H` cannot represent all canonical or learned frames. Those cases must be out-of-hypothesis and scored for rejection, not relabelled.
- A confidence interval cannot repair an undefined denominator, map regeneration, or label leakage; these are hard stops, not uncertainty bars.

## Owner decision

- [ ] All checklist fields pass and the owner records `READY_FOR_SEPARATE_BENCHMARK_CONSTRUCTION`; or
- [ ] Any field fails and the owner records the exact stop branch, leaving the project at protocol-only status.

Until the first option is signed and separately authorized, do not implement or execute the benchmark. Preserve method END-LINE, `new_method_validated=false`, and `novelty_authorization=NONE`.
