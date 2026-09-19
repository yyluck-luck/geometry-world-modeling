"""Independent source-only adversarial probes for the exact S47 C2 V6 candidate.

This script never invokes prepare/attach/authorization/launcher main, never opens
the C2 image body, and never imports a model or scientific package.  All process
and filesystem exercises use disposable temporary directories and processes.
"""
from __future__ import annotations

import ast
from datetime import datetime, timezone
import dis
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import tempfile
import time
from types import ModuleType, SimpleNamespace


PROJECT = Path("/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling")
HERE = PROJECT / "work/S47_c2_confirmation_generation"
EXPECTED = {
    "PROTOCOL.md": "809f78bbcc1a1f78c36227837104f62c693173c2e875dc10f8dd1919f60a3454",
    "FREEZE_PROTOCOL.md": "7decb45ef030b4c6852899530c9fecf4d75766c66805c83c860e8d3b8c592832",
    "generation_gate.py": "fc0365f93c57a70d6a73d614edaaee600a288617bb3ea2650f95fa7e87cb41ea",
    "runtime_adapter.py": "5e6f2e89c724cfc3f5b4eb486eb2a9384fde9b23fb12010576f5c7f3f98e8d7f",
    "launch_generation.py": "ee0c3f5a37758a778c2dfc9c687ef5805f7eb6a2f990311a9e64116b73bc281d",
    "freeze_c2_manifest.py": "477a0bbb2317422028b8cf9750152bda1ebb0bb784ace026b10985c7fc525d5f",
    "create_launch_authorization.py": "cdf4153d905f7e5226c0032e9ad0c2fcce86f5652412ae246f2c919336fe49d9",
    "inference_seed44.yaml": "90871e1df4d0569f52a8baa7919f66000ec2f1a4f9a9275a2e4fbe384a6a07b9",
}
FORMAL = (
    HERE / ".execution_01.supervisor_failure.json",
    HERE / ".execution_01.watchdog_failure.json",
    HERE / ".freeze_attempt_01.claimed",
    HERE / ".freeze_attempt_01.staging",
    HERE / ".review_attachment_01.claimed",
    HERE / ".review_attachment_01.preflight",
    HERE / ".review_attachment_01.staging",
    HERE / "FINAL_ATTACHMENT_REVIEW.json",
    HERE / "LAUNCH_READINESS_REVIEW.json",
    HERE / "execution_01",
    HERE / "freeze_attempt_01",
    HERE / "launch_authorization_01.json",
    HERE / "launch_authorization_attempt_01",
    PROJECT / "results/S47_C2_confirmation_generation",
    HERE / "review_attachment_01",
)


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def lexists(path):
    return os.path.lexists(path)


def load_exact_module(name, path):
    payload = Path(path).read_bytes()
    module = ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = ""
    sys.modules[name] = module
    exec(compile(payload, str(path), "exec", dont_inherit=True), module.__dict__)
    return module


class FakeControl:
    def validate(self):
        return {"synthetic": True}


def exact_derived_namespace_probe(launcher):
    """Prove the production watchdog lookup cannot see parent-local psutil."""
    with tempfile.TemporaryDirectory(prefix="s47-c2-v6-derived-") as temporary:
        held = launcher.HeldDirectory.open(Path(temporary).resolve())
        frame = SimpleNamespace(
            f_code=launcher._run_supervisor.__code__,
            f_locals={"execution": held, "control": FakeControl()},
        )
        real_sys = launcher.sys
        try:
            launcher.sys = SimpleNamespace(_getframe=lambda depth: frame)
            code, proof = launcher.derive_launcher()
        finally:
            launcher.sys = real_sys
            held.close()

    derived_namespace = {}
    exec(code, derived_namespace)
    parent_code = derived_namespace["parent"].__code__
    instructions = list(dis.get_instructions(parent_code))
    imports_psutil = any(
        item.opname == "IMPORT_NAME" and item.argval == "psutil"
        for item in instructions
    )
    psutil_store_fast = any(
        item.opname == "STORE_FAST" and item.argval == "psutil"
        for item in instructions
    )
    launch_tree = ast.parse((HERE / "launch_generation.py").read_bytes())
    supervisor = next(
        node for node in launch_tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "_run_supervisor"
    )
    psutil_namespace_loads = []
    psutil_namespace_stores = []
    for node in ast.walk(supervisor):
        if not isinstance(node, ast.Subscript):
            continue
        if not (isinstance(node.value, ast.Name) and node.value.id == "namespace"):
            continue
        key = node.slice.value if isinstance(node.slice, ast.Constant) else None
        if key != "psutil":
            continue
        record = {"line": node.lineno, "context": type(node.ctx).__name__}
        if isinstance(node.ctx, ast.Load):
            psutil_namespace_loads.append(record)
        else:
            psutil_namespace_stores.append(record)
    key_error = False
    try:
        derived_namespace["psutil"]
    except KeyError:
        key_error = True
    require(proof["reversible_full_AST_equal"] is True, "Derived AST proof failed")
    require(imports_psutil and psutil_store_fast, "Inherited parent no longer keeps psutil local")
    require("psutil" in parent_code.co_varnames, "psutil is not a parent local")
    require("psutil" not in derived_namespace and key_error, "Derived namespace unexpectedly has psutil")
    require(
        [item["line"] for item in psutil_namespace_loads] == [1453, 1461]
        and psutil_namespace_stores == [],
        "Unexpected production namespace psutil access pattern",
    )
    return {
        "exact_derived_ast_reversible": True,
        "derived_module_namespace_contains_psutil": False,
        "inherited_parent_imports_psutil": imports_psutil,
        "inherited_parent_psutil_is_fast_local": psutil_store_fast,
        "parent_code_varnames_contains_psutil": True,
        "production_namespace_psutil_load_lines": [1453, 1461],
        "production_namespace_psutil_store_lines": [],
        "direct_missing_key_reproduced": key_error,
        "implication": "The real watchdog evaluates namespace['psutil'] with no such key and enters its failure path before monitoring the worker.",
    }


def read_one_line(fd, timeout=5.0):
    deadline = time.monotonic() + timeout
    payload = b""
    while b"\n" not in payload:
        if time.monotonic() > deadline:
            raise RuntimeError("Timed out waiting for child record")
        chunk = os.read(fd, 4096)
        if not chunk:
            raise RuntimeError("Child record pipe closed")
        payload += chunk
    line, remainder = payload.split(b"\n", 1)
    require(not remainder, "Unexpected trailing child record")
    return json.loads(line)


def real_three_pid_topology_probe(launcher):
    outer_read, outer_write = os.pipe()
    supervisor_pid = os.getpid()
    watchdog_pid = os.fork()
    if watchdog_pid == 0:
        exit_code = 7
        try:
            os.close(outer_read)
            os.setsid()
            worker_read, worker_write = os.pipe()
            worker_pid = os.fork()
            if worker_pid == 0:
                try:
                    os.close(worker_read)
                    os.setsid()
                    direct_parent = os.getppid()
                    output_identity = {"device": 11, "inode": 22}
                    execution_identity = {"device": 33, "inode": 44}
                    ticket = {
                        "schema": "s47-c2-worker-launch-ticket-v2",
                        "status": "BOUND_AFTER_WATCHDOG_OWNERSHIP",
                        "supervisor_pid": supervisor_pid,
                        "watchdog_pid": direct_parent,
                        "worker_pid": os.getpid(),
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
                        direct_parent_pid=direct_parent,
                        worker_pid=os.getpid(),
                        output_root="/synthetic/output",
                        output_identity=output_identity,
                        execution_identity=execution_identity,
                    )
                    result = {
                        "supervisor_pid": supervisor_pid,
                        "watchdog_pid": direct_parent,
                        "worker_pid": os.getpid(),
                        "worker_observed_ppid": direct_parent,
                        "legacy_parent_pid": legacy["parent_pid"],
                    }
                    os.write(worker_write, json.dumps(result, sort_keys=True).encode() + b"\n")
                    os.close(worker_write)
                    os._exit(0)
                except BaseException:
                    os._exit(8)
            os.close(worker_write)
            result = read_one_line(worker_read)
            os.close(worker_read)
            _, status_value = os.waitpid(worker_pid, 0)
            result["worker_exit"] = os.waitstatus_to_exitcode(status_value)
            result["watchdog_pid_observed"] = os.getpid()
            result["watchdog_observed_ppid"] = os.getppid()
            os.write(outer_write, json.dumps(result, sort_keys=True).encode() + b"\n")
            exit_code = 0
        finally:
            try:
                os.close(outer_write)
            except OSError:
                pass
            os._exit(exit_code)
    os.close(outer_write)
    result = read_one_line(outer_read)
    os.close(outer_read)
    _, status_value = os.waitpid(watchdog_pid, 0)
    result["watchdog_exit"] = os.waitstatus_to_exitcode(status_value)
    require(
        result["worker_exit"] == result["watchdog_exit"] == 0
        and len({result["supervisor_pid"], result["watchdog_pid"], result["worker_pid"]}) == 3
        and result["watchdog_pid"] == result["watchdog_pid_observed"] == watchdog_pid
        and result["watchdog_observed_ppid"] == supervisor_pid
        and result["worker_observed_ppid"] == watchdog_pid
        and result["legacy_parent_pid"] == watchdog_pid,
        "Real three-PID topology did not satisfy the translated legacy predicate",
    )
    return result


class NoSuchProcess(Exception):
    pass


class ShellProcessAPI:
    STATUS_ZOMBIE = "zombie"

    @staticmethod
    def _snapshot():
        text = subprocess.check_output(
            ["/bin/ps", "-axo", "pid=,ppid=,lstart=,stat="], text=True
        )
        records = {}
        for line in text.splitlines():
            parts = line.split()
            if len(parts) < 8:
                continue
            pid = int(parts[0]); ppid = int(parts[1])
            stamp = " ".join(parts[2:7])
            try:
                created = time.mktime(time.strptime(stamp, "%a %b %d %H:%M:%S %Y"))
            except ValueError:
                continue
            records[pid] = {"ppid": ppid, "created": float(created), "stat": parts[7]}
        return records

    class ProcessObject:
        def __init__(self, api, pid):
            self.api = api
            self.pid = int(pid)

        def _record(self):
            try:
                return self.api._snapshot()[self.pid]
            except KeyError:
                raise NoSuchProcess(self.pid)

        def create_time(self):
            return self._record()["created"]

        def status(self):
            return "zombie" if self._record()["stat"].startswith("Z") else "running"

        def is_running(self):
            try:
                return not self._record()["stat"].startswith("Z")
            except NoSuchProcess:
                return False

        def children(self, recursive=False):
            require(recursive is False, "Probe supports one-level discovery only")
            records = self.api._snapshot()
            return [self.api.Process(pid) for pid, record in records.items()
                    if record["ppid"] == self.pid]

        def send_signal(self, current_signal):
            try:
                os.kill(self.pid, current_signal)
            except ProcessLookupError:
                raise NoSuchProcess(self.pid)

    def Process(self, pid):
        process = self.ProcessObject(self, pid)
        process._record()
        return process


def pid_absent_or_zombie(pid, timeout=5.0):
    api = ShellProcessAPI()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            process = api.Process(pid)
            if process.status() == api.STATUS_ZOMBIE:
                return True
        except NoSuchProcess:
            return True
        time.sleep(0.02)
    return False


def spawn_worker_with_detached_child(marker, command_read, info_write, timing):
    os.setsid()
    if timing == "late":
        require(os.read(command_read, 1) == b"S", "Late descendant trigger missing")
    child_pid = os.fork()
    if child_pid == 0:
        try:
            os.setsid()
            marker.write_text(str(os.getpid()), encoding="ascii")
            for descriptor in (0, 1, 2):
                try:
                    os.close(descriptor)
                except OSError:
                    pass
            while True:
                time.sleep(1)
        finally:
            os._exit(0)
    os.write(
        info_write,
        json.dumps({"worker_pid": os.getpid(), "descendant_pid": child_pid,
                    "timing": timing, "setsid": True, "closed_stdio": True},
                   sort_keys=True).encode() + b"\n",
    )
    while True:
        time.sleep(1)


def real_detached_cleanup_probe(launcher, timing):
    require(timing in {"pre", "late"}, "Unknown cleanup timing")
    with tempfile.TemporaryDirectory(prefix="s47-c2-v6-cleanup-") as temporary:
        marker = Path(temporary) / "descendant.pid"
        command_read, command_write = os.pipe()
        info_read, info_write = os.pipe()
        worker_pid = os.fork()
        if worker_pid == 0:
            try:
                os.close(command_write); os.close(info_read)
                spawn_worker_with_detached_child(marker, command_read, info_write, timing)
            finally:
                os._exit(9)
        os.close(command_read); os.close(info_write)
        ledger = {}
        descendant_pid = None
        try:
            api = ShellProcessAPI()
            if timing == "late":
                launcher._refresh_descendant_ledger(api, worker_pid, ledger)
                require(set(ledger) == {worker_pid}, "Late ledger was not worker-only initially")
                os.write(command_write, b"S")
            info = read_one_line(info_read)
            descendant_pid = info["descendant_pid"]
            deadline = time.monotonic() + 5
            while not marker.exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            require(marker.exists(), "Detached child did not publish readiness")
            if timing == "pre":
                launcher._refresh_descendant_ledger(api, worker_pid, ledger)
                require({worker_pid, descendant_pid} <= set(ledger),
                        "Pre-registered ledger omitted detached descendant")
            actions, status_value, complete = launcher._terminate_and_reap_owned_group(
                worker_pid, process_api=api, descendant_ledger=ledger
            )
            gone = {
                str(worker_pid): pid_absent_or_zombie(worker_pid),
                str(descendant_pid): pid_absent_or_zombie(descendant_pid),
            }
            require(
                complete and status_value != 0 and all(gone.values())
                and {worker_pid, descendant_pid} <= set(ledger),
                "Detached registered cleanup did not close",
            )
            return {
                "timing": timing,
                "worker_pid": worker_pid,
                "descendant_pid": descendant_pid,
                "setsid": True,
                "closed_stdio": True,
                "ledger_pids": sorted(ledger),
                "cleanup_complete": complete,
                "worker_status": status_value,
                "all_target_pids_absent_or_zombie": gone,
                "signals_recorded": actions,
            }
        finally:
            for descriptor in (command_write, info_read):
                try:
                    os.close(descriptor)
                except OSError:
                    pass
            for pid in (descendant_pid, worker_pid):
                if pid:
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
            try:
                os.waitpid(worker_pid, os.WNOHANG)
            except ChildProcessError:
                pass


def terminal_fault_probe(launcher):
    results = {}
    with tempfile.TemporaryDirectory(prefix="s47-c2-v6-terminal-") as temporary:
        root = Path(temporary).resolve()
        execution = root / "execution_01"; execution.mkdir()
        held_root = launcher.HeldDirectory.open(root)
        held_execution = launcher.HeldDirectory.open(execution)
        terminal = launcher.HeldCreatedJSON.create(
            held_execution.fd, launcher.SUPERVISOR_COMMIT,
            {"status": "COMMIT_CANDIDATE_REQUIRES_OUTER_RETURN_AND_NO_ROOT_FAILURE",
             "standalone_success": False},
        )
        real_fsync = launcher.os.fsync
        try:
            def fail_directory_sync(descriptor):
                if descriptor == held_execution.fd:
                    raise OSError("independent file-fsync/dir-fsync fault")
                return real_fsync(descriptor)
            launcher.os.fsync = fail_directory_sync
            rejected = False
            try:
                terminal.sync_directory()
            except OSError:
                rejected = True
        finally:
            launcher.os.fsync = real_fsync
        launcher.write_new_json_at(
            held_root.fd, launcher.SUPERVISOR_FAILURE_FALLBACK,
            {"status": "SUPERVISOR_TERMINAL_COMMIT_NOT_ACCEPTED",
             "terminal_commit_is_standalone_success": False},
        )
        body = json.loads((execution / launcher.SUPERVISOR_COMMIT).read_text())
        results["post_file_fsync_pre_directory_fsync"] = {
            "directory_sync_rejected": rejected,
            "commit_body_standalone_success": body["standalone_success"],
            "root_failure_recorded": (root / launcher.SUPERVISOR_FAILURE_FALLBACK).is_file(),
        }
        terminal.close(); held_execution.close(); held_root.close()

    with tempfile.TemporaryDirectory(prefix="s47-c2-v6-pathswap-") as temporary:
        root = Path(temporary).resolve()
        execution = root / "execution_01"; execution.mkdir()
        held_root = launcher.HeldDirectory.open(root)
        held_execution = launcher.HeldDirectory.open(execution)
        terminal = launcher.HeldCreatedJSON.create(
            held_execution.fd, launcher.SUPERVISOR_COMMIT,
            {"status": "COMMIT_CANDIDATE_REQUIRES_OUTER_RETURN_AND_NO_ROOT_FAILURE",
             "standalone_success": False},
        )
        terminal.sync_directory()
        moved = root / "execution_01.moved"
        os.rename(execution, moved); execution.mkdir()
        rejected = False
        try:
            held_execution.validate()
        except RuntimeError:
            rejected = True
        launcher.write_new_json_at(
            held_root.fd, launcher.SUPERVISOR_FAILURE_FALLBACK,
            {"status": "SUPERVISOR_TERMINAL_COMMIT_NOT_ACCEPTED",
             "terminal_commit_is_standalone_success": False},
        )
        results["post_commit_canonical_name_replacement"] = {
            "canonical_validation_rejected": rejected,
            "commit_remained_only_on_held_moved_inode": (
                (moved / launcher.SUPERVISOR_COMMIT).is_file()
                and not (execution / launcher.SUPERVISOR_COMMIT).exists()
            ),
            "root_failure_recorded": (root / launcher.SUPERVISOR_FAILURE_FALLBACK).is_file(),
        }
        terminal.close(); held_execution.close(); held_root.close()
    require(
        results["post_file_fsync_pre_directory_fsync"] == {
            "directory_sync_rejected": True,
            "commit_body_standalone_success": False,
            "root_failure_recorded": True,
        }
        and all(results["post_commit_canonical_name_replacement"].values()),
        "Terminal fault matrix did not fail closed",
    )
    return results


def main():
    require(sys.version_info[:2] in {(3, 12), (3, 13)}, "Need reviewed Python 3.12/3.13")
    formal_before = {str(path): lexists(path) for path in FORMAL}
    require(not any(formal_before.values()), "Formal C2 state is not fresh")
    actual = {name: sha(HERE / name) for name in EXPECTED}
    require(actual == EXPECTED, "Exact V6 candidate hash mismatch")
    launcher = load_exact_module("_s47_c2_v6_adversarial", HERE / "launch_generation.py")
    result = {
        "schema": "s47-c2-v6-independent-adversarial-probe-v1",
        "status": "REPRODUCED_V6_PRODUCTION_WATCHDOG_PROCESS_API_NAMESPACE_BLOCKER",
        "started_and_completed_utc": datetime.now(timezone.utc).isoformat(),
        "python": {
            "version": ".".join(str(x) for x in sys.version_info[:3]),
            "executable": sys.executable,
            "isolated": sys.flags.isolated == 1,
            "dont_write_bytecode": sys.dont_write_bytecode,
            "no_site": sys.flags.no_site == 1,
        },
        "exact_candidate_sha256": actual,
        "derived_namespace_blocker": exact_derived_namespace_probe(launcher),
        "real_three_pid_topology": real_three_pid_topology_probe(launcher),
        "real_registered_detached_cleanup": {
            "pre_registered": real_detached_cleanup_probe(launcher, "pre"),
            "late_registered": real_detached_cleanup_probe(launcher, "late"),
        },
        "disposable_terminal_faults": terminal_fault_probe(launcher),
        "execution_boundary": {
            "prepare_calls": 0,
            "attach_calls": 0,
            "authorization_main_calls": 0,
            "formal_gate_calls": 0,
            "launcher_main_calls": 0,
            "production_worker_calls": 0,
            "model_or_scientific_imports": 0,
            "c2_input_body_bytes_read": 0,
            "images_opened": 0,
            "pixels_decoded": 0,
            "generation_calls": 0,
            "formal_paths_created": 0,
        },
    }
    formal_after = {str(path): lexists(path) for path in FORMAL}
    require(formal_after == formal_before and not any(formal_after.values()),
            "Probe changed formal C2 state")
    result["formal_paths_lexists_after"] = formal_after
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
