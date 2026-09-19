# The sealed contrast that the leak could not touch (2026-09-18)

> **CORRECTION NOTICE, appended 2026-09-18 after external review.**
> This file **overstated the result in the negative direction** and its inferential statistics
> are withdrawn. The measured finite-panel mean of shipped retrieval against fixed-offset
> context is **+0.242 dB, which is POSITIVE**. Wording in this file such as "is not
> distinguishable from", "does not beat", "still does not win", or "a bounded negative result"
> is **wrong** and is retracted. The standard error and t statistic are also withdrawn: windows
> were declared a finite panel, so dividing the window-level SD by sqrt(14) is not a defensible
> sampling standard error. The SD is retained as a description of heterogeneity only.
> The word "held-out" is narrowed: these are **exposed development sequences** whose target
> frames are held out from conditioning, not independent held-out evaluation data.
> The file is preserved unedited below as the superseded record.
> Authoritative version: `docs/RETRIEVAL_ARMS_RESULT_20260918.md`.


Status: `MEASURED_DEVELOPMENT_RESULT`. `new_method_validated=false`,
`novelty_authorization=NONE`. Exposed development sequences; no human approval implied.

## 1. Why this contrast survives the contamination finding

The `initial_threshold` leak contaminated the NMS-**enabled** arm only. Two of the three
sealed S111 arms cannot be affected:

- `static` builds its context from fixed offsets `[0, 15, 30, 45]` and never calls
  `get_context_info`.
- `memory_nms_off` reads `self.initial_threshold` into `current_threshold`, but the only
  consumer of that variable is a `while` loop guarded by `and use_non_maximum_suppression`,
  which is False. Code reading is not measurement, so this is being verified empirically by
  `nms_off_threshold_independence.py` (job 595625), which forces the attribute to the primed
  percentile, to 1e8, to 1e-9 and to 0.0 and requires the selection to be unchanged.

Subject to that check, the `memory_nms_off` vs `static` contrast from sealed job 594957
stands without regenerating anything.

## 2. Correction to my own aggregation

The sealed scorer reported this contrast with `n_pairs = 28`. That is 14 windows x 2 seeds.
Seeds are controlled stochastic replications within a window, not independent scenes, so 28
overstates precision. Averaging the two seeds within each window first:

| aggregation | mean | sd | SE | t | positive |
|---|---|---|---|---|---|
| seed-level (as sealed, overstated) | +0.242 dB | 1.417 | 0.268 | 0.90 | 17/28 |
| **window-level (correct)** | **+0.242 dB** | **1.270** | **0.340** | **0.71** | **8/14** |

Per-window paired differences (`memory_nms_off` minus `static`, dB):

```
scene_13  w050 +2.055   w100 +1.038   w150 +0.505   w200 -1.571
          w250 +0.548   w300 -0.131   w350 -0.348
scene_14  w050 +0.265   w100 +1.652   w150 +1.974   w200 +0.978
          w250 -0.404   w300 -1.102   w350 -2.073
```

**On this held-out 14-window panel, VMem's shipped surfel-indexed retrieval is not
distinguishable from a fixed-offset context.** Eight of fourteen windows favour retrieval,
the mean is a fifth of the between-window spread, and the sign is inconsistent.

This is a bounded negative result about one consumer on one dependency group. It does not
establish that retrieval is useless in general, and it is not a claim about the VMem paper's
own reported experiments, which use different data, different trajectories, and a different
evaluation.

The comparison is if anything generous to retrieval: `static` may use frames only up to
offset +45, while the retrieval bank extends to +55, i.e. retrieval may draw on frames
strictly closer to the targets at +60..+105. It still does not win.

## 3. A mechanical reason, visible in metadata before any score

Distinct frames actually delivered into the four context slots:

| arm | 3 distinct | 4 distinct |
|---|---|---|
| `static` | 0 | 32 |
| `memory_nms_off` (shipped) | 20 | 8 |
| `memory_nms_on` (leaked) | 2 | 26 |

The shipped retrieval wastes a context slot in **10 of 14 windows**. The cause is in the
pinned source: with NMS disabled the selection is seeded with `sorted_frames[0]` (the
surfel-nearest candidate) and then `len(self.c2ws) - 1` (the most recent stored frame). Under
forward extrapolation - targets at +60..+105 beyond a bank ending at +55 - the nearest
candidate *is* the most recent frame, so the two seeds collide and the fill step cannot
recover the slot. Observed directly, e.g. scene_13 w050 selects `[105, 105, 100, 95]`.

This is a property of the released code interacting with a forward-extrapolation regime, and
it is determined entirely by retrieval metadata: it is knowable before any target is decoded.

**It is not yet a finding.** Stratifying the sealed windows by slot utilisation gives
+1.124 dB (n=4) where four distinct frames were delivered versus -0.111 dB (n=10) where three
were, but that is a post-hoc split on a non-randomised variable with four windows on one side.
It is recorded as a hypothesis with a predeclared test, not as a result.

## 4. The predeclared test of that hypothesis

Slot-utilisation control, declared before the outputs exist: re-run the shipped retrieval arm
with the duplicated slot replaced by the next distinct candidate already ranked by the
pipeline's own distance ordering. Nothing is trained, no weights change, no new selection
criterion is introduced, and the candidate ordering is the pipeline's own; the only change is
that a slot which currently repeats an already-present frame instead receives the next
distinct frame the pipeline had already ranked.

Cost: 14 windows x 2 seeds = 28 generations. Only the 10 duplicate-bearing windows can move;
the 4 already-distinct windows are an internal null control that must reproduce the sealed
output byte-for-byte.

Prospective decision rule, fixed now: the duplication explanation is retained only if the
repaired arm improves on the sealed shipped arm by at least 0.20 dB in mean over the ten
affected windows **and** the four unaffected windows reproduce byte-identically. If the
repaired arm moves by less than 0.20 dB, duplication is exonerated as the explanation and the
negative result in section 2 stands with no mechanical account.

This is a diagnostic of what the consumer responds to, not a retrieval policy proposal. No
novelty claim attaches to it under any outcome.
