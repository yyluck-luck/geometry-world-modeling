#!/usr/bin/env python3
"""Independent source and synthetic attack suite for S45B V6.

Only candidate/reference source text and generated temporary state are opened.
No real C1 manifest, receipt, event, tensor, image, or pixel is opened, and no
formal binding, permanent lock, or execution directory is created.
"""
from __future__ import annotations

import ast
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import types


HERE = Path(__file__).resolve().parent
WORKER = HERE / "camera_guard.py"
SUPERVISOR = HERE / "supervise_camera_guard.py"
PROTOCOL = HERE / "PROTOCOL.md"
TEMPLATE = HERE / "C1_CAMERA_GUARD_BINDING_TEMPLATE.json"
B0 = HERE.parents[1] / "work/S42_baseline_failure_preregistration/score_b0_blind.py"
V5 = HERE.parent / "S45B_c1_numeric_camera_guard_supervised_v5"

FORMAL_NAMES = (
    "execution_01",
    ".c1_numeric_camera_guard.lock",
    ".c1_numeric_camera_guard.lock.staging",
    "C1_CAMERA_GUARD_BINDING_V6.json",
    "BINDING_REVIEW_V6.json",
    "GOVERNANCE_ATTESTATION_V6.json",
)

EXPECTED_V5_HISTORY = {
    "camera_guard.py": "37951063262505ef18bb62e0544c31cfb5a460434e9a67b489f58fab9315dbdb",
    "supervise_camera_guard.py": "98084f2a7806b4f88a52a6599edeba9633c066f3bb2b128c4fba2ba70577b3bd",
    "PROTOCOL.md": "29915a117a561c73e32e30ae3f85d09d7466adb4a1a247fcda1b9da1f3366139",
    "C1_CAMERA_GUARD_BINDING_TEMPLATE.json": "12045c57d99fbaa3275f2023bef04847bcbea5825a5dac67a1be7cfb4382bd52",
    "synthetic_selftest.py": "c95331c14d2d17256da42efb94f86c636a468e33918d4db48a639c7129749593",
    "SOURCE_REVIEW_PRIMARY_V5.json": "ad062bf954faeaaaf754d5ed554d0cdda0778da9e5ed1f70090c6340b060d55e",
    "SOURCE_REVIEW_ADVERSARIAL_V5.json": "92950952b3fe260f441fe555d94a18dee589a036749035204c926ea8fe14b640",
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
    require(1 <= node.lineno <= node.end_lineno <= len(lines),
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


def enclosing_function(tree):
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
    owner = enclosing_function(tree)
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if (isinstance(key, ast.Constant) and key.value == key_name
                        and isinstance(value, ast.Constant) and value.value is True):
                    found.append(owner(node))
        if (isinstance(node, ast.keyword) and node.arg == key_name
                and isinstance(node.value, ast.Constant) and node.value.value is True):
            found.append(owner(node))
    return found


def named_function(tree, name):
    found = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    require(len(found) == 1, "missing or duplicate function: " + name)
    return found[0]


def call_lines(function_node, predicate):
    return sorted(
        node.lineno for node in ast.walk(function_node)
        if isinstance(node, ast.Call) and predicate(node.func)
    )


def name_call(name):
    return lambda node: isinstance(node, ast.Name) and node.id == name


def attribute_call(owner, name):
    return lambda node: (
        isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
        and node.value.id == owner and node.attr == name
    )


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


def formal_paths_present(root):
    return [str(Path(root) / name) for name in FORMAL_NAMES
            if os.path.lexists(Path(root) / name)]


def assert_formal_paths_absent():
    present = formal_paths_present(HERE)
    require(not present, "formal V6 path unexpectedly exists: " + repr(present))


def review_files_do_not_break_source_suite():
    with tempfile.TemporaryDirectory(prefix="s45b_v6_review_phase_") as raw:
        root = Path(raw)
        (root / "SOURCE_REVIEW_PRIMARY_V6.json").write_text("{}\n")
        (root / "SOURCE_REVIEW_ADVERSARIAL_V6.json").write_text("{}\n")
        require(not formal_paths_present(root),
                "Completed source reviews were confused with formal attempt paths")


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
            and set(cache) == {"c2ws", "Ks"},
            "camera selector retained or traversed a pixel field")

    pixel = dict(raw)
    pixel.update(shape=[576, 576, 3], nbytes=576 * 576 * 3 * 4)
    store = worker.CameraTensorStore(
        {"tensor_descriptors": {pixel["blob"]: pixel}, "files": {}},
        Path("/synthetic/nonexistent/archive"), float("inf"),
    )
    store._snapshot = lambda *args, **kwargs: (_ for _ in ()).throw(
        AssertionError("pixel-shaped tensor reached a body open")
    )
    try:
        store.decode(worker.TensorDescriptor(pixel), lambda shape: shape == [4, 4],
                     "pixel masquerade")
    except ValueError:
        pass
    else:
        raise AssertionError("pixel-shaped tensor passed the pre-open shape gate")


def main():
    assert_formal_paths_absent()
    review_files_do_not_break_source_suite()
    worker_raw, worker_text, worker_tree, worker = load_exact_source(WORKER, "_s45b_v6_worker")
    supervisor_raw, supervisor_text, supervisor_tree, supervisor = load_exact_source(
        SUPERVISOR, "_s45b_v6_supervisor",
    )

    forbidden = {"numpy", "torch", "PIL", "cv2", "diffusers"}
    require(not imported_roots(worker_tree).intersection(forbidden)
            and not imported_roots(supervisor_tree).intersection(forbidden),
            "scientific, image, or model import found")
    require(true_publication_owners(worker_tree, "passed") == []
            and true_publication_owners(worker_tree, "terminal_authority") == [],
            "worker can publish terminal truth")
    passed_owners = true_publication_owners(supervisor_tree, "passed")
    authority_owners = true_publication_owners(supervisor_tree, "terminal_authority")
    require(passed_owners == ["formal_supervision"]
            and authority_owners == ["formal_supervision"],
            "terminal truth exists outside the supervisor exit-gated stdout record")

    require(worker.PROTOCOL_SHA256 == sha256(PROTOCOL), "worker protocol pin differs")
    require(worker.BINDING_TEMPLATE_SHA256 == sha256(TEMPLATE), "worker template pin differs")
    require(worker.SELFTEST_SHA256 == sha256(Path(__file__).resolve()),
            "worker independent-selftest pin differs")
    require(worker.SUPERVISOR == SUPERVISOR and supervisor.WORKER == WORKER,
            "worker/supervisor canonical paths differ")

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
    require(built_in["status"] == "PASS_SYNTHETIC_ONLY", "worker math suite failed")
    supervised = supervisor.synthetic_selftest()
    require(supervised["status"] == "PASS_SUPERVISOR_SYNTHETIC_AND_FAULT_INJECTION_ONLY",
            "supervisor attack suite failed")

    base = [
        [0.0, -1.0, 0.0, 1.0], [1.0, 0.0, 0.0, -2.0],
        [0.0, 0.0, 1.0, 3.0], [0.0, 0.0, 0.0, 1.0],
    ]
    max_reference_error = max(
        worker.matrix_max_abs(worker.expected_pose(base, yaw),
                              independent_expected_pose(base, yaw))
        for yaw in worker.EXPECTED_YAW
    )
    require(max_reference_error <= 1e-15, "worker differs from B0 yaw convention")

    formal = named_function(supervisor_tree, "formal_supervision")
    preflight_lines = call_lines(formal, attribute_call("worker", "formal_preflight"))
    capability_lines = call_lines(formal, name_call("runtime_capability_preflight"))
    commit_lines = call_lines(formal, attribute_call("worker", "commit_attempt_lease"))
    require(len(preflight_lines) == len(capability_lines) == len(commit_lines) == 1
            and preflight_lines[0] < capability_lines[0] < commit_lines[0],
            "exact runtime capability preflight does not precede permanent attempt")
    formal_segment = ast.get_source_segment(supervisor_text, formal)
    require("spawn_contained" in formal_segment and "bounded_process_wait" in formal_segment
            and "process_group_empty" not in formal_segment
            and "capability_sha256" in formal_segment
            and "runtime_capability_preflight" in formal_segment
            and "executable_snapshot(SANDBOX_EXEC)" in formal_segment
            and "executable_snapshot(PYTHON_EXECUTABLE)" in formal_segment,
            "formal supervisor bypasses V6 containment/capability binding")

    resource_limit = ast.get_source_segment(
        supervisor_text, named_function(supervisor_tree, "worker_resource_limit"),
    )
    require("RLIMIT_CPU" in resource_limit and "RLIMIT_FSIZE" in resource_limit
            and "RLIMIT_AS" not in resource_limit and "RLIMIT_RSS" not in resource_limit,
            "nonportable Darwin address-space/RSS preexec limit survived")
    wait_segment = ast.get_source_segment(
        supervisor_text, named_function(supervisor_tree, "bounded_process_wait"),
    )
    require(all(token in wait_segment for token in (
        "darwin_process_usage", "os.wait4", "memory_limit_exceeded",
        "wait4_peak_rss", "terminate_exact_process",
    )), "exact-PID Darwin memory/wait4 gate is incomplete")
    capability_segment = ast.get_source_segment(
        supervisor_text, named_function(supervisor_tree, "synthetic_capability_child"),
    )
    require(all(token in capability_segment for token in (
        "FORK_SETSID_KEEP_STDIO", "FORK_SETSID_CLOSE_STDIO",
        "POSIX_SPAWN_SETSID", "resource.getrlimit",
    )), "setsid/stdio containment attacks are absent")

    terminal = named_function(supervisor_tree, "publish_terminal_seal")
    unlink_lines = call_lines(terminal, attribute_call("os", "unlink"))
    post_record_lines = call_lines(terminal, name_call("regular_record_at"))
    close_lines = call_lines(terminal, name_call("close_leases"))
    terminal_segment = ast.get_source_segment(supervisor_text, terminal)
    require(len(unlink_lines) >= 1 and len(post_record_lines) == 1
            and min(unlink_lines) < post_record_lines[0] < min(close_lines)
            and all(token in terminal_segment for token in (
                "RENAME_RECREATE_FINAL_AFTER_UNLINK",
                "UNLINK_RECREATE_FINAL_AFTER_UNLINK",
                "observed_while_all_core_evidence_fds_held",
                "canonical_path_alone_is_authoritative",
            )), "terminal authority is not consumed from held FDs after commit")
    diagnostic_segment = ast.get_source_segment(
        supervisor_text,
        named_function(supervisor_tree, "canonical_seal_matches_held_observation"),
    )
    require("if not isinstance(observation, dict)" in diagnostic_segment
            and "candidate_lstat" in diagnostic_segment,
            "canonical pathname can be accepted without a held-FD observation")
    terminal_call_lines = call_lines(formal, name_call("publish_terminal_seal"))
    control_close_lines = call_lines(formal, name_call("close_terminal_control_fds"))
    truth_lines = sorted(
        node.lineno for node in ast.walk(formal)
        if isinstance(node, ast.Dict)
        and any(
            isinstance(key, ast.Constant) and key.value == "passed"
            and isinstance(value, ast.Constant) and value.value is True
            for key, value in zip(node.keys, node.values)
        )
    )
    require(len(terminal_call_lines) == len(control_close_lines) == len(truth_lines) == 1
            and terminal_call_lines[0] < control_close_lines[0] < truth_lines[0]
            and "requires_supervisor_process_exit_zero" in formal_segment
            and "write_all(sys.stdout.fileno(), external_body)" in formal_segment
            and "sys.stdout.flush" in formal_segment,
            "terminal PASS is not restricted to post-close exact stdout plus exit-zero")

    worker_formal = ast.get_source_segment(
        worker_text, named_function(worker_tree, "formal_worker_run"),
    )
    require(all(token in worker_formal for token in (
        "lock_doc", "capability_sha256", "runtime_capability_preflight",
        "governance_attestation_sha256",
    )), "worker does not bind capability/governance through the permanent lock")

    template = json.loads(TEMPLATE.read_text())
    require(template.get("schema") == "s45b-c1-numeric-camera-guard-binding-template-v3"
            and template.get("status") == "UNBOUND_SUPERVISED_V6_TEMPLATE_NOT_EXECUTABLE"
            and template.get("placeholder_hashes") == 15,
            "V6 binding template is not explicitly unbound")
    nulls = sum(value is None for value in template["source_set"].values())
    nulls += sum(item["sha256"] is None for item in template["upstream"].values())
    require(nulls == 15 and template["governance_attestation_requirement"]["sha256"] is None,
            "V6 template null/governance boundary differs")

    history = {name: sha256(V5 / name) for name in EXPECTED_V5_HISTORY}
    require(history == EXPECTED_V5_HISTORY, "V5 source or review history changed")
    blocked = json.loads((V5 / "SOURCE_REVIEW_ADVERSARIAL_V5.json").read_text())
    require(blocked.get("status")
            == "BLOCKED_S45B_C1_NUMERIC_CAMERA_GUARD_SUPERVISED_SOURCE_REVIEW_V5"
            and len(blocked.get("blocking_findings", [])) == 3,
            "V5 three-CRITICAL correction evidence is not preserved")

    selective_decoder_tests(worker)
    assert_formal_paths_absent()
    output = {
        "schema": "s45b-c1-numeric-camera-guard-independent-synthetic-test-v3",
        "status": "PASS_V6_STATIC_SYNTHETIC_AND_ATTACK_TESTS_ONLY",
        "version": "S45B-supervised-held-fd-no-fork-exit-gated-v6.0.0",
        "python": sys.version,
        "identities": {
            "camera_guard.py": hashlib.sha256(worker_raw).hexdigest(),
            "supervise_camera_guard.py": hashlib.sha256(supervisor_raw).hexdigest(),
            "PROTOCOL.md": sha256(PROTOCOL),
            "C1_CAMERA_GUARD_BINDING_TEMPLATE.json": sha256(TEMPLATE),
            "synthetic_selftest.py": sha256(Path(__file__).resolve()),
            "reviewed_b0_reference": sha256(B0),
            "v5_adversarial_blocked_review": history["SOURCE_REVIEW_ADVERSARIAL_V5.json"],
        },
        "checks": {
            "source_compile_and_no_model_import": "PASS",
            "worker_pending_only_supervisor_terminal_constructor": "PASS",
            "exact_protocol_template_selftest_binding": "PASS",
            "B0_source_segments_and_yaw_math": "PASS",
            "max_reference_error": max_reference_error,
            "runtime_capability_precedes_one_use_commit": "PASS",
            "RLIMIT_AS_removed_exact_launcher_exercised": "PASS",
            "darwin_libproc_wait4_memory_fail_closed": "PASS",
            "sandbox_no_fork_setsid_stdio_attack_matrix": "PASS",
            "held_fd_terminal_consumer_and_path_swap_attacks": "PASS",
            "review_phase_canonical_rerun": "PASS",
            "raw_tensor_provenance_and_pixel_preopen_rejection": "PASS",
            "V5_sources_primary_and_BLOCKED_reviews_preserved": "PASS",
            "supervisor_attack_suite": supervised["checks"],
            "formal_paths_absent_before_and_after": "PASS",
        },
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
