# R228 Membership-final review of R227

## Concrete remaining gap

R227 requires a membership signature, digest, version, and freshness, but does not bind the signature to a trusted membership-key anchor or define key-rotation/rollback rules. A stale or unauthorized signing key could therefore validate a syntactically current membership configuration.

## Fail-closed repair

Add key trust and rotation gates:

```yaml
membership_key_policy:
  trust_anchor_ref: "MISSING_EVIDENCE"
  signer_identity: "MISSING_EVIDENCE"
  signer_authorization: "pending"
  key_version: "MISSING_EVIDENCE"
  rotation_policy_ref: "MISSING_EVIDENCE"
  rollback_protection: "pending"
  signature_verification: "pending"
quorum_policy:
  untrusted_or_unauthorized_signer: "reject_and_remain_B_STATIC_ONLY"
  key_rollback_or_pending_rotation: "reject_and_remain_B_STATIC_ONLY"
```

Acceptance requires membership signatures rooted in a trusted anchor, authorized signer, current key version, and rollback-safe rotation.

## Status and stop condition

Remain `B_STATIC_ONLY`; `allowed_next_branch_state=explicit_null`; `allowed_next_branch_value=null`; `transition_policy=prohibited`. Stop on missing trust anchor/rotation/authorization, stale or rolled-back key, pending signature verification, membership mismatch, or any execution/transition attempt.
