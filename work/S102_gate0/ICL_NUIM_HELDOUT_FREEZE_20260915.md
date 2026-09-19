# ICL-NUIM held-out acquisition freeze (2026-09-15)

## Purpose

取得一个许可清楚、带 RGB-D、相机轨迹和明确深度/时间顺序的补充测试来源，作为正式 GRC 进入资格审计的候选。它是 synthetic RGB-D benchmark，不能冒充真实传感器泛化；Bonn dynamic 仍作为真实动态候选，待其许可与独立性证据完成后再决定。

## Frozen source and split

- Official source page: <https://www.doc.ic.ac.uk/~ahanda/VaFRIC/iclnuim.html>
- License shown by the official page: Creative Commons 3.0 (CC BY 3.0).
- Frozen acquisition target: `living_room_traj0_frei_png.tar.gz` (`lr kt0`, official TUM-compatible RGB-D package).
- Official page reports 1,510 images, 30 Hz, 51 seconds, TUM-format RGB-D and a `TrajectoryGT` file. The page and a portion of the official pose text were read during candidate search, so this is not a zero-metadata-exposure claim.
- Planned test split after acquisition: first 70% of frame indices for calibration/development, last 30% for `HELD_OUT_TEST`; split hash and exact frame list must be generated before any future-GT scoring.

## Eligibility boundary

This freeze permits acquisition and structural inspection. It does not automatically grant `Gate0=PASS`: the package must still provide one-to-one RGB/depth identity, timestamps or a defensible frame-time rule, intrinsics, depth unit, pose convention, SHA manifest, license receipt, and a method-freeze/exposure audit. The first structural audit (`work/S102_gate0/ICL_NUIM_ARCHIVE_AUDIT_v2.json`) found 1,509 RGB PNGs, 1,509 16-bit depth PNGs, 1,509 one-to-one association rows and 1,508 pose rows. The follow-up mapping audit found RGB/depth/association IDs 0..1508 and pose IDs 1..1508; the explicit rule is to exclude association ID 0 and retain 1..1508, producing 1,508 one-to-one pairs. The pairing subgate is `PASS`, while the overall candidate remains `BLOCKED_TIMESTAMP_SEMANTICS_AND_FULL_QUALIFICATION` until the frame-index/30 Hz rule, depth/camera conventions, split and GT isolation are explicitly frozen. See `work/S102_gate0/ICL_NUIM_MAPPING_MANIFEST.json`.

## No-leakage rule

The selector may read historical RGB-D/camera information only. Future RGB/depth/pose bytes are opened only after prediction seals are written. The official metadata and calibration/pose-format pages were read during candidate search, and a portion of the official pose text was opened; this is a conservative **data-access held-out** candidate rather than a claim of zero metadata exposure. The raw archive was acquired only after the acquisition freeze; no image pixels were decoded and no model was run in the structural audit.

## Acquisition command (remote, resumable, no model execution)

```bash
mkdir -p "$HOME/datasets/icl_nuim"
curl -L --fail --retry 3 --continue-at - \
  -o "$HOME/datasets/icl_nuim/living_room_traj0_frei_png.tar.gz" \
  https://www.doc.ic.ac.uk/~ahanda/living_room_traj0_frei_png.tar.gz
```

The download receipt must record URL, start/end UTC, bytes, SHA256, HTTP status, and the exact command. Do not unpack or score until the Gate0 manifest is generated.
