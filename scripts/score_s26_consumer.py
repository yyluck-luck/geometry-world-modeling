#!/usr/bin/env python3
"""S26 frozen saved-head consumer depth scoring; no model or GA imports.

prepare-inputs only copies existing metadata identities. score needs the caller's
frozen manifest digest and all four completed producer seals before any GT bytes.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()
PROTOCOL = ROOT / "docs/S26_CONSUMER_SCORING_PROTOCOL.md"
PREP = ROOT / "work/S26_scoring_preparation"
BASE = ROOT / "results/S26_consumer_baseline"
OUTPUT = BASE / "scoring"
COUNTS = {"common_old": 4, "cut3r": 8, "ttt3r": 8, "filt3r": 8}
METHODS = ("cut3r", "ttt3r", "filt3r")
OLD, NEW = list(range(4)), list(range(4, 8))
HEIGHT, WIDTH = 384, 512
TOLERANCE = {"atol": 1e-6, "rtol": 1e-6}
SCHEMA = "s26-consumer-scoring-v1"
GT_SOURCE = ROOT / "results/S23_geometry_diagnostic/gt_receipt.json"
CANDIDATE_SOURCE = ROOT / "work/S26_consumer_baseline_preparation/candidate_inputs.json"


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def valid_sha(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def require(condition, message):
    if not condition:
        raise ValueError(message)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def fixed_config():
    return {
        "schema": SCHEMA,
        "producer_dirs": {m: str(BASE / m) for m in COUNTS},
        "producer_frame_counts": COUNTS,
        "scoring_output": str(OUTPUT),
        "old_frame_indices": OLD,
        "new_frame_indices": NEW,
        "prediction_shape_hw": [HEIGHT, WIDTH],
        "sensor_shape_hw": [480, 640],
        "sensor_depth_divisor": 5000,
        "nearest_mapping": "floor((2*target_index+1)*source_size/(2*target_size))",
        "gt_valid": "finite_and_positive_on_target_grid",
        "prediction_invalid": "nonfinite_or_nonpositive",
        "invalid_policy": "any_invalid_on_valid_gt_makes_frame_absrel_rmse_null;delta1_invalid_is_failure",
        "aggregation": "equal_frame_mean_only_if_all_prespecified_frames_defined",
        "old_depth_tolerance": TOLERANCE,
        "gt_scale_fit": False,
        "confidence_mask": False,
        "far_depth_cut": False,
        "delta1_threshold": 1.25,
        "delta1_comparison": "strict_less_than",
    }


def prepare_inputs():
    """Read only JSON/source/protocol bytes, never a referenced depth image."""
    PREP.mkdir(parents=True, exist_ok=True)
    target = PREP / "candidate_scoring_inputs.json"
    require(not target.exists(), f"Refuse existing candidate: {target}")
    original = CANDIDATE_SOURCE.read_bytes()
    historical = GT_SOURCE.read_bytes()
    records = json.loads(original)["depth_coverage_metadata"]
    gt_records = json.loads(historical)["files"]
    require(len(records) == 8, "Exactly eight depth metadata rows required")
    inherited = {(r["index"], r["path"]): r["sha256"] for r in gt_records}
    frames = []
    for i, row in enumerate(records):
        require(row["index"] == i, "Ordered indices 0..7 required")
        key = (i, row["depth_file"])
        require(key in inherited and valid_sha(inherited[key]), "Historical GT SHA absent")
        frames.append({"index": i, "path": row["depth_file"], "sha256": inherited[key],
                       "rgb_time": row["rgb_time"], "depth_time": row["depth_time"]})
    require(len({r["path"] for r in frames}) == 8, "Duplicate depth paths")
    config = fixed_config()
    config.update({
        "prepared_utc": utc(),
        "status": "METADATA_CANDIDATE_REQUIRES_PARENT_FREEZE",
        "gt_depth_frames": frames,
        "control_sha256": {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in (SELF, PROTOCOL)},
        "metadata_sources_sha256": {
            str(CANDIDATE_SOURCE.relative_to(ROOT)): digest(original),
            str(GT_SOURCE.relative_to(ROOT)): digest(historical)},
        "evidence_scope": "Eight sensor-depth images were previously read in S23; this preparation reads only metadata, not PNG or prediction arrays. No new independent data.",
    })
    validate_config(config)
    write_json(target, config)
    return {"status": "PASS_METADATA_ONLY", "path": str(target), "sha256": digest(target.read_bytes()),
            "true_array_reads": 0, "sensor_png_byte_reads": 0, "model_runs": 0, "ga_runs": 0}


def validate_config(config):
    require(isinstance(config, dict), "manifest.scoring must be object")
    for key, value in fixed_config().items():
        require(config.get(key) == value, f"Frozen scoring policy mismatch: {key}")
    frames = config.get("gt_depth_frames")
    require(isinstance(frames, list) and len(frames) == 8, "GT frame count must be eight")
    data_root = ROOT / "data/tum/fr2_desk_download/extracted/rgbd_dataset_freiburg2_desk/depth"
    for i, row in enumerate(frames):
        require(row.get("index") == i and valid_sha(row.get("sha256")), "Bad GT frame identity")
        p = Path(row["path"])
        require(p.is_absolute() and p.parent == data_root and p.suffix == ".png", "Unexpected GT path domain")
        require(all(isinstance(row.get(k), (int, float)) and math.isfinite(row[k]) for k in ("rgb_time", "depth_time")), "Invalid frame timestamps")
        require(float(p.stem) == row["depth_time"], "GT path timestamp mismatch")
        if i:
            require(row["rgb_time"] > frames[i-1]["rgb_time"], "RGB chronology mismatch")
    require(len({r["path"] for r in frames}) == 8, "GT paths must be unique")
    controls = config.get("control_sha256", {})
    required = {str(p.relative_to(ROOT)) for p in (SELF, PROTOCOL)}
    require(set(controls) == required and all(valid_sha(s) for s in controls.values()), "Scorer/protocol control identities required")
    metadata = config.get("metadata_sources_sha256", {})
    require(set(metadata) == {str(CANDIDATE_SOURCE.relative_to(ROOT)), str(GT_SOURCE.relative_to(ROOT))}
            and all(valid_sha(s) for s in metadata.values()), "Both metadata source identities required")


def seal_producers(config, parent_sha, reader=None):
    """All receipt/seal/NPZ hashes precede any array decode or sensor reader.

    reader injection is for artificial byte-fixture tests, not a public CLI bypass.
    """
    reader = reader or (lambda path: Path(path).read_bytes())
    identities, output_bytes = {}, {}
    receipts = {}
    for mode, count in COUNTS.items():
        directory = Path(config["producer_dirs"][mode])
        path = directory / "receipt.json"
        raw = reader(path)
        receipts[mode] = receipt = json.loads(raw)
        identities[str(path)] = digest(raw)
        require(receipt.get("status") == "PASS", f"Producer {mode} is not PASS")
        require(receipt.get("manifest_sha256") == parent_sha, f"Producer {mode} parent mismatch")
        require(receipt.get("mode") == mode and receipt.get("frame_count") == count, f"Producer {mode} domain mismatch")
        require(valid_sha(receipt.get("inputs_seal_sha256")), f"Producer {mode} input seal SHA absent")
        require(valid_sha(receipt.get("outputs", {}).get("output.npz")), f"Producer {mode} NPZ SHA absent")
    for mode, count in COUNTS.items():
        directory = Path(config["producer_dirs"][mode])
        path = directory / "inputs_seal.json"
        raw = reader(path)
        identities[str(path)] = digest(raw)
        require(digest(raw) == receipts[mode]["inputs_seal_sha256"], f"Input seal SHA mismatch: {mode}")
        seal = json.loads(raw)
        require(seal.get("manifest_sha256") == parent_sha and seal.get("mode") == mode
                and seal.get("frame_count") == count, f"Input seal metadata mismatch: {mode}")
        require(seal.get("sensor_depth_used") is False, f"Sensor depth prohibited in producer: {mode}")
    for mode in COUNTS:
        path = Path(config["producer_dirs"][mode]) / "output.npz"
        raw = reader(path)
        identities[str(path)] = digest(raw)
        require(digest(raw) == receipts[mode]["outputs"]["output.npz"], f"NPZ SHA mismatch: {mode}")
        output_bytes[mode] = raw
    return output_bytes, identities


def decode_outputs(buffers):
    import numpy as np
    arrays, diagnostics = {}, {}
    for mode, n in COUNTS.items():
        shapes = {"depth": (n, HEIGHT, WIDTH), "point_cloud": (n, HEIGHT, WIDTH, 3),
                  "conf": (n, HEIGHT, WIDTH), "focal": (n, 1), "pp": (n, 2), "c2w": (n, 4, 4)}
        with np.load(io.BytesIO(buffers[mode]), allow_pickle=False) as z:
            require(len(z.files) == len(shapes) and set(z.files) == set(shapes), f"Unexpected NPZ keys: {mode}")
            arrays[mode], diagnostics[mode] = {}, {}
            for key, shape in shapes.items():
                a = z[key]
                require(a.shape == shape and a.dtype == np.float32, f"Expected FP32 {shape}: {mode}/{key}")
                arrays[mode][key] = a
                diagnostics[mode][key] = {"shape": list(a.shape), "dtype": str(a.dtype),
                                          "nonfinite_count": int((~np.isfinite(a)).sum())}
        # Nonfinite new depth is retained for invalid-prediction accounting.
        # No other head participates in the sensor depth denominator.
    return arrays, diagnostics


def old_depth_check(reference, other):
    import numpy as np
    require(reference.shape == other.shape, "Old prefix shape mismatch")
    require(np.isfinite(reference).all() and (reference > 0).all(), "Common old depth must be finite positive")
    require(np.isfinite(other).all() and (other > 0).all(), "Reconstructed old depth must be finite positive")
    a, b = other.astype(np.float64), reference.astype(np.float64)
    difference = np.abs(a - b)
    mismatch = difference > TOLERANCE["atol"] + TOLERANCE["rtol"] * np.abs(b)
    return {"numeric_array_equal": bool(np.array_equal(reference, other)),
            "bitwise_equal": reference.dtype == other.dtype and reference.tobytes() == other.tobytes(),
            "unequal_element_count": int(np.count_nonzero(reference != other)),
            "max_abs_difference_m": float(difference.max()),
            "mean_abs_difference_m": float(difference.mean()),
            "outside_tolerance_count": int(mismatch.sum()), "tolerance": TOLERANCE,
            "within_tolerance": bool(not mismatch.any()),
            "meaning": "Output log/exp roundtrip only; frozen internal parameters require the producer observer's separate bitwise check."}


def nearest_grid(a, height=HEIGHT, width=WIDTH):
    import numpy as np
    y = ((2 * np.arange(height) + 1) * a.shape[0]) // (2 * height)
    x = ((2 * np.arange(width) + 1) * a.shape[1]) // (2 * width)
    return a[y[:, None], x[None, :]]


def depth_metrics(prediction, gt):
    import numpy as np
    require(prediction.shape == gt.shape and prediction.ndim == 2, "Metric requires corresponding 2D arrays")
    p, g = prediction.astype(np.float64), gt.astype(np.float64)
    valid_gt = np.isfinite(g) & (g > 0)
    invalid = (~np.isfinite(p)) | (p <= 0)
    n = int(valid_gt.sum())
    n_invalid = int((valid_gt & invalid).sum())
    row = {"grid_pixels": int(g.size), "gt_valid_pixels": n,
           "gt_invalid_pixels": int(g.size - n),
           "prediction_invalid_all_pixels": int(invalid.sum()),
           "prediction_invalid_on_gt_pixels": n_invalid,
           "prediction_invalid_fraction_on_gt": n_invalid / n if n else None,
           "absrel": None, "rmse_m": None, "delta1": None,
           "delta1_success_pixels": 0, "metric_status": "EMPTY_GT" if not n else "INVALID_PREDICTION" if n_invalid else "DEFINED"}
    if not n:
        return row
    valid_both = valid_gt & ~invalid
    pv, gv = p[valid_both], g[valid_both]
    hits = int(np.count_nonzero(np.maximum(pv / gv, gv / pv) < 1.25))
    row.update(delta1=hits / n, delta1_success_pixels=hits)
    if n_invalid == 0:
        row.update(absrel=float(np.mean(np.abs(pv - gv) / gv)),
                   rmse_m=float(np.sqrt(np.mean((pv - gv) ** 2))))
        require(math.isfinite(row["absrel"]) and math.isfinite(row["rmse_m"]), "Nonfinite computed metric")
    return row


def aggregate(rows, indices):
    require([r["index"] for r in rows] == indices, "Aggregate requires every fixed ordered frame")
    result = {"frame_indices": indices, "frame_count": len(indices),
              "aggregation": "equal_frame_mean;no_available_frame_or_pixel_pooled_substitution"}
    for key in ("absrel", "rmse_m", "delta1", "prediction_invalid_fraction_on_gt"):
        values = [r[key] for r in rows]
        result[key] = math.fsum(values) / len(values) if all(v is not None for v in values) else None
        result[key + "_defined_frames"] = sum(v is not None for v in values)
    for key in ("gt_valid_pixels", "gt_invalid_pixels", "prediction_invalid_all_pixels", "prediction_invalid_on_gt_pixels"):
        result[key + "_sum_descriptive"] = sum(r[key] for r in rows)
    result["empty_gt_frames"] = [r["index"] for r in rows if r["gt_valid_pixels"] == 0]
    result["invalid_prediction_frames"] = [r["index"] for r in rows if r["prediction_invalid_on_gt_pixels"] > 0]
    return result


def load_sensor_depths(frames):
    import numpy as np
    from PIL import Image
    depths, records, identities = [], [], {}
    for row in frames:
        raw = Path(row["path"]).read_bytes()
        sha = digest(raw)
        require(sha == row["sha256"], f"Sensor depth SHA mismatch: frame {row['index']}")
        identities[row["path"]] = sha
        with Image.open(io.BytesIO(raw)) as im:
            require(im.format == "PNG", "Expected sensor PNG")
            a = np.asarray(im)
        require(a.shape == (480, 640) and a.dtype.kind in "ui", "Expected integer 480x640 sensor depth")
        require(int(a.min()) >= 0 and int(a.max()) <= 65535, "Sensor depth outside uint16 range")
        g = nearest_grid(a).astype(np.float64) / 5000.0
        depths.append(g)
        records.append({**row, "bytes": len(raw), "source_shape": list(a.shape), "source_dtype": str(a.dtype),
                        "positive_source_pixels": int((a > 0).sum()), "positive_target_pixels": int((g > 0).sum())})
    return depths, records, identities


def score(manifest_path, expected_sha):
    require(valid_sha(expected_sha), "Caller must supply frozen manifest SHA256")
    require(not OUTPUT.exists(), f"Refuse existing scoring output: {OUTPUT}")
    manifest_path = Path(manifest_path).resolve()
    raw = manifest_path.read_bytes()
    require(digest(raw) == expected_sha, "Caller manifest SHA mismatch")
    config = json.loads(raw)["scoring"]
    validate_config(config)
    identities = {str(manifest_path): expected_sha}
    for key in ("control_sha256", "metadata_sources_sha256"):
        for name, expected in config[key].items():
            p = ROOT / name
            require(digest(p.read_bytes()) == expected, f"Bound {key} changed: {name}")
            identities[str(p)] = expected
    OUTPUT.mkdir(parents=True, exist_ok=False)
    receipt = {"status": "RUNNING", "started_utc": utc(), "manifest_sha256": expected_sha,
               "schema": SCHEMA, "sensor_gt_byte_reads_started": False,
               "prediction_decode_started": False, "model_runs": 0, "ga_runs": 0,
               "evidence_scope": "Scoring previously seen sensor data after four new GA producer seals; not novel-method, memory-mechanism, or video-generation evidence."}
    write_json(OUTPUT / "receipt.json", receipt)
    try:
        buffers, producer_ids = seal_producers(config, expected_sha)
        identities.update(producer_ids)
        write_json(OUTPUT / "pre_score_seal.json", {"utc": utc(), "status": "PASS", "manifest_sha256": expected_sha,
                   "input_sha256": identities, "all_four_producers_pass": True,
                   "all_four_npz_sha_verified": True, "prediction_arrays_decoded": False,
                   "sensor_gt_bytes_read": False})
        receipt.update(prediction_decode_started=True)
        write_json(OUTPUT / "receipt.json", receipt)
        arrays, schema_report = decode_outputs(buffers)
        del buffers
        write_json(OUTPUT / "output_schema.json", schema_report)
        old_checks = {m: old_depth_check(arrays["common_old"]["depth"], arrays[m]["depth"][:4]) for m in METHODS}
        write_json(OUTPUT / "old_prefix_checks.json", old_checks)
        require(all(r["within_tolerance"] for r in old_checks.values()), "Old depth output violates frozen roundtrip tolerance")
        receipt.update(sensor_gt_byte_reads_started=True, sensor_gt_read_started_utc=utc())
        write_json(OUTPUT / "receipt.json", receipt)
        gt, gt_records, gt_ids = load_sensor_depths(config["gt_depth_frames"])
        identities.update(gt_ids)
        write_json(OUTPUT / "gt_receipt.json", {"utc": utc(), "manifest_sha256": expected_sha, "files": gt_records,
                   "historical_identity_source": str(GT_SOURCE), "already_seen_in_s23": True})
        rows = []
        for mode, n in COUNTS.items():
            for i in range(n):
                row = {"mode": mode, "index": i, "partition": "old" if i < 4 else "new",
                       "primary": mode in METHODS and i in NEW,
                       **depth_metrics(arrays[mode]["depth"][i], gt[i])}
                # Post-clean confidence is described without screening any depth pixel.
                import numpy as np
                conf = arrays[mode]["conf"][i]
                row["post_clean_positive_finite_conf_fraction_all_grid"] = float((np.isfinite(conf) & (conf > 0)).mean())
                rows.append(row)
        with (OUTPUT / "per_frame.csv").open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        select = lambda m, indices: [r for r in rows if r["mode"] == m and r["index"] in indices]
        metrics = {"schema": SCHEMA, "utc": utc(), "manifest_sha256": expected_sha,
                   "primary_new4": {m: aggregate(select(m, NEW), NEW) for m in METHODS},
                   "diagnostic_all8": {m: aggregate(select(m, list(range(8))), list(range(8))) for m in METHODS},
                   "diagnostic_old4": {m: aggregate(select(m, OLD), OLD) for m in COUNTS},
                   "per_frame": rows, "unit_rmse": "meter", "scale_fit": False,
                   "confidence_mask": False, "gt_far_cut": False,
                   "evidence_limits": ["8 previously seen fr2_desk frames, approximately 0.236 seconds; only 4 new frames in main comparison",
                       "Pixels and adjacent frames are not independent experimental samples; no significance or generalization claim",
                       "All methods use given GT camera control, common old predicted depth, and saved network heads",
                       "Depth is a consumer component endpoint, not a memory failure, retrieval, or generated video measurement"]}
        write_json(OUTPUT / "metrics.json", metrics)
        for path, expected in identities.items():
            require(digest(Path(path).read_bytes()) == expected, f"Input changed during scoring: {path}")
        outputs = {p.name: digest(p.read_bytes()) for p in sorted(OUTPUT.iterdir()) if p.name != "receipt.json"}
        receipt.update(status="PASS", completed_utc=utc(), input_sha256_before_after=identities,
                       inputs_unchanged=True, sensor_gt_images_decoded=len(gt), per_frame_rows=len(rows), outputs=outputs,
                       primary_absrel_rmse_complete=all(metrics["primary_new4"][m][k] is not None for m in METHODS for k in ("absrel", "rmse_m")),
                       pass_meaning="Execution/seal checks completed; see metric nulls and evidence limits before scientific interpretation")
        write_json(OUTPUT / "receipt.json", receipt)
        return receipt
    except Exception as exc:
        receipt.update(status="FAIL", failed_utc=utc(), error_type=type(exc).__name__, error=str(exc))
        write_json(OUTPUT / "receipt.json", receipt)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("prepare-inputs", help="Copy eight historical depth identities; no image/array reads")
    run = sub.add_parser("score", help="Run only after parent freeze and all four completed producers")
    run.add_argument("--manifest", required=True)
    run.add_argument("--manifest-sha256", required=True)
    args = parser.parse_args()
    result = prepare_inputs() if args.action == "prepare-inputs" else score(args.manifest, args.manifest_sha256)
    print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
