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
GATE_SHA256 = "fc0365f93c57a70d6a73d614edaaee600a288617bb3ea2650f95fa7e87cb41ea"
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


def directory_flags():
    return (
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    )


class DirectoryLease:
    """Hold every ancestor directory identity across one authorization window."""

    def __init__(self, path, chain):
        self.path = Path(path)
        self.chain = chain
        self.fd = chain[-1][1]
        last = os.fstat(self.fd)
        self.identity = {"device": last.st_dev, "inode": last.st_ino}
        self.closed = False

    @classmethod
    def open(cls, path):
        path = Path(path)
        require(path.is_absolute(), "Authorization directory must be absolute")
        current = os.open("/", directory_flags())
        root = os.fstat(current)
        chain = [(Path("/"), current, root.st_dev, root.st_ino)]
        prefix = Path("/")
        try:
            for part in path.parts[1:]:
                following = os.open(part, directory_flags(), dir_fd=current)
                opened = os.fstat(following)
                require(stat.S_ISDIR(opened.st_mode), "Authorization ancestor is not a directory")
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
        require(not self.closed, "Authorization directory lease is closed")
        for path, descriptor, device, inode in self.chain:
            opened = os.fstat(descriptor)
            named = os.stat(path, follow_symlinks=False)
            require(
                stat.S_ISDIR(opened.st_mode) and stat.S_ISDIR(named.st_mode)
                and (opened.st_dev, opened.st_ino) == (device, inode)
                and (named.st_dev, named.st_ino) == (device, inode),
                "Authorization directory or ancestor changed: " + str(path),
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


def write_new_at(directory, name, document):
    directory.validate()
    payload = json_bytes(document)
    flags = (
        os.O_WRONLY | os.O_CREAT | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    )
    descriptor = os.open(name, flags, 0o600, dir_fd=directory.fd)
    try:
        view = memoryview(payload)
        while view:
            count = os.write(descriptor, view)
            require(count > 0, "Short authorization record write")
            view = view[count:]
        os.fchmod(descriptor, 0o444)
        os.fsync(descriptor)
        opened = os.fstat(descriptor)
        named = os.stat(name, dir_fd=directory.fd, follow_symlinks=False)
        require(
            stat.S_ISREG(opened.st_mode)
            and (opened.st_dev, opened.st_ino) == (named.st_dev, named.st_ino)
            and opened.st_size == len(payload),
            "Authorization record inode changed while its descriptor remained open",
        )
    finally:
        os.close(descriptor)
    os.fsync(directory.fd)
    return hashlib.sha256(payload).hexdigest()


def stage_authorization(attempt, document):
    payload = json_bytes(document)
    flags = (
        os.O_WRONLY | os.O_CREAT | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    )
    descriptor = os.open(STAGE.name, flags, 0o600, dir_fd=attempt.fd)
    try:
        view = memoryview(payload)
        while view:
            count = os.write(descriptor, view)
            require(count > 0, "Short staged authorization write")
            view = view[count:]
        os.fchmod(descriptor, 0o444)
        os.fsync(descriptor)
        opened = os.fstat(descriptor)
        named = os.stat(STAGE.name, dir_fd=attempt.fd, follow_symlinks=False)
        require(
            (opened.st_dev, opened.st_ino) == (named.st_dev, named.st_ino)
            and opened.st_size == len(payload),
            "Staged authorization entry differs from its held descriptor",
        )
        os.fsync(attempt.fd)
        return descriptor, payload
    except BaseException:
        os.close(descriptor)
        raise


def publish_staged_authorization(here, attempt, staged_fd):
    here.validate()
    attempt.validate()
    require(not entry_exists(here, AUTHORIZATION.name),
            "Fixed launch authorization is already occupied")
    libc = ctypes.CDLL(None, use_errno=True)
    require(hasattr(libc, "renameatx_np"), "macOS renameatx_np is required")
    function = libc.renameatx_np
    function.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    function.restype = ctypes.c_int
    result = function(
        attempt.fd, os.fsencode(STAGE.name), here.fd, os.fsencode(AUTHORIZATION.name), 0x00000004
    )
    if result != 0:
        number = ctypes.get_errno()
        raise OSError(number, os.strerror(number), str(AUTHORIZATION))
    os.fsync(attempt.fd)
    os.fsync(here.fd)
    opened = os.fstat(staged_fd)
    published = os.stat(AUTHORIZATION.name, dir_fd=here.fd, follow_symlinks=False)
    require(
        (opened.st_dev, opened.st_ino) == (published.st_dev, published.st_ino)
        and not entry_exists(attempt, STAGE.name),
        "Published authorization is not the still-held staged inode",
    )


def read_json(path, expected, label):
    path = Path(path)
    require(path.is_absolute(), label + " path must be absolute")
    payload, _ = verified_bytes(path, expected, label)
    return json.loads(payload)


def json_bytes(value):
    return (
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    ).encode("utf-8")


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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--core-file-sha256", required=True)
    parser.add_argument("--core-sha256", required=True)
    parser.add_argument("--prepare-receipt-sha256", required=True)
    parser.add_argument("--attachment-receipt-sha256", required=True)
    parser.add_argument("--metadata-gate-sha256", required=True)
    parser.add_argument("--final-attachment-review-sha256", required=True)
    parser.add_argument("--launch-readiness-review-sha256", required=True)
    args = parser.parse_args()
    lease_claimed = False
    terminal_success = False
    output_root = None
    tool_source_sha = sha(SELF)
    here = DirectoryLease.open(HERE)
    attempt = None
    staged_fd = None
    retained_controls = []
    retained_files = []
    result = None
    try:
        manifest = read_json(MANIFEST, args.manifest_sha256, "Canonical C2 manifest")
        output_root = Path(manifest.get("output_root", ""))
        require(output_root.is_absolute(), "C2 output root is not absolute")
        require_formal_freshness(output_root)
        gate = load_gate(manifest)
        manifest = gate.read_frozen(MANIFEST, args.manifest_sha256)
        attachment = gate.require_published_attachment(
            MANIFEST, args.manifest_sha256, manifest
        )
        bindings, attachment_completed_utc = gate.launch_review_bindings(
            manifest, args.manifest_sha256
        )
        supplied = {
            "manifest_sha256": args.manifest_sha256,
            "core_file_sha256": args.core_file_sha256,
            "core_sha256": args.core_sha256,
            "prepare_receipt_sha256": args.prepare_receipt_sha256,
            "attachment_receipt_sha256": args.attachment_receipt_sha256,
            "metadata_gate_sha256": args.metadata_gate_sha256,
        }
        require(supplied == bindings, "Caller launch bindings differ from the published bundle")
        prepared = gate.require_successful_prepare_bundle(
            core_file_sha256_value=bindings["core_file_sha256"],
            core_sha256_value=bindings["core_sha256"],
            receipt_sha256_value=bindings["prepare_receipt_sha256"],
        )

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

        # Hold the already verified prepare and attachment directory inodes
        # before the one irreversible authorization-attempt claim.
        retained_controls = [
            DirectoryLease.open(gate.PREPARE_ROOT),
            DirectoryLease.open(gate.ATTACHMENT_ROOT),
        ]
        require(retained_controls[0].entries() == {"manifest_core.json", "receipt.json"},
                "Prepared core terminal shape changed before authorization")
        require(retained_controls[1].entries()
                == {"manifest.json", "metadata_gate.json", "receipt.json"},
                "Attachment terminal shape changed before authorization")
        file_specs = {
            "manifest": (MANIFEST, bindings["manifest_sha256"]),
            "core": (gate.PREPARE_CORE, bindings["core_file_sha256"]),
            "prepare_receipt": (
                gate.PREPARE_RECEIPT, bindings["prepare_receipt_sha256"]
            ),
            "attachment_receipt": (
                gate.PUBLISHED_RECEIPT, bindings["attachment_receipt_sha256"]
            ),
            "metadata_gate": (
                gate.PUBLISHED_METADATA_GATE, bindings["metadata_gate_sha256"]
            ),
            "prepare_sentinel": (
                gate.PREPARE_SENTINEL,
                prepared["receipt"]["attempt_sentinel"]["sha256"],
            ),
            "attach_sentinel": (
                gate.ATTACH_SENTINEL, attachment["attempt_sentinel_sha256"]
            ),
            "authorization_tool": (SELF, tool_source_sha),
        }
        for kind, path in gate.FINAL_REVIEW_PATHS.items():
            file_specs["terminal_review_" + kind] = (path, review_hashes[kind])
        for name, (path, digest) in file_specs.items():
            retained_files.append(
                gate.RegularBinding(path, digest, "Authorization-held C2 " + name)
            )
        require_formal_freshness(output_root)
        here.validate()
        require(not entry_exists(here, ATTEMPT.name)
                and not entry_exists(here, AUTHORIZATION.name),
                "Authorization single-attempt names are occupied")
        os.mkdir(ATTEMPT.name, mode=0o700, dir_fd=here.fd)
        lease_claimed = True
        attempt = DirectoryLease.open(ATTEMPT)
        started = {
            "schema": "s47-c2-authorization-attempt-start-v2",
            "status": "ATTEMPT_LEASE_CLAIMED",
            "attempt_path": str(ATTEMPT),
            "attempt_identity": dict(attempt.identity),
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "tool_source_sha256": tool_source_sha,
            "manifest_sha256": args.manifest_sha256,
            "retry_permitted": False,
        }
        started_sha = write_new_at(attempt, ATTEMPT_STARTED.name, started)

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
        for control in retained_controls:
            control.validate()
        for control_file in retained_files:
            control_file.validate()
        attempt.validate()
        here.validate()
        require(not entry_exists(here, AUTHORIZATION.name)
                and not occupied(EXECUTION) and not occupied(output_root),
                "Later formal path appeared during authorization")

        require(not entry_exists(attempt, STAGE.name),
                "Fixed authorization staging name is occupied")
        staged_fd, payload = stage_authorization(attempt, document)
        authorization_sha = hashlib.sha256(payload).hexdigest()
        for control in retained_controls:
            control.validate()
        for control_file in retained_files:
            control_file.validate()
        publish_staged_authorization(here, attempt, staged_fd)
        published = os.fstat(staged_fd)
        authorization_identity = {
            "device": published.st_dev,
            "inode": published.st_ino,
            "size": published.st_size,
            "mode": stat.S_IMODE(published.st_mode),
        }
        require(
            hashlib.sha256(payload).hexdigest() == authorization_sha
            and (published.st_mode & 0o222) == 0,
            "Held authorization bytes or mode changed at publication",
        )
        success = {
            "schema": "s47-c2-authorization-attempt-receipt-v2",
            "status": "AUTHORIZED_AND_ATTEMPT_SEALED",
            "attempt_path": str(ATTEMPT),
            "attempt_identity": dict(attempt.identity),
            "attempt_started_sha256": started_sha,
            "authorization_path": str(AUTHORIZATION),
            "authorization_sha256": authorization_sha,
            "authorization_identity": authorization_identity,
            "tool_source_sha256": tool_source_sha,
            "manifest_sha256": args.manifest_sha256,
            "completed_utc": datetime.now(timezone.utc).isoformat(),
            "retry_permitted": False,
            "generation_calls": 0,
            "pixels_decoded": 0,
            "terminal_shape": ["attempt_started.json", "success_receipt.json"],
            "terminal_success": True,
        }
        write_new_at(attempt, ATTEMPT_SUCCESS.name, success)
        require(attempt.entries() == {"attempt_started.json", "success_receipt.json"},
                "Authorization success lease has an ambiguous terminal shape")
        attempt.validate()
        here.validate()
        for control in retained_controls:
            control.validate()
        for control_file in retained_files:
            control_file.validate()
        canonical_authorization = os.stat(
            AUTHORIZATION.name, dir_fd=here.fd, follow_symlinks=False
        )
        require(
            stat.S_ISREG(canonical_authorization.st_mode)
            and {
                "device": canonical_authorization.st_dev,
                "inode": canonical_authorization.st_ino,
                "size": canonical_authorization.st_size,
                "mode": stat.S_IMODE(canonical_authorization.st_mode),
            }
            == authorization_identity,
            "Canonical authorization changed before the success terminal seal",
        )
        terminal_success = True
        result = {
            "status": document["status"],
            "path": str(AUTHORIZATION),
            "sha256": authorization_sha,
            "attempt_receipt": str(ATTEMPT_SUCCESS),
            "created_utc": document["created_utc"],
            "generation_calls": 0,
            "pixels_decoded": 0,
        }
    except BaseException as error:
        if lease_claimed and not terminal_success and attempt is not None:
            failure = {
                "schema": "s47-c2-authorization-attempt-receipt-v2",
                "status": "AUTHORIZATION_ATTEMPT_FAILED_AND_SEALED",
                "attempt_path": str(ATTEMPT),
                "attempt_identity": dict(attempt.identity),
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
                if not entry_exists(attempt, ATTEMPT_FAILURE.name):
                    write_new_at(attempt, ATTEMPT_FAILURE.name, failure)
            except BaseException:
                pass
        raise
    finally:
        if staged_fd is not None:
            os.close(staged_fd)
        if attempt is not None:
            attempt.close()
        for control_file in retained_files:
            control_file.close()
        for control in retained_controls:
            control.close()
        here.close()
    # Reporting happens after the terminal success region. A broken stdout
    # cannot create a contradictory failure receipt beside success.
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
