# Research brief: enumerate the camera-pose metric family, and test one specific lead against it

Copy everything below the line.

---

# WHY THIS TASK EXISTS

I am auditing a frozen, camera-conditioned latent-diffusion view generator. Twice in one day I built
or planned something without first enumerating the **family** of established methods on its task
line, and each time an established method already existed:

- I built a cross-view reprojection geometry evaluator. **TSED** (arXiv:2304.10700), **GeCo**
  (arXiv:2512.22274), **PDI-Bench** (arXiv:2605.15185), **SGC** (arXiv:2603.19048) and **MEt3R** all
  target geometric consistency of generated views. GeCo's stated scope even covers the specific
  defect I spent a day discovering in my own implementation — occlusion-inconsistency in static
  scenes.
- The failure was not "I missed one paper". It was **stopping at the first hit**.

I now have a second evaluator in the same state: **built, unit-tested, never run, never compared to
the literature.** It extracts camera poses from generated frames and reports rotation and translation
error in the CameraCtrl protocol. Before it is used, I need its family.

**Do not repeat my error. Enumerating one method is a failed answer.**

---

# PART 1 — VERIFIED GROUND TRUTH ABOUT THE SYSTEM

Taken from the pinned source, not inferred from names. A previous ideation pass hallucinated an
entire research track by guessing the architecture from terminology. **If a proposal contradicts this
table, it is void.**

| fact | verified value |
|---|---|
| model class | camera-conditioned **latent diffusion**. **Not** token-autoregressive |
| image autoencoder | `AutoencoderKL`, continuous and KL-regularised. **No VQ, no codebook anywhere in the model directory** |
| sampler | `DDPMDiscretization`, `DiscreteDenoiser(num_idx=1000)`, classifier-free guidance |
| one forward pass | **8 frames denoised jointly**: 4 context + 4 target, `input_masks = [T,T,T,T,F,F,F,F]` |
| autoregression | **across generation calls**, not within an image. Generated frames are written back into the memory bank |
| **writeback** | the generated frame is stored paired with the **commanded** target camera, not a measured one |
| memory | surfel cloud; retrieval renders surfels from an averaged query pose, ranks candidates by geodesic camera distance, then applies non-maximum suppression |
| camera conditioning | Plücker coordinates, **first context camera as reference** |
| camera normalisation | median-based outlier mask, subtract the **mean** of surviving centres, scale by `camera_scale / ‖first camera‖`. **Not extrema-based** |
| "frozen consumer" | **my project constraint** — I may not train the model. It is not a component of the architecture |

---

# PART 2 — PRIMARY TASK: enumerate the camera-pose / trajectory metric family

For **generated** video or generated novel views, enumerate how the field measures whether the
realised camera motion matches the commanded camera motion.

Cover at least: the CameraCtrl-style protocol (relative-to-first-frame, furthest-frame translation
normalisation, RotErr/TransErr); trajectory error conventions imported from SLAM and odometry (ATE,
RPE, and their alignment conventions); anything used by recent camera-controlled video generation
work; and anything used by world-model or 4D-generation benchmarks.

For each, I need:

```
Name / arXiv id or venue+year
Exact definition, quoted, with the section it comes from
What supplies the poses being compared (estimated from generated frames? commanded? both?)
Which estimator, and whether the paper qualifies that estimator
Alignment / normalisation convention, and what it is invariant to
Declared failure handling: what happens when extraction fails or is unreliable
Verification: VERIFIED (I read the method/experiments) | ABSTRACT-ONLY | UNVERIFIED
```

**Then tell me where a reference-pose-based rotation/translation error sits inside that family, and
whether it adds anything the family does not already have.** I expect the honest answer may be "it is
a standard instance and should simply be reported as such". That is a useful answer.

---

# PART 3 — THE ONE QUESTION THAT IS BOTH A GATE AND A POSSIBLE LEAD

This is the highest-value item in this brief.

A generated image need not admit a well-defined rigid camera at all. If the generator produced a
non-rigid distortion of the scene, a pose estimator will still return a pose — it will fit one — and
any "error" computed from it measures the fit, not a physical camera.

**Search for published work that addresses when camera pose is identifiable from generated imagery**,
and how that is tested. Specifically:

1. Does any work **qualify its pose extractor on generated frames**, as opposed to on real clips with
   known poses? Real-clip calibration is standard; qualification on generated content is what I need.
2. Is there a published **identifiability or observability test** — low parallax, insufficient depth
   variation, insufficient static correspondence — applied to generated views before a pose number is
   reported?
3. Does anyone report **how often extraction fails** on generated video, and keep those cases in the
   denominator rather than dropping them?
4. Has anyone measured whether the **rigid-camera assumption itself** holds for generated frames, for
   example by testing whether the correspondences admit a single rigid motion?

**A well-supported negative answer to any of these is the most valuable output of this brief.** It
would simultaneously tell me that my gate has no published precedent to borrow, and identify a gap.

Do not assert a gap from absence of search results. If you cannot establish occupancy, say
`UNVERIFIED` and name what you would need to read.

---

# PART 4 — INNOVATION EXPLORATION, CONSTRAINED

Two previous ideation passes produced, between them, zero admissible candidates, and two independent
reviews ratified stopping. The failures were: inventing constraints instead of using mine; ignoring
the required schema; re-proposing occupied claims; and proposing work that needs training or
architecture changes when both are forbidden.

## My actual constraints

**FIXED, not relaxable.** No new architecture. No modification of the upstream source. No
human-subject study. Two exposed development sequences in one dependency group, so no population
claim is available from them.

**RELAXABLE only with my prior written approval, and you must state which a candidate needs:**
training or fine-tuning; new data; a new or newly-enabled evaluator; extra generation budget;
additional frozen models.

## Already occupied — verified at primary source, do not re-propose

| claim | occupied by |
|---|---|
| historical retrieval need not beat recent-window conditioning | VRAG, arXiv:2505.21996v4 |
| a bounded context budget is wasted on redundant/adjacent frames; diversity helps | Context as Memory, arXiv:2506.03141 |
| deduplicating near-duplicate retrieved content | RAGME, arXiv:2504.06672 |
| retrieval collapses toward temporally local neighbours | LongLive-RAG, arXiv:2606.02553 |
| finer geometric evidence does not guarantee better independent selection | COVRAG, arXiv:2606.02479 |
| camera-conditioning reference-frame / gauge dependence | PRoPE, arXiv:2507.10496; EscherNet, arXiv:2402.03908 |
| geometric consistency metrics for generated views | TSED, GeCo, PDI-Bench, SGC, MEt3R |
| evaluation state, episodic versus accumulated | TTAB, arXiv:2306.03536 |

**Also closed internally:** duplicate-context-slot repair (ran, failed its prespecified threshold,
closed); slot-0 ray-gauge routes (impossible in source); the state leak as a contribution; and three
source-conflict/risk-calibrated selection proposals stopped before execution.

## What I want from this part

**Ground the exploration in Part 3.** The strongest lead I currently hold is that generated frames
are written back into the memory bank **paired with their commanded camera**, so if a generated image
does not actually correspond to that camera, the bank accumulates a mislabelled image-camera pair
that feeds later retrieval and surfel construction. The source proves how the label is written; it
does **not** prove any image deviates. That premise is untested.

Tell me: **what would have to be true for that to be a real effect, what published work bears on it,
and what is the smallest experiment that could kill it.** If the honest answer is that it is either
already occupied or unmeasurable under my constraints, say so.

Beyond that one lead, propose additional candidates only if they survive the schema below. **Five
well-verified candidates beat fifty.** An honest shortfall is acceptable; padding is not.

```
Claim (the finding a paper would assert, not a topic)
Mechanism, at the level of the actual computation, and which Part 1 fact it depends on
Nearest prior work: real id, with the specific passage or number that makes it near
Occupancy: OCCUPIED / ADJACENT / OPEN     Verification: VERIFIED / ABSTRACT-ONLY / UNVERIFIED
Relaxations needed, and therefore ADMISSIBLE or INADMISSIBLE
Smallest decisive experiment, with arms
What must be true for it to work
Kill criterion
Venue fit and cost
```

---

# HARD RULES

1. **Never invent an identifier, title, author or number.** If you cannot verify, write `UNVERIFIED`
   and say what you would need to check. A fabricated citation is worse than an empty field.
2. **Abstract-only reading is never an occupancy verdict.**
3. **Enumerate families, not single hits.** For any "the established method is X", list what else
   occupies that space and why X is the right comparator.
4. **A trained method in an adjacent domain does not automatically occupy an untrained mechanism
   here, and porting a standard method into this system is not automatically novel.** Argue both.
5. If your honest conclusion is that Part 3 has no gap and Part 4 has no admissible candidate, **say
   so plainly.** That will be acted on, not argued with.
