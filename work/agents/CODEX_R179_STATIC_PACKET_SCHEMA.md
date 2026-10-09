# R179 Static paired-item specification / audit packet schema

**Purpose:** pre-execution implementability and identifiability check for the conditional FUP/AReject hypothesis. This is a schema only; placeholders are synthetic and do not instantiate project/protected data or benchmark results.

## Packet metadata

```yaml
packet_id: "R179-SYNTHETIC-001"
status: "static_only"
source_data: "synthetic_placeholder"
model_run: "MISSING_EVIDENCE"
benchmark_result: "MISSING_EVIDENCE"
predeclared_kill_margins:
  metadata_classifier_excess_accuracy: 0.05
  annotator_agreement_min: 0.80
  baseline_equivalence_delta: 0.03
```

## Paired-item record schema

```yaml
item_id: "SYN-PAIR-0001"
visible_artifact:
  canonical_bytes_sha256: "PLACEHOLDER_HASH"
  rendering_manifest: "MISSING_EVIDENCE"
  byte_identity_verified: "MISSING_EVIDENCE"
certificate:
  canonical_text: "SYNTHETIC UNIQUE CERTIFICATE PLACEHOLDER"
  normalized_surface_hash: "PLACEHOLDER_HASH"
  producer_frame_id_exposed: false
  label_id_exposed: false
latent_worlds:
  world_A:
    producer_frame_definition: "SYNTHETIC_FRAME_A"
    label_mapping: "SYNTHETIC_LABEL_MAP_A"
    allowed_answer_set: ["A"]
  world_B:
    producer_frame_definition: "SYNTHETIC_FRAME_B"
    label_mapping: "SYNTHETIC_LABEL_MAP_B"
    allowed_answer_set: ["B"]
non_equivalence_basis: "MISSING_EVIDENCE"
uniqueness_status: "MISSING_EVIDENCE"
expected_action: "MISSING_EVIDENCE"
leakage_audit:
  canonicalization_recipe: "MISSING_EVIDENCE"
  metadata_only_classifier_accuracy: "MISSING_EVIDENCE"
  pass_margin: "<= chance + 0.05"
independent_adjudication:
  annotator_count: "MISSING_EVIDENCE"
  admissible_interpretation_agreement: "MISSING_EVIDENCE"
  counter_world_non_equivalence_agreement: "MISSING_EVIDENCE"
  adjudication_notes: "MISSING_EVIDENCE"
```

## Known-unique control schema

```yaml
item_id: "SYN-UNIQUE-CTRL-0001"
paired_with: "SYN-PAIR-0001"
visible_artifact:
  canonical_bytes_sha256: "PLACEHOLDER_CONTROL_HASH"
certificate:
  normalized_surface_hash: "MATCHES_SAME_FORMAT_AS_PAIR"
latent_worlds:
  only_admissible_answer: "A"
uniqueness_status: "KNOWN_UNIQUE_PENDING_AUDIT"
expected_action: "accept-unique"
format_match_audit: "MISSING_EVIDENCE"
independent_adjudication: "MISSING_EVIDENCE"
```

## Required missing-evidence markers

Every unverified field must remain exactly `MISSING_EVIDENCE` (or a documented placeholder). A packet cannot be upgraded to an executable benchmark item while any of these remain missing: canonical visible bytes, rendering manifest, non-equivalence basis, answer sets, uniqueness status, leakage classifier result, annotator agreement, or control-format match.

## Acceptance / kill rules

- **Leakage kill:** metadata-only classifier accuracy > chance + 0.05 after canonicalization ⇒ discard the pair family.
- **Oracle/identifiability kill:** annotator agreement < 0.80 for admissible interpretations or counter-world non-equivalence ⇒ discard the item.
- **Control kill:** known-unique control cannot be accepted at the same certificate surface format ⇒ no attribution to FUP/AReject.
- **Baseline kill:** after eventual preregistered evaluation, generic abstention/label-error baseline within Δ=0.03 on all required metrics ⇒ retire the distinction.
- **Semantic-control kill:** byte identity passes but blinded semantic review fails ⇒ mark `MISSING_EVIDENCE` and discard; byte identity alone is insufficient.

## Status

`method_status=END-LINE`; `benchmark_only=true`; `new_method_validated=false`; `novelty_authorization=NONE`. This packet defines evidence prerequisites only and reports no benchmark result.
