"""Archive superseded current summaries and publish the verified S34 state."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import sys

ROOT = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
WS = Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip')
PACK = WS/'outputs/S34_固定旧地图三条件与真实照片_2026-09-07'
now = datetime.now(timezone.utc)
stamp = now.isoformat()
archive = ROOT/'docs/history'/f'{now:%Y%m%dT%H%M%SZ}_before_S34_closure'
archive.mkdir(parents=True, exist_ok=False)
sha = lambda b: hashlib.sha256(b).hexdigest()
paths = [ROOT/'RESEARCH_MEMORY.md', ROOT/'docs/S34_NEXT_STEP.md', ROOT/'docs/START_HERE_CURRENT.md', WS/'最新科研进展.md', WS/'研究交接总览_2026-09-06.md']
paths += [ROOT/'docs'/name for name in ['RESEARCH_HANDOFF_CURRENT.md','PROPOSAL_PROGRESS_CURRENT.md','PROJECT_DELIVERY_TRACKER.md','PAPER_LOGIC_CURRENT.md','IDEA_GENERATION_FOCUS_CURRENT.md']]
before = {}
for path in paths:
    data = path.read_bytes()
    dest = archive/(('WS_' if path.is_relative_to(WS) else 'ROOT_')+path.name)
    dest.write_bytes(data)
    before[str(path)] = {'sha256':sha(data),'archived_to':str(dest)}

link = lambda label, path: f'[{label}](<{path}>)'
report = link('S34完整报告',ROOT/'docs/S34_RESULTS.md')
bundle = link('8张真实照片、结果图及全部日志',PACK/'先读我.md')
decision = link('下一决策及源码依据',ROOT/'work/S34_next_decision/decision.md')
resource = link('最新有界资源检查',ROOT/'work/S34_resource_refresh/report.md')
memory_link = link('当前科研记忆',ROOT/'RESEARCH_MEMORY.md')
log_link = link('实际时间账',ROOT/'RESEARCH_LOG.md')

current = f'''<!-- CURRENT_STATUS_BEGIN -->
更新UTC：{stamp}。**S34实际执行、评分、两类不同作者数值复核、最终表述审和照片快照均已完成。新做800次Adam/反传，实际建一次旧地图、三次追加和三次原渲染；0次新网络推理。**

固定旧4帧预测后，新4帧平均深度相对误差：零步4.6059117%、自由400步4.3473826%、普通尺度约束400步4.3220763%。自由优化已提供大部分改善；额外尺度收益仅0.0253064个百分点，且帧7两个优化条件都略差零步。单个已见0.236秒窗口、给定GT相机，不代表独立场景或长期生成。

三条件地图616/651/650点及渲染确有变化，但渲染焦距也不同；候选均为0–7全部八张。最终默认选图、真实生成缓存及视频尚未运行。停止把已知尺度控制包装成创新，也不继续短窗扫参。

{report}；{bundle}；{memory_link}；{log_link}。用户快照220文件、219载荷SHA及98本地链接根核验通过；8张原始照片逐字复制，PNG实际查看。大数组仅本地链接，完整报告原字节另存，不冒充完全便携的数据包。

下一科学执行回到已有S20原生成基线：一张实拍→第一批四张生成→第二批四张生成，验证第一批的真实缓存是否实际进入第二批条件。尚缺项目验收的原VMem主权重与指定VAE；资源未齐备前不启动、不造缓存。{decision}；{resource}。遵循Supervisor02_Idea_Generation、idea-evaluator、本地Claude科学批判；新方法与PhD深度/CCF A质量目标仍未完成。
<!-- CURRENT_STATUS_END -->'''
for path in paths:
    if 'CURRENT_STATUS_BEGIN' in path.read_text():
        old = path.read_text()
        updated, count = re.subn(r'<!-- CURRENT_STATUS_BEGIN -->.*?<!-- CURRENT_STATUS_END -->', lambda _: current, old, count=1, flags=re.S)
        assert count == 1
        path.write_text(updated)

old_memory = (archive/'ROOT_RESEARCH_MEMORY.md').read_text()
memory = old_memory.split('## S30最新实际执行与交付')[0]
memory = re.sub(r'更新UTC：[^\n]+', f'更新UTC：{stamp}；北京时间=UTC+8。**S34真实800步、原地图/三次渲染、12行主评分、两类不同作者复核、最终报告与8照片快照全部完成。普通尺度额外收益小且候选不变，退出尺度创新叙事；下一原生成闭环受原模型组件缺项约束。**', memory, count=1)
memory += f'''| S34 | 强旧4冻结，800实际Adam/反传；新4 AbsRel零步/自由/约束4.605912/4.347383/4.322076%。原map/render变化、候选全部八张同；两类独立数值与交付核PASS。普通控制，非新方法/完整视频。 | docs/S34_RESULTS.md |

## S34已完成的实际链条与结论

输入为已见fr2_desk首8档案，约0.235880秒，给定GT光学相机。共同旧4来自S29 C2a零步/S21原4头，新8头来自S21 cut3r档案；不同源不称前缀字节相同。旧depth0–3固定，所有8个focal仍可训练；两臂57真实初态raw/decoded/objective一致。普通getter梯度修复和尺度约束不算创新。

主生产UTC21:38:49.004084–21:40:48.662662，外控119.658477秒。真实2MST/14PnP/800Adam/800backward/4clean/806objective、0新model。共同旧packet一次与两400臂均PASS，zero取自由臂保存初態另clean，无第三MST。正式contract SHA2c51a060a294a335c3844b04dc78028bd687b724266792ea89f1a6cb597cb465。主session54299、consumer44064、独立80493均已exit0，不重轮询或重跑。

消费者UTC21:42:05.220522–21:42:18.700442，外控13.479520秒；共同493个旧Surfel只建一次，三份完整深拷贝追加。新点123/158/157，最终616/651/650；原512×288渲染可见48777/50726/50334像素。原focal缓存4→12，均值402.08610535/406.63647970/405.87696075再乘.65；同外参不等于同内参，渲染变化不是质量证据。

原票权数值变化，但三组有序候选均0–7、quota每项1，因为n=min14,k且k8。默认NMS缺原len5历史/真实latent状态，最终context未跑。相同合法缓存、相机和NMS状态下相同候选通向同条件仅为源码条件推论，不是已生成相同视频或所有后续请求无效的证明。

120文件完整终态封存21:44:22.805906；主评分实际21:44:44.835389–45.809354，首GT字节21:44:45.451549才读取。固定新4×3完整12行/3均值，每组547012有效GT、239420无效GT、0无效预测。AbsRel .046059116645085774/.04347382601427406/.04322076250691019；RMSE .23858161931309185/.23202392161346547/.23083091088459334m；delta1 .9672805089812623/.9703837623471877/.9706103051722855。

自由对零步收益.2585290631个百分点，约束再对自由仅.0253063507个百分点；index7两400AbsRel略差零步。自由pair有效log均值最大漂移.3306571869却平均深度改善，漂移本身不构成失败/遗忘。收束all-trainable伤害外推与尺度创新叙事，不继续该短窗调参。

不同作者consumer保存量与fsum票权21:44:44.832850–45.375239实际PASS；深度/raw另式核21:47:54.677414–58.014601实际PASS，12行/3均值/57共同初態/228初末raw/各800优化梯度尺度保存记录/1600尺度边界，AbsRel/RMSE差最多1.39e-17/5.55e-17。保存梯度未重新反传；地图核未独立重实现renderer或Octree，不能称物理可见性验证。完整回执和SHA见{report}。

最终报告bbfcd5ae6e28da63a7e2bce072a9e4b7c34059bfde83b92e52bc3460ff774c2b，22门最终表述审PASS，work/S34_independent_review/final_claim_review.json。两PNG作者和root已实际view，PDF/SVG未另渲染；work/S34_root_preparation/visual_review.json。快照{PACK}，220总文件/219载荷40763051B，含manifest40871308B；8原照片/12CSV/全部800各类日志/3渲染。manifest f007ad26376a9a9d5551a12e5cc4fb2a47ccccc9d1e1c971cde1fe922804b104；root219SHA、13MD仅链接改写、98链接、8原图核PASS，work/S34_root_preparation/snapshot_review.json。38大数组仅本地链接；最终表述/根QA另在ROOT，不回改封存包。

## 唯一下一项与启动条件

{decision}已接受：回到原S20两批生成1→5→9，只有实际第一批generated ID缓存被第二批条件消费，才叫闭环。原576×576/T8/50步/context4/target4/seed42，两批同worker不重播种；两次原Navigator5°转向，原NMS在len5初始化；初图作者changi，不能借用S34八帧或假latent补状态。原数学保留，S33修正不偷偷带入原baseline。

沿docs/S20_MINIMAL_VIDEO_PROTOCOL_DRAFT.md；四真实原组件齐备且加载/源码/观察器身份审定后才能另行冻结。建议CPU8/FP32、每批1800秒/45GiB是未验证预算，不是保证。主VMem与原指定VAE当前没有项目验收的完整本地资源，{resource}区分公开元数据、网络失败与有限本地扫描；不能说全电脑不存在或MPS/CPU必然不支持。不要反复401/环境smoke/无意义代理，不孤立下载暂无法启用的大组件以代替科研。

## 旧结果、技能与环境

S30–S33详细记忆已完整归档：{link('本次修改前的完整记忆',archive/'ROOT_RESEARCH_MEMORY.md')}；逐阶段报告、原成功/失败目录和主账保持。S32/S33已完成16真实RGB新网络与累计2400Adam；S33三可用窗普通约束同时胜零步/k，缺pose窗全部NA，不能与S34混算新的独立实验。旧快照不覆盖当前主账。

Supervisor固定207bc6f7a1aa107e544099c2c7cc86816fba9628，通读59MD+70PDF页记录在既有reader目录；2.2强基线→失败→机制指导本轮反证。idea-evaluator否决已有尺度机制新颖性及短窗代理不能验证生成主张；Claude scientific-critical-thinking用于反例/焦距混杂/条件推断/证据边界；figure-designer用于完整轴与非实拍图标识。技能路径和具体应用见docs/IDEA_GENERATION_FOCUS_CURRENT.md，未调用Claude模型/CLI。

M3Max64GiB，无远程GPU；.venv-cut3r/bin/python为Py3.12/Torch2.7/NumPy1.26.4，科学CPU8/FP32，独立复算CPU1/FP64；overlay work/S17C_environment/site-packages。原512DPT3173761006B、SHA45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103，不重复下载/无理由重hash。绘图用既有HomebrewPy3.13/Matplotlib3.10.9，不改科学环境。

VMem39291e4f272f6b4f270691d930926ab5930f942e，CUT3R8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf；隔离源码work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R。原文件只读，修改通过冻结wrapper；祖先git覆盖HOME，不全量git add/commit。旧HTTP服务PID55105非实验，不动。14周proposal约前3周至第4周初交付成熟度，非工时；新方法/公平跨场景/生成闭环/最终论文演示仍缺，不标整个目标完成。
'''
# Keep stage table valid: insert S34 before the historical failure paragraph.
row = '| S34 | 强旧4冻结，800实际Adam/反传；新4 AbsRel零步/自由/约束4.605912/4.347383/4.322076%。原map/render变化、候选全部八张同；两类独立数值与交付核PASS。普通控制，非新方法/完整视频。 | docs/S34_RESULTS.md |\n'
memory = memory.replace(row, '', 1)
memory = memory.replace('\nS26原共同4', '\n'+row+'\nS26原共同4', 1)
(ROOT/'RESEARCH_MEMORY.md').write_text(memory)

latest = f'''# 最新科研进展

更新时间UTC：{stamp}；北京时间UTC+8。

**这轮真做了800步优化和三次原地图渲染，结果与独立复核都已完成。** 固定前四张照片对应的旧深度，再用后四张照片比较三种普通处理。

| 条件 | 后四帧平均深度相对误差（越低越好） |
|---|---:|
| 不优化 | 4.6059% |
| 普通优化400步 | 4.3474% |
| 加入已有尺度约束400步 | 4.3221% |

普通优化已经提供大部分改善，额外约束只改善0.0253个百分点，第八张照片还略变差。因此当前不能把尺度约束算作创新。地图和渲染确实变化，但三组候选照片仍完全相同；渲染焦距也不同，不能据此说视频更好。这里只用了一个已见短片段，且给定了真实相机。

**下一步回到完整生成：用第一批真正生成的图片，帮助生成第二批图片，检查缓存是否被实际用上。** 已有具体两批实验协议；当前缺可核实的原VMem主权重和原指定VAE，尚未启动。资源缺口与本机实际运行能力分开记录，不伪造缓存、不改用其他模型冒充原复现。

- {bundle}：220文件，8张原始照片、12行评分、两幅图、全部优化日志和复核回执。
- {report}；{decision}；{resource}。
- {memory_link}与{log_link}。

按照Supervisor第2章、本地Claude科学批判与idea-evaluator收束被证据削弱的方向。新方法和PhD/CCF A质量目标仍未达到；这一轮完成的是有真实证据的基线与问题排查。
'''
(ROOT/'docs/START_HERE_CURRENT.md').write_text(latest)
(WS/'最新科研进展.md').write_text(latest)
(ROOT/'docs/S34_NEXT_STEP.md').write_text(f'''# S34完成后的下一步

更新时间UTC：{stamp}。S34的实现、真实执行、评分、两类独立复核和交付均已完成，不再使用旧“待运行”计划作为当前状态。

{report}；{bundle}。

接受{decision}：普通尺度控制不是新方法，当前八张候选全部相同；不继续短窗调参或伪造合法历史。下一项回到[既有S20原生成协议](S20_MINIMAL_VIDEO_PROTOCOL_DRAFT.md)，真实完成1→5→9并验证generated cache实际进入第二批条件。

状态：NOT_READY_RESOURCE。原VMem和指定VAE尚未在项目内完成资源验收。{resource}。在完整原组件、最终加载适配与观察器协议就绪前不启动；未规定未来开始时间。资源未知不是已测计算不支持，也不以重复下载、smoke或代理实验代替生成基线。

原S34执行前文档已保存在{link('历史版本',archive/'ROOT_S34_NEXT_STEP.md')}；冻结contract和结果原件不改。
''')
receipt = {'status':'CURRENT_RECORDS_SYNCHRONIZED','utc':stamp,'archive':str(archive),'before':before,
           'after':{str(p):sha(p.read_bytes()) for p in paths},
           'scientific_reruns':0,'frozen_report_modified':False,'snapshot_modified':False}
(ROOT/'work/S34_root_preparation/current_records_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
sys.path.insert(0,str(ROOT/'scripts'))
from research_log import append_event
append_event('S34完整交付与当前记忆同步，接受回到原生成基线',
             '主执行/12行评分/两类独立核/22门最终表述审已PASS。根核219载荷SHA、13份仅改链接文稿、98链接及8真实照片，快照220文件。普通尺度额外收益0.025306pp且候选不变，收束创新叙事；下一原1→5→9缓存闭环需缺失原权重组件。归档并同步10份当前入口，不改冻结报告和旧实验。',
             evidence=['work/S34_root_preparation/snapshot_review.json','work/S34_root_preparation/visual_review.json','work/S34_independent_review/final_claim_review.json','work/S34_root_preparation/current_records_receipt.json','work/S34_next_decision/decision.md'],
             next_step='记录有界官方/本地资源刷新实际结果；原组件齐备后才冻结两批真实生成。',
             occurred_at=stamp,time_source='actual archive and current-document synchronization clock; prior delivery/review times remain in their receipts')
print(json.dumps({'utc':stamp,'files_updated':len(paths),'archive':str(archive)},ensure_ascii=False))
