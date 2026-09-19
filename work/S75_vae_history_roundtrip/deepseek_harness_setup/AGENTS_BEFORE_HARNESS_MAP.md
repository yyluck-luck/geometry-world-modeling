# Research continuity

Before continuing this project, read `RESEARCH_PRINCIPLES.md`, `RESEARCH_MEMORY.md`, and the latest entries of `RESEARCH_LOG.md`. The principles document records the user's continuing requirements; maintain it when the user revises those requirements.

The user is a beginner. Explain the question, action, finding, and next step in simple Chinese. Use concrete examples; define technical terms only when needed. User prefers autonomous progress on this local machine and has no remote GPU as of 2026-09-05.

Maintain local research memory during every work session:

- Keep `RESEARCH_MEMORY.md` as the short current-state summary, including constraints, verified findings, uncertainty, and next action.
- Append dated events through `scripts/research_log.py`. The canonical append-only record is `research_events.jsonl`; `RESEARCH_LOG.md` is its readable view. Include time in Asia/Shanghai, action, outcome, evidence paths, and next step.
- Log session starts, completed experiments, material failures/corrections, changes of direction, and session completion. Do not fabricate time spent or exact historical event times. Backfilled events must state their timestamp source and actual recording time.
- Preserve old results and protocols. Record exploratory follow-ups separately from pre-run plans. Record negative results as clearly as positive results.
- Every experimental conclusion must link to actual outputs. Keep synthetic, source-code, real-data, and end-to-end evidence distinct. Changed retrieval does not by itself mean worse retrieval or worse generated video.

The project uses HKUSTDial/Supervisor-Skills. Relevant skills and pinned upstream code are documented in `docs/RESEARCH_STATUS.md` and `vendor/provenance.json`. Do not overwrite original proposal/drafts while doing experiments. No messages to the advisor or others are authorized.
