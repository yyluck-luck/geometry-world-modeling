# Repair window manifest — full 14-window accounting (2026-09-18)

Built from receipts, not from memory: census job 595614, sealed job 594957, in-place job 595902,
refill job 595891. `new_method_validated=false`, `novelty_authorization=NONE`.

## Why this file exists

An external review noted that the census reported **10** duplication-affected windows while the
repair result covered **8**, and that "no-op gate 8/8" did not state its units. Both are resolved
here from the receipts. No generation was run to make the accounting tidier, and the denominator
was not silently redefined.

## The manifest

| scene | window | shipped context (sealed) | distinct | repair status | repaired context |
|---|---|---|---|---|---|
| scene_13 | w050 | [105, 105, 100, 95] | 3 | REPAIRED | [105, **90**, 100, 95] |
| scene_13 | w100 | [140, 155, 145, 150] | 4 | NO-OP CONTROL | unchanged |
| scene_13 | w150 | [150, 205, 155, 160] | 4 | NO-OP CONTROL | unchanged |
| scene_13 | w200 | [255, 255, 250, 245] | 3 | **EXCLUDED** — no replacement candidate exists | — |
| scene_13 | w250 | [305, 305, 300, 295] | 3 | REPAIRED | [305, **290**, 300, 295] |
| scene_13 | w300 | [355, 355, 350, 345] | 3 | REPAIRED | [355, **340**, 350, 345] |
| scene_13 | w350 | [405, 405, 400, 395] | 3 | REPAIRED | [405, **390**, 400, 395] |
| scene_14 | w050 | [105, 105, 100, 95] | 3 | REPAIRED | [105, **90**, 100, 95] |
| scene_14 | w100 | [155, 155, 150, 145] | 3 | **EXCLUDED** — no replacement candidate exists | — |
| scene_14 | w150 | [170, 205, 165, 160] | 4 | NO-OP CONTROL | unchanged |
| scene_14 | w200 | [220, 255, 215, 210] | 4 | NO-OP CONTROL | unchanged |
| scene_14 | w250 | [305, 305, 300, 295] | 3 | REPAIRED | [305, **290**, 300, 295] |
| scene_14 | w300 | [355, 355, 350, 345] | 3 | REPAIRED | [355, **340**, 350, 345] |
| scene_14 | w350 | [405, 405, 400, 395] | 3 | REPAIRED | [405, **390**, 400, 395] |

```
14 windows with both sealed endpoints
 =  4 already delivering four distinct frames   (no-op internal controls)
 + 10 with a duplicated slot                    (duplication-affected)
      =  8 repaired and scored
      +  2 excluded: the pipeline's entire ranked candidate list holds only
           three distinct frames, so no replacement candidate exists at all
```

## Eligibility rule and when it was fixed

Eligibility is "a duplicate exists **and** the pipeline's own ranked candidate list contains a
frame not already selected." The two exclusions are structural: the selector has nothing to put in
the freed slot. They are refusals recorded by the run itself
(`status: INSUFFICIENT_DISTINCT_CANDIDATES`), not post-hoc drops.

The counts 8 / 4 / 2 were written into `REPAIR_SPEC_PREDECLARED_20260918.md` **before any repair
output was scored**, derived from the metadata of the earlier refill run (job 595891). No PSNR
informed the eligibility rule.

## Correct statement of the result

> The in-place duplicate-slot replacement changed PSNR by **−0.016 dB in mean across the 8 of 10
> duplication-affected windows for which a replacement candidate exists** (SD 0.309, 3 of 8
> positive). Two affected windows could not be tested because the selector offers no replacement
> candidate. The predeclared retention threshold was +0.20 dB; the explanation is discarded.

This is **not** "a completed test across all ten affected windows."

## Units of the byte-identity gates

- **No-op gate: 8 window-seed executions** = 4 no-op windows x 2 seeds. All 8 byte-identical to the
  sealed shipped output.
- **NULL gate (leak comparison, separate experiment): 4 window-seed executions** = 2 NULL windows
  x 2 seeds. All 4 byte-identical.

Each gate certifies exactly the cases it covers and nothing beyond them.

## The two "8"s are different sets

The repair covers 8 windows; the leak census CONTENT stratum also has 8 windows. **They are not the
same 8** and must never be conflated:

- repaired: scene_13 w050, w250, w300, w350; scene_14 w050, w250, w300, w350
- CONTENT: scene_13 w050, w100, w250, w350; scene_14 w050, w200, w250, w350

They differ in four entries. Repair eligibility comes from the duplication intervention; the
CONTENT stratum comes from the separate leak comparison.
