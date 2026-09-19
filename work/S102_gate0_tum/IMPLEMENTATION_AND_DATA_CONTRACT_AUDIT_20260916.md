# Gate 0 implementation and data-contract audit (2026-09-16)

## Purpose

This audit freezes the conditions required before the first formal VMem long-horizon baseline. It is a contract check, not a model result and not a novelty claim.

## Required PASS items

1. **Camera model:** record image width/height, `K`, distortion coefficients, pixel-center convention, and camera-to-world/world-to-camera direction for every scene.
2. **Depth semantics:** record raw dtype, invalid value (`0` or other), scale factor, radial-versus-optical-axis interpretation, and the exact `depth -> metric z` equation.
3. **Pairing:** use a deterministic one-to-one RGB-depth mapping. Record tolerance, tie rule, dropped rows, and all missing/duplicate counts.
4. **Pose semantics:** record pose source, timestamp/frame identity, quaternion order, translation units, and transform direction. Do not treat ICL frame index as a hardware timestamp.
5. **Future-GT isolation:** define history, calibration, and held-out future windows before decoding future answers. Selector code may see history and candidate metadata only; future RGB/depth/pose/GT is opened only by the sealed scorer after prediction output is hashed.
6. **Held-out identity:** hash the archive and manifest. A scene whose metadata or pose text was inspected before freezing is labelled development/conditional, not zero-exposure blind test.
7. **Fair budget:** freeze candidate pool, selected count, context length, output count, sampling steps, seed/RNG policy, resolution, dtype, checkpoint/config hashes, and runtime budget for all selectors.
8. **Independent readback:** after a run, a separate verifier recomputes manifest hashes, row counts, pairing, metrics, and seal without changing the protocol.

## Current evidence

- TUM FR3 long office household metadata audit: job 588524, 2488/2585 RGB-D pairs within 20 ms, monotonic unique indices, one depth sample decoded. This is qualification only.
- ICL-NUIM lr0: conditional synthetic controlled candidate. Mapping sub-gate passed, but metadata exposure and single-scene scope prevent blind or cross-scene claims.
- H800 VMem model-load smoke: job 588459, load-only, no data/forward/GT.
- H800 CUT3R RGB-only component forward: job 586719, no depth/pose/GT.

## Decision

`BLOCKED_FORMAL_BASELINE_PENDING_CONTRACT_FREEZE`. The next executable task is to fill and independently review the signed pre-run manifest. No GRC/SOCF score is interpreted before that gate.
