# Adversarial design review request

You are acting as a skeptical senior reviewer for a single-student CVPR/ICCV-track
project. Your job is to attack the proposed next experiment, not to encourage it.
Prefer "this does not change any decision, drop it" over polite improvement
suggestions. Answer in English.

## What the project is

Geometry-aware world modeling. The pinned consumer is VMem (arXiv 2506.18903),
a camera-conditioned autoregressive view generator with surfel-indexed view
memory. Frozen weights. No training is performed and none is planned.

Compute is not the constraint: an H800 is available and one generation of four
576x576 target frames at 50 steps costs about one minute.

## What has actually been measured (all development scope, exposed data)

All numbers below come from 423 sealed generations on RGB-D Scenes v2
(scene_13, scene_14), 2 scenes x up to 16 windows x arms x 2 seeds, scored with
a frozen RGB metric. Replay is byte-identical across same-seed repeats and even
across nodes, so differences are not sampling noise.

1. **Memory gives no measurable benefit.** With both arms receiving *identical*
   real history frames, and the only difference being whether VMem's surfel
   memory + `get_context_info` selects the context versus a fixed recency
   heuristic:
   - RGB: memory - recency = **+0.032 dB**, sd 1.285, n=16 pairs, 9/16 positive
   - With NMS on (the pinned config value): **-0.729 dB**, 9/28 positive
   - Contrast-normalized cross-view reprojection consistency: NMS-on is worse by
     +0.111 (about 4.1 SE, 5/28); NMS-off is within noise (1.4 SE, 12/28)

2. **Context *content* matters a lot, ~2 dB.** Giving the generator the four
   earliest frames instead of the four most recent costs about 2.3 dB, robust
   across 2 scenes, 16 windows, 2 seeds (4/32 positive).

3. **Collapsing 4 unique context frames to 1 costs ~2.2 dB** (3/32 positive),
   but 4 unique to 2 unique is indistinguishable from noise (15/32). So it is a
   collapse cliff, not a graded multiplicity effect.

4. **The first context slot is a gauge.** `get_cond` calls
   `get_plucker_coordinates(extrinsics_src=all_w2cs[:1], ...)`, so the first
   context camera defines the ray reference frame. Same multiset, different
   slot-0 frame, shifts PSNR by 0.55-0.87 dB in a single window; at scale the
   effect shrinks to -0.318 dB with inconsistent sign.

## The experiment that just failed, and why

A preregistered revisit diagnostic on TUM `fr1_room` was designed to test the
leading competing explanation for finding (1): that the earlier test sequences
simply contained no leave-and-return, so memory had nothing to contribute.

Revisit windows were defined by pose proximity: exists i < j with translation
< 0.30 m, geodesic rotation < 20 deg, and j - i > 150 frames. A minimum of three
independent leave-and-return episodes was required, declared before any data
contact.

The metadata feasibility gate returned **UNTESTABLE** (two episodes, and every
revisit and control window collapsed into a single dependency group). Zero
generation budget was spent.

A cheap diagnostic then produced the finding that motivates this request:

| frame bucket | frames with translation < 0.30 m | also rotation < 20 deg |
|---|---|---|
| 150-349 | 0 | 0 |
| 350-449 | 36 | **0** |
| 750-849 | 71 | **0** |
| 850-949 | 77 | **0** |
| 950-1049 | 73 | 41 |
| 1050+ | 88-100 | 81-83 |

The camera returns to earlier *positions* from frame ~350 onward, but every one
of those is rejected by the *rotation* criterion until ~950. Same place, different
viewing direction.

## The proposed next step you must attack

**Claim being made:** pose proximity is the wrong window-eligibility criterion,
and using it may be why the revisit test is untestable and why finding (1) may be
uninformative.

**Proposed measurement, zero generation:** for every candidate window, compute
the *residual coverage gain* of older history over the recency context. Warp the
target view's sensor depth into each history frame, count target pixels that are
covered by at least one older history frame but by no recency frame, and report
that fraction. Select windows by residual coverage gain instead of pose
proximity.

This quantity is taken from published work, not invented here: COVRAG
(arXiv 2606.02479) defines target-view coverage maps and selects frames by
maximizing residual coverage gain, and explicitly states that pose or
field-of-view overlap is "too coarse to reason about pixel-wise visibility."
AnchorWeave (arXiv 2602.14941) uses coverage-driven local memory retrieval.

**Intended framing:** not a new retrieval method. The published coverage quantity
is used as an *experiment-eligibility measure*, to identify windows in which any
retriever could possibly help, before spending generation budget.

**Declared decision rule:**
- residual coverage gain approximately zero in all available windows
  -> finding (1) is a property of the available data, not of the method; stop
  claiming anything about retrieval and redirect the project
- substantial residual gain exists in some windows, and pose proximity does not
  select them -> the earlier window selection was mis-specified; rerun the memory
  versus recency contrast on coverage-selected windows

## What to attack

1. **Decision value.** Does either outcome actually change the next action, or
   would the project do the same thing regardless? If the latter, say drop it.

2. **Circularity.** Coverage is computed with depth and pose. VMem's retrieval
   is itself geometric. Does selecting windows by coverage gain guarantee that a
   geometric retriever wins there, making the follow-up experiment vacuous? If so,
   what is the correct control?

3. **Is the negative result already explained more simply?** Finding (4) says the
   first context slot sets the ray gauge. Retrieval changes which frame lands in
   slot 0. Could findings (1) and (4) be the same phenomenon, so that the whole
   revisit line is chasing an artifact?

4. **Prior art discrimination.** Given COVRAG and AnchorWeave, is there any
   defensible residual contribution in using coverage as an eligibility measure
   rather than a retrieval rule? Name the closest prior work that already does
   the eligibility use, if it exists. A negative answer is useful.

5. **Small-N inference.** Realistically there will be fewer than 10 usable
   windows and at most 3 weakly independent episodes, all from one trajectory.
   State plainly what can and cannot be concluded from that, and whether any
   design at this scale can support a publishable claim, or whether the honest
   output is a measurement report with an explicit non-result.

6. **The strongest alternative use of one H800 week.** Given findings (1)-(4),
   name the single experiment you would run instead, and say why it beats this
   one. You may propose abandoning the memory-benefit question entirely.

## Constraints on your answer

- Do not propose training, fine-tuning, or new model development.
- Do not propose a broad benchmark, a survey, or additional auditing.
- Prefer one decisive experiment over a program.
- If your recommendation is "the honest output here is a negative-result
  measurement paper, not a method paper", say so directly.
- Cite specific papers where they change the judgement; do not pad with
  citations.
