#!/usr/bin/env python3
"""External supervisor and atomic terminal sealer for the S45B C1 camera guard.

The worker can write only pending evidence.  This supervisor owns the one-use
attempt, observes worker termination and resource boundaries, revalidates every
canonical evidence inode, and is the sole source of an authoritative PASS seal.
Synthetic modes operate only inside isolated temporary directories.
"""
from __future__ import annotations

import argparse
import ast
import ctypes
from datetime import datetime, timezone
import errno
import fcntl
import hashlib
import hmac
import json
import os
from pathlib import Path
import platform
import resource
import secrets
import selectors
import signal
import stat
import subprocess
import sys
import tempfile
import time
import traceback
import types


HERE = Path(__file__).resolve().parent
SELF = Path(__file__).resolve()
WORKER = HERE / "camera_guard.py"
PYTHON_EXECUTABLE = Path(sys.executable).resolve()
FORMAL_OUT = HERE / "execution_01"
LOCK = HERE / ".c1_numeric_camera_guard.lock"
LOCK_STAGING = HERE / ".c1_numeric_camera_guard.lock.staging"
BINDING = HERE / "C1_CAMERA_GUARD_BINDING_V10.json"
BINDING_REVIEW = HERE / "BINDING_REVIEW_V10.json"
PRIMARY_REVIEW = HERE / "SOURCE_REVIEW_PRIMARY_V10.json"
ADVERSARIAL_REVIEW = HERE / "SOURCE_REVIEW_ADVERSARIAL_V10.json"
GOVERNANCE_RECEIPT = HERE / "GOVERNANCE_ATTESTATION_V10.json"

REPORT_NAME = "report.json"
WORKER_RECEIPT_NAME = "worker_receipt.json"
WORKER_FAILURE_NAME = "worker_postwrite_failure.json"
SUPERVISOR_RECEIPT_NAME = "supervisor_receipt.json"
BARRIER_NAME = "terminalization_barrier.json"
TERMINAL_SEAL_NAME = "terminal_pass_candidate.json"
TERMINAL_SEAL_STAGING_NAME = ".terminal_pass_candidate.staging"
TERMINAL_FAILURE_NAME = "terminal_seal_failure.json"

TIME_LIMIT_SECONDS = 300.0
CPU_LIMIT_SECONDS = 120
MAX_WORKER_RSS_BYTES = 2 * 1024 * 1024 * 1024
MAX_STDOUT_BYTES = 65536
MAX_STDERR_BYTES = 65536
MAX_ARTIFACT_BYTES = 64 * 1024 * 1024
HEX_LENGTH = 64
SANDBOX_EXEC = Path("/usr/bin/sandbox-exec")
SANDBOX_PROFILE = "(version 1) (allow default) (deny process-fork)"
DARWIN_LIBPROC = "/usr/lib/libproc.dylib"
RUSAGE_INFO_V4 = 4
MEMORY_SAMPLE_INTERVAL_SECONDS = 0.02
CAPABILITY_PROBE_BYTES = 8 * 1024 * 1024
ARTIFACT_AUTH_DOMAIN = b"S45B-C1-V10-PREBOUND-ARTIFACT"


class SupervisorTermination(RuntimeError):
    pass


class InjectedSyntheticFailure(RuntimeError):
    pass


_RUSAGE_V4_FIELDS = (
    "user_time", "system_time", "pkg_idle_wkups", "interrupt_wkups",
    "pageins", "wired_size", "resident_size", "phys_footprint",
    "proc_start_abstime", "proc_exit_abstime", "child_user_time",
    "child_system_time", "child_pkg_idle_wkups", "child_interrupt_wkups",
    "child_pageins", "child_elapsed_abstime", "diskio_bytesread",
    "diskio_byteswritten", "cpu_time_qos_default",
    "cpu_time_qos_maintenance", "cpu_time_qos_background",
    "cpu_time_qos_utility", "cpu_time_qos_legacy",
    "cpu_time_qos_user_initiated", "cpu_time_qos_user_interactive",
    "billed_system_time", "serviced_system_time", "logical_writes",
    "lifetime_max_phys_footprint", "instructions", "cycles",
    "billed_energy", "serviced_energy", "interval_max_phys_footprint",
    "runnable_time",
)


class DarwinRusageInfoV4(ctypes.Structure):
    _fields_ = [("uuid", ctypes.c_uint8 * 16)] + [
        (name, ctypes.c_uint64) for name in _RUSAGE_V4_FIELDS
    ]


def require(value, message):
    if not value:
        raise ValueError(message)


def utc():
    return datetime.now(timezone.utc).isoformat()


def encoded_json(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
            + "\n").encode("utf-8")


def canonical(value):
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def valid_sha(value):
    return (
        type(value) is str and len(value) == HEX_LENGTH
        and all(ch in "0123456789abcdef" for ch in value)
    )


def darwin_process_usage(pid):
    """Read kernel process memory/accounting for one exact live Darwin PID."""
    require(platform.system() == "Darwin", "V10 requires the reviewed Darwin containment path")
    library = ctypes.CDLL(DARWIN_LIBPROC, use_errno=True)
    function = library.proc_pid_rusage
    function.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p]
    function.restype = ctypes.c_int
    value = DarwinRusageInfoV4()
    ctypes.set_errno(0)
    result = function(int(pid), RUSAGE_INFO_V4, ctypes.byref(value))
    if result != 0:
        number = ctypes.get_errno()
        raise OSError(number, os.strerror(number))
    return {
        "process_uuid": bytes(value.uuid).hex(),
        "resident_size_bytes": int(value.resident_size),
        "phys_footprint_bytes": int(value.phys_footprint),
        "lifetime_max_phys_footprint_bytes": int(value.lifetime_max_phys_footprint),
        "user_time_ns": int(value.user_time),
        "system_time_ns": int(value.system_time),
    }


def inode_identity(value):
    return value.st_dev, value.st_ino, value.st_mode


def stat_record(value):
    if stat.S_ISREG(value.st_mode):
        kind = "regular"
    elif stat.S_ISDIR(value.st_mode):
        kind = "directory"
    elif stat.S_ISLNK(value.st_mode):
        kind = "symlink"
    else:
        kind = "other"
    return {
        "device": value.st_dev,
        "inode": value.st_ino,
        "mode": value.st_mode,
        "nlink": value.st_nlink,
        "type": kind,
        "size": value.st_size,
        "mtime_ns": value.st_mtime_ns,
        "ctime_ns": value.st_ctime_ns,
    }


def read_exact_fd(fd, size):
    require(type(size) is int and 0 <= size <= MAX_ARTIFACT_BYTES,
            "Artifact size exceeds the fixed supervisor scope")
    pieces = []
    offset = 0
    while offset < size:
        block = os.pread(fd, min(1024 * 1024, size - offset), offset)
        require(bool(block), "Artifact has unexpected EOF")
        pieces.append(block)
        offset += len(block)
    require(os.pread(fd, 1, size) == b"", "Artifact grew beyond its lstat size")
    return b"".join(pieces)


def verify_worker_no_process_creation(source):
    """Statically narrow the formal worker to one OS process."""
    tree = ast.parse(source.decode("utf-8"), filename=str(WORKER))
    forbidden_imports = {"subprocess", "multiprocessing", "ctypes", "pty"}
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    require(not imported.intersection(forbidden_imports),
            "Formal worker imports a process-creation escape module")
    forbidden_os_calls = {
        "fork", "forkpty", "posix_spawn", "posix_spawnp", "popen", "system",
        "spawnl", "spawnle", "spawnlp", "spawnlpe", "spawnv", "spawnve",
        "spawnvp", "spawnvpe", "execl", "execle", "execlp", "execlpe",
        "execv", "execve", "execvp", "execvpe",
    }
    observed = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        if (isinstance(function, ast.Attribute) and isinstance(function.value, ast.Name)
                and function.value.id == "os" and function.attr in forbidden_os_calls):
            observed.append("os." + function.attr)
        if isinstance(function, ast.Name) and function.id in {"Popen", "run", "call", "check_call"}:
            observed.append(function.id)
    require(not observed, "Formal worker contains a process-creation call: " + repr(observed))
    audit = {
        "forbidden_import_roots_absent": sorted(forbidden_imports),
        "forbidden_os_calls_absent": sorted(forbidden_os_calls),
        "observed_process_creation_calls": observed,
    }
    return {"status": "PASS_EXACT_WORKER_NO_PROCESS_CREATION_AST", "audit_sha256": sha256_bytes(canonical(audit))}


def executable_snapshot(path):
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        held = os.fstat(fd)
        named = os.stat(path, follow_symlinks=False)
        require(stat.S_ISREG(held.st_mode) and stat_record(held) == stat_record(named)
                and held.st_nlink == 1 and os.access(path, os.X_OK),
                "Containment executable is not one stable executable regular file")
        body = read_exact_fd(fd, held.st_size)
        after = os.fstat(fd)
        require(stat_record(held) == stat_record(after),
                "Containment executable changed while hashing")
        return {
            "path": str(path), "sha256": sha256_bytes(body), "bytes": len(body),
            "lstat": stat_record(held),
        }
    finally:
        os.close(fd)


def load_worker_same_fd(expected_sha256=None):
    require(expected_sha256 is None or valid_sha(expected_sha256),
            "Worker SHA-256 is malformed")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(WORKER, flags)
    try:
        before = os.fstat(fd)
        path_before = os.stat(WORKER, follow_symlinks=False)
        require(
            stat.S_ISREG(before.st_mode) and stat.S_ISREG(path_before.st_mode)
            and before.st_nlink == path_before.st_nlink == 1
            and stat_record(before) == stat_record(path_before),
            "Worker source is not one stable single-link regular file",
        )
        source = read_exact_fd(fd, before.st_size)
        digest = sha256_bytes(source)
        require(expected_sha256 is None or digest == expected_sha256,
                "Worker source SHA-256 differs")
        after = os.fstat(fd)
        path_after = os.stat(WORKER, follow_symlinks=False)
        require(stat_record(before) == stat_record(after) == stat_record(path_after),
                "Worker source changed while loading")
    except BaseException:
        os.close(fd)
        raise
    no_process_audit = verify_worker_no_process_creation(source)
    module = types.ModuleType("_s45b_c1_camera_worker_exact")
    module.__file__ = str(WORKER)
    code = compile(source.decode("utf-8"), str(WORKER), "exec")
    exec(code, module.__dict__)
    module._held_source_lease = {
        "fd": fd,
        "source": source,
        "code": code,
        "identity": inode_identity(before),
        "bytes": len(source),
        "sha256": digest,
    }
    return module, {
        "path": str(WORKER),
        "sha256": digest,
        "bytes": len(source),
        "lstat": stat_record(before),
        "no_process_creation_audit": no_process_audit,
    }


def verify_loaded_worker_lease(worker, expected_sha256=None):
    lease = getattr(worker, "_held_source_lease", None)
    require(type(lease) is dict and type(lease.get("fd")) is int,
            "Loaded worker has no retained source FD")
    expected = lease["sha256"] if expected_sha256 is None else expected_sha256
    held = os.fstat(lease["fd"])
    named = os.stat(WORKER, follow_symlinks=False)
    require(
        stat.S_ISREG(held.st_mode) and stat.S_ISREG(named.st_mode)
        and held.st_nlink == named.st_nlink == 1
        and inode_identity(held) == lease["identity"] == inode_identity(named)
        and held.st_size == named.st_size == lease["bytes"],
        "Retained worker source FD/path identity changed",
    )
    body = read_exact_fd(lease["fd"], lease["bytes"])
    require(body == lease["source"] and sha256_bytes(body) == expected,
            "Retained worker bytes differ from reviewed bytes")
    return {
        "sha256": expected,
        "bytes": lease["bytes"],
        "device": held.st_dev,
        "inode": held.st_ino,
        "mode": held.st_mode,
    }


def close_loaded_worker_lease(worker):
    lease = getattr(worker, "_held_source_lease", None)
    if isinstance(lease, dict) and type(lease.get("fd")) is int and lease["fd"] >= 0:
        os.close(lease["fd"])
        lease["fd"] = -1


def regular_record_at(directory_fd, directory_path, name, fd, expected_sha256, nlink):
    require(type(name) is str and "/" not in name and name not in ("", ".", ".."),
            "Artifact name is not one fixed directory entry")
    held = os.fstat(fd)
    path_now = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    require(
        stat.S_ISREG(held.st_mode) and stat.S_ISREG(path_now.st_mode)
        and held.st_nlink == path_now.st_nlink == nlink
        and stat_record(held) == stat_record(path_now),
        "Artifact lstat/device/inode/link/type/size identity differs: " + name,
    )
    body = read_exact_fd(fd, held.st_size)
    digest = sha256_bytes(body)
    require(expected_sha256 is None or digest == expected_sha256,
            "Artifact SHA-256 differs: " + name)
    return {
        "path": str(Path(directory_path) / name),
        "name": name,
        "sha256": digest,
        "bytes": len(body),
        "lstat": stat_record(held),
    }, body


def open_regular_lease(directory_fd, directory_path, name, expected_sha256=None, nlink=1):
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(name, flags, dir_fd=directory_fd)
    try:
        record, body = regular_record_at(
            directory_fd, directory_path, name, fd, expected_sha256, nlink,
        )
    except BaseException:
        os.close(fd)
        raise
    return {"fd": fd, "record": record, "body": body}


def verify_regular_lease(directory_fd, directory_path, lease, nlink=1):
    record, body = regular_record_at(
        directory_fd, directory_path, lease["record"]["name"], lease["fd"],
        lease["record"]["sha256"], nlink,
    )
    require(record == lease["record"] and body == lease["body"],
            "Held artifact lease changed: " + lease["record"]["name"])
    return record


def close_leases(leases):
    first = None
    for lease in leases.values():
        fd = lease.get("fd", -1)
        if fd >= 0:
            try:
                os.close(fd)
            except OSError as error:
                if first is None:
                    first = error
            lease["fd"] = -1
    if first is not None:
        raise first


def create_prebound_worker_artifact(output_fd, output_path, name):
    """Create the sole worker output inode before fork and retain its writable FD."""
    require(name in (REPORT_NAME, WORKER_RECEIPT_NAME),
            "Unknown prebound worker artifact")
    flags = (
        os.O_RDWR | os.O_CREAT | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    )
    fd = os.open(name, flags, 0o400, dir_fd=output_fd)
    try:
        opened = os.fstat(fd)
        named = os.stat(name, dir_fd=output_fd, follow_symlinks=False)
        identity = inode_identity(opened)
        require(
            stat.S_ISREG(opened.st_mode) and stat.S_ISREG(named.st_mode)
            and opened.st_nlink == named.st_nlink == 1
            and identity == inode_identity(named)
            and opened.st_size == named.st_size == 0,
            "Prebound worker artifact was not created as one empty inode",
        )
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        os.fsync(fd)
        os.fsync(output_fd)
        return {
            "fd": fd,
            "name": name,
            "path": str(Path(output_path) / name),
            "identity": identity,
            "created_lstat": stat_record(opened),
        }
    except BaseException:
        os.close(fd)
        raise


def verify_prebound_worker_artifact(output_fd, output_path, lease,
                                    expected_sha256=None, require_empty=False):
    """Read the parent-held inode directly; pathname is only a mismatch guard."""
    name = lease["name"]
    held = os.fstat(lease["fd"])
    named = os.stat(name, dir_fd=output_fd, follow_symlinks=False)
    require(
        stat.S_ISREG(held.st_mode) and stat.S_ISREG(named.st_mode)
        and held.st_nlink == named.st_nlink == 1
        and inode_identity(held) == lease["identity"] == inode_identity(named),
        "Prebound worker artifact pathname/inode binding changed: " + name,
    )
    if require_empty:
        require(held.st_size == named.st_size == 0
                and os.pread(lease["fd"], 1, 0) == b"",
                "Prebound worker artifact is not empty: " + name)
    body = read_exact_fd(lease["fd"], held.st_size)
    digest = sha256_bytes(body)
    require(expected_sha256 is None or digest == expected_sha256,
            "Prebound worker artifact SHA differs: " + name)
    record = {
        "path": str(Path(output_path) / name),
        "name": name,
        "sha256": digest,
        "bytes": len(body),
        "lstat": stat_record(held),
        "prebound_identity": list(lease["identity"]),
        "read_channel": "SUPERVISOR_HELD_PRESPAWN_FD_NO_PATH_REOPEN",
    }
    return record, body


def artifact_auth_tag(secret, artifact_name, value_without_tag):
    require(type(secret) is bytes and len(secret) == 32,
            "Artifact authentication secret must be exactly 32 bytes")
    require(artifact_name in (REPORT_NAME, WORKER_RECEIPT_NAME),
            "Artifact authentication domain is unknown")
    message = (
        ARTIFACT_AUTH_DOMAIN + b"\0" + artifact_name.encode("ascii")
        + b"\0" + canonical(value_without_tag)
    )
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


def verify_artifact_auth(secret, artifact_name, value):
    require(type(value) is dict, "Authenticated artifact is not a JSON object")
    supplied = value.get("artifact_authentication_hmac_sha256")
    unsigned = {key: item for key, item in value.items()
                if key != "artifact_authentication_hmac_sha256"}
    expected = artifact_auth_tag(secret, artifact_name, unsigned)
    require(type(supplied) is str and hmac.compare_digest(supplied, expected),
            "Prebound worker artifact authentication failed: " + artifact_name)


def directory_record(worker, parent_fd, parent_path, parent_identity,
                     output_fd, output_name, output_identity,
                     expected_entries, expected_nlinks):
    worker.verify_directory_lease(
        parent_fd, parent_path, parent_identity,
        output_fd, output_name, output_identity,
    )
    held = os.fstat(output_fd)
    path_now = os.stat(output_name, dir_fd=parent_fd, follow_symlinks=False)
    require(stat.S_ISDIR(held.st_mode) and stat_record(held) == stat_record(path_now),
            "Canonical output directory lstat identity differs")
    names = sorted(os.listdir(output_fd))
    require(names == sorted(expected_entries),
            "Canonical output directory inventory differs")
    entries = {}
    for name in names:
        value = os.stat(name, dir_fd=output_fd, follow_symlinks=False)
        require(stat.S_ISREG(value.st_mode), "Output inventory contains a non-regular entry")
        require(value.st_nlink == expected_nlinks.get(name, 1),
                "Output inventory link count differs: " + name)
        entries[name] = stat_record(value)
    return {
        "path": str(Path(parent_path) / output_name),
        "lstat": stat_record(held),
        "inventory": entries,
        "inventory_sha256": sha256_bytes(canonical(entries)),
    }


def lock_record(worker, parent_fd, parent_path, parent_identity,
                lock_fd, lock_name, lock_identity, lock_sha256, lock_bytes):
    worker.verify_lock_lease(
        parent_fd, parent_path, parent_identity, lock_fd, lock_name,
        lock_identity, lock_sha256, lock_bytes,
    )
    held = os.fstat(lock_fd)
    path_now = os.stat(lock_name, dir_fd=parent_fd, follow_symlinks=False)
    body = read_exact_fd(lock_fd, lock_bytes)
    require(stat_record(held) == stat_record(path_now),
            "Permanent lock lstat identity differs")
    return {
        "path": str(Path(parent_path) / lock_name),
        "sha256": sha256_bytes(body),
        "bytes": len(body),
        "lstat": stat_record(held),
    }


def collect_evidence_bundle(worker, parent_fd, parent_path, parent_identity,
                            lock_fd, lock_name, lock_identity, lock_sha256, lock_bytes,
                            output_fd, output_name, output_identity,
                            leases, expected_entries, expected_nlinks=None):
    if expected_nlinks is None:
        expected_nlinks = {}
    records = {
        name: verify_regular_lease(
            output_fd, Path(parent_path) / output_name, lease,
            expected_nlinks.get(name, 1),
        )
        for name, lease in leases.items()
    }
    return {
        "permanent_lock": lock_record(
            worker, parent_fd, parent_path, parent_identity,
            lock_fd, lock_name, lock_identity, lock_sha256, lock_bytes,
        ),
        "canonical_execution_directory": directory_record(
            worker, parent_fd, parent_path, parent_identity,
            output_fd, output_name, output_identity,
            expected_entries, expected_nlinks,
        ),
        "artifacts": records,
    }


def stable_evidence_projection(bundle):
    directory = bundle["canonical_execution_directory"]
    return {
        "permanent_lock": bundle["permanent_lock"],
        "canonical_execution_identity": {
            key: directory["lstat"][key]
            # Directory link counts and sizes legitimately change when the
            # staging/final directory entries are created.  Every full bundle
            # still records and validates both fields against the held FD and
            # canonical pathname at that boundary; the cross-boundary stable
            # identity is therefore the inode/type identity only.
            for key in ("device", "inode", "mode", "type")
        },
        "artifacts": bundle["artifacts"],
    }


def write_staged_regular(output_fd, output_path, name, value):
    body = encoded_json(value)
    flags = (
        os.O_RDWR | os.O_CREAT | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    )
    fd = os.open(name, flags, 0o600, dir_fd=output_fd)
    close_error = None
    try:
        opened = os.fstat(fd)
        require(stat.S_ISREG(opened.st_mode) and opened.st_nlink == 1,
                "Terminal-seal staging is not one regular inode")
        offset = 0
        while offset < len(body):
            written = os.write(fd, body[offset:])
            require(written > 0, "Terminal-seal staging write made no progress")
            offset += written
        os.fsync(fd)
        record, observed = regular_record_at(
            output_fd, output_path, name, fd, sha256_bytes(body), 1,
        )
        require(observed == body, "Terminal-seal staging bytes differ")
    finally:
        try:
            os.close(fd)
        except OSError as error:
            close_error = error
    if close_error is not None:
        raise close_error
    os.fsync(output_fd)
    return record, body


def fault_point(name, expected):
    if expected != name:
        return
    if name.startswith("SIGKILL_"):
        os.kill(os.getpid(), signal.SIGKILL)
    if name.startswith("SIGTERM_"):
        os.kill(os.getpid(), signal.SIGTERM)
    raise InjectedSyntheticFailure(name)


def publish_terminal_seal(
    worker, parent_fd, parent_path, parent_identity,
    lock_fd, lock_name, lock_identity, lock_sha256, lock_bytes,
    output_fd, output_name, output_identity, leases, seal,
    fault=None,
):
    """Return a nonauthoritative candidate observation after required closes.

    No pathname written here contains ``passed=true``.  Only the current
    supervisor can turn the returned held-FD observation into an exit-gated
    terminal PASS JSON on stdout after this function has completed.
    """
    base_entries = sorted(leases)
    require(TERMINAL_SEAL_NAME not in base_entries and TERMINAL_SEAL_STAGING_NAME not in base_entries,
            "Terminal names cannot be supplied as evidence leases")
    require(worker.entry_absent(output_fd, TERMINAL_SEAL_NAME)
            and worker.entry_absent(output_fd, TERMINAL_SEAL_STAGING_NAME),
            "Terminal seal or staging already exists")
    pre = collect_evidence_bundle(
        worker, parent_fd, parent_path, parent_identity,
        lock_fd, lock_name, lock_identity, lock_sha256, lock_bytes,
        output_fd, output_name, output_identity,
        leases, base_entries,
    )
    seal = dict(seal)
    seal["pre_terminal_publish_evidence"] = pre
    seal["authority_conditions"] = {
        "final_name": TERMINAL_SEAL_NAME,
        "final_regular_file_nlink": 1,
        "staging_name_absent": TERMINAL_SEAL_STAGING_NAME,
        "terminal_failure_absent": TERMINAL_FAILURE_NAME,
        "independent_result_review_required": True,
        "canonical_path_alone_is_authoritative": False,
        "candidate_consumer": "same_supervisor_held_final_and_evidence_fds_only",
        "atomic_commit": "unlink_staging_then_revalidate_held_final_and_all_evidence_before_return",
    }
    stage_record, body = write_staged_regular(
        output_fd, Path(parent_path) / output_name,
        TERMINAL_SEAL_STAGING_NAME, seal,
    )
    fault_point("STAGE_CLOSE_BEFORE_PUBLISH", fault)

    with_stage = base_entries + [TERMINAL_SEAL_STAGING_NAME]
    pre_link = collect_evidence_bundle(
        worker, parent_fd, parent_path, parent_identity,
        lock_fd, lock_name, lock_identity, lock_sha256, lock_bytes,
        output_fd, output_name, output_identity,
        leases, with_stage,
    )
    require(stable_evidence_projection(pre_link) == stable_evidence_projection(pre),
            "Core evidence changed after terminal staging close")

    os.link(
        TERMINAL_SEAL_STAGING_NAME, TERMINAL_SEAL_NAME,
        src_dir_fd=output_fd, dst_dir_fd=output_fd, follow_symlinks=False,
    )
    fault_point("SIGKILL_AFTER_LINK", fault)
    fault_point("SIGTERM_AFTER_LINK", fault)
    fault_point("DIR_FSYNC_BEFORE_COMMIT", fault)
    os.fsync(output_fd)

    stage = open_regular_lease(
        output_fd, Path(parent_path) / output_name,
        TERMINAL_SEAL_STAGING_NAME, sha256_bytes(body), nlink=2,
    )
    final = open_regular_lease(
        output_fd, Path(parent_path) / output_name,
        TERMINAL_SEAL_NAME, sha256_bytes(body), nlink=2,
    )
    terminal_leases = {"stage": stage, "final": final}
    returned_observation = None
    try:
        require(
            stage["record"]["lstat"] == final["record"]["lstat"]
            and stage["body"] == final["body"] == body,
            "Terminal seal hard-link publication changed identity/content",
        )
        post_link = collect_evidence_bundle(
            worker, parent_fd, parent_path, parent_identity,
            lock_fd, lock_name, lock_identity, lock_sha256, lock_bytes,
            output_fd, output_name, output_identity,
            leases, base_entries + [TERMINAL_SEAL_NAME, TERMINAL_SEAL_STAGING_NAME],
            {TERMINAL_SEAL_NAME: 2, TERMINAL_SEAL_STAGING_NAME: 2},
        )
        require(stable_evidence_projection(post_link) == stable_evidence_projection(pre),
                "Lock/output/report/worker/supervisor evidence changed after seal link")
        os.fsync(output_fd)
        fault_point("FINAL_DIR_FSYNC_BEFORE_COMMIT", fault)

        # The unlink changes the held seal inode from two names to one.  No FD
        # closes before the following final-path and evidence revalidation.
        os.unlink(TERMINAL_SEAL_STAGING_NAME, dir_fd=output_fd)
        if fault in ("RENAME_RECREATE_FINAL_AFTER_UNLINK", "UNLINK_RECREATE_FINAL_AFTER_UNLINK"):
            if fault.startswith("RENAME"):
                os.rename(
                    TERMINAL_SEAL_NAME, ".attacker-displaced-seal",
                    src_dir_fd=output_fd, dst_dir_fd=output_fd,
                )
            else:
                os.unlink(TERMINAL_SEAL_NAME, dir_fd=output_fd)
            replacement_fd = os.open(
                TERMINAL_SEAL_NAME,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL
                | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
                0o600, dir_fd=output_fd,
            )
            try:
                offset = 0
                while offset < len(body):
                    offset += os.write(replacement_fd, body[offset:])
                os.fsync(replacement_fd)
            finally:
                os.close(replacement_fd)
        fault_point("SIGKILL_AFTER_UNLINK", fault)
        fault_point("SIGTERM_AFTER_UNLINK", fault)
        os.fsync(output_fd)
        require(_entry_absent(output_fd, TERMINAL_SEAL_STAGING_NAME),
                "Terminal staging name survived the authority transition")
        committed_final, committed_body = regular_record_at(
            output_fd, Path(parent_path) / output_name, TERMINAL_SEAL_NAME,
            final["fd"], sha256_bytes(body), 1,
        )
        stage_after = os.fstat(stage["fd"])
        require(
            stat.S_ISREG(stage_after.st_mode) and stage_after.st_nlink == 1
            and inode_identity(stage_after)
            == inode_identity(os.fstat(final["fd"]))
            and committed_body == body,
            "Held terminal inode did not become the exact single-link final seal",
        )
        post_commit = collect_evidence_bundle(
            worker, parent_fd, parent_path, parent_identity,
            lock_fd, lock_name, lock_identity, lock_sha256, lock_bytes,
            output_fd, output_name, output_identity,
            leases, base_entries + [TERMINAL_SEAL_NAME],
            {TERMINAL_SEAL_NAME: 1},
        )
        require(stable_evidence_projection(post_commit) == stable_evidence_projection(pre),
                "Core evidence changed at final held-FD consumption")
        parsed = json.loads(committed_body.decode("utf-8"))
        require(
            parsed == seal
            and parsed.get("schema") == "s45b-c1-numeric-camera-guard-terminal-candidate-v4"
            and parsed.get("status")
            == "NUMERIC_WORKER_PASS_PENDING_HELD_FD_CLOSE_AND_EXTERNAL_EXIT_ZERO"
            and parsed.get("passed") is False
            and parsed.get("terminal_authority") is False
            and parsed.get("authority_conditions", {}).get("canonical_path_alone_is_authoritative") is False,
            "Held final candidate does not have the full exact V10 pending document",
        )
        returned_observation = {
            "schema": "s45b-v10-held-terminal-candidate-observation-v3",
            "status": "HELD_CANDIDATE_READY_FOR_EXTERNAL_EXIT_GATED_SEAL",
            "passed": False,
            "terminal_authority": False,
            "candidate_sha256": sha256_bytes(committed_body),
            "candidate_bytes": len(committed_body),
            "candidate_lstat": committed_final["lstat"],
            "evidence_projection_sha256": sha256_bytes(
                canonical(stable_evidence_projection(post_commit))
            ),
            "canonical_path_alone_is_authoritative": False,
            "observed_while_all_core_evidence_fds_held": True,
        }
        fault_point("REQUIRED_FD_CLOSE_AFTER_HELD_CONSUMPTION", fault)
        close_leases(leases)
        if fault == "FINAL_SEAL_CLOSE_ERROR":
            os.close(final["fd"])
        close_leases(terminal_leases)
        os.fsync(output_fd)
        return returned_observation
    finally:
        try:
            close_leases(terminal_leases)
        except OSError:
            pass


def canonical_seal_matches_held_observation(output_fd, observation):
    """Diagnostic only: a path may match a prior held-FD candidate observation.

    This function cannot create PASS and deliberately returns false when no
    live supervisor observation is supplied.
    """
    if not isinstance(observation, dict):
        return False
    if (
        observation.get("schema") != "s45b-v10-held-terminal-candidate-observation-v3"
        or observation.get("status") != "HELD_CANDIDATE_READY_FOR_EXTERNAL_EXIT_GATED_SEAL"
        or observation.get("passed") is not False
        or observation.get("terminal_authority") is not False
        or observation.get("canonical_path_alone_is_authoritative") is not False
        or observation.get("observed_while_all_core_evidence_fds_held") is not True
        or not valid_sha(observation.get("candidate_sha256"))
    ):
        return False
    for forbidden in (
        TERMINAL_SEAL_STAGING_NAME, TERMINAL_FAILURE_NAME, WORKER_FAILURE_NAME,
    ):
        if not _entry_absent(output_fd, forbidden):
            return False
    try:
        lease = open_regular_lease(
            output_fd, Path("/diagnostic-only-output"), TERMINAL_SEAL_NAME,
            observation["candidate_sha256"], nlink=1,
        )
    except (FileNotFoundError, ValueError, OSError):
        return False
    try:
        return (
            lease["record"]["bytes"] == observation.get("candidate_bytes")
            and lease["record"]["lstat"] == observation.get("candidate_lstat")
        )
    finally:
        close_leases({"seal": lease})


def close_terminal_control_fds(output_fd, lock_fd, parent_fd, fault=None):
    """Durably close every remaining filesystem control FD before PASS exists."""
    os.fsync(output_fd)
    os.fsync(lock_fd)
    os.fsync(parent_fd)
    for label, fd in (
        ("OUTPUT", output_fd), ("LOCK", lock_fd), ("PARENT", parent_fd),
    ):
        if fault == "FINAL_" + label + "_FD_CLOSE_ERROR":
            os.close(fd)
        os.close(fd)


def _entry_absent(directory_fd, name):
    try:
        os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        return True
    return False


def terminate_exact_process(pid):
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def worker_resource_limit():
    """Portable Darwin limits used by both capability probe and formal worker.

    Darwin rejects the V5 address-space/RSS limits on this host.  Memory
    acceptance is instead enforced by the
    supervisor's exact-PID libproc high-water monitor plus wait4 evidence.
    """
    resource.setrlimit(resource.RLIMIT_CPU, (CPU_LIMIT_SECONDS, CPU_LIMIT_SECONDS))
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_ARTIFACT_BYTES, MAX_ARTIFACT_BYTES))


def contained_command(inner):
    require(type(inner) is list and inner and all(type(item) is str for item in inner),
            "Contained command is malformed")
    return [str(SANDBOX_EXEC), "-p", SANDBOX_PROFILE, *inner]


def spawn_contained(inner, pass_fds=()):
    """Synthetic subprocess helper; the V10 formal worker never uses this path."""
    return subprocess.Popen(
        contained_command(inner),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        pass_fds=tuple(pass_fds),
        close_fds=True,
        start_new_session=True,
        preexec_fn=worker_resource_limit,
    )


class ForkedProcess:
    """Minimal process handle consumed by bounded_process_wait."""
    def __init__(self, pid, stdout, stderr, execution_binding):
        self.pid = pid
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = None
        self.execution_binding = execution_binding


def apply_darwin_no_fork_sandbox():
    """Apply Seatbelt inside the already-forked interpreter, without exec."""
    require(platform.system() == "Darwin", "V10 formal containment requires Darwin")
    library = ctypes.CDLL(None, use_errno=True)
    function = library.sandbox_init
    function.argtypes = [ctypes.c_char_p, ctypes.c_uint64,
                         ctypes.POINTER(ctypes.c_char_p)]
    function.restype = ctypes.c_int
    free_error = library.sandbox_free_error
    free_error.argtypes = [ctypes.c_char_p]
    free_error.restype = None
    error_buffer = ctypes.c_char_p()
    ctypes.set_errno(0)
    result = function(SANDBOX_PROFILE.encode("utf-8"), 0,
                      ctypes.byref(error_buffer))
    try:
        message = None if not error_buffer.value else error_buffer.value.decode("utf-8")
        require(result == 0,
                "Darwin sandbox_init failed: " + (message or str(ctypes.get_errno())))
    finally:
        if error_buffer.value:
            free_error(error_buffer)


def close_child_fds_except(allowed):
    allowed = set(allowed) | {0, 1, 2}
    for raw in os.listdir("/dev/fd"):
        try:
            fd = int(raw)
        except ValueError:
            continue
        if fd <= 2 or fd in allowed:
            continue
        try:
            os.close(fd)
        except OSError:
            pass


def _fork_loaded_entry(entry, entry_args, kept_fds, execution_binding):
    """Fork the current interpreter, apply containment, and call loaded code.

    There is deliberately no exec, posix_spawn, script pathname, or interpreter
    pathname between the final source binding and entry invocation.
    """
    stdout_read, stdout_write = os.pipe()
    stderr_read, stderr_write = os.pipe()
    pid = os.fork()
    if pid == 0:
        try:
            os.close(stdout_read)
            os.close(stderr_read)
            os.setsid()
            null_fd = os.open(os.devnull, os.O_RDONLY)
            os.dup2(null_fd, 0)
            os.dup2(stdout_write, 1)
            os.dup2(stderr_write, 2)
            if null_fd > 2:
                os.close(null_fd)
            if stdout_write > 2 and stdout_write != 1:
                os.close(stdout_write)
            if stderr_write > 2 and stderr_write != 2:
                os.close(stderr_write)
            worker_resource_limit()
            apply_darwin_no_fork_sandbox()
            close_child_fds_except(kept_fds)
            result = entry(*entry_args)
            sys.stdout.flush()
            sys.stderr.flush()
            os._exit(int(result or 0))
        except BaseException:
            try:
                os.write(2, traceback.format_exc().encode("utf-8", "replace"))
            except BaseException:
                pass
            os._exit(126)
    os.close(stdout_write)
    os.close(stderr_write)
    return ForkedProcess(
        pid,
        os.fdopen(stdout_read, "rb", buffering=0),
        os.fdopen(stderr_read, "rb", buffering=0),
        execution_binding,
    )


def _execute_loaded_worker(source_code, namespace):
    module = types.ModuleType("_s45b_c1_camera_worker_fork_bound_v10")
    module.__file__ = str(WORKER)
    exec(source_code, module.__dict__)
    require(module.SELF == WORKER and module.formal_worker_run.__module__
            == module.__name__, "Fork-bound worker module identity differs")
    return module.formal_worker_run(namespace)


def spawn_bound_worker(worker, namespace, interpreter_binding,
                       interpreter_binding_sha256):
    """Launch exact reviewed worker code in the current interpreter image."""
    source_record = verify_loaded_worker_lease(worker, namespace.self_sha256)
    lease = worker._held_source_lease
    kept = (
        namespace.parent_fd, namespace.lock_fd, namespace.output_fd,
        namespace.capability_fd, namespace.worker_source_fd,
        namespace.report_fd, namespace.worker_receipt_fd,
    )
    require(namespace.worker_source_fd == lease["fd"],
            "Formal namespace does not carry the retained worker source FD")
    execution_binding = {
        "schema": "s45b-v10-fork-bound-worker-execution-v1",
        "launch_mechanism": "FORK_ALREADY_RUNNING_INTERPRETER_THEN_SANDBOX_INIT_NO_EXEC",
        "interpreter_binding_sha256": interpreter_binding_sha256,
        "interpreter_process_uuid": interpreter_binding["process_uuid"],
        "worker_source": source_record,
        "ordinary_worker_path_reopened": False,
        "ordinary_interpreter_path_reopened": False,
    }
    return _fork_loaded_entry(
        _execute_loaded_worker, (lease["code"], namespace), kept,
        execution_binding,
    )


def bounded_process_wait(
    process, time_limit=TIME_LIMIT_SECONDS,
    stdout_limit=MAX_STDOUT_BYTES, stderr_limit=MAX_STDERR_BYTES,
    memory_limit=MAX_WORKER_RSS_BYTES, expected_process_uuid=None,
):
    """Observe one sandboxed PID with wait4 and Darwin kernel memory accounting."""
    require(time_limit > 0 and stdout_limit >= 0 and stderr_limit >= 0 and memory_limit > 0,
            "Process observation limits are malformed")
    deadline = time.monotonic() + time_limit
    streams = {process.stdout: ("stdout", stdout_limit),
               process.stderr: ("stderr", stderr_limit)}
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    selector = selectors.DefaultSelector()
    timed_out = False
    output_limit_exceeded = False
    memory_limit_exceeded = False
    memory_monitor_failed = False
    memory_monitor_error = None
    memory_samples = 0
    max_phys_footprint = 0
    max_resident_size = 0
    observed_process_uuid = None
    child_done = False
    child_usage = None
    try:
        for stream in streams:
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ)
        while selector.get_map() or not child_done:
            if not child_done:
                try:
                    observed = darwin_process_usage(process.pid)
                except OSError as error:
                    if error.errno not in (errno.ESRCH, errno.ENOENT):
                        memory_monitor_failed = True
                        memory_monitor_error = type(error).__name__ + ": " + str(error)
                        terminate_exact_process(process.pid)
                else:
                    observed_process_uuid = observed["process_uuid"]
                    if (expected_process_uuid is not None
                            and observed_process_uuid != expected_process_uuid):
                        memory_monitor_failed = True
                        memory_monitor_error = "Exact worker executable UUID differs"
                        terminate_exact_process(process.pid)
                    memory_samples += 1
                    max_phys_footprint = max(
                        max_phys_footprint,
                        observed["phys_footprint_bytes"],
                        observed["lifetime_max_phys_footprint_bytes"],
                    )
                    max_resident_size = max(max_resident_size, observed["resident_size_bytes"])
                    if max(max_phys_footprint, max_resident_size) > memory_limit:
                        memory_limit_exceeded = True
                        terminate_exact_process(process.pid)
                try:
                    waited_pid, status, usage = os.wait4(process.pid, os.WNOHANG)
                except ChildProcessError:
                    waited_pid = 0
                if waited_pid == process.pid:
                    process.returncode = os.waitstatus_to_exitcode(status)
                    child_usage = usage
                    child_done = True
            remaining = deadline - time.monotonic()
            if remaining <= 0 and not child_done:
                timed_out = True
                terminate_exact_process(process.pid)
            wait_slice = MEMORY_SAMPLE_INTERVAL_SECONDS
            if not child_done:
                wait_slice = max(0.0, min(wait_slice, remaining))
            events = selector.select(wait_slice)
            for key, _ in events:
                stream = key.fileobj
                label, limit = streams[stream]
                try:
                    amount = max(1, min(65536, limit - len(buffers[label]) + 1))
                    chunk = os.read(stream.fileno(), amount)
                except BlockingIOError:
                    continue
                if not chunk:
                    selector.unregister(stream)
                    continue
                buffers[label].extend(chunk)
                if len(buffers[label]) > limit:
                    del buffers[label][limit + 1:]
                    output_limit_exceeded = True
                    terminate_exact_process(process.pid)
                    selector.unregister(stream)
            if child_done and not selector.get_map():
                break
        if not child_done:
            terminate_exact_process(process.pid)
            waited_pid, status, child_usage = os.wait4(process.pid, 0)
            require(waited_pid == process.pid, "wait4 reaped another process")
            process.returncode = os.waitstatus_to_exitcode(status)
    finally:
        selector.close()
        for stream in streams:
            try:
                stream.close()
            except OSError:
                pass
    require(child_usage is not None, "Exact worker wait4 resource evidence is absent")
    wait4_peak_rss = maxrss_bytes(child_usage.ru_maxrss)
    max_observed_memory = max(max_phys_footprint, max_resident_size, wait4_peak_rss)
    if max_observed_memory > memory_limit:
        memory_limit_exceeded = True
    if memory_samples == 0:
        memory_monitor_failed = True
        if memory_monitor_error is None:
            memory_monitor_error = "No successful proc_pid_rusage sample"
    return {
        "returncode": process.returncode,
        "stdout": bytes(buffers["stdout"]),
        "stderr": bytes(buffers["stderr"]),
        "timed_out": timed_out,
        "output_limit_exceeded": output_limit_exceeded,
        "memory_limit_exceeded": memory_limit_exceeded,
        "memory_monitor_failed": memory_monitor_failed,
        "memory_monitor_error": memory_monitor_error,
        "memory_monitor_samples": memory_samples,
        "peak_phys_footprint_bytes": max_phys_footprint,
        "peak_resident_size_bytes": max_resident_size,
        "wait4_peak_rss_bytes": wait4_peak_rss,
        "max_observed_memory_bytes": max_observed_memory,
        "process_uuid": observed_process_uuid,
        "expected_process_uuid": expected_process_uuid,
        "user_cpu_seconds": child_usage.ru_utime,
        "system_cpu_seconds": child_usage.ru_stime,
    }


def maxrss_bytes(value):
    return int(value) if platform.system() == "Darwin" else int(value) * 1024


def darwin_process_path(pid):
    require(platform.system() == "Darwin", "V10 process-image binding requires Darwin")
    library = ctypes.CDLL(DARWIN_LIBPROC, use_errno=True)
    function = library.proc_pidpath
    function.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
    function.restype = ctypes.c_int
    buffer = ctypes.create_string_buffer(4096)
    ctypes.set_errno(0)
    count = function(int(pid), buffer, len(buffer))
    if count <= 0:
        number = ctypes.get_errno()
        raise OSError(number, os.strerror(number))
    return buffer.value.decode("utf-8")


def current_interpreter_binding():
    """Describe the already-running interpreter image inherited by fork."""
    usage = darwin_process_usage(os.getpid())
    kernel_path = Path(darwin_process_path(os.getpid())).resolve()
    executable_path = Path(sys.executable).resolve()
    kernel_snapshot = executable_snapshot(kernel_path)
    launcher_snapshot = executable_snapshot(executable_path)
    value = {
        "schema": "s45b-v10-running-interpreter-binding-v1",
        "launch_mechanism": "FORK_ALREADY_RUNNING_INTERPRETER_NO_EXEC",
        "supervisor_pid": os.getpid(),
        "kernel_process_path": str(kernel_path),
        "process_uuid": usage["process_uuid"],
        "kernel_process_image_snapshot": kernel_snapshot,
        "sys_executable_launcher_snapshot": launcher_snapshot,
        "kernel_image_may_differ_from_framework_launcher": True,
        "python_implementation": platform.python_implementation(),
        "python_version": sys.version,
        "cache_tag": sys.implementation.cache_tag,
    }
    return value, sha256_bytes(canonical(value))


def worker_namespace(args):
    return argparse.Namespace(
        self_sha256=args.worker_sha256,
        supervisor_sha256=args.self_sha256,
        primary_source_review_sha256=args.primary_source_review_sha256,
        adversarial_source_review_sha256=args.adversarial_source_review_sha256,
        binding_sha256=args.binding_sha256,
        binding_review_sha256=args.binding_review_sha256,
        governance_attestation_sha256=args.governance_attestation_sha256,
        out=args.out,
    )


def formal_worker_namespace(
    args, capability_fd, capability_sha256,
    parent_fd, parent_identity, lock_fd, lock_identity,
    lock_sha256, lock_bytes, output_fd, output_identity,
    worker_source_lease, report_prebound, worker_receipt_prebound,
    interpreter_binding_sha256,
):
    """Build the in-memory entry arguments; no CLI or pathname is constructed."""
    return argparse.Namespace(
        self_sha256=args.worker_sha256,
        supervisor_sha256=args.self_sha256,
        primary_source_review_sha256=args.primary_source_review_sha256,
        adversarial_source_review_sha256=args.adversarial_source_review_sha256,
        binding_sha256=args.binding_sha256,
        binding_review_sha256=args.binding_review_sha256,
        governance_attestation_sha256=args.governance_attestation_sha256,
        runtime_interpreter_binding_sha256=interpreter_binding_sha256,
        out=args.out,
        parent_fd=parent_fd,
        lock_fd=lock_fd,
        output_fd=output_fd,
        capability_fd=capability_fd,
        worker_source_fd=worker_source_lease["fd"],
        worker_source_dev=worker_source_lease["identity"][0],
        worker_source_ino=worker_source_lease["identity"][1],
        worker_source_mode=worker_source_lease["identity"][2],
        worker_source_bytes=worker_source_lease["bytes"],
        report_fd=report_prebound["fd"],
        report_dev=report_prebound["identity"][0],
        report_ino=report_prebound["identity"][1],
        report_mode=report_prebound["identity"][2],
        worker_receipt_fd=worker_receipt_prebound["fd"],
        worker_receipt_dev=worker_receipt_prebound["identity"][0],
        worker_receipt_ino=worker_receipt_prebound["identity"][1],
        worker_receipt_mode=worker_receipt_prebound["identity"][2],
        capability_sha256=capability_sha256,
        supervisor_pid=os.getpid(),
        parent_dev=parent_identity[0], parent_ino=parent_identity[1],
        parent_mode=parent_identity[2],
        lock_dev=lock_identity[0], lock_ino=lock_identity[1],
        lock_mode=lock_identity[2], lock_sha256=lock_sha256,
        lock_bytes=lock_bytes,
        output_dev=output_identity[0], output_ino=output_identity[1],
        output_mode=output_identity[2],
    )


def _attempt_denied_process_escape(kind):
    """Actually attempt the V5 escape shapes; PASS only on kernel EPERM."""
    if kind in ("FORK_SETSID_KEEP_STDIO", "FORK_SETSID_CLOSE_STDIO"):
        try:
            child = os.fork()
        except PermissionError as error:
            require(error.errno == errno.EPERM, kind + " failed for an unexpected reason")
            return {"result": "DENIED_BY_SANDBOX", "errno": error.errno}
        if child == 0:
            try:
                os.setsid()
                if kind.endswith("CLOSE_STDIO"):
                    for fd in (0, 1, 2):
                        try:
                            os.close(fd)
                        except OSError:
                            pass
                time.sleep(5)
            finally:
                os._exit(91)
        try:
            os.kill(child, signal.SIGKILL)
            os.waitpid(child, 0)
        finally:
            pass
        return {"result": "ESCAPE_CREATION_WAS_ALLOWED", "errno": 0}
    if kind == "POSIX_SPAWN_SETSID":
        try:
            child = os.posix_spawn(
                "/bin/sleep", ["sleep", "5"], os.environ.copy(), setsid=True,
            )
        except PermissionError as error:
            require(error.errno == errno.EPERM, kind + " failed for an unexpected reason")
            return {"result": "DENIED_BY_SANDBOX", "errno": error.errno}
        try:
            os.kill(child, signal.SIGKILL)
            os.waitpid(child, 0)
        finally:
            pass
        return {"result": "ESCAPE_CREATION_WAS_ALLOWED", "errno": 0}
    raise AssertionError("Unknown containment attack")


def synthetic_capability_child():
    cpu = resource.getrlimit(resource.RLIMIT_CPU)
    fsize = resource.getrlimit(resource.RLIMIT_FSIZE)
    attacks = {
        kind: _attempt_denied_process_escape(kind)
        for kind in (
            "FORK_SETSID_KEEP_STDIO",
            "FORK_SETSID_CLOSE_STDIO",
            "POSIX_SPAWN_SETSID",
        )
    }
    allocation = bytearray(CAPABILITY_PROBE_BYTES)
    for offset in range(0, len(allocation), 4096):
        allocation[offset] = 1
    time.sleep(0.10)
    value = {
        "schema": "s45b-v10-darwin-fork-bound-capability-probe-v1",
        "status": "PASS_CAPABILITY_PROBE_ONLY",
        "pid": os.getpid(),
        "cpu_limit": list(cpu),
        "file_size_limit": list(fsize),
        "sandbox_attacks": attacks,
        "allocation_bytes_touched": len(allocation),
    }
    passed = (
        cpu == (CPU_LIMIT_SECONDS, CPU_LIMIT_SECONDS)
        and fsize == (MAX_ARTIFACT_BYTES, MAX_ARTIFACT_BYTES)
        and all(item["result"] == "DENIED_BY_SANDBOX" for item in attacks.values())
    )
    require(passed, "Darwin containment capability probe failed")
    print(json.dumps(value, sort_keys=True, allow_nan=False))
    return 0


def runtime_capability_preflight(worker_source_record):
    """Exercise the exact fork-without-exec production mechanism pre-attempt."""
    require(platform.system() == "Darwin", "V10 formal execution supports reviewed macOS only")
    interpreter_binding, interpreter_binding_sha256 = current_interpreter_binding()
    execution_binding = {
        "schema": "s45b-v10-fork-bound-capability-execution-v1",
        "launch_mechanism": "FORK_ALREADY_RUNNING_INTERPRETER_THEN_SANDBOX_INIT_NO_EXEC",
        "interpreter_binding_sha256": interpreter_binding_sha256,
        "interpreter_process_uuid": interpreter_binding["process_uuid"],
        "ordinary_interpreter_path_reopened": False,
        "ordinary_script_path_reopened": False,
    }
    started_utc = utc()
    process = _fork_loaded_entry(
        synthetic_capability_child, (), (), execution_binding,
    )
    observation = bounded_process_wait(
        process, time_limit=10.0,
        expected_process_uuid=interpreter_binding["process_uuid"],
    )
    completed_utc = utc()
    require(
        observation["returncode"] == 0
        and not observation["timed_out"]
        and not observation["output_limit_exceeded"]
        and not observation["memory_limit_exceeded"]
        and not observation["memory_monitor_failed"]
        and observation["stderr"] == b"",
        "Exact Darwin containment capability process failed",
    )
    try:
        payload = json.loads(observation["stdout"].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Containment capability output is not exact JSON") from error
    expected_attacks = {
        "FORK_SETSID_KEEP_STDIO",
        "FORK_SETSID_CLOSE_STDIO",
        "POSIX_SPAWN_SETSID",
    }
    require(
        payload.get("schema") == "s45b-v10-darwin-fork-bound-capability-probe-v1"
        and payload.get("status") == "PASS_CAPABILITY_PROBE_ONLY"
        and payload.get("cpu_limit") == [CPU_LIMIT_SECONDS, CPU_LIMIT_SECONDS]
        and payload.get("file_size_limit") == [MAX_ARTIFACT_BYTES, MAX_ARTIFACT_BYTES]
        and payload.get("allocation_bytes_touched") == CAPABILITY_PROBE_BYTES
        and set(payload.get("sandbox_attacks", {})) == expected_attacks
        and all(
            item == {"result": "DENIED_BY_SANDBOX", "errno": errno.EPERM}
            for item in payload["sandbox_attacks"].values()
        )
        and observation["memory_monitor_samples"] > 0
        and observation["max_observed_memory_bytes"] > 0,
        "Fork-bound containment capability proof is incomplete",
    )
    binding_after, binding_after_sha256 = current_interpreter_binding()
    require(binding_after == interpreter_binding
            and binding_after_sha256 == interpreter_binding_sha256,
            "Running interpreter binding changed across capability probe")
    return {
        "schema": "s45b-v10-runtime-capability-preflight-v1",
        "status": "PASS_BEFORE_ATTEMPT_COMMIT",
        "started_utc": started_utc,
        "completed_utc": completed_utc,
        "platform": platform.platform(),
        "python": sys.version,
        "launch_mechanism": "FORK_ALREADY_RUNNING_INTERPRETER_THEN_SANDBOX_INIT_NO_EXEC",
        "running_interpreter_binding": interpreter_binding,
        "running_interpreter_binding_sha256": interpreter_binding_sha256,
        "sandbox_profile": SANDBOX_PROFILE,
        "sandbox_profile_sha256": sha256_bytes(SANDBOX_PROFILE.encode("utf-8")),
        "worker_no_process_creation_audit": worker_source_record["no_process_creation_audit"],
        "probe": payload,
        "observation": {
            key: value for key, value in observation.items()
            if key not in ("stdout", "stderr")
        },
        "stdout_sha256": sha256_bytes(observation["stdout"]),
        "stderr_sha256": sha256_bytes(observation["stderr"]),
        "formal_paths_created": 0,
    }


REPORT_KEYS = frozenset({
    "schema", "status", "passed", "terminal_authority", "row",
    "numeric_worker_verdict", "tolerance", "cache_commit_sizes",
    "batch_authoritative_target_counts", "base_homogeneous_row_max_abs",
    "planned_yaw_degrees", "cache_commit_continuity",
    "batch_target_to_cache", "planned_sequence", "id8_to_id0",
    "pixel_score", "visual_quality", "rendered_pixel_camera_obedience",
    "method_gain", "novelty", "worker_sha256", "supervisor_sha256",
    "primary_source_review_sha256", "adversarial_source_review_sha256",
    "binding_sha256", "binding_review_sha256",
    "governance_attestation_sha256", "runtime_interpreter_binding_sha256",
    "executed_worker_source_binding", "archive_manifest_sha256",
    "archive_events_sha256", "s45_result_review_sha256", "event_chain",
    "camera_tensor_identities", "c1_tensor_bodies_read",
    "c1_tensor_bodies_close_verified", "c1_tensor_body_bytes_read",
    "external_supervisor_exit_and_terminal_seal_required",
    "evidence_boundary", "artifact_authentication_hmac_sha256",
})

WORKER_RECEIPT_KEYS = frozenset({
    "schema", "status", "row", "passed", "terminal_authority",
    "worker_pid", "supervisor_pid", "started_utc", "attempt",
    "automatic_retries", "worker_sha256", "supervisor_sha256",
    "primary_source_review_sha256", "adversarial_source_review_sha256",
    "binding_sha256", "binding_review_sha256",
    "governance_attestation_sha256", "runtime_interpreter_binding_sha256",
    "pixel_bodies_opened", "pixels_decoded", "images_viewed",
    "model_renderer_generation_runs", "numeric_worker_verdict",
    "report_sha256", "c1_tensor_bodies_read",
    "c1_tensor_bodies_close_verified", "c1_tensor_body_bytes_read",
    "sources_and_bound_metadata_unchanged_at_worker_close",
    "worker_recheck_identity_records", "worker_close_identity_records",
    "elapsed_seconds", "completed_utc", "executed_worker_source_binding",
    "report_artifact_identity", "worker_receipt_artifact_identity",
    "artifact_authentication_hmac_sha256",
})


def exact_keys(value, expected, label):
    require(type(value) is dict and set(value) == set(expected),
            label + " has missing or extra fields")


def finite_error(value, tolerance, label):
    require(type(value) in (int, float) and not isinstance(value, bool)
            and float(value) >= 0.0 and float(value) <= tolerance
            and float(value) == float(value) and abs(float(value)) != float("inf"),
            label + " is nonfinite, negative, or over tolerance")


def validate_error_rows(rows, expected_ids, tolerance, include_yaw=False):
    require(type(rows) is list and len(rows) == len(expected_ids),
            "Numeric evidence row count differs")
    for position, (row, expected_id) in enumerate(zip(rows, expected_ids)):
        keys = {"id", "pose_max_abs", "K_max_abs"}
        if include_yaw:
            keys.add("yaw_degrees")
        exact_keys(row, keys, "Numeric evidence row")
        require(type(row["id"]) is int and row["id"] == expected_id,
                "Numeric evidence ID order differs")
        finite_error(row["pose_max_abs"], tolerance,
                     f"pose error at ID{expected_id}")
        finite_error(row["K_max_abs"], tolerance,
                     f"K error at ID{expected_id}")
        if include_yaw:
            require(type(row["yaw_degrees"]) in (int, float)
                    and not isinstance(row["yaw_degrees"], bool)
                    and float(row["yaw_degrees"])
                    == (0.0, 1.25, 2.5, 3.75, 5.0, 3.75, 2.5, 1.25, 0.0)[position],
                    "Planned yaw value/order differs")


def validate_camera_tensor_identities(value, expected_count, expected_bytes):
    require(type(value) is dict and 0 < len(value) <= 32
            and len(value) == expected_count,
            "Camera tensor identity count differs")
    total = 0
    for raw, item in value.items():
        exact_keys(item, {
            "descriptor_sha256", "body_sha256", "dtype", "shape", "nbytes",
        }, "Camera tensor identity")
        require(type(raw) is str
                and raw == "tensors/" + item["descriptor_sha256"] + ".bin"
                and valid_sha(item["descriptor_sha256"])
                and valid_sha(item["body_sha256"]),
                "Camera tensor path/hash identity differs")
        require(item["dtype"] in ("float32", "float64")
                and type(item["shape"]) is list
                and all(type(number) is int and number > 0
                        for number in item["shape"]),
                "Camera tensor dtype/shape differs")
        shape = item["shape"]
        camera_shape = shape in ([3, 3], [4, 4])
        batch_shape = (
            len(shape) == 3 and 4 <= shape[0] <= 8
            and shape[1] == shape[2] and shape[1] in (3, 4)
        )
        require(camera_shape or batch_shape,
                "Camera tensor shape is outside c2w/K scope")
        width = 4 if item["dtype"] == "float32" else 8
        count = 1
        for number in shape:
            count *= number
        require(type(item["nbytes"]) is int
                and item["nbytes"] == count * width
                and 0 < item["nbytes"] <= 4096,
                "Camera tensor byte count differs")
        total += item["nbytes"]
    require(total == expected_bytes, "Camera tensor total body bytes differ")


def expected_identity_observations(records):
    return {
        raw: {"matches_start": True, "current": record}
        for raw, record in records.items()
    }


def validate_complete_worker_artifacts(
    worker, report, worker_receipt, report_body, worker_receipt_body,
    capability, args, preflight, worker_pid,
    report_prebound, worker_receipt_prebound, interpreter_binding_sha256,
):
    """Validate every scientific and provenance field before terminal authority."""
    exact_keys(report, REPORT_KEYS, "Worker report")
    exact_keys(worker_receipt, WORKER_RECEIPT_KEYS, "Worker receipt")
    require(encoded_json(report) == report_body
            and encoded_json(worker_receipt) == worker_receipt_body,
            "Worker artifacts are not exact canonical JSON documents")
    verify_artifact_auth(capability, REPORT_NAME, report)
    verify_artifact_auth(capability, WORKER_RECEIPT_NAME, worker_receipt)

    tolerance = report["tolerance"]
    require(type(tolerance) is float and tolerance == 1e-6,
            "Numeric tolerance differs from the frozen contract")
    require(report["cache_commit_sizes"] == [5, 9]
            and report["batch_authoritative_target_counts"] == [4, 4]
            and report["planned_yaw_degrees"]
            == [0.0, 1.25, 2.5, 3.75, 5.0, 3.75, 2.5, 1.25, 0.0],
            "Frozen camera sequence metadata differs")
    finite_error(report["base_homogeneous_row_max_abs"], tolerance,
                 "Base homogeneous-row error")
    validate_error_rows(report["cache_commit_continuity"], range(5), tolerance)
    validate_error_rows(report["batch_target_to_cache"], range(1, 9), tolerance)
    validate_error_rows(report["planned_sequence"], range(9), tolerance, include_yaw=True)
    exact_keys(report["id8_to_id0"], {"pose_max_abs", "K_max_abs"},
               "ID8-to-ID0 closure")
    finite_error(report["id8_to_id0"]["pose_max_abs"], tolerance,
                 "ID8-to-ID0 pose closure")
    finite_error(report["id8_to_id0"]["K_max_abs"], tolerance,
                 "ID8-to-ID0 K closure")
    require(
        report["pixel_score"] == "NOT_EVALUATED"
        and report["visual_quality"] == "NOT_EVALUATED"
        and report["rendered_pixel_camera_obedience"]
        == "NOT_EVALUATED_NO_FROZEN_PROXY"
        and report["method_gain"] == "NOT_EVALUATED"
        and report["novelty"] == "NOT_EVALUATED",
        "A scientific non-goal sentinel differs",
    )

    expected_hashes = {
        "worker_sha256": args.worker_sha256,
        "supervisor_sha256": args.self_sha256,
        "primary_source_review_sha256": args.primary_source_review_sha256,
        "adversarial_source_review_sha256": args.adversarial_source_review_sha256,
        "binding_sha256": args.binding_sha256,
        "binding_review_sha256": args.binding_review_sha256,
        "governance_attestation_sha256": args.governance_attestation_sha256,
        "runtime_interpreter_binding_sha256": interpreter_binding_sha256,
        "archive_manifest_sha256":
            preflight["binding"]["upstream"]["archive_manifest"]["sha256"],
        "archive_events_sha256":
            preflight["binding"]["upstream"]["archive_events"]["sha256"],
        "s45_result_review_sha256":
            preflight["binding"]["upstream"]["s45_result_review"]["sha256"],
    }
    require(all(report[key] == value for key, value in expected_hashes.items()),
            "Worker report source/upstream identities differ")
    expected_source_binding = verify_loaded_worker_lease(worker, args.worker_sha256)
    require(report["executed_worker_source_binding"] == expected_source_binding
            and report["event_chain"] == preflight["event_summary"],
            "Worker execution source or event-chain identity differs")
    body_count = report["c1_tensor_bodies_read"]
    close_count = report["c1_tensor_bodies_close_verified"]
    body_bytes = report["c1_tensor_body_bytes_read"]
    require(type(body_count) is int and type(close_count) is int
            and type(body_bytes) is int and body_count == close_count > 0
            and body_bytes > 0,
            "Worker tensor open/close counters differ")
    validate_camera_tensor_identities(
        report["camera_tensor_identities"], body_count, body_bytes,
    )
    require(
        report["schema"] == "s45b-c1-numeric-camera-guard-worker-report-v3"
        and report["status"]
        == "C1_REQUESTED_CAMERA_INPUT_CONDITION_RESULT_PENDING_EXTERNAL_SUPERVISOR_SEAL"
        and report["passed"] is False and report["terminal_authority"] is False
        and report["row"] == "C1"
        and report["numeric_worker_verdict"]
        == "PASS_C1_REQUESTED_CAMERA_INPUT_CONDITION_GUARD_ONLY"
        and report["external_supervisor_exit_and_terminal_seal_required"] is True
        and type(report["evidence_boundary"]) is str
        and bool(report["evidence_boundary"]),
        "Worker report terminal boundary differs",
    )

    require(
        worker_receipt["schema"]
        == "s45b-c1-numeric-camera-guard-worker-receipt-v3"
        and worker_receipt["status"]
        == "C1_NUMERIC_CAMERA_WORKER_EVIDENCE_WRITTEN_PENDING_PROCESS_EXIT_AND_SUPERVISOR_SEAL"
        and worker_receipt["passed"] is False
        and worker_receipt["terminal_authority"] is False
        and worker_receipt["row"] == "C1"
        and worker_receipt["worker_pid"] == worker_pid
        and worker_receipt["supervisor_pid"] == os.getpid()
        and worker_receipt["attempt"] == 1
        and worker_receipt["automatic_retries"] == 0
        and worker_receipt["numeric_worker_verdict"]
        == report["numeric_worker_verdict"]
        and worker_receipt["report_sha256"] == sha256_bytes(report_body)
        and worker_receipt["sources_and_bound_metadata_unchanged_at_worker_close"] is True
        and worker_receipt["executed_worker_source_binding"] == expected_source_binding
        and worker_receipt["report_artifact_identity"]
        == list(report_prebound["identity"])
        and worker_receipt["worker_receipt_artifact_identity"]
        == list(worker_receipt_prebound["identity"]),
        "Worker receipt execution/evidence binding differs",
    )
    require(all(worker_receipt[key] == expected_hashes[key] for key in (
        "worker_sha256", "supervisor_sha256", "primary_source_review_sha256",
        "adversarial_source_review_sha256", "binding_sha256",
        "binding_review_sha256", "governance_attestation_sha256",
        "runtime_interpreter_binding_sha256",
    )), "Worker receipt source/governance identities differ")
    require(
        worker_receipt["c1_tensor_bodies_read"] == body_count
        and worker_receipt["c1_tensor_bodies_close_verified"] == close_count
        and worker_receipt["c1_tensor_body_bytes_read"] == body_bytes
        and worker_receipt["pixel_bodies_opened"] == 0
        and worker_receipt["pixels_decoded"] == 0
        and worker_receipt["images_viewed"] == 0
        and worker_receipt["model_renderer_generation_runs"] == 0,
        "Worker receipt counters differ",
    )
    expected_records = expected_identity_observations(preflight["records"])
    require(worker_receipt["worker_recheck_identity_records"] == expected_records
            and worker_receipt["worker_close_identity_records"] == expected_records,
            "Worker full source/upstream close observations differ")
    started = datetime.fromisoformat(worker_receipt["started_utc"].replace("Z", "+00:00"))
    completed = datetime.fromisoformat(worker_receipt["completed_utc"].replace("Z", "+00:00"))
    require(started.tzinfo is not None and completed.tzinfo is not None
            and started <= completed <= datetime.now(timezone.utc)
            and type(worker_receipt["elapsed_seconds"]) in (int, float)
            and not isinstance(worker_receipt["elapsed_seconds"], bool)
            and 0.0 <= float(worker_receipt["elapsed_seconds"]) <= TIME_LIMIT_SECONDS,
            "Worker receipt time interval differs")
    return {
        "report_complete_schema_sha256": sha256_bytes(canonical(sorted(REPORT_KEYS))),
        "worker_receipt_complete_schema_sha256":
            sha256_bytes(canonical(sorted(WORKER_RECEIPT_KEYS))),
        "all_numeric_and_provenance_fields_validated": True,
        "artifact_authentication": "HMAC_SHA256_PRIVATE_CAPABILITY",
    }


def signal_handler(signum, frame):
    raise SupervisorTermination("Supervisor received signal " + str(signum))


def write_supervisor_failure(worker, output_fd, phase, error, details):
    if output_fd is None:
        return
    target = (
        SUPERVISOR_RECEIPT_NAME
        if worker.entry_absent(output_fd, SUPERVISOR_RECEIPT_NAME)
        else TERMINAL_FAILURE_NAME
    )
    if not worker.entry_absent(output_fd, target):
        return
    value = {
        "schema": "s45b-c1-numeric-camera-guard-supervisor-failure-v1",
        "status": "FAILED_OR_PARTIAL_C1_NUMERIC_CAMERA_SUPERVISION",
        "passed": False,
        "terminal_authority": False,
        "failed_phase": phase,
        "error_type": type(error).__name__,
        "error": str(error),
        "traceback": traceback.format_exc(),
        "details": details,
        "completed_utc": utc(),
        "pixel_bodies_opened": 0,
        "pixels_decoded": 0,
        "images_viewed": 0,
        "model_renderer_generation_runs": 0,
    }
    try:
        worker.write_new_at(output_fd, target, value)
    except BaseException:
        pass


def formal_supervision(args):
    require(sys.flags.isolated == 1 and sys.flags.dont_write_bytecode == 1 and sys.flags.no_site == 1,
            "Formal supervisor must run with -I -B -S")
    require(Path(args.out).is_absolute() and Path(args.out) == FORMAL_OUT,
            "Only the canonical execution_01 output is accepted")
    worker, worker_source_record = load_worker_same_fd(args.worker_sha256)
    parent_fd = None
    lock_fd = None
    output_fd = None
    capability_read = None
    capability_write = None
    capability = None
    report_prebound = None
    worker_receipt_prebound = None
    process = None
    leases = {}
    phase = "NON_CONSUMING_PREFLIGHT"
    details = {"worker_source": worker_source_record}
    old_term = signal.signal(signal.SIGTERM, signal_handler)
    old_int = signal.signal(signal.SIGINT, signal_handler)
    try:
        parent_flags = (
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        )
        parent_fd = os.open(HERE, parent_flags)
        parent_stat = os.fstat(parent_fd)
        parent_identity = worker.inode_identity(parent_stat)
        require(stat.S_ISDIR(parent_stat.st_mode), "Supervisor source path is not a directory")
        worker.verify_directory_lease(parent_fd, HERE, parent_identity)
        fcntl.flock(parent_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

        preflight = worker.formal_preflight(worker_namespace(args), parent_fd, parent_identity)
        phase = "NON_CONSUMING_RUNTIME_CAPABILITY_PREFLIGHT"
        runtime_preflight = runtime_capability_preflight(worker_source_record)
        runtime_preflight_sha256 = sha256_bytes(canonical(runtime_preflight))
        interpreter_binding = runtime_preflight["running_interpreter_binding"]
        interpreter_binding_sha256 = runtime_preflight[
            "running_interpreter_binding_sha256"
        ]
        require(
            all(worker.entry_absent(parent_fd, name) for name in (
                FORMAL_OUT.name, LOCK.name, LOCK_STAGING.name,
            )),
            "Runtime capability preflight created a formal path",
        )
        capability = secrets.token_bytes(32)
        capability_sha256 = sha256_bytes(capability)
        capability_read, capability_write = os.pipe()
        require(os.write(capability_write, capability) == len(capability),
                "Capability pipe write was incomplete")
        os.close(capability_write)
        capability_write = None
        phase = "ATOMIC_ATTEMPT_COMMIT"
        lease_record = {
            "schema": "s45b-c1-numeric-camera-guard-attempt-lease-v4",
            "status": "FAIL_CLOSED_ATTEMPT_COMMITTED_NO_VALID_TERMINAL_SEAL",
            "passed": False,
            "terminal_authority": False,
            "row": "C1",
            "attempt": 1,
            "attempt_consumed": True,
            "automatic_retries": 0,
            "lease_committed_after_complete_preflight": True,
            "lease_committed_after_runtime_capability_preflight": True,
            "preflight_started_utc": preflight["started_utc"].isoformat(),
            "lease_prepared_utc": utc(),
            "formal_output_path": str(FORMAL_OUT),
            "terminal_candidate_path": str(FORMAL_OUT / TERMINAL_SEAL_NAME),
            "terminal_pass_seal_channel": "complete_exact_supervisor_stdout_json_plus_exit_zero",
            "terminal_authority_rule": (
                "Only the supervisor stdout PASS seal after held-FD candidate single-link commit, "
                "exact evidence revalidation, successful required closes, observed process exit "
                "zero, and independent result review can supersede this default failure; every "
                "canonical candidate remains passed=false"
            ),
            "supplied_identities": {
                "camera_guard.py": args.worker_sha256,
                "supervise_camera_guard.py": args.self_sha256,
                "primary_source_review": args.primary_source_review_sha256,
                "adversarial_source_review": args.adversarial_source_review_sha256,
                "C1_CAMERA_GUARD_BINDING_V10.json": args.binding_sha256,
                "BINDING_REVIEW_V10.json": args.binding_review_sha256,
                "governance_attestation": args.governance_attestation_sha256,
            },
            "capability_sha256": capability_sha256,
            "runtime_interpreter_binding_sha256": interpreter_binding_sha256,
            "worker_launch_mechanism":
                "FORK_ALREADY_RUNNING_INTERPRETER_THEN_SANDBOX_INIT_NO_EXEC",
            "runtime_capability_preflight": {
                "status": "PASS_CAPABILITY_PROBE_ONLY_BEFORE_ATTEMPT_COMMIT",
                "record_sha256": runtime_preflight_sha256,
                "record": runtime_preflight,
            },
            "c1_tensor_bodies_read": 0,
            "c1_tensor_body_bytes_read": 0,
            "pixel_bodies_opened": 0,
            "pixels_decoded": 0,
            "images_viewed": 0,
            "model_renderer_generation_runs": 0,
        }
        lock_fd, lock_identity, lock_sha256, lock_bytes = worker.commit_attempt_lease(
            parent_fd, HERE, parent_identity, LOCK.name, LOCK_STAGING.name, lease_record,
        )
        phase = "CANONICAL_OUTPUT_LEASE"
        output_fd, output_identity = worker.create_output_lease(parent_fd, parent_identity)
        phase = "PRESPAWN_CREATE_ONLY_WORKER_OUTPUT_BINDING"
        report_prebound = create_prebound_worker_artifact(
            output_fd, FORMAL_OUT, REPORT_NAME,
        )
        worker_receipt_prebound = create_prebound_worker_artifact(
            output_fd, FORMAL_OUT, WORKER_RECEIPT_NAME,
        )
        leases[REPORT_NAME] = report_prebound
        leases[WORKER_RECEIPT_NAME] = worker_receipt_prebound
        worker_namespace_bound = formal_worker_namespace(
            args, capability_read, capability_sha256,
            parent_fd, parent_identity, lock_fd, lock_identity,
            lock_sha256, lock_bytes, output_fd, output_identity,
            worker._held_source_lease, report_prebound, worker_receipt_prebound,
            interpreter_binding_sha256,
        )

        phase = "WORKER_PROCESS_SPAWN_AND_WAIT"
        binding_now, binding_now_sha256 = current_interpreter_binding()
        require(binding_now == interpreter_binding
                and binding_now_sha256 == interpreter_binding_sha256,
                "Running interpreter binding changed before formal worker fork")
        verify_loaded_worker_lease(worker, args.worker_sha256)
        verify_prebound_worker_artifact(
            output_fd, FORMAL_OUT, report_prebound, require_empty=True,
        )
        verify_prebound_worker_artifact(
            output_fd, FORMAL_OUT, worker_receipt_prebound, require_empty=True,
        )
        started_monotonic = time.monotonic()
        process = spawn_bound_worker(
            worker, worker_namespace_bound,
            interpreter_binding, interpreter_binding_sha256,
        )
        os.close(capability_read)
        capability_read = None
        observation = bounded_process_wait(
            process, expected_process_uuid=interpreter_binding["process_uuid"],
        )
        elapsed = time.monotonic() - started_monotonic
        stdout = observation["stdout"]
        stderr = observation["stderr"]
        usage = {
            "elapsed_seconds": elapsed,
            "user_cpu_seconds": observation["user_cpu_seconds"],
            "system_cpu_seconds": observation["system_cpu_seconds"],
            "wait4_peak_rss_bytes": observation["wait4_peak_rss_bytes"],
            "peak_phys_footprint_bytes": observation["peak_phys_footprint_bytes"],
            "peak_resident_size_bytes": observation["peak_resident_size_bytes"],
            "max_observed_memory_bytes": observation["max_observed_memory_bytes"],
            "memory_monitor_samples": observation["memory_monitor_samples"],
            "process_uuid": observation["process_uuid"],
            "expected_process_uuid": observation["expected_process_uuid"],
            "stdout_bytes": len(stdout),
            "stdout_sha256": sha256_bytes(stdout),
            "stderr_bytes": len(stderr),
            "stderr_sha256": sha256_bytes(stderr),
            "time_limit_seconds": TIME_LIMIT_SECONDS,
            "cpu_limit_seconds": CPU_LIMIT_SECONDS,
            "rss_limit_bytes": MAX_WORKER_RSS_BYTES,
            "stdout_limit_bytes": MAX_STDOUT_BYTES,
            "stderr_limit_bytes": MAX_STDERR_BYTES,
            "memory_mechanism": "Darwin proc_pid_rusage V4 plus exact-pid wait4 high-water evidence",
        }
        details.update(
            worker_pid=process.pid,
            worker_returncode=observation["returncode"],
            timed_out=observation["timed_out"],
            output_limit_exceeded=observation["output_limit_exceeded"],
            memory_limit_exceeded=observation["memory_limit_exceeded"],
            memory_monitor_failed=observation["memory_monitor_failed"],
            no_fork_sandbox_preflight_sha256=runtime_preflight_sha256,
            fork_bound_execution=process.execution_binding,
            resource_usage=usage,
        )
        require(
            not observation["timed_out"]
            and not observation["output_limit_exceeded"]
            and not observation["memory_limit_exceeded"]
            and not observation["memory_monitor_failed"]
            and observation["returncode"] == 0
            and len(stdout) == 0 and len(stderr) == 0
            and elapsed <= TIME_LIMIT_SECONDS
            and usage["user_cpu_seconds"] + usage["system_cpu_seconds"] <= CPU_LIMIT_SECONDS + 1
            and usage["max_observed_memory_bytes"] <= MAX_WORKER_RSS_BYTES,
            "Worker exit, no-fork containment, stdio, time, CPU, or memory boundary failed",
        )

        phase = "WORKER_EVIDENCE_AND_SOURCE_REVALIDATION"
        worker.verify_directory_lease(
            parent_fd, HERE, parent_identity,
            output_fd, FORMAL_OUT.name, output_identity,
        )
        worker.verify_lock_lease(
            parent_fd, HERE, parent_identity, lock_fd, LOCK.name,
            lock_identity, lock_sha256, lock_bytes,
        )
        unchanged, supervisor_close_records = worker.same_records(
            preflight["records"], preflight["deadline"],
        )
        require(unchanged, "Source or bound metadata changed after worker exit")
        report_record, report_body = verify_prebound_worker_artifact(
            output_fd, FORMAL_OUT, report_prebound,
        )
        worker_record, worker_receipt_body = verify_prebound_worker_artifact(
            output_fd, FORMAL_OUT, worker_receipt_prebound,
        )
        report_prebound["record"] = report_record
        report_prebound["body"] = report_body
        worker_receipt_prebound["record"] = worker_record
        worker_receipt_prebound["body"] = worker_receipt_body
        report_lease = report_prebound
        worker_lease = worker_receipt_prebound
        report = json.loads(report_lease["body"].decode("utf-8"))
        worker_receipt = json.loads(worker_lease["body"].decode("utf-8"))
        complete_validation = validate_complete_worker_artifacts(
            worker, report, worker_receipt,
            report_body, worker_receipt_body, capability,
            args, preflight, process.pid,
            report_prebound, worker_receipt_prebound,
            interpreter_binding_sha256,
        )
        initial_bundle = collect_evidence_bundle(
            worker, parent_fd, HERE, parent_identity,
            lock_fd, LOCK.name, lock_identity, lock_sha256, lock_bytes,
            output_fd, FORMAL_OUT.name, output_identity,
            leases, sorted(leases),
        )

        phase = "SUPERVISOR_PENDING_RECEIPT_WRITE"
        supervisor_receipt = {
            "schema": "s45b-c1-numeric-camera-guard-supervisor-receipt-v2",
            "status": "WORKER_EXIT_ZERO_AND_EVIDENCE_OBSERVED_PENDING_TERMINAL_SEAL",
            "passed": False,
            "terminal_authority": False,
            "row": "C1",
            "supervisor_sha256": args.self_sha256,
            "worker_sha256": args.worker_sha256,
            "worker_returncode": observation["returncode"],
            "worker_exact_pid_reaped_with_wait4": True,
            "worker_process_creation_denied_by_darwin_sandbox": True,
            "worker_no_descendant_claim_scope": "NO_FORK_OR_POSIX_SPAWN_EXACT_WORKER_ONLY",
            "worker_timed_out": observation["timed_out"],
            "worker_output_limit_exceeded": observation["output_limit_exceeded"],
            "worker_memory_limit_exceeded": observation["memory_limit_exceeded"],
            "worker_memory_monitor_failed": observation["memory_monitor_failed"],
            "worker_stdout_empty": len(stdout) == 0,
            "worker_stderr_empty": len(stderr) == 0,
            "worker_resource_usage": usage,
            "fork_bound_worker_execution": process.execution_binding,
            "complete_worker_artifact_validation": complete_validation,
            "runtime_capability_preflight_sha256": runtime_preflight_sha256,
            "runtime_interpreter_binding_sha256": interpreter_binding_sha256,
            "capability_sha256_bound_in_permanent_lock": capability_sha256,
            "governance_attestation_sha256": args.governance_attestation_sha256,
            "worker_report": report_lease["record"],
            "worker_receipt": worker_lease["record"],
            "initial_post_exit_evidence": initial_bundle,
            "source_and_bound_metadata_unchanged_after_worker_exit": True,
            "source_close_records": supervisor_close_records,
            "completed_utc": utc(),
            "terminal_seal_required": True,
            "independent_result_review_required": True,
            "pixel_bodies_opened": 0,
            "pixels_decoded": 0,
            "images_viewed": 0,
            "model_renderer_generation_runs": 0,
        }
        supervisor_sha256 = worker.write_new_at(
            output_fd, SUPERVISOR_RECEIPT_NAME, supervisor_receipt,
        )
        supervisor_lease = open_regular_lease(
            output_fd, FORMAL_OUT, SUPERVISOR_RECEIPT_NAME, supervisor_sha256,
        )
        leases[SUPERVISOR_RECEIPT_NAME] = supervisor_lease

        phase = "TERMINALIZATION_BARRIER_WRITE"
        before_barrier = collect_evidence_bundle(
            worker, parent_fd, HERE, parent_identity,
            lock_fd, LOCK.name, lock_identity, lock_sha256, lock_bytes,
            output_fd, FORMAL_OUT.name, output_identity,
            leases, sorted(leases),
        )
        barrier = {
            "schema": "s45b-c1-numeric-camera-guard-terminalization-barrier-v1",
            "status": "PENDING_NONAUTHORITATIVE_TERMINALIZATION_BARRIER",
            "passed": False,
            "terminal_authority": False,
            "before_barrier_evidence": before_barrier,
            "created_utc": utc(),
        }
        barrier_sha256 = worker.write_new_at(output_fd, BARRIER_NAME, barrier)
        barrier_lease = open_regular_lease(
            output_fd, FORMAL_OUT, BARRIER_NAME, barrier_sha256,
        )
        leases[BARRIER_NAME] = barrier_lease
        after_barrier = collect_evidence_bundle(
            worker, parent_fd, HERE, parent_identity,
            lock_fd, LOCK.name, lock_identity, lock_sha256, lock_bytes,
            output_fd, FORMAL_OUT.name, output_identity,
            leases, sorted(leases),
        )
        require(
            stable_evidence_projection(after_barrier)["permanent_lock"]
            == stable_evidence_projection(before_barrier)["permanent_lock"]
            and stable_evidence_projection(after_barrier)["canonical_execution_identity"]
            == stable_evidence_projection(before_barrier)["canonical_execution_identity"]
            and all(
                after_barrier["artifacts"][name] == before_barrier["artifacts"][name]
                for name in before_barrier["artifacts"]
            ),
            "Evidence changed across terminalization barrier",
        )

        phase = "ATOMIC_TERMINAL_CANDIDATE"
        seal = {
            "schema": "s45b-c1-numeric-camera-guard-terminal-candidate-v4",
            "status": "NUMERIC_WORKER_PASS_PENDING_HELD_FD_CLOSE_AND_EXTERNAL_EXIT_ZERO",
            "passed": False,
            "terminal_authority": False,
            "row": "C1",
            "numeric_worker_verdict": report["numeric_worker_verdict"],
            "worker_returncode_observed": 0,
            "worker_exact_pid_reaped_with_wait4": True,
            "worker_process_creation_denied_by_darwin_sandbox": True,
            "worker_no_descendant_claim_scope": "NO_FORK_OR_POSIX_SPAWN_EXACT_WORKER_ONLY",
            "worker_timed_out": False,
            "worker_output_limit_exceeded": False,
            "worker_memory_limit_exceeded": False,
            "worker_memory_monitor_failed": False,
            "worker_stdout_empty": True,
            "worker_stderr_empty": True,
            "worker_resource_boundaries_passed": True,
            "fork_bound_worker_execution": process.execution_binding,
            "complete_worker_artifact_validation": complete_validation,
            "runtime_capability_preflight_sha256": runtime_preflight_sha256,
            "runtime_interpreter_binding_sha256": interpreter_binding_sha256,
            "capability_sha256_bound_in_permanent_lock": capability_sha256,
            "supervisor_sha256": args.self_sha256,
            "worker_sha256": args.worker_sha256,
            "primary_source_review_sha256": args.primary_source_review_sha256,
            "adversarial_source_review_sha256": args.adversarial_source_review_sha256,
            "binding_sha256": args.binding_sha256,
            "binding_review_sha256": args.binding_review_sha256,
            "governance_attestation_sha256": args.governance_attestation_sha256,
            "attempt_lock_sha256": lock_sha256,
            "post_worker_exit_and_post_barrier_evidence": after_barrier,
            "prebound_worker_output_fds_held_from_before_spawn_through_validation": True,
            "canonical_path_alone_is_authoritative": False,
            "completed_utc": utc(),
            "independent_result_review_required": True,
            "evidence_boundary": (
                "Requested archived c2w/K input-condition validity only; no pixel score, "
                "quality, rendered-camera obedience, method gain, causal result, or novelty"
            ),
        }
        terminal_observation = publish_terminal_seal(
            worker, parent_fd, HERE, parent_identity,
            lock_fd, LOCK.name, lock_identity, lock_sha256, lock_bytes,
            output_fd, FORMAL_OUT.name, output_identity, leases, seal,
        )
        require(
            terminal_observation.get("status")
            == "HELD_CANDIDATE_READY_FOR_EXTERNAL_EXIT_GATED_SEAL"
            and terminal_observation.get("passed") is False
            and terminal_observation.get("terminal_authority") is False
            and terminal_observation.get("candidate_sha256") is not None
            and canonical_seal_matches_held_observation(output_fd, terminal_observation),
            "Held terminal authority observation did not survive exact diagnostic recheck",
        )
        details["held_candidate_observation"] = terminal_observation
        phase = "FINAL_HELD_WORKER_SOURCE_CLOSE"
        verify_loaded_worker_lease(worker, args.worker_sha256)
        close_loaded_worker_lease(worker)
        phase = "FINAL_FILESYSTEM_CONTROL_FD_CLOSE"
        close_terminal_control_fds(output_fd, lock_fd, parent_fd)
        output_fd = None
        lock_fd = None
        parent_fd = None
        phase = "EXTERNAL_HELD_FD_AUTHORITY_EMISSION"
        external_authority = {
            "schema": "s45b-c1-numeric-camera-guard-terminal-pass-seal-v4",
            "status": "PASS_C1_REQUESTED_CAMERA_INPUT_CONDITION_GUARD_ONLY",
            "passed": True,
            "terminal_authority": True,
            "held_candidate_observation": terminal_observation,
            "supervisor_sha256": args.self_sha256,
            "worker_sha256": args.worker_sha256,
            "attempt_lock_sha256": lock_sha256,
            "governance_attestation_sha256": args.governance_attestation_sha256,
            "canonical_path_alone_is_authoritative": False,
            "all_filesystem_control_fds_closed_before_pass_construction": True,
            "held_worker_source_fd_verified_and_closed_before_pass_construction": True,
            "requires_complete_exact_stdout_json": True,
            "requires_supervisor_process_exit_zero": True,
            "independent_result_review_required": True,
        }
        external_body = encoded_json(external_authority)
        write_all(sys.stdout.fileno(), external_body)
        sys.stdout.flush()
        return 0
    except BaseException as error:
        if process is not None and process.returncode is None:
            terminate_exact_process(process.pid)
            try:
                waited_pid, status, _ = os.wait4(process.pid, 0)
                if waited_pid == process.pid:
                    process.returncode = os.waitstatus_to_exitcode(status)
            except BaseException:
                pass
        if output_fd is not None:
            write_supervisor_failure(worker, output_fd, phase, error, details)
        return 2
    finally:
        signal.signal(signal.SIGTERM, old_term)
        signal.signal(signal.SIGINT, old_int)
        try:
            close_leases(leases)
        except OSError:
            pass
        try:
            close_loaded_worker_lease(worker)
        except OSError:
            pass
        for fd in (capability_write, capability_read, output_fd, lock_fd, parent_fd):
            if type(fd) is int and fd >= 0:
                try:
                    os.close(fd)
                except OSError:
                    pass


def synthetic_prebound_writer(worker, output_fd, report_lease, receipt_lease, secret):
    worker.write_prebound_json(
        output_fd, REPORT_NAME, report_lease["fd"], report_lease["identity"],
        {"schema": "synthetic-prebound-report", "passed": False}, secret,
    )
    worker.write_prebound_json(
        output_fd, WORKER_RECEIPT_NAME, receipt_lease["fd"],
        receipt_lease["identity"],
        {"schema": "synthetic-prebound-receipt", "passed": False}, secret,
    )
    return 0


def synthetic_loaded_code_entry(code, output_fd):
    module = types.ModuleType("_s45b_v10_synthetic_exact_loaded_code")
    module.__file__ = "/synthetic/held/source.py"
    exec(code, module.__dict__)
    return module.entry(output_fd)


def synthetic_numeric_result(worker):
    base = [
        [1.0, 0.0, 0.0, 1.25],
        [0.0, 0.0, -1.0, -0.5],
        [0.0, 1.0, 0.0, 2.75],
        [0.0, 0.0, 0.0, 1.0],
    ]
    k = [[500.0, 0.0, 288.0], [0.0, 500.0, 288.0], [0.0, 0.0, 1.0]]
    poses = [worker.expected_pose(base, yaw) for yaw in worker.EXPECTED_YAW]
    ks = [[row[:] for row in k] for _ in range(9)]
    batches = [
        {"c2ws": poses[1:5], "Ks": ks[1:5]},
        {"c2ws": poses[5:9], "Ks": ks[5:9]},
    ]
    commits = [
        {"c2ws": poses[:5], "Ks": ks[:5]},
        {"c2ws": poses[:9], "Ks": ks[:9]},
    ]
    return worker.evaluate_numeric_guard(batches, commits)


def signed_fixture(secret, name, value):
    result = dict(value)
    result["artifact_authentication_hmac_sha256"] = artifact_auth_tag(
        secret, name, value,
    )
    return result, encoded_json(result)


def complete_synthetic_worker_fixture(worker, secret):
    result = synthetic_numeric_result(worker)
    verdict = result.pop("status")
    dummy = "a" * 64
    source_binding = verify_loaded_worker_lease(worker)
    event_chain = {"event_count": 1, "last_event_sha256": "b" * 64}
    report_identity = (41, 43, stat.S_IFREG | 0o400)
    receipt_identity = (41, 47, stat.S_IFREG | 0o400)
    report = dict(result)
    report.update(
        schema="s45b-c1-numeric-camera-guard-worker-report-v3",
        status="C1_REQUESTED_CAMERA_INPUT_CONDITION_RESULT_PENDING_EXTERNAL_SUPERVISOR_SEAL",
        passed=False,
        terminal_authority=False,
        row="C1",
        numeric_worker_verdict=verdict,
        worker_sha256=source_binding["sha256"],
        supervisor_sha256="c" * 64,
        primary_source_review_sha256="d" * 64,
        adversarial_source_review_sha256="e" * 64,
        binding_sha256="f" * 64,
        binding_review_sha256="1" * 64,
        governance_attestation_sha256="2" * 64,
        runtime_interpreter_binding_sha256="3" * 64,
        executed_worker_source_binding=source_binding,
        archive_manifest_sha256="4" * 64,
        archive_events_sha256="5" * 64,
        s45_result_review_sha256="6" * 64,
        event_chain=event_chain,
        camera_tensor_identities={
            "tensors/" + dummy + ".bin": {
                "descriptor_sha256": dummy,
                "body_sha256": "7" * 64,
                "dtype": "float64",
                "shape": [4, 4],
                "nbytes": 128,
            },
        },
        c1_tensor_bodies_read=1,
        c1_tensor_bodies_close_verified=1,
        c1_tensor_body_bytes_read=128,
        external_supervisor_exit_and_terminal_seal_required=True,
        evidence_boundary="SYNTHETIC_REQUESTED_C2W_K_ONLY",
    )
    report, report_body = signed_fixture(secret, REPORT_NAME, report)
    now = utc()
    receipt = {
        "schema": "s45b-c1-numeric-camera-guard-worker-receipt-v3",
        "status": "C1_NUMERIC_CAMERA_WORKER_EVIDENCE_WRITTEN_PENDING_PROCESS_EXIT_AND_SUPERVISOR_SEAL",
        "row": "C1", "passed": False, "terminal_authority": False,
        "worker_pid": 4242, "supervisor_pid": os.getpid(),
        "started_utc": now, "attempt": 1, "automatic_retries": 0,
        "worker_sha256": source_binding["sha256"],
        "supervisor_sha256": "c" * 64,
        "primary_source_review_sha256": "d" * 64,
        "adversarial_source_review_sha256": "e" * 64,
        "binding_sha256": "f" * 64,
        "binding_review_sha256": "1" * 64,
        "governance_attestation_sha256": "2" * 64,
        "runtime_interpreter_binding_sha256": "3" * 64,
        "pixel_bodies_opened": 0, "pixels_decoded": 0, "images_viewed": 0,
        "model_renderer_generation_runs": 0,
        "numeric_worker_verdict": verdict,
        "report_sha256": sha256_bytes(report_body),
        "c1_tensor_bodies_read": 1,
        "c1_tensor_bodies_close_verified": 1,
        "c1_tensor_body_bytes_read": 128,
        "sources_and_bound_metadata_unchanged_at_worker_close": True,
        "worker_recheck_identity_records": {},
        "worker_close_identity_records": {},
        "elapsed_seconds": 0.01,
        "completed_utc": now,
        "executed_worker_source_binding": source_binding,
        "report_artifact_identity": list(report_identity),
        "worker_receipt_artifact_identity": list(receipt_identity),
    }
    receipt, receipt_body = signed_fixture(secret, WORKER_RECEIPT_NAME, receipt)
    args = argparse.Namespace(
        worker_sha256=source_binding["sha256"], self_sha256="c" * 64,
        primary_source_review_sha256="d" * 64,
        adversarial_source_review_sha256="e" * 64,
        binding_sha256="f" * 64, binding_review_sha256="1" * 64,
        governance_attestation_sha256="2" * 64,
    )
    preflight = {
        "records": {}, "event_summary": event_chain,
        "binding": {"upstream": {
            "archive_manifest": {"sha256": "4" * 64},
            "archive_events": {"sha256": "5" * 64},
            "s45_result_review": {"sha256": "6" * 64},
        }},
    }
    return {
        "report": report, "report_body": report_body,
        "receipt": receipt, "receipt_body": receipt_body,
        "args": args, "preflight": preflight, "worker_pid": 4242,
        "report_prebound": {"identity": report_identity},
        "receipt_prebound": {"identity": receipt_identity},
        "interpreter_binding_sha256": "3" * 64,
    }


def synthetic_setup(worker, root):
    parent_flags = (
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    )
    parent_fd = os.open(root, parent_flags)
    fcntl.flock(parent_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    parent_identity = worker.inode_identity(os.fstat(parent_fd))
    lock_doc = {
        "schema": "synthetic-v10-attempt-lock-v1",
        "status": "FAIL_CLOSED_ATTEMPT_COMMITTED_NO_VALID_TERMINAL_SEAL",
        "passed": False,
    }
    lock_fd, lock_identity, lock_sha, lock_bytes = worker.commit_attempt_lease(
        parent_fd, root, parent_identity, "attempt.lock", "attempt.lock.staging", lock_doc,
    )
    os.mkdir("execution", 0o700, dir_fd=parent_fd)
    output_fd = os.open(
        "execution",
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
        dir_fd=parent_fd,
    )
    output_identity = worker.inode_identity(os.fstat(output_fd))
    for name, value in (
        (REPORT_NAME, {"schema": "synthetic-report", "status": "PENDING", "passed": False}),
        (WORKER_RECEIPT_NAME, {"schema": "synthetic-worker", "status": "PENDING", "passed": False}),
        (SUPERVISOR_RECEIPT_NAME, {"schema": "synthetic-supervisor", "status": "PENDING", "passed": False}),
        (BARRIER_NAME, {"schema": "synthetic-barrier", "status": "PENDING", "passed": False}),
    ):
        worker.write_new_at(output_fd, name, value)
    leases = {
        name: open_regular_lease(output_fd, Path(root) / "execution", name)
        for name in (REPORT_NAME, WORKER_RECEIPT_NAME, SUPERVISOR_RECEIPT_NAME, BARRIER_NAME)
    }
    seal = {
        "schema": "s45b-c1-numeric-camera-guard-terminal-candidate-v4",
        "status": "NUMERIC_WORKER_PASS_PENDING_HELD_FD_CLOSE_AND_EXTERNAL_EXIT_ZERO",
        "passed": False,
        "terminal_authority": False,
        "numeric_worker_verdict": "PASS_C1_REQUESTED_CAMERA_INPUT_CONDITION_GUARD_ONLY",
        "row": "C1",
        "synthetic_only": True,
    }
    return {
        "root": Path(root), "parent_fd": parent_fd, "parent_identity": parent_identity,
        "lock_fd": lock_fd, "lock_identity": lock_identity,
        "lock_sha": lock_sha, "lock_bytes": lock_bytes,
        "output_fd": output_fd, "output_identity": output_identity,
        "leases": leases, "seal": seal,
    }


def synthetic_close(state):
    try:
        close_leases(state.get("leases", {}))
    except BaseException:
        pass
    for name in ("output_fd", "lock_fd", "parent_fd"):
        fd = state.get(name)
        if type(fd) is int and fd >= 0:
            try:
                os.close(fd)
            except OSError:
                pass


def assert_no_true_pass_paths(output_fd):
    """Synthetic oracle: interrupted filesystem states contain no truthy PASS."""
    for name in (TERMINAL_SEAL_NAME, TERMINAL_SEAL_STAGING_NAME):
        try:
            fd = os.open(
                name,
                os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=output_fd,
            )
        except FileNotFoundError:
            continue
        try:
            held = os.fstat(fd)
            named = os.stat(name, dir_fd=output_fd, follow_symlinks=False)
            require(stat.S_ISREG(held.st_mode) and stat_record(held) == stat_record(named),
                    "Synthetic candidate path identity differs")
            parsed = json.loads(read_exact_fd(fd, held.st_size).decode("utf-8"))
            require(parsed.get("passed") is False
                    and parsed.get("terminal_authority") is False,
                    "Interrupted candidate path contains a truthy PASS")
        finally:
            os.close(fd)


def write_raw_new_at(directory_fd, name, body):
    """Synthetic helper for identical-byte inode replacement attacks."""
    fd = os.open(
        name,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
        0o600, dir_fd=directory_fd,
    )
    try:
        offset = 0
        while offset < len(body):
            written = os.write(fd, body[offset:])
            require(written > 0, "Synthetic replacement write made no progress")
            offset += written
        os.fsync(fd)
    finally:
        os.close(fd)


def synthetic_publish(worker, state, fault=None):
    return publish_terminal_seal(
        worker,
        state["parent_fd"], state["root"], state["parent_identity"],
        state["lock_fd"], "attempt.lock", state["lock_identity"],
        state["lock_sha"], state["lock_bytes"],
        state["output_fd"], "execution", state["output_identity"],
        state["leases"], state["seal"], fault=fault,
    )


def checked_synthetic_root(raw):
    root = Path(raw).resolve()
    temp_root = Path(tempfile.gettempdir()).resolve()
    require(root.parent == temp_root and root.name.startswith("s45b_supervised_fault_"),
            "Synthetic fault child is outside its isolated temporary root")
    require(root != HERE and FORMAL_OUT not in (root, *root.parents),
            "Synthetic fault child aliases a formal project path")
    return root


def synthetic_fault_child(raw_root, fault):
    root = checked_synthetic_root(raw_root)
    worker, _ = load_worker_same_fd()
    state = synthetic_setup(worker, root)
    try:
        synthetic_publish(worker, state, fault=fault)
    finally:
        synthetic_close(state)
    return 99


def isolated_fault_process(root, fault):
    process = subprocess.Popen(
        [str(PYTHON_EXECUTABLE), "-I", "-B", "-S", str(SELF),
         "--synthetic-fault-child", fault, "--synthetic-root", str(root)],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        start_new_session=True,
    )
    stdout, stderr = process.communicate(timeout=30)
    return process.returncode, stdout, stderr


def synthetic_resource_child(mode):
    if mode in ("STDOUT_OVERFLOW", "STDERR_OVERFLOW"):
        fd = 1 if mode == "STDOUT_OVERFLOW" else 2
        body = b"x" * (max(MAX_STDOUT_BYTES, MAX_STDERR_BYTES) + 4096)
        offset = 0
        while offset < len(body):
            offset += os.write(fd, body[offset:])
        return 0
    if mode == "SLEEP_TIMEOUT":
        while True:
            time.sleep(1)
    raise AssertionError("Unknown synthetic resource child")


def isolated_resource_process(mode, time_limit=5.0):
    process = spawn_contained(
        [str(PYTHON_EXECUTABLE), "-I", "-B", "-S", str(SELF),
         "--synthetic-resource-child", mode],
    )
    return bounded_process_wait(
        process, time_limit=time_limit,
    )


def synthetic_selftest():
    worker, worker_record = load_worker_same_fd()
    checks = {}

    runtime = runtime_capability_preflight(worker_record)
    require(runtime["status"] == "PASS_BEFORE_ATTEMPT_COMMIT"
            and all(item["result"] == "DENIED_BY_SANDBOX"
                    for item in runtime["probe"]["sandbox_attacks"].values()),
            "Exact production containment preflight failed")
    checks["exact_production_launcher_preflight_before_attempt"] = "PASS"
    checks["fork_setsid_keep_stdio_denied"] = "PASS_KERNEL_EPERM"
    checks["fork_setsid_close_stdio_denied"] = "PASS_KERNEL_EPERM"
    checks["posix_spawn_setsid_denied"] = "PASS_KERNEL_EPERM"

    # V6's missing acquisition-window attack: the parent creates both inodes
    # before fork, the child writes only inherited FDs, and the parent never
    # reopens either pathname to acquire authority.
    with tempfile.TemporaryDirectory(prefix="s45b_v10_prebound_nominal_") as raw:
        root = Path(raw).resolve()
        os.mkdir(root / "execution", 0o700)
        output_fd = os.open(
            root / "execution", os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
        report_bound = create_prebound_worker_artifact(
            output_fd, root / "execution", REPORT_NAME,
        )
        receipt_bound = create_prebound_worker_artifact(
            output_fd, root / "execution", WORKER_RECEIPT_NAME,
        )
        secret = secrets.token_bytes(32)
        interpreter, interpreter_sha = current_interpreter_binding()
        process = _fork_loaded_entry(
            synthetic_prebound_writer,
            (worker, output_fd, report_bound, receipt_bound, secret),
            (output_fd, report_bound["fd"], receipt_bound["fd"]),
            {"schema": "synthetic-v10-prebound-writer",
             "interpreter_binding_sha256": interpreter_sha},
        )
        observation = bounded_process_wait(
            process, time_limit=5.0,
            expected_process_uuid=interpreter["process_uuid"],
        )
        require(observation["returncode"] == 0 and observation["stdout"] == b""
                and observation["stderr"] == b"",
                "Inherited prebound-FD writer failed")
        for name, lease in ((REPORT_NAME, report_bound),
                            (WORKER_RECEIPT_NAME, receipt_bound)):
            record, body = verify_prebound_worker_artifact(
                output_fd, root / "execution", lease,
            )
            payload = json.loads(body.decode("utf-8"))
            verify_artifact_auth(secret, name, payload)
            require(record["read_channel"]
                    == "SUPERVISOR_HELD_PRESPAWN_FD_NO_PATH_REOPEN",
                    "Prebound evidence was not read from the parent-held FD")
        close_leases({"report": report_bound, "receipt": receipt_bound})
        os.close(output_fd)
    checks["prespawn_create_only_pair_child_inherited_fd_publication"] = "PASS"

    for attacked_name in (REPORT_NAME, WORKER_RECEIPT_NAME):
        with tempfile.TemporaryDirectory(prefix="s45b_v10_prelaunch_swap_") as raw:
            root = Path(raw).resolve()
            os.mkdir(root / "execution", 0o700)
            output_fd = os.open(root / "execution", os.O_RDONLY | os.O_DIRECTORY)
            report_bound = create_prebound_worker_artifact(
                output_fd, root / "execution", REPORT_NAME,
            )
            receipt_bound = create_prebound_worker_artifact(
                output_fd, root / "execution", WORKER_RECEIPT_NAME,
            )
            leases_by_name = {REPORT_NAME: report_bound,
                              WORKER_RECEIPT_NAME: receipt_bound}
            os.rename(attacked_name, attacked_name + ".original",
                      src_dir_fd=output_fd, dst_dir_fd=output_fd)
            write_raw_new_at(output_fd, attacked_name, b"")
            try:
                verify_prebound_worker_artifact(
                    output_fd, root / "execution", leases_by_name[attacked_name],
                    require_empty=True,
                )
            except (ValueError, OSError):
                checks["prespawn_" + attacked_name + "_substitution"] = "PASS_REJECTED"
            else:
                raise AssertionError("Pre-spawn output substitution was accepted")
            close_leases({"report": report_bound, "receipt": receipt_bound})
            os.close(output_fd)

    for attacked_name in (REPORT_NAME, WORKER_RECEIPT_NAME):
        with tempfile.TemporaryDirectory(prefix="s45b_v10_preacquire_swap_") as raw:
            root = Path(raw).resolve()
            os.mkdir(root / "execution", 0o700)
            output_fd = os.open(root / "execution", os.O_RDONLY | os.O_DIRECTORY)
            report_bound = create_prebound_worker_artifact(
                output_fd, root / "execution", REPORT_NAME,
            )
            receipt_bound = create_prebound_worker_artifact(
                output_fd, root / "execution", WORKER_RECEIPT_NAME,
            )
            secret = secrets.token_bytes(32)
            synthetic_prebound_writer(
                worker, output_fd, report_bound, receipt_bound, secret,
            )
            leases_by_name = {REPORT_NAME: report_bound,
                              WORKER_RECEIPT_NAME: receipt_bound}
            os.rename(attacked_name, attacked_name + ".honest",
                      src_dir_fd=output_fd, dst_dir_fd=output_fd)
            forged = encoded_json({
                "schema": "same-user-forged", "passed": False,
                "artifact_authentication_hmac_sha256": "0" * 64,
            })
            write_raw_new_at(output_fd, attacked_name, forged)
            try:
                verify_prebound_worker_artifact(
                    output_fd, root / "execution", leases_by_name[attacked_name],
                )
            except (ValueError, OSError):
                checks["preacquisition_" + attacked_name + "_substitution"] = "PASS_REJECTED"
            else:
                raise AssertionError("Pre-acquisition output substitution was accepted")
            close_leases({"report": report_bound, "receipt": receipt_bound})
            os.close(output_fd)

    with tempfile.TemporaryDirectory(prefix="s45b_v10_same_inode_tamper_") as raw:
        root = Path(raw).resolve()
        os.mkdir(root / "execution", 0o700)
        output_fd = os.open(root / "execution", os.O_RDONLY | os.O_DIRECTORY)
        report_bound = create_prebound_worker_artifact(
            output_fd, root / "execution", REPORT_NAME,
        )
        receipt_bound = create_prebound_worker_artifact(
            output_fd, root / "execution", WORKER_RECEIPT_NAME,
        )
        secret = secrets.token_bytes(32)
        synthetic_prebound_writer(worker, output_fd, report_bound, receipt_bound, secret)
        forged = encoded_json({
            "schema": "same-inode-forged", "passed": False,
            "artifact_authentication_hmac_sha256": "0" * 64,
        })
        os.pwrite(report_bound["fd"], forged, 0)
        os.ftruncate(report_bound["fd"], len(forged))
        os.fsync(report_bound["fd"])
        _, body = verify_prebound_worker_artifact(
            output_fd, root / "execution", report_bound,
        )
        try:
            verify_artifact_auth(secret, REPORT_NAME, json.loads(body.decode("utf-8")))
        except ValueError:
            checks["same_inode_report_tamper_without_capability"] = "PASS_REJECTED_HMAC"
        else:
            raise AssertionError("Unauthenticated same-inode tamper was accepted")
        close_leases({"report": report_bound, "receipt": receipt_bound})
        os.close(output_fd)

    # Force the exact V6 race on a disposable source: replace its pathname
    # after compilation but before fork.  The child still executes ORIGINAL
    # because the code object and interpreter image are inherited, not reopened.
    with tempfile.TemporaryDirectory(prefix="s45b_v10_source_exec_binding_") as raw:
        source_path = Path(raw) / "probe.py"
        original = b"import os\ndef entry(fd):\n os.write(fd, b'ORIGINAL')\n return 0\n"
        source_path.write_bytes(original)
        source_fd = os.open(source_path, os.O_RDONLY)
        source_stat = os.fstat(source_fd)
        code = compile(original.decode("utf-8"), str(source_path), "exec")
        os.rename(source_path, source_path.with_suffix(".honest"))
        source_path.write_text(
            "import os\ndef entry(fd):\n os.write(fd, b'MALICIOUS')\n return 0\n"
        )
        require(inode_identity(os.stat(source_path, follow_symlinks=False))
                != inode_identity(source_stat),
                "Disposable source substitution did not change inode")
        read_fd, write_fd = os.pipe()
        interpreter, interpreter_sha = current_interpreter_binding()
        process = _fork_loaded_entry(
            synthetic_loaded_code_entry, (code, write_fd), (write_fd,),
            {"schema": "synthetic-v10-loaded-code-race",
             "interpreter_binding_sha256": interpreter_sha},
        )
        os.close(write_fd)
        observation = bounded_process_wait(
            process, time_limit=5.0,
            expected_process_uuid=interpreter["process_uuid"],
        )
        executed = os.read(read_fd, 64)
        os.close(read_fd)
        os.close(source_fd)
        require(observation["returncode"] == 0 and executed == b"ORIGINAL"
                and observation["process_uuid"] == interpreter["process_uuid"],
                "Loaded-code fork executed pathname replacement or another image")
    checks["postcheck_worker_path_swap_cannot_change_executed_bytes"] = "PASS_ORIGINAL"
    checks["forked_worker_process_uuid_matches_running_interpreter"] = "PASS"

    secret = secrets.token_bytes(32)
    # Rebuild once with the same key used by both fixture documents.
    fixture = complete_synthetic_worker_fixture(worker, secret)
    validate_complete_worker_artifacts(
        worker, fixture["report"], fixture["receipt"],
        fixture["report_body"], fixture["receipt_body"], secret,
        fixture["args"], fixture["preflight"], fixture["worker_pid"],
        fixture["report_prebound"], fixture["receipt_prebound"],
        fixture["interpreter_binding_sha256"],
    )
    for key in sorted(REPORT_KEYS):
        changed = json.loads(json.dumps(fixture["report"]))
        del changed[key]
        try:
            validate_complete_worker_artifacts(
                worker, changed, fixture["receipt"], encoded_json(changed),
                fixture["receipt_body"], secret, fixture["args"],
                fixture["preflight"], fixture["worker_pid"],
                fixture["report_prebound"], fixture["receipt_prebound"],
                fixture["interpreter_binding_sha256"],
            )
        except ValueError:
            pass
        else:
            raise AssertionError("Missing report field was accepted: " + key)
    for key in sorted(WORKER_RECEIPT_KEYS):
        changed = json.loads(json.dumps(fixture["receipt"]))
        del changed[key]
        try:
            validate_complete_worker_artifacts(
                worker, fixture["report"], changed, fixture["report_body"],
                encoded_json(changed), secret, fixture["args"],
                fixture["preflight"], fixture["worker_pid"],
                fixture["report_prebound"], fixture["receipt_prebound"],
                fixture["interpreter_binding_sha256"],
            )
        except ValueError:
            pass
        else:
            raise AssertionError("Missing worker-receipt field was accepted: " + key)
    for label, mutate in (
        ("planned_sequence_nested_field", lambda value:
            value["planned_sequence"][4].pop("yaw_degrees")),
        ("camera_tensor_identity_nested_field", lambda value:
            next(iter(value["camera_tensor_identities"].values())).pop("shape")),
        ("not_evaluated_sentinel", lambda value:
            value.__setitem__("novelty", "PASS")),
    ):
        changed = json.loads(json.dumps(fixture["report"]))
        changed.pop("artifact_authentication_hmac_sha256")
        mutate(changed)
        changed, changed_body = signed_fixture(secret, REPORT_NAME, changed)
        try:
            validate_complete_worker_artifacts(
                worker, changed, fixture["receipt"], changed_body,
                fixture["receipt_body"], secret, fixture["args"],
                fixture["preflight"], fixture["worker_pid"],
                fixture["report_prebound"], fixture["receipt_prebound"],
                fixture["interpreter_binding_sha256"],
            )
        except ValueError:
            checks["complete_schema_rejects_" + label] = "PASS_REJECTED"
        else:
            raise AssertionError("Nested complete-schema deletion was accepted: " + label)
    checks["complete_report_top_level_deletion_matrix"] = len(REPORT_KEYS)
    checks["complete_worker_receipt_top_level_deletion_matrix"] = len(WORKER_RECEIPT_KEYS)

    with tempfile.TemporaryDirectory(prefix="s45b_supervised_nominal_") as raw:
        state = synthetic_setup(worker, Path(raw).resolve())
        try:
            observation = synthetic_publish(worker, state)
            require(
                observation["status"]
                == "HELD_CANDIDATE_READY_FOR_EXTERNAL_EXIT_GATED_SEAL"
                and observation["passed"] is False
                and observation["terminal_authority"] is False
                and canonical_seal_matches_held_observation(
                    state["output_fd"], observation,
                )
                and not canonical_seal_matches_held_observation(state["output_fd"], None),
                "Nominal held-FD candidate observation is malformed",
            )
            nominal_fd = os.open(
                TERMINAL_SEAL_NAME, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0),
                dir_fd=state["output_fd"],
            )
            try:
                body = os.pread(nominal_fd, observation["candidate_bytes"], 0)
            finally:
                os.close(nominal_fd)
            os.rename(
                TERMINAL_SEAL_NAME, ".post-return-original",
                src_dir_fd=state["output_fd"], dst_dir_fd=state["output_fd"],
            )
            replacement_fd = os.open(
                TERMINAL_SEAL_NAME,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0),
                0o600, dir_fd=state["output_fd"],
            )
            try:
                offset = 0
                while offset < len(body):
                    offset += os.write(replacement_fd, body[offset:])
                os.fsync(replacement_fd)
            finally:
                os.close(replacement_fd)
            require(
                not canonical_seal_matches_held_observation(
                    state["output_fd"], observation,
                ),
                "Identical-byte post-return inode replacement matched the held observation",
            )
            checks["nominal_held_fd_terminal_consumption"] = "PASS"
            checks["canonical_path_alone_has_no_authority"] = "PASS"
            checks["post_return_identical_byte_inode_swap"] = "PASS_REJECTED"
        finally:
            synthetic_close(state)

    with tempfile.TemporaryDirectory(prefix="s45b_supervised_failure_marker_") as raw:
        state = synthetic_setup(worker, Path(raw).resolve())
        try:
            observation = synthetic_publish(worker, state)
            worker.write_new_at(
                state["output_fd"], TERMINAL_FAILURE_NAME,
                {"schema": "synthetic-late-failure", "passed": False},
            )
            require(not canonical_seal_matches_held_observation(
                        state["output_fd"], observation),
                    "Terminal failure marker did not invalidate a seal")
            checks["terminal_failure_marker_invalidates_pass"] = "PASS_REJECTED"
        finally:
            synthetic_close(state)

    for fault in (
        "STAGE_CLOSE_BEFORE_PUBLISH",
        "DIR_FSYNC_BEFORE_COMMIT",
        "FINAL_DIR_FSYNC_BEFORE_COMMIT",
        "REQUIRED_FD_CLOSE_AFTER_HELD_CONSUMPTION",
        "FINAL_SEAL_CLOSE_ERROR",
    ):
        with tempfile.TemporaryDirectory(prefix="s45b_supervised_fault_") as raw:
            state = synthetic_setup(worker, Path(raw).resolve())
            try:
                try:
                    synthetic_publish(worker, state, fault=fault)
                except (InjectedSyntheticFailure, OSError):
                    pass
                else:
                    raise AssertionError("Synthetic fault did not interrupt: " + fault)
                require(not canonical_seal_matches_held_observation(state["output_fd"], None),
                        "Path-only state created authority after fault: " + fault)
                assert_no_true_pass_paths(state["output_fd"])
                checks[fault.lower()] = "PASS_FAIL_CLOSED"
            finally:
                synthetic_close(state)

    with tempfile.TemporaryDirectory(prefix="s45b_supervised_control_close_") as raw:
        state = synthetic_setup(worker, Path(raw).resolve())
        try:
            observation = synthetic_publish(worker, state)
            require(canonical_seal_matches_held_observation(
                        state["output_fd"], observation),
                    "Candidate changed before terminal control-FD close")
            close_terminal_control_fds(
                state["output_fd"], state["lock_fd"], state["parent_fd"],
            )
            state["output_fd"] = state["lock_fd"] = state["parent_fd"] = -1
            checks["all_terminal_control_fds_close"] = "PASS_BEFORE_PASS_CONSTRUCTION"
        finally:
            synthetic_close(state)

    for fault in (
        "FINAL_OUTPUT_FD_CLOSE_ERROR",
        "FINAL_LOCK_FD_CLOSE_ERROR",
        "FINAL_PARENT_FD_CLOSE_ERROR",
    ):
        with tempfile.TemporaryDirectory(prefix="s45b_supervised_control_close_") as raw:
            root = Path(raw).resolve()
            state = synthetic_setup(worker, root)
            try:
                synthetic_publish(worker, state)
                try:
                    close_terminal_control_fds(
                        state["output_fd"], state["lock_fd"], state["parent_fd"],
                        fault=fault,
                    )
                except OSError:
                    pass
                else:
                    raise AssertionError("Control-FD close fault did not interrupt: " + fault)
                check_fd = os.open(
                    root / "execution",
                    os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
                    | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
                )
                try:
                    assert_no_true_pass_paths(check_fd)
                finally:
                    os.close(check_fd)
                checks[fault.lower()] = "PASS_NO_TRUTHY_PATH_OR_STDOUT_SEAL"
            finally:
                synthetic_close(state)

    for fault, expected_returncode in (
        ("SIGKILL_AFTER_LINK", -signal.SIGKILL),
        ("SIGTERM_AFTER_LINK", -signal.SIGTERM),
        ("SIGKILL_AFTER_UNLINK", -signal.SIGKILL),
        ("SIGTERM_AFTER_UNLINK", -signal.SIGTERM),
    ):
        raw = tempfile.mkdtemp(prefix="s45b_supervised_fault_")
        root = Path(raw).resolve()
        try:
            returncode, stdout, stderr = isolated_fault_process(root, fault)
            require(returncode == expected_returncode and stdout == b"" and stderr == b"",
                    "Signal fault child did not terminate at the requested boundary")
            output_fd = os.open(
                root / "execution",
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
            )
            try:
                require(not canonical_seal_matches_held_observation(output_fd, None),
                        "Signal interruption created path-only authority")
                assert_no_true_pass_paths(output_fd)
                final_stat = os.stat(TERMINAL_SEAL_NAME, dir_fd=output_fd, follow_symlinks=False)
                if fault.endswith("AFTER_LINK"):
                    require(final_stat.st_nlink == 2
                            and not worker.entry_absent(output_fd, TERMINAL_SEAL_STAGING_NAME),
                            "Pre-unlink signal does not retain the invalid two-link state")
                else:
                    require(final_stat.st_nlink == 1
                            and worker.entry_absent(output_fd, TERMINAL_SEAL_STAGING_NAME),
                            "Post-unlink signal state differs from the expected one-link path")
            finally:
                os.close(output_fd)
            checks[fault.lower()] = "PASS_NO_HELD_FD_OBSERVATION_RETURNED"
        finally:
            import shutil
            shutil.rmtree(root)

    for attack in (
        "RENAME_RECREATE_FINAL_AFTER_UNLINK",
        "UNLINK_RECREATE_FINAL_AFTER_UNLINK",
    ):
        with tempfile.TemporaryDirectory(prefix="s45b_supervised_commit_attack_") as raw:
            state = synthetic_setup(worker, Path(raw).resolve())
            try:
                try:
                    synthetic_publish(worker, state, fault=attack)
                except (ValueError, OSError):
                    pass
                else:
                    raise AssertionError("Final seal replacement returned an observation")
                require(not canonical_seal_matches_held_observation(state["output_fd"], None),
                        "Replacement canonical path became authoritative")
                assert_no_true_pass_paths(state["output_fd"])
                checks[attack.lower()] = "PASS_REJECTED_BEFORE_AUTHORITY_RETURN"
            finally:
                synthetic_close(state)

    for attack in ("rename_recreate", "symlink_replace"):
        with tempfile.TemporaryDirectory(prefix="s45b_supervised_output_attack_") as raw:
            root = Path(raw).resolve()
            state = synthetic_setup(worker, root)
            try:
                os.rename(
                    "execution", "execution.old",
                    src_dir_fd=state["parent_fd"], dst_dir_fd=state["parent_fd"],
                )
                if attack == "rename_recreate":
                    os.mkdir("execution", 0o700, dir_fd=state["parent_fd"])
                else:
                    os.symlink("execution.old", "execution", dir_fd=state["parent_fd"])
                try:
                    collect_evidence_bundle(
                        worker, state["parent_fd"], state["root"], state["parent_identity"],
                        state["lock_fd"], "attempt.lock", state["lock_identity"],
                        state["lock_sha"], state["lock_bytes"],
                        state["output_fd"], "execution", state["output_identity"],
                        state["leases"], sorted(state["leases"]),
                    )
                except (ValueError, OSError):
                    checks["execution_directory_" + attack] = "PASS_REJECTED"
                else:
                    raise AssertionError("Canonical execution-directory attack was accepted")
            finally:
                synthetic_close(state)

    with tempfile.TemporaryDirectory(prefix="s45b_supervised_output_hardlink_") as raw:
        state = synthetic_setup(worker, Path(raw).resolve())
        try:
            try:
                os.link(
                    "execution", "execution.alias",
                    src_dir_fd=state["parent_fd"], dst_dir_fd=state["parent_fd"],
                )
            except OSError:
                checks["execution_directory_hardlink"] = "PASS_KERNEL_REJECTED"
            else:
                raise AssertionError("Kernel admitted a directory hard link")
        finally:
            synthetic_close(state)

    for artifact_name in (
        REPORT_NAME, WORKER_RECEIPT_NAME, SUPERVISOR_RECEIPT_NAME, BARRIER_NAME,
    ):
        for attack in ("hardlink", "symlink", "rename_recreate", "unlink_recreate"):
            with tempfile.TemporaryDirectory(prefix="s45b_supervised_artifact_") as raw:
                root = Path(raw).resolve()
                state = synthetic_setup(worker, root)
                try:
                    lease = state["leases"][artifact_name]
                    body = lease["body"]
                    if attack == "hardlink":
                        os.link(
                            artifact_name, artifact_name + ".alias",
                            src_dir_fd=state["output_fd"], dst_dir_fd=state["output_fd"],
                        )
                    elif attack == "symlink":
                        os.rename(
                            artifact_name, artifact_name + ".original",
                            src_dir_fd=state["output_fd"], dst_dir_fd=state["output_fd"],
                        )
                        os.symlink(
                            WORKER_RECEIPT_NAME if artifact_name != WORKER_RECEIPT_NAME else REPORT_NAME,
                            artifact_name, dir_fd=state["output_fd"],
                        )
                    elif attack == "rename_recreate":
                        os.rename(
                            artifact_name, artifact_name + ".original",
                            src_dir_fd=state["output_fd"], dst_dir_fd=state["output_fd"],
                        )
                        write_raw_new_at(state["output_fd"], artifact_name, body)
                    else:
                        os.unlink(artifact_name, dir_fd=state["output_fd"])
                        write_raw_new_at(state["output_fd"], artifact_name, body)
                    try:
                        verify_regular_lease(
                            state["output_fd"], root / "execution", lease,
                        )
                    except (ValueError, OSError):
                        checks[artifact_name + "_" + attack] = "PASS_REJECTED"
                    else:
                        raise AssertionError(
                            artifact_name + " " + attack + " attack was accepted"
                        )
                finally:
                    synthetic_close(state)

    for attack in ("hardlink", "symlink", "rename_recreate", "unlink_recreate"):
        with tempfile.TemporaryDirectory(prefix="s45b_supervised_lock_attack_") as raw:
            state = synthetic_setup(worker, Path(raw).resolve())
            try:
                if attack == "hardlink":
                    os.link(
                        "attempt.lock", "attempt.lock.alias",
                        src_dir_fd=state["parent_fd"], dst_dir_fd=state["parent_fd"],
                    )
                elif attack == "symlink":
                    os.rename(
                        "attempt.lock", "attempt.lock.original",
                        src_dir_fd=state["parent_fd"], dst_dir_fd=state["parent_fd"],
                    )
                    os.symlink(
                        "attempt.lock.original", "attempt.lock", dir_fd=state["parent_fd"],
                    )
                elif attack == "rename_recreate":
                    os.rename(
                        "attempt.lock", "attempt.lock.original",
                        src_dir_fd=state["parent_fd"], dst_dir_fd=state["parent_fd"],
                    )
                    body = os.pread(state["lock_fd"], state["lock_bytes"], 0)
                    write_raw_new_at(state["parent_fd"], "attempt.lock", body)
                else:
                    body = os.pread(state["lock_fd"], state["lock_bytes"], 0)
                    os.unlink("attempt.lock", dir_fd=state["parent_fd"])
                    write_raw_new_at(state["parent_fd"], "attempt.lock", body)
                try:
                    worker.verify_lock_lease(
                        state["parent_fd"], state["root"], state["parent_identity"],
                        state["lock_fd"], "attempt.lock", state["lock_identity"],
                        state["lock_sha"], state["lock_bytes"],
                    )
                except (ValueError, OSError):
                    checks["permanent_lock_" + attack] = "PASS_REJECTED"
                else:
                    raise AssertionError("Permanent-lock attack was accepted")
            finally:
                synthetic_close(state)

    for mode, stream_name in (("STDOUT_OVERFLOW", "stdout"),
                              ("STDERR_OVERFLOW", "stderr")):
        observed = isolated_resource_process(mode)
        require(observed["output_limit_exceeded"] and not observed["timed_out"]
                and observed["returncode"] != 0,
                "Output overflow was not terminated fail-closed")
        require(len(observed["stdout"]) <= MAX_STDOUT_BYTES + 1
                and len(observed["stderr"]) <= MAX_STDERR_BYTES + 1,
                "Output overflow capture exceeded the hard observation bound")
        checks[stream_name + "_overflow"] = "PASS_TERMINATED_FAIL_CLOSED"

    observed = isolated_resource_process("SLEEP_TIMEOUT", time_limit=0.1)
    require(observed["timed_out"] and not observed["output_limit_exceeded"]
            and observed["returncode"] != 0
            and observed["stdout"] == b"" and observed["stderr"] == b"",
            "Wall-time timeout was not terminated fail-closed")
    checks["wall_time_timeout"] = "PASS_TERMINATED_FAIL_CLOSED"

    process = spawn_contained(
        [str(PYTHON_EXECUTABLE), "-I", "-B", "-S", str(SELF),
         "--synthetic-resource-child", "SLEEP_TIMEOUT"],
    )
    observed = bounded_process_wait(process, time_limit=5.0, memory_limit=1)
    require(observed["memory_limit_exceeded"] and observed["returncode"] != 0,
            "Exact-PID memory high-water gate did not fail closed")
    checks["darwin_exact_pid_memory_high_water_gate"] = "PASS_TERMINATED_FAIL_CLOSED"

    close_loaded_worker_lease(worker)
    return {
        "schema": "s45b-c1-numeric-camera-guard-supervisor-synthetic-selftest-v3",
        "status": "PASS_SUPERVISOR_SYNTHETIC_AND_FAULT_INJECTION_ONLY",
        "worker_source": worker_record,
        "runtime_capability_preflight": runtime,
        "checks": checks,
        "formal_runner_calls": 0,
        "real_c1_manifest_receipt_event_tensor_or_image_files_opened": 0,
        "c1_tensor_bodies_read": 0,
        "real_scientific_arrays_mapped": 0,
        "pixels_decoded": 0,
        "images_viewed": 0,
        "model_renderer_generation_calls": 0,
        "formal_paths_created": 0,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic-self-test", action="store_true")
    parser.add_argument("--synthetic-capability-child", action="store_true")
    parser.add_argument("--synthetic-fault-child", choices=(
        "SIGKILL_AFTER_LINK", "SIGTERM_AFTER_LINK",
        "SIGKILL_AFTER_UNLINK", "SIGTERM_AFTER_UNLINK",
    ))
    parser.add_argument("--synthetic-resource-child", choices=(
        "STDOUT_OVERFLOW", "STDERR_OVERFLOW", "SLEEP_TIMEOUT",
    ))
    parser.add_argument("--synthetic-root")
    parser.add_argument("--self-sha256")
    parser.add_argument("--worker-sha256")
    parser.add_argument("--primary-source-review-sha256")
    parser.add_argument("--adversarial-source-review-sha256")
    parser.add_argument("--binding-sha256")
    parser.add_argument("--binding-review-sha256")
    parser.add_argument("--governance-attestation-sha256")
    parser.add_argument("--out")
    args = parser.parse_args()
    formal_names = (
        "self_sha256", "worker_sha256", "primary_source_review_sha256",
        "adversarial_source_review_sha256", "binding_sha256",
        "binding_review_sha256", "governance_attestation_sha256", "out",
    )
    if args.synthetic_self_test:
        require(not args.synthetic_capability_child
                and args.synthetic_fault_child is None and args.synthetic_resource_child is None
                and args.synthetic_root is None
                and all(getattr(args, name) is None for name in formal_names),
                "Synthetic self-test accepts no formal or child arguments")
        print(json.dumps(synthetic_selftest(), sort_keys=True, allow_nan=False))
        return 0
    if args.synthetic_fault_child is not None:
        require(not args.synthetic_capability_child
                and args.synthetic_resource_child is None and args.synthetic_root is not None
                and all(getattr(args, name) is None for name in formal_names),
                "Synthetic fault child accepts only its isolated root and fault")
        return synthetic_fault_child(args.synthetic_root, args.synthetic_fault_child)
    if args.synthetic_resource_child is not None:
        require(not args.synthetic_capability_child
                and args.synthetic_fault_child is None and args.synthetic_root is None
                and all(getattr(args, name) is None for name in formal_names),
                "Synthetic resource child accepts no formal or filesystem arguments")
        return synthetic_resource_child(args.synthetic_resource_child)
    if args.synthetic_capability_child:
        require(args.synthetic_fault_child is None and args.synthetic_resource_child is None
                and args.synthetic_root is None
                and all(getattr(args, name) is None for name in formal_names),
                "Synthetic capability child accepts no formal or filesystem arguments")
        return synthetic_capability_child()
    require(args.synthetic_root is None and all(getattr(args, name) is not None for name in formal_names),
            "Formal supervisor requires every exact identity and the canonical output")
    require(all(valid_sha(getattr(args, name)) for name in formal_names if name != "out"),
            "Formal supervisor received a malformed SHA-256")
    return formal_supervision(args)


if __name__ == "__main__":
    raise SystemExit(main())
