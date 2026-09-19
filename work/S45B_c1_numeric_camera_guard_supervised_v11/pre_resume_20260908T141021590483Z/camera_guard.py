#!/usr/bin/env python3
"""Supervised C1 numeric requested-camera worker; source-only until reviewed.

The formal worker can read archive/event metadata and only the small c2w/K
tensor bodies selected from two batch_input and two cache_commit captures.  It
can publish only pending worker evidence.  The separately reviewed supervisor
is the sole source allowed to publish a terminal PASS seal after process-exit,
resource, no-fork containment, durability, and identity checks.  The canonical
candidate remains pending-only; terminal truth is an exact exit-gated supervisor
stdout record.  Neither source opens
pixels, PIL/PNG bodies, models, renderers, or generation code.
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import fcntl
import hashlib
import hmac
import json
import math
import os
from pathlib import Path
import re
import stat
import struct
import time
import traceback


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SELF = Path(__file__).resolve()
PROTOCOL = HERE / "PROTOCOL.md"
PROTOCOL_SHA256 = "7b369639c4558535fa9fbe239d23a153347776201c75ef18b2704e4b450a7c06"
BINDING_TEMPLATE = HERE / "C1_CAMERA_GUARD_BINDING_TEMPLATE.json"
BINDING_TEMPLATE_SHA256 = "a55d4a62ecc1fd151167b2ed76289a660255bbefae6cd3a5f313e7d05eb3e593"
SELFTEST = HERE / "synthetic_selftest.py"
SELFTEST_SHA256 = "d65a6ed11dba59237d8d82e70e6bbb6e6ef914e5ed918bd7af775a36cbdf02b4"
SUPERVISOR = HERE / "supervise_camera_guard.py"
BINDING = HERE / "C1_CAMERA_GUARD_BINDING_V11.json"
BINDING_REVIEW = HERE / "BINDING_REVIEW_V11.json"
SOURCE_REVIEW_PRIMARY = HERE / "SOURCE_REVIEW_PRIMARY_V11.json"
SOURCE_REVIEW_ADVERSARIAL = HERE / "SOURCE_REVIEW_ADVERSARIAL_V11.json"
GOVERNANCE_ATTESTATION = HERE / "GOVERNANCE_ATTESTATION_V11.json"
FORMAL_OUT = HERE / "execution_01"
LOCK = HERE / ".c1_numeric_camera_guard.lock"
LOCK_STAGING = HERE / ".c1_numeric_camera_guard.lock.staging"
REPORT_NAME = "report.json"
WORKER_RECEIPT_NAME = "worker_receipt.json"
WORKER_FAILURE_NAME = "worker_postwrite_failure.json"
SUPERVISOR_RECEIPT_NAME = "supervisor_receipt.json"
BARRIER_NAME = "terminalization_barrier.json"
TERMINAL_SEAL_NAME = "terminal_pass_candidate.json"
TERMINAL_SEAL_STAGING_NAME = ".terminal_pass_candidate.staging"
TERMINAL_FAILURE_NAME = "terminal_seal_failure.json"

S42 = ROOT / "work/S42_baseline_failure_preregistration"
S42_PROTOCOL = S42 / "PROTOCOL.md"
S42_PROTOCOL_SHA256 = "89fb44e0b77a85a66fe611cd2f885fed0288229cbb027e04da25fc0631507b3f"
B0_REFERENCE = S42 / "score_b0_blind.py"
B0_REFERENCE_SHA256 = "f36be25001f5138bd985ca186d49c6d44e66b5b9c599b8c0dfc6e8691a4719de"
B0_CONTRACT_SHA256 = "1143f700855ab32df3d703fc91b2ff8707ca3dc3e217407156be9247d677c11b"
B0_PRIMARY_REVIEW = S42 / "B0_SCORER_SOURCE_REVIEW.json"
B0_PRIMARY_REVIEW_SHA256 = "befb1af9c498a1423320cbd59011c56bdd4218ac56b4bb63667f4696b31184b0"
B0_ADVERSARIAL_REVIEW = S42 / "B0_SCORER_SOURCE_REVIEW_ADVERSARIAL.json"
B0_ADVERSARIAL_REVIEW_SHA256 = "a2874380d0cd62c68a1c9e5749d55bc6af37d47efde5726315db80c8d3b0abeb"
B0_MAX_ABS_SOURCE_SHA256 = "5b19516bcaa6d650b7259d4e806266ab40762a358989190f2d3327fbaceb3fd4"
B0_CAMERA_SOURCE_SHA256 = "7dfa29e4bdaca569cf485b8c575f1d48f5dbcabb61011f6ab1998fea79b9a8e3"

S44 = ROOT / "work/S44_c1_confirmation_generation"
C1_EXECUTION = S44 / "execution_01"
C1_OUTPUT = ROOT / "results/S44_C1_confirmation_generation"
C1_MANIFEST = S44 / "review_attachment_01/manifest.json"
C1_MANIFEST_SHA256 = "1e86e8279c608995a03d6675a8636c354d6d4d046b7c8faea9611d6e6a9fd93b"
C1_GENERATION_RECEIPT = C1_EXECUTION / "receipt.json"
C1_GENERATION_WORKER_RECEIPT = C1_EXECUTION / "worker_receipt.json"
C1_ARCHIVE_MANIFEST = C1_OUTPUT / "archive/manifest.json"
C1_ARCHIVE_EVENTS = C1_OUTPUT / "archive/events.jsonl"

S45 = ROOT / "work/S45_c1_result_readback"
S45_READBACK_SOURCE = S45 / "readback.py"
S45_READBACK_SOURCE_SHA256 = "0ec8eda2e89553a201ec274144038ec79f9c3cbb751ebe30ec1d619c8145a2ab"
S45_SUPERVISOR_SOURCE = S45 / "supervise_readback.py"
S45_SUPERVISOR_SOURCE_SHA256 = "825396fc5ac69ac210a6fc6021171543c830c6906bf2f9d0cf6e44ef75c23d78"
S45_TERMINAL_BINDING = S45 / "terminal_binding_01.json"
S45_SUPERVISOR_RECEIPT = S45 / "supervision_01/receipt.json"
S45_WORKER_RECEIPT = S45 / "executed_01/receipt.json"
S45_REPORT = S45 / "executed_01/report.json"
S45_RESULT_REVIEW = S45 / "supervision_01/independent_result_review.json"
S45_RESULT_REVIEW_SHA256 = "2b5e4bc3dcf28f60b320ae4d3af2b4949b60a526cacc62b2deacd87ac6ddad4c"

EXPECTED_YAW = (0.0, 1.25, 2.5, 3.75, 5.0, 3.75, 2.5, 1.25, 0.0)
TOLERANCE = 1e-6
SECONDS = 300
MAX_CAMERA_TENSOR_BYTES = 4096
HEX = re.compile(r"^[0-9a-f]{64}$")
AUTHOR_ROLE = "/root/c2_v5_lifecycle_review"
WIDTHS = {"float32": 4, "float64": 8}
ARTIFACT_AUTH_DOMAIN = b"S45B-C1-V11-PREBOUND-ARTIFACT"


class GuardInvalid(ValueError):
    """The requested c2w/K condition fails a frozen numeric validity guard."""


class TensorDescriptor(dict):
    """Marker created only from a raw archive kind=tensor node."""


def require(value, message):
    if not value:
        raise ValueError(message)


def require_guard(value, message):
    if not value:
        raise GuardInvalid(message)


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def encoded_json(value):
    return (
        json.dumps(
            value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False,
        ) + "\n"
    ).encode("utf-8")


def artifact_auth_tag(secret, artifact_name, value_without_tag):
    """Authenticate complete evidence over the private parent/child capability.

    The capability bytes never enter argv or a filesystem artifact.  The public
    capability SHA remains in the permanent lock, while this HMAC prevents a
    same-user pathname replacement from constructing a new accepted document.
    """
    require(type(secret) is bytes and len(secret) == 32,
            "Artifact authentication secret must be exactly 32 bytes")
    require(artifact_name in (REPORT_NAME, WORKER_RECEIPT_NAME),
            "Artifact authentication domain is unknown")
    require(type(value_without_tag) is dict
            and "artifact_authentication_hmac_sha256" not in value_without_tag,
            "Artifact authentication input must omit its tag")
    message = (
        ARTIFACT_AUTH_DOMAIN + b"\0" + artifact_name.encode("ascii")
        + b"\0" + canonical(value_without_tag)
    )
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


def prebound_identity(value):
    return (value.st_dev, value.st_ino, value.st_mode)


def verify_prebound_artifact(output_fd, name, fd, identity, require_empty=False):
    """Verify one supervisor-created output without reopening it by pathname."""
    require(name in (REPORT_NAME, WORKER_RECEIPT_NAME),
            "Prebound artifact name is outside the worker write scope")
    require(type(fd) is int and fd >= 3 and type(identity) is tuple
            and len(identity) == 3, "Prebound artifact descriptor is malformed")
    held = os.fstat(fd)
    named = os.stat(name, dir_fd=output_fd, follow_symlinks=False)
    require(
        stat.S_ISREG(held.st_mode) and stat.S_ISREG(named.st_mode)
        and held.st_nlink == named.st_nlink == 1
        and prebound_identity(held) == identity
        and prebound_identity(named) == identity,
        "Prebound artifact pathname/inode/mode binding changed: " + name,
    )
    if require_empty:
        require(held.st_size == named.st_size == 0 and os.pread(fd, 1, 0) == b"",
                "Prebound artifact is not empty before worker publication: " + name)
    return held


def write_prebound_json(output_fd, name, fd, identity, value, secret):
    """Publish authenticated JSON only through a supervisor-created held FD."""
    verify_prebound_artifact(output_fd, name, fd, identity, require_empty=True)
    unsigned = dict(value)
    require("artifact_authentication_hmac_sha256" not in unsigned,
            "Prebound document already contains an authentication tag")
    signed = dict(unsigned)
    signed["artifact_authentication_hmac_sha256"] = artifact_auth_tag(
        secret, name, unsigned,
    )
    body = encoded_json(signed)
    write_all(fd, body)
    os.fsync(fd)
    held = verify_prebound_artifact(output_fd, name, fd, identity)
    require(held.st_size == len(body) and os.pread(fd, len(body), 0) == body
            and os.pread(fd, 1, len(body)) == b"",
            "Prebound artifact bytes differ after publication: " + name)
    return hashlib.sha256(body).hexdigest(), body


def verify_inherited_worker_source(fd, identity, expected_sha256, expected_bytes):
    """Bind the executing in-memory code to the still-held reviewed source FD."""
    require(type(fd) is int and fd >= 3 and type(identity) is tuple
            and len(identity) == 3 and HEX.fullmatch(expected_sha256 or "") is not None
            and type(expected_bytes) is int and expected_bytes > 0,
            "Inherited worker-source binding is malformed")
    held = os.fstat(fd)
    named = os.stat(SELF, follow_symlinks=False)
    require(
        stat.S_ISREG(held.st_mode) and stat.S_ISREG(named.st_mode)
        and held.st_nlink == named.st_nlink == 1
        and prebound_identity(held) == identity
        and prebound_identity(named) == identity
        and held.st_size == named.st_size == expected_bytes,
        "Inherited worker source FD/path identity changed",
    )
    digest = hashlib.sha256()
    offset = 0
    while offset < expected_bytes:
        block = os.pread(fd, min(1024 * 1024, expected_bytes - offset), offset)
        require(bool(block), "Inherited worker source ended early")
        digest.update(block)
        offset += len(block)
    require(os.pread(fd, 1, expected_bytes) == b""
            and digest.hexdigest() == expected_sha256,
            "Inherited worker source bytes differ from reviewed bytes")
    return {
        "sha256": expected_sha256,
        "bytes": expected_bytes,
        "device": held.st_dev,
        "inode": held.st_ino,
        "mode": held.st_mode,
    }


def utc():
    return datetime.now(timezone.utc).isoformat()


def parse_utc(value, label):
    require(type(value) is str and bool(value), label + " must be a nonempty timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(label + " is not ISO-8601") from error
    require(parsed.tzinfo is not None and parsed.utcoffset() == timezone.utc.utcoffset(parsed),
            label + " must be timezone-aware UTC")
    return parsed


def lexists(path):
    return os.path.lexists(os.fspath(path))


def stat_identity(value):
    return (
        value.st_dev, value.st_ino, value.st_mode, value.st_size,
        value.st_mtime_ns, value.st_ctime_ns,
    )


def file_snapshot(path, expected_sha256=None, deadline=None, max_bytes=None):
    path = Path(path)
    require(path.is_absolute() and path.resolve() == path, "Identity path is not canonical: " + str(path))
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        before = os.fstat(fd)
        path_before = os.stat(path, follow_symlinks=False)
        require(
            stat.S_ISREG(before.st_mode) and stat.S_ISREG(path_before.st_mode)
            and stat_identity(before) == stat_identity(path_before),
            "Identity is not one stable regular non-symlink file: " + str(path),
        )
        require(max_bytes is None or before.st_size <= max_bytes,
                "Identity exceeds bounded snapshot scope: " + str(path))
        digest = hashlib.sha256()
        pieces = []
        count = 0
        while count < before.st_size:
            if deadline is not None:
                require(time.monotonic() <= deadline, "C1 camera guard time limit reached")
            block = os.pread(fd, min(8 * 1024 * 1024, before.st_size - count), count)
            require(bool(block), "Identity has unexpected EOF: " + str(path))
            digest.update(block)
            pieces.append(block)
            count += len(block)
        require(os.pread(fd, 1, before.st_size) == b"", "Identity grew during snapshot: " + str(path))
        after = os.fstat(fd)
        path_after = os.stat(path, follow_symlinks=False)
        require(
            stat_identity(before) == stat_identity(after)
            and stat_identity(before) == stat_identity(path_after)
            and count == before.st_size,
            "Identity changed while snapshotting: " + str(path),
        )
        value = digest.hexdigest()
        require(expected_sha256 is None or value == expected_sha256,
                "SHA-256 differs: " + str(path))
        return b"".join(pieces), {
            "path": str(path), "sha256": value, "bytes": count,
            "stat": list(stat_identity(before)),
        }
    finally:
        os.close(fd)


def file_record(path, expected_sha256=None, deadline=None):
    _, record = file_snapshot(path, expected_sha256, deadline)
    return record


def read_json(path, expected_sha256, label, deadline=None):
    require(HEX.fullmatch(expected_sha256 or "") is not None,
            label + " SHA-256 is not lowercase hexadecimal")
    raw, record = file_snapshot(
        path, expected_sha256, deadline, max_bytes=256 * 1024 * 1024,
    )
    doc = json.loads(raw.decode("utf-8"))
    return doc, record


def function_source_sha(source_bytes, tree, name):
    found = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    require(len(found) == 1, "Reviewed B0 function is missing or duplicated: " + name)
    node = found[0]
    require(type(node.lineno) is int and type(node.end_lineno) is int,
            "Reviewed B0 function lacks exact source bounds: " + name)
    lines = source_bytes.splitlines(keepends=True)
    require(1 <= node.lineno <= node.end_lineno <= len(lines),
            "Reviewed B0 function source bounds differ: " + name)
    return hashlib.sha256(b"".join(lines[node.lineno - 1:node.end_lineno])).hexdigest()


def top_level_literal(tree, name):
    found = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id == name:
                found.append(ast.literal_eval(node.value))
    require(len(found) == 1, "Reviewed B0 constant is missing or duplicated: " + name)
    return found[0]


def verify_static_reference(self_sha256, supervisor_sha256, deadline):
    require(HEX.fullmatch(self_sha256 or "") is not None, "Runner SHA-256 must be lowercase hexadecimal")
    require(HEX.fullmatch(supervisor_sha256 or "") is not None,
            "Supervisor SHA-256 must be lowercase hexadecimal")
    fixed = {
        SELF: self_sha256,
        SUPERVISOR: supervisor_sha256,
        PROTOCOL: PROTOCOL_SHA256,
        BINDING_TEMPLATE: BINDING_TEMPLATE_SHA256,
        SELFTEST: SELFTEST_SHA256,
        S42_PROTOCOL: S42_PROTOCOL_SHA256,
        B0_REFERENCE: B0_REFERENCE_SHA256,
        B0_PRIMARY_REVIEW: B0_PRIMARY_REVIEW_SHA256,
        B0_ADVERSARIAL_REVIEW: B0_ADVERSARIAL_REVIEW_SHA256,
        S45_READBACK_SOURCE: S45_READBACK_SOURCE_SHA256,
        S45_SUPERVISOR_SOURCE: S45_SUPERVISOR_SOURCE_SHA256,
    }
    records = {}
    snapshots = {}
    for path, digest in fixed.items():
        snapshots[path], records[str(path)] = file_snapshot(path, digest, deadline)
    b0_source = snapshots[B0_REFERENCE]
    tree = ast.parse(b0_source.decode("utf-8"), filename=str(B0_REFERENCE))
    require(function_source_sha(b0_source, tree, "max_abs") == B0_MAX_ABS_SOURCE_SHA256,
            "Reviewed B0 max_abs source segment differs")
    require(function_source_sha(b0_source, tree, "verify_requested_camera_conditions")
            == B0_CAMERA_SOURCE_SHA256,
            "Reviewed B0 camera-guard source segment differs")
    require(tuple(top_level_literal(tree, "EXPECTED_YAW")) == EXPECTED_YAW,
            "Reviewed B0 yaw sequence differs")
    require(top_level_literal(tree, "POSE_K_TOLERANCE") == TOLERANCE,
            "Reviewed B0 pose/K tolerance differs")
    primary, _ = read_json(B0_PRIMARY_REVIEW, B0_PRIMARY_REVIEW_SHA256, "B0 primary review", deadline)
    adversarial, _ = read_json(
        B0_ADVERSARIAL_REVIEW, B0_ADVERSARIAL_REVIEW_SHA256,
        "B0 adversarial review", deadline,
    )
    require(
        primary.get("schema") == "s42-b0-blind-scorer-source-review-v1"
        and primary.get("status") == "PASS_S42_B0_BLIND_SCORER_SOURCE_REVIEW"
        and primary.get("scorer_sha256") == B0_REFERENCE_SHA256
        and primary.get("contract_sha256") == B0_CONTRACT_SHA256
        and primary.get("preregistration_protocol_sha256") == S42_PROTOCOL_SHA256
        and primary.get("executed") is False
        and primary.get("s40_generated_images_viewed") is False
        and primary.get("s40_result_arrays_decoded") is False
        and primary.get("blocking_findings") == [],
        "Reviewed B0 primary source review no longer has its narrow PASS",
    )
    require(
        adversarial.get("schema") == "s42-b0-blind-scorer-adversarial-source-review-v1"
        and adversarial.get("status") == "PASS_S42_B0_BLIND_SCORER_ADVERSARIAL_SOURCE_REVIEW"
        and adversarial.get("scorer_sha256") == B0_REFERENCE_SHA256
        and adversarial.get("contract_sha256") == B0_CONTRACT_SHA256
        and adversarial.get("preregistration_protocol_sha256") == S42_PROTOCOL_SHA256
        and adversarial.get("executed") is False
        and adversarial.get("s40_generated_images_viewed") is False
        and adversarial.get("s40_result_arrays_decoded") is False
        and adversarial.get("blocking_findings") == [],
        "Reviewed B0 adversarial source review no longer has its narrow PASS",
    )
    return records


def expected_source_review_identities(self_sha256, supervisor_sha256):
    return {
        "camera_guard.py": self_sha256,
        "supervise_camera_guard.py": supervisor_sha256,
        "PROTOCOL.md": PROTOCOL_SHA256,
        "C1_CAMERA_GUARD_BINDING_TEMPLATE.json": BINDING_TEMPLATE_SHA256,
        "synthetic_selftest.py": SELFTEST_SHA256,
        "s42_baseline_protocol": S42_PROTOCOL_SHA256,
        "b0_camera_reference": B0_REFERENCE_SHA256,
        "b0_primary_source_review": B0_PRIMARY_REVIEW_SHA256,
        "b0_adversarial_source_review": B0_ADVERSARIAL_REVIEW_SHA256,
        "s45_readback_source": S45_READBACK_SOURCE_SHA256,
        "s45_supervisor_source": S45_SUPERVISOR_SOURCE_SHA256,
        "s45_result_review_expected": S45_RESULT_REVIEW_SHA256,
    }


def verify_source_reviews(args, started_utc, deadline):
    expected = expected_source_review_identities(
        args.self_sha256, args.supervisor_sha256,
    )
    reviews = []
    records = {}
    for path, digest, kind in (
        (SOURCE_REVIEW_PRIMARY, args.primary_source_review_sha256, "primary"),
        (SOURCE_REVIEW_ADVERSARIAL, args.adversarial_source_review_sha256, "adversarial"),
    ):
        review, record = read_json(path, digest, kind + " camera-guard source review", deadline)
        require(
            review.get("schema") == "s45b-c1-numeric-camera-guard-source-review-v4"
            and review.get("review_kind") == kind
            and review.get("status") == "PASS_S45B_C1_NUMERIC_CAMERA_GUARD_SUPERVISED_SOURCE_REVIEW_V11"
            and review.get("verdict") == "PASS_SUPERVISED_SOURCE_NOT_EXECUTED"
            and review.get("reviewed_identities") == expected
            and review.get("author_role") == AUTHOR_ROLE
            and type(review.get("reviewer_role")) is str and bool(review["reviewer_role"])
            and type(review.get("reviewer_task_id")) is str and bool(review["reviewer_task_id"])
            and type(review.get("reviewer_turn_id")) is str and bool(review["reviewer_turn_id"])
            and review.get("executed") is False
            and review.get("c1_tensor_bodies_read") == 0
            and review.get("pixels_decoded") == 0
            and review.get("images_viewed") == 0
            and review.get("blocking_findings") == [],
            "C1 camera-guard source review is incomplete or belongs to another source set",
        )
        completed = parse_utc(review.get("completed_utc"), kind + " source review completed_utc")
        require(completed <= started_utc, "Source review occurs after formal guard start")
        reviews.append(review)
        records[str(path)] = record
    roles = [AUTHOR_ROLE] + [review["reviewer_role"] for review in reviews]
    require(len(set(roles)) == 3, "Guard author and two source reviewers must be pairwise distinct")
    require(len({review["reviewer_task_id"] for review in reviews}) == 2,
            "Source-review task identities must be distinct")
    return reviews, records


def fixed_upstream_paths():
    return {
        "generation_manifest": C1_MANIFEST,
        "generation_terminal_receipt": C1_GENERATION_RECEIPT,
        "generation_worker_receipt": C1_GENERATION_WORKER_RECEIPT,
        "s45_terminal_binding": S45_TERMINAL_BINDING,
        "s45_supervisor_receipt": S45_SUPERVISOR_RECEIPT,
        "s45_worker_receipt": S45_WORKER_RECEIPT,
        "s45_report": S45_REPORT,
        "s45_result_review": S45_RESULT_REVIEW,
        "archive_manifest": C1_ARCHIVE_MANIFEST,
        "archive_events": C1_ARCHIVE_EVENTS,
    }


def verify_binding(args, source_reviews, started_utc, deadline):
    require(BINDING != BINDING_TEMPLATE, "Executable binding must differ from the template")
    binding, binding_record = read_json(BINDING, args.binding_sha256, "C1 camera-guard binding", deadline)
    expected_source_set = {
        "camera_guard.py": args.self_sha256,
        "supervise_camera_guard.py": args.supervisor_sha256,
        "PROTOCOL.md": PROTOCOL_SHA256,
        "C1_CAMERA_GUARD_BINDING_TEMPLATE.json": BINDING_TEMPLATE_SHA256,
        "synthetic_selftest.py": SELFTEST_SHA256,
        "primary_source_review": args.primary_source_review_sha256,
        "adversarial_source_review": args.adversarial_source_review_sha256,
    }
    require(
        binding.get("schema") == "s45b-c1-numeric-camera-guard-binding-v4"
        and binding.get("status") == "FROZEN_C1_NUMERIC_CAMERA_GUARD_SUPERVISED_INPUT_BINDING_V11"
        and binding.get("row") == "C1"
        and binding.get("placeholder_hashes") == 0
        and binding.get("source_set") == expected_source_set
        and type(binding.get("author_role")) is str and bool(binding["author_role"])
        and type(binding.get("author_task_id")) is str and bool(binding["author_task_id"])
        and type(binding.get("author_turn_id")) is str and bool(binding["author_turn_id"]),
        "C1 camera-guard binding is incomplete, pending, or belongs to another source set",
    )
    upstream = binding.get("upstream")
    require(type(upstream) is dict and set(upstream) == set(fixed_upstream_paths()),
            "C1 camera-guard binding has the wrong upstream identity domain")
    for name, fixed_path in fixed_upstream_paths().items():
        item = upstream.get(name)
        require(
            type(item) is dict and set(item) == {"path", "sha256"}
            and item.get("path") == str(fixed_path)
            and HEX.fullmatch(item.get("sha256", "")) is not None,
            "Malformed or noncanonical upstream binding: " + name,
        )
    require(upstream["generation_manifest"]["sha256"] == C1_MANIFEST_SHA256,
            "Binding names another C1 manifest")
    require(upstream["s45_result_review"]["sha256"] == S45_RESULT_REVIEW_SHA256,
            "Binding names another S45 independent result review")
    created = parse_utc(binding.get("created_utc"), "camera-guard binding created_utc")
    source_times = [parse_utc(review["completed_utc"], "source review completed_utc") for review in source_reviews]
    require(max(source_times) <= created <= started_utc,
            "Camera-guard binding must follow both source reviews and precede execution")

    binding_review, review_record = read_json(
        BINDING_REVIEW, args.binding_review_sha256, "C1 camera-guard binding review", deadline,
    )
    expected_reviewed = {
        "camera_guard.py": args.self_sha256,
        "supervise_camera_guard.py": args.supervisor_sha256,
        "PROTOCOL.md": PROTOCOL_SHA256,
        "C1_CAMERA_GUARD_BINDING_TEMPLATE.json": BINDING_TEMPLATE_SHA256,
        "synthetic_selftest.py": SELFTEST_SHA256,
        "primary_source_review": args.primary_source_review_sha256,
        "adversarial_source_review": args.adversarial_source_review_sha256,
        "C1_CAMERA_GUARD_BINDING_V11.json": args.binding_sha256,
        **{name: item["sha256"] for name, item in upstream.items()},
    }
    require(
        binding_review.get("schema") == "s45b-c1-numeric-camera-guard-binding-review-v4"
        and binding_review.get("status") == "PASS_S45B_C1_NUMERIC_CAMERA_GUARD_SUPERVISED_BINDING_REVIEW_V11"
        and binding_review.get("verdict") == "PASS_SUPERVISED_BINDING_ONLY_NO_TENSOR_BODIES"
        and binding_review.get("reviewed_identities") == expected_reviewed
        and binding_review.get("author_role") == binding["author_role"]
        and type(binding_review.get("reviewer_role")) is str
        and bool(binding_review["reviewer_role"])
        and type(binding_review.get("reviewer_task_id")) is str
        and bool(binding_review["reviewer_task_id"])
        and type(binding_review.get("reviewer_turn_id")) is str
        and bool(binding_review["reviewer_turn_id"])
        and binding_review.get("executed") is False
        and binding_review.get("c1_tensor_bodies_read") == 0
        and binding_review.get("pixels_decoded") == 0
        and binding_review.get("images_viewed") == 0
        and binding_review.get("blocking_findings") == [],
        "C1 camera-guard binding lacks its exact no-body independent review",
    )
    reviewed = parse_utc(binding_review.get("completed_utc"), "binding review completed_utc")
    require(created <= reviewed <= started_utc, "Binding review time order differs")
    roles = {
        AUTHOR_ROLE,
        source_reviews[0]["reviewer_role"], source_reviews[1]["reviewer_role"],
        binding["author_role"], binding_review["reviewer_role"],
    }
    require(len(roles) == 5, "Source author/reviewers and binding author/reviewer must be distinct")
    task_ids = {
        source_reviews[0]["reviewer_task_id"], source_reviews[1]["reviewer_task_id"],
        binding["author_task_id"], binding_review["reviewer_task_id"],
    }
    require(len(task_ids) == 4, "Review and binding task identities must be pairwise distinct")
    return binding, binding_review, {
        str(BINDING): binding_record, str(BINDING_REVIEW): review_record,
    }


def verify_governance_attestation(
    args, source_reviews, binding, binding_review, started_utc, deadline,
):
    """Require an out-of-candidate governance receipt for role/time claims.

    The Python source validates exact cross-document consistency.  Trust in the
    named orchestration task remains external and is stated as such; unequal
    self-declared role strings alone never authorize V11.
    """
    receipt, record = read_json(
        GOVERNANCE_ATTESTATION, args.governance_attestation_sha256,
        "external V11 governance attestation", deadline,
    )
    artifacts = {
        **expected_source_review_identities(args.self_sha256, args.supervisor_sha256),
        "primary_source_review": args.primary_source_review_sha256,
        "adversarial_source_review": args.adversarial_source_review_sha256,
        "C1_CAMERA_GUARD_BINDING_V11.json": args.binding_sha256,
        "BINDING_REVIEW_V11.json": args.binding_review_sha256,
        "v6_primary_blocked_review":
        "0b30345a8546cd2e89036b118b12b75825cf7662b133d2bac380b4f9904aeb16",
    }
    expected_events = {
        "source_author": {
            "role": AUTHOR_ROLE,
            "task_id": AUTHOR_ROLE,
        },
        "primary_source_review": {
            "role": source_reviews[0]["reviewer_role"],
            "task_id": source_reviews[0]["reviewer_task_id"],
            "turn_id": source_reviews[0]["reviewer_turn_id"],
            "completed_utc": source_reviews[0]["completed_utc"],
            "artifact_sha256": args.primary_source_review_sha256,
        },
        "adversarial_source_review": {
            "role": source_reviews[1]["reviewer_role"],
            "task_id": source_reviews[1]["reviewer_task_id"],
            "turn_id": source_reviews[1]["reviewer_turn_id"],
            "completed_utc": source_reviews[1]["completed_utc"],
            "artifact_sha256": args.adversarial_source_review_sha256,
        },
        "binding_author": {
            "role": binding["author_role"],
            "task_id": binding["author_task_id"],
            "turn_id": binding["author_turn_id"],
            "completed_utc": binding["created_utc"],
            "artifact_sha256": args.binding_sha256,
        },
        "binding_review": {
            "role": binding_review["reviewer_role"],
            "task_id": binding_review["reviewer_task_id"],
            "turn_id": binding_review["reviewer_turn_id"],
            "completed_utc": binding_review["completed_utc"],
            "artifact_sha256": args.binding_review_sha256,
        },
    }
    issuer = receipt.get("issuer")
    require(
        receipt.get("schema") == "s45b-c1-numeric-camera-guard-governance-attestation-v1"
        and receipt.get("status") == "PASS_EXTERNAL_ORCHESTRATOR_PROVENANCE_GATE_V11"
        and receipt.get("trust_boundary")
        == "EXTERNAL_ORCHESTRATOR_PROVENANCE_NOT_SELF_AUTHENTICATED_BY_CANDIDATE"
        and receipt.get("artifact_identities") == artifacts
        and receipt.get("role_time_events") == expected_events
        and type(issuer) is dict and set(issuer) == {"role", "task_id", "turn_id"}
        and all(type(issuer[key]) is str and bool(issuer[key]) for key in issuer)
        and receipt.get("blocking_findings") == []
        and receipt.get("authorizes_exact_source_binding_only") is True
        and receipt.get("formal_execution_completed") is False,
        "External governance attestation is absent, self-inconsistent, or belongs to another source set",
    )
    created = parse_utc(receipt.get("created_utc"), "governance attestation created_utc")
    binding_reviewed = parse_utc(
        binding_review["completed_utc"], "binding review completed_utc",
    )
    require(binding_reviewed <= created <= started_utc,
            "Governance attestation must follow binding review and precede execution")
    return receipt, {str(GOVERNANCE_ATTESTATION): record}


def verify_upstream(binding, deadline):
    upstream = binding["upstream"]
    docs = {}
    records = {}
    for name in fixed_upstream_paths():
        if name == "archive_events":
            records[str(C1_ARCHIVE_EVENTS)] = file_record(
                C1_ARCHIVE_EVENTS, upstream[name]["sha256"], deadline,
            )
        else:
            docs[name], records[str(fixed_upstream_paths()[name])] = read_json(
                fixed_upstream_paths()[name], upstream[name]["sha256"], name, deadline,
            )

    manifest = docs["generation_manifest"]
    require(
        manifest.get("schema") == "s44-c1-confirmation-two-batch-v1"
        and manifest.get("status") == "FROZEN_C1_BASELINE_CONFIRMATION_TWO_BATCH_EXECUTION"
        and manifest.get("derivation_policy", {}).get("row") == "C1"
        and manifest.get("output_root") == str(C1_OUTPUT),
        "C1 manifest contract differs",
    )
    generation = docs["generation_terminal_receipt"]
    worker = docs["generation_worker_receipt"]
    require(
        generation.get("schema") == "s44-c1-confirmation-launch-v1"
        and generation.get("status") == "C1_BASELINE_EXTERNAL_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW"
        and generation.get("manifest_sha256") == C1_MANIFEST_SHA256
        and generation.get("returncode") == 0
        and generation.get("worker_spawned") is True
        and generation.get("source_unchanged_at_close") is True
        and generation.get("worker_receipt_sha256") == upstream["generation_worker_receipt"]["sha256"]
        and "limit_exceeded" not in generation
        and "unexpected_live_descendants" not in generation,
        "C1 generation terminal receipt is not a clean successful terminal record",
    )
    require(
        worker.get("schema") == "s44-c1-confirmation-worker-v1"
        and worker.get("status") == "C1_BASELINE_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW"
        and worker.get("manifest_sha256") == C1_MANIFEST_SHA256
        and worker.get("source_unchanged_at_close") is True
        and worker.get("runtime_factory_calls") == 1
        and worker.get("full_resource_checks") == 1
        and worker.get("archive_receipt", {}).get("path") == str(C1_ARCHIVE_MANIFEST)
        and worker.get("archive_receipt", {}).get("sha256") == upstream["archive_manifest"]["sha256"],
        "C1 generation worker receipt is incomplete or names another archive",
    )

    terminal = docs["s45_terminal_binding"]
    refs = terminal
    require(
        terminal.get("schema") == "s45-c1-terminal-binding-v1"
        and terminal.get("status") == "FROZEN_C1_TERMINAL_SUCCESS_AND_FULL_ARCHIVE_BINDING"
        and terminal.get("row") == "C1"
        and terminal.get("placeholder_hashes") == 0
        and terminal.get("created_after_terminal") is True
        and refs.get("external_receipt", {}).get("sha256") == upstream["generation_terminal_receipt"]["sha256"]
        and refs.get("external_receipt", {}).get("path") == str(C1_GENERATION_RECEIPT)
        and refs.get("worker_receipt", {}).get("sha256") == upstream["generation_worker_receipt"]["sha256"]
        and refs.get("worker_receipt", {}).get("path") == str(C1_GENERATION_WORKER_RECEIPT)
        and refs.get("archive_manifest", {}).get("sha256") == upstream["archive_manifest"]["sha256"]
        and refs.get("archive_manifest", {}).get("path") == str(C1_ARCHIVE_MANIFEST),
        "S45 terminal binding does not bind this C1 terminal/archive set",
    )

    supervisor = docs["s45_supervisor_receipt"]
    result = supervisor.get("worker_result", {})
    require(
        supervisor.get("schema") == "s45-c1-readback-external-supervisor-v1"
        and supervisor.get("status") == "C1_READBACK_RETURNED_PENDING_INDEPENDENT_RESULT_REVIEW"
        and supervisor.get("supervisor_sha256") == S45_SUPERVISOR_SOURCE_SHA256
        and supervisor.get("returncode") == 0
        and supervisor.get("success_pending_independent_review") is True
        and supervisor.get("manifest_path") == str(C1_MANIFEST)
        and supervisor.get("manifest_sha256") == C1_MANIFEST_SHA256
        and supervisor.get("c1_execution_receipt_path") == str(C1_GENERATION_RECEIPT)
        and supervisor.get("c1_execution_receipt_sha256") == upstream["generation_terminal_receipt"]["sha256"]
        and result.get("worker_receipt_path") == str(S45_WORKER_RECEIPT)
        and result.get("worker_receipt_sha256") == upstream["s45_worker_receipt"]["sha256"]
        and result.get("report_path") == str(S45_REPORT)
        and result.get("report_sha256") == upstream["s45_report"]["sha256"],
        "S45 supervisor receipt is not the exact successful C1 readback",
    )
    readback_worker = docs["s45_worker_receipt"]
    require(
        readback_worker.get("schema") == "s45-c1-real-saved-output-readback-v1"
        and readback_worker.get("status") == "PASS_SAVED_C1_IDENTITIES_AND_CACHE_CONSUMPTION_ONLY"
        and readback_worker.get("passed") is True
        and readback_worker.get("readback_source_sha256") == S45_READBACK_SOURCE_SHA256
        and readback_worker.get("report_sha256") == upstream["s45_report"]["sha256"]
        and readback_worker.get("new_model_or_ga_runs") == 0
        and readback_worker.get("quality_status") == "NOT_EVALUATED",
        "S45 worker receipt does not have its narrow saved-output PASS",
    )
    identities = readback_worker.get("identities", {})
    require(
        identities.get(str(C1_ARCHIVE_MANIFEST), {}).get("sha256") == upstream["archive_manifest"]["sha256"]
        and identities.get(str(C1_ARCHIVE_EVENTS), {}).get("sha256") == upstream["archive_events"]["sha256"],
        "S45 worker identity set does not bind the archive manifest/events used here",
    )
    report = docs["s45_report"]
    require(
        report.get("saved_quantity_consumption_status")
        == "VERIFIED_BY_IDENTITY_BOUND_ARCHIVED_ARRAY_CHAIN_IF_THIS_REPORT_PASSES"
        and report.get("pixel_identity_status")
        == "ARCHIVED_PIL_PIXEL_TENSORS_AND_ARCHIVE_FILE_BYTES_IDENTITY_ONLY"
        and report.get("row") == "C1"
        and report.get("manifest_sha256") == C1_MANIFEST_SHA256
        and report.get("actual_archive_capture_counts", {}).get("cache_commit") == 2
        and report.get("png_decode_or_visual_quality_status") == "NOT_EVALUATED",
        "S45 report is not the exact narrow C1 identity/cache result",
    )
    result_review = docs["s45_result_review"]
    require(
        result_review.get("schema") == "s45-c1-readback-result-review-v1"
        and result_review.get("status") == "PASS_S45_C1_READBACK_RESULT_REVIEW"
        and result_review.get("verdict") == "PASS_SAVED_OUTPUT_IDENTITIES_AND_CACHE_CONSUMPTION_ONLY"
        and result_review.get("supervisor_receipt_path") == str(S45_SUPERVISOR_RECEIPT)
        and result_review.get("supervisor_receipt_sha256") == upstream["s45_supervisor_receipt"]["sha256"]
        and result_review.get("worker_receipt_path") == str(S45_WORKER_RECEIPT)
        and result_review.get("worker_receipt_sha256") == upstream["s45_worker_receipt"]["sha256"]
        and result_review.get("report_path") == str(S45_REPORT)
        and result_review.get("report_sha256") == upstream["s45_report"]["sha256"]
        and result_review.get("row_validity_assertions", {}).get("requested_pose_K_guard_pass") is False
        and result_review.get("downstream_row_validity_status")
        == "BLOCKED_AWAITING_S42_NUMERIC_REQUESTED_POSE_K_GUARD"
        and type(result_review.get("downstream_row_validity_blockers")) is list
        and bool(result_review["downstream_row_validity_blockers"])
        and result_review.get("blocking_findings") == []
        and type(result_review.get("author_role")) is str
        and type(result_review.get("reviewer_role")) is str
        and result_review["author_role"] != result_review["reviewer_role"],
        "S45 result review is missing, unbound, or incorrectly treats pose/K as already passed",
    )

    archive = docs["archive_manifest"]
    events_item = archive.get("files", {}).get("events.jsonl", {})
    require(
        archive.get("schema") == "s35-full-original-output-archive-v1"
        and archive.get("status") == "ARCHIVE_COMPLETE"
        and archive.get("evidence_kind") == "recorded_execution"
        and archive.get("caller_manifest_sha256") == C1_MANIFEST_SHA256
        and archive.get("source_identities") == manifest.get("source_identities")
        and not archive.get("missing_required_names")
        and archive.get("failed_captures") == 0
        and events_item.get("sha256") == upstream["archive_events"]["sha256"],
        "C1 full archive is incomplete or names another event chain",
    )
    return docs, records


def decode_scalar(node, label):
    require(type(node) is dict and node.get("kind") == "scalar", label + " is not a scalar key")
    value = node.get("value")
    expected = {"str": str, "int": int, "bool": bool, "NoneType": type(None)}
    kind = node.get("type")
    require(kind in expected and type(value) is expected[kind], label + " scalar label/value differs")
    return value


def raw_dict_fields(node, label):
    require(type(node) is dict and node.get("kind") == "dict" and type(node.get("items")) is list,
            label + " is not a raw archival dictionary")
    result = {}
    for item in node["items"]:
        require(type(item) is dict and set(item) == {"key", "value"}, label + " has a malformed item")
        key = decode_scalar(item["key"], label + " key")
        require(type(key) is str and key not in result, label + " has a duplicate/non-string key")
        result[key] = item["value"]
    return result


def raw_tensor(node, label):
    require(type(node) is dict and node.get("kind") == "tensor",
            label + " did not originate from a raw kind=tensor node")
    return TensorDescriptor(node)


def raw_tensor_list(node, label):
    require(type(node) is dict and node.get("kind") in ("list", "tuple")
            and type(node.get("items")) is list,
            label + " is not an exact archival list/tuple")
    values = [raw_tensor(item, label + " item") for item in node["items"]]
    return values if node["kind"] == "list" else tuple(values)


def select_camera_capture(name, tree):
    top = raw_dict_fields(tree, name)
    if name == "batch_input":
        require("target_c2ws" in top and "target_Ks" in top, "batch_input lacks target c2w/K")
        return {
            "target_c2ws": raw_tensor(top["target_c2ws"], "batch_input.target_c2ws"),
            "target_Ks": raw_tensor(top["target_Ks"], "batch_input.target_Ks"),
        }
    require(name == "cache_commit" and "cache" in top, "cache_commit lacks cache")
    cache = raw_dict_fields(top["cache"], "cache_commit.cache")
    require("c2ws" in cache and "Ks" in cache, "cache_commit.cache lacks c2w/K")
    return {
        "c2ws": raw_tensor_list(cache["c2ws"], "cache_commit.cache.c2ws"),
        "Ks": raw_tensor_list(cache["Ks"], "cache_commit.cache.Ks"),
    }


def selected_event_captures(events_path, archive_manifest, expected_sha256, deadline):
    raw_events, event_record = file_snapshot(
        events_path, expected_sha256, deadline, max_bytes=512 * 1024 * 1024,
    )
    require(event_record["sha256"] == expected_sha256,
            "Archive event chain identity differs")
    require(raw_events.endswith(b"\n"), "Archive event chain ends in a partial line")
    selected = {"batch_input": [], "cache_commit": []}
    complete_counts = {}
    pending = {}
    previous = "0" * 64
    count = 0
    final_event = None
    for raw_line in raw_events.splitlines(keepends=True):
        require(time.monotonic() <= deadline, "C1 camera guard time limit reached")
        require(raw_line.endswith(b"\n"), "Archive event chain has a partial line")
        row = json.loads(raw_line.decode("utf-8"))
        body = {key: value for key, value in row.items() if key != "sha256"}
        require(
            row.get("schema") == "s35-full-original-output-archive-v1"
            and row.get("evidence_kind") == "recorded_execution"
            and row.get("seq") == count
            and row.get("previous_sha256") == previous
            and hashlib.sha256(canonical(body)).hexdigest() == row.get("sha256"),
            "Archive event hash chain is broken",
        )
        payload = row.get("payload", {})
        event = row.get("event")
        if event == "capture_begin":
            key = (payload.get("name"), payload.get("occurrence"))
            require(row["seq"] not in pending, "Duplicate capture begin")
            pending[row["seq"]] = key
        elif event == "capture_complete":
            name = payload.get("name")
            occurrence = payload.get("occurrence")
            require(pending.pop(payload.get("begin_seq"), None) == (name, occurrence),
                    "Broken archive capture pair")
            require(occurrence == complete_counts.get(name, 0), "Archive occurrence order differs")
            complete_counts[name] = occurrence + 1
            if name in selected:
                require(occurrence < 2, "More than two selected camera captures")
                selected[name].append(select_camera_capture(name, payload.get("tree")))
        else:
            require(event in ("archive_start", "archive_finalize"), "Archive contains a failure/unexpected event")
        previous = row["sha256"]
        final_event = event
        count += 1
    require(
        not pending and final_event == "archive_finalize"
        and count == archive_manifest.get("event_count")
        and previous == archive_manifest.get("last_event_sha256")
        and complete_counts == archive_manifest.get("archived_name_counts")
        and len(selected["batch_input"]) == len(selected["cache_commit"]) == 2,
        "Archive event/capture closure differs",
    )
    return selected, {"event_count": count, "last_event_sha256": previous}


def flatten(value):
    if type(value) is list:
        result = []
        for item in value:
            result.extend(flatten(item))
        return result
    return [value]


def nested_shape(value):
    if type(value) is not list:
        require_guard(type(value) in (int, float) and type(value) is not bool,
                      "Camera/K value is not an exact real scalar")
        return ()
    require_guard(bool(value), "Camera/K array has an empty dimension")
    child = nested_shape(value[0])
    require_guard(all(nested_shape(item) == child for item in value[1:]),
                  "Camera/K array is ragged")
    return (len(value),) + child


def reshape(values, shape):
    require(type(shape) is list and shape and all(type(n) is int and n > 0 for n in shape),
            "Cannot reshape malformed camera tensor")
    iterator = iter(values)
    def build(level):
        if level == len(shape) - 1:
            return [next(iterator) for _ in range(shape[level])]
        return [build(level + 1) for _ in range(shape[level])]
    result = build(0)
    try:
        next(iterator)
    except StopIteration:
        return result
    raise ValueError("Camera tensor contains surplus values")


class CameraTensorStore:
    def __init__(self, archive_manifest, archive_root, deadline):
        self.manifest = archive_manifest
        self.root = archive_root
        self.deadline = deadline
        self.opened = {}
        self.body_opened_count = 0
        self.body_bytes_read = 0
        self.close_verified_count = 0

    def decode(self, descriptor, shape_check, label):
        require(type(descriptor) is TensorDescriptor, label + " lost raw tensor provenance")
        desc = dict(descriptor)
        descriptor_keys = {
            "blob", "byteorder", "bytes_sha256", "dtype", "kind",
            "nbytes", "order", "sha256", "shape",
        }
        require(
            set(desc) == descriptor_keys and desc.get("kind") == "tensor"
            and desc.get("byteorder") == "little" and desc.get("order") == "C"
            and desc.get("dtype") in WIDTHS
            and HEX.fullmatch(desc.get("sha256", "")) is not None
            and HEX.fullmatch(desc.get("bytes_sha256", "")) is not None,
            label + " descriptor codec differs",
        )
        shape = desc.get("shape")
        require(type(shape) is list and all(type(n) is int and n > 0 for n in shape)
                and shape_check(shape), label + " shape is outside frozen camera/K scope")
        count = math.prod(shape)
        require(desc.get("nbytes") == count * WIDTHS[desc["dtype"]]
                and 0 < desc["nbytes"] <= MAX_CAMERA_TENSOR_BYTES,
                label + " byte size is outside frozen camera/K scope")
        registry = self.manifest.get("tensor_descriptors")
        files = self.manifest.get("files")
        raw = desc.get("blob")
        require(type(registry) is dict and type(files) is dict and type(raw) is str,
                "Archive tensor registry is malformed")
        require(registry.get(raw) == desc, label + " differs from archive tensor registry")
        require(raw == "tensors/" + desc["sha256"] + ".bin", label + " blob path is not canonical")
        side_raw = "tensors/" + desc["sha256"] + ".json"
        body_item, side_item = files.get(raw), files.get(side_raw)
        require(
            type(body_item) is dict and set(body_item) == {"bytes", "sha256"}
            and body_item.get("bytes") == desc["nbytes"]
            and body_item.get("sha256") == desc["bytes_sha256"]
            and type(side_item) is dict and set(side_item) == {"bytes", "sha256"},
            label + " body/sidecar manifest identity differs",
        )
        if raw not in self.opened:
            self.opened[raw] = self._snapshot(desc, body_item, side_item, side_raw, label)
        item = self.opened[raw]
        require(item["descriptor"] == desc, label + " cached descriptor differs")
        code = "f" if desc["dtype"] == "float32" else "d"
        values = [item[0] for item in struct.iter_unpack("<" + code, item["snapshot"])]
        require(len(values) == count and all(math.isfinite(value) for value in values),
                label + " contains nonfinite or wrong-count values")
        return reshape(values, shape)

    def _snapshot(self, desc, body_item, side_item, side_raw, label):
        path = self.root / desc["blob"]
        sidecar = self.root / side_raw
        require(path.parent == self.root / "tensors" and sidecar.parent == self.root / "tensors",
                label + " tensor path escapes archive/tensors")
        require(not path.is_symlink() and not sidecar.is_symlink(), label + " tensor/sidecar is symlinked")
        side_doc, side_record = read_json(
            sidecar, side_item.get("sha256", ""), label + " sidecar", self.deadline,
        )
        require(side_doc == desc and sidecar.stat().st_size == side_item.get("bytes"),
                label + " sidecar differs from descriptor")
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(path, flags)
        self.body_opened_count += 1
        try:
            before = os.fstat(fd)
            path_stat = os.stat(path, follow_symlinks=False)
            require(stat.S_ISREG(before.st_mode) and stat.S_ISREG(path_stat.st_mode)
                    and before.st_size == desc["nbytes"]
                    and (before.st_dev, before.st_ino) == (path_stat.st_dev, path_stat.st_ino),
                    label + " opened body identity differs")
            pieces = []
            digest = hashlib.sha256()
            offset = 0
            while offset < desc["nbytes"]:
                require(time.monotonic() <= self.deadline, "C1 camera guard time limit reached")
                block = os.pread(fd, min(4096, desc["nbytes"] - offset), offset)
                require(bool(block), label + " has unexpected EOF")
                pieces.append(block); digest.update(block); offset += len(block)
                self.body_bytes_read += len(block)
            require(os.pread(fd, 1, desc["nbytes"]) == b"", label + " exceeds descriptor size")
            after = os.fstat(fd)
            require(stat_identity(before) == stat_identity(after), label + " changed during same-FD read")
            snapshot = b"".join(pieces)
            body_sha = digest.hexdigest()
            require(body_sha == desc["bytes_sha256"] == body_item["sha256"], label + " body SHA differs")
            base = {key: value for key, value in desc.items() if key not in ("blob", "sha256")}
            require(hashlib.sha256(canonical(base) + b"\0" + snapshot).hexdigest() == desc["sha256"],
                    label + " descriptor-plus-body SHA differs")
            return {
                "fd": fd, "path": path, "descriptor": desc, "snapshot": snapshot,
                "body_sha256": body_sha, "opened_identity": stat_identity(before),
                "sidecar": sidecar, "sidecar_record": side_record,
            }
        except BaseException:
            os.close(fd)
            raise

    def close(self, verify):
        first_error = None
        for raw, item in list(self.opened.items()):
            try:
                if verify:
                    current = os.fstat(item["fd"])
                    require(stat_identity(current) == item["opened_identity"], "Used camera tensor metadata changed")
                    data = os.pread(item["fd"], len(item["snapshot"]), 0)
                    require(data == item["snapshot"] and hashlib.sha256(data).hexdigest() == item["body_sha256"],
                            "Used camera tensor body changed before sealing")
                    current_path = os.stat(item["path"], follow_symlinks=False)
                    require((current.st_dev, current.st_ino) == (current_path.st_dev, current_path.st_ino),
                            "Used camera tensor canonical path changed")
                    side = file_record(
                        item["sidecar"], item["sidecar_record"]["sha256"], self.deadline,
                    )
                    require(side["stat"] == item["sidecar_record"]["stat"],
                            "Used camera tensor sidecar changed before sealing")
                    self.close_verified_count += 1
            except BaseException as error:
                if first_error is None:
                    first_error = error
            finally:
                os.close(item["fd"])
                del self.opened[raw]
        if first_error is not None:
            raise first_error
        return self.close_verified_count

    def identities(self):
        return {
            raw: {
                "descriptor_sha256": item["descriptor"]["sha256"],
                "body_sha256": item["body_sha256"],
                "dtype": item["descriptor"]["dtype"],
                "shape": item["descriptor"]["shape"],
                "nbytes": item["descriptor"]["nbytes"],
            }
            for raw, item in self.opened.items()
        }


def matrix_max_abs(first, second):
    require_guard(nested_shape(first) == nested_shape(second), "Camera/K shape differs")
    a, b = flatten(first), flatten(second)
    require_guard(len(a) == len(b) and a and all(math.isfinite(x) for x in a + b),
                  "Camera/K shape or finiteness differs")
    return max(abs(float(x) - float(y)) for x, y in zip(a, b))


def expected_pose(base, yaw_degrees):
    require_guard(len(base) == 4 and all(type(row) is list and len(row) == 4 for row in base),
                  "Base c2w is not 4x4")
    angle = math.radians(yaw_degrees)
    rotation = [
        [math.cos(angle), 0.0, math.sin(angle)],
        [0.0, 1.0, 0.0],
        [-math.sin(angle), 0.0, math.cos(angle)],
    ]
    result = [[0.0] * 4 for _ in range(4)]
    for row in range(3):
        for column in range(3):
            result[row][column] = sum(rotation[row][k] * float(base[k][column]) for k in range(3))
        result[row][3] = float(base[row][3])
    result[3] = [0.0, 0.0, 0.0, 1.0]
    return result


def evaluate_numeric_guard(batch_targets, cache_commits):
    require_guard(len(batch_targets) == len(cache_commits) == 2,
                  "Exactly two batch_input/cache_commit occurrences are required")
    require_guard(
        len(cache_commits[0]["c2ws"]) == len(cache_commits[0]["Ks"]) == 5
        and len(cache_commits[1]["c2ws"]) == len(cache_commits[1]["Ks"]) == 9,
        "Cache history is not exactly 5 then 9",
    )
    continuity = []
    for frame_id in range(5):
        pose_error = matrix_max_abs(cache_commits[0]["c2ws"][frame_id], cache_commits[1]["c2ws"][frame_id])
        k_error = matrix_max_abs(cache_commits[0]["Ks"][frame_id], cache_commits[1]["Ks"][frame_id])
        require_guard(pose_error <= TOLERANCE and k_error <= TOLERANCE,
                      "First cache commit is not preserved in second cache")
        continuity.append({"id": frame_id, "pose_max_abs": pose_error, "K_max_abs": k_error})

    # S42 anchors every planned pose, fixed K and closure to final-cache ID0.
    base_pose = cache_commits[1]["c2ws"][0]
    base_k = cache_commits[1]["Ks"][0]
    homogeneous_error = matrix_max_abs(base_pose[3], [0.0, 0.0, 0.0, 1.0])
    require_guard(homogeneous_error <= TOLERANCE,
                  "Base c2w homogeneous row differs")
    actual_poses = [base_pose]
    actual_ks = [base_k]
    cross = []
    for batch_index, (begin, end) in enumerate(((1, 5), (5, 9))):
        targets = batch_targets[batch_index]
        require_guard(len(targets["c2ws"]) >= 4 and len(targets["Ks"]) >= 4,
                      "Batch has fewer than four authoritative targets")
        cache = cache_commits[batch_index]
        for offset, frame_id in enumerate(range(begin, end)):
            pose_error = matrix_max_abs(targets["c2ws"][offset], cache["c2ws"][frame_id])
            k_error = matrix_max_abs(targets["Ks"][offset], cache["Ks"][frame_id])
            require_guard(pose_error <= TOLERANCE and k_error <= TOLERANCE,
                          "batch_input to cache_commit c2w/K cross-check failed")
            cross.append({"id": frame_id, "pose_max_abs": pose_error, "K_max_abs": k_error})
            actual_poses.append(cache["c2ws"][frame_id])
            actual_ks.append(cache["Ks"][frame_id])

    planned = []
    for frame_id, yaw in enumerate(EXPECTED_YAW):
        pose_error = matrix_max_abs(actual_poses[frame_id], expected_pose(base_pose, yaw))
        k_error = matrix_max_abs(actual_ks[frame_id], base_k)
        require_guard(pose_error <= TOLERANCE and k_error <= TOLERANCE,
                      "Planned yaw or fixed K guard failed")
        planned.append({
            "id": frame_id, "yaw_degrees": yaw,
            "pose_max_abs": pose_error, "K_max_abs": k_error,
        })
    closure_pose = matrix_max_abs(actual_poses[8], actual_poses[0])
    closure_k = matrix_max_abs(actual_ks[8], actual_ks[0])
    require_guard(closure_pose <= TOLERANCE and closure_k <= TOLERANCE,
                  "ID8 does not close to ID0 c2w/K")
    return {
        "status": "PASS_C1_REQUESTED_CAMERA_INPUT_CONDITION_GUARD_ONLY",
        "row": "C1",
        "tolerance": TOLERANCE,
        "cache_commit_sizes": [5, 9],
        "batch_authoritative_target_counts": [4, 4],
        "base_homogeneous_row_max_abs": homogeneous_error,
        "planned_yaw_degrees": list(EXPECTED_YAW),
        "cache_commit_continuity": continuity,
        "batch_target_to_cache": cross,
        "planned_sequence": planned,
        "id8_to_id0": {"pose_max_abs": closure_pose, "K_max_abs": closure_k},
        "pixel_score": "NOT_EVALUATED",
        "visual_quality": "NOT_EVALUATED",
        "rendered_pixel_camera_obedience": "NOT_EVALUATED_NO_FROZEN_PROXY",
        "method_gain": "NOT_EVALUATED",
        "novelty": "NOT_EVALUATED",
    }


def decode_selected_cameras(captures, store):
    batches = []
    for index, item in enumerate(captures["batch_input"]):
        c2ws = store.decode(
            item["target_c2ws"],
            lambda shape: len(shape) == 3 and 4 <= shape[0] <= 8 and shape[1:] == [4, 4],
            f"batch_input[{index}].target_c2ws",
        )
        ks = store.decode(
            item["target_Ks"],
            lambda shape: len(shape) == 3 and 4 <= shape[0] <= 8 and shape[1] == shape[2] and shape[1] in (3, 4),
            f"batch_input[{index}].target_Ks",
        )
        batches.append({"c2ws": c2ws[:4], "Ks": ks[:4]})
    commits = []
    for index, item in enumerate(captures["cache_commit"]):
        expected = 5 if index == 0 else 9
        require_guard(len(item["c2ws"]) == len(item["Ks"]) == expected,
                      "Cache descriptor history is not 5 then 9")
        c2ws = [
            store.decode(desc, lambda shape: shape == [4, 4], f"cache_commit[{index}].c2ws[{slot}]")
            for slot, desc in enumerate(item["c2ws"])
        ]
        ks = []
        for slot, desc in enumerate(item["Ks"]):
            value = store.decode(
                desc,
                lambda shape: len(shape) == 2 and shape[0] == shape[1] and shape[0] in (3, 4),
                f"cache_commit[{index}].Ks[{slot}]",
            )
            ks.append(value)
        commits.append({"c2ws": c2ws, "Ks": ks})
    base_k_shape = [len(commits[0]["Ks"][0]), len(commits[0]["Ks"][0][0])]
    require_guard(all([len(k), len(k[0])] == base_k_shape for commit in commits for k in commit["Ks"]),
                  "Cache K matrix shapes differ")
    require_guard(all([len(k), len(k[0])] == base_k_shape for batch in batches for k in batch["Ks"]),
                  "Target/cache K matrix shapes differ")
    return batches, commits


def inode_identity(value):
    return value.st_dev, value.st_ino, value.st_mode


def verify_directory_lease(
    parent_fd, parent_path, parent_identity,
    output_fd=None, output_name=None, output_identity=None,
):
    parent_now = os.fstat(parent_fd)
    parent_path_now = os.stat(parent_path, follow_symlinks=False)
    require(
        stat.S_ISDIR(parent_now.st_mode)
        and inode_identity(parent_now) == parent_identity
        and inode_identity(parent_path_now) == parent_identity,
        "Camera-guard source directory inode lease changed",
    )
    if output_fd is not None:
        require(type(output_name) is str and bool(output_name),
                "Output lease requires a fixed entry name")
        output_now = os.fstat(output_fd)
        output_path_now = os.stat(output_name, dir_fd=parent_fd, follow_symlinks=False)
        require(
            stat.S_ISDIR(output_now.st_mode)
            and inode_identity(output_now) == output_identity
            and inode_identity(output_path_now) == output_identity,
            "Formal output directory inode lease changed",
        )


def entry_absent(parent_fd, name):
    try:
        os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return True
    return False


def write_all(fd, body):
    offset = 0
    while offset < len(body):
        written = os.write(fd, body[offset:])
        require(written > 0, "File-descriptor write made no progress")
        offset += written


def write_new_at(directory_fd, name, value):
    require(type(name) is str and re.fullmatch(r"[a-z_]+\.json", name) is not None,
            "Formal artifact name is outside the fixed JSON scope")
    body = encoded_json(value)
    flags = (
        os.O_WRONLY | os.O_CREAT | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    )
    fd = os.open(name, flags, 0o600, dir_fd=directory_fd)
    try:
        opened = os.fstat(fd)
        require(stat.S_ISREG(opened.st_mode) and opened.st_nlink == 1,
                "Formal artifact is not a single-link regular file")
        write_all(fd, body)
        os.fsync(fd)
        closed = os.fstat(fd)
        path_now = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        require(
            inode_identity(opened) == inode_identity(closed) == inode_identity(path_now)
            and closed.st_size == len(body) and closed.st_nlink == 1,
            "Formal artifact inode changed while writing",
        )
    finally:
        os.close(fd)
    os.fsync(directory_fd)
    return hashlib.sha256(body).hexdigest()


def verify_lock_lease(
    parent_fd, parent_path, parent_identity, lock_fd, lock_name,
    lock_identity, lock_sha256, lock_bytes,
):
    verify_directory_lease(parent_fd, parent_path, parent_identity)
    held = os.fstat(lock_fd)
    path_now = os.stat(lock_name, dir_fd=parent_fd, follow_symlinks=False)
    require(
        stat.S_ISREG(held.st_mode) and stat.S_ISREG(path_now.st_mode)
        and held.st_nlink == path_now.st_nlink == 1
        and inode_identity(held) == lock_identity
        and inode_identity(path_now) == lock_identity
        and held.st_size == path_now.st_size == lock_bytes,
        "Permanent attempt lock pathname/inode/link identity changed",
    )
    snapshot = os.pread(lock_fd, lock_bytes, 0)
    require(
        len(snapshot) == lock_bytes
        and os.pread(lock_fd, 1, lock_bytes) == b""
        and hashlib.sha256(snapshot).hexdigest() == lock_sha256,
        "Permanent attempt lock structured receipt changed",
    )


def commit_attempt_lease(
    parent_fd, parent_path, parent_identity, lock_name, staging_name, lease_record,
):
    """Atomically publish a fully written fail-closed receipt as the one-use lock."""
    verify_directory_lease(parent_fd, parent_path, parent_identity)
    require(entry_absent(parent_fd, lock_name), "Permanent C1 camera-guard attempt already exists")
    require(entry_absent(parent_fd, staging_name), "Fixed attempt-lease staging entry already exists")
    body = encoded_json(lease_record)
    body_sha256 = hashlib.sha256(body).hexdigest()
    flags = (
        os.O_RDWR | os.O_CREAT | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    )
    fd = os.open(staging_name, flags, 0o600, dir_fd=parent_fd)
    committed = False
    try:
        opened = os.fstat(fd)
        require(stat.S_ISREG(opened.st_mode) and opened.st_nlink == 1,
                "Attempt-lease staging is not one regular file")
        write_all(fd, body)
        os.fsync(fd)
        written = os.fstat(fd)
        staging_now = os.stat(staging_name, dir_fd=parent_fd, follow_symlinks=False)
        require(
            inode_identity(opened) == inode_identity(written) == inode_identity(staging_now)
            and written.st_nlink == staging_now.st_nlink == 1
            and written.st_size == staging_now.st_size == len(body)
            and hashlib.sha256(os.pread(fd, len(body), 0)).hexdigest() == body_sha256,
            "Attempt-lease staging identity/content changed",
        )
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        os.link(
            staging_name, lock_name,
            src_dir_fd=parent_fd, dst_dir_fd=parent_fd, follow_symlinks=False,
        )
        committed = True
        os.fsync(parent_fd)
        os.unlink(staging_name, dir_fd=parent_fd)
        os.fsync(parent_fd)
        lock_stat = os.fstat(fd)
        lock_identity = inode_identity(lock_stat)
        verify_lock_lease(
            parent_fd, parent_path, parent_identity, fd, lock_name,
            lock_identity, body_sha256, len(body),
        )
        return fd, lock_identity, body_sha256, len(body)
    except BaseException:
        if not committed:
            try:
                current = os.stat(staging_name, dir_fd=parent_fd, follow_symlinks=False)
                if inode_identity(current) == inode_identity(os.fstat(fd)):
                    os.unlink(staging_name, dir_fd=parent_fd)
                    os.fsync(parent_fd)
            except BaseException:
                pass
        os.close(fd)
        raise


def same_records(records, deadline):
    closed = {}
    ok = True
    for raw, opened in records.items():
        try:
            current = file_record(Path(raw), opened["sha256"], deadline)
            match = current["stat"] == opened["stat"] and current["bytes"] == opened["bytes"]
        except BaseException as error:
            current = {"error": type(error).__name__ + ": " + str(error)}
            match = False
        closed[raw] = {"matches_start": match, "current": current}
        ok = ok and match
    return ok, closed


def synthetic_selftest():
    base = [
        [1.0, 0.0, 0.0, 1.25],
        [0.0, 0.0, -1.0, -0.5],
        [0.0, 1.0, 0.0, 2.75],
        [0.0, 0.0, 0.0, 1.0],
    ]
    k = [[500.0, 0.0, 288.0], [0.0, 500.0, 288.0], [0.0, 0.0, 1.0]]
    poses = [expected_pose(base, yaw) for yaw in EXPECTED_YAW]
    ks = [[row[:] for row in k] for _ in range(9)]
    batches = [
        {"c2ws": poses[1:5], "Ks": ks[1:5]},
        {"c2ws": poses[5:9], "Ks": ks[5:9]},
    ]
    commits = [
        {"c2ws": poses[:5], "Ks": ks[:5]},
        {"c2ws": poses[:9], "Ks": ks[:9]},
    ]
    result = evaluate_numeric_guard(batches, commits)
    require(result["status"] == "PASS_C1_REQUESTED_CAMERA_INPUT_CONDITION_GUARD_ONLY",
            "Positive synthetic guard failed")

    def rejected(change):
        copied_batches = json.loads(json.dumps(batches))
        copied_commits = json.loads(json.dumps(commits))
        change(copied_batches, copied_commits)
        try:
            evaluate_numeric_guard(copied_batches, copied_commits)
        except GuardInvalid:
            return True
        return False

    def mismatch(b, c): b[0]["c2ws"][0][0][0] += 2e-6
    def wrong_sign(b, c):
        bad = expected_pose(base, -EXPECTED_YAW[1]); b[0]["c2ws"][0] = bad; c[0]["c2ws"][1] = bad; c[1]["c2ws"][1] = bad
    def k_drift(b, c): c[1]["Ks"][6][0][0] += 2e-6
    def closure(b, c): b[1]["c2ws"][3][0][3] += 2e-6; c[1]["c2ws"][8][0][3] += 2e-6
    def nonfinite(b, c): b[0]["Ks"][0][0][0] = float("inf")
    require(all(rejected(change) for change in (mismatch, wrong_sign, k_drift, closure, nonfinite)),
            "A negative synthetic camera/K case was accepted")

    boundary_batches = json.loads(json.dumps(batches))
    boundary_batches[0]["c2ws"][0][3][0] = TOLERANCE
    require(evaluate_numeric_guard(boundary_batches, commits)["status"]
            == "PASS_C1_REQUESTED_CAMERA_INPUT_CONDITION_GUARD_ONLY",
            "Inclusive <=1e-6 boundary was rejected")
    over_batches = json.loads(json.dumps(batches))
    over_batches[0]["c2ws"][0][3][0] = TOLERANCE * 1.000001
    try:
        evaluate_numeric_guard(over_batches, commits)
    except GuardInvalid:
        pass
    else:
        raise AssertionError("Strictly over-tolerance synthetic mismatch was accepted")
    return {
        "schema": "s45b-c1-numeric-camera-guard-synthetic-selftest-v1",
        "status": "PASS_SYNTHETIC_ONLY",
        "b0_convention": "LEFT_MULTIPLY_Y_WITH_POSITIVE_SIN_AT_0_2_AND_NEGATIVE_SIN_AT_2_0",
        "positive_path": "PASS",
        "negative_cases": [
            "target_to_cache_mismatch", "wrong_yaw_sign", "K_drift",
            "ID8_closure_failure", "nonfinite_value", "strictly_over_tolerance",
        ],
        "inclusive_tolerance_boundary": "PASS",
        "c1_files_opened": 0,
        "c1_tensor_bodies_read": 0,
        "pixels_decoded": 0,
        "images_viewed": 0,
        "formal_paths_created": 0,
    }


def formal_preflight(args, parent_fd, parent_identity):
    """Run all harmless metadata/source gates before the one-use lease exists."""
    started_monotonic = time.monotonic()
    started_utc = datetime.now(timezone.utc)
    deadline = started_monotonic + SECONDS
    require(Path(args.out).is_absolute() and os.fspath(Path(args.out)) == os.fspath(FORMAL_OUT),
            "Only the fixed execution_01 output is accepted")
    verify_directory_lease(parent_fd, HERE, parent_identity)
    for name in (FORMAL_OUT.name, LOCK.name, LOCK_STAGING.name):
        require(entry_absent(parent_fd, name), "Formal/preparation entry already exists: " + name)
    static_records = verify_static_reference(
        args.self_sha256, args.supervisor_sha256, deadline,
    )
    source_reviews, review_records = verify_source_reviews(args, started_utc, deadline)
    binding, binding_review, binding_records = verify_binding(
        args, source_reviews, started_utc, deadline,
    )
    governance, governance_records = verify_governance_attestation(
        args, source_reviews, binding, binding_review, started_utc, deadline,
    )
    docs, upstream_records = verify_upstream(binding, deadline)
    captures, event_summary = selected_event_captures(
        C1_ARCHIVE_EVENTS, docs["archive_manifest"],
        binding["upstream"]["archive_events"]["sha256"], deadline,
    )
    records = {
        **static_records, **review_records, **binding_records,
        **governance_records, **upstream_records,
    }
    unchanged, precommit_records = same_records(records, deadline)
    require(unchanged, "A source or bound metadata identity changed during harmless preflight")
    verify_directory_lease(parent_fd, HERE, parent_identity)
    for name in (FORMAL_OUT.name, LOCK.name, LOCK_STAGING.name):
        require(entry_absent(parent_fd, name), "Formal/preparation entry appeared during preflight: " + name)
    return {
        "started_monotonic": started_monotonic,
        "started_utc": started_utc,
        "deadline": deadline,
        "binding": binding,
        "governance_attestation": governance,
        "docs": docs,
        "captures": captures,
        "event_summary": event_summary,
        "records": records,
        "precommit_records": precommit_records,
    }


def create_output_lease(parent_fd, parent_identity):
    verify_directory_lease(parent_fd, HERE, parent_identity)
    require(entry_absent(parent_fd, FORMAL_OUT.name), "Formal output appeared before lease creation")
    os.mkdir(FORMAL_OUT.name, mode=0o700, dir_fd=parent_fd)
    flags = (
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    )
    output_fd = os.open(FORMAL_OUT.name, flags, dir_fd=parent_fd)
    output_stat = os.fstat(output_fd)
    output_identity = inode_identity(output_stat)
    require(stat.S_ISDIR(output_stat.st_mode), "Formal output lease is not a directory")
    verify_directory_lease(
        parent_fd, HERE, parent_identity,
        output_fd, FORMAL_OUT.name, output_identity,
    )
    return output_fd, output_identity


def committed_worker_preflight(
    args, parent_fd, parent_identity,
    lock_fd, lock_identity, lock_sha256, lock_bytes,
    output_fd, output_identity,
    report_fd, report_identity, worker_receipt_fd, worker_receipt_identity,
):
    """Repeat every identity gate after commit before any tensor-body open."""
    started_monotonic = time.monotonic()
    started_utc = datetime.now(timezone.utc)
    deadline = started_monotonic + SECONDS
    require(Path(args.out).is_absolute() and os.fspath(Path(args.out)) == os.fspath(FORMAL_OUT),
            "Only the fixed execution_01 output is accepted")
    verify_directory_lease(
        parent_fd, HERE, parent_identity,
        output_fd, FORMAL_OUT.name, output_identity,
    )
    verify_lock_lease(
        parent_fd, HERE, parent_identity, lock_fd, LOCK.name,
        lock_identity, lock_sha256, lock_bytes,
    )
    require(entry_absent(parent_fd, LOCK_STAGING.name),
            "Attempt-lock staging entry remains after commit")
    verify_prebound_artifact(
        output_fd, REPORT_NAME, report_fd, report_identity, require_empty=True,
    )
    verify_prebound_artifact(
        output_fd, WORKER_RECEIPT_NAME, worker_receipt_fd,
        worker_receipt_identity, require_empty=True,
    )
    for name in (
        WORKER_FAILURE_NAME, SUPERVISOR_RECEIPT_NAME, BARRIER_NAME, TERMINAL_SEAL_NAME,
        TERMINAL_SEAL_STAGING_NAME, TERMINAL_FAILURE_NAME,
    ):
        require(entry_absent(output_fd, name),
                "Formal artifact exists before worker start: " + name)

    static_records = verify_static_reference(
        args.self_sha256, args.supervisor_sha256, deadline,
    )
    source_reviews, review_records = verify_source_reviews(args, started_utc, deadline)
    binding, binding_review, binding_records = verify_binding(
        args, source_reviews, started_utc, deadline,
    )
    governance, governance_records = verify_governance_attestation(
        args, source_reviews, binding, binding_review, started_utc, deadline,
    )
    docs, upstream_records = verify_upstream(binding, deadline)
    captures, event_summary = selected_event_captures(
        C1_ARCHIVE_EVENTS, docs["archive_manifest"],
        binding["upstream"]["archive_events"]["sha256"], deadline,
    )
    records = {
        **static_records, **review_records, **binding_records,
        **governance_records, **upstream_records,
    }
    unchanged, recheck_records = same_records(records, deadline)
    require(unchanged, "A source or bound metadata identity changed in worker recheck")
    verify_directory_lease(
        parent_fd, HERE, parent_identity,
        output_fd, FORMAL_OUT.name, output_identity,
    )
    verify_lock_lease(
        parent_fd, HERE, parent_identity, lock_fd, LOCK.name,
        lock_identity, lock_sha256, lock_bytes,
    )
    verify_prebound_artifact(
        output_fd, REPORT_NAME, report_fd, report_identity, require_empty=True,
    )
    verify_prebound_artifact(
        output_fd, WORKER_RECEIPT_NAME, worker_receipt_fd,
        worker_receipt_identity, require_empty=True,
    )
    return {
        "started_monotonic": started_monotonic,
        "started_utc": started_utc,
        "deadline": deadline,
        "binding": binding,
        "governance_attestation": governance,
        "docs": docs,
        "captures": captures,
        "event_summary": event_summary,
        "records": records,
        "recheck_records": recheck_records,
    }


def write_worker_failure(
    output_fd, worker_receipt_fd, worker_receipt_identity, secret,
    base, phase, error, store, report_written, worker_receipt_written,
):
    bodies_opened = 0 if store is None else store.body_opened_count
    body_bytes = 0 if store is None else store.body_bytes_read
    close_verified = 0 if store is None else store.close_verified_count
    value = dict(base)
    value.update(
        status="FAILED_OR_PARTIAL_C1_NUMERIC_CAMERA_WORKER",
        passed=False,
        terminal_authority=False,
        failed_phase=phase,
        error_type=type(error).__name__,
        error=str(error),
        traceback=traceback.format_exc(),
        report_written=report_written,
        worker_receipt_written=worker_receipt_written,
        c1_tensor_bodies_read=bodies_opened,
        c1_tensor_bodies_close_verified=close_verified,
        c1_tensor_body_bytes_read=body_bytes,
        completed_utc=utc(),
    )
    # A post-receipt failure is represented by the nonzero child exit and the
    # parent's fail-closed lock.  Never create or reopen another worker path.
    if not worker_receipt_written:
        write_prebound_json(
            output_fd, WORKER_RECEIPT_NAME, worker_receipt_fd,
            worker_receipt_identity, value, secret,
        )


def formal_worker_run(args):
    """Run only under the exact external supervisor and publish pending evidence."""
    started_monotonic = time.monotonic()
    base = {
        "schema": "s45b-c1-numeric-camera-guard-worker-receipt-v3",
        "status": "WORKER_STARTED_NO_TERMINAL_AUTHORITY",
        "row": "C1",
        "passed": False,
        "terminal_authority": False,
        "worker_pid": os.getpid(),
        "supervisor_pid": args.supervisor_pid,
        "started_utc": utc(),
        "attempt": 1,
        "automatic_retries": 0,
        "worker_sha256": args.self_sha256,
        "supervisor_sha256": args.supervisor_sha256,
        "primary_source_review_sha256": args.primary_source_review_sha256,
        "adversarial_source_review_sha256": args.adversarial_source_review_sha256,
        "binding_sha256": args.binding_sha256,
        "binding_review_sha256": args.binding_review_sha256,
        "governance_attestation_sha256": args.governance_attestation_sha256,
        "runtime_interpreter_binding_sha256": args.runtime_interpreter_binding_sha256,
        "pixel_bodies_opened": 0,
        "pixels_decoded": 0,
        "images_viewed": 0,
        "model_renderer_generation_runs": 0,
    }
    parent_fd = args.parent_fd
    lock_fd = args.lock_fd
    output_fd = args.output_fd
    capability_fd = args.capability_fd
    worker_source_fd = args.worker_source_fd
    report_fd = args.report_fd
    worker_receipt_fd = args.worker_receipt_fd
    report_identity = (args.report_dev, args.report_ino, args.report_mode)
    worker_receipt_identity = (
        args.worker_receipt_dev, args.worker_receipt_ino, args.worker_receipt_mode,
    )
    worker_source_identity = (
        args.worker_source_dev, args.worker_source_ino, args.worker_source_mode,
    )
    capability = None
    store = None
    phase = "SUPERVISOR_CAPABILITY_AND_INHERITED_FD_VALIDATION"
    report_written = False
    worker_receipt_written = False
    try:
        require(os.getppid() == args.supervisor_pid and args.supervisor_pid > 1,
                "Formal worker parent is not the declared supervisor")
        fds = (
            parent_fd, lock_fd, output_fd, capability_fd, worker_source_fd,
            report_fd, worker_receipt_fd,
        )
        require(all(type(fd) is int and fd >= 3 for fd in fds) and len(set(fds)) == 7,
                "Formal worker requires seven distinct inherited descriptors")
        capability = os.read(capability_fd, 33)
        require(
            len(capability) == 32 and os.read(capability_fd, 1) == b""
            and hashlib.sha256(capability).hexdigest() == args.capability_sha256,
            "Supervisor capability pipe differs",
        )
        os.close(capability_fd)
        capability_fd = -1

        parent_identity = (args.parent_dev, args.parent_ino, args.parent_mode)
        lock_identity = (args.lock_dev, args.lock_ino, args.lock_mode)
        output_identity = (args.output_dev, args.output_ino, args.output_mode)
        source_binding = verify_inherited_worker_source(
            worker_source_fd, worker_source_identity,
            args.self_sha256, args.worker_source_bytes,
        )
        verify_prebound_artifact(
            output_fd, REPORT_NAME, report_fd, report_identity, require_empty=True,
        )
        verify_prebound_artifact(
            output_fd, WORKER_RECEIPT_NAME, worker_receipt_fd,
            worker_receipt_identity, require_empty=True,
        )
        verify_directory_lease(
            parent_fd, HERE, parent_identity,
            output_fd, FORMAL_OUT.name, output_identity,
        )
        verify_lock_lease(
            parent_fd, HERE, parent_identity, lock_fd, LOCK.name,
            lock_identity, args.lock_sha256, args.lock_bytes,
        )
        lock_doc = json.loads(os.pread(lock_fd, args.lock_bytes, 0).decode("utf-8"))
        require(
            lock_doc.get("schema") == "s45b-c1-numeric-camera-guard-attempt-lease-v4"
            and lock_doc.get("capability_sha256") == args.capability_sha256
            and lock_doc.get("supplied_identities", {}).get("governance_attestation")
            == args.governance_attestation_sha256
            and lock_doc.get("runtime_interpreter_binding_sha256")
            == args.runtime_interpreter_binding_sha256
            and lock_doc.get("runtime_capability_preflight", {}).get("status")
            == "PASS_CAPABILITY_PROBE_ONLY_BEFORE_ATTEMPT_COMMIT",
            "Capability or governance identity is not bound in the permanent attempt lock",
        )

        phase = "POST_COMMIT_COMPLETE_IDENTITY_RECHECK"
        preflight = committed_worker_preflight(
            args, parent_fd, parent_identity,
            lock_fd, lock_identity, args.lock_sha256, args.lock_bytes,
            output_fd, output_identity,
            report_fd, report_identity, worker_receipt_fd, worker_receipt_identity,
        )

        phase = "SELECTED_CAMERA_TENSOR_BODY_READ_AND_NUMERIC_GUARD"
        store = CameraTensorStore(
            preflight["docs"]["archive_manifest"], C1_ARCHIVE_MANIFEST.parent,
            preflight["deadline"],
        )
        batches, commits = decode_selected_cameras(preflight["captures"], store)
        result = evaluate_numeric_guard(batches, commits)
        numeric_verdict = result.pop("status")
        require(
            numeric_verdict == "PASS_C1_REQUESTED_CAMERA_INPUT_CONDITION_GUARD_ONLY",
            "Numeric guard returned an unknown worker verdict",
        )
        tensor_identities = store.identities()

        phase = "TENSOR_CLOSE_AND_FINAL_SOURCE_REVALIDATION"
        close_verified = store.close(verify=True)
        unchanged, close_records = same_records(
            preflight["records"], preflight["deadline"],
        )
        require(unchanged, "A source or bound metadata identity changed before worker evidence")
        verify_directory_lease(
            parent_fd, HERE, parent_identity,
            output_fd, FORMAL_OUT.name, output_identity,
        )
        verify_lock_lease(
            parent_fd, HERE, parent_identity, lock_fd, LOCK.name,
            lock_identity, args.lock_sha256, args.lock_bytes,
        )

        phase = "PENDING_REPORT_WRITE"
        report = dict(result)
        report.update(
            schema="s45b-c1-numeric-camera-guard-worker-report-v3",
            status="C1_REQUESTED_CAMERA_INPUT_CONDITION_RESULT_PENDING_EXTERNAL_SUPERVISOR_SEAL",
            passed=False,
            terminal_authority=False,
            row="C1",
            numeric_worker_verdict=numeric_verdict,
            worker_sha256=args.self_sha256,
            supervisor_sha256=args.supervisor_sha256,
            primary_source_review_sha256=args.primary_source_review_sha256,
            adversarial_source_review_sha256=args.adversarial_source_review_sha256,
            binding_sha256=args.binding_sha256,
            binding_review_sha256=args.binding_review_sha256,
            governance_attestation_sha256=args.governance_attestation_sha256,
            runtime_interpreter_binding_sha256=args.runtime_interpreter_binding_sha256,
            executed_worker_source_binding=source_binding,
            archive_manifest_sha256=preflight["binding"]["upstream"]["archive_manifest"]["sha256"],
            archive_events_sha256=preflight["binding"]["upstream"]["archive_events"]["sha256"],
            s45_result_review_sha256=preflight["binding"]["upstream"]["s45_result_review"]["sha256"],
            event_chain=preflight["event_summary"],
            camera_tensor_identities=tensor_identities,
            c1_tensor_bodies_read=store.body_opened_count,
            c1_tensor_bodies_close_verified=close_verified,
            c1_tensor_body_bytes_read=store.body_bytes_read,
            external_supervisor_exit_and_terminal_seal_required=True,
            evidence_boundary=(
                "Requested archived c2w/K input-condition worker evidence only; no pixels, "
                "quality, rendered-camera obedience, score, method gain, causal claim, or novelty"
            ),
        )
        report_sha256, _ = write_prebound_json(
            output_fd, REPORT_NAME, report_fd, report_identity, report, capability,
        )
        report_written = True
        verify_directory_lease(
            parent_fd, HERE, parent_identity,
            output_fd, FORMAL_OUT.name, output_identity,
        )
        verify_lock_lease(
            parent_fd, HERE, parent_identity, lock_fd, LOCK.name,
            lock_identity, args.lock_sha256, args.lock_bytes,
        )

        phase = "PENDING_WORKER_RECEIPT_WRITE"
        worker_receipt = dict(base)
        worker_receipt.update(
            status="C1_NUMERIC_CAMERA_WORKER_EVIDENCE_WRITTEN_PENDING_PROCESS_EXIT_AND_SUPERVISOR_SEAL",
            passed=False,
            terminal_authority=False,
            numeric_worker_verdict=numeric_verdict,
            report_sha256=report_sha256,
            c1_tensor_bodies_read=store.body_opened_count,
            c1_tensor_bodies_close_verified=close_verified,
            c1_tensor_body_bytes_read=store.body_bytes_read,
            sources_and_bound_metadata_unchanged_at_worker_close=True,
            worker_recheck_identity_records=preflight["recheck_records"],
            worker_close_identity_records=close_records,
            elapsed_seconds=time.monotonic() - started_monotonic,
            completed_utc=utc(),
        )
        worker_receipt.update(
            executed_worker_source_binding=source_binding,
            report_artifact_identity=list(report_identity),
            worker_receipt_artifact_identity=list(worker_receipt_identity),
        )
        write_prebound_json(
            output_fd, WORKER_RECEIPT_NAME, worker_receipt_fd,
            worker_receipt_identity, worker_receipt, capability,
        )
        worker_receipt_written = True

        phase = "POST_WORKER_RECEIPT_CLOSE_REVALIDATION"
        unchanged, final_records = same_records(
            preflight["records"], preflight["deadline"],
        )
        require(unchanged, "A source or bound metadata identity changed after worker receipt")
        verify_directory_lease(
            parent_fd, HERE, parent_identity,
            output_fd, FORMAL_OUT.name, output_identity,
        )
        verify_lock_lease(
            parent_fd, HERE, parent_identity, lock_fd, LOCK.name,
            lock_identity, args.lock_sha256, args.lock_bytes,
        )
        verify_inherited_worker_source(
            worker_source_fd, worker_source_identity,
            args.self_sha256, args.worker_source_bytes,
        )
        verify_prebound_artifact(
            output_fd, REPORT_NAME, report_fd, report_identity,
        )
        verify_prebound_artifact(
            output_fd, WORKER_RECEIPT_NAME, worker_receipt_fd,
            worker_receipt_identity,
        )
        require(
            all(entry_absent(output_fd, name) for name in (
                WORKER_FAILURE_NAME, SUPERVISOR_RECEIPT_NAME,
                BARRIER_NAME, TERMINAL_SEAL_NAME, TERMINAL_SEAL_STAGING_NAME,
                TERMINAL_FAILURE_NAME,
            )),
            "A supervisor/terminal artifact appeared before worker return",
        )
        return 0
    except BaseException as error:
        if store is not None:
            try:
                store.close(verify=True)
            except BaseException as close_error:
                error = RuntimeError(
                    str(error) + "; tensor close verification: " + str(close_error)
                )
        try:
            write_worker_failure(
                output_fd, worker_receipt_fd, worker_receipt_identity, capability,
                base, phase, error, store, report_written, worker_receipt_written,
            )
        except BaseException:
            pass
        return 2
    finally:
        for fd in (
            capability_fd, report_fd, worker_receipt_fd,
            worker_source_fd, output_fd, lock_fd, parent_fd,
        ):
            if type(fd) is int and fd >= 0:
                try:
                    os.close(fd)
                except OSError:
                    pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic-self-test", action="store_true")
    args = parser.parse_args()
    if args.synthetic_self_test:
        print(json.dumps(synthetic_selftest(), sort_keys=True, allow_nan=False))
        return 0
    require(False,
            "V11 worker has no formal pathname CLI: the reviewed supervisor forks its "
            "already-running interpreter and invokes held-source code in memory")


if __name__ == "__main__":
    raise SystemExit(main())
