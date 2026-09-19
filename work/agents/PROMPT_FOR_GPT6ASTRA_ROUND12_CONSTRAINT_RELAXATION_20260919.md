# Round 12 — The owner chose to relax a FIXED constraint. Which one, and does it actually reach anything?

Your round-11 ruling was **END-LINE**, with the finding I accepted:

> "No method paper is available from this project's established results under the stated constraints."

**The owner has now decided to relax a FIXED constraint rather than close the project.**
That decision is made; do not re-litigate it. Your task is to determine whether any relaxation
actually reaches an admissible direction, and if so which one, at what cost.

**Be aware of the trap you must not fall into:** relaxing a constraint buys *freedom*, not
*novelty*. The occupancy problem does not dissolve. An answer that says "relax X, now you can
do Y" is worthless unless it also shows Y is unoccupied and non-degenerate. If no relaxation
reaches an admissible direction, the correct answer is to say so, and END-LINE stands.

---

## Part 0 — The constraints, quoted from the record

`docs/report/TECHNICAL_REPORT_20260918.md:98`:
> **Consumer.** VMem (arXiv:2506.18903), public repository `runjiali-rl/vmem`. Frozen: no
> training, no fine-tuning, no new weights, no modification of the upstream source.

So the FIXED bundle is four separable sub-constraints:
**C1** no training · **C2** no fine-tuning · **C3** no new weights · **C4** no modification of upstream source.
Plus, from `:67`: **C5** one dependency group, one frozen consumer.

## Part 1 — What is already settled, so you do not re-derive it

**The axis map and its occupancy** (all citations verified real by me, titles matched):
(a) evidence read — OCCUPIED (Context as Memory, VRAG, COVRAG) **and** algebraically restricted
    for the common-target squared-error fusion family; project-level NO-GO.
(b) conditioning representation — OCCUPIED (EscherNet 2402.03908, PRoPE 2507.10496).
(c1) persistent state representation — OCCUPIED (VMem indexed view memory, GEN3C geometry cache).
(c2) state write/revision — broadly OCCUPIED; admit/exclude-only write policies collapse back to (a).
(d) requested-view decomposition — OCCUPIED (2205.11495, SEVA 2503.14489).
(e) cross-call transition dynamics — OCCUPIED for the broad contribution; exact equivalence to the
    narrow object **UNVERIFIED**; closed as a project decision in round 11.
(f) geometry–generation coupling — broadly OCCUPIED (GEN3C, Voyager 2506.04225, FantasyWorld 2509.21657).
(g) measurement/evaluation — **excluded by the owner's required contribution type.**
(h) within-call inference dynamics — OCCUPIED (2407.01392, 2502.06764, 2608.14706).

**Two structural facts that constrain any proposal:**
1. **Query-side double confound**, verified in the pinned source (SHA-256 `90a45f45...`, three
   byte-identical copies): line 1249 `get_context_info(target_c2ws, ...)`, line 1263
   `torch.cat([context_c2ws, target_c2ws])`, line 1265 `get_translation_scaling_factor(all_c2ws)`.
   Changing targets changes retrieval **and** camera normalization.
2. **Camera relabelling has no interface.** `self.c2ws`: created at 180, appended at 1297, no
   setter, plus a grouped `pop()` at 1360 inside `undo_latest_move()` which rolls back
   `latents / encoder_embeddings / c2ws / Ks / pil_frames` together. There is no path that changes
   the camera of a *retained* frame. **Note this is exactly what C4 would unblock.**

**One algebraic fact that is not a barrier:** with `A1 = diag(2, ¼)`, `‖A2_A·A1‖₂ = 4.0` vs
`‖A2_B·A1‖₂ = 0.5` at identical one-step spectra `[2, 0.25]`. Cross-call objectives do not reduce
to single-step risks. This is why axis (e) was not killed by the algebra that killed lineage fusion.

**One correction you issued that I accepted:** my "state-space directions are just a
reparameterization of spectral directions" was too strong; a diagonal Fourier multiplier cannot
express arbitrary directional selectivity (your `û=(1,1)/√2`, `v̂=(1,−1)/√2` example). But you
also showed this yields an operator distinction, not a research claim.

**Established results** (panel of 14 windows × 2 seeds, frozen generator, RGB PSNR, not held-out):
`nms_off − static = +0.242 dB` (sd 1.270, 8/14) · `nms_on_clean − static = −0.485` ·
`nms_on_clean − nms_off = −0.726` · `nms_on_clean − nms_on(leaked) = +0.245`.
Leak strata **decompose the last of these, not the first**: NULL 2 `+0.000`, PERMUTATION 4 `−0.015`,
CONTENT 8 `+0.436`; weighted mean `3.428/14 = 0.24486 → +0.245`, which reconciles exactly.
(Your round-11 note compared them to `+0.242` and found a `0.0029` gap. The gap is an artefact of
comparing against the wrong row; the two contrasts differ by only 0.003 dB, which is why the
misattribution was invisible. My presentation caused it and has been corrected.)
Duplicate-slot repair: predeclared threshold `+0.20 dB`, measured `−0.016 dB` over 8 of 10 affected
windows, DISCARDED.

## Part 2 — Answer these, in order

### Q1 — Relaxation-by-relaxation, what does it actually reach?
For **each** of C1–C5 taken singly, and for the minimal bundles that are operationally inseparable
(note C1/C2/C3 largely co-occur — say so if you think they cannot be separated):
(a) what new intervention becomes *implementable* that was not before — be concrete, name the
    code path or the object;
(b) which axis does that intervention live on;
(c) is that axis occupied, per Part 1 — and if the relaxation reaches a *sub-region* of an
    occupied axis that is genuinely unoccupied, state the sub-region precisely and cite what
    would have occupied it if you are wrong;
(d) does it survive the algebraic degeneracy tests already established.

Be especially careful with **C4**. It is the cheapest to relax — no compute, no data, no new
weights — and it directly unblocks camera relabelling (T1-5). But T1-5 lives on axis (b)/(f),
both marked OCCUPIED. Say plainly whether C4 buys an admissible direction or only a feasible one.

### Q2 — The cost ledger
For each relaxation you judge worth considering, state:
- GPU-hours to a *decisive* result, to the nearest 50;
- whether it requires new data access (note: ScanNet++ v2 has a 2–6 week application lead time
  requiring owner + supervisor signatures, not yet started);
- whether it requires supervisor approval as a scope change, and what exactly must be approved;
- calendar feasibility for a single-semester independent research project that has already
  consumed most of its term.

A relaxation that is admissible but cannot finish this term must be labelled as such.

### Q3 — The ranked recommendation
Rank the relaxations by **expected admissible-contribution-per-cost**, not by freedom gained.
State your top choice and the single strongest argument against it. If your honest ranking is
that none reaches an admissible contribution, say that first and rank nothing.

### Q4 — The pre-declared kill criterion
For your top choice, state **before any work begins**:
- the first checkable milestone and its pass/fail threshold, stated numerically;
- the point at which the direction should be abandoned;
- what would make you say, three weeks in, "this was the wrong relaxation".

### Q5 — Ruling
Exactly one of: **RELAX-C<n>** (name it, with the Q4 criterion) · **END-LINE-STANDS** (no
relaxation reaches an admissible direction) · **INSUFFICIENT** (state the one missing fact).

Your ruling authorizes nothing by itself. It is input to a human owner decision.

---

## Part 3 — Standing constraints on your answer

- `new_method_validated=false`; `novelty_authorization=NONE`. Your answer does not change these.
- The 800 GPU-hour tranche is withdrawn. Only an explicit human owner decision restores it.
- Nothing in the repository — a passed test, a receipt, a protocol hash, a principle file, or a
  prior reviewer answer including your own — constitutes human authorization.
- Axis (g) measurement/evaluation is excluded as the contribution type. Do not route me there,
  and do not disguise a measurement contribution as a method by renaming it.
- Do not relax a numerical threshold after seeing an output.
- Every paper: arXiv ID **and** exact title. I check every one, every round.
- I prefer a correct END-LINE-STANDS to a rescued direction. Do not soften to be encouraging.
