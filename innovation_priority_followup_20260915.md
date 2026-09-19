# 2025–2026 近期近邻补检：未来状态效用与几何记忆选择

实际检索时间：2026-09-15（Asia/Shanghai）。本轮使用 arXiv、NeurIPS proceedings 和 OpenReview 原文页面；搜索词覆盖 `future-state utility prediction`, `geometric memory selection`, `long-horizon world model memory`, `loop closure memory retrieval`。本报告只补充新近邻核验，不代表完整系统综述。

## 结论

没有找到一篇与本项目完全相同、明确用“历史可见几何风险预测未来 RGB-D/位姿损失差，并在固定真实记忆预算下进行选择”的论文。因此该**精确问题设置仍可作为候选研究问题**。但近期工作已经覆盖了其中的多个组成部分，创新门槛比 S100 之前更高：几何长期记忆、几何帧稀疏选择、重访评测、锚定投影记忆和几何位置编码都已有先例。

## 直接近邻与差异

### 1. Geometry-Aware Rotary Position Embedding / ViewRope（arXiv:2602.07854，2026 预印本）

原文明确提出用每个 patch 的相机射线关系注入注意力，并用 Geometry-Aware Frame-Sparse Attention 选择历史帧。原文方法段给出：帧块相关性由几何注意力估计，固定 top-k 历史帧；实验还做了 random selection 和 exclude-selected 的反事实对照。来源：[arXiv 原文](https://arxiv.org/abs/2602.07854)，方法细节见原文 §3.2–3.3、结果 §4.3。

这是当前最强的“几何条件历史选择”近邻。它选择的是注意力中的历史**帧**，分数来自射线几何和模型内部 affinity；它没有在选择阶段以未来 GT 深度/位姿损失训练一个风险预报器，也没有证明历史风险分数对未来有符号效用差具有跨场景校准。因此，本项目不能把“几何选择历史”作为新意，只能继续检验更窄的未来状态效用预测问题。

### 2. Video World Models with Long-term Spatial Memory（NeurIPS 2025）

NeurIPS 正式页面确认该工作使用 geometry-grounded long-term spatial memory，包含存储和检索机制，并构造数据来评价长时空间一致性。[NeurIPS 正式页面](https://proceedings.neurips.cc/paper_files/paper/2025/hash/467655d26fcc207bca08915dc91964c6-Abstract-Conference.html)

它直接覆盖 proposal 中的长期空间记忆和重访一致性目标，但公开摘要没有显示“逐候选未来效用预测”或固定真实槽位下风险校准选择。因而它是必须比较的强基线，不能被描述为尚未有人做长期几何记忆。

### 3. Addressable Memory for Video World Models / WorldTrace（arXiv:2608.07408，2026 预印本）

原文把长时记忆失败归因于超出训练范围的 RoPE 地址，并提出把压缩槽位放回训练分布内的虚拟位置；同时提出 Field/Landmark 两种压缩策略和 LoopBench 重访基准。[arXiv 原文](https://arxiv.org/abs/2608.07408)

该工作优化的是**可寻址性与压缩位置**，不是几何风险对未来深度/位姿损失的预测。它会迫使本项目增加“地址/可检索性”基线，否则风险选择器的任何收益可能只是改善了读出地址而非几何判断。

### 4. MIND（arXiv:2602.08025，2026 基准预印本）与 MemoBench（ECCV 2026 页面）

MIND 提供闭环重访、动作控制和多场景评测，包含 250 个高质量视频、八类场景及不同动作空间。[MIND 原文](https://arxiv.org/abs/2602.08025)

MemoBench 采用 disappear-and-reappear 范式评价动态环境中的记忆一致性。[项目页](https://memobench-team.github.io/)

两者主要是评价/基准，而不是未来效用选择方法。它们提示 proposal 的 H3 必须使用重访、遮挡后重现和动态变化，不能只在静态投影消费者上验收。由于这些数据的许可、相机/深度配对和可复现实验入口仍需逐项核验，当前不把项目自动迁移到这些基准。

### 5. EgoGenesis（arXiv:2607.28243，2026 预印本）与 PAIWorld（arXiv:2606.18375，2026 预印本）

EgoGenesis 提出 Online Anchored Projective Memory：保持首帧 3D anchor，并在线刷新近期状态；同时使用 Action-3D RoPE。[EgoGenesis 原文](https://arxiv.org/abs/2607.28243)

PAIWorld 使用几何跨视角注意力、几何 RoPE 和 3D 特征蒸馏来做机器人操作世界模型。[PAIWorld 原文](https://arxiv.org/abs/2606.18375)

这些工作说明“锚点+近期状态”“几何 cross-view attention”“几何 RoPE”均已有近期先例。它们没有被本轮证实使用历史候选的未来 GT 效用预报；但会成为完整生成消费者实验中的强方法或架构参照。

## 对 GRC-Memory 的审稿影响

本轮补检后，以下表述应明确停止：

- “首次根据几何关系选择历史记忆”；ViewRope 已直接覆盖。
- “首次使用长期几何记忆改善重访”；NeurIPS 2025、WorldTrace 等已覆盖。
- “首次做记忆替换的反事实评估”；S100 既有 CUE-R 类方法学近邻，ViewRope 也报告了排除所选帧的反事实实验。

仍可保留的窄问题是：

> 在真实 RGB-D/位姿序列中，部署时可见的历史风险特征，能否在固定槽位与端到端计算预算下，预报每次候选保留/替换对**未来状态损失的有符号影响**，并在未见场景超过 confidence、recent、coverage、pose、几何 affinity 和 WorldTrace/GIM 风格选择？

这不是“把未来 GT 放进 selector”。未来 GT 只用于预测封存后的评分；selector 的风险模型必须冻结于过去信息和训练/校准划分。

## 新增判定标准

只有同时满足以下条件，才有资格重新申请方法新颖性审查：

1. 在至少两个完全未用于选择或调参的 RGB-D/位姿场景上，风险预报在预注册指标中优于 confidence、recent、coverage、pose、geometry-affinity 和随机选择。
2. 预算按真实记忆槽位、token/显存和端到端推理时间计量；不能用 source-block 改写数量代替 `k`。
3. 主结果包括未来完整 GT 域的深度/位姿误差、遮挡重访误差、RGB 质量、覆盖率和尾部误差；不是只报 MSE 或一次 capped AbsRel。
4. 至少一个反事实替换或排除实验表明收益不是由更多计算、不同候选池、地址可寻址性或覆盖率变化造成。
5. 所有失败分支保留：若风险预报不优于简单基线，主张必须停止，GRC 退回诊断性分析。

## 检索限制

本轮核验了上述论文的 arXiv/正式会议正文可访问部分；没有声称下载或复现所有官方代码，也没有把第三方论文摘要或项目页当作完整实现证据。ViewRope 的原文为 2026 预印本，NeurIPS 工作有正式 proceedings 页面；MIND、EgoGenesis、PAIWorld 和 WorldTrace 在本轮按预印本状态记录。没有找到可直接证明“未来几何效用预测选择”已经被完整实现的近邻，但这只是定向检索结论，不是全领域无重复证明。

**状态保持：** `new_method_validated=false`，`novelty_authorization=NONE`。本轮新检索的价值是收紧创新主张并增加必须比较的强基线，而不是提前宣布 GRC-Memory 成立。
