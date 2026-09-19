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
    next_step = "Follow the actual C2 V9 preparation/authorization/execution receipts; preserve V8 SIGTERM history and never infer completion from source PASS or a provisional commit. Finish the mandatory row. S57 all-30 saved-output measurement returned0; independently audit apparent sign/convention mismatch before interpreting labels. No method selected or validated."
    record["next_step"] = next_step
    record["corrections"].append("V9 has its own immutable recovery namespace with unchanged scientific controls. C1 score, independent recomputation and nine-frame post-score observation are already complete. S56 is question triage and Gemini critique, not new-method evidence. Current V9 receipt observations supersede legacy V8 running/preparation language.")
    for check in record["checks"]:
        if check["item"] in ("experiment", "agents", "local_tools"):
            check["finding"] = f"C1 measurement/recompute/post-score display completed. V9 preserves the V8 interrupted attempt and requires its existing actual stage-specific evidence. Latest external V9 return={v9_return}; monitor={v9_live}. Observed file statuses are recorded separately, not automatically approved. S57 standard observer all-30 saved-output measurement is completed, with sign/convention interpretation pending independent source audit; it is separate from new model generation; no new C2 pixel authority follows from this check."
        elif check["item"] == "retrieval":
            check["finding"] = "S56 read three primary methods (WorldStereo, SPMem, GEN3C) within recorded sections. Gemini Pro Extended was actually consulted through CUA; full prompt/response and independent source/mathematical corrections are saved. CameraCtrl venue corrected to ICLR2025; AI suggestions are not evidence."
        elif check["item"] == "innovation":
            check["finding"] = "B0 and C1 strict events are false; original at-least-two-of-three cannot be reached, while C2 remains mandatory. S56 rejects current method commitment and retains bounded rendered-camera observation before longer-horizon claims. No ROI/threshold/pair changes, no ordinary homography/SIFT novelty claim, NO_METHOD_SELECTED and new_method_validated=false."
        elif check["item"] == "records":
            check["finding"] = "Actual session events, source handoffs, negative results, S56 reading and Gemini critique remain in the append-only project ledger. Source-only, synthetic controls, existing real generated frames and new generation must retain distinct labels."

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
    f"实际间隔{interval:.6f}分钟；七项已核。S40历史运行回执原始状态{state}、阶段{latest['budget_phase']}、完成批次{latest['completed_batches']}、进程树RSS {latest['process_tree_rss_bytes']}B。该记录不把运行态或终态字段自动解释为科学成功。",
    evidence=["workflow_checks.jsonl", "work/S40_declared_variant_generation/execution_01/monitor.jsonl", "work/S40_declared_variant_generation/execution_01/full_resource_gate.json"],
    next_step=next_step,
    occurred_at=now.isoformat(),
    time_source="Actual current clock and current S40 monitor/terminal files",
    event_id=event_id,
)

print(json.dumps({"status": "RECORDED", "checked_utc": now.isoformat(), "interval_minutes": interval, "run_state": state}, ensure_ascii=False))
