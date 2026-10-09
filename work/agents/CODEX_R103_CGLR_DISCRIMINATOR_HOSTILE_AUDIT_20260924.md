# R103 hostile audit of the R102 CGLR discriminator

Date: 2026-09-24 (Asia/Shanghai)  
Scope: read-only protocol audit. No runner/fixture execution, no GPU/Slurm,
no protected C8/evaluation reads, and no frozen-contract or flag changes.

## Verdict

**REVISE before owner acceptance.** R102 has the right estimand and kill
conditions, but the phrase “access-matched generic/append-only control” is not
itself a machine-checkable condition. Equal-area supports and same noise do not
ensure that CGLR and controls received the same event residual, provenance,
correspondence, visibility, threshold, and update budget. A cleaner measured
event reaching CGLR would look like a causal reveal gain while actually being
an input-access advantage. This is one confounder: **unbound access
equivalence**.

## Evidence and comparison

R102 defines the difference-in-differences and equal-area support pair
(`work/agents/CODEX_R102_FRESH_STATE_GATE0_INNOVATION_AUDIT_20260924.md:60-78`),
but does not bind an event/input identity across its listed arms. S131 requires
the same episode, seed, legal context, geometry-only reveal mask, sealed target,
and explicit append-only/generic/global/no-reveal/shuffled controls
(`work/S131_CGLR_contract/DESIGN_AND_PREREGISTRATION.md:24-37,74-88`). Its
estimand also assumes `M_r` is an independent reveal support and `M_u` is
equal-area and depth/distance matched
(`work/S131_CGLR_contract/DESIGN_AND_PREREGISTRATION.md:53-67`).

The later owner-contract audits make the missing condition explicit: strong
controls must receive the same event residual, provenance, support,
correspondence, threshold, and budget, with measured and wrong-component event
variants (`work/agents/CODEX_R53_R52_READINESS_AUDIT_20260924.md:18-22`).
R60/R62 then require one shared per-event base input and arm-specific typed rule
parameters only (`work/agents/CODEX_R60_R58_EXECUTION_PREFLIGHT_CORRECTION_20260924.md:89-104`;
`work/agents/CODEX_R62_R60_TWO_PHASE_OWNER_GATE_CORRECTION_20260924.md:37-54,97-119`).
R46 independently requires H2 to pass before any score and forbids choosing
conventions from C8 metrics (`work/agents/CODEX_R46_POSE_CONVENTION_DCR_AUDIT_20260924.md:68-77`).

## Concrete tightening (preserves S131/R62 semantics)

Replace R102's prose “access-matched” requirement with this pre-score contract:

1. For each event, materialize camera-keyed computed visibility records and
   the event object before scoring. Query separation uses world cell IDs and
   camera-keyed sets; never intersects `(u,v)` coordinates from different image
   planes.
2. Recompute one canonical `base_input_sha256` containing the event residual,
   source provenance, support/correspondence, computed visibility, threshold,
   and update budget. Every arm in the event vector (CGLR, append-only,
   generic-global, no-reveal, shuffle-placebo, and the R62 strong controls)
   must have byte-identical base input. Only the closed `transition_rule_id`
   and typed rule parameters may differ. Supplied hashes are recomputed and
   compared before any metric is read.
3. Include both R53 event variants, `A_large_measured` and
   `A_large_wrong_component`, in the synthetic event table. Their event inputs
   are fixed before scoring and are not arm-rule parameters. Compare the
   complete event vector, with channel-specific denominators, on at least two
   held-out future cameras.

## Exact falsification / acceptance rule

After owner and H2 gates pass, accept the discriminator only if CGLR has
positive RGB and geometry/depth difference-in-differences on both future
cameras, meets the frozen support/outside-update cutoffs, and beats every
access-matched strong control. Return:

* `REJECT_FIXTURE` if any arm's recomputed base input differs, a visibility set
  is copied from expected truth, a measured/wrong-component event is absent, or
  any target/post-state value enters an input or rule hash;
* `REJECT_NON_IDENTIFIABLE` if CGLR and a strong control tie on the complete
  event signature or if the observed gain is explained by the wrong-component,
  append-only, generic, global, or shuffled arm;
* `UNTESTABLE_NO_DENOMINATOR` for a zero RGB/depth denominator; and
* `H2_UNIDENTIFIABLE` before hashing/scoring for missing, ambiguous, or failed
  H2 provenance.

Any one of these terminals kills the mechanism claim; the result may remain a
descriptive benchmark only. A successful synthetic `PASS_CONTRACT_REPLAY`
would still be conformance evidence, not novelty or real-data validation.

## Next owner prerequisite

Supply one independently reviewed synthetic-only packet containing the R62
ten-arm/event table, computed camera-keyed visibility envelope and hashes,
measured/wrong-component events, independent H2 source/boundary packet, R89
owner identity, and a supported CPU runner. Until then the project remains
`NO_COMMAND_AVAILABLE`, `new_method_validated=false`, and
`novelty_authorization=NONE`.
