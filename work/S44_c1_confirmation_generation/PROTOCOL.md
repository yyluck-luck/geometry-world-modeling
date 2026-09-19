# S44 C1 baseline-only confirmation generation protocol

Status: source preparation only. No C1 model, image decode, generation, archive, score, or visual inspection is authorized until the exact frozen manifest core receives two different-author reviews and those reviews are attached create-only.

## Scientific purpose and fixed differences

C1 is the second row of the already frozen S42 three-scene return-discrepancy screen. It is a strong-baseline confirmation run, not a method, ablation, or novelty experiment. It must use the same declared component variant and the same two-batch VMem path as B0/S40.

Relative to the sealed S40/B0 generation manifest, only these run variables may change:

- input: `jesus.jpg`, SHA-256 `d611976bb9d3e8d6e1740b86ead24028bfd7857944eba118458e09e7e645f3e1`, original size 1702 x 1276;
- seed: 43 instead of 42, represented consistently in `controls.seed`, a separately bound inference YAML whose only semantic/byte-content change is `seed: 42` to `seed: 43`, and the Python/NumPy/Torch RNG calls;
- output root: `results/S44_C1_confirmation_generation`;
- row-specific schema/status text, row-specific gate/adapter/launcher/protocol source identities, review bindings, and timestamps needed to keep this execution separate and auditable.

All scientific controls remain fixed: CPU, float32, 8 threads, 576 x 576, T=8, context=4, target=4, 50 diffusion steps, default NMS, `initialize -> turn_left(5) -> turn_right(5)`, 1800 seconds per batch, 3600 seconds total, 45 GiB process-tree RSS, and at least 10 GiB free disk. One fresh worker loads once; both batches share the same pipeline and RNG without a reset. The history must be 1 -> 5 -> 9.

The exact frozen S42 primary comparison remains ID0 versus ID8 on `M_outer4`; the threshold remains strict unrounded float64 MSE greater than 0.01. This generation stage does not score or view C1.

## Reuse boundary

The sealed S39 loading evidence is reused only as evidence that the five named component files and declared ft-mse variant loaded successfully under the S40 model/config structure before generation. The C1 gate proves that its YAML equals the sealed S40 YAML after the single `seed: 42` to `seed: 43` substitution. Image preprocessing is not part of model construction, so the prior `changi.jpg` identity is not reused as C1 input evidence. The C1 gate separately binds and hashes the exact `jesus.jpg` bytes before model construction. It must never claim that S39 loaded or generated the C1 image.

The C1 launcher is an AST-derived copy of the frozen S35 supervisor. It may change only the gate/factory routes and fixed schema/status labels, and must reverse to the exact S35 AST. The C1 runtime adapter is an AST-derived copy of the exact S35 runtime factory. It changes only the gate import, four evidence labels, and the four exact seed literals used by `random.seed`, `numpy.random.seed`, `torch.manual_seed`, and the config guard from 42 to 43; reversing those edits must recover the complete S35 AST. It then applies the same VAE and state-dict invariant checks used for S40. The S35 integration, archive, trace, model, geometry, renderer, and navigation sources are reused byte-for-byte.

## Freeze and review sequence

1. A standard-library-only freeze tool completes command/source/parent/input/config/freshness preflight before it can consume a formal path. Freshness treats broken symlinks as occupied. It writes a complete hidden staging bundle and atomically publishes one immutable `freeze_attempt_01/manifest_core.json` plus its receipt without importing scientific packages or decoding pixels.
2. A source reviewer and a runtime/freshness reviewer, both different from the core author, independently bind the exact core hash and issue no PASS if any non-allowed difference, path reuse, source mismatch, missing resource, output collision, or scope ambiguity exists.
3. The freeze tool checks that attaching the two exact reviews did not change the review-excluded core hash, validates the exact future manifest through a temporary non-authoritative path, and assembles a read-only attachment bundle in hidden staging. It writes the metadata gate and successful attach receipt before adding the canonical manifest, then atomically publishes the complete `review_attachment_01` directory without replacement.
4. The row-specific execution gate accepts only the exact canonical attached-manifest path together with its sibling successful attach receipt and metadata-gate hash. Only that final manifest SHA may be passed to the launcher. The launcher writes to a new `execution_01`; the scientific output root must still be absent.

Review PASS is permission to attempt the frozen baseline once. It is not evidence that generation completed or that C1 supports a failure hypothesis.

## Required terminal evidence and boundaries

The launcher preserves actual start/end times, process-tree monitoring, trace boundary, return code, worker receipt, resource gate, runtime loading, and partial evidence on failure. A returned process is still pending independent archive/readback review. Later work must independently verify the full archive, second-batch consumption of first-batch generated history, camera-condition closure, authoritative nine-frame pixel identities, blind scoring, and all-nine visual QA before C1 becomes a technically valid row.

No C1 outcome alone completes the cohort. C2 remains mandatory regardless of B0 or C1 results. No infrastructure repair, successful run, metric difference, or visual impression is an innovation claim.

## Frozen parents

- S40 final manifest: `work/S40_declared_variant_generation/review_attachment_01/manifest.json`, SHA-256 `9951a78909a7d792dd536cea067c14e369cff776115a078d2f61c66c085cdebe`.
- S42 preregistration: `work/S42_baseline_failure_preregistration/PROTOCOL.md`; its actual SHA is bound by the freeze tool and final manifest.
- S39 loading manifest and all four loading evidence records remain exactly those bound by the sealed S40 manifest.
