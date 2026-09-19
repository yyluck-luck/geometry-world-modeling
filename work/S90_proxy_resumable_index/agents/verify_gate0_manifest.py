#!/usr/bin/env python3
"""Offline Gate-0 qualification checker for a frozen GRC pilot manifest.

This tool never opens a URL, downloads data, decodes model outputs, or reads
future answer bytes through the selector.  It validates local paths, declared
camera/depth semantics, scene-level split separation, and manifest bindings.
It is deliberately a qualification gate, not a scientific score.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any


SCHEMA = "grc-gate0-manifest-v1"
SPLITS = ("development", "calibration", "test")
SHA256_HEX = 64


class Check:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.counts: dict[str, int] = {}

    def ok(self, name: str, value: bool, detail: str) -> None:
        self.counts[name] = self.counts.get(name, 0) + 1
        if not value:
            self.errors.append(f"{name}: {detail}")

    def warn(self, name: str, detail: str) -> None:
        self.warnings.append(f"{name}: {detail}")


def finite(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(float(x))


def nonempty_string(x: Any) -> bool:
    return isinstance(x, str) and bool(x.strip())


def sha256_file(path: Path, chunk: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            block = f.read(chunk)
            if not block:
                return h.hexdigest()
            h.update(block)


def path_value(root: Path, value: Any) -> Path | None:
    if not nonempty_string(value):
        return None
    p = Path(value)
    return p if p.is_absolute() else (root / p)


def check_matrix(c: Check, value: Any, shape: tuple[int, int], name: str) -> None:
    valid = isinstance(value, list) and len(value) == shape[0] and all(
        isinstance(row, list) and len(row) == shape[1] and all(finite(x) for x in row)
        for row in value
    )
    c.ok("camera_matrix", valid, f"{name} must be finite {shape[0]}x{shape[1]}")


def check_file_record(c: Check, root: Path, rec: Any, name: str, do_hash: bool) -> set[Path]:
    """Check a local file record; returns resolved paths used by the manifest."""
    used: set[Path] = set()
    c.ok("file_record", isinstance(rec, dict), f"{name} must be an object")
    if not isinstance(rec, dict):
        return used
    p = path_value(root, rec.get("path"))
    c.ok("file_path", p is not None, f"{name}.path is missing")
    declared = rec.get("sha256")
    c.ok("file_sha256", isinstance(declared, str) and len(declared) == SHA256_HEX and all(x in "0123456789abcdef" for x in declared.lower()), f"{name}.sha256 must be lowercase SHA-256")
    if p is None:
        return used
    p = p.resolve()
    used.add(p)
    c.ok("file_exists", p.is_file(), f"{name}: local file does not exist: {p}")
    if p.is_file() and do_hash and isinstance(declared, str) and len(declared) == SHA256_HEX:
        actual = sha256_file(p)
        c.ok("file_hash", actual == declared.lower(), f"{name}: SHA-256 mismatch (declared {declared}, actual {actual})")
    size = rec.get("bytes")
    if size is not None:
        c.ok("file_bytes", isinstance(size, int) and size >= 0 and (not p.is_file() or p.stat().st_size == size), f"{name}.bytes must equal the local size")
    return used


def validate(manifest_path: Path, do_hash: bool) -> dict[str, Any]:
    c = Check()
    root = manifest_path.parent.resolve()
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"schema": "gate0-report-v1", "status": "INVALID", "errors": [f"manifest_read: {exc}"], "warnings": [], "network_used": False}
    c.ok("top_object", isinstance(manifest, dict), "manifest must be a JSON object")
    if not isinstance(manifest, dict):
        return {"schema": "gate0-report-v1", "status": "INVALID", "errors": c.errors, "warnings": c.warnings, "network_used": False}
    c.ok("schema", manifest.get("schema") == SCHEMA, f"expected schema {SCHEMA}")
    c.ok("manifest_version", nonempty_string(manifest.get("manifest_version")), "manifest_version is required")
    source = manifest.get("source")
    c.ok("source_object", isinstance(source, dict), "source must be an object")
    if isinstance(source, dict):
        for key in ("dataset", "revision", "license", "scene_kind"):
            c.ok("source_field", nonempty_string(source.get(key)), f"source.{key} is required; use UNKNOWN only with a warning and downgraded gate")
        if source.get("license") == "UNKNOWN":
            c.warn("license", "license is UNKNOWN; this manifest cannot be used for a release claim")
        c.ok("source_no_url_fetch", source.get("network_fetch_performed") is False, "network_fetch_performed must be false for this offline checker")
    splits = manifest.get("splits")
    c.ok("splits_object", isinstance(splits, dict), "splits must contain development/calibration/test")
    split_scene_sets: dict[str, set[str]] = {}
    if isinstance(splits, dict):
        for split in SPLITS:
            rows = splits.get(split)
            c.ok("split_present", isinstance(rows, list) and bool(rows), f"split {split} must be a non-empty list")
            scenes: set[str] = set()
            if isinstance(rows, list):
                for i, unit_id in enumerate(rows):
                    c.ok("split_unit_id", nonempty_string(unit_id), f"splits.{split}[{i}] must be a unit_id string")
                    if nonempty_string(unit_id):
                        scenes.add(str(unit_id))
            split_scene_sets[split] = scenes
        for a in SPLITS:
            for b in SPLITS:
                if a < b:
                    c.ok("split_disjoint", split_scene_sets.get(a, set()).isdisjoint(split_scene_sets.get(b, set())), f"split ids overlap between {a} and {b}")
    units = manifest.get("units")
    c.ok("units_list", isinstance(units, list) and bool(units), "units must be a non-empty list")
    by_id: dict[str, dict[str, Any]] = {}
    all_used: set[Path] = set()
    if isinstance(units, list):
        for idx, u in enumerate(units):
            prefix = f"units[{idx}]"
            c.ok("unit_object", isinstance(u, dict), f"{prefix} must be an object")
            if not isinstance(u, dict):
                continue
            unit_id = u.get("unit_id")
            scene = u.get("scene_id")
            split = u.get("split")
            c.ok("unit_identity", nonempty_string(unit_id) and nonempty_string(scene), f"{prefix} needs unit_id and scene_id")
            c.ok("unit_split", split in SPLITS, f"{prefix}.split must be one of {SPLITS}")
            if nonempty_string(unit_id):
                c.ok("unit_unique", str(unit_id) not in by_id, f"duplicate unit_id {unit_id}")
                by_id[str(unit_id)] = u
            if split in SPLITS and nonempty_string(unit_id):
                c.ok("unit_listed", str(unit_id) in split_scene_sets.get(split, set()), f"{prefix} is not listed in its split")
            for key in ("query_time_s", "future_horizon_s"):
                c.ok("unit_time", finite(u.get(key)), f"{prefix}.{key} must be finite")
            history = u.get("history")
            c.ok("history_list", isinstance(history, list) and len(history) >= 6, f"{prefix}.history needs >=6 candidate frames")
            target = u.get("future_target")
            c.ok("future_target_object", isinstance(target, dict), f"{prefix}.future_target is required")
            if not isinstance(target, dict):
                continue
            query_cam = u.get("query_camera")
            c.ok("query_camera_object", isinstance(query_cam, dict), f"{prefix}.query_camera is required")
            for cam_name, cam in (("query_camera", query_cam), ("future_target.camera", target.get("camera"))):
                if not isinstance(cam, dict):
                    continue
                check_matrix(c, cam.get("K"), (3, 3), f"{prefix}.{cam_name}.K")
                check_matrix(c, cam.get("T_world_from_camera"), (4, 4), f"{prefix}.{cam_name}.T_world_from_camera")
                # The matrix field is named T_world_from_camera; allowing a
                # second convention here would silently swap poses.  A
                # different convention must be converted and given a new
                # manifest schema rather than accepted as an alias.
                c.ok("camera_semantics", cam.get("coordinate_system") == "world_from_camera", f"{prefix}.{cam_name}.coordinate_system must be exactly world_from_camera")
                c.ok("camera_units", nonempty_string(cam.get("translation_unit")), f"{prefix}.{cam_name}.translation_unit is required")
            depth_sem = target.get("depth_semantics")
            c.ok("depth_semantics", isinstance(depth_sem, dict), f"{prefix}.future_target.depth_semantics is required")
            if isinstance(depth_sem, dict):
                for key in ("kind", "unit", "invalid_value", "registered_to"):
                    c.ok("depth_field", key in depth_sem, f"{prefix}.future_target.depth_semantics.{key} is required")
                c.ok("depth_kind", depth_sem.get("kind") in ("camera_z", "ray_range", "inverse_depth", "disparity"), f"{prefix}: unsupported depth kind")
                c.ok("depth_registration", depth_sem.get("registered_to") == "future_target_rgb", f"{prefix}: target depth registration must be explicit")
            target_paths: set[Path] = set()
            for key in ("rgb", "depth", "valid_mask"):
                if key in target:
                    target_paths |= check_file_record(c, root, target.get(key), f"{prefix}.future_target.{key}", do_hash)
            target_paths |= check_file_record(c, root, target.get("pose"), f"{prefix}.future_target.pose", do_hash) if target.get("pose") is not None else set()
            selection_paths = set()
            allowed = u.get("selection_input_paths")
            c.ok("selection_input_list", isinstance(allowed, list), f"{prefix}.selection_input_paths must be a list")
            if isinstance(allowed, list):
                for j, raw in enumerate(allowed):
                    p = path_value(root, raw)
                    c.ok("selection_input_path", p is not None, f"{prefix}.selection_input_paths[{j}] invalid")
                    if p is not None:
                        selection_paths.add(p.resolve())
            c.ok("future_isolation", target_paths.isdisjoint(selection_paths), f"{prefix}: future answer path appears in selector input paths")
            for j, h in enumerate(history if isinstance(history, list) else []):
                hp = f"{prefix}.history[{j}]"
                c.ok("history_object", isinstance(h, dict), f"{hp} must be an object")
                if not isinstance(h, dict):
                    continue
                c.ok("history_id", nonempty_string(h.get("frame_id")), f"{hp}.frame_id required")
                c.ok("history_timestamp", finite(h.get("timestamp_s")), f"{hp}.timestamp_s required")
                c.ok("past_only", finite(h.get("timestamp_s")) and finite(u.get("query_time_s")) and float(h["timestamp_s"]) < float(u["query_time_s"]), f"{hp} is not strictly before query_time_s")
                cam = h.get("camera")
                if isinstance(cam, dict):
                    check_matrix(c, cam.get("K"), (3, 3), f"{hp}.camera.K")
                    check_matrix(c, cam.get("T_world_from_camera"), (4, 4), f"{hp}.camera.T_world_from_camera")
                    c.ok("history_camera_units", nonempty_string(cam.get("translation_unit")), f"{hp}.camera.translation_unit required")
                else:
                    c.ok("history_camera_object", False, f"{hp}.camera required")
                for key in ("rgb", "depth"):
                    if key in h:
                        all_used |= check_file_record(c, root, h.get(key), f"{hp}.{key}", do_hash)
                c.ok("history_has_geometry", "depth" in h or isinstance(h.get("geometry_features"), dict), f"{hp} needs depth or declared past geometry_features")
            all_used |= target_paths
    min_per_scene = manifest.get("minimum")
    c.ok("minimum_object", isinstance(min_per_scene, dict), "minimum must declare pilot thresholds")
    if isinstance(min_per_scene, dict):
        c.ok("minimum_scenes", min_per_scene.get("independent_scenes", 0) >= 3, "Gate 0 pilot requires >=3 independent scenes")
        c.ok("minimum_history", min_per_scene.get("history_candidates", 0) >= 6, "Gate 0 pilot requires >=6 history candidates")
        c.ok("minimum_queries", min_per_scene.get("future_queries", 0) >= 3, "Gate 0 pilot requires >=3 future queries")
    # A scene must be declared as a scene, not inferred from file names.
    scenes = {u.get("scene_id") for u in units if isinstance(u, dict) and nonempty_string(u.get("scene_id"))} if isinstance(units, list) else set()
    c.ok("independent_scene_count", len(scenes) >= 3, f"only {len(scenes)} scene_id values are present; need >=3 for Gate 0 pilot")
    report = {
        "schema": "gate0-report-v1",
        "status": "PASS" if not c.errors else "REJECT",
        "gate": "GATE0_DATA_QUALIFICATION",
        "checker": str(Path(__file__).resolve()),
        "checker_sha256": sha256_file(Path(__file__).resolve()),
        "manifest": str(manifest_path.resolve()),
        "manifest_schema": manifest.get("schema"),
        "manifest_sha256": sha256_file(manifest_path),
        "network_used": False,
        "file_hashes_checked": bool(do_hash),
        "unit_count": len(units) if isinstance(units, list) else 0,
        "scene_count": len(scenes),
        "errors": c.errors,
        "warnings": c.warnings,
        "checks": c.counts,
        "scientific_claim": "qualification_only; no future error or method gain measured",
    }
    return report


def main() -> int:
    p = argparse.ArgumentParser(description="Offline GRC Gate-0 manifest qualification; never uses the network")
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--no-hash", action="store_true", help="validate schema/path metadata without reading file bytes")
    args = p.parse_args()
    report = validate(args.manifest.resolve(), do_hash=not args.no_hash)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(args.report.resolve()), "errors": len(report["errors"]), "network_used": False}, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
