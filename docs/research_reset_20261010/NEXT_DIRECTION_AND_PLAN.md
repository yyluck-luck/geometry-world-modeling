# Next direction and six-week decision plan

Date: 2026-10-10 America/Los_Angeles. **ANALYTICAL design, not an experimental result.** One next candidate, conditional on the existing P2 completing or being retired under its unchanged gates. No new GPU job was submitted for this direction. A fully executable protocol still requires a sealed input manifest and implementation fingerprint before data-dependent execution.

## Decision

Prioritize **spatial response supervision for memory-conditioned generation**. Keep retrieval, camera geometry and the conditioning architecture fixed. Train how output changes when remembered appearance changes, including where output must not change. The intended contribution is a specific response objective that improves natural cross-view memory use beyond equal-data ordinary adaptation. It is not a new selector, B warp-input branch, W2 source selector, P1 blend, or a different name for P2 guidance.

[Evidence](EXPERIMENT_MAP.md): S139's history is useful to a geometric predictor but not to the frozen generator; S141 A improves generic adaptation without a demonstrated memory advantage. S143 requires fixing the context package while studying consumption. These motivate the question but do not prove this candidate will work.

## Candidate comparison

| Candidate | Mechanism | Decision |
|---|---|---|
| Spatial response supervision | Match signed output changes to the projection of changed memory content; preserve unrelated output | One bounded falsification assay next; novelty and effectiveness unverified |
| Ancestry-aware write updates | Avoid treating generated descendants as independent evidence while retaining provisional imagined state | Park. No inspected project result establishes this failure; observed/imagined separation and provenance already have strong prior art |
| Learned utility retrieval or generic reliable local fusion | Learn helpful context or weight local anchors | Reject as current innovation claim: FAR/MemLearner/I3DM/AnchorWeave directly occupy the broad mechanism; S143/S146 already address the local retrieval question |

See [literature synthesis](LITERATURE_AND_NOVELTY.md) for exact titles and identifiers. In particular Point Prompting already propagates appearance interventions; CAER already reweights training using response magnitude; ARGUS already uses counterfactual reference augmentation. The proposed narrow difference is **supervising signed spatial response**, which must beat these simpler explanations. Search absence is not proof of novelty.

## First decisive assay: measure the deficit before training

Proposed label: P3 spatial-response assay. This is a new causal question; it does not reopen any stopped candidate. All following counts/thresholds are **ANALYTICAL prospective choices**, to be bound to the final dated protocol before generation.

1. Use four exposed development clips: the first two in each S141 monitor sequence, ordered by the existing monitor manifest, passing a source-only geometry/visibility eligibility rule fixed before generation. Freeze actual IDs and all exclusions before model responses are read. Do not borrow S146 rooms or silently replace a failed panel. Seeds42 and7, paired initial noise across factual/edited outputs.
2. Construct a bounded appearance edit on one fixed scene surface, coherent across visible source views. Hold context IDs, order, poses, geometry, visibility and sampling fixed. Use measured source geometry or a separately validated planar construction; do not call CUT3R a ground-truth oracle. Edited targets and target visibility are scoring-only assets. Independent projection/mask checks must precede scientific interpretation; a tautological self-rendering check is insufficient.
3. Compare frozen VMem and fixed S141 A using factual versus edited memory. Add A same-camera positive controls, a displaced-edit control, and one frozen-strength A counterfactual-guidance control adapted from Point Prompting. The latter is a scoped adaptation, not an official reproduction. Do not tune its strength after pilot scores.
4. Sample from the same initial noise and save complete predictions, input hashes, correspondence/visibility masks, unedited baselines, noise hashes, exact model/adapter identities and runtimes. Shared random noise permits a paired output difference; target RGB never enters inference.
5. Score signed alignment and normalized response error E=||G(M')-G(M)-(Y'-Y)||/||Y'-Y|| on the affected support, plus response energy outside it. Zero response has E=1. Report each clip, sequence and seed; do not replace locality with a global average.

**Screening gates:** independently validated geometric transfer E≤0.2; same-camera A E≤0.5; cross-view A E≥0.8, with the same qualitative separation in both monitor sequences and both seeds. These are development screening tolerances, not population significance. If the correspondence assay is invalid or same-camera positive control fails, stop as INVALID_ASSAY; it is not evidence against cross-view memory. If A already transfers the edit, stop the proposed deficit premise. Intermediate outcomes are inconclusive and do not trigger larger training. If one fixed inference-guidance control resolves the deficit without increased off-support error, stop the immediate adapter plan and retain that simpler explanation.

**Resource gate:** at most two RTX3090 GPU-hours in total, at most two idle owner-authorized cards, one active pilot. Include loading, same-camera controls and the extra guidance branch. Profile the first complete cell, then project the entire mandatory panel conservatively. If it cannot fit, stop as COMPUTE_CAP; do not omit controls or produce a partial scientific verdict. No H800 allocation is assumed. CPU construction can proceed after the protocol/input freeze, but no new pilot is dispatched while P2 remains active.

## Only if the assay passes: the actual method test

Reuse S141 `s141_common.py` (build_cond, attention LoRA, adapter loading), its training eps_pred path and `gen_s141.py` sampler. Add a paired-response regularizer to the same trainable adapter, without a new retrieval encoder or aligned warp-input branch.

Let e1/e2 be factual/edited prediction errors. A response loss is an error-coupling term ||e2-e1||²; it is not automatically a new learning principle. Use identical paired examples and account for forward/backward compute in four controls: original-data SFT; paired-data SFT; paired-data SFT plus response objective; paired-data SFT plus shuffled spatial correspondence. Include memory dropout and inference guidance in the final comparison if the mechanism survives. Ordinary same-data SFT is the central comparator, not only the old frozen VMem.

**Prevent a target shortcut:** for the auxiliary response branch use the same high-noise target latent, independent of edited appearance, in both forwards. Separately noised factual/edited targets could reveal the desired difference even if the model ignores memory. Keep correctly noised targets in the ordinary supervised loss. Validate the claim through full sampling from shared initial noise, plus crossed-memory/target controls. Do not call the regularizer an identified real-world causal effect.

The method must improve both response locality and unedited natural revisit quality. A marker-only improvement, gain explained by extra paired data, unchanged result after correspondence shuffling, or degradation hidden outside the edited region kills the method claim. Before any training, freeze its concrete data, initialization, loss coefficient, update count, exact controls and compute cap. Larger sweeps are outside the existing autonomous two-GPU-hour pilot scope.

## Six weeks, conditional on evidence

| Week | Deliverable | Decision |
|---|---|---|
| 1 | Close existing P2; consume S145/S146 once; implement and execute the bounded spatial-response assay | No valid specific deficit -> stop this candidate |
| 2 | One matched small training pilot with paired-data and shuffled-correspondence controls | No added mechanism benefit -> stop; no coefficient sweep |
| 3 | Test unedited natural revisits with recent-context, nearest4, raw warp and simple blend references | Synthetic-only effect or no memory advantage -> stop method claim |
| 4 | One scene-disjoint confirmation panel, frozen before images/results are inspected for choices | Require positive effects across rooms and no hidden concentration/quality loss; no scene swapping |
| 5 | One second suitable public consumer or stronger public memory baseline, matched where feasible | If unavailable or unaffordable, narrow the VMem-specific claim; do not invent cross-model generalization |
| 6 | Write the supported method with ablations and failure cases, or a clear negative result and reusable assay | No rebranding failed candidates as a successful CCF-A method |

Weeks2–5 are resource proposals, not evidence or blanket approval for large training. Each next stage gets one brief protocol, one execution and one independent numerical check. Only a real compute/owner decision should pause progress; no signatures, quorum, repeated reviewer rounds or new packet machinery.

## What counts as CCF-A-level progress

A distinctive mechanism with a compelling need; gains beyond matched data/compute and strong simple controls; natural cross-scene memory utility; at least one serious alternative consumer; and a reusable implementation. A diagnostic pilot pass alone satisfies none of the complete paper claim. Current status remains `new_method_validated=false`, `novelty_authorization=NONE`.
