"""Copy the finished report and evidence into a fresh dated user-facing folder."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import shutil
import sys

R = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
W = Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip')
D = R/'work/S67_translated_query_diagnostic'
now = datetime.now(timezone.utc)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert (D/'NEXT_REAL_REFERENCE_FEASIBILITY.md').is_file()
assert (D/'ROOT_FINAL_RESULT_ACCEPTANCE.json').is_file()
out = W/'outputs'/('科研诊断与下一步_'+now.astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d_%H%M%S'))
out.mkdir()
mapping = {
    R/'docs/S67_TRANSLATED_QUERY_RESULT.md': '中文结果说明.md',
    R/'work/resumption_20260909/CURRENT_STATUS.md': '当前研究交接_本次快照.md',
    D/'figures/S67_projection_changes_context_unchanged.png': '诊断图_全部515点与5来源.png',
    D/'figures/S67_projection_changes_context_unchanged.svg': '诊断图_全部515点与5来源.svg',
    D/'figures/manifest.json': '原始绘图清单.json',
    D/'PROTOCOL.md': '结果前固定实验规则.md',
    D/'external_01/receipt.json': '实际运行外部回执.json',
    D/'execution_01/receipt.json': '实际数值结果回执.json',
    D/'SOURCE_REVIEW.md': '结果前不同作者源码审查.md',
    D/'INDEPENDENT_RESULT_REVIEW.md': '不同作者独立结果复核.md',
    D/'INDEPENDENT_RESULT_REVIEW.json': '不同作者独立结果复核.json',
    D/'ROOT_FINAL_RESULT_ACCEPTANCE.json': '最终结果接受记录.json',
    D/'NEAREST_WORK_BOUNDARY.md': '最近论文与创新边界.md',
    D/'NEXT_REAL_REFERENCE_FEASIBILITY.md': '下一步真实参考可行性.md',
    D/'ROOT_NEXT_REFERENCE_ACCEPTANCE.json': '下一步参考审查接受记录.json',
}
rows = []
for source, name in mapping.items():
    destination = out/name
    shutil.copy2(source, destination)
    source_sha = sha(source)
    assert sha(destination) == source_sha
    rows.append({'source':str(source), 'copy':str(destination), 'sha256':source_sha, 'bytes':source.stat().st_size})
old_images = W/'outputs/客厅实验实图与评分_2026-09-09_074506'
assert old_images.is_dir()
intro = f'''# 先看这里

本快照创建于北京时间{now.astimezone(timezone(timedelta(hours=8))).isoformat()}。先读[中文结果说明](<{out}/中文结果说明.md>)，再看[诊断图](<{out}/诊断图_全部515点与5来源.png>)和[下一步真实参考可行性](<{out}/下一步真实参考可行性.md>)。

本轮真实完成一次约5秒的保存数据诊断和不同作者独立复算：人为改变深度后，投影明显变化，最终四张记忆及全部返回缓存不变。它是有限的负结果，尚无新方法收益或新视频。

此前生成的全部图片另存于[客厅实图与评分文件夹](<{old_images}>)，其中1张输入、8张模型输出。这里的“实图”表示实际落盘结果，不表示模型图是现场实拍照片。

本目录为带时间的副本；继续研究以项目[当前记忆](<{R}/RESEARCH_MEMORY.md>)、[当前交接](<{R}/docs/RESEARCH_HANDOFF_CURRENT.md>)和[追加主账](<{R}/RESEARCH_LOG.md>)为准。旧快照及全部失败记录保持原样。
'''
(out/'先看这里.md').write_text(intro)
manifest = {'created_utc':now.isoformat(), 'copied_files':rows, 'copied_count':len(rows), 'all_copy_sha256_equal':True, 'intro_sha256':sha(out/'先看这里.md'), 'claim_boundary':'Saved-data numerical diagnostic, no new model generation and no validated novel method.'}
(out/'交付清单.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
receipt = {'created_utc':now.isoformat(), 'output_directory':str(out), 'copied_count':len(rows), 'all_copy_sha256_equal':True, 'manifest_sha256':sha(out/'交付清单.json')}
with (D/'ROOT_USER_SNAPSHOT_RECEIPT.json').open('x') as f:
    json.dump(receipt,f,ensure_ascii=False,indent=2)
    f.write('\n')
sys.path.insert(0,str(R/'scripts'))
from research_log import append_event
append_event('S67结果与真实参考可行性已交付带日期快照', f'已复制{len(rows)}份报告、原始图、协议、实际回执、不同作者复核和下一步数据审查，所有副本与来源SHA一致。保留原客厅九帧目录与旧记录；本动作仅交付，不是新实验。', ['work/S67_translated_query_diagnostic/ROOT_USER_SNAPSHOT_RECEIPT.json','docs/S67_TRANSLATED_QUERY_RESULT.md','work/S67_translated_query_diagnostic/NEXT_REAL_REFERENCE_FEASIBILITY.md'], '按真实参考可行性报告冻结最小新问题及匹配基线；当前没有新模型在后台运行，不为本例不变选图路径追加生成。')
print(json.dumps(receipt,ensure_ascii=False))
