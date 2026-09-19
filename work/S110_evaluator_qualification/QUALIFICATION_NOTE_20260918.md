# Reference-only qualification of the cross-view reprojection evaluator

> **CORRECTION NOTICE, appended 2026-09-18 after external review and a support audit.**
> Parts 1-3 below are **preserved unedited** but several of their conclusions are **withdrawn**.
> The word "floor" is withdrawn as a label for condition A; the spatial-frequency argument is
> withdrawn; the occlusion attribution, the "larger than any plausible arm effect" claim, the 27.5x
> ratio as an evaluator property, the phrase "any surface-consistent texture", the reading of B as a
> *wrong-geometry* control, and the recommendation to retire the evaluator in favour of TSED are all
> withdrawn. **Part 4 is authoritative.**


2026-09-18. Zero generation. No sealed output was read. Real RGB, sensor depth, dataset poses and
intrinsics only. `new_method_validated=false`, `novelty_authorization=NONE`.

Run on `slogin-02`, 14 windows (the same panel as the sealed runs), 12 ordered view pairs each.
Receipt: `REFERENCE_FLOOR_20260918.json`. Script: `reference_floor_qualification.py`.

## Why this had to happen before the evaluator is used

`geom_eval_s110.py` warps one **generated** view into another **generated** view using the dataset's
own sensor depth and poses, and reports RGB MAE. It had never been run on anything, and **no
reference floor had ever been computed**, so its number had no interpretable zero. It also has no
z-buffer and no forward-backward visibility check, so occluded surfaces are sampled silently.

## Conditions

| | construction |
|---|---|
| **A floor** | real target frames, unmodified |
| **B consistent-but-wrong** | every pixel coloured by a deterministic function of its world XYZ, so the same 3D surface point gets the same colour in every view |
| **C independent-error** | real frames plus independent per-view noise |

## Results, mean over 14 windows

| condition | reproj MAE | spatial sd | MAE/sd | coverage |
|---|---|---|---|---|
| A floor (real) | **7.942** | 60.560 | **0.1324** | **0.792** |
| B consistent-wrong | 15.279 | 93.948 | 0.1622 | 0.792 |
| C independent-error | 85.638 | 87.942 | 0.9746 | 0.792 |

## What is now established

**1. The metric's zero is 7.942, not 0.** Ground-truth frames warped into each other with their own
sensor depth and poses already disagree by 7.942 MAE. Any generated number must be read against
this.

**2. Per-window floor varies from 5.795 to 10.123 — a spread of 4.328 MAE.** That is larger than any
plausible arm difference. **Any arm comparison must be paired within window**; unpaired arm means
would be dominated by which windows they cover.

**3. 20.8% of pixels are never scored.** Coverage is 0.792, the remainder being invalid sensor depth
or out-of-bounds reprojection. The evaluator reports these counts, but the surviving 79.2% is not a
uniform sample of the image — it excludes exactly the depth-invalid and grazing-geometry regions
where generation is hardest.

**4. It is a consistency metric, not a fidelity metric, and the size of that effect is now measured.**
Per unit of appearance deviation from the real frames:

| | deviation from real | reproj MAE | cost per unit deviation |
|---|---|---|---|
| B surface-consistent | 91.45 | 15.279 | **0.167** |
| C independent | 62.97 | 85.638 | **1.360** |

**Independent error is penalised 8.1x more per unit than surface-consistent error** — and C carries
*less* total appearance error than B while scoring 5.6x worse. A completely wrong but
surface-consistent appearance is cheap under this metric.

This is not by itself a defect: the evaluator was built to measure cross-view consistency. It does
mean the number **cannot be read as fidelity**, and that a generator which is consistently wrong
will not be caught by it.

## What this run did NOT establish, and a defect in my own control

**Control B is confounded.** It varied spatial frequency along with consistency: its colour field has
period 0.35 m and spatial sd 93.9 against the real frames' 60.6. A high-frequency field amplifies the
same small depth and pose error into a large photometric error, which is why B scored *worse* than
the floor (15.279 vs 7.942) rather than better. **B therefore does not cleanly isolate consistency**,
and the earlier expectation that a consistent-but-wrong image would beat the floor is neither
confirmed nor refuted. A corrected control must frequency-match the real frames.

**Control C is not energy-matched as intended.** Noise was scaled for a Gaussian, then clipped to
[0,255], which cut the realised deviation from the intended 91.45 to 62.97. The comparison above uses
the realised deviations, so the 8.1x ratio stands, but the design intent was equal energy and it was
not achieved.

**`MAE/sd` does not fix this.** The contrast normalisation removes a global scaling of the
prediction, which is what it was built for, but B's ratio is still worse than A's (0.1622 vs 0.1324),
so it does not remove sensitivity to spatial frequency.

## Consequences for use

- The evaluator may be used only with the floor reported alongside, and only paired within window.
- Per `RESEARCH_PRINCIPLES` v2.13 it **may not be the sole primary metric**. The established metric
  on this task line is TSED (arXiv:2304.10700), whose thresholded count of consistent frame pairs is
  also structurally more robust to the unhandled-occlusion problem than a dense mean. MEt3R
  (Asim et al. 2024, as used by COVRAG) estimates correspondences from the generated images with
  DUSt3R, which this evaluator deliberately avoids; the three answer different questions and are not
  interchangeable.
- Before any generated result is scored with it, either the occlusion handling is added, or the
  absence of a visibility check is reported as a stated limitation with the 79.2% coverage.

---

# Part 2: visibility handling added, floor re-measured

Same day, same panel, zero generation, no sealed output read. Receipt:
`VISIBILITY_FLOOR_20260918.json`. Script: `visibility_corrected_floor.py`.

Two standard tests were added, using only sensor depth and dataset poses:

- **Z-buffer.** The point's depth in the source camera is compared with the source view's **own**
  sensor depth at the landing pixel. If it is behind by more than the tolerance, the point is
  occluded and is rejected rather than sampled.
- **Forward-backward.** The landing pixel is unprojected with the source's own sensor depth and
  projected back. If it does not return within the pixel tolerance, the correspondence is rejected.

Thresholds were **declared in the file before the run**: depth tolerance `max(0.02 m, 2% of range)`,
cycle tolerance `1.0 px`. Two alternates are reported as a descriptive sensitivity check only.

## Results, mean over 14 windows

| setting | A floor | coverage | B consistent-wrong | C independent |
|---|---|---|---|---|
| baseline, no checks | 7.942 | 0.792 | 15.279 | 85.638 |
| z-buffer only | 7.013 | 0.722 | 5.518 | 85.883 |
| forward-backward only | 6.807 | 0.677 | 4.612 | 86.185 |
| **both** | **6.807** | **0.675** | **4.545** | 86.187 |

## The finding the missing visibility check had been hiding

**With visibility handling, the completely wrong but surface-consistent condition scores 4.545 —
below the ground-truth frames' own floor of 6.807.**

In Part 1, without the checks, B scored 15.279 and appeared to be *penalised*. That was an artefact.
B's colour field is high-frequency, so every occluded pixel it sampled produced a large error, while
the real frames are locally smooth and absorbed the same occlusion errors mildly. Removing occluded
and non-cycle-consistent pixels therefore helped B far more than A: B fell 70.3%, A only 14.3%.

**The spatial-frequency confound in B now works against the result rather than for it.** A
high-frequency field should be *harder* on this metric, and B still beats ground truth. The Part 1
caveat about that confound therefore no longer weakens this conclusion; it makes it conservative.

Cost per unit of appearance deviation from the real frames:

| setting | B surface-consistent | C independent | ratio |
|---|---|---|---|
| baseline | 0.1671 | 1.3600 | 8.1x |
| **z-buffer + forward-backward** | **0.0497** | **1.3687** | **27.5x** |

## What this means for use of the evaluator

**This metric can be driven below the ground-truth floor by any surface-consistent texture,
regardless of whether that texture is correct.** It therefore cannot support a claim that one arm
recovers geometry better than another; it can only say that one arm's views are more mutually
compatible under the reference correspondence field. A smoother or more internally consistent
generator will win on it while being wrong.

Had it been run on the sealed arms without this qualification, that failure mode would have been
invisible.

## Secondary observations

- **Occlusion is not the dominant term in the floor.** It accounts for about 1.1 MAE of 7.942. The
  remainder is sensor depth noise, pose error and nearest-neighbour sampling.
- **The forward-backward check subsumes almost all of the z-buffer's rejections** (6.807 with cycle
  alone versus 7.013 with z-buffer alone; adding the z-buffer to the cycle check changes the floor by
  0.000 and coverage by 0.002). If only one is implemented, it should be the cycle check.
- **The floor is robust to the tolerance choice; the coverage is not.** Across a 5x tolerance range
  the floor moves 6.715 / 6.807 / 6.901, but coverage moves 0.437 / 0.675 / 0.714. Any coverage-based
  statement is therefore threshold-sensitive and must quote the tolerance.
- **Coverage falls to 0.675**, so a third of pixels are excluded. The surviving set is not a uniform
  sample of the image: it excludes depth-invalid, occluded and grazing regions, which are where
  generation is hardest.

---

# Part 3: the established metrics on this task line, found late

Same day. Surfaced by an external ideation pass and verified at primary source. **This materially
changes the conclusion of Parts 1 and 2.**

There are at least four published metrics targeting geometric consistency of generated views on this
exact task line, none of which was searched for before this project built its own:

| metric | id | verified content |
|---|---|---|
| **TSED** | arXiv:2304.10700 | *"we introduce a new metric, the thresholded symmetric epipolar distance (TSED), to measure the number of consistent frame pairs in a sequence."* Autoregressive conditional diffusion NVS. |
| **GeCo** | arXiv:2512.22274 | *"a geometry-grounded metric for jointly detecting geometric deformation and **occlusion-inconsistency** artifacts in **static scenes**. By fusing residual motion and depth priors, GeCo produces interpretable, dense consistency maps."* Also usable as a training-free guidance loss. |
| **PDI-Bench** | arXiv:2605.15185 | quantitative audit of geometric coherence; object-centric observations via segmentation and point tracking, lifted to 3D, projective-geometry residuals. |
| **SGC** | arXiv:2603.19048 | "Measuring 3D Spatial Geometric Consistency in Dynamic Video Generation". |
| MEt3R | Asim et al. 2024 | correspondences estimated from the generated images with DUSt3R, compared in DINO feature space. |

## What this does to Parts 1 and 2

**GeCo covers the defect Part 2 spent the day discovering.** Its stated scope is static scenes and
**occlusion-inconsistency**, fusing depth priors with residual motion into dense maps. The z-buffer
and forward-backward checks added in Part 2 are standard practice that GeCo already incorporates,
and it adds a motion cue this evaluator has no analogue for.

The Part 1 and Part 2 measurements remain correct as stated: the floor is 6.807 with visibility
handling, coverage 0.675, and a surface-consistent wrong texture scores 4.545, below ground truth.
Those numbers stand and they did have to be measured before any use.

**But the conclusion changes.** This evaluator is a weaker instance of an established family: dense
reprojection error with an exogenous correspondence field, no motion cue, no scale-invariant fusion,
a hand-added occlusion test, and a demonstrated failure on a surface-consistent wrong texture.

**Recommendation: retire it as a candidate primary or secondary endpoint.** If a geometry endpoint is
needed, use TSED for the thresholded-consistency reading and GeCo for the dense diagnostic, both of
which are published, comparable with other work, and already handle the occlusion case. Keep this
evaluator only as an internal sanity check with its floor quoted, if at all.

**Its one remaining distinguishing property** is that the correspondence field is fully exogenous
(sensor depth and dataset poses), whereas MEt3R estimates correspondences from the generated images
with DUSt3R and this project's consumer uses CUT3R internally. That motivation was sound. It does
not survive the fact that the metric can be driven below the ground-truth floor by a wrong texture.

---

# Part 4 (authoritative): support audit, and the withdrawals it forces

Receipt: `SUPPORT_AUDIT_20260918.json`. Script: `support_audit.py`. Run on `slogin-02`, zero
generation, no sealed output read.

## What the evaluator actually measures, restated

**Reference-warped RGB disagreement on qualified overlap.** For a fixed directional correspondence
map and support mask derived from sensor depth and dataset poses, it is the mean L1 RGB difference
between one image and another sampled through that map. **The recorded reference RGB does not appear
in the expression** — only its geometry determines the correspondence and the support. A lower score
means exactly that this quantity decreased. It is not a certificate of coherent scene structure,
accurate depth, correct camera motion, or faithful appearance.

## Audit result 1 — support is provably content-independent, verified

The support routine is passed only depth, poses and intrinsics; no image reaches it. Masks and
sampled flat indices were hashed per directional pair and compared across all conditions:
**identical, PASS**. Equal coverage totals were not accepted as evidence; the indices themselves
match.

## Audit result 2 — an exact fidelity-blindness demonstration, replacing the earlier one

Applying **a single fixed RGB channel permutation to every real image** leaves the score
**bit-identical**:

```
max |R(A) - R(D)| over 14 windows = 0.000000000000
mean R(A) = 6.8072      mean R(D) = 6.8072
```

With equal channel weights and an L1 over channels, permuting channels identically in every view
reorders the summands and cannot change the sum. Fidelity to the recorded RGB is destroyed; the
score does not move at all.

**This supersedes the world-coordinate retexturing as the fidelity-blindness argument.** It is exact
rather than empirical, introduces no geometry of its own, and needs no claim about spatial frequency.
The defensible statement is:

> Lower reference-warped photometric disagreement does not imply greater appearance fidelity.

## Audit result 3 — the B versus A comparison, paired and per window

| scene | window | B − A |
|---|---|---|
| scene_13 | w050 | −2.611 |
| scene_13 | w100 | −4.415 |
| scene_13 | w150 | −4.025 |
| scene_13 | w200 | −6.218 |
| scene_13 | w250 | −6.273 |
| scene_13 | w300 | −5.571 |
| scene_13 | w350 | −2.967 |
| scene_14 | w050 | −1.763 |
| scene_14 | w100 | **+1.762** |
| scene_14 | w150 | **+0.958** |
| scene_14 | w200 | **+0.090** |
| scene_14 | w250 | −0.258 |
| scene_14 | w300 | **+0.928** |
| scene_14 | w350 | −1.301 |

Mean −2.262, **B lower in 10 of 14 windows, not 14 of 14**, and the sign is scene-dependent:
uniformly and largely negative in scene_13, mixed and small in scene_14. Part 2 reported only the
pooled mean and hid this.

## Audit result 4 — the mask change, decomposed correctly

Measured directly rather than inferred, with `q` the kept fraction of the candidate support:

```
q = 0.8485      R_kept = 6.8072      R_rejected = 15.0288
R_old - R_kept = (1 - q)(R_rejected - R_kept) = 1.2458
```

Part 2 stated "occlusion accounts for about 1.1 MAE of the floor". That used the wrong identity —
the difference is `(1-q)(R_rejected - R_kept)`, not `(1-q)·R_rejected` — and, more importantly,
**the rejected samples were never shown to be occlusions.** A depth disagreement or a failed
round trip can arise from sensor noise, calibration error, sampling, or genuine occlusion, and this
run does not separate them. The consequent claim that "the remainder is mostly depth noise, pose
error and nearest-neighbour sampling" is withdrawn as unsupported.

These masks should be called **reference-derived visibility/geometry-consistency masks**, not
visibility labels.

## Explicit withdrawals from Parts 1–3

1. **"Floor".** Condition A is not a lower bound on this quantity. It is the real-reference residual
   under this pipeline, and it carries calibration error, sampling error, image noise, exposure and
   view-dependent appearance, none of which a generator must reproduce. Scoring below A does not mean
   "better than reality".
2. **The spatial-frequency argument.** Pixel-value standard deviation is not spatial frequency; 93.9
   against 60.6 establishes no frequency difference, and sensitivity depends on local gradients,
   correspondence error, sampling phase and which samples survive the mask. The claim that the
   confound "works against the result" is withdrawn.
3. **B as a wrong-geometry control.** B changes appearance while **inheriting the reference
   geometry** by construction. It cannot show that incorrect geometry scores well. The strongest
   objection — "you replaced appearance while preserving the geometric correspondence, and a
   consistency score preferred the consistent appearance" — is fatal to that framing.
4. **The occlusion attribution and the residual-composition claim**, per audit result 4.
5. **"The 4.328 spread is larger than any plausible arm effect."** No arm has ever been evaluated
   with this metric. The spread is reference heterogeneity, not a detection limit. Pairing within
   window is required because the design is paired, not because an unmeasured effect is assumed
   small.
6. **The 27.5x ratio as a property of the evaluator.** B and C differ in error magnitude, spatial
   structure, clipping behaviour and interaction with the original residual; dividing by reference
   MAE does not equalise them, and L1 admits no decomposition into "baseline plus corruption". The
   raw scores are kept; the ratio is not promoted.
7. **"Any surface-consistent texture."** Two constructions were tested, not a class.
8. **The recommendation to retire this evaluator in favour of TSED.** They answer different
   questions. An epipolar constraint places a match on a line and does not determine position along
   it; TSED's own authors note insensitivity to correspondence error parallel to the epipolar line.
   A reference-depth mapping tests a specific position on that line. TSED also derives its matches
   from the generated imagery, so its evidence and coverage vary with appearance, whereas this
   evaluator's support is fixed. **Neither is a fidelity measure.**

## Standing conclusion

Retain the corrected implementation as an **auxiliary photometric-compatibility diagnostic on its
declared support**, with the real-reference residual and the coverage quoted alongside. Do not use it
as a standalone measure of recovered geometry. The published family — TSED (arXiv:2304.10700), GeCo
(arXiv:2512.22274), PDI-Bench (arXiv:2605.15185), SGC (arXiv:2603.19048), MEt3R — remains the
comparable reporting standard, and this project's failure to enumerate that family before building
its own is recorded in the principles rather than here.

**None of this is a research contribution.** It is a measurement contract: an implementation defect
was found and fixed, and the meaning of the number was narrowed. No generator output was evaluated.
