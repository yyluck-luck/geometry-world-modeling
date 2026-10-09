# R215 Owner-artifact acceptance schema

Static schema only. No external artifact is supplied or consumed; no parser, consumer, data/model access, evaluation, commitment resolution, or result mutation occurs.

## Machine-checkable record

```yaml
record:
  external_id: "MISSING_EVIDENCE"
  provenance_chain: "MISSING_EVIDENCE"
  payload_sha256: "MISSING_EVIDENCE"
  canonicalization_recipe_ref: "MISSING_EVIDENCE"
  canonicalization_status: "pending"
  digest_recomputed_locally: "pending"
  digest_match: "pending"
  issuer_identity: "MISSING_EVIDENCE"
  verifier_identity: "MISSING_EVIDENCE"
  issuer_verifier_distinct: "pending"
  independence_basis: "MISSING_EVIDENCE"
  self_reference_check: "pending"
  external_scope_check: "pending"
  rule_outcomes:
    all_rules_must_match: "pending"
    terminal_rejection: "pending"
    unknown_state_rejection: "pending"
    explicit_null_state_value: "pending"
    deprecated_bare_field_rejection: "pending"
    no_transition: "pending"
```

Allowed result enum: `pass | fail | pending`; missing evidence maps to `pending`. Acceptance requires every required field resolved and every check equal to `pass`.

## Fail-closed branch gate

```yaml
branch:
  name: "B_STATIC_ONLY"
  allowed_next_branch_state: "explicit_null"
  allowed_next_branch_value: null
  transition_policy: "prohibited"
  execution_authorization: false
```

## Exact stop condition

If any required field is `MISSING_EVIDENCE` or any check is `pending`/`fail`, remain `B_STATIC_ONLY`; do not transition, retrieve, parse, execute, resolve commitments, access models/data, evaluate, or write results.
