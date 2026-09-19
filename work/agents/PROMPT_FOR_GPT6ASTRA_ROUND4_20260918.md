# Prompt for GPT-6 Astra — round 4: I under-specified the constraints in round 3. Re-answer Q5.

Copy everything below the line.

---

You answered round 3 with: close the branch, write the technical report, and *"I cannot name a
remaining experiment that I would recommend spending the few hundred generations on."*

I did all of it. The report is written, the denominator is reconciled to "8 of 10", the
provenance is corrected, the branch is closed.

**But I gave you an incomplete constraint set, and the omission is material.** I described the
scope as "two exposed development sequences, PSNR on RGB only, a fixed forward panel." I did not
tell you that this project also holds a **frozen, fixture-tested, human-approved revisit protocol
on a separate sequence that was never launched** — and that the entire project has never measured
the one regime where the consumer's memory is supposed to matter.

I am asking you to re-answer Q5 with the real constraint set. I am also telling you up front why
the obvious answer may still be no.

## Part 1 — you were right about the provenance, and the public repo confirms it

I checked the live repository, not just my snapshot. Public HEAD
`39291e4f272f6b4f270691d930926ab5930f942e` (2025-07-25). My pinned `navigation.py` is
**byte-identical** to it (sha256 `6d267365d5dcccf9f7cd6d535f19f80521f60a9634dffb35b9af398407389fcf`),
so there is no snapshot divergence to blame. The three call sites are at lines 185, 234 and **321**,
and the third one — `_turn`, reached from `app.py:208/210` — passes no NMS argument. The non-`extern/`
Python files at HEAD are exactly `app.py`, `navigation.py`, `modeling/*`, `utils/*`: **no evaluation
script**, confirmed.

My four claims that you flagged are retracted in the report, and the procedural lesson is recorded:
searching a parameter name finds only the sites that override it; the count of overrides is never the
count of call sites.

One consequence that cuts *toward* the experiment below: **turning is the operation that enables
NMS, and turning is what you do when you look back at a region you saw before.** The revisit regime
and the NMS-enabled path are the same path.

## Part 2 — what I withheld: the revisit protocol

The project's whole measured record is forward extrapolation: targets beyond the end of the bank,
no return to previously observed regions. VMem's own memory demonstration is the opposite regime
(§4.3, revisitations; K=4 temporal selection 7.52 dB versus VMem 14.82 dB). **I have never measured
that regime.**

There is a complete apparatus for it, built and frozen on 2026-09-17, never run:

- frozen protocol, sha256 `bfcb5d98…`, plus two addenda `7b28bb3c…` and `19fa9d15…`
- episode attribution, dependency grouping, per-window container isolation with a canary that
  asserts its own limits (16/16), dataset-keyed depth decoding that refuses unregistered datasets,
  a contrast-invariant geometry metric, CameraCtrl-protocol pose metrics (4/4)
- arm matrix: `recency`, `early_visit`, `memory_nms_on`, `memory_nms_off`
- primary contrast declared **before** any data contact: `memory_nms_on − recency`
- budget 16 windows × 4 arms × 2 seeds = **128 generations**
- human approval recorded 2026-09-17, after a readiness review
- declared stopping rule: **fewer than three independent revisit episodes → UNTESTABLE, budget not
  spent**

## Part 3 — why it was never launched, with the number

The stopping rule fired. I re-ran the feasibility gate today with the **corrected** episode
detector (an earlier version split one continuous return into three nominal episodes; the fix
merges on return-frame contiguity using the pre-declared 30-frame tolerance, with no retuning, and
the defective version is retained as a separate file):

```
sequence: TUM rgbd_dataset_freiburg1_room   (metadata only; no pixel decoded)
revisit windows found            : 8
control windows found            : 8
independent revisit episodes     : 2      required: 3
revisit dependency groups        : 1
verdict: UNTESTABLE_INSUFFICIENT_INDEPENDENT_REVISITS
```

Qualifying revisits, translation/rotation against thresholds 0.30 m / 20.0°:
`0.293 m / 18.8°`, `0.203 m / 19.6°`, `0.271 m / 19.5°`. Every one is just inside the rotation
threshold.

So all 8 revisit windows come from **one dependency group** and **two** leave-and-return events.
The protocol refuses, and the 128 generations were correctly not spent.

**The binding constraint on this project is data, not ideas.** That is the honest version of what
I was going to ask you as "what innovation is left."

## Part 4 — what I would be asking you to approve

A single, bounded constraint relaxation: **one additional sequence, selected on metadata alone,
qualifying if and only if it yields ≥3 independent loop-closure events under the already-frozen
criteria.** No training, no new weights, no metric change, no protocol change, no new arm.

Everything else stays exactly as frozen. Two things from today would be wired in before launch:

1. **`isolate_arm_state` per arm.** The frozen arm matrix iterates `memory_nms_off` and
   `memory_nms_on` on one pipeline object — precisely the ordering that produced this project's
   cross-arm threshold leak. Without the isolation routine (order-invariance gate 11/11, including
   a non-vacuity assertion), that run would reproduce the contamination at 128-generation scale.
2. **Selection metadata recorded per window**, including distinct-frame delivery, since the
   duplicate-slot collision will occur here too and should be observed rather than discovered
   afterwards.

## What I need from you

**Q1. Does the revisit protocol change your round-3 answer?** You said no experiment was worth the
generations *under the constraints I gave you*. Those constraints omitted an approved, frozen,
never-run protocol for the one regime the project has not measured. Re-answer with that included.
If your answer is still no, say so plainly.

**Q2. Is "one new qualified sequence" a justified relaxation, or futile?** My own concern is that
even a qualifying sequence gives **one dependency group**, and you have already ruled that one
dependency group cannot establish an average effect. Does measuring a *different regime* buy
anything that a *different scene in the same regime* would not — or is the regime gap a real gap
and the dependency-group limit a separate, unfixable one? Be specific about which of the two is
binding.

**Q3. How do I handle a pre-declared primary contrast whose rationale is now partly falsified?**
`memory_nms_on − recency` was declared before data contact. Its stated rationale was (a) "NMS-on is
VMem's shipped default" — which I have now corrected to "NMS-on is the configuration value and the
effective setting for the turning path" — and (b) "it was already the stricter of the two in earlier
development runs", which referred to the **−0.729 dB figure that is now withdrawn as contaminated**
(the clean value is −0.485 dB). Changing the primary now would be exactly the post-hoc arm
promotion the protocol forbids. Keeping it means keeping a declaration whose empirical basis was
withdrawn. Which is correct, and what exactly must be disclosed?

**Q4. What would a revisit result have to look like to be worth anything?** VMem's own ablation
reports 7.52 dB for K=4 temporal selection against 14.82 dB for its method. My `recency` arm is a
stronger baseline than that comparator, and on the forward panel my fixed-context baseline scored
about 14.5 dB. Given that, what interaction magnitude would be interpretable rather than noise, and
what would it establish that the published ablation has not already established? If the honest
answer is "it would at best reproduce a known result on one scene", say that.

**Q5. If the answer to Q1 and Q2 is no, is this project finished?** I need to hear that explicitly
if it is true. The alternative I can see is that the remaining work is not experimental at all —
writing up, the provenance question to the authors, and stopping. Tell me if that is the whole
remaining scope.

Unchanged constraints: frozen consumer, no training, no fine-tuning, no new weights, no metric
invention, PSNR on RGB plus the already-frozen geometry and pose metrics, roughly a few hundred
generations. New data is requestable but only with prospective written approval and only on
metadata-based qualification, never chosen after seeing outcomes. Do not soften a negative answer.
