# R219 Manifest review of R218

## Concrete remaining gap

R218 requires an immutable manifest and exact set equality, but `required_result_field_manifest_ref` remains `MISSING_EVIDENCE` and has no manifest version, canonical serialization, or integrity digest. A consumer could substitute or silently revise the field set while still claiming exact equality.

## Fail-closed repair

Require a committed manifest identity before any acceptance evaluation:

```yaml
required_result_field_manifest:
  manifest_id: "MISSING_EVIDENCE"
  manifest_version: "MISSING_EVIDENCE"
  canonicalization_recipe_ref: "MISSING_EVIDENCE"
  manifest_sha256: "MISSING_EVIDENCE"
  immutable_status: "MISSING_EVIDENCE"
  exact_set_match: "pending"
manifest_policy:
  missing_or_unverified_manifest: "reject_and_remain_B_STATIC_ONLY"
  any_field_omitted_or_added: "reject_and_remain_B_STATIC_ONLY"
```

Acceptance requires a single independently verified manifest whose canonical hash and exact field set are stable; no local or runtime-generated manifest is admissible.

## Status and stop condition

Remain `B_STATIC_ONLY`; `allowed_next_branch_state=explicit_null`; `allowed_next_branch_value=null`; `transition_policy=prohibited`. Stop on missing/unverified manifest identity, hash mismatch, field omission/addition, non-pass token, or any attempted execution/transition.
