# R231 Rotation-time review of R230

## Concrete remaining gap

R230 requires a trusted time source and ordering consensus but does not bind the time source to an authenticated authority or define monotonicity across verifier instances. A rollback or divergent clock could make activation/revocation order appear valid to different verifiers.

## Fail-closed repair

Add authenticated time and cross-verifier consistency gates:

```yaml
time_authority:
  time_source_identity: "MISSING_EVIDENCE"
  time_source_signature: "MISSING_EVIDENCE"
  trust_anchor_ref: "MISSING_EVIDENCE"
  monotonic_counter_or_epoch: "MISSING_EVIDENCE"
  cross_verifier_time_consistency: "pending"
  rollback_detection: "pending"
time_policy:
  unauthenticated_or_nonmonotonic_time: "reject_and_remain_B_STATIC_ONLY"
  divergent_or_rolled_back_time: "reject_and_remain_B_STATIC_ONLY"
```

Acceptance requires authenticated time evidence, monotonic epoch/counter, cross-verifier consistency, and rollback detection before applying rotation ordering.

## Status and stop condition

Remain `B_STATIC_ONLY`; `allowed_next_branch_state=explicit_null`; `allowed_next_branch_value=null`; `transition_policy=prohibited`. Stop on missing time authority/anchor, signature, monotonic counter, consistency or rollback checks, pending ordering, key mismatch, or any execution/transition attempt.
