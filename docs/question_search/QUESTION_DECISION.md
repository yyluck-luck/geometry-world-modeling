# Bounded question search — decision

2026-09-18, **corrected 2026-09-18 after external review**. Scope: one search for a research
question different from the closed duplicate-context branch. Authorized: source inspection,
primary-source reading, CPU analysis of existing artifacts, experiment specification.
**No generation was run and none is requested.**

## Decision

**Surviving candidates: ZERO — as an investment decision, not as an empirical refutation.**

| object | accurate status |
|---|---|
| duplicate-slot repair (old branch) | **Completed its prespecified test, did not meet the criterion, stays closed.** |
| Candidate A | **Evidence status: untested for the specified recent/spread experiment. Project disposition: closed without execution; not selected for further investment.** Not empirically falsified. |
| Candidate B | **No sufficiently specific, valuable residual hypothesis was established. Not disproved.** |
| S112 revisit | **Untestable under its own frozen qualification rule. No new data requested.** |

**Exact new residual: NONE established.** **Generation budget requested: 0.** **Verdict: STOP.**

No `ONE_EXPERIMENT.md` is produced.

---

## Corrections to the first version of this document

The first version overstated its conclusions in five ways. All are retracted here.

1. **It claimed the +0.242 dB primary contrast is an average over a target-wise profile.** That is
   a mathematical error, corrected in §1 below.
2. **It reported oracle numbers computed under a changed score, without saying so**, and compared
   them to a threshold defined on the original score.
3. **It instantiated candidate A's "two pre-fixed context policies" as the two released retrieval
   behaviours, and then rejected candidate A using that instantiation.** Candidate A does not
   specify those policies.
4. **It inferred from horizon-wise winner reversals that a historical probe cannot predict a fixed
   aggregate endpoint.** That inference does not follow.
5. **It inferred that one dependency group makes a positive descriptive finite-panel claim
   untestable.** That was an asymmetric evidence standard.

A sixth correction concerns candidate B's source argument and is in §3.

---

## 1. The scoring-definition error, and the corrected numbers

The prespecified primary score pools MSE across the four targets **before** taking one PSNR. My
feasibility analysis took a PSNR per target and averaged. For per-frame MSEs \(e_1..e_4\):

\[
Q_{\text{pooled}} = -10\log_{10}\operatorname{AM}(e),\qquad
Q_{\text{frame}}  = -10\log_{10}\operatorname{GM}(e),\qquad
Q_{\text{frame}} - Q_{\text{pooled}} = 10\log_{10}\frac{\operatorname{AM}(e)}{\operatorname{GM}(e)} \ge 0.
\]

**The gap is arm-dependent**, measured on these 14 windows:

| arm | mean gap | min | max |
|---|---|---|---|
| `static` | +0.227 dB | +0.060 | +0.617 |
| `memory_nms_off` | **+0.697 dB** | +0.232 | +1.388 |
| `memory_nms_on` | +0.564 dB | +0.024 | +1.226 |
| `memory_nms_on_clean` | +0.533 dB | +0.023 | +1.133 |

Because the gap differs by up to ~0.47 dB between arms, **contrasts, per-window winners and oracle
ceilings all move between the two aggregations.** Reproduced directly:

| `memory_nms_off` − `static` | value |
|---|---|
| pooled MSE, then PSNR (**prespecified**) | **+0.242 dB** |
| PSNR per target, then average | **+0.712 dB** |

**Retracted:** "the +0.242 dB aggregate is an average over this profile." The two numbers are
different aggregations of the same predictions, both valid, and +0.712 is **not** an additive
decomposition of +0.242. The prespecified scoring rule is unchanged and remains primary.

### Oracle numbers, fully specified

All of the following: **prespecified pooled-MSE PSNR**; the 14 windows with all arms present;
seeds 42 and 7 **averaged within a window first**; **one policy chosen per window** (not per
target frame); oracle = mean over windows of the per-window maximum, minus the maximum over
policies of the mean over windows.

| policy pair (both already generated) | best constant | oracle | ceiling | windows where the second-listed policy scores higher |
|---|---|---|---|---|
| `memory_nms_off` vs `memory_nms_on_clean` | 14.637 | 14.692 | **+0.055 dB** | 5/14 |
| `memory_nms_off` vs `memory_nms_on` (leaked) | 14.637 | 14.694 | **+0.057 dB** | 4/14 |
| `static` vs `memory_nms_on_clean` | 14.395 | 14.755 | **+0.360 dB** | 6/14 |
| `static` vs `memory_nms_off` | 14.637 | 15.039 | **+0.402 dB** | 8/14 |

The last column was previously headed "flips", which was ambiguous. It counts windows where the
**second-listed** policy scores higher, with strict comparison; exact ties are counted to the
first-listed policy and do not affect the oracle, which takes the maximum. It is **not** the number
of windows in which the oracle departs from the best constant policy — for the last row that count
is 6/14, not 8/14, because the best constant policy there is already `memory_nms_off`. The column is
descriptive and is not needed for the bound to hold.

Under the framewise-average score the same two headline pairs give +0.065 dB and +0.255 dB. The
first version of this document reported those framewise figures without labelling them.

**Scope of these numbers.** These are **retrospective upper bounds for selecting among the
specified, already-generated outputs on the fixed panel and seeds. They do not bound performance
under new policies, new generation seeds, altered execution states, or a different selection
granularity.** A selector that chose correctly in every window would *attain* the oracle; the
correct statement is that no selector obeying the same per-window granularity can **exceed** it. The
earlier phrasing "no real selector can reach it" is withdrawn.

**Granularity is not interchangeable.** Choosing once per window is a stricter permission than
choosing per seed, since
\(\max_a \tfrac12\sum_s Q_{w,s,a} \le \tfrac12\sum_s \max_a Q_{w,s,a}\), and choosing per
target frame is looser still — and splicing frames from two joint generations is not necessarily a
generation strategy the system permits. Where a proposal does not state its granularity, a
per-window oracle is **a conditional bound, not "the proposal's bound."**

**The row involving the leaked arm is retained as an execution diagnostic only.** Its appearance in
an oracle table does not make that state a recommended configuration.

---

## 2. Candidate A — history-to-future context-utility transfer

### What I actually evaluated, and why it does not bound candidate A

Candidate A, as given to me, specifies "two pre-fixed context policies" without naming them. **No
draft naming them exists in this repository** — a search for the recent/spread index sets
`[11,10,9,8]` and `[11,7,4,0]` returns nothing. I therefore chose an instantiation myself: the two
released retrieval behaviours. That choice was mine and was not labelled as such.

Review states candidate A's specified policies are a **recent** set `[11,10,9,8]` and a **spread**
set `[11,7,4,0]`, both delivering four distinct frames with slot 0 = the most recent frame, and
**neither requiring native retrieval**. That differs from my instantiation in a way that matters
directly: my `static` arm has slot 0 = the *oldest* frame, and slot 0 is the Plücker reference
camera, so my pair is not a re-labelling of theirs.

**Therefore: none of the oracle numbers in §1 bounds candidate A.** Its policies have never been
generated. Recorded status: **untested**.

**What those numbers do still establish, and which is retained as a real negative result.**
Conditional on these already-generated outputs, this panel, these seeds, this score and per-window
granularity, **no selector routing between `memory_nms_off` and `memory_nms_on_clean` can gain more
than +0.055 dB.** Any proposal that would require a +0.20 dB gain from routing between exactly those
two arms under exactly those conditions is therefore excluded without implementing a router. That
conclusion is retained. What is withdrawn is only its extension — it does not apply to other
policies, other seeds, or another scoring definition, and so it does not kill the recent/spread
proposal.

### Two withdrawn inferences

**Withdrawn — horizon reversal does not prove unpredictability.** I found that the per-window
winner is constant across the four target horizons in only 6/14 windows (`static` vs
`memory_nms_off`, framewise score). I concluded the probe's answer "is determined by a design
choice, not by the window." That does not follow. Candidate A asks a probe to predict the winner
under a **fixed four-frame aggregate endpoint**, not at every horizon. Every window could reverse
internally while the aggregate winner remains predictable from a history-computable signal.
The observation is a **transfer-risk signal**, not a completed test.

**Withdrawn — one dependency group does not forbid the descriptive claim.** "This fixed selector
beats both constant policies by X dB on these 14 windows, these seeds, this score" is arithmetic on
a finite panel and needs no significance test. What one dependency group forbids is the
**population** reading. I had applied the strict standard to a hypothetical positive result while
accepting negative descriptive results at the same scope — an asymmetric standard, corrected here.

### Reasons the investment is still declined

These are resource judgements, not refutations.

- **Indirect evidence of transfer risk.** Winner reversal across target position within a window
  was measured at 6/14 constant — **on the policy pairs I generated, not on the recent/spread pair**.
  It suggests the risk; it is not a measured transfer failure of candidate A.
- **Structural mismatch is unresolved.** Withholding a block to build the probe shrinks the
  candidate pool and shortens the horizon, and both policies are pool-dependent.
- **Objective overlap with the project's own closed GRC.** GRC = fixed-budget risk-calibrated
  memory selection: a history-computable signal predicting a better future outcome. Candidate A
  shares that upper-level objective. It is **not** identical: GRC targets geometric error, A targets
  RGB PSNR; GRC is risk-calibrated, A is a fixed decision; GRC is fixed-budget, A adds probe cost.
  Those differences do not by themselves constitute innovation, and the overlap does not by itself
  prove occupancy or impossibility. It raises the bar for explaining what is new.
- **Expected information gain does not cover the cost.** The probe arm requires a new generation
  block. *Not being currently authorized is an execution constraint, not evidence of low research
  value, and is not offered as a reason.*

**I do not claim the specified recent/spread experiment would fail.** I claim it has not been run,
its value is unestablished, and the measured transfer risk plus objective overlap make it a poor
use of the remaining budget.

### Prior-art relation, recorded

| relation | verdict |
|---|---|
| 1. Same objective | **Overlapping** with the project's own closed GRC proposal. |
| 2. Same mechanism | **No** — measured probe performance rather than a conflict/risk feature. |
| 3. Same evaluation claim | **Overlapping but not identical** — RGB PSNR vs geometric error; fixed decision vs risk calibration. |
| 4. Adjacent topic | validation-set and online model selection; diffusion likelihood scoring. |

---

## 3. Candidate B — companion-query effects

### Status: no sufficiently specific, valuable residual hypothesis was established

Not "disproved by the word joint."

**Corrected source claim.** The first version asserted that companion targets which do not extend
the translation extrema leave the normalization scale unchanged, so the anchor's conditioning
tensor would be bit-identical. **That is wrong.** `get_translation_scaling_factor`
(`pipeline.py:1089`) does not normalize by extrema. It computes each centre's distance to the
**median**, masks outliers at 10x the 97th percentile, subtracts the **mean** of the surviving
centres, and then sets

```
translation_scaling_factor = camera_scale / ||camera_dists[0]||  + 0.01
```

— the **first camera's distance from the recentred origin**. Changing an interior companion can
move the mean and therefore that distance and the scale. **I never measured tensor equality for any
candidate set, so no such evidence is retained; the claim is withdrawn entirely, not weakened.**

The origin of the error is identifiable: "furthest-frame normalization" is the convention in this
project's **evaluation** metric `pose_metric_cameractrl.py` (CameraCtrl protocol). I carried that
description into the consumer's **conditioning** path, where it does not apply.

**Corrected logical claim.** Slot 0 being invariant to the threshold leak closed one route — the
leak cannot change the reference camera. It does **not** close the different route in which
changing the companion target set changes the native normalization scale. Those are distinct steps
in the same function chain. PRoPE (arXiv:2507.10496) is clear adjacent work on reference-frame
sensitivity in absolute raymap encodings, but adjacency alone does not occupy every specific
target-set-dependence experiment, and I should not have written it as doing so.

**What remains true.** Joint denoising of 8 frames permits cross-target influence; it does not
guarantee that an arbitrary companion change moves the anchor, nor that any movement is
consequential. Equally, merely demonstrating such dependence would not be a contribution. **No
specific, falsifiable, valuable consequence was formulated**, and every artifact uses the same four
target offsets so nothing can be analysed without new generation. Hence: not investigated further,
not refuted.

---

## 4. Not promoted, and why

The feasibility analysis showed a target-position profile for `memory_nms_off` − `static`
(framewise score): +2.950, +0.398, −0.180, −0.321 dB at +60/+75/+90/+105. I did not promote this to
a candidate. Two reasons, and one correction:

- **Occupancy.** "Spread beats adjacent/clustered context" is the published ablation in Context as
  Memory (arXiv:2506.03141): FOV+Random 19.17/17.47 to FOV+Non-adj 20.11/18.19.
- **Adjacency to the closed branch.** It is a finer aggregation of the same arms and question.
- **Correction:** I wrote that clustered-recent context "helps a near target and hurts a far one."
  Target position, camera pose and visible content co-vary in these artifacts, so the profile is a
  **description of effects by target position**; temporal distance and context clustering are not
  isolated as causes. That causal wording is withdrawn.

---

## 5. Final decision

| field | value |
|---|---|
| **Candidate** | **NONE selected for investment** |
| **Exact new residual** | **NONE established** (candidate A untested; candidate B unformulated) |
| **Rival explanation** | For A: documented transfer risk across target position, plus objective overlap with the project's own closed GRC line. For B: ordinary joint denoising, plus an unseparated native normalization path. |
| **One discriminating experiment** | None proposed. |
| **Feasibility** | A is executable but unfunded and unauthorized here. B is specifiable but has no valuable formulated consequence. |
| **Publication ceiling** | Not estimated for an untested experiment. B's best framing remains an evaluation-protocol note. |
| **Requested generation budget** | **0** |
| **Verdict** | **STOP — decline further investment; do not record either candidate as refuted.** |

`new_method_validated=false`. `novelty_authorization=NONE`. No approval is self-signed here.
