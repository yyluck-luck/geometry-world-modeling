# RAIMA V3 第二次实时碰撞与顶会创新模式刷新

- 检索冻结时间：2026-09-08T10:18:45.349986+00:00（北京时间 18:18:45）
- 状态：`PRIMARY_SOURCE_COLLISION_AND_DESIGN_THREAT_ADDENDUM`
- 边界：只记录文献碰撞、设计威胁和可证伪路线；不修改已冻结 V3，不授权方法、模型运行或新颖性
- 本轮新增模型运行：`0`
- 检索规则：正式会议页面优先；预印本明确标为预印本；未检索到不等于不存在

## 给新手的一句话

顶会和最新预印本已经把“3D 记忆”“可更新记忆”“按视角检索”“压缩检索”“随机检索消融”做得很拥挤。当前仍可能值得研究的不是再造一种记忆，而是检查一个被整体分数掩盖的问题：**系统声称找到了正确记忆时，那条具体记忆是否真的在具体生成路径上产生了空间正确、对未输入真实参考有益的变化。**

这仍是待验证问题，不是创新成果。

## 1. 新增直接碰撞

| 工作 | 状态 | 已覆盖内容 | 对本项目的直接约束 |
|---|---|---|---|
| Spatia: Video Generation with Updatable Spatial Memory | CVPR 2026 | 以持续更新的 3D point cloud 作为 spatial memory，用视觉 SLAM 更新，并以渲染的 2D point-cloud sequence控制视频生成 | “可更新 3D memory”“动态/静态解耦”“显式相机控制”均不能成为我们的宽泛创新声明 |
| Plenoptic Video Generation / PlenopticDreamer | CVPR 2026 | 多历史视频的时空记忆、3D FOV 检索；公开消融包含 random context retrieval 与 retrieved-context 数量 | “加入随机检索对照”或“测上下文数量”不是贡献。其随机检索结果也只说明整体性能变化，尚不能替代单 source、单 consumer、空间定位和 held-out utility 的联合审计 |
| Geometry-Aware Implicit Memory for Video World Models / GIM-World | arXiv:2606.02436，2026-06-01；本轮未确认正式主会 | 固定大小隐式 memory token、camera-queryable geometry head、训练期 3D teacher 和 information-guided pruning | “几何感知隐式记忆”“相机查询几何监督”“信息量剪枝”均已被占据；RAIMA 不得把 geometry-aware memory 本身称新 |
| Compression and Retrieval / CaR | arXiv:2606.23105，2026-06-22；本轮未确认正式主会 | viewpoint positional encoding、attention-driven implicit retrieval、轻量上下文压缩和 SceneFly 数据 | “学习式视角检索”“压缩后检索”“attention retrieval”均已被占据；未来方法必须由真实审计失败形状决定，并与这些简单强基线比较 |

## 2. 一个会让反事实实验失效的顶会警告

ICLR 2026 的 *Addressing divergent representations from causal interventions on neural networks* 理论和实证说明，常见内部因果干预可能把表示推离模型自然分布；其中有些偏移会激活原本沉睡的行为路径，导致解释不忠实。

该论文研究的是**内部表示干预**，不能直接证明 VMem 的输入级 source replacement 一定失效。但是它暴露了一个适用于本项目的严重设计威胁：如果删掉、置零或乱序 memory source 生成了训练时从未见过的条件，我们测到的可能是“异常输入反应”，而不是该 source 的自然因果作用。

因此后续冻结协议至少需要：

1. 与自然 memory 分布匹配的 `matched replacement`，不能只用 zero/drop/scramble；
2. 不改变 source 个数、张量形状、时间位置和大尺度统计量的 placebo；
3. 结果前规定的 intervention-validity 与 distribution-shift 检查；
4. 将异常分布的干预单列为 stress test，不能并入主 estimand；
5. 若自然匹配无法成立，主因果声明直接停止，而不是从异常干预中选最好看的结果。

## 3. 从顶会论文学习到的创新生成模式

CVPR 2026 的 *Causality in Video Diffusers is Separable from Denoising* 先对层和去噪步做系统 probe，发现重复计算与稀疏跨帧注意的规律，再据此提出把时序推理和逐帧渲染分离的架构。它提供的可迁移方法论是：

1. 先找一个强基线中可重复、可定位的反常规律；
2. 用机制 probe 判断失败发生在哪个模块、哪个阶段；
3. 只针对已定位瓶颈改结构；
4. 用强基线和真实/合成双域证明收益不是偶然。

这正支持本项目当前的顺序：先完成 source × consumer 审计，再决定是否需要 routing、reweighting、refresh 或另一种方法。不能从该论文直接推出我们的方法，也不能把“先 probe 后设计”称作新颖贡献。

## 4. 碰撞后仍存活的最窄问题

`ordinary-selected runtime source × explicitly enumerated consumer × outcome-preprocessed 3D support × in-distribution matched intervention × never-conditioned real reference`

它要同时回答五件事：

1. memory item 是否实际被普通运行时规则选中；
2. 它是否对预注册的具体 consumer 路径产生可重复变化；
3. 变化是否落在结果前定义的 3D 支持区域，而非任意全局波动；
4. 在未送入生成器的真实 reference 上，该变化是有益、无效还是有害；
5. 结论是否跨 scene cluster、seed 和第二个 stable-source 架构保持。

任何单项都不是创新。只有这个联合问题在真实数据上形成稳定、重要、强基线未解释的失败，才可以进入方法设计。

## 5. 当前裁决和硬停止规则

裁决：`PIVOT_NARROWER; MEASUREMENT_CANDIDATE_ONLY; NO_METHOD; NOVELTY_NONE`

以下任一情况发生即停止把它包装成论文级新问题：

- matched intervention 本身无法通过自然分布检查；
- source 或 consumer 身份不能由运行期证据唯一绑定；
- effect 只在 zero/drop/scramble 等异常干预上出现；
- effect 无法在 3D support 上定位；
- held-out reference utility 不稳定、效应过小或在 scene-level 置信区间内包含预注册无效区；
- WorldTrace、Spatia、PlenopticDreamer、GIM-World/CaR 或简单 pose/age/reliability baseline 已解释相同现象；
- 只在单一 VMem 架构成立，第二个 stable-source host 不复现。

## 6. 一手来源

- Spatia（CVPR 2026）：<https://openaccess.thecvf.com/content/CVPR2026/papers/Zhao_Spatia_Video_Generation_with_Updatable_Spatial_Memory_CVPR_2026_paper.pdf>
- Plenoptic Video Generation（CVPR 2026）：<https://openaccess.thecvf.com/content/CVPR2026/papers/Fu_Plenoptic_Video_Generation_CVPR_2026_paper.pdf>
- GIM-World（预印本）：<https://arxiv.org/abs/2606.02436>
- Compression and Retrieval（预印本）：<https://arxiv.org/abs/2606.23105>
- Addressing divergent representations from causal interventions（ICLR 2026）：<https://proceedings.iclr.cc/paper_files/paper/2026/hash/133e588e1429f9f1e25b215da145580e-Abstract-Conference.html>
- Causality in Video Diffusers is Separable from Denoising（CVPR 2026）：<https://openaccess.thecvf.com/content/CVPR2026/html/Bai_Causality_in_Video_Diffusers_is_Separable_from_Denoising_CVPR_2026_paper.html>
