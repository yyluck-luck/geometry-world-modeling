# C-002 reviewer identity hardening design — Agent A

## Scope and inspected state

This is a read-only design review for C-002. It does not approve a protocol, modify the validator/assembler, or authorize a run.

Inspected current remote artifacts:

- `GATE0_CONTRACT_CANDIDATE_v8.json`, SHA-256 `8d8038bad5ba79244b92f927953e94b13cd07a8bc975efd9862391481b9f6d36`.
- `validate_gate0_v2.py`, SHA-256 `a14b4cb65fdf2622aff1f591b014c423a8b4a743ebce37eabf3baefc70f2e8a0`.
- `assemble_s103_reviewed_contract.py`, SHA-256 `f844c4979294bfd562f87560bfb5e799f4382746fc803a80ba69763e96a4c5b2`.

The current assembler's `different_reviewer` and validator's `independent_reviewer` only strip whitespace and compare case-sensitive free-form strings. They do not restrict reviewer names to known identities, do not reject noncanonical spelling, and do not require the adapter and protocol reviewers to differ.

## Minimal policy

Use one versioned policy identifier and the same closed, role-specific allowlist in both assembler and validator:

```python
REVIEWER_IDENTITY_POLICY_ID = "s103-canonical-reviewers-v1"
REVIEWER_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REVIEWER_ROLE_ALLOWLIST = {
    "adapter": frozenset({"codex-agent-adapter-review-20260916"}),
    "protocol": frozenset({"codex-agent-protocol-review-20260916"}),
}
```

The allowlist must be code-owned, not accepted from a candidate-authored JSON field. Otherwise the protocol author could add an alias for itself and recreate the same vulnerability. The bound validator and assembler must contain the same policy ID and table; a parity regression must fail if they diverge.

Canonicalization must be ASCII-only and fail closed:

```python
def canonical_identity(value):
    if not isinstance(value, str):
        return None
    folded = value.strip().casefold()
    if not REVIEWER_ID_RE.fullmatch(folded):
        return None
    if value != folded:
        return None  # reject whitespace, case variants, and noncanonical spelling
    return folded

def allowed_reviewer(review, role):
    reviewer = canonical_identity(review.get("reviewer") if isinstance(review, dict) else None)
    if reviewer not in REVIEWER_ROLE_ALLOWLIST[role]:
        return None
    return reviewer
```

All equality and distinctness checks must compare the `casefold()` canonical form, even though noncanonical raw spellings are rejected. Restricting the accepted alphabet to lowercase ASCII also rejects Unicode homoglyph/full-width variants rather than trying to normalize them into identities.

Protocol and adapter authors must pass the same canonical identity parser. For the adapter review, require its canonical reviewer to be different from both `protocol.author` and `dataset.adapter_author`. For the final protocol review, require its canonical reviewer to be different from the protocol author, every adapter author, and every bound adapter reviewer. Finally, require the canonical adapter-reviewer set and protocol reviewer to be disjoint.

## Required fields and binding

The smallest schema change is:

1. Add `protocol.reviewer_identity_policy_id: "s103-canonical-reviewers-v1"` to the next candidate. The assembler and validator must reject a missing or different value.
2. Keep `reviewer` as the sole reviewer identity field in each review artifact. Its value must be the exact canonical allowlisted string for the role inferred from its binding slot; do not trust a self-declared role or alias field.
3. Keep the existing immutable descriptors `{path, bytes, sha256}` for `dataset.adapter_review_ref` and top-level `review_ref`. Identity acceptance is performed only after the referenced JSON has been independently rehashed and loaded.
4. Do not treat prereview status as final protocol approval. The final protocol review must bind the exact canonical SHA of the adapter-bound protocol that includes `reviewer_identity_policy_id`.

The existing Agent A adapter review is compatible without rewriting its contents:

- canonical reviewer: `codex-agent-adapter-review-20260916`;
- allowed role: `adapter` only;
- current artifact SHA-256: `6553b7f991538e52f68be5afc5bde2f943261c0b796c7660c808de9da8a6c0bb`.

The assembler should bind that exact file descriptor into `protocol.datasets.rgbd-scenes-v2.adapter_review_ref`. A different file using the same reviewer string is not the same review and must not substitute for this hash-bound artifact.

## Minimal executable checks

Assembler stage 1:

```python
require(protocol["reviewer_identity_policy_id"] == REVIEWER_IDENTITY_POLICY_ID, "reviewer policy mismatch")
adapter_reviewer = allowed_reviewer(adapter_review, "adapter")
require(adapter_reviewer is not None, "adapter reviewer is not canonical/allowlisted")
require(adapter_reviewer not in {canonical_identity(author), canonical_identity(adapter_author)},
        "adapter reviewer is an author")
```

Assembler stage 2:

```python
protocol_reviewer = allowed_reviewer(protocol_review, "protocol")
require(protocol_reviewer is not None, "protocol reviewer is not canonical/allowlisted")
require(protocol_reviewer not in {canonical_identity(author), canonical_identity(adapter_author)},
        "protocol reviewer is an author")
require(protocol_reviewer != adapter_reviewer,
        "adapter and protocol reviews require distinct canonical reviewers")
```

The validator must independently repeat all of the same checks after loading and rehashing `adapter_review_ref` and `review_ref`; assembler success is not evidence that validator identity checks ran.

## Required negative and positive tests

Add the following tests to both assembler tests and validator self-tests (or one shared truth-table fixture executed against both implementations):

1. Reject protocol author `codex-root-20260916` presented as `CODEX-ROOT-20260916`.
2. Reject the same author with leading/trailing whitespace.
3. Reject an unknown alias such as `codex-root-20260916-reviewer`.
4. Reject Unicode/full-width or homoglyph spellings, including `ｃodex-root-20260916`.
5. Reject uppercase or whitespace variants of an otherwise allowlisted reviewer; only the canonical raw spelling is accepted.
6. Reject missing, empty, non-string, or punctuation-containing reviewer values.
7. Reject `codex-agent-adapter-review-20260916` in the protocol-review slot.
8. Reject `codex-agent-protocol-review-20260916` in the adapter-review slot.
9. Reject the same canonical identity for adapter and protocol review even if a synthetic test allowlist accidentally grants it both roles.
10. Reject a changed/missing `protocol.reviewer_identity_policy_id`.
11. Reject a copied review JSON with the correct reviewer string when its `{bytes, sha256}` no longer matches the bound descriptor.
12. Positively accept the exact Agent A adapter review descriptor and canonical identity in the adapter slot.
13. Positively accept `codex-agent-protocol-review-20260916` only for a final review whose `protocol_sha256` equals the exact adapter-bound protocol SHA, and only when it differs from the bound adapter reviewer.
14. Assert assembler/validator parity for every identity test vector.

## Security boundary

This minimal scheme closes C-002's alias, case, whitespace, role-confusion, and same-reviewer gaps. It is not cryptographic authentication: a party able to write a new artifact could still type an allowlisted identity. If the threat model includes malicious repository writers impersonating another reviewer, the next step must be a signature or platform-issued reviewer attestation bound to the review hash. Until then, claims should be limited to enforcement of the frozen canonical agent-ID policy, not human identity authentication.
