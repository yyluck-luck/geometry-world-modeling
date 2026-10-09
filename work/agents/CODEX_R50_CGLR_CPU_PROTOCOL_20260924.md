# R50 executable CPU protocol for CGLR identifiability

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only protocol. Synthetic values only; no real C8 data, target RGB/depth, replay, GPU/Slurm execution, receipt mutation, or validation-flag change.

## Decision purpose

This protocol tests only whether the CGLR information pathway is distinguishable from its controls in a deterministic synthetic state machine. It does not validate a learned world model or prove literature novelty. The real-data C8 panel remains blocked by the R48 H2 provenance decision.

Outcomes are terminal and ordered:

1. H2_UNIDENTIFIABLE: the H2 provenance precondition is missing or fails.
2. REJECT_FIXTURE: schema, geometry, hash, denominator, or deterministic-integrity failure.
3. REJECT_CONTRACT: CGLR violates evidence immutability, support conservation, or no-reveal identity.
4. REJECT_NON_IDENTIFIABLE: CGLR satisfies its contract but has the same intervention signature as a control.
5. PASS_INFORMATION_PATHWAY_ONLY: CGLR has a unique synthetic signature. This permits only a DCR operator review; it is not a method novelty claim.

## 1. H2 provenance precondition

The protocol must not score any arm until this object is present and independently reviewed:

    h2_provenance = {
      "frame_label": "optical_cv" or "vmem_gl",
      "source_manifest_sha256": "<sha256 of exact source files>",
      "boundary_artifact_sha256": "<sha256 of CPU-checkable boundary artifact>",
      "identity_formula": "inv(T_frame) @ X == p_frame",
      "max_abs_error": <= 1e-6,
      "status": "PASS"
    }

The boundary artifact must include a known camera-frame pointmap, known c2w, the expected world point, and the exact operation at the CUT3R/VMem boundary. A helper-function algebra test without a producer pointmap-frame declaration is insufficient. If any field is absent, the frame label is ambiguous, or max_abs_error exceeds 1e-6, return H2_UNIDENTIFIABLE. No CGLR arm may be used to choose P0 versus P1.

The synthetic fixture itself never reads real C8 maps or target sensors. Its pointmap frame is explicit and must agree with this precondition.

## 2. Exact fixture JSON schema

The canonical fixture is UTF-8 JSON with sorted keys, separators comma/colon, no NaN/Inf, and all numeric state values quantized to integer micro-units q=1e-6 before hashing. The hashes field is excluded while computing fixture_sha256. A valid fixture has schema cglr-cpu-protocol-v1 and data_scope synthetic_only.

The following is the complete minimal fixture instance. Lists marked by range notation are expanded before hashing.

    {
      "schema": "cglr-cpu-protocol-v1",
      "protocol_id": "R50_CGLR_20260924",
      "data_scope": "synthetic_only",
      "status": "DESIGN_ONLY",
      "deterministic": true,
      "rng_seed": 0,
      "dtype": "float64",
      "quantization": {"unit": 0.000001, "rounding": "nearest_even"},
      "units": {"world": "metre", "depth": "metre", "state": "quantized_micro"},
      "camera_convention": {
        "pose": "camera_to_world",
        "axes": "OpenCV_x_right_y_down_z_forward",
        "K": [[300,0,320],[0,300,240],[0,0,1]],
        "source_size": [640,480],
        "map_size": [512,288],
        "principal_point": "map_centre",
        "pixel_rule": "round_then_euclidean_radius_le_1.5"
      },
      "h2_provenance": {
        "frame_label": "REQUIRED_FROM_OWNER_ARTIFACT",
        "source_manifest_paths": [
          "work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py",
          "work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R/src/dust3r/utils/geometry.py",
          "work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R/cloud_opt/dust3r_opt/optimizer.py"
        ],
        "source_manifest_sha256": "REQUIRED",
        "boundary_artifact_sha256": "REQUIRED",
        "identity_formula": "REQUIRED",
        "max_abs_error": "REQUIRED",
        "status": "REQUIRED_PASS"
      },
      "cameras": {
        "context": {
          "c2w": [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]
        },
        "reveal_A": {
          "c2w": [[0,0,1,0.8],[0,1,0,0.1],[-1,0,0,0.2],[0,0,0,1]]
        },
        "negative_B": {
          "c2w": [[0,-1,0,-0.2],[1,0,0,0.6],[0,0,1,0.3],[0,0,0,1]]
        },
        "third_C": {
          "c2w": [[1,0,0,0.3],[0,0,-1,-0.4],[0,1,0,0.7],[0,0,0,1]]
        }
      },
      "patches": {
        "A": {"component": "surface_S", "cells": ["A00","A01","A02","A03","A04","A05","A06","A07","A08","A09","A10","A11","A12","A13","A14","A15"]},
        "C": {"component": "surface_S", "cells": ["C00","C01","C02","C03","C04","C05","C06","C07","C08","C09","C10","C11","C12","C13","C14","C15"]},
        "B": {"component": "unrelated_U", "cells": ["B00","B01","B02","B03","B04","B05","B06","B07","B08","B09","B10","B11","B12","B13","B14","B15"]},
        "U": {"component": "outside", "cells": ["U00","U01","U02","U03","U04","U05","U06","U07","U08","U09","U10","U11","U12","U13","U14","U15"]}
      },
      "visibility": {
        "reveal_A": {"A": 16, "C": 0, "B": 0, "U": 0},
        "negative_B": {"A": 0, "C": 0, "B": 16, "U": 0},
        "third_C": {"A": 0, "C": 16, "B": 0, "U": 0}
      },
      "correspondence": {
        "A_to_C": {"type": "oracle_same_surface", "pairs": 16},
        "B_to_C": {"type": "none", "pairs": 0},
        "shuffled_A_to_C": {"type": "fixed_wrong_component", "source_patch": "A", "target_patch": "U", "pairs": 16, "permutation_seed": 0}
      },
      "state_pre": {
        "E": {
          "records": [
            {"id": "m_B", "patch": "B", "value": [0.4,0.4,0.8], "provenance": "measured"}
          ]
        },
        "B": {
          "slots": [
            {"id": "a_pred", "patch": "A", "value": [0.1,0.1,1.0], "provenance": "predicted"},
            {"id": "c_pred", "patch": "C", "value": [0.1,0.1,1.0], "provenance": "predicted"},
            {"id": "b_measured", "patch": "B", "value": [0.4,0.4,0.8], "provenance": "measured"},
            {"id": "u_pred", "patch": "U", "value": [0.2,0.2,0.9], "provenance": "predicted"}
          ]
        }
      },
      "truth": {
        "A": [0.9,0.1,1.2],
        "C": [0.9,0.1,1.2],
        "B": [0.2,0.5,0.7],
        "U": [0.2,0.2,0.9]
      },
      "events": {
        "none": {"patch": null, "value": null, "tau_l2": 0.25},
        "A_small": {"patch": "A", "value": [0.2,0.1,1.02], "tau_l2": 0.25},
        "A_large": {"patch": "A", "value": [0.9,0.1,1.2], "tau_l2": 0.25},
        "B_large": {"patch": "B", "value": [0.1,0.5,0.7], "tau_l2": 0.25}
      },
      "arm_ids": [
        "cglr_typed", "append_only", "generic_global",
        "mask_only_local", "residual_transport_untyped",
        "no_reveal", "shuffle_placebo"
      ],
      "hashes": {
        "fixture_sha256": "COMPUTED_AFTER_CANONICALIZATION",
        "state_pre_sha256": "COMPUTED",
        "source_manifest_sha256": "FROM_H2_OBJECT"
      }
    }

Each cell name is literal and must be retained before hashing. Values are state vectors [appearance_1, appearance_2, metric_depth]; this is not target RGB or depth data.

## 3. Exact arm definitions

All arms receive the same canonical state_pre, event object, correspondence table, threshold, and operation budget. Arm input hashes must match after removing only arm_id and the arm's declared rule. Predictions may never be inserted into E.

1. cglr_typed:
   * append the reveal record to E;
   * compute residual e=event.value-B_pre[event.patch];
   * write only when ||e||_2 > tau_l2, support intersects, and the target slot provenance is predicted;
   * for A_large, write A and transfer the same residual through oracle A_to_C to C;
   * for A_small, the B state remains byte-identical;
   * for B_large, the measured B slot is not writable;
   * all non-gated slots are byte-identical.

2. append_only:
   * append the reveal record to E;
   * never rewrite B;
   * third-C output uses the unchanged c_pred slot.

3. generic_global:
   * append the reveal record to E;
   * add the event residual to every B slot, including measured b_measured and unrelated u_pred, using a fixed broadcast coefficient 0.25;
   * this is a deterministic global-update control with a fixed broadcast coefficient; no capacity claim is made.

4. mask_only_local:
   * append the reveal record to E;
   * use the same A/C support mask as CGLR;
   * apply a fixed residual [0.4,0.0,0.1] independent of event magnitude and provenance;
   * this control tests whether a local mask alone explains the result.

5. residual_transport_untyped:
   * append the reveal record to E;
   * transport residual through the event correspondence regardless of provenance;
   * for B_large, write the measured b_measured slot;
   * for A_large, write A and C;
   * no outside-support conservation rule is enforced.

6. no_reveal:
   * do not append an event;
   * return state_pre exactly.

7. shuffle_placebo:
   * execute cglr_typed with the fixed wrong-component correspondence A-to-U;
   * A may update for A_large, U receives the misrouted residual, and C must not receive the oracle A residual.

The abstract renderer is fixed: the reveal camera scores patch A, the third camera scores patch C, and the negative camera scores patch B. E is not directly substituted for the third-C slot; only B-state writes affect C. This prevents append-only from receiving an unregistered direct view of C. Each slot value is broadcast to its 16 named cells before rendering, so the state and metric denominators are cell-level.

## 4. Hashes and integrity

Use SHA-256 over canonical JSON after expanding cell lists and quantizing numeric values. Record:

* fixture_sha256: canonical fixture excluding hashes;
* state_pre_sha256 and evidence_pre_sha256;
* per-event event_sha256;
* per-arm arm_input_sha256;
* B_post_sha256, E_post_sha256, and rendered_output_sha256;
* h2 source_manifest_sha256 and boundary_artifact_sha256;
* protocol_sha256: this protocol file's exact bytes.

Hash failure, missing hash, or an arm input mismatch is REJECT_FIXTURE. Do not overwrite any existing C8 hash or receipt.

## 5. Denominators and metrics

The fixture has 16 cells in each of A, C, B, and U; state denominator N_state=64.

* N_reveal=N_A=16. Reveal error is mean L1 error over A cells.
* N_third=N_C=16. Third-camera error is mean L1 error over C cells.
* N_negative=N_B=16. Negative-reveal error is mean L1 error over B cells.
* N_outside=32 for an A/C update (B and U cells); N_outside=48 for a B update (A, C, and U cells). Outside drift fraction is changed outside cells divided by the event-specific N_outside. A slot value is broadcast to all 16 cells in its named patch before this count.
* N_changed is the number of state cells whose quantized values differ from B_pre. Locality precision is changed cells in allowed support divided by N_changed; if N_changed=0, report UNDEFINED_NO_CHANGE rather than zero. Locality recall is changed cells in allowed support divided by allowed-support cells.
* N_evidence is the count of E records, and evidence integrity is the exact relation E_post = E_pre union event. Predictions entering E are an immediate contract failure.
* no-reveal identity is an exact B and E hash equality, not a tolerance.
* Every metric is reported per arm and per event; no cells are pooled across events or cameras.

The primary signature is the vector (B_post_hash, E_post_hash, outside_drift_fraction, third_error, negative_error, no_reveal_identity). A CGLR signature that is identical to a control across all events is not identifiable.

## 6. PASS and rejection rules

Before arm scoring, apply H2 precondition and fixture/hash checks.

PASS_INFORMATION_PATHWAY_ONLY requires all of the following:

1. H2 provenance status is PASS.
2. The fixture and every arm input hash is valid.
3. For A_large, cglr_typed reaches truth on A and C within quantization epsilon, has outside drift 0, preserves measured B, and appends only the reveal to E.
4. For A_small and none, cglr_typed leaves B exactly unchanged; the reveal append for A_small is the only E difference.
5. For B_large, cglr_typed leaves C and measured B unchanged while E appends the negative reveal.
6. no_reveal is byte-identical everywhere.
7. The cglr_typed signature differs from append_only, mask_only_local, residual_transport_untyped, and shuffle_placebo on at least one predeclared event, and no control matches the complete CGLR event signature.
8. The third-camera C visibility is disjoint from the reveal camera image plane, while A is visible at the reveal camera, by the explicit visibility counts.

Return REJECT_CONTRACT if any conservation, provenance, no-reveal, hash, or event semantics fail. Return REJECT_NON_IDENTIFIABLE if CGLR's full event signature is matched by a control or if the third-C improvement is explained by append-only/mask-only. Return H2_UNIDENTIFIABLE before all other outcomes when provenance is absent or inconsistent. A PASS is a synthetic information-pathway result only; it cannot authorize a learned-model claim or real-data C8 rescoring.

## 7. No-go boundaries

Do not add target RGB/depth, real C8 maps, future camera answers, learned weights, or post-hoc threshold fitting. Do not call scene_13/scene_14 independent test data. Do not use this protocol to repair old C8 J or to claim hidden-surface support scarcity. Keep new_method_validated=false and novelty_authorization=NONE.
