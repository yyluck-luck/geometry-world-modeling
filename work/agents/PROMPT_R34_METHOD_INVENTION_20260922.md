# Round 34 — Invent methods. This round is generative, not an audit.

You are not reviewing anything. You are the researcher who must propose what this project builds next. **Output new methods.** Use the repository to ground them and the web to avoid reinventing published work — but a survey, a ranking of existing work, or a list of what is occupied is a failed round.

## The bar (set by an earlier reviewer; I accept it)
Under the same legal state-management protocol and the same evidence inputs, does the method change the model's PREDICTIVE ability — about future views, content reappearing after occlusion, cross-view geometry? NOT: does the system err less after a reset bug is fixed. Operation lists (write/merge/decay/rollback) are not mechanisms. Moving from the read side to the write side does not upgrade a contribution. Reranking which frames are read is not enough (five such candidates were already judged adjacent and sub-paper).

## Resources
The owner accepted cross-semester work (decision C7 in RESEARCH_MEMORY.md). You MAY propose training, fine-tuning/LoRA, new weights, upstream modification, new data, and substantial GPU time (SuperPOD H800 nodes, 8 GPUs each, are physically available). Do not self-censor on cost: price each proposal honestly, then propose it anyway.

## Clues only this project has (verify each in the repo; treat them as evidence about where the real gap is)

1. From the four target cameras, only 1 of 12 banked frames has any visible surfels (docs/S103_S109_GPU_EXPERIMENT_SUMMARY_20260917.md, "frame_count_raw = [(11, 1)]").
2. At fixed k=4, context POSITION spans 5.6 dB on the panel; spanning the bank beats pure recency.
3. At a FIXED multiset, changing only which frame occupies slot 0 moves output by 0.55 dB.
4. A prospectively registered repair of a duplicated context slot gave -0.016 dB against a +0.20 dB threshold.
5. Shipped retrieval beats a fixed-offset context by only +0.242 dB (SD 1.270).
6. Classical correlated-estimate fusion over the context sources is algebraically empty: at optimal weights the cross-source covariance term adds zero information (verified numerically to 4.4e-16; see docs/proposal_v2/NEW_PROPOSAL_DRAFT_20260919.md).
7. My own reading of the selection code (verify it — pipeline.py roughly :640-:755): surfel visibility only decides WHICH frames enter the candidate pool and HOW MANY TIMES each is duplicated (:657); ordering, diversity and fallback are done entirely in camera-POSE space by geodesic distance (:665, :711-:750); and max_frames = min(k, len(candidates), ...) (:671) uses the total PIXEL count, so when visibility collapses the context itself can shrink. In other words the "geometry-aware memory" contributes membership, while pose heuristics decide everything else.

My tentative synthesis, which may be wrong: **this class of system is bottlenecked by SUPPORT SCARCITY, not support selection** — there is not enough visible, geometrically valid evidence for the target, so every selection/reweighting/fusion method attacks a term with no headroom. Clue 6 says optimal reweighting cannot extract more; clue 4 says de-duplicating existing support buys nothing; clue 1 says support barely exists; clue 2 says what matters is covering the trajectory.

## What I want

**Part 1 — Test my synthesis before building on it.** Is "support scarcity, not selection" actually implied by clues 1-7, or am I adding evidence across different logical levels (a known failure mode of mine)? What is the cheapest zero-GPU check against saved artifacts in this repo that could falsify it (for example: does the 5.6 dB positional effect survive controlling for the number of visible surfels / visible frames per window)? If the saved artifacts allow it, run it on CPU and report. If they do not, say what is missing.

**Part 2 — Invent 8 to 12 methods.** Each must change what the model predicts, not which frames it reads or keeps. For each give: name; mechanism in 2-3 sentences; where exactly it plugs into VMem (file:line or module); the claim; the estimand; the single experiment that would kill it; honest cost in H800-hours and weeks; the nearest published work (arXiv ID) and the one-sentence delta. Spread them: some that assume support scarcity is true (manufacture support), some that hold even if it is false.

Directions I have NOT seen seriously explored here, as prompts only — go beyond them:
- manufacturing support: generating or completing geometry/appearance for the target region before conditioning, rather than choosing among existing frames;
- making the generator robust to, or aware of, how much valid support it has (e.g. conditioning on a support/visibility map, or training with support dropout so low-support regions are treated as prediction rather than copying);
- exploiting the slot-0 asymmetry (clue 3): if the generator treats the first slot specially, learn or design what should go there, or remove the asymmetry;
- using clue 6's algebra constructively: if reweighting existing sources is provably empty, what changes the information content itself?

**Part 3 — Pick the single strongest one and go deep.** A concrete implementation plan against the actual VMem code: which modules change, what is trained and on what data, the training objective, the first 1-2 week milestone that would already tell us whether to continue, and the held-out evaluation it ultimately needs. Say why it would be hard to scoop in the next 12 months.

**Part 4 — What does clue 3 (slot-0 at fixed multiset) reveal about how this model consumes context?** Inspect the model / conditioning code in the repo if present (search for where context latents and cameras are embedded and whether positional or slot embeddings exist). This is a concrete mechanistic question and may itself be a method lever.

Do not re-propose: lineage-aware fusion (algebraically empty), the five selection-layer rerankers (query consensus, coverage-distance-novelty rerank, occlusion-risk priority, adaptive candidate budget, source counterfactual replay), or a learned write/merge/decay/rollback gate. Do not rename them.

## Output
Write to exactly one new file: work/agents/CODEX_R34_METHOD_INVENTION_20260922.md.
