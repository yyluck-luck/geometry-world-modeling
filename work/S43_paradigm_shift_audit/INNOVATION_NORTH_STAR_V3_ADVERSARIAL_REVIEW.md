# INNOVATION NORTH STAR V3 独立对抗审查

- 审查对象：`INNOVATION_NORTH_STAR_V3.md`
- 审查对象 SHA256：`f0e5893ad4892f11f36641476f8858ca9347db4075b35b32faf5beaf4ce102aa`
- 审查时间：`2026-09-08T10:05:30.406965+00:00`
- 审查角色：`/root/c2_generation_builder`
- 作者独立性：审查人不是 V3 作者，也未修改 V3
- 审查类型：fresh adversarial review
- 总体裁决：`PIVOT`
- Stage D 裁决：`KEEP_BOUNDED_MEASUREMENT_PILOT_AFTER_ALL_UPSTREAM_GATES`
- Stage C 裁决：`BLOCKED_PENDING_IDENTIFIABILITY_POWER_AND_COMPUTE_REVISION`
- 方法裁决：`NO_METHOD_SELECTED` 保持正确
- 新颖性裁决：`NONE` 保持正确
- 新模型运行：`0`
- 真实生成图片读取：`0`
- 模型载入：`0`
- 结果数组读取：`0`

## 给新手的结论

V3 已经把问题说得比 V2 准确得多：它不再把“输出变化小”说成“模型没有用记忆”，也不再把“影响落在投影区域外”直接说成“模型用错了位置”。这部分值得保留。

但 V3 现在还不是可以直接执行的确认实验。最关键的问题是：同一段协议允许研究者用几种不同方式计算主结果，而这些方式可能改变某个 scene 是否达到 20%，进而改变 5/8 的最终门。8 个 scene 对很普遍的中等效应也缺少足够检验功效。参考图像合同只能支持“相对于这组参考图更好或更坏”，不能把共享曝光、配准或场景状态偏差消掉。

所以本审查不否定这条研究线，而是要求把它收窄：先做一个有严格边界的 Stage D 可执行性试验；在进入 Stage C 前写成一个唯一可计算、做过功效分析且计算预算已落实的 V4 统计规范。当前不能把 AOIG、SEM、RCSU 的组合本身当作方法创新。

## 1. 审查范围与方法

本审查独立检查了五类问题：

1. AOIG、SEM、RCSU 是否在现有干预和观测下可识别；
2. 三参考观测合同能否支撑所写的效用结论；
3. `8 scene × 2 trajectory × 5 seed` 的统计门能否支持预定结论；
4. 当前本机资源能否执行该设计；
5. 2024 至 2026 年顶会或强预印本是否已经覆盖其测量或方法核心。

审查采用结果前的最不利解释：如果协议允许两个都看似合理的实现产生不同结论，就视为未冻结；如果一个解释只能由额外假设成立，就要求显式记录该假设；如果近邻工作已覆盖一般思想，就只把视频、3D、稳定 source identity 的特定交集当候选测量空间。

外部计算证据使用：

- `RAIMA_V3_COMPUTE_FEASIBILITY.md`
- SHA256：`c762be650a7cd91405a8a2b04992b8ef9a2f27100dc2e0146c6b9c3d8b49eebe`
- 状态：`PLANNING_ESTIMATE_ONLY`
- 该文件同样记录新模型运行 `0`

外部实时碰撞证据使用：

- `RAIMA_V3_LIVE_COLLISION_ADDENDUM_2026-09-08T1002Z.md`
- SHA256：`91c300c4365dbae1ea0715d159b1248c88cf159e2949e7aa13267a9e0ec77550`
- 状态：`PRIMARY_SOURCE_COLLISION_ADDENDUM`
- 本审查随后独立打开其中列出的一手论文或会议页面复核核心碰撞；该 addendum 没有被当作新颖性证明

## 2. 通过项

以下设计决定应保留。

### 2.1 可识别性措辞明显改善

- `Access–Observable-Influence Gap` 只描述指定干预下可观察输出响应不足，没有写成“没有使用”。
- `Support–Effect Mismatch` 先作为描述量；只有 support 外 effect 同时损害独立 reference 才允许升级为 harmful mismatch。
- `Reference-Conditioned Signed Utility` 明确条件于 reference roster、metric、replacement、source、target 和 seed，没有写成现实世界的永久 causal benefit。
- 主分析明确条件于 `stored ∩ ordinarily selected ∩ numerically addressable`，没有假装识别 Store 或 Select 的因果贡献。

这四点解决了 V2 最危险的过度解释。它们仍应是下一版的语言边界。

### 2.2 发现与确认分开

- B0/C1/C2 被限定为受协议开发影响的 discovery 数据。
- Stage C 要求未参与设计的新 scene。
- scene 被定义为独立统计单位；trajectory 和 seed 没有被当作独立样本。
- 失败 trajectory 和失败 seed 被要求保留。

这些规则能降低挑样本和伪重复风险。

### 2.3 SEM 的像素级构造方向正确

主 effect map 使用 raw target matched-zero direct effect，没有把不同 source 的 negative magnitude 逐像素相减。negative、replay 和 placebo 是独立数值 veto。这个方向与 S48 V6 的可识别性修订一致。

### 2.4 二项算术正确，但解释需要继续收窄

在 8 个 scene 独立且 scene 阳性概率的零假设为 `p <= 0.20` 时，观察到至少 5 个阳性的单侧精确二项尾概率确为：

`P[X >= 5 | X ~ Binomial(8, 0.2)] = 0.0104064`

V3 报告的两侧 95% Clopper–Pearson 下界约 `0.244863` 也与该计数相符。问题不在算术，而在抽样框架、功效和主 endpoint 尚未唯一冻结。

### 2.5 新颖性边界诚实

V3 明确写了 `NO_METHOD_SELECTED`、`novelty NONE`、`PARADIGM_SHIFT_NOT_ESTABLISHED`，并禁止“已提出新 routing/arbitration 方法”等对外说法。本审查没有发现 V3 在现阶段把测量交集正式冒充方法贡献。

## 3. 分级问题

### CRITICAL

`0`

当前文件是结果前候选设计，并且主动声明无方法、无新颖性、无真实结果。因此下面的问题会阻止 Stage C 和论文主张，但尚未构成已经发布的错误结论。

### MAJOR-1：主 endpoint 不能从文本唯一复算

V3 将每个 scene 的全部合格 source-target 聚合成 `retrieval–operation discrepancy rate`，但没有冻结以下决定：

- 分母是三个 endpoint 的共同 eligible 集合，还是各 endpoint 自己的 eligible 集合之并集；
- reference 不足会使 RCSU 不合格，此时该 source-target 是从分母删除，还是计为 RCSU 阴性但继续参加 AOIG/SEM；
- 两条 trajectory 是先各算 rate 再等权，还是先合并全部 source-target；
- source-target 数量不同时，source、target、trajectory 的权重如何分配；
- consumer 组合 `c` 有多个时，是任一组合阳性、全部组合阳性，还是只使用一个预冻结主组合；
- 两个 edit family 对三类 endpoint 的合并规则是否完全相同；
- 一个 source-target 同时满足多个 endpoint 时如何去重。

这些不是排版细节。不同合理实现会改变 scene rate 是否越过 20%，继而改变 5/8、8-scene mean 和 leave-one-scene-out 三重门。

**必须修复：** 在看 Stage C 像素前给出有限 typed roster 和一条伪代码级聚合算法。至少冻结 planned denominator、endpoint-specific eligibility flags、共同与非共同缺失集、trajectory 权重、consumer/edit family 的逻辑量词以及 union 去重。对每种 reference 缺失给出 worst-case 编码，不能让缺少 reference 选择性降低分母。

### MAJOR-2：8-scene 门的功效不足，且 scene 抽样框架未定义

5/8 对 `p0=0.2` 的一类错误控制是正确的，但 V3 没有给目标备择概率、功效或 scene 如何代表目标总体。独立复算 `P[X >= 5]`：

| 真实 scene 阳性概率 | 仅 5/8 计数门的通过概率 |
|---:|---:|
| 0.20 | 0.0104064 |
| 0.30 | 0.05796765 |
| 0.40 | 0.1736704 |
| 0.50 | 0.36328125 |
| 0.60 | 0.5940864 |
| 0.70 | 0.80589565 |
| 0.80 | 0.9437184 |

这还是未叠加 `mean >=20%` 和 leave-one-scene-out `>=15%` 两个附加门的上限功效。即使真实现象存在于一半 scene，单独 5/8 门也只有约 36.3% 机会通过。把少于 5/8 解释为“没有系统性问题”会混淆低功效和真实阴性。

scene 也没有抽样框架：室内/室外、纹理、遮挡、运动、return baseline、对象类别、光照和同一物理空间的复用规则未冻结。没有概率抽样或明确目标总体时，精确二项 p 值只对固定实验 roster 内的理想独立 Bernoulli 模型成立，不能自动外推到视频世界模型总体。

**必须修复：** 明确目标总体和 scene 采样/分层规则；证明没有同一物理环境、拍摄批次或共享 calibration 造成 cluster；预设有科学意义的备择概率并做完整联合门功效模拟。若仍用 8 scene，应把 no-go 写成“本规模未达到 systematic gate”，不能写成现象不存在。若目标是对 50% 至 60% 的普遍性有合理功效，应增加独立 scene 或采用经独立统计审查冻结的两阶段设计。

### MAJOR-3：三参考观测不能界定共享系统偏差

`Delta_ref = max pairwise primary-loss` 能测 reference 之间的分歧，却不能测它们共同具有的偏差。例如三个 reference 都受同一个曝光偏移、warp 偏移、标定误差或状态错配影响时，pairwise loss 可以很小，但它们都不是目标时刻的无偏代理。

还有一个数学边界：normalized RGB MSE 的 pairwise 值不是距离，`2 * Delta_ref` 没有自动成为输出对未知真值 loss 差的上界。V3 已经把量称为 reference-conditioned，这是正确的；但 `Delta_U` 只能是启发式 practical floor，不能写成已覆盖“reference 自身不确定性”的统计保证。

如果合格 reference 多于 3 个，V3 也没有冻结选哪三个或是否全部使用。时间邻近 reference 高度相关时，“三个 reference 分别同号”不能提供三份独立证据。

**必须修复：** 绑定 S48 V6 的 exact 四文件 SHA，而不是只写版本名；冻结 eligible reference roster、超过三份时的选择规则、common-valid domain 和每份 reference 的单独损失。加入可检测共享偏差的 calibration/reference-negative，至少报告 reference 时间间隔和相关结构。把 `Delta_U=max(0.001,2 Delta_ref)` 明确标成工程阈值并做阈值敏感性；仍只允许 `reference-roster-conditioned` 结论。

本次核到的 S48 V6 候选四文件为：

- preregistration SHA256 `6611d5f803740207fcfcec44eae8f756076f0763cb3eff8349fe1065905c03a0`
- normative spec SHA256 `29014cf8504a5b91040e96074c6d6edf47038814f230cb8d62e5822998d19d2f`
- reference implementation SHA256 `af6079dcce32af12b6bd0240e73fce2bae2e7aaeb39fa90dfcf1c99e9b7a5189`
- tests SHA256 `d05110ab6665eed6912b1ddfd07a00f99490b29d99cd63322d6326a81187c89c`

这些 SHA 只是本审查时观察到的 source-only 包，不能替代其后续独立审查和执行授权。

### MAJOR-4：处理版本和 consumer 聚合没有冻结，estimand 仍是一组量而非一个主量

AOIG 的记号包含 `consumer combination c` 和 `edit family f`，SEM、RCSU 又使用不同的 family、support、reference 和 replacement 条件。V3 没有给出有限的 `c` roster，也没有指定主分析对应 total-effect 还是受控 direct-effect 处理版本。

如果修改一个 appearance consumer 后重新计算其所有下游 descendant，这是该 hook 下的 total-effect intervention；如果冻结其他受影响 descendant，则是受控干预。二者回答不同问题。任取“最显著”的 `c` 或 family 会产生隐藏多重选择。

positive control 的 5/5 通过和两个 in-distribution family 的 5/5 不敏感也需要固定聚合层级。现在无法判断是每个 `c` 都须通过、至少一个通过，还是跨 consumer 平均后通过。

**必须修复：** 冻结一个 primary treatment version：目标 source 的一个预指定 consumer 输入被编辑，所有该输入的目标侧后代按同一路径重算；其他组合只作为 secondary controlled interventions。用有限表列出每个 endpoint 的 `c × family × sign × support × replacement`，并给出每格是否为 primary、是否进入 union、失败如何编码。不得从 Stage D 的最大 effect 选择 Stage C 主组合，除非用独立 discovery/confirmation 分割并重新冻结。

### MAJOR-5：确认性总体与“视频世界模型”范围不匹配

V3 的实现条件需要稳定 source ID、显式 selection、可枚举 appearance consumer 和 3D support。当前这些条件主要由 VMem 式实现提供。8 个 scene 即使全部通过，也只说明该 host 和该审计接口下存在现象，不能直接支持一般“视频世界模型”结论。

Kill rule 10 要求第二个 stable-source 架构复现，但 Stage C 主设计没有把 host architecture 作为预注册维度，也没有说明第二架构使用相同 source/target roster、处理版本和 reference 合同。

**必须修复：** 二选一。第一种是把论文范围明确收窄为 VMem-specific audit/bug characterization。第二种是在 broad claim 前增加第二 host architecture，以 scene 为配对单位，冻结相同可识别 source contract，并报告 host interaction。第二种会进一步增加预算，不能只把第二架构写成结果后的 kill rule。

### MAJOR-6：Stage C 在当前本机预算下不可执行

外部预算审计基于已完成的两次真实 CPU 两批运行，历史单进程峰值约 24 GiB，本机 64 GiB，因此保守按一次一个 generation process 估算。S48 最低协议每 seed 需要 28 个 target process；加入暂估 Pilot-B 后为 44 个。

由 `RAIMA_V3_COMPUTE_FEASIBILITY.md` 复核：

- 最小 1 seed Stage D 下界约 10.8639 小时；
- 5 seeds 最低约 54.3193 小时；
- Stage C 最低 2,240 target processes，乐观串行约 869.1 小时，即 36.21 天；
- 加入暂估额外 arms 后为 3,520 processes，约 1,348.4 小时，即 56.18 天；
- 这些估计还未包含失败率、metric、reference、审查和 I/O。

因此 `8×2×5` 不是目前本机可直接承诺的确认性设计。为了省计算在看过 Stage D 结果后删负控或减 seed，会破坏结果前合同。

**必须修复：** Stage C 前冻结完整 arm 数、snapshot 复用等价门、失败率、磁盘预算、wall-time 预算和可用算力。若采用序贯或两阶段设计，需在看确认性像素前做独立统计审查。当前只允许在全部上游门通过后做一个预注册 source-target、一个 seed 的 Stage D 最小否证试验；它不能估总体频率。

### MINOR-1：RCSU 的三参考聚合细节不完整

“三个合格 reference 分别计算时同号”没有规定若有 4 个以上 reference 怎么处理；`median |U| >= Delta_U` 是每个 reference 各自跨 seed 计算，还是先跨 reference 聚合再跨 seed 计算也不唯一。不同 reference 的 common-valid domain 可能不同，从而混入像素集合变化。

**修复：** 固定 roster 和嵌套聚合顺序，要求同一 pair 使用同一 common-valid mask，并为每个 reference 输出 typed receipt。

### MINOR-2：Holm 家族没有列成有限假设表

“三项 secondary families 使用 Holm”没有说明每个 family 内包含多少 source-target、consumer、support、replacement 和 metric 假设，也没有定义 scene-level test statistic 和离散小样本 p 值。interaction 是在 negative RCSU 后触发的数据依赖分析，需独立层级或 alpha 分配。

**修复：** 在 Stage C manifest 中列出所有 primary/secondary hypothesis IDs、方向、test statistic、有效样本规则和 multiplicity family；interaction 使用预冻结 gatekeeping 顺序。

### MINOR-3：AOIG 的噪声地板聚合层级不明确

`max(replay_p95, E_negative)` 没有在 V3 内说明 p95 是在像素、重复 replay、seed 还是 source-target 之间计算。negative source 有多个时的选择或聚合同样不清楚。这会影响 `D >= 0.5/255`。

**修复：** 绑定 S48 exact implementation，并在 V3 级 manifest 明确 replay receipt 数量、canonical pairing、negative roster 和 floor 的逐层聚合。

### MINOR-4：20% 同时作为单位内门和总体零假设缺少后果依据

V3 用 20% 定义 scene 阳性，同时用 `p0=0.2` 定义 scene 阳性概率零假设。两个 20% 回答不同层次的问题，目前看起来是方便的双阈值，而不是由下游科学后果或决策成本推导。

**修复：** 分别说明 source-target discrepancy rate 的最小重要比例与 scene prevalence 的最小重要比例，并预注册 10%、15%、20%、25% 的敏感性表。敏感性不能替代主门，但能防止把一个任意常数当作领域事实。

## 4. 三类 estimand 的可识别性判定

| Estimand | 当前能识别什么 | 当前不能识别什么 | 裁决 |
|---|---|---|---|
| AOIG | 在 stored、selected、addressable 条件下，指定 source edit 对已枚举 consumer 路径的可观察输出响应是否超过实验地板 | source 在内部是否被“使用”；未枚举 consumer；冗余、抵消或不可编辑充分统计量 | `KEEP_WITH_LOCAL_INTERFACE_SCOPE` |
| SEM | raw matched-zero direct effect 与预冻结 3D support 的操作性匹配，并由独立 reference loss 判定 support 外变化是否有害 | 语义上的正确影响区域；反射、阴影、遮挡等所有合理传播路径；all-path localization | `KEEP_AS_DESCRIPTIVE_THEN_VETOED_HARM_TEST` |
| RCSU | O-reinsert 相对 matched P 在固定 reference roster 和 metric 下的 signed loss difference | 来源对未知现实真值的永久 benefit；reference 共享偏差之外的真实反事实 | `KEEP_AS_REFERENCE_ROSTER_CONDITIONED_ONLY` |

三个量本身可以成为审计测量，但不能直接拼成一个已识别的统一“memory quality”潜变量。它们的 union 只表示至少一个预定义操作性异常发生。

## 5. 8 scene、2 trajectory、5 seed 的统计审计

### 5.1 独立单位

以 scene 为独立单位是正确选择。trajectory 嵌套在 scene，seed 是 paired technical repeat。所有区间、检验和 bootstrap 都必须在 scene 层重采样或使用 exact scene-level statistic。

如果两条 trajectory 共享相同 reference capture、calibration、source memory 或拍摄 session，它们不能提供第二个独立单位。5 个 seed 的 5/5 与 4/5 规则只表示对随机生成噪声的稳定性，不增加 scene-level 自由度。

### 5.2 Primary gate 是复合决策门，不是单一显著性检验

最终 go 同时要求：

1. 至少 5/8 scene 阳性；
2. scene 等权平均 rate 至少 20%；
3. 每个 leave-one-scene-out 平均 rate 至少 15%。

只有第一项有当前报告的精确二项尾概率。后两项与第一项相关，且 scene rate 来自大量内部 dependent source-target。不能把 `0.0104064` 当作整个复合 gate 的 p 值。下一版应把三者定义为决策规则，并通过固定 roster 下的 simulation 报告整体一类错误和功效。

### 5.3 Kill rule 的正确解释

若 8 scene 少于 5 个通过，允许删除“已观察到普遍的领域大象”表述。它不能证明 gap 不存在，也不能证明机制错误。低功效、reference ineligibility、hook 失败或 scene roster 偏移都可能导致 no-go。V4 应把统计 no-go、可识别性失败和工程失败分开编码。

## 6. 2024 至 2026 年碰撞审计

以下比较只使用论文或官方会议页面的一手来源。它说明哪些一般思想已经被占据，也说明 RAIMA 还可能留下什么狭窄空间。

| 近邻 | 已覆盖的核心 | 与 V3 的碰撞 | 对 V3 的后果 |
|---|---|---|---|
| CUE-R, arXiv 2026, <https://arxiv.org/abs/2604.05467> | 对单条检索证据做 REMOVE/REPLACE/DUPLICATE，测 operational utility、trace divergence 和两支持非加性交互 | 直接覆盖“逐 source 干预、操作性效用、answer-only/ordinary metric 会漏掉 effect、集合非加性”的一般思想 | AOIG/RCSU/interactions 作为抽象思想不新；只能主张视频和 3D source contract 下的新现象或新工具 |
| TetherMem, arXiv 2026, <https://arxiv.org/abs/2608.26902> | 冻结长视频生成器的 query-aware、region/age-conditioned memory routing；指出一致性与运动指标会漏掉 memory-anchored scene under-progression | 直接占据“普通视频指标通过但历史 memory 仍有害”及条件 routing 方法空间 | 若未来方法只是 region/age/query gate，必须以它为强基线；不能把问题发现或普通 gate 当新意 |
| WorldTrace/LoopBench, arXiv 2026, <https://arxiv.org/abs/2608.07408> | 将 KV memory 的存储和 addressability 分开，以 in-distribution virtual position 保持压缩 memory 可寻址，并在长 detour 后回访场景 | 直接占据 Store/Address 分层、回环 episodic recall、training-free cache 修复 | RAIMA 不能声称首次分离 storage/addressability 或首次视频回环 benchmark；WorldTrace/LoopBench 是最直接视频基线 |
| ReWorld, arXiv 2026, <https://arxiv.org/abs/2608.23565> | 固定预算 KV cache、pose-indexed landmark bank、palindrome return trajectory、分钟级 out-and-back recall | 占据 pose-nearest retrieval、固定 cache budget 和回文返回轨迹 | RAIMA 必须测 ordinary-selected 单 source 的责任和 reference 后果，整体返回首景相似度不足以区分贡献 |
| MBench, arXiv 2026, <https://arxiv.org/abs/2606.00793> | 将视频世界模型 memory benchmark 分成 entity、environment、causal consistency 与 12 个子维度，并使用真实长视频 | 直接占据“系统性视频 memory benchmark”和层级 taxonomy | RAIMA 不能以新 benchmark 或 taxonomy 为主张；只能证明 runtime source intervention 提供已有 benchmark 没有的增量证据 |
| E3C, arXiv 2026, <https://arxiv.org/abs/2605.26316> | point-cloud 3D memory 带 video-VAE appearance descriptor，渲染到 target viewpoint 做 view-aligned conditioning，并展示 scene editing | 占据 3D point memory、per-point appearance 与可编辑生成的组合 | “编辑 3D memory 会改变视频”不新；RAIMA 必须依靠 matched zero、负控、双 support 和 withheld reference 区分可编辑性与 source-level effect |
| What-If World, arXiv 2026, <https://arxiv.org/abs/2605.27589> | 用只改变一个物理细节的成对 prompts/videos 检查模型输出是否按物理因果方向变化；指出单视频看似合理仍可漏掉失败 | 占据“成对干预揭示单样本评价盲点”和 world-model causal benchmark 叙事 | RAIMA 的差异只能来自内部 runtime memory source、3D support 与真实 reference utility，不能来自 paired intervention 一般概念 |
| Scalable Influence and Fact Tracing, ICLR 2025, <https://proceedings.iclr.cc/paper_files/paper/2025/hash/65798a76cc176c29b6bfefe84b0a03ff-Abstract-Conference.html> | 大规模训练数据 attribution 中，经典 retrieval 更擅长找显式相关文本，梯度 influence 更接近改变预测的样本；两者可错位 | 占据“retrieval relevance 与 causal influence 不等价”的跨领域现象 | RAIMA 不能把 retrieval/influence gap 单独当新意；必须证明视频 runtime、3D spatial 和 reference utility 的联合现象 |
| ARC-JSD, ICLR 2026, <https://proceedings.iclr.cc/paper_files/paper/2026/hash/ed67dff7cb96e7e86c4d91c0d5db49bb-Abstract-Conference.html> | 无微调、梯度或替代模型的 context attribution，并定位 attention heads 与 MLP layers | 占据 generic context attribution 和内部层定位 | 若未来加入 hidden-state probe，必须把它作为 source-specific output intervention 的辅助测量，不能把 JSD 或 attention attribution 换名成方法 |
| CF-RAG, ICLR 2026, <https://proceedings.iclr.cc/paper_files/paper/2026/hash/1c078897dc08d46091d0d361d9955c6b-Abstract-Conference.html> | 用 counterfactual queries 识别 causally relevant distinctions，并行仲裁冲突证据 | 占据 counterfactual evidence arbitration 的一般框架 | 未来 set-conditioned arbitration 必须说明视频生成、source geometry 与连续输出带来的新机制，而非概念迁移 |
| CoRM-RAG, arXiv/SIGIR 2026, <https://arxiv.org/abs/2605.01302> | relevance–robustness gap、cognitive perturbation、轻量 Evidence Critic、risk-aware abstention | 占据“relevance 不是 utility”和由反事实 teacher 学风险 critic | 不能把 retrieval score 到 utility 的 gap 或轻量 critic 本身当贡献 |
| Attribution Blind Spot, arXiv 2026, <https://arxiv.org/abs/2605.26778> | 表明 output consistency 不能认证是 retrieved context 还是参数记忆主导；内部表示只提供 membership-conditioned signal，论文也明确不认证单条生成用了哪个 source | 支持 V3 把 Use 降为 Observable Influence，同时封死“输出不变即未使用”和“内部 probe 即来源认证” | 可把 representation divergence 作为二级诊断，不能作为 source-use 证明或独立新方法 |
| Ref4D-VideoBench, CVPR 2026, <https://openaccess.thecvf.com/content/CVPR2026/html/Wei_Ref4D-VideoBench_Four-Dimensional_Reference-Based_Evaluation_of_Text-to-Video_Generative_Models_CVPR_2026_paper.html> | 600 个 reference video、12 个指标、四维细粒度 reference-based 视频评价，并验证更接近人类判断 | 占据“reference-based 视频评价比 no-reference 更可靠”的一般主张 | 三参考合同和 reference metric 只是测量设计；需证明 source intervention 带来 Ref4D 无法回答的独立信息 |
| Hi3DEval, NeurIPS 2025 Datasets & Benchmarks, <https://proceedings.neurips.cc/paper_files/paper/2025/hash/42ffaddcc6edc9fb05ff9f9b49fca700-Abstract-Datasets_and_Benchmarks_Track.html> | object/part/material 的层级 3D 生成评价，结合视频与 3D 表征 | 占据 hierarchical、geometry-aware evaluation 的一般空间 | 3D support 分层本身不新；必须通过 source-conditioned intervention 和 reference utility 展示增量构念效度 |

### 6.1 仍可能保留的窄贡献

当前没有被上述近邻直接等同覆盖的，是以下严格交集：

> 在显式视频世界 memory 中，对 ordinarily selected、稳定标识且可数值寻址的 runtime source，在已枚举 appearance consumer 上做 matched intervention，并同时报告 3D support、输出 direct effect 与 withheld-reference-conditioned utility。

这个交集目前只是 measurement specialization。组件交集不会自动产生新颖性。要升级为论文贡献，至少需要：

1. 在预注册的多 scene、最好多 host 架构上观察到近邻指标无法预测的稳定现象；
2. 证明该审计相对于 retrieval score、TetherMem 式 routing signals、CUE-R 式 item intervention 和 reference/hierarchical metrics 有增量预测或诊断价值；
3. 由真实失败结构导出一个视频特有机制，并胜过对应强基线；
4. 在独立 held-out scene 上验证，而不是由 B0/C1/C2 反复调协议。

新增碰撞进一步否决了五类宽泛表述：首次分开 storage/addressability、首次视频 memory 回环 benchmark、首次发现 retrieval 与 influence 错位、首次通过编辑 3D memory 验证生成影响、首次用 paired intervention 揭示 world-model 单样本指标盲点。WorldTrace/LoopBench、ReWorld、MBench、E3C、What-If World 和 ICLR 2025 influence 工作已经分别占据这些主张。

它们没有完全杀死上述四因素交集，因为现有页面尚未同时给出 `ordinary-selected source × enumerated runtime consumer × 3D support × withheld real reference` 的 typed matched audit。但检索未发现不等于首创；这个交集只有在真实多 scene、多 host 数据显示独立增量后才值得再次做新颖性审查。

在此之前，正确标签是 `MEASUREMENT_CANDIDATE`，不是新任务范式、方法或颠覆式创新。

## 7. Idea Evaluator 五维评估

该评分评估当前研究设计，不是论文录用概率。

| 维度 | 分数 / 10 | 依据 |
|---|---:|---|
| Higher | 6 | 从 retrieval success 深入到 source-conditioned response、support 和 utility，问题有机制价值；尚无真实效应或增量效度 |
| Faster | 2 | Stage C 乐观串行也约 36.2 至 56.2 天，且协议/执行链仍有上游门 |
| Stronger | 7 | matched zero、replay、negative、positive、placebo、kill rules 和 discovery/confirmation 分离较强；主聚合与 reference 识别仍未闭合 |
| Cheaper | 2 | 单 seed 最低约 10.9 小时，确认 cohort 超出当前本机现实预算 |
| Broader | 4 | 抽象问题广，但当前可识别接口和证据主要是 VMem-specific；第二 host 尚未进入正式设计 |

第一性原理问题成立，技术周期也基本成立。Hamming 重要性和“领域大象”仍待真实确认。当前最短板不是再起一个方法名，而是构念效度、唯一统计实现、计算计划和跨 host 外推。

## 8. PIVOT 后的最小 V4 要求

V4 在进入 Stage C 前至少要新增以下冻结物：

1. `ESTIMAND_TABLE`：每个 endpoint 的 unit、treatment version、comparison、outcome、support、eligible rule 和 aggregation；
2. `PRIMARY_ENDPOINT_REFERENCE_IMPLEMENTATION`：从 typed receipts 到 scene rate 和三重 go gate 的唯一纯函数，加边界和缺失反例测试；
3. `SCENE_SAMPLING_MANIFEST`：目标总体、场景分层、物理独立性、两 trajectory 规则和禁止替换规则；
4. `POWER_AND_SENSITIVITY`：复合 gate 的一类错误、功效、缺失、cluster 和 10% 至 25% 阈值敏感性；
5. `REFERENCE_CONTRACT_BINDING`：绑定 exact S48 文件 SHA、固定 roster、common-valid mask、共享偏差 calibration 和 nested aggregation；
6. `FINITE_HYPOTHESIS_REGISTRY`：primary/secondary/interaction 的方向、family、alpha 和 gatekeeping；
7. `COMPUTE_MANIFEST`：完整 target process 数、snapshot 等价证据、失败率、磁盘、wall time、算力来源和停止规则；
8. `NOVELTY_MATRIX`：至少包含 WorldTrace/LoopBench、ReWorld、MBench、E3C、What-If World、Scalable Influence、ARC-JSD、Attribution Blind Spot、CUE-R、TetherMem、CF-RAG、CoRM-RAG、Ref4D 和 Hi3DEval 的逐项能力对照与必须胜过的 baseline。

上述文件只能在看 Stage C 结果前冻结。Stage D 可以验证 hook、控制、量级和预算，但不得用来修改 Stage C 主 endpoint 后继续称为同一份确认协议。

## 9. 最终裁决

### `PIVOT`

保留：

- 结果前的 reference-anchored interventional measurement 方向；
- AOIG、SEM、RCSU 的降级措辞；
- stored/selected/addressable 条件范围；
- scene 作为独立单位；
- matched controls、reference veto、kill rules；
- `NO_METHOD_SELECTED` 和 `novelty NONE`。

阻止：

- 用当前文本直接运行 Stage C；
- 把 5/8 的单项二项尾概率当整个复合 gate 的 p 值；
- 把 no-go 当现象不存在；
- 把三参考一致当成现实真值保证；
- 把 AOIG、SEM、RCSU 的交集本身当方法或范式创新；
- 在只有 VMem host 时外推到视频世界模型总体；
- 在当前本机预算下承诺全量确认实验。

允许的下一步只有两条：完成所有上游 source/execution gate 后做一个严格限定的 Stage D 最小否证，或先完成上述 V4 统计与预算冻结。任何方法开发都必须等真实、稳定且近邻基线未解释的失败出现。

## 10. 审查边界声明

本审查只读取 V3 文本、source-only S48 V6 合同文件的哈希、已存在的计算可行性文本、实时碰撞 addendum 和其中指向的一手论文/会议页面；独立执行的只有标准库二项概率算术与文件 SHA256。没有运行 VMem、C1、C2、S48 arm 或任何生成模型；没有读取或解码生成图片；没有读取科学 payload 或结果数组；没有产生实验结果；没有授权 novelty、method、Stage C 或真实执行。
