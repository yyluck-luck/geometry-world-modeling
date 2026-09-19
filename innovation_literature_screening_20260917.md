# Innovation literature screening (2026-09-17, title/abstract level only)

## Status and boundary

`SCREENING_ONLY`; this is a title/abstract-level arXiv API scan across 6 query angles (44 raw
hits, deduplicated below), not the primary-source method/assumption/ablation reading that
`RESEARCH_PRINCIPLES.md` v2.12 requires before any competing-work judgment. No claim here changes
`new_method_validated=false` or `novelty_authorization=NONE`. Purpose: surface candidates newer
than the existing `docs/LITERATURE_SYNTHESIS_V2.md` / `work/agents/INNOVATION_SYNTHESIS_20260916.md`
neighbor list that must be deep-read before SOCF-A / FGB-SI can keep their current distinction
claims.

## Method

Six arXiv API queries (`export.arxiv.org/api/query`, sortBy=submittedDate), run 2026-09-17 from
the local machine (not SuperPOD): (1) causal intervention + generative memory, (2) future-aware
memory in world models, (3) geometry-aware video-diffusion consistency, (4) retrieval memory for
video generation, (5) 3D memory conditioning for video, (6) revisit/long-horizon memory in world
models. Raw outputs saved under `/tmp/gwm_innov_scan/q1..q6.txt` (not copied into the repo; ephemeral
scratch only). No dataset, checkpoint, or GT access; no model run.

## Candidates requiring a deep-read pass before the next Gate0/SOCF cycle

1. **R2M-Bench** (arXiv 2608.27328, 2026-08-27) — "Evaluating Revisit Memory via Relative
   Consistency in Interactive Video World Models." Abstract-level overlap risk: **high**. It
   directly targets the same measurement gap FGB-SI/S6-S7 rely on (raw first-visit vs. return-frame
   similarity is a weak proxy for real memory), proposing a relative-consistency metric instead.
   Must check: does it already provide a source-level or intervention-based causal test, or is it a
   purely observational/benchmark metric? If purely observational, FGB-SI's source-intervention
   framing may still be distinct; if not, FGB-SI needs a corrected differentiation paragraph.
2. **OctWorld** (arXiv 2609.03919, 2026-09-03) — "Long-Range World-Consistent Video Generation with
   Octree-Based 3D Mapping." Directly adjacent to VMem's octree memory partition (the exact
   mechanism this project's S3 explicitly avoided reproducing). Must check whether it performs any
   source-level retain/replace causal test or only standard octree retrieval/fusion.
3. **Ring Forcing** (arXiv 2608.26794, 2026-08-27) — "Towards Precise Long-Term Memory for
   Autoregressive Video Diffusion," explicitly separates object permanence vs. memory retrieval
   accuracy. Potential near-neighbor to the project's source-identity/localization split.
4. **LayerRecall** (arXiv 2608.28460, 2026-08-28) — "A State-Conditioned Memory Router for
   Long-Horizon Consistency," a router deciding what history to keep/evict. Near-neighbor to any
   source-selection framing; check whether it reports signed per-source causal effect or only
   aggregate quality.
5. **GLAM** (arXiv 2609.14561, 2026-09-13) and **TourPhysics** (arXiv 2609.04911, 2026-09-04) —
   both distinguish observation-driven vs. intervention-driven state change; lower priority but
   relevant vocabulary check for "intervention" framing collisions.
6. **World-Action Models for Robot Learning and Control: A Survey** (arXiv 2609.16074, 2026-09-13)
   — brand new (4 days old), useful only as a landscape/neighbor-completeness check, not a method
   competitor.

## Not new / already tracked

Wonder, ReWorld, Matrix-Game 3.5, Echo-Memory (2606.09803), Retrieve What's Missing (2606.02479)
resurfaced and match prior records in `RESEARCH_MEMORY.md` / `docs/LITERATURE_VERIFIED.md`; no
correction needed from this pass alone.

## Explicit non-claims

- This pass does not confirm or refute any overlap; it only ranks what to read next.
- No PDF/HTML method sections were opened in this pass; abstracts only.
- Not run on SuperPOD; no relation to Gate0, S103-VMemBase, or the exact-boundary probe track.

## Next step

Deep-read R2M-Bench and OctWorld method sections first (highest overlap risk with FGB-SI and the
VMem octree baseline respectively); update `SOCF_A_v2_INNOVATION_UPDATE_20260916.md` /
`docs/LITERATURE_SYNTHESIS_V2.md` only after primary-source reading, with explicit assumption,
method, and falsification-boundary comparison per Supervisor-Skills 2.3.
