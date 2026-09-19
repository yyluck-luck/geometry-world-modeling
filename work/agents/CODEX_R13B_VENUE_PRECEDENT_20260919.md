# Round 13-B：诊断 / forensic 贡献的发表先例、门槛与 venue 现实

日期：2026-09-19  
范围：公开论文先例与本项目已有证据的对照。本文不提出新方法，不作资助判断，也不把诊断证据写成方法创新。

## Q5 先给负面答案

按现有材料，即使把“贡献必须是 method”这一约束放宽，本项目现在也**不能被称为已经达到可发表的 diagnostic / forensic contribution 门槛**。现有证据足以支持“一个冻结的 VMem consumer 中存在可复现的跨调用状态依赖，并在一个暴露的开发 panel 上量化了它的影响”这一单系统 forensic case study；它还没有达到已发表先例中反复出现的更高门槛：跨系统或跨任务的外部效度、独立或 held-out 验证、对已发表结论或排名的明确影响，以及可被其他系统采用并复核的通用检查。

这个判断不是说材料没有价值，也不是说未来逻辑上不可能发表。它表示：若要把当前报告推进到 TMLR、NeurIPS 的 reproducibility / evaluation 路线，或 main conference 的诊断论文，所需的是新的证据层，而不是在同一 14-window panel 上再加若干 seeds。若不补足这些证据，较诚实的归类是内部技术报告、窄范围复现/审计稿，或专门的 reproducibility venue 候选。

## 证据边界：仓库中实际核对到的内容

我直接核对了三份 pinned VMem source：

- work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py
- work/S17_cpu_preflight/original/modeling/pipeline.py
- work/S102_gate0_3dmatch/adapter_v1/sources/vmem_pipeline.py

三份文件 byte-identical，sha256 均为 90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e。三份文件的相同行号是：

- line 1249：get_context_info(target_c2ws, use_non_maximum_suppression)；
- line 1263：torch.cat([context_c2ws, target_c2ws])；
- line 1265：get_translation_scaling_factor(all_c2ws)。

这支持“目标位姿同时进入检索和相机归一化”这一 source-level confound：改变 target_c2ws 会同时改变检索内容和 normalization path，不能把 query-side intervention 直接解释为单一检索效应。

self.c2ws 的准确表述是“两处写入/创建、无 setter、另有一处成组删除”：line 180 初始化，line 1297 append，line 1360 在 undo_latest_move() 中与其他状态一起 pop。因此不能写成“所有 mutation 只有两个 site”；但仍没有能保留同一帧内容而只改相机标签的 setter。initial_threshold 的 NMS-off 写入、NMS-on 的条件写入、以及 reset() 不清除该字段，均与报告中的源码审计一致。

docs/report/TECHNICAL_REPORT_20260918.md 给出的实验边界也已核对：

- 数据是 RGB-D Scenes v2 scene_13、scene_14 的两个暴露 development sequences；14 个固定 windows，2 个 seeds，one dependency group，one frozen consumer；这些不是 independent held-out evaluation data。
- metric 只有 RGB PSNR，没有 geometry、perceptual 或 human metric。
- pre-scoring census 为 NULL 2 / PERMUTATION 4 / CONTENT 8，slot 0 为 14/14 invariant；NULL 的 4 个 window-seed 输出经 SHA-256 byte identity gate 验证。
- order-invariance gate 是 11/11，包含 non-vacuity check；它覆盖的是 retrieval selection 的执行顺序，不是生成输出对 context slot order 的普遍不变性。
- nms_on_clean − nms_on(leaked) = +0.245 dB，SD 0.711，6/14；分层为 NULL +0.000（n=2）、PERMUTATION −0.015（n=4）、CONTENT +0.436（n=8），这些分层数字分解的是这个 clean-vs-leaked estimand。
- 另一项 nms_off − static = +0.242 dB，SD 1.270；repair 的 inplace − memory_nms_off = −0.016 dB，SD 0.309。所以“SD 约为均值 5 倍”只近似适用于 +0.242 / 1.270 这一行（约 5.25 倍），不适用于所有 contrast；+0.245 / 0.711 约 2.9 倍，−0.016 / 0.309 约 19.3 倍。
- pre-declared +0.20 dB repair criterion 未达到：8/10 可实例化 affected windows 上为 −0.016 dB，因此该 repair explanation 已按预先规则 discarded。
- 报告明确说该 panel 没有 revisitation，因此没有 reproduces、tests 或 contradicts VMem paper 的 revisitation experiment；不能把本 panel 的绝对 PSNR 当作对原论文 headline claim 的反驳。

这些是本报告使用的事实层；“诊断性可发表”是与外部 precedent 的比较，不是从仓库事实自动推出的标签。

## Q1：已发表的 diagnostic / forensic / analytical 先例

检索跨越 deep RL、benchmark uncertainty、metric critique、retrieval/recommendation reproducibility、data contamination、ML-for-health、语言生成评估和 computer vision evaluation。下表保留 arXiv ID、arXiv 的 exact title，以及可核对的 venue/year。每行最后一句只说明论文的主要诊断形式。

### 主会或期刊中、诊断本身是主要贡献的先例

| arXiv ID 与 exact title | Venue / year | 主要贡献形式 |
|---|---|---|
| [arXiv:1709.06560 — “Deep Reinforcement Learning that Matters”](https://arxiv.org/abs/1709.06560) | AAAI 2018 Technical Track: Machine Learning（AAAI 页面将 venue title 的 “That” 大写）[[AAAI]](https://ojs.aaai.org/index.php/AAAI/article/view/11694) | 对多个 published deep-RL 实验重新测量 seed、metric、baseline 与 reporting variability，指出结论对实验协议敏感，并给出报告规范；属于 reproducibility failure + protocol/reporting flaw。 |
| [arXiv:2005.12729 — “Implementation Matters in Deep Policy Gradients: A Case Study on PPO and TRPO”](https://arxiv.org/abs/2005.12729) | ICLR 2020；官方 poster 使用 accepted-title variant “Implementation Matters in Deep RL: A Case Study on PPO and TRPO” [[ICLR]](https://iclr.cc/virtual_2020/poster_r1etN1rtPB) | 对 released PPO/TRPO implementations 做 code-level attribution audit，发现优化细节而非算法名本身解释了大部分性能差异；属于 hidden implementation dependency + conclusion attribution。 |
| [arXiv:2006.05990 — “What Matters In On-Policy Reinforcement Learning? A Large-Scale Empirical Study”](https://arxiv.org/abs/2006.05990) | ICLR 2021（ICLR 页面有 title variant “What Matters for On-Policy Deep Actor-Critic Methods? A Large-Scale Study”）[[ICLR]](https://iclr.cc/virtual/2021/papers.html) | 用 50+ implementation choices、5 个环境和超过 250,000 agents 分析已有 on-policy RL 实践；不是新 learner，而是大规模 implementation/evaluation diagnosis。 |
| [arXiv:2108.13264 — “Deep Reinforcement Learning at the Edge of the Statistical Precipice”](https://arxiv.org/abs/2108.13264) | NeurIPS 2021 [[proceedings]](https://proceedings.neurips.cc/paper_files/paper/2021/file/f514cec81cb148559cf475e7426eed5e-Paper.pdf) | 在 Atari-100k/ALE、Procgen、DM Control 上显示少量 runs 的 point estimate 会误导 benchmark ranking，扩展到 uncertainty-aware evaluation 与可复用的 rliable tooling；属于 benchmark invalidation + adoptable test/library。 |
| [arXiv:2310.17867 — “Reproducibility in Multiple Instance Learning: A Case For Algorithmic Unit Tests”](https://arxiv.org/abs/2310.17867) | NeurIPS 2023 [[NeurIPS]](https://papers.neurips.cc/paper_files/paper/2023/hash/2bab8865fa4511e445767e3750b2b5ac-Abstract-Conference.html) | 用 model-agnostic synthetic unit tests 检查 5 个 prominent deep-MIL models 是否满足标准 MIL assumption，发现全部存在违反；属于 hidden-assumption defect + 可迁移的 unit-test protocol。 |
| [arXiv:2006.06264 — “Tangled up in BLEU: Reevaluating the Evaluation of Automatic Machine Translation Evaluation Metrics”](https://arxiv.org/abs/2006.06264) | ACL 2020 main [[ACL Anthology]](https://aclanthology.org/2020.acl-main.448/) | 证明 translation sample/outlier 选择会改变 BLEU 等 metric 的 pairwise ranking 与置信判断，并给出 protocol safeguards；属于 evaluation-protocol / metric flaw + effect quantification。 |
| [arXiv:2104.11222 — “On Aliased Resizing and Surprising Subtleties in GAN Evaluation”](https://arxiv.org/abs/2104.11222) | CVPR 2022 [[CVPR]](https://openaccess.thecvf.com/content/CVPR2022/papers/Parmar_On_Aliased_Resizing_and_Surprising_Subtleties_in_GAN_Evaluation_CVPR_2022_paper.pdf) | 显示 resize、anti-aliasing 和 JPEG preprocessing 会大幅改变 FID，并发布建议与 reference implementation；属于 protocol/implementation flaw + 影响量化。 |
| [arXiv:2306.04675 — “Exposing flaws of generative model evaluation metrics and their unfair treatment of diffusion models”](https://arxiv.org/abs/2306.04675) | NeurIPS 2023 [[NeurIPS]](https://papers.neurips.cc/paper_files/paper/2023/hash/0bc795afae289ed465a65a3b4b1f4eb7-Abstract-Conference.html) | 跨 17 个 metrics 和 human experiment 检查 metric-human disagreement 及对 diffusion models 的不公平；属于 benchmark/metric invalidation + cross-model stress test。 |
| [arXiv:1911.07698 — “A Troubling Analysis of Reproducibility and Progress in Recommender Systems Research”](https://arxiv.org/abs/1911.07698) | ACM TOIS 39(2), 2021 [[DBLP]](https://dblp.org/rec/journals/tois/DacremaBCJ21.html) | 扫描 26 篇 recommender papers，实际复现 12 篇，发现 11/12 neural approaches 被简单 baseline 超过；属于 reproduction failure + baseline/protocol critique。 |
| [arXiv:2503.07823 — “Reproducibility and Artifact Consistency of the SIGIR 2022 Recommender Systems Papers Based on Message Passing”](https://arxiv.org/abs/2503.07823) | ACM TOIS 44(1), 2025，DOI [10.1145/3772275](https://doi.org/10.1145/3772275) | 审计 10 篇 graph-based recommender papers，发现错误 split、train-test leakage、paper/artifact 不一致和偏弱 baseline，导致多数 claims 无法确认；属于 multi-paper forensic audit + benchmark invalidation。 |
| [arXiv:2207.07048 — “Leakage and the Reproducibility Crisis in ML-based Science”](https://arxiv.org/abs/2207.07048) | Patterns 4(9), 2023，published title 为 “Leakage and the reproducibility crisis in machine-learning-based science” [[PMC]](https://pmc.ncbi.nlm.nih.gov/articles/PMC10499856/) | 跨 17 个领域、294 篇论文建立 8 类 leakage taxonomy，并用 reproduction case 展示 leakage 如何消除复杂模型相对简单模型的优势；属于 leakage audit + reproduction failure + general reporting artifact。 |
| [arXiv:2212.10020 — “On the Blind Spots of Model-Based Evaluation Metrics for Text Generation”](https://arxiv.org/abs/2212.10020) | ACL 2023 Long Paper [[ACL Anthology]](https://aclanthology.org/2023.acl-long.674/) | 在 open-ended generation、translation、summarization 上对现有 NLG metrics 做 synthetic stress tests，揭示 blind spots 并提供跨任务的测试设计；属于 metric critique + reusable stress-test protocol。 |
| [arXiv:2204.00004 — “Reproducibility Issues for BERT-based Evaluation Metrics”](https://arxiv.org/abs/2204.00004) | EMNLP 2022 main [[ACL Anthology]](https://aclanthology.org/2022.emnlp-main.192/) | 重现 4 个 released BERT metrics，发现 undocumented preprocessing、missing code、weak baselines 和错误 CSV column 会改变或夸大 metric-human correlation；属于 bug identification + effect quantification + metric/protocol audit。 |
| [arXiv:2311.09783 — “Investigating Data Contamination in Modern Benchmarks for Large Language Models”](https://arxiv.org/abs/2311.09783) | NAACL 2024 Long Paper [[ACL Anthology]](https://aclanthology.org/2024.naacl-long.482/) | 审计 MMLU 等 released benchmarks 的 retrieval overlap，并提出 Testset Slot Guessing 作为污染诊断；属于 leakage audit + adoptable contamination test。 |
| [arXiv:2310.17589 — “An Open Source Data Contamination Report for Large Language Models”](https://arxiv.org/abs/2310.17589) | Findings of EMNLP 2024 [[ACL PDF]](https://aclanthology.org/2024.findings-emnlp.30.pdf) | 在超过 15 个 models、6 个 benchmarks 上量化约 1–45% contamination 和相应 accuracy inflation，并开放完整 pipeline；属于 leakage audit + reusable audit infrastructure。 |
| [arXiv:2407.07565 — “On Leakage of Code Generation Evaluation Datasets”](https://arxiv.org/abs/2407.07565) | Findings of EMNLP 2024 [[ACL PDF]](https://aclanthology.org/2024.findings-emnlp.772.pdf) | 分解 code-generation evaluation 的三类 leakage，发布 161-prompt 的 genuinely held-out LBPP benchmark，并显示 SOTA 在 held-out 上明显下降；属于 leakage audit + held-out benchmark invalidation。 |
| [arXiv:1907.01463 — “Reproducibility in Machine Learning for Health”](https://arxiv.org/abs/1907.01463) | ICLR 2019 Reproducibility in Machine Learning Workshop [[ML Anthology]](https://mlanthology.org/iclrw/2019/anonymous2019iclrw-reproducibility-a/) | 系统审计超过 100 篇 ML-for-health papers 的 data/code accessibility 与 reproducibility reporting，并提出可执行的报告建议；属于 reproducibility audit。 |
| [arXiv:2405.11125 — “A Reproducibility Study on Quantifying Language Similarity: The Impact of Missing Values in the URIEL Knowledge Base”](https://arxiv.org/abs/2405.11125) | NAACL 2024 Student Research Workshop [[ACL PDF]](https://aclanthology.org/2024.naacl-srw.25.pdf) | 审计广泛复用的 URIEL/lang2vec knowledge base，发现语言 typological coverage 与 missing-value handling 会改变 similarity 结论；属于 hidden-data-dependency / reproducibility audit。 |

### 专门 reproducibility track 或窄范围但正式发表的先例

| arXiv ID 与 exact title | Venue / year | 主要贡献形式 |
|---|---|---|
| [arXiv:1708.04133 — “Reproducibility of Benchmarked Deep Reinforcement Learning Tasks for Continuous Control”](https://arxiv.org/abs/1708.04133) | ICML 2017 Reproducibility in Machine Learning Workshop [[workshop]](https://openreview.net/group?id=ICML.cc%2F2017%2FRML) | 重跑 DDPG/TRPO 在 Hopper/Half-Cheetah 上的 benchmark，分离 seed、hyperparameter 与 environment variance，并形成 reporting guidance；属于 reproduction failure/variance audit。 |
| [arXiv:2404.14989 — “A Reproducibility Study of PLAID”](https://arxiv.org/abs/2404.14989) | SIGIR 2024 Resource & Reproducibility track；track 与 DOI 可由 [[SIGIR proceedings]](https://sigir-2024.github.io/proceedings.html) 核对 | 重现 PLAID，并补上缺失的 BM25+ColBERTv2 baseline，发现低延迟 reranking 和 token-alignment pattern；属于 reproduction failure + baseline omission + generalizable insight。 |
| [arXiv:2301.10493 — “From Baseline to Top Performer: A Reproducibility Study of Approaches at the TREC 2021 Conversational Assistance Track”](https://arxiv.org/abs/2301.10493) | ECIR 2023，Springer chapter [[DOI]](https://doi.org/10.1007/978-3-031-28241-6_12) | 跨 TREC 2020/2021 重现 baseline 与 top system，发现 top-vs-baseline gap 从 18% 缩到 5%，并量化哪些 component effects 能泛化；属于 reproduction failure + published ranking/conclusion correction。 |
| [arXiv:2410.13989 — “Reproducibility study of ‘LICO: Explainable Models with Language-Image Consistency’”](https://arxiv.org/abs/2410.13989) | Transactions on Machine Learning Research / ML Reproducibility Challenge 2024 [[OpenReview PDF]](https://openreview.net/pdf?id=Mf1H8X5DVb) | 对 released LICO 做全面 reproduction，主要性能增益无法复现；属于 reproduction failure + protocol/implementation diagnosis。 |
| [arXiv:2109.09670 — “Reproducibility Study: Comparing Rewinding and Fine-tuning in Neural Network Pruning”](https://arxiv.org/abs/2109.09670) | ReScience C ML Reproducibility Challenge 2021 [[article]](https://zenodo.org/record/6574679/files/article.pdf) | 重现三种 pruning approaches，并在 CIFAR100/WideResNet 扩展后发现大模型中的边界条件；属于 reproduction + limitation analysis。该例是 mixed reproduction，不应伪装成纯 bug report。 |

### 形式相近但不纳入“已核实正式先例”主集合的边界项

- Tramer et al., [arXiv:2202.12219 — “Debugging Differential Privacy: A Case Study for Privacy Auditing”](https://arxiv.org/abs/2202.12219)：作者 publication page 目前只给出 arXiv preprint；peer-reviewed venue **UNVERIFIED**，所以不把它用作“已发表主会先例”。它仍说明：一个约 10× 的 implementation bug effect 也不自动产生已核实的 main-track publication。
- Barratt & Sharma, [arXiv:1801.01973 — “A Note on the Inception Score”](https://arxiv.org/abs/1801.01973)：公开 metadata 指向 ICML 2018 workshop；具体 proceedings record **UNVERIFIED**，因此只作边界证据。
- 对 arXiv:2005.12729 的 venue title，arXiv/openreview PDF 曾出现 “ICLR 2019” 字样，而 ICLR 官方 2020 poster/download 页面给出 accepted-title variant 和 ICLR 2020；本文采用官方 ICLR 2020 记录，并保留 arXiv exact title。这个 discrepancy 已显式标出。

## Q2：哪些 observable properties 真正区分了已发表诊断工作？

下表是从已发表集合做的观察性比较，不是一个必要充分定理。

| 属性 | 先例中实际出现的证据 | 对区分的判断 |
|---|---|---|
| 影响已发表结论、排名或 headline comparison | Engstrom 将 PPO/TRPO 差异归因改写；Dacrema 的 11/12 neural-vs-simple baseline 结果；TREC gap 18%→5%；Agarwal 显示 benchmark point estimates 可反转；BLEU/FID/resize papers 显示 protocol 会改变 ranking 或可信度 | **强区分项。** 最强论文不只“发现 bug”，而是证明读者会得出不同结论。 |
| 跨系统、模型、环境或 benchmark 的 breadth | Henderson、Agarwal、MIL unit tests、BLEU、metric stress tests、contamination papers 都覆盖多个 independent units；PLAID 和 TREC 至少跨 baseline/system 或跨年份 | **强区分项。** 不是单纯追求论文数，而是让发现脱离一个 code path 后仍可检验。 |
| 超出单一 codebase 的 general lesson | unit-test pattern、uncertainty-aware profile、contamination taxonomy、resize reference implementation、reporting checklist | **强区分项。** 可迁移的规则或 diagnostic artifact 是 main-track 和 TMLR 先例的共同点。 |
| 可被他人采用的 test、protocol、library 或 held-out benchmark | rliable、MIL algorithmic unit tests、BLEU safeguards、TS-Guessing、open contamination pipeline、LBPP held-out set | **强区分项。** “别人能按同一规则检查”比只给一个本地 traceback 更有发表价值。 |
| held-out / prospective separation | Oren/LBPP 明确提供 genuinely held-out set；跨年份 TREC 与跨 benchmark reproduction 提供 out-of-sample-like check；但一些 reproductions 并不严格是预注册 held-out | **有帮助但非绝对必要。** 它主要区分外部效度和泛化措辞；不存在一个被这些论文共同证明的固定 N 或固定 held-out 比例。 |
| sample size 绝对阈值 | 先例规模从一个系统的 reproduction 到 17 fields/294 papers、250,000 agents 不等 | **不是单独的区分项。** 14 个窗口并非因数字本身自动无效；问题在于 14 个是暴露窗口、只来自两个 sequence、不能支撑 prevalence/generalization。 |
| effect size 很大 | DP bug、TREC gap、ranking inversion 等很醒目 | **不是充分条件。** 大 effect 没有跨系统或可复用 lesson 仍可能停留在 preprint/workshop；反过来，metric/reproducibility papers 也可凭严谨协议与一般性发表。 |
| 负结果 | ReScience C、NeurIPS reproducibility/evaluation guidance 和 MLRC 明确容纳 failure、negative result、generalizability failure | **不是劣势本身。** 负结果必须同时提供可审计过程、独立复核和可迁移 lesson。 |
| “有一个 bug”本身 | 多篇成功论文的起点是 implementation/state/protocol flaw | **不够。** published bar 更接近“bug + consequence + scope + reusable audit”，而非 bug report alone。 |

因此最稳定的区分组合是：

**结论影响 + 跨独立 units 的外部效度 + 可采用的 audit/test artifact。**

held-out 与不确定性分析加强可信度，但没有证据支持一个简单的硬阈值；增加同一暴露 panel 的 seeds 也不会自动产生这些属性。

## Q3：把这些区分项逐项对照本项目

| published-diagnostic property | 本项目已有 | 具体缺口 |
|---|---|---|
| 真实 defect 与 consequence | 有。initial_threshold 的跨调用依赖、reset() 不清除、order-invariance 11/11、pre-scoring census、NULL byte identity、clean/leaked effect 都有仓库和 sealed-artifact 记录 | 还没有证明该 defect 改写了 VMem 原论文的已发表 headline conclusion、ranking 或 revisitation result。报告明确说当前 panel 不包含 revisitation。 |
| 因果/归因清晰度 | 有较严谨的 gate、byte identity 与 pre-declared repair disposition；NULL/PERMUTATION/CONTENT 先于 score 固定 | source-level confound 仍存在：同一 target_c2ws 驱动 retrieval query 和 camera normalization。query-side intervention 不能直接被归因为 retrieval-only mechanism。 |
| breadth | 14 windows、两个 exposed sequences、两 seeds、一个 dependency group、一个 frozen consumer | 没有第二个 released consumer、版本、任务、dataset family 或 downstream metric；不能估计系统家族中的 prevalence 或平均 effect。 |
| held-out / independent validation | 没有。报告明确把 sequences 标为 exposed development data | 不能用同一 14 windows 支撑泛化到新场景的陈述；也没有预先封存的独立 evaluation set。 |
| effect and uncertainty | 有 window-level means/SD、stratification 和 finite-panel accounting | 14-window RGB PSNR effect 多数小于 0.5 dB 且 heterogeneity 很大；报告没有 SE、CI、test、equivalence 或 bootstrap。+0.242/1.270 约 5.25×，但 clean−leaked 与 repair 的 SD/mean 比例不同，不能用一个“5×”概括。 |
| general lesson | 有潜在的 state-leak/order audit lesson；gate、census、byte-identity accounting 是可描述的 artifacts | 尚未在第二个 consumer 或外部系统上运行，因此“可迁移 protocol”仍是设计意图，不是外部验证过的 artifact。 |
| adopted artifact / protocol | 本仓库内有 order gate、regime census、hash gate、repair manifest | 没有独立作者采用或跨系统复核的证据；本地 checklist 还不能等同于 rliable、MIL unit tests 或 held-out contamination benchmark 那种已展示可迁移性。 |
| original repair / negative result | 有：+0.20 dB threshold 预先声明，实际 −0.016 dB，按规则 discarded | 这个负结果只说明该 repair explanation 在这 8 个可实例化 affected windows 上未达标准；它不把 state defect 变成跨系统机制，也不修复 held-out 缺失。 |

所以当前材料**清除了“本地诊断真实存在且有可复核结果”的低门槛，但落在已发表广义诊断工作的关键高门槛之下**。缺口是结构性的，不是把表格写得更长就会消失。

如果要使它成为一个有现实可能性的 TMLR / NeurIPS reproducibility-evaluation / main-track 诊断稿，最小的新增证据类别是：

1. 至少一个独立 released consumer/version，最好再有独立 downstream task 或 benchmark，使 state dependency 与 consequence 不只存在于这一个 VMem path。
2. 在分析前封存的 held-out scenes/windows，且不与两条 exposed development sequences 混用。
3. 把 order/state audit protocol 在多个系统上运行，报告哪些检查可复用、哪些是 VMem-specific；不能只声称通用。
4. 直接连接到原论文或公开 benchmark 的 published conclusion/ranking：必须展示什么结论被改变、改变范围多大、哪些结论不受影响。
5. 对 window-level heterogeneity 给出适合有限 panel 的 uncertainty/replication evidence，并让独立运行者复核关键 artifact。
6. 至少一个非 RGB-PSNR 的评价维度，或明确证明该诊断结论在与任务相关的第二个 evaluation view 上仍成立；这不是为了堆 metric，而是为了避免把单一 pixel metric 的变化误当成系统级 consequence。

这些是“发表门槛对应的证据补齐项”，不是本报告提出的新方法。仅增加同一 panel 的 seeds、重新生成相同 windows、或继续调 repair threshold，不会补齐 breadth、held-out 或 external adoption。

## Q4：什么 venue 实际会发表这种工作？

### Main conference tracks

AAAI、ICLR、NeurIPS、ACL、CVPR 都有诊断论文先例，但主会先例的共同条件是：问题跨越一个 codebase，或能改变 benchmark/metric/algorithm comparison，并提供可复用的测试、protocol 或 tool。上表的 Henderson、Engstrom、Agarwal、Choshen、Freitag、Parmar、Kynkäänniemi 都属于这种“diagnosis is the intellectual contribution”形态。

因此“诊断工作不能进 main track”是错的；但“单系统 forensic report 通常足以进 main track”也没有被这些先例支持。

### TMLR 与 NeurIPS 的 reproducibility / evaluation 路线

[TMLR editorial policies](https://www.jmlr.org/tmlr/editorial-policies.html) 明确把以下内容放进 scope：对现有 technique 揭示 strengths/weaknesses 的实验研究、对既有 claims 的 reproducibility studies，以及能给出 convincing evidence 和 actionable lessons 的 work。其 reproducibility certification 还要求超出简单 verification 的 added baselines、analysis、ablations 或 insight。

[NeurIPS 2026 Call for Evaluations & Datasets](https://neurips.cc/Conferences/2026/CallForEvaluationsDatasets) 与 [E&D FAQ](https://neurips.cc/Conferences/2026/EvaluationsDatasetsFAQ) 说明 E&D track 的 evaluation contribution、benchmark limitations/failure modes、rigorous reproduction/auditing/stress-testing 和 negative/critical analyses 可以进入与 main track 并列的 proceedings；要求 evaluation 是核心 intellectual contribution，并要求 code/data 或足以复核的分析材料按其政策提供。

[NeurIPS 2026 Call for Reproducibility](https://neurips.cc/Conferences/2026/CallForReproducibility) 说明 MLRC 已整合为 NeurIPS 2026 的官方路线，但 submission 需要先被 TMLR 接收；展示在 NeurIPS，论文属于 TMLR proceedings，不属于 NeurIPS proceedings。该 call 的 scope 包括 reproductions、failures、generalizability、meta-reproducibility 和 stress-testing evaluation benchmarks。

这使 TMLR/MLRC 成为窄而严谨诊断稿的现实路线，但现有项目仍缺少上面列出的跨系统和 independent validation 证据。

### Reproducibility journals、专门 track 与 workshops

[ReScience C](https://rescience.github.io/) 是同行评审、开放获取、明确面向 computational replication 的期刊；其 [write guide](https://rescience.github.io/write/) 也接受 negative results、failure 和 replication obstacles。它比 main track 更能容纳单篇系统的深度复现，但仍要求独立实现、可审计 artifact 和清楚的 replication finding。

SIGIR 2024 的 [Resource & Reproducibility call](https://sigir-2024.github.io/call_for_res_rep_papers.html) 是另一种现实范例：论文进入主 proceedings 的专门 track，但要求 generalizability 或 new insight，而不是只证明代码能运行。ECIR 的 reproducibility session 和 ICML 2017 的 RML workshop 则显示，较窄的 reproduction/protocol diagnosis 确实有专门落点。

在 health/ML 等垂直领域，ML4H 一类 symposium/findings track 会显式征集 negative results、reproducibility studies 和 critique；这种 route 的 audience 与要求都比通用 main track 更聚焦。

### Registered reports

[Center for Open Science 的 registered reports 说明](https://www.cos.io/initiatives/registered-reports)代表的是“结果产生前审查 protocol，之后按预先承诺发表”的路线。它适合在 data collection/analysis 前锁定 hypothesis、sample、analysis 和 stopping rule；本项目的两条 sequences 已经作为 exposed development data 使用，因此不能把当前结果事后改写成一份真正的 registered report。它可以说明未来 protocol 的形式，但不是当前材料的补救 venue。

## 结论

已发表 precedent 支持一个清晰但有条件的答案：diagnostic / forensic work 可以发表，甚至可以进 AAAI、ICLR、NeurIPS、ACL、CVPR；但进入这些 venue 的论文通常把一个局部故障提升为跨系统可复核的结论，展示它改变了公开 comparison，或交付了别人可采用的 benchmark/test/protocol。TMLR、MLRC、ReScience C、SIGIR/ECIR reproducibility routes 对窄范围工作更现实，但也不把“单一 consumer + 暴露 panel + 一个 metric”自动视为充分。

就本项目现有证据，诚实裁定仍是：**达到了严谨的单系统诊断报告层，但没有达到可发表的广义 diagnostic contribution 层。** 这个差距只有通过新的独立证据类别才可能缩小；在没有这些证据时，不能用 effect 的方向、11/11 gate、byte identity 或更多同 panel seeds 代替外部效度。

## 核验说明与来源边界

- 论文表中的 arXiv IDs、exact titles 和 venue links 均以 arXiv 页面与官方 venue/proceedings/Anthology 页面交叉核对；显式标出的 title/year discrepancy 保留为 discrepancy。
- “UNVERIFIED” 只用于没有足够正式 venue 证据的边界项；未把这些边界项当作主集合的发表先例。
- 本文件是本轮唯一新建文件。未运行 GPU、训练或 generation；未修改已有仓库文件。
