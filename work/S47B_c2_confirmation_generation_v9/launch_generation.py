"""Bounded C2 two-batch entry, reversibly derived from the sealed S35 supervisor."""
from __future__ import annotations

import ast
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import select
import signal
import stat
import subprocess
import sys
import time
import traceback
from types import ModuleType, SimpleNamespace


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
S35 = ROOT / "work/S35_generation_integration"
PARENT = S35 / "launch_original.py"
PARENT_SHA256 = "8744cb8959cded2394c1471c660dd84f929b5ae24ac97e81379304aed0be702e"
GATE = HERE / "generation_gate.py"
GATE_SHA256 = "4cd5c2179d2eaf17b85890acb5198d8573d2525be3e787a7ce00a17e7f2473cd"
PUBLISHED_MANIFEST = HERE / "review_attachment_01/manifest.json"
EXECUTION = HERE / "execution_01"
CAPABILITY_RECORD = "worker_capability.json"
CAPABILITY_CONSUMED = "worker_capability_consumed.json"
WATCHDOG_RECEIPT = "watchdog_receipt.json"
WATCHDOG_FALLBACK_RECEIPT = ".execution_01.watchdog_failure.json"
SUPERVISOR_STARTED = "supervisor_attempt_started.json"
SUPERVISOR_PROVISIONAL = "supervisor_terminal_provisional.json"
SUPERVISOR_COMMIT = "supervisor_terminal_commit.json"
SUPERVISOR_FAILURE_FALLBACK = ".execution_01.supervisor_failure.json"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
LABELS = {
    "s35-original-generation-run-v1": "s47-c2-confirmation-two-batch-v1",
    "FROZEN_REAL_EXECUTION": "FROZEN_C2_BASELINE_CONFIRMATION_TWO_BATCH_EXECUTION",
    "s35-original-worker-v1": "s47-c2-confirmation-worker-v1",
    "s35-original-launch-v1": "s47-c2-confirmation-launch-v1",
    "ORIGINAL_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW": "C2_BASELINE_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW",
    "COMPLETED_EXTERNAL_RUN_PENDING_INDEPENDENT_REVIEW": "C2_BASELINE_EXTERNAL_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW",
    "FAILED_OR_PARTIAL_ORIGINAL_RUN": "FAILED_OR_PARTIAL_C2_BASELINE_RUN",
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def read_regular_snapshot(path, label):
    """Read one regular-file byte snapshot from one no-follow descriptor."""
    path = Path(path)
    require(path.is_absolute(), label + " path must be absolute")
    flags = (os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
             | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        require(stat.S_ISREG(before.st_mode), label + " must be a regular file")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
        identity_before = (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        )
        identity_after = (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        )
        payload = b"".join(chunks)
        require(identity_before == identity_after and len(payload) == before.st_size,
                label + " changed while its descriptor was open")
        return payload
    finally:
        os.close(descriptor)


def snapshot_sha(path):
    return hashlib.sha256(read_regular_snapshot(Path(path).absolute(), "Bound file")).hexdigest()


def load_bound_snapshot(path, identities):
    """Compile and execute the exact bytes hashed on the same descriptor read."""
    path = Path(path).absolute()
    expected = identities.get(str(path))
    payload = read_regular_snapshot(path, "Bound source")
    require(isinstance(expected, str) and HEX64.fullmatch(expected)
            and hashlib.sha256(payload).hexdigest() == expected,
            "Unbound or changed source: " + str(path))
    name = path.stem
    module = ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = ""
    sys.modules[name] = module
    try:
        exec(compile(payload, str(path), "exec", dont_inherit=True), module.__dict__)
    except BaseException:
        if sys.modules.get(name) is module:
            del sys.modules[name]
        raise
    return module


def json_bytes(document):
    return (
        json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    ).encode("utf-8")


def directory_flags():
    return (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )


class HeldDirectory:
    """A no-symlink absolute directory chain retained for one mutation window."""

    def __init__(self, path, chain):
        self.path = Path(path)
        self.chain = chain
        self.fd = chain[-1][1]
        self.identity = {"device": chain[-1][2], "inode": chain[-1][3]}
        self.closed = False

    @classmethod
    def open(cls, path):
        path = Path(path)
        require(path.is_absolute(), "Held directory path must be absolute")
        current = os.open("/", directory_flags())
        root_stat = os.fstat(current)
        chain = [(Path("/"), current, root_stat.st_dev, root_stat.st_ino)]
        prefix = Path("/")
        try:
            for part in path.parts[1:]:
                next_fd = os.open(part, directory_flags(), dir_fd=current)
                current_stat = os.fstat(next_fd)
                require(stat.S_ISDIR(current_stat.st_mode), "Held path component is not a directory")
                prefix = prefix / part
                chain.append((prefix, next_fd, current_stat.st_dev, current_stat.st_ino))
                current = next_fd
            handle = cls(path, chain)
            handle.validate()
            return handle
        except BaseException:
            for _, descriptor, _, _ in reversed(chain):
                try:
                    os.close(descriptor)
                except OSError:
                    pass
            raise

    def validate(self):
        require(not self.closed, "Held directory is already closed")
        for path, descriptor, device, inode in self.chain:
            by_fd = os.fstat(descriptor)
            by_path = os.stat(path, follow_symlinks=False)
            require(
                stat.S_ISDIR(by_fd.st_mode)
                and stat.S_ISDIR(by_path.st_mode)
                and (by_fd.st_dev, by_fd.st_ino) == (device, inode)
                and (by_path.st_dev, by_path.st_ino) == (device, inode),
                "Held directory or one of its ancestors changed: " + str(path),
            )
        return dict(self.identity)

    def duplicate_chain(self):
        """Duplicate the already-held ancestor chain for the forked full gate."""
        self.validate()
        duplicated = []
        try:
            for path, descriptor, device, inode in self.chain:
                copy_fd = os.dup(descriptor)
                os.set_inheritable(copy_fd, False)
                duplicated.append((str(path), copy_fd, device, inode))
            return duplicated
        except BaseException:
            for _, descriptor, _, _ in duplicated:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
            raise

    def close(self):
        if not self.closed:
            self.closed = True
            for _, descriptor, _, _ in reversed(self.chain):
                try:
                    os.close(descriptor)
                except OSError:
                    pass


def entry_stat(directory, name):
    return os.stat(name, dir_fd=directory.fd, follow_symlinks=False)


def entry_exists(directory, name):
    try:
        entry_stat(directory, name)
    except FileNotFoundError:
        return False
    return True


class HeldCreatedJSON:
    """A create-only JSON inode retained through file, directory, and path checks."""

    def __init__(self, directory_fd, name, descriptor, payload):
        self.directory_fd = directory_fd
        self.name = name
        self.fd = descriptor
        self.payload = payload
        opened = os.fstat(descriptor)
        self.identity = {
            "device": opened.st_dev,
            "inode": opened.st_ino,
            "size": opened.st_size,
        }
        self.closed = False

    @classmethod
    def create(cls, directory_fd, name, document, *, mode=0o444):
        payload = json_bytes(document)
        flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0)
        )
        descriptor = os.open(name, flags, 0o600, dir_fd=directory_fd)
        try:
            view = memoryview(payload)
            while view:
                written = os.write(descriptor, view)
                require(written > 0, "Short create-only JSON write")
                view = view[written:]
            os.fchmod(descriptor, mode)
            os.fsync(descriptor)
            held = cls(directory_fd, name, descriptor, payload)
            held.validate()
            return held
        except BaseException:
            os.close(descriptor)
            raise

    @property
    def sha256(self):
        return hashlib.sha256(self.payload).hexdigest()

    def validate(self):
        require(not self.closed, "Held JSON inode is already closed")
        opened = os.fstat(self.fd)
        by_name = os.stat(
            self.name, dir_fd=self.directory_fd, follow_symlinks=False
        )
        require(
            stat.S_ISREG(opened.st_mode)
            and stat.S_ISREG(by_name.st_mode)
            and (opened.st_dev, opened.st_ino, opened.st_size)
            == (self.identity["device"], self.identity["inode"], self.identity["size"])
            == (by_name.st_dev, by_name.st_ino, by_name.st_size)
            and opened.st_size == len(self.payload),
            "Create-only JSON entry changed while its descriptor was held",
        )
        return dict(self.identity)

    def sync_directory(self):
        self.validate()
        os.fsync(self.directory_fd)
        self.validate()

    def close(self):
        if not self.closed:
            self.closed = True
            os.close(self.fd)


def write_new_json_at(directory_fd, name, document, *, mode=0o444):
    held = HeldCreatedJSON.create(directory_fd, name, document, mode=mode)
    try:
        held.sync_directory()
        return held.sha256
    finally:
        held.close()


def read_json_at(directory_fd, name, label, expected=None):
    flags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    descriptor = os.open(name, flags, dir_fd=directory_fd)
    try:
        before = os.fstat(descriptor)
        require(stat.S_ISREG(before.st_mode), label + " is not a regular file")
        payload = b""
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            payload += chunk
        after = os.fstat(descriptor)
        by_name = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        require(
            (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
            == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
            and (after.st_dev, after.st_ino) == (by_name.st_dev, by_name.st_ino)
            and len(payload) == before.st_size,
            label + " changed while its descriptor was held",
        )
        digest = hashlib.sha256(payload).hexdigest()
        if expected is not None:
            require(digest == expected, label + " SHA-256 differs")
        return json.loads(payload), digest
    finally:
        os.close(descriptor)


def parse_exact_arguments(argv, *, internal):
    """Reject abbreviations, equals forms, repeats, and unknown options."""
    values = list(argv)
    if internal:
        require(values and values[0] == "--worker", "Internal worker marker is missing")
        values = values[1:]
    else:
        require("--worker" not in values, "The public C2 entry cannot select worker mode")
    allowed = ("--manifest", "--manifest-sha256", "--execution-directory")
    require(len(values) == 2 * len(allowed), "C2 launcher requires three exact split-form options")
    parsed = {}
    for index in range(0, len(values), 2):
        option, value = values[index:index + 2]
        require(option in allowed and "=" not in option, "Unknown, abbreviated, or equals-form option")
        require(option not in parsed, "Duplicate C2 launcher option: " + option)
        require(isinstance(value, str) and value and not value.startswith("--"),
                "C2 launcher option is missing its value: " + option)
        parsed[option] = value
    require(set(parsed) == set(allowed), "C2 launcher option set is incomplete")
    require(parsed["--manifest"] == str(PUBLISHED_MANIFEST),
            "C2 launch is bound to the canonical attached manifest")
    require(HEX64.fullmatch(parsed["--manifest-sha256"]) is not None,
            "C2 manifest SHA-256 is malformed")
    require(parsed["--execution-directory"] == str(EXECUTION),
            "C2 single attempt is bound to canonical execution_01")
    return SimpleNamespace(
        manifest=parsed["--manifest"],
        manifest_sha256=parsed["--manifest-sha256"],
        execution_directory=parsed["--execution-directory"],
        worker=internal,
    )


def translate_worker_ticket(ticket, *, manifest_sha256, launcher_sha256,
                            supervisor_pid, direct_parent_pid, worker_pid,
                            output_root, output_identity, execution_identity):
    """Validate the V7 three-process binding and return the legacy worker view."""
    require(
        isinstance(ticket, dict)
        and set(ticket) == {
            "schema", "status", "supervisor_pid", "watchdog_pid", "worker_pid",
            "manifest_sha256", "launcher_sha256", "output_root",
            "output_identity", "execution_identity", "parent_requested_utc",
            "created_utc", "direct_worker_parent",
        }
        and ticket.get("schema") == "s47-c2-worker-launch-ticket-v2"
        and ticket.get("status") == "BOUND_AFTER_WATCHDOG_OWNERSHIP"
        and ticket.get("supervisor_pid") == supervisor_pid
        and ticket.get("watchdog_pid") == direct_parent_pid
        and ticket.get("worker_pid") == worker_pid
        and ticket.get("manifest_sha256") == manifest_sha256
        and ticket.get("launcher_sha256") == launcher_sha256
        and ticket.get("output_root") == output_root
        and ticket.get("output_identity") == output_identity
        and ticket.get("execution_identity") == execution_identity
        and ticket.get("direct_worker_parent") == "WATCHDOG_PID",
        "Worker launch ticket does not bind the actual supervisor/watchdog/worker topology",
    )
    return {
        "parent_pid": direct_parent_pid,
        "manifest_sha256": manifest_sha256,
        "launcher_sha256": launcher_sha256,
        "output_root": output_root,
        "output_identity": dict(output_identity),
        "created_utc": ticket["created_utc"],
        "execution_identity": dict(execution_identity),
    }


class ForkWorkerProcess:
    """Popen-compatible worker status relayed by its direct-parent watchdog."""

    def __init__(self, pid, wait_pid, status_fd):
        self.pid = pid
        self.wait_pid = wait_pid
        self.status_fd = status_fd
        self.status_buffer = b""
        self.returncode = None
        self.watchdog_returncode = None

    def _close_status(self):
        if self.status_fd is not None:
            try:
                os.close(self.status_fd)
            except OSError:
                pass
            self.status_fd = None

    def _read_status(self, timeout):
        if self.returncode is not None:
            return self.returncode
        require(self.status_fd is not None,
                "Worker-status channel closed without a terminal status")
        readable, _, _ = select.select([self.status_fd], [], [], timeout)
        if not readable:
            return None
        chunk = os.read(self.status_fd, 128)
        if not chunk:
            self._close_status()
            raise RuntimeError("Watchdog closed before relaying worker status")
        self.status_buffer += chunk
        if b"\n" not in self.status_buffer:
            return None
        line, remainder = self.status_buffer.split(b"\n", 1)
        require(not remainder and re.fullmatch(rb"-?[0-9]+", line) is not None,
                "Malformed worker status from watchdog")
        self.returncode = int(line)
        self._close_status()
        return self.returncode

    def poll(self):
        return self._read_status(0)

    def wait(self, timeout=None):
        if self.returncode is not None:
            return self.returncode
        deadline = None if timeout is None else time.monotonic() + max(0.0, timeout)
        while True:
            remaining = None if deadline is None else max(0.0, deadline - time.monotonic())
            result = self._read_status(remaining)
            if result is not None:
                return result
            if deadline is not None and time.monotonic() >= deadline:
                raise subprocess.TimeoutExpired("S47 C2 forked worker", timeout)

    def terminate(self):
        if self.poll() is None:
            try:
                os.killpg(self.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass

    def wait_watchdog(self, timeout=None):
        if self.watchdog_returncode is not None:
            return self.watchdog_returncode
        if timeout is None:
            _, status_value = os.waitpid(self.wait_pid, 0)
            self.watchdog_returncode = os.waitstatus_to_exitcode(status_value)
            return self.watchdog_returncode
        deadline = time.monotonic() + max(0.0, timeout)
        while True:
            waited, status_value = os.waitpid(self.wait_pid, os.WNOHANG)
            if waited == self.wait_pid:
                self.watchdog_returncode = os.waitstatus_to_exitcode(status_value)
                return self.watchdog_returncode
            if time.monotonic() >= deadline:
                raise subprocess.TimeoutExpired("S47 C2 watchdog", timeout)
            time.sleep(min(0.01, max(0.0, deadline - time.monotonic())))


def _group_exists(pgid):
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _is_missing_process_error(error):
    return type(error).__name__ in {"NoSuchProcess", "ZombieProcess"}


def _refresh_descendant_ledger(process_api, worker_pid, ledger):
    """Retain PID/create-time identities across reparenting and session changes."""
    require(process_api is not None and hasattr(process_api, "Process"),
            "A reviewed process-identity API is required")
    queue = [worker_pid] + sorted(pid for pid in ledger if pid != worker_pid)
    visited = set()
    added = []
    while queue:
        pid = queue.pop(0)
        if pid in visited:
            continue
        visited.add(pid)
        try:
            process = process_api.Process(pid)
            created = float(process.create_time())
            status_value = process.status()
        except BaseException as error:
            if _is_missing_process_error(error):
                continue
            raise
        expected = ledger.get(pid)
        require(expected is None or created == expected,
                "A registered process identity was reused")
        if status_value == getattr(process_api, "STATUS_ZOMBIE", "zombie"):
            continue
        if expected is None:
            ledger[pid] = created
            added.append({"pid": pid, "created": created})
        try:
            children = process.children(recursive=False)
        except BaseException as error:
            if _is_missing_process_error(error):
                continue
            raise
        for child in children:
            child_pid = int(child.pid)
            try:
                child_created = float(child.create_time())
                child_status = child.status()
            except BaseException as error:
                if _is_missing_process_error(error):
                    continue
                raise
            prior = ledger.get(child_pid)
            require(prior is None or prior == child_created,
                    "A discovered descendant PID identity was reused")
            if child_status != getattr(process_api, "STATUS_ZOMBIE", "zombie"):
                if prior is None:
                    ledger[child_pid] = child_created
                    added.append({"pid": child_pid, "created": child_created})
                queue.append(child_pid)
    return added


def _registered_identity_alive(process_api, pid, created):
    try:
        process = process_api.Process(pid)
        return (
            float(process.create_time()) == created
            and process.status() != getattr(process_api, "STATUS_ZOMBIE", "zombie")
            and process.is_running()
        )
    except BaseException as error:
        if _is_missing_process_error(error):
            return False
        raise


def _all_registered_gone(process_api, ledger):
    return all(
        not _registered_identity_alive(process_api, pid, created)
        for pid, created in ledger.items()
    )


def _signal_registered(process_api, ledger, current_signal, actions):
    for pid, created in sorted(ledger.items(), reverse=True):
        try:
            process = process_api.Process(pid)
            if (
                float(process.create_time()) == created
                and process.status() != getattr(process_api, "STATUS_ZOMBIE", "zombie")
                and process.is_running()
            ):
                process.send_signal(current_signal)
                actions.append({
                    "signal": int(current_signal),
                    "target_pid": pid,
                    "created": created,
                })
        except BaseException as error:
            if not _is_missing_process_error(error):
                raise


def _terminate_and_reap_owned_group(worker_pid, worker_status=None, *,
                                    process_api, descendant_ledger):
    """Terminate the direct child and every durable PID/create-time identity."""
    actions = []
    for current_signal, timeout in ((signal.SIGTERM, 2.0), (signal.SIGKILL, 2.0)):
        _refresh_descendant_ledger(process_api, worker_pid, descendant_ledger)
        if (
            worker_status is not None
            and not _group_exists(worker_pid)
            and _all_registered_gone(process_api, descendant_ledger)
        ):
            break
        try:
            os.killpg(worker_pid, current_signal)
            actions.append({"signal": int(current_signal), "target_pgid": worker_pid})
        except ProcessLookupError:
            pass
        _signal_registered(process_api, descendant_ledger, current_signal, actions)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            _refresh_descendant_ledger(process_api, worker_pid, descendant_ledger)
            if worker_status is None:
                waited, raw_status = os.waitpid(worker_pid, os.WNOHANG)
                if waited == worker_pid:
                    worker_status = os.waitstatus_to_exitcode(raw_status)
            if (
                worker_status is not None
                and not _group_exists(worker_pid)
                and _all_registered_gone(process_api, descendant_ledger)
            ):
                break
            time.sleep(0.02)
    if worker_status is None:
        _, raw_status = os.waitpid(worker_pid, 0)
        worker_status = os.waitstatus_to_exitcode(raw_status)
    _refresh_descendant_ledger(process_api, worker_pid, descendant_ledger)
    cleanup_complete = (
        not _group_exists(worker_pid)
        and _all_registered_gone(process_api, descendant_ledger)
    )
    return actions, worker_status, cleanup_complete


def _watchdog_loop(liveness_fd, acknowledgement_fd, status_fd, worker_pid,
                   execution_fd, here_fd, binding, process_api):
    """Direct worker parent; liveness EOF before ``S`` means supervisor loss."""
    exit_code = 3
    worker_status = None
    worker_status_relayed = False
    supervisor_completed = False
    descendant_ledger = {}
    ledger_additions = []
    try:
        opened_execution = os.fstat(execution_fd)
        require(
            (opened_execution.st_dev, opened_execution.st_ino)
            == (binding["execution_identity"]["device"],
                binding["execution_identity"]["inode"]),
            "Watchdog inherited another execution directory inode",
        )
        ledger_additions.extend(
            _refresh_descendant_ledger(process_api, worker_pid, descendant_ledger)
        )
        while worker_status is None or not supervisor_completed:
            ledger_additions.extend(
                _refresh_descendant_ledger(process_api, worker_pid, descendant_ledger)
            )
            if worker_status is None:
                waited, raw_status = os.waitpid(worker_pid, os.WNOHANG)
                if waited == worker_pid:
                    worker_status = os.waitstatus_to_exitcode(raw_status)
                    message = (str(worker_status) + "\n").encode("ascii")
                    try:
                        require(os.write(status_fd, message) == len(message),
                                "Watchdog could not relay worker status")
                        worker_status_relayed = True
                    except BrokenPipeError:
                        worker_status_relayed = False
            readable, _, _ = select.select([liveness_fd], [], [], 0.05)
            if readable:
                command = os.read(liveness_fd, 1)
                if command == b"S":
                    supervisor_completed = True
                elif command == b"":
                    break
                else:
                    raise RuntimeError("Unknown supervisor/watchdog protocol byte")
            if supervisor_completed and worker_status is None:
                raise RuntimeError("Supervisor completed before direct child worker was reaped")
        actions = []
        cleanup_complete = (
            worker_status is not None
            and not _group_exists(worker_pid)
            and _all_registered_gone(process_api, descendant_ledger)
        )
        if not supervisor_completed or not cleanup_complete:
            actions, worker_status, cleanup_complete = _terminate_and_reap_owned_group(
                worker_pid, worker_status, process_api=process_api,
                descendant_ledger=descendant_ledger,
            )
        if not worker_status_relayed:
            message = (str(worker_status) + "\n").encode("ascii")
            try:
                require(os.write(status_fd, message) == len(message),
                        "Watchdog could not relay final worker status")
                worker_status_relayed = True
            except BrokenPipeError:
                worker_status_relayed = False
        cleanup_complete = (
            cleanup_complete
            and worker_status is not None
            and _all_registered_gone(process_api, descendant_ledger)
        )
        receipt = {
            "schema": "s47-c2-worker-watchdog-v2",
            "status": (
                "WATCHDOG_CONFIRMED_REGISTERED_DESCENDANTS_GONE"
                if supervisor_completed and cleanup_complete
                else "SUPERVISOR_LOST_REGISTERED_DESCENDANTS_TERMINATED"
                if cleanup_complete
                else "SUPERVISOR_LOST_CLEANUP_UNCONFIRMED"
            ),
            "completed_utc": datetime.now(timezone.utc).isoformat(),
            "supervisor_pid": binding["supervisor_pid"],
            "watchdog_pid": os.getpid(),
            "worker_pid": worker_pid,
            "worker_pgid": worker_pid,
            "manifest_sha256": binding["manifest_sha256"],
            "launcher_sha256": binding["launcher_sha256"],
            "execution_directory": str(EXECUTION),
            "execution_identity": binding["execution_identity"],
            "output_root": binding["output_root"],
            "output_identity": binding["output_identity"],
            "supervisor_completed_protocol": supervisor_completed,
            "supervisor_liveness_lost": not supervisor_completed,
            "worker_returncode": worker_status,
            "worker_status_relayed": worker_status_relayed,
            "cleanup_actions": actions,
            "cleanup_complete": cleanup_complete,
            "descendant_identity_ledger": [
                {"pid": pid, "created": created}
                for pid, created in sorted(descendant_ledger.items())
            ],
            "descendant_ledger_additions": ledger_additions,
            "all_registered_descendants_gone": _all_registered_gone(
                process_api, descendant_ledger
            ),
            "process_identity_source": "PSUTIL_PID_PLUS_CREATE_TIME_RECURSIVE_DISCOVERY",
            "scope": "Direct worker plus every PID/create-time descendant observed while any registered ancestor remained live; identities remain authoritative after setsid, process-group change, and reparenting",
        }
        try:
            canonical_execution = os.stat(
                EXECUTION.name, dir_fd=here_fd, follow_symlinks=False
            )
        except OSError:
            canonical_matches = False
        else:
            canonical_matches = (
                stat.S_ISDIR(canonical_execution.st_mode)
                and (canonical_execution.st_dev, canonical_execution.st_ino)
                == (opened_execution.st_dev, opened_execution.st_ino)
            )
        receipt["canonical_execution_identity_at_close"] = canonical_matches
        if canonical_matches:
            write_new_json_at(execution_fd, WATCHDOG_RECEIPT, receipt)
        else:
            receipt["status"] = "SUPERVISOR_LOST_CLEANUP_RECORDED_AT_ROOT_FALLBACK"
            write_new_json_at(here_fd, WATCHDOG_FALLBACK_RECEIPT, receipt)
        exit_code = 0 if cleanup_complete and canonical_matches else 4
        try:
            os.write(acknowledgement_fd, b"1" if exit_code == 0 else b"0")
        except OSError:
            pass
    except BaseException as error:
        cleanup_actions = []
        cleanup_complete = False
        try:
            cleanup_actions, worker_status, cleanup_complete = (
                _terminate_and_reap_owned_group(
                    worker_pid, worker_status, process_api=process_api,
                    descendant_ledger=descendant_ledger,
                )
            )
        except BaseException:
            pass
        failure = {
            "schema": "s47-c2-worker-watchdog-v2",
            "status": "WATCHDOG_INTERNAL_FAILURE_ATTEMPT_TERMINATED",
            "completed_utc": datetime.now(timezone.utc).isoformat(),
            "supervisor_pid": binding.get("supervisor_pid"),
            "watchdog_pid": os.getpid(),
            "worker_pid": worker_pid,
            "worker_pgid": worker_pid,
            "manifest_sha256": binding.get("manifest_sha256"),
            "launcher_sha256": binding.get("launcher_sha256"),
            "execution_directory": str(EXECUTION),
            "execution_identity": binding.get("execution_identity"),
            "output_root": binding.get("output_root"),
            "output_identity": binding.get("output_identity"),
            "supervisor_completed_protocol": supervisor_completed,
            "supervisor_liveness_lost": not supervisor_completed,
            "worker_returncode": worker_status,
            "worker_status_relayed": worker_status_relayed,
            "cleanup_actions": cleanup_actions,
            "cleanup_complete": cleanup_complete,
            "descendant_identity_ledger": [
                {"pid": pid, "created": created}
                for pid, created in sorted(descendant_ledger.items())
            ],
            "all_registered_descendants_gone": (
                _all_registered_gone(process_api, descendant_ledger)
                if descendant_ledger else False
            ),
            "error_type": type(error).__name__,
            "error": str(error),
            "scope": "Fail-closed watchdog error evidence; never a success seal",
        }
        try:
            opened_execution = os.fstat(execution_fd)
            canonical_execution = os.stat(
                EXECUTION.name, dir_fd=here_fd, follow_symlinks=False
            )
            canonical_matches = (
                stat.S_ISDIR(canonical_execution.st_mode)
                and (canonical_execution.st_dev, canonical_execution.st_ino)
                == (opened_execution.st_dev, opened_execution.st_ino)
            )
            failure["canonical_execution_identity_at_close"] = canonical_matches
            target_fd = execution_fd if canonical_matches else here_fd
            target_name = WATCHDOG_RECEIPT if canonical_matches else WATCHDOG_FALLBACK_RECEIPT
            try:
                os.stat(target_name, dir_fd=target_fd, follow_symlinks=False)
            except FileNotFoundError:
                write_new_json_at(target_fd, target_name, failure)
        except BaseException:
            pass
        try:
            os.write(acknowledgement_fd, b"0")
        except OSError:
            pass
    finally:
        for descriptor in (
            liveness_fd, acknowledgement_fd, status_fd, execution_fd, here_fd
        ):
            if descriptor is None:
                continue
            try:
                os.close(descriptor)
            except OSError:
                pass
        os._exit(exit_code)


def derive_launcher(*, compile_only=False):
    parent_bytes = read_regular_snapshot(PARENT.absolute(), "Sealed S35 launcher")
    if hashlib.sha256(parent_bytes).hexdigest() != PARENT_SHA256:
        raise RuntimeError("Sealed S35 launcher changed")
    original = ast.parse(parent_bytes, filename=str(PARENT))
    changes = {}
    counts = {label: 0 for label in LABELS}
    routes = {"resource_gate.py": 0, "runtime_factory.py": 0}
    here_count = 0
    hardening = {
        "capability_spawn": 0,
        "execution_adoption": 0,
        "output_claim": 0,
        "worker_ticket_snapshot": 0,
        "worker_receipt_snapshot": 0,
        "worker_receipt_bound_digest": 0,
    }

    def changed(old, new):
        new = ast.copy_location(new, old)
        key = (type(new).__name__, new.lineno, new.col_offset)
        if key in changes:
            raise RuntimeError("Overlapping C2 launcher derivation edits")
        changes[key] = (copy.deepcopy(old), ast.dump(new, include_attributes=False))
        return new

    class Route(ast.NodeTransformer):
        def visit_Assign(self, node):
            nonlocal here_count
            if (
                len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "HERE"
            ):
                here_count += 1
                replacement = copy.deepcopy(node)
                replacement.value = ast.Call(
                    func=ast.Name(id="Path", ctx=ast.Load()),
                    args=[ast.Constant(str(S35))],
                    keywords=[],
                )
                return changed(node, replacement)
            if (
                len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "ticket"
            ):
                hardening["worker_ticket_snapshot"] += 1
                replacement = copy.deepcopy(node)
                replacement.value = ast.Call(
                    func=ast.Name(id="_read_bound_launch_ticket", ctx=ast.Load()),
                    args=[
                        ast.Name(id="execution", ctx=ast.Load()),
                        ast.Attribute(value=ast.Name(id="args", ctx=ast.Load()), attr="manifest_sha256", ctx=ast.Load()),
                        ast.Call(func=ast.Name(id="sha", ctx=ast.Load()),
                                 args=[ast.Name(id="__file__", ctx=ast.Load())], keywords=[]),
                    ],
                    keywords=[],
                )
                return changed(node, replacement)
            if (
                len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "wr"
            ):
                hardening["worker_receipt_snapshot"] += 1
                replacement = copy.deepcopy(node)
                replacement.value = ast.Call(
                    func=ast.Name(id="_read_worker_receipt", ctx=ast.Load()),
                    args=[ast.Name(id="worker_receipt", ctx=ast.Load())],
                    keywords=[],
                )
                return changed(node, replacement)
            return self.generic_visit(node)

        def visit_Call(self, node):
            node = self.generic_visit(node)
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "mkdir"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id in {"execution", "output"}
            ):
                variable = node.func.value.id
                if variable == "execution":
                    hardening["execution_adoption"] += 1
                    helper = "_adopt_execution"
                else:
                    hardening["output_claim"] += 1
                    helper = "_claim_output"
                return changed(
                    node,
                    ast.Call(
                        func=ast.Name(id=helper, ctx=ast.Load()),
                        args=[ast.Name(id=variable, ctx=ast.Load())],
                        keywords=[],
                    ),
                )
            if (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "subprocess"
                and node.func.attr == "Popen"
            ):
                hardening["capability_spawn"] += 1
                replacement = copy.deepcopy(node)
                replacement.func = ast.Name(id="_spawn_worker", ctx=ast.Load())
                replacement.keywords.extend([
                    ast.keyword(arg="execution", value=ast.Name(id="execution", ctx=ast.Load())),
                    ast.keyword(
                        arg="manifest_sha256",
                        value=ast.Attribute(value=ast.Name(id="args", ctx=ast.Load()),
                                            attr="manifest_sha256", ctx=ast.Load()),
                    ),
                    ast.keyword(
                        arg="launcher_sha256",
                        value=ast.Subscript(
                            value=ast.Name(id="record", ctx=ast.Load()),
                            slice=ast.Constant("source_sha256"),
                            ctx=ast.Load(),
                        ),
                    ),
                    ast.keyword(arg="output_root", value=ast.Name(id="output", ctx=ast.Load())),
                    ast.keyword(arg="process_api", value=ast.Name(id="psutil", ctx=ast.Load())),
                ])
                return changed(node, replacement)
            if (
                isinstance(node.func, ast.Name)
                and node.func.id == "sha"
                and len(node.args) == 1
                and isinstance(node.args[0], ast.Name)
                and node.args[0].id == "worker_receipt"
            ):
                hardening["worker_receipt_bound_digest"] += 1
                replacement = copy.deepcopy(node)
                replacement.func = ast.Name(id="_last_snapshot_sha", ctx=ast.Load())
                return changed(node, replacement)
            return node

        def visit_BinOp(self, node):
            if (
                isinstance(node.op, ast.Div)
                and isinstance(node.left, ast.Name)
                and node.left.id == "HERE"
                and isinstance(node.right, ast.Constant)
                and node.right.value in routes
            ):
                name = node.right.value
                routes[name] += 1
                target = "generation_gate.py" if name == "resource_gate.py" else "runtime_adapter.py"
                return changed(
                    node,
                    ast.Call(
                        func=ast.Name(id="Path", ctx=ast.Load()),
                        args=[ast.Constant(str(HERE / target))],
                        keywords=[],
                    ),
                )
            return self.generic_visit(node)

        def visit_Constant(self, node):
            if isinstance(node.value, str) and node.value in LABELS:
                counts[node.value] += 1
                return changed(node, ast.Constant(LABELS[node.value]))
            return node

    derived = Route().visit(copy.deepcopy(original))
    ast.fix_missing_locations(derived)
    expected = {label: 1 for label in LABELS}
    expected["ORIGINAL_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW"] = 3
    expected["COMPLETED_EXTERNAL_RUN_PENDING_INDEPENDENT_REVIEW"] = 2
    expected["FAILED_OR_PARTIAL_ORIGINAL_RUN"] = 2
    if (
        counts != expected
        or routes != {"resource_gate.py": 2, "runtime_factory.py": 1}
        or here_count != 1
        or hardening != {
            "capability_spawn": 1,
            "execution_adoption": 1,
            "output_claim": 1,
            "worker_ticket_snapshot": 1,
            "worker_receipt_snapshot": 1,
            "worker_receipt_bound_digest": 1,
        }
    ):
        raise RuntimeError(
            "Unexpected S35 launcher route/label/hardening locations: "
            + str((counts, routes, here_count, hardening))
        )

    restored_keys = set()

    class Restore(ast.NodeTransformer):
        def generic_visit(self, node):
            key = (type(node).__name__, getattr(node, "lineno", None), getattr(node, "col_offset", None))
            if key in changes:
                old, derived_dump = changes[key]
                if ast.dump(node, include_attributes=False) != derived_dump:
                    raise RuntimeError("C2 launcher derivation subtree changed")
                restored_keys.add(key)
                return copy.deepcopy(old)
            return super().generic_visit(node)

    restored = Restore().visit(copy.deepcopy(derived))
    if len(restored_keys) != len(changes) or ast.dump(
        restored, include_attributes=False
    ) != ast.dump(original, include_attributes=False):
        raise RuntimeError("C2 launcher differs from S35 beyond the declared reversible edits")
    code = compile(derived, str(PARENT) + "[S47 C2 route/labels/security]", "exec")
    proof = {
        "parent_sha256": PARENT_SHA256,
        "label_counts": counts,
        "route_counts": routes,
        "here_assignments": here_count,
        "security_hardening_counts": hardening,
        "reversible_full_AST_equal": True,
        "original_budget_and_trace_boundary_math_unchanged": True,
        "row": "C2",
    }
    if compile_only:
        return proof
    caller = sys._getframe(1)
    require(
        caller.f_code is _run_supervisor.__code__
        and isinstance(caller.f_locals.get("execution"), HeldDirectory)
        and caller.f_locals["execution"].closed is False
        and caller.f_locals.get("control") is not None,
        "Executable derived code is available only to the active outer supervisor",
    )
    caller.f_locals["execution"].validate()
    caller.f_locals["control"].validate()
    return code, proof


def _run_supervisor(args):
    """Own the only attempt, monitor, capability, watchdog, and final seal."""
    require(Path(args.execution_directory) == EXECUTION and args.worker is False,
            "Supervisor is not bound to canonical execution_01")
    launcher_sha = snapshot_sha(Path(__file__).absolute())
    gate_module = load_bound_snapshot(GATE, {str(GATE): GATE_SHA256})
    control = gate_module.open_launch_control_lease(
        Path(args.manifest), args.manifest_sha256
    )
    here = HeldDirectory.open(HERE)
    execution = None
    output = None
    watchdog = {"pid": None, "life_write": None, "ack_read": None, "handle": None}
    parent_returncode = 1
    final_error = None
    terminal_committed = False
    terminal_file = None
    try:
        control.validate()
        here.validate()
        require(not entry_exists(here, EXECUTION.name),
                "Canonical execution_01 single-attempt lease is already occupied")
        require(
            not entry_exists(here, WATCHDOG_FALLBACK_RECEIPT)
            and not entry_exists(here, SUPERVISOR_FAILURE_FALLBACK),
            "A fixed prior lifecycle-failure receipt makes the attempt non-fresh",
        )
        require(not os.path.lexists(gate_module.C2_OUTPUT),
                "C2 scientific output root is already occupied")
        os.mkdir(EXECUTION.name, mode=0o700, dir_fd=here.fd)
        execution = HeldDirectory.open(EXECUTION)
        require(execution.validate() == {
            "device": os.fstat(execution.fd).st_dev,
            "inode": os.fstat(execution.fd).st_ino,
        }, "Execution directory identity was not retained")
        attempt_started = {
            "schema": "s47-c2-supervisor-attempt-start-v1",
            "status": "SINGLE_ATTEMPT_CLAIMED_BEFORE_PARENT_ENTRY",
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "supervisor_pid": os.getpid(),
            "manifest_sha256": args.manifest_sha256,
            "launcher_sha256": launcher_sha,
            "execution_directory": str(EXECUTION),
            "execution_identity": dict(execution.identity),
            "retry_permitted": False,
        }
        started_sha = write_new_json_at(execution.fd, SUPERVISOR_STARTED, attempt_started)
        provisional_sha = write_new_json_at(
            execution.fd,
            SUPERVISOR_PROVISIONAL,
            {
                "schema": "s47-c2-supervisor-terminal-provisional-v1",
                "status": "PENDING_NOT_A_SUCCESS_RECORD",
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "supervisor_pid": os.getpid(),
                "manifest_sha256": args.manifest_sha256,
                "launcher_sha256": launcher_sha,
                "attempt_started_sha256": started_sha,
                "execution_directory": str(EXECUTION),
                "execution_identity": dict(execution.identity),
                "retry_permitted": False,
                "standalone_success": False,
            },
        )

        code, derivation = derive_launcher()
        snapshot_digests = {}
        capability_state = {
            "issued": False,
            "consumed": False,
            "supervisor_pid": os.getpid(),
            "token": None,
            "secret": None,
        }
        pending_ticket = None

        def adopt_execution(path):
            require(Path(path) == EXECUTION, "Derived parent selected another execution directory")
            require(execution.validate() == execution.identity,
                    "Execution lease changed before parent adoption")

        def claim_output(path):
            nonlocal output
            require(Path(path) == gate_module.C2_OUTPUT,
                    "Derived parent selected another scientific output root")
            require(output is None, "Scientific output root was already claimed")
            parent_handle = HeldDirectory.open(Path(path).parent)
            try:
                parent_handle.validate()
                require(not entry_exists(parent_handle, Path(path).name),
                        "Scientific output single-attempt lease is occupied")
                os.mkdir(Path(path).name, mode=0o700, dir_fd=parent_handle.fd)
            finally:
                parent_handle.close()
            output = HeldDirectory.open(path)
            output.validate()

        def bound_write_new(path, value):
            nonlocal pending_ticket
            candidate = Path(path).absolute()
            document = copy.deepcopy(value)
            if candidate.parent == EXECUTION:
                execution.validate()
                if candidate.name == "launch_ticket.json":
                    require(output is not None and output.validate() == output.identity,
                            "Launch ticket requires the held scientific output inode")
                    require(
                        pending_ticket is None
                        and not entry_exists(execution, "launch_ticket.json")
                        and set(document) == {
                            "parent_pid", "manifest_sha256", "launcher_sha256",
                            "output_root", "created_utc",
                        }
                        and document.get("parent_pid") == capability_state["supervisor_pid"],
                        "Derived parent launch-ticket request is malformed or repeated",
                    )
                    pending_ticket = {
                        "manifest_sha256": document["manifest_sha256"],
                        "launcher_sha256": document["launcher_sha256"],
                        "output_root": document["output_root"],
                        "output_identity": dict(output.identity),
                        "execution_identity": dict(execution.identity),
                        "parent_requested_utc": document["created_utc"],
                    }
                    return hashlib.sha256(canonical(pending_ticket)).hexdigest()
                if candidate.name == "worker_receipt.json":
                    complete = (
                        document.get("status")
                        == "C2_BASELINE_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW"
                    )
                    consumption = gate_module.seal_active_resource_session(
                        require_complete=complete
                    )
                    if consumption is not None:
                        document["scientific_consumption_binding"] = consumption
                document.setdefault("execution_identity", dict(execution.identity))
                return write_new_json_at(execution.fd, candidate.name, document)
            if output is not None and candidate.parent == gate_module.C2_OUTPUT:
                output.validate()
                return write_new_json_at(output.fd, candidate.name, document)
            raise RuntimeError("Derived launcher attempted an unbound create-only JSON path: " + str(candidate))

        def bound_ticket(execution_path, manifest_sha256, source_sha256):
            require(Path(execution_path) == EXECUTION, "Worker ticket path is not canonical")
            ticket, digest = read_json_at(execution.fd, "launch_ticket.json", "Parent launch ticket")
            snapshot_digests["launch_ticket.json"] = digest
            return translate_worker_ticket(
                ticket,
                manifest_sha256=manifest_sha256,
                launcher_sha256=source_sha256,
                supervisor_pid=capability_state["supervisor_pid"],
                direct_parent_pid=os.getppid(),
                worker_pid=os.getpid(),
                output_root=str(gate_module.C2_OUTPUT),
                output_identity=output.identity,
                execution_identity=execution.identity,
            )

        def bound_worker_receipt(path):
            require(Path(path) == EXECUTION / "worker_receipt.json",
                    "Parent attempted another worker receipt path")
            document, digest = read_json_at(
                execution.fd, "worker_receipt.json", "Worker terminal receipt"
            )
            snapshot_digests["worker_receipt.json"] = digest
            return document

        def bound_last_sha(path):
            name = Path(path).name
            require(name in snapshot_digests, "No bound descriptor digest for " + name)
            return snapshot_digests[name]

        namespace = {
            "__file__": str(Path(__file__).absolute()),
            "__name__": "_s47_c2_monitored_derived_runtime",
            "_read_bound_launch_ticket": bound_ticket,
            "_read_worker_receipt": bound_worker_receipt,
            "_last_snapshot_sha": bound_last_sha,
            "_adopt_execution": adopt_execution,
            "_claim_output": claim_output,
        }
        exec(code, namespace)
        namespace["sha"] = snapshot_sha
        namespace["load_bound"] = lambda path, identities: (
            gate_module
            if Path(path).absolute() == GATE
            and identities.get(str(GATE)) == GATE_SHA256
            else load_bound_snapshot(path, identities)
        )
        namespace["read_frozen"] = lambda path, expected: control.frozen_manifest(
            Path(path), expected, namespace
        )
        namespace["write_new"] = bound_write_new
        raw_parent = namespace["parent"]
        raw_worker = namespace["worker"]

        def consume_capability(worker_args, token):
            require(Path(worker_args.execution_directory) == EXECUTION and worker_args.worker is True,
                    "Worker is not bound to canonical execution_01")
            record, record_sha = read_json_at(
                execution.fd, CAPABILITY_RECORD, "Worker capability record"
            )
            expected_secret = hashlib.sha256(capability_state["secret"]).hexdigest()
            require(
                token is capability_state["token"]
                and capability_state["issued"] is True
                and capability_state["consumed"] is False
                and isinstance(capability_state["secret"], bytes)
                and len(capability_state["secret"]) == 32
                and set(record) == {
                    "schema", "status", "created_utc", "supervisor_pid",
                    "watchdog_pid", "worker_pid", "manifest_sha256",
                    "launcher_sha256", "execution_directory",
                    "execution_identity", "output_root", "output_identity",
                    "secret_sha256", "capability_transport",
                    "liveness_transport", "public_worker_cli", "reusable",
                }
                and record.get("schema") == "s47-c2-worker-capability-record-v2"
                and record.get("status") == "ISSUED_ONCE_INSIDE_ACTIVE_MONITORED_PARENT"
                and record.get("supervisor_pid") == capability_state["supervisor_pid"]
                and record.get("watchdog_pid") == os.getppid()
                and record.get("worker_pid") == os.getpid()
                and record.get("manifest_sha256") == worker_args.manifest_sha256
                and record.get("launcher_sha256") == launcher_sha
                and record.get("execution_directory") == str(EXECUTION)
                and record.get("execution_identity") == execution.identity
                and record.get("output_root") == str(gate_module.C2_OUTPUT)
                and record.get("output_identity") == output.identity
                and record.get("secret_sha256") == expected_secret
                and record.get("public_worker_cli") is False
                and record.get("reusable") is False
                and not entry_exists(execution, CAPABILITY_CONSUMED),
                "Worker capability is forged, redirected, or already consumed",
            )
            capability_state["consumed"] = True
            consumed = {
                "schema": "s47-c2-worker-capability-consumption-v2",
                "status": "CONSUMED_ONCE_BEFORE_WORKER_GATE",
                "consumed_utc": datetime.now(timezone.utc).isoformat(),
                "supervisor_pid": capability_state["supervisor_pid"],
                "watchdog_pid": os.getppid(),
                "worker_pid": os.getpid(),
                "manifest_sha256": worker_args.manifest_sha256,
                "launcher_sha256": launcher_sha,
                "execution_directory": str(EXECUTION),
                "execution_identity": dict(execution.identity),
                "output_root": str(gate_module.C2_OUTPUT),
                "output_identity": dict(output.identity),
                "capability_record_sha256": record_sha,
                "secret_sha256": expected_secret,
                "reusable": False,
            }
            write_new_json_at(execution.fd, CAPABILITY_CONSUMED, consumed)

        def guarded_worker(worker_args, token):
            consume_capability(worker_args, token)
            gate_module.adopt_inherited_output_directory(
                gate_module.C2_OUTPUT,
                output.duplicate_chain(),
                dict(output.identity),
            )
            return raw_worker(worker_args)

        def spawn_worker(command, *, cwd, env, stdout, stderr, start_new_session,
                         execution: Path, manifest_sha256, launcher_sha256,
                         output_root, process_api):
            """Private closure: mint only after the monitored parent reaches Popen."""
            require(capability_state["issued"] is False and capability_state["token"] is None,
                    "The single worker capability was already issued")
            require(Path(execution) == EXECUTION and output is not None,
                    "Worker spawn requires the held execution and output leases")
            require(execution_identity == execution_handle.identity,
                    "Worker spawn execution binding changed")
            require(output.validate() == output.identity,
                    "Output root changed before worker spawn")
            require(process_api is not None and hasattr(process_api, "Process"),
                    "Derived parent did not inject its reviewed process API")
            internal = parse_exact_arguments(command[3:], internal=True)
            require(
                command[:3]
                == [str(ROOT / ".venv-cut3r/bin/python"), "-B", str(Path(__file__).absolute())]
                and internal.manifest_sha256 == manifest_sha256 == args.manifest_sha256
                and launcher_sha256 == launcher_sha
                and Path(output_root) == gate_module.C2_OUTPUT
                and start_new_session is True,
                "Derived worker command or frozen bindings changed",
            )
            capability_state["token"] = object()
            capability_state["secret"] = secrets.token_bytes(32)
            capability_state["issued"] = True
            ready_read, ready_write = os.pipe()
            life_read, life_write = os.pipe()
            ack_read, ack_write = os.pipe()
            status_read, status_write = os.pipe()
            info_read, info_write = os.pipe()
            binding = {
                "supervisor_pid": os.getpid(),
                "manifest_sha256": manifest_sha256,
                "launcher_sha256": launcher_sha,
                "execution_identity": dict(execution_handle.identity),
                "output_root": str(gate_module.C2_OUTPUT),
                "output_identity": dict(output.identity),
            }
            watchdog_pid = os.fork()
            if watchdog_pid == 0:
                worker_pid = None
                worker_group_ready = False
                try:
                    for descriptor in (ready_write, life_write, ack_read, status_read, info_read):
                        os.close(descriptor)
                    signal.signal(signal.SIGTERM, signal.SIG_DFL)
                    signal.signal(signal.SIGINT, signal.SIG_DFL)
                    os.setsid()
                    group_ready_read, group_ready_write = os.pipe()
                    worker_pid = os.fork()
                    if worker_pid == 0:
                        exit_code = 1
                        try:
                            for descriptor in (
                                group_ready_read, life_read, ack_write,
                                status_write, info_write,
                            ):
                                os.close(descriptor)
                            os.setsid()
                            require(os.write(group_ready_write, b"G") == 1,
                                    "Worker could not publish process-group readiness")
                            os.close(group_ready_write)
                            os.chdir(cwd)
                            os.environ.clear()
                            os.environ.update(env)
                            os.dup2(stdout.fileno(), 1)
                            os.dup2(stderr.fileno(), 2)
                            require(os.read(ready_read, 1) == b"1",
                                    "Active monitored parent did not issue the worker capability")
                            os.close(ready_read)
                            exit_code = int(guarded_worker(internal, capability_state["token"]))
                        except BaseException:
                            traceback.print_exc()
                        finally:
                            os._exit(exit_code)
                    os.close(ready_read)
                    os.close(group_ready_write)
                    require(os.read(group_ready_read, 1) == b"G",
                            "Worker did not establish its owned session")
                    worker_group_ready = True
                    os.close(group_ready_read)
                    info = canonical({"watchdog_pid": os.getpid(), "worker_pid": worker_pid}) + b"\n"
                    require(os.write(info_write, info) == len(info),
                            "Watchdog could not publish the owned worker identity")
                    os.close(info_write)
                    for stream in (stdout, stderr):
                        try:
                            os.close(stream.fileno())
                        except OSError:
                            pass
                    watchdog_fd = os.dup(execution_handle.fd)
                    watchdog_here_fd = os.dup(here.fd)
                    _watchdog_loop(
                        life_read, ack_write, status_write, worker_pid,
                        watchdog_fd, watchdog_here_fd, binding, process_api
                    )
                except BaseException:
                    traceback.print_exc()
                    if worker_pid is not None:
                        try:
                            if worker_group_ready:
                                _terminate_and_reap_owned_group(
                                    worker_pid, process_api=process_api,
                                    descendant_ledger={},
                                )
                            else:
                                os.kill(worker_pid, signal.SIGKILL)
                                os.waitpid(worker_pid, 0)
                        except BaseException:
                            pass
                    os._exit(5)
            watchdog.update(
                pid=watchdog_pid, life_write=life_write, ack_read=ack_read, handle=None
            )
            process = None
            ready_write_open = True
            info_read_open = True
            status_read_owned = True
            try:
                for descriptor in (ready_read, life_read, ack_write, status_write, info_write):
                    os.close(descriptor)
                readable, _, _ = select.select([info_read], [], [], 5.0)
                require(readable, "Watchdog did not publish an owned worker within five seconds")
                info_payload = b""
                while b"\n" not in info_payload:
                    chunk = os.read(info_read, 1024)
                    require(chunk, "Watchdog closed before publishing the worker identity")
                    info_payload += chunk
                os.close(info_read)
                info_read_open = False
                info_line, info_remainder = info_payload.split(b"\n", 1)
                info = json.loads(info_line)
                require(
                    not info_remainder
                    and set(info) == {"watchdog_pid", "worker_pid"}
                    and info["watchdog_pid"] == watchdog_pid
                    and isinstance(info["worker_pid"], int)
                    and info["worker_pid"] > 1,
                    "Watchdog published a malformed worker identity",
                )
                worker_pid = info["worker_pid"]
                process = ForkWorkerProcess(worker_pid, watchdog_pid, status_read)
                status_read_owned = False
                watchdog["handle"] = process
                require(pending_ticket is not None,
                        "Derived parent did not request its launch ticket before spawn")
                launch_ticket = {
                    "schema": "s47-c2-worker-launch-ticket-v2",
                    "status": "BOUND_AFTER_WATCHDOG_OWNERSHIP",
                    "supervisor_pid": os.getpid(),
                    "watchdog_pid": watchdog_pid,
                    "worker_pid": worker_pid,
                    "manifest_sha256": pending_ticket["manifest_sha256"],
                    "launcher_sha256": pending_ticket["launcher_sha256"],
                    "output_root": pending_ticket["output_root"],
                    "output_identity": pending_ticket["output_identity"],
                    "execution_identity": pending_ticket["execution_identity"],
                    "parent_requested_utc": pending_ticket["parent_requested_utc"],
                    "created_utc": datetime.now(timezone.utc).isoformat(),
                    "direct_worker_parent": "WATCHDOG_PID",
                }
                write_new_json_at(
                    execution_handle.fd, "launch_ticket.json", launch_ticket
                )
                record = {
                "schema": "s47-c2-worker-capability-record-v2",
                "status": "ISSUED_ONCE_INSIDE_ACTIVE_MONITORED_PARENT",
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "supervisor_pid": os.getpid(),
                "watchdog_pid": watchdog_pid,
                "worker_pid": worker_pid,
                "manifest_sha256": manifest_sha256,
                "launcher_sha256": launcher_sha,
                "execution_directory": str(EXECUTION),
                "execution_identity": dict(execution_handle.identity),
                "output_root": str(gate_module.C2_OUTPUT),
                "output_identity": dict(output.identity),
                "secret_sha256": hashlib.sha256(capability_state["secret"]).hexdigest(),
                "capability_transport": "PRIVATE_PARENT_CLOSURE_AND_FORK_INHERITANCE",
                "liveness_transport": "DIRECT_PARENT_WATCHDOG_PIPE_HELD_FOR_FULL_MONITOR_LIFETIME",
                "public_worker_cli": False,
                "reusable": False,
                }
                write_new_json_at(execution_handle.fd, CAPABILITY_RECORD, record)
                require(os.write(ready_write, b"1") == 1,
                        "Worker capability synchronization write failed")
                os.close(ready_write)
                ready_write_open = False
                return process
            except BaseException:
                if ready_write_open:
                    try:
                        os.close(ready_write)
                    except OSError:
                        pass
                if info_read_open:
                    try:
                        os.close(info_read)
                    except OSError:
                        pass
                if status_read_owned:
                    try:
                        os.close(status_read)
                    except OSError:
                        pass
                if watchdog["life_write"] is not None:
                    try:
                        os.close(watchdog["life_write"])
                    except OSError:
                        pass
                    watchdog["life_write"] = None
                if process is not None:
                    process._close_status()
                try:
                    if process is None:
                        os.waitpid(watchdog_pid, 0)
                    else:
                        process.wait_watchdog(timeout=10)
                except (OSError, subprocess.TimeoutExpired):
                    pass
                if watchdog["ack_read"] is not None:
                    try:
                        os.close(watchdog["ack_read"])
                    except OSError:
                        pass
                    watchdog["ack_read"] = None
                watchdog["pid"] = None
                watchdog["handle"] = None
                raise

        execution_handle = execution
        execution_identity = dict(execution.identity)
        namespace["_spawn_worker"] = spawn_worker
        control.validate()
        parent_returncode = int(raw_parent(args))

        if watchdog["pid"] is not None:
            require(os.write(watchdog["life_write"], b"S") == 1,
                    "Could not close the watchdog protocol normally")
            os.close(watchdog["life_write"])
            watchdog["life_write"] = None
            acknowledgement = os.read(watchdog["ack_read"], 1)
            os.close(watchdog["ack_read"])
            watchdog["ack_read"] = None
            watchdog_status = watchdog["handle"].wait_watchdog(timeout=10)
            require(
                acknowledgement == b"1" and watchdog_status == 0,
                "Independent watchdog did not confirm registered-descendant cleanup",
            )
            watchdog_receipt, watchdog_sha = read_json_at(
                execution.fd, WATCHDOG_RECEIPT, "Worker watchdog receipt"
            )
            require(
                watchdog_receipt.get("status")
                == "WATCHDOG_CONFIRMED_REGISTERED_DESCENDANTS_GONE"
                and watchdog_receipt.get("cleanup_complete") is True
                and watchdog_receipt.get("all_registered_descendants_gone") is True
                and watchdog_receipt.get("supervisor_completed_protocol") is True
                and watchdog_receipt.get("supervisor_liveness_lost") is False
                and watchdog_receipt.get("canonical_execution_identity_at_close") is True
                and watchdog_receipt.get("worker_returncode")
                == watchdog["handle"].returncode
                and output is not None
                and watchdog_receipt.get("output_identity") == output.identity,
                "Watchdog terminal receipt is not the registered no-survivor state",
            )
        else:
            watchdog_sha = None

        control_identity = control.validate()
        execution.validate()
        if output is not None:
            output.validate()
        parent_receipt, parent_receipt_sha = read_json_at(
            execution.fd, "receipt.json", "Derived parent terminal receipt"
        )
        worker_terminal, worker_terminal_sha = read_json_at(
            execution.fd, "worker_receipt.json", "Worker terminal receipt for outer seal"
        )
        consumption = worker_terminal.get("scientific_consumption_binding", {})
        success = (
            parent_returncode == 0
            and parent_receipt.get("status")
            == "C2_BASELINE_EXTERNAL_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW"
            and watchdog_sha is not None
            and consumption.get("all_required_resources_consumed") is True
            and output is not None
            and consumption.get("output_identity") == output.identity
        )
        terminal_commit = {
            "schema": "s47-c2-external-supervisor-terminal-commit-v2",
            "status": "COMMIT_CANDIDATE_REQUIRES_OUTER_RETURN_AND_NO_ROOT_FAILURE",
            "outcome_status": (
                "RUN_RETURNED_PENDING_INDEPENDENT_REVIEW"
                if success else "FAILED_OR_PARTIAL_ATTEMPT"
            ),
            "standalone_success": False,
            "completed_utc": datetime.now(timezone.utc).isoformat(),
            "supervisor_pid": os.getpid(),
            "manifest_sha256": args.manifest_sha256,
            "launcher_sha256": launcher_sha,
            "derivation_proof": derivation,
            "attempt_started_sha256": started_sha,
            "terminal_provisional_sha256": provisional_sha,
            "execution_directory": str(EXECUTION),
            "execution_identity": dict(execution.identity),
            "output_root": str(gate_module.C2_OUTPUT),
            "output_identity": None if output is None else dict(output.identity),
            "control_plane_identity": control_identity,
            "parent_returncode": parent_returncode,
            "parent_receipt_sha256": parent_receipt_sha,
            "worker_receipt_sha256": worker_terminal_sha,
            "scientific_consumption_binding": consumption,
            "watchdog_receipt_sha256": watchdog_sha,
            "retry_permitted": False,
            "quality_status": "NOT_EVALUATED",
            "method_or_novelty_status": "NOT_EVALUATED",
        }
        terminal_file = HeldCreatedJSON.create(
            execution.fd, SUPERVISOR_COMMIT, terminal_commit
        )
        terminal_file.sync_directory()
        terminal_file.validate()
        control_identity_after_commit = control.validate()
        require(control_identity_after_commit == control_identity,
                "Launch-control identity changed during terminal commit")
        here.validate()
        execution.validate()
        if output is not None:
            output.validate()
        terminal_file.validate()
        require(not entry_exists(here, SUPERVISOR_FAILURE_FALLBACK),
                "A root-level supervisor failure receipt already exists")
        here.validate()
        execution.validate()
        terminal_committed = True
        return 0 if success else 1
    except BaseException as error:
        final_error = error
        if watchdog["life_write"] is not None:
            try:
                os.close(watchdog["life_write"])
            except OSError:
                pass
            watchdog["life_write"] = None
        if watchdog["pid"] is not None:
            try:
                watchdog["handle"].wait_watchdog(timeout=10)
            except OSError:
                pass
            except subprocess.TimeoutExpired:
                pass
        if execution is not None and not terminal_committed:
            try:
                failure = {
                    "schema": "s47-c2-external-supervisor-root-failure-v2",
                    "status": "SUPERVISOR_TERMINAL_COMMIT_NOT_ACCEPTED",
                    "completed_utc": datetime.now(timezone.utc).isoformat(),
                    "supervisor_pid": os.getpid(),
                    "manifest_sha256": args.manifest_sha256,
                    "launcher_sha256": launcher_sha,
                    "execution_directory": str(EXECUTION),
                    "execution_identity": dict(execution.identity),
                    "terminal_commit_may_exist": entry_exists(
                        execution, SUPERVISOR_COMMIT
                    ),
                    "terminal_commit_is_standalone_success": False,
                    "error_type": type(error).__name__,
                    "error": str(error),
                    "traceback": traceback.format_exc(),
                    "retry_permitted": False,
                    "quality_status": "NOT_EVALUATED",
                    "method_or_novelty_status": "NOT_EVALUATED",
                }
                if not entry_exists(here, SUPERVISOR_FAILURE_FALLBACK):
                    write_new_json_at(
                        here.fd, SUPERVISOR_FAILURE_FALLBACK, failure
                    )
            except BaseException:
                pass
        return 1
    finally:
        for descriptor_name in ("life_write", "ack_read"):
            descriptor = watchdog.get(descriptor_name)
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
        if watchdog.get("handle") is not None:
            watchdog["handle"]._close_status()
        if terminal_file is not None:
            terminal_file.close()
        if output is not None:
            output.close()
        if execution is not None:
            execution.close()
        here.close()
        control.close()


def main():
    argv = sys.argv[1:]
    args = parse_exact_arguments(argv, internal=False)
    def interrupted(signum, frame):
        raise KeyboardInterrupt("Launcher/worker received signal " + str(signum))
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    return _run_supervisor(args)


if __name__ == "__main__":
    raise SystemExit(main())
