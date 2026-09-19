# GeoCausal Memory Contract：Benchmark 论文范围审计

- 审计日期：2026-09-08（Asia/Shanghai）
- 暂定任务名：**GeoCausal-Mem Audit**
- 论文定位：显式检索式视频世界模型的来源级因果诊断与评测
- 当前状态：范围锁定草案；不是已建成 benchmark，不是投稿稿件

## Step 1: Five-pillar completeness table

| Pillar | Covered? | Your content | Improvement suggestion |
|---|---|---|---|
| Research Gap | **Y，待实证加固** | 现有工作分别评测长期记忆、重访质量、几何检索、注意力或模块收益，但这些结果不能逐条证明 Store → Select → Address → Influence → Localization → Benefit。 | 用 C1/C2 的一个自然失败做 Figure 1：记忆被选中且可寻址，却没有超过控制的作用、在错误区域起作用或带来负收益。若找不到这种实例，撤销 gap。 |
| Construction Pipeline | **N** | 只有候选方案：从自然失败开始，再做同身份、同几何的低强度外观干预、matched zero-edit 和 exact replay；尚无已运行流水线、规模和质量门结果。 | 采用“自然种子 + controlled injection”：来源冻结 → replay 稳定性 → 每sign的edit/zero直接pair → 全路径一致性检查 → geometry support/placebo → 人/自动质量复核 → 分层划分。先做一个CAL source的pilot，再定规模。 |
| Evaluation Framework | **Y，未验证** | 六阶段 taxonomy；A0、F00/F10/F01/F11；每family/seed/sign的matched direct pair；Influence、Localization、Benefit顺序门；后续可用AURC/risk–coverage。 | 让V5 normative spec/reference implementation通过fresh review；验证geometry support与人工区域判断的一致性；避免只报告热图。 |
| Empirical Findings | **N** | 当前只有基线工程证据与近邻文献压力测试；没有 GeoCausal 实验结果。 | 至少形成三类可复核 Finding：失效发生在哪一阶段、因果效应是否空间正确、因果分数是否在普通 proxy 之外预测自然收益。 |
| Companion Method | **NA，当前不做** | 接受/拒绝/重新观察是后续候选；现在没有训练信号和有效性证据。 | 只有 causal score 存在稳定 oracle headroom 后，才训练轻量接受器；否则保持为诊断 benchmark。 |

五支柱结论：**Research Gap 和 Evaluation Framework 有骨架；Construction Pipeline 与 Empirical Findings 仍为空。** 当前最有价值的工作是 kill experiment，不是先扩充网络结构。

## Step 2: Introduction six-part logic chain

| Part | Your content |
|---|---|
| 1. Background + Running Example | 长视频世界模型在离开后重访场景时容易改变旧环境。Figure 1 应展示同一次普通运行中：某条历史来源被存储、检索并寻址，但输出变化是否真的来自它、发生在何处、是否有益仍未知。 |
| 2. Existing-benchmark limitations (up to 3) | **Limitation 1：** 重访 PSNR/LPIPS 等系统平均分不能指出具体来源是否被消费。 **Limitation 2：** attention、retention 或模块 ablation 不能证明单来源的全路径 total effect。 **Limitation 3：** 即使有因果效应，也可能落在错误空间区域或不能预测自然质量。 |
| 3. Research Questions | **RQ1：** 显式记忆失败主要发生在 Store、Select、Address、Influence、Localization、Benefit 的哪一段？ **RQ2：** 全路径一致的单来源`edit−matched zero-edit`直接效应是否超过exact replay/negative并集中在干预前几何支持区？ **RQ3：** 该分数能否在attention、pose overlap、retrieval score等普通proxy之外预测自然重访错误或收益？ |
| 4. Design Considerations | 来源必须来自普通未干预运行；编辑保持 source ID 与几何；只匹配干预前外生量与非目标初态；所有目标来源后代重算；F10/F01 只诊断路径冲突；自然失败与合成注入分开报告。 |
| 5. Our Proposal | 构建来源级六阶段审计协议和一个从自然重访种子派生的可复现 controlled-injection 集合，输出阶段标签、全路径 causal effect、geometry localization 与 benefit/accept 风险曲线。 |
| 6. Contributions | **当前只能作为条件式目标：** 1) 六阶段证据 taxonomy；2) 保持来源身份与几何的全路径干预流水线；3) 多模型、分阶段的实证边界；4) 若存在 headroom，再提供接受/重观察基线。没有数据前不得在论文中写成已完成贡献。 |

## Step 3: Section outline for §2 to §7

### §2 Gap and benchmark definition

明确 in-scope：具有稳定 source ID、能列出全部真实消费路径的显式检索式视频世界模型；自然重访；来源级因果、空间局部和效用。明确 out-of-scope：无法追踪来源的纯隐状态模型、一般视频美学、物理常识全覆盖和训练数据记忆。**Table 1** 比较至少 SPMEM、Long-Context SSM、WorldTrace、WorldKV、CaR、DensityKV、GIM-World、Matrix-Game 3.5、Echo-Memory、TetherCache 与本协议的六阶段覆盖。

### §3 Construction pipeline

采用“自然种子 + controlled injection”。阶段为：普通运行采集 → 盲质量评分 → 稳定自然失败筛选 → source与全部消费路径冻结 → exact replay → 每个family/seed/sign的低强度edit和同流程zero-edit → matched negative/positive → 全路径一致性与后代重算检查 → support/placebo/quality标签 → 分层拆分。**Figure 2** 画一条样本的完整流转，并在每一步标注输入、输出、失败回执和实际样本数量。当前数量未知，不能预填。

### §4 Evaluation framework

按六阶段给每个样本状态；主比较仅每个sign的`F11-edit−matched F11-zero`，F00用于replay/sham管线诊断，`F10/F01`各配matched-zero并只用于发现路径冲突。指标包括control-calibrated direct effect、control-excess map相对真实support与三族placebo的局部性、以及自然error/Benefit的样本外增量预测；若做拒绝决策，加入AURC、risk–coverage、clean false rejection与总体paired loss。**Figure 3** 是来源到区域的因果效应图；**Table 2** 给公式、范围、自动化程度和人工校验。

### §5 Experiments by RQ

RQ1 报各阶段失败比例；RQ2 报 exact replay、因果和局部性；RQ3 比较 causal score 与 attention、pose overlap、retrieval score、简单 gate、addressability 修复、selection/repair 近邻。跨场景、多来源、多种子，并至少覆盖第二个可审计架构。**Table 3** 是最大总表；每一节只有数据支持时才写 **Finding X**。

### §6 Discussion and research opportunities

讨论何时“保存但不可寻址”“寻址但不消费”“消费但空间错误”“局部正确但无益”。把未通过的阶段当能力边界，不把负结果藏起来。研究机会包括 source-aware tracing、几何一致的记忆编辑和带风险控制的 re-observe。

### §7 Related work

按长期视频记忆、KV/显式检索、几何记忆、因果干预、选择性预测五类组织。使用同一张六阶段对照表，逐项说明对象、粒度、干预机制与任务设置的不同，不用“未搜到”证明新颖性。

## Step 4: Pre-submission self-check

**Pre-submission Verdict：NOT READY**

### Critical issues

1. 没有已经验证的自然失败 running example，Figure 1 不成立。
2. 没有运行过的 construction pipeline、样本规模、数据统计或 Figure 2。
3. 没有 GeoCausal empirical findings，不能写 Finding 1/2/3。
4. 没有覆盖多个强基线和至少第二个可审计架构的总结果表。
5. 没有人工/自动区域与质量标签的一致性证据。

### Major issues

1. 六阶段 taxonomy 是有理据的设计，尚未由数据证明能区分实际系统。
2. C1仍缺数值相机守卫/盲评分，C2尚未生成；现有真实生成不能作为候选方法收益。
3. 数据许可、拆分、污染控制、发布格式和维护计划尚未定义。
4. 多种子统计、置信区间和功效预算尚未由 pilot 方差确定。
5. 完整跨模型实验超出当前本机资源，应先用单模型 kill experiment 判断是否值得申请 GPU 或合作。

### 当前设计目标

| Goal | Strategy now | Gate before claiming completion |
|---|---|---|
| G1 Coverage | 六阶段 × 自然失败类型 × 场景/来源分层 | 至少两个可审计架构和多个独立场景；数量由 pilot 决定 |
| G2 Fine-grained diagnostics | source-level causal effect + pre-treatment geometry support + benefit | 三道门均有冻结公式和不确定性区间 |
| G3 Scalability | 日志自动抽 source、自动 replay/干预/支持区计算 | 每样本成本和失败率实测，人工只审难例 |
| G4 Quality | 哈希绑定、同源全路径检查、独立复核、盲质量评分 | 有结构化失败回执、区域/质量人工一致性和复现实验 |

## 从顶会工作提炼出的创新执行规则

1. **像 WorldModelBench 一样，先证明旧指标漏掉了重要能力，再建新评测。** 不能因为指标更细就自动有贡献。
2. **像 SPMEM 一样，把几何记忆、数据和真实重访评测连起来。** 但本项目的差异应落在来源级因果证据，而不是再做一个普通几何记忆模块。
3. **吸取 ICLR 2024 activation patching 反例：有端到端变化仍可能来自休眠旁路。** 所以要做 all-path、后代重算、F10/F01 冲突诊断与 exact replay。
4. **接受/拒绝必须沿用 ICML selective prediction 的 risk–coverage 规范。** 只展示过滤后样本更好会产生选择偏差，不能作为有效方法结论。
5. **Dual-Granularity Memory 已占据“双记忆”架构叙事。** PC-DPM只有在同一source跨consumer provenance失配被反事实识别，并优于容量匹配token/geometry/context基线时才保留方法差别。

## 一手来源

- [SPMEM / NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/467655d26fcc207bca08915dc91964c6-Abstract-Conference.html)
- [WorldModelBench / NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/4ec03ed08a3fcb59e1c815b5598beff1-Abstract-Datasets_and_Benchmarks_Track.html)
- [Long-Context State-Space Video World Models / ICCV 2025](https://openaccess.thecvf.com/content/ICCV2025/html/Po_Long-Context_State-Space_Video_World_Models_ICCV_2025_paper.html)
- [Dual-Granularity Memory / CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Wang_Dual-Granularity_Memory_for_Efficient_Video_Generation_CVPR_2026_paper.html)
- [Is This the Subspace You Are Looking for? / ICLR 2024](https://openreview.net/forum?id=Ebt7JgMHv1)
- [SelectiveNet / ICML 2019](https://proceedings.mlr.press/v97/geifman19a)
- [WorldTrace](https://arxiv.org/abs/2608.07408)
- [WorldKV](https://arxiv.org/abs/2605.22718)
- [CaR](https://arxiv.org/abs/2606.23105)
- [DensityKV](https://arxiv.org/abs/2608.27922)
- [GIM-World](https://arxiv.org/abs/2606.02436)
- [Matrix-Game 3.5](https://arxiv.org/abs/2608.29910)
- [Echo-Memory](https://arxiv.org/abs/2606.09803)
- [TetherCache](https://arxiv.org/abs/2606.13035)
- [CUE-R](https://arxiv.org/abs/2604.05467)
