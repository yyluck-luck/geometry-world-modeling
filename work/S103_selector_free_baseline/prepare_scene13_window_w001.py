#!/usr/bin/env python3
"""Freeze one explicitly exposed scene13 development window for S103.

The data-custodian step copies only history RGB/pose, a hashed K JSON, and four
predeclared command-camera JSON files into the predictor stage.  Future RGB/depth
and original pose files remain outside that stage and are referenced only by the
scorer manifest.  Reading target pose to create a command is explicitly exposed
development metadata, so this window cannot support a blind pose/held-out claim.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil

import numpy as np


DATASET_ID = "rgbd-scenes-v2"
SCENE_ID = "rgbd-scenes-v2-scene_13"
SEQUENCE_ID = "seq-01"
HISTORY_IDS = [0, 15, 30, 45]
TARGET_IDS = [60, 75, 90, 105]


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def desc(path):
    path = Path(path).resolve()
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha_file(path)}


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def write_new(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(payload)


def record(role, frame_id, file_ref):
    return {"dataset_id": DATASET_ID, "scene_id": SCENE_ID,
            "sequence_id": SEQUENCE_ID, "frame_id": str(frame_id),
            "role": role, "file": file_ref}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--stage-root", required=True)
    parser.add_argument("--artifact-dir", required=True)
    args = parser.parse_args()

    dataset = Path(args.dataset_root).resolve()
    stage = Path(args.stage_root).resolve()
    artifact = Path(args.artifact_dir).resolve()
    require(dataset.is_dir(), "dataset root missing")
    require(not stage.exists(), "stage root already exists; never mutate a frozen stage")
    require(not artifact.exists(), "artifact directory already exists")
    sequence = dataset / SEQUENCE_ID
    intrinsics_source = dataset / "camera-intrinsics.txt"
    require(sequence.is_dir() and intrinsics_source.is_file(), "scene layout incomplete")
    for frame_id in HISTORY_IDS + TARGET_IDS:
        for suffix in ("color.png", "depth.png", "pose.txt"):
            require((sequence / f"frame-{frame_id:06d}.{suffix}").is_file(),
                    f"missing frame component {frame_id}/{suffix}")

    (stage / "history").mkdir(parents=True)
    (stage / "query").mkdir()
    artifact.mkdir(parents=True)
    reads = []
    predictor_records = []

    for frame_id in HISTORY_IDS:
        for suffix, role in (("color.png", "history_rgb"), ("pose.txt", "history_pose")):
            source = sequence / f"frame-{frame_id:06d}.{suffix}"
            target = stage / "history" / source.name
            shutil.copy2(source, target)
            reads.append({"purpose": "predictor_history_copy", "source": desc(source)})
            predictor_records.append(record(role, frame_id, desc(target)))

    K = np.loadtxt(intrinsics_source, dtype=np.float64)
    require(K.shape == (3, 3) and np.isfinite(K).all(), "camera intrinsics invalid")
    intrinsics = {
        "schema": "s103-camera-intrinsics-v1", "dataset_id": DATASET_ID,
        "scene_id": SCENE_ID, "K": K.tolist(), "native_wh": [640, 480],
        "distortion": "none documented in converted source; no undistortion applied",
        "pixel_center_convention": "u+0.5,v+0.5 development compatibility choice",
        "source": desc(intrinsics_source)
    }
    intrinsics_target = stage / "camera_intrinsics.json"
    write_new(intrinsics_target, json_bytes(intrinsics))
    reads.append({"purpose": "camera_intrinsics", "source": desc(intrinsics_source)})
    predictor_records.append(record("camera_intrinsics", "shared", desc(intrinsics_target)))

    command_provenance = []
    for frame_id in TARGET_IDS:
        source_pose = sequence / f"frame-{frame_id:06d}.pose.txt"
        matrix = np.loadtxt(source_pose, dtype=np.float64)
        require(matrix.shape == (4, 4) and np.isfinite(matrix).all(), "command pose invalid")
        require(abs(float(np.linalg.det(matrix[:3, :3])) - 1.0) < 1e-5, "command rotation invalid")
        command = {
            "schema": "s103-predeclared-command-camera-v1",
            "dataset_id": DATASET_ID, "scene_id": SCENE_ID,
            "sequence_id": SEQUENCE_ID, "frame_id": str(frame_id),
            "c2w": matrix.tolist(),
            "source_role": "dataset_mapping_pose_promoted_to_command_for_exposed_development_baseline",
            "source_pose": desc(source_pose),
            "blind_pose_evaluation_allowed": False,
            "heldout_claim_allowed": False
        }
        command_path = stage / "query" / f"command_camera_{frame_id:06d}.json"
        write_new(command_path, json_bytes(command))
        predictor_records.append(record("command_camera", frame_id, desc(command_path)))
        command_provenance.append({"frame_id": str(frame_id), "command": desc(command_path),
                                   "source_pose": desc(source_pose)})
        reads.append({"purpose": "predeclared_command_camera_metadata", "source": desc(source_pose)})

    role_order = {"history_rgb": 0, "history_pose": 1, "command_camera": 2, "camera_intrinsics": 3}
    predictor_records.sort(key=lambda row: (role_order[row["role"]],
                                            -1 if row["frame_id"] == "shared" else int(row["frame_id"])))
    predictor_manifest = {
        "schema": "s103-predictor-inputs-v1",
        "roles": ["history_rgb", "history_pose", "command_camera", "camera_intrinsics"],
        "development_data_exposed": True,
        "records": predictor_records,
        "future_rgb_present": False, "future_depth_present": False,
        "whole_archive_present": False
    }
    predictor_payload = json_bytes(predictor_manifest)
    write_new(stage / "predictor_inputs.json", predictor_payload)
    write_new(artifact / "predictor_inputs.json", predictor_payload)
    require(sha_file(stage / "predictor_inputs.json") == sha_file(artifact / "predictor_inputs.json"),
            "predictor manifest copies differ")

    scorer_records = []
    for frame_id in TARGET_IDS:
        for suffix, role in (("color.png", "future_rgb"), ("depth.png", "future_depth"),
                             ("pose.txt", "future_pose")):
            source = sequence / f"frame-{frame_id:06d}.{suffix}"
            scorer_records.append(record(role, frame_id, desc(source)))
            reads.append({"purpose": "scorer_manifest_hash_only", "source": desc(source),
                          "payload_decoded": role == "future_pose"})
    scorer_manifest = {
        "schema": "s103-scorer-inputs-v1", "records": scorer_records,
        "predictor_stage_contains_none_of_these_paths": True,
        "data_custodian_opened_bytes_before_prediction": True,
        "predictor_opened_bytes_before_seal": False,
        "note": "Development-only identity hashing is not zero-exposure held-out evaluation."
    }
    write_new(artifact / "scorer_inputs.json", json_bytes(scorer_manifest))

    window = {
        "schema": "s103-scene13-development-window-v1",
        "status": "FROZEN_DEVELOPMENT_CANDIDATE_PENDING_REVIEW",
        "dataset_id": DATASET_ID, "scene_id": SCENE_ID, "sequence_id": SEQUENCE_ID,
        "history_ids": [str(x) for x in HISTORY_IDS],
        "target_ids": [str(x) for x in TARGET_IDS], "chronological": True,
        "selection_rule": "fixed frame IDs declared before any S103 model forward; selected from frame identity and pose metadata only",
        "target_pose_role": "predeclared command input; blind pose scoring prohibited",
        "predictor_stage_root": str(stage),
        "predictor_inputs": desc(artifact / "predictor_inputs.json"),
        "staged_predictor_inputs": desc(stage / "predictor_inputs.json"),
        "scorer_inputs": desc(artifact / "scorer_inputs.json"),
        "command_camera_provenance": command_provenance,
        "claim_boundary": "one exposed development window; not held-out, not independent, not a method comparison"
    }
    write_new(artifact / "WINDOW_MANIFEST.json", json_bytes(window))
    receipt = {
        "schema": "s103-development-window-preparation-receipt-v1",
        "status": "WINDOW_STAGED_PENDING_INDEPENDENT_REVIEW_AND_FORMAL_ISOLATION_BINDING",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "generator": desc(Path(__file__)),
        "window_manifest": desc(artifact / "WINDOW_MANIFEST.json"),
        "predictor_inputs": desc(artifact / "predictor_inputs.json"),
        "staged_predictor_inputs": desc(stage / "predictor_inputs.json"),
        "scorer_inputs": desc(artifact / "scorer_inputs.json"),
        "stage_file_count": sum(1 for item in stage.rglob("*") if item.is_file()),
        "data_custodian_reads": reads,
        "target_rgb_pixels_decoded": False,
        "target_depth_pixels_decoded": False,
        "target_pose_metadata_exposed": True,
        "model_forward_completed": False,
        "future_scoring_completed": False,
        "formal_gate0_pass": False,
        "new_method_validated": False,
        "novelty_authorization": "NONE"
    }
    write_new(artifact / "PREPARATION_RECEIPT.json", json_bytes(receipt))

    # Freeze the stage against accidental edits.  A later contract refers to its
    # exact files and must create a new directory for any revision.
    for path in stage.rglob("*"):
        os.chmod(path, 0o444 if path.is_file() else 0o555)
    os.chmod(stage, 0o555)
    print(json.dumps({"status": receipt["status"], "stage": str(stage),
                      "artifact": str(artifact), "stage_file_count": receipt["stage_file_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
