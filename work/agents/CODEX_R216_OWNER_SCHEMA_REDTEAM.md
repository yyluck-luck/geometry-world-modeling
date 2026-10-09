# R216 R215 owner-schema red-team

## Concrete ambiguity

R215 declares the result enum `pass | fail | pending`, but does not explicitly state what happens when a supplied owner artifact contains an unknown result token (for example, `verified`, an empty string, or a missing rule outcome). The final stop condition covers `MISSING_EVIDENCE`, `pending`, and `fail`, but an unknown token could be mishandled as truthy or accepted by a permissive consumer.

## Required fail-closed repair

Add a schema invariant:

```yaml
unknown_or_missing_result_token: "reject_and_remain_B_STATIC_ONLY"
missing_rule_outcome: "reject_and_remain_B_STATIC_ONLY"
```

Every result-bearing field must be present and exactly one of `pass | fail | pending`; only all fields equal to `pass` can satisfy acceptance. No implicit coercion, truthiness, or default success is permitted.

## Status and stop condition

This is a schema review only. No external artifact, parser, consumer, data/model access, evaluation, commitment resolution, or result mutation occurred. Remain `B_STATIC_ONLY`; stop on any unknown/missing token or any `MISSING_EVIDENCE`/`pending`/`fail` value.
