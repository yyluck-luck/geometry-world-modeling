# Round 27-S — Occupancy, on survivors only, against the claim triple

Read `work/agents/CODEX_R25Q_CONTRACT_FILTER_A_20260920.md`. It filtered 55 Part-A candidates
down to ten LIVE ones: **A4, A5, A6, A14, A22, A89, A90, A91, A92, A94**. Each has a written
claim, estimand, stakeholder, minimal evidence contract and kill condition. That round
deliberately did not assess prior art. This round does, and only for those ten.

## Why the previous twenty-three occupancy rounds were worthless

They asked "has anyone modified the retrieval selector / the memory write path / the camera
conditioning?" The answer to that is always yes, for every slot, so every round returned
"occupied" and nothing survived. That question is about a **mechanism slot**. It cannot
distinguish a field where everything is done from a field where nothing specific is done.

**Assess occupancy against the `claim + estimand + stakeholder` triple, not the mechanism.**
A paper that builds the same machinery but never measures the same quantity, or measures it
for a different decision-maker, does not occupy the claim. Conversely a paper with entirely
different machinery that already establishes the same claim on the same estimand *does*
occupy it, and I want to be told so plainly.

## Verdicts

- **OCCUPIED** — published work already establishes this claim on this estimand. Give the
  citation and the specific result. This kills the candidate; say so.
- **ADJACENT** — related work exists but the claim, the estimand, or the stakeholder differs.
  State the delta in one sentence, then answer separately: **is that delta something a
  reviewer would accept as a contribution, or is it a parameter change?** Be willing to say
  the delta is too small. Most "novel" work dies here and I would rather learn it now.
- **OPEN** — you looked and found nothing establishing this claim on this estimand. Say where
  you looked. "OPEN" from a shallow search is worse than useless, so state your search scope.

## Required per candidate

1. Verdict, with the claim triple restated in one line (do not make me re-derive it).
2. Citations: **arXiv ID or DOI, venue, year, and the specific claim/section relied on.**
   I will check every one. Two of your predecessors were caught citing real papers for
   results those papers do not contain, so cite the section, not just the paper.
3. If OCCUPIED or ADJACENT: **what is the residual?** Frequently a mechanism is published but
   the estimand my candidate names was never measured, or was measured only under a
   protocol that does not bind. If the residual is empty, say it is empty.
4. If OPEN: the single cheapest observation that would **falsify** the claim. Not confirm it.

## Search scope I expect

Top venues for world models, novel-view synthesis, video/scene generation, retrieval,
SLAM/3D reconstruction, and active perception, plus arXiv preprints. Selection-layer work is
often buried in ablation sections and in systems/robotics venues rather than in generation
papers; several survivors are selection-layer, so do not search generation venues alone.

## Constraints

- Frozen consumer, zero GPU, no training, no fine-tuning, no new weights, no upstream
  modification, no dataset downloads. This round is literature work; it changes no code.
- `new_method_validated=false`, `novelty_authorization=NONE`. Nothing you output changes them.
  **OPEN does not mean novel and does not mean authorized.** It means the search did not find
  an occupant; that is a statement about the search.
- Do not soften a verdict because a candidate is the only one left. If all ten are occupied,
  report all ten occupied — that is a real and useful result, and I will act on it.

## Q — after the table

1. Which survivors, if any, are OPEN with a non-empty falsification test runnable this week
   at zero GPU?
2. For the ADJACENT ones: is there a **combination** of two or more that is less occupied
   than either alone, or is that just stacking parameter changes? Be skeptical of yourself here.
3. Rank the surviving-after-occupancy set by *decision value per unit of evidence cost*.
4. If your honest answer is "nothing here is worth a paper", say that and say what the
   material is worth instead (an artifact, a negative result, a workshop note, nothing).

Write to exactly one new file: `work/agents/CODEX_R27S_OCCUPANCY_SURVIVORS_20260920.md`.
Do not modify any other file. Do not delete files you did not create.
