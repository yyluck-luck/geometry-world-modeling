# R166 Scorer-Artifact Challenge for Conditional FUP/AReject

**Access date:** 2026-09-24  
**Evidence boundary:** R164 and its cited-source boundary only. No broader search, code/data/fixture/runner execution, GPU, Slurm, evaluation replay, receipt, or flag mutation.

## Challenge question

Could the apparent hidden-frame false-unique-certification gap be produced entirely by scorer engineering choices—depth thresholds, map hashes, branch call counts, or the trusted synthetic wrapper—rather than by a benchmark-relevant failure mode?

## Falsification verdict

**Current verdict: the gap is unvalidated and remains vulnerable to scorer artifacts.** R164's protocol is useful only as a conditional benchmark construction. FUP/AReject survive as estimands if, and only if, their separation from engineering choices is demonstrated under the controls below. Without those controls, a unique pass or `H2_UNIDENTIFIABLE` result is a property of the chosen scorer and wrapper, not evidence of a cross-system certification failure.

Method END-LINE remains unchanged.

## Strongest artifact explanations and controls

### A. Threshold, rounding, and depth conversion

**Artifact:** A permissive tolerance, pixel-center rule, rounding rule, or unit conversion can create a unique pass or rejection independent of frame semantics.

**Control:** Freeze the primary tolerance and equations before oracle release; publish an independently fixed sensitivity grid, exact ID/depth residuals, positive-z and in-bounds rates, and fixed denominators. Repeat the same hidden cases over the pre-registered grid without selecting a favorable threshold.

**Falsifier:** If the FUP/AReject ordering or effect appears only at a post-hoc threshold, changes sign across the pre-registered grid, or disappears under the documented projective tolerance, reject the conditional gap as threshold engineering.

### B. Map hash and branch call count

**Artifact:** Hash checks or call-count metadata may drive the result, or branch-specific regeneration may let each query pass its own map.

**Control:** Require one producer call and one content-addressed map per case; every query cell records the same map hash, dimensions, ID/depth arrays, and units. Include a deliberate regeneration sentinel and a metadata-blind rerun that verifies content equality independently of filenames or hashes.

**Falsifier:** If FUP/AReject changes while map bytes and query values are held fixed but hash labels or call-count fields are changed, or if a regeneration sentinel passes, the result is a scorer artifact and the case is rejected.

### C. Synthetic-wrapper/oracle construction

**Artifact:** The wrapper may encode the desired label or transform and thereby make its own scorer outcome appear identifiable.

**Control:** Commit wrapper source/transform hashes and oracle labels before the producer call. Treat producer-declared tags as comparator-only. Use at least one independently specified transform implementation or analytically pre-registered control per frame category, including canonical out-of-hypothesis cases. The scorer never sees the oracle until prediction sealing.

**Falsifier:** If labels are derived from producer self-description, if two wrapper implementations disagree without a source-pinned adjudication, or if FUP/AReject depends on wrapper identity rather than the hidden transform category, reject the gap as wrapper engineering.

### D. Units, schema, and metadata leakage

**Artifact:** Millimetre/metre conversion, transposed ID/depth arrays, map headers, paths, or exceptions can reveal or force a convention.

**Control:** Source-pin units/schema in the oracle manifest; strip label-bearing metadata from public artifacts; retain a unit/schema perturbation negative control; audit public paths, headers, logs, and exceptions before scorer release.

**Falsifier:** If the scorer can infer `h` from visible metadata, or the perturbation uniquely passes, reject the case under `LEAKAGE_STOP` or `ORACLE_INDEPENDENCE_STOP`.

### E. Scorer implementation and residual baseline

**Artifact:** The 2x2 implementation may contain an indexing or acceptance-rule bug that ordinary residual checks would not share.

**Control:** Compare ordinary declared-convention round trips, residual minimization, and the fail-closed same-map 2x2 scorer on the same immutable maps. Require an independent rerun from public manifests and a case-level discrepancy ledger. Report both-pass/both-fail rates and the in-hypothesis accuracy alongside FUP/AReject.

**Falsifier:** If an independent scorer/rerun disagrees after the same map/query inputs, or if FUP/AReject differs only because of scorer indexing/acceptance logic while ordinary controls agree, reject the protocol implementation.

## Required decision rule

The conditional protocol survives only when all of the following hold on held-out synthetic cases:

1. FUP/AReject strata are fixed before scoring and hidden-label custody is independently evidenced.
2. The effect is stable across the pre-registered threshold/rounding/unit grid.
3. The result is unchanged by metadata-blind map-hash verification and is not reproduced by branch regeneration.
4. Independent wrapper/control paths agree with the source-pinned oracle categories.
5. The same-map scorer shows lower false-unique certification or higher correct rejection than ordinary declared-convention and residual baselines, with fixed denominators and uncertainty intervals.
6. An independent rerun reproduces per-case tables and aggregate estimates without label access before sealing.

If any condition fails, report the exact existing stop branch (`LEAKAGE_STOP`, `HIDDEN_LABEL_CUSTODY_STOP`, `ORACLE_INDEPENDENCE_STOP`, `MAP_IMMUTABILITY_STOP`, `SCORER_FREEZE_STOP`, `ESTIMAND_STOP`, `STRATUM_STOP`, or `RERUN_STOP`) and classify the finding as scorer engineering.

## Final disposition

No empirical benchmark has been run, so the conditional FUP/AReject protocol remains a falsifiable proposal rather than evidence. Do not implement or execute it in the current research line. Preserve `new_method_validated=false`, `novelty_authorization=NONE`, and method END-LINE.
