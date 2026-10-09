# R186 Sealed-reference / canonicalization-control audit memo schema

**Scope:** schema only. All values are synthetic placeholders or `MISSING_EVIDENCE`; commitments are never resolved and no benchmark item is instantiated.

## Memo gates

```yaml
memo_id: "R186-SYNTHETIC-001"
branch: "B_STATIC_ONLY"
allowed_next_branch: null
execution_authorization: false
model_access: "prohibited"
result_writes: "prohibited"
source_data: "synthetic_placeholder"
```

## Synthetic sealed commitments

```yaml
commitments:
  producer_frame_world_A: "SYNTHETIC_COMMITMENT_A"
  producer_frame_world_B: "SYNTHETIC_COMMITMENT_B"
  answer_set_A: "SYNTHETIC_ANSWER_COMMITMENT_A"
  answer_set_B: "SYNTHETIC_ANSWER_COMMITMENT_B"
  sealed_spec_ref: "MISSING_EVIDENCE"
  dereference_status: "MISSING_EVIDENCE"
  access_policy_ref: "MISSING_EVIDENCE"
```

Raw world definitions and answer values are intentionally absent. `dereference_status` must remain `MISSING_EVIDENCE` until an independently authorized audit exists.

## Complete canonicalization recipe fields

```yaml
canonicalization:
  recipe_id: "SYN-CANON-0.1"
  version: "0.1.0"
  encoding: "UTF-8"
  unicode_normalization: "NFC"
  line_endings: "LF"
  whitespace_policy: "MISSING_EVIDENCE"
  field_order: "MISSING_EVIDENCE"
  excluded_fields: "MISSING_EVIDENCE"
  numeric_format: "MISSING_EVIDENCE"
  serialization_format: "MISSING_EVIDENCE"
  hash_algorithm: "SHA-256"
  recipe_content: "MISSING_EVIDENCE"
  reproducibility_check: "MISSING_EVIDENCE"
```

No hash, identity, or equality claim is valid while any recipe field remains missing.

## Deterministic comparison procedure

```yaml
comparison:
  procedure_id: "SYN-FMT-CMP-0.1"
  input_fields: ["canonical_certificate", "normalized_surface_hash"]
  normalization_recipe_ref: "SYN-CANON-0.1"
  comparison_operator: "MISSING_EVIDENCE"
  tie_break_rule: "MISSING_EVIDENCE"
  independent_audit_ref: "MISSING_EVIDENCE"
  comparison_result: "MISSING_EVIDENCE"
```

A matching placeholder hash is not a comparison result.

## Parser fail-closed assertions

```yaml
parser_guards:
  reject_if_branch != "B_STATIC_ONLY": true
  reject_if_allowed_next_branch != null: true
  reject_if_execution_authorization != false: true
  reject_if_model_access != "prohibited": true
  reject_if_result_writes != "prohibited": true
  reject_if_any_required_field == "MISSING_EVIDENCE": true
  commitment_dereference: "prohibited"
  parser_audit_ref: "MISSING_EVIDENCE"
```

These assertions are declarative schema requirements; no parser is run by this memo.

## Independent review fields

```yaml
independent_review:
  reviewer_count: "MISSING_EVIDENCE"
  conflict_policy: "MISSING_EVIDENCE"
  interpretation_agreement: "MISSING_EVIDENCE"
  non_equivalence_agreement: "MISSING_EVIDENCE"
  canonicalization_reproducibility_agreement: "MISSING_EVIDENCE"
  control_comparison_agreement: "MISSING_EVIDENCE"
  review_record_ref: "MISSING_EVIDENCE"
```

## Status

`method_status=END-LINE`; `benchmark_only=true`; `new_method_validated=false`; `novelty_authorization=NONE`. This memo authorizes no data creation, commitment resolution, model access, execution, evaluation, or result mutation.
