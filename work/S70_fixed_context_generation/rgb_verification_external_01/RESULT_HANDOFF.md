# Actual S70 independent integer score verification

Recorded UTC: 2026-09-09T04:21:12.356009+00:00. **PASS_INDEPENDENT_INTEGER_RGB_SCORE**. Exactly one unchanged reviewed verifier execution, external04:19:17.702321–04:19:17.896067Z, return0,0.193763917 seconds under120-second external timeout. Worker measured0.136156917 seconds. No retry/source edit/model execution/image viewing.

| Target | A0 MSE | A1 MSE | B MSE | B−A0 |
|---:|---:|---:|---:|---:|
| 20 | 0.084402762864581607 | 0.084402762864581607 | 0.085639750822802993 | +0.0012369879582213947 |
| 21 | 0.14832556277322112 | 0.14832556277322112 | 0.1392612263580415 | -0.0090643364151796243 |
| 22 | 0.16481927034075905 | 0.16481927034075905 | 0.15386415836904591 | -0.01095511197171316 |
| 23 | 0.12711907509778805 | 0.12711907509778805 | 0.1223895150020944 | -0.0047295600956936473 |
| All4 mean | 0.13116666776908745 | 0.13116666776908745 | 0.12528866263799621 | -0.0058780051310912589 |

All43 fixed MSE, PSNR and signed-difference comparisons match the sealed main score within the frozen absolute+relative1e−12 rule; maximum observed absolute discrepancy1.7763568394002505e−15. The aggregate signed integer numerator is−1,521,726,258 over denominator258,884,812,800. Thus B has lower mean emitted-RGB error in this fixed case and the predicted higher-support-A0 lower-error event isfalse. Target20 goes in the opposite direction to targets21–23; no target was dropped.

A0/A1 full8 latent, four raw FP32 RGB and four emitted uint8 RGB C-order bytes all match exactly, and all replay/sign/interpretation fields agree with the main scorer. One repeat does not estimate a replay variance distribution. This is a known sequence with four correlated targets, fixed selected-context bundles and natural normalization differences; no new method or general benefit is established.

Reference preprocessing support: exactly36 fixed pixels/108 RGB channels across all4 native targets, all within the predetermined≤1-level allowance, observed maximum1. This checks the independent area-bin/crop support calculation against saved references at those locations only. It does not independently reproduce the full reference preprocessor, the neural model, or B's full raw-output quantizer. The integer score itself recomputes every emitted/reference pixel.

Actual verifier input reads total51,225,527 B including source/metadata. Eight NPY files contain49,102,848 numeric-body B plus1,024 header B; four original PNG files add2,062,492 B. Thus this stage read real generated/reference RGB bodies and decoded reference PNGs, while viewing no image. Full per-file identities/kinds/bytes and comparisons remain in the result receipt.

- Result: `../rgb_verification_01/receipt.json`, SHA256 `9e92ed0be2f5e2e268d9241ca163bc356dd770d2abb06c9ad8fba2c62bd1b862` (0444).
- External execution: `receipt.json`, SHA256 `0a15179181245654ae0a2956e20d23e5bbf65c7fe6cb536ce166ca2237749fc9` (0444).
- Actual verification binding: SHA256 `d3c3777dd3b861def698d6dcee5933cb336f12e9e7216d04433a9354283043b2`.

Root owns acceptance, full16-image export/view and scientific reporting. No export was started by this verifier.
