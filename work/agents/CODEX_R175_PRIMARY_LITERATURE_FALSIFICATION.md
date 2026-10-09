# R175 Primary-literature falsification search (bounded)

**Scope and stop rule.** One bounded web search cycle (2026-09-23), using public paper/project pages or official implementations only. Target equivalence: (A) hidden producer-frame/camera-reference misdeclaration detection, (B) hidden-label false-unique certification, (C) ambiguity rejection equivalent to FUP/AReject. No project data, code, fixtures, runners, or evaluation were used. This is a literature falsification screen, not a novelty proof.

## Exact queries

1. `benchmark hidden camera frame convention misdeclaration producer frame evaluation dataset paper`
2. `benchmark false unique label certification ambiguity rejection evaluator paper`
3. `official implementation ambiguity rejection benchmark vision language model uncertainty abstention`

## Primary sources found

| Source (primary link) | What it actually evaluates | Relation to target |
|---|---|---|
| [Certainly Uncertain (ICLR 2025), Microsoft Research page](https://www.microsoft.com/en-us/research/publication/certainly-uncertain-a-benchmark-and-metric-for-multimodal-epistemic-and-aleatoric-awareness/) | 178K contrastive VQA pairs; makes questions unanswerable by image inpainting/caption prompting; confidence-weighted accuracy. | **Partial overlap with C:** uncertainty/unanswerability and calibration. It does not test producer-frame metadata, hidden label provenance, or a rule that rejects a claimed unique answer because multiple latent explanations remain. |
| [RoboAbstention official project page + dataset/code links](https://purseclab.github.io/RoboAbstention/) | 6,069 embodied image-instruction cases, eight abstention classes (missing/ambiguous referent, false premise, underspecification, infeasibility, capability, contradiction); auditable generation and abstention rates. | **Closest analogue to C:** explicit ambiguity/false-premise rejection. Its unit is whether an instruction is answerable/executable in an embodied scene, not whether a benchmark claim is uniquely certified under hidden producer-frame or hidden-label alternatives. No A/B mechanism is reported. |
| [When Robots Should Say “I Don’t Know” (CVPR 2026 paper/supplement)](https://openaccess.thecvf.com/content/CVPR2026/papers/Wu_When_Robots_Should_Say_I_Dont_Know_Benchmarking_Abstention_in_CVPR_2026_paper.pdf) | Embodied-QA abstention with ambiguity taxonomy; reports abstention recall/precision and whether explanations match the true uncertainty cause. | **Partial C overlap:** evaluates recognizing ambiguity and correct abstention reason. It does not establish hidden producer-frame identity, hidden-label uniqueness, or FUP-style certificate validity. (CVF PDF was access-blocked in this run; search result and title are recorded.) |
| [Phantom of Benchmark Dataset (WACV 2023 workshop)](https://openaccess.thecvf.com/content/WACV2023W/DNOW/papers/Chung_Phantom_of_Benchmark_Dataset_Resolving_Label_Ambiguity_Problem_on_Image_WACVW_2023_paper.pdf) | Image-recognition benchmark addressing label ambiguity; discusses limits of a single ground-truth label and proposes ambiguity handling. | **Partial B/C overlap:** label ambiguity and non-singleton ground truth are conceptually relevant. No evidence in the accessible record of hidden-label provenance attacks or a false-unique certification test. PDF returned 403 during this run, so claims are limited to indexed metadata/snippet. |
| [Annotation Error Detection survey (Computational Linguistics)](https://doi.org/10.1162/coli_a_00464) | Defines annotation-error flaggers/scorers; notes ambiguity/error discovery without assigning a gold label. | **Partial B overlap:** detects problematic labels and distinguishes flagging from scoring. It is a survey/framework, not a benchmark for hidden labels or uniqueness certificates; no producer-frame test. |
| [Pervasive Label Errors in Test Sets](https://arxiv.org/abs/2103.14749) | Measures label errors in 10 common datasets and impact on benchmark results. | **Partial B overlap:** demonstrates false benchmark conclusions from label errors. It does not hide labels from an evaluator or test rejection of a false unique certificate; no A/C mechanism. |

## Falsification result

No located primary source exposes an equivalent benchmark/evaluator that jointly or explicitly measures **hidden producer-frame misdeclaration**, **hidden-label false-unique certification**, or an FUP/AReject-style **certificate-level ambiguity rejection**. Existing work covers adjacent outcomes: generic multimodal uncertainty, embodied abstention, annotation-error detection, or label-ambiguity-aware datasets. These sources therefore weaken a broad claim such as “no one studies uncertainty/ambiguity,” but do **not** falsify the narrower mechanism-level distinction above.

## Uncertainty and limits

- Search was intentionally short and query-bounded; absence means “not found under these queries,” not exhaustive proof of novelty.
- “Hidden producer-frame” and “false-unique certification” are operational terms from the target proposal; papers may use different vocabulary (camera convention, reference frame, provenance, selective prediction, set-valued prediction).
- RoboAbstention is the strongest nearby benchmark for ambiguity rejection, so any final claim must state the non-overlap at the **certificate/provenance mechanism** level and cite it as prior adjacent work.

**Status:** benchmark-only falsification screen; no method validation or novelty authorization changed.
