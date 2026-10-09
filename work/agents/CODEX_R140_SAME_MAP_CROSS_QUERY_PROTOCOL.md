# R140 Same-Map Cross-Query Protocol

**Status:** corrected protocol only; no implementation or execution.  
**Purpose:** resolve the R135/R136 pose alternatives without the R138 self-consistent-map flaw. Every query below uses one immutable producer output.

## 1. Fixed synthetic fixture and one producer call

Use the fixed 24-point metric fixture from R137: a 16-point plane at `z=5.0` (`x={-1.2,-0.4,0.4,1.2}`, `y={-0.8,-0.2666666667,0.2666666667,0.8}`) plus the eight vertices of a unit cube centered at `(0,0,3.0)`. Each point has an immutable ID. Use metres, a 640×480 raster, and

`K=[[560,0,319.5],[0,560,239.5],[0,0,1]]`.

Use one anchor dataset pose `T_cv,0=I_4` and pre-register the **single producer input pose** as

`T_in = T_cv,0 F4 = F4`,  
`F4=diag(1,-1,-1,1)`, `F3=diag(1,-1,-1)`.

The producer call receives the fixture points/images and exactly this `T_in`. It emits one immutable map `M` containing an ID map, a depth map, dimensions, intrinsics, depth units, and a frame tag. `M` is written once, content-addressed, and reused for every query cell; it must never be regenerated per hypothesis.

**UNKNOWN blocker:** the inspected sources expose the transformed pose at `pipeline.py:975-988` and `:1031-1037`, but do not establish the producer API, output ID/depth schema, or output frame semantics. The call is therefore not executable until H2 source pinning fills those fields.

## 2. Pre-registered frame tag and input manifest

Before the producer call, freeze a manifest with:

- `T_cv=I_4`, `T_in=F4`, `F3/F4`, `K`, image size, point coordinates/IDs, and source hashes;
- `producer_input_convention = c2w` (the pipeline labels/stores c2w at `pipeline.py:149-181`);
- `map_frame_tag ∈ {RAW_CV, TRANSFORMED_G}`;
- `map_depth_unit = metres` (or one explicitly documented conversion to metres);
- the exact rounding rule (`np.round`/nearest-even), bounds, and nearest-depth z-buffer.

The actual `map_frame_tag`, producer output depth unit, and producer call signature are currently **UNKNOWN**. Stop before implementation if any remains unset. The frame tag must be source-pinned, not inferred from a later query result.

## 3. Same-map 2×2 query confusion table

For each of the 24 world points, compute

`p_cv = (T_cv^{-1}X_h)[:3]`,  
`p_g = (T_in^{-1}X_h)[:3] = F3 p_cv`.

Define two queries into the same immutable map `M`:

- `Q_RAW`: pass `q=p_cv`;
- `Q_F3`: pass `q=F3 p_cv`.

Evaluate both queries against the same `M` and report this table (all cells use the same map bytes, IDs, depth values, intrinsics, and denominator):

| Expected producer frame (from pre-registered tag) | `Q_RAW: q=p_cv` | `Q_F3: q=F3 p_cv` |
|---|---|---|
| `RAW_CV` | `C_RAW_RAW` | `C_RAW_F3` |
| `TRANSFORMED_G` | `C_G_RAW` | `C_G_F3` |

Rows are interpretations of the one tagged map, not separately generated maps. The binding row is selected from the manifest before looking at query outcomes. The opposite row is retained as a diagnostic sensitivity table; it cannot be used to relabel `M`.

Each cell records, over the fixed denominator, valid positive-z rate, in-bounds rate, exact point-ID rate, depth residuals, and pass/fail. No PSNR, RGB metric, or branch-specific map regeneration is allowed.

## 4. Fixed equations, tolerance, and denominator

Projection for query `q=(x,y,z)` is

`u=fx*x/z+cx`, `v=fy*y/z+cy`, `u_hat=np.round(u)`, `v_hat=np.round(v)`.

Require `z>0`, `0≤u_hat<640`, and `0≤v_hat<480`. At `(u_hat,v_hat)`, read `M.id_map` and `M.depth_map` and compute

`e_depth = |M.depth_map[v_hat,u_hat] - z|`,  
`TOL(z)=max(0.05,0.05 z)` metres.

The fixed denominator is `N_den=24` point IDs. Invalid z, out-of-bounds pixels, missing IDs, or non-finite depth count as failures and never reduce the denominator. The source tolerance and positive-z/depth semantics come from `compute_support_masks.py:17-18,27-42,44-57`; depth units must be confirmed or converted to metres before applying `TOL`.

For an optional algebraic audit, record `e_frame=||p_g-F3 p_cv||_∞` and the round-trip error of the tagged producer pose. These are sanity checks only: they are identities by construction and cannot select the winning query. Selection must use same-map ID/depth observations.

## 5. Unique acceptance and H2 rejection

A query **passes** only if all 24 correspondences are finite, positive-z, in bounds, exact-ID matched, and satisfy `e_depth≤TOL(z)`. The binding row must satisfy exactly one of:

- `RAW_CV` tag: `C_RAW_RAW` passes and `C_RAW_F3` fails;
- `TRANSFORMED_G` tag: `C_G_F3` passes and `C_G_RAW` fails.

A numeric “uniqueness margin” beyond pass/fail is **UNKNOWN** and must not be invented. If both queries pass, neither passes, or the manifest tag disagrees with the only passing query, reject the fixture as `H2_UNIDENTIFIABLE`. Do not choose by a smaller mean residual.

The raw-frame alternative is supported only by a tagged `RAW_CV` map with the `Q_RAW`/`Q_F3` pattern above. The transformed-frame/evaluator-hygiene explanation is supported only by a tagged `TRANSFORMED_G` map with the `Q_F3`/`Q_RAW` pattern above. No method claim follows either outcome.

## 6. Owner, H2, and runner prerequisites

### Owner prerequisite — **UNKNOWN until assigned**

An owner must sign the manifest, freeze the 24 points/IDs, `T_in`, `K`, `F3/F4`, units, rounding, z-buffer, denominator, query table, and source hashes. No implementation starts before owner identity and review sign-off are recorded.

### H2 prerequisite — **UNKNOWN until source-pinned**

H2 must provide a source-pinned producer call showing that `T_in=F4` is consumed as c2w, identify whether `M` is `RAW_CV` or `TRANSFORMED_G`, document map depth units and ID/depth alignment, and preserve the immutable map hash. The current sources establish the visible transformed callsite but not these producer outputs; therefore H2 remains unresolved.

### Runner prerequisite — **UNKNOWN until reviewed**

Only after the owner and H2 gates pass may a runner be implemented. It must perform one producer call, persist one immutable `M`, execute both queries against that same `M`, emit the full 2×2 table with `N_den=24`, and carry a convention registry (c2w/w2c, axes, frame tag, `K`, units, crop/resize, rounding, tolerance, hashes). It must not select the frame from query outcomes or target/future data and must not overwrite frozen artifacts.

## 7. Stop rule

If the producer call, map frame tag, output units/schema, owner sign-off, or runner registry is `UNKNOWN`; if `M` cannot be immutable and shared; if the binding row has no unique pass/fail pattern; or if any identity/depth value is non-finite, stop with `H2_UNIDENTIFIABLE`. Do not implement, execute, rescore real data, submit GPU/Slurm work, touch receipts/flags, or infer a method claim. Preserve `new_method_validated=false` and `novelty_authorization=NONE`.
