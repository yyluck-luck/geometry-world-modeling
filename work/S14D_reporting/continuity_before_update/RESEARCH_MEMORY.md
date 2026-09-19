# 当前研究记忆

更新：2026-09-06 15:08:43，北京时间。S14C真实档案诊断与不同算法复算完成；结果不支持当前“分散越大、选图越差”的限定设想。成功S13/S14A/S14B/S14C不重跑；新方法效果与完整视频仍未证明。主账优先。

## 每次接手先读

- 本目录AGENTS.md、本文件、RESEARCH_LOG.md最新条目；完整路线为docs/RESEARCH_HANDOFF_CURRENT.md，当前工作区根目录也有研究交接总览_2026-09-06.md。用户是新手，用简单中文解释问题、实际行动、证据、下一步。
- 主项目 `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling`；用户交付快照 `/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/`。主账优先于快照。
- M3 Max、64GB、CPU/MPS；没有远程GPU/CUDA。不重复下载已有约3GB CUT3R权重，不重跑成功S4–S14B；本地没有完整VMem生成证据。
- 用户授权自主研究、本地工具/网络检索、多agents；用HKUSTDial/Supervisor-Skills和本地Claude技能说明，不调用Claude模型/CLI。不能发导师消息、代填个人信息申请或虚构会议/课程完成。上层Git含家目录，不全量stage/commit。
- 保留原proposal、失败目录、冻结文件、旧报告和ZIP。先前长记忆另存work/S14A_handoff_update/RESEARCH_MEMORY.md；完整历史在追加账本和各阶段docs，不以旧“下一步”覆盖本页。

## 目前最重要的证据

1. 真做过模型实验：S6与S8各三段、每段20历史+4查询的真实RGB输入，CPU运行CUT3R有保存输出与metadata。S6北京时间09-05 23:44–23:45，S8 09-06 03:43–03:44。这里是预训练几何推理，不是新训练或视频。原图在data/tum，用户照片入口outputs/独立场景验证/真实照片_72张和outputs/实验用的真实照片_72张。
2. S7/S8来源/位置因素效果依场景改变。S8主A0P0/A0P1/A1P0/A1P1支持80.281293/80.281293/80.798944/80.817906%，原S7具体模式未重复；几何误差和支持可反向。S8只是另一个物理场景，不是更广泛化；发布模型训练未接触TUM没有证明。
3. S10工程优化约7.78倍只限既定CPU渲染组件与24已见查询，非新方法/视频速度。S11地图192相关条件和30人工来源编辑验证实现，不能冒充新独立场景。固定查询缓存B暂停，不恢复无实际调用收益的故事。
4. S12同14候选数、同4输出、相同NMS；来源14减姿态14：S7test−2.3389606843pp，S8test+4.3829196654pp。两方都有预测几何，非有/无几何对照，也不同计算成本。全部24相关已见查询，192配对行不是192独立样本。数值独立审计23647项通过。
5. S13事后oracle已完成并独立164328组合复算：24已见query，来源14/姿态14/全20各选四，72最优摘要和48当前分数精确。S7test来源池余量2.732103pp、姿态池1.593045pp；S8为6.349001pp、10.053341pp。Oracle借用实测答案且放松NMS，不是纯排序/NMS损失、可部署收益、创新或视频证据。原冻结52输入漏直接绑定设计中的S12 summary/独立审计；事后补核不修复事前合同。原环境与结束源码身份未保存，保留范围限制。首次默认目录冻结路径失败在解码前，V1/失败目录不删。
6. S13结果/48行CSV/6分层图完整，1707项不同作者成稿核对；PDF字体类型警告保留，独立渲染无可见缺陷。S12旧回执MD哈希勘误另存docs/S12_MANUSCRIPT_HASH_ERRATUM_2026-09-06.md，不改旧ZIP。S13交付93载荷94成员3705054字节，ZIP SHA31c3e0654ff80d010320201d9f44121aa667c302d727d93bee866a79f558b2a6；只验证归档，不冒称新机执行。

## S14当前：数据准备已完成，方法价值未证明

- 12搜索、3问题组、5直接近邻+2背景、7原文快照见docs/S14_INNOVATION_CANDIDATES_REVIEW.md及work/S14_innovation_review。C1为相对姿态回退的受损风险，C2为跨图冲突；只允许前置诊断。COVRAG/I3DM覆盖、LayerRecall状态路由、LTT风险控制、传统MVS一致性都有先例，普通组合不是创新认证。
- 先前403中断的正式审读已由不同候选作者完成，见docs/S14_FORMAL_METHOD_REVIEW.md与work/S14_formal_method_review/review.json。C1只是普通监督门控；C2未操作化，均为有条件前置诊断。初稿误将原作者未提出的15列C2版本作CRITICAL裁定，根提出后改为真实候选F6 MAJOR；旧MD/JSON保留。旧docs/S14_REVIEW_CONTINUATION.md是历史状态。必须同信息、同GT监督、同模型容量普通门控强基线；先计算两方案再路由需要算总成本，不是同14信息预算。场景级独立假设/校准精度/未见测试不可跳过。
- S14A于UTC04:13:05.778786冻结，manifest SHA199ad23c8f0d24ea52e33356c69e60078df097c365c3395200b83e67e7a422f1；实际04:13:34.920590–04:13:34.963716一次完成。30评分前JSON、24行15特征+6元数据、288条已存pair来源使用，源码SHA1dff7df7acff1ac565fb103968495a37a34dff0b94c51c24499406beaf62c005。没有GT/评分/NPZ/原图读取、拟合、选图或模型运行。
- 不同提取器作者的root独立实现于04:13:41.266316–04:13:41.284597重算360值、CSV和来源通过；最大差2.220446049250313e-16，预定门1e-12，整数/ID/保存gap精确。源码/manifest/30输入前后未变，调用者另核10控制项。见docs/S14A_RESULTS.md、results/S14A_prediction_features、results/S14A_independent_verification。准备文档保持历史运行前状态，不事后改写。
- V1预审拦下FP32差值误拒，随后混合符号零缺陷也在真实提取前修复；旧源码/阻断报告保留。28项人工测试不等于真实效果；最终V2不同作者前审通过。提取器Python3.13.0标准库，核验Python3.12.14/NumPy2.3.5，不改成功源码。
- 24查询仍已见且相关；阶段/块/query等仅元数据，禁止进入学习特征；query姿态依赖已见query RGB，不等于生成前只有轨迹的部署接口。正式方法审读与S14B测量已完成。下一步需独立定义分散量是否帮助发现选图失败的探索协议及普通来源数/相机分散等基线，并补新场景身份和配准；未通过就收束诊断，不能靠包装普通门控凑创新。

## 最新场景与测量决定

- docs/S14_SCENE_AND_PRECISION_PLAN.md：TUM不同序列可能同房间，fr1办公室/fr2大厅均设计已见，fr3身份待核，新增合格校准/测试组为0。7-Scenes仅替代入口，房间独立性/RGB-depth配准/训练接触未知，不下载前先核许可和评价接口。6新组2/2/2仅条件性诊断预算；不能以小样本给窄风险保证。根另复算28项公式数值，非效果实验。
- docs/S14_MECHANISM_INPUT_AUDIT.md：15列未含直接冲突；24份观测/事件/A0P0地图/来源文件身份已核，复用12旧header，未解码数组或事件JSON。分散可能来自曲面/密度/匹配筛选，不直接叫错误。均值位置天然最小化同组平方残差，不能拿此证明真实改进。
- S14B已完成：设计文档保留DRAFT历史状态，由docs/S14B_EXECUTION_MANIFEST.json于UTC05:51:52.726840启用，SHA58a4b2a9a102a05eac91a3b5c403d4366343d5feefb3ddfb1093d1e72b97f7c1。生产60c5fe173ef1c0dea213ec4cb3cf2c79fd7963b50782c0ed825fdbef2ad5145b、独立核验de4cb9652d84c89eddc12b6dc70298f1df7253b5c4b6ddb6856ca51de6b7bcc6及25控制/24输入均已冻结并前后核身份。
- results/S14B_observation_disagreement于UTC05:51:59.074424–05:52:00.674630单次SUCCESS：24输入8,926,362字节、12NPZ/42数组/12JSON、6块/88,088观测/16,164点/64,896点帧组。CPU档案测量1.600312秒、RSS182,059,008字节，不是模型或视频耗时。
- results/S14B_independent_verification于UTC05:52:28.886440–05:52:30.099798 PASS：不同作者dict/math.fsum实现，1,983,074精确和472,500浮点检查；maxdiff8.348877145181177e-14，门atol1e-12/rtol1e-10未变。输入/控制/源码/manifest和生产文件前后身份均通过。准备35人工检查不是实验样本；两作者各读同两份结构JSON，准备真实数组0。
- S14B仅固定事件预测分散：7,397单来源点四量全零，8,767多来源点B>0，只说明非全零退化，不能说真实错误/实用信号。全部116非空m层见work/S14B_reporting/all_m_strata.csv；六块仅两个已见场景，计数不是独立样本。D=B+A是恒等式；未读GT/query/评分/特征、未拟合/选图/运行模型/视频；不代表C2联合冲突新机制已成立。见docs/S14B_RESULTS.md。
- 本轮研究决定汇总docs/S14_RESEARCH_DECISION_2026-09-06.md。原S14A和全部旧ZIP保持不变。每次新数据/特征实验另立协议，不能因正式审读完成就跳过执行合同。

## 技能、交付与定时接续

- 已实际应用Supervisor idea-evaluator、tech-paper-template类型分流→benchmark-paper-template，论文仍NOT READY；Claude scientific-critical-thinking/brainstorming用于反例与证据分级。figure-designer、Matplotlib、PDF独立渲染用于S13；历史Draw.io、XeLaTeX产物保留。本轮不机械调用无关技能、不造实验照片。具体见docs/SKILL_APPLICATION_AUDIT.md与S13_RESEARCH_SCOPE_AND_SKILLS.md。
- outputs/完整研究路线与交接提供路线、全量日志、当前记忆、机器账本、docs快照、当前源码和S14A证据；输出是有截点快照，后续主账优先。outputs/四图选择上限诊断为S13独立交付。
- 原automation已改为每30分钟科研流程检查与接续，ACTIVE、同一任务。按docs/RESEARCH_WORKFLOW_CHECKLIST.md核七项，追加workflow_checks.jsonl和主账后继续实质工作。默认重要变化通知，可选提醒偏好尚未回答。电脑和应用需运行，设频率不代表历史准点执行。首次记录是手动检查，不冒充heartbeat触发。
- 原课程完整VMem基线、视频验证、真实导师活动/工时/最终提交仍有缺口，见docs/PROJECT_DELIVERY_TRACKER.md。不能把本轮输入整理或归档完成标成整个科研项目完成。

- 最新完成审查docs/S14B_COMPLETION_REVIEW.md已PASS：102组机器合同检查、3,442项报告/116层转写核对；不冒称第三次几何复算。m=2因出生质心等于锚点，A=B、D=2B是代数依赖，不能作独立新信号。

## 最新S14C：真实数据离线诊断取得负结果

- 执行合同docs/S14C_EXECUTION_MANIFEST.json在UTC06:52:49.413572冻结，SHA f7ff9711c41954d057c01045bfb1a1fcfe4c1babc85b1c6e1a0d3d8d7f76403e。32预测输入、1旧评分、31控制与manifest共65文件，三个实际调用前后身份未变。
- UTC06:53:09.787438–06:53:10.696581实际读取2CSV/30JSON，计算24个已见相关查询的四图分散差和三普通基线；64,656点访问、10,743共同点访问、60,435来源pair访问。先封存预测量，UTC06:53:32.064848–06:53:32.204587才关联S12旧实测评分。没有新模型、训练、选图、GT重新评分或视频。
- UTC06:53:38.596394–06:53:39.500164不同作者/不同公式复算PASS：803,179精确、82,684浮点检查，maxdiff7.105427357601002e-15，预定atol1e-12/rtol1e-10不变。见results/S14C_independent_verification/verification.json。
- 主量为相同共同点域中G四图减P四图的来源质心分散；G来源规则、P相机位姿规则。结果变量为G相对P损失的实测支持百分点。S7 scene rho=-0.30434782608695654、S8=0.05913123959890826，否定预先规定的“两已有场景都正相关”有限命题；不据此否定全部几何方向。
- 全24行和8组×4量的32相关都保留，无合并两场景相关、拟合或阈值。13个常量组的rho未定义不是0；7行G=P。S8每块历史四图分散恒定而查询效果变化，block1甚至优劣变号，说明当前历史代理缺少目标视角信息。不能翻转符号/调权/筛query来挽救本代理。
- docs/S14C_RESULTS.md、work/S14C_reporting/all_24_queries.csv、all_32_correlations.csv与figures/s14c_all_queries.png/svg提供全部结果；图无拟合/抖动/删点，重合点如实重叠。
- 准备期人工CLI漏传root，误读取1份真实预测JSON字节用于SHA后即停；真实JSON解码/评分/数值行0。原错误“读取0”回执保留，另存scope_correction.json。后续纯人工集成通过，不计作真实实验样本。
- 新场景核查docs/S14_NEW_SCENE_IDENTITY_AUDIT.md：7-Scenes原版配准不能直接接本评分；fr3物理房间关系未知；Bonn static_close_far是具体候选。根两次HTTP范围请求读493,422字节ZIP目录，独立核3,508成员字段；没有新图像/GT成员内容/全包下载，不能记作新场景实验。见docs/S14_BONN_METADATA_ACCESS_RESULT.md。
- 下一项实质工作：单独定义目标视角可见性/遮挡测量，与普通覆盖、重投影/MVS和相机基线比较；先冻结新协议，再做明确增量诊断和新场景准备。不是已认证创新，不重复本次成功计算。旧章节的S14B“下一步”由此替代。

- S14C完成审查PASS，5,826项身份/转写/图范围核对，另有实际PNG视觉检查；未重跑数值。见docs/S14C_COMPLETION_REVIEW.md。
