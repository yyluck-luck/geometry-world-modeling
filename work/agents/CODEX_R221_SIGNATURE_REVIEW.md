# R221 Signature review of R220

## Concrete remaining gap

R220 requires an owner identity, detached signature, algorithm, and verification, but does not bind verification to a trusted key reference, validity interval, or revocation status. A self-signed or expired/revoked key could therefore satisfy a superficial `signature_verification=pass` field.

## Fail-closed repair

Add explicit trust and validity gates:

```yaml
signature_trust:
  trusted_key_ref: "MISSING_EVIDENCE"
  key_owner_match: "pending"
  signature_verification: "pending"
  certificate_validity: "pending"
  revocation_status: "pending"
  verification_time: "MISSING_EVIDENCE"
trust_policy:
  untrusted_key_or_owner_mismatch: "reject_and_remain_B_STATIC_ONLY"
  expired_or_revoked_key: "reject_and_remain_B_STATIC_ONLY"
  pending_verification: "reject_and_remain_B_STATIC_ONLY"
```

A detached signature is acceptable only when verified against an independently trusted, current, non-revoked key bound to the declared owner.

## Status and stop condition

Remain `B_STATIC_ONLY`; `allowed_next_branch_state=explicit_null`; `allowed_next_branch_value=null`; `transition_policy=prohibited`. Stop on missing trust root, owner mismatch, pending/failed signature, expired/revoked key, field-set mismatch, or any execution/transition attempt.
