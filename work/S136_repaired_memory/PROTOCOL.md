# S136 protocol — repaired VMem memory, and the camera-convention question at 8 seeds

Authorization: owner standing authorization, 2026-10-09 (AGENTS.md). Written before any S136 run.
Diagnostic; `new_method_validated=false`, `novelty_authorization=NONE`.

## Why (from S133–S135)
- S133: the surfel map was mis-scaled by more than 10× in 8/14 windows (silent PnP identity fallback). The adaptive
  PnP threshold removes the blow-ups, but leaves the scale biased low (median 0.70).
- S134 (H800): the fix changes VMem's default NMS-on contexts in only 4/14 windows. The native map gate failed
  11/14, so no generation was run.
- S135: (a) KPS, a known-pose dense scale init, recovers σ on synthetic short baselines (9/9 tests) and improves the
  real stage-1 scale. (b) VMem's selection is pose-distance ranking plus pose NMS over a surfel-visibility
  candidate set. On the repaired map all memory frames are candidates in 13/14 windows. (c) The S111 priming (5 then 7
  frames) never puts bank offsets 25/30/35 into memory. VMem only adds surfels for the last 4 frames per construct.
- C9: the generator's camera convention (native vs gl) moved static PSNR by up to ±3.7 dB per window; mean +0.687 dB,
  inconclusive at 2 seeds.

## Repaired memory
gl convention (dataset OpenCV poses converted to the OpenGL input VMem expects) + KPS scale init + chunk4 priming
(5 frames, then 4, then 3, one construct each; VMem's cadence). INIT is `kps` or `kpsK` (known K). Step A runs both;
the canonical INIT is fixed by the rule below, before any generation.

## Step A — maps and contexts
H800 (canonical) and TACC gpu13 (cross-check), `run_retrieval_s136.py`, 14 windows (w50–w350), gl + chunk4 × {kps, kpsK}.
Gate (per INIT): window scale ratio in [0.5, 2] for ≥ 12/14, none > 10 or < 0.1, median own-render corr ≥ 0.5,
no BLOCKED window. Memory coverage (frames owning surfels) is reported, expected 12/12.
Canonical INIT = the gate-passing variant with the smaller median |log scale ratio|. If neither passes, no memory arm
is generated. Q1 below still runs, because static generation does not use the map.

## Step B — generation (8 seeds; H800 42,7,1,2 · TACC 3,4,5,6; each (window, seed) cell on one site)
Arms:
- static_native, static_gl — 16 windows (w0–w350), offsets 0,15,30,45.
- mem_orig_native — the sealed configuration (S134 H800 native/orig contexts), 14 windows.
- mem_orig_gl — the original pipeline under gl (S134 H800 gl/orig contexts), 14 windows.
- mem_rep_gl — the repaired memory (S136 canonical contexts), 14 windows, only if the gate passes.

## Contrasts (unit: window mean over 8 seeds; window-cluster bootstrap 95% CI, 10k, rng 0)
- **Q1 (convention, C9 replication):** static_gl − static_native, 16 windows. C9's rule, unchanged:
  MISMATCH_CONFIRMED if mean ≥ +1.0 dB and ≥ 12/16 windows positive. Also IMPROVES / WORSENS / NO_MATERIAL_CHANGE /
  INCONCLUSIVE by the S134 rule (±0.2 dB, CI).
- **Q2 (does repaired memory help?):** mem_rep_gl − static_gl, 14 windows. S134 verdict rule.
- Q3 (repair effect): mem_rep_gl − mem_orig_gl, 14 windows.
- Q4 (link to the report): mem_orig_native − static_native, 14 windows, now at 8 seeds.
- Per-site breakdown for every contrast.

## Leakage boundary
As S134. The model process sees bank color+pose and target pose only. Scoring and map evaluation are separate
processes. Window overlap means a frame can be a target in one window and a bank frame in another. Isolation is by
code (each window reads only its own bank), as in C8/C9/S134.

## Stopping
Report after step B. Any follow-up needs a new protocol file.

## Amendment 1 (2026-10-09 ~16:35 UTC, before any S136 score was computed)
- Generation of the arms that do not depend on S136 step A started at once on TACC (plan_v1: static_native,
  static_gl, mem_orig_native, mem_orig_gl; 59 unique contexts). mem_rep_gl will be appended (plan_v2, a superset;
  existing outputs are skipped) once the H800 step A gate is evaluated.
- The TACC kpsK step-A cross-check was stopped after 2 windows to free GPU 4 for generation. TACC still cross-checks
  kps. H800 runs both INITs, as planned.
- mem_orig_gl has 13 windows: H800 S134 gl/orig scene_13 w200 is BLOCKED (IndexError, as in C9), recorded not dropped.
- S134 Amendment 1 is honoured inside S136: the S134 gl + S133-fix map passed its gate on H800 (12/14 in scale range,
  median own-render corr 0.63, none extreme). The S134 gl arm mem_fix_gl is added (plan_v1b; 3 new unique contexts).
  Its pre-registered S134 contrasts are mem_fix_gl − mem_orig_gl and mem_fix_gl − static_gl.
