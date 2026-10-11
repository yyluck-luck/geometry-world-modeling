# S143 result — the context the warp prefers is not the context VMem's generator prefers (exploratory, exposed chess)

Protocol: `PROTOCOL.md` (frozen 0cabac3c before any generation; Amendments 1–2 before any S143 score; Amendment 3 after the
discovery analysis and before any fresh-seed score). Idea: codex `gpt-6-astra` (ultra) R259; rejection rounds R260, R261.
Status: **exploratory case study on an exposed panel**; consumer-specific evidence utility as a concept is not new (FAR,
arXiv:2609.34677). `new_method_validated=false`, `novelty_authorization=NONE`.

## Execution
- Pool (`POOL.json`, SHA 0eea0997…): 24 S139 chess windows × 6 unique ordered sets (rules: 1 static_recent, 2 mem_pose,
  3 mem_vmem, 4 nearest-4, 5 coverage-greedy over 32-frame-bank CUT3R + KPS depth, 6 random); every set sorted by bank
  index; no duplicates arose. All rule-5 KPS records finite and OK.
- Warps: 144 sets × 4 targets, S139 CPU pipeline (all KPS OK); scored once per (window, set) (`results/WARP_SCORES.json`).
- Generation: frozen VMem (gen_s141.py, zero-init adapters = base), 144 sets × seeds 3–6 = 576 outputs on two RTX 3090,
  complete windows per GPU; replay gate passed (S139 mem_vmem window 0 seed 3 byte-identical, 913394e0…).

## Discovery results (frozen analysis, `results/S143_ANALYSIS.json`)
| quantity | value |
|---|---|
| **R_2seed_hindsight** (cross-fitted two-seed hindsight selector minus warp-selected set, held-out seed fold) | **+0.320 dB [+0.186, +0.458]**, 18/24 windows > 0 |
| pair means (seq-01→02 / 04→03 / 06→05); leave-one-pair-out | +0.359 / +0.359 / +0.243; 0.301–0.359 |
| frozen null 95th percentiles (full-panel factor / independent windows); tail p | 0.291 / 0.098; p = 0.035 / 2e-5 |
| threshold max(0.20, null95s) | 0.291 → **passed**; spread gate (mean best − worst warp 2.84 dB ≥ 1) passed |
| window-specific structure: selector − best single rule (rule 4 in both folds) | +0.275 [+0.120, +0.445] ≥ 0.216 → passed |
| within-window Spearman(Q_W, Q_G), mean | 0.16 |
| SSIM-reselected R (exploratory) | +0.014 [+0.004, +0.024] |

Per-rule means (descriptive):
| rule | warp PSNR | generated PSNR | generated SSIM | warp best in |
|---|---|---|---|---|
| 1 static_recent | 13.11 | 11.49 | 0.487 | 1/24 |
| 2 mem_pose | 14.30 | 11.58 | 0.484 | 1/24 |
| 3 mem_vmem (VMem's retrieval) | 14.38 | **11.19** | 0.465 | 1/24 |
| 4 nearest-4 | 14.30 | **11.94** | 0.500 | 6/24 |
| 5 coverage-greedy | **15.41** | 11.92 | 0.493 | 14/24 |
| 6 random | 14.05 | 11.38 | 0.482 | 1/24 |
Copy-nearest baselines: whole bank 12.22 dB; within sets 11.44–12.19.

**Decision (pre-registered wording):** on this exposed panel and fixed slot policy, the B2-PSNR selector leaves a held-seed
VMem-PSNR shortfall (+0.32 dB) relative to a target-informed two-seed selector, under the stated null sensitivities; and the
preference structure is window-specific beyond a single global rule.

## Reading (discovery)
- Geometric evidence utility and generator benefit rank the same context sets differently (Spearman 0.16).
- The generator does best with the frames whose cameras are closest to the targets (nearest-4, no diversity filter) and
  worst with VMem's own retrieval, which applies pose-NMS for diversity. The warp does best with coverage-maximising sets.
  This contrasts with VMem's own ablation on RealEstate10K cycles (surfel retrieval > camera distance); the regimes and the
  exact baselines differ (codex R264 examines this).
- Sorting mem_vmem into bank order lowered its warp from 14.57 to 14.38 dB: context order matters to CUT3R.

## Fresh seeds 42, 7, 1, 2 (Amendments 1–3; `results/S143_FRESH.json`; descriptive, seed panels as units)
Selections frozen from discovery seeds only and saved before any fresh contrast (`results/S143_FRESH_FROZEN_SELECTIONS.json`);
fresh generation passed the provenance gate (generator, helper, plan, scorer identical to discovery). 576 cells, all RTX 3090.
| contrast | mean | fresh seed panels (42 / 7 / 1 / 2) | pairs | descriptive gate |
|---|---|---|---|---|
| C_frozen4_discovery: c_G_disc − c_W | **+0.384 dB** | +0.37 / +0.28 / +0.39 / +0.49 | +0.45 / +0.45 / +0.25 | pass |
| local vs global: c_G_disc − rule 4 | +0.277 dB | +0.25 / +0.18 / +0.28 / +0.39 | +0.56 / +0.19 / +0.08 | pass |
| **Amendment 3: nearest-4 − mem_vmem (VMem retrieval)** | **+0.738 dB** | +0.82 / +0.90 / +0.60 / +0.63 | +0.56 / +0.56 / +1.10 (17/24 windows) | pass |
| Amendment 3: nearest-4 − c_W | +0.108 dB | +0.12 / +0.10 / +0.11 / +0.10 | −0.10 / +0.26 / +0.17 | fail (< 0.20) |
| Amendment 3: nearest-4 − static | +0.442 dB | +0.51 / +0.48 / +0.47 / +0.31 | +0.26 / +0.44 / +0.63 | pass |
Independent recomputation (separate minimal code): R = 0.320443 (discovery), nearest-4 − mem_vmem = +0.747 (discovery) /
+0.738 dB (fresh), equal to the analysis outputs.

**Reading.** The discovery pattern holds on fresh seeds: the generator-preferred package beats the warp-preferred one
(+0.38 dB, every seed panel), and the simple nearest-camera rule beats VMem's own surfel retrieval by +0.74 dB for VMem's
own generator (every seed panel, every sequence pair). This is seed-level replication on the same exposed room; a scene-level
test on untouched rooms is S146. Nearest-4 is not reliably better than the warp-preferred set (+0.11, below the bar).

## Limits
One exposed scene (three sequence pairs sharing history banks), 24 windows, six construction rules, one frozen consumer,
reused discovery seeds; selectors are target-informed (not deployable); utilities are specific to this warp predictor and
PSNR.
