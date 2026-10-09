# R242 CGLR prior-art falsification search

## Queries

1. `provenance reveal intervention false unique acceptance benchmark selective prediction abstention paper`
2. `vision language model uncertainty calibration abstention benchmark official code provenance metadata`
3. `selective prediction abstention conformal vision language benchmark ambiguity official implementation`

## Primary/official sources and overlap

| Source | Identifier / official link | Overlap assessment |
|---|---|---|
| **AbstentionBench: A Holistic Benchmark for LLM Abstention** | Official implementation: https://github.com/facebookresearch/AbstentionBench | **Direct outcome overlap, mechanism gap:** evaluates underspecified/unanswerable questions across 20 datasets and abstention scenarios. It does not isolate producer-frame provenance-only reveal or false-unique certificate acceptance. |
| **Learning Conformal Abstention Policies for Adaptive Risk Management in LLMs/VLMs** | arXiv:2502.06884; official code: https://github.com/sinatayebati/vlm-uncertainty | **Direct uncertainty/selective-prediction overlap:** conformal abstention, hallucination detection, calibration, coverage. No provenance-only reveal or hidden producer-frame intervention is specified. |
| **Certainly Uncertain: A Benchmark and Metric for Multimodal Epistemic and Aleatoric Awareness** | ICLR 2025; official page: https://www.microsoft.com/en-us/research/publication/certainly-uncertain-a-benchmark-and-metric-for-multimodal-epistemic-and-aleatoric-awareness/ | **Partial overlap:** contrastive answerable/unanswerable visual questions and confidence-weighted accuracy. Does not manipulate hidden producer provenance while holding visible artifact fixed. |
| **Look Again Before You Abstain: Budgeted Conformal Evidence Acquisition for Reliable VLM** | arXiv:2606.16667; https://doi.org/10.48550/arXiv.2606.16667 | **Closest intervention overlap:** adds visual evidence acquisition (zoom/crop/claim-specific intervention) and compares answer/abstain/acquire. The intervention is visual evidence acquisition, not provenance-only reveal; it warns naive acquisition can break conformal guarantees. |
| **Conformal Linguistic Calibration** | NeurIPS 2025; Microsoft page: https://www.microsoft.com/en-us/research/publication/conformal-linguistic-calibration-trading-off-between-factuality-and-specificity/ | **Partial overlap:** calibrated answer sets/linguistic uncertainty, not hidden provenance or certificate-level false uniqueness. |
| **RoboAbstention / The Yes-Man Syndrome** | Official project: https://purseclab.github.io/RoboAbstention/ | **Direct ambiguity outcome overlap:** embodied false-premise, ambiguous referent, underspecification, and abstention. No provenance-only reveal or hidden-label counter-world control. |

## Falsification conclusion

Adjacent work substantially covers abstention, confidence calibration, answer-set uncertainty, and evidence acquisition. I found no primary source in these bounded queries that explicitly holds the visible artifact fixed, reveals only producer-frame/label provenance, and measures false-unique acceptance against a hidden counter-world. This is a **mechanism-level gap candidate**, not a novelty finding: generic abstention or evidence-acquisition baselines may explain any observed effect.

## Uncertainty

Search vocabulary may miss work using provenance, metadata, reference-frame, source attribution, or selective prediction terms. Several relevant 2026 papers are recent preprints/official pages; no exhaustive survey or full-text implementation audit was performed. Therefore “not found” is bounded evidence only.

## Falsifiable discriminating protocol

Specify a preregistered 2×2 static design: provenance-only reveal vs provenance-neutral metadata intervention, crossed with hidden counter-world vs known-unique control. Canonicalize token count, formatting, order, envelope size, timing, and side channels; seal outcomes; use generic abstention and conformal evidence-acquisition baselines. H1 predicts a selective reduction in false-unique acceptance only for provenance reveal on counter-worlds, with unique controls preserved. Reject CGLR if neutral intervention matches provenance reveal, if side-channel/leakage audits fail, or if baseline performance is indistinguishable.

## Status

`method_status=END-LINE`; `benchmark_only=true`; `new_method_validated=false`; `novelty_authorization=NONE`; no code/data/model/GPU/evaluation execution occurred.
