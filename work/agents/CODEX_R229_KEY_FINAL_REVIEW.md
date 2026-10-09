# R229 Key-final review of R228

## Concrete remaining gap

R228 requires a trusted anchor, signer authorization, key version, rotation policy, and rollback protection, but does not define how a rotation is authorized or how old/new keys overlap. During rotation, an unauthorized key or prematurely retired key could validate membership, or rollback could be hidden by version ambiguity.

## Fail-closed repair

Add explicit rotation-consensus gates:

```yaml
key_rotation_policy:
  rotation_authorization_ref: "MISSING_EVIDENCE"
  approving_quorum_ref: "MISSING_EVIDENCE"
  old_key_valid_until: "MISSING_EVIDENCE"
  new_key_valid_from: "MISSING_EVIDENCE"
  overlap_consistency_check: "pending"
  old_key_revocation_status: "pending"
  version_monotonicity_check: "pending"
rotation_policy:
  unauthorized_or_nonmonotonic_rotation: "reject_and_remain_B_STATIC_ONLY"
  invalid_overlap_or_pending_revocation: "reject_and_remain_B_STATIC_ONLY"
```

Acceptance requires quorum-authorized rotation, monotonic versions, explicit overlap interval, and verified revocation of retired keys.

## Status and stop condition

Remain `B_STATIC_ONLY`; `allowed_next_branch_state=explicit_null`; `allowed_next_branch_value=null`; `transition_policy=prohibited`. Stop on missing rotation authorization/quorum, overlap or revocation status, version rollback, pending key checks, membership mismatch, or any execution/transition attempt.
