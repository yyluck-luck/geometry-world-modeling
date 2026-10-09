# R39 innovation synthesis: CGLR with RRST and CRR

Date: 2026-09-23

This is the current method decision after the R38 mechanism search and hostile review. It is not a
novelty authorization or a validation result. `new_method_validated=false` and
`novelty_authorization=NONE` remain unchanged.

## Decision

The broad phrase “delayed-observation posterior correction” is too broad. The working candidate is
now **CGLR: Conservative Geometric Local Revision**, with two separable pieces:

- **RRST (Reveal-Residual Surface Transport):** implementation operator that transports a registered
  RGB-D reveal residual through 3D surface correspondence into the same pre-reveal hidden hypothesis.
- **CRR (Causal Reveal Residual):** same-noise paired test that gates the post/pre generative change
  by the newly revealed support and enforces conservation outside that support.

CGLR is not “belief update,” “scene completion,” “persistent memory,” “re-entry consistency,” or
“delayed smoothing.” Those are occupied or too generic. The proposed unit is the conjunction:

`materialized hidden hypothesis + contradictory registered reveal + residual-gated local revision +
counterfactual third-camera generation + outside-support conservation`.

## Why the conjunction remains worth testing

[3D-Belief](https://arxiv.org/abs/2605.11367) occupies explicit 3D belief and online update;
[WRBench](https://arxiv.org/abs/2606.20545) occupies hide-and-return state persistence; and
[GEM-Occ](https://arxiv.org/abs/2607.05543) occupies visibility-aware causal occupancy memory.
The candidate therefore has to target a static/quasi-static hidden surface and prove that a measured
correction is transported to a *third camera* through the same hypothesis, rather than merely adding
the reveal frame or updating an occupancy map.

Closest project-specific threats are geometry-conditioned generation, generic completion, visibility
maps, and slot-0 conditioning. These are controls or substrates, not contributions.

## Minimal information-pathway contract

Maintain typed state:

```text
E = immutable measured RGB-D evidence and camera poses
B = hidden-surface hypotheses with provenance, uncertainty, and query coordinates
R = a reveal event registered to the same surface/ray coordinates
```

At reveal, compute the RGB-D residual against the *pre-reveal* rendering of `B`. Update only the
support that both intersects the independently computed reveal mask and exceeds the calibrated
uncertainty threshold. Copy `B` exactly outside that support. Render the corrected `B` at a third
held-out camera. Predictions must not enter `E`.

The minimum difference-in-differences estimand is:

```text
Delta = [Err_pre(reveal) - Err_post(reveal)]
        - [Err_pre(untouched) - Err_post(untouched)]
```

Require positive RGB and depth directions, locality, and monotone correction with residual magnitude.
PSNR alone is not sufficient.

## Controls and rejection rules

Use held-out hidden → reveal → third-camera episodes, at least eight independent episodes for the
first feasibility pass, with matched:

1. append-only reveal-frame retrieval;
2. capacity-matched generic completion/depth adapter;
3. global online update;
4. no-transport local update;
5. no-reveal counterfactual;
6. shuffled reveal mask/residual threshold;
7. slot-0 RS canonicalization from C8.

Reject CGLR if append-only or generic completion matches it, if global update explains the gain, if
the update leaks outside the reveal support, if untouched regions drift, if gains appear only at the
reveal camera, or if C8 attributes the apparent failure to delivery/indexing. If a paper is found
with the exact residual-gated local revision and conservation contract, retire the candidate.

## Immediate next step

Do not build a large architecture. First write a zero-GPU paired-episode data contract and a mask/
provenance evaluator. Run C8 only after owner review. Promote CGLR to a tiny adapter pilot only if
C8 finds real support scarcity after delivery and indexing are separated.

