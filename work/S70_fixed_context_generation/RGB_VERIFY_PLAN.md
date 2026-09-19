# S70 independent RGB score verification plan

Frozen source-only at 2026-09-09T02:58:25.614726+00:00. Author: `/root/c2_v9_recovery_author`. This author wrote the generator, but did not write the root scorer. This is a team-internal, different arithmetic implementation of the same fixed metric. Primary separately verifies generation, RNG and model state; this verifier does not reproduce a neural model or broaden the scientific conclusion.

After the generation has been independently accepted **and** root's single main score has been sealed, root creates `ROOT_RGB_VERIFY_BINDING.json` with:

- `status`: `ACCEPTED_S70_SCORED_OUTPUTS_FOR_INDEPENDENT_RGB_VERIFY`
- `source_files_sha256`: actual absolute paths and SHA for this `verify_rgb_score.py` and `RGB_VERIFY_PLAN.md` (optionally author delivery/source review).
- `root_scoring_binding_sha256`: actual SHA of existing `ROOT_SCORING_BINDING.json`.
- `score_receipt_sha256`: actual SHA of `scoring_01/receipt.json`.

No future digest is filled or asserted here. Invoke the un-resolved project `.venv-cut3r/bin/python -B work/S70_fixed_context_generation/verify_rgb_score.py <actual verification-binding SHA>`. Exact source and fixed-contract hashes are verified before scientific reads. Create-only `rgb_verification_01/receipt.json`; ≤120s externally, final boundary time check internally. Failed inputs/comparisons remain in the new receipt, and a failure directory is never reused. No automatic following stage. No weights, renderer, get_cond, Torch model, image viewing or new generation.

## Exact inputs and arithmetic

The contract SHA is `a776fd9cc1af9014de2e9226364f8990e9a2461c45b23aa6e03e5354370df8ac`; root scorer interface SHA is `4c698efddeca50a2c35812632516ca458ab0f1a8f9dec8f4aa4cdde0f1584ab5`. The root scorer is read as provenance and **never imported or executed** by this verifier. NumPy1.26.4/Pillow10.3.0 in the existing Python3.12 venv are sufficient; no Torch import.

Read three saved `targets_uint8.npy` arrays `[4,576,576,3]`, A0/A1 `all8_latents.npy` `[8,4,72,72]` and raw `targets_fp32.npy` `[4,3,576,576]`, plus the scored `transformed_targets_uint8.npy` `[4,576,576,3]`. These eight NPY files contain49,102,848 array-body bytes before NPY headers. Each actual file is SHA-bound, decoded with pickle disabled and checked for exact dtype/shape/finite values. Read the four original target PNGs with contract SHA and native640×480 RGB identity only after the above binding exists. Record every actual source/metadata/array/PNG file read and byte count, distinguishing raw generated RGB from latents and reference RGB. No source-only preparation reads any of these science bodies.

IDs are exactly20–23, each once in that order; arms exactlyA0/A1/B with histories A0=A1 `[19,18,13,12]`, B `[19,18,14,13]`. Every full frame has576×576×3 channel values; full aggregate has4×576×576×3. Convert emitted/reference uint8 to int64 **before subtraction**, sum squared integer differences in int64 (worst-case aggregate below2^63), then divide the integer sum once by `N*255^2`. Sum all four frame integer numerators for each arm's aggregate. Equal-size full frames make this identical mathematically to the root's mean of four FP64 per-frame means, while avoiding its division-before-subtraction implementation.

Recompute each frame/arm MSE and PSNR, whole-four MSE and PSNR-from-MSE, per-frame and aggregate signed `B-A0`, and the fixed A0/A1 and A0/B emitted-output MSE diagnostics. PSNR is `-10log10(MSE)` with peak1; exact zero is JSON string `Infinity`, never a dropped frame. Floating comparison is frozen as `abs(a-b) <= 1e-12 + 1e-12*abs(scored)`. Compare the aggregate signed numerator as an exact integer for positive/zero/negative interpretation; a nonpositive numerator cannot be labeled support for A0. No new ROI, mask, alignment, exposure normalization, target selection, threshold or test of significance.

Independently compare A0/A1 C-order **raw bytes** for full8 latent, four raw FP32 targets and four emitted uint8 targets. Shape/dtype must also agree. Match the root's three flags and combined flag. A failed replay is a valid descriptive outcome: reproduction of `all_passed=false` can pass this verifier, while context attribution remains false and support label is null. Do not retry, change the result or remove B. Known target exposure, GT cameras, ft-mse VAE, approximate K/no undistortion and full-bundle intervention limitations remain mandatory; `new_method_validated=false`.

## Predetermined reference mapping spot checks

For each of the four references, inspect these **nine fixed (y,x) target pixels**: `(0,0), (0,575), (575,0), (575,575), (288,288), (123,234), (421,197), (96,96), (479,479)`. All three RGB channels are checked:36 pixel locations/108 channels in total, not108 independent samples.

Independently derive native support from640×480→768×576 area resize then576² center crop with left96/top0. For target(y,x), set j=x+96. Adaptive-area source rows are `floor(y*480/576)` through `ceil((y+1)*480/576)` exclusive; columns `floor(j*640/768)` through `ceil((j+1)*640/768)` exclusive. Sum native integer RGB over that rectangular support and divide by its count; floor is the ideal exact-linear uint8 truncation. Compare each saved reference channel to this ideal with absolute tolerance≤1 level, fixed before results, because the actual source does FP32 normalization to[-1,1], FP32 pooling and normalization back before uint8 truncation. Record support bounds/count/sum, ideal integer value, actual saved value and level difference. No tolerance is adapted from results.

This checks finite mapping support and coarse quantization consistency only. It is not full pixelwise preprocessing equivalence, not an independently transformed full reference, not actual prediction-emission regeneration, and not geometric or perceptual validation. The main metric independently recomputes all pixels **against the saved transformed references**. Root's original-preprocessor source execution and full prediction quantizer check remain separate evidence. In particular, the generator's advisory Torch min-branch field has the already disclosed float32 -0.1 comparison boundary; its actual uint8 emission and raw arrays, not that advisory field, are authoritative.

Source basis for area bins is local Torch functional `interpolate` (area→adaptive_avg_pool2d), and `ATen/native/AdaptivePooling.h` start_index/end_index. These are only read to derive the formula; no Torch call or preprocessing is run by this verifier. Original util lines354–428 provide resize/crop dimensions; lines430–526 provide load/FP32 normalization. Source pins follow.

| Source | SHA256 |
|---|---|
| `work/S20_environment/isolated_vmem_source/utils/util.py` | `30a97451f7a895e99ab881e97249f564e6b97eca2b5ea4d8f83953c26c4cf65e` |
| `.venv-cut3r/lib/python3.12/site-packages/torch/nn/functional.py` | `0c02464c208daff72bcfcb3f0eed09a136e0766d926c08c4bfd0038eb977bc28` |
| `.venv-cut3r/lib/python3.12/site-packages/torch/include/ATen/native/AdaptivePooling.h` | `848380c20abb80dc0a2273704dfeb5dc17ad0973c1e264d8d25d99eec720c241` |

## Author validation

Compile-only with the existing venv; no actual score/array/reference/model reads, no scientific calculation and no synthetic or old test matrix. A distinct author may review the frozen source while generation runs. Actual verification waits for root's score and its concrete binding. Prior generator/root/reviewer files and the main ledger remain untouched.
