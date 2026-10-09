# R243 CGLR gap red-team

## Queries

- `vision language provenance source attribution benchmark metadata reference frame uncertainty paper`
- `active evidence acquisition provenance reveal multimodal selective prediction benchmark`
- `camera reference frame ambiguity benchmark vision language provenance metadata`

## Direct and partial overlaps

| Source | Identifier / official link | Overlap with provenance-only reveal distinction |
|---|---|---|
| **COMFORT: Do Vision-Language Models Represent Space and How?** | arXiv:2410.17385; https://arxiv.org/abs/2410.17385 | **Direct frame ambiguity overlap:** evaluates multiple spatial frames of reference and ambiguity. It does not test false-unique certificate acceptance under hidden producer provenance. |
| **FoREST: Frame of Reference Evaluation in Spatial Reasoning Tasks** | EMNLP 2025; https://aclanthology.org/2025.emnlp-main.1772.pdf | **Direct reference-frame overlap:** benchmark explicitly evaluates FoR comprehension and ambiguity. Hidden provenance intervention remains untested in the accessible description. |
| **ViewSpatial-Bench** | ECCV 2026 project note: https://en.papernotes.org/ECCV2026/multimodal_vlm/viewspatial-bench_evaluating_multi-perspective_spatial_localization_in_vision-la/ | **Direct perspective metadata overlap:** camera/person reference frames, geometry-derived labels, ambiguity filtering. It changes explicit reference framing, not a provenance-only reveal controlling false-unique acceptance. |
| **MAVIS: Multimodal Source Attribution in Long-form VQA** | AAAI 2026, DOI 10.1609/aaai.v40i39.40585; https://ojs.aaai.org/index.php/AAAI/article/view/40585 | **Direct source-attribution overlap:** fact-level citations and groundedness. It evaluates attribution quality, not hidden producer-frame counter-world rejection. |
| **Look Again Before You Abstain (BCEA)** | arXiv:2606.16667; https://doi.org/10.48550/arXiv.2606.16667 | **Direct active-intervention overlap:** answer/abstain/acquire with claim-specific visual interventions and conformal controls. Intervention is visual re-examination, not provenance-only reveal. |
| **SIEVES: Selective Prediction through Visual Evidence Scoring** | arXiv:2604.25855; https://arxiv.org/abs/2604.25855 | **Direct selective-prediction overlap:** evidence localization quality drives coverage/risk selection. No hidden provenance manipulation or false-unique certificate test. |
| **REVEAL-Bench** | Official implementation: https://github.com/TrustMedia-zju/REVEAL | **Partial forensic evidence overlap:** multi-view forensic evidence and chain-of-evidence reasoning. Its task is image-generation detection, not provenance-only intervention and ambiguity rejection. |

## Red-team decision

R242’s gap is narrower after this search but not falsified outright. COMFORT/FoREST/ViewSpatial cover reference-frame ambiguity; MAVIS covers source attribution; BCEA/SIEVES cover active evidence acquisition and selective prediction. A broad claim that “no benchmark studies provenance, reference frames, or evidence-based abstention” is rejected. The only surviving candidate is the conjunction: **same visible artifact + provenance-only reveal + hidden counter-world + false-unique acceptance metric**.

## Falsifying experiment

A static preregistered 2×2 protocol must compare provenance-only reveal with a provenance-neutral metadata intervention on hidden counter-world and known-unique controls, matched for token count, formatting, frame wording, evidence order, and side channels. Include COMFORT/FoREST-style explicit frame controls, MAVIS-style citation/source controls, and BCEA/SIEVES-style acquisition/grounding baselines. If any baseline matches provenance-only reveal, or if neutral metadata produces the same selective effect, the CGLR distinction is rejected.

## Uncertainty and prerequisites

Search was bounded and terminology may miss work using source identity, camera convention, metadata provenance, or certificate validation. No full implementation audit or experiment was run. Required evidence remains absent: canonical paired interventions, sealed outcomes, leakage/side-channel audit, independent adjudication, and held-out results.

## Status

`method_status=END-LINE`; `benchmark_only=true`; `new_method_validated=false`; `novelty_authorization=NONE`; remain `B_STATIC_ONLY` with no transition or execution.
