# R218 Final schema review of R217

## Concrete remaining gap

R217 correctly rejects unknown/missing tokens and forbids coercion, but `acceptance_condition: all_required_result_fields_exactly_equal_pass` does not define the required field set. A permissive consumer could omit an outcome field and still evaluate the remaining fields as all-pass, creating an acceptance bypass.

## Required fail-closed repair

Define an immutable required-field manifest (for example, the full rule-outcome list plus provenance, integrity, verifier, and no-transition checks) and require exact set equality:

```yaml
required_result_field_manifest_ref: "MISSING_EVIDENCE"
field_set_policy: "exact_manifest_match"
missing_or_extra_result_field: "reject_and_remain_B_STATIC_ONLY"
acceptance_condition: "every_manifest_field_present_and_exactly_pass"
```

Until the manifest is supplied and independently verified, acceptance remains impossible.

## Branch and stop status

`branch=B_STATIC_ONLY`; `allowed_next_branch_state=explicit_null`; `allowed_next_branch_value=null`; `transition_policy=prohibited`. No parser, consumer, external artifact, data/model access, evaluation, commitment resolution, or result mutation occurred. Stop on omitted/extra fields, any non-pass token, or any attempted transition.
