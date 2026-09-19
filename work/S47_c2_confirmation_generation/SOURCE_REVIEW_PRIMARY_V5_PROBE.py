#!/usr/bin/env python3
"""Primary-review-only V5 probes; no formal C2 path, payload, or model access."""
from __future__ import annotations

import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import time
from types import ModuleType


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LAUNCHER = HERE / "launch_generation.py"
LAUNCHER_SHA256 = "e9279dc9233463f2e4dec5c98b65893647b1a5e7197b0c40afb23aeb04a8730b"
PARENT = ROOT / "work/S35_generation_integration/launch_original.py"
PARENT_SHA256 = "8744cb8959cded2394c1471c660dd84f929b5ae24ac97e81379304aed0be702e"
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
    HERE / "execution_01",
    ROOT / "results/S47_C2_confirmation_generation",
)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha256(payload):
    return hashlib.sha256(payload).hexdigest()


def pid_exists(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def wait_pid_gone(pid, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not pid_exists(pid):
            return True
        time.sleep(0.02)
    return not pid_exists(pid)


def load_launcher(payload):
    module = ModuleType("_s47_c2_v5_primary_probe_launcher")
    module.__file__ = str(LAUNCHER)
    module.__package__ = ""
    sys.modules[module.__name__] = module
    exec(compile(payload, str(LAUNCHER), "exec", dont_inherit=True), module.__dict__)
    return module


def static_parent_binding_probe(launcher_payload, parent_payload):
    launcher_tree = ast.parse(launcher_payload, filename=str(LAUNCHER))
    parent_tree = ast.parse(parent_payload, filename=str(PARENT))
    parent_worker = next(
        node for node in parent_tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "worker"
    )
    supervisor = next(
        node for node in launcher_tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_run_supervisor"
    )
    route = next(
        node for node in ast.walk(launcher_tree)
        if isinstance(node, ast.ClassDef) and node.name == "Route"
    )
    bound_ticket = next(
        node for node in ast.walk(supervisor)
        if isinstance(node, ast.FunctionDef) and node.name == "bound_ticket"
    )
    spawn_worker = next(
        node for node in ast.walk(supervisor)
        if isinstance(node, ast.FunctionDef) and node.name == "spawn_worker"
    )
    worker_text = ast.unparse(parent_worker)
    ticket_text = ast.unparse(bound_ticket)
    spawn_text = ast.unparse(spawn_worker)
    route_methods = {
        node.name for node in route.body if isinstance(node, ast.FunctionDef)
    }
    facts = {
        "inherited_worker_requires_ticket_parent_pid_equal_actual_ppid": (
            "ticket['parent_pid'] == os.getppid()" in worker_text
        ),
        "bound_ticket_requires_ticket_parent_pid_equal_supervisor_pid": (
            "ticket.get('parent_pid') == capability_state['supervisor_pid']" in ticket_text
        ),
        "bound_ticket_returns_unmodified_ticket": "return ticket" in ticket_text,
        "watchdog_forks_worker": (
            "watchdog_pid = os.fork()" in spawn_text
            and "worker_pid = os.fork()" in spawn_text
        ),
        "derivation_has_compare_rewrite": "visit_Compare" in route_methods,
        "legal_supervisor_to_watchdog_parent_pid_transfer_present": False,
    }
    require(
        facts
        == {
            "inherited_worker_requires_ticket_parent_pid_equal_actual_ppid": True,
            "bound_ticket_requires_ticket_parent_pid_equal_supervisor_pid": True,
            "bound_ticket_returns_unmodified_ticket": True,
            "watchdog_forks_worker": True,
            "derivation_has_compare_rewrite": False,
            "legal_supervisor_to_watchdog_parent_pid_transfer_present": False,
        },
        "Expected V5 parent-PID conflict was not reproduced",
    )
    return facts


def setsid_escape_probe(launcher):
    with tempfile.TemporaryDirectory(prefix="s47-v5-primary-escape-") as temporary:
        root = Path(temporary).resolve()
        execution = root / "execution_01"
        output = root / "output"
        execution.mkdir()
        output.mkdir()
        identities_path = root / "identities.json"
        escape_ready = root / "escape_ready"
        original_execution = launcher.EXECUTION
        launcher.EXECUTION = execution
        life_read, life_write = os.pipe()
        ack_read, ack_write = os.pipe()
        status_read, status_write = os.pipe()
        watchdog_pid = os.fork()
        if watchdog_pid == 0:
            worker_pid = None
            try:
                os.close(life_write)
                os.close(ack_read)
                os.close(status_read)
                os.setsid()
                worker_pid = os.fork()
                if worker_pid == 0:
                    os.setsid()
                    escaped_pid = os.fork()
                    if escaped_pid == 0:
                        os.setsid()
                        escape_ready.write_text(str(os.getpid()), encoding="utf-8")
                        for descriptor in (0, 1, 2):
                            try:
                                os.close(descriptor)
                            except OSError:
                                pass
                        while True:
                            time.sleep(1)
                    identities_path.write_text(
                        json.dumps({"worker_pid": os.getpid(), "escaped_pid": escaped_pid}),
                        encoding="utf-8",
                    )
                    while True:
                        time.sleep(1)
                execution_fd = os.open(
                    execution, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
                )
                here_fd = os.open(root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
                execution_stat = os.fstat(execution_fd)
                output_stat = os.stat(output, follow_symlinks=False)
                launcher._watchdog_loop(
                    life_read,
                    ack_write,
                    status_write,
                    worker_pid,
                    execution_fd,
                    here_fd,
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
                    },
                )
            except BaseException:
                if worker_pid is not None:
                    try:
                        os.killpg(worker_pid, signal.SIGKILL)
                    except OSError:
                        pass
                os._exit(9)
        os.close(life_read)
        os.close(ack_write)
        os.close(status_write)
        escaped_pid = None
        try:
            deadline = time.monotonic() + 5
            while (
                (not identities_path.exists() or not escape_ready.exists())
                and time.monotonic() < deadline
            ):
                time.sleep(0.01)
            require(identities_path.exists() and escape_ready.exists(),
                    "Escaped-descendant fixture did not become ready")
            identities = json.loads(identities_path.read_text(encoding="utf-8"))
            escaped_pid = identities["escaped_pid"]
            os.close(life_write)
            life_write = None
            receipt_path = execution / launcher.WATCHDOG_RECEIPT
            deadline = time.monotonic() + 8
            while not receipt_path.exists() and time.monotonic() < deadline:
                time.sleep(0.02)
            require(receipt_path.exists(), "Candidate watchdog left no receipt")
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            _, raw_status = os.waitpid(watchdog_pid, 0)
            watchdog_exit = os.waitstatus_to_exitcode(raw_status)
            escaped_alive = pid_exists(escaped_pid)
            result = {
                "worker_pid": identities["worker_pid"],
                "escaped_pid": escaped_pid,
                "escaped_descendant_called_setsid": True,
                "escaped_descendant_closed_stdio_0_1_2": True,
                "watchdog_exit": watchdog_exit,
                "watchdog_ack": os.read(ack_read, 8).decode("ascii", errors="replace"),
                "worker_status_relay": os.read(status_read, 128).decode(
                    "ascii", errors="replace"
                ),
                "watchdog_status": receipt.get("status"),
                "watchdog_cleanup_complete_claim": receipt.get("cleanup_complete"),
                "escaped_pid_alive_after_watchdog_terminal_receipt": escaped_alive,
            }
            require(
                watchdog_exit == 0
                and result["watchdog_ack"] == "1"
                and result["watchdog_cleanup_complete_claim"] is True
                and escaped_alive,
                "Expected V5 setsid escape was not reproduced",
            )
            return result
        finally:
            if life_write is not None:
                try:
                    os.close(life_write)
                except OSError:
                    pass
            if escaped_pid is not None and pid_exists(escaped_pid):
                try:
                    os.kill(escaped_pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            cleanup_gone = True if escaped_pid is None else wait_pid_gone(escaped_pid)
            launcher.EXECUTION = original_execution
            for descriptor in (ack_read, status_read):
                try:
                    os.close(descriptor)
                except OSError:
                    pass
            if "result" in locals():
                result["reviewer_cleanup_signal"] = int(signal.SIGKILL)
                result["escaped_pid_gone_after_reviewer_cleanup"] = cleanup_gone


def terminal_and_path_probe(launcher):
    with tempfile.TemporaryDirectory(prefix="s47-v5-primary-terminal-") as temporary:
        root = Path(temporary).resolve()
        execution = root / "execution_01"
        execution.mkdir()
        directory_fd = os.open(
            execution, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        )
        original_fsync = launcher.os.fsync

        def fail_directory_fsync(descriptor):
            if descriptor == directory_fd:
                raise OSError("synthetic directory fsync failure")
            return original_fsync(descriptor)

        launcher.os.fsync = fail_directory_fsync
        raised = None
        try:
            launcher.write_new_json_at(
                directory_fd,
                "supervisor_seal.json",
                {
                    "schema": "synthetic",
                    "status": "SUPERVISOR_SEALED_RUN_PENDING_INDEPENDENT_REVIEW",
                },
            )
        except BaseException as error:
            raised = type(error).__name__ + ": " + str(error)
        finally:
            launcher.os.fsync = original_fsync
        seal = execution / "supervisor_seal.json"
        pass_shaped_left = (
            seal.exists()
            and json.loads(seal.read_text(encoding="utf-8")).get("status")
            == "SUPERVISOR_SEALED_RUN_PENDING_INDEPENDENT_REVIEW"
        )
        os.close(directory_fd)

        held_path = root / "held_execution"
        held_path.mkdir()
        held = launcher.HeldDirectory.open(held_path)
        held.validate()
        moved = root / "held_execution.moved"
        os.rename(held_path, moved)
        held_path.mkdir()
        digest = launcher.write_new_json_at(
            held.fd,
            "supervisor_seal.json",
            {"status": "SUPERVISOR_SEALED_RUN_PENDING_INDEPENDENT_REVIEW"},
        )
        post_validation_rejected = False
        try:
            held.validate()
        except RuntimeError:
            post_validation_rejected = True
        held.close()
        result = {
            "directory_fsync_fault": raised,
            "pass_shaped_seal_left_after_write_helper_failure": pass_shaped_left,
            "path_swap_after_last_validation_write_returned_sha256": digest,
            "seal_written_to_renamed_held_inode": (moved / "supervisor_seal.json").exists(),
            "seal_written_to_canonical_replacement": (
                held_path / "supervisor_seal.json"
            ).exists(),
            "post_write_validation_would_reject": post_validation_rejected,
        }
        require(
            raised == "OSError: synthetic directory fsync failure"
            and pass_shaped_left
            and result["seal_written_to_renamed_held_inode"]
            and not result["seal_written_to_canonical_replacement"]
            and post_validation_rejected,
            "Expected V5 terminal/path gap was not reproduced",
        )
        return result


def main():
    require(sys.version_info[:2] in {(3, 12), (3, 13)},
            "Review probe requires Python 3.12 or 3.13")
    before = {str(path): os.path.lexists(path) for path in FORMAL_PATHS}
    require(not any(before.values()), "Formal C2 state exists; review probe refuses")
    started_utc = datetime.now(timezone.utc).isoformat()
    launcher_payload = LAUNCHER.read_bytes()
    parent_payload = PARENT.read_bytes()
    require(sha256(launcher_payload) == LAUNCHER_SHA256, "V5 launcher changed")
    require(sha256(parent_payload) == PARENT_SHA256, "S35 parent changed")
    launcher = load_launcher(launcher_payload)
    parent_binding = static_parent_binding_probe(launcher_payload, parent_payload)
    escape = setsid_escape_probe(launcher)
    terminal = terminal_and_path_probe(launcher)
    after = {str(path): os.path.lexists(path) for path in FORMAL_PATHS}
    require(before == after and not any(after.values()), "Probe created formal C2 state")
    require(escape["escaped_pid_gone_after_reviewer_cleanup"],
            "Reviewer cleanup did not remove escaped synthetic PID")
    result = {
        "schema": "s47-c2-v5-primary-review-probe-v1",
        "status": "REPRODUCED_BLOCKING_V5_CONTROL_FLOW_AND_TERMINAL_COUNTEREXAMPLES",
        "started_utc": started_utc,
        "completed_utc": datetime.now(timezone.utc).isoformat(),
        "python": {
            "version": ".".join(str(item) for item in sys.version_info[:3]),
            "executable": sys.executable,
            "isolated": sys.flags.isolated == 1,
            "dont_write_bytecode": sys.dont_write_bytecode,
            "no_site": sys.flags.no_site == 1,
        },
        "launcher_sha256": LAUNCHER_SHA256,
        "parent_sha256": PARENT_SHA256,
        "parent_pid_binding": parent_binding,
        "setsid_closed_stdio_escape": escape,
        "terminal_and_path_gaps": terminal,
        "formal_paths_before": before,
        "formal_paths_after": after,
        "formal_gate_calls": 0,
        "prepare_calls": 0,
        "attach_calls": 0,
        "authorization_main_calls": 0,
        "launcher_main_calls": 0,
        "production_worker_calls": 0,
        "model_or_scientific_imports": 0,
        "generation_calls": 0,
        "c2_input_body_bytes_read": 0,
        "component_bodies_read": 0,
        "pixels_decoded": 0,
        "images_opened": 0,
        "formal_paths_created": 0,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
