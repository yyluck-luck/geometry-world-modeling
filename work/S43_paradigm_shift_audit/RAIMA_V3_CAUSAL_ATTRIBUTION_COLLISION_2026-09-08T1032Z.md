# RAIMA V3 单来源因果归因碰撞

- 检索冻结时间：2026-09-08T10:32:42.202494+00:00（北京时间18:32:42）
- 状态：`PRIMARY_SOURCE_COLLISION_NOTE`
- 新模型运行：`0`
- 边界：该文研究训练数据归因，不是视频世界模型的运行期 3D memory；以下迁移均明确标为设计启发，不能当作直接实证

## 新碰撞

Nature Communications 2026 的 *Outputs of generative diffusion models are often unattributable* 用因果反事实定义生成样本对训练数据单元的可归因性：固定外生生成因素，省略一个训练数据单元，并以事实输出与反事实输出的最大距离形成 Counterfactual Radius。论文报告，训练数据规模增大时，输出对任一单独训练单元的可归因性可能衰减；它还指出外观相似不能替代反事实归因。

该结论与 RAIMA 的对象不同：论文省略的是**训练数据**，需要可消融模型；RAIMA拟审计的是推理期已存储、已选中、可寻址的**运行时 memory item**。因此不能直接把该论文的结论搬到VMem，也不能说它已经做了3D runtime memory审计。

## 它杀死的宽泛创新表述

- “首次发现生成输出可能对单一来源几乎无响应”；
- “首次用固定噪声的反事实省略测生成来源影响”；
- “首次说明相似/检索证据不等于因果归因”。

这些概念已有强跨域先例。RAIMA若存活，只能依赖更窄的联合对象：

`ordinary-selected runtime memory source × enumerated appearance consumer × 3D support × in-distribution intervention × never-conditioned real-reference signed utility`

## 新增设计约束

1. 单source低effect可能来自多来源冗余或抵消，不能写成“模型没有使用memory”。
2. 主文只允许报告`tested single-source observable influence`；group/interaction分析只能作为结果后机制追踪，并需另行冻结。
3. factual/counterfactual必须固定seed、noise、prompt、camera、source order及除目标source外的全部条件。
4. 相似度、检索分数和addressability只作上游描述量，不能代替output intervention。
5. 若任何普通选中source都低effect，但联合移除有大effect，结论应是`distributed/redundant influence`，而非memory-blindness。

## 当前裁决

`GENERIC_SINGLE_SOURCE_ATTRIBUTION_NOVELTY_REJECTED; RUNTIME_3D_REFERENCE_ANCHORED_INTERSECTION_REMAINS_UNVALIDATED`

这使候选主张更窄，但也让未来阳性结果更有解释力：真正值得报告的是运行期3D memory在特定生成路径上的空间与效用责任，而不是一般“来源能不能归因”。

## 一手来源

- Zheng Dai and David K. Gifford, *Outputs of generative diffusion models are often unattributable*, Nature Communications 17, 6974 (2026)：<https://www.nature.com/articles/s41467-026-75667-5>
