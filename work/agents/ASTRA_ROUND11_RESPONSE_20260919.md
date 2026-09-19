# Round 11 adversarial review

## Q1 — 占据结论

我确认“当前约束下关闭 axis (e)”这一停止判断；我没有确认“已用有限检索证明全领域占据”这种更强的普遍命题。

我对仓库的核对结果与这个判断相容。三份 pinned pipeline 的 SHA-256 都是 `90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e`，且逐字节一致。三处调用确实分别是 [pipeline.py:1249](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:1249>)、[pipeline.py:1263](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:1263>)、[pipeline.py:1265](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:1265>)。因此 target pose 同时进入检索查询和拼接后的相机归一化。关于 `self.c2ws`，准确表述是 line 180 初始化、line 1297 追加这两个写入/创建点；没有 setter 或 property，但 line 1360 还有 `pop()` 删除状态。这个小修正不改变双重混淆结论，却避免把“写入点”误写成“所有状态 mutation”。

能构成反驳的最强候选，是把方向定义成**相机条件证据边界下的因果状态/证据切空间**：先在冻结权重上区分“保持同一场景但修正可识别缺陷”的扰动，和“改变真实场景信息”的扰动；再看模型自身 rollout 的有限视界增益矩阵。这个方向不是天然等于频率方向，也不是梯度路线。频率是像素/时间坐标上的一组基；证据切空间由相机、历史帧和场景保持约束定义，通常是输入条件相关、非线性的。只有在额外假设存在固定可逆线性映射时，二者才可称作简单 reparameterization。因而你“state-space directions 必然只是 spectral directions 的重命名”这一理由过强。

但是这条逻辑缝仍不足以成为可辩护的方法差别：

1. 这只是一个待检验的区分。必须在训练前用冻结权重测量有限视界增益，并检验它是否有不能由频谱特征或梯度路线解释的残差。项目没有这项测量，也没有显示 pinned consumer 存在这样的残差；而这个 frozen probe 本身属于 owner 已排除的 measurement/evaluation 工作，不能偷偷把它当成方法贡献。
2. “固定 evidence-read graph”在这个 consumer 上不是无条件事实。改变 target pose 会改变 retrieval 和 `get_translation_scaling_factor` 的输入；若不先把这两条路径都封存，测到的是查询、归一化和生成器的混合效应。
3. 现有工作已经分别覆盖并组合了对象的主要语义：自回归误差纠正和有限 rollout 的 [BAgger: Backwards Aggregation for Mitigating Drift in Autoregressive Video Diffusion, arXiv:2512.12080](https://arxiv.org/abs/2512.12080), [VideoAR: Autoregressive Video Generation via Next-Frame & Scale Prediction, arXiv:2601.05966](https://arxiv.org/abs/2601.05966)；稳定性与运动/内容保留的 [Steady-Forcing: Balancing Spatial Persistence and Motion Continuity in Long-Horizon Nature Video Diffusion, arXiv:2606.14732](https://arxiv.org/abs/2606.14732)；频率选择性保持的 [FreqForcing: Autoregressive Long Video Generation via Spectral Self-Anchoring, arXiv:2607.27110](https://arxiv.org/abs/2607.27110)；长期积分的方向导数正则化的 [Jacobian Regularization Stabilizes Long-Term Integration of Neural Differential Equations, arXiv:2602.04608](https://arxiv.org/abs/2602.04608)；以及相机/几何条件下的场景一致性和静态—动态分解的 [Prisma-World: Camera-Controllable Multi-Agent Video World Model, arXiv:2606.09507](https://arxiv.org/abs/2606.09507)、[Matrix-Game 3.5: Enhancing Real-Time Streaming Interactive World Models with Patch Memory, arXiv:2608.29910](https://arxiv.org/abs/2608.29910)，以及直接把 state-space、autoregressive video 和长期 scene memory 放在一起的 [Long-Context State-Space Video World Models, arXiv:2505.20171](https://arxiv.org/abs/2505.20171)。

独立检索还找到更直接的 own-rollout 近邻：[Self Forcing: Bridging the Train-Test Gap in Autoregressive Video Diffusion, arXiv:2506.08009](https://arxiv.org/abs/2506.08009) 和 [Stable Video Infinity: Infinite-Length Video Generation with Error Recycling, arXiv:2510.09212](https://arxiv.org/abs/2510.09212)。前者把模型自身 rollout 纳入训练，后者把自生成误差回收为监督；二者都削弱“有限视界自身错误衰减”作为机制主张的独立性，尽管没有替本项目证明 state-space 版本完全相同。 关于你列出的 [Large Distant Gradients Need Not Be Reliable: reliability-weighted credit assignment for long-horizon autoregressive forecasting, arXiv:2609.12890](https://arxiv.org/abs/2609.12890)，本轮 export.arxiv API 的单篇抓取返回空结果；我因此把它视为你提供的线索，而不是本轮独立核验的支柱。即使把它完全剔除，前述已核实的 own-rollout、稳定性—运动、几何/相机和 state-space 近邻仍足以关闭当前方法主张。

这些引用不能单独证明“任何状态空间版本都已被做过”。它们足以说明：要把本项目版本称为新方法，必须先给出冻结权重上的、证据边界受控的、非频谱且非梯度路线的方向性差异；目前没有。故我不推翻关闭判断。

## Q2 — 搜索失败模式审计

原搜索对“稳定性—运动—保留敏感性—自身 rollout”这组表面词很强，但对“区分机制”的词族不够宽。它足以支持一个项目停止决定，却不足以支持严格的普遍命题“该合取已被全领域占据”。我实际用 arXiv API 做了以下补搜，结果说明遗漏确实有内容：

- **exposure bias / teacher forcing / free-running / scheduled sampling / corrective trajectories**。这些词会找到 [Scheduled Sampling for Sequence Prediction with Recurrent Neural Networks, arXiv:1506.03099](https://arxiv.org/abs/1506.03099)、[Professor Forcing: A New Algorithm for Training Recurrent Networks, arXiv:1610.09038](https://arxiv.org/abs/1610.09038) 和 [A Reduction of Imitation Learning and Structured Prediction to No-Regret Online Learning, arXiv:1011.0686](https://arxiv.org/abs/1011.0686)。它们不等于本项目的方法，但会提前暴露“自身 rollout 训练”并非新措辞。
- **cross-frame error correction / self-rollout correction / next-frame error propagation**。这组检索直接返回 [VideoAR: Autoregressive Video Generation via Next-Frame & Scale Prediction, arXiv:2601.05966](https://arxiv.org/abs/2601.05966)，其摘要明确把 Cross-Frame Error Correction 作为长期一致性机制；它应当在第一次占据审查时出现。
- **directional stability / anisotropic contraction / Koopman residual compensation / Lyapunov / controllability / observability / singular-vector sensitivity**。这组词会找到 [A Compensated Koopman Neural Operator with Selective State-Space Dynamics for Unsteady Flows, arXiv:2608.25879](https://arxiv.org/abs/2608.25879) 和上面的 Jacobian 正则化论文。它们不是 camera-conditioned video，但正好检验“state-space directional gain 是否只是频谱或梯度路线”的区分，不能省略。
- **camera-conditioned / view-conditioned / shared-scene evidence / cross-view consistency / static-dynamic disentanglement**。这组词返回 [Prisma-World: Camera-Controllable Multi-Agent Video World Model, arXiv:2606.09507](https://arxiv.org/abs/2606.09507) 和 [Matrix-Game 3.5: Enhancing Real-Time Streaming Interactive World Models with Patch Memory, arXiv:2608.29910](https://arxiv.org/abs/2608.29910)。它们直接触及“固定相机条件证据边界”而不是只讨论频带。
- **camera trajectory + 4D geometry + self-forcing / revisit / loop closure / historical retention**。这组词会返回 [Geometry-as-context: Modulating Explicit 3D in Scene-consistent Video Generation to Geometry Context, arXiv:2602.21929](https://arxiv.org/abs/2602.21929)、[MV-Forcing: Long Multi-View Video Generation via 4D-Grounded Spatio-Temporal Self-Forcing, arXiv:2607.05376](https://arxiv.org/abs/2607.05376)、[Closing the Loop: Training-Free Revisit Consistency for Autoregressive Generative Rendering, arXiv:2607.21848](https://arxiv.org/abs/2607.21848) 和 [Memorize-and-Generate: Towards Long-Term Consistency in Real-Time Video Generation, arXiv:2512.18741](https://arxiv.org/abs/2512.18741)。这正是原查询最可能漏掉的“固定相机证据边界 + 场景保留”近邻。
- **scene identity/content retention after stabilization / motion-preserving stabilization / counterfactual scene sensitivity**。这组词应与 stability、long-horizon、autoregressive、world model 交叉，并沿每篇 seed 做 citation chaining；原检索主要从“error gain”反向查，容易漏掉以 identity、geometry、subject consistency 命名的同一问题。还应加入 [Relax Forcing: Relaxed KV-Memory for Consistent Long Video Generation, arXiv:2603.21366](https://arxiv.org/abs/2603.21366) 这类按记忆角色选择历史、同时保留运动的标题族。
- **检索范围和证据来源**。还应查 CVPR、ICLR、NeurIPS 正式论文及 workshop 版本，做 title/abstract/引用链回溯，而不是只查一组近似短语。正面占据命题被一篇反例即可推翻，所以不能把“我没有搜到”升级成穷尽证明。

因此，Q2 的准确结论是：搜索存在确认偏差，不能为全领域的 OCCUPIED 定理背书；但补搜没有发现一个同时满足“非频谱、非梯度路线、固定相机证据边界、冻结权重可先验检查、并且已经形成可训练方法主张”的反例。结合 Q1 的缺失测量，停止 axis (e) 仍然是正确的项目决策。

## Q3 — 终止交付物

在当前约束下，没有可供提交的方法论文。

诚实的终止交付物只能是一份**冻结生成器的可复核诊断/取证技术报告**，记录检索器状态泄漏、查询—归一化双重混淆、有限 panel 上的上下文对照、重复槽位修复失败及其适用边界；它不能被包装成方法贡献，也不能被改名为 owner 已排除的 measurement/evaluation 贡献。

现有数字应原样保留并带证据等级：

- order-invariance gate 是 retrieval 状态顺序的 11/11 PASS，含 non-vacuity；它是软件/协议有效性证据，不是方法收益。
- leak census 是 NULL 2、PERMUTATION 4、CONTENT 8，slot 0 在 14/14 中不变；NULL 的 4/4 byte-identity gate 说明该层是输入相同，不是生成改进。
- 在同一 14-window paired panel 上，`nms_off - static = +0.242 dB`，SD 1.270，8/14 为正；`nms_on_clean - static = -0.485 dB`；`nms_on_clean - nms_off = -0.726 dB`。这是有限、暴露开发序列上的 RGB PSNR 结果，不是 held-out 泛化，也不是方法验证。
- leak 分层为 NULL +0.000、PERMUTATION -0.015、CONTENT +0.436 dB。它说明不同输入差异层级的影响不相同，不能单独推出训练方向。
- 重复槽位的预声明修复门槛为 +0.20 dB；in-place 修复实测 -0.016 dB，且只覆盖 10 个受影响窗口中的 8 个，另 2 个没有符合预声明策略的第四个 distinct candidate；no-op 控制通过 8 个 byte-identical executions。该分支已经按规则 discarded，不能事后改门槛或改候选规则。

报告应明确引用 [TECHNICAL_REPORT_20260918.md](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/report/TECHNICAL_REPORT_20260918.md>) 的结果表和修正记录，并保留 `new_method_validated=false`、`novelty_authorization=NONE`。不应安排新的训练、fine-tuning、GPU 生成或以“先测再决定”为名的 800 GPU-hour 恢复。

## Q4 — 裁定

**END-LINE**

