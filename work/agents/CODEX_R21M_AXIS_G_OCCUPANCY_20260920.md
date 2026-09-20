# Round 21-M — Axis (g) occupancy review

**Review date:** 2026-09-19 (workspace date; requested filename date 2026-09-20)  
**Scope:** camera-conditioned video generation, video world models, and long-horizon/memory video models.  
**Decision state preserved:** `new_method_validated=false`; `novelty_authorization=NONE`; the 800 GPU-hour tranche remains withdrawn.

## Executive ruling

**AXIS-G-OCCUPIED.** The three sub-regions are all occupied at the level of a publishable general claim:

- **(g1) metrics:** occupied, from FVD/VBench-style video measures to camera- and geometry-specific world-model measures.
- **(g2) benchmarks:** occupied, including camera control, interaction, long-horizon stability, and memory/revisit suites.
- **(g3) experimental-validity machinery:** occupied in the broad claim relevant here. `WorldRoamBench` publishes an explicit validity gate before physics scoring, and *Validate the Dream Before You Trust Its Verdict* publishes an admissibility ladder for accepting world-model verdicts as evidence. The project's gates are narrower and useful as a worked audit, but the principle is no longer unoccupied.

The narrow statement “no paper has exactly this project's retrieval-arm byte-identity/order/provenance gate” is **UNVERIFIED** and search-bounded. It cannot support `AXIS-G-OPEN`: a reviewer can identify the direct world-model validity-gate precedents, then classify the project package as a single-consumer implementation without cross-system external validity or external adoption. Lead 2 is also closed by a direct benchmark published after the Steady-Forcing open call.

## Verification method and limits

I read the three pinned VMem copies, the current ledgers, the technical report, and the concrete S103 gate scripts. I searched primary arXiv records and, where available, the arXiv HTML. Every paper used below has an arXiv identifier and the exact title shown on the arXiv record. A negative statement means only “not found in this bounded search,” and is marked **UNVERIFIED** where appropriate. I did not train, download weights, install packages, send messages, or run GPU jobs.

The mandatory Astra review command was attempted twice with the repository prompt, network enabled, `gpt-6-astra`, and `ultra`; both attempts stopped at `failed to initialize in-process app-server client: Operation not permitted`. No substantive Astra output was obtained, so that external-review channel is **UNVERIFIED**. The literature checks below are from direct arXiv pages plus the independent parallel searches recorded in this session.

## Repository facts checked

The three source copies are byte-identical by SHA-256 (`90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e`) and agree at the requested consumer path:

- `work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:1249` calls `get_context_info(target_c2ws, use_non_maximum_suppression)`.
- `:1263` forms `torch.cat([context_c2ws, target_c2ws])`.
- `:1265` calls `get_translation_scaling_factor(all_c2ws)`.

The same snippets occur in `work/S17_cpu_preflight/original/modeling/pipeline.py` and `work/S102_gate0_3dmatch/adapter_v1/sources/vmem_pipeline.py`. These lines make retrieval selection, context concatenation, and camera normalization one consumer path; they do not by themselves establish a comparison-validity contribution.

The requested `self.c2ws` claim needs a precise correction. In the pinned file there are two *insertion/assignment* sites (`:180`, `self.c2ws = [c2w]`, and `:1297`, `self.c2ws.append(...)`) and no setter that relabels an already-retained pose. However, `undo_latest_move()` mutates the list at `:1360` with `self.c2ws.pop()` (the surrounding loop is `:1359–1364`). Thus “only two sites” is true only if “written” silently excludes deletion; “no setter for retained-frame camera relabeling” remains true. This correction does not reopen T1-5: `pop()` rolls back recent frames and does not provide a retained-frame pose-relabel operation or synchronized surfel rebuild.

The project machinery is real but its evidence level is limited:

| Local asset | What the repository actually establishes | Evidence boundary |
|---|---|---|
| `work/S103_selector_free_baseline/arm_state_isolation_test.py:2–18,57–80,181–193` | Zero-diffusion order-invariance test: the worker's isolation routine clears mutable fields and deletes `initial_threshold`; the receipt records **11/11**, including a non-vacuity check that detects the contaminated ordering. | Protocol/software validity for the tested three windows, not a model-quality gain. |
| `leak_regime_census.py:2–31,204–229` | Pre-scoring classification of the 14-window panel into `NULL 2 / PERMUTATION 4 / CONTENT 8`; slot 0 was invariant in 14/14. No target ground truth or diffusion was read by this census. | A pre-score eligibility/attribution census on this finite panel. |
| `docs/report/TECHNICAL_REPORT_20260918.md:252–277` | NULL byte-identity gate: 4 window-seed executions, all SHA-256 identical; no-op gate: 8 window-seed executions, all identical to sealed output; historical linkage 28/28. | Licenses reuse only for those covered cases; it does not validate uncovered arms. |
| `REPAIR_SPEC_PREDECLARED_20260918.md:1–4,42–57` and report §1 | The +0.20 dB retention threshold and eligibility rule were fixed before repair scoring; measured in-place repair was −0.016 dB over 8 eligible affected windows and was discarded. | A prospective negative decision on an exposed two-sequence finite panel, not held-out external validity. |
| `RESEARCH_MEMORY.md:2026–2031` and `docs/LIFECYCLE_AUDIT_CLOSEOUT_20260919.md:34–38,102–107` | The four-tuple is `(writer on call A, public sequence A→B, exact consumer on B, dominance check)`. Applying it reclassified CausVid from HIT to CLEAN after the consumer was traced. | Demonstrates that the audit catches a false positive in its own search; it is not a prevalence estimate. |

The ledger explicitly records the structural gaps: no second released consumer or dataset family, no clean held-out system-level test, no proof that the observed defect changes a published VMem ranking, and no external adoption of the artifact. The finite panel is exposed development data, not a population sample.

## Q1 — Occupancy by sub-region

### (g1) Metrics — **OCCUPIED**

The prior that metric work is heavily occupied is correct. Representative primary records are:

| arXiv ID and exact title | What it occupies |
|---|---|
| [arXiv:1812.01717, *Towards Accurate Generative Models of Video: A New Metric & Challenges*](https://arxiv.org/abs/1812.01717) | Introduces Fréchet Video Distance (FVD) and a video evaluation setting. |
| [arXiv:2311.17982, *VBench: Comprehensive Benchmark Suite for Video Generative Models*](https://arxiv.org/abs/2311.17982) | Disentangled video dimensions such as subject/background consistency, temporal flicker, and motion smoothness. |
| [arXiv:2411.13503, *VBench++: Comprehensive and Versatile Benchmark Suite for Video Generative Models*](https://arxiv.org/abs/2411.13503) | Extends the metric/benchmark family to broader generation settings and trustworthiness. |
| [arXiv:2401.07781, *Towards A Better Metric for Text-to-Video Generation*](https://arxiv.org/abs/2401.07781) | T2VScore and a human-judgment resource for text-video alignment and video quality. |
| [arXiv:2406.15252, *VideoScore: Building Automatic Metrics to Simulate Fine-grained Human Feedback for Video Generation*](https://arxiv.org/abs/2406.15252) | Automatic fine-grained quality, consistency, dynamics, and alignment scoring trained against human feedback. |
| [arXiv:2503.21755, *VBench-2.0: Advancing Video Generation Benchmark Suite for Intrinsic Faithfulness*](https://arxiv.org/abs/2503.21755) | Intrinsic faithfulness dimensions including physics, commonsense, controllability, human fidelity, and creativity. |
| [arXiv:2502.20694, *WorldModelBench: Judging Video Generation Models As World Models*](https://arxiv.org/abs/2502.20694) | World-model violation judgments for instruction following and physics adherence, with human labels and an automated judge. |
| [arXiv:2602.07854, *Geometry-Aware Rotary Position Embedding for Consistent Video World Model*](https://arxiv.org/abs/2602.07854) | Publishes the ViewBench diagnostic suite for loop-closure fidelity and geometric drift. |
| [arXiv:2605.15185, *Quantitative Video World Model Evaluation for Geometric-Consistency*](https://arxiv.org/abs/2605.15185) | PDI-Bench and a perspective-distortion/geometric-consistency diagnostic. |
| [arXiv:2608.18710, *CamWorldQA: Perceptual Quality Assessment of Camera-Controlled World Video Generation*](https://arxiv.org/abs/2608.18710) | Camera-conditioned perceptual quality: 720 generated videos, six methods, 20 sources, six camera trajectories, human ratings, and the CWQA predictor. |

These are not all the same construct. FVD and VBench measure broad video behavior; ViewBench, PDI-Bench, and CamWorldQA target camera/geometry/world-model behavior. That diversity makes “a new metric for camera-conditioned or memory video” an occupied contribution class, even though individual metrics still have blind spots.

### (g2) Benchmarks, datasets, protocols, and leaderboards — **OCCUPIED**

The prior that benchmark work is heavily occupied is also correct. Representative direct records include:

| arXiv ID and exact title | Occupied evaluation object |
|---|---|
| [arXiv:2310.11440, *EvalCrafter: Benchmarking and Evaluating Large Video Generation Models*](https://arxiv.org/abs/2310.11440) | Prompt suite, objective metrics, human alignment, and leaderboard-style comparison for large video generators. |
| [arXiv:2502.20694, *WorldModelBench: Judging Video Generation Models As World Models*](https://arxiv.org/abs/2502.20694) | Human-labeled world-model violations and automated judging across application domains. |
| [arXiv:2605.03941, *iWorld-Bench: A Benchmark for Interactive World Models with a Unified Action Generation Framework*](https://arxiv.org/abs/2605.03941) | Unified action generation and long-video interaction/memory evaluation. |
| [arXiv:2603.22212, *Omni-WorldBench: Towards a Comprehensive Interaction-Centric Evaluation for World Models*](https://arxiv.org/abs/2603.22212) | Interaction-centric suite and metrics for causal response across states and trajectories. |
| [arXiv:2605.25874, *WBench: A Comprehensive Multi-turn Benchmark for Interactive Video World Model Evaluation*](https://arxiv.org/abs/2605.25874) | Multi-turn cases and human-validated submetrics for quality, adherence, consistency, and physics. |
| [arXiv:2604.21686, *WorldMark: A Unified Benchmark Suite for Interactive Video World Models*](https://arxiv.org/abs/2604.21686) | Shared action adapters, identical scenes/actions, 500 standardized cases, and visual/control/world-consistency suites. |
| [arXiv:2606.00793, *MBench: A Comprehensive Benchmark on Memory Capability for Video World Models*](https://arxiv.org/abs/2606.00793) | Entity, environment, and causal consistency over memory-specific subdimensions. |
| [arXiv:2606.20545, *Current World Models Lack a Persistent State Core*](https://arxiv.org/abs/2606.20545) | WRBench-style hidden-event persistence under look-away/return tests. |
| [arXiv:2608.13552, *PlayWorld: Benchmarking World Models with Agent Players over Long-Horizon Objectives*](https://arxiv.org/abs/2608.13552) | 171 objective-driven scenarios evaluated through agent players on geometry, interaction, out-of-sight evolution, and insight evolution. |
| [arXiv:2606.31672, *WorldRoamBench: An Open-World Benchmark for Long-Horizon Stability of Interactive World Models*](https://arxiv.org/abs/2606.31672) | 10–60 s open-world interactions, per-frame action, drift, physics, scene memory, and subject memory. |
| [arXiv:2608.02603, *WorldExam: Benchmarking World Models from Apparent Appearance to Inherent Reactivity*](https://arxiv.org/abs/2608.02603) | Unified camera/action/language cases spanning visual quality, control adherence, spatial consistency, and reactivity. |
| [arXiv:2512.18741, *Memorize-and-Generate: Towards Long-Term Consistency in Real-Time Video Generation*](https://arxiv.org/abs/2512.18741) | MAG-Bench for historical-memory retention and long-term consistency. |

The camera-controlled and memory subregions are therefore not empty corners. They have dedicated benchmark artifacts even when the benchmark is introduced inside a method paper. If one restricts “benchmark contribution” to a benchmark-only paper, the independent suites `WorldModelBench`, `WorldMark`, `WBench`, `MBench`, `PlayWorld`, and `WorldRoamBench` still suffice for occupancy.

### (g3) Experimental-validity machinery — **OCCUPIED at the claim level relevant to Lead 1**

This sub-region needs a granularity distinction. The project’s machinery operates at the **comparison-arm and provenance** level: isolate state, classify before scoring, prove byte identity before reusing sealed outputs, enforce a predeclared discard rule, and trace writer → public sequence → consumer. The closest published works are not all identical, but two direct world-model precedents close the broad claim.

1. **Direct world-model admissibility:** [arXiv:2607.07196, *Validate the Dream Before You Trust Its Verdict: Admissibility for World-Model Simulators*](https://arxiv.org/abs/2607.07196) states that a generative world model used as a test oracle must be accredited before its verdicts count as assurance evidence. It defines an L0–L4 admissibility ladder, from generation quality through action robustness, OOD/envelope behavior, failure attribution, and transfer of simulated verdicts to reality. This is an explicit contribution whose purpose is to decide when a world-model result is admissible evidence, not merely to report another quality score.

2. **Direct sample-level validity gate in a video-world benchmark:** [arXiv:2606.31672, *WorldRoamBench: An Open-World Benchmark for Long-Horizon Stability of Interactive World Models*](https://arxiv.org/abs/2606.31672) has a section titled “Validity Gate.” Before physics scoring, first-person rollouts must show pose-verified camera translation; third-person rollouts must show continuous subject tracking. Invalid cases are excluded from the aggregate physics score, and the paper reports scores conditional on the model-specific accepted subset. The arXiv HTML gives the gate in §3.4.1 and its operational details in Appendix G.1, including static/no-response, disappearance, teleportation, and tracking-loss checks.

These two precedents occupy different levels: `WorldRoamBench` gates whether a generated rollout is score-eligible; *Validate the Dream* gates whether a world-model verdict is assurance-eligible. Together they defeat the broad claim “validity gating for generative video/world-model experiments is unoccupied.” The project’s exact comparison-arm gate may still be a **narrow unverified niche**, but novelty of a narrow implementation would require independent systems, common-denominator rules, held-out tests, and adoption. Those are absent here.

Adjacent published validity/reproducibility machinery further weakens any generic-first claim:

- [arXiv:2108.13264, *Deep Reinforcement Learning at the Edge of the Statistical Precipice*](https://arxiv.org/abs/2108.13264) proposes interval estimates, performance profiles, robust aggregates, and `rliable`. It is a statistical reliability methodology, not a video admissibility gate; it is **not** correctly summarized as “rliable for video.”
- [arXiv:2310.17867, *Reproducibility in Multiple Instance Learning: A Case For Algorithmic Unit Tests*](https://arxiv.org/abs/2310.17867) uses synthetic algorithmic unit tests to expose violations of MIL assumptions. It is a strong model-agnostic test precedent, but not a generative-video comparison gate.
- [arXiv:2207.07048, *Leakage and the Reproducibility Crisis in ML-based Science*](https://arxiv.org/abs/2207.07048) surveys leakage across 17 fields and proposes model information sheets. It is a general leakage/reproducibility precedent, not a video/world-model-specific gate.
- [arXiv:2406.08845, *Rethinking Human Evaluation Protocol for Text-to-Video Models: Enhancing Reliability,Reproducibility, and Practicality*](https://arxiv.org/abs/2406.08845) proposes a standardized T2V human-evaluation protocol. It is broader evaluation machinery, not the same admissibility predicate.
- [arXiv:2605.21800, *stable-worldmodel: A Platform for Reproducible World Modeling Research and Evaluation*](https://arxiv.org/abs/2605.21800) packages standardized data, baselines, tasks, and OOD variation for reproducible world-model evaluation. It is platform/protocol infrastructure rather than the project's exact arm gate.
- [arXiv:2311.18807, *Pre-registration for Predictive Modeling*](https://arxiv.org/abs/2311.18807) addresses data-dependent decisions and test reuse in predictive modeling; it is not video/world-model-specific.
- [arXiv:2606.11129, *WorldOlympiad: Can Your World Model Survive a Triathlon?*](https://arxiv.org/abs/2606.11129) is a structured world-model evaluation protocol, but its abstract does not establish the project’s specific pre-score admissibility machinery.

**UNVERIFIED negative:** I did not find a paper that combines, in exactly one retrieval-conditioned video experiment, all of (i) order-invariance/non-vacuity, (ii) pre-score NULL/PERMUTATION/CONTENT classification, (iii) byte-identity licensing of sealed output reuse, (iv) a prospectively fixed discard threshold, and (v) the four-tuple consumer-dominance audit. This is a bounded absence claim, not evidence that the combination is novel or publishable.

## Q2 — Is Lead 1 unoccupied?

**No, as stated.** The direct answer is not “this is merely rliable for video.” `rliable` supplies uncertainty-aware aggregation and can catch ranking reversals; it does not decide whether an individual generated rollout or world-model verdict is admissible. The algorithmic-unit-test and leakage papers likewise provide neighboring principles, not the exact gate.

The problem is that the exact broad proposition in Lead 1 is already claimed by closer work. `WorldRoamBench` decides whether a rollout enters a physics comparison at all. *Validate the Dream* decides which evidence ladder a world-model verdict has satisfied before it can be trusted as assurance evidence. A reviewer can therefore say:

> The S103 package is a narrower retrieval-arm/provenance instantiation of an existing validity/admissibility idea, demonstrated on one frozen consumer and an exposed finite panel.

That objection is materially stronger than a generic “checklist” objection because the nearest paper uses the words **validity gate** and operationalizes exclusion before scoring. The project has a meaningful narrower distinction — it gates attribution between arms rather than only output eligibility — but no cross-system demonstration that this distinction transfers or changes a published conclusion. The ledger’s own correction from CausVid HIT to CLEAN shows why the four-tuple is valuable as internal discipline; it does not establish external novelty.

## Lead 2 — Steady-Forcing’s open call

[arXiv:2606.14732, *Steady-Forcing: Balancing Spatial Persistence and Motion Continuity in Long-Horizon Nature Video Diffusion*](https://arxiv.org/abs/2606.14732) explicitly says that generic VBench aggregate scores under-penalize fixed-camera artifacts, can reward drift-induced optical flow as Dynamic Degree, and do not directly penalize texture hardening or flow stagnation. That statement is verified on the arXiv abstract.

The named gap is no longer open. [arXiv:2608.28694, *SNF-Bench: Separating Static Drift from Natural Flow in Long-Horizon Fixed-Camera Video Generation*](https://arxiv.org/abs/2608.28694), submitted 2026-08-27, directly separates static support from dynamic flow and reports static fidelity, flow persistence with absolute magnitude, and drift leakage. Its abstract also describes mechanistic validation: injected translation/rotation/scale drift and progressive late freezing must move the intended factors selectively. This is a direct fill of the task-specific static-camera nature-flow evaluation gap, not just a nearby generic benchmark.

The project cannot reach SNF-Bench as a contribution at zero GPU from its actual assets. The existing VMem panel is two exposed RGB-D indoor sequences with camera-conditioned view generation; it contains no fixed-camera nature-flow corpus, static-support/flow masks, or long-horizon nature rollouts. A CPU-only implementation of the score formulas over already-saved suitable videos might be possible, but no such videos are present in the project assets (**UNVERIFIED** whether an external released-output reuse route could supply them). Producing and comparing the required model outputs would require inference compute and a new data/protocol scope, which the withdrawn tranche and this run forbid.

## Q3 — Strongest claim available from the actual assets

If a reviewer forced one sentence, the strongest defensible candidate would be:

> **“A score-independent audit protocol for retrieval-conditioned video comparisons can reject order-dependent arms and license sealed-output reuse only when arm-state isolation, consumer-input byte identity, provenance linkage, and a predeclared discard rule pass, as demonstrated by a finite VMem worked example.”**

The single strongest objection is:

> **“This is a single-consumer protocol engineering report subsumed at the principle level by `WorldRoamBench`’s validity gate and the L0–L4 admissibility ladder, with no cross-system held-out external validity, no demonstrated change to a published ranking, and no outside adoption.”**

The sentence is therefore a description of the project’s most valuable asset, not an authorization to call it a new evaluation method. The negative repair result (−0.016 dB under a +0.20 dB predeclared threshold) is a useful example of disciplined stopping; it does not turn the gate into a metric or benchmark contribution.

## Q4 — Cost and venue

For the sentence above, using only the assets already present:

- **New GPU:** **0 GPU-hours.** This is a packaging/reanalysis claim; no new generation is needed or authorized.
- **Work:** **2–4 calendar weeks, UNVERIFIED estimate**, for a clean artifact, independent source re-check, explicit denominators, and a reproducible CPU-only checker. This estimate is not a recorded experiment duration.
- **Venue:** at the current evidence level, **workshop or artifact/engineering report** is the honest ceiling. A main track or evaluation/datasets track would require independent systems and a reusable artifact demonstrated beyond this consumer; TMLR would still face the same external-validity and contribution-scope objection. Those additions are not feasible under the current no-GPU/no-new-generation boundary.

A full cross-system validity contribution would have an unknown, nonzero compute and engineering cost; it is **UNVERIFIED** and outside this run. No venue acceptance is implied.

## Q5 — Final ruling

**AXIS-G-OCCUPIED — (g1) metrics, (g2) benchmarks, and (g3) validity/admissibility machinery are all occupied at the claim level needed for a new contribution.**

The only surviving description is a narrow, internally demonstrated retrieval-arm audit worked example. It does not clear the project’s recorded diagnostic bar (cross-system external validity, conclusion impact, and external adoption). The evidence therefore supports closeout/record preservation, not reopening the method search, the 800 GPU-hour tranche, or `novelty_authorization`.

## Reference list used for the occupancy ruling

The tables above contain the arXiv ID, exact title, and direct primary link for every paper used in the ruling. The decisive records are:

1. arXiv:2606.31672 — *WorldRoamBench: An Open-World Benchmark for Long-Horizon Stability of Interactive World Models*.
2. arXiv:2607.07196 — *Validate the Dream Before You Trust Its Verdict: Admissibility for World-Model Simulators*.
3. arXiv:2608.28694 — *SNF-Bench: Separating Static Drift from Natural Flow in Long-Horizon Fixed-Camera Video Generation*.
4. arXiv:2606.14732 — *Steady-Forcing: Balancing Spatial Persistence and Motion Continuity in Long-Horizon Nature Video Diffusion*.
5. arXiv:2108.13264 — *Deep Reinforcement Learning at the Edge of the Statistical Precipice*.
6. arXiv:2310.17867 — *Reproducibility in Multiple Instance Learning: A Case For Algorithmic Unit Tests*.
7. arXiv:2207.07048 — *Leakage and the Reproducibility Crisis in ML-based Science*.

**No existing repository file was intentionally modified by this review.**
