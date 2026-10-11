# Brief R267 — DECISION/REJECTION: how should S146 proceed now that VMem's memory geometry fails on the fresh rooms? (2026-10-11)

Read work/S146_fresh12/PROTOCOL.md (with Amendments 1-2), your R265 (binding spec) and R266 (KPS-R rejection:
work/agents/CODEX_R266_KPSR_REJECTION.md), and the new bank-only diagnostic work/S146_fresh12/diag/KPS_DIAG_{0,1,2}.json
(produced by diag_kps_s146.py with the ORIGINAL KPS + per-view logging, kps_diag.py). No step-A retrieval, generation or
target scoring has run for S146. Summary of the diagnostic (verify in the files): for step A's construction sizes
(5, 20, 32 bank frames, star rooted at bank[0]): apt1/kitchen fine at 5 and 20 (all views finite, 100% positive depth),
32-frame objective infinite in 2/8 windows; apt2/luke residual 112-160 px at all sizes and one view with only ~53%
positive depth from 20 frames on; office2/5a objective infinite at 20 and 32 frames in all 8 windows, a view with ~61%
positive depth. Chess (S139/S143) had 96/96 finite calls. The H20 history spans the whole sequence0 of each room.

The scientific aim of S146 is a project-fresh test of the S143 finding "nearest-4 beats VMem's own retrieval for VMem's
generator" (S143 fresh seeds: +0.74 dB). Decide, with reasons, among (and attack each):
(a) keep the frozen design and R265/R266 strict geometry gates -> most windows INELIGIBLE for mem_vmem -> report
    INVALID_ASSAY for the primary plus the diagnostic as a finding about VMem's memory on multi-area banks;
(b) treat VMem's retrieval as a black-box deployed policy: run step A with the R266-corrected KPS-R-fixed-support-v1
    (or the original KPS), no geometric validity gate on VMem's internals, record all diagnostics; the comparison is between
    the four frame ids each policy outputs (always valid bank frames); is this scientifically legitimate and how must the
    claim be worded?
(c) a pre-generation redesign of the banks/windows so banks are co-visible (e.g. history frames restricted by a pose-only
    rule), or other rooms — without biasing toward nearest-4 — and what that does to freshness and comparability;
(d) anything better (e.g. replace mem_vmem by mem_pose as the primary comparator; run both (a) diagnostics and (b)).
Give ONE recommended path with the exact protocol amendment text, gates and claim wording, and the minimal code changes.
Output: write exactly one file, work/agents/CODEX_R267_S146_PATH_DECISION.md. I prefer a correct negative to an encouraging
answer.
