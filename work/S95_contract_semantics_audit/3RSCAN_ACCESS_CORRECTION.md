# 3RScan access and temporal semantics correction

时间：2026-09-12 19:06 Asia/Shanghai

## Correction

The previous S94 report stated that a complete sample requires user-completed Terms of Use. That statement was too strong. The official repository setup script labels `3RScan.v2.zip` as example data and invokes a direct public download. The project/documentation pages state a general Terms-of-Use route for data, but the sources reviewed do not explicitly say whether the example archive is exempt.

Correct status: `sample access/permission scope = AMBIGUOUS_NOT_VERIFIED`; do not submit forms or personal information, and do not infer either permission or prohibition. This correction does not pass Gate 0 because complete frame bodies, frame-level synchronization, intrinsics, units, depth validity and pose text are still unverified.

## Temporal correction

The FAQ describes reference as an initial scan (usually the most complete or first) and rescan as the other scans. The associated task semantics discuss later scans, but the reviewed metadata does not establish exact per-scan timestamps or a continuous next-frame sequence. The safe problem wording is `reference-to-rescan revisit/change evaluation`, not continuous-video future-frame prediction.

Evidence: official repository `setup.sh`, README/FAQ and documentation links recorded in `work/S94_ALT_3RSCAN01/GATE0_RESULT.json`; detailed local review in `data_access_review.md`.
