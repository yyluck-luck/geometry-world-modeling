#!/usr/bin/env python3
"""Append a cadence-safe workflow audit for the current S40/B0 evidence chain."""

import fcntl
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from research_log import append_event

PINS = {
    "manifest": "9951a78909a7d792dd536cea067c14e369cff776115a078d2f61c66c085cdebe",
    "source_review": "e7d23041d32f748ea2cf0e27b2a08c35b92c4400e0ecbcbeb28545d70c5bb9d1",
    "runtime_review": "33681baf8cf68b8f58010ba8b24aa7dbb036494ccb28ab8e7b30facdb8e2cdff",
    "launch_ticket": "ccebc0daec5b532f3afefcfb76933cf32d1701242c9075ba695e5882e810776c",
    "full_gate": "5a23262c01c2e777721b9c320b4344e26be3f20ef991836b0e53035dfb090948",
}
PATHS = {
    "manifest": ROOT / "work/S40_declared_variant_generation/review_attachment_01/manifest.json",
    "source_review": ROOT / "work/S40_declared_variant_generation/freeze_attempt_01/source_core_review.json",
    "runtime_review": ROOT / "work/S40_declared_variant_generation/freeze_attempt_01/runtime_freeze_review.json",
    "launch_ticket": ROOT / "work/S40_declared_variant_generation/execution_01/launch_ticket.json",
    "full_gate": ROOT / "work/S40_declared_variant_generation/execution_01/full_resource_gate.json",
}


def sha256(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


actual = {name: sha256(path) for name, path in PATHS.items()}
if actual != PINS:
    raise RuntimeError("Frozen S40 identity changed")
if read_json(PATHS["source_review"]).get("status") != "PASS_S40_GENERATION_SOURCE_REVIEW":
    raise RuntimeError("S40 source-core review changed")
if read_json(PATHS["runtime_review"]).get("status") != "READY_TO_ATTEMPT_S40_DECLARED_GENERATION":
    raise RuntimeError("S40 runtime-core review changed")
if read_json(PATHS["full_gate"]).get("status") != "PASS_DECLARED_GENERATION_RESOURCE_GATE":
    raise RuntimeError("S40 full resource gate changed")

target = ROOT / "workflow_checks.jsonl"
with target.open("r", encoding="utf-8") as handle:
    prior = [json.loads(line) for line in handle if line.strip()]
if not prior:
    raise RuntimeError("No prior workflow check")
previous_raw = prior[-1]["checked_utc"]
previous = datetime.fromisoformat(previous_raw)
now = datetime.now(timezone.utc)
interval = (now - previous).total_seconds() / 60.0
if interval < 30:
    raise RuntimeError(f"Only {interval:.6f} minutes since the last check")

execution = ROOT / "work/S40_declared_variant_generation/execution_01"
monitor_lines = [line for line in (execution / "monitor.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
if not monitor_lines:
    raise RuntimeError("S40 monitor is empty")
latest = json.loads(monitor_lines[-1])
monitor_age = (now - datetime.fromisoformat(latest["utc"])).total_seconds()
terminal_path = execution / "receipt.json"
terminal = read_json(terminal_path) if terminal_path.exists() else None
state = terminal.get("status") if terminal else "RUNNING"
s40_terminal_review_path = execution / "independent_terminal_evidence_review.json"
s40_terminal_review = (
    read_json(s40_terminal_review_path) if s40_terminal_review_path.is_file() else None
)
if terminal is None and (
    monitor_age > 30
    or latest["process_tree_rss_bytes"] > 45 * 1024**3
    or latest["disk_free_bytes"] < 10 * 1024**3
):
    raise RuntimeError("Live S40 monitor is stale or outside its contract")

readback_review = ROOT / "work/S40_result_readback/supervisor_source_review_v2.json"
readback_review_observation = (
    {"path": str(readback_review), "sha256": sha256(readback_review), "status": read_json(readback_review).get("status")}
    if readback_review.is_file()
    else {"status": "PENDING_OR_NOT_YET_WRITTEN"}
)
readback_source = ROOT / "work/S40_result_readback/readback.py"
attempt1_supervisor = ROOT / "work/S40_result_readback/supervision_01/receipt.json"
attempt1_worker = ROOT / "work/S40_result_readback/executed_01/receipt.json"
attempt2_supervisor = ROOT / "work/S40_result_readback/supervision_02/receipt.json"
attempt2_result_review = ROOT / "work/S40_result_readback/supervision_02/independent_result_review.json"
attempt1 = {
    "supervisor": read_json(attempt1_supervisor) if attempt1_supervisor.is_file() else None,
    "worker": read_json(attempt1_worker) if attempt1_worker.is_file() else None,
}
attempt2 = read_json(attempt2_supervisor) if attempt2_supervisor.is_file() else None
attempt2_review = read_json(attempt2_result_review) if attempt2_result_review.is_file() else None
b0_root = ROOT / "work/S42_baseline_failure_preregistration"
b0_scorer = b0_root / "score_b0_blind.py"
b0_contract = b0_root / "B0_SCORING_CONTRACT.json"
b0_primary_review = b0_root / "B0_SCORER_SOURCE_REVIEW.json"
b0_adversarial_review = b0_root / "B0_SCORER_SOURCE_REVIEW_ADVERSARIAL.json"
b0_result_review_path = b0_root / "B0_score_attempt_01/independent_result_review.json"
b0_visual_manifest = ROOT / "results/S40_declared_variant_generation/visual_qa_all9/manifest.json"
b0_recompute_root = b0_root / "B0_independent_recompute"
b0_recompute_source_review_path = b0_recompute_root / "SOURCE_REVIEW.json"
b0_recompute_result_review_path = b0_recompute_root / "execution_01/independent_result_review.json"
b0_recompute_executions = sorted(path for path in b0_recompute_root.glob("execution_[0-9][0-9]") if path.is_dir())
c1_root = ROOT / "work/S44_c1_confirmation_generation"
c1_withdrawn_pass_path = c1_root / "FREEZE_TOOL_SOURCE_REVIEW.json"
c1_blocked_review_path = c1_root / "FREEZE_TOOL_SOURCE_REVIEW_BLOCKED.json"
c1_v2_review_path = c1_root / "FREEZE_TOOL_SOURCE_REVIEW_V2.json"
c1_v2_adversarial_review_path = c1_root / "FREEZE_TOOL_SOURCE_REVIEW_V2_ADVERSARIAL.json"
c1_manifest_core_path = c1_root / "freeze_attempt_01/manifest_core.json"
c1_final_manifest_path = c1_root / "review_attachment_01/manifest.json"
c1_final_attachment_review_path = c1_root / "FINAL_ATTACHMENT_INDEPENDENT_REVIEW.json"
c1_launch_readiness_review_path = c1_root / "LAUNCH_READINESS_INDEPENDENT_REVIEW.json"
c1_execution_path = c1_root / "execution_01"
c1_terminal_path = c1_execution_path / "receipt.json"
c1_terminal_review_path = c1_execution_path / "independent_terminal_execution_review.json"
c1_monitor_path = c1_execution_path / "monitor.jsonl"
b0_attempts = sorted(path for path in b0_root.glob("B0_score_attempt_[0-9][0-9]") if path.is_dir())
b0_terminal = read_json(b0_attempts[-1] / "receipt.json") if b0_attempts and (b0_attempts[-1] / "receipt.json").is_file() else None
b0_primary = read_json(b0_primary_review) if b0_primary_review.is_file() else None
b0_adversarial = read_json(b0_adversarial_review) if b0_adversarial_review.is_file() else None
b0_result_review = read_json(b0_result_review_path) if b0_result_review_path.is_file() else None
b0_recompute_source_review = read_json(b0_recompute_source_review_path) if b0_recompute_source_review_path.is_file() else None
b0_recompute_terminal = read_json(b0_recompute_executions[-1] / "receipt.json") if b0_recompute_executions and (b0_recompute_executions[-1] / "receipt.json").is_file() else None
b0_recompute_result_review = read_json(b0_recompute_result_review_path) if b0_recompute_result_review_path.is_file() else None
c1_withdrawn_pass = read_json(c1_withdrawn_pass_path) if c1_withdrawn_pass_path.is_file() else None
c1_blocked_review = read_json(c1_blocked_review_path) if c1_blocked_review_path.is_file() else None
c1_v2_review = read_json(c1_v2_review_path) if c1_v2_review_path.is_file() else None
c1_v2_adversarial_review = read_json(c1_v2_adversarial_review_path) if c1_v2_adversarial_review_path.is_file() else None
c1_final_attachment_review = read_json(c1_final_attachment_review_path) if c1_final_attachment_review_path.is_file() else None
c1_launch_readiness_review = read_json(c1_launch_readiness_review_path) if c1_launch_readiness_review_path.is_file() else None
c1_terminal = read_json(c1_terminal_path) if c1_terminal_path.is_file() else None
c1_terminal_review = (
    read_json(c1_terminal_review_path) if c1_terminal_review_path.is_file() else None
)
c1_monitor_lines = (
    [line for line in c1_monitor_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if c1_monitor_path.is_file()
    else []
)
c1_monitor_latest = json.loads(c1_monitor_lines[-1]) if c1_monitor_lines else None
c1_readback_preparation = ROOT / "work/S45_c1_result_readback/preparation_receipt.json"
c1_readback_root = ROOT / "work/S45_c1_result_readback"
c1_readback_binding_path = c1_readback_root / "terminal_binding_01.json"
c1_readback_supervisor_receipt_path = c1_readback_root / "supervision_01/receipt.json"
c1_readback_worker_receipt_path = c1_readback_root / "executed_01/receipt.json"
c1_readback_result_review_path = c1_readback_root / "supervision_01/independent_result_review.json"
c1_readback_binding = (
    read_json(c1_readback_binding_path) if c1_readback_binding_path.is_file() else None
)
c1_readback_supervisor_receipt = (
    read_json(c1_readback_supervisor_receipt_path)
    if c1_readback_supervisor_receipt_path.is_file()
    else None
)
c1_readback_worker_receipt = (
    read_json(c1_readback_worker_receipt_path)
    if c1_readback_worker_receipt_path.is_file()
    else None
)
c1_readback_result_review = (
    read_json(c1_readback_result_review_path)
    if c1_readback_result_review_path.is_file()
    else None
)
c1_blind_scoring_preparation = ROOT / "work/S46_c1_blind_scoring_preparation"
c1_numeric_root = ROOT / "work/S45B_c1_numeric_camera_guard_preparation"
c1_numeric_primary_blocked_path = c1_numeric_root / "SOURCE_REVIEW_PRIMARY_BLOCKED.json"
c1_numeric_primary_pass_path = c1_numeric_root / "SOURCE_REVIEW_PRIMARY.json"
c1_numeric_adversarial_pass_path = c1_numeric_root / "SOURCE_REVIEW_ADVERSARIAL.json"
c1_numeric_binding_path = c1_numeric_root / "C1_CAMERA_GUARD_BINDING.json"
c1_numeric_execution_path = c1_numeric_root / "execution_01"
c1_numeric_final_candidate_path = c1_numeric_root / "FINAL_CANDIDATE_SELFTEST_RECEIPT.json"
c1_numeric_primary_blocked = (
    read_json(c1_numeric_primary_blocked_path)
    if c1_numeric_primary_blocked_path.is_file()
    else None
)
c1_numeric_primary_pass = (
    read_json(c1_numeric_primary_pass_path)
    if c1_numeric_primary_pass_path.is_file()
    else None
)
c1_numeric_adversarial_pass = (
    read_json(c1_numeric_adversarial_pass_path)
    if c1_numeric_adversarial_pass_path.is_file()
    else None
)
c1_numeric_final_candidate = (
    read_json(c1_numeric_final_candidate_path)
    if c1_numeric_final_candidate_path.is_file()
    else None
)
c1_numeric_primary_is_pass = (c1_numeric_primary_pass or {}).get("status", "").startswith("PASS_")
c1_numeric_adversarial_is_pass = (c1_numeric_adversarial_pass or {}).get("status", "").startswith("PASS_")
c1_numeric_adversarial_is_blocked = (c1_numeric_adversarial_pass or {}).get("status", "").startswith("BLOCKED_")
c1_numeric_v5_root = ROOT / "work/S45B_c1_numeric_camera_guard_supervised_v5"
c1_numeric_v5_candidate_path = c1_numeric_v5_root / "FROZEN_SOURCE_SET.json"
c1_numeric_v5_primary_path = c1_numeric_v5_root / "SOURCE_REVIEW_PRIMARY_V5.json"
c1_numeric_v5_adversarial_path = c1_numeric_v5_root / "SOURCE_REVIEW_ADVERSARIAL_V5.json"
c1_numeric_v5_binding_path = c1_numeric_v5_root / "C1_CAMERA_GUARD_BINDING_V5.json"
c1_numeric_v5_execution_path = c1_numeric_v5_root / "execution_01"
c1_numeric_v5_candidate = (
    read_json(c1_numeric_v5_candidate_path) if c1_numeric_v5_candidate_path.is_file() else None
)
c1_numeric_v5_primary = (
    read_json(c1_numeric_v5_primary_path) if c1_numeric_v5_primary_path.is_file() else None
)
c1_numeric_v5_adversarial = (
    read_json(c1_numeric_v5_adversarial_path) if c1_numeric_v5_adversarial_path.is_file() else None
)
c1_numeric_v5_primary_is_pass = (c1_numeric_v5_primary or {}).get("status", "").startswith("PASS_")
c1_numeric_v5_adversarial_is_pass = (c1_numeric_v5_adversarial or {}).get("status", "").startswith("PASS_")
c1_numeric_v6_root = ROOT / "work/S45B_c1_numeric_camera_guard_supervised_v6"
c1_numeric_v6_required = (
    "camera_guard.py",
    "supervise_camera_guard.py",
    "synthetic_selftest.py",
    "PROTOCOL.md",
    "C1_CAMERA_GUARD_BINDING_TEMPLATE.json",
)
c1_numeric_v6_source_files_present = all(
    (c1_numeric_v6_root / name).is_file() for name in c1_numeric_v6_required
)
c1_numeric_v6_candidate_path = c1_numeric_v6_root / "FROZEN_SOURCE_SET.json"
c1_numeric_v6_receipt_path = c1_numeric_v6_root / "FINAL_SYNTHETIC_SELFTEST_RECEIPT.json"
c1_numeric_v6_primary_path = c1_numeric_v6_root / "SOURCE_REVIEW_PRIMARY_V6.json"
c1_numeric_v6_adversarial_path = c1_numeric_v6_root / "SOURCE_REVIEW_ADVERSARIAL_V6.json"
c1_numeric_v6_binding_path = c1_numeric_v6_root / "C1_CAMERA_GUARD_BINDING_V6.json"
c1_numeric_v6_execution_path = c1_numeric_v6_root / "execution_01"
c1_numeric_v6_candidate = (
    read_json(c1_numeric_v6_candidate_path) if c1_numeric_v6_candidate_path.is_file() else None
)
c1_numeric_v6_primary = (
    read_json(c1_numeric_v6_primary_path) if c1_numeric_v6_primary_path.is_file() else None
)
c1_numeric_v6_adversarial = (
    read_json(c1_numeric_v6_adversarial_path) if c1_numeric_v6_adversarial_path.is_file() else None
)
c2_root = ROOT / "work/S47_c2_confirmation_generation"
c2_static_selftest = c2_root / "CANDIDATE_STATIC_SELFTEST.json"
c2_v4_static_selftest_path = c2_root / "CANDIDATE_STATIC_SELFTEST_V4.json"
c2_v4_primary_review_path = c2_root / "SOURCE_REVIEW_PRIMARY_V4.json"
c2_v4_adversarial_review_path = c2_root / "SOURCE_REVIEW_ADVERSARIAL_V4.json"
c2_v5_static_selftest_path = c2_root / "CANDIDATE_STATIC_SELFTEST_V5.json"
c2_v5_primary_review_path = c2_root / "SOURCE_REVIEW_PRIMARY_V5.json"
c2_v5_adversarial_review_path = c2_root / "SOURCE_REVIEW_ADVERSARIAL_V5.json"
c2_v6_static_selftest_path = c2_root / "CANDIDATE_STATIC_SELFTEST_V6.json"
c2_v6_primary_review_path = c2_root / "SOURCE_REVIEW_PRIMARY_V6.json"
c2_v6_adversarial_review_path = c2_root / "SOURCE_REVIEW_ADVERSARIAL_V6.json"
c2_v4_static_selftest = (
    read_json(c2_v4_static_selftest_path)
    if c2_v4_static_selftest_path.is_file()
    else None
)
c2_v4_primary_review = (
    read_json(c2_v4_primary_review_path)
    if c2_v4_primary_review_path.is_file()
    else None
)
c2_v4_adversarial_review = (
    read_json(c2_v4_adversarial_review_path)
    if c2_v4_adversarial_review_path.is_file()
    else None
)
c2_v5_static_selftest = (
    read_json(c2_v5_static_selftest_path)
    if c2_v5_static_selftest_path.is_file()
    else None
)
c2_v5_primary_review = (
    read_json(c2_v5_primary_review_path)
    if c2_v5_primary_review_path.is_file()
    else None
)
c2_v5_adversarial_review = (
    read_json(c2_v5_adversarial_review_path)
    if c2_v5_adversarial_review_path.is_file()
    else None
)
c2_v6_static_selftest = (
    read_json(c2_v6_static_selftest_path)
    if c2_v6_static_selftest_path.is_file()
    else None
)
c2_v6_primary_review = (
    read_json(c2_v6_primary_review_path)
    if c2_v6_primary_review_path.is_file()
    else None
)
c2_v6_adversarial_review = (
    read_json(c2_v6_adversarial_review_path)
    if c2_v6_adversarial_review_path.is_file()
    else None
)
c2_v3_primary_blocked_path = c2_root / "FREEZE_TOOL_SOURCE_REVIEW_V2.json"
c2_v3_adversarial_blocked_path = c2_root / "FREEZE_TOOL_SOURCE_REVIEW_V2_ADVERSARIAL.json"
c2_v3_primary_blocked = (
    read_json(c2_v3_primary_blocked_path)
    if c2_v3_primary_blocked_path.is_file()
    else None
)
c2_v3_adversarial_blocked = (
    read_json(c2_v3_adversarial_blocked_path)
    if c2_v3_adversarial_blocked_path.is_file()
    else None
)
c2_execution_path = c2_root / "execution_01"
novelty_refresh_path = ROOT / "work/S43_paradigm_shift_audit/LIVE_NOVELTY_REFRESH_2026-09-08.md"
innovation_v2_path = ROOT / "work/S43_paradigm_shift_audit/INNOVATION_NORTH_STAR_V2.md"
innovation_v2_review_path = ROOT / "work/S43_paradigm_shift_audit/INNOVATION_NORTH_STAR_V2_ADVERSARIAL_REVIEW.md"
innovation_v3_path = ROOT / "work/S43_paradigm_shift_audit/INNOVATION_NORTH_STAR_V3.md"
innovation_v3_review_path = ROOT / "work/S43_paradigm_shift_audit/INNOVATION_NORTH_STAR_V3_ADVERSARIAL_REVIEW.md"
innovation_v3_compute_path = ROOT / "work/S43_paradigm_shift_audit/RAIMA_V3_COMPUTE_FEASIBILITY.md"
pc_dpm_collision_path = ROOT / "work/S43_paradigm_shift_audit/PC_DPM_NOVELTY_COLLISION_REVIEW_V1.md"
s48_root = ROOT / "work/S48_geocausal_kill_experiment"
s48_draft_path = s48_root / "S48_GEOCAUSAL_KILL_EXPERIMENT_PREREGISTRATION_DRAFT.md"
s48_v1_review_path = s48_root / "INDEPENDENT_STATISTICAL_REVIEW.md"
s48_v2_review_path = s48_root / "INDEPENDENT_STATISTICAL_REVIEW_V2.md"
s48_v3_review_path = s48_root / "INDEPENDENT_STATISTICAL_REVIEW_V3.md"
s48_v4_review_path = s48_root / "INDEPENDENT_STATISTICAL_REVIEW_V4.md"
s48_v5_review_path = s48_root / "INDEPENDENT_STATISTICAL_REVIEW_V5.md"
s48_v6_review_path = s48_root / "INDEPENDENT_STATISTICAL_REVIEW_V6.md"
s48_hook_audit_path = s48_root / "SOURCE_HOOK_STATIC_AUDIT_V2_README.md"
s48_normative_spec_path = s48_root / "S48_NORMATIVE_ANALYSIS_SPEC_V1.md"
s48_normative_reference_path = s48_root / "s48_analysis_reference_v1.py"
s48_normative_test_path = s48_root / "test_s48_analysis_reference_v1.py"
s48_v6_normative_spec_path = s48_root / "S48_NORMATIVE_ANALYSIS_SPEC_V2.md"
s48_v6_normative_reference_path = s48_root / "s48_analysis_reference_v2.py"
s48_v6_normative_test_path = s48_root / "test_s48_analysis_reference_v2.py"
s48_draft_text = s48_draft_path.read_text(encoding="utf-8") if s48_draft_path.is_file() else ""
s48_v3_review_text = s48_v3_review_path.read_text() if s48_v3_review_path.is_file() else "PENDING"
s48_v4_review_text = s48_v4_review_path.read_text() if s48_v4_review_path.is_file() else "PENDING"
s48_v5_review_text = s48_v5_review_path.read_text() if s48_v5_review_path.is_file() else "PENDING"
s48_v6_review_text = s48_v6_review_path.read_text() if s48_v6_review_path.is_file() else "PENDING"
c1_current_source_sha256 = {
    name: sha256(c1_root / name)
    for name in (
        "freeze_c1_manifest.py",
        "generation_gate.py",
        "runtime_adapter.py",
        "launch_generation.py",
        "PROTOCOL.md",
        "FREEZE_PROTOCOL.md",
        "inference_seed43.yaml",
    )
}


def nested_string_values(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from nested_string_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from nested_string_values(item)
    elif isinstance(value, str):
        yield value


def current_c1_review_passes(review):
    if (review or {}).get("status") != "PASS_S44_C1_FREEZE_TOOL_SOURCE_REVIEW":
        return False
    recorded = set(nested_string_values(review))
    return all(digest in recorded for digest in c1_current_source_sha256.values())


c1_numeric_v6_source_sha256 = {
    name: sha256(c1_numeric_v6_root / name)
    for name in c1_numeric_v6_required
    if (c1_numeric_v6_root / name).is_file()
}


def current_c1_numeric_v6_review_passes(review):
    if not (review or {}).get("status", "").startswith("PASS_"):
        return False
    recorded = set(nested_string_values(review))
    return (
        c1_numeric_v6_candidate_path.is_file()
        and sha256(c1_numeric_v6_candidate_path) in recorded
        and len(c1_numeric_v6_source_sha256) == len(c1_numeric_v6_required)
        and all(digest in recorded for digest in c1_numeric_v6_source_sha256.values())
    )


c1_primary_current_pass = current_c1_review_passes(c1_v2_review)
c1_adversarial_current_pass = current_c1_review_passes(c1_v2_adversarial_review)
c1_dual_source_review_ready = c1_primary_current_pass and c1_adversarial_current_pass
c1_numeric_v6_primary_is_pass = current_c1_numeric_v6_review_passes(c1_numeric_v6_primary)
c1_numeric_v6_adversarial_is_pass = current_c1_numeric_v6_review_passes(c1_numeric_v6_adversarial)
c1_numeric_v6_has_blocker = any(
    (review or {}).get("status", "").startswith("BLOCKED")
    for review in (c1_numeric_v6_primary, c1_numeric_v6_adversarial)
)
c1_source_review_state = (
    "DUAL_PASS_CURRENT_SOURCES"
    if c1_dual_source_review_ready
    else "BLOCKED_SUPERSEDES_WITHDRAWN_PASS_AWAITING_CURRENT_DUAL_REVIEW"
    if c1_blocked_review
    else "PENDING_CURRENT_DUAL_REVIEW"
)
if (
    b0_terminal
    and b0_terminal.get("technically_valid") is True
    and (b0_result_review or {}).get("status") == "PASS_B0_SEALED_RESULT_REVIEW"
    and b0_visual_manifest.is_file()
    and b0_recompute_terminal
    and (b0_recompute_result_review or {}).get("status")
    == "PASS_S42_B0_INDEPENDENT_RECOMPUTE_RESULT_REVIEW"
):
    if c1_execution_path.is_dir():
        if c1_terminal:
            if (c1_readback_result_review or {}).get("status") == "PASS_S45_C1_READBACK_RESULT_REVIEW":
                pose_guard = (c1_readback_result_review or {}).get(
                    "row_validity_assertions", {}
                ).get("requested_pose_K_guard_pass")
                if pose_guard is True:
                    next_step = "Bind the independently reviewed C1 identities, then complete the blind-score source and pre-score attestation gates before one machine score."
                elif c1_numeric_v6_candidate and c1_numeric_v6_has_blocker:
                    next_step = "Finish and freeze a new source-only S45B v7 repair for the inherited-descriptor, executed-byte, complete-schema, and pre-launch attack blockers, then restart both exact-hash reviews; v6 cannot bind, score, or expose pixels."
                elif c1_numeric_v6_candidate and c1_numeric_v6_primary_is_pass and c1_numeric_v6_adversarial_is_pass:
                    next_step = "Create and independently review the exact S45B v6 binding plus external governance attestation; dual source PASS still does not authorize execution, blind scoring, or pixel viewing."
                elif c1_numeric_v6_candidate and (c1_numeric_v6_primary_is_pass or c1_numeric_v6_adversarial_is_pass):
                    next_step = "Complete the missing fresh different-author S45B v6 source review; one PASS alone does not authorize binding, execution, blind scoring, or pixel viewing."
                elif c1_numeric_v6_candidate:
                    next_step = "Obtain fresh pairwise-distinct primary and adversarial reviews of the exact frozen S45B v6 five-file source set; author and root synthetic tests do not authorize binding, execution, blind scoring, or pixel viewing."
                elif c1_numeric_v6_source_files_present:
                    next_step = "Finish and freeze the source-only S45B v6 repair, then obtain two fresh exact-hash reviews; v5 remains adversarially BLOCKED and no formal binding, execution, blind score, or pixel view is authorized."
                elif c1_numeric_v5_candidate and c1_numeric_v5_primary_is_pass and c1_numeric_v5_adversarial_is_pass:
                    next_step = "Create and independently review the exact S45B v5 binding; dual source PASS still does not authorize execution or blind scoring."
                elif c1_numeric_v5_candidate and c1_numeric_v5_primary_is_pass:
                    next_step = "Complete the fresh different-author adversarial review of the exact S45B v5 five-file source set; primary PASS alone does not authorize binding, execution, blind score, or pixel view."
                elif c1_numeric_v5_candidate:
                    next_step = "Obtain fresh pairwise-distinct primary and adversarial reviews of the exact S45B v5 source set; author self-tests do not authorize binding, execution, blind score, or pixel view."
                elif c1_numeric_adversarial_is_blocked:
                    next_step = "Revise S45B so only an independent supervisor can publish terminal PASS after observed child exit and final lock/output/report/receipt identity checks; then freeze new hashes and restart both reviews."
                elif c1_numeric_final_candidate and c1_numeric_primary_is_pass and not c1_numeric_adversarial_is_pass:
                    next_step = "Complete the fresh different-author adversarial review of the exact revised S45B source set; the primary PASS alone does not authorize binding, execution, blind score, or pixel view."
                elif c1_numeric_final_candidate:
                    next_step = "Obtain fresh different-author primary and adversarial reviews of the exact revised S45B source set; author self-tests do not authorize binding, execution, blind score, or pixel view."
                elif c1_numeric_primary_blocked:
                    next_step = "Revise the blocked S45B C1 numeric camera guard lock/receipt design, then obtain fresh primary and adversarial source reviews before any binding, execution, blind score, or pixel view."
                else:
                    next_step = "Complete a separately reviewed saved-array C1 pose/K numeric guard before binding or running the blind score; do not infer numeric closure from propagation identity."
            elif c1_readback_supervisor_receipt:
                next_step = "Independently review the completed S45 C1 saved-output readback before any score, pixel view, or row-validity claim."
            elif c1_readback_binding:
                next_step = "Run the uniquely bound and independently source-reviewed S45 saved-output readback once; preserve any failure without retry."
            else:
                next_step = "Independently review the terminal C1 execution evidence and create a post-review terminal binding before any readback, score, or visual inspection."
        else:
            next_step = "Continue only the already-started C1 execution and its persisted monitor; do not launch a duplicate. In parallel, prepare output-blind readback, scoring, and C2 tools."
    elif c1_final_manifest_path.is_file():
        next_step = "Independently recheck the attached C1 manifest and fresh resource boundary, then start its single supervised baseline generation attempt."
    elif c1_manifest_core_path.is_file():
        next_step = "Obtain two different-author reviews of the exact C1 core, then attach them create-only without launching generation."
    elif c1_dual_source_review_ready:
        next_step = "Run the reviewed standard-library C1 core freeze, then obtain two different-author core reviews."
    else:
        next_step = "Finish two current-source reviews of the corrected C1 freeze/runtime path; the withdrawn PASS cannot authorize freeze or launch."
elif (
    b0_terminal
    and b0_terminal.get("technically_valid") is True
    and (b0_result_review or {}).get("status") == "PASS_B0_SEALED_RESULT_REVIEW"
    and b0_visual_manifest.is_file()
):
    next_step = "Complete static review and the one permitted independent B0 numeric recomputation, then freeze and review C1."
elif (b0_primary or {}).get("status") == "PASS_S42_B0_BLIND_SCORER_SOURCE_REVIEW" and (b0_adversarial or {}).get("status") == "PASS_S42_B0_BLIND_SCORER_ADVERSARIAL_SOURCE_REVIEW":
    next_step = "Create the attempt-specific blind attestation after both exact reviews, then execute the unique frozen B0 machine score once."
else:
    next_step = "Complete both independent static reviews of the exact B0 scorer and contract; revise on any blocker and do not score or view images before dual PASS."

record = {
    "schema": "research-workflow-check-v1",
    "checked_utc": now.isoformat(),
    "checked_local": now.astimezone(ZoneInfo("Asia/Shanghai")).isoformat(),
    "previous_checked_utc": previous_raw,
    "interval_minutes": interval,
    "trigger": "S40 terminal baseline, reviewed readback, and blind B0 gate",
    "checks": [
        {"item": "skills", "status": "PASS", "finding": "The active work follows Supervisor 02 Idea Generation and the local scientific workflow: strong baseline before method, first-principles hidden-assumption audit, fatal-flaw idea evaluation, adversarial primary-source retrieval, independently reviewed pilot preregistration, and figure/PDF integrity checks that do not imply scientific success.", "evidence": "RESEARCH_PRINCIPLES.md"},
        {"item": "innovation", "status": "PASS", "finding": f"No infrastructure or baseline repair is called a novel method. The independent collision audit rejects PC-DPM hard shared weights and generic stale-memory routing/refresh as standalone novelty. RAIMA V3 narrows the candidate to AOIG, harmful SEM, and RCSU under explicit identifiability, reference, scene-cluster, kill, and no-method rules. V3 present={innovation_v3_path.is_file()}, fresh V3 review present={innovation_v3_review_path.is_file()}, local compute audit present={innovation_v3_compute_path.is_file()}, and novelty authorization remains NONE.", "evidence": "work/S43_paradigm_shift_audit/INNOVATION_NORTH_STAR_V3.md"},
        {"item": "experiment", "status": "PASS", "finding": f"The unique frozen S40 process is terminal ({state}) and separate terminal review is {(s40_terminal_review or {}).get('status', 'MISSING')}; B0 sealed result review is {(b0_result_review or {}).get('status', 'MISSING')}; C1 terminal evidence and narrow cache-consumption readback passed, but S45B v6 camera-guard primary review is {(c1_numeric_v6_primary or {}).get('status', 'PENDING')} and no blind score or pixel view is authorized. C2 v3-v5 remain blocked/superseded; V6 source-only candidate is {(c2_v6_static_selftest or {}).get('status', 'PENDING')} with fresh primary/adversarial {(c2_v6_primary_review or {}).get('status', 'PENDING')} / {(c2_v6_adversarial_review or {}).get('status', 'PENDING')}; C2 execution present={c2_execution_path.is_dir()}. S48 V6 fresh review present={s48_v6_review_path.is_file()} and verdict BLOCKED={('Verdict: **BLOCKED**' in s48_v6_review_text)}. No C1 score, C2 model run, S48 arm, or new pixel view is authorized.", "evidence": "work/S48_geocausal_kill_experiment/INDEPENDENT_STATISTICAL_REVIEW_V6.md"},
        {"item": "local_tools", "status": "PASS", "finding": f"Independent reviews stopped invalid paths before formal execution. C1 V6 source review exposed inherited-descriptor and executed-byte gaps; C2 V5 attack probes exposed lifecycle faults and V6 now passes author plus root Python 3.12/3.13 source/synthetic reruns while still awaiting two fresh reviews. S48 V6 executes 44/44 tests in both environments but remains scientifically BLOCKED by typed-evidence counterexamples. Local reference code, Draw.io, and Poppler remain separated from model evidence. Current historical C1 source-review state: {c1_source_review_state}.", "evidence": "work/S47_c2_confirmation_generation/CANDIDATE_STATIC_SELFTEST_V6.json"},
        {"item": "retrieval", "status": "PASS", "finding": f"The primary-source/top-venue synthesis includes VMem, SPMEM, WorldStereo, Geometry-as-context, MomentSeeker, Hi3DEval, Ref4D-VideoBench, ClashEval, Causal LLM Routing, CF-RAG, CoRM-RAG, GaME, WorldMM, WorldCraft, and TetherMem. Source tokens, geometry gates, hierarchical/reference evaluation, harmful evidence, counterfactual evidence arbitration, query/region/age routing, and stale-memory refresh are treated as occupied. Only a real, architecture-scoped joint source-accountability phenomenon remains conditional. Refresh present={novelty_refresh_path.is_file()}, collision audit present={pc_dpm_collision_path.is_file()}, and V3 keeps method status NO_METHOD_SELECTED.", "evidence": "work/S43_paradigm_shift_audit/INNOVATION_NORTH_STAR_V3.md"},
        {"item": "agents", "status": "PASS", "finding": f"Builders and reviewers remain separated. C1 V6 primary/adversarial states are {(c1_numeric_v6_primary or {}).get('status', 'PENDING')} / {(c1_numeric_v6_adversarial or {}).get('status', 'PENDING')} and any blocker forces V7. C2 V6 source-only candidate is {(c2_v6_static_selftest or {}).get('status', 'PENDING')} with fresh review states {(c2_v6_primary_review or {}).get('status', 'PENDING')} / {(c2_v6_adversarial_review or {}).get('status', 'PENDING')}; any BLOCKED review prevents prepare. S48 V6 is independently BLOCKED and V7 source-only repair is required. No formal new C1 guard run, C2 execution, or S48 arm is authorized.", "evidence": "work/S48_geocausal_kill_experiment/INDEPENDENT_STATISTICAL_REVIEW_V6.md"},
        {"item": "records", "status": "PASS", "finding": "Generation and readback boundaries, blocker/correction evidence, current hashes, top-venue collision audits, Innovation North Star V3, its local compute feasibility audit, S48 V6 independent BLOCKED review, C1 V6 BLOCKED source review, C2 V6 source-only freeze, hook audits, and figure QA are retained; source/static/synthetic tests and diagrams remain distinct from scientific results.", "evidence": "RESEARCH_LOG.md"},
    ],
    "issues": [
        f"Actual interval is {interval:.6f} minutes and is recorded without backdating.",
        "The workflow check is late relative to the 30-minute target and records the actual interval without backdating.",
        "Readback attempt01 remains a representation-layer technical failure; attempt02 is the independently reviewed narrow cache-consumption readback and does not establish image quality.",
        "B0 is one technically valid sealed row with no severe discrepancy event; it cannot establish the preregistered three-scene cohort conclusion.",
        "The runnable VAE is the declared ft-mse component variant; exact original SD2.1 VAE identity remains unknown.",
        "No natural failure, causal effect, method gain, novelty, or acceptance claim is established.",
        "The first C1 freeze-tool PASS was explicitly withdrawn by a later BLOCKED review and remains invalid; the corrected current sources, actual core, attachment, and launch-readiness chain passed separate later reviews.",
        "The S43 expanded literature result is KEEP_CONDITIONAL_AFTER_EXPANDED_NETWORK_AUDIT with novelty authorization NONE.",
        "The S43 live refresh separates Address from Select and Consume, while the independent challenge separates Influence, Localization, and Benefit and narrows the architecture scope; these conceptual refinements are not empirical novelty results.",
        "S45B v4 and v5 preserve their superseded BLOCKED histories. V6 is also BLOCKED by its fresh primary review; the new V7 source-only repair must close inherited-result-descriptor, executed-byte, complete-schema, and pre-launch attack windows before restarting both reviews.",
        "Both independent reviews block the S47 C2 v3 launcher; its candidate self-test cannot authorize a freeze, launch, model load, generation, or pixel access.",
        "C2 v4 is dual BLOCKED and V5 is BLOCKED by parent topology, descendant containment, and terminal publication defects. V6 closes those known defects in source/synthetic tests but still requires two fresh different-author exact-hash reviews before prepare; no review carries forward.",
        "The PC-DPM hard-shared-weight method and generic stale-memory rejection/refresh are explicitly rejected as standalone novelty. Interaction-aware arbitration is only a deferred method space, not a validated method or novelty claim.",
        "S48 V6 is independently BLOCKED despite 44/44 dual-environment tests: replay identity, localization tail, held-out reference identity, replacement eligibility, comparison semantics, valid-domain roles, and typed sequential ledger require V7 source-only repair and fresh review.",
        "RAIMA V3 full Stage C is compute-blocked on the current 64 GiB local machine at an optimistic serial estimate of 36.2-56.2 uninterrupted days; this does not permit post-hoc removal of controls or confirmation units.",
    ],
    "corrections": [
        "The first-batch Python [0] list and second-batch int64 tensor are now treated as distinct frozen source representations; other tensor checks remain unchanged.",
        "The 2026-09-07T15:24:55Z workflow record used a stale template that incorrectly said attempt02 was pending; this later checker revision preserves and corrects that record rather than backdating it.",
        "The exact v3.3 readback worker, rebound supervisor, attempt02 receipts/report, and independent result review now form the accepted narrow upstream gate.",
        "The 2026-09-07T17:18:30Z workflow row incorrectly treated the withdrawn C1 PASS as active; this current checker revision preserves that row and requires two reviews bound to every current C1 source SHA.",
    ],
    "new_method_validated": False,
    "next_step": next_step,
    "runtime_observation": {
        "state": state,
        "latest_monitor_utc": latest["utc"],
        "monitor_age_seconds": monitor_age,
        "elapsed_seconds": latest["elapsed_seconds"],
        "budget_phase": latest["budget_phase"],
        "completed_batches": latest["completed_batches"],
        "process_tree_rss_bytes": latest["process_tree_rss_bytes"],
        "disk_free_bytes": latest["disk_free_bytes"],
        "trace_sequence_count": latest["trace_sequence_count"],
        "terminal_receipt_present": terminal is not None,
        "readback_supervisor_review": readback_review_observation,
        "current_readback_source_sha256": sha256(readback_source),
        "readback_attempt01": {
            "supervisor_status": attempt1["supervisor"].get("status") if attempt1["supervisor"] else None,
            "worker_status": attempt1["worker"].get("status") if attempt1["worker"] else None,
            "worker_error": attempt1["worker"].get("error") if attempt1["worker"] else None,
            "report_present": (ROOT / "work/S40_result_readback/executed_01/report.json").is_file(),
        },
        "readback_attempt02": {
            "supervisor_status": attempt2.get("status") if attempt2 else None,
            "independent_result_review_status": attempt2_review.get("status") if attempt2_review else None,
            "quality_status": attempt2.get("quality_status") if attempt2 else None,
        },
        "b0_gate": {
            "scorer_sha256": sha256(b0_scorer),
            "contract_sha256": sha256(b0_contract),
            "primary_source_review_status": b0_primary.get("status") if b0_primary else None,
            "adversarial_source_review_status": b0_adversarial.get("status") if b0_adversarial else None,
            "attempt_directories": [str(path) for path in b0_attempts],
            "latest_terminal_status": b0_terminal.get("status") if b0_terminal else None,
            "latest_technically_valid": b0_terminal.get("technically_valid") if b0_terminal else None,
            "sealed_result_review_status": b0_result_review.get("status") if b0_result_review else None,
            "all_nine_visual_manifest_present": b0_visual_manifest.is_file(),
            "independent_recompute_source_review_status": b0_recompute_source_review.get("status") if b0_recompute_source_review else None,
            "independent_recompute_terminal_status": b0_recompute_terminal.get("status") if b0_recompute_terminal else None,
            "independent_recompute_result_review_status": b0_recompute_result_review.get("status") if b0_recompute_result_review else None,
        },
        "c1_preparation": {
            "source_review_state": c1_source_review_state,
            "withdrawn_pass_status": c1_withdrawn_pass.get("status") if c1_withdrawn_pass else None,
            "withdrawn_pass_authorizes_execution": False,
            "superseding_blocked_status": c1_blocked_review.get("status") if c1_blocked_review else None,
            "v2_primary_status": c1_v2_review.get("status") if c1_v2_review else None,
            "v2_primary_binds_all_current_sources": c1_primary_current_pass,
            "v2_adversarial_status": c1_v2_adversarial_review.get("status") if c1_v2_adversarial_review else None,
            "v2_adversarial_binds_all_current_sources": c1_adversarial_current_pass,
            "current_source_sha256": c1_current_source_sha256,
            "manifest_core_present": c1_manifest_core_path.is_file(),
            "final_manifest_present": c1_final_manifest_path.is_file(),
            "final_attachment_review_status": c1_final_attachment_review.get("status") if c1_final_attachment_review else None,
            "launch_readiness_review_status": c1_launch_readiness_review.get("status") if c1_launch_readiness_review else None,
            "generation_started": c1_execution_path.is_dir(),
            "terminal_status": c1_terminal.get("status") if c1_terminal else None,
            "latest_monitor": c1_monitor_latest,
        },
        "c1_numeric_camera_guard": {
            "primary_blocked_status": c1_numeric_primary_blocked.get("status") if c1_numeric_primary_blocked else None,
            "primary_blocked_sha256": sha256(c1_numeric_primary_blocked_path) if c1_numeric_primary_blocked_path.is_file() else None,
            "primary_pass_status": c1_numeric_primary_pass.get("status") if c1_numeric_primary_pass else None,
            "adversarial_pass_status": c1_numeric_adversarial_pass.get("status") if c1_numeric_adversarial_pass else None,
            "revised_candidate_status": c1_numeric_final_candidate.get("status") if c1_numeric_final_candidate else None,
            "revised_candidate_sha256": sha256(c1_numeric_final_candidate_path) if c1_numeric_final_candidate_path.is_file() else None,
            "formal_binding_present": c1_numeric_binding_path.is_file(),
            "formal_execution_present": c1_numeric_execution_path.is_dir(),
            "v6_frozen_source_set_present": c1_numeric_v6_candidate_path.is_file(),
            "v6_frozen_source_set_sha256": sha256(c1_numeric_v6_candidate_path) if c1_numeric_v6_candidate_path.is_file() else None,
            "v6_synthetic_receipt_sha256": sha256(c1_numeric_v6_receipt_path) if c1_numeric_v6_receipt_path.is_file() else None,
            "v6_current_source_sha256": c1_numeric_v6_source_sha256,
            "v6_primary_status": c1_numeric_v6_primary.get("status") if c1_numeric_v6_primary else None,
            "v6_primary_binds_all_current_sources": c1_numeric_v6_primary_is_pass,
            "v6_adversarial_status": c1_numeric_v6_adversarial.get("status") if c1_numeric_v6_adversarial else None,
            "v6_adversarial_binds_all_current_sources": c1_numeric_v6_adversarial_is_pass,
            "v6_binding_present": c1_numeric_v6_binding_path.is_file(),
            "v6_execution_present": c1_numeric_v6_execution_path.is_dir(),
            "requested_pose_K_guard_pass": False,
        },
        "c2_preparation": {
            "v3_primary_status": c2_v3_primary_blocked.get("status") if c2_v3_primary_blocked else None,
            "v3_primary_sha256": sha256(c2_v3_primary_blocked_path) if c2_v3_primary_blocked_path.is_file() else None,
            "v3_adversarial_status": c2_v3_adversarial_blocked.get("status") if c2_v3_adversarial_blocked else None,
            "v3_adversarial_sha256": sha256(c2_v3_adversarial_blocked_path) if c2_v3_adversarial_blocked_path.is_file() else None,
            "candidate_static_selftest_present": c2_static_selftest.is_file(),
            "v4_candidate_status": c2_v4_static_selftest.get("status") if c2_v4_static_selftest else None,
            "v4_candidate_sha256": sha256(c2_v4_static_selftest_path) if c2_v4_static_selftest_path.is_file() else None,
            "v4_primary_status": c2_v4_primary_review.get("status") if c2_v4_primary_review else None,
            "v4_primary_sha256": sha256(c2_v4_primary_review_path) if c2_v4_primary_review_path.is_file() else None,
            "v4_adversarial_status": c2_v4_adversarial_review.get("status") if c2_v4_adversarial_review else None,
            "v4_adversarial_sha256": sha256(c2_v4_adversarial_review_path) if c2_v4_adversarial_review_path.is_file() else None,
            "v5_candidate_status": c2_v5_static_selftest.get("status") if c2_v5_static_selftest else None,
            "v5_candidate_sha256": sha256(c2_v5_static_selftest_path) if c2_v5_static_selftest_path.is_file() else None,
            "v5_primary_status": c2_v5_primary_review.get("status") if c2_v5_primary_review else None,
            "v5_primary_sha256": sha256(c2_v5_primary_review_path) if c2_v5_primary_review_path.is_file() else None,
            "v5_adversarial_status": c2_v5_adversarial_review.get("status") if c2_v5_adversarial_review else None,
            "v5_adversarial_sha256": sha256(c2_v5_adversarial_review_path) if c2_v5_adversarial_review_path.is_file() else None,
            "v6_candidate_status": c2_v6_static_selftest.get("status") if c2_v6_static_selftest else None,
            "v6_candidate_sha256": sha256(c2_v6_static_selftest_path) if c2_v6_static_selftest_path.is_file() else None,
            "v6_primary_status": c2_v6_primary_review.get("status") if c2_v6_primary_review else None,
            "v6_primary_sha256": sha256(c2_v6_primary_review_path) if c2_v6_primary_review_path.is_file() else None,
            "v6_adversarial_status": c2_v6_adversarial_review.get("status") if c2_v6_adversarial_review else None,
            "v6_adversarial_sha256": sha256(c2_v6_adversarial_review_path) if c2_v6_adversarial_review_path.is_file() else None,
            "formal_execution_present": c2_execution_path.is_dir(),
            "model_or_pixel_access_authorized": False,
        },
        "s48_pilot_design": {
            "v1_statistical_review_present": s48_v1_review_path.is_file(),
            "v1_statistical_review_sha256": sha256(s48_v1_review_path) if s48_v1_review_path.is_file() else None,
            "v2_statistical_review_sha256": sha256(s48_v2_review_path) if s48_v2_review_path.is_file() else None,
            "v3_statistical_review_sha256": sha256(s48_v3_review_path) if s48_v3_review_path.is_file() else None,
            "v4_statistical_review_sha256": sha256(s48_v4_review_path) if s48_v4_review_path.is_file() else None,
            "v5_statistical_review_sha256": sha256(s48_v5_review_path) if s48_v5_review_path.is_file() else None,
            "v6_statistical_review_sha256": sha256(s48_v6_review_path) if s48_v6_review_path.is_file() else None,
            "v6_statistical_review_blocked": "Verdict: **BLOCKED**" in s48_v6_review_text,
            "current_draft_sha256": sha256(s48_draft_path) if s48_draft_path.is_file() else None,
            "v5_header_present": s48_draft_text.startswith("# S48 GeoCausal 最小否证实验预注册草案 V5"),
            "v6_header_present": s48_draft_text.startswith("# S48 GeoCausal 最小否证实验预注册草案 V6"),
            "normative_spec_present": s48_normative_spec_path.is_file(),
            "normative_reference_present": s48_normative_reference_path.is_file(),
            "normative_test_present": s48_normative_test_path.is_file(),
            "v6_normative_spec_present": s48_v6_normative_spec_path.is_file(),
            "v6_normative_reference_present": s48_v6_normative_reference_path.is_file(),
            "v6_normative_test_present": s48_v6_normative_test_path.is_file(),
            "execution_authorized": False,
        },
        "innovation_v3": {
            "north_star_present": innovation_v3_path.is_file(),
            "north_star_sha256": sha256(innovation_v3_path) if innovation_v3_path.is_file() else None,
            "fresh_review_present": innovation_v3_review_path.is_file(),
            "fresh_review_sha256": sha256(innovation_v3_review_path) if innovation_v3_review_path.is_file() else None,
            "compute_feasibility_present": innovation_v3_compute_path.is_file(),
            "compute_feasibility_sha256": sha256(innovation_v3_compute_path) if innovation_v3_compute_path.is_file() else None,
            "method_selected": False,
            "novelty_authorized": False,
        },
        "bound_sha256": actual,
    },
}

# Current candidate observations are informational and never grant execution rights.
# The legacy evidence above stays intact; this snapshot supersedes stale version prose.
def source_only_observation(relative):
    p = ROOT / relative
    if not p.is_file():
        return {"path": str(p), "present": False, "status": "NOT_YET_PERSISTED"}
    data = read_json(p)
    return {"path": str(p), "present": True, "sha256": sha256(p),
            "status": data.get("status", "PRESENT_WITHOUT_STATUS")}

continuation = {
    "c1_v10": source_only_observation("work/S45B_c1_numeric_camera_guard_supervised_v10/FROZEN_SOURCE_SET.json"),
    "c1_v9_actual_failure": source_only_observation("work/S45B_c1_numeric_camera_guard_supervised_v9/ACTUAL_EXECUTION_FAILURE_DIAGNOSIS_V9.json"),
    "c2_v8_attachment": source_only_observation("work/S47B_c2_confirmation_generation_v8/review_attachment_01/receipt.json"),
    "c1_v9": source_only_observation("work/S45B_c1_numeric_camera_guard_supervised_v9/FROZEN_SOURCE_SET.json"),
    "c2_v7_actual_failed_launch": source_only_observation("work/resumption_20260908/C2_V7_EXTERNAL_LAUNCH/receipt.json"),
    "c2_v8": source_only_observation("work/S47B_c2_confirmation_generation_v8/FROZEN_SOURCE_SET_V8.json"),
    "s52_rgb_time_cameras": source_only_observation("work/S52_next_discriminating_prediction/RGB_TIME_CAMERA_RECEIPT.json"),
    "c1_v8": source_only_observation("work/S45B_c1_numeric_camera_guard_supervised_v8/FROZEN_SOURCE_SET.json"),
    "c1_v8_formal_call": source_only_observation("work/resumption_20260908/C1_V8_FORMAL_ORCHESTRATION.json"),
    "c2_prepared": source_only_observation("work/S47_c2_confirmation_generation/freeze_attempt_01/receipt.json"),
    "s50_reference_metadata": source_only_observation("work/S50_heldout_reference_metadata/evidence.json"),
    "s51_exact_math": source_only_observation("work/S51_innovation_math_guidance/MATH_RECEIPT.json"),
    "innovation_guidance_sha256": sha256(ROOT / "docs/INNOVATION_GUIDANCE_CURRENT.md"),
    "c1_v7": source_only_observation("work/S45B_c1_numeric_camera_guard_supervised_v7/FROZEN_SOURCE_SET.json"),
    "c1_v7_primary": source_only_observation("work/S45B_c1_numeric_camera_guard_supervised_v7/SOURCE_REVIEW_PRIMARY_V7.json"),
    "c2_v7": source_only_observation("work/S47_c2_confirmation_generation/CANDIDATE_STATIC_SELFTEST_V7.json"),
    "raima_v4": source_only_observation("work/S43_paradigm_shift_audit/raima_v4/FROZEN_SOURCE_SET.json"),
    "s48_v7": source_only_observation("work/S48_geocausal_kill_experiment/SOURCE_ONLY_V7_FREEZE_RECEIPT.json"),
    "s49_reference_time": source_only_observation("work/S49_reference_data_feasibility/reference_time_feasibility.json"),
    "execution_authorization": "NONE_FROM_THIS_CHECK",
}
record["continuation_source_only_snapshot"] = continuation
record["corrections"].append(
    "2026-09-08 continuation supersedes legacy V6/V7 repair prose: C1 V8 was dual-reviewed and bound, but the observed formal invocation returned 2 without a PASS; preserve failure and diagnose before continuation. C2 V7 source reviews and unique prepare completed, pending the existing later gates. S50 found a previously exposed RGB reference candidate and timestamp mismatch, not a clean confirmatory input. Guidance v2.2 explicitly permits parallel top-venue and mathematical inspiration. Presence and self-test PASS do not authorize execution."
)
if continuation["c1_v10"]["present"]:
    next_step = "C1 V9 really read 11 camera tensors/1584 bytes, worker exited zero but supervisor rejected a legal single K[3,3]; preserve its consumed failed attempt. V10 changes only that shape predicate, then requires existing fresh reviews and one numeric execution. C2 V8 actual prepare and attachment passed; complete existing final reviews and authorization. No new method validated."
    record["next_step"] = next_step
for check in record["checks"]:
    if check["item"] in ("experiment", "agents", "local_tools"):
        check["finding"] = (
            "Current continuation snapshot supersedes the historical V6/V7 text. "
            f"C1 V10={continuation['c1_v10']['status']}; C2 V8 attachment={continuation['c2_v8_attachment']['status']}. "
            "C1 V9 read 11 camera bodies/1584 bytes but outer return2 has no valid PASS; the one-clause V10 repair preserves numeric math. C2 V7 returned1 before model load; V8 prepare and attachment actually passed after independent reviews. "
            "S40/C1 historical generation evidence remains valid within its declared-variant scope. "
            "C1 scoring, C2 generation and S48 arms have no new authorization from this check. "
            "S51 used actual SymPy exact arithmetic. S52 used real TUM trajectory text and SciPy cross-checked RGB-time interpolation; neither calculation read image bodies or ran a model."
        )
    elif check["item"] == "innovation":
        check["finding"] = (
            f"RAIMA V4={continuation['raima_v4']['status']}; no method selected and novelty NONE. "
            "Verified local TUM timestamp metadata cannot supply three never-conditioned references in a 20ms window. "
            "V4 full CPU design is extrapolated at 90.53-140.46 days; source consistency is not real endpoint validity. "
            "Any narrower reference contract needs a new result-before protocol; no old threshold is silently relaxed."
            " Guidance v2.2 permits papers and mathematics as independent inspiration sources. S51 verified nearby original papers and a standard linear-algebra lemma, not new scientific gain."
            " S52 separates equal semantic-embedding gradients from pixel gradients and useful source attribution. LongDiff venue-year corrected to CVPR2025 using the official proceedings."
        )

# 2026-09-08 actual continuation after explicit final review handoff.
continuation.update({
    "c1_v10_actual_failure": source_only_observation("work/S45B_c1_numeric_camera_guard_supervised_v10/ACTUAL_EXECUTION_FAILURE_DIAGNOSIS_V10.json"),
    "c1_v10_review_mutation": source_only_observation("work/S45B_c1_numeric_camera_guard_supervised_v10/REVIEW_MUTATION_INCIDENT_V10.json"),
    "c1_v11": source_only_observation("work/S45B_c1_numeric_camera_guard_supervised_v11/FROZEN_SOURCE_SET.json"),
    "c2_v8_started": source_only_observation("work/resumption_20260908/C2_V8_EXTERNAL_LAUNCH/started.json"),
    "c2_v8_terminal": source_only_observation("work/resumption_20260908/C2_V8_EXTERNAL_LAUNCH/receipt.json"),
})
c2_live_path = ROOT / "work/S47B_c2_confirmation_generation_v8/execution_01/monitor.jsonl"
if c2_live_path.is_file():
    lines = c2_live_path.read_text().splitlines()
    continuation["c2_v8_monitor_observation"] = json.loads(lines[-1]) if lines else None
next_step = "Prioritize full reading of the two user repositories and innovation triage; monitor C2 actual CPU generation, complete C1 V11 ordinary full-success integration before fresh reviews, preserve V10 failure and recovered original review. No validated new method."
record["next_step"] = next_step
record["corrections"].append("At this actual check C2 V8 was authorized and launched after explicit final SHA handoffs; worker output confirms model loading and sampling began. C1 V10 also failed after 11 camera bodies/1584B; recovered original bound review bytes do not grant PASS. Legacy preparation-only wording above is historical.")
for check in record["checks"]:
    if check["item"] in ("experiment", "agents", "local_tools"):
        check["finding"] = "C2 V8 actual CPU sampling is observed in worker.stderr; not completed or scored. C1 V10 actual camera-only execution failed at record comparison; V11 author is repairing the full ordinary success chain before freeze. Source review mutation recovered to exact original SHA in a separate immutable history file. Two other agents perform S53 nearest-paper mechanism triage and full academic-figure repository reading; root reads all four learning_research tracked texts and linked primary pages."
    elif check["item"] == "skills":
        check["finding"] += " Current reading applies Supervisor vibe-research-workflow; full user-specified academic-figure skills and pengsida research guidance are being mapped into project decisions, with per-file reading scope."
    elif check["item"] == "retrieval":
        check["finding"] += " Used web search/open and public GitHub clone; Notion web extraction failed and public HTML was saved separately without claiming content read. Computer/Gemini API is absent from this session's callable tools and local AX permission check is false; no Gemini response is invented."

# Actual resumption finding supersedes earlier sampling-only observation.
if (ROOT / "work/resumption_20260908/C2_V8_RESUMPTION_OBSERVATION.json").is_file():
    continuation["c2_v8_resumption"] = source_only_observation("work/resumption_20260908/C2_V8_RESUMPTION_OBSERVATION.json")
    continuation["c2_v8_resumption_terminal_amendment"] = source_only_observation("work/resumption_20260908/C2_V8_RESUMPTION_OBSERVATION_AMENDMENT_TERMINAL_PATHS.json")
    next_step = "Continue full priority repository reading and ICML primary-paper inspiration; review the actual Gemini response. C2 V8 is interrupted: SIGTERM, zero completed batches, hidden supervisor terminal commit failure. Preserve consumed attempt; no rerun from this check. C1 V11 ordinary full success regression is being resumed before source freeze."
    record["next_step"] = next_step
    record["corrections"].append("C2 V8 sampling has stopped; do not treat the earlier running observation as current. Direct cua_repl now successfully inspected the Gemini tab and submitted the authorized public research prompt; local AX false did not imply no computer interface.")
    for check in record["checks"]:
        if check["item"] in ("experiment", "agents", "local_tools"):
            check["finding"] += " Latest resumption supersedes the above running state: C2 V8 stopped after SIGTERM with completed_batches=0, known monitor/terminal failure; related processes absent. Root reviewed exact final recovery SHA and amendment. C1 V11 unfinished source-only work is resumed by a declared new author, with no formal guard or pixel run."
        elif check["item"] == "retrieval":
            check["finding"] += " Correction: callable cua_repl successfully reads authorized Gemini Pro Extended; task prompt sent. Pengsida project and idea page toggles expanded and read via browser. ICML PMLR primary PDF reading is active in a separate agent."

# Current completed reading and V11 continuation override, preserving old ledger rows.
if (ROOT / "work/S54_priority_repository_reading/gemini/ROOT_ADOPTION_RECEIPT.json").is_file():
    refs = {
        "reading_external_coverage": "work/S54_priority_repository_reading/learning_research_external_coverage.json",
        "gemini_actual_adoption": "work/S54_priority_repository_reading/gemini/ROOT_ADOPTION_RECEIPT.json",
        "arxiv_actual_query": "work/S54_priority_repository_reading/sources/arxiv_api_history_guidance/receipt.json",
        "c1_v11_primary": "work/S45B_c1_numeric_camera_guard_supervised_v11/SOURCE_REVIEW_PRIMARY_V11.json",
        "c1_v11_adversarial": "work/S45B_c1_numeric_camera_guard_supervised_v11/SOURCE_REVIEW_ADVERSARIAL_V11.json",
        "c1_v11_formal": "work/resumption_20260908/C1_V11_FORMAL_ORCHESTRATION.json",
        "c1_v11_result_review": "work/S45B_c1_numeric_camera_guard_supervised_v11/INDEPENDENT_RESULT_REVIEW_V11.json",
    }
    continuation.update({key: source_only_observation(path) for key, path in refs.items()})
    formal_path = ROOT / refs["c1_v11_formal"]
    formal_return = read_json(formal_path).get("returncode") if formal_path.is_file() else "NOT_EXECUTED"
    next_step = "Finish C1 V11 actual camera result review and the existing S46 blind-score connection; preserve interrupted C2 V8 and use a new recovery attempt. Apply completed repository and ICML reading to one discriminating research question. No method is selected or validated."
    if formal_return not in (0, "NOT_EXECUTED"):
        next_step = "C1 V11 actual supervisor returned nonzero after numeric worker success; diagnose the production stdout/flush/exit tail before any new source version. No terminal PASS or score is authorized. Preserve C2 interrupted attempt. Repository/ICML/Gemini reading is complete within recorded scope; no method validated."
    record["next_step"] = next_step
    record["corrections"].append("Current evidence supersedes all earlier preparation/reading-in-progress descriptions. Gemini 3.1 Pro Extended response and independent rejection of unsupported mechanism are saved. S40 run_state is a historical raw receipt status, not current review completion.")
    for check in record["checks"]:
        if check["item"] in ("experiment", "agents", "local_tools"):
            check["finding"] = f"C1 V11 frozen source received two final different-author PASS reviews; actual camera-only supervisor return={formal_return}, scientific scope determined by its terminal and independent result review. C2 V8 stopped during first-batch sampling with zero completed batches. No new video or method result is inferred. S46 version adaptation is source-only; no C1 pixels viewed."
        elif check["item"] == "skills":
            check["finding"] = "Supervisor handbook 2.2/2.3 and relevant research skills remain primary. Principles v2.3, innovation guidance and full reading reports now apply user-selected pengsida and figure repository material. Claude skills are used without invoking Claude models."
        elif check["item"] == "retrieval":
            check["finding"] = "Actual public arXiv API HTTP200 returned History-Guided Video Diffusion v2. Two ICML2025 primary papers were read within recorded sections. All four pengsida tracked texts and eight core external visible pages were read, including expanded toggles. Actual Gemini Pro Extended response was independently checked; unsupported citations/mechanism were not adopted."
        elif check["item"] == "innovation":
            check["finding"] = "NO_METHOD_SELECTED; new_method_validated=false. Standard algebra shows final output interaction can arise downstream; S55 suggests same-start first-denoiser observation within future existing arms. This is an unimplemented diagnostic refinement, not a new algorithm. Current priority is reliable baseline failure evidence and a bounded falsifiable question."

# V12 observations describe actual artifacts; a source PASS remains distinct from execution.
v12_dir = ROOT / "work/S45B_c1_numeric_camera_guard_supervised_v12"
if (v12_dir / "FROZEN_SOURCE_SET.json").is_file():
    v12_refs = {
        "c1_v12_source": "work/S45B_c1_numeric_camera_guard_supervised_v12/FROZEN_SOURCE_SET.json",
        "c1_v12_formal": "work/resumption_20260908/C1_V12_FORMAL_ORCHESTRATION.json",
        "c1_v12_result_review": "work/S45B_c1_numeric_camera_guard_supervised_v12/INDEPENDENT_RESULT_REVIEW_V12.json",
        "s46_v3_source": "work/S46_c1_blind_scoring_wrapper_v3/FROZEN_SOURCE_SET.json",
        "s46_c1_score": "work/S46_c1_blind_scoring_preparation/C1_score_attempt_01/receipt.json",
        "s46_c1_recompute_review": "work/S46_c1_blind_scoring_preparation/C1_independent_recompute/execution_01/independent_result_review.json",
        "c1_post_score_visual": "results/S44_C1_confirmation_generation/visual_qa_all9/VISUAL_QA_OBSERVATION.json",
    }
    continuation.update({key: source_only_observation(path) for key, path in v12_refs.items()})
    v12_formal = ROOT / v12_refs["c1_v12_formal"]
    v12_return = read_json(v12_formal).get("returncode") if v12_formal.is_file() else "NOT_EXECUTED"
    v12_review = ROOT / v12_refs["c1_v12_result_review"]
    review_status = read_json(v12_review).get("status") if v12_review.is_file() else "NOT_DELIVERED"
    score_path = ROOT / v12_refs["s46_c1_score"]
    score_status = read_json(score_path).get("status") if score_path.is_file() else "NOT_EXECUTED"
    score_report_path = score_path.parent / "report.json"
    score_math = read_json(score_report_path).get("math_result", {}) if score_report_path.is_file() else {}
    next_step = "Continue from actual V12 numeric terminal and independent review, then the existing S46 blind scoring contract. Preserve V11 failure and interrupted C2 V8. No method has been selected or validated."
    record["next_step"] = next_step
    for check in record["checks"]:
        if check["item"] in ("experiment", "agents", "local_tools"):
            check["finding"] = f"V12 fixes the shared actual production write/flush tail with independent source reviews and real pipe fault checks; actual supervisor return={v12_return}, independent numeric review={review_status}, C1 score receipt={score_status}. These distinct stages do not imply visual quality or innovation. C2 V8 remains interrupted with zero completed batches."
        elif check["item"] == "innovation" and score_math:
            check["finding"] = f"C1 frozen primary event={score_math.get('event_MSE_gt_0_01')}; B0 event is false. If C1 remains valid and false, C2 alone cannot reach the original at-least-two-of-three criterion. C2 remains mandatory and cohort INCOMPLETE. Do not alter threshold/ROI or cherry-pick diagnostic pairs; choose a new important question only with new prospective evidence. No method selected or validated."
    if score_math:
        next_step = "C1 is machine-scored; consult exact independent recompute/result review and post-score visual observations. Preserve all results and complete C2 with a new authorized recovery attempt. Accept the unsupported narrow hypothesis instead of moving thresholds; define a new important research question before method experiments."
        record["next_step"] = next_step
    record["corrections"].append("V12 observations supersede the older V11-in-progress text. Original failed V11 and review tickets remain preserved; no worker or pending candidate is promoted to final success.")

# September 9 local continuation. Read actual V9 receipts without promoting presence to success.
v9_dir = ROOT / "work/S47B_c2_confirmation_generation_v9"
if (v9_dir / "FROZEN_SOURCE_SET_V9.json").is_file():
    v9_refs = {
        "c2_v9_source": "work/S47B_c2_confirmation_generation_v9/FROZEN_SOURCE_SET_V9.json",
        "c2_v9_primary_source": "work/S47B_c2_confirmation_generation_v9/SOURCE_REVIEW_PRIMARY_V9.json",
        "c2_v9_adversarial_source": "work/S47B_c2_confirmation_generation_v9/SOURCE_REVIEW_ADVERSARIAL_V9.json",
        "c2_v9_prepare": "work/resumption_20260909/C2_V9_PREPARE_ORCHESTRATION.json",
        "c2_v9_attachment": "work/resumption_20260909/C2_V9_ATTACH_ORCHESTRATION.json",
        "c2_v9_authorization": "work/resumption_20260909/C2_V9_AUTHORIZATION_ORCHESTRATION.json",
        "c2_v9_external_start": "work/resumption_20260909/C2_V9_EXTERNAL_LAUNCH/started.json",
        "c2_v9_external_return": "work/resumption_20260909/C2_V9_EXTERNAL_LAUNCH/receipt.json",
        "s56_reading": "work/S56_negative_result_question_triage/SOURCE_READ_SCOPE_RECEIPT.json",
        "s56_gemini": "work/S56_negative_result_question_triage/gemini/INTERACTION_AND_REVIEW_RECEIPT.json",
        "s57_all30_observation": "work/resumption_20260909/S57_ALL30_EXTERNAL_RETURN_OBSERVATION.json",
        "c2_v9_terminal_correction": "work/resumption_20260909/C2_V9_TERMINAL_OBSERVATION_CORRECTION.json",
        "s57_coordinate_correction": "work/S57_coordinate_convention_audit/FINAL_DELIVERY.json",
        "s59_primary_reading": "work/S59_rollout_mechanism_learning/SOURCE_READ_SCOPE.json",
        "s59_gemini": "work/S59_rollout_mechanism_learning/gemini/INTERACTION_AND_REVIEW_RECEIPT.json",
        "s60_terminal_failure": "work/S60_c2_v9_failure_audit/TERMINAL_FAILURE_AUDIT.json",
        "s60_unit_replay_review": "work/S60_renderer_unit_replay/INDEPENDENT_RESULT_REVIEW.json",
        "s60_all_depths": "work/S60_scale_gauge_source_question/ALL_FIVE_SAVED_DEPTHS.json",
    }
    continuation.update({key: source_only_observation(path) for key, path in v9_refs.items()})
    v9_monitor = v9_dir / "execution_01/monitor.jsonl"
    v9_live = None
    if v9_monitor.is_file():
        for line in reversed(v9_monitor.read_text().splitlines()):
            try:
                v9_live = json.loads(line)
                break
            except json.JSONDecodeError:
                continue
    continuation["c2_v9_latest_monitor"] = v9_live
    v9_outer_path = ROOT / v9_refs["c2_v9_external_return"]
    v9_return = read_json(v9_outer_path).get("returncode") if v9_outer_path.is_file() else "NO_EXTERNAL_RETURN_RECEIPT"
    next_step = "C2 V9 externally returned1 after one completed batch: independent failure audit is complete. S60 saved-geometry two-condition original-kernel replay and independent result review confirm a unit-dependent empty retrieval; all five final depth maps are tiny before surfel construction. Define a unit-consistent baseline repair variant while preserving the consumed attempt; no C2 full readback, score or quality claim. Previous17:11 running description was stale and is explicitly corrected. S57 source-coordinate correction withdrew all15 inconsistent labels as model-failure evidence. S59 two formal NeurIPS papers and Gemini critique completed within recorded scope; equal-energy noise does not identify exposure bias. No method selected or validated."
    record["next_step"] = next_step
    record["corrections"].append("V9 has its own immutable recovery namespace with unchanged scientific controls. C1 score, independent recomputation and nine-frame post-score observation are already complete. S56 is question triage and Gemini critique, not new-method evidence. Current V9 receipt observations supersede legacy V8 running/preparation language.")
    for check in record["checks"]:
        if check["item"] in ("experiment", "agents", "local_tools"):
            check["finding"] = f"C1 measurement/recompute/post-score display completed. V9 preserves the V8 interrupted attempt and requires its existing actual stage-specific evidence. Latest external V9 return={v9_return}; monitor={v9_live}. Observed file statuses are recorded separately, not automatically approved. S57 saved-output measurement and separate source-coordinate correction are complete: B0 13 nominal-consistent/1 unknown/1 endpoint; C1 14 unknown/1 endpoint. Original inconsistent labels are withdrawn as failure evidence. V9 actual return1 is a partial generation failure, not a quality score; latest monitor is historical after exit, never proof of liveness."
        elif check["item"] == "retrieval":
            check["finding"] = "S56 read three primary methods (WorldStereo, SPMem, GEN3C) within recorded sections. Gemini Pro Extended was actually consulted through CUA; full prompt/response and independent source/mathematical corrections are saved. CameraCtrl venue corrected to ICLR2025; S59 Self Forcing and FramePack formal NeurIPS2025 specified sections, actual source reads, exact anisotropy counterexample and second Gemini full response/critique are saved. AI suggestions are not evidence."
        elif check["item"] == "innovation":
            check["finding"] = "B0 and C1 strict events are false; original at-least-two-of-three cannot be reached, while C2 remains mandatory. S56 rejects current method commitment and retains bounded rendered-camera observation before longer-horizon claims. No ROI/threshold/pair changes, no ordinary homography/SIFT novelty claim, NO_METHOD_SELECTED and new_method_validated=false."
        elif check["item"] == "records":
            check["finding"] = "Actual session events, source handoffs, negative results, S56/S59 reading, Gemini critique, S57 observer erratum and explicit C2 stale-status correction remain in the append-only project ledger. Source-only, synthetic controls, existing real generated frames and new generation must retain distinct labels."

# S61 is a saved-data component result, not a new generation or cohort completion.
s61_review = ROOT / "work/S61_unit_consistent_retrieval/INDEPENDENT_RESULT_REVIEW.json"
if s61_review.is_file():
    continuation["s61_component_result"] = source_only_observation(
        "work/S61_unit_consistent_retrieval/INDEPENDENT_RESULT_REVIEW.json"
    )
    if (
        sha256(s61_review) == "84e5df2fcab2c5ee3a932e534296aedc22fc26929e2bf7eece42ad2284b23181"
        and read_json(s61_review).get("status") == "PASS_S61_SAVED_GEOMETRY_COMPONENT_ACCEPTANCE"
    ):
        next_step = "S61 reusable renderer-unit adapter passed five finite synthetic checks and one saved C2 geometry acceptance with three fixed length units; actual external return0 and independent result review are complete. Three numeric maps match S60 exactly; zero model/RGB/new C2. Next verify one successful B0/C1 saved retrieval input and the original context selection/cache-index chain. Normalized depth changes weights; this is a baseline engineering variant, not full-pipeline scale invariance or new-method evidence. Preserve all original C2 failures and NO_METHOD_SELECTED."
        record["next_step"] = next_step
        record["corrections"].append("S61 now has an implemented and independently checked saved-data component. This supersedes S60's component-not-yet-implemented stage only; full generation and C2 completion remain absent.")
        for check in record["checks"]:
            if check["item"] == "experiment":
                check["finding"] = "S61 actual external run18:31:03.822785–18:31:11.024874Z returned0 in7.202s. Three fixed units of one515-point scene each called the original renderer once; all output maps match S60 exactly. Independent result review18:34:24Z passed. This is saved geometry computation, no new model/RGB/full C2."
            elif check["item"] == "agents":
                check["finding"] = "Adapter author, independent source/result reviewer, semantic-neighbor reviewer and root acceptance execution had separate responsibilities. Final S61 author-only handoff and review identities are recorded; no agent result is counted as a new method."
            elif check["item"] == "innovation":
                check["finding"] = "S61 uses known common-length normalization and changes cos/(1+depth) semantics. Pinned DUSt3R sources and old S27/S29/S34 evidence were reread, not counted as a new search or discovery. No method selected, no quality gain established; original B0/C1 negative events and C2 failure remain."

s62_review = ROOT / "work/S62_b0_context_integration/INDEPENDENT_RESULT_REVIEW.json"
if s62_review.is_file():
    continuation["s62_context_result"] = source_only_observation(
        "work/S62_b0_context_integration/INDEPENDENT_RESULT_REVIEW.json"
    )
    if (
        sha256(s62_review) == "6bfac5fbb371be8a373579e53f8f2353bbee24aabd4290096599b6f978b64ff4"
        and read_json(s62_review).get("status") == "PASS_S62_BOUNDED_SAVED_CONTEXT_RESULT_REVIEW"
    ):
        next_step = "S62 one saved successful B0 input passed original and S61 context paths, including real cache gathers and independent result review. Weights changed but five-source quotas, IDs[0,2,4,1] and all true context arrays stayed equal. C2 pre-failure seq50 true cache is present by metadata/size only. Follow work/S62_b0_context_integration/ROOT_NEXT_ACTION.md for a separate failed-C2 input declaration, exact expected original failure and adapter context check before a production variant. No new model/RGB/get_cond/full C2 or validated method."
        record["next_step"] = next_step
        record["corrections"].append("S62 advances one successful saved-input path through actual NMS and true cache gather. It supersedes S61's context-not-yet-checked stage only, not missing C2 or generation evidence.")
        for check in record["checks"]:
            if check["item"] == "experiment":
                check["finding"] = "S62 external19:24:11.899512–19:24:19.337218Z returned0 in7.437706s. Two original context calls on one567-surfel B0 input read1678 unique numeric blobs/2571584B; each invoked one original renderer/retrieval. Independent result review19:28:56Z verified finite maps and all true cache slots. Zero model/RGB/get_cond/new generation."
            elif check["item"] == "innovation":
                check["finding"] = "Before execution, source/oldS34 analysis predicted that same source membership with context4 and1<=k<=14 gives quota1 each. S62 observed changed weights with unchanged IDs and true context; this is known engineering mechanism validation, not method novelty or video benefit. No threshold/ROI/candidate-budget change, NO_METHOD_SELECTED."
            elif check["item"] == "agents":
                check["finding"] = "Separate S62 source author, source/result reviewer, pre-result semantic reviewer and root execution. Reviewer independently read4NPZ and26 necessary original numeric blobs, without author Decoder or renderer rerun. C2 cache coverage is metadata-only, not a run."

# S63 is a completed saved-failure context check, not a model generation.
s63_review = ROOT / "work/S63_c2_context_integration/INDEPENDENT_RESULT_REVIEW.json"
if s63_review.is_file():
    continuation["s63_failed_context_result"] = source_only_observation(
        "work/S63_c2_context_integration/INDEPENDENT_RESULT_REVIEW.json")
    if (sha256(s63_review) == "90c3eff57423f0360ada6bdfb3ebcbbdf428b707962568698634eae63528a426"
        and read_json(s63_review).get("status") == "PASS_S63_BOUNDED_INDEPENDENT_RESULT_REVIEW"):
        next_step = "S63 saved failed C2 input passed exact original IndexError reproduction and S61 full context/cache return, with independent result review. Follow work/S63_c2_context_integration/ROOT_NEXT_ACTION.md to prepare a separately declared production renderer-unit variant, fresh original image/seed44 and two batches. Earlier RNG snapshot is before later optimizer random draws; saved cache is not a strict generation checkpoint. Do not rerun successful S60-S63 without reason or replace original cohort missing C2. No method selected, no new full generation yet."
        record["next_step"] = next_step
        record["corrections"].append("S63 supersedes metadata-only C2-cache and context-not-yet-tested language. Full model/get_cond and generation are still outside this completed saved-data check.")
        findings = {
            "skills": "Applied Supervisor Vibe Coding small verifiable steps and local Claude scientific-critical-thinking measurement validity, confounding and post-exposure boundaries. Exact actual application is in docs/S63_C2_REAL_CONTEXT_RECOVERY_RESULT.md; no Claude model and no invented user attestation.",
            "experiment": "S63 external20:23:36.359549-20:23:39.312174Z returned0 in2.952651s. Original exact empty maps/line711 IndexError; canonical58756 support/438 surfels, IDs[0,2,4,1], true FP32 cache slots exact. Independent result20:27:52Z passed.1496 archive blobs1631256B plus seen51896B reference, zero model/RGB/get_cond/new video.",
            "innovation": "Restored source reachability and true cache return on one seen failure are conventional baseline engineering. Original empty pool versus canonical five-source pool is not evidence of weight-quality gain. Original two false events and failed C2 preserved, NO_METHOD_SELECTED, novelty NONE.",
            "agents": "Separate author, independent source/result reviewer, production source/state analyst and root execution. Independent result decoder read15 necessary original blobs1528164B and3 new NPZ plus1 seen reference, with no rerender. Root verified final reports and actual byte identities.",
            "retrieval": "Existing S60/S61 official issue/scale semantics and S34 mechanism sources reused; no new external fact or novelty claim required a repeated search/Gemini query. New hypothesis or production-claim expansion still requires targeted primary retrieval.",
            "local_tools": "Used current CPU8 Python3.12.14/NumPy1.26.4/Torch2.7.0/SciPy1.16.2 for one bounded saved-data run, metadata/source inspection and independent numeric readback. Full production variant has not run.",
            "records": "Canonical append-only events retain actual S63 source handoff, unique runtime, independent result, minor root SHA-helper correction and production RNG-gap assessment. Current docs and dated snapshot distinguish saved context success from missing original full C2 and no method gain."
        }
        for check in record["checks"]:
            if check["item"] in findings:
                check["finding"] = findings[check["item"]]

# S64 has its own live production variant identity; old S40 raw state is historical.
s64 = ROOT / "work/S64_unit_repaired_generation"
if (s64 / "AUTHOR_DELIVERY.json").is_file():
    s64_state = {"row": "C2_UNIT_REPAIRED_S64", "original_cohort_eligible": False}
    for label, relative in {
        "author": "AUTHOR_DELIVERY.json", "prepared": "freeze_attempt_01/receipt.json",
        "attached": "review_attachment_01/receipt.json", "authorized": "ROOT_AUTHORIZATION_ORCHESTRATION.json",
        "external_started": "external_launch_01/started.json", "external_return": "external_launch_01/receipt.json",
        "worker": "execution_01/worker_receipt.json", "parent": "execution_01/receipt.json"
    }.items():
        path = s64 / relative
        if path.is_file():
            value = read_json(path)
            s64_state[label] = {"path": str(path), "sha256": sha256(path), **{key: value[key] for key in ("status", "returncode", "started_utc", "completed_utc", "supervisor_pid", "elapsed_seconds") if key in value}}
    monitor = s64 / "execution_01/monitor.jsonl"
    if monitor.is_file():
        lines = monitor.read_text().splitlines()
        if lines:
            s64_state["last_monitor"] = json.loads(lines[-1])
            s64_state["monitor_age_seconds"] = (now - datetime.fromisoformat(s64_state["last_monitor"]["utc"])).total_seconds()
    continuation["s64_unit_variant_current"] = s64_state
    if "external_return" in s64_state:
        next_step = "S64 external launcher has actually returned; independently review its return, terminal, actual unit-call receipt and archive before classifying completion. Then do bounded result readback and prefix identity comparison. Keep original C2 failure and original cohort separate. No method selected."
    elif "external_started" in s64_state:
        next_step = "Continue observing the single already-started S64 unit-repaired generation and actual live monitor until external return. Do not launch a duplicate. Prepare minimal output readback in parallel, then verify actual unit call and both batches. Original C2/cohort unchanged, no novelty claim."
    else:
        next_step = "Continue the existing S64 reviewed prepare/attach/authorization chain using actual published artifacts, then once-only generation. S60-S63 completed; do not rerun them or relabel engineering as novelty."
    record["next_step"] = next_step
    record["corrections"].append("S64 current observation supersedes S63 next-step text; original S40 raw run_state and prior completed saved-data scopes remain historical, not the new production state.")
    for check in record["checks"]:
        if check["item"] == "experiment":
            check["finding"] = "Current S64 separately declared unit variant stages are bound in continuation.s64_unit_variant_current. Installation or process start is not generation completion; external return plus terminal and independent evidence review are separate."
        elif check["item"] == "innovation":
            check["finding"] = "S64 is a conventional unit repair derived after the C2 failure, excluded from original cohort. Weight semantics change. NO_METHOD_SELECTED and novelty NONE remain; geometric observability is a question, not a method."
        elif check["item"] == "agents":
            check["finding"] = "Different author and two independent reviewers checked the actual S64 source, prepared core and published package; root owns execution. Actual reports record their bounded scopes."
        elif check["item"] == "local_tools":
            check["finding"] = "Current local filesystem/source/resource tools and retained CPU8 FP32 generation route are used; actual execution stage appears in s64_unit_variant_current. No duplicate model run."
        elif check["item"] == "records":
            check["finding"] = "S64 exact source delivery, first failed fixture check, final local check, genuine independent reviews, actual prepare/attachment/launch receipts and canonical events are retained. No backdated timestamps or overwritten old C2 attempt."

# S65 is independently checked mathematics and primary-source reading, not a model result.
s65 = ROOT / "work/S65_observability_triage"
if (s65 / "PRIMARY_MATH_REVIEW.json").is_file():
    continuation["s65_observability_triage"] = {
        name: {"path": str(s65 / name), "sha256": sha256(s65 / name)}
        for name in ("PRIMARY_MATH_REVIEW.json", "GEMINI_OBSERVATION.json",
                     "ROOT_EXACT_COUNTEREXAMPLE.json", "S65_BEGINNER_RESEARCH_NOTE.md")
        if (s65 / name).is_file()
    }
    for check in record["checks"]:
        if check["item"] == "retrieval":
            check["finding"] = "S65 actual Gemini Pro Extended reply retained and independently corrected using DROID-SLAM NeurIPS2021 main/supplement and CVPR2016 SfM Revisited. Root and independent Fraction calculations agree. VGGT abstract/index only; PDF403 and HTML404 retained. No new method selected."
        elif check["item"] == "skills":
            check["finding"] = "Supervisor Vibe Coding small implementation/result steps and Claude local scientific-critical-thinking applied to S64 independent production/readback review and S65 measurement identifiability, counterexample and confounding. Skills are local guidance, not a Claude model call."

# S64 completed engineering readback; retain its own prospective scoring boundary.
s64_result = ROOT / "work/S64_unit_repaired_generation/INDEPENDENT_POSTRUN_RESULT_REVIEW.json"
if s64_result.is_file() and sha256(s64_result) == "c5a60a522eea8ecf27b75908c72f7f66717a08ed91b6a011ee2bf88383fcf562":
    continuation["s64_independent_postrun_result"] = {"path": str(s64_result), "sha256": sha256(s64_result), "status": read_json(s64_result)["status"]}
    next_step = "S64 full generation and bounded independent readback are complete. Do not rerun this model. Follow NEXT_CAMERA_SCORE_REUSE_NOTE.md for a thin S64 binding of existing camera and scoring mathematics: camera numeric result, fixed exploratory score and independent recomputation, then all-nine-frame viewing. Preserve original C2 failure/cohort; quality still NOT_EVALUATED, no new method."
    record["next_step"] = next_step
    for check in record["checks"]:
        if check["item"] == "experiment":
            check["finding"] = "S64 external generation returned0 in2729.029596s, two50-step batches. Actual readback returned0 in1.161150s; different author directly rehashed92 payloads161552008B including147308544B RGB, confirmed real cache consumption and27 equal prefix fields. No quality score/image display/model recomputation."
        elif check["item"] == "records":
            check["finding"] = "Actual S64 generation, terminal review, one readback, independent173 grouped checks and27 raw prefix comparisons are preserved. Root pre-execution interpreter correction retained without inventing a failed run. Current result and S65 beginner note lead the handoff."

# S66 fixes the measurement scope without rerunning the completed model.
s66 = ROOT / "work/S66_s64_camera_scoring"
if (s66 / "ROOT_SCORE_RECOMPUTE_OBSERVATION.json").is_file():
    s66_state = {}
    for name in ("ROOT_SESSION_START.json", "RESULT_INTERPRETATION_BEFORE_SCORE.md", "SOURCE_REVIEW.json", "CAMERA_INDEPENDENT_RESULT_REVIEW.json", "ROOT_SCORE_RECOMPUTE_OBSERVATION.json", "score_01/report.json", "score_01/receipt.json", "external_score_01/receipt.json", "recompute_01/report.json", "recompute_01/receipt.json", "external_recompute_01/receipt.json", "INDEPENDENT_SCORE_RESULT_REVIEW.json", "ROOT_VISUAL_BINDING.json", "ROOT_VISUAL_QA_OBSERVATION.json", "NEXT_SCIENTIFIC_DECISION_REVIEW.md"):
        path = s66 / name
        if path.is_file():
            s66_state[name] = {"path": str(path), "sha256": sha256(path)}
    continuation["s66_actual_measurement"] = s66_state
    final_review = s66 / "INDEPENDENT_SCORE_RESULT_REVIEW.json"
    visual = s66 / "ROOT_VISUAL_QA_OBSERVATION.json"
    complete = final_review.is_file() and read_json(final_review).get("status", "").startswith("PASS") and not read_json(final_review).get("blockers") and visual.is_file()
    next_step = ("S66 fixed scoring, actual independent recomputation and all-nine-frame viewing completed. Preserve the original C2 failure and current null method claim; follow the bounded next scientific decision on translated queries and selection sensitivity before expanding video generation." if complete else "S66 score and independent implementation recompute returned0 with exact math. Finish the different-author result review, then actual all-nine PNG export and viewing; do not repeat successful scoring or model runs.")
    record["next_step"] = next_step
    findings = {
        "skills": "Supervisor Vibe Coding small actual execution and figure-designer complete-frame QA; local Claude scientific-critical-thinking applied to confounding, measurement limits and prospective interpretation. No claimed user attestation or Claude model call.",
        "innovation": "S64 engineering variant fixed MSE event false; no method selected. Distinguish short pure rotation from depth observability and actual selection sensitivity. k<=14 weight branch alone cannot justify longer generation; source-pool changes remain possible.",
        "experiment": "S66 camera independently verified11 bodies1584B. Score and another implementation actually read9 RGB snapshots8957952B each, returned0 with identical9 metrics/hex/counts/event. MSE0.0006382446123931144 is an exploratory single-variant result, not a replacement C2 row or method improvement. Final review/display availability recorded in continuation.",
        "local_tools": "Existing Python3.12.14/NumPy1.26.4 environment used for bounded score/recompute and original RGB PNG export. Actual receipts and image manifests separate computation from display; no duplicate model.",
        "retrieval": "No fresh broad retrieval needed for fixed existing measurement. Reuse verified S65 DROID/SfM primary sources and Gemini reply; the next-decision reviewer records any new targeted source access. No claim of fresh search or model consultation merely for tool count.",
        "agents": "Separate source author, camera/math reviewer and final score-result reviewer; root ran score/recompute and owns binding/display. Team-internal independent checks, not external independent model reproduction.",
        "records": "Actual source, camera, score and recompute returns and partial/failed fixture history retained. New S66 artifacts are separate; current entrypoint synchronization and dated all-frame snapshot follow accepted results. No backdated checks."
    }
    for check in record["checks"]:
        if check["item"] in findings:
            check["finding"] = findings[check["item"]]
    record["corrections"].append("S66 current measurement supersedes S64 quality-not-yet text. Historical S40 fields and original failed C2 remain unchanged; absence of a final review/display is not silently treated as completion.")

# S67 is one controlled saved-data pair; it is not a new model run.
s67 = ROOT / "work/S67_translated_query_diagnostic"
if (s67 / "external_01/receipt.json").is_file():
    s67_paths = ("PROTOCOL.md", "AUTHOR_DELIVERY.json", "SOURCE_REVIEW.json", "external_01/receipt.json", "execution_01/receipt.json", "ROOT_ACTUAL_RESULT_OBSERVATION.json", "INDEPENDENT_RESULT_REVIEW.json", "NEAREST_WORK_BOUNDARY.md", "ROOT_PRIMARY_SOURCE_CROSSCHECK.json", "PLOT_RUNTIME_CORRECTION.json", "ROOT_FIGURE_QA.json")
    continuation["s67_fixed_pair"] = {name: {"path": str(s67/name), "sha256": sha256(s67/name)} for name in s67_paths if (s67/name).is_file()}
    final = s67 / "INDEPENDENT_RESULT_REVIEW.json"
    verified = final.is_file() and read_json(final).get("status", "").startswith("PASS") and not read_json(final).get("blockers")
    next_step = ("S67 fixed-pair result independently verified: projection changed but all selected IDs and returned contexts stayed identical. Stop adding generation for this fixed selected-ID explanation. Next establish an available real translated-reference witness and a matched ordinary selection baseline before choosing a method or extending video runs." if verified else "S67 actual external5.064598s return0. Root checked all outputs and identical contexts; different-author independent numerical review is pending. Finish it without rerunning renderer/model, then preserve the fixed-case null selected-ID result.")
    record["next_step"] = next_step
    findings = {
        "skills": "Supervisor small fixed diagnosis, handbook2.3 hidden-assumption check, idea-evaluator F6/F9 limited application, local Claude scientific-critical-thinking and figure-designer all-data plot. No claimed full five-dimension score or user attestation.",
        "innovation": "S67 changes515 points along common-center rays at one fixed translated query.514 points change by>1e-6px, max57.9713px; same five members/quota1 and selected[0,2,4,1], all4context types+IDs byte-identical. This rejects only this fixed selected-ID mechanism; no method gain or universal geometry conclusion.",
        "experiment": "One real CPU numerical diagnostic on existing archived data,1496 blobs1631256B, A/B each one original renderer/retrieval/context call, externalreturn0 in5.064598s. No RGB/model/get_cond/video; same actual query, both units equal, no parameter retries. Independent result availability recorded in continuation.",
        "local_tools": "Existing Python3.12.14 NumPy1.26.4 Torch2.7.0 SciPy1.16.2 environment for diagnostic. Initial figure import lacked matplotlib; retained failure, reused existing plotting venv NumPy2.3.5/Matplotlib3.10.6, exported all-data SVG/PNG and visually checked. Experiment environment unchanged.",
        "retrieval": "Actual targeted primary retrieval: WorldStereo and Coverage Optimization for Camera View Selection. Author HTML methods/ablations/limits read, root directly crosschecked key sections; formal PDF/direct-page failures retained. Attribute-regression Fisher gain is not a depth posterior; current pair lacks independent benefit labels. No repeated Gemini call for this already-scoped diagnostic.",
        "agents": "Separate code author, source reviewer and independent numerical/result reviewer; root performed the one actual pair, context byte comparison, original-paper crosscheck and descriptive plot. Team internal roles and actual review scopes retained.",
        "records": "S66 nine real output PNGs and score package copied into current workspace with22 matching file SHAs. S67 frozen protocol/source, actual return, root result, reading and plot runtime correction retained; append-only main ledger and dated current handoff distinguish pending from verified."
    }
    current_evidence = {
        "skills": "RESEARCH_PRINCIPLES.md",
        "innovation": "work/S67_translated_query_diagnostic/INDEPENDENT_RESULT_REVIEW.md" if verified else "work/S67_translated_query_diagnostic/ROOT_ACTUAL_RESULT_OBSERVATION.json",
        "experiment": "work/S67_translated_query_diagnostic/external_01/receipt.json",
        "local_tools": "work/S67_translated_query_diagnostic/ROOT_FIGURE_QA.json",
        "retrieval": "work/S67_translated_query_diagnostic/NEAREST_WORK_BOUNDARY.md",
        "agents": "work/S67_translated_query_diagnostic/INDEPENDENT_RESULT_REVIEW.json" if verified else "work/S67_translated_query_diagnostic/SOURCE_REVIEW.json",
        "records": "RESEARCH_LOG.md",
    }
    for check in record["checks"]:
        if check["item"] in findings:
            check["finding"] = findings[check["item"]]
            check["evidence"] = current_evidence[check["item"]]
    record["corrections"].append("Current S67 fixed numerical pair supersedes older S66 next-action/source-preparation text. Original failed C2 and S40 raw terminal fields remain historical; no novelty inferred from new files.")

# S68 is a real five-history encoder bridge with a separately bounded result review.
s68 = ROOT / "work/S68_tum_vmem_cache_bridge"
if (s68 / "ROOT_FINAL_RESULT_ACCEPTANCE.json").is_file():
    paths = ("ROOT_FINAL_RESULT_ACCEPTANCE.json", "PROTOCOL.md", "ARGV_CORRECTION.json", "SOURCE_REVIEW.json", "external_01/receipt.json", "execution_01/receipt.json", "INDEPENDENT_RESULT_REVIEW.json", "NON_DUPLICATED_QUESTION_REVIEW.md", "NEXT_CAMERA_CONSUMER_INTERFACE.md", "PRIMARY_SOURCE_INPUT_CONTRACT_REVIEW.md")
    continuation["s68_real_history_appearance_cache"] = {name: {"path": str(s68/name), "sha256": sha256(s68/name)} for name in paths if (s68/name).is_file()}
    final = read_json(s68 / "INDEPENDENT_RESULT_REVIEW.json")
    accepted = read_json(s68 / "ROOT_FINAL_RESULT_ACCEPTANCE.json")
    verified = final.get("status") == "PASS_S68_INDEPENDENT_APPEARANCE_RESULT_REVIEW" and not final.get("blockers") and accepted.get("status") == "ACCEPTED_FIVE_REAL_HISTORY_APPEARANCE_CACHE_ONLY"
    next_step = ("S68 five real history appearance caches independently verified. Reuse three S52 RGB-time cameras and add six missing timestamps, verify actual axis/ray convention, then execute original scaling/get_cond on fixed ordered sets. No new generation yet; old target-RGB exposure limits this to a known fixed-set conditional comparison. Do not re-encode S68 or rerun successful S64-S67." if verified else "S68 root acceptance exists but result status is inconsistent; resolve retained evidence before dependent work.")
    record["next_step"] = next_step
    findings = {
        "skills": ("Supervisor Vibe Coding fixed small source, different-author review, actual once-only run and bounded result check; idea-evaluator F1/F6/F9 limited application and local Claude scientific-critical-thinking for input exposure and proxy boundaries. No full idea score or Claude model call.", "RESEARCH_PRINCIPLES.md"),
        "innovation": ("Old S8 query pose used target RGB despite update=false. Fixed ordered sets [19,18,13,12] vs [19,18,14,13] permit only post-selection conditional comparison; recompute all downstream camera/conditioning quantities. Five appearance caches are engineering preparation, not a new method. NO_METHOD_SELECTED remains.", "work/S68_tum_vmem_cache_bridge/NON_DUPLICATED_QUESTION_REVIEW.md"),
        "experiment": ("Actual once-only CPU8 FP32 original VAE/CLIP bridge encoded five real history PNGs, external18.644267s return0, 2625997B RGB and4279161112B weights. Five NPZ contain20 arrays. Different author checked source PNG identities/headers, saved outputs and independent K arithmetic; no neural reproduction, target pixels, depth, get_cond or video.", "work/S68_tum_vmem_cache_bridge/external_01/receipt.json"),
        "local_tools": ("Existing venv original encoder definitions and offline local weights used. Wrong resolved base interpreter in author delivery corrected before run; retained correction. Self peak RSS12969394176B differs from sampled tree peak10275667968B. No timeout or repeated encoder.", "work/S68_tum_vmem_cache_bridge/execution_01/receipt.json"),
        "retrieval": ("Actual targeted web primary-method reading of VMem, WorldStereo and Mem-World input camera/reference contracts; latter only verified as preprint. No fresh Gemini needed for exact source input contract. Earlier actual Gemini evidence remains preserved.", "work/S68_tum_vmem_cache_bridge/PRIMARY_SOURCE_INPUT_CONTRACT_REVIEW.md"),
        "agents": ("Separate source author, source reviewer and saved-result/K reviewer. Team-internal138 identity/structure/arithmetic checks are not138 scientific samples or an independent neural reproduction. Root accepted the actual bounded result.", "work/S68_tum_vmem_cache_bridge/INDEPENDENT_RESULT_REVIEW.json"),
        "records": ("S68 pre-run five-source narrowing, argv correction, frozen source, actual receipts, original PNG and cache identities, source/result reviews, conditional-scope finding and next camera interface retained. Current handoff supersedes old pending text without rewriting old experiments.", "RESEARCH_LOG.md")
    }
    for check in record["checks"]:
        if check["item"] in findings:
            check["finding"], check["evidence"] = findings[check["item"]]
    record["corrections"].append("S68 real encoder completion supersedes S67 next-action text. Historical S40 raw run_state is not current pending state. RGB-time cameras, numeric ray alignment and actual get_cond remain unexecuted; no new method or generated video.")

# S69 accepted actual original conditions; S70 remains a source plan only.
s69 = ROOT / "work/S69_tum_camera_conditioning"
if (s69 / "ROOT_FINAL_RESULT_ACCEPTANCE.json").is_file():
    names = ("ROOT_FINAL_RESULT_ACCEPTANCE.json", "SOURCE_REVIEW.json", "external_01/receipt.json", "execution_01/receipt.json", "INDEPENDENT_RESULT_REVIEW.json", "ROOT_PRE_RUN_PREDICTION.md", "GEMINI_OBSERVATION.json", "GEMINI_FACTCHECK.md", "INPUT_CONTRACT_SOURCE_REVIEW.md")
    continuation["s69_actual_two_fixed_conditions"] = {name: {"path": str(s69/name), "sha256": sha256(s69/name)} for name in names}
    result = read_json(s69 / "INDEPENDENT_RESULT_REVIEW.json")
    acceptance = read_json(s69 / "ROOT_FINAL_RESULT_ACCEPTANCE.json")
    verified = result.get("status") == "PASS_S69_INDEPENDENT_CAMERA_CONDITIONING_RESULT_REVIEW" and not result.get("blockers") and acceptance.get("status") == "ACCEPTED_NINE_CAMERAS_AND_TWO_FIXED_CONDITION_ASSEMBLIES_ONLY"
    plan = ROOT / "work/S70_fixed_context_generation/SOURCE_PLAN.md"
    continuation["s70_source_plan"] = {"path": str(plan), "sha256": sha256(plan), "scope": "Source plan only at this check; no S70 program or generation launch asserted."}
    next_step = ("S69 actual nine cameras/two original condition assemblies independently verified. Next implement/review S70 A0/A1/B full50-step sampling+decode using saved conditions, original MultiviewCFG index0 and actual paired RNG evidence; preregister all-four-target RGB score/resources before launch. S70 is a source plan only. Do not rerun S68/S69." if verified else "S69 acceptance/review mismatch: inspect retained evidence before dependent work.")
    record["next_step"] = next_step
    findings = {
        "skills": ("Actual Supervisor Vibe Coding skill/reference and local Claude scientific-critical-thinking read this turn: small source, different-author review, one actual numerical execution and independent saved-result validation; evaluate GT/interpolation/calibration and causal claim limits. No new full idea-evaluator score or Claude model call.", "RESEARCH_PRINCIPLES.md"),
        "innovation": ("Fixed A/B scale27.322040557861328 vs26.265939712524414; prospective common-target direction and moment/scale predictions plus CLIP replacement arithmetic passed. This identifies condition structure only, not scale sensitivity or benefit. S70 first tests complete ordered-reference-set effect, not isolated scale/content/order. NO_METHOD_SELECTED.", "docs/S69_CAMERA_CONDITIONING_RESULT.md"),
        "experiment": ("Six RGB-time cameras interpolated and three saved cameras reused; original two-condition computation external1.363065s return0. Different-author independent log/exp cameras and direct rays returned0 in0.264039s;150 structure/identity checks plus40 numerical comparisons passed, not190 scientific samples. No RGB/depth/weights/new video this stage.", "work/S69_tum_camera_conditioning/INDEPENDENT_RESULT_REVIEW.json"),
        "local_tools": ("Existing CPU8 FP32 Torch2.7.0 with NumPy/SciPy for original conditioning; independent verifier NumPy/SciPy only. Real GT1417998B+five saved caches440740B consumed by worker; output three NPZ39arrays. Root previous readback verified actual complete saved outputs; no repeated encoder or model.", "work/S69_tum_camera_conditioning/ROOT_ACTUAL_RESULT_OBSERVATION.json"),
        "retrieval": ("Actual TUM official optical-camera/approximate-K source check and proactive authorized Gemini3.1 Pro Extended consultation. Actual visible response saved with missing inline formulas disclosed; CameraCtrl official ICLR2025 factchecked. Reject invented depth/warp path, one-repeat variance and pure-content causal claims. Primary source does not prove VMem scale harm.", "work/S69_tum_camera_conditioning/GEMINI_FACTCHECK.md"),
        "agents": ("Separate source author, source/result numerical reviewer and input/Gemini causal-claim reviewer; root read final evidence and accepted. Independent actual verifier reads14,646,332B scientific files, no author numerical function/Torch/model. Team-internal verification, not independent model reproduction.", "work/S69_tum_camera_conditioning/ROOT_FINAL_RESULT_ACCEPTANCE.json"),
        "records": ("Actual start/finish, pre-result predictions, finite source/result review, root acceptance, Gemini source errors and S70 source-only boundary retained in append-only main ledger. Current handoff update and dated snapshot follow accepted report; old failures and no-method status remain.", "RESEARCH_LOG.md")
    }
    for check in record["checks"]:
        if check["item"] in findings:
            check["finding"], check["evidence"] = findings[check["item"]]
    record["corrections"].append("S69 final acceptance supersedes S68 pending-camera/get_cond next step. Historical S40 terminal/pending fields remain old experiment evidence, not the current state; no new generation or innovation validated.")

# S70 real fixed-context continuation. Earlier S40/S69 fields remain historical evidence.
s70 = ROOT / "work/S70_fixed_context_generation"
s70_started_path = s70 / "external_01/started.json"
if s70_started_path.is_file():
    import os

    def latest_complete_jsonl(path):
        if not path.is_file():
            return None
        rows = path.read_bytes().splitlines(keepends=True)
        complete_rows = [line for line in rows if line.endswith(b"\n") and line.strip()]
        return json.loads(complete_rows[-1]) if complete_rows else None

    started = read_json(s70_started_path)
    external_path = s70 / "external_01/receipt.json"
    worker_path = s70 / "execution_01/receipt.json"
    external = read_json(external_path) if external_path.is_file() else None
    worker = read_json(worker_path) if worker_path.is_file() else None
    monitor = latest_complete_jsonl(s70 / "external_01/monitor.jsonl")
    progress = latest_complete_jsonl(s70 / "execution_01/progress.jsonl")
    observed_utc = datetime.now(timezone.utc)
    age = (observed_utc-datetime.fromisoformat(monitor["utc"])).total_seconds() if monitor else None
    try:
        os.kill(started["pid"], 0)
        pid_exists = True
    except ProcessLookupError:
        pid_exists = False
    except PermissionError:
        pid_exists = True  # Existence only, not process ownership or identity proof.
    if external is not None:
        s70_state = ("RETURNED_COMPLETE_AWAITING_RESULT_VALIDATION"
                     if external.get("returncode") == 0 and not external.get("stop_reason")
                     and not external.get("observer_error")
                     and (worker or {}).get("status") == "COMPLETE_THREE_FIXED_GENERATION_ARMS"
                     else "RETURNED_FAILURE_PRESERVED")
    else:
        s70_state = ("RUNNING_OBSERVED" if pid_exists and age is not None and 0 <= age <= 30
                     else "STARTED_WITH_RUNTIME_OBSERVATION_GAP")
    names = ("AUTHOR_DELIVERY.json", "INPUTS.json", "SOURCE_REVIEW.json", "ROOT_SOURCE_DELIVERY.json",
             "SCORING_CONTRACT.json", "ROOT_RUN_BINDING.json", "RGB_VERIFY_AUTHOR_DELIVERY.json",
             "RGB_VERIFY_SOURCE_REVIEW.json", "external_01/started.json", "external_01/receipt.json",
             "execution_01/receipt.json", "INDEPENDENT_RESULT_REVIEW.json",
             "ROOT_FINAL_RESULT_ACCEPTANCE.json", "scoring_01/receipt.json",
             "rgb_verification_01/receipt.json")
    current = dict(observed_utc=observed_utc.isoformat(), state=s70_state,
        evidence={name: {"path": str(s70/name), "sha256": sha256(s70/name)}
                  for name in names if (s70/name).is_file()},
        actual_started_utc=started["started_utc"], pid=started["pid"],
        pid_exists_observation=pid_exists, pid_check_scope="os.kill(pid,0) existence only",
        latest_external_monitor=monitor, latest_worker_progress=progress,
        external_monitor_age_seconds=age, external_returncode=(external or {}).get("returncode"),
        worker_status=(worker or {}).get("status"),
        worker_exact_replay_pass=(worker or {}).get("exact_replay_pass"),
        completed_arms=[name for name, arm in (worker or {}).get("arms", {}).items()
                        if arm.get("status") == "COMPLETE_ARM"],
        check_reads_scope="source and JSON/JSONL metadata only; no weights/NPZ/NPY/PNG bodies",
        science_or_novelty_validated_by_workflow_check=False)
    continuation["s70_live_continuation"] = current
    if "s70_source_plan" in continuation:
        record["historical_s69_s70_plan_snapshot"] = dict(continuation["s70_source_plan"])
        continuation["s70_source_plan"]["scope"] = "Historical source plan; current stage is s70_live_continuation, not unstarted."
    score_path = s70 / "scoring_01/receipt.json"
    verify_path = s70 / "rgb_verification_01/receipt.json"
    score = read_json(score_path) if score_path.is_file() else None
    score_verify = read_json(verify_path) if verify_path.is_file() else None
    current["score_status"] = (score or {}).get("status")
    current["independent_rgb_verification_status"] = (score_verify or {}).get("status")
    if s70_state == "RUNNING_OBSERVED":
        next_step = "Continue the unique already-running S70 A0/A1/B full50-step generation under root's live external observer. Preserve all results/failures; do not duplicate launch. After actual return, independently verify all outputs/shared RNG, then score all four fixed targets and run the independently reviewed integer verifier. No quality or novelty claim before actual results."
    elif s70_state == "STARTED_WITH_RUNTIME_OBSERVATION_GAP":
        next_step = "Inspect the existing S70 external observer and saved progress for the actual observation gap; do not infer completion, restart or duplicate launch. Preserve failures and report the real terminal state."
    elif s70_state == "RETURNED_FAILURE_PRESERVED":
        next_step = "Inspect the actual preserved S70 external/worker failure. Do not retry for a favorable result or call missing arms complete; any repair requires a separately declared future step."
    elif (score_verify or {}).get("status") == "PASS_INDEPENDENT_INTEGER_RGB_SCORE":
        next_step = "S70 score and independent integer verifier are present; root must accept their actual scopes and report the fixed-case sign/replay/limits. Do not infer new method, geometric mechanism or generalization."
    elif (score or {}).get("status") == "COMPLETE_FIXED_RGB_SCORE_PENDING_INDEPENDENT_RECOMPUTE":
        next_step = "S70 fixed score has returned; bind its actual sealed inputs to the reviewed independent integer verifier once, preserve all signs and replay failures, and retain the fixed-case limitations."
    else:
        next_step = "S70 external generation has returned; finish independent generation/RNG/model-state validation before root binds the frozen all-four-target RGB score. Source or workflow PASS alone is not result acceptance."
    record.update(current_stage="S70_FIXED_CONTEXT_GENERATION", current_stage_state=s70_state,
                  trigger="S70 actual live/terminal continuation with preserved historical S40/S69 evidence",
                  next_step=next_step)
    record["corrections"].append("S70 actually started; this current continuation supersedes the historical S69 source-plan-only text. Preserve oldS40/S69 fields and earlier records, but never treat them as current generation readiness/completion. The workflow audit is process compliance, not a new scientific result.")
    findings = {
        "skills": ("Supervisor small-step original-code reuse, different-author source review and bounded actual execution; principlesv2.4/v2.5 apply English-first research, evidence reuse and a dedicated concurrent innovation researcher. No invented user comprehension or model consultation.", "RESEARCH_PRINCIPLES.md"),
        "innovation": ("S70 is a fixed known-sequence ordered-context comparison with A0/A1 exact replay and B; original ft-mse variant, old target exposure, GT cameras and full downstream bundle changes remain explicit. Sign, quality and mechanism are unvalidated while generation runs. NO_METHOD_SELECTED and new_method_validated=false.", "work/S70_fixed_context_generation/SCORING_CONTRACT.json"),
        "experiment": (f"Actual S70 state={s70_state}; started={started['started_utc']}, pid={started['pid']}, latest worker metadata={progress}. Three50-step arms are planned, not presumed complete. Terminal return and different-author generation/RNG review precede any new fixed RGB score. This checker reads metadata only.", "work/S70_fixed_context_generation/external_01/started.json"),
        "local_tools": ("Existing CPU8 FP32 original VMem/sampler0 MultiviewCFG and declared ft-mse VAE route is actually running or terminal as recorded. Root external5520s total/1800s perarm/45GiB/10GiB limits, actual monitor metadata and no duplicate model process; checker does not alter executing sources or load scientific bodies.", "work/S70_fixed_context_generation/external_01/monitor.jsonl"),
        "retrieval": ("Existing S65-S69 primary-source and Gemini evidence reused for the frozen comparison. Dedicated parallel innovation search follows English primary-source/negative-evidence batches under principlesv2.5; this process check does not claim unobserved papers read or convert suggestions into frozen arm changes.", "RESEARCH_PRINCIPLES.md"),
        "agents": ("Separate generator author, primary source/generation-result reviewer, root observer/scorer/executor and dedicated innovation researcher. Generator author separately implemented integer score verification of the root scorer, not an independent neural reproduction. Actual review and execution scopes remain separate.", "work/S70_fixed_context_generation/SOURCE_REVIEW.json"),
        "records": ("S70 readonly source identities, distinct review, prospective fixed four-target scoring contract, root run binding and actual external start/monitor are retained. A backup and create-only update receipt precede this checker update. Existing append behavior records the actual late interval; root separately owns current-entrypoint sync and mainlog edits.", "work/S70_fixed_context_generation/ROOT_RUN_BINDING.json")}
    for check in record["checks"]:
        if check["item"] in findings:
            check["finding"], check["evidence"] = findings[check["item"]]
            if check["item"] == "experiment" and s70_state == "STARTED_WITH_RUNTIME_OBSERVATION_GAP":
                check["status"] = "NEEDS_ATTENTION"
    if s70_state == "STARTED_WITH_RUNTIME_OBSERVATION_GAP":
        record["issues"].append("S70 has a real started receipt but the PID/fresh external-monitor observation is incomplete; inspect root's current observer without duplicating it.")


# Actual S70 result acceptance uses ROOT_RESULT_ACCEPTANCE.json, not the older
# planned ROOT_FINAL_RESULT_ACCEPTANCE filename. Preserve historical records.
s70_accept_path = ROOT / "work/S70_fixed_context_generation/ROOT_RESULT_ACCEPTANCE.json"
if s70_accept_path.is_file():
    accepted = read_json(s70_accept_path)
    s70_root = s70_accept_path.parent
    accepted_pins = accepted.get("files_sha256", {})
    pins_match = bool(accepted_pins) and all(
        (s70_root / name).is_file() and sha256(s70_root / name) == expected
        for name, expected in accepted_pins.items())
    accepted_ok = (pins_match and accepted.get("status") ==
                   "ACCEPTED_S70_INDEPENDENT_GENERATION_AND_FIXED_RGB_SCORE")
    if accepted_ok:
        final_state = "COMPLETE_INDEPENDENTLY_ACCEPTED_FIXED_NEGATIVE_RESULT"
        record.update(current_stage_state=final_state,
            next_step="S70 generation/replay/scoring and independent integer verification are accepted. Preserve the negative fixed result and all images; continue S71 existing-image framing/convention diagnosis and qualified dynamic-baseline preparation, without rerunning S70 or claiming novelty.")
        continuation["s70_live_continuation"].update(state=final_state,
            root_result_acceptance_sha256=sha256(s70_accept_path),
            root_result_acceptance_pins_match=True)
        current_findings = {
            "experiment": "Actual complete3x50-step S70 return0, exactA/A replay, different-author generation verification, fixed all4-target score and independent integer recomputation accepted. This workflow reads only their identity-bound metadata; it is not another scientific validation.",
            "innovation": "Fixed higher-support-A RGB benefit is false: A0/A1 mean0.13116666776908745, B0.12528866263799618; B-A=-0.005878005131091268. Full-bundle effect only; known target exposure, GT/approxK and ft-mse variant retained. No method selected.",
            "records": "Actual ROOT_RESULT_ACCEPTANCE.json pins all completed generation/score verification receipts. Root all16 visual QA and complete report are saved. Historical source-plan and pending states no longer describe current S70 completion."}
        for check in record["checks"]:
            if check["item"] in current_findings:
                check.update(status="PASS", finding=current_findings[check["item"]],
                             evidence=str(s70_accept_path.relative_to(ROOT)))
        record["corrections"].append("Use actual S70 ROOT_RESULT_ACCEPTANCE filename and all its consumed receipt identities; retain prior pending-state report as superseded history.")
    else:
        record["issues"].append("S70 root-result acceptance exists but its expected status or receipt identities do not match; inspect before dependent work.")

# S71 is a completed saved-image diagnostic, not another neural generation.
s71_accept_path = ROOT / "work/S71_s70_framing_diagnosis/ROOT_RESULT_ACCEPTANCE.json"
if s71_accept_path.is_file():
    accepted71 = read_json(s71_accept_path)
    pins71 = accepted71.get("files_sha256", {})
    pins71_match = bool(pins71) and all(
        (s71_accept_path.parent / name).is_file()
        and sha256(s71_accept_path.parent / name) == expected
        for name, expected in pins71.items())
    ok71 = (pins71_match and accepted71.get("status") ==
            "ACCEPTED_S71_DESCRIPTIVE_DISPLACEMENT_ARITHMETIC_ONLY"
            and accepted71.get("new_method_validated") is False)
    if ok71:
        next_step = "S71 saved-image diagnostic and independent coordinate arithmetic accepted. Next qualify fixed requested-geometry checks on real history19 to all real targets20-23 before generated-image comparisons; retain approximate K/distortion, insufficient matches and non-identifiability. No S70 rerun or novelty claim."
        record.update(current_stage="S71_SAVED_IMAGE_FRAMING_DIAGNOSIS",
            current_stage_state="COMPLETE_INDEPENDENT_COORDINATE_ARITHMETIC_ACCEPTED",
            trigger="S71 accepted existing-image analysis; prior generation fields remain historical",
            next_step=next_step)
        continuation["s71_accepted_diagnostic"] = dict(
            acceptance_sha256=sha256(s71_accept_path), receipt_pins_match=True,
            scope=accepted71.get("scope"), new_method_validated=False)
        findings71 = {
            "experiment": "One actual1.456041s existing16-PNG analysis,12pairs retained and4zero-repeat controls; target23both insufficient. Different-author0.074828s saved-coordinate arithmetic305checks passed, not305 scientific samples. No new model generation or physical camera estimate.",
            "innovation": "Local feature displacement increases on targets20-22, but target23sparse matches include suspected errors. Arithmetic does not establish correspondence truth, camera compliance or cause. Input calibration, declared VAE variant, domain and learned compliance remain competing explanations. NO_METHOD_SELECTED.",
            "retrieval": "Three bounded English primary-source batches checked VMem/SEVA competing explanations, camera-metric identifiability and official TUM fr1 calibration. Low epipolar residual alone cannot prove full camera correctness; first qualify the observer on real photographs.",
            "agents": "Dedicated primary-source innovation researcher plus separate interface auditor and saved-coordinate numerical verifier completed bounded tasks. Root accepted final handoffs and viewed all8 diagnostic panels; no claim of continued idle agent work.",
            "records": "S71 frozen contract/source, actual run, independent scalar arithmetic, root acceptance and all8-panel visual QA are retained. Root pass/passed wrapper error and empty visual output directory preserved; no scientific rerun. Current entrypoints and user report synchronized separately."}
        for check in record["checks"]:
            if check["item"] in findings71:
                check.update(status="PASS", finding=findings71[check["item"]],
                             evidence=str(s71_accept_path.relative_to(ROOT)))
        record["corrections"].append("S71 actual accepted diagnostic supersedes earlier planned S71 next steps; S70 negative result remains unchanged. This metadata workflow check is not independent scientific validation.")
    else:
        record["issues"].append("S71 acceptance status or pinned evidence mismatch; inspect retained files before dependent work.")

# S72 accepted real-photo observer qualification supersedes planned real controls.
s72_path = ROOT / "work/S72_fixed_requested_geometry/ROOT_RESULT_ACCEPTANCE.json"
if s72_path.is_file():
    s72 = read_json(s72_path)
    s72_pins = s72.get("files_sha256", {})
    s72_ok = (s72.get("status") == "ACCEPTED_S72_REAL_CONTROL_ARITHMETIC_ONLY"
        and s72.get("new_method_validated") is False and bool(s72_pins)
        and all((s72_path.parent / name).is_file()
            and sha256(s72_path.parent / name) == value for name, value in s72_pins.items()))
    if s72_ok:
        next_step = "S72 real controls and independent arithmetic complete. Next frozen existing A0/B-target comparison with same anchor19 and requested geometry, reporting match availability as well as residuals; common-anchor intersection is secondary conditioned analysis. Preserve all4 targets, outlier tails, fr2 correction and NO_METHOD_SELECTED."
        record.update(current_stage="S72_REAL_PHOTO_FIXED_REQUESTED_GEOMETRY",
            current_stage_state="COMPLETE_INDEPENDENT_REAL_CONTROL_ARITHMETIC_ACCEPTED",
            trigger="S72 actual real-control completion; older S70/S71 states historical",
            next_step=next_step)
        continuation["s72_accepted_real_controls"] = dict(
            acceptance_sha256=sha256(s72_path), receipt_pins_match=True,
            new_method_validated=False, camera_correctness_validated=False)
        s72_findings = {
            "skills": "Supervisor small frozen step and different-author review; local Claude scientific critical thinking applied to construct validity/selection; handbook2.3 tests hidden assumptions; figure-designer supports actual4panel visual evidence. No user attestation invented.",
            "experiment": "Actual1.955583s real5PNG run,4pairs638matches retained; independent0.140874s rederivation125checks passed. No new neural model/weights/generated-target comparison. All4panel figure viewed. Target23p95=121.102955px and16percentabove10px retained; notcameraPASS.",
            "innovation": "Real controls have finite modest medians but substantial tails. Ordinary fixed-F geometry/availability/paired-support controls are not new methods. Output fitted-F consistency plus nonstaticness cannot alone certify requested motion. NO_METHOD_SELECTED.",
            "local_tools": "Existing CPU8FP32 original image helper path plus SIFT/NumPy; anchor tensor exactly matches acceptedS68. Independent scalar world-ray triple products from original camera/K fields. V1cv2area variant corrected before any run and retained unexecuted.",
            "retrieval": "Actual S69 data paths arefr2_desk; officialfr2K/distortion checked and priorfr1 applicability corrected. Four bounded dedicated source/method/public-metric/selection batches, including exact public commit3eba6273ab60faf1b28dad524c10123fe94111e3; paper/code scopes distinct.",
            "agents": "Initial innovation scout usage-limit failure preserved; a different scout completed4bounded batches, another author audited source and independently recomputed geometry. Agents stopped after final delivery, not claimed continuously running during idle time.",
            "records": "S72 frozenv1/v2source, pre-run correction, actual runtime, different-author scalar review, root finalacceptance and4panelQA plus S71fr2errata saved. Actual long workflow gaps retained, no timer reset or fictional work time."}
        for check in record["checks"]:
            if check["item"] in s72_findings:
                check.update(status="PASS", finding=s72_findings[check["item"]], evidence=str(s72_path.relative_to(ROOT)))
        record["corrections"].append("S72 real-control result accepted, not generated-camera or new-method validation. Previous S71 planned real controls and fr1 applicability text superseded.")
    else:
        record["issues"].append("S72 result acceptance status or pinned evidence mismatch; inspect before dependent work.")

# S73 accepted saved-image arithmetic; no additional neural generation.
s73_path = ROOT / "work/S73_generated_fixed_geometry/ROOT_RESULT_ACCEPTANCE.json"
if s73_path.is_file():
    s73 = read_json(s73_path)
    s73_pins = s73.get("files_sha256", {})
    s73_ok = (s73.get("status") == "ACCEPTED_S73_EXISTING_IMAGE_ARITHMETIC_ONLY"
        and s73.get("new_method_validated") is False and bool(s73_pins)
        and all((s73_path.parent / name).is_file()
            and sha256(s73_path.parent / name) == value for name, value in s73_pins.items()))
    if s73_ok:
        next_step = "S73 saved-image geometry/support analysis accepted. Freeze one real-match wrong-pose-label sensitivity control (20/23,21/22) with sign-invariant normalized-F separation; preserve all matches, no fitting, rematching or favorable permutation selection. Then choose the smallest comparison that separates generator failure explanations; no S70-S73 rerun or novelty claim."
        record.update(current_stage="S73_EXISTING_GENERATED_FIXED_GEOMETRY",
            current_stage_state="COMPLETE_INDEPENDENT_EXISTING_IMAGE_ARITHMETIC_ACCEPTED",
            trigger="S73 saved-image analysis accepted; earlier stages historical", next_step=next_step)
        continuation["s73_accepted_existing_image_comparison"] = dict(
            acceptance_sha256=sha256(s73_path), receipt_pins_match=True,
            new_method_validated=False, generated_camera_validated=False)
        s73_findings = {
            "skills": "Supervisor small frozen step and different-author audit; local Claude scientific critical thinking for matching selection/construct validity; figure-designer for all12 saved rows. No private user attestation claimed.",
            "experiment": "Actual corrected worker1.062418s return0,9oldPNG4075371B;8generated rows1150matches plus4reused real rows638. Independent309arithmetic checks from original cameras/K and savedxy passed. Common support92/48/6/0; both all4eventsUNKNOWN, not success. Zero new neural models.",
            "innovation": "Existing correspondences disagree with requested geometry but matching/calibration/shape/camera causes not isolated. EgoSim/GEN3C/VIVID already implement key geometry/masking/soft-attention ingredients. Calibrated unknown handling remains a question, not selected method. NO_METHOD_SELECTED.",
            "local_tools": "Existing SIFT NumPy environment and independent scalar world-ray arithmetic; Matplotlib3.10.6 NumPy2.3.5 only for saved-statistic SVG/PNG. Root visually inspected complete figure. No new weights or image synthesis.",
            "retrieval": "Dedicated bounded English primary-source batches: CameraCtrl real error floor, fixed-F identifiability, EgoSim/GEN3C/VIVID mechanisms and pinned apple/ml-vivid source, redundancy prior. Formal venue/version and code-reading boundaries retained; not model validation.",
            "agents": "Dedicated innovation scout advanced finite source questions alongside a different author doing exact source and independent scalar result verification. Root performed actual run and synthesis. Completed batches recorded; no claim agents run during idle task time.",
            "records": "S73 frozen contract, first wrong-interpreter import failure with0scientificreads, corrected v2output namespace, actual external argv/time, all12rows, independent review, root acceptance and figure QA retained. Old current-status body backed up before concise refresh."}
        for check in record["checks"]:
            if check["item"] in s73_findings:
                check.update(status="PASS", finding=s73_findings[check["item"]], evidence=str(s73_path.relative_to(ROOT)))
        record["corrections"].append("S73 complete saved-image analysis supersedes planned generated-target comparison; both shared-support all4events remainUNKNOWN. No new method or neural generation.")
    else:
        record["issues"].append("S73 acceptance status or pinned evidence mismatch; inspect before dependent work.")

# S74 sensitivity and S75 decoder-only completion, separately scoped.
s74_path = ROOT / "work/S74_wrong_pose_control/ROOT_RESULT_ACCEPTANCE.json"
s75_dir = ROOT / "work/S75_vae_history_roundtrip"
if s74_path.is_file():
    s74 = read_json(s74_path)
    valid = s74.get("status") == "ACCEPTED_S74_FIXED_WRONG_LABEL_ARITHMETIC_ONLY" and bool(s74.get("files_sha256"))
    valid = valid and all(sha256(s74_path.parent / n) == h for n, h in s74.get("files_sha256", {}).items())
    if valid:
        record.update(current_stage="S74_FIXED_WRONG_LABEL_SENSITIVITY", current_stage_state="COMPLETE_INDEPENDENT_ARITHMETIC_ACCEPTED")
        next_step = "Accept S75 five-history decoder-only results; then freeze a target-camera relative-response pilot. S74 sensitivity does not change S73 UNKNOWN or establish a new method."
        record["next_step"] = next_step
        continuation["s74"] = dict(acceptance_sha256=sha256(s74_path), all4_wrong_label_sensitivity=True, s73_events="UNKNOWN")
    else:
        record["issues"].append("S74 acceptance pins/status mismatch")
s75_receipt_path = s75_dir / "execution_01/receipt.json"
if s75_receipt_path.is_file():
    s75 = read_json(s75_receipt_path)
    if s75.get("status") == "COMPLETE_FIVE_HISTORY_VAE_ROUNDTRIP":
        accepted_path = s75_dir / "ROOT_RESULT_ACCEPTANCE.json"
        accepted = read_json(accepted_path) if accepted_path.is_file() else {}
        accepted_ok = (accepted.get("status") == "ACCEPTED_S75_FIVE_REAL_HISTORY_DECODER_ARITHMETIC_ONLY" and bool(accepted.get("files_sha256"))
            and all(sha256(s75_dir / n) == h for n,h in accepted.get("files_sha256", {}).items()))
        record.update(current_stage="S75_FIVE_REAL_HISTORY_DECODER_ONLY", current_stage_state="COMPLETE_INDEPENDENT_ARITHMETIC_ACCEPTED" if accepted_ok else "MODEL_COMPLETED_INDEPENDENT_REVIEW_PENDING")
        next_step = "Prepare frozen relative camera-response pilot without rerunning successful baseline; exact old A0 RNG reuse must be verified. No method selected." if accepted_ok else "Independently recompute saved S75 FP32 errors and coordinates, visually inspect all five photo pairs, and record limits before acceptance."
        record["next_step"] = next_step
        findings = {
            "skills": "Supervisor frozen smallest experiment and different-author verification; local Claude scientific-critical-thinking for selection and construct validity; idea-evaluator fatal-flaws for novelty limits.",
            "experiment": "S74 same638 real matches, one fixed wrong-label swap, all4 paired medians positive; independent146 checks. S75 actual one VAE load/five history decodes, zero new encode/CLIP/VMem/sampling calls. S75 independent status recorded separately. Neither experiment proves generated camera correctness.",
            "innovation": "NO_METHOD_SELECTED. Relative camera-response is a next falsifiable question, not novel method. S73 both all4events UNKNOWN retained; component roundtrip does not establish generated-latent compatibility.",
            "local_tools": "Lexical local Python environment, CPU8 FP32 decoder with observed elapsed/RSS and original preprocessing; S75 review acceptance is separately recorded. Consult docs/HARNESS_GUIDE.md for tool setup; this workflow check does not inspect model credentials or imply external model access.",
            "retrieval": "Dedicated bounded English original-source batches: CamVerse, official ICLR2026 TTM and official ft-mse card. Decoder-only fine-tuning narrows coordinate-mismatch story; exact SD2.1 VAE identity remains unknown. Gemini tab readable but no new prompt sent because documented interaction methods were not returned.",
            "agents": "Dedicated innovation scout active alongside independent S75 arithmetic verifier and local harness capability discovery; root ran model and synthesizes. Finite batch limits and completion are explicit.",
            "records": "Frozen S74/S75 sources, source reviews, actual external starts/finishes, per-history arrays/PNGs and receipts preserved. Root metadata wrapper pass/pass_ error retained, no scientific rerun. Workflow cadence records actual elapsed time including delay."}
        for check in record["checks"]:
            if check["item"] in findings:
                check.update(status="PASS", finding=findings[check["item"]], evidence=str(s75_receipt_path.relative_to(ROOT)))
        continuation["s75"] = dict(receipt_sha256=sha256(s75_receipt_path), independent_accepted=accepted_ok, new_method_validated=False)
        record["corrections"].append("S74 complete, S75 decoder execution complete; S75 review status explicit. Does not change S73 UNKNOWN or original SD2.1 identity UNKNOWN.")


# S76 current actual observation; no models or scientific array bodies read.
s76_dir = ROOT / "work/S76_relative_camera_response"
s76_start_path = s76_dir / "external_01/started.json"
if s76_start_path.is_file():
    import os
    import subprocess

    s76_read_errors = []
    def s76_json(path):
        if not path.is_file():
            return None
        try:
            return read_json(path)
        except (OSError, ValueError) as error:
            s76_read_errors.append(str(path.relative_to(ROOT)) + ": " + type(error).__name__)
            return None

    s76_start = s76_json(s76_start_path) or {}
    s76_external = s76_json(s76_dir / "external_01/receipt.json")
    s76_worker = s76_json(s76_dir / "execution_01/receipt.json")
    s76_score = s76_json(s76_dir / "scoring_01/receipt.json")
    # Existing helper retains only complete JSONL lines; S76 depends on accepted S70.
    s76_monitor = latest_complete_jsonl(s76_dir / "external_01/monitor.jsonl")
    s76_progress = latest_complete_jsonl(s76_dir / "execution_01/progress.jsonl")
    s76_observed = datetime.now(timezone.utc)
    s76_age = ((s76_observed - datetime.fromisoformat(s76_monitor["utc"])).total_seconds()
               if s76_monitor else None)
    s76_pid = s76_start.get("pid")
    s76_process_matches = False
    s76_process_note = "No valid worker PID"
    if isinstance(s76_pid, int) and s76_pid > 0:
        try:
            os.kill(s76_pid, 0)
            command = subprocess.run(["/bin/ps", "-p", str(s76_pid), "-o", "command="],
                                     capture_output=True, text=True, timeout=2, check=False)
            # Existence plus expected worker/contract argv, not a process-birth proof.
            expected_argv = s76_start.get("argv", [])
            s76_process_matches = (command.returncode == 0 and len(expected_argv) == 4
                and expected_argv[2] == str(s76_dir / "run_single_yaw.py")
                and expected_argv[2] in command.stdout and expected_argv[3] in command.stdout)
            s76_process_note = "os.kill(pid, 0) plus ps worker path/contract argv observation"
        except (OSError, subprocess.SubprocessError) as error:
            s76_process_note = type(error).__name__
    s76_generation_complete = (bool(s76_worker)
        and s76_worker.get("status") == "COMPLETE_SINGLE_YAW_FIXED_STREAM"
        and s76_worker.get("stream_identity_pass") is True
        and s76_worker.get("model_unchanged") is True
        and s76_worker.get("all4_targets_preserved") is True)
    if s76_read_errors:
        s76_state = "METADATA_OBSERVATION_GAP"
    elif s76_external is not None:
        if (s76_external.get("returncode") != 0 or s76_external.get("stop_reason") is not None
                or s76_external.get("observer_error") is not None):
            s76_state = "RETURNED_FAILURE_PRESERVED"
        elif not s76_generation_complete:
            s76_state = "RETURNED_INCOMPLETE_METADATA_REQUIRES_INSPECTION"
        elif (s76_score or {}).get("status") == "COMPLETE_SAVED_YAW_DIRECTION_DIAGNOSTIC":
            s76_state = "SCORE_RETURNED_INDEPENDENT_REVIEW_PENDING"
        elif (s76_score or {}).get("status") == "FAILED":
            s76_state = "SCORE_FAILED_PRESERVED"
        else:
            s76_state = "GENERATION_RETURNED_RESULT_REVIEW_PENDING"
    else:
        s76_live = (s76_process_matches and s76_age is not None and 0 <= s76_age <= 30
                    and s76_pid in (s76_monitor or {}).get("pids", []))
        s76_state = "RUNNING_OBSERVED" if s76_live else "STARTED_WITH_RUNTIME_OBSERVATION_GAP"
    s76_needs_attention = ("GAP" in s76_state or "FAIL" in s76_state or "INCOMPLETE" in s76_state)
    if s76_state == "RUNNING_OBSERVED":
        next_step = "Observe the unique existing S76 +5-degree target-yaw arm under its 1h/45GiB sampled RSS/10GiB free-disk observer. Do not launch another model or rerun A0. After terminal return, verify actual stream/model/condition evidence before the frozen all-four-target score."
    elif s76_needs_attention:
        next_step = "Inspect the saved S76 observer/worker/scorer metadata and the actual process observation. Preserve incomplete or failed outputs; do not infer completion or automatically retry."
    else:
        next_step = "S76 actual execution/scoring stage is recorded, with no scientific acceptance inferred. Root performs appropriate independent saved-evidence review, and runs the frozen score only if generation comparison checks pass; preserve all four targets, missing support and null events."
    record.update(current_stage="S76_RELATIVE_CAMERA_RESPONSE", current_stage_state=s76_state,
                  trigger="Actual S76 live/terminal metadata supersedes completed S75 follow-up plans", next_step=next_step)
    continuation["s76_live_continuation"] = dict(observed_utc=s76_observed.isoformat(), state=s76_state,
        pid=s76_pid, process_matches_observation=s76_process_matches, process_check_scope=s76_process_note,
        actual_started_utc=s76_start.get("started_utc"), monitor_age_seconds=s76_age,
        latest_external_monitor=s76_monitor, latest_worker_progress=s76_progress,
        external_returncode=(s76_external or {}).get("returncode"),
        stop_reason=(s76_external or {}).get("stop_reason"),
        worker_status=(s76_worker or {}).get("status"), score_status=(s76_score or {}).get("status"),
        metadata_read_errors=s76_read_errors, science_or_novelty_validated_by_workflow_check=False)
    s76_findings = {
        "skills": "Supervisor bounded failure-driven comparison and different-author source review; fixed H/noise/selection limits retained. This metadata checker does not add scientific validation.",
        "experiment": f"Actual S76 observed state={s76_state}; one new target-yaw arm and reused accepted S70 A0. External/worker/scorer statuses are recorded separately, not inferred from source PASS.",
        "innovation": "NO_METHOD_SELECTED. Fixed-image-grid noise is an exogenous-input diagnostic, not exact H-equivariance. Full-system camera consumers vary together; one scene/four coupled targets do not establish a method or resolve S73 UNKNOWN.",
        "local_tools": "Existing CPU8 FP32 VMem/sampler/VAE plus fixed old RNG and resource observer. S75 decoder QA/acceptance is historical. DeepSeek setup/model availability is separate; use docs/HARNESS_GUIDE.md, never inspect private state here.",
        "retrieval": "Frozen S76 protocol cites reused primary-source camera/noise counterevidence. This audit makes no claim of a new search batch or Gemini/DeepSeek model call.",
        "agents": "S76 source author and different-author source reviewer delivered bounded artifacts; root owns actual launch and subsequent result acceptance. Do not infer current agent activity from older S75 descriptions.",
        "records": "Actual S76 started/progress and available external, worker and scorer JSON receipts are preserved separately. This check reads metadata only, keeps the actual cadence interval, and does not trigger a duplicate experiment."}
    for check in record["checks"]:
        if check["item"] in s76_findings:
            check.update(status="NEEDS_ATTENTION" if check["item"] == "experiment" and s76_needs_attention else "PASS",
                         finding=s76_findings[check["item"]], evidence=str(s76_start_path.relative_to(ROOT)))
    if s76_needs_attention:
        record["issues"].append("S76 current observation requires inspection: " + s76_state)
    record["corrections"].append("S76 real start supersedes S75's planned-pilot/harness-discovery wording; historical S74/S75 results are retained. Running, returned, scored and scientifically accepted are distinct.")

with target.open("a+", encoding="utf-8") as handle:
    fcntl.flock(handle, fcntl.LOCK_EX)
    handle.seek(0)
    current = [json.loads(line) for line in handle if line.strip()]
    if not current or current[-1].get("checked_utc") != previous_raw:
        raise RuntimeError("Workflow ledger changed before append")
    handle.seek(0, 2)
    handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    handle.flush()
    fcntl.flock(handle, fcntl.LOCK_UN)

event_id = "s40-live-workflow-check-" + now.strftime("%Y%m%dT%H%M%S%fZ")
append_event(
    "科研流程七项实查完成",
    f"实际间隔{interval:.6f}分钟；七项流程已检查。当前阶段{record.get('current_stage', 'HISTORICAL_S40_CHAIN')}、实际状态{record.get('current_stage_state', state)}。S40历史原始状态{state}、完成批次{latest['completed_batches']}保留；流程检查不解释为生成完成、画质收益或创新。",
    evidence=["workflow_checks.jsonl", "work/S40_declared_variant_generation/execution_01/monitor.jsonl", "work/S40_declared_variant_generation/execution_01/full_resource_gate.json"] + (["work/S70_fixed_context_generation/external_01/started.json", "work/S70_fixed_context_generation/external_01/monitor.jsonl"] if s70_started_path.is_file() else []),
    next_step=next_step,
    occurred_at=now.isoformat(),
    time_source="Actual current clock and current-stage JSON/JSONL observations; S40 monitor/terminal fields remain historical",
    event_id=event_id,
)

print(json.dumps({"status": "RECORDED", "checked_utc": now.isoformat(), "interval_minutes": interval, "run_state": state, "current_stage": record.get("current_stage"), "current_stage_state": record.get("current_stage_state")}, ensure_ascii=False))
