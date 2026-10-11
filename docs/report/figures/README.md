# R270 report figures

**Complete: 8 figures / 16 verified exports.**

Source snapshot: `260bc5c87ce8753cf38561496083bbb1d40d3432`. CPU only; all numeric inputs are Git blobs from this snapshot. Local ignored/uncommitted JSONs, source images, target frames, weights and datasets are not read.

`new_method_validated=false`; `novelty_authorization=NONE`.

R270 adds Figure 1, replaces fig04's zero-origin bars with arm-minus-B2 dots and an A_R-relative gate, and moves fig02a values into separate columns outside the plotting axes. Static-context B2 SSIM is unavailable and is explicitly marked N/A. The committed R269 script and README are preserved in `r269_snapshot/`.

## Reproduce

From the repository root:

```bash
/opt/homebrew/opt/python@3.13/bin/python3.13 -B docs/report/figures/make_figures.py --revision 260bc5c87ce8753cf38561496083bbb1d40d3432
```

The script prints every plotted value and interval with its JSON key, verifies source consistency, writes this README, and checks export signatures and PNG DPI. `--revision` freezes inputs even if another process advances HEAD. Missing sources are explicit and never replaced with different-seed results or transcribed report prose.

## Produced figures

### S139 / S140 chess arm means and contrasts

[fig01_s139_s140_chess.png](fig01_s139_s140_chess.png) · [fig01_s139_s140_chess.pdf](fig01_s139_s140_chess.pdf)

B2(mem_vmem) exceeds VMem(mem_vmem) in PSNR but trails it in SSIM; WGS minus B2 includes zero for PSNR and is positive for SSIM. The top panels show every requested arm, with unavailable static-context B2 SSIM explicitly marked N/A. The bottom panels retain the archived paired window-bootstrap intervals on seed-averaged windows, not confidence intervals over scenes or seed panels. S139's window interval is used, not its separate pair-cluster sensitivity interval.

Sources: `S139`, `S139_SSIM`, `S140`, `B2_STATIC`, `B2_MEM`, `S139_B`.

### S141 · Chess: primary contrasts and supporting comparisons

[fig02a_s141_chess.png](fig02a_s141_chess.png) · [fig02a_s141_chess.pdf](fig02a_s141_chess.pdf)

A_mem improves over base_mem in the archived PSNR and SSIM contrasts; B_mem vs warp has opposite signs across the metrics. Diamonds identify the registered primary arm contrasts (PSNR primary, SSIM secondary); circles are supporting comparisons, including the seed-subset replica. All use window means over seeds 3–6 and archived window-bootstrap 95% intervals. A is attention LoRA; B adds the warp-latent branch. Chess was excluded from training but exposed in prior stages.

Sources: `S141`.

### S141 · Chess: exploratory contrasts

[fig02b_s141_exploratory.png](fig02b_s141_exploratory.png) · [fig02b_s141_exploratory.pdf](fig02b_s141_exploratory.pdf)

The exploratory contrasts do not replace the registered primaries. Every top-level exploratory contrast in the analysis JSON is included, with the archived 95% window-bootstrap CI; history-favourable subgroups and covered/hole analyses are outside this requested panel.

Sources: `S141`.

### S141 · RGB-D Scenes: secondary transfer panel

[fig02c_s141_rgbd.png](fig02c_s141_rgbd.png) · [fig02c_s141_rgbd.pdf](fig02c_s141_rgbd.pdf)

A_static improves over base_static, while B_static trails the warp and both learned comparators in these archived contrasts. This exposed secondary panel uses static contexts, seed-averaged windows and archived 95% window-bootstrap intervals.

Sources: `S141`.

### S143 per-rule warp versus generated PSNR

[fig03a_s143_rules.png](fig03a_s143_rules.png) · [fig03a_s143_rules.pdf](fig03a_s143_rules.pdf)

The rule with the highest mean warp PSNR differs from the rule with the highest mean generated PSNR. Each point is an archived per-rule discovery mean. POOL maps each rule to a per-window set; its WARP_SCORES mean is checked against Q_W. No images or target frames are read.

Sources: `S143`, `WARP`, `POOL`.

### S143 discovery and fresh contrasts

[fig03b_s143_contrasts.png](fig03b_s143_contrasts.png) · [fig03b_s143_contrasts.pdf](fig03b_s143_contrasts.pdf)

The archived discovery and fresh contrasts have positive means. The selectors are target-informed hindsight selectors on fixed exposed chess windows, not deployable target-blind selectors or fresh-scene confirmation. Discovery uses two-seed cross-fitting; fresh uses selections frozen from all discovery seeds. Fresh seed panels are the unit and no formal seed-level inference is made. Fresh intervals are explicitly descriptive window bootstraps, not confidence intervals over seed panels. The discovery JSON contains no seed-panel points.

Sources: `S143`, `FRESH`.

### S144 development arm/control differences from B2

[fig04_s144_development.png](fig04_s144_development.png) · [fig04_s144_development.pdf](fig04_s144_development.pdf)

S144 fails its archived development gate. Every arm/control is shown relative to B2 on a zoomed dot plot; A_none is explicitly annotated off scale with its absolute PSNR. The dashed control ceiling is (A_R − B2) − 0.20 dB, so only dagger-marked gate controls must lie to its left; the dotted line marks A_R. V is the warp's VAE round-trip; F/A are frozen/adapted backbones, C/R are terminal clamp/release, P replaces covered pixels, REV reverses the paste, and BL is a development-fitted global blend whose score is optimistic. The complete gate additionally checks interaction, SSIM and per-sequence signs.

Sources: `DEV`, `GATE`.

### S146 per-room KPS diagnostic

[fig05_s146_kps.png](fig05_s146_kps.png) · [fig05_s146_kps.pdf](fig05_s146_kps.pdf)

The KPS diagnostic records non-finite whole objectives and low positive-depth fractions in some room/construction cells. Non-finite means not math.isfinite(err), including Infinity. Each denominator is the number of windows in that room, after pooling shards. The depth statistic is the minimum over every stored view, including constructions with non-finite objectives; n_views is not used as the objective denominator.

Sources: `KPS0`, `KPS1`, `KPS2`.

## Missing sources / limitations

None of the requested input files are missing from this snapshot.

- Figure 1: B2(static_recent) SSIM is not recorded in the committed inputs. B2_STATIC:/rows/* contains psnr but no ssim; S140 warps score mem_vmem contexts only. The SSIM cell is explicitly N/A, not zero or an estimate.

The brief's POOL file is committed at `work/S143_context_ranking/POOL.json`, outside its `results/` directory. S141 is split across three figures and S143 across two to keep individual labels readable. No new statistical intervals are fitted: only archived intervals are shown; arm means and diagnostics without supplied intervals remain descriptive.

## Source files and content hashes

| Alias | Committed file | Git blob | SHA-256 |
|---|---|---|---|
| S139 | `work/S139_crossseq_revisit/results/S139_ANALYSIS.json` | `703557dac59fe0131165d0898a0610b2caf9fa74` | `862c26f7563f9eab9aec5bb95f6a2868ac2b89ee3835aa022cad87ef7bdaaab0` |
| S139_B | `work/S139_crossseq_revisit/results/S139_BASELINE_CONTRASTS.json` | `084b44709015a5cff8c62de32132416f54fb4462` | `cd281a98cd2de24b03bab085fcbdbf1830da2723d3b694ae3146ce5122a3fbee` |
| S140 | `work/S140_warp_guided/results/CONFIRM_ANALYSIS.json` | `786cc9a8e01027a41d7f350ef155ac6ac713e4b9` | `ef2b0a87654c0c7d872f46f8dca93b86c7ed0ea48d997d498d6183ac62026865` |
| S139_SSIM | `work/S140_warp_guided/results/s139_ssim/S139_SSIM_ANALYSIS.json` | `80229ce6bfdb0aef24ce768ff8466b2527cca31d` | `d0ade410a32d464d174319adb961d3a4a8f3b450a23013ec33f86a783910df31` |
| B2_STATIC | `work/S139_crossseq_revisit/BASE_b2_static.json` | `563ff0d2c713caa7ec848780fc1621a7a8a714cc` | `9c95977f93a923bb31a133aac8a0c9f443b9f0ff32c9e8f78d693ac81fdfe8cb` |
| B2_MEM | `work/S139_crossseq_revisit/BASE_b2_mem_vmem.json` | `dcdcec41da88ed26f865dbc0a8a81f6da1440e61` | `478407dd57883cebb255b3237424a15ef6eb0b505351433e256a8e56aeb3db4f` |
| S141 | `work/S141_finetune/results/S141_ANALYSIS.json` | `dccc2292eac44249619720757ec9e88a3ee9d232` | `323848ff27da6d96b78d10506f3257849799a33802ff655781f87122c6e7a350` |
| S143 | `work/S143_context_ranking/results/S143_ANALYSIS.json` | `fe87bc258c46ac4e8d005b80dbdfd3c7dafd1eae` | `22c5b75a4d7783d93da307d6b5bb725b2dd92755280401b9b550bb15b05eeed3` |
| FRESH | `work/S143_context_ranking/results/S143_FRESH.json` | `a28fbc0a65fdd1b23e7ec904412611bc1322f977` | `ebe355b4c5bd28e710c614cd06a6646a82e8c4fc2e46fa97b7425a51834ed80d` |
| WARP | `work/S143_context_ranking/results/WARP_SCORES.json` | `95ebb287a67fae6bd94deae7c1e88c88231dc70c` | `d0d4ded32f166e53bdabf9aeacde6675a12f3ede4a127f283d35d607951b3982` |
| POOL | `work/S143_context_ranking/POOL.json` | `55b22b464dd9370d983e5fa29c82b61062d38132` | `0eea09978b17f71491a459651e9c39a2925af97f948c9b597406b48d7957cad5` |
| DEV | `work/S144_A_wgs/results/SCORES_dev.json` | `66312212f59c895ae12fbc76c3dd0fb5ef972bc6` | `a8a6f634166a7c68c89307141fc35ca752b04feaf523ae5081643ba4a732f963` |
| GATE | `work/S144_A_wgs/results/DEV_GATE.json` | `afb542155b1e084d9ecfd9c1693cb25cada7931e` | `677a559b6a6027cd41fd3ffbaab019b6feb7650e2184835735edeecafaeeee18` |
| KPS0 | `work/S146_fresh12/diag/KPS_DIAG_0.json` | `80b24269d4229048cad0e28cfa56a6627a5c3c38` | `c5c629364c34331ed2c7a31cfa31e16c3809d6ed766323ff4338dbe326400396` |
| KPS1 | `work/S146_fresh12/diag/KPS_DIAG_1.json` | `f0164f214e40510bba21867147dc0c8928302cf8` | `b7e5e8e9f8ec10154e1575e4886bef40ee434dfd1c65ed1407e4310ce03a7aea` |
| KPS2 | `work/S146_fresh12/diag/KPS_DIAG_2.json` | `0dee01f09d895c40acf73849a08f38a447a8e6c3` | `6e6970452868dbb2a595e73e9c167f5f9099e9a70a4aac42395c7c504c1fb17e` |

## Figure 1 schema mapping

| Quantity | Exact source/key | Treatment |
|---|---|---|
| VMem arm PSNR means | `S139:/arm_means_db/{static_recent,mem_vmem,mem_pose}` | Archived numeric means |
| VMem arm SSIM means | `S139_SSIM:/ssim_means/{static_recent,mem_vmem,mem_pose}` | Archived numeric means |
| B2 static PSNR | `B2_STATIC:/rows/*/psnr`, identified by `/rows/*/window_id` | Arithmetic mean over unique windows |
| B2 static SSIM | No field in `B2_STATIC:/rows/*` | N/A; no score or CI fabricated |
| B2 memory and WGS means | `S140:/{psnr_db,ssim}/means/{B2,WGS}` | Archived numeric means |
| VMem memory minus static PSNR | `S139:/contrasts/PRIMARY_mem_vmem_vs_static_recent/{mean_db,ci95_window}` | Window CI, not pair-cluster CI |
| VMem memory minus static SSIM | `S139_SSIM:/contrasts/mem_vmem-static_recent_ssim/{mean,ci}` | Archived window CI |
| B2 memory minus VMem memory | `S140:/{psnr_db,ssim}/B2_minus_VMem/{mean,ci95}` | Archived numeric means and window CIs |
| WGS minus B2 memory | `S140:/{psnr_db,ssim}/WGS_minus_B2/{mean,ci95}` | Archived numeric means and window CIs |
| Baseline consistency | `B2_MEM:/rows/*/psnr`; `S139_B:/B2_mem_vmem - VMem mem_vmem/all` | Mean and rounded-text checks only; the rounded string is not a plotted input |

Schema distinctions are intentional: S139 PSNR has `mean_db` and `ci95_window`, S139 SSIM has `mean` and `ci`, and S140 has `mean` and `ci95`. The baseline contrast JSON contains formatted strings, not full-precision numeric estimates. Arm means have no supplied CIs. S140's published B2 SSIM is retained: the analysis merges duplicate warp records with last-input precedence, not site averaging (`work/S140_warp_guided/analyze_confirm_s140.py:11`).

## Definitions and code provenance

JSON paths below use JSON Pointer syntax; `*` and `[room=...]` explicitly denote the filters described in the derivation column. `MEASURED` means an archived experimental summary copied from JSON, not a new experiment. `DERIVED` means a deterministic aggregation of stored measurements. Decimal strings preserve the loaded Python floats; plot labels are rounded only for legibility.

- S139 contrasts average paired seeds per window and use window-bootstrap intervals: `work/S139_crossseq_revisit/analyze_s139.py:21`, `:30`, `:38`. Arm means: `:56`. Static B2 context selection and PSNR-only output: `work/S139_crossseq_revisit/baselines_s139.py:49`, `:68`.
- S140 means and window-bootstrap intervals: `work/S140_warp_guided/analyze_confirm_s140.py:21`, `:25`, `:28`, `:32`. The stored intervals use 10,000 resamples with RNG seed 0 and percentile endpoints 2.5 and 97.5; none are refitted here.
- S141 window-mean contrasts and bootstrap: `work/S141_finetune/analyze_s141.py:22`, `:33`, `:63`, `:70`, `:96`; registration and scope: `work/S141_finetune/PROTOCOL.md:51`, `:72`.
- S144 seed averaging and gate: `work/S144_A_wgs/analyze_s144.py:14`, `:28`, `:49`, `:56`; control definitions: `work/S144_A_wgs/PROTOCOL.md:9`. The gate requires A_R minus A_C and every mandatory control to be at least +0.20 dB (`:20`); in arm-minus-B2 coordinates the control ceiling is `(A_R - B2) - 0.20`. The +0.20 constant is ANALYTICAL, encoded in `GATE:/checks/means_ge_0.20` and corroborated by the protocol and analyzer, not an experimental measurement.
- S143 rule names: `work/S143_context_ranking/PROTOCOL.md:14`. Rule mapping is checked against the committed POOL and WARP files. Fresh inference scope is stated by `FRESH:/note`. No discovery seed-panel points are fabricated.
- S146 uses the stored whole-objective `err` and `positive_depth_frac` fields. A non-finite objective is counted once per construction/window; it is not a per-view failure count.

## Design and validation

Experimental-results guidance from the figure-designer skill was applied: vector PDFs plus 300 dpi PNGs, DejaVu Sans at readable panel sizes, an Okabe–Ito qualitative palette and viridis diagnostic scales, direct labels/marker shapes in addition to colour, and no fitted trend or selective winning-arm display. Forest plots include zero; S144 is an explicitly zoomed dot plot of differences with the off-scale value annotated; scatter and heatmap axes are explicit. Use panels near their intended full slide/report width; do not shrink multi-panel figures into a narrow column.

The complete final script stdout follows, including the exact-value table, consistency checks, export sizes and SHA-256 hashes. Separate verification commands and their complete output are in `verification.log` when supplied. No root linter configuration or plotting test suite is configured. The full unrelated suite is outside this restricted-write figure task; a scoped existing CPU metric test is documented in that log. This is a visualization of archived results, not a new model experiment.

## Exact command and complete stdout

```text
DATA_REVISION 260bc5c87ce8753cf38561496083bbb1d40d3432
COMMAND /opt/homebrew/opt/python@3.13/bin/python3.13 -B docs/report/figures/make_figures.py --revision 260bc5c87ce8753cf38561496083bbb1d40d3432
SCRIPT_SHA256 97ea30f576df42ae2dfaea08dec656a8dccb691c7905da1118c5badd1f0db6a8
ENV Python=3.13.0 NumPy=2.4.6 Matplotlib=3.10.9
new_method_validated=false; novelty_authorization=NONE
LIMITATION Figure 1: B2(static_recent) SSIM is not recorded in the committed inputs. B2_STATIC:/rows/* contains psnr but no ssim; S140 warps score mem_vmem contexts only. The SSIM cell is explicitly N/A, not zero or an estimate.
PLOTTED VALUES (round-trip Python float representations)
figure | label | metric | value | ci95_low | ci95_high | evidence | source:key | derivation
fig01_s139_s140_chess | VMem · static_recent | psnr_db | 11.544654511739592 | None | None | MEASURED | S139:/arm_means_db/static_recent | direct
fig01_s139_s140_chess | VMem · mem_vmem | psnr_db | 11.364143104597444 | None | None | MEASURED | S139:/arm_means_db/mem_vmem | direct
fig01_s139_s140_chess | VMem · mem_pose | psnr_db | 11.54636676404582 | None | None | MEASURED | S139:/arm_means_db/mem_pose | direct
fig01_s139_s140_chess | B2 · static_recent | psnr_db | 13.114046887387012 | None | None | DERIVED | B2_STATIC:/rows/*/psnr | arithmetic mean over unique /rows/*/window_id; deterministic warp, no seed replication
fig01_s139_s140_chess | B2 · mem_vmem | psnr_db | 14.57238774192119 | None | None | MEASURED | S140:/psnr_db/means/B2 | direct
fig01_s139_s140_chess | S140 WGS · mem_vmem | psnr_db | 14.592669875811927 | None | None | MEASURED | S140:/psnr_db/means/WGS | direct
fig01_s139_s140_chess | VMem · static_recent | ssim | 0.4892834044682483 | None | None | MEASURED | S139_SSIM:/ssim_means/static_recent | direct
fig01_s139_s140_chess | VMem · mem_vmem | ssim | 0.4702946466471379 | None | None | MEASURED | S139_SSIM:/ssim_means/mem_vmem | direct
fig01_s139_s140_chess | VMem · mem_pose | ssim | 0.4802337164292112 | None | None | MEASURED | S139_SSIM:/ssim_means/mem_pose | direct
fig01_s139_s140_chess | B2 · mem_vmem | ssim | 0.431765907133619 | None | None | MEASURED | S140:/ssim/means/B2 | direct
fig01_s139_s140_chess | S140 WGS · mem_vmem | ssim | 0.4569128923273335 | None | None | MEASURED | S140:/ssim/means/WGS | direct
fig01_s139_s140_chess | VMem(mem_vmem) − VMem(static_recent) | contrast psnr_db | -0.18051140714214683 | -0.5177184693492473 | 0.14474936062757815 | MEASURED | S139:/contrasts/PRIMARY_mem_vmem_vs_static_recent/{mean_db,ci95_window} | direct
fig01_s139_s140_chess | B2(mem_vmem) − VMem(mem_vmem) | contrast psnr_db | 3.208244637323745 | 2.8412112010956028 | 3.5812008243596134 | MEASURED | S140:/psnr_db/B2_minus_VMem/{mean,ci95} | direct
fig01_s139_s140_chess | WGS − B2(mem_vmem) | contrast psnr_db | 0.020282133890735892 | -0.09460827842278613 | 0.134346219561331 | MEASURED | S140:/psnr_db/WGS_minus_B2/{mean,ci95} | direct
fig01_s139_s140_chess | VMem(mem_vmem) − VMem(static_recent) | contrast ssim | -0.018988757821110386 | -0.03233085443110516 | -0.0060680027653385645 | MEASURED | S139_SSIM:/contrasts/mem_vmem-static_recent_ssim/{mean,ci} | direct
fig01_s139_s140_chess | B2(mem_vmem) − VMem(mem_vmem) | contrast ssim | -0.03852873951351891 | -0.06852788762868538 | -0.008501490620741006 | MEASURED | S140:/ssim/B2_minus_VMem/{mean,ci95} | direct
fig01_s139_s140_chess | WGS − B2(mem_vmem) | contrast ssim | 0.0251469851937145 | 0.014721126846173624 | 0.03618809998685416 | MEASURED | S140:/ssim/WGS_minus_B2/{mean,ci95} | direct
fig02a_s141_chess | PRIMARY_A: A_mem - base_mem | psnr_db | 0.330455947375833 | 0.07821663972646646 | 0.5848574621557386 | MEASURED | S141:/contrasts/psnr_db/PRIMARY_A: A_mem - base_mem/{mean,ci95} | direct
fig02a_s141_chess | PRIMARY_B: B_mem - B2_warp | psnr_db | -3.5577375522453565 | -3.9125100163074857 | -3.201337443267911 | MEASURED | S141:/contrasts/psnr_db/PRIMARY_B: B_mem - B2_warp/{mean,ci95} | direct
fig02a_s141_chess | A_mem - A_static | psnr_db | -0.3317431131225079 | -0.6693554968797133 | 0.005715392610856676 | MEASURED | S141:/contrasts/psnr_db/A_mem - A_static/{mean,ci95} | direct
fig02a_s141_chess | B_mem - base_mem | psnr_db | -0.260244240843249 | -0.5311888817625581 | 0.01971167513985996 | MEASURED | S141:/contrasts/psnr_db/B_mem - base_mem/{mean,ci95} | direct
fig02a_s141_chess | A_static - base_static | psnr_db | 0.44786856671250036 | 0.09563757953943759 | 0.8216873025044766 | MEASURED | S141:/contrasts/psnr_db/A_static - base_static/{mean,ci95} | direct
fig02a_s141_chess | base_mem - base_static (S139 replica, seeds 3-6) | psnr_db | -0.21433049378584057 | -0.5324032397005126 | 0.09948471584740064 | MEASURED | S141:/contrasts/psnr_db/base_mem - base_static (S139 replica, seeds 3-6)/{mean,ci95} | direct
fig02a_s141_chess | PRIMARY_A: A_mem - base_mem | ssim | 0.017847964462513726 | 0.0057009362790267915 | 0.030187338774946205 | MEASURED | S141:/contrasts/ssim/PRIMARY_A: A_mem - base_mem/{mean,ci95} | direct
fig02a_s141_chess | PRIMARY_B: B_mem - B2_warp | ssim | 0.07331398331249754 | 0.04552474054895962 | 0.0989613422968735 | MEASURED | S141:/contrasts/ssim/PRIMARY_B: B_mem - B2_warp/{mean,ci95} | direct
fig02a_s141_chess | A_mem - A_static | ssim | -0.0076607483594367904 | -0.020802626126290608 | 0.005358817601033176 | MEASURED | S141:/contrasts/ssim/A_mem - A_static/{mean,ci95} | direct
fig02a_s141_chess | B_mem - base_mem | ssim | 0.03685721972336372 | 0.026482266022746143 | 0.04776606932282448 | MEASURED | S141:/contrasts/ssim/B_mem - base_mem/{mean,ci95} | direct
fig02a_s141_chess | A_static - base_static | ssim | 0.006768394261598587 | -0.005190736096119508 | 0.018894955345119032 | MEASURED | S141:/contrasts/ssim/A_static - base_static/{mean,ci95} | direct
fig02a_s141_chess | base_mem - base_static (S139 replica, seeds 3-6) | ssim | -0.018740318560351927 | -0.031528798822546375 | -0.006861493523077422 | MEASURED | S141:/contrasts/ssim/base_mem - base_static (S139 replica, seeds 3-6)/{mean,ci95} | direct
fig02b_s141_exploratory | B_mem - A_mem (exploratory) | psnr_db | -0.590700188219082 | -0.7667898344263362 | -0.4149773790959703 | MEASURED | S141:/contrasts/psnr_db/B_mem - A_mem (exploratory)/{mean,ci95} | direct
fig02b_s141_exploratory | B_static - B2_warp_static | psnr_db | -2.129292676267967 | -2.63706888810361 | -1.5988635784910454 | MEASURED | S141:/exploratory_Bstatic/psnr_db/B_static - B2_warp_static/{mean,ci95} | direct
fig02b_s141_exploratory | B_mem - B_static | psnr_db | 0.029895978556787533 | -0.1520021387686195 | 0.2312440107741306 | MEASURED | S141:/exploratory_Bstatic/psnr_db/B_mem - B_static/{mean,ci95} | direct
fig02b_s141_exploratory | B_static - A_static | psnr_db | -0.9523392798983773 | -1.242393772572586 | -0.6566392095593804 | MEASURED | S141:/exploratory_Bstatic/psnr_db/B_static - A_static/{mean,ci95} | direct
fig02b_s141_exploratory | B2_warp_mem - B2_warp_static | psnr_db | 1.4583408545341772 | 0.9056304137397878 | 2.051024686080295 | MEASURED | S141:/exploratory_Bstatic/psnr_db/B2_warp_mem - B2_warp_static/{mean,ci95} | direct
fig02b_s141_exploratory | (B_mem - B_static) - (A_mem - A_static) | psnr_db | 0.3616390916792955 | 0.030391032572317414 | 0.6960423405978284 | MEASURED | S141:/exploratory_Bstatic/psnr_db/(B_mem - B_static) - (A_mem - A_static)/{mean,ci95} | direct
fig02b_s141_exploratory | B_mem - A_mem (exploratory) | ssim | 0.019009255260849994 | 0.009763625283570339 | 0.02816586928868976 | MEASURED | S141:/contrasts/ssim/B_mem - A_mem (exploratory)/{mean,ci95} | direct
fig02b_s141_exploratory | B_static - B2_warp_static | ssim | 0.0505428406225595 | 0.022006396345750547 | 0.08023336388675184 | MEASURED | S141:/exploratory_Bstatic/ssim/B_static - B2_warp_static/{mean,ci95} | direct
fig02b_s141_exploratory | B_mem - B_static | ssim | -0.019680831503743928 | -0.03294197984699471 | -0.00637338433104257 | MEASURED | S141:/exploratory_Bstatic/ssim/B_mem - B_static/{mean,ci95} | direct
fig02b_s141_exploratory | B_static - A_static | ssim | 0.03102933840515713 | 0.018895604007411748 | 0.04312863594386726 | MEASURED | S141:/exploratory_Bstatic/ssim/B_static - A_static/{mean,ci95} | direct
fig02b_s141_exploratory | B2_warp_mem - B2_warp_static | ssim | -0.04245197419368196 | -0.07495839971415989 | -0.008171362782013605 | MEASURED | S141:/exploratory_Bstatic/ssim/B2_warp_mem - B2_warp_static/{mean,ci95} | direct
fig02b_s141_exploratory | (B_mem - B_static) - (A_mem - A_static) | ssim | -0.012020083144307137 | -0.026606598178235193 | 0.0024079309427179354 | MEASURED | S141:/exploratory_Bstatic/ssim/(B_mem - B_static) - (A_mem - A_static)/{mean,ci95} | direct
fig02c_s141_rgbd | A_static - base_static | psnr_db | 1.1615370047265947 | 0.6121227630232082 | 1.728599090857742 | MEASURED | S141:/rgbd_secondary/psnr_db/A_static - base_static/{mean,ci95} | direct
fig02c_s141_rgbd | B_static - B2_warp | psnr_db | -7.429620478250985 | -8.397425682668723 | -6.520815384882339 | MEASURED | S141:/rgbd_secondary/psnr_db/B_static - B2_warp/{mean,ci95} | direct
fig02c_s141_rgbd | B_static - base_static | psnr_db | -2.617291825226224 | -3.4254634642042694 | -1.8275434396230315 | MEASURED | S141:/rgbd_secondary/psnr_db/B_static - base_static/{mean,ci95} | direct
fig02c_s141_rgbd | B_static - A_static | psnr_db | -3.778828829952819 | -4.474120508530148 | -3.1671504801605184 | MEASURED | S141:/rgbd_secondary/psnr_db/B_static - A_static/{mean,ci95} | direct
fig02c_s141_rgbd | A_static - base_static | ssim | 0.03888142597861588 | 0.024022985599003732 | 0.05551552692486438 | MEASURED | S141:/rgbd_secondary/ssim/A_static - base_static/{mean,ci95} | direct
fig02c_s141_rgbd | B_static - B2_warp | ssim | -0.1630651978775859 | -0.21440653799509163 | -0.11497381273075012 | MEASURED | S141:/rgbd_secondary/ssim/B_static - B2_warp/{mean,ci95} | direct
fig02c_s141_rgbd | B_static - base_static | ssim | -0.056620510877110064 | -0.0737973057111958 | -0.03752222655457446 | MEASURED | S141:/rgbd_secondary/ssim/B_static - base_static/{mean,ci95} | direct
fig02c_s141_rgbd | B_static - A_static | ssim | -0.09550193685572594 | -0.11320483698218595 | -0.07793283616774715 | MEASURED | S141:/rgbd_secondary/ssim/B_static - A_static/{mean,ci95} | direct
fig03a_s143_rules | Rule 1: Static recent | warp PSNR dB | 13.11401564110696 | None | None | MEASURED | S143:/per_rule_means/1/Q_W | direct
fig03a_s143_rules | Rule 1: Static recent | generated PSNR dB | 11.48922492430492 | None | None | MEASURED | S143:/per_rule_means/1/Q_G | direct
fig03a_s143_rules | Rule 2: Pose NMS | warp PSNR dB | 14.302340101633597 | None | None | MEASURED | S143:/per_rule_means/2/Q_W | direct
fig03a_s143_rules | Rule 2: Pose NMS | generated PSNR dB | 11.578046203671269 | None | None | MEASURED | S143:/per_rule_means/2/Q_G | direct
fig03a_s143_rules | Rule 3: VMem retrieval | warp PSNR dB | 14.378107910072954 | None | None | MEASURED | S143:/per_rule_means/3/Q_W | direct
fig03a_s143_rules | Rule 3: VMem retrieval | generated PSNR dB | 11.190094111192636 | None | None | MEASURED | S143:/per_rule_means/3/Q_G | direct
fig03a_s143_rules | Rule 4: Nearest-4 | warp PSNR dB | 14.297765238408843 | None | None | MEASURED | S143:/per_rule_means/4/Q_W | direct
fig03a_s143_rules | Rule 4: Nearest-4 | generated PSNR dB | 11.93700455399753 | None | None | MEASURED | S143:/per_rule_means/4/Q_G | direct
fig03a_s143_rules | Rule 5: Coverage greedy | warp PSNR dB | 15.41430347084947 | None | None | MEASURED | S143:/per_rule_means/5/Q_W | direct
fig03a_s143_rules | Rule 5: Coverage greedy | generated PSNR dB | 11.917725370534484 | None | None | MEASURED | S143:/per_rule_means/5/Q_G | direct
fig03a_s143_rules | Rule 6: Random | warp PSNR dB | 14.051417766163008 | None | None | MEASURED | S143:/per_rule_means/6/Q_W | direct
fig03a_s143_rules | Rule 6: Random | generated PSNR dB | 11.380289371042409 | None | None | MEASURED | S143:/per_rule_means/6/Q_G | direct
fig03b_s143_contrasts | Discovery: hindsight selector − warp selector | PSNR contrast dB | 0.3204426551367352 | 0.18621406878824748 | 0.45803741621525984 | MEASURED | S143:/R_2seed_hindsight/{mean,ci95} | direct
fig03b_s143_contrasts | Discovery: local selector − global rule | PSNR contrast dB | 0.27530107138564425 | 0.11979204753953406 | 0.44496105376650114 | MEASURED | S143:/global_rule_gap/{mean,ci95} | direct
fig03b_s143_contrasts | Fresh: frozen hindsight selector − warp selector | PSNR contrast dB | 0.38448566771630205 | 0.24472311537486954 | 0.5367412648910487 | MEASURED | FRESH:/C_frozen4_discovery/{mean,window_bootstrap_ci95_descriptive} | direct
fig03b_s143_contrasts | Fresh: frozen hindsight selector − warp selector; seed 42 | seed-panel PSNR contrast dB | 0.37134612612406587 | None | None | MEASURED | FRESH:/C_frozen4_discovery/seed_panel_means/42 | direct
fig03b_s143_contrasts | Fresh: frozen hindsight selector − warp selector; seed 7 | seed-panel PSNR contrast dB | 0.2792607306597931 | None | None | MEASURED | FRESH:/C_frozen4_discovery/seed_panel_means/7 | direct
fig03b_s143_contrasts | Fresh: frozen hindsight selector − warp selector; seed 1 | seed-panel PSNR contrast dB | 0.3942270970989586 | None | None | MEASURED | FRESH:/C_frozen4_discovery/seed_panel_means/1 | direct
fig03b_s143_contrasts | Fresh: frozen hindsight selector − warp selector; seed 2 | seed-panel PSNR contrast dB | 0.4931087169823907 | None | None | MEASURED | FRESH:/C_frozen4_discovery/seed_panel_means/2 | direct
fig03b_s143_contrasts | Fresh: frozen local selector − global rule | PSNR contrast dB | 0.2767029469457284 | 0.12903204522370826 | 0.4256935108083881 | MEASURED | FRESH:/local_vs_global/{mean,window_bootstrap_ci95_descriptive} | direct
fig03b_s143_contrasts | Fresh: frozen local selector − global rule; seed 42 | seed-panel PSNR contrast dB | 0.2494466609580006 | None | None | MEASURED | FRESH:/local_vs_global/seed_panel_means/42 | direct
fig03b_s143_contrasts | Fresh: frozen local selector − global rule; seed 7 | seed-panel PSNR contrast dB | 0.18311346059562195 | None | None | MEASURED | FRESH:/local_vs_global/seed_panel_means/7 | direct
fig03b_s143_contrasts | Fresh: frozen local selector − global rule; seed 1 | seed-panel PSNR contrast dB | 0.2837703504437541 | None | None | MEASURED | FRESH:/local_vs_global/seed_panel_means/1 | direct
fig03b_s143_contrasts | Fresh: frozen local selector − global rule; seed 2 | seed-panel PSNR contrast dB | 0.39048131578553696 | None | None | MEASURED | FRESH:/local_vs_global/seed_panel_means/2 | direct
fig03b_s143_contrasts | Fresh: nearest-4 − VMem retrieval | PSNR contrast dB | 0.7382526642964204 | 0.45412143040243313 | 1.0299661976035481 | MEASURED | FRESH:/rule_contrasts/r_disc(rule 4) - rule 3 (mem_vmem)/{mean,window_bootstrap_ci95_descriptive} | direct
fig03b_s143_contrasts | Fresh: nearest-4 − VMem retrieval; seed 42 | seed-panel PSNR contrast dB | 0.8213982755145857 | None | None | MEASURED | FRESH:/rule_contrasts/r_disc(rule 4) - rule 3 (mem_vmem)/seed_panel_means/42 | direct
fig03b_s143_contrasts | Fresh: nearest-4 − VMem retrieval; seed 7 | seed-panel PSNR contrast dB | 0.9037378398595625 | None | None | MEASURED | FRESH:/rule_contrasts/r_disc(rule 4) - rule 3 (mem_vmem)/seed_panel_means/7 | direct
fig03b_s143_contrasts | Fresh: nearest-4 − VMem retrieval; seed 1 | seed-panel PSNR contrast dB | 0.6015598476098764 | None | None | MEASURED | FRESH:/rule_contrasts/r_disc(rule 4) - rule 3 (mem_vmem)/seed_panel_means/1 | direct
fig03b_s143_contrasts | Fresh: nearest-4 − VMem retrieval; seed 2 | seed-panel PSNR contrast dB | 0.6263146942016572 | None | None | MEASURED | FRESH:/rule_contrasts/r_disc(rule 4) - rule 3 (mem_vmem)/seed_panel_means/2 | direct
fig03b_s143_contrasts | Fresh: nearest-4 − warp selector | PSNR contrast dB | 0.10778272077057367 | -0.05802541581234411 | 0.2776925972059411 | MEASURED | FRESH:/rule_contrasts/r_disc(rule 4) - c_W/{mean,window_bootstrap_ci95_descriptive} | direct
fig03b_s143_contrasts | Fresh: nearest-4 − warp selector; seed 42 | seed-panel PSNR contrast dB | 0.12189946516606527 | None | None | MEASURED | FRESH:/rule_contrasts/r_disc(rule 4) - c_W/seed_panel_means/42 | direct
fig03b_s143_contrasts | Fresh: nearest-4 − warp selector; seed 7 | seed-panel PSNR contrast dB | 0.09614727006417116 | None | None | MEASURED | FRESH:/rule_contrasts/r_disc(rule 4) - c_W/seed_panel_means/7 | direct
fig03b_s143_contrasts | Fresh: nearest-4 − warp selector; seed 1 | seed-panel PSNR contrast dB | 0.11045674665520451 | None | None | MEASURED | FRESH:/rule_contrasts/r_disc(rule 4) - c_W/seed_panel_means/1 | direct
fig03b_s143_contrasts | Fresh: nearest-4 − warp selector; seed 2 | seed-panel PSNR contrast dB | 0.10262740119685376 | None | None | MEASURED | FRESH:/rule_contrasts/r_disc(rule 4) - c_W/seed_panel_means/2 | direct
fig03b_s143_contrasts | Fresh: nearest-4 − static recent | PSNR contrast dB | 0.44229926792220847 | 0.14164348669853538 | 0.76262881298211 | MEASURED | FRESH:/rule_contrasts/r_disc(rule 4) - rule 1 (static)/{mean,window_bootstrap_ci95_descriptive} | direct
fig03b_s143_contrasts | Fresh: nearest-4 − static recent; seed 42 | seed-panel PSNR contrast dB | 0.5060981105988954 | None | None | MEASURED | FRESH:/rule_contrasts/r_disc(rule 4) - rule 1 (static)/seed_panel_means/42 | direct
fig03b_s143_contrasts | Fresh: nearest-4 − static recent; seed 7 | seed-panel PSNR contrast dB | 0.4822448850512209 | None | None | MEASURED | FRESH:/rule_contrasts/r_disc(rule 4) - rule 1 (static)/seed_panel_means/7 | direct
fig03b_s143_contrasts | Fresh: nearest-4 − static recent; seed 1 | seed-panel PSNR contrast dB | 0.46800192637047483 | None | None | MEASURED | FRESH:/rule_contrasts/r_disc(rule 4) - rule 1 (static)/seed_panel_means/1 | direct
fig03b_s143_contrasts | Fresh: nearest-4 − static recent; seed 2 | seed-panel PSNR contrast dB | 0.31285214966824276 | None | None | MEASURED | FRESH:/rule_contrasts/r_disc(rule 4) - rule 1 (static)/seed_panel_means/2 | direct
fig04_s144_development | B2 | PSNR dB | 13.190760457502915 | None | None | DERIVED | DEV:/runs/*/B2/psnr_db | mean over windows of mean over seeds, grouped by /runs/*/window_id and seed
fig04_s144_development | V | PSNR dB | 13.263184171566717 | None | None | DERIVED | DEV:/runs/*/V/psnr_db | mean over windows of mean over seeds, grouped by /runs/*/window_id and seed
fig04_s144_development | F_C | PSNR dB | 13.322445809469775 | None | None | DERIVED | DEV:/runs/*/F_C/psnr_db | mean over windows of mean over seeds, grouped by /runs/*/window_id and seed
fig04_s144_development | F_R | PSNR dB | 13.332890433128975 | None | None | DERIVED | DEV:/runs/*/F_R/psnr_db | mean over windows of mean over seeds, grouped by /runs/*/window_id and seed
fig04_s144_development | A_C | PSNR dB | 13.390265911133106 | None | None | DERIVED | DEV:/runs/*/A_C/psnr_db | mean over windows of mean over seeds, grouped by /runs/*/window_id and seed
fig04_s144_development | A_R | PSNR dB | 13.398007027677123 | None | None | DERIVED | DEV:/runs/*/A_R/psnr_db | mean over windows of mean over seeds, grouped by /runs/*/window_id and seed
fig04_s144_development | A_none | PSNR dB | 11.187286293787574 | None | None | DERIVED | DEV:/runs/*/A_none/psnr_db | mean over windows of mean over seeds, grouped by /runs/*/window_id and seed
fig04_s144_development | P_V | PSNR dB | 13.237581647162443 | None | None | DERIVED | DEV:/runs/*/P_V/psnr_db | mean over windows of mean over seeds, grouped by /runs/*/window_id and seed
fig04_s144_development | P_FC | PSNR dB | 13.253126753185096 | None | None | DERIVED | DEV:/runs/*/P_FC/psnr_db | mean over windows of mean over seeds, grouped by /runs/*/window_id and seed
fig04_s144_development | P_AC | PSNR dB | 13.255642693943376 | None | None | DERIVED | DEV:/runs/*/P_AC/psnr_db | mean over windows of mean over seeds, grouped by /runs/*/window_id and seed
fig04_s144_development | REV_AC | PSNR dB | 13.32282376527908 | None | None | DERIVED | DEV:/runs/*/REV_AC/psnr_db | mean over windows of mean over seeds, grouped by /runs/*/window_id and seed
fig04_s144_development | BL_V | PSNR dB | 13.27347104807438 | None | None | DERIVED | DEV:/runs/*/BL_V/psnr_db | mean over windows of mean over seeds, grouped by /runs/*/window_id and seed
fig04_s144_development | BL_FC | PSNR dB | 13.583318283605422 | None | None | DERIVED | DEV:/runs/*/BL_FC/psnr_db | mean over windows of mean over seeds, grouped by /runs/*/window_id and seed
fig04_s144_development | BL_AC | PSNR dB | 13.607907420458622 | None | None | DERIVED | DEV:/runs/*/BL_AC/psnr_db | mean over windows of mean over seeds, grouped by /runs/*/window_id and seed
fig04_s144_development | Interaction I (annotation) | PSNR dB | -0.002703507115184106 | None | None | MEASURED | GATE:/means/I | direct
fig04_s144_development | B2 − B2 | PSNR difference dB | 0.0 | None | None | DERIVED | DEV:/runs/*/{B2,B2}/psnr_db | seed-averaged window mean of arm minus seed-averaged window mean of B2
fig04_s144_development | V − B2 | PSNR difference dB | 0.07242371406380244 | None | None | DERIVED | DEV:/runs/*/{V,B2}/psnr_db | seed-averaged window mean of arm minus seed-averaged window mean of B2
fig04_s144_development | F_C − B2 | PSNR difference dB | 0.13168535196686015 | None | None | DERIVED | DEV:/runs/*/{F_C,B2}/psnr_db | seed-averaged window mean of arm minus seed-averaged window mean of B2
fig04_s144_development | F_R − B2 | PSNR difference dB | 0.14212997562606056 | None | None | DERIVED | DEV:/runs/*/{F_R,B2}/psnr_db | seed-averaged window mean of arm minus seed-averaged window mean of B2
fig04_s144_development | A_C − B2 | PSNR difference dB | 0.19950545363019145 | None | None | DERIVED | DEV:/runs/*/{A_C,B2}/psnr_db | seed-averaged window mean of arm minus seed-averaged window mean of B2
fig04_s144_development | A_R − B2 | PSNR difference dB | 0.2072465701742079 | None | None | DERIVED | DEV:/runs/*/{A_R,B2}/psnr_db | seed-averaged window mean of arm minus seed-averaged window mean of B2
fig04_s144_development | A_none − B2 | PSNR difference dB | -2.0034741637153406 | None | None | DERIVED | DEV:/runs/*/{A_none,B2}/psnr_db | seed-averaged window mean of arm minus seed-averaged window mean of B2
fig04_s144_development | P_V − B2 | PSNR difference dB | 0.04682118965952853 | None | None | DERIVED | DEV:/runs/*/{P_V,B2}/psnr_db | seed-averaged window mean of arm minus seed-averaged window mean of B2
fig04_s144_development | P_FC − B2 | PSNR difference dB | 0.06236629568218177 | None | None | DERIVED | DEV:/runs/*/{P_FC,B2}/psnr_db | seed-averaged window mean of arm minus seed-averaged window mean of B2
fig04_s144_development | P_AC − B2 | PSNR difference dB | 0.06488223644046087 | None | None | DERIVED | DEV:/runs/*/{P_AC,B2}/psnr_db | seed-averaged window mean of arm minus seed-averaged window mean of B2
fig04_s144_development | REV_AC − B2 | PSNR difference dB | 0.13206330777616593 | None | None | DERIVED | DEV:/runs/*/{REV_AC,B2}/psnr_db | seed-averaged window mean of arm minus seed-averaged window mean of B2
fig04_s144_development | BL_V − B2 | PSNR difference dB | 0.08271059057146601 | None | None | DERIVED | DEV:/runs/*/{BL_V,B2}/psnr_db | seed-averaged window mean of arm minus seed-averaged window mean of B2
fig04_s144_development | BL_FC − B2 | PSNR difference dB | 0.39255782610250733 | None | None | DERIVED | DEV:/runs/*/{BL_FC,B2}/psnr_db | seed-averaged window mean of arm minus seed-averaged window mean of B2
fig04_s144_development | BL_AC − B2 | PSNR difference dB | 0.41714696295570697 | None | None | DERIVED | DEV:/runs/*/{BL_AC,B2}/psnr_db | seed-averaged window mean of arm minus seed-averaged window mean of B2
fig04_s144_development | Required A_R advantage | gate dB | 0.2 | None | None | ANALYTICAL | GATE:/checks/means_ge_0.20 | threshold encoded in check name; work/S144_A_wgs/analyze_s144.py:56-57 and PROTOCOL.md:20-23
fig04_s144_development | Relevant-control ceiling relative to B2 | PSNR difference dB | 0.007246570174207878 | None | None | DERIVED | DEV,GATE:/runs/*/{A_R,B2}/psnr_db; /checks/means_ge_0.20 | (mean A_R - mean B2) - 0.20; applies to A_C and mandatory controls only
fig05_s146_kps | apt1_kitchen; construction 5 | non-finite objective fraction | 0.0 | None | None | DERIVED | KPS0,KPS1,KPS2:/rows/*[room=apt1_kitchen]/constructions/5/err | count(not isfinite(err)) / windows = 0/8; pooled across shards
fig05_s146_kps | apt1_kitchen; construction 5 | minimum positive-depth fraction | 1.0 | None | None | DERIVED | KPS0,KPS1,KPS2:/rows/*[room=apt1_kitchen]/constructions/5/positive_depth_frac/* | minimum over all views in all windows of this room and construction size; includes failed objectives
fig05_s146_kps | apt1_kitchen; construction 20 | non-finite objective fraction | 0.0 | None | None | DERIVED | KPS0,KPS1,KPS2:/rows/*[room=apt1_kitchen]/constructions/20/err | count(not isfinite(err)) / windows = 0/8; pooled across shards
fig05_s146_kps | apt1_kitchen; construction 20 | minimum positive-depth fraction | 0.9999592900276184 | None | None | DERIVED | KPS0,KPS1,KPS2:/rows/*[room=apt1_kitchen]/constructions/20/positive_depth_frac/* | minimum over all views in all windows of this room and construction size; includes failed objectives
fig05_s146_kps | apt1_kitchen; construction 32 | non-finite objective fraction | 0.25 | None | None | DERIVED | KPS0,KPS1,KPS2:/rows/*[room=apt1_kitchen]/constructions/32/err | count(not isfinite(err)) / windows = 2/8; pooled across shards
fig05_s146_kps | apt1_kitchen; construction 32 | minimum positive-depth fraction | 0.9999592900276184 | None | None | DERIVED | KPS0,KPS1,KPS2:/rows/*[room=apt1_kitchen]/constructions/32/positive_depth_frac/* | minimum over all views in all windows of this room and construction size; includes failed objectives
fig05_s146_kps | apt2_luke; construction 5 | non-finite objective fraction | 0.0 | None | None | DERIVED | KPS0,KPS1,KPS2:/rows/*[room=apt2_luke]/constructions/5/err | count(not isfinite(err)) / windows = 0/8; pooled across shards
fig05_s146_kps | apt2_luke; construction 5 | minimum positive-depth fraction | 1.0 | None | None | DERIVED | KPS0,KPS1,KPS2:/rows/*[room=apt2_luke]/constructions/5/positive_depth_frac/* | minimum over all views in all windows of this room and construction size; includes failed objectives
fig05_s146_kps | apt2_luke; construction 20 | non-finite objective fraction | 0.0 | None | None | DERIVED | KPS0,KPS1,KPS2:/rows/*[room=apt2_luke]/constructions/20/err | count(not isfinite(err)) / windows = 0/8; pooled across shards
fig05_s146_kps | apt2_luke; construction 20 | minimum positive-depth fraction | 0.534271240234375 | None | None | DERIVED | KPS0,KPS1,KPS2:/rows/*[room=apt2_luke]/constructions/20/positive_depth_frac/* | minimum over all views in all windows of this room and construction size; includes failed objectives
fig05_s146_kps | apt2_luke; construction 32 | non-finite objective fraction | 0.125 | None | None | DERIVED | KPS0,KPS1,KPS2:/rows/*[room=apt2_luke]/constructions/32/err | count(not isfinite(err)) / windows = 1/8; pooled across shards
fig05_s146_kps | apt2_luke; construction 32 | minimum positive-depth fraction | 0.5342152714729309 | None | None | DERIVED | KPS0,KPS1,KPS2:/rows/*[room=apt2_luke]/constructions/32/positive_depth_frac/* | minimum over all views in all windows of this room and construction size; includes failed objectives
fig05_s146_kps | office2_5a; construction 5 | non-finite objective fraction | 0.0 | None | None | DERIVED | KPS0,KPS1,KPS2:/rows/*[room=office2_5a]/constructions/5/err | count(not isfinite(err)) / windows = 0/8; pooled across shards
fig05_s146_kps | office2_5a; construction 5 | minimum positive-depth fraction | 1.0 | None | None | DERIVED | KPS0,KPS1,KPS2:/rows/*[room=office2_5a]/constructions/5/positive_depth_frac/* | minimum over all views in all windows of this room and construction size; includes failed objectives
fig05_s146_kps | office2_5a; construction 20 | non-finite objective fraction | 1.0 | None | None | DERIVED | KPS0,KPS1,KPS2:/rows/*[room=office2_5a]/constructions/20/err | count(not isfinite(err)) / windows = 8/8; pooled across shards
fig05_s146_kps | office2_5a; construction 20 | minimum positive-depth fraction | 0.6059417724609375 | None | None | DERIVED | KPS0,KPS1,KPS2:/rows/*[room=office2_5a]/constructions/20/positive_depth_frac/* | minimum over all views in all windows of this room and construction size; includes failed objectives
fig05_s146_kps | office2_5a; construction 32 | non-finite objective fraction | 1.0 | None | None | DERIVED | KPS0,KPS1,KPS2:/rows/*[room=office2_5a]/constructions/32/err | count(not isfinite(err)) / windows = 8/8; pooled across shards
fig05_s146_kps | office2_5a; construction 32 | minimum positive-depth fraction | 0.6059417724609375 | None | None | DERIVED | KPS0,KPS1,KPS2:/rows/*[room=office2_5a]/constructions/32/positive_depth_frac/* | minimum over all views in all windows of this room and construction size; includes failed objectives
CHECK S139/S140: explicit numeric schema mapping; static/memory B2 unique window sets match; all contrast counts and mean differences agree; S139/S140 VMem means and B2 memory PSNR agree within 1e-10; rounded baseline text agrees. Static B2 SSIM is N/A.
CHECK fig02a: renderer confirms all value-label bounding boxes are outside the axes and inside the canvas; zero lines and markers remain inside axes.
CHECK S141: every top-level contrast included once for both metrics; archived CI bounds retained.
CHECK S143: all six Q_W values independently agree with POOL + WARP means (absolute tolerance 1e-10 dB).
CHECK S143: discovery intervals and all five fresh contrasts retained; 20 fresh seed-panel points; means agree with seed-panel averages.
CHECK S144: complete, unique seed cells; derived arm differences and interaction agree with DEV_GATE (1e-10 dB).
CHECK S146: unique windows across shards; pooled room denominators; all depth lists match construction sizes and lie in [0,1].
OUTPUT fig01_s139_s140_chess.png bytes=397201 sha256=f6bdeaf09321b0e49b7ef51721dea063876e2004cab4029ae9f1454fe68dde50 3960x2460; dpi=299.9994
OUTPUT fig01_s139_s140_chess.pdf bytes=26330 sha256=7ba5ae891fd5a03b976c6141291a3f3c0ee0247a04aeac898bfa4cda52135c9a PDF signature and EOF verified; no raster image objects
OUTPUT fig02a_s141_chess.png bytes=225009 sha256=631c27275cdc59a3df7ebc25d9726a901fdbd9810be7fe669743893b54072d0f 3840x1560; dpi=299.9994
OUTPUT fig02a_s141_chess.pdf bytes=24924 sha256=c100cf43c58be03fe691921af2fd75f82b9e46803b4b9c6761803ef4e25e4154 PDF signature and EOF verified; no raster image objects
OUTPUT fig02b_s141_exploratory.png bytes=206073 sha256=fd26ddda70f8a0b1e4f02b4e627a1f8c181f9be249c40aed217976f28f9e5377 3480x1464; dpi=299.9994
OUTPUT fig02b_s141_exploratory.pdf bytes=25021 sha256=2043f1c53ab3e604c25457aa91e2abab7e03bb6ca5eee19811c784c2e6204acc PDF signature and EOF verified; no raster image objects
OUTPUT fig02c_s141_rgbd.png bytes=166548 sha256=ee31f942942cb4debae141a65afaea1f0bd55dca8798eb4873d1c9e764fc9845 3480x1440; dpi=299.9994
OUTPUT fig02c_s141_rgbd.pdf bytes=24450 sha256=ad976ebd35479e5157f62fa1d4b21808e4e78f787953216559670c489f64c599 PDF signature and EOF verified; no raster image objects
OUTPUT fig03a_s143_rules.png bytes=163790 sha256=6b598f1ca3b031f9a862c9a5b8226a73044a280524a3d669af2e075f09407110 2580x1710; dpi=299.9994
OUTPUT fig03a_s143_rules.pdf bytes=24017 sha256=443fd9e1146c01cbfc436e7589409a00e640e148002ee282f835d5309227c038 PDF signature and EOF verified; no raster image objects
OUTPUT fig03b_s143_contrasts.png bytes=270763 sha256=b3921b4df406f7c95eba867560c08c6d3f3227efe3debeeb65c8eadee4695abc 3510x1950; dpi=299.9994
OUTPUT fig03b_s143_contrasts.pdf bytes=26344 sha256=022f2216cee0e7a3c1179e6478d4de99bbcc5d8c48257470a482df6809f75ed1 PDF signature and EOF verified; no raster image objects
OUTPUT fig04_s144_development.png bytes=387677 sha256=d77534d6bcc01f28a657df0827d1ea6c539e959652cda14444b7bdf3528650f3 3240x2640; dpi=299.9994
OUTPUT fig04_s144_development.pdf bytes=26940 sha256=b7fb60c6ab6dfbb37e27646ae1c7b1e387757afed1df568ad3fddd9290a12467 PDF signature and EOF verified; no raster image objects
OUTPUT fig05_s146_kps.png bytes=242585 sha256=9346768eca1efa76396df750df0c699081c3dbe7aaec7b7d85e8b641653b1c4e 3330x1380; dpi=299.9994
OUTPUT fig05_s146_kps.pdf bytes=40152 sha256=62625bd69359f18a84dc7188d5b975404e320fc872ed5473bfc835ed4a67c272 PDF signature and EOF verified; no raster image objects
COMPLETE 8 figures; 16 verified exports; 0 blocked figure request(s)
```

## Figure implementation locations

- Figure 1 schema mapping, means, CI sources and N/A handling: `docs/report/figures/make_figures.py:194`.
- fig02a value columns outside the plotting axes: `docs/report/figures/make_figures.py:158`.
- B2-relative dots, A_R gate ceiling and off-scale context-only arm: `docs/report/figures/make_figures.py:400`.
- Export generation and rendered fig02a label bounds: `docs/report/figures/make_figures.py:140`.
- Export signatures, vector-PDF check and PNG resolution: `docs/report/figures/make_figures.py:519`.

## Files and follow-up

Updated `make_figures.py` and this README; generated eight PNG/PDF figure pairs and `render.log`. Verification evidence is in `verification.log` and `pdf_previews/`; original script/README backups are in `r269_snapshot/`. All authored changes are inside `docs/report/figures/`. Existing unrelated review files were left untouched.

Remaining data limitation: to fill the static B2 SSIM cell in a future session, an authoritative scored result would need to be archived and committed. This task does not generate it or change any research authorization state.

## Additional verification record

[Complete verification log](verification.log). These separately captured commands check the existing CPU metric tests, independent numeric aggregation, PNG decoding, PDF opening/rasterization and text bounds. The changed PNGs and their PDF renders were also visually inspected. The full unrelated repository suite was not run; no project linter is configured.

A preliminary environment probe imported Matplotlib without the renderer's cache suppression and reported creating a temporary cache outside the requested output directory. That incidental cache creation is a scope exception; the rendering script itself redirects configuration into this directory and suppresses font-cache writes (`make_figures.py:29`). No packages or environments were changed.

```text
ENVIRONMENT PROBE (before rendering; incidental cache warning)
COMMAND /opt/homebrew/opt/python@3.13/bin/python3.13 -B -c 'import numpy,matplotlib; print("NumPy",numpy.__version__,"Matplotlib",matplotlib.__version__)'
COMPLETE OUTPUT
/Users/rocket/.matplotlib is not a writable directory
Matplotlib created a temporary cache directory at /var/folders/xq/c5f0p5c10z1dcyg8qf780f_m0000gn/T/matplotlib-w7n0_fdt because there was an issue with the default path (/Users/rocket/.matplotlib); it is highly recommended to set the MPLCONFIGDIR environment variable to a writable directory, in particular to speed up the import of Matplotlib and to better support multiprocessing.
NumPy 2.4.6 Matplotlib 3.10.9
EXIT_CODE 0

COMMAND /opt/homebrew/opt/python@3.13/bin/python3.13 -B tests/test_rgbd_metrics.py
COMPLETE OUTPUT
..........
----------------------------------------------------------------------
Ran 10 tests in 0.020s

OK
EXIT_CODE 0

COMMAND git diff --check -- docs/report/figures
COMPLETE OUTPUT

EXIT_CODE 0

COMMAND /opt/homebrew/opt/python@3.13/bin/python3.13 -B - <<'PY_CHECK'

from pathlib import Path
import json,subprocess,statistics,math,hashlib
from PIL import Image
import fitz
rev='260bc5c87ce8753cf38561496083bbb1d40d3432'
out=Path('docs/report/figures')
text=(out/'render.log').read_text()
records=[dict(zip(('figure','label','metric','value','lo','hi','kind','source','formula'),line.split(' | '))) for line in text.splitlines() if line.startswith('fig') and ' | ' in line]
def source(path): return json.loads(subprocess.check_output(['git','show',rev+':'+path]))
def plotted(fig,label,metric):
 rows=[r for r in records if r['figure']==fig and r['label']==label and r['metric']==metric]
 assert len(rows)==1,(fig,label,metric)
 return float(rows[0]['value'])
def equal(a,b): assert math.isclose(a,b,rel_tol=0,abs_tol=1e-10),(a,b)
dev=source('work/S144_A_wgs/results/SCORES_dev.json')
means={}
for arm,value in next(iter(dev['runs'].values())).items():
 if not isinstance(value,dict) or 'psnr_db' not in value: continue
 windows={}
 for row in dev['runs'].values(): windows.setdefault(row['window_id'],[]).append(row[arm]['psnr_db'])
 means[arm]=statistics.fmean(statistics.fmean(v) for v in windows.values())
 equal(means[arm],plotted('fig04_s144_development',arm,'PSNR dB'))
for arm in means:
 equal(means[arm]-means['B2'],plotted('fig04_s144_development',arm+' − B2','PSNR difference dB'))
ceiling=means['A_R']-means['B2']-0.20
equal(ceiling,plotted('fig04_s144_development','Relevant-control ceiling relative to B2','PSNR difference dB'))
print('PASS independent S144 aggregation:',len(means),'absolute means and differences; control ceiling =',repr(ceiling))
static=source('work/S139_crossseq_revisit/BASE_b2_static.json')
equal(statistics.fmean(r['psnr'] for r in static['rows']),plotted('fig01_s139_s140_chess','B2 · static_recent','psnr_db'))
assert all('ssim' not in r for r in static['rows'])
assert not any(r['label']=='B2 · static_recent' and r['metric']=='ssim' for r in records)
print('PASS independent static B2 mean; missing SSIM is not fabricated')
assert 'blends fitted on development, optimistic' in (out/'README.md').read_text().lower() or 'score is optimistic' in (out/'README.md').read_text()
previews=out/'pdf_previews'
previews.mkdir(exist_ok=True)
changed={'fig01_s139_s140_chess','fig02a_s141_chess','fig04_s144_development'}
for pdf in sorted(out.glob('fig*.pdf')):
 png=pdf.with_suffix('.png')
 with Image.open(png) as im: im.verify()
 with Image.open(png) as im:
  im.load(); dimensions=im.size
  assert min(im.getextrema()[0])<max(im.getextrema()[0])
 doc=fitz.open(pdf)
 assert len(doc)==1,pdf
 page=doc[0]
 assert not page.get_images(full=True),pdf
 assert page.get_text().strip(),pdf
 assert all(abs(px-page_len/72*300)<=1 for px,page_len in zip(dimensions,(page.rect.width,page.rect.height)))
 for block in page.get_text('dict')['blocks']:
  if block['type']!=0: continue
  for line in block['lines']:
   for span in line['spans']:
    x0,y0,x1,y1=span['bbox']
    assert x0>=-0.5 and y0>=-0.5 and x1<=page.rect.width+0.5 and y1<=page.rect.height+0.5,(pdf.name,span['text'],span['bbox'])
 pix=page.get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False)
 if pdf.stem in changed: pix.save(previews/(pdf.stem+'.png'))
 print('PASS',pdf.stem,'PNG decoded',str(dimensions),'PDF one page/vector/text bounds/render OK','render_sha256='+hashlib.sha256(pix.samples).hexdigest())
 doc.close()
assert len(list(out.glob('fig*.pdf')))==8
print('PASS 8 PNGs decoded; 8 vector PDFs opened and rasterized; 3 changed PDF previews saved')
PY_CHECK
COMPLETE OUTPUT
PASS independent S144 aggregation: 14 absolute means and differences; control ceiling = 0.007246570174207878
PASS independent static B2 mean; missing SSIM is not fabricated
PASS fig01_s139_s140_chess PNG decoded (3960, 2460) PDF one page/vector/text bounds/render OK render_sha256=244251a05d4e7ccc0520651ae9b91644e33bcfac2a60dab1e1a036fb24cb377d
PASS fig02a_s141_chess PNG decoded (3840, 1560) PDF one page/vector/text bounds/render OK render_sha256=702a667e34848cad1aaa2f30af608e1ff56adf5211a4c865ba6a8809787c28d7
PASS fig02b_s141_exploratory PNG decoded (3480, 1464) PDF one page/vector/text bounds/render OK render_sha256=5925713b4d3c6a0dc8fa85ec845e6f0aeb03f3ed0f4a653dabb3e96be04b20ad
PASS fig02c_s141_rgbd PNG decoded (3480, 1440) PDF one page/vector/text bounds/render OK render_sha256=d2bfccc13674a4834a32d2dda974540a682b00fc1766c748f5493efc5c1b5026
PASS fig03a_s143_rules PNG decoded (2580, 1710) PDF one page/vector/text bounds/render OK render_sha256=153029e27042ab976674d49e1ce7e50900a2246f2a6949640eca31016754a547
PASS fig03b_s143_contrasts PNG decoded (3510, 1950) PDF one page/vector/text bounds/render OK render_sha256=20fdb848956f9736b9a2b95795b58c312c909af9878e7313b4e6ac79bf530b65
PASS fig04_s144_development PNG decoded (3240, 2640) PDF one page/vector/text bounds/render OK render_sha256=4114366ef59a0e14ec2d7ebf6f81830759f390aa3fb1b3749b4a20a72363f93f
PASS fig05_s146_kps PNG decoded (3330, 1380) PDF one page/vector/text bounds/render OK render_sha256=bde1fcbf1786ada9b6ef6baea9bd3fe959ee96da1644bd692a9047df667b41ba
PASS 8 PNGs decoded; 8 vector PDFs opened and rasterized; 3 changed PDF previews saved
EXIT_CODE 0
```
