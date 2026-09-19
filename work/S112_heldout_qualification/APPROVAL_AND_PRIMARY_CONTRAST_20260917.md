# Execution approval and prospective declaration of the primary contrast

**Recorded before any contact with the fr1_room sequence.**

## Approval

The project owner instructed execution of the revisit diagnostic on
2026-09-17, after reviewing `LAUNCH_READINESS_20260917.md`.

Scope, unchanged from the readiness document:

> Single sequence (TUM `rgbd_dataset_freiburg1_room`), frozen four arms,
> revisit context-selection and native-retrieval diagnostic.
> This is not a complete VMem memory-system validation, does not lift other
> gates, and creates no method or novelty authorization.

`new_method_validated=false`; `novelty_authorization=NONE`.

## Prospective resolution of the undefined primary contrast

The frozen protocol names "the memory arm" but declares two of them. This is
resolved here, **before any window is built and before any data is read**, so it
cannot be chosen after seeing outcomes:

- **PRIMARY contrast:** `memory_nms_on` minus `recency`.
  Rationale: NMS-on is VMem's shipped default configuration, so it is the
  setting a reader would assume, and it was already the stricter of the two in
  earlier development runs.
- **Pre-declared SECONDARY arms, all reported regardless of outcome:**
  `memory_nms_off` minus `recency`, and `early_visit` minus `recency`.

No arm may be promoted to primary after scoring. All four arms are reported.

## Declared interaction quantity

```
d(window, seed)  = primary_score(arm) - primary_score(recency)
interaction      = aggregate(d | revisit) - aggregate(d | non_revisit)
```

Aggregation follows the amendment: the two seeds of a window are averaged first,
the window is the analysis unit, and the standard error is computed from
window-level values with the revisit and control groups treated separately.

## Declared stopping rules, unchanged

- Fewer than three independent revisit episodes -> `UNTESTABLE`, budget not spent
- Failing the preregistered positive interaction -> stop pursuing the
  missing-revisit explanation; this is **not** proof of universal falsity and
  **not** evidence of equivalence
- Guard failure -> retain the score and the full denominator, withhold only the
  geometric interpretation
- No window replacement, no threshold change, no seed substitution, no rescue
  sequence after an unfavourable result
