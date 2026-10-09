# R180 Schema completeness review (R179 text only)

## Overall verdict

**FAIL for executable use; PASS for static-only intent.** R179 correctly marks most evidence as missing and declares static-only status, but several fields still permit hidden oracle leakage, circular labels, non-reproducible controls, or accidental execution authorization.

## Field-level findings and exact fixes

| Field | Finding | Required fix |
|---|---|---|
| `latent_worlds.world_A/world_B.*` | The full latent definitions and allowed answer sets appear in the packet. If this packet reaches an evaluator, it leaks the oracle. | Split into `authoritative_sealed_world_spec_ref` and `evaluator_visible_world_stub`; keep answer sets and mapping sealed, with only a commitment hash visible. |
| `uniqueness_status` | Free-form status can be assigned from the same hidden oracle that defines uniqueness, creating circularity. | Replace with `uniqueness_label_source`, `pre_registered_decision_rule`, and independently adjudicated `allowed_answer_set_commitment`; prohibit deriving it from `expected_action`. |
| `expected_action` | A populated action field can authorize a future runner or become the label itself. | Rename to `static_expected_action_placeholder`; require literal `MISSING_EVIDENCE` in all pre-execution packets and add `execution_authorization: false`. |
| `non_equivalence_basis` | A missing narrative basis is not a reproducible test. | Add `basis_type`, `pre_registered_predicate_ref`, and `independent_review_record_ref`; reject prose-only justification. |
| `canonical_bytes_sha256` / hashes | Placeholder hashes and unspecified canonicalization permit recomputation drift. | Add immutable `canonicalization_version`, byte encoding, line-ending policy, and `hash_status`; placeholders must never be treated as verified. |
| `MATCHES_SAME_FORMAT_AS_PAIR` | This assertion is circular until the format comparison is independently recorded. | Replace with `format_match_status: MISSING_EVIDENCE` plus a deterministic comparison recipe and independent audit reference. |
| `latent_worlds.only_admissible_answer` | A plain answer value exposes the gold label and allows accidental oracle use. | Store only a sealed commitment and adjudication reference; keep answer value evaluator-hidden. |
| packet metadata | `status: static_only` is descriptive but not an enforced gate. | Add explicit `execution_authorization: false`, `model_access: prohibited`, and `result_writes: prohibited`. |

## Static-only acceptance condition

The artifact can remain as a schema after applying the field fixes above. Until then, retain `benchmark_only=true`, `new_method_validated=false`, and `novelty_authorization=NONE`; do not instantiate items or run evaluation.
