# R227 Quorum-final review of R226

## Concrete remaining gap

R226 requires quorum/authority and validated failover, but does not bind quorum membership to an authenticated, versioned configuration. A stale or attacker-supplied membership list could satisfy a numeric quorum while excluding the true authority or admitting an untrusted replica.

## Fail-closed repair

Add membership authenticity and configuration freshness gates:

```yaml
quorum_membership:
  membership_config_ref: "MISSING_EVIDENCE"
  membership_config_digest: "MISSING_EVIDENCE"
  membership_signature: "MISSING_EVIDENCE"
  configuration_version: "MISSING_EVIDENCE"
  freshness_check: "pending"
  member_identity_verification: "pending"
  quorum_check: "pending"
quorum_policy:
  unauthenticated_or_stale_membership: "reject_and_remain_B_STATIC_ONLY"
  unknown_member_or_config_rollback: "reject_and_remain_B_STATIC_ONLY"
```

Acceptance requires authenticated membership, current configuration version, verified member identities, and quorum under that exact configuration.

## Status and stop condition

Remain `B_STATIC_ONLY`; `allowed_next_branch_state=explicit_null`; `allowed_next_branch_value=null`; `transition_policy=prohibited`. Stop on missing/invalid membership signature or version, stale/rolled-back config, unknown member, pending quorum/failover checks, or any execution/transition attempt.
