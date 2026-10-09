# R59 final schema audit of R58

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only hostile audit. No fixture execution, real C8 data, replay, GPU/Slurm submission, receipt mutation, or validation-flag change.

## Verdict

**REVISE once before final owner acceptance.** R58's computed envelope is materially complete. Its projection/mask/set/count hashes do not self-hash, the fixture-context and base-input domains resolve without expected/post-state/target values, and each arm shares the same per-event base input while differing only in the rule hash. One remaining schema ambiguity is that only `COMPUTED_BEFORE_HASH` is explicitly forbidden as a run-time literal; other descriptive placeholders remain in the envelope and could be mistaken for valid values.

## Audit findings

### 1. Placeholder handling is incomplete

R58 correctly states that `COMPUTED_BEFORE_HASH` is forbidden, but the schema also contains these descriptive markers:

* `COMPUTED_FROM_PROJECTED_PIXELS`
* `COMPUTED_FROM_VISIBILITY_MASKS`
* `COMPUTED_FROM_COMPUTED_SETS`
* `COMPUTED_FROM_COMPUTED_COUNTS`
* `COMPUTED_FROM_MANIFEST_RULE_PATHS`
* `metadata_only`
* `canonical arm name`
* `canonical rule-only JSON`

The document explains that they are descriptions, but an execution preflight is not required to reject every one. If any marker survives into a hash subject, the protocol can produce a formally valid hash over a non-executed placeholder.

### 2. Hash recursion and leakage audit: PASS

The four computed hashes hash their raw computed records, not their own hash fields. `contract_manifest_sha256` hashes the rule-only manifest paths, which contain no computed hash values or expected visibility values. `fixture_context_sha256` hashes the already computed hash values but is not itself included in `fixture_context_paths`; there is no recursive cycle. `base_input_paths` include computed records and the manifest hash, but no post-state, rendered output, target truth, or expected set. `arm_input_sha256` hashes only the base and rule hashes.

### 3. Access matching and non-leakage: PASS

For every event, all arms share the same state, event, correspondence, threshold, update budget, geometry, and computed visibility records through `base_input_sha256`. The rule parameter domain is the only arm-specific input. R58 forbids event values, expected/computed visibility, target truth, post-state, and output in `transition_rule_parameters`; this is sufficient once the placeholder preflight is added.

### 4. R56/R52 precedence: PASS

R58 inherits R56's explicit precedence over R52 §2.2 for projection, rounded-pixel bounds, occlusion, and query separation. No ambiguity remains in that ordering.

## Exact final correction

Add an execution preflight object and apply it before canonicalization or any hash computation:

```json
{
  "execution_preflight": {
    "forbidden_literal_markers": [
      "COMPUTED_BEFORE_HASH",
      "COMPUTED_FROM_PROJECTED_PIXELS",
      "COMPUTED_FROM_VISIBILITY_MASKS",
      "COMPUTED_FROM_COMPUTED_SETS",
      "COMPUTED_FROM_COMPUTED_COUNTS",
      "COMPUTED_FROM_MANIFEST_RULE_PATHS",
      "metadata_only",
      "canonical arm name",
      "canonical rule-only JSON"
    ],
    "required_materialized_fields": [
      "#/computed/projected_pixels",
      "#/computed/visibility_masks",
      "#/computed/computed_visibility_sets",
      "#/computed/computed_visibility_counts",
      "#/computed/projected_pixels_sha256",
      "#/computed/visibility_masks_sha256",
      "#/computed/computed_visibility_sets_sha256",
      "#/computed/computed_visibility_counts_sha256",
      "#/contract_manifest_sha256",
      "#/state_pre_cells",
      "#/event_instance",
      "#/threshold/tau_l2",
      "#/update_budget",
      "#/arm/transition_rule_id",
      "#/arm/transition_rule_parameters"
    ],
    "reject_if_marker_occurs": "any string value in any required materialized field or extracted hash subject",
    "reject_if_missing_or_placeholder": true
  }
}
```

The preflight must recursively scan required fields and every extracted hash subject. A field is valid only after its placeholder marker is replaced by the correctly typed canonical value: arrays/records for computed objects and hashes, an actual arm identifier/rule ID, and a canonical rule-parameter object. `arm_id` may be excluded from hash inputs, but `metadata_only` is not an acceptable run-time value for it.

After preflight, retain the R58 formulas unchanged. Any marker, missing field, or wrong type returns `REJECT_FIXTURE` before H2 scoring or arm execution. H2 absence or failure still returns `H2_UNIDENTIFIABLE` before all fixture outcomes.

## Final stop conditions

After this preflight is added, owner review may accept the schema for a later synthetic-only execution. A computed/expected mismatch remains `REJECT_FIXTURE`; a strong-control complete-signature tie remains `REJECT_NON_IDENTIFIABLE`; a typed-arm invariant failure remains `REJECT_CONTRACT`. No real C8, replay, GPU/Slurm, receipt, or validation-flag action is unlocked.

## Decision

**R59: REVISE once, then PASS-ready.** R58's hash domains, computed-only semantics, precedence, and access matching survive hostile review. Add the explicit marker/type preflight before final owner acceptance.
