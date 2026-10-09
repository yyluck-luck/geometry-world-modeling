# R237 Paired-trace red-team of R236

## Concrete confounds

1. **Expected-outcome leakage:** R236 stores expected outcomes alongside each trace. A consumer could classify from labels rather than enforce the protocol.
2. **Non-identifiability:** “Change only ack membership/version/order” is asserted but no canonical field diff or independent diff audit is defined; hidden serialization or metadata changes could drive the result.
3. **Control asymmetry:** Trace A is called a valid control, but its signer/membership/quorum evidence is synthetic and unresolved, so H1/H0 predictions may not actually differ.

## Repairs

```yaml
trace_audit:
  canonical_payload_diff_ref: "MISSING_EVIDENCE"
  allowed_changed_paths: ["ack_membership_version_or_order"]
  unexpected_diff_policy: "reject_and_remain_B_STATIC_ONLY"
  expected_outcome_visibility: "sealed_from_consumer"
  independent_diff_audit: "MISSING_EVIDENCE"
```

Expected outcomes must be withheld from any consumer and retained only as sealed commitments. A pair is admissible only if an independent diff audit confirms the single allowed change and an adjudicator confirms H1/H0 make different predictions.

## Rejection criteria

Reject the pair family if labels are visible, any unallowed field differs, canonical bytes cannot be compared deterministically, synthetic control validity is unresolved, or H1/H0 predictions coincide.

## Branch and status

Remain `B_STATIC_ONLY`; `allowed_next_branch_state=explicit_null`; `allowed_next_branch_value=null`; `transition_policy=prohibited`. No parser, consumer, external artifact, data/model access, evaluation, commitment resolution, or result mutation is authorized.
