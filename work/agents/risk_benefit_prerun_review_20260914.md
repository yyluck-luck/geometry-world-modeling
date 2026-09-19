# 风险到未来收益诊断：独立实验前审（2026-09-14）

**审查对象**：S91R-C 的已保存控制分析、S92 尾部诊断，以及拟议的 S15B 几何消费者重算。  
**审查边界**：只检查现有缓存能否识别问题、哪些混杂会阻断解释，以及一个最有判别力的对照。没有修改旧结果、没有训练、没有运行新模型。

## 1. 要检验的命题

候选命题是：从过去 proposal 中计算的 old/new 几何相对不一致度

\[
D_s(u)=\frac{|z_{new,s}(u)-z_{old,s}(u)|}{0.5(|z_{new,s}(u)|+|z_{old,s}(u)|)}
\]

能够区分在固定几何更新预算下的未来有符号收益。定义条件 `c` 相对 `never` 的像素收益为

\[
b_c(u)=\mathrm{AbsRel}_{never}(u)-\mathrm{AbsRel}_{c}(u),
\]

正值表示条件 `c` 改善，负值表示变差。这个命题比“D 与未来误差相关”更强，因为它要求 D 能指导一个固定预算的消费者干预。

## 2. 缓存可以识别什么

现有数组足以做一次**回顾性、已见单段、已知查询相机的几何消费者诊断**：

- `proposals.npz` 有 4 个来源的 `old_self_z_m`、`new_self_z_m`、old/new confidence、来源相机和内参；四个来源各有 `224×224=50,176` 个像素，当前 old/new 均为正且有限，因此可以在过去量上做固定分位排序。
- `target_predictions.npz` 有 `never`、`all_new` 等七种已保存消费者输出，以及每个输出像素的 source provenance；`evaluation_gt.npz` 有 4 个已保存目标深度。
- `s15b_memory_consumer.py` 的 `render` 会重新投影全部四个来源并做 z-buffer，因此可重算“只把固定 source block 从 old 替换成 new”的下游结果，避免把旧 target 像素直接拼接成假干预。
- `target_camera_inputs.npz` 提供共同查询相机；它不是新的 future depth，但它表示一个**已知查询相机条件下**的几何读出问题，不是完整 world-model 的未知相机预测。

因此可识别的对象是：**固定 20% source-block 更新预算下，D 排序的局部替换是否比同覆盖率随机替换产生更好的已保存目标几何误差**。这不能识别跨场景效果、生成视频质量或单条记忆的总因果效应。

## 3. 必须提前冻结的处理

建议每个 source 的 196 个 `16×16` block 用以下确定规则处理：

1. 每块用 `median(D)` 作为几何风险；每源选恰好 `floor(0.20×196)=39` 块。low-D 和 high-D 都按 `(block statistic, row, col)` 稳定排序解决并列，不用 `D≤quantile` 造成数量漂移。
2. low-D / high-D 的阈值只从 4 个 source proposal 的全部过去正有限 old/new 像素得到；不使用 future mask、future depth、target prediction、GT 或结果后调阈值。
3. 随机 placebo 也每源选恰好 39 块、无放回；预先固定 20 个 seed，不能根据结果增删 seed 或挑最好的一次。它是唯一建议保留的显式对照：`low-D 39-block update` 对比 `same per-source coverage random 39-block update`。
4. 若保留 high-D 和 confidence-delta 条件，它们应当作为预注册的机制应力条件，不能事后从它们和随机组中挑一组作为主结论。若希望本轮只执行一个判别对照，则优先执行 low-D vs random；high-D/confidence 可留为后续，不影响本次判断。
5. 新 runner 的 `never` 与 `all_new` 必须逐元素、逐 provenance ID 与已保存 `target_predictions.npz` 的方法 0/1 完全一致；不一致就停止，不读取 GT 评分。

## 4. 结果应怎样计算

对每个目标、每个条件，至少同时报告：

- **主收益**：`b_c=AbsRel_never−AbsRel_c` 的均值；正值是改善。
- **worst-5%**：按固定 paired pixels 的 `b_c` 从小到大，取最差 `ceil(0.05 n)` 个的平均（lower-tail CVaR-5%）；负值表示最坏尾部变差。不能把“最高5%恶化质量占比”与这个 signed worst-5% 混用。
- **公平分母**：主表用所有条件共享的 `GT-valid ∩ prediction-valid` 交集，逐目标列有效像素数；另报每条件自己的覆盖率和 `delta1_all_gt`。共享交集避免某条件靠少输出难例改善均值，但交集过小也必须显式标红。
- **目标聚合**：先列 4 个目标的结果，再报 4 目标等权均值；不要把像素池化成一个独立样本或把 4 个目标称成 4 个独立场景。
- **机制记录**：保存每条件的 source provenance map、相对 `never`/`all_new` 的 source-ID 变化、投影覆盖、每源实际 changed blocks/pixels。若 low-D 只改变了很少的可见像素，不能解释成完整 20% 记忆收益。

## 5. 主要阻断点与审稿结论

### Source ID 混杂（主要阻断）

S91R-C 已显示 `never` 与 `all_new` 的配对像素 source identity 仅约 4.35%–5.49% 相同。由于 z-buffer 会在 old→new 替换后重新决定可见来源，`b_c` 是整个固定消费者的效果，不能解释为“同一记忆条目被替换后的因果效应”。本实验可以检验 consumer-level block policy，不能支持 GRC 的单记忆因果主张。必须把 source-ID 变化作为结果，而不是丢弃。

### GT 泄漏与已见数据

风险排序本身可做到过去-only，但目标相机和目标深度是同一已保存 S15B 单段数据；`evaluation_gt.npz` 只能在所有预测与 provenance 封存后读取。即使严格执行顺序，这仍是回顾性 exploratory audit，不能作为未见确认或跨场景验证。

### 选择后偏差

四目标、多个条件和多个尾部指标会产生事后挑选空间。所有条件、39/196 覆盖率、20 个 seed、worst-5% 定义和主分母必须在读结果前冻结；不得因 low-D、high-D、confidence 或随机种子中某个更好就改写主问题。固定 20% 只是预算匹配，不是风险校准得到的最优预算。

### 相关特征的替代解释

S91R-C 的 disagreement 加入 confidence/depth/edge/mask/pose 控制后平均 `ΔR²=0.01463` 且四个留出目标均为正，但因 source identity 低而触发 `STOP_GRC_METHOD_CLAIM`。因此新 block audit 可以检查“D 排序在真实重新投影消费者中是否有小的策略收益”，却不能声称 D 已证明是独立信号；随机 placebo 是必要且足够的第一对照，不能替代 confidence-only 或 coverage 的完整竞争基线。

## 6. 前审结论与唯一建议

**结论：有条件通过一次 exploratory consumer-level audit；不通过 GRC-Memory 方法验证。**

本地缓存能识别的最有价值、最便宜问题是：

> 在每源恰好更新 39/196 个 16×16 source blocks、完全相同投影/z-buffer 和已知目标相机下，low-D 更新相对同覆盖率随机更新是否提高未来 signed AbsRel，且 worst-5% 不恶化？

建议唯一显式对照为**每源 39 块的固定覆盖率随机 placebo（20 个预注册 seed）**。若 low-D 不稳定超过随机，或 worst-5% 明显为负，则停止把 D 当作记忆选择依据；若胜出，也只能得到“已见单段的消费者策略信号”，必须另用未见 RGB-D/位姿和同 source ID 合同验证后才可讨论方法贡献。

**状态**：`PRE-RUN_CONDITIONAL_PASS_EXPLORATORY_ONLY`。  
**禁止表述**：已验证 GRC、单记忆因果收益、跨场景泛化、视频质量提升、创新成立。

## 7. 对 S99 固定改写预算草案的逐条前审

**通过条件**：S99 可以运行一次保存数据的几何消费者重渲染，但以下边界必须保持在协议和结果表中。

1. **这不是 `k` 条记忆预算。** 39 个 block/source 是候选几何网格的改写数量；每块 256 像素，4 源共 156/784 blocks、39,936/200,704 source pixels。它不等于 39 条历史帧、token、显存或检索记忆。论文中必须称“固定 source-block rewrite budget”，不能称 GRC 的记忆容量 `k=39`。
2. **19.898% 而非精确 20%。** `floor(0.20×196)=39`，实际比例为 39/196=19.897959%。四源合计仍是 156/784=19.897959%。所有规则和图注使用这个精确比例。
3. **更新幅度不是被匹配的。** low-D、high-D、confidence_gain 和 uniform random 虽然每源同为 39 块，但 `|z_new−z_old|` 的总和、均值、median、p90 可能显著不同。每条件必须报告更新像素的 L1/L2/相对幅度及每源分布；如果 low-D 胜出，只能说“在该固定改写数下的策略信号”，不能排除“它改得更小”这一解释。uniform random 是覆盖率 placebo，不是幅度匹配 placebo。
4. **coverage 不能藏在共同域里。** 预先定义的“25 条件预测有效性的全交集”虽然避免了看 GT 后选域，但会把 post-treatment 的可见性/遮挡结果纳入分母选择，且 20 个随机条件可能令交集变小。建议主表使用每条件与 `never` 的 paired domain（`GT-valid ∩ never-valid ∩ condition-valid`），逐条件报告分母与 coverage；同时保存并报告全 25 条件交集作为预注册敏感性分析。若坚持全交集为主，必须报告从 GT-valid、never-valid 到全交集的逐步像素损失，且交集过小则结论降级。
5. **共同相机是已知条件。** `target_c2w` 来自旧 S15B 的给定相机合同，目标深度才是评分答案。新实验不得暗示仅靠历史 RGB 预测了未来相机；应称“已知查询相机条件下的几何消费者”。
6. **端点只做接线与参考。** `never`/`all_new` 不是 39 块同预算方法；它们用于逐值/逐 source-ID 接线核验及全量上下界参考。只有 low-D、random 等 39-block 条件之间可比较固定改写预算。
7. **答案隔离顺序必须可审计。** prediction 阶段不得打开 `evaluation_gt.npz` 或目标 depth PNG；封存所有 25 条件的 depth/provenance/masks 后，独立 score 阶段才读取答案。缓存中的 target camera 可以在 prediction 阶段使用，但记录其既有来源和 SHA。
8. **选择后偏差仍然存在。** 这些四目标和 S15B 方法已在先前工作中暴露；本轮“先冻结再评分”只能防止本轮新增的结果后调参，不能创造未见测试。所有 20 个随机 seed 和四目标等权聚合必须固定，不能挑最佳 seed/条件。
9. **至少一项独立复核。** 复核者从冻结 mask 和 source geometry 重新实现一个 low-D 目标的 projection/z-buffer，逐值核对 depth 与 source-ID；不能只检查 JSON 字段。复核前不读取 GT 数值，复核评分再单独读取同四张答案。

### 本审查建议的唯一对照

若本轮只保留一个正式对照，选 **每源随机 39 block 的 20 个固定 seed placebo**，并将 low-D 作为主策略。high-D 是方向反例，confidence_gain 是普通信号对照；二者可作为已冻结的补充条件，但不能在结果后改作主对照。所有条件都应报告，不能用“随机均值”替代其 seed 分布。

### S99 的验收门

在没有读取 GT 前，必须有：25 条条件的选择 masks、block 分数、固定 seed、端点 parity（depth 与 source-ID）、输出完整性和源码/协议 SHA。评分后，只有当 low-D 在至少 3/4 目标及四目标等权平均都优于 random 均值和 confidence_gain，同时 delta1_all_gt 不下降时，才可以把它写成“下一轮开发候选”；即便如此，仍是已见单段 consumer-level 信号，不是 GRC-Memory 验证。
