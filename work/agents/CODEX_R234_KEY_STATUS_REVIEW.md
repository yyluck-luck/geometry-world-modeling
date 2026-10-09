# R234 Key-status review of R233

## Concrete remaining gap

R233 requires cache invalidation after key rotation/revocation but does not define propagation guarantees or acknowledgements across verifier replicas. One node could retain a stale key-status cache while another has invalidated it, allowing inconsistent acceptance.

## Fail-closed repair

Add invalidation propagation and quorum-ack gates:

```yaml
cache_invalidation_policy:
  invalidation_event_id: "MISSING_EVIDENCE"
  propagation_scope: "MISSING_EVIDENCE"
  replica_ack_set: "MISSING_EVIDENCE"
  minimum_ack_quorum: "MISSING_EVIDENCE"
  ack_freshness: "pending"
  replica_cache_consistency: "pending"
  stale_cache_rejection: "pending"
trust_policy:
  missing_or_insufficient_invalidation_ack: "reject_and_remain_B_STATIC_ONLY"
  replica_cache_divergence: "reject_and_remain_B_STATIC_ONLY"
```

Acceptance requires authenticated invalidation propagation, quorum acknowledgements, and consistent cache state before accepting attestations.

## Status and stop condition

Remain `B_STATIC_ONLY`; `allowed_next_branch_state=explicit_null`; `allowed_next_branch_value=null`; `transition_policy=prohibited`. Stop on missing invalidation event/ack/quorum, pending consistency checks, stale or divergent cache, revoked key, replayed attestation, or any execution/transition attempt.
