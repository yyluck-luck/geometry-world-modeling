# S96/S97 审稿人式创新评估

- 评估时间：2026-09-12（Asia/Shanghai）
- 评估者：独立审稿视角 agent
- 评估对象：`work/S96_gim_saved_pose_audit` 与 `work/S97_dev_rgbd_pair_audit`
- 研究边界：`new_method_validated=false`，`novelty_authorization=NONE`；不把审计通过写成 GRC-Memory 或 GIM-World 成立。

## 一、给审稿人的一句话判断

S96 和 S97 目前形成的是**可复查的工程与数据资格证据**，不是独立方法贡献。它们的价值在于排除了两类会污染论文结论的错误：一是把有限位姿核谱计算当成完整 GIM 复现，二是把“文件存在/最近邻配对”当成有效的 RGB-D-位姿未来评测。若继续完成冻结的未来查询实验、风险预测和 source-level 消融，这些审计可以成为一篇“可靠评测合同/问题定义”论文的基础材料；当前不能单独支撑 PhD/CCF-A 级方法主张。

## 二、S96：GIM 保存位姿核谱审计

### 2.1 已证明的内容（方法证据之前的基础证据）

- 使用保存的 TUM `freiburg1_xyz` 3000 行 GT 位姿、四个预先冻结的 16 行池和官方源码快照。
- 实际计算了 4 个采样池 × 2 个条件（官方高层时间因子、关闭时间敏感性），共 8 个核矩阵。
- 独立实现使用 NumPy/FP64 重建，74/74 复核通过；重建矩阵与保存矩阵最大绝对误差在 `9.88e-15` 至 `2.08e-11`。
- 这 8 个有限样本条件下均未观察到带 `1e-4` jitter 后的负特征值；所返回的索引满足数量、池成员和首尾锚点检查。
- 没有读取 RGB/深度，没有模型推理，没有生成消费者 forward，没有未来查询评分，因此它只验证数值链和输入适配。

### 2.2 审稿人不会接受的外推

1. 不能由 8 个池推出 GIM 核在所有轨迹、带宽、尺度、时间跨度下都 PSD。
2. 不能由“无负特征值”推出 kernel 的信息增益排名正确、选择有未来预测价值，或官方论文结论被复现。
3. 不能由 `official_selected` 索引的形状/锚点检查推出信息论最优性。
4. 不能由当前适配假设（TUM camera-to-world、相机 `+Z`、米/厘米缩放、行号时间）推出跨数据集坐标语义正确。
5. 这不是 GRC-Memory 的 risk calibration、memory selection 或 future-error 实验。

### 2.3 审稿式评分

| 项目 | 当前分数（10分） | 说明 |
|---|---:|---|
| 工程审计价值 | 8.0 | 可复查、独立重算、明确冻结输入；能阻止错误复现声明 |
| 数值可靠性 | 8.0 | 74/74、矩阵差异小；但仍只覆盖有限池 |
| GIM 方法证据 | 2.5 | 没有原生模型、训练或完整消费者；仅有核组件审计 |
| GRC 证据 | 0.5 | 没有历史风险到未来误差链 |
| 独立创新证据 | 1.5 | “有限核谱 audit”可做 reproducibility note，尚非新研究问题 |
| **潜在论文价值（条件）** | **5.5** | 若扩展成跨核/跨数据/跨带宽的可证伪评价合同，才可能升级 |

### 2.4 S96 能否成为独立贡献？

当前不能。最可能的审稿结论是：`useful implementation check / reproducibility appendix`。只有在以下条件下，S96 才可能升级为独立问题的一部分：

- 预先定义“核合法性”而非只看本次最小特征值；覆盖多轨迹、尺度、带宽、采样密度、时间项和 jitter 敏感性。
- 对比原论文实现、规范 PSD/修正 kernel、直接 baseline selector；报告选择结果和未来几何误差，而非只报告谱。
- 给出一个可推翻预测：例如，某种 kernel 非 PSD/不稳定性会导致选择排名在扰动下不稳定，并能预测未来误差或 memory selection failure。
- 将任何理论/实现缺陷与真实消费者结果连接起来；否则它仍只是数值审计。

## 三、S97：TUM RGB-D 官方关联复核

### 3.1 已证明的内容

- 两个本地 TUM 目录中的 RGB、深度、GT 文本可读，图像尺寸均 640×480，RGB 为 RGB，深度为 16-bit `I;16`，无图像读取错误。
- 按项目冻结规则做了一对一 RGB-depth 关联（严格 `|dt| < 0.020 s`，不重复使用 depth），并按 GT 间隔 `>0.100 s` 的闭合支持区间筛选。
- `fr1_xyz`：798/798/3000，792 个唯一 RGB-D 关联，788 对落在同一 GT 支持区间，4 对被排除。
- `fr2_desk_timestamp_guard`：2965/2964/20926，2893 个唯一 RGB-D 关联，2212 对落在同一 GT 支持区间，681 对被排除。
- 两个序列均已用于早期开发（`DEVELOPMENT_SEEN`），所以只能用于工程调试和协议验证，不能作为 held-out 或跨场景确认。

### 3.2 关键负结果的审稿意义

原来的逐 RGB 最近邻 GT 诊断会重复使用 depth，并跨过 GT 长间隔；因此“最近邻全部有 GT”会制造虚假的评测资格。S97 官方复核把这个风险显式化：fr2 有 681 个唯一 RGB-D 对不能落在同一连续 GT 支持区间。这个负结果很有价值，因为它证明**数据配对是科学变量，而不是准备工作细节**。

但它仍然没有证明：

- 历史几何风险能预测未来位置/深度误差；
- GRC 比 recent、pose-only、coverage、confidence、GIM 或随机选择更好；
- 动态/长期世界状态得到改善；
- 两个开发序列上的结果可以泛化。

### 3.3 审稿式评分

| 项目 | 当前分数（10分） | 说明 |
|---|---:|---|
| 工程/数据资格价值 | 9.0 | 明确修正 naive nearest 误配；规则与计数可追溯 |
| 数据协议可靠性 | 7.5 | 一对一与 GT 支持区间已执行；仍需评估 pose interpolation、K、单位与深度有效像素质量 |
| 未来评测证据 | 1.0 | 尚未冻结历史/未来并读取未来答案做评分 |
| 方法证据 | 0.5 | 没有 selector 或 world-model inference |
| 独立创新证据 | 2.0 | “配对合同影响结论”是重要测量问题，当前还不是方法 |
| **潜在论文价值（条件）** | **6.0** | 若形成公开、可复现的未来几何评测合同并展示误配导致排名翻转，潜力上升 |

### 3.4 S97 能否成为独立贡献？

单独不能。最安全的定位是 `data/protocol qualification`。它有一个可升级的研究问题：**在历史选择与未来几何评估中，时间关联/支持区间合同是否会改变记忆选择器排名和尾部风险结论？** 但必须做预注册的“错误关联 vs 官方关联”对照，并明确错误关联只是故障诊断，不能作为主结果。

## 四、S96 + S97 联合后最有希望的创新方向

### 候选 1：未来几何价值评测问题（当前首选）

**命题：** 在固定 item/token/时间预算下，历史观测级几何风险是否能预测未参与选择的未来 RGB-D/pose 误差，并在完整 consumer path 后仍有增量价值？

- 潜在新颖性：7.5/10（问题定义有机会独立；方法尚未证明）
- 当前证据：1.5/10（只有数据/核数值准备）
- 失败风险：高；可能只是 pose/coverage/recent 的重命名。
- 必须满足：独立 calibration、未来答案隔离、至少 5 条独立轨迹、每条 ≥3 个 future query、固定 `k=2/4/8`、公平 cache/forward/latency 成本、强 baseline 与 source identity。
- 否证：risk-only 不优于 pose/coverage/utility，或优势在成本匹配后消失；风险排序不预测 future error；跨轨迹方向不稳定。

### 候选 2：反事实 source-level memory effect

对一条已被真实 consumer 使用的历史 item，只删除/替换该 item，重算所有下游状态，固定干预前外生条件与非目标初态；测量未来几何误差变化。

- 潜在新颖性：8.0/10；当前证据：0/10。
- 必须先有稳定 consumer、可寻址 source ID、exact replay 方差估计、完整后代重算。
- 不能把冻结下游 latent 的差分称 total effect；那只能叫受限路径诊断。
- 若 `F11-F00` 不超过 replay 波动、局部性不超过面积匹配置换、收益符号依赖 placebo，则停止。

### 候选 3：几何-外观交互的可重复失败规律

在可信/扰动几何 × 普通/几何约束外观的预注册 2×2 中，测量未来深度、重投影、pose 与 tail risk 的交互项。

- 潜在新颖性：6.5/10；当前证据：2.5/10（S86/S92 只有描述性动机）。
- 若交互项在多场景、不同消费者、不同 mask/面积匹配下稳定，可能形成 measurement/diagnosis 贡献。
- 若只在单场景或 MSE 与视觉重影不一致，则降级为 ablation，不能升级方法。

## 五、下一步按优先级排列（只列可判别工作）

1. **完成 S97 的 pose/K/单位协议守卫**：明确 TUM camera-to-world、内参来源、深度 scale、pose 插值和支持区间；保存每个 future query 的身份。
2. **构造 Gate-0 资格清单**：至少 5 条独立序列/场景；每条 ≥6 历史候选、≥3 future query；严格冻结历史/未来分区，不把同一开发轨迹切窗冒充独立场景。
3. **先做无模型的风险预测试验**：只用历史重投影/深度/可见性风险，测其与未来 3D/深度误差的 Spearman、Pearson、分位数覆盖和 calibration；先回答“风险是否有预测信息”。这比直接训练 selector 便宜。
4. **再做公平 selector 对照**：random、recent、pose-distance、coverage、depth-only、confidence-only、GIM/MI（若实现合法）、utility-only、risk-only、risk+utility；`k=2/4/8`，记录输入字节、token、GPU/CPU 时间、forward 次数。
5. **只有风险预测成立后再做完整 consumer path**：固定噪声和非目标条件，测 future RGB-D/pose；保留 replay variance、source identity、tail/CVaR 和 matched-mask locality。
6. **跨动态数据确认**：TUM 只能静态开发校准；若主张动态 4D，优先 Bonn Dynamic 或合规的 3RScan environment-group split。3RScan reference/rescan 必须按 environment group 留出，不能把 scan ID 当独立场景。
7. **把 GIM 核谱风险作为审计变量**：若选用 GIM，应同时跑原公式、PSD-safe comparator 和带宽/时间敏感性，观察排名/未来误差是否受 kernel 稳定性影响。不能只报“本次特征值为正”。

## 六、最终审稿结论

- **现在最强结论**：工程审计和数据协议已经明显更可靠；S97 的误配负结果是应保留的科学边界，S96 的 74/74 复核是有限数值链确认。
- **现在不能说**：GRC-Memory 已成立、GIM selector 有效、存在顶会级方法、完成了真实未来生成。
- **最可能的论文位置**：当前材料可成为主论文的 reproducibility/data-contract section，或一篇测量/评测方法的起点；不能作为完整 method paper 的结果段。
- **升级条件**：需要真实 future query、独立轨迹、校准风险的预测性、完整 consumer 的因果/paired effect、强基线和公平成本，以及跨场景确认。
- **停止条件**：Gate-0 配对不合格、风险与未来误差无预测关系、risk-only 不优于普通基线、source effect 低于 replay、或优势只在开发序列成立，则停止 GRC 方法叙事，报告负结果并转向可靠评测/故障诊断。
