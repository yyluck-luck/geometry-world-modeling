#!/usr/bin/env python3
"""Candidate external supervisor for the unique C2 saved-output readback.

This entry is inert until exact independent source reviews and a real post-run
terminal binding are supplied.  It reuses the reviewed S40 v3.3 process monitor
through a reversible AST label derivation, while replacing its source and
generation-input validators with C2-specific fail-closed checks.
"""
from __future__ import annotations

import argparse
import ast
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
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
C2 = ROOT / "work/S47B_c2_confirmation_generation_v9"
C2_EXECUTION = C2 / "execution_01"
C2_OUTPUT = ROOT / "results/S47B_C2_confirmation_generation_v9"
C2_MANIFEST = C2 / "review_attachment_01/manifest.json"
C2_MANIFEST_SHA256 = "caa6d7c04d7784e731165e05c07ff4e358322d14c8e76f08c2337b7f4dc641ac"
C2_LAUNCHER = C2 / "launch_generation.py"
C2_LAUNCHER_SHA256 = "54c17a221e16b41c62b208cabe54895b0b0d8fc9c12528eb4d997408bb150693"
C2_GATE = C2 / "generation_gate.py"
C2_GATE_SHA256 = "4cd5c2179d2eaf17b85890acb5198d8573d2525be3e787a7ce00a17e7f2473cd"
OUTER = ROOT / "work/resumption_20260909/C2_V9_EXTERNAL_LAUNCH"
OUTER_SOURCE = ROOT / "work/resumption_20260909/launch_c2_v9_observed.py"
OUTER_SOURCE_SHA256 = "5eb013808104d4baea95c25ed91c85fc18732c9523b744263679977c6d376ccf"
OUTER_START_SHA256 = "9eb4eaab88ff1dc7fb2c06b1fd482ff12bad8d8b1ae97ccc25f00ddbc52ef968"
FAILURE_PATHS = (
    C2 / ".execution_01.supervisor_failure.json",
    C2 / ".execution_01.watchdog_failure.json",
)

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
SUCCESS = "C2_READBACK_RETURNED_PENDING_INDEPENDENT_RESULT_REVIEW"
HEX = re.compile(r"^[0-9a-f]{64}$")

LABELS = {
    "s40-readback-external-supervisor-v1": "s58-c2-readback-external-supervisor-v1",
    "s40-readback-launch-ticket-v1": "s58-c2-readback-launch-ticket-v1",
    "S40_READBACK_RETURNED_PENDING_INDEPENDENT_REVIEW": SUCCESS,
    "FAILED_OR_PARTIAL_SUPERVISED_S40_READBACK":
        "FAILED_OR_PARTIAL_SUPERVISED_C2_READBACK",
    "NOT_READY_BEFORE_S40_READBACK": "NOT_READY_BEFORE_C2_READBACK",
    "s40-real-saved-output-readback-v1": "s58-c2-real-saved-output-readback-v1",
    "PASS_SAVED_S40_IDENTITIES_AND_CACHE_CONSUMPTION_ONLY":
        "PASS_SAVED_C2_IDENTITIES_AND_CACHE_CONSUMPTION_ONLY",
    "FAILED_OR_PARTIAL_S40_READBACK": "FAILED_OR_PARTIAL_C2_READBACK",
    "s40_execution_receipt_path": "c2_execution_receipt_path",
    "s40_execution_receipt_sha256": "c2_execution_receipt_sha256",
    "Saved complete archive identities and actual first-output/cache/second-condition/sampler latent chain; no model, rendering or video quality recomputation":
        "Saved C2 complete archive identities and actual first-output/cache/second-condition/sampler latent chain; no model, rendering or image-quality recomputation",
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
        "C2 terminal binding",
    )
    require(
        binding.get("schema") == "s58-c2-terminal-binding-v1"
        and binding.get("status") == "FROZEN_C2_TERMINAL_SUCCESS_AND_FULL_ARCHIVE_BINDING"
        and binding.get("row") == "C2"
        and binding.get("placeholder_hashes") == 0
        and binding.get("created_after_terminal") is True,
        "C2 terminal binding is partial, pending, or from another row",
    )
    parse_utc(binding.get("created_utc"), "C2 terminal binding created_utc")
    return binding, stat


def _v9_closed_state(commit):
    """Read-only replay of V9's existing control-file/directory identity checks.

    This never calls a generation/resource gate, authorization creator or model.
    The existing lease checks prepare/attachment/authorization terminal records.
    """
    require(sha256(C2_GATE) == C2_GATE_SHA256, "Bound V9 gate source changed")
    for path in FAILURE_PATHS:
        require(not lexists(path), "V9 root-level failure entry exists: " + str(path))
    spec = importlib.util.spec_from_file_location("_s58_v9_readonly_gate", C2_GATE)
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    lease = gate.open_launch_control_lease(C2_MANIFEST, C2_MANIFEST_SHA256)
    try:
        require(lease.validate() == commit.get("control_plane_identity"),
                "V9 prepare/attachment/authorization identity differs from terminal commit")
        for path, key in ((C2_EXECUTION, "execution_identity"), (C2_OUTPUT, "output_identity")):
            directory = gate.DirectoryBinding.open(path)
            try:
                require(directory.validate() == commit.get(key),
                        "V9 terminal directory identity changed: " + key)
            finally:
                directory.close()
    finally:
        lease.close()
    for path in FAILURE_PATHS:
        require(not lexists(path), "V9 root failure appeared during terminal check")


def _v9_terminal_envelope(namespace, refs, parent, worker):
    """Require the actual outer return in addition to V9's non-final commit."""
    docs, records = {}, {}
    canonical = {
        "external_receipt": OUTER / "receipt.json",
        "external_started": OUTER / "started.json",
        "terminal_commit": C2_EXECUTION / "supervisor_terminal_commit.json",
        "watchdog_receipt": C2_EXECUTION / "watchdog_receipt.json",
    }
    for key, path in canonical.items():
        require(refs[key]["path"] == path, "Noncanonical V9 terminal reference: " + key)
        document, identity = namespace["read_bound_json"](path, refs[key]["sha256"], key)
        docs[key] = document
        records[str(path)] = {**identity, "sha256": refs[key]["sha256"]}
    require(refs["external_started"]["sha256"] == OUTER_START_SHA256,
            "Outer start differs from the actually observed unique V9 launch")
    outer, started = docs["external_receipt"], docs["external_started"]
    commit, watchdog = docs["terminal_commit"], docs["watchdog_receipt"]
    expected_argv = [
        str(PYTHON), "-B", str(C2_LAUNCHER), "--manifest", str(C2_MANIFEST),
        "--manifest-sha256", C2_MANIFEST_SHA256,
        "--execution-directory", str(C2_EXECUTION),
    ]
    require(
        started.get("status") == "REVIEWED_LAUNCHER_STARTED_NOT_YET_MODEL_VERIFIED"
        and started.get("argv") == outer.get("argv") == expected_argv
        and started.get("started_utc") == outer.get("started_utc")
        and type(started.get("supervisor_pid")) is int
        and started["supervisor_pid"] > 0
        and outer.get("supervisor_pid") == started["supervisor_pid"]
        and outer.get("status") == "EXTERNALLY_OBSERVED_RETURN_PENDING_INDEPENDENT_TERMINAL_REVIEW"
        and type(outer.get("returncode")) is int and outer["returncode"] == 0
        and outer.get("external_timeout") is False,
        "Actual V9 outer process did not return cleanly or does not match its start",
    )
    for name in ("stdout", "stderr"):
        path = OUTER / (name + ".txt")
        records[str(path)] = namespace["bound_file_record"](
            path, outer.get(name + "_sha256"), "V9 outer " + name)
    consumption = worker.get("scientific_consumption_binding", {})
    require(
        commit.get("schema") == "s47-c2-external-supervisor-terminal-commit-v2"
        and commit.get("status") == "COMMIT_CANDIDATE_REQUIRES_OUTER_RETURN_AND_NO_ROOT_FAILURE"
        and commit.get("outcome_status") == "RUN_RETURNED_PENDING_INDEPENDENT_REVIEW"
        and commit.get("standalone_success") is False
        and type(commit.get("parent_returncode")) is int
        and commit["parent_returncode"] == parent.get("returncode") == 0
        and commit.get("manifest_sha256") == C2_MANIFEST_SHA256
        and commit.get("launcher_sha256") == C2_LAUNCHER_SHA256
        and commit.get("parent_receipt_sha256") == refs["parent_receipt"]["sha256"]
        and commit.get("worker_receipt_sha256") == refs["worker_receipt"]["sha256"]
        and commit.get("watchdog_receipt_sha256") == refs["watchdog_receipt"]["sha256"]
        and commit.get("supervisor_pid") == started["supervisor_pid"]
        and commit.get("execution_directory") == str(C2_EXECUTION)
        and commit.get("output_root") == str(C2_OUTPUT)
        and consumption.get("all_required_resources_consumed") is True
        and consumption.get("output_identity") == commit.get("output_identity")
        and commit.get("scientific_consumption_binding") == consumption,
        "V9 commit or worker scientific-consumption identity is incomplete",
    )
    require(
        watchdog.get("schema") == "s47-c2-worker-watchdog-v2"
        and watchdog.get("status") == "WATCHDOG_CONFIRMED_REGISTERED_DESCENDANTS_GONE"
        and all(watchdog.get(key) is True for key in (
            "cleanup_complete", "all_registered_descendants_gone",
            "supervisor_completed_protocol", "canonical_execution_identity_at_close"))
        and watchdog.get("supervisor_liveness_lost") is False
        and type(watchdog.get("worker_returncode")) is int
        and watchdog["worker_returncode"] == parent.get("returncode") == 0
        and watchdog.get("worker_pid") == parent.get("pid")
        and watchdog.get("supervisor_pid") == started["supervisor_pid"]
        and watchdog.get("manifest_sha256") == C2_MANIFEST_SHA256
        and watchdog.get("launcher_sha256") == C2_LAUNCHER_SHA256
        and watchdog.get("execution_directory") == str(C2_EXECUTION)
        and watchdog.get("output_root") == str(C2_OUTPUT)
        and watchdog.get("execution_identity") == commit.get("execution_identity")
        and watchdog.get("output_identity") == commit.get("output_identity"),
        "V9 watchdog does not attest the same clean terminal worker and directories",
    )
    outer_done = parse_utc(outer.get("completed_utc"), "actual V9 outer completed_utc")
    require(
        parse_utc(started.get("started_utc"), "V9 started_utc")
        < parse_utc(parent.get("completed_utc"), "V9 parent completed_utc")
        <= parse_utc(watchdog.get("completed_utc"), "V9 watchdog completed_utc")
        <= parse_utc(commit.get("completed_utc"), "V9 commit completed_utc")
        <= outer_done,
        "V9 parent/watchdog/commit/actual-outer completion order differs",
    )
    _v9_closed_state(commit)
    return records, outer_done, commit


def derive_supervisor(*, compile_only=False):
    """Derive the process monitor and install C2-specific validators."""
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
            raise RuntimeError("Overlapping C2 supervisor derivation edits")
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
                        "C2 supervisor derivation subtree changed")
                restored_keys.add(key)
                return copy.deepcopy(old)
            return super().generic_visit(node)

    restored = Restore().visit(copy.deepcopy(derived))
    require(
        len(restored_keys) == len(changes)
        and ast.dump(restored, include_attributes=False)
        == ast.dump(original, include_attributes=False),
        "C2 supervisor differs from reviewed S40 v3.3 beyond declared labels",
    )
    proof = {
        "parent_path": str(BASE_SUPERVISOR),
        "parent_sha256": BASE_SUPERVISOR_SHA256,
        "label_counts": counts,
        "reversible_full_AST_equal": True,
        "inherited_process_tree_monitor": True,
        "inherited_300_second_2gib_10gib_limits": True,
        "c2_specific_validators_installed": True,
        "v9_actual_outer_commit_watchdog_and_no_root_failure_required": True,
        "v9_control_plane_and_directory_identity_rechecked_at_close": True,
        "model_renderer_generation_calls": 0,
    }
    if compile_only:
        compile(derived, str(BASE_SUPERVISOR) + "[S58 C2 labels]", "exec")
        return proof

    namespace = {
        "__file__": str(SELF),
        "__name__": "_s58_c2_derived_supervisor",
    }
    exec(compile(derived, str(BASE_SUPERVISOR) + "[S58 C2 labels]", "exec"), namespace)

    namespace.update(
        HERE=HERE,
        ROOT=ROOT,
        S40=C2,
        SELF=SELF,
        SUPERVISOR_PROTOCOL=SUPERVISOR_PROTOCOL,
        SUPERVISOR_REVIEW=SUPERVISOR_REVIEW,
        READBACK=READBACK,
        READBACK_PROTOCOL=READBACK_PROTOCOL,
        GENERATION_LAUNCHER=C2_LAUNCHER,
        PYTHON=PYTHON,
        SUPERVISION_DIRECTORY_NAME=SUPERVISION_DIRECTORY_NAME,
        READBACK_DIRECTORY_NAME=READBACK_DIRECTORY_NAME,
        SUCCESS=SUCCESS,
        READBACK_SHA256=sha256(READBACK),
        GENERATION_LAUNCHER_SHA256=C2_LAUNCHER_SHA256,
        fresh_child_directory=safe_fresh_child_directory,
    )

    def source_identities_at_start(expected_self_sha256, expected_review_sha256):
        args = _ACTIVE_ARGS
        require(args is not None, "C2 supervisor arguments are unavailable")
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
            str(C2_GATE): C2_GATE_SHA256,
            str(OUTER_SOURCE): OUTER_SOURCE_SHA256,
            str(PREPARATION_RECEIPT): args.preparation_receipt_sha256,
            str(READBACK_REVIEW_PRIMARY): args.worker_review_primary_sha256,
            str(READBACK_REVIEW_ADVERSARIAL): args.worker_review_adversarial_sha256,
            str(SUPERVISOR_REVIEW): args.supervisor_review_sha256,
        }
        records = {}
        for raw, expected in current.items():
            records[raw] = namespace["bound_file_record"](
                Path(raw), expected, "bound C2 readback source " + raw
            )

        preparation, _ = namespace["read_bound_json"](
            PREPARATION_RECEIPT,
            args.preparation_receipt_sha256,
            "S58 preparation receipt",
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
            preparation.get("schema") == "s58-c2-readback-preparation-v1"
            and preparation.get("status")
            == "SOURCE_PREPARATION_ONLY_AWAITING_ACTUAL_GENERATION_TERMINAL"
            and preparation.get("author_role") == "/root/negative_result_question_triage"
            and preparation.get("source_identities") == expected_sources
            and preparation.get("c2_manifest", {}).get("sha256") == C2_MANIFEST_SHA256
            and preparation.get("terminal_binding_created") is False
            and operations.get("c2_payload_bytes_read") == 0
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
                review.get("schema") == "s58-c2-readback-source-review-v1"
                and review.get("review_kind") == kind
                and review.get("status") == "PASS_S58_C2_READBACK_SOURCE_REVIEW"
                and review.get("verdict") == "PASS_SOURCE_NOT_EXECUTED"
                and review.get("reviewed_identities") == worker_identities
                and review.get("executed") is False
                and review.get("c2_payload_bytes_read") == 0
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
            supervisor.get("schema") == "s58-c2-readback-supervisor-source-review-v1"
            and supervisor.get("status") == "PASS_S58_C2_READBACK_SUPERVISOR_SOURCE_REVIEW"
            and supervisor.get("verdict") == "PASS_SUPERVISOR_NOT_EXECUTED"
            and supervisor.get("reviewed_identities") == supervisor_identities
            and supervisor.get("executed") is False
            and supervisor.get("c2_payload_bytes_read") == 0
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
            and all(author == "/root/negative_result_question_triage" for author in worker_authors)
            and supervisor_author == "/root/negative_result_question_triage"
            and all(
                role != "/root/negative_result_question_triage"
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
        require(binding.get("failure_paths_required_absent") == [str(path) for path in FAILURE_PATHS],
                "Terminal binding does not name both canonical V9 root failure paths")

        refs = {}
        for key in (
            "manifest", "parent_receipt", "worker_receipt", "full_resource_gate",
            "runtime_loading", "observation_summary", "archive_manifest", "trace_events",
            "external_receipt", "external_started", "terminal_commit", "watchdog_receipt",
        ):
            ref = binding.get(key)
            require(
                isinstance(ref, dict)
                and isinstance(ref.get("path"), str)
                and Path(ref["path"]).is_absolute()
                and Path(ref["path"]) == Path(ref["path"]).resolve()
                and isinstance(ref.get("sha256"), str)
                and HEX.fullmatch(ref["sha256"]),
                "Malformed terminal binding block: " + key,
            )
            refs[key] = {"path": Path(ref["path"]).resolve(), "sha256": ref["sha256"]}

        require(
            refs["manifest"] == {"path": C2_MANIFEST, "sha256": C2_MANIFEST_SHA256}
            and manifest_path == C2_MANIFEST
            and manifest_sha == C2_MANIFEST_SHA256,
            "Terminal binding or invocation does not use the canonical C2 manifest",
        )
        require(
            refs["parent_receipt"]["path"] == C2_EXECUTION / "receipt.json"
            and generation_receipt_path == refs["parent_receipt"]["path"]
            and generation_receipt_sha == refs["parent_receipt"]["sha256"],
            "Terminal binding or invocation names another C2 inner parent receipt",
        )
        require(
            refs["worker_receipt"]["path"] == C2_EXECUTION / "worker_receipt.json"
            and refs["full_resource_gate"]["path"] == C2_EXECUTION / "full_resource_gate.json"
            and refs["runtime_loading"]["path"] == C2_OUTPUT / "runtime_loading.json"
            and refs["observation_summary"]["path"] == C2_OUTPUT / "observation_summary.json"
            and refs["archive_manifest"]["path"] == C2_OUTPUT / "archive/manifest.json"
            and refs["trace_events"]["path"] == C2_OUTPUT / "trace/events.jsonl",
            "Terminal binding contains a noncanonical C2 evidence path",
        )

        manifest, manifest_stat = namespace["read_bound_json"](
            C2_MANIFEST, C2_MANIFEST_SHA256, "canonical C2 manifest"
        )
        require(
            manifest.get("schema") == "s47-c2-confirmation-two-batch-v1"
            and manifest.get("status") == "FROZEN_C2_BASELINE_CONFIRMATION_TWO_BATCH_EXECUTION"
            and manifest.get("derivation_policy", {}).get("row") == "C2"
            and manifest.get("output_root") == str(C2_OUTPUT)
            and len(manifest.get("source_identities", {})) == 219
            and manifest.get("source_identities", {}).get(str(C2_LAUNCHER)) == C2_LAUNCHER_SHA256
            and manifest.get("variant", {}).get("repo") == "stabilityai/sd-vae-ft-mse"
            and manifest.get("variant", {}).get("exact_original_baseline") is False,
            "Canonical C2 manifest contract differs",
        )

        external, external_stat = namespace["read_bound_json"](
            refs["parent_receipt"]["path"], refs["parent_receipt"]["sha256"],
            "C2 terminal inner parent receipt"
        )
        boundary = external.get("trace_budget_boundary", {})
        completed = boundary.get("completed", [])
        require(
            external.get("schema") == "s47-c2-confirmation-launch-v1"
            and external.get("status")
            == "C2_BASELINE_EXTERNAL_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW"
            and external.get("manifest_sha256") == C2_MANIFEST_SHA256
            and Path(external.get("manifest_path", "")).resolve() == C2_MANIFEST
            and external.get("source_sha256") == C2_LAUNCHER_SHA256
            and external.get("source_unchanged_at_close") is True
            and external.get("worker_spawned") is True
            and external.get("returncode") == 0
            and external.get("worker_status")
            == "C2_BASELINE_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW"
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
            "C2 inner parent receipt is not a clean closed two-batch terminal result",
        )
        binding_created_utc = parse_utc(
            binding.get("created_utc"), "C2 terminal binding created_utc"
        )
        external_completed_utc = parse_utc(
            external.get("completed_utc"), "C2 inner parent receipt completed_utc"
        )
        require(
            external_completed_utc < binding_created_utc,
            "C2 terminal binding was not created after the terminal receipt",
        )

        worker, worker_stat = namespace["read_bound_json"](
            refs["worker_receipt"]["path"], refs["worker_receipt"]["sha256"],
            "C2 terminal worker receipt"
        )
        require(
            worker.get("schema") == "s47-c2-confirmation-worker-v1"
            and worker.get("status") == "C2_BASELINE_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW"
            and worker.get("manifest_sha256") == C2_MANIFEST_SHA256
            and worker.get("source_sha256") == C2_LAUNCHER_SHA256
            and worker.get("source_unchanged_at_close") is True
            and worker.get("runtime_factory_calls") == 1
            and worker.get("full_resource_checks") == 1
            and worker.get("observation_summary_sha256") == refs["observation_summary"]["sha256"]
            and worker.get("trace_events_sha256") == refs["trace_events"]["sha256"]
            and worker.get("archive_receipt", {}).get("sha256")
            == refs["archive_manifest"]["sha256"],
            "C2 worker receipt is incomplete or not bound to the terminal set",
        )
        envelope_records, external_completed_utc, terminal_commit = _v9_terminal_envelope(
            namespace, refs, external, worker)
        require(external_completed_utc < binding_created_utc,
                "C2 binding predates the actual outer process return")
        terminal_guard["commit"] = terminal_commit

        gate, gate_stat = namespace["read_bound_json"](
            refs["full_resource_gate"]["path"], refs["full_resource_gate"]["sha256"],
            "C2 full resource gate"
        )
        require(
            gate.get("schema") == "s47-c2-generation-resource-gate-v1"
            and gate.get("status") == "PASS_C2_DECLARED_GENERATION_RESOURCE_GATE"
            and gate.get("manifest_sha256") == C2_MANIFEST_SHA256,
            "C2 full resource gate is incomplete or unbound",
        )
        loading, loading_stat = namespace["read_bound_json"](
            refs["runtime_loading"]["path"], refs["runtime_loading"]["sha256"],
            "C2 runtime loading receipt"
        )
        require(
            loading.get("status") == "PASS_S47_C2_DECLARED_VARIANT_COMPONENT_LOADING_ONLY"
            and loading.get("manifest_sha256") == C2_MANIFEST_SHA256
            and loading.get("variant") == manifest.get("variant")
            and isinstance(loading.get("state_dict_loads"), list)
            and bool(loading.get("state_dict_loads"))
            and all(item.get("missing_keys") == [] and item.get("unexpected_keys") == []
                    for item in loading["state_dict_loads"]),
            "C2 runtime loading record is not the clean declared-variant load",
        )
        summary, summary_stat = namespace["read_bound_json"](
            refs["observation_summary"]["path"], refs["observation_summary"]["sha256"],
            "C2 observation summary"
        )
        require(summary.get("batches") is not None,
                "C2 observation summary does not contain batch records")

        archive, archive_stat = namespace["read_bound_json"](
            refs["archive_manifest"]["path"], refs["archive_manifest"]["sha256"],
            "C2 full archive manifest"
        )
        require(
            archive.get("status") == "ARCHIVE_COMPLETE"
            and archive.get("evidence_kind") == "recorded_execution"
            and archive.get("caller_manifest_sha256") == C2_MANIFEST_SHA256
            and archive.get("source_identities") == manifest.get("source_identities")
            and not archive.get("missing_required_names")
            and archive.get("failed_captures") == 0
            and worker.get("archive_receipt", {}).get("path")
            == str(refs["archive_manifest"]["path"]),
            "C2 full archive is not terminally complete",
        )
        trace_record = namespace["bound_file_record"](
            refs["trace_events"]["path"], refs["trace_events"]["sha256"],
            "C2 trace events chain"
        )

        review_refs = binding.get("terminal_reviews", {})
        terminal_reviews = []
        terminal_review_times = []
        review_statuses = {
            "external_execution": "PASS_S47_C2_TERMINAL_EXECUTION_EVIDENCE_REVIEW",
            "archive_trace_metadata": "PASS_S47_C2_ARCHIVE_TRACE_METADATA_REVIEW",
        }
        review_bindings = {
            "manifest_sha256": C2_MANIFEST_SHA256,
            "parent_receipt_sha256": refs["parent_receipt"]["sha256"],
            "external_receipt_sha256": refs["external_receipt"]["sha256"],
            "external_started_sha256": refs["external_started"]["sha256"],
            "terminal_commit_sha256": refs["terminal_commit"]["sha256"],
            "watchdog_receipt_sha256": refs["watchdog_receipt"]["sha256"],
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
                path, ref["sha256"], "C2 terminal review " + role
            )
            require(
                review.get("schema") == "s47-c2-terminal-evidence-review-v1"
                and review.get("status") == status
                and review.get("bindings") == review_bindings
                and review.get("executed") is False
                and review.get("blocking_findings") == []
                and review.get("quality_status") == "NOT_EVALUATED"
                and review.get("method_or_novelty_status") == "NOT_EVALUATED",
                "C2 terminal review is incomplete or overclaims: " + role,
            )
            reviewed_utc = parse_utc(
                review.get("reviewed_utc"), "C2 terminal review reviewed_utc: " + role
            )
            require(
                external_completed_utc < reviewed_utc <= binding_created_utc,
                "C2 terminal review ordering differs: " + role,
            )
            terminal_reviews.append(review)
            terminal_review_times.append(reviewed_utc.isoformat())
            review_records[str(path)] = {**review_stat, "sha256": ref["sha256"]}
        review_roles = [review.get("reviewer_role") for review in terminal_reviews]
        require(
            len(set(review_roles)) == 2
            and all(isinstance(role, str) and role and role != "/root" for role in review_roles),
            "C2 terminal reviews are not two distinct non-root roles",
        )

        input_records = {
            str(C2_MANIFEST): {**manifest_stat, "sha256": C2_MANIFEST_SHA256},
            str(refs["parent_receipt"]["path"]): {
                **external_stat, "sha256": refs["parent_receipt"]["sha256"]},
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
            **envelope_records,
        }
        return {
            "manifest": manifest,
            "generation_launch": external,
            "generation_worker": worker,
            "generation_output": C2_OUTPUT,
            "generation_execution": C2_EXECUTION,
            "input_records": input_records,
        }

    # Preserve the monitor and its byte/stat close checks, adding only V9's
    # absence/control-directory requirements when closing the terminal input set.
    terminal_guard = {}
    base_close_identity_check = namespace["close_identity_check"]

    def close_identity_check_v9(records):
        unchanged, closed = base_close_identity_check(records)
        if str(OUTER / "receipt.json") in records:
            try:
                _v9_closed_state(terminal_guard["commit"])
                closed["v9_terminal_state"] = {"matches_start": True}
            except BaseException as error:
                unchanged = False
                closed["v9_terminal_state"] = {
                    "matches_start": False,
                    "error": type(error).__name__ + ": " + str(error),
                }
        return unchanged, closed

    namespace["close_identity_check"] = close_identity_check_v9
    namespace["source_identities_at_start"] = source_identities_at_start
    namespace["validate_generation_inputs"] = validate_generation_inputs
    namespace["DERIVATION_PROOF"] = proof
    return namespace


def _write_preflight_failure(error):
    record = {
        "schema": "s58-c2-readback-preflight-failure-v1",
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
        args.s40_execution_receipt = Path(binding["parent_receipt"]["path"]).resolve()
        args.s40_execution_receipt_sha256 = binding["parent_receipt"]["sha256"]
        checked = namespace["validate_generation_inputs"](
            args.manifest,
            args.manifest_sha256,
            args.s40_execution_receipt,
            args.s40_execution_receipt_sha256,
        )
        for formal in (execution, out):
            for protected in (checked["generation_output"], checked["generation_execution"]):
                require(not namespace["paths_overlap"](formal, protected),
                        "Formal readback path overlaps C2 generation evidence")
        require(shutil.disk_usage(HERE).free >= namespace["MINIMUM_FREE_BYTES"],
                "Insufficient free disk before formal C2 readback attempt")
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
