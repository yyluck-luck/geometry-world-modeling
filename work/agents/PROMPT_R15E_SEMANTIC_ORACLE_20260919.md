# Round 15-E — The semantic oracle: how do you prove a field *ought* to have been cleared?

This is the pivotal problem. A prior round raised it as the strongest structural objection and I
accepted it:

> Without an explicit reset/initialize contract, "this field was not cleared" does **not**
> automatically mean defect — it may be intentional persistence. The audit must show the field
> *ought* to be cleared under the public lifecycle semantics, not merely that it is absent from
> some function body.

Without a defensible oracle the whole audit degenerates into style checking. **Solve this, or
establish that it cannot be solved.**

## The two verified instances the oracle must adjudicate

**Instance 1 — VMem** (`runjiali-rl/vmem`, HEAD `39291e4f...`, `modeling/pipeline.py` SHA-256
`90a45f45...`): `self.initial_threshold` written unconditionally at `:704-705` on the NMS-disabled
path; the NMS-enabled path writes only when `is_second_step = len(self.pil_frames)==5` (`:674`);
read unconditionally at `:708`; `reset()` (`:135-146`) clears 11+ list fields and `global_step`
but not this one; the attribute is **never initialised in `__init__`**.

**Instance 2 — GEN3C** (`nv-tlabs/GEN3C`, HEAD `db2ffe12...`, CVPR 2025 Highlight):
`gui/api/server_cosmos_base.py:46-71` — `seed_model` clears the 3D cache and pose/intrinsics
history at `:53-55`, then calls `seeding_method(...)` at `:62-70` which **can raise**
(`cosmos_predict1/diffusion/inference/gen3c_persistent.py:208`), and only then sets
`self.model_seeded = True` at `:71`. `server.py` catches and returns HTTP 400, so the process
survives with a cleared cache and a stale `True` flag; `/request-inference` admits on
`server_base.py:122`.
**Crucially:** `gen3c_persistent.py:551-553` `clear_cache()` sets the *model's own*
`self.model_was_seeded = False`. So the codebase clears the seeding flag at one layer and not at
the other, for near-identically named fields.

## The candidate oracle I want you to stress-test, then improve or refute

**"Internal inconsistency as evidence of intent."** The GEN3C case suggests an oracle that needs
no author input and no external specification: *the codebase itself declares the intended
lifecycle semantics at one layer and violates them at another.* `model_was_seeded` being cleared
in `clear_cache()` is direct evidence that the authors regard seeding state as session-scoped;
the un-cleared `model_seeded` at the outer layer is therefore a defect **by the project's own
declared semantics**, not by my preference.

Attack this. Specifically:
1. Does it generalise, or does it only work when a *duplicate* of the field happens to exist at
   another layer? If it only works for duplicates, what is its coverage — and does VMem's
   `initial_threshold` have any such sibling, or does Instance 1 fail this oracle entirely?
2. What is the false-positive mode — a case where two layers legitimately differ in lifecycle?
3. Is "cleared in the same reset method as its peers" a weaker but broader variant? VMem's
   `reset()` clears 11+ fields; `initial_threshold` is the odd one out. Is "peer-group
   non-uniformity" a defensible oracle, or is it exactly the style-checking the objection warns
   about?

## Other oracle families you must survey, with citations

- **Specification / invariant inference from code and executions** — Daikon-style dynamic
  invariant detection, likely-invariant mining, API protocol/typestate inference, object usage
  model mining. Do any of these already provide "this field belongs to the reset set"?
- **Documentation- and comment-derived contracts** — inferring intended behaviour from docstrings,
  README lifecycle descriptions, type annotations. How reliable is this in practice per published
  evaluations?
- **Differential and metamorphic oracles** — e.g. "same public call sequence, different
  interleaving, output must be identical". Does a metamorphic relation sidestep the intent
  question entirely by making the *user-visible contract* the oracle rather than the field?
- **Test-pollution / order-dependence detection oracles** — what do PolDet, PRADET, ODRepair, NIO
  actually use as their oracle, and can that oracle be transplanted here? This matters because
  the same objection says my work is a cross-domain rename of theirs; if their oracle transfers
  cleanly, that strengthens the rename objection. **Report that honestly if true.**

## Questions

**Q1 — Is there a defensible oracle for Instance 1 and Instance 2?** Answer per instance. It is a
legitimate outcome that GEN3C has one and VMem does not.

**Q2 — Rank the oracle families** by defensibility for this setting, and state the single best
one with its precise statement.

**Q3 — Does the metamorphic route dissolve the problem?** If the claim becomes "the documented
public API admits two call sequences that a user would regard as equivalent, and they produce
different results," then intent about any internal field never has to be established. State
whether this is (a) sound, (b) already occupied, and (c) applicable to both instances.

**Q4 — If no defensible oracle exists,** say so plainly and first. That result would close this
direction and I would rather have it now than after two weeks of auditing.

## Output
Write to exactly one new file: `work/agents/CODEX_R15E_SEMANTIC_ORACLE_20260919.md`.
Do not modify any existing file. No GPU, no training, no generation.
Every source: arXiv ID / DOI / venue **and** exact title. I check every one.
Mark unverified items UNVERIFIED. A correct negative beats an encouraging answer.
