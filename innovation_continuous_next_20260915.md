# Continuous innovation scan: dynamic-landmark validity for pose-indexed memory

Date: 2026-09-15 (Asia/Shanghai)  
Status: one primary-source direction; hypothesis only. `new_method_validated=false`; `novelty_authorization=NONE`.

## New primary source and exact gap

The new source is Chen et al., **ReWorld: An Interactive World Model with Long-Horizon Memory** (arXiv:2608.23565, 2026): [paper](https://arxiv.org/abs/2608.23565). ReWorld uses a bounded KV cache plus a pose-indexed landmark bank; aged chunks are admitted and later retrieved by pose proximity (paper lines 100–113 and 295–298 in the HTML view). Its conclusion explicitly says that memory is still keyed on camera pose alone and identifies extension to dynamic scenes as a next step. The source establishes ReWorld's stated mechanism and limitation; it does not establish that the proposed extension is novel or effective.

## Candidate: DLV (dynamic-landmark validity)

DLV would attach a history-only validity state to each stored landmark. Before retrieval, it measures whether geometry/appearance projected from that landmark remains mutually consistent with *later observed history* at overlapping rays, using source IDs and visibility. A landmark with persistent disagreement is marked stale for the affected spatial support; retrieval then uses the nearest valid landmark plus the recent window. The state is updated only when the new observation has arrived, and no future RGB, depth, pose, mask, or future-validity field may be read at the decision time.

The proposed increment is validity of an old landmark under observed scene change, rather than ReWorld's pose-only nearest-landmark retrieval or SOCF-A's proposed replacement-direction prediction. This separation is provisional: if DLV's validity score is exactly the same as pairwise conflict/coverage or merely reweights recency, the candidate collapses and must be retired.

## Falsifiable prediction

On held-out dynamic or object-change revisit queries, with identical candidate bank, KV budget, recent-window size, consumer seed, denoising steps and compute, DLV will reduce trajectory-level future geometric tail loss (future depth AbsRel and valid pose/reprojection error) relative to ReWorld-style pose-only retrieval and recent/coverage controls, while static-scene queries will not worsen beyond a predeclared tolerance. The effect must remain after stratifying by viewpoint distance and observed overlap. If it only improves current reconstruction or RGB appearance, the hypothesis is false.

## Minimal test

After Gate 0, no-data model-load smoke and the frozen VMem baseline, use two qualified development trajectories containing a controlled revisit with an observed object/region change and one static revisit. At `k=4` (and one frozen sensitivity budget), replay the same memory candidates under pose-only, recent, coverage/confidence, and DLV policies. Serialize the history-only validity state, selected source IDs, and consumer outputs before opening future RGB-D/pose. Then score paired future mean and worst-query AbsRel, pose/reprojection error where valid, stale-region coverage, source identity, and compute. The pilot only checks whether the validity signal is finite, traceable, and distinguishable from existing controls; it is not validation.

## Kill criteria

Kill DLV if dynamic labels or validity updates use future answers; if no qualified change/revisit cases exist; if validity is non-finite or source identity cannot be traced; if pose-only/recent/coverage has identical ranking; if static-scene loss exceeds the tolerance; or if paired future geometric loss is unchanged/worse after equal-budget accounting. A pass would authorize only a larger held-out experiment, not a novelty or method claim.

## Nearest-work boundary

ReWorld is the exact nearest work for pose-indexed bounded landmark memory. ViewRope, Spatia, GIM-World and WorldTrace already occupy geometry-aware attention, explicit spatial updating, learned geometric compression, and addressable/transition memory. Therefore DLV can be considered only as a narrow test-time validity/expiry policy, and only if its dynamic-change signal adds information beyond conflict, recency, visibility, pose distance, confidence and utility controls. No implementation or experiment has been run.

## Decision

Keep DLV as a conditional candidate for one small falsification pilot, below SOCF-A in priority. If the project's available data contain no observed dynamic change under an auditable contract, record a null result and do not simulate one as evidence. Current state remains `new_method_validated=false`, `novelty_authorization=NONE`.

