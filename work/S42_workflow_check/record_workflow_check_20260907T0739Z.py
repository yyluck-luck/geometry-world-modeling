#!/usr/bin/env python3
"""Append the post-interruption 30-minute research-workflow audit."""

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

PREVIOUS = datetime.fromisoformat("2026-09-07T06:56:37.093157+00:00")
TARGET = PREVIOUS.timestamp() + 30 * 60
EXPECTED = {
    "loading_review": "5707a2ca8e300084a7371b8979b046cdab1021d63409de155a61db53f246da5a",
    "freeze_review_v1": "1338179c9475cd46f14755b9f1f19b37670e61e327116878490d0b229cacf302",
    "freeze_review_v2": "f8ef9ccee6a11d846f4f3a2c1df85952197e2e13a22044339e7988eba3e9ae89",
    "freeze_tool": "752830d25cb9e11e943aff583fd72a6db44eb9f7114871b16c0a833148779aa9",
    "freeze_protocol": "77c84b89b284f5c87535b164e4f29479759265adb3919f5f7e8038bf57da2d58",
}


def sha256(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


paths = {
    "loading_review": ROOT / "work/S39_component_variant/loading_attempt_01/independent_loading_evidence_review.json",
    "freeze_review_v1": ROOT / "work/S40_declared_variant_generation/freeze_tool_source_review.json",
    "freeze_review_v2": ROOT / "work/S40_declared_variant_generation/freeze_tool_source_review_incremental_v2.json",
    "freeze_tool": ROOT / "work/S40_declared_variant_generation/freeze_s40_manifest.py",
    "freeze_protocol": ROOT / "work/S40_declared_variant_generation/FREEZE_PROTOCOL.md",
}
actual = {name: sha256(path) for name, path in paths.items()}
if actual != EXPECTED:
    raise RuntimeError("Bound S39/S40 workflow evidence changed")
if read_json(paths["loading_review"]).get("status") != "PASS_S39_LOADING_EVIDENCE_REVIEW":
    raise RuntimeError("S39 loading review is not PASS")
if any(read_json(paths[name]).get("status") != "REVISION_REQUIRED" for name in ("freeze_review_v1", "freeze_review_v2")):
    raise RuntimeError("Historical blocking S40 reviews were not preserved")

generation_root = ROOT / "results/S40_declared_variant_generation"
execution_root = ROOT / "work/S40_declared_variant_generation/execution_01"
if generation_root.exists() or execution_root.exists():
    raise RuntimeError("S40 started before the freeze-tool review passed")

now = datetime.now(timezone.utc)
if now.timestamp() < TARGET:
    raise RuntimeError("30-minute target has not arrived")
interval = (now - PREVIOUS).total_seconds() / 60.0

record = {
    "schema": "research-workflow-check-v1",
    "checked_utc": now.isoformat(),
    "checked_local": now.astimezone(ZoneInfo("Asia/Shanghai")).isoformat(),
    "previous_checked_utc": PREVIOUS.isoformat(),
    "interval_minutes": interval,
    "trigger": "Post-interruption state recovery before S40 core freeze",
    "checks": [
        {"item": "skills", "status": "PASS", "finding": "Re-read the project principles, quality targets, errata and workflow checklist; kept Supervisor strong-baseline-to-failure and local scientific review rules active.", "evidence": "RESEARCH_PRINCIPLES.md"},
        {"item": "innovation", "status": "PASS", "finding": "Source-to-region addressability remains a falsifiable diagnostic hypothesis only; no load, freeze, or generic routing change is called a method contribution.", "evidence": "work/S42_causal_memory_gap_search/RECONCILIATION.md"},
        {"item": "experiment", "status": "PASS", "finding": "S39 real loading review remains PASS and both S40 reserved roots remain absent. No generation was started during the interruption.", "evidence": "work/S39_component_variant/loading_attempt_01/independent_loading_evidence_review.json"},
        {"item": "local_tools", "status": "PASS", "finding": "Restored actual filesystem, hash, agent and process state before continuing; the corrected freeze tool still has its reviewed byte identity.", "evidence": "work/S40_declared_variant_generation/freeze_s40_manifest.py"},
        {"item": "retrieval", "status": "PASS", "finding": "No new method claim arose in this interval, so the existing verified 35-source literature base remains applicable; repeating broad search would not resolve the current execution gate.", "evidence": "work/S42_causal_memory_gap_search/sources.json"},
        {"item": "agents", "status": "PASS", "finding": "The interrupted third v3 review was explicitly re-dispatched to the same independent reviewer; interrupted status was not treated as a scientific failure or a PASS.", "evidence": "work/S40_declared_variant_generation/freeze_tool_source_review_incremental_v2.json"},
        {"item": "records", "status": "ACTION_REQUIRED", "finding": "The requested 30-minute cadence was late because the prior turn was interrupted. The real interval is recorded without backdating, and the ledger/memory synchronization remains due after the next material S40 milestone.", "evidence": "workflow_checks.jsonl"},
    ],
    "issues": [
        f"Actual interval is {interval:.6f} minutes; the missed target is disclosed rather than backdated.",
        "The third incremental freeze-tool review has not yet returned PASS.",
        "No real S40 video, natural failure, causal effect, improvement, or method novelty is established.",
    ],
    "corrections": [
        "Recovered filesystem and agent state after the interruption before running anything.",
        "Re-dispatched only the unfinished v3 independent review; no successful experiment or transfer was repeated.",
    ],
    "new_method_validated": False,
    "next_step": "Wait for the v3 source verdict; if PASS, freeze one S40 core and obtain two different-author actual-core reviews before the single real generation.",
    "runtime_observation": {
        "s39_loading_review_sha256": actual["loading_review"],
        "s40_generation_root_absent": True,
        "s40_execution_root_absent": True,
        "current_freeze_tool_sha256": actual["freeze_tool"],
        "current_freeze_protocol_sha256": actual["freeze_protocol"],
        "v3_review_state": "REDISPATCHED_AFTER_INTERRUPTION",
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
    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

append_event(
    "S42 中断后科研流程七项实查完成",
    f"实际间隔{interval:.6f}分钟；迟于30分钟目标，已如实记录。恢复后确认S39加载复核仍PASS，S40两个运行根均不存在，第三轮冻结工具审查仅重新派发，未把中断冒充通过或科学失败。",
    evidence=["workflow_checks.jsonl", "work/S39_component_variant/loading_attempt_01/independent_loading_evidence_review.json", "work/S40_declared_variant_generation/freeze_tool_source_review_incremental_v2.json"],
    next_step=record["next_step"],
    occurred_at=now.isoformat(),
    time_source="Actual current clock after heartbeat recovery; interval computed from previous recorded check",
    event_id="s42-workflow-check-post-interruption-20260907T0739Z",
)

print(json.dumps({"status": "RECORDED", "checked_utc": now.isoformat(), "interval_minutes": interval}, ensure_ascii=False))
