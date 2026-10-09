# R137 Synthetic Frame-Fixture Protocol

**Status:** protocol only; implementation and execution are blocked pending the prerequisites below.  
**Scope:** zero-GPU synthetic identity check for the R135/R136 pose alternatives. No protected data, runner, receipts, flags, Slurm, or real-data scoring is used.

## 1. Fixed fixture geometry

Use world coordinates in metres and OpenCV camera axes `(x right, y down, z forward)`.

- **Plane:** `z=5.0`, with `x ∈ {-1.2,-0.4,0.4,1.2}` and `y ∈ {-0.8,-0.2666666667,0.2666666667,0.8}` (16 points).
- **Cube vertices:** axis-aligned cube centered at `(0,0,3.0)` with side `1.0`; use all eight vertices `(±0.5, ±0.5, 2.5 or 3.5)` (8 points).
- The fixture point set is therefore fixed at `N_point=24`; each point has a stable ID. A nearest-depth z-buffer is used if a projected pixel collision occurs.

Use three fixed camera-to-world matrices. Let

`R_y(θ) = [[cosθ,0,sinθ],[0,1,0],[-sinθ,0,cosθ]]`.

- `T_cv,0 = [R_y(0°), (0,0,0)]`
- `T_cv,1 = [R_y(+10°), (0.20,0.00,0.15)]`
- `T_cv,2 = [R_y(-12°), (-0.20,0.05,0.10)]`

All matrices are homogeneous 4×4 with final row `[0,0,0,1]`. The nonzero Y/Z coordinates and nonzero yaw are required to distinguish the raw and flipped branches.

## 2. Fixed camera and transform definitions

Use one explicit 640×480 raster and

`K = [[560,0,319.5],[0,560,239.5],[0,0,1]]`.

Depth is stored and compared in metres. The source evaluator converts PNG millimetres to metres (`compute_support_masks.py:24-25`); no PNG I/O is needed for this fixture.

Define

`F4 = diag(1,-1,-1,1)`, `F3 = diag(1,-1,-1)`.

For `T_cv=[R,t]` and homogeneous world point `X_h`,

`p_cv = (T_cv^{-1} X_h)[:3] = R^T (X-t)`.

For the transformed branch,

`T_g = T_cv F4`,  
`p_g = (T_g^{-1} X_h)[:3] = F3 p_cv`.

These are the conventions exposed by `compute_support_masks.py:6-8,27-42,83-88` and `pipeline.py:950-955,975-982,1123-1140`.

## 3. Inputs and required outputs

### Inputs

1. The 24 fixed world points and IDs.
2. The three fixed `T_cv,i` matrices.
3. `K`, raster size, `F4/F3`, and the branch label.
4. Frozen raster rules: integer pixel coordinates, `np.round`/nearest-even tie behavior, bounds, and nearest-depth z-buffer.
5. Frozen depth tolerance `TOL(z)=max(0.05, 0.05z)` metres from `compute_support_masks.py:17-18,38-40`.

### Outputs per camera and point

Record the branch label, `p_cv`, `p_g`, direct camera coordinates, projected real coordinates `(u,v)`, rounded pixel `(û,v̂)`, positive-z/bounds status, map point ID/depth, camera-space residuals, back-projection residuals, and depth residual. Report branch-level maxima, means, valid counts, and the fixed denominator; do not report PSNR or a learned-model metric.

## 4. Bidirectional identity equations

For each point and candidate transform `T`:

1. **Forward world-to-camera:** `p(T,X)=(T^{-1}X_h)[:3]`.
2. **Back camera-to-world:** `X̂(T,p)= (T [p;1])[:3]`.
3. **Camera identity error (for the transformed candidate):**

   `e_cam = || p_g - F3 p_cv ||_∞`.

   For the raw candidate, use the analogous identity `e_cam_raw = ||p_cv - (T_cv^{-1}X_h)[:3]||_∞`.

4. **World round-trip error:**

   `e_world = || X - X̂(T_branch,p_branch) ||_∞`,

   where `(T_branch,p_branch)` is `(T_cv,p_cv)` for `RAW_RAW`/`RAW_FLIP`, `(T_g,p_g)` for `FLIP_FLIP`/`FLIP_RAW`, and `(F4 T_cv, p(F4 T_cv,X))` for `WORLD_PRE_FLIP`.

5. **Raster projection:**

   `u = fx p_x/p_z + cx`, `v = fy p_y/p_z + cy`; round with the frozen `np.round` rule, then require `p_z>0` and `0≤û<640`, `0≤v̂<480`.

6. **Map depth residual:** at the matched point ID/pixel, `e_depth=|d_map-p_z|`.

The identity check is finite and passes only when the branch-specific camera error (`e_cam` for the transformed branch, `e_cam_raw` for the raw branch) and `e_world` are each `≤ 1e-6` metres. A raster/depth check additionally requires `e_depth ≤ TOL(p_z)` and exact point-ID agreement after rounding. The source retrieval gate's positive-z, bounds, and pixel-radius semantics are retained from `compute_support_masks.py:44-57`; this fixture uses exact-ID agreement to avoid hiding a frame error in a permissive radius.

## 5. Candidate branches

| Branch | Producer/map frame | Evaluator query passed to the map | Purpose |
|---|---|---|---|
| `RAW_RAW` | `T_cv`, `p_cv` | `p_cv` | Raw-frame neutralization alternative. |
| `FLIP_FLIP` | `T_cv F4`, `p_g=F3 p_cv` | `F3 p_cv` | Pipeline-transformed-frame hypothesis. |
| `FLIP_RAW` | `T_cv F4`, `p_g` | `p_cv` | One-sided evaluator omission control. |
| `RAW_FLIP` | `T_cv`, `p_cv` | `F3 p_cv` | Opposite one-sided control. |
| `WORLD_PRE_FLIP` | `F4 T_cv` | its direct camera point | Negative control for an unsupported world-frame flip. |

The first two branches are the only substantive alternatives. The one-sided and world-pre-flip branches are controls and cannot be selected as explanations merely because they fit one projection.

## 6. Fixed denominator and acceptance criteria

The denominator is fixed before any branch is inspected: `N_den = 3 cameras × 24 fixture points = 72` correspondences. Every branch reports all 72; invalid z/bounds or missing IDs count as failures, not denominator changes.

A branch **passes identity** iff every correspondence is finite and its branch-specific camera error plus `e_world` are each `≤ 1e-6`. It **passes raster/depth** iff identity passes, every correspondence has positive z and in-bounds rounded pixels, IDs agree, and every `e_depth` meets `TOL`.

- **Accept the raw-frame alternative** only if `RAW_RAW` is the unique branch passing both identity and raster/depth, while `FLIP_FLIP` fails at least one fixed criterion.
- **Support the transformed-frame/evaluator-hygiene explanation** only if `FLIP_FLIP` is the unique branch passing both and `RAW_RAW` fails.
- **Reject both explanations / mark unresolved** if neither substantive branch passes or if both pass. Do not choose a branch by a smaller mean error when the pass status is tied.

The source evidence fixes the `1e-6` identity threshold and `TOL`; **a numeric margin for “unique” beyond pass/fail is UNKNOWN and must not be invented.**

## 7. Required owner, H2, and runner gates

### Owner gate (UNKNOWN until assigned)

An owner must freeze and sign the fixture manifest containing the 24 coordinates, all three matrices, `K`, `F4/F3`, units, rounding, z-buffer, denominator, branch table, and source hashes. **Owner identity is UNKNOWN in this protocol; implementation stops until assigned.**

### H2 producer gate (UNKNOWN until source-pinned)

Before implementation or scoring, a source-pinned producer boundary must state whether pointmaps/surfels are emitted in `p_cv` or `p_g`. The visible callsite (`pipeline.py:975-988,1031-1037`) passes transformed poses, but producer internals are not established by the inspected sources. The `RAW_RAW` versus `FLIP_FLIP` fixture comparison must uniquely pass before H2 is resolved. If not, retain `H2_UNIDENTIFIABLE`.

### Runner gate (UNKNOWN until reviewed)

A runner may be implemented or used only after it can carry an explicit convention registry (c2w/w2c, axes, `F3`, depth units, `K`, crop/resize, rounding, tolerance, source hashes), preserve `N_den=72`, record the selected branch, and prevent target/future data from selecting transforms. The runner must expose a map-frame tag and must not overwrite frozen artifacts. The real C8 runner and any GPU/Slurm/receipt/flag action remain out of scope until these gates pass.

## 8. Stop rule

If the owner is unassigned, the producer frame is not source-pinned, the fixture has no unique passing substantive branch, any identity error is non-finite or `>1e-6`, or units/rounding/denominator cannot be frozen, stop with `H2_UNIDENTIFIABLE`. Do not implement, execute, rescore, or interpret real data; preserve `new_method_validated=false` and `novelty_authorization=NONE`.
