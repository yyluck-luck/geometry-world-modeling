#!/usr/bin/env python3
"""Independent source, contract, math, and fault tests for S45B v5.

This script opens only candidate/reference source text and creates synthetic
state in isolated temporary directories.  It must never open any real C1
manifest, receipt, event, tensor, image, pixel body, binding, lock, or formal
execution directory.
"""
from __future__ import annotations

import ast
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import sys
import tempfile
import types


HERE = Path(__file__).resolve().parent
WORKER = HERE / "camera_guard.py"
SUPERVISOR = HERE / "supervise_camera_guard.py"
PROTOCOL = HERE / "PROTOCOL.md"
TEMPLATE = HERE / "C1_CAMERA_GUARD_BINDING_TEMPLATE.json"
B0 = HERE.parents[1] / "work/S42_baseline_failure_preregistration/score_b0_blind.py"
HISTORY = HERE.parent / "S45B_c1_numeric_camera_guard_preparation/history_v4_adversarial_blocked_285f9b64"

FORMAL_PATHS = (
    HERE / "execution_01",
    HERE / ".c1_numeric_camera_guard.lock",
    HERE / ".c1_numeric_camera_guard.lock.staging",
    HERE / "C1_CAMERA_GUARD_BINDING_V5.json",
    HERE / "BINDING_REVIEW_V5.json",
    HERE / "SOURCE_REVIEW_PRIMARY_V5.json",
    HERE / "SOURCE_REVIEW_ADVERSARIAL_V5.json",
)

EXPECTED_V4_HISTORY = {
    "camera_guard.py": "285f9b64f6ad53f14c21f725ff1884b632ef7766d63bf6e43af780b716160bb4",
    "PROTOCOL.md": "514fb18d5b2446ac50393fbe6c5fda34dd7b771356c037ff789e20710f49abcb",
    "C1_CAMERA_GUARD_BINDING_TEMPLATE.json": "a2d8aa4e686523db15044f28c1d7f39e1ff50f73f4485b303bd7b31247b2dc1a",
    "synthetic_selftest.py": "2d3674998103073fc3e884b3432f7d385bf432d4bfc7b8d51c4477ebaefc81aa",
    "SOURCE_REVIEW_PRIMARY.json": "c97faa0def6c027c762ede46e72c955d02787e320f1fc0c82300eabe294adf23",
    "SOURCE_REVIEW_ADVERSARIAL.json": "006a89e504c4f5ef8ff88c529a0e8486ddc626b2f521dbb7c8ee4ea0996c13dd",
}


def require(value, message):
    if not value:
        raise AssertionError(message)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_exact_source(path, module_name):
    raw = Path(path).read_bytes()
    text = raw.decode("utf-8")
    tree = ast.parse(text, filename=str(path))
    compile(tree, str(path), "exec")
    module = types.ModuleType(module_name)
    module.__file__ = str(Path(path).resolve())
    exec(compile(text, str(path), "exec"), module.__dict__)
    return raw, text, tree, module


def function_source_sha(source_bytes, tree, name):
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    require(len(nodes) == 1, "missing or duplicate function: " + name)
    node = nodes[0]
    lines = source_bytes.splitlines(keepends=True)
    require(type(node.lineno) is int and type(node.end_lineno) is int
            and 1 <= node.lineno <= node.end_lineno <= len(lines),
            "function source bounds differ: " + name)
    return hashlib.sha256(b"".join(lines[node.lineno - 1:node.end_lineno])).hexdigest()


def imported_roots(tree):
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def enclosing_functions(tree):
    parents = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent

    def owner(node):
        current = node
        while current in parents:
            current = parents[current]
            if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return current.name
        return None
    return owner


def true_publication_owners(tree, key_name):
    owner = enclosing_functions(tree)
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if (isinstance(key, ast.Constant) and key.value == key_name
                        and isinstance(value, ast.Constant) and value.value is True):
                    found.append(owner(node))
        if isinstance(node, ast.keyword) and node.arg == key_name:
            if isinstance(node.value, ast.Constant) and node.value.value is True:
                found.append(owner(node))
    return found


def call_lines(function_node, predicate):
    return sorted(
        node.lineno for node in ast.walk(function_node)
        if isinstance(node, ast.Call) and predicate(node.func)
    )


def named_function(tree, name):
    found = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    require(len(found) == 1, "missing or duplicate function: " + name)
    return found[0]


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


def assert_formal_paths_absent():
    present = [str(path) for path in FORMAL_PATHS if os.path.lexists(path)]
    require(not present, "formal path unexpectedly exists: " + repr(present))


def synthetic_lock_tests(worker):
    checks = {}
    with tempfile.TemporaryDirectory(prefix="s45b_v5_lock_") as raw:
        root = Path(raw).resolve()
        flags = (os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
                 | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0))
        parent_fd = os.open(root, flags)
        lock_fd = None
        try:
            identity = worker.inode_identity(os.fstat(parent_fd))
            worker.verify_directory_lease(parent_fd, root, identity)
            lease = {
                "schema": "synthetic-v5-attempt-lock",
                "status": "FAIL_CLOSED_ATTEMPT_COMMITTED_NO_VALID_TERMINAL_SEAL",
                "passed": False,
            }
            lock_fd, lock_identity, lock_sha, lock_bytes = worker.commit_attempt_lease(
                parent_fd, root, identity, "attempt.lock", "attempt.lock.staging", lease,
            )
            worker.verify_lock_lease(
                parent_fd, root, identity, lock_fd, "attempt.lock",
                lock_identity, lock_sha, lock_bytes,
            )
            committed = json.loads(os.pread(lock_fd, lock_bytes, 0).decode("utf-8"))
            require(committed == lease and worker.entry_absent(parent_fd, "attempt.lock.staging"),
                    "attempt commit is not one exact structured failure receipt")
            try:
                worker.commit_attempt_lease(
                    parent_fd, root, identity, "attempt.lock", "attempt.lock.staging", lease,
                )
            except ValueError:
                checks["duplicate_attempt"] = "PASS_REJECTED"
            else:
                raise AssertionError("duplicate attempt was accepted")

            os.link("attempt.lock", "attempt.alias", src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
            try:
                worker.verify_lock_lease(
                    parent_fd, root, identity, lock_fd, "attempt.lock",
                    lock_identity, lock_sha, lock_bytes,
                )
            except ValueError:
                checks["lock_hardlink"] = "PASS_REJECTED"
            else:
                raise AssertionError("lock hardlink was accepted")
            os.unlink("attempt.alias", dir_fd=parent_fd)

            os.unlink("attempt.lock", dir_fd=parent_fd)
            replacement_fd = os.open(
                "attempt.lock",
                os.O_WRONLY | os.O_CREAT | os.O_EXCL
                | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
                0o600, dir_fd=parent_fd,
            )
            try:
                os.write(replacement_fd, b"{}\n")
                os.fsync(replacement_fd)
            finally:
                os.close(replacement_fd)
            try:
                worker.verify_lock_lease(
                    parent_fd, root, identity, lock_fd, "attempt.lock",
                    lock_identity, lock_sha, lock_bytes,
                )
            except ValueError:
                checks["lock_unlink_recreate"] = "PASS_REJECTED"
            else:
                raise AssertionError("lock unlink/recreate was accepted")
        finally:
            if lock_fd is not None:
                os.close(lock_fd)
            os.close(parent_fd)

    with tempfile.TemporaryDirectory(prefix="s45b_v5_lock_symlink_") as raw:
        root = Path(raw).resolve()
        flags = (os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
                 | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0))
        parent_fd = os.open(root, flags)
        try:
            identity = worker.inode_identity(os.fstat(parent_fd))
            os.symlink("missing-target", "attempt.lock", dir_fd=parent_fd)
            try:
                worker.commit_attempt_lease(
                    parent_fd, root, identity, "attempt.lock", "attempt.lock.staging",
                    {"schema": "synthetic", "passed": False},
                )
            except ValueError:
                checks["preexisting_lock_symlink"] = "PASS_REJECTED"
            else:
                raise AssertionError("preexisting lock symlink was accepted")
        finally:
            os.close(parent_fd)
    return checks


def selective_decoder_tests(worker):
    raw = {
        "kind": "tensor", "blob": "tensors/" + "a" * 64 + ".bin",
        "byteorder": "little", "bytes_sha256": "b" * 64,
        "dtype": "float32", "nbytes": 64, "order": "C",
        "sha256": "a" * 64, "shape": [4, 4],
    }
    listed = worker.raw_tensor_list({"kind": "list", "items": [raw]}, "list")
    tupled = worker.raw_tensor_list({"kind": "tuple", "items": [raw]}, "tuple")
    require(type(listed) is list and type(tupled) is tuple,
            "list/tuple provenance was collapsed")
    try:
        worker.raw_tensor({"kind": "dict", "items": []}, "ordinary dict")
    except ValueError:
        pass
    else:
        raise AssertionError("ordinary dictionary entered the tensor path")

    def scalar(value):
        return {"kind": "scalar", "type": "str", "value": value}

    def raw_dict(mapping):
        return {"kind": "dict", "items": [
            {"key": scalar(key), "value": value} for key, value in mapping.items()
        ]}

    forbidden = {"kind": "pil_image", "pixels": {"kind": "must_not_be_traversed"}}
    batch = worker.select_camera_capture("batch_input", raw_dict({
        "target_c2ws": raw, "target_Ks": raw, "unselected_image": forbidden,
    }))
    cache = worker.select_camera_capture("cache_commit", raw_dict({
        "cache": raw_dict({
            "c2ws": {"kind": "list", "items": [raw] * 5},
            "Ks": {"kind": "tuple", "items": [raw] * 5},
            "pil_frames": {"kind": "list", "items": [forbidden]},
        }),
    }))
    require(set(batch) == {"target_c2ws", "target_Ks"}
            and set(cache) == {"c2ws", "Ks"}
            and len(cache["c2ws"]) == len(cache["Ks"]) == 5,
            "camera selector retained or traversed a pixel field")

    pixel = dict(raw)
    pixel.update(shape=[576, 576, 3], nbytes=576 * 576 * 3 * 4)
    marker = worker.TensorDescriptor(pixel)
    store = worker.CameraTensorStore(
        {"tensor_descriptors": {pixel["blob"]: pixel}, "files": {}},
        Path("/synthetic/nonexistent/archive"), float("inf"),
    )
    store._snapshot = lambda *args, **kwargs: (_ for _ in ()).throw(
        AssertionError("pixel-shaped tensor reached a body open")
    )
    try:
        store.decode(marker, lambda shape: shape == [4, 4], "pixel masquerade")
    except ValueError:
        pass
    else:
        raise AssertionError("pixel-shaped tensor passed the pre-open shape gate")


def main():
    assert_formal_paths_absent()
    worker_raw, worker_text, worker_tree, worker = load_exact_source(WORKER, "_s45b_v5_worker")
    supervisor_raw, supervisor_text, supervisor_tree, supervisor = load_exact_source(
        SUPERVISOR, "_s45b_v5_supervisor",
    )

    forbidden_imports = {"numpy", "torch", "PIL", "cv2", "diffusers"}
    require(not imported_roots(worker_tree).intersection(forbidden_imports)
            and not imported_roots(supervisor_tree).intersection(forbidden_imports),
            "scientific, image, or model import found")
    require(true_publication_owners(worker_tree, "passed") == []
            and true_publication_owners(worker_tree, "terminal_authority") == [],
            "worker can publish terminal truth")
    require(set(true_publication_owners(supervisor_tree, "passed"))
            == {"formal_supervision", "synthetic_setup"}
            and set(true_publication_owners(supervisor_tree, "terminal_authority"))
            == {"formal_supervision", "synthetic_setup"},
            "passed=true exists outside the supervisor's formal/synthetic seal constructors")

    require(worker.PROTOCOL_SHA256 == sha256(PROTOCOL),
            "worker does not bind the exact protocol")
    require(worker.BINDING_TEMPLATE_SHA256 == sha256(TEMPLATE),
            "worker does not bind the exact template")
    require(worker.SELFTEST_SHA256 == sha256(Path(__file__).resolve()),
            "worker does not bind the exact independent self-test")
    require(worker.SUPERVISOR == SUPERVISOR and supervisor.WORKER == WORKER,
            "worker/supervisor canonical source paths differ")

    b0_raw = B0.read_bytes()
    b0_tree = ast.parse(b0_raw.decode("utf-8"), filename=str(B0))
    require(sha256(B0) == "f36be25001f5138bd985ca186d49c6d44e66b5b9c599b8c0dfc6e8691a4719de",
            "reviewed B0 source changed")
    require(function_source_sha(b0_raw, b0_tree, "max_abs")
            == "5b19516bcaa6d650b7259d4e806266ab40762a358989190f2d3327fbaceb3fd4",
            "B0 max_abs source segment changed")
    require(function_source_sha(b0_raw, b0_tree, "verify_requested_camera_conditions")
            == "7dfa29e4bdaca569cf485b8c575f1d48f5dbcabb61011f6ab1998fea79b9a8e3",
            "B0 camera source segment changed")

    built_in = worker.synthetic_selftest()
    require(built_in["status"] == "PASS_SYNTHETIC_ONLY", "worker synthetic math failed")
    supervised = supervisor.synthetic_selftest()
    require(supervised["status"] == "PASS_SUPERVISOR_SYNTHETIC_AND_FAULT_INJECTION_ONLY",
            "supervisor fault suite failed")

    base = [
        [0.0, -1.0, 0.0, 1.0],
        [1.0, 0.0, 0.0, -2.0],
        [0.0, 0.0, 1.0, 3.0],
        [0.0, 0.0, 0.0, 1.0],
    ]
    max_reference_error = 0.0
    for yaw in worker.EXPECTED_YAW:
        candidate = worker.expected_pose(base, yaw)
        reference = independent_expected_pose(base, yaw)
        max_reference_error = max(
            max_reference_error, worker.matrix_max_abs(candidate, reference),
        )
    require(max_reference_error <= 1e-15,
            "worker differs from the independently transcribed B0 convention")

    formal = named_function(supervisor_tree, "formal_supervision")
    preflight_lines = call_lines(
        formal,
        lambda f: isinstance(f, ast.Attribute) and f.attr == "formal_preflight",
    )
    commit_lines = call_lines(
        formal,
        lambda f: isinstance(f, ast.Attribute) and f.attr == "commit_attempt_lease",
    )
    require(len(preflight_lines) == len(commit_lines) == 1
            and preflight_lines[0] < commit_lines[0],
            "permanent attempt precedes harmless preflight")

    terminal = named_function(supervisor_tree, "publish_terminal_seal")
    terminal_text = ast.get_source_segment(supervisor_text, terminal)
    require(all(token in terminal_text for token in (
        "write_staged_regular", "os.link", "collect_evidence_bundle",
        "close_leases(leases)", "os.fsync(output_fd)",
        "os.unlink(TERMINAL_SEAL_STAGING_NAME", "nlink=2",
    )), "terminal sealer omits a required stage/revalidate/close/fsync/commit operation")
    unlink_line = call_lines(
        terminal,
        lambda f: isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name)
        and f.value.id == "os" and f.attr == "unlink",
    )
    link_line = call_lines(
        terminal,
        lambda f: isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name)
        and f.value.id == "os" and f.attr == "link",
    )
    close_lines = call_lines(
        terminal,
        lambda f: isinstance(f, ast.Name) and f.id == "close_leases",
    )
    require(len(unlink_line) == len(link_line) == 1 and max(close_lines) < unlink_line[0]
            and link_line[0] < unlink_line[0],
            "seal authority unlink is not the final transition after link and closes")

    artifact_guard = named_function(supervisor_tree, "regular_record_at")
    artifact_text = ast.get_source_segment(supervisor_text, artifact_guard)
    require(all(token in artifact_text for token in (
        "os.fstat", "os.stat", "stat.S_ISREG", "st_nlink", "stat_record",
        "read_exact_fd", "sha256_bytes",
    )), "artifact lease omits lstat/inode/link/type/size/SHA validation")
    dir_guard = named_function(supervisor_tree, "directory_record")
    dir_text = ast.get_source_segment(supervisor_text, dir_guard)
    require(all(token in dir_text for token in (
        "verify_directory_lease", "os.fstat", "os.stat", "stat.S_ISDIR",
        "os.listdir", "inventory_sha256",
    )), "canonical execution lease omits identity/inventory validation")
    bound_wait = named_function(supervisor_tree, "bounded_process_wait")
    wait_text = ast.get_source_segment(supervisor_text, bound_wait)
    require(all(token in wait_text for token in (
        "selectors.DefaultSelector", "time.monotonic", "terminate_group",
        "stdout_limit", "stderr_limit", "process.wait",
    )), "supervisor process observation is not hard bounded")
    formal_text = ast.get_source_segment(supervisor_text, formal)
    require(all(token in formal_text for token in (
        "start_new_session=True", "pass_fds=", "preexec_fn=worker_resource_limit",
        "process_group_empty", "process.returncode == 0", "len(stdout) == 0",
        "len(stderr) == 0", "publish_terminal_seal",
    )), "supervisor omits process-exit/descendant/stdio/resource gating")

    lock_checks = synthetic_lock_tests(worker)
    selective_decoder_tests(worker)

    template = json.loads(TEMPLATE.read_text())
    require(template.get("schema") == "s45b-c1-numeric-camera-guard-binding-template-v2"
            and template.get("status") == "UNBOUND_SUPERVISED_V5_TEMPLATE_NOT_EXECUTABLE"
            and template.get("placeholder_hashes") == 15,
            "v5 binding template is not explicitly unbound")
    null_upstream = [name for name, item in template["upstream"].items()
                     if item["sha256"] is None]
    null_source = [name for name, value in template["source_set"].items()
                   if value is None]
    require(len(null_upstream) + len(null_source) == 15,
            "template null count differs")
    require(template["upstream"]["s45_result_review"]["sha256"]
            == worker.S45_RESULT_REVIEW_SHA256,
            "template names another S45 result review")

    history_identities = {name: sha256(HISTORY / name) for name in EXPECTED_V4_HISTORY}
    require(history_identities == EXPECTED_V4_HISTORY,
            "withdrawn v4 source/review history changed")
    primary = json.loads((HISTORY / "SOURCE_REVIEW_PRIMARY.json").read_text())
    adversarial = json.loads((HISTORY / "SOURCE_REVIEW_ADVERSARIAL.json").read_text())
    require(primary.get("status") == "PASS_S45B_C1_NUMERIC_CAMERA_GUARD_SOURCE_REVIEW"
            and adversarial.get("status") == "BLOCKED_S45B_C1_NUMERIC_CAMERA_GUARD_SOURCE_REVIEW"
            and len(adversarial.get("blocking_findings", [])) == 2,
            "v4 correction history does not preserve PASS then BLOCKED evidence")

    assert_formal_paths_absent()
    output = {
        "schema": "s45b-c1-numeric-camera-guard-independent-synthetic-test-v2",
        "status": "PASS_V5_STATIC_SYNTHETIC_AND_FAULT_INJECTION_ONLY",
        "version": "S45B-supervised-terminal-seal-v5.0.0",
        "python": sys.version,
        "identities": {
            "camera_guard.py": hashlib.sha256(worker_raw).hexdigest(),
            "supervise_camera_guard.py": hashlib.sha256(supervisor_raw).hexdigest(),
            "PROTOCOL.md": sha256(PROTOCOL),
            "C1_CAMERA_GUARD_BINDING_TEMPLATE.json": sha256(TEMPLATE),
            "synthetic_selftest.py": sha256(Path(__file__).resolve()),
            "reviewed_b0_reference": sha256(B0),
            "withdrawn_v4_adversarial_review": history_identities["SOURCE_REVIEW_ADVERSARIAL.json"],
        },
        "checks": {
            "both_sources_compile": "PASS",
            "no_scientific_image_or_model_import": "PASS",
            "worker_has_no_passed_true_or_terminal_authority_true": "PASS",
            "supervisor_only_terminal_truth_constructors": "PASS",
            "exact_worker_protocol_template_selftest_binding": "PASS",
            "cross_version_B0_source_segment_identity": "PASS",
            "independent_left_multiply_sign_reference": "PASS",
            "max_reference_error": max_reference_error,
            "worker_numeric_positive_negative_and_boundary_suite": "PASS",
            "harmless_preflight_precedes_attempt_commit": "PASS",
            "permanent_lock_fail_closed_and_attack_suite": lock_checks,
            "pending_worker_then_process_exit_descendant_stdio_resource_supervision": "PASS",
            "terminal_two_link_invalid_then_single_unlink_commit": "PASS",
            "lock_output_report_worker_supervisor_evidence_revalidated": "PASS",
            "supervisor_fault_injection": supervised["checks"],
            "raw_tensor_list_tuple_provenance": "PASS",
            "pixel_shape_rejected_before_body_open": "PASS",
            "unbound_template_null_count": "PASS",
            "withdrawn_v4_PASS_and_BLOCKED_history_preserved": "PASS",
            "formal_paths_absent_before_and_after": "PASS",
        },
        "unbound_upstream_identities": null_upstream,
        "unbound_source_identities": null_source,
        "formal_runner_calls": 0,
        "real_c1_manifest_receipt_event_tensor_or_image_files_opened": 0,
        "c1_tensor_bodies_read": 0,
        "real_scientific_arrays_mapped": 0,
        "pixels_decoded": 0,
        "images_viewed": 0,
        "model_renderer_generation_calls": 0,
        "formal_paths_created": 0,
    }
    print(json.dumps(output, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
