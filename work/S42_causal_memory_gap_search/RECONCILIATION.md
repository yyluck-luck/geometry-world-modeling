# S42 v2 协调审查：统一消费者诊断的阶段、编号与解释

审查时间：2026-09-07（UTC）。审查者：`/root/clip_mean_innovation_audit`。  
裁决：**PASS**。  
范围：追加式协调文件；没有覆盖或修改 S42 v1，没有修改根协议、增量审查或主研究账，没有运行模型。

## 1. 绑定对象与权限顺序

本审查逐字节绑定以下文件：

| 身份 | 路径 | SHA-256 | 角色 |
|---|---|---|---|
| 当前根协议 | `work/S41_gemini_adversarial_review/primary_retrieval_and_root_review.md` | `fd07dfc743f9a0c3f350f5d719936b74d5d902f3f10910c1a0b30b8ecda4059a` | **唯一执行协议与 A/F/S 标签权威** |
| 增量审查 v2 | `work/S41_gemini_adversarial_review/root_review_incremental_v2.json` | `6c8ee3c30dffaf1454a4e178e45f0fe5805bb8d23ad8e8c81bfdfb7913068ce8` | 对旧根稿的审查清单，不是执行协议 |
| S42 v1 报告 | `work/S42_causal_memory_gap_search/REPORT.md` | `8693ace94524cafb5b5e44cf72f4011e757266a70a8025bb6839b777efdaf6ea` | 创新排重、数学事实和候选指标的历史审计 |
| S42 v1 来源 | `work/S42_causal_memory_gap_search/sources.json` | `82d3e85e0b13af1909080d109e82eff7d56c411e2de1af2df8f6b689e7c4dff9` | v1 文献与本地证据清单 |
| S42 v1 回执 | `work/S42_causal_memory_gap_search/receipt.json` | `780c6ac0c83094a80e1f56e0f32e23d8324c79adc8d7a65e4d840a66d1cfce9a` | v1 完成与非执行边界 |

增量审查 v2 记录的被审根稿 SHA 是 `141512...`，并给出 `REVISION_REQUIRED`；当前根协议 SHA 已变为 `fd07df...`。本次将 v2 的六项 pass condition 当成回归清单，重新核当前根协议。当前根协议已经逐项包含：

1. Gate 1 区分“任何 CLIP 影响”和“与冻结回访失败相关的方向性变化”；
2. 分开处理 A1 改善、A1 恶化及 A2–A5 无改善的逻辑；
3. F10/F01 明确为 cross-path-inconsistent branch interventions，F11 为 coherent counterfactual；
4. 首个图像反事实限制为 geometry/support-preserving appearance edit，并保存图像、mask、过程和几何稳定证据；
5. signed factorial interaction 在固定有符号标量或特征空间中先作 contrast、后取范数；
6. 协议标题与进入 source-to-region 诊断的条件已经操作化。

因此，v2 的旧 `REVISION_REQUIRED` 不应直接贴到当前 `fd07df...` 根协议上。对当前版本的协调裁决是 `PASS`。

### 冲突时的唯一优先级

1. 实际实验标签、阶段、进入条件和解释：以当前根协议 `fd07df...` 为准。
2. 本文件只提供 S42 v1 到根协议的交叉映射与去歧义。
3. S42 v1 保留为不可变历史审计；其中与根协议冲突的臂编号不再具有执行含义。
4. 增量审查 v2 保留为旧版本审查历史；它的修改项已经在当前根协议中闭合。

## 2. 唯一 canonical 阶段与标签

### G0：真实基线与自然失败门

- 完成真实组件冻结、加载、S40 两批生成与 `samples_z`→第二批 cache 的 readback。
- 在看任何替代结果前冻结自然回访失败、目标区域、场景、轨迹、noise/seed 与评价。
- 没有稳定自然失败时停止该方向。
- G0 没有 `A`、`F` 或 `C` 科学臂。

### G1：CLIP 路径影响与失败相关性

| canonical 标签 | 唯一含义 | 解释边界 |
|---|---|---|
| `A0` | 原始 uniform CLIP mean 的 exact replay | 与已保存 baseline 比较；重复运行写作 `A0@rep=n`，不再创建 `A0R` 新臂 |
| `A1` | zero-CLIP，其他路径和实际 noise 完全固定 | 只移除 crossattn 信息；不是同信息性能 baseline |

G1 先判断 `Influence`，再判断 `Failure relevance`：

- A1−A0 只超过 replay 容差：只能说 CLIP 路径影响输出。
- 变化仅为全局色调/风格、未改变冻结回访结果：停止局部身份/mean 分支。
- 只有冻结回访区域的预注册结果也超过容差，且报告方向、相机服从与整体质量，才进入 G2。
- A1 改善只说明当前全局 CLIP 条件的存在或内容可能有害，不单独归因给算术 mean。

### G2a：目标方向的普通单来源基线

| canonical 标签 | 唯一含义 |
|---|---|
| `A2` | 固定 K 个候选中的最近视角单向量，匹配 A0 mean 的 L2 范数 |
| `A3` | 固定 K 个候选中的最远视角单向量，匹配 A0 mean 的 L2 范数 |

A2≈A3 只否定目标方向解释，不能跳过 G2b。

### G2b：集合代表与几何加权普通基线

| canonical 标签 | 唯一含义 |
|---|---|
| `A4` | 固定 K 个候选中的 CLIP medoid，匹配 A0 mean 的 L2 范数 |
| `A5` | 固定 K 个候选的 Surfel 票权 mean，匹配 A0 mean 的 L2 范数 |

G1 通过后，A2–A5 构成完整普通聚合审计。任何一臂稳定解决问题时，它成为更强 baseline，不产生创新结论。

### D：source-to-region 消费者 factorial 诊断

进入 D 必须满足当前根协议的四项条件：真实自然失败已核验；A0 exact replay 成立；G1 对冻结回访结果有相关作用；至少一个预注册来源相关 contrast 不能由整体质量或相机代价解释。A2–A5 不要求形成性能改善，但必须先完成普通聚合审计；D 是消费者诊断分支，不是方法 headroom 分支。

首个干净反事实只使用真实观测来源 `i`：

- 在保存的 source mask 内作低强度、预注册的 appearance-only 或 photometric edit；
- 相机、场景几何、可见支持、检索 IDs 保持不变；
- 保存 `I_i`、`I_i_cf`、edit mask、编辑过程/参数及生成前几何稳定检查的 SHA；
- 会改变几何/支持的 edit 只能进入压力测试，不能沿用原支持区 `M_i`；
- 不把生成来源的 `samples_z` 解码再编码冒充配对真实 latent。

| canonical 标签 | CLIP 来源版本 | `replace` latent 来源版本 | 唯一解释 |
|---|---|---|---|
| `F00` | 原图 | 原图 | 与 A0 相同的 coherent factual condition |
| `F10` | 反事实图 | 原图 | CLIP-only branch response；**cross-path conflict**，不是性能 baseline |
| `F01` | 原图 | 反事实图 | replace-only branch response；**cross-path conflict**，不是性能 baseline |
| `F11` | 反事实图 | 反事实图 | 唯一 coherent image counterfactual |

F10/F01 的大伪影可能来自两条 appearance path 收到互相矛盾的版本。只有在两个或以上预注册低强度反事实中方向/定位重复，并与 F11 一致，才允许解释分支响应。

对事前固定方向的标量结果 `Y`，唯一交互定义为：

\[
I_Y=(Y_{11}-Y_{01})-(Y_{10}-Y_{00})
=Y_{11}-Y_{10}-Y_{01}+Y_{00}.
\]

空间交互必须先在同一固定有符号输出/特征表示上计算逐位置 factorial contrast，再取范数。禁止对非负距离图直接相减后声称协同、互补或冗余。CLIP 与 latent 编码器、维度和扰动能量不同，禁止用未经归一的标量效应大小给两条路径排名。

### S：可选 correspondence stress

`S_Rperm`、`S_Pperm`、`S_RPperm` 保留根协议含义：它们是分布外绑定压力测试，不进入 A0–A5，不进入 F factorial，也不能用来排列 crossattn、replace、Plücker 谁“主导”。

### C：H3 错误/矛盾记忆压力测试

H3 仍是 `METHOD-REJECT / BENCHMARK-CONDITIONAL`，不进入当前必跑链。若 D 之后有充分真实证据需要继续，使用独立坐标标签，不复用 A/F：

\[
C(\text{type},q,\text{policy}).
\]

- `type ∈ {RR, TR, IS}`：`RR` 为 reference–reference conflict，`TR` 为 target–reference conflict，`IS` 为 insufficiency。
- geometry mismatch 记为 `GM-EXCLUDED`；它不属于固定正确 retrieval 后的 H3 消费冲突。
- `q ∈ {0,1,half,all}`：冲突/不足来源剂量。
- `policy ∈ {mean,null,nearest,generic,poe}`：原 mean、memory-null、预注册 nearest/best-single、普通 gate/router、PoE 强基线。

示例：`C(RR,half,mean)` 表示一半参考彼此冲突、仍由 original mean 消费；`C(TR,1,null)` 表示一个 target–reference conflict 且 CLIP memory-null。

这套 `C(type,q,policy)` 命名同时修复 v1 H3 的重复/别名问题：v1 的 `reference–reference` 与后文 `source–source` 指同一类，统一只写 `RR`；`target–reference` 与后文 `target–source` 指同一类，统一只写 `TR`。定义只在本节出现一次，后续只引用代号，不再重复 bullet。

H3 唯一、无重复的 kill list 为：

1. `C(*,q,mean)` 的损失不随 q 呈稳定剂量响应；
2. `null` 或预注册单来源 oracle 相对 mean 没有正 headroom；
3. 现象可由 norm、域外 donor 或未冻结 pose/latent/cache/RNG 解释；
4. deployable score 的 AURC 不优于普通 confidence，或收益依赖高 clean false-reject；
5. generic gate/router/PoE 在等参数、等计算或清楚披露信息差异后达到同样结果；
6. 人工 conflict 有效但预注册真实自然错误不能复现。

任何 headroom 只保留 failure benchmark，不自动恢复 gate/router/subset/null 方法创新。

## 3. S42 v1 H2 臂的降级与重命名

S42 v1 `REPORT.md:298-307` 曾把 `A2/A3/A4` 用于 source embedding 替换。这与根协议的 A2 nearest、A3 farthest、A4 medoid 冲突。从本文件起，那三个 v1 标签**失去执行含义**，且不能出现在 manifest、结果目录、图表或主账中。

| S42 v1 历史标签/内容 | v2 状态 | 若未来保留的唯一新名 | 证据等级与限制 |
|---|---|---|---|
| v1 `A0` exact original mean | 与根协议一致 | `A0` | canonical |
| v1 `A0R` exact replay | 删除独立臂身份 | `A0@rep=n` | A0 的技术重复，不计新科学臂 |
| v1 `A1` zero-CLIP | 与根协议一致 | `A1` | canonical negative control |
| v1 `A2`：高支持来源 \(e_s\leftarrow\bar e_{-s}\) | 降级、非主矩阵 | `E-H-meanfill` | embedding-only、与原 latent cross-path inconsistent；低于 F10，不能作为性能 baseline |
| v1 `A3`：低支持来源 \(e_s\leftarrow\bar e_{-s}\) | 降级、非主矩阵 | `E-L-meanfill` | optional sensitivity negative control；不能替代 F01/F11 或 A3 farthest |
| v1 `A4`：高支持来源换真实 donor | 降级、非主矩阵 | `E-H-donor` | donor 可能改变语义/域；只作 embedding-space stress，不能替代 geometry-preserving image CF |

`E-*` 不进入当前执行顺序。只有 canonical D-stage 已完成，而且需要额外检验 embedding-space intervention fidelity 时，才可另立预注册协议运行。它们仍需固定所有其他条件、披露 cross-path conflict，并且不能用来证明自然来源贡献、性能改善或创新。

v1 中 `T_s/LC_s/NLC_s` 可保留为**补充指标定义**：当根协议使用二值 pixel mask 且区域等面积时，v1 的 `LC` 退化为根协议的 `Localization`；`NLC` 只是按支持面积校正的衍生量。执行时必须首先报告根协议要求的支持区绝对效应、非支持区绝对效应和原始 `Localization`，不能用 `NLC` 代替。

## 4. 两个数学结论与根协议的兼容性

### 4.1 均值的来源分配不变性

S42 v1 的结论

\[
m(E)=K^{-1}\sum_i e_i,\qquad m(P E)=m(E)
\]

以及 uniform mean 的 \((K-1)d\) 维线性零空间，对 canonical `A0` 完全成立。它还给出三条必要限定：

1. 置换 embedding 顺序但仍求 uniform mean 是接线守卫，不是科学臂；除浮点求和次序误差外，条件不变。
2. 该定理不预测 `F10` 没有效应。修改一个来源图会使聚合向量变化 \((e_i^{cf}-e_i)/K\)，模型可以响应这个总向量变化；定理只说 mean 没有携带“这段 delta 来自来源 i”的显式分配标签。
3. `A5` 是带来源票权的 weighted mean。若固定权重但只置换 embedding，输出通常会改变；uniform-mean 的无条件置换不变性不能原样外推 A5。只有同时置换完整的 `(weight, embedding)` 配对，集合函数才保持不变。

根协议用外部冻结的来源身份、edit mask 和支持区 `M_i` 来定义 intervention 与测量；它不声称 crossattn token 内部显式知道来源 i。因此，外部 source-indexed 反事实设计与 mean 的内部来源盲性不矛盾。

### 4.2 单 key cross-attention 的权重退化

S42 v1 的结论

\[
\operatorname{softmax}(q_rk^\top/\sqrt d)v=v
\]

对 A0–A5 和 F00/F10 中保持 one-token crossattn 的条件均成立：单 key 上的 attention weight 恒为 1，不能通过权重在来源或区域之间选择。

这不要求最终输出在每个区域相同。相同 value 可通过残差、位置相关 query state、后续层、逐帧 `replace` latent、`concat` Plücker/mask 与 `dense_vector` Plücker 产生位置相关响应。因而：

- F10 的局部响应不能解释为“单 key attention 选中了某区域”；
- F01/F11 允许检查空间 latent 路径与全局 CLIP 路径的 branch response/interaction；
- 根协议把 `concat` 与 `dense_vector` 两份 Plücker、`c/uc` 和其他状态固定，正好补足 v1 因果图中用一个 `G` 概括的相机条件；
- factorial signed interaction 与定理兼容，因为它测不同路径输入的输出交互，不声称恢复 attention 权重的地址空间。

### 4.3 兼容性总表

| 项目 | 兼容性 | 协调解释 |
|---|---|---|
| A0 uniform mean | PASS | 两个定理直接适用 |
| A1 zero-CLIP | PASS | 是路径影响负对照，不检验均值置换定理 |
| A2/A3/A4 | PASS | 都是普通单 token 替代；单-key定理适用，uniform-mean定理不适用 |
| A5 weighted mean | PASS_WITH_SCOPE | 单-key定理适用；uniform mean 的置换不变性只在成对置换权重/embedding时成立 |
| F00/F10/F01/F11 | PASS | 外部 intervention 知道来源身份；模型内 mean 不必显式保留来源标签 |
| F10/F01 cross-path conflict | PASS_WITH_WARNING | 只作 branch response，不能当自然 joint-condition 性能证据 |
| signed interaction | PASS | 先在固定有符号表示计算，与非负 localization 距离分开 |
| `Localization/LC/NLC` | PASS_WITH_PRIORITY | 根协议原始 Localization 与 inside/outside absolute effect 为必报；NLC 仅补充 |
| S_Rperm/S_Pperm/S_RPperm | PASS_AS_STRESS | 定理不把 OOD correspondence stress 变成因果 dominance 证据 |

没有发现需要修改两个数学定理的逻辑冲突；需要修正的是它们的适用域与实验标签，而本文件已经完成该协调。

## 5. 回归检查与最终裁决

| 检查 | 结果 |
|---|---|
| 当前根协议 SHA 与任务给定身份一致 | PASS |
| 增量审查 v2 SHA 与任务给定身份一致 | PASS |
| v2 六项因果修正在当前根协议中出现 | PASS |
| A0–A5 每个标签只有一个 canonical 含义 | PASS |
| v1 A0R 降为 A0 replicate，不额外占臂 | PASS |
| v1 source 替换 A2–A4 已重命名 `E-*` 并移出主矩阵 | PASS |
| F00/F10/F01/F11 与 geometry-preserving image CF 完整保留 | PASS |
| F10/F01 的 cross-path-conflict 限定完整保留 | PASS |
| signed interaction 先有符号 contrast 后取 norm | PASS |
| H3 RR/TR 同义重复已用唯一代号消除 | PASS |
| S42 v1 文件保持原 SHA | PASS |
| 模型运行、视频生成、主账写入 | 0 / 0 / 0 |

**最终裁决：PASS。** 当前根协议可以作为唯一 canonical 执行设计；S42 v1 的数学事实和候选指标在本文件限定的范围内兼容。v1 的 source-replacement `A2/A3/A4` 不再是可执行标签，只有重命名后的 `E-*` optional stress 身份。这个协调只消除了协议冲突，不证明实验有效，也不产生创新结论。

