#!/usr/bin/env python3
"""Append timestamped research events; render a readable Chinese ledger."""
import argparse
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
import uuid
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
ZONE = ZoneInfo("Asia/Shanghai")


def iso_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def append_event(action, outcome, evidence=(), next_step="", occurred_at=None,
                 time_source="current clock", event_id=None, root=ROOT):
    recorded = iso_now()
    occurred = occurred_at or recorded
    instant = datetime.fromisoformat(occurred)
    if instant.tzinfo is None:
        raise ValueError("Event time must include a timezone")
    event = dict(id=event_id or str(uuid.uuid4()), occurred_at=occurred,
                 occurred_local=instant.astimezone(ZONE).isoformat(timespec="seconds"),
                 recorded_at=recorded, time_source=time_source, action=action,
                 outcome=outcome, evidence=list(evidence), next_step=next_step)
    root = Path(root)
    with (root/"research_events.jsonl").open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        handle.seek(0)
        existing = [json.loads(line) for line in handle if line.strip()]
        if any(item["id"] == event["id"] for item in existing):
            return False
        handle.seek(0, 2)
        handle.write(json.dumps(event, ensure_ascii=False)+"\n")
        handle.flush()
        existing.append(event)
        render(existing, root/"RESEARCH_LOG.md")
        fcntl.flock(handle, fcntl.LOCK_UN)
    return True


def render(events, path):
    # A 2026-09-08 recovery compared UTC with +08:00 strings and appended
    # duplicate recovery entries. Keep the raw append-only ledger intact;
    # collapse only that marked recovery's exact content aliases in this view.
    def recovery_key(event):
        instant = datetime.fromisoformat(event['occurred_at']).astimezone(timezone.utc)
        return (instant.isoformat(timespec='seconds'), event['action'], event['outcome'])

    originals = {recovery_key(e) for e in events
                 if not e['id'].startswith('recovered-readable-')}
    visible = []
    collapsed = 0
    for event in events:
        if (event['id'].startswith('recovered-readable-')
                and event.get('time_source', '').startswith('Recovered from prior readable-only log;')
                and recovery_key(event) in originals):
            collapsed += 1
        else:
            visible.append(event)
    lines = ["# 研究时间记录", "", "时间统一显示为北京时间（Asia/Shanghai，UTC+8）。",
             "原始记录只追加；历史事件若补记，会注明时间来源及补记时间。时间点不等于已投入工时。", ""]
    if collapsed:
        lines += [f"日志恢复纠正：原始JSONL保留{collapsed}条误补的重复恢复记录；本视图合并同一UTC秒、动作和正文完全相同的已标记别名。它们不代表新增工作，原始事件未删除。", ""]
    for event in sorted(visible, key=lambda x: datetime.fromisoformat(x["occurred_at"])):
        lines += [f"## {event['occurred_local']} · {event['action']}", "",
                  event["outcome"], "", f"时间依据：{event['time_source']}；记录写入于 {event['recorded_at']}。", ""]
        if event["evidence"]:
            lines += ["证据："+"；".join(f"`{p}`" for p in event["evidence"]), ""]
        if event["next_step"]:
            lines += ["下一步："+event["next_step"], ""]
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", required=True)
    parser.add_argument("--outcome", required=True)
    parser.add_argument("--evidence", action="append", default=[])
    parser.add_argument("--next-step", default="")
    args = parser.parse_args()
    append_event(args.action, args.outcome, args.evidence, args.next_step)
