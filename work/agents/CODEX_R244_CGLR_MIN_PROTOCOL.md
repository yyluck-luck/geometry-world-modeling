# R244 Minimal CGLR falsification protocol (Branch B static design)

## Decision boundary

This is a preregistration-ready **schema**, not an executed benchmark. No code, data, parser, model, GPU, Slurm, or evaluation action is authorized. Until the owner packet and audits below exist, the conjunction remains non-identifiable and status is `END-LINE`.

## Hypothesis and estimand

- **H1 (CGLR):** revealing only producer-frame/label provenance reduces false-unique acceptance on hidden counter-worlds while preserving acceptance on known-unique controls.
- **H0 (generic alternative):** the same reduction is explained by generic abstention prompting, explicit frame wording, source attribution, or active evidence acquisition.
- **Estimand:** paired difference-in-differences in false-unique acceptance rate (FUA):
  `[(FUA(provenance-reveal, counterworld) − FUA(provenance-reveal, unique)) − (FUA(neutral, counterworld) − FUA(neutral, unique))]`.
  Lower FUA under provenance reveal supports H1 only if all controls and audits pass.

## Minimal 2×2 arms

Cross two intervention arms with two outcome worlds:

1. **Provenance-only reveal:** reveal producer-frame/label provenance; hold visible artifact and certificate fixed.
2. **Provenance-neutral intervention:** add equal-length, semantically irrelevant metadata and identical caution budget; no provenance.
3. **Hidden counter-world:** same visible bytes admit two independently adjudicated latent interpretations.
4. **Known-unique control:** same surface schema, one admissible interpretation.

Include matched generic-abstention, explicit-frame (COMFORT/FoREST-style), source-attribution (MAVIS-style), and acquire/re-examine (BCEA/SIEVES-style) baselines.

## Canonicalization and controls

Pre-register a canonicalization recipe fixing UTF-8/NFC, line endings, field order, whitespace, token budget, certificate template, ordering, envelope size, timing budget, retry/error behavior, and access count. The only allowed semantic diff is provenance reveal versus neutral metadata. A deterministic diff manifest and independent audit must confirm this.

## Sealed outcomes and leakage audits

Seal latent worlds, allowed answer sets, and expected actions from any evaluator. Equalize commitment envelope length, ordering, metadata, compression, encryption randomness, timing, retries, and error paths. Run a metadata-only hidden-label predictor audit; accuracy must be at chance within a preregistered margin. Any side-channel difference rejects the pair family.

## Metrics and denominators

Report per-arm counts and denominators: FUA among all counter-world items; unique acceptance among unique controls; correct ambiguity rejection; over-rejection; abstention rate; coverage; and intervention token/latency budgets. Use paired item-level differences with confidence intervals and fixed missingness rules. Do not report aggregate rates without denominators.

## Falsification thresholds

Reject H1 if any of the following holds: (a) provenance-neutral intervention matches provenance reveal within Δ=0.03 on the estimand; (b) generic abstention/frame/source/acquisition baselines are statistically indistinguishable on all primary metrics; (c) unique-control acceptance drops by >5 percentage points under provenance reveal; (d) metadata-only predictor exceeds chance by >0.05; (e) independent adjudicator agreement on counter-world non-equivalence is <0.80; or (f) canonicalization/diff/side-channel audits fail.

## Required owner packet before any execution

A sealed owner packet must provide: item schema and hashes; latent-world/answer commitments; canonicalization version and diff manifest; baseline prompt specifications; envelope/side-channel audit; independent adjudication records; trustable audit identity; and preregistered thresholds above. All fields are currently `MISSING_EVIDENCE`.

## Stop rules and status

Stop and remain `B_STATIC_ONLY` if any required field is missing, any outcome becomes observable, any branch transition is attempted, or any parser/model/data/evaluation action is proposed. Current ruling: **END-LINE pending owner packet; no validation or novelty authorization.**

`method_status=END-LINE`; `benchmark_only=true`; `new_method_validated=false`; `novelty_authorization=NONE`.
