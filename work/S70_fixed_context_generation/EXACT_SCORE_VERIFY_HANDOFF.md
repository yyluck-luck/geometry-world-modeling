# Exact S70 score → integer verification → visual export handoff

Read-only source check at **2026-09-09T03:39:44.055876+00:00**. Let `D=/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S70_fixed_context_generation`. No S70 array, generated/reference PNG, weight, score result or verification result was read. No test or program was rerun; no source changed. This note describes the interface already implemented and reviewed, not a new gate.

**After root's actual generation acceptance and sealed main score**, root supplies `D/ROOT_RGB_VERIFY_BINDING.json` and its actual SHA256. The binding must contain:

| Field | Exact requirement |
|---|---|
| `status` | `ACCEPTED_S70_SCORED_OUTPUTS_FOR_INDEPENDENT_RGB_VERIFY` |
| `source_files_sha256` | Absolute-path→actual-SHA map including `D/verify_rgb_score.py` and `D/RGB_VERIFY_PLAN.md`; optional final delivery/review pins are also checked if included. |
| `root_scoring_binding_sha256` | Actual SHA of `D/ROOT_SCORING_BINDING.json`. |
| `score_receipt_sha256` | Actual SHA of sealed `D/scoring_01/receipt.json`. |

The existing scoring binding must retain status `ACCEPTED_S70_COMPLETE_GENERATION_FOR_FIXED_SCORING`, target IDs `[20,21,22,23]`, `ordered_reference_ids` equal to `{A0:[19,18,13,12],A1:[19,18,13,12],B:[19,18,14,13]}`, and absolute-path `result_files_sha256` entries for all nine saved generation arrays. Its source identity map is already the main scorer's input contract. The sealed score status must be **`COMPLETE_FIXED_RGB_SCORE_PENDING_INDEPENDENT_RECOMPUTE`** with the same binding/contract/scorer SHA and four frames in that order. No future hash is supplied by this note.

Invoke once, under root's external120-second timeout, with argv: **`["/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/.venv-cut3r/bin/python", "-B", "/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S70_fixed_context_generation/verify_rgb_score.py", actual_verification_binding_sha]`**. Keep the venv interpreter path un-resolved. The new create-only output is `D/rgb_verification_01/receipt.json`; expected successful status **`PASS_INDEPENDENT_INTEGER_RGB_SCORE`**, return0. Failure is `FAILED_PRESERVED`/return1; retain its output and do not reuse the directory. The verifier never starts export automatically.

The actual verifier reads eight NPY bodies: all three emitted `execution_01/{A0,A1,B}/targets_uint8.npy`, A0/A1 `all8_latents.npy` and `targets_fp32.npy`, plus `scoring_01/transformed_targets_uint8.npy`;49,102,848 numeric bytes, file headers additional. It additionally decodes the four contract-pinned native target PNGs. These are **real RGB-body reads**, even without viewing. It recomputes full-frame and four-target integer SSE divided by `N×255²`, PSNR and signed B−A0 within fixed absolute+relative1e−12; raw A0/A1 byte replay and36 predetermined reference mapping pixels are separately checked. It does not re-run the neural model or the full reference preprocessor, or independently recheck B's raw emission. A correctly reproduced failed A/A replay can pass arithmetic verification while attribution remains false/support null. This remains one known sequence with four correlated targets, GT cameras, declared ft-mse VAE, approximate K/no undistortion, and no validated new method.

**Static exporter compatibility: no concrete field error found.** `export_complete_visuals.py` consumes the two exact statuses above and matching `target_ids`; reference identity comes from `score.outputs_before_receipt["transformed_targets_uint8.npy"].sha256`, generated identity from `binding.result_files_sha256[absolute_path]`. All16 native outputs use the four correct row labels and fields `score.frames[i].mse[arm]`, `score.replay.all_passed`, and `score.delta_B_minus_A0`. These fields exist in the implemented score/verification schemas. After accepted actual results, the exporter creates `visuals_01`, checks PNG round-trip bytes, and emits status `COMPLETE_ALL16_NATIVE_PNGS_EXACT_READBACK`. This is only a low-impact source/schema check: no rendered-layout/runtime validation was done. The exporter snapshot was0644 at read time; root owns its final source and execution.

Exact observed source/review identities:

| File under D | SHA256 |
|---|---|
| `score_fixed_contexts.py` | `4c698efddeca50a2c35812632516ca458ab0f1a8f9dec8f4aa4cdde0f1584ab5` |
| `verify_rgb_score.py` | `dcaa746a6e338371d0cceac4855c276a535f0a5c526a8da0d2fd0c22d8e09acf` |
| `RGB_VERIFY_PLAN.md` | `039ad6e71584e40f4f3f9e25fa171db24e6e8f31fa262397ae82798481b50011` |
| `SCORING_CONTRACT.json` | `a776fd9cc1af9014de2e9226364f8990e9a2461c45b23aa6e03e5354370df8ac` |
| `RGB_VERIFY_SOURCE_REVIEW.json` | `4d8310eda1ac8b26e50226c6b509efea495ab9c90cbfa63e96ecc3ec57835073` |
| `ROOT_VERIFIER_SOURCE_ACCEPTANCE.json` | `b03379175e41daabeafa9fb48aad8c163f8d32f26096a57bf0da8705b2ded9bb` |
| `export_complete_visuals.py` | `0dc12e14a2dd0baceffe5c27324d8ddac1489b54cadc6acf7796bda761ab5387` |

Next: wait for root’s real sealed score and actual verification-binding SHA, then execute the already-reviewed integer verifier once. No additional synthetic suite or model launch is needed.
