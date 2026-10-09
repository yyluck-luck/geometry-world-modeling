# R212 Acceptance-gate repair delta

Applies conceptually to R210/R211; prior files remain unchanged. Non-executable schema only. No external retrieval, parser/consumer execution, commitment resolution, or evaluation; unresolved fields remain `MISSING_EVIDENCE`.

## Explicit gate result enum

```yaml
gate_result_enum: ["pass", "fail", "pending"]
pending_policy: "reject_and_remain_static"
missing_evidence_policy: "pending"
```

## Required provenance and self-reference gates

```yaml
provenance_gates:
  self_reference:
    result: "pending"
    required_result: "pass"
  external_record_scope:
    result: "pending"
    required_result: "pass"
  provenance_chain:
    result: "pending"
    required_result: "pass"
```

## Integrity gates

```yaml
integrity_gates:
  digest_recomputed_locally:
    result: "pending"
    required_result: "pass"
  digest_match:
    result: "pending"
    required_result: "pass"
  canonicalization_recipe:
    result: "pending"
    required_result: "pass"
```

## Independent verifier gate

```yaml
verifier_gate:
  verifier_identity: "MISSING_EVIDENCE"
  issuer_identity: "MISSING_EVIDENCE"
  issuer_verifier_distinct:
    result: "pending"
    required_result: "pass"
  independence_basis:
    result: "pending"
    required_result: "pass"
```

## Acceptance decision

```yaml
acceptance_gate:
  decision: "pending"
  allowed_decisions: ["accept", "reject", "pending"]
  accept_allowed_if: "all_required_gates == pass"
  otherwise: "remain_B_STATIC_ONLY"
```

No synthetic or `MISSING_EVIDENCE` value can satisfy a `pass` gate.

## Preserved no-transition gates

```yaml
branch: "B_STATIC_ONLY"
allowed_next_branch_state: "explicit_null"
allowed_next_branch_value: null
transition_policy: "prohibited"
execution_authorization: false
model_access: "prohibited"
result_writes: "prohibited"
```

## Status

`method_status=END-LINE`; `benchmark_only=true`; `new_method_validated=false`; `novelty_authorization=NONE`. This delta authorizes no external retrieval, parser, consumer execution, commitment resolution, evaluation, or result mutation.
