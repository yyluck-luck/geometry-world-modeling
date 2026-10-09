# R185 Continuation synthesis (R178–R184)

## Decision for next session

Retain only a **benchmark-only, conditional hypothesis**: a purported unique certificate should be rejected when evaluator-hidden producer-frame or label provenance permits multiple independently admissible latent interpretations. This remains a mechanism-level hypothesis, not a novelty or validation claim. Generic abstention, uncertainty, and label-error overlap remains substantial.

## Hard blockers

1. Sealed commitments must remain non-dereferenceable in the static branch, with an auditable access policy.
2. Canonicalization must have complete, versioned recipe content (field order, whitespace, exclusions, encoding, hash procedure) and reproducibility evidence.
3. Control-format equality must use a deterministic comparison recipe and independent audit; matching hashes alone are insufficient.
4. Branch boundary must remain machine-readable and fail-closed: `B_STATIC_ONLY`, `allowed_next_branch: null`, execution/validation prohibited.
5. Independent adjudication must establish admissible interpretations and counter-world non-equivalence without exposing the latent oracle.

## Kill conditions

Retire the hypothesis if any commitment is exposed or dereferenced in the static branch; any hash/control result is asserted with unresolved recipe/audit fields; a downstream parser treats placeholders or branch-A fields as authorization; or a generic abstention/label-error baseline is statistically equivalent within the predeclared margin once evaluation is ever authorized. Also kill if annotator agreement cannot establish non-equivalence without circular labels.

## Next eligible non-GPU evidence object

Create only a **sealed-reference/access-policy and canonicalization-control audit memo** containing synthetic commitments, the complete recipe text, deterministic comparison procedure, parser fail-closed assertions, and independent-review field definitions. Keep all actual values `MISSING_EVIDENCE`; do not instantiate benchmark items, resolve commitments, run models, or report results.

## Status invariants

`method_status=END-LINE`; `benchmark_only=true`; `new_method_validated=false`; `novelty_authorization=NONE`.
