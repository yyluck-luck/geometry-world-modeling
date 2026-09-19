#!/usr/bin/env python3
"""Independent source/contract and in-memory tests for the S45B candidate.

This script must not open C1 manifests, receipts, archives, result tensors,
images, or formal attempt paths.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import tempfile


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "camera_guard.py"
PROTOCOL = HERE / "PROTOCOL.md"
TEMPLATE = HERE / "C1_CAMERA_GUARD_BINDING_TEMPLATE.json"
FORMAL = HERE / "execution_01"
BINDING = HERE / "C1_CAMERA_GUARD_BINDING.json"
LOCK = HERE / ".c1_numeric_camera_guard.lock"
LOCK_STAGING = HERE / ".c1_numeric_camera_guard.lock.staging"
B0 = HERE.parents[1] / "work/S42_baseline_failure_preregistration/score_b0_blind.py"


def require(value, message):
    if not value:
        raise AssertionError(message)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def function_source_sha(source_bytes, tree, name):
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    require(len(nodes) == 1, "missing/duplicate function: " + name)
    node = nodes[0]
    lines = source_bytes.splitlines(keepends=True)
    require(type(node.lineno) is int and type(node.end_lineno) is int
            and 1 <= node.lineno <= node.end_lineno <= len(lines),
            "function source bounds differ: " + name)
    return hashlib.sha256(b"".join(lines[node.lineno - 1:node.end_lineno])).hexdigest()


def independent_expected_pose(base, yaw_degrees):
    angle = yaw_degrees * math.pi / 180.0
    rotation = (
        (math.cos(angle), 0.0, math.sin(angle)),
        (0.0, 1.0, 0.0),
        (-math.sin(angle), 0.0, math.cos(angle)),
    )
    expected = [[0.0] * 4 for _ in range(4)]
    for i in range(3):
        for j in range(3):
            expected[i][j] = sum(rotation[i][k] * base[k][j] for k in range(3))
        expected[i][3] = base[i][3]
    expected[3] = [0.0, 0.0, 0.0, 1.0]
    return expected


def main():
    require(not os.path.lexists(FORMAL), "formal attempt path exists")
    require(not os.path.lexists(BINDING), "executable binding unexpectedly exists")
    require(not os.path.lexists(LOCK) and not os.path.lexists(LOCK_STAGING),
            "formal attempt lease or staging path exists")
    source_text = SOURCE.read_text()
    source_tree = ast.parse(source_text, filename=str(SOURCE))
    compile(source_tree, str(SOURCE), "exec")
    imports = set()
    for node in ast.walk(source_tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    require(not imports.intersection({"numpy", "torch", "PIL", "cv2", "diffusers"}),
            "scientific/image/model import found")

    b0_source = B0.read_bytes()
    b0_tree = ast.parse(b0_source.decode("utf-8"), filename=str(B0))
    require(sha256(B0) == "f36be25001f5138bd985ca186d49c6d44e66b5b9c599b8c0dfc6e8691a4719de",
            "reviewed B0 source changed")
    require(function_source_sha(b0_source, b0_tree, "max_abs")
            == "5b19516bcaa6d650b7259d4e806266ab40762a358989190f2d3327fbaceb3fd4",
            "B0 max_abs source segment changed")
    require(function_source_sha(b0_source, b0_tree, "verify_requested_camera_conditions")
            == "7dfa29e4bdaca569cf485b8c575f1d48f5dbcabb61011f6ab1998fea79b9a8e3",
            "B0 camera source segment changed")

    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("_s45b_camera_guard_synthetic", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(module.PROTOCOL_SHA256 == sha256(PROTOCOL),
            "runner does not bind the exact protocol")
    require(module.BINDING_TEMPLATE_SHA256 == sha256(TEMPLATE),
            "runner does not bind the exact unbound template")
    require(module.SELFTEST_SHA256 == sha256(Path(__file__).resolve()),
            "runner does not bind the exact independent synthetic self-test")
    require(module.B0_MAX_ABS_SOURCE_SHA256
            == "5b19516bcaa6d650b7259d4e806266ab40762a358989190f2d3327fbaceb3fd4"
            and module.B0_CAMERA_SOURCE_SHA256
            == "7dfa29e4bdaca569cf485b8c575f1d48f5dbcabb61011f6ab1998fea79b9a8e3",
            "runner does not bind the version-independent B0 function source segments")
    built_in = module.synthetic_selftest()
    require(built_in["status"] == "PASS_SYNTHETIC_ONLY", "built-in selftest failed")

    base = [
        [0.0, -1.0, 0.0, 1.0],
        [1.0, 0.0, 0.0, -2.0],
        [0.0, 0.0, 1.0, 3.0],
        [0.0, 0.0, 0.0, 1.0],
    ]
    max_reference_error = 0.0
    for yaw in module.EXPECTED_YAW:
        candidate = module.expected_pose(base, yaw)
        reference = independent_expected_pose(base, yaw)
        max_reference_error = max(max_reference_error, module.matrix_max_abs(candidate, reference))
    require(max_reference_error <= 1e-15, "candidate differs from independently transcribed B0 convention")

    main_node = [
        node for node in source_tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "main"
    ][0]
    preflight_lines = [
        node.lineno for node in ast.walk(main_node)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        and node.func.id == "formal_preflight"
    ]
    commit_lines = [
        node.lineno for node in ast.walk(main_node)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        and node.func.id == "commit_attempt_lease"
    ]
    require(len(preflight_lines) == len(commit_lines) == 1
            and preflight_lines[0] < commit_lines[0],
            "permanent attempt lease is not committed strictly after harmless preflight")
    committed_node = [
        node for node in source_tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "committed_formal_run"
    ][0]
    lock_revalidation_lines = [
        node.lineno for node in ast.walk(committed_node)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        and node.func.id == "verify_lock_lease"
    ]
    require(len(lock_revalidation_lines) >= 8,
            "committed run does not revalidate the permanent lock at every trust boundary")
    lock_verify_node = [
        node for node in source_tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "verify_lock_lease"
    ][0]
    lock_verify_text = ast.get_source_segment(source_text, lock_verify_node)
    require(all(token in lock_verify_text for token in (
        "os.fstat", "os.stat", "st_nlink", "inode_identity", "stat.S_ISREG",
        "hashlib.sha256", "os.pread",
    )), "lock verifier omits a frozen pathname/inode/content property")

    with tempfile.TemporaryDirectory(prefix="s45b_camera_guard_synthetic_") as raw_tmp:
        temp_root = Path(raw_tmp).resolve()
        parent_flags = (
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        )
        parent_fd = os.open(temp_root, parent_flags)
        lease_fd = None
        try:
            parent_stat = os.fstat(parent_fd)
            parent_identity = module.inode_identity(parent_stat)
            module.verify_directory_lease(parent_fd, temp_root, parent_identity)
            module.fcntl.flock(parent_fd, module.fcntl.LOCK_EX | module.fcntl.LOCK_NB)
            try:
                module.require(False, "synthetic harmless preflight rejection")
            except ValueError:
                pass
            else:
                raise AssertionError("synthetic preflight rejection did not reject")
            require(module.entry_absent(parent_fd, "attempt.lock")
                    and module.entry_absent(parent_fd, "attempt.lock.staging"),
                    "preflight rejection consumed a synthetic attempt lease")

            lease_record = {
                "schema": "synthetic-attempt-lease-v1",
                "status": "FAIL_CLOSED_ATTEMPT_COMMITTED_NO_VALID_TERMINAL_RECEIPT",
                "passed": False,
                "attempt_consumed": True,
                "c1_tensor_bodies_read": 0,
                "pixels_decoded": 0,
            }
            lease_fd, lease_identity, lease_sha256, lease_bytes = module.commit_attempt_lease(
                parent_fd, temp_root, parent_identity,
                "attempt.lock", "attempt.lock.staging", lease_record,
            )
            module.verify_lock_lease(
                parent_fd, temp_root, parent_identity, lease_fd, "attempt.lock",
                lease_identity, lease_sha256, lease_bytes,
            )
            committed_doc = json.loads(os.pread(lease_fd, lease_bytes, 0).decode("utf-8"))
            require(committed_doc == lease_record
                    and module.entry_absent(parent_fd, "attempt.lock.staging"),
                    "atomic lease does not expose exactly one parseable fail-closed receipt")

            try:
                module.commit_attempt_lease(
                    parent_fd, temp_root, parent_identity,
                    "attempt.lock", "attempt.lock.staging", lease_record,
                )
            except ValueError:
                pass
            else:
                raise AssertionError("a second synthetic attempt lease was accepted")

            os.unlink("attempt.lock", dir_fd=parent_fd)
            replacement_flags = (
                os.O_WRONLY | os.O_CREAT | os.O_EXCL
                | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
            )
            replacement_fd = os.open("attempt.lock", replacement_flags, 0o600, dir_fd=parent_fd)
            try:
                os.write(replacement_fd, b"{}\n")
                os.fsync(replacement_fd)
            finally:
                os.close(replacement_fd)
            try:
                module.verify_lock_lease(
                    parent_fd, temp_root, parent_identity, lease_fd, "attempt.lock",
                    lease_identity, lease_sha256, lease_bytes,
                )
            except ValueError:
                pass
            else:
                raise AssertionError("lock pathname unlink/recreate was not detected")
        finally:
            if lease_fd is not None:
                os.close(lease_fd)
            os.close(parent_fd)

    raw = {
        "kind": "tensor", "blob": "tensors/" + "a" * 64 + ".bin",
        "byteorder": "little", "bytes_sha256": "b" * 64,
        "dtype": "float32", "nbytes": 64, "order": "C",
        "sha256": "a" * 64, "shape": [4, 4],
    }
    listed = module.raw_tensor_list({"kind": "list", "items": [raw]}, "list")
    tupled = module.raw_tensor_list({"kind": "tuple", "items": [raw]}, "tuple")
    require(type(listed) is list and type(tupled) is tuple,
            "list/tuple provenance was collapsed")
    try:
        module.raw_tensor({"kind": "dict", "items": []}, "ordinary dict")
    except ValueError:
        pass
    else:
        raise AssertionError("descriptor-shaped ordinary dict could enter tensor path")

    def scalar(value):
        return {"kind": "scalar", "type": "str", "value": value}

    def raw_dict(mapping):
        return {
            "kind": "dict",
            "items": [
                {"key": scalar(key), "value": value}
                for key, value in mapping.items()
            ],
        }

    forbidden_pixels = {
        "kind": "pil_image",
        "pixels": {"kind": "forbidden_pixel_body_must_not_be_traversed"},
    }
    selected_batch = module.select_camera_capture("batch_input", raw_dict({
        "target_c2ws": raw,
        "target_Ks": raw,
        "unselected_image": forbidden_pixels,
    }))
    selected_cache = module.select_camera_capture("cache_commit", raw_dict({
        "cache": raw_dict({
            "c2ws": {"kind": "list", "items": [raw] * 5},
            "Ks": {"kind": "tuple", "items": [raw] * 5},
            "pil_frames": {"kind": "list", "items": [forbidden_pixels]},
        }),
    }))
    require(set(selected_batch) == {"target_c2ws", "target_Ks"}
            and set(selected_cache) == {"c2ws", "Ks"}
            and len(selected_cache["c2ws"]) == len(selected_cache["Ks"]) == 5,
            "selective camera decoder traversed or retained a non-camera field")

    pixel_shape = dict(raw)
    pixel_shape.update(shape=[576, 576, 3], nbytes=576 * 576 * 3 * 4)
    marker = module.TensorDescriptor(pixel_shape)
    store = module.CameraTensorStore(
        {"tensor_descriptors": {pixel_shape["blob"]: pixel_shape}, "files": {}},
        Path("/synthetic/nonexistent/archive"), float("inf"),
    )
    store._snapshot = lambda *args, **kwargs: (_ for _ in ()).throw(
        AssertionError("pixel-shaped tensor reached a body-open path")
    )
    try:
        store.decode(marker, lambda shape: shape == [4, 4], "pixel masquerade")
    except ValueError:
        pass
    else:
        raise AssertionError("pixel-shaped tensor was accepted")

    template = json.loads(TEMPLATE.read_text())
    require(template["schema"] == "s45b-c1-numeric-camera-guard-binding-template-v1"
            and template["status"] == "UNBOUND_TEMPLATE_NOT_EXECUTABLE"
            and template["placeholder_hashes"] == 14,
            "binding template is not explicitly unbound")
    require(template["upstream"]["s45_result_review"]["sha256"]
            == module.S45_RESULT_REVIEW_SHA256,
            "reported S45 result-review identity differs")
    null_upstream = [name for name, item in template["upstream"].items() if item["sha256"] is None]
    null_source = [name for name, value in template["source_set"].items() if value is None]
    require(len(null_upstream) + len(null_source) == template["placeholder_hashes"],
            "template null hash count differs")

    output = {
        "schema": "s45b-c1-numeric-camera-guard-independent-synthetic-test-v1",
        "status": "PASS_STATIC_AND_SYNTHETIC_ONLY",
        "identities": {
            "camera_guard.py": sha256(SOURCE),
            "PROTOCOL.md": sha256(PROTOCOL),
            "C1_CAMERA_GUARD_BINDING_TEMPLATE.json": sha256(TEMPLATE),
            "reviewed_b0_reference": sha256(B0),
        },
        "checks": {
            "python_ast_compile": "PASS",
            "runner_protocol_and_template_self_binding": "PASS",
            "preflight_precedes_permanent_lease_static_order": "PASS",
            "lock_revalidated_at_all_committed_trust_boundaries": "PASS",
            "lock_verifier_covers_fd_path_inode_nlink_type_size_and_sha": "PASS",
            "atomic_structured_fail_closed_attempt_lease": "PASS",
            "directory_wide_cooperating_runner_serialization": "PASS",
            "duplicate_attempt_lease_rejection": "PASS",
            "lock_path_unlink_recreate_detection": "PASS",
            "no_scientific_image_or_model_import": "PASS",
            "reviewed_b0_function_source_identity_cross_version": "PASS",
            "independent_left_multiply_sign_crosscheck": "PASS",
            "max_reference_error": max_reference_error,
            "positive_and_negative_numeric_cases": "PASS",
            "inclusive_tolerance": "PASS",
            "raw_tensor_and_list_tuple_provenance": "PASS",
            "selective_decoder_ignores_pil_pixel_subtree": "PASS",
            "pixel_shape_rejected_before_body_open": "PASS",
            "unbound_template_and_null_count": "PASS",
        },
        "unbound_upstream_identities": null_upstream,
        "unbound_source_identities": null_source,
        "c1_files_opened": 0,
        "c1_tensor_bodies_read": 0,
        "real_scientific_arrays_mapped": 0,
        "pixels_decoded": 0,
        "images_viewed": 0,
        "formal_paths_created": 0,
    }
    require(not os.path.lexists(FORMAL) and not os.path.lexists(LOCK)
            and not os.path.lexists(LOCK_STAGING),
            "synthetic lease tests touched a formal path")
    print(json.dumps(output, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
