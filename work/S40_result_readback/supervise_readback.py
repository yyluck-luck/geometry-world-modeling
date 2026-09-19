#!/usr/bin/env python3
"""Fixed external supervisor for the one fresh S40 saved-output readback attempt02.

This source is preparation only until separately reviewed and explicitly launched.
It never accepts an arbitrary child command and does not import the readback worker.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time
import traceback


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
S40 = ROOT / "work/S40_declared_variant_generation"
SELF = Path(__file__).resolve()
SUPERVISOR_PROTOCOL = HERE / "SUPERVISOR_PROTOCOL.md"
SUPERVISOR_REVIEW = HERE / "supervisor_source_review_v2.json"
READBACK = HERE / "readback.py"
READBACK_PROTOCOL = HERE / "PROTOCOL_DRAFT.md"
READBACK_REVIEW = HERE / "source_review_v3_3.json"
READBACK_REVIEW_ADVERSARIAL = HERE / "source_review_v3_3_adversarial.json"
READBACK_REVISION = HERE / "revision_v3_3_receipt.json"
ATTEMPT1_SUPERVISOR_RECEIPT = HERE / "supervision_01/receipt.json"
ATTEMPT1_WORKER_RECEIPT = HERE / "executed_01/receipt.json"
ATTEMPT1_UNEXPECTED_REPORT = HERE / "executed_01/report.json"
GENERATION_LAUNCHER = S40 / "launch_generation.py"
PYTHON = ROOT / ".venv-cut3r/bin/python"

SUPERVISOR_PROTOCOL_SHA256 = "e16832daf1fbda8f98e61da368cf00a319659f8d6970c79d582b0e35685827b3"
READBACK_SHA256 = "d4c22504569ad1fb1fcc74ea1da83b4f244f4de803f5d0fadc16e8da06777933"
READBACK_PROTOCOL_SHA256 = "257e1b7583b000e907cde8baf3e4e3fcefb9f2c81037ed98887d0f6367483163"
READBACK_REVIEW_SHA256 = "70d4c48a6940778247763c901637e18e231b926f4733ac8edb64923ef0240484"
READBACK_REVIEW_ADVERSARIAL_SHA256 = "8ca313e712eec18d275122c95181aff987ae1ff5ceb04a880af61bb41b5a3ec7"
READBACK_REVISION_SHA256 = "bebc80b8fccf6e8699d4768f6ffab097bcc75f6bca4a7f101ef53e827b0e2e9d"
ATTEMPT1_SUPERVISOR_RECEIPT_SHA256 = "f269dc2486478e65176c38445ab97251f31a5a4ac6c9f50cbd344a73daefd5da"
ATTEMPT1_WORKER_RECEIPT_SHA256 = "4b762c3061d395a6767f319a553e681dbea8fe4d90bd49e5ac8a563d36bf35c6"
ATTEMPT1_READBACK_SHA256 = "4c7a4208c4a67b003bae7b5574b48ce44d6034797bf2e9c5ab021e4d04e4cbf6"
GENERATION_LAUNCHER_SHA256 = "8ade694bc750f9693fc461257437af7b919b0c46755fc0eef2e21096d31e8860"
SUPERVISION_DIRECTORY_NAME = "supervision_02"
READBACK_DIRECTORY_NAME = "executed_02"

SECONDS = 300.0
RSS_BYTES = 2 * 1024**3
MINIMUM_FREE_BYTES = 10 * 1024**3
POLL_SECONDS = 0.5
THREAD_ENVIRONMENT = (
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)
HEX = re.compile(r"^[0-9a-f]{64}$")
SUCCESS = "S40_READBACK_RETURNED_PENDING_INDEPENDENT_REVIEW"
INTERRUPTED_SIGNAL = None


class SupervisorInterrupted(RuntimeError):
    """Raised at an owned checkpoint after SIGINT or SIGTERM was observed."""


def utc():
    return datetime.now(timezone.utc).isoformat()


def require(value, message):
    if not value:
        raise RuntimeError(message)


def raise_if_interrupted():
    if INTERRUPTED_SIGNAL is not None:
        raise SupervisorInterrupted("S40 readback supervisor received signal " + str(INTERRUPTED_SIGNAL))


def sha256(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def stat_record(path):
    path = Path(path)
    stat = path.stat()
    return {
        "path": str(path.resolve()),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "ctime_ns": stat.st_ctime_ns,
        "device": stat.st_dev,
        "inode": stat.st_ino,
    }


def same_stat(left, right):
    return all(left[key] == right[key] for key in ("path", "size", "mtime_ns", "ctime_ns", "device", "inode"))


def fsync_directory(directory):
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_new(path, value):
    path = Path(path)
    with path.open("x") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    fsync_directory(path.parent)


def append_monitor(handle, value):
    handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n")
    handle.flush()
    os.fsync(handle.fileno())


def absolute_path(raw, label):
    path = Path(raw)
    require(path.is_absolute(), label + " must be an absolute path")
    return path.resolve()


def fresh_child_directory(raw, label, expected_name):
    path = absolute_path(raw, label)
    require(path.parent == HERE, label + " must be a direct child of " + str(HERE))
    require(path.name == expected_name, label + " must have the fixed basename " + expected_name)
    require(path != HERE and not path.exists(), label + " must be fresh")
    require(path.parent.is_dir(), label + " parent is unavailable")
    return path


def paths_overlap(left, right):
    left, right = Path(left).resolve(), Path(right).resolve()
    return left == right or left.is_relative_to(right) or right.is_relative_to(left)


def read_bound_json(path, expected_sha256, label):
    path = Path(path).resolve()
    require(path.is_file(), label + " is missing")
    require(isinstance(expected_sha256, str) and HEX.fullmatch(expected_sha256), label + " SHA-256 is invalid")
    before = stat_record(path)
    require(before["size"] < 256 * 1024**2, label + " exceeds the bounded JSON metadata scope")
    actual = sha256(path)
    after_hash = stat_record(path)
    require(same_stat(before, after_hash) and actual == expected_sha256, label + " changed or has the wrong SHA-256")
    value = json.loads(path.read_text())
    require(same_stat(before, stat_record(path)), label + " changed while parsing")
    return value, before


def bound_file_record(path, expected_sha256, label):
    path = Path(path).resolve()
    require(path.is_file(), label + " is missing")
    require(isinstance(expected_sha256, str) and HEX.fullmatch(expected_sha256), label + " SHA-256 is invalid")
    before = stat_record(path)
    actual = sha256(path)
    require(actual == expected_sha256 and same_stat(before, stat_record(path)),
            label + " changed or has the wrong SHA-256")
    return {**before, "sha256": actual}


def source_identities_at_start(expected_self_sha256, expected_review_sha256):
    fixed = {
        SUPERVISOR_PROTOCOL: SUPERVISOR_PROTOCOL_SHA256,
        READBACK: READBACK_SHA256,
        READBACK_PROTOCOL: READBACK_PROTOCOL_SHA256,
        READBACK_REVIEW: READBACK_REVIEW_SHA256,
        READBACK_REVIEW_ADVERSARIAL: READBACK_REVIEW_ADVERSARIAL_SHA256,
        READBACK_REVISION: READBACK_REVISION_SHA256,
        ATTEMPT1_SUPERVISOR_RECEIPT: ATTEMPT1_SUPERVISOR_RECEIPT_SHA256,
        ATTEMPT1_WORKER_RECEIPT: ATTEMPT1_WORKER_RECEIPT_SHA256,
        GENERATION_LAUNCHER: GENERATION_LAUNCHER_SHA256,
    }
    records = {}
    for path, expected in fixed.items():
        records[str(path)] = bound_file_record(path, expected, "bound source " + str(path))
    records[str(SELF)] = bound_file_record(SELF, expected_self_sha256, "reviewed supervisor source")
    supervisor_review, review_stat = read_bound_json(
        SUPERVISOR_REVIEW, expected_review_sha256, "supervisor independent source review"
    )
    records[str(SUPERVISOR_REVIEW)] = {**review_stat, "sha256": expected_review_sha256}
    require(
        supervisor_review.get("schema") == "s40-readback-supervisor-source-review-v2"
        and supervisor_review.get("status") == "PASS_S40_READBACK_SUPERVISOR_V3_3_REBIND_SOURCE_REVIEW"
        and supervisor_review.get("verdict") == "PASS_SUPERVISOR_REBIND_NOT_EXECUTED"
        and Path(supervisor_review.get("supervisor_path", "")).resolve() == SELF
        and supervisor_review.get("supervisor_sha256") == expected_self_sha256
        and Path(supervisor_review.get("protocol_path", "")).resolve() == SUPERVISOR_PROTOCOL
        and supervisor_review.get("protocol_sha256") == SUPERVISOR_PROTOCOL_SHA256
        and supervisor_review.get("bound_readback") == {
            "readback.py": READBACK_SHA256,
            "PROTOCOL_DRAFT.md": READBACK_PROTOCOL_SHA256,
            "source_review_v3_3.json": READBACK_REVIEW_SHA256,
            "source_review_v3_3_adversarial.json": READBACK_REVIEW_ADVERSARIAL_SHA256,
            "revision_v3_3_receipt.json": READBACK_REVISION_SHA256,
        }
        and supervisor_review.get("bound_attempt01_receipts") == {
            "supervision_01/receipt.json": ATTEMPT1_SUPERVISOR_RECEIPT_SHA256,
            "executed_01/receipt.json": ATTEMPT1_WORKER_RECEIPT_SHA256,
        }
        and supervisor_review.get("generation_launcher_sha256") == GENERATION_LAUNCHER_SHA256
        and supervisor_review.get("executed") is False
        and supervisor_review.get("blocking_findings") == []
        and isinstance(supervisor_review.get("author_role"), str)
        and isinstance(supervisor_review.get("reviewer_role"), str)
        and supervisor_review.get("author_role") != supervisor_review.get("reviewer_role"),
        "The exact supervisor/protocol pair lacks a different-role PASS source review",
    )
    review, _ = read_bound_json(READBACK_REVIEW, READBACK_REVIEW_SHA256, "primary readback source review")
    identities = review.get("identities_relative_to_review_directory", {})
    require(
        review.get("schema") == "s40-readback-source-review-v3-3"
        and review.get("status") == "PASS_S40_READBACK_V3_3_SOURCE_REVIEW"
        and review.get("verdict") == "PASS_SOURCE_DELTA_REVIEW_NOT_EXECUTED"
        and identities.get("readback.py") == READBACK_SHA256
        and identities.get("PROTOCOL_DRAFT.md") == READBACK_PROTOCOL_SHA256
        and identities.get("revision_v3_3_receipt.json") == READBACK_REVISION_SHA256
        and review.get("executed") is False
        and review.get("blocking_findings") == []
        and review.get("new_blocking_source_findings") == [],
        "The exact readback worker did not pass its primary v3.3 source review",
    )
    require(
        isinstance(review.get("author_role"), str)
        and isinstance(review.get("reviewer_role"), str)
        and review.get("author_role") != review.get("reviewer_role"),
        "The primary v3.3 worker review is not different-role",
    )
    adversarial, _ = read_bound_json(
        READBACK_REVIEW_ADVERSARIAL,
        READBACK_REVIEW_ADVERSARIAL_SHA256,
        "adversarial readback source review",
    )
    adversarial_identities = adversarial.get("reviewed_identities", {})
    require(
        adversarial.get("schema") == "s40-readback-source-review-v3-3"
        and adversarial.get("status") == "PASS_S40_READBACK_V3_3_SOURCE_REVIEW"
        and adversarial.get("verdict") == "PASS_SOURCE_DELTA_REVIEW_NOT_EXECUTED"
        and adversarial_identities.get("readback_source", {}).get("actual_sha256") == READBACK_SHA256
        and adversarial_identities.get("readback_source", {}).get("expected_sha256") == READBACK_SHA256
        and adversarial_identities.get("protocol", {}).get("actual_sha256") == READBACK_PROTOCOL_SHA256
        and adversarial_identities.get("protocol", {}).get("expected_sha256") == READBACK_PROTOCOL_SHA256
        and adversarial_identities.get("revision_receipt", {}).get("actual_sha256") == READBACK_REVISION_SHA256
        and adversarial_identities.get("revision_receipt", {}).get("expected_sha256") == READBACK_REVISION_SHA256
        and adversarial.get("blocking_findings") == [],
        "The exact readback worker did not pass its adversarial v3.3 source review",
    )
    adversarial_boundary = adversarial.get("execution_boundary", {})
    require(
        adversarial_boundary.get("readback_executed") is False
        and adversarial_boundary.get("readback_source_imported") is False
        and adversarial_boundary.get("supervisor_executed") is False
        and adversarial_boundary.get("scientific_arrays_mapped_or_compared") is False
        and adversarial_boundary.get("images_decoded_or_viewed") is False
        and isinstance(adversarial.get("author_role"), str)
        and isinstance(adversarial.get("reviewer_role"), str)
        and adversarial.get("author_role") != adversarial.get("reviewer_role"),
        "The adversarial v3.3 review execution or authorship boundary is invalid",
    )
    revision, _ = read_bound_json(READBACK_REVISION, READBACK_REVISION_SHA256, "v3.3 revision receipt")
    revision_boundary = revision.get("unchanged_boundaries", {})
    require(
        revision.get("schema") == "s40-readback-revision-v3-3-receipt-v1"
        and revision.get("status") == "SOURCE_AND_PROTOCOL_REVISED_AWAITING_INDEPENDENT_REREVIEW"
        and revision.get("current_identities") == {
            "readback_sha256": READBACK_SHA256,
            "protocol_sha256": READBACK_PROTOCOL_SHA256,
        }
        and revision_boundary.get("readback_runs") == 0
        and revision_boundary.get("model_ga_gate_scoring_or_generation_runs") == 0
        and revision_boundary.get("images_decoded_or_viewed") == 0
        and revision_boundary.get("scientific_arrays_mapped_or_compared") == 0,
        "The v3.3 revision receipt is incomplete or belongs to another source pair",
    )
    attempt1_supervisor, _ = read_bound_json(
        ATTEMPT1_SUPERVISOR_RECEIPT,
        ATTEMPT1_SUPERVISOR_RECEIPT_SHA256,
        "failed attempt01 supervisor receipt",
    )
    attempt1_worker, _ = read_bound_json(
        ATTEMPT1_WORKER_RECEIPT,
        ATTEMPT1_WORKER_RECEIPT_SHA256,
        "failed attempt01 worker receipt",
    )
    require(
        attempt1_supervisor.get("schema") == "s40-readback-external-supervisor-v1"
        and attempt1_supervisor.get("status") == "FAILED_OR_PARTIAL_SUPERVISED_S40_READBACK"
        and attempt1_supervisor.get("worker_spawned") is True
        and attempt1_supervisor.get("readback_invocations") == 1
        and attempt1_supervisor.get("returncode") == 2
        and attempt1_supervisor.get("error") == "Readback worker returned nonzero"
        and attempt1_supervisor.get("success_pending_independent_review") is False,
        "The preserved outer attempt01 failure receipt is not the expected technical failure",
    )
    require(
        attempt1_worker.get("schema") == "s40-real-saved-output-readback-v1"
        and attempt1_worker.get("status") == "FAILED_OR_PARTIAL_S40_READBACK"
        and attempt1_worker.get("passed") is False
        and attempt1_worker.get("readback_source_sha256") == ATTEMPT1_READBACK_SHA256
        and attempt1_worker.get("error_type") == "TypeError"
        and attempt1_worker.get("error") == "list indices must be integers or slices, not str"
        and attempt1_worker.get("new_model_or_ga_runs") == 0
        and attempt1_worker.get("weights_original_photo_gt_read") is False
        and attempt1_worker.get("quality_status") == "NOT_EVALUATED"
        and not ATTEMPT1_UNEXPECTED_REPORT.exists(),
        "The preserved worker attempt01 failure or no-report boundary is not exact",
    )
    return records


def validate_generation_inputs(manifest_path, manifest_sha, generation_receipt_path, generation_receipt_sha):
    require(manifest_path.is_file() and manifest_path.name == "manifest.json" and manifest_path.is_relative_to(S40),
            "Manifest must be a final S40 manifest inside the S40 preparation directory")
    manifest, manifest_stat = read_bound_json(manifest_path, manifest_sha, "S40 manifest")
    require(
        manifest.get("schema") == "s40-declared-variant-two-batch-v1"
        and manifest.get("status") == "FROZEN_DECLARED_VARIANT_TWO_BATCH_EXECUTION"
        and manifest.get("variant", {}).get("repo") == "stabilityai/sd-vae-ft-mse"
        and manifest.get("variant", {}).get("exact_original_baseline") is False,
        "Only the final declared-ft-mse S40 manifest is accepted",
    )
    require(
        manifest.get("source_identities", {}).get(str(GENERATION_LAUNCHER)) == GENERATION_LAUNCHER_SHA256,
        "S40 manifest does not bind the reviewed generation launcher",
    )
    generation_output = Path(manifest.get("output_root", ""))
    require(generation_output.is_absolute(), "S40 output root is not absolute")
    generation_output = generation_output.resolve()
    require(generation_output.is_dir(), "Completed S40 generation output is absent")

    require(
        generation_receipt_path.is_file()
        and generation_receipt_path.name == "receipt.json"
        and generation_receipt_path.parent.is_relative_to(S40),
        "Generation receipt must be an S40 external receipt.json",
    )
    launch, launch_stat = read_bound_json(
        generation_receipt_path, generation_receipt_sha, "S40 generation external receipt"
    )
    generation_execution = generation_receipt_path.parent.resolve()
    require(
        launch.get("schema") == "s40-declared-variant-launch-v1"
        and launch.get("status") == "DECLARED_VARIANT_EXTERNAL_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW"
        and launch.get("manifest_sha256") == manifest_sha
        and Path(launch.get("manifest_path", "")).resolve() == manifest_path
        and launch.get("source_sha256") == GENERATION_LAUNCHER_SHA256
        and launch.get("source_unchanged_at_close") is True
        and launch.get("worker_spawned") is True
        and launch.get("returncode") == 0
        and launch.get("worker_status") == "DECLARED_VARIANT_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW"
        and "limit_exceeded" not in launch
        and "unexpected_live_descendants" not in launch,
        "S40 generation external receipt is not a clean terminal success",
    )
    boundary = launch.get("trace_budget_boundary", {})
    completions = boundary.get("completed", [])
    require(
        boundary.get("session_closed") is True
        and boundary.get("seen_failure") is False
        and boundary.get("pending_bytes") == 0
        and isinstance(completions, list)
        and len(completions) == 2
        and [item.get("retained_frame_ids") for item in completions] == [[1, 2, 3, 4], [5, 6, 7, 8]],
        "Generation receipt lacks the closed two-batch 1-to-5-to-9 boundary",
    )
    worker_digest = launch.get("worker_receipt_sha256")
    worker_path = generation_execution / "worker_receipt.json"
    worker, worker_stat = read_bound_json(worker_path, worker_digest, "S40 generation worker receipt")
    require(
        worker.get("schema") == "s40-declared-variant-worker-v1"
        and worker.get("status") == "DECLARED_VARIANT_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW"
        and worker.get("manifest_sha256") == manifest_sha
        and worker.get("source_sha256") == GENERATION_LAUNCHER_SHA256
        and worker.get("source_unchanged_at_close") is True
        and worker.get("runtime_factory_calls") == 1
        and worker.get("full_resource_checks") == 1,
        "S40 generation worker receipt is incomplete or unbound",
    )
    return {
        "manifest": manifest,
        "generation_launch": launch,
        "generation_worker": worker,
        "generation_output": generation_output,
        "generation_execution": generation_execution,
        "input_records": {
            str(manifest_path): {**manifest_stat, "sha256": manifest_sha},
            str(generation_receipt_path): {**launch_stat, "sha256": generation_receipt_sha},
            str(worker_path): {**worker_stat, "sha256": worker_digest},
        },
    }


def refresh_tree(process, tracked, psutil):
    try:
        parent = psutil.Process(process.pid)
        candidates = [parent, *parent.children(recursive=True)]
    except psutil.NoSuchProcess:
        candidates = []
    except psutil.Error as error:
        raise RuntimeError("Cannot inspect readback process tree: " + type(error).__name__ + ": " + str(error))
    for candidate in candidates:
        try:
            tracked[(candidate.pid, candidate.create_time())] = candidate
        except psutil.NoSuchProcess:
            continue
        except psutil.Error as error:
            raise RuntimeError("Cannot bind process identity: " + type(error).__name__ + ": " + str(error))

    rss = 0
    live = []
    zombies = []
    for (pid, created), candidate in list(tracked.items()):
        try:
            if candidate.create_time() != created or not candidate.is_running():
                continue
            status = candidate.status()
            if status == psutil.STATUS_ZOMBIE:
                zombies.append(pid)
                continue
            rss += candidate.memory_info().rss
            live.append({"pid": pid, "created": created})
        except psutil.NoSuchProcess:
            continue
        except psutil.Error as error:
            raise RuntimeError("Cannot measure bound process: " + type(error).__name__ + ": " + str(error))
    return rss, live, zombies


def process_group_alive(pgid):
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def known_survivors(tracked, psutil):
    survivors = []
    for (pid, created), candidate in tracked.items():
        try:
            if candidate.create_time() == created and candidate.is_running() and candidate.status() != psutil.STATUS_ZOMBIE:
                survivors.append({"pid": pid, "created": created})
        except psutil.NoSuchProcess:
            continue
        except psutil.Error as error:
            survivors.append({"pid": pid, "created": created, "inspection_error": type(error).__name__ + ": " + str(error)})
    return survivors


def terminate_tree(process, tracked, psutil):
    evidence = {"started_utc": utc(), "process_group": process.pid, "actions": [], "survivors": []}
    try:
        refresh_tree(process, tracked, psutil)
    except BaseException as error:
        evidence["discovery_error"] = type(error).__name__ + ": " + str(error)

    for sig, wait_seconds in ((signal.SIGTERM, 2.0), (signal.SIGKILL, 2.0)):
        try:
            os.killpg(process.pid, sig)
            evidence["actions"].append({"target": "process_group", "pgid": process.pid, "signal": int(sig)})
        except ProcessLookupError:
            evidence["actions"].append({"target": "process_group", "pgid": process.pid, "signal": int(sig), "already_absent": True})
        except OSError as error:
            evidence["actions"].append({"target": "process_group", "pgid": process.pid, "signal": int(sig), "error": str(error)})
        for (pid, created), candidate in list(tracked.items()):
            try:
                if candidate.create_time() == created and candidate.is_running() and candidate.status() != psutil.STATUS_ZOMBIE:
                    candidate.send_signal(sig)
                    evidence["actions"].append({"target": "tracked_process", "pid": pid, "created": created, "signal": int(sig)})
            except psutil.NoSuchProcess:
                continue
            except psutil.Error as error:
                evidence["actions"].append({"target": "tracked_process", "pid": pid, "created": created,
                                             "signal": int(sig), "error": type(error).__name__ + ": " + str(error)})
        deadline = time.monotonic() + wait_seconds
        while time.monotonic() < deadline:
            if process.poll() is not None and not known_survivors(tracked, psutil) and not process_group_alive(process.pid):
                break
            time.sleep(0.05)
        if process.poll() is not None and not known_survivors(tracked, psutil) and not process_group_alive(process.pid):
            break

    if process.poll() is None:
        try:
            process.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            evidence["direct_child_wait_timeout"] = True
    evidence["returncode"] = process.poll()
    evidence["process_group_alive_at_close"] = process_group_alive(process.pid)
    evidence["survivors"] = known_survivors(tracked, psutil)
    evidence["completed_utc"] = utc()
    return evidence


def verify_readback_success(out, manifest_path, manifest_sha, generation_receipt_path, generation_receipt_sha):
    require(out.is_dir(), "Readback worker did not create its fresh output directory")
    require({path.name for path in out.iterdir()} == {"report.json", "receipt.json"},
            "Successful readback output must contain exactly report.json and receipt.json")
    worker_receipt_path = out / "receipt.json"
    worker_receipt_sha = sha256(worker_receipt_path)
    worker, worker_receipt_stat = read_bound_json(
        worker_receipt_path,
        worker_receipt_sha,
        "readback worker receipt",
    )
    require(
        worker.get("schema") == "s40-real-saved-output-readback-v1"
        and worker.get("status") == "PASS_SAVED_S40_IDENTITIES_AND_CACHE_CONSUMPTION_ONLY"
        and worker.get("passed") is True
        and worker.get("readback_source_sha256") == READBACK_SHA256
        and worker.get("new_model_or_ga_runs") == 0
        and worker.get("weights_original_photo_gt_read") is False
        and worker.get("quality_status") == "NOT_EVALUATED",
        "Readback worker did not return its narrow saved-output PASS",
    )
    identities = worker.get("identities", {})
    require(
        identities.get(str(manifest_path), {}).get("sha256") == manifest_sha
        and identities.get(str(generation_receipt_path), {}).get("sha256") == generation_receipt_sha,
        "Readback worker receipt does not bind both external inputs",
    )
    require(isinstance(identities, dict) and 0 < len(identities) <= 100000,
            "Readback worker identity set is empty or unreasonable")
    identity_records = {}
    resolved_paths = set()
    for raw_path, item in identities.items():
        require(isinstance(raw_path, str) and isinstance(item, dict),
                "Malformed readback worker identity")
        path = Path(raw_path)
        require(path.is_absolute() and path.resolve() == path,
                "Readback worker identity path is not canonical")
        require(str(path) not in resolved_paths, "Duplicate canonical readback worker identity")
        resolved_paths.add(str(path))
        signature = item.get("stat")
        require(
            isinstance(signature, list)
            and len(signature) == 5
            and all(type(value) is int for value in signature)
            and isinstance(item.get("bytes"), int)
            and item["bytes"] >= 0
            and isinstance(item.get("sha256"), str)
            and HEX.fullmatch(item["sha256"]),
            "Malformed saved-file identity in readback worker receipt",
        )
        current = stat_record(path)
        expected_stat = {
            "path": str(path),
            "size": signature[0],
            "mtime_ns": signature[1],
            "ctime_ns": signature[2],
            "device": signature[3],
            "inode": signature[4],
        }
        require(item["bytes"] == signature[0] and same_stat(current, expected_stat),
                "A readback input changed after the worker's final seal: " + str(path))
        identity_records[str(path)] = {**expected_stat, "worker_sha256": item["sha256"]}
    identity_set_sha256 = hashlib.sha256(
        json.dumps(
            identities,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    ).hexdigest()
    report_path = out / "report.json"
    report_sha = worker.get("report_sha256")
    require(identities.get(str(report_path), {}).get("sha256") == report_sha,
            "Readback worker identity set does not bind its report")
    report, _ = read_bound_json(report_path, report_sha, "readback report")
    require(
        report.get("manifest_sha256") == manifest_sha
        and report.get("scope") == "Saved complete archive identities and actual first-output/cache/second-condition/sampler latent chain; no model, rendering or video quality recomputation",
        "Readback report belongs to another manifest or claim scope",
    )
    worker_identity_count = len(identity_records)
    identity_records[str(worker_receipt_path)] = {
        **worker_receipt_stat,
        "worker_sha256": worker_receipt_sha,
    }
    result = {
        "worker_receipt_path": str(worker_receipt_path),
        "worker_receipt_sha256": worker_receipt_sha,
        "worker_status": worker["status"],
        "report_path": str(report_path),
        "report_sha256": report_sha,
        "actual_selected_context_ids": report.get("actual_selected_context_ids"),
        "verified_generated_ids_in_second_context": report.get("verified_generated_ids_in_second_context"),
        "worker_identity_count": worker_identity_count,
        "readback_close_stat_count_including_worker_receipt": len(identity_records),
        "worker_identity_set_sha256": identity_set_sha256,
    }
    return result, identity_records


def close_identity_check(records):
    closed = {}
    unchanged = True
    for raw, start in records.items():
        path = Path(raw)
        try:
            current = {**stat_record(path), "sha256": sha256(path)}
            matches = same_stat(start, current) and start["sha256"] == current["sha256"]
        except BaseException as error:
            current = {"path": raw, "error": type(error).__name__ + ": " + str(error)}
            matches = False
        closed[raw] = {"matches_start": matches, "current": current}
        unchanged = unchanged and matches
    return unchanged, closed


def close_stat_identity_check(records):
    mismatches = []
    for raw, start in records.items():
        try:
            if not same_stat(start, stat_record(Path(raw))):
                mismatches.append({"path": raw, "reason": "stat_changed"})
        except BaseException as error:
            mismatches.append({"path": raw, "reason": type(error).__name__ + ": " + str(error)})
    return not mismatches, mismatches


def supervise(args, execution):
    started = time.monotonic()
    out = None
    record = {
        "schema": "s40-readback-external-supervisor-v1",
        "status": "CHECKING_INPUTS_BEFORE_READBACK",
        "started_utc": utc(),
        "scientific_status": "NOT_EVALUATED",
        "quality_status": "NOT_EVALUATED",
        "limits": {
            "threads": 1,
            "seconds": SECONDS,
            "rss_bytes": RSS_BYTES,
            "minimum_free_bytes": MINIMUM_FREE_BYTES,
            "poll_seconds": POLL_SECONDS,
        },
        "supervisor_sha256": args.supervisor_sha256,
        "supervisor_review_sha256": args.supervisor_review_sha256,
        "supervisor_review_path": str(SUPERVISOR_REVIEW),
        "manifest_path": str(args.manifest),
        "manifest_sha256": args.manifest_sha256,
        "s40_execution_receipt_path": str(args.s40_execution_receipt),
        "s40_execution_receipt_sha256": args.s40_execution_receipt_sha256,
        "execution_directory": str(execution),
        "out": str(args.out),
        "worker_spawned": False,
        "readback_invocations": 0,
        "sampled_peak_process_tree_rss_bytes": 0,
        "monitor_samples": 0,
        "maximum_poll_gap_seconds": 0.0,
        "automatic_retries": 0,
        "supervisor_result_array_reads": 0,
        "model_gate_generation_or_renderer_calls": 0,
    }
    process = None
    psutil = None
    tracked = {}
    source_records = {}
    input_records = {}
    readback_identity_records = {}
    try:
        require(HEX.fullmatch(args.supervisor_sha256 or ""),
                "Supervisor SHA-256 must be lowercase hexadecimal")
        require(HEX.fullmatch(args.supervisor_review_sha256 or ""),
                "Supervisor review SHA-256 must be lowercase hexadecimal")
        require(HEX.fullmatch(args.manifest_sha256 or ""),
                "Manifest SHA-256 must be lowercase hexadecimal")
        require(HEX.fullmatch(args.s40_execution_receipt_sha256 or ""),
                "S40 execution receipt SHA-256 must be lowercase hexadecimal")
        args.manifest = absolute_path(args.manifest, "manifest")
        args.s40_execution_receipt = absolute_path(args.s40_execution_receipt, "S40 execution receipt")
        out = fresh_child_directory(args.out, "readback output directory", READBACK_DIRECTORY_NAME)
        require(not paths_overlap(execution, out), "Fresh supervisor and readback directories overlap")
        record["manifest_path"] = str(args.manifest)
        record["s40_execution_receipt_path"] = str(args.s40_execution_receipt)
        record["out"] = str(out)
        raise_if_interrupted()
        source_records = source_identities_at_start(
            args.supervisor_sha256,
            args.supervisor_review_sha256,
        )
        record["source_identities_at_start"] = source_records
        checked = validate_generation_inputs(
            args.manifest,
            args.manifest_sha256,
            args.s40_execution_receipt,
            args.s40_execution_receipt_sha256,
        )
        input_records = checked["input_records"]
        record["input_identities_at_start"] = input_records
        protected = [checked["generation_output"], checked["generation_execution"]]
        require(not paths_overlap(execution, out), "Supervisor evidence and readback output directories overlap")
        for fresh in (execution, out):
            for existing in protected:
                require(not paths_overlap(fresh, existing), "Fresh readback path overlaps S40 generation evidence")
        require(shutil.disk_usage(out.parent).free >= MINIMUM_FREE_BYTES, "Insufficient free disk before readback")
        require(PYTHON.is_file(), "Fixed local scientific Python is unavailable")
        require(time.monotonic() - started <= SECONDS, "Preflight exhausted the total 300-second limit")
        raise_if_interrupted()

        command = [
            str(PYTHON),
            "-B",
            str(READBACK),
            "--manifest",
            str(args.manifest),
            "--manifest-sha256",
            args.manifest_sha256,
            "--execution-directory",
            str(checked["generation_execution"]),
            "--launch-receipt-sha256",
            args.s40_execution_receipt_sha256,
            "--out",
            str(out),
            "--seconds",
            "300",
        ]
        record["command"] = command
        env = os.environ.copy()
        for name in THREAD_ENVIRONMENT:
            env[name] = "1"
        env.pop("PYTHONPATH", None)
        env.pop("PYTHONHOME", None)
        env.update(
            PYTHONDONTWRITEBYTECODE="1",
            PYTHONNOUSERSITE="1",
            HF_HUB_OFFLINE="1",
            TRANSFORMERS_OFFLINE="1",
            HF_HUB_DISABLE_IMPLICIT_TOKEN="1",
            TOKENIZERS_PARALLELISM="false",
            MPLBACKEND="Agg",
        )
        record["fixed_child_environment"] = {name: env[name] for name in THREAD_ENVIRONMENT}
        record["fixed_child_environment"].update(
            PYTHONDONTWRITEBYTECODE=env["PYTHONDONTWRITEBYTECODE"],
            PYTHONNOUSERSITE=env["PYTHONNOUSERSITE"],
            HF_HUB_OFFLINE=env["HF_HUB_OFFLINE"],
            TRANSFORMERS_OFFLINE=env["TRANSFORMERS_OFFLINE"],
            HF_HUB_DISABLE_IMPLICIT_TOKEN=env["HF_HUB_DISABLE_IMPLICIT_TOKEN"],
            TOKENIZERS_PARALLELISM=env["TOKENIZERS_PARALLELISM"],
        )
        ticket = {
            "schema": "s40-readback-launch-ticket-v1",
            "created_utc": utc(),
            "parent_pid": os.getpid(),
            "supervisor_sha256": source_records[str(SELF)]["sha256"],
            "supervisor_review_sha256": args.supervisor_review_sha256,
            "source_identities": {path: item["sha256"] for path, item in source_records.items()},
            "manifest_path": str(args.manifest),
            "manifest_sha256": args.manifest_sha256,
            "s40_execution_receipt_path": str(args.s40_execution_receipt),
            "s40_execution_receipt_sha256": args.s40_execution_receipt_sha256,
            "out": str(out),
            "command": command,
            "limits": record["limits"],
            "claim": "One saved-output readback attempt only; no quality or novelty certification",
        }
        write_new(execution / "launch_ticket.json", ticket)

        import psutil as psutil_module

        psutil = psutil_module
        record["psutil_version"] = psutil.__version__
        record["psutil_path"] = str(Path(psutil.__file__).resolve())
        with (execution / "worker.stdout.txt").open("x") as stdout, \
                (execution / "worker.stderr.txt").open("x") as stderr, \
                (execution / "monitor.jsonl").open("x") as monitor:
            previous_poll = time.monotonic()
            process = subprocess.Popen(
                command,
                cwd=str(ROOT),
                env=env,
                stdout=stdout,
                stderr=stderr,
                start_new_session=True,
            )
            record.update(
                status="READBACK_RUNNING",
                worker_spawned=True,
                readback_invocations=1,
                pid=process.pid,
                process_group=process.pid,
                worker_started_utc=utc(),
            )
            try:
                tracked[(process.pid, psutil.Process(process.pid).create_time())] = psutil.Process(process.pid)
            except psutil.NoSuchProcess:
                pass
            raise_if_interrupted()
            while True:
                reasons = []
                inspection_error = None
                try:
                    rss, live, zombies = refresh_tree(process, tracked, psutil)
                except BaseException as error:
                    rss, live, zombies = None, [], []
                    inspection_error = type(error).__name__ + ": " + str(error)
                    reasons.append("process_tree_inspection")
                try:
                    free = shutil.disk_usage(out.parent).free
                except OSError as error:
                    free = None
                    reasons.append("disk_inspection")
                    inspection_error = (inspection_error + "; " if inspection_error else "") + type(error).__name__ + ": " + str(error)
                now = time.monotonic()
                elapsed = now - started
                gap = now - previous_poll
                previous_poll = now
                record["maximum_poll_gap_seconds"] = max(record["maximum_poll_gap_seconds"], gap)
                record["monitor_samples"] += 1
                if rss is not None:
                    record["sampled_peak_process_tree_rss_bytes"] = max(
                        record["sampled_peak_process_tree_rss_bytes"], rss
                    )
                if elapsed > SECONDS:
                    reasons.append("total_wall_time")
                if rss is not None and rss > RSS_BYTES:
                    reasons.append("process_tree_rss")
                if free is not None and free < MINIMUM_FREE_BYTES:
                    reasons.append("disk_free")
                if INTERRUPTED_SIGNAL is not None:
                    reasons.append("interrupt_signal_" + str(INTERRUPTED_SIGNAL))
                append_monitor(
                    monitor,
                    {
                        "utc": utc(),
                        "elapsed_seconds": elapsed,
                        "process_tree_rss_bytes": rss,
                        "disk_free_bytes": free,
                        "live_processes": live,
                        "zombie_pids": zombies,
                        "inspection_error": inspection_error,
                        "returncode_observed": process.poll(),
                        "limit_reasons": reasons,
                    },
                )
                if reasons:
                    record["monitor_stop_reasons"] = reasons
                    resource_reasons = [reason for reason in reasons if not reason.startswith("interrupt_signal_")]
                    if resource_reasons:
                        record["limit_exceeded"] = resource_reasons
                    if INTERRUPTED_SIGNAL is not None:
                        record["interrupted_signal"] = INTERRUPTED_SIGNAL
                    if inspection_error:
                        record["monitor_inspection_error"] = inspection_error
                    record["termination"] = terminate_tree(process, tracked, psutil)
                    break
                if process.poll() is not None:
                    break
                time.sleep(POLL_SECONDS)

        if process.poll() is None:
            record["termination"] = terminate_tree(process, tracked, psutil)
        raise_if_interrupted()
        record["returncode"] = process.poll()
        record["elapsed_seconds_including_termination"] = time.monotonic() - started
        post_limits = list(record.get("limit_exceeded", []))
        if record["elapsed_seconds_including_termination"] > SECONDS and "total_wall_time" not in post_limits:
            post_limits.append("total_wall_time")
        if record["sampled_peak_process_tree_rss_bytes"] > RSS_BYTES and "process_tree_rss" not in post_limits:
            post_limits.append("process_tree_rss")
        if post_limits:
            record["limit_exceeded"] = post_limits
        require(record["elapsed_seconds_including_termination"] <= SECONDS, "Readback exceeded the 300-second external limit")
        require(record["sampled_peak_process_tree_rss_bytes"] <= RSS_BYTES, "Readback exceeded the 2-GiB process-tree RSS limit")
        require("limit_exceeded" not in record and "monitor_inspection_error" not in record,
                "Readback monitor recorded a resource or inspection failure")
        require(record["returncode"] == 0, "Readback worker returned nonzero")

        survivors = known_survivors(tracked, psutil)
        group_alive = process_group_alive(process.pid)
        if survivors or group_alive:
            record["unexpected_live_descendants"] = {
                "tracked": survivors,
                "process_group_alive": group_alive,
            }
            record["termination"] = terminate_tree(process, tracked, psutil)
        require("unexpected_live_descendants" not in record, "Readback left a live process or process group")
        worker_result, readback_identity_records = verify_readback_success(
            out,
            args.manifest,
            args.manifest_sha256,
            args.s40_execution_receipt,
            args.s40_execution_receipt_sha256,
        )
        record["worker_result"] = worker_result
        raise_if_interrupted()
        record["elapsed_seconds_including_postcheck"] = time.monotonic() - started
        require(record["elapsed_seconds_including_postcheck"] <= SECONDS,
                "Readback and outer identity validation exceeded the total 300-second limit")
        record["status"] = SUCCESS
        record["scope"] = (
            "External resource-bounded saved-output readback returned; actual result remains pending "
            "different-author review and does not establish generation quality or novelty"
        )
    except BaseException as error:
        if process is not None and psutil is not None and (
            process.poll() is None or process_group_alive(process.pid) or known_survivors(tracked, psutil)
        ):
            record["termination"] = terminate_tree(process, tracked, psutil)
        if process is not None:
            record["returncode"] = process.poll()
        record.update(
            status=("FAILED_OR_PARTIAL_SUPERVISED_S40_READBACK" if record.get("worker_spawned")
                    else "NOT_READY_BEFORE_S40_READBACK"),
            error_type=type(error).__name__,
            error=str(error),
            traceback=traceback.format_exc(),
        )
        if out is not None and out.exists():
            record["partial_readback_output"] = {
                "path": str(out),
                "files": sorted(str(path.relative_to(out)) for path in out.rglob("*") if path.is_file()),
            }
    finally:
        if process is not None and psutil is not None and process.poll() is None:
            record["termination"] = terminate_tree(process, tracked, psutil)
            record["returncode"] = process.poll()
            record["status"] = "FAILED_OR_PARTIAL_SUPERVISED_S40_READBACK"
        source_records_unchanged, source_close = close_identity_check(source_records)
        input_records_unchanged, input_close = close_identity_check(input_records)
        sources_unchanged = bool(source_records) and source_records_unchanged
        inputs_unchanged = bool(input_records) and input_records_unchanged
        readback_inputs_unchanged, readback_input_mismatches = close_stat_identity_check(
            readback_identity_records
        )
        record["source_identities_at_close"] = source_close
        record["input_identities_at_close"] = input_close
        record["sources_unchanged_at_close"] = sources_unchanged
        record["inputs_unchanged_at_close"] = inputs_unchanged
        record["readback_worker_identity_count_at_close"] = len(readback_identity_records)
        record["readback_worker_identity_stats_unchanged_at_close"] = readback_inputs_unchanged
        record["readback_worker_identity_stat_mismatches"] = readback_input_mismatches
        if source_records and not sources_unchanged:
            record["status"] = "FAILED_BOUND_SOURCE_CHANGED"
        elif input_records and not inputs_unchanged:
            record["status"] = "FAILED_BOUND_INPUT_CHANGED"
        elif record.get("status") == SUCCESS and not readback_inputs_unchanged:
            record["status"] = "FAILED_BOUND_READBACK_INPUT_CHANGED"
        evidence = {}
        for name in ("launch_ticket.json", "monitor.jsonl", "worker.stdout.txt", "worker.stderr.txt"):
            path = execution / name
            if path.is_file():
                try:
                    evidence[name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
                except BaseException as error:
                    evidence[name] = {"error": type(error).__name__ + ": " + str(error)}
                    if record.get("status") == SUCCESS:
                        record["status"] = "FAILED_SUPERVISION_EVIDENCE_SEAL"
        record["supervision_evidence"] = evidence
        if INTERRUPTED_SIGNAL is not None:
            record["interrupted_signal"] = INTERRUPTED_SIGNAL
            if record.get("status") == SUCCESS:
                record["status"] = "FAILED_OR_PARTIAL_SUPERVISED_S40_READBACK"
        record["completed_utc"] = utc()
        record["wall_seconds_before_terminal_receipt_write"] = time.monotonic() - started
        if record["wall_seconds_before_terminal_receipt_write"] > SECONDS:
            final_limits = list(record.get("limit_exceeded", []))
            if "total_wall_time" not in final_limits:
                final_limits.append("total_wall_time")
            record["limit_exceeded"] = final_limits
            if record.get("status") == SUCCESS:
                record["status"] = "FAILED_OR_PARTIAL_SUPERVISED_S40_READBACK"
        record["success_pending_independent_review"] = record.get("status") == SUCCESS
        record["limitations"] = [
            "Process-tree RSS is sampled every 0.5 seconds, so the recorded peak is not a continuous-kernel maximum.",
            "Thread environment values are fixed to one; this is not an operating-system CPU-affinity proof.",
            "The supervisor reads only metadata receipts; the child readback performs saved-array verification.",
            "The outer layer rechecks the worker's complete identity set by stat seal without rereading tensor bodies.",
            "The process claim covers the child process group and descendants observed through psutil; a process that changes session and reparents before first observation could evade the userspace sampler.",
            "Success is pending independent result review and does not certify model math, visual quality, exact-original equivalence, or novelty.",
        ]
        write_new(execution / "receipt.json", record)
    return 0 if record.get("status") == SUCCESS else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--supervisor-sha256", required=True)
    parser.add_argument("--supervisor-review-sha256", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--s40-execution-receipt", required=True)
    parser.add_argument("--s40-execution-receipt-sha256", required=True)
    parser.add_argument("--execution-directory", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    def interrupted(signum, frame):
        global INTERRUPTED_SIGNAL
        del frame
        if INTERRUPTED_SIGNAL is None:
            INTERRUPTED_SIGNAL = signum

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    execution = fresh_child_directory(
        args.execution_directory,
        "supervisor execution directory",
        SUPERVISION_DIRECTORY_NAME,
    )
    execution.mkdir(parents=False, exist_ok=False)
    return supervise(args, execution)


if __name__ == "__main__":
    raise SystemExit(main())
