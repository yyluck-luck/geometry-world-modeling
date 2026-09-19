#!/usr/bin/env python3
"""Blind, machine-only B0 scorer for the frozen S40 full archive.

Preparation only.  A different-author source review, a successful independently
reviewed S40 readback, and a pre-score blindness attestation are mandatory.  This
program never opens a PNG/PIL image, emits no image, and does not import a model.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
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
CONTRACT = HERE / "B0_SCORING_CONTRACT.json"
CONTRACT_SHA256 = "1143f700855ab32df3d703fc91b2ff8707ca3dc3e217407156be9247d677c11b"
PROTOCOL = HERE / "PROTOCOL.md"
PROTOCOL_SHA256 = "89fb44e0b77a85a66fe611cd2f885fed0288229cbb027e04da25fc0631507b3f"
PREREG_RECEIPT = HERE / "receipt.json"
PREREG_RECEIPT_SHA256 = "5336c838de1714a6ab1f65be56312d21148d9dc6114162a7ee59497f3bbb2cf7"
SOURCE_REVIEW = HERE / "B0_SCORER_SOURCE_REVIEW.json"
ADVERSARIAL_SOURCE_REVIEW = HERE / "B0_SCORER_SOURCE_REVIEW_ADVERSARIAL.json"
BLINDNESS_ATTESTATION = HERE / "B0_BLINDNESS_ATTESTATION_PRE_SCORE.json"
BLINDNESS_TEMPLATE = HERE / "B0_BLINDNESS_ATTESTATION_TEMPLATE.json"
B0_SCORE_LOCK = HERE / ".b0_score.lock"
FROZEN_MANIFEST = ROOT / "work/S40_declared_variant_generation/review_attachment_01/manifest.json"
FROZEN_MANIFEST_SHA256 = "9951a78909a7d792dd536cea067c14e369cff776115a078d2f61c66c085cdebe"
GENERATION_RECEIPT = ROOT / "work/S40_declared_variant_generation/execution_01/receipt.json"
GENERATION_RECEIPT_SHA256 = "4c771df1e46f96e218b92f01339b55ebd056ef002fdc28e0083a5bb0907300d4"
GENERATION_WORKER_RECEIPT = ROOT / "work/S40_declared_variant_generation/execution_01/worker_receipt.json"
GENERATION_WORKER_RECEIPT_SHA256 = "a564a67e63036b3195390b5059476c1729c99e74bb0a8fe0ef26e0c1211b4911"
READBACK_SUPERVISOR_SHA256 = "f04b9bcd4a0e2908d2bc3ead9a732e16d4f4ef651a60541a87f37a7b37f2b238"
READBACK_SUPERVISOR_SOURCE = ROOT / "work/S40_result_readback/supervise_readback.py"
READBACK_SUPERVISOR_PROTOCOL = ROOT / "work/S40_result_readback/SUPERVISOR_PROTOCOL.md"
READBACK_SUPERVISOR_PROTOCOL_SHA256 = "e16832daf1fbda8f98e61da368cf00a319659f8d6970c79d582b0e35685827b3"
READBACK_SUPERVISOR_SOURCE_REVIEW = ROOT / "work/S40_result_readback/supervisor_source_review_v2.json"
READBACK_SUPERVISOR_REVIEW_SHA256 = "9c608a57a54e716103dbf83d4aca73151d8fafed8d0e0099802cd9daabf2ab1e"
READBACK_WORKER_SHA256 = "d4c22504569ad1fb1fcc74ea1da83b4f244f4de803f5d0fadc16e8da06777933"
READBACK_WORKER_SOURCE = ROOT / "work/S40_result_readback/readback.py"
READBACK_SOURCE_REVIEW = ROOT / "work/S40_result_readback/source_review_v3_3.json"
READBACK_SOURCE_REVIEW_SHA256 = "70d4c48a6940778247763c901637e18e231b926f4733ac8edb64923ef0240484"
READBACK_ADVERSARIAL_SOURCE_REVIEW = ROOT / "work/S40_result_readback/source_review_v3_3_adversarial.json"
READBACK_ADVERSARIAL_SOURCE_REVIEW_SHA256 = "8ca313e712eec18d275122c95181aff987ae1ff5ceb04a880af61bb41b5a3ec7"
READBACK_REVISION_RECEIPT = ROOT / "work/S40_result_readback/revision_v3_3_receipt.json"
READBACK_REVISION_RECEIPT_SHA256 = "bebc80b8fccf6e8699d4768f6ffab097bcc75f6bca4a7f101ef53e827b0e2e9d"
READBACK_SUPERVISOR_RECEIPT = ROOT / "work/S40_result_readback/supervision_02/receipt.json"
READBACK_SUPERVISOR_RECEIPT_SHA256 = "f69b903b2f2987547e7e612c1234eaa7e1d3caa86a8ce2f2e7bee9f04178a894"
READBACK_WORKER_RECEIPT = ROOT / "work/S40_result_readback/executed_02/receipt.json"
READBACK_WORKER_RECEIPT_SHA256 = "24bc325c4740589b548e0bbe7c9244cb57168f5a032af605f71b3cd09965f18e"
READBACK_REPORT = ROOT / "work/S40_result_readback/executed_02/report.json"
READBACK_REPORT_SHA256 = "a15e4264090361847a57516499d3bf4f1203de80bf26fbba5fd63f181ec5ea21"
READBACK_RESULT_REVIEW = ROOT / "work/S40_result_readback/supervision_02/independent_result_review.json"
READBACK_RESULT_REVIEW_SHA256 = "ef56ef5e49da7f3da5df873b92c5bc3f16197c2c460eaf4b2519289db787f6d5"
EXPECTED_INPUT_SHA256 = "12fc2c4ddfccee952d5390b147b813a8f062209832ec675013f82283e796e54a"
EXPECTED_YAW = (0.0, 1.25, 2.5, 3.75, 5.0, 3.75, 2.5, 1.25, 0.0)
REGIONS = {
    "R1": (0, 192, 0, 192),
    "R2": (0, 192, 384, 576),
    "R3": (192, 384, 0, 192),
    "R4": (192, 384, 384, 576),
}
PAIRS = ((1, 7), (2, 6), (3, 5))
MSE_THRESHOLD = 0.01
POSE_K_TOLERANCE = 1e-6
PIXEL_COUNT = 147456
RGB_SCALAR_COUNT = 442368
SECONDS = 300
HEX = re.compile(r"^[0-9a-f]{64}$")
ATTEMPT = re.compile(r"^B0_score_attempt_([0-9]{2})$")
WIDTHS = {
    "bool": 1, "uint8": 1, "int8": 1, "uint16": 2, "int16": 2,
    "float16": 2, "bfloat16": 2, "uint32": 4, "int32": 4,
    "float32": 4, "uint64": 8, "int64": 8, "float64": 8,
    "complex64": 8, "complex128": 16,
}
VERIFIED_TENSOR_DESCRIPTORS = {}
ARCHIVE_FILE_IDENTITIES = {}
USED_TENSOR_HANDLES = {}
SCORER_AUTHOR_ROLE = "/root"


class TechnicalInvalid(RuntimeError):
    """A frozen validity guard failed; the attempt may be retained and reviewed."""


class TensorDescriptor(dict):
    """Descriptor carrying provenance from a raw archive kind=tensor node."""


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_utc(raw: str, label: str) -> datetime:
    require(type(raw) is str and bool(raw), label + " must be a nonempty UTC timestamp")
    try:
        value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(label + " is not ISO-8601") from error
    require(value.tzinfo is not None and value.utcoffset() == timezone.utc.utcoffset(value),
            label + " must be timezone-aware UTC")
    return value


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def canonical(value) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def sha256(path: Path, *, deadline: float | None = None) -> str:
    before = path.stat()
    digest = hashlib.sha256()
    count = 0
    with path.open("rb") as handle:
        while block := handle.read(8 * 1024 * 1024):
            digest.update(block)
            count += len(block)
            if deadline is not None:
                require(time.monotonic() <= deadline, "B0 scoring time limit reached")
    after = path.stat()
    require(
        count == before.st_size
        and (before.st_size, before.st_mtime_ns, before.st_ctime_ns, before.st_dev, before.st_ino)
        == (after.st_size, after.st_mtime_ns, after.st_ctime_ns, after.st_dev, after.st_ino),
        "File changed while hashing: " + str(path),
    )
    return digest.hexdigest()


def absolute_file(raw: str, label: str) -> Path:
    path = Path(raw)
    require(path.is_absolute() and path.resolve() == path and path.is_file(), label + " must be an existing canonical absolute file")
    return path


def read_json(path: Path, expected_sha256: str, label: str, *, deadline: float):
    require(HEX.fullmatch(expected_sha256 or "") is not None, label + " SHA-256 is malformed")
    require(path.stat().st_size <= 256 * 1024 * 1024, label + " exceeds bounded JSON scope")
    actual = sha256(path, deadline=deadline)
    require(actual == expected_sha256, label + " SHA-256 differs")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(sha256(path, deadline=deadline) == actual, label + " changed while parsing")
    return value


def json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def write_new(path: Path, value) -> None:
    """Publish a complete create-only JSON file while retaining failed staging evidence."""
    payload = json_bytes(value)
    require(not path.exists(), "Refusing to replace existing output: " + str(path))
    stage = path.parent / ("." + path.name + ".stage-%d-%d" % (os.getpid(), time.time_ns()))
    try:
        with stage.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(stage, path, follow_symlinks=False)
        stage.unlink()
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except BaseException:
        if stage.exists():
            stage.unlink()
        raise


def attempt_directories():
    existing = []
    for path in HERE.iterdir():
        old = ATTEMPT.fullmatch(path.name)
        if old and path.is_dir():
            existing.append((int(old.group(1)), path))
    return sorted(existing)


def create_attempt_staging(raw: str) -> tuple[Path, Path, int]:
    out = Path(raw)
    require(out.is_absolute() and out.resolve() == out, "B0 output must be a canonical absolute path")
    require(out.parent == HERE, "B0 output must be a direct child of the preregistration directory")
    match = ATTEMPT.fullmatch(out.name)
    require(match is not None, "B0 output must be named B0_score_attempt_NN")
    number = int(match.group(1))
    staging = [path for path in HERE.iterdir()
               if path.is_dir() and path.name.startswith(".B0_score_attempt_") and ".staging-" in path.name]
    require(not staging, "An unsealed B0 staging directory exists and blocks automatic retry")
    existing = attempt_directories()
    require([n for n, _ in existing] == list(range(1, len(existing) + 1)), "Existing B0 attempt sequence has a gap")
    require(number == len(existing) + 1, "B0 attempt must use the next sequential directory")
    for old_number, path in existing:
        receipt = path / "receipt.json"
        require(receipt.is_file(), "An existing B0 attempt lacks a terminal receipt and blocks automatic retry")
        old = json.loads(receipt.read_text(encoding="utf-8"))
        require(old.get("attempt") == old_number and old.get("out") == str(path),
                "An existing B0 terminal receipt is misbound")
        require(old.get("technically_valid") is not True,
                "A technically valid B0 attempt already exists and may not be rerun")
    stage = HERE / ("." + out.name + ".staging-%d-%d" % (os.getpid(), time.time_ns()))
    stage.mkdir(mode=0o700, parents=False, exist_ok=False)
    return stage, out, number


def assert_attempt_lease(stage: Path, out: Path, attempt: int) -> None:
    require(stage.is_dir() and stage.parent == HERE and not out.exists(),
            "Current B0 staging lease or final output state differs")
    staging = [path for path in HERE.iterdir()
               if path.is_dir() and path.name.startswith(".B0_score_attempt_") and ".staging-" in path.name]
    require(staging == [stage], "The current B0 scorer no longer owns the sole staging directory")
    existing = attempt_directories()
    require([n for n, _ in existing] == list(range(1, attempt)),
            "B0 attempt sequence changed while the score lock was held")
    for old_number, path in existing:
        receipt = path / "receipt.json"
        require(receipt.is_file(), "A prior B0 attempt lost its terminal receipt")
        old = json.loads(receipt.read_text(encoding="utf-8"))
        require(old.get("attempt") == old_number and old.get("out") == str(path)
                and old.get("technically_valid") is not True,
                "A prior B0 attempt became valid or misbound")


def publish_attempt(stage: Path, out: Path, attempt: int) -> None:
    assert_attempt_lease(stage, out, attempt)
    require((stage / "receipt.json").is_file(), "B0 staging directory lacks its terminal receipt")
    os.rename(stage, out)
    directory_fd = os.open(HERE, os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def verify_fixed_sources(args, deadline: float):
    require(HEX.fullmatch(args.scorer_sha256 or "") is not None, "Scorer SHA-256 is malformed")
    require(sha256(SELF, deadline=deadline) == args.scorer_sha256, "Scorer does not match caller-bound SHA-256")
    fixed = {
        str(CONTRACT): CONTRACT_SHA256,
        str(PROTOCOL): PROTOCOL_SHA256,
        str(PREREG_RECEIPT): PREREG_RECEIPT_SHA256,
        str(READBACK_SUPERVISOR_SOURCE): READBACK_SUPERVISOR_SHA256,
        str(READBACK_SUPERVISOR_PROTOCOL): READBACK_SUPERVISOR_PROTOCOL_SHA256,
        str(READBACK_SUPERVISOR_SOURCE_REVIEW): READBACK_SUPERVISOR_REVIEW_SHA256,
        str(READBACK_WORKER_SOURCE): READBACK_WORKER_SHA256,
        str(READBACK_SOURCE_REVIEW): READBACK_SOURCE_REVIEW_SHA256,
        str(READBACK_ADVERSARIAL_SOURCE_REVIEW): READBACK_ADVERSARIAL_SOURCE_REVIEW_SHA256,
        str(READBACK_REVISION_RECEIPT): READBACK_REVISION_RECEIPT_SHA256,
        str(READBACK_SUPERVISOR_RECEIPT): READBACK_SUPERVISOR_RECEIPT_SHA256,
        str(READBACK_WORKER_RECEIPT): READBACK_WORKER_RECEIPT_SHA256,
        str(READBACK_REPORT): READBACK_REPORT_SHA256,
        str(READBACK_RESULT_REVIEW): READBACK_RESULT_REVIEW_SHA256,
    }
    for raw, expected in fixed.items():
        require(sha256(Path(raw), deadline=deadline) == expected, "Frozen scoring source changed: " + raw)
    review = read_json(SOURCE_REVIEW, args.source_review_sha256, "B0 scorer source review", deadline=deadline)
    require(
        review.get("schema") == "s42-b0-blind-scorer-source-review-v1"
        and review.get("status") == "PASS_S42_B0_BLIND_SCORER_SOURCE_REVIEW"
        and Path(review.get("scorer_path", "")).resolve() == SELF
        and review.get("scorer_sha256") == args.scorer_sha256
        and Path(review.get("contract_path", "")).resolve() == CONTRACT
        and review.get("contract_sha256") == CONTRACT_SHA256
        and review.get("preregistration_protocol_sha256") == PROTOCOL_SHA256
        and review.get("executed") is False
        and review.get("s40_generated_images_viewed") is False
        and review.get("s40_result_arrays_decoded") is False
        and review.get("blocking_findings") == []
        and review.get("author_role") == SCORER_AUTHOR_ROLE
        and isinstance(review.get("reviewer_role"), str)
        and bool(review["reviewer_role"])
        and isinstance(review.get("completed_utc"), str),
        "The exact B0 scorer/contract pair lacks a blind different-author PASS source review",
    )
    adversarial = read_json(
        ADVERSARIAL_SOURCE_REVIEW, args.adversarial_source_review_sha256,
        "B0 scorer adversarial source review", deadline=deadline,
    )
    require(
        adversarial.get("schema") == "s42-b0-blind-scorer-adversarial-source-review-v1"
        and adversarial.get("status") == "PASS_S42_B0_BLIND_SCORER_ADVERSARIAL_SOURCE_REVIEW"
        and Path(adversarial.get("scorer_path", "")).resolve() == SELF
        and adversarial.get("scorer_sha256") == args.scorer_sha256
        and Path(adversarial.get("contract_path", "")).resolve() == CONTRACT
        and adversarial.get("contract_sha256") == CONTRACT_SHA256
        and adversarial.get("preregistration_protocol_sha256") == PROTOCOL_SHA256
        and adversarial.get("executed") is False
        and adversarial.get("s40_generated_images_viewed") is False
        and adversarial.get("s40_result_arrays_decoded") is False
        and adversarial.get("blocking_findings") == []
        and adversarial.get("author_role") == SCORER_AUTHOR_ROLE
        and isinstance(adversarial.get("reviewer_role"), str)
        and bool(adversarial["reviewer_role"])
        and isinstance(adversarial.get("completed_utc"), str),
        "The exact B0 scorer/contract pair lacks an independent adversarial PASS source review",
    )
    require(
        len({SCORER_AUTHOR_ROLE, review["reviewer_role"], adversarial["reviewer_role"]}) == 3,
        "B0 scorer author, primary reviewer, and adversarial reviewer must be pairwise distinct",
    )
    parse_utc(review["completed_utc"], "primary source review completed_utc")
    parse_utc(adversarial["completed_utc"], "adversarial source review completed_utc")
    return review, adversarial, fixed


def verify_blindness_attestation(
    path: Path, expected_sha256: str, manifest_path: Path, manifest_sha256: str,
    scorer_sha256: str, primary_review_sha256: str, adversarial_review_sha256: str,
    primary_review, adversarial_review, attempt: int, out: Path,
    score_started_utc: datetime, deadline: float,
):
    require(path == BLINDNESS_ATTESTATION and path != BLINDNESS_TEMPLATE,
            "Only the fixed real B0 blindness attestation path is accepted")
    doc = read_json(path, expected_sha256, "pre-score blindness attestation", deadline=deadline)
    require(
        doc.get("schema") == "s42-b0-blindness-attestation-v1"
        and doc.get("status") == "PASS_B0_BLINDNESS_PRE_SCORE"
        and doc.get("manifest_path") == str(manifest_path)
        and doc.get("manifest_sha256") == manifest_sha256
        and doc.get("scorer_path") == str(SELF)
        and doc.get("scorer_sha256") == scorer_sha256
        and doc.get("contract_path") == str(CONTRACT)
        and doc.get("contract_sha256") == CONTRACT_SHA256
        and doc.get("primary_source_review_path") == str(SOURCE_REVIEW)
        and doc.get("primary_source_review_sha256") == primary_review_sha256
        and doc.get("adversarial_source_review_path") == str(ADVERSARIAL_SOURCE_REVIEW)
        and doc.get("adversarial_source_review_sha256") == adversarial_review_sha256
        and doc.get("authorized_attempt") == attempt == 1
        and doc.get("authorized_output_path") == str(out)
        and doc.get("generated_images_or_montages_viewed") is False
        and doc.get("s40_result_arrays_decoded_for_metric_selection") is False
        and doc.get("roi_pair_metric_or_threshold_changed_after_output") is False
        and doc.get("attestor_role") == SCORER_AUTHOR_ROLE,
        "Blindness attestation does not establish the required pre-score isolation",
    )
    attested = parse_utc(doc.get("created_utc"), "blindness attestation created_utc")
    primary_completed = parse_utc(primary_review.get("completed_utc"), "primary source review completed_utc")
    adversarial_completed = parse_utc(
        adversarial_review.get("completed_utc"), "adversarial source review completed_utc"
    )
    require(max(primary_completed, adversarial_completed) <= attested <= score_started_utc,
            "Blindness attestation must be after both reviews and no later than score start")
    return doc


def verify_manifest(path: Path, expected_sha256: str, deadline: float):
    require(path == FROZEN_MANIFEST and expected_sha256 == FROZEN_MANIFEST_SHA256, "Only the frozen B0 S40 manifest is accepted")
    manifest = read_json(path, expected_sha256, "S40 manifest", deadline=deadline)
    controls = manifest.get("controls", {})
    require(
        manifest.get("schema") == "s40-declared-variant-two-batch-v1"
        and manifest.get("status") == "FROZEN_DECLARED_VARIANT_TWO_BATCH_EXECUTION"
        and manifest.get("evidence_kind") == "recorded_execution"
        and manifest.get("input_image", {}).get("sha256") == EXPECTED_INPUT_SHA256
        and controls.get("seed") == 42
        and controls.get("height") == controls.get("width") == 576
        and controls.get("target_num_frames") == 4
        and controls.get("operations") == ["turn_left(5)", "turn_right(5)"],
        "S40 manifest is not the frozen B0 generation condition",
    )
    return manifest


def verify_generation_receipt(path: Path, expected_sha256: str, manifest, manifest_sha256: str, deadline: float):
    require(
        path == GENERATION_RECEIPT and expected_sha256 == GENERATION_RECEIPT_SHA256,
        "Only the actual frozen S40 execution_01 terminal receipt is accepted",
    )
    receipt = read_json(path, expected_sha256, "S40 generation terminal receipt", deadline=deadline)
    require(
        receipt.get("status") == "DECLARED_VARIANT_EXTERNAL_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW"
        and receipt.get("manifest_sha256") == manifest_sha256
        and receipt.get("returncode") == 0
        and receipt.get("worker_spawned") is True
        and receipt.get("source_unchanged_at_close") is True
        and "limit_exceeded" not in receipt
        and "unexpected_live_descendants" not in receipt,
        "S40 generation is not in the required terminal successful pending-review state",
    )
    worker_path = path.parent / "worker_receipt.json"
    worker_sha = receipt.get("worker_receipt_sha256")
    require(
        worker_path == GENERATION_WORKER_RECEIPT
        and worker_sha == GENERATION_WORKER_RECEIPT_SHA256,
        "S40 generation worker is not the frozen execution_01 worker",
    )
    worker = read_json(worker_path, worker_sha, "S40 generation worker receipt", deadline=deadline)
    require(
        worker.get("status") == receipt.get("worker_status") == "DECLARED_VARIANT_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW"
        and worker.get("manifest_sha256") == manifest_sha256
        and worker.get("source_unchanged_at_close") is True
        and worker.get("runtime_factory_calls") == 1
        and worker.get("full_resource_checks") == 1,
        "S40 worker receipt is incomplete or belongs to another run",
    )
    output_root = Path(manifest.get("output_root", ""))
    require(output_root.is_absolute() and output_root.resolve() == output_root and output_root.is_dir(), "Frozen S40 output root is unavailable")
    return receipt, worker, worker_path, worker_sha, output_root


def verify_readback(supervisor_path: Path, supervisor_sha: str, result_review_path: Path,
                    result_review_sha: str, manifest_path: Path, manifest_sha: str,
                    generation_path: Path, generation_sha: str, deadline: float):
    require(
        supervisor_path == READBACK_SUPERVISOR_RECEIPT
        and supervisor_sha == READBACK_SUPERVISOR_RECEIPT_SHA256
        and result_review_path == READBACK_RESULT_REVIEW
        and result_review_sha == READBACK_RESULT_REVIEW_SHA256,
        "Only the independently reviewed S40 readback attempt02 is accepted",
    )
    supervisor = read_json(supervisor_path, supervisor_sha, "S40 readback supervisor receipt", deadline=deadline)
    result = supervisor.get("worker_result", {})
    require(
        supervisor.get("schema") == "s40-readback-external-supervisor-v1"
        and supervisor.get("status") == "S40_READBACK_RETURNED_PENDING_INDEPENDENT_REVIEW"
        and supervisor.get("supervisor_sha256") == READBACK_SUPERVISOR_SHA256
        and supervisor.get("supervisor_review_sha256") == READBACK_SUPERVISOR_REVIEW_SHA256
        and supervisor.get("manifest_path") == str(manifest_path)
        and supervisor.get("manifest_sha256") == manifest_sha
        and supervisor.get("s40_execution_receipt_path") == str(generation_path)
        and supervisor.get("s40_execution_receipt_sha256") == generation_sha
        and supervisor.get("readback_invocations") == 1
        and supervisor.get("automatic_retries") == 0
        and supervisor.get("returncode") == 0
        and supervisor.get("sources_unchanged_at_close") is True
        and supervisor.get("inputs_unchanged_at_close") is True
        and supervisor.get("readback_worker_identity_stats_unchanged_at_close") is True
        and supervisor.get("success_pending_independent_review") is True
        and supervisor.get("quality_status") == "NOT_EVALUATED"
        and supervisor.get("scientific_status") == "NOT_EVALUATED"
        and "limit_exceeded" not in supervisor
        and "unexpected_live_descendants" not in supervisor
        and "error" not in supervisor
        and result.get("worker_status") == "PASS_SAVED_S40_IDENTITIES_AND_CACHE_CONSUMPTION_ONLY",
        "S40 readback supervisor receipt does not establish one clean readback",
    )
    worker_path = absolute_file(result.get("worker_receipt_path", ""), "readback worker receipt")
    report_path = absolute_file(result.get("report_path", ""), "readback report")
    worker_sha = result.get("worker_receipt_sha256")
    report_sha = result.get("report_sha256")
    require(
        worker_path == READBACK_WORKER_RECEIPT
        and worker_sha == READBACK_WORKER_RECEIPT_SHA256
        and report_path == READBACK_REPORT
        and report_sha == READBACK_REPORT_SHA256,
        "S40 readback attempt02 worker/report identity differs from the frozen B0 contract",
    )
    worker = read_json(worker_path, worker_sha, "readback worker receipt", deadline=deadline)
    report = read_json(report_path, report_sha, "readback report", deadline=deadline)
    require(
        worker.get("schema") == "s40-real-saved-output-readback-v1"
        and worker.get("status") == "PASS_SAVED_S40_IDENTITIES_AND_CACHE_CONSUMPTION_ONLY"
        and worker.get("passed") is True
        and worker.get("readback_source_sha256") == READBACK_WORKER_SHA256
        and worker.get("quality_status") == "NOT_EVALUATED"
        and worker.get("new_model_or_ga_runs") == 0
        and worker.get("weights_original_photo_gt_read") is False
        and worker.get("report_sha256") == report_sha
        and report.get("manifest_sha256") == manifest_sha,
        "Readback worker/report narrow PASS is missing or misbound",
    )
    review = read_json(result_review_path, result_review_sha, "S40 readback result review", deadline=deadline)
    require(
        review.get("schema") == "s40-readback-result-review-v1"
        and review.get("status") == "PASS_S40_READBACK_RESULT_REVIEW"
        and review.get("manifest_sha256") == manifest_sha
        and review.get("supervisor_receipt_path") == str(supervisor_path)
        and review.get("supervisor_receipt_sha256") == supervisor_sha
        and review.get("worker_receipt_path") == str(worker_path)
        and review.get("worker_receipt_sha256") == worker_sha
        and review.get("report_path") == str(report_path)
        and review.get("report_sha256") == report_sha
        and review.get("readback_source_review_sha256") == READBACK_SOURCE_REVIEW_SHA256
        and review.get("adversarial_readback_source_review_sha256") == READBACK_ADVERSARIAL_SOURCE_REVIEW_SHA256
        and review.get("generated_images_or_montages_viewed") is False
        and review.get("metric_roi_pair_or_threshold_selected_from_outputs") is False
        and review.get("executed") is False
        and review.get("blocking_findings") == [],
        "The exact S40 readback lacks the required blind independent result review",
    )
    require(
        isinstance(review.get("author_role"), str)
        and isinstance(review.get("reviewer_role"), str)
        and review["author_role"] != review["reviewer_role"],
        "S40 readback result review is not independent from its author role",
    )
    return supervisor, worker, report, review


def decode_tree(node):
    require(type(node) is dict, "Every archive metadata node must be an exact JSON object")
    kind = node.get("kind")
    if kind == "dict":
        pairs = [(decode_tree(item["key"]), decode_tree(item["value"])) for item in node["items"]]
        require(len(dict(pairs)) == len(pairs), "Duplicate archival mapping keys")
        return dict(pairs)
    if kind == "list":
        return [decode_tree(item) for item in node["items"]]
    if kind == "tuple":
        return tuple(decode_tree(item) for item in node["items"])
    if kind == "scalar":
        value = node.get("value")
        expected = {"str": str, "int": int, "bool": bool, "NoneType": type(None)}
        label = node.get("type")
        require(label in expected and type(value) is expected[label], "Archive scalar label/value exact type differs")
        return value
    if kind == "python_float64":
        raw = bytes.fromhex(node["little_endian_hex"])
        require(len(raw) == 8, "Malformed archived Python float64")
        return struct.unpack("<d", raw)[0]
    if kind == "tensor":
        return TensorDescriptor(node)
    if kind == "pil_image":
        require("pixels" in node, "Archived PIL image lacks its pixel tensor")
        image = dict(node)
        image["pixels"] = decode_tree(node["pixels"])
        return image
    if kind == "torch_metadata":
        require(type(node.get("type")) is str and type(node.get("value")) is str,
                "Malformed torch metadata")
        return dict(node)
    raise ValueError("Unsupported archive metadata kind: " + repr(kind))


def event_groups(events_path: Path, expected_sha: str, deadline: float):
    require(sha256(events_path, deadline=deadline) == expected_sha, "Archive events.jsonl identity differs")
    groups = {}
    pending = {}
    previous = "0" * 64
    count = 0
    with events_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            require(time.monotonic() <= deadline, "B0 scoring time limit reached")
            require(line.endswith("\n"), "Archive event chain ends in a partial line")
            row = json.loads(line)
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
            if row["event"] == "capture_begin":
                pending[row["seq"]] = (payload["name"], payload["occurrence"])
            elif row["event"] == "capture_complete":
                require(pending.pop(payload["begin_seq"], None) == (payload["name"], payload["occurrence"]), "Broken archive capture pair")
                items = groups.setdefault(payload["name"], [])
                require(payload["occurrence"] == len(items), "Archive occurrence order differs")
                items.append(decode_tree(payload["tree"]))
            else:
                require(row["event"] in ("archive_start", "archive_finalize"), "Unexpected archive failure event")
            previous = row["sha256"]
            count += 1
    require(not pending and count > 0, "Archive event chain is incomplete")
    return groups, count, previous


def import_numpy():
    import numpy as np
    require(np.__version__ == "1.26.4", "B0 scorer requires the frozen NumPy 1.26.4 environment")
    return np


def stat_identity(value) -> tuple[int, int, int, int, int, int]:
    return (
        value.st_dev, value.st_ino, value.st_mode, value.st_size,
        value.st_mtime_ns, value.st_ctime_ns,
    )


def read_fd_snapshot(fd: int, expected_size: int, deadline: float) -> tuple[bytes, str, tuple]:
    before = os.fstat(fd)
    require(stat.S_ISREG(before.st_mode) and before.st_size == expected_size,
            "Opened tensor is not the expected regular file")
    pieces = []
    digest = hashlib.sha256()
    offset = 0
    while offset < expected_size:
        require(time.monotonic() <= deadline, "B0 scoring time limit reached")
        block = os.pread(fd, min(8 * 1024 * 1024, expected_size - offset), offset)
        require(bool(block), "Unexpected tensor EOF")
        pieces.append(block)
        digest.update(block)
        offset += len(block)
    require(os.pread(fd, 1, expected_size) == b"", "Tensor body exceeds its registered size")
    after = os.fstat(fd)
    require(stat_identity(before) == stat_identity(after), "Tensor file changed during same-FD snapshot")
    snapshot = b"".join(pieces)
    require(len(snapshot) == expected_size and hashlib.sha256(snapshot).hexdigest() == digest.hexdigest(),
            "Tensor snapshot assembly differs from its streaming hash")
    return snapshot, digest.hexdigest(), stat_identity(before)


def bind_archive_registry(archive_manifest, archive_root: Path) -> int:
    registry = archive_manifest.get("tensor_descriptors")
    files = archive_manifest.get("files")
    require(type(registry) is dict and len(registry) == 1951,
            "Archive tensor descriptor registry is not the frozen complete table")
    require(type(files) is dict and len(files) == 3912,
            "Archive file identity registry is not the frozen complete table")
    bound_descriptors = {}
    bound_files = {}
    descriptor_keys = {
        "blob", "byteorder", "bytes_sha256", "dtype", "kind",
        "nbytes", "order", "sha256", "shape",
    }
    for raw, descriptor in registry.items():
        require(type(raw) is str and type(descriptor) is dict and set(descriptor) == descriptor_keys,
                "Malformed registered tensor descriptor")
        require(
            descriptor.get("blob") == raw
            and descriptor.get("kind") == "tensor"
            and descriptor.get("byteorder") == "little"
            and descriptor.get("order") == "C"
            and descriptor.get("dtype") in WIDTHS
            and HEX.fullmatch(descriptor.get("sha256", "")) is not None
            and HEX.fullmatch(descriptor.get("bytes_sha256", "")) is not None,
            "Registered tensor descriptor identity differs",
        )
        shape = descriptor.get("shape")
        require(isinstance(shape, list) and all(type(value) is int and value >= 0 for value in shape),
                "Registered tensor shape differs")
        require(math.prod(shape) * WIDTHS[descriptor["dtype"]] == descriptor.get("nbytes"),
                "Registered tensor byte count differs")
        require(raw == "tensors/" + descriptor["sha256"] + ".bin",
                "Registered tensor body is not at its canonical content-addressed path")
        side_raw = "tensors/" + descriptor["sha256"] + ".json"
        body_item = files.get(raw)
        side_item = files.get(side_raw)
        require(
            type(body_item) is dict and set(body_item) == {"bytes", "sha256"}
            and body_item.get("bytes") == descriptor["nbytes"]
            and body_item.get("sha256") == descriptor["bytes_sha256"],
            "Registered tensor body differs from archive manifest.files",
        )
        require(
            type(side_item) is dict and set(side_item) == {"bytes", "sha256"}
            and type(side_item.get("bytes")) is int and side_item["bytes"] > 0
            and HEX.fullmatch(side_item.get("sha256", "")) is not None,
            "Registered tensor sidecar differs from archive manifest.files",
        )
        body_path = archive_root / raw
        side_path = archive_root / side_raw
        require(
            not body_path.is_symlink() and not side_path.is_symlink()
            and body_path.is_file() and side_path.is_file()
            and stat.S_ISREG(body_path.stat().st_mode) and stat.S_ISREG(side_path.stat().st_mode)
            and body_path.stat().st_size == body_item["bytes"]
            and side_path.stat().st_size == side_item["bytes"],
            "Registered tensor body or sidecar is missing, nonregular, linked, or wrong-sized",
        )
        require(body_path.parent == archive_root / "tensors" and side_path.parent == archive_root / "tensors",
                "Registered tensor path escapes the archive tensor directory")
        bound_descriptors[raw] = dict(descriptor)
        bound_files[raw] = dict(body_item)
        bound_files[side_raw] = dict(side_item)
    require(len(bound_descriptors) == len(registry), "Duplicate raw tensor registry key")
    VERIFIED_TENSOR_DESCRIPTORS.clear()
    VERIFIED_TENSOR_DESCRIPTORS.update(bound_descriptors)
    ARCHIVE_FILE_IDENTITIES.clear()
    ARCHIVE_FILE_IDENTITIES.update(bound_files)
    require(not USED_TENSOR_HANDLES, "A prior tensor-handle scope remains open")
    return len(bound_descriptors)


def tensor_snapshot(desc, archive_root: Path, *, expected_dtype: str | None = None,
                    expected_shape: list[int] | None = None, deadline: float):
    require(
        type(desc) is TensorDescriptor
        and desc.get("kind") == "tensor"
        and desc.get("byteorder") == "little"
        and desc.get("order") == "C"
        and desc.get("dtype") in WIDTHS,
        "Malformed authoritative tensor descriptor",
    )
    shape = desc.get("shape")
    require(isinstance(shape, list) and all(type(value) is int and value >= 0 for value in shape), "Malformed tensor shape")
    require(math.prod(shape) * WIDTHS[desc["dtype"]] == desc.get("nbytes"), "Tensor byte count differs")
    require(expected_dtype is None or desc["dtype"] == expected_dtype, "Authoritative tensor dtype differs")
    require(expected_shape is None or shape == expected_shape, "Authoritative tensor shape differs")
    raw = desc.get("blob")
    require(type(raw) is str and raw in VERIFIED_TENSOR_DESCRIPTORS,
            "Tensor blob is absent from the complete archive registry")
    descriptor = dict(desc)
    require(descriptor == VERIFIED_TENSOR_DESCRIPTORS[raw],
            "Event tensor descriptor differs from archive_manifest.tensor_descriptors")
    require(raw == "tensors/" + descriptor["sha256"] + ".bin",
            "Tensor blob path is not canonical")
    path = archive_root / raw
    side_raw = "tensors/" + descriptor["sha256"] + ".json"
    sidecar = archive_root / side_raw
    body_item = ARCHIVE_FILE_IDENTITIES.get(raw)
    side_item = ARCHIVE_FILE_IDENTITIES.get(side_raw)
    require(type(body_item) is dict and type(side_item) is dict,
            "Tensor body or sidecar lacks a registered manifest.files identity")
    require(not path.is_symlink() and not sidecar.is_symlink(),
            "Tensor body or sidecar may not be a symbolic link")
    require(path.parent == archive_root / "tensors" and sidecar.parent == archive_root / "tensors",
            "Tensor body or sidecar escapes the archive tensor directory")
    cached = USED_TENSOR_HANDLES.get(raw)
    if cached is not None:
        require(cached["descriptor"] == descriptor, "Cached tensor descriptor differs")
        return cached["snapshot"], path, cached["body_sha256"]
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        opened = os.fstat(fd)
        path_stat = os.stat(path, follow_symlinks=False)
        require(stat.S_ISREG(opened.st_mode) and stat.S_ISREG(path_stat.st_mode),
                "Tensor body is not a regular file")
        require((opened.st_dev, opened.st_ino) == (path_stat.st_dev, path_stat.st_ino),
                "Opened tensor body differs from its canonical path")
        snapshot, body_sha, opened_identity = read_fd_snapshot(fd, descriptor["nbytes"], deadline)
        require(
            body_sha == descriptor["bytes_sha256"]
            and body_item.get("bytes") == len(snapshot)
            and body_item.get("sha256") == body_sha,
            "Tensor snapshot differs from descriptor or manifest.files identity",
        )
        base = {key: value for key, value in descriptor.items() if key not in ("blob", "sha256")}
        require(hashlib.sha256(canonical(base) + b"\0" + snapshot).hexdigest() == descriptor["sha256"],
                "Tensor descriptor-plus-snapshot SHA-256 differs")
        side_doc = read_json(sidecar, side_item["sha256"], "tensor sidecar", deadline=deadline)
        require(sidecar.stat().st_size == side_item["bytes"] and side_doc == descriptor,
                "Tensor sidecar differs from descriptor or manifest.files identity")
        USED_TENSOR_HANDLES[raw] = {
            "fd": fd,
            "path": path,
            "descriptor": descriptor,
            "snapshot": snapshot,
            "body_sha256": body_sha,
            "opened_identity": opened_identity,
        }
        fd = -1
        return snapshot, path, body_sha
    finally:
        if fd >= 0:
            os.close(fd)


def close_tensor_handles(*, deadline: float, verify: bool) -> int:
    count = len(USED_TENSOR_HANDLES)
    error = None
    for raw, item in list(USED_TENSOR_HANDLES.items()):
        try:
            if verify:
                current = os.fstat(item["fd"])
                require(stat_identity(current) == item["opened_identity"],
                        "Used tensor file metadata changed before score sealing")
                _, closing_sha, closing_identity = read_fd_snapshot(
                    item["fd"], item["descriptor"]["nbytes"], deadline
                )
                require(closing_identity == item["opened_identity"]
                        and closing_sha == item["body_sha256"],
                        "Used tensor body changed before score sealing")
                path_stat = os.stat(item["path"], follow_symlinks=False)
                require((path_stat.st_dev, path_stat.st_ino) == (current.st_dev, current.st_ino),
                        "Used tensor canonical path changed before score sealing")
        except BaseException as caught:
            if error is None:
                error = caught
        finally:
            os.close(item["fd"])
            del USED_TENSOR_HANDLES[raw]
    if error is not None:
        raise error
    return count


def array(desc, archive_root: Path, np, *, expected_dtype: str | None = None,
          expected_shape: list[int] | None = None, deadline: float):
    snapshot, path, body_sha = tensor_snapshot(
        desc, archive_root, expected_dtype=expected_dtype, expected_shape=expected_shape, deadline=deadline
    )
    require(desc["dtype"] != "bfloat16", "BFloat16 is outside B0 numeric scoring scope")
    value = np.frombuffer(snapshot, dtype=np.dtype(desc["dtype"]).newbyteorder("<"))
    value = value.reshape(tuple(desc["shape"]), order="C")
    value.setflags(write=False)
    return value, path, body_sha


def max_abs(a, b, np) -> float:
    require(a.shape == b.shape and np.isfinite(a).all() and np.isfinite(b).all(), "Camera/K shape or finiteness differs")
    return float(np.max(np.abs(a.astype(np.float64) - b.astype(np.float64))))


def verify_requested_camera_conditions(batch_inputs, cache_commits, archive_root: Path, np, deadline: float):
    require(len(batch_inputs) == len(cache_commits) == 2, "Exactly two batch_input/cache_commit occurrences are required")
    final_cache = cache_commits[1]["cache"]
    require(len(final_cache["c2ws"]) == len(final_cache["Ks"]) == 9, "Final cache does not contain IDs 0-8")
    base_pose, _, _ = array(final_cache["c2ws"][0], archive_root, np, expected_shape=[4, 4], deadline=deadline)
    base_K, _, _ = array(final_cache["Ks"][0], archive_root, np, deadline=deadline)
    require(base_K.shape in ((3, 3), (4, 4)), "Unexpected intrinsic matrix shape")
    cross = []
    actual_poses = [np.asarray(base_pose)]
    actual_Ks = [np.asarray(base_K)]
    for batch_index, (begin, end) in enumerate(((1, 5), (5, 9))):
        targets, _, _ = array(batch_inputs[batch_index]["target_c2ws"], archive_root, np, deadline=deadline)
        target_Ks, _, _ = array(batch_inputs[batch_index]["target_Ks"], archive_root, np, deadline=deadline)
        require(targets.ndim == 3 and list(targets.shape[1:]) == [4, 4] and targets.shape[0] >= 4, "Batch target c2w shape differs")
        require(target_Ks.ndim == 3 and target_Ks.shape[0] >= 4 and target_Ks.shape[1:] == base_K.shape, "Batch target K shape differs")
        cache = cache_commits[batch_index]["cache"]
        require(len(cache["c2ws"]) == len(cache["Ks"]) == end, "Cache history length differs")
        for offset, frame_id in enumerate(range(begin, end)):
            pose, _, _ = array(cache["c2ws"][frame_id], archive_root, np, expected_shape=[4, 4], deadline=deadline)
            K, _, _ = array(cache["Ks"][frame_id], archive_root, np, expected_shape=list(base_K.shape), deadline=deadline)
            pose_cross = max_abs(targets[offset], pose, np)
            k_cross = max_abs(target_Ks[offset], K, np)
            require(pose_cross <= POSE_K_TOLERANCE and k_cross <= POSE_K_TOLERANCE, "batch_input to cache_commit pose/K cross-check failed")
            cross.append({"id": frame_id, "pose_max_abs": pose_cross, "K_max_abs": k_cross})
            actual_poses.append(np.asarray(pose))
            actual_Ks.append(np.asarray(K))
    planned = []
    base = np.asarray(base_pose, dtype=np.float64)
    require(max_abs(base[3], np.asarray([0.0, 0.0, 0.0, 1.0]), np) <= POSE_K_TOLERANCE, "Base c2w homogeneous row differs")
    for frame_id, yaw in enumerate(EXPECTED_YAW):
        angle = math.radians(yaw)
        rotation = np.asarray([
            [math.cos(angle), 0.0, math.sin(angle)],
            [0.0, 1.0, 0.0],
            [-math.sin(angle), 0.0, math.cos(angle)],
        ], dtype=np.float64)
        expected = np.eye(4, dtype=np.float64)
        expected[:3, :3] = rotation @ base[:3, :3]
        expected[:3, 3] = base[:3, 3]
        pose_error = max_abs(np.asarray(actual_poses[frame_id]), expected, np)
        k_error = max_abs(np.asarray(actual_Ks[frame_id]), np.asarray(base_K), np)
        require(pose_error <= POSE_K_TOLERANCE and k_error <= POSE_K_TOLERANCE, "Planned yaw or fixed K guard failed")
        planned.append({"id": frame_id, "yaw_degrees": yaw, "pose_max_abs": pose_error, "K_max_abs": k_error})
    closure_pose = max_abs(np.asarray(actual_poses[8]), np.asarray(actual_poses[0]), np)
    closure_K = max_abs(np.asarray(actual_Ks[8]), np.asarray(actual_Ks[0]), np)
    require(closure_pose <= POSE_K_TOLERANCE and closure_K <= POSE_K_TOLERANCE, "ID8 does not close to the requested ID0 c2w/K")
    return {
        "status": "PASS_REQUESTED_CAMERA_CONDITION_ONLY",
        "tolerance": POSE_K_TOLERANCE,
        "batch_to_cache": cross,
        "planned_sequence": planned,
        "exact_return": {"pose_max_abs": closure_pose, "K_max_abs": closure_K},
        "visual_camera_obedience": "NOT_EVALUATED_NO_FROZEN_PROXY",
    }


def mse_for_regions(first, second, regions, np):
    total = 0.0
    scalars = 0
    details = {}
    for name, (y0, y1, x0, x1) in regions.items():
        a = np.asarray(first[y0:y1, x0:x1], dtype=np.float64) / 255.0
        b = np.asarray(second[y0:y1, x0:x1], dtype=np.float64) / 255.0
        square_sum = float(np.sum(np.square(b - a), dtype=np.float64))
        count = int(a.size)
        mse = square_sum / count
        details[name] = metric_record(mse, (y1 - y0) * (x1 - x0), count)
        total += square_sum
        scalars += count
    require(scalars == RGB_SCALAR_COUNT, "Frozen M_outer4 scalar count differs")
    return total / scalars, details


def metric_record(mse: float, pixels: int, scalars: int):
    require(math.isfinite(mse) and mse >= 0.0, "Nonfinite or negative MSE")
    psnr = None if mse == 0.0 else -10.0 * math.log10(mse)
    return {
        "mse_float64": mse,
        "mse_float64_hex": mse.hex(),
        "psnr_db_float64": psnr,
        "psnr_db_display_when_zero": "+inf" if mse == 0.0 else None,
        "pixels": pixels,
        "rgb_scalars": scalars,
    }


def score_pixels(pil_frames, archive_root: Path, np, deadline: float):
    require(isinstance(pil_frames, list) and len(pil_frames) == 9, "Authoritative final cache must map exactly IDs 0-8")
    arrays = []
    identities = []
    for frame_id, image in enumerate(pil_frames):
        require(
            isinstance(image, dict)
            and image.get("kind") == "pil_image"
            and image.get("mode") == "RGB"
            and image.get("size") == [576, 576],
            "ID%d is not archived 576x576 RGB" % frame_id,
        )
        value, path, body_sha = array(
            image.get("pixels"), archive_root, np,
            expected_dtype="uint8", expected_shape=[576, 576, 3], deadline=deadline,
        )
        arrays.append(value)
        identities.append({
            "id": frame_id,
            "tensor_descriptor_sha256": image["pixels"]["sha256"],
            "tensor_body_sha256": body_sha,
            "blob": str(path),
        })
    bodies = [item["tensor_body_sha256"] for item in identities]
    if all(value == bodies[0] for value in bodies[1:]) or len(set(bodies[1:])) == 1:
        raise TechnicalInvalid("DEGENERATE_COPY/CAMERA_CONTROL_UNRESOLVED")
    primary_mse, regions = mse_for_regions(arrays[0], arrays[8], REGIONS, np)
    primary = metric_record(primary_mse, PIXEL_COUNT, RGB_SCALAR_COUNT)
    require(primary["pixels"] == PIXEL_COUNT and primary["rgb_scalars"] == RGB_SCALAR_COUNT, "Frozen M_outer4 count differs")
    full_delta = np.asarray(arrays[8], dtype=np.float64) / 255.0 - np.asarray(arrays[0], dtype=np.float64) / 255.0
    full_mse = float(np.sum(np.square(full_delta), dtype=np.float64)) / int(full_delta.size)
    pairs = {}
    for left, right in PAIRS:
        mse, _ = mse_for_regions(arrays[left], arrays[right], REGIONS, np)
        pairs["%d_%d" % (left, right)] = metric_record(mse, PIXEL_COUNT, RGB_SCALAR_COUNT)
    return {
        "authoritative_pixel_identities": identities,
        "primary": primary,
        "event_MSE_gt_0_01": primary_mse > MSE_THRESHOLD,
        "equality_is_not_event": primary_mse == MSE_THRESHOLD,
        "per_region_diagnostic": regions,
        "full_frame_diagnostic": metric_record(full_mse, 576 * 576, 576 * 576 * 3),
        "generated_only_pair_diagnostic_no_GT": pairs,
    }


def score(args, stage: Path, out: Path, attempt: int):
    started = time.monotonic()
    score_started_utc = datetime.now(timezone.utc)
    deadline = started + SECONDS
    receipt = {
        "schema": "s42-b0-blind-score-receipt-v1",
        "status": "CHECKING_BLIND_FROZEN_INPUTS",
        "started_utc": score_started_utc.isoformat(),
        "attempt": attempt,
        "out": str(out),
        "scorer_path": str(SELF),
        "scorer_sha256": args.scorer_sha256,
        "contract_path": str(CONTRACT),
        "contract_sha256": CONTRACT_SHA256,
        "preregistration_protocol_sha256": PROTOCOL_SHA256,
        "primary_source_review_path": str(SOURCE_REVIEW),
        "primary_source_review_sha256": args.source_review_sha256,
        "adversarial_source_review_path": str(ADVERSARIAL_SOURCE_REVIEW),
        "adversarial_source_review_sha256": args.adversarial_source_review_sha256,
        "blindness_attestation_path": args.blindness_attestation,
        "blindness_attestation_sha256": args.blindness_attestation_sha256,
        "technically_valid": False,
        "score_executed": False,
        "images_opened_or_emitted": 0,
        "model_generation_or_renderer_calls": 0,
        "scientific_scope": "B0 single-scene development screen only",
    }
    report = None
    try:
        source_review, adversarial_source_review, fixed = verify_fixed_sources(args, deadline)
        manifest_path = absolute_file(args.manifest, "S40 manifest")
        generation_path = absolute_file(args.s40_execution_receipt, "S40 generation receipt")
        readback_supervisor_path = absolute_file(args.readback_supervisor_receipt, "S40 readback supervisor receipt")
        result_review_path = absolute_file(args.readback_result_review, "S40 readback result review")
        blindness_path = absolute_file(args.blindness_attestation, "pre-score blindness attestation")
        manifest = verify_manifest(manifest_path, args.manifest_sha256, deadline)
        blindness = verify_blindness_attestation(
            blindness_path, args.blindness_attestation_sha256,
            manifest_path, args.manifest_sha256, args.scorer_sha256,
            args.source_review_sha256, args.adversarial_source_review_sha256,
            source_review, adversarial_source_review, attempt, out,
            score_started_utc, deadline,
        )
        generation, generation_worker, generation_worker_path, generation_worker_sha, output_root = verify_generation_receipt(
            generation_path, args.s40_execution_receipt_sha256, manifest, args.manifest_sha256, deadline
        )
        readback = verify_readback(
            readback_supervisor_path, args.readback_supervisor_receipt_sha256,
            result_review_path, args.readback_result_review_sha256,
            manifest_path, args.manifest_sha256,
            generation_path, args.s40_execution_receipt_sha256, deadline,
        )
        archive_manifest_path = output_root / "archive/manifest.json"
        archive_ref = generation_worker.get("archive_receipt", {})
        require(Path(archive_ref.get("path", "")).resolve() == archive_manifest_path, "S40 worker archive path differs")
        archive_manifest = read_json(archive_manifest_path, archive_ref.get("sha256", ""), "S40 full archive manifest", deadline=deadline)
        require(
            archive_manifest.get("schema") == "s35-full-original-output-archive-v1"
            and archive_manifest.get("status") == "ARCHIVE_COMPLETE"
            and archive_manifest.get("evidence_kind") == "recorded_execution"
            and archive_manifest.get("caller_manifest_sha256") == args.manifest_sha256
            and not archive_manifest.get("missing_required_names")
            and archive_manifest.get("failed_captures") == 0,
            "S40 full archive is not a complete recorded execution",
        )
        archive_root = archive_manifest_path.parent
        tensor_registry_count = bind_archive_registry(archive_manifest, archive_root)
        events_item = archive_manifest.get("files", {}).get("events.jsonl", {})
        events_path = archive_root / "events.jsonl"
        groups, event_count, last_sha = event_groups(events_path, events_item.get("sha256", ""), deadline)
        require(
            event_count == archive_manifest.get("event_count")
            and last_sha == archive_manifest.get("last_event_sha256"),
            "Archive chain closure differs from its manifest",
        )
        require(len(groups.get("batch_input", [])) == 2 and len(groups.get("cache_commit", [])) == 2, "B0 requires two complete batch/cache captures")
        np = import_numpy()
        camera = verify_requested_camera_conditions(groups["batch_input"], groups["cache_commit"], archive_root, np, deadline)
        receipt["score_executed"] = True
        pixel_scores = score_pixels(groups["cache_commit"][1]["cache"]["pil_frames"], archive_root, np, deadline)
        used_tensor_count = close_tensor_handles(deadline=deadline, verify=True)
        event = pixel_scores["event_MSE_gt_0_01"]
        report = {
            "schema": "s42-b0-blind-score-report-v1",
            "completed_utc": utc(),
            "row": "B0",
            "attempt": attempt,
            "manifest_path": str(manifest_path),
            "manifest_sha256": args.manifest_sha256,
            "s40_execution_receipt_path": str(generation_path),
            "s40_execution_receipt_sha256": args.s40_execution_receipt_sha256,
            "readback_supervisor_receipt_path": str(readback_supervisor_path),
            "readback_supervisor_receipt_sha256": args.readback_supervisor_receipt_sha256,
            "readback_result_review_path": str(result_review_path),
            "readback_result_review_sha256": args.readback_result_review_sha256,
            "blindness_attestation_path": str(blindness_path),
            "blindness_attestation_sha256": args.blindness_attestation_sha256,
            "archive_manifest_path": str(archive_manifest_path),
            "archive_manifest_sha256": archive_ref["sha256"],
            "archive_events_sha256": events_item["sha256"],
            "archive_tensor_descriptor_registry_count": tensor_registry_count,
            "same_fd_immutable_tensor_snapshots_verified_at_close": used_tensor_count,
            "primary_source_review_sha256": args.source_review_sha256,
            "adversarial_source_review_sha256": args.adversarial_source_review_sha256,
            "requested_camera_condition_guard": camera,
            "visual_camera_compliance_proxy": "MISSING_NOT_PREREGISTERED",
            "visual_quality_QA_all9": "NOT_YET_ALLOWED_UNTIL_THIS_MACHINE_RECEIPT_IS_SEALED",
            "score": pixel_scores,
            "row_event": event,
            "row_status": "B0_TECHNICALLY_VALID_SEVERE_DISCREPANCY_EVENT" if event else "B0_TECHNICALLY_VALID_NO_SEVERE_DISCREPANCY_EVENT",
            "cohort_status": "INCOMPLETE",
            "interpretation_cap": (
                "RETURN_RGB_DISCREPANCY_CAMERA_CAUSE_UNRESOLVED_SINGLE_ROW"
                if event else "B0_SINGLE_ROW_NO_EVENT_C1_C2_STILL_REQUIRED"
            ),
            "GT_boundary": "ID0 is an observed RGB reference for the exact-return camera only; no depth, 3D, motion, or whole-video GT is claimed.",
            "claim_boundary": "No memory/mean attribution, camera-obedience PASS, repeatability, cohort confirmation, visual-quality PASS, or novelty claim.",
            "images_opened_or_emitted": 0,
        }
        receipt.update(
            status="PASS_B0_MACHINE_SCORE_SINGLE_ROW_COHORT_INCOMPLETE",
            technically_valid=True,
            row_event=event,
            cohort_status="INCOMPLETE",
            source_review_sha256=args.source_review_sha256,
            adversarial_source_review_sha256=args.adversarial_source_review_sha256,
            blindness_attestation_sha256=args.blindness_attestation_sha256,
            upstream_readback_result_review_sha256=args.readback_result_review_sha256,
            upstream_readback_status=readback[0]["status"],
            archive_tensor_descriptor_registry_count=tensor_registry_count,
            same_fd_immutable_tensor_snapshots_verified_at_close=used_tensor_count,
            fixed_source_identities=fixed,
            limitations=[
                "B0 is one development row; C1 and C2 remain mandatory for the preregistered cohort decision.",
                "Archived requested c2w/K closure does not establish rendered visual camera obedience.",
                "The independent visual camera proxy and all-nine visual quality QA remain absent before post-score viewing.",
                "Generated-only pairs are diagnostics without GT.",
            ],
        )
    except TechnicalInvalid as error:
        report = None
        receipt.update(
            status="INVALID_OR_UNINTERPRETABLE",
            technically_valid=False,
            invalid_reason=str(error),
            error_type=type(error).__name__,
            error=str(error),
            traceback=traceback.format_exc(),
        )
    except BaseException as error:
        report = None
        receipt.update(
            status="FAILED_OR_PARTIAL_B0_BLIND_SCORE" if receipt.get("score_executed") else "NOT_READY_BEFORE_B0_BLIND_SCORE",
            technically_valid=False,
            error_type=type(error).__name__,
            error=str(error),
            traceback=traceback.format_exc(),
        )
    finally:
        if USED_TENSOR_HANDLES:
            try:
                close_tensor_handles(deadline=deadline, verify=False)
            except BaseException as close_error:
                report = None
                receipt.update(
                    status="FAILED_OR_PARTIAL_B0_BLIND_SCORE",
                    technically_valid=False,
                    error_type=type(close_error).__name__,
                    error=str(close_error),
                    traceback=traceback.format_exc(),
                )
    receipt["completed_utc"] = utc()
    receipt["elapsed_seconds"] = time.monotonic() - started
    receipt["deadline_seconds"] = SECONDS
    receipt["human_viewing_now_allowed"] = receipt.get("status") == "PASS_B0_MACHINE_SCORE_SINGLE_ROW_COHORT_INCOMPLETE"
    assert_attempt_lease(stage, out, attempt)
    success = (
        report is not None
        and receipt.get("status") == "PASS_B0_MACHINE_SCORE_SINGLE_ROW_COHORT_INCOMPLETE"
        and receipt.get("technically_valid") is True
    )
    if success:
        report_payload = json_bytes(report)
        report_sha = hashlib.sha256(report_payload).hexdigest()
        receipt["report_path"] = str(out / "report.json")
        receipt["report_sha256"] = report_sha
        write_new(stage / "report.json", report)
        require(sha256(stage / "report.json", deadline=deadline) == report_sha,
                "Staged B0 report differs before terminal receipt seal")
    else:
        report = None
        receipt["technically_valid"] = False
        receipt["human_viewing_now_allowed"] = False
        require(not (stage / "report.json").exists(),
                "A technically invalid B0 staging attempt may not expose a report")
    assert_attempt_lease(stage, out, attempt)
    write_new(stage / "receipt.json", receipt)
    return 0 if receipt.get("technically_valid") is True else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scorer-sha256", required=True)
    parser.add_argument("--source-review-sha256", required=True)
    parser.add_argument("--adversarial-source-review-sha256", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--s40-execution-receipt", required=True)
    parser.add_argument("--s40-execution-receipt-sha256", required=True)
    parser.add_argument("--readback-supervisor-receipt", required=True)
    parser.add_argument("--readback-supervisor-receipt-sha256", required=True)
    parser.add_argument("--readback-result-review", required=True)
    parser.add_argument("--readback-result-review-sha256", required=True)
    parser.add_argument("--blindness-attestation", required=True)
    parser.add_argument("--blindness-attestation-sha256", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    lock_flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    lock_fd = os.open(B0_SCORE_LOCK, lock_flags, 0o600)
    with os.fdopen(lock_fd, "r+b", closefd=True) as lock_handle:
        require(stat.S_ISREG(os.fstat(lock_handle.fileno()).st_mode), "B0 score lock is not a regular file")
        try:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError("Another B0 scorer holds the exclusive attempt lock") from error
        stage, out, attempt = create_attempt_staging(args.out)
        result = score(args, stage, out, attempt)
        publish_attempt(stage, out, attempt)
        return result


if __name__ == "__main__":
    raise SystemExit(main())
