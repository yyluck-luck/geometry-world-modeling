# Seed robustness of the technical report's contrasts (zero GPU, from sealed S113 rows)

Source: `docs/report/bundle/S113_SCORES.json` rows, 14 windows x seeds 42 and 7. Prompted by C8 Experiment 1, which
showed the same arm differing by 1.5 dB between seeds.

| contrast | mean seed 42 | mean seed 7 | seed-folded | per-window sign agrees across seeds | median abs(delta_s42 - delta_s7) |
|---|---|---|---|---|---|
| nms_off - static (report +0.242) | +0.154 | +0.330 | +0.242 | 11/14 | 0.934 dB |
| clean nms_on - nms_off (report -0.726) | -0.779 | -0.673 | -0.726 | 6/14 | 0.641 dB |
| clean - leaked (Delta_leak, +0.245) | +0.120 | +0.369 | +0.245 | 9/14 | 0.205 dB |

Same arm across seeds (static): median abs(PSNR_s42 - PSNR_s7) = 0.919 dB, max 3.474 dB.

Reading: all three panel-level means keep their sign under either seed alone, so the panel-mean statements survive
this check. Per-window contrasts do not: seed-to-seed differences (0.2-0.9 dB median) are as large as or larger than
the effects, and for the -0.726 contrast only 6/14 windows keep their sign across seeds. Any per-window claim on this
harness is unsupported, and with two seeds the panel means are themselves only loosely pinned.
