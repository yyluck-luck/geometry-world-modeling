# Source notes — only the evidence the decision rests on

2026-09-18. Every item below was read or computed for this decision. Nothing here is a novelty
claim. No generation was run.

## 1. Evidence computed from existing sealed artifacts (CPU only)

Inputs: sealed run `job-594957` (`static`, `memory_nms_off`, `memory_nms_on`), clean-arm run
`job-595887` (`memory_nms_on_clean`), and the already-authorized target RGB. Pixel preprocessing is
identical to the delivered scorers. Seeds are folded within a window first; the window is the unit.
14 windows have all arms at all four target positions.

**Two aggregations appear below and must not be mixed.**

| name | definition | status |
|---|---|---|
| **pooled** | accumulate MSE over the four targets, then one PSNR | **prespecified primary score; unchanged** |
| **framewise** | one PSNR per target, then average the four | post-hoc, introduced by this analysis only |

For per-target MSEs \(e_1..e_4\): pooled \(=-10\log_{10}\mathrm{AM}(e)\), framewise
\(=-10\log_{10}\mathrm{GM}(e)\), so framewise − pooled \(=10\log_{10}(\mathrm{AM}/\mathrm{GM})\ge0\).
**The gap is arm-dependent**, so contrasts, per-window winners and oracle ceilings all change
between them.

**Per-window aggregation gap: the difference between the two scoring definitions, computed within
each window–seed execution and then averaged over the two seeds. Mean, min and max are over the
fourteen windows.**

| arm | mean gap | min | max |
|---|---|---|---|
| `static` | +0.227 dB | +0.060 | +0.617 |
| `memory_nms_off` | **+0.697 dB** | +0.232 | +1.388 |
| `memory_nms_on` | +0.564 dB | +0.024 | +1.226 |
| `memory_nms_on_clean` | +0.533 dB | +0.023 | +1.133 |

**Checking the two aggregations against each other is legitimate on this data set and is not the
error that was retracted.** With the same windows, seeds and weights,
\(\overline Q_{\text{frame},a} = \overline Q_{\text{pooled},a} + \overline g_a\), so

\[
\Delta_{\text{frame}} = \Delta_{\text{pooled}} + \overline g_{\text{off}} - \overline g_{\text{static}}
= 0.242 + (0.697 - 0.227) = 0.712\ \text{dB},
\]

which closes at the reported precision. That identity shows the difference comes from the
definition, not from a scoring fault.

**Three limits on it.** The gap is **not a universal constant**: "subtract 0.697 to convert" is
valid for no other arm, window set or experiment. Arm-mean gaps **cannot convert per-window winners
or oracle ceilings**, because the oracle takes a per-window maximum and the per-window adjustments
are not recoverable from an arm mean. And the gap is a **difference between two definitions**, not a
correction for generator bias and not a penalty owed by a wrong score; pooled is primary here because
it was fixed in advance, not because it is provably the better endpoint for all tasks.

### 1.1 Oracle ceiling for per-window policy choice

**Full specification for every number below:** prespecified **pooled** score; the 14 windows listed
in §1.2; seeds 42 and 7 averaged **within a window first**; **one policy chosen per window**, not
per target; oracle = mean over windows of the per-window max; best constant = max over policies of
the mean over windows.

| policy pair (both already generated) | best constant | oracle | ceiling | flips |
|---|---|---|---|---|
| `memory_nms_off` vs `memory_nms_on_clean` | 14.637 | 14.692 | **+0.055 dB** | 5/14 |
| `memory_nms_off` vs `memory_nms_on` (leaked) | 14.637 | 14.694 | **+0.057 dB** | 4/14 |
| `static` vs `memory_nms_on_clean` | 14.395 | 14.755 | **+0.360 dB** | 6/14 |
| `static` vs `memory_nms_off` | 14.637 | 15.039 | **+0.402 dB** | 8/14 |

Under the **framewise** aggregation the first and fourth rows become +0.065 dB and +0.255 dB. The
first version of these notes printed the framewise figures without labelling the change of score.

**Scope.** Each ceiling bounds per-window selection between **those two already-generated
policies**, on **those windows and seeds**, under **that score**, at **that selection granularity**.
A selector choosing correctly everywhere would attain it; no selector under the same granularity can
exceed it. These numbers do **not** bound candidate A, whose specified recent/spread policies have
never been generated.

### 1.2 Winner stability across target horizon, within a window

| policy pair | horizon-constant winner |
|---|---|
| `static` vs `memory_nms_off` | 6/14 windows |
| `memory_nms_off` vs `memory_nms_on_clean` | 6/14 windows |
| `static` vs `memory_nms_on_clean` | 7/14 windows |

Example patterns for `static`(A) vs `memory_nms_off`(B) across +60/+75/+90/+105:
`BAAA` appears in scene_13 w300, w350 and scene_14 w250, w300, w350; `BBAA` in scene_13 w150 and
scene_14 w050. The typical failure is retrieval winning at the nearest target and losing at the
rest.

### 1.3 Horizon profile

Mean PSNR over 14 windows, seeds folded:

| arm | +60 | +75 | +90 | +105 |
|---|---|---|---|---|
| `static` | 16.308 | 15.025 | 14.050 | 13.108 |
| `memory_nms_off` | 19.258 | 15.423 | 13.870 | 12.787 |
| `memory_nms_on_clean` | 17.646 | 14.439 | 13.262 | 12.429 |

Retrieval minus fixed-offset, per horizon:

| | +60 | +75 | +90 | +105 |
|---|---|---|---|---|
| mean | **+2.950** | +0.398 | −0.180 | −0.321 |
| sd | 2.003 | 1.688 | 1.375 | 1.310 |
| positive | 13/14 | 7/14 | 5/14 | 6/14 |

**RETRACTED (2026-09-18).** The first version stated that the report's **+0.242 dB** aggregate
"is an average over this profile." That is a mathematical error. The four framewise contrasts above
average to **+0.712 dB**, which is exactly the `memory_nms_off` − `static` contrast computed under
the **framewise** aggregation — a different quantity from the prespecified pooled **+0.242 dB**, and
**not its additive decomposition**. Both are correct under their own definitions. The prespecified
scoring rule is unchanged.

**RETRACTED causal wording.** The first version wrote that clustered-recent context "favours a near
target." Target position, camera pose and visible content co-vary across these four targets, so the
profile is a description of **effects by target position**. Temporal distance, slot position and
context clustering are not isolated as causes here.

Retained as fact: the shipped retrieval seeds its selection with the surfel-nearest candidate and
the most recent stored frame, which coincide in 10 of 14 windows, giving a temporally clustered
context (e.g. `[105, 105, 100, 95]` = offsets +55/+55/+50/+45) against the fixed-offset arm's
+0/+15/+30/+45. The finalized report was **not edited** except for the dated addendum in its §9.

## 2. Primary-source records used to close directions

Read at primary source earlier in this project, local copies at
`/home/yliutz/gwm_litread_20260918/`. Only the items the decision actually rests on are repeated.

- **Context as Memory**, arXiv:2506.03141 — context-selection ablation, verified cell by cell:
  Random 17.70 / 17.07, FOV+Random 19.17 / 17.47, **FOV+Non-adj 20.11 / 18.19**. Excluding
  adjacent (redundant, clustered) context is worth +0.94 and +0.72 dB. **This occupies the
  replacement candidate considered in §"Replacement candidate" of the decision**: spread-versus-
  clustered context, measured in PSNR.
- **PRoPE**, arXiv:2507.10496 — *"sensitive to the arbitrary choice of reference frame, which can
  hinder generalization."* Occupies the camera-normalization route that candidate B would traverse
  if the scale were allowed to vary.

Not re-litigated here, recorded for completeness because they were cited in the register and
verified earlier at primary source: VRAG arXiv:2505.21996v4 (history-buffer retrieval losing to
recent-window conditioning), RAGME arXiv:2504.06672 (deduplication of retrieved video),
LongLive-RAG arXiv:2606.02553 (retrieval collapsing to temporally local neighbours), COVRAG
arXiv:2606.02479 (finer geometric evidence insufficient without effective selection), TTAB
arXiv:2306.03536 (episodic versus accumulated evaluation state).

## 3. Project records read as records, not as proof

- **GRC** — "fixed-budget risk-calibrated memory selection": a history-computable signal predicting
  lower future geometric error. S91 formal evaluation **BLOCKED**; S99 found the low-disagreement
  advantage over confidence unstable and **stopped that claim**. Candidate A **overlaps GRC's
  upper-level objective** (use history to choose for the future). It is not identical: geometric
  error vs RGB PSNR, risk calibration vs a fixed decision, fixed budget vs added probe cost. The
  overlap raises the bar for explaining what is new; it does **not** prove occupancy or
  impossibility. The first version overstated this as "same objective and same evaluation claim".
- **SOCF-A** — history-only source-conflict feature predicting the *signed* change in a future
  RGB-D/pose loss when one memory source is replaced, with abstention. **STOPPED** before
  execution.
- **FGB-SI** — source-intervention future-geometry measurement with complete consumer-descendant
  recomputation. **STOPPED**; its own note records that generic future-aware fixed-budget memory is
  not a novelty basis.
- **S112** — frozen revisit protocol, fixture-tested, approval recorded 2026-09-17, never launched.
  Its own predeclared rule returned `UNTESTABLE_INSUFFICIENT_INDEPENDENT_REVISITS`: 2 independent
  loop-closure events against a required 3, with all 8 revisit windows in **one** dependency group.
  Qualifying revisits sit just inside the rotation threshold (0.293 m/18.8°, 0.203 m/19.6°,
  0.271 m/19.5° against 0.30 m/20.0°).

## 4. Interface facts confirmed by source inspection

Relevant only to candidate B's design and its rejection.

- The consumer denoises 8 frames in one pass, 4 context and 4 targets, with
  `input_masks = [T,T,T,T,F,F,F,F]`. Companion targets are inside the same denoised tensor as the
  anchor.
- `get_translation_scaling_factor` (`pipeline.py:1089`) is applied to the concatenation of context
  and target cameras, so replacing a companion target can change the normalization scale and hence
  the anchor's own camera encoding.
- **CORRECTED.** The first version claimed this normalization uses the furthest-frame translation,
  so that companion sets not extending the translation extent would leave the scale unchanged.
  **That is wrong.** The function computes each centre's distance to the **median**, masks outliers
  at 10x the 97th percentile, subtracts the **mean** of the surviving centres, and then sets
  `translation_scaling_factor = camera_scale / ||camera_dists[0]|| + 0.01` — the **first camera's
  distance from the recentred origin**. Changing an interior companion can move the mean and hence
  the scale. **No tensor-equality check was ever run for any candidate set, so no such evidence is
  retained and the claim is withdrawn in full.**
- Two further branches exist and the division above is the general case, not the only one: the
  outlier threshold is capped by `torch.clamp(..., max=1e6)`, and when the first camera sits within
  `atol=1e-5` of the recentred origin the factor falls back to `camera_scale` with no division.
- Source of the error, recorded: furthest-frame normalization is the convention in this project's
  **evaluation** metric `pose_metric_cameractrl.py` (CameraCtrl protocol). That description was
  carried into the consumer's **conditioning** path, where it does not hold.
- Slot 0 being invariant to the threshold leak closes the route "leak changes the reference camera".
  It does **not** close the distinct route "changing the companion target set changes the native
  normalization scale". PRoPE (arXiv:2507.10496) is adjacent work on reference-frame sensitivity,
  but adjacency alone does not occupy every specific target-set-dependence experiment.
- Every existing artifact in this project uses the same four target offsets, so no companion
  variation exists to analyse without new generation.

## 5. What was not done

No diffusion generation. No new data. No new weights, training or fine-tuning. No new evaluator.
No hidden-state, attention or camera-normalization override. No message to any external recipient.
No approval self-signed. The prespecified primary scoring rule was not changed. The finalized
technical report was not edited except for one dated post-hoc addendum in its §9.

**Candidate A's specified policies were never generated.**

Provenance, resolved on review: *the concrete recent/spread draft existed as a ChatGPT conversation
attachment but was not present in the repository or available to the executing agent. The agent
evaluated a different, self-selected policy pair. Those results do not evaluate or bound the draft
experiment.* My search of this repository returned nothing because the file was never placed here.

The draft's contents, **as supplied by the reviewer and not independently verified by me** (I hold
no copy to hash; the reported sha256 is
`2dd57fc243e852ef40dd243bfe32237bc6e9723886222fa25c82c599c8d06f4c`):

| use | bank size | Recent | Spread |
|---|---|---|---|
| historical probe | 8 | `[7,6,5,4]` | `[7,5,2,0]` |
| future task | 12 | `[11,10,9,8]` | `[11,7,4,0]` |

One policy is chosen per window and shared by both future evaluation seeds, which are **1009 and
1013** — not the 42/7 of every sealed artifact here, so no existing output can serve as an arm of
that experiment. The draft is marked throughout as an unauthorized draft.

Supplying the file **does not return the experiment to a pending state and creates no generation
authorization.** Candidate A remains: evidence status **untested**; disposition **closed without
execution**.
