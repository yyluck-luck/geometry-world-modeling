# Proposal研究进度与导师汇报入口

<!-- EXPERIMENT_NAME_LEGEND_20260912_BEGIN -->
> **S编号与具体试验名称说明（2026-09-12更新）**  
> 文档中的 `S86`–`S90` 是项目内部阶段编号，保留它们是为了让结果、日志和回执可以追溯；括号内是给新读者看的具体名称。编号不是论文术语、结果等级或“实验成功”的标志。S88–S90主要是数据资格/传输与协议审查，不能误读成模型性能实验。
>
> - **S86（单场景四目标几何条件注入基线实验）**：在一个已见静态场景、四个相关目标上，比较历史几何注入方式的真实生成链和RGB误差。
> - **S87（末端引导强度控制与多步引导必要性反例实验）**：复用S86缓存，比较末端处理强度与持续多步引导；它只检验该已见场景的有限反例，不验证GRC或长期几何收益。
> - **S88（RTMV相机JSON元数据与静态投影数据资格检查）**：核对归档身份、相机元数据和可访问的静态文件头；不是RGB-D配对性能实验。
> - **S89（RTMV配对数据TLS接续失败审查）**：记录两种TLS/传输接续尝试及其失败边界；失败本身不等于数据缺失或科学负结果。
> - **S90（RTMV归档配对数据恢复与索引协议审查）**：检查受限Range传输、归档成员身份、断点恢复和索引安全条件；已恢复的512B文件头不等于取得可用深度正文。
>
> 后续报告首次出现编号时应同时写成“**S86（单场景四目标几何条件注入基线实验）**”这类形式；后文可使用编号，但不要只写编号来替代试验名称。
<!-- EXPERIMENT_NAME_LEGEND_20260912_END -->

## 本轮实际复算：S91R（已保存历史候选与未来深度误差回顾性复算）

在没有新网络和新模型调用的情况下，对既有 S15B old/new 几何候选、目标预测和传感器深度执行固定公式复算。几何相对不一致度与目标 AbsRel 在 `never` 与 `all_new` 保存输出上均为正向描述性相关；32个 method×target×source 组合由独立脚本复核通过。该结果只是一段已暴露 TUM 数据的先导信号，不能当作未见测试、跨场景证据或 GRC-Memory 验证。

正式的 S91（未来几何风险增量预测试验，GRC-Pilot）仍需 Gate 0 通过后，在相同候选池、相同预算下与 recent、random、pose-distance、coverage、utility-only、confidence-only 和 WORLDMEM式记忆基线比较。



更新时间：2026-09-12 14:55（Asia/Shanghai，时间来自 current clock）。这是对当前 proposal 的状态更新，不是完成度百分比，也不是论文录用判断。

## 可以说已经完成的部分

1. 明确了 proposal 的研究问题：长期、多视角和遮挡下，历史几何信息是否帮助世界模型保持未来空间一致性。
2. 完成 S86 局部真实基线：一个已见静态场景、四个相关目标，完整生成链和 RGB MSE 已保存。
3. 完成 S87 末端强度控制及独立数值复核：普通末端处理在该场景取得 MSE 0.05116758，低于旧持续引导的 0.05242222；target22 变差，重影仍在。
4. 完成 S88–S90 数据访问和协议审查：已取得相机元数据及一个 `00134.depth.exr` 的 512B tar 头，仅证明受限传输成功；未取得 RGB/EXR 正文或配对未来真值。
5. 完成 GRC 候选的近邻和数学审查：GIM-World 等工作已覆盖几何记忆、信息增益和固定预算的部分组合；原先逐条风险上界、直接 CRC 保证和通用 1−1/e 表述已撤回。
6. 完成两个 Agent 产出的导师稿草案和创新下一步门草案：相关文件在 `agents/advisor_oral_brief_20260912.md` 和 `agents/innovation_next_gate_20260912.md`；内容已由 root/S90 审计纳入，但不构成方法验证。另有假设矩阵 `agents/yesterday_hypotheses_matrix_20260912.md`。

## 还没有完成的部分

- 没有完成 GRC-Memory 的真实方法实现和端到端验证。
- 没有得到跨场景、带时间关系、RGB/深度/相机严格配对的确认集。
- 没有独立未来几何真值下的三维位置误差结果。
- 没有完成完整动态长视频、强基线公平比较、消融和独立确认。
- 因此当前仍是 `NO_METHOD_SELECTED / new_method_validated=false`，不能说已达到 PhD 或 CCF A 投稿标准。

## 当前进度的合理表达

按 proposal 顺序，基线复现、失败分析、近邻检索和问题收敛已有实质进展；方法设计、合格数据、跨场景实验和论文级确认仍处于前面几项完成后的阶段。用“前半段研究基础已经建立，后半段验证工作尚未完成”比给出虚假的百分比更准确。

## 下一步路线

先完成并复审 S90 索引工程修正，再完成 Gate 0 数据资格：历史池、未来 RGB-D、相机/时间/单位/坐标、GT 隔离和缺失清单。之后并行做低成本 2×2 重影诊断；只有 Gate 0 通过，才做 risk-only、utility-only、coverage、recent/distance、random 和 GRC 的同候选池同预算比较。任何结果都要在未调参场景或时间段复核。

完整可朗读稿见 `agents/advisor_oral_brief_20260912.md`；逐条科学勘误见 `DIALOGUE_CLAIM_AUDIT.md`。索引脚本已经有两轮安全修正，但独立审查仍列出 R1–R10/REVISE，尚未发起新的有界网络索引；不能把数据传输或索引当作创新结果。


## 本轮新增进展（继续科研）

- 完成 Gate 0 离线资格检查器 `agents/verify_gate0_manifest.py`。用现有 RTMV 候选运行结果为 `REJECT / DATA_NOT_AVAILABLE`，7项资格缺失，`network_used=false`；这是真实的资格拒绝结果，不是实验失败。
- S90 索引协议又完成一轮本地修正：canonical archive URL、checkpoint archive identity、seed/连续成员链、终端 zero block、输出锁和断点一致性检查；`py_compile` 与本地 `SEED_CHAIN_PASS` 通过。独立审查仍保留 REVISE，未联网。
- 统一给说明文档补充了试验名称图例，覆盖45份说明性Markdown；没有修改原始数值、模型输出、代码结果或PDF。


## S91R-C修正（2026-09-12 15:47，覆盖本报告中S91R的过强解读）

上一节S91R保留为历史记录，但不能继续按“32个 method×target×source 组合/方法”或“正相关足以支持GRC”来汇报。控制审查确认：总计是2方法×4目标×4来源=32个分层，每个方法16个；原始分位边界还把future-valid掩码带入了边界计算，现已用过去候选的全部finite/positive像素重新计算。

在固定留一目标控制下，四个目标的有符号未来AbsRel改善 never−all_new 均值为 -0.014472/-0.007696/-0.005395/-0.006582，即 all_new 的平均误差在四目标均变差，尽管像素层面的改善比例分别为 0.5948/0.6317/0.6467/0.6459。加入 disagreement 的控制模型ΔR²平均 +0.01463 且4/4为正，但同目标同来源的身份一致率只有约 4.35%–5.49%，无法把该预测增量解释成同一记忆条目的收益或因果效应。

因此本轮状态明确为 S91R-C（已保存历史候选与未来深度误差的增量风险及有符号收益控制审查）= STOP_GRC_METHOD_CLAIM。它是已见数据的测量审查，不是新模型、未见测试、跨场景验证或方法结果。正式 S91（未来几何风险增量预测试验，GRC-Pilot）仍为 BLOCKED_ON_GATE0。

控制审查和独立算术回执：work/S91R_saved_future_error_reanalysis/CONTROL_AUDIT_REPORT.md、control_audit_results.json、control_audit_recheck.json。

## S90传输修正第二版（2026-09-12 15:51）

针对第一轮独立复审提出的REVISE项，已完成本地代码修正：INFLIGHT现在绑定冻结的计划SHA、代码SHA和完整归档身份；恢复前交叉校验offset/body/body_sha/length/kind；新增已提交terminal-zero孤儿journal不重复恢复与stale offset拒绝fixture；初始S89 URL要求HTTPS、huggingface.co和精确canonical resolve路径。

本地 py_compile 与离线运输测试输出 `S90_TRANSPORT_REPAIR_OFFLINE_PASS`。这仍只是索引工程证据；尚未联网、尚未取得RGB/深度正文，也尚未通过第二次独立复审。若复审通过，下一步才允许一次有界网络索引；结果必须重新运行Gate0。


## S90第二次独立复审状态（2026-09-12 15:50）

修正后的第二次独立复审仍为 **REVISE**。复审发现完整RTMV源URL包含 `/datasets/TontonTremblay/RTMV/resolve/<commit>/abc.tar`，当前canonical helper漏掉数据集前缀，导致合法seed被错误拒绝；同时malformed INFLIGHT的 `record.kind=WRONG`、`record.length=999` 尚未被恢复逻辑拒绝。此项已回派修复，尚未联网。


## S90一次有界网络索引真实结果（2026-09-12 15:55）

最终工程复审通过后，按冻结预算从偏移12605440请求512B。真实结果是 STOPPED_TRANSPORT：HTTP 302、curl return 56、0新增正文、0新增头。安全回执记录了重定向说明正文1034B超过本次512B cap，未将302或失败写成数据获得。complete_view_ids为空，没有请求RGB/深度/JSON正文，Gate0仍为 REJECT / DATA_NOT_AVAILABLE。因此正式S91（未来几何风险增量预测试验，GRC-Pilot）继续阻断；不重复盲发同一请求。

证据：work/S90_proxy_resumable_index/index_01/RECEIPT.json、CHECKPOINT.json、MATCHED_VIEWS.json。

## S92（保存数据未来误差尾部风险分解）

S92对已保存S15B预测执行了固定尾部诊断。四个目标中，all_new平均MAE/AbsRel均变差，但改善像素比例为59.5%–64.7%；恶化总量最高5%像素占83.5%–85.5%。这支持“多数小幅改善被少数高幅度恶化抵消”的描述性解释，因此后续正式评价可预注册 mean AbsRel 与 worst-5%/CVaR 两类指标。S92没有新模型、新GT或未见场景，不能解释几何因果，也不改变S91R-C的 STOP_GRC_METHOD_CLAIM。

证据：work/S92_tail_risk_decomposition/PROTOCOL.md、RESULTS.md、results.json、run_s92_tail.py。

## S92创新前沿检索同步（2026-09-12 16:18）

专职创新Agent核对了NeurIPS 2025 Conformal Risk Training、NeurIPS 2024 Active Anytime-Valid RCPS、CVPR 2024 MemoNav和NeurIPS 2025 Prediction Value in Control。结论是CVaR/conformal risk、顺序风险控制、forgetting memory以及“预测误差不等于下游价值”均已有近邻，不能单独包装成GRC的新颖性。当前仅保留窄问题候选：校准历史几何风险在固定记忆预算、完整消费路径和独立未来RGB-D/相机真值下，能否预测source-level几何收益；正式验证仍需同时报告mean与CVaR并审计host/GPU成本。

证据：work/S92_tail_risk_decomposition/agents/innovation_frontier_scan.md。本轮未运行论文代码，未产生方法成立结论。

## S90 transport_v2 两次独立续接结果（2026-09-12 16:17）

为处理302说明体超过512B上限，新增独立transport_v2：HEAD不跟随跳转、解析并校验Location后才允许同host Range。index_02实际HEAD仍为HTTP302/TLS0/curl18/0正文，未得到Location；index_03仅加入ignore-content-length后变为TLS1但curl35、HTTP0、LibreSSL SSL_ERROR_SYSCALL，仍无Location且未进入Range。两次均0新header/body、无RGB-D配对、Gate0仍阻断。旧index_01保持不变；后续停止重复RTMV请求，转向替代数据资格审查。

证据：work/S90_proxy_resumable_index/transport_v2/FINAL_REPORT.md、index_02/RECEIPT.json、index_03/RECEIPT.json。

## S93 ALT-TUM-01（TUM RGB-D单序列最小资格检查）

为绕过RTMV传输阻断，对TUM `freiburg1_xyz`做小预算资格检查。真实取得ground-truth文本201100B/3000行，RGB/Depth AVI各65536B前缀并确认640×480 MPEG-4容器；但未取得可解码的带原始时间戳RGB/Depth PNG帧对，内参、单位与场景划分尚未绑定，许可也未确认。因此状态为 `GATE0_NOT_PASSED`，没有运行S91或任何未来误差评分。

证据：work/S93_ALT_TUM01/PROTOCOL.md、RESULTS.md、GATE0_RESULT.json。

## S93 ALT-TUM-01创新近邻同步（2026-09-12 16:24）

TUM-specific检索Agent核对了TUM官方benchmark、CVPR 2024 RGB-D SLAM benchmark、GS-SLAM、Photo-SLAM、SIGGRAPH 2024 RTG-SLAM和CVPR 2025 MASt3R-SLAM及官方代码。近邻已经覆盖误差驱动选择、可靠几何选择和统一公平评价；TUM适合做未来RGB-D/pose配对验证，但不能把TUM的静态3D模型质量当作几何真值。若继续ALT-TUM，必须固定候选池/记忆槽位/consumer，比较recent、uniform、random、pose/coverage、confidence、reprojection、depth、CVaR和utility-only，并记录source identity与GPU/host memory。GRC仍为candidate、novelty UNKNOWN、not validated。

证据：work/S93_ALT_TUM01/agents/innovation_tum_protocol.md。

## S93-FrameProbe 与 S94评价合同（2026-09-12 17:14）

TUM帧级探针实际得到RGB AVI和Depth AVI的局部/完整媒体，但一次负Range语法错误导致完整RGB AVI 8,059,298B误下载；该文件已标记unintended，不作为合规数据。Depth解码为8-bit RGB而非16-bit深度，AVI只保留相对30fps PTS，没有原始TUM绝对时间戳，因此不能绑定GT pose，Gate0仍未通过。

S94独立评价合同已通过离线检查 `S94_CONTRACT_OFFLINE_PASS`，要求未来答案隔离、source identity全链路、固定k=4及2/8敏感性、GPU/host/读取/选择/前向成本、mean AbsRel/worst-5%/CVaR95、强基线和至少5条独立轨迹×3个查询；合同仅为PROTOCOL_ONLY_NOT_RUN。

证据：work/S93_ALT_TUM01/frame_probe/RESULTS.md、receipt.json、VERIFY_FRAME_PROBE.json、work/S94_evaluation_contract_review/EVALUATION_CONTRACT.md。
## S94 ALT-3RSCAN-01：3RScan作为TUM替代候选的资格审查（2026-09-12 17:19）

对官方3RScan仓库、FAQ、文档、JSON元数据和样例归档做了有界检查。官方资料提供校准RGB-D、6DoF pose、内参K、reference/rescan和跨scan变换；本机看到478个场景组、1004个rescan，样例中央目录含两个scan，每个51个color、51个depth、51个pose和`_info.txt`。但本轮只取得JSON以及ZIP头/尾，未取得完整帧正文、16-bit depth、pose或`_info.txt`，所以没有验证同步、K数值、单位和深度有效率。

结论：`CONDITIONAL_CANDIDATE / GATE0_NOT_PASSED`。3RScan保留为优先替代候选，但不启动S91，也不把元数据当成模型实验或真实RGB-D结果。完整结果见`work/S94_ALT_3RSCAN01/`；数据Terms不由agent代填。

## S94评价合同（固定预算未来几何风险记忆选择）

独立合同离线检查通过`S94_CONTRACT_OFFLINE_PASS`。它冻结未来答案隔离、source identity、k=4及2/8敏感性、GPU/host/读取/选择/前向成本、mean/worst-5%/CVaR95、重投影与覆盖率、强基线及至少5条独立轨迹×3个未来查询。合同状态是`PROTOCOL_ONLY / NOT_RUN`，不代表S91或GRC已验证。

证据：`work/S94_evaluation_contract_review/EVALUATION_CONTRACT.md`、`EVALUATION_CONTRACT.json`、`VULNERABILITIES_AND_REPAIRS.md`。

## S96/S97：保存位姿核谱与本地RGB-D官方关联复核（2026-09-12 19:49）

### S96实际做了什么

本轮没有读取模型权重、没有做RGB-D推理，而是把GIM-World的公开核函数接线到项目已有的保存位姿列表上，检查有限核矩阵的特征值、抖动后的谱以及选择索引，并由独立脚本重新构造8个矩阵。8个池/参数组合均通过本轮的有限PSD数值门；独立复核74/74项通过。这个结果排除了当前输入与接线中的一个具体数值异常，但不能外推为GIM全局正确，更不能等同于GRC-Memory或未来预测实验。

### S97为什么必须修正

原S97使用每个RGB分别寻找最近depth和GT，适合做“文件可读性诊断”，却不是项目冻结的正式关联规则：它允许重复使用同一depth，也可能跨过GT长间隔。新增官方关联复核严格使用`src/tum_rgbd.py`的唯一贪心匹配（`|RGB-depth|<20 ms`），并按GT相邻间隔大于100 ms建立连续支持区间，要求RGB和depth落在同一区间。

| 开发序列 | 原始行数 RGB/depth/GT | 一对一RGB-D | 同一连续GT区间 | 图像读取错误 |
|---|---:|---:|---:|---:|
| fr1_xyz | 798/798/3000 | 792 | 788 | 0 |
| fr2_desk_timestamp_guard | 2965/2964/20926 | 2893 | 2212 | 0 |

保留图像均为640×480，RGB是8-bit RGB，depth是16-bit `I;16`。fr2有681个一对一匹配不能落入同一GT支持区间，因此不能把全序列直接当作连续带GT测试。两个序列已经在早期开发中使用，仍是`DEVELOPMENT_SEEN`，不是held-out。

### 对总研究目标的影响

这轮把“本地确实有可读RGB-D”与“可以做严谨的未见未来评测”分开了：前者现在有工程证据，后者仍被数据暴露、连续GT支持和held-out资格阻断。S91仍未启动，`new_method_validated=false`、`novelty_authorization=NONE`保持不变。

证据：`work/S96_gim_saved_pose_audit/run_01/RESULTS.json`、`INDEPENDENT_REVIEW.md`、`independent_results.json`、`work/S97_dev_rgbd_pair_audit/run_02_official_association_results.json`、`S97_OFFICIAL_ASSOCIATION_CORRECTION.md`。

## S95合同语义审查、3RScan访问纠正与GIM核函数诊断（2026-09-12 19:06）

独立数学审计发现，S94字段验证器未覆盖六项会改变解释的语义：`k=8`敏感性要求候选数至少8而原Gate0只写至少6；worst-5%与严格`x>q95`的CVaR在ties下不同且全相同误差会出现空尾；5条轨迹只应作最低描述性门；marginal calibration不能自动变成post-selection calibration；几何风险分量需要冻结单位/归一化；请求相机必须记录实际信息可用时间。已创建`work/S95_contract_semantics_audit/S95_CONTRACT_REPAIR_PATCH.md`和可执行验证脚本，S94仍为PROTOCOL_ONLY，正式S91继续禁止。

3RScan访问边界同步纠正：官方setup把样例ZIP标为example data并直接下载，但总Terms规则没有明确样例是否例外，因此状态是`AMBIGUOUS_NOT_VERIFIED`，不能断言“必须注册”或“无需许可”。reference/rescan应表述为重访/变化，不直接等同连续future frame。

对GIM-World Eq.16平方角距离Gaussian做独立公式诊断：四个大圆等间隔方向、`sigma_r=pi`的Gram最小特征值为`-0.15846314545655754`。这提示实现需说明PSD安全处理，并与CVPR2015 geodesic Gaussian理论一致；它不是GIM代码复现，也不证明作者报告失效。

证据：`work/S95_contract_semantics_audit/`；正式方法、GRC和S91仍未验证。

### 术语说明补充

本报告中S96段落虽然放在S95段之后用于保持“当前状态”叙述，但实验编号按发生顺序仍是S95→S96→S97。S96的初始结果文件曾显示等待独立复核；最终结论必须读取随后落盘的`INDEPENDENT_REVIEW.md`和`independent_results.json`（74/74项通过）。S97表格中的图像格式只描述通过同一连续GT支持区间的保留对，不代表全序列每一行都符合该条件。

### 独立创新审查结论

独立审稿Agent对最新证据的评分是：S96当前独立创新证据约1.5/10，S97当前创新证据约2/10。S96可支持“公开核函数接线和有限输入谱性质可复核”的工程结论；S97可支持“配对合同会改变可用评测样本”的数据审计结论。两者都不能支持GRC-Memory有效或GIM全局成立。潜在论文问题仍是：在固定记忆/计算预算下，历史观测级校准几何风险能否预测独立未来RGB-D/位姿误差，并在完整消费者路径上击败强基线；目前证据仍为candidate，尚无方法结果。

证据：`work/agents/innovation_s96_s97_review.md`、`work/agents/report_sync_audit_s96_s97.md`。

## S98：固定未来窗口可行性审计（2026-09-12 20:27）

把S97通过官方关联的开发数据继续按S8固定窗口合同检查：每窗8.840秒、24个等距目标、最近帧误差≤50 ms且不重复，并在GT间隔超过100 ms处分段。fr1只产生2个合格窗口，达不到预设的3窗口最低条件；fr2产生6个合格窗口，可按0、2、5选取。但fr2已经用于早期开发，不能当作held-out确认。所有拒绝都是连续时长不足，没有出现目标超差或重复帧。该审计没有运行模型、没有读取深度像素或GT位姿值，因此不能支持未来误差、记忆选择收益或GRC方法主张。

证据：`work/S98_dev_window_feasibility/RESULTS.md`、`RESULTS.json`、`run_window_audit.py`。
