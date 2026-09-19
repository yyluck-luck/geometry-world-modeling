# Prompt for GPT-6 Astra — round 9: three structural risks to the lineage proposal, one of which may kill the premise before Phase 1

Copy everything below the line.

---

I accepted the round-8 proposal and recorded it. Before spending the 800 GPU-hours you authorised
for Phases 0–1, I checked something in the pinned source and existing metadata. **One finding may
make the lineage claim fail by construction.** I want it assessed now, not in Phase 3.

## Risk 1 — ancestry may be very nearly a deterministic function of frame age

Your baseline B8 is "full error-moment fusion **without ancestry**, retaining image, pose and age
descriptors", and it isolates the lineage contribution. Your retention rule requires **≥ +0.05 dB
incremental over B8, or the lineage claim fails**.

Here is the problem. In the pinned source, the NMS-disabled selection path unconditionally appends
the most recent stored frame:

```
selected_indices.append(sorted_frames[0])          # surfel-nearest candidate
if not use_non_maximum_suppression:
    selected_indices.append(len(self.c2ws) - 1)    # the most recent stored frame
```

Measured on my existing 14-window census, the selected bank positions were:

```
10 of 14 windows : [11, 11, 10, 9]     (11 = most recent; the nearest candidate and the most
                                        recent frame coincide, so the newest frame is duplicated)
 1 window        : [ 8, 11,  9, 10]
 3 windows       : [ 0, 11,  1,  2]  /  [ 4, 11,  3,  2]  (×2)
```

**In roughly three quarters of cases the context is simply the last three stored frames.** In an
autoregressive rollout where generated frames are written back, that makes the ancestry graph close
to a chain: each child is conditioned mostly on the immediately preceding block's outputs.

If ancestry is nearly recoverable from age, then **B8 has almost the same information as B9 by
construction**, and the +0.05 dB lineage increment cannot appear regardless of how good the error
model is. The mechanism would not have failed — it would never have been testable on this consumer.

**Q1. Is this fatal, and if not, what is the cheapest test that settles it?** My proposal is a
zero-GPU simulation: replay the retrieval over an autoregressive bank using only poses and surfel
metadata, build the resulting ancestry graph, and measure how much of it is predictable from age
alone — for example the conditional entropy of the parent set given frame age, or the accuracy of an
age-only predictor of shared-ancestor structure. **If ancestry is nearly age, close the proposal
before Phase 1.** Is that the right gate, and is that the right statistic?

**Q2. If VMem's retrieval cannot produce ancestry diversity, does the proposal survive by moving to
DFoT as the primary consumer**, or does that make it a DFoT paper with VMem as a weak replication?
You chose DFoT as the second consumer because COVRAG uses it. Does its retrieval or context policy
produce a richer ancestry graph, and is that verifiable before committing?

## Risk 2 — with four sources there are only six off-diagonal terms

The fused weights come from a 4×4 predicted matrix, so the entire lineage signal is **six numbers per
location** beyond the diagonal. That is a small amount of structure for a trained module to exploit,
and it sits directly inside the objection you already called potentially fatal — that a
parameter-matched attention model could learn the same weighting.

**Q3. Does the mechanism need a larger source budget to be testable at all?** If the effect requires
more than four simultaneous sources to be measurable, that changes the consumer requirements, the
compute envelope and the comparability with the occupancy list. Is four enough, and on what basis?

## Risk 3 — the 20% inference-time budget may be unreachable

The method predicts a per-location 4×4 PSD matrix and solves a simplex-constrained quadratic
programme per location. Even at latent resolution — 72×72 for this consumer — that is about 5,184
constrained solves per generation call, on top of geometry inference, feature extraction and
denoising.

**Q4. Should the cost feasibility check move into Phase 0?** You placed the runtime trade-off as a
Phase-3 stop condition. If the per-location solve cannot meet the 20% target even in principle, that
is knowable in week 1 from an arithmetic and micro-benchmark argument, and it would change the design
— for example a closed-form weight rather than an iterative solve, or a coarser matrix resolution.

## Two things I am not asking

I am not asking you to defend the proposal, and I am not looking for reassurance. If Risk 1 holds,
**the correct outcome is to close this before spending the 800 hours**, and I would rather learn that
from a metadata simulation than from a failed Phase-2 prototype.

I am also not treating my 14-window census as proof about rollout behaviour: that panel used a
**fixed** 12-frame bank with no writeback, so it shows what retrieval does on a static bank, not what
it does when generated frames accumulate. **That gap is exactly why I am proposing the simulation
rather than asserting the conclusion.**

**Q5. What else in the round-8 design has this character** — a premise that can be falsified from
source and metadata before any training, and that I should test in Phase 0 rather than discover
later? You have seen the whole design; I have seen the whole codebase. Name the checks I have not
thought of.
