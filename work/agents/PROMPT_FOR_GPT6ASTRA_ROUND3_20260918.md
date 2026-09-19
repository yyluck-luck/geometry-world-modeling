# Prompt for GPT-6 Astra — round 3: the predeclared test failed. Confirm closure or name what is left.

Copy everything below the line.

---

You ruled: if the repair came back below 0.20 dB, report the value and close the branch — do not
lower the threshold, change the replacement policy, or elevate a favourable subgroup. **It came
back at −0.016 dB.** I am reporting it and I have changed nothing. This message asks you to
confirm closure or to name, specifically, what is left.

I also ran the primary-source pass you implied was necessary. Every occupancy verdict you gave me
was relayed; I downloaded and read all of them and located the exact cited numbers in the papers.
Results in Part 3. One of your citations needed a correction in my favour and one produced
something you did not have.

## Part 1 — I acted on all three of your corrections

**Sign.** You were right and this was my worst error of the day. +0.242 dB is positive. I had
written "does not beat fixed-offset context" and "a bounded negative result." Both retracted, with
correction notices on the affected files. Correct statement: across 14 fixed windows and 2 fixed
seeds, shipped retrieval achieved a mean PSNR advantage of **+0.242 dB** over fixed-offset
context, SD across windows 1.270, median +0.385, 8/14 positive, range −2.073 to +2.055.

**Inference.** SE = 0.340 and t = 0.71 withdrawn. I declared windows a finite panel and then
divided by sqrt(14); that was incoherent. No SE, t, CI, significance test, equivalence test or
bootstrap appears anywhere now. SD is reported only as heterogeneity.

**Scope.** "Held-out" narrowed everywhere to "exposed development sequences whose target frames
are held out from conditioning."

## Part 2 — your two implementation objections, both checked

**Candidate pool.** You were right that `pipeline.py:492` computes
`num_retrieved_frames = min(context_num_frames + 10, len(timestep_weights))`, so a matching
four-element prefix would not certify the remainder. I did not answer this with the argument that
a 12-frame bank saturates the min. I measured it: the ranked list was read at `context_num_frames`
5, 6 and 7 — three different pool requests — and the lists were **exactly nested in every window**,
e.g. `[11,11,10,9,8] ⊂ [11,11,10,9,8,3] ⊂ [11,11,10,9,8,3,4]`, with the shipped `[11,11,10,9]` as
prefix. Index 11 appearing twice is the collision itself: it is simultaneously the surfel-nearest
candidate and the most recent stored frame.

**Order conflation.** You were right that my first repair produced `(a,a,b,c) → (a,b,c,d)`, mixing
a content change with a position change. I added the in-place arm `(a,a,b,c) → (a,d,b,c)` and made
it primary. I did **not** delete or rewrite the first arm; it is retained and reported, and the
specification was written down before any repair output was scored.

## Part 3 — primary-source verification of your occupancy verdicts

All confirmed. Exact quotes and cell values located in the papers.

- **VRAG 2505.21996v4** — verbatim: *"The History Buffer method performs poorly, with an SSIM score
  of 0.188, indicating that naive historical frame retrieval without effective in-context training
  fails to maintain long-term consistency."* Occupies "historical retrieval need not beat
  recent-window conditioning." I also preserved your qualification that this is not an across-metric
  negative.
- **Context as Memory 2506.03141** — ablation verified cell by cell: Random 17.70/17.07,
  FOV+Random 19.17/17.47, **FOV+Non-adj 20.11/18.19**. A published redundancy-selection ablation
  in the same units I use, worth +0.94 and +0.72 dB.
- **RAGME 2504.06672** — verbatim: *"The WebVid10M dataset contains duplicate or highly similar
  videos; to prevent the model from processing redundant information..."* plus a named
  deduplication strategy, in retrieval-augmented video **generation**.
- **LongLive-RAG 2606.02553** — verbatim: *"off-the-shelf image features tend to retrieve
  temporally local neighbors..."*, addressed by a loss that *"suppresses redundant local
  similarity."*
- **COVRAG 2606.02479** — verified: FoV+Independent 0.141/0.198 versus target-view
  coverage+Independent 0.149/0.210, recovered to 0.100/0.156 by residual selection.
- **PRoPE 2507.10496** — verbatim: *"They are sensitive to the arbitrary choice of reference frame,
  which can hinder generalization."*
- **TTAB 2306.03536** — episodic versus accumulated adaptation confirmed.

I have killed every corresponding direction in my register.

**One thing you did not have.** The VMem paper itself states: *"To avoid oversampling repeatedly
visited regions, we apply a non-maximum suppression algorithm that reduces redundancy in memory and
promotes broader scene coverage among the top-K."* The config sets it true. The released interface
disables it at both call sites. The release contains **only the demo** — `app.py`, `navigation.py`,
`modeling/`, `utils/` — and **no evaluation or benchmark script**, so the configuration behind the
paper's tables cannot be determined from the release. I state this as a released-demo-path
observation only and never as a claim that the published results are wrong.

I also verified your point about scope. The paper's memory demonstration is §4.3, *"Long-term view
generation with revisitations"*, and its K=4 selector ablation reports temporal selection at
**7.52 dB** against VMem at **14.82 dB**. My fixed-offset arm scores about **14.5 dB**. My panel is
forward extrapolation without revisits. I do not reproduce, test or contradict that experiment.

## Part 4 — the complete final numbers

Seeds folded within window first. No inferential statistics anywhere.

| contrast | n windows | mean | SD | positive |
|---|---|---|---|---|
| shipped retrieval − fixed offset | 14 | +0.242 dB | 1.270 | 8/14 |
| clean NMS-on − fixed offset | 14 | −0.485 dB | 1.489 | 6/14 |
| clean NMS-on − shipped retrieval | 14 | −0.726 dB | 1.210 | 5/14 |
| **INPLACE repair − shipped** | **8** | **−0.016 dB** | **0.309** | **3/8** |
| REFILL repair − shipped | 8 | −0.032 dB | 0.304 | 3/8 |
| INPLACE − REFILL (pure order) | 8 | +0.016 dB | 0.037 | 5/8 |

Leak effect (clean − leaked), stratified by a census fixed before any scoring:
**NULL n=2: +0.000 dB** (byte-identical, sha256-verified — this was also the gate that made reusing
sealed outputs admissible, and it passed); **PERMUTATION n=4: −0.015 dB**; CONTENT n=8: +0.436 dB.

No-op gate on the repair: 8/8 byte-identical to the sealed shipped output.

The only pattern I can see across three independent interventions on the same consumer:

| intervention | change to context | effect |
|---|---|---|
| reorder the same multiset | none — identical frames | 0.015 dB |
| replace a duplicate with the next ranked **nearby** frame (105 → 90) | one nearby frame | 0.016 dB |
| enable NMS, which selects a **distant** frame (105 → 55) | one distant frame | −0.726 dB |

## What I need from you

**Q1. Confirm closure, or name what is left.** By your own rule this branch is closed. If you
agree, say so plainly and I will write the technical report and stop. If you think something
remains, name the single experiment and what it would establish — not a direction, one experiment.

**Q2. Is the three-intervention pattern in the last table a result, or an artefact of scale?**
0.015, 0.016 and −0.726 dB. The first two are near zero and the third is not. My concern is that
this is just "bigger perturbation, bigger effect" restated, with no content. Tell me if it is
empty. If it is not empty, what is the smallest control that would make it a claim rather than a
description, given a frozen consumer, no training and no new data?

**Q3. Is the released-path provenance discrepancy reportable, and to whom?** The paper describes
NMS as part of the method; the released demo disables it at every call site; the release ships no
evaluation script. I believe the only honest statement is about the demo path. Is that worth a
paragraph in a technical report, an issue to the authors, or nothing? Tell me if reporting it at
all risks being read as an accusation.

**Q4. What is the correct artefact and what must it NOT say?** Give me the section list for a
technical report that a supervisor can assess, and the specific sentences that would be
overclaiming. I have already overclaimed once today in the negative direction and once earlier by
calling a contaminated arm a memory result; I would rather you write the prohibitions explicitly.

**Q5. Is there a different question worth asking with the remaining compute, under the same fixed
constraints?** Frozen consumer, no training, no new data, two exposed sequences, PSNR on RGB only,
roughly a few hundred generations available. If the answer is that no question worth asking fits
inside those constraints, say that — it is the answer I most need and the one I am least able to
reach on my own.

Do not propose anything requiring training, fine-tuning, new weights, new datasets, or a human
study. Do not soften a negative answer.
