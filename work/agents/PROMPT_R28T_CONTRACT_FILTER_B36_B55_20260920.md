# Round 28-T — Contract filter for B36–B55 (closing a gap I left)

Round 26-R filtered Part B, but only B1–B35, because my prompt said B1–B35. R24-P actually
generated **55** Part-B candidates. R26-R flagged the boundary in its own output rather than
quietly ruling on candidates it was not asked about, which was correct. This round closes the
remaining twenty: **B36–B55**, in `work/agents/CODEX_R24P_GENERATION_20260920.md`.

Read `work/agents/CODEX_R26R_CONTRACT_FILTER_B_20260920.md` first and **match its format and
its severity**. Do not be more generous to B36–B55 than that round was to B1–B35 — these are
the tail of the same generation round and there is no reason to expect them to be stronger.

## Per candidate

| claim | estimand | stakeholder | minimal evidence contract incl. negative controls | registry position (object of change × time of intervention × claim type × stakeholder) | kill condition | verdict | price to a decisive result |

Verdicts: `LIVE` / `NO-CLAIM` / `NO-STAKEHOLDER` / `NOT-FALSIFIABLE` / `UNPRICED`.

Two fields do the killing, so do not let them go soft:

- **Estimand.** "Better consistency" is not an estimand. It must be something that could be
  the label on an axis, with an aggregation order fixed in advance.
- **Stakeholder.** Who changes a decision because of this result? If the honest answer is
  "nobody", write NO-STAKEHOLDER. R25-Q found 27 of 55 Part-A candidates were engineering
  actions wearing a claim's clothing; expect the same rate here.

## Pricing

Use R26-R's notation exactly (H, H+SN, T, F, W, U, MC, C and the S/M/L/XL planning bands) so
the two tables compose into one price list. Price to a **decisive** result — multi-seed,
held-out, ablations, failure reruns, independent recomputation — not to a first figure.
If a candidate's task/data/interface contract is still undefined, write **UNPRICED** and say
which contract is missing. An honest UNPRICED is worth more to me than a fabricated range.

Hold the same constraints R26-R verified: scene_13/14 are exposed development sequences and
do not qualify as held-out; ScanNet++ v2 needs owner + supervisor signatures and a 2–6 week
lead and **has not been started**; the 800 H800-hour tranche remains withdrawn; C6 relaxed
only "the contribution need not be a method" and relaxed no resource constraint.

## Q — after the table

1. Does any B36–B55 candidate beat **B21** (R26-R's cheapest credible path: ~200–800 H800-h,
   6–14 weeks, needs F/T + W + U + C)? If none does, say none does.
2. Does any of them need a **different** authorization bundle than B1–B35 did — i.e. does the
   tail of the generation round open a cheaper door, or the same door?
3. Does anything here change R26-R's recommendation not to lift the freeze yet?

No occupancy verdicts in this round. A later round does that, and only for survivors.
`new_method_validated=false`, `novelty_authorization=NONE`; LIVE is not authorization.

Write to exactly one new file: `work/agents/CODEX_R28T_CONTRACT_FILTER_B36_B55_20260920.md`.
Do not modify any other file. Do not delete files you did not create.
