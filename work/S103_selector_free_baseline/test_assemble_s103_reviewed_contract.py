#!/usr/bin/env python3
"""Synthetic ordering tests for review binding; no model, data, or GPU."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile


HERE = Path(__file__).resolve().parent
ASSEMBLER = HERE / "assemble_s103_reviewed_contract.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def write(path: Path, value: dict):
    path.write_text(json.dumps(value), encoding="utf-8")


def run(*args):
    return subprocess.run([sys.executable, str(ASSEMBLER), *map(str, args)],
                          text=True, capture_output=True)


def main() -> int:
    checks = []
    with tempfile.TemporaryDirectory(prefix="s103-review-order-") as temp:
        root = Path(temp)
        adapter = root / "adapter.py"; adapter.write_text("# fixture\n")
        protocol = {"status": "FROZEN", "author": "author-a",
                    "reviewer_identity_policy_id": "s103-canonical-reviewers-v1", "datasets": {
            "dataset-a": {"adapter_ref": {"path": str(adapter), "bytes": adapter.stat().st_size,
                                             "sha256": sha(adapter)},
                          "adapter_author": "author-a", "adapter_review_ref": None}}}
        candidate = root / "candidate.json"
        write(candidate, {"schema": "gwm-gate0-staged-v2", "protocol": protocol,
                          "review_ref": None, "post_run": {}})
        adapter_review = root / "adapter_review.json"
        write(adapter_review, {"status": "ADAPTER_ACCEPTED", "adapter_sha256": sha(adapter),
                               "reviewer": "codex-agent-adapter-review-20260916",
                               "reviewed_at_utc": "2026-09-16T13:00:00+00:00",
                               "evidence_checked": [{"path": str(adapter), "bytes": adapter.stat().st_size,
                                                     "sha256": sha(adapter)}],
                               "checks": {"identity": True}, "findings": ["fixture checked"],
                               "limitations": ["synthetic test"]})
        bound = root / "adapter_bound.json"
        stage1 = run("--candidate", candidate, "--adapter-review", adapter_review,
                     "--output", bound)
        bound_obj = json.loads(bound.read_text()) if bound.exists() else {}
        bound_hash = canonical(bound_obj.get("protocol", {}))
        checks.append(("adapter review binds before protocol review",
                       stage1.returncode == 0 and bound_obj.get("review_ref") is None))

        stale_review = root / "stale_review.json"
        write(stale_review, {"verdict": "PRE_RUN_APPROVED", "protocol_sha256": canonical(protocol),
                             "reviewer": "codex-agent-protocol-review-20260916",
                             "reviewed_at_utc": "2026-09-16T13:01:00+00:00",
                             "evidence_checked": [{"path": str(candidate), "bytes": candidate.stat().st_size,
                                                   "sha256": sha(candidate)}],
                             "checks": {"identity": True}, "findings": ["stale"],
                             "limitations": ["synthetic test"]})
        stale_out = root / "stale_out.json"
        stale = run("--candidate", bound, "--adapter-review", adapter_review,
                    "--protocol-review", stale_review, "--output", stale_out)
        checks.append(("pre-adapter protocol approval is rejected",
                       stale.returncode != 0 and not stale_out.exists()))

        final_review = root / "final_review.json"
        write(final_review, {"verdict": "PRE_RUN_APPROVED", "protocol_sha256": bound_hash,
                             "reviewer": "codex-agent-protocol-review-20260916",
                             "reviewed_at_utc": "2026-09-16T13:02:00+00:00",
                             "evidence_checked": [{"path": str(bound), "bytes": bound.stat().st_size,
                                                   "sha256": sha(bound)}],
                             "checks": {"identity": True}, "findings": ["final hash checked"],
                             "limitations": ["synthetic test"]})
        final_out = root / "final.json"
        final = run("--candidate", bound, "--adapter-review", adapter_review,
                    "--protocol-review", final_review, "--output", final_out)
        checks.append(("final adapter-bound protocol approval is accepted",
                       final.returncode == 0 and final_out.exists()))

        same_author = root / "same_author.json"
        write(same_author, {"status": "ADAPTER_ACCEPTED", "adapter_sha256": sha(adapter),
                            "reviewer": "author-a", "findings": ["self signed"],
                            "limitations": []})
        rejected_out = root / "rejected.json"
        rejected = run("--candidate", candidate, "--adapter-review", same_author,
                       "--output", rejected_out)
        checks.append(("same-author adapter review is rejected",
                       rejected.returncode != 0 and not rejected_out.exists()))

        alias_review = root / "alias_review.json"
        alias_obj = json.loads(adapter_review.read_text())
        alias_obj["reviewer"] = "CODEX-AGENT-ADAPTER-REVIEW-20260916"
        write(alias_review, alias_obj)
        alias_out = root / "alias_out.json"
        alias = run("--candidate", candidate, "--adapter-review", alias_review,
                    "--output", alias_out)
        checks.append(("uppercase allowlist alias is rejected",
                       alias.returncode != 0 and not alias_out.exists()))

        draft = root / "draft.json"
        write(draft, {"status": "DRAFT_NOT_A_REVIEW", "adapter_sha256": sha(adapter),
                      "reviewer": None, "findings": [], "limitations": []})
        draft_out = root / "draft_out.json"
        draft_result = run("--candidate", candidate, "--adapter-review", draft,
                           "--output", draft_out)
        checks.append(("unfilled review template is rejected",
                       draft_result.returncode != 0 and not draft_out.exists()))

        overwrite = run("--candidate", candidate, "--adapter-review", adapter_review,
                        "--output", bound)
        checks.append(("existing reviewed contract cannot be overwritten", overwrite.returncode != 0))

    status = "PASS" if all(ok for _, ok in checks) else "FAIL"
    print(json.dumps({"scope": "synthetic review-order checks only", "status": status,
                      "checks": [{"name": name, "passed": ok} for name, ok in checks]}, indent=2))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
