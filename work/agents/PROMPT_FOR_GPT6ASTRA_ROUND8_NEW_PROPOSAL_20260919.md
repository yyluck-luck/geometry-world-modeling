# Prompt for GPT-6 Astra — round 8: the constraints are being lifted. Scope a new multi-semester project aimed at a method paper.

Copy everything below the line.

---

You closed round 7 with: redefine the semester objective, do not enable training as a rescue, and
you could not nominate a trained mechanism from the existing measurements.

**The owner has accepted the semester reframing and is now asking a different question.** He is not
trying to rescue the current project. He is commissioning a **new proposal** with the blocking
constraints deliberately removed, aimed at a method paper at CVPR/ICCV/ECCV/NeurIPS level, and is
willing to fund a two-paper sequence across more than one semester.

**Your round-7 answer does not settle this question, because it was conditioned on constraints that
no longer apply.** In particular you wrote that training alone "leaves the evaluation bottleneck
unchanged" and that fitting on the current two exposed sequences would not give independent
evidence. **New data is now on the table as part of the same decision.**

I am asking for a scoped, costed project — not ideas.

## 1. What is now permitted

| previously fixed | now |
|---|---|
| no training or fine-tuning | **permitted**, including trained sub-components with a frozen generator |
| two exposed development sequences, one dependency group | **new data permitted**, including acquisition and qualification as part of the plan |
| one frozen consumer | **additional consumers permitted** |
| one semester | **multi-semester permitted**; a two-paper sequence is acceptable |
| generation budget of a few hundred forwards | **expandable**, to be justified in the plan |

Still fixed: no human-subject study; no claim unsupported by its evidence; no fabricated citations.

## 2. Corrections from round 7 that I have applied, so you do not re-derive them

- **"All occupiers are trained methods" was my error.** CamTrol (arXiv:2406.10126, *Training-free
  Camera Control for Video Generation*, ICLR 2025) is explicitly training-free. Verified.
- **"Trained versus frozen" is not binary.** LongLive-RAG trains a retrieval representation with a
  frozen generator; COVRAG combines explicit residual-coverage selection with trained memory
  conditioning. Components must be decomposed, not labelled wholesale.
- **"The training-free lane is measured-negative" was over-broad.** The −0.016 dB concerns one
  replacement policy, one consumer, one endpoint, eight eligible windows.
- **The 30% rubric component is not self-zeroed.** One full design → predeclaration → implementation
  → execution → adjudication cycle completed with a negative outcome; whether it satisfies the
  rubric is the instructor's judgement.

## 3. Assets that carry into a new project

- A byte-reproducible generation and scoring pipeline: sealed predictions, hash-verified receipts,
  passing byte-identity gates, predeclared thresholds, and a documented correction discipline.
- A fully characterised frozen consumer: complete call graph, retrieval ranking and NMS logic, camera
  normalisation (median mask, mean centring, first-camera scaling), Plücker conditioning with the
  first context camera as reference, joint 8-frame denoising, and generated-frame writeback paired
  with the **commanded** camera. Public HEAD verified byte-identical to the pinned snapshot.
- A verified occupancy map across roughly twenty papers, with verbatim quotes and cell-level numbers.
- Two evaluators, both qualified and scoped: a reference-warped reprojection diagnostic shown to be
  fidelity-blind by an exact channel-permutation invariance, and a pose evaluator identified as a
  standard instance of the CamCo/CamI2V normalisation family.
- A measured, unexploited observation on the existing panel: the retrieval policy's advantage over a
  fixed-offset context is **+2.950 dB at target offset +60 and −0.321 dB at +105**, 13/14 windows
  positive at the nearest target and 5–7/14 at the rest. Whether this is occupied has not been
  checked.

## 4. Verified occupancy — do not propose these as the contribution

VRAG arXiv:2505.21996v4 · Context as Memory arXiv:2506.03141 · RAGME arXiv:2504.06672 ·
LongLive-RAG arXiv:2606.02553 · COVRAG arXiv:2606.02479 · PRoPE arXiv:2507.10496 ·
EscherNet arXiv:2402.03908 · TTAB arXiv:2306.03536 · TSED arXiv:2304.10700 · GeCo arXiv:2512.22274 ·
PDI-Bench arXiv:2605.15185 · SGC arXiv:2603.19048 · MEt3R arXiv:2501.06336 ·
SysCON3D arXiv:2605.18754 · CamTrol arXiv:2406.10126 · PosePilot arXiv:2505.01729v2 ·
CamDirector arXiv:2603.02256v1 · MotionCtrl · CameraCtrl · CamCo · CamI2V · Cavia · CameraCtrl II ·
WorldScore · CamVerse · SANA-WM · Matrix-Game 3.5.

Closed internally: GRC risk-calibrated memory selection; SOCF-A; FGB-SI; duplicate-context-slot
repair; T1-5 pose-label feedback (closed on feasibility — the pinned source exposes no camera
relabelling interface).

## 5. What I need, in this order

**Q1. Name ONE mechanism for the primary method paper.** Not a menu. State the claim a reviewer
would see, the computation it changes, and — against the specific occupiers in §4 — the reason it is
not already covered. You wrote in round 7 that you could not supply this sentence under the old
constraints. **With training and new data permitted, supply it or state that it still cannot be
supplied.**

**Q2. Give the evaluation design that could actually support it.** In round 7 you gave planning
figures: dozens of independent test environments rather than more windows on two sequences, and an
illustrative n ≈ 49 at δ = 0.20 dB with a scene-level SD of 0.50 dB. **Turn that into a concrete
data plan**: which public datasets, how many scenes for development versus untouched evaluation, what
qualification each must pass, and what the acquisition and licensing risks are. Name datasets that
exist.

**Q3. Give the baseline matrix.** You specified the structure in round 7 — intervention removed,
strong simple context policies, closest compatible published mechanism, mechanism-specific control,
matched information and computation. **Instantiate it for the mechanism you named in Q1**, and say
which of the §4 systems must actually be reproduced versus cited, given incompatible interfaces.

**Q4. Assess the two-paper sequence.** The owner will accept two papers. My proposed split is:
 * **Paper 1** — the bounded empirical study already supported by existing assets, at TMLR level;
 * **Paper 2** — the method paper from Q1.
Is that the right split? Does Paper 1 help or hurt Paper 2 — does it burn the interesting material,
or does it establish the measurement foundation Paper 2 needs? Would a different split be stronger?

**Q5. Cost and timeline, honestly.** Phases, GPU-hours, data-acquisition lead time, and the point in
each phase at which the project should be killed if a gate fails. Include the risk that the
mechanism in Q1 fails its own predeclared test, as the previous one did.

**Q6. The question I most need answered.** If, with training, new data, additional consumers and
multiple semesters all permitted, **you still cannot name a differentiated mechanism**, say so
directly. That would mean the obstacle was never the constraints, and the owner needs to hear it
before committing another semester and a data budget.

Do not soften a negative answer. Do not fabricate identifiers. Where you cannot verify occupancy,
write UNVERIFIED and name what must be read.
