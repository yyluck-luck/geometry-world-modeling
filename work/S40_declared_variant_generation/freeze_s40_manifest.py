"""Freeze the actual S40 generation core and attach two external reviews.

Standard-library metadata only. This tool never imports a scientific model,
reads a component body, decodes an image, or starts generation.
"""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import traceback


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CANDIDATE = HERE / "manifest_candidate.json"
CANDIDATE_SHA256 = "d3515e5ff2da0843da6bbfcdb4e13105c513e10202653561259485f65d547543"
GENERATION_GATE_SHA256 = "ca16d8be631898e0200b14fcd0a19fd2d8bc6b91f32da4f5ada6038103ba7b14"
TOOL_FILES = (Path(__file__).resolve(), HERE / "FREEZE_PROTOCOL.md")


def utc():
    return datetime.now(timezone.utc).isoformat()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha256(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def signature(path):
    path = Path(path).resolve(strict=True)
    info = path.stat()
    require(stat.S_ISREG(info.st_mode), "Regular file required: " + str(path))
    return {
        "path": str(path),
        "size": info.st_size,
        "mtime_ns": info.st_mtime_ns,
        "ctime_ns": info.st_ctime_ns,
        "device": info.st_dev,
        "inode": info.st_ino,
    }


def write_new(path, payload):
    with Path(path).open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def bind_gate():
    path = HERE / "generation_gate.py"
    require(sha256(path) == GENERATION_GATE_SHA256, "Reviewed S40 gate changed")
    spec = importlib.util.spec_from_file_location("_s40_freeze_bound_gate", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def record(path):
    path = Path(path).resolve(strict=True)
    return {"path": str(path), "sha256": sha256(path)}


def reserved_roots():
    """Return the two fresh roots reserved for the later real S40 run."""
    require(sha256(CANDIDATE) == CANDIDATE_SHA256, "Reviewed S40 candidate changed")
    candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
    generation_root = Path(candidate["output_root"]).resolve()
    execution_root = (HERE / "execution_01").resolve()
    require(generation_root.is_absolute(), "S40 generation output root must be absolute")
    return generation_root, execution_root


def require_attach_core_uses_reserved_generation_root(args):
    """Preflight an external core before attach can create its output directory."""
    core_path = Path(args.core).resolve(strict=True)
    require(sha256(core_path) == args.core_sha256, "S40 core file SHA mismatch")
    core = json.loads(core_path.read_text(encoding="utf-8"))
    actual = core.get("output_root")
    require(isinstance(actual, str), "S40 core output root is missing")
    expected = reserved_roots()[0]
    require(Path(actual).resolve() == expected, "S40 core output root differs from reviewed candidate")


def paths_overlap(left, right):
    """True when either resolved path equals, contains, or is inside the other."""
    left = Path(left).resolve()
    right = Path(right).resolve()
    return left == right or left in right.parents or right in left.parents


def require_isolated_fresh_output(output):
    output = Path(output).resolve()
    for reserved in reserved_roots():
        require(not paths_overlap(output, reserved), "Freeze output overlaps reserved S40 run root: " + str(reserved))
        require(not reserved.exists(), "Reserved S40 run root is not fresh: " + str(reserved))


def prepare(args, output, gate, receipt):
    require(sha256(CANDIDATE) == CANDIDATE_SHA256, "Reviewed S40 candidate changed")
    core = json.loads(CANDIDATE.read_text(encoding="utf-8"))
    require(
        core.get("status") == "DRAFT_NOT_READY_FOR_GENERATION"
        and core.get("review_receipts") == {},
        "Only the reviewed empty-review candidate can be frozen",
    )
    require(core.get("source_identities") == gate.required_sources(), "Candidate source domain changed")
    require(core.get("controls") == gate.S39_GATE.REF.CONTROLS, "Candidate controls changed")
    require(core.get("runtime") == gate.RUNTIME, "Candidate runtime changed")
    require(core.get("generation_limits") == gate.LIMITS, "Candidate limits changed")
    require_isolated_fresh_output(output)

    s39_manifest = record(args.s39_manifest)
    parent = json.loads(Path(s39_manifest["path"]).read_text(encoding="utf-8"))
    gate.S39_GATE.check_manifest(s39_manifest["path"], s39_manifest["sha256"], metadata_only=True)

    evidence = {
        "launch": record(args.launch),
        "worker": record(args.worker),
        "runtime_loading": record(args.runtime_loading),
        "full_resource_gate": record(args.full_resource_gate),
    }
    loading_review = record(args.loading_review)
    core["components"] = copy.deepcopy(parent["components"])
    core["config"] = copy.deepcopy(parent["config"])
    core["input_image"] = copy.deepcopy(parent["input_image"])
    core["s39_loading_manifest"] = s39_manifest
    core["s39_resource_core_sha256"] = gate.core_sha256(parent)
    core["s39_loading_evidence"] = evidence
    core["s39_loading_review"] = loading_review
    core.pop("blocking_reasons", None)
    core.update(
        status=gate.FROZEN,
        evidence_kind="recorded_execution",
        created_utc=utc(),
        review_receipts={},
        freeze_preparation={
            "schema": "s40-generation-core-freeze-v1",
            "candidate_path": str(CANDIDATE),
            "candidate_sha256": CANDIDATE_SHA256,
            "tool_sources": {str(path): sha256(path) for path in TOOL_FILES},
            "actual_s39_records": {
                "manifest": s39_manifest,
                "evidence": evidence,
                "loading_review": loading_review,
            },
            "component_bodies_read": 0,
            "pixels_decoded": 0,
            "scientific_imports": 0,
            "purpose": "Await two separately authored reviews of this exact S40 core",
        },
    )

    gate.loading_chain(core)
    require(core["components"] == parent["components"], "Copied component identity changed")
    require(core["config"] == parent["config"], "Copied config identity changed")
    require(core["input_image"] == parent["input_image"], "Copied input identity changed")
    current_signatures = {
        name: signature(entry["path"])
        for name, entry in {
            "s39_manifest": s39_manifest,
            **evidence,
            "loading_review": loading_review,
        }.items()
    }

    path = output / "manifest_core.json"
    require_isolated_fresh_output(output)
    write_new(path, core)
    path.chmod(0o444)
    require_isolated_fresh_output(output)
    receipt.update(
        status="S40_CORE_FROZEN_AWAITING_REAL_REVIEWS",
        core_path=str(path),
        core_file_sha256=sha256(path),
        core_sha256=gate.core_sha256(core),
        s39_resource_core_sha256=core["s39_resource_core_sha256"],
        actual_s39_records=core["freeze_preparation"]["actual_s39_records"],
        actual_s39_record_signatures=current_signatures,
        execution_authorized=False,
    )


def attach_reviews(args, output, gate, receipt):
    core_path = Path(args.core).resolve(strict=True)
    require(sha256(core_path) == args.core_sha256, "S40 core file SHA mismatch")
    core = json.loads(core_path.read_text(encoding="utf-8"))
    require(
        core.get("schema") == gate.SCHEMA
        and core.get("status") == gate.FROZEN
        and core.get("variant") == gate.VARIANT
        and core.get("review_receipts") == {},
        "Only an unreviewed frozen S40 core is accepted",
    )
    actual_generation_root = core.get("output_root")
    require(
        isinstance(actual_generation_root, str)
        and Path(actual_generation_root).resolve() == reserved_roots()[0],
        "S40 core output root differs from reviewed candidate",
    )
    active_s39_records = {
        "manifest": core.get("s39_loading_manifest"),
        "evidence": core.get("s39_loading_evidence"),
        "loading_review": core.get("s39_loading_review"),
    }
    expected_preparation = {
        "schema": "s40-generation-core-freeze-v1",
        "candidate_path": str(CANDIDATE),
        "candidate_sha256": CANDIDATE_SHA256,
        "tool_sources": {str(path): sha256(path) for path in TOOL_FILES},
        "actual_s39_records": active_s39_records,
        "component_bodies_read": 0,
        "pixels_decoded": 0,
        "scientific_imports": 0,
        "purpose": "Await two separately authored reviews of this exact S40 core",
    }
    require(
        core.get("freeze_preparation") == expected_preparation,
        "S40 freeze preparation is incomplete or disagrees with active S39 records",
    )
    require_isolated_fresh_output(output)
    gate.loading_chain(core)

    final = copy.deepcopy(core)
    bindings = {
        "source_review": (args.source_review, args.source_review_sha256),
        "runtime_freeze": (args.runtime_freeze, args.runtime_freeze_sha256),
    }
    for role, (raw_path, expected) in bindings.items():
        path = Path(raw_path).resolve(strict=True)
        require(sha256(path) == expected, "S40 review file SHA mismatch: " + role)
        review = json.loads(path.read_text(encoding="utf-8"))
        require(
            review.get("status") == gate.REVIEW_STATUSES[role]
            and review.get("variant") == gate.VARIANT
            and review.get("core_sha256") == gate.core_sha256(core),
            "S40 review does not approve this core: " + role,
        )
        final["review_receipts"][role] = {"path": str(path), "sha256": expected}
    require(gate.core_sha256(final) == gate.core_sha256(core), "Reviews changed immutable S40 core")
    require(sha256(core_path) == args.core_sha256, "S40 core changed during attachment")

    manifest_path = output / "manifest.json"
    require_isolated_fresh_output(output)
    write_new(manifest_path, final)
    manifest_path.chmod(0o444)
    manifest_sha = sha256(manifest_path)
    metadata = gate.check_manifest(manifest_path, manifest_sha, metadata_only=True)
    write_new(output / "metadata_gate.json", metadata)
    require_isolated_fresh_output(output)
    receipt.update(
        status="S40_REVIEWS_ATTACHED_METADATA_GATE_PASSED",
        manifest_path=str(manifest_path),
        manifest_sha256=manifest_sha,
        core_sha256=gate.core_sha256(final),
        core_file_sha256=args.core_sha256,
        execution_authorized=False,
        worker_full_content_verification_still_required=True,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    prepare_parser = sub.add_parser("prepare")
    for name in (
        "s39-manifest",
        "launch",
        "worker",
        "runtime-loading",
        "full-resource-gate",
        "loading-review",
        "out",
    ):
        prepare_parser.add_argument("--" + name, required=True)
    attach_parser = sub.add_parser("attach-reviews")
    for name in (
        "core",
        "core-sha256",
        "source-review",
        "source-review-sha256",
        "runtime-freeze",
        "runtime-freeze-sha256",
        "out",
    ):
        attach_parser.add_argument("--" + name, required=True)
    args = parser.parse_args()

    output = Path(args.out).resolve()
    if args.mode == "attach-reviews":
        require_attach_core_uses_reserved_generation_root(args)
    require_isolated_fresh_output(output)
    output.mkdir(parents=True, exist_ok=False)
    receipt = {
        "schema": "s40-freeze-tool-receipt-v1",
        "started_utc": utc(),
        "mode": args.mode,
        "source_sha256": sha256(__file__),
        "protocol_sha256": sha256(HERE / "FREEZE_PROTOCOL.md"),
        "status": "CHECKING",
        "execution_authorized": False,
        "model_constructors": 0,
        "scientific_imports": 0,
        "component_body_bytes_read": 0,
        "pixels_decoded": 0,
        "generation_calls": 0,
    }
    try:
        gate = bind_gate()
        if args.mode == "prepare":
            prepare(args, output, gate, receipt)
        else:
            attach_reviews(args, output, gate, receipt)
    except BaseException as error:
        receipt.update(
            status="NOT_READY_S40_FREEZE_OR_REVIEW_ATTACHMENT_FAILED",
            error_type=type(error).__name__,
            error=str(error),
            traceback=traceback.format_exc(),
        )
    finally:
        receipt["completed_utc"] = utc()
        receipt["source_unchanged"] = sha256(__file__) == receipt["source_sha256"]
        receipt["protocol_unchanged"] = sha256(HERE / "FREEZE_PROTOCOL.md") == receipt["protocol_sha256"]
        if not receipt["source_unchanged"] or not receipt["protocol_unchanged"]:
            receipt["status"] = "FAILED_S40_FREEZE_SOURCE_CHANGED"
        write_new(output / "receipt.json", receipt)
    print(json.dumps({"status": receipt["status"], "completed_utc": receipt["completed_utc"]}, ensure_ascii=False))
    return 0 if receipt["status"] in {
        "S40_CORE_FROZEN_AWAITING_REAL_REVIEWS",
        "S40_REVIEWS_ATTACHED_METADATA_GATE_PASSED",
    } else 2


if __name__ == "__main__":
    raise SystemExit(main())
