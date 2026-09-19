#!/usr/bin/env python3
"""Candidate external supervisor for the unique C1 saved-output readback.

This entry is inert until exact independent source reviews and a real post-run
terminal binding are supplied.  It reuses the reviewed S40 v3.3 process monitor
through a reversible AST label derivation, while replacing its source and
generation-input validators with C1-specific fail-closed checks.
"""
from __future__ import annotations

import argparse
import ast
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import traceback
import uuid


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
C1 = ROOT / "work/S44_c1_confirmation_generation"
C1_EXECUTION = C1 / "execution_01"
C1_OUTPUT = ROOT / "results/S44_C1_confirmation_generation"
C1_MANIFEST = C1 / "review_attachment_01/manifest.json"
C1_MANIFEST_SHA256 = "1e86e8279c608995a03d6675a8636c354d6d4d046b7c8faea9611d6e6a9fd93b"
C1_LAUNCHER = C1 / "launch_generation.py"
C1_LAUNCHER_SHA256 = "c94a982b0c0cb3fa895323ca9d7aa4e2b91eb7146eece35bdb0aedd1c157a74b"

BASE_SUPERVISOR = ROOT / "work/S40_result_readback/supervise_readback.py"
BASE_SUPERVISOR_SHA256 = "f04b9bcd4a0e2908d2bc3ead9a732e16d4f4ef651a60541a87f37a7b37f2b238"
BASE_READBACK = ROOT / "work/S40_result_readback/readback.py"
BASE_READBACK_SHA256 = "d4c22504569ad1fb1fcc74ea1da83b4f244f4de803f5d0fadc16e8da06777933"

SELF = Path(__file__).resolve()
READBACK = HERE / "readback.py"
READBACK_PROTOCOL = HERE / "PROTOCOL.md"
SUPERVISOR_PROTOCOL = HERE / "SUPERVISOR_PROTOCOL.md"
PREPARATION_RECEIPT = HERE / "preparation_receipt.json"
READBACK_REVIEW_PRIMARY = HERE / "SOURCE_REVIEW_PRIMARY.json"
READBACK_REVIEW_ADVERSARIAL = HERE / "SOURCE_REVIEW_ADVERSARIAL.json"
SUPERVISOR_REVIEW = HERE / "SUPERVISOR_SOURCE_REVIEW.json"
TERMINAL_BINDING = HERE / "terminal_binding_01.json"
PYTHON = ROOT / ".venv-cut3r/bin/python"

SUPERVISION_DIRECTORY_NAME = "supervision_01"
READBACK_DIRECTORY_NAME = "executed_01"
SUCCESS = "C1_READBACK_RETURNED_PENDING_INDEPENDENT_RESULT_REVIEW"
HEX = re.compile(r"^[0-9a-f]{64}$")

LABELS = {
    "s40-readback-external-supervisor-v1": "s45-c1-readback-external-supervisor-v1",
    "s40-readback-launch-ticket-v1": "s45-c1-readback-launch-ticket-v1",
    "S40_READBACK_RETURNED_PENDING_INDEPENDENT_REVIEW": SUCCESS,
    "FAILED_OR_PARTIAL_SUPERVISED_S40_READBACK":
        "FAILED_OR_PARTIAL_SUPERVISED_C1_READBACK",
    "NOT_READY_BEFORE_S40_READBACK": "NOT_READY_BEFORE_C1_READBACK",
    "s40-real-saved-output-readback-v1": "s45-c1-real-saved-output-readback-v1",
    "PASS_SAVED_S40_IDENTITIES_AND_CACHE_CONSUMPTION_ONLY":
        "PASS_SAVED_C1_IDENTITIES_AND_CACHE_CONSUMPTION_ONLY",
    "FAILED_OR_PARTIAL_S40_READBACK": "FAILED_OR_PARTIAL_C1_READBACK",
    "s40_execution_receipt_path": "c1_execution_receipt_path",
    "s40_execution_receipt_sha256": "c1_execution_receipt_sha256",
    "Saved complete archive identities and actual first-output/cache/second-condition/sampler latent chain; no model, rendering or video quality recomputation":
        "Saved C1 complete archive identities and actual first-output/cache/second-condition/sampler latent chain; no model, rendering or image-quality recomputation",
}
EXPECTED_LABEL_COUNTS = {
    "s40-readback-external-supervisor-v1": 2,
    "s40-readback-launch-ticket-v1": 1,
    "S40_READBACK_RETURNED_PENDING_INDEPENDENT_REVIEW": 1,
    "FAILED_OR_PARTIAL_SUPERVISED_S40_READBACK": 5,
    "NOT_READY_BEFORE_S40_READBACK": 1,
    "s40-real-saved-output-readback-v1": 2,
    "PASS_SAVED_S40_IDENTITIES_AND_CACHE_CONSUMPTION_ONLY": 1,
    "FAILED_OR_PARTIAL_S40_READBACK": 1,
    "s40_execution_receipt_path": 3,
    "s40_execution_receipt_sha256": 2,
    "Saved complete archive identities and actual first-output/cache/second-condition/sampler latent chain; no model, rendering or video quality recomputation": 1,
}

_ACTIVE_ARGS = None


def utc():
    return datetime.now(timezone.utc).isoformat()


def parse_utc(value, label):
    require(isinstance(value, str) and value, label + " must be a nonempty timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise RuntimeError(label + " is not valid ISO-8601") from error
    require(
        parsed.tzinfo is not None and parsed.utcoffset() == timezone.utc.utcoffset(parsed),
        label + " must be timezone-aware UTC",
    )
    return parsed


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha256(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def lexists(path):
    return os.path.lexists(os.fspath(path))


def safe_fresh_child_directory(raw, label, expected_name):
    """Reject every existing directory entry, including a broken symlink."""
    candidate = Path(raw)
    require(candidate.is_absolute(), label + " must be an absolute path")
    require(candidate.name == expected_name,
            label + " must have the fixed basename " + expected_name)
    require(candidate.parent.resolve() == HERE,
            label + " must be a direct child of " + str(HERE))
    require(not lexists(candidate), label + " must be a fresh absent filesystem entry")
    resolved = candidate.resolve(strict=False)
    require(resolved.parent == HERE and resolved.name == expected_name,
            label + " canonical path differs")
    require(HERE.is_dir(), label + " parent is unavailable")
    return resolved


def _terminal_binding(namespace, expected_sha256):
    require(HEX.fullmatch(expected_sha256 or ""),
            "Terminal binding SHA-256 must be lowercase hexadecimal")
    binding, stat = namespace["read_bound_json"](
        TERMINAL_BINDING,
        expected_sha256,
        "C1 terminal binding",
    )
    require(
        binding.get("schema") == "s45-c1-terminal-binding-v1"
        and binding.get("status") == "FROZEN_C1_TERMINAL_SUCCESS_AND_FULL_ARCHIVE_BINDING"
        and binding.get("row") == "C1"
        and binding.get("placeholder_hashes") == 0
        and binding.get("created_after_terminal") is True,
        "C1 terminal binding is partial, pending, or from another row",
    )
    parse_utc(binding.get("created_utc"), "C1 terminal binding created_utc")
    return binding, stat


def derive_supervisor(*, compile_only=False):
    """Derive the process monitor and install C1-specific validators."""
    require(sha256(BASE_SUPERVISOR) == BASE_SUPERVISOR_SHA256,
            "Reviewed S40 v3.3 supervisor parent changed")
    original = ast.parse(BASE_SUPERVISOR.read_bytes(), filename=str(BASE_SUPERVISOR))
    derived = copy.deepcopy(original)
    changes = {}
    counts = {label: 0 for label in LABELS}

    def changed(old, new):
        new = ast.copy_location(new, old)
        key = (type(new).__name__, new.lineno, new.col_offset)
        if key in changes:
            raise RuntimeError("Overlapping C1 supervisor derivation edits")
        changes[key] = (copy.deepcopy(old), ast.dump(new, include_attributes=False))
        return new

    class Labels(ast.NodeTransformer):
        def visit_Constant(self, node):
            if isinstance(node.value, str) and node.value in LABELS:
                counts[node.value] += 1
                return changed(node, ast.Constant(LABELS[node.value]))
            return node

    derived = Labels().visit(derived)
    ast.fix_missing_locations(derived)
    require(counts == EXPECTED_LABEL_COUNTS,
            "Unexpected reviewed-supervisor label counts: " + str(counts))

    restored_keys = set()

    class Restore(ast.NodeTransformer):
        def generic_visit(self, node):
            key = (
                type(node).__name__,
                getattr(node, "lineno", None),
                getattr(node, "col_offset", None),
            )
            if key in changes:
                old, derived_dump = changes[key]
                require(ast.dump(node, include_attributes=False) == derived_dump,
                        "C1 supervisor derivation subtree changed")
                restored_keys.add(key)
                return copy.deepcopy(old)
            return super().generic_visit(node)

    restored = Restore().visit(copy.deepcopy(derived))
    require(
        len(restored_keys) == len(changes)
        and ast.dump(restored, include_attributes=False)
        == ast.dump(original, include_attributes=False),
        "C1 supervisor differs from reviewed S40 v3.3 beyond declared labels",
    )
    proof = {
        "parent_path": str(BASE_SUPERVISOR),
        "parent_sha256": BASE_SUPERVISOR_SHA256,
        "label_counts": counts,
        "reversible_full_AST_equal": True,
        "inherited_process_tree_monitor": True,
        "inherited_300_second_2gib_10gib_limits": True,
        "c1_specific_validators_installed": True,
        "model_renderer_generation_calls": 0,
    }
    if compile_only:
        compile(derived, str(BASE_SUPERVISOR) + "[S45 C1 labels]", "exec")
        return proof

    namespace = {
        "__file__": str(SELF),
        "__name__": "_s45_c1_derived_supervisor",
    }
    exec(compile(derived, str(BASE_SUPERVISOR) + "[S45 C1 labels]", "exec"), namespace)

    namespace.update(
        HERE=HERE,
        ROOT=ROOT,
        S40=C1,
        SELF=SELF,
        SUPERVISOR_PROTOCOL=SUPERVISOR_PROTOCOL,
        SUPERVISOR_REVIEW=SUPERVISOR_REVIEW,
        READBACK=READBACK,
        READBACK_PROTOCOL=READBACK_PROTOCOL,
        GENERATION_LAUNCHER=C1_LAUNCHER,
        PYTHON=PYTHON,
        SUPERVISION_DIRECTORY_NAME=SUPERVISION_DIRECTORY_NAME,
        READBACK_DIRECTORY_NAME=READBACK_DIRECTORY_NAME,
        SUCCESS=SUCCESS,
        READBACK_SHA256=sha256(READBACK),
        GENERATION_LAUNCHER_SHA256=C1_LAUNCHER_SHA256,
        fresh_child_directory=safe_fresh_child_directory,
    )

    def source_identities_at_start(expected_self_sha256, expected_review_sha256):
        args = _ACTIVE_ARGS
        require(args is not None, "C1 supervisor arguments are unavailable")
        require(HEX.fullmatch(expected_self_sha256 or ""),
                "Supervisor SHA-256 must be lowercase hexadecimal")
        require(expected_self_sha256 == sha256(SELF),
                "Caller did not bind the exact current supervisor source")
        require(expected_review_sha256 == args.supervisor_review_sha256,
                "Supervisor review SHA binding differs")

        current = {
            str(SELF): expected_self_sha256,
            str(READBACK): sha256(READBACK),
            str(READBACK_PROTOCOL): sha256(READBACK_PROTOCOL),
            str(SUPERVISOR_PROTOCOL): sha256(SUPERVISOR_PROTOCOL),
            str(BASE_READBACK): BASE_READBACK_SHA256,
            str(BASE_SUPERVISOR): BASE_SUPERVISOR_SHA256,
            str(PREPARATION_RECEIPT): args.preparation_receipt_sha256,
            str(READBACK_REVIEW_PRIMARY): args.worker_review_primary_sha256,
            str(READBACK_REVIEW_ADVERSARIAL): args.worker_review_adversarial_sha256,
            str(SUPERVISOR_REVIEW): args.supervisor_review_sha256,
        }
        records = {}
        for raw, expected in current.items():
            records[raw] = namespace["bound_file_record"](
                Path(raw), expected, "bound C1 readback source " + raw
            )

        preparation, _ = namespace["read_bound_json"](
            PREPARATION_RECEIPT,
            args.preparation_receipt_sha256,
            "S45 preparation receipt",
        )
        expected_sources = {
            str(READBACK): current[str(READBACK)],
            str(READBACK_PROTOCOL): current[str(READBACK_PROTOCOL)],
            str(SELF): current[str(SELF)],
            str(SUPERVISOR_PROTOCOL): current[str(SUPERVISOR_PROTOCOL)],
            str(BASE_READBACK): BASE_READBACK_SHA256,
            str(BASE_SUPERVISOR): BASE_SUPERVISOR_SHA256,
        }
        operations = preparation.get("operations", {})
        require(
            preparation.get("schema") == "s45-c1-readback-preparation-v1"
            and preparation.get("status")
            == "SOURCE_ONLY_AWAITING_C1_TERMINAL_BINDING_AND_INDEPENDENT_SOURCE_REVIEWS"
            and preparation.get("author_role") == "/root/c1_readback_builder"
            and preparation.get("source_identities") == expected_sources
            and preparation.get("c1_manifest", {}).get("sha256") == C1_MANIFEST_SHA256
            and preparation.get("terminal_binding_created") is False
            and operations.get("c1_payload_bytes_read") == 0
            and operations.get("pixels_decoded") == 0
            and operations.get("scientific_arrays_mapped") == 0
            and operations.get("readback_runs") == 0
            and operations.get("model_renderer_generation_runs") == 0,
            "Preparation receipt is not the exact zero-payload source-only record",
        )

        worker_identities = {
            "readback.py": current[str(READBACK)],
            "PROTOCOL.md": current[str(READBACK_PROTOCOL)],
            "s40_v3_3_parent": BASE_READBACK_SHA256,
            "preparation_receipt.json": args.preparation_receipt_sha256,
        }
        worker_reviews = []
        for path, digest, kind in (
            (READBACK_REVIEW_PRIMARY, args.worker_review_primary_sha256, "primary"),
            (READBACK_REVIEW_ADVERSARIAL, args.worker_review_adversarial_sha256, "adversarial"),
        ):
            review, _ = namespace["read_bound_json"](path, digest, kind + " worker source review")
            require(
                review.get("schema") == "s45-c1-readback-source-review-v1"
                and review.get("review_kind") == kind
                and review.get("status") == "PASS_S45_C1_READBACK_SOURCE_REVIEW"
                and review.get("verdict") == "PASS_SOURCE_NOT_EXECUTED"
                and review.get("reviewed_identities") == worker_identities
                and review.get("executed") is False
                and review.get("c1_payload_bytes_read") == 0
                and review.get("pixels_decoded") == 0
                and review.get("scientific_arrays_mapped") == 0
                and review.get("blocking_findings") == [],
                "Worker source review is incomplete or belongs to another source set",
            )
            worker_reviews.append(review)

        supervisor, _ = namespace["read_bound_json"](
            SUPERVISOR_REVIEW,
            args.supervisor_review_sha256,
            "supervisor source review",
        )
        supervisor_identities = {
            "supervise_readback.py": current[str(SELF)],
            "SUPERVISOR_PROTOCOL.md": current[str(SUPERVISOR_PROTOCOL)],
            "s40_v3_3_supervisor_parent": BASE_SUPERVISOR_SHA256,
            "readback.py": current[str(READBACK)],
            "PROTOCOL.md": current[str(READBACK_PROTOCOL)],
            "preparation_receipt.json": args.preparation_receipt_sha256,
            "SOURCE_REVIEW_PRIMARY.json": args.worker_review_primary_sha256,
            "SOURCE_REVIEW_ADVERSARIAL.json": args.worker_review_adversarial_sha256,
        }
        require(
            supervisor.get("schema") == "s45-c1-readback-supervisor-source-review-v1"
            and supervisor.get("status") == "PASS_S45_C1_READBACK_SUPERVISOR_SOURCE_REVIEW"
            and supervisor.get("verdict") == "PASS_SUPERVISOR_NOT_EXECUTED"
            and supervisor.get("reviewed_identities") == supervisor_identities
            and supervisor.get("executed") is False
            and supervisor.get("c1_payload_bytes_read") == 0
            and supervisor.get("pixels_decoded") == 0
            and supervisor.get("scientific_arrays_mapped") == 0
            and supervisor.get("blocking_findings") == [],
            "Supervisor source review is incomplete or belongs to another source set",
        )
        roles = [
            worker_reviews[0].get("reviewer_role"),
            worker_reviews[1].get("reviewer_role"),
            supervisor.get("reviewer_role"),
        ]
        worker_authors = [
            worker_reviews[0].get("author_role"),
            worker_reviews[1].get("author_role"),
        ]
        supervisor_author = supervisor.get("author_role")
        require(
            all(isinstance(role, str) and role for role in roles)
            and len(set(roles)) == 3
            and all(author == "/root/c1_readback_builder" for author in worker_authors)
            and supervisor_author == "/root"
            and all(
                role not in {"/root/c1_readback_builder", "/root"}
                for role in roles
            ),
            "Source reviews do not have three distinct roles independent of the actual source authors",
        )
        return records

    def validate_generation_inputs(manifest_path, manifest_sha, generation_receipt_path,
                                   generation_receipt_sha):
        args = _ACTIVE_ARGS
        binding, binding_stat = _terminal_binding(namespace, args.terminal_binding_sha256)
        expected_formal = {
            "supervision": str(HERE / SUPERVISION_DIRECTORY_NAME),
            "readback_output": str(HERE / READBACK_DIRECTORY_NAME),
        }
        require(binding.get("formal_readback_paths") == expected_formal,
                "Terminal binding names another formal readback attempt")

        refs = {}
        for key in (
            "manifest", "external_receipt", "worker_receipt", "full_resource_gate",
            "runtime_loading", "observation_summary", "archive_manifest", "trace_events",
        ):
            ref = binding.get(key)
            require(
                isinstance(ref, dict)
                and isinstance(ref.get("path"), str)
                and Path(ref["path"]).is_absolute()
                and isinstance(ref.get("sha256"), str)
                and HEX.fullmatch(ref["sha256"]),
                "Malformed terminal binding block: " + key,
            )
            refs[key] = {"path": Path(ref["path"]).resolve(), "sha256": ref["sha256"]}

        require(
            refs["manifest"] == {"path": C1_MANIFEST, "sha256": C1_MANIFEST_SHA256}
            and manifest_path == C1_MANIFEST
            and manifest_sha == C1_MANIFEST_SHA256,
            "Terminal binding or invocation does not use the canonical C1 manifest",
        )
        require(
            refs["external_receipt"]["path"] == C1_EXECUTION / "receipt.json"
            and generation_receipt_path == refs["external_receipt"]["path"]
            and generation_receipt_sha == refs["external_receipt"]["sha256"],
            "Terminal binding or invocation names another C1 external receipt",
        )
        require(
            refs["worker_receipt"]["path"] == C1_EXECUTION / "worker_receipt.json"
            and refs["full_resource_gate"]["path"] == C1_EXECUTION / "full_resource_gate.json"
            and refs["runtime_loading"]["path"] == C1_OUTPUT / "runtime_loading.json"
            and refs["observation_summary"]["path"] == C1_OUTPUT / "observation_summary.json"
            and refs["archive_manifest"]["path"] == C1_OUTPUT / "archive/manifest.json"
            and refs["trace_events"]["path"] == C1_OUTPUT / "trace/events.jsonl",
            "Terminal binding contains a noncanonical C1 evidence path",
        )

        manifest, manifest_stat = namespace["read_bound_json"](
            C1_MANIFEST, C1_MANIFEST_SHA256, "canonical C1 manifest"
        )
        require(
            manifest.get("schema") == "s44-c1-confirmation-two-batch-v1"
            and manifest.get("status") == "FROZEN_C1_BASELINE_CONFIRMATION_TWO_BATCH_EXECUTION"
            and manifest.get("derivation_policy", {}).get("row") == "C1"
            and manifest.get("output_root") == str(C1_OUTPUT)
            and len(manifest.get("source_identities", {})) == 218
            and manifest.get("source_identities", {}).get(str(C1_LAUNCHER)) == C1_LAUNCHER_SHA256
            and manifest.get("variant", {}).get("repo") == "stabilityai/sd-vae-ft-mse"
            and manifest.get("variant", {}).get("exact_original_baseline") is False,
            "Canonical C1 manifest contract differs",
        )

        external, external_stat = namespace["read_bound_json"](
            refs["external_receipt"]["path"], refs["external_receipt"]["sha256"],
            "C1 terminal external receipt"
        )
        boundary = external.get("trace_budget_boundary", {})
        completed = boundary.get("completed", [])
        require(
            external.get("schema") == "s44-c1-confirmation-launch-v1"
            and external.get("status")
            == "C1_BASELINE_EXTERNAL_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW"
            and external.get("manifest_sha256") == C1_MANIFEST_SHA256
            and Path(external.get("manifest_path", "")).resolve() == C1_MANIFEST
            and external.get("source_sha256") == C1_LAUNCHER_SHA256
            and external.get("source_unchanged_at_close") is True
            and external.get("worker_spawned") is True
            and external.get("returncode") == 0
            and external.get("worker_status")
            == "C1_BASELINE_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW"
            and external.get("worker_receipt_sha256") == refs["worker_receipt"]["sha256"]
            and "limit_exceeded" not in external
            and "unexpected_live_descendants" not in external
            and boundary.get("session_closed") is True
            and boundary.get("seen_failure") is False
            and boundary.get("pending_bytes") == 0
            and isinstance(completed, list)
            and len(completed) == 2
            and [item.get("retained_frame_ids") for item in completed]
            == [[1, 2, 3, 4], [5, 6, 7, 8]],
            "C1 external receipt is not a clean closed two-batch terminal result",
        )
        binding_created_utc = parse_utc(
            binding.get("created_utc"), "C1 terminal binding created_utc"
        )
        external_completed_utc = parse_utc(
            external.get("completed_utc"), "C1 external receipt completed_utc"
        )
        require(
            external_completed_utc < binding_created_utc,
            "C1 terminal binding was not created after the terminal receipt",
        )

        worker, worker_stat = namespace["read_bound_json"](
            refs["worker_receipt"]["path"], refs["worker_receipt"]["sha256"],
            "C1 terminal worker receipt"
        )
        require(
            worker.get("schema") == "s44-c1-confirmation-worker-v1"
            and worker.get("status") == "C1_BASELINE_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW"
            and worker.get("manifest_sha256") == C1_MANIFEST_SHA256
            and worker.get("source_sha256") == C1_LAUNCHER_SHA256
            and worker.get("source_unchanged_at_close") is True
            and worker.get("runtime_factory_calls") == 1
            and worker.get("full_resource_checks") == 1
            and worker.get("observation_summary_sha256") == refs["observation_summary"]["sha256"]
            and worker.get("trace_events_sha256") == refs["trace_events"]["sha256"]
            and worker.get("archive_receipt", {}).get("sha256")
            == refs["archive_manifest"]["sha256"],
            "C1 worker receipt is incomplete or not bound to the terminal set",
        )

        gate, gate_stat = namespace["read_bound_json"](
            refs["full_resource_gate"]["path"], refs["full_resource_gate"]["sha256"],
            "C1 full resource gate"
        )
        require(
            gate.get("schema") == "s44-c1-generation-resource-gate-v1"
            and gate.get("status") == "PASS_C1_DECLARED_GENERATION_RESOURCE_GATE"
            and gate.get("manifest_sha256") == C1_MANIFEST_SHA256,
            "C1 full resource gate is incomplete or unbound",
        )
        loading, loading_stat = namespace["read_bound_json"](
            refs["runtime_loading"]["path"], refs["runtime_loading"]["sha256"],
            "C1 runtime loading receipt"
        )
        require(
            loading.get("status") == "PASS_S44_C1_DECLARED_VARIANT_COMPONENT_LOADING_ONLY"
            and loading.get("manifest_sha256") == C1_MANIFEST_SHA256
            and loading.get("variant") == manifest.get("variant")
            and isinstance(loading.get("state_dict_loads"), list)
            and bool(loading.get("state_dict_loads"))
            and all(item.get("missing_keys") == [] and item.get("unexpected_keys") == []
                    for item in loading["state_dict_loads"]),
            "C1 runtime loading record is not the clean declared-variant load",
        )
        summary, summary_stat = namespace["read_bound_json"](
            refs["observation_summary"]["path"], refs["observation_summary"]["sha256"],
            "C1 observation summary"
        )
        require(summary.get("batches") is not None,
                "C1 observation summary does not contain batch records")

        archive, archive_stat = namespace["read_bound_json"](
            refs["archive_manifest"]["path"], refs["archive_manifest"]["sha256"],
            "C1 full archive manifest"
        )
        require(
            archive.get("status") == "ARCHIVE_COMPLETE"
            and archive.get("evidence_kind") == "recorded_execution"
            and archive.get("caller_manifest_sha256") == C1_MANIFEST_SHA256
            and archive.get("source_identities") == manifest.get("source_identities")
            and not archive.get("missing_required_names")
            and archive.get("failed_captures") == 0
            and worker.get("archive_receipt", {}).get("path")
            == str(refs["archive_manifest"]["path"]),
            "C1 full archive is not terminally complete",
        )
        trace_record = namespace["bound_file_record"](
            refs["trace_events"]["path"], refs["trace_events"]["sha256"],
            "C1 trace events chain"
        )

        review_refs = binding.get("terminal_reviews", {})
        terminal_reviews = []
        terminal_review_times = []
        review_statuses = {
            "external_execution": "PASS_S44_C1_TERMINAL_EXECUTION_EVIDENCE_REVIEW",
            "archive_trace_metadata": "PASS_S44_C1_ARCHIVE_TRACE_METADATA_REVIEW",
        }
        review_bindings = {
            "manifest_sha256": C1_MANIFEST_SHA256,
            "external_receipt_sha256": refs["external_receipt"]["sha256"],
            "worker_receipt_sha256": refs["worker_receipt"]["sha256"],
            "archive_manifest_sha256": refs["archive_manifest"]["sha256"],
            "trace_events_sha256": refs["trace_events"]["sha256"],
        }
        review_records = {}
        for role, status in review_statuses.items():
            ref = review_refs.get(role, {})
            require(
                isinstance(ref.get("path"), str)
                and Path(ref["path"]).is_absolute()
                and isinstance(ref.get("sha256"), str)
                and HEX.fullmatch(ref["sha256"]),
                "Malformed terminal review binding: " + role,
            )
            path = Path(ref["path"]).resolve()
            review, review_stat = namespace["read_bound_json"](
                path, ref["sha256"], "C1 terminal review " + role
            )
            require(
                review.get("schema") == "s44-c1-terminal-evidence-review-v1"
                and review.get("status") == status
                and review.get("bindings") == review_bindings
                and review.get("executed") is False
                and review.get("blocking_findings") == []
                and review.get("quality_status") == "NOT_EVALUATED"
                and review.get("method_or_novelty_status") == "NOT_EVALUATED",
                "C1 terminal review is incomplete or overclaims: " + role,
            )
            reviewed_utc = parse_utc(
                review.get("reviewed_utc"), "C1 terminal review reviewed_utc: " + role
            )
            require(
                external_completed_utc < reviewed_utc <= binding_created_utc,
                "C1 terminal review ordering differs: " + role,
            )
            terminal_reviews.append(review)
            terminal_review_times.append(reviewed_utc.isoformat())
            review_records[str(path)] = {**review_stat, "sha256": ref["sha256"]}
        review_roles = [review.get("reviewer_role") for review in terminal_reviews]
        require(
            len(set(review_roles)) == 2
            and all(isinstance(role, str) and role and role != "/root" for role in review_roles),
            "C1 terminal reviews are not two distinct non-root roles",
        )

        input_records = {
            str(C1_MANIFEST): {**manifest_stat, "sha256": C1_MANIFEST_SHA256},
            str(refs["external_receipt"]["path"]): {
                **external_stat, "sha256": refs["external_receipt"]["sha256"]},
            str(refs["worker_receipt"]["path"]): {
                **worker_stat, "sha256": refs["worker_receipt"]["sha256"]},
            str(refs["full_resource_gate"]["path"]): {
                **gate_stat, "sha256": refs["full_resource_gate"]["sha256"]},
            str(refs["runtime_loading"]["path"]): {
                **loading_stat, "sha256": refs["runtime_loading"]["sha256"]},
            str(refs["observation_summary"]["path"]): {
                **summary_stat, "sha256": refs["observation_summary"]["sha256"]},
            str(refs["archive_manifest"]["path"]): {
                **archive_stat, "sha256": refs["archive_manifest"]["sha256"]},
            str(refs["trace_events"]["path"]): trace_record,
            str(TERMINAL_BINDING): {**binding_stat, "sha256": args.terminal_binding_sha256},
            **review_records,
        }
        return {
            "manifest": manifest,
            "generation_launch": external,
            "generation_worker": worker,
            "generation_output": C1_OUTPUT,
            "generation_execution": C1_EXECUTION,
            "input_records": input_records,
        }

    namespace["source_identities_at_start"] = source_identities_at_start
    namespace["validate_generation_inputs"] = validate_generation_inputs
    namespace["DERIVATION_PROOF"] = proof
    return namespace


def _write_preflight_failure(error):
    record = {
        "schema": "s45-c1-readback-preflight-failure-v1",
        "status": "NON_AUTHORITATIVE_PREFLIGHT_FAILURE_FORMAL_ATTEMPT_NOT_CONSUMED",
        "created_utc": utc(),
        "error_type": type(error).__name__,
        "error": str(error),
        "traceback": traceback.format_exc(),
        "formal_supervision_path_created": False,
        "formal_readback_output_created": False,
        "automatic_retry": False,
    }
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    path = HERE / ("preflight_failure_" + stamp + "_" + uuid.uuid4().hex + ".json")
    with path.open("x") as handle:
        json.dump(record, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    descriptor = os.open(HERE, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--supervisor-sha256", required=True)
    parser.add_argument("--preparation-receipt-sha256", required=True)
    parser.add_argument("--worker-review-primary-sha256", required=True)
    parser.add_argument("--worker-review-adversarial-sha256", required=True)
    parser.add_argument("--supervisor-review-sha256", required=True)
    parser.add_argument("--terminal-binding-sha256", required=True)
    parser.add_argument("--execution-directory", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    global _ACTIVE_ARGS
    _ACTIVE_ARGS = args
    try:
        for name in (
            "supervisor_sha256", "preparation_receipt_sha256",
            "worker_review_primary_sha256", "worker_review_adversarial_sha256",
            "supervisor_review_sha256", "terminal_binding_sha256",
        ):
            require(HEX.fullmatch(getattr(args, name) or ""),
                    name + " must be lowercase hexadecimal")
        namespace = derive_supervisor()
        execution = safe_fresh_child_directory(
            args.execution_directory, "supervisor execution directory",
            SUPERVISION_DIRECTORY_NAME,
        )
        out = safe_fresh_child_directory(
            args.out, "readback output directory", READBACK_DIRECTORY_NAME,
        )
        require(execution != out, "Formal supervisor and readback paths overlap")

        namespace["source_identities_at_start"](
            args.supervisor_sha256, args.supervisor_review_sha256
        )
        binding, _ = _terminal_binding(namespace, args.terminal_binding_sha256)
        args.manifest = Path(binding["manifest"]["path"]).resolve()
        args.manifest_sha256 = binding["manifest"]["sha256"]
        args.s40_execution_receipt = Path(binding["external_receipt"]["path"]).resolve()
        args.s40_execution_receipt_sha256 = binding["external_receipt"]["sha256"]
        checked = namespace["validate_generation_inputs"](
            args.manifest,
            args.manifest_sha256,
            args.s40_execution_receipt,
            args.s40_execution_receipt_sha256,
        )
        for formal in (execution, out):
            for protected in (checked["generation_output"], checked["generation_execution"]):
                require(not namespace["paths_overlap"](formal, protected),
                        "Formal readback path overlaps C1 generation evidence")
        require(shutil.disk_usage(HERE).free >= namespace["MINIMUM_FREE_BYTES"],
                "Insufficient free disk before formal C1 readback attempt")
        require(PYTHON.is_file(), "Fixed local scientific Python is unavailable")
    except BaseException as error:
        _write_preflight_failure(error)
        return 2

    def interrupted(signum, frame):
        del frame
        if namespace["INTERRUPTED_SIGNAL"] is None:
            namespace["INTERRUPTED_SIGNAL"] = signum

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        execution.mkdir(parents=False, exist_ok=False)
    except BaseException as error:
        _write_preflight_failure(error)
        return 2
    return namespace["supervise"](args, execution)


if __name__ == "__main__":
    raise SystemExit(main())
