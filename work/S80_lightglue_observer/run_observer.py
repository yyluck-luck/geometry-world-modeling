#!/usr/bin/env python3
"""S80 one-shot saved-image observer diagnostic. No work runs on import.

--self-test uses only synthetic NumPy arrays. --execute is the bounded parent;
--worker is its child. Both require the delivered source and contract hashes.
"""
import argparse
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).absolute().parent
CONTRACT = HERE / "RUN_CONTRACT.json"


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, obj):
    with path.open("x") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())


def event(out, kind, **data):
    with (out / "events.jsonl").open("a") as f:
        f.write(json.dumps({"utc": utc(), "kind": kind, **data}, allow_nan=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def checked_bytes(spec):
    data = Path(spec["path"]).read_bytes()
    if len(data) != spec["bytes"] or sha(data) != spec["sha256"]:
        raise ValueError("Frozen input identity mismatch: " + spec["path"])
    return data


def check_contract(args):
    source = Path(__file__).read_bytes()
    raw = CONTRACT.read_bytes()
    if sha(source) != args.source_sha or sha(raw) != args.contract_sha:
        raise ValueError("Source/contract hash mismatch; do not run changed bytes")
    c = json.loads(raw)
    if c["schema"] != "S80_OBSERVER_DIAGNOSTIC_V1":
        raise ValueError("Unexpected contract schema")
    if len(c["images"]) != 13 or len(c["pairs"]) != 12:
        raise ValueError("All 13 images / 12 pairs are required")
    if Path(args.output).name != args.output or not args.output.startswith("execution_"):
        raise ValueError("Output must be one new execution_* directory under S80")
    return c, HERE / args.output


def array_identity(a):
    import numpy as np
    a = np.ascontiguousarray(a)
    return {"shape": list(a.shape), "dtype": str(a.dtype), "sha256": sha(a.tobytes())}


def save_arrays(path, data):
    import numpy as np
    with path.open("xb") as f:
        np.savez(f, **data)
        f.flush()
        os.fsync(f.fileno())
    return {"path": str(path), "sha256": sha(path.read_bytes()),
            "bytes": path.stat().st_size,
            "arrays": {k: array_identity(v) for k, v in data.items()}}


def quantiles(values):
    import numpy as np
    return np.quantile(values, [.25, .5, .75, .95], method="linear").tolist() if len(values) else None


def geometry(x0, x1, F, anchor_n, eps=1e-12):
    """Two directional point-to-line distances and their mean, never filtering matches."""
    import numpy as np
    p0 = np.column_stack((x0, np.ones(len(x0))))
    p1 = np.column_stack((x1, np.ones(len(x1))))
    l1, l0 = p0 @ F.T, p1 @ F
    numerator = np.abs(np.sum(p1 * l1, axis=1))
    n1, n0 = np.linalg.norm(l1[:, :2], axis=1), np.linalg.norm(l0[:, :2], axis=1)
    valid = np.isfinite(numerator) & np.isfinite(n1) & np.isfinite(n0) & (n1 > eps) & (n0 > eps)
    residuals = np.full((len(x0), 3), np.nan, dtype=np.float64)
    residuals[valid, 0] = numerator[valid] / n1[valid]
    residuals[valid, 1] = numerator[valid] / n0[valid]
    residuals[valid, 2] = residuals[valid, :2].mean(axis=1)
    vals = residuals[valid, 2]
    counts = {str(t): int(np.count_nonzero(vals <= t)) for t in (2, 5, 10)}
    summary = {"valid_count": int(valid.sum()), "invalid_count": int((~valid).sum()),
               "quantiles_q25_q50_q75_q95_px": quantiles(vals),
               "min_px": float(vals.min()) if len(vals) else None,
               "max_px": float(vals.max()) if len(vals) else None,
               "counts_le_px": counts,
               "fraction_of_valid_le_px": {k: v / len(vals) if len(vals) else None for k, v in counts.items()},
               "fraction_of_all_anchor_le_px": {k: v / anchor_n if anchor_n else None for k, v in counts.items()}}
    return residuals, valid, summary


def coverage(x, size):
    import numpy as np
    if not len(x):
        return {"occupied_4x4_cells": 0, "span_xy_fraction": None}
    ij = np.clip(np.floor(x / np.asarray(size) * 4).astype(int), 0, 3)
    return {"occupied_4x4_cells": int(len(np.unique(ij, axis=0))),
            "span_xy_fraction": ((x.max(0) - x.min(0)) / np.asarray(size)).tolist()}


def mutual_ratio(ids0, dist0, ids1, dist1, ratio):
    """Strict ratio in both directions, then mutual nearest-neighbor identity."""
    import numpy as np
    n, m = len(ids0), len(ids1)
    a, b = np.full(n, -1, np.int64), np.full(m, -1, np.int64)
    good0 = (ids0[:, 1] >= 0) & (dist0[:, 0] < ratio * dist0[:, 1])
    good1 = (ids1[:, 1] >= 0) & (dist1[:, 0] < ratio * dist1[:, 1])
    for i in np.flatnonzero(good0):
        j = int(ids0[i, 0])
        if 0 <= j < m and good1[j] and int(ids1[j, 0]) == int(i):
            a[i], b[j] = j, i
    return a, b


def bf_match(d0, d1, ratio):
    import cv2
    import numpy as np
    bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)
    def neighbors(a, b):
        ids = np.full((len(a), 2), -1, dtype=np.int64)
        distances = np.full((len(a), 2), np.nan, dtype=np.float32)
        if len(a) and len(b):
            for row in bf.knnMatch(a, b, k=min(2, len(b))):
                for k, match in enumerate(row):
                    ids[match.queryIdx, k] = match.trainIdx
                    distances[match.queryIdx, k] = match.distance
        return ids, distances
    ids0, dist0 = neighbors(d0, d1)
    ids1, dist1 = neighbors(d1, d0)
    m0, m1 = mutual_ratio(ids0, dist0, ids1, dist1, ratio)
    return {"matches0": m0, "matches1": m1,
            "matching_scores0": dist0[:, 0].copy(), "matching_scores1": dist1[:, 0].copy(),
            "knn_ids0": ids0, "knn_ids1": ids1,
            "knn_l2_distances0": dist0, "knn_l2_distances1": dist1}


def accepted_pairs(data, n, m):
    import numpy as np
    a, b = data["matches0"], data["matches1"]
    if a.shape != (n,) or b.shape != (m,) or a.dtype.kind not in "iu" or b.dtype.kind not in "iu":
        raise ValueError("Invalid match vector shapes/dtypes")
    if np.any((a < -1) | (a >= m)) or np.any((b < -1) | (b >= n)):
        raise ValueError("Out-of-range match index")
    i = np.flatnonzero(a >= 0)
    j = a[i]
    if not np.array_equal(b[j], i) or len(np.flatnonzero(b >= 0)) != len(i):
        raise ValueError("Nonreciprocal match vectors")
    for k, size in (("matching_scores0", n), ("matching_scores1", m)):
        if data[k].shape != (size,):
            raise ValueError("Invalid score vector shape")
    return np.column_stack((i, j)).astype(np.int64)


def validate_feature(feat):
    import numpy as np
    n = len(feat["keypoints"])
    shapes = {"keypoints": (n, 2), "descriptors": (n, 128), "scales": (n,),
              "oris": (n,), "image_size": (2,), "keypoint_scores": (n,)}
    if n > 1500 or set(feat) != set(shapes):
        raise ValueError("Unexpected official SIFT feature fields/count")
    for k, shape in shapes.items():
        if feat[k].shape != shape or feat[k].dtype != np.float32 or not np.isfinite(feat[k]).all():
            raise ValueError("Malformed or nonfinite feature: " + k)
    if not np.array_equal(feat["image_size"], [576, 576]):
        raise ValueError("Unexpected native image size")
    return n


def worker(c, out, args):
    started, tick = utc(), time.monotonic()
    counts = {"image_read_attempts": 0, "images_read_and_identity_verified": 0, "sift_extract_attempts": 0, "sift_extract_successes": 0,
              "bf_pair_attempts": 0, "lightglue_forward_attempts": 0, "lightglue_forward_successes": 0}
    rows, feature_meta = [], {}
    try:
        for spec in c["official_source_files"]:
            checked_bytes(spec)
        camera_data = json.loads(checked_bytes(c["geometry_receipt"]))
        Fs = {int(p["target_id"]): p["Fraw"] for p in camera_data["pairs"]}
        if set(Fs) != {20, 21, 22, 23}:
            raise ValueError("Fixed S72 geometry targets mismatch")
        sys.path[:0] = [c["source_dir"], c["overlay"]]
        import importlib.metadata as metadata
        import random
        import cv2
        import numpy as np
        import torch
        from PIL import Image
        import lightglue.sift as sift_module
        from lightglue import LightGlue, SIFT
        from lightglue.utils import numpy_image_to_torch
        if str(Path(sift_module.__file__).resolve()) != str(Path(c["source_dir"]) / "lightglue/sift.py"):
            raise ValueError("Unexpected imported LightGlue source")
        versions = {k: metadata.version(k) for k in c["versions"]}
        if versions != c["versions"] or sys.version_info[:2] != (3, 12):
            raise ValueError("Runtime versions differ from frozen contract")
        torch.set_num_threads(c["resources"]["torch_threads"])
        torch.set_num_interop_threads(1)
        cv2.setNumThreads(1)
        cv2.setRNGSeed(80)
        random.seed(80)
        np.random.seed(80)
        torch.manual_seed(80)
        torch.set_grad_enabled(False)
        def forbidden_download(*unused, **unused_kw):
            raise RuntimeError("Implicit torch.hub weight download is forbidden")
        torch.hub.load_state_dict_from_url = forbidden_download
        extractor = SIFT(**c["sift"]).eval().cpu()
        matcher = LightGlue(features=None, **c["lightglue"]).eval().float().cpu()
        state = torch.load(io.BytesIO(checked_bytes(c["weights"])), map_location="cpu", weights_only=True)
        for i in range(c["lightglue"]["n_layers"]):
            state = {k.replace(f"self_attn.{i}", f"transformers.{i}.self_attn"): v for k, v in state.items()}
            state = {k.replace(f"cross_attn.{i}", f"transformers.{i}.cross_attn"): v for k, v in state.items()}
        incompatible = matcher.load_state_dict(state, strict=False)
        if sorted(incompatible.missing_keys) != ["confidence_thresholds"] or incompatible.unexpected_keys:
            raise ValueError("Weight key coverage mismatch")
        parameters = {}
        for name, p in matcher.named_parameters():
            if name not in state or p.dtype != torch.float32 or not torch.equal(p, state[name]):
                raise ValueError("Learned parameter not loaded exactly: " + name)
            parameters[name] = array_identity(p.detach().numpy())
        write_json(out / "COMPONENT_RECEIPT.json", {
            "utc": utc(), "versions": versions, "python": sys.version,
            "source_dir": c["source_dir"], "sift_conf": vars(extractor.conf),
            "lightglue_conf": vars(matcher.conf), "device": "cpu", "dtype": "float32",
            "missing_keys": incompatible.missing_keys, "unexpected_keys": incompatible.unexpected_keys,
            "confidence_thresholds": matcher.confidence_thresholds.tolist(),
            "parameter_count": sum(p.numel() for p in matcher.parameters()), "parameters": parameters,
            "torch_threads": torch.get_num_threads(), "opencv_threads": cv2.getNumThreads(),
            "weights_sha256": c["weights"]["sha256"], "model_forward_calls_at_receipt": 0})
        del state
        features = {}
        for spec in c["images"]:
            key = spec["id"]
            event(out, "feature_started", image_id=key)
            try:
                counts["image_read_attempts"] += 1
                data = checked_bytes(spec)
                counts["images_read_and_identity_verified"] += 1
                with Image.open(io.BytesIO(data)) as im:
                    if im.format != "PNG" or im.mode != "RGB" or im.size != (576, 576):
                        raise ValueError("Expected native RGB 576 PNG")
                    pixels = np.asarray(im).copy()
                image = numpy_image_to_torch(pixels)
                counts["sift_extract_attempts"] += 1
                event(out, "sift_extract_call", image_id=key, attempt=counts["sift_extract_attempts"])
                with torch.inference_mode():
                    result = extractor.extract(image, resize=None)
                feat = {k: v[0].detach().cpu().numpy().copy() for k, v in result.items()}
                n = validate_feature(feat)
                counts["sift_extract_successes"] += 1
                saved = save_arrays(out / "features" / (key + ".npz"), feat)
                features[key] = feat
                feature_meta[key] = {"status": "AVAILABLE" if n else "EMPTY_FEATURE_SET", "N": n,
                                     "input_sha256": spec["sha256"], "saved": saved}
                del pixels, image, result
            except Exception as e:
                features[key] = None
                feature_meta[key] = {"status": "EXTRACTION_ERROR", "N": None,
                                     "error_type": type(e).__name__, "error": str(e), "traceback": traceback.format_exc()}
            write_json(out / "features" / (key + ".json"), feature_meta[key])
            event(out, "feature_finished", image_id=key, status=feature_meta[key]["status"])
        write_json(out / "FEATURE_MANIFEST.json", feature_meta)
        for pair in c["pairs"]:
            src, dst = pair["source_id"], pair["target_image_id"]
            f0, f1 = features[src], features[dst]
            n, m = feature_meta[src]["N"], feature_meta[dst]["N"]
            for method in ("BF", "LG"):
                row_id = pair["id"] + "_" + method
                row = {"row_id": row_id, **pair, "matcher": method, "N_source": n, "N_target": m,
                       "source_feature_file_sha256": feature_meta[src].get("saved", {}).get("sha256"),
                       "target_feature_file_sha256": feature_meta[dst].get("saved", {}).get("sha256"),
                       "M": None, "correct": None, "wrong": None, "new_method_validated": False}
                event(out, "pair_started", row_id=row_id)
                pair_tick = time.monotonic()
                try:
                    if f0 is None or f1 is None or n == 0 or m == 0:
                        row.update(status="MISSING_FEATURES", reason={src: feature_meta[src]["status"], dst: feature_meta[dst]["status"]})
                    else:
                        if method == "BF":
                            counts["bf_pair_attempts"] += 1
                            arr = bf_match(f0["descriptors"], f1["descriptors"], c["bf"]["ratio"])
                            row["score_semantics"] = "Raw nearest-neighbor L2 distance (lower is closer), not probability; rejected points may have finite scores."
                        else:
                            def tensors(feat):
                                return {k: torch.from_numpy(v.copy())[None] for k, v in feat.items()}
                            counts["lightglue_forward_attempts"] += 1
                            event(out, "lightglue_forward_call", row_id=row_id, attempt=counts["lightglue_forward_attempts"])
                            with torch.inference_mode():
                                pred = matcher({"image0": tensors(f0), "image1": tensors(f1)})
                            counts["lightglue_forward_successes"] += 1
                            arr = {k: v[0].detach().cpu().numpy().copy() for k, v in pred.items() if k != "stop"}
                            row["stop_layer"] = int(pred["stop"])
                            if row["stop_layer"] != 9:
                                raise ValueError("Unexpected adaptive/early stop")
                            row["score_semantics"] = "Official LightGlue assignment scores; positive scores can remain on rejected indices."
                            del pred
                        row["raw_matcher_saved"] = save_arrays(out / "pairs" / (row_id + "_raw_matcher.npz"), arr)
                        if method == "LG" and any(not np.isfinite(arr[k]).all() for k in ("matching_scores0", "matching_scores1")):
                            raise ValueError("Nonfinite LightGlue score output")
                        matches = accepted_pairs(arr, n, m)
                        if method == "LG" and not np.array_equal(arr["matches"], matches):
                            raise ValueError("Compact/full LightGlue index disagreement")
                        arr["accepted_indices"] = matches
                        x0, x1 = f0["keypoints"][matches[:, 0]].astype(np.float64), f1["keypoints"][matches[:, 1]].astype(np.float64)
                        arr["source_xy"], arr["target_xy"] = x0, x1
                        for label, target in (("correct", pair["target_id"]), ("wrong", pair["wrong_target_id"])):
                            F = np.asarray(Fs[target], dtype=np.float64)
                            residual, valid, stats = geometry(x0, x1, F, n, c["geometry"]["line_norm_epsilon"])
                            arr[label + "_F"], arr[label + "_residuals"], arr[label + "_valid"] = F, residual, valid
                            row[label] = stats
                        both = arr["correct_valid"] & arr["wrong_valid"]
                        paired = np.full(len(matches), np.nan)
                        paired[both] = arr["wrong_residuals"][both, 2] - arr["correct_residuals"][both, 2]
                        arr["wrong_minus_correct_px"], arr["joint_valid"] = paired, both
                        row.update(status="COMPUTED_DESCRIPTIVE" if len(matches) else "EMPTY_MATCH_SET",
                                   M=len(matches), unmatched_source=n-len(matches), unmatched_target=m-len(matches),
                                   matched_fraction_source=len(matches)/n, matched_fraction_target=len(matches)/m,
                                   source_coverage=coverage(x0, f0["image_size"]), target_coverage=coverage(x1, f1["image_size"]),
                                   source_all_feature_coverage=coverage(f0["keypoints"], f0["image_size"]),
                                   target_all_feature_coverage=coverage(f1["keypoints"], f1["image_size"]),
                                   joint_valid_count=int(both.sum()), paired_wrong_minus_correct_quantiles_px=quantiles(paired[both]),
                                   paired_positive_count=int(np.count_nonzero(paired[both] > 0)),
                                   paired_zero_count=int(np.count_nonzero(paired[both] == 0)),
                                   paired_negative_count=int(np.count_nonzero(paired[both] < 0)))
                        row["saved"] = save_arrays(out / "pairs" / (row_id + ".npz"), arr)
                except Exception as e:
                    row.update(status="PAIR_ERROR", error_type=type(e).__name__, error=str(e), traceback=traceback.format_exc())
                row["elapsed_seconds"] = time.monotonic() - pair_tick
                row["completed_utc"] = utc()
                write_json(out / "pairs" / (row_id + ".json"), row)
                rows.append(row)
                event(out, "pair_finished", row_id=row_id, status=row["status"])
        missing = [r["row_id"] for r in rows if r["status"] in ("PAIR_ERROR", "MISSING_FEATURES")]
        status = "COMPLETE_DESCRIPTIVE_WITH_MISSING" if missing else "COMPLETE_DESCRIPTIVE_ONLY"
        write_json(out / "ROWS.json", rows)
        write_json(out / "receipt.json", {"started_utc": started, "completed_utc": utc(), "elapsed_seconds": time.monotonic()-tick,
            "status": status, "counts": counts, "expected_rows": 24, "actual_rows": len(rows), "missing_rows": missing,
            "contract_sha256": args.contract_sha, "source_sha256": args.source_sha,
            "new_method_validated": False, "old_experiments_modified": False})
        return 2 if missing else 0
    except BaseException as e:
        write_json(out / "WORKER_FAILURE.json", {"started_utc": started, "failed_utc": utc(), "elapsed_seconds": time.monotonic()-tick,
            "error_type": type(e).__name__, "error": str(e), "traceback": traceback.format_exc(), "counts": counts,
            "completed_rows": len(rows), "new_method_validated": False})
        return 1


def process_tree_rss(pid):
    result = subprocess.run(["/bin/ps", "-axo", "pid=,ppid=,rss="], capture_output=True, text=True, check=True, timeout=5)
    entries = [tuple(map(int, line.split())) for line in result.stdout.splitlines() if line.strip()]
    descendants = {pid}
    while True:
        expanded = descendants | {p for p, parent, rss in entries if parent in descendants}
        if expanded == descendants:
            break
        descendants = expanded
    return sum(rss * 1024 for p, parent, rss in entries if p in descendants)


def supervise(c, out, args):
    out.mkdir()  # refuse to overwrite/resume any prior attempt
    (out / "features").mkdir()
    (out / "pairs").mkdir()
    started, tick, peak, samples, stop = utc(), time.monotonic(), 0, 0, None
    env = dict(os.environ)
    env.update(PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1", OMP_NUM_THREADS="2", MKL_NUM_THREADS="2",
               OPENBLAS_NUM_THREADS="2", VECLIB_MAXIMUM_THREADS="2", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    argv = [c["python"], "-B", str(Path(__file__).absolute()), "--worker", "--contract-sha", args.contract_sha,
            "--source-sha", args.source_sha, "--output", args.output]
    with (out / "worker.stdout.txt").open("x") as stdout, (out / "worker.stderr.txt").open("x") as stderr:
        p = subprocess.Popen(argv, cwd=c["project_root"], env=env, stdout=stdout, stderr=stderr, start_new_session=True)
        try:
            write_json(out / "STARTED.json", {"utc": started, "pid": p.pid, "argv": argv,
                "contract_sha256": args.contract_sha, "source_sha256": args.source_sha, "resources": c["resources"]})
            with (out / "monitor.jsonl").open("x") as monitor:
                while p.poll() is None:
                    elapsed = time.monotonic() - tick
                    rss = process_tree_rss(p.pid)
                    peak, samples = max(peak, rss), samples + 1
                    monitor.write(json.dumps({"utc": utc(), "elapsed_seconds": elapsed, "rss_bytes": rss}) + "\n")
                    monitor.flush()
                    if elapsed >= c["resources"]["wall_seconds"]:
                        stop = "WALL_TIMEOUT"
                    elif rss > c["resources"]["rss_stop_bytes"]:
                        stop = "SAMPLED_RSS_LIMIT"
                    if stop:
                        break
                    time.sleep(c["resources"]["sample_seconds"])
        except BaseException as e:
            stop = "SUPERVISOR_ERROR: " + type(e).__name__ + ": " + str(e)
        if stop and p.poll() is None:
            try:
                os.killpg(p.pid, signal.SIGTERM)
                p.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        rc = p.wait()
        if stop is None and time.monotonic() - tick > c["resources"]["wall_seconds"]:
            stop = "WALL_BUDGET_OVERRUN_AT_EXIT"
    write_json(out / "EXTERNAL_RECEIPT.json", {"started_utc": started, "completed_utc": utc(),
        "elapsed_seconds": time.monotonic()-tick, "returncode": rc, "stop_reason": stop,
        "peak_sampled_process_tree_rss_bytes": peak, "monitor_samples": samples,
        "rss_scope": "Worker process tree sampled every 0.5 s plus ps overhead; not an instantaneous hard RSS guarantee.",
        "new_method_validated": False})
    return rc if rc else (1 if stop else 0)


def self_test():
    import numpy as np
    F = np.array([[0., 0., 0.], [0., 0., -1.], [0., 1., 0.]])
    x0, x1 = np.array([[1., 5.], [2., 5.]]), np.array([[3., 8.], [4., 5.]])
    r, valid, s = geometry(x0, x1, F, 4)
    assert np.array_equal(r, [[3., 3., 3.], [0., 0., 0.]]) and valid.all()
    assert s["counts_le_px"] == {"2": 1, "5": 2, "10": 2}
    assert s["fraction_of_all_anchor_le_px"]["2"] == .25
    assert np.array_equal(geometry(x0, x1, -7 * F, 4)[0], r)
    assert not geometry(x0, x1, np.zeros((3, 3)), 4)[1].any()
    assert geometry(np.empty((0, 2)), np.empty((0, 2)), F, 4)[2]["quantiles_q25_q50_q75_q95_px"] is None
    assert quantiles(np.array([1., 3., 5., 7.])) == [2.5, 4., 5.5, 6.699999999999999]
    ids = np.array([[0, 1], [1, 0]], dtype=np.int64)
    d = np.array([[1., 2.], [1.5, 2.]])
    a, b = mutual_ratio(ids, d, ids, d, .75)
    assert a.tolist() == [0, -1] and b.tolist() == [0, -1]  # equality .75 is rejected
    assert mutual_ratio(ids, np.zeros((2, 2)), ids, np.zeros((2, 2)), .75)[0].tolist() == [-1, -1]
    a2, b2 = mutual_ratio(ids, np.array([[1., 2.], [1., 2.]]), ids[::-1], np.array([[1., 2.], [1., 2.]]), .75)
    assert (a2 == -1).all() and (b2 == -1).all()  # both ratios pass, reciprocal identity fails
    matches = accepted_pairs({"matches0": a, "matches1": b, "matching_scores0": np.array([.2, .9]),
                              "matching_scores1": np.array([.2, .9])}, 2, 2)
    assert matches.tolist() == [[0, 0]]  # positive rejected score must not create a match
    assert coverage(np.array([[0., 0.], [575., 575.]]), [576, 576])["occupied_4x4_cells"] == 2
    print(json.dumps({"status": "SYNTHETIC_SELFTEST_PASS", "utc": utc(), "numpy": np.__version__,
                      "images_read": 0, "models_loaded": 0, "sift_extract_calls": 0, "lightglue_forward_calls": 0}))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    modes = ap.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test", action="store_true")
    modes.add_argument("--execute", action="store_true")
    modes.add_argument("--worker", action="store_true")
    ap.add_argument("--contract-sha")
    ap.add_argument("--source-sha")
    ap.add_argument("--output", default="execution_01")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    c, out = check_contract(args)
    return worker(c, out, args) if args.worker else supervise(c, out, args)


if __name__ == "__main__":
    raise SystemExit(main())
