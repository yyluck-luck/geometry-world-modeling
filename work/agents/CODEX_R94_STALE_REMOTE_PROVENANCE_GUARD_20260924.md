# R94 stale-remote provenance guard

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design/read-only audit. No sync command, runner, fixture, owner/H2
artifact, real C8 input, replay, GPU/Slurm job, receipt, or validation flag was
created or modified.

## Finding

R93 observed a real evidence split: the local root had the current R70/R89/R92
design records, while the remote root initially had only older R49/R50/R52
design memos. The exact evidence is:

* R93's local/remote search and absence classification:
  `work/agents/CODEX_R93_OWNER_H2_CHECKLIST_VERIFICATION_20260924.md:9-20,24-34,47-51`;
* the live handoff describing the stale checkout and the required guard:
  `docs/RESEARCH_HANDOFF_CURRENT.md:1-13`;
* the subsequent synchronization record: `RESEARCH_LOG.md:15618-15626`,
  which says R70/R89/R90/R91/R92/R93 and current ledgers were copied and their
  local/remote SHA-256 values matched. This changed evidence availability only;
  it did not authorize execution.

This event shows why a remote path existing, or a copied memo carrying a valid
individual hash, cannot itself be treated as owner/H2 readiness.

## One minimal guard: two-sided complete manifest-set attestation

Introduce one future-only `provenance_sync_attestation_v1` handshake for the
readiness evidence set. The proposed artifact is absent; it is a gate, not a
scientific result.

### Local challenge and fixed set

The local controller creates a fresh random `sync_nonce` and a fixed,
owner-reviewed ordered set of path/role entries. The set must include every
readiness-gating record and ledger needed for the current handoff, including
the S131 contract, latest R70/R89 protocol records, current R91/R92/R93/R94
memos, `docs/RESEARCH_HANDOFF_CURRENT.md`, `docs/RESEARCH_PLANS_EN.md`,
`RESEARCH_LOG.md`, `research_events.jsonl`, and `workflow_checks.jsonl`. The
exact set version is recorded; no wildcard or “copy what exists” rule is valid.

Each entry is:

```text
{path, fixed_role, regular_file=true, size_bytes, sha256}
```

The set digest is:

```text
expected_local_manifest_sha256 =
  SHA256(canonical_json_v2({set_version, sorted(path, fixed_role, size, sha256)}))
```

The manifest itself, the remote attestation, and their supplied hash fields are
excluded from the entry set and only structurally validated, so there is no
self-hash recursion. A missing required path is a failed set, never a fabricated
placeholder. The local controller retains this freshly computed digest outside
the remote checkout and passes only the nonce and expected digest to the
verifier.

### Remote verification and local decision

The remote verifier stages the exact set under a new disposable snapshot root
and returns a receipt containing the nonce, observed entries, and
`remote_manifest_sha256`. Before returning `SYNC_VERIFIED`, it rejects missing,
extra, duplicate, symlink, hard-link, traversal, alias, socket, or non-regular
paths, then recomputes every file hash and the set digest.

The local controller—not the remote receipt—makes the decision:

```text
SYNC_VERIFIED iff
  nonce == fresh_local_nonce
  and remote_manifest_sha256 == expected_local_manifest_sha256
  and every path, role, size, and sha256 matches the local set exactly
```

Otherwise the state is `REMOTE_PROVENANCE_UNVERIFIED` and the remote checkout
cannot satisfy owner/H2 readiness. The nonce prevents replay of an older valid
attestation. A later append to any ledger changes its listed hash and makes the
attestation `STALE`; a new local set and new nonce are required. This is the
minimal whole-ledger check needed to catch both stale checkout and partial sync.

## Attack checks

| Attack | Guard detection | Stop result |
|---|---|---|
| Remote is stale and lacks current R70/R89/R92/R93 records | required path/role entry missing or remote set digest differs | `REMOTE_PROVENANCE_UNVERIFIED`; keep `NO_COMMAND_AVAILABLE` |
| Partial sync omits a ledger or handoff file | exact set cardinality/path check or whole-ledger digest mismatch | same; do not infer readiness from matching subset hashes |
| Same-path content swap | per-file SHA/size mismatch and set digest mismatch | same; if H2 artifact were otherwise present, later phase-2 status remains `H2_UNIDENTIFIABLE` |
| Swap a protocol file into an H2/owner role path | fixed path-to-role map mismatch before digest acceptance | same; no cross-role fallback |
| Replay an old manifest/remote receipt | fresh nonce or freshly computed local digest mismatch | `REMOTE_PROVENANCE_UNVERIFIED` |
| Append to `RESEARCH_LOG.md` after sync | listed ledger hash no longer equals local current set | `STALE`; resync before any readiness claim |
| Symlink, hard-link, traversal, socket, or alias escape | root/type/realpath/link check before hashing | boundary abort; no input bytes consumed |

The guard does not replace R89 owner hashing or R70 H2 checks. If the set is
verified but an owner tuple, code manifest, H2 source manifest, packet, or
boundary artifact is absent or invalid, the existing statuses still apply:
`NO_COMMAND_AVAILABLE`, `OWNER_REVIEW_REQUIRED`, `REJECT_FIXTURE`, or
`H2_UNIDENTIFIABLE` at the specified phase.

## Terminal condition

The guard is a provenance/evidence hygiene contract only. It does not create
the missing runner or artifacts and does not authorize CGLR, real C8, replay,
GPU/Slurm, receipt mutation, or validation-flag changes. Until the R92
artifacts exist and this two-sided attestation is `SYNC_VERIFIED`, remain at
`NO_COMMAND_AVAILABLE`; project flags remain `new_method_validated=false` and
`novelty_authorization=NONE`.

**R94 status: STALE-REMOTE GUARD / DESIGN-ONLY / EXECUTION BLOCKED.**
