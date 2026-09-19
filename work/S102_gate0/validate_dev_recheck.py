#!/usr/bin/env python3
"""S102 development-only gate recheck from the immutable S97 audit receipt.

This does not claim a held-out result. It checks that existing development
evidence is structurally sufficient to reject accidental test-set reuse.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "work/S97_dev_rgbd_pair_audit/RESULTS.json"
OUT = Path(__file__).resolve().parent / "GATE0_RESULT.json"

def main():
    src = json.loads(SRC.read_text())
    cases = src.get("cases", [])
    checks = []
    checks.append({"id": "source_receipt_exists", "pass": bool(cases)})
    checks.append({"id": "all_cases_marked_development_seen", "pass": all(c.get("exposure_state") == "DEVELOPMENT_SEEN" for c in cases)})
    checks.append({"id": "rgb_depth_header_verified", "pass": all(bool(c.get("rgb_header_modes_sizes")) and bool(c.get("depth_header_modes_sizes")) for c in cases)})
    checks.append({"id": "no_bad_image_reads", "pass": all(c.get("bad_image_reads") == 0 for c in cases)})
    checks.append({"id": "not_held_out", "pass": all(c.get("exposure_state") != "HELD_OUT_TEST" for c in cases)})
    result = {
        "schema": "S102-gate0-development-recheck-v1",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "source_receipt": str(SRC),
        "source_receipt_sha256": __import__("hashlib").sha256(SRC.read_bytes()).hexdigest(),
        "checks": checks,
        "status": "BLOCKED_DEVELOPMENT_DATA_NOT_HELD_OUT",
        "formal_s91_run": False,
        "model_inferences": 0,
        "completed_utc": datetime.now(timezone.utc).isoformat(),
        "next_step": "Obtain a new legally usable held-out RGB-D/pose sequence and rerun the full Gate0 manifest check.",
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "checks_pass": sum(x["pass"] for x in checks), "checks_total": len(checks)}))

if __name__ == "__main__":
    main()
