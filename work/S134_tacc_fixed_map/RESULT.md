# S134 result — step A only. The map gate failed (11/14), so no generation, as pre-registered

Protocol: `PROTOCOL.md` (+ Amendment 1). Sites: SuperPOD H800 job 671986 (canonical) and TACC gpu13 RTX 3090
(cross-check). `new_method_validated=false`, `novelty_authorization=NONE`.

## Harness
- The H800 native/orig contexts reproduce the sealed C8 job 609623 contexts **14/14 for both NMS-on and NMS-off**.
- TACC setup: all 5 weights match the transfer receipt by SHA-256, and the env is the exact SuperPOD freeze
  (Python 3.11.16, torch 2.7.0+cu126). The model-process stage holds no depth and no target color. Windows overlap,
  so one window's target can be another window's bank frame, but each window's process reads only its own bank
  (as in C8/C9).

## Map gate (native, S133 fix) — FAIL
Window scale ratio = median rendered surfel depth / median dataset depth, at target views, H800.

| | in [0.5, 2] | > 10 | < 0.1 | median own-render corr |
|---|---|---|---|---|
| native orig | 7/14 | 5 | 0 | 0.22 |
| native fix | **11/14** | 0 | 0 | 0.12 |

The fix removes every blow-up, but 13 w350 (0.43), 14 w100 (0.27) and 14 w150 (0.11) stay below 0.5. The gate needed
≥ 12/14, so **step B was not run**. The own-render correlation stays low under native (camera axes flipped relative
to CUT3R; see C8/C9).

## What the fix changes in retrieval (H800, VMem default clean NMS-on)
Contexts change in only **4/14** windows: 13 w150, 13 w200, 14 w100, 14 w150. NMS-off changes in 2/14.
The ×300–700 blow-up windows 13 w250/w300/w350 keep **identical** contexts. S135 explains why.

## Cross-hardware reproducibility of VMem retrieval
Same code, inputs and weights. H800 and RTX 3090 agree on NMS-on contexts in only **8/14** (orig) and **9/14** (fix)
windows. On the 3090, orig scene_13 w200 also fails with the `IndexError` that C9 saw under gl on H800.
S135 traces the divergence to TF32: CUT3R's `croco.py` sets `torch.backends.cuda.matmul.allow_tf32 = True` globally
on import, and VMem's pose geodesic is then computed with TF32 on the H800.

## gl variants (Amendment 1)
| H800 | in [0.5, 2] | > 10 | median own-render corr | BLOCKED |
|---|---|---|---|---|
| gl orig | 6/13 | 5 | 0.61 | scene_13 w200 (IndexError, as in C9) |
| gl fix | **12/14** | 0 | **0.63** | none |

**gl + fix passes the Amendment-1 gate.** The gl arms are therefore generated, inside S136 (plan_v1b: static_gl,
mem_orig_gl, mem_fix_gl, 8 seeds, both sites). Under gl the fix changes NMS-on contexts in 2/13 windows.
The convention lifts the own-render correlation from about 0.1–0.2 (native) to about 0.6. That is the geometric
side of the C8/C9 convention mismatch.

## Files
`results/stepA_superpod/` (H800 receipts, maps, map evaluations, context report), `results/stepA_tacc/` (3090 receipts).
