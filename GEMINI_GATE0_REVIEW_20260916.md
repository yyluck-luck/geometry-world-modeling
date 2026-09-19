# Gemini advisory Gate0 review — 2026-09-16

Status: `REVIEW_RECEIVED_ADVISORY_ONLY`. This is a root-authored summary of a response read from the user-opened Gemini in-app browser. It is not an independent reproduction, signed pre-run approval, or scientific result.

Conversation: https://gemini.google.com/app/98591b89d8bb18fc

The prompt disclosed only four summarized implementation issues: circular pre/post checks, the two S103 meanings, the keyword-only future-path guard, and declared versus recomputed staged hashes. No credentials, private source files, raw research data, or personal identifiers were submitted.

## Recommendations received

1. Separate pre-run configuration/input checks from post-run output and metric checks.
2. Use unambiguous names for the saved-geometry diagnostic and the VMem baseline.
3. Enforce the permitted time/index inputs in the loader and/or filesystem boundary; do not rely on JSON keyword matching.
4. Compute SHA-256 from actual staged weights and inputs and fail dispatch when it differs from the frozen manifest.
5. Label synthetic or no-data tests as pipeline verification only. Retain local logs and complete denominators.
6. Use an adversarial leakage probe before execution and preserve source/config/environment provenance and RNG behavior.

## Root disposition

- Accepted 1–4 as concrete corroboration of the existing local audit. `validate_gate0_v2.py` already implements the staged readiness structure and actual file hash checks; a real contract and runtime isolation evidence remain necessary.
- Accepted 5. Job 588611 is explicitly a no-data model-load smoke, not model forward or scientific evidence.
- Accepted 6 in a bounded form: denied-outcome probes must exercise the actual predictor boundary, and reproducibility records must capture relevant versions, source/config hashes, seeds and measured nondeterminism.
- Did not adopt a blanket demand for bit-exact reproduction across hardware, a complete environment-variable dump, or a repository-wide hard rename of immutable historical experiment files. Those are not prerequisites established by the current evidence and could misstate reproducibility or damage provenance. Active plans now use display aliases `S103-GeoDiag` and `S103-VMemBase`, with historical paths retained.
- Do not remove input-manifest freezing because Gemini mentioned post-run manifest generation: the pre-run manifest must exist and be reviewed before dispatch; only output manifests and metric receipts are post-run artifacts.

## Remaining decision

Gemini cannot grant Gate0. A separate reviewer must inspect and bind the concrete adapter, effective runtime configuration, permitted inputs, enforced isolation probe, source/weight hashes, budget and wrapper before the actual v2 contract can reach `PRE_RUN_READY`. Held-out and method conclusions additionally require output sealing and post-run independent recomputation.
