# S96/S97 progress report and snapshot sync audit

- Audit time: 2026-09-12 (Asia/Shanghai)
- Auditor role: independent report/snapshot consistency review
- Scope: `work/S90_proxy_resumable_index/REPORT_PROGRESS_UPDATE_20260912.md`, `EXPERIMENT_NAME_LEGEND.md`, S96/S97 machine-readable outputs, and user snapshot `创新候选逐条核验_S90_2026-09-12/UPDATE_INDEX_20260912.json`.

## PASS findings

1. The progress report contains a dedicated S96/S97 section. Its numerical claims agree with the machine-readable outputs: S96 has eight finite kernel-pool/setting rows and the independent reconstruction reports 74/74 checks; S97 reports fr1 792 one-to-one RGB-D matches / 788 pairs inside one GT support interval and fr2 2893 / 2212. The report correctly states that this is a finite component audit and an RGB-D qualification audit, not model inference, not an S91 run, and not GRC validation.
2. The S97 correction is scientifically bounded. The report distinguishes the earlier nearest-neighbour diagnostic from the protocol recheck, names the strict `<20 ms` unique-greedy RGB-D rule and `>100 ms` GT gap support rule, retains `DEVELOPMENT_SEEN`, and preserves `new_method_validated=false` and `novelty_authorization=NONE`.
3. The user snapshot contains the S96 and S97 protocol/results/review files, including `run_01/RESULTS.json`, `INDEPENDENT_REVIEW.md`, `independent_results.json`, `run_02_official_association_results.json`, and `S97_OFFICIAL_ASSOCIATION_CORRECTION.md`. The 188-entry `UPDATE_INDEX_20260912.json` was independently checked: no missing files and no SHA-256 or byte-count mismatches.
4. The snapshot copy of `REPORT_PROGRESS_UPDATE_20260912.md` is byte-identical to the project report (18,586 bytes; SHA-256 `2268448dacb8f33010cc4fb42c507e3c8f666207e690386dcedb7c84fc666437`).

## REVISE findings (no old result was changed)

1. **Experiment-name legend is incomplete (MAJOR for beginner-facing reporting).** `EXPERIMENT_NAME_LEGEND.md` explains S86–S94, but has no entries for S95, S96, or S97. The progress report therefore introduces S96/S97 without the global “S number = internal stage, not success level” explanation and without the requested parenthesized concrete names. Add:
   - S95（评价合同语义、3RScan访问边界与GIM核函数数学诊断）：protocol semantics/access scope/kernel formula audit; not model or GRC validation.
   - S96（保存位姿上的GIM核谱与选择索引有限审计）：finite saved-pose component audit; no RGB-D reading/model inference; PSD result is local and not global GIM validation.
   - S97（本地TUM RGB-D一对一关联与连续GT支持区间资格复核）：development-only file/header and association qualification; no held-out test and no S91.
   Then mirror the updated legend into the snapshot and rebuild its index.
2. **Chronology is confusing.** The report appends an S96/S97 section before the later S95 section. Move the S95 heading before S96/S97, or add a clear note that append order reflects completion time rather than S-number order. This prevents a beginner from reading S96 as preceding S95.
3. **S96 status wording should be explicit.** `run_01/RESULTS.json` retains `EXECUTED_COMPONENT_ONLY_PENDING_INDEPENDENT_REVIEW`, while `independent_results.json` and the report say 74/74 independent checks passed. Add one sentence: “原始执行回执状态仍保留 pending；独立复核文件随后完成，74/74 是复核结论，不是方法质量通过。” Do not rewrite the original result status.
4. **Reproducibility boundary for S97.** The report names `src/tum_rgbd.py`, but the snapshot does not copy that implementation. The S97 JSON does record data-file SHA values, but not the association-source SHA. Add the association source SHA (and optionally copy the exact source under a clearly labelled vendor/audit directory) to the S97 correction or snapshot manifest. This is a provenance improvement, not a scientific result.
5. **Scope of image-header claim.** The phrase “保留图像均为640×480…” should remain explicitly tied to the 788/2212 pairs retained after GT-support filtering; it must not be interpreted as all 792/2893 official matches or as a held-out sequence property. The current table is numerically correct, but a parenthetical “对同区间保留对” would remove ambiguity.

## Recommended acceptance wording

Until the above documentation repairs are made, the scientific status is still acceptable as:

> S96 is a finite, independently recomputed GIM-kernel component audit; it found no negative eigenvalue in the eight tested saved-pose matrices, but does not validate GIM globally or establish GRC. S97 is a development-seen TUM RGB-D association qualification; it found readable 640×480 RGB and 16-bit depth for the retained pairs, while 681 fr2 pairs fail the continuous-GT-support rule. Neither result is a held-out future-geometry experiment.

No new method, novelty, PhD/CCF-A, or S91 claim is authorized by this audit.
