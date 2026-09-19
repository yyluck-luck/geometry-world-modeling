#!/usr/bin/env python3
"""Create the unique S47 C2 launch authorization after two terminal reviews.

This standard-library tool never imports model code, opens the C2 input image,
or launches generation.  It validates the already published attachment and two
fixed-path, different-author reviews, writes a complete hidden staging file,
and publishes launch_authorization_01.json with macOS RENAME_EXCL.
"""
from __future__ import annotations

import argparse
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
GATE = HERE / "generation_gate.py"
GATE_SHA256 = "299f2f3212fe0b1c17dd35f2ac7c05ac851c43b42f6ae1327f8af60ae68aa264"
MANIFEST = HERE / "review_attachment_01/manifest.json"
AUTHORIZATION = HERE / "launch_authorization_01.json"
EXECUTION = HERE / "execution_01"
ATTEMPT = HERE / "launch_authorization_attempt_01"
ATTEMPT_STARTED = ATTEMPT / "attempt_started.json"
ATTEMPT_SUCCESS = ATTEMPT / "success_receipt.json"
ATTEMPT_FAILURE = ATTEMPT / "failure_receipt.json"
STAGE = ATTEMPT / "authorization.staging.json"


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


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


def occupied(path):
    return os.path.lexists(os.fspath(path))


def read_json(path, expected, label):
    path = Path(path)
    require(path.is_absolute(), label + " path must be absolute")
    payload, _ = verified_bytes(path, expected, label)
    return json.loads(payload)


def json_bytes(value):
    return (
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    ).encode("utf-8")


def write_new(path, payload):
    with Path(path).open("xb") as handle:
        handle.write(payload)
        os.fchmod(handle.fileno(), 0o444)
        handle.flush()
        os.fsync(handle.fileno())
    descriptor = os.open(Path(path).parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_publish_file(stage, destination):
    require(occupied(stage), "Authorization staging file disappeared")
    require(not occupied(destination), "launch_authorization_01.json is already occupied")
    libc = ctypes.CDLL(None, use_errno=True)
    require(hasattr(libc, "renamex_np"), "macOS renamex_np is required")
    renamex_np = libc.renamex_np
    renamex_np.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
    renamex_np.restype = ctypes.c_int
    result = renamex_np(os.fsencode(stage), os.fsencode(destination), 0x00000004)
    if result != 0:
        number = ctypes.get_errno()
        raise OSError(number, os.strerror(number), os.fspath(destination))
    descriptor = os.open(Path(destination).parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def load_gate(manifest):
    expected = manifest.get("source_identities", {}).get(str(GATE))
    require(expected == GATE_SHA256,
            "Manifest cannot choose a different C2 generation-gate verifier")
    payload, _ = verified_bytes(
        GATE, GATE_SHA256, "Independently pinned generation-gate source"
    )
    name = "_s47_c2_authorization_gate"
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
    return module


def require_formal_freshness(output_root):
    require(not occupied(AUTHORIZATION), "The fixed launch authorization is already occupied")
    require(not occupied(ATTEMPT), "The fixed authorization-attempt lease is already occupied")
    require(not occupied(EXECUTION), "C2 execution_01 is no longer fresh")
    require(not occupied(output_root), "C2 scientific output root is no longer fresh")


def attempt_identity():
    path_stat = os.stat(ATTEMPT, follow_symlinks=False)
    require(stat.S_ISDIR(path_stat.st_mode), "Authorization-attempt lease is redirected")
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(ATTEMPT, flags)
    try:
        opened = os.fstat(descriptor)
        require((path_stat.st_dev, path_stat.st_ino) == (opened.st_dev, opened.st_ino),
                "Authorization-attempt lease inode changed")
        return {"device": opened.st_dev, "inode": opened.st_ino}
    finally:
        os.close(descriptor)


def require_post_claim_freshness(output_root, identity):
    require(attempt_identity() == identity, "Authorization-attempt lease changed after claim")
    require(not occupied(AUTHORIZATION), "The fixed launch authorization is already occupied")
    require(not occupied(EXECUTION), "C2 execution_01 is no longer fresh")
    require(not occupied(output_root), "C2 scientific output root is no longer fresh")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--core-file-sha256", required=True)
    parser.add_argument("--core-sha256", required=True)
    parser.add_argument("--attachment-receipt-sha256", required=True)
    parser.add_argument("--metadata-gate-sha256", required=True)
    parser.add_argument("--final-attachment-review-sha256", required=True)
    parser.add_argument("--launch-readiness-review-sha256", required=True)
    args = parser.parse_args()
    lease_claimed = False
    identity = None
    output_root = None
    tool_source_sha = sha(SELF)
    try:
        manifest = read_json(MANIFEST, args.manifest_sha256, "Canonical C2 manifest")
        output_root = Path(manifest.get("output_root", ""))
        require(output_root.is_absolute(), "C2 output root is not absolute")
        require_formal_freshness(output_root)
        gate = load_gate(manifest)
        manifest = gate.read_frozen(MANIFEST, args.manifest_sha256)
        gate.require_published_attachment(MANIFEST, args.manifest_sha256, manifest)
        bindings, attachment_completed_utc = gate.launch_review_bindings(
            manifest, args.manifest_sha256
        )
        supplied = {
            "manifest_sha256": args.manifest_sha256,
            "core_file_sha256": args.core_file_sha256,
            "core_sha256": args.core_sha256,
            "attachment_receipt_sha256": args.attachment_receipt_sha256,
            "metadata_gate_sha256": args.metadata_gate_sha256,
        }
        require(supplied == bindings, "Caller launch bindings differ from the published bundle")

        review_hashes = {
            "final_attachment": args.final_attachment_review_sha256,
            "launch_readiness": args.launch_readiness_review_sha256,
        }
        review_documents = {
            kind: read_json(
                gate.FINAL_REVIEW_PATHS[kind], review_hashes[kind], kind + " review"
            )
            for kind in gate.FINAL_REVIEW_STATUSES
        }
        created_utc = datetime.now(timezone.utc).isoformat()
        document = gate.build_launch_authorization_document(
            bindings=bindings,
            attachment_completed_utc=attachment_completed_utc,
            review_documents=review_documents,
            review_hashes=review_hashes,
            created_utc=created_utc,
            tool_sha256=tool_source_sha,
        )

        # All read-only validation is complete. The first mutation claims the
        # fixed attempt forever; every later failure remains sealed under it.
        require_formal_freshness(output_root)
        os.mkdir(ATTEMPT, mode=0o700)
        lease_claimed = True
        identity = attempt_identity()
        started = {
            "schema": "s47-c2-authorization-attempt-start-v1",
            "status": "ATTEMPT_LEASE_CLAIMED",
            "attempt_path": str(ATTEMPT),
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "tool_source_sha256": tool_source_sha,
            "manifest_sha256": args.manifest_sha256,
            "retry_permitted": False,
        }
        write_new(ATTEMPT_STARTED, json_bytes(started))
        require_post_claim_freshness(output_root, identity)

        current_manifest = read_json(MANIFEST, args.manifest_sha256, "Canonical C2 manifest")
        require(current_manifest == manifest, "C2 manifest snapshot changed before authorization")
        require(sha(SELF) == tool_source_sha, "Authorization tool changed before publication")
        current_bindings, current_attachment_utc = gate.launch_review_bindings(
            manifest, args.manifest_sha256
        )
        require(
            current_bindings == bindings and current_attachment_utc == attachment_completed_utc,
            "C2 attachment changed before authorization",
        )
        for kind, path in gate.FINAL_REVIEW_PATHS.items():
            current_review = read_json(path, review_hashes[kind], kind + " review")
            require(current_review == review_documents[kind],
                    kind + " review snapshot changed before authorization")

        require(not occupied(STAGE), "Fixed authorization staging path is occupied")
        payload = json_bytes(document)
        write_new(STAGE, payload)
        staged, _ = verified_bytes(
            STAGE, hashlib.sha256(payload).hexdigest(), "Staged C2 authorization"
        )
        require(json.loads(staged) == document, "Staged authorization bytes differ")
        require_post_claim_freshness(output_root, identity)
        atomic_publish_file(STAGE, AUTHORIZATION)
        authorization_sha = sha(AUTHORIZATION)
        success = {
            "schema": "s47-c2-authorization-attempt-receipt-v1",
            "status": "AUTHORIZED_AND_ATTEMPT_SEALED",
            "attempt_path": str(ATTEMPT),
            "authorization_path": str(AUTHORIZATION),
            "authorization_sha256": authorization_sha,
            "tool_source_sha256": tool_source_sha,
            "manifest_sha256": args.manifest_sha256,
            "completed_utc": datetime.now(timezone.utc).isoformat(),
            "retry_permitted": False,
            "generation_calls": 0,
            "pixels_decoded": 0,
        }
        write_new(ATTEMPT_SUCCESS, json_bytes(success))
        print(json.dumps({
            "status": document["status"],
            "path": str(AUTHORIZATION),
            "sha256": authorization_sha,
            "attempt_receipt": str(ATTEMPT_SUCCESS),
            "created_utc": document["created_utc"],
            "generation_calls": 0,
            "pixels_decoded": 0,
        }, ensure_ascii=False))
        return 0
    except BaseException as error:
        if lease_claimed:
            failure = {
                "schema": "s47-c2-authorization-attempt-receipt-v1",
                "status": "AUTHORIZATION_ATTEMPT_FAILED_AND_SEALED",
                "attempt_path": str(ATTEMPT),
                "completed_utc": datetime.now(timezone.utc).isoformat(),
                "tool_source_sha256": tool_source_sha,
                "authorization_published": occupied(AUTHORIZATION),
                "stage_retained": occupied(STAGE),
                "error_type": type(error).__name__,
                "error": str(error),
                "traceback": traceback.format_exc(),
                "retry_permitted": False,
                "generation_calls": 0,
                "pixels_decoded": 0,
            }
            try:
                write_new(ATTEMPT_FAILURE, json_bytes(failure))
            except BaseException:
                pass
        raise


if __name__ == "__main__":
    raise SystemExit(main())
