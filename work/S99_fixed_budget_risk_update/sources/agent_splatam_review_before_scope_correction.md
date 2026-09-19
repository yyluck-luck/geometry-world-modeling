# S99 与 SplaTAM 官方代码的 keyframe overlap / tracking loss 对照

- 核对时间：2026-09-14（Asia/Shanghai）
- 范围：仅代码/协议审查；未运行 SplaTAM、未下载权重或数据、未修改 S99 代码和冻结文件。
- 官方仓库：[`spla-tam/SplaTAM`](https://github.com/spla-tam/SplaTAM)
- 固定 commit：`da6bbcd24c248dc884ac7f49d62e91b841b26ccc`（`main`，2024-06-19，`Update Torch Version Requirements`）。本机读取的文件 SHA256：
  - `utils/keyframe_selection.py`: `0ea469e1a75276f4618bfa5d1374c2b77b4bf1def8faabe6db949d4832e6fa1a`
  - `scripts/splatam.py`: `b8adb286bea49d6302769ec5af25af4938318044691a8996575c443e4b538816`

## 1. 官方代码中实际做了什么

### 1.1 overlap 不是单纯的 pose 距离

文件：[`utils/keyframe_selection.py` at commit](https://github.com/spla-tam/SplaTAM/blob/da6bbcd24c248dc884ac7f49d62e91b841b26ccc/utils/keyframe_selection.py#L40-L95)

函数 `keyframe_selection_overlap` 位于 **lines 40–95**：

1. **当前帧采样**（lines 54–60）：从当前 `gt_depth` 的正深度像素中随机抽取 `pixels=1600` 个像素。函数内部没有自己的 seed 参数，结果依赖外部 PyTorch RNG 状态。
2. **反投影**（lines 61–62，以及 `get_pointcloud` lines 10–37）：用当前帧内参和 `w2c` 把采样像素变为世界点；无效/相机原点点被移除。
3. **投影到每个历史 keyframe**（lines 64–82）：用历史 `est_w2c` 投影，并要求投影坐标位于边界 `edge=20` 内、且深度为正。
4. **overlap 分数**（lines 83–85）：
   \[
   o_j=\frac{\#\{\text{当前采样点投影到 keyframe }j\text{ 的有效像素}\}}{\#\{\text{反投影点}\}}.
   \]
5. **排序和实际抽取**（lines 87–95）：代码先按 `o_j` 降序排序，再过滤 `o_j>0`；但随后对这些候选执行 `np.random.permutation(... )[:k]`。因此**代码实际是从所有有 overlap 的候选中随机抽 k 个**，并非严格返回 overlap 最高的 k 个。论文文字描述“highest overlap”时，复现必须同时记录这一实现差异；不能只按论文自然语言改写代码。

### 1.2 keyframe 窗口包含“重叠候选 + 最近 keyframe + 当前帧”

文件：[`scripts/splatam.py` at commit](https://github.com/spla-tam/SplaTAM/blob/da6bbcd24c248dc884ac7f49d62e91b841b26ccc/scripts/splatam.py#L800-L850)

- lines **808–810**：令 `num_keyframes = mapping_window_size - 2`，调用 `keyframe_selection_overlap`，把返回的候选转回时间索引。
- lines **811–814**：若历史列表非空，强制加入最后一个 keyframe（最近 keyframe）。
- lines **815–817**：强制加入当前帧，用 `-1` 标识。
- lines **830–849**：每个 mapping iteration 从这个窗口中随机抽一个帧；历史帧使用保存的 `color/depth`，当前帧使用当前输入。mapping loss 随后在该随机抽到的帧上计算。

keyframe 本身按固定间隔、首帧或倒数第二帧加入列表（lines **911–925**），并保存 `id`、估计 `w2c`、`color`、`depth`。它是一个在线增长的帧级缓存，而不是只在一个固定候选池上做一次静态排序。

### 1.3 tracking loss 使用 silhouette 和有效深度共同约束

文件：[`scripts/splatam.py` at commit](https://github.com/spla-tam/SplaTAM/blob/da6bbcd24c248dc884ac7f49d62e91b841b26ccc/scripts/splatam.py#L214-L290)

函数 `get_loss` 从 **lines 214–216** 开始。tracking 分支只对相机参数求梯度（lines 220–224）；mapping 分支则可对 Gaussian、相机或两者求梯度（lines 225–240）。

- lines **247–259** 渲染 RGB、depth、silhouette；`presence_sil_mask = (silhouette > sil_thres)`，并从二阶深度量构造渲染不确定性。
- lines **261–272** 构造有效深度/非 NaN 掩码；可选地去掉深度离群点；只有 tracking 且 `use_sil_for_loss` 时，才把 silhouette mask 加入 tracking mask。
- lines **274–280**：L1 depth loss。tracking 时是 masked absolute error 的 `sum`；mapping 时是 `mean`。
- lines **282–290**：tracking 的 RGB loss 也是 masked absolute error 的 `sum`（若启用 silhouette/outlier mask），否则使用全图 sum；mapping 使用 `0.8 L1 + 0.2(1-SSIM)`。
- lines **693–697**：tracking loop 每轮调用 `get_loss(..., tracking=True)`，反向传播后更新相机。

这对应论文中的 RGB-D tracking/mapping，但代码的 silhouette 是**当前地图在当前视角的可见性/密度掩码**，不是对某个历史 item 的未来 signed benefit 校准。

## 2. 与 S99 固定 source-block 更新的精确区别

S99 协议和 runner：[`work/S99_fixed_budget_risk_update/PROTOCOL.md`](../S99_fixed_budget_risk_update/PROTOCOL.md)、[`run.py`](../S99_fixed_budget_risk_update/run.py)。当前 S99 是已见 S15B 数据上的几何消费者重渲染，不是 SplaTAM 运行。

| 轴 | SplaTAM 官方代码 | S99 fixed source-block 更新 | 对科学解释的影响 |
|---|---|---|---|
| 选择单位 | 在线 keyframe（整帧，含颜色/深度/估计 pose） | 四个固定来源 `[0,3,6,9]` 内的 `16×16` 几何块，共每源196块 | S99 不是帧级 keyframe cache；只能比较“局部块改写”与几何门控，不能称复现 SplaTAM memory |
| 候选分数 | 当前帧深度点投影到历史 keyframe 的有效比例 `o_j` | 历史 `D_b = median(|z_new-z_old|/[0.5(|z_new|+|z_old|)])`，未校准为概率风险 | overlap 是当前视角覆盖；`D_b` 是历史 old/new 不一致度，二者目标不同 |
| 预算 | `mapping_window_size−2` 个 overlap 候选 + 最近帧 + 当前帧；每个 mapping iteration 随机抽帧 | 每源固定更新 39/196 块（约19.9%），另有 high/low/confidence/20 random | S99 固定的是改写数量，不是 SplaTAM 的 frame window、GPU memory、forward 或 token budget |
| 状态更新 | 对 Gaussian map 和/或相机做梯度优化；可 densify/prune | 只把 selected block 的 `old_z` 换成 `new_z`，然后重新做投影/z-buffer；没有 learned state、优化器或视频生成 | S99 结果只能说明 saved geometric consumer 的相对端点效果 |
| 选择随机性 | 当前 depth 像素随机抽样；重叠候选代码又随机抽 k；mapping iteration 随机抽窗口帧 | random 条件预设 20 个 NumPy seed；low/high/confidence 为确定性排序 | 复现 SplaTAM 风格 baseline 必须独立冻结 PyTorch/NumPy RNG，不能把 SplaTAM 代码的随机抽样误写成确定性 top-k |
| 目标 | 跟踪当前相机、优化在线地图并生成新 Gaussian | 比较未来四个已见目标深度上的重投影误差/coverage/尾部 | SplaTAM 的在线 tracking loss 不是 future RGB-D signed benefit |
| source identity | 关键帧 ID 可追踪，但 Gaussian 更新由多帧优化共同产生 | `source_pixel_identity` 随 z-buffer 重新计算；保留块到未来像素的身份 | S99 有更直接的 block provenance，但仍非单一历史帧的完整 consumer effect |

因此，SplaTAM 最适合作为一个**强工程对照族**：`overlap/visibility-gated` 与 `depth-residual/coverage-gated`，而不是把 S99 叙述成 SplaTAM 的复现。若要实现对照，必须先定义“一个 source block 的 overlap”如何计算（例如把当前 query 的有效深度点投影到该来源对应相机），并固定同样 39 块/源、相同 z-buffer、相同 future query 和相同计算成本。

## 3. 对上一份原文分析的核对

上一份分析称 SplaTAM 有三类相关信号：silhouette/可见性、overlap keyframe 选择、RGB-D 残差。这与官方代码一致，但需要两个更精确的修正：

1. 论文/代码的 overlap 选择不是单纯“选最高 overlap 的 k 个”：代码 **lines 87–95** 在排序后再次随机置换并截取，因此应报告为“overlap-ranked candidate pool + random k sampling”，除非另立实现修正并明确偏离官方代码。
2. tracking 的 depth/RGB loss 是当前渲染地图对当前观测的 masked L1（tracking 时 sum），并在 `use_sil_for_loss` 时限制到 silhouette；它不是对更新前后两个长期状态的 paired future loss，也没有 source-level `L(0)`/`L(1)`。

## 4. 可证伪的下一步假设（不在本轮执行）

### H-S99-Overlap-v1

在相同每源 39 个块、相同 candidate pool、z-buffer、未来 query 和运行预算下，定义一个 SplaTAM-style `overlap/visibility` block score：当前 query 的有效 RGB-D 点反投影到 source block 对应相机后，统计进入该 block 的比例；同时记录 silhouette/valid-depth mask 和当前深度残差。若它真正刻画“更新后对未来的有用程度”，则：

\[
\operatorname{Spearman}(o_b, B_b)>0,
\quad
B_b=L_{\mathrm{retain}}-L_{\mathrm{update}},
\]

且 overlap-gated 的平均 `B` 应至少不低于 S99 的 low-disagreement gate；其 `P(B<0)` 和 worst-5% 也不应更差。

**支持条件（预先写死）：** 至少 3/4 个未来目标和四目标等权平均中，overlap-gated 相对 20-seed random 的 mean AbsRel 有利；同时 delta1 不下降、负收益比例与 CVaR95 不劣于 low-disagreement；结果要在新的合法未见轨迹或动态重访数据上重复。

**否证条件：**

- `o_b` 与 `B_b` 无正方向关系，或低 overlap 的块反而有更高正收益；
- overlap-gated 不超过 random/pose/coverage，或优势在同样读取/选择/forward 成本后消失；
- low-disagreement 的优势在加入 overlap/silhouette/depth-residual 后完全消失，说明它可能只是普通可见性/重叠的替代变量；
- 只有当前 RGB/MSE 变好，future depth/pose 或 worst-5% 变坏；
- 由于 SplaTAM 代码中的随机候选抽样，重复 seed 后结论不稳定。

本假设只测试“overlap/visibility 是否已足以解释低几何不一致度的收益”，不授予 GRC-Memory 或任何新颖性结论。

## 5. 结论边界

- 已核实：官方 commit、函数、行号、随机采样、overlap 计算、silhouette/loss mask、keyframe 窗口和 mapping 随机抽样。
- 可用于 S99 的：作为公平的强工程 baseline 设计依据和混杂解释；必须匹配 39-block budget 与相同 consumer。
- 尚未证明：SplaTAM 风格 overlap 是否能预测 S99 的 signed future benefit；是否优于 low-disagreement；是否能支持新的方法问题。
- 本轮没有模型执行、没有新数据结果、没有新颖性授权。

## 原始来源

1. [SplaTAM official repository at fixed commit](https://github.com/spla-tam/SplaTAM/tree/da6bbcd24c248dc884ac7f49d62e91b841b26ccc)
2. [`utils/keyframe_selection.py`, lines 40–95](https://github.com/spla-tam/SplaTAM/blob/da6bbcd24c248dc884ac7f49d62e91b841b26ccc/utils/keyframe_selection.py#L40-L95)
3. [`scripts/splatam.py`, keyframe window lines 800–849 and tracking loss lines 214–290](https://github.com/spla-tam/SplaTAM/blob/da6bbcd24c248dc884ac7f49b841b26ccc/scripts/splatam.py#L214-L290)

## 6. 针对 S99 负结果的唯一后续机制假设

### 结果边界

S99 新结果为：low-disagreement 四目标平均 AbsRel `0.07956058`，略优于 20-seed random 均值 `0.07997773`，但差于 confidence-gain `0.07836487`；low-disagreement 的平均 `delta1_all_gt` 为 `0.66126`，低于 random `0.66441` 和 confidence-gain `0.66216`。这是一个已见 saved geometric consumer 上的探索性结果；四个目标来自同一序列，不能当作跨场景确认。

### 机制假设 H-S99-Redundancy-v1

**低不一致度 `D_b` 主要是“避免明显有害改写”的安全分数，而不是“增加未来信息”的收益分数。** 因此 low-D 选择器可能挑中与旧状态几乎相同、未来增量很小的冗余块；confidence-gain 选择器虽然不保证安全，但更可能挑中能改变未来可见几何的块。这一假设同时预测：

1. 单块 signed future benefit `B_b=L(never)-L(update_b)` 与 `D_b` 的相关性接近零或不稳定；
2. 在相同 39 块/源预算下，low-D 的负收益比例可能低于 random，但其正收益均值不高；confidence-gain 的平均 `B_b` 更高，因而可解释其 AbsRel 优势。

这只是对 S99 负结果的一个机制解释；若数据不支持，必须放弃该解释，不把 low-D 改称新方法。

### 一个决定性实验：逐块 signed-benefit response matrix

在同一 S99 saved consumer、同一四个来源和四个目标上，冻结当前 `never` 状态、旧/新几何、相机/K/尺度、z-buffer、代码和随机种子。对每个 source block（4×196=784 个）分别做一次**只改写这一块**的完整重渲染：

- `F0`：不改该块（never）；
- `F1(b)`：只把 block `b` 从 old 替换为 new；
- 目标答案只在所有 `F1(b)` 预测完成并封存后读取；
- 计算每个 block/target 的 `B_b=AbsRel(F0)-AbsRel(F1(b))`，以及 source provenance 改变、coverage、worst-5% 和 `delta1` 的配对差。

只用历史信息形成两个预先冻结的排序：`D_b`（low-D）和 `confidence_gain_b`；未来 `B_b` 只作结果，不参与排序或阈值。然后在每源 39-block 预算下报告：

- `mean(B_b)`、`median(B_b)`、`P(B_b<0)` 和 signed-benefit CVaR；
- `Spearman(D_b,B_b)` 与 `Spearman(confidence_gain_b,B_b)`，按目标和四目标等权汇总；
- 由逐块 `B_b` 生成的 39-block 集合仅作**oracle 上界诊断**，不作为合法 selector 结果。

**预注册支持/否证规则：**

- 若 low-D 的 `P(B<0)` 明显较低但 `mean(B)` 接近 0，且 confidence-gain 的 `mean(B)`/下尾更好，支持“low-D 是 harm-avoidance、不是增益预测”机制；
- 若 `D_b` 与 `B_b` 呈稳定正向关系，或 low-D 的 mean/signed-tail 在逐块响应和四目标中均优于 confidence-gain，则否证该机制，并停止把 confidence-gain 优势解释为“信息增量”；
- 若所有 `B_b` 均小于 exact replay 波动，或 source provenance 变化极少，结论为“当前 consumer 无法识别逐块未来收益”，不升级任何方法主张；
- 由于 S99 是 previously exposed saved-data consumer，本实验最多解释该设置下的机制，不能宣称 held-out、跨场景或 GRC-Memory 成立。

