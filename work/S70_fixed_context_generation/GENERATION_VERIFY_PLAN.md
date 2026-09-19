# S70 independent generation-result verification

Author: `/root/c2_v9_source_primary`, distinct from the generator author. This is a prospective, source-only handoff. It has not read S70 scientific results or verified that generation completed.

Run once after root supplies actual completed external and worker receipt SHA256 values:

```text
/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/.venv-cut3r/bin/python -B /Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S70_fixed_context_generation/verify_generation.py <actual-external-receipt-SHA256> <actual-worker-receipt-SHA256>
```

The existing real `ROOT_RUN_BINDING.json` is pinned. No future result hash is invented. Output is create-only `generation_verification_01/receipt.json`, sealed 0444 on return. Root may supervise this small verification with a 120-second external timeout; the verifier also checks its final elapsed time against 120 seconds. An exception records a failed receipt without replacing an earlier attempt.

The finite check covers:

- Actual external return, stdout/stderr identities, worker completion, fixed argv/controls/source/accepted-input bindings, sampled resource trace and registered worker exit. Resource conclusions retain the observer's sampled scope.
- The exact ordered worker readlist and empty model-loading discrepancies. Original weight identities are checked against recorded consumed SHA/size and the already audited loader source. The verifier never opens weight bodies, constructs a model, or re-hashes live parameters. Before/after value, object-identity and training-mode hash aggregates are checked against the saved model baseline.
- Both accepted S69 condition archives, all 18 fields and fixed input order. Each arm must have one sampler call, 50 finite-return step records and full-eight decode metadata. Common/restored/entry/terminal RNG records, every consecutive step transition and all three saved initial-noise identities must agree with the original fixed draw path. No step epsilon is regenerated.
- All three arms' saved noise, full-eight latents, four raw FP32 targets and four emitted uint8 targets: file/body SHA, shape, dtype and finite values. The literal original NumPy emission mapping is independently checked across all 12 targets. The frozen FP32 −0.1 advisory-flag boundary is disclosed and does not alter emitted bytes.
- Full A0/A1 latent, raw-target and emitted-target byte equality, separate from numerical equality. A0-versus-B differences are descriptive counts/maxima without a reference score. If accurate records show failed replay, verification can pass while attribution remains false. B is retained; there is no retry or additional condition.

Planned scientific reads are exactly twelve generated NPY files (63,700,992 array-body bytes; 63,702,528 bytes including their standard NumPy headers) and two accepted S69 NPZ files (12,785,532 file bytes). Source, contract, actual terminal/progress/RNG/model-descriptor JSON and text are read separately and individually logged. Actual counts and bytes, including headers, are reported from the real readlist; the fixed size projection does not substitute for that record. The local VAE configuration is read; the weight symlink is resolved/stat'ed only.

There are zero reference RGB/depth reads, image displays, model imports/instances, sampling/decoding calls, or weight-body reads. This is a different-author, team-internal verification of saved results and observed execution evidence, not an external model reproduction, image-quality result, old C2/cohort completion, online retrieval result, or new-method validation. The known-target, GT-camera, approximate-intrinsics and declared ft-mse-VAE limitations remain.

Preparation validation: direct `--compile-only` returned 0 with `COMPILE_ONLY_NO_GENERATION_PAYLOAD_READ`. This mode reads only its own source and imports no NumPy or Torch. No real verification, numerical fixture or scientific array decoding was performed during preparation.
