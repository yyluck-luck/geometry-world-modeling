# Round 25-Q — Apply the contract filter to the A-side candidates. Do NOT assess occupancy.

## Why this round exists, and why its order matters

Round 24-P diagnosed a process error that ran for twenty-three rounds: I searched by asking
*"which internal slot is still empty?"* and filtered by occupancy **first**. Its prescription was
explicit:

> **先固定 `claim + estimand + stakeholder + minimal evidence contract`,再从 Part A/B 里选一个
> 可证伪机制。** ... **它避免把"没有找到第九个槽位"误当成"没有研究问题"。**

So this round applies that filter, and **occupancy is deliberately deferred to a later round.**
If you spend this round telling me candidates are taken, the round is wasted and I will rerun it.
A candidate that cannot state a claim, an estimand, a stakeholder and a decisive evidence contract
**should die here, before any literature search is spent on it.**

## Subject

`work/agents/CODEX_R24P_GENERATION_20260920.md`, **Part A only** (A1–A25 plus the supplementary
A-series in 补充生成分支). These are the candidates that are executable under the current hard
limits: consumer frozen (no training, no fine-tuning, no new weights, no upstream modification),
**zero GPU authorised**, term mostly consumed.

Part B is out of scope for this round — a separate round covers it.

## The filter — apply to every A-side candidate

For each, produce:

1. **Claim** — one sentence a reviewer would have to accept as new. If you cannot write one
   without hedging, mark the candidate `NO-CLAIM` and move on. That is a valid and useful outcome.
2. **Estimand** — the exact quantity: what is compared, on what population, under what aggregation,
   with what controls. "Better consistency" is not an estimand. State it as something that could be
   written on an axis label.
3. **Stakeholder** — *who changes a decision because of the result?* Model authors, deployers,
   evaluators, downstream agents, the owner's supervisor? If the honest answer is "nobody", say so.
4. **Minimal evidence contract** — the cheapest evidence that would decide the claim either way,
   including its negative controls. State whether it is achievable at **zero GPU** on a frozen
   consumer, and if not, say what it needs.
5. **Registry position** — place it on the multi-layer map Round 24-P prescribed:
   `object of change × time of intervention × claim type × stakeholder`.
   A candidate may occupy several cells; do not force a single slot.
6. **Kill condition** — the single observation that would end it. If none exists, it is not
   falsifiable and should be marked as such.

## Then

### Q1 — The survivor table
Every A-side candidate, one row, with the six fields compressed. Mark each `LIVE`, `NO-CLAIM`,
`NO-STAKEHOLDER`, `NOT-FALSIFIABLE`, or `NEEDS-RESOURCES`. **I expect most to die. That is the
point of a filter.** A round that marks everything LIVE has not filtered.

### Q2 — The top five, ranked by decision value per unit cost
Not by elegance, not by novelty — by *how much a real decision changes* divided by *what it costs
to find out*. For each of the five, write the claim and the evidence contract in full.

### Q3 — The common failure mode
Across the candidates that died, what did they have in common? This tells me whether the
generation round itself was biased in a direction I should correct next time.

### Q4 — Is any survivor executable *this week* at zero GPU?
Name it, and state exactly what the first artefact would be. If none is, say so plainly — the
honest answer may be that every A-side candidate needs resources the project does not have.

## Constraints on your answer

- **No occupancy verdicts.** Not "this is taken", not "prior art exists". A later round does that.
- `new_method_validated=false`; `novelty_authorization=NONE`; the 800 GPU-hour tranche remains
  withdrawn; outbound messages remain forbidden. Your answer changes none of these.
- Do not rescue a candidate by weakening its claim until it is unfalsifiable.
- **I would rather end this round with two live candidates than twenty hedged ones.**

## Output
Write to exactly one new file: `work/agents/CODEX_R25Q_CONTRACT_FILTER_A_20260920.md`.
**Do not create, modify, move or delete any other file** — two earlier rounds destroyed
uncommitted work by doing so.
No GPU, training, weight download, or package installation.
