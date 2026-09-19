# S43 独立对抗审查：六级几何因果记忆合同还能否区分

- 审查时间：2026-09-08T12:56:09+08:00
- 身份：独立 adversarial novelty audit；本文件不是 canonical S43 报告，也不改写既有冻结结论
- 候选对象：对普通运行中实际选中、当前可寻址的一条记忆来源做 source-coherent、all-consumer-path 反事实；只固定外生条件与非目标初态，重算目标来源的全部后代；随后检验输出效应的干预前几何局部性，以及 item-level 有符号分数对自然重访错误/收益的样本外预测
- 方法：依照 Supervisor-Skills `02_Idea_Generation`，尤其 2.3 的重要问题、隐藏假设、elephant-in-the-room、技术周期与 kill test；检索策略是搜索反例和等价工作，不把关键词未命中当作新颖性证据
- 当前裁决：**KEEP ONLY AS AN ARCHITECTURE-SCOPED JOINT EVIDENCE CONTRACT**
- 新颖性授权：**NONE**

## 1. 结论先行

`Store → Select → Address → Consume → Localize → Benefit/Accept` 仍可作为一个**联合证据合同**与已核工作区分，但只在下面这个很窄的范围内：

> **显式检索式视频世界模型，且系统保留稳定 source ID，并能审计同一来源进入的全部真实消费路径。** 对普通运行实际选择且当前可寻址的一条来源，估计其条件于原始选择集合的、跨全部下游路径的 source-coherent 因果效应；检验该效应是否落在干预前定义的几何支持区；再检验 item-level 有符号因果分数能否在 attention、pose/FoV、recency、retrieval score、source quality 和 support area 之外，增量预测留出自然重访的收益或伤害。

这不是六个新部件，也不是当前可宣称的新算法。每一层都已有强近邻：WorldTrace 占据 Address，WorldKV/I3DM/CaR/TetherCache 占据 Select/Consume，I3DM/MosaicMem/Matrix-Game 3.5/GIM-World 占据 geometry-aware routing，Echo-Memory 占据 Store-vs-readout 的受控分解，Vision-Language Binding/LocoGen/Activation Patching 占据因果路径干预，CUE-R 占据“实际使用的单项证据→remove/replace/duplicate→多轴有符号 utility”。当前只剩这些环节的**严格连接**尚可验证。

这个连接仍可能被审稿人视为显然组合。它只有在产生一个非显然经验规律时才有论文价值，例如：

1. attention/pose 选中的记忆经常有零或负的 signed utility；
2. 同一来源在两个真实消费路径中产生方向相反的作用；
3. 几何看似有效的来源却把影响扩散到支持区外，并预测自然重访失败；
4. causal-local score 在强检索分数和 gate 之后仍有稳定的样本外增量预测力。

如果只得到“改一条来源，输出会变”或“支持区内比随机区域亮”，应降级为诊断或实现验证。

## 2. 最接近的五组作者—年份

1. **Jia Li et al., 2026，I3DM**：从历史帧生成空间置信图、做最大覆盖选择、3D 对齐，并把可靠区域注入视频生成器；这是几何选择与局部消费的最近直接压力。[最新版 arXiv v2，31 Jul 2026](https://arxiv.org/abs/2603.23413v2)
2. **Xindi Wu et al., 2026，WorldTrace**：指出“已存储”不等于“当前可寻址”，用 in-distribution 虚拟位置维护长时 KV 的可寻址性。[arXiv v1，7 Aug 2026](https://arxiv.org/abs/2608.07408v1)
3. **Yu Meng et al., 2026，TetherCache**：GRAB 用 attention relevance 与 temporal diversity 做 memory admission，TAME 编辑 recalled tokens；generic select/gate/repair 已被直接占据。[arXiv v1，11 Jun 2026](https://arxiv.org/abs/2606.13035v1)
4. **Wayne King et al., 2026，Echo-Memory**：在共享 backbone/training/sampler/eval 下分开 capacity、compression、read-out、recurrence，并用 replay/in-domain/open-domain 三分支显示 store 不等于 usable readout。[arXiv v1，8 Jun 2026](https://arxiv.org/abs/2606.09803v1)
5. **Siddharth Jain and Venkat Narayan Vedam, 2026，CUE-R**：对模型报告实际使用的一条检索证据做 REMOVE/REPLACE/DUPLICATE，计算多轴 utility 与双证据非加性；广义“per-item intervention→utility”已被占据。[arXiv v1，7 Apr 2026](https://arxiv.org/abs/2604.05467v1)

## 3. 六级合同逐层压力图

| 工作 | Store | Select | Address | Consume | Localize | Benefit/Accept | 对候选的结论 |
|---|---:|---:|---:|---:|---:|---:|---|
| [WorldTrace](https://arxiv.org/abs/2608.07408v1) | 是 | 部分 | **强** | 系统级 | 否 | 系统级 | Address 不能再藏在 Consume 中；若地址修复解释失败，候选降级 |
| [WorldKV](https://arxiv.org/abs/2605.22718v1) | **强** | **强** | 部分 | **强** | attention/视角对应，不是因果局部图 | 系统级 | chunk 级 Store/Select/Consume 已有；不能主张“选择历史并重新注入” |
| [CaR](https://arxiv.org/abs/2606.23105v1) | 是 | 连续 attention | 隐式 | **强** | 视角/FoV 驱动 | 系统级 | 没有一个全局离散 selected item；六级合同不应声称覆盖这类模型 |
| [DensityKV](https://arxiv.org/abs/2608.27922v1) | **强** | 每层/每 head token 准入 | post-RoPE key | **强** | admission trace，不是输出因果定位 | 系统级 | 简单 token retention heatmap 不新；干预单位需另定义 |
| [GIM-World](https://arxiv.org/abs/2606.02436v1) | 压缩 state | 信息剪枝 | camera-queryable | 是 | geometry feature map | 系统级 | 压缩后无 frame/patch 一一对应；不属于初始“稳定 source ID”范围 |
| [I3DM](https://arxiv.org/abs/2603.23413v2) | 帧 bank | **空间置信图+最大覆盖** | 直接帧索引 | **3D-aligned injection** | **可靠区域图** | 聚合重访收益 | 与 Select/Consume/Localize 四层高度重叠；只剩 source-coherent 因果效应和自然 signed utility 预测 |
| [MosaicMem](https://arxiv.org/abs/2603.17117v1) | 3D patch | target-view retrieval | patch provenance | aligned conditioning | **显式几何 patch** | 系统级 | 几何局部、provenance、编辑接口都不能称新 |
| [Matrix-Game 3.5](https://arxiv.org/abs/2608.29910v1) | patch/context/reference | coverage-aware | tiled PRoPE | unified self-attention | **reverse source map** | 系统级 | source provenance 和几何支持很接近；若以 patch 为单位，合同需重新定义 |
| [TetherCache](https://arxiv.org/abs/2606.13035v1) | 分层 KV | **GRAB admission** | 当前 cache layout | native attention | 否 | **gate+TAME repair+系统收益** | gate/admission/repair 不是核心新颖性 |
| [Echo-Memory](https://arxiv.org/abs/2606.09803v1) | 多种 | 不以单项为主 | 部分 | **read-out 路径消融** | 否 | 三分支 metric bundle | Store≠Consume、raw-context 强基线和多分支评测已被占据 |
| [CUE-R](https://arxiv.org/abs/2604.05467v1) | evidence set | **优先实际 used item** | 可见 chunk ID | 黑盒输出 | trace，不是视频几何 | **单项多轴 utility** | broad per-item counterfactual utility 已有；只可主张视频世界模型特有连接 |
| [Vision-Language Binding](https://arxiv.org/abs/2605.24624v1) | 外部 reference | 不适用 | token sequence | **knockout/patching 的多路径因果** | token/路径 | 否 | source-to-output causal routing 不是空白；all-path 必须显示额外科学发现 |

## 4. 三项指定工作的精确版本与代码证据

### 4.1 TetherCache

- 论文：[*TetherCache: Stabilizing Autoregressive Long-Form Video Generation with Gated Recall and Trusted Alignment*](https://arxiv.org/abs/2606.13035v1)，arXiv:2606.13035v1，submitted 11 Jun 2026。
- 官方项目：[TetherCache project](https://my4f175.github.io/TetherCache/)。
- 官方代码快照：[commit `37c581ace23ff5df201f45e8282065d19b4ace8c`](https://github.com/my4f175/TetherCache/tree/37c581ace23ff5df201f45e8282065d19b4ace8c)，本次 `git ls-remote HEAD` 于 2026-09-08 复核一致；commit time `2026-06-12T11:16:30+08:00`，subject `update readme`。
- 源码证据：[`grab.py` L76–112](https://github.com/my4f175/TetherCache/blob/37c581ace23ff5df201f45e8282065d19b4ace8c/tethercache/grab.py#L76-L112) 明确计算 attention mass、temporal diversity、组合分数并 top-k；[`patched_attention.py` L219–289](https://github.com/my4f175/TetherCache/blob/37c581ace23ff5df201f45e8282065d19b4ace8c/tethercache/patched_attention.py#L219-L289) 先运行 admission，再把缓存 K/V 送入真实 attention readout；[`install.py` L79–136](https://github.com/my4f175/TetherCache/blob/37c581ace23ff5df201f45e8282065d19b4ace8c/tethercache/install.py#L79-L136) 为每个 attention layer 建独立状态。
- 致命压力：如果 S43 被写成“根据分数接受/拒绝历史、再修复记忆”，与 TetherCache 高度重叠。并且 TetherCache 的选择是 layer-specific，不天然存在一个全局 item；S43 必须限定 stable source ID 并定义跨层 union/intersection 或排除该架构。

### 4.2 Echo-Memory

- 论文：[*Echo-Memory: A Controlled Study of Memory in Action World Models*](https://arxiv.org/abs/2606.09803v1)，arXiv:2606.09803v1；arXiv submission history 是 8 Jun 2026，而 HTML title page 显示 `August 24, 2026`。两处元数据冲突，本报告以版本号与 arXiv submission history 为准，不把 title-page 日期当发布时间。
- 官方代码快照：[commit `194be716aedaa84d9bd377740d6e6d9c32a309cb`](https://github.com/Echo-Team-Joy-Future-Academy-JD/Echo-Memory/tree/194be716aedaa84d9bd377740d6e6d9c32a309cb)，本次 `git ls-remote HEAD` 于 2026-09-08 复核一致；commit time `2026-08-16T09:49:34+08:00`，subject `Treat an already-published Comfy Registry version as success.`
- 源码/文档证据：[`doc/memory_mechanisms.md` L1–40](https://github.com/Echo-Team-Joy-Future-Academy-JD/Echo-Memory/blob/194be716aedaa84d9bd377740d6e6d9c32a309cb/doc/memory_mechanisms.md#L1-L40) 把 Context、Compression、Spatial、State-Space 的存储与 read-out 路径逐一映射；[`README.md` L31–53](https://github.com/Echo-Team-Joy-Future-Academy-JD/Echo-Memory/blob/194be716aedaa84d9bd377740d6e6d9c32a309cb/README.md#L31-L53) 说明 release 范围并记录 geometry-grounded path 是 10 Jul 后加入；[`README.md` L131–137](https://github.com/Echo-Team-Joy-Future-Academy-JD/Echo-Memory/blob/194be716aedaa84d9bd377740d6e6d9c32a309cb/README.md#L131-L137) 明确论文 `spatial_mem` 是 time-averaged token-grid，不是新加入的 3D geometry path。
- 论文证据：正文/附录把写入与读取拆开，比较 inject-none、text-KV concat、dedicated cross-attention；inject-none 可改善 replay，但 open-domain return 仍弱，直接说明“存了”与“真正可用”不能混同。
- 致命压力：如果 S43 只做 memory family/readout 消融或 replay/in-domain/open-domain 平均表，它只是 Echo-Memory 风格评测。剩余差异必须是运行时单 source、全部实际路径的相干因果效应与样本外 signed utility。
- 版本边界：不能把上述 commit 中 2026-07-10 后加入的 geometry path 说成 arXiv v1 论文表格已经验证的结果。

### 4.3 CUE-R

- 论文：[*CUE-R: Beyond the Final Answer in Retrieval-Augmented Generation*](https://arxiv.org/abs/2604.05467v1)，arXiv:2604.05467v1，submitted 7 Apr 2026；这是 RAG 预印本，不是视频世界模型论文，也没有已核正式顶会状态。
- 作者代码快照：[commit `84d7a6dbb1336e57aee8053c0ee9bb72155839ff`](https://github.com/jainsid24/cue-r/tree/84d7a6dbb1336e57aee8053c0ee9bb72155839ff)，README 自述为 official code；本次 `git ls-remote HEAD` 于 2026-09-08 复核一致；commit time `2026-04-07T18:17:54-07:00`，subject `paper and citations`。
- 源码证据：[`src/cue_r/core.py` L345–426](https://github.com/jainsid24/cue-r/blob/84d7a6dbb1336e57aee8053c0ee9bb72155839ff/src/cue_r/core.py#L345-L426) 优先选择模型报告已使用且匹配 gold support 的 chunk，然后实现 original/remove/replace/duplicate；[`src/analyze_cue_r_stats.py` L95–140](https://github.com/jainsid24/cue-r/blob/84d7a6dbb1336e57aee8053c0ee9bb72155839ff/src/analyze_cue_r_stats.py#L95-L140) 做 original-vs-intervention 的 paired delta 与 bootstrap CI；[`src/run_cue_r_support_synergy.py` L50–143](https://github.com/jainsid24/cue-r/blob/84d7a6dbb1336e57aee8053c0ee9bb72155839ff/src/run_cue_r_support_synergy.py#L50-L143) 比较删除 support 1、support 2 和两者，并计算非加性 synergy。
- 致命压力：`actually used item + remove/replace/duplicate + paired signed utility + interaction` 的抽象结构已有。S43 不能把“逐项反事实效用”单独写成新颖性；只能保留 stable visual source、真实多消费路径、pre-treatment 3D support、自然 revisit error/benefit 的联合限定。
- 重要区别：CUE-R 的 trace 是浅层可观察行为，目标是 QA correctness/grounding/confidence；它没有视频生成的几何支持、相机服从、像素效应图或世界状态演化。这是域和测量连接上的差异，不是反事实思想的新颖性。

## 5. 其他已核代码快照

以下 HEAD 均在 2026-09-08 用远端 `git ls-remote` 或已冻结官方仓库复核。列出 commit 只为使结论可重查，不表示代码已运行出论文结果。

| 工作 | 官方仓库快照 | 本次用于判断的源码事实 |
|---|---|---|
| WorldKV | [`046f6d19890555fd4601e8888d7258bee12fad01`](https://github.com/cvlab-kaist/WorldKV/tree/046f6d19890555fd4601e8888d7258bee12fad01) | [`image2video_fast.py` L502–586](https://github.com/cvlab-kaist/WorldKV/blob/046f6d19890555fd4601e8888d7258bee12fad01/wan/image2video_fast.py#L502-L586) 生成并跨层应用 selected chunk IDs；[`model_fast.py` L287–337](https://github.com/cvlab-kaist/WorldKV/blob/046f6d19890555fd4601e8888d7258bee12fad01/wan/modules/model_fast.py#L287-L337) 构造 sink/retrieval/recent 并实际 attention 消费 |
| CaR | [`8823c03544dfdd9a98966451e24b97fd5ad7ab76`](https://github.com/Orange-3DV-Team/CaR/tree/8823c03544dfdd9a98966451e24b97fd5ad7ab76) | [`custom_model.py` L730–798](https://github.com/Orange-3DV-Team/CaR/blob/8823c03544dfdd9a98966451e24b97fd5ad7ab76/wan/modules/custom_model.py#L730-L798) 显示同一输入走 native self-attention 与 camera self-attention；统一上游 source edit 自然会流入两支，因此“all-path”本身可能只是正确实现 |
| DensityKV | [`dcb1fba4a5606daf730ca9bfe32ac717596833ce`](https://github.com/ZhaoWQQ/DensityKV/tree/dcb1fba4a5606daf730ca9bfe32ac717596833ce) | 每层/每 head token bank 与 density admission；不是一个全局 selected frame |
| I3DM | [`895033d098a683ad49ed945a8524dea327895fe4`](https://github.com/Riga2/I3DM/tree/895033d098a683ad49ed945a8524dea327895fe4) | [`frame_memory_retrieval.py` L166–266](https://github.com/Riga2/I3DM/blob/895033d098a683ad49ed945a8524dea327895fe4/scripts/frame_memory_retrieval.py#L166-L266) 为候选生成 confidence maps 并做最大覆盖选择；[`eval_re10k.py` L385–417](https://github.com/Riga2/I3DM/blob/895033d098a683ad49ed945a8524dea327895fe4/scripts/eval_re10k.py#L385-L417) 取回稳定帧索引并送入 NVS/生成路径 |
| Vision-Language Binding | [`dca0b97d2788b099933d0b121001cefc6c099762`](https://github.com/ChrisG777/i2i-interp/tree/dca0b97d2788b099933d0b121001cefc6c099762) | T2I Lens、Attention Knockout、I2I patching 展示 reference 信息的不同因果路径 |
| Matrix-Game 3.5 | [`fbf7def0693ae14f745ba35bf2a26215d4ef991d`](https://github.com/Riemann-Dynamics/Matrix-Game-3.5/tree/fbf7def0693ae14f745ba35bf2a26215d4ef991d) | patch provenance、target-view 对齐、统一 pose-aware sequence；几何 source map 已是公开能力 |
| GIM-World project site | [`17c09f41597658526614b1c580a620341b78f152`](https://github.com/gim-world/gim-world.github.io/tree/17c09f41597658526614b1c580a620341b78f152) | 该仓库是项目网站，不是已核方法实现；不能把此 commit 当算法代码快照 |
| Ada-RefSR | [`2d3d882db0d75dd77bf4c41c98c731be9520a275`](https://github.com/vivoCameraResearch/AdaRefSR/tree/2d3d882db0d75dd77bf4c41c98c731be9520a275) | per-output-token soft gating 与误导 reference 抑制使 generic gate 不可作主创新 |

WorldTrace 的官方项目页在本次已核页面上没有暴露可固定的公开方法实现仓库；不据此推断不存在代码。GIM-World 的已核 GitHub 是 project-site repo，也不等同算法实现。

## 6. 最窄可辩护差异

建议论文/汇报只使用下面这个 scoped claim：

> **We study an architecture-scoped evidence contract for explicit-retrieval video world models that preserve a stable source identity across every conditioning branch. Conditioned on the naturally selected and addressable source set, we intervene coherently on one runtime-selected source, recompute all of its downstream descendants, localize the resulting output effect against a pre-treatment geometric support, and test whether the signed item-level effect predicts held-out natural revisit utility beyond retrieval and attention baselines.**

中文对应：

> 我们研究的是显式检索式视频世界模型中的架构限定证据合同：模型必须在每条条件路径中保留稳定来源身份。条件于普通运行已选择且可寻址的来源集合，我们对其中一条来源做跨全部消费路径的一致干预并重算其全部后代；将输出效应与干预前几何支持对齐；再检验单项有符号效应能否在检索/注意力基线之外预测留出自然重访效用。

不能使用的扩大表述：

- “适用于所有 video world models”：CaR/MemLearner 的连续隐式注意力、GIM-World 的压缩 tokens、DensityKV/TetherCache 的 per-head/per-layer bank 没有一个天然全局 item。
- “估计 Store→Select 全流程总效应”：selection IDs/order 在观察普通运行后被固定，因此主估计量是**条件于已选集合的 post-selection total downstream effect**。
- “首次逐项因果 utility”：CUE-R 已经占据跨域抽象。
- “首次几何局部记忆”：I3DM、MosaicMem、Matrix-Game 3.5 已直接占据。
- “首次 gate/accept/repair”：TetherCache 与 Ada-RefSR 已直接施压。

## 7. 因果估计量必须这样写

设普通运行先产生选择集合与顺序 `R0`，其中来源 `i` 实际被选且通过 addressability 检查。令 `X` 包含 prompt、camera trajectory、intrinsics、模型权重、sampler、实际 noise/RNG、原始非目标记忆与其他干预前外生状态。令 `z∈{0,1}` 表示对来源 `i` 的原始或低强度、几何保持的外观版本。

主比较应写为：

`Y_i(z) = G(X, R0, descendants_i(z), descendants_-i(0))`

`tau_i^post-select = L_or_map(Y_i(1), Y_i(0))`

其中 `descendants_i(z)` 必须重算：CLIP/semantic representation、replace/latent representation、attention K/V、融合状态和后续生成等目标来源的全部后代。只固定 `X` 和 `R0`，不能把目标来源的 downstream mediator 冻结。

若系统有两个消费者，四格为：

- `F00`：原来源进入两路；
- `F10`：只改消费者 1；
- `F01`：只改消费者 2；
- `F11`：从 source upstream 改一次并重建两路。

主效应只用 `F11−F00`。`F10/F01` 是 edge/path diagnostic；它们可能对应不自然的 cross-world state，不能叫总效应。交互 `F11−F10−F01+F00` 可诊断路径冲突或协同，但也不是 Store/Select 的总效应。

### 7.1 Influence、Localization 与 Benefit 是三个不同 estimand

低强度 appearance-only 的 `F11−F00` 只能直接回答前两个问题：

1. **Influence**：同一来源的外观轻微变化是否让输出发生超过 replay 的变化。可写成非负量 `I_i(delta)=D(Y(T_delta(x_i)),Y(x_i))`。
2. **Localization**：上面的变化是否富集在干预前支持 `S0` 内。可写成 `ER_i(delta)`。

它**不能单独给出 benefit 的符号**。输出变化很大可能使结果更好，也可能使结果更差；effect-map 的方向或亮度不提供效用顺序。只有相对独立目标 `Y*` 的 loss comparison 才能定义 benefit。

为避免 CUE-R 式 REMOVE/REPLACE 改变上下文长度、slot、位置、attention normalization 或主题分布，最便宜的首个 signed-benefit 对照应使用**同一来源、同一 slot/address、对称低强度 photometric perturbation**：

- 保持 source ID、token 数、顺序、mask、pose、intrinsics、depth/visibility、RoPE 地址、几何支持、对象 identity、场景 context 与所有非目标状态不变；
- 对同一原始来源施加预注册的 `T_{+delta}` 与 `T_{-delta}`，例如小幅、互为对称的曝光或色度变化；只选静态、照明稳定且变换后 identity/shape/support 检查通过的案例；
- 两个版本都从 raw source upstream 重算全部消费者；
- 使用真实 GT return 或实验前冻结的真实 revisit observation `Y*`，定义局部有符号效用：

`B_i^local(delta) = 0.5 * [L(Y(T_{+delta}(x_i)),Y*) + L(Y(T_{-delta}(x_i)),Y*)] - L(Y(x_i),Y*)`。

`B_i^local>0` 只表示原始、未改外观比同幅度的两侧 photometric alternatives 更有利；`B_i^local<0` 表示至少在这个局部邻域中，原始证据不是 loss-optimal。这个量仍然**不是“该 item 存在相对不存在”的绝对 benefit**，必须如此命名。

若需要进一步估计 item 相对可替代历史的增量收益，第二便宜的对照是在看结果前选一张**同场景、同对象 identity、相邻时刻、pose/FoV/support 匹配的未选帧**，保持 slot/address/token budget 不变并 source-coherent 替换。定义 `B_i^matched=L(Y(matched_alt_i),Y*)-L(Y(x_i),Y*)`。它比删除或跨场景 replacement 更少受上下文分布混淆，但只估计“相对这个预注册 matched alternative”的收益；若必须重投影，应只在双向可见共同支持上评分并单报 warping holes。

## 8. 全部致命重叠与失败点

1. **I3DM overlap**：3D-aware per-candidate confidence map、最大覆盖 selection、3D-aligned injection、reliable-region conditioning 已有；若 S43 只做 geometry score 或局部注入，方向被吞没。
2. **WorldTrace overlap**：addressability 已是独立问题；若 WorldTrace 式位置修复解释全部失败，S43 只剩 bug/diagnostic。
3. **WorldKV/CaR overlap**：相机/动作或视角注意力检索并消费历史已有；selection/retrieval 本身不可主张。
4. **DensityKV/TetherCache overlap**：token/frame admission、attention relevance、temporal diversity、cache readout 和 memory editing 已有；generic keep/drop/repair 被吞没。
5. **MosaicMem/Matrix-Game 3.5/GIM-World overlap**：几何 patch、source provenance、camera-queryable memory、局部编辑和 geometry supervision 已有；geometry-local memory 不是空白。
6. **Echo-Memory overlap**：Store-vs-readout、raw-context capacity 强基线、三分支 metric bundle 已有；普通 memory ablation 被吞没。
7. **CUE-R overlap**：actually-used evidence item、remove/replace/duplicate、paired utility、multi-item synergy 已有；单项反事实 utility 的抽象贡献被吞没。
8. **Vision-Language Binding/LocoGen/Activation Patching overlap**：reference-to-output 路径干预、直接效应与方法选择敏感性已有；“做 causal tracing”本身不新。
9. **all-path hygiene 风险**：在 CaR 或 Matrix-Game 3.5 的统一 token 路径中，上游 source edit 自动流经所有分支；如果没有发现跨路径矛盾，all-path 可能只是实现正确性。
10. **post-selection 限制**：固定 `R0` 后不能声称估计 Select 或 Store 的全流程因果效应。
11. **单 item 不足以预测**：一个案例只能证明该案例的敏感性；不能证明 item score 预测自然错误或收益。
12. **OOD perturbation 风险**：大幅颜色/纹理编辑可能只测出生成器对异常输入敏感；必须做低强度、support-preserving、强度 sweep 和 null/duplicate 对照。
13. **冗余与协同**：移除一个来源无效可能因另一个来源冗余，并不等于未消费；CUE-R 已显示多项非加性，至少要做 duplicate 与小规模 pairwise factorial。
14. **stale state**：来源在几何上仍可见却在时间上过期；静态 pilot 必须先排除，再把 stale/dynamic 单列。
15. **循环几何证据**：若 support mask 与效果由同一模型或同一预测误差产生，会形成循环验证；优先使用冻结 pose/depth/visibility 或独立几何 proxy。
16. **相机/质量混杂**：return RGB error 可由相机未服从、冻结、复制或整体崩坏造成；必须保留 camera-obedience 和 quality guardrail。
17. **像素伪重复**：单图像素、相邻帧和同一 seed 不是独立样本；不能用像素 bootstrap 冒充跨场景统计。
18. **有影响不等于有益**：大因果响应可能是伤害。Benefit 必须是相对 GT 或冻结 return reference 的有符号 loss difference。
19. **组合显然性**：即使所有六层实现正确，也可能只是把已有工具相接。必须发现强 baseline 无法解释的非显然规律。

## 9. 最低成本 kill experiment

### 9.1 Stage A：一条来源、零训练、只判断是否继续

优先使用当前 VMem 类显式来源系统，因为它保留 frame/source ID，并已有真实多消费路径审计基础。实验前按不看输出的规则冻结一个静态自然重访案例：目标来源必须在普通运行中真实被选、当前可寻址、pre-treatment 几何支持有效且面积不极端；动态/stale/重复来源排除出首个 pilot。

最小运行集合：

1. `A0` exact replay：完全相同的输入、cache、retrieval order、实际 noise/RNG 重复至少 3 次，得到数值/系统本底；若系统理论上应确定而输出不一致，先修复复现。
2. `F00`：原来源走全部路径。
3. `F10`：只改 CLIP/semantic path。
4. `F01`：只改 replace/latent path。
5. `F11`：在 source upstream 做一次相同低强度 appearance edit，重建全部真实消费表示。
6. 如成本可接受，加 `REMOVE/NULL` 与 `DUPLICATE`，分别排查必要性和冗余/位置效应。

效应图 `E(p)` 用相同 frozen output comparison 计算。干预前几何支持记为 `S0`，局部富集：

`ER = [sum_{p∈S0} E(p) / sum_p E(p)] / [|S0| / |Omega|]`

随机框不是充分基线。应用与 `S0` 面积、形状、edge density 和 baseline error 尽量匹配的平移/置换 masks，Stage A 只做同案例 permutation screening；跨场景结论留给 Stage B。

### 9.2 预注册 kill 条件

出现任一项就停止六级主线或降级：

1. 预注册自然失败不可稳定复现；
2. `F11−F00` 不超过 exact-replay 最大波动加预设 numerical tolerance；
3. 只有 `F10` 或 `F01` 有效，`F11` 无效或方向冲突；
4. `ER` 不超过 1，或不超过 matched-mask permutation 的 95th percentile；
5. edit strength 稍变就翻转排序/符号，或 null/duplicate 表明只是异常输入/位置效应；
6. support 无效、来自循环 estimator、来源 stale，或另一来源完全冗余而未被建模；
7. WorldTrace 式 address repair、camera-obedience 或整体质量检查已解释现象。

Stage A 通过最多只允许写：“该实际 selected source 在这个案例中存在超过 replay 的、几何富集的 post-selection downstream causal sensitivity。”不能写 predictor、acceptance method 或 novelty。

若同一次运行能获得冻结真实 return `Y*`，可顺带加入上节的 `T_{+delta}/T_{-delta}`，计算 `B_i^local`。它是低成本的局部 signed-benefit screening；`REMOVE/NULL` 只作必要性压力测试，因为它会改变 evidence/context distribution，不能替代 matched benefit 主对照。

## 10. Stage B：只有 Stage A 通过后才测试 Benefit/Accept

至少需要多个独立 source-target pairs、多个场景与冻结的 train/calibration/test split。两场景 pilot 仍只是 screening。先保留 Stage A 的 `I_i`、`ER_i` 和 `B_i^local` 为三个独立字段，不能把 influence magnitude 当成 signed benefit。对每条来源再定义相对预注册 matched alternative 的自然收益：

`B_i^matched = L(Y_with_matched_alternative_i, Y*) − L(Y_with_original_i, Y*)`

正值表示原来源优于这个同分布替代，负值表示原来源相对替代有害。另报 REMOVE/NULL 的 presence sensitivity，但不要把上下文长度/attention normalization 变化混入主 benefit。候选 causal-local score 必须在留出集上相对以下强基线提供增量：

- attention mass；
- pose/FoV overlap；
- recency；
- CLIP/retrieval similarity；
- source quality 与 support area；
- WorldKV camera/action score；
- I3DM uncertainty/coverage score；
- TetherCache attention+diversity；
- DensityKV density；
- raw context、nearest、best-single、null/reject-all。

报告指标应同时包含 held-out rank correlation 或 AUROC/AUPRC、risk–coverage/AURC、clean false rejection、overall paired loss，以及 camera/quality guardrails。[SelectiveNet, ICML 2019](https://proceedings.mlr.press/v97/geifman19a.html) 说明拒绝机制必须用 risk–coverage 衡量，不能只报“拒绝后准确率”。如果 causal score 不优于上述普通分数，`Benefit/Accept` 失败，剩余结果只是解释性 case study。

## 11. 从顶会方法学迁移的四个设计动作

1. **反转隐藏假设**：沿 `stored ≠ selected ≠ addressable ≠ consumed ≠ localized ≠ helpful` 逐级拆开。WorldTrace、Echo-Memory 和 [Sufficient Context, ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/33dffa2e3d2ab74a783d1a8c292f66d9-Abstract-Conference.html) 都证明相邻层不能互相替代。
2. **决定性干预与双重分离**：`F11` 是 source-coherent 主比较，`F10/F01` 只定位路径，配 exact replay、null、duplicate 和 matched-mask。参考 [LocoGen, ICML 2024](https://proceedings.mlr.press/v235/basu24b.html) 的 direct-effect 干预与 [Vision-Language Binding](https://arxiv.org/abs/2605.24624v1) 的 path knockout/patching，但把结论限制在当前架构。
3. **注意力只是强基线**：[I²AM, ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/c4a59e985de8b134328f41a47bc7dfac-Abstract-Conference.html) 已能从 reference 到 generated output 构造 attention attribution。S43 必须证明因果局部量在 attention/pose/retrieval 之后还有样本外价值。
4. **预注册 kill，不为漂亮图改指标**：[Activation Patching best practices, ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/06a52a54c8ee03cd86771136bc91eb1f-Abstract-Conference.html) 显示 corruption 与 evaluation metric 的选择可产生相互矛盾的定位结果。因此在看 treatment output 前冻结 source、edit family、strength、metric、mask、nulls、SESOI 和停止条件。

## 12. 最终 reviewer-style verdict

**Verdict: Weak Accept for one cheap falsification experiment; Reject as a novelty claim or method claim today.**

六级合同在“显式检索 + stable source ID + 多消费路径”的视频世界模型内仍有一个窄而清楚的可证伪差异。但 I3DM、TetherCache、Echo-Memory 和 CUE-R 已分别占据最关键的四块，且 I3DM 比原 S43 邻近表显示得更近。当前最合理的研究动作不是先训练 gate，而是跑 Stage A 让候选尽快失败或暴露一个非显然现象。只有 Stage A 的 `F11`、pre-treatment geometry enrichment 和 Stage B 的 held-out incremental benefit 三关依次通过，并跨第二 consumer/scene family 复现，才值得升级成论文方法。

本文件没有运行模型、生成视频或复现实验结果；它只完成一手论文、官方项目与官方代码的 source-level 对抗审查及实验冻结建议。
