# R220 Final manifest review of R219

## Concrete remaining gap

R219 adds manifest version, canonicalization, SHA, and immutable status, but it does not bind the manifest to an external owner or signer. A party could provide a self-generated manifest with a valid hash and mark it immutable, making exact-set equality internally consistent while changing the required field set.

## Fail-closed repair

Require external authority and detached signature fields before acceptance:

```yaml
manifest_authority:
  owner_identity: "MISSING_EVIDENCE"
  owner_commitment: "MISSING_EVIDENCE"
  detached_signature: "MISSING_EVIDENCE"
  signature_algorithm: "MISSING_EVIDENCE"
  signature_verification: "pending"
  authority_scope: "MISSING_EVIDENCE"
manifest_policy:
  unsigned_or_unverified_manifest: "reject_and_remain_B_STATIC_ONLY"
  owner_scope_unresolved: "reject_and_remain_B_STATIC_ONLY"
```

A manifest hash alone is insufficient; acceptance requires an independently verifiable owner/signature binding and exact field-set match.

## Status and stop condition

Remain `B_STATIC_ONLY`; `allowed_next_branch_state=explicit_null`; `allowed_next_branch_value=null`; `transition_policy=prohibited`. Stop on absent/unverified owner or signature, mutable manifest status, hash mismatch, field omission/addition, non-pass token, or any attempted execution/transition.
