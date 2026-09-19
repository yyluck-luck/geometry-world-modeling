# Provenance-Coupled Dual-Path Memory：条件式创新生死卡 V1

- 建立时间：2026-09-08（Asia/Shanghai）
- 状态：`CONDITIONAL_HYPOTHESIS_NOT_IMPLEMENTED_NOT_VALIDATED`
- 当前新颖性授权：`NONE`
- 适用范围：显式检索、source ID稳定、semantic与latent等appearance consumer均可枚举的生成世界模型
- 证据边界：来自固定VMem源码静态审计、S48因果协议和一手论文；没有新增模型运行，没有读取C1/C2 pixel，没有方法增益

## 给新手的一句话

VMem当前像是把四位证人的“文字证词”先平均成一句话，却把他们的“照片证据”分别保留；如果两条路径不知道同一条信息来自谁，生成器可能把正确记忆用错位置。候选方法让每条来源在语义与潜变量两条路径中使用同一来源身份和几何权重，并在证据显示某条记忆有害时拒绝或重新观察。

## 1. 已观察事实与待检验缺口

固定`vendor/vmem_snapshot/modeling/pipeline.py` SHA `90a45f45...d7e`的静态AST证据显示：

1. ordinary retrieval仍保留`context_time_indices`与slotwise `context_latents`；
2. `get_cond`中的`replace`路径保留latent结构；
3. `context_encoder_embeddings`在`pipeline.py:1124`沿source维全局求均值后广播；
4. 当前API不返回逐source target support，真实consumer hook尚未实现。

前三项形成**consumer-asymmetry假设**，不等于它已造成错误。S48的F10/F01/F11、sham、negative和positive control专门判断：单独改变semantic或latent路径是否制造冲突，而全路径同源改变是否得到不同响应。

## 2. 条件式方法定义

设普通运行选中来源`k=1...K`，其semantic token为`E_k`，latent为`L_k`，对target像素或token `q` 的干预前fractional geometry provenance为`W_{k,q}`。

原baseline semantic路径近似使用：

`E_bar = mean_k E_k`。

候选方法不先求全局均值，而是保留`{E_k}`，并从同一个冻结provenance对象产生归一化权重：

`alpha_{k,q}=Normalize_k(g(W_{k,q}, address_k, quality_k))`。

同一个`alpha`同时约束：

1. semantic cross-attention中每个来源的K/V贡献；
2. latent/replace路径中相同source slot的贡献；
3. 可选的`accept / reject / re-observe`动作。

训练版只能在后续跨scene实验中使用S48/S49定义的source-level signed Benefit作离线教师。推理时不得读取未来reference或生成后指标。gate结构、geometry attention、per-source token和选择性预测本身都不是新意；候选贡献只能来自**同一来源跨consumer的provenance一致性约束，以及该约束与真实signed utility的因果连接**。

## 3. 可推翻预测

| 编号 | 冻结预测 | 失败时的动作 |
|---|---|---|
| P0 natural failure | C1/C2及新增scene先出现相机服从、可重复的真实重访失败 | 没有失败则停止本路线，不制造问题 |
| P1 path conflict | 在失败unit中，F10/F01至少一条显示超过controls的响应，且两路径effect map方向/位置不一致；F11恢复同源干预后不一致下降 | 没有可复现冲突则删除dual-path机制故事 |
| P2 provenance localization | F11响应在逐actual-target geometry expected locus上同时超过面积、`G_shape`和`G_camera`；source purity足够时再超过`G_source` | 不局部则不使用geometry provenance作方法核心 |
| P3 signed utility | 对同步独立真实reference，selected source在不同scene同时存在稳定正/负Benefit差异，生成前特征可预测符号 | Benefit恒正、恒零或不可测则不训练acceptance策略 |
| P4 method increment | 完整coupling在held-out scenes的全体paired loss与risk–coverage上优于容量匹配per-source tokens、geometry-attention、普通gate、WorldStereo/Spatia式最接近实现 | 仅增加token或geometry即可解释时，不主张新机制 |
| P5 outside safety | support外画质、相机服从、运动与动态生成不劣于预注册margin | 只改善局部却损害全局时判失败 |

## 4. 必须做的容量匹配机制矩阵

| Arm | Per-source semantic | Geometry provenance | Semantic/latent共享权重 | Signed-utility action | 用途 |
|---|---:|---:|---:|---:|---|
| M0 VMem | 否，全局均值 | 检索有 | 否 | 否 | 原baseline |
| M1 token capacity | 是 | 否 | 否 | 否 | 排除“只是token更多” |
| M2 geometry semantic | 是 | 是 | 否 | 否 | 对齐WorldStereo/I3DM式几何attention |
| M3 shared coupling | 是 | 是 | 是 | 否 | 检验跨consumer provenance同步 |
| M4 full candidate | 是 | 是 | 是 | 是 | 检验有害来源拒绝/重观察 |
| M5 oracle upper bound | 是 | 是 | 是 | 使用真实Benefit | 只给headroom，不是可部署方法 |

所有arm必须保持backbone、训练数据、参数增量、token预算、采样器、seed、camera path和计算预算可比。M5永久标为oracle。

## 5. 与最新直接近邻的边界

| 近邻 | 已覆盖 | 本候选仍需证明的额外信息 |
|---|---|---|
| [VMem, ICCV 2025](https://openaccess.thecvf.com/content/ICCV2025/html/Li_VMem_Consistent_Interactive_Video_Scene_Generation_with_Surfel-Indexed_View_Memory_ICCV_2025_paper.html) | surfel-indexed view memory与目标可见性检索 | 已选source跨consumer的身份同步是否解决真实失败 |
| [SPMEM, NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/467655d26fcc207bca08915dc91964c6-Abstract-Conference.html) | static spatial、recent working、historical episodic多路memory | 不是多路条件数量，而是同一source provenance是否在消费者间一致 |
| [Spatia, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/papers/Zhao_Spatia_Video_Generation_with_Updatable_Spatial_Memory_CVPR_2026_paper.pdf) | point-cloud projection、reference、preceding-video多条件；reference-only局部负例 | 对单条来源做控制校准反事实并以同步reference定signed Benefit |
| [WorldStereo, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_WorldStereo_Bridging_Camera-Guided_Video_Generation_and_Scene_Reconstruction_via_3D_CVPR_2026_paper.html) | 3D correspondence限制memory attention receptive field | 同一source权重跨semantic与latent消费者同步，并经F10/F01识别 |
| [PlenopticDreamer, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/papers/Fu_Plenoptic_Video_Generation_CVPR_2026_paper.pdf) | 3D-FoV多历史视频检索、渐进context、self-conditioning | 不是再做FoV检索，而是判断已检索item是否有局部且有益的因果作用 |
| [LongDiff, CVPR 2025](https://www.openaccess.thecvf.com/content/CVPR2025/papers/Li_LongDiff_Training-Free_Long_Video_Generation_in_One_Go_CVPR_2025_paper.pdf) | attention信息稀释及informative frame selection | 固定source集合后，VMem跨consumer provenance丢失是否是不同且可复现的根因 |
| [Dual-Granularity Memory, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Wang_Dual-Granularity_Memory_for_Efficient_Video_Generation_CVPR_2026_paper.html) | chunk内context memory与跨segment latent context memory协同，目标是高效长视频生成 | “dual memory/局部+全局路径”已被占据；本候选必须用source-level反事实证明跨consumer身份失配及共享provenance的增量 |
| [Movie Weaver, CVPR 2025](https://openaccess.thecvf.com/content/CVPR2025/papers/Liang_Movie_Weaver_Tuning-Free_Multi-Concept_Video_Personalization_with_Anchored_Prompts_CVPR_2025_paper.pdf) | anchored prompt与concept embedding显式绑定概念、参考图和参考顺序 | source tag、reference order与concept-image linkage已被占据；M1必须包含这一类来源编码，PC-DPM只能主张ordinary retrieval中的跨consumer共享provenance及其因果增量 |
| [Video Alchemist, CVPR 2025](https://openaccess.thecvf.com/content/CVPR2025/papers/Chen_Multi-subject_Open-set_Personalization_in_Video_Generation_CVPR_2025_paper.pdf) | image-index embedding区分参考来源，personalization与text用分离cross-attention | per-reference token/分路attention是M1/M2强基线；共享provenance必须提供超出身份token的增量 |
| [Saber, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/papers/Zhou_Scaling_Zero-Shot_Reference-to-Video_Generation_CVPR_2026_paper.pdf) | reference-video attention mask及多identity/multi-view reference扩展 | source-aware mask已被占据；本候选须证明ordinary memory跨consumer失配和signed utility，不是一般多参考绑定 |
| [Structural Video Diffusion, ICCV 2025](https://openaccess.thecvf.com/content/ICCV2025/html/Wang_Multi-identity_Human_Image_Animation_with_Structural_Video_Diffusion_ICCV_2025_paper.html) | identity-specific embeddings加depth/surface-normal结构条件 | M2必须包含“per-source embedding+geometry”直接对照 |
| [Geometry-as-context, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Hu_Geometry-as-context_Modulating_Explicit_3D_in_Scene-consistent_Video_Generation_to_Geometry_CVPR_2026_paper.html) | Plucker-ray camera-gated self-attention与显式geometry context | M2还必须包含camera-conditioned geometry gate；“相机门控”不能解释为本候选贡献 |
| [VRAG, NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/e32310c3acb058d563a6a9e54d0e9000-Abstract-Conference.html) | video retrieval加显式global-state conditioning，区分memory不足与不可约自回归累积误差 | 失败归因必须有no-memory/global-state/retrieval强对照；不能默认全部长期漂移都来自source provenance |
| I3DM / TetherCache / CUE-R | 3D注入、可信对齐、逐item utility干预 | 三者都必须进入强对照；联合因果合同不能靠组件拼接自动获得新颖性 |

## 6. Idea-evaluator五维裁决

| 维度 | 当前分数（5分制） | 理由 |
|---|---:|---|
| Higher | 3 | 若能把来源级因果链变成新的评价对象与机制解释，知识增量可能较高；当前无实证 |
| Faster | 1 | per-source token通常增加计算，本方向不以速度为主要贡献 |
| Stronger | 3 | 有机会同时改善重访一致性与可解释失败定位；必须胜过容量/几何强对照 |
| Cheaper | 2 | 轻量adapter可能便宜，但离线因果教师很昂贵 |
| Broader | 2 | 原理可扩展到显式retrieval模型，但当前只对consumer可枚举架构成立 |

**当前裁决：`KEEP_CONDITIONAL_FOR_KILL_EXPERIMENT_ONLY`。** 分数不是成果评级；P0–P3任何一项失败，都应停止或改写问题。

## 7. Fatal-flaw audit

1. 全局semantic mean可能是合理scene summary，source identity只需由latent路径承载；静态不对称可能完全无害。
2. F10/F01是人为路径冲突，可能离开自然分布；必须由两edit family、sham、negative、positive和自然失败约束。
3. geometry expected locus不是denoiser真实pixel routing；即使局部化通过，也不能写成内部attention ground truth。
4. 当前C1/C2没有同步独立reference，Benefit可能根本不可执行；必须收集或使用合资格的新多相机scene，不能拿ID0顶替。
5. Spatia、WorldStereo、Dual-Granularity Memory、Movie Weaver、Video Alchemist、Saber、Geometry-as-context、VRAG或后续工作可能已经通过不同术语实现等价耦合；投稿前必须再次扩展引用网络并核源码。
6. 本机CPU可完成小pilot，不足以承诺训练大模型；应先用冻结backbone和小adapter验证机制，再决定外部算力。

## 8. 决策顺序

1. 先完成C1数值守卫/盲评分与C2真实baseline；
2. 只在自然失败出现后，让S48协议通过fresh review并实现最小observer/replacement hook；
3. 先判P1–P3，不写训练代码；
4. P1–P3跨scene成立后，另立确认与方法协议，执行M0–M5矩阵；
5. 只有held-out增量、全局安全和最新近邻排重同时通过，才允许将PC-DPM写成方法贡献。
