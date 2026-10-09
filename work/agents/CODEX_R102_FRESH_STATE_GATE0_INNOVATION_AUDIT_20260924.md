# R102 fresh-state Gate-0 and innovation audit

Date: 2026-09-24 (Asia/Shanghai)  
Scope: read-only design audit. No GPU/Slurm submission, no implementation, no
C8/evaluation-data read, no receipt or frozen-contract change.

## Decision

**Outcome (a): retain Reveal-Intervention/CGLR only as a falsifiable CPU-only
discriminator; do not claim a new method or validation.** RCA/BRD remain
closed/unsupported. DCR remains a convention-controlled benchmark setting,
not a mechanism. The discriminator below is the only surviving innovation
candidate worth an owner-reviewed synthetic conformance step; it is a test
contract, not a result.

## Fresh-state reconciliation

The heartbeat's older “partial/unverified” wording is stale for VMem file
integrity. The fresh remote re-verification records five required artifacts,
exact SHA matches, `result: PASS`, and explicitly supersedes the old starting
text (`work/S101_env_bootstrap/VMEM_FRESH_REVERIFY_20260924.json:1-37`). The
current handoff and plan also state `COMPLETE_SHA_VERIFIED` and historical
no-data smoke completion (`docs/RESEARCH_HANDOFF_CURRENT.md:17-21`;
`docs/RESEARCH_PLANS_EN.md:3-18`).
This verifies content identity and a no-data smoke only. It does **not** imply
Gate-0 success, H2 pose correctness, CGLR validation, or novelty.

The execution state is unchanged: R100 found all six owner/H2/fixture role
artifacts absent at both local and remote roots, no dedicated synthetic CPU
runner, and no supported command (`work/agents/CODEX_R100_POST_R99_READINESS_RECHECK_20260924.md:8-30`).
The one required owner action is a complete, independently reviewed,
synthetic-only packet (source-pinned runner/code manifest, canonical fixture,
boundary/H2 artifacts plus R70 packet, and R89 `OWNER_ACCEPTED` identity)
(`work/agents/CODEX_R100_POST_R99_READINESS_RECHECK_20260924.md:32-43`). Therefore the current status remains
`NO_COMMAND_AVAILABLE`, `new_method_validated=false`, and
`novelty_authorization=NONE`.

## Failure-driven red-team

1. **Convention confound (highest priority).** The C8 audit establishes a
   deterministic H1 evaluator join error: maps use `T_cv F`, while the
   evaluator supplies raw-frame points; the missing `F_3=diag(1,-1,-1)` gives
   `p_g=F_3 p_cv` (`work/agents/CODEX_R46_POSE_CONVENTION_DCR_AUDIT_20260924.md:37-48`).
   The audit explicitly says H2 remains open at the CUT3R pointmap boundary and
   that low `J` is `UNINTERPRETABLE_POSE_CONVENTION`, not model evidence
   (`work/agents/CODEX_R46_POSE_CONVENTION_DCR_AUDIT_20260924.md:7-10,50-54`). Any apparent reveal gain before H1/H2 identity is
   fixed is rejected as an evaluator/source-convention artifact.
2. **Generic information addition.** An append-only or generic completion
   branch can improve queries simply by receiving another RGB-D observation.
   S131 therefore requires append-only, generic-completion, global-update,
   no-reveal, and shuffled-mask controls, with at least two future cameras
   (`work/S131_CGLR_contract/episode_schema.json:23-35`; `work/S131_CGLR_contract/DESIGN_AND_PREREGISTRATION.md:74-88`).
3. **Wrong pathway or leakage.** A gain confined to the reveal camera,
   outside-support drift, target/future-RGB selection, or a shuffled mask gain
   is compatible with memorization, global latent drift, or support/scale
   error. It cannot support a reveal-specific causal pathway.

## CPU-only discriminator (synthetic first)

### Estimand

For each held-out future camera `q` and each equal-area pair of pixels/supports
`(S_reveal, S_untouched)`, compute the paired change from pre-reveal to
post-reveal for RGB and geometry/depth:

```text
L_m = [Err_m(pre,S_reveal,q) - Err_m(post,S_reveal,q)]
      - [Err_m(pre,S_untouched,q) - Err_m(post,S_untouched,q)]
```

Use the same random seed and identical pre-reveal state for every arm. Fit one
positive depth scale only on a calibration subset, freeze it, then score held
out queries. The candidate CGLR arm must be compared with S131's pre-reveal,
no-reveal counterfactual, append-only, generic-completion, global-update,
RRST_CGLR, and shuffled-mask arms, with a reveal-camera-held-out from at least
two future queries. Report RGB and depth/geometry separately, support
precision, and outside-support update mass (S131 cutoffs include
`min_support_precision=0.8` and `max_outside_update_mass=0.05`).

### Required CPU fixture gates

Before any real-data or GPU step, a metric plane/cube fixture with explicit
OpenCV cameras, `K`, depth units, and both `T_cv` and `T_cv F` must satisfy the
synthetic identity and positive-depth/rounding checks. Then a source-boundary
replay must decide whether CUT3R receives `T_cv` or `T_cv F`; R46 requires this
   H2 decision independently of C8 scores (`work/agents/CODEX_R46_POSE_CONVENTION_DCR_AUDIT_20260924.md:68-77`). If H2 is not
uniquely identified, the discriminator terminates as `H2_UNIDENTIFIABLE`.

### Falsifiable prediction

Only if the identity/H2 gates pass, CGLR supports its narrow pathway claim when
both future cameras show `L_RGB > 0` and `L_geom > 0`, the reveal support
precision is at least 0.8, outside-support update mass is at most 0.05, and
the paired effect exceeds each access-matched generic/append-only control.
The same result must fail for the no-reveal and shuffled-mask controls and must
not be confined to the reveal camera. This is an information-pathway
discriminator; it does not establish conference-level novelty.

## Explicit competing explanations and kill rule

The competing explanations are (E1) H1/H2 pose or scale/intrinsic artifact,
(E2) generic completion/append-only context gain, (E3) global latent update,
(E4) reveal-camera or target leakage, and (E5) arbitrary mask/support choice.

**Kill CGLR immediately** if the synthetic identity fixture fails; H2 remains
ambiguous; no calibration scale transfers to held-out windows; CGLR matches a
generic/append-only control; the gain appears only on the reveal camera; global
update matches the local arm; untouched support drifts beyond the cutoff; a
shuffled mask also gains; target/future RGB influences any choice; or the
effect disappears after the H1 frame repair. In that case retain only a
descriptive reveal benchmark and reject the mechanism/novelty line. These are
the R46 no-go conditions (`work/agents/CODEX_R46_POSE_CONVENTION_DCR_AUDIT_20260924.md:91-103`)
and S131 kill conditions, not post-hoc thresholds.

## Final state

The strongest surviving candidate is therefore **conditional CGLR reveal-event
causal locality**, pending the absent owner-reviewed synthetic packet. No
experiment is authorized or available in this cycle. The project remains
`new_method_validated=false` and `novelty_authorization=NONE`.
