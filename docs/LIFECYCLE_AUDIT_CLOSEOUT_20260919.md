# Lifecycle-state audit — closeout

**Date:** 2026-09-19 · **Disposition:** STOP · **GPU used:** none
`new_method_validated=false` · `novelty_authorization=NONE` · 800 GPU-hour tranche withdrawn
C6 (the requirement that the contribution be a method) **not relaxed**; everything below therefore
sits outside the authorised contribution type.

This document consolidates one day's work. The append-only ledger `RESEARCH_MEMORY.md` holds 26
entries for this date; this is the readable summary, not a replacement for it.

---

## 1. What was attempted

After every method axis closed, one reframing survived review: *released stateful video /
world-memory systems may have incomplete reset and state-isolation semantics — a defect class, not
one bug, detectable by a pre-specified audit and measurable on frozen weights.*

The day tested whether that reframing is (a) unoccupied, (b) supportable by evidence obtainable at
zero cost, and (c) able to carry a contribution.

## 2. The audit predicate, as corrected

The predicate was revised **after it produced a false positive**. Final form:

1. **Persistent state identification** — locate the state unit across a public call-ownership
   boundary; show call A wrote it and the object survives into call B.
2. **Consumption proof** — show the value written on A is *actually read* on B, with no
   recompute, overwrite, cache rebuild, or object swap in between.
   *A structural asymmetry between the init path and the reset path is not sufficient.*
3. **Lifecycle coverage proof** — check every field, alias, and outer admission/gating flag on B's
   read path; show the public reset, failure path, or new-session boundary misses one of them.

**Minimum evidence, all four required and all from the same case:**

```
(writer on call A, public sequence A→B, exact consumer on B,
 dominance check showing no recompute/overwrite/reset covers it)
```

Missing any element → `SUSPECT-UNTRACED`, never HIT.
Deliberate history/autoregressive state → `INTENDED-CONTINUATION`, and it may not fill a gap.

**Both failure directions are real:**
- *"field absent from `reset()`" ⇏ defect* — CausVid recomputes positions per call.
- *"an explicit reset exists" ⇏ clean* — GEN3C's `clear_cache()` resets the inner flag while the
  outer admission flag at another layer is never cleared.

## 3. Result

**Frame: N = 20** — commit-locked, public-call-boundary-audited video/world-model candidates, from
a 32-row survey, excluding 10 OUT-OF-PREDICATE and 2 modality exclusions.
**This is a convenience frame, not a sampling frame.**

| verdict | count |
|---|---|
| static HIT | **2/20** — VMem, GEN3C |
| NEAR | 2/20 — MagicWorld v1, PlayGen |
| CLEAN | 15/20 |
| SUSPECT-UNTRACED | 1/20 — Matrix-Game 1 |
| **measured under frozen weights** | **0/20** |

Sensitivity: admitting class-level state and public-API config mismatch makes Matrix-Game 1 a third
HIT (3/20). Reported separately; not merged into the main count.

### The two surviving assets are each incomplete, in opposite ways

| | oracle | measured consequence |
|---|---|---|
| **GEN3C** | ✅ public admission invariant: `model_seeded ⇒ usable cache`; structurally a **monotone readiness latch gating a non-monotone clearable resource** | ❌ none |
| **VMem** | ❌ `NO-DEFENSIBLE-ORACLE` | ✅ `nms_on_clean − nms_on(leaked) = +0.245 dB` (sd 0.711, 6/14, 14 windows × 2 seeds, frozen generator) |

**They cannot be paired.** `(oracle, no consequence)` + `(consequence, no oracle)` is not
`(oracle and consequence)`: different consumers, state owners, public contracts and intervention
sequences. The four-tuple must belong to one case. A joint document is legitimate only if clearly
labelled as an audit / worked-example report.

### Scope limits on GEN3C

`server.py:77-84` selects `CosmosModel` only for `model_name ∈ {cosmos, cosmos-predict1}`;
`server_cosmos.py:92-96` builds `Gen3cPersistentModel` only when `gpu_count == 1`.
**The latch defect is in the base class and is config-independent; the released `:208` trigger is
single-GPU-specific.** `MultiGPUInferenceAR` was **not audited**.

## 4. Verified facts worth preserving

- The pinned VMem source **is** the current public release: `runjiali-rl/vmem` HEAD
  `39291e4f...`, `modeling/pipeline.py` SHA-256 `90a45f45...`, byte-identical to three in-repo copies.
- VMem trigger sequence is **move, move, then turn** — not "any move then turn". The NMS-enabled
  branch reassigns when `is_second_step = (len(self.pil_frames) == 5)`.
- `initial_threshold` is never initialised in `__init__` and never cleared by `reset()`.
- GEN3C: `model_seeded = False` occurs **only** in `server_base.py:60`. Nowhere in the codebase is
  it set False again.
- `CosmosBaseModel()` constructs with no arguments — `InferenceModel.__bases__ == ['object']`,
  confirmed dynamically; `@abstractmethod` without `ABCMeta` does not prevent instantiation.
- **Upstream disclosure: nothing found for either project.** VMem and GEN3C both return zero
  issue/PR/commit matches for the relevant terms, independently checked twice.
  **`AGENTS.md` forbids contacting maintainers; no disclosure was made or attempted.**

## 5. Retracted today

| retracted | why |
|---|---|
| CausVid as HIT | its KV cache has no index fields; positions recomputed per call; no stale read |
| constructor-equivalence oracle | "absent from `reset()`" is a signal, not evidence |
| cross-layer near-identical-field oracle | ranks 4th of 7; cannot convict alone |
| successor-implementation-declaration oracle | the added reset governs fields CausVid never had |
| "Choose New Image" oracle | a labelled session control is an auditor's inference, not a stated contract |
| "retrieval-set route is zero-GPU" | constructor loads VMem/VAE/CLIP/CUT3R; all three archival scripts hardcode `device='cuda'` |
| PlayGen as NEAR-to-HIT | key is a per-connection SID; the orphaned entry is unreachable — a memory leak |

**More was retracted than survived.** Each retraction happened while amendment was still
legitimate, or before any external claim was made.

## 6. Experiment E1 — designed, not executed

A pre-declared spec for a zero-GPU GEN3C demonstration was sealed at commit `c97f4f2`
(SHA-256 `080ffc5b...`) **before** any execution. Pre-execution adversarial review then ruled
**do not execute**: the trigger would have been harness-manufactured, P3 observed admission only,
and undeclared preconditions would have failed before the stub was reached.

Disposition: **`DESIGNED_NOT_EXECUTED`**. The sealed spec is preserved unchanged; replacements were
not written back into it.

Permitted label for the static result:
`STATIC_RELEASED_REACHABILITY_PLUS_EXCEPTION_AGNOSTIC_WRAPPER_CONTROL_FLOW`.
**Forbidden labels**, recorded to prevent later drift: `MEASURED_RELEASED_TRIGGER`,
`END_TO_END_RELEASED_FAILURE`, "released `:208` observed", runtime consequence, image quality,
prevalence, published-result impact, new-method validation.

## 7. What this does not support

- **No prevalence claim.** Both error directions pass a single code review; the candidate set is a
  convenience sample; C5 is unmeasured; one reviewer easily writes structural signal as conclusion.
  A prevalence claim would need a pre-registered population, independent two-person per-consumer
  review, explicit stratification, and frozen-weight controls per HIT — and even then only within a
  defined frame.
- **No method contribution**, under the unchanged C6 requirement.
- **No claim about either project's published results.**

## 8. Open items

1. A genuine public relation **R** for VMem — must be supplied and pre-registered by the owner, not
   inferred by the auditor.
2. A frozen-weight consequence for GEN3C — requires GPU authorisation that does not exist.
3. Maintainer confirmation from either project — requires disclosure authorisation that does not exist.

**Until the owner decides C6, the recorded disposition is STOP.**
