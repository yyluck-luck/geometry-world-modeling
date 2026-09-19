#!/usr/bin/env python3
"""Recompute the small C1 terminal evidence chain without opening payload bodies.

This is an internal root audit.  It deliberately cannot satisfy the protocol's
different-author independent-review requirement and therefore grants no
readback, scoring, visual, method, or novelty authorization.
"""

from __future__ import annotations

import collections
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "work/S44_c1_confirmation_generation"
EXECUTION = HERE / "execution_01"
RESULT = ROOT / "results/S44_C1_confirmation_generation"
MANIFEST = HERE / "review_attachment_01/manifest.json"
LAUNCH_SOURCE = HERE / "launch_generation.py"
OUTPUT = EXECUTION / "root_terminal_evidence_audit_v2.json"
EXPECTED_MANIFEST_SHA256 = "1e86e8279c608995a03d6675a8636c354d6d4d046b7c8faea9611d6e6a9fd93b"
EXPECTED_LAUNCH_SHA256 = "c94a982b0c0cb3fa895323ca9d7aa4e2b91eb7146eece35bdb0aedd1c157a74b"


def sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path):
    data = path.read_bytes()
    if data and not data.endswith(b"\n"):
        raise RuntimeError(f"JSONL is not newline terminated: {path}")
    return [json.loads(line) for line in data.decode("utf-8").splitlines() if line]


def canonical_event_sha256(row: dict) -> str:
    unsigned = dict(row)
    unsigned.pop("sha256", None)
    body = json.dumps(
        unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def require(condition: bool, message: str, blockers: list[str]):
    if not condition:
        blockers.append(message)


def validate_chain(rows: list[dict], expected_schema: str, blockers: list[str], label: str):
    previous = "0" * 64
    for index, row in enumerate(rows):
        require(row.get("seq") == index, f"{label}: noncontiguous seq at {index}", blockers)
        require(row.get("schema") == expected_schema, f"{label}: schema changed at {index}", blockers)
        require(
            row.get("evidence_kind") == "recorded_execution",
            f"{label}: non-execution evidence at {index}",
            blockers,
        )
        require(
            row.get("previous_sha256") == previous,
            f"{label}: previous hash mismatch at {index}",
            blockers,
        )
        require(
            row.get("sha256") == canonical_event_sha256(row),
            f"{label}: canonical row hash mismatch at {index}",
            blockers,
        )
        previous = row.get("sha256")
    return previous


def main() -> int:
    if os.path.lexists(OUTPUT):
        raise RuntimeError(f"Refusing to replace existing audit: {OUTPUT}")

    paths = {
        "parent_receipt": EXECUTION / "receipt.json",
        "worker_receipt": EXECUTION / "worker_receipt.json",
        "full_resource_gate": EXECUTION / "full_resource_gate.json",
        "launch_ticket": EXECUTION / "launch_ticket.json",
        "metadata_gate": EXECUTION / "metadata_gate.json",
        "monitor": EXECUTION / "monitor.jsonl",
        "worker_stdout": EXECUTION / "worker.stdout.txt",
        "worker_stderr": EXECUTION / "worker.stderr.txt",
        "runtime_loading": RESULT / "runtime_loading.json",
        "observation_summary": RESULT / "observation_summary.json",
        "trace_events": RESULT / "trace/events.jsonl",
        "archive_manifest": RESULT / "archive/manifest.json",
        "archive_events": RESULT / "archive/events.jsonl",
        "manifest": MANIFEST,
        "launch_source": LAUNCH_SOURCE,
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        raise RuntimeError("Missing terminal evidence: " + ", ".join(missing))
    evidence_sha256 = {name: sha256(path) for name, path in paths.items()}

    blockers: list[str] = []
    require(evidence_sha256["manifest"] == EXPECTED_MANIFEST_SHA256, "manifest SHA changed", blockers)
    require(evidence_sha256["launch_source"] == EXPECTED_LAUNCH_SHA256, "launcher SHA changed", blockers)

    manifest = read_json(MANIFEST)
    parent = read_json(paths["parent_receipt"])
    worker = read_json(paths["worker_receipt"])
    gate = read_json(paths["full_resource_gate"])
    ticket = read_json(paths["launch_ticket"])
    metadata_gate = read_json(paths["metadata_gate"])
    runtime = read_json(paths["runtime_loading"])
    summary = read_json(paths["observation_summary"])
    archive = read_json(paths["archive_manifest"])

    require(parent.get("schema") == "s44-c1-confirmation-launch-v1", "parent schema", blockers)
    require(
        parent.get("status") == "C1_BASELINE_EXTERNAL_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW",
        "parent terminal status",
        blockers,
    )
    require(parent.get("returncode") == 0 and parent.get("worker_spawned") is True, "parent return", blockers)
    require(parent.get("scientific_status") == "NOT_EVALUATED", "parent scientific boundary", blockers)
    require(parent.get("manifest_sha256") == EXPECTED_MANIFEST_SHA256, "parent manifest binding", blockers)
    require(parent.get("source_sha256") == EXPECTED_LAUNCH_SHA256, "parent launcher binding", blockers)
    require(parent.get("source_unchanged_at_close") is True, "parent source close binding", blockers)
    require(
        parent.get("worker_receipt_sha256") == evidence_sha256["worker_receipt"],
        "parent worker-receipt binding",
        blockers,
    )

    require(worker.get("schema") == "s44-c1-confirmation-worker-v1", "worker schema", blockers)
    require(
        worker.get("status") == "C1_BASELINE_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW",
        "worker terminal status",
        blockers,
    )
    require(worker.get("scientific_status") == "NOT_EVALUATED", "worker scientific boundary", blockers)
    require(worker.get("manifest_sha256") == EXPECTED_MANIFEST_SHA256, "worker manifest binding", blockers)
    require(worker.get("source_sha256") == EXPECTED_LAUNCH_SHA256, "worker launcher binding", blockers)
    require(worker.get("source_unchanged_at_close") is True, "worker source close binding", blockers)
    require(worker.get("full_resource_checks") == 1, "worker completed resource gates", blockers)
    require(worker.get("full_resource_checks_attempted") == 1, "worker attempted resource gates", blockers)
    require(worker.get("runtime_factory_calls") == 1, "worker runtime factory count", blockers)
    require(
        worker.get("archive_receipt", {}).get("sha256") == evidence_sha256["archive_manifest"],
        "worker archive binding",
        blockers,
    )
    require(
        worker.get("observation_summary_sha256") == evidence_sha256["observation_summary"],
        "worker summary binding",
        blockers,
    )
    require(
        worker.get("trace_events_sha256") == evidence_sha256["trace_events"],
        "worker trace binding",
        blockers,
    )

    require(gate.get("status") == "PASS_C1_DECLARED_GENERATION_RESOURCE_GATE", "full gate status", blockers)
    require(gate.get("manifest_sha256") == EXPECTED_MANIFEST_SHA256, "full gate manifest", blockers)
    require(gate.get("row") == "C1", "full gate row", blockers)
    require(gate.get("controls") == manifest.get("controls"), "gate controls differ", blockers)
    gate_component_projection = {
        name: {key: record.get(key) for key in ("path", "size", "sha256")}
        for name, record in gate.get("components", {}).items()
    }
    require(
        gate_component_projection == manifest.get("components"),
        "gate component identity projection differs",
        blockers,
    )
    require(gate.get("source_identities") == manifest.get("source_identities"), "gate sources differ", blockers)
    require(gate.get("input_image") == manifest.get("input_image"), "gate input differs", blockers)
    require(gate.get("config") == manifest.get("config"), "gate config differs", blockers)
    require(ticket.get("manifest_sha256") == EXPECTED_MANIFEST_SHA256, "launch ticket manifest", blockers)
    require(ticket.get("output_root") == manifest.get("output_root"), "launch ticket output", blockers)
    require(metadata_gate.get("status") == "PASS_METADATA_ONLY", "metadata gate status", blockers)
    require(metadata_gate.get("manifest_sha256") == EXPECTED_MANIFEST_SHA256, "metadata manifest", blockers)

    source_mismatches = []
    source_bytes = 0
    for raw_path, expected in manifest.get("source_identities", {}).items():
        path = Path(raw_path)
        if not path.is_file():
            source_mismatches.append({"path": raw_path, "problem": "missing"})
            continue
        source_bytes += path.stat().st_size
        actual = sha256(path)
        if actual != expected:
            source_mismatches.append({"path": raw_path, "expected": expected, "actual": actual})
    require(len(manifest.get("source_identities", {})) == 218, "source identity count", blockers)
    require(not source_mismatches, "one or more source identities changed", blockers)
    require(
        archive.get("source_identities") == manifest.get("source_identities"),
        "archive source domain differs",
        blockers,
    )

    require(runtime.get("status") == "PASS_S44_C1_DECLARED_VARIANT_COMPONENT_LOADING_ONLY", "runtime status", blockers)
    require(runtime.get("manifest_sha256") == EXPECTED_MANIFEST_SHA256, "runtime manifest", blockers)
    require(runtime.get("network_attempts") == 0, "runtime network attempts", blockers)
    state_load_errors = []
    for index, item in enumerate(runtime.get("state_dict_loads", [])):
        if item.get("missing_keys") or item.get("unexpected_keys"):
            state_load_errors.append(index)
    require(len(runtime.get("state_dict_loads", [])) == 3, "runtime state-dict attempt count", blockers)
    require(not state_load_errors, "runtime state-dict keys differ", blockers)
    vae_info = runtime.get("vae_loading_info", {})
    require(
        all(not vae_info.get(key) for key in ("missing_keys", "unexpected_keys", "mismatched_keys", "error_msgs")),
        "VAE loading info contains errors",
        blockers,
    )
    require(runtime.get("generation_calls") == 0, "runtime-loading substep call count", blockers)
    require(runtime.get("original_sd21_equivalence_verified") is False, "baseline identity boundary", blockers)

    monitor = read_jsonl(paths["monitor"])
    require(len(monitor) == parent.get("samples") == 5192, "monitor row count", blockers)
    elapsed = [row["elapsed_seconds"] for row in monitor]
    phases = [row["budget_phase"] for row in monitor]
    batches = [row["completed_batches"] for row in monitor]
    rss = [row["process_tree_rss_bytes"] for row in monitor]
    disk = [row["disk_free_bytes"] for row in monitor]
    require(all(b >= a for a, b in zip(elapsed, elapsed[1:])), "monitor elapsed not monotone", blockers)
    require(all(b >= a for a, b in zip(phases, phases[1:])), "monitor phase not monotone", blockers)
    require(all(b >= a for a, b in zip(batches, batches[1:])), "monitor batches not monotone", blockers)
    max_gap = max(b - a for a, b in zip(elapsed, elapsed[1:]))
    require(abs(max_gap - parent.get("maximum_poll_gap_seconds", -1)) < 1e-9, "monitor max-gap binding", blockers)
    require(max(rss) == parent.get("sampled_peak_process_tree_rss_bytes"), "monitor peak RSS binding", blockers)
    limits = parent.get("limits", {})
    require(max(rss) < limits.get("rss_bytes", 0), "RSS budget exceeded", blockers)
    require(min(disk) > limits.get("minimum_free_bytes", 10**30), "disk floor crossed", blockers)
    require(max(elapsed) < limits.get("total_seconds", 0), "total time budget exceeded", blockers)
    for phase in (1, 2):
        phase_elapsed = [row["phase_elapsed_seconds"] for row in monitor if row["budget_phase"] == phase]
        require(phase_elapsed and max(phase_elapsed) < limits.get("seconds_per_batch", 0), f"phase {phase} budget", blockers)
    require(
        monitor[-1]["completed_batches"] == 2
        and monitor[-1]["budget_phase"] == 2
        and monitor[-1]["trace_sequence_count"] == 327
        and monitor[-1]["process_tree_rss_bytes"] == 0,
        "monitor terminal row",
        blockers,
    )

    trace_rows = read_jsonl(paths["trace_events"])
    trace_last = validate_chain(trace_rows, "s20-generation-trace-v1", blockers, "trace")
    trace_counts = collections.Counter(row.get("event") for row in trace_rows)
    expected_trace_counts = {
        "session": 1,
        "observation": 209,
        "batch_begin": 2,
        "sample_call": 2,
        "sampler_enter": 2,
        "denoiser_call": 100,
        "sampler_return": 2,
        "sample_return": 2,
        "cache_commit": 2,
        "map_commit": 2,
        "batch_complete": 2,
        "session_end": 1,
    }
    require(dict(trace_counts) == expected_trace_counts, "trace event counts", blockers)
    require(trace_rows[0].get("payload", {}).get("manifest_sha256") == EXPECTED_MANIFEST_SHA256, "trace manifest", blockers)
    require(trace_rows[0].get("payload", {}).get("source_identities") == manifest.get("source_identities"), "trace sources", blockers)
    batch_begins = [row for row in trace_rows if row.get("event") == "batch_begin"]
    batch_completes = [row for row in trace_rows if row.get("event") == "batch_complete"]
    history_before_lengths = [len(row["payload"]["history_before"]) for row in batch_begins]
    selected_context_ids = [row["payload"]["selected_context_ids"] for row in batch_begins]
    retained_frame_ids = [row["payload"]["retained_frame_ids"] for row in batch_completes]
    require(history_before_lengths == [1, 5], "history 1-to-5 progression", blockers)
    require(selected_context_ids == [[0], [0, 2, 4, 1]], "selected context IDs", blockers)
    require(retained_frame_ids == [[1, 2, 3, 4], [5, 6, 7, 8]], "retained IDs", blockers)
    require(trace_rows[-1].get("event") == "session_end" and trace_rows[-1]["payload"].get("batches") == 2, "trace closure", blockers)
    boundary = parent.get("trace_budget_boundary", {})
    require(boundary.get("parsed_events") == len(trace_rows), "parent trace row binding", blockers)
    require(boundary.get("session_closed") is True and boundary.get("seen_failure") is False, "parent trace state", blockers)
    require(boundary.get("pending_bytes") == 0, "parent pending trace bytes", blockers)
    require(
        [(item["event_seq"], item["event_sha256"], item["retained_frame_ids"]) for item in boundary.get("completed", [])]
        == [(row["seq"], row["sha256"], row["payload"]["retained_frame_ids"]) for row in batch_completes],
        "parent batch-boundary binding",
        blockers,
    )

    require(summary.get("status") == "OBSERVED_ROUTE_RETURNED_NOT_QUALITY_VERIFIED", "summary status", blockers)
    require(summary.get("evidence_kind") == "recorded_execution", "summary evidence kind", blockers)
    require(summary.get("counts", {}).get("sampler_call") == 2, "summary sampler count", blockers)
    require(summary.get("counts", {}).get("euler_step") == 100, "summary Euler count", blockers)
    require(summary.get("counts", {}).get("main_model_forward") == 100, "summary model-forward count", blockers)
    require(
        [item.get("selected_context_ids") for item in summary.get("batches", [])] == selected_context_ids,
        "summary selected-context binding",
        blockers,
    )
    require(
        [item.get("retained_ids") for item in summary.get("batches", [])] == retained_frame_ids,
        "summary retained-ID binding",
        blockers,
    )

    archive_rows = read_jsonl(paths["archive_events"])
    archive_last = validate_chain(archive_rows, "s35-full-original-output-archive-v1", blockers, "archive")
    require(archive.get("status") == "ARCHIVE_COMPLETE", "archive status", blockers)
    require(archive.get("evidence_kind") == "recorded_execution", "archive evidence", blockers)
    require(archive.get("scientific_status") == "NOT_EVALUATED", "archive scientific boundary", blockers)
    require(archive.get("caller_manifest_sha256") == EXPECTED_MANIFEST_SHA256, "archive manifest binding", blockers)
    require(archive.get("event_count") == len(archive_rows) == 102, "archive event count", blockers)
    require(archive.get("last_event_sha256") == archive_last, "archive last-event binding", blockers)
    require(archive.get("failed_captures") == 0 and archive.get("missing_required_names") == {}, "archive capture failures", blockers)
    require(
        archive.get("caller_metadata", {}).get("observation_summary_sha256") == evidence_sha256["observation_summary"],
        "archive summary binding",
        blockers,
    )
    require(
        archive.get("files", {}).get("events.jsonl", {}).get("sha256") == evidence_sha256["archive_events"],
        "archive events file binding",
        blockers,
    )
    archive_stat_mismatches = []
    declared_bytes = 0
    archive_root = RESULT / "archive"
    for relative, identity in archive.get("files", {}).items():
        path = archive_root / relative
        declared_bytes += identity.get("bytes", 0)
        if not path.is_file() or path.stat().st_size != identity.get("bytes"):
            archive_stat_mismatches.append(relative)
    require(not archive_stat_mismatches, "archive inventory stat mismatch", blockers)
    require(set(archive.get("tensor_descriptors", {})).issubset(archive.get("files", {})), "tensor descriptor inventory", blockers)

    log_bytes = paths["worker_stdout"].read_bytes() + b"\n" + paths["worker_stderr"].read_bytes()
    fatal_signatures = [
        token.decode("ascii")
        for token in (b"Traceback (most recent call last)", b"MemoryError", b"CUDA out of memory", b"Segmentation fault", b"Killed: 9")
        if token.lower() in log_bytes.lower()
    ]
    require(not fatal_signatures, "fatal signature in worker logs", blockers)

    report = {
        "schema": "s44-c1-root-terminal-evidence-audit-v2",
        "status": "PASS_ROOT_TERMINAL_EVIDENCE_AUDIT_NOT_INDEPENDENT" if not blockers else "BLOCKED_ROOT_TERMINAL_EVIDENCE_AUDIT",
        "reviewed_utc": datetime.now(timezone.utc).isoformat(),
        "reviewer_role": "/root",
        "independent_author": False,
        "authorization": "NONE",
        "scope": "Small receipts, JSON/JSONL metadata, all 218 small source bodies, and archive file stats only. No archive tensor, blob, or image payload body was opened; no image was decoded or viewed.",
        "evidence_sha256": evidence_sha256,
        "checks": {
            "terminal_returncode_zero": parent.get("returncode") == 0,
            "worker_receipt_bound": parent.get("worker_receipt_sha256") == evidence_sha256["worker_receipt"],
            "source_identity_files_rehashed": len(manifest.get("source_identities", {})),
            "source_identity_total_bytes_rehashed": source_bytes,
            "source_identity_mismatches": source_mismatches,
            "monitor_rows": len(monitor),
            "maximum_poll_gap_seconds": max_gap,
            "sampled_peak_process_tree_rss_bytes": max(rss),
            "minimum_observed_disk_free_bytes": min(disk),
            "trace_rows": len(trace_rows),
            "trace_event_counts": dict(trace_counts),
            "trace_last_sha256": trace_last,
            "history_before_lengths": history_before_lengths,
            "selected_context_ids": selected_context_ids,
            "retained_frame_ids": retained_frame_ids,
            "archive_event_rows": len(archive_rows),
            "archive_files_stat_checked": len(archive.get("files", {})),
            "archive_declared_file_bytes": declared_bytes,
            "archive_tensor_descriptors": len(archive.get("tensor_descriptors", {})),
            "archive_payload_bodies_opened": 0,
            "fatal_log_signatures": fatal_signatures,
        },
        "blocking_findings": blockers,
        "claim_boundary": {
            "established_by_this_internal_audit": [
                "The unique C1 parent and worker returned with code zero under their external limits.",
                "The small terminal metadata chain closes two batches and binds history lengths 1 then 5, selected IDs [0] then [0,2,4,1], and retained IDs 1 through 8.",
                "All 218 small source identities still match and all archive inventory paths have their declared byte sizes.",
            ],
            "not_established": [
                "Protocol-required different-author independent terminal review.",
                "Archive tensor, blob, or image body correctness or saved-quantity consumption.",
                "Image quality, camera compliance, blind metric, severe failure, causal effect, method gain, novelty, PhD-level contribution, or CCF-A readiness.",
            ],
        },
        "operations": {
            "model_or_pipeline_runs": 0,
            "readback_runs": 0,
            "scoring_runs": 0,
            "image_decodes_or_views": 0,
            "archive_payload_body_reads": 0,
            "network_requests": 0,
        },
        "next_gate": "Obtain two valid different-author terminal evidence reviews before constructing S45 terminal_binding_01 or executing readback.",
    }
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "output": str(OUTPUT), "blockers": blockers}, ensure_ascii=False))
    return 0 if not blockers else 2


if __name__ == "__main__":
    raise SystemExit(main())
