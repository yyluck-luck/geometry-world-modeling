# AGENTS and skill configuration audit (2026-09-16)

## Reference

OpenAI, “Rethinking skills and prompts for GPT-6 Astra,” 2026-09-11: <https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra>. The article recommends short trigger descriptions, progressive disclosure, contextual file reading, fewer mechanical itineraries, explicit completion criteria, and narrow permission boundaries.

## Findings

| Finding | Risk | Minimal action |
|---|---|---|
| Project `AGENTS.md` required reading the same three ledgers before every continuation, even a narrow follow-up. | Repeated context loading and unnecessary waiting. | Scope full reading to session start, resumption/compaction, or state change; narrow follow-ups read the current ledger plus relevant supporting file. Keep the full 20-minute heartbeat checklist because it is an explicit user requirement. **Applied.** |
| `AGENTS.md` still said remote GPU was unavailable as of 2026-09-05. | Direct contradiction after verified H800 jobs; agents could avoid an authorized path. | Replace with the current H800/SSH/Slurm boundary. **Applied.** |
| `RESEARCH_PRINCIPLES.md` contains many explicit scientific gates and seven heartbeat checks. | This is verbose, but these are user-requested data/GT/novelty safeguards rather than redundant skill triggers. Removing them would weaken scientific validity. | Keep; do not rewrite globally. Use the ledger and receipts instead of repeating prose in each task prompt. |
| `deep-research` asks for 3–5 perspectives and one agent per perspective. | It can exceed the available three child-agent slots if invoked for a small lookup. | Trigger only for survey-grade requests; for a narrow paper lookup use ordinary retrieval. No skill edit needed. |
| `idea-evaluator` and `tech-paper-template` are already scoped to idea evaluation and paper skeletons. | No material conflict detected. | No change. |
| `vibe-research-workflow` is a meta-router and points to supporting guidance. | Progressive disclosure is already present. | No change. |
| Automation prompt previously had stale “transfer partial” wording and a 10-minute cadence. | Wrong next action and duplicate polling. | Update heartbeat to 20 minutes and current S102/S103 state through the app automation tool. **Applied.** |

## Deliberately unchanged

- No “stop when uncertain” rule was added: bounded exploratory work remains allowed when it cannot affect formal scoring.
- No subjective “full-score” or repeated confirmation gate was added.
- No automatic task expansion or requirement to run every skill was added.
- Gate0, held-out isolation, same-budget controls, and novelty kill criteria remain because they protect the scientific claim rather than add ceremony.

## Verification

The modified `AGENTS.md` was read back after the patch. The active automation was updated to `RRULE:FREQ=MINUTELY;INTERVAL=20` and now names S102 job 588524 and the conditional Gate0 status. The change does not alter any experiment output or scientific conclusion.
