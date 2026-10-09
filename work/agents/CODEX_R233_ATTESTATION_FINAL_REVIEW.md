# R233 Attestation-final review of R232

## Concrete remaining gap

R232 requires attestation freshness, replay checks, and current authority-key status, but does not bind key revocation/rotation status to an authenticated, fresh source. A verifier could accept a fresh attestation signed by a key that was revoked after a stale key-status snapshot.

## Fail-closed repair

Add key-status source and cache invalidation gates:

```yaml
key_status_policy:
  status_source_ref: "MISSING_EVIDENCE"
  status_source_signature: "MISSING_EVIDENCE"
  status_fetched_at: "MISSING_EVIDENCE"
  max_status_age: "MISSING_EVIDENCE"
  cache_invalidation_check: "pending"
  revocation_rotation_consistency: "pending"
  current_key_status: "pending"
trust_policy:
  stale_or_unauthenticated_key_status: "reject_and_remain_B_STATIC_ONLY"
  cache_not_invalidated_after_rotation: "reject_and_remain_B_STATIC_ONLY"
```

Acceptance requires fresh, authenticated key status and verified cache invalidation after rotation or revocation.

## Status and stop condition

Remain `B_STATIC_ONLY`; `allowed_next_branch_state=explicit_null`; `allowed_next_branch_value=null`; `transition_policy=prohibited`. Stop on missing status source/signature/freshness, pending invalidation or revocation checks, stale key snapshot, replayed attestation, or any execution/transition attempt.
