# R235 Cache-final review of R234

## Concrete remaining gap

R234 requires invalidation propagation and quorum acknowledgements but does not bind acknowledgements to authenticated replica identities and the current quorum membership/version. A stale or unauthorized replica set could fabricate quorum completion while a valid node retains stale key status.

## Fail-closed repair

Add ack identity and membership-version gates:

```yaml
invalidation_ack_policy:
  event_signature: "MISSING_EVIDENCE"
  ack_signer_identity_set: "MISSING_EVIDENCE"
  ack_membership_config_ref: "MISSING_EVIDENCE"
  ack_membership_version: "MISSING_EVIDENCE"
  signer_membership_consistency: "pending"
  quorum_threshold_check: "pending"
  ack_event_order_check: "pending"
trust_policy:
  unauthenticated_or_stale_ack_signer: "reject_and_remain_B_STATIC_ONLY"
  membership_version_mismatch: "reject_and_remain_B_STATIC_ONLY"
  insufficient_or_reordered_ack_set: "reject_and_remain_B_STATIC_ONLY"
```

Acceptance requires signed acknowledgements from current, authorized members, meeting threshold in event order.

## Status and stop condition

Remain `B_STATIC_ONLY`; `allowed_next_branch_state=explicit_null`; `allowed_next_branch_value=null`; `transition_policy=prohibited`. Stop on missing ack signatures/membership/version/order, pending quorum checks, stale cache, revoked key, replayed event, or any execution/transition attempt.
