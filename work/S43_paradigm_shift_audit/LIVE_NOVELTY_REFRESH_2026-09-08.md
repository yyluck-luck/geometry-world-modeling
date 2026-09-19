# S43 实时创新复核增量：从五级合同收紧为六级合同

- 证据冻结时间：2026-09-08T04:22:23Z
- 复核对象：**在显式检索、稳定 source ID、全部真实消费路径可审计的架构中，固定外生条件和非目标初始状态，对普通运行中实际选中的一条记忆来源做跨全部真实消费路径的一致反事实；该来源的全部下游后代必须重新计算。随后分别检验 influence、干预前 geometry localization 与独立定义的 signed benefit。**
- 本次性质：在既有 `NEAREST_WORK_CAUSAL_MEMORY_ACCEPTANCE_V2.md` 与 `EXPANDED_CITATION_NETWORK_AUDIT.md` 之后追加的实时压力测试；不改写旧冻结证据。
- 当前裁决：**KEEP_ONLY_AS_ARCHITECTURE_SCOPED_JOINT_EVIDENCE_CONTRACT**
- 新颖性授权：**NONE**。本文只说明候选仍有可证伪差异，不允许写“首个”“已证明创新”或“达到 CCF-A”。

## 1. 给新手的直接答案

现在有一个**候选创新点**，但还没有实验把它证明出来。

现有方法大多回答“过去有没有被存下来、系统挑了什么、平均画质有没有提高”。我们要回答的是更严格的一串问题：

> 某条过去的画面真的被当前生成使用了吗？如果只连贯改变这一条画面，它造成的变化是否出现在几何上应该受它影响的位置？这个因果量能否提前判断一次自然重访会成功、失败，或应当拒绝这条记忆？

这更像一个新的**证据合同、诊断任务和接受协议**，而不是先发明一个更复杂的网络。只有最小实验通过后，才值得把它升级成训练方法。

## 2. 本轮冻结的研究问题

1. **RQ1**：2025–2026 年最近工作分别覆盖了记忆的存储、选择、寻址、消费、空间定位和实际收益中的哪些环节？
2. **RQ2**：已检查论文或官方代码中，是否出现了与“单来源、固定状态、全路径、几何局部、自然错误预测”联合等价的公开协议？
3. **RQ3**：哪个最便宜的实验可以推翻候选，避免先训练一个普通 gate？

## 3. 为什么五级合同必须改为六级

原合同是 `Store → Select → Consume → Localize → Benefit/Accept`。WorldTrace 给出一个不能忽略的反例：历史内容即使仍在 KV cache 中，超出训练跨度的 RoPE 相对位置也可能让模型无法可靠读取；在旋转后的空间直接压缩还会混合不兼容的相位。因此“被选中”与“当前查询能可靠寻址”不是一回事。

本轮把合同收紧为：

1. **Store**：该来源及其来源身份确实进入可访问的记忆；
2. **Select**：普通、未受干预的运行确实选择该来源；
3. **Address**：在当前时刻、位置编码和缓存布局下，查询仍能区分并读取该来源；
4. **Consume**：固定 prompt、camera、noise、RNG 与非目标初始记忆等外生量后，在全部真实消费路径中连贯改变该来源并重算全部下游后代，会造成超过 exact-replay 本底的输出变化；
5. **Localize**：变化显著集中在干预前冻结的几何支持区，并超过支持区面积占比基线；
6. **Benefit/Accept**：相对独立质量目标和公平替代条件定义有符号收益；再检验预处理可见的单项特征能否增量预测自然错误或收益，并支持接受、拒绝或重新观察。

低强度 `F11−F00` 外观编辑只直接识别 **Influence** 和 **Localization**。变化大不代表有益，效应图也不给出收益正负；Benefit 必须另有相对冻结 return reference 的损失比较。

这次拆分是**问题定义的修订**，不是已经成立的创新结论。

## 4. 新增一手来源压力测试

| 工作 | 已建立的最近能力 | 对六级合同的主要压力 | 本轮没有在已检查材料中识别到的联合部分 |
|---|---|---|---|
| [WorldTrace](https://arxiv.org/abs/2608.07408) | 将位置可寻址性与压缩内容信息量分开；用 in-distribution 虚拟位置和 canonical keys 做长时 KV 记忆；LoopBench 测长绕行后的重访 | **Address 已经是明确问题，不能再把它埋在 Select/Consume 中** | 对普通运行实际选中的单一来源做外生条件匹配、跨全部消费路径且重算后代的反事实；输出效应的几何局部性；单项分数预测自然失败 |
| [WorldKV](https://arxiv.org/abs/2605.22718) | 缓存被逐出的 KV chunks，按相机/动作对应关系选择并重新插回注意力窗口；在固定预算下压缩 | Store、Select、Address 和系统级收益已有强先例；注意力能够显示视角对应 | 注意力相关或整模块/整 chunk 比较不等于一条来源的 total causal effect，也没有干预前几何区域上的输出效应检验 |
| [CaR](https://arxiv.org/abs/2606.23105) | 通过相对视角位置编码和 attention 做隐式连续检索，并压缩长上下文 | 几何查询、检索和消费已经可以在同一注意力机制内完成 | 没有识别到普通运行中单项来源的 exact-replay 全路径干预或单项因果分数对自然重访的预测 |
| [DensityKV](https://arxiv.org/abs/2608.27922) | 按 head 保存 token 级 KV bank，用 post-RoPE key 密度做准入/淘汰；展示来源时间与空间 token 的 admission trace | token 级保留身份、寻址表示和准入分析已有近邻，简单的“保留热图”不够新 | admission/retention 说明什么留下来，不说明某条留下来的来源对最终像素造成了什么局部因果效应 |
| [GIM-World](https://arxiv.org/abs/2606.02436) | 将历史压为固定 memory tokens，用相机射线查询的 geometry head 蒸馏 VGGT patch features；有几何监督和 pruning 消融 | “几何监督写进记忆”“camera-queryable memory”“局部 patch 级目标”均已有直接先例 | 其 memory tokens 明确没有输入帧/patch 一一对应；没有识别到运行时单来源全路径反事实、输出效应定位和单项错误预测 |
| [Matrix-Game 3.5](https://arxiv.org/abs/2608.29910) | 3D patch provenance、目标视图对齐、统一 pose-aware attention、固定 seed 的模块级 ablation | source provenance、pre-treatment geometry support 和固定种子模块比较都不能单独主张 | 普通运行已选单项的全路径 total effect、超过面积基线的局部性、对自然失败的增量预测 |
| [I3DM](https://arxiv.org/abs/2603.23413v2) | 历史帧空间置信图、最大覆盖选择、3D 对齐和可靠区域注入 | Select、Consume、Localize 已有最直接近邻；几何选择/局部注入都不能单独主张 | 同一 runtime source 的全路径 post-selection effect、matched-mask enrichment 和自然 signed benefit |
| [TetherCache](https://arxiv.org/abs/2606.13035v1) | GRAB 用 attention relevance + temporal diversity 做准入；TAME 对 recalled K/V 做 trusted alignment | generic select/gate/repair 与系统收益已经被占据 | 稳定 source ID 的全路径因果定位及其在强 selection/repair proxy 外的增量收益预测 |
| [Echo-Memory](https://arxiv.org/abs/2606.09803v1) | 固定 backbone/training/sampler/eval，分解 capacity、compression、read-out、recurrence；replay/return 结论会反转 | Store≠Read-out、raw-context 强基线和多分支评测已经被占据 | 普通运行单 source 的 post-selection effect、pre-treatment geometry localization 和 matched signed benefit |
| [CUE-R](https://arxiv.org/abs/2604.05467v1) | 优先实际 used evidence，做 REMOVE/REPLACE/DUPLICATE、paired delta、bootstrap 与双证据非加性 | 抽象的 per-item intervention→signed utility 已有；不能宣称首次逐项因果效用 | 视频生成特有的稳定视觉来源、多消费路径、相机/几何支持和自然重访质量连接 |
| [Utility-Oriented Visual Evidence Selection](https://arxiv.org/abs/2605.13277v1) | 用输出分布 information gain 定义 visual evidence utility，并用轻量 surrogate 预测 | “输出变化代表证据效用”和“训练轻量 utility gate”已有跨域压力 | influence 必须与 signed benefit 分开；接受器必须证明几何因果标签有额外价值 |

### 4.1 官方代码快照

- WorldKV 官方仓库快照：`046f6d19890555fd4601e8888d7258bee12fad01`，commit time `2026-07-18T08:23:43+00:00`。
- DensityKV 官方仓库快照：`dcb1fba4a5606daf730ca9bfe32ac717596833ce`，commit time `2026-08-31T15:19:32+08:00`。
- I3DM 官方仓库快照：`895033d098a683ad49ed945a8524dea327895fe4`。
- TetherCache 官方仓库快照：`37c581ace23ff5df201f45e8282065d19b4ace8c`，commit time `2026-06-12T11:16:30+08:00`。
- Echo-Memory 官方仓库快照：`194be716aedaa84d9bd377740d6e6d9c32a309cb`，commit time `2026-08-16T09:49:34+08:00`。该 commit 含论文 v1 之后的 geometry path；不能倒推成 v1 表格结果。
- CUE-R 作者仓库快照：`84d7a6dbb1336e57aee8053c0ee9bb72155839ff`，commit time `2026-04-07T18:17:54-07:00`；README 自述 official code。
- 早期只在 WorldKV 与 DensityKV 两个快照中，对 `counterfactual|intervention|knockout|activation patching|causal effect|source-coherent|all-path` 做过大小写不敏感文件级搜索，均返回 0 个文件；这一词表探针不覆盖后来新增的仓库。

这个 0 只表示**在指定快照和指定词表中未命中**，不能证明代码没有语义等价实现，更不能证明领域没有等价方法。论文方法、实验和图表的正向核验仍是结论主体。

## 5. 本轮后的候选创新定义

暂定工作名：**GeoCausal Memory Contract（几何因果记忆证据合同）**。

候选贡献必须是以下连接，而不是其中任一单独零件：

1. 从普通运行日志冻结一条**实际被选择且可寻址**的真实来源；
2. 固定 prompt、pose、K/Plücker、retrieval IDs、实际 noise、RNG、非目标来源与干预前初态；目标来源影响的 attention、融合状态、latents 和后续生成等**全部下游后代必须重新计算**；
3. 对同一来源做语义和几何保持不变的低强度外观编辑；
4. 让编辑在该来源的 CLIP、replace/latent 及所有其他真实消费路径中保持一致；
5. 用 `F11 − F00` 作为唯一 total-effect 主比较，`F10/F01` 只诊断路径冲突；
6. 在干预前冻结 source geometry support，比较 support 内外效应；除面积占比外，还用面积、形状、边缘密度和 baseline error 匹配的置换 mask 作零假设；
7. 把 influence、localization 与 signed benefit 保存为不同字段，不用非负敏感度冒充收益；
8. 对同一来源的对称低强度 photometric 变化定义 `B_local`，并在需要时用同场景、同 identity、pose/FoV/support 匹配的未选帧定义 `B_matched`；两者都相对冻结 return reference 计算 loss difference；
9. 检验这些量是否在普通质量指标、检索相似度、注意力、pose/FoV、recency、source quality 和 support area 之外，增量预测自然重访 error/benefit；
10. 若有 oracle headroom，再评估 accept/reject/re-observe 的 AURC、risk–coverage、clean false rejection 和总体 paired loss。

## 6. 最便宜的决定性实验

### 6.1 先找自然问题

- 在真实生成 C1 和强制确认 C2 中分别找可复现的自然重访失败；
- 不允许用合成效应冒充自然视频失败；
- 没有稳定失败，候选直接停止，不为“做方法”而造问题。

### 6.2 建立因果零点

- **A0 exact replay**：完全相同输入和状态重复生成，冻结本底分布；
- **A1 consumer relevance**：最小 source-coherent 外观干预必须显著超过 replay；此处只识别 influence，不预设收益方向；
- 若 A0 波动与 A1 同量级，停止定位主张。

### 6.3 单来源四格试验

- `F00`：原来源进入全部路径；
- `F10`：只改变 CLIP 路径；
- `F01`：只改变 replace/latent 路径；
- `F11`：同一改变进入全部真实路径。

只有 `F11 − F00` 可以估计主 total effect。若效应只出现在 F10/F01，说明存在路径冲突，候选失败。

### 6.4 三道升级门

1. **因果门**：只固定外生条件并重算目标来源全部后代后，total-effect 的配对置信下界超过 exact-replay；
2. **局部门**：geometry enrichment ratio 超过 1，并超过 matched-mask permutation 的 95% 分位；
3. **收益门**：`B_local` 与 `B_matched` 的符号可解释、对 placebo 构造稳定，并在留出数据上优于 attention、pose/FoV、recency、retrieval score、source quality、support area 和简单 gate。

通过第一关只能称“单来源因果敏感性”；通过第二关才能称“source-to-region 局部性”；三关全过且跨场景、跨消费者复现后，才有资格讨论方法贡献。

## 7. 反方解释和 kill 条件

以下任一情况出现就降级或停止：

1. 找不到稳定的真实自然失败；
2. exact replay 波动淹没干预效应；
3. WorldTrace 式 addressability 修复已经解释全部失败；
4. F11 无效而单路径 F10/F01 有效；
5. 局部效应不超过 support 面积基线；
6. 局部富集不超过匹配 mask 的 95% 分位，或效应只是一张漂亮敏感图；
7. `B_local/B_matched` 对 placebo 构造敏感、符号不稳定或没有独立 reference；
8. attention、pose/FoV、recency、retrieval score、source quality、support area 或普通 gate 已达到相同风险—覆盖率；
9. 结果只能在一个场景、一个编辑或一个消费者中复现；
10. 新公开的一手工作完成同一六级联合合同。

## 8. 裁决

本轮没有发现足以直接否定候选的公开一手工作，但 I3DM、WorldTrace、TetherCache、Echo-Memory、CUE-R、WorldKV、CaR、DensityKV、GIM-World 和 Matrix-Game 3.5 已把可主张空间压缩得很窄。当前可保留的差异是：

> **在保留稳定 source ID 且全部消费路径可审计的显式检索式视频世界模型中，条件于普通运行已选择且可寻址的来源集合，对一条来源做 source-coherent post-selection intervention 并重算全部后代；分别检验 influence、干预前 geometry localization 和相对公平替代条件的 signed benefit。**

### 8.1 因果术语纠正

早期文本中的“固定其余内部状态”容易被理解为连目标来源产生的下游中介也冻结。那样得到的不是 total effect，甚至可能把真正的作用路径人为切断。本增量报告将正式含义修正为：**只匹配干预前外生条件与非目标初态，目标来源的所有后代自然重算。** 后续协议和实现必须使用这一版本。

因此继续做 C1/C2 的真实失败与 exact-replay 证据。当前仍是候选创新，`novelty_authorization=NONE`。

### 8.2 收益符号纠正与架构范围

`F11−F00` 的低强度 appearance edit 产生的是非负影响/敏感度，不能自动说明原记忆有益或有害。后续必须单独报告：

- `Influence`：是否超过 exact replay；
- `Localization`：是否超过 geometry support 的 matched-mask null；
- `B_local`：原来源相对同一来源对称低强度 photometric alternatives 的局部收益；
- `B_matched`：原来源相对同场景、同 identity、pose/FoV/support 匹配未选帧的增量收益。

固定普通选择集合后，主估计量只能称 **post-selection downstream effect**，不能称 Store→Select 的全流程总效应。CaR、GIM-World、DensityKV/TetherCache 等不保留天然全局 source item 的架构不在初始主张范围内。

独立反方报告：`INDEPENDENT_ADVERSARIAL_SIX_STAGE_AUDIT_2026-09-08.md`，其裁决是只允许一次低成本证伪实验，不授权 novelty 或 method claim。

## 9. 本轮一手来源

1. [Addressable Memory for Video World Models / WorldTrace](https://arxiv.org/abs/2608.07408)
2. [WorldKV: Efficient World Memory with World Retrieval and Compression](https://arxiv.org/abs/2605.22718)
3. [Compression and Retrieval: Implicit Memory Retrieval for Video World Models / CaR](https://arxiv.org/abs/2606.23105)
4. [DensityKV: Density-Guided KV Cache Compression for Long Video Generation](https://arxiv.org/abs/2608.27922)
5. [Geometry-Aware Implicit Memory for Video World Models / GIM-World](https://arxiv.org/abs/2606.02436)
6. [Matrix-Game 3.5](https://arxiv.org/abs/2608.29910)
7. [I3DM](https://arxiv.org/abs/2603.23413v2)
8. [TetherCache](https://arxiv.org/abs/2606.13035v1)
9. [Echo-Memory](https://arxiv.org/abs/2606.09803v1)
10. [CUE-R](https://arxiv.org/abs/2604.05467v1)
11. [Utility-Oriented Visual Evidence Selection](https://arxiv.org/abs/2605.13277v1)
