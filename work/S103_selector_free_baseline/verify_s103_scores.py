#!/usr/bin/env python3
"""Independent recomputation for S103's post-seal full-frame RGB score.

This implementation does not import the scorer.  It reopens the sealed array and
future RGB records, independently repeats the frozen resize/crop, and checks the
saved metrics using integer accumulators.
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


def sha_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def resolve(ref, base, label):
    require(isinstance(ref, dict), f"{label}: missing descriptor")
    path = Path(ref["path"])
    if not path.is_absolute():
        path = Path(base) / path
    path = path.resolve()
    require(path.is_file(), f"{label}: missing file")
    require(path.stat().st_size == ref.get("bytes"), f"{label}: bytes differ")
    require(sha_file(path) == ref.get("sha256"), f"{label}: hash differs")
    return path


def ref_grid(path):
    with Image.open(path) as image:
        native = np.asarray(image.convert("RGB"), dtype=np.uint8)
    require(native.shape == (480, 640, 3), "reference native shape differs")
    value = torch.tensor(native.transpose(2, 0, 1).copy(), dtype=torch.float32)[None] / 255.0
    value = torch.nn.functional.adaptive_avg_pool2d(value, (576, 768))[:, :, :, 96:672]
    require(tuple(value.shape) == (1, 3, 576, 576), "independent transform shape differs")
    return np.minimum(np.maximum(value[0].permute(1, 2, 0).numpy() * 255.0, 0), 255).astype(np.uint8)


def emitted(frame):
    image = frame.transpose(1, 2, 0)
    if float(image.min()) < -0.1:
        image = (image + 1.0) / 2.0
    return np.minimum(np.maximum(image * 255.0, 0), 255).astype(np.uint8)


def score(prediction, reference):
    difference = prediction.astype(np.int64) - reference.astype(np.int64)
    abs_sum = int(np.abs(difference).sum(dtype=np.int64))
    sq_sum = int(np.square(difference).sum(dtype=np.int64))
    count = int(difference.size)
    mse = sq_sum / (count * 65025)
    return count, abs_sum, sq_sum, abs_sum / (count * 255), mse, (
        "Infinity" if mse == 0 else -10.0 * math.log10(mse)
    )


def close(actual, expected, label):
    if actual == "Infinity" or expected == "Infinity":
        require(actual == expected, f"{label}: infinity status differs")
        return
    require(math.isfinite(float(actual)) and math.isfinite(float(expected)), f"{label}: non-finite")
    require(abs(float(actual) - float(expected)) <= 1e-12 + 1e-12 * abs(float(expected)),
            f"{label}: numeric difference")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", required=True)
    parser.add_argument("--prediction-seal", required=True)
    parser.add_argument("--scoring-receipt", required=True)
    parser.add_argument("--scoring-receipt-sha256", required=True)
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    contract_path = Path(args.contract).resolve()
    base = contract_path.parent
    contract = json.loads(contract_path.read_text())
    protocol = contract["protocol"]
    protocol_sha = canonical_sha(protocol)
    require(args.reviewer != protocol.get("author"), "independent reviewer must differ from protocol author")

    seal_path = Path(args.prediction_seal).resolve()
    seal = json.loads(seal_path.read_text())
    require(seal.get("protocol_sha256") == protocol_sha, "seal protocol hash differs")
    prediction_ref = [item for item in seal["files"]
                      if Path(item.get("path", "")).name == "predicted_target_rgb_fp32.npy"]
    require(len(prediction_ref) == 1, "sealed prediction identity differs")
    prediction = np.load(resolve(prediction_ref[0], base, "prediction"), allow_pickle=False)
    require(prediction.shape == (4, 3, 576, 576) and prediction.dtype == np.float32
            and np.isfinite(prediction).all(), "sealed prediction array differs")

    receipt_path = Path(args.scoring_receipt).resolve()
    require(sha_file(receipt_path) == args.scoring_receipt_sha256, "scoring receipt hash differs")
    receipt = json.loads(receipt_path.read_text())
    require(receipt.get("run_id") == protocol.get("run_id"), "scoring run_id differs")
    require(receipt.get("protocol_sha256") == protocol_sha, "scoring protocol hash differs")
    metrics_path = resolve(receipt.get("metrics_ref"), receipt_path.parent, "metrics")
    metrics = json.loads(metrics_path.read_text())

    manifest_path = resolve(protocol["scorer_inputs_ref"], base, "scorer manifest")
    manifest = json.loads(manifest_path.read_text())
    rows = [row for row in manifest["records"] if row.get("role") == "future_rgb"]
    target_ids = [str(item) for item in protocol["windows"][0]["target_ids"]]
    rows.sort(key=lambda row: target_ids.index(str(row["frame_id"])))
    require(len(rows) == len(target_ids) == 4, "future RGB count differs")

    frame_rows = []
    total_count = total_abs = total_sq = 0
    for index, row in enumerate(rows):
        reference = ref_grid(resolve(row["file"], base, "future RGB"))
        current = emitted(prediction[index])
        count, abs_sum, sq_sum, mae, mse, psnr = score(current, reference)
        saved = metrics["frames"][index]
        require(str(saved["frame_id"]) == target_ids[index], "metric frame order differs")
        require(saved["channel_value_count"] == count, "frame count differs")
        require(saved["absolute_integer_sum"] == abs_sum, "absolute sum differs")
        require(saved["squared_integer_sum"] == sq_sum, "squared sum differs")
        close(mae, saved["mae_0_1"], "frame MAE")
        close(mse, saved["mse_0_1"], "frame MSE")
        close(psnr, saved["psnr_db"], "frame PSNR")
        total_count += count
        total_abs += abs_sum
        total_sq += sq_sum
        frame_rows.append({"frame_id": target_ids[index], "count": count,
                           "absolute_integer_sum": abs_sum, "squared_integer_sum": sq_sum})

    aggregate = metrics["aggregate"]
    aggregate_mse = total_sq / (total_count * 65025)
    require(aggregate["channel_value_count"] == total_count, "aggregate count differs")
    require(aggregate["absolute_integer_sum"] == total_abs, "aggregate absolute sum differs")
    require(aggregate["squared_integer_sum"] == total_sq, "aggregate squared sum differs")
    close(total_abs / (total_count * 255), aggregate["mae_0_1"], "aggregate MAE")
    close(aggregate_mse, aggregate["mse_0_1"], "aggregate MSE")
    close("Infinity" if aggregate_mse == 0 else -10.0 * math.log10(aggregate_mse),
          aggregate["psnr_db"], "aggregate PSNR")

    output = {
        "schema": "s103-independent-rgb-recompute-v1",
        "status": "METRICS_RECOMPUTED_MATCH",
        "reviewer": args.reviewer,
        "run_id": protocol["run_id"],
        "protocol_sha256": protocol_sha,
        "metrics_sha256": sha_file(metrics_path),
        "scoring_receipt_sha256": args.scoring_receipt_sha256,
        "frames": frame_rows,
        "recomputed_full_frame_count": total_count,
        "future_depth_opened": False,
        "future_pose_opened": False,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "new_method_validated": False,
    }
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x") as stream:
        json.dump(output, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": output["status"], "metrics_sha256": output["metrics_sha256"]}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"VERIFIER_BLOCKED: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
