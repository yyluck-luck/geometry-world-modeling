# GRC-Pilot创新检索闸门：固定预算、未来一致性与不确定性选择

- 检索时间：2026-09-12 15:39（Asia/Shanghai，UTC 07:39）
- 目的：给正式 `S91（未来几何风险增量预测试验，GRC-Pilot）` 固定必须加入的强对照与可推翻预测。
- 范围：本轮核对三篇原始论文/官方代码，避开已经在前轮详细记录的 R2M-Bench、WorldPack、GIM-World、CAP、Long-Context SSM、WORLDMEM、C3。检索只产生协议依据，不构成项目实验。

## 1. Addressable Memory for Video World Models（WorldTrace）

**原始位置。** Wu et al., arXiv:2608.07408v1, 2026-08-07。方法和实验分别见原文 Sec. 2--4；固定预算分配见 Appendix E.1（原文 HTML 行 686--697），记忆成本见 E.6（751--760），LoopBench 的自生成回访协议见 Appendix E/原文行 672。

**机制与 GRC 的差别。** WorldTrace 解决的是自回归视频 KV cache 的可寻址性：把远历史压到固定槽位，并将摘要放入训练分布内的虚拟位置；Field 做 canonical-key 均值，Landmark 保留场景进入时的关键轨迹。它按时间/场景事件写 cache，并没有用“历史几何风险 → 独立未来几何收益”作选择目标，也没有 conformal 风险上界。其 LoopBench 主要把回访结果与模型早先生成的匹配位姿帧比较，不能替代独立传感器深度或几何真值。

**必须加入的对照。** `sliding/recent`、`WorldTrace-Field`、`WorldTrace-Landmark`（若工程可复用）；各自严格相同 summary+recent 槽位数、GPU cache、host memory、生成步数和回访轨迹。预算表必须单独记录 GPU cache、CPU/host 记忆、选择/更新时间；原文 E.6 显示 Field 虽 GPU 固定，host canonical key 会随历史增长，不能只写固定 k 帧。

**可推翻预测。** 在相同预算下，如果 GRC-Pilot 的 risk+utility 不能超过 recent/sliding 或 WorldTrace 的未来深度、位姿重投影和回访一致性，或仅靠自生成回访指标提升而独立深度无提升，GRC 的“未来几何价值”主张应停止。

## 2. MemRoPE: Training-Free Infinite Video Generation via Evolving Memory Tokens

**原始位置。** Kim et al., arXiv:2603.12513v1, 2026-03-12。摘要与方法见原文 Sec. 4（Memory Tokens、Online RoPE、Three-Tier Cache）；Algorithm 1（HTML 行 189--217）；实验协议见 Sec. 5.1（278--282）；局限见 Sec. 6（353--355）。

**机制与 GRC 的差别。** MemRoPE 把缓存的 key 以不带 RoPE 的形式保存，再在注意力时重加位置编码；双 EMA 汇总长、短期记忆，固定 sink/memory/local 三层缓存。它是训练无关的固定槽位内容压缩，不根据几何风险或未来答案选择历史，也不提供独立几何校准。其自身局限承认 EMA 对远距离内容是有损的，因此不能把“缓存稳定”直接解释为“未来几何正确”。

**必须加入的对照。** `MemRoPE`（双 EMA + 在线 RoPE）、`sliding/recent`、`random`，与 `confidence-only`、`coverage-only`、`pose-distance-only`、`risk-only`、`utility-only` 及 `risk+utility` 在相同槽位、相同 denoising、相同显存和相同历史预算下比较。单独报告几何指标与外观指标，避免 EMA 保持外观而几何恶化时被平均分掩盖。

**可推翻预测。** 若 risk+utility 在未见场景的未来几何误差不显著低于 MemRoPE/滑窗，或 risk 特征在 confidence/coverage 控制后没有增量解释力，则 GRC 不是已证实的选择机制；若只在单段已暴露场景有效，应降级为探索相关性。

## 3. FisherRF: Active View Selection and Mapping with Radiance Fields Using Fisher Information

**原始位置。** Jiang, Lei, Daniilidis, ECCV 2024；原文 Sec. 3.1--3.3（Fisher 信息、EIG、批量贪心）；官方代码仓库 README 的运行入口和依赖也已核对。原文明确：Fisher/Hessian 可不读取候选视图真实图像，批选择逐次更新 Hessian（Algorithm 1），并与 ActiveNeRF、Random、BayesRays 对比。

**机制与 GRC 的差别。** FisherRF 优化的是对 radiance-field 参数的期望信息增益，目标是主动采集新视角；GRC 是对已观测历史做风险校准、并预测未来世界状态收益。两者的“信息价值”不能互换：Fisher 高不代表历史几何可靠，也不代表未来深度误差低。GRC 若只写 `I(Y_future;H_S)` 而没有 Fisher/EIG 对照，审稿人可认为它只是换领域的 information-gain 复述。

**必须加入的对照。** `Fisher/EIG-proxy`（若不能运行完整 radiance field，必须明确为不可用或代理），以及 `random`、`pose-distance`、`coverage`、`confidence-only`。同时报告历史风险的校准曲线/risk--coverage、未来几何误差和固定预算收益，不能只报告选择后的最终 MSE。

**可推翻预测。** 若 Fisher/EIG 或 coverage 在相同预算下已经达到与 risk+utility 相同的未来几何收益，或 risk+utility 没有在 Fisher/coverage 之外带来增量，则 GRC 的“校准风险是必要机制”不成立，只能保留诊断协议。

## 审稿式结论（不是新颖性宣称）

本轮没有发现足以直接宣布 GRC 新颖性的“无人覆盖空白”。WorldTrace 已覆盖固定槽位和长时回访，MemRoPE 已覆盖固定缓存与动态位置，FisherRF 已覆盖信息增益式选择。GRC 仍可能形成**不同的问题设定**，但必须同时证明：

1. 选择对象是历史观测，而不是主动采集视角或单纯 KV 压缩；
2. 风险在校准集上预测独立未来几何答案，而不是只预测当前重投影或自生成回访；
3. risk+utility 在 confidence、coverage、pose、recent/random、Fisher/EIG（可运行时）和近邻 memory 方法之外有稳定增量；
4. 所有方法都使用相同历史数量、显存/CPU状态、推理时间和输出生成预算。

**当前闸门：** Gate 0 尚未通过，故不能运行正式 GRC-Pilot；上述对照和预测先冻结到协议。`new_method_validated=false`，`novelty_authorization=NONE`。

## 原始链接

- [WorldTrace 原文 HTML](https://arxiv.org/html/2608.07408v1)
- [MemRoPE 原文 HTML](https://arxiv.org/html/2603.12513v1)
- [FisherRF 原文 HTML](https://arxiv.org/html/2311.17874v2)
- [FisherRF 官方代码](https://github.com/JiangWenPL/FisherRF)
