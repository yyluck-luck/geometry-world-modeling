#!/usr/bin/env python3
"""Run three newly frozen S8 RGB blocks using the unchanged S6 model runner.

This controller reads depth bytes only for SHA256 integrity checks. It never
decodes measurements or passes their paths to the model. It does not compare
new scenes with S5 and does not perform measurement scoring or video generation.
See docs/S8_CONTROLLER_REVIEW_NOTES.md for the protocol/manifest contract.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import signal
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
RUNNER_SHA = "cc3ae6fd6243ce3531e540dc8c70ef61af0e868c919c7232a16616cf750ba292"
BASE_RUNNER_SHA = "efb3c8b72ada668818d4211e6d5bb4aa357a3404778cf29d849f8551160bf923"
CHECKPOINT_SHA = "7a7d83e47f822e040980c8f5aff4c15aa94366d469d3ceae51fa30cc2f62327d"
CHECKPOINT_BYTES = 2994205002
COMMIT = "8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf"
ADAPTER_SHA = "6939dcead1b87e920eafce9aae47c1cc9a46b7a651ef816b3f521c779582152e"
MAX_RSS_BYTES = 16 * 1024**3
TIMEOUT_SECONDS = 900
PRECISION = ("Parameters, inputs and saved outputs FP32; official encoder internally "
             "casts Q/K to FP16 for RoPE and restores the original dtype")
PROTOCOL_CONTRACT = {
    "schema": "s8-controller-v1", "stage": "S8", "block_count": 3,
    "frames_per_block": 24, "history_count": 20, "query_count": 4,
    "splits": ["test", "test", "test"], "device": "cpu",
    "cpu_threads": 8, "seed": 0, "dtype": "float32",
    "runner_sha256": RUNNER_SHA, "base_runner_sha256": BASE_RUNNER_SHA,
    "checkpoint_sha256": CHECKPOINT_SHA, "checkpoint_bytes": CHECKPOINT_BYTES,
    "commit": COMMIT, "adapter_sha256": ADAPTER_SHA,
    "timeout_seconds_per_block": TIMEOUT_SECONDS, "max_rss_bytes": MAX_RSS_BYTES,
    "depth_sent_to_model": False, "query_updates_state": False,
}
ARRAY_SHAPES = {
    "pts3d_in_self_view": [1, 224, 224, 3], "pts3d_in_other_view": [1, 224, 224, 3],
    "conf_self": [1, 224, 224], "conf": [1, 224, 224], "rgb": [1, 224, 224, 3],
    "camera_pose": [1, 7], "camera_c2w": [1, 4, 4],
}


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(2**20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, f"Duplicate JSON key: {key}")
        value[key] = item
    return value


def read_json(content):
    return json.loads(content, object_pairs_hook=_unique_object,
                      parse_constant=lambda value: (_ for _ in ()).throw(
                          ValueError(f"Nonfinite JSON literal: {value}")))


def write_json(path, value):
    path = Path(path)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    temp.replace(path)


def parse_protocol(content):
    """Read a JSON protocol or one explicit machine-readable Markdown fence."""
    if content.lstrip().startswith("{"):
        protocol = read_json(content)
    else:
        blocks = re.findall(r"^```s8-controller-json\s*\n(.*?)^```\s*$", content,
                            flags=re.MULTILINE | re.DOTALL)
        require(len(blocks) == 1, "Protocol needs exactly one s8-controller-json fence")
        protocol = read_json(blocks[0])
    require(isinstance(protocol, dict), "Protocol must contain a JSON object")
    for key, expected in PROTOCOL_CONTRACT.items():
        if key == "splits":
            continue
        actual = protocol.get(key)
        require(type(actual) is type(expected) and actual == expected,
                f"Protocol declaration mismatch: {key}")
    splits = protocol.get("splits")
    require(isinstance(splits, list) and len(splits) == 3 and
            all(isinstance(split, str) and split in ("development", "test") for split in splits),
            "Protocol splits must declare three development/test labels")
    return protocol


def valid_sha(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def safe_data_path(data, value):
    """Reject traversal, foreign path syntax, aliases, and escaped symlinks."""
    require(isinstance(value, str) and value and "\\" not in value and "\0" not in value,
            "Expected a nonempty POSIX relative data path")
    relative = PurePosixPath(value)
    require(not relative.is_absolute() and ".." not in relative.parts and
            ":" not in value and str(relative) == value and relative.parts,
            "Expected a safe canonical relative data path")
    root = Path(data).resolve(strict=True)
    target = (root / value).resolve(strict=True)
    require(target.is_relative_to(root) and target.is_file(),
            f"Data path is not a regular file inside --data: {value}")
    return target


def validate_manifest(manifest, data, protocol_sha256, protocol):
    require(isinstance(manifest, dict), "Manifest must be an object")
    require(valid_sha(protocol_sha256) and manifest.get("protocol_sha256") == protocol_sha256,
            "Manifest protocol_sha256 does not match the supplied frozen protocol")
    require(manifest.get("runner_sha256") == RUNNER_SHA, "Manifest runner_sha256 mismatch")
    # Additional matching declarations are welcome, but contradictory ones fail.
    for key, expected in protocol.items():
        if key in manifest and key not in ("schema",):
            require(type(manifest[key]) is type(expected) and manifest[key] == expected,
                    f"Manifest/protocol declaration mismatch: {key}")
    blocks = manifest.get("blocks")
    require(isinstance(blocks, list) and len(blocks) == 3, "Expected exactly three blocks")
    require([b.get("block") for b in blocks] == [0, 1, 2] and
            all(type(b.get("block")) is int for b in blocks), "Expected ordered block IDs 0,1,2")
    require([b.get("split") for b in blocks] == protocol["splits"], "Manifest split mismatch")
    identities, prepared = [], []
    seen = {kind: {"path": set(), "inode": set(), "sha256": set(), "timestamp": set()}
            for kind in ("rgb", "depth")}
    for block in blocks:
        frames = block.get("frames")
        require(isinstance(frames, list) and len(frames) == 24, "Expected 24 frames per block")
        require([f.get("frame") for f in frames] == list(range(24)) and
                all(type(f.get("frame")) is int for f in frames), "Expected ordered frame IDs 0..23")
        images, previous_timestamp = [], None
        for frame in frames:
            identity = {"block": block["block"], "split": block["split"], "frame": frame["frame"]}
            for kind in ("rgb", "depth"):
                record = frame.get(kind)
                require(isinstance(record, dict), f"Missing {kind} association")
                timestamp = record.get("timestamp")
                require(type(timestamp) in (int, float) and math.isfinite(timestamp),
                        f"Expected finite numeric {kind} timestamp")
                if kind == "rgb":
                    require(previous_timestamp is None or timestamp > previous_timestamp,
                            "RGB timestamps must be strictly increasing within every block")
                    previous_timestamp = timestamp
                target = safe_data_path(data, record.get("path"))
                expected = frame.get(kind + "_sha256")
                require(valid_sha(expected) and sha(target) == expected,
                        f"Input integrity mismatch: {record.get('path')}")
                stat = target.stat()
                values = {"path": str(target), "inode": (stat.st_dev, stat.st_ino),
                          "sha256": expected, "timestamp": timestamp}
                for field, value in values.items():
                    require(value not in seen[kind][field],
                            f"Duplicate {kind} {field} across the 72 inputs")
                    seen[kind][field].add(value)
                identity[kind] = {"path": str(target), "relative_path": record["path"],
                                  "timestamp": timestamp, "sha256": expected, "bytes": stat.st_size}
                if kind == "rgb":
                    images.append(target)
            identities.append(identity)
        prepared.append({"block": block["block"], "split": block["split"], "images": images})
    require(not seen["rgb"]["path"] & seen["depth"]["path"] and
            not seen["rgb"]["inode"] & seen["depth"]["inode"], "RGB and depth must be separate files")
    return prepared, identities


def expected_flags():
    # Importing the frozen runner has no torch import or inference side effects.
    from run_s6_cut3r import planned_view_flags
    return planned_view_flags(24, 20)


def verify_query_policy(raw):
    flags = expected_flags()
    for key in ("requested_view_flags", "prepared_view_flags", "view_flags_before_inference",
                "view_flags_after_inference"):
        require(raw.get(key) == flags, f"Saved view flags differ: {key}")
    require(raw.get("history_count") == 20 and raw.get("query_count") == 4 and
            raw.get("view_policy_preserved") is True and raw.get("history_only_memory_ok") is True,
            "History-only query policy did not pass")
    audit = raw.get("query_state_write_audit", {})
    for key, value in {"ok": True, "expected_snapshots": 25, "actual_snapshots": 25,
                       "anchor_snapshot_index": 20, "history_count": 20, "query_count": 4,
                       "fields": {"state_feat": 0, "pose_memory": 3}}.items():
        require(audit.get(key) == value, f"Query-state audit mismatch: {key}")
    checks = audit.get("checks", [])
    require(len(checks) == 8 and {(c["field"], c["snapshot_index"]) for c in checks} ==
            {(field, i) for field in ("state_feat", "pose_memory") for i in range(21, 25)},
            "Incomplete query-state check coverage")
    anchors = {}
    shapes = {"state_feat": [1, 768, 768], "pose_memory": [1, 256, 1536]}
    for check in checks:
        require(all(check.get(k) is True for k in ("exactly_unchanged", "finite", "anchor_finite",
                                                   "same_shape_and_dtype")) and
                check.get("max_absolute_difference") == 0 and
                check.get("after_view") == check["snapshot_index"] - 1 and
                check.get("shape") == check.get("anchor_shape") == shapes[check["field"]] and
                check.get("dtype") == check.get("anchor_dtype") == "torch.float32",
                "Query-state recorded values/schema changed")
        digest = check.get("anchor_tensor_sha256")
        require(valid_sha(digest) and check.get("tensor_sha256") == digest,
                "Query-state recorded tensor hashes differ")
        require(anchors.setdefault(check["field"], digest) == digest, "Query-state anchors differ")
    return audit


def verify_output_arrays(path, recorded):
    import numpy as np
    expected = {f"frame{i}_{key}": shape for i in range(24) for key, shape in ARRAY_SHAPES.items()}
    require(isinstance(recorded, dict) and set(recorded) == set(expected), "Output metadata keys differ")
    verified = {}
    with np.load(path, allow_pickle=False) as arrays:
        require(len(arrays.files) == 168 and set(arrays.files) == set(expected), "Expected exactly 168 arrays")
        for key, shape in expected.items():
            value = arrays[key]
            require(list(value.shape) == shape and value.dtype == np.dtype("float32"),
                    f"Actual output schema differs: {key}")
            require(bool(np.isfinite(value).all()), f"Nonfinite actual prediction: {key}")
            meta = recorded[key]
            require(meta.get("shape") == shape and meta.get("dtype") == "float32" and
                    meta.get("all_finite") is True and meta.get("finite_fraction") == 1.0 and
                    meta.get("min") == float(value.min()) and meta.get("max") == float(value.max()),
                    f"Saved output statistics differ from actual array: {key}")
            verified[key] = {"shape": shape, "dtype": "float32", "all_finite": True,
                             "tensor_sha256": hashlib.sha256(value.tobytes()).hexdigest()}
    return verified


def verify_completed_block(out, images, frozen):
    raw = read_json((out / "run_metadata.json").read_text())
    required = {"ok": True, "phase": "complete", "views": 24, "runner_sha256": RUNNER_SHA,
                "base_runner_sha256": BASE_RUNNER_SHA, "inference_ok": True,
                "all_outputs_finite": True, "required_outputs_present": True,
                "device": "cpu", "dtype": "float32", "seed": 0, "cpu_threads": 8,
                "commit": COMMIT, "tracked_changes": "", "actual_head_type": "linear",
                "actual_patch_image_size": [224, 224], "parameters": 748443655,
                "checkpoint_all_keys_matched": True, "resolution_model": "224_linear_intermediate",
                "upstream_source_files_unmodified": True, "upstream_execution_unmodified": False,
                "precision_semantics": PRECISION, "input_tensor_shapes": [[1, 3, 224, 224]] * 24,
                "vmem_complete_pipeline": False, "video_generated": False, "accuracy_evaluated": False}
    for key, expected in required.items():
        require(raw.get(key) == expected, f"Block metadata mismatch: {key}")
    require(raw.get("repo") == frozen["repo"] and raw.get("python_executable") == sys.executable,
            "Runner source/Python identity differs")
    require(sha(out / "runner_snapshot.py") == RUNNER_SHA, "Block runner snapshot hash mismatch")
    require(raw.get("images") == images, "Saved RGB input identity/order differs")
    checkpoint = raw.get("checkpoint", {})
    require(checkpoint == frozen["checkpoint"], "Loaded checkpoint identity differs")
    require(raw.get("checkpoint_serialization", {}).get("weights_only") is True,
            "Checkpoint was not loaded with weights-only deserialization")
    require(raw.get("model_config", {}).get("downstream_head_class") ==
            "dust3r.heads.linear_head.LinearPts3dPose", "Unexpected concrete model head")
    compat = raw.get("runtime_compatibility", {})
    require(compat.get("signed_rope_adapter") is True and compat.get("blocking_input_staging") is True
            and compat.get("adapter_sha256") == ADAPTER_SHA
            and compat.get("validation_sha256") == frozen["signed_rope_check_sha256"],
            "Runtime compatibility evidence differs")
    for name, value in raw.get("loaded_modules", {}).items():
        module = Path(value).resolve()
        require(module.is_relative_to(Path(frozen["repo"])), f"Loaded module outside pinned repo: {name}")
        rel = str(module.relative_to(frozen["repo"]))
        require(rel in frozen["upstream_python_sha256"] and
                sha(module) == frozen["upstream_python_sha256"][rel], f"Loaded source differs: {name}")
    require(set(raw.get("loaded_modules", {})) ==
            {"dust3r.model", "dust3r.inference", "dust3r.utils.image", "models.pos_embed"},
            "Loaded module evidence incomplete")
    staging = raw.get("input_device_staging", {})
    checks = staging.get("checks", [])
    fields = ("img", "ray_map", "camera_pose", "img_mask", "ray_mask", "update", "reset")
    require(staging.get("mode") == "blocking_before_official_inference" and
            staging.get("all_values_preserved") is True and len(checks) == 168 and
            {(c["view"], c["field"]) for c in checks} == {(i, k) for i in range(24) for k in fields}
            and all(c.get("values_preserved") is True for c in checks), "Input staging checks incomplete")
    require(type(raw.get("peak_process_rss_bytes")) is int and 0 < raw["peak_process_rss_bytes"] <= MAX_RSS_BYTES,
            "Completed process peak RSS exceeds budget or lacks a positive measurement")
    audit = verify_query_policy(raw)
    require(sha(out / "predictions.npz") == raw.get("predictions_sha256"), "Saved prediction hash mismatch")
    arrays = verify_output_arrays(out / "predictions.npz", raw.get("outputs"))
    verification = {"ok": True, "verified_utc": now(), "arrays_verified": len(arrays), "arrays": arrays,
                    "input_identity_verified": True, "query_state_write_audit": audit,
                    "state_audit_scope": "Validate frozen runner's in-process records and tensor hashes; state tensors are not archived",
                    "metadata_sha256": sha(out / "run_metadata.json"), "runner_sha256": RUNNER_SHA,
                    "predictions_sha256": raw["predictions_sha256"]}
    write_json(out / "s8_output_verification.json", verification)
    return raw, verification


def git_output(repo, *args):
    git = "/usr/bin/git" if sys.platform == "darwin" else "git"
    return subprocess.check_output([git, "-C", str(repo), *args], text=True).strip()


def verify_source(repo):
    require(git_output(repo, "rev-parse", "HEAD") == COMMIT, "Official source commit differs")
    require(not git_output(repo, "status", "--porcelain", "--untracked-files=no"), "Official tracked source changed")
    tracked = set(git_output(repo, "ls-files", "-z").split("\0"))
    source_files = sorted((repo / "src").rglob("*.py"))
    require(source_files, "Pinned source tree is empty")
    for source in source_files:
        require(source.is_file() and not source.is_symlink() and str(source.relative_to(repo)) in tracked,
                f"Untracked or symbolic Python source could shadow pinned code: {source}")
    return {str(source.relative_to(repo)): sha(source) for source in source_files}


def source_snapshot(output, repo):
    snapshot = output / "source_snapshot"
    snapshot.mkdir()
    paths = {"run_s8_sequence.py": Path(__file__).resolve(),
             "run_s6_cut3r.py": ROOT / "scripts/run_s6_cut3r.py",
             "run_cut3r_local.py": ROOT / "scripts/run_cut3r_local.py",
             "cut3r_rope_compat.py": ROOT / "scripts/cut3r_rope_compat.py"}
    records = {}
    for name, path in paths.items():
        shutil.copy2(path, snapshot / name)
        records[name] = {"source_path": str(path), "sha256": sha(snapshot / name)}
    archive = snapshot / "upstream_source.tar"
    git = "/usr/bin/git" if sys.platform == "darwin" else "git"
    with archive.open("xb") as stream:
        subprocess.run([git, "-C", str(repo), "archive", "--format=tar", COMMIT], stdout=stream, check=True)
    records[archive.name] = {"commit": COMMIT, "sha256": sha(archive), "bytes": archive.stat().st_size}
    write_json(snapshot / "manifest.json", records)
    return records


def stop_process(process):
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            process.wait()
            return
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()


def run_monitored(command, log_path, entry, save):
    process = None
    started = time.monotonic()
    samples = []
    try:
        with log_path.open("x") as log:
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            entry["pid"] = process.pid
            save()
            peak = 0
            while process.poll() is None:
                result = subprocess.run(["ps", "-o", "rss=", "-p", str(process.pid)],
                                        capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and result.stdout.strip():
                    rss = int(result.stdout.strip()) * 1024
                    peak = max(peak, rss)
                    samples.append({"elapsed_seconds": time.monotonic() - started, "rss_bytes": rss})
                elif process.poll() is None:
                    entry["stop_reason"] = "rss_monitor_failed"
                    break
                if peak > MAX_RSS_BYTES:
                    entry["stop_reason"] = "observed_rss_budget_exceeded"
                    break
                if time.monotonic() - started > TIMEOUT_SECONDS:
                    entry["stop_reason"] = "timeout"
                    break
                time.sleep(0.5)
            stop_process(process)
            entry.update(returncode=process.returncode, observed_peak_rss_bytes=peak,
                         monitored_seconds=time.monotonic() - started, completed_utc=now())
            require(not entry.get("stop_reason") and process.returncode == 0,
                    "Block failed; all outputs/logs retained and remaining blocks stopped")
    finally:
        if process is not None:
            stop_process(process)
            entry.setdefault("returncode", process.returncode)
        write_json(log_path.with_suffix(".rss.json"), {"samples": samples, "sample_interval_seconds": 0.5})
        save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("manifest", "protocol", "repo", "data", "checkpoint", "signed-rope-check", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args()
    # Refuse existing paths, including broken symlinks. Creation is exclusive.
    if args.output.exists() or args.output.is_symlink():
        parser.error("Choose a new output directory; previous attempts are preserved")
    args.output.mkdir(parents=True, exist_ok=False)
    output = args.output.resolve()
    shutil.copy2(__file__, output / "sequence_runner_snapshot.py")
    report = {"schema": "s8-sequence-metadata-v1", "stage": "S8", "started_utc": now(),
              "ok": False, "phase": "preflight", "blocks": [], "sequence_runner_sha256": sha(__file__),
              "runner_sha256": RUNNER_SHA, "base_runner_sha256": BASE_RUNNER_SHA,
              "evidence_level": "independent_pretrained_geometry_inference",
              "vmem_complete_pipeline": False, "video_generated": False, "accuracy_evaluated": False,
              "precision_semantics": PRECISION, "python_executable": sys.executable, "python": sys.version,
              "resource_policy": {"timeout_seconds_per_block": TIMEOUT_SECONDS,
                                  "observed_rss_limit_bytes": MAX_RSS_BYTES,
                                  "rss_sample_interval_seconds": 0.5,
                                  "limit_kind": "sampled process RSS soft budget, checked against final process peak",
                                  "rss_scope": "single model process; descendants are terminated with its process group"},
              "view_policy": {"reset": False, "update": [True] * 20 + [False] * 4,
                              "img_mask": True, "ray_mask": False, "history_count": 20, "query_count": 4,
                              "new_process_per_block": True, "depth_sent_to_model": False},
              "s5_history_comparison_performed": False, "depth_files_decoded_by_controller": False}

    def save():
        write_json(output / "sequence_metadata.json", report)

    def event(name, **extra):
        value = {"utc": now(), "event": name, **extra}
        with (output / "events.jsonl").open("a") as stream:
            stream.write(json.dumps(value, ensure_ascii=False, allow_nan=False) + "\n")
        print(json.dumps(value, ensure_ascii=False, allow_nan=False), flush=True)

    def interrupted(signum, _frame):
        raise InterruptedError(f"Controller received signal {signum}; stopping its model process group")

    signal.signal(signal.SIGTERM, interrupted)
    save()
    try:
        # Read once, bind the parsed content and archived bytes to identical hashes.
        manifest_bytes, protocol_bytes = args.manifest.read_bytes(), args.protocol.read_bytes()
        manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
        protocol_sha = hashlib.sha256(protocol_bytes).hexdigest()
        (output / "frozen_inputs.json").write_bytes(manifest_bytes)
        (output / "frozen_protocol.md").write_bytes(protocol_bytes)
        report.update(manifest_sha256=manifest_sha, protocol_sha256=protocol_sha,
                      manifest_path=str(args.manifest.resolve()), protocol_path=str(args.protocol.resolve()),
                      frozen_utc=now(), data_path=str(args.data.resolve()))
        save()
        protocol = parse_protocol(protocol_bytes.decode("utf-8"))
        manifest = read_json(manifest_bytes.decode("utf-8"))
        require(sha(ROOT / "scripts/run_s6_cut3r.py") == RUNNER_SHA, "Frozen S6 runner changed")
        require(sha(ROOT / "scripts/run_cut3r_local.py") == BASE_RUNNER_SHA, "Frozen base runner changed")
        require(sha(ROOT / "scripts/cut3r_rope_compat.py") == ADAPTER_SHA, "Signed RoPE adapter changed")
        blocks, identities = validate_manifest(manifest, args.data, protocol_sha, protocol)
        repo = args.repo.resolve(strict=True)
        upstream_sources = verify_source(repo)
        checkpoint = args.checkpoint.resolve(strict=True)
        require(checkpoint.is_file() and checkpoint.stat().st_size == CHECKPOINT_BYTES and
                sha(checkpoint) == CHECKPOINT_SHA, "Original verified checkpoint identity differs")
        download_path = checkpoint.parent / "download_manifest.json"
        download = read_json(download_path.read_text())
        require(download.get("status") == "verified_download" and download.get("sha256") == CHECKPOINT_SHA
                and download.get("actual_size") == CHECKPOINT_BYTES, "Checkpoint download manifest is not verified")
        rope_path = args.signed_rope_check.resolve(strict=True)
        rope_bytes = rope_path.read_bytes()
        rope = read_json(rope_bytes.decode("utf-8"))
        require(rope.get("ok") is True and rope.get("adapter_sha256") == ADAPTER_SHA and
                rope.get("commit") == COMMIT, "Signed RoPE compatibility check failed or differs")
        (output / "signed_rope_check.json").write_bytes(rope_bytes)
        shutil.copy2(download_path, output / "checkpoint_download_manifest.json")
        frozen = {"repo": str(repo), "checkpoint": {"path": str(checkpoint), "bytes": CHECKPOINT_BYTES,
                                                     "sha256": CHECKPOINT_SHA},
                  "signed_rope_check_sha256": hashlib.sha256(rope_bytes).hexdigest(),
                  "upstream_python_sha256": upstream_sources}
        report.update(frozen, commit=COMMIT, checkpoint_sha256=CHECKPOINT_SHA, dataset=manifest.get("dataset"),
                      protocol_contract=protocol, expected_view_flags=expected_flags(),
                      source_snapshot=source_snapshot(output, repo), input_identities=identities,
                      preflight_completed_utc=now())
        # Originals, data and source must retain these identities through the run.
        fixed_paths = [(args.manifest, manifest_sha), (args.protocol, protocol_sha),
                       (Path(__file__), report["sequence_runner_sha256"]),
                       (ROOT / "scripts/run_s6_cut3r.py", RUNNER_SHA),
                       (ROOT / "scripts/run_cut3r_local.py", BASE_RUNNER_SHA),
                       (ROOT / "scripts/cut3r_rope_compat.py", ADAPTER_SHA),
                       (rope_path, frozen["signed_rope_check_sha256"]),
                       (download_path, sha(output / "checkpoint_download_manifest.json"))]

        def recheck():
            for path, digest in fixed_paths:
                require(sha(path) == digest, f"Frozen file changed after preflight: {path}")
            for record in identities:
                for kind in ("rgb", "depth"):
                    identity = record[kind]
                    require(sha(identity["path"]) == identity["sha256"], "Input changed after preflight")
            require(verify_source(repo) == upstream_sources, "Upstream source changed after preflight")

        recheck()
        save()
        event("preflight_verified", rgb_images=72, depth_files_integrity_checked=72,
              manifest_sha256=manifest_sha, protocol_sha256=protocol_sha)
        for block in blocks:
            recheck()
            bid, images = block["block"], block["images"]
            out = output / f"block{bid}"
            command = [sys.executable, str(ROOT / "scripts/run_s6_cut3r.py"), "--repo", str(repo),
                       "--checkpoint", str(checkpoint), "--images", *map(str, images),
                       "--device", "cpu", "--threads", "8", "--history-count", "20", "--output", str(out),
                       "--input-source", f"S8 block{bid}; RGB only; history20/query4; manifest {manifest_sha}",
                       "--signed-rope-check", str(rope_path)]
            entry = {"block": bid, "split": block["split"], "started_utc": now(), "output": f"block{bid}",
                     "log": f"block{bid}.log", "command": command, "ok": False}
            report["blocks"].append(entry)
            report["phase"] = f"block{bid}"
            save()
            event("block_starting", block=bid)
            run_monitored(command, output / f"block{bid}.log", entry, save)
            expected_images = [{"path": identity["rgb"]["path"], "sha256": identity["rgb"]["sha256"]}
                               for identity in identities if identity["block"] == bid]
            raw, verified = verify_completed_block(out, expected_images, frozen)
            recheck()
            entry.update(ok=True, arrays_verified=verified["arrays_verified"],
                         history_only_memory_ok=True, inference_seconds=raw["inference_seconds"],
                         predictions_sha256=raw["predictions_sha256"], model_completed_utc=raw["completed_utc"],
                         process_peak_rss_bytes=raw["peak_process_rss_bytes"],
                         verification_sha256=sha(out / "s8_output_verification.json"),
                         metadata_sha256=verified["metadata_sha256"])
            save()
            event("block_verified", block=bid, arrays=verified["arrays_verified"])
        require(sum(b["arrays_verified"] for b in report["blocks"]) == 504, "Expected 504 verified arrays")
        require(sha(checkpoint) == CHECKPOINT_SHA, "Checkpoint changed during sequence")
        report.update(ok=True, phase="complete", arrays_verified=504, completed_utc=now())
        save()
        event("complete", blocks=3, images=72, finite_arrays=504)
        return 0
    except BaseException:
        report.update(ok=False, phase="failed", completed_utc=now(), error=traceback.format_exc())
        save()
        event("failed", error=report["error"])
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
