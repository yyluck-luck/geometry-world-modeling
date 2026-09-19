# S17 CPU component preflight: source candidates and actual artificial checks

Recorded 2026-09-06, actual test UTC 11:04:17.899667–11:04:19.117603
(Asia/Shanghai 19:04:17–19:04:19), elapsed 1.217958 seconds.

**PASS_COMPONENTS_ONLY: 123 checks. This is not a full VMem or video-generation run.**
The checks used small random attention modules, artificial tensors, an independent
scalar rotary-position reference, and the extracted `do_sample` function with fake
sampler/denoiser/autoencoder objects. No trained model, weight, real RGB/depth image,
full pipeline, GPU, video, package installation, or download was used.

## Fixed source and artifacts

Author checkout:
`/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem`

Commit: `39291e4f272f6b4f270691d930926ab5930f942e`.
Selected original sources were copied under `original/`; modifications exist only
under `patched/`. The original tracked checkout was clean before and after; copied
source hashes were checked before and after. `source_provenance.json` records every
source and changed candidate. This is not a copied full runnable repository.

| Artifact | SHA-256 |
|---|---|
| `cpu_candidate.patch` | `6d8e1d459114d3c9026bcc8d2559d35bc965a24c22fb4916d97a35d1456c4bd4` |
| `source_provenance.json` | `cddb3a4a36a737dba6ef028af8c1d9626eb6bd4e66f7bc484617cc308f923a43` |
| `test_preflight.py` | `c8d385b6b0eb9e6abd66e4def6ff5c3c4dae045df48549dbb9b8170f00ff4ba7` |
| `numeric_receipt.json` | `7e8e8021e2fc25917971b62b5753a46550496bb833d9b219d42f1c38af341d2e` |

`prepare.py` creates the copies/patch and refuses to overwrite original copies.
The test script likewise refuses to overwrite its receipt. The successful stage
should not be rerun without a new scientific or implementation reason.

## Findings and exact boundaries

### Attention: native CPU flash already works

Author `modeling/modules/transformer.py:71–73` forces
`SDPBackend.FLASH_ATTENTION`. On the existing PyTorch 2.7.0 CPU environment this
**does work**: the profiler explicitly records
`aten::_scaled_dot_product_flash_attention_for_cpu` in all four artificial cases.
It must not be described as a CUDA-only blocker.

Actual forward calls supply no attention mask, no causal flag, no attention
dropout, and no custom scale. Their effective contract is full noncausal attention,
dropout zero, scale `1/sqrt(head_dim)`. Output-module dropout is separate; the
tested modules are in evaluation mode. Tests preserve this contract rather than
claiming a new general masked/causal implementation.

Artificial Q/K/V shapes `(B, heads, Qlength, Klength, dim)` were
`(2,5,17,17,64)`, `(2,5,17,19,64)`, `(3,2,8,8,64)`, and
`(1,2,129,137,64)`. They cover self, cross, temporal-length-eight, and uneven chunk
boundaries. They do not reproduce full sequence lengths or measure full model
memory/time.

| Comparison against FP64 dense formula | Maximum absolute error | Frozen tolerance |
|---|---:|---|
| Native CPU flash, FP32 | 7.748603820800781e-7 | atol 2e-6, rtol 2e-5 |
| Full CPU math SDPA, FP32 | 9.5367431640625e-7 | same |
| Query-only math chunks 7/64/128, FP32 | 9.5367431640625e-7 | same |

The candidate adds optional `cpu_math_query_chunk_size`, default zero, preserving
native flash. A positive value splits only Q; every chunk sees the entire K/V and
one complete softmax over all keys. Splitting K into independently normalized
softmaxes would be mathematically wrong and was not implemented. Eight actual
tiny VMem `Attention` module comparisons test same randomly initialized parameters
with self/cross context and default/chunked paths. No full pipeline configuration
plumbing for this optional attribute is claimed; a future isolated runner must
explicitly select it if required.

The other agent's 8.009 GiB single-logit-matrix calculation is a theoretical
explicit-dense alternative at full video dimensions. It is not a measured memory
cost of the existing CPU flash kernel or of these tiny checks.

### RoPE: signed positions and actual half-precision interface

Author `extern/CUT3R/src/croco/models/pos_embed.py:117–126` catches an unavailable
compiled extension and prints that a slow fallback is in use, while the fallback
class below is commented out. Importing that isolated original module in the
present missing-extension environment leaves `RoPE2D` undefined; the recorded
message is not evidence that a fallback exists.

Author `curope/curope.cpp` already contains a CPU mathematical implementation.
The package build nonetheless uses a CUDA extension and CUDA source. Its CPU
accessor is float32, while the embedded `blocks.py` explicitly converts q and k
to float16 before RoPE even when the surrounding inference is FP32. Therefore
merely compiling a CPU version of that accessor or removing `.cuda()` is not a
complete interface repair.

The candidate `rope_cpu.py` follows the original quarter-channel layout:
`[u_y, v_y, u_x, v_x]`. For each axis, quarter coordinate `j`, and signed position
`p`, its angle is `F0*p/base**(j/quarter)`. It computes the rotations in FP32 and
restores the input dtype. Position `-1` is preserved as a negative angle; it is
not clamped or converted to an unsigned index. `F0` is applied explicitly.

The old project `scripts/cut3r_rope_compat.py` assumes an existing Python RoPE
class with helper methods and `F0=1`. It cannot simply install on VMem's undefined
fallback symbol; it was not blindly reused. New code retains the upstream
CC BY-NC-SA notice.

Independent verification uses Python float64 scalar `math.pow/cos/sin` loops,
with direct channel indices from the C++ layout. It does not call the candidate
formula or an unavailable compiled extension as its oracle.

| Check | Maximum absolute error | Frozen tolerance |
|---|---:|---|
| D48/D64, signed positions -31..31 including -1, FP32, F0=1 or -0.5 | 2.2351741790771484e-6 | atol/rtol 2e-5 |
| Same source interface with FP16 input/output | 1.52587890625e-5 | atol/rtol 2e-3 |
| Separate signed stress positions ±767/±324/±31, FP32 | 7.653236389160156e-5 | atol 3e-4, rtol 1e-4 |
| Original CUT3R tiny self/cross blocks through candidate vs scalar RoPE | 6.8694353103637695e-6 | atol 2e-4, rtol 2e-3 |

The actual original self/cross block tests confirm that their RoPE call inputs
are FP16 and their surrounding operations are FP32. Zero-position identity,
input nonmutation, output dtype, dispatcher parity and rejection of unsupported
dtype/shape/position types also pass. Head dimensions 48 and 64 are artificial
source-compatible cases, not a validation of the unpublished-in-this-test 512
checkpoint configuration.

The wrapper selects the new implementation on CPU and retains the compiled
implementation on CUDA if available. Other devices fail explicitly. CUDA/MPS,
compiled-kernel numerical parity, gradient/backward and in-place alias semantics
were not tested. The candidate returns a new tensor; the actual examined forward
call sites assign this return value.

### Device plumbing: do_sample has real hard-CUDA calls

The exact source `do_sample` was AST-extracted without importing its dependency-
heavy module. In a CPU fake-sampler invocation the original function fails with
`AssertionError: Torch not compiled with CUDA enabled`; its CUDA autocast also
warns and disables itself. This is an actual component failure, not a full-model
attempt.

The candidate normalizes `device` to a torch device, makes autocast conditional
on CUDA, and moves c2w/K/input_frame_mask to that device. The original
`torch.randn(shape).to(device)` is preserved to avoid silently changing the RNG
source for CUDA callers. CPU fake-function tests check exact seeded noise,
device propagation, decode/latent returns, sample-only returns, and an interrupted
sampler returning None. All pass without the CUDA autocast warning.

This function still expects upstream c/uc, models and encoders to use compatible
devices/dtypes. It does not recursively repair them. Source inspection shows
the pipeline's generate call already passes `self.device` to `do_sample` and to
scene construction. The candidate also changes the scene-construction direct-
caller default to `None`, resolved as `self.device`, and makes the app decorator
device-aware. Those two changes were parsed and manually reviewed only; the
full pipeline/UI was not imported or executed.

## Environment and integration gaps

Existing executable: project `.venv-cut3r/bin/python`, Python 3.12.14,
macOS 26.7 arm64, torch 2.7.0, 8 CPU threads. Seed 0 governs artificial tensors;
the isolated noise-reproducibility check deliberately uses documented seed 17.
CUDA unavailable; MPS available but not selected.

Present by import specification: NumPy, einops, OmegaConf, transformers,
safetensors, torchvision, cv2, roma. Missing: diffusers, pytorch_lightning,
open_clip, gradio, spaces, open3d, curope and kornia. Presence is an import-spec
inventory, not proof that all present packages integrate correctly.

Full VMem construction still downloads/loads its main checkpoint, a diffusion
autoencoder, OpenCLIP and 512 CUT3R weights and uses additional dependencies.
These assets, full memory feasibility, scene construction, diffusion sampler,
video decoding, complete device consistency, model-quality parity and runtime
remain unverified. No dependencies or original checkout files were changed.

## Process and next decision

Applied the Supervisor `vibe-research-workflow` coding guidance and local Claude
`sci-scientific-critical-thinking` guidance already read in this research session:
bounded implementation, independent mathematical reference, explicit assumptions,
and retained actual failures. No Claude model/CLI was used. Root maintains the
canonical project ledger; this subtask records its own source, code and receipt.

The next bounded step is source-only review of whether the embedded CUT3R 512
geometry path can be invoked independently of the full VMem/VAE/OpenCLIP pipeline.
Only after a frozen interface/resource plan and completed weight identity checks
should a new real two-image integration attempt be made. This component preflight
alone does not justify starting a full video-generation run.
