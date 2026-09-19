# 当前科研记忆与接手入口

更新UTC：2026-09-06T18:47:09.566074+00:00；北京时间=UTC+8。**S31保存量诊断与不同公式完整复核完成：C2a初态5.03905%→原400步42.37947%→单标量恢复11.56681%；普通恢复有用但仍输零步。结束此四帧调参，下一步冻结其他消费者窗口的三对照。尚未选窗或运行S32；无新方法或完整视频验收。**

## 先读与长期要求

项目根目录是`/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling`；本任务工作目录`/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip`，outputs是给用户的日期快照。先读AGENTS.md、RESEARCH_PRINCIPLES.md v1.4、本文件和RESEARCH_LOG.md最新条目。阶段完整结果在docs/Sxx_RESULTS.md；当前完整交接docs/RESEARCH_HANDOFF_CURRENT.md。本次精简前的逐阶段详记完整保存在[历史记忆](docs/history/20260906T184709Z_before_S31_results/ROOT_RESEARCH_MEMORY.md)，没有删除历史证据。

用户是MSc新手，简单中文、本机自主推进、时间记录、每30分钟实查，Supervisor尤其02_Idea_Generation与本地Claude技能、多agent和原文检索。用Claude skills，不调用Claude模型/CLI。最终目标PhD深度/CCF A投稿质量，未完成，不能保证录用/导师反应。按强基线→失败→原因→方法；普通修复与已有组合不能改名作创新。没有发导师/他人消息授权。

`scripts/research_log.py.append_event`追加research_events.jsonl并渲染RESEARCH_LOG.md；补记用真实回执时间并注明记录时间。旧原件/失败/协议不改，不重复成功运行。实际最近流程检查2026-09-06T19:13:09.609502+00:00，间隔43.080940分钟，跨结束回合与本次heartbeat，超出30分钟如实记录；进行中下一检查不迟于2026-09-06T19:43:09.609502+00:00。

## 目前最关键的科学证据

| 阶段 | 实际结果及边界 | 完整记录 |
|---|---|---|
| S21/S22/S23 | 已见fr2_desk300帧CUT/TTT/FILT ATE8.254/2.848/1.858cm；278有深度配对/22缺失，完整300深度均值NA。全是已有方法。 | docs/S21_RESULTS.md–S23_RESULTS.md |
| S24 | fr1_xyz全798RGB→796配对/26.572059秒，CPU8/512DPT三法实际推理；ATE12.24063/9.68646/2.90258cm，8预定块FILT ATE较好，无灾难遗忘事件。7164行/6618pairs另式复核；图裁尖峰原FAIL保留，v2完整轴实际查看通过。 | docs/S24_RESULTS.md |
| S25 | 原VMem几何调用重放全历史并重置S/M；GA消费anchor self+后续other，不直接用raw camera_pose。state adapter60作者/92独立人工测试只是静态可用性，没做模型干预。 | work/S25_consumer_relevance/consumer_relevance.md |
| S26B | 真实新三法各400GA，原共同旧4导入历史。新4 AbsRel67.82589/93.54310/67.57302%；共同旧4已83.33823%。28行/40均值独立复核PASS。先查坏起点，不能直接归因记忆。旧focal使保存world点位变化，但0实际Surfel/cache/query事件。 | docs/S26B_RESULTS.md |
| S27/S27M | 保存量分析发现raw self不是全体GA实际输入，不准以4.4859%作公平优化起点。新1MST/3PnP/1backward/0Adam显示注册depth梯度断链；初始化与旧400终点逐位同。原断链发生在每次getter新ParameterStack；仅去detach仍不足。 | docs/S27_RESULTS.md |
| S28 | 匹配全部33初态的原A/修梯度B各真实400步；B梯度出现但AbsRel83.33823→87.47618%，loss更低。完整8行/800记录另式PASS。修getter只是恢复已知语义。 | docs/S28_RESULTS.md |
| S29 | 两零步初始化控制/2MST/6PnP/0Adam/0GT：s0=.1731799841按比例缩小全部局部深度，公共R/t相消；23检查及另一公式全786432点PASS。单位尺度不等于训练期固定尺度；S29当时未评分，S30之后评分其封存初态。 | docs/S29_RESULTS.md |
| S30 | C2t/C2a都修getter，各自33raw/深度/目标与S29逐字匹配，真实800Adam/反传、0新网络。C2t83.33823→87.47128%；C2a5.03905→42.37947%，原loss均显著下降。16行/66raw/800记录不同作者完整PASS，两图实际查看。 | docs/S30_RESULTS.md |
| S31 | 每臂一个自身初态全像素k，D*=kD400后评分。C2t84.05310%，C2a11.56681%，都仍输自身零步。8新行/2均值+原16行导入；0网络/GA/MST/backward，另式完整复核PASS。 | docs/S31_RESULTS.md |

S26原共同4已跑400步但独立clean参考12像素失配导致FAILED原件保留；新FP32dense参考全字节一致只许可IMPORT_VALIDATED，不追认PASS。S26B首次启动缺显式importlib.util在数组前失败保留；只补标准库bootstrap的第二次启动成功。S22原生CPU RoPE精度失败、S24原裁轴图、绘图环境失败均保留。不要把修复后的新产物覆盖历史失败。

## S30最新实际执行与交付

实际18:12:29.415572–18:13:32.552760UTC，63.137115秒，work/S30_launch/receipt.json PASS，session78388已exit0。正式合同work/S30_scale_optimization_preparation/contract.json SHA000fa5d5b19cc516a581b382e457dcf8e03494da50b220d8f32c0ad0b16224a3。每臂400原Adam/.01/linear，1MST/3PnP/1clean，403objective含3次无更新观测；相机/pp固定，depth/focal/pair pose原声明可训练。全两端点封存后评分，共同GT相机显式oracle，不是完全无GT实验。

独立保存量复核18:21:29.386122–31.143825UTC，16完整评分/16组浮点/8差/66raw/800记录，AbsRel/RMSE最大差2.22e-16；梯度范数来自记录没有重算。work/S30_independent_numeric_review/receipt.json；session29860已exit0。

WS outputs/S30_优化损坏准确起点的真实证据_2026-09-07，90文件/89载荷7778316B，4原始实拍、两图、完整16评分与800步。manifest SHAb3e920ba3c0404f5c34389291576d20f091223a355f5b96839ab717de72cfeb9；作者68链接/root89载荷SHA核通过。图作者/root实际view PNG；PDF/SVG未单独栅格渲染。S28/29历史快照保持。

## S31已完成的精确边界

正式合同work/S31_scale_shape_preparation/contract.json SHA85d535ca913ed5a913cd259070bacd8b316a34e40aef1a55dd5043303b5f2587，runner94f7678f，protocol6c035724。不同作者源前审work/S31_independent_pre_review/final_pre_review.json SHA616c4f896091df2c747aa2c23de2b9d97f0ed4633d1664aa104659c7651b8793。每臂固定FP64 v=logD400-logD0，k=exp(-mean_all(v))；无逐帧k/shift/GT拟合/掩码/挑步。两臂D*先封存才原四GT新评分。不是优化器内部gauge控制，也没有拼接旧world/pair冒充新消费者。

实际主计算18:39:38.377241–39.991019UTC/1.613648秒；外控2.064877秒/RSS161890304B。root独立式18:39:40.439971–41.224466UTC/.784328秒；外控1.033285秒/RSS147668992B。CPU1、180s/2GiB两阶段实控。work/S31_execution/dispatch_receipt.json PASS；session91126已exit0，不再轮询。

C2t k1.2728267635863444，AbsRel.8405310395783584、RMSE1.7358592534233022m、delta1.000003668809251269408；C2a k1.5505380808239486，AbsRel.1156681167701237、RMSE.3674165247915667m、delta1.920872098614643。相对自身初态AbsRel分别恶化.007148738755245243/.06527761892375104。两组各validGT540363/missing246069/invalidPred0。

相对初态log-change平方和公共/帧间/帧内占比C2t82.979993/.645462/16.374545%，C2a85.683393/.110465/14.206143%。这是log变化分解，不是GT误差解释率、真实三维形状毁坏或已证尺度根因；没有新增D*==D0二元纯比例门。

root参考work/S31_root_numeric_review/recompute.py SHA42e2314f010e6d04a880a15d8a05bf342b13a8f92b599e6bc97bcad270532365，标量log(b/a)+fsum/原始矩，与作者log差/中心平方和独立；全1572864像素v/D*、92代数量、新8评分/2组/16差/CSV通过。D*最大差0，v最大4.72e-16，AbsRel1.11e-16、RMSE4.44e-16；不重复原16端点评分/历史梯度。完整docs/S31_RESULTS.md；WS outputs/S31_尺度恢复后仍输给起点_2026-09-07快照46文件/45载荷2357454B，4原始RGB，manifest SHA1b5f0575a336d9f881738d670f0661d20e6dd0118c50e4d20c8bd3db09634128；作者45链接/root45载荷SHA及源报告核验通过。

## 下一决策：换窗口验证，结束本四帧调整

保留零步、原400步、单比例恢复三普通对照，必须共享一个预定的实际消费者起点，不混入未被消费的raw self头。先在预定其他窗口确认旧4起点/优化失败，再决定old4→new4完整链条。下一项先做时间/pose元数据与预算冻结，禁止看新目标分数选窗；记录不重叠规则、允许输入、已有RGB/GT暴露状态。已见场景的新窗口也不能冒充盲测。尚未选择实际窗口、创建S32或开始新运行。不同作者结果后判断work/S31_next_decision/review.md已完成，优先固定C2a规则为三对照共同起点，C2t历史完整保留，不按新结果更换主起点。

本轮Supervisor第2章、idea-evaluator与Claude科学批判要求从被基线解决后剩余问题提炼方法。work/S30_next_decision/critique.md有完整原文近邻及停止规则。官方DUSt3R ctor注册depth/getter直接exp，known-pose也norm_pw_scale=False：S28是已有梯度语义，不能称VMem独有漏尺度约束；上游norm=True的.5不是米制答案。work/S29_upstream_baseline_comparison含固定官方源码与边界。MapAnything/TCO/Eigen2014已覆盖尺度分解/先验等普通思路，泛门控、相机条件、反馈环或重积分不足以认定新意。

五路初轮idea cards work/S23_innovation_*均完成且未成立新方法；Supervisor reader已读59MD+70PDF页，固定207bc6f7a1aa107e544099c2c7cc86816fba9628。具体应用docs/IDEA_GENERATION_FOCUS_CURRENT.md，不以读手册/agent数量代替实验证据。

## 环境、完整生成与proposal缺口

M3Max64GiB，无远程GPU；.venv-cut3r/bin/python为Py3.12/Torch2.7/NumPy1.26.4，科学CPU8/FP32，S31保存分析CPU1/FP64。overlay work/S17C_environment/site-packages；原512DPT权重3173761006B SHA45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103，不重复下载。图用既有HomebrewPy3.13/Matplotlib3.10.9，不改科学venv。

VMem commit39291e4f272f6b4f270691d930926ab5930f942e；CUT3R8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf。实际几何隔离源码work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R；阶段patch通过冻结wrapper生效，不把未改的原文件宣称已永久修复。祖先git覆盖HOME，不全量git add/commit。

完整VMem视频未执行，原主权重gated/VAE缺口仍在，work/S25_official_resource_recheck记录官方有限核查；未申请个人访问/登录/擅自替换未知权重。此缺口不阻止本机消费者研究。14周proposal交付成熟度约前3周到第4周初，不是工时；新机制、公平跨场景、生成闭环、最终论文演示仍缺。
