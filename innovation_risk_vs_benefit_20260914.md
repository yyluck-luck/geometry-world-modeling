# 从“低几何风险”到“更新有益”：原文检索与可证伪诊断

- 检索/写入时间：2026-09-14（Asia/Shanghai）
- 任务：审查当前候选命题 `低历史几何风险 => 采用该历史更新会降低未来误差`。
- 原则：本文件是原文近邻与实验设计分析；没有运行模型，不修改主账，不把 GRC-Memory 写成已验证方法。
- 精读原论文：SelectiveNet（ICML 2019）、Policy Learning With Observational Data（Econometrica 2021）、SplaTAM（CVPR 2024）。

## 1. 先把问题写成两个潜在结果

对历史记忆条目 `i` 和未来查询 `t`，定义两个**潜在结果**（同一条件下只能实际观察其中一个）：

- `L_t(1,i)`：接受/应用条目 `i`，让它经过完整 world-model consumer 后得到的未来几何损失；
- `L_t(0,i)`：拒绝/保留旧状态（或重新观察），在相同外生条件下得到的未来几何损失。

真正的 signed future benefit 应定义为：

\[
B_{t,i}=L_t(0,i)-L_t(1,i).
\]

`B>0` 才代表更新有益，`B<0` 代表更新有害。当前 GRC 候选里的 `q_i`（重投影、深度、可见性风险）至多试图预测 `L_t(1,i)` 的坏程度；它**没有自动提供** `L_t(0,i)`，所以不能由“低 q”逻辑推出 `B>0`。

一个最简单的反例是：旧状态已经很准（`L(0)=0.01`），新条目也很低风险（`L(1)=0.02`）。新条目满足“低风险”，但 `B=-0.01`，更新反而有害。反过来，某条目绝对重投影误差较大（`L(1)=0.10`），但旧状态更差（`L(0)=0.30`），它仍有正收益。故选择目标必须从**绝对风险排序**升级为**相对基线的效应/决策收益**。

## 2. 原论文一：SelectiveNet 只解决“接受样本的风险”，不解决“更新相对保留是否有益”

**来源：** Geifman & El-Yaniv, *SelectiveNet: A Deep Neural Network with an Integrated Reject Option*, ICML 2019。原文给出的 coverage 为
`φ(g)=E[g(x)]`，selective risk 为
`R(f,g)=E[ℓ(f(x),y)g(x)]/φ(g)`，并将问题写成在 `φ(g)≥c` 约束下最小化 `R(f,g)`；见[论文原文](https://proceedings.mlr.press/v97/geifman19a/geifman19a.pdf)（定义见 PDF 第 1 页，目标和损失见第 2 页）。

### 原文机制

SelectiveNet 学习预测头 `f` 和拒绝/覆盖头 `g`，用覆盖率约束优化已接受样本的条件风险；它还加入辅助头，避免模型只拟合被选择的子集。该问题的动作是“输出预测/拒绝预测”，基线是“不输出”，而不是“把一个状态写入持久记忆后与旧状态竞争”。

### 对当前问题的精确启发

把“接受历史项”看成 coverage gate 是有用的，但目标函数应改成**增量收益选择**：

\[
\min_{g:\,\phi(g)\ge c}
 E[L(1,i)-L(0,i)\mid g(i)=1],
\]

或在固定预算下最大化
`E[B_i·g(i)] - λ Cost(g)`。单独最小化 `E[L(1)|accept]` 会出现“保留旧状态本来更好”的错误；它只能告诉我们被接受的更新本身风险较低，不能证明更新值得执行。

### 关键近邻边界

- 已覆盖：risk–coverage 曲线、按置信度拒绝、覆盖率校准；不能把“risk-calibrated selector”单独写成创新。
- 尚未由该论文覆盖：历史 item 的 source identity、完整 consumer 下的 `L(1)` 与 `L(0)` 配对、未来 RGB-D/pose 目标、几何支持局部性。
- 结论：SelectiveNet 给出**拒绝选项的评价语言**，但不提供 GRC 的 signed benefit 识别。

## 3. 原论文二：政策学习把“动作是否值得”写成 treatment effect / welfare，而不是 outcome risk

**来源：** Athey & Wager, *Policy Learning With Observational Data*, Econometrica 2021。[期刊原文](https://onlinelibrary.wiley.com/doi/10.3982/ECTA15732)；[可检索公式的开放预印本](https://arxiv.org/pdf/1702.02896)。

### 原文机制和公式

论文先构造 doubly robust score `Γ̂_i` 来估计个体条件 treatment effect，再在受约束政策类 `Π` 中求：

\[
\hat\pi=\arg\max_{\pi\in\Pi}
\frac1n\sum_i(2\pi(X_i)-1)\hat\Gamma_i.
\]

原文明确说明：`Γ̂_i` 是干预相对另一动作的效应分数；在选择性可观测等假设下，策略价值可用双重稳健估计，且给出 utilitarian regret 的渐近保证。这个目标与当前问题的差异非常关键：策略学习估计的是**做与不做的差值**，不是只估计“做了以后有多差”。

### 对 GRC 的可迁移形式

把 `W_i=1` 定义为“接受历史条目/更新记忆”，`W_i=0` 定义为“保留旧记忆/重新观察”，将 future geometric loss 作为 outcome，则可定义：

\[
\tau_i=E[L(1,i)-L(0,i)\mid X_i],
\qquad
B_i=-\tau_i.
\]

若有可交换性（动作分配不再依赖未观测因素）和 positivity（每类 `X` 都有两种动作样本），可以借鉴 doubly robust score 估计 `B_i`，再在固定记忆预算下选择 `B_i>0` 的条目。若没有随机化或自然重复，不能直接套用因果保证；必须使用 exact replay 的成对干预、预先冻结的随机动作或明确写成描述性反事实诊断。

### 当前论文与 GRC 的差别

- 已覆盖：受预算约束的动作选择、效应而非绝对风险、政策 value/regret 评价。
- 可能未覆盖：历史观测 item → world-model 全部消费路径 → 未参与选择的未来 RGB-D/pose；但“可能未覆盖”不等于新颖性证明。
- 重要限制：本项目的 `DEVELOPMENT_SEEN` TUM 轨迹和确定性 memory routing 不能自动满足 policy learning 的可交换性/positivity；不能用小样本离线差分宣称 treatment effect。

## 4. 原论文三：SplaTAM 展示 online 3D memory 的强基线，但其局部几何门控不是 signed future benefit

**来源：** Keetha et al., *SplaTAM: Splat, Track & Map 3D Gaussians for Dense RGB-D SLAM*, CVPR 2024。[CVPR 原文页面](https://openaccess.thecvf.com/content/CVPR2024/html/Keetha_SplaTAM_Splat_Track__Map_3D_Gaussians_for_Dense_RGB-D_CVPR_2024_paper.html)，[可读原文](https://arxiv.org/html/2312.02126v3)。

### 原文机制和公式

SplaTAM 用渲染的 silhouette 判断地图中已经有可靠密度的区域，并在相机跟踪时只在可见可靠区域计算：

\[
L_t=\sum_p (S(p)>0.99)\,[L_1(D(p))+0.5L_1(C(p))].
\]

地图稠密化使用：

\[
M(p)=(S(p)<0.5)
+ (D_{GT}(p)<D(p))\,[L_1(D(p))>\lambda\,MDE],
\]

其中 `λ=50` 是经验阈值。它还保存当前帧、最近关键帧和与当前视图重叠最高的 `k−2` 个关键帧；重叠由当前深度点云落入候选关键帧视锥的点数决定。原文见[公式与关键帧规则](https://arxiv.org/html/2312.02126v3#S4.SS1)。

### 对当前问题的精确启发

SplaTAM 证明了“可见性/重叠/深度残差”是合理的 online mapping 信号，也给出 RGB 与 depth loss 必须共同使用的反例。但其门控回答的是“当前地图哪里需要优化/增加 Gaussian”，而不是：

1. 一条具体历史 item 是否真的被未来生成 consumer 使用；
2. 接受它相对保留旧地图的未来几何效果 `B_i`；
3. 该 item 的风险分数是否能预测这种 signed effect；
4. 在动态变化、运动模糊、大深度噪声下，低局部残差是否会导致有害持久更新。

原文的限制段还明确提到对运动模糊、大深度噪声和激烈旋转敏感，并要求已知内参和稠密深度。这些条件正是“看起来局部可信、但未来更新有害”的候选故障来源；不过这只是近邻启发，不是当前项目数据证明。

## 5. 三篇论文合起来后的核心判断

### 5.1 低风险与正收益不是同一个统计量

| 量 | 询问的问题 | 可否直接支持更新决策 |
|---|---|---|
| `q_i` 或 selective risk | 接受该 item 后，结果本身可能有多大误差？ | 不够；缺少保留旧状态的反事实 |
| coverage | 有多少 item 被接受？ | 不够；可能覆盖了很多“安全但无用”更新 |
| `B_i=L(0)-L(1)` | 接受相对保留是否改善未来？ | 是，需成对干预/随机化/明确识别条件 |
| policy value | 整个选择策略的平均收益和 regret | 是，需固定预算和独立未来 outcome |
| tail/CVaR of `B` | 少量有害更新是否抵消多数小收益？ | 必须；与 S92 尾部现象直接相关 |

### 5.2 “harmful confident update” 是必须预注册的反例

即使 `q_i` 很小，也可能出现：

- **冗余更新**：旧状态已覆盖该区域，新 item 几何安全但没有增量信息，`B≈0`；
- **基线更强**：旧状态有更低未来误差，安全的新 item 仍使融合退化，`B<0`；
- **动态变化**：历史帧局部重投影良好，但物体/遮挡已改变，持久写入污染未来；
- **路径冲突**：同一 source 在 latent/attention/几何路径的权重不一致，绝对风险低但下游组合产生重影；
- **时间/配对错误**：低误差来自错误最近邻或 support gap 两侧，真实未来几何反而被污染。S97 已说明此类数据合同错误会把“可用”误判为“可评测”。

因此必须报告 `P(B<0 | q≤τ)` 和 worst-tail，而不能只报告被选择子集的 mean AbsRel。

## 6. 最便宜的决定性诊断（不训练新方法）

### Gate R1：先验证“风险是否预测更新收益”

在合法、未见、严格 RGB-D/pose 配对数据上，冻结历史候选、未来查询、阈值和随机种子。对同一历史 item 做两个完整 consumer 路径：

- `F1`：接受该 item；
- `F0`：保留旧记忆/删除该 item。

固定干预前外生条件、非目标历史和同一 noise，但目标 item 的所有下游后代必须重算。用未来独立 depth/pose 计算 `B=L(F0)-L(F1)`。先不训练 selector，只检验：

1. `Spearman(q_i, B_i)` 的方向和 bootstrap 区间；低 `q` 是否更常有 `B>δ`；
2. `P(B<0|q≤τ)` 是否低于预注册上限；
3. `B` 的 mean、median、worst-5% 和 CVaR95；
4. placebo：打乱 source ID、替换面积/形状/edge density 匹配的 mask，观察定位收益是否消失；
5. exact replay 方差：若 `|B|` 不超过同一条件重放噪声，判定无法识别。

推荐把主门写成**benefit calibration**而非只写 risk calibration：

\[
\Pr(B_i>\delta\mid q_i\le\tau)\ge 1-\alpha,
\]

或对 `B_i` 构造下置信界 `LCB(B_i)>δ` 才允许更新。仅有 `UCB(L(1))` 不足以证明收益，除非同时有可靠的 `LCB(L(0))`。

### Gate R2：最小决策对照

在同一候选池和固定 `k` 下比较：

1. recent / random / pose-only / coverage；
2. risk-only（当前 GRC 候选）；
3. utility-only（直接估计 `B`）；
4. benefit-gated（只接受 `LCB(B)>δ`）；
5. risk+benefit（成本相同）；
6. “保留旧状态”安全基线。

所有方法共享 consumer、候选数、输入 token/bytes、forward 次数和选择时间；未来答案不可进入校准和排序。主指标报告 signed future benefit、mean AbsRel、worst-5%/CVaR95、reprojection/coverage、负收益比例和延迟/内存。

### Gate R3：最小在线 3D memory 近邻对照

用 SplaTAM 式 overlap/silhouette/depth-residual 作为**强工程基线**，但将其改写为当前消费者可执行的候选选择器；不声称复现 SplaTAM 的完整 SLAM。关键问题是：

- 局部 overlap/残差 gate 是否能预测 `B`？
- risk-only 是否在相同预算下超过 overlap/coverage？
- 动态/遮挡条件下，二者是否出现 harmful confident updates？

若 risk-only 只与 SplaTAM 式 coverage 一样好，GRC 的独立贡献就很弱；若 benefit-gated 在多个场景显著降低负收益尾部，才有理由继续方法化。

## 7. 审稿式新颖性判断

| 候选表述 | 近邻覆盖情况 | 当前潜力 | 直接失败条件 |
|---|---|---:|---|
| “低几何风险选择记忆” | SelectiveNet、GIM/空间记忆、SplaTAM式 gate 已覆盖表面机制 | 3–5/10 | 只优化 selected risk 或只换阈值 |
| “风险-预算 memory pruning” | GIM/长期记忆/forgetting 已部分覆盖 | 4–6/10 | 只报告当前重建或闭环画质 |
| “历史 item 的 calibrated risk 预测独立未来误差” | 本轮未找到完整同命题证据，但仍是问题空白 | 7/10（未验证） | q 与 future loss 无预测性 |
| **“benefit-calibrated memory update：预测接受相对保留的 signed future benefit”** | 三篇论文分别覆盖 selective risk、policy effect、online geometry gate；未见完整 world-model source-level 联合合同 | **7.5–8/10 潜力** | 无法识别 `L(0)`、效应低于 replay、普通 baseline 已解释 |
| “仅用 GIM 核谱/PSD 修复作为创新” | 属于实现/数学审计 | 1–3/10 | 没有 consumer 与未来效应 |

“benefit-calibrated update”目前只能作为**新的可证伪研究问题/方法候选**，不能写成已成立创新。它比原 GRC-Memory 风险排序更精确：模型不是问“这个 item 安不安全”，而是问“在同一未来任务下，采用它是否比保留当前状态更好”。

## 8. 停止条件（提前写死）

立即停止该创新主张并降级为测量/工程报告，若发生任一情况：

1. `L(0)` 无法在合法数据上定义，或没有可复查的 source-level intervention；
2. `B` 的绝对值不超过 exact replay noise，或符号随 seed/placebo 改变；
3. 低 `q` 与 `B` 没有预注册方向关系，`P(B<0|q≤τ)` 不低于安全基线；
4. benefit-gated 不优于 utility-only、coverage、pose-only 或“保留旧状态”，尤其在成本匹配后优势消失；
5. 只在 TUM 开发序列成立，换未见场景/动态序列后消失；
6. 未来答案泄漏到校准、阈值或候选排序，或 RGB-D/GT 支持区间不满足 S97/S98 合同；
7. 只改善当前 RGB/MSE，未来 depth/pose 或尾部风险恶化；
8. 普通 attention/overlap/silhouette/depth gate 在同一 source identity 和预算下已解释全部效果。

## 9. 最终结论

本轮原文精读支持一个更清楚的创新分界：SelectiveNet 的 risk–coverage 不能回答 update-vs-retain；Athey–Wager 的 policy learning 提供“动作相对另一动作的效应/策略价值”框架；SplaTAM 提供 online 3D memory 的 overlap、silhouette 和 depth-residual 强基线，但没有 source-level signed future benefit。由此，当前最值得做的低成本实验不是训练一个更复杂的 risk gate，而是先在真实未见配对数据上估计 `B=L(0)-L(1)`，检验低风险是否真的对应正收益。

如果 R1/R2 失败，必须保留失败并停止 GRC 方法叙事；如果它们在多场景、固定预算、强基线和完整 consumer 下成功，才可把“benefit-calibrated memory update”升级为方法候选。当前状态仍是 `new_method_validated=false`，没有新的模型实验结果。
