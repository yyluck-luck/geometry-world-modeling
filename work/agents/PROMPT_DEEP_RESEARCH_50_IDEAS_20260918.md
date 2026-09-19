# Deep-research brief: 50+ top-venue innovation candidates for a frozen view-generation consumer

Copy everything below the line into a deep-research / parallel-agent system.

---

# ROLE

You are a research ideation team for a graduate independent research project that must produce a
top-venue paper (CVPR / ICCV / ECCV / NeurIPS / ICML / ICLR). Run **parallel specialist tracks**,
then consolidate once.

**Deliver at least 50 distinct candidates**, every one carrying the mandatory fields in the schema
below. A candidate without those fields does not count toward the 50.

---

# 1. THE SITUATION, STATED WITHOUT SPIN

The project studies **VMem** (arXiv:2506.18903), a surfel-indexed camera-conditioned autoregressive
view generator. The consumer is **pinned and frozen**: no training, no fine-tuning, no weight
changes have occurred.

**What has already been done and closed.** A full audit of context selection produced a completed
negative-direction result: a duplicate-context-slot repair, prespecified at +0.20 dB retention
threshold, measured **−0.016 dB** and was discarded by its own rule. A bounded search for a
replacement question returned **zero survivors**, and that was ratified by two independent review
rounds. The project has a finalized technical report and a closed branch.

**Therefore: do not re-propose anything in the closed list in §3. The value you add is entirely in
directions that are not there.**

## Assets that already exist and are real

These are reusable and should be treated as leverage, not as achievements:

- A byte-reproducible generation and scoring pipeline with sealed predictions, hash-verified
  receipts, and byte-identity gates that have passed (28/28 historical linkage; NULL-stratum and
  no-op controls exactly identical).
- **Three validated evaluators. Only one has ever been used.** RGB PSNR was used for every result.
  A cross-view reprojection geometry evaluator (uses only sensor depth and dataset poses, estimates
  nothing from predictions, CPU-only) and a CameraCtrl-protocol pose evaluator (Rdist/Tdist, needs a
  geometry model to extract poses from generated frames) were built, unit-tested, and **never run on
  any output**.
- 116+ sealed generations across four context-policy arms on a fixed 14-window panel.
- A characterized consumer: the exact call graph, the retrieval selection logic, the camera
  normalization path, the joint 8-frame denoising interface (4 context + 4 target), and a verified
  provenance discrepancy in the released demo.

---

# 2. CONSTRAINTS — mark every candidate against these

**FIXED, cannot be relaxed.** No new architecture. No modification of the upstream consumer source.
No human-subject study. Any result on the two existing sequences is a finite panel with one
dependency group, so no population claim is available from them alone.

**RELAXABLE with explicit prior approval** — and you must state which relaxations a candidate needs:

| lever | currently | relaxable to |
|---|---|---|
| training | forbidden | fine-tuning, adapters, a trained selector, a learned probe |
| data | 2 exposed development sequences | new sequences with prospective metadata qualification |
| evaluator | RGB PSNR only used | two built-but-unused evaluators; new metrics need justification |
| generation budget | ~few hundred forwards | larger, with justification |
| consumer | one frozen model | additional public frozen models, for cross-model claims |

A candidate needing **no** relaxation is rare and especially valuable. A candidate needing training
plus new data plus a new metric is probably a different project — say so rather than hiding it.

---

# 3. OCCUPIED — verified at primary source. Do not re-propose.

Each was read in full, not by abstract. Re-proposing any of these wastes a slot.

| claim | occupied by | the exact verified content |
|---|---|---|
| historical retrieval need not beat recent-window conditioning | VRAG, arXiv:2505.21996v4 | *"The History Buffer method performs poorly, with an SSIM score of 0.188, indicating that naive historical frame retrieval without effective in-context training fails to maintain long-term consistency."* |
| a bounded context budget is wasted on redundant/adjacent frames; diversity helps | Context as Memory, arXiv:2506.03141 | selection ablation: Random 17.70/17.07, FOV+Random 19.17/17.47, FOV+Non-adj **20.11/18.19** |
| deduplicating near-duplicate retrieved content | RAGME, arXiv:2504.06672 | named deduplication stage in retrieval-augmented video generation |
| retrieval collapses toward temporally local neighbours | LongLive-RAG, arXiv:2606.02553 | a loss that suppresses redundant local similarity |
| finer geometric evidence does not guarantee better independent selection | COVRAG, arXiv:2606.02479 | **lower is better.** FoV+Indep **0.141**/0.198 is *better* than the finer target-view-coverage+Indep **0.149**/0.210; residual selection recovers 0.100/0.156 |
| camera-conditioning reference-frame / gauge sensitivity | PRoPE, arXiv:2507.10496; EscherNet, arXiv:2402.03908 | *"sensitive to the arbitrary choice of reference frame, which can hinder generalization"* |
| evaluation state, episodic vs accumulated adaptation | TTAB, arXiv:2306.03536 (ICML 2023) | episodic vs online state accumulation distinction |

**Also closed internally, do not revive:** duplicate-context-slot repair; slot-0 ray-gauge routes
(proven impossible in source); state-leak-as-contribution; source-conflict / future-geometry
selection scoring (SOCF-A, FGB-SI, GRC — all stopped or blocked before or during execution).

**Note the pattern and use it.** Every occupying work above is a **trained** method. If you believe
an untrained lane remains open, say why explicitly. If you believe the untrained lane is closed in
2026, say that too — it is a useful answer.

---

# 4. PARALLEL TRACKS — run these as separate agents, minimum ideas each

Do not let one track's framing leak into another. Diversity across tracks is the point.

| track | mandate | min ideas |
|---|---|---|
| **T1 Mechanism** | Inside the consumer: conditioning interface, camera encoding, memory representation, joint denoising coupling, autoregressive state. What is architecturally true of this class that nobody has exploited? | 10 |
| **T2 Measurement** | What is systematically mismeasured in this subfield? Protocol, endpoint, aggregation, leakage, comparability. What would a rigorous measurement contribution look like? | 8 |
| **T3 Data / benchmark** | What data or benchmark gap blocks progress? What would a new evaluation resource establish that existing ones cannot? | 8 |
| **T4 Cross-field transfer** | What is standard in LLM long-context memory, RL world models, SLAM / SfM, information retrieval, or streaming systems that has **not** crossed into camera-conditioned view generation — and would be non-trivial here? | 10 |
| **T5 Failure modes** | What breaks in these systems that nobody has characterized? Drift, collapse, forgetting, state hazards, degeneracy, compounding error. | 8 |
| **T6 Analysis / theory** | What can be proven, bounded or characterized **without training** — identifiability, invariance, information limits, capacity of a fixed context budget? | 6 |

---

# 5. MANDATORY SCHEMA — every candidate, no exceptions

```
ID:               T<track>-<n>
One-line claim:   the finding a paper would assert, not the topic
Mechanism:        why it would be true, at the level of the actual computation
Nearest prior work: real arXiv ID or venue+year, with the specific passage or number that makes it near
Occupancy verdict: OCCUPIED / ADJACENT / OPEN
Verification:     VERIFIED (I read the method/experiments) | ABSTRACT-ONLY | UNVERIFIED
Relaxations needed: training? new data? new evaluator? extra budget? extra models?
Smallest decisive experiment: one experiment, with arms
What must be true: the assumption that, if false, kills it
Kill criterion:   the result that would end it
Venue fit:        which venue and why
Cost:             rough generation / compute / human effort
```

## Hard rules

1. **Never invent an arXiv ID, title, author or number.** If you cannot verify, write `UNVERIFIED`
   and say what you would need to check. A fabricated citation invalidates the whole candidate and
   is worse than an empty field.
2. **Abstract-only reading is never an occupancy verdict.** Mark it `ABSTRACT-ONLY`.
3. **A trained critic in text-RAG does not automatically occupy an untrained visual mechanism**, and
   **porting a standard selector into this consumer is not automatically novel.** Argue the specific
   case both ways.
4. No two candidates may share the same mechanism with different wording. Merge duplicates before
   submitting; a merged pair counts as one.
5. If a track cannot reach its minimum without padding, **report the shortfall** rather than filling
   it. An honest 42 beats a padded 50.

---

# 6. CONSOLIDATION — one pass, after the tracks report

1. **Full table** of all candidates with the schema fields.
2. **Partition by relaxation**: (a) works under current constraints; (b) needs one relaxation;
   (c) needs two or more. State the count in each.
3. **Ranked shortlist of 5**, ordered by (expected contribution) / (cost and risk). For each, give
   the strongest reviewer objection you can construct and whether it is fatal.
4. **The honest ceiling**: for the top candidate, what venue is realistic for a one-semester
   independent project with one frozen consumer, and what would it take to exceed that?
5. **The kill list**: which of your own 50 you would discard first, and why. Be specific.
6. **If your honest conclusion is that none of the 50 supports a top-venue paper under any single
   relaxation, say so explicitly.** That is a permitted and valuable answer, and it will be acted on
   rather than argued with.

---

# 7. WHAT NOT TO DO

Do not produce a topic list — "explore memory efficiency", "study long-horizon consistency" are not
candidates. Do not restate the occupied claims in §3 with new vocabulary. Do not propose anything
requiring a human-subject study or a new architecture. Do not soften a negative assessment to
produce a longer list. Do not claim novelty for moving a known method between domains without
arguing what breaks in the move.

**The deliverable is 50+ checkable candidates and one ranked shortlist, not 50 sentences.**
