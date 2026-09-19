# Prompt for GPT-6 Astra — round 5: re-review the corrections, including whether I over-corrected

Copy everything below the line.

---

You reviewed a bounded question-search decision and found it unacceptable: it had not added
generation (fine), but its rejection reasons contained a changed scoring definition, a substituted
candidate, and several invalid inferences. Your ruling was that the old repair branch stays closed
and no generation starts, but `QUESTION_DECISION.md` must change "已证伪" to an accurate status,
because *declining to invest* and *having been experimentally refuted* are different things.

**I accepted every correction and verified each one against source or data before applying it.**
This round added no generation; GPU queue is empty. I am asking you to re-review the corrections
themselves — in particular whether I have now swung too far in the other direction.

## Part 1 — what I verified before accepting

### 1.1 The scoring-definition error: confirmed, and the gap is arm-dependent

Your algebra is exactly right. The prespecified score pools MSE across four targets then takes one
PSNR; my analysis took one PSNR per target then averaged:

\[
Q_{\text{frame}} - Q_{\text{pooled}} = 10\log_{10}\frac{\mathrm{AM}(e)}{\mathrm{GM}(e)} \ge 0.
\]

Measured on the 14 windows, the gap **differs by arm**:

| arm | mean gap | min | max |
|---|---|---|---|
| `static` | +0.227 dB | +0.060 | +0.617 |
| `memory_nms_off` | **+0.697 dB** | +0.232 | +1.388 |
| `memory_nms_on` | +0.564 dB | +0.024 | +1.226 |
| `memory_nms_on_clean` | +0.533 dB | +0.023 | +1.133 |

Direct reproduction of the same contrast under both aggregations:

| `memory_nms_off` − `static` | value |
|---|---|
| pooled MSE then PSNR (**prespecified**) | **+0.242 dB** |
| PSNR per target then average | **+0.712 dB** |

I retracted "the +0.242 aggregate is an average over this profile" as a mathematical error, kept
the prespecified rule as primary, and labelled the framewise figures as a separate post-hoc
aggregation.

### 1.2 Oracle numbers recomputed under the prespecified score, fully specified

Specification now attached to every number: prespecified pooled score; the 14 windows with all arms;
seeds 42 and 7 averaged **within a window first**; **one policy chosen per window**, not per target;
oracle = mean over windows of the per-window max; best constant = max over policies of the mean.

| policy pair (both already generated) | best constant | oracle | ceiling | flips |
|---|---|---|---|---|
| `memory_nms_off` vs `memory_nms_on_clean` | 14.637 | 14.692 | **+0.055 dB** | 5/14 |
| `memory_nms_off` vs `memory_nms_on` (leaked) | 14.637 | 14.694 | **+0.057 dB** | 4/14 |
| `static` vs `memory_nms_on_clean` | 14.395 | 14.755 | **+0.360 dB** | 6/14 |
| `static` vs `memory_nms_off` | 14.637 | 15.039 | **+0.402 dB** | 8/14 |

**Your +0.402 check value reproduces exactly.** I also changed "no real selector can reach it" to
"no selector under the same per-window granularity can exceed it", since a selector that chose
correctly everywhere would attain it.

### 1.3 The normalization claim: you were right, and I found the origin of my error

I read `get_translation_scaling_factor` (`pipeline.py:1089`). It does **not** normalize by extrema.
It computes each centre's distance to the **median**, masks outliers at 10× the 97th percentile,
subtracts the **mean** of surviving centres, then sets
`translation_scaling_factor = camera_scale / ||camera_dists[0]|| + 0.01` — the **first camera's
distance from the recentred origin**. Changing an interior companion can move the mean and hence the
scale.

I had run **no** tensor-equality check on any candidate set, so there was nothing to preserve; the
claim is withdrawn in full rather than weakened.

The error's origin is identifiable and I recorded it: furthest-frame normalization is the convention
in this project's **evaluation** metric `pose_metric_cameractrl.py` (CameraCtrl protocol). I carried
that description into the consumer's **conditioning** path, where it does not hold. I also accepted
that slot-0 invariance closes only the "leak changes the reference camera" route, not the distinct
"companion set changes the native scale" route, and that PRoPE's adjacency does not occupy every
specific target-set-dependence experiment.

### 1.4 Two inferences withdrawn

**Horizon reversal does not prove unpredictability.** Candidate A asks a probe to predict the winner
under a fixed four-frame aggregate endpoint, not at every target position. Every window could
reverse internally while the aggregate winner stays predictable. Recorded as a **transfer-risk
signal**, not a completed test.

**One dependency group does not forbid the descriptive claim.** "This fixed selector beats both
constant policies by X dB on these windows, seeds and score" is arithmetic on a finite panel. What
one dependency group forbids is the population reading. I had applied the strict standard to a
hypothetical positive result while accepting negative descriptive results at the same scope. That
asymmetry is corrected.

## Part 2 — the one correction I could NOT verify, and what I did about it

You wrote that you re-read the candidate A experiment file and that its policies are
\(R=[11,10,9,8]\) and \(S=[11,7,4,0]\), both four distinct frames, slot 0 = newest, native retrieval
not required.

**That file does not exist in this repository.** A search for those index sets returns nothing. The
candidate A text I was given specifies only "two pre-fixed context policies", unnamed.

I accepted your correction anyway, because it holds regardless of where the draft lives: **I chose
an instantiation myself and did not label it as my choice, so my oracle numbers cannot bound a
policy pair I invented.** I recorded candidate A as **untested**, noted that the recent/spread sets
appear nowhere here, and noted that the difference matters concretely — my `static` arm has slot 0 =
**oldest** frame, whereas the recent/spread pair has slot 0 = **newest**, and slot 0 is the Plücker
reference camera, so mine is not a relabelling of theirs.

**Q0. If that draft exists, please supply it.** If it does not, then "candidate A as specified"
currently has no specification in my possession, and I would like that stated plainly rather than
left as an implied disagreement.

## Part 3 — the corrected status, verbatim

| object | accurate status |
|---|---|
| duplicate-slot repair | Completed its prespecified test, did not meet the criterion, stays closed. |
| Candidate A | Its specified experiment was never executed. Existing oracle numbers do not correspond to its policies. Not selected for investment; **NOT empirically falsified**. |
| Candidate B | No sufficiently specific, valuable residual hypothesis was established. **Not disproved**. |
| S112 | Untestable under its own frozen qualification rule. No new data requested. |

Verdict: **STOP — decline further investment; do not record either candidate as refuted.**
Generation budget requested: **0**.

Reasons the investment is still declined, stated as resource judgements rather than refutations:
documented transfer risk across target position (winner constant in only 6/14 windows); unresolved
structural mismatch, since withholding a block shrinks the pool and shortens the horizon and both
policies are pool-dependent; overlap with this project's own closed GRC objective — which I now
state as *overlapping but not identical* (geometric error vs RGB PSNR, risk calibration vs fixed
decision, fixed budget vs added probe cost), explicitly not as proof of occupancy or impossibility;
and the cost of a probe arm that is unauthorized here.

## Part 4 — the addendum, added verbatim as you supplied it

Appended to the finalized report as a dated §9, with the primary results and the closed repair
decision preserved:

> **Post-hoc target-wise analysis.** At target offsets +60, +75, +90, and +105, the mean framewise
> PSNR contrasts for NMS-off minus fixed-offset context were +2.950, +0.398, −0.180, and −0.321 dB,
> respectively, with seeds averaged within windows. Their arithmetic mean is +0.712 dB. This uses a
> different aggregation from the prespecified four-frame pooled-MSE PSNR contrast of +0.242 dB and
> is not its additive decomposition. The profile is descriptive and does not isolate temporal
> distance, target-slot position, or context clustering as a cause.

I added one sentence of my own explaining why the aggregations differ and that the gap is
arm-dependent. **I did not add** "the gain is carried almost entirely by the nearest target",
per your instruction. I also withdrew my earlier causal wording that clustered-recent context
"favours a near target", since target position, camera pose and visible content co-vary.

## What I need from you

**Q1. Did I over-correct anywhere?** Specifically: is "not empirically falsified" now too generous
to candidate A? The measured transfer risk is real, and I do not want a correct process fix to
convert a weak proposal into an artificially open one. Tell me if any of my retractions gave back
more than the evidence requires.

**Q2. Is the two-aggregation presentation right?** I kept pooled as primary, labelled framewise as
post-hoc, and reported the arm-dependent Jensen gap. Is reporting the gap per arm the correct way to
show the two are not interchangeable, or does it invite a reader to "convert" between them, which
would be wrong?

**Q3. Is my oracle specification now complete?** Policies, windows, seeds, score, selection
granularity, and the order of averaging versus maximizing. If anything is still under-specified,
name it. I would also like to know whether a per-window oracle is even the right bound to quote for
a proposal whose selection granularity is unstated.

**Q4. Is the candidate B status right?** "No sufficiently specific, valuable residual hypothesis was
established" — not disproved. Given I have now withdrawn the normalization argument entirely, is
there a version of the companion-query question that is specific and valuable, or does your earlier
judgement stand independent of my bad argument for it?

**Q5. This is the third consecutive round in which an external review caught an overstatement of
mine — the sign error, the call-graph error, and now the scoring-definition error.** Each was
verifiable from data or source I already had. What procedural check would have caught these
*before* delivery rather than after? I would rather adopt one concrete pre-delivery check than
continue relying on review to find them.

Constraints unchanged: frozen consumer, no training, no new data, no new weights, two exposed
development sequences, one dependency group, RGB PSNR, no hidden-state or camera-normalization
overrides, finite panel is not population evidence. **No generation is requested and none will be
run on the strength of your answer without separate approval.** Do not soften a negative answer.
