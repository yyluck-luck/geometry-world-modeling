# S41 第四轮根审：把“聚合替换”降级为真实消费者因果诊断

记录时间：2026-09-07（UTC；精确事件时间另见主账）。本轮问题固定为：在 VMem 已经选定同一批历史帧后，单个全局 CLIP 均值条件是否对回访输出有实际作用；若有，它是否保留历史来源与目标区域之间可定位的影响。当前没有真实 VMem 视频结果，因此本文只有源码事实、文献排重和预实验设计。

## 1. 三类证据不得混合

1. **本地固定源码事实。** `CLIPConditioner.forward` 调用 OpenCLIP `encode_image`，每帧得到一个全局向量；`get_cond` 对所选帧向量沿帧维求 mean，再复制为每个相机一个 K/V 长度为 1 的条件。
2. **外部研究意见。** Gemini 第四轮已经撤回其上一轮“直接按 Surfel mask CLIP token”的建议。该回答从可见网页文字人工转录，并非后端导出或实验。
3. **原论文边界。** 独立代理从正式会议页和论文检查了 VMem、WorldMem、WorldStereo、Spatia、Geometry-as-Context、PoCo、SPAD、EpiDiff 等。文献能否定普通方法包装，却不能证明本项目剩余问题首次提出。

## 2. 本地源码通路纠错

VMem 的条件不能笼统称为“latent concat + CLIP”。固定源码中四条路径是：

| 名称 | 实际内容 | 消费位置 |
|---|---|---|
| `crossattn` | 被选历史图的全局 CLIP 向量先求 mean，形成一个 token | 作为网络 `y` |
| `replace` | 历史帧 VAE latent 加一位 mask；目标位置为零 | 每次 denoising 前把 context 帧输入位置替换为固定 latent |
| `concat` | 输入帧 mask 与 Plücker 坐标 | 与 denoising input 按通道拼接 |
| `dense_vector` | Plücker 坐标 | 作为网络的 dense camera condition |

因此，后续对照应称“全局 CLIP 通路是否被 `replace` 历史 latent 和相机条件压过”，不能写成“concat latent 主导”。Surfel 在这段接口中负责检索历史 frame IDs；已核代码没有 Surfel 颜色到 CLIP patch 的映射，也没有可供逐 patch mask 的 CLIP token。

## 3. 近邻对宽泛方法的否决

| 最近工作 | 正式状态/原始入口 | 已经覆盖的机制 | 对本项目的裁决 |
|---|---|---|---|
| VMem | ICCV 2025；[CVF](https://openaccess.thecvf.com/content/ICCV2025/html/Li_VMem_Consistent_Interactive_Video_Scene_Generation_with_Surfel-Indexed_View_Memory_ICCV_2025_paper.html) | Surfel 索引历史视图、几何投票与 NMS 检索 | 必须先复现的直接基线 |
| WorldMem | NeurIPS 2025；[Proceedings](https://proceedings.neurips.cc/paper_files/paper/2025/hash/470629a47e2d65ce0606c40055df5d26-Abstract-Conference.html) | 绑定 frame/pose/time 的 token memory 与 state-aware attention | “保留来源状态再 attention”已有直接近邻 |
| Context-as-Memory | SIGGRAPH Asia 2025；[DOI](https://doi.org/10.1145/3757377.3763833) | 按 FOV 检索历史帧，并沿时间维直接拼入条件 | “不压缩、直接给历史帧”是强基线 |
| WorldStereo | CVPR 2026；[CVF](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_WorldStereo_Bridging_Camera-Guided_Video_Generation_and_Scene_Reconstruction_via_3D_CVPR_2026_paper.html) | 增量点云的 global-geometric memory；以 3D correspondence 限制 spatial-stereo attention 感受野 | 普通 geometry-guided local routing 被直接覆盖 |
| Spatia | CVPR 2026；[CVF PDF](https://openaccess.thecvf.com/content/CVPR2026/papers/Zhao_Spatia_Video_Generation_with_Updatable_Spatial_Memory_CVPR_2026_paper.pdf) | 可更新点云空间记忆、SLAM 更新、轨迹渲染条件 | 点云更新/投影条件不能作为新意 |
| Geometry-as-Context | CVPR 2026；[CVF](https://openaccess.thecvf.com/content/CVPR2026/html/Hu_Geometry-as-context_Modulating_Explicit_3D_in_Scene-consistent_Video_Generation_to_Geometry_CVPR_2026_paper.html) | 显式 geometry context 与 camera-gated attention | 给 query 加几何或普通 gate 不能作为新意 |
| PoCo | CVPR 2026；[CVF PDF](https://openaccess.thecvf.com/content/CVPR2026/papers/Huang_Rethinking_Position_Embedding_as_a_Context_Controller_for_Multi-Reference_and_CVPR_2026_paper.pdf) | 以 reference side information 的 RoPE 控制多参考关联 | source ID/tag/positional binding 已有直接压力 |
| SPAD / EpiDiff | CVPR 2024；[SPAD](https://openaccess.thecvf.com/content/CVPR2024/html/Kant_SPAD_Spatially_Aware_Multi-View_Diffusers_CVPR_2024_paper.html)、[EpiDiff](https://openaccess.thecvf.com/content/CVPR2024/html/Huang_EpiDiff_Enhancing_Multi-View_Synthesis_via_Localized_Epipolar-Constrained_Diffusion_CVPR_2024_paper.html) | Plücker/对极几何约束跨视图或局部特征 attention | 几何 attention 不是新的基本算子 |

此外，项目既有综述已核 AnchorWeave 的多局部几何记忆、多 anchor controller 和 pose-guided fusion，MosaicMem 的三维 patch 与对齐读出，LSM-World 的 latent 三维缓存。它们继续压缩“把多个历史条件融合得更好”这一宽泛故事的空间。

**立即否决：** mean→learned attention、router、加权和、source tag、epipolar mask、point-cloud update 或 camera gate 都不能作为论文主创新。将多个已有模块组合进 VMem 也不会自动产生实质创新。

## 4. 只保留一个可证伪问题

> 在完全固定 Surfel 检索结果、逐帧 latent、相机条件、随机噪声和采样过程后，VMem 的单个全局 CLIP token 是否对真实回访内容有可测的因果影响；若有，某一历史来源的条件变化是否主要影响它在几何上支持的目标区域，而非无差别改变整幅画面？

这是 **memory-consumer sufficiency / addressability audit** 的候选问题，目前仍是基线诊断。它不等价于“mean 一定有害”，也不等价于“局部路由就是新方法”。

## 5. 分阶段的最小决策树，先用便宜门杀死假说

### Gate 0：必须先有真实自然失败

- 完成 S39 组件冻结和真实加载；保存 exact weight hashes。
- 执行 S40 原设置两批生成，核第一批 `samples_z` 真正进入第二批历史缓存。
- 在未看聚合替代结果前，冻结自然发生的回访失败、目标区域、场景、轨迹和 seed。
- 若原 baseline 不出现稳定目标失败，停止本方向，不人工制造成功案例。

### Gate 1：CLIP 通路影响门

只跑两臂：A0 exact mean replay；A1 zero CLIP。两臂保持相同历史 IDs/顺序、`replace`、`concat`、`dense_vector`、noise tensor、sampler/CFG/steps、模型和 VAE。A1 故意删除信息，因此不是同信息性能比较，只是因果负对照。

- A0 不能逐值复现原 baseline：先修接线，停止科学分析。
- A1 与 A0 在预注册容差内没有输出差异：没有证据表明 CLIP 通路影响当前失败，停止 mean 路线。

Gate 1 必须分开两个判断：

1. **Influence。** 配对的 A1−A0 输出差异超过 exact-replay 容差，只说明 crossattn 对输出有影响。
2. **Failure relevance。** 只有 A1−A0 同时让预注册回访区域的主结果超过预注册容差，才进入 A2–A5；必须报告变化方向，以及相机服从和整体质量是否付出代价。若变化仅是全局色调或风格，停止局部身份/mean 分支。

A1 若改善，只能暂时指向“当前全局 CLIP 条件的存在或内容可能有害”；它不能单独把问题归因到算术 mean。

### Gate 2：A2–A5 普通强基线

Gate 1 通过后，固定六臂标签：A2 最近视角单向量、A3 最远视角单向量、A4 CLIP medoid、A5 Surfel 票权 mean。所有替代向量匹配原 mean 的 L2 范数，均只使用固定的 K 个历史候选和输出前可得信息，不用 GT 或生成结果选权。A0–A5 共享同一冻结上游候选池、同一单 token 输出接口与同一下游生成预算；各臂实际交付给 denoiser 的信息有意不同，必须逐臂披露。

可按解释分为 Gate 2a（A2/A3，检验目标相关方向）与 Gate 2b（A4/A5，检验稳健集合代表与几何加权）。但 Gate 1 一旦通过，完整的“聚合是否为主因”审计必须覆盖 A2–A5：A2 失败不能跳过 A4，A2/A4 失败也不能跳过 A5，因为三者检验不同解释。

- A2 与 A3 相近：更像任意向量扰动，不支持目标相关绑定，但不终止 A4/A5。
- A2–A5 中任何普通臂已稳定解决：它成为更强 baseline，不能称创新。
- A1 不改善预注册失败，且 A2–A5 也无跨场景、跨配对 seed 的稳健改善：没有证据表明 mean 是主要原因。
- A1 改善而 A2–A5 均不改善：只能说当前全局 CLIP 条件可能有害；算术 mean、CLIP 编码器的全局粒度与整条 crossattn 通路仍互相混淆。
- A1 使预注册失败更坏，且 A2–A5 也无改善：当前 CLIP 条件对该结果有用，拒绝“有害 mean”故事。
- 改善只出现在开发场景、范数不匹配设置或牺牲相机服从/视觉质量：拒绝中心解释。

不把 `[N,1024]` 多 token sequence 放进主矩阵：它改变 K/V 长度与计算；发布的 checkpoint/interface 只验证了 mean 后单 token 路径，未找到发布的训练证据表明模型适配过 K/V 长度大于 1。因此它是未经验证且很可能分布外的结构干预，失败或成功都会混入接口改变。无关场景向量也只可作额外 sanity check，不能代替同候选池对照。

## 6. 满足进入条件后，转入 source-to-region 消费者诊断

进入本节必须同时满足：已经核验一个真实自然失败；A0 可逐值复现；Gate 1 对冻结回访结果有相关而非仅全局风格的效应；并且至少一个预注册的来源相关 contrast 仍不能由整体质量或相机服从代价解释。这里允许 A2–A5 没有形成性能改善，因为本节是**消费者诊断分支**，不是方法 headroom 或性能方法开发。

先选择一个**真实观测来源** `i`，并在看目标输出或 GT 前冻结同一幅源图的反事实 `I_i -> I_i_cf`。首轮只允许在保存的 source mask 内做预注册的局部 appearance-only 或 photometric edit，必须保持相机、场景几何、可见支持和检索 IDs 不变；保存原图、反事实图和 edit mask 的 SHA、编辑过程与参数，以及生成前定义的几何稳定检查。会改变几何或支持区域的编辑只能标为压力测试，且不得沿用原 `M_i` 做定位。

第一项干净测试不得使用生成来源：真实观测的 `replace` latent 是该图经 VAE 编码所得；生成来源保存的是 sampler 返回的 `samples_z`，把其解码帧重新编码会改变 latent provenance，不能悄悄当成配对干预。若以后研究生成来源，只能把预先声明的 delta-transfer 构造标为压力测试，并单独报告。

用同一图像反事实做小型 2×2 分支归因，复用 A0：

| 条件 | 来源 `i` 的 CLIP embedding | 来源 `i` 的 `replace` latent | 身份 |
|---|---|---|---|
| F00 | 原图 | 原图 | A0 原条件 |
| F10 | 反事实图 | 原图 | CLIP-only 干预 |
| F01 | 原图 | 反事实图 | replace-only 干预 |
| F11 | 反事实图 | 反事实图 | 两条 appearance 路径同时干预 |

F10/F01 故意让两条 appearance 路径接收互相矛盾的同一来源版本，因此只作 branch-response 干预，不是性能 baseline；大伪影可能来自跨条件冲突。F11 才是协调一致的图像反事实。一个分支效应只有在两个或以上预注册的低强度反事实中重复出现、方向/定位一致且与 F11 一致时，才可进入解释。

四项都保持正确 pose/K、`concat` 与 `dense_vector` 中的两份 Plücker、其余来源、mask、noise、RNG、sampler、权重和评估代码不变。必须保存两条条件空间中的实际 delta；因为 CLIP 与 latent 的编码器、维度和扰动能量不同，禁止用未经归一化的标量效应大小给两条通路排名。

对每个事前固定方向的标量结果 `Y`，交互定义为：

`Interaction_Y = (Y11 - Y01) - (Y10 - Y00) = Y11 - Y10 - Y01 + Y00`。

若报告空间交互图，必须先在一个固定的有符号输出或特征表示中做同一 factorial contrast，再取范数；不得事后把非负距离图直接相减来声称互补或冗余。

对固定来源 `i`，预先由预测几何得到其目标支持区域 `M_i`。对 F10、F01、F11 的每个配对 contrast，以输出距离图 `D_i(p)` 记录效应，并报告：

`Localization(i) = sum_{p in M_i} D_i(p) / (sum_p D_i(p) + eps)`。

必须同时报告支持区和非支持区的绝对效应，避免分母很小时比例虚高。该量只描述条件干预的输出响应，不是神经元归因、Shapley 贡献或真实因果世界效应。识别依赖以下假设：

1. 生成在固定 noise 和状态下可重复；
2. 每一分支干预只进入表中声明的 appearance 条件；
3. `M_i` 在看输出之前由固定预测几何构造；
4. 没有跨臂隐藏缓存污染；
5. 解码与指标不会把轻微全局色调变化误判为局部身份恢复。

若 CLIP-only 只造成全局风格变化、可定位性不能预测自然失败，或结果只复述几何支持率/全局 CLIP 距离，候选 benchmark 也应停止。若可跨 VMem 与另一公开 memory consumer 重现，才有资格讨论“新问题/诊断协议”；若随后提出方法，还需与 WorldStereo、WorldMem、Context-as-Memory、PoCo、AnchorWeave、普通 router/gate 做同信息或清楚披露信息差异的强对照。

### 可选绑定压力测试，不进入 A0–A5 主矩阵

- `S_Rperm`：只在历史槽之间按固定循环置换四个 latent 通道，保留 `replace` mask。它破坏图像—相机与图像—时间的联合对应，只能说明输出对这种矛盾或槽位绑定是否敏感；大效应不能证明 `replace` 主导，零效应也不能证明 `replace` 未使用。
- `S_Pperm`：若置换历史相机条件，必须在 `concat` 和 `dense_vector` 中同时置换 Plücker，并在 conditional `c` 与 unconditional `uc` 两支保持一致；各自的 concat mask 通道不变。
- `S_RPperm`：可选地用同一固定置换同时移动 latent 和两份 Plücker，用来三角分析 appearance–geometry 配对与槽位效应。

三项都属于分布外 correspondence stress，不是普通 baseline，不具备联合意义上的同信息公平性，也不能用于给 crossattn、replace 与 Plücker 三条路径排“谁主导”。

## 7. 当前裁决

- **方法裁决：Reject and Pivot。** Gemini 提议和最自然的替换均被接口事实或近邻工作压死。
- **问题裁决：Accept with Revisions。** 消费者充分性与 source-to-region 反事实定位可以调查，但必须先通过真实 baseline、自然失败和 Gate 1。
- **证据状态：0 次模型加载、0 个真实生成视频、0 项性能改善。** S39 attempt4 的运行状态由其独立回执记录，本文件不把下载进度算作实验。

配套证据：[第四轮提示](prompt_4.md)、[可见回答转录](response_4_visible.md)、[第三轮独立核验](independent_verification.md)、[独立创新审查](../S41_clip_mean_innovation_audit/AUDIT.md)、[既有综述](../../docs/LITERATURE_SYNTHESIS_V2.md)。
