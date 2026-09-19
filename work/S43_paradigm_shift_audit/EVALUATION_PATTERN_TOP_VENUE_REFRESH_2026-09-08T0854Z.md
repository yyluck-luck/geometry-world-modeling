# 顶会评价范式碰撞刷新（2026-09-08T08:54Z）

- 状态：`PRIMARY_SOURCE_COLLISION_UPDATE`
- 新颖性授权：`NONE`
- 范围：会议官方页面；只更新问题边界，没有新增模型运行

## 直接改变本项目主张边界的三项工作

### MomentSeeker（NeurIPS 2025 Datasets and Benchmarks）

官方页面：<https://proceedings.neurips.cc/paper_files/paper/2025/hash/281e0b9142763f2b6c944fedb8550ba9-Abstract-Datasets_and_Benchmarks_Track.html>

该工作明确指出，只看端到端长视频理解表现，无法判断关键时刻是否被准确访问，因此单独建立 moment retrieval benchmark。它占据了“端到端成功不等于访问成功”这一通用问题结构。

**对我们的约束：** `Address` 与最终输出分开不是独立创新。剩余差别必须是生成世界模型中、ordinary-selected external memory item 在访问之后的 `Influence → Localization → Benefit` 责任链。

### Hi3DEval（NeurIPS 2025 Datasets and Benchmarks）

官方页面：<https://proceedings.neurips.cc/paper_files/paper/2025/hash/42ffaddcc6edc9fb05ff9f9b49fca700-Abstract-Datasets_and_Benchmarks_Track.html>

该工作用 object-level 与 part-level 的 hierarchical validity 评价3D生成，并建立多维标注与自动评分。

**对我们的约束：** “把一个总分拆成层级/局部维度”已经有强先例。GeoCausal Memory Contract 必须依靠跨层逻辑约束、逐 source 反事实和可推翻的非显然实证，而不能把六层列表本身称为贡献。

### Ref4D-VideoBench（CVPR 2026）

官方页面：<https://openaccess.thecvf.com/content/CVPR2026/html/Wei_Ref4D-VideoBench_Four-Dimensional_Reference-Based_Evaluation_of_Text-to-Video_Generative_Models_CVPR_2026_paper.html>

该工作说明 no-reference 评价难以给出可追责的 instance-level 判断，因而使用高质量 reference videos 和12项结构化指标。

**对我们的约束：** “使用真实 reference 做细粒度视频评价”也不是创新。S48 的 Benefit 只能作为因果合同中的必要真值端点；新信息必须来自某条运行时 memory source 的 matched intervention 对这个端点的 signed change。

## 更新后的最窄候选主张

不能主张：

1. 首次做分层/多维评价；
2. 首次用 reference video；
3. 首次区分访问与端到端任务成功；
4. 首次做3D局部或实例级评价。

只有在真实数据支持后，才可能主张：

> 对显式视频世界模型中 ordinary-selected、source-ID稳定的单条外部记忆，首次在同一冻结协议中连接 Store/Select/Address 的运行证据、跨所有 appearance consumer 的 matched intervention、干预前几何 support 的反事实定位，以及对独立真实 return reference 的 signed Benefit；并揭示传统 retrieval/return 指标系统性漏掉的失败。

“首次”仍需投稿前完整系统检索与源码核验；当前只记录目标差别，不授权新颖性。

## 实验设计动作

1. 把 MomentSeeker 式 access 指标列为 Address baseline，而非贡献；
2. 把 Hi3DEval 式 hierarchical/part-level scoring 列为 evaluation baseline，而非贡献；
3. 把 Ref4D 式 reference-based multi-dimensional score 列为 Benefit baseline，而非贡献；
4. 只有 source intervention 对真实 reference 的 paired signed delta 才进入核心结果；
5. 若普通 retrieval/access + reference metric 已解释全部现象，停止 GeoCausal/PC-DPM 主张。

