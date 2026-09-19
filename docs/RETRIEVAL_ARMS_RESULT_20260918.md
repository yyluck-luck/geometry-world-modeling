# Retrieval arms on the fixed 14-window panel — authoritative result (2026-09-18)

Status: `MEASURED_FINITE_PANEL_RESULT`. `new_method_validated=false`,
`novelty_authorization=NONE`. No human approval implied.

Supersedes `docs/UNCONTAMINATED_RETRIEVAL_RESULT_20260918.md`, which stated the direction
wrongly. Both are retained.

## 0. Scope, stated before the numbers

**Two exposed development sequences** (scene_13, scene_14), 14 fixed windows, 2 fixed seeds,
one dependency group, one frozen consumer, PSNR on RGB only. Target frames are held out **from
conditioning**; the sequences themselves are exposed and have shaped the hypotheses. These are
**not** independent held-out evaluation data and the word "held-out" is not used for them.

Windows are a **finite panel**, not a sample from a population. The quantity measured is the
mean over those exact 14 windows and 2 seeds. It is not an estimate of a population effect.
**No standard error, t statistic, confidence interval, significance test, equivalence test or
window bootstrap is reported**, because none of them matches this design. SD is reported purely
as a description of how much the effect varies across the panel.

Both compared arms receive real historical frames. This is **retrieval-selected history versus
fixed-offset history**, not memory versus no memory.

## 1. The arms

| arm | context | provenance |
|---|---|---|
| `static` | frames at offsets +0, +15, +30, +45 | fixed, no retrieval call |
| `memory_nms_off` | pipeline retrieval, NMS disabled | the **movement** path: `navigation.py:185,234` pass `use_non_maximum_suppression=False` |
| `memory_nms_on` (leaked) | NMS enabled under an inherited `initial_threshold = 1e8` | sealed job 594957; interpretation withdrawn |
| `memory_nms_on_clean` | NMS enabled from an isolated state | job 595887, this run |

Targets are at offsets +60, +75, +90, +105. The retrieval bank spans +0..+55; the fixed-offset
arm may use only up to +45. Retrieval therefore has a **candidate-availability advantage**. That
is reported as an unequal horizon, not as a guarantee of any performance ordering: a frozen
generator's output is not monotone in candidate proximity, and this selector carries no dominance
guarantee.

## 2. Results, window-level (seeds folded within window first, per v2.14)

| contrast | mean | SD across windows | windows positive |
|---|---|---|---|
| `memory_nms_off` − `static` | **+0.242 dB** | 1.270 | 8/14 |
| `memory_nms_on_clean` − `static` | **−0.485 dB** | 1.489 | 6/14 |
| `memory_nms_on_clean` − `memory_nms_off` | **−0.726 dB** | 1.210 | 5/14 |
| `memory_nms_on_clean` − `memory_nms_on` (leaked) | +0.245 dB | 0.711 | 6/14 |

Median of the shipped-minus-static differences is +0.385 dB; the range is −2.073 to +2.055.

**Correct statement of the first row:** across 14 fixed windows and 2 fixed seeds, the shipped
retrieval configuration achieved a mean PSNR advantage of **+0.242 dB** over a fixed-offset
context, with variation across windows (SD 1.270) about five times the mean and 8 of 14 windows
favouring retrieval.

This does **not** say retrieval fails, does not establish a negligible advantage, and does not
generalise beyond the panel. An earlier draft of this project said "does not beat"; that was
wrong and is retracted.

## 3. What the corrected NMS-on arm settles

The sealed `memory_nms_on` arm ran with a threshold inherited from a preceding NMS-off call
(`get_context_info` writes `1e8` in its disabled branch; the enabled branch assigns only at
exactly five stored frames; `reset()` does not clear it). Its −0.729 dB figure was withdrawn as
an estimate of the independently initialised effect.

Job 595887 replaces it. From an isolated state, `memory_nms_on_clean` − `static` = **−0.485 dB**.
The sign is unchanged and the magnitude shrinks by about a third.

**Consequence for the released system:** the released demo uses **both** settings. Movement
(`navigation.py:185,234`) passes `use_non_maximum_suppression=False`; turning (`navigation.py:321`,
reached from `app.py:208/210`) passes no argument and resolves to the config default `true`. On this
panel the setting used for turning is **0.726 dB worse** than the setting used for movement.
Because the disabled branch writes `initial_threshold = 1e8` and the enabled branch assigns only at
exactly five stored frames, a native sequence of movement followed by turning consumes the leaked
value: the threshold a turn uses depends on whether the user moved first. This is static
reachability plus selector semantics; the demo was not run, and nothing here bears on the paper's
evaluation. See `docs/ENTRY_PATH_CORRECTION_20260918.md`.

## 4. What the leak actually changed, decomposed

A zero-diffusion census (job 595614) classified every window before any score existed, by whether
the leaked threshold changed the padded context ids: **NULL 2, PERMUTATION 4, CONTENT 8**.
Slot 0 was identical in 14/14 windows, as the source requires (`sorted_frames[0]` is appended
before the threshold loop and never reads the threshold).

| stratum | n | mean of `clean − leaked` | SD |
|---|---|---|---|
| NULL (identical selection) | 2 | **+0.000 dB** | 0.000 |
| PERMUTATION (same multiset, different order) | 4 | **−0.015 dB** | 0.015 |
| CONTENT (different multiset) | 8 | +0.436 dB | 0.917 |

**Which contrast these strata decompose — read this before quoting them.** Weighted by the stated
window counts, `(2×0.000 + 4×(−0.015) + 8×0.436)/14 = 0.24486 → **+0.245 dB**`, which is row 4 of
§2, `memory_nms_on_clean − memory_nms_on (leaked)`. It is **not** a decomposition of the primary
contrast `memory_nms_off − static = +0.242 dB` in row 1. The two differ by 0.003 dB, so quoting
these strata next to the primary contrast without naming the estimand produces a false
decomposition that no magnitude check will catch. An external review made exactly that
reconciliation attempt on 2026-09-19 and reported a 0.0029 dB "discrepancy"; there is none.

The NULL stratum is exactly zero because the two arms received byte-identical consumer input and
produced byte-identical output — verified by sha256 on all four runs. That is the validity gate
for reusing sealed outputs instead of regenerating them, and it passed.

**The PERMUTATION stratum is the informative one.** Holding the context multiset, cameras,
intrinsics, normalisation input and slot-0 ray gauge all fixed and changing only slot order moved
PSNR by **0.015 dB**. In this regime, the leak's entire effect is carried by *which frames* were
selected, not by the order they occupy.

Scope limit: this is order variation among orderings the retrieval itself produced, on four
windows. It does not license a general claim that this architecture is order-insensitive, and a
non-zero difference is expected from reordered floating-point reductions alone; the finding is
that the magnitude is negligible here, not that the computation is invariant.

## 5. The duplicate-slot observation, and what it is not

Distinct frames delivered into the four context slots: `static` 4/4 in every window; shipped
retrieval **3 distinct in 10 of 14 windows**; clean NMS-on 4 distinct in 13 of 14.

Source cause: the disabled selection is seeded with `sorted_frames[0]` (surfel-nearest) and then
`len(self.c2ws) - 1` (most recent). Under forward extrapolation those collide, and the fill step
cannot recover the slot because the duplicate already counts toward `len(selected_indices)`.

This is an **implementation behaviour**, established from source and metadata. It is **not** a
reason why retrieval "cannot" outperform the baseline: three well-chosen distinct frames with one
repeated could beat four poorly chosen frames. The post-hoc 4-distinct versus 3-distinct split of
the sealed windows is retained only as the observation that motivated the repair experiment; no
regression, subgroup search or explanatory weight is built on it.

Of the 14 windows, 8 are repairable, 4 already deliver four distinct frames (internal no-op
controls), and 2 have only three distinct candidates in the pipeline's entire ranked list, so the
duplicate there is a genuine candidate shortage rather than a recoverable slot.

The repair experiment and its prospective decision rule are specified in
`work/S103_selector_free_baseline/REPAIR_SPEC_PREDECLARED_20260918.md`, recorded before any repair
output was scored.

## 6. What none of this establishes

Not that memory or retrieval is ineffective in general. Not anything about long-horizon scene
consistency or revisit behaviour, which is the setting the original selector ablation targets and
which this forward-window panel does not reproduce. Not that the published results are affected
by the state leak: contamination is *demonstrated* in this project's comparative execution and
*reachable* in the released demo, but the release ships no evaluation script, so the configuration
behind the paper's tables cannot be determined from it. Not any population-level effect,
from any number of additional seeds, windows, or replays.
