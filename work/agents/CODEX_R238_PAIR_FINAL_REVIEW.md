# R238 Paired-trace final review of R237

## Concrete remaining confound

R237 seals expected outcomes and whitelists one changed path, but does not specify whether sealed commitments have identical lengths, ordering, or envelope metadata. A consumer or preprocessing step could infer the outcome from commitment size, field presence, or ordering without evaluating the protocol factor.

## Required evidence / repair

```yaml
sealed_outcome_audit:
  envelope_schema_version: "MISSING_EVIDENCE"
  envelope_length_equal: "pending"
  field_order_equal: "pending"
  metadata_constant: "pending"
  commitment_access_control: "MISSING_EVIDENCE"
  side_channel_audit: "MISSING_EVIDENCE"
canonical_diff_audit:
  allowed_changed_paths: ["ack_membership_version_or_order"]
  unexpected_diff_policy: "reject_and_remain_B_STATIC_ONLY"
  independent_diff_record: "MISSING_EVIDENCE"
```

Require equalized sealed envelopes and an independent side-channel audit before treating the pair as discriminating. If envelope equality or side-channel control cannot be established, reject the paired-trace hypothesis as non-identifiable.

## Rejection criteria

Reject if any sealed-envelope metadata differs, commitment access is not controlled, canonical diff evidence is missing, H1/H0 predictions coincide, or expected outcomes become observable.

## Branch and status

Remain `B_STATIC_ONLY`; `allowed_next_branch_state=explicit_null`; `allowed_next_branch_value=null`; `transition_policy=prohibited`. No parser, consumer, external artifact, data/model access, evaluation, commitment resolution, or result mutation is authorized.
