# R222 Trust-root final review of R221

## Concrete remaining gap

R221 adds trusted key, validity, revocation, and verification-time fields, but it does not specify the authoritative source and freshness requirements for those statuses. A stale or attacker-controlled revocation response could be marked `pass`, allowing a revoked key or expired certificate to appear valid.

## Fail-closed repair

Add source authenticity and freshness gates:

```yaml
trust_status_source:
  trust_anchor_ref: "MISSING_EVIDENCE"
  revocation_source_ref: "MISSING_EVIDENCE"
  revocation_source_signature: "MISSING_EVIDENCE"
  status_fetched_at: "MISSING_EVIDENCE"
  max_status_age: "MISSING_EVIDENCE"
  freshness_check: "pending"
  source_authenticity_check: "pending"
trust_policy:
  unauthenticated_or_stale_status: "reject_and_remain_B_STATIC_ONLY"
  pending_source_or_freshness_check: "reject_and_remain_B_STATIC_ONLY"
```

Acceptance requires an independently authenticated trust/revocation source and a freshness check within the declared maximum age.

## Status and stop condition

Remain `B_STATIC_ONLY`; `allowed_next_branch_state=explicit_null`; `allowed_next_branch_value=null`; `transition_policy=prohibited`. Stop on missing/unauthenticated/stale trust status, pending checks, key mismatch/revocation, field-set mismatch, or any execution/transition attempt.
