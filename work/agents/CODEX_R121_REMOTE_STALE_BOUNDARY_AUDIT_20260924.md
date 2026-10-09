# R121 remote-stale boundary audit

Date: 2026-09-24 (Asia/Shanghai)  
Scope: read-only verification of R120's local/remote readiness boundary. No
implementation, fixture execution, GPU/Slurm job, protected C8/evaluation
read, receipt update, or flag change.

## Verdict: PASS

R120 correctly separates the three relevant states:

1. **Absent:** local exact checks find all six owner/H2/fixture files and the
   dedicated runner absent. This is the operative state and returns
   `NO_COMMAND_AVAILABLE` (`work/agents/CODEX_R120_FINAL_OWNER_PACKET_STATUS_20260924.md:8-20`).
2. **Remote stale/unverified:** the fresh SSH probe timed out during banner
   exchange. R120 explicitly treats the remote state as stale/unverified and
   does not infer readiness from the timeout (`...R120...:22-31`). The older
   R93/R100 remote listings are historical knowledge only, not a substitute for
   a current attestation.
3. **Present-but-unverified:** any future file is not accepted merely because
   it exists. R120 requires role/path, SHA, owner-hash, H2 bidirectional, and
   immutable-snapshot checks before readiness (`...R120...:46-48`). This agrees
   with R93's distinction between design records and executable owner/H2 roles
   (`work/agents/CODEX_R93_OWNER_H2_CHECKLIST_VERIFICATION_20260924.md:17-20,36-51`).

No remote timeout is treated as `OWNER_ACCEPTED`, H2 pass, command availability,
or execution permission. The local absence is sufficient to keep the gate
closed even if the remote host cannot be contacted.

## Exact owner action and stop condition

The owner must supply one complete, independently reviewed, content-addressed
synthetic-only packet: source-pinned runner/code manifest, canonical fixture,
measured H2 source/packet/boundary artifacts, R85/R89 owner review artifact,
R98 frozen snapshot identity/digest, and review-only command text/discovery
evidence. Until all gates pass, retain `NO_COMMAND_AVAILABLE`, `NO_REOPEN`,
END-LINE, `new_method_validated=false`, and `novelty_authorization=NONE`.

The SSH timeout changes only the remote knowledge label to stale/unverified; it
does not create a retry authorization, expose a command, or permit CPU/GPU/
Slurm/C8/evaluation work.

**R121 status: PASS / absent-vs-stale-vs-present-unverified boundary closed /
NO_EXECUTION.**
