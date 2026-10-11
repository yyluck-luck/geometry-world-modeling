# R269 report figures

**PARTIAL: 7 figures / 14 verified PNG and PDF exports.** Figure 1 is blocked by missing committed S139/S140 inputs; details below.

Source snapshot: `52bdb866eb5987cb97f4d68c1f991d4e1e4ab05c`. CPU only; all numeric inputs are Git blobs from this snapshot. Local ignored/uncommitted JSONs, source images, target frames, weights and datasets are not read.

`new_method_validated=false`; `novelty_authorization=NONE`.

## Reproduce

From the repository root:

```bash
/opt/homebrew/opt/python@3.13/bin/python3.13 -B docs/report/figures/make_figures.py --revision 52bdb866eb5987cb97f4d68c1f991d4e1e4ab05c
```

The script prints every plotted value and interval with its JSON key, verifies source consistency, writes this README, and checks export signatures and PNG DPI. `--revision` freezes inputs even if another process advances HEAD. Missing sources are explicit and never replaced with different-seed results or transcribed report prose.

## Produced figures

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

### S144 development arm/control PSNR

[fig04_s144_development.png](fig04_s144_development.png) · [fig04_s144_development.pdf](fig04_s144_development.pdf)

S144 fails its archived development gate. Bars include every scored arm/control and start at zero. V denotes the warp's VAE round-trip; F/A are frozen/adapted backbones, C/R are terminal clamp/release, P replaces covered pixels, REV reverses that paste, and BL is a development-fitted global blend. These development scores do not establish held-out improvement.

Sources: `DEV`, `GATE`.

### S146 per-room KPS diagnostic

[fig05_s146_kps.png](fig05_s146_kps.png) · [fig05_s146_kps.pdf](fig05_s146_kps.pdf)

The KPS diagnostic records non-finite whole objectives and low positive-depth fractions in some room/construction cells. Non-finite means not math.isfinite(err), including Infinity. Each denominator is the number of windows in that room, after pooling shards. The depth statistic is the minimum over every stored view, including constructions with non-finite objectives; n_views is not used as the objective denominator.

Sources: `KPS0`, `KPS1`, `KPS2`.

## Missing sources / limitations

- Figure 1 (S139/S140) not plotted: requested result JSONs absent from this committed snapshot: work/S139_crossseq_revisit/results/S139_ANALYSIS.json; work/S139_crossseq_revisit/results/S139_BASELINE_CONTRASTS.json; work/S140_warp_guided/results/CONFIRM_ANALYSIS.json; work/S140_warp_guided/results/s139_ssim/S139_SSIM_ANALYSIS.json. These paths are ignored by Git in this checkout. Commit the authoritative files, then add/verify their schema before rendering this panel; no ignored result bytes were read.

The brief's POOL file is committed at `work/S143_context_ranking/POOL.json`, outside its `results/` directory. S141 is split across three figures and S143 across two to keep individual labels readable. No new statistical intervals are fitted: only archived intervals are shown; arm means and diagnostics without supplied intervals remain descriptive.

## Source files and content hashes

| Alias | Committed file | Git blob | SHA-256 |
|---|---|---|---|
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

## Definitions and code provenance

JSON paths below use JSON Pointer syntax; `*` and `[room=...]` explicitly denote the filters described in the derivation column. `MEASURED` means an archived experimental summary copied from JSON, not a new experiment. `DERIVED` means a deterministic aggregation of stored measurements. Decimal strings preserve the loaded Python floats; plot labels are rounded only for legibility.

- S141 window-mean contrasts and bootstrap: `work/S141_finetune/analyze_s141.py:22`, `:33`, `:63`, `:70`, `:96`; registration and scope: `work/S141_finetune/PROTOCOL.md:51`, `:72`.
- S144 seed averaging and gate: `work/S144_A_wgs/analyze_s144.py:14`, `:28`, `:49`; control definitions: `work/S144_A_wgs/PROTOCOL.md:9`.
- S143 rule names: `work/S143_context_ranking/PROTOCOL.md:14`. Rule mapping is checked against the committed POOL and WARP files. Fresh inference scope is stated by `FRESH:/note`. No discovery seed-panel points are fabricated.
- S146 uses the stored whole-objective `err` and `positive_depth_frac` fields. A non-finite objective is counted once per construction/window; it is not a per-view failure count.

## Design and validation

Experimental-results guidance from the figure-designer skill was applied: vector PDFs plus 300 dpi PNGs, DejaVu Sans at readable panel sizes, an Okabe–Ito qualitative palette and viridis diagnostic scales, direct labels/marker shapes in addition to colour, and no fitted trend or selective winning-arm display. Forest plots include zero; S144 bars start at zero; scatter and heatmap axes are explicit. Use panels near their intended full slide/report width; do not shrink multi-panel figures into a narrow column.

The complete final script stdout follows, including the exact-value table, consistency checks, export sizes and SHA-256 hashes. Repository tests are not invoked by the figure script; this is a deterministic visualization of archived results, not a new model experiment.

### Environment correction and repository check

The supplied project venv has NumPy but lacks Matplotlib. No packages or environments were changed. Rendering uses the existing Homebrew Python environment named by the command above. The initial attempt ended before rendering:

```bash
.venv-cut3r/bin/python -B docs/report/figures/make_figures.py --revision 52bdb866eb5987cb97f4d68c1f991d4e1e4ab05c
```

Complete output (initial script version):

```text
Traceback (most recent call last):
  File "/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/report/figures/make_figures.py", line 31, in <module>
    import matplotlib
ModuleNotFoundError: No module named 'matplotlib'
```

A scoped existing CPU metric test was run with bytecode writes disabled; it checks the repository's synthetic RGB-D metrics, not the figure code. No root linter configuration or existing plotting tests were found. The full unrelated repository suite was not run under this task's restricted-write boundary.

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-cut3r/bin/python -B tests/test_rgbd_metrics.py
```

Complete output:

```text
..........
----------------------------------------------------------------------
Ran 10 tests in 0.011s

OK
```

## Exact command and complete stdout

```text
DATA_REVISION 52bdb866eb5987cb97f4d68c1f991d4e1e4ab05c
COMMAND /opt/homebrew/opt/python@3.13/bin/python3.13 -B docs/report/figures/make_figures.py --revision 52bdb866eb5987cb97f4d68c1f991d4e1e4ab05c
SCRIPT_SHA256 cf2b409d69c426872a679a5180d5d9b8591c8e0b9c29f5aeb89ee6adf71d6772
ENV Python=3.13.0 NumPy=2.4.6 Matplotlib=3.10.9
new_method_validated=false; novelty_authorization=NONE
BLOCKED Figure 1 (S139/S140) not plotted: requested result JSONs absent from this committed snapshot: work/S139_crossseq_revisit/results/S139_ANALYSIS.json; work/S139_crossseq_revisit/results/S139_BASELINE_CONTRASTS.json; work/S140_warp_guided/results/CONFIRM_ANALYSIS.json; work/S140_warp_guided/results/s139_ssim/S139_SSIM_ANALYSIS.json. These paths are ignored by Git in this checkout. Commit the authoritative files, then add/verify their schema before rendering this panel; no ignored result bytes were read.
PLOTTED VALUES (round-trip Python float representations)
figure | label | metric | value | ci95_low | ci95_high | evidence | source:key | derivation
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
CHECK S141: every top-level contrast included once for both metrics; archived CI bounds retained.
CHECK S143: all six Q_W values independently agree with POOL + WARP means (absolute tolerance 1e-10 dB).
CHECK S143: discovery intervals and all five fresh contrasts retained; 20 fresh seed-panel points; means agree with seed-panel averages.
CHECK S144: complete, unique seed cells; derived arm differences and interaction agree with DEV_GATE (1e-10 dB).
CHECK S146: unique windows across shards; pooled room denominators; all depth lists match construction sizes and lie in [0,1].
OUTPUT fig02a_s141_chess.png bytes=215273 sha256=e350caecb2163eed185c21fad9f44ba4264de3cadcc9da77b73c64ba02ec6559 3480x1464; dpi=299.9994
OUTPUT fig02a_s141_chess.pdf bytes=25017 sha256=66efdce81c8c0a6825d8f4e126a7606e735409f43d23e750bad635cc8aa8669a PDF signature and EOF verified; no raster image objects
OUTPUT fig02b_s141_exploratory.png bytes=206073 sha256=fd26ddda70f8a0b1e4f02b4e627a1f8c181f9be249c40aed217976f28f9e5377 3480x1464; dpi=299.9994
OUTPUT fig02b_s141_exploratory.pdf bytes=25021 sha256=56feae70942536ffd3dfc0b2b2dd0c76a461393621fe5f5a3f44b0a50ac2b94e PDF signature and EOF verified; no raster image objects
OUTPUT fig02c_s141_rgbd.png bytes=166548 sha256=ee31f942942cb4debae141a65afaea1f0bd55dca8798eb4873d1c9e764fc9845 3480x1440; dpi=299.9994
OUTPUT fig02c_s141_rgbd.pdf bytes=24450 sha256=3ed07fb9620e81b442db1ecb30c976259030c0ab092273127067a42dc1433c58 PDF signature and EOF verified; no raster image objects
OUTPUT fig03a_s143_rules.png bytes=163790 sha256=6b598f1ca3b031f9a862c9a5b8226a73044a280524a3d669af2e075f09407110 2580x1710; dpi=299.9994
OUTPUT fig03a_s143_rules.pdf bytes=24017 sha256=cfb59f6a037e8055a1c08dde7eefc3fcc693d95d4f5848e02f69ad9997e7c7da PDF signature and EOF verified; no raster image objects
OUTPUT fig03b_s143_contrasts.png bytes=270763 sha256=b3921b4df406f7c95eba867560c08c6d3f3227efe3debeeb65c8eadee4695abc 3510x1950; dpi=299.9994
OUTPUT fig03b_s143_contrasts.pdf bytes=26344 sha256=c5d03822dbf550a676f3ff7513721d7ea62322b4bb51397c369242be01cb0481 PDF signature and EOF verified; no raster image objects
OUTPUT fig04_s144_development.png bytes=278047 sha256=555d6c66852dca4c1629d6802055ee6133c0efd06ab11fbf71ece654022ab956 2910x2340; dpi=299.9994
OUTPUT fig04_s144_development.pdf bytes=23863 sha256=c56eca4c1e3298a09a6f1d58060d4dafeffed179717e74aaf8d192f77724facb PDF signature and EOF verified; no raster image objects
OUTPUT fig05_s146_kps.png bytes=242585 sha256=9346768eca1efa76396df750df0c699081c3dbe7aaec7b7d85e8b641653b1c4e 3330x1380; dpi=299.9994
OUTPUT fig05_s146_kps.pdf bytes=40152 sha256=1cc7e2498b5ff899da99f0c935d756d1bc508e426d2d3f8d4bb0b8d2186de29b PDF signature and EOF verified; no raster image objects
PARTIAL 7 figures; 14 verified exports; 1 blocked figure request(s)
```
