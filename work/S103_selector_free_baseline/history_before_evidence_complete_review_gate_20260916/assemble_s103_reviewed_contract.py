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
    findings = review.get("findings")
    limitations = review.get("limitations")
    return (isinstance(findings, list) and bool(findings) and
            all(isinstance(item, str) and bool(item.strip()) for item in findings) and
            isinstance(limitations, list) and
            all(isinstance(item, str) and bool(item.strip()) for item in limitations))


def different_reviewer(review: dict, *authors) -> bool:
    reviewer = review.get("reviewer")
    normalized = {str(author or "").strip() for author in authors}
    return isinstance(reviewer, str) and bool(reviewer.strip()) and reviewer.strip() not in normalized


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
    require(different_reviewer(adapter_review, author, adapter_author),
            "adapter reviewer is missing or is an author")
    require(substantive(adapter_review), "adapter review lacks findings or explicit limitations")
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
        require(different_reviewer(protocol_review, author),
                "protocol reviewer is missing or is the protocol author")
        require(substantive(protocol_review),
                "protocol review lacks findings or explicit limitations")
        contract["review_ref"] = desc(protocol_path)
        status = "REVIEWS_BOUND_PENDING_VALIDATOR"

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "dataset_id": dataset_id,
                      "protocol_sha256": protocol_hash, "output": desc(output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
