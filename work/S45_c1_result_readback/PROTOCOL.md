# S45 C1 saved-output readback candidate protocol

Status: `SOURCE_ONLY_AWAITING_C1_TERMINAL_BINDING_AND_INDEPENDENT_SOURCE_REVIEWS`.
This directory is being prepared while the unique S44 C1 generation is still running.
No C1 result file, tensor body, image body, pixel array, trace payload, terminal receipt,
or model output was read to prepare this candidate.  No readback attempt has run.  An
absent future identity is never represented by a fabricated hash or placeholder file.

## Purpose and claim boundary

The eventual worker may establish only an identity-bound readback of saved C1 outputs:
whether the first-batch generated history was actually committed, selected in the
second batch, passed through the recorded condition/sampler path, and preserved across
the second `cache_commit`.  It separately records three meanings that must not be merged:

1. **Saved-quantity consumption:** bitwise comparisons of the archived latent,
   embedding, camera and intrinsic tensors along the recorded call path.
2. **Pixel identity:** archived PIL pixel-tensor provenance and cross-batch bitwise
   identity, plus hashes of archived files.  This does not decode a PNG or judge what it
   depicts.
3. **Image quality:** `NOT_EVALUATED`.  Visual quality, camera obedience, blind C1
   scoring, method gain and novelty belong to later, separately frozen stages.

## Exact derivation from reviewed S40 v3.3

`readback.py` is a reversible AST derivation of the independently reviewed S40 v3.3
reader at `work/S40_result_readback/readback.py`, SHA-256
`d4c22504569ad1fb1fcc74ea1da83b4f244f4de803f5d0fadc16e8da06777933`.
It changes only the generation directory and its four row-specific pinned source
identities, plus the fixed schema/status/scope labels required for C1.  Before executing,
it reverses every edit and requires full AST equality with that exact parent.

The inherited v3.3 checks remain mandatory:

- only a raw archive `kind=tensor` node creates the internal `TensorDescriptor` marker;
  a descriptor-shaped ordinary dictionary cannot be mapped;
- a marked descriptor must equal the previously body-verified complete descriptor, not
  merely point at a registered blob path;
- `kind=pil_image` recursively preserves the provenance marker on its `pixels` tensor;
- list and tuple remain distinct, scalar type labels must match exact built-in value
  types, batch 1 must contain the exact integer list `[0]`, and batch 2 must contain a
  fully verified one-dimensional integer tensor;
- the archive inventory, tensor sidecars and bodies, archive/trace hash chains,
  two-batch state machine, 50 Euler observations per batch, 576-resolution sample
  shapes, source hashes and input stat seals are checked without importing Torch, a
  model, a renderer or the generation pipeline;
- there must be exactly two archive `cache_commit` captures and two corresponding trace
  events.  The first committed five rows must match the second context cache; the second
  context must contain at least one generated ID; the second commit and map must close
  the 1 -> 5 -> 9 history.  Latent, embedding, camera, K and cached PIL pixel tensors are
  checked through the same cross-batch chain.

The C1 manifest is already fixed at
`work/S44_c1_confirmation_generation/review_attachment_01/manifest.json`, SHA-256
`1e86e8279c608995a03d6675a8636c354d6d4d046b7c8faea9611d6e6a9fd93b`.
The reader requires its 218-file source domain and these row-specific pins:

- `launch_generation.py`: `c94a982b0c0cb3fa895323ca9d7aa4e2b91eb7146eece35bdb0aedd1c157a74b`
- `generation_gate.py`: `961b9550f5ea438a338eb24ba9f36dd18f22d7f0719f9b54109e182755ab43dc`
- `runtime_adapter.py`: `afedaadca7bff62616368541d980a28f24131e1256eafef7af81275aa09dfb4e`
- `PROTOCOL.md`: `77c72263f6f58f77e5990a7db1557773013b9b84b14fb040f20faaaae6e701b5`

It also requires C1-specific manifest, generation, worker and component-loading statuses.
It does not inherit S40's selected IDs or file counts as expected C1 results.  The only
fixed scientific execution contract is the preregistered two-batch 1 -> 5 -> 9 path; all
actual C1 identities and selected IDs must come from the sealed C1 archive.

## Future terminal gate

The worker is not runnable from this preparation receipt.  After C1 reaches a clean
terminal state, `terminal_binding_01.json` must be created once from actual files and
must bind the exact manifest, external terminal receipt, worker receipt, resource gate,
runtime-loading receipt, observation summary, full archive manifest, trace chain and two
different-author terminal-evidence reviews.  Its own file SHA is supplied to the
supervisor.  The following identities do not exist or are not terminally sealable during
this preparation and therefore have no value in this protocol:

- C1 external terminal `execution_01/receipt.json` SHA;
- C1 terminal `worker_receipt.json` SHA;
- terminal `runtime_loading.json` and `observation_summary.json` SHAs;
- full `archive/manifest.json` and `trace/events.jsonl` SHAs;
- the two terminal-evidence review SHAs;
- the final `terminal_binding_01.json` SHA.

All must be measured only after the unique generation closes.  A missing file, partial
receipt, nonzero return, resource-limit field, open trace, incomplete archive, review
blocker, mismatched hash, reused formal path, or broken symlink keeps the readback closed.

## Eventual output and failure rule

The only formal supervisor path is `supervision_01`; the only formal worker output is
`executed_01`.  Both must be absent filesystem entries, including absent broken
symlinks, through terminal-binding preflight.  Preflight failures use unique
non-authoritative receipts and do not consume either formal path.  Once
`supervision_01` is created, every partial or failed execution is retained there and
`executed_01` is never deleted or reused.  There is no automatic retry, alternate
command, output overwrite, result cleanup, or resource-budget expansion.

The worker may import only NumPy 1.26.4 after a complete archive descriptor/body identity
has passed; it uses read-only memmaps.  The outer supervisor fixes one numerical thread,
a 300-second total wall budget, sampled process-tree RSS at 2 GiB, and a 10 GiB free-disk
floor.  These are execution limits, not claims that this unexecuted candidate already
passed them.

