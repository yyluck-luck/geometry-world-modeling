# 近邻原文核验矩阵（2026-09-11）

本轮针对用户点名的三个 arXiv 原文进行了定向阅读，不下载权重。结论只反映论文明确写出的机制与评价；没有写出的项目记为 `UNKNOWN`。这是近邻审查，不是新方法验证。

| 工作 | 历史选择/路由 | 几何 | 固定预算/成本 | 校准未来风险 | 与 GRC-Memory 的边界 |
|---|---|---|---|---|---|
| MemLearner, arXiv:2606.31734v1 | **YES（学习查询）**：Q tokens 从 C tokens 中按预测 P 自适应抽取；不是显式 top-k 帧选择。对照含 VMem、CaM、VRAG。 | 相机编码可选；方法查询本身“不依赖相机姿态”；没有显式几何风险分数。 | C 长度可到 9×P；早层查询、后层移除 C 等效率策略。是上下文长度/层数控制，非 GRC 的风险约束。 | **本轮已读范围未见** conformal/校准 expected-risk 控制；训练使用预测 token 的 diffusion loss，报告 GT/Revisit 的 PSNR、LPIPS、FID、FVD 与 fps。 | 已占据“为未来视频状态学习自适应历史记忆查询”高层问题。GRC 若只是把 learned query 换成 risk gate，近邻风险高；必须证明显式风险校准与可审计选择带来的独立可测增益。 |
| GIM-World, arXiv:2606.02436v1 | **YES**：历史预编码前按信息准则剪枝；保留子集 S，目标为 `I(S; H\\S)`，GP pose-time kernel，greedy 选取。 | **YES（训练时）**：camera-queryable geometry head，以冻结 VGGT 特征监督固定 memory；推理丢弃 geometry head/teacher。 | **YES**：memory 固定槽数；历史剪枝预算 K；作者称 greedy 对其 GP 子模目标近似最优。 | **本轮已读范围未见** conformal 校准或“未来风险上界”保证；几何损失是训练监督，评价为 MSE/LPIPS/PSNR/SSIM/RPE/reprojection 等。 | 与 GRC 的“几何、信息收益、固定预算”三者交集已直接重叠。本轮辨认出的潜在差异是：部署前可得的几何残差经过时间/场景校准，并直接预测 held-out future geometric loss；这尚未验证。 |
| ContextMaster, arXiv:2608.04956v1 | **YES**：query-dependent block-sparse routing；对 history/source 分开竞争，保留 reference/source 的 ConstraintSink。 | **PARTIAL/UNKNOWN**：论文使用 role-aware RoPE、source–target 时间对齐和上下文约束；本轮已读范围未见显式三维几何风险或深度真值。 | **YES（核心贡献）**：绝对 block budget B，目标每个 query 最多 B blocks；clean context KV cache 可复用；复杂度从随历史增长变为 `O(N_X B m D)`。 | **本轮已读范围未见** conformal 或 expected-risk 校准；论文使用 dense teacher→sparse student 的 privileged distillation 与 rollout matching。 | 固定预算、稀疏路由和未来生成消费已是直接先例；GRC 不能把“固定预算检索”单独作为新颖性。潜在差异须落在 geometry-risk calibration 与未来几何损失可证伪预测，并用相同预算/消费者公平比较。 |

## 原文证据定位

- MemLearner：§3.2–3.3 说明 Q→C/P 查询拓扑与早层查询；§4.1–5.2 给出数据、训练和 GT/Revisit 评价；附录 §0.C.10 明确比较 geometry-based VRAG。原文：[arXiv HTML](https://arxiv.org/html/2606.31734v1)。
- GIM-World：§3.3 Eq.14 是 camera-queryable VGGT feature cosine loss；§3.4 Eq.15–18 是 GP pose-time kernel、固定 K 剪枝与 greedy 信息准则；§3.5 Eq.19–20 是生成损失加几何监督。原文：[arXiv HTML](https://arxiv.org/html/2606.02436v1)。
- ContextMaster：§3.1 Eq.3 是 role-aware RoPE；§3.2 Eq.4–7 定义 cache、ConstraintSink 与固定 B routing，§3.2 明确稀疏读取复杂度与历史长度无关；§3.3 是 dense teacher 到 sparse student 的蒸馏。原文：[arXiv HTML](https://arxiv.org/html/2608.04956v1)。

## 审稿式结论

1. “历史记忆选择 + 几何信息 + 固定预算”不是空白：GIM-World 已把三者放进同一系统；ContextMaster 已把固定预算稀疏消费做成核心问题；MemLearner 已把未来状态驱动的自适应查询做成端到端机制。
2. GRC 的可检验差别不能写成“使用 uncertainty/conformal/MI”。必须先定义一个只依赖目标时刻以前信息的标量风险，按时间或场景隔离校准，再在同一选择规则下检验它是否预测独立未来几何损失，并与上述三类近邻及简单 pose/FOV/均匀基线公平比较。
3. 目前证据等级：**近邻边界已核验；GRC 新颖性 UNKNOWN；GRC 方法效果未验证；不授权 method/CCF-A 主张。**

## 题名与 arXiv 编号勘误

本轮核对到的 NVIDIA 页面对应 **Addressable Memory for Video World Models**，arXiv 编号为 **2608.07408**。经 root 复核，主综述 `docs/LITERATURE_SYNTHESIS_V2.md:36` 与 `CITATION_AUDIT.md:33/38` 原本已正确区分：`2512.15716` 为 Spatia，`2608.07408` 为 WorldTrace/Addressable Memory。此前的混写来自本轮 `pasted_claims_verify` 的阅读归因错误，不是历史主文档错误；现已更正。此勘误不改变本矩阵对三个点名近邻的判断。
