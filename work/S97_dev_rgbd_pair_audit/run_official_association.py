#!/usr/bin/env python3
"""Recheck S97 using the project's frozen one-to-one RGB-D/GT rules.

This is an engineering qualification audit only.  It does not run a model or
claim an unseen test result.  The earlier S97 run used independent nearest
neighbours; this run preserves it and supplies the protocol-compliant result.
"""
import hashlib, json, statistics, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from PIL import Image

BASE = Path(__file__).resolve().parent
PROJECT = BASE.parents[1]
sys.path.insert(0, str(PROJECT / "src"))
from tum_rgbd import read_timestamp_file, associate_rgb_depth

CASES = {
    "fr1_xyz": PROJECT / "data/tum/rgbd_dataset_freiburg1_xyz",
    "fr2_desk_guard": PROJECT / "data/tum/fr2_desk_timestamp_guard/rgbd_dataset_freiburg2_desk",
}
MAX_RGB_DEPTH = 0.020
GT_GAP = 0.100

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read_gt_times(path):
    vals = []
    for lineno, line in enumerate(Path(path).read_text().splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        fields = line.split()
        if len(fields) != 8:
            raise ValueError(f"{path}:{lineno}: expected 8 columns")
        vals.append(float(fields[0]))
    vals.sort()
    if not vals or any(b <= a for a, b in zip(vals, vals[1:])):
        raise ValueError(f"{path}: GT timestamps are not strictly increasing")
    intervals = [[vals[0], vals[0]]]
    for a, b in zip(vals, vals[1:]):
        if b - a > GT_GAP:
            intervals.append([b, b])
        else:
            intervals[-1][1] = b
    return vals, intervals

def interval_at(t, intervals):
    # Intervals are sorted, closed, and have disjoint support.
    for i, (lo, hi) in enumerate(intervals):
        if lo <= t <= hi:
            return i
    return None

def main():
    started = datetime.now(timezone.utc).isoformat()
    result = {
        "schema": "S97-official-association-v1",
        "status": "RUNNING",
        "started_utc": started,
        "rgb_depth_rule": "tum_rgbd.associate_rgb_depth, strict |dt| < 0.020, unique greedy",
        "gt_rule": "sorted timestamps; gap > 0.100 creates a closed support interval; both RGB and depth must be in the same interval",
        "images_decoded": True,
        "model_inferences": 0,
        "formal_s91_run": False,
        "cases": [],
    }
    for name, root in CASES.items():
        rgb = read_timestamp_file(root / "rgb.txt")
        depth = read_timestamp_file(root / "depth.txt")
        gt_times, gt_intervals = read_gt_times(root / "groundtruth.txt")
        matches = associate_rgb_depth(rgb, depth, max_difference=MAX_RGB_DEPTH)
        kept, excluded = [], []
        for i, match in enumerate(matches):
            ri = interval_at(match.rgb.timestamp, gt_intervals)
            di = interval_at(match.depth.timestamp, gt_intervals)
            if ri is None or di is None or ri != di:
                excluded.append({"match_index": i, "reason": "same_closed_gt_interval_required",
                                 "rgb_t": match.rgb.timestamp, "depth_t": match.depth.timestamp,
                                 "rgb_interval": ri, "depth_interval": di})
                continue
            kept.append((i, match, ri))
        rgb_modes, depth_modes, bad = {}, {}, []
        depth_nonzero = []
        used_depth = set()
        for i, match, interval in kept:
            used_depth.add(match.depth.path)
            try:
                with Image.open(root / match.rgb.path) as im:
                    key = str((im.mode, tuple(im.size)))
                    rgb_modes[key] = rgb_modes.get(key, 0) + 1
                with Image.open(root / match.depth.path) as im:
                    key = str((im.mode, tuple(im.size)))
                    depth_modes[key] = depth_modes.get(key, 0) + 1
                    arr = np.asarray(im)
                    depth_nonzero.append(float(np.count_nonzero(arr) / arr.size))
            except Exception as exc:
                bad.append({"match_index": i, "error": repr(exc)})
        result["cases"].append({
            "id": name,
            "root": str(root),
            "exposure_state": "DEVELOPMENT_SEEN",
            "source_shas": {f: sha(root / f) for f in ("rgb.txt", "depth.txt", "groundtruth.txt")},
            "counts": {"rgb_rows": len(rgb), "depth_rows": len(depth), "gt_rows": len(gt_times),
                       "gt_intervals": len(gt_intervals), "official_rgb_depth_matches": len(matches),
                       "official_pairs_same_gt_interval": len(kept),
                       "excluded_pairs_gt_support": len(excluded)},
            "duplicate_depth_reuse": 0,
            "rgb_header_modes_sizes": rgb_modes,
            "depth_header_modes_sizes": depth_modes,
            "bad_image_reads": len(bad),
            "depth_nonzero_fraction_summary": ({"min": min(depth_nonzero), "median": statistics.median(depth_nonzero), "max": max(depth_nonzero)} if depth_nonzero else None),
            "excluded_examples": excluded[:5],
            "bad_examples": bad[:3],
        })
    result["status"] = "PASS_OFFICIAL_ASSOCIATION_DEVELOPMENT_ONLY"
    result["completed_utc"] = datetime.now(timezone.utc).isoformat()
    out = BASE / "run_02_official_association_results.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "cases": [
        (c["id"], c["counts"]["official_rgb_depth_matches"], c["counts"]["official_pairs_same_gt_interval"], c["bad_image_reads"])
        for c in result["cases"]]}, ensure_ascii=False))

if __name__ == "__main__":
    main()
