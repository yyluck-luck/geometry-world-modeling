# R236 Protocol-only discriminating test

## Hypothesis

H1: inconsistent key-status acceptance is caused by invalidation acknowledgements that are not bound to current authorized membership/version/order, allowing a stale replica cache to remain trusted.

## Strongest competing explanation

H0: the discrepancy is caused by a generic rule-composition or parser-state bug independent of cache invalidation, membership, or acknowledgement ordering.

## Static paired-trace design (synthetic only)

Define two matched protocol traces with identical rule outcomes and timestamps:

- **Trace A (valid control):** current membership/version, authenticated ack signer set, quorum threshold met, ordered invalidation event, cache-consistency state marked synthetic.
- **Trace B (single-factor perturbation):** change only ack membership/version/order binding to an invalid or stale value; retain all other fields identical.

No trace is executed; values remain placeholders.

```yaml
trace_pair:
  control_trace: "SYNTHETIC_TRACE_A"
  perturbation_trace: "SYNTHETIC_TRACE_B"
  changed_factor: "ack_membership_version_or_order"
  execution_status: "NOT_RUN"
```

## Required evidence before any conclusion

- Canonical, byte-identical trace serialization except the declared factor.
- Independently specified expected outcomes for both traces.
- Evidence that signer identity, membership version, quorum threshold, and event order are the only changed fields.
- A parser/enforcer audit record proving unknown/pending fields reject.
- Independent adjudication that H1 and H0 make different predictions.

All evidence fields are currently `MISSING_EVIDENCE`.

## Rejection criteria

Reject H1 as discriminating if: (1) no single-factor pair can be specified; (2) H0 predicts the same outcome as H1; (3) any trace difference leaks through unrelated formatting; (4) expected outcomes are treated as observed results; or (5) required audit/evidence fields remain missing and someone attempts to infer a result.

## Branch and status

Remain `B_STATIC_ONLY`; `allowed_next_branch_state=explicit_null`; `allowed_next_branch_value=null`; `transition_policy=prohibited`. No external artifact, parser, consumer, data/model access, evaluation, commitment resolution, or result mutation is authorized.
