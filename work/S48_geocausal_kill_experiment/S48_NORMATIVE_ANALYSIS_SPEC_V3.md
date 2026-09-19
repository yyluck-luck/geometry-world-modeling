# S48 source-only normative analysis specification V3

- Research package label: `S48_SOURCE_ONLY_V7`
- Status: `CANDIDATE_PENDING_FRESH_INDEPENDENT_REVIEW`
- Execution/model/arm/novelty authorization: `NONE`
- Normative siblings: `S48_GEOCAUSAL_KILL_EXPERIMENT_PREREGISTRATION_DRAFT_V2.md`, `s48_analysis_reference_v3.py`, `test_s48_analysis_reference_v3.py`
- Language boundary: RAIMA V3 SHA-256 `f0e5893ad4892f11f36641476f8858ca9347db4075b35b32faf5beaf4ce102aa`

Prose, implementation and tests form one indivisible candidate. Any disagreement is `BLOCKED`. A future reviewer must bind all four whole-file SHA-256 values. This code is a finite NumPy reference; it does not read experiment payloads, load VMem, run an arm, implement the production hook, or establish a scientific result.

## 1. Primitive domains

1. Saved output APIs accept only actual `numpy.ndarray`, dtype exactly `uint8`, shape exactly `576x576x3`. Lists, floats, other integer dtypes, grayscale and alpha are rejected.
2. The only output conversion is `x=u8.astype(float64)/255`. Direct effect is `mean_channel(abs(x_edit-x_zero))`; normalized RGB MSE is in `[0,1]` squared-error units.
3. Public validity masks require ndarray dtype exactly bool. Bound evidence is copied C-contiguous and marked read-only.
4. Bound support/placebo maps require ndarray dtype exactly float64, two dimensions, finite values in `[0,1]`. Topology uses `W>0` and four-connectivity.
5. Published scalar inputs must be real numeric types excluding bool; coercible strings and NaN/Inf fail.
6. IDs/counts requiring integers accept exact Python `int`, excluding bool and floats. SHA-256 strings are exactly 64 lowercase hex characters.
7. Canonical array identities contain a domain tag, exact dtype string, shape and C-order bytes. Canonical record identities contain a domain tag and newline-delimited, single-line fields.

## 2. Source transformations

Families and nonzero ladders are fixed:

- exposure log gain: `(1/64,1/32,1/16,1/8)`;
- texture high-pass: `(.05,.10,.20,.30)`;
- signs: exact `-1,+1`;
- zero: exact numeric `0.0` through the same family branch.

The seven stages are `decode_uint8`, `family_edit`, `clip_0_1`, `multiply_255_round_half_even_uint8`, `reencode`, `semantic_consumer`, `latent_consumer`. Semantic and latent finite tensors are constructed once in that order and hashed. `select_minimum_source_dose` requires the exact dose/sign ladder and chooses the first dose whose two signs pass the frozen source gates.

This finite transform is not the production CLIP/VAE adapter. Production remains blocked until an independently reviewed hook proves the real consumer inventory, preprocessing, call order and tensor identities.

## 3. ReplayLedger and InfluenceReceipt

### 3.1 Replay

`build_replay_ledger` takes exactly four native uint8 outputs, one native float64 support and five state identities. It stores read-only copies. It constructs exactly six lexicographically ordered pairs. For every pair it derives:

- the two bound output SHA values;
- full-frame mean direct-effect distance;
- all symmetric `ArmGuardMetrics` from the same outputs and support;
- a canonical pair SHA.

`validate_replay_ledger` re-hashes the four outputs and support, recomputes all six distances and all guard metrics, verifies exact pair set and order, then derives `tau_output=max(1e-6,max distance)`. No caller-supplied replay scalar is accepted downstream.

### 3.2 Influence

`CellKey=(source_id,target,seed,family,sign)`. `ArmIdentityReceipt` binds state, noise, RNG, snapshot, target roster, source adapter, consumer schema and slot.

`InfluenceReceipt` embeds the exact arm identity, replay ledger and six read-only native outputs. Its validator re-derives output hashes, raw target/negative/positive maps, map hashes, means, replay tau,

`D_target=mean(target)-max(tau,mean(negative))`

and the same positive-control value. Threshold is `Delta_I=0.5/255`. Public free-scalar Influence APIs do not exist.

## 4. PlaceboMaskLedger and SupportEffectReceipt

`PlaceboMaskLedger` is family typed as shape, camera or source. It binds generator SHA, shape, ordered compressed float64 mask bytes, each raw-mask SHA, each compressed SHA and one canonical SHA. Validation decompresses and re-hashes every mask; duplicates, zero/full masks, count changes and reorderings fail.

`tail_from_mask_ledger` re-derives true mass and every placebo mass from a raw effect map, true support and typed ledger. The true support may not itself appear in the ledger. Lower median is the stable sorted element at `(n-1)//2`; descriptive tail rank is `(1 + count(placebo_mass>=true_mass))/(n+1)`.

`SupportEffectReceipt` embeds its exact Influence, read-only support, shape ledger and camera ledger. The public builder accepts no effect map or tail scalar: it derives target and negative raw maps from Influence outputs. It requires support equality with ReplayLedger support. Validation recomputes both tails and every scalar.

The support alignment screen passes only when:

- Influence target and positive control pass;
- target `ER>1` and `L_area>=0.02`;
- negative mean ratio `<=0.25` and negative same-support `L_area<=0.01`;
- shape and camera counts are each `>=199`, true mass is strictly above lower median, and tail rank `<=0.05`.

A uniform direct map returns to its support-area baseline and fails. Screen failure only licenses `SEM_DESCRIPTIVE_STOP`; this V7 does not implement or identify RAIMA harmful SEM.

## 5. Output guard

The production-size symmetric guard keeps V6 thresholds and exact domains. It covers global, support and 32-pixel support-neighborhood patch grids, mutual-match coverage, median/P95 displacement, outside RGB/chroma, symmetric sharpness, saturation percentage and tear. Replay floors are componentwise maxima from a validated ReplayLedger. Passing excludes only registered gross alternatives; it does not prove camera, geometry, semantics or artifact absence.

## 6. Reference identity and uncertainty

### 6.1 Exclusion and roster

`ObservationExclusionLedger` embeds exact target, memory and conditioning capture/file identities. Target answer reuse in memory or conditioning fails. Duplicate identities within each roster fail.

`ReferenceRosterReceipt` embeds the exclusion ledger and the complete supplied candidate flow. An eligible candidate must be distinct from target by both capture and file, absent from memory and conditioning by both identities, same scene, within calibrated `10,000,000 ns`, position ratio `<=100,000 ppm`, rotation `<=2,000,000 microdegrees`, FoV difference `<=1,000,000 microdegrees`, and pass exact O/R identity, registered view pairs and O/R support/outside domains. Identity support must equal the valid-domain support. Candidate/capture/file identities are unique. At least three eligible observations are mandatory; the single-reference API always raises `SpecError`.

### 6.2 Bound roles and masks

`IdentityAgreement` embeds read-only support, each role's integer identity map and bool validity map, hashes and re-derived agreement quantities. Allowed roles are exactly O/R or O/R/P.

`ValidDomainReceipt` embeds the read-only domain mask and every role validity mask. Allowed ordered role tuples are exactly O/R, O/R/P or O/R/A. Validation re-hashes all masks and recomputes denominator, common-valid numerator, holes, coverage and hole ratio. A one-role or arbitrary-role receipt cannot pass.

### 6.3 Natural-revisit uncertainty

`ReferenceUncertaintyReceipt` embeds a validated roster, read-only support, every eligible reference RGB and validity mask. It requires exact coverage of the eligible capture roster and derives every unordered pair loss on common-valid support:

`Delta_ref=max(pairwise losses)` and `Delta_U=max(.001,2*Delta_ref)`.

Primary RCSU eligibility additionally requires `Delta_ref<=.001`. These references must be separate observations, never memory/conditioning items. Current local TUM/C1/C2 cannot supply the required synchronized triple, so this contract is not currently executable there.

## 7. P replacement selector

The CAL quality metric is exactly `CAL_SOURCE_REPROJECTION_RGB_MSE_V1`. `QualityCalibrationReceipt` binds a CAL manifest, at least eight sorted values and nearest-rank Q1/Q2/Q3 at index `ceil(q*n)-1`. `quality_quartile` uses right-side boundary insertion, so a cutpoint tie belongs to the higher quartile.

Binary IoU is `count((W_O>0)&(W_P>0))/count((W_O>0)|(W_P>0))`. Weighted area ratio is `sum(W_P)/sum(W_O)`.

`build_replacement_roster` returns every supplied candidate in canonical `(insertion_event,source_id UTF-8,file SHA)` order and retains every eligible P. Eligibility is the conjunction of: P distinct from O; same scene; exact integer insertion recency `<=2`; camera thresholds; binary IoU `>=.80`; weighted area ratio in `[.90,1.10]`; same CAL quartile; exact O/R/P identity; required four view pairs; exact O/R/P support/outside domains; P support agreement across candidate, identity and domain evidence. Empty eligible roster fails.

O-reinsert and P-replacement receipts must share every registered non-content invariant, including process isolation, adapter, base snapshot, injection point, slot, shape, position/source interfaces, context length, quantization, consumer order/calls, noise/RNG, target roster and trace schema.

## 8. UtilityReceipt

Allowed `UtilityKey.estimand` values and exact meanings are:

- `LOCAL_EDIT_PREFERENCE`: treatment edit, comparator same-path zero; family/sign required; replacement blank.
- `MATCHED_REPLACEMENT_RCSU`: treatment P, comparator O-reinsert; replacement ID required; family blank/sign zero.
- `SOURCE_ABSENCE_RCSU`: treatment absence, comparator O-reinsert; replacement ID exactly `ABSENT`; family blank/sign zero.

`UtilityReceipt` embeds the reference-uncertainty receipt, treatment/comparator/reference outputs, validity mask and support. All arrays are read-only. Support must equal the uncertainty support. Validator re-derives all hashes and

`U=loss(treatment,R)-loss(comparator,R)`

on support and outside. `signed_class` is `+1` for `U>=Delta_U`, `-1` for `U<=-Delta_U`, otherwise 0. Outside passes iff its absolute difference is at most `max(.0005,2*Delta_ref)`. The three keys are interpretation-distinct. Free Benefit scalar APIs and the ambiguous old names fail closed.

An absence-key result remains an operational contrast until a future execution receipt proves that source presence is the only changed factor. It is never inferred from local-edit or replacement values.

## 9. Exact sequential ledger

`ExperimentPlan` requires one or more targets, exactly five unique seeds, fixed family/sign tuples, one or more eligible P, at least three reference captures, and exact reference/replacement receipt hashes.

`evaluate_sequential_ledger` verifies:

1. the exact `target x seed x family x sign` Influence grid;
2. same replay, arm identity and three zero-output identities within each target-seed;
3. stop on any positive-control failure;
4. AOIG candidate only when every registered target edit is below threshold; mixed results stop as intervention sensitivity;
5. support evidence is forbidden before all target cells pass, then must cover the exact same grid and exact Influence hashes;
6. support failure stops as descriptive SEM and forbids utility;
7. utility then covers the exact local-edit, every-P and optional absence grid for every reference and seed;
8. outside veto; five-seed median magnitude; at least 4/5 same sign; all references same sign.

It emits one typed terminal action. Its word `COMPLETE` means only that the supplied source-only ledger is structurally complete. It never means a model experiment or paper claim is complete.

## 10. Data feasibility and allowed conclusion

The independent metadata receipt at `/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/resumption_20260908/reference_time_feasibility.json`, SHA-256 `02dd1b304fc9e84bc4f99cd3b3ccfcf0fdee0685f7f14907edaa21959e07c8eb`, reports that the current local streams cannot supply three independent references inside the required time window. This blocks complete RCSU/Benefit on B0/C1/C2 regardless of source-code test success.

The only allowed package conclusion is source-only: exact frozen code passed finite synthetic tests in the recorded interpreters, subject to fresh independent review. Real-data access, model runs, quality, AOIG, harmful SEM, RCSU, method gain and novelty all remain zero/unestablished.
