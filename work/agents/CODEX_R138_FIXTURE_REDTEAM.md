# R138 Fixture Red-Team Audit

**Verdict:** concrete correction required. R137 has a decisive internal identifiability flaw.

## Material flaw

R137 defines the two substantive branches as separate map/query pairs (`RAW_RAW` and `FLIP_FLIP`) at lines 89-97, and its synthetic check says to “generate a tiny retrieval map” for each candidate producer contract (lines 79-85). The identity equations are then tautological within each pair:

- `p_cv = T_cv^{-1}X` by definition (lines 36-38), so the raw branch's camera and world round-trip errors are zero for a raw map.
- `p_g = (T_cvF4)^{-1}X = F3 p_cv` by definition (lines 40-43), so the transformed branch's errors are zero for a transformed map.

If each branch gets its own map generated in its own frame, both branches can satisfy the `<=1e-6` identity and raster/depth criteria at lines 101-107. The “unique branch” rule therefore cannot identify the producer convention; it only verifies that each branch is self-consistent. This makes RAW_RAW versus FLIP_FLIP non-identifiable even with perfect arithmetic.

## Correction proposal

1. **Freeze one map before branch evaluation.** Generate one immutable synthetic producer output from one source-pinned producer call and one fixed input pose. The map must not be regenerated after selecting or inspecting a candidate branch.
2. **Cross-query the same map.** For that single map, evaluate both query conventions (`p_cv` and `F3 p_cv`) against identical point IDs, pixels, and depth values. Report the 2×2 map/query confusion table. Self-consistency of a separately generated map is diagnostic only and cannot establish the winner.
3. **Require the producer input/frame to be recorded.** The fixture manifest must state whether the frozen producer call received `T_cv` or `T_cv F4`, and must preserve the returned pointmap/surfel coordinates and depth in an immutable frame-tagged artifact. The source-pinned producer boundary is currently unavailable, as R137 itself acknowledges at lines 117-119.
4. **Change acceptance.** Accept a convention only when exactly one query transform passes the same-map identity, ID, positive-z, and depth criteria while the other fails. If the producer input or map frame is not fixed before querying, return `H2_UNIDENTIFIABLE`; do not call a branch “unique.”

The `1e-6` identity threshold, `TOL(z)`, fixed denominator, and stop conditions may remain, but they must be applied to the same frozen map for both queries. This correction is protocol-level only; no implementation or execution is authorized by this audit.

## Required stop rule

Until a source-pinned producer call, one immutable map, and a pre-registered map-frame tag exist, stop. Do not implement the R137 fixture, rescore real data, or infer evaluator hygiene or a method claim. Preserve `new_method_validated=false`, `novelty_authorization=NONE`, and `H2_UNIDENTIFIABLE`.
