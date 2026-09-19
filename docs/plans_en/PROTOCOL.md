# S91 (Future Geometric-Risk Incremental-Prediction Experiment, GRC-Pilot)

> Source: `work/S91_grc_pilot_protocol/PROTOCOL.md`  
> Source SHA-256: `9294c15a03abcd3586aeb8a4f9f6f7aa7d4a1804e7885f87ee9cfbe2e42bff3c`

## Current status

`BLOCKED_ON_GATE0`. This is a formal unseen-scene experiment protocol, not an already completed model result. Gate 0 must first confirm that every scene has historical RGB-D/geometry, future RGB-D/geometry, camera semantics, temporal order, file SHA, and answer isolation.

## Scientific question

With a fixed historical candidate pool, fixed slot count `k`, fixed consumer, and fixed total cost, can geometrical risk computable from the past predict geometric error for a future query and provide incremental benefit beyond simple time, pose, coverage, and confidence selection?

## Concrete inputs

At time `t`, the selector may read only historical RGB, historical depth or geometric features, historical timestamps, historical camera, the request camera, and fixed model state. Future RGB, future depth, future pose, future mask, future model output, and future error remain locked until selection is completed and sealed.

For each scene/trajectory: at least 6 historical candidates and at least 3 future queries; split development, calibration, and test by scene, never randomly by frame. Primary metrics aggregate by scene/trajectory/query; pixels are not independent samples.

## Selectors

Under exactly the same candidate pool, `k`, consumer, noise, and budget, compare:

1. `random-k`: preregister multiple seeds;
2. `recent-k`: most recent in time;
3. `nearest-pose-k`: distance to the request camera;
4. `coverage-k`: historical spatial/field-of-view coverage;
5. `utility-only`: utility based only on past information;
6. `confidence-only`: existing confidence;
7. `risk-only`: geometric risk;
8. `risk+utility`: GRC candidate;
9. `worldmem-style`: fixed-budget relevance/memory-retrieval strong baseline (implementation identity must be frozen separately).

## Risk definition

The development-stage preregistered risk vector includes reprojection residual, depth consistency, visibility conflict, historical-source coverage, and model confidence. The calibrator may fit only on calibration scenes; test scenes use the already frozen risk mapping and may not read future answers to tune thresholds.

## Primary metrics

Prefer future object-center/keypoint 3D position error. If data provides depth only, downgrade to camera-Z depth error and treat RGB MSE, coverage, failure rate, and runtime cost as auxiliary metrics. Report Spearman correlation between risk and future error, error trends at fixed risk quantiles, and paired loss differences for every test query.

## Preregistered falsification conditions

- Risk direction is unstable on test scenes or its interval covers zero;
- `risk+utility` does not outperform `coverage`, `nearest-pose`, `utility-only`, or `confidence-only`;
- The advantage appears only in one scene, one camera trajectory, or one seed;
- Any selector reads future answers, future pose, future mask, or a post-generation score;
- Only RGB MSE improves while the primary geometric metric does not;
- The selector changes slot count, consumer budget, or total runtime cost, making the comparison unfair.

## Result boundary

Even if S91 passes, it shows only measured incremental benefit of risk-aware selection within this data scope; it does not automatically imply a theoretical guarantee, cross-dataset generalization, or PhD/CCF-A level. If it fails, stop the GRC-Memory method claim and retain the negative result and failure diagnosis.
