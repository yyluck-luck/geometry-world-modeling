#!/usr/bin/env python3
"""Independent-code self-audit of the staged scene13 development window.

This is not a different-author review.  It checks identities, hashes, stage
contents, permissions, and command-camera provenance without decoding future RGB
or depth pixels.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import stat

import numpy as np


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check_ref(ref):
    path = Path(ref["path"]).resolve()
    require(path.is_file(), f"missing file: {path}")
    require(path.stat().st_size == ref["bytes"], f"byte mismatch: {path}")
    require(sha(path) == ref["sha256"], f"hash mismatch: {path}")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    artifact = Path(args.artifact_dir).resolve()
    window = json.loads((artifact / "WINDOW_MANIFEST.json").read_text())
    predictor = json.loads((artifact / "predictor_inputs.json").read_text())
    scorer = json.loads((artifact / "scorer_inputs.json").read_text())
    stage = Path(window["predictor_stage_root"]).resolve()

    history = [str(x) for x in window["history_ids"]]
    targets = [str(x) for x in window["target_ids"]]
    require(history == ["0", "15", "30", "45"], "history identity changed")
    require(targets == ["60", "75", "90", "105"], "target identity changed")
    require(set(history).isdisjoint(targets) and window["chronological"] is True,
            "window overlap/chronology invalid")
    require(predictor["roles"] == ["history_rgb", "history_pose", "command_camera", "camera_intrinsics"],
            "predictor roles differ")
    records = predictor["records"]
    counts = {role: sum(row["role"] == role for row in records) for role in predictor["roles"]}
    require(counts == {"history_rgb": 4, "history_pose": 4,
                       "command_camera": 4, "camera_intrinsics": 1}, "predictor role counts differ")
    predictor_paths = {check_ref(row["file"]) for row in records}
    require(all(path.is_relative_to(stage) for path in predictor_paths), "predictor path escapes stage")
    require(not any("depth" in path.name for path in predictor_paths), "depth unexpectedly staged")
    require(not any(path.name.endswith("color.png") and f"{int(frame):06d}" in path.name
                    for frame in targets for path in predictor_paths), "future RGB unexpectedly staged")

    scorer_paths = {check_ref(row["file"]) for row in scorer["records"]}
    require(len(scorer["records"]) == 12, "scorer record count differs")
    require({row["role"] for row in scorer["records"]} == {"future_rgb", "future_depth", "future_pose"},
            "scorer roles differ")
    require(all(not path.is_relative_to(stage) for path in scorer_paths), "outcome path is inside predictor stage")
    require(predictor_paths.isdisjoint(scorer_paths), "predictor and scorer share a payload path")

    for item in window["command_camera_provenance"]:
        command_path = check_ref(item["command"])
        source_pose = check_ref(item["source_pose"])
        command = json.loads(command_path.read_text())
        source = np.loadtxt(source_pose, dtype=np.float64)
        require(np.array_equal(np.asarray(command["c2w"], dtype=np.float64), source),
                "command camera matrix differs from declared source pose")
        require(command["blind_pose_evaluation_allowed"] is False
                and command["heldout_claim_allowed"] is False, "command claim boundary differs")

    stage_files = sorted(path for path in stage.rglob("*") if path.is_file())
    require(len(stage_files) == 14, "stage file count differs")
    require(sha(stage / "predictor_inputs.json") == sha(artifact / "predictor_inputs.json"),
            "staged and archived predictor manifests differ")
    require(all(not (path.stat().st_mode & stat.S_IWUSR) for path in stage_files),
            "a staged file remains owner-writable")
    require(not (stage.stat().st_mode & stat.S_IWUSR), "stage root remains owner-writable")

    result = {
        "schema": "s103-scene13-window-self-audit-v1",
        "status": "PASS_SELF_AUDIT_NOT_INDEPENDENT_REVIEW",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "history_ids": history, "target_ids": targets,
        "predictor_role_counts": counts,
        "stage_file_count": len(stage_files),
        "predictor_payload_paths": len(predictor_paths),
        "scorer_payload_paths": len(scorer_paths),
        "future_rgb_pixels_decoded": False,
        "future_depth_pixels_decoded": False,
        "model_forward_completed": False,
        "formal_gate0_pass": False,
        "different_author_review_completed": False,
        "next_step": "Obtain adapter/window review by a different author and bind this exact stage into a formal compute-node isolation receipt."
    }
    output = Path(args.output).resolve()
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
