#!/usr/bin/env python3
"""Select one complete geometry candidate using source RGB, optical c2w and K.

No sensor depths or target image/pose are opened. All correspondence supports are
established before any candidate is scored. Scores use the same matches and do
not discard invalid candidate predictions. Ground truth is not an input.
"""
import argparse
import datetime as dt
import hashlib
import io
import itertools
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile

import numpy as np

SCHEMA = "w2-source-geometry-selection-v1"
CONFIG = {
    "sift": {"nfeatures": 4096, "nOctaveLayers": 3, "contrastThreshold": 0.04,
             "edgeThreshold": 10, "sigma": 1.6},
    "ratio_strict": 0.75, "symmetric_epipolar_px_max": 1.0,
    "parallax_deg_min": 1.0, "pair_matches_min": 20,
    "eligible_pairs_min": 3, "reprojection_cap_px": 32.0,
    "tie_tolerance": 1e-12, "cv2_threads": 1, "cv2_seed": 0,
    "epipolar_definition": "maximum of both point-to-line distances",
    "positive_triangulation_depth_required": True,
    "pair_weighting": "equal eligible pair mean; equal directions and matches within pair",
}
GRID = (384, 512)
NATIVE = (480, 640)
SAFE_ID = re.compile(r"[A-Za-z0-9_.-]+\Z")
REF = re.compile(r"seq-[0-9]+/[0-9]{6}\Z")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha_bytes(blob):
    return hashlib.sha256(blob).hexdigest()


def sha_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def atomic_publish(path, writer):
    path = Path(path)
    fd, temporary = tempfile.mkstemp(prefix="." + path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as fh:
            writer(fh)
            fh.flush()
            os.fsync(fh.fileno())
        os.link(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def publish_json(path, value):
    blob = json.dumps(value, indent=2, sort_keys=True, allow_nan=False).encode() + b"\n"
    atomic_publish(path, lambda fh: fh.write(blob))


def validate_manifest(manifest):
    candidates, windows = manifest["candidates"], manifest["windows"]
    require(len(candidates) == 4 and len(windows) > 0, "Expected four candidates and nonempty windows")
    require([c["candidate_id"] for c in candidates] == ["c0", "c1", "c2", "c3"],
            "Candidate order must be c0,c1,c2,c3")
    for c in candidates:
        require(sorted(c["order"]) == list(range(4)), "Candidate order is not a permutation")
    require(len({w["window_id"] for w in windows}) == len(windows), "Duplicate window identities")
    for w in windows:
        require(bool(SAFE_ID.fullmatch(w["window_id"])) and w["window_id"] not in {".", ".."}, "Unsafe window ID")
        rel = PurePosixPath(w["scene_rel"])
        require(rel.parts and not rel.is_absolute() and ".." not in rel.parts, "Unsafe scene path")
        refs = w["source_refs"]
        require(len(refs) == 4 and len(set(refs)) == 4 and all(REF.fullmatch(r) for r in refs),
                "Expected exactly four distinct valid source refs")
        require(not set(refs).intersection(w.get("target_refs", [])), "Source and target identities overlap")
    # The protocol, not a loosely accepted manifest knob, fixes these constants.
    if "selector" in manifest:
        for key, value in manifest["selector"].items():
            require(key in CONFIG and CONFIG[key] == value, "Selector config does not match frozen code")
    return candidates, windows


def inside(root, relative):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    require(path.is_relative_to(root), "Source path escapes data root")
    return path


def source_allowlist(data_root, window):
    scene = PurePosixPath(window["scene_rel"])
    entries = [("K", inside(data_root, scene / "camera-intrinsics.txt"))]
    for index, ref in enumerate(window["source_refs"]):
        require(bool(REF.fullmatch(ref)), "Invalid source reference")
        sequence, frame = ref.split("/")
        prefix = scene / sequence / ("frame-" + frame)
        entries.extend([(f"rgb_{index}", inside(data_root, str(prefix) + ".color.png")),
                        (f"pose_{index}", inside(data_root, str(prefix) + ".pose.txt"))])
    return entries


def load_sources(data_root, window):
    from PIL import Image
    root = Path(data_root).resolve()
    entries = source_allowlist(root, window)
    blobs, fingerprints = {}, {}
    for label, path in entries:
        blob = path.read_bytes()
        blobs[label] = blob
        fingerprints[path.relative_to(root).as_posix()] = {"sha256": sha_bytes(blob), "bytes": len(blob)}
    K = np.loadtxt(io.BytesIO(blobs["K"]), dtype=np.float64).reshape(3, 3)
    require(np.isfinite(K).all() and K[0, 0] > 0 and K[1, 1] > 0 and np.allclose(K[2], [0, 0, 1]),
            "Invalid native intrinsics")
    rgbs, poses = [], []
    for i in range(4):
        with Image.open(io.BytesIO(blobs[f"rgb_{i}"])) as image:
            rgb = np.asarray(image.convert("RGB")).copy()
        require(rgb.shape == (*NATIVE, 3), "Expected native source RGB 480x640")
        pose = np.loadtxt(io.BytesIO(blobs[f"pose_{i}"]), dtype=np.float64).reshape(4, 4)
        require(np.isfinite(pose).all() and np.allclose(pose[3], [0, 0, 0, 1], atol=1e-6), "Invalid source pose")
        R = pose[:3, :3]
        require(np.allclose(R.T @ R, np.eye(3), atol=1e-5) and np.isclose(np.linalg.det(R), 1, atol=1e-5),
                "Source pose is not rigid")
        rgbs.append(rgb)
        poses.append(pose)
    return rgbs, np.stack(poses), K, fingerprints


def native_to_grid(uv):
    """The exact W1 half-pixel / square-crop / CUT3R-center-crop mapping."""
    uv = np.asarray(uv, dtype=np.float64)
    mapped = np.column_stack([((uv[:, 0] + 0.5) * 1.2 - 96) * 512 / 576 - 0.5,
                              (uv[:, 1] + 0.5) * 1.2 * 512 / 576 - 64 - 0.5])
    finite = np.isfinite(mapped).all(axis=1)
    indices = np.rint(np.where(np.isfinite(mapped), mapped, -1000)).astype(np.int64)
    inside_crop = finite & (indices[:, 0] >= 0) & (indices[:, 0] < GRID[1]) & (indices[:, 1] >= 0) & (indices[:, 1] < GRID[0])
    return indices, inside_crop


def project(uv, depth, source_pose, target_pose, K):
    uv, depth = np.asarray(uv, dtype=np.float64), np.asarray(depth, dtype=np.float64)
    rays = np.column_stack([uv, np.ones(len(uv))]) @ np.linalg.inv(K).T
    with np.errstate(invalid="ignore", divide="ignore", over="ignore"):
        points = rays * depth[:, None]
        world = points @ source_pose[:3, :3].T + source_pose[:3, 3]
        target = (world - target_pose[:3, 3]) @ target_pose[:3, :3]
        projected = target @ K.T
        out = projected[:, :2] / projected[:, 2:3]
    valid = np.isfinite(depth) & (depth > 0) & np.isfinite(out).all(axis=1) & np.isfinite(target[:, 2]) & (target[:, 2] > 0)
    valid &= (out[:, 0] >= 0) & (out[:, 0] < NATIVE[1]) & (out[:, 1] >= 0) & (out[:, 1] < NATIVE[0])
    return out, valid


def skew(v):
    x, y, z = v
    return np.array([[0., -z, y], [z, 0., -x], [-y, x, 0.]])


def geometric_match_filter(uv_i, uv_j, pose_i, pose_j, K):
    """Known-pose epipolar and observed-ray parallax filters, no depths."""
    uv_i, uv_j = np.asarray(uv_i, dtype=np.float64), np.asarray(uv_j, dtype=np.float64)
    xi = np.column_stack([uv_i, np.ones(len(uv_i))])
    xj = np.column_stack([uv_j, np.ones(len(uv_j))])
    inverse_K = np.linalg.inv(K)
    rotation = pose_j[:3, :3].T @ pose_i[:3, :3]
    translation = pose_j[:3, :3].T @ (pose_i[:3, 3] - pose_j[:3, 3])
    F = inverse_K.T @ skew(translation) @ rotation @ inverse_K
    line_j, line_i = xi @ F.T, xj @ F
    numerator = np.abs(np.sum(xj * line_j, axis=1))
    norm_j, norm_i = np.linalg.norm(line_j[:, :2], axis=1), np.linalg.norm(line_i[:, :2], axis=1)
    epipolar = np.full(len(uv_i), np.inf)
    good_lines = (norm_i > 1e-15) & (norm_j > 1e-15)
    epipolar[good_lines] = numerator[good_lines] * np.maximum(1 / norm_i[good_lines], 1 / norm_j[good_lines])
    ray_i = xi @ inverse_K.T @ pose_i[:3, :3].T
    ray_j = xj @ inverse_K.T @ pose_j[:3, :3].T
    ray_i /= np.linalg.norm(ray_i, axis=1)[:, None]
    ray_j /= np.linalg.norm(ray_j, axis=1)[:, None]
    cosine = np.sum(ray_i * ray_j, axis=1)
    parallax = np.degrees(np.arccos(np.clip(cosine, -1, 1)))
    # Least-squares closest approach of two observed world rays. These depths
    # are derived only from source correspondences and cameras, never sensors.
    baseline = pose_j[:3, 3] - pose_i[:3, 3]
    rhs_i, rhs_j = ray_i @ baseline, -(ray_j @ baseline)
    determinant = 1 - cosine ** 2
    with np.errstate(divide="ignore", invalid="ignore"):
        distance_i = (rhs_i + cosine * rhs_j) / determinant
        distance_j = (cosine * rhs_i + rhs_j) / determinant
        midpoint = 0.5 * (pose_i[:3, 3] + ray_i * distance_i[:, None]
                          + pose_j[:3, 3] + ray_j * distance_j[:, None])
        z_i = ((midpoint - pose_i[:3, 3]) @ pose_i[:3, :3])[:, 2]
        z_j = ((midpoint - pose_j[:3, 3]) @ pose_j[:3, :3])[:, 2]
    positive_depth = np.isfinite(z_i) & np.isfinite(z_j) & (z_i > 0) & (z_j > 0) & (determinant > 1e-12)
    _, crop_i = native_to_grid(uv_i)
    _, crop_j = native_to_grid(uv_j)
    accepted = crop_i & crop_j & np.isfinite(epipolar) & (epipolar <= CONFIG["symmetric_epipolar_px_max"])
    accepted &= np.isfinite(parallax) & (parallax >= CONFIG["parallax_deg_min"])
    accepted &= positive_depth
    return accepted, epipolar, parallax, np.column_stack([z_i, z_j])


def mutual_ratio_matches(descriptors_i, descriptors_j, cv2):
    if descriptors_i is None or descriptors_j is None or min(len(descriptors_i), len(descriptors_j)) < 2:
        return np.empty((0, 2), dtype=np.int64)
    matcher = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)

    def accepted(query, train):
        result = {}
        for neighbours in matcher.knnMatch(query, train, k=2):
            if len(neighbours) == 2 and neighbours[0].distance < CONFIG["ratio_strict"] * neighbours[1].distance:
                result[neighbours[0].queryIdx] = neighbours[0].trainIdx
        return result

    forward, backward = accepted(descriptors_i, descriptors_j), accepted(descriptors_j, descriptors_i)
    return np.array([(i, j) for i, j in sorted(forward.items()) if backward.get(j) == i], dtype=np.int64).reshape(-1, 2)


def source_matches(rgbs, poses, K):
    import cv2
    cv2.setNumThreads(CONFIG["cv2_threads"])
    cv2.setRNGSeed(CONFIG["cv2_seed"])
    sift = cv2.SIFT_create(**CONFIG["sift"])
    keypoints, descriptors = [], []
    for rgb in rgbs:
        kp, desc = sift.detectAndCompute(cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY), None)
        keypoints.append(np.array([k.pt for k in kp], dtype=np.float64).reshape(-1, 2))
        descriptors.append(desc)
    pairs, arrays = [], {f"keypoints_{i}": k for i, k in enumerate(keypoints)}
    for i, j in itertools.combinations(range(4), 2):
        matched = mutual_ratio_matches(descriptors[i], descriptors[j], cv2)
        uv_i, uv_j = keypoints[i][matched[:, 0]], keypoints[j][matched[:, 1]]
        accepted, epipolar, parallax, triangulated_z = geometric_match_filter(uv_i, uv_j, poses[i], poses[j], K)
        pair = {"source_i": i, "source_j": j, "uv_i": uv_i[accepted], "uv_j": uv_j[accepted],
                "mutual_ratio_count": len(matched), "filtered_count": int(accepted.sum()),
                "eligible": int(accepted.sum()) >= CONFIG["pair_matches_min"]}
        pairs.append(pair)
        prefix = f"pair_{i}_{j}_"
        arrays.update({prefix + "mutual_keypoint_indices": matched, prefix + "accepted": accepted,
                       prefix + "epipolar_px": epipolar, prefix + "parallax_deg": parallax,
                       prefix + "triangulated_source_z": triangulated_z,
                       prefix + "uv_i": uv_i[accepted], prefix + "uv_j": uv_j[accepted]})
    return pairs, arrays, {"opencv": cv2.__version__, "numpy": np.__version__}


def support_status(pairs):
    eligible = [p for p in pairs if p["eligible"]]
    if len(eligible) < CONFIG["eligible_pairs_min"]:
        return "fewer_than_three_eligible_pairs"
    adjacency = {i: set() for i in range(4)}
    for p in eligible:
        i, j = p["source_i"], p["source_j"]
        adjacency[i].add(j)
        adjacency[j].add(i)
    seen, stack = set(), [0]
    while stack:
        node = stack.pop()
        if node not in seen:
            seen.add(node)
            stack.extend(adjacency[node] - seen)
    return None if seen == set(range(4)) else "eligible_graph_not_connected_over_all_four_sources"


def directed_loss(depth_map, uv_source, uv_observed, pose_source, pose_target, K):
    grid, in_crop = native_to_grid(uv_source)
    require(in_crop.all(), "Matched support must be in the fixed CUT3R crop")
    depth = depth_map[grid[:, 1], grid[:, 0]].astype(np.float64)
    predicted, valid = project(uv_source, depth, pose_source, pose_target, K)
    epe = np.linalg.norm(predicted - uv_observed, axis=1)
    loss = np.ones(len(depth), dtype=np.float64)
    valid &= np.isfinite(epe)
    loss[valid] = np.minimum(epe[valid], CONFIG["reprojection_cap_px"]) / CONFIG["reprojection_cap_px"]
    return loss, predicted, valid


def choose_candidate(scores):
    scores = np.asarray(scores, dtype=np.float64)
    require(np.isfinite(scores).all() and len(scores) == 4, "Invalid whole-candidate scores")
    return int(np.flatnonzero(scores <= scores.min() + CONFIG["tie_tolerance"])[0])


def score_candidates(depths, pairs, poses, K):
    require(depths.shape == (4, 4, *GRID), "Expected candidate x source x 384 x 512 depths")
    reason = support_status(pairs)
    arrays, pair_scores, scores = {}, [], []
    eligible = [p for p in pairs if p["eligible"]]
    for candidate_index, geometry in enumerate(depths):
        values = []
        for pair in eligible:
            i, j = pair["source_i"], pair["source_j"]
            a, q_a, valid_a = directed_loss(geometry[i], pair["uv_i"], pair["uv_j"], poses[i], poses[j], K)
            b, q_b, valid_b = directed_loss(geometry[j], pair["uv_j"], pair["uv_i"], poses[j], poses[i], K)
            values.append(float(0.5 * (a.mean() + b.mean())))
            prefix = f"c{candidate_index}_pair_{i}_{j}_"
            arrays.update({prefix + "loss_i_to_j": a, prefix + "loss_j_to_i": b,
                           prefix + "projected_i_to_j": q_a, prefix + "projected_j_to_i": q_b,
                           prefix + "valid_i_to_j": valid_a, prefix + "valid_j_to_i": valid_b})
        pair_scores.append(values)
        scores.append(float(np.mean(values)) if values else None)
    chosen = 0 if reason else choose_candidate(scores)
    return {"selected_candidate_id": f"c{chosen}", "selected_candidate_index": chosen,
            "scores": {f"c{i}": v for i, v in enumerate(scores)},
            "pair_scores": {f"c{i}": v for i, v in enumerate(pair_scores)},
            "abstained": reason is not None, "abstention_reason": reason}, arrays


def load_candidates(directory, window, candidates, manifest_sha, protocol_sha, source_hashes, poses, K):
    depths, provenance = [], {}
    for candidate in candidates:
        basename = f"{window['window_id']}__{candidate['candidate_id']}"
        npz_path, receipt_path = Path(directory) / (basename + ".npz"), Path(directory) / (basename + ".json")
        receipt = json.loads(receipt_path.read_text())
        digest = sha_file(npz_path)
        require(receipt.get("status") == "OK" and receipt.get("candidate_sha256") == digest,
                "Candidate receipt status or file hash mismatch")
        require(receipt.get("manifest_sha256") == manifest_sha and receipt.get("protocol_sha256") == protocol_sha,
                "Candidate was generated for another manifest/protocol")
        require(receipt.get("window") == window and receipt.get("candidate") == candidate,
                "Candidate identity mismatch")
        require(receipt.get("source_files") == source_hashes, "Candidate source input hashes changed")
        with np.load(npz_path, allow_pickle=False) as data:
            require(data["depths"].shape == (4, *GRID), "Wrong depth shape")
            require(data["source_refs"].tolist() == window["source_refs"], "Candidate sources out of canonical order")
            require(np.allclose(data["K"], K, rtol=0, atol=1e-10) and np.allclose(data["poses"], poses, rtol=0, atol=1e-6),
                    "Candidate source camera parameters mismatch")
            depths.append(data["depths"].copy())
        provenance[candidate["candidate_id"]] = {"npz_sha256": digest, "receipt_sha256": sha_file(receipt_path),
                                                "file": npz_path.name, "receipt": receipt_path.name}
    return np.stack(depths), provenance


def verify_existing(output, identity):
    json_path, npz_path = Path(str(output) + ".json"), Path(str(output) + ".npz")
    if not json_path.exists() and not npz_path.exists():
        return False
    require(json_path.is_file() and npz_path.is_file(), "Incomplete selection output; refusing overwrite")
    receipt = json.loads(json_path.read_text())
    require(receipt.get("status") == "OK" and receipt.get("fingerprint") == sha_bytes(canonical(identity)),
            "Selection identity changed; refusing overwrite")
    require(receipt.get("matches_sha256") == sha_file(npz_path), "Selection match/residual hash changed")
    return True


def validate_decision(result):
    pairs = result["pair_records"]
    require([(p["source_i"], p["source_j"]) for p in pairs] == list(itertools.combinations(range(4), 2)),
            "Selection pair identity mismatch")
    require(all(p["eligible"] == (p["filtered_count"] >= CONFIG["pair_matches_min"]) for p in pairs),
            "Selection pair eligibility mismatch")
    reason = support_status(pairs)
    require(result["abstention_reason"] == reason and result["abstained"] == (reason is not None),
            "Selection fallback does not match source support")
    scores = result["candidate_scores"]
    require(len(scores) == 4 and scores == [result["scores"][f"c{i}"] for i in range(4)],
            "Selection score fields differ")
    chosen = 0 if reason else choose_candidate(scores)
    require(result["selected_candidate_index"] == chosen and result["selected_candidate_id"] == f"c{chosen}",
            "Selection is not the frozen argmin/fallback")


def make_seal(out, windows, common):
    records = []
    for window in windows:
        basename = window["window_id"]
        j, n = out / (basename + ".json"), out / (basename + ".npz")
        result = json.loads(j.read_text())
        require(result.get("status") == "OK" and result.get("window") == window,
                "Selection incomplete or identity mismatch")
        require(all(result.get(key) == value for key, value in common.items()), "Selection seal common provenance mismatch")
        require(sha_file(n) == result.get("matches_sha256"), "Selection support checksum mismatch")
        validate_decision(result)
        identity = {key: result[key] for key in (*common.keys(), "window", "source_files", "candidate_files")}
        require(result.get("fingerprint") == sha_bytes(canonical(identity)), "Selection fingerprint mismatch")
        records.append({"window_id": basename, "receipt": j.name, "receipt_sha256": sha_file(j),
                        "matches": n.name, "matches_sha256": sha_file(n),
                        "selected_candidate_id": result["selected_candidate_id"], "abstained": result["abstained"]})
    seal_path = out / "SELECTION_SEAL.json"
    seal = {**common, "schema": SCHEMA + "-seal", "records": records,
            "all_windows_selected": len(records), "sensor_depth_read": False, "target_data_read": False}
    if seal_path.exists():
        existing = json.loads(seal_path.read_text())
        require(all(existing.get(k) == v for k, v in seal.items()), "Existing selection seal differs")
    else:
        publish_json(seal_path, {**seal, "sealed_utc": dt.datetime.now(dt.timezone.utc).isoformat()})
    return seal_path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("manifest", "data-root", "candidates", "out", "protocol-sha", "freeze"):
        parser.add_argument("--" + key, required=True)
    parser.add_argument("--seal", action="store_true", help="Verify all selection records and seal; no source data is opened")
    args = parser.parse_args(argv)
    require(bool(re.fullmatch("[0-9a-f]{64}", args.protocol_sha)), "Protocol digest must be lower-case SHA-256")
    manifest_bytes = Path(args.manifest).read_bytes()
    candidates, windows = validate_manifest(json.loads(manifest_bytes))
    freeze = Path(args.freeze)
    require(freeze.is_file(), "Freeze receipt is required before selection")
    common = {"schema": SCHEMA, "selector_sha256": sha_file(__file__), "config": CONFIG,
              "manifest_sha256": sha_bytes(manifest_bytes), "protocol_sha256": args.protocol_sha,
              "freeze_sha256": sha_file(freeze)}
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if args.seal:
        print(make_seal(out, windows, common))
        return 0
    for window in windows:
        started = dt.datetime.now(dt.timezone.utc).isoformat()
        rgbs, poses, K, source_files = load_sources(args.data_root, window)
        depths, candidate_files = load_candidates(args.candidates, window, candidates,
            common["manifest_sha256"], args.protocol_sha, source_files, poses, K)
        identity = {**common, "window": window, "source_files": source_files, "candidate_files": candidate_files}
        prefix = out / window["window_id"]
        if verify_existing(prefix, identity):
            print(f"[skip] {window['window_id']} verified", flush=True)
            continue
        pairs, arrays, versions = source_matches(rgbs, poses, K)
        result, residuals = score_candidates(depths, pairs, poses, K)
        arrays.update(residuals)
        arrays.update(poses=poses, K=K, source_refs=np.array(window["source_refs"], dtype="U"))
        npz_path = Path(str(prefix) + ".npz")
        atomic_publish(npz_path, lambda fh: np.savez_compressed(fh, **arrays))
        pair_records = [{k: value for k, value in pair.items() if not k.startswith("uv_")} for pair in pairs]
        receipt = {**identity, **result, "status": "OK", "fingerprint": sha_bytes(canonical(identity)),
                   "window_id": window["window_id"], "started_utc": started,
                   "candidate_scores": [result["scores"][f"c{i}"] for i in range(4)],
                   "candidate_hashes": {key: value["npz_sha256"] for key, value in candidate_files.items()},
                   "pair_records": pair_records, "matches_sha256": sha_file(npz_path),
                   "matches_file": npz_path.name,
                   "camera_intrinsics": K.tolist(), "source_optical_c2w": poses.tolist(), "versions": versions,
                   "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                   "sensor_depth_read": False, "target_data_read": False,
                   "confidence_used": False, "candidate_scores_use_identical_support": True}
        publish_json(Path(str(prefix) + ".json"), receipt)
        print(f"[ok] {window['window_id']} selected={result['selected_candidate_id']} abstained={result['abstained']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
