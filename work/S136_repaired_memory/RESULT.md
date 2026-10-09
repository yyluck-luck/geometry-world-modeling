# S136 result — the camera convention matters (+0.89 dB); a repaired memory still does not beat static

Protocol: `PROTOCOL.md` (+ Amendment 1). Sites: SuperPOD H800 (step A job 672240, step B job 673576; seeds 42, 7, 1, 2)
and TACC gpu13 RTX 3090 (seeds 3, 4, 5, 6). 71 unique contexts × 8 seeds = 568 generations, all scored.
`new_method_validated=false`, `novelty_authorization=NONE`.

## Harness
- H800 static native, seeds 42/7: **32/32 SHA-256 manifest matches** with sealed S111 job 594957 (hashes computed on
  the cluster; the arrays are not in the checkout).
- Repaired-memory map gate (H800): 14/14 windows within scale [0.5, 2] (actual 0.77–1.26), median own-render corr
  0.785, 12/12 bank frames in memory in every window, no BLOCKED window. Canonical INIT = kps by the rule
  (median |log r| 0.099 vs kpsK 0.172).

## Results (window mean over 8 seeds; window-cluster bootstrap 95% CI; `results/S136_ANALYSIS.json`)
| contrast | Δ PSNR (dB) | 95% CI | windows + | verdict | H800 / 3090 |
|---|---|---|---|---|---|
| **Q1 static_gl − static_native** (16 w) | **+0.890** | [+0.248, +1.469] | 12/16 | **IMPROVES**; C9 rule (≥ +1.0) not met | +0.83 / +0.95 |
| **Q2 mem_rep_gl − static_gl** | −0.059 | [−1.153, +0.942] | 8/14 | NO_MATERIAL_CHANGE | −0.05 / −0.07 |
| Q3 mem_rep_gl − mem_orig_gl | −0.145 | [−0.580, +0.153] | 4/13 | NO_MATERIAL_CHANGE | −0.09 / −0.21 |
| Q4 mem_orig_native − static_native | −0.219 | [−0.820, +0.391] | 6/14 | INCONCLUSIVE | −0.37 / −0.07 |
| S134 gl: mem_fix_gl − mem_orig_gl | −0.180 | [−0.655, +0.116] | 1/13 | NO_MATERIAL_CHANGE | −0.18 / −0.18 |
| S134 gl: mem_fix_gl − static_gl | −0.045 | [−1.107, +0.951] | 8/14 | NO_MATERIAL_CHANGE | −0.10 / +0.01 |
| mem_rep_gl − mem_fix_gl | −0.014 | [−0.174, +0.148] | 4/14 | NO_MATERIAL_CHANGE | +0.04 / −0.07 |

Arm means (dB): static_native 14.36, static_gl 15.25, mem_orig_native 14.00, mem_orig_gl 15.48, mem_fix_gl 15.15,
mem_rep_gl 15.14.

## What this settles
1. **Convention.** Converting the dataset's OpenCV poses to the OpenGL input VMem expects improves static generation
   by +0.89 dB (CI excludes 0), with the same direction and similar size in both seed/hardware blocks (+0.83 / +0.95).
   C9 (2 seeds) was underpowered. This is measured for the static arm. The sealed static results used native and
   understate it by about this much; the memory arms were not re-measured under both conventions here. The pre-registered C9 "confirmed"
   bar (+1.0 dB) is not met and is reported as such.
2. **Memory.** The repair changes the map (scale via KPS, coverage via chunked priming, convention gl; gate 14/14).
   It produces no detectable PSNR difference against static (Q2 −0.06 dB, CI [−1.15, +0.94], wide; scenes cancel)
   or against the broken memory (Q3, S134). These are NO_MATERIAL_CHANGE verdicts under the ±0.2 dB rule, not
   equivalence tests. This is consistent with S135's mechanism: retrieval is pose-distance NMS, so map quality
   rarely changes which frames are chosen.
3. The report's `memory_nms_on_clean − static = −0.485 dB` (2 seeds) becomes **−0.22 dB, CI [−0.82, +0.39]**, at
   8 seeds. Verdict INCONCLUSIVE (|mean| > 0.2, CI covers 0). It no longer supports a negative memory effect.

## Limits
Exposed panel, 2 scenes, 14–16 windows, 8 seeds, PSNR only, one frozen consumer. Pairing is within site. Hardware is
confounded with the seed block (H800 42,7,1,2; 3090 3,4,5,6), so per-site differences are not hardware-only. Q1/Q2
agree in direction across blocks; Q3/Q4 differ more. Twelve context keys are shared by two or three arms by design
(codex R250).
