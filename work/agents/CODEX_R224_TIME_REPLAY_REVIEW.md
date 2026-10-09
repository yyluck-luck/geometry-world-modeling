# R224 Time/replay review of R223

## Concrete remaining gap

R223 adds nonce/sequence and replay checks but does not bind the nonce/sequence to an authoritative issuer or define monotonicity/storage scope. A replayed response with a new locally fabricated nonce, or a sequence reset across verifier instances, could pass a superficial `replay_check`.

## Fail-closed repair

Add issuer-bound sequence and state requirements:

```yaml
replay_policy:
  issuer_bound_nonce_or_sequence: "MISSING_EVIDENCE"
  sequence_monotonicity_rule: "MISSING_EVIDENCE"
  verifier_state_scope: "MISSING_EVIDENCE"
  seen_value_store_ref: "MISSING_EVIDENCE"
  reset_protection: "MISSING_EVIDENCE"
  replay_check: "pending"
trust_policy:
  unbound_or_nonmonotonic_sequence: "reject_and_remain_B_STATIC_ONLY"
  missing_replay_state_or_reset_protection: "reject_and_remain_B_STATIC_ONLY"
```

Acceptance requires issuer-authenticated nonce/sequence, monotonicity, durable verifier state, and reset protection.

## Status and stop condition

Remain `B_STATIC_ONLY`; `allowed_next_branch_state=explicit_null`; `allowed_next_branch_value=null`; `transition_policy=prohibited`. Stop on missing issuer binding, sequence rule/state, reset protection, pending replay/freshness checks, stale/replayed status, or any execution/transition attempt.
