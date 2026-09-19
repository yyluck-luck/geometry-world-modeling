# Prompt for GPT-6 Astra — round 7: the owner wants a PhD-level paper. Tell him whether that is reachable from here, and what it costs.

Copy everything below the line.

---

You have reviewed this project six times. Each round you narrowed a claim, killed a direction, or
caught an overstatement, and I acted on all of it. **The owner has now stated his objective
explicitly: a PhD-level paper.** I am asking you to assess that objective against the actual
evidence, not against effort.

I will state the position without spin, including the parts that argue against the objective.
**If your honest answer is that a PhD-level contribution is structurally unreachable under these
constraints, say so plainly and name what would be reachable instead.** That answer will be acted
on.

## 1. What the original proposal promised, and what exists

The course proposal promised five things, with these grading weights: literature and problem
definition 15%; baseline and geometric-failure characterisation 15%; **design and integration of a
geometric-consistency mechanism 30%**; experimental evaluation 25%; final report 15%.

| component | weight | honest state |
|---|---|---|
| literature / problem definition | 15% | **Strong.** ~15 papers read at primary source with verbatim quotes and cell-level numbers. The occupancy map has repeatedly killed my own directions. |
| baseline / failure characterisation | 15% | **1 of 5 required factors.** The proposal requires camera motion, **object motion, sparse observation, occlusion, re-appearance**. My panel is static-scene **forward extrapolation only**. No revisits, no object motion, no occlusion factorisation. |
| **mechanism design and integration** | **30%** | **No deliverable.** Five candidates, all closed. Detail below. |
| experimental evaluation | 25% | **High protocol quality, wrong object.** 116+ sealed generations, byte-reproducible, predeclared thresholds, five documented self-corrections — but evaluating a frozen baseline's configuration, not an integrated mechanism. |
| final report | 15% | **Finalised.** Eight sections plus six appendices, LaTeX/PDF, self-verifying artefact bundle. |

## 2. The 30% component: five candidates, five closures

| candidate | outcome |
|---|---|
| GRC-Memory (risk-calibrated memory selection) | blocked at S91; S99 measured the low-disagreement advantage as unstable and losing to a confidence baseline; claim stopped |
| SOCF-A (source-conflict feature predicting future loss) | stopped before execution — proposed a selection policy before anything was established about what the consumer responds to |
| FGB-SI (source-intervention future-geometry measurement) | stopped before execution |
| **duplicate-context-slot repair** — the only one fully executed | **ran and failed its own predeclared test: −0.016 dB against a +0.20 dB retention threshold**, across the 8 of 10 affected windows where the policy offers a replacement. Threshold not lowered, policy not changed, no subgroup elevated. |
| T1-5 (pose-label feedback in self-generated history) | **closed on feasibility, zero GPU.** The pinned source writes `self.c2ws` in exactly two places — `initialize` and `.append` — and exposes **no setter, mutator, or relabelling method**. Routing corrected labels into the native surfel/retrieval path is impossible without modifying upstream source, which is a fixed constraint. |

**Net: zero mechanisms integrated with a demonstrated benefit.** One full design→predeclare→
implement→execute→adjudicate cycle was completed and returned a negative.

## 3. The structural problem I want you to address directly

Every work that occupies the adjacent space is a **trained** method:

VRAG (arXiv:2505.21996v4), Context as Memory (arXiv:2506.03141), RAGME (arXiv:2504.06672),
LongLive-RAG (arXiv:2606.02553), COVRAG (arXiv:2606.02479), PosePilot (arXiv:2505.01729v2),
CamDirector (arXiv:2603.02256v1).

The untrained, input-side lane is not hypothetical — **I walked it, and it produced −0.016 dB.**

The measurement/evaluation lane was also walked: the geometry evaluator was qualified, found to be
fidelity-blind by an exact channel-permutation invariance, and demoted; and the family it belongs to
(TSED arXiv:2304.10700, GeCo arXiv:2512.22274, PDI-Bench arXiv:2605.15185, SGC arXiv:2603.19048,
MEt3R) was found to predate it. The pose evaluator is likewise a standard instance of an occupied
family (MotionCtrl, CameraCtrl, CamCo, CamI2V, Cavia, CameraCtrl II, WorldScore, CamVerse, SANA-WM,
Matrix-Game 3.5). Two independent reviews ruled the evaluation-methodology genre down to a technical
report.

**So: the untrained mechanism lane is measured-negative, the evaluation lane is occupied, and the
mechanism lane that is open requires training.**

## 4. Fixed and relaxable

**Fixed unless the owner changes them:** one frozen consumer, no upstream source modification, no
human-subject study, two exposed development sequences in one dependency group, so no population
claim is available from them.

**Relaxable with the owner's written approval:** training or fine-tuning; new data; new or
newly-enabled evaluators; generation budget; additional frozen models.

**Time:** a one-semester independent research project, already substantially elapsed.

## 5. What I am asking

**Q1. Is a PhD-level contribution reachable from this position, and under which single relaxation?**
Rank the three routes I can see by (expected contribution) / (cost and risk), and add any I have
missed:
 (A) new data to cover the four missing failure factors — closes the 15% gap, does **not** close the 30%;
 (B) allow training — the only route that touches the 30%, but that is a different project's scale;
 (C) reframe the deliverable around the proposal's fifth promise, the quality/geometry/consistency/
     cost trade-off analysis — zero GPU, explicitly abandons the 30%.

**Q2. If the answer is "not reachable", what IS reachable from these assets?** The assets are: a
byte-reproducible generation and scoring pipeline with sealed predictions and passing byte-identity
gates; a fully characterised frozen consumer including its call graph, retrieval logic, camera
normalisation and a verified released-path provenance discrepancy; a verified occupancy map across
~15 papers; two qualified-and-scoped evaluators; and a documented correction discipline. **Name the
strongest paper those assets can support, and its realistic venue.**

**Q3. Is there a mechanism question that is untrained, admissible under the fixed constraints, and
not occupied — that I have not asked?** I have exhausted my own generation of these. Two ideation
passes produced zero admissible candidates. If you also cannot name one, say so; that is the
decisive answer.

**Q4. What is the honest minimum for "PhD-level" in this subfield in 2026?** I want the standard
stated concretely — number of scenes, number of consumers, whether a trained component is
effectively mandatory, what counts as an adequate baseline — so the owner can decide against a real
target rather than an aspiration.

**Q5. If training is allowed, what is the single highest-value trained mechanism given everything
measured here?** Not a survey of options — one, with the reason it is not already occupied by the
seven trained works above, and what its smallest decisive experiment would be.

Do not soften a negative answer, and do not propose anything requiring a human study or upstream
source modification. If the honest conclusion is that the owner should redefine the objective rather
than pursue it, state that as the recommendation.
