# S44 C1/C2 pre-result decision table

Frozen UTC: 2026-09-07T18:11:02+00:00. At this time the unique C1 run had no terminal receipt and no completed batch. Root had read only manifest, gate, process, monitor, and stderr progress metadata; no C1 generated tensor, image payload, PNG, metric, montage, or visual output had been opened. The three preparation agents were explicitly restricted from reading C1 output payloads.

This table applies the already frozen S42 protocol. It does not create a new metric, threshold, or scientific claim.

## Fixed row rule

- Authoritative row statistic: unrounded float64 `MSE_M` over the fixed `M_outer4` mask between authoritative cache IDs 0 and 8.
- Severe return-discrepancy event: `MSE_M > 0.01`.
- Equality at `0.01` is not an event.
- The displayed `ReturnPSNR_M < 20 dB` is only the monotonic equivalent of the same MSE rule.
- A row must first pass execution, archive/readback, ID mapping, pose/intrinsics, pixel identity, denominator, and independent-review guards. Otherwise it is technically invalid and the cohort remains incomplete.

## Cohort outcomes fixed before C1 result access

B0 is already technically valid with `MSE_M = 0.005278160708699555`, so its event is false. Therefore:

| C1 event | C2 event | Three-row decision after all technical gates | Required action |
|---|---|---|---|
| false | false | `NO_CONFIRMED_PREDECLARED_FAILURE` | Stop the frozen severe-return hypothesis. Do not move the ROI, lower the threshold, replace scenes, or relabel a softer visual defect as this event. |
| false | true | `NO_CONFIRMED_PREDECLARED_FAILURE` | Report the single C2 event and heterogeneity, but stop the cohort hypothesis. |
| true | false | `NO_CONFIRMED_PREDECLARED_FAILURE` | Report the single C1 event and heterogeneity, but stop the cohort hypothesis. |
| true | true | At least two of three rows have events. Before a separately frozen camera-obedience proxy passes, the maximum status is `RETURN_RGB_DISCREPANCY_CAMERA_CAUSE_UNRESOLVED`. | Audit global visual collapse and camera obedience before any memory-consumer intervention or attribution. |
| invalid or missing | either | `INCOMPLETE` | Preserve the failed/partial attempt. Retry only if the frozen protocol permits an objective technical retry; never substitute another image, seed, or output. |

## Innovation gate after the cohort decision

1. A completed C1 image or attractive montage is baseline evidence, not method novelty.
2. A confirmed RGB discrepancy still does not identify memory, retrieval, CLIP mean, geometry, or camera control as the cause.
3. Memory attribution is allowed only after a natural failure and camera/quality confounds are separated, using exact replay and the same ordinarily selected source.
4. The surviving S43 question requires all of: single selected source, fixed other state, source-coherent change through all consumer paths, pre-intervention geometry support plus an area baseline, and incremental prediction of natural revisit error or benefit.
5. Matrix-Game 3.5 is a mandatory strong baseline for patch provenance, geometry support, unified attention, and fixed-seed module ablation. MosaicMem V2 remains an unpublished `NOT_ASSESSABLE` monitoring risk.
6. If exact-replay variance is comparable to the intervention, effect concentration fails to beat the area baseline, the item score does not predict natural revisit behavior, or a public primary source completes the joint contract first, the candidate is killed or repositioned.

## Evidence boundary

This is a timestamped interpretation freeze made during the running C1 baseline. It is not a C1 terminal result, readback, score, visual review, confirmed natural failure, causal effect, method gain, novelty result, PhD-level completion, or CCF-A-level completion.
