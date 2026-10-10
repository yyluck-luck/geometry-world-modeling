# Self-audit of S139 (self-audit, no codex; owner 2026-10-10: "u can do by yourself not codex")

Replaces the codex R251/R252 reviews, which failed on model capacity (7 + 2 attempts). Automated checks:
`work/S139_crossseq_revisit/SELF_AUDIT_CHECKS.json`. Manual code review notes are below.

## Automated checks (all pass)
| check | result |
|---|---|
| Manifest = protocol (pairs, starts, 20 H + 12 C bank, targets, static offsets, priming [15, 12]); no target in its own bank | PASS (24/24) |
| VMem contexts ⊆ bank; memory covers all 32 bank frames | PASS (24/24) |
| Generation logs (RTX 3090, 288 runs): ctx_refs and target_refs equal the plan | PASS |
| Scored frames equal plan targets; 8 seeds per context (72 contexts); seed→site split 42, 7, 1, 2 / 3, 4, 5, 6 | PASS |
| H800 job rebuilt the plan from the step-A receipt byte-identically to local plan_v2 | PASS (`cmp`) |
| Primary recomputed by a different code path (per-seed paired, then window mean) | −0.1805 dB (reported −0.181); HF −0.334, RF +0.126 |

## Manual review
- `run_retrieval_s139.py`: `pipe.config` is the same object as `cfg` (`pipeline.py:48`). `construct_and_store_scene`
  reads `target_num_frames` at call time (`:1027`), so setting it to the chunk length gives every new frame surfels.
  The receipts confirm 32/32 coverage. The value is restored in `finally`. The NMS threshold is set by the 5-frame
  `get_context_info` call, as in VMem. `reset()` clears all list state and `initial_threshold`.
- `pose_arms_s139.py`: threshold from the first five bank frames (VMem's 5-frame state); target = last target with a
  quaternion round trip (VMem's `average_camera_pose` of one pose); fp32 torch geodesic. The stratum uses poses only.
- `gen_s139.py`: refs resolve to `DATA/chess/seq-XX/frame-NNNNNN`; gl conversion is applied once to context and target
  poses; the sampler is unchanged from C9/S134; outputs are keyed by ctx_key + seed.
- `baselines_s139.py`: CUT3R receives the raw OpenCV poses, which equal VMem's `get_transformed_c2ws(gl)`. Depth
  back-mapping uses the corrected pixel-centre formula. Copy-nearest uses VMem's geodesic over the full bank.
- Leakage: the model stage holds no depth (checked in-job: 0), and target-only frames have no colour. Targets of one
  window that are bank frames of another are read only by that other window's process (same isolation as C8–S136).

## Caveats that stand
- 7-Scenes RGB focal: the protocol fixed 585. Relocalisation literature often uses ≈ 525 for RGB. Arm contrasts share
  K; absolute geometry (and B2 quality) is approximate.
- The three sequence pairs share history banks within a pair, so the window bootstrap overstates independence. The
  pair-cluster CI is reported (3 clusters, descriptive only).
- B2 is a direct geometric predictor, not a capacity-matched generator control.
