# Prompt for GPT-6 Astra — round 2: the direction collapsed, and a different result emerged

Copy everything below the line.

---

You reviewed this project earlier today and ruled: kill the gauge direction, kill SOCF-A and
FGB-SI, stop treating the withdrawn -0.729 dB as a memory result, and aim at a bounded
evaluation case study. I acted on all of it. Then checking your two static claims produced a
different situation than either of us described, and I need you to attack the new one.

I will state what I verified, what it destroyed, and what replaced it. **Attack first.** If the
honest answer is that there is no research contribution left here, say so plainly; a negative
answer is worth more to me than encouragement.

## Part 1 — your static claim was right, and it killed my strongest direction

You said slot 0 is selected before the NMS threshold applies. Verified in the pinned source
(`pipeline.py`, sha256 `90a45f45...`, lines 709-716): `selected_indices.append(sorted_frames[0])`
executes unconditionally before the threshold loop, and `sorted_frames` never reads
`initial_threshold`. Measured across all 14 windows of the panel: **slot 0 identical under clean
and leaked thresholds in 14/14**. Since `get_plucker_coordinates` takes its reference from
`extrinsics_src=all_w2cs[:1]`, the leak provably cannot move the ray reference frame.

**My "M5 x M3 via slot-0" proposal is dead.** I am not asking you to revisit it.

## Part 2 — checking your attribution warning produced a stronger correction against me

You warned that an incomplete `reset()` does not establish that native execution is
contaminated. Following that produced something neither of us had:

`app.py` constructs `Navigator(MODEL, ...)`; `navigation.py` is the only path into generation;
**both of its call sites pass `use_non_maximum_suppression=False`** (lines 187 and 236). The
config declares `use_non_maximum_suppression: true`. There is exactly one internal caller of
`get_context_info`.

Consequences I have accepted and written into the record:

1. The leak is **not** a defect of native inference. Under a single setting the disabled branch
   rewrites `1e8` on every call, so nothing stale is ever consumed. The leak requires running two
   settings on one pipeline object — my comparative harness. I will not claim the published
   results are contaminated.
2. **NMS-on is not the method as shipped.** The shipped path is NMS-off. My earlier framing was
   wrong.
3. The config's declared default retrieval setting is unreachable through the released interface.

## Part 3 — what this salvaged, at zero additional cost

If the disabled branch is independent of the leaked attribute, the sealed comparison involving it
was never contaminated. I did not assume this. I forced `initial_threshold` to the primed
percentile, to 1e8, to 1e-9, to 0.0, and deleted it, then required the selection to be unchanged:
**6/6 windows invariant**. (Deleting it does not even raise, because the disabled branch assigns
`1e8` before reading it — which is simultaneously why it is immune and why it is the leak source.)
The third arm builds its context from fixed offsets and never calls retrieval at all.

So this contrast stood already, sealed, untouched. I also found my own aggregation error: the
sealed scorer reported `n_pairs = 28`, which is 14 windows x 2 seeds, treating controlled
stochastic replications as independent units.

**Shipped surfel-indexed retrieval minus fixed-offset context, window-level:
+0.242 dB, sd 1.270, SE 0.340, 8/14 windows positive.**

Per-window (dB): +2.055, +1.038, +0.505, -1.571, +0.548, -0.131, -0.348, +0.265, +1.652, +1.974,
+0.978, -0.404, -1.102, -2.073.

The comparison is generous to retrieval: the retrieval bank reaches offset +55 while the
fixed-offset arm may use only up to +45, so retrieval may draw on frames strictly closer to the
targets at +60..+105. It still does not win.

## Part 4 — a mechanical account, visible in metadata before any score

Distinct frames actually delivered into the four context slots:

| arm | 3 distinct | 4 distinct |
|---|---|---|
| fixed-offset | 0 windows | 14 |
| shipped retrieval | **10** | 4 |
| leaked NMS-on | 1 | 13 |

Cause, in the pinned source: the disabled selection is seeded with `sorted_frames[0]`
(surfel-nearest) and then `len(self.c2ws) - 1` (most recent). Under forward extrapolation —
targets at +60..+105 beyond a bank ending at +55 — the nearest candidate **is** the most recent
frame. The two seeds collide, and the fill step cannot recover the slot because the duplicate
already counts toward `len(selected_indices)`.

Post-hoc stratification of the sealed windows: +1.124 dB (n=4) where four distinct frames were
delivered, -0.111 dB (n=10) where three were. **I am not treating this as a finding.** It is a
post-hoc split on a non-randomised variable with four windows on one side.

## Part 5 — what is running, and the predeclared rule

I corrected your budget. You costed the state question at 84-88 generations assuming the leaked
and recency arms would be regenerated. They do not need to be: an independent rebuild reproduced
the sealed leaked selections frame-for-frame, and the disabled arm is threshold-independent. Only
the clean arm was missing: **28 generations**, running now.

A zero-diffusion census classified every window by what the leak actually changed, before any
score existed: **NULL 2, PERMUTATION 4, CONTENT 8.** NULL windows are a built-in validity gate —
identical consumer input means the outputs must be byte-identical, or my reuse of sealed outputs
is inadmissible and I will report it as such. PERMUTATION windows hold the multiset, cameras,
intrinsics, normalisation input and slot-0 gauge all fixed, so any difference there is a pure
slot-order effect with no injected scale and no reference override.

Second experiment, decision rule fixed before outputs exist: deduplicate the pipeline's own
selection and let freed slots be filled from its own distance-ranked candidate list. No training,
no weight change, no new ranking or selection criterion. The ranking is read out of the pipeline
rather than re-implemented, by requesting a longer selection with the query centre held fixed and
requiring the first four indices to match the normal call. **Retain the duplication explanation
only if the repaired arm gains >= 0.20 dB over the affected windows AND every unaffected window
reproduces byte-identically.** Below that, the explanation is discarded and the negative result
stands with no mechanical account.

## What I need from you

**Q1. Is the negative result the contribution, or is it a null that reviewers will read as an
unconvincing reproduction?** The claim would be: on a held-out panel, a published geometry-indexed
retrieval memory does not outperform a fixed-offset context, under a comparison biased in its
favour, with a specific mechanical reason why it cannot. Tell me the strongest reviewer objection
and whether it is fatal. Include the possibility that 14 windows on 2 sequences simply cannot
support a negative claim regardless of how clean the controls are.

**Q2. Search specifically for prior work that already reports retrieval or memory selection in
video/view generation failing to beat a naive recency or fixed-offset context, and for any work
reporting degenerate context-slot utilisation in a retrieval-augmented generator.** Not "memory
helps" papers — I need the negative and the degeneracy literature. If this is occupied, say so and
kill it. A negative answer is the most valuable thing you can give me.

**Q3. Is the slot-duplication account a real mechanism or a confound?** The repaired arm changes
which images enter the consumer, so a gain could be "more distinct information" rather than
"duplication was harmful." Name the control that separates those two, within a frozen consumer, no
training, and tell me if no such control exists.

**Q4. If the duplication test comes back below 0.20 dB, what is left?** I would then have a clean
negative result with no mechanism. Is that publishable at workshop level, or is it a technical
report? Do not soften this.

**Q5. What should I stop doing now?** Name the specific work in Parts 3-5 that I should abandon.
I would rather cut a live direction than spend three weeks on something you can see is dead.

Constraints that do not move: frozen consumer, no training or fine-tuning, no new weights, no new
dataset downloads, two exposed development sequences, one dependency group, PSNR on RGB only.
Windows are a finite panel, not a sample from a population. Do not propose anything requiring
training, new data, or a human study.
