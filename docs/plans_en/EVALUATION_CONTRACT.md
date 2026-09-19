# S94 Minimum Evaluation Contract: Future Geometric-Risk Memory Selection Under a Fixed Budget

> Source: `work/S94_evaluation_contract_review/EVALUATION_CONTRACT.md`  
> Source SHA-256: `c3240963f405ed9dc05df797a9a9374f731a1c8c20b307a9673402b307559950`

Version: `S94-v1`

Review-record time: 2026-09-12 17:11:57 (Asia/Shanghai)

Status: `PROTOCOL_ONLY / NOT_RUN`

## 1. Research question and falsifiable hypothesis

The research question is: under the same historical candidate pool, memory slots, consumer, and total compute cost, can geometric risk from historical observations predict the geometric error of an **independent future query** and provide incremental benefit beyond existing time, pose, coverage, and confidence selection?

The only allowed primary-method hypothesis is:

> On unseen trajectories, `risk+utility` has lower future geometric error than `recent`, `nearest-pose`, `coverage`, `confidence-only`, and any runnable long-term-memory baseline, with the advantage appearing in both mean error and tail risk.

This is not the hypothesis that “risk correlates with error.” Correlation can be a diagnostic, but is insufficient to establish an effective selection method.

## 2. Gate0: data qualification and answer isolation

Every scene must have all of the following:

1. Historical RGB and depth/geometry, with original timestamps;
2. Future RGB and depth/geometry, with original timestamps;
3. Intrinsics, extrinsics/pose, coordinate system, and depth units for the request camera;
4. Recheckable file SHA, data source, and terms of use;
5. At least 6 historical candidates and 3 future queries.

The formal confirmation set must contain at least **5 mutually independent test trajectories**, each with at least 3 future queries. With only 3–4 trajectories, mark `PILOT_ONLY` and do not write a cross-scene confirmation. Split by scene/trajectory rather than randomly by frame: `development`, `calibration`, and `test` are mutually exclusive.

The temporal constraint is `t_history < t_query`. Historical candidates may come from frames before the query; future RGB, future depth, future pose, future mask, future model output, future error, and any future-validity label must not enter the selector, utility training, or threshold setting.

Operationally, use two stages and two directories:

- The `select/` process receives only the historical manifest, request camera, and frozen model state, and outputs source IDs;
- The `score/` process mounts future answers only after the `select/` output SHA is sealed;
- Selector input and future manifests use different Unix permissions or container mounts; save system-call/file-access audits after the run;
- If any selector log, cache, or checkpoint reads a future path, invalidate the entire query, rather than only deleting one metric.

## 3. Source identity contract

Every historical candidate observation must have a stable `source_id`:

```text
{dataset, scene_id, trajectory_id, frame_id, timestamp_ns, modality, file_sha256}
```

Selector output must save the candidate ranking, selected source IDs, unselected IDs, scores, and tie-break rule. Every slot read by the consumer retains its source ID; if fusion occurs, save the complete source-ID set composing that slot and its weights.

The scoring side must report at least:

- `selected_source_identity_match`: whether the same source actually entered the consumer;
- `source_traceability_rate`: proportion of output slots traceable to original sources;
- `identity_collision_rate`: proportion of different sources incorrectly merged.

If traceability is `< 95%` or identity match cannot be computed, downgrade the run to a “system-level memory comparison” and do not claim a single-memory geometric-risk effect.

## 4. Fixed budget and fair comparison

Freeze the following budgets in advance for every query; all methods must be identical:

|Budget item|Contract requirement|
|---|---|
|Candidate pool|The same historical candidate IDs and count|
|Slot count|Fixed `k`; primary contract defaults to `k=4`, with sensitivity runs at `k=2,8`|
|GPU/cache|Record peak bytes and token count; cap set by the frozen budget of the largest legal baseline|
|CPU/host memory|Count separately; do not hide unbounded host keys or indexes behind “fixed k”|
|Selection compute|Record selection time, bytes read, forward count, and FLOPs/available approximation|
|Consumer compute|Same denoising steps, resolution, noise/RNG, model weights, VAE, and post-processing|
|Output|Same query camera, output count, and stopping condition|

Report GPU cache and host memory in separate columns. If baselines such as WorldTrace-Field and MemRoPE have host state that grows with history, count actual peak usage; over the frozen cap is `OVER_BUDGET` and cannot be reported as GPU usage only.

If a method cannot run under the same `k` or memory cap, do not manufacture fairness by deleting its state. Mark it `INCOMPATIBLE_BASELINE` and retain the reason for missingness in the main table.

## 5. Methods and strong baselines

All methods read the same candidate pool and use the same consumer:

1. `random-k`: at least 5 preregistered seeds, reporting the mean and seed interval;
2. `recent-k`: most recent in time;
3. `nearest-pose-k`: pose distance to the request camera;
4. `coverage-k`: historical spatial/field-of-view coverage;
5. `pose/reprojection-only`: pose or reprojection error only;
6. `depth-consistency-only`: historical depth consistency only;
7. `confidence-only`: existing model confidence only;
8. `utility-only`: utility from past information only, never future answers;
9. `risk-only`: geometric risk only;
10. `risk+utility`: GRC candidate;
11. When reusable, add `WorldTrace-Field/Landmark`, `MemRoPE`, and `WORLDMEM-style`, recording implementation versions strictly;
12. If resources permit, add `Fisher/EIG-proxy`; if complete FisherRF cannot run, label this explicitly as a proxy and do not call it a reproduction of the original method.

`oracle-future` may be used only as an upper-bound diagnostic; it cannot enter the main ranking, tune thresholds, or be written as a deployable method.

## 6. Metrics and statistical units

### 6.1 Primary geometric metrics

- Preferred: 3D position error of future object centers/keypoints;
- If only depth is available: camera-coordinate Z `AbsRel` and `MAE(m)`; depth units, invalid values, and clipping range are frozen at Gate0;
- If camera and depth are available: future-frame reprojection error (px) and valid coverage as auxiliary geometric metrics.

### 6.2 Tail risk

Report all of the following:

- Mean `AbsRel` over all valid pixels/points;
- Per-query worst-5% `AbsRel` (mean of the highest-error 5%);
- Per-query `CVaR95` (mean error above the 95th percentile);
- Failure rate, valid coverage, and missing-depth rate.

`worst-5%` and `CVaR95` are risk metrics, not significance evidence treating pixels as independent samples.

### 6.3 Aggregation and confidence intervals

The primary statistical unit is `scene/trajectory/query`. Aggregate within each query first, then by trajectory; do not treat hundreds of thousands of pixels as hundreds of thousands of independent experiments. Report each query’s paired difference (method−baseline), then calculate 95% CIs with a trajectory-level bootstrap. If fewer than 5 test trajectories exist, report descriptive intervals only and mark `PILOT_ONLY`.

Also report risk calibration: the development/calibration risk–coverage curve, future-error trends at fixed risk quantiles, and test-set Spearman only as auxiliary evidence; do not treat Spearman itself as method benefit.

## 7. Pre-run freeze checklist

Before reading any test-future file, save `FREEZE.json` containing at least:

- Dataset version, scene/trajectory split, all source IDs and SHAs;
- Model/weight/code commit, consumer, and VAE identity;
- `k`, GPU/host/token/time budgets;
- Parameters, random seeds, and tie-breaks for every baseline;
- Primary metrics, invalid-value rules, and CVaR/worst-5% definitions;
- Prediction direction (lower error is better), stopping rules, and missing-data handling.

After freezing, do not change the risk formula, threshold, quantile, or visualization selection based on test results. Any change creates a new contract version.

## 8. Stopping rules

Stop the GRC method claim and retain results and failure evidence if any of the following occurs:

1. Gate0 fails; timestamps/camera/depth units cannot be bound; or future truth is missing;
2. The selector accesses future answers, future pose/mask, post-generation error, or a future-valid mask;
3. Source traceability is `<95%`, or entry of the same source into the consumer cannot be checked;
4. Any method exceeds GPU/host/time/slot budget and cannot be fairly repaired under the frozen rules;
5. On more than 5 test trajectories, `risk+utility` does not simultaneously improve mean AbsRel and worst-5%/CVaR95 over the strongest non-oracle baseline, or the paired CI crosses zero with unstable direction;
6. The gain appears only in one scene, one trajectory, or one random seed, or only RGB MSE improves while the primary geometric metric does not;
7. Results come only from seen/tuned scenes or only from retrospective saved-data recomputation;
8. Compute cost increases substantially while geometric benefit does not exceed strong baselines such as `coverage`, `nearest-pose`, `confidence-only`, or `WorldTrace/MemRoPE`.

When a stopping rule fires, the result may be retained as a `measurement/diagnostic` or negative result, but it must not be renamed or packaged as a validated new method.

## 9. Pass conditions (still not proof of innovation)

Only after Gate0, answer isolation, source traceability, fixed budget, and independent review all pass, and `risk+utility` shows stable paired improvement on the primary geometric metric and at least one tail metric over the strongest non-oracle baseline on at least 5 test trajectories, may the work enter method-paper review. Even then, cross-dataset tests, ablations, mechanistic counterexamples, and near-neighbor review are required; this contract does not grant `novelty_authorization`.

## S95 semantic-review freeze reminder (2026-09-12)

Passing the offline S94 field check does not mean that the contract semantics are sufficient. `work/S95_contract_semantics_audit/RESULTS.md` found that the following must be fixed before formal execution: `N>=k_max` (the current k=8 sensitivity conflicts with the original N>=6), the fractional-tail definition for finite-sample CVaR, the descriptive-only gate for five trajectories, the distinction between marginal and post-selection calibration, risk-component units/normalization, and the actual information-availability time of the request camera. Formal S91 remains prohibited until the S95 patch passes.
