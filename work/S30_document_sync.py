from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

ROOT = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
WS = Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip')
now = datetime.now(timezone.utc)
stamp = now.strftime('%Y%m%dT%H%M%SZ')
archive = ROOT / 'docs/history' / (stamp + '_before_S30_results')
archive.mkdir(exist_ok=False)
changed = []

def put(p, text):
    if p.exists():
        label = ('WS_' if p.is_relative_to(WS) else 'ROOT_') + p.name
        shutil.copy2(p, archive / label)
    p.write_text(text)
    changed.append(dict(path=str(p), sha256=hashlib.sha256(p.read_bytes()).hexdigest()))

summary = '**S30真实两臂各400步与不同作者完整复核已完成：单位尺度起点AbsRel5.03905%→终点42.37947%，原目标7.16118→0.0106400；原尺度臂83.33823%→87.47128%。两臂均修复梯度并逐字匹配各自S29初态。只修初始化仍不足。S31仅准备无GT单标量输出诊断，尚未执行。未成立新方法或完整视频结果，最终质量目标未完成。**'
memory = (ROOT / 'RESEARCH_MEMORY.md').read_text()
memory = re.sub(r'更新UTC：[^\n]+', f'更新UTC：{now.isoformat()}；北京时间=UTC+8。{summary}', memory, count=1)
start = memory.index('## S30')
end = memory.index('## 创新问题与技能具体应用', start)
memory = memory[:start] + '''## S30已完成：初始化较准，原优化仍损坏深度

正式合同work/S30_scale_optimization_preparation/contract.json SHA000fa5d5b19cc516a581b382e457dcf8e03494da50b220d8f32c0ad0b16224a3。runner8b7d7945、scorer75b92de8；root全文/21身份/两CLI与不同作者final_pre_review SHA879276223bfa477538f0c2fecd887c1016108d093d9b5073ace849aacc045ed3通过后冻结。

实际18:12:29.415572–18:13:32.552760UTC、63.137115秒，work/S30_launch/receipt.json PASS。session78388已exit0，勿重复轮询。C2t/C2a各400原Adam、1MST、3PnP、1clean，合计800新反传、0新网络；每臂另2getter边界目标/1postfinal，共403objective。8实拍PIL准备→已见common4，给定GT相机oracle输入；传感器深度仅在四端点全封存后评分。两臂相同修正getter、s29同族R0/居中t，只有初始化scale不同，训练期scale仍自由。每臂所有33raw初态/深度/初objective与各自S29逐字一致。

全部16评分/四组等帧均值：C2t initial AbsRel .8333823008231132、RMSE1.7257683115359483m、delta1=0；final .8747127535468233/1.803365109563265/0。C2a initial .05039049784637266/.27299278874047767/.9530260597130815；final .42379472814800356/.9108701709443372/.005172422134189376。C2a增加37.340423个百分点，虽然终点优于C2t终点，但远差于自己的零步强baseline。四组各有效GT540363、缺失246069、无无效预测；不GT拟合尺度/选步/conf筛/远点裁切。

C2t原objective1.2426233291625977→.0051070312038064；C2a7.1611785888671875→.010640016756951809。mean_pixel(finaldepth/initialdepth) C2t [.7637662292,.7946617603,.7967272401,.8073114753]，C2a [.6385813951,.6628937125,.6605189443,.6643793583]，不是ratio-of-means。两臂全部400步四depthgrad非None有限；independent clean全像素0失配、functional objective和world反投影原门PASS。尚不证明变化纯尺度或整体坐标对齐错误。

外控C2t30.970393秒/RSS1043103744B；C2a31.062435秒/RSS1057865728B，含观测开销非速度benchmark。不同作者保存数据复核实际18:21:29.386122–18:21:31.143825UTC、1.757563秒，外控2.068128秒/RSS465485824B。work/S30_independent_numeric_review/receipt.json PASS：16全网格3145728访问、16浮点组均值/8差分/全CSV/66raw初態/800完整记录；AbsRel/RMSE最大差2.22e-16，其他0。复用S28独立OpenCV逐行数学，不重算梯度范数，0模型/GA/MST/backward。session29860已exit0，不再轮询。

完整报告docs/S30_RESULTS.md已写；work/S30_reporting图与用户快照准备中。旧S28/S29成功产物和所有历史失败保持。

## S31仅准备：区分公共缩放与非均匀变化

先使用S30保存D0/D400，每臂全四帧一个k=exp(-mean(log D400-log D0))，不看GT求系数、不逐帧缩放、不加shift、不搜索超参。完整分解log-change的公共、帧间与帧内成分；封存D*=k D400后才按原4GT评分。零步C2a继续作为强对照。不新增优化/网络；这是事后输出归一描述，不能称优化器gauge修复、whole-world Sim3、真实物理形状因果或论文新方法。代码/协议work/S31_scale_shape_preparation由独立agent准备中，尚未审后冻结或执行。若普通约束足够，归工程基线；之后再考虑公平跨场景/实际消费者控制。

''' + memory[end:]
put(ROOT / 'RESEARCH_MEMORY.md', memory)

block = f'''<!-- CURRENT_STATUS_BEGIN -->
**当前状态（UTC {now.isoformat()}）**：[S30真实结果](S30_RESULTS.md)与不同作者完整复核已完成。单位尺度初始AbsRel5.03905%→400步42.37947%，损失反而下降；原尺度臂83.33823%→87.47128%。真实800步、0新网络，所有初态和原评分门通过。仅修初始化不够。

下一步S31仅准备：在保存输出上用自身起点求每臂单个全局尺度，分解公共与非均匀变化，0新GA；尚未冻结/执行，不是新算法。先读[当前记忆](../RESEARCH_MEMORY.md)、[S30报告](S30_RESULTS.md)与最新主账。旧原件/失败保持；已见四帧、GT相机oracle、0完整视频，最终质量目标未完成。
<!-- CURRENT_STATUS_END -->'''
for name in ['RESEARCH_HANDOFF_CURRENT.md','PROPOSAL_PROGRESS_CURRENT.md','PROJECT_DELIVERY_TRACKER.md','PAPER_LOGIC_CURRENT.md']:
    p = ROOT / 'docs' / name
    old = p.read_text()
    assert old.count('<!-- CURRENT_STATUS_BEGIN -->') == 1
    put(p, re.sub(r'<!-- CURRENT_STATUS_BEGIN -->.*?<!-- CURRENT_STATUS_END -->', lambda _: block, old, count=1, flags=re.S))
p = WS / '研究交接总览_2026-09-06.md'
wsblock = block.replace('(S30_RESULTS.md)', f'(<{ROOT}/docs/S30_RESULTS.md>)').replace('(../RESEARCH_MEMORY.md)', f'(<{ROOT}/RESEARCH_MEMORY.md>)')
put(p, re.sub(r'<!-- CURRENT_STATUS_BEGIN -->.*?<!-- CURRENT_STATUS_END -->', lambda _: wsblock, p.read_text(), count=1, flags=re.S))

front = f'''# 最新科研进展

更新UTC：{now.isoformat()}；北京时间=UTC+8。

**真实实验发现：原本较准确的深度，被优化器越改越差。** 保留原预测尺度时，初始平均相对深度误差5.04%，400步后42.38%；程序的loss却从7.16降到0.01064。另一初始尺度臂83.34%→87.47%，同样变差。

本轮确实在本机做了两组各400步几何优化，复用真实照片的已有预测，没有再次运行神经网络。不同作者已复核全部16条评分、66个初态张量和800步记录，最大数值差只有2.22e-16。四帧已经用于探索，给定相机使用真值；还不能据此宣称新方法、跨场景效果或视频生成成功。

下一步先用保存结果区分“整体缩小”与“不同位置的变化”，只从预测自身起点求一个尺度，不按真值调参。S31仍在准备，尚未执行；普通尺度修正若已能解决问题，就作为工程基线。

- [S30完整报告：真实数据、运行时间和复核](<{ROOT}/docs/S30_RESULTS.md>)
- [S29报告、4张原始实拍和完整核验](<{WS}/outputs/S29_初始化尺度的真实证据_2026-09-07/先读我.md>)
- [S28图、4张实拍与逐步记录](<{WS}/outputs/S28_梯度修复负结果与下一步_2026-09-07/先读我.md>)
- [此前796帧强基线](<{ROOT}/docs/S24_RESULTS.md>)
- [项目当前记忆](<{ROOT}/RESEARCH_MEMORY.md>)
- [每步时间记录](<{ROOT}/RESEARCH_LOG.md>)

按Supervisor第2章“基线→失败→根因→方法”推进，使用本地Claude科学批判技能、官方原文与源码检索、并行实现和审查。PhD研究深度/CCF A投稿质量仍是目标，尚未达到。S30结果图和实拍快照正在整理。
'''
put(ROOT / 'docs/START_HERE_CURRENT.md', front)
put(WS / '最新科研进展.md', front)

p = ROOT / 'docs/IDEA_GENERATION_FOCUS_CURRENT.md'
t = p.read_text()
t = t.replace('S30准备两臂400原步并统一零步/终点评分，检验起点与优化的作用；尚未运行。', 'S30已完成两臂400原步与16条完整独立复核：C2a初始5.03905%→终点42.37947%，原loss降低；C2t83.33823%→87.47128%。仅修初始尺度仍损坏深度。S31先准备无GT的自身初态单标量保存量诊断，分解公共/帧间/帧内log变化；0新GA，尚未执行。它是普通输出归一描述，不能称优化器gauge修复或新方法。')
put(p, t)

sys.path.insert(0, str(ROOT / 'scripts'))
from research_log import append_event
append_event('S30不同作者完整数值复核通过，确认准确起点被原优化损坏',
    'C2a AbsRel5.03905%→42.37947%，C2t83.33823%→87.47128%；原目标均下降。实际800新Adam/反传、0新网络。独立复核16全网格/16均值/8差/66初态/800记录，最大差2.22e-16，实际18:21:29.386122–31.143825UTC；0新GA/MST/backward。报告和当前交接已同步，图及快照整理中，S31仅准备。',
    evidence=['docs/S30_RESULTS.md','work/S30_independent_numeric_review/receipt.json','work/S30_independent_numeric_execution/review/receipt.json','RESEARCH_MEMORY.md'],
    next_step='完成S30图和实拍快照；审查S31只用自身起点的单标量分解，先区分尺度与非均匀变化，不按GT调参。',
    occurred_at='2026-09-06T18:21:31.143825+00:00', time_source='actual saved audit receipt; recorded after report synchronization')
(archive / 'sync_receipt.json').write_text(json.dumps(dict(status='PASS', recorded_utc=now.isoformat(), changed=changed), indent=2, ensure_ascii=False) + '\n')
print(json.dumps(dict(status='PASS', updated_documents=len(changed), archive=str(archive))))
