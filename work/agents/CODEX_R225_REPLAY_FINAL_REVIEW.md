# R225 Replay-final review of R224

## Concrete remaining gap

R224 requires durable verifier state and reset protection but does not define state integrity, rollback detection, or consistency across verifier instances. A stale snapshot or rollback of the seen-value store could accept a previously consumed sequence even when issuer binding and monotonicity are correct.

## Fail-closed repair

Add state-integrity and rollback gates:

```yaml
replay_state_integrity:
  state_store_commitment: "MISSING_EVIDENCE"
  state_store_integrity_digest: "MISSING_EVIDENCE"
  rollback_detection: "pending"
  replica_consistency_check: "pending"
  checkpoint_monotonicity: "MISSING_EVIDENCE"
  durable_commit_ack: "pending"
replay_policy:
  rollback_or_inconsistent_state: "reject_and_remain_B_STATIC_ONLY"
  missing_integrity_or_commit_ack: "reject_and_remain_B_STATIC_ONLY"
```

Acceptance requires an integrity-bound, monotonic state store with rollback detection, replica consistency, and durable commit acknowledgement.

## Status and stop condition

Remain `B_STATIC_ONLY`; `allowed_next_branch_state=explicit_null`; `allowed_next_branch_value=null`; `transition_policy=prohibited`. Stop on missing state integrity/rollback/replica/commit evidence, pending replay or freshness checks, stale/replayed status, or any execution/transition attempt.
