# 机制创新检索：2026-09-15 全网核实（第一批）

**性质：** 文献排重与缺口检索。**只收录我亲自 fetch 并读到内容的页面**；搜索摘要里出现但未打开的内容一律标 `UNVERIFIED`，内容农场站点（如 `moltbook`、`hotmolts`、`arxivlens`）**不予采信**。
**目的：** 找出尚未被覆盖、可证伪的机制创新方向。
**结论先行：项目现有候选 GRC 的核心构想已被 2026 年的工作大面积占据，需要换轴。**

---

## 1. 已核实的工作（按对项目的威胁度排序）

### 🔴 Mem-World / W-VMem —— **最直接的威胁**

- **标题：** Mem-World: Memory-Augmented Action-Conditioned World Models for Persistent Robot Manipulation
- **URL：** <https://arxiv.org/abs/2606.18960>（v1 2026-06-17，v2 06-18）
- **它做了什么（原文摘要）：** 提出 **W-VMem，"4D wrist-view-centered surfel-indexed memory"**，把历史观测锚定到**随时间演化的表面元素**上；"explicitly modeling **when and where** scene elements are observed"，从而实现 **"geometry-aware retrieval of relevant history frames conditioned on future actions"**；生成时 **"relevant history frames are selected via surfel-based rendering and scoring, providing informative and non-redundant context"**。
- **为什么是威胁：** 把 GRC 的四个要素**全部占了**——surfel 几何记忆、几何感知检索、**以未来动作为条件**、**打分选择 + 非冗余**。
- **它没做的：** 面向机器人操作（手腕相机、末端遮挡），不是场景漫游；"non-redundant" 指的是渲染覆盖意义上的信息冗余，**不是误差相关结构**。

### 🔴 Future Forcing —— 抢占了 "future-aware" 这个词

- **标题：** Future Forcing: Future-aware Training-free KV Cache Policy for Autoregressive Video Generation
- **URL：** <https://arxiv.org/abs/2605.30083>（2026-05-28）
- **核心思想（原文）：** 发现自回归视频模型中 **"the underlying canonical pre-RoPE query distribution remains remarkably stable"**，因此**未来 query 分布可从历史统计估计**；据此构造 future query proxy → 按该 proxy 给 KV token 打分 → 在仿射子空间内合并冗余 token。**无需训练**。VBench-Long 60 秒生成上 subject consistency 提升最多 1.49。
- **为什么是威胁：** "预测未来需要什么 → 在固定缓存预算下选择" 这条思路已经在 KV 缓存域实现且免训练。GRC 若只讲"用未来误差指导选择"，会被视为 KV 缓存领域的同类工作换到几何记忆上。
- **它没做的：** 打分依据是 **query 分布代理**，不是**显式的未来误差预测**；对象是时间维 KV token，不是跨视角几何记忆。

### 🔴🔴 GIM-World 第 3.4 节 —— **GRC 的选择机制本身已被发表**

- **标题：** Geometry-Aware Implicit Memory for Video World Models（南京大学 + 快手 Kling 团队）
- **URL：** <https://arxiv.org/abs/2606.02436>（2026-06-01）；全文 <https://arxiv.org/html/2606.02436v1>
- **已由我亲自读原文核实（非摘要转述）**，§3.4 "Information-Guided Pruning" 的目标函数原文是：

  $$S^{\star}=\arg\max_{S}\; I\bigl(S;\,\mathcal{H}\setminus S\bigr)\quad\text{s.t.}\quad|S|\leq K$$

  即 **"在固定基数预算 K 下，最大化保留子集与被丢弃历史之间的互信息"**。这正是 **Krause 等人的 mutual-information sensor-placement 判据**（论文明确引用 Krause et al.），用 **贪心算法**求解。

- **判据的实例化：** 对每帧观测建 **Gaussian process**，核为 **位姿—时间 RBF 核**：

  $$k(c_i,c_j)=\exp\left(-\frac{\lVert p_i-p_j\rVert_2^2}{2\sigma_p^2}-\frac{\angle(\mathbf{f}_i,\mathbf{f}_j)^2}{2\sigma_r^2}-\frac{(t_i-t_j)^2}{2\sigma_t^2}\right)$$

  （$p_i$ 相机位置，$\mathbf{f}_i$ 前向，$t_i$ 时间）。用高斯过程后验方差 $\sigma^2(h\mid A)$ 度量剩余不确定性，贪心选子集。

- **其余组件：** 固定大小可学习 memory query + 两段 transformer 编码器（推理耗时不到扩散主干 **0.3%**）；训练时用 **VGGT** 作冻结几何 teacher，通过 camera-queryable geometry head 以逐 patch 余弦损失 $\mathcal{L}_{geo}$ 蒸馏；条件注入方式沿用 **Context-as-Memory**；数据集为 **MIND**。

- **为什么这是决定性的：** 项目自己的记忆里写着 "GIM 已有 geometry + MI + 固定预算"。**现在从原文确认，这不止是"有相似要素"——数学形式就是 GRC 的选择机制**（几何索引的记忆条目 + 固定预算 + 贪心 + 信息判据）。

- **仍然不同的地方（GRC 仅存的差异）：**
  1. GIM-World 的目标是 **"对丢弃帧的信息量"（冗余/覆盖）**，是**重建被丢弃的历史**；不是**可靠性风险**。
  2. GP 核用**相机位姿/时间**作几何代理，度量的是**冗余**，**不是几何不可靠性**。
  3. 目标是 **重建**，**不是未来预测误差**。

  ⚠️ 但差异 2 和 3 已被 **Mem-World** 与 **Future Forcing** 分别占掉（见上）。**GRC 剩下的可辩护增量很薄。**

### 🟠 DreamX-World 1.0 —— 相机几何检索 + 对不完美记忆的鲁棒化

- **URL：** <https://arxiv.org/abs/2606.16993>（2026-06-15）
- **相关点：** "Memory-Conditioned Scene Persistence **retrieves earlier views through camera-geometry-based retrieval**"；"**residual recycling makes the conditioning path less sensitive to imperfect memory latents**"；训练时**用自己的生成历史**（long-rollout training）以减少风格/颜色漂移。
- **含义：** "相机几何检索"已被做成标准组件；而且他们的应对策略是**钝化对坏记忆的敏感度**（damping），不是**选择或修正记忆**。

### 🟠 Mirage / Latent Spatial Memory

- **标题：** Latent Spatial Memory for Video World Models
- **URL：** <https://arxiv.org/abs/2606.09828>（v1 06-08，v2 08-27，Microsoft）
- **它做了什么：** 把 3D 缓存直接存在**扩散潜空间**，用 depth-guided back-projection 提升 latent token 到 3D，用**潜空间 warping** 查询新视角。相对显式点云基线：端到端生成快 **10.57×**、显存降 **55×**。WorldScore SOTA，RealEstate10K 重建质量强。
- **含义：** "显式点云记忆笨重" 这个动机被大幅削弱——**换表示**这条路已经被走通且效果显著。

### 🟡 R2M-Bench —— **对项目最有价值的一篇**

- **标题：** R2M-Bench: Evaluating Revisit Memory via Relative Consistency in Interactive Video World Models
- **URL：** <https://arxiv.org/abs/2608.27328>（2026-08-27，代码 <https://github.com/AMAP-ML/R2MBench>）
- **它解决的问题（原文）：** "High similarity between first-visit and return frames does not necessarily show that a video world model remembered the scene; the intervening rollout may simply have changed very little." —— 即**绝对回访相似度会被"慢动作/画面几乎没变"作弊**。
- **它的方法：** 对每次回访，取同一条 rollout 里两个对照：**gap-matched 非回访对**（测一般时间稳定性）和**短程对**（测短时一致性）。得到 **MemoryGain (MG)**（回访相对时间基线的优势）与 **Normalized Memory Ratio (NMR)**（用短程到基线的动态范围归一）。评测外观保真、场景/物体身份、局部几何、持久状态。
- **规模：** 100 参考场景 × 3 条"离开—返回"轨迹 = 300 实例；评了 7 个动作条件视频世界模型；Overall NMR 与人类一致性判断 Spearman ρ=0.547（95% CI [0.45,0.63]）；与生成运动的模型内相关为 0.072，而原始回访相似度是 0.207——**相对校准确实削弱了慢动作捷径**。
- **含义：** 项目最缺的"怎么测记忆"这一环，**2026 年 8 月已经被别人定义好了**。这既是坏消息（少了一个可做贡献）也是好消息（**可以直接用**，不必自建）。

### 🟡 Motion Attribution (Motive)

- **URL：** <https://arxiv.org/abs/2601.08828>（v1 01-13，v2 07-03，NVIDIA/Princeton）
- **它做了什么：** 梯度式**数据归因**用于视频生成，用 **motion-weighted loss mask** 把时序动态从静态外观中分离，算 motion-specific influence；据此筛选微调片段，VBench 上 motion smoothness 与 dynamic degree 提升，人类偏好胜率 74.1%。
- **含义：** "归因 + 用归因做筛选"在**训练数据**域已经存在。若项目想做"归因哪条记忆导致重影"，必须说清与训练数据归因的差别。

### 🟡 ViewRope（项目已知）

- **URL：** <https://arxiv.org/abs/2602.07854>，ICLR 2026（<https://iclr.cc/virtual/2026/10018027>）
- 几何感知旋转位置编码，用于一致视频世界模型；ViewBench 上有稀疏注意力对照。

---

## 2. 田野现状总结

| 已被占据的机制轴 | 占据者 |
|---|---|
| 显式深度 + 重投影正则 | GeoVideo (NeurIPS 2025) |
| 显式 3D 建模进视频生成 | World-consistent Video Diffusion (CVPR 2025) |
| 空间索引 / 相机几何检索 | AlayaWorld, DreamX-World, Context-as-Memory |
| 几何条件的历史帧选择 | ViewRope (ICLR 2026) |
| **几何感知检索 + 未来条件 + 打分 + 非冗余选择** | **Mem-World / W-VMem (2026-06)** |
| **未来感知的固定预算缓存策略（免训练）** | **Future Forcing (2026-05)** |
| 几何隐式记忆 + 信息引导剪枝 | GIM-World (2026-06) |
| 潜空间 3D 记忆（快 10.57×、省 55×） | Mirage (2026-06/08) |
| 回访记忆的评测协议 | R2M-Bench (2026-08) |
| 生成内容的运动归因 + 数据筛选 | Motive (2026-01/07) |

**判断：** "挑更好的记忆" 这条轴**已经非常拥挤**。GRC 的原构想（几何风险 + 未来误差 + 固定预算 + 超强基线）**单独拿出来不足以支撑新颖性主张**——至少 Mem-World 和 Future Forcing 各占了一半。

---

## 3. 尚未被占据的缺口（我的判断，需继续排重）

### 缺口 A：**误差相关结构** vs 个体风险

**所有被检索到的工作都假设记忆条目提供独立证据**，因此"更多/更好"就意味着更准。"非冗余"（Mem-World）指渲染覆盖意义上的信息冗余，**不是误差相关**。

但在生成式世界模型里，记忆来自**同一个估计器、同一个生成器**，误差是**系统性相关**的。相关误差下：
- 增加记忆**降低方差的效果被削弱**，甚至**放大偏差**；
- 按个体"质量/风险"排序的贪心选择，可能**提高系统性误差**；
- 第 k 条记忆的边际收益**依赖前 k−1 条**。

**可证伪预测：** 构造两组记忆集合，**个体风险匹配**但**误差相关结构不同**；相关性强的那组应产生**更重的重影**，即使其"平均几何质量"更好。

**为什么不是"多样性选择"换名：** 多样性/覆盖看**输入特征**；这里看**误差结构**。两条记忆可以几何上差异很大却共享同一个系统偏差。

**可在现有资产上测：** 项目的 S15B/S99 已保存固定预测与消费者输出，无需新训练即可构造匹配对照。

### 缺口 B：**混合何时最优** 的理论 + 判据

项目自己的反常观察：**MSE 大幅下降（0.131→0.052）但重影依旧**。检索到的所有工作都在报告一致性指标**改善**，**没有一篇报告"指标改善但伪影没走"**。

项目已有一个两像素反例说明"cycle=0 也可能落点错 20px"。把它推广成一般判据——**软混合 k 条冲突条件何时给出正确后验均值、何时必然产生重影**——既解释了自己的反常，又能导出"该不该混合"的可测判据。

**风险：** 理论工作，若定理平凡则无价值；且需要真实实验支撑而不只是构造反例。

### 缺口 C：**记忆失败归因**的三分解

R2M-Bench 测的是记忆**成功**。"把一次失败分解为几何错 / 选错 / 混合坏"**没有人做**。项目的 2×2 诊断（可信/受扰几何 × 普通/几何约束 RGB）正是这个方向，但项目自己标为"诊断协议，暂不是方法"。

**风险：** 纯诊断难以作为方法贡献；且项目在此已有负结果（S86/S87）。

### 缺口 D：**符号翻转的普遍性**

项目 S99 观察到：同一记忆质量干预对**不同目标符号相反**（低不一致度对随机 3/4 目标更好，但对 confidence 四目标都更差）。**没有检索到任何工作报告这种符号翻转。**

若能被刻画（什么条件下干预有益、什么条件下有害），这直接推翻"更好记忆→更好输出"的领域默认假设，是一个**强的负面结果型贡献**。

---

## 3.5 跨域可迁移机制（子检索二：预算化子集选择）

子检索二系统扫描了 17 个机制族（子模/coreset/主动感知/KV 淘汰/自适应信息获取/数据估值/变点检测等），结论：**所有 2026 年视频与 3D 记忆侧的机制都在优化"期望值"，没有一个做尾部风险；且全部假设"均匀的每项基数预算"。**

### 首推：CVaR 风险厌恶子模最大化

- **出处：** Zhou & Tokekar, *An Approximation Algorithm for Risk-averse Submodular Optimization*, WAFR 2018, <https://arxiv.org/abs/1807.09358>
- **它做什么：** 最大化子模集合函数的 **CVaR（条件风险价值）**，即优化**尾部/最坏分位**而非均值；在 **matroid 约束**下有近似保证（Sequential Greedy，保证含**曲率**依赖项）。
- **为什么可迁移：** 检索到的每一个视频/3D 记忆选择器（GIM-World §3.4、H₂O 的 dynamic submodular、DensityKV、OmniMem、PaFu-KV）**都在优化期望信息量**。而项目的关切不同类：要避免的是"保留的记忆在目标区域**自信地错**"这种**尾部事件**。CVaR 正是"优化最坏分位而非均值"的机器。**未检索到任何视频生成或 3D 缓存工作使用它**（属搜索性缺失，非存在性证明）。

### 次推：非均匀代价的自适应子模（EC²）

- **出处：** Golovin, Krause & Ray, *Near-Optimal Bayesian Active Learning with Noisy Observations*, <https://arxiv.org/abs/1010.3091>
- **为什么可迁移：** 这是检索到**唯一**原生处理**异构代价**与**相关噪声**的代价模型（原文保证"even if the tests have non-uniform cost and their noise is correlated"）。项目的预算写作"固定槽位 / 固定 FLOPs"，但**各项代价实际不同**（远处关键帧的注意力代价 ≠ 稠密 surfel 块），且可靠性分数**噪声空间相关**。所有视频侧工作用的都是**均匀基数预算**。
- **注意：** 机制本身是 2010 年的，但它在这里有意思恰恰是因为**近期没有视频论文移植过它**。

### ⭐ 最重要的：一个零成本的决定性证伪实验

在**现有缓存**上，对一组目标视角，等大小地计算两个子集：

1. **coverage-greedy**（GIM-World 的判据 / 项目已否决的基线）
2. **Δ-greedy**，其中 $\Delta_i$ = 保留第 $i$ 项对**未来预测误差**的降低量

然后报告**两个打分在各项之间的秩相关**（Spearman ρ）。

| 结果 | 含义 |
|---|---|
| **ρ ≳ 0.8** | coverage 是未来误差的**好代理** → GIM-World 的判据已经涵盖 GRC 的意图 → **GRC 塌缩为改名** |
| **ρ 低**，且 coverage 最优子集在目标区域**含有高不可靠项** | **GRC 是真机制的干净证据** |

**不需要重训练**，只需选择 + 评测。

### 已被占、不要再用作主打的

普通贪心覆盖（GIM-World 直接先例）、信息增益 NBV 用于 3D 记忆（FisherRF + risk-aware masking，<https://arxiv.org/abs/2403.11396>）、注意力幅值 KV 淘汰（H₂O <https://arxiv.org/abs/2306.14048>、StreamingLLM <https://arxiv.org/abs/2309.17453>）、冗余/密度去重（DensityKV <https://arxiv.org/abs/2608.27922>）、学习式显著性打分（PaFu-KV <https://arxiv.org/abs/2601.21896>）、检索增强历史（LongLive-RAG <https://arxiv.org/abs/2606.02553>、Context-as-Memory DOI 10.1145/3757377.3763833）、测试时梯度写记忆（GradMem, ICML 2026, <https://arxiv.org/abs/2603.13875>）。

### 另需核查的未决项

- **BOCPD**（Adams & MacKay 2007）用于**作废过期几何记忆**：子检索二**无法取到原始出处**，全部相关说法标 `UNVERIFIED`。项目应把它当作**开放且未被占据**的方向，但引用前必须核实原文。
- `(1-1/e)` 界（Nemhauser–Wolsey 1978）与 Krause–Singh–Guestrin JMLR 全文**未取到**，标 `UNVERIFIED`。

**原始子检索报告：** [`innovation_scan/budgeted_selection_survey.md`](innovation_scan/budgeted_selection_survey.md)（136 行，含 17 族对照表、查询清单、局限声明）；原始笔记 [`innovation_scan/survey_notes.md`](innovation_scan/survey_notes.md)。

---

## 4. 检索方法记录的查询

```
video world model long-term spatial memory retrieval 2026
geometry-aware memory selection video diffusion
correlated errors subset selection marginal benefit dependent items submodular
attribution of artifacts to specific conditioning frames in video diffusion
predicting future view synthesis error from current uncertainty geometry
world model benchmark memory revisit loop closure evaluation 2026
conflicting conditions multi-view diffusion hard selection vs soft blending occlusion aware
error correlation aware selection rather than independent risk retrieval generation
when does conditional averaging produce ghosting posterior mean diffusion theorem
memory write invalidation stale vs wrong world model update
"value of information" select which memory frames to condition video generation future error
geometry conditioned frame selection world model ViewRope
memory retrieval world model predicting which history helps upcoming view
```

**未完成：** 四路并行检索（记忆机制全景 / 预算选择跨域迁移 / 误差归因 / 数据集与评测）仍在运行，结果回来后本文需增补。

**边界：** 本文是**检索记录**，不是新颖性结论。按项目规则，任何候选在升级为方向前必须完成独立排重与前审。本文**不授权**任何新颖性主张。
