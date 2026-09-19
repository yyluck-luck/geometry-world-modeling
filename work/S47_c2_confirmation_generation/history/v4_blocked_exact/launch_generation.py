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
GATE_SHA256 = "299f2f3212fe0b1c17dd35f2ac7c05ac851c43b42f6ae1327f8af60ae68aa264"
PUBLISHED_MANIFEST = HERE / "review_attachment_01/manifest.json"
EXECUTION = HERE / "execution_01"
CAPABILITY_RECORD = "worker_capability.json"
CAPABILITY_CONSUMED = "worker_capability_consumed.json"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_SNAPSHOT_DIGESTS = {}
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


def read_json_snapshot(path, label, expected=None):
    payload = read_regular_snapshot(Path(path).absolute(), label)
    digest = hashlib.sha256(payload).hexdigest()
    if expected is not None:
        require(isinstance(expected, str) and HEX64.fullmatch(expected) and digest == expected,
                label + " SHA-256 differs")
    document = json.loads(payload)
    _SNAPSHOT_DIGESTS[str(Path(path).absolute())] = digest
    return document, digest


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


def read_c2_frozen_snapshot(path, expected, namespace):
    path = Path(path)
    require(path == PUBLISHED_MANIFEST, "Only the canonical C2 manifest may launch")
    manifest, _ = read_json_snapshot(path, "C2 launch manifest", expected)
    require(
        manifest.get("schema") == "s47-c2-confirmation-two-batch-v1"
        and manifest.get("status") == "FROZEN_C2_BASELINE_CONFIRMATION_TWO_BATCH_EXECUTION",
        "A frozen C2 baseline manifest is required",
    )
    runtime = manifest.get("runtime", {})
    require(runtime.get("python_executable") == str(namespace["PYTHON"]),
            "Only the frozen C2 virtualenv is supported")
    require(runtime.get("pythonpath") == [str(item) for item in namespace["PYTHONPATH"]],
            "Frozen C2 import-path order differs")
    require(namespace["PYTHON"].is_file()
            and all(item.is_dir() for item in namespace["PYTHONPATH"]),
            "C2 runtime paths are unavailable")
    current = snapshot_sha(Path(__file__).absolute())
    identities = manifest.get("source_identities", {})
    require(
        identities.get(str(Path(__file__).absolute())) == current
        and identities.get(str(GATE)) == GATE_SHA256,
        "C2 launcher or independently pinned gate is outside the manifest source domain",
    )
    return manifest


def write_new_json(path, document):
    payload = json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8") + b"\n"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            require(written > 0, "Short capability record write")
            view = view[written:]
        os.fchmod(descriptor, 0o444)
        os.fsync(descriptor)
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


def require_fixed_execution_argument(argv):
    """Validate the complete public vector and return the sanitized arguments."""
    return parse_exact_arguments(argv, internal=False)


def read_worker_launch_ticket(execution, manifest_sha256, launcher_sha256):
    require(Path(execution) == EXECUTION, "Worker execution directory is not canonical execution_01")
    ticket, _ = read_json_snapshot(EXECUTION / "launch_ticket.json", "Parent launch ticket")
    require(
        ticket.get("parent_pid") == os.getppid()
        and ticket.get("manifest_sha256") == manifest_sha256
        and ticket.get("launcher_sha256") == launcher_sha256,
        "Worker launch ticket differs from the live parent binding",
    )
    return ticket


def read_worker_receipt(path):
    document, _ = read_json_snapshot(path, "Worker terminal receipt")
    return document


def last_snapshot_sha(path):
    key = str(Path(path).absolute())
    require(key in _SNAPSHOT_DIGESTS, "No parsed snapshot SHA is available for " + key)
    return _SNAPSHOT_DIGESTS[key]


class ForkWorkerProcess:
    """Small Popen-compatible handle for the single forked C2 worker."""

    def __init__(self, pid):
        self.pid = pid
        self.returncode = None

    def poll(self):
        if self.returncode is not None:
            return self.returncode
        waited, status_value = os.waitpid(self.pid, os.WNOHANG)
        if waited == 0:
            return None
        self.returncode = os.waitstatus_to_exitcode(status_value)
        return self.returncode

    def wait(self, timeout=None):
        if self.returncode is not None:
            return self.returncode
        if timeout is None:
            _, status_value = os.waitpid(self.pid, 0)
            self.returncode = os.waitstatus_to_exitcode(status_value)
            return self.returncode
        deadline = time.monotonic() + max(0.0, timeout)
        while True:
            result = self.poll()
            if result is not None:
                return result
            if time.monotonic() >= deadline:
                raise subprocess.TimeoutExpired("S47 C2 forked worker", timeout)
            time.sleep(min(0.01, max(0.0, deadline - time.monotonic())))

    def terminate(self):
        if self.poll() is None:
            os.kill(self.pid, signal.SIGTERM)


def spawn_capability_worker(
    command,
    *,
    cwd,
    env,
    stdout,
    stderr,
    start_new_session,
    execution,
    manifest_sha256,
    launcher_sha256,
    output_root,
    worker_entry,
    capability,
    capability_state,
):
    """Fork once; only the inherited opaque object can enter the worker."""
    require(Path(execution) == EXECUTION, "Parent attempted a noncanonical worker execution path")
    internal = parse_exact_arguments(command[3:], internal=True)
    require(command[:3] == [str(ROOT / ".venv-cut3r/bin/python"), "-B", str(Path(__file__).absolute())],
            "Derived parent worker prefix changed")
    require(internal.manifest_sha256 == manifest_sha256,
            "Worker command manifest differs from parent state")
    require(
        capability is capability_state.get("token")
        and capability_state.get("issued") is False
        and capability_state.get("consumed") is False,
        "C2 internal worker capability was forged or reused",
    )
    require(not os.path.lexists(EXECUTION / CAPABILITY_RECORD)
            and not os.path.lexists(EXECUTION / CAPABILITY_CONSUMED),
            "Worker capability was already staged or consumed")
    require(start_new_session is True, "C2 worker must retain its monitored process group")
    capability_state["issued"] = True
    capability_state["parent_pid"] = os.getpid()
    ready_read, ready_write = os.pipe()
    process = None
    try:
        pid = os.fork()
        if pid == 0:
            exit_code = 1
            try:
                os.close(ready_write)
                if start_new_session:
                    os.setsid()
                os.chdir(cwd)
                os.environ.clear()
                os.environ.update(env)
                os.dup2(stdout.fileno(), 1)
                os.dup2(stderr.fileno(), 2)
                require(os.read(ready_read, 1) == b"1",
                        "Parent did not issue the C2 worker capability")
                os.close(ready_read)
                exit_code = int(worker_entry(internal, capability))
            except BaseException:
                traceback.print_exc()
            finally:
                os._exit(exit_code)
        process = ForkWorkerProcess(pid)
        os.close(ready_read)
        ready_read = -1
        record = {
            "schema": "s47-c2-worker-capability-record-v1",
            "status": "ISSUED_ONCE_BY_MONITORED_PARENT",
            "parent_pid": os.getpid(),
            "worker_pid": pid,
            "manifest_sha256": manifest_sha256,
            "launcher_sha256": launcher_sha256,
            "execution_directory": str(EXECUTION),
            "output_root": str(output_root),
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "secret_sha256": hashlib.sha256(capability_state["secret"]).hexdigest(),
            "capability_transport": "FORK_INHERITED_OPAQUE_MEMORY_TOKEN_WITH_ONE_BYTE_PARENT_SYNC",
            "public_worker_cli": False,
            "reusable": False,
        }
        write_new_json(EXECUTION / CAPABILITY_RECORD, record)
        require(os.write(ready_write, b"1") == 1, "Worker capability sync write failed")
    except BaseException:
        if process is not None:
            process.terminate()
            process.wait()
        raise
    finally:
        if ready_read >= 0:
            os.close(ready_read)
        os.close(ready_write)
    return process


def consume_worker_capability(args, capability, capability_state):
    """Consume the fork-inherited object identity before the raw worker gate."""
    require(Path(args.execution_directory) == EXECUTION,
            "Internal worker is not bound to canonical execution_01")
    record, _ = read_json_snapshot(EXECUTION / CAPABILITY_RECORD, "Worker capability record")
    require(
        capability is capability_state.get("token")
        and capability_state.get("issued") is True
        and capability_state.get("consumed") is False
        and capability_state.get("parent_pid") == os.getppid()
        and isinstance(capability_state.get("secret"), bytes)
        and len(capability_state["secret"]) == 32
        and record.get("schema") == "s47-c2-worker-capability-record-v1"
        and record.get("parent_pid") == os.getppid()
        and record.get("worker_pid") == os.getpid()
        and record.get("manifest_sha256") == args.manifest_sha256
        and record.get("launcher_sha256") == snapshot_sha(Path(__file__).absolute())
        and record.get("execution_directory") == str(EXECUTION)
        and record.get("secret_sha256")
        == hashlib.sha256(capability_state["secret"]).hexdigest()
        and record.get("status") == "ISSUED_ONCE_BY_MONITORED_PARENT"
        and record.get("capability_transport")
        == "FORK_INHERITED_OPAQUE_MEMORY_TOKEN_WITH_ONE_BYTE_PARENT_SYNC"
        and record.get("public_worker_cli") is False
        and record.get("reusable") is False
        and not os.path.lexists(EXECUTION / CAPABILITY_CONSUMED),
        "Worker capability is forged, redirected, or already consumed",
    )
    capability_state["consumed"] = True
    consumed = dict(
        schema="s47-c2-worker-capability-consumption-v1",
        status="CONSUMED_ONCE_BEFORE_WORKER_GATE",
        consumed_utc=datetime.now(timezone.utc).isoformat(),
        parent_pid=os.getppid(),
        worker_pid=os.getpid(),
        manifest_sha256=args.manifest_sha256,
        capability_record_sha256=last_snapshot_sha(EXECUTION / CAPABILITY_RECORD),
        secret_sha256=record["secret_sha256"],
        capability_transport=record["capability_transport"],
        reusable=False,
    )
    write_new_json(EXECUTION / CAPABILITY_CONSUMED, consumed)
    return consumed


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
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "subprocess"
                and node.func.attr == "Popen"
            ):
                hardening["capability_spawn"] += 1
                replacement = copy.deepcopy(node)
                replacement.func = ast.Name(id="_spawn_capability_worker", ctx=ast.Load())
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
    namespace = {
        "__file__": str(Path(__file__).absolute()),
        "__name__": "_s47_c2_derived_supervisor",
        "_read_bound_launch_ticket": read_worker_launch_ticket,
        "_read_worker_receipt": read_worker_receipt,
        "_last_snapshot_sha": last_snapshot_sha,
    }
    exec(code, namespace)
    namespace["sha"] = snapshot_sha
    namespace["load_bound"] = load_bound_snapshot
    namespace["read_frozen"] = lambda path, expected: read_c2_frozen_snapshot(
        path, expected, namespace
    )
    raw_parent = namespace["parent"]
    raw_worker = namespace["worker"]
    capability_state = {
        "token": None,
        "secret": None,
        "issued": False,
        "consumed": False,
    }

    def guarded_worker(args, capability):
        require(Path(args.execution_directory) == EXECUTION and args.worker is True,
                "Worker is not bound to canonical execution_01")
        consume_worker_capability(args, capability, capability_state)
        return raw_worker(args)

    def spawn_bound_worker(*args, **kwargs):
        require(
            capability_state == {
                "token": None,
                "secret": None,
                "issued": False,
                "consumed": False,
            },
            "C2 worker capability was already created",
        )
        capability_state["token"] = object()
        capability_state["secret"] = secrets.token_bytes(32)
        return spawn_capability_worker(
            *args,
            worker_entry=guarded_worker,
            capability=capability_state["token"],
            capability_state=capability_state,
            **kwargs,
        )

    namespace["_spawn_capability_worker"] = spawn_bound_worker

    def guarded_parent(args):
        require(Path(args.execution_directory) == EXECUTION and args.worker is False,
                "Parent is not bound to canonical execution_01")
        return raw_parent(args)

    namespace["parent"] = guarded_parent
    namespace["worker"] = guarded_worker
    namespace["worker_capability_publicly_available"] = False
    return namespace


def main():
    argv = sys.argv[1:]
    args = parse_exact_arguments(argv, internal=False)
    def interrupted(signum, frame):
        raise KeyboardInterrupt("Launcher/worker received signal " + str(signum))
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    namespace = derive_launcher()
    return namespace["parent"](args)


if __name__ == "__main__":
    raise SystemExit(main())
