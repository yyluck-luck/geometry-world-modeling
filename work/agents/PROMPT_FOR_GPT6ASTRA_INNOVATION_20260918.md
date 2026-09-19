# Deep innovation search, grounded in measured mechanism

You are a senior researcher helping a one-student CVPR/ICCV-track project decide
what it should actually try to contribute. Think hard before answering. Search
the literature where it changes your judgement. Answer in English.

Do not produce a survey, a roadmap, or a list of plausible-sounding directions.
Produce a small number of falsifiable hypotheses that this project could test
with the resources it has, plus an honest statement of which are already
occupied.

## Hard constraints

- Consumer is **frozen**: VMem (arXiv 2506.18903), camera-conditioned
  autoregressive view generation with surfel-indexed view memory, pinned weights.
  No training, no fine-tuning, no architecture change. Ever, in this project.
- One H800. One generation of four 576x576 frames at 50 steps takes ~1 minute.
  Compute is not the constraint.
- Data: RGB-D Scenes v2 (two sequences, exposed) and TUM RGB-D. Small N is the
  binding constraint: at most ~14 paired windows from two sequences, and
  dependency grouping collapses them to one group.
- Everything is measured on a frozen RGB metric plus two auxiliary geometric
  measures. There is no human study and none is planned.

## What has actually been measured, byte-reproducibly

These are not literature claims. They are this project's own measurements, with
byte-identical replay across same-seed repeats and across compute nodes.

**M1. Context position dominates, ~2 dB.** Giving the generator the four
earliest history frames instead of the four most recent costs about 2.3 dB,
consistent across 2 sequences, 16 windows, 2 seeds (positive in 4/32 pairs).

**M2. A collapse cliff, not a graded multiplicity effect.** Going from 4 unique
context frames to 1 unique costs ~2.2 dB (positive in 3/32). Going from 4 unique
to 2 unique is indistinguishable from noise (15/32). Duplication is catastrophic
only at total collapse.

**M3. The first context slot is the ray gauge.** `get_cond` calls
`get_plucker_coordinates(extrinsics_src=all_w2cs[:1], ...)`, so the first context
camera defines the reference frame for every ray, and the translation scale is
derived from that same camera's distance to the centroid. Same context multiset,
different slot-0 frame, shifts PSNR by 0.55-0.87 dB in a single window.

**M4. Retrieval is rotation-gated in a way pose-proximity intuition misses.** On
a TUM room loop, the camera returns to earlier *positions* from frame ~350
onward (36-77 qualifying frames per 100-frame bucket), but every one is rejected
by a 20-degree rotation criterion until frame ~950. Same place, different
viewing direction.

**M5. The pinned retrieval carries persistent state that leaks across
evaluation arms.** `get_context_info` writes `self.initial_threshold = 1e8` in
its NMS-disabled branch, and the NMS-enabled branch assigns that attribute only
when the pipeline holds exactly five frames. At full bank size it does not
reassign, so an NMS-on call immediately after an NMS-off call **inherits 1e8**.
`reset()` does not clear the attribute. This project's own earlier comparison
was contaminated by exactly this: its "NMS-on" arm ran under a threshold leaked
from the preceding NMS-off call. Reproducing the call ordering restored
byte-identical agreement with the sealed artifacts, 28/28, which is how the
mechanism was confirmed.

**M6. Under that contaminated procedure, memory retrieval did not beat a fixed
context heuristic.** RGB difference +0.032 dB (9/16 positive); the NMS-on arm was
worse on a contrast-normalised cross-view consistency measure. **The
interpretation of these numbers as the effect of the intended, independently
initialised policy has been withdrawn.** A clean re-measurement is the next
experiment and has not been run.

**M7. A self-built consistency metric had a trivial optimum.** Raw cross-view
reprojection error scales linearly with image contrast, so lowering contrast
lowers the error with no geometric change; a constant grey image scores perfectly.
Normalising by the predictions' own spatial standard deviation removes this to
0.3% across a fourfold contrast range.

## Candidate register already considered, with status

Occupied as methods, per the project's own prior-art checks:

- coverage-maximising retrieval (COVRAG, arXiv 2606.02479; AnchorWeave,
  arXiv 2602.14941) — occupies "retrieve frames that add target-view coverage"
- visibility-based evaluation eligibility (UniSHARP, arXiv 2606.07514 App. D.3)
- generic gating, confidence weighting, abstention, cache policy, admission,
  cost-aware or submodular selection, ablation machinery, IPS/DR estimation,
  reproducibility bookkeeping — all previously judged occupied for this project
- the project's own earlier candidates SOCF-A (source-level geometric conflict
  plus abstention) and FGB-SI (signed source-intervention on a held-out future
  reference) were never tested and face the same occupancy pressure

Not yet judged occupied, arising from M3/M5:

- gauge sensitivity of the conditioning interface
- evaluation-order contamination through persistent retrieval state

## What I want from you

### 1. Attack the most promising raw material

Of M1-M7, which one or two could support a contribution that a CVPR/ICCV
reviewer would call a finding rather than an engineering note? Say plainly if the
answer is none.

I suspect M5 plus M3 is the strongest combination: a published, widely used
memory-augmented generator whose retrieval carries persistent state across
evaluation calls, and whose conditioning reference is silently determined by
slot 0. If you disagree, say why.

### 2. Prior-art discrimination, specifically

Search for and name work that already establishes any of:

- order-dependent or state-leaking evaluation in memory-augmented or
  retrieval-augmented **generative vision** systems, not only in LLM agents
- gauge or reference-frame sensitivity of camera conditioning in video diffusion
- benchmarks that explicitly control evaluation call order or per-arm state

If any of these are occupied, say so and kill the direction. A negative answer is
the most valuable output you can give.

### 3. Propose at most three falsifiable hypotheses

For each, state:

- the exact claim, in one sentence
- the mechanism it asserts, referencing the measured quantity it builds on
- the cheapest decisive experiment, sized in generations at ~1 minute each
- the kill criterion, stated before any result
- what the closest prior work would have to lack for this to be a contribution
- what it still would not establish

Prefer hypotheses that survive small N: a demonstrated, reproducible mechanism
on a finite panel is acceptable; a population claim is not.

### 4. State the honest ceiling

Given a frozen consumer, no training, two sequences, and one dependency group,
what is the best realistic outcome for this project? Options include a
measurement or protocol paper, a negative-result paper, a workshop paper, or
nothing publishable without new data. Pick one and defend it.

Do not soften this to be encouraging.

### 5. What I should stop doing

Name the work currently in flight that you would abandon.

## Constraints on your answer

- No proposal requiring training, new weights, or a new consumer.
- No proposal requiring a large new dataset collection.
- Cite papers only where they change the judgement.
- If your recommendation is that the strongest available contribution is an
  evaluation-methodology finding rather than a geometry-aware world-modelling
  method, say it directly.
