# Round 14-D — Can the cross-system breadth gap be closed with ZERO GPU?

This is a **feasibility survey**, not a novelty review. Do not rank research directions, do not
issue a funding verdict.

## Why this question decides everything

A precedent study concluded that the three properties separating published diagnostic work from
an unpublished technical report are: **conclusion impact**, **cross-system external validity**,
and **an adoptable audit artifact**. This project has one system. Adding a second (and third)
released system is therefore the load-bearing gap.

**The decisive question is whether that gap can be closed by static source analysis alone** —
reading released repositories — rather than by running generation. If yes, the cost is near zero
and the project is executable in the remaining term. If no, it needs GPU time that is currently
unauthorised and a term that is mostly gone.

## The audit predicate (pre-specified; do not modify it to fit what you find)

A repository exhibits the defect class if **all five** hold:
1. an instance attribute is written on one branch or call path;
2. it is read on a different path whose own write is conditionally guarded and may not fire;
3. the documented `reset()` / `initialize()` / new-session path does not clear it;
4. the triggering mixed call sequence is reachable from the documented public API or shipped demo;
5. the behavioural difference would be measurable on frozen weights.

Conditions 1–4 are **statically checkable**. Condition 5 requires running the model.
**Report 1–4 and 5 separately. Do not claim 5 for any system you did not run.**

Our reference instance, already verified: VMem (`runjiali-rl/vmem`, public HEAD
`39291e4f272f6b4f270691d930926ab5930f942e`, `modeling/pipeline.py` SHA-256 `90a45f45...`):
`initial_threshold` written unconditionally at `pipeline.py:704-705` on the NMS-disabled path;
the NMS-enabled path writes only when `is_second_step = len(self.pil_frames) == 5` (`:674`);
read unconditionally at `:708`; `reset()` (`:135-147`) does not clear it; not initialised in
`__init__`; reachable from `app.py` GUI as move, move, turn.

## Questions

### Q1 — The candidate population
List released, public-code, stateful video / world-model / long-video-memory systems that are
plausible audit targets. For each: repository URL, arXiv ID and exact title, whether the code is
actually public and complete, and whether it maintains cross-call instance state with a
reset/initialize path. Include at minimum, and verify rather than assume: WorldMem, GEN3C,
Matrix-Game / Matrix-Game 2.0, Cosmos world models, Self-Forcing, LongLive, StreamingT2V,
FramePack, Voyager, FantasyWorld. Add any others you find.

**Exclude, with a reason stated, any system whose code is not public or which is stateless across
calls.** A short honest list beats a long speculative one.

### Q2 — Apply conditions 1–4 statically, to as many as you can
For each system you can actually inspect: give file path, line numbers, the commit SHA you read,
and a verdict per condition. Report three outcomes: **HIT** (1–4 all hold), **NEAR** (some hold,
say which fail), **CLEAN** (state handling is complete — this is a real and reportable result).

**Do not fabricate line numbers. If you cannot fetch a repository, say so and mark it
NOT-INSPECTED rather than guessing.** A survey with 4 inspected systems and honest gaps is worth
more than 10 systems of speculation.

### Q3 — The honest count
How many independent systems could realistically be audited to conditions 1–4 within about two
weeks of one person's work, with no GPU? State the number and what limits it.

### Q4 — What condition 5 would cost
For the HIT systems only: what would it take to demonstrate a measured behavioural consequence —
model weights availability, licence, VRAM, approximate GPU-hours per system to a decisive result.
Note whether any HIT system can be run at all on a single node.

### Q5 — The verdict on feasibility
Can the cross-system breadth gap be closed with zero GPU (conditions 1–4 only), or does a
credible contribution require condition 5 on at least some systems? State plainly which. If your
finding is that a static-only survey would be dismissed by reviewers as insufficient, say that.

## Output
Write to exactly one new file: `work/agents/CODEX_R14D_SECOND_CONSUMER_FEASIBILITY_20260919.md`.
Do not modify any existing file. No GPU, no training, no generation, no model downloads.
Every code claim: repository, commit SHA, path, line numbers. Every paper: arXiv ID and exact
title. Mark anything unverified as UNVERIFIED.
