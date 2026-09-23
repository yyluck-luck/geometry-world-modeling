# Round 32 — Repository-level re-review of three GPT-6 Pro rounds

Three review rounds (R29-P1, R30-P2, R31-P3, all dated 2026-09-21 in RESEARCH_MEMORY.md) were run on GPT-6 Pro through the ChatGPT app. **Pro could not read this repository.** Every repository fact it used was my paraphrase. The ledger marks all three as "no codex repository-level review". You are that review.

## Task 1 — check every repository fact those rounds relied on
For each of R29-P1, R30-P2, R31-P3, list every claim about this repository, the pinned VMem source, a measured number, or a job, and mark it VERIFIED / WRONG / UNVERIFIABLE with file:line. Include the numbers I fed in: +0.242 dB, -0.726 dB, -0.016 dB vs +0.20 dB, 5.6 dB, 0.55 dB, "1 of 12 bank frames visible", replay byte-identical across dgx-21/dgx-09, N=20 audit tallies, 4.4e-16.

## Task 2 — the most important check: was Delta_leak actually measured?
R31-P3 concluded: we measured Delta_setting = Y(NMS-on, clean) - Y(NMS-off) = -0.726 dB, but never Delta_leak = Y(NMS-on, inherited state) - Y(NMS-on, valid state), so the claim "the leak costs performance" is unsupported.

But docs/RETRIEVAL_ARMS_RESULT_20260918.md reports a fourth row: `memory_nms_on_clean - memory_nms_on (leaked)` = +0.245 dB, SD 0.711, 6/14 windows. Determine precisely:
- What the leaked arm's state history was (which job, what preceded it, what value initial_threshold held when read).
- Whether that inherited state is the SAME state the native demo produces in the move, move, turn sequence, or an artificial one.
- Whether everything else was held equal between the leaked and clean arms (same windows, seeds, bank, candidate pool).
- Therefore: is -0.245 dB a legitimate finite-panel estimate of Delta_leak? If yes, R31-P3's central retraction is itself partly wrong. If no, say exactly which condition fails.
Also check how the ledger and the technical report describe this row, and whether the "-0.729 dB withdrawn" figure relates to it.

## Task 3 — the "zero replay envelope" claim
R31-P3 argued a wrong experiment can execute deterministically, so byte-identical replay proves nothing about experimental semantics. Check what the replay actually covered (which job, which arm, which inputs). State the exact scope that "replay envelope = 0" can honestly claim.

## Task 4 — the "0/20 measured under frozen weights" ambiguity
Find the original N=20 audit record. State which meaning it had: (a) no system ever ran a frozen forward, or (b) no system had a defect-specific downstream causal measurement.

## Output
Write to exactly one new file: work/agents/CODEX_R32_REPO_REREVIEW_OF_PRO_20260922.md. End with a short list: which conclusions of R29/R30/R31 STAND, which are OVERTURNED, which are NARROWED.
