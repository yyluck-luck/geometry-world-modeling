#!/usr/bin/env python3
"""Validate the Gate0 pre-run contract without opening any future data.

Exit 0 means the contract is complete enough to permit the next pre-run step.
Exit 2 means the contract is structurally readable but formally BLOCKED.
Exit 3 means malformed input or a missing required field.
This validator never reads datasets, predictions, or GT; it only reads JSON.
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path

SCHEMA = "gwm-gate0-contract-v1"
SECTIONS = (
    "camera", "depth", "rgb_depth_pairing", "pose", "future_gt_isolation",
    "heldout_identity", "fair_budget", "checkpoints_and_code", "independent_readback",
)
SHA256 = re.compile(r"^[0-9a-f]{64}$")

def err(errors, msg):
    errors.append(msg)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("contract", nargs="?", default=str(Path(__file__).with_name("gate0_contract_v1.json")))
    args = ap.parse_args()
    path = Path(args.contract)
    try:
        obj = json.loads(path.read_text())
    except Exception as exc:
        print(json.dumps({"status": "MALFORMED", "error": str(exc)}, indent=2))
        return 3

    errors, blocked = [], []
    if obj.get("schema") != SCHEMA:
        err(errors, f"schema must be {SCHEMA!r}")
    if obj.get("contract_version") != 1:
        err(errors, "contract_version must be integer 1")
    if obj.get("status") not in {"BLOCKED", "PASS"}:
        err(errors, "status must be BLOCKED or PASS")
    if obj.get("formal_experiment_eligibility") not in {"BLOCKED", "PASS"}:
        err(errors, "formal_experiment_eligibility must be BLOCKED or PASS")

    sections = obj.get("sections")
    if not isinstance(sections, dict):
        err(errors, "sections must be an object")
        sections = {}
    for name in SECTIONS:
        section = sections.get(name)
        if not isinstance(section, dict):
            err(errors, f"missing section {name}")
            continue
        status = section.get("status")
        if status not in {"BLOCKED", "PASS"}:
            err(errors, f"{name}.status must be BLOCKED or PASS")
        elif status != "PASS":
            blocked.append(f"{name}: status={status}")
        required = section.get("required", [])
        values = section.get("values", {})
        if not isinstance(required, list) or not isinstance(values, dict):
            err(errors, f"{name}.required must be a list and values an object")
            continue
        for key in required:
            if key not in values:
                err(errors, f"{name}.values missing required key {key}")
            elif values[key] is None and status == "PASS":
                err(errors, f"{name}.values.{key} is null while section is PASS")

    # Hash format checks are useful even while blocked; no file is opened.
    candidates = []
    scene = obj.get("sources", {}).get("candidate_scene", {})
    candidates.append(("sources.candidate_scene.archive_sha256", scene.get("archive_sha256")))
    held = sections.get("heldout_identity", {}).get("values", {}) if isinstance(sections.get("heldout_identity"), dict) else {}
    candidates.append(("sections.heldout_identity.values.archive_sha256", held.get("archive_sha256")))
    candidates.append(("sections.heldout_identity.values.manifest_sha256", held.get("manifest_sha256")))
    ck = sections.get("checkpoints_and_code", {}).get("values", {}) if isinstance(sections.get("checkpoints_and_code"), dict) else {}
    for key in ("vmem_checkpoint", "cut3r_checkpoint_if_used"):
        val = ck.get(key)
        if isinstance(val, dict):
            candidates.append((f"checkpoints_and_code.{key}.sha256", val.get("sha256")))
    for label, value in candidates:
        if value is None:
            continue
        if not isinstance(value, str) or not SHA256.fullmatch(value):
            err(errors, f"{label} must be a lowercase SHA-256 hex string")

    # Cross-field guards make accidental bypasses visible.
    if obj.get("status") == "PASS" and blocked:
        err(errors, "top-level PASS is inconsistent with blocked sections")
    if obj.get("formal_experiment_eligibility") == "PASS" and blocked:
        err(errors, "formal eligibility PASS is inconsistent with blocked sections")
    if obj.get("formal_experiment_eligibility") == "PASS" and obj.get("status") != "PASS":
        err(errors, "formal eligibility PASS requires top-level status PASS")
    # Semantic guards for sections that cannot be represented by a non-null placeholder.
    future = sections.get("future_gt_isolation", {}).get("values", {}) if isinstance(sections.get("future_gt_isolation"), dict) else {}
    if sections.get("future_gt_isolation", {}).get("status") == "PASS":
        if future.get("prediction_output_hash_before_gt_open") is not True:
            err(errors, "future_gt_isolation PASS requires prediction_output_hash_before_gt_open=true")
        if future.get("future_rgb_depth_pose_gt_not_read_before_seal") is not True:
            err(errors, "future_gt_isolation PASS requires future GT not read before seal=true")
    heldout_values = sections.get("heldout_identity", {}).get("values", {}) if isinstance(sections.get("heldout_identity"), dict) else {}
    if sections.get("heldout_identity", {}).get("status") == "PASS" and heldout_values.get("zero_exposure_before_freeze") is not True:
        err(errors, "heldout_identity PASS requires zero_exposure_before_freeze=true")
    readback_values = sections.get("independent_readback", {}).get("values", {}) if isinstance(sections.get("independent_readback"), dict) else {}
    if sections.get("independent_readback", {}).get("status") == "PASS":
        for key in ("post_run_manifest_recompute", "metric_recompute", "output_seal_check"):
            if readback_values.get(key) is not True:
                err(errors, f"independent_readback PASS requires {key}=true")

    result = {
        "schema": SCHEMA,
        "contract": str(path),
        "structural_status": "PASS" if not errors else "MALFORMED",
        "formal_status": "PASS" if not blocked and not errors and obj.get("status") == "PASS" and obj.get("formal_experiment_eligibility") == "PASS" else "BLOCKED",
        "blocked_sections": blocked,
        "errors": errors,
        "reads_future_data": False,
        "next_action": "Do not launch a formal experiment until formal_status is PASS." if (blocked or errors) else "Proceed to independent pre-run review and signed dispatch manifest."
    }
    print(json.dumps(result, indent=2))
    if errors:
        return 3
    return 0 if result["formal_status"] == "PASS" else 2

if __name__ == "__main__":
    raise SystemExit(main())
