# E1 — Pre-declared specification: GEN3C stale-admission consequence, zero GPU

**Frozen before any execution output exists.** No result had been produced when this was written.
Nothing below may be changed after seeing output. If the spec itself is wrong, the run is
discarded and a new spec is written and re-declared, rather than amended in place.

## 1. Object under test

Released repository `nv-tlabs/GEN3C`, public commit `db2ffe12ced12ddafcec5e0422ee46ce8520746b`
(confirmed by `git rev-parse HEAD` on a shallow clone, 2026-09-19).
Paper: arXiv:2503.03751, *GEN3C: 3D-Informed World-Consistent Video Generation with Precise Camera
Control* (CVPR 2025 Highlight).

**No file in the released tree is modified.** Released modules are imported as-is.

## 2. The claim being tested

> After a successful seed, a subsequent **failed** seed leaves the server with the 3D cache
> cleared but the outer `model_seeded` flag still `True`, so `request_inference` admits a request
> that the server's own admission precondition was meant to reject.

Source basis, all verified statically before this spec was written:

| fact | location |
|---|---|
| `self.model_seeded = False` in `InferenceModel.__init__` | `gui/api/server_base.py:60` |
| `request_inference` raises unless `self.model_seeded` | `gui/api/server_base.py:122` |
| `seed_model` clears cache and histories **before** seeding | `gui/api/server_cosmos_base.py:53-55` |
| `seeding_method(...)` is called and may raise | `gui/api/server_cosmos_base.py:62-70` |
| `self.model_seeded = True` executes **only on success** | `gui/api/server_cosmos_base.py:71` |
| multi-frame seeding without depths raises | `cosmos_predict1/diffusion/inference/gen3c_persistent.py:208` |
| the model's own `clear_cache()` sets `cache=None`, `model_was_seeded=False` | `gen3c_persistent.py:551-553` |

## 3. Harness construction, declared in advance

`CosmosBaseModel` is instantiated directly. This is possible because `InferenceModel`
(`server_base.py:30`) is a **plain class that does not inherit `ABC`**; `@abstractmethod` without
`ABCMeta` does not prevent instantiation. `CosmosBaseModel.__init__`
(`server_cosmos_base.py:37-38`) only calls `super().__init__(**kwargs)` and does **not** construct
an inner model, so the inner model is supplied by the harness.

The stub assigned to `.model` implements exactly four members, with **no video model, no weights,
no torch tensors, no CUDA**:

1. `clear_cache()` → sets its own `cache = None`, `model_was_seeded = False`;
2. `seed_model_from_values(**kwargs)` → returns a minimal valid result on call 1; raises a
   controlled exception on call 2;
3. `frames_per_batch` → an integer, so admission bounds are computable;
4. `inference_on_cameras(...)` → records whether it was reached and whether `cache is None`.

Inputs are small NumPy arrays. **If instantiating `CosmosBaseModel` turns out to require editing
released source, E1 is declared INFEASIBLE and reported as such** — no patched variant is
substituted and no result is claimed.

## 4. The declared sequence

| step | action | recorded |
|---|---|---|
| S0 | construct `CosmosBaseModel`, attach stub | `model_seeded`, stub `cache` |
| S1 | `await seed_model(req_A)` — stub succeeds | `model_seeded`, stub `cache`, `model_was_seeded` |
| S2 | `await seed_model(req_B)` — stub raises on call 2 | exception type, `model_seeded`, stub `cache` |
| S3 | `request_inference(req_C)` | admitted or raised; stub `cache` at admission |
| S4 | **clean-control**: fresh harness, repeat S1–S2, then explicitly set `model_seeded = False`, then S3 | admitted or raised |

## 5. Pass / fail, frozen now

**CONFIRMED if and only if all four hold:**

- **P1** — after S1, `model_seeded is True`.
- **P2** — after S2, the exception propagated out of `seed_model`, **and** `model_seeded is still
  True`, **and** the stub's `cache is None` (cleared before the failure).
- **P3** — at S3, `request_inference` returns an `asyncio.Task` **without raising**: the request is
  admitted while the cache is `None`.
- **P4 — non-vacuity / clean-control** — at S4, with the flag explicitly cleared,
  `request_inference` **raises**. This proves the admission gate is functional, so P3 is caused by
  the stale flag and not by an inert gate.

**REFUTED if any of P1–P3 fails.** A refutation is recorded as a correction and GEN3C is removed
from the HIT column of the audit table.

**DISCARDED AS VACUOUS if P1–P3 hold but P4 fails** — an always-admitting gate proves nothing.
GEN3C then returns to UNVERIFIED rather than being counted in either direction.

## 6. What a CONFIRMED result does and does not license

**Licensed:** the label `MEASURED_SERVER_CONTRACT_CONSEQUENCE` for GEN3C — a reproducible,
released-code control-flow consequence at the server/API layer.

**Not licensed, and must be printed alongside any use of the result:**

- `frozen_weight_generation_consequence` remains **UNMEASURED**. No video was generated, no weights
  loaded. This is **not** evidence about image quality or network behaviour.
- It is **not** evidence that GEN3C's published results are affected.
- The stub is attached by the harness. Selecting a custom model through **public configuration
  alone is not possible**; the released factory exposes no arbitrary class path. This limitation is
  reported, never omitted.
- One confirmed instance is **not** prevalence. It licenses no `M/N` claim.
- It says nothing about VMem, whose intent oracle remains **UNRESOLVED**, or about CausVid.

## 7. Standing constraints

No GPU. No training. No fine-tuning. No weight download. No modification of released source.
`new_method_validated=false`; `novelty_authorization=NONE`.
This experiment authorises nothing further; it produces one recorded observation and its stated limits.
