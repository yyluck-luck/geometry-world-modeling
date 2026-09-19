#!/usr/bin/env python3
"""Append the 30-minute workflow audit while the unique S40 run is active."""

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

PREVIOUS = datetime.fromisoformat("2026-09-07T10:56:31.979755+00:00")
TARGET = PREVIOUS.timestamp() + 30 * 60
EXPECTED = {
    "manifest": "9951a78909a7d792dd536cea067c14e369cff776115a078d2f61c66c085cdebe",
    "source_review": "e7d23041d32f748ea2cf0e27b2a08c35b92c4400e0ecbcbeb28545d70c5bb9d1",
    "runtime_review": "33681baf8cf68b8f58010ba8b24aa7dbb036494ccb28ab8e7b30facdb8e2cdff",
    "launch_ticket": "ccebc0daec5b532f3afefcfb76933cf32d1701242c9075ba695e5882e810776c",
    "full_gate": "5a23262c01c2e777721b9c320b4344e26be3f20ef991836b0e53035dfb090948",
}


def sha256(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


paths = {
    "manifest": ROOT / "work/S40_declared_variant_generation/review_attachment_01/manifest.json",
    "source_review": ROOT / "work/S40_declared_variant_generation/freeze_attempt_01/source_core_review.json",
    "runtime_review": ROOT / "work/S40_declared_variant_generation/freeze_attempt_01/runtime_freeze_review.json",
    "launch_ticket": ROOT / "work/S40_declared_variant_generation/execution_01/launch_ticket.json",
    "full_gate": ROOT / "work/S40_declared_variant_generation/execution_01/full_resource_gate.json",
}
actual = {name: sha256(path) for name, path in paths.items()}
if actual != EXPECTED:
    raise RuntimeError("Frozen S40 identities changed")
if read_json(paths["source_review"]).get("status") != "PASS_S40_GENERATION_SOURCE_REVIEW":
    raise RuntimeError("S40 actual-core source review is not PASS")
if read_json(paths["runtime_review"]).get("status") != "READY_TO_ATTEMPT_S40_DECLARED_GENERATION":
    raise RuntimeError("S40 actual-core runtime review is not ready")
if read_json(paths["full_gate"]).get("status") != "PASS_DECLARED_GENERATION_RESOURCE_GATE":
    raise RuntimeError("S40 full resource gate is not PASS")

now = datetime.now(timezone.utc)
if now.timestamp() < TARGET:
    raise RuntimeError("30-minute target has not arrived")
interval = (now - PREVIOUS).total_seconds() / 60.0

execution = ROOT / "work/S40_declared_variant_generation/execution_01"
monitor_lines = [line for line in (execution / "monitor.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
if not monitor_lines:
    raise RuntimeError("S40 monitor is empty")
latest = json.loads(monitor_lines[-1])
monitor_age = (now - datetime.fromisoformat(latest["utc"])).total_seconds()
terminal_path = execution / "receipt.json"
terminal = read_json(terminal_path) if terminal_path.exists() else None
run_state = terminal.get("status") if terminal else "RUNNING"
if terminal is None:
    if monitor_age > 30 or latest["process_tree_rss_bytes"] > 45 * 1024**3 or latest["disk_free_bytes"] < 10 * 1024**3:
        raise RuntimeError("Live S40 monitor is stale or outside its resource contract")

record = {
    "schema": "research-workflow-check-v1",
    "checked_utc": now.isoformat(),
    "checked_local": now.astimezone(ZoneInfo("Asia/Shanghai")).isoformat(),
    "previous_checked_utc": PREVIOUS.isoformat(),
    "interval_minutes": interval,
    "trigger": "Actual S40 two-batch baseline execution",
    "checks": [
        {"item": "skills", "status": "PASS", "finding": "Applied the Supervisor freeze-before-run and strong-baseline-first sequence, plus local scientific peer-review and statistical evidence boundaries. Two blocking source reviews were retained and repaired before execution.", "evidence": "work/S40_declared_variant_generation/freeze_tool_source_review_incremental_v3.json"},
        {"item": "innovation", "status": "PASS", "finding": "The active run is a declared-variant baseline. It is not labelled as a new method; source-to-region addressability remains conditional on a natural failure and later replay intervention.", "evidence": "work/S42_h1_instrumentation_feasibility/REPORT.md"},
        {"item": "experiment", "status": "PASS", "finding": "The exact manifest received two different-author actual-core reviews, metadata gate and a fresh full five-component resource gate before one worker began. Runtime limits and the actual live/terminal state are recorded.", "evidence": "work/S40_declared_variant_generation/execution_01/monitor.jsonl"},
        {"item": "local_tools", "status": "PASS", "finding": "The reviewed local launcher, process-tree monitor, source/hash gates and immutable trace/archive are active. A bounded readback supervisor is being implemented separately and is not being run early.", "evidence": "work/S40_declared_variant_generation/execution_01/launch_ticket.json"},
        {"item": "retrieval", "status": "NOT_APPLICABLE", "finding": "This interval executes the already frozen baseline; no new literature claim or candidate mechanism was introduced, so repeating search would not change the execution decision.", "evidence": "work/S42_causal_memory_gap_search/sources.json"},
        {"item": "agents", "status": "PASS", "finding": "Different agents reviewed the actual S40 source core and runtime core; independent agents are now auditing the future saved-result readback wrapper while root alone owns the live generation session.", "evidence": "work/S40_declared_variant_generation/freeze_attempt_01/runtime_freeze_review.json"},
        {"item": "records", "status": "PASS", "finding": "Core freeze, dual review, attachment, metadata gate, generation start, and the actual running observation are appended with real timestamps. RUNNING is not reported as success.", "evidence": "RESEARCH_LOG.md"},
    ],
    "issues": [
        f"Actual interval is {interval:.6f} minutes and is recorded without backdating.",
        "S40 remains unreviewed as a generated result until terminal evidence and readback independently pass.",
        "The exact original SD2.1 VAE identity remains unknown; this is the declared ft-mse component variant.",
        "No natural failure, causal effect, improvement, novelty, or submission claim is established.",
    ],
    "corrections": [
        "A missing outer readback resource supervisor was identified before readback and is being implemented/reviewed without touching the active run.",
    ],
    "new_method_validated": False,
    "next_step": "Continue only the same S40 process to a terminal receipt; then independently audit terminal artifacts and run readback only through its reviewed CPU1/300s/2GiB supervisor.",
    "runtime_observation": {
        "state": run_state,
        "latest_monitor_utc": latest["utc"],
        "monitor_age_seconds": monitor_age,
        "elapsed_seconds": latest["elapsed_seconds"],
        "budget_phase": latest["budget_phase"],
        "completed_batches": latest["completed_batches"],
        "process_tree_rss_bytes": latest["process_tree_rss_bytes"],
        "disk_free_bytes": latest["disk_free_bytes"],
        "trace_sequence_count": latest["trace_sequence_count"],
        "manifest_sha256": actual["manifest"],
        "launch_ticket_sha256": actual["launch_ticket"],
        "full_resource_gate_sha256": actual["full_gate"],
    },
}

target = ROOT / "workflow_checks.jsonl"
with target.open("a+", encoding="utf-8") as handle:
    fcntl.flock(handle, fcntl.LOCK_EX)
    handle.seek(0)
    prior = [json.loads(line) for line in handle if line.strip()]
    if not prior or prior[-1].get("checked_utc") != PREVIOUS.isoformat():
        raise RuntimeError("Unexpected previous workflow check")
    handle.seek(0, 2)
    handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    handle.flush()
    fcntl.flock(handle, fcntl.LOCK_UN)

append_event(
    "S42 科研流程七项实查完成",
    f"实际间隔{interval:.6f}分钟。已核skills、创新边界、真实实验、工具、检索适用性、多agent与记录；S40实际状态为{run_state}，完成批次{latest['completed_batches']}，进程树RSS {latest['process_tree_rss_bytes']}B。未把运行中状态当成功。",
    evidence=["workflow_checks.jsonl", "work/S40_declared_variant_generation/execution_01/monitor.jsonl", "work/S40_declared_variant_generation/execution_01/full_resource_gate.json"],
    next_step=record["next_step"],
    occurred_at=now.isoformat(),
    time_source="Actual current clock and live S40 monitor/terminal receipt",
    event_id="s42-workflow-check-20260907T1126Z",
)

print(json.dumps({"status": "RECORDED", "checked_utc": now.isoformat(), "interval_minutes": interval, "run_state": run_state}, ensure_ascii=False))
