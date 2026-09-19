#!/usr/bin/env python3
"""Append the next actual 30-minute research-workflow audit."""

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


PREVIOUS = datetime.fromisoformat("2026-09-07T06:26:25.772726+00:00")
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
    raise RuntimeError("Reviewed S39/S40 workflow evidence changed")

loading_review = read_json(paths["loading_review"])
review_v1 = read_json(paths["freeze_review_v1"])
review_v2 = read_json(paths["freeze_review_v2"])
if loading_review.get("status") != "PASS_S39_LOADING_EVIDENCE_REVIEW":
    raise RuntimeError("S39 independent loading review is not PASS")
if review_v1.get("status") != "REVISION_REQUIRED" or review_v2.get("status") != "REVISION_REQUIRED":
    raise RuntimeError("Historical S40 blocking reviews were not preserved")

generation_root = ROOT / "results/S40_declared_variant_generation"
execution_root = ROOT / "work/S40_declared_variant_generation/execution_01"
if generation_root.exists() or execution_root.exists():
    raise RuntimeError("S40 was started before the freeze-tool review passed")

now = datetime.now(timezone.utc)
if now.timestamp() < TARGET:
    raise RuntimeError("30-minute target has not arrived; refusing an early check")
interval = (now - PREVIOUS).total_seconds() / 60.0

record = {
    "schema": "research-workflow-check-v1",
    "checked_utc": now.isoformat(),
    "checked_local": now.astimezone(ZoneInfo("Asia/Shanghai")).isoformat(),
    "previous_checked_utc": PREVIOUS.isoformat(),
    "interval_minutes": interval,
    "trigger": "S39 actual loading review and adversarial S40 freeze-tool revision",
    "checks": [
        {
            "item": "skills",
            "status": "PASS",
            "finding": "Continued Supervisor strong-baseline-to-failure discipline and the local scientific hypothesis, statistics, peer-review, critical-thinking and brainstorming rules. Review findings were treated as blockers rather than waived.",
            "evidence": "work/S42_statistical_preregistration/PROTOCOL.md",
        },
        {
            "item": "innovation",
            "status": "PASS",
            "finding": "The source-to-region causal diagnosis remains an unvalidated hypothesis. No generic routing or pooling mechanism, component loading, or infrastructure repair was relabelled as novelty.",
            "evidence": "work/S42_causal_memory_gap_search/RECONCILIATION.md",
        },
        {
            "item": "experiment",
            "status": "PASS",
            "finding": "S39 is a real completed component-loading run with an independent evidence PASS. S40 has not started: both reserved run roots are absent while the manifest-freeze tool remains under review.",
            "evidence": "work/S39_component_variant/loading_attempt_01/independent_loading_evidence_review.json",
        },
        {
            "item": "local_tools",
            "status": "PASS",
            "finding": "Used local hashing, immutable JSON receipts, AST validation, path-isolation probes, apply_patch and multi-agent source review. No model or large-weight read occurred during the S40 tool revision.",
            "evidence": "work/S40_declared_variant_generation/freeze_tool_source_review_incremental_v2.json",
        },
        {
            "item": "retrieval",
            "status": "PASS",
            "finding": "The frozen 35-record primary literature base and exact VMem source remain the current evidence base; no unsupported external suggestion was promoted to a claim.",
            "evidence": "work/S42_causal_memory_gap_search/sources.json",
        },
        {
            "item": "agents",
            "status": "PASS",
            "finding": "A different agent independently cleared the S39 loading evidence and another adversarial reviewer twice blocked S40 preparation, first on two issues and then on one remaining path-alias edge case.",
            "evidence": "work/S40_declared_variant_generation/freeze_tool_source_review.json",
        },
        {
            "item": "records",
            "status": "PASS",
            "finding": "S39 loading review and both S40 REVISION_REQUIRED receipts remain timestamped and hash-bound. Failures are retained rather than overwritten.",
            "evidence": "RESEARCH_LOG.md",
        },
    ],
    "issues": [
        f"Actual interval is {interval:.6f} minutes and is recorded without backdating.",
        "The third incremental S40 freeze-tool review is still required before prepare.",
        "The exact original SD2.1 VAE identity remains unknown; the runnable target is the declared ft-mse component variant.",
        "No S40 video, natural failure, causal effect, improvement, method novelty, or acceptance-level result exists yet.",
    ],
    "corrections": [
        "R2 now exact-rebinds freeze_preparation to the active S39 manifest, four evidence records and loading review.",
        "R1 now isolates freeze outputs from both reserved run roots and pins an external core output_root before attach creates any directory.",
    ],
    "new_method_validated": False,
    "next_step": "Obtain a PASS third incremental source review; only then freeze one actual S40 core, obtain two different-author actual-core reviews, attach them, and start one bounded real generation.",
    "runtime_observation": {
        "s39_loading_review_status": loading_review["status"],
        "s39_loading_review_sha256": actual["loading_review"],
        "s40_generation_root_absent": True,
        "s40_execution_root_absent": True,
        "s40_freeze_review_v1_status": review_v1["status"],
        "s40_freeze_review_v1_sha256": actual["freeze_review_v1"],
        "s40_freeze_review_v2_status": review_v2["status"],
        "s40_freeze_review_v2_sha256": actual["freeze_review_v2"],
        "current_freeze_tool_sha256": actual["freeze_tool"],
        "current_freeze_protocol_sha256": actual["freeze_protocol"],
    },
}

target = ROOT / "workflow_checks.jsonl"
with target.open("a+", encoding="utf-8") as handle:
    fcntl.flock(handle, fcntl.LOCK_EX)
    handle.seek(0)
    prior = [json.loads(line) for line in handle if line.strip()]
    if not prior or prior[-1].get("checked_utc") != PREVIOUS.isoformat():
        raise RuntimeError("Unexpected previous workflow check; refusing duplicate or out-of-order append")
    handle.seek(0, 2)
    handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    handle.flush()
    fcntl.flock(handle, fcntl.LOCK_UN)

append_event(
    "S42 科研流程七项实查完成",
    f"实际间隔{interval:.6f}分钟。技能、创新边界、真实实验、本地工具、检索、独立agent和记录均已核对。S39实际加载及独立复核已通过；S40冻结工具两次被审查阻断并完成针对性修正，当前仍未开始生成。",
    evidence=[
        "workflow_checks.jsonl",
        "work/S39_component_variant/loading_attempt_01/independent_loading_evidence_review.json",
        "work/S40_declared_variant_generation/freeze_tool_source_review.json",
        "work/S40_declared_variant_generation/freeze_tool_source_review_incremental_v2.json",
    ],
    next_step=record["next_step"],
    occurred_at=now.isoformat(),
    time_source="Actual current clock; interval computed from previous recorded check",
    event_id="s42-workflow-check-after-20260907T065625Z",
)

print(json.dumps({"status": "RECORDED", "checked_utc": now.isoformat(), "interval_minutes": interval}, ensure_ascii=False))
