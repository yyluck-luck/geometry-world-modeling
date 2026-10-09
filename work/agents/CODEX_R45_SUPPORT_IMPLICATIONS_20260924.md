# R45 support implications: C8 audit and the RCA/BRD/DCR decision

Date: 2026-09-24 (Asia/Shanghai)  
Scope: adjudication of completed C8 support audit job 609623 using local receipts; no GPU,
new model run, Slurm submission, or validation-flag change.  
Status remains `new_method_validated=false`; `novelty_authorization=NONE`.

## Decision

**Close RCA and BRD for the current VMem support-driven pipeline as unsupported and
uninterpretable.** This is a pipeline decision, not a universal proof that either idea can never
work. The C8 panel does not contain the precondition needed to justify a hidden-surface correction
method: bank support and delivered-context support are already high, while the low surfel/depth-hit
quantity `J` cannot be interpreted physically because the pose-convention check passes in only 3 of
14 windows.

Use the following status labels:

* RCA: `CLOSED_UNSUPPORTED_SUPPORT` on this panel; no S132 router scoring or adapter pilot.
* BRD: `CLOSED_UNSUPPORTED_SUPPORT` plus `UNINTERPRETABLE_POSE_CONVENTION`; no negative-reveal
  method pilot.
* DCR: **conditionally defensible as a benchmark/evaluation setting only**, with a fresh
  convention-controlled contract. It is not a method authorization and is not validated by C8.

## Receipt-backed facts

The remote receipt is `c8-support-retrieval-v2`, job 609623 on `dgx-45`, status
`MAPS_COMPLETE_NO_DIFFUSION`, with 14 `OK` records and 56 target maps. The CPU mask receipt reports:

| Quantity | Observed C8 result | Interpretation under the frozen contract |
|---|---:|---|
| Bank support `B` | 0.755--0.984 across all 14 windows | no low-bank-support window; the scarcity premise is not supported |
| Delivered context `C` | every arm/window is at least 0.2; clean arm 0.491--0.972 | no high-`B`/low-`C` delivery explanation |
| VMem hit `J` | 0.000--0.092; all 14 below 0.2 | a low value is observed but is not yet a physical indexing diagnosis |
| Pose-convention gate | 3/14 windows pass both requirements | `J` is `UNINTERPRETABLE_POSE_CONVENTION` |
| Own-render depth correlation | overall median about 0.190; some ratios in the hundreds | camera/depth convention or scale remains unresolved |

The receipt proves map construction and isolation ordering. It does not prove hidden-surface
scarcity, a valid world-coordinate registration, a generated-view improvement, or a new method.
The exact local analysis is `work/S130_C8_diagnostics/SUPPORT_AUDIT_ANALYSIS_609623.md`.

## Why RCA is closed on this pipeline

RCA was motivated as a gate that prevents a delayed contradiction from being written as scene
evidence when the cause could instead be camera/gauge or transient corruption. That mechanism still
requires a meaningful hidden-surface generative belief and a trustworthy physical registration of
the reveal. C8 finds no context-support scarcity: the target surfaces are visible in the bank and in
the delivered contexts. The only apparent downstream failure, low `J`, is confounded by pose and
scale interpretation. Therefore the current data cannot distinguish “RCA would prevent a bad scene
write” from “the renderer/indexer is using an invalid convention” or “the hidden branch was not
needed.” Running the RCA CPU contract now would measure a synthetic routing exercise disconnected
from the observed VMem failure.

This is stronger than a weak result and weaker than a prior-art rejection: the support gate blocks
the causal estimand before implementation. The correct action is a read-only convention/scale audit,
not a GPU pilot or threshold tuning.

## Why BRD is closed on this pipeline

BRD requires predicted-only ghost surfaces and an independently identifiable negative reveal. High
`B` and high `C` do not establish that such a ghost surface exists; they show that the relevant
surfaces are already present in available context. Low `J` cannot establish missing occupancy or
free-space evidence while the pose check fails. Without a valid registered negative reveal, a BRD
deletion could simply erase a convention-induced projection or a valid hypothesis. Thus BRD is
`UNSUPPORTED_SUPPORT` and `UNINTERPRETABLE_POSE_CONVENTION`, not a negative method result.

## DCR fallback: what remains defensible

DCR (Delayed Contradictory Reveal) remains defensible **only as a new evaluation setting**, separated
from the C8 explanation. The setting should use static geometry, a sealed pre-reveal prediction, a
delayed positive or negative RGB-D reveal, and at least two future camera queries. It must freeze:

1. known camera-to-world convention, metric depth units, and scale, verified by an independent
   algebraic/rendering check;
2. independent geometry-only support masks and immutable evidence provenance;
3. target RGB/depth sealing until every arm, prediction, and hash is committed;
4. append-only, generic-completion, and occupancy/robust-pose controls;
5. positive and negative reveal cases with separate estimands and no support/indexing ambiguity;
6. cross-camera scoring that is not based on the unresolved C8 `J` quantity.

The C8 panel itself cannot instantiate this benchmark because its pose-convention check fails in
11/14 windows. A synthetic or independently calibrated held-out set could make DCR testable, but
that would be a new contract and should remain CPU/design-only until owner review. DCR must not claim
that C8 established support scarcity, RCA/BRD validity, or a VMem gain.

## Updated shortlist and stop rule

1. **DCR evaluation setting (conditional)** — retain as the only defensible research object after
   rebuilding the pose-controlled contract.
2. **RCA** — close for the current pipeline as `CLOSED_UNSUPPORTED_SUPPORT`; reopen only if a later
   read-only convention audit makes `J` interpretable and an independent delayed-reveal panel is
   constructed.
3. **BRD** — close for the current pipeline as `CLOSED_UNSUPPORTED_SUPPORT` /
   `UNINTERPRETABLE_POSE_CONVENTION`; same reopen condition, plus a valid negative reveal.
4. **CGLR/CRR** — remain a causal evaluation operator/control, not a method path.

If the convention/scale audit does not produce an interpretable registration, stop the hidden-surface
method search and report the infrastructure/evaluation limitation. Do not use the low `J` number as
evidence for a geometry-completion adapter, RCA, BRD, or DCR success. No validation flag is changed
by this memo.

## Receipt identities

- `work/S130_C8_diagnostics/remote_support_609623/C8_SUPPORT_MASKS.json`  
  SHA-256 `a480aa8814578858501726b2b64c41be69f8a6dde36dbd6b2fda8a74890d94be`
- `work/S130_C8_diagnostics/remote_support_609623/C8_SUPPORT_RETRIEVAL_RECEIPT.json`  
  SHA-256 `c5718f8bd7901d7892cdbae2920598de89af287e5e9c4520796f108892689e35`
- `work/S130_C8_diagnostics/SUPPORT_AUDIT_ANALYSIS_609623.md`  
  SHA-256 `66d7cbdab4dd26bd296f3b9c55d1e4bd2cd9fd0f4b883e078da40a6b42ec6a11`

