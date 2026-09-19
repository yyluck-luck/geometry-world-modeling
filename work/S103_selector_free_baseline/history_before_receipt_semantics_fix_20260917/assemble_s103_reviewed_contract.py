#!/usr/bin/env python3
"""Bind genuine review artifacts into S103 in the only valid order.

Stage 1 binds an already-written adapter review and emits the protocol SHA that a
different author must review. Stage 2 binds a protocol review of that exact SHA.
This tool never creates a review, never changes review contents, and never
overwrites an output file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


REVIEWER_IDENTITY_POLICY_ID = "s103-canonical-reviewers-v1"
REVIEWER_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REVIEWER_ROLE_ALLOWLIST = {
    "adapter": frozenset({"codex-agent-adapter-review-20260916"}),
    "protocol": frozenset({"codex-agent-protocol-review-20260916"}),
}


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def desc(path: Path) -> dict:
    path = path.resolve()
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)}


def canonical_sha(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def substantive(review: dict) -> bool:
    try:
        from datetime import datetime
        reviewed_at = datetime.fromisoformat(review.get("reviewed_at_utc", ""))
    except (TypeError, ValueError):
        return False
    evidence = review.get("evidence_checked")
    checks = review.get("checks")
    findings = review.get("findings")
    limitations = review.get("limitations")
    return (reviewed_at.tzinfo is not None and
            isinstance(evidence, list) and bool(evidence) and
            all(isinstance(item, dict) and isinstance(item.get("path"), str) and
                type(item.get("bytes")) is int and item["bytes"] >= 0 and
                isinstance(item.get("sha256"), str) and len(item["sha256"]) == 64
                for item in evidence) and
            isinstance(checks, dict) and bool(checks) and
            all(value is True for value in checks.values()) and
            isinstance(findings, list) and bool(findings) and
            all(isinstance(item, str) and bool(item.strip()) for item in findings) and
            isinstance(limitations, list) and bool(limitations) and
            all(isinstance(item, str) and bool(item.strip()) for item in limitations))


def canonical_identity(value):
    if not isinstance(value, str):
        return None
    folded = value.strip().casefold()
    if value != folded or not REVIEWER_ID_RE.fullmatch(folded):
        return None
    return folded


def allowed_reviewer(review: dict, role: str):
    reviewer = canonical_identity(review.get("reviewer") if isinstance(review, dict) else None)
    return reviewer if reviewer in REVIEWER_ROLE_ALLOWLIST[role] else None


def different_reviewer(review: dict, *authors) -> bool:
    reviewer = canonical_identity(review.get("reviewer") if isinstance(review, dict) else None)
    normalized = {canonical_identity(author) for author in authors}
    return reviewer is not None and None not in normalized and reviewer not in normalized


def verify_review_evidence(review: dict) -> None:
    for index, item in enumerate(review["evidence_checked"]):
        path = Path(item["path"]).resolve()
        require(path.is_file(), f"review evidence {index} missing: {path}")
        require(path.stat().st_size == item["bytes"], f"review evidence {index} size mismatch")
        require(sha(path) == item["sha256"], f"review evidence {index} SHA mismatch")


def load_json(path: Path) -> dict:
    obj = json.loads(path.read_text())
    require(isinstance(obj, dict), f"JSON object required: {path}")
    return obj


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--adapter-review", required=True)
    parser.add_argument("--protocol-review")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    candidate = Path(args.candidate).resolve()
    adapter_path = Path(args.adapter_review).resolve()
    output = Path(args.output).resolve()
    require(candidate.is_file(), "candidate contract missing")
    require(adapter_path.is_file(), "adapter review missing")
    require(not output.exists(), "output already exists; reviewed contracts are immutable")

    contract = load_json(candidate)
    require(contract.get("schema") == "gwm-gate0-staged-v2", "wrong contract schema")
    protocol = contract.get("protocol")
    require(isinstance(protocol, dict) and protocol.get("status") == "FROZEN",
            "protocol must already be frozen")
    require(protocol.get("reviewer_identity_policy_id") == REVIEWER_IDENTITY_POLICY_ID,
            "reviewer identity policy mismatch")
    author = protocol.get("author")
    datasets = protocol.get("datasets")
    require(isinstance(datasets, dict) and len(datasets) == 1,
            "S103 review assembler expects exactly one dataset")
    dataset_id, dataset = next(iter(datasets.items()))
    adapter_ref = dataset.get("adapter_ref") or {}
    adapter_author = dataset.get("adapter_author")
    require(isinstance(adapter_author, str) and bool(adapter_author.strip()),
            "adapter author identity missing")

    adapter_review = load_json(adapter_path)
    require(adapter_review.get("status") == "ADAPTER_ACCEPTED", "adapter review is not accepted")
    require(adapter_review.get("adapter_sha256") == adapter_ref.get("sha256"),
            "adapter review does not bind current adapter SHA")
    adapter_reviewer = allowed_reviewer(adapter_review, "adapter")
    require(adapter_reviewer is not None, "adapter reviewer is noncanonical or not role-allowlisted")
    require(different_reviewer(adapter_review, author, adapter_author),
            "adapter reviewer is missing or is an author")
    require(substantive(adapter_review),
            "adapter review lacks timestamped evidence, all-pass checks, findings, or limitations")
    verify_review_evidence(adapter_review)
    dataset["adapter_review_ref"] = desc(adapter_path)
    contract["review_ref"] = None
    protocol_hash = canonical_sha(protocol)
    status = "ADAPTER_BOUND_PENDING_PROTOCOL_REVIEW"

    if args.protocol_review:
        protocol_path = Path(args.protocol_review).resolve()
        require(protocol_path.is_file(), "protocol review missing")
        protocol_review = load_json(protocol_path)
        require(protocol_review.get("verdict") == "PRE_RUN_APPROVED",
                "protocol review is not approved")
        require(protocol_review.get("protocol_sha256") == protocol_hash,
                "protocol review does not bind adapter-bound protocol SHA")
        protocol_reviewer = allowed_reviewer(protocol_review, "protocol")
        require(protocol_reviewer is not None,
                "protocol reviewer is noncanonical or not role-allowlisted")
        require(different_reviewer(protocol_review, author),
                "protocol reviewer is missing or is the protocol author")
        require(different_reviewer(protocol_review, adapter_author),
                "protocol reviewer is the adapter author")
        require(protocol_reviewer != adapter_reviewer,
                "adapter and protocol reviewers must be distinct")
        require(substantive(protocol_review),
                "protocol review lacks timestamped evidence, all-pass checks, findings, or limitations")
        verify_review_evidence(protocol_review)
        contract["review_ref"] = desc(protocol_path)
        status = "REVIEWS_BOUND_PENDING_VALIDATOR"

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "dataset_id": dataset_id,
                      "protocol_sha256": protocol_hash, "output": desc(output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
