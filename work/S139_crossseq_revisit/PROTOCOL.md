# S139 protocol — does VMem's (repaired) memory help when real long-range history exists? Cross-sequence revisits

Owner standing authorization (2026-10-09). Frozen **before any image or depth content of 7-Scenes chess is read**.
Prior exposure: archive downloaded and hashed (2026-09-16, `HELDOUT_EXPOSURE_AUDIT_20260917.md`: "moderate", RGB/depth
not co-registered). No model has ever run on it in this project. Claim scope: "held out from this project's design and
analysis decisions"; pretraining exposure of CUT3R/VMem to 7-Scenes is not verified.
`new_method_validated=false`, `novelty_authorization=NONE`.

## Why
S133–S138: on short single-pass windows VMem's retrieval reduces to pose-distance NMS, and a fully repaired memory shows
no detectable gain over static (S136 Q2). The remaining defence of spatial memory is that it pays off only when there is
real long-range history: revisits of places seen earlier, possibly from other viewpoints. Single-loop sequences give one
dependent revisit event (S113, fr1_room UNTESTABLE). 7-Scenes provides six traversals of one room in a common world frame,
so another traversal can serve as long-range memory and every window is an independent revisit opportunity.

## Data and windows (mechanical, poses and timestamps only)
- Scene: 7-Scenes `chess`, sequences seq-01…06, 1000 frames each, `frame-XXXXXX.{color.png,pose.txt}` (camera-to-world).
- Intrinsics: fx = fy = 585, cx = 320, cy = 240 (dataset documentation). Depth is not used (not co-registered).
- Pairs (history H → current C): (seq-01 → seq-02), (seq-04 → seq-03), (seq-06 → seq-05).
- Windows in C: start s ∈ {150, 250, 350, 450, 550, 650, 750, 850} → 8 per pair, 24 in total.
- Bank (32 frames, all strictly before the first target): H frames 0, 50, …, 950 (20), then C frames s, s+5, …, s+55 (12).
- Targets: C frames s+60, s+75, s+90, s+105.
- Convention: dataset poses are OpenCV camera-to-world, converted to gl for VMem (as S136). The KPS convention detector
  (S135) is run on the step-A windows and reported. If native wins in the majority, all results are flagged.

## Memory (repaired, as S136 + full coverage)
gl + KPS init + coverage priming: initialise with H0 and append H1–H4, then construct (5 frames). Append the remaining 15 H
frames, then construct with target_num_frames = 15. Append the 12 C frames, then construct with target_num_frames = 12.
Every bank frame owns surfels. The NMS threshold is set at the 5-frame state, as in VMem. Contexts come from VMem
`get_context_info` (NMS on, clean).

## Arms (k = 4)
- `static_recent`: C frames s, s+15, s+30, s+45 (the project's static rule).
- `mem_vmem`: VMem retrieval over the 32-frame bank (canonical contexts from H800 step A).
- `mem_pose`: VMem's pose-distance ranking + NMS over all 32 bank frames, with no surfels and the same threshold rule
  (CPU fp32, `pose_only_retrieval.select`).
Generation: VMem static-path sampler (S136 `gen` with cross-sequence frame ids), gl, 8 seeds.
H800 runs 42, 7, 1, 2 and the RTX 3090 runs 3, 4, 5, 6. Each (window, seed) cell is on one site.

## Metric and analysis
PSNR (C9 scorer), window = 4 targets, mean over 8 seeds. Window-cluster bootstrap 95% CI (10k, rng 0). Also reported:
a pair-cluster bootstrap (3 clusters, descriptive) and per-pair means. Verdict rule as S134/S136 (±0.2 dB with CI).
- **Primary:** mem_vmem − static_recent (24 windows).
- Secondary: mem_vmem − mem_pose (does surfel visibility add over pose in a revisit regime?); mem_pose − static_recent.
- Pre-registered stratum (pose-only, computed before scoring): history-favourable windows, where the last target is
  closer, by VMem's geodesic, to some H frame than to every recent C frame. Report the primary within each stratum and
  their difference.
- Descriptive: the fraction of retrieved contexts that come from H.
- CPU baselines (as S137): B0 copy-nearest bank frame per target; B2 CUT3R + KPS forward warp from the mem_vmem
  contexts and from the static contexts.

## Prediction and decision
If long-range memory is useful when history exists, mem_vmem − static_recent is IMPROVES, larger in history-favourable
windows. NO_MATERIAL_CHANGE or WORSENS extends the S136 negative to a revisit regime. mem_vmem vs mem_pose shows whether
any gain needs geometry or only pose.

## Leakage boundary
Model processes see the bank frames (color + pose) and target poses only. Scoring is a separate process. Targets never
appear in a bank (C frames < s+60; H is another sequence).

## Stopping
Report after scoring. No window, pair or threshold changes after content exposure.

## Amendment 1 (2026-10-10 ~02:20 UTC, before any S139 score)
- Unzip: all six sequences have 1000 pose/color/depth files. seq-01.zip reports a warning on its directory entry
  ("ucsize <> csize for STORED entry"). No file is missing.
- KPS convention check (CPU, first 5 bank frames of each pair; `CONVENTION_CHECK.json`): **gl wins 3/3** (median
  reprojection 9–16 px vs 103 px–∞ for native, where σ collapses to the grid floor). gl is used, as planned.
- Pose-only quantities (`POSE_ARMS.json`): 16/24 windows are history-favourable. mem_pose contexts draw 50–100% of their
  frames from the history sequence.
- Generation of the arms that do not depend on step A (static_recent, mem_pose; plan_v1, 48 contexts) started on TACC
  (seeds 3–6) while H800 step A runs. mem_vmem is appended when step A finishes (plan_v2, superset).
- Step A (H800 job 674961) done: 24/24 windows OK, memory covers 32/32 bank frames in every window, KPS σ stable
  across the three constructs; VMem contexts are 88.5% history frames on average; mem_vmem ≠ mem_pose in 24/24
  windows (with 32 frames the surfel visibility keeps only the top-14 candidates). plan_v2 = plan_v1 + 24 mem_vmem
  contexts (72 unique). H800 step B (job 674991) builds the same plan from the receipt inside the job.
- Exploratory (not pre-registered): B2 warp from mem_pose contexts 14.35 dB vs from static_recent 13.11 dB; B0
  copy-nearest bank frame 12.22 dB.
