# R125 owner-packet acceptance matrix

**Date:** 2026-09-24 (Asia/Shanghai)  
**Scope:** read-only acceptance-matrix audit of the future owner packet. No
runner or fixture execution, command discovery, protected C8/evaluation read,
GPU/Slurm work, receipt mutation, or validation-flag change occurred.

## Verdict: PASS (matrix); packet remains `NO_COMMAND_AVAILABLE`

The current owner-facing records describe one complete synthetic-only packet,
one gate order, and explicit replay/substitution rejection statuses. The matrix
is internally consistent. This PASS audits the acceptance contract only; it
does not assert that the packet exists, authorize a command, reopen END-LINE,
or validate a method.

## Acceptance matrix

| Requirement | Accept only when | Reject / terminal status | Evidence |
|---|---|---|---|
| Local/remote knowledge boundary | The packet is supplied for a fresh audit. Remote files are treated as evidence only after role, path, SHA, owner, H2, and snapshot checks. | Local absence keeps `NO_COMMAND_AVAILABLE`; SSH timeout or stale remote state is not readiness. | `work/agents/CODEX_R120_FINAL_OWNER_PACKET_STATUS_20260924.md:8-20,22-48`; `work/agents/CODEX_R121_REMOTE_STALE_BOUNDARY_AUDIT_20260924.md:14-21,30-43` |
| Immutable snapshot | A post-rename read-only root is reopened with `O_NOFOLLOW`; fresh nonce, `local:<nonce>:<final_manifest_sha256>`, role/path/inode/link checks, and a full digest pass immediately before readiness all match. | Any root, nonce, inode/link, role/path, file hash, or digest change returns `STALE`/`REMOTE_PROVENANCE_UNVERIFIED` before owner/H2 access. | `work/agents/CODEX_R114_OWNER_ACTION_CHECKLIST_20260924.md:22-24,50-60`; `work/agents/CODEX_R111_OWNER_GATE_FINAL_AUDIT_20260924.md:53-71` |
| Owner review gate | One artifact has `OWNER_ACCEPTED`, the R70 protocol/manifest chain, synthetic-only decision scope, UTC decision time, independent reviewer role, and is bound to the final snapshot. | Missing, stale, replayed, substituted, or semantically mismatched valid owner artifact returns `OWNER_REVIEW_REQUIRED` before materialization/H2. | `work/agents/CODEX_R109_DCR_READINESS_AUDIT_20260924.md:7-15,17-31`; `work/agents/CODEX_R110_OWNER_GATE_SUBSTITUTION_AUDIT_20260924.md:64-77`; `work/agents/CODEX_R114_OWNER_ACTION_CHECKLIST_20260924.md:25-28,56-59` |
| Canonical owner hash | There is exactly one lowercase 64-hex `/owner_gate/review_artifact_sha256`; verifier removes exactly that pointer and recomputes `canonical_json_v2` over the remaining review artifact. | Duplicate, alias, marker, second subject, filtered projection, or mismatch is rejected before H2 (`REJECT_FIXTURE` for malformed input; `OWNER_REVIEW_REQUIRED` for a well-formed but mismatched/replayed artifact). | `work/agents/CODEX_R111_OWNER_GATE_FINAL_AUDIT_20260924.md:24-44,61-71`; `work/agents/CODEX_R112_CANONICAL_OWNER_HASH_CLOSURE_20260924.md:26-43,45-58`; `work/agents/CODEX_R114_OWNER_ACTION_CHECKLIST_20260924.md:29-31,56-59,63-67` |
| Manifest identity and role binding | The R85 `manifest_identity` has exactly seven fields, fixed schemas/roles/paths, independently recomputed code/H2/boundary hashes, and `runner_code_manifest_sha256 != h2_source_manifest_sha256`. | Role/path substitution, copied boundary/H2/code bytes, or chain-name-only identity is rejected before materialization/score (`REJECT_FIXTURE` or `OWNER_REVIEW_REQUIRED` per syntax versus valid-but-mismatched artifact). | `work/agents/CODEX_R110_OWNER_GATE_SUBSTITUTION_AUDIT_20260924.md:37-43,51-69,71-82`; `work/agents/CODEX_R111_OWNER_GATE_FINAL_AUDIT_20260924.md:46-51` |
| Typed H2/source boundary | `h2_source_manifest`, `h2_packet`, and `boundary_artifact` contain the typed frame/pose fields, exact formulas, source/boundary hashes, finite measured bidirectional identity error `<=1e-6`, and `status=PASS`. | Missing, marker-valued, conflicting, or error-failing H2 returns `H2_UNIDENTIFIABLE` before H2-dependent hashes/scores. | `work/agents/CODEX_R108_DCR_ACCEPTANCE_AUDIT_20260924.md:17-36,38-47`; `work/agents/CODEX_R114_OWNER_ACTION_CHECKLIST_20260924.md:35-38,56-60` |
| Synthetic fixture and controls | The sealed metric plane/cube has explicit cameras, intrinsics, depth units, crop/rounding, independent calibration/held-out scale, camera-keyed computed visibility, all R62/S131 arms and denominators, and target data sealed until commits. | Ambiguity/leakage gives `REJECT_FIXTURE`; zero denominator gives `UNTESTABLE_NO_DENOMINATOR`; an access-matched control reproducing the full CGLR signature gives `REJECT_NON_IDENTIFIABLE` and keeps END-LINE. | `work/agents/CODEX_R113_ENDLINE_CHALLENGE_20260924.md:38-49,51-69`; `work/agents/CODEX_R114_OWNER_ACTION_CHECKLIST_20260924.md:39-45,60-61` |
| Runner and command boundary | A source-pinned CPU-only runner and command text/discovery evidence are supplied for review only after the complete packet and gates are independently accepted. | Before acceptance, do not execute, dispatch, schedule, or expose the command as runnable; a partial packet remains `NO_COMMAND_AVAILABLE`. | `work/agents/CODEX_R114_OWNER_ACTION_CHECKLIST_20260924.md:17-20,43-48,69-80`; `work/agents/CODEX_R120_FINAL_OWNER_PACKET_STATUS_20260924.md:33-48` |
| Scientific state boundary | Even a future synthetic benchmark pass is recorded as benchmark evidence only; method novelty requires the matched-control improvement and independent prior-art comparison. | Keep `NO_REOPEN`, END-LINE, `new_method_validated=false`, and `novelty_authorization=NONE`; no GPU or method-language revision follows this audit. | `work/agents/CODEX_R113_ENDLINE_CHALLENGE_20260924.md:71-77`; `work/agents/CODEX_R114_OWNER_ACTION_CHECKLIST_20260924.md:69-80` |

## One replay/substitution-resistant acceptance invariant

**Accept the owner packet only if all of the following are recomputed from the
same fresh R98 frozen snapshot immediately before readiness:**

```text
supplied = review_artifact["owner_gate"]["review_artifact_sha256"]
subject = canonical_json_v2(
    review_artifact with exactly
    /owner_gate/review_artifact_sha256 removed)
require supplied == SHA256(subject)
require frozen_snapshot_id == local:<fresh_sync_nonce>:<final_manifest_sha256>
require snapshot_final_digest == recomputed_digest
require all R85 role-bound code/H2/boundary hashes match that snapshot
require runner_code_manifest_sha256 != h2_source_manifest_sha256
```

If any final-root, nonce, inode/link, role/path, file-hash, or digest check
changes, return `STALE`/`REMOTE_PROVENANCE_UNVERIFIED`; if the snapshot is
stable but the single owner subject, role tuple, or chain does not match,
return `OWNER_REVIEW_REQUIRED` before materialization or H2 access. This one
conjunctive invariant blocks replay of an old `OWNER_ACCEPTED` artifact and
substitution of a different code/H2/boundary root. It follows the canonical
single-hash rule and final-snapshot precedence in R110--R112 and R114.

Evidence: `work/agents/CODEX_R110_OWNER_GATE_SUBSTITUTION_AUDIT_20260924.md:44-77`;
`work/agents/CODEX_R111_OWNER_GATE_FINAL_AUDIT_20260924.md:53-71`;
`work/agents/CODEX_R112_CANONICAL_OWNER_HASH_CLOSURE_20260924.md:26-43`;
`work/agents/CODEX_R114_OWNER_ACTION_CHECKLIST_20260924.md:50-67`.

## Current blocker and stop rule

The matrix PASS does not mean the owner packet is present. R120's exact local
role-bound files and runner were absent, and the remote probe was stale/
unverified. Until a complete packet arrives and a fresh readiness audit passes,
keep `NO_COMMAND_AVAILABLE`, `NO_REOPEN`, END-LINE,
`new_method_validated=false`, and `novelty_authorization=NONE`. Do not expose,
execute, dispatch, or schedule a command; do not access protected data or
submit GPU/Slurm work.

**R125 status: PASS / acceptance matrix closed / packet not supplied / NO
EXECUTION.**
