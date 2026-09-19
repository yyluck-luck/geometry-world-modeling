# S43 扩展引文网络审计：五项联合合同是否已被最近工作覆盖

- 审计编号：S43-EXPANDED-CITATION-NETWORK-20260908
- 证据冻结：2026-09-07T17:36:27Z（2026-09-08 01:36:27，Asia/Shanghai）
- 主裁决：**KEEP_CONDITIONAL_AFTER_EXPANDED_NETWORK_AUDIT**
- 新颖性授权：**NONE**
- 与 V2 的关系：本文件只完成 V2 要求的扩展检索，不修改或覆盖任何既有冻结文件。

## 1. 给新手的一句话

最接近的论文已经分别做到“固定随机种子后干预内部路径”“把历史图像拆成带三维来源的 patch”“用自然重访衡量记忆收益”。本次可访问的一手证据中，仍没有一篇把这三部分严密地连成同一个实验；这只能支持继续做决定性实验，不能支持“已经证明创新”。

## 2. 证据规则和判定词

科学结论只使用作者论文、官方项目页、官方代码仓库和作者主页。Semantic Scholar 与 OpenAlex 只用于发现前向条目和说明可访问范围，其计数不作为论文能力证据。

本文使用以下判定：

- **FULL**：一手方法明确满足该条件。
- **PARTIAL**：包含相邻能力，但缺少该条件中的关键约束。
- **ANALOGUE_ONLY**：在另一个任务中有严格类比，不能直接算作世界模型合同。
- **NO_IN_CHECKED_SOURCE**：在本次检查到的一手论文、项目页和公开代码范围中没有识别到；不等于领域中不存在。
- **NOT_ASSESSABLE**：只有未公开信号，没有可审方法和实验，不能计为满足或不满足。

“未检到”始终表示“本次可访问范围内没有识别到”，绝不等于“不存在”。任何 NO_IN_CHECKED_SOURCE 都不是新颖性证明。

## 3. 冻结的五项联合合同

候选协议只有同时满足 C1–C5 才算完整近邻：

1. **C1 单项干预**：干预一次真实运行中已经被选择的一条记忆项，而不是关闭整个 memory 模块、整段上下文或任意隐藏单元。
2. **C2 全状态固定**：固定 prompt、pose、intrinsics、检索集合与顺序、非目标记忆、latent/noise、RNG、采样器和其他相关内部状态，以 exact replay 的本底分布为零点。
3. **C3 全消费路径一致**：同一个来源变化进入该来源在真实系统里的所有消费路径；单改 CLIP、latent、KV 或某条 attention edge 只能用于诊断路径冲突。
4. **C4 预处理前几何定位**：输出差异在干预前由来源几何确定的支持区内显著集中，并超过支持区面积占比等机会基线；post-hoc attention map 不足够。
5. **C5 自然失败或收益预测**：单项因果分数对未人工注入的自然重访失败或收益有配对、增量或校准预测，而不只是“干预后画面变了”。

## 4. 五条件压力矩阵

| 一手来源 | C1 | C2 | C3 | C4 | C5 | 五项联合 |
|---|---|---|---|---|---|---|
| [Vision-Language Binding](https://arxiv.org/abs/2605.24624) | NO_IN_CHECKED_SOURCE | ANALOGUE_ONLY | NO_IN_CHECKED_SOURCE | NO_IN_CHECKED_SOURCE | NO_IN_CHECKED_SOURCE | **0/5 FULL** |
| [MosaicMem](https://arxiv.org/abs/2603.17117) | PARTIAL | NO_IN_CHECKED_SOURCE | NO_IN_CHECKED_SOURCE | PARTIAL | PARTIAL | **0/5 FULL** |
| [CaR / Implicit Memory Retrieval](https://arxiv.org/abs/2606.23105) | NO_IN_CHECKED_SOURCE | NO_IN_CHECKED_SOURCE | NO_IN_CHECKED_SOURCE | NO_IN_CHECKED_SOURCE | PARTIAL | **0/5 FULL** |
| [DreamX-World 1.0](https://arxiv.org/abs/2606.16993) | PARTIAL | NO_IN_CHECKED_SOURCE | NO_IN_CHECKED_SOURCE | PARTIAL | PARTIAL | **0/5 FULL** |
| [Matrix-Game 3.5](https://arxiv.org/abs/2608.29910) | PARTIAL | PARTIAL | NO_IN_CHECKED_SOURCE | PARTIAL | PARTIAL | **0/5 FULL** |
| [R2M-Bench](https://arxiv.org/abs/2608.27328) | NO_IN_CHECKED_SOURCE | NO_IN_CHECKED_SOURCE | NO_IN_CHECKED_SOURCE | NO_IN_CHECKED_SOURCE | PARTIAL | **0/5 FULL** |
| [ReWorld](https://arxiv.org/abs/2608.23565) | NO_IN_CHECKED_SOURCE | PARTIAL | NO_IN_CHECKED_SOURCE | NO_IN_CHECKED_SOURCE | PARTIAL | **0/5 FULL** |
| [StateBench / StateAgent](https://arxiv.org/abs/2609.03673) | NO_IN_CHECKED_SOURCE | NO_IN_CHECKED_SOURCE | NO_IN_CHECKED_SOURCE | NO_IN_CHECKED_SOURCE | PARTIAL | **0/5 FULL** |
| MosaicMem V2（作者主页中的 In Progress 项） | NOT_ASSESSABLE | NOT_ASSESSABLE | NOT_ASSESSABLE | NOT_ASSESSABLE | NOT_ASSESSABLE | **不可评估** |

矩阵中的 PARTIAL 不能相加成一个完整合同。例如，一篇论文有几何支持，另一篇有自然重访指标，第三篇有固定种子消融，不代表已有方法在同一运行、同一记忆项和同一预注册协议中完成了 C1–C5。

## 5. 最高压力邻居一：Vision-Language Binding

### 5.1 一手材料

- 论文：[arXiv:2605.24624v1](https://arxiv.org/abs/2605.24624)，2026-05-23。
- 官方项目：[chrisg777.github.io/i2i-interp](https://chrisg777.github.io/i2i-interp/)。
- 官方代码：[ChrisG777/i2i-interp](https://github.com/ChrisG777/i2i-interp)。
- 本地核验的 PDF SHA-256：ec17bf1deffcc4468cd160df2f2c3da7686cd870e1d5f8bc2e225a7fe8503836。
- 代码冻结快照：dca0b97d2788b099933d0b121001cefc6c099762，提交时间 2026-08-26T14:18:01-07:00。

### 5.2 它已经做到什么

论文在 FLUX.2 的统一注意力序列中研究 text、reference-image 和 output/noise tokens 的信息路径，并给出三个干预：

1. T2I Lens 把 I2I 运行中的中间 text activations 复制到无 reference 的 T2I 运行；
2. Attention Knockout 切断 reference→text 或 reference→image 的注意力边；
3. I2I-to-I2I Patching 把 source 编辑运行的 text activations 复制到使用另一张 reference 的 target 运行。

论文覆盖 2,875 个编辑任务，并把可语言描述的 style、color、scene 信息主要定位到 padding text tokens 的中介路径；特定 face 或 instance identity 更多通过 reference→image 直接路径传递。source 与 target 使用不同 noise seeds，因此跨运行属性转移不能简单归因于共享噪声。

官方代码进一步确认 target baseline 与 patched target 重建相同 target prompt、reference、dimensions 和 target seed；source 与 target reference 不同，任务要求相同。这是非常强的固定目标运行因果类比，也是当前候选 C2 设计必须达到的最低标准。

### 5.3 为什么仍不是五项联合合同

- **C1：否。** 被干预的是参考图条件和其中间 text-token activations，不是视频世界模型一次运行中由检索器选择的一条历史记忆项。
- **C2：类比成立。** target baseline 与 patched target 固定 target seed、prompt、reference 和尺寸；但它不是包含检索集合、相机、长期历史、所有消费者缓存的世界模型 exact replay。
- **C3：否。** patching 只替换 text-token 路径，而 target 自己的 reference 路径仍然存在。论文自己报告 patching 并不完美，并推断存在 secondary/backup pathways。Attention Knockout 也切的是选定边，不是让同一来源变化一致地通过所有真实消费者。
- **C4：否。** “padding token 定位”是序列位置定位，不是由相机几何在干预前定义的输出区域，也没有 mask-area 机会基线。
- **C5：否。** 主论文测的是受控 I2I 属性传递，不是自然重访失败或收益预测。

### 5.4 论文后官方代码的新信号

2026-08-26 的官方仓库加入 repair/amplify 实验：先筛选 style-transfer 失败，再放大 text_from_ref、image_from_text 或 image_from_ref 路径。仓库中的结果表包含 450 条 baseline census、130 条 strict failures、31 条 subject failures、390 条 amplification census 以及 54 条 rescue 记录。

这些文件说明作者已把“机制诊断”向“失败修复”推进。但各表的任务池和判分条件不完全相同，本审计不计算或宣称统一修复率。它仍是普通 I2I 的后验失败筛选与路径放大，没有运行时选中记忆项、几何支持、面积基线或预注册的自然重访预测。因此它是强邻接信号，不把 C5 升为 FULL。

## 6. 最高压力邻居二：MosaicMem

### 6.1 一手材料

- 论文：[arXiv:2603.17117v1](https://arxiv.org/abs/2603.17117)，2026-03-17。
- 官方项目：[mosaicmem.github.io/mosaicmem](https://mosaicmem.github.io/mosaicmem/)。
- 官方项目页在证据冻结时明确显示 “Code (Coming)”；本次没有取得可核验的 MosaicMem V1 官方代码链接。这只是当前公开状态，不代表以后不会发布。
- 本地核验的 PDF SHA-256：cdb0c9c4401775f1ca050c123095ce2f4f9aa9eb8311a76b363018346ff15e3e。

### 6.2 它已经做到什么

MosaicMem 把 VAE/image patches 作为记忆基本单元，用 depth、intrinsics 和 pose 提升到三维，再投影到目标视图并组成 memory canvas。Warped RoPE 与 Warped Latent 用于修正 memory patches 和目标 latent 的空间对齐。系统支持 sparse/dense retrieval、patch 删除、复制、移动、跨场景拼接、分钟级导航和自回归 rollout。

它的 Consistency Score 在人工标注的对应区域内计算 SSIM、PSNR 和 LPIPS。这已经占据两块重要空间：

- 历史来源具有局部 patch 粒度和三维几何位置；
- 评估可以限制在对应的局部区域，而不只看全图平均。

论文还公开了自然系统失败：大相机运动可能检不到足够 patches；Warped RoPE 在边界附近可能生成新物体；Warped Latent 与其组合能缓解部分问题。

### 6.3 为什么仍不是五项联合合同

- **C1：部分。** 系统能选择、移动或删除 patches，但论文没有给出对某一次普通推理中已经选中的单一 patch 做 matched intervention 并估计其独立因果效应的协议。
- **C2：否。** 论文的模块比较和编辑演示没有把检索 ID、其他 memory、noise/RNG、pose 和所有相关内部状态冻结为 item-level exact replay。
- **C3：否。** 没有证明同一来源的 patch、latent、context 或其他可能重复证据在全部消费路径中同步变化。
- **C4：部分。** 它有干预前可得的三维 patch correspondence，也有对应区域内的质量分数；缺少的是“F11−F00 输出差异在预冻结 support 内集中”及相对于 support 面积占比的因果定位检验。
- **C5：部分。** 论文展示自然重访收益和系统级失败，却没有用单项因果分数预测哪些自然重访会失败或从该项获益。

MosaicMem 因此使“patch 级三维记忆、几何对应区、局部编辑”本身不能再成为创新主张。仍可检验的只剩严格 item-level、all-path、geometry-localized、natural-error-predictive 的连接。

## 7. CaR 与 DreamX-World 是否进一步挤压

### 7.1 CaR：连续隐式检索挤压 Select/Consume，但缺少可干预单项

[Compression and Retrieval: Implicit Memory Retrieval for Video World Models](https://arxiv.org/abs/2606.23105) 把压缩后的全历史上下文作为 attention keys，通过相对相机 pose 让 target queries 连续地检索相关内容。论文用 A→B→C→B→D→B→A 的受控轨迹展示接近目标视角的历史 clip 获得更强 attention，并用 PSNR、SSIM、LPIPS 和 FVD 评估重访。

- 官方仓库：[Orange-3DV-Team/CaR](https://github.com/Orange-3DV-Team/CaR)。
- 代码冻结快照：8823c03544dfdd9a98966451e24b97fd5ad7ab76，2026-08-14T19:06:07+08:00。
- 本地 PDF SHA-256：5385a8ced32607991cdc6e3d4dd6179dcd740668acb6e8fbed6dc97fad1a0206。
- 冻结仓库已提供 inference；README 仍把 training、完整 checkpoint/full SceneFly 等部分列为待办，不能把公开推理误写成完整复现实验包。

CaR 的检索是分布在连续 attention 上的软策略，没有自然的“一个已经选中的离散 memory item”。论文没有 item-level intervention、全状态固定 replay、全路径同源干预、几何 effect mask/area baseline 或 per-item causal predictor。它让候选必须解释连续检索时如何定义干预单位，但没有完成 C1–C5。

### 7.2 DreamX-World：几何检索、错误记忆鲁棒性和重访基线都已拥挤

[DreamX-World 1.0](https://arxiv.org/abs/2606.16993) 的 Memory-Conditioned Scene Persistence 用视角重叠选择较早 memory frames，把 memory、recent context 和 target latents 放入同一 self-attention 条件流。Residual Recycling 扰动 conditioning tokens 而保持 target clean，使模型学习在 memory 有用时使用它，并在不完美 memory latent 下回退到生成先验。

其自然重访协议包括 out-and-back、heading-change 和 loop-closure；评估覆盖 pixel、perceptual、semantic、place-recognition 和 geometric consistency，并用匹配 temporal gap 的 non-revisit pairs 作为行为基线。这使“用自然重访和 gap-matched baseline 检查记忆”不再新。

- 官方项目：[AMAP DreamX-World](https://amap-ml.github.io/DreamX_World/)。
- 官方代码：[AMAP-ML/DreamX-World](https://github.com/AMAP-ML/DreamX-World)。
- 官方模型：[GD-ML/DreamX-World-5B](https://huggingface.co/GD-ML/DreamX-World-5B)。
- 代码冻结快照：a1f4c6e5e45600718e5236955f2e0702e53fc275，2026-07-23T17:44:29+08:00。
- 本地 PDF SHA-256：8524f77fb6c10071f6098a285abf086b13f6a7a117ddcaf3470c2ca3d90bc122。

DreamX 仍没有在固定 replay 中改变一个实际选中的 memory frame、统一处理该来源的全部路径、把输出因果差异定位到 pre-treatment geometry support 并超过面积基线，或让该 item 的因果分数预测自然重访收益。因此它强烈挤压 C5 的行为侧，却没有封闭五项合同。

## 8. 后向引用网络

### 8.1 Vision-Language Binding 的后向网络

官方 PDF 含 25 条编号参考文献；本审计对 25 条题名和论文中的使用语境进行筛查，并对最接近的机制工作检查一手论文：

- [Localizing and Editing Knowledge in Text-to-Image Generative Models](https://proceedings.iclr.cc/paper_files/paper/2024/hash/4bfcebedf7a2967c410b64670f27f904-Abstract-Conference.html)：定位并编辑 T2I 内部知识；
- [How to Use and Interpret Activation Patching](https://arxiv.org/abs/2404.15255)：说明 activation patching 的干预和解释边界；
- ConceptAttention、Follow the Flow、Diffusion Lens、Padding Tone：覆盖 diffusion 内部概念、text-token 流和 padding token 机制；
- [I2AM](https://proceedings.iclr.cc/paper_files/paper/2025/hash/c4a59e985de8b134328f41a47bc7dfac-Abstract-Conference.html)：reference-to-generated bi-attribution 与局部区域评价；
- What’s in the Image?：VLM 视觉信息流的机制分析。

这一后向网络已经覆盖 activation patching、attention routing、reference-to-output attribution 和空间/序列定位。它没有在已查材料中把这些工具用于“运行时选中的视频记忆项 + 全路径一致反事实 + pre-treatment geometry/area + 自然重访预测”的完整合同。

### 8.2 MosaicMem 的后向网络

官方 PDF 实际列出 49 条编号参考记录；Semantic Scholar 的去重/匹配元数据显示 46 条。两者口径不同，本审计采用论文的 49 条作为书目事实，不把索引数当作论文参考文献总数。

对 49 条题名与上下文完成筛查，最接近的记忆/几何论文进一步核查如下：

- [Spatia](https://arxiv.org/abs/2512.15716)：可更新 spatial memory；
- [WorldPack](https://arxiv.org/abs/2512.02473)：压缩 memory；
- [VMem](https://arxiv.org/abs/2506.18903)：surfel-indexed view memory；
- [SPMEM](https://arxiv.org/abs/2506.05284)：长期 spatial memory；
- [Context as Memory](https://arxiv.org/abs/2506.03141)：基于视场/几何的历史帧检索；
- [WorldMem](https://arxiv.org/abs/2504.12369)：带状态的长期 memory；
- [Gen3C](https://arxiv.org/abs/2503.03751)：显式三维条件与相机控制；
- [RELIC](https://arxiv.org/abs/2512.04040)：长时 memory；
- [PRoPE](https://arxiv.org/abs/2507.10496)：相机投影相对位置编码；
- [PE-Field](https://arxiv.org/abs/2510.20385)：空间位置编码场。

这些工作共同使 memory container、pose/FoV retrieval、3D correspondence、compressed tokens、patch/point/surfel representation 均处于拥挤区。本次没有在这些一手材料中识别到五项联合协议；这个范围结论不能外推为领域不存在。

## 9. 前向引用网络及可访问范围

### 9.1 发现索引的边界

证据冻结时的二级发现快照：

| 目标 | Semantic Scholar 可访问结果 | OpenAlex 快照 | 可下的结论 |
|---|---:|---:|---|
| Vision-Language Binding | metadata 请求遇到 429；单独 citations endpoint 返回空列表 | cited_by_count=0，updated 2026-07-28 | **无法给出可靠前向枚举或零引用结论** |
| MosaicMem | 14 个 citing records，referenceCount=46 | cited_by_count=0，updated 2026-07-28 | S2 的 14 条用于候选发现；OA 快照明显滞后于部分 8–9 月论文 |
| CaR | 1 个 citing record | cited_by_count=0，updated 2026-07-28 | 检查已返回的 R2M-Bench；不能保证全集 |
| DreamX-World | 单独 endpoint 返回 19 个 citing records | cited_by_count=0，updated 2026-07-28 | 19 条用于候选发现；不能称穷尽 |

索引分歧说明引用网络仍在快速变化。下文只如实列出当时接口返回的候选；论文能力判断回到对应 arXiv/官方页面。

### 9.2 MosaicMem 的 14 条可发现前向候选

S2 快照返回：

1. [SolarWM](https://arxiv.org/abs/2609.02886)
2. [Matrix-Game 3.5](https://arxiv.org/abs/2608.29910)
3. [Code World Model](https://arxiv.org/abs/2608.25927)
4. [Addressable Memory for Video World Models / WorldTrace](https://arxiv.org/abs/2608.07408)
5. [Streaming Multi-Agent Autoregressive Diffusion Model with World State Registers](https://arxiv.org/abs/2607.21594)
6. [PE-Field 4D](https://arxiv.org/abs/2607.15667)
7. [DreamX-World 1.0](https://arxiv.org/abs/2606.16993)
8. [WorldOlympiad](https://arxiv.org/abs/2606.11129)
9. [Geometry-Aware Implicit Memory for Video World Models](https://arxiv.org/abs/2606.02436)
10. [Effective Multi-sensor Conditioning for Street-view Novel-view Synthesis](https://arxiv.org/abs/2606.01590)
11. [Towards Interactive Video World Modeling: Frontiers, Challenges, Benchmarks, and Future Trends](https://arxiv.org/abs/2606.01164)
12. [ReMind](https://arxiv.org/abs/2605.25333)
13. [SANA-WM](https://arxiv.org/abs/2605.15178)
14. [Matrix-Game 3.0](https://arxiv.org/abs/2604.08995)

对 14 条均做一手题名/摘要筛查；对 Matrix-Game 3.5、DreamX、WorldTrace/GIM/ReMind 等高相关项做方法级复核。没有在可检查范围中识别到 C1–C5 全部 FULL。最强新增压力是 Matrix-Game 3.5。

### 9.3 DreamX 的 19 条可发现前向候选

S2 快照返回的 arXiv IDs 为：

2609.03557、2609.03673、2609.02886、2608.31106、2608.29910、2608.27168、2608.25927、2608.23070、2608.23565、2608.23189、2608.23383、2608.16859、2608.14022、2608.13489、2607.26037、2607.14076、2607.07534、2606.30292、2604.21686。

对应条目包括 data pipeline、StateBench、SolarWM、DreamX-Creator、Matrix-Game 3.5、Magpie、Code World Model、world-model survey/simulator analyses、ReWorld、EchoWM、audio-visual world models、HarnessEval-W、ForgeWM、DreamX-Phi、Wonder、Pixels-to-States、Infinite Worlds、DreamForge 和 WorldMark。对 19 条均做一手题名/摘要筛查；对 Matrix-Game 3.5、ReWorld 与 StateBench 做全文方法级复核。没有在该可访问集合中识别到五项联合合同。

### 9.4 CaR 的可发现前向候选

S2 返回一条：[R2M-Bench](https://arxiv.org/abs/2608.27328)。该 benchmark 有 300 个实例、同一 rollout 内 gap-matched baseline、short-range dynamic range、MemoryGain 和 NMR。论文明确说明 positive MemoryGain 不应解释为内部 memory mechanism 的因果估计，且架构、规模、训练和推理差异阻止把模型间差异因果归结到 retrieval。

R2M-Bench 因而是 C5 的强行为基线，但没有内部 item intervention、全路径反事实或几何 effect localization。未来实验应把 MG/DR/NMR 纳入自然重访分层，而不能把 MG 当作 C1–C4 的替代品。

## 10. 最强公开压力：Matrix-Game 3.5

[Matrix-Game 3.5](https://arxiv.org/abs/2608.29910) 由 MosaicMem 作者 Runjia Qian、Wei Yu 等继续推进，并提供[官方项目](https://matrix-game-v3-5.github.io/)和[官方代码](https://github.com/Riemann-Dynamics/Matrix-Game-3.5)。它是本次审计中对候选最强的公开压力：

1. 每个历史 latent patch 用 depth、intrinsics 和 pose 提升到三维，再投影到目标相机。
2. z-buffer 对每个 target cell 选择最近可见 surface。
3. aligned memory canvas 的 reverse map 记录 source frame 和原 patch location。
4. patch memory、context memory、anchor、target 和 dynamic-subject reference tokens 进入同一 pose-aware self-attention 序列。
5. 论文给出一个固定 initial state、camera trajectory、text prompt 和 random seed 的消融，只移除整个 dynamic-subject reference prefix；移除后身份和局部外观漂移。

这意味着以下元素已不能单独声称新颖：patch-level 3D provenance、几何 support、统一 token sequence、固定种子 memory-module ablation、长期重访和 subject mask。

它仍没有完成：

- 对正常运行中一个被选 patch/source 的匹配干预；
- 让该来源在 patch、context、reference 等所有可能重复路径中一致变化；
- 用 F11−F00 把生成差异定位到干预前 support 并超过面积基线；
- 用 per-item causal score 预测自然重访失败/收益。

因此 Matrix-Game 3.5 将候选从“几何 patch memory”压缩为更窄的“source-total-effect + geometry-localization + natural-error prediction”联合测量问题。它不推翻这条联合问题，但显著提高了决定性实验的门槛。

## 11. 其他高压力前向工作

### 11.1 ReWorld

[ReWorld](https://arxiv.org/abs/2608.23565) 使用 pose-indexed MRoPE，把 bounded KV cache 中的历史 chunks 按 pose proximity 作为 landmarks 检索。其 palindrome protocol 对每个方法固定 camera intent、matched prompt 和 seed，并对 mirror revisit pairs 用 SSIM、LPIPS、DINO 与 ORB 评价。

它提供固定 seed 的自然重访协议和模块/cache-policy 消融，但不是单一已选来源的 causal replay；没有 all-path mutation、geometry effect mask/area baseline 或 per-source predictor。它加强 C2/C5 的基线要求，不完成联合合同。

### 11.2 StateBench / StateAgent

[Do Video Generators Track the World Across Segments?](https://arxiv.org/abs/2609.03673) 明确区分 observation memory 与 state reasoning。StateBench 的任务让关键状态在段落边界被遮挡或模糊，要求模型依据历史事件推断此刻真正的 world state，而不是复制最后可见外观。

它没有内部单记忆项干预和几何定位合同，但暴露一个关键混淆：一条视觉 memory 即使几何正确、外观相似，也可能已经因事件更新而变成 stale evidence。候选后续的自然错误标签必须区分“没用到正确历史”“用了已经过期的历史”和“状态更新推理失败”。

## 12. 作者近作

### 12.1 Vision-Language Binding 作者侧

- Chris Ge 的[官方主页](https://chrisg777.github.io/)列出 VLB、Agent Psychometrics 和 Private Linear Regression；后两项没有视频记忆几何合同。
- Rohit Gandikota 的[官方主页](https://rohitgandikota.github.io/)列出 [Gaze Heads](https://arxiv.org/abs/2606.14703)：用少量 attention heads 跟随当前描述区域，并通过 attention-mask intervention 因果地把 VLM 文本描述重定向到指定图像区域。它进一步说明“区域级因果路由”已经是公开能力，但任务是 VLM 语言输出，没有 world memory、revisit、pre-treatment 3D support 或五项联合合同。
- [Distilling Diversity and Control](https://arxiv.org/abs/2503.10637) 用首个 diffusion timestep 的干预恢复多样性；它强化机制定位和修复的邻接压力，但不是记忆来源审计。
- Tamar Rott Shaham 的[官方主页](https://tamarott.github.io/)列出 MAIA、FIND、belief tracking 等自动/因果解释工作；本次没有在主页列出的近作中识别到目标视频记忆合同。

### 12.2 MosaicMem 作者侧

Matrix-Game 3.5 是最相关的已公开近作，已经单列为最高压力。它由 MosaicMem 作者 Runjia Qian、Wei Yu 参与，论文、项目和代码均公开，因此作为科学证据计入压力矩阵。

## 13. 未公开信号必须单独处理：MosaicMem V2

Wei Yu 的官方主页源码 [papers.js](https://github.com/gnosisyuw/gnosisyuw.github.io/blob/main/content/papers.js) 列出：

- 标题：MosaicMem V2: Object-Centric Controllability on a Memory Canvas for AI Game Worlds
- 作者：Wei Yu, Runjia Qian, Dennis Anthony, Yumeng Li, Weiwei Wan, Animesh Garg
- venue：In Progress
- 摘要信号：在 persistent memory canvas 上做 object-centric controllable generation，面向 interactive AI game worlds

证据冻结时：

- 作者主页仓库 HEAD：f61d2619cbf0d45761a6fef725c00756a105dab1；
- papers.js blob：a25aa36d576dbb52f62ddfd77d2d6ba2d2745da3；
- 该文件最近提交：281ee746593892f7b49a176b6aa3afa3d853ce6d，2026-04-09；
- 条目没有 url、paper 或 code 字段，只有 media；
- 精确标题的 arXiv 和 GitHub 一手检索没有取得公开论文或代码。

这是一条**UNPUBLISHED_SIGNAL**，不是一篇可评审科学论文。C1–C5 必须全部标为 **NOT_ASSESSABLE**，不得因摘要措辞推断满足或不满足，不得把它计入“已查论文没有做到”的分母。

它同时是最高优先级监测风险。若公开版本出现下列任一组合，应立即重审候选：

- 单对象或单 patch 的 source-coherent replay；
- geometry effect concentration 加 mask-area baseline；
- per-item 分数对自然重访错误或收益的预测；
- 尤其是以上三项与 fixed-state、all-consumer-path intervention 同时出现。

## 14. 裁决与研究边界

### 14.1 本次可以说什么

**KEEP_CONDITIONAL_AFTER_EXPANDED_NETWORK_AUDIT**：在本次明确列出的、证据冻结时可访问的一手论文/项目/代码范围中，没有识别到一项同时满足 C1–C5 的公开协议。

最接近的能力已被不同工作占据：

- VLB：固定目标 seed 的 causal path patching；
- MosaicMem / Matrix-Game 3.5：patch geometry、provenance 与 aligned support；
- DreamX / ReWorld / R2M-Bench：自然重访、gap-matched behavior 和 fixed-seed protocol；
- StateBench：stale observation 与真实 world state 的区分。

因此候选只有在同一实验里闭合五项合同，并超过这些分项基线，才可能产生有区分力的贡献。

### 14.2 本次不能说什么

- 不能说“首个”“领域不存在”“已证明新颖”或“达到 CCF-A”。
- 不能把 Semantic Scholar/OpenAlex 的返回数量当作穷尽检索。
- 不能把 MosaicMem V2 的 In Progress 摘要当作论文方法证据。
- 不能把 R2M 的 MemoryGain、DreamX 的 revisit gains、attention maps 或 fixed-seed module ablation 当作 item-level causal score。
- 不能把多个不同论文分别满足的局部能力拼接成一篇已满足完整合同的工作，反过来也不能由它们分散存在就断言联合合同必然新。

### 14.3 继续路线的最小强制要求

下一轮实验必须预注册并实现：

1. exact replay 本底；
2. 正常运行已选择的一条 source；
3. F00/F10/F01/F11，其中只有 F11−F00 是总效应主比较；
4. 干预前冻结的 source geometry support；
5. support 内外效应、面积基线和配对置信区间；
6. 自然重访 error/benefit 标签，以及 item causal score 的增量预测；
7. R2M 的 gap-matched MG/DR/NMR 作为行为层对照；
8. stale-but-geometrically-valid memory 的 state-update 对照；
9. Matrix-Game 3.5 式 patch provenance 与 fixed-seed module ablation 作为强基线。

若上述联合实验失败，候选应降级为诊断工具或 baseline 分析；若 MosaicMem V2 或其他公开一手来源先完成五项联合合同，应立即触发 kill/reposition。

## 15. 一手来源索引

### 核心目标

1. [Vision-Language Binding paper](https://arxiv.org/abs/2605.24624)
2. [Vision-Language Binding project](https://chrisg777.github.io/i2i-interp/)
3. [Vision-Language Binding code](https://github.com/ChrisG777/i2i-interp)
4. [MosaicMem paper](https://arxiv.org/abs/2603.17117)
5. [MosaicMem project](https://mosaicmem.github.io/mosaicmem/)
6. [CaR paper](https://arxiv.org/abs/2606.23105)
7. [CaR code/project](https://github.com/Orange-3DV-Team/CaR)
8. [DreamX-World paper](https://arxiv.org/abs/2606.16993)
9. [DreamX-World project](https://amap-ml.github.io/DreamX_World/)
10. [DreamX-World code](https://github.com/AMAP-ML/DreamX-World)

### 高压力前向与作者近作

11. [Matrix-Game 3.5 paper](https://arxiv.org/abs/2608.29910)
12. [Matrix-Game 3.5 project](https://matrix-game-v3-5.github.io/)
13. [Matrix-Game 3.5 code](https://github.com/Riemann-Dynamics/Matrix-Game-3.5)
14. [R2M-Bench](https://arxiv.org/abs/2608.27328)
15. [ReWorld](https://arxiv.org/abs/2608.23565)
16. [StateBench / StateAgent](https://arxiv.org/abs/2609.03673)
17. [Gaze Heads](https://arxiv.org/abs/2606.14703)
18. [Wei Yu official homepage source](https://github.com/gnosisyuw/gnosisyuw.github.io/blob/main/content/papers.js)

## 16. 最终审计句

> 本次扩展后向、前向和作者网络没有在已核一手来源中推翻五项联合缺口；Matrix-Game 3.5 把公开压力推到 patch provenance、统一注意力和固定种子模块消融，MosaicMem V2 则构成不可评估但必须监测的未公开风险。裁决仅为继续做严格、可证伪实验，novelty_authorization 仍为 NONE。
