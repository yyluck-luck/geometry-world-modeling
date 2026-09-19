# S42：检索后记忆消费者的因果可寻址性与充分性缺口搜索

审查时间：2026-09-07（UTC）。审查者：`/root/clip_mean_innovation_audit`。  
状态：**文献与源码审计完成；没有运行模型；没有生成视频；没有修改主研究账。**

## 结论先行

本轮没有找到一个可以直接声称为新方法的 attention、router、gate 或加权聚合器。WorldMem、EasyRef、MiMo、CorrAdapter、WorldStereo、PoCo、ReBind、Ada-RefSR、Memory Forcing、ReMind 和 Composition of Memory Experts 已分别覆盖 token 化历史、组图交互、历史建模、对应关系聚合、几何约束注意力、来源身份绑定、参考关系绑定、可靠性 gating、动态依赖不同记忆及多记忆专家组合。把这些模块移植到 VMem 接口，最多是强 baseline。

仍值得保留的中心问题是：

> 在 VMem 的几何检索集合、历史 latent、pose/K 和随机生成过程全部固定后，CLIP 记忆消费支路能否把某一个历史来源的证据作用定位到它真正支持的目标区域；若不能，这个不可寻址性是否解释真实回访失败？

这个问题目前只达到 **KEEP-CONDITIONAL：优先作为 benchmark/characterization seed**。源码可以严格证明 VMem 的 CLIP 支路丢失来源分配信息，并且单 key cross-attention 自身不能进行来源或空间寻址；源码不能证明该支路在真实生成中重要，因为逐帧 latent、mask 和 Plücker 仍走并行路径。必须先通过 `mean` 对 `zero-CLIP` 的真实影响门，再谈区域因果效应。

三个窄假设的最终排序为：

1. **H2 来源到区域的因果作用可定位性：KEEP-CONDITIONAL，最高优先级。** 若成立，首先是 benchmark/characterization 贡献。
2. **H1 CLIP 支路的信息瓶颈在真实 VMem 中是 active：KEEP-AS-GATE。** 它是 H2 的先决机制检查，本身更像负结果或系统刻画。
3. **H3 错误/矛盾记忆下的 subset/null 选择：METHOD-REJECT，BENCHMARK-CONDITIONAL。** 简单 gate、router、threshold、top-k、weighted mean 和 PoE 都不能作为创新。

## 1. 冻结问题、范围与证据等级

### 1.1 冻结研究问题

- **RQ1：容量。** 固定检索后，VMem 的 CLIP 消费支路在数学上保留了哪些来源身份和空间关联？
- **RQ2：实际作用。** 该支路在真实、可复现的 VMem 回访生成中是否对输出有超过 exact replay 噪声的作用？
- **RQ3：可寻址性。** 若有作用，移除或替换某一来源的 CLIP 证据，变化是否集中在该来源由生成前几何所支持的目标区域？
- **RQ4：错误记忆。** 固定检索集合后，矛盾或错误的记忆是否产生可重复的负迁移，以及 `subset/null` 是否有 oracle headroom？

### 1.2 严格证据边界

本报告把结论分成三层：

| 层级 | 本轮得到的证据 | 可以说什么 | 不能说什么 |
|---|---|---|---|
| 源码/数学事实 | 固定隔离 VMem 源码；均值与单 token attention 的推导 | CLIP 支路对来源分配不变；单 key attention 权重不能进行 query-dependent 寻址 | 不能说整个 VMem 对来源或区域盲，因为逐帧 latent 与相机条件仍存在 |
| 文献排重 | 正式会议页面、正式论文或可靠 arXiv 原文 | 普通 attention/router/gate/source tag/PoE 已有直接或强抽象近邻 | 定向检索未找到完全相同组合，不等于证明首次提出 |
| 待做真实实验 | 本轮没有运行 | 只能预注册干预、识别假设和 kill rule | 不能声称 CLIP 路径影响输出、均值有害、区域效应存在或方法提升 |

截至本轮读取的本地记录，S40 的真实两批生成入口只完成源码准备/独立前审，尚无可用真实生成结果；后续资源获取进度可能由主线程继续更新。本报告不把下载、源码编译或协议准备当作实验。

## 2. 源码事实与可证明的信息瓶颈

### 2.1 VMem 的实际检索—消费接口

固定隔离源码中：

1. `get_context_info` 先渲染 Surfel、统计 source frame 票权，再按相机距离与 NMS 得到 `selected_indices`；随后用同一组索引读取逐帧 `c2ws`、`latents`、`encoder_embeddings` 与 `Ks`。见 `pipeline.py:505-522, 630-765`。
2. `get_cond` 对 K 个图像 embedding 执行 `torch.mean(encoder_embeddings, dim=0)`，再用 `"d -> n 1 d"` 给每个 camera 复制**一个** context token。见 `pipeline.py:1124-1153`。
3. 历史 latent 没有被这个均值压缩；它按帧写入 `c_replace`。mask 与 Plücker 写入 `c_concat`。见 `pipeline.py:1154-1171`。
4. `CLIPConditioner` 使用 OpenCLIP ViT-H-14 的 `encode_image`，该接口在此处返回每张图一个全局向量；源码没有向生成器交付 patch token。见 `conditioner.py:7-39`。
5. 自定义 `Attention` 将 context 线性映射成 K/V 后调用 scaled dot-product attention。见 `transformer.py:39-75`。

### 2.2 定理 1：来源分配不可识别

设固定检索得到 K 个全局图像向量

\[
E=(e_1,\ldots,e_K),\qquad e_i\in\mathbb{R}^d,
\]

VMem 的 CLIP 条件为

\[
m(E)=\frac{1}{K}\sum_{i=1}^{K}e_i.
\]

对任意排列 \(\pi\)，

\[
m(e_{\pi(1)},\ldots,e_{\pi(K)})=m(E).
\]

若 \(\Pi\) 表示“哪个 embedding 绑定到哪个来源 slot”的分配，且无序多重集 \(\mathcal E=\{e_i\}\) 已知，则

\[
I\!\left(m(E);\Pi\mid\mathcal E\right)=0.
\]

此外，只要扰动满足 \(\sum_i\delta_i=0\)，就有

\[
m(e_1+\delta_1,\ldots,e_K+\delta_K)=m(E).
\]

对 K>1，线性求和映射的零空间维数为 \((K-1)d\)。因此，许多互不相同的来源集合状态在这个支路产生完全相同的条件。

这证明的是 **CLIP mean 支路的表示上限**。它没有证明全模型丢失来源顺序，因为 `c_replace` 中仍有逐帧 latent，`c_concat` 中仍有相机射线与 mask。

### 2.3 定理 2：单 key cross-attention 本身不能做来源/区域寻址

本源码给每个 camera 的 cross-attention context 长度为 1。对任一 head 和任一 query token \(q_r\)，只有一个 key/value：

\[
\operatorname{Attn}(q_r,k,v)
=\operatorname{softmax}\!\left(\frac{q_rk^\top}{\sqrt d}\right)v
=1\cdot v=v.
\]

因此，这个 attention 的权重不随目标区域 \(r\) 改变，也没有第二个来源 token 可供选择。后续残差、逐帧 latent、卷积/MLP 或其他 attention 仍可能让最终输出出现局部差异；所以正确表述是：

> **该 CLIP cross-attention 支路本身没有 query-dependent 的来源/区域地址空间。最终模型是否因此失败是经验问题。**

### 2.4 可检验因果图

把几何检索集合记为 \(R\)，逐帧 latent 为 \(L\)，pose/K、Plücker 和 mask 为 \(G\)，CLIP 来源向量为 \(E\)，实际噪声/采样过程为 \(U\)，输出为 \(Y\)：

\[
R\rightarrow(E,L,G),\quad E\rightarrow m(E)\rightarrow Y,\quad (L,G,U)\rightarrow Y.
\]

固定 \(R,L,G,U\)，只执行 \(do(E_s\leftarrow e_s')\)，得到的是 **CLIP 消费支路的受控路径效应**。它不是“整套记忆”的总效应，也不是“检索器”的效果。任何报告都必须保留这一区别。

## 3. 近邻工作的四轴排重

四轴统一为：**输入 / 状态 / 更新 / 读出**。最后一列给出对本项目的实际裁决。表中差异是基于原文的对照推断，不等于新颖性证明。

| 工作 | 输入 | 状态 | 更新 | 读出 | 对本候选的裁决 |
|---|---|---|---|---|---|
| VMem, ICCV 2025 | 历史/生成帧、相机、预测几何 | Surfel→source frame 索引；逐帧 latent/CLIP/pose/K | 新帧与新几何持续写入 | 几何选 ID；latent 逐帧消费，CLIP 求单均值 | 被审 baseline；本问题严格发生在检索之后 |
| WorldMem, NeurIPS 2025 | 历史 token、pose、time、当前状态 | 绑定 pose/time 的 token memory bank | 历史持续加入 | FOV/time/sim 筛选，relative pose/time 强化 Q/K 后 cross-attention | “来源状态绑定的多 token attention”已有，不能作为新方法 |
| EasyRef, ICML 2025 | 多参考图与指令 | MLLM 学到的组图交互表征 | 离线训练，不是在线地图 | adapter 把组图表征注入 diffusion | 已直接指出平均/拼接缺少图间交互；interactive aggregator 不新 |
| MiMo, ICLR 2026 | VideoAR 历史与未来 token | 学到的历史表征 | masked history/current/future 联合训练 | 历史表征条件化 VideoAR | “history understanding”本身已是明确问题 |
| CorrAdapter, CVPR 2026 | 多图及原生 correspondence | 对齐区域特征 | 离线训练 correspondence/adapter | aligned-area aggregation 注入 diffusion | 局部对应掩码与区域聚合已有直接近邻 |
| WorldStereo, CVPR 2026 | 相机轨迹、2D bank、增量 3D cache | global geometry + spatial-stereo memory | 生成过程中对齐更新 3D cache | 3D correspondence 限制 target-reference attention receptive field | 几何 token routing/local attention 为直接重复，否决 |
| Spatia / Geometry-as-Context, CVPR 2026 | 历史帧、点云/相机几何 | 可更新点云或显式几何 context | SLAM/MapAnything 更新，或在模型内调制 query/gate | projection-video ControlNet，或 Camera Gated Attention | 点云更新、SLAM memory、Plücker query/gate 均已被直接覆盖 |
| PoCo, CVPR 2026 | 多参考/多 shot token 与 reference ID | 带 side information 的 token | SideInfo-RoPE 注入关联状态 | 通过 Q-K 位置关系控制 source association | source ID / reference tag 路线被覆盖，否决 |
| ReBind, arXiv 2026 | 多参考图、编辑指令 | object/attribute 与 reference 的显式语义绑定 | ReBind-Instruct 与轻量编辑适配训练 | 嵌入 reference token 的结构化指令条件化视频编辑 | 进一步封死“显式 reference relationship”作为本项目独立新意 |
| AnchorWeave, arXiv 2026 | 每帧局部点云、目标相机 | 分开保存的 local spatial memories | 每帧构建/检索，覆盖式选 anchor | 多 anchor attention 与 pose-guided fusion | 多 anchor + pose fusion 已有；其 mean 消融不是 VMem CLIP mean 的直接证据 |
| MosaicMem, arXiv 2026 | 3D positioned patches、目标 query | hybrid 3D patch memory | 随历史加入/组合 patch | target-aware patch retrieval、Warped Latent/RoPE | “保持局部 patch 可寻址”已有方法近邻；其相机/视觉取舍支持做诊断，不证明本项目新 |
| LSM-World, arXiv 2026 | RGB、depth、camera | 世界坐标 3D latent tokens | lift/update，过滤动态对象/sky | z-buffer 投影成 target latent + visibility mask，经 side branch 条件化 | 显式空间 latent 投影已有；动态过滤也暴露状态范围边界 |
| WorldTrace, arXiv 2026 | 长 rollout 的 KV cache | 压缩 cache 与虚拟位置 | 历史压缩或 landmark 保存 | in-distribution virtual positions 维持地址可读 | “addressability”与不兼容位置相位平均的危害已有直接先例；本项目只能聚焦固定 VMem 来源→区域作用 |
| Memory Forcing, arXiv 2025 | temporal context + geometry-indexed spatial history | temporal/spatial memory 与增量 3D cache | Hybrid/Chained Forward Training 与增量重建 | point-to-frame retrieval 后 memory cross-attention | 已研究探索时过度依赖不足 spatial context；动态选择依赖不是新问题 |
| ReMind, arXiv 2026 | protected anchors、degraded intervals、noisy recent memory | reference KV cache + spatiotemporal address | node-drop/noisy-memory/reference-cache curriculum | PM-RoPE 单 attention 读取，训练模型忽略不可靠 recent context | “错误记忆、干净锚点、动态依赖”高度直接覆盖；普通 reject/gate 不新 |
| Composition of Memory Experts, ICLR 2026 | short-term、episodic、spatial memory | 三类 memory experts | long-term expert 用轻量 TTT 写入外部 diffusion weights | contrastive product-of-experts 组合预测 | expert fusion/PoE 已是强 baseline，不能当新意 |
| Ada-RefSR, ICLR 2026 | 低质图与可能不可靠 reference | summary tokens 与隐式相关性 | 学习 Adaptive Implicit Correlation Gating | 在 attention backbone 抑制误导参考 | confidence/reference gate 被直接覆盖，否决 |
| MultiRef, ACM MM 2025；MultiBanana, CVPR 2026 | 多张异质/不一致参考与生成指令 | 静态多参考集合 | benchmark 数据，不维护世界状态 | 测 source fidelity、组合、数量/域/尺度等失败 | 多参考冲突与来源保真 benchmark 已存在；本项目需证明时空世界记忆的额外问题 |
| HM-World / MemoBench, arXiv 2026 | 动态对象退出、遮挡、再进入；真实/合成 clips | 隐藏期间应演化的动态状态 | HyDRA 更新/检索或仅 benchmark | 重现动态对象及状态 | broad “out-of-sight memory” benchmark 已被覆盖；不能作为本项目大题目 |
| Sufficient Context, ICLR 2025；RECOMP, ICLR 2024 | query + retrieved context | sufficiency score 或压缩摘要，可为空 | 分类/压缩后选择增强 | answer 或 guided abstention / empty context | 检索充分性与 null action 已有抽象直接先例 |
| Why So Gullible?, NAACL Findings 2024；CARE, EMNLP 2025 | 错误/冲突 retrieved evidence | discriminator 或 conflict-aware compact memory | 对抗/判别训练 | 调节外部 context 的消费 | conflict classifier + gate 已有，不能单独构成视觉创新 |
| Selective QA over Conflicting Multi-Source Personal Memory, arXiv 2026 | 多源、有偏、缺失、冲突记忆 | 结构化 fusion/resolver | 受控 source distortions | answer 或 abstain，报告 selective accuracy/coverage | “冲突多源记忆 + abstain + risk/coverage”问题定义已有；视觉时空接口只是剩余差别 |
| D-TRAK, ICLR 2024；DAS, ICLR 2025 | diffusion 训练样本与输出 | 训练数据 influence/attribution score | leave-one-out/预测分布比较等 | 归因训练数据贡献 | 泛称“diffusion causal attribution”不新；它们不处理部署时固定记忆来源到目标区域 |

### 3.1 普通机制黑名单

下列机制继续作为 baseline 或被否决方向，不得在后续报告中换名复活：

- 多个来源 token + cross-attention、sparse router、top-k router；
- 几何/epipolar/correspondence mask 限制 attention；
- source ID、frame ID、pose/time、SideInfo-RoPE；
- scalar confidence、per-token gate、uncertainty threshold、learned assessor；
- nearest/best-single/medoid/weighted mean；
- mixture/product of memory experts；
- 更新点云、3D latent、patch memory、SLAM cache；
- conflict classifier 后选择 subset/null。

这些机制仍必须进入强基线，但不能作为中心创新主张。

## 4. H1：CLIP 支路的信息瓶颈在真实 VMem 中是否 active

**状态：KEEP-AS-GATE；若不通过，H2 与 H3 的 CLIP 消费路线一起停止。**

### (a) 可观测失败

源码容量上限只有在下列现象出现时才是实际问题：

1. exact replay 稳定后，`mean` 与 `zero-CLIP` 的输出差异显著高于 replay 数值门；
2. 在几何支持高、cache/pose/K/latent readback 全部正确的自然回访中，仍有内容保持失败；
3. 单一来源的受控替换产生可重复作用，而不是仅出现随机全局漂移；
4. 逐帧 latent 并未已经解释/承载全部可用历史外观。

### (b) 最强已有等价机制

WorldMem 的 pose/time-bound token bank、EasyRef 的 group-image interaction、MiMo 的 history understanding、WorldStereo 的 correspondence-constrained readout、PoCo/ReBind 的来源绑定，以及 WorldTrace 的 KV addressability 都是更强消费机制。它们使“保留多 token 或加来源标签”本身不能成为创新。本假设只问现有 VMem 的 CLIP 支路是否在真实运行中成为 active bottleneck。

### (c) 反事实干预与识别假设

最小干预：

\[
Y^{\text{mean}}=Y(R,L,G,U,m(E)),\qquad
Y^{0}=Y(R,L,G,U,0_d).
\]

受控路径效应为

\[
\Delta_{\text{CLIP}}=d(Y^{\text{mean}},Y^{0}).
\]

必须满足：

- 同一模型/VAE、frame IDs 和顺序、latents、pose/K、mask/Plücker、trajectory、CFG、sampler、steps；
- 保存并复用实际 noise tensor，而不只复用 seed；
- 第二次运行不得重新检索、重新编码或更新 cache；
- 先做 exact replay 定义数值噪声门；
- 输出评价区域和失败 case 在看干预结果前冻结；
- `zero-CLIP` 是支路移除，不代表“无历史”，因为 latent 历史仍在；
- 稳定性/SUTVA：同一冻结输入不会受到其他并发状态或隐藏 cache 污染；
- exclusion：干预只改变 CLIP condition，不通过日志路径、dtype、batch 顺序或 RNG 改变生成；
- 结论限于该声明组件变体，不外推 exact-original VMem。

### (d) 最便宜真实实验

S40 一旦有通过 readback 的真实 baseline，只跑两个科学条件：A0 原 `mean` 与 A1 `zero-CLIP`；每个条件先做 exact replay 守卫。优先使用一个预注册的自然回访失败和至少两个配对 noise tensors。保存 `c/uc`、`replace`、`concat`、noise、`samples_z`、解码输出的数组 SHA。只有 A0/A1 超过 replay 门，才允许进入 H2。

### (e) Kill result

- A0 与 A1 的差异不超过 exact replay 门；
- 差异只来自重新检索、cache 更新、dtype/batch 或 RNG 不一致；
- 回访失败在 CLIP 干预前已由错误 pose/K、不可见支持或 cache 接线解释；
- `zero-CLIP` 改变输出但没有可重复方向，且不同 paired noises 不一致；
- 只有手选 case 有效，预注册确认 case 无效。

### (f) 若成立是什么贡献

首先是 **characterization/negative-result**：证明一个源码可见的容量限制在真实 VMem 中确实 active。单独不构成方法论文；若 H2 也成立，才可成为新 benchmark 的机制基础。

## 5. H2：来源到目标区域的因果作用可定位性

**状态：KEEP-CONDITIONAL；本轮最值得保留的问题。**

窄假设：在检索集合固定且某来源确实覆盖目标区域时，一个能正确消费记忆的系统，移除该来源的独有语义证据所造成的输出作用应更多集中在该来源支持的目标区域；这一效应集中度应在控制几何支持量后仍预测回访误差。

### (a) 可观测失败

- 某来源有高几何支持，但其受控移除对任何区域都几乎无作用：记忆“存了、选了、没被用”；
- 有总作用，但作用在来源不支持的区域大面积扩散：消费者缺乏可寻址性或干预分布外；
- 作用集中度与回访保持无关，几何支持已解释全部差异：该诊断没有增量价值；
- 来源的事实证据被移除后，受支持区域反而改善：该来源为有害消费或几何支持并不等于语义适用。

### (b) 最强已有等价机制

WorldStereo、CorrAdapter、SPAD、EpiDiff 已直接把几何/对应关系写进局部 attention；WorldMem 与 PoCo 维护来源身份；ReBind 明确绑定属性与参考；MultiRef/MultiBanana 测来源保真；D-TRAK/DAS/ProMark/CAD 已研究 diffusion 归因。故 **局部 attention、source tag、correspondence mask 或“做 attribution”都不新**。

定向检索暂未找到同时满足以下条件的工作：固定在线世界模型的 retrieval IDs 与全部生成随机性，只干预一个部署时记忆来源，并用生成前几何支持图验证 source→target-region 的作用集中度。这个“未找到”只支持继续验证，不能写成首次提出。

### (c) 反事实干预与 identification assumptions

令 \(A_{sr}\in[0,1]\) 表示来源 \(s\) 对目标区域 \(r\) 的生成前几何支持比例。它必须由干预前的 Surfel/source index、可见性和遮挡规则确定并冻结。令 \(Y\) 为 factual 输出，\(Y^{(-s)}\) 为只移除来源 \(s\) 独有 CLIP 贡献后的输出。首选保持 K 和 shape 不变的干预是：

\[
do(e_s\leftarrow \bar e_{-s}),\qquad
\bar e_{-s}=\frac{1}{K-1}\sum_{j\ne s}e_j,
\]

并记录聚合向量范数/余弦；若该替换分布外，则用预注册、相机距离和范数匹配的真实 in-scene donor 做敏感性分析。不得用 GT 选 donor。

把目标划分为等面积 latent cells，或在不等面积区域下显式使用面积 \(|r|\)。定义区域敏感性：

\[
D_{sr}=d\!\left(\phi_r(Y),\phi_r(Y^{(-s)})\right),\qquad
T_s=\sum_r |r|D_{sr}.
\]

只有 \(T_s\) 超过 exact replay 门，才计算效应集中度：

\[
LC_s=\frac{\sum_r |r|A_{sr}D_{sr}}{\sum_r |r|D_{sr}+\epsilon}.
\]

为去除“支持面积大自然容易覆盖变化”的平凡效应，定义面积基线

\[
\pi_s=\frac{\sum_r A_{sr}|r|}{\sum_r |r|},
\]

以及当 \(\pi_s<1\) 时的归一化局部提升

\[
NLC_s=\frac{LC_s-\pi_s}{1-\pi_s}.
\]

`D`、`LC`、`NLC` 只表示**敏感性/作用定位**，没有 GT 时不能称为有益。若冻结 target GT \(Y^*\) 可用，区域收益另定义为

\[
B_{sr}=\ell_r(Y^{(-s)},Y^*)-\ell_r(Y,Y^*),
\]

正值才表示 factual 来源在该区域有益。

识别假设：

1. **Consistency/SUTVA**：相同 frozen state 与 noise 对应同一潜在输出；不同 run 不共享可变隐藏状态。
2. **Exclusion**：只改 \(e_s\)，不改选择集合、latents、poses、K、mask、Plücker、cache、sampler 或 RNG。
3. **Pre-treatment support**：\(A_{sr}\) 完全由输出前信息确定，不使用生成输出或 GT 修 mask。
4. **Support validity**：Surfel 投影及 source index 足以作为“来源可见支持”的代理；遮挡/深度误差必须分层或报告测量误差。
5. **Positivity**：每个待比较来源在冻结数据中既有有效支持，也能构造不依赖 GT 的合法替代；无支持来源不进入主要估计。
6. **Intervention fidelity**：替代向量的 norm、dtype、shape 和相似度处于观察分布；至少一个真实 donor 敏感性分析方向一致。
7. **No post-selection**：场景、来源、区域、距离函数和确认集在看结果前冻结。
8. **Path-specific interpretation**：估计限于 CLIP 消费支路，不解释 latent 支路的总记忆效果。

### (d) 最便宜真实实验

先通过 H1。随后在两个真实场景的预注册自然回访上，每个 target 选一个高支持来源和一个面积匹配低支持来源；固定所有生成状态，只做 factual 与单来源替代的 paired runs。最多六个条件：

| 臂 | 条件 | 用途 |
|---|---|---|
| A0 | exact original mean | factual 基线 |
| A0R | A0 exact replay | 数值/接线噪声门 |
| A1 | zero-CLIP | CLIP 总影响门 |
| A2 | 高支持来源 \(s_h\) 替换为 \(\bar e_{-s_h}\) | 主要 source→region 效应 |
| A3 | 面积匹配低支持来源 \(s_l\) 同样替换 | locality negative control |
| A4 | 高支持来源换成预注册 norm/camera-matched 真实 donor | 干预分布敏感性 |

这些臂不增加模型参数，均向下游交付同一个同维 token；聚合向量事先生成、保存并哈希。A2/A3/A4 不是“新聚合方法”，只是干预。报告 `T_s`、`LC_s`、`NLC_s`、区域损失差、相机服从、防复制指标、逐场景逐 noise 原始行和 bootstrap CI；样本太少时只报 pilot，不做总体推断。

### (e) Kill result

- H1 影响门失败；
- 所有 \(T_s\) 不超过 replay 门；
- 高支持来源的 `NLC` 不高于面积/低支持控制，或方向随 donor/noise 翻转；
- 作用集中完全由支持面积解释，对回访损失没有增量预测；
- 只有 hand-picked 开发场景有效，冻结确认场景无效；
- 结果对遮挡/深度误差极敏感，无法区别支持图错误与消费者错误；
- 改善仅表现为复制历史视图、损害目标相机服从或整体生成质量。

### (f) 若成立是什么贡献

最稳妥定位是 **benchmark/characterization**：把“存到、检索到、消费到、作用到正确区域”拆成可审计的因果链，并给出 controlled path-specific 指标。只有该诊断跨场景、跨至少第二种 memory consumer 成立，且后续非普通机制在等参数/等计算下击败 WorldStereo/WorldMem/PoCo/Ada-RefSR 风格强基线，才可能升级为 companion method。

## 6. H3：错误/矛盾记忆下是否需要选择性 subset/null 消费

**状态：METHOD-REJECT；BENCHMARK-CONDITIONAL，低于 H2。**

这里的“abstain”仅指**不消费 CLIP 外部记忆**，模型仍生成视频；必须写成 `memory-null action`，不能与拒绝回答或停止生成混为一谈。

### (a) 可观测失败

固定同一组检索 IDs 后，用真实、norm-matched、预注册的冲突 embedding 替换 0、1、约一半、全部来源。若原 mean 的回访/生成损失随冲突剂量单调恶化，并且 `null` 或某个单来源 oracle 明显优于 mean，则存在有害记忆消费和选择性 headroom。

必须区分：

- **target–reference conflict**：来源内容与当前目标状态不相容；
- **reference–reference conflict**：被选来源彼此矛盾；
- **insufficiency**：来源没有足够信息，但不一定错误；
- **geometry mismatch**：来源本就不支持目标，不属于固定正确检索后的消费者冲突。

### (b) 最强已有等价机制

ReMind 已直接用 node-drop/noisy-memory 和 protected clean anchors 训练视频生成器忽略不可靠近期 context；Memory Forcing 已研究探索/回访时对 temporal 与 spatial memory 的动态依赖；Ada-RefSR 用 learned summary tokens 和 AICG 抑制误导参考；Composition of Memory Experts 用 PoE 组合多类世界记忆；PoCo/ReBind 处理参考混淆/绑定；MultiRef/MultiBanana 测异质多参考；Sufficient Context、RECOMP、Why So Gullible、CARE 与 Selective QA 已覆盖 sufficiency、conflict assessor、empty context 与 abstention/risk–coverage。因而普通 subset/null 决策机制没有足够新颖性。

### (c) 反事实干预与 identification assumptions

令冲突剂量 \(q\in\{0,1,\lceil K/2\rceil,K\}\)，随机但预注册地选择 q 个来源，用真实 donor embedding 替换，保持每个向量 norm、dtype 与 K 不变；检索 IDs、latents、poses、K、mask/Plücker、noise、sampler 不变。定义：

\[
H_{\text{oracle}}=ell(Y^{\text{mean}},Y^*)-
\min\left\{\ell(Y^{\varnothing},Y^*),\min_s\ell(Y^{\{s\}},Y^*)\right\}.
\]

oracle 只用于判断 headroom，绝不能作为可部署方法。若后续训练无 GT score \(g(x)\)，阈值 \(\tau\) 下：

\[
\text{coverage}(\tau)=P(g(x)\ge\tau),\quad
\text{risk}(\tau)=\mathbb E[\ell(Y,Y^*)\mid g(x)\ge\tau].
\]

此外必须报告所有 target 的总体 paired loss 与 clean false-reject；只报 accepted subset 的 risk 会掩盖大量拒绝。

识别要求：冲突来源在看结果前随机化；donor 不能用 GT 或输出指标挑选；冲突剂量不得改变其余条件或 generator compute；source–source 与 target–source conflict 单独构造；分数/threshold 在确认集前冻结；oracle 与 deployable rule 严格分开。

### (d) 最便宜真实实验

只做“问题是否存在”的五基线压力测试，不训练新模块：

1. original mean；
2. null/zero-CLIP；
3. geometry-nearest 或预注册 best-single heuristic；
4. 等预算 generic attention/router 或 Ada-RefSR 风格 gate（后续若已有实现）；
5. PoE/expert fusion 强基线（只有公平实现可用时）。

先做 0/1/half/all 的 dose-response 与 `H_oracle`。没有 headroom 就停止；有 headroom也只证明 failure setting，不证明候选方法。

### (e) Kill result

- mean 不随冲突剂量稳定恶化；
- `null/best-single` oracle 相对 mean 没有正 headroom；
- 现象只由向量范数、域外 donor 或 pose/latent/cache 变化解释；
- 任何 deployable score 的 AURC 不优于普通 confidence，或收益来自高 clean false-reject；
- generic gate/router/PoE 在等参数/等计算下达到同样结果；
- ReMind/Ada-RefSR/PoCo 风格 baseline 已完整覆盖机制和结果。

### (f) 若成立是什么贡献

当前最多是 **failure benchmark/characterization**。若想升级为方法贡献，至少必须同时具备：

- 分离 reference–reference 与 target–reference conflict；
- 动作为 set-valued \(\{\text{subset},\varnothing\}\)；
- 推理决策不看 GT；
- 报告 risk–coverage/AURC、clean false-reject 与总体 paired loss；
- 击败 null、nearest/best-single、generic router/gate 和 PoE；
- 在真实自然错误而不只人为 corruption 上复现。

即便满足这些条件，仍需重新做精确新颖性检索；本轮不预先承诺方法创新。

## 7. 三个假设的共同退出树

```text
真实 S40 baseline + 全链 readback 是否成立？
├─ 否：不运行消费者实验；继续资源/基线恢复
└─ 是：是否存在预注册的自然回访失败？
   ├─ 否：停止 VMem failure claim
   └─ 是：mean vs zero-CLIP 是否超过 exact replay 门？
      ├─ 否：杀死 H1；H2/H3 的 CLIP 路线停止
      └─ 是：单来源干预是否有稳定总作用？
         ├─ 否：杀死 H2
         └─ 是：作用是否在来源支持区域集中并预测误差？
            ├─ 否：仅保留 bottleneck characterization
            └─ 是：保留 H2 benchmark；再测真实/受控 conflict headroom
               ├─ 无 dose-response 或无 oracle headroom：杀死 H3
               └─ 有：只保留 H3 failure benchmark；普通 gate/router 仍非创新
```

## 8. Idea-evaluator 裁决

### 8.1 Fatal flaws

| 风险 | 严重度 | 裁决 |
|---|---|---|
| F1 无法区别最近工作 | 对方法版是 **CRITICAL** | attention/router/gate/PoE/source tag/geometry mask 全部 Reject and Pivot；H2 只保留为固定检索、固定 RNG 的因果诊断 |
| F2 把结构定理写成效果结论 | **CRITICAL** | 定理只限 CLIP 支路；必须先过真实 A0/A1 影响门 |
| F3 干预分布外 | MAJOR | mean-replacement 与真实 norm/camera-matched donor 双重敏感性分析；结果需方向一致 |
| F4 支持图测错造成伪 locality | MAJOR | 生成前冻结、遮挡分层、面积校正、低支持 negative control |
| F5 GT 泄漏 | **CRITICAL** | GT 只能算损失/oracle，不得选来源、donor、subset、threshold 或区域 |
| F6 当前不可执行 | MAJOR | 等真实 S40 baseline 及完整权重/SHA/readback；本轮不运行模型 |

### 8.2 五维判断

这里只评 H2 的 benchmark/characterization 版本，不评已否决的模块方法：

| 维度 | 分数 / 10 | 依据 |
|---|---:|---|
| Higher | 6 | 若能定位“检索正确但消费错位”，可指导后续模型；当前无效果数据 |
| Faster | 5 | 反事实需要额外生成，不具速度优势；有界 pilot 只是研究成本低 |
| Stronger | 7 | 对错误归因、遮挡和历史冲突有鲁棒性诊断价值；仍待真实验证 |
| Cheaper | 6 | 诊断不训练模型，可先少量 paired runs；不代表部署更便宜 |
| Broader | 6 | 抽象接口可迁移到其他 memory consumer；当前只精确核 VMem |

无 8 分维度，不满足强接收。生命周期定位为 frontier diagnostic seed；以本机无远程 GPU 的资源，零训练有界审计是 Yellow，可训练新 consumer 是 Red。

### 8.3 最终裁决

- **最值得保留的新问题：** 固定 retrieval 与随机生成过程后，测量 source→target-region 的受控路径效应，并区分“已存、已选、已消费、作用在正确区域”。
- **只作前置门：** VMem CLIP mean/单 token 支路的信息瓶颈是否 active。
- **否决为创新：** 任何普通 attention/router/gate/threshold/top-k/source tag/geometry mask/PoE/weighted mean。
- **低优先级保留：** 错误/矛盾记忆下的 memory-null selective-risk benchmark；已有直接近邻很多，只在 H1/H2 成立并出现真实 headroom 后继续。

## 9. 下一步只有一个决定性动作

主线程获得通过 SHA 与 readback 的真实 S40 baseline 后，先执行 H1 的 A0/A0R/A1 最小影响门。这个门需要的计算最少，同时会直接决定是否值得为 H2/H3 花更多真实生成成本。在该门通过前，不实现新 attention、router 或 conflict gate。

## 10. 检索范围与限制

本轮结合项目 `docs/LITERATURE_SYNTHESIS_V2.md`、S38 已核学习材料、S41 排重、固定 VMem 源码，以及 2024–2026 的 CVPR/ICCV/ICLR/NeurIPS/ICML/ACL 正式页面或可靠 arXiv 原文。检索同时使用正向机制词（addressable memory、multi-reference binding、spatial memory、selective augmentation）和反向失败词（conflicting/noisy/insufficient memory、abstention、causal attribution、region effect）。

这是问题导向的定向检索，不是全数据库系统综述。未找到完全相同组合，不代表不存在；在任何投稿级 novelty claim 前，需要再做引用网络、同义词扩展和独立作者复核。
