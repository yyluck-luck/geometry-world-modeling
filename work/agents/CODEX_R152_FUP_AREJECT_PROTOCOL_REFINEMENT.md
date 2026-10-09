# R152 FUP/AReject Protocol Refinement

**Access date:** 2026-09-24  
**Allowed evidence:** R150 and only the primary/official sources cited there (via R142). No broader search, protected data, code/fixture/runner execution, GPU, Slurm, receipt, or flag mutation was used.

## Objective

Refine the hidden-frame false-unique-certification gap from R150 into an identifiable synthetic-only benchmark protocol. The estimands are:

```
FUP = P(exactly one convention is certified | true producer frame is wrong, undocumented, or outside the declared hypothesis)
AReject = P(H2_UNIDENTIFIABLE is emitted | true producer frame is outside the declared hypothesis)
```

These are certification-error quantities; they do not claim a new reconstruction or rendering method.

## Identifiability audit

FUP and AReject are identifiable only when the benchmark generator, not the scorer, records a hidden source-pinned frame label `h`, the declared hypothesis set `H`, and one immutable map per case. For every case the manifest must bind:

- producer input pose convention, output frame label, depth units, ID/depth schema, intrinsics, image size, pixel center, rounding, z-buffer, and source hash;
- `H = {RAW_CV, TRANSFORMED_G}` for the two-query scorer, with any canonical/other frame explicitly marked out-of-hypothesis;
- map content hash and a single producer-call identifier reused by all scorer branches;
- fixed case and system identifiers so denominators are known before outcomes.

Do not estimate the quantities if any of `h`, `H`, units/schema, or map immutability is unknown. An undocumented producer is a labelled out-of-hypothesis case in the synthetic generator; it is not permission for the scorer to infer or relabel `h`.

## Strongest competing explanations and controls

### 1. Residual threshold or tolerance choice

A false unique pass can be caused by a permissive depth tolerance rather than frame confusion. Freeze one tolerance function and rounding rule before scoring, report depth/ID residual distributions, and add a threshold-sensitivity table using thresholds fixed independently of outcomes. No threshold may be selected from the lowest residual or from a preferred convention.

**Reject** a benchmark claim if the unique-pass result disappears under the pre-registered tolerance or if only a post hoc threshold produces separation.

### 2. Branch-specific map regeneration

Regenerating a map per query can make `RAW` and `F3` each pass by construction. Persist one content-addressed map and require identical hashes, IDs, depths, intrinsics, units, and dimensions for every query cell. Include a deliberate regeneration sentinel as a leakage control; it must be labelled invalid and excluded from FUP/AReject.

**Reject** any case with unequal map hashes or a map call count other than one.

### 3. Hidden depth units or schema

Metres versus millimetres, ID/depth misalignment, or a transposed map can mimic a frame error. Unit, schema, array shape, and ID/depth alignment must be source-pinned in the manifest and checked without reading the hidden label. Add a known unit-perturbation negative control whose expected outcome is failure or `H2_UNIDENTIFIABLE`.

**Reject** if units/schema are inferred from residuals, if the negative control uniquely passes, or if a unit conversion is changed after seeing outcomes.

### 4. Pixel-center, rounding, and fixture symmetry

Pixel-center or nearest-pixel choices can alter pass/fail, and a symmetric fixture can allow both queries to pass. Use asymmetric point coordinates, nontrivial camera poses, fixed pixel-center/rounding rules, and held-out geometries. Require a full fixed-denominator ID/depth table, not a mean residual.

**Reject** if both queries pass on a case intended to be in-hypothesis, if the result depends on branch-specific rounding, or if the fixture has not been held out.

### 5. Canonical frames outside the two-query hypothesis

DUSt3R-style common/canonical frames are a direct competing explanation. Generate explicit out-of-hypothesis cases and require `H2_UNIDENTIFIABLE`; do not force a RAW/F3 label. A canonical frame that accidentally produces one passing query is counted in FUP, while a correct rejection contributes to AReject.

**Reject** if out-of-hypothesis labels are unavailable to the generator, if the scorer can inspect `h`, or if canonical cases are silently removed.

## Minimal future synthetic-only protocol

1. Use at least three independently maintained producer families represented by the cited convention families, with hidden labels and one producer call per case.
2. Use multiple asymmetric geometries, poses, intrinsics, pixel conventions, units, and held-out geometry/pose splits. Keep all protected or real evaluation data out of scope.
3. Freeze the manifest, scorer, tolerance, query equations, denominator, and acceptance rule before revealing outcomes. Every branch reads the same immutable map.
4. Compare ordinary declared-convention round trips, residual minimization, and the fail-closed same-map 2x2 scorer. Include regeneration, unit, schema, and canonical-frame negative controls.
5. Report per-case outcomes and aggregate `FUP`, `AReject`, in-hypothesis unique-identification accuracy, both-pass/both-fail rates, ID/depth errors, positive-z/in-bounds rates, denominators, and confidence intervals. Never collapse failures or exclusions.
6. Require an independent rerun from source hashes and manifests. Use no scorer-side access to hidden labels.

## Final decision and stopping rule

**Verdict: retain the estimands, with the controls above.** R150's gap survives only as a conditional benchmark-construction hypothesis. It is falsified if FUP/AReject cannot be separated from tolerance, regeneration, units/schema, pixel conventions, or canonical-frame cases; if map hashes differ; if hidden labels leak; or if an existing cited-style baseline measures the same conditional quantities.

Do not implement or execute this protocol in the current research line. Preserve `new_method_validated=false` and `novelty_authorization=NONE`; any future benchmark requires separate authorization and owner review.
