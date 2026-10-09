# R223 Trust-source review of R222

## Concrete remaining gap

R222 requires an authenticated source and freshness check, but leaves the time reference and freshness bound unspecified (`max_status_age` is `MISSING_EVIDENCE`). Without a trusted clock/time basis and replay protection, an old but validly signed revocation response could pass freshness or be evaluated against an attacker-controlled timestamp.

## Fail-closed repair

Add explicit time and replay gates:

```yaml
freshness_policy:
  trusted_time_source_ref: "MISSING_EVIDENCE"
  max_status_age: "MISSING_EVIDENCE"
  status_timestamp: "MISSING_EVIDENCE"
  clock_skew_bound: "MISSING_EVIDENCE"
  nonce_or_sequence: "MISSING_EVIDENCE"
  replay_check: "pending"
  freshness_check: "pending"
trust_policy:
  missing_time_basis_or_replay_proof: "reject_and_remain_B_STATIC_ONLY"
  stale_or_replayed_status: "reject_and_remain_B_STATIC_ONLY"
```

Acceptance requires a trusted time basis, explicit age/skew bounds, and a non-replayed status response.

## Status and stop condition

Remain `B_STATIC_ONLY`; `allowed_next_branch_state=explicit_null`; `allowed_next_branch_value=null`; `transition_policy=prohibited`. Stop on missing time/replay fields, pending checks, stale/replayed status, key/source mismatch, field-set mismatch, or any execution/transition attempt.
