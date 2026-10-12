#!/usr/bin/env python3
"""Independent post-score arithmetic check; no model/scorer imports.

Refuses to read measurements unless the complete candidate seal AND scored
RESULTS.json exist and their identities agree. The window is preselected in
source code, not selected after inspecting outcomes.
"""
import argparse
import hashlib
import io
import json
import math
import os
from pathlib import Path
import tempfile

import numpy as np

WINDOW = "scene_13__w0000"
ATOL = 1e-10


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def ensure(value, message):
    if not value:
        raise AssertionError(message)


def read_json(path):
    return json.loads(Path(path).read_text())


class Comparison:
    def __init__(self):
        self.count = 0
        self.max_error = 0.

    def exact(self, actual, expected, name):
        self.count += 1
        ensure(actual == expected, f"{name}: {actual!r} != {expected!r}")

    def numeric(self, actual, expected, name):
        a, b = np.asarray(actual, dtype=float), np.asarray(expected, dtype=float)
        self.count += 1
        ensure(a.shape == b.shape, f"{name}: shape mismatch")
        ensure(np.isfinite(a).all() and np.isfinite(b).all(), f"{name}: nonfinite comparison")
        error = float(np.max(np.abs(a - b))) if a.size else 0.
        self.max_error = max(self.max_error, error)
        ensure(error <= ATOL, f"{name}: absolute error {error:.17g} exceeds {ATOL}")


def authorize_measurements(stage):
    # This check must precede any depth, pose, intrinsics or candidate-array read.
    seal_path, result_path = stage / "CANDIDATE_SEAL.json", stage / "scores/RESULTS.json"
    ensure(seal_path.is_file() and result_path.is_file(),
           "REFUSED: both CANDIDATE_SEAL.json and scores/RESULTS.json must exist before measurement access")
    seal, result = read_json(seal_path), read_json(result_path)
    ensure(result["status"] == "COMPLETE", "REFUSED: scores are not complete")
    ensure(result["seal_sha256"] == digest(seal_path), "REFUSED: result/seal mismatch")
    ensure(seal["ground_truth_opened"] is False, "REFUSED: prediction seal boundary mismatch")
    for name, key in (("MANIFEST.json", "manifest_sha256"), ("PROTOCOL.md", "protocol_sha256")):
        ensure(digest(stage / name) == seal[key] == result[key], "REFUSED: changed " + name)
    freeze_path = stage / "FREEZE.json"
    ensure(digest(freeze_path) == seal["freeze_sha256"], "REFUSED: changed freeze")
    freeze = read_json(freeze_path)
    for name, expected in freeze["files"].items():
        ensure(digest(stage / name) == expected, "REFUSED: frozen file changed: " + name)
    manifest = read_json(stage / "MANIFEST.json")
    expected = {w["window_id"] + "__" + c["candidate_id"] + ".npz"
                for w in manifest["windows"] for c in manifest["candidates"]}
    ensure(len(seal["records"]) == len(expected) and {r["npz"] for r in seal["records"]} == expected,
           "REFUSED: incomplete candidate seal")
    for record in seal["records"]:
        for name, key in (("npz", "npz_sha256"), ("receipt", "receipt_sha256")):
            ensure(Path(record[name]).name == record[name], "REFUSED: unsafe seal filename")
            ensure(digest(stage / "candidates" / record[name]) == record[key], "REFUSED: candidate bytes changed")
    ensure(seal["sealed_utc"] <= result["scored_utc"], "REFUSED: invalid chronology")
    return manifest, result


def interior_mask(depth):
    finite_positive = np.isfinite(depth) & (depth > 0) & (depth < 10)
    keep = finite_positive.copy()
    for axis, shift in ((0, 1), (0, -1), (1, 1), (1, -1)):
        neighbor = np.roll(depth, shift, axis=axis)
        keep &= np.roll(finite_positive, shift, axis=axis) & (np.abs(depth - neighbor) <= .05)
    keep[[0, -1], :] = False
    keep[:, [0, -1]] = False
    return keep


def camera_projection(pixels, depths, source_pose, target_pose, K):
    """Compose a camera-to-camera affine transform, then project each point."""
    rays = np.vstack(((pixels[:, 0] - K[0, 2]) / K[0, 0],
                      (pixels[:, 1] - K[1, 2]) / K[1, 1], np.ones(len(pixels))))
    rotation = target_pose[:3, :3].T @ source_pose[:3, :3]
    translation = target_pose[:3, :3].T @ (source_pose[:3, 3] - target_pose[:3, 3])
    with np.errstate(invalid="ignore", divide="ignore", over="ignore"):
        xyz = rotation @ (rays * depths) + translation[:, None]
        uv = np.column_stack((K[0, 0] * xyz[0] / xyz[2] + K[0, 2],
                              K[1, 1] * xyz[1] / xyz[2] + K[1, 2]))
    valid = np.isfinite(uv).all(axis=1) & np.isfinite(xyz[2]) & (xyz[2] > 0)
    valid &= (uv[:, 0] >= 0) & (uv[:, 0] < 640) & (uv[:, 1] >= 0) & (uv[:, 1] < 480)
    return uv, xyz[2], valid


def independent_window(stage, data_root, manifest, result, check):
    from PIL import Image
    window = next(w for w in manifest["windows"] if w["window_id"] == WINDOW)
    reported = next(row for row in result["rows"] if row["window_id"] == WINDOW)["primary"]
    scoring = manifest["scoring"]
    check.exact(scoring["stride"], 4, "frozen stride")
    check.numeric([scoring["depth_max_m"], scoring["depth_edge_m"], scoring["visibility_m"],
                   scoring["invalid_projection_penalty"]], [10., .05, .05, 1.], "frozen measurement rules")
    pixels = np.array([(u, v) for v in range(0, 480, 4) for u in range(0, 640, 4)])
    # Exact historical floating-point expression, including round-to-nearest-even.
    x = np.rint(((pixels[:, 0] + .5) * 1.2 - 96) * 512 / 576 - .5).astype(int)
    y = np.rint((pixels[:, 1] + .5) * 1.2 * 512 / 576 - 64 - .5).astype(int)
    crop = (x >= 0) & (x < 512) & (y >= 0) & (y < 384)
    pixels, x, y = pixels[crop], x[crop], y[crop]
    candidates = []
    K = None
    for candidate in manifest["candidates"]:
        path = stage / "candidates" / (WINDOW + "__" + candidate["candidate_id"] + ".npz")
        with np.load(path, allow_pickle=False) as arrays:
            check.exact(arrays["source_refs"].tolist(), window["source_refs"], "candidate source identities")
            check.exact(arrays["candidate_order"].tolist(), candidate["order"], "candidate source order")
            candidates.append(arrays["depths"][:, y, x].astype(float))
            if K is None:
                K = arrays["K"].copy()
            else:
                check.numeric(arrays["K"], K, "candidate K agreement")
    check.exact(len(candidates), 4, "candidate count")
    data_hashes = {}

    def measurement(reference):
        seq, frame = reference.split("/")
        base = Path(window["scene_rel"]) / seq / ("frame-" + frame)
        blobs = []
        for suffix in (".depth.png", ".pose.txt"):
            relative = str(base) + suffix
            content = (data_root / relative).read_bytes()
            h = hashlib.sha256(content).hexdigest()
            check.exact(h, result["measurement_input_hashes"][relative], "sensor input hash")
            data_hashes[relative] = h
            blobs.append(content)
        with Image.open(io.BytesIO(blobs[0])) as image:
            depth = np.array(image, dtype=float) / 1000.
        pose = np.loadtxt(io.BytesIO(blobs[1])).reshape(4, 4)
        return depth, pose, interior_mask(depth)

    sources = [measurement(ref) for ref in window["source_refs"]]
    targets = [measurement(ref) for ref in window["target_refs"]]
    support_counts, all_losses, all_invalid, target_labels = [], [], [], []
    for si, (source_depth, source_pose, source_mask) in enumerate(sources):
        measured = source_depth[pixels[:, 1], pixels[:, 0]]
        source_ok = source_mask[pixels[:, 1], pixels[:, 0]]
        for ti, (target_depth, target_pose, target_mask) in enumerate(targets):
            uv_true, z_true, visible = camera_projection(pixels, measured, source_pose, target_pose, K)
            indices = np.flatnonzero(source_ok & visible)
            rounded = np.rint(uv_true[indices]).astype(int)
            bounded = ((rounded[:, 0] >= 0) & (rounded[:, 0] < 640)
                       & (rounded[:, 1] >= 0) & (rounded[:, 1] < 480))
            indices, rounded = indices[bounded], rounded[bounded]
            in_target = target_mask[rounded[:, 1], rounded[:, 0]]
            depth_agreement = np.abs(target_depth[rounded[:, 1], rounded[:, 0]] - z_true[indices]) <= .05
            indices = indices[in_target & depth_agreement]
            support_counts.append({"source": si, "target": ti, "tuples": int(len(indices))})
            losses, invalids = [], []
            for candidate in candidates:
                predicted = candidate[si, indices]
                uv, _, in_image = camera_projection(pixels[indices], predicted, source_pose, target_pose, K)
                good = np.isfinite(predicted) & (predicted > 0) & in_image
                error = np.ones(len(indices), dtype=float)
                delta = uv[good] - uv_true[indices[good]]
                error[good] = np.minimum(np.sqrt(np.sum(delta * delta, axis=1)) / math.hypot(640, 480), 1.)
                losses.append(error)
                invalids.append(~good)
            all_losses.append(np.array(losses))
            all_invalid.append(np.array(invalids))
            target_labels.extend([ti] * len(indices))
    losses = np.concatenate(all_losses, axis=1)
    invalids = np.concatenate(all_invalid, axis=1)
    target_labels = np.asarray(target_labels)
    check.exact(support_counts, reported["support_counts"], "native source-target support counts")
    check.exact(losses.shape[1], reported["tuple_count"], "whole-window tuple count")
    means = [math.fsum(row) / len(row) for row in losses]
    per_target = []
    for ti in range(len(targets)):
        subset = losses[:, target_labels == ti]
        if subset.shape[1]:
            per_target.append(min(math.fsum(row) for row in subset))
    computed = {"fixed_errors": means, "complete_oracle": min(means),
                "complete_oracle_index": int(np.argmin(means)),
                "per_target_oracle": math.fsum(per_target) / losses.shape[1],
                "per_tuple_oracle": math.fsum(np.min(losses, axis=0)) / losses.shape[1],
                "invalid_projection_fraction": [int(np.sum(row)) / len(row) for row in invalids]}
    for key, value in computed.items():
        if key == "complete_oracle_index":
            check.exact(value, reported["candidate"][key], "window " + key)
        else:
            check.numeric(value, reported["candidate"][key], "window " + key)
    return {"window_id": WINDOW, "tuple_count": losses.shape[1], "candidate": computed,
            "support_counts": support_counts, "measurement_hashes": data_hashes}


def arithmetic_aggregate(rows, stratum="primary"):
    n = len(rows)

    def average(family, key, index=None):
        values = [row[stratum][family][key] for row in rows]
        if index is not None:
            values = [value[index] for value in values]
        return math.fsum(values) / n

    fixed = [average("candidate", "fixed_errors", i) for i in range(4)]
    oracle = average("candidate", "complete_oracle")
    fusion = average("single_controls", "fixed_errors", 0)
    medoid = average("single_controls", "fixed_errors", 1)
    scale = average("scale", "complete_oracle")
    normalized = average("normalized", "complete_oracle")
    return {"windows": n, "fixed_errors": fixed, "fixed_capped_epe_pixels": [800 * x for x in fixed],
            "complete_oracle": oracle, "complete_oracle_capped_epe_pixels": 800 * oracle,
            "fusion_error": fusion, "medoid_error": medoid,
            "scale_oracle": scale, "normalized_oracle": normalized,
            "per_target_oracle": average("candidate", "per_target_oracle"),
            "per_tuple_oracle": average("candidate", "per_tuple_oracle"),
            "headroom_vs_c0": 1 - oracle / fixed[0],
            "best_fixed_order_index": fixed.index(min(fixed)),
            "gain_vs_best_fixed_order": 1 - oracle / min(fixed),
            "gain_vs_better_single_control": 1 - oracle / min(fusion, medoid),
            "gain_vs_scale_oracle": 1 - oracle / scale,
            "normalized_headroom_vs_c0": 1 - normalized / fixed[0]}


def check_aggregates(manifest, result, check):
    rows = result["rows"]
    check.exact([r["window_id"] for r in rows], [w["window_id"] for w in manifest["windows"]], "all window identities")
    summaries = {"primary": arithmetic_aggregate(rows), "secondary": arithmetic_aggregate(rows, "secondary")}
    scenes = {scene: arithmetic_aggregate([row for row in rows if row["scene"] == scene])
              for scene in sorted({row["scene"] for row in rows})}
    for name, summary in list(summaries.items()) + [("scene:" + s, value) for s, value in scenes.items()]:
        expected = result["primary_by_scene"][name.split(":", 1)[1]] if name.startswith("scene:") else result[name]
        for key, value in summary.items():
            check.numeric(value, expected[key], name + ":" + key)
    primary = summaries["primary"]
    gates = [(primary["headroom_vs_c0"] < .10, "whole_clip_headroom_below_10_percent"),
             (any(s["headroom_vs_c0"] <= 0 for s in scenes.values()), "not_positive_in_both_scenes"),
             (primary["gain_vs_better_single_control"] < .05, "gain_over_single_controls_below_5_percent"),
             (primary["gain_vs_best_fixed_order"] < .05, "gain_over_best_fixed_order_below_5_percent"),
             (primary["gain_vs_scale_oracle"] < .05, "gain_over_scale_oracle_below_5_percent"),
             (primary["normalized_headroom_vs_c0"] < .10, "normalized_headroom_below_10_percent")]
    failed = [reason for condition, reason in gates if condition]
    decision = "STOP_TESTED_FAMILY" if failed else "GO_TO_CONSUMER_PILOT"
    check.exact(failed, result["failed_gates"], "failed gate list")
    check.exact(decision, result["verdict"], "gate verdict")
    return {**summaries, "primary_by_scene": scenes, "verdict": decision, "failed_gates": failed}


def save_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".independent-check-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(value, handle, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temp, path)
    finally:
        Path(temp).unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True, type=Path)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    ensure(not args.out.exists(), "Refusing to overwrite an earlier independent check")
    comparison = Comparison()
    try:
        manifest, result = authorize_measurements(args.stage)
        window = independent_window(args.stage, args.data_root, manifest, result, comparison)
        aggregates = check_aggregates(manifest, result, comparison)
        output = {"status": "NUMERICAL_AGREEMENT", "checked_window": WINDOW,
                  "checks": comparison.count, "max_absolute_difference": comparison.max_error,
                  "absolute_tolerance": ATOL, "independent_checker_sha256": digest(__file__),
                  "results_sha256": digest(args.stage / "scores/RESULTS.json"),
                  "seal_sha256": digest(args.stage / "CANDIDATE_SEAL.json"),
                  "window": window, "aggregates": aggregates}
        save_new(args.out, output)
        print(json.dumps({key: output[key] for key in ("status", "checked_window", "checks", "max_absolute_difference")}))
        return 0
    except Exception as error:
        failure = {"status": "FAILURE", "checked_window": WINDOW,
                   "error": type(error).__name__ + ": " + str(error),
                   "checks": comparison.count, "max_absolute_difference": comparison.max_error,
                   "independent_checker_sha256": digest(__file__)}
        save_new(args.out, failure)
        print(json.dumps(failure))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
