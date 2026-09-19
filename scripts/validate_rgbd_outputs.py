#!/usr/bin/env python3
"""Independently verify saved S2/S3 evidence without importing live experiment code.

Source hashes refer to reproduction_source.zip at run time, not today's source.
Without --data, raw image/archive hashes are explicitly marked unverified.
An incomplete/missing experiment can never produce a passing report.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import sys
from urllib.parse import urlparse
import zipfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
METHODS = ("first_write", "frame_mean")


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"Nonfinite JSON {value}")))


def read_jsonl(path):
    return [json.loads(line, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"Nonfinite JSON {value}")))
            for line in Path(path).read_text().splitlines() if line.strip()]


class Verifier:
    def __init__(self):
        self.checks = []
        self.errors = []
        self.summary = {}

    def check(self, label, condition, detail=None):
        item = dict(check=label, passed=bool(condition))
        if detail is not None:
            item["detail"] = detail
        self.checks.append(item)
        if not condition:
            raise ValueError(label + (f": {detail}" if detail is not None else ""))

    def section(self, name, function):
        try:
            return function()
        except Exception as error:
            self.errors.append(dict(section=name, error=f"{type(error).__name__}: {error}"))
            return None

    def fraction(self, label, value, nullable=False):
        self.check(label, (nullable and value is None) or
                   (isinstance(value, (int, float)) and not isinstance(value, bool) and np.isfinite(value) and 0 <= value <= 1), value)

    def integer(self, label, value, low=0, high=None):
        self.check(label, isinstance(value, int) and not isinstance(value, bool) and value >= low and (high is None or value <= high), value)


def verify_run(v, directory, label):
    meta = read_json(directory / "run_metadata.json")
    start = datetime.fromisoformat(meta["started_utc"])
    end = datetime.fromisoformat(meta["completed_utc"])
    v.check(f"{label}: completed timestamp is timezone-aware and after start",
            start.tzinfo is not None and end.tzinfo is not None and end >= start)
    hashes = meta["source_sha256"]
    v.check(f"{label}: source hash inventory is nonempty", isinstance(hashes, dict) and bool(hashes))
    with zipfile.ZipFile(directory / "reproduction_source.zip") as archive:
        names = archive.namelist()
        v.check(f"{label}: archive has no duplicate paths", len(names) == len(set(names)))
        v.check(f"{label}: archive inventory equals run source inventory", set(names) == set(hashes))
        bad = [name for name, digest in hashes.items() if hashlib.sha256(archive.read(name)).hexdigest() != digest]
        v.check(f"{label}: every archived source matches recorded SHA256", not bad, dict(files=len(hashes), mismatches=bad))
    v.summary[f"{label}_archived_source_files"] = len(hashes)
    return meta


def verify_manifest(v, manifest, label):
    matches = manifest["matches"]
    v.check(f"{label}: match count equals valid pose count", len(matches) == manifest["valid_pose_matches"])
    v.check(f"{label}: matches are depth-time ordered", all(a["depth"]["timestamp"] < b["depth"]["timestamp"] for a, b in zip(matches, matches[1:])))
    for kind in ("rgb", "depth"):
        for key in ("timestamp", "path"):
            values = [m[kind][key] for m in matches]
            v.check(f"{label}: unique {kind} {key}", len(values) == len(set(values)))
    offsets = [abs(m["rgb"]["timestamp"] - m["depth"]["timestamp"]) for m in matches]
    v.check(f"{label}: every match is strictly within 20ms", bool(offsets) and max(offsets) < .02)
    qa = manifest["qa_indices"]
    v.check(f"{label}: 24 unique valid QA indices", len(qa) == len(set(qa)) == 24 and all(isinstance(i, int) and 0 <= i < len(matches) for i in qa))
    blocks = manifest["blocks"]
    v.check(f"{label}: three blocks with 24 frames", len(blocks) == 3 and all(len(block) == 24 for block in blocks))
    flattened = [i for block in blocks for i in block]
    v.check(f"{label}: no repeated frame across temporal blocks", len(flattened) == len(set(flattened)) and all(isinstance(i, int) and 0 <= i < len(matches) for i in flattened))
    histories, heldout = set(), set()
    for b, block in enumerate(blocks):
        v.check(f"{label}: block {b} strictly time ordered", all(a < c for a, c in zip(block, block[1:])))
        histories.update(block[:20]); heldout.update(block[20:])
    v.check(f"{label}: held-out frames never occur in any history", histories.isdisjoint(heldout))
    v.check(f"{label}: recorded depth divisor is 5000", manifest["depth_scale_divisor"] == 5000)
    v.summary[f"{label}_history_frames"] = len(histories)
    v.summary[f"{label}_heldout_frames"] = len(heldout)


def verify_qa(v, directory, meta, manifest):
    rows = read_json(directory / "frame_qa.json")
    v.check("S2: exactly 24 completed QA observations", len(rows) == meta["qa_frames"] == meta["config"]["qa_frames"] == 24)
    v.check("S2: coordinate check marked complete", meta["coordinate_checks_passed"] is True)
    for i, row in enumerate(rows):
        prefix = f"S2 sample {i}"
        match = manifest["matches"][manifest["qa_indices"][i]]
        v.check(f"{prefix}: sample and matched frame identity", row["sample"] == i and
                row["timestamp"] == match["depth"]["timestamp"] and row["rgb_timestamp"] == match["rgb"]["timestamp"] and
                row["depth_path"] == match["depth"]["path"] and row["rgb_path"] == match["rgb"]["path"])
        v.check(f"{prefix}: finite coordinate roundtrip errors within tolerance", 0 <= row["roundtrip_max_pixel_error"] <= 1e-6 and 0 <= row["roundtrip_max_depth_error_m"] <= 1e-9)
        v.check(f"{prefix}: time and pose gap limits", abs(row["offset_seconds"]) < .02 and 0 <= row["pose_gap_seconds"] <= .1 and
                np.isclose(row["offset_seconds"], row["rgb_timestamp"] - row["timestamp"], rtol=0, atol=1e-12))
        v.fraction(f"{prefix}: valid depth fraction", row["valid_depth_fraction"])
        v.integer(f"{prefix}: positive sampled point count", row["sampled_points"], low=1)
        q = row["valid_depth_m_quantiles"]
        v.check(f"{prefix}: finite positive ordered depth quantiles", len(q) == 5 and np.isfinite(q).all() and min(q) > 0 and all(a <= b for a, b in zip(q, q[1:])))
    v.summary["qa_observations"] = len(rows)
    return rows


def record_key(record):
    return (record["block"], record["stride"], float(record["first_frame_depth_axis_bias_m"]), record["query"])


def recompute_stats(pred, target, mask):
    values = (pred - target)[mask]
    if not len(values):
        return dict(n=0, mae_mm=None, median_abs_mm=None, p90_abs_mm=None, within_30mm=None, signed_mean_mm=None)
    absolute = np.abs(values)
    return dict(n=len(values), mae_mm=float(absolute.mean() * 1000), median_abs_mm=float(np.median(absolute) * 1000),
                p90_abs_mm=float(np.quantile(absolute, .9) * 1000), within_30mm=float((absolute <= .03).mean()),
                signed_mean_mm=float(values.mean() * 1000))


def compare_stats(v, label, saved, actual):
    differences = {}
    for key, value in actual.items():
        got = saved[key]
        if value is None:
            ok = got is None
        elif key == "n":
            ok = isinstance(got, int) and got == value
        else:
            ok = isinstance(got, (int, float)) and np.isfinite(got) and np.isclose(got, value, atol=1e-8, rtol=1e-8)
        if not ok:
            differences[key] = dict(saved=got, recomputed=value)
    v.check(label, not differences, differences if differences else None)


def verify_case(v, case_path, result, manifest, resolutions):
    block, stride, bias = result["block"], result["stride"], float(result["bias_m"])
    prefix = f"S3 block{block}/stride{stride}/bias{bias}"
    v.integer(f"{prefix}: block ID", block, high=2)
    records = result["records"]
    v.check(f"{prefix}: four distinct held-out queries", sorted(r["query"] for r in records) == list(range(4)))
    for method in METHODS:
        path = case_path / f"{method}.npz"
        provenance_path = case_path / f"{method}_provenance.json"
        info = result["maps"][method]
        provenance = read_json(provenance_path)
        with np.load(path, allow_pickle=False) as arrays:
            n = len(arrays["points"])
            v.check(f"{prefix}/{method}: finite map arrays and point count", n == info["points"] and
                    arrays["points"].shape == arrays["normals"].shape == (n, 3) and arrays["radii"].shape == arrays["counts"].shape == (n,) and
                    all(np.isfinite(arrays[name]).all() for name in ("points", "normals", "radii", "counts")) and
                    np.all(arrays["radii"] >= 0))
            v.check(f"{prefix}/{method}: provenance covers every map point", set(provenance) == {str(i) for i in range(n)})
            valid = all(isinstance(ids, list) and bool(ids) and len(ids) == len(set(ids)) and
                        all(isinstance(t, int) and not isinstance(t, bool) and 0 <= t < 20 for t in ids) and
                        arrays["counts"][int(i)] == len(ids) for i, ids in provenance.items())
            v.check(f"{prefix}/{method}: sources are unique history IDs, never held-out, with matching update counts", valid)
        trace = info["build_trace"]
        v.check(f"{prefix}/{method}: exactly 20 history-only build steps", [row["frame_id"] for row in trace] == list(range(20)))
        old = 0
        for row in trace:
            v.check(f"{prefix}/{method}: build accounting at frame {row['frame_id']}", row["old_points"] == old and
                    row["merged_points"] + row["new_points"] == row["input_points"] and
                    row["total_points"] == row["old_points"] + row["new_points"] and
                    min(row["merged_points"], row["new_points"], row["input_points"]) >= 0)
            old = row["total_points"]
        v.check(f"{prefix}/{method}: final map trace and recorded file sizes", old == n and path.stat().st_size == info["map_npz_bytes"] and
                provenance_path.stat().st_size == info["provenance_json_bytes"])
    for record in records:
        q = record["query"]
        tag = f"{prefix}/query{q}"
        selected_match = manifest["matches"][manifest["blocks"][block][20 + q]]
        v.check(f"{tag}: record belongs to condition and held-out timestamp", record_key(record)[:3] == (block, stride, bias) and
                record["timestamp"] == selected_match["depth"]["timestamp"] and record["split"] == ("development" if block == 0 else "test"))
        v.integer(f"{tag}: common pixels nonnegative", record["common_prediction_pixels"])
        with np.load(case_path / f"query_{q}_depths.npz", allow_pickle=False) as arrays:
            target, valid, common = arrays["target"], arrays["target_valid"], arrays["common"]
            v.check(f"{tag}: masks and depth shapes", target.ndim == 2 and valid.dtype == common.dtype == np.bool_ and
                    all(arrays[key].shape == target.shape for key in ("target_valid", "common", *METHODS)))
            expected_common = valid & np.isfinite(arrays["first_write"]) & np.isfinite(arrays["frame_mean"])
            v.check(f"{tag}: saved common mask is independently reconstructed", np.array_equal(common, expected_common))
            denominator = int(valid.sum())
            v.check(f"{tag}: target/common pixel counts match saved masks", denominator == record["valid_target_pixels"] and int(common.sum()) == record["common_prediction_pixels"] and
                    np.all(np.isfinite(target[valid])) and np.all(target[valid] > 0))
            for method in METHODS:
                g = record["geometry"][method]
                compare_stats(v, f"{tag}/{method}: primary geometry statistics recomputed", g, recompute_stats(arrays[method], target, common))
                own = valid & np.isfinite(arrays[method])
                compare_stats(v, f"{tag}/{method}: own-support geometry statistics recomputed", g["own_support"], recompute_stats(arrays[method], target, own))
                coverage = g["coverage_of_valid_target"]
                v.fraction(f"{tag}/{method}: geometry coverage in range", coverage, nullable=not denominator)
                v.check(f"{tag}/{method}: geometry coverage matches masks", coverage is None if not denominator else np.isclose(coverage, float(own.sum() / denominator)))
        v.check(f"{tag}: exact configured retrieval resolutions", set(record["retrieval"]) == {str(width) for width in resolutions})
        for width, pair in record["retrieval"].items():
            for method in METHODS:
                trace = pair[method]
                selected = trace["selected"]
                v.check(f"{tag}/{width}/{method}: four unique valid history selections", len(selected) == len(set(selected)) == 4 and
                        all(isinstance(t, int) and not isinstance(t, bool) and 0 <= t < 20 for t in selected))
                for field in ("candidates",):
                    ids = trace[field]
                    v.check(f"{tag}/{width}/{method}: {field} IDs valid", len(ids) == len(set(ids)) and all(isinstance(t, int) and 0 <= t < 20 for t in ids))
                for field in ("weights", "candidate_counts"):
                    rows = trace[field]
                    v.check(f"{tag}/{width}/{method}: {field} source IDs and values valid", len({r[0] for r in rows}) == len(rows) and
                            all(isinstance(i, int) and 0 <= i < 20 and np.isfinite(value) and value >= 0 for i, value in rows))
                v.fraction(f"{tag}/{width}/{method}: fixed support coverage in range", trace["fixed_measurement_support_coverage"], nullable=not denominator)
                v.fraction(f"{tag}/{width}/{method}: rendered coverage in range", trace["rendered_coverage"])
            a, b = [pair[m]["fixed_measurement_support_coverage"] for m in METHODS]
            expected = None if not denominator else b - a
            v.check(f"{tag}/{width}: coverage delta and set-change flag consistent", pair["selection_set_changed"] ==
                    (set(pair[METHODS[0]]["selected"]) != set(pair[METHODS[1]]["selected"])) and
                    (pair["coverage_delta"] is None if expected is None else np.isclose(pair["coverage_delta"], expected, atol=1e-12)))
    return records


def verify_experiment(v, directory, meta, manifest):
    cfg = meta["config"]
    expected = set(itertools.product(cfg["blocks"], cfg["strides"], map(float, cfg["biases"])))
    v.check("S3: configured conditions contain no duplicates", len(expected) == len(cfg["blocks"]) * len(cfg["strides"]) * len(cfg["biases"]))
    v.check("S3: retrieval resolutions unique", bool(cfg["resolutions"]) and len(cfg["resolutions"]) == len(set(cfg["resolutions"])))
    paths = sorted(directory.glob("*/result.json"))
    results = [(path, read_json(path)) for path in paths]
    conditions = [(r["block"], r["stride"], float(r["bias_m"])) for _, r in results]
    v.check("S3: all configured cases completed exactly once", len(conditions) == len(set(conditions)) == len(expected) and set(conditions) == expected)
    errors = read_json(directory / "errors.json")
    v.check("S3: no recorded experiment errors", errors == [] and meta["errors"] == 0)
    v.check("S3: metadata case counts agree with config and files", meta["expected_cases"] == meta["completed_cases"] == len(expected))
    saved = read_jsonl(directory / "records.jsonl")
    v.check("S3: aggregated records have no duplicates", len(saved) == len({record_key(r) for r in saved}))
    aggregate = {record_key(r): r for r in saved}
    all_records = []
    for path, result in results:
        checked = v.section(str(path.relative_to(directory)), lambda p=path, r=result: verify_case(v, p.parent, r, manifest, cfg["resolutions"]))
        if checked is not None:
            all_records.extend(checked)
    v.check("S3: every case record equals aggregate JSONL record", len(all_records) == len(saved) and
            all(aggregate.get(record_key(r)) == r for r in all_records))
    queries = len(expected) * 4
    retrieval_rows = queries * len(cfg["resolutions"])
    v.check("S3: query/retrieval counts agree with config", len(saved) == meta["paired_queries"] == queries and meta["paired_retrieval_rows"] == retrieval_rows)
    with (directory / "pairs.csv").open(newline="") as stream:
        csv_rows = list(csv.DictReader(stream))
    csv_keys = [(int(r["block"]), int(r["stride"]), float(r["first_frame_depth_axis_bias_m"]), int(r["query"]), int(r["width"])) for r in csv_rows]
    expected_keys = {record_key(r) + (w,) for r in saved for w in cfg["resolutions"]}
    v.check("S3: CSV contains each paired retrieval once", len(csv_rows) == retrieval_rows and len(csv_keys) == len(set(csv_keys)) and set(csv_keys) == expected_keys)
    for row, key in zip(csv_rows, csv_keys):
        record = aggregate[key[:4]]
        pair = record["retrieval"][str(key[4])]
        v.check(f"S3 CSV {key}: matches JSON selections and shared count", int(row["common_prediction_pixels"]) == record["common_prediction_pixels"] and
                all(row[f"{method}_selected"] == ",".join(map(str, pair[method]["selected"])) for method in METHODS) and
                row["selection_set_changed"] == str(pair["selection_set_changed"]))
        for method in METHODS:
            value = pair[method]["fixed_measurement_support_coverage"]
            v.check(f"S3 CSV {key}/{method}: coverage equals JSON", row[f"{method}_support_coverage"] == "" if value is None else
                    np.isclose(float(row[f"{method}_support_coverage"]), value, atol=1e-12))
    v.summary.update(completed_cases=len(results), paired_queries=len(saved), paired_retrieval_rows=len(csv_rows),
                     expected_cases=len(expected), expected_paired_queries=queries, expected_paired_retrieval_rows=retrieval_rows)


def verify_data(v, root, qa_rows, metas, manifests):
    archive_manifest_path = root.parent / "download_manifest.json"
    manifest_hash = sha256(archive_manifest_path)
    v.check("Raw data: download manifest matches both run metadata hashes", all(meta["dataset_archive_manifest_sha256"] == manifest_hash for meta in metas))
    download = read_json(archive_manifest_path)
    archive = root.parent / Path(urlparse(download["source_url"]).path).name
    v.check("Raw data: archive byte count matches download record", archive.stat().st_size == download["expected_size"])
    v.check("Raw data: archive SHA256 matches download record", sha256(archive) == download["sha256"])
    for row in qa_rows:
        for kind in ("rgb", "depth"):
            path = (root / row[f"{kind}_path"]).resolve()
            v.check(f"Raw data: QA {row['sample']} {kind} path stays within dataset", path.is_relative_to(root.resolve()))
            v.check(f"Raw data: QA {row['sample']} {kind} SHA256", sha256(path) == row[f"{kind}_sha256"])
    paths = {m[kind]["path"] for manifest in manifests for m in manifest["matches"] for kind in ("rgb", "depth")}
    v.check("Raw data: every manifest image exists", all((root / name).is_file() for name in paths), dict(image_files=len(paths)))
    v.summary["raw_data_verification"] = dict(status="passed", qa_image_hashes=len(qa_rows) * 2,
                                               archive_sha256=download["sha256"], note="Non-QA images have existence checks; archive integrity is checked as a whole.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qa", type=Path, default=ROOT / "results/S2_rgbd_qa")
    parser.add_argument("--experiment", type=Path, default=ROOT / "results/S3_rgbd_memory")
    parser.add_argument("--data", type=Path, help="Optional extracted TUM sequence directory; also verifies adjacent original archive")
    args = parser.parse_args()
    v = Verifier()
    started = datetime.now(timezone.utc).isoformat()
    qa_meta = v.section("S2 metadata/source archive", lambda: verify_run(v, args.qa, "S2"))
    ex_meta = v.section("S3 metadata/source archive", lambda: verify_run(v, args.experiment, "S3"))
    qa_manifest = v.section("S2 selection manifest read", lambda: read_json(args.qa / "selection_manifest.json"))
    ex_manifest = v.section("S3 selection manifest read", lambda: read_json(args.experiment / "selection_manifest.json"))
    for label, manifest in (("S2", qa_manifest), ("S3", ex_manifest)):
        if manifest is not None:
            v.section(f"{label} selection manifest", lambda m=manifest, l=label: verify_manifest(v, m, l))
    if qa_manifest is not None and ex_manifest is not None:
        v.section("Cross-run frame selection", lambda: v.check("S2/S3: identical recorded data selection", qa_manifest == ex_manifest))
    qa_rows = None
    if qa_meta is not None and qa_manifest is not None:
        qa_rows = v.section("S2 frame QA", lambda: verify_qa(v, args.qa, qa_meta, qa_manifest))
    if ex_meta is not None and ex_manifest is not None:
        v.section("S3 cases and paired records", lambda: verify_experiment(v, args.experiment, ex_meta, ex_manifest))
    if args.data is None:
        v.summary["raw_data_verification"] = dict(status="not_requested", note="Pass means saved evidence is internally consistent; raw data hashes were not rechecked. Use --data.")
    elif all(item is not None for item in (qa_rows, qa_meta, ex_meta, qa_manifest, ex_manifest)):
        v.section("Raw dataset hashes", lambda: verify_data(v, args.data, qa_rows, [qa_meta, ex_meta], [qa_manifest, ex_manifest]))
    else:
        v.errors.append(dict(section="Raw dataset hashes", error="Cannot verify raw data because required run metadata or QA records failed."))
    report = dict(status="passed" if not v.errors and all(c["passed"] for c in v.checks) else "failed",
                  started_utc=started, completed_utc=datetime.now(timezone.utc).isoformat(),
                  validator_sha256=sha256(__file__), qa_directory=str(args.qa.resolve()), experiment_directory=str(args.experiment.resolve()),
                  source_policy="Verify recorded run-time hashes against archived source; current source may differ.",
                  summary=v.summary, checks=v.checks, errors=v.errors)
    output = args.experiment / "verification.json"
    if args.experiment.is_dir():
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))
    print(json.dumps(dict(status=report["status"], checks=len(v.checks), errors=v.errors,
                          summary=v.summary, report=str(output) if args.experiment.is_dir() else None), ensure_ascii=False))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
