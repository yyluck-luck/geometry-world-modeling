# Prompt for GPT-6 Astra — round 6: the dormant evaluator was qualified, and it fails a reference control

Copy everything below the line.

---

You and a second reviewer both told me to qualify the built-but-never-used evaluators **before**
using them, and to treat "written and unit-tested" as distinct from "scientifically validated". I
did that. **The evaluator fails a reference-only control, and the failure was hidden until I fixed a
missing visibility check.** Zero generation was run; no sealed output was read.

I want this attacked before I record it as a finding.

## 1. What the evaluator computes

`geom_eval_s110.py` warps one **generated** view into another **generated** view and reports dense
RGB MAE. The correspondence field is **fully exogenous**: the dataset's own Kinect depth, the
dataset's poses, the dataset's intrinsics. Nothing is estimated from the predictions — that was
deliberate, to avoid sharing a reconstruction prior with the consumer, which uses CUT3R internally.

It had **never been run on anything**, and **no reference floor had ever been computed**.

## 2. Three reference conditions, real data only

| | construction |
|---|---|
| **A floor** | real target frames, unmodified |
| **B consistent-but-wrong** | every pixel coloured by a deterministic function of its world XYZ, so the same 3D surface point receives the same colour in every view. Appearance entirely wrong; cross-view agreement near perfect by construction |
| **C independent-error** | real frames plus independent per-view noise |

## 3. First run, as the evaluator stands

| condition | reproj MAE | coverage |
|---|---|---|
| A floor (real) | **7.942** | 0.792 |
| B consistent-wrong | 15.279 | 0.792 |
| C independent | 85.638 | 0.792 |

Per-window floor ranges 5.795 to 10.123, a spread of 4.328 — larger than any plausible arm effect,
so any arm comparison must be paired within window. 20.8% of pixels are never scored.

B scored **worse** than the floor. I was ready to record that the "consistent but wrong" concern was
not confirmed, and that my control was confounded because its colour field is high-frequency
(spatial sd 93.9 against the real frames' 60.6) while the metric's zero is not zero.

## 4. Then I added the visibility handling, and the result reversed

The evaluator had **no z-buffer and no forward-backward check**: it warped every valid-depth pixel
and sampled the source at the rounded location even when that surface was occluded there. I added
both, using only sensor depth and dataset poses. Thresholds were declared in the file before the run
— depth tolerance `max(0.02 m, 2% of range)`, cycle tolerance `1.0 px` — with two alternates
reported as descriptive sensitivity only.

| setting | A floor | coverage | B | C |
|---|---|---|---|---|
| baseline, no checks | 7.942 | 0.792 | 15.279 | 85.638 |
| z-buffer only | 7.013 | 0.722 | 5.518 | 85.883 |
| forward-backward only | 6.807 | 0.677 | 4.612 | 86.185 |
| **both** | **6.807** | **0.675** | **4.545** | 86.187 |

**With visibility handling, the completely wrong but surface-consistent condition scores 4.545 —
below the ground-truth frames' own floor of 6.807.**

B fell 70.3% when occluded pixels were removed; A fell only 14.3%. B's high-frequency field turned
every occluded sample into a large error, while the locally smooth real frames absorbed the same
occlusion errors mildly. **The frequency confound I had flagged therefore works against this result,
not for it** — a high-frequency field should be harder on this metric, and it still beats ground
truth.

Cost per unit of appearance deviation from the real frames: surface-consistent **0.0497**,
independent **1.3687** — a **27.5x** ratio, up from 8.1x before the fix.

Secondary: occlusion is only ~1.1 MAE of the original floor, so the floor is mostly depth noise,
pose error and nearest-neighbour sampling. The forward-backward check subsumes almost all of the
z-buffer's rejections. The floor is robust to the tolerance (6.715 / 6.807 / 6.901 across a 5x
range) but coverage is not (0.437 / 0.675 / 0.714).

## 5. What I would conclude, and want you to attack

> This metric can be driven below the ground-truth floor by any surface-consistent texture,
> regardless of correctness. It therefore cannot support a claim that one arm recovers geometry
> better than another; it can only say that one arm's views are more mutually compatible under the
> reference correspondence field.

## Questions

**Q1. Is B a legitimate control, or have I built a degenerate input that no generator could produce?**
This is my main worry. A world-XYZ colour field is exactly consistent by construction. If the honest
reading is "you constructed an oracle-consistent image and showed the consistency metric likes it",
then this demonstrates nothing a reader did not already know, and I should say so. What would make it
a fair control — matching the real frames' spatial frequency, or something else?

**Q2. Does "B below A" actually follow, or is it an artefact of the coverage change?** B and A are
scored on the same mask within each pair, but the visibility tests reject pixels based on **geometry
only**, not on either image's content, so I believe the masks are identical for A, B and C within a
window-pair. I have not verified that claim in code. If it is false, the comparison is invalid. Tell
me what else could make this an artefact.

**Q3. Is the ground-truth floor the right comparator at all?** Real frames are not "perfect" under
this metric — they carry sensor noise and pose error that a generator does not have to reproduce. Is
"B beats A" the right framing, or should the claim be restricted to "B beats A" being evidence only
that the metric is not a fidelity measure?

## 6. Added after the above was written: the metric family I had not searched

An ideation pass surfaced three further metrics on this exact task line. I verified all of them at
primary source:

| metric | id | verified content |
|---|---|---|
| **TSED** | arXiv:2304.10700 | *"we introduce a new metric, the thresholded symmetric epipolar distance (TSED), to measure the number of consistent frame pairs in a sequence."* Autoregressive conditional diffusion NVS. |
| **GeCo** | arXiv:2512.22274 | *"a geometry-grounded metric for jointly detecting geometric deformation and **occlusion-inconsistency** artifacts in **static scenes**. By fusing residual motion and depth priors, GeCo produces interpretable, dense consistency maps."* Also usable as a training-free guidance loss. |
| **PDI-Bench** | arXiv:2605.15185 | object-centric observations via segmentation and point tracking, lifted to 3D, projective-geometry residuals. |
| **SGC** | arXiv:2603.19048 | "Measuring 3D Spatial Geometric Consistency in Dynamic Video Generation". |

**GeCo's stated scope covers exactly the defect section 4 spent a day discovering.** Static scenes,
occlusion-inconsistency, depth priors fused with a residual-motion cue this evaluator has no
analogue for, dense maps. The z-buffer and forward-backward checks I added are standard practice
that GeCo already incorporates. I did not add a capability; I caught up to one.

This is the third time today that an established method on this task line turned out to exist and
not to have been searched for. My standing rule already required searching before building a metric;
it did not require enumerating the *family*, and I stopped at the first hit.

**Q4. Should the evaluator simply be retired?** My current conclusion is yes: it is a weaker instance
of an established family — dense reprojection error with an exogenous correspondence field, no motion
cue, no scale-invariant fusion, a hand-added occlusion test, and a demonstrated failure on a
surface-consistent wrong texture. The plan would be TSED for a thresholded-consistency reading and
GeCo for a dense diagnostic, with mine kept only as an internal sanity check with its floor quoted,
if at all. Its one distinguishing property is that the correspondence field is fully exogenous,
whereas MEt3R estimates correspondences from the generated images with DUSt3R while my consumer uses
CUT3R internally. **Is that exogeneity worth preserving, or is it outweighed by the fact that the
metric can be driven below the ground-truth floor by a wrong texture?**

**Q4b. Does any of today's evaluator work retain value, or is it all catch-up?** The floor numbers
(6.807, coverage 0.675) and the B-below-A result are correct and were necessary before any use. But
if the honest reading is that a published metric already handles this and I merely rediscovered
standard practice at the cost of a day, say that plainly.

**Q5. Does this change the priority order?** The second reviewer ranked T1-5 (pose-label feedback in
self-generated history) first and this evaluator work second. This result makes me think the
evaluator cannot serve as the secondary endpoint T1-5's design assumed. If so, does T1-5 still have a
usable endpoint, or does it collapse to RGB PSNR alone?

**Q6. What search procedure would have caught the family, not just the first hit?** I now require
enumerating a task line's metric family before building anything, but I would rather adopt a
procedure you consider actually sufficient than invent another rule that fails on the next case.

Constraints unchanged: frozen consumer, no training, no new data, two exposed development sequences,
one dependency group, finite panel is not population evidence. **No generation is requested.** Do not
soften a negative answer.
