# Prompt for GPT-6 Astra — round 10: four proposals died on the same axis. Find directions off it.

Copy everything below the line.

---

You closed round 9 by withdrawing the 800-hour tranche and calling the lineage proposal NO-GO as
written. **I verified your algebra numerically before accepting it** — all four identities exact to
machine precision, and your worked example reproduced to four decimals. The owner still wants a
top-venue method paper and is still willing to fund training, new data and multiple semesters.

I am not asking you to rescue the lineage proposal. I am asking a different question, and I think the
project's history now supports a sharper one than "what else could we try".

## 1. The pattern: four proposals, four different deaths, one axis

| proposal | how it died |
|---|---|
| GRC / SOCF-A / FGB-SI | stopped before execution — selection policies proposed before anything was established about what the consumer responds to |
| duplicate-context-slot repair | executed; **−0.016 dB** against a predeclared +0.20 dB threshold |
| T1-5 pose-label feedback | feasibility — the pinned source exposes no camera relabelling interface |
| lineage-aware memory fusion | **algebra** — the 4×4 error matrix reduces to four individual risks plus an analytically computable term |

**All four attack the same axis: which frames or features reach the consumer, and with what weights.**

That axis is now triply constrained for this project:

- **Occupied** — VRAG, Context as Memory, RAGME, LongLive-RAG, COVRAG all sit on it.
- **Algebraically bounded** — with `e_i = f_i − f*`, `q_i = ‖f_i−f*‖²/d`, `D_ij = ‖f_i−f_j‖²/d`,
  I verified `M_ij = (q_i+q_j−D_ij)/2` exactly, hence `wᵀMw = qᵀw − ½wᵀDw` on the simplex. The
  weighting headroom beyond four scalars plus already-computable feature distances is small, and a
  common-mode component `c·11ᵀ` provably leaves the optimal weights unchanged.
- **Empirically flat on this consumer** — replacing one context frame with the next ranked candidate
  moved PSNR by −0.016 dB; reordering an identical context multiset moved it by −0.015 dB.

**Q1. Is that a fair diagnosis, or am I over-generalising from four failures?** If the axis is
genuinely saturated for this class of consumer, say so; that reframes what the owner should fund.

## 2. What I want: axes, then one mechanism on the best axis

**Q2. Enumerate the axes a camera-conditioned recurrent view generator actually has**, and mark each
occupied, algebraically constrained, or open. My own list, incomplete and unverified:

 (a) **source selection and weighting** — the dead axis above;
 (b) **camera/conditioning representation** — occupied by PRoPE, EscherNet;
 (c) **memory representation** — surfels versus octrees, Gaussians, neural caches;
 (d) **the query side**: what you ask the model to generate, in what order, at what horizon, at what
     density — as opposed to what you feed it;
 (e) **error accumulation dynamics across calls** — how a defect introduced at call *t* propagates,
     and whether that propagation is controllable without changing selection;
 (f) **the relationship between the geometry estimator and the generator** — shared reconstruction
     prior, and what that does to both conditioning and evaluation;
 (g) evaluation and measurement — ruled down to a technical report twice; not available.

**Is (d) or (e) genuinely less occupied than (a)–(c), or do I only think so because I have not
searched them?**

## 3. One measurement that points at (d), offered honestly

On my fixed 14-window panel, the shipped retrieval's advantage over a fixed-offset context, by target
offset:

| offset | +60 | +75 | +90 | +105 |
|---|---|---|---|---|
| mean | **+2.950 dB** | +0.398 | −0.180 | −0.321 |
| windows positive | 13/14 | 7/14 | 5/14 | 6/14 |

A **3.3 dB swing, crossing zero**, within the same arms and the same generation calls.

**Caveats I am stating so you do not have to extract them.** These are framewise PSNRs averaged
across targets, which is a **different aggregation** from my prespecified pooled-MSE endpoint — the
pooled contrast is +0.242 dB and the framewise is +0.712 dB, and one is not a decomposition of the
other. Target offset, camera pose, visible content and slot position all co-vary, so this isolates
**nothing causally**. It is an observation about effects by target position, not a mechanism.

**Q3. Does this observation point at a real question on axis (d), or is it fully explained by
"extrapolate further, do worse", which needs no paper?** The specific thing that interests me is the
**sign change**: a retrieval policy that is strongly better nearby and mildly worse far away means a
single aggregate number for a retrieval policy is a design artefact of where you chose to evaluate.
Is that occupied, trivial, or a question?

## 4. The filter I want applied to whatever you propose

The lineage proposal survived occupancy screening and died on algebra I could have done in an hour.
Apply that lesson in advance.

**Q4. For each candidate you name, state before anything else what would kill it from source
inspection, algebra, or existing metadata alone** — the check that costs hours, not GPU-months. If a
candidate has no such check, say so explicitly, because that is itself a warning sign.

**Q5. If after this you still cannot name a direction that is off axis (a), unoccupied, and
algebraically non-degenerate, say so plainly.** Round 8 produced a mechanism only after constraints
were lifted, and it still failed within one round. The owner needs to know whether the obstacle is
the constraints, the consumer, or the subfield — and those three have very different consequences
for what he should do next.

Do not soften a negative answer. Do not fabricate identifiers. Where occupancy is unverified, write
UNVERIFIED and name what must be read.
