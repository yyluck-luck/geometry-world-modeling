# 当前科研记忆与接手入口

更新UTC：2026-09-06T15:29:11.857427+00:00；北京时间=UTC+8。**S23与五路首轮已完成；S24正在真实运行：CUT3R与TTT3R均全796帧PASS，FILT3R运行中。** 最新实时状态见各方法receipt。最终目标仍未达成。最近目标轮分类progress：实际新基线、代码/消费者证据、用户第2章重点落实均有产物。


## 用户目标与不变原则

用户是希望读博的MSc新手，要求本机自主持续研究、中文说明、时间记录、每30分钟实查、Supervisor与本地Claude skills、多agent/检索。最终目标PhD深度与CCF A类投稿质量，当前未达到，也不保证录用/老师反应。优先强基线→真实剩余失败→方法。不得无故重跑成功阶段；不调用Claude模型/CLI、不发导师消息、不替用户提交个人资料。

先读[原则](RESEARCH_PRINCIPLES.md)、[质量要求](RESEARCH_QUALITY_TARGETS.md)及[笔误勘误](RESEARCH_QUALITY_TARGETS_ERRATA.md)，再读最新RESEARCH_LOG.md与[完整交接](docs/RESEARCH_HANDOFF_CURRENT.md)。追加账本research_events.jsonl通过scripts/research_log.py写，日志为其渲染。workflow_checks.jsonl最新实际检查15:14:50.033545UTC，距上次27.430分钟；历史曾31.431分钟稍超，记录保留，均不称定时触发。

## 真实基线与结果

- S21/S22：同一fr2_desk已见300帧CUT3R/TTT3R/FILT3R真运行及轨迹评分完成。位置RMSE 8.254/2.848/1.858cm；都是已有方法。FILT原生CPU4帧兼容失败保存，一行RoPE精度控制后24头完全相同才跑300。原evo+不同矩阵公式通过；不能称外部复现。详docs/S21_RESULTS.md、S22_RESULTS.md。
- S23：0新模型；复用3×300已保存真实几何头。278张深度配对、22缺失，完整300主均值NA。278帧描述AbsRel CUT4.6235%/TTT3.2608%/FILT3.0618%；平均逐帧RMSE .392691/.325125/.340982m，勿与pooled RMSE混用。
- S23事后分层：>8m传感器记录占1.027%有效像素、FILT平方误差60.221%。未剔除这些像素，未证明传感器错误或记忆遗忘。轨迹GT尺度用于dense depth反而更差；逐帧GT尺度只是oracle。DPT同帧头闭合不等于跨帧一致性。
- S23运行25.49秒外控、峰720MiB；900帧次固定网格不同公式复算通过；另一作者完成执行前审查，并非外部团队数值复现。报告docs/S23_RESULTS.md；三幅已实际查看图在work/S23_reporting，真实照片例为frame220。

## 手册与五路创新

用户最新要求重点关注02_Idea_Generation。根本轮重新全文读2.1/2.2/2.3；原则v1.4，具体五维矩阵/10重要问题/下一步见docs/IDEA_GENERATION_FOCUS_CURRENT.md。普通缓存仅工程对照，消费者改进才是科研主轴；不把手册经验工时当用户实际投入。

一名reader已通读12个SKILL、18篇中文handbook、28参考、README及70页PDF，59MD+1PDF；126其他文件只索引。commit207bc6f7a1aa107e544099c2c7cc86816fba9628。详work/S23_supervisor_readthrough/audit.md。阅读与执行范围分别写明；用2.2实验路线、2.3构思和idea-evaluator反证，不机械套不相关规则。

五路首轮全完成：[根任务决策](docs/S23_INNOVATION_ROUTES.md)，原卡work/S23_innovation_1_state、_2_geometry、_3_generation、_4_occlusion、_5_budget。没有已验证新方法。优先状态/pose-memory因果诊断，但先等更完整自然基线；普通几何一致性和mask重编码方向降优先；生成分支组合需真实生成资源；预算关系需先证明自然回访/淘汰事件。不能把S23远点尾部同时解释成这五个故事。

## 当前运行：S24

本地TUM fr1_xyz全798RGB，796严格20ms一对一GT配对，26.572059秒；早期用过此场景，非盲测。候选与独立timestamp复核已完成，未做新GT数值评分。脚本scripts/s24_baseline_expansion.py、协议docs/S24_BASELINE_EXPANSION_PROTOCOL.md；评分器由另一agent完成，26个人工构造检查通过（非真实实验）；独立前审23项通过，绑定37文件。已于14:26:28.111951UTC冻结SHA95b2c749fddefc432472b0aae56c1602fb3110940a86fedc5047b201049924b7；14:26:33启动dispatch，统一exec session53980。CUT3R→TTT3R→FILT3R→评分连续执行；进度在results/S24_baseline_expansion/{method}/receipt.json与work/S24_execution/{method}/receipt.json，不重复启动。每方法3600秒/48GiB，全部封存才评分。不要因看到旧结果调参数。

## 环境与原生成主线

M3 Max64GiB、CPU8，暂无远程GPU；ROOT .venv-cut3r/bin/python为Torch2.7/NumPy1.26环境，work/S17C_environment/site-packages含evo/Matplotlib。原512权重data/cut3r/cut3r_512_dpt_4_64.pth完整，3173761006B，SHA45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103，不重下。

完整VMem视频仍未执行。公开512与嵌入几何成功不等于生成。最新现有HF登录元数据读取在14:00:17UTC因LocalTokenNotFoundError失败，未发认证HTTP/申请/下载；原主权重gated、原VAE资源缺口未解。work/S23_generator_access_followup/receipt.json。没有新的公开视频结果。

## Proposal与历史

原14周proposal：1–3文献/基线、4–5失败分析、6–9方法、10–12评估、13–14交付。目前交付成熟度约前3周到第4周初，非实耗工时；创新方法与生成闭环尚缺。

此前S0–S22完整记忆保存于[历史原件](docs/history/RESEARCH_MEMORY_before_S23_2026-09-06.md)，未删除旧证据。全部路径、失败/纠正、旧阶段均见完整交接与追加主账；工作区outputs为快照，不能覆盖更新的主账。祖先Git覆盖HOME，不全量git add/commit。

方向1的完整state捕捉/四动作分支静态准备已完成，详下方S25；目前在准备S26消费者pilot。S25没有冻结、没有模型运行，当前不得读取S24 GT或按部分结果改方案。

## S25最新：源码与静态准备，不是实验结果

完整state四臂adapter已完成，work/S25_state_intervention_preparation。最终SHA c5467552a8801e675f52ad1c5a74d6994831d43ef815265a2433a7c4142233c3；60个作者标准库检查、92个最终独立小型检查通过，后者只有36输入tensor元素+3runtime元素、约203MiB、0模型。原training flags、signed RoPE及绝对索引边界均修正。真实连续/恢复兼容仍未验证，S25没有冻结/运行。

更重要的消费者审计work/S25_consumer_relevance/consumer_relevance.md：原VMem每次几何调用从头初始化S/M，但重放全部历史，不是仅4参考+4新帧；返回state_args只可选viewer使用、不传回主pipeline续接。GA不用raw camera_pose，也不直接用非anchor self-depth；真正目标是anchor self/conf_self、后续other/conf，在给定相机和旧depth冻结下优化并重建最终几何。M可经pose_token影响other头，只是结构路径，尚无收益。原S24自由ATE不能直接验收proposal。根已独立读取pipeline、wrapper相关调用核对。

S26仅准备实际消费者baseline计划/adapter，work/S26_consumer_baseline_preparation（agent进行中）：拟重放已有S21/S22头，原GA给定共同相机和共同旧depth，比较被实际消费的量；先小组件兼容，再扩展，0新执行。不能把共同GTdepth喂成旧depth，不能把小pilot当完整生成结果。

## S24后续依赖链

多时间跨度诊断已在14:55:37.741709UTC冻结：work/S24_horizon_preparation/run_manifest.json SHA2383042f75ceea9f8aa9f1645acf3e8f038ad5c332f1a7684080ae152a7a4460。全796起点、相邻/1秒/5秒，Decimal时间、无末端则NA、1秒分箱，不重新对齐/不自动选事件/无失败阈值。独立静态前审PASS；38人工SE3检查不是实测独立复算。

主S24 dispatch仍session53980，PID15300/creation1788704793.197378。依赖后处理session20829在运行、等待该实际PID及完整dispatch PASS，之后自动运行horizon与scripts/plot_s24_baseline.py；不重复模型。合同work/S24_postprocess/contract.json和receipt.json，单次依赖job不是新heartbeat。最终应COMPLETED_PENDING_VISUAL_REVIEW，必须实际看4张结果PNG后才能交付图的视觉QA；尚未有S24分数或图。不要改被冻结控制文件，否则后续会正确拒绝。

## 完整生成资源最新

work/S25_official_resource_recheck核作者当前README/项目页/HF metadata，未发现新官方公开替代入口；主权重仍gated=auto、同revision和5,056,346,672B身份。7个小URL、31,242B、4TLS EOF保留，没有权重下载/认证/申请；旧401没重复。资源缺口未解决，但本地消费者/基线工作可继续。

## S26当前执行准备与后续排重

2026-09-06T15:29:11.857427+00:00：原消费者pilot的adapter/plan/source准备完成；root已写scripts/s26_consumer_baseline.py及docs/S26_CONSUMER_EXECUTION_PROTOCOL.md。metadata候选manifest SHA2af4f8bb13caee8923ce180e0dcc02bb2a6538b3a3c0f87684bd8db33af0dccf，565源/控制文件和5523依赖身份；尚未正式冻结或执行。独立agent最终前审进行中。

共同8个GT相机显式当输入，共同旧4depth仅由original4原GA产生；新4主表，旧4不混主均值。四个400步GA计划，0新网络前向；必须S24完整dispatch PASS后再启动。21项CPU1/spy接口检查、评分作者58人工检查、root22人工公式/封存顺序检查完成；都不代表真实GA/效果，范围与各自代码SHA见work/S26_runtime_preflight和S26_root_review。GT深度逐PNG身份从既有S23 seal继承，准备未重读GT。

近邻跟进work/S26_consumer_novelty_check已核5篇原方法：G-CUT3R/Pow3R/MapAnything/TCO/RayMap3R。普通相机条件、相机loss反馈或ray门控不足以成为新方法；TCO为重要直接排重项。保持实际消费者自然失败问题待测，没有新方法成立。
