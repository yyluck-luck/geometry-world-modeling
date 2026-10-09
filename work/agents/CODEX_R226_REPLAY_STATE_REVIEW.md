# R226 Replay-state review of R225

## Concrete remaining gap

R225 requires replica consistency and durable commit acknowledgement but does not define quorum/authority or recovery behavior. A split-brain verifier set could each report a locally consistent state, while a failover to a stale replica accepts a replayed sequence.

## Fail-closed repair

Add quorum and recovery gates:

```yaml
replica_policy:
  authority_or_quorum_ref: "MISSING_EVIDENCE"
  minimum_consistent_replicas: "MISSING_EVIDENCE"
  quorum_check: "pending"
  failover_state_validation: "pending"
  stale_replica_rejection: "pending"
  recovery_checkpoint_ref: "MISSING_EVIDENCE"
replay_policy:
  split_brain_or_quorum_failure: "reject_and_remain_B_STATIC_ONLY"
  unvalidated_failover_or_recovery: "reject_and_remain_B_STATIC_ONLY"
```

Acceptance requires an authoritative/quorum state, validated failover checkpoint, and explicit rejection of stale or split-brain replicas.

## Status and stop condition

Remain `B_STATIC_ONLY`; `allowed_next_branch_state=explicit_null`; `allowed_next_branch_value=null`; `transition_policy=prohibited`. Stop on missing quorum/authority or recovery evidence, pending replica checks, stale/split-brain state, replay/freshness failure, or any execution/transition attempt.
