"""Sync the root's observed reading/baseline status, retaining every old snapshot."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import sys

R = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
W = Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip')
now = datetime.now(timezone.utc)
body = '更新UTC：' + now.isoformat() + '（北京时间UTC+8）。本段覆盖下方历史状态。\n\n'
body += (R/'work/resumption_20260909/CURRENT_STATUS.md').read_text()
backup = R/'work/resumption_20260909'/('reading_entrypoint_backup_'+now.strftime('%Y%m%dT%H%M%S%fZ'))
backup.mkdir()
changed = []
for i, p in enumerate([R/'RESEARCH_MEMORY.md', R/'docs/RESEARCH_HANDOFF_CURRENT.md', R/'docs/PROPOSAL_PROGRESS_CURRENT.md', R/'docs/PAPER_LOGIC_CURRENT.md', R/'docs/PROJECT_DELIVERY_TRACKER.md']):
    old = p.read_text()
    (backup/f'{i}_{p.name}').write_text(old)
    start = '<!-- CURRENT_STATUS_BEGIN -->'
    end = '<!-- CURRENT_STATUS_END -->'
    assert old.count(start) == old.count(end) == 1
    a = old.index(start) + len(start)
    b = old.index(end, a)
    p.write_text(old[:a]+'\n'+body+'\n'+old[b:])
    changed.append(p)
p = W/'最新科研进展.md'
(backup/p.name).write_text(p.read_text())
p.write_text('# 最新科研进展\n\n'+body)
changed.append(p)
p = W/'研究交接总览_2026-09-06.md'
old = p.read_text()
(backup/p.name).write_text(old)
p.write_text('> 当前接续 '+now.isoformat()+'：先读[最新研究记忆](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/RESEARCH_MEMORY.md>)与[最新科研进展](</Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/最新科研进展.md>)。实际运行、独立复核、失败和创新边界以最新记忆与主账为准；下方是保留的历史快照。\n\n'+old)
changed.append(p)
receipt = {'updated_utc':now.isoformat(), 'backup':str(backup), 'changed':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in changed}}
(backup/'SYNC_RECEIPT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
sys.path.insert(0,str(R/'scripts'))
from research_log import append_event
append_event('同步当前科研结果与接续到全部入口', '以当前观察更新五份项目入口与两份工作区入口；原入口逐份备份。实际执行、独立复核、未完成环节和创新边界分别保留，不把当前状态写回旧实验结果。', [str((backup/'SYNC_RECEIPT.json').relative_to(R)), 'work/resumption_20260909/CURRENT_STATUS.md', 'docs/INNOVATION_GUIDANCE_CURRENT.md'], '按最新入口中的有限下一步继续；依据实际失败选择可证伪机制，不以阅读或修复增加创新成熟度。')
print(json.dumps(receipt,ensure_ascii=False))
