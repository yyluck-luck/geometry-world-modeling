#!/usr/bin/env python3
"""S15B fixed two-hypothesis photo costs. No model, depth answers or target RGB."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import resource
import signal
import sys
import time
import traceback

import numpy as np
from PIL import Image, __version__ as PIL_VERSION

SOURCE_IDS = [0, 3, 6, 9]
WITNESS_IDS = list(range(12, 20))
SIZE = 224
PATCH = 16
SENTINEL = 255
NPZ_KEYS = {"old_self_z", "new_self_z", "source_c2w", "witness_c2w", "K", "scale_model_per_meter"}
CONTRACT = {
    "source_ids": SOURCE_IDS, "witness_ids": WITNESS_IDS,
    "input_size": [640, 480], "resize": [299, 224], "crop": [37, 0, 261, 224],
    "image_transform": "PIL RGB; LANCZOS resize; crop; PIL L",
    "census": "5x5 row-major excluding center; neighbor < center; 24 bits",
    "projection": "physical pinhole; float64; floor(pixel+0.5)",
    "source_center_min": 2, "source_center_max": 221,
    "witness_center_min": 2, "witness_center_max": 221,
    "support": "both hypotheses finite positive source z and witness z; both rounded centers in bounds",
    "patch_size": 16, "minimum_group_paired_observations": 64,
    "groups": [[12, 13, 14, 15], [16, 17, 18, 19]],
    "visibility_filter": False, "photometric_tie": "keep_old",
    "matched_tie": "source_id, patch_row, patch_col",
    "accepted_patch_action": "entire 16x16 block; downstream geometry validity remains separate",
    "maximum_cpu_seconds": 600, "maximum_rss_bytes": 8 * 1024**3,
    "experiment_kind": "exploratory_existing_component_not_novel_method",
}


def utc():
    return datetime.now(timezone.utc).isoformat()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def identity(path):
    path = Path(path)
    return {"path": str(path.resolve()), "bytes": path.stat().st_size, "sha256": sha(path)}


def validate_identity(item):
    path = Path(item["path"])
    require(path.is_absolute() and str(path.resolve()) == str(path), "Canonical absolute input path required")
    require(path.is_file(), "Missing allowed input")
    require(sha(path) == item["sha256"], "Input SHA mismatch: " + str(path))
    return path


def validate_manifest(manifest):
    require(manifest["schema"] == "s15b-witness-costs-v1", "Manifest schema")
    require(manifest["contract"] == CONTRACT, "Frozen contract differs from runner")
    sources, witnesses = manifest["source_images"], manifest["witness_images"]
    require([x["source_id"] for x in sources] == SOURCE_IDS, "Source identity/order")
    require([x["frame_id"] for x in witnesses] == WITNESS_IDS, "Witness identity/order")
    items = [manifest["proposal_seal"], manifest["proposal_npz"], *sources, *witnesses]
    paths = [x["path"] for x in items]
    require(len(paths) == len(set(paths)), "Duplicate input paths")
    require(Path(paths[0]).suffix == ".json" and Path(paths[1]).suffix == ".npz", "Proposal roles")
    require(all(Path(x["path"]).suffix.lower() == ".png" for x in sources + witnesses), "Only contracted PNG RGB inputs")
    # The seal is a root-owned identity assertion, not an instruction to open every referenced file.
    for item in items:
        validate_identity(item)
    return items


def validate_poses(poses, count):
    require(poses.shape == (count, 4, 4) and np.isfinite(poses).all(), "Pose dimensions/finite")
    require(np.allclose(poses[:, 3], [0, 0, 0, 1], atol=1e-5, rtol=0), "Pose bottom row")
    rotation = poses[:, :3, :3]
    require(np.allclose(rotation @ rotation.transpose(0, 2, 1), np.eye(3), atol=1e-5, rtol=0), "Pose orthogonality")
    require(np.allclose(np.linalg.det(rotation), 1, atol=1e-5, rtol=0), "Pose handedness")


def load_proposals(path, counters):
    with np.load(path, allow_pickle=False) as archive:
        require(set(archive.files) == NPZ_KEYS, "Only six contracted proposal arrays allowed")
        arrays = {}
        for key in sorted(NPZ_KEYS):
            a = archive[key]
            require(a.dtype.kind == "f", "Floating proposal field required: " + key)
            arrays[key] = a.astype(np.float64)
            counters["proposal_arrays_decoded"] += 1
    for key in ("old_self_z", "new_self_z"):
        require(arrays[key].shape == (4, SIZE, SIZE), "Source depth proposal dimensions")
    validate_poses(arrays["source_c2w"], 4)
    validate_poses(arrays["witness_c2w"], 8)
    K = arrays["K"]
    require(K.shape == (3, 3) and np.isfinite(K).all(), "K dimensions/finite")
    require(np.array_equal(K[2], [0, 0, 1]) and K[0, 0] > 0 and K[1, 1] > 0, "Physical pinhole K")
    require(abs(np.linalg.det(K)) > 1e-12, "Singular K")
    scale = arrays["scale_model_per_meter"]
    require(scale.shape == () and np.isfinite(scale) and scale > 0, "Positive scalar history scale")
    return arrays


def census5(gray):
    require(gray.shape == (SIZE, SIZE) and gray.dtype == np.uint8, "Census input")
    code = np.zeros_like(gray, dtype=np.uint32)
    center = gray[2:-2, 2:-2]
    bit = 0
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if dy == 0 and dx == 0:
                continue
            code[2:-2, 2:-2] |= ((gray[2 + dy:SIZE - 2 + dy, 2 + dx:SIZE - 2 + dx] < center).astype(np.uint32) << bit)
            bit += 1
    return code


def load_census(path, counters):
    with Image.open(path) as image:
        require(image.size == (640, 480), "Contracted source image resolution")
        gray = np.asarray(image.convert("RGB").resize((299, 224), Image.Resampling.LANCZOS)
                          .crop((37, 0, 261, 224)).convert("L"), dtype=np.uint8)
        counters["rgb_images_decoded"] += 1
    return census5(gray)


def popcount24(values):
    values = np.asarray(values, dtype=np.uint32)
    result = np.zeros(values.shape, dtype=np.uint8)
    for bit in range(24):
        result += ((values >> bit) & 1).astype(np.uint8)
    return result


def source_world(z, c2w, K):
    rows, cols = np.indices((SIZE, SIZE), dtype=np.float64)
    pixel = np.stack((cols, rows, np.ones_like(cols)), axis=-1)
    ray = pixel @ np.linalg.inv(K).T
    with np.errstate(invalid="ignore", over="ignore"):
        xyz = (ray * z[..., None]) @ c2w[:3, :3].T + c2w[:3, 3]
    valid = np.isfinite(z) & (z > 0) & np.isfinite(xyz).all(axis=-1)
    valid[:2] = False
    valid[-2:] = False
    valid[:, :2] = False
    valid[:, -2:] = False
    return xyz, valid


def project_rounded(world, witness_c2w, K, source_valid):
    # Row-vector inverse of a c2w rigid transform, without fitting or correcting a pose.
    with np.errstate(invalid="ignore", divide="ignore", over="ignore"):
        camera = (world - witness_c2w[:3, 3]) @ witness_c2w[:3, :3]
        homogeneous = camera @ K.T
        u = homogeneous[..., 0] / homogeneous[..., 2]
        v = homogeneous[..., 1] / homogeneous[..., 2]
        rounded_u = np.floor(u + 0.5)
        rounded_v = np.floor(v + 0.5)
    valid = source_valid & np.isfinite(camera).all(axis=-1) & (camera[..., 2] > 0)
    valid &= np.isfinite(rounded_u) & np.isfinite(rounded_v)
    valid &= (rounded_u >= 2) & (rounded_u <= 221) & (rounded_v >= 2) & (rounded_v <= 221)
    # Convert only finite, in-bounds projections. Invalid/non-finite values never become indices.
    col = np.zeros(source_valid.shape, dtype=np.int64)
    row = np.zeros(source_valid.shape, dtype=np.int64)
    col[valid] = rounded_u[valid].astype(np.int64)
    row[valid] = rounded_v[valid].astype(np.int64)
    return row, col, valid


def paired_costs(source_code, witness_code, old_projection, new_projection):
    old_row, old_col, old_valid = old_projection
    new_row, new_col, new_valid = new_projection
    valid = old_valid & new_valid
    old_cost = np.full(valid.shape, SENTINEL, dtype=np.uint8)
    new_cost = np.full(valid.shape, SENTINEL, dtype=np.uint8)
    old_cost[valid] = popcount24(source_code[valid] ^ witness_code[old_row[valid], old_col[valid]])
    new_cost[valid] = popcount24(source_code[valid] ^ witness_code[new_row[valid], new_col[valid]])
    return valid, old_cost, new_cost


def aggregate_rules(valid, old_cost, new_cost):
    require(valid.shape == old_cost.shape == new_cost.shape == (4, 8, SIZE, SIZE), "Cost tensor dimensions")
    require(valid.dtype == bool and old_cost.dtype == new_cost.dtype == np.uint8, "Cost tensor types")
    require(np.all(old_cost[valid] <= 24) and np.all(new_cost[valid] <= 24), "Hamming cost domain")
    require(np.all(old_cost[~valid] == SENTINEL) and np.all(new_cost[~valid] == SENTINEL), "Missing sentinel")
    rows = []
    masks = {name: np.zeros((4, SIZE, SIZE), dtype=bool) for name in ("pool_new", "split_new", "matched_absolute_new")}
    for source_index, source_id in enumerate(SOURCE_IDS):
        for patch_row in range(14):
            for patch_col in range(14):
                sl = (source_index, slice(None), slice(16 * patch_row, 16 * (patch_row + 1)), slice(16 * patch_col, 16 * (patch_col + 1)))
                v = valid[sl]
                counts = v.sum(axis=(1, 2), dtype=np.int64)
                old_sums = np.where(v, old_cost[sl], 0).sum(axis=(1, 2), dtype=np.int64)
                new_sums = np.where(v, new_cost[sl], 0).sum(axis=(1, 2), dtype=np.int64)
                count = int(counts.sum())
                old_sum, new_sum = int(old_sums.sum()), int(new_sums.sum())
                eligible = bool(counts[:4].sum() >= 64 and counts[4:].sum() >= 64)
                pool = old_sum > new_sum
                split = eligible and bool(old_sums[:4].sum() > new_sums[:4].sum() and old_sums[4:].sum() > new_sums[4:].sum())
                argmin = count > 0 and new_sum < old_sum
                require(pool == argmin, "Integer same-support pool/argmin equivalence")
                row = dict(source_index=source_index, source_id=source_id, patch_row=patch_row, patch_col=patch_col,
                           paired_observations=count, old_hamming_sum=old_sum, new_hamming_sum=new_sum,
                           paired_gain_hamming_sum=old_sum-new_sum, group0_count=int(counts[:4].sum()),
                           group1_count=int(counts[4:].sum()), split_eligible=eligible, pool_new=pool,
                           split_new=split, matched_absolute_new=False, pool_argmin_new=argmin)
                for j, witness_id in enumerate(WITNESS_IDS):
                    row[f"w{witness_id}_count"] = int(counts[j])
                    row[f"w{witness_id}_old_sum"] = int(old_sums[j])
                    row[f"w{witness_id}_new_sum"] = int(new_sums[j])
                rows.append(row)
    K = sum(row["split_new"] for row in rows)
    eligible_rows = [row for row in rows if row["split_eligible"]]
    ranked = sorted(eligible_rows, key=lambda r: (Fraction(r["new_hamming_sum"], r["paired_observations"]), r["source_id"], r["patch_row"], r["patch_col"]))
    for row in ranked[:K]:
        row["matched_absolute_new"] = True
    for row in rows:
        sl = (row["source_index"], slice(16 * row["patch_row"], 16 * (row["patch_row"] + 1)), slice(16 * row["patch_col"], 16 * (row["patch_col"] + 1)))
        for name in masks:
            masks[name][sl] = row[name]
    require(len(rows) == 784 and sum(r["matched_absolute_new"] for r in rows) == K, "Full denominator/matched action count")
    return rows, masks


class ResourceGuard:
    def __init__(self):
        self.start = time.process_time()

    def check(self):
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        rss_bytes = int(rss if sys.platform == "darwin" else rss * 1024)
        require(rss_bytes <= CONTRACT["maximum_rss_bytes"], "RSS bound exceeded")
        require(time.process_time() - self.start <= CONTRACT["maximum_cpu_seconds"], "CPU bound exceeded")
        return rss_bytes


def timeout_handler(signum, frame):
    raise TimeoutError("600 second wall-time guard exceeded")


def run(manifest_path, output):
    require(not output.exists(), "Fresh output directory required")
    output.mkdir(parents=True)
    counters = {"proposal_arrays_decoded": 0, "rgb_images_decoded": 0, "model_calls": 0, "depth_answer_images_decoded": 0, "final_target_rgb_decoded": 0}
    metadata = {"schema": "s15b-witness-cost-run-v1", "started_at_utc": utc(), "status": "RUNNING", "counters": counters,
                "contract": CONTRACT, "manifest": identity(manifest_path), "runner": identity(__file__),
                "environment": {"python": sys.version, "numpy": np.__version__, "pillow": PIL_VERSION},
                "proposal_seal_scope": "SHA checked only; root freezer and independent pre-review bind proposal/source/witness camera identities; seal links not traversed",
                "evidence_kind": "real_input_photo_costs_only_if_manifest_is_real; not_depth_accuracy_or_novelty"}
    write_json(output / "run_metadata.json", metadata)
    guard = ResourceGuard()
    previous_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(600)
    try:
        manifest = json.loads(manifest_path.read_text())
        allowed_items = validate_manifest(manifest)
        proposals = load_proposals(manifest["proposal_npz"]["path"], counters)
        source_codes = [load_census(x["path"], counters) for x in manifest["source_images"]]
        witness_codes = [load_census(x["path"], counters) for x in manifest["witness_images"]]
        guard.check()
        valid = np.zeros((4, 8, SIZE, SIZE), dtype=bool)
        old_cost = np.full(valid.shape, SENTINEL, dtype=np.uint8)
        new_cost = np.full(valid.shape, SENTINEL, dtype=np.uint8)
        for s in range(4):
            old_world, old_good = source_world(proposals["old_self_z"][s], proposals["source_c2w"][s], proposals["K"])
            new_world, new_good = source_world(proposals["new_self_z"][s], proposals["source_c2w"][s], proposals["K"])
            for w in range(8):
                po = project_rounded(old_world, proposals["witness_c2w"][w], proposals["K"], old_good)
                pn = project_rounded(new_world, proposals["witness_c2w"][w], proposals["K"], new_good)
                valid[s, w], old_cost[s, w], new_cost[s, w] = paired_costs(source_codes[s], witness_codes[w], po, pn)
                guard.check()
        rows, masks = aggregate_rules(valid, old_cost, new_cost)
        np.savez_compressed(output / "paired_costs.npz", paired_valid=valid, old_hamming=old_cost, new_hamming=new_cost)
        np.savez_compressed(output / "rule_masks.npz", **masks)
        with (output / "patches.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        write_json(output / "patches.json", rows)
        summary = {"total_predeclared_patches": 784, "patches_with_paired_observations": sum(r["paired_observations"] > 0 for r in rows),
                   "split_eligible_patches": sum(r["split_eligible"] for r in rows),
                   "paired_observations": int(valid.sum()), "count_unit": "source_pixel_times_witness; not independent samples",
                   "old_hamming_sum": int(old_cost[valid].sum(dtype=np.int64)), "new_hamming_sum": int(new_cost[valid].sum(dtype=np.int64)),
                   "action_counts": {name: sum(r[name] for r in rows) for name in masks},
                   "pool_argmin_exact_equivalence": all(r["pool_new"] == r["pool_argmin_new"] for r in rows),
                   "matched_absolute_scope": "same eligible support; same K as split; diagnostic given K, not independent deployable policy",
                   "visibility_claim": False, "depth_accuracy_measured": False}
        write_json(output / "summary.json", summary)
        for item in allowed_items:
            validate_identity(item)
        require(sha(manifest_path) == metadata["manifest"]["sha256"], "Manifest changed during execution")
        require(sha(__file__) == metadata["runner"]["sha256"], "Runner changed during execution")
        metadata.update(status="SUCCESS", completed_at_utc=utc(), cpu_seconds=time.process_time()-guard.start,
                        peak_rss_bytes=guard.check(), allowed_input_identities=allowed_items,
                        outputs=[identity(p) for p in sorted(output.iterdir()) if p.name != "run_metadata.json"])
    except BaseException as exc:
        metadata.update(status="FAIL", completed_at_utc=utc(), error=repr(exc), traceback=traceback.format_exc())
        write_json(output / "run_metadata.json", metadata)
        raise
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous_handler)
    write_json(output / "run_metadata.json", metadata)
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", "--output", dest="output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.manifest.resolve(), args.output.resolve())
    print(json.dumps({"status": result["status"], "output": str(args.output.resolve()), "counters": result["counters"]}))


if __name__ == "__main__":
    main()
