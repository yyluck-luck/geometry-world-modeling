#!/usr/bin/env python3
"""One-shot independent numeric recomputation of sealed B0 attempt01.

This source does not import the primary B0 scorer and never decodes or emits an
image.  Execution is gated on a different-author review of this exact source.
"""
from __future__ import annotations

import argparse
import ctypes
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import time
import traceback


HERE = Path(__file__).resolve().parent
SELF = Path(__file__).resolve()
PROTOCOL = HERE / "PROTOCOL.md"
PROTOCOL_SHA256 = "e3086d3ea373295b83f08dbba919d016a96243e31ebf15142bb609de0d68f0b7"
SOURCE_REVIEW = HERE / "SOURCE_REVIEW.json"
AUTHOR_ROLE = "/root"

SEALED_ATTEMPT = HERE.parent / "B0_score_attempt_01"
SEALED_RECEIPT = SEALED_ATTEMPT / "receipt.json"
SEALED_RECEIPT_SHA256 = "93c90e24e404aa1f87e111ed3a7c79d51de9d9bf35babd060ac807af9d99f2ad"
SEALED_REPORT = SEALED_ATTEMPT / "report.json"
SEALED_REPORT_SHA256 = "13b190b126e925ae18f43728781c323d5cece8d9a591b73e6e9bf3a865aa8a8e"

FINAL_OUTPUT = HERE / "execution_01"
LOCK_PATH = HERE / ".independent_recompute.lock"
STAGING_PREFIX = ".execution_01.staging-"
HEX = re.compile(r"^[0-9a-f]{64}$")
PIXEL_SHAPE = (576, 576, 3)
PIXEL_BYTES = 576 * 576 * 3
PIXEL_COUNT = 147456
RGB_SCALAR_COUNT = 442368
FULL_FRAME_PIXEL_COUNT = 576 * 576
FULL_FRAME_RGB_SCALAR_COUNT = 576 * 576 * 3
MSE_THRESHOLD = 0.01
DEADLINE_SECONDS = 300
RENAME_EXCL = 0x00000004
CLAIM_BOUNDARY = (
    "Numeric agreement with one sealed B0 report only; no visual quality, rendered camera "
    "obedience, repeatability, C1/C2 cohort confirmation, causal attribution, method gain, "
    "or novelty conclusion."
)
REGIONS = (
    ("R1", (0, 192, 0, 192)),
    ("R2", (0, 192, 384, 576)),
    ("R3", (192, 384, 0, 192)),
    ("R4", (192, 384, 384, 576)),
)
PAIRS = ((1, 7), (2, 6), (3, 5))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_utc(raw, label: str) -> datetime:
    require(type(raw) is str and bool(raw), label + " must be a nonempty UTC timestamp")
    try:
        value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(label + " is not ISO-8601") from error
    require(value.tzinfo is not None and value.utcoffset() == timezone.utc.utcoffset(value),
            label + " must be timezone-aware UTC")
    return value


def stat_identity(value) -> tuple[int, int, int, int, int, int]:
    return (
        value.st_dev, value.st_ino, value.st_mode, value.st_size,
        value.st_mtime_ns, value.st_ctime_ns,
    )


def sha256_path(path: Path, *, deadline: float | None = None) -> str:
    before = path.stat()
    require(stat.S_ISREG(before.st_mode), "Identity input is not a regular file: " + str(path))
    digest = hashlib.sha256()
    count = 0
    with path.open("rb") as handle:
        while block := handle.read(8 * 1024 * 1024):
            digest.update(block)
            count += len(block)
            if deadline is not None:
                require(time.monotonic() <= deadline, "Independent recomputation deadline reached")
    after = path.stat()
    require(count == before.st_size and stat_identity(before) == stat_identity(after),
            "Identity input changed while hashing: " + str(path))
    return digest.hexdigest()


def read_json(path: Path, expected_sha256: str, label: str, *, deadline: float):
    require(HEX.fullmatch(expected_sha256 or "") is not None, label + " SHA-256 is malformed")
    require(path.is_absolute() and path.resolve() == path and path.is_file() and not path.is_symlink(),
            label + " must be a canonical regular non-symlink file")
    require(path.stat().st_size <= 64 * 1024 * 1024, label + " exceeds bounded JSON scope")
    actual = sha256_path(path, deadline=deadline)
    require(actual == expected_sha256, label + " SHA-256 differs")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(sha256_path(path, deadline=deadline) == actual, label + " changed while parsing")
    return value


def json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def path_entry_exists(path: Path) -> bool:
    """Return true for every destination entry, including a broken symlink."""
    return os.path.lexists(path)


def publish_directory_exclusive(staging: Path, destination: Path) -> None:
    """Atomically publish a same-parent directory without replacing any entry."""
    require(staging.parent == HERE and destination.parent == HERE,
            "Independent recomputation publication must stay in its frozen parent")
    before = os.stat(staging, follow_symlinks=False)
    require(stat.S_ISDIR(before.st_mode) and not staging.is_symlink(),
            "Independent recomputation staging entry is not a real directory")
    require(not path_entry_exists(destination),
            "Independent recomputation destination already exists before publication")
    libc = ctypes.CDLL(None, use_errno=True)
    require(hasattr(libc, "renamex_np"),
            "This frozen macOS publication requires renamex_np")
    renamex_np = libc.renamex_np
    renamex_np.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
    renamex_np.restype = ctypes.c_int
    ctypes.set_errno(0)
    result = renamex_np(
        os.fsencode(str(staging)), os.fsencode(str(destination)), RENAME_EXCL
    )
    if result != 0:
        error_number = ctypes.get_errno()
        raise OSError(error_number, os.strerror(error_number), str(destination))
    after = os.stat(destination, follow_symlinks=False)
    require((after.st_dev, after.st_ino, after.st_mode)
            == (before.st_dev, before.st_ino, before.st_mode)
            and not path_entry_exists(staging)
            and stat.S_ISDIR(after.st_mode)
            and not destination.is_symlink(),
            "Published recomputation directory identity differs from staging")
    fsync_directory(HERE)


def write_new(path: Path, value) -> None:
    payload = json_bytes(value)
    require(not path.exists(), "Refusing to replace output: " + str(path))
    temporary = path.parent / ("." + path.name + ".write-%d-%d" % (os.getpid(), time.time_ns()))
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path, follow_symlinks=False)
        temporary.unlink()
        fsync_directory(path.parent)
    except BaseException:
        if temporary.exists():
            temporary.unlink()
        raise


def verify_source_gate(args, deadline: float):
    require(HEX.fullmatch(args.source_sha256 or "") is not None, "Source SHA-256 is malformed")
    require(sha256_path(SELF, deadline=deadline) == args.source_sha256,
            "Recomputer source differs from caller-bound SHA-256")
    require(sha256_path(PROTOCOL, deadline=deadline) == PROTOCOL_SHA256,
            "Recomputation protocol SHA-256 differs")
    review = read_json(SOURCE_REVIEW, args.source_review_sha256,
                       "independent recomputer source review", deadline=deadline)
    require(
        review.get("schema") == "s42-b0-independent-recompute-source-review-v1"
        and review.get("status") == "PASS_S42_B0_INDEPENDENT_RECOMPUTE_SOURCE_REVIEW"
        and Path(review.get("source_path", "")).resolve() == SELF
        and review.get("source_sha256") == args.source_sha256
        and Path(review.get("protocol_path", "")).resolve() == PROTOCOL
        and review.get("protocol_sha256") == PROTOCOL_SHA256
        and review.get("sealed_receipt_path") == str(SEALED_RECEIPT)
        and review.get("sealed_receipt_sha256") == SEALED_RECEIPT_SHA256
        and review.get("sealed_report_path") == str(SEALED_REPORT)
        and review.get("sealed_report_sha256") == SEALED_REPORT_SHA256
        and review.get("executed") is False
        and review.get("images_viewed") is False
        and review.get("tensor_or_image_payload_bodies_read") is False
        and review.get("blocking_findings") == []
        and review.get("author_role") == AUTHOR_ROLE
        and type(review.get("reviewer_role")) is str
        and bool(review["reviewer_role"])
        and review["reviewer_role"] != AUTHOR_ROLE,
        "Exact recomputer source lacks a different-author static PASS review",
    )
    parse_utc(review.get("completed_utc"), "source review completed_utc")
    return review


def load_sealed_records(deadline: float):
    receipt = read_json(SEALED_RECEIPT, SEALED_RECEIPT_SHA256,
                        "sealed B0 receipt", deadline=deadline)
    require(
        receipt.get("schema") == "s42-b0-blind-score-receipt-v1"
        and receipt.get("status") == "PASS_B0_MACHINE_SCORE_SINGLE_ROW_COHORT_INCOMPLETE"
        and receipt.get("technically_valid") is True
        and receipt.get("attempt") == 1
        and receipt.get("out") == str(SEALED_ATTEMPT)
        and receipt.get("report_path") == str(SEALED_REPORT)
        and receipt.get("report_sha256") == SEALED_REPORT_SHA256,
        "Sealed B0 receipt does not bind the frozen successful attempt01 report",
    )
    report = read_json(SEALED_REPORT, SEALED_REPORT_SHA256,
                       "sealed B0 report", deadline=deadline)
    require(
        report.get("schema") == "s42-b0-blind-score-report-v1"
        and report.get("row") == "B0"
        and report.get("attempt") == 1
        and report.get("row_event") is report.get("score", {}).get("event_MSE_gt_0_01"),
        "Sealed B0 report top-level identity or event closure differs",
    )
    identities = report.get("score", {}).get("authoritative_pixel_identities")
    require(type(identities) is list and len(identities) == 9,
            "Sealed report must name exactly nine authoritative pixel identities")
    archive_manifest_path = Path(report.get("archive_manifest_path", ""))
    require(archive_manifest_path.is_absolute() and archive_manifest_path.name == "manifest.json",
            "Sealed report archive path is malformed")
    tensor_directory = archive_manifest_path.parent / "tensors"
    checked = []
    for expected_id, identity in enumerate(identities):
        require(type(identity) is dict and set(identity) == {
            "id", "tensor_descriptor_sha256", "tensor_body_sha256", "blob"
        }, "Authoritative pixel identity fields differ")
        descriptor_sha = identity.get("tensor_descriptor_sha256")
        body_sha = identity.get("tensor_body_sha256")
        blob = Path(identity.get("blob", ""))
        require(
            type(identity.get("id")) is int and identity["id"] == expected_id
            and HEX.fullmatch(descriptor_sha or "") is not None
            and HEX.fullmatch(body_sha or "") is not None
            and blob.is_absolute() and blob.resolve() == blob
            and blob.parent == tensor_directory
            and blob.name == descriptor_sha + ".bin",
            "Authoritative pixel identity %d is not canonical" % expected_id,
        )
        checked.append({
            "id": expected_id,
            "tensor_descriptor_sha256": descriptor_sha,
            "tensor_body_sha256": body_sha,
            "blob": blob,
        })
    return receipt, report, checked


def read_fd_snapshot(fd: int, expected_size: int, deadline: float):
    before = os.fstat(fd)
    require(stat.S_ISREG(before.st_mode) and before.st_size == expected_size,
            "Pixel body is not a regular file of the exact frozen length")
    digest = hashlib.sha256()
    pieces = []
    offset = 0
    while offset < expected_size:
        require(time.monotonic() <= deadline, "Independent recomputation deadline reached")
        block = os.pread(fd, min(8 * 1024 * 1024, expected_size - offset), offset)
        require(bool(block), "Unexpected pixel body EOF")
        pieces.append(block)
        digest.update(block)
        offset += len(block)
    require(os.pread(fd, 1, expected_size) == b"", "Pixel body exceeds exact frozen length")
    after = os.fstat(fd)
    require(stat_identity(before) == stat_identity(after), "Pixel body changed during same-FD read")
    snapshot = b"".join(pieces)
    require(len(snapshot) == expected_size and hashlib.sha256(snapshot).hexdigest() == digest.hexdigest(),
            "Pixel snapshot differs from its streaming hash")
    return snapshot, digest.hexdigest(), stat_identity(before)


def open_pixels(identity, np, deadline: float):
    path = identity["blob"]
    require(path.is_file() and not path.is_symlink(), "Pixel blob is missing, linked, or nonregular")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        opened = os.fstat(fd)
        path_stat = os.stat(path, follow_symlinks=False)
        require(stat.S_ISREG(opened.st_mode) and stat.S_ISREG(path_stat.st_mode),
                "Pixel blob is not a regular file")
        require((opened.st_dev, opened.st_ino) == (path_stat.st_dev, path_stat.st_ino),
                "Opened pixel blob differs from its canonical path")
        snapshot, body_sha, opened_identity = read_fd_snapshot(fd, PIXEL_BYTES, deadline)
        require(body_sha == identity["tensor_body_sha256"],
                "Pixel body SHA-256 differs from the sealed report")
        array = np.frombuffer(snapshot, dtype=np.dtype("<u1")).reshape(PIXEL_SHAPE, order="C")
        array.setflags(write=False)
        handle = {
            "id": identity["id"],
            "fd": fd,
            "path": path,
            "opened_identity": opened_identity,
            "snapshot": snapshot,
            "array": array,
            "body_sha256": body_sha,
            "tensor_descriptor_sha256": identity["tensor_descriptor_sha256"],
        }
        fd = -1
        return handle
    finally:
        if fd >= 0:
            os.close(fd)


def close_pixel_handles(handles, *, deadline: float, verify: bool) -> int:
    count = len(handles)
    first_error = None
    for handle in handles:
        try:
            if verify:
                current = os.fstat(handle["fd"])
                require(stat_identity(current) == handle["opened_identity"],
                        "Pixel body metadata changed before recomputation seal")
                _, closing_sha, closing_identity = read_fd_snapshot(handle["fd"], PIXEL_BYTES, deadline)
                path_stat = os.stat(handle["path"], follow_symlinks=False)
                require(
                    closing_identity == handle["opened_identity"]
                    and closing_sha == handle["body_sha256"]
                    and (path_stat.st_dev, path_stat.st_ino) == (current.st_dev, current.st_ino),
                    "Pixel body or canonical path changed before recomputation seal",
                )
        except BaseException as error:
            if first_error is None:
                first_error = error
        finally:
            os.close(handle["fd"])
    handles.clear()
    if first_error is not None:
        raise first_error
    return count


def metric_record(mse: float, pixels: int, scalars: int):
    require(math.isfinite(mse) and mse >= 0.0, "Recomputed MSE is nonfinite or negative")
    psnr = None if mse == 0.0 else -10.0 * math.log10(mse)
    return {
        "mse_float64": mse,
        "mse_float64_hex": mse.hex(),
        "psnr_db_float64": psnr,
        "psnr_db_display_when_zero": "+inf" if mse == 0.0 else None,
        "pixels": pixels,
        "rgb_scalars": scalars,
    }


def mse_outer4(first, second, np):
    total = 0.0
    scalars = 0
    regions = {}
    for name, (y0, y1, x0, x1) in REGIONS:
        left = np.asarray(first[y0:y1, x0:x1], dtype=np.float64) / 255.0
        right = np.asarray(second[y0:y1, x0:x1], dtype=np.float64) / 255.0
        square_sum = float(np.sum(np.square(right - left), dtype=np.float64))
        count = int(left.size)
        mse = square_sum / count
        regions[name] = metric_record(mse, (y1 - y0) * (x1 - x0), count)
        total += square_sum
        scalars += count
    require(scalars == RGB_SCALAR_COUNT, "M_outer4 scalar count differs")
    return total / scalars, regions


def compare_record(label: str, actual, expected, mismatches) -> None:
    if type(expected) is not dict:
        mismatches.append({"field": label, "reason": "sealed metric record is not an object"})
        return
    expected_mse = expected.get("mse_float64")
    expected_hex = expected.get("mse_float64_hex")
    expected_psnr = expected.get("psnr_db_float64")
    numeric_mse = type(expected_mse) in (int, float) and type(expected_mse) is not bool
    mse_self_consistent = numeric_mse and float(expected_mse).hex() == expected_hex
    psnr_equal = (
        actual["psnr_db_float64"] is None and expected_psnr is None
        or actual["psnr_db_float64"] is not None
        and type(expected_psnr) in (int, float) and type(expected_psnr) is not bool
        and actual["psnr_db_float64"].hex() == float(expected_psnr).hex()
    )
    equal = (
        mse_self_consistent
        and actual["mse_float64_hex"] == expected_hex
        and psnr_equal
        and actual["psnr_db_display_when_zero"] == expected.get("psnr_db_display_when_zero")
        and actual["pixels"] == expected.get("pixels")
        and actual["rgb_scalars"] == expected.get("rgb_scalars")
    )
    if not equal:
        mismatches.append({"field": label, "reason": "numeric record differs",
                           "recomputed": actual, "sealed": expected})


def recompute(report, identities, np, deadline: float):
    handles = []
    completed = False
    try:
        for identity in identities:
            handles.append(open_pixels(identity, np, deadline))
        require([handle["id"] for handle in handles] == list(range(9)),
                "Pixel handle ID order differs")
        bodies = [handle["body_sha256"] for handle in handles]
        copy_guard_pass = not (
            all(value == bodies[0] for value in bodies[1:])
            or len(set(bodies[1:])) == 1
        )
        arrays = [handle["array"] for handle in handles]
        primary_mse, region_records = mse_outer4(arrays[0], arrays[8], np)
        primary = metric_record(primary_mse, PIXEL_COUNT, RGB_SCALAR_COUNT)
        full_delta = (
            np.asarray(arrays[8], dtype=np.float64) / 255.0
            - np.asarray(arrays[0], dtype=np.float64) / 255.0
        )
        full_frame_mse = float(
            np.sum(np.square(full_delta), dtype=np.float64)
        ) / int(full_delta.size)
        require(int(full_delta.size) == FULL_FRAME_RGB_SCALAR_COUNT,
                "Full-frame RGB scalar count differs")
        full_frame = metric_record(
            full_frame_mse, FULL_FRAME_PIXEL_COUNT, FULL_FRAME_RGB_SCALAR_COUNT
        )
        pair_records = {}
        for left, right in PAIRS:
            mse, _ = mse_outer4(arrays[left], arrays[right], np)
            pair_records["%d_%d" % (left, right)] = metric_record(
                mse, PIXEL_COUNT, RGB_SCALAR_COUNT
            )
        event = primary_mse > MSE_THRESHOLD
        equality = primary_mse == MSE_THRESHOLD
        used_count = close_pixel_handles(handles, deadline=deadline, verify=True)
        require(used_count == 9, "Exactly nine same-FD pixel closures are required")
        completed = True
    finally:
        if handles:
            close_pixel_handles(handles, deadline=deadline, verify=False)
    require(completed, "Independent recomputation did not close all pixel identities")

    sealed_score = report.get("score", {})
    mismatches = []
    if not copy_guard_pass:
        mismatches.append({"field": "copy_guard", "reason": "frozen degeneracy condition is true"})
    compare_record("score.primary", primary, sealed_score.get("primary"), mismatches)
    compare_record(
        "score.full_frame_diagnostic",
        full_frame,
        sealed_score.get("full_frame_diagnostic"),
        mismatches,
    )
    sealed_regions = sealed_score.get("per_region_diagnostic")
    if type(sealed_regions) is not dict or set(sealed_regions) != {name for name, _ in REGIONS}:
        mismatches.append({"field": "score.per_region_diagnostic", "reason": "region keys differ"})
    else:
        for name, _ in REGIONS:
            compare_record("score.per_region_diagnostic." + name,
                           region_records[name], sealed_regions[name], mismatches)
    sealed_pairs = sealed_score.get("generated_only_pair_diagnostic_no_GT")
    if type(sealed_pairs) is not dict or set(sealed_pairs) != set(pair_records):
        mismatches.append({"field": "score.generated_only_pair_diagnostic_no_GT",
                           "reason": "diagnostic pair keys differ"})
    else:
        for name in sorted(pair_records):
            compare_record("score.generated_only_pair_diagnostic_no_GT." + name,
                           pair_records[name], sealed_pairs[name], mismatches)
    comparisons = (
        ("score.event_MSE_gt_0_01", event, sealed_score.get("event_MSE_gt_0_01")),
        ("score.equality_is_not_event", equality, sealed_score.get("equality_is_not_event")),
        ("row_event", event, report.get("row_event")),
        ("row_status",
         "B0_TECHNICALLY_VALID_SEVERE_DISCREPANCY_EVENT" if event
         else "B0_TECHNICALLY_VALID_NO_SEVERE_DISCREPANCY_EVENT",
         report.get("row_status")),
    )
    for field, actual, expected in comparisons:
        if type(actual) is bool:
            equal = expected is actual
        else:
            equal = expected == actual
        if not equal:
            mismatches.append({"field": field, "reason": "value differs",
                               "recomputed": actual, "sealed": expected})
    return {
        "copy_guard_pass": copy_guard_pass,
        "primary": primary,
        "per_region": region_records,
        "full_frame_diagnostic": full_frame,
        "fixed_generated_only_pairs_no_GT": pair_records,
        "event_MSE_gt_0_01": event,
        "equality_is_not_event": equality,
        "mismatches": mismatches,
    }


def closing_identity_check(args, deadline: float) -> None:
    require(sha256_path(SELF, deadline=deadline) == args.source_sha256,
            "Recomputer source changed before result seal")
    require(sha256_path(PROTOCOL, deadline=deadline) == PROTOCOL_SHA256,
            "Recomputation protocol changed before result seal")
    require(sha256_path(SOURCE_REVIEW, deadline=deadline) == args.source_review_sha256,
            "Source review changed before result seal")
    require(sha256_path(SEALED_RECEIPT, deadline=deadline) == SEALED_RECEIPT_SHA256,
            "Sealed B0 receipt changed before result seal")
    require(sha256_path(SEALED_REPORT, deadline=deadline) == SEALED_REPORT_SHA256,
            "Sealed B0 report changed before result seal")


def create_staging() -> Path:
    require(not path_entry_exists(FINAL_OUTPUT),
            "Independent recomputation execution_01 destination entry already exists")
    require(not any(path.name.startswith(STAGING_PREFIX) for path in HERE.iterdir()),
            "An incomplete independent recomputation staging directory exists")
    staging = HERE / (STAGING_PREFIX + "%d-%d" % (os.getpid(), time.time_ns()))
    staging.mkdir(mode=0o700, parents=False, exist_ok=False)
    fsync_directory(HERE)
    return staging


def audit(args, staging: Path) -> int:
    started = time.monotonic()
    deadline = started + DEADLINE_SECONDS
    receipt = {
        "schema": "s42-b0-independent-recompute-receipt-v1",
        "status": "CHECKING_FROZEN_INPUTS",
        "started_utc": utc(),
        "source_path": str(SELF),
        "source_sha256": args.source_sha256,
        "protocol_path": str(PROTOCOL),
        "protocol_sha256": PROTOCOL_SHA256,
        "source_review_path": str(SOURCE_REVIEW),
        "source_review_sha256": args.source_review_sha256,
        "sealed_receipt_path": str(SEALED_RECEIPT),
        "sealed_receipt_sha256": SEALED_RECEIPT_SHA256,
        "sealed_report_path": str(SEALED_REPORT),
        "sealed_report_sha256": SEALED_REPORT_SHA256,
        "audit_completed": False,
        "images_viewed_or_emitted": 0,
        "model_generation_renderer_readback_calls": 0,
        "scientific_scope": "Independent numeric recomputation of one sealed B0 row only",
        "claim_boundary": CLAIM_BOUNDARY,
    }
    audit_report = None
    try:
        source_review = verify_source_gate(args, deadline)
        _, sealed_report, identities = load_sealed_records(deadline)
        import numpy as np
        require(np.__version__ == "1.26.4", "Independent recomputer requires NumPy 1.26.4")
        recomputed = recompute(sealed_report, identities, np, deadline)
        closing_identity_check(args, deadline)
        passed = not recomputed["mismatches"]
        status = "PASS_EXACT_B0_NUMERIC_RECOMPUTE" if passed else "MISMATCH_B0_NUMERIC_RECOMPUTE"
        audit_report = {
            "schema": "s42-b0-independent-recompute-report-v1",
            "status": status,
            "completed_utc": utc(),
            "source_sha256": args.source_sha256,
            "protocol_sha256": PROTOCOL_SHA256,
            "source_review_sha256": args.source_review_sha256,
            "sealed_receipt_sha256": SEALED_RECEIPT_SHA256,
            "sealed_report_sha256": SEALED_REPORT_SHA256,
            "authoritative_pixel_identities": [
                {
                    "id": item["id"],
                    "tensor_descriptor_sha256": item["tensor_descriptor_sha256"],
                    "tensor_body_sha256": item["tensor_body_sha256"],
                    "blob": str(item["blob"]),
                }
                for item in identities
            ],
            "numeric_recomputation": recomputed,
            "images_viewed_or_emitted": 0,
            "model_generation_renderer_readback_calls": 0,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        receipt.update(status=status, audit_completed=True, exact_match=passed,
                       source_review_reviewer_role=source_review["reviewer_role"],
                       mismatch_count=len(recomputed["mismatches"]))
    except BaseException as error:
        audit_report = None
        receipt.update(
            status="FAILED_BEFORE_COMPLETE_B0_NUMERIC_RECOMPUTE",
            audit_completed=False,
            exact_match=False,
            error_type=type(error).__name__,
            error=str(error),
            traceback=traceback.format_exc(),
        )
    receipt["completed_utc"] = utc()
    receipt["elapsed_seconds"] = time.monotonic() - started
    receipt["deadline_seconds"] = DEADLINE_SECONDS
    complete = (
        audit_report is not None
        and receipt.get("audit_completed") is True
        and receipt.get("status") in {
            "PASS_EXACT_B0_NUMERIC_RECOMPUTE",
            "MISMATCH_B0_NUMERIC_RECOMPUTE",
        }
    )
    if complete:
        report_payload = json_bytes(audit_report)
        report_sha = hashlib.sha256(report_payload).hexdigest()
        receipt["report_path"] = str(FINAL_OUTPUT / "report.json")
        receipt["report_sha256"] = report_sha
        write_new(staging / "report.json", audit_report)
        require(sha256_path(staging / "report.json", deadline=deadline) == report_sha,
                "Staged recomputation report SHA-256 differs")
    else:
        audit_report = None
        receipt["audit_completed"] = False
        receipt["exact_match"] = False
        require(not (staging / "report.json").exists(),
                "Incomplete recomputation may not expose a numeric report")
    write_new(staging / "receipt.json", receipt)
    return 0 if receipt.get("status") == "PASS_EXACT_B0_NUMERIC_RECOMPUTE" else (
        1 if receipt.get("status") == "MISMATCH_B0_NUMERIC_RECOMPUTE" else 2
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--source-review-sha256", required=True)
    args = parser.parse_args()
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    lock_fd = os.open(LOCK_PATH, flags, 0o600)
    with os.fdopen(lock_fd, "r+b", closefd=True) as lock_handle:
        require(stat.S_ISREG(os.fstat(lock_handle.fileno()).st_mode),
                "Independent recomputation lock is not regular")
        try:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError("Another independent recomputation holds the lock") from error
        staging = create_staging()
        result = audit(args, staging)
        require((staging / "receipt.json").is_file(), "Staging lacks a terminal receipt")
        fsync_directory(staging)
        if result == 2:
            fsync_directory(HERE)
            return result
        require((staging / "report.json").is_file(),
                "Completed recomputation staging lacks its numeric report")
        publish_directory_exclusive(staging, FINAL_OUTPUT)
        return result


if __name__ == "__main__":
    raise SystemExit(main())
