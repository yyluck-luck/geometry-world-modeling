# S70 fixed-context generation protocol

Frozen before any S70 generation, target-reference read or score. Author: `/root/c2_v9_recovery_author`. This executes one fixed post-selection comparison, with an exact A replay control. S69 is already independently accepted (`ROOT_FINAL_RESULT_ACCEPTANCE.json`, SHA `e2eae97c8d541d6bf127dbd61137e3ad1d9f8af3fdfce869bf696be3613506c4`). The earlier SOURCE_PLAN is historical; its then-pending S69 condition has now been resolved.

## Fixed experiment and actual inputs

Order is A0=geometry, A1=geometry, B=pose14. Geometry histories are `[19,18,13,12]`; pose14 histories are `[19,18,14,13]`. Both use targets `[20,21,22,23]` in the final four of eight slots. Read exactly the two accepted S69 NPZ files, jointly 12,785,532 file bytes, from verified bytes and validate all 19 fields per file against frozen shape/dtype/body SHA and finiteness. Only saved `c__*`, `uc__*`, `post_cond_optical_c2ws`, `K_pixels_576`, and `input_masks` enter sampling. The other saved fields are provenance checks. Make independent Torch copies for each arm. Do not rerun get_cond or flip/center/scale cameras again.

The complete two condition bundles change naturally, including original normalization and guidance inputs. These are already seen targets, GT-camera conditioning and fixed historical selection sets. Approximate ROS K, interpolation and lack of undistortion remain limitations. This is not online retrieval, an unseen-target experiment, an independent multi-scene sample, a new method or a replacement C2/cohort result.

## Reused model and sampling definitions

Load the six original source files listed by exact SHA in INPUTS.json. Register empty `modeling` and `modeling.modules` namespaces, then verified original transformer/layers/network/sampling/autoencoder definitions. Register modules before execution for dataclasses. Extract only the original `do_sample` and `tensor_to_pil` AST definitions from the bound util source, with their complete globals. Do not import the full pipeline/CUT3R/CLIP, instantiate Navigator, encode images, retrieve, construct geometry or invoke a renderer. Preserve the original FLASH_ATTENTION context and the already declared S20 CPU do_sample adaptation.

Use original `VMemModel(VMemModelParams())`, `VMemWrapper`, original `AutoEncoder(chunk_size=1)`, `DDPMDiscretization`, `DiscreteDenoiser(num_idx=1000)` and `create_samplers(guider_types=1,...)[0]`. Index 0 here is **MultiviewCFG**, not guider type 0. Each arm gets a fresh sampler and denoiser. Original four c/uc fields remain present: crossattn, replace, concat and dense_vector. Original guidance uses each arm's actual saved normalized camera/K/mask.

Fixed CPU8 (interop1), FP32, 576×576, T8/C4/F8, cfg2.0, cfg_min1.2, all50 original steps, s_churn0/s_noise1, original full8 VAE decode with chunk1. No tiling/slicing, resolution or step reduction. The two local weights are VMem (5,056,346,672 B) and declared ft-mse VAE (334,643,276 B), plus 547 B VAE config; identities are in INPUTS.json and taken from accepted S64. Consume the exact verified weight bytes in the decoders: Torch weights_only CPU and strict state dict, original key mapping; VAE original constructor routed to the verified local config and one safetensor byte load, requiring empty loading discrepancies. Network downloads are disabled. The original SD2.1 VAE identity remains UNKNOWN; ft-mse is a declared component variant, not an exact original-baseline claim.

## Randomness, model state and failure meaning

After load, set seed44 once and capture complete actual Python, NumPy legacy and Torch CPU RNG states. Restore that same state immediately before each original do_sample. Save each actual `[8,4,72,72]` FP32 initial noise **before** original prepare_sampling_loop modifies it. Original sampler is called exactly once per arm. Its 50 sampler_step calls still draw randn_like at churn0 because sigma_hat includes1e-6; preserve this behavior. Observe each step's before/after RNG SHA without drawing any additional randomness. Save complete common, sampler-entry and terminal states. A failed step also records its entered state and exception; completed steps are distinguished from failures.

Three actual initial-noise body hashes, sampler-entry RNG states, all50 corresponding step RNG states and final RNG states must agree. This validates the recorded stream under the fixed original draw path; the individual step epsilon bodies are not archived. It does not infer shared randomness from the seed alone.

The same two loaded CPU/FP32 eval models are reused. Record actual byte SHA for every parameter/buffer plus object/data pointer/version identity and all training modes, once as a detailed baseline and before/after every arm as matching aggregate SHA. This checks value equality, not only object identity. No per-step weight rehash or model copies. A changed/unchecked model state stops remaining arms. All returned latent/RGB arrays and any failures remain on disk.

A0/A1 exact raw byte equality is required separately for all8 latent, four-target FP32 RGB and uint8 output. No numerical tolerance or torch.equal substitution. A replay mismatch does **not** delete B, rerun an arm, or change conditions. It sets `exact_replay_pass=false`; all returned arms may still be described, but their difference is not attributed to context. Actual RNG mismatch is a failed fixed-generation experiment after retaining all returned results. Ordinary arm exceptions are retained and other fixed arms may continue only with verified unchanged model state and available resources. No retries or result-dependent choice.

## Outputs and bounded execution

Exact argv (the venv executable must not be resolved to its base interpreter):

```text
["/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/.venv-cut3r/bin/python", "-B", "/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S70_fixed_context_generation/generate_fixed_contexts.py"]
```

The single create-only output is `work/S70_fixed_context_generation/execution_01`. Existing failure/results are never overwritten. Root starts it only after distinct source review and binding to root's prospective observer/scoring contract. Root's external observer enforces 1800s per arm, 5520s total, process-tree RSS45GiB and ≥10GiB disk free. Worker checks the same time/disk limits and its macOS **self** peak RSS at boundaries; this is not a substitute for external process-tree monitoring. No launch here. Progress rows expose actual phase `start/load/arm_start/step/arm_complete/failure/complete`, UTC, elapsed_seconds, arm, step, arm_elapsed_seconds, pid. Load includes distinct component progress. External termination may leave a partial directory without a worker final receipt; the external return/termination is authoritative for that case.

Each `A0`, `A1`, `B` directory contains:

| File | Content |
|---|---|
| `noise.npy` | Actual initial FP32 `[8,4,72,72]`, before scaling |
| `all8_latents.npy` | Actual returned FP32 `[8,4,72,72]`, saved before decode |
| `targets_fp32.npy` | Raw decoded FP32 `[4,3,576,576]`, target order20–23 |
| `targets_uint8.npy` | Original per-frame tensor_to_pil output `[4,576,576,3]` |
| `outputs.json` | `arrays` keys all8_latents/targets_fp32/targets_uint8, path/file SHA/shape/dtype/body bytes/body SHA, target IDs, status |
| `steps.jsonl`, RNG JSON, `receipt.json` | Actual timing/randomness/state/conditions and complete or failed arm |

Full8 RGB is decoded transiently, but only the four targets are persisted. Save raw FP32 **before** original quantization: per-frame min<−0.1 triggers `(x+1)/2`, otherwise unchanged; then ×255, clip, uint8 truncation. Record actual raw min and branch per target. No unconditional range conversion or rounding. No reference RGB/depth bodies are read and no generated image is viewed; generated RGB numerical bodies are necessarily computed, serialized and hashed, not described as “0 RGB.”

Global `receipt.json` contains all arm statuses, original input/source metadata identities, actual readlist, progress SHA and model/randomness/replay results. Success status `COMPLETE_THREE_FIXED_GENERATION_ARMS` requires three full arms and the shared actual random stream; `exact_replay_pass` remains an independent boolean. Otherwise status is `FAILED_FIXED_GENERATION`; unrun arms are explicit. Worker files are finalized0444. Root handles scientific score/independent checks separately; no automatic scoring, pixel viewing or threshold changes.

Author validation is limited to compile and one inert source import (`--check-imports`): module definitions/package versions, no model instance, no weight/condition NPZ/RGB body and no execution directory. No old numerical matrix is repeated. Author delivery lists only the four author-owned files, preserving root and reviewer ownership of their separate material.
