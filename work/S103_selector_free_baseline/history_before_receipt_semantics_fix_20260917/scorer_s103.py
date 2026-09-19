#!/usr/bin/env python3
"""Post-seal RGB scorer for the S103 selector-free development baseline.

This process is deliberately separate from the predictor.  It verifies a frozen
protocol and prediction seal before opening any future RGB file.  Depth and pose
outcomes stay unopened in this first development score and must be handled by a
separately frozen geometry metric.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import sys

import numpy as np
from PIL import Image
import torch


def require(value, message):
    if not value:
        raise RuntimeError(message)


def utc_now():
    return datetime.now(timezone.utc)


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def sha_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def descriptor(path):
    path = Path(path).resolve()
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha_file(path)}


def resolve_ref(ref, base, label, parse_json=False):
    require(isinstance(ref, dict), f"{label}: missing descriptor")
    path = Path(ref["path"])
    if not path.is_absolute():
        path = Path(base) / path
    path = path.resolve()
    require(path.is_file(), f"{label}: missing file {path}")
    require(path.stat().st_size == ref.get("bytes"), f"{label}: byte count mismatch")
    require(sha_file(path) == ref.get("sha256"), f"{label}: SHA-256 mismatch")
    return json.loads(path.read_text()) if parse_json else path


def identity(record):
    return tuple(str(record[key]) for key in ("dataset_id", "scene_id", "sequence_id", "frame_id"))


def future_rgb_to_model_grid(raw):
    with Image.open(io.BytesIO(raw)) as image:
        rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
    require(rgb.shape == (480, 640, 3), f"future RGB native shape differs: {rgb.shape}")
    tensor = torch.from_numpy(rgb.transpose(2, 0, 1).copy()).float().unsqueeze(0) / 255.0
    # Frozen VMem transform: 640x480 -> 768x576 area resize -> centred 576 crop.
    transformed = torch.nn.functional.interpolate(
        tensor, size=(576, 768), mode="area", antialias=False
    )[:, :, :, 96:672]
    require(tuple(transformed.shape) == (1, 3, 576, 576), "reference transform shape differs")
    array = transformed[0].permute(1, 2, 0).numpy()
    return np.clip(array * 255.0, 0, 255).astype(np.uint8)


def prediction_to_uint8(frame):
    require(frame.shape == (3, 576, 576), f"prediction frame shape differs: {frame.shape}")
    image = frame.transpose(1, 2, 0)
    rescaled = bool(float(image.min()) < -0.1)
    if rescaled:
        image = (image + 1.0) / 2.0
    return np.clip(image * 255.0, 0, 255).astype(np.uint8), rescaled


def integer_metrics(prediction, reference):
    require(prediction.shape == reference.shape == (576, 576, 3), "score shape differs")
    delta = prediction.astype(np.int64) - reference.astype(np.int64)
    absolute_sum = int(np.abs(delta).sum(dtype=np.int64))
    squared_sum = int((delta * delta).sum(dtype=np.int64))
    count = int(delta.size)
    mse = squared_sum / (count * 255 * 255)
    return {
        "channel_value_count": count,
        "absolute_integer_sum": absolute_sum,
        "squared_integer_sum": squared_sum,
        "mae_0_1": absolute_sum / (count * 255),
        "mse_0_1": mse,
        "psnr_db": "Infinity" if mse == 0 else -10.0 * math.log10(mse),
    }


def write_new_json(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", required=True)
    parser.add_argument("--prediction-seal", required=True)
    parser.add_argument("--prediction-seal-sha256", required=True)
    parser.add_argument("--dispatch-manifest", required=True)
    parser.add_argument("--dispatch-manifest-sha256", required=True)
    parser.add_argument("--launch-guard-receipt", required=True)
    parser.add_argument("--launch-guard-receipt-sha256", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    contract_path = Path(args.contract).resolve()
    base = contract_path.parent
    contract = json.loads(contract_path.read_text())
    require(contract.get("schema") == "gwm-gate0-staged-v2", "wrong contract schema")
    protocol = contract.get("protocol", {})
    require(protocol.get("status") == "FROZEN", "protocol is not frozen")
    run_id = protocol.get("run_id")
    require(bool(run_id), "run_id missing")
    protocol_sha = canonical_sha(protocol)
    formal = protocol.get("formal_execution", {})

    scorer_path = resolve_ref(protocol.get("scorer_ref"), base, "scorer implementation")
    require(scorer_path == Path(__file__).resolve(), "contract binds a different scorer")
    metric_path = resolve_ref(protocol.get("budget", {}).get("metric_definition_ref"),
                              base, "metric definition")
    metric = json.loads(metric_path.read_text())
    require(metric.get("schema") == "s103-rgb-metric-definition-v1", "wrong metric definition")

    scorer_manifest = resolve_ref(protocol.get("scorer_inputs_ref"), base, "scorer manifest", True)
    records = scorer_manifest.get("records", [])
    require(records and all(row.get("role") in {"future_rgb", "future_depth", "future_pose"}
                            for row in records), "scorer manifest contains a non-outcome role")

    seal_path = Path(args.prediction_seal).resolve()
    require(sha_file(seal_path) == args.prediction_seal_sha256, "prediction seal SHA mismatch")
    seal = json.loads(seal_path.read_text())
    dispatch_path = Path(args.dispatch_manifest).resolve()
    require(sha_file(dispatch_path) == args.dispatch_manifest_sha256,
            "dispatch manifest supplied SHA mismatch")
    dispatch = json.loads(dispatch_path.read_text())
    guard_path = Path(args.launch_guard_receipt).resolve()
    require(sha_file(guard_path) == args.launch_guard_receipt_sha256,
            "launch guard supplied SHA mismatch")
    guard = json.loads(guard_path.read_text())
    require(dispatch.get("schema") == "gwm-gate0-v2-dispatch-manifest-v1" and
            dispatch.get("status") == "FROZEN" and dispatch.get("stage") == "pre-run",
            "dispatch schema/status/stage mismatch")
    require(dispatch.get("contract_sha256") == sha_file(contract_path) and
            dispatch.get("protocol_sha256") == protocol_sha and
            dispatch.get("run_id") == run_id and dispatch.get("scope") == protocol.get("scope"),
            "dispatch does not bind contract/protocol")
    component_bindings = {
        "validator_sha256": formal.get("validator_ref"),
        "predictor_wrapper_sha256": formal.get("predictor_ref"),
        "prediction_sealer_sha256": formal.get("sealer_ref"),
        "sbatch_script_sha256": formal.get("sbatch_ref"),
        "formal_bundle_preparer_sha256": formal.get("bundle_preparer_ref"),
        "launch_guard_sha256": formal.get("launch_guard_ref"),
        "generic_launcher_sha256": formal.get("generic_launcher_ref"),
        "formal_chain_regression_receipt_sha256": formal.get("formal_chain_regression_receipt_ref"),
    }
    for key, artifact_ref in component_bindings.items():
        require(isinstance(artifact_ref, dict) and dispatch.get(key) == artifact_ref.get("sha256"),
                f"dispatch component binding mismatch: {key}")
    require(dispatch.get("runtime_binding_sha256") ==
            (protocol.get("runtime_binding_ref") or {}).get("sha256"), "dispatch runtime mismatch")
    require(dispatch.get("isolation_receipt_sha256") ==
            (((protocol.get("isolation") or {}).get("receipt_ref") or {}).get("sha256")),
            "dispatch isolation mismatch")
    require(dispatch.get("execution_boundary_id") ==
            (protocol.get("isolation") or {}).get("execution_boundary_id"), "dispatch boundary mismatch")
    require(guard.get("schema") == "gwm-formal-launch-guard-receipt-v1" and
            guard.get("status") == "PASS", "launch guard receipt invalid")
    require(guard.get("manifest_sha256") == args.dispatch_manifest_sha256 and
            guard.get("contract_sha256") == sha_file(contract_path) and
            guard.get("protocol_sha256") == protocol_sha and guard.get("run_id") == run_id and
            guard.get("scope") == protocol.get("scope") and
            guard.get("execution_boundary_id") == dispatch.get("execution_boundary_id"),
            "launch guard provenance mismatch")
    for key in component_bindings:
        require(guard.get(key) == dispatch.get(key), f"launch guard component mismatch: {key}")
    require(seal.get("schema") == "s103-prediction-seal-v1" and
            seal.get("status") == "PREDICTION_SEALED" and
            seal.get("prediction_complete") is True and
            seal.get("future_scoring_permitted") is True,
            "seal is not a trusted successful prediction seal")
    require(seal.get("run_id") == run_id, "seal run_id mismatch")
    require(seal.get("protocol_sha256") == protocol_sha, "seal protocol hash mismatch")
    require(seal.get("contract_sha256") == sha_file(contract_path) and
            seal.get("dispatch_manifest_sha256") == args.dispatch_manifest_sha256,
            "seal contract/dispatch provenance mismatch")
    for key in ("predictor_wrapper_sha256", "prediction_sealer_sha256",
                "validator_sha256", "sbatch_script_sha256"):
        require(seal.get(key) == dispatch.get(key), f"seal component mismatch: {key}")
    require(seal.get("execution_boundary_id") == dispatch.get("execution_boundary_id"),
            "seal execution boundary mismatch")
    require(seal.get("predictor_exit_code") == 0, "predictor did not exit successfully")
    require(seal.get("unauthorized_input_reads") == 0, "predictor reported unauthorized reads")
    require(seal.get("future_outcome_files_opened") is False and seal.get("future_gt_opened") is False,
            "seal reports future access")
    sealed_at = datetime.fromisoformat(seal["sealed_at_utc"])
    require(sealed_at.tzinfo is not None, "seal timestamp lacks timezone")
    launched_at = datetime.fromisoformat(guard["recorded_at_utc"])
    completed_at = datetime.fromisoformat(seal["predictor_completed_at_utc"])
    require(launched_at.tzinfo is not None and completed_at.tzinfo is not None and
            launched_at <= completed_at <= sealed_at, "launch/prediction/seal timestamp order invalid")

    predicted_refs = [row for row in seal.get("files", [])
                      if Path(row.get("path", "")).name == "predicted_target_rgb_fp32.npy"]
    require(len(predicted_refs) == 1, "seal must bind exactly one predicted RGB array")
    prediction_path = resolve_ref(predicted_refs[0], base, "sealed prediction")
    prediction = np.load(prediction_path, allow_pickle=False)
    require(prediction.shape == (4, 3, 576, 576), f"prediction array shape differs: {prediction.shape}")
    require(prediction.dtype == np.float32 and np.isfinite(prediction).all(),
            "prediction array dtype/finite check failed")

    windows = protocol.get("windows", [])
    require(len(windows) == 1, "first development scorer requires exactly one window")
    window = windows[0]
    prefix = tuple(str(window[key]) for key in ("dataset_id", "scene_id", "sequence_id"))
    target_ids = [str(value) for value in window.get("target_ids", [])]
    expected = {prefix + (frame_id,) for frame_id in target_ids}
    future_rgb = [row for row in records if row["role"] == "future_rgb"]
    require(len(future_rgb) == 4 and {identity(row) for row in future_rgb} == expected,
            "future RGB identities do not match the frozen target window")
    future_rgb.sort(key=lambda row: target_ids.index(str(row["frame_id"])))

    out = Path(args.output_dir).resolve()
    out.mkdir(parents=True, exist_ok=False)
    opened_at = None
    references = []
    opened = []
    for row in future_rgb:
        if opened_at is None:
            opened_at = utc_now()
            require(opened_at >= sealed_at, "future outcome would open before prediction seal")
        path = resolve_ref(row["file"], base, "future RGB")
        raw = path.read_bytes()
        references.append(future_rgb_to_model_grid(raw))
        opened.append({"identity": list(identity(row)), **descriptor(path)})
    references = np.stack(references)

    emitted = []
    rescale_branches = []
    frames = []
    for index, frame_id in enumerate(target_ids):
        current, branch = prediction_to_uint8(prediction[index])
        emitted.append(current)
        rescale_branches.append(branch)
        frames.append({"frame_id": frame_id, **integer_metrics(current, references[index])})
    emitted = np.stack(emitted)

    np.save(out / "emitted_target_rgb_uint8.npy", emitted, allow_pickle=False)
    np.save(out / "transformed_future_rgb_uint8.npy", references, allow_pickle=False)
    total_abs = sum(row["absolute_integer_sum"] for row in frames)
    total_sq = sum(row["squared_integer_sum"] for row in frames)
    total_n = sum(row["channel_value_count"] for row in frames)
    aggregate_mse = total_sq / (total_n * 255 * 255)
    metrics = {
        "schema": "s103-rgb-score-v1",
        "run_id": run_id,
        "protocol_sha256": protocol_sha,
        "metric_definition_sha256": sha_file(metric_path),
        "target_ids": target_ids,
        "frames": frames,
        "aggregate": {
            "channel_value_count": total_n,
            "absolute_integer_sum": total_abs,
            "squared_integer_sum": total_sq,
            "mae_0_1": total_abs / (total_n * 255),
            "mse_0_1": aggregate_mse,
            "psnr_db": "Infinity" if aggregate_mse == 0 else -10.0 * math.log10(aggregate_mse),
        },
        "prediction_range_rescale_branch": rescale_branches,
        "geometry_scored": False,
        "claim_boundary": "development RGB score only; no held-out, geometry, memory, or method claim",
    }
    write_new_json(out / "metrics.json", metrics)
    receipt = {
        "schema": "s103-post-seal-rgb-scoring-receipt-v1",
        "status": "RGB_SCORE_COMPLETE_PENDING_INDEPENDENT_RECOMPUTE",
        "run_id": run_id,
        "protocol_sha256": protocol_sha,
        "prediction_seal_sha256": args.prediction_seal_sha256,
        "dispatch_manifest_sha256": args.dispatch_manifest_sha256,
        "launch_guard_receipt_sha256": args.launch_guard_receipt_sha256,
        "outcomes_first_opened_at_utc": opened_at.isoformat(),
        "future_files_opened": opened,
        "future_depth_opened": False,
        "future_pose_opened": False,
        "metrics_ref": descriptor(out / "metrics.json"),
        "derived_arrays": [descriptor(out / "emitted_target_rgb_uint8.npy"),
                           descriptor(out / "transformed_future_rgb_uint8.npy")],
        "scorer_ref": descriptor(Path(__file__)),
        "completed_at_utc": utc_now().isoformat(),
        "new_method_validated": False,
        "novelty_authorization": "NONE",
    }
    write_new_json(out / "SCORING_RECEIPT.json", receipt)
    print(json.dumps({"status": receipt["status"], "metrics_ref": receipt["metrics_ref"]}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"SCORER_BLOCKED: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
