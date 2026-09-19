#!/usr/bin/env python3
"""Create and attach reviews to the one frozen S47 C2 manifest."""
from __future__ import annotations

import argparse
import copy
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import traceback
from types import ModuleType


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SELF = Path(__file__).resolve()
FREEZE_PROTOCOL = HERE / "FREEZE_PROTOCOL.md"
FREEZE_PROTOCOL_SHA256 = "122f840d3be68d813bb911445590e3b2c00a7428de92020fe1624933df4d9faf"
GATE = HERE / "generation_gate.py"
SOURCE_HASHES = {
    "generation_gate.py": "5add4e5b6170f42ff75cdede7f40a061cd1b98a253f0fb6411444990155255ec",
    "runtime_adapter.py": "5e6f2e89c724cfc3f5b4eb486eb2a9384fde9b23fb12010576f5c7f3f98e8d7f",
    "launch_generation.py": "4a96ba1e49a8ce2dae4885f70cf3b55debcacde594425dbaae1d59268dafc974",
    "create_launch_authorization.py": "209d6b141e154574d8ddd59e252839c27c911e4ec6fba4b18da5a9aca16ec89e",
    "PROTOCOL.md": "183ae19b30c28b224d631e0d1a06051322391dab10386de0169a98a4f1e952ef",
}
PREPARE_OUTPUT = HERE / "freeze_attempt_01"
ATTACH_OUTPUT = HERE / "review_attachment_01"
EXECUTION_OUTPUT = HERE / "execution_01"
PREPARE_STAGE = HERE / ".freeze_attempt_01.staging"
ATTACH_STAGE = HERE / ".review_attachment_01.staging"
PREPARE_SENTINEL = HERE / ".freeze_attempt_01.claimed"
ATTACH_SENTINEL = HERE / ".review_attachment_01.claimed"
AUTHOR_ROLE = "/root"


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    payload, _ = read_regular_snapshot(Path(path).absolute(), "Bound file")
    return hashlib.sha256(payload).hexdigest()


def read_regular_snapshot(path, label):
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
        payload = b"".join(chunks)
        require(
            (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
            == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
            and len(payload) == before.st_size,
            label + " changed while its descriptor was open",
        )
        return payload, before
    finally:
        os.close(descriptor)


def verified_bytes(path, expected, label):
    payload, identity = read_regular_snapshot(Path(path).absolute(), label)
    require(isinstance(expected, str) and len(expected) == 64
            and hashlib.sha256(payload).hexdigest() == expected,
            label + " SHA-256 differs")
    return payload, identity


def json_bytes(value):
    return (
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    ).encode("utf-8")


def read_json(path, expected, label):
    path = Path(path)
    require(path.is_absolute(), label + " path must be absolute")
    payload, _ = verified_bytes(path, expected, label)
    return json.loads(payload)


def occupied(path):
    """Treat every directory entry, including a broken symlink, as occupied."""
    return os.path.lexists(os.fspath(path))


def directory_flags():
    return (
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    )


class DirectoryLease:
    """Persistent no-follow directory and ancestor identity binding."""

    def __init__(self, path, chain):
        self.path = Path(path)
        self.chain = chain
        self.fd = chain[-1][1]
        final = os.fstat(self.fd)
        self.identity = {"device": final.st_dev, "inode": final.st_ino}
        self.closed = False

    @classmethod
    def open(cls, path):
        path = Path(path)
        require(path.is_absolute(), "Directory lease path must be absolute")
        current = os.open("/", directory_flags())
        root = os.fstat(current)
        chain = [(Path("/"), current, root.st_dev, root.st_ino)]
        prefix = Path("/")
        try:
            for part in path.parts[1:]:
                following = os.open(part, directory_flags(), dir_fd=current)
                opened = os.fstat(following)
                require(stat.S_ISDIR(opened.st_mode), "Directory lease component is not a directory")
                prefix = prefix / part
                chain.append((prefix, following, opened.st_dev, opened.st_ino))
                current = following
            result = cls(path, chain)
            result.validate()
            return result
        except BaseException:
            for _, descriptor, _, _ in reversed(chain):
                try:
                    os.close(descriptor)
                except OSError:
                    pass
            raise

    def validate(self):
        require(not self.closed, "Directory lease is already closed")
        for path, descriptor, device, inode in self.chain:
            opened = os.fstat(descriptor)
            named = os.stat(path, follow_symlinks=False)
            require(
                stat.S_ISDIR(opened.st_mode) and stat.S_ISDIR(named.st_mode)
                and (opened.st_dev, opened.st_ino) == (device, inode)
                and (named.st_dev, named.st_ino) == (device, inode),
                "Directory lease or ancestor changed: " + str(path),
            )
        return dict(self.identity)

    def entries(self):
        self.validate()
        return set(os.listdir(self.fd))

    def close(self):
        if not self.closed:
            self.closed = True
            for _, descriptor, _, _ in reversed(self.chain):
                try:
                    os.close(descriptor)
                except OSError:
                    pass


def entry_exists(directory, name):
    try:
        os.stat(name, dir_fd=directory.fd, follow_symlinks=False)
    except FileNotFoundError:
        return False
    return True


def write_new_at(directory, name, value, *, mode=0o444):
    directory.validate()
    payload = json_bytes(value)
    flags = (
        os.O_WRONLY | os.O_CREAT | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    )
    descriptor = os.open(name, flags, 0o600, dir_fd=directory.fd)
    try:
        view = memoryview(payload)
        while view:
            count = os.write(descriptor, view)
            require(count > 0, "Short create-only freeze record write")
            view = view[count:]
        os.fchmod(descriptor, mode)
        os.fsync(descriptor)
        opened = os.fstat(descriptor)
        named = os.stat(name, dir_fd=directory.fd, follow_symlinks=False)
        require(
            stat.S_ISREG(opened.st_mode)
            and (opened.st_dev, opened.st_ino) == (named.st_dev, named.st_ino)
            and opened.st_size == len(payload),
            "Freeze record inode changed while its descriptor was held",
        )
    finally:
        os.close(descriptor)
    os.fsync(directory.fd)
    return hashlib.sha256(payload).hexdigest()


def atomic_publish_directory_at(parent, stage_name, destination_name, stage):
    """RENAME_EXCL relative to one held parent dirfd; retain the moved inode."""
    parent.validate()
    stage.validate()
    require(entry_exists(parent, stage_name) and not entry_exists(parent, destination_name),
            "Freeze publication source/destination lease changed")
    libc = ctypes.CDLL(None, use_errno=True)
    require(hasattr(libc, "renameatx_np"), "macOS renameatx_np is required")
    renameatx_np = libc.renameatx_np
    renameatx_np.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    renameatx_np.restype = ctypes.c_int
    result = renameatx_np(
        parent.fd, os.fsencode(stage_name), parent.fd, os.fsencode(destination_name), 0x00000004
    )
    if result != 0:
        number = ctypes.get_errno()
        raise OSError(number, os.strerror(number), destination_name)
    os.fsync(parent.fd)
    named = os.stat(destination_name, dir_fd=parent.fd, follow_symlinks=False)
    opened = os.fstat(stage.fd)
    require(
        stat.S_ISDIR(named.st_mode)
        and (named.st_dev, named.st_ino) == (opened.st_dev, opened.st_ino)
        and not entry_exists(parent, stage_name),
        "Published freeze directory is not the held staging inode",
    )
    _, descriptor, device, inode = stage.chain[-1]
    stage.path = parent.path / destination_name
    stage.chain[-1] = (stage.path, descriptor, device, inode)
    stage.validate()


def load_gate():
    require(sha(FREEZE_PROTOCOL) == FREEZE_PROTOCOL_SHA256, "Freeze protocol changed")
    for name, expected in SOURCE_HASHES.items():
        require(sha(HERE / name) == expected, "C2 runtime source changed: " + name)
    payload, _ = verified_bytes(
        GATE, SOURCE_HASHES["generation_gate.py"], "Frozen C2 generation gate source"
    )
    name = "_s47_c2_freeze_gate"
    module = ModuleType(name)
    module.__file__ = str(GATE)
    module.__package__ = ""
    sys.modules[name] = module
    try:
        exec(compile(payload, str(GATE), "exec", dont_inherit=True), module.__dict__)
    except BaseException:
        if sys.modules.get(name) is module:
            del sys.modules[name]
        raise
    require(module.required_sources()[str(GATE)] == SOURCE_HASHES["generation_gate.py"],
            "C2 gate source-domain identity differs")
    return module


def freeze_preparation_record(gate):
    return {
        "schema": "s47-c2-core-freeze-v1",
        "tool_source": {"path": str(SELF), "sha256": sha(SELF)},
        "freeze_protocol": {
            "path": str(FREEZE_PROTOCOL),
            "sha256": FREEZE_PROTOCOL_SHA256,
        },
        "base_s40": gate.exact_parent_bindings()["s40_manifest"],
        "s42_preregistration": gate.exact_parent_bindings()["s42_preregistration"],
        "component_bodies_read": 0,
        "pixels_decoded": 0,
        "scientific_imports": 0,
        "purpose": "Await two separately authored reviews of the exact C2 baseline core",
    }


def require_fresh_reserved(gate):
    require(not occupied(gate.C2_OUTPUT), "Reserved C2 scientific output root is not fresh")
    require(not occupied(EXECUTION_OUTPUT), "C2 execution_01 already exists")
    require(
        not occupied(gate.LAUNCH_AUTHORIZATION),
        "prepare/attach requires the later launch authorization path to remain absent",
    )
    require(
        not occupied(gate.AUTHORIZATION_ATTEMPT),
        "prepare/attach requires the authorization-attempt lease to remain absent",
    )
    require(
        not occupied(gate.ATTACH_PREFLIGHT_ROOT),
        "A fixed attach-preflight lease is already occupied",
    )


def build_core(gate):
    base = gate.read_base_s40()
    require(sha(gate.S42_PROTOCOL) == gate.S42_PROTOCOL_SHA256,
            "S42 preregistration changed")
    require(
        gate.C2_INPUT.is_file()
        and gate.C2_INPUT.stat().st_size == gate.C2_INPUT_BYTES
        and sha(gate.C2_INPUT) == gate.C2_INPUT_SHA256,
        "C2 input path, size, or full SHA-256 differs",
    )
    gate.require_single_seed_config_derivation(base)
    core = {
        "schema": gate.SCHEMA,
        "status": gate.FROZEN,
        "evidence_kind": "recorded_execution",
        "variant": copy.deepcopy(base["variant"]),
        "created_utc": utc(),
        "controls": copy.deepcopy(gate.CONTROLS),
        "runtime": copy.deepcopy(base["runtime"]),
        "generation_limits": copy.deepcopy(base["generation_limits"]),
        "output_root": str(gate.C2_OUTPUT),
        "components": copy.deepcopy(base["components"]),
        "config": gate.exact_config_record(),
        "input_image": gate.exact_input_record(),
        "source_identities": gate.required_sources(),
        "s39_loading_manifest": copy.deepcopy(base["s39_loading_manifest"]),
        "s39_resource_core_sha256": base["s39_resource_core_sha256"],
        "s39_loading_evidence": copy.deepcopy(base["s39_loading_evidence"]),
        "s39_loading_review": copy.deepcopy(base["s39_loading_review"]),
        "parent_bindings": gate.exact_parent_bindings(),
        "derivation_policy": gate.exact_derivation_policy(),
        "freeze_preparation": freeze_preparation_record(gate),
        "review_receipts": {},
    }
    return core


def verify_unreviewed_core(gate, core, expected_sha, expected_core_sha,
                           expected_prepare_receipt_sha):
    prepared = gate.require_successful_prepare_bundle(
        core_file_sha256_value=expected_sha,
        core_sha256_value=expected_core_sha,
        receipt_sha256_value=expected_prepare_receipt_sha,
    )
    require(prepared["core"] == core, "Successful prepare core snapshot differs")
    expected = build_core(gate)
    expected["created_utc"] = core.get("created_utc")
    require(core == expected, "Frozen C2 core differs from the exact builder policy")
    require(core.get("review_receipts") == {}, "Unreviewed C2 core already has review bindings")
    require(
        core.get("freeze_preparation") == freeze_preparation_record(gate),
        "C2 freeze preparation identity differs",
    )
    return gate.core_sha256(core), prepared


def prepare(args, gate, stage, output, receipt, core):
    require(output == PREPARE_OUTPUT, "Prepare output must be freeze_attempt_01")
    require_fresh_reserved(gate)
    core_file_sha = write_new_at(stage, "manifest_core.json", core, mode=0o444)
    core_sha = gate.core_sha256(core)
    receipt.update(
        status="S47_C2_CORE_FROZEN_AWAITING_TWO_REVIEWS",
        manifest_core_path=str(output / "manifest_core.json"),
        manifest_core_file_sha256=core_file_sha,
        core_sha256=core_sha,
        input_bytes_hashed=gate.C2_INPUT_BYTES,
        config_bytes_hashed=gate.C2_CONFIG.stat().st_size,
        config_seed_derivation="EXACT_S40_BYTES_EXCEPT_UNIQUE_SEED_42_TO_44_PLUS_ONE_TERMINAL_LF",
        pixels_decoded=0,
        component_bodies_read=0,
        scientific_imports=0,
        generation_calls=0,
        prepare_receipt_path=str(output / "receipt.json"),
        prepare_directory_identity=dict(stage.identity),
        terminal_shape=["manifest_core.json", "receipt.json"],
        retry_permitted=False,
    )


def build_attachment(args, gate):
    core_path = Path(args.core)
    require(core_path == PREPARE_OUTPUT / "manifest_core.json",
            "Attach requires the unique freeze_attempt_01 core")
    core = read_json(core_path, args.core_file_sha256, "C2 manifest core")
    core_sha, prepared = verify_unreviewed_core(
        gate, core, args.core_file_sha256, args.core_sha256,
        args.prepare_receipt_sha256,
    )
    require(core_sha == args.core_sha256, "Caller-bound C2 core SHA differs")
    bindings = {
        "source_review": (Path(args.source_review), args.source_review_sha256),
        "runtime_freeze": (Path(args.runtime_review), args.runtime_review_sha256),
    }
    reviewer_roles = []
    final = copy.deepcopy(core)
    for role, (path, expected) in bindings.items():
        review = read_json(path, expected, "C2 " + role)
        require(
            review.get("schema") == "s47-c2-generation-core-review-v1"
            and review.get("status") == gate.REVIEW_STATUSES[role]
            and review.get("row") == "C2"
            and review.get("variant") == gate.VARIANT
            and review.get("core_path") == str(core_path)
            and review.get("core_file_sha256") == args.core_file_sha256
            and review.get("core_sha256") == core_sha
            and review.get("prepare_receipt_sha256") == prepared["receipt_sha256"]
            and review.get("author_role") == AUTHOR_ROLE
            and isinstance(review.get("reviewer_role"), str)
            and review["reviewer_role"] != AUTHOR_ROLE
            and review.get("executed") is False
            and review.get("model_or_scientific_imports") == 0
            and review.get("pixels_decoded") == 0
            and review.get("blocking_findings") == [],
            "C2 review does not approve this exact unexecuted core: " + role,
        )
        reviewer_roles.append(review["reviewer_role"])
        final["review_receipts"][role] = {"path": str(path), "sha256": expected}
    require(len(set(reviewer_roles)) == 2, "C2 source and runtime reviews require distinct authors")
    require(gate.core_sha256(final) == core_sha, "Attaching reviews changed C2 core")
    return final, core_sha, prepared["receipt_sha256"], prepared["directory_identity"]


def preflight_attachment(args, gate, here):
    """Validate the exact future manifest without publishing an executable path."""
    final, core_sha, prepare_receipt_sha, prepare_identity = build_attachment(args, gate)
    manifest_sha = hashlib.sha256(json_bytes(final)).hexdigest()
    preflight_root = gate.ATTACH_PREFLIGHT_ROOT
    candidate = gate.ATTACH_PREFLIGHT_MANIFEST
    require(not occupied(preflight_root), "Fixed C2 attach-preflight lease is occupied")
    here.validate()
    os.mkdir(preflight_root.name, mode=0o700, dir_fd=here.fd)
    preflight = DirectoryLease.open(preflight_root)
    completed = False
    try:
        staged_sha = write_new_at(preflight, candidate.name, final, mode=0o444)
        require(staged_sha == manifest_sha, "C2 attachment candidate bytes differ")
        metadata = gate.check_attachment_preflight(candidate, manifest_sha)
        completed = True
    finally:
        if completed:
            preflight.validate()
            os.unlink(candidate.name, dir_fd=preflight.fd)
            os.fsync(preflight.fd)
            preflight.close()
            os.rmdir(preflight_root.name, dir_fd=here.fd)
            os.fsync(here.fd)
        else:
            preflight.close()
    require(
        metadata.get("status") == "UNPUBLISHED_ATTACHMENT_PREFLIGHT_ONLY"
        and metadata.get("unpublished_attachment_check") is True
        and metadata.get("execution_authorized") is False,
        "C2 unpublished attachment metadata preflight failed",
    )
    return final, core_sha, prepare_receipt_sha, prepare_identity, manifest_sha, metadata


def attach(stage, output, gate, receipt, final, core_sha, prepare_receipt_sha,
           prepare_identity, manifest_sha, metadata):
    require(output == ATTACH_OUTPUT, "Attach output must be review_attachment_01")
    require_fresh_reserved(gate)
    require(
        hashlib.sha256(json_bytes(final)).hexdigest() == manifest_sha,
        "C2 attachment bytes changed after preflight",
    )
    metadata_sha = write_new_at(stage, "metadata_gate.json", metadata, mode=0o444)
    receipt.update(
        status="S47_C2_REVIEWS_ATTACHED_METADATA_GATE_PASSED",
        manifest_path=str(gate.PUBLISHED_MANIFEST),
        manifest_sha256=manifest_sha,
        core_file_sha256=sha(PREPARE_OUTPUT / "manifest_core.json"),
        core_sha256=core_sha,
        prepare_receipt_sha256=prepare_receipt_sha,
        prepare_directory_identity=prepare_identity,
        review_receipts=copy.deepcopy(final["review_receipts"]),
        metadata_gate_status=metadata["status"],
        metadata_gate_path=str(gate.PUBLISHED_METADATA_GATE),
        metadata_gate_sha256=metadata_sha,
        model_or_scientific_imports=0,
        config_seed_derivation="EXACT_S40_BYTES_EXCEPT_UNIQUE_SEED_42_TO_44_PLUS_ONE_TERMINAL_LF",
        pixels_decoded=0,
        generation_calls=0,
        scientific_status="NOT_EVALUATED",
        attachment_directory_identity=dict(stage.identity),
        terminal_shape=["manifest.json", "metadata_gate.json", "receipt.json"],
        retry_permitted=False,
    )
    receipt["completed_utc"] = utc()
    receipt["source_unchanged_at_close"] = sha(SELF) == receipt["tool_source_sha256"]
    require(receipt["source_unchanged_at_close"], "C2 freeze tool changed before publication")
    require_fresh_reserved(gate)
    # The success receipt is still non-authoritative without the canonical
    # manifest.  Publishing the manifest is deliberately the final mutation.
    write_new_at(stage, "receipt.json", receipt, mode=0o444)
    require_fresh_reserved(gate)
    write_new_at(stage, "manifest.json", final, mode=0o444)


def validate_cli(args, output):
    attach_values = (
        args.core,
        args.core_file_sha256,
        args.core_sha256,
        args.prepare_receipt_sha256,
        args.source_review,
        args.source_review_sha256,
        args.runtime_review,
        args.runtime_review_sha256,
    )
    if args.mode == "prepare":
        require(output == PREPARE_OUTPUT, "Prepare output must be freeze_attempt_01")
        require(all(value is None for value in attach_values), "Prepare rejects attach-only arguments")
    else:
        require(output == ATTACH_OUTPUT, "Attach output must be review_attachment_01")
        require(
            all(isinstance(value, str) and bool(value) for value in attach_values),
            "Attach requires complete core and review bindings",
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=("prepare", "attach"))
    parser.add_argument("--out", required=True)
    parser.add_argument("--core")
    parser.add_argument("--core-file-sha256")
    parser.add_argument("--core-sha256")
    parser.add_argument("--prepare-receipt-sha256")
    parser.add_argument("--source-review")
    parser.add_argument("--source-review-sha256")
    parser.add_argument("--runtime-review")
    parser.add_argument("--runtime-review-sha256")
    args = parser.parse_args()
    output = Path(args.out)
    selected_stage = PREPARE_STAGE if args.mode == "prepare" else ATTACH_STAGE
    sentinel = PREPARE_SENTINEL if args.mode == "prepare" else ATTACH_SENTINEL
    require(output.is_absolute(), "C2 freeze output must use its exact absolute path")
    receipt = {
        "schema": "s47-c2-freeze-tool-receipt-v2",
        "status": "CHECKING",
        "mode": args.mode,
        "started_utc": utc(),
        "tool_source_path": str(SELF),
        "tool_source_sha256": sha(SELF),
        "freeze_protocol_sha256": FREEZE_PROTOCOL_SHA256,
        "scientific_status": "NOT_EVALUATED",
    }
    stage = None
    here = DirectoryLease.open(HERE)
    prepare_lease = None
    published = False
    receipt_written = False
    failure_record = None
    try:
        # Complete every non-mutating command/source/parent/input/config review
        # before the sole protocol-compliant output directory can be consumed.
        validate_cli(args, output)
        here.validate()
        require(not entry_exists(here, output.name), "C2 freeze output already exists")
        require(not entry_exists(here, selected_stage.name),
                "Fixed C2 freeze/attach staging lease is occupied")
        require(not entry_exists(here, sentinel.name),
                "The fixed C2 freeze/attach attempt sentinel is already occupied")
        gate = load_gate()
        require_fresh_reserved(gate)
        if args.mode == "prepare":
            prepared = build_core(gate)
        else:
            require(entry_exists(here, PREPARE_SENTINEL.name),
                    "Attach requires the consumed unique prepare sentinel")
            prepare_lease = DirectoryLease.open(PREPARE_OUTPUT)
            require(prepare_lease.entries() == {"manifest_core.json", "receipt.json"},
                    "Attach requires the exact successful prepare directory shape")
            prepared = preflight_attachment(args, gate, here)
        require_fresh_reserved(gate)
        if prepare_lease is not None:
            prepare_lease.validate()
        here.validate()
        require(not entry_exists(here, output.name),
                "C2 freeze output was occupied during preflight")
        require(not entry_exists(here, selected_stage.name),
                "Fixed C2 staging lease was occupied during preflight")
        sentinel_document = {
            "schema": "s47-c2-fixed-attempt-sentinel-v1",
            "status": "ATTEMPT_IRREVERSIBLY_CLAIMED",
            "mode": args.mode,
            "claimed_utc": utc(),
            "tool_source_sha256": receipt["tool_source_sha256"],
            "parent_directory_identity": dict(here.identity),
            "output_path": str(output),
            "staging_path": str(selected_stage),
            "retry_permitted": False,
        }
        sentinel_sha = write_new_at(here, sentinel.name, sentinel_document, mode=0o444)
        receipt["attempt_sentinel"] = {"path": str(sentinel), "sha256": sentinel_sha}
        os.mkdir(selected_stage.name, mode=0o700, dir_fd=here.fd)
        stage = DirectoryLease.open(selected_stage)
        if args.mode == "prepare":
            prepare(args, gate, stage, output, receipt, prepared)
            receipt["completed_utc"] = utc()
            receipt["source_unchanged_at_close"] = sha(SELF) == receipt["tool_source_sha256"]
            require(receipt["source_unchanged_at_close"], "C2 freeze tool changed before receipt")
            write_new_at(stage, "receipt.json", receipt, mode=0o444)
            receipt_written = True
            require(stage.entries() == {"manifest_core.json", "receipt.json"},
                    "Prepare success directory has an unexpected terminal shape")
        else:
            attach(stage, output, gate, receipt, *prepared)
            receipt_written = True
            require(stage.entries() == {"manifest.json", "metadata_gate.json", "receipt.json"},
                    "Attach success directory has an unexpected terminal shape")
        require_fresh_reserved(gate)
        here.validate()
        require(not entry_exists(here, output.name),
                "C2 freeze output was occupied before atomic publication")
        atomic_publish_directory_at(here, selected_stage.name, output.name, stage)
        published = True
    except BaseException as error:
        receipt.update(
            status="NOT_READY_S47_C2_FREEZE_OR_ATTACHMENT_FAILED",
            error_type=type(error).__name__,
            error=str(error),
            traceback=traceback.format_exc(),
            scientific_status="NOT_EVALUATED",
        )
        receipt["completed_utc"] = utc()
        receipt["source_unchanged_at_close"] = sha(SELF) == receipt["tool_source_sha256"]
        receipt["retry_permitted"] = False
        if stage is not None:
            target_name = "failure_receipt.json"
            if not entry_exists(stage, target_name):
                write_new_at(stage, target_name, receipt, mode=0o444)
            try:
                if stage.path == selected_stage:
                    require(not entry_exists(here, output.name),
                            "Fixed failed C2 attempt output is occupied")
                    atomic_publish_directory_at(here, selected_stage.name, output.name, stage)
                failure_record = str(output / target_name)
            except BaseException:
                failure_record = "HELD_ATTEMPT_INODE_UNPUBLISHED_AFTER_PATH_IDENTITY_FAILURE"
    finally:
        if stage is not None:
            stage.close()
        if prepare_lease is not None:
            prepare_lease.close()
        here.close()
    print(json.dumps({
        "status": receipt["status"],
        "completed_utc": receipt.get("completed_utc"),
        "receipt_written": receipt_written,
        "published": published,
        "failure_record": failure_record,
    }, ensure_ascii=False))
    return 0 if receipt["status"] in {
        "S47_C2_CORE_FROZEN_AWAITING_TWO_REVIEWS",
        "S47_C2_REVIEWS_ATTACHED_METADATA_GATE_PASSED",
    } else 2


if __name__ == "__main__":
    raise SystemExit(main())
