# R60 execution-preflight correction for R58

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only addendum. No fixture execution, real C8 data, replay, GPU/Slurm submission, receipt mutation, or validation-flag change.

## Purpose and order of operations

This addendum applies the R59 final schema correction to `CODEX_R58_R56_COMPUTED_ENVELOPE_CORRECTION_20260924.md`. It preserves R52/R56 visibility precedence, computed-only scoring, access-matched arms, H2 provenance, and `PASS_CONTRACT_REPLAY` scope.

The execution order is fixed:

1. Load the synthetic fixture as an untrusted design object.
2. Run the recursive marker and type preflight below.
3. If preflight fails, return `REJECT_FIXTURE` **before canonicalization, hashing, H2 scoring, or arm execution**.
4. If preflight passes, materialize computed geometry and the computed envelope, then canonicalize and hash.
5. Apply the H2 provenance gate before scoring any arm.

No hash or metric may be produced from a placeholder schema value.

## 1. Recursive forbidden-marker preflight

Use this exact marker list. A marker is forbidden when it appears as a complete string value or as a substring of any string value in a required field or extracted hash subject:

```json
{
  "forbidden_literal_markers": [
    "COMPUTED_BEFORE_HASH",
    "COMPUTED_FROM_PROJECTED_PIXELS",
    "COMPUTED_FROM_VISIBILITY_MASKS",
    "COMPUTED_FROM_COMPUTED_SETS",
    "COMPUTED_FROM_COMPUTED_COUNTS",
    "COMPUTED_FROM_MANIFEST_RULE_PATHS",
    "metadata_only",
    "canonical arm name",
    "canonical rule-only JSON",
    "REQUIRED",
    "SEE_SECTION",
    "AS_R50",
    "PLACEHOLDER",
    "TODO"
  ],
  "scan_rule": "recursively scan every scalar string under required paths and every extracted hash subject; reject on substring match",
  "scan_before": ["numeric_quantization", "canonical_json", "SHA256", "H2 scoring", "arm execution"]
}
```

The scan covers nested arrays and objects, not only top-level fields. It also scans `transition_rule_parameters`, `event_instance`, computed records, H2 fields, and every value selected by a hash path. A forbidden marker anywhere returns `REJECT_FIXTURE`.

## 2. Required materialized fields and type checks

The following paths must exist before canonicalization. Type checks are strict; null is allowed only where the event schema explicitly permits it (`none` event patch/value/correspondence):

| JSON pointer | Required type/invariant |
|---|---|
| `#/computed/projected_pixels` | array of camera-keyed cell records; each has camera, cell, integer pixel, finite `z` |
| `#/computed/visibility_masks` | array of camera-keyed records for every cell; Boolean predicate fields and `visible` |
| `#/computed/computed_visibility_sets` | object camera → patch → unique sorted cell-ID array |
| `#/computed/computed_visibility_counts` | object camera → patch → non-negative integer count matching computed sets |
| `#/computed/projected_pixels_sha256` | exactly 64 lowercase hexadecimal characters |
| `#/computed/visibility_masks_sha256` | exactly 64 lowercase hexadecimal characters |
| `#/computed/computed_visibility_sets_sha256` | exactly 64 lowercase hexadecimal characters |
| `#/computed/computed_visibility_counts_sha256` | exactly 64 lowercase hexadecimal characters |
| `#/contract_manifest_sha256` | exactly 64 lowercase hexadecimal characters |
| `#/state_pre_cells` | array of exactly 64 unique row-major records with id, patch, value, provenance |
| `#/event_instance` | object with event_id, patch, value, source_provenance, correspondence_id, allowed_support |
| `#/threshold/tau_l2` | finite non-negative number; R52 value is 0.25 |
| `#/update_budget` | object with positive integer transition/cell/evidence limits and fixed update order |
| `#/arm/arm_id` | actual arm identifier, not a marker; one of the declared R52 arms |
| `#/arm/transition_rule_id` | actual rule identifier matching `arm_id` |
| `#/arm/transition_rule_parameters` | JSON object containing only predeclared rule parameters |

The declared arm identifiers are:

```text
cglr_typed
append_only
generic_global
mask_only_local
residual_transport_untyped
no_reveal
shuffle_placebo
local_residual_no_provenance
local_residual_no_conservation
mask_same_residual
```

`arm_id` is metadata and is excluded from `base_input_sha256` and `arm_rule_sha256`, but it must still be a real identifier for result labeling. `transition_rule_id` must be the corresponding actual rule name; `transition_rule_parameters` must be a typed object, not a prose description.

## 3. Arm-rule parameter contract

Each rule object may contain only fixed, predeclared operator parameters, such as:

```json
{
  "threshold_gate": "on|off",
  "provenance_gate": "predicted_only|any",
  "correspondence_mode": "event_declared|fixed_wrong_component|none",
  "conservation_mode": "outside_zero|equal_mass_drift|none",
  "evidence_action": "append|none",
  "broadcast_coefficient": 0.25
}
```

The exact allowed keys and value domains are part of the arm rule definition and are hashed through `arm_rule_paths`. The object must not contain event values/residuals, expected or computed visibility, target truth, future camera answers, target RGB/depth, post-state, post-evidence, rendered output, or any post-hoc metric. Presence of any such field returns `REJECT_FIXTURE` before hashing. This keeps all arms access-matched through the shared base input and makes the rule hash the only intentional arm difference.

## 4. Preflight algorithm

The runner must perform these checks in order:

```text
preflight(fixture):
  assert required paths exist
  recursively scan required paths and extracted hash subjects for forbidden markers
  assert all required types, finite values, lengths, unique IDs, and hash formats
  assert arm_id is a declared actual ID and transition_rule_id matches it
  assert transition_rule_parameters has only allowed typed keys
  assert forbidden event/expected/post-state/target fields are absent from the rule object
  return PASS_PREFLIGHT
```

Any failed assertion returns `REJECT_FIXTURE` and stops. Only after `PASS_PREFLIGHT` may the runner compute world-point projections, materialize `computed.*`, quantize numeric values, canonicalize JSON, or calculate a SHA-256 value. A hash field must be recomputed from its raw subject and compared to the supplied value; a self-supplied hash is not trusted.

## 5. Hash and H2 ordering

After preflight and computed-envelope materialization, retain the R58 domains and formulas:

* `contract_manifest_sha256` hashes only rule paths, excluding expected visibility values;
* `fixture_context_sha256` hashes H2 identifiers and computed hash values, not its own field;
* `base_input_sha256` hashes computed geometry/masks/sets/counts, state, event, correspondence, threshold, budget, and manifest hash;
* `arm_rule_sha256` hashes only the actual rule ID and typed rule parameters;
* `arm_input_sha256` hashes the base and rule hashes.

The H2 object is then checked. Missing/ambiguous frame provenance or an identity error above `1e-6` returns `H2_UNIDENTIFIABLE` before any arm score. H2 cannot be used to bypass the preflight or to choose an arm rule.

## 6. Scope and stop conditions

R52/R56 query separation, channel-specific denominators, strong-control comparison, no-reveal identity, and `PASS_CONTRACT_REPLAY` remain unchanged after this preflight. Placeholder/type leakage is `REJECT_FIXTURE`; H2 failure is `H2_UNIDENTIFIABLE`; a typed-arm invariant failure is `REJECT_CONTRACT`; a complete strong-control tie is `REJECT_NON_IDENTIFIABLE`.

No real C8 data, replay, GPU/Slurm job, receipt edit, or validation-flag change is performed or unlocked by this correction.

## Decision

**R60 status: EXECUTION-PREFLIGHT CORRECTION COMPLETE / DESIGN-ONLY.** All known R59 placeholder and type ambiguities are now rejected before canonicalization and hashing. Owner review and H2 provenance remain required before any synthetic fixture execution.
