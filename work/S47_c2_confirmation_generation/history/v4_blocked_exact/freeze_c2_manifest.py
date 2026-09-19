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
FREEZE_PROTOCOL_SHA256 = "f5a4607218f3742467386822de5e1688c3838805ccac49609220729677ac55bd"
GATE = HERE / "generation_gate.py"
SOURCE_HASHES = {
    "generation_gate.py": "299f2f3212fe0b1c17dd35f2ac7c05ac851c43b42f6ae1327f8af60ae68aa264",
    "runtime_adapter.py": "6d11873b2a4d3cea231e30350a185c6771bed60dc03f68395b66127c93cc430e",
    "launch_generation.py": "e614aef6ca8a7d0ac82370a37cdf68f75e5f5b031c43c4dd15ffeab0eddfea0b",
    "create_launch_authorization.py": "0fc336853fc100e65b5cf1262bf40bffe68f42127ab1bc5196fe233e47bca05b",
    "PROTOCOL.md": "93b40a8e9d94b80cbfbd80d5da680ce417a010faac6b18649ed0f0f0e6d45031",
}
PREPARE_OUTPUT = HERE / "freeze_attempt_01"
ATTACH_OUTPUT = HERE / "review_attachment_01"
EXECUTION_OUTPUT = HERE / "execution_01"
PREPARE_STAGE = HERE / ".freeze_attempt_01.staging"
ATTACH_STAGE = HERE / ".review_attachment_01.staging"
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


def write_new(path, value, *, mode=None):
    path = Path(path)
    payload = json_bytes(value)
    with path.open("xb") as handle:
        handle.write(payload)
        if mode is not None:
            os.fchmod(handle.fileno(), mode)
        handle.flush()
        os.fsync(handle.fileno())
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def read_json(path, expected, label):
    path = Path(path)
    require(path.is_absolute(), label + " path must be absolute")
    payload, _ = verified_bytes(path, expected, label)
    return json.loads(payload)


def occupied(path):
    """Treat every directory entry, including a broken symlink, as occupied."""
    return os.path.lexists(os.fspath(path))


def require_atomic_directory_publisher():
    libc = ctypes.CDLL(None, use_errno=True)
    require(hasattr(libc, "renamex_np"), "macOS renamex_np is required for atomic publication")
    function = libc.renamex_np
    function.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
    function.restype = ctypes.c_int
    return function


def atomic_publish_directory(stage, destination, renamex_np):
    """Publish a complete directory without replacing any existing entry."""
    require(occupied(stage), "C2 staging directory disappeared before publication")
    require(not occupied(destination), "C2 publication destination is already occupied")
    rename_excl = 0x00000004
    result = renamex_np(os.fsencode(stage), os.fsencode(destination), rename_excl)
    if result != 0:
        number = ctypes.get_errno()
        raise OSError(number, os.strerror(number), os.fspath(destination))


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


def verify_unreviewed_core(gate, core, expected_sha):
    require(sha(PREPARE_OUTPUT / "manifest_core.json") == expected_sha,
            "Frozen C2 core file changed")
    expected = build_core(gate)
    expected["created_utc"] = core.get("created_utc")
    require(core == expected, "Frozen C2 core differs from the exact builder policy")
    require(core.get("review_receipts") == {}, "Unreviewed C2 core already has review bindings")
    require(
        core.get("freeze_preparation") == freeze_preparation_record(gate),
        "C2 freeze preparation identity differs",
    )
    return gate.core_sha256(core)


def prepare(args, gate, stage, output, receipt, core):
    require(output == PREPARE_OUTPUT, "Prepare output must be freeze_attempt_01")
    require_fresh_reserved(gate)
    core_path = stage / "manifest_core.json"
    write_new(core_path, core, mode=0o444)
    core_file_sha = sha(core_path)
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
    )


def build_attachment(args, gate):
    core_path = Path(args.core)
    require(core_path == PREPARE_OUTPUT / "manifest_core.json",
            "Attach requires the unique freeze_attempt_01 core")
    core = read_json(core_path, args.core_file_sha256, "C2 manifest core")
    core_sha = verify_unreviewed_core(gate, core, args.core_file_sha256)
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
    return final, core_sha


def preflight_attachment(args, gate):
    """Validate the exact future manifest without publishing an executable path."""
    final, core_sha = build_attachment(args, gate)
    manifest_sha = hashlib.sha256(json_bytes(final)).hexdigest()
    preflight_root = gate.ATTACH_PREFLIGHT_ROOT
    candidate = gate.ATTACH_PREFLIGHT_MANIFEST
    require(not occupied(preflight_root), "Fixed C2 attach-preflight lease is occupied")
    os.mkdir(preflight_root, mode=0o700)
    completed = False
    try:
        write_new(candidate, final, mode=0o444)
        require(sha(candidate) == manifest_sha, "C2 attachment candidate bytes differ")
        metadata = gate.check_attachment_preflight(candidate, manifest_sha)
        completed = True
    finally:
        if completed:
            os.unlink(candidate)
            os.rmdir(preflight_root)
    require(
        metadata.get("status") == "UNPUBLISHED_ATTACHMENT_PREFLIGHT_ONLY"
        and metadata.get("unpublished_attachment_check") is True
        and metadata.get("execution_authorized") is False,
        "C2 unpublished attachment metadata preflight failed",
    )
    return final, core_sha, manifest_sha, metadata


def attach(stage, output, gate, receipt, final, core_sha, manifest_sha, metadata):
    require(output == ATTACH_OUTPUT, "Attach output must be review_attachment_01")
    require_fresh_reserved(gate)
    manifest_path = stage / "manifest.json"
    metadata_path = stage / "metadata_gate.json"
    receipt_path = stage / "receipt.json"
    require(
        hashlib.sha256(json_bytes(final)).hexdigest() == manifest_sha,
        "C2 attachment bytes changed after preflight",
    )
    write_new(metadata_path, metadata, mode=0o444)
    receipt.update(
        status="S47_C2_REVIEWS_ATTACHED_METADATA_GATE_PASSED",
        manifest_path=str(gate.PUBLISHED_MANIFEST),
        manifest_sha256=manifest_sha,
        core_sha256=core_sha,
        review_receipts=copy.deepcopy(final["review_receipts"]),
        metadata_gate_status=metadata["status"],
        metadata_gate_path=str(gate.PUBLISHED_METADATA_GATE),
        metadata_gate_sha256=sha(metadata_path),
        model_or_scientific_imports=0,
        config_seed_derivation="EXACT_S40_BYTES_EXCEPT_UNIQUE_SEED_42_TO_44_PLUS_ONE_TERMINAL_LF",
        pixels_decoded=0,
        generation_calls=0,
        scientific_status="NOT_EVALUATED",
    )
    receipt["completed_utc"] = utc()
    receipt["source_unchanged_at_close"] = sha(SELF) == receipt["tool_source_sha256"]
    require(receipt["source_unchanged_at_close"], "C2 freeze tool changed before publication")
    require_fresh_reserved(gate)
    # The success receipt is still non-authoritative without the canonical
    # manifest.  Publishing the manifest is deliberately the final mutation.
    write_new(receipt_path, receipt, mode=0o444)
    require_fresh_reserved(gate)
    write_new(manifest_path, final, mode=0o444)


def validate_cli(args, output):
    attach_values = (
        args.core,
        args.core_file_sha256,
        args.core_sha256,
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
    parser.add_argument("--source-review")
    parser.add_argument("--source-review-sha256")
    parser.add_argument("--runtime-review")
    parser.add_argument("--runtime-review-sha256")
    args = parser.parse_args()
    output = Path(args.out)
    selected_stage = PREPARE_STAGE if args.mode == "prepare" else ATTACH_STAGE
    require(output.is_absolute(), "C2 freeze output must use its exact absolute path")
    receipt = {
        "schema": "s47-c2-freeze-tool-receipt-v1",
        "status": "CHECKING",
        "mode": args.mode,
        "started_utc": utc(),
        "tool_source_path": str(SELF),
        "tool_source_sha256": sha(SELF),
        "freeze_protocol_sha256": FREEZE_PROTOCOL_SHA256,
        "scientific_status": "NOT_EVALUATED",
    }
    stage = None
    published = False
    receipt_written = False
    failure_record = None
    try:
        # Complete every non-mutating command/source/parent/input/config review
        # before the sole protocol-compliant output directory can be consumed.
        validate_cli(args, output)
        require(not occupied(output), "C2 freeze output already exists")
        require(not occupied(selected_stage), "Fixed C2 freeze/attach staging lease is occupied")
        renamex_np = require_atomic_directory_publisher()
        gate = load_gate()
        require_fresh_reserved(gate)
        if args.mode == "prepare":
            prepared = build_core(gate)
        else:
            prepared = preflight_attachment(args, gate)
        require_fresh_reserved(gate)
        require(not occupied(output), "C2 freeze output was occupied during preflight")
        require(not occupied(selected_stage), "Fixed C2 freeze/attach staging lease was occupied during preflight")
        os.mkdir(selected_stage, mode=0o700)
        stage = selected_stage
        if args.mode == "prepare":
            prepare(args, gate, stage, output, receipt, prepared)
            receipt["completed_utc"] = utc()
            receipt["source_unchanged_at_close"] = sha(SELF) == receipt["tool_source_sha256"]
            require(receipt["source_unchanged_at_close"], "C2 freeze tool changed before receipt")
            write_new(stage / "receipt.json", receipt, mode=0o444)
            receipt_written = True
        else:
            attach(stage, output, gate, receipt, *prepared)
            receipt_written = True
        require_fresh_reserved(gate)
        require(not occupied(output), "C2 freeze output was occupied before atomic publication")
        atomic_publish_directory(stage, output, renamex_np)
        stage = None
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
        if stage is not None and occupied(stage):
            target = stage / "receipt.json"
            if occupied(target):
                target = stage / "failure_receipt.json"
            write_new(target, receipt, mode=0o444)
            try:
                require(not occupied(output), "Fixed failed C2 attempt output is occupied")
                atomic_publish_directory(stage, output, require_atomic_directory_publisher())
                stage = None
                failure_record = str(output / target.name)
            except BaseException:
                failure_record = str(target)
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
