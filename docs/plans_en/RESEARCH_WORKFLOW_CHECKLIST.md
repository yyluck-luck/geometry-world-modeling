# Research Workflow Check Every 30 Minutes

> Source: `docs/RESEARCH_WORKFLOW_CHECKLIST.md`  
> Source SHA-256: `44903c6f49711b4e59cb926044c224fc7b273185ebed124ac5ab9c0f7f3be6ca`

The user explicitly requested on 2026-09-06 that every 30 minutes we check adherence to skills, innovation progress, recording, local tools and web retrieval, and continue the research. This file gives scheduled continuation in the current chat a stable procedure; the schedule frequency is managed by the in-app scheduler, not by this file.

## First restore the real state each time

Read the project AGENTS, RESEARCH_MEMORY, latest RESEARCH_LOG, and check existing model/experiment/download processes and unfinished agents. Do not rerun a successful experiment based on an old handoff snapshot. The master ledger is in this project; user materials are in the current workspace outputs. If the previous run stopped because of a service error, first check whether artifacts were saved, then continue the unfinished work; do not call the interruption an experiment failure.

## Seven checks, each requiring concrete evidence or a reason for not applying

| Check | Facts to verify | Handling when it does not pass |
|---|---|---|
| Skills actually executed | Which Supervisor skills were selected at this stage, which SKILL/reference files were read, what steps were executed, and what artifacts correspond; whether the local Claude skill applies | Read applicable material and fill missing gates; state the local scope and unexecuted items. Do not use irrelevant skills for the sake of quantity or treat reading as completion. |
| Innovation and falsification | What the hypothesis is, what is new relative to the closest original work, what could falsify it, and whether it is confirmed, pending validation, or rejected | Use targeted retrieval of original papers to find counterexamples; if same-information/same-supervision/same-capacity baselines are insufficient, first complete the protocol. Without novelty evidence, keep it pending and do not promise a teacher’s reaction. |
| Experiment authenticity | Whether input domain, primary settings/sensitivities, candidate/output/compute budgets, GT isolation, pre-run freeze, failure retention, and independent review were actually completed | Record deviations and correct the later workflow; do not rewrite old freezes, delete failures, or present related conditions as independent samples. |
| Local tool use | Whether concrete local scripts, rg, Python environments, numerical recomputation, LaTeX/Draw.io/plotting, etc. leave checkable artifacts, and whether the tool fits the question | Reuse existing dependencies/weights first; invoke tools when there is a clear need, without opening graphical apps or repeating models every round. |
| Web retrieval | Whether novelty, near-neighbor methods, and time-varying dependencies have original-paper URLs/versions/access records, and which questions still lack sources | When new facts are needed, check authoritative originals and save queries/evidence; when no new retrieval is needed, record not applicable and why rather than repeating mechanically. |
| Multi-agent and audit | Whether substantive independent sub-tasks were delegated when parallel work was possible; whether implementation and numerical/document review roles are clear; whether process errors were recorded | Parallelize after boundaries are clear; retain artifacts after service failure and continue reasonably. Do not call same-author self-check an independent audit. |
| Memory and delivery | Whether each start/completion/failure/correction/redirect has actual occurrence and recording times, action, result, evidence, and next step; whether main memory agrees with latest outputs | Append through `scripts/research_log.py`; for historical backfills state the time source. Synchronize handoff and user snapshots; do not treat elapsed time as student hours. |

Use `PASS`, `ACTION_REQUIRED`, or `NOT_APPLICABLE` for each item, with evidence paths and the basis for judgment. An innovation candidate awaiting validation is not a workflow failure; presenting it as established is the problem. An independent audit in progress is not the same as no audit; record its actual progress.

## Recording and continuing

Append one entry to `workflow_checks.jsonl` each round: actual UTC and Beijing time, check interval, seven statuses/evidence, findings, corrections made, and next step. Also use `scripts/research_log.py` to record the round’s conclusion and substantive action; keep only current progress and pending work in RESEARCH_MEMORY. Normal checks are recorded locally too, while whether to notify the user follows this task’s reminder preference.

After the check, perform the most important locally feasible next step instead of merely generating more check reports. New experiments follow independent reading, freeze, execution, review, explanation, and delivery. Explorations whose results have already been seen must be labeled explicitly. Failure or a negative result can also be valid research progress.

Preserve authorization boundaries: autonomous local reading/writing, experiment preparation, retrieval, and research reports are allowed; do not send advisor messages, fabricate meetings/hours, request model access requiring personal information, or call the Claude model (only use its local skills). Full videos, course submission, and advisor evaluation are accepted only on real evidence.
