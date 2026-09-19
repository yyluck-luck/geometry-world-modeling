# Round 15-G — Can condition 5 be demonstrated without GPU and without model weights?

This is a **feasibility and design question**, not a novelty review.

## The constraint that currently blocks the project

A prior round concluded: zero GPU closes the static breadth gap (conditions 1–4), but
**condition 5 — a measured behavioural consequence under frozen weights — still needs runs**, and
reviewers would treat a static-only cross-system table as code-risk evidence rather than
demonstrated external validity. The project has no authorised GPU tranche and a mostly-consumed
term, so this is the binding practical constraint.

## The idea I want you to test seriously, then accept or refute

The two verified HITs have **different consequence types**:

- **VMem**: stale `initial_threshold` → a *subtle change in retrieval behaviour* → different
  generated frames. Demonstrating this plausibly needs the real model. We already measured
  `+0.245 dB` (clean vs leaked) on our own 14-window panel with the real frozen generator.
- **GEN3C**: stale `self.model_seeded` flag → *an invalid state is admitted*. The server clears
  the 3D cache at `gui/api/server_cosmos_base.py:53-55`, `seeding_method(...)` raises at
  `cosmos_predict1/diffusion/inference/gen3c_persistent.py:208`, `server.py` returns HTTP 400,
  and `/request-inference` then admits the request at `gui/api/server_base.py:122` because the
  flag was never reset — while `clear_cache()` at `gen3c_persistent.py:551-553` *did* reset the
  model's own `model_was_seeded`.

**Hypothesis:** the GEN3C-class consequence is demonstrable with a *stub model* — no weights, no
GPU, CPU only. If the server's control flow admits a request against a cleared cache, that is an
observable, reproducible behavioural fact about the released code, independent of what the
network would have generated.

Test this hypothesis properly:
- Is the GEN3C server layer separable from the model such that a stub satisfying its interface can
  be injected **without modifying the released source**? Identify the exact seam (class, import,
  factory, config) and say whether injection requires a patch. **A demonstration that requires
  editing the released code is much weaker — say so if that is the case.**
- What exactly would the stub demonstration establish, and what would it *not*? Be precise: it
  shows a reachable inconsistent-state admission, not an image-quality consequence.
- Would a reviewer accept a stub-based demonstration as condition 5, or reject it as "you only
  showed the code path executes"? Look for published precedent where a defect's consequence was
  demonstrated with mocks/stubs rather than the full system, and cite it.

## Also evaluate these cheaper-than-full-GPU routes

1. **Smallest real checkpoint.** For either HIT, is there a released small/distilled variant that
   runs on one consumer GPU or CPU? Give VRAM, licence, and rough runtime.
2. **Deterministic replay.** Can the VMem consequence be shown by *recording* retrieval decisions
   (which frame indices are selected) rather than generating pixels? Selection indices are a
   discrete, cheap-to-compute output; the generator need not run at all. Does the project's
   existing zero-diffusion census already constitute this, and would a reviewer accept
   "the retrieval set differs" as a behavioural consequence without pixels?
3. **CPU-only inference.** Is CPU inference feasible for any HIT at reduced resolution/frames,
   and what would one decisive sequence cost in wall-clock hours?

## Questions

**Q1 — Can condition 5 be met with zero GPU for GEN3C?** Yes/no, with the seam identified and the
strength of the resulting evidence stated honestly.

**Q2 — Can it be met for VMem without generating pixels?** Specifically assess the
"retrieval-set-differs" route and the existing zero-diffusion census as evidence.

**Q3 — The minimum viable evidence package** that a reviewer would accept for a cross-system
behavioural claim, and its true cost in GPU-hours (0 is an allowed answer) and wall-clock days.

**Q4 — If the honest answer is that condition 5 cannot be met without GPU,** say so first and
plainly, and state the minimum GPU-hours for the cheapest decisive demonstration.

## Output
Write to exactly one new file: `work/agents/CODEX_R15G_CONDITION5_ROUTES_20260919.md`.
Do not modify any existing file. **Do not run any model, do not download weights, do not execute
the GEN3C server.** This round is analysis and design only.
Every source: arXiv ID / DOI / URL and exact title. Every code claim: repository, commit, path, lines.
