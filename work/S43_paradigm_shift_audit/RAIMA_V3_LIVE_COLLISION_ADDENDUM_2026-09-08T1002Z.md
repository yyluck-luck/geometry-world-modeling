# RAIMA V3 实时近邻碰撞补充

- 检索冻结时间：2026-09-08T10:02:47.760671Z（北京时间 18:02:47）
- 状态：`PRIMARY_SOURCE_COLLISION_ADDENDUM`
- 作用：给冻结 V3 的 fresh adversarial reviewer 提供新增近邻；不修改 V3，不授权新颖性
- 模型运行：`0`
- 检索边界：检索命中可以否决宽泛主张；检索未命中不能证明首创

## 给新手的一句话

新论文已经占据“记忆能不能被找到”“回去时像不像原场景”“检索相关不等于真正影响输出”等宽泛问题。我们若要有论文价值，必须证明一个更具体、也更难的问题：**在视频世界模型已经选中并定位到某条 3D 历史来源以后，这条来源究竟在哪条生成路径产生了多大变化，这个变化是否落在合理空间区域，并且是否真的让未送入模型的真实参考更接近。**

当前只把它称为待验证交集，不能称创新结果。

## 1. 新增直接近邻

| 工作 | 公开状态 | 已占据内容 | 对 RAIMA 的约束 |
|---|---|---|---|
| Addressable Memory for Video World Models / WorldTrace | arXiv:2608.07408，2026-08-07；未在本轮确认主会录用 | 把长时 KV memory 的存储与 addressability 分开；用虚拟位置保持可寻址，并用 LoopBench 的返回轨迹测 episodic recall | `Address`分层、ABA/回环轨迹、返回首帧相似度、training-free cache修复都不能称新；Stage C必须把WorldTrace/LoopBench列为最直接视频基线 |
| ReWorld | arXiv:2608.23565，2026-08-24；未在本轮确认主会录用 | pose-indexed landmark memory、palindrome return trajectories、固定cache预算和分钟级out-and-back recall | 回文/返回轨迹、pose-nearest retrieval和固定预算不是新意；RAIMA必须测ordinary-selected单source责任，而不是再做一个整体回环分数 |
| MBench | arXiv:2606.00793，2026-05-30；未在本轮确认主会录用 | 把视频世界模型memory benchmark拆为entity、environment、causal consistency及12个子维度，并用真实长视频评价 | “做一个memory benchmark”或层级taxonomy本身不足；RAIMA要提供已有benchmark没有的runtime source intervention与reference-bound证据 |
| E3C | arXiv:2605.26316，2026-05-25；未在本轮确认主会录用 | 明确3D point memory、per-point appearance feature、view-aligned conditioning；通过删除3D memory中的物体点展示生成编辑 | “编辑3D memory会改变视频”和单次object removal已经被演示；RAIMA的edit必须有matched zero、负控、空间support和held-out reference，且不能把可编辑性直接解释成source causal use |
| What-If World | arXiv:2605.27589，2026-05-26；未在本轮确认主会录用 | 用只改变一个物理变量的成对视频测试，把单视频看似合理与对干预敏感分开 | “成对干预揭示单样本指标盲点”已被占据；RAIMA的区别必须是内部runtime memory source、3D support与真实reference utility，而非prompt-level物理反事实 |

## 2. 顶会机制近邻

| 工作 | 已核 venue | 已占据内容 | 对 RAIMA 的约束 |
|---|---|---|---|
| Scalable Influence and Fact Tracing for LLM Pretraining | ICLR 2025 Conference | 实证指出经典检索更擅长找显式相关文本，而梯度影响更接近改变预测的训练样本；两者可能错位 | “retrieval relevance 不等于 causal influence”是跨领域已知发现，不能作为RAIMA单独的新颖性；视频、runtime、3D spatial、reference utility的联合现象才可能形成差异 |
| Attributing Response to Context (ARC-JSD) | ICLR 2026 Conference | 无需微调/梯度/替代模型地识别重要context sentence，并定位与context attribution有关的attention heads和MLP层 | generic context attribution与内部层定位已被占据；若未来增加hidden-state probe，必须与source-specific output intervention联合，而不能把JSD/attention attribution换皮成方法 |
| Counterfactual RAG (CF-RAG) | ICLR 2026 Conference | counterfactual query与parallel evidence arbitration | generic counterfactual evidence arbitration已占据；任何后续memory routing都要胜过其思想迁移和更简单gate |
| State-Change Counterfactuals | ICCV 2025 | 为procedure-aware视频表征构造状态变化反事实，用于错误检测、检索与识别 | generic video counterfactual learning和“What if”叙事已被占据；RAIMA当前只允许结果前audit，不把counterfactual一词当创新 |

## 3. 强预印本解释性近邻

The Attribution Blind Spot（arXiv:2605.26778）指出，仅从输出一致不能辨认模型是依赖外部context还是参数记忆，并明确其内部表示信号也不能认证单条生成究竟用了哪个来源。这直接支持V3把“Use”降级为`Observable Influence`，同时否决“输出几乎不变就证明没用memory”的表述。

它也给出一个未来可检验的二级方向：若VMem hook可审计，可将输出干预与内部consumer representation divergence做联合测量。但在真实AOIG出现前，不建立新方法，也不把跨域内部probe迁移称新颖。

## 4. 碰撞后的候选贡献层级

### 当前保留：新问题/测量候选

`ordinary-selected runtime source × enumerated appearance consumer × 3D support × held-out real reference`

必须同时观察：

1. 已存储、已选中、可寻址；
2. 在matched replay与in-distribution source intervention下产生稳定可观察effect，或稳定低于预注册detectability门；
3. effect与两种结果前geometry support的关系；
4. effect对至少3个从未进入conditioning的真实reference的同号utility；
5. scene-cluster确认与第二个stable-source架构复验。

### 结果前禁止：方法贡献

当前不得提出或命名routing、critic、shared-weight、refresh、cache、active sensing或counterfactual arbitration方法。它们分别与TetherMem、WorldTrace、CF-RAG/CoRM-RAG、GaME/WorldMM/WorldCraft及已有active-retrieval工作重叠，而且尚无真实failure决定该修哪里。

### 可能的论文形态

如果Stage C确认联合gap，并且普通retrieval/return指标、WorldTrace/TetherMem式routing、统一attention与简单pose/age/reliability gate都无法解释或修复，最强贡献顺序应是：

1. 一个以前整体分数遮住的、source-level且具有reference后果的真实失败现象；
2. 一个可复用的typed interventional audit与确认性benchmark；
3. 仅针对剩余失败形状设计的方法，并证明跨架构增量。

如果只得到回环分数差、3D memory可编辑、或retrieval/influence错位的一般结论，则相关概念已被上述工作占据，应降级为复现或诊断。

## 5. 本轮裁决

`PIVOT_NARROWER; NO_METHOD; NOVELTY_NONE`

新增检索没有杀死RAIMA的联合审计问题，但杀死了以下对外表述：

- 首次区分memory storage和addressability；
- 首个视频memory回环benchmark；
- 首次发现retrieval不等于influence；
- 首次通过编辑3D memory验证生成影响；
- 首个成对干预world-model评价。

只有真实数据证明上述四因素交集产生稳定、重要、强基线未覆盖的现象，才重启新颖性判断。

## 6. 一手来源

- WorldTrace：<https://arxiv.org/abs/2608.07408>
- ReWorld：<https://arxiv.org/abs/2608.23565>
- MBench：<https://arxiv.org/abs/2606.00793>
- E3C：<https://arxiv.org/abs/2605.26316>
- What-If World：<https://arxiv.org/abs/2605.27589>
- Scalable Influence and Fact Tracing（ICLR 2025）：<https://proceedings.iclr.cc/paper_files/paper/2025/hash/65798a76cc176c29b6bfefe84b0a03ff-Abstract-Conference.html>
- ARC-JSD（ICLR 2026）：<https://proceedings.iclr.cc/paper_files/paper/2026/hash/ed67dff7cb96e7e86c4d91c0d5db49bb-Abstract-Conference.html>
- CF-RAG（ICLR 2026）：<https://proceedings.iclr.cc/paper_files/paper/2026/hash/1c078897dc08d46091d0d361d9955c6b-Abstract-Conference.html>
- State-Change Counterfactuals（ICCV 2025）：<https://openaccess.thecvf.com/content/ICCV2025/html/Kung_What_Changed_and_What_Could_Have_Changed_State-Change_Counterfactuals_for_ICCV_2025_paper.html>
- Attribution Blind Spot：<https://arxiv.org/abs/2605.26778>
