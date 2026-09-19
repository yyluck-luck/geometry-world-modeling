# M-PAI-01-P0: cross-context provenance-localization pilot

- Candidate stable ID: `M-PAI-01` (Provenance-localized Appearance–Geometry Interaction).
- Pilot stable ID / revision: `M-PAI-01-P0 / v1`.
- Recorded time: 2026-09-16 01:54:04 +08:00, from `clock.curr_time` (2026-09-15 17:54:04 UTC).
- Status: `PREREGISTRATION_WRITTEN_NOT_EXECUTED`.
- Scope: one retrospective-development, saved-output diagnostic. No model invocation, rendering, SSH, future-GT scoring, or new data decoding is part of this pilot.
- Scientific status: `new_method_validated=false`; `novelty_authorization=NONE`.

## 1. Question, correction, and falsifiable hypothesis

The broad candidate proposes that local provenance competition can interact with appearance conditioning and contribute to ghosting. **This cache cannot test the appearance interaction.** It contains depth and renderer-provenance arrays, with no generated RGB, appearance factor, latent trajectory, or externally measured geometric error. P0 tests only a necessary localization premise:

> For a fixed source-block swap and target camera, the locations where renderer provenance switches in one frozen background context predict where the depth perturbation concentrates in the other frozen background context, beyond reference-depth, local depth-gradient, source-ordinal, visibility-boundary, and coarse image-location controls.

Two corrections supersede the first informal P0 suggestion:

1. `source_pixel_identity` is **source ordinal × 224 × 224 + source row × 224 + source column**. A change can be a different pixel from the same source. It is not automatically a cross-source identity change.
2. An identity-flip mask and a depth difference computed from the same two rendered outputs are coupled by the renderer. Same-context enrichment is not a decisive test. The primary test transfers the mask from context 0 to context 1, then reverses the direction. Same-context results are descriptive only.

The cache is a deterministic known-camera geometric renderer using saved proposals, not a VMem diffusion/video output. Positive P0 evidence would retain a localization diagnostic; it would not establish a causal appearance mechanism, future benefit, or a new algorithm.

## 2. Exposure declaration and present data boundary

S100/S103 aggregate results were seen before this document. S103 already reports 72 pair-context-target rows and `MECHANISM_UNRESOLVED`. Consequently this is a prospective specification of a **new statistic on previously seen development data**, not an untouched-test preregistration. No result of the statistic below has been computed by this agent.

The current ledger records scene_13 as calibration/development and scene_14 as an independent-scene candidate whose 239,153,034-byte archive was hashed before extraction (`d3011fe0c00c133b31899ed24c7bf49a00541a0c39d218c3b5647b3d781531b6`). This document neither opens those archives nor changes Gate0 readiness. The scientific baseline remains subject to the corrected Gate0/implementation contract. Estimated mapping poses must not be called independent motion-capture ground truth.

## 3. Required identities and allowed inputs

All paths below are relative to `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling`.

| Input | Required SHA-256 | Role |
|---|---|---|
| `work/S100_context_matched_swap/predict_01/SEAL.json` | `d488589333c5d901713a5535c70935380dcbc18aabd01db425f1c0f52dd8e78f` | Prediction-seal identity |
| `work/S100_context_matched_swap/FREEZE.json` | `c39b7dc2be955681489296dacda0db7712dbd4f3c1e825589e16b5ade1e2855f` | Inherited development freeze |
| `work/S100_context_matched_swap/select_01/SELECTION.json` | `d41cd7309d845a5df0962a0de05e4dc689a66cfdaa16c891d37148ec63f99d57` | Pair, source, context, arm, seed and row mapping |
| `work/S100_context_matched_swap/predict_01/DESCRIPTION.json` | `c1b1516fe596dfc7ff701813a7562ee336ce50cf6f3a75b5b2bb6f9d1bc70320` | Renderer/no-model/no-GT provenance |
| `work/S100_context_matched_swap/predict_01/predictions.npz` | `0cb92a118e25356ae845c82e3eedea2efeff71ee657c7d5ca5ceb384cf50e32e` | Only scientific array payload allowed |
| `scripts/s15b_memory_consumer.py` | `4541af96cfba4a2c7770dd5d9c068f2906e2912794bcb943b39ca15501c4f061` | Read-only interpretation of provenance and renderer semantics; do not execute/import it |
| `work/S103_prediction_geometry_decomposition/run_01/INPUT_MANIFEST.json` | `8117e6ed184be4c0c5d45e0943772d03f63bffe21ce17bff6d5a0f32fec6c289` | Contextual link to prior diagnostic |

At execution, verify these identities, bind the pilot script and this document's hash, and check the seal's `freeze_sha256` and `files` entries. Validate only the listed input closure. Do not recursively open every path in inherited manifests: some inherited paths reference GT. A hash read is permitted for the allowed sealed cache; no GT path is permitted even for hashing.

### Arrays that must exist

- `predictions.npz/depth_m`: float64, shape `(36, 4, 224, 224)`, finite and nonnegative; zero denotes missing prediction.
- `predictions.npz/source_pixel_identity`: int64, identical shape; values in `[-1, 4*224*224-1]`; `depth_m > 0` must equal `source_pixel_identity >= 0` exactly.
- `SELECTION.json/conditions`: 36 unique row identities. Group by `(pair_id, source, context)` and then arm; require exactly one `low` and one `conf`. Do not infer pairs from row adjacency.
- Nine pair IDs `0..8`, sources `0,1,3` with 2/4/3 pairs respectively, contexts exactly `0,1`, and target-axis indices bound to target IDs `20,21,22,23` by the archived producer. Both arms of each pair/context must share the recorded seed.

No `selection.npz`, source RGB, source geometry, GT depth, pose payload, model checkpoint, or renderer rerun is needed. Missing fields or identity failures produce `UNTESTABLE_INPUT_CONTRACT`; they do not authorize regeneration.

## 4. Fixed analysis domain and transfer units

A map-case is `(pair p, target t, reference context a, recipient context b=1-a)`. There are exactly `9*4*2=72` planned map-cases. They are repeated measurements from one seen scene, not 72 independent samples.

For each pair and target, define `D` as pixels with finite positive depth and nonnegative identity in **all four** cached outputs: low/conf × contexts 0/1. D is shared between directions. This estimates localization conditional on common prediction support; it cannot establish missing-pixel quality. Report all four support counts, common-support count, and excluded-support count separately.

If D is empty, stop this complete pilot as `UNTESTABLE_COMMON_SUPPORT`. Never silently remove a target, source, context, or pair.

For a direction `a -> b`, define on D:

```
M_a(x) = [I_low,a(x) != I_conf,a(x)]
e_b(x) = abs(Z_low,b(x) - Z_conf,b(x))
W_b    = sum_D e_b(x)
C_obs  = sum_D M_a(x) * e_b(x) / W_b
```

If `W_b <= 1e-12 metres`, record `NO_MEASURABLE_RECIPIENT_CHANGE`, set the primary contrast for this map-case to zero, and retain it in all denominators. If M is empty, the contrast is also zero. The 1e-12 value is a numerical-zero guard, not a physical accuracy threshold.

## 5. Matched-placebo construction

Build the matching covariates from the **reference context's conf output only**, plus the common-support domain. Do not use recipient depth magnitudes, recipient gradients, e_b, same-context depth differences, or future answers to form strata or pick placebos.

For every x in D, form one categorical stratum from all of:

1. Reference source ordinal: `floor(I_conf,a / 50176)` in `{0,1,2,3}`.
2. Reference depth bin in metres: `(0,0.5]`, `(0.5,1]`, `(1,2]`, `(2,4]`, `(4,infinity)`.
3. Reference relative-depth-gradient bin. Compute `g(x)=max_y abs(Z_conf,a(x)-Z_conf,a(y))/max(Z_conf,a(x),1e-12)` over existing four-neighbours y in D. Use bins `{0}`, `(0,0.01]`, `(0.01,0.05]`, `(0.05,infinity)`, and `no_valid_neighbour`.
4. Common-support boundary: `interior` if all four grid neighbours exist and belong to D; otherwise `boundary`.
5. Coarse target location: `(floor(row/56), floor(col/56))`, giving 16 fixed image tiles.

For stratum s, let n_s be its pixel count and m_s its number of reference-mask pixels. A placebo uniformly samples exactly m_s of its n_s pixels without replacement, independently between strata. Thus every placebo has the same total mask area and exact joint counts of source ordinal, depth bin, depth-gradient bin, boundary class, and image tile.

Use the exact matched-null expectation for the primary statistic, avoiding Monte Carlo noise:

```
C_null = sum_s (m_s / n_s) * sum_{x in s} e_b(x) / W_b
E_case = C_obs - C_null
```

Generate exactly 199 explicit masks per case only for placebo-distribution diagnostics and implementation readback. Use NumPy PCG64 with `SeedSequence([20260916, 101, p, t, a, replicate_index])`; sort strata and pixel indices lexicographically before sampling. Compare their mean with the analytic expectation as a diagnostic, not an extra success test. The analytic formula is authoritative.

Record mask area, stratum counts, and the fraction of M in strata where `0 < m_s < n_s`. If every case has zero such fraction, stop as `UNTESTABLE_NO_MATCHED_RANDOMIZATION`. Do not merge bins or weaken matching after results are seen.

**Permutation correction:** applying a global bijection to the source labels leaves an equality/inequality mask unchanged and is not a valid placebo. Permuting the paired identity tuples within the fixed strata induces the same matched-mask null above; it is not a second independent test. Pixel sampling does not preserve connected-component shape, so the conditional placebo reference is descriptive and must not be used as a causal randomization p-value.

## 6. Primary contrast and dependence-aware summaries

Compute `E_case` for both directions and all four targets, retaining numerical-zero cases as zero.

1. Pair score: average the eight map-cases for each pair.
2. Source score: average pair scores within each source (2, 4 and 3 pairs).
3. **Primary contrast T:** unweighted mean of the three source scores. This prevents source 1's larger number of selected pairs from dominating the result.

Report T, every source score, every target score, each transfer-direction score, and leave-one-pair/source/target-out recomputations. Target and direction scores retain equal-source weighting.

The resampling unit is the **complete pair ID**, keeping both contexts and all four targets together. For a descriptive stability interval, use 10,000 bootstrap replicates that sample the original number of pair IDs with replacement **within each source**, then recompute equal-source T. Seed: PCG64 `SeedSequence([20260916,101,10000])`. Report the 2.5%/97.5% percentile interval as a *within-cache pair-resampling stability interval*. Do not call it a scene-population confidence interval. There is only one scene and three correlated source groups; neither pixels nor target frames are independent sampling units.

## 7. Secondary checks that cannot replace the primary result

- Split M into `cross_source_switch` (source ordinals differ) and `within_source_pixel_switch` (ordinal equal, full identity differs). Report area and transferred depth-change mass for both. A signal driven entirely by within-source switches cannot be described as cross-source conflict.
- Report same-context C solely to show the structural coupling; a positive same-context result with failed cross-context transfer is a negative P0 outcome.
- Report signed depth differences descriptively, without calling their sign improvement or error: no geometric truth is available here.
- Report conditional-support exclusion and numerical-zero cases. No valid-only improvement or ghosting reduction can be claimed.
- The archived exact replay covers one deterministic renderer case. It does not establish diffusion repeatability; this pilot executes no new replay.

## 8. Decision and kill criteria

Output `PILOT_LOCALIZATION_PREMISE_SURVIVES` only if all of these are true:

1. Input/domain contract passes and the primary contrast T is strictly positive.
2. All three source scores, both direction scores, and all four target scores are strictly positive.
3. All leave-one-pair/source/target-out primary contrasts are strictly positive.
4. The lower endpoint of the descriptive pair-resampling stability interval is above zero.
5. At least one map-case has measurable recipient change and matched-randomization capacity.

Otherwise output `PILOT_LOCALIZATION_PREMISE_NOT_SUPPORTED`, preserving which condition failed. Do not rescue a failure by changing masks, bins, targets, source weights, seeds, zero handling, or the primary endpoint. An input/domain failure is `UNTESTABLE`, not scientific falsification.

These conditions decide whether the narrow localization premise merits further testing. Even survival leaves `APPEARANCE_INTERACTION=UNKNOWN`, `FUTURE_BENEFIT=UNKNOWN`, `CAUSAL_MECHANISM=UNESTABLISHED`, and `NOVELTY=UNASSESSED`. Failure stops M-PAI-01's present localization route; do not re-label the same outputs as a positive SOCF-A or FGB-Future result.

## 9. Cost and immutable execution boundary

- GPU hours: **0**. Neural-model/renderer calls: **0**. GT scoring calls: **0**.
- Planned resources: one local CPU process, maximum 10 minutes and 2 GiB resident memory. Record actual runtime and peak memory; stop on the cap without increasing it automatically.
- A future pilot runner may read only the allowed input list, create a fresh output directory, and save input hashes, case/stratum statistics, primary/secondary summaries, random seeds, numerical-zero and support counts, decision reasons, runtime, and independent arithmetic readback.
- No old artifact or main research plan is changed. This preregistration is the sole artifact written by the present task. It is not an execution receipt.

## 10. Held-out confirmation is a separate experiment

P0 cannot confirm the broad appearance–geometry hypothesis. Confirmation requires a separately frozen, qualified held-out protocol and the following **additional arrays/evidence**:

- Actual generated RGB for all four geometry × appearance arms, with identical target cameras, source membership, common exogenous noise, resolution, steps, output count, and compute accounting.
- A precisely specified appearance-only manipulation; its inputs cannot contain target RGB/depth answers. Recompute every descendant naturally after each intervention.
- Source identity/provenance or independently frozen support maps from the actual VMem consumer. The toy-renderer identity map cannot be silently substituted.
- Reference sensor depth and qualified K/pose/registration semantics for scorer-only use after prediction sealing; estimated-pose and frozen-depth-estimator limitations must remain explicit.
- Independent scenes, with scene_13 kept as calibration/development and scene_14 used only after qualification and exposure audit. A single scene14 result is a falsification pilot, not cross-scene confirmation.
- A predeclared geometry × appearance difference-in-differences contrast with geometry/ghosting outcomes, replay controls, ordinary consumer and matched-cost controls, and scene-level replication. No threshold or manipulation may be selected using scene14 outcomes.

Existing nearest-work reports already cover geometry-conditioned rendering/cross-frame fusion (ViewDiff), long-term spatial memory (VMem), and geometry-prior contamination (GeometryCrafter). This document makes no first/novel claim. Its contribution to the workflow is a cheap, falsifiable precursor that can fail before any expensive hypothesis experiment.

## 11. Read-only evidence used in preparation

- `work/S103_prediction_geometry_decomposition/RESULTS.md` and `run_01/INPUT_MANIFEST.json`: already-seen 72-row development boundary.
- `work/S100_context_matched_swap/select_01/SELECTION.json`, `predict_01/SEAL.json`, `DESCRIPTION.json`, `FREEZE.json`, and producer source: exact cache pairing and identities.
- `scripts/s15b_memory_consumer.py:67-80,101`: flattened source-pixel provenance and deterministic z-buffer semantics.
- `RESEARCH_MEMORY.md` current Gate0/3DMatch entry and `work/S102_gate0_3dmatch/SOURCE_ONLY_ACQUISITION_PROPOSAL_20260916.json`: acquisition-only boundary.
- `work/agents/innovation_round5_mechanism_shift_20260916.md` and `innovation_reviewer_round_20260916.md`: the appearance-interaction mechanism remains unverified and distinct from method success.

Preparation performed metadata/source reads and wrote this document only. It did not execute the proposed statistic, load model weights, contact SuperPOD, decode scene14, or open GT.
