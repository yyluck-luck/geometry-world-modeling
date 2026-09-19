"""S26 metadata/source inspection only; never opens NPZ, RGB PNG or GT arrays."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

from saved_heads_adapter import derive_original_functions

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def main():
    m21path = ROOT / "work/S21_baseline_preparation/run_manifest.json"
    m22path = ROOT / "work/S22_filt_shared_precision/run_manifest.json"
    m23path = ROOT / "work/S23_geometry_preparation/manifest.json"
    m17path = ROOT / "docs/S17C_EXECUTION_MANIFEST.json"
    envpath = ROOT / "work/S17C_environment/environment_ready.json"
    m21, m22, m23, m17, env = map(read, (m21path, m22path, m23path, m17path, envpath))
    frames = m21["frames"][:8]
    assert len(frames) == 8 and frames == m22["frames"][:8]
    assert [f["index"] for f in frames] == list(range(8))
    assert m21["checkpoint_sha256"] == m22["checkpoint_sha256"]
    assert env["status"] == "PASS_IMPORT_ONLY_NO_MODEL"
    assert Path(m17["python"]).is_file() and Path(m17["overlay"]).is_dir()
    source_root = Path(m17["source_root"])
    source_ids = {p: h for p, h in m17["identities"].items() if Path(p).is_relative_to(source_root)}
    for p, expected in source_ids.items():
        assert sha(p) == expected, p
    source_ids.update({str(p): sha(p) for p in (m17path, Path(m17["source_plan"]), envpath,
                                                 Path(m17["import_smoke"]))})
    binding = {
        "schema": "s26-original-consumer-source-binding-draft-v1",
        "source_commit": m17["source_commit"], "source_root": str(source_root),
        "embedded_root": str(source_root / "extern/CUT3R"),
        "python": m17["python"], "overlay": m17["overlay"],
        "source_identities": source_ids,
        "dependency_identity_parent_manifest": str(m17path),
        "status": "DRAFT_NOT_EXPERIMENT_FREEZE",
    }
    write("source_binding.json", binding)
    wrapper = source_root / "extern/CUT3R/surfel_inference.py"
    module, proof = derive_original_functions(wrapper.read_text())
    derived_path = HERE / "derived_original_functions.py"
    derived_path.write_text(ast.unparse(module) + "\n")
    compile(derived_path.read_text(), str(derived_path), "exec")

    names = {
        "common_old_depth_original4": ROOT / "results/S21_baseline/original4",
        "cut3r": ROOT / "results/S21_baseline/cut3r",
        "ttt3r": ROOT / "results/S21_baseline/ttt3r",
        "filt3r": ROOT / "results/S22_filt_shared_precision/filt3r",
    }
    archives = {}
    receipts = {}
    for name, path in names.items():
        receipt_path = path / "receipt.json"
        r = read(receipt_path)
        n = 4 if name == "common_old_depth_original4" else 8
        assert r["status"] == "PASS" and r["frames_completed"] >= n
        assert r["manifest_sha256"] == sha(m22path if name == "filt3r" else m21path)
        selected = r["outputs"][:n]
        assert [e["index"] for e in selected] == list(range(n))
        archives[name] = []
        for entry in selected:
            actual_path = path / entry["file"]
            assert actual_path.is_file()
            archives[name].append(dict(index=entry["index"], path=str(actual_path),
                                       sha256=entry["sha256"], bytes=actual_path.stat().st_size,
                                       identity_basis="sealed producer receipt; NPZ bytes not opened this turn"))
        receipts[name] = dict(path=str(receipt_path), sha256=sha(receipt_path), mode=r["mode"],
                              source=r["actual_source"], frames_completed=r["frames_completed"])
    coverage = []
    for i, f in enumerate(frames):
        d = m23["frames"][i]
        assert d["index"] == i and d["rgb_time"] == f["rgb_time"]
        dp = Path(d["depth_file"]) if d["depth_file"] else None
        coverage.append({**d, "exists": dp.is_file() if dp else False,
                         "bytes": dp.stat().st_size if dp and dp.is_file() else None,
                         "absolute_time_delta_s": abs(d["depth_time"] - f["rgb_time"]) if dp else None,
                         "valid_pixel_count": "UNKNOWN_NOT_DECODED"})
    assert all(d["exists"] for d in coverage)
    inputs = {
        "schema": "s26-eight-frame-consumer-pilot-candidate-v1", "status": "DRAFT_NOT_FROZEN",
        "frames": frames, "prefix_length": 4, "new_frame_indices": [4, 5, 6, 7],
        "rgb_time_span_seconds": frames[-1]["rgb_time"] - frames[0]["rgb_time"],
        "archives": archives, "producer_receipts": receipts,
        "given_pose_condition": {"source": m21["gt_file"], "expected_sha256": m21["gt_sha256"],
                                 "paired_timestamp_source": str(m21path),
                                 "coordinates_read_now": False,
                                 "role": "common oracle camera condition, not blinded/deployable pose estimation"},
        "depth_coverage_metadata": coverage,
        "depth_content_identity": "NOT_BOUND_HERE; S23 metadata manifest has no per-PNG SHA. Inherit an existing trustworthy byte seal if available; otherwise seal a new scoring snapshot only after all four GA jobs seal, before PNG decode.",
        "depth_input_prohibition": "Sensor depth is scoring-only after all GA outputs seal; never used as common old depth",
        "common_old_depth": "one original4 given-pose/no-depth GA, sealed once and reused by all three eight-frame runs",
        "metadata_identities": {str(p): sha(p) for p in (m21path, m22path, m23path)},
    }
    write("candidate_inputs.json", inputs)
    assert "torch" not in sys.modules and "numpy" not in sys.modules
    receipt = {
        "schema": "s26-source-metadata-preparation-v1", "recorded_utc": datetime.now(timezone.utc).isoformat(),
        "passed_static_preparation": True, "experiment_approved_or_frozen": False,
        "source_file_count": len(source_ids) - 4, "source_proof": proof,
        "archive_records": sum(map(len, archives.values())),
        "frame_count": 8, "depth_metadata_matched_count": 8,
        "max_rgb_depth_delta_seconds": max(x["absolute_time_delta_s"] for x in coverage),
        "NPZ_RGB_GT_bytes_opened": 0, "prediction_array_decodes": 0, "GT_pose_coordinate_parses": 0,
        "GT_depth_png_decodes": 0, "model_instantiations": 0, "model_forwards": 0,
        "GA_runs": 0, "torch_or_numpy_imported": False, "frozen_files_modified": False,
        "identities": {str(HERE / name): sha(HERE / name) for name in (
            "saved_heads_adapter.py", "prepare_metadata.py", "source_binding.json",
            "derived_original_functions.py", "candidate_inputs.json", "plan.md")},
        "runtime_and_numerical_compatibility": "NOT_RUN",
    }
    write("preparation_receipt.json", receipt)
    print(json.dumps({k: receipt[k] for k in ("recorded_utc", "passed_static_preparation", "source_file_count",
        "archive_records", "depth_metadata_matched_count", "max_rgb_depth_delta_seconds",
        "NPZ_RGB_GT_bytes_opened", "GA_runs", "model_forwards")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
