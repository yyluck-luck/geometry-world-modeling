# SOCF-A-v2 bounded innovation update (2026-09-16)

## Status

`CONDITIONAL_HYPOTHESIS_ONLY`; no experiment, novelty authorization, or validation. Current project declarations remain `new_method_validated=false` and `novelty_authorization=NONE`.

## Hypothesis

With a fixed memory budget and the complete VMem consumer path, a history-only source-conflict feature (reprojection/depth disagreement, visibility conflict, and source provenance) may predict the signed change in a later held-out future RGB-D/pose loss when one source is replaced. An abstention rule should suppress cases whose direction is unstable.

## Closest mechanisms and competing explanation

The project frontier scan identifies pose-indexed bounded memory/redundancy retrieval (ReWorld), geometry/information/coverage selection (GIM-World/Mem-World), and future-aware KV selection/merging (Future Forcing) as close mechanisms. SOCF-A is distinct only if it is a source-level, history-only signed intervention forecast with abstention. A simpler explanation is that the score is a renamed pose-distance, visibility/coverage, confidence, or source-identity proxy; gains may arise from changed valid coverage, z-buffer/source identity, recomputation, or replay noise.

## Smallest authorized experiment after prerequisites

Only after an explicit formal Gate0 receipt (current status NOT_RUN/BLOCKED) and a compute-node container smoke pass: freeze one qualified held-out query, k=4 pool, camera command, non-target sources, checkpoint/config/runtime hashes, and common RNG. Run baseline plus one predeclared source keep-to-pose/support-matched replacement, recomputing every downstream consumer descendant. Use three exact replays with common seeds/noise, seal predictions before mounting future RGB/depth/pose scorer inputs, and report paired future depth/reprojection/pose loss with pre-seal denominator specification; realized valid-pixel counts only post-seals.

## Kill criteria

Kill or downgrade SOCF-A if the intervention delta is no larger than exact-replay variation, direction changes across replays, source identity/coverage explains the effect, residualized conflict adds no value beyond pose/visibility/coverage/confidence, compute differs, leakage occurs, or future depth/pose/tail loss does not improve. One scene/query cannot support a method claim.

## Current decision

Do not run this pilot. The next prerequisite remains an executable digest-pinned CUDA isolation probe followed by the selector-free VMem baseline and same-pool controls.

## Adversarial refinement: support/owner confounder

A signed intervention delta can be explained entirely by changing the renderer's active support/owner map: valid-pixel count, z-buffer visibility, source provenance, and evidence density change when a source is replaced. The project’s S99 evidence already showed low source-identity agreement and no reliable low-disagreement advantage, so this confounder is concrete.

The required control is a Support/Conflict-Matched Control (SCMC): same candidate pool, k, forward count, seed/noise, and budget, with exact pre-intervention target support-mask equality whenever possible, plus owner-count, pose-distance, and confidence matching. If no exact match exists, mark `UNTESTABLE_SUPPORT_MATCH`; do not relax to an approximate match and claim causal separation. Recompute all consumer descendants and compare paired future losses on one full denominator. Kill if SOCF and SCMC move equally, if the effect is within replay variation, or if coverage/owner/confidence controls explain it.

## Second adversarial refinement: branch-dependent RNG

Matching an integer seed does not guarantee matching noise when the intervention path consumes a different number or order of random draws. A signed SOCF delta can therefore be execution stochasticity rather than source conflict, independently of support/owner changes.

Use a Noise-Locked Paired Replay Control (NLPRC): freeze and hash initial noise tensors, Python/NumPy/Torch CPU/CUDA RNG states, deterministic flags, schedule, execution order, forward/output counts, candidate pool, camera, and budget; restore identical snapshots before retain and intervention arms. Include a byte-identical no-op route to estimate replay variation. Kill or downgrade if the no-op exceeds the replay envelope, locked replays flip sign, or the SOCF effect fails to exceed the predeclared 95% no-op envelope. If the no-op cannot run in the same container, report `UNTESTABLE`.

## Third adversarial refinement: source-ID permutation placebo

A separate candidate-pool/source-identity control is required. Freeze one sealed candidate pool per query, source tensors/features, IDs/order, k/slot budget, camera/history, checkpoint/config, complete downstream recomputation, cost, and NLPRC snapshots. After sealing the SOCF score vector, permute only the score-to-source-ID assignment across predeclared permutations while preserving support, pose, coverage, confidence, and residual values. Seal outputs before future scoring.

The provenance claim survives only if the source-aligned arm exceeds the permutation-placebo envelope at matched support/coverage/owner and cost. Kill or downgrade if the gain survives permutation, fails to separate from the placebo, or source-ID mapping/descendants cannot be audited. If the control cannot run, report `UNTESTABLE`.

## Fourth adversarial refinement: post-selection denominator bias

SCMC, NLPRC, and SIPP do not prevent complete-case bias if unmatched support cases, failed placebos, abstentions, invalid outputs, or difficult queries are silently dropped. Before intervention or future scoring, hash the full eligible target-query universe. Use one intention-to-treat denominator and identical target set for SOCF, controls, and placebos; retain every failure in a feasibility ledger as `UNTESTABLE` or failure. Complete-case analysis is secondary only.

Kill or downgrade if gains appear only after exclusions, arm/query inclusion differs, or the full-denominator effect is within zero/replay bounds.

## Current distinction and downgrade boundary

After a formal Gate0 receipt (currently NOT_RUN/BLOCKED), SCMC, NLPRC, SIPP, and ITT denominator controls, the only defensible distinction is an auditable source-level signed intervention estimand: a history-only predictor of the change in an externally supplied, held-out future RGB-D/pose reference loss when one named memory source is retained versus replaced, with complete consumer recomputation and abstention for unstable directions.

This is sharper than ordinary confidence/coverage selection because the target is a signed future counterfactual, but current reviews identify close threats including CUE-R, ViewRope/SplaTAM, and cache abstention. Even if all controls pass, treat SOCF-A as a reproducible measurement/selection protocol unless residualized held-out future gains replicate across scenes and horizons. If not, downgrade/reject the method claim and use FGB-Future or a negative evaluation.

## Minimal decisive package after all controls

The smallest future protocol-evidence package is a cross-fitted signed-source intervention package; any one-query check is PILOT_DIAGNOSTIC_ONLY and cannot establish protocol evidence. Prerequisites are `formal_gate0_status=PASS` (explicit model-forward receipt required), digest-pinned CUDA/container, selector-free VMem baseline, legal future RGB-D/pose scorer, two calibration trajectories, one untouched held-out trajectory/scene, and auditable descendant recomputation.

Freeze candidate pool/IDs/order, k=4, cost, target cameras, checkpoint/config/runtime hashes, conflict features, NLPRC states, abstention threshold, and SIPP permutations. On calibration trajectories, run three locked F0 retain versus predeclared F1 replacement replays and fit control-only versus control-plus-conflict models. On held-out targets, compare SOCF, retain baseline, SCMC, NLPRC no-op, and SIPP placebo under one hashed ITT denominator and pre-seal denominator_spec_hash; the scorer emits realized_denominator_hash only after prediction_sealed=true. Kill if effects are replay-sized/sign-unstable, add no cross-fitted value beyond controls, fail matched-cost comparisons, appear only after exclusions, or improve RGB while future geometry worsens. Otherwise retain only as a measurement protocol, not automatically as a new method.

## Consumer-recomputation preflight

A source swap can leave stale mutable state (cached latents/KV, attention or renderer buffers, or source-pixel identity), making F1 an incomplete recomputation. Before interpreting any effect, run F0->F1 and F1->F0 from identical serialized pre-consumer state in fresh processes. Hash memory input, encoded tokens/KV, attention outputs, renderer support/owner/provenance, and final RGB/depth/pose outputs. Require order-invariant arm hashes and regeneration/audit of every downstream node of the replaced source.

Stop as `INVALID_CONSUMER_RECOMPUTATION` if arm order changes outputs, stale buffers are reused without an audited exemption, or final pixels cannot be traced to frozen source IDs.

## Implementation preflight: stale-state closure

The complete-path intervention must serialize the pre-consumer state and run retain/replacement arms in fresh processes in both orders. Stage hashes must cover memory input, latent/KV, attention, renderer support/owner/provenance, and final outputs. Any order dependence or stale mutable state invalidates the estimand before future scoring.

## Administrative simplification only

No scientific gate can be removed: Gate0/container legality, selector-free baseline, SCMC, NLPRC, SIPP, ITT denominator, and order-reversal provenance address distinct failure modes. The only safe simplification is one immutable preflight manifest and shared frozen input/arm matrix reused by all arms. Preserve every arm, fresh-process checks, full denominator, and explicit `UNTESTABLE` outcomes.

## Immutable preflight manifest schema

Administrative schema fields are frozen for future use: manifest/study status; authorization and gate receipts; environment/code/container/checkpoint/config/dependency/runtime/hardware/budget; candidate pool and ordered source IDs; hashed ITT target universe and fixed denominator; RNG/noise snapshots; arms F0/SOCF-F1/SCMC/NLPRC-no-op/SIPP/baseline controls with stage/output hashes and costs; source-to-pixel provenance/DAG/order-reversal audit; prediction seal and scorer receipt; decision statuses including explicit `UNTESTABLE_*`, `REPLAY_INVALID`, `INVALID_CONSUMER_RECOMPUTATION`, `LEAKAGE_DETECTED`, and `BUDGET_MISMATCH`. Missing legality, matching, provenance, replay, or denominator evidence is never PASS.


## Schema ambiguity corrections (2026-09-16)

- Replace free-form `SCORABLE` with an explicit transition: `prediction_sealed=true` only after all arm outputs and hashes are frozen; `future_scoring_permitted=false` before that. Reserve `PASS` for a completed decision with every required receipt.
- Split `denominator_spec_hash` (pre-seal rule only) from `realized_denominator_hash` (post-seal scorer output). The pre-seal manifest must not contain future GT values or realized valid-pixel counts.
- Name SIPP `score_to_source_id_permutation`; preserve source tensors/features/support/pose and record permutation seed/hash plus arm-pool hash. A relabeled tensor or changed candidate pool is not an identity placebo.


## Status namespace and pilot-label corrections (2026-09-16)

- Namespace environment receipts explicitly: transfer `status=PASS`, CUDA availability, and `PASS_ENV_AND_IMPORT_ONLY` are environment/transfer evidence only; require `formal_gate0_status=NOT_RUN|BLOCKED` until an explicit model-forward Gate0 receipt exists.
- Relabel the single qualified held-out query experiment `PILOT_DIAGNOSTIC_ONLY`; it is not protocol evidence. Only the two calibration trajectories plus untouched held-out scene/horizon package can be `PROTOCOL_EVIDENCE`.
- Replace “pre-seal denominator specification; realized valid-pixel counts only post-seals” with the two-phase contract: pre-seal `denominator_spec_hash`; post-seal scorer `realized_denominator_hash`. Future RGB/depth/pose mounts and realized valid-pixel counts remain forbidden before `prediction_sealed=true`.


## 2026-09-16 — FGB-SI distinction narrowed by primary-source review

**Design-only candidate:** FGB-SI (source-intervention future-geometry measurement) estimates the signed effect of retaining versus replacing one named history source on an externally supplied, held-out future RGB-D/pose state in a fixed commanded coordinate frame, with complete consumer-descendant recomputation and source-to-pixel provenance.

Closest occupied mechanisms include ReWorld pose-indexed bounded memory/redundancy retrieval, Future Forcing future-aware KV selection/merging, and WorldRoamBench geometry/retention metrics. Generic future-aware fixed-budget memory or KV importance is therefore not a novelty basis. The scoped distinction is the auditable named-source intervention plus externally supplied, held-out future RGB-D/pose reference and provenance.

Falsify if the effect adds no held-out future value beyond pose/coverage/confidence/utility, disappears under source/common-bias controls or registration checks, cannot be traced to external geometry, or appears only in one scene/horizon. If so, retain FGB-SI only as a negative/evaluation protocol. No experiment or novelty validation is authorized.
