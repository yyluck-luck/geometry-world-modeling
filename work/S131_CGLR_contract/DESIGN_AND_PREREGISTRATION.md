# S131 CGLR zero-GPU paired-episode contract

Date: 2026-09-23

This directory defines a data and evaluation contract only. It does not modify pinned VMem source,
run a model, submit Slurm, train an adapter, or establish novelty. The project flags remain
`new_method_validated=false` and `novelty_authorization=NONE`.

## Working method label

**CGLR (Conservative Geometric Local Revision)** is tested conceptually as:

- **RRST:** an engineering substrate that transports a delayed RGB-D reveal residual through a
  surface correspondence field. Residual transport itself is not a novelty claim because it has
  prior art in [Boosting View Synthesis with Residual Transfer](https://openaccess.thecvf.com/content/CVPR2022/papers/Rong_Boosting_View_Synthesis_With_Residual_Transfer_CVPR2022_paper.pdf).
- **CRR:** the sole candidate mechanism: use the real delayed reveal as a causal intervention in a
  same-noise pre/post generation pair, then test that only the newly revealed support changes.

The claim under test is the reveal-specific causal pathway, not a new map, uncertainty head, depth
adapter, retrieval rule, residual warp, or generic belief update. Fixed-seed local editing and
counterfactual masking are prior-art threats; reveal-camera/future-camera separation and an immutable
evidence ledger are mandatory controls.

## Episode protocol

Each episode has four disjoint camera roles from an independent held-out scene:

1. `context`: exactly four delivered frames. The target patch is hidden from all four.
2. `pre_reveal_query`: camera used to render the hidden-surface prediction. Its RGB-D is sealed.
3. `reveal`: a later camera whose RGB-D exposes the patch and has nonzero residual against the
   pre-reveal prediction.
4. `future_queries`: at least two held-out cameras distinct from `reveal`; their RGB-D is used only
   for scoring. The correction must persist across both cameras, so a single reveal-camera gain is
   insufficient.

The episode manifest contains camera poses, intrinsics, frame hashes, a geometry-only reveal mask,
and sealed references. Target RGB/D must never enter context construction or the pre-reveal output.

## Typed state and provenance

```text
E_pre  = context RGB-D and camera poses only
B_pre  = predicted hidden surface belief, with provenance and uncertainty
R      = reveal RGB-D, registered to B_pre coordinates
E_post = E_pre union R; no prediction may be written into E_post
B_post = B_pre updated only where reveal support and residual gate overlap
```

The evaluator must verify byte identity of `E_pre` before and after the update. Outside the registered
reveal support, the required conservation rule is `B_post == B_pre` up to a declared numerical
tolerance. A global latent update fails this contract.

## Estimands and pre-registered thresholds

For each episode, let `M_r` be the independent reveal support and `M_u` an equal-area untouched
support matched by depth and distance from the camera. The primary difference-in-differences is:

```text
Delta = [Err_pre(M_r) - Err_post(M_r)]
        - [Err_pre(M_u) - Err_post(M_u)]
```

Report RGB and depth versions separately for each future query, plus reveal-camera error before/after
transport. A feasibility signal requires positive direction for both RGB and depth on both future
queries, correction-support precision at least 0.80,
outside-support update mass at most 0.05, and no material untouched-region drift. These are pilot
cutoffs, not statistical claims; the eight-episode pilot is descriptive only.

Residual gating is calibrated before reading future-camera outcomes. A pixel is eligible only when
`residual > max(0.05 m, 0.05*z)` in depth or exceeds a frozen RGB residual threshold estimated from
context sensor noise. If the reveal does not expose a valid patch or the residual is zero, mark the
episode `UNTESTABLE`, never favorable.

## Matched controls

Every episode must have the same target camera, seed, and legal context under:

1. `pre_reveal`: no reveal information;
2. `append_only`: reveal frame added/retrieved, no belief rewrite;
3. `generic_completion`: capacity-matched geometry/completion adapter;
4. `global_update`: unconstrained online update;
5. `CRR_CGLR`: reveal-specific causal residual branch with conservation rule (RRST may be used only
   as an implementation substrate);
6. `no_reveal_counterfactual`: same inputs and noise as `pre_reveal`, repeated;
7. `shuffled_mask`: residual and mask deliberately mismatched.

CRR uses the same diffusion noise for `pre_reveal`, `append_only`, and `CRR_CGLR` where the
implementation permits. The no-reveal branch must not change the belief or measured evidence.

## Kill conditions

Close CGLR if append-only or generic completion matches future-camera improvement; if global update
matches local update; if gains appear only at the reveal camera; if the correction is not local; if
untouched regions drift; if the gain disappears after C8 slot-0 RS canonicalization; if target RGB/D
leaks into context or masks; or if a primary paper is found with the same residual-gated local
revision and conservation test.

## Authorization boundary

This contract may be validated with CPU-only manifest and geometry checks. It does not authorize the
C8 GPU diagnostics or a CGLR adapter pilot. C8 owner review and a support-scarcity result excluding
delivery/indexing explanations are prerequisites for any model execution.
