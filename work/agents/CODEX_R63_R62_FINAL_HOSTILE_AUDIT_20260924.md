# R63 final hostile audit of R62

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only final audit. No fixture execution, real C8 data, replay, GPU/Slurm submission, receipt mutation, or validation-flag change.

## Verdict

**REVISE once for H2 precedence; otherwise PASS-ready.** R62 closes the ordering, owner-gate, arm-mapping, and hash-recomputation gaps. One concrete edge case remains: phase 0 says to scan H2 fields for forbidden markers, so an H2 placeholder such as `"REQUIRED"` can return `REJECT_FIXTURE` before the phase-2 H2 gate. Under the R52 contract, missing, ambiguous, or invalid H2 provenance must be classified as `H2_UNIDENTIFIABLE` before any arm score.

## Audit results

### Owner gate: PASS

`OWNER_ACCEPTED`, a review hash, and the accepted-protocol string are hard requirements before materialization. The design artifact intentionally lacks that status, so it cannot execute accidentally. The owner hash is correctly excluded from arm input domains.

### Phase order: PASS except H2 marker classification

The phase sequence is otherwise complete:

```text
phase_0_static_preflight -> phase_1_materialize -> phase_2_H2_gate
  -> phase_3_hash_verification -> phase_4_arm_score
```

Computed fields are created before their hashes, H2 is checked before H2-dependent hash extraction, and no arm score occurs before all gates. The only issue is that phase 0's generic marker scan includes H2 values.

### Arm mapping and access: PASS

All ten R52/R61 arms have a closed `arm_id = transition_rule_id` mapping and typed parameter values. Event, expected visibility, computed visibility, target truth, post-state, and output values remain in the shared base or are forbidden from rule parameters. All arms for one event use the same recomputed base hash.

### Hash domains and supplied-value verification: PASS

The computed records, manifest/context hashes, per-event base hashes, per-arm rule hashes, and derived arm-input hashes are each recomputed from raw subjects and compared to supplied values. The formulas do not self-hash, and expected/post-state/target fields are excluded.

### Evaluation leakage and terminal wording: PASS

Computed visibility drives query separation, denominators, and metrics. The owner gate and H2 gate do not select an arm. `PASS_CONTRACT_REPLAY` remains synthetic conformance only; a strong-control tie remains `REJECT_NON_IDENTIFIABLE`.

## One minimal correction

Change phase 0 so the generic forbidden-marker scan excludes the H2 subtree, and make phase 2 own every H2 presence/format/marker decision:

```text
phase_0_static_preflight:
  scan all supplied non-H2 fields for forbidden markers and type errors
  do not classify #/h2_provenance/* markers here
  enforce OWNER_ACCEPTED and static arm mapping

phase_2_H2_gate:
  if #/h2_provenance is missing, contains a forbidden marker,
  has an ambiguous frame label, malformed hashes, wrong identity formula,
  or max_abs_error > 1e-6:
      return H2_UNIDENTIFIABLE
```

H2 fields may still be recursively scanned for safety, but every missing/marker/format failure in that subtree must map to `H2_UNIDENTIFIABLE`, not `REJECT_FIXTURE`. This preserves the R52 terminal precedence while keeping all non-H2 placeholder failures as `REJECT_FIXTURE` before hashing.

## Stop conditions

Until this H2-subtree exception is added, do not execute the fixture. After it is added:

* owner-gate failure is `OWNER_REVIEW_REQUIRED`;
* H2 absence/ambiguity/marker/format failure is `H2_UNIDENTIFIABLE`;
* all other schema or hash failures are `REJECT_FIXTURE`;
* typed-arm invariant failure is `REJECT_CONTRACT`;
* a complete strong-control signature tie is `REJECT_NON_IDENTIFIABLE`.

No real C8 data, replay, GPU/Slurm, receipt, or validation-flag action is unlocked by this audit.

## Decision

**R63: REVISE once, then PASS-ready.** R62 is otherwise owner-ready. Apply the H2-subtree classification correction before any synthetic fixture execution or acceptance of a conformance result.
