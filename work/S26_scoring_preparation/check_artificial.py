#!/usr/bin/env python3
"""Author self-checks: artificial values/byte fixtures only; no true data."""
import importlib.util
import io
import json
import math
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "scripts/score_s26_consumer.py"
spec = importlib.util.spec_from_file_location("s26_scorer", SOURCE)
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)
checks = []


def check(name, condition):
    if not condition:
        raise AssertionError(name)
    checks.append({"name": name, "status": "PASS"})


def rejects(name, fn, message):
    try:
        fn()
    except ValueError as e:
        check(name, message in str(e))
    else:
        raise AssertionError(name + ": accepted invalid fixture")


def scalar_metric(p, g):
    vals = [(float(a), float(b)) for a, b in zip(p.flat, g.flat) if math.isfinite(float(b)) and b > 0]
    invalid = sum(not math.isfinite(a) or a <= 0 for a, b in vals)
    if not vals:
        return (None, None, None, invalid)
    hits = sum(math.isfinite(a) and a > 0 and max(a / b, b / a) < 1.25 for a, b in vals)
    absrel = math.fsum(abs(a - b) / b for a, b in vals) / len(vals) if invalid == 0 else None
    rmse = math.sqrt(math.fsum((a - b) ** 2 for a, b in vals) / len(vals)) if invalid == 0 else None
    return (absrel, rmse, hits / len(vals), invalid)


def vector_scalar(name, p, g):
    got = s.depth_metrics(p, g)
    actual = [got[k] for k in ("absrel", "rmse_m", "delta1", "prediction_invalid_on_gt_pixels")]
    expected = scalar_metric(p, g)
    check(name, all(a is b if a is None or b is None else math.isclose(a, b, rel_tol=1e-14, abs_tol=1e-14)
                    for a, b in zip(actual, expected)))
    return got


def gate_fixtures():
    sha = "a" * 64
    config = s.fixed_config()
    blobs = {}
    for mode, count in s.COUNTS.items():
        directory = Path(config["producer_dirs"][mode])
        seal = {"manifest_sha256": sha, "mode": mode, "frame_count": count, "sensor_depth_used": False}
        bseal = json.dumps(seal).encode()
        bout = ("artificial NPZ byte placeholder " + mode).encode()
        receipt = {"status": "PASS", "manifest_sha256": sha, "mode": mode, "frame_count": count,
                   "inputs_seal_sha256": s.digest(bseal), "outputs": {"output.npz": s.digest(bout)}}
        blobs[str(directory / "receipt.json")] = json.dumps(receipt).encode()
        blobs[str(directory / "inputs_seal.json")] = bseal
        blobs[str(directory / "output.npz")] = bout
    return config, sha, blobs


def check_gate(name, alter=None, expected_error=None):
    config, sha, blobs = gate_fixtures()
    if alter:
        alter(config, blobs)
    trace = []

    def reader(path):
        trace.append(str(path))
        if str(path) not in blobs:
            raise AssertionError("Unpermitted fixture read / potential GT access: " + str(path))
        return blobs[str(path)]

    if expected_error:
        rejects(name, lambda: s.seal_producers(config, sha, reader), expected_error)
    else:
        buffers, ids = s.seal_producers(config, sha, reader)
        check(name, set(buffers) == set(s.COUNTS) and len(ids) == 12)
        check("gate_checks_all_receipts_then_all_seals_then_all_npz", [Path(p).name for p in trace] == ["receipt.json"] * 4 + ["inputs_seal.json"] * 4 + ["output.npz"] * 4)
    check(name + "_no_GT_paths", all(Path(p).name in ("receipt.json", "inputs_seal.json", "output.npz") for p in trace))
    return trace


def change_receipt(field, value):
    def mutate(config, blobs):
        path = str(Path(config["producer_dirs"]["filt3r"]) / "receipt.json")
        obj = json.loads(blobs[path])
        obj[field] = value
        blobs[path] = json.dumps(obj).encode()
    return mutate


def change_seal(field, value, reseal):
    def mutate(config, blobs):
        directory = Path(config["producer_dirs"]["filt3r"])
        path = str(directory / "inputs_seal.json")
        obj = json.loads(blobs[path])
        obj[field] = value
        blobs[path] = json.dumps(obj).encode()
        if reseal:
            rp = str(directory / "receipt.json")
            receipt = json.loads(blobs[rp])
            receipt["inputs_seal_sha256"] = s.digest(blobs[path])
            blobs[rp] = json.dumps(receipt).encode()
    return mutate


def main():
    target = Path(__file__).parent / "artificial_checks_v1.json"
    if target.exists():
        raise ValueError("Refuse existing self-check receipt")
    t0 = s.utc()
    g = np.array([[1., 2.], [4., 13.107]], dtype=np.float64)
    row = vector_scalar("perfect_vector_and_scalar", g.copy(), g)
    check("perfect_exact", row["absrel"] == row["rmse_m"] == 0 and row["delta1"] == 1)
    row = vector_scalar("twice_depth_vector_and_scalar", 2 * g, g)
    check("twice_depth_no_scale_fit", row["absrel"] == 1 and row["delta1"] == 0)
    mixed_g = np.array([[1., 0., np.nan], [2., np.inf, 13.107]])
    mixed_p = np.array([[1.1, np.nan, -2.], [2.2, 0., 12.5]])
    row = vector_scalar("zero_nonfinite_gt_excluded_far_retained", mixed_p, mixed_g)
    check("only_gt_domain_controls_denominator", row["gt_valid_pixels"] == 3 and row["prediction_invalid_all_pixels"] == 3 and row["prediction_invalid_on_gt_pixels"] == 0)
    for val, name in ((np.nan, "nan"), (np.inf, "inf"), (0., "zero"), (-1., "negative")):
        p = g.copy()
        p[0, 0] = val
        row = vector_scalar("invalid_prediction_" + name, p, g)
        check("invalid_full_denominator_" + name, row["absrel"] is None and row["rmse_m"] is None and row["delta1"] == .75)
    row = vector_scalar("empty_gt", np.zeros((1, 3)), np.array([[0., np.nan, np.inf]]))
    check("empty_gt_not_perfect", row["metric_status"] == "EMPTY_GT" and row["delta1"] is None)
    row = vector_scalar("delta1_float64_strict_boundaries", np.array([[.8, 1.25]]), np.ones((1, 2)))
    check("both_exact_boundaries_fail", row["delta1"] == 0)
    row = vector_scalar("delta1_saved_fp32_value", np.array([[.8]], dtype=np.float32), np.ones((1, 1)))
    check("fp32_point8_is_above_exact_point8", row["delta1"] == 1)
    row = vector_scalar("all_predictions_invalid", np.array([[np.nan, -1.]]), np.ones((1, 2)))
    check("all_invalid_delta1_zero", row["delta1"] == 0 and row["prediction_invalid_fraction_on_gt"] == 1)
    grid = np.arange(480 * 640, dtype=np.int32).reshape(480, 640)
    nearest = s.nearest_grid(grid)
    pil = np.asarray(Image.fromarray(grid).resize((512, 384), Image.Resampling.NEAREST))
    check("nearest_matches_PIL_full_640x480", np.array_equal(nearest, pil))
    scalar = np.array([[grid[((2 * y + 1) * 480) // 768, ((2 * x + 1) * 640) // 1024] for x in range(512)] for y in range(384)])
    check("nearest_matches_scalar_full_grid", np.array_equal(nearest, scalar))
    check("uint16_far_depth_preserved", s.nearest_grid(np.full((480, 640), 65535, dtype=np.uint16)).astype(np.float64).min() / 5000 == 13.107)
    old = np.array([[[.1, 1., 13.107]]], dtype=np.float32)
    check("old_exact_bitwise", s.old_depth_check(old, old.copy())["bitwise_equal"])
    roundtrip = np.exp(np.log(old))
    check("old_fp32_logexp_roundtrip", s.old_depth_check(old, roundtrip)["within_tolerance"])
    changed = old.copy()
    changed[0, 0, 1] += 1e-4
    check("old_outside_fixed_tolerance", not s.old_depth_check(old, changed)["within_tolerance"])
    invalidold = old.copy()
    invalidold[0, 0, 0] = 0
    rejects("old_nonpositive_rejected", lambda: s.old_depth_check(old, invalidold), "finite positive")
    a = {"index": 4, **s.depth_metrics(np.array([[2.]]), np.ones((1, 1)))}
    b = {"index": 5, **s.depth_metrics(np.ones((1, 3)), np.ones((1, 3)))}
    agg = s.aggregate([a, b], [4, 5])
    check("equal_frame_not_pixel_pooled", agg["absrel"] == .5 and agg["delta1"] == .5)
    c = {"index": 6, **s.depth_metrics(np.array([[np.nan]]), np.ones((1, 1)))}
    d = {"index": 7, **s.depth_metrics(np.ones((1, 1)), np.ones((1, 1)))}
    agg = s.aggregate([a, b, c, d], s.NEW)
    check("missing_one_metric_invalidates_complete_new4_mean", agg["absrel"] is None and agg["absrel_defined_frames"] == 3 and agg["delta1"] == .5)
    rejects("cannot_omit_prespecified_frame", lambda: s.aggregate([a, b, d], s.NEW), "every fixed ordered frame")
    check_gate("four_complete_producers_gate")
    trace = check_gate("fourth_nonpass_rejected", change_receipt("status", "RUNNING"), "not PASS")
    check("fourth_nonpass_before_any_npz", all(Path(p).name == "receipt.json" for p in trace))
    check_gate("wrong_parent_rejected", change_receipt("manifest_sha256", "b" * 64), "parent mismatch")
    check_gate("wrong_frame_count_rejected", change_receipt("frame_count", 4), "domain mismatch")
    check_gate("wrong_mode_rejected", change_receipt("mode", "cut3r"), "domain mismatch")
    check_gate("tampered_inputseal_rejected", change_seal("frame_count", 4, False), "Input seal SHA mismatch")
    check_gate("producer_sensor_usage_rejected", change_seal("sensor_depth_used", True, True), "Sensor depth prohibited")
    check_gate("resealed_wrong_input_domain_rejected", change_seal("frame_count", 4, True), "metadata mismatch")

    def alter_npz(config, blobs):
        blobs[str(Path(config["producer_dirs"]["filt3r"]) / "output.npz")] += b"tamper"
    check_gate("tampered_fourth_npz_rejected", alter_npz, "NPZ SHA mismatch")
    # Artificial NPZs exercise decode contract with temporarily tiny spatial dimensions.
    original_h, original_w = s.HEIGHT, s.WIDTH
    s.HEIGHT, s.WIDTH = 2, 3
    buffers = {}
    try:
        for mode, n in s.COUNTS.items():
            arr = {"depth": np.ones((n, 2, 3), np.float32), "point_cloud": np.ones((n, 2, 3, 3), np.float32),
                   "conf": np.ones((n, 2, 3), np.float32), "focal": np.ones((n, 1), np.float32),
                   "pp": np.ones((n, 2), np.float32), "c2w": np.repeat(np.eye(4, dtype=np.float32)[None], n, axis=0)}
            if mode == "cut3r":
                arr["depth"][4, 0, 0] = np.nan
            out = io.BytesIO()
            np.savez(out, **arr)
            buffers[mode] = out.getvalue()
        decoded, diag = s.decode_outputs(buffers)
        check("artificial_four_npz_schema", set(decoded) == set(s.COUNTS))
        check("invalid_new_depth_retained_not_filtered", np.isnan(decoded["cut3r"]["depth"][4, 0, 0]) and diag["cut3r"]["depth"]["nonfinite_count"] == 1)
        out = io.BytesIO()
        np.savez(out, depth=np.ones((4, 2, 3), np.float32))
        bad = {**buffers, "common_old": out.getvalue()}
        rejects("missing_auxiliary_keys_rejected", lambda: s.decode_outputs(bad), "Unexpected NPZ keys")
    finally:
        s.HEIGHT, s.WIDTH = original_h, original_w
    with tempfile.TemporaryDirectory(prefix="s26_artificial_") as tmp:
        saved_output = s.OUTPUT
        try:
            s.OUTPUT = Path(tmp)
            rejects("existing_output_refused_before_manifest_read", lambda: s.score("never_open_this_manifest", "a" * 64), "Refuse existing scoring output")
            s.OUTPUT = Path(tmp) / "scoring"
            manifest = Path(tmp) / "artificial_manifest.json"
            manifest.write_text("{}")
            rejects("caller_wrong_manifest_sha_rejected", lambda: s.score(manifest, "a" * 64), "Caller manifest SHA mismatch")
        finally:
            s.OUTPUT = saved_output
    check("no_model_or_ga_modules_imported", not any(k == "torch" or k.startswith("cloud_opt") for k in __import__("sys").modules))
    receipt = {"status": "PASS", "started_utc": t0, "completed_utc": s.utc(), "checks": checks,
               "check_count": len(checks), "scope": "Author artificial numeric/byte fixture checks, not true-data validation or independent experimental audit",
               "source_sha256": s.digest(SOURCE.read_bytes()), "protocol_sha256": s.digest(s.PROTOCOL.read_bytes()),
               "checker_sha256": s.digest(Path(__file__).read_bytes()),
               "true_prediction_array_reads": 0, "sensor_gt_png_byte_reads": 0, "model_runs": 0, "ga_runs": 0,
               "numpy_version": np.__version__, "python_version": __import__("sys").version}
    s.write_json(target, receipt)
    print(json.dumps({k: v for k, v in receipt.items() if k != "checks"}, indent=2))


if __name__ == "__main__":
    main()
