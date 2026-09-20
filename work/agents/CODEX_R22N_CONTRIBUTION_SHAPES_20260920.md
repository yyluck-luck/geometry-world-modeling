this round was run on `gpt-5.6-sol` at `xhigh` reasoning effort, **not** on `gpt-6-astra / ultra`, because astra returned `model is at capacity` four consecutive times (82k / 131k / 22k / 3.7k tokens). The owner authorised the substitution. Mark your file `PRODUCED_BY=gpt-5.6-sol/xhigh; PENDING_ASTRA_REVIEW`.

# Round 22-N — How accepted world-model papers construct novelty

`PRODUCED_BY=gpt-5.6-sol/xhigh; PENDING_ASTRA_REVIEW`

## Executive ruling

**SHAPE-AVAILABLE — measurement / validity apparatus:** a state-isolation audit based on a
four-tuple (writer on call A, public A→B sequence, exact consumer on B, and a dominance check
that no recompute/overwrite/reset covers the field). This is the strongest zero-GPU shape that
the current assets can support. It is a proposal, not a validated new method, and it does not
authorize changing either `new_method_validated=false` or `novelty_authorization=NONE`.

The important qualification is that “shape available” is not “publishable now.” Existing
evidence is still **INSUFFICIENT for a publishable diagnostic claim**: the audit is a convenience
panel, has no external sampling frame or independent adoption, and the two strongest cases split
oracle evidence from measured consequence. If those gaps cannot be closed with a CPU/static
artifact and independent review, the honest end state becomes `INSUFFICIENT`, not a method claim.

## 1. What was checked locally

### Pinned VMem source

The three named copies were byte-identical under SHA-256 (`90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e`):

- `work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py`
- `work/S17_cpu_preflight/original/modeling/pipeline.py`
- `work/S102_gate0_3dmatch/adapter_v1/sources/vmem_pipeline.py`

In each copy the requested lines are present:

- line 1249: `get_context_info(target_c2ws, use_non_maximum_suppression)`;
- line 1263: `torch.cat([context_c2ws, target_c2ws], dim=0)`;
- line 1265: `get_translation_scaling_factor(all_c2ws)`.

The positive writes to `self.c2ws` occur at line 180 (`self.c2ws = [c2w]`) and line 1297
(`self.c2ws.append(...)`), with no property setter. A precision correction to the brief is
needed: line 1360 also mutates the list with `self.c2ws.pop()`. Thus “two write sites” is true
for assignment/append, but not for all mutations. This matters to a lifecycle audit because a
pop is a state transition even though it is not a new value write.

### Project evidence boundary

The project summary records a convenience audit of 20 systems: static `HIT=2` (VMem and GEN3C),
`NEAR=2`, `CLEAN=15`, and `SUSPECT-UNTRACED=1`; frozen-weight end-to-end measurements are `0`.
The four-tuple correctly reclassified CausVid from an apparent hit to CLEAN. The GEN3C result is
a source-level lifecycle defect, not a generated-video experiment. The VMem number is the
technical report's `memory_nms_on_clean − memory_nms_on (leaked)` contrast, `+0.245 dB` over a
14-window paired panel and two seeds; it is **not** a memory-versus-static improvement.
Therefore the two cases cannot be combined into “oracle plus measured consequence.”

Primary local records: [`docs/IDEAS_SUMMARY_FOR_REPORT_20260920.md`](../docs/IDEAS_SUMMARY_FOR_REPORT_20260920.md),
[`docs/report/TECHNICAL_REPORT_20260918.md`](../docs/report/TECHNICAL_REPORT_20260918.md),
[`RESEARCH_MEMORY.md`](../RESEARCH_MEMORY.md), and [`RESEARCH_PRINCIPLES.md`](../RESEARCH_PRINCIPLES.md).

## 2. Evidence method and corpus

I used a **stratified convenience sample**, not a random sample: two accepted papers were sought
for each candidate contribution shape, and one extra paper was used where a paper naturally
instantiates two shapes. The denominator below is therefore descriptive only; it cannot be
interpreted as the prevalence of contribution shapes in the field.

“Accepted” means that I checked an official CVPR/ICCV/NeurIPS/ICLR/ICML proceedings record or
official proceedings page. An arXiv identifier is included for traceability. Papers whose venue
could not be confirmed are not counted in the 18-paper denominator. Titles below are the exact
accepted-paper titles; where the accepted title differs from the arXiv shorthand, that is stated.

The following 18 verified accepted papers form the primary denominator (18 unique papers):

1. [Diffusion Forcing: Next-token Prediction Meets Full-Sequence Diffusion](https://proceedings.neurips.cc/paper_files/paper/2024/hash/2aee1c4159e48407d68fe16ae8e6e49e-Abstract-Conference.html) — **NeurIPS 2024**, arXiv:2407.01392.
2. [Self Forcing: Bridging the Train-Test Gap in Autoregressive Video Diffusion](https://proceedings.neurips.cc/paper_files/paper/2025/hash/f4823f831af67a3ef15e41a85434422a-Abstract-Conference.html) — **NeurIPS 2025**, arXiv:2506.08009.
3. [Learning Interactive Real-World Simulators](https://proceedings.iclr.cc/paper_files/paper/2024/hash/c4d66eae503694424123b93ac0fbaf17-Abstract-Conference.html) — **ICLR 2024**, arXiv:2310.06114.
4. [Position: Video as the New Language for Real-World Decision Making](https://proceedings.mlr.press/v235/yang24z.html) — **ICML 2024**, arXiv:2402.17139. The accepted proceedings title includes the prefix “Position:”.
5. [Navigation World Models](https://openaccess.thecvf.com/content/CVPR2025/html/Bar_Navigation_World_Models_CVPR_2025_paper.html) — **CVPR 2025**, arXiv:2412.03572.
6. [Video World Models with Long-term Spatial Memory](https://openreview.net/pdf?id=HbTxc6U1fO) — **NeurIPS 2025**, arXiv:2506.05284.
7. [EscherNet: A Generative Model for Scalable View Synthesis](https://openaccess.thecvf.com/content/CVPR2024/html/Kong_EscherNet_A_Generative_Model_for_Scalable_View_Synthesis_CVPR_2024_paper.html) — **CVPR 2024**, arXiv:2402.03908.
8. [Cameras as Relative Positional Encoding](https://openreview.net/pdf?id=6aae4eff4f0e621cb9a82817adf18917131eaa55) — **NeurIPS 2025**, arXiv:2507.10496.
9. [LongLive: Real-time Interactive Long Video Generation](https://proceedings.iclr.cc/paper_files/paper/2026/hash/91a1610c6ed9e02d33f826b46f472b92-Abstract-Conference.html) — **ICLR 2026**, arXiv:2509.22622.
10. [GEN3C: 3D-Informed World-Consistent Video Generation with Precise Camera Control](https://openaccess.thecvf.com/content/CVPR2025/html/Ren_GEN3C_3D-Informed_World-Consistent_Video_Generation_with_Precise_Camera_Control_CVPR_2025_paper.html) — **CVPR 2025 Highlight**, arXiv:2503.03751.
11. [Stable Virtual Camera: Generative View Synthesis with Diffusion Models](https://openaccess.thecvf.com/content/ICCV2025/html/Zhou_Stable_Virtual_Camera_Generative_View_Synthesis_with_Diffusion_Models_ICCV_2025_paper.html) — **ICCV 2025**, arXiv:2503.14489.
12. [CameraCtrl: Enabling Camera Control for Video Diffusion Models](https://proceedings.iclr.cc/paper_files/paper/2025/hash/f98fd73d59d8494489ea970747b91fe4-Abstract-Conference.html) — **ICLR 2025**, arXiv:2404.02101.
13. [How Far is Video Generation from World Model: A Physical Law Perspective](https://proceedings.mlr.press/v267/kang25g.html) — **ICML 2025**, arXiv:2411.02385.
14. [Is Your World Simulator a Good Story Presenter? A Consecutive Events-Based Benchmark for Future Long Video Generation](https://openaccess.thecvf.com/content/CVPR2025/html/Wang_Is_Your_World_Simulator_a_Good_Story_Presenter_A_Consecutive_CVPR_2025_paper.html) — **CVPR 2025**, arXiv:2412.16211.
15. [VBench: Comprehensive Benchmark Suite for Video Generative Models](https://openaccess.thecvf.com/content/CVPR2024/html/Huang_VBench_Comprehensive_Benchmark_Suite_for_Video_Generative_Models_CVPR_2024_paper.html) — **CVPR 2024**, arXiv:2311.17982.
16. [WorldModelBench: Judging Video Generation Models As World Models](https://proceedings.neurips.cc/paper_files/paper/2025/hash/4ec03ed08a3fcb59e1c815b5598beff1-Abstract-Datasets_and_Benchmarks_Track.html) — **NeurIPS 2025 Datasets and Benchmarks Track**, arXiv:2502.20694.
17. [SANA-Video: Efficient Video Generation with Block Linear Diffusion Transformer](https://proceedings.iclr.cc/paper_files/paper/2026/hash/41b93c59da0d0f835907fd661d419db2-Abstract-Conference.html) — **ICLR 2026**, arXiv:2509.24695.
18. [MotionStream: Real-Time Video Generation with Interactive Motion Controls](https://proceedings.iclr.cc/paper_files/paper/2026/hash/0cece806cd3d1dfad4a893f016ad3d7d-Abstract-Conference.html) — **ICLR 2026**, arXiv:2511.01266.

Context only: [Matrix-Game: Interactive World Foundation Model](https://arxiv.org/abs/2506.18701),
arXiv:2506.18701, was not assigned a confirmed venue in the checked record and is therefore
**UNVERIFIED** and excluded from the denominator. The same rule applies to other project anchors
whose acceptance record was not independently confirmed in this pass.

## 3. Taxonomy of contribution shapes (Q1)

The shapes are not mutually exclusive. For the distribution in Section 4 I assign each paper a
single primary shape; in this section I also show legitimate secondary readings.

| Shape | At least two accepted examples and the paper's novelty framing | Typical resources | Zero GPU? |
|---|---|---|---|
| **1. New mechanism on an existing task** | **Diffusion Forcing** (NeurIPS 2024, arXiv:2407.01392) argues that independently noised tokens plus full-sequence denoising bridge next-token prediction and diffusion, enabling variable-horizon generation. **Self Forcing** (NeurIPS 2025, arXiv:2506.08009) argues that training on self-generated autoregressive rollouts with a holistic video loss closes the train/test exposure gap. | New objective/training loop, model changes, video data, substantial training and ablations. | **No** for a new empirical result; only a paper-level design discussion is zero GPU. |
| **2. Problem reframing** | **Learning Interactive Real-World Simulators** (ICLR 2024, arXiv:2310.06114) reframes video generation as an interactive simulator on which planners/RL can act. **Position: Video as the New Language for Real-World Decision Making** (ICML 2024, arXiv:2402.17139) reframes video as a common interface for perception, planning, action and environment simulation, rather than a passive prediction target. | A credible new use case, task protocol, baselines, usually a model or simulator and downstream evaluation. | **Partly**: the reframing and protocol can be designed on CPU; demonstrating the claimed capability normally cannot. |
| **3. New task / capability definition** | **Navigation World Models** (CVPR 2025, arXiv:2412.03572) makes action-conditioned future-video simulation and trajectory ranking in unfamiliar environments the capability being evaluated. **Video World Models with Long-term Spatial Memory** (NeurIPS 2025, arXiv:2506.05284) makes spatial revisitation and long-term memory a first-class world-model capability, with explicit 3-D/episodic memory. | New task contract, data/annotations, evaluation protocol, often a trained model and long-horizon rollouts. | **Protocol yes; capability evidence no** under the current frozen-consumer and no-GPU constraints. |
| **4. Representation substitution** | **EscherNet** (CVPR 2024, arXiv:2402.03908) replaces ordinary view-conditioning with a scalable generative/implicit 3-D representation plus camera positional encoding. **Cameras as Relative Positional Encoding** (NeurIPS 2025, arXiv:2507.10496) replaces absolute ray-map conditioning with relative projective camera encoding and argues for transfer across novel-view, stereo and spatial-cognition tasks. | New representation, architecture/training, data diversity and controlled comparisons. | **No** for a new trained representation; static analysis of an existing representation is zero GPU but is a different claim. |
| **5. Regime extension** | **LongLive** (ICLR 2026, arXiv:2509.22622) extends short-clip video diffusion to interactive minute-scale/240-second streaming with a reported real-time regime. **MotionStream** (ICLR 2026, arXiv:2511.01266) extends interactive generation to sub-second/real-time, effectively unbounded streaming with motion controls. MotionStream is also an efficiency paper; the overlap is substantive rather than an error. | Training/tuning for long context, memory/cache engineering, long videos, latency profiling and often high-end GPUs. | **No** for reaching the new horizon/latency regime. |
| **6. System integration** | **GEN3C** (CVPR 2025 Highlight, arXiv:2503.03751) composes depth, a 3-D point cache, camera rendering and video diffusion so explicit geometry supplies camera control/consistency. **CameraCtrl** (ICLR 2025, arXiv:2404.02101) composes a camera-control module with a video diffusion backbone and training recipe to make camera motion controllable. **Stable Virtual Camera** (ICCV 2025, arXiv:2503.14489) is a further integration example: one generalist diffusion system plus training/sampling design handles arbitrary view targets and trajectories. | Integration engineering, interface contracts, data preparation and end-to-end validation; often no single isolated “new block,” but still significant compute. | **Usually no** for a publishable end-to-end result; CPU static integration tests are possible. |
| **7. Negative / limitation result** | **How Far is Video Generation from World Model: A Physical Law Perspective** (ICML 2025, arXiv:2411.02385) constructs a physical-law testbed and argues that in-distribution scaling does not yield robust OOD law abstraction. **Is Your World Simulator a Good Story Presenter?** (CVPR 2025, arXiv:2412.16211) shows that detail/quality metrics can hide failure on consecutive-event story completion and reports the limitation as the central result. | Carefully controlled counterexamples, baselines, evaluation, and enough runs to exclude an implementation artifact. | **Sometimes**: source-level or existing-output counterexamples can be CPU-only; new model-wide negative claims may need inference. |
| **8. Measurement contribution** | **VBench** (CVPR 2024, arXiv:2311.17982) contributes a hierarchical 16-dimension benchmark and human-aligned evaluation rather than a generator. **WorldModelBench** (NeurIPS 2025 Datasets and Benchmarks Track, arXiv:2502.20694) contributes a world-model-specific benchmark with human labels and automated judging because ordinary video metrics miss physical/instruction violations. | Dataset/manifest design, metric validity, labels, baselines, reproducible evaluator and adoption-oriented packaging. | **Yes for a static/CPU audit or evaluator over existing artifacts; no for fresh large-scale generation or human labeling.** This is the only clearly reachable shape here. |
| **9. Scaling / efficiency** | **SANA-Video** (ICLR 2026, arXiv:2509.24695) argues that a block-linear diffusion transformer and constant-memory state change the cost/latency regime, including consumer-GPU minute video. **Stable Virtual Camera** (ICCV 2025, arXiv:2503.14489) also has a scaling/efficiency reading: one generalist model and sampling scheme replaces per-scene NeRF-style optimization across many views/trajectories. (The same paper is counted under system integration only in the primary distribution.) | Architectural efficiency work, profiling, careful quality-at-equal-budget comparisons and usually substantial training. | **No** for a new scaling claim; auditing reported numbers is zero GPU but does not reproduce them. |

The empirical pattern is therefore not “novelty equals an unoccupied mechanism axis.” Accepted papers
frequently change the object being measured, the regime, the representation, the system boundary,
or the validity apparatus.

## 4. Distribution in the inspected corpus (Q2)

For an additive denominator, I assigned each of the 18 unique papers one **primary** shape. This
coding is a reporting device, not a claim that papers have only one contribution shape.

| Primary shape | Count | Fraction of this convenience sample |
|---|---:|---:|
| New mechanism | 2 | 2/18 = 11.1% |
| Problem reframing | 2 | 2/18 = 11.1% |
| New task/capability | 2 | 2/18 = 11.1% |
| Representation substitution | 2 | 2/18 = 11.1% |
| Regime extension | 2 | 2/18 = 11.1% |
| System integration | 2 | 2/18 = 11.1% |
| Negative/limitation | 2 | 2/18 = 11.1% |
| Measurement | 2 | 2/18 = 11.1% |
| Scaling/efficiency | 2 | 2/18 = 11.1% |
| **Total** | **18** | **100%** |

This flat result is an artefact of the deliberately balanced sample, not a field estimate. It is
not evidence that each shape is equally common. The defensible conclusion is weaker and more useful:
shape 1 is plainly **not the only accepted shape**, and the project’s former mechanism-only search
was an unrepresentative target. A random, venue-stratified corpus would be needed to estimate real
fractions.

## 5. What this project tried, and what it never tried (Q3)

### Mapping the project’s directions

| Project direction | Shape(s) in the taxonomy | Status in the project |
|---|---|---|
| Evidence read/retrieval and weighted fusion (axis a) | Mechanism; measurement as a possible evaluator | Occupied/closed; the common squared-error fusion objective was algebraically degenerate. |
| Conditional representation (axis b) | Representation substitution; mechanism | Occupied by prior art (including EscherNet and PRoPE); no new consumer change authorized. |
| Persistent state representation/write (axis c) | Representation substitution; mechanism | Occupied by VMem/GEN3C; pinned VMem lifecycle was audited, not changed. |
| Request-view decomposition (axis d) | Mechanism; system integration | Occupied by existing camera/view systems; no new training allowed. |
| Cross-call transfer dynamics (axis e) | Mechanism; regime/capability | Occupied by Self Forcing and related work; frozen consumer prevents a new training regime. |
| Geometry–generation coupling (axis f) | System integration; representation | Occupied by GEN3C/Voyager-style systems; no upstream or weight modification allowed. |
| Within-call inference dynamics (axis h) | Mechanism; scaling/efficiency | Occupied by Diffusion Forcing-style work; no inference-engine change was authorized. |
| Lifecycle state-isolation audit / four-tuple | Measurement; negative/limitation; problem reframing | Actually attempted as source-level infrastructure and a 20-case audit. It was not yet run as an externally validated paper artifact. |
| Measurement/evaluation axis (g) | Measurement | Explicitly excluded as a *contribution type* in the earlier method-only contract; infrastructure (order-invariance gate, pre-scoring census, byte identity, discard rules and four-tuple) was built but not presented as the contribution. C6 is now relaxed. |

### Shapes never attempted as a publishable proposal

1. **Regime extension** was never attempted. This is a deliberate consequence of the frozen
   consumer, zero-GPU requirement and withdrawn 800 GPU-hour tranche, not an accidental omission.
2. **Scaling/efficiency** was never attempted. It would require changing the model/inference
   regime or producing new equal-quality/latency evidence; the same compute and consumer
   constraints block it.
3. **System integration as the novelty claim** was never attempted. Ordinary wrappers and audit
   infrastructure existed, but the project did not claim a new publishable composition; calling
   existing components together would not by itself clear the contribution bar.

Problem reframing, new capability definition, negative/limitation analysis and measurement were
attempted late through the lifecycle-audit turn, but only as exploratory/static evidence. They are
not validated contributions. Representation and mechanism directions were attempted repeatedly and
were closed as occupied or infeasible. No direction changes `new_method_validated=false`.

## 6. Strongest reachable proposal (Q4)

### Reviewer-facing claim

> **For stateful released video/world-model systems, reset correctness cannot be inferred either
> from a field being absent from `reset()` or from a reset call being present. A four-tuple audit
> that links the writer on call A, the public A→B sequence, the exact consumer on B, and a
> dominance proof that no recompute/overwrite/reset covers that state is a falsifiable validity
> apparatus that reclassifies apparent lifecycle hits and exposes order-dependent stale-state
> paths.**

The available project evidence is consistent with this claim: the audit reclassified CausVid to
CLEAN; the 20-case convenience panel contains 15 CLEAN verdicts and one static GEN3C HIT; and the
VMem `+0.245 dB` contrast is kept in a separate measured-evidence bucket rather than used as an
oracle. The claim deliberately does **not** say that 15/20 is a prevalence estimate, that GEN3C
has a measured video consequence, or that VMem’s contrast validates a new method.

**Shape:** measurement / validity apparatus, with a secondary negative/limitation result.

**Accepted shape precedent:** VBench (CVPR 2024) and WorldModelBench (NeurIPS 2025 Datasets and
Benchmarks Track) demonstrate that a benchmark/validity apparatus can itself be the publishable
contribution. WorldModelBench is the closest precedent because it makes a previously under-measured
world-model validity property explicit and packages a reproducible judgment protocol.

### Strongest objection

The objection is not that the four-tuple is incoherent; it is that the current evidence does not
yet establish external validity or conclusion impact. The panel is convenience-sampled; the
source-level GEN3C case has no end-to-end run; VMem has a measured contrast but no defensible public
oracle; and `+0.245 dB` is a leak contrast on exposed development sequences, RGB PSNR only. A
reviewer can therefore say that the proposal is a careful internal audit, not a generally useful
measurement contribution. “15/20 CLEAN” is a reliability-looking count, not a prevalence result.

### What must be true for survival

1. Freeze the four-tuple, verdict classes and dominance rule before re-auditing; release manifests,
   code paths, hashes and negative controls.
2. Have an independent reviewer audit cases blind to the owner’s labels, and report agreement plus
   a comparison against the naive rules “missing from reset” and “reset call exists.” The key result
   should be a reproducible reclassification, not a hand-picked anecdote.
3. Add at least two or three independently released systems beyond VMem/GEN3C, including a known
   clean negative control and a positive case. Do not claim prevalence without a declared sampling
   frame.
4. For at least one positive case, show either a permitted end-to-end consequence or a fully
   reproducible static downstream invalid-state trace. If only static evidence is available, call
   it a static lifecycle defect and do not imply generated-video degradation.
5. Make the artifact CPU-runnable and adoptable: one command, immutable inputs, trace output,
   byte identity, and a clear separation between static HIT, measured HIT, NEAR and CLEAN.
6. Keep the VMem measurement separate from the audit claim. A future run may test it, but the
   current contrast cannot be used to manufacture the missing oracle/consequence conjunction.

This proposal is reachable with zero GPU **only in the static/CPU audit scope**. New video
generation, human labeling at scale, or a latency/quality demonstration would violate the current
run constraints and would need an explicitly re-authorized resource budget.

## 7. Final ruling (Q5)

**SHAPE-AVAILABLE — measurement / validity apparatus: the four-tuple state-isolation audit.**

It is the single strongest reachable shape and has accepted precedents (VBench and WorldModelBench).
The present project evidence is not yet enough to call it a publishable result; if the independent
review, cross-system cases and adoptable CPU artifact cannot be produced, the correct downgrade is
`INSUFFICIENT`. No part of this ruling changes `new_method_validated=false`,
`novelty_authorization=NONE`, the frozen-consumer constraint, or the withdrawn 800 GPU-hour tranche.

## 8. Review-layer limitation

The repository’s required external Astra review could not be completed in this run. The attempted
local Codex fallback failed before model output with an in-process app-server permission error
(`Operation not permitted`); it produced no substantive review. This file therefore records the
owner-authorized `gpt-5.6-sol/xhigh` substitution and remains `PENDING_ASTRA_REVIEW`. That failure
is a tooling limitation, not evidence for or against the contribution claim.
