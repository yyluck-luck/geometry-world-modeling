from pathlib import Path
from datetime import datetime, timezone
import json, sys

root=Path(__file__).resolve().parents[1]
ws=Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip')
now=datetime.now(timezone.utc).isoformat()
history=root/'docs/history';history.mkdir(exist_ok=True)
names=['RESEARCH_MEMORY.md','docs/RESEARCH_HANDOFF_CURRENT.md','docs/PROPOSAL_PROGRESS_CURRENT.md','docs/START_HERE_CURRENT.md','docs/PROJECT_DELIVERY_TRACKER.md','docs/PAPER_LOGIC_CURRENT.md']
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
for name in names:
    (history/(stamp+'_'+Path(name).name)).write_bytes((root/name).read_bytes())

memory=f'''# 当前科研记忆与接手入口

更新UTC：{now}；北京时间=UTC+8。**S24三个796帧真实基线及评分/复核/图表全部完成。S26首次运行FAILED保留；其已完成的共同旧4帧GA保存量已通过IMPORT_VALIDATED复核。S26B只续跑未执行的三个8帧GA，当前在最终独立前审，尚未冻结/启动。**

## 目标、原则与接手

用户是MSc新手，要求简单中文、本机自主持续推进、时间记录、每30分钟实查、Supervisor及本地Claude skills、多agent与原文检索；不是调用Claude模型/CLI。最终目标PhD深度/CCF A投稿质量，当前未达到；不保证录用或老师反应。先强基线→真实剩余失败→可证伪机制。读取AGENTS.md、RESEARCH_PRINCIPLES.md v1.4、最新RESEARCH_LOG.md；通过scripts/research_log.py追加research_events.jsonl。旧原件/失败/协议不改，不发导师消息。

最近实际流程检查15:46:03.159826UTC，间隔31.218771分钟稍超30分钟，已如实记录；下一次应不晚于16:16:03UTC。不是声称定时器实际触发。完整历史路径见docs/RESEARCH_HANDOFF_CURRENT.md；本次更新前记忆另存docs/history。outputs只是交付快照。

## 已完成的真实证据

- S21/S22，同fr2_desk已见300帧：CUT/TTT/FILT ATE 8.254/2.848/1.858cm，已有方法。FILT原生CPU精度兼容失败保留；一行RoPE精度统一后24头精确相同才跑300。S23复用预测，278深度配对/22缺失，完整300均值NA；278描述AbsRel4.6235/3.2608/3.0618%，逐帧RMSE均值.392691/.325125/.340982m。>8m少量GT占FILT大量SSE，未证明传感器错或遗忘。见docs/S21_RESULTS.md至S23_RESULTS.md。
- **S24已完成**：fr1_xyz全798RGB→796严格20ms配对，26.572059秒，场景早期已见，非盲测。同512DPT/CPU8，CUT→TTT→FILT真实全头/pose完成后统一评分。主ATE12.2406289/9.6864554/2.9025811cm；RPEt .01442914/.01581448/.00638827m。FILT预定8块ATE均较低，不能据非零误差宣称灾难遗忘。最终报告docs/S24_RESULTS.md，主results/S24_baseline_expansion/scoring，多跨度results/S24_horizon_diagnostic。
- S24全起点1秒/5秒RPEt RMSE：CUT .153804/.183083m，TTT .107212/.126482m，FILT .034825/.040754m；不重新对齐。7164行/6618有效配对不同数学重算通过，主表不同作者、horizon同作者另一公式，非外部复现。work/S24_independent_numeric_review。
- S24原主图裁掉TTT尖峰的问题保留FAIL图，另存scripts/plot_s24_baseline_v2.py，只改完整共同纵轴。work/S24_reporting_v2已实际查看PASS报告尺寸；不称最终排版认证。WS outputs/S24_796帧真实结果_2026-09-06含报告、图表、9张未经修改实拍、数值及SHA清单。原session53980/20829都exit0，不再轮询/重跑。

## 当前消费者实验：S26失败 → S26B准备

S26原冻结manifest SHAd517d349ed34cedaa2c2c45b812698bf02d6f4ab5220899e3e34fefe6fd847ce。首8个fr2_desk帧，仅0.235880秒，老4+新4组件pilot。共同GT相机是显式oracle控制输入；共同旧depth来自original4原GA，不是GT深度。旧深度/相机固定，新深度和所有focal可优化，原VMem star anchor0、400/.01。0新网络。

15:37:04UTC原dispatch启动；三源PIL预处理和28档案六头拼装PASS。共同旧4真实400GA完成+clean+全输出保存后，15:37:36.803991独立clean参考不一致导致FAILED。其余三个GA没有开始，sensor深度未读。原结果results/S26_consumer_baseline和work/S26_execution不覆盖。

12/786432置信度失配全部定位：11个半像素取整翻转、1个先前清零传播；NumPy/Torch FP32 inverse及累加次序不同。原clean可精确重放，新独立dense-gather公式与原输出逐字节一致，没有容差豁免。work/S26_clean_recovery/DIAGNOSIS_AND_IMPORT.md；29项保存量复核15:55:14–15:55:15UTC通过，receipt SHA65efcbe2c181cb866e40b0d33e3846edbb1565e9d3644102ae6e22f7ce273927，结论仅IMPORT_VALIDATED。历史postfinal标量/flags/PnP/module库存未落盘，明确NOT_RECORDED；本次新纯函数复算不冒充原记录。

S26B候选在work/S26B_preparation，scripts/s26b_consumer_baseline.py，scripts/score_s26b_consumer.py。另一作者最终前审中。root审后新冻结manifest，导入共享PASS产物及共同旧depth，原失败保留；仅运行CUT/TTT/FILT三个新8图GA共1200步，再全部封存后sensor深度评分。导入receipt的PASS只表示新IMPORT_VALIDATED，0新GA；不能追认旧S26。新GA每臂保留原PIL输入构造和完整数学门；observer在关键阶段持久化。不要修改旧冻结脚本或重跑已成功400步。启动前先看run_manifest与work/S26B_execution真实状态，防止重复。

## 创新问题与技能具体应用

重点docs/IDEA_GENERATION_FOCUS_CURRENT.md与Supervisor handbook2.1/2.2/2.3；固定207bc6f7a1aa107e544099c2c7cc86816fba9628。reader已读59MD+70页PDF（12skills/18中文章/28refs/README），126其他文件只索引。五路首轮全完成，work/S23_innovation_*，没有成立新方法。idea-evaluator先排致命缺陷，Claude科学批判区分代理、消费者与生成结果。

原VMem每几何调用重置S/M、重放全历史；GA不用raw camera_pose，只消费anchor self与后续other。自由ATE改善不能验收proposal。S25四臂state adapter仅静态，60作者/92独立小测试，不是模型干预结果。

新源码线索work/S26_commit_consistency_source/audit.md：旧depth/pose固定但旧focal优化，重建旧world可变；提交的Surfel旧点不重写。另surfel_Ks累计所有历史focal快照、查询用均值、undo未同步。**只是源码机制线索，尚无消费者数值/伤害/创新证据。** 普通focal冻结/重建旧图/修缓存必须作工程对照；old-only冻结不能误用会冻结整个8帧栈的preset_focal。S26B完整旧4描述诊断正在预先准备，0新GT/GA，不称真实Surfel/cache运行。

work/S26_consumer_novelty_check已核G-CUT3R/Pow3R/MapAnything/TCO/RayMap3R五篇原方法；TCO重要直接近邻，泛化相机条件/loss反馈/ray门控不足以是新方法。不能靠换名或图好看认定创新。

## 环境、完整生成与proposal缺口

M3Max64GiB、CPU8、无远程GPU；.venv-cut3r/bin/python：Torch2.7/NumPy1.26，work/S17C_environment/site-packages为evo/Matplotlib overlay。原512权重data/cut3r/cut3r_512_dpt_4_64.pth完整3173761006B，SHA45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103，不重下。祖先Git覆盖HOME，不全量git add/commit。

完整VMem视频未执行，原主权重gated、VAE缺口未解。work/S25_official_resource_recheck核7官方小URL未找到替代；未擅自认证申请或下载未知替代权重。本地消费者研究仍可推进，不把资源缺口扩大成整个项目无法进展。

原14周proposal：1–3文献/基线、4–5失败、6–9方法、10–12评价、13–14交付；当前成熟度约前3周到第4周初，不是实际学生工时。主要缺口仍是新机制、公平跨场景确认、生成闭环、最终论文演示。
'''
(root/'RESEARCH_MEMORY.md').write_text(memory)

status=f'''<!-- CURRENT_STATUS_BEGIN -->
**当前状态（UTC {now}）**：S24三个796帧真实基线、评分、数值复核及修正版图表全部完成，ATE依次12.241/9.686/2.903cm。见[S24完整结果](S24_RESULTS.md)。S26原400步共同旧图GA已执行但参考clean核验失败；原FAILED保留，29项保存量补核后仅允许IMPORT_VALIDATED导入。S26B另立合同，只续跑未执行的三个8图GA，当前待最终独立前审/冻结。没有已验证新方法，也没有完整生成视频。

接手先读[当前记忆](../RESEARCH_MEMORY.md)、[第2章应用](IDEA_GENERATION_FOCUS_CURRENT.md)、[S26诊断](../work/S26_clean_recovery/DIAGNOSIS_AND_IMPORT.md)及[S26B计划](../work/S26B_preparation/plan.md)。原S24 sessions53980/20829均已exit0，不重启。最新执行状态以主账和回执为准。
<!-- CURRENT_STATUS_END -->

'''
for name in names[1:]:
    p=root/name;old=p.read_text();pos=old.find('# ')
    body=old[pos:] if pos>=0 else old
    p.write_text(status+'以下为按各自时间保留的历史路线与证据；其中旧的“当前/下一步”不覆盖上方现状。\n\n'+body)

start=f'''# 现在的研究在做什么

更新UTC：{now}。

研究问题是：**看过更多照片后，系统能否修正三维地图，同时保住已经正确的历史？**

三种已有方法在796张真实照片上的运行、评分和图表已完成。位置误差依次约12.24、9.69、2.90厘米；它们是强基线结果，尚不是我们的新方法。

现在把已有真实预测送进VMem原几何优化，保持相机条件和旧深度相同，检查新地图的质量。首个共同旧图已算完400步；独立参考在12个像素发生浮点取整偏差，已逐点定位并补核。旧失败记录保留，后续将复用已验证输出，仅跑剩余三个优化。

创新线索是：锁住旧深度，是否仍会因焦距变化而改变旧点的位置？目前只是源码线索，必须先看实际输出，再排除普通修复和已有论文。完整生成视频和已验证创新仍未完成。

- [S24结果、图表和实拍](S24_RESULTS.md)
- [当前完整记忆](../RESEARCH_MEMORY.md)
- [科研时间记录](../RESEARCH_LOG.md)
- [手册第2章怎样用于本项目](IDEA_GENERATION_FOCUS_CURRENT.md)
- [对照proposal的总进度](PROPOSAL_PROGRESS_CURRENT.md)
'''
(root/'docs/START_HERE_CURRENT.md').write_text(start)
user=f'''# 最新科研进展

更新UTC：{now}；北京时间=UTC+8。

**796张真实照片、三种已有方法的完整实验已经完成，结果和真实照片都已整理好。** CUT3R、TTT3R、FILT3R的位置误差约12.24、9.69、2.90厘米。这是实际模型输出的评分，尚不是我们的创新成果。

下一步正在验证：**几何模型的预测，送进VMem真正使用的地图优化后，哪种更有效？** 首个共同旧地图已实际优化400步。数值复核出现的12像素偏差已定位并补核；保留原失败记录，准备复用保存结果，只续跑剩余三个优化。当前在最终独立前审，还没有这一轮深度评分。

正在追踪一个具体创新线索：旧深度不变，焦距变化是否仍会挪动旧地图上的点？先测是否发生、是否有害，再与普通修复和已有论文比较。没有已验证新方法，也没有新生成视频。

- [先看结果和真实照片](outputs/S24_796帧真实结果_2026-09-06/先看这里.md)
- [S24完整结果报告](outputs/S24_796帧真实结果_2026-09-06/完整结果报告.md)
- [最新项目记忆](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/RESEARCH_MEMORY.md>)
- [每一步时间记录](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/RESEARCH_LOG.md>)
- [Supervisor第2章具体执行](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/IDEA_GENERATION_FOCUS_CURRENT.md>)

PhD研究深度和CCF A投稿质量仍是最终目标。当前主要处于强基线与失败分析阶段。
'''
(ws/'最新科研进展.md').write_text(user)
handoff=ws/'研究交接总览_2026-09-06.md'
old=handoff.read_text();(history/(stamp+'_workspace_handoff.md')).write_text(old)
handoff.write_text(f'**最新接续（UTC {now}）**：S24三方法796帧全部完成；S26原失败保留、保存输出补核完成；S26B待独立前审/冻结。先读[最新科研进展](最新科研进展.md)和项目主账。以下为历史快照，不覆盖新状态。\n\n'+old)
sys.path.insert(0,str(root/'scripts'))
from research_log import append_event
append_event('S26保存量恢复完成；S24交付快照与当前交接同步',
    '独立保存量复核于15:55:14–15:55:15UTC完成29项，IMPORT_VALIDATED仅允许新合同导入，旧FAILED保留。12像素失配全归因，0新GA/GT。S26B最小候选由另一作者完成并独立前审；只计划3个未执行GA。S24快照含图表/9原始照片/数值，当前记忆已清除旧运行状态；时间为本次同步记录，非回填实验起止。',
    evidence=['work/S26_clean_recovery/recovery_receipt.json','work/S26B_preparation/manifest_candidate.json','docs/S24_RESULTS.md','RESEARCH_MEMORY.md',str(ws/'outputs/S24_796帧真实结果_2026-09-06/manifest.json')],
    next_step='审查并冻结S26B，导入保存量后执行三个真实GA与统一评分；完成旧focal/world描述诊断。')
print(json.dumps({'updated_utc':now,'archive_prefix':stamp,'status':'DONE'},ensure_ascii=False))
