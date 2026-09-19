#!/usr/bin/env python3
"""Append the S41 round-4 workflow audit once, using the actual wall clock."""

import fcntl
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from research_log import append_event


PREVIOUS = datetime.fromisoformat("2026-09-07T05:25:40.234940+00:00")
PARTIAL = ROOT / "data/vmem_recovery/xet_attempt4_01/.cache/huggingface/download/BsfI4pabC8UVUK-YxYSLmqRDQ1E=.675dc486a02ea06ecf8b6ab0cf4ef88c92298751b2daacf9f65c59871fcb7fe4.7789fa3d.incomplete"
EXECUTION_RECEIPT = ROOT / "work/S41_vmem_xet_attempt4/execution_01/receipt.json"


now = datetime.now(timezone.utc)
interval = (now - PREVIOUS).total_seconds() / 60.0
partial_bytes = PARTIAL.stat().st_size if PARTIAL.exists() else None
execution = json.loads(EXECUTION_RECEIPT.read_text(encoding="utf-8"))

record = {
    "schema": "research-workflow-check-v1",
    "checked_utc": now.isoformat(),
    "checked_local": now.astimezone(ZoneInfo("Asia/Shanghai")).isoformat(),
    "previous_checked_utc": PREVIOUS.isoformat(),
    "interval_minutes": interval,
    "trigger": "S41 source-reviewed VMem attempt4 and adversarial consumer-gap review",
    "checks": [
        {
            "item": "skills",
            "status": "PASS",
            "finding": "Applied Supervisor problem/resource convergence and closest-work rejection, vibe-research evidence boundaries, idea-evaluator fatal-flaw tests, deep-research primary-source verification, and local Claude scientific-critical-thinking guidance.",
            "evidence": "work/S41_gemini_adversarial_review/primary_retrieval_and_root_review.md",
        },
        {
            "item": "innovation",
            "status": "PASS",
            "finding": "Rejected generic pooling, attention, routing, source tags, geometry gates, and point-cloud updates as crowded prior work. Retained only a falsifiable memory-consumer sufficiency/addressability diagnostic, pending a natural real baseline failure.",
            "evidence": "work/S41_clip_mean_innovation_audit/AUDIT.md",
        },
        {
            "item": "experiment",
            "status": "PASS",
            "finding": f"Attempt4 is an actual resource transfer with RUNNING receipt and {partial_bytes} observed temporary bytes. It is not a model load or scientific run; zero videos, GT reads, or performance gains are claimed.",
            "evidence": "work/S41_vmem_xet_attempt4/execution_01/receipt.json",
        },
        {
            "item": "local_tools",
            "status": "PASS",
            "finding": "Used the official authenticated huggingface_hub 1.30.0 plus hf_xet 1.6.0 path, fixed revision, local process/stat checks, source hashing, and Codex agents; no duplicate transfer was launched.",
            "evidence": "work/S41_vmem_xet_attempt4/source_review.json",
        },
        {
            "item": "retrieval",
            "status": "PASS",
            "finding": "Primary conference pages and frozen local source were used to correct Gemini's spatial-token assumption and to reject covered mechanisms before implementation.",
            "evidence": "work/S41_gemini_adversarial_review/independent_verification_round4.md",
        },
        {
            "item": "agents",
            "status": "PASS",
            "finding": "Three independent agents are active on S39 post-download execution safety, round-4 protocol reconciliation, and broader S42 novelty-gap search.",
            "evidence": "research_events.jsonl",
        },
        {
            "item": "records",
            "status": "PASS",
            "finding": "Attempt4 start, visible Gemini round 4, primary-source/root review, source-review hashes, automation cadence correction, and this actual check are preserved without rewriting older failures.",
            "evidence": "RESEARCH_LOG.md",
        },
    ],
    "issues": [
        f"Actual interval is {interval:.6f} minutes and is recorded without backdating.",
        "Attempt4 remains incomplete until the terminal receipt reports exact size and full-file SHA-256; temporary byte growth is not a valid model artifact.",
        "The retained consumer-addressability idea is still a diagnostic hypothesis, not a novel method or demonstrated improvement.",
    ],
    "corrections": [
        "The automation RRULE was corrected in place from 20 minutes to the requested 30 minutes while preserving the same thread and prompt.",
        "Multi-token CLIP sequences were removed from the primary fair matrix because they change K/V length and are out of the published checkpoint interface distribution.",
        "S39 freeze/load remains gated on one verified original VMem file and independent reviews of the actual frozen core.",
    ],
    "new_method_validated": False,
    "next_step": "Continue the same attempt4 to terminal verification; reconcile the causal protocol with independent review; if and only if full SHA passes, execute the reviewed S39 freeze and loading chain before the S40 real two-batch baseline.",
    "runtime_observation": {
        "attempt4_receipt_status": execution.get("status"),
        "attempt4_partial_bytes": partial_bytes,
        "expected_bytes": execution.get("expected_bytes"),
        "expected_sha256": execution.get("expected_sha256"),
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
    "S41 科研流程七项实查完成",
    f"实际间隔{interval:.6f}分钟。已核技能、创新边界、实验真实性、本地工具、正式检索、三名独立agent与记录；attempt4当时仅为RUNNING资源下载，临时文件{partial_bytes}B，0模型加载、0视频、0性能结论。消费者可寻址性仍只是待真实基线反证的诊断假说。",
    evidence=[
        "workflow_checks.jsonl",
        "work/S41_vmem_xet_attempt4/execution_01/receipt.json",
        "work/S41_gemini_adversarial_review/primary_retrieval_and_root_review.md",
        "work/S41_clip_mean_innovation_audit/AUDIT.md",
    ],
    next_step=record["next_step"],
    occurred_at=now.isoformat(),
    time_source="Actual current clock; interval computed from previous recorded check",
)

print(json.dumps({"status": "RECORDED", "checked_utc": now.isoformat(), "interval_minutes": interval, "partial_bytes": partial_bytes}, ensure_ascii=False))
