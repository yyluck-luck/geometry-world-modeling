# R104 CGLR novelty-boundary audit

Date: 2026-09-24 (Asia/Shanghai)  
Scope: read-only prior-art and contract audit. No GPU/Slurm, no runner or
fixture execution, no protected C8/evaluation reads, and no flag/contract edits.

## Decision

**Reject CGLR as a method-novelty claim at Gate 0.** Retain it only as a
descriptive reveal-event benchmark and a falsification harness. The R103
correction is necessary for an interpretable comparison, but it does not add an
information pathway. Byte-identical `base_input_sha256`, typed transition
rules, hash-domain checks, and owner/H2 gates are evaluation and provenance
hygiene; they constrain an experiment without changing what the model can
write or consume. `new_method_validated=false` and
`novelty_authorization=NONE` remain unchanged.

## Inspected evidence

R103's revision requires every arm to share an identical event/base input and
to differ only by a typed transition rule, with measured/wrong-component
events, complete event-vector comparison, and explicit rejection terminals
(`work/agents/CODEX_R103_CGLR_DISCRIMINATOR_HOSTILE_AUDIT_20260924.md`). R62
states the same invariant: all arms for one event receive one shared base input
and only their closed rule mapping may differ
(`work/agents/CODEX_R62_R60_TWO_PHASE_OWNER_GATE_CORRECTION_20260924.md:37-54,97-119`).
Those checks prevent access imbalance and leakage; they are not a new state
transition, representation, loss, or renderer.

S131 defines the candidate mechanism as a delayed RGB-D reveal, same-noise
pre/post pair, and change only on newly revealed support
(`work/S131_CGLR_contract/DESIGN_AND_PREREGISTRATION.md:9-22`). Its episode,
conservation, and matched-control rules already make this a testable contract,
not a validated method
(`work/S131_CGLR_contract/DESIGN_AND_PREREGISTRATION.md:24-37,39-88`).

## Prior-art boundary

The R38 search records that residual transfer through 3D correspondence,
visibility, and angular weighting is already present in *Boosting View
Synthesis with Residual Transfer*; residual transport is therefore plumbing,
not the contribution (`work/agents/CODEX_R38_HOSTILE_INNOVATION_REDTEAM_20260923.md:16-28,54-59`).
The same audit identifies fixed-seed correspondence-guided local editing
(Edicho), structured counterfactual masking (Counterfactual World Modeling),
persistent 3D state (PERSIST), selective exposed-surface updates (INGRID), and
generic sequential belief/completion systems as direct threats
(`work/agents/CODEX_R40_HOSTILE_UPDATE_20260923.md:26-45`). R38 explicitly
states that same-noise, support masks, and outside-mask conservation are only
plausibly distinctive in conjunction and that this subset intersection is an
unverified search result, not a novelty proof
(`work/agents/CODEX_R38_HOSTILE_INNOVATION_REDTEAM_20260923.md:46-59,97-99`).

### Strongest competing mechanism

The strongest operational competitor is the **Edicho/CWM local-counterfactual
editing family**: correspondence-guided fixed-seed local diffusion editing
already supplies the same-noise, support-gated intervention, while structured
counterfactual masking supplies pre/post causal comparison. PERSIST/INGRID
further cover persistent latent 3D state and selective updates. CGLR's delayed
RGB-D event and third-camera score are useful benchmark conditions, but the
R103/R62 machinery does not turn them into a new model operator.

## One falsifier

Run only the owner-reviewed synthetic contract if the missing packet ever
arrives. If CGLR's complete event signature and held-out future-camera output
are reproducible by the access-matched `mask_only_local` or
`residual_transport_untyped` rule under the same shared base input, return
`REJECT_NON_IDENTIFIABLE`; this directly falsifies a CGLR-specific information
pathway under R62's rule-only arm distinction. An exact primary-paper match to
the delayed RGB-D, persistent cross-camera, residual-gated conservation
conjunction is an independent literature kill condition under S131
(`work/S131_CGLR_contract/DESIGN_AND_PREREGISTRATION.md:90-96`).

## Next prerequisite

Do not implement or write novelty language. To reopen the mechanism line, the
owner must first supply an independently reviewed, source-pinned synthetic-only
packet (R62 ten-arm event table, computed camera-keyed visibility and hashes,
independent H2 source/boundary artifact, R89 owner identity, and supported CPU
runner) **and** complete an independent primary-paper comparison against the
Edicho/CWM/PERSIST/INGRID threat set. Until both exist, report CGLR only as a
benchmark/falsification protocol and keep `NO_COMMAND_AVAILABLE`.
