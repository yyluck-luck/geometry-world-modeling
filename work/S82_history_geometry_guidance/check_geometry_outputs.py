#!/usr/bin/env python3
"""Read-only S82 component archive review; never loads a model or source image.

Use --selftest for artificial pose cases only. Real output review requires an
explicit execution directory, frozen contract SHA, and a new report pathname.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
from datetime import datetime, timezone
import numpy as np

IDS = [12, 13, 18, 19]
SHAPES = {"pts3d_in_self_view": [1, 384, 512, 3],
          "pts3d_in_other_view": [1, 384, 512, 3],
          "conf_self": [1, 384, 512], "conf": [1, 384, 512],
          "camera_pose": [1, 7], "rgb": [1, 384, 512, 3]}
POSE_ATOL, POSE_RTOL, RIGID_ATOL = 2e-6, 2e-6, 5e-6


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def independent_pose(pose):
    """Float64 normalized wxyz formula, independently of official torch code."""
    v = np.asarray(pose, dtype=np.float64)
    require(v.shape == (7,) and np.isfinite(v).all(), "invalid pose vector")
    q = v[3:]
    norm = np.linalg.norm(q)
    require(np.isfinite(norm) and norm > 0, "zero/invalid quaternion")
    w, x, y, z = q / norm
    r = np.array([[1-2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y)],
                  [2*(x*y+w*z), 1-2*(x*x+z*z), 2*(y*z-w*x)],
                  [2*(x*z-w*y), 2*(y*z+w*x), 1-2*(x*x+y*y)]])
    c = np.eye(4, dtype=np.float64)
    c[:3, :3], c[:3, 3] = r, v[:3]
    return c


def check_camera(actual, raw_pose):
    a = np.asarray(actual)
    require(a.shape == (4, 4) and np.isfinite(a).all(), "invalid c2w")
    reference = independent_pose(raw_pose)
    require(np.allclose(a, reference, atol=POSE_ATOL, rtol=POSE_RTOL), "pose decode mismatch")
    require(np.array_equal(a[3], [0, 0, 0, 1]), "homogeneous row mismatch")
    rotation = a[:3, :3].astype(np.float64)
    require(np.allclose(rotation.T @ rotation, np.eye(3), atol=RIGID_ATOL, rtol=0), "rotation orthogonality")
    require(abs(np.linalg.det(rotation)-1) <= RIGID_ATOL, "rotation determinant")
    return float(np.abs(a-reference).max())


def review(execution, contract_path, expected_sha):
    execution = execution.resolve()
    raw_contract = contract_path.read_bytes()
    require(sha(raw_contract) == expected_sha, "contract SHA mismatch")
    c = json.loads(raw_contract)
    require([r["history_id"] for r in c["history_rgb"]] == IDS, "contract ID order")
    require(c["generation_slot_order"] == [19, 18, 13, 12], "generation slot order")
    require(c["output_schema"]["head_shapes"] == SHAPES, "contract head schema")
    receipt_bytes = (execution/"RECEIPT.json").read_bytes()
    r = json.loads(receipt_bytes)
    supervision_bytes = (execution/"SUPERVISION.json").read_bytes()
    s = json.loads(supervision_bytes)
    require(r["status"] == "RAW_FOUR_HISTORY_COMPLETE", "worker incomplete")
    require(s["status"] == "COMPLETE" and s["returncode"] == 0 and s["attempts"] == 1, "supervision incomplete")
    require(r["contract_sha256"] == s["contract_sha256"] == expected_sha, "receipt contract mismatch")
    require(r["runner_sha256"] == c["runner_sha256"], "runner identity mismatch")
    for key, expected in {"model_loads": 1, "recurrent_calls": 1, "downstream_head_calls": 4,
                          "frames_completed": 4, "image_decodes": 4, "optimizer_calls": 0,
                          "render_calls": 0, "generation_calls": 0}.items():
        require(r[key] == expected, "call count: " + key)
    require(r["model_training"] is False and r["fresh_recurrent_state"] is True, "eval/state")
    require(r["loaded_previous_state"] is False and r["target_or_depth_inputs"] is False, "input scope")
    require(not r["prohibited_open_attempts"], "prohibited scientific open")
    actual_reads = r["scientific_input_reads"]
    expected_reads = c["history_rgb"]
    require(len(actual_reads) == len(expected_reads) == 4, "RGB identity read count")
    for a, b in zip(actual_reads, expected_reads):
        require(all(a[k] == b[k] for k in ["path", "sha256", "size_bytes"]), "input identity")
    checkpoint = r["checkpoint_identity"]
    require(checkpoint["inherited_sha256"] == c["checkpoint"]["sha256"] and checkpoint["current_sha256_recomputed"] is False, "inherited checkpoint identity")
    require(all(checkpoint[k] == c["checkpoint"][k] for k in ["path", "size_bytes", "mtime_ns"]), "checkpoint stat identity")
    require(r["input_open_counts"] == {v["path"]: v["expected_file_read_opens"] for v in c["history_rgb"]+[c["checkpoint"]]}, "scientific file open count")
    require([v["history_id"] for v in r["output_heads"]] == IDS, "output ID order")
    require([v["inference_row"] for v in r["output_heads"]] == list(range(4)), "output row order")
    require(r["preprocessing"]["image_paths_in_decode_order"] == [v["path"] for v in c["history_rgb"]], "decode order")
    require(r["preprocessing"]["processed_wh"] == [[512, 384]]*4, "processed shape")
    records = r["artifacts"]
    expected_names = {"PREPROCESSED_INPUTS.npz", "PREDICTED_CAMERAS.npz"} | {f"head_{i:02d}_history_{hid}.npz" for i, hid in enumerate(IDS)}
    require(len(records) == 6 and {Path(v["path"]).name for v in records} == expected_names, "archive set")
    arrays, stats = {}, {}
    for record in records:
        path = Path(record["path"]).resolve()
        require(path.parent == execution, "artifact outside execution directory")
        raw = path.read_bytes()
        require(len(raw) == record["size_bytes"] and sha(raw) == record["sha256"], "archive hash/size")
        with np.load(io.BytesIO(raw), allow_pickle=False) as archive:
            require(len(archive.files) == len(set(archive.files)) and set(archive.files) == set(record["tensors"]), "archive keys")
            values = {k: archive[k] for k in archive.files}
        stats[path.name] = {}
        for key, value in values.items():
            meta = record["tensors"][key]
            require(list(value.shape) == meta["shape"] and str(value.dtype) == meta["dtype"], "shape/dtype metadata")
            require(value.nbytes == meta["body_bytes"] and sha(value.tobytes(order="C")) == meta["body_sha256"], "tensor body hash")
            require(value.dtype.kind in "biuf" and np.isfinite(value).all(), "nonfinite or nonnumeric archive")
            stats[path.name][key] = {"shape": list(value.shape), "dtype": str(value.dtype),
                                    "min": float(value.min()), "max": float(value.max())}
        arrays[path.name] = values
    pre = arrays["PREPROCESSED_INPUTS.npz"]
    coordinate_keys = {"K_native_approx", "K_512_approx", "native_to_512", "grid512_to_grid576"}
    require(set(pre) == coordinate_keys | {"history_ids", "images_normalized", "rgb01_reconstructed_from_normalized"}, "preprocessing archive keys")
    require(pre["history_ids"].dtype == np.int64 and np.array_equal(pre["history_ids"], IDS), "preprocessing IDs")
    images = pre["images_normalized"]
    rgb01 = pre["rgb01_reconstructed_from_normalized"]
    require(images.shape == (4, 3, 384, 512) and images.dtype == np.float32, "preprocessed normalized shape/dtype")
    require(rgb01.shape == (4, 384, 512, 3) and rgb01.dtype == np.float32, "preprocessed RGB01 shape/dtype")
    require(images.min() >= -1 and images.max() <= 1 and rgb01.min() >= 0 and rgb01.max() <= 1, "declared normalization range")
    require(np.array_equal(rgb01, (images.transpose(0, 2, 3, 1)+1.)/2.), "RGB01 normalization inverse")
    for key in coordinate_keys:
        require(pre[key].shape == (3, 3) and pre[key].dtype == np.float64, "coordinate metadata shape/dtype")
        require(np.array_equal(pre[key], np.asarray(c["coordinates"][key], dtype=np.float64)), "coordinate contract mismatch")
    cameras = arrays["PREDICTED_CAMERAS.npz"]
    require(set(cameras) == {"history_ids", "predicted_c2w"}, "camera archive keys")
    require(cameras["history_ids"].dtype == np.int64 and np.array_equal(cameras["history_ids"], IDS), "camera IDs")
    require(cameras["predicted_c2w"].shape == (4, 4, 4) and cameras["predicted_c2w"].dtype == np.float32, "camera shape/dtype")
    max_error = 0.0
    for i, hid in enumerate(IDS):
        name = f"head_{i:02d}_history_{hid}.npz"
        head = arrays[name]
        require(set(head) == set(SHAPES), "six head keys")
        for key, shape in SHAPES.items():
            require(list(head[key].shape) == shape and head[key].dtype == np.float32, "raw head shape/dtype")
        item = r["output_heads"][i]
        require(item["artifact"] == next(v for v in records if Path(v["path"]).name == name), "head artifact binding")
        require(set(item["finite"]) == set(SHAPES) and all(v is True for v in item["finite"].values()), "head finite receipt")
        saved = cameras["predicted_c2w"][i]
        require(np.array_equal(saved.astype(np.float64), np.asarray(item["official_decoded_predicted_c2w"])), "camera receipt/archive mismatch")
        max_error = max(max_error, check_camera(saved, head["camera_pose"][0]))
    return {"status": "PASS_COMPONENT_OUTPUTS_ONLY", "contract_sha256": expected_sha,
            "receipt_sha256": sha(receipt_bytes), "supervision_sha256": sha(supervision_bytes),
            "archive_sha256": {Path(v["path"]).name: v["sha256"] for v in records},
            "history_ids": IDS, "component_statistics_only": stats,
            "max_pose_abs_difference": max_error, "pose_atol": POSE_ATOL,
            "pose_rtol": POSE_RTOL, "rigid_atol": RIGID_ATOL,
            "scientific_quality_evaluated": False, "GT_read": False,
            "model_calls": 0, "source_RGB_or_depth_decodes": 0}


def selftest():
    cases = [[0, 0, 0, 1, 0, 0, 0], [1, -2, 3, 2, 0, 0, 0],
             [0, 0, 0, 0, 1, 0, 0], [0, 0, 0, 1, 0, 0, 1],
             [0, 0, 0, -1, 0, 0, -1]]
    matrices = [independent_pose(x) for x in cases]
    require(np.array_equal(matrices[0], np.eye(4)), "identity example")
    require(np.array_equal(matrices[1][:3, 3], [1, -2, 3]), "translation example")
    require(np.allclose(matrices[2][:3, :3], np.diag([1, -1, -1])), "180deg example")
    require(np.allclose(matrices[3][:3, :3] @ [1, 0, 0], [0, 1, 0]), "90deg example")
    require(np.array_equal(matrices[3], matrices[4]), "quaternion sign equivalence")
    for v, m in zip(cases, matrices):
        check_camera(m.astype(np.float32), v)
    try:
        independent_pose([0]*7)
    except ValueError:
        pass
    else:
        raise ValueError("zero quaternion accepted")
    return {"status": "PASS_SYNTHETIC_POSE_CASES_ONLY", "artificial_valid_cases": 5,
            "zero_quaternion_rejected": True, "real_output_files_read": 0,
            "model_calls": 0, "source_image_decodes": 0}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--execution", type=Path)
    p.add_argument("--contract", type=Path)
    p.add_argument("--contract-sha256")
    p.add_argument("--report", type=Path, required=True)
    a = p.parse_args()
    require(not a.report.exists(), "refusing to overwrite review record")
    if a.selftest:
        require(a.execution is None and a.contract is None and a.contract_sha256 is None, "selftest has no scientific input")
    else:
        require(all([a.execution, a.contract, a.contract_sha256]), "explicit frozen inputs required")
    result = {}
    try:
        result = selftest() if a.selftest else review(a.execution, a.contract, a.contract_sha256)
    except Exception as exc:
        result = {"status": "FAILED", "error": repr(exc)}
        raise
    finally:
        result.update(recorded_utc=datetime.now(timezone.utc).isoformat(),
                      checker_sha256=sha(Path(__file__).read_bytes()))
        with a.report.open("x") as output:
            json.dump(result, output, ensure_ascii=False, indent=2, allow_nan=False)
            output.write("\n")
