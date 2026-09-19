# Innovation register — primary-source pass and final experimental outcome (2026-09-18)

Status: `REGISTER_UPDATE_AFTER_PRIMARY_READ`. `new_method_validated=false`,
`novelty_authorization=NONE`. Nothing here is a novelty, priority, or approval claim.

Supersedes the occupancy section of `INNOVATION_REGISTER_UPDATE_20260918.md` (which also
carries a correction notice for an unrelated sign error). Both retained.

## 0. What changed since the last register

Every occupancy verdict below was previously **relayed**. Per `RESEARCH_PRINCIPLES.md` v2.12/v2.13
a relayed claim cannot close a direction. All nine sources were downloaded and read at primary
source on 2026-09-18 and the specific cited numbers were located in the papers themselves. Local
copies: `/home/yliutz/gwm_litread_20260918/` on SuperPOD (HTML + extracted text).

## 1. Verified prior art

### 1.1 Retrieval from history can lose to recent-window conditioning — OCCUPIED

**VRAG, arXiv:2505.21996v4, "Learning World Models for Interactive Video Generation."**
Verbatim from the paper: *"The History Buffer method performs poorly, with an SSIM score of
0.188, indicating that naive historical frame retrieval without effective in-context training
fails to maintain long-term consistency."* Its History Buffer baseline maintains a 124-frame
buffer partitioned into 5 exponentially decreasing segments, sampling 2 frames per segment.

**Verdict: kill any framing of "historical retrieval need not beat recent-window conditioning" as
this project's observation.** Published, with an explicit named baseline.

Qualification I must preserve: this is not an across-metric "retrieval fails" result. The paper's
own 300-frame table shows DF20 at PSNR 16.643 while other configurations differ by metric; citing
it as a blanket negative would repeat exactly the overstatement this project already committed
once today.

### 1.2 Redundant retrieved context wastes a bounded budget — OCCUPIED, three ways

**RAGME, arXiv:2504.06672.** Verbatim: *"The WebVid10M dataset contains duplicate or highly
similar videos; to prevent the model from processing redundant information, given a query q..."*
and *"we apply a deduplication strategy to prevent returning (multiple) similar elements in a
dataset with redundant entries."* Retrieval-augmented **video generation**, with deduplication as
a named component.

**Context as Memory, arXiv:2506.03141.** Its context-selection ablation, verified cell by cell:

| Strategy | PSNR (GT) | PSNR (history) |
|---|---|---|
| Random | 17.70 | 17.07 |
| FOV+Random | 19.17 | 17.47 |
| **FOV+Non-adj** | **20.11** | **18.19** |
| FOV+Non-adj+Far-space-time | 20.22 | 18.11 |

Excluding adjacent (redundant) context is worth +0.94 dB and +0.72 dB. This is a direct,
published redundancy-selection ablation in the same measurement units this project uses.

**LongLive-RAG, arXiv:2606.02553.** Verbatim: *"off-the-shelf image features tend to retrieve
temporally local neighbors, making them less suitable for long generated videos where useful
context may be far outside the recent window"*, addressed by a *"Window Temporal Delta Loss that
suppresses redundant local similarity."*

**Verdict: kill "a small context budget can be squandered on redundant frames" and
"deduplication/diversity is a remedy" as contributions.** All three are published, and Context as
Memory quantifies it in PSNR.

### 1.3 Better geometric evidence is insufficient without effective selection — OCCUPIED

**COVRAG, arXiv:2606.02479.** Verified ablation:

| | Evidence | Selection | MEt3R ↓ | LPIPS ↓ |
|---|---|---|---|---|
| (a) | FoV overlap | Independent | 0.141 | 0.198 |
| (c) | Target-view coverage | Independent | 0.149 | 0.210 |
| (d) | Target-view coverage | Residual | 0.100 | 0.156 |

Finer geometric evidence with independent selection is **worse** than coarser evidence with
independent selection; residual selection recovers it.

**Verdict: kill any "geometry-aware retrieval evidence versus effective context utilisation"
framing as novel.**

### 1.4 Camera-conditioning reference-frame dependence — OCCUPIED

**PRoPE, arXiv:2507.10496.** Verbatim: *"They are sensitive to the arbitrary choice of reference
frame, which can hinder generalization"* and *"To remove the need for a global reference frame,
recent works have introduced relative encodings for SE(3) camera poses."*

**Verdict: confirmed kill.** Independently, this project's own source trace already showed the
state leak cannot move the slot-0 ray reference, so the route was dead on its own evidence.

### 1.5 Evaluation state, resetting, episodic versus accumulated — OCCUPIED

**TTAB, arXiv:2306.03536 (ICML 2023).** Confirmed to distinguish episodic adaptation from
accumulated state (*"Some TTA methods are episodic, performing adaptations on the base model"*).

**Verdict: kill "state-aware evaluation" and "resetting changes conclusions" as contributions.**
Those remain necessary controls here, not novelty.

### 1.6 What the search did NOT find occupied

No source examined reports the specific mechanism found here: **a released view-generation
selection path consuming two nominal context slots with the same frame, because separately seeded
nearest-candidate and most-recent selections collide.** That is an implementation diagnosis, not a
method or a general mechanism, and section 3 shows it has no measured performance consequence.

## 2. Verified provenance discrepancy in the consumer

The VMem paper (arXiv:2506.18903) describes non-maximum suppression as part of its method:
*"To avoid oversampling repeatedly visited regions, we apply a non-maximum suppression algorithm
that reduces redundancy in memory and promotes broader scene coverage among the top-K."*
`configs/inference/inference.yaml:16` sets `use_non_maximum_suppression: true`.

The released interface uses **both** settings. `navigation.py` is the only caller of
`generate_trajectory_frames` and has **three** call sites: `move_backward` (185) and `move_forward`
(234) pass `use_non_maximum_suppression=False`; **`_turn` (321), reached from `app.py:208/210` via
`turn_left`/`turn_right`, passes no argument**, which resolves to the config default `true`.

An earlier version of this register stated that every call site disables NMS. That was wrong: I had
searched for the *parameter* name, which finds only the sites that override it, rather than
enumerating the call sites of the *function*. Because the disabled branch writes
`initial_threshold = 1e8` and the enabled branch assigns only at exactly five stored frames, a
native movement-then-turn sequence consumes the leaked value, so the cross-arm leak is **natively
reachable** and is not exclusive to comparative harnesses. Static reachability only: the demo was
not run. See `docs/ENTRY_PATH_CORRECTION_20260918.md`.

**Boundary, stated because it limits the claim:** the release contains only the demo
(`app.py`, `navigation.py`, `modeling/`, `utils/`) and **no evaluation or benchmark script**. The
configuration used to produce the paper's tables therefore cannot be determined from the release.
This is a statement about the released demo path only. It is **not** a claim that the paper's
reported results are wrong, and must never be written as one.

The paper's memory demonstration is §4.3, *"Long-term view generation with revisitations."* Its
selector ablation at K=4 reports temporal selection at PSNR 7.52 against VMem at 14.82. This
project's panel is forward extrapolation without revisits, and its fixed-offset arm scores about
14.5 dB — a far stronger baseline than the 7.52 dB comparator. **This project does not reproduce,
test, or contradict the published revisit experiment.**

## 3. Final experimental outcome

All aggregation folds seeds within a window first (v2.14). Windows are a finite panel: **no SE,
t statistic, confidence interval, significance test, equivalence test or bootstrap is reported.**

| contrast | n windows | mean | SD | positive |
|---|---|---|---|---|
| movement-path retrieval (NMS off) − fixed offset | 14 | **+0.242 dB** | 1.270 | 8/14 |
| clean NMS-on − fixed offset | 14 | −0.485 dB | 1.489 | 6/14 |
| clean NMS-on − shipped retrieval | 14 | −0.726 dB | 1.210 | 5/14 |
| INPLACE repair − movement-path retrieval | **8 of 10 affected** | **−0.016 dB** | 0.309 | 3/8 |
| REFILL repair − movement-path retrieval | 8 of 10 affected | −0.032 dB | 0.304 | 3/8 |
| INPLACE − REFILL (pure order) | 8 | +0.016 dB | 0.037 | 5/8 |

Leak effect (clean − leaked), split by a census fixed before scoring:
NULL n=2 **+0.000** (byte-identical, verified by sha256); PERMUTATION n=4 **−0.015**;
CONTENT n=8 +0.436.

### The predeclared repair rule fired against the hypothesis

Threshold 0.20 dB, fixed in `REPAIR_SPEC_PREDECLARED_20260918.md` before any repair output was
scored. Measured INPLACE gain **−0.016 dB**. No-op gate passed (8/8 byte-identical to the sealed
shipped output). **Verdict: the duplication-as-performance-explanation is DISCARDED**, across the 8 of 10
duplication-affected windows for which the selector offers any replacement candidate; the other 2
are structurally untestable (its whole ranked list holds three distinct frames). Full accounting in
`work/S103_selector_free_baseline/REPAIR_WINDOW_MANIFEST_20260918.md`. This is not a completed test
across all ten. The
threshold was not lowered, the replacement policy was not changed, and no favourable subgroup was
elevated.

### Candidate provenance was verified, not argued

The ranked candidate list was read from the pipeline at `context_num_frames` 5, 6 and 7 — three
different `context_num_frames + 10` pool requests — and the lists were exactly nested in every
window (`[11,11,10,9,8] ⊂ [...,3] ⊂ [...,3,4]`, with the shipped `[11,11,10,9]` as prefix). The
duplicated index 11 is visible directly: it is both the surfel-nearest candidate and the most
recent stored frame.

### The one coherent pattern across three independent interventions

| intervention | magnitude of change to the context | measured effect |
|---|---|---|
| reorder the same multiset | none (identical frames) | 0.015 dB |
| replace a duplicate with the next ranked neighbour (e.g. 105 → 90) | one nearby frame | 0.016 dB |
| enable NMS, selecting distant frames (e.g. 105 → 55) | one distant frame | −0.726 dB |

On this panel the consumer is insensitive to slot order and to substituting a *nearby* frame, but
responds strongly to substituting a *distant* one, in the direction of worse PSNR. This is a
description of three measured interventions on one frozen consumer and one dependency group. It
is not a general property of the architecture and no mechanism is claimed for it.

## 4. Register status of every candidate

| candidate | status |
|---|---|
| SOCF-A | **STOPPED** |
| FGB-SI | **STOPPED** |
| coverage / gating / cache-policy design | **STOPPED** |
| gauge / reference-frame dependence | **KILLED** — occupied (PRoPE), and dead on own source evidence |
| state-aware evaluation as a contribution | **KILLED** — occupied (TTAB) |
| leak acting through slot-0 ray gauge | **KILLED** — impossible in source; slot 0 invariant 14/14 |
| retrieval-fails-vs-recency as a finding | **KILLED** — occupied (VRAG), and the panel mean is positive anyway |
| redundant-context / dedup as a contribution | **KILLED** — occupied (RAGME, Context as Memory, LongLive-RAG) |
| geometry-evidence vs selection framing | **KILLED** — occupied (COVRAG) |
| slot-duplication as a performance explanation | **DISCARDED by predeclared rule** (−0.016 dB) |
| duplicate-slot collision as an implementation diagnosis | **RETAINED as a provenance note only**, with no performance consequence |

## 5. Honest position

What remains is a set of correct, reproducible measurements on one frozen consumer, one dependency
group, two exposed development sequences and fourteen windows, with every claimed mechanism either
occupied in the literature or discarded by its own predeclared test. The appropriate output is a
technical report that records the measurements, the contamination audit, the released-path
provenance discrepancy, and the failed mechanism hypothesis. **No novelty claim is supportable and
none is made.**
