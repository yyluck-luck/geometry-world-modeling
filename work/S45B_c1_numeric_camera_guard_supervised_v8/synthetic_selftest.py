#!/usr/bin/env python3
"""Independent source and synthetic attack suite for S45B V8.

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
V6 = HERE.parent / "S45B_c1_numeric_camera_guard_supervised_v6"

FORMAL_NAMES = (
    "execution_01",
    ".c1_numeric_camera_guard.lock",
    ".c1_numeric_camera_guard.lock.staging",
    "C1_CAMERA_GUARD_BINDING_V8.json",
    "BINDING_REVIEW_V8.json",
    "GOVERNANCE_ATTESTATION_V8.json",
)

EXPECTED_V6_HISTORY = {
    "camera_guard.py": "5a4c327f52800da456cb7f6292ed9c2864e2d4c44f0988e38cadfc7972248d0c",
    "supervise_camera_guard.py": "bf6a9d79b2ae4015b2452af3fc711964418921ce0f3bfcd31f5a11e28947db92",
    "PROTOCOL.md": "8ba86240ba1fe8352230dd8b1739604e7392bb32fe5bbfcdfe088b0cde678977",
    "C1_CAMERA_GUARD_BINDING_TEMPLATE.json": "f3be3fb84b4f5c07b82d7d2266ee8517852f9b41301220f4e90a7b6b1af092e8",
    "synthetic_selftest.py": "0b616d626ee170efcbff2b4fcaf24ab53e8f1d3dfea8d59e034f38084385b413",
    "FROZEN_SOURCE_SET.json": "4156b62c26e57c0717914859901053fbf4967779337b4cd6d3401bd6be53d26d",
    "FINAL_SYNTHETIC_SELFTEST_RECEIPT.json": "58e4b4a7431a5969be7b34f374f10c51939ac8e726f61b7721d99203d64938d0",
    "SOURCE_REVIEW_PRIMARY_V6.json": "0b30345a8546cd2e89036b118b12b75825cf7662b133d2bac380b4f9904aeb16",
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
    require(not present, "formal V8 path unexpectedly exists: " + repr(present))


def review_files_do_not_break_source_suite():
    with tempfile.TemporaryDirectory(prefix="s45b_v8_review_phase_") as raw:
        root = Path(raw)
        (root / "SOURCE_REVIEW_PRIMARY_V8.json").write_text("{}\n")
        (root / "SOURCE_REVIEW_ADVERSARIAL_V8.json").write_text("{}\n")
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


def final_cache_anchor_regression(worker):
    """Compare actual V7/V8 functions on opposing and aligned tolerance bands."""
    import copy
    legacy_path = HERE.parent / "S45B_c1_numeric_camera_guard_supervised_v7/camera_guard.py"
    require(sha256(legacy_path) == "6f60c290888dd3ee66aabf570d87136c8026f25d09372d3d1e42f4ba9c0bc34c",
            "preserved V7 numeric witness source changed")
    _, _, _, legacy = load_exact_source(legacy_path, "_s45b_v7_anchor_witness")
    records = []
    for field in ("pose", "K", "both"):
        for direction in (-1.0, 1.0):
            for valid_at_final in (False, True):
                base = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0],
                        [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
                k = [[500.0, 0.0, 288.0], [0.0, 500.0, 288.0], [0.0, 0.0, 1.0]]
                poses = [worker.expected_pose(base, yaw) for yaw in worker.EXPECTED_YAW]
                ks = [copy.deepcopy(k) for _ in poses]
                shift = direction * worker.TOLERANCE * (1.5 if valid_at_final else -0.75)
                for index in range(1, 9):
                    if field in ("pose", "both"):
                        poses[index][0][3] += shift
                    if field in ("K", "both"):
                        ks[index][0][0] += shift
                commits = copy.deepcopy([
                    {"c2ws": poses[:5], "Ks": ks[:5]},
                    {"c2ws": poses[:9], "Ks": ks[:9]},
                ])
                # deepcopy the two cache entries independently: ID0 must differ.
                commits = [copy.deepcopy(commits[0]), copy.deepcopy(commits[1])]
                if field in ("pose", "both"):
                    commits[1]["c2ws"][0][0][3] += direction * worker.TOLERANCE * 0.75
                if field in ("K", "both"):
                    commits[1]["Ks"][0][0][0] += direction * worker.TOLERANCE * 0.75
                batches = copy.deepcopy([
                    {"c2ws": poses[1:5], "Ks": ks[1:5]},
                    {"c2ws": poses[5:9], "Ks": ks[5:9]},
                ])
                outcomes = {}
                for name, module in (("v7", legacy), ("v8", worker)):
                    try:
                        result = module.evaluate_numeric_guard(batches, commits)
                    except module.GuardInvalid:
                        outcomes[name] = False
                    else:
                        require(result["status"] == "PASS_C1_REQUESTED_CAMERA_INPUT_CONDITION_GUARD_ONLY",
                                "numeric guard returned an unexpected result")
                        outcomes[name] = True
                require(outcomes["v8"] is valid_at_final,
                        "V8 disagrees with the final-anchor tolerance band")
                require(outcomes["v7"] is (not valid_at_final),
                        "preserved V7 failed to reproduce the first-anchor discrepancy")
                records.append({"field": field, "direction": direction,
                                "expected_final_anchor_pass": valid_at_final, **outcomes})
    require(len(records) == 12, "anchor regression case count differs")
    return {"status": "PASS_SYNTHETIC_FINAL_CACHE_ANCHOR_REGRESSION", "cases": records,
            "real_data_reads": 0, "model_runs": 0}


def main():
    assert_formal_paths_absent()
    review_files_do_not_break_source_suite()
    worker_raw, worker_text, worker_tree, worker = load_exact_source(WORKER, "_s45b_v8_worker")
    supervisor_raw, supervisor_text, supervisor_tree, supervisor = load_exact_source(
        SUPERVISOR, "_s45b_v8_supervisor",
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
    required_v8_attacks = {
        "prespawn_create_only_pair_child_inherited_fd_publication",
        "prespawn_report.json_substitution",
        "prespawn_worker_receipt.json_substitution",
        "preacquisition_report.json_substitution",
        "preacquisition_worker_receipt.json_substitution",
        "same_inode_report_tamper_without_capability",
        "postcheck_worker_path_swap_cannot_change_executed_bytes",
        "forked_worker_process_uuid_matches_running_interpreter",
        "complete_report_top_level_deletion_matrix",
        "complete_worker_receipt_top_level_deletion_matrix",
        "complete_schema_rejects_planned_sequence_nested_field",
        "complete_schema_rejects_camera_tensor_identity_nested_field",
        "complete_schema_rejects_not_evaluated_sentinel",
    }
    require(required_v8_attacks.issubset(supervised["checks"])
            and supervised["checks"]["complete_report_top_level_deletion_matrix"]
            == len(supervisor.REPORT_KEYS)
            and supervised["checks"]["complete_worker_receipt_top_level_deletion_matrix"]
            == len(supervisor.WORKER_RECEIPT_KEYS),
            "V8 pre-acquisition or complete-schema attack matrix is incomplete")

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
    require("spawn_bound_worker" in formal_segment and "bounded_process_wait" in formal_segment
            and "process_group_empty" not in formal_segment
            and "capability_sha256" in formal_segment
            and "runtime_capability_preflight" in formal_segment
            and "create_prebound_worker_artifact" in formal_segment
            and "verify_prebound_worker_artifact" in formal_segment
            and "validate_complete_worker_artifacts" in formal_segment
            and "worker_command" not in formal_segment
            and "spawn_contained" not in formal_segment
            and "open_regular_lease(output_fd, FORMAL_OUT, REPORT_NAME)" not in formal_segment
            and "open_regular_lease(output_fd, FORMAL_OUT, WORKER_RECEIPT_NAME)" not in formal_segment,
            "formal supervisor bypasses V8 containment/capability binding")

    fork_segment = ast.get_source_segment(
        supervisor_text, named_function(supervisor_tree, "_fork_loaded_entry"),
    )
    bound_spawn_segment = ast.get_source_segment(
        supervisor_text, named_function(supervisor_tree, "spawn_bound_worker"),
    )
    loaded_worker_segment = ast.get_source_segment(
        supervisor_text, named_function(supervisor_tree, "_execute_loaded_worker"),
    )
    require("os.fork()" in fork_segment
            and "apply_darwin_no_fork_sandbox" in fork_segment
            and "subprocess" not in fork_segment and "Popen" not in fork_segment
            and "verify_loaded_worker_lease" in bound_spawn_segment
            and "FORK_ALREADY_RUNNING_INTERPRETER_THEN_SANDBOX_INIT_NO_EXEC"
            in bound_spawn_segment
            and "lease[\"code\"]" in bound_spawn_segment
            and "exec(source_code, module.__dict__)" in loaded_worker_segment,
            "Worker bytes or interpreter are not bound through fork-without-exec")

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
        "wait4_peak_rss", "terminate_exact_process", "expected_process_uuid",
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
        "governance_attestation_sha256", "verify_inherited_worker_source",
        "write_prebound_json", "report_fd", "worker_receipt_fd",
    )) and "write_new_at(output_fd, REPORT_NAME" not in worker_formal
        and "write_new_at(output_fd, WORKER_RECEIPT_NAME" not in worker_formal,
        "worker does not use only the inherited source/output bindings")

    template = json.loads(TEMPLATE.read_text())
    require(template.get("schema") == "s45b-c1-numeric-camera-guard-binding-template-v4"
            and template.get("status") == "UNBOUND_SUPERVISED_V8_TEMPLATE_NOT_EXECUTABLE"
            and template.get("placeholder_hashes") == 15,
            "V8 binding template is not explicitly unbound")
    nulls = sum(value is None for value in template["source_set"].values())
    nulls += sum(item["sha256"] is None for item in template["upstream"].values())
    require(nulls == 15 and template["governance_attestation_requirement"]["sha256"] is None,
            "V8 template null/governance boundary differs")

    history = {name: sha256(V6 / name) for name in EXPECTED_V6_HISTORY}
    require(history == EXPECTED_V6_HISTORY, "V6 source/review history changed")
    blocked = json.loads((V6 / "SOURCE_REVIEW_PRIMARY_V6.json").read_text())
    require(blocked.get("status")
            == "BLOCKED_S45B_C1_NUMERIC_CAMERA_GUARD_SUPERVISED_SOURCE_REVIEW_V6"
            and sum(item.get("severity") == "CRITICAL"
                    for item in blocked.get("blocking_findings", [])) == 2
            and sum(item.get("severity") == "MAJOR"
                    for item in blocked.get("blocking_findings", [])) == 2,
            "V6 two-CRITICAL/two-MAJOR correction evidence is not preserved")

    selective_decoder_tests(worker)
    anchor_regression = final_cache_anchor_regression(worker)
    assert_formal_paths_absent()
    output = {
        "schema": "s45b-c1-numeric-camera-guard-independent-synthetic-test-v4",
        "status": "PASS_V8_STATIC_SYNTHETIC_AND_ATTACK_TESTS_ONLY",
        "version": "S45B-prebound-output-fork-bound-interpreter-complete-schema-v8.0.0",
        "python": sys.version,
        "identities": {
            "camera_guard.py": hashlib.sha256(worker_raw).hexdigest(),
            "supervise_camera_guard.py": hashlib.sha256(supervisor_raw).hexdigest(),
            "PROTOCOL.md": sha256(PROTOCOL),
            "C1_CAMERA_GUARD_BINDING_TEMPLATE.json": sha256(TEMPLATE),
            "synthetic_selftest.py": sha256(Path(__file__).resolve()),
            "reviewed_b0_reference": sha256(B0),
            "v6_primary_blocked_review": history["SOURCE_REVIEW_PRIMARY_V6.json"],
        },
        "checks": {
            "source_compile_and_no_model_import": "PASS",
            "final_cache_anchor_twelve_boundary_cases": anchor_regression,
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
            "V6_sources_receipts_and_BLOCKED_review_preserved": "PASS",
            "prespawn_prebound_output_pair_and_preacquisition_attacks": "PASS",
            "fork_without_exec_worker_and_interpreter_binding": "PASS",
            "complete_numeric_and_provenance_schema_validation": "PASS",
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
