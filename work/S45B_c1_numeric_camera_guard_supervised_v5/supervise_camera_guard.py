#!/usr/bin/env python3
"""External supervisor and atomic terminal sealer for the S45B C1 camera guard.

The worker can write only pending evidence.  This supervisor owns the one-use
attempt, observes worker termination and resource boundaries, revalidates every
canonical evidence inode, and is the sole source of an authoritative PASS seal.
Synthetic modes operate only inside isolated temporary directories.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
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
FORMAL_OUT = HERE / "execution_01"
LOCK = HERE / ".c1_numeric_camera_guard.lock"
LOCK_STAGING = HERE / ".c1_numeric_camera_guard.lock.staging"
BINDING = HERE / "C1_CAMERA_GUARD_BINDING_V5.json"
BINDING_REVIEW = HERE / "BINDING_REVIEW_V5.json"
PRIMARY_REVIEW = HERE / "SOURCE_REVIEW_PRIMARY_V5.json"
ADVERSARIAL_REVIEW = HERE / "SOURCE_REVIEW_ADVERSARIAL_V5.json"

REPORT_NAME = "report.json"
WORKER_RECEIPT_NAME = "worker_receipt.json"
WORKER_FAILURE_NAME = "worker_postwrite_failure.json"
SUPERVISOR_RECEIPT_NAME = "supervisor_receipt.json"
BARRIER_NAME = "terminalization_barrier.json"
TERMINAL_SEAL_NAME = "terminal_pass_seal.json"
TERMINAL_SEAL_STAGING_NAME = ".terminal_pass_seal.staging"
TERMINAL_FAILURE_NAME = "terminal_seal_failure.json"

TIME_LIMIT_SECONDS = 300.0
CPU_LIMIT_SECONDS = 120
MAX_WORKER_RSS_BYTES = 2 * 1024 * 1024 * 1024
MAX_STDOUT_BYTES = 65536
MAX_STDERR_BYTES = 65536
MAX_ARTIFACT_BYTES = 64 * 1024 * 1024
HEX_LENGTH = 64


class SupervisorTermination(RuntimeError):
    pass


class InjectedSyntheticFailure(RuntimeError):
    pass


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
    finally:
        os.close(fd)
    module = types.ModuleType("_s45b_c1_camera_worker_exact")
    module.__file__ = str(WORKER)
    code = compile(source.decode("utf-8"), str(WORKER), "exec")
    exec(code, module.__dict__)
    return module, {
        "path": str(WORKER),
        "sha256": digest,
        "bytes": len(source),
        "lstat": stat_record(before),
    }


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
    if name == "SIGKILL_AFTER_LINK":
        os.kill(os.getpid(), signal.SIGKILL)
    if name == "SIGTERM_AFTER_LINK":
        os.kill(os.getpid(), signal.SIGTERM)
    raise InjectedSyntheticFailure(name)


def publish_terminal_seal(
    worker, parent_fd, parent_path, parent_identity,
    lock_fd, lock_name, lock_identity, lock_sha256, lock_bytes,
    output_fd, output_name, output_identity, leases, seal,
    fault=None,
):
    """Publish PASS only at the last single-link commit after all close/fsync checks."""
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
        "atomic_commit": "unlink_staging_only_after_post_link_revalidation_and_all_artifact_fd_closes",
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
    try:
        require(
            stage["record"]["lstat"] == final["record"]["lstat"]
            and stage["body"] == final["body"] == body,
            "Terminal seal hard-link publication changed identity/content",
        )
    finally:
        close_leases({"stage": stage, "final": final})

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
    close_leases(leases)
    fault_point("ARTIFACT_CLOSE_BEFORE_COMMIT", fault)
    os.fsync(output_fd)
    fault_point("FINAL_DIR_FSYNC_BEFORE_COMMIT", fault)

    # This unlink is the sole authority commit.  Before it the PASS inode has
    # two names and is explicitly invalid; after it every scientific artifact
    # has already been revalidated, fsynced, and successfully closed.
    os.unlink(TERMINAL_SEAL_STAGING_NAME, dir_fd=output_fd)
    return sha256_bytes(body)


def terminal_seal_authoritative(output_fd):
    for forbidden in (TERMINAL_FAILURE_NAME, WORKER_FAILURE_NAME):
        if not _entry_absent(output_fd, forbidden):
            return False
    try:
        os.stat(TERMINAL_SEAL_STAGING_NAME, dir_fd=output_fd, follow_symlinks=False)
    except FileNotFoundError:
        pass
    else:
        return False
    try:
        seal = open_regular_lease(
            output_fd, Path("/synthetic-or-reviewed-output"),
            TERMINAL_SEAL_NAME, nlink=1,
        )
    except (FileNotFoundError, ValueError, OSError, json.JSONDecodeError):
        return False
    try:
        try:
            doc = json.loads(seal["body"].decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return False
        return (
            doc.get("schema") == "s45b-c1-numeric-camera-guard-terminal-pass-seal-v1"
            and doc.get("status") == "PASS_C1_REQUESTED_CAMERA_INPUT_CONDITION_GUARD_ONLY"
            and doc.get("passed") is True
            and doc.get("terminal_authority") is True
        )
    finally:
        close_leases({"seal": seal})


def process_group_empty(pgid):
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return True
    except PermissionError:
        return False
    return False


def _entry_absent(directory_fd, name):
    try:
        os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        return True
    return False


def terminate_group(pgid):
    try:
        os.killpg(pgid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def worker_resource_limit():
    resource.setrlimit(resource.RLIMIT_CPU, (CPU_LIMIT_SECONDS, CPU_LIMIT_SECONDS))
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_ARTIFACT_BYTES, MAX_ARTIFACT_BYTES))
    if hasattr(resource, "RLIMIT_AS"):
        resource.setrlimit(resource.RLIMIT_AS, (MAX_WORKER_RSS_BYTES, MAX_WORKER_RSS_BYTES))


def bounded_process_wait(
    process, time_limit=TIME_LIMIT_SECONDS,
    stdout_limit=MAX_STDOUT_BYTES, stderr_limit=MAX_STDERR_BYTES,
):
    """Drain child pipes with hard byte/time bounds and return terminal evidence."""
    require(time_limit > 0 and stdout_limit >= 0 and stderr_limit >= 0,
            "Process observation limits are malformed")
    deadline = time.monotonic() + time_limit
    streams = {process.stdout: ("stdout", stdout_limit),
               process.stderr: ("stderr", stderr_limit)}
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    selector = selectors.DefaultSelector()
    timed_out = False
    output_limit_exceeded = False
    try:
        for stream in streams:
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ)
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                timed_out = True
                terminate_group(process.pid)
                break
            events = selector.select(min(remaining, 0.25))
            if not events and process.poll() is not None:
                # A surviving descendant may still hold a pipe; keep draining
                # until EOF or the same fixed deadline.
                continue
            for key, _ in events:
                stream = key.fileobj
                label, limit = streams[stream]
                try:
                    chunk = os.read(stream.fileno(), min(65536, limit - len(buffers[label]) + 1))
                except BlockingIOError:
                    continue
                if not chunk:
                    selector.unregister(stream)
                    continue
                buffers[label].extend(chunk)
                if len(buffers[label]) > limit:
                    output_limit_exceeded = True
                    terminate_group(process.pid)
                    break
            if output_limit_exceeded:
                break
        if timed_out or output_limit_exceeded:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                terminate_group(process.pid)
                process.wait(timeout=5)
        else:
            remaining = max(0.0, deadline - time.monotonic())
            try:
                process.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                timed_out = True
                terminate_group(process.pid)
                process.wait(timeout=5)
    finally:
        selector.close()
        for stream in streams:
            try:
                stream.close()
            except OSError:
                pass
    return bytes(buffers["stdout"]), bytes(buffers["stderr"]), timed_out, output_limit_exceeded


def maxrss_bytes(value):
    return int(value) if platform.system() == "Darwin" else int(value) * 1024


def worker_namespace(args):
    return argparse.Namespace(
        self_sha256=args.worker_sha256,
        supervisor_sha256=args.self_sha256,
        primary_source_review_sha256=args.primary_source_review_sha256,
        adversarial_source_review_sha256=args.adversarial_source_review_sha256,
        binding_sha256=args.binding_sha256,
        binding_review_sha256=args.binding_review_sha256,
        out=args.out,
    )


def worker_command(args, capability_fd, capability_sha256,
                   parent_fd, parent_identity, lock_fd, lock_identity,
                   lock_sha256, lock_bytes, output_fd, output_identity):
    values = {
        "--self-sha256": args.worker_sha256,
        "--supervisor-sha256": args.self_sha256,
        "--primary-source-review-sha256": args.primary_source_review_sha256,
        "--adversarial-source-review-sha256": args.adversarial_source_review_sha256,
        "--binding-sha256": args.binding_sha256,
        "--binding-review-sha256": args.binding_review_sha256,
        "--out": args.out,
        "--parent-fd": parent_fd,
        "--lock-fd": lock_fd,
        "--output-fd": output_fd,
        "--capability-fd": capability_fd,
        "--capability-sha256": capability_sha256,
        "--supervisor-pid": os.getpid(),
        "--parent-dev": parent_identity[0],
        "--parent-ino": parent_identity[1],
        "--parent-mode": parent_identity[2],
        "--lock-dev": lock_identity[0],
        "--lock-ino": lock_identity[1],
        "--lock-mode": lock_identity[2],
        "--lock-sha256": lock_sha256,
        "--lock-bytes": lock_bytes,
        "--output-dev": output_identity[0],
        "--output-ino": output_identity[1],
        "--output-mode": output_identity[2],
    }
    command = [sys.executable, "-I", "-B", "-S", str(WORKER), "--formal-worker"]
    for name, value in values.items():
        command.extend((name, str(value)))
    return command


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
        phase = "ATOMIC_ATTEMPT_COMMIT"
        lease_record = {
            "schema": "s45b-c1-numeric-camera-guard-attempt-lease-v2",
            "status": "FAIL_CLOSED_ATTEMPT_COMMITTED_NO_VALID_TERMINAL_SEAL",
            "passed": False,
            "terminal_authority": False,
            "row": "C1",
            "attempt": 1,
            "attempt_consumed": True,
            "automatic_retries": 0,
            "lease_committed_after_complete_preflight": True,
            "preflight_started_utc": preflight["started_utc"].isoformat(),
            "lease_prepared_utc": utc(),
            "formal_output_path": str(FORMAL_OUT),
            "terminal_seal_path": str(FORMAL_OUT / TERMINAL_SEAL_NAME),
            "terminal_authority_rule": (
                "Only a single-link terminal_pass_seal.json with absent staging/failure, exact "
                "bound evidence, and independent result review can supersede this default failure"
            ),
            "supplied_identities": {
                "camera_guard.py": args.worker_sha256,
                "supervise_camera_guard.py": args.self_sha256,
                "primary_source_review": args.primary_source_review_sha256,
                "adversarial_source_review": args.adversarial_source_review_sha256,
                "C1_CAMERA_GUARD_BINDING_V5.json": args.binding_sha256,
                "BINDING_REVIEW_V5.json": args.binding_review_sha256,
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

        phase = "WORKER_PROCESS_SPAWN_AND_WAIT"
        capability_read, capability_write = os.pipe()
        capability = secrets.token_bytes(32)
        capability_sha256 = sha256_bytes(capability)
        os.write(capability_write, capability)
        os.close(capability_write)
        capability_write = None
        command = worker_command(
            args, capability_read, capability_sha256,
            parent_fd, parent_identity, lock_fd, lock_identity,
            lock_sha256, lock_bytes, output_fd, output_identity,
        )
        started_monotonic = time.monotonic()
        before_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            pass_fds=(parent_fd, lock_fd, output_fd, capability_read),
            close_fds=True,
            start_new_session=True,
            preexec_fn=worker_resource_limit,
        )
        os.close(capability_read)
        capability_read = None
        stdout, stderr, timed_out, output_limit_exceeded = bounded_process_wait(process)
        elapsed = time.monotonic() - started_monotonic
        after_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
        usage = {
            "elapsed_seconds": elapsed,
            "user_cpu_seconds": after_usage.ru_utime - before_usage.ru_utime,
            "system_cpu_seconds": after_usage.ru_stime - before_usage.ru_stime,
            "peak_rss_bytes": maxrss_bytes(after_usage.ru_maxrss),
            "peak_rss_platform_unit": "bytes_on_Darwin_kibibytes_converted_elsewhere",
            "stdout_bytes": len(stdout),
            "stdout_sha256": sha256_bytes(stdout),
            "stderr_bytes": len(stderr),
            "stderr_sha256": sha256_bytes(stderr),
            "time_limit_seconds": TIME_LIMIT_SECONDS,
            "cpu_limit_seconds": CPU_LIMIT_SECONDS,
            "rss_limit_bytes": MAX_WORKER_RSS_BYTES,
            "stdout_limit_bytes": MAX_STDOUT_BYTES,
            "stderr_limit_bytes": MAX_STDERR_BYTES,
        }
        descendants_empty = process_group_empty(process.pid)
        if not descendants_empty:
            terminate_group(process.pid)
        details.update(
            worker_pid=process.pid,
            worker_returncode=process.returncode,
            timed_out=timed_out,
            output_limit_exceeded=output_limit_exceeded,
            process_group_empty_after_wait=descendants_empty,
            resource_usage=usage,
        )
        require(
            not timed_out and not output_limit_exceeded
            and process.returncode == 0 and descendants_empty
            and len(stdout) == 0 and len(stderr) == 0
            and elapsed <= TIME_LIMIT_SECONDS
            and usage["user_cpu_seconds"] + usage["system_cpu_seconds"] <= CPU_LIMIT_SECONDS + 1
            and usage["peak_rss_bytes"] <= MAX_WORKER_RSS_BYTES,
            "Worker exit, descendants, stdio, time, CPU, or RSS boundary failed",
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
        report_lease = open_regular_lease(output_fd, FORMAL_OUT, REPORT_NAME)
        leases[REPORT_NAME] = report_lease
        worker_lease = open_regular_lease(output_fd, FORMAL_OUT, WORKER_RECEIPT_NAME)
        leases[WORKER_RECEIPT_NAME] = worker_lease
        report = json.loads(report_lease["body"].decode("utf-8"))
        worker_receipt = json.loads(worker_lease["body"].decode("utf-8"))
        require(
            report.get("schema") == "s45b-c1-numeric-camera-guard-worker-report-v2"
            and report.get("status") == "C1_REQUESTED_CAMERA_INPUT_CONDITION_RESULT_PENDING_EXTERNAL_SUPERVISOR_SEAL"
            and report.get("passed") is False
            and report.get("terminal_authority") is False
            and report.get("row") == "C1"
            and report.get("numeric_worker_verdict")
            == "PASS_C1_REQUESTED_CAMERA_INPUT_CONDITION_GUARD_ONLY"
            and report.get("worker_sha256") == args.worker_sha256
            and report.get("supervisor_sha256") == args.self_sha256
            and report.get("primary_source_review_sha256") == args.primary_source_review_sha256
            and report.get("adversarial_source_review_sha256") == args.adversarial_source_review_sha256
            and report.get("binding_sha256") == args.binding_sha256
            and report.get("binding_review_sha256") == args.binding_review_sha256
            and worker_receipt.get("schema") == "s45b-c1-numeric-camera-guard-worker-receipt-v2"
            and worker_receipt.get("status") == "C1_NUMERIC_CAMERA_WORKER_EVIDENCE_WRITTEN_PENDING_PROCESS_EXIT_AND_SUPERVISOR_SEAL"
            and worker_receipt.get("passed") is False
            and worker_receipt.get("terminal_authority") is False
            and worker_receipt.get("row") == "C1"
            and worker_receipt.get("numeric_worker_verdict") == report.get("numeric_worker_verdict")
            and worker_receipt.get("worker_sha256") == args.worker_sha256
            and worker_receipt.get("supervisor_sha256") == args.self_sha256
            and worker_receipt.get("primary_source_review_sha256") == args.primary_source_review_sha256
            and worker_receipt.get("adversarial_source_review_sha256") == args.adversarial_source_review_sha256
            and worker_receipt.get("binding_sha256") == args.binding_sha256
            and worker_receipt.get("binding_review_sha256") == args.binding_review_sha256
            and worker_receipt.get("report_sha256") == report_lease["record"]["sha256"],
            "Worker artifacts are not the exact pending-only evidence pair",
        )
        initial_bundle = collect_evidence_bundle(
            worker, parent_fd, HERE, parent_identity,
            lock_fd, LOCK.name, lock_identity, lock_sha256, lock_bytes,
            output_fd, FORMAL_OUT.name, output_identity,
            leases, sorted(leases),
        )

        phase = "SUPERVISOR_PENDING_RECEIPT_WRITE"
        supervisor_receipt = {
            "schema": "s45b-c1-numeric-camera-guard-supervisor-receipt-v1",
            "status": "WORKER_EXIT_ZERO_AND_EVIDENCE_OBSERVED_PENDING_TERMINAL_SEAL",
            "passed": False,
            "terminal_authority": False,
            "row": "C1",
            "supervisor_sha256": args.self_sha256,
            "worker_sha256": args.worker_sha256,
            "worker_returncode": process.returncode,
            "worker_process_group_empty_after_wait": descendants_empty,
            "worker_timed_out": timed_out,
            "worker_output_limit_exceeded": output_limit_exceeded,
            "worker_stdout_empty": len(stdout) == 0,
            "worker_stderr_empty": len(stderr) == 0,
            "worker_resource_usage": usage,
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

        phase = "ATOMIC_TERMINAL_PASS_SEAL"
        seal = {
            "schema": "s45b-c1-numeric-camera-guard-terminal-pass-seal-v1",
            "status": "PASS_C1_REQUESTED_CAMERA_INPUT_CONDITION_GUARD_ONLY",
            "passed": True,
            "terminal_authority": True,
            "row": "C1",
            "numeric_worker_verdict": report["numeric_worker_verdict"],
            "worker_returncode_observed": 0,
            "worker_process_group_empty_after_wait": True,
            "worker_timed_out": False,
            "worker_output_limit_exceeded": False,
            "worker_stdout_empty": True,
            "worker_stderr_empty": True,
            "worker_resource_boundaries_passed": True,
            "supervisor_sha256": args.self_sha256,
            "worker_sha256": args.worker_sha256,
            "primary_source_review_sha256": args.primary_source_review_sha256,
            "adversarial_source_review_sha256": args.adversarial_source_review_sha256,
            "binding_sha256": args.binding_sha256,
            "binding_review_sha256": args.binding_review_sha256,
            "attempt_lock_sha256": lock_sha256,
            "post_worker_exit_and_post_barrier_evidence": after_barrier,
            "all_writable_artifact_fds_fsynced_and_closed_before_authority_commit": True,
            "completed_utc": utc(),
            "independent_result_review_required": True,
            "evidence_boundary": (
                "Requested archived c2w/K input-condition validity only; no pixel score, "
                "quality, rendered-camera obedience, method gain, causal result, or novelty"
            ),
        }
        publish_terminal_seal(
            worker, parent_fd, HERE, parent_identity,
            lock_fd, LOCK.name, lock_identity, lock_sha256, lock_bytes,
            output_fd, FORMAL_OUT.name, output_identity, leases, seal,
        )
        return 0
    except BaseException as error:
        if process is not None and process.poll() is None:
            terminate_group(process.pid)
            try:
                process.wait(timeout=5)
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
        for fd in (capability_write, capability_read, output_fd, lock_fd, parent_fd):
            if type(fd) is int and fd >= 0:
                try:
                    os.close(fd)
                except OSError:
                    pass


def synthetic_setup(worker, root):
    parent_flags = (
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    )
    parent_fd = os.open(root, parent_flags)
    fcntl.flock(parent_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    parent_identity = worker.inode_identity(os.fstat(parent_fd))
    lock_doc = {
        "schema": "synthetic-attempt-lock-v1",
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
        "schema": "s45b-c1-numeric-camera-guard-terminal-pass-seal-v1",
        "status": "PASS_C1_REQUESTED_CAMERA_INPUT_CONDITION_GUARD_ONLY",
        "passed": True,
        "terminal_authority": True,
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
        [sys.executable, "-I", "-B", "-S", str(SELF),
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
    process = subprocess.Popen(
        [sys.executable, "-I", "-B", "-S", str(SELF),
         "--synthetic-resource-child", mode],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        start_new_session=True,
    )
    stdout, stderr, timed_out, output_limit_exceeded = bounded_process_wait(
        process, time_limit=time_limit,
    )
    empty = process_group_empty(process.pid)
    if not empty:
        terminate_group(process.pid)
    return process.returncode, stdout, stderr, timed_out, output_limit_exceeded, empty


def synthetic_selftest():
    worker, worker_record = load_worker_same_fd()
    checks = {}

    with tempfile.TemporaryDirectory(prefix="s45b_supervised_nominal_") as raw:
        state = synthetic_setup(worker, Path(raw).resolve())
        try:
            synthetic_publish(worker, state)
            require(terminal_seal_authoritative(state["output_fd"]),
                    "Nominal terminal seal is not authoritative")
            checks["nominal_atomic_terminal_pass"] = "PASS"
        finally:
            synthetic_close(state)

    with tempfile.TemporaryDirectory(prefix="s45b_supervised_failure_marker_") as raw:
        state = synthetic_setup(worker, Path(raw).resolve())
        try:
            synthetic_publish(worker, state)
            worker.write_new_at(
                state["output_fd"], TERMINAL_FAILURE_NAME,
                {"schema": "synthetic-late-failure", "passed": False},
            )
            require(not terminal_seal_authoritative(state["output_fd"]),
                    "Terminal failure marker did not invalidate a seal")
            checks["terminal_failure_marker_invalidates_pass"] = "PASS_REJECTED"
        finally:
            synthetic_close(state)

    for fault in (
        "STAGE_CLOSE_BEFORE_PUBLISH",
        "DIR_FSYNC_BEFORE_COMMIT",
        "ARTIFACT_CLOSE_BEFORE_COMMIT",
        "FINAL_DIR_FSYNC_BEFORE_COMMIT",
    ):
        with tempfile.TemporaryDirectory(prefix="s45b_supervised_fault_") as raw:
            state = synthetic_setup(worker, Path(raw).resolve())
            try:
                try:
                    synthetic_publish(worker, state, fault=fault)
                except InjectedSyntheticFailure:
                    pass
                else:
                    raise AssertionError("Synthetic fault did not interrupt: " + fault)
                require(not terminal_seal_authoritative(state["output_fd"]),
                        "Injected failure left an authoritative PASS: " + fault)
                checks[fault.lower()] = "PASS_FAIL_CLOSED"
            finally:
                synthetic_close(state)

    for fault, expected_returncode in (("SIGKILL_AFTER_LINK", -signal.SIGKILL),
                                       ("SIGTERM_AFTER_LINK", -signal.SIGTERM)):
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
                require(not terminal_seal_authoritative(output_fd),
                        "Signal interruption left an authoritative PASS")
                final_stat = os.stat(TERMINAL_SEAL_NAME, dir_fd=output_fd, follow_symlinks=False)
                require(final_stat.st_nlink == 2
                        and not worker.entry_absent(output_fd, TERMINAL_SEAL_STAGING_NAME),
                        "Interrupted seal does not retain the expected invalid two-link state")
            finally:
                os.close(output_fd)
            checks[fault.lower()] = "PASS_FAIL_CLOSED_TWO_LINK_STATE"
        finally:
            import shutil
            shutil.rmtree(root)

    with tempfile.TemporaryDirectory(prefix="s45b_supervised_swap_") as raw:
        root = Path(raw).resolve()
        state = synthetic_setup(worker, root)
        try:
            os.rename("execution", "execution.old", src_dir_fd=state["parent_fd"], dst_dir_fd=state["parent_fd"])
            os.mkdir("execution", 0o700, dir_fd=state["parent_fd"])
            try:
                collect_evidence_bundle(
                    worker, state["parent_fd"], state["root"], state["parent_identity"],
                    state["lock_fd"], "attempt.lock", state["lock_identity"],
                    state["lock_sha"], state["lock_bytes"],
                    state["output_fd"], "execution", state["output_identity"],
                    state["leases"], sorted(state["leases"]),
                )
            except ValueError:
                checks["execution_directory_rename_recreate"] = "PASS_REJECTED"
            else:
                raise AssertionError("Canonical execution directory replacement was accepted")
        finally:
            synthetic_close(state)

    for attack in ("hardlink", "symlink"):
        with tempfile.TemporaryDirectory(prefix="s45b_supervised_artifact_") as raw:
            root = Path(raw).resolve()
            state = synthetic_setup(worker, root)
            try:
                if attack == "hardlink":
                    os.link("report.json", "report.alias", src_dir_fd=state["output_fd"], dst_dir_fd=state["output_fd"])
                else:
                    os.unlink("report.json", dir_fd=state["output_fd"])
                    os.symlink("worker_receipt.json", "report.json", dir_fd=state["output_fd"])
                try:
                    verify_regular_lease(
                        state["output_fd"], root / "execution",
                        state["leases"][REPORT_NAME],
                    )
                except (ValueError, OSError):
                    checks["report_" + attack + "_attack"] = "PASS_REJECTED"
                else:
                    raise AssertionError("Report alias/replacement attack was accepted")
            finally:
                synthetic_close(state)

    for mode, stream_name in (("STDOUT_OVERFLOW", "stdout"),
                              ("STDERR_OVERFLOW", "stderr")):
        returncode, stdout, stderr, timed_out, exceeded, empty = isolated_resource_process(mode)
        require(exceeded and not timed_out and empty and returncode != 0,
                "Output overflow was not terminated fail-closed")
        require(len(stdout) <= MAX_STDOUT_BYTES + 1 and len(stderr) <= MAX_STDERR_BYTES + 1,
                "Output overflow capture exceeded the hard observation bound")
        checks[stream_name + "_overflow"] = "PASS_TERMINATED_FAIL_CLOSED"

    returncode, stdout, stderr, timed_out, exceeded, empty = isolated_resource_process(
        "SLEEP_TIMEOUT", time_limit=0.1,
    )
    require(timed_out and not exceeded and empty and returncode != 0
            and stdout == b"" and stderr == b"",
            "Wall-time timeout was not terminated fail-closed")
    checks["wall_time_timeout"] = "PASS_TERMINATED_FAIL_CLOSED"

    return {
        "schema": "s45b-c1-numeric-camera-guard-supervisor-synthetic-selftest-v1",
        "status": "PASS_SUPERVISOR_SYNTHETIC_AND_FAULT_INJECTION_ONLY",
        "worker_source": worker_record,
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
    parser.add_argument("--synthetic-fault-child", choices=("SIGKILL_AFTER_LINK", "SIGTERM_AFTER_LINK"))
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
    parser.add_argument("--out")
    args = parser.parse_args()
    formal_names = (
        "self_sha256", "worker_sha256", "primary_source_review_sha256",
        "adversarial_source_review_sha256", "binding_sha256",
        "binding_review_sha256", "out",
    )
    if args.synthetic_self_test:
        require(args.synthetic_fault_child is None and args.synthetic_resource_child is None
                and args.synthetic_root is None
                and all(getattr(args, name) is None for name in formal_names),
                "Synthetic self-test accepts no formal or child arguments")
        print(json.dumps(synthetic_selftest(), sort_keys=True, allow_nan=False))
        return 0
    if args.synthetic_fault_child is not None:
        require(args.synthetic_resource_child is None and args.synthetic_root is not None
                and all(getattr(args, name) is None for name in formal_names),
                "Synthetic fault child accepts only its isolated root and fault")
        return synthetic_fault_child(args.synthetic_root, args.synthetic_fault_child)
    if args.synthetic_resource_child is not None:
        require(args.synthetic_fault_child is None and args.synthetic_root is None
                and all(getattr(args, name) is None for name in formal_names),
                "Synthetic resource child accepts no formal or filesystem arguments")
        return synthetic_resource_child(args.synthetic_resource_child)
    require(args.synthetic_root is None and all(getattr(args, name) is not None for name in formal_names),
            "Formal supervisor requires every exact identity and the canonical output")
    require(all(valid_sha(getattr(args, name)) for name in formal_names if name != "out"),
            "Formal supervisor received a malformed SHA-256")
    return formal_supervision(args)


if __name__ == "__main__":
    raise SystemExit(main())
