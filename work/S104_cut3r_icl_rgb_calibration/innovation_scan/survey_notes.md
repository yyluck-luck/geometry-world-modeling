# Working notes: budgeted subset-selection mechanisms (cross-domain survey)

## CRITICAL PRECEDENT (verified)
- **GIM-World**, "Geometry-Aware Implicit Memory for Video World Models", arXiv:2606.02436 (submitted 1 Jun 2026), Wei et al., Kling Team Kuaishou + Nanjing Univ.
  - URL: https://arxiv.org/abs/2606.02436 (html: https://arxiv.org/html/2606.02436v1)
  - Sec 3.4 "Information-Guided Pruning": keeps subset S with |S| <= K maximising I(S; H\S),
    *explicitly* citing "the mutual-information sensor-placement criterion of Krause et al. [30]",
    optimizing with a greedy algorithm. GP over per-frame observations with a **pose-time kernel**
    k(ci,cj) = exp(-||pi-pj||^2/2sig_p^2 - angle(fi,fj)^2/2sig_r^2 - (ti-tj)^2/2sig_t^2).
  - => Fixed-cardinality (budget) informative-subset selection over a geometric (pose-indexed)
    camera history, greedy, in a video world model memory. This is the near-neighbour.
  - Difference from GRC: GIM-world objective is *coverage/informativeness about dropped frames*
    (MI), NOT *risk of geometric unreliability in the target region*, and NOT *future prediction
    error reduction*. So GRC's novelty must live in (i) risk/uncertainty-weighting and
    (ii) future-error objective, NOT in "budgeted subset selection of geometry memory".
  - Note: it prunes history *before* encoding into an implicit memory; the project uses explicit 3D/surfel cache.
- **DensityKV** arXiv:2608.27922 (28 Aug 2026) - historical KV bank management, Soft-Riesz density
  redundancy, bounded capacity, autoregressive video diffusion. Training-free.
- **OmniMem** arXiv:2605.30519 (28 May 2026) - explicit full-range sparse KV retrieval, Adaptive
  Window Exclusion, Query-Shared KV Selection, Per-Head Scattered KV Access. Budget = sparse KV budget.
- **Context-as-Memory** SIGGRAPH Asia 2025, DOI 10.1145/3757377.3763833 - memory *retrieval*,
  compared against random selection baseline.
- **Video World Models with Long-term Spatial Memory** (SPMem) arXiv:2506.05284 (5 Jun 2025) -
  geometry-grounded long-term spatial memory + retrieval.
- **WorldPlay** arXiv:2512.14614 - long-term geometric consistency interactive world modeling.
- **Mem-World** arXiv:2606.18960 - memory-augmented action-conditioned world models.
- **GradMem** arXiv:2603.13875 (ICML 2026) - test-time gradient-descent memory writing, frozen
  weights, self-supervised context reconstruction loss, fixed memory size.
- H2O arXiv:2306.14048 - KV eviction as *dynamic submodular* problem, theoretical guarantee.
- SnapKV arXiv:2404.14469 - observation-window attention, clustered important KV positions.
- Sener & Savarese coreset arXiv:1708.00489 (ICLR 2018) - k-center greedy, theoretical characterisation.
- Zhou & Tokekar arXiv:1807.09358 - CVaR risk-averse submodular max, Sequential Greedy, matroid constraint.
- FisherRF / RaEM arXiv:2403.11396 - risk-aware masking on top of expected-information-gain NBV.
- CDVM arXiv:2605.11312 (IJCAI 2026) - constrained data-value maximisation pruning, influence/attribution.
