# 创新北极星 V1：把“有记忆”改写成“记忆必须为自己的作用负责”

- 冻结时间：2026-09-08T08:42:37Z（Asia/Shanghai 16:42:37）
- 状态：`CONDITIONAL_RESEARCH_DESIGN_NOT_A_NOVELTY_OR_RESULT_CLAIM`
- 当前新颖性授权：`NONE`
- 当前方法运行：`0`
- 依据：Supervisor-Skills 2.2/2.3、`idea-evaluator`、`benchmark-paper-template`、`tech-paper-template`、本机 Claude brainstorming/research/verification 原则
- 证据边界：真实 S40/C1 baseline 已运行；本文件没有新增模型运行，没有读取 C1/C2 像素，也没有方法增益

## 给新手的一句话

多数工作问“模型有没有存到、找回历史”；我们要追问更难的一句：

> **某条被选中的历史记忆，究竟有没有改变生成，是否只改变它几何上负责的地方，以及这个改变到底帮了还是害了？**

如果强 baseline 在普通指标上看似成功，却频繁出现“选中但没用、用了但位置错、位置对但有害”，这会是一个值得报告的新测量问题。只有找到这种真实失败，并证明跨路径来源失配是原因，PC-DPM 才有资格成为方法创新。

## 1. Supervisor-Skills 2.3 的四个创新问题

| 2.3 问题 | 本项目的回答 | 可推翻证据 |
|---|---|---|
| 第一性原理 | 一个 memory item 的价值不由 retrieval score 决定，而由它对最终输出的因果变化和净收益决定 | 干预 selected item 后输出不变，或变化与该 item 无关 |
| 隐藏假设 | 现有评测常默认“stored/retrieved = correctly and beneficially used” | Store/Select/Address 通过，但 Influence/Localization/Benefit 失败 |
| 领域里的大象 | 长时视频论文常报告总体质量、重访一致性或 attention，却少有逐 source 的全消费路径责任证明 | 最近邻若已完整覆盖同一六级合同，则本问题不新 |
| Hamming 重要问题 | 一个世界模型若不能判断记忆是帮助还是伤害，就不能安全扩展到长期交互 | 跨 scene 没有稳定有害记忆，或普通 gate 已完全解决 |

## 2. 三条可选路线

### 路线 A：只做更强的整体一致性分数

优点是最快。缺点是 WorldModelBench、VMem cycle evaluation 和许多重访指标已经覆盖大量空间；单一新分数很难构成高影响贡献。

**裁决：不作为主线。** 只能作为基础测量工具。

### 路线 B：直接给 VMem 增加 source token、camera gate 或 geometry attention

优点是容易实现。缺点是 Movie Weaver、Video Alchemist、WorldStereo、Geometry-as-context、Spatia 与其他近邻已经覆盖 reference identity、分路 attention、相机门控、3D 对应和多路径 memory。模块拼接很容易被审稿人击穿。

**裁决：只作为强 baseline。** M1/M2 必须实现，但不能称创新。

### 路线 C：先建立 GeoCausal Memory Contract，再条件式实现 PC-DPM

这条路线先把 memory 当作可审计的“处理”，用

`Store → Select → Address → Influence → Localization → Benefit`

逐级找断点。若真实断点落在 semantic 与 latent consumer 对同一 source 的身份不一致，再让它们共享同一 provenance 权重，并依据生成前特征执行 `accept / reject / re-observe`。

**裁决：当前推荐。** 它最能把 baseline 的未解失败变成问题定义、机制解释和方法，但也最容易被实验否决。

## 3. 当前最强创新候选

### 3.1 测量贡献：GeoCausal Memory Contract

六级合同不是六个新模块。候选新意是把它们组成一个不能跳步的责任链，并报告传统指标漏掉的失败比例：

1. **Store**：来源是否真的写进 memory；
2. **Select**：普通运行是否真的选中它；
3. **Address**：该来源在目标时刻是否仍可寻址；
4. **Influence**：全 appearance consumer 的 matched intervention 是否真的改变输出；
5. **Localization**：变化是否落在干预前就确定的几何 support，而非任意显著区域；
6. **Benefit**：相对同路径 zero-edit 和公平替代，它对独立真实 reference 的 signed loss 是正还是负。

最有冲击力的实证不是“我们的分数更高”，而是：

> 一个强模型在 retrieval、attention、普通 replay/return 上看似成功，但逐 source 审计显示它没有使用被检索记忆，或把来源作用到了错误位置，或稳定降低真实回访质量。

### 3.2 方法贡献：Provenance-Coupled Dual-Path Memory（PC-DPM）

固定 VMem 源码存在一个可定位但尚未证明有害的不对称：semantic embeddings 在 source 维求均值后广播，而 latent/replace 路径保留 slot 结构。候选机制是保留逐 source semantic token，并让 semantic 与 latent consumer 共用同一个、由目标几何和可寻址性产生的 provenance 权重。

PC-DPM 只有在下列全部成立时才保留：

- 自然回访失败真实存在且相机服从；
- 单独干预两条 consumer 路径得到可重复的冲突效应；
- 全路径同源干预减少冲突；
- 效应落在该 source 的预处理几何 support；
- signed Benefit 在 held-out scenes 可预测；
- 共享 provenance 的增量胜过 token 数、source ID、camera gate、geometry attention、global state、普通 retrieval 和容量匹配对照。

### 3.3 结果贡献：Memory Liability Frontier

若 selected memory 确有正负收益，就报告覆盖率与伤害风险的完整前沿，而不是只挑接受样本：在不同 acceptance coverage 下，测量总体 paired loss、负收益率、clean false rejection、相机服从、support 外画质、时间和内存代价。

这不是先验新颖性声明。Selective prediction 已有 risk–coverage 传统；只有在逐 source 视频 memory 因果标签和跨 consumer 机制上产生额外发现时，它才是本论文的结果贡献。

## 4. 顶会碰撞后保留下来的窄差别

| 已被近邻占据，必须做对照 | 仍待证明的窄差别 |
|---|---|
| VMem 的 3D surfel 检索与 cycle trajectory | 被普通检索选中的单一 source 是否跨所有 consumer 产生局部且有益的因果作用 |
| WorldStereo / I3DM 的几何约束读取或注入 | 同一 source 的 provenance 权重是否必须跨 semantic/latent consumer 同步 |
| Movie Weaver / Video Alchemist 的来源或顺序 token | ordinary memory retrieval 下的跨 consumer 来源责任，不是人工 prompt/reference 绑定 |
| Geometry-as-context 的 camera gate | camera gate 不能解释的 source-level consumer conflict |
| VRAG 的 retrieval + global state | 区分记忆缺失、已选未用、作用错位和记忆有害 |
| activation patching / diffusion neuron localization | 两类 edit、sham、未选 source 负控、已知 consumer 正控和几何零假设组成的视频 memory 责任链 |

## 5. 决定生死的六个预测

| Gate | 预注册问题 | 通过后能说什么 | 失败动作 |
|---|---|---|---|
| P0 | C1/C2/新增 scene 是否出现相机服从且可重复的自然失败 | 存在真实研究对象 | 停止当前机制故事，不制造失败 |
| P1 | F10/F01 是否显示跨 consumer 冲突，F11 是否减少冲突 | source provenance 失配值得研究 | 删除 dual-path 机制 |
| P2 | matched-zero direct effect 是否超过 replay/negative，并通过 shape/camera/source placebo | 影响与 source 的目标几何位置相符 | 删除 geometry-localization 主张 |
| P3 | 同步、未进入 memory 的真实 reference 是否给出稳定 signed Benefit | 有资格学习 accept/reject/re-observe | 降级为 Influence/Localization measurement |
| P4 | M3/M4 是否在 held-out scenes 胜过全部容量匹配强对照 | 有方法增量 | 方法降级为负结果或删除 |
| P5 | support 外质量、相机、运动和成本是否不越界 | 增益没有靠破坏别处换取 | 判方法失败 |

任何一个 gate 都禁止事后换阈值、挑 scene 或删除失败 seed 来保住故事。

## 6. “老师会惊讶”的证据形态

最终需要的是一张任何人都能看懂的反例图，而不是响亮名字：

1. 左侧展示 baseline 检索到正确 source，普通指标也通过；
2. 中间展示逐 source matched intervention，证明该 source 实际未生效、错位或有害；
3. 右侧展示 PC-DPM 只在同一预注册区域修复，并且独立真实 reference 的误差下降；
4. 图下同时列出所有失败 seed、effect size、置信区间、coverage、成本和强对照。

如果只能得到漂亮样例，没有独立 reference、反事实和失败全量统计，就不属于这一级证据。

## 7. 论文逻辑链检查

### 当前定位

现阶段定位为 **New Problem/Setting + Measurement**。PC-DPM 是条件式 Technique 分支，尚未进入论文贡献。

| 环节 | 当前内容 |
|---|---|
| 背景 | 显式 3D memory 正成为长时交互视频世界模型的核心组件 |
| 限制 1 | 现有指标把 retrieval 或整体重访质量近似为 memory 成功 |
| 限制 2 | 多 consumer 可能用不同粒度表示同一来源，来源责任会丢失 |
| 限制 3 | 记忆帮助与伤害被平均，无法做生成前风险控制 |
| 目标 | 建立逐 source、逐 target、跨 consumer 的可否证 memory 责任合同 |
| 挑战 1 | 干预必须与普通路径匹配，避免分布外编辑假象 |
| 挑战 2 | 局部效应必须与预处理几何 support 区分 shape/camera/source 偏置 |
| 挑战 3 | 净收益必须使用同步、未进入 memory 的独立真实 reference |
| 模块 A | 两 edit families + same-path dose-zero + sham/negative/positive controls |
| 模块 B | fractional geometry provenance + independent placebo tests |
| 模块 C | signed Benefit + risk–coverage + held-out scene split |
| 条件式方法 | PC-DPM 共享 provenance；offline teacher，online 不看未来 reference |

四项一致性检查：

- Limitations → Goal：`PASS_CONDITIONAL`
- Goal → Challenges：`PASS_CONDITIONAL`
- Challenges → Modules：`PASS_CONDITIONAL`
- Modules → Contributions：`BLOCKED_BY_NO_REAL_S48_OR_METHOD_RESULT`

## 8. 当前状态与下一步

1. S40 与 C1 的 baseline 生成是真实运行；B0 只有一行有效盲评分，尚不能支持广泛结论。
2. C1 V6 目前只有冻结源码与双解释器 synthetic PASS，等待两份 fresh source review；不得把它写成真实相机结果。
3. C2 V5 仍在 source review，尚无 prepare、attach、authorization、launch、model 或 pixel 结果。
4. S48 V5 因 255 倍单位歧义和 false localization 反例被 BLOCKED；V6 正修订，尚无因果实验。
5. 先完成 P0，再让 S48 V6 经 fresh review；只有 P0–P3 存活才实现 M0–M5。

## 9. 禁止过度声称

当前可以说：已经得到一个经最近邻压力收窄、可被真实实验杀死的创新候选，并有明确的 measurement→mechanism→method 递进路线。

当前不能说：首创已证明、PC-DPM 有增益、S48 已运行、达到 PhD/CCF A 水平、一定会让老师惊讶或保证录用。

