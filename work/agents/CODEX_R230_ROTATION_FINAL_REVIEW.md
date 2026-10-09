# R230 Rotation-final review of R229

## Concrete remaining gap

R229 defines old/new key validity and overlap fields but does not bind them to a trusted time source or specify ordering when revocation and activation timestamps conflict. Different verifiers could therefore accept different keys during clock skew or an ambiguous overlap boundary.

## Fail-closed repair

Add a single authoritative time/order policy:

```yaml
rotation_time_policy:
  trusted_time_source_ref: "MISSING_EVIDENCE"
  clock_skew_bound: "MISSING_EVIDENCE"
  timestamp_order_rule: "MISSING_EVIDENCE"
  overlap_boundary_inclusive: "MISSING_EVIDENCE"
  activation_before_revocation_check: "pending"
  revocation_before_activation_check: "pending"
  ordering_consensus: "pending"
rotation_policy:
  ambiguous_or_skewed_timestamps: "reject_and_remain_B_STATIC_ONLY"
  conflicting_activation_revocation_order: "reject_and_remain_B_STATIC_ONLY"
```

Acceptance requires one trusted time/order rule, bounded skew, deterministic boundary semantics, and consensus on activation/revocation order.

## Status and stop condition

Remain `B_STATIC_ONLY`; `allowed_next_branch_state=explicit_null`; `allowed_next_branch_value=null`; `transition_policy=prohibited`. Stop on missing time/order policy, ambiguous boundaries, clock skew, pending checks, key rollback/mismatch, or any execution/transition attempt.
