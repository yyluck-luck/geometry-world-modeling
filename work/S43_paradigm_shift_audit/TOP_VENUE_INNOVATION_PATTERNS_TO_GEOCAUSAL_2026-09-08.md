# 顶会创新方法怎样落到本项目：从“有记忆”到“有益地使用记忆”

- 建立时间：2026-09-08（Asia/Shanghai）
- 状态：`LITERATURE_SYNTHESIS_AND_CONDITIONAL_IDEA_LADDER`
- 证据边界：一手论文/正式会议页面与已核官方仓库；没有新增模型运行，没有读取C1/C2像素
- 当前新颖性授权：`NONE`
- 流程依据：Supervisor-Skills `02_Idea_Generation`，尤其2.2“强baseline→失败→根因→方法”和2.3“隐藏假设/领域里的大象/重要问题/可推翻预测”

## 给新手的结论

现在已经有一个**值得真实实验检验的创新候选**，但还不能叫“已完成创新”。

许多记忆世界模型证明了它们可以**存历史、选历史或把历史送进网络**。本项目追问一个更严格的问题：

> 普通运行中被选中的某一条历史记忆，是否真的经过所有消费路径改变了生成；改变是否落在它几何上负责的位置；相对公平替代，它最终是帮助还是伤害？

如果强模型经常出现“存了但不可寻址、选了但没被用、用了但作用错位、作用了但反而有害”，这会暴露现有长期记忆评价的盲点。若这种规律跨模型和场景成立，它可以成为measurement/benchmark贡献；若生成前特征还能预测signed benefit，才进一步形成方法。

## 顶会论文采用的创新套路，以及我们学到什么

| 一手工作 | 它真正的创新动作 | 对本项目的约束/启发 |
|---|---|---|
| [WorldModelBench, NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/4ec03ed08a3fcb59e1c815b5598beff1-Abstract-Datasets_and_Benchmarks_Track.html) | 指出现有“视频质量”评价遗漏physics adherence，再用大规模标注和judge使缺口可测，最后把评价信号用于改进模型 | 评价论文不能只发明一个分数；必须证明旧指标漏掉重要失败、建立可信标注/协议，并让信号能指导改进 |
| [SPMEM, NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/467655d26fcc207bca08915dc91964c6-Abstract-Conference.html) | 把长期遗忘落到geometry-grounded spatial/episodic memory，并配套训练/评价数据 | 普通几何memory已被占据；我们的差别只能来自“已选item是否产生局部且有益的因果作用” |
| [Long-Context SSM World Models, ICCV 2025](https://openaccess.thecvf.com/content/ICCV2025/html/Po_Long-Context_State-Space_Video_World_Models_ICCV_2025_paper.html) | 用block-wise SSM scan换取长上下文，再用dense local attention补局部一致性 | raw context/SSM是强capacity与架构baseline；不能只与弱短窗口检索方法比较 |
| [VMem, ICCV 2025](https://openaccess.thecvf.com/content/ICCV2025/html/Li_VMem_Consistent_Interactive_Video_Scene_Generation_with_Surfel-Indexed_View_Memory_ICCV_2025_paper.html) | 用surfel把历史视图索引到3D表面，再按目标可见表面取回相关视图 | “检索相关视图”正是原baseline；Store/Select本身不能成为我们的新意 |
| [Spatia, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/papers/Zhao_Spatia_Video_Generation_with_Updatable_Spatial_Memory_CVPR_2026_paper.pdf) | 持续更新3D point-cloud memory，并把spatial projection、reference和preceding-video tokens通过不同条件路径送入生成器 | “多路径空间记忆条件”已经存在；但其公开2×2消融中reference-only的LPIPS-C可比无条件更差，说明“记忆被提供”不等于“记忆有益”，支持本项目必须测signed Benefit |
| [WorldStereo, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_WorldStereo_Bridging_Camera-Guided_Video_Generation_and_Scene_Reconstruction_via_3D_CVPR_2026_paper.html) | global-geometric memory控制粗结构，spatial-stereo memory用3D correspondence限制attention receptive field读取细节 | 3D对应约束memory attention已经是正式顶会方法；“按几何区域注入/注意”不能单独作为本项目创新，必须证明来源级因果效用或双路径冲突的额外机制 |
| [PlenopticDreamer, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/papers/Fu_Plenoptic_Video_Generation_CVPR_2026_paper.pdf) | 用3D FoV从视频—相机memory bank检索多个历史片段，配合渐进context与self-conditioned训练保持多视角长时一致 | 3D可见性检索、多context conditioning和长时训练均已占据；普通source-preserving tokens或FoV gate不是足够差别 |
| [LongDiff, CVPR 2025](https://www.openaccess.thecvf.com/content/CVPR2025/papers/Li_LongDiff_Training-Free_Long_Video_Generation_in_One_Go_CVPR_2025_paper.pdf) | 从attention随帧数增长产生information dilution出发，用informative frame selection和位置处理保持细节 | “平均/过多上下文稀释细节”已有理论化先例；本项目只有在固定已选source、比较VMem语义全局平均与slotwise latent路径并显示可复现冲突时才产生新信息 |
| [Dual-Granularity Memory, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Wang_Dual-Granularity_Memory_for_Efficient_Video_Generation_CVPR_2026_paper.html) | 用sink/boundary context memory保持chunk内连续，再用latent context memory检索跨segment信息并cross-attention融合，以效率为主要目标 | “双记忆/双粒度/局部+全局路径”也已被占据；PC-DPM必须证明的是同一source身份在不同appearance consumer间失配，并用共享provenance修复真实失败，而不是再叠两个memory模块 |
| [Movie Weaver, CVPR 2025](https://openaccess.thecvf.com/content/CVPR2025/papers/Liang_Movie_Weaver_Tuning-Free_Multi-Concept_Video_Personalization_with_Anchored_Prompts_CVPR_2025_paper.pdf) | 用`[R1]/[R2]` anchored prompt把概念描述连到对应参考图，并用concept embedding编码参考图顺序，针对cross-attention的order-agnostic与identity blending | “来源标签、参考图顺序编码、概念—图片绑定”已经有直接顶会先例；PC-DPM不能把source token本身当创新，必须在ordinary retrieval而非人工prompt绑定中证明跨consumer provenance失配、几何局部因果效应和signed Benefit |
| [Video Alchemist, CVPR 2025](https://openaccess.thecvf.com/content/CVPR2025/papers/Chen_Multi-subject_Open-set_Personalization_in_Video_Generation_CVPR_2025_paper.pdf) | 给不同参考图加入image-index embedding，并将personalization与text放入分离cross-attention，以维持多主体身份和减少条件竞争 | per-reference身份token与分路attention已有正式先例；PC-DPM的M1/M2必须把它视为容量/路由强基线，不能把source ID embedding本身称新 |
| [Scaling Zero-Shot Reference-to-Video Generation, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/papers/Zhou_Scaling_Zero-Shot_Reference-to-Video_Generation_CVPR_2026_paper.pdf) | 用reference-video attention mask约束交互，并扩展到multi-identity/multi-view references | source-aware mask和多参考绑定也已被占据；剩余差别必须是ordinary-retrieved memory中跨consumer共享provenance、逐source反事实与signed utility闭环 |
| [Structural Video Diffusion, ICCV 2025](https://openaccess.thecvf.com/content/ICCV2025/html/Wang_Multi-identity_Human_Image_Animation_with_Structural_Video_Diffusion_ICCV_2025_paper.html) | 用identity-specific embeddings绑定多人物外观，并用depth/surface-normal结构条件处理交互 | 身份专属表示加几何条件已有先例；本项目必须胜过“给每source单独embedding+geometry”的直接对照 |
| [Geometry-as-context, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Hu_Geometry-as-context_Modulating_Explicit_3D_in_Scene-consistent_Video_Generation_to_Geometry_CVPR_2026_paper.html) | 交替生成RGB与geometry context，用Plucker-ray camera-gated attention调制self-attention，并用geometry dropout保持RGB-only推理 | camera-conditioned gate、显式geometry context和几何dropout都已占据；PC-DPM若只加相机门或几何条件没有新意，M2还应加入camera-gated强对照 |
| [VRAG / Learning World Models for Interactive Video Generation, NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/e32310c3acb058d563a6a9e54d0e9000-Abstract-Conference.html) | 区分不可约的自回归累积误差与不足的memory机制，并用video retrieval与显式global state conditioning减少长期误差 | “加检索/全局状态减少长期漂移”已经有强基线；我们的measurement必须区分记忆缺失、记忆被选但未消费、消费错位和记忆有害，不能把所有回访失败都归咎于memory容量 |
| [WorldTrace](https://arxiv.org/abs/2608.07408) | 找出长rollout时RoPE越界令已存KV不可寻址，并用in-distribution虚拟位置修复 | Address必须从Select中单列；若内容已选却无法寻址，不能说consumer拒绝使用 |
| [Echo-Memory](https://arxiv.org/abs/2606.09803) | 固定backbone/optimizer/action/sampler/eval，仅改变capacity、compression、read-out、recurrence；证明replay与return会给出不同结论 | 必须做matched matrix；replay好不能替代自然return，存储与readout不可混写 |
| [I3DM](https://arxiv.org/abs/2603.23413v2) | 3D-aware retrieval之外，还做3D-aligned injection，只在可靠warping区域注入 | geometry-localized injection已是直接近邻；我们的Localization必须用counterfactual matched-mask证据，而非“有support图” |
| [TetherCache](https://arxiv.org/abs/2606.13035) | GRAB做attention+diversity选择，TAME把召回token对齐到trusted distribution | 普通selection、gate、memory editing和trusted alignment都不是新；必须作为强baseline |
| [CUE-R](https://arxiv.org/abs/2604.05467) | 对单条检索证据做REMOVE/REPLACE/DUPLICATE，报告paired signed utility和交互 | “逐item干预看效用”已有直接抽象先例；本项目必须以视频生成的全消费路径、几何局部零假设和独立真实return reference建立额外差别 |
| [Utility-Oriented Visual Evidence Selection](https://arxiv.org/abs/2605.13277) | 用输出分布information gain定义visual evidence utility，再用轻量surrogate加速 | generic utility surrogate已被占据；未来head不能只说“预测utility” |
| [SelectiveNet, ICML 2019](https://proceedings.mlr.press/v97/geifman19a.html) | 把拒绝与任务损失共同训练，并以risk–coverage评价 | 未来accept/reject必须报告AURC、覆盖率、clean false rejection和全体样本损失 |
| [Activation-patching审计, ICLR 2024](https://openreview.net/forum?id=Ebt7JgMHv1) | 显示corruption、metric和隐藏通路会改变因果定位结论 | 单一编辑响应不够；必须有两edit family、sham、未选source负控、已知consumer正控和剂量稳健性 |

## 当前创新候选的三层结构

### A. 先做可否证measurement：GeoCausal Memory Contract

限定对象是“显式检索、source ID稳定、所有真实appearance consumer可枚举”的模型。证据链是：

`Store → Select → Address → Influence → Localization → Benefit`

这里每个节点单独都不是新意。可能的贡献是**联合合同和非显然的实证规律**：现有系统把前3步当作记忆成功，但后3步可能大量失败，而且旧的replay/return/attention分数不能识别这些失败。

最便宜的决定实验正在写入S48 V5：先要求自然失败，再对普通运行已选source做post-selection全路径一致干预；每个family/seed/sign都用相同re-encode/replace流程的zero-edit作直接配对，以逐像素replay和matched-negative超额图排除空间化sham；再用逐target实际相机support及彼此不混合的`G_shape/G_camera/G_source`排除空间偏置，用同步且从未进入memory的真实照片判signed benefit。V1–V4的独立BLOCKED审查全部保留。

### B. 只有A成立才做方法：GeoCausal Acceptance Head

输入只使用生成前可见的addressability、source-target geometry、retrieval、attention先验、source quality和memory trust。昂贵的source-level signed benefit只作离线教师；轻量学生输出`accept / reject / re-observe`。

潜在机制差别不在head结构，而在教师标签同时满足：

1. 普通运行实际选中且可寻址；
2. 同一source的全部appearance路径一起干预；
3. effect在干预前geometry support上超过matched spatial null；
4. 对独立真实return reference有signed benefit；
5. 训练/test按scene分离并评价risk–coverage和全体损失。

若attention、pose、retrieval或source-quality普通阈值达到相同held-out表现，就停止方法主张。

### C. 更高风险的训练机制：Provenance-coupled Dual-path Memory

当前VMem源码静态审计给出一个比普通gate更具体的机制假设：latent/replace路径保留slot结构，而semantic embedding在`get_cond`中沿source维全局平均后广播。若S48的F10/F01显示两条路径单独干预产生冲突，未来可让同一source provenance权重同时约束semantic与latent消费者，保留per-source semantic tokens，并用signed Benefit决定accept/reject/re-observe；核心目标是让两条路径对“谁提供了信息”保持一致。

这一层目前只是高风险假说。WorldStereo已用3D correspondence限制memory attention，Spatia/SPMEM已使用多条件路径，LongDiff已讨论information dilution，Dual-Granularity Memory已组合chunk内context与跨segment latent memory，Movie Weaver/Video Alchemist/Saber/Structural Video Diffusion又占据参考来源绑定、per-reference identity、分离attention和source-aware mask，Geometry-as-context占据camera-gated geometry conditioning，VRAG占据retrieval加global state；所以“保留source token”“做几何attention”“双记忆”“双路融合”“加source ID”或“加camera gate”任何单项都不新。只有**同一来源跨消费者provenance同步**能被F10/F01反事实识别、解释真实重访失败，并在强近邻上带来样本外收益时，才值得立为方法。若多edit/sham/自然return不支持，就删除C。

## 让结果真正有冲击力需要什么

老师会关注的不是名字，而是下面这种证据：

1. 一个强baseline在普通replay/return指标上看似成功，但合同显示某些selected sources没有真正影响输出，或影响落错位置，或有稳定负收益；
2. 这种错位不能由相机失从、随机seed、接口长度、attention、pose overlap、source quality、RoPE addressability或分布外删除解释；
3. 同一规律在独立scene和至少第二类memory consumer上复现；
4. 一个只看生成前信息的轻量策略能减少负收益，同时在相同覆盖率下优于TetherCache式策略和普通gate；
5. 全部失败案例、选择flow、效应量、风险覆盖和计算代价都公开，不只展示漂亮视频。

## 立即执行顺序

1. 完成C1数值相机守卫、盲评分与C2真实生成；它们决定有没有自然失败。
2. S48 V5与normative implementation必须先通过新鲜独立统计/因果审查；V1–V4的BLOCKED裁决不追认到新版本。
3. 只有自然失败和S48双门都通过，才运行一个CAL source的最小干预。
4. Influence、Localization、Benefit任一失败就收束或停止；不训练head。
5. Pilot存活才设计S49跨scene确认；确认后才决定论文是measurement/benchmark，还是benchmark+method。

## 当前可主张与不可主张

可以说：已经从近邻压力中得到一个架构限定、可被真实实验推翻的创新候选，并把它压成了严格的最小否证路线。

不能说：已经证明首创、已经有方法增益、已经达到PhD/CCF A水平、一定会让老师惊讶或一定录用。
