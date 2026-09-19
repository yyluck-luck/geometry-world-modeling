# S70 result interpretation: the fixed support-to-benefit prediction failed

Review: `/root/c2_v9_source_primary`, 2026-09-09 04:19:16 UTC to 2026-09-09T04:21:48.064846+00:00. Scope: existing score/contract JSON, S66 protocol/adapter and its exact S46 mathematical source, S66 saved score metadata and S64 input protocol. No new arrays, reference images, weights, model call or experiment. Root handles visual QA. This interprets the actual main score; it is not an additional scoring gate or a pixel recomputation. The main receipt itself retains `PENDING_INDEPENDENT_RECOMPUTE`; independent numerical acceptance is a separate existing task.

**The recorded signed result favors B and contradicts the prospective higher-support-A benefit direction in this one case.** A0 and A1 have identical mean MSE 0.13116666776908745; B has 0.12528866263799618. The frozen difference `L(B)−L(A0)` is −0.005878005131091268. B is closer on three targets; A is closer on target 20. All four remain in the primary mean.

| Target | MSE(B)−MSE(A0) | Lower recorded error |
|---|---:|---|
| 20 | +0.0012369879582214 | A0 |
| 21 | −0.009064336415179647 | B |
| 22 | −0.010955111971713144 | B |
| 23 | −0.004729560095693738 | B |

The metric compares authoritative emitted uint8 images, normalized by 255, against the fixed original area-resized/cropped and quantized TUM references over every pixel of all four frames. PSNR from mean MSE is 8.8217651437445 dB for A and 9.020882265040619 dB for B. This does not certify perceptual superiority, physical camera obedience or geometric accuracy. One repeat is exact reproducibility evidence, not a noise-variance estimate; the four nearby targets are correlated observations from one known sequence, not four independent trials. The contract's nonpositive-difference stop condition applies to this fixed motivation. Do not replace the seed, targets, metric or sign after seeing it.

## S66 is a different question, not a much better score on this benchmark

S66's 0.0006382446123931144 measures normalized uint8 discrepancy between **living_room input ID0 and generated return ID8**, on four fixed 192×192 regions (147,456 pixels / 442,368 RGB scalars). Its primary function is a predefined return-view discrepancy check, with strict event `MSE>0.01`. It is not four real TUM target-time references. S70 instead uses five encoded real TUM history sources across two fixed four-source bundles and four full 576×576 future-reference comparisons.

Although both formulas use normalized uint8 and float64 squared differences, their reference identities, scene, trajectory, conditioning, spatial support and aggregation differ. Ratios, percentage deterioration and a quality ranking between 0.000638… and 0.125–0.131 are therefore invalid. Even substituting S66's full-frame diagnostic 0.000914694351664958 leaves different inputs and comparison targets. The S66 threshold 0.01 must not be imported as an S70 severe-failure criterion. Its low discrepancy and event=false remain valid for its own frozen question; S70 does not overwrite the old C2 failure/cohort.

## What changed, and what remains unidentified

The actual verified A0/A1 replay and shared three-arm RNG support interpreting a difference from the **complete fixed ordered-context intervention** in this execution. A=[19,18,13,12] and B=[19,18,14,13] change membership and slot order, historical camera inputs, natural translation normalization, latent/embedding conditioning and their guidance descendants. Target physical cameras, model resources, seed/draw path and the evaluation target set are controlled. Descendants were recomputed, so the observed difference is not a test with those mechanisms held fixed.

This does not isolate the effect of source12 versus source14, camera scale alone, slot order, latent versus semantic content, or the geometry-selection algorithm. The source sets were fixed after historical selection; online retrieval was not compared. “More geometric support guarantees lower RGB error” loses its local motivation here, but “geometric support is generally harmful” and “scale caused the failure” do not follow. Likewise, this known TUM case does not establish missing dynamic state, high-order synergy, multiple futures or a new memory mechanism. Approximate K, GT/interpolated cameras, historical target exposure and the declared ft-mse VAE remain limitations.

## Concrete next diagnostic using existing evidence

Complete the already planned all-target visual QA against the saved transformed references, with A0/A1/B shown for every target. Check whether the major mismatch is recognizable camera/layout displacement, scene-content change or smoothing/color differences, and whether the B-over-A direction is visibly consistent with those errors. Record this as exploratory diagnosis, without changing the full-frame endpoint, scoring selected patches or omitting target20. This review has not seen the pixels and therefore cannot assign any of those causes.

If the existing images expose a concrete camera/layout mismatch, the next inexpensive work is a focused audit of the corresponding saved conditioning/crop/convention assumptions; algebraic ray checks alone did not prove real optical calibration or the model's response to those rays. If no specific defect is visible, retain the negative fixed comparison and stop the higher-support-benefit proposal. A later dynamic-data probe or ordinary recent/uniform baseline needs its own task justification; this result does not justify additional model arms or a named innovation.

## Exact source scope

The following file identities were checked at finalization; only their text/JSON bytes were read in this task:

- `work/S70_fixed_context_generation/scoring_01/receipt.json` — SHA256 `47eca25ed70d459875d0070fdf10ccc19a2a338426f49aa14e1c4d54911a7745`.
- `work/S70_fixed_context_generation/SCORING_CONTRACT.json` — SHA256 `a776fd9cc1af9014de2e9226364f8990e9a2461c45b23aa6e03e5354370df8ac`.
- `work/S66_s64_camera_scoring/PROTOCOL.md` — SHA256 `00320480d9a2ee56c5636dd79d96a8b8dc083627b01010c3ce070d1738363d5c`.
- `work/S66_s64_camera_scoring/measure.py` — SHA256 `55ab15381fb745f37af68a0978bb59c9d00e2ff1fa1870c969a3850aa117744a`.
- `work/S66_s64_camera_scoring/score_01/report.json` — SHA256 `5ce6bf7920820edb0fcd6f080a44b98fa88624cfa5ec3bade8b408aeadf03493`.
- `work/S46_c1_blind_scoring_preparation/score_c1_blind_candidate.py` — SHA256 `ada2ba80eceebe83a514fd929c6cc82b69669e6525e261ff4729064f2bac3f1a`.
- `work/S64_unit_repaired_generation/PROTOCOL.md` — SHA256 `82f0882401bc7ac79b9f893973b076a3dfbbd570a8cafaf1e23a5f0c4ae71691`.
