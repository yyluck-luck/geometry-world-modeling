#!/usr/bin/env python3
import fcntl
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from research_log import append_event

previous = datetime.fromisoformat("2026-09-07T04:52:51.410489+00:00")
now = datetime.now(timezone.utc)
interval = (now - previous).total_seconds() / 60.0
record = {
    "schema": "research-workflow-check-v1",
    "checked_utc": now.isoformat(),
    "checked_local": now.astimezone(ZoneInfo("Asia/Shanghai")).isoformat(),
    "previous_checked_utc": previous.isoformat(),
    "interval_minutes": interval,
    "trigger": "S41 VMem recovery terminal failure and Gemini third adversarial review",
    "checks": [
        {"item": "skills", "status": "PASS", "finding": "Applied vibe-research evidence boundaries, idea-evaluator fatal-flaw/closest-work logic, and deep-research primary-citation verification; external AI advice remains unadopted pending checks.", "evidence": "work/S41_gemini_adversarial_review/prompt.md"},
        {"item": "innovation", "status": "PASS", "finding": "CLIP-mean detail-loss remains a falsifiable hypothesis, not a result. Ordinary pooling, anchor, weighting, attention, and router variants remain controls rather than novelty.", "evidence": "work/S41_gemini_adversarial_review/response_visible.md"},
        {"item": "experiment", "status": "PASS", "finding": "HTTP recovery actually ran and failed before receiving any Range bytes; retained candidate is unverified. Zero model loads, generated frames, GT reads, or scientific experiment results.", "evidence": "data/vmem_recovery/http_recovery_01/receipt.json"},
        {"item": "local_tools", "status": "PASS", "finding": "Used official SDK metadata, a source-reviewed strict Range tool, local stat/rg, Codex CUA for the authorized Gemini UI, and bounded agent reviews.", "evidence": "work/S39_auth_recovery/partial_recovery/source_review_v2.json"},
        {"item": "retrieval", "status": "PASS", "finding": "Gemini supplied one nearby-paper candidate; independent primary-paper and source-code verification was dispatched before any adoption.", "evidence": "work/S41_gemini_adversarial_review/receipt.json"},
        {"item": "agents", "status": "PASS", "finding": "Three independent tasks are active: transfer-failure diagnosis, CLIP-mean innovation audit, and Gemini claim verification.", "evidence": "work/S41_gemini_adversarial_review/receipt.json"},
        {"item": "records", "status": "PASS", "finding": "Attempt3 terminal state, Range recovery failure, visible Gemini prompt/answer, actual check interval, and next actions are being appended without altering older evidence.", "evidence": "research_events.jsonl"}
    ],
    "issues": [
        f"Actual check interval was {interval:.6f} minutes; any delay beyond 30 minutes is recorded rather than backdated.",
        "Direct signed-CDN Range request raised ConnectError after zero received bytes; repeating the identical path is not justified.",
        "Gemini's proposed per-Surfel CLIP-token visibility map may assume spatial token structure that the actual VMem encoder does not expose."
    ],
    "corrections": [
        "Retain both 3,479,430,365-byte files as unverified artifacts and do not load them.",
        "Do not retry the same direct-CDN Range path before an independent transport diagnosis.",
        "Verify every Gemini citation and implementation assumption against primary papers and the frozen source."
    ],
    "new_method_validated": False,
    "next_step": "Finish independent S41 reviews; choose a materially different verified VMem acquisition path, or document the resource boundary; only after full SHA may S39 loading and the real two-batch baseline run."
}

target = ROOT / "workflow_checks.jsonl"
with target.open("a+", encoding="utf-8") as handle:
    fcntl.flock(handle, fcntl.LOCK_EX)
    handle.seek(0)
    prior = [json.loads(line) for line in handle if line.strip()]
    if not prior or prior[-1].get("checked_utc") != previous.isoformat():
        raise RuntimeError("Unexpected previous workflow check; refusing duplicate or out-of-order append")
    handle.seek(0, 2)
    handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    handle.flush()
    fcntl.flock(handle, fcntl.LOCK_UN)

append_event(
    "S39 attempt3 与严格 Range 恢复均真实终止",
    "Attempt3 在1800秒外控后超时并完成进程组清理；保留3479430365B硬链接。随后经独立源码审查的恢复工具复制该候选，官方元数据身份通过，但对签名CDN的单次Range请求在收到0字节时ConnectError。两个3479430365B文件均未完成SHA，不得加载；0模型/视频/GT。",
    evidence=["work/S39_auth_recovery/vmem_low_concurrency_attempt3/receipt.json", "data/vmem_recovery/http_recovery_01/receipt.json", "work/S39_auth_recovery/partial_recovery/source_review_v2.json"],
    next_step="等待独立传输诊断；不重复同一直接CDN Range路径，寻找不同且可完整SHA验收的合法获取方案。",
    occurred_at="2026-09-07T05:12:15.354159+00:00",
    time_source="Backfilled from terminal recovery receipt; attempt3 earlier terminal details retained in its own receipt"
)
append_event(
    "S41 Gemini 第三轮反驳审查实际完成并进入独立核验",
    "在用户已授权的Gemini Pro Extended会话发送真实源码约束，页面返回六臂诊断和一个几何token路由建议。原答按可见文本保存；未采纳方法或引用。初步发现其可能把全局CLIP embedding误当作可对应Surfel的空间token，已分派论文/源码独立核验。0模型加载/生成/GT。",
    evidence=["work/S41_gemini_adversarial_review/prompt.md", "work/S41_gemini_adversarial_review/response_visible.md", "work/S41_gemini_adversarial_review/receipt.json"],
    next_step="结合独立源码审查和正式论文核验，只保留可实现且可被真实VMem闭环推翻的诊断；普通聚合控制不称创新。",
    occurred_at=now.isoformat(),
    time_source="Current clock after visible response capture; Gemini service did not expose an exact generation timestamp"
)
append_event(
    "科研流程七项检查完成",
    f"实际间隔{interval:.6f}分钟；技能、创新边界、实验真实性、本地工具、检索、agent和记录逐项检查。发现Range恢复0字节ConnectError及Gemini空间token假设风险；均已转入不同作者诊断。新方法仍未验证。",
    evidence=["workflow_checks.jsonl", "work/S41_gemini_adversarial_review/receipt.json", "data/vmem_recovery/http_recovery_01/receipt.json"],
    next_step=record["next_step"],
    occurred_at=now.isoformat(),
    time_source="Actual current clock; interval computed from previous recorded check"
)

print(json.dumps({"status": "RECORDED", "checked_utc": now.isoformat(), "interval_minutes": interval}, ensure_ascii=False))
