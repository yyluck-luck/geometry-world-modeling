#!/usr/bin/env python3
"""Thin identity/I/O wrapper for the frozen S46 C1 scoring kernel.

The source is deliberately unbound.  Formal use requires an exact external
binding, two source reviews, a pre-score blindness attestation, and a fresh
independent V12 numeric-camera-guard result review.  Until then it must not open
any C1 tensor body.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import time


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SELF = Path(__file__).resolve()
BINDING = HERE / "WRAPPER_EXECUTION_BINDING.json"
SCORER = ROOT / "work/S46_c1_blind_scoring_preparation/score_c1_blind_candidate.py"
SCORER_SHA256 = "ada2ba80eceebe83a514fd929c6cc82b69669e6525e261ff4729064f2bac3f1a"
CONTRACT_TEMPLATE = ROOT / "work/S46_c1_blind_scoring_preparation/C1_SCORING_CONTRACT_TEMPLATE.json"
CONTRACT_TEMPLATE_SHA256 = "79299749250c22dd9719d93964b9c179a8884f01c530bf07a45625c59395ab7b"
PROTOCOL = ROOT / "work/S42_baseline_failure_preregistration/PROTOCOL.md"
PROTOCOL_SHA256 = "89fb44e0b77a85a66fe611cd2f885fed0288229cbb027e04da25fc0631507b3f"
OUTPUT = ROOT / "work/S46_c1_blind_scoring_preparation/C1_score_attempt_01"
TENSOR_DIR = ROOT / "results/S44_C1_confirmation_generation/archive/tensors"
FROZEN_MATH_SHA256 = "9bee0abe9392e04e061adb7cf8b39297d7730e7045ed856486f1e03ee8d82812"
SHAPE = (576, 576, 3)
NBYTES = 576 * 576 * 3
HEX = re.compile(r"^[0-9a-f]{64}$")
WRAPPER_AUTHOR_ROLE = "/root/execution_resumption_audit"
SCORER_AUTHOR_ROLE = "/root/c1_blind_score_builder"

FIXED_UPSTREAM = {
    "generation_manifest": {
        "path": ROOT / "work/S44_c1_confirmation_generation/review_attachment_01/manifest.json",
        "sha256": "1e86e8279c608995a03d6675a8636c354d6d4d046b7c8faea9611d6e6a9fd93b",
        "fields": {"/schema": "s44-c1-confirmation-two-batch-v1", "/status": "FROZEN_C1_BASELINE_CONFIRMATION_TWO_BATCH_EXECUTION"},
    },
    "generation_terminal_receipt": {
        "path": ROOT / "work/S44_c1_confirmation_generation/execution_01/receipt.json",
        "sha256": "44753718ca666d134ac9500ffcd6ada6b0e7e4e6ce6cbfc3bfa9f50de85dcb18",
        "fields": {"/schema": "s44-c1-confirmation-launch-v1", "/status": "C1_BASELINE_EXTERNAL_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW", "/returncode": 0, "/scientific_status": "NOT_EVALUATED", "/manifest_sha256": "1e86e8279c608995a03d6675a8636c354d6d4d046b7c8faea9611d6e6a9fd93b"},
    },
    "generation_worker_receipt": {
        "path": ROOT / "work/S44_c1_confirmation_generation/execution_01/worker_receipt.json",
        "sha256": "5deea6956876f03d7b36ed6ab57f608f9613da79e133921d3ead0865196b18f0",
        "fields": {"/schema": "s44-c1-confirmation-worker-v1", "/status": "C1_BASELINE_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW", "/scientific_status": "NOT_EVALUATED", "/manifest_sha256": "1e86e8279c608995a03d6675a8636c354d6d4d046b7c8faea9611d6e6a9fd93b"},
    },
    "readback_supervisor_receipt": {
        "path": ROOT / "work/S45_c1_result_readback/supervision_01/receipt.json",
        "sha256": "801798bd89f9ffc06025652e1af4abeb533a9bcda503cdfb80857824a353d611",
        "fields": {"/schema": "s45-c1-readback-external-supervisor-v1", "/status": "C1_READBACK_RETURNED_PENDING_INDEPENDENT_RESULT_REVIEW", "/returncode": 0, "/scientific_status": "NOT_EVALUATED", "/quality_status": "NOT_EVALUATED", "/manifest_sha256": "1e86e8279c608995a03d6675a8636c354d6d4d046b7c8faea9611d6e6a9fd93b"},
    },
    "readback_worker_receipt": {
        "path": ROOT / "work/S45_c1_result_readback/executed_01/receipt.json",
        "sha256": "54b457212fc0128c3fe8c59d9549d7b2f25e26bc8e5778ca38edae868c8201a1",
        "fields": {"/schema": "s45-c1-real-saved-output-readback-v1", "/status": "PASS_SAVED_C1_IDENTITIES_AND_CACHE_CONSUMPTION_ONLY", "/passed": True, "/quality_status": "NOT_EVALUATED"},
    },
    "readback_report": {
        "path": ROOT / "work/S45_c1_result_readback/executed_01/report.json",
        "sha256": "423e5fb85ea092ba613ff71d28671f89f7df365eb29be8ca1c8f9a950662df47",
        "fields": {"/row": "C1", "/manifest_sha256": "1e86e8279c608995a03d6675a8636c354d6d4d046b7c8faea9611d6e6a9fd93b", "/pixel_identity_status": "ARCHIVED_PIL_PIXEL_TENSORS_AND_ARCHIVE_FILE_BYTES_IDENTITY_ONLY", "/png_decode_or_visual_quality_status": "NOT_EVALUATED"},
    },
    "readback_result_review": {
        "path": ROOT / "work/S45_c1_result_readback/supervision_01/independent_result_review.json",
        "sha256": "2b5e4bc3dcf28f60b320ae4d3af2b4949b60a526cacc62b2deacd87ac6ddad4c",
        "fields": {"/schema": "s45-c1-readback-result-review-v1", "/status": "PASS_S45_C1_READBACK_RESULT_REVIEW", "/manifest_sha256": "1e86e8279c608995a03d6675a8636c354d6d4d046b7c8faea9611d6e6a9fd93b", "/downstream_row_validity_status": "BLOCKED_AWAITING_S42_NUMERIC_REQUESTED_POSE_K_GUARD"},
    },
}

REQUIRED_VALIDITY = (
    "generation_first_technically_valid_attempt",
    "readback_independently_reviewed",
    "cache_readback_guard_pass",
    "requested_pose_K_guard_pass",
    "all_nine_authoritative_pixels_identified",
    "no_visual_QA_before_machine_score",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_utc(value, label: str) -> datetime:
    require(type(value) is str and bool(value), label + " must be UTC text")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.tzinfo is not None and parsed.utcoffset() == timezone.utc.utcoffset(parsed), label + " must be UTC")
    return parsed


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def _identity(st):
    return (st.st_dev, st.st_ino, st.st_mode, st.st_nlink, st.st_size, st.st_mtime_ns, st.st_ctime_ns)


def read_snapshot(path: Path, *, expected_sha256: str | None = None, expected_size: int | None = None, max_bytes: int = 16 * 1024 * 1024):
    path = Path(path)
    require(path.is_absolute() and path.resolve() == path, "Path is not canonical absolute: " + str(path))
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode), "Not a regular file: " + str(path))
        if expected_size is not None:
            require(before.st_size == expected_size, "File size differs: " + str(path))
        require(before.st_size <= max_bytes, "File exceeds bounded read: " + str(path))
        blocks = []
        offset = 0
        while offset < before.st_size:
            block = os.pread(fd, min(1024 * 1024, before.st_size - offset), offset)
            require(bool(block), "Unexpected EOF: " + str(path))
            blocks.append(block)
            offset += len(block)
        require(os.pread(fd, 1, offset) == b"", "Unexpected trailing bytes: " + str(path))
        after = os.fstat(fd)
        named = path.stat()
        require(_identity(before) == _identity(after) and (named.st_dev, named.st_ino) == (before.st_dev, before.st_ino), "File identity changed during same-FD read: " + str(path))
        payload = b"".join(blocks)
        digest = hashlib.sha256(payload).hexdigest()
        if expected_sha256 is not None:
            require(HEX.fullmatch(expected_sha256 or "") is not None and digest == expected_sha256, "SHA-256 differs: " + str(path))
        return payload, digest
    finally:
        os.close(fd)


def read_json_snapshot(path: Path, expected_sha256: str):
    raw, digest = read_snapshot(path, expected_sha256=expected_sha256, max_bytes=32 * 1024 * 1024)
    value = json.loads(raw)
    require(type(value) is dict, "JSON root must be an object: " + str(path))
    return value, digest, len(raw)


def pointer(value, raw: str):
    require(type(raw) is str and raw.startswith("/") and "~" not in raw, "Only simple JSON pointers are accepted")
    current = value
    for part in raw[1:].split("/"):
        if type(current) is dict:
            require(part in current, "Missing JSON pointer " + raw)
            current = current[part]
        elif type(current) is list and part.isdigit():
            index = int(part)
            require(index < len(current), "Missing JSON pointer " + raw)
            current = current[index]
        else:
            raise ValueError("Missing JSON pointer " + raw)
    return current


def validate_fields(doc, fields, label: str) -> None:
    for raw, expected in fields.items():
        require(pointer(doc, raw) == expected, label + " differs at " + raw)


def validate_pixel_descriptors(identities, tensor_dir: Path, *, open_bodies: bool, np=None):
    require(type(identities) is list and len(identities) == 9, "Exactly nine pixel identities are required")
    tensor_dir = Path(tensor_dir)
    require(tensor_dir.is_absolute() and tensor_dir.resolve() == tensor_dir and tensor_dir.is_dir(), "Tensor directory differs")
    frames = []
    descriptor_bytes = 0
    body_bytes = 0
    descriptors = []
    for expected_id, item in enumerate(identities):
        require(type(item) is dict and set(item) == {"id", "tensor_descriptor_sha256", "tensor_body_sha256", "blob"}, "Pixel identity fields differ")
        descriptor = item["tensor_descriptor_sha256"]
        body_sha = item["tensor_body_sha256"]
        require(item["id"] == expected_id and type(item["id"]) is int, "Pixel IDs must be 0 through 8")
        require(HEX.fullmatch(descriptor or "") is not None and HEX.fullmatch(body_sha or "") is not None, "Pixel hash is malformed")
        body_path = Path(item["blob"])
        require(body_path.is_absolute() and body_path.parent == tensor_dir and body_path.name == descriptor + ".bin", "Descriptor-addressed body path differs")
        sidecar_path = tensor_dir / (descriptor + ".json")
        sidecar_raw, _ = read_snapshot(sidecar_path, max_bytes=64 * 1024)
        descriptor_bytes += len(sidecar_raw)
        sidecar = json.loads(sidecar_raw)
        require(type(sidecar) is dict and sidecar == {
            "blob": "tensors/" + descriptor + ".bin",
            "byteorder": "little",
            "bytes_sha256": body_sha,
            "dtype": "uint8",
            "kind": "tensor",
            "nbytes": NBYTES,
            "order": "C",
            "sha256": descriptor,
            "shape": list(SHAPE),
        }, "Pixel descriptor differs for ID%d" % expected_id)
        body_stat = body_path.stat()
        require(stat.S_ISREG(body_stat.st_mode) and body_stat.st_size == NBYTES and not body_path.is_symlink(), "Pixel body metadata differs for ID%d" % expected_id)
        descriptors.append(sidecar)
        if open_bodies:
            require(np is not None and np.__version__ == "1.26.4", "Formal body loading requires NumPy 1.26.4")
            raw, actual = read_snapshot(body_path, expected_sha256=body_sha, expected_size=NBYTES, max_bytes=NBYTES)
            body_bytes += len(raw)
            require(actual == body_sha, "Pixel body hash differs")
            frame = np.frombuffer(raw, dtype=np.uint8).reshape(SHAPE)
            require(frame.flags.c_contiguous, "Pixel snapshot is not C-contiguous")
            frames.append(frame)
    return {"frames": frames if open_bodies else None, "descriptors": descriptors, "descriptor_bytes_read": descriptor_bytes, "body_bytes_read": body_bytes}


def validate_current_real_metadata():
    documents = {}
    json_bytes_read = 0
    for label, frozen in FIXED_UPSTREAM.items():
        doc, _, count = read_json_snapshot(frozen["path"], frozen["sha256"])
        validate_fields(doc, frozen["fields"], label)
        documents[label] = doc
        json_bytes_read += count
    identities = documents["readback_result_review"].get("authoritative_pixel_identities")
    pixels = validate_pixel_descriptors(identities, TENSOR_DIR, open_bodies=False)
    require(pixels["body_bytes_read"] == 0, "Metadata validation opened a C1 body")
    return {"documents": documents, "identities": identities, "json_bytes_read": json_bytes_read, **pixels}


def load_bound(path_record, label: str):
    require(type(path_record) is dict and set(path_record) == {"path", "sha256"}, label + " binding fields differ")
    require(HEX.fullmatch(path_record.get("sha256") or "") is not None, label + " hash is malformed")
    path = Path(path_record.get("path", ""))
    doc, _, _ = read_json_snapshot(path, path_record["sha256"])
    return path, doc


def validate_source_reviews(binding, contract_path: Path, contract_sha: str, wrapper_sha: str):
    reviews = []
    expected = (
        ("primary_source_review", "s46-c1-blind-scorer-source-review-v1", "PASS_S46_C1_BLIND_SCORER_SOURCE_REVIEW"),
        ("adversarial_source_review", "s46-c1-blind-scorer-adversarial-source-review-v1", "PASS_S46_C1_BLIND_SCORER_ADVERSARIAL_SOURCE_REVIEW"),
    )
    for key, schema, status_value in expected:
        path, review = load_bound(binding[key], key)
        require(review.get("schema") == schema and review.get("status") == status_value, key + " is not PASS")
        require(review.get("scorer_path") == str(SCORER) and review.get("scorer_sha256") == SCORER_SHA256, key + " scorer identity differs")
        require(review.get("wrapper_path") == str(SELF) and review.get("wrapper_sha256") == wrapper_sha, key + " wrapper identity differs")
        require(review.get("bound_contract_path") == str(contract_path) and review.get("bound_contract_sha256") == contract_sha, key + " contract identity differs")
        require(review.get("preregistration_protocol_path") == str(PROTOCOL) and review.get("preregistration_protocol_sha256") == PROTOCOL_SHA256, key + " protocol identity differs")
        require(review.get("executed") is False and review.get("c1_payload_or_tensor_bodies_read") is False and review.get("c1_images_or_montages_viewed") is False and review.get("blocking_findings") == [], key + " blindness fields differ")
        require(review.get("scorer_author_role") == SCORER_AUTHOR_ROLE and review.get("wrapper_author_role") == WRAPPER_AUTHOR_ROLE, key + " author roles differ")
        require(type(review.get("reviewer_role")) is str and bool(review["reviewer_role"]), key + " reviewer role missing")
        parse_utc(review.get("completed_utc"), key + " completed_utc")
        reviews.append((path, review, binding[key]["sha256"]))
    roles = {SCORER_AUTHOR_ROLE, WRAPPER_AUTHOR_ROLE, reviews[0][1]["reviewer_role"], reviews[1][1]["reviewer_role"]}
    require(len(roles) == 4, "Scorer author, wrapper author, and two reviewers must be distinct")
    return reviews


def validate_numeric_review(record, expected_identities):
    path, review = load_bound(record, "numeric_guard_independent_review")
    require(review.get("schema") == "s45b-c1-numeric-camera-guard-independent-result-review-v1" and review.get("status") == "PASS_S45B_C1_NUMERIC_CAMERA_GUARD_INDEPENDENT_RESULT_REVIEW_V12", "V12 numeric guard lacks independent terminal PASS")
    require(review.get("row") == "C1" and review.get("passed") is True and review.get("requested_pose_K_guard_pass") is True, "V12 numeric guard row verdict differs")
    require(review.get("numeric_guard_terminal_schema") == "s45b-c1-numeric-camera-guard-terminal-pass-seal-v4" and review.get("numeric_guard_terminal_status") == "PASS_C1_REQUESTED_CAMERA_INPUT_CONDITION_GUARD_ONLY" and review.get("numeric_guard_terminal_authority") is True and review.get("observed_supervisor_returncode") == 0, "V12 terminal evidence assertion differs")
    require(review.get("pixels_decoded") == 0 and review.get("images_viewed") == 0 and review.get("blocking_findings") == [], "V12 independent review scope differs")
    assertions = review.get("row_validity_assertions")
    require(type(assertions) is dict and all(assertions.get(key) is True for key in REQUIRED_VALIDITY), "C1 row-validity assertions are incomplete")
    require(review.get("authoritative_pixel_identities") == expected_identities, "V12 row review does not preserve the exact S45 pixel identities")
    completed = parse_utc(review.get("completed_utc"), "numeric guard independent review completed_utc")
    return path, review, completed


def validate_contract(binding, expected_identities):
    contract_path, contract = load_bound(binding["bound_contract"], "bound_contract")
    contract_sha = binding["bound_contract"]["sha256"]
    require(contract.get("schema") == "s46-c1-blind-scoring-bound-contract-v1" and contract.get("status") == "BOUND_C1_IDENTITY_CANDIDATE_AWAITING_DUAL_SOURCE_REVIEW_AND_BLINDNESS_ATTESTATION" and contract.get("row") == "C1", "Bound C1 contract header differs")
    require(contract.get("template_path") == str(CONTRACT_TEMPLATE) and contract.get("template_sha256") == CONTRACT_TEMPLATE_SHA256, "Contract template identity differs")
    require(contract.get("frozen_math_sha256") == FROZEN_MATH_SHA256 and hashlib.sha256(canonical(contract.get("frozen_math"))).hexdigest() == FROZEN_MATH_SHA256, "Frozen C1 math tree differs")
    slots = contract.get("binding_slots")
    require(type(slots) is dict and slots.get("authorized_attempt") == 1 and slots.get("authorized_output_path") == str(OUTPUT), "Contract attempt differs")
    require(slots.get("archive_tensor_directory") == str(TENSOR_DIR) and slots.get("authoritative_pixel_identities") == expected_identities, "Contract pixel identity domain differs")
    require(slots.get("pixel_identity_source_record_label") == "row_validity_review" and slots.get("pixel_identities_json_pointer") == "/authoritative_pixel_identities" and slots.get("row_validity_assertions_json_pointer") == "/row_validity_assertions", "Contract identity/assertion pointers differ")
    require(slots.get("required_true_row_validity_assertions") == list(REQUIRED_VALIDITY), "Contract row-validity names differ")
    records = slots.get("upstream_records")
    require(type(records) is list and len(records) == 8, "Contract must bind eight upstream records")
    indexed = {record.get("label"): record for record in records if type(record) is dict}
    require(set(indexed) == set(FIXED_UPSTREAM) | {"row_validity_review"}, "Contract upstream labels differ")
    for label, frozen in FIXED_UPSTREAM.items():
        record = indexed[label]
        require(record.get("path") == str(frozen["path"]) and record.get("sha256") == frozen["sha256"], label + " contract identity differs")
        require(type(record.get("expected_json_fields")) is dict, label + " expected fields missing")
        for key, value in frozen["fields"].items():
            require(record["expected_json_fields"].get(key) == value, label + " contract assertion differs at " + key)
    row_record = indexed["row_validity_review"]
    require(row_record.get("path") == binding["numeric_guard_independent_review"]["path"] and row_record.get("sha256") == binding["numeric_guard_independent_review"]["sha256"], "Contract row-validity record is not the exact V12 independent review")
    return contract_path, contract, contract_sha


def validate_blindness(binding, contract_path, contract_sha, reviews, score_started):
    _, doc = load_bound(binding["blindness_attestation"], "blindness_attestation")
    require(doc.get("schema") == "s46-c1-blindness-attestation-v1" and doc.get("status") == "PASS_S46_C1_BLINDNESS_PRE_SCORE" and doc.get("row") == "C1", "Blindness attestation is not PASS")
    require(doc.get("scorer_path") == str(SCORER) and doc.get("scorer_sha256") == SCORER_SHA256 and doc.get("bound_contract_path") == str(contract_path) and doc.get("bound_contract_sha256") == contract_sha, "Blindness attestation source identities differ")
    require(doc.get("primary_source_review_path") == str(reviews[0][0]) and doc.get("primary_source_review_sha256") == reviews[0][2] and doc.get("adversarial_source_review_path") == str(reviews[1][0]) and doc.get("adversarial_source_review_sha256") == reviews[1][2], "Blindness attestation review identities differ")
    require(doc.get("authorized_attempt") == 1 and doc.get("authorized_output_path") == str(OUTPUT), "Blindness attempt differs")
    for field in ("generated_images_or_montages_viewed", "c1_tensor_or_image_payload_bodies_read_for_metric_selection", "c1_metrics_observed_before_attestation", "roi_pair_metric_or_threshold_changed_after_generation_started"):
        require(doc.get(field) is False, "Blindness field must be false: " + field)
    created = parse_utc(doc.get("created_utc"), "blindness created_utc")
    require(created >= max(parse_utc(reviews[0][1]["completed_utc"], "primary review UTC"), parse_utc(reviews[1][1]["completed_utc"], "adversarial review UTC")) and created <= score_started, "Blindness attestation ordering differs")


def load_math_kernel():
    raw, _ = read_snapshot(SCORER, expected_sha256=SCORER_SHA256, max_bytes=512 * 1024)
    namespace = {"__name__": "s46_frozen_c1_math", "__file__": str(SCORER)}
    exec(compile(raw, str(SCORER), "exec"), namespace)
    require(namespace.get("FROZEN_MATH_SHA256") == FROZEN_MATH_SHA256 and callable(namespace.get("score_frames")), "Frozen scorer interface differs")
    return namespace["score_frames"]


def write_new(path: Path, value) -> str:
    payload = json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False).encode("utf-8") + b"\n"
    with path.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    return hashlib.sha256(payload).hexdigest()


def publish_attempt(binding, identities, score_frames, np, score_started):
    stage = OUTPUT.parent / ("." + OUTPUT.name + ".staging")
    require(not OUTPUT.exists() and not stage.exists(), "C1 score attempt or staging already exists")
    stage.mkdir(mode=0o700)
    valid = False
    report_sha = None
    error = None
    try:
        loaded = validate_pixel_descriptors(identities, TENSOR_DIR, open_bodies=True, np=np)
        result = score_frames(loaded["frames"], np)
        report = {
            "schema": "s46-c1-blind-score-report-v1",
            "status": "PASS_C1_BLIND_SCORE_TECHNICALLY_VALID",
            "row": "C1",
            "completed_utc": utc(),
            "binding_path": str(BINDING),
            "binding_sha256": binding["_binding_sha256"],
            "frozen_scorer_sha256": SCORER_SHA256,
            "math_result": result,
            "c1_pixel_bodies_read": 9,
            "images_rendered_or_viewed": 0,
            "claim_boundary": "One machine-scored C1 baseline row; C2 remains mandatory and no visual quality, camera obedience, method gain, or novelty is established.",
        }
        report_sha = write_new(stage / "report.json", report)
        valid = True
    except Exception as caught:
        error = {"type": type(caught).__name__, "message": str(caught)}
    receipt = {
        "schema": "s46-c1-blind-score-receipt-v1",
        "status": "PASS_C1_BLIND_SCORE_TERMINAL" if valid else "FAILED_OR_TECHNICALLY_INVALID_C1_BLIND_SCORE_TERMINAL",
        "technically_valid": valid,
        "started_utc": score_started.isoformat(),
        "completed_utc": utc(),
        "attempt": 1,
        "out": str(OUTPUT),
        "binding_path": str(BINDING),
        "binding_sha256": binding["_binding_sha256"],
        "report_sha256": report_sha,
        "error": error,
        "model_generation_or_readback_calls": 0,
        "images_rendered_or_viewed": 0,
    }
    write_new(stage / "receipt.json", receipt)
    directory_fd = os.open(stage, os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    os.rename(stage, OUTPUT)
    parent_fd = os.open(OUTPUT.parent, os.O_RDONLY)
    try:
        os.fsync(parent_fd)
    finally:
        os.close(parent_fd)
    return 0 if valid else 2


def formal(args) -> int:
    require(HEX.fullmatch(args.wrapper_sha256 or "") is not None and read_snapshot(SELF, expected_sha256=args.wrapper_sha256, max_bytes=1024 * 1024)[1] == args.wrapper_sha256, "Caller-bound wrapper SHA differs")
    require(HEX.fullmatch(args.binding_sha256 or "") is not None, "Binding SHA is malformed")
    binding, _, _ = read_json_snapshot(BINDING, args.binding_sha256)
    required_keys = {"schema", "status", "completed_utc", "row", "wrapper", "scorer", "bound_contract", "primary_source_review", "adversarial_source_review", "blindness_attestation", "numeric_guard_independent_review", "authorized_output_path"}
    require(set(binding) == required_keys and binding.get("schema") == "s46-c1-blind-scoring-wrapper-execution-binding-v1" and binding.get("status") == "BOUND_C1_BLIND_SCORING_WRAPPER_EXECUTION_AWAITING_EXACT_GATE_VALIDATION" and binding.get("row") == "C1", "Execution binding header or fields differ")
    parse_utc(binding.get("completed_utc"), "binding completed_utc")
    require(binding.get("wrapper") == {"path": str(SELF), "sha256": args.wrapper_sha256} and binding.get("scorer") == {"path": str(SCORER), "sha256": SCORER_SHA256} and binding.get("authorized_output_path") == str(OUTPUT), "Execution binding fixed identities differ")
    real = validate_current_real_metadata()
    numeric_path, _, numeric_completed = validate_numeric_review(binding["numeric_guard_independent_review"], real["identities"])
    contract_path, _, contract_sha = validate_contract(binding, real["identities"])
    reviews = validate_source_reviews(binding, contract_path, contract_sha, args.wrapper_sha256)
    score_started = datetime.now(timezone.utc)
    validate_blindness(binding, contract_path, contract_sha, reviews, score_started)
    require(numeric_completed <= score_started and str(numeric_path) == binding["numeric_guard_independent_review"]["path"], "Numeric guard review must predate score")
    require(not OUTPUT.exists(), "Authorized C1 attempt already exists")
    import numpy as np
    require(np.__version__ == "1.26.4", "Formal score requires NumPy 1.26.4")
    binding["_binding_sha256"] = args.binding_sha256
    return publish_attempt(binding, real["identities"], load_math_kernel(), np, score_started)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binding-sha256", required=True)
    parser.add_argument("--wrapper-sha256", required=True)
    args = parser.parse_args()
    return formal(args)


if __name__ == "__main__":
    raise SystemExit(main())
