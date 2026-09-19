#!/usr/bin/env python3
"""V6 source-only adversarial checks; never invoke a formal C2 path or model."""
from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import sys
import tempfile
import time
from types import ModuleType


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PRODUCTION = (
    HERE / "PROTOCOL.md",
    HERE / "FREEZE_PROTOCOL.md",
    HERE / "generation_gate.py",
    HERE / "runtime_adapter.py",
    HERE / "launch_generation.py",
    HERE / "freeze_c2_manifest.py",
    HERE / "create_launch_authorization.py",
    HERE / "inference_seed44.yaml",
)
PYTHON_SOURCES = tuple(path for path in PRODUCTION if path.suffix == ".py") + (
    HERE / "static_selftest.py",
)
FORMAL_PATHS = (
    HERE / "freeze_attempt_01",
    HERE / "review_attachment_01",
    HERE / "FINAL_ATTACHMENT_REVIEW.json",
    HERE / "LAUNCH_READINESS_REVIEW.json",
    HERE / "launch_authorization_01.json",
    HERE / "launch_authorization_attempt_01",
    HERE / ".freeze_attempt_01.claimed",
    HERE / ".review_attachment_01.claimed",
    HERE / ".review_attachment_01.preflight",
    HERE / ".freeze_attempt_01.staging",
    HERE / ".review_attachment_01.staging",
    HERE / ".execution_01.watchdog_failure.json",
    HERE / ".execution_01.supervisor_failure.json",
    HERE / "execution_01",
    ROOT / "results/S47_C2_confirmation_generation",
)
SCIENTIFIC_PREFIXES = (
    "torch", "numpy", "PIL", "diffusers", "open_clip", "omegaconf",
    "kornia", "cv2", "safetensors",
)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, document, mode=0o444):
    payload = (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode()
    if path.exists():
        path.chmod(0o600)
    path.write_bytes(payload)
    path.chmod(mode)
    return hashlib.sha256(payload).hexdigest()


def load_module_snapshot(name, path):
    payload = Path(path).read_bytes()
    module = ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = ""
    sys.modules[name] = module
    exec(compile(payload, str(path), "exec", dont_inherit=True), module.__dict__)
    return module


class DenyScientificImports:
    def find_spec(self, fullname, path=None, target=None):
        if any(fullname == prefix or fullname.startswith(prefix + ".")
               for prefix in SCIENTIFIC_PREFIXES):
            raise ImportError("V6 source-only test denied scientific import: " + fullname)
        return None


def rejected(function, *args, **kwargs):
    try:
        function(*args, **kwargs)
    except (RuntimeError, OSError):
        return True
    raise RuntimeError("Adversarial negative case was accepted")


def top_function(tree, name):
    return next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                and node.name == name)


def nested_names(function):
    return {node.name for node in ast.walk(function)
            if isinstance(node, ast.FunctionDef) and node is not function}


class NoSuchProcess(Exception):
    pass


class SyntheticProcessAPI:
    """Small psutil-shaped registry used only by disposable process tests."""

    STATUS_ZOMBIE = "zombie"

    def __init__(self, registry):
        self.registry = Path(registry)

    def _records(self):
        records = {}
        if self.registry.exists():
            for line in self.registry.read_text(encoding="utf-8").splitlines():
                if line:
                    item = json.loads(line)
                    records[int(item["pid"])] = item
        return records

    def Process(self, pid):
        return SyntheticProcess(self, int(pid))


class SyntheticProcess:
    def __init__(self, api, pid):
        self.api = api
        self.pid = pid

    def _record(self):
        item = self.api._records().get(self.pid)
        if item is None or not self.is_running():
            raise NoSuchProcess(self.pid)
        return item

    def create_time(self):
        return float(self._record()["created"])

    def status(self):
        self._record()
        return "running"

    def is_running(self):
        try:
            os.kill(self.pid, 0)
        except ProcessLookupError:
            return False
        return True

    def children(self, recursive=False):
        require(recursive is False, "Synthetic process API only exposes direct children")
        result = []
        for item in self.api._records().values():
            if int(item["parent_pid"]) == self.pid:
                child = SyntheticProcess(self.api, int(item["pid"]))
                if child.is_running():
                    result.append(child)
        return result

    def send_signal(self, current_signal):
        self._record()
        os.kill(self.pid, current_signal)


def register_synthetic_process(path, pid, parent_pid):
    line = json.dumps(
        {"pid": int(pid), "parent_pid": int(parent_pid), "created": float(pid)},
        sort_keys=True,
    ).encode("utf-8") + b"\n"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        require(os.write(descriptor, line) == len(line),
                "Synthetic process registration was partial")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def synthetic_prepare_terminal_probe(gate, scratch):
    names = (
        "HERE", "PREPARE_ROOT", "PREPARE_CORE", "PREPARE_RECEIPT",
        "PREPARE_SENTINEL", "PREPARE_STAGING_LEASE", "FREEZE_PROTOCOL",
        "FREEZE_PROTOCOL_SHA256",
    )
    original = {name: getattr(gate, name) for name in names}
    root = scratch / "prepare-control"
    root.mkdir()
    attempt = root / "freeze_attempt_01"
    attempt.mkdir()
    freeze_tool = root / "freeze_c2_manifest.py"
    freeze_tool.write_text("# synthetic standard-library probe\n")
    protocol = root / "FREEZE_PROTOCOL.md"
    protocol.write_text("synthetic\n")
    sentinel_path = root / ".freeze_attempt_01.claimed"
    stage_path = root / ".freeze_attempt_01.staging"
    try:
        gate.HERE = root
        gate.PREPARE_ROOT = attempt
        gate.PREPARE_CORE = attempt / "manifest_core.json"
        gate.PREPARE_RECEIPT = attempt / "receipt.json"
        gate.PREPARE_SENTINEL = sentinel_path
        gate.PREPARE_STAGING_LEASE = stage_path
        gate.FREEZE_PROTOCOL = protocol
        gate.FREEZE_PROTOCOL_SHA256 = sha(protocol)
        root_stat = os.stat(root, follow_symlinks=False)
        attempt_stat = os.stat(attempt, follow_symlinks=False)
        core = {"review_receipts": {}, "synthetic": "V6"}
        core_file_sha = write_json(gate.PREPARE_CORE, core)
        core_sha = gate.core_sha256(core)
        sentinel = {
            "schema": "s47-c2-fixed-attempt-sentinel-v1",
            "status": "ATTEMPT_IRREVERSIBLY_CLAIMED",
            "mode": "prepare",
            "claimed_utc": "2026-09-08T00:00:00+00:00",
            "tool_source_sha256": sha(freeze_tool),
            "parent_directory_identity": {
                "device": root_stat.st_dev, "inode": root_stat.st_ino,
            },
            "output_path": str(attempt),
            "staging_path": str(stage_path),
            "retry_permitted": False,
        }
        sentinel_sha = write_json(sentinel_path, sentinel)
        receipt = {
            "schema": "s47-c2-freeze-tool-receipt-v2",
            "status": "S47_C2_CORE_FROZEN_AWAITING_TWO_REVIEWS",
            "mode": "prepare",
            "started_utc": "2026-09-07T23:59:59+00:00",
            "completed_utc": "2026-09-08T00:00:01+00:00",
            "manifest_core_path": str(gate.PREPARE_CORE),
            "manifest_core_file_sha256": core_file_sha,
            "core_sha256": core_sha,
            "prepare_receipt_path": str(gate.PREPARE_RECEIPT),
            "tool_source_path": str(freeze_tool),
            "tool_source_sha256": sha(freeze_tool),
            "freeze_protocol_sha256": sha(protocol),
            "scientific_status": "NOT_EVALUATED",
            "input_bytes_hashed": gate.C2_INPUT_BYTES,
            "config_bytes_hashed": gate.C2_CONFIG.stat().st_size,
            "config_seed_derivation": "EXACT_S40_BYTES_EXCEPT_UNIQUE_SEED_42_TO_44_PLUS_ONE_TERMINAL_LF",
            "source_unchanged_at_close": True,
            "component_bodies_read": 0,
            "pixels_decoded": 0,
            "scientific_imports": 0,
            "generation_calls": 0,
            "retry_permitted": False,
            "prepare_directory_identity": {
                "device": attempt_stat.st_dev, "inode": attempt_stat.st_ino,
            },
            "terminal_shape": ["manifest_core.json", "receipt.json"],
            "attempt_sentinel": {"path": str(sentinel_path), "sha256": sentinel_sha},
        }
        receipt_sha = write_json(gate.PREPARE_RECEIPT, receipt)
        positive = gate.require_successful_prepare_bundle(
            core_file_sha256_value=core_file_sha,
            core_sha256_value=core_sha,
            receipt_sha256_value=receipt_sha,
        )
        require(positive["receipt_sha256"] == receipt_sha,
                "Synthetic successful prepare bundle was rejected")
        write_json(attempt / "failure_receipt.json", {"status": "FAILED"})
        coexistence = rejected(
            gate.require_successful_prepare_bundle,
            core_file_sha256_value=core_file_sha,
            core_sha256_value=core_sha,
            receipt_sha256_value=receipt_sha,
        )
        os.unlink(attempt / "failure_receipt.json")
        tampered = dict(receipt, unexpected_success_field=True)
        tampered_sha = write_json(gate.PREPARE_RECEIPT, tampered)
        exact_shape = rejected(
            gate.require_successful_prepare_bundle,
            core_file_sha256_value=core_file_sha,
            core_sha256_value=core_sha,
            receipt_sha256_value=tampered_sha,
        )
        return {"success_failure_coexistence": coexistence,
                "unexpected_success_field": exact_shape}
    finally:
        for name, value in original.items():
            setattr(gate, name, value)


def synthetic_authorization_terminal_probe(gate, scratch):
    names = (
        "AUTHORIZATION_ATTEMPT", "AUTHORIZATION_ATTEMPT_STARTED",
        "AUTHORIZATION_ATTEMPT_RECEIPT", "LAUNCH_AUTHORIZATION",
    )
    original = {name: getattr(gate, name) for name in names}
    attempt = scratch / "authorization_attempt_01"
    attempt.mkdir()
    authorization_path = scratch / "launch_authorization_01.json"
    authorization_sha = write_json(authorization_path, {"synthetic": True})
    authorization_stat = os.stat(authorization_path, follow_symlinks=False)
    attempt_stat = os.stat(attempt, follow_symlinks=False)
    attempt_identity = {"device": attempt_stat.st_dev, "inode": attempt_stat.st_ino}
    authorization_identity = {
        "device": authorization_stat.st_dev,
        "inode": authorization_stat.st_ino,
        "size": authorization_stat.st_size,
        "mode": authorization_stat.st_mode & 0o7777,
    }
    expected, tool_sha = "a" * 64, "b" * 64
    try:
        gate.AUTHORIZATION_ATTEMPT = attempt
        gate.AUTHORIZATION_ATTEMPT_STARTED = attempt / "attempt_started.json"
        gate.AUTHORIZATION_ATTEMPT_RECEIPT = attempt / "success_receipt.json"
        gate.LAUNCH_AUTHORIZATION = authorization_path
        started = {
            "schema": "s47-c2-authorization-attempt-start-v2",
            "status": "ATTEMPT_LEASE_CLAIMED",
            "attempt_path": str(attempt),
            "attempt_identity": attempt_identity,
            "started_utc": "2026-09-08T00:00:00+00:00",
            "tool_source_sha256": tool_sha,
            "manifest_sha256": expected,
            "retry_permitted": False,
        }
        started_sha = write_json(gate.AUTHORIZATION_ATTEMPT_STARTED, started)
        success = {
            "schema": "s47-c2-authorization-attempt-receipt-v2",
            "status": "AUTHORIZED_AND_ATTEMPT_SEALED",
            "attempt_path": str(attempt),
            "attempt_identity": attempt_identity,
            "attempt_started_sha256": started_sha,
            "authorization_path": str(authorization_path),
            "authorization_sha256": authorization_sha,
            "authorization_identity": authorization_identity,
            "tool_source_sha256": tool_sha,
            "manifest_sha256": expected,
            "completed_utc": "2026-09-08T00:00:01+00:00",
            "retry_permitted": False,
            "generation_calls": 0,
            "pixels_decoded": 0,
            "terminal_shape": ["attempt_started.json", "success_receipt.json"],
            "terminal_success": True,
        }
        write_json(gate.AUTHORIZATION_ATTEMPT_RECEIPT, success)
        gate.require_successful_authorization_attempt(
            expected, authorization_sha, tool_sha, authorization_identity
        )
        write_json(attempt / "failure_receipt.json", {"status": "FAILED"})
        coexistence = rejected(
            gate.require_successful_authorization_attempt,
            expected, authorization_sha, tool_sha, authorization_identity,
        )
        os.unlink(attempt / "failure_receipt.json")
        write_json(attempt / "authorization.staging.json", {"status": "PARTIAL"})
        staging = rejected(
            gate.require_successful_authorization_attempt,
            expected, authorization_sha, tool_sha, authorization_identity,
        )
        os.unlink(attempt / "authorization.staging.json")
        write_json(gate.AUTHORIZATION_ATTEMPT_RECEIPT,
                   dict(success, unexpected_success_field=True))
        exact_shape = rejected(
            gate.require_successful_authorization_attempt,
            expected, authorization_sha, tool_sha, authorization_identity,
        )
        write_json(gate.AUTHORIZATION_ATTEMPT_RECEIPT,
                   dict(success, terminal_success=False))
        terminal_flag = rejected(
            gate.require_successful_authorization_attempt,
            expected, authorization_sha, tool_sha, authorization_identity,
        )
        return {
            "success_failure_coexistence": coexistence,
            "staging_coexistence": staging,
            "unexpected_success_field": exact_shape,
            "terminal_success_false": terminal_flag,
        }
    finally:
        for name, value in original.items():
            setattr(gate, name, value)


def synthetic_runtime_journal_probe(runtime, scratch):
    output = scratch / "runtime-output"
    output.mkdir()
    original_output = runtime.gate_api.C2_OUTPUT
    original_dup = runtime.gate_api.duplicate_output_dirfd
    original_validate = runtime.gate_api.validate_gate
    original_state = dict(runtime._RUNTIME_JOURNAL)
    try:
        runtime.gate_api.C2_OUTPUT = output
        runtime.gate_api.duplicate_output_dirfd = lambda gate: os.open(
            output, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        )
        runtime.gate_api.validate_gate = lambda gate: gate
        runtime._RUNTIME_JOURNAL.update(count=0, last=None, terminal=False)
        receipt = output / "runtime_loading.json"
        runtime.atomic_save_runtime_receipt(
            receipt, {"status": "LOADING_C2_DECLARED_COMPONENT_VARIANT"}, output, {}
        )
        runtime.atomic_save_runtime_receipt(
            receipt, {"status": "PASS_S47_C2_DECLARED_VARIANT_COMPONENT_LOADING_ONLY"},
            output, {},
        )
        terminal = receipt.read_bytes()
        post_terminal_rejected = rejected(
            runtime.atomic_save_runtime_receipt,
            receipt, {"status": "FAILED_AFTER_TERMINAL"}, output, {},
        )
        require(
            receipt.read_bytes() == terminal
            and sorted(path.name for path in output.iterdir())
            == ["runtime_loading.event_0001.json", "runtime_loading.event_0002.json",
                "runtime_loading.json"],
            "Create-only runtime journal did not preserve its terminal inode",
        )
        return post_terminal_rejected
    finally:
        runtime.gate_api.C2_OUTPUT = original_output
        runtime.gate_api.duplicate_output_dirfd = original_dup
        runtime.gate_api.validate_gate = original_validate
        runtime._RUNTIME_JOURNAL.clear()
        runtime._RUNTIME_JOURNAL.update(original_state)


def resource_consumption_seal_probe(gate):
    required = {
        "config", "input_image", "vmem", "cut3r", "clip",
        "vae_config", "vae_weight",
    }
    session = object.__new__(gate.ResourceSession)
    session.closed = False
    session.sealed = False
    session.resources = {name: None for name in required}
    session.consumption_counts = {name: 0 for name in required}
    session.validate = lambda: {}
    session.summary = lambda: {
        "all_required_resources_consumed": all(
            value >= 1 for value in session.consumption_counts.values()
        )
    }
    incomplete = rejected(session.seal, require_complete=True)
    session.consumption_counts = {name: 1 for name in required}
    complete = session.seal(require_complete=True)
    duplicate_after_seal = rejected(session.duplicate, "config")
    require(complete["all_required_resources_consumed"] is True,
            "Complete seven-resource seal was rejected")
    return {
        "incomplete_success_rejected": incomplete,
        "all_seven_consumed": complete["all_required_resources_consumed"],
        "post_seal_duplicate_rejected": duplicate_after_seal,
    }


def inherited_output_inode_probe(gate, scratch):
    output = scratch / "held-output"
    output.mkdir()
    opened = gate.DirectoryBinding.open(output)
    duplicated = []
    try:
        for path, descriptor, device, inode in opened.chain:
            duplicate = os.dup(descriptor)
            os.set_inheritable(duplicate, False)
            duplicated.append((str(path), duplicate, device, inode))
        identity = dict(opened.identity)
    finally:
        opened.close()
    adopted = gate.DirectoryBinding.adopt(output, duplicated, identity)
    adopted.validate()
    moved = scratch / "held-output.original"
    os.rename(output, moved)
    output.mkdir()
    try:
        swapped = rejected(adopted.validate)
    finally:
        adopted.close()
    require(swapped, "Inherited output directory did not reject a path/inode swap")
    return swapped


def worker_ticket_topology_probe(launcher):
    supervisor_pid = os.getppid() + 1000000
    direct_parent_pid = os.getppid()
    worker_pid = os.getpid()
    output_identity = {"device": 11, "inode": 22}
    execution_identity = {"device": 33, "inode": 44}
    ticket = {
        "schema": "s47-c2-worker-launch-ticket-v2",
        "status": "BOUND_AFTER_WATCHDOG_OWNERSHIP",
        "supervisor_pid": supervisor_pid,
        "watchdog_pid": direct_parent_pid,
        "worker_pid": worker_pid,
        "manifest_sha256": "a" * 64,
        "launcher_sha256": "b" * 64,
        "output_root": "/synthetic/output",
        "output_identity": output_identity,
        "execution_identity": execution_identity,
        "parent_requested_utc": "2026-09-08T00:00:00+00:00",
        "created_utc": "2026-09-08T00:00:01+00:00",
        "direct_worker_parent": "WATCHDOG_PID",
    }
    legacy = launcher.translate_worker_ticket(
        ticket,
        manifest_sha256="a" * 64,
        launcher_sha256="b" * 64,
        supervisor_pid=supervisor_pid,
        direct_parent_pid=direct_parent_pid,
        worker_pid=worker_pid,
        output_root="/synthetic/output",
        output_identity=output_identity,
        execution_identity=execution_identity,
    )
    exact_inherited_predicate = (
        legacy["parent_pid"] == os.getppid()
        and legacy["manifest_sha256"] == "a" * 64
        and legacy["launcher_sha256"] == "b" * 64
    )
    wrong_direct_parent_rejected = rejected(
        launcher.translate_worker_ticket,
        ticket,
        manifest_sha256="a" * 64,
        launcher_sha256="b" * 64,
        supervisor_pid=supervisor_pid,
        direct_parent_pid=direct_parent_pid + 1,
        worker_pid=worker_pid,
        output_root="/synthetic/output",
        output_identity=output_identity,
        execution_identity=execution_identity,
    )
    supervisor_as_direct_parent_rejected = rejected(
        launcher.translate_worker_ticket,
        ticket,
        manifest_sha256="a" * 64,
        launcher_sha256="b" * 64,
        supervisor_pid=supervisor_pid,
        direct_parent_pid=supervisor_pid,
        worker_pid=worker_pid,
        output_root="/synthetic/output",
        output_identity=output_identity,
        execution_identity=execution_identity,
    )
    require(
        exact_inherited_predicate
        and wrong_direct_parent_rejected
        and supervisor_as_direct_parent_rejected,
        "V6 worker ticket does not close the inherited parent-PID predicate",
    )
    return {
        "separate_supervisor_watchdog_worker_ids": True,
        "legacy_parent_pid_equals_actual_direct_parent": exact_inherited_predicate,
        "wrong_direct_parent_rejected": wrong_direct_parent_rejected,
        "supervisor_cannot_impersonate_direct_parent": supervisor_as_direct_parent_rejected,
    }


def terminal_commit_failure_probe(launcher, scratch):
    fsync_root = scratch / "terminal-fsync-root"
    fsync_root.mkdir()
    fsync_execution = fsync_root / "execution_01"
    fsync_execution.mkdir()
    held_root = launcher.HeldDirectory.open(fsync_root)
    held_execution = launcher.HeldDirectory.open(fsync_execution)
    candidate = None
    original_fsync = launcher.os.fsync
    try:
        launcher.write_new_json_at(
            held_execution.fd,
            launcher.SUPERVISOR_PROVISIONAL,
            {"status": "PENDING_NOT_A_SUCCESS_RECORD", "standalone_success": False},
        )
        candidate = launcher.HeldCreatedJSON.create(
            held_execution.fd,
            launcher.SUPERVISOR_COMMIT,
            {
                "status": "COMMIT_CANDIDATE_REQUIRES_OUTER_RETURN_AND_NO_ROOT_FAILURE",
                "standalone_success": False,
            },
        )

        def fail_execution_directory_fsync(descriptor):
            if descriptor == held_execution.fd:
                raise OSError("synthetic post-file directory fsync failure")
            return original_fsync(descriptor)

        launcher.os.fsync = fail_execution_directory_fsync
        directory_sync_rejected = rejected(candidate.sync_directory)
        launcher.os.fsync = original_fsync
        launcher.write_new_json_at(
            held_root.fd,
            launcher.SUPERVISOR_FAILURE_FALLBACK,
            {
                "status": "SUPERVISOR_TERMINAL_COMMIT_NOT_ACCEPTED",
                "terminal_commit_may_exist": True,
                "terminal_commit_is_standalone_success": False,
            },
        )
        body = json.loads(
            (fsync_execution / launcher.SUPERVISOR_COMMIT).read_text(encoding="utf-8")
        )
        fsync_fail_closed = (
            directory_sync_rejected
            and body["standalone_success"] is False
            and (fsync_root / launcher.SUPERVISOR_FAILURE_FALLBACK).is_file()
        )
    finally:
        launcher.os.fsync = original_fsync
        if candidate is not None:
            candidate.close()
        held_execution.close()
        held_root.close()

    swap_root = scratch / "terminal-swap-root"
    swap_root.mkdir()
    swap_execution = swap_root / "execution_01"
    swap_execution.mkdir()
    held_root = launcher.HeldDirectory.open(swap_root)
    held_execution = launcher.HeldDirectory.open(swap_execution)
    candidate = launcher.HeldCreatedJSON.create(
        held_execution.fd,
        launcher.SUPERVISOR_COMMIT,
        {
            "status": "COMMIT_CANDIDATE_REQUIRES_OUTER_RETURN_AND_NO_ROOT_FAILURE",
            "standalone_success": False,
        },
    )
    candidate.sync_directory()
    moved = swap_root / "execution_01.moved"
    os.rename(swap_execution, moved)
    swap_execution.mkdir()
    post_commit_path_validation_rejected = rejected(held_execution.validate)
    launcher.write_new_json_at(
        held_root.fd,
        launcher.SUPERVISOR_FAILURE_FALLBACK,
        {
            "status": "SUPERVISOR_TERMINAL_COMMIT_NOT_ACCEPTED",
            "terminal_commit_may_exist": True,
            "terminal_commit_is_standalone_success": False,
        },
    )
    candidate.validate()
    path_swap_fail_closed = (
        post_commit_path_validation_rejected
        and (moved / launcher.SUPERVISOR_COMMIT).is_file()
        and not (swap_execution / launcher.SUPERVISOR_COMMIT).exists()
        and (swap_root / launcher.SUPERVISOR_FAILURE_FALLBACK).is_file()
    )
    candidate.close()
    held_execution.close()
    held_root.close()
    require(fsync_fail_closed and path_swap_fail_closed,
            "Terminal commit fault or canonical-path swap did not fail closed")
    return {
        "post_file_pre_directory_fsync_fault_has_root_failure": fsync_fail_closed,
        "commit_body_never_standalone_success": True,
        "post_commit_canonical_path_swap_has_root_failure": path_swap_fail_closed,
        "commit_fd_held_through_post_write_validation": True,
    }


def pid_gone(pid, timeout=6.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        time.sleep(0.02)
    return False


def watchdog_monitor_death_probe(launcher, scratch, *, monitor_signal, after_marker,
                                 descendant_timing):
    require(descendant_timing in {None, "pre_registered", "late_registered"},
            "Unknown synthetic descendant timing")
    label = "%d-%d-%s" % (monitor_signal, after_marker, descendant_timing or "none")
    root = scratch / ("watchdog-root-" + label)
    root.mkdir()
    execution = root / "execution_01"
    execution.mkdir()
    output = root / "output"
    output.mkdir()
    identity_path = execution / "synthetic_worker_identity.json"
    marker_path = execution / "capability_consumed.marker"
    registry_path = execution / "synthetic_process_registry.jsonl"
    info_read, info_write = os.pipe()
    original_execution = launcher.EXECUTION
    launcher.EXECUTION = execution
    monitor_pid = os.fork()
    if monitor_pid == 0:
        try:
            os.close(info_read)
            life_read, life_write = os.pipe()
            ack_read, ack_write = os.pipe()
            status_read, status_write = os.pipe()
            watchdog_pid = os.fork()
            if watchdog_pid == 0:
                worker_pid = None
                try:
                    for descriptor in (life_write, ack_read, status_read):
                        os.close(descriptor)
                    os.setsid()
                    group_read, group_write = os.pipe()
                    worker_pid = os.fork()
                    if worker_pid == 0:
                        os.close(group_read)
                        for descriptor in (life_read, ack_write, status_write, info_write):
                            os.close(descriptor)
                        os.setsid()
                        owned_worker_pid = os.getpid()
                        register_synthetic_process(
                            registry_path, owned_worker_pid, os.getppid()
                        )
                        os.write(group_write, b"G")
                        os.close(group_write)
                        descendant_pid = None
                        if descendant_timing is not None:
                            descendant_pid = os.fork()
                            if descendant_pid == 0:
                                os.setsid()
                                for descriptor in (0, 1, 2):
                                    try:
                                        os.close(descriptor)
                                    except OSError:
                                        pass
                                if descendant_timing == "late_registered":
                                    time.sleep(0.15)
                                    register_synthetic_process(
                                        registry_path, os.getpid(), owned_worker_pid
                                    )
                                while True:
                                    time.sleep(1)
                            if descendant_timing == "pre_registered":
                                register_synthetic_process(
                                    registry_path, descendant_pid, os.getpid()
                                )
                        write_json(identity_path, {
                            "worker_pid": os.getpid(),
                            "descendant_pid": descendant_pid,
                        })
                        if after_marker:
                            marker_path.write_text("yes")
                        while True:
                            time.sleep(1)
                    os.close(group_write)
                    require(os.read(group_read, 1) == b"G",
                            "Synthetic worker did not establish its session")
                    os.close(group_read)
                    execution_fd = os.open(
                        execution, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
                    )
                    here_fd = os.open(
                        root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
                    )
                    execution_stat = os.fstat(execution_fd)
                    output_stat = os.stat(output, follow_symlinks=False)
                    info = json.dumps({
                        "worker": worker_pid, "watchdog": os.getpid()
                    }, sort_keys=True).encode() + b"\n"
                    os.write(info_write, info)
                    os.close(info_write)
                    launcher._watchdog_loop(
                        life_read, ack_write, status_write, worker_pid,
                        execution_fd, here_fd,
                        {
                            "supervisor_pid": os.getppid(),
                            "manifest_sha256": "a" * 64,
                            "launcher_sha256": "b" * 64,
                            "execution_identity": {
                                "device": execution_stat.st_dev,
                                "inode": execution_stat.st_ino,
                            },
                            "output_root": str(output),
                            "output_identity": {
                                "device": output_stat.st_dev,
                                "inode": output_stat.st_ino,
                            },
                        }, SyntheticProcessAPI(registry_path),
                    )
                except BaseException:
                    try:
                        if worker_pid:
                            launcher._terminate_and_reap_owned_group(
                                worker_pid,
                                process_api=SyntheticProcessAPI(registry_path),
                                descendant_ledger={},
                            )
                    except BaseException:
                        pass
                    os._exit(7)
            for descriptor in (life_read, ack_read, ack_write, status_read,
                               status_write, info_write):
                os.close(descriptor)
            while True:
                time.sleep(1)
        finally:
            os._exit(0)
    os.close(info_write)
    try:
        buffer = b""
        deadline = time.monotonic() + 5
        while b"\n" not in buffer and time.monotonic() < deadline:
            readable, _, _ = select.select([info_read], [], [], 0.1)
            if readable:
                chunk = os.read(info_read, 1024)
                require(chunk, "Synthetic watchdog closed before identity publication")
                buffer += chunk
        require(b"\n" in buffer, "Synthetic watchdog identity publication timed out")
        info_line, remainder = buffer.split(b"\n", 1)
        require(not remainder, "Synthetic watchdog identity had trailing bytes")
        info = json.loads(info_line)
        deadline = time.monotonic() + 5
        while not identity_path.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        require(identity_path.exists(), "Synthetic worker identity was never published")
        identities = json.loads(identity_path.read_text())
        require(identities["worker_pid"] == info["worker"],
                "Synthetic watchdog did not own the reported worker")
        if identities["descendant_pid"] is not None:
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                registered = SyntheticProcessAPI(registry_path)._records()
                if identities["descendant_pid"] in registered:
                    break
                time.sleep(0.01)
            require(identities["descendant_pid"] in registered,
                    "Synthetic detached descendant was never registered")
        if after_marker:
            deadline = time.monotonic() + 5
            while not marker_path.exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            require(marker_path.exists(), "Requested post-consumption death point was not reached")
        os.kill(monitor_pid, monitor_signal)
        os.waitpid(monitor_pid, 0)
        receipt_path = execution / launcher.WATCHDOG_RECEIPT
        deadline = time.monotonic() + 8
        while not receipt_path.exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        require(receipt_path.exists(), "Watchdog left no external cleanup receipt")
        receipt = json.loads(receipt_path.read_text())
        all_pids = [identities["worker_pid"]]
        if identities["descendant_pid"] is not None:
            all_pids.append(identities["descendant_pid"])
        gone = {str(pid): pid_gone(pid) for pid in all_pids}
        require(
            receipt["status"]
            == "SUPERVISOR_LOST_REGISTERED_DESCENDANTS_TERMINATED"
            and receipt["cleanup_complete"] is True
            and receipt["all_registered_descendants_gone"] is True
            and receipt["supervisor_completed_protocol"] is False
            and receipt["supervisor_liveness_lost"] is True
            and receipt["worker_pid"] == identities["worker_pid"]
            and all(gone.values()),
            "Watchdog did not fail closed and remove every owned process",
        )
        ledger_pids = {
            item["pid"] for item in receipt["descendant_identity_ledger"]
        }
        require(set(all_pids) <= ledger_pids,
                "Watchdog receipt omitted a registered descendant identity")
        return {
            "status": receipt["status"],
            "descendant_timing": descendant_timing,
            "detached_descendant_closed_stdio": descendant_timing is not None,
            "all_reported_pids_gone": gone,
            "ledger_pids": sorted(ledger_pids),
        }
    finally:
        launcher.EXECUTION = original_execution
        try:
            os.close(info_read)
        except OSError:
            pass
        try:
            os.kill(monitor_pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            os.waitpid(monitor_pid, 0)
        except ChildProcessError:
            pass


def main():
    require(sys.version_info[:2] in {(3, 12), (3, 13)},
            "V6 self-test requires reviewed Python 3.12 or 3.13")
    require(all(not os.path.lexists(path) for path in FORMAL_PATHS),
            "A formal C2 path exists; source-only self-test refuses to run")
    parsed = {path.name: ast.parse(path.read_bytes(), filename=str(path))
              for path in PYTHON_SOURCES}
    for path in PYTHON_SOURCES:
        text = path.read_text()
        if path.name != "static_selftest.py":
            require("seed: 43" not in text and "S44" not in text,
                    "Stale row or seed label in " + path.name)

    launcher_tree = parsed["launch_generation.py"]
    launcher_top = {node.name for node in launcher_tree.body if isinstance(node, ast.FunctionDef)}
    supervisor = top_function(launcher_tree, "_run_supervisor")
    nested = nested_names(supervisor)
    launcher_text = ast.unparse(launcher_tree)
    consume = next(node for node in ast.walk(supervisor)
                   if isinstance(node, ast.FunctionDef) and node.name == "consume_capability")
    derive = top_function(launcher_tree, "derive_launcher")
    derive_arguments = {
        item.arg for item in (
            list(derive.args.args) + list(derive.args.kwonlyargs)
        )
    }
    capability_route_static = (
        "spawn_capability_worker" not in launcher_top
        and "consume_worker_capability" not in launcher_top
        and {"spawn_worker", "consume_capability", "guarded_worker"} <= nested
        and derive_arguments == {"compile_only"}
        and "_return_code" not in launcher_text
        and "secrets.token_bytes(32)" in ast.unparse(supervisor)
        and "_watchdog_loop" in launcher_top
        and "_terminate_and_reap_owned_group" in launcher_top
        and "worker_pid = os.fork()" in ast.unparse(supervisor)
        and "ForkWorkerProcess(worker_pid, watchdog_pid, status_read)" in ast.unparse(supervisor)
        and "SUPERVISOR_LOST_REGISTERED_DESCENDANTS_TERMINATED" in launcher_text
        and "_refresh_descendant_ledger" in launcher_top
        and "_all_registered_gone" in launcher_top
        and "translate_worker_ticket" in launcher_top
        and "BOUND_AFTER_WATCHDOG_OWNERSHIP" in launcher_text
        and "COMMIT_CANDIDATE_REQUIRES_OUTER_RETURN_AND_NO_ROOT_FAILURE" in launcher_text
        and "SUPERVISOR_TERMINAL_COMMIT_NOT_ACCEPTED" in launcher_text
        and "output_root" in ast.unparse(consume)
        and "output_identity" in ast.unparse(consume)
        and "record.get('watchdog_pid') == os.getppid()" in ast.unparse(consume)
    )
    require(capability_route_static,
            "Unique monitored capability route or watchdog binding is incomplete")
    freeze_text = ast.unparse(parsed["freeze_c2_manifest.py"])
    gate_text = ast.unparse(parsed["generation_gate.py"])
    runtime_text = ast.unparse(parsed["runtime_adapter.py"])
    authorization_text = ast.unparse(parsed["create_launch_authorization.py"])
    prepare_authorization_static = (
        "require_successful_prepare_bundle" in freeze_text
        and "prepare_receipt_sha256" in freeze_text
        and "directory.entries() == {'manifest_core.json', 'receipt.json'}" in gate_text
        and "attempt_directory.entries() == {'attempt_started.json', 'success_receipt.json'}" in gate_text
        and "set(receipt) ==" in gate_text
        and "set(lease) ==" in gate_text
        and "terminal_success" in gate_text
    )
    require(prepare_authorization_static,
            "Prepare or authorization success-only terminal verifier is incomplete")
    persistent_directory_static = (
        "renameatx_np" in freeze_text and "renameatx_np" in authorization_text
        and "DirectoryLease" in freeze_text and "DirectoryLease" in authorization_text
        and ".freeze_attempt_01.claimed" in freeze_text
        and ".review_attachment_01.claimed" in freeze_text
    )
    require(persistent_directory_static,
            "Persistent directory leases or outer attempt sentinels are incomplete")
    scientific_descriptor_static = (
        "duplicate_resource_fd" in runtime_text
        and "load_verified_config" in runtime_text
        and "load_verified_input" in runtime_text
        and "bound_safetensors_load_file" in runtime_text
        and "bound_io_open" in runtime_text
        and "under_vae" in runtime_text
        and "patch.object(os, 'listdir', bound_listdir)" in runtime_text
        and "patch.object(Path, 'is_file', bound_path_is_file)" in runtime_text
        and "os.replace" not in runtime_text
        and ".runtime_loading.s47-c2.tmp" not in runtime_text
        and "runtime_loading.event_%04d.json" in runtime_text
    )
    require(scientific_descriptor_static,
            "Scientific same-FD loading or create-only runtime journal is incomplete")
    require(
        "RegularBinding(AUTHORIZATION_ATTEMPT_STARTED, None" in gate_text
        and "RegularBinding(AUTHORIZATION_ATTEMPT_RECEIPT, None" in gate_text
        and "authorization_identity" in gate_text
        and "all_required_resources_consumed" in gate_text
        and "require_complete" in gate_text,
        "Same-FD authorization identity or seven-resource terminal seal is incomplete",
    )

    blocker = DenyScientificImports()
    sys.meta_path.insert(0, blocker)
    try:
        gate = load_module_snapshot("generation_gate", HERE / "generation_gate.py")
        runtime = load_module_snapshot("_s47_runtime_v6_static", HERE / "runtime_adapter.py")
        launcher = load_module_snapshot("_s47_launcher_v6_static", HERE / "launch_generation.py")
        freeze = load_module_snapshot("_s47_freeze_v6_static", HERE / "freeze_c2_manifest.py")
        authorization = load_module_snapshot(
            "_s47_authorization_v6_static", HERE / "create_launch_authorization.py"
        )
        require(gate.C2_PROTOCOL_SHA256 == sha(HERE / "PROTOCOL.md")
                and gate.FREEZE_PROTOCOL_SHA256 == sha(HERE / "FREEZE_PROTOCOL.md"),
                "Gate protocol pins differ")
        require(freeze.FREEZE_PROTOCOL_SHA256 == sha(HERE / "FREEZE_PROTOCOL.md"),
                "Freeze protocol pin differs")
        require(launcher.GATE_SHA256 == sha(HERE / "generation_gate.py")
                and authorization.GATE_SHA256 == sha(HERE / "generation_gate.py"),
                "Launcher or authorization gate pin differs")
        require(freeze.SOURCE_HASHES == {
            name: sha(HERE / name) for name in (
                "generation_gate.py", "runtime_adapter.py", "launch_generation.py",
                "create_launch_authorization.py", "PROTOCOL.md",
            )
        }, "Freeze transitive source pins differ")
        require(len(gate.required_sources()) == 219, "C2 source-domain count changed")

        launcher_proof = launcher.derive_launcher(compile_only=True)
        runtime_proof = runtime.derive_factory(compile_only=True)
        require(
            launcher_proof["reversible_full_AST_equal"] is True
            and launcher_proof["security_hardening_counts"] == {
                "capability_spawn": 1, "execution_adoption": 1, "output_claim": 1,
                "worker_ticket_snapshot": 1, "worker_receipt_snapshot": 1,
                "worker_receipt_bound_digest": 1,
            }
            and rejected(launcher.derive_launcher)
            and runtime_proof["reversible_full_AST_equal"] is True
            and runtime_proof["same_fd_config_loader_sites"] == 1
            and runtime_proof["same_fd_torch_loader_sites"] == 1
            and runtime_proof["same_fd_loader_patch_sites"] == 1
            and runtime_proof["same_fd_input_loader_sites"] == 1,
            "Reversible V6 derivation or namespace-closure proof failed",
        )

        public = ["--manifest", str(launcher.PUBLISHED_MANIFEST),
                  "--manifest-sha256", "a" * 64,
                  "--execution-directory", str(launcher.EXECUTION)]
        cli_negative = {
            "alternate_execution": public[:-1] + [str(HERE / "execution_02")],
            "repeated": public + ["--execution-directory", str(launcher.EXECUTION)],
            "split_equal": public + ["--manifest-sha256=" + "a" * 64],
            "equal_only": ["--manifest=" + str(launcher.PUBLISHED_MANIFEST)] + public[2:],
            "abbreviation": public[:-2] + ["--execution-dir", str(launcher.EXECUTION)],
            "worker": ["--worker"] + public,
            "unknown": public + ["--extra", "x"],
            "double_dash": ["--"] + public,
        }
        require(launcher.parse_exact_arguments(public, internal=False).worker is False,
                "Canonical public launch vector failed")
        for vector in cli_negative.values():
            require(rejected(launcher.parse_exact_arguments, vector, internal=False),
                    "Unsafe CLI vector passed")

        with tempfile.TemporaryDirectory(prefix="s47-c2-v6-static-") as temporary:
            scratch = Path(temporary).resolve()
            real = scratch / "real"; real.mkdir()
            nested_dir = real / "nested"; nested_dir.mkdir()
            os.symlink(real, scratch / "linked")
            ancestor_symlink_rejected = rejected(
                gate.DirectoryBinding.open, scratch / "linked" / "nested"
            )
            payload_path = nested_dir / "payload.bin"
            payload_path.write_bytes(b"approved")
            binding = gate.RegularBinding(payload_path, sha(payload_path), "synthetic payload")
            moved = nested_dir / "approved.opened"
            os.rename(payload_path, moved)
            payload_path.write_bytes(b"replacement")
            duplicate = os.dup(binding.fd); os.lseek(duplicate, 0, os.SEEK_SET)
            held_bytes = os.read(duplicate, 1024); os.close(duplicate)
            path_swap_rejected = rejected(binding.validate)
            binding.close()
            require(held_bytes == b"approved" and path_swap_rejected,
                    "Same-FD resource did not retain and detect path replacement")

            prepare_conflict_rejected = synthetic_prepare_terminal_probe(gate, scratch)
            authorization_conflict_rejected = synthetic_authorization_terminal_probe(gate, scratch)
            runtime_terminal_preserved = synthetic_runtime_journal_probe(runtime, scratch)
            resource_consumption = resource_consumption_seal_probe(gate)
            inherited_output_swap_rejected = inherited_output_inode_probe(gate, scratch)
            worker_ticket_topology = worker_ticket_topology_probe(launcher)
            terminal_commit_faults = terminal_commit_failure_probe(launcher, scratch)
            watchdog_results = {
                "sigkill_before_consume": watchdog_monitor_death_probe(
                    launcher, scratch, monitor_signal=signal.SIGKILL,
                    after_marker=False, descendant_timing=None),
                "sigkill_after_consume": watchdog_monitor_death_probe(
                    launcher, scratch, monitor_signal=signal.SIGKILL,
                    after_marker=True, descendant_timing=None),
                "sigterm_after_consume": watchdog_monitor_death_probe(
                    launcher, scratch, monitor_signal=signal.SIGTERM,
                    after_marker=True, descendant_timing=None),
                "sigkill_pre_registered_setsid_closed_stdio_descendant": watchdog_monitor_death_probe(
                    launcher, scratch, monitor_signal=signal.SIGKILL,
                    after_marker=True, descendant_timing="pre_registered"),
                "sigkill_late_registered_setsid_closed_stdio_descendant": watchdog_monitor_death_probe(
                    launcher, scratch, monitor_signal=signal.SIGKILL,
                    after_marker=True, descendant_timing="late_registered"),
            }
    finally:
        sys.meta_path.remove(blocker)

    scientific_loaded = sorted(name for name in sys.modules if any(
        name == prefix or name.startswith(prefix + ".") for prefix in SCIENTIFIC_PREFIXES
    ))
    require(scientific_loaded == [], "Scientific modules were imported: " + repr(scientific_loaded))
    require(all(not os.path.lexists(path) for path in FORMAL_PATHS),
            "V6 source-only self-test created a formal C2 path")
    require(sha(HERE / "SOURCE_REVIEW_ADVERSARIAL_V4.json")
            == "03e19676a6a1ea1810bfd199628ad4504c3f59ee48542da7bdfc13f09a0f0cb1"
            and sha(HERE / "SOURCE_REVIEW_PRIMARY_V4.json")
            == "0036acc53dfde7ff1a9a5f8ead7db01df80f53b84e44476c306bc2ca3d38167c",
            "Exact V4 blocked review history changed")

    result = {
        "status": "PASS_S47_C2_V6_CANDIDATE_STATIC_SELFTEST",
        "python": {"version": ".".join(str(value) for value in sys.version_info[:3]),
                   "executable": sys.executable, "isolated": sys.flags.isolated == 1,
                   "dont_write_bytecode": sys.dont_write_bytecode,
                   "no_site": sys.flags.no_site == 1},
        "scope": "standard-library AST and disposable adversarial process/filesystem checks only",
        "row": "C2", "seed": 44, "source_count": 219,
        "formal_gate_calls": 0, "prepare_calls": 0, "attach_calls": 0,
        "authorization_main_calls": 0, "launcher_main_calls": 0,
        "production_worker_calls": 0, "model_or_scientific_imports": 0,
        "generation_calls": 0, "input_image_body_bytes_read": 0,
        "pixels_decoded": 0, "formal_paths_created": 0,
        "checks": {
            "launcher_full_ast_reversible": True,
            "runtime_full_ast_reversible": True,
            "module_level_capability_minter_absent": capability_route_static,
            "runtime_namespace_not_returned": derive_arguments == {"compile_only"},
            "capability_output_root_and_inode_bound": (
                "output_root" in ast.unparse(consume)
                and "output_identity" in ast.unparse(consume)
            ),
            "cli_negative_cases": sorted(cli_negative),
            "ancestor_symlink_rejected": ancestor_symlink_rejected,
            "same_fd_path_swap_rejected": path_swap_rejected,
            "prepare_terminal_negative_matrix": prepare_conflict_rejected,
            "authorization_terminal_negative_matrix": authorization_conflict_rejected,
            "runtime_create_only_terminal_preserved": runtime_terminal_preserved,
            "seven_resource_consumption_seal": resource_consumption,
            "inherited_output_inode_swap_rejected": inherited_output_swap_rejected,
            "three_process_ticket_topology": worker_ticket_topology,
            "terminal_commit_fault_matrix": terminal_commit_faults,
            "watchdog_monitor_death_matrix": watchdog_results,
            "persistent_freeze_auth_execution_directory_fds": persistent_directory_static,
            "scientific_payload_path_reopens_in_candidate_route": (
                0 if scientific_descriptor_static else None
            ),
        },
        "candidate_sha256": {path.name: sha(path) for path in PRODUCTION},
        "static_selftest_sha256": sha(HERE / "static_selftest.py"),
        "withdrawn_v5": {
            "candidate_receipt_sha256": sha(HERE / "CANDIDATE_STATIC_SELFTEST_V5.json"),
            "primary_blocked_review_sha256": sha(HERE / "SOURCE_REVIEW_PRIMARY_V5.json"),
            "review_probe_sha256": sha(HERE / "SOURCE_REVIEW_PRIMARY_V5_PROBE.py"),
            "authority_for_v6": "NONE"},
        "formal_lexists": {str(path): os.path.lexists(path) for path in FORMAL_PATHS},
        "next_gate": "TWO_FRESH_DIFFERENT_AUTHOR_EXACT_V6_SOURCE_REVIEWS_BEFORE_UNIQUE_PREPARE",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
