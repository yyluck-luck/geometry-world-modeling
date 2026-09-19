#!/usr/bin/env python3
"""Create an identity-bound C1 scoring or recomputation candidate.

This is a metadata-only renderer.  It rejects metric/result fields and never
opens any referenced generation, readback, tensor, image, or score payload.
The output remains non-executable until the reviews and attestation described
by the corresponding template are complete.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent
SCORE_TEMPLATE = HERE / "C1_SCORING_CONTRACT_TEMPLATE.json"
SCORE_TEMPLATE_SHA256 = "79299749250c22dd9719d93964b9c179a8884f01c530bf07a45625c59395ab7b"
RECOMPUTE_TEMPLATE = HERE / "C1_INDEPENDENT_RECOMPUTE_BINDING_TEMPLATE.json"
RECOMPUTE_TEMPLATE_SHA256 = "dda75a1d6cf590972ea2b33d547e9a94efb6b68dacfa85917f86f8ece20fd0aa"
HEX = re.compile(r"^[0-9a-f]{64}$")
FORBIDDEN_KEY_FRAGMENT = re.compile(
    r"(metric|mse|psnr|score_value|row_event|pixel_value|tensor_value|quality_result)",
    re.IGNORECASE,
)
REQUIRED_RECORD_LABELS = {
    "generation_manifest",
    "generation_terminal_receipt",
    "generation_worker_receipt",
    "readback_supervisor_receipt",
    "readback_worker_receipt",
    "readback_report",
    "readback_result_review",
    "row_validity_review",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def canonical(value) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def parse_utc(value, label: str) -> None:
    require(type(value) is str and bool(value), label + " must be nonempty")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.tzinfo is not None and parsed.utcoffset() == timezone.utc.utcoffset(parsed),
            label + " must be timezone-aware UTC")


def canonical_absolute_string(value, label: str, *, directory: bool = False) -> str:
    require(type(value) is str and bool(value), label + " must be a nonempty string")
    path = Path(value)
    require(path.is_absolute() and ".." not in path.parts, label + " must be an absolute normalized path")
    require(value == str(path), label + " must use its direct normalized spelling")
    if not directory:
        require(bool(path.name), label + " must name a file")
    return value


def reject_result_content(value, label: str = "binding") -> None:
    if type(value) is dict:
        for key, child in value.items():
            require(type(key) is str, label + " contains a non-string key")
            require(FORBIDDEN_KEY_FRAGMENT.search(key) is None,
                    label + " contains forbidden result-like key: " + key)
            reject_result_content(child, label + "/" + key)
    elif type(value) is list:
        for index, child in enumerate(value):
            reject_result_content(child, label + "/%d" % index)
    else:
        require(type(value) in (str, int, bool, type(None)),
                label + " contains a non-JSON-scalar binding value")


def read_input(path: Path):
    require(path.is_absolute() and path.resolve() == path and path.is_file() and not path.is_symlink(),
            "Binding input must be a canonical regular non-symlink file")
    require(path.stat().st_size <= 4 * 1024 * 1024, "Binding input is too large")
    raw = path.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def read_template(path: Path, expected_sha: str):
    require(sha256(path) == expected_sha, "Template identity changed: " + str(path))
    return json.loads(path.read_text(encoding="utf-8"))


def validate_records(records) -> None:
    require(type(records) is list and len(records) == len(REQUIRED_RECORD_LABELS),
            "Exactly eight upstream metadata records are required")
    labels = set()
    for record in records:
        require(type(record) is dict and set(record) == {
            "label", "path", "sha256", "expected_json_fields"
        }, "Each upstream record must have the exact four binding fields")
        label = record["label"]
        require(type(label) is str and label in REQUIRED_RECORD_LABELS and label not in labels,
                "Upstream record label is missing, duplicated, or unexpected")
        labels.add(label)
        canonical_absolute_string(record["path"], label + " path")
        require(HEX.fullmatch(record["sha256"] or "") is not None,
                label + " SHA-256 is malformed")
        expected = record["expected_json_fields"]
        require(type(expected) is dict and bool(expected),
                label + " must freeze at least one non-result metadata assertion")
        for pointer, value in expected.items():
            require(type(pointer) is str and pointer.startswith("/") and "~" not in pointer,
                    label + " has a malformed simple JSON pointer")
            require(type(value) in (str, int, bool, type(None)),
                    label + " expected field must be a JSON scalar")
    require(labels == REQUIRED_RECORD_LABELS, "Required upstream record labels differ")


def validate_pixels(identities, tensor_directory: str) -> None:
    require(type(identities) is list and len(identities) == 9,
            "Exactly nine authoritative pixel identities are required")
    tensor_parent = Path(tensor_directory)
    for expected_id, item in enumerate(identities):
        require(type(item) is dict and set(item) == {
            "id", "tensor_descriptor_sha256", "tensor_body_sha256", "blob"
        }, "Pixel identity fields differ")
        descriptor = item["tensor_descriptor_sha256"]
        body = item["tensor_body_sha256"]
        blob = Path(canonical_absolute_string(item["blob"], "pixel blob"))
        require(item["id"] == expected_id and type(item["id"]) is int,
                "Pixel IDs must be the exact sequence 0 through 8")
        require(HEX.fullmatch(descriptor or "") is not None and HEX.fullmatch(body or "") is not None,
                "Pixel identity SHA-256 is malformed")
        require(blob.parent == tensor_parent and blob.name == descriptor + ".bin",
                "Pixel body must use its descriptor-addressed canonical tensor path")


def bind_score(template, binding, binding_path: Path, binding_sha: str):
    require(binding.get("schema") == "s46-c1-upstream-identity-binding-v1"
            and binding.get("status") == "READY_TO_BIND_C1_IDENTITIES_AFTER_INDEPENDENT_READBACK"
            and binding.get("row") == "C1",
            "C1 upstream identity binding header differs")
    parse_utc(binding.get("completed_utc"), "binding completed_utc")
    reject_result_content(binding)
    records = binding.get("upstream_records")
    validate_records(records)
    tensor_directory = canonical_absolute_string(
        binding.get("archive_tensor_directory"), "archive tensor directory", directory=True
    )
    identities = binding.get("authoritative_pixel_identities")
    validate_pixels(identities, tensor_directory)
    attempt = binding.get("authorized_attempt")
    out = canonical_absolute_string(binding.get("authorized_output_path"), "authorized output")
    require(type(attempt) is int and attempt >= 1
            and Path(out).parent == HERE
            and Path(out).name == "C1_score_attempt_%02d" % attempt,
            "Authorized C1 score attempt path and number differ")
    source_label = binding.get("pixel_identity_source_record_label")
    require(source_label in {"readback_report", "row_validity_review"},
            "Pixel identities must be traceable to readback_report or row_validity_review")
    identity_pointer = binding.get("pixel_identities_json_pointer")
    validity_pointer = binding.get("row_validity_assertions_json_pointer")
    for pointer in (identity_pointer, validity_pointer):
        require(type(pointer) is str and pointer.startswith("/") and "~" not in pointer,
                "Binding JSON pointer is malformed")
    result = dict(template)
    result["schema"] = "s46-c1-blind-scoring-bound-contract-v1"
    result["status"] = "BOUND_C1_IDENTITY_CANDIDATE_AWAITING_DUAL_SOURCE_REVIEW_AND_BLINDNESS_ATTESTATION"
    result["template_path"] = str(SCORE_TEMPLATE)
    result["template_sha256"] = SCORE_TEMPLATE_SHA256
    result["identity_binding_path"] = str(binding_path)
    result["identity_binding_sha256"] = binding_sha
    result["binding_slots"] = {
        "binding_completed_utc": binding["completed_utc"],
        "authorized_attempt": attempt,
        "authorized_output_path": out,
        "required_upstream_record_labels": sorted(REQUIRED_RECORD_LABELS),
        "upstream_records": records,
        "authoritative_pixel_identities": identities,
        "pixel_identity_source_record_label": source_label,
        "pixel_identities_json_pointer": identity_pointer,
        "archive_tensor_directory": tensor_directory,
        "row_validity_record_label": "row_validity_review",
        "row_validity_assertions_json_pointer": validity_pointer,
        "required_true_row_validity_assertions": template["binding_slots"]["required_true_row_validity_assertions"],
    }
    require(
        hashlib.sha256(canonical(result["frozen_math"])).hexdigest()
        == template["frozen_math_sha256"],
        "Frozen C1 mathematical subtree changed during identity binding",
    )
    return result


def bind_recompute(template, binding, binding_path: Path, binding_sha: str):
    require(binding.get("schema") == "s46-c1-recompute-identity-binding-v1"
            and binding.get("status") == "READY_TO_BIND_AFTER_SEALED_C1_PRIMARY_SCORE"
            and binding.get("row") == "C1",
            "C1 recomputation identity binding header differs")
    parse_utc(binding.get("completed_utc"), "binding completed_utc")
    reject_result_content(binding)
    attempt = binding.get("sealed_score_attempt")
    require(type(attempt) is int and attempt >= 1, "Sealed score attempt is malformed")
    fields = (
        "sealed_score_receipt_path", "sealed_score_receipt_sha256",
        "sealed_score_report_path", "sealed_score_report_sha256",
        "recompute_source_path", "recompute_source_sha256",
        "authorized_output_path",
    )
    for field in fields:
        require(field in binding, "Missing recomputation identity field: " + field)
    for field in ("sealed_score_receipt_path", "sealed_score_report_path", "recompute_source_path",
                  "authorized_output_path"):
        canonical_absolute_string(binding[field], field)
    for field in ("sealed_score_receipt_sha256", "sealed_score_report_sha256", "recompute_source_sha256"):
        require(HEX.fullmatch(binding[field] or "") is not None, field + " is malformed")
    result = dict(template)
    result.update({
        "schema": "s46-c1-independent-recompute-bound-binding-v1",
        "status": "BOUND_C1_RECOMPUTE_CANDIDATE_AWAITING_DIFFERENT_AUTHOR_SOURCE_REVIEW",
        "template_path": str(RECOMPUTE_TEMPLATE),
        "template_sha256": RECOMPUTE_TEMPLATE_SHA256,
        "identity_binding_path": str(binding_path),
        "identity_binding_sha256": binding_sha,
        "binding_completed_utc": binding["completed_utc"],
        "sealed_score_attempt": attempt,
        "sealed_score_receipt_path": binding["sealed_score_receipt_path"],
        "sealed_score_receipt_sha256": binding["sealed_score_receipt_sha256"],
        "sealed_score_report_path": binding["sealed_score_report_path"],
        "sealed_score_report_sha256": binding["sealed_score_report_sha256"],
        "recompute_source_path": binding["recompute_source_path"],
        "recompute_source_sha256": binding["recompute_source_sha256"],
        "recompute_source_review_path": None,
        "recompute_source_review_sha256": None,
        "authorized_output_path": binding["authorized_output_path"],
    })
    return result


def write_create_only(path: Path, value) -> None:
    require(path.is_absolute() and path.parent == HERE and not os.path.lexists(path),
            "Output must be a fresh direct child of the S46 preparation directory")
    payload = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    with path.open("x", encoding="utf-8") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=("score", "recompute"), required=True)
    parser.add_argument("--binding", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    binding_path = Path(args.binding)
    binding, binding_sha = read_input(binding_path)
    if args.kind == "score":
        template = read_template(SCORE_TEMPLATE, SCORE_TEMPLATE_SHA256)
        result = bind_score(template, binding, binding_path, binding_sha)
    else:
        template = read_template(RECOMPUTE_TEMPLATE, RECOMPUTE_TEMPLATE_SHA256)
        result = bind_recompute(template, binding, binding_path, binding_sha)
    write_create_only(Path(args.out), result)
    print(json.dumps({
        "status": result["status"],
        "out": args.out,
        "sha256": sha256(Path(args.out)),
        "payloads_opened": 0,
        "images_viewed": 0,
        "formal_score_executed": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
