# Round 26-R — Apply the same contract filter to the B-side, and price the unfreeze decision

## Purpose

Round 24-P generated Part B (B1–B35) under the assumption that the consumer freeze is lifted:
training, fine-tuning, new weights and upstream modification permitted, compute available.

**None of that is authorised.** The owner has relaxed only C6 (the contribution need not be a
method). The 800 GPU-hour tranche remains withdrawn, the consumer remains frozen, and the term is
mostly consumed.

So this round is **not** a plan. It is a **price list**: if the owner were to lift the freeze, what
would that buy, and at what cost? The owner needs this to make an informed decision, and cannot
make it on a list of candidate titles.

## The filter — same six fields as the A-side round

For each B-side candidate: **claim · estimand · stakeholder · minimal evidence contract ·
registry position (`object × time × claim type × stakeholder`) · kill condition.**

Apply it as strictly as to the A-side. **Do not assess occupancy** — a later round does that.

## Additionally, for every candidate you mark LIVE

**Price it honestly:**
- GPU-hours to a *decisive* result — not to a first plot, to a result that would survive review.
  Give a range and say what drives the spread.
- Data: does it need a held-out set the project does not have? Note that ScanNet++ v2 access has a
  **2–6 week application lead time requiring owner and supervisor signatures, not yet started.**
- Calendar: weeks of wall-clock, assuming one person.
- Which specific constraint must be lifted: training? fine-tuning? new weights? upstream
  modification? multiple consumers? Be precise — the owner may lift one and not others.

## Then

### Q1 — The B-side table, with prices
All candidates, with verdict and price. Mark clearly which are impossible this term **even if the
freeze were lifted today**.

### Q2 — The cheapest credible method contribution
Of everything in Part B, what is the single cheapest path to a defensible *method* result — the
thing the owner originally wanted? State its total cost and its earliest realistic completion.
**If the honest answer is that nothing in Part B completes this term, say that first and plainly.**

### Q3 — What one constraint, if lifted, unlocks the most?
Rank the constraints — training, fine-tuning, new weights, upstream modification, multi-consumer,
compute — by how much each unlocks per unit of what it costs the owner to grant. This is the
decision the owner actually faces, and it should be stated as a ranking, not a narrative.

### Q4 — The honest recommendation
If the owner asked you "should I lift the freeze?", what would you say, and what would you need to
know first? You may say "do not lift it" — that is an acceptable answer and I will record it.

## Constraints

- **No occupancy verdicts this round.**
- Do not assume any authorisation. Every price is conditional on an owner decision that has not
  been made.
- `new_method_validated=false`; `novelty_authorization=NONE`.
- Do not inflate or deflate costs to make a direction look attractive. If you cannot price
  something honestly, mark it `UNPRICED` and say why.

## Output
Write to exactly one new file: `work/agents/CODEX_R26R_CONTRACT_FILTER_B_20260920.md`.
**Do not create, modify, move or delete any other file.**
No GPU, training, weight download, or package installation.
