#!/usr/bin/env python3
"""Append one actual S42 workflow audit after the 30-minute target."""

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


PREVIOUS = datetime.fromisoformat("2026-09-07T05:55:50.537386+00:00")
TARGET = PREVIOUS.timestamp() + 30 * 60


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


now = datetime.now(timezone.utc)
if now.timestamp() < TARGET:
    raise RuntimeError("30-minute target has not arrived; refusing an early check")

attempt4_path = ROOT / "work/S41_vmem_xet_attempt4/execution_01/receipt.json"
freeze_path = ROOT / "work/S39_component_variant/freeze_attempt_01/receipt.json"
attempt4 = read_json(attempt4_path)
freeze = read_json(freeze_path)
interval = (now - PREVIOUS).total_seconds() / 60.0

attempt4_ok = (
    attempt4.get("status") == "VERIFIED_COMPLETE_ORIGINAL_WEIGHT"
    and attempt4.get("download_exit_code") == 0
    and attempt4.get("actual_bytes") == attempt4.get("expected_bytes") == 5056346672
    and attempt4.get("actual_sha256")
    == attempt4.get("expected_sha256")
    == "675dc486a02ea06ecf8b6ab0cf4ef88c92298751b2daacf9f65c59871fcb7fe4"
    and attempt4.get("file_stable_during_hash") is True
    and attempt4.get("child_still_alive") is False
    and attempt4.get("group_still_alive") is False
)
freeze_ok = (
    freeze.get("status") == "CORE_FROZEN_AWAITING_REAL_REVIEWS"
    and freeze.get("component_bytes_read") == 12509269337
    and freeze.get("core_file_sha256")
    == "192a67337fb825a7ba156b3454d160faf489914efd76ba78f91f2e73e4f9205b"
    and freeze.get("core_sha256")
    == "816d86cbdb529f5621b4e9e210ec6ddd925390eb33c75cad07dc0664d12fb416"
)
if not attempt4_ok or not freeze_ok:
    raise RuntimeError("Current resource or freeze facts failed the workflow audit")

record = {
    "schema": "research-workflow-check-v1",
    "checked_utc": now.isoformat(),
    "checked_local": now.astimezone(ZoneInfo("Asia/Shanghai")).isoformat(),
    "previous_checked_utc": PREVIOUS.isoformat(),
    "interval_minutes": interval,
    "trigger": "S42 verified VMem resource, actual S39 core freeze, and causal preregistration",
    "checks": [
        {
            "item": "skills",
            "status": "PASS",
            "finding": "Applied Supervisor strong-baseline-to-failure discipline, vibe-research evidence boundaries, idea-evaluator and deep-research, plus local Claude scientific hypothesis, statistical analysis, peer review, critical thinking, and brainstorming guidance. The formal hypothesis-report figure requirement was not triggered because this stage produces executable protocols rather than a LaTeX hypothesis report.",
            "evidence": "work/S42_h1_instrumentation_feasibility/REPORT.md",
        },
        {
            "item": "innovation",
            "status": "PASS",
            "finding": "The current work remains a falsifiable source-to-region causal diagnosis. Generic pooling, attention, routing, geometry gates, source tags, point-cloud updates, and weighted means remain rejected as novelty; no method claim is made before a real natural failure and causal gates.",
            "evidence": "work/S42_causal_memory_gap_search/RECONCILIATION.md",
        },
        {
            "item": "experiment",
            "status": "PASS",
            "finding": "Attempt4 is a real completed resource transfer with exact full-file SHA. S39 prepare then reread all five component bodies and froze their actual identities. These are resource and reproducibility operations: zero model constructors, zero model loads, zero generations, and zero performance claims at this checkpoint.",
            "evidence": "work/S39_component_variant/freeze_attempt_01/receipt.json",
        },
        {
            "item": "local_tools",
            "status": "PASS",
            "finding": "Used the official Hugging Face SDK and Xet transport, local file/process/stat/hash validation, immutable freeze tooling, Codex multi-agent review, and local skill documents; no duplicate transfer or unreviewed load was launched.",
            "evidence": "work/S41_vmem_xet_attempt4/execution_01/receipt.json",
        },
        {
            "item": "retrieval",
            "status": "PASS",
            "finding": "The current protocol is grounded in 35 primary or reliable literature records and frozen VMem source, with Gemini suggestions treated as untrusted proposals and corrected against source and primary papers.",
            "evidence": "work/S42_causal_memory_gap_search/sources.json",
        },
        {
            "item": "agents",
            "status": "PASS",
            "finding": "Independent agents covered protocol reconciliation, H1 instrumentation feasibility, baseline-failure preregistration, statistical preregistration, and the two separately authored actual-core reviews; only completed artifacts count as evidence.",
            "evidence": "research_events.jsonl",
        },
        {
            "item": "records",
            "status": "PASS",
            "finding": "Attempt4 terminal success, exact receipt SHA, the one-time S39 prepare, actual core identities, protocol reconciliation, and H1 feasibility were appended with real timestamps while earlier failed transfers remain preserved.",
            "evidence": "RESEARCH_LOG.md",
        },
    ],
    "issues": [
        f"Actual interval is {interval:.6f} minutes and is recorded without backdating.",
        "The frozen core still requires two reviews of the actual canonical core before attach and loading.",
        "The exact original SD2.1 VAE identity remains unknown, so the runnable system is the declared ft-mse component variant.",
        "No real S40 baseline, natural failure, causal effect, improvement, or novelty is established yet.",
    ],
    "corrections": [
        "The stale S40 progress handoff was replaced with attempt4 and the current S39/S40 gates.",
        "The handoff now records that the root causal protocol and S42 label reconciliation passed document-level review.",
        "A0 replay planning now saves sampler-entry RNG and reuses the original unconditional branch; seed-only replay is rejected.",
    ],
    "new_method_validated": False,
    "next_step": "Complete two actual-core reviews, attach them without swapping file and canonical core SHA values, run the metadata gate, then run one bounded S39 component-loading attempt and independently review its four evidence files before S40.",
    "runtime_observation": {
        "attempt4_receipt_status": attempt4.get("status"),
        "attempt4_receipt_sha256": sha256(attempt4_path),
        "attempt4_actual_bytes": attempt4.get("actual_bytes"),
        "attempt4_actual_sha256": attempt4.get("actual_sha256"),
        "freeze_status": freeze.get("status"),
        "freeze_receipt_sha256": sha256(freeze_path),
        "core_file_sha256": freeze.get("core_file_sha256"),
        "core_sha256": freeze.get("core_sha256"),
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
    f"实际间隔{interval:.6f}分钟。已核技能、创新边界、实验真实性、本地工具、正式检索、独立agent和记录。attempt4全SHA与进程终态通过，S39 prepare重读12509269337B并冻结实际core；当前仍为等待双审，0模型加载、0视频、0性能或创新结论。",
    evidence=[
        "workflow_checks.jsonl",
        "work/S41_vmem_xet_attempt4/execution_01/receipt.json",
        "work/S39_component_variant/freeze_attempt_01/receipt.json",
        "work/S42_h1_instrumentation_feasibility/REPORT.md",
        "work/S42_causal_memory_gap_search/RECONCILIATION.md",
    ],
    next_step=record["next_step"],
    occurred_at=now.isoformat(),
    time_source="Actual current clock; interval computed from previous recorded check",
)

print(json.dumps({"status": "RECORDED", "checked_utc": now.isoformat(), "interval_minutes": interval}, ensure_ascii=False))
