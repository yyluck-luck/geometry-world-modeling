"""Refresh current entry points without altering historical research evidence."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import sys

R=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
W=Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip')
now=datetime.now(timezone.utc)
stamp=now.strftime('%Y%m%dT%H%M%SZ')
back=R/'work/resumption_20260908'/('entrypoint_backup_'+stamp)
back.mkdir()
def observe(rel):
    p=R/rel
    if not p.is_file(): return '尚未落盘'
    data=json.loads(p.read_text())
    return str(data.get('status',data.get('returncode','已落盘，见原文件')))
c2_source=observe('work/S47_c2_confirmation_generation/SOURCE_REVIEW.json')
c2_attach=observe('work/S47_c2_confirmation_generation/review_attachment_01/receipt.json')
body=f'''更新UTC：{now.isoformat()}（北京时间UTC+8）。本段覆盖下方历史状态。

**原则已升至v2.2。** 用户新增要求已写入[当前创新指导](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/INNOVATION_GUIDANCE_CURRENT.md>)：允许从强基线失败、顶会原论文机制、数学结构三条线并行寻找启发。候选逐项记录来源、假设、机制差别、可推翻预测、最小实验、否决条件与实际时间。理论推导不必等待整个基线完成；选择方法和声称收益仍须真实实验与强对照。

**真实实验数量没有因本轮修复增加。** 既有S40和C1各一次本机CPU两批VMem生成，采用声明的ft-mse VAE变体，非原SD2.1 VAE精确复现。B0 MSE=0.005278160708699555，小于预注册0.01；仅一行没有严重差异事件。C1像素仍未查看或盲评分。C2、S48方法arm均未生成。

| 分支 | 当前有效状态 | 下一步 |
|---|---|---|
| C1相机核验 | V7最终cache锚点错误已最小修为V8；V8双源码票、独立绑定与外部编排完成。但原监督入口实际return2、无PASS，未产生有效相机数值结果。只读诊断定位旧S45 binding的top-level引用被误读为嵌套字段，且report被错误要求具备worker receipt的schema/status | 保留失败，按NONCONSUMING_PREFLIGHT_DIAGNOSIS_V8核全部上游适配并做有限最小修复；冻结源码与旧票不可就地改写，不以模拟测试替代实物核验 |
| C2公平基线 | V7依赖传递修复获两名非作者PASS；唯一prepare已成功。核心源码票：{c2_source}；runtime票READY。附件：{c2_attach} | 按既定后续两票和launch授权流程接续；没有生成或评分授权来自本状态文档 |
| S50实拍候选 | 实际核45份文本/路径元数据，未读图片；fr2 source19/alternative18/target20存在，但target过去S8已作为输入，须标记历史暴露。旧target pose与RGB相差15.005ms | 按RGB时刻相机重建未来发现性输入，不能把update=false称为未见，也不能用TUM照片评价无对应关系的S40/C1场景 |
| S51文献与数学 | 核原论文近邻，后两项明确是arXiv预印本；SymPy1.14.0实际完成16组平均映射秩/零空间分析 | 标准数学揭示平均路径来源不可分辨性，但其他latent路径仍保留来源；尚不能推出质量损失或新方法 |
| S48/RAIMA | S48 V7已有限源码冻结；RAIMA V4已有独立统计审查，完整确认仍因数据和本机预算不满足而暂停扩展 | 不继续堆大协议，先完成可执行数据与有限实证问题 |

**科学边界：** `NO_METHOD_SELECTED`、`novelty_authorization=NONE`、`new_method_validated=false`。普通门控、来源token、均值的秩-零度推导、基线bug修复不能单独包装成创新。RAIMA V4完整CPU预算90.53–140.46天为历史计时外推；单unit单seed最小pilot约10.86小时。单张参考上的实测误差差值不自动等于期望风险差。

Proposal进度估计仍为整体交付40–45%、核心科学25–30%、14周路线约第5–6周；不是实际学时。本轮没有足够科学新结果提高这一估计。PhD深度/CCF A质量仍为目标，尚未达到。

入口：[文献与数学分析](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S51_innovation_math_guidance/LITERATURE_AND_MATH_ADDENDUM.md>)；[S50实拍见证](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S50_heldout_reference_metadata/FEASIBILITY.md>)；[研究主账](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/RESEARCH_LOG.md>)。实际事件统一经append_event记录；旧失败/撤回记录保留。导师邮件仍只是草稿，未发送。
'''
changed=[]
for index,p in enumerate([R/'RESEARCH_MEMORY.md',R/'docs/RESEARCH_HANDOFF_CURRENT.md',R/'docs/PROPOSAL_PROGRESS_CURRENT.md']):
    old=p.read_text()
    (back/f'{index}_{p.name}').write_text(old)
    begin='<!-- CURRENT_STATUS_BEGIN -->';end='<!-- CURRENT_STATUS_END -->'
    assert old.count(begin)==old.count(end)==1,p
    a=old.index(begin)+len(begin); b=old.index(end,a)
    p.write_text(old[:a]+'\n'+body+old[b:])
    changed.append(str(p))
p=W/'最新科研进展.md'
(back/p.name).write_text(p.read_text())
p.write_text('# 最新科研进展\n\n'+body)
changed.append(str(p))
handoff=W/'研究交接总览_2026-09-06.md'
if handoff.is_file():
    old=handoff.read_text();(back/handoff.name).write_text(old)
    # A compact new entry points to the canonical live state; dated body stays intact.
    handoff.write_text(f'> 接续更新 {now.isoformat()}：原则v2.2已加入顶会论文和数学启发；最新C1/C2/S50/S51状态请先读[当前研究记忆](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/RESEARCH_MEMORY.md>)与[创新指导](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/INNOVATION_GUIDANCE_CURRENT.md>)。下方为保留的历史交接。\n\n'+old)
    changed.append(str(handoff))
manifest=dict(updated_utc=now.isoformat(),backups=str(back),changed={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in changed})
(back/'SYNC_RECEIPT.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
sys.path.insert(0,str(R/'scripts'))
from research_log import append_event
append_event('同步创新指导与实际失败/准备结果到科研接手入口','同步原则v2.2入口、S50/S51新证据、C1 V8实际非PASS与C2真实prepare状态；保留全部旧入口备份及历史正文，没有增加科学完成度。',changed+[str(back/'SYNC_RECEIPT.json')],'从当前入口继续C1 schema最小修复、C2既定后续流程和数据可执行的创新判别。')
print(json.dumps(manifest,ensure_ascii=False))
