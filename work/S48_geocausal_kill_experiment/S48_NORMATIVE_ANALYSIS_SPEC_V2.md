# S48 source-only normative analysis/edit/guard specification V2

- Version: `V2`
- Status: `SOURCE_ONLY_CANDIDATE_PENDING_FRESH_INDEPENDENT_REVIEW`
- Execution authorization: `NONE`
- Novelty authorization: `NONE`
- Supersedes for future G7 binding: V1 normative package only; V1 files remain immutable history and do not authorize an arm.

This document and the sibling files `s48_analysis_reference_v2.py` and
`test_s48_analysis_reference_v2.py` are one indivisible candidate package.
All three whole-file SHA-256 values must be bound by a future G7 manifest and
freshly reviewed by a different author.  A disagreement between prose, code,
or tests is `BLOCKED`; an executor may not choose the favorable version.

The package is finite NumPy/statistics code.  It does not read C1/C2 payloads,
load a model, run a generation arm, implement the VMem hook, or establish
quality, causal effect, Benefit, method gain, or novelty.

## 1. Typed numeric domains

### 1.1 Saved model outputs

Every public API that consumes a saved model output accepts only an actual
`numpy.ndarray` with dtype exactly `np.uint8`, rank three, final dimension 3,
and nonzero height and width.  Production guards additionally require
`576 x 576 x 3`.  Lists, float arrays, normalized arrays, other integer dtypes,
alpha/grayscale images, and implicit casts are rejected.

Inside each public function the only conversion is

`x = u.astype(np.float64) / 255.0`.

The normalized array is never divided by 255 again.  Influence maps, image
guard RGB/chroma quantities, and Benefit losses therefore live in `[0,1]`
units.  For two outputs `u_edit,u_zero`, the direct effect is

`e(p) = mean_c |x_edit(p,c) - x_zero(p,c)|`.

One code-value in one channel has effect `1/(3*255)` at that pixel; one
code-value in all three channels has effect `1/255`.  Output MSE is

`sum_p w(p) * mean_c (x(p,c)-r(p,c))^2 / sum_p w(p)`.

Thus one code-value in all channels has MSE `1/255^2`; `delta_B=0.001` is in
this normalized squared-error domain.

### 1.2 Weight, validity, identity and scalar domains

- Weight maps are finite float64-compatible `H x W` values in `[0,1]`.
- Every public validity argument must be a `numpy.ndarray` with dtype exactly
  `np.bool_`; NaN, floats, `0/1` integers and lists are rejected rather than
  cast.
- Identity arrays must be `numpy.ndarray`, integer dtype, rank two, and use
  nonnegative IDs.  ID 0 is background only when valid is true.  An invalid
  pixel never enters a set or denominator.
- Counts and IDs use exact Python integers; booleans cannot stand for ints.
- All published scalars must be finite and in their stated mathematical
  domains.  Invalid inputs raise `SpecError`; no NaN sentinel is emitted.

## 2. Source edit, zero dose, quantization and consumer trace

The only reference API for both treatment and matched zero is
`apply_source_bundle(source_u8, family, sign, dose)`.  `source_u8` is strict
uint8 RGB.  `family` is `exposure_log_gain` or `texture_highpass`, `sign` is
the integer `-1` or `+1`, and dose is either exact `0.0` or one value in the
family's frozen ladder:

- exposure: `(1/64, 1/32, 1/16, 1/8)`;
- texture: `(0.05, 0.10, 0.20, 0.30)`.

Treatment and zero execute the same ordered stages:

1. decode strict uint8 once to `x=float64/255`;
2. compute the family edit with signed dose (dose zero is an identity inside
   this same branch, not a bypass);
3. clip elementwise to `[0,1]`;
4. compute `q = rint(255*x_clipped)` using IEEE/NumPy round-half-to-even;
5. cast the proved `[0,255]` integers to uint8;
6. decode those exact bytes once for consumer preprocessing;
7. create both consumer tensors in fixed order `semantic`, then `latent`, and
   record the complete seven-stage order and canonical tensor SHA-256 values.

The finite reference preprocessing is explicit: semantic is little-endian
float32 CHW in `[0,1]`; latent is little-endian float32 CHW in `[-1,1]` using
`2*x-1`.  Canonical hashes include a domain tag, dtype, shape and C-order
bytes.  This does not claim to implement VMem's real CLIP/VAE transforms.  A
future hook must freeze its real two preprocessors and prove the same
decode/edit/clip/quantize/reencode call graph, consumer order, tensor identity
and complete consumer inventory before G7 can pass.

For each family/sign, treatment and zero must have identical source bytes,
seed, noise/RNG initial state, snapshot, slot, target roster, adapter SHA and
consumer trace schema; dose is the only treatment field that differs.  Two
zero calls on identical bytes must return bitwise-identical uint8, tensor
bytes and both hashes.

## 3. Influence, replay and Localization

### 3.1 Influence

For every preregistered `family x seed x sign x target`, compute the target
direct map from the strict uint8 matched pair.  Let `E=mean_p e(p)`.  Let
`Q_neg` be the full-frame mean of the separately paired negative-source direct
map.  Let `tau_output=max(1e-6, all exact-replay full-frame distances for the
same seed and target)`.  The Influence value is

`I = E - max(tau_output, Q_neg)`,

and must satisfy `I >= delta_I = 0.5/255`.  Replay and negative maps are never
subtracted pixel by pixel from the target map.

### 3.2 Replay receipt identity

With exactly four replay instances indexed `0,1,2,3`, the replay input is six
typed `ReplayPairReceipt` objects.  Every receipt binds `seed`, `target`,
`replay_i`, `replay_j`, and symmetric guard metrics.  The required pair set is
exactly `{(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)}` with `i<j`; duplicate,
reversed, missing, extra, mixed-seed, or mixed-target receipts are invalid.

Every image-pair guard quantity is symmetric by definition:

- displacement uses the union of A-to-B and B-to-A mutual-match distances;
- RGB and chroma differences use absolute differences;
- sharpness is the bounded symmetric value
  `|vA-vB|/max(vA,vB,1e-12)`, with exact 0 when both are at most `1e-12`;
- saturation and tear use absolute differences.

Replay floors are componentwise maxima only after all receipts pass identity
and domain checks.  All fields must be finite and nonnegative; coverages are
in `[0,1]`, RGB/chroma/tear in `[0,1]`, saturation in `[0,100]`, and every P95
must be at least its corresponding median.

### 3.3 Raw-map Localization and independent negative veto

The sole Localization map is the raw target matched-zero direct effect `e`.
For pre-treatment support weight `W` and `epsilon=1e-12`:

`area(W)=sum W / |Omega|`

`mass(e,W)=sum W*e / (sum e + epsilon)`

`L_area(e,W)=mass(e,W)-area(W)` and `ER=mass/area`.

There is no per-pixel replay or negative subtraction.  Consequently, a
spatially uniform direct effect returns to the area baseline (`L_area` is zero
up to the explicit epsilon), regardless of where a negative control acts.
The V5 576x576 8-bit counterexample (target delta `(8,-5,4)` everywhere,
negative delta `(1,-1,1)` only outside an 86-row support) is a permanent test
and must fail Localization.

The negative pair is an independent numeric veto on the same predeclared
support, not a calibration map.  It passes only when all hold:

- `mean(e_neg)/mean(e_target) <= 0.25` (zero target mean is invalid);
- `L_area(e_neg,W) <= 0.01`;
- target Influence already passed;
- target Localization has `ER>1` and `L_area>=0.02`;
- each separately frozen shape and camera library has at least 199 candidates,
  true-support mass strictly above its lower median, and descriptive tail rank
  `<=0.05`.

The source-placebo library is reported separately.  With at least 19 eligible
masks it uses the same median/rank rule for source-specific language; with
fewer it is `NOT_IDENTIFIABLE`.  These ranks remain descriptive, not
randomization p-values.

## 4. Weight maps, histogram and validity

Binary topology is `W>0`, uses four-connectivity, and exposed-edge perimeter.
Positive-weight histograms exclude zeros.  For every positive weight the bin
index is exactly

`index = min(floor(10*W), 9)`.

This formula, rather than generated float edges, governs `.1` through `.9`
and `1.0`.  Context descriptors reject any validity dtype other than bool.

## 5. Output guard and its limited claim

`arm_guard_metrics` accepts only native `576x576x3 np.uint8` output pairs and
a `576x576` support.  Its frozen 9x9 patch matcher uses grid centers
`16+32k`, a +/-8 pixel search, deterministic tie order and mutual matches.
The report includes global, support-interior and a 32-pixel support-neighborhood
grid counts, expected counts, coverage, and symmetric median/P95 displacement.
Support and neighborhood must each contain at least one grid center.

Additional symmetric guards are full-channel outside-support RGB difference,
outside-support chroma difference
`0.5*mean(|delta(R-G)|,|delta(B-G)|)` (bounded in `[0,1]`), bounded symmetric
sharpness deviation, absolute saturated-channel-sample percentage difference
and absolute tear difference.  The fixed lower bounds are:

- global matches at least 50 and global coverage at least 0.75;
- support and neighborhood coverage at least 0.50;
- global/support/neighborhood median displacement at most 1 px and P95 at
  most 3 px, each compared with its same-field replay maximum;
- outside RGB and chroma at most `2/255`;
- sharpness deviation at most 0.10;
- saturation difference at most 1 percentage point;
- tear difference at most `2/255`.

Periodic tiling, a support-local shift, a pure-chroma outside change and a
low-texture frame are permanent adversarial tests.  Passing this finite guard
only excludes these registered gross displacement, coverage, RGB/chroma,
sharpness, saturation and tear alternatives.  It does not prove requested
camera/K correctness, geometry correctness, semantic preservation, absence of
all artifacts, or causal localization.  Numeric camera/K and blind visual
checks remain independent gates.

## 6. Reference and Benefit finite contract

### 6.1 Sensor synchronization

A `SyncCalibration` binds an integer reference epoch `t0_sensor_ns`, integer
offset `offset_ns`, signed integer drift `drift_ppb`, and nonempty measured
integer residuals.  Timestamp mapping is

`t_cal = t_sensor + offset_ns + round_half_even((t_sensor-t0)*drift_ppb / 10^9)`.

The rational rounding is exact integer round-half-to-even.  The calibration
passes only if `max(abs(residual_ns)) <= 10,000,000`.  A reference then needs
`abs(t_cal,R - t_cal,target) <= 10,000,000 ns`.

### 6.2 Camera eligibility and stable roster

Camera centers are finite 3-vectors; rotations are finite orthonormal 3x3
matrices with determinant +1; FoV is finite in `(0,180)` degrees.  Let
`b_O=||c_O-c_target||`; `b_O<=1e-6` is invalid.  A reference candidate passes:

- target-position ratio `||c_R-c_target||/b_O <= 0.10`;
- target rotation geodesic angle `<=2 degrees`;
- FoV difference `<=1 degree`;
- the synchronization rule above;
- exact dataset scene ID and the identity contract below.

For stable comparison, nonnegative finite degrees are converted to microdegree
integers and nonnegative finite ratios to ppm using the exact binary64
`as_integer_ratio()` followed by integer round-half-to-even.  No display
rounding participates.  The sort key is
`(|dt| ns, angle udeg, ratio ppm, FoV udeg, file SHA, candidate ID UTF-8)`.
Exact target cameras are eligible.  Ties are therefore resolved by file SHA
then ID.  Complete candidate and exclusion flow is retained.

### 6.3 Identity, view pairs, valid domains and holes

For Benefit replacement, identity is a triad `O,R,P`.  On `W>0`, the valid
denominator is `sum W` only where all three validity masks are true; invalid
pixels are excluded from the agreement numerator and denominator and are
reported separately as coverage.  Agreement is

`sum W * 1{ID_O=ID_R=ID_P} / sum W` over the tri-valid domain.

It must be at least 0.95, tri-valid weight coverage must be at least 0.70, and
the non-background ID sets of O, R and P over the tri-valid domain must be
identical.  For local O/R Benefit the same definitions apply to the O/R pair.

The non-dynamic RGB-warp residual receipts must contain exactly `O_R`,
`R_PREV_R`, and `R_R_NEXT`; replacement Benefit additionally requires `P_R`.
Each stores the three per-channel median absolute normalized RGB differences
on a strict bool valid mask, all `<=2/255`.  Duplicate, missing or extra view
pairs fail.

For each declared support or outside domain `D`, common validity is the exact
intersection of the named view-valid masks.  The receipt records
`domain_denominator=count(D)`, `common_valid_numerator=count(D & V_common)`,
`hole_numerator=count(D & ~V_common)`, `hole_denominator=count(D)`, coverage
and hole ratio.  No fill or interpolation changes these counts.  The domain
must be nonempty, coverage must be at least 0.70, and hole ratio at most 0.10.
An empty outside domain is invalid rather than silently omitted.

### 6.4 RGB losses and Benefit signs

All output/reference RGB arrays use the strict uint8 contract and the single
normalization in section 1.  Pixel loss is the mean of three squared channel
errors; spatial loss is the validity/weight-normalized mean of pixel loss.
No exposure normalization is applied.

`B_local = loss(Y_edit,R)-loss(Y_zero,R)` and
`B_matched = loss(Y_P,R)-loss(Y_O-reinsert,R)`.

Positive values favor the original appearance.  Each registered
family/seed/sign/target and each seed/target/P must separately satisfy
`B>=delta_B=0.001`; equality passes.  Outside noninferiority uses the same
formula and `loss(treatment)-loss(comparator)<=0.0005`.

### 6.5 Fair O-reinsert comparator

Ordinary F00 is only a pipeline diagnostic.  `Y_O-reinsert` and `Y_P` must
come from different fresh processes using the same frozen process-isolation
spec, source-adapter SHA, base snapshot, injection point, slot, token/tensor shapes, position and
source-ID interface, context length, quantization rule, consumer order,
initial noise SHA, RNG-state SHA, target roster SHA and trace-schema SHA.
Both must record exactly one semantic and one latent consumer call in the same
order.  The only permitted scientific difference is source identity/content
and the resulting encoded/consumer tensor hashes; attempt/process IDs must be
distinct.  A typed receipt validator enforces these invariants.

P does **not** need to be target-synchronous.  Its temporal eligibility is
only the preregistered memory-recency rule `|insertion_event_P-
insertion_event_O|<=2`.  Target synchronization applies to the independent
reference R, not P.  This removes the V5 ambiguous "per-P time gate".

## 7. What remains blocked

This V2 package closes finite definitions only.  It does not authorize a
model arm.  G7 must still bind and receive fresh independent PASS reviews for:

1. actual post-selection observer/replacement hook and complete downstream
   consumer inventory;
2. actual CLIP/LPIPS source-only dose gate weights and preprocessing;
3. renderer and 199-per-family placebo feasibility on the selected unit;
4. fresh-process supervisor, exact state/noise/RNG replay and complete arm
   manifest;
5. real two-consumer VMem preprocessors and tensor trace, not only this finite
   reference adapter;
6. real synchronization observations/calibration receipt, camera/depth/flow,
   identity labels, warps, dynamic masks, view-pair receipts, common domains
   and reference/replacement rosters;
7. numeric requested camera/K guard, natural-failure G0/G1, and a fresh review
   of the complete V6 preregistration plus this exact V2 package.

Until every gate passes: model loads `0`, S48 arms `0`, C1/C2 payload bytes
read by this package `0`, execution authorization `NONE`, method/novelty claim
`NONE`.
