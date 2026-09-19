# S58 C2 V9 saved-output readback — source draft

Status: `SOURCE_PREPARATION_ONLY_AWAITING_ACTUAL_GENERATION_TERMINAL`.
This is a source adaptation under the fixed S58 reuse plan
`work/S58_c2_postgeneration_reuse/REUSE_PLAN.md`, SHA-256
`c0111e5a799f1d033294fd9702d7299669fa9c277774ba57d6ecd4019f0f5352`.
It does not assert V9 completion, create a terminal binding, authorize execution,
or report a C2 measurement. Root owns the later actual-terminal review and ledger.

## Fixed inheritance and exact delta

The immediate implementation reference is S45 C1 `readback.py`, SHA
`0ec8eda2e89553a201ec274144038ec79f9c3cbb751ebe30ec1d619c8145a2ab`.
The executable derivation still uses the exact S40 v3.3 reader, SHA
`d4c22504569ad1fb1fcc74ea1da83b4f244f4de803f5d0fadc16e8da06777933`.
It changes only the generation-root assignment, its five C2 source pins, fixed
row/schema/status/scope labels, and exactly one assertion:
`len(m['source_identities']) == 218` becomes `== 219`.
The AST transform counts that exact comparison once, reverses every edit, and
requires full equality with the pinned S40 AST. This is the only numeric literal
change; no tensor, tree, trace, matching, camera or scoring math is altered.

The canonical manifest is
`work/S47B_c2_confirmation_generation_v9/review_attachment_01/manifest.json`, SHA
`caa6d7c04d7784e731165e05c07ff4e358322d14c8e76f08c2337b7f4dc641ac`, schema
`s47-c2-confirmation-two-batch-v1`, status
`FROZEN_C2_BASELINE_CONFIRMATION_TWO_BATCH_EXECUTION`, with exactly 219 sources.
Its five row-specific source pins, also checked against their actual file bytes:

| Source | SHA-256 |
|---|---|
| generation_gate.py | 4cd5c2179d2eaf17b85890acb5198d8573d2525be3e787a7ce00a17e7f2473cd |
| runtime_adapter.py | 5e6f2e89c724cfc3f5b4eb486eb2a9384fde9b23fb12010576f5c7f3f98e8d7f |
| launch_generation.py | 54c17a221e16b41c62b208cabe54895b0b0d8fc9c12528eb4d997408bb150693 |
| create_launch_authorization.py | 34666995d93a4e9a4629ac31b75b7c65e3fc989a0efe10732113c358284053a5 |
| PROTOCOL.md | 18c8a1ea3ce8f7c1b82195e3fc46adabc24488b6ce474d16a09cf79bbde17599 |

The output route is `results/S47B_C2_confirmation_generation_v9`. The input and
seed remain the frozen C2 living_room.jpg and 44; the reader neither replaces them
nor imports the generation pipeline.

## Unchanged scientific checks and boundary

The reader retains S40 v3.3 `Reader.descriptor/tree/metadata/array` and
`trace_sequence`: raw tensor provenance markers, verified complete descriptors,
PIL pixel-tensor provenance, exact list/tuple/scalar types, batch-1 integer `[0]`,
batch-2 verified integer-vector IDs, sidecar/body and archive/trace hash chains,
50 Euler observations per batch, 576-resolution shapes, and input stat seals.
Exactly two cache commits must close history 1 → 5 → 9. First-batch generated
history must occur in the second context. Latent, embedding, camera, intrinsic
and cached PIL pixel tensors follow the inherited bitwise cross-batch checks.

A future PASS means saved-output identities and saved-quantity cache consumption
only. Archived pixel-tensor byte identity is separate from PNG decoding and
visual quality; those remain `NOT_EVALUATED`. Requested numeric cameras are
separate from rendered camera obedience. S57's observer correction is not part
of this reader. There is no C2 blind score, cohort decision, model improvement,
long-horizon result or novelty claim here.

## Execution remains closed

Preparation reads source text and allowed metadata only: no C2 result payload,
trace payload, tensor body, image body, array mapping, model call or readback run.
Only source parsing/compilation and reversible AST derivation checks are performed.
No future receipt SHA is fabricated and no formal `terminal_binding_01.json`,
`supervision_01` or `executed_01` is created.

The future supervisor requirements are in `SUPERVISOR_PROTOCOL.md`. The source
reviews are new reviews of these exact hashes; S45 reviews do not transfer.
Only after the actual V9 outer return and scientific execution/metadata reviews
exist may root create the real terminal binding. The unchanged monitor bounds
are one numerical thread, 300 seconds, sampled 2 GiB process-tree RSS, and a
10 GiB free-disk floor. Only read-only NumPy memmaps are permitted by the worker.
Fresh-path and no-retry rules preserve every failed or partial formal attempt.
