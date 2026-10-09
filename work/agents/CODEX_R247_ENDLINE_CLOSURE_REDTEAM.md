# R247 END-LINE closure red-team

## Narrow primary-source search

Queries targeted occlusion/reappearance, hidden-surface geometry, frame/provenance interventions, and selective geometric prediction.

| Source | Link / identifier | Direct overlap / counterexample assessment |
|---|---|---|
| **Do VLMs Understand 3D Scenes or Just Catalogue Objects?** | arXiv:2605.20448, https://arxiv.org/abs/2605.20448 | **Direct geometry counterexample:** 3,034-sample benchmark explicitly probes depth-ordered occlusion with counterfactual operationalisations and reports severe VLM failures. This already supplies hidden-surface/occlusion falsification, though not producer-provenance reveal. |
| **SPATIALUNCERTAIN** | https://zhangyuejoslin.github.io/spatialuncertain/ | **Direct abstention/geometry overlap:** controlled 3D benchmark with occlusion and perspective ambiguity where abstention is appropriate. It subsumes geometry-aware uncertainty evaluation without provenance-only intervention. |
| **CAPTURE: Occluded Object Counting** | ICCV 2025, https://www.openaccess.thecvf.com/content/ICCV2025/papers/Pothiraj_CAPTURE_Evaluating_Spatial_Reasoning_in_Vision_Language_Models_via_Occluded_ICCV2025_paper.pdf | **Direct occlusion benchmark overlap:** compares occluded/unoccluded versions to test spatial reasoning degradation. No hidden producer-frame certificate mechanism. |
| **COMFORT / FoREST / ViewSpatial-Bench** | arXiv:2410.17385; https://aclanthology.org/2025.emnlp-main.1772.pdf; https://en.papernotes.org/ECCV2026/multimodal_vlm/viewspatial-bench_evaluating_multi-perspective_spatial_localization_in_vision-la/ | **Direct frame-of-reference overlap:** camera/person/reference-frame ambiguity already benchmarked. |
| **BCEA / SIEVES** | arXiv:2606.16667; arXiv:2604.25855 | **Direct selective evidence overlap:** active acquisition and evidence-scored abstention already test whether additional evidence changes answering. |
| **Peeking Behind Objects / Behind the Veil / OCC-MLLM-V2** | arXiv:1807.08776; CVPR 2024; DOI 10.1016/j.jvcir.2026.104887 | **Direct hidden-surface reconstruction overlap:** occluded-region geometry is explicitly modeled or benchmarked. |

## Counterexample and decision

These sources provide material counterexamples to any broad claim that occlusion/reappearance, hidden-surface geometry, frame ambiguity, or geometry-aware abstention lacks a benchmark mechanism. The remaining conjunction—same visible artifact, provenance-only reveal, hidden counter-world, false-unique metric—was not directly found in this bounded search, but R244 already shows it is non-identifiable without owner packet, sealing, and side-channel audits.

**Decision: keep END-LINE.** No directly inspected source reopens a defensible, identifiable contribution under current Branch B evidence restrictions. The narrow conjunction remains a future falsifiable question only; it is not a benchmark contribution now.

## Required evidence to reopen

A readable owner packet must provide canonical paired items, hidden-world commitments, independent geometry adjudication, provenance-only versus neutral intervention controls, leakage/side-channel audit, and held-out false-unique metrics. Without these, no counterexample defeats closure.

## Status

`method_status=END-LINE`; `benchmark_only=true`; `new_method_validated=false`; `novelty_authorization=NONE`; remain `B_STATIC_ONLY` with no code/data/model/parser/benchmark/GPU/Slurm/evaluation/receipt/flag actions.
