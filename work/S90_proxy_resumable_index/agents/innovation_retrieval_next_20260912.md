# Innovation retrieval next round (2026-09-12)

- Retrieval time: 2026-09-12 07:23 UTC.
- Scope: English primary sources, 2024--2026, focused on history memory, future prediction, geometric/spatial consistency, compute-limited memory, or calibrated uncertainty.
- Exclusions: R2M-Bench, WorldPack, GIM-World, and CAP were deliberately not repeated.
- Boundary: this is a near-neighbor audit. It does not establish novelty or validate GRC-Pilot.

## 1. Long-Context State-Space Video World Models (ICCV 2025)

Primary source: [CVF ICCV 2025 paper page/PDF](https://openaccess.thecvf.com/content/ICCV2025/papers/Po_Long-Context_State-Space_Video_World_Models_ICCV_2025_paper.pdf), title and abstract also indexed from the official CVF repository. The paper evaluates long-term memory through spatial retrieval and reasoning over extended horizons, and uses a state-space architecture for efficient autoregressive inference.

Mechanism difference from GRC-Pilot: this work makes the *model state representation and recurrent inference* efficient; it does not, from the indexed abstract, select individual history observations using calibrated geometric risk and then test their incremental effect on a held-out future geometric answer. GRC-Pilot is a protocol-level test: freeze a world-model/inference budget, rank candidate historical observations, and measure future pose/depth/reprojection error. The overlap is long-horizon spatial memory, so any claim that “long-term memory itself” is new would be unsafe.

Falsifiable prediction for GRC-Pilot: at equal number of retained frames and equal inference budget, a risk-ranked selector should reduce future geometric error relative to recency and random selectors; if the recurrent state model already matches or beats it without risk ranking, the proposed selector has no demonstrated value.

## 2. WORLDMEM: Long-term Consistent Video World Models (NeurIPS 2025)

Primary source: [NeurIPS 2025 conference paper PDF](https://papers.neurips.cc/paper_files/paper/2025/file/470629a47e2d65ce0606c40055df5d26-Paper-Conference.pdf). The official paper record describes an autoregressive world model with memory representation/retrieval for long-term consistent interactive video prediction.

Mechanism difference from GRC-Pilot: WORLDMEM addresses long-term consistency using a learned memory representation/retrieval mechanism and current-state/history information. GRC-Pilot instead asks whether a *pre-declared geometric-risk score* predicts future geometric benefit under a fixed history budget. Retrieval similarity or learned relevance is not equivalent to calibrated risk, and a long-term consistency score is not equivalent to future metric-grounded geometric error. However, this is a close baseline family: GRC experiments must include a learned retrieval/relevance baseline if the code and data permit.

Falsifiable prediction for GRC-Pilot: under matched retained-frame count, compute, and future camera/action sequence, calibrated geometric-risk ranking must outperform WORLDMEM-style relevance/recency ranking on held-out reprojection/depth error in at least the prespecified multi-scene split. Failure means the risk signal is not useful as a selector.

## 3. World Models That Know When They Don't Know: Controllable Video Generation with Calibrated Uncertainty (C3, arXiv 2512.05927, 2025 preprint)

Primary source: [arXiv abstract](https://arxiv.org/abs/2512.05927). The abstract states that C3 trains continuous-scale calibrated uncertainty for controllable video models using strictly proper scoring rules, latent-space uncertainty, and pixel-level heatmaps; it reports Bridge and DROID experiments and OOD detection.

Mechanism difference from GRC-Pilot: C3 calibrates uncertainty of *generated future video regions* and uses it for confidence/OOD detection. GRC-Pilot calibrates risk attached to *historical observations used as memory* and tests whether that risk predicts a future geometric answer. Thus “using calibrated uncertainty” is already occupied; the defensible distinction would have to be the history-level intervention, fixed-memory budget, and future geometric target. Because this source is an arXiv preprint, acceptance status is not assumed.

Falsifiable prediction for GRC-Pilot: history-level risk should predict future geometric error even after controlling for C3-style output uncertainty (if available); if output uncertainty alone explains all variance, the history-risk contribution is not independently supported.

## Reviewer-style synthesis

1. The strongest pressure is that long-horizon memory, memory retrieval, and calibrated uncertainty each already exist separately.
2. The narrow testable contribution remains the *intervention*: replace one history item while holding noise, action/camera path, retained-frame count, and compute fixed, then measure a pre-registered future geometric metric.
3. Required baselines are at least recency, random, visual/relevance retrieval, and a learned memory/recurrent-state baseline where reproducible.
4. Required claim boundary: until paired RGB-D/camera/future truth pass Gate 0 and the multi-scene experiment runs, GRC-Memory/GRC-Pilot status remains `candidate / novelty UNKNOWN / not validated`.
