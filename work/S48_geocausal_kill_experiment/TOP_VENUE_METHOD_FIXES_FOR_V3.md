# S48 V3：顶会与统计一手来源驱动的方法学修复包

- 角色：独立方法学／统计／因果代理；本文件不是作者回应，也不是执行授权
- 完成时间：2026-09-08 14:28 CST（UTC+08:00）
- 直接输入：`INDEPENDENT_STATISTICAL_REVIEW_V2.md`（whole-file SHA-256 `3470ae9a421bc3b8ce916b8e6959d36d49e1ccc9f12e7002e841fdd22ff1b372`）
- 被修复的 V2 草案：archive SHA-256 `ef92be76a8f8f2d6cd6fe70e629f77114751d9ed2a05228618038087e6fda92d`
- 检索期间只读观察到的 V3 草案快照 SHA-256：`02f3be4120ba4c7ee7da719313c1d430d133185cafbe56bb80eea3788b5896c1`；本文件不构成对该快照的 fresh review
- 只读源码：`vendor/vmem_snapshot/modeling/pipeline.py`，SHA-256 `90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e`
- 对照源码：`work/S20_environment/isolated_vmem_source/modeling/pipeline.py`，SHA-256 `680da1c14db8a6780a37fca3a8bac5bb59f0aa7d395db96d4360b352eb7f2255`；两者仅见 device-default 修补差异，本报告的方法判断绑定前者
- 边界：只读项目文字、源码结构与论文；未运行或导入模型；未打开、解码或检查 C1/C2 tensor、image、pixel；未修改任何 S48 预注册草案
- 本文件自身 canonical SHA-256（删除本字段所在整行后计算）：`a86b8c66d042b0817e5a36cc6e7d019662e08433072fcbcb0979e5e1c1aa1a99`
- **方法包裁决：PASS_TO_DRAFT；S48 执行状态：BLOCKED_PENDING_IMPLEMENTATION_AND_FRESH_REVIEW**

## 1. 需要冻结的五个决定

1. **matched masks 走描述性困难对照路线。** 不再把 199 个 mask 的排名叫 p 值，也不把不同生成机制混成一个“零分布”。形状位置、相机几何、其他来源是三个不同问题，必须逐族报告。
2. **support 是干预前、目标视角下的几何预期作用区。** 当前 VMem 用 surfel 投影来选整帧上下文，并没有把 appearance 按像素路由到消费者。因此 support 与 effect 对齐可以支持“geometry-aligned downstream effect”，不能单独证明“像素级 memory routing”。
3. **当前源码每个 arm 都新进程。** 内置 `reset()` 没有清空实际使用的多项状态；相同 seed 也不等于相同随机输入。每个 arm 必须从同一只读快照和同一个已物化 noise tensor 启动。
4. **Benefit 只在预先冻结的多视角 common-visible support 上计分。** 该区域由相机、深度、surfel、双向重投影和遮挡决定，不能用任何 arm 输出优化配准或挑区域。
5. **两个 edit family、正负 dose、两个 seed 形成唯一的合取门。** 先对正负 dose 的绝对 effect map 求平均；每个 family×seed 分别过门；pilot 的 unit 摘要取最弱一项，不能挑最好的一项。

## 2. 一手来源核验与它们实际支持的结论

证据等级：A 为正式同行评审顶会或统计期刊原文；B 为官方框架文档；C 为尚未确认顶会录用的预印本，只用于近邻边界。

| 来源 | 等级 | 原文可支持的结论 | 不能从该来源推出的结论 |
|---|---|---|---|
| [Hemerik & Goeman, Exact testing with random permutations, TEST 2018](https://link.springer.com/article/10.1007/s11749-017-0571-1) | A | 随机置换检验的有效性来自零假设下的变换不变性与群结构；identity、inverse、closure 是关键结构 | 任意生成 199 个相似 mask 就自动得到 0.05 级别的 p 值 |
| [Phipson & Smyth, Permutation P-values Should Never Be Zero, 2010](https://gksmyth.github.io/pubs/PermPValuesPreprint.pdf) | A | 在有效的置换／Monte Carlo 机制内，观察值计入分母可避免零 p 值并给正确离散尾部 | `+1` 可以修复一个本来就没有可交换 assignment 的 mask library |
| [Mrkvička et al., Revisiting the random shift approach, Spatial Statistics 2021](https://www.sciencedirect.com/science/article/pii/S2211675320300245) | A | 空间检验要求统计量序列可交换；torus shift 破坏空间相关时会产生 liberal test | 图像中的刚性平移、旋转或 wrap-around 可默认视为有效置换 |
| [I²AM, ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/c4a59e985de8b134328f41a47bc7dfac-Abstract-Conference.html) | A | 图像到图像扩散可用双向 attribution 和 mask alignment 评价；论文把随机 10%–30% box 当比较基线 | 随机区域比较被该论文校准成随机化显著性检验；它没有这样主张 |
| [VMem, ICCV 2025](https://openaccess.thecvf.com/content/ICCV2025/html/Li_VMem_Consistent_Interactive_Video_Scene_Generation_with_Surfel-Indexed_View_Memory_ICCV_2025_paper.html) | A | surfel-indexed view memory 用 3D surface observation 来检索相关历史视图 | surfel provenance 等于生成器内部逐像素 appearance routing |
| [MVSNet, ECCV 2018](https://openaccess.thecvf.com/content_ECCV_2018/html/Yao_Yao_MVSNet_Depth_Inference_ECCV_2018_paper.html) | A | 多视图比较应先把视图投到共同 reference-camera frustum | 只凭 pose 接近就可以直接逐像素计算 RGB MSE |
| [Xu & Tao, Multi-Scale Geometric Consistency Guided MVS, CVPR 2019](https://openaccess.thecvf.com/content_CVPR_2019/html/Xu_Multi-Scale_Geometric_Consistency_Guided_Multi-View_Stereo_CVPR_2019_paper.html) | A | forward/backward reprojection consistency 可筛选可靠多视图对应 | 本项目的 `1 px`、`2% depth` 是该论文给出的通用真理 |
| [Monodepth2, ICCV 2019](https://openaccess.thecvf.com/content_ICCV_2019/html/Godard_Digging_Into_Self-Supervised_Monocular_Depth_Estimation_ICCV_2019_paper.html) | A | minimum reprojection 与 auto-masking 用来处理遮挡和违反相机运动假设的像素 | 遮挡像素可以与可见像素一起进入主 photometric loss |
| [OCAI, CVPR 2024](https://openaccess.thecvf.com/content/CVPR2024/html/Jeong_OCAI_Improving_Optical_Flow_Estimation_by_Occlusion_and_Consistency_Aware_CVPR_2024_paper.html) | A | forward/backward consistency、occlusion awareness 和 hole handling 应显式进入跨视图评价 | warping holes 可被普通插值后当真实观测评分 |
| [Zhang & Nanda, Activation Patching Best Practices, ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/06a52a54c8ee03cd86771136bc91eb1f-Abstract-Conference.html) | A | corruption 与评价 metric 的选择会显著改变 localization 结论 | 看见一次 intervention response 就足以断言 faithful mechanism |
| [Makelov et al., Interpretability Illusion, ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/70b8505ac79e3e131756f793cd80eb8d-Abstract-Conference.html) | A | naïve patching 可激活 dormant parallel pathway，造成看似正确的端到端效应 | 单一强 edit 或 positive response 足以排除 intervention artifact |
| [Kleijnen, Common Random Numbers, Management Science 1988](https://pubsonline.informs.org/doi/abs/10.1287/mnsc.34.1.65) | A | common random numbers 会造成配对依赖，应按配对／协方差结构分析，且仍需要独立 replication | 两个共享 noise 的 seed 可当两个独立 scene |
| [Agarwal et al., Statistical Precipice, NeurIPS 2021](https://proceedings.neurips.cc/paper/2021/hash/f514cec81cb148559cf475e7426eed5e-Abstract.html) | A | 少量 runs 的点估计可能给出不可靠结论，应报告不确定性和稳健聚合 | 在一个 scene 上增加 seeds 就能得到总体泛化结论 |
| [Berger, Multiparameter Hypothesis Testing, Technometrics 1982](https://www.tandfonline.com/doi/abs/10.1080/00401706.1982.10487790)；[Eaton & Muirhead, Multiple Endpoints, 2007](https://www.sciencedirect.com/science/article/abs/pii/S0378375807001061) | A | 当科学 claim 要求所有端点都成立时，每个端点都通过的 intersection–union 逻辑与 claim 对齐 | 在 “任意一个 edit 成功” 的 claim 下不做 multiplicity 控制 |
| [Bouthillier et al., ICML 2019](https://proceedings.mlr.press/v97/bouthillier19a.html)；[Pineau et al., JMLR 2021](https://jmlr.org/papers/v22/20-303.html) | A | 数值可重复与研究发现可复现不同；代码、数据、方差源和实验流程都要保存 | bitwise replay 可以替代新 scene confirmation |
| [PyTorch deterministic algorithms](https://docs.pytorch.org/docs/main/generated/torch.use_deterministic_algorithms.html)；[PyTorch randomness note](https://docs.pytorch.org/docs/stable/notes/randomness.html) | B | deterministic mode 可在无确定实现时抛错；该设置本身仍不足以保证完整复现 | 只设一个 seed 就能保证跨进程、跨版本和跨硬件完全相同 |
| [I3DM, 2026 preprint](https://arxiv.org/abs/2603.23413)；[AGRA, 2026 preprint](https://arxiv.org/abs/2606.12217) | C | 3D-aware retrieval、reliable warp region、空间因果扰动已是直接近邻压力 | 可把它们写成已通过顶会同行评审的基线，或把 geometry support 本身称作本项目创新 |

上述论文支持的是设计原则。`K=199`、`0.70 coverage`、`1 px`、`2% depth`、`0.02 localization SESOI` 等具体数值仍是**项目选择**，必须由独立 CAL 或科学容忍度冻结，不能声称由某篇顶会论文规定。

## 3. 修复一：把 matched masks 变成三个分开的描述性困难对照族

### 3.1 为什么不能保留随机化 p 值

V2 的真实 support 是普通运行选择后确定的，而假 mask 来自其他来源投影、刚性空间变换和伪相机三种机制。真实 support 没有从同一 assignment mechanism 中被随机抽中；三类候选也不共享同一个科学零假设。面积、边界、质心、深度等 caliper 只能增加“像不像”，不能建立零假设下的 exchangeability。

`(1 + #extreme)/(K+1)` 只在有效随机化结构里校正离散尾部。`K=199` 只让最小可能值成为 `1/200=0.005`。它不证明 type-I error 控制。空间图像还明显非平稳，边缘、物体、遮挡和画面边界都会让平移后的 mask 与原 mask 分布不同。

### 3.2 推荐直接写入 V3 的规范条款

> **Matched-placebo 定义。** 本 pilot 不实施随机化检验。所有 placebos 只构成预先规定的描述性困难对照，不给 p 值、alpha、显著性或零分布解释。三个生成族分别回答不同问题，禁止混成一个 library 或在族之间补足数量：
>
> 1. `G_shape`：对真实 support 作预冻结的无 wrap 刚性平移／旋转；越界像素直接使候选失格，不做 torus wrap；
> 2. `G_camera`：用预冻结的伪 target cameras 在同一 576×576 canvas 上重新渲染同一份干预前 surfel/provenance；
> 3. `G_source`：在真实 target camera 下渲染所有通过资格门的未选 source supports。
>
> `G_shape` 与 `G_camera` 各要求 `K_g=199` 个唯一候选。`G_source` 使用全部合格未选来源，不抽样、不复制；其数量单独报告。每族的 proposal grid、参数、遍历顺序、去重键、calipers、tie-break、seed（如仍需抽样）和不足动作都在任何 intervention output 前冻结并 hash。任何一族都不得用另一族的候选补到 199。
>
> 所有 matching covariates 只来自 source、普通 selection、相机和干预前 geometry。禁止读取 A0/F00/F11、reference photometric error 或 Benefit outputs 来生成、筛选、重排候选。生成器先保存 proposal 数、重复数、各 caliper 拒绝数、接受率、最终 mask 数、完整有序 ID 列表和 artifact SHA。
>
> 主 support 若采用 `[0,1]` fractional provenance 权重，则三个 placebo families 也必须生成同域权重图，不能拿 binary placebo 与 weighted true support 比较。对权重图 `W` 定义
>
> `area(W)=Σ_{p∈Ω}W(p)/|Ω|`，
>
> `mass_{f,s,t}(W)=Σ_{p∈Ω}W(p)d_{f,s,t}(p)/[Σ_{p∈Ω}d_{f,s,t}(p)+eps]`。
>
> 刚性变换必须携带原权重值；camera/source placebos 用同一个 fractional provenance 规则重新计算权重。连通分量与周长在预冻结的 `1{W>0}` 上计算，同时匹配 `ΣW` 和冻结的 weight-histogram distance。若选择 binary-union 作为主分析，则真实 support 与所有 placebos 都必须统一二值化，并把 fractional 结果降为 sensitivity。
>
> 对每个 edit family `f`、paired seed `s`、target frame `t` 和 placebo family `g`，在相同 effect map 上定义
>
> `L^g_{f,s,t}=mass_{f,s,t}(S_t)-median_{M∈G_g}mass_{f,s,t}(M)`，
>
> `r^g_{f,s,t}=[1+Σ_{M∈G_g}1{mass(M)>=mass(S_t)}]/[1+|G_g|]`。
>
> `r^g` 只叫 finite-library descriptive tail rank。它没有概率校准。`G_shape` 和 `G_camera` 必须分别达到预冻结的 `L^g` 与 top-tail 门，不能用 pooled rank。`G_source` 报告真实 support 相对全部合格未选-source supports 的序位；若数量太少而不能形成预注册尾部，要求真实 support 严格超过每个合格 source placebo，并明确候选数。没有合格 `G_source` 时，允许保留“geometry-aligned”结果，但 selected-source-specific localization 记为 `NOT_IDENTIFIABLE`。
>
> 每个 `f×s` 都须同时通过面积门、`G_shape` 门和 `G_camera` 门。若主张 selected-source-specific localization，还须通过 `G_source` 门。mask、seed、pixel 和 frame 都是技术重复，不增加科学 `n`。

### 3.3 generator 的确定性实现合同

- 先按固定参数网格**枚举**，再按 `(matching_distance, family_parameter_tuple, mask_sha256)` 词典序选前 199；这样比“不断随机采到 199 个”为何入选更可复算。
- 如果候选空间太大而必须 subsample，先冻结 PRNG 算法、seed、proposal 上限和完整 draw order；不得在失败后换 seed。
- 主 calipers 可保留面积、连通分量、尺度归一化周长、质心格、低 IoU、深度、深度梯度、投影置信和边界密度；每项都必须给公式、单位、闭区间方向以及 NaN/empty 行为。
- weighted 主分析还必须匹配有效权重总和与 weight histogram；否则 null maps 可能只因更稀或更弱而更难收集 effect mass。
- `G_camera` 的 pose delta 必须成对、单位明确，并固定投影到 actual-target canvas 的方法。伪相机只改变 mask，不改变 effect map。
- 所有 masks 在任何 F11 输出产生前 seal；artifact 后续只读。若 mask SHA、顺序或数量漂移，整个 RQ2 invalid。

### 3.4 只有坚持 p 值时才允许的备选路线

若未来必须给 randomization p，需另立设计并同时满足：有限变换集合 `G` 包含 identity、inverse 和 closure；在 `H0` 下完整 effect field 对 `G` 分布不变；observed placement 是 `G` orbit 的一个等概率成员；统计量和所有 conditioning 在 assignment 前固定；任何 outcome-informed caliper 禁止；抽样方式包含 identity 并按有效随机置换公式计算。只要场景语义、边界、遮挡或空间相关让不变性不可辩护，就必须 kill p-value 路线。对当前单幅非平稳视频帧，**不推荐此路线**。

### 3.5 matched-mask kill 条件

- 任一必需 family 无法按冻结规则得到规定数量，或需要放宽 caliper／换 seed；
- 真实 support 与候选 library 使用了不同 resolution、crop、z-buffer、可见性或数值域；
- 任一候选读了 intervention/Benefit 输出；
- 三族被 pooled 后只报一个 rank；
- 把 `r<=0.05` 写成显著、p 值、5% type-I error 或 95% 置信度；
- 只有 `G_shape` 通过却主张 source-specific localization；
- mask family、edit family 或 seed 只选择结果最好者。

## 4. 修复二：把 post-selection support 定义成可复算的目标视角映射

### 4.1 当前源码决定了什么

只读源码给出四个必须尊重的事实：

1. `render_surfels_to_image()` 在 228–409 行返回简单 z-buffer 的 `depth/surfel_index_map/cos_value_map`。
2. ordinary retrieval 在 639–647 行用多个 target poses 的**平均 pose**和 `target_K*0.65` 生成内部 `retrieved_info`。这张 map 用于选择，不能直接充当每个实际 target frame 的评价 support。
3. `process_retrieved_spatial_information()` 在 462–502 行把同一个 surfel 的权重记给 `surfel_to_timestep[j]` 中每个 timestep；`merge_surfels()` 在 818–824 行会给已有 surfel 追加 timestep。provenance 因而是多对多。
4. `get_context_info()` 在 759–765 行只返回 context tensors 与 `context_time_indices`，不返回 support。随后 1249–1267 行把整帧 latents/embeddings 送进 `get_cond()`。当前代码没有逐像素 appearance gate。

由此，V3 不能把 retrieval 时的平均相机 map 复制成 support，也不能把一个多 provenance surfel 事后唯一归给目标 source。support 应被称为“由 pre-treatment geometry/provenance 定义的目标视角预期作用区”。

### 4.2 推荐直接写入 V3 的规范条款

> **Post-selection support contract。** ordinary `get_context_info()` 完成后，先保存有序 `context_time_indices`、每个 slot 的 source ID、重复 slot 和目标 source `s*`；任何 intervention 不能重新运行或改变 selection。对每个实际 target frame `t`，使用该时点冻结的完整 surfels、`surfel_to_timestep`、实际 `c2w_t/K_t`、576×576 target canvas，以及与 ordinary renderer 完全相同的 near/far、backface、disk rasterization、z-buffer 和 tie-break，重新渲染：
>
> `j_t(p)=frontmost frozen surfel index at target pixel p`，
>
> `T_t(p)=surfel_to_timestep[j_t(p)]`。
>
> 主权重固定为
>
> `w^frac_t(p)=1{s*∈T_t(p)}/|T_t(p)|`，
>
> 并同时保存两个必要 sensitivity：
>
> `w^union_t(p)=1{s*∈T_t(p)}`，
>
> `w^exclusive_t(p)=1{T_t(p)={s*}}`。
>
> 空像素、backface、无 provenance、非有限 depth 和 z-buffer 未命中像素权重为 0，并各自计数。主报告使用 `w^frac`；union/exclusive 不得在看到结果后替换主权重。每一 target frame 单独计算 effect 与 localization，再按预先冻结的等权 frame 聚合形成 episode statistic；禁止把所有 pixels pooled 成伪样本。
>
> hook 在任何 arm 前输出并 hash：selection call ID、source/slot map、actual target cameras/K、surfel table SHA、完整 provenance SHA、`j_t` SHA、三种 support SHA、resolution/crop/rasterizer config、support area、exclusive purity、holes 与重现校验。hook 只增加观测字段和一个 post-selection replacement point，不能改变 ordinary selection、tensor shape/dtype/device、geometry 或非目标 slot。
>
> 本实验把该 support 解释为 geometry-projected expected locus。因为 VMem 消费的是整帧 context tensors，不得把 support alignment 单独写成真实逐像素路由或证明 denoiser 只在 support 内使用该来源。

`w^frac` 是本项目的归因约定，不是 VMem 论文给出的 ground truth。选它的理由是多 provenance 时避免把同一 surfel 的全部面积同时完整归给多个来源。必须同时显示 union/exclusive 敏感性，读者才能看出结论是否依赖这个约定。

### 4.3 support kill／降级条件

- 无法从**同一次 ordinary selection**稳定恢复 source ID、slot 和实际消费 tensor slice；
- support 仍来自 average pose/`0.65K` retrieval map，而非每个 actual target pose/K；
- `surfel_to_timestep` 缺失、空、索引越界或在 arm 之间漂移；
- 主 support 为空、全屏、非有限，或有效面积落在 CAL 冻结范围之外；
- `exclusive purity = Σw_exclusive/Σw_union` 低于预冻结门：降级为 shared-provenance geometry alignment，禁止 selected-source-specific claim；
- hook 改变 selection 结果、context 顺序、形状、dtype、device 或普通 F00 输出；
- consumer path inventory 不完整，或 F11 未覆盖所有 appearance descendants；
- 支持区域是从 effect/attention/Benefit 结果反推的。

## 5. 修复三：每个 arm 的 fresh-process 状态隔离合同

### 5.1 为什么“同 seed + reset”不够

源码 118–127 行初始化实际字段 `latents`、`encoder_embeddings`、`Ks`、`surfels`、`surfel_to_timestep`、`pil_frames`，运行还使用 `c2ws`。但 135–146 行的 `reset()` 清空的是 `rgb_vae_latents`、`rgb_encoder_embeddings`、`all_pil_frames` 等不同名称，没有清空 `latents`、`encoder_embeddings`、`c2ws` 或 `pil_frames`。1294–1309 行又把输出追加回 memory 并重建 scene。当前 SHA 的 in-process reset 不能进入 S48。

PyTorch 官方文档也明确说明 deterministic algorithms 只是必要组件之一；相同 seed 没有保证其他 RNG、实际 noise tensor、库版本和非确定算子相同。

### 5.2 推荐直接写入 V3 的规范条款

> **Arm isolation contract。** 当前 pipeline SHA 下，每个 A0/F00/F10/F01/F11、sham、positive/negative control 和 Benefit replacement arm 必须由全新的 OS process/process-group 执行，并在执行一个 arm 后退出。所有 arm 只读加载同一个 `BASE_STATE`，其 manifest 至少包括：代码／weights／config／环境 lock SHA，初始输入与 prompt SHA，所有 target cameras/K，`latents`、`encoder_embeddings`、`c2ws`、`Ks`、`pil_frames`、surfels、depths、provenance、selection 与 support artifacts，actual materialized noise tensors，以及 Python/NumPy/Torch CPU/每块 CUDA RNG states。
>
> 启动进程前设置并记录 Python hash、CUDA/cuDNN/cuBLAS 与 deterministic flags。若能力允许，调用 `torch.use_deterministic_algorithms(True, warn_only=False)`；遇到不支持的算子必须失败并重冻执行方案，不能静默切为 warning 或非确定模式。固定软件版本、driver、device ID 和 precision。
>
> 每个 arm 的步骤固定为：创建不可复用的 `attempt_id` 和 exclusive-create 输出目录；启动新 PID/PGID；验证只读 `BASE_STATE`；物化并记录 actual noise SHA；计算 `pre_state_digest` 并要求与 base digest 完全相同；只运行一个 arm；写入输出、trace、state、return code、stdout/stderr 和资源 receipt SHA；fsync/close；退出；由父进程确认 PID/PGID 及子进程全部终止、没有仍占用的 GPU/文件句柄，再允许下一个 arm。
>
> 同一 paired seed 的所有 arm 使用同一个已保存 noise tensor，不得仅根据整数 seed 重新采样。不同 paired seeds 使用不同 noise tensors，但仍来自预冻结列表。任何 arm 均不能读取其他 arm 的可写 cache、输出目录或临时状态。

### 5.3 两阶段封存顺序

1. `STATIC_SEAL`：冻结代码、base state、support/mask generator、dose ladder、arm list、随机顺序生成算法和所有公式。
2. `A0_STAGE`：只运行预定 exact replays，计算每个 metric 自己单位的 replay floor；由固定脚本生成 `A0_FLOOR_RECEIPT`。此时所有 intervention/Benefit arms 保持 sealed。
3. `ARM_STAGE`：receipt SHA 写回 manifest 后，按预冻结 seed 得到的 block-randomized order 运行 arms；穿插位置的 F00 sentinel 也预先冻结。
4. 不允许因某 arm 失败只追加一个“更好”的替代 attempt。完整 attempts 保留；arm-related failure 进入最坏情形或 kill 规则。

### 5.4 fresh-process kill 条件

- 使用当前内置 `reset()` 承担 arm 隔离；
- pre-state、actual noise、RNG 或 support digest 不同；
- 输出目录已有旧文件、mtime 早于 launch、attempt ID 重用或 stale output 被接受；
- PID/PGID、return code、终态或资源释放 receipt 缺失；
- deterministic capability 报错后静默降级；
- 某种处理比 control 更常 crash、超时或产生 missing，而分析删除这些 attempts；
- A0 floor 在序列中漂移超过冻结门，或 F00 sentinel 失败；
- 一个进程连续运行多个 arms，或共享可写 cache/state。

## 6. 修复四：跨视角 common-visible support 与配准

### 6.1 目标坐标系和有效像素

所有主损失固定在 actual target frame 的 576×576 pixel grid。对目标像素 `p` 的 frozen 3D surfel/point `X_t(p)`，向每个资格视图 `v∈{O,P,R}` 投影 `q_v=π_v(X_t(p))`。定义 `V_{v,t}(p)=1` 当且仅当：

1. `q_v` 在图像内且相机深度为正；
2. `q_v` 处存在冻结 depth/surfel，不是 hole；
3. projected depth 与该视图 depth 在冻结相对阈值 `eps_z` 内；
4. 从 `q_v` 按该视图 depth 反投影并回到 target 后，round-trip error `<=eps_px`；
5. 双向 z-buffer 都判为可见；没有 one-to-many collision 未决；
6. 不属于动态、时间错位、遮挡不一致或相机模型失配的排除区域。

主区域按比较对象分别定义：

`C^local_t = support(w_t>0) ∩ V_{O,t} ∩ V_{R,t}`，

`C^matched_t(P) = support(w_t>0) ∩ V_{O,t} ∩ V_{P,t} ∩ V_{R,t}`。

不同 replacement `P` 必须有自己的 `C^matched_t(P)`；不能先找一个最有利的共同区域给全部 P。reference RGB 用冻结的插值器 warp 到 target grid；validity mask 在插值前由 geometry 决定，hole 不得被填充后变成有效观测。所有 arms 在同一个已冻结 `C` 上评分，不能各自产生 mask。

### 6.2 推荐直接写入 V3 的规范条款

> **Registration and common-support contract。** reference、original source 与每个 replacement 的资格只使用封存图像、camera/K、时间戳、干预前 depth/surfels 和冻结代码。不得用 F11/Benefit 输出估计 homography、optical flow、exposure transform、validity mask 或选择 reference/replacement。一般非平面场景使用 depth/surfel reprojection，不用单一全局 homography 代替 3D 配准。
>
> 固定 `eps_px`、`eps_z`、z-buffer tolerance、depth sampler、RGB interpolation、collision tie-break、border、hole、dynamic mask、颜色域和所有 NaN 行为。保存 forward/backward residual 分布、valid count、`|C|/|S|`、hole rate、occlusion rejection、每个 view artifact SHA 与 common-support SHA。
>
> 主 MSE 使用未经输出自适应光度校正的 uint8 sRGB；任何曝光／白平衡仿射只能是预冻结 sensitivity，并且参数必须来自校准板或 arm-independent non-support control region。不得通过最小化 Benefit loss 拟合校正。
>
> 多 target frames 先逐帧计算 loss difference，再等权聚合；不同 replacement 先在各自 `C(P)` 上形成配对 loss difference，再按完整预冻结 `P_i` 等权聚合。禁止把可见 pixels 数当独立样本量。

V3 可以保留 `eps_px=1.0`、相对 depth `0.02`、coverage `0.70`、hole `0.10` 作为 pilot 项目门，但应明确这些值来自项目 CAL／科学容忍度，不是 MVSNet、Monodepth2 或 OCAI 给出的通用阈值。最好预注册更严格的一组 sensitivity，仅用于稳健性，不改变主门。

### 6.3 common-support kill 条件

- reference、source 或 replacement 缺 camera/K/depth，或相机坐标约定无法唯一转换；
- forward/backward 或 z-buffer 检查失败，coverage 低于冻结门，hole rate 高于门；
- registration/photometric 参数是看 Benefit output 后调出的；
- 动态物体、曝光跳变或不同时间的外观变化无法从 memory effect 中分开；
- 不同 arms 使用不同评价 mask；
- 非平面 scene 仍用单一 homography 做主配准；
- `C(P)` 为空时放宽 caliper、换 P 或改 reference；
- 只在原 `S` 上报漂亮数字而隐藏 common-visible 覆盖率与 support 外恶化。

## 7. 修复五：唯一化 multi-edit、dose、seed 和 controls 的聚合

### 7.1 dose 选择必须是一条确定函数

“只用 source-only 信息调 dose”仍不够；如果有多个合格 dose，事后任选仍会产生自由度。直接写入：

> 对每个 edit family `f`，在输出产生前冻结升序候选 ladder `Δ_f=(δ_f,1<...<δ_f,J)`、source-only lower edit floor、upper identity/CLIP/LPIPS/edge/clipping bounds 和全部算法 SHA。对每个候选同时检查 `+δ` 与 `-δ`；选择**两侧都通过所有 source-only 门的最小 δ**。没有候选通过则该 family invalid-stop。选中后该 family 在所有 seeds、paths 和 Benefit-local 中只使用这一 δ，不做第二剂量，也不因 generator response 太弱而增大。

所有具体 source-only 阈值都必须在 G7 给数值。若尚无独立 CAL，就先做不读取任何生成输出的 source transform feasibility，而不是凭主观挑 dose。

### 7.2 effect map 与 control-adjusted Influence

对每个 family `f`、seed `s`、符号 `a∈{+,-}`：

`d^a_{f,s}(p)=mean_c |Y^a_{f,s}(p,c)-Y^0_s(p,c)|/255`，

`d_{f,s}(p)=0.5[d^+_{f,s}(p)+d^-_{f,s}(p)]`。

必须先取每侧的绝对像素差再平均。禁止先平均 `Y+` 与 `Y-`，否则对称改变会相消。

当前 V3 分别要求 treatment 高于 `tau+delta_I`、negative/sham 低于同一界，但两者可以无限接近。更强且唯一的门为：

`I_{f,s}=D_{f,s}-max(tau_output,s, D_sham,s, D_negative,f,s)`，

并要求每个 `f×s` 都有 `I_{f,s}>=delta_I`。positive control 单独验证命名 consumer path 的连通性：

`D_positive,s-max(tau_output,s,D_sham,s)>=delta_positive`，

其中 `delta_positive`、tensor slice、符号无关评价与预期 trace 在 G7 冻结。positive control 不进入 treatment effect，也不能靠极大剂量制造 trivially pass。

### 7.3 Localization 与 Benefit 的唯一合取

- Influence：两个 family×两个 seed 的四个 `I_{f,s}` 全部通过。pilot unit 摘要 `I_i^rob=min_{f,s}I_{f,s}`。
- Localization：每个 `f×s` 分别在每个必需 placebo family 上过门；unit 摘要 `L_i^rob=min_{f,s,g}L^g_{f,s}`。若只通过一个 edit，报告 edit-specific sensitivity 并 kill broad mechanism claim。
- Local Benefit 必须把 family 和 seed 写进下标：

  `B^local_{f,s}=0.5[loss_C(Y^+_{f,s},R)+loss_C(Y^-_{f,s},R)]-loss_C(Y^0_s,R)`。

  两个 family×两个 seed 全部超过 `delta_B_local`，才称在两个机制邻域中稳定有益。
- Matched Benefit 对每个 seed 先对**全部预冻结合格 replacements**等权平均：

  `B^matched_s=mean_{P∈P_i}[loss_{C(P)}(Y_s(P),R)-loss_{C(P)}(Y_s(O),R)]`。

  两个 seeds 分别超过 `delta_B_matched`。这只支持“相对该完整 matched set 的平均收益”，不支持优于每一个 P；如果科学 claim 要求逐个优于，就必须改成 `min_P B_s(P)` 并在输出前冻结。
- S48 只做合取式 kill decision，不产生总体 p 值。S49 若要求所有 endpoint/family 成立，可使用 intersection–union 逻辑；若改成“任一 family 成立”，必须冻结 Holm 等 familywise 修正。
- paired seeds、positive/negative controls、masks、frames、pixels 都是 unit 内技术重复。未来 S49 先在 source/episode 内按上述函数聚合，再让独立 scenes 等权；不能把它们提升为 scene-level `n`。

### 7.4 multi-edit／seed kill 条件

- dose ladder、合格标准或最小合格选择规则没有在输出前冻结；
- 正负 dose 先平均输出再取绝对值；
- treatment 没有超过 replay、sham、negative 中的最大者加 SESOI；
- positive control 没有触达预先命名 consumer，或 positive response 只能由异常大 edit 得到；
- 任一预定 family/seed 失败后仍挑成功者写 broad claim；
- `B_local` 忽略 edit family，或 `B_matched` 在看到 loss 后挑 P；
- S48 给总体显著性，或 S49 把 seed/mask/pixel 当独立样本。

## 8. G7 manifest 最少字段

以下字段缺一项，fresh pre-run review 应判 BLOCKED：

| 组 | 必需字段 |
|---|---|
| 版本 | code/weights/config/env/driver/device/metric/launcher SHA；源码行和 hook SHA |
| 因果对象 | estimand 字符串、DAG、唯一 post-selection injection point、all-consumer inventory |
| selection | ordinary call ID、source ID、slot/order/duplicate map、selection artifacts SHA |
| support | per-target camera/K、surfel/provenance SHA、renderer参数、fractional/union/exclusive支持 SHA、area/purity/hole rules |
| masks | 三个 family 的独立 config、proposal grid、calipers、order/seed、counts、rejections、有序 IDs、artifacts SHA、family-specific gates |
| edits | 两 family 的公式、dose ladders、双侧 source-only gates、唯一最小合格 dose、sham/negative/positive tensors与阈值 |
| randomness | paired seed IDs、actual noise tensor SHA、Python/NumPy/Torch CPU/CUDA RNG receipts、deterministic capability receipt |
| process | base-state digest、arm list、block order、attempt ID schema、PID/PGID、exclusive dirs、timeout、return/resource terminal states |
| A0 | replay schedule、每个 metric 同单位 floor 公式、sentinel positions、sealed floor receipt SHA |
| registration | view eligibility、camera convention、depth/reprojection/z-buffer/interpolation/dynamic rules、`C_local/C(P)` SHA、coverage/hole gates |
| metrics | RGB domain、epsilon、per-frame→episode→scene aggregation、SESOIs、support-outside guard、NaN/empty/missing rules |
| reporting | all attempts flow、arm failures、no optional stopping、claim ladder、S48/S49 separation |

## 9. 一张可执行的 claim ladder

| 通过的证据 | 最多允许的结论 | 仍禁止的结论 |
|---|---|---|
| Influence only | 该 selected source 的 post-selection appearance bundle 在本 CAL unit 中改变输出 | source total effect、benefit、geometry localization |
| Influence + area + `G_shape/G_camera` | effect 在本 unit 中与预冻结 geometry support 对齐，并超过规定空间 placebos | 随机化显著性、source-specific routing |
| 再过 `G_source` 与 provenance purity | effect 对 selected-source geometry 比其他合格 source supports 更集中 | 像素级 denoiser routing ground truth |
| 再过 independent-reference common-support Benefit | 原 source 相对指定 local/matched alternatives 在本 CAL unit 上更有益 | scene-level 泛化、预测器有效、方法新颖性 |
| 独立 S49 scenes + 冻结推断通过 | 对预注册目标总体的有限外推 | 自动达到顶会水平或超过近邻方法 |
| held-out acceptance head + 强基线 | 可评价 GeoCausal accept/reject 是否带来增量价值 | 在未比较 I3DM/TetherCache/CUE-R/普通 gates 时宣称新方法胜出 |

## 10. 自我对抗检查与剩余限制

1. **文献没有直接验证这套 VMem 协议。** 本报告把统计原理、多视图可见性和 intervention 诊断拼成一个可审查设计；它仍需代码实现与合成／静态自测后 fresh review。
2. **fractional provenance 是约定。** 它比任意唯一归属更保守，但不等于真实 consumer attribution，所以必须同时报告 union/exclusive。
3. **描述性 top 5% 仍是门槛，不是概率。** 它适合 pilot kill decision；不能在论文里用“显著”包装。
4. **严格三族对照可能降低通过率。** 这是设计目的：失败应告诉我们 geometry alignment 不稳，而不是通过 pooling 稀释困难对照。
5. **fresh process 解决 carryover，不解决科学方差。** 只有独立新 scenes 能支撑外推。
6. **common-visible scoring 会减少像素。** 覆盖不足应停止 Benefit，而不是回到未经配准的全 support MSE。
7. **I3DM/AGRA 目前仅按预印本定位。** 它们可用于 novelty pressure 和 proxy 设计，不能写成已正式顶会接受的证据。
8. **本报告没有读任何模型输出。** 所有建议都来自协议、源码结构和文献；没有新的实验结果或效果承诺。

## 11. 对 V3 的最终建议

V3 应采用本文件的描述性、逐族 matched-placebo 路线，并再补三处当前草案中仍值得收紧的点：

1. 把单个混合 `K=199` library 改为 `G_shape/G_camera/G_source` 分开生成、分开 gate；
2. 明确 support 是按每个 actual target camera 重渲染的 fractional provenance expected locus，并明确它不是逐像素 consumer routing；
3. 把 Influence 改成相对 `max(replay, sham, negative)` 的净 SESOI，同时给 `B_local` 加上 edit-family 与 seed 下标。

这些条款足以解除 V2 的**方法学设计** blocker，但不解除执行 blocker。后续必须先完成 hook、mask generator、fresh-process launcher、registration/metric 代码与只读 manifest，再由不继承本报告结论的独立代理做 fresh source/protocol review。只有该审查 PASS，才可启动任何 S48 模型 arm。
