# R240 Paired-trace decision

## Decision

**Currently reject the paired-trace hypothesis as non-identifiable for acceptance.** R239 correctly names timing, encoding, retry/error, and access-count channels, but its `hidden_label_predictor_accuracy` gate requires an executed predictor/audit. Under the mandated static-only boundary, that evidence does not exist, so the protocol cannot establish that the hidden provenance factor is the cause of any predicted difference.

The hypothesis may remain a conditional design idea for future review, but it must not be treated as a benchmark result, validated method, or novelty claim.

## Evidence still missing

- Equalized timing, compression, encryption-randomness, retry/error, and access-count traces.
- Independent side-channel audit and hidden-label predictor result with a predeclared chance margin.
- Canonical single-factor diff proof and sealed-outcome envelope audit.
- Independent adjudication that H1 and H0 make different predictions.

## Exact stop rule

Until all evidence above is independently supplied and verified, remain `B_STATIC_ONLY` with `allowed_next_branch_state=explicit_null`, `allowed_next_branch_value=null`, and `transition_policy=prohibited`. No parser, consumer, external artifact retrieval, data/model access, evaluation, commitment resolution, or result mutation is authorized.

`method_status=END-LINE`; `benchmark_only=true`; `new_method_validated=false`; `novelty_authorization=NONE`.
