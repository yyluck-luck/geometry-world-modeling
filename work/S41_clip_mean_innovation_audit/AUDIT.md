# S41：VMem 多历史 CLIP 均值的独立创新审查

审查时间（UTC）：2026-09-07。审查者：`/root/clip_mean_innovation_audit`。

## 结论先行

当前可保留的是一个**待证伪的新问题**，不是一个已经成立的新方法：

> 当 VMem 的几何检索已经固定选中同一组历史帧时，把每帧的全局 CLIP 向量压成一个算术均值，是否破坏了“语义证据来自哪一帧、对应哪个视角/区域”的绑定，使检索到的历史细节不能传到回访输出？

直接把 `mean` 换成 attention、router、加权平均、最近帧或锚点，不能作为创新。新增的直接近邻进一步封死了四条看似自然的路线：WorldStereo 已用 3D correspondence 约束检索参考与目标的 attention receptive field，并明确面向 fine-grained detail；Spatia 已做视觉 SLAM 持续更新的点云记忆；Geometry-as-Context 已把 Plücker 相机信息写入 query 并门控 attention 输出；PoCo 已用 reference side information 控制多参考 token 关联。更早的 SPAD 与 EpiDiff 也已覆盖 epipolar-constrained cross-view attention。因此，**“均值不好，所以加 attention/router/几何 token routing/source tag/点云更新/gating”这一整组方法版本均应 Reject and Pivot**。

仍值得做的路线是先把它改写为“固定检索后的记忆消费者是否真正利用了被检索证据”的因果诊断。只有真实 VMem 生成出现自然回访失败，而且只替换 cross-attention 聚合后能在同输入、同噪声、同采样计算下稳定改变并改善输出，才进入方法设计。当前 S40 仍是源码准备通过、`runtime_authorized=false`、未执行真实模型加载/生成，故本报告没有任何效果结论。

## 1. 已核源码事实与证据边界

固定隔离源码的事实如下：

1. `get_context_info` 先由 Surfel 渲染、source timestep 票权、目标相机距离和 NMS 形成历史 frame IDs；随后按这些 IDs 读取逐帧 `latents`、`encoder_embeddings`、`c2ws` 与 `Ks`。
2. `get_cond` 在任何 cross-attention 之前执行 `torch.mean(encoder_embeddings, dim=0)`，随后把同一个一维全局向量复制给所有相机：`repeat(..., "d -> n 1 d")`。
3. 每帧 VAE latent 没有被这一步平均；它进入 `c_replace`。`c_concat` 由输入掩码与相机 Plücker 坐标组成。已核路径没有 Surfel RGB/颜色专门注入生成器。
4. 新生成帧的未来 latent 直接取自 `samples_z[~input_masks]`，同时对解码样本重新计算 CLIP embedding，并追加到后续历史。
5. `CLIPConditioner` 使用 OpenCLIP ViT-H-14 的 `encode_image`，每张图输出全局向量；源码没有保存 patch token 供 source-region 绑定。

关键本地身份：

| 文件 | SHA-256 | 用途 |
|---|---|---|
| `vendor/vmem_snapshot/modeling/pipeline.py` | `90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e` | 便于查看的固定 VMem pipeline 快照 |
| `work/S20_environment/isolated_vmem_source/modeling/pipeline.py` | `680da1c14db8a6780a37fca3a8bac5bb59f0aa7d395db96d4360b352eb7f2255` | S20 隔离原源码 |
| `work/S20_environment/isolated_vmem_source/modeling/modules/conditioner.py` | `b79eb0cf4d94345a720a9a844c7daa6206b0a9234d714b7f9f23a9571c7c5fc1` | 全局 CLIP 图像编码路径 |
| `work/S38_paper_learning/agent_a_video/report.md` | `bf5207ae41f3f4ad2c34118ffa160a18367e2973713fe4304f658a7154099a56` | 已核长视频/记忆近邻学习 |
| `work/S38_paper_learning/agent_b_geometry/report.md` | `6d654b148b5f5ef2f2953ece1d403c57f33d5e51d62ac87fa1a9a698cf03c28c` | 已核几何方法的归因边界 |
| `work/S40_declared_variant_generation/PROTOCOL_DRAFT.md` | `2c026b3dff79ca9155e5ad86a8c539b6597b6be7ed73b2c407b3d83ce75d7ced` | 两批真实生成准备协议，尚未执行 |
| `work/S40_declared_variant_generation/runtime_adapter.py` | `d26f7e8990fd218273361c04484c8c0ea499a693486fd7bb040e3b03306a79c4` | 声明 VAE 变体的加载适配器 |
| `work/S40_declared_variant_generation/launch_generation.py` | `8ade694bc750f9693fc461257437af7b919b0c46755fc0eef2e21096d31e8860` | 两批生成外控入口，尚未获运行授权 |

这只证明源码结构。没有证明：CLIP 路径对输出有可测影响、均值导致细节丢失、任何替代聚合更好、真实视频已生成，或存在论文创新。

## 2. 最可能推翻中心假说的五个解释

| # | 反证解释 | 为什么合理 | 最便宜的决定性检查 | 推翻条件 |
|---|---|---|---|---|
| 1 | 逐帧 VAE latent 已承担局部外观，CLIP 均值只给全局风格/语义 | `c_replace` 保留每帧 latent，且相机条件另走 Plücker；模型可能根本不需要 CLIP 保存局部细节 | 在完全固定的合法生成中比较原 mean 与 zero-CLIP，保存完整 `c/uc`、noise、`samples/samples_z` | zero-CLIP 与 mean 在预先冻结的数值/感知门内无实质差异，说明 CLIP 通路不是当前瓶颈 |
| 2 | 局部信息在每张图进入平均之前已被全局 CLIP 编码丢掉 | Conditioner 只返回每图一个全局向量，没有 patch token | 检查单图向量对局部实例/纹理扰动是否敏感；再比较单图向量和均值 | 不同局部内容的单图 CLIP 向量难以区分，或单图替代也不能保留细节，则责任在 encoder/表征粒度而非 mean |
| 3 | 均值是在去除视角、曝光和生成噪声，反而是有用的共识估计 | 多视角同一静态场景中，不同帧差异可能多为 nuisance；平均可降低噪声 | 原 mean 对比 medoid、最近帧、最远帧与几何加权 mean | mean 在预选场景/配对种子上稳定不差，尤其在视角服从不退化时更好，则“均值有害”被拒绝 |
| 4 | “几何选对 ID”不等于目标像素可用：遮挡、深度误差、相机/K、latent 顺序或消费 trace 可能错 | Surfel 支持率是几何代理，不直接证明历史外观能投影到目标区域 | 核第二批实际选中 cache 是否逐数组等于第一批提交内容；核姿态/K/可见掩码与目标区域 | 失败由不可见/错误对齐帧解释，或 trace 内容错接，则这是 baseline/检索问题，不是聚合问题 |
| 5 | 替换向量是训练分布外干预；生成漂移可能来自 denoiser、VAE 或自回归 `samples_z`，而非 mean | VMem 训练时预期 mean；任意替换即使改变输出也未必是改进，第二批又消费生成 latent | 先看第一批与第二批失败起点；记录替代向量范数、方向、输出质量与相机服从 | 只有分布外向量引起任意变化、改进不能跨种子/场景复现，或 drift 在 CLIP 干预前已出现，则不能归因给 mean |

五项中任何一项成立，都足以阻止把“均值导致回访失败”写进论文结论。

## 3. 最便宜且严谨的六臂干预矩阵

### 3.1 先决条件

这不是现在就能运行的实验。必须先得到一个通过原始 trace/readback 核验的真实 S40 两批结果，并明确它是 `VMem + stabilityai/sd-vae-ft-mse` 的**声明组件变体**，不是 exact-original VMem。还需在看替代结果之前预选至少两个未用于开发的场景、回访动作与配对 seeds，并冻结一个真实自然失败。若原 baseline 没有可复现的目标失败，停止该假说。

所有科学臂共同冻结：

- 同一模型与 VAE、同一历史及目标轨迹、同一选中 frame IDs 和顺序；
- 同一逐帧 latent、pose、K、Plücker、input mask、context/target 时序；
- 同一 seed、实际 noise tensor、采样器、步数、CFG 和两批不重置 RNG 的规则；
- 同一 K 个已经算出的 CLIP 向量作为**可用输入集合**，不得用 GT、目标输出或最终指标选权重；
- 每臂输出恰好一个同维 cross-attention 向量，再按原代码复制到相同相机数；
- 学习参数增量均为 0，denoiser/VAE 前向次数完全相同。

为避免把聚合计算差异混进生成时间，应在任何视频输出产生前一次性计算、保存并哈希六个向量；每臂生成时只读取一个缓存向量。聚合自身耗时另报，不能宣称全流程严格等时。除 A1 的故意移除信息外，各臂可用输入集合、输出维度和下游计算相同；单向量臂有意改变实际保留的信息，这是要检验的变量。

### 3.2 六臂

| 臂 | 聚合定义 | 信息量/参数/计算控制 | 它回答什么 | 身份 |
|---|---|---|---|---|
| A0 原 mean | `m = mean(e_1...e_K)`，逐值复现源码 | 原输入、原向量维度、0 参数、原生成计算 | 真实基线 | baseline |
| A1 zero-CLIP | 先照常读完 K 个向量，再输出 `0_d` | 形状/模型/前向相同；故意删除 cross-attn 语义 | CLIP 通路是否真的影响输出 | causal negative control |
| A2 最近视角 | 在固定已选 K 中，以 VMem 已用的目标平均相机距离取最近帧 embedding；匹配 `||m||` | 不新增帧/GT；读同一 K 与 pose，0 参数 | 单一相关观测是否胜过平均稀释 | ordinary baseline |
| A3 最远视角 | 同一 K 中距离最远的 embedding；匹配 `||m||` | 与 A2 相同输入/输出/计算边界 | 若 A2 改善，是否真来自视角相关性而非任意换向量 | directional negative control |
| A4 CLIP medoid | 选择与其余 K 个向量平均余弦最接近的**真实观察向量**；匹配 `||m||` | 读取全部 K，不插值新语义，0 参数 | 问题来自“平均落在非观察点”还是缺少图间共识 | ordinary set baseline |
| A5 几何票权 mean | 用 VMem 在输出前已经计算的 Surfel/source 票权，对固定已选 K 重归一加权；结果匹配 `||m||` | 只用 predicted/pre-output geometry，不用 GT；0 参数 | 查询相关但仍为单向量的最强简单控制 | ordinary weighted baseline |

范数匹配定义为 `v <- v * ||m||/(||v||+eps)`，`eps` 与 dtype 事前冻结。A0 必须有一次 exact replay；把 embedding 顺序打乱后重新求 mean 必须与 A0 数值一致。这两项是接线守卫，不另算科学臂。

### 3.3 结果证据必须保存

每个场景/seed/臂都保存：

1. 冻结清单：组件变体、全部源码/权重/小输入身份、K、frame IDs/顺序、pose/K、trajectory、seed、sampler。
2. 条件证据：K 个 CLIP 数组 SHA、六个聚合向量的数组 SHA/shape/dtype/norm/cosine；实际传入的 `crossattn`、`concat`、`replace`、`c/uc` 和 noise 数组 SHA。
3. 历史闭环证据：第一批 `samples_z` 与提交 cache 的逐数组对应；第二批读取 cache 与第一批提交值逐数组相等；不只保存 frame ID。
4. 输出证据：原始 `samples`、`samples_z`、解码帧、trace 顺序、返回码、进程树峰值 RSS、每阶段耗时和任何失败目录。
5. 评价证据：预先冻结的回访可见区域、与先前同位置观察的 PSNR/SSIM/LPIPS 或独立视觉表征距离；相机服从/视角变化指标；防止“复制旧帧”投机的运动和 novel-view 检查。CLIP 相似度不能单独作为主指标，因为被干预的正是 CLIP 条件。
6. 统计证据：每个场景和 seed 的配对原始行，不能只报均值；开发场景与未见确认场景分开。

### 3.4 失败与退出条件

- baseline 未出现预注册的自然回访失败：停止，不造一个失败来支持方法。
- A1 与 A0 没有超过 exact-replay 数值噪声的输出差异：CLIP 消费通路在该设置下无证据，停止 mean 方法线。
- A2/A4/A5 没有在多个预选场景与配对 seeds 上一致改善回访保持，或改善伴随相机服从/质量退化：拒绝“均值是主因”。
- A2 与 A3 表现相近：变化更可能是向量扰动或范数/分布外效应，不是目标相关证据绑定。
- 改善在范数匹配后消失、只在已看开发场景存在，或需要用 GT/输出结果选权重：无效。
- A5 这样的普通零参数加权即可解决：把它作为更强 baseline；不能包装成创新。
- trace、缓存数组、pose/K、噪声或 frame IDs 任一不相同：该对照作废，归为接线/基线修复。
- 只有声明 VAE 变体成功而 exact-original 身份仍未知：允许报告变体诊断，禁止外推“原 VMem 必然如此”。

## 4. 直接近邻的四轴排重

下表的“状态”指生成时保留的中间表示，“更新”指它怎样形成或随序列变化，“读出”指怎样进入生成。差异说明只用于排重，不证明本项目原创。

| 工作 | 输入 | 状态 | 更新 | 读出 | 对本项目的直接压力 |
|---|---|---|---|---|---|
| [VMem, ICCV 2025](https://openaccess.thecvf.com/content/ICCV2025/html/Li_VMem_Consistent_Interactive_Video_Scene_Generation_with_Surfel-Indexed_View_Memory_ICCV_2025_paper.html) | 历史/生成图、相机、预测几何、目标轨迹 | Surfel→source frame 索引，加每帧 latent/全局 CLIP/pose/K | 新帧经几何估计合并 Surfel，并追加 `samples_z` 与 CLIP | 几何票权+pose/NMS 选 ID；逐帧 latent 进入 context，全局 CLIP 在源码中求 mean | 它是必须保留的真实 baseline；本项目问题发生在其“检索后消费”接口 |
| [EasyRef, ICML 2025](https://proceedings.mlr.press/v267/zong25a.html) | 多张参考图、文本/指令 | MLLM 的组图交互表征，不是在线空间记忆 | 通过渐进式离线训练学习多参考表征；无在线地图更新 | 投影器/adapter 把组图表征注入 diffusion | 它已明确针对平均/拼接多图 embedding 缺乏图间交互；generic interactive aggregator 不新 |
| [WorldMem, NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/470629a47e2d65ce0606c40055df5d26-Abstract-Conference.html) | 历史帧 token、pose、timestamp 与当前状态 | token 级历史 memory bank，每个单位绑定 pose/time | 历史生成 token 与状态持续加入 bank | FOV/time/相似过滤后，以相对 pose/time 加强 Q/K、视觉 token 作 V 的 cross-attention | “保留每帧 token + 状态感知 attention”已存在于同一世界模拟问题 |
| [MiMo, ICLR 2026](https://proceedings.iclr.cc/paper_files/paper/2026/hash/9d30c2def27b5c6a5fb21a9aa5c16f8f-Abstract-Conference.html) | VideoAR 历史帧 token 与未来帧 | 经过专门学习的历史内部表征 | 训练时遮挡历史 token，并联合预测当前/未来 masked token | 增强的历史表征作为 VideoAR 条件 | “历史表征质量限制自回归视频”本身已成为中心问题；只说 history encoding 更好不足以新 |
| [CorrAdapter, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_Align_Images_Before_You_Generate_CVPR_2026_paper.html) | 多图 diffusion 的中间特征；不依赖外部几何/语义先验 | 由模型内部特征构建的跨图 correspondence | 每个 bypass/生成过程构造对应关系；另有可选训练 | aligned-area aggregator 只在匹配区域传递消息 | “对应关系约束的区域聚合”也已存在；仅加几何 mask/区域 attention 仍不够区分 |

### 4.1 四篇 2026 直接近邻：输入—状态—更新—读出

| 工作 | 输入 | 状态 | 更新 | 读出 | 四轴差别与裁决 |
|---|---|---|---|---|---|
| [WorldStereo, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_WorldStereo_Bridging_Camera-Guided_Video_Generation_and_Scene_Reconstruction_via_3D_CVPR_2026_paper.html) | 初始/已生成参考帧、参考与目标相机、pointmap、全局点云 |  temporally downsampled 2D memory bank + WorldMirror 重建的 3D cache | 新生成帧加入 2D bank；逐段点云增量重建，并以重叠视图的 Umeyama 对齐合并 | Global-Geometric Memory 的 ControlNet 注入粗结构/相机控制；Spatial-Stereo Memory 以 3D correspondence 配对目标与检索参考，限制 attention receptive field 保存细节 | 它比 VMem 的“先选 ID、再全局 CLIP mean”读出更局部，且正面解决几何记忆的 fine-detail 消费；**geometry-guided token routing 作为方法新意被直接否决** |
| [Spatia, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/papers/Zhao_Spatia_Video_Generation_with_Updatable_Spatial_Memory_CVPR_2026_paper.pdf) | 初始图、先前生成 clip、参考帧、文本、相机轨迹及其点云 projection video | 持久 3D scene point-cloud spatial memory，加参考帧与 preceding clip tokens | 每轮用全部先前/新生成帧经 MapAnything/visual SLAM 更新点云 | 按目标轨迹把点云渲染成 projection video，由 ControlNet 融合；参考帧和 preceding video tokens 进入主干 | 它的状态与更新比 VMem 更显式；**“可更新点云记忆 + SLAM + 几何条件生成”作为方法新意被否决** |
| [Geometry-as-Context, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Hu_Geometry-as-context_Modulating_Explicit_3D_in_Scene-consistent_Video_Generation_to_Geometry_CVPR_2026_paper.html) | 图像/文本/显式几何 context 与目标相机的 Plücker rays | 自回归 interleaved RGB–geometry context；并非独立外部 memory bank | 每步先估当前视图几何，再模拟、渲染并恢复 novel-view RGB；训练时随机丢 geometry context | Camera Gated Attention 用 Plücker 特征增强 query，并门控 self-attention 输出 | 状态形态虽不同，但“geometry as context / camera-conditioned gating”已正面出现；**把几何写进 query 或 gate 作为新意被否决** |
| [PoCo / Rethinking Position Embedding, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/papers/Huang_Rethinking_Position_Embedding_as_a_Context_Controller_for_Multi-Reference_and_CVPR_2026_paper.pdf) | 多参考图、多 shot 视频/文本、用户给出的 reference identifiers | 拼接的 reference/shot tokens + SideInfo-RoPE 的额外 side-information 坐标；无持久空间地图 | 训练学习 multi-reference/multi-shot 生成；无在线记忆更新 | 保留 full attention connectivity，用 reference-specific RoPE phase 调制 Q–K 关联 | 它不做 3D 区域支持，但已解决“相似参考被错绑”的 source association；**source ID/tag/side-info positional binding 作为新意被否决** |

这四篇与 VMem 的轴差别分别在“消费者的局部读出”“空间状态的在线更新”“几何作为生成上下文”“来源标识控制关联”，恰好覆盖了从 CLIP mean 最容易想到的四类替代。差别本身不足以恢复新颖性：若提案只是把其中任一组件搬进 VMem，贡献仍是已知机制的组合。

### 4.2 2024 几何 attention 先例

| 工作 | 已覆盖机制 | 对候选的压力 |
|---|---|---|
| [SPAD, CVPR 2024](https://openaccess.thecvf.com/content/CVPR2024/html/Kant_SPAD_Spatially_Aware_Multi-View_Diffusers_CVPR_2024_paper.html) | 跨视图 self-attention 施加 epipolar constraint，并以 Plücker ray coordinates 作 position encoding | 仅用相机几何限制多视图 token 交互早已有正式先例 |
| [EpiDiff, CVPR 2024](https://openaccess.thecvf.com/content/CVPR2024/html/Huang_EpiDiff_Enhancing_Multi-View_Synthesis_via_Localized_Epipolar-Constrained_Diffusion_CVPR_2024_paper.html) | 在冻结 diffusion 中插入轻量 ECA block；Near-Views Cross-Attention 沿极线把邻视图特征聚到 target ray points，Ray Self-Attention 再融合深度/射线特征 | “geometry-guided localized routing/aggregation”不是 2026 才出现，也不能靠换 backbone 恢复新意 |

由 WorldStereo、SPAD、EpiDiff 三者共同施压后，Gemini 提出的 **geometry-guided token routing 明确按方法新颖性 Reject and Pivot**。WorldStereo 与本项目的任务、记忆检索和细节保持最近；SPAD/EpiDiff 则证明核心几何约束 attention 算子已有更早先例。它们可以成为强 baseline 或模块来源，不能成为论文主贡献。

其他会让简单组件替换失去新颖性的正式近邻：Movie Weaver（CVPR 2025）的 per-reference concept embedding 与 anchored prompt；MS-Diffusion（ICLR 2025）的 layout-masked multi-subject cross-attention；Mixture of Contexts（ICLR 2026）的稀疏 attention router；Ada-RefSR（ICLR 2026）的 reference correlation gate。它们说明 source tag、layout mask、attention/router、置信门控与普通加权都应作为近邻或强 baseline，而非贡献本身。

本轮没有检索到一篇正式工作明确冻结**同一几何检索结果和全部生成随机量**，再用 source-level counterfactual 逐级核验“检索增益是否经过条件消费者传到目标可见区域”。这只可写成“在本轮关键词和正式来源中没有直接重合结果”，不能写成“首创”；仍需完整 deep-research 级系统综述。

## 5. 普通机制与可能具有实质新意的边界

### 5.1 这些只是普通 attention/router

- 让 query 对 K 个 CLIP 向量做 softmax attention；
- 按相机距离、Surfel 票权、余弦相似度或学习分数加权平均；
- nearest/anchor/medoid/top-k；加 source ID/position embedding 已被 PoCo 的 SideInfo-RoPE 直接施压；
- 给每帧开独立 KV，再用普通 cross-attention 读取；
- 用可见 mask、极线或 correspondence 只聚合匹配区域；WorldStereo、SPAD、EpiDiff 和 CorrAdapter 均是必须比较的先例；
- 用置信门选择、拒绝或混合 reference；
- 用点云/SLAM 更新空间记忆，或把点云 projection video 接入 ControlNet；
- 用 Plücker/几何特征修改 query、key、位置编码或 attention output gate；
- 换更强视觉 encoder，或增加 token 数后与单向量 mean 比较；
- 修改 frame IDs、历史长度或算力后把收益归给聚合。

以上都可做强 baseline 或工程修复，但邻近论文已经覆盖其核心思想。

### 5.2 值得保留的新问题

建议将问题命名为描述性术语，而不是提前取方法品牌：

**固定检索后的语义—几何归因缺口（post-retrieval semantic–geometric attribution gap）**：检索模块输出的是带来源与视角的证据集合，但消费者把语义压成与 source 无关、对所有目标相机相同的向量。要问的不是“mean 是否比 attention 差”，而是：

1. 更好的检索能否在生成输出中产生可定位的因果效应？
2. 每个被选 source 的语义变化是否只影响其几何可支持的目标区域？
3. 多 source 冲突时，系统是在保留可核来源、选择一个状态、明确拒绝，还是无证据地混合？
4. 这种消费者充分性是否能预测长程回访失败，且超出检索支持率和全局图像相似度？

这更像一个“新问题/诊断协议”候选，而不是现成的新方法。

### 5.3 现阶段可保留的边界

新增近邻后，以下组件只能作为 baseline：来源绑定的 memory packet（WorldMem/PoCo 已施压）、物理支持约束的 attention（WorldStereo/SPAD/EpiDiff/CorrAdapter 已施压）、可更新点云状态（Spatia 已施压）、camera/geometry gate（Geometry-as-Context 已施压）。把它们组合起来也不会自动变成创新。

现阶段唯一可以保留的是**固定检索后的消费者充分性问题与其因果审计协议**：

1. 固定 frame IDs、逐帧 latent、几何、噪声和采样，只反事实改变某个 source 的条件证据；
2. 测量该改变是否在其几何支持的 target region 产生可重复效应，并同时约束非支持区域不应响应；
3. 检验这份 source-to-region 因果可定位性是否能预测自然长程回访失败，并超过检索支持率、全局相似度和普通 attention/router 的解释力；
4. 用 WorldStereo 式局部读出、WorldMem 式状态注意力、PoCo 式 source binding、SPAD/EpiDiff 式几何 attention、普通 gate/router 作为同输入/同预算对照。

“冲突记忆应保留多状态并允许 abstain”只能列为**未验证的方法种子**；PoCo 已覆盖 reference confusion，Ada-RefSR 已覆盖参考置信门，是否仍有独立问题空间必须另做针对动态场景、时态冲突和不确定性的正式检索。当前不能把它写成创新贡献。

## 6. Idea Evaluator

### 6.1 第一印象与两种候选分流

| 候选 | 论文类型 | 一句话故事 |
|---|---|---|
| A：mean→attention/router | Novel Method（声称失败） | 用已有多参考交互模块替换算术平均；与近邻高度重叠 |
| B：固定检索后的消费者充分性审计 | Novel Problem / diagnostic setting（待验证） | 即使检索选对历史，消费者也可能因来源绑定丢失而无法把证据传到正确目标区域；用固定检索反事实把链条逐段验收 |

### 6.2 Fatal-flaws audit

| # | 缺陷 | 严重度 | 具体防守 |
|---|---|---|---|
| F1 无法区别最近工作 | 对候选 A 是 **CRITICAL**；对候选 B 是 MAJOR | A 直接停止：WorldStereo/SPAD/EpiDiff 覆盖几何 attention，PoCo 覆盖 source binding，Spatia 覆盖更新点云，Geometry-as-Context 覆盖 geometry gating。B 必须只以“冻结检索后的消费者因果审计/评测问题”为核心，并把这些工作与 EasyRef、WorldMem、MiMo、CorrAdapter 纳入排重和强对照 |
| F6 主张当前不可验证 | MAJOR | 先完成真实 S40 变体 baseline、自然回访失败、条件/缓存 readback，再运行六臂；未满足时不写效果或机制结论 |

候选 A 按 skill 的 CRITICAL 规则直接 `Reject and Pivot`。以下评分只针对候选 B。

### 6.3 生命周期与能力匹配

| 项目 | 已知输入 | 判断 |
|---|---|---|
| 类型 | Frontier exploration / diagnostic benchmark seed | 先做诊断可控制在 3–9 个月范围；若升级为重新训练 world model，则变成 12+ 月创新技术 |
| 学生能力 | 用户自述新手；有效周工时未知 | 理论/工程能力不能假装已知；必须依靠冻结协议、自动核验和小步门控 |
| 计算 | M3 Max 64GB，本地，无远程 GPU | 六臂推理诊断可能可做但需先实测；重新训练 EasyRef/WorldMem 级模块明显不匹配当前资源 |
| 匹配 | 诊断为 Yellow；新训练式方法为 Red | 先做零参数因果审查；没有显著可复现 headroom 就不进入训练 |

### 6.4 五维评分（只针对候选 B）

| 维度 | 分数 | 依据 | 提升条件 |
|---|---:|---|---|
| Higher | 7 | 机制型、无数据：若检索证据确实在消费者处丢失，修复该接口可能提升回访保持；当前无任何收益结果 | 六臂先证明消费者瓶颈，并与最强同预算 memory attention 对比 |
| Faster | 5 | 无依据：固定计算只是公平性约束，不是速度贡献 | 若审计能用少量 counterfactual 预测无需全量生成的失败，再独立证明节省成本 |
| Stronger | 7 | 机制型、无数据：source/view 绑定针对大视角回访和冲突历史的鲁棒性 | 在未见场景、遮挡/动态变化分层验证，并报告失败边界 |
| Cheaper | 5 | 无数据或机制证明训练/部署更省 | 保持零参数诊断；不要把缺少 GPU 包装成算法节省 |
| Broader | 6 | 机制型、无数据：检索—消费接口存在于多种外部记忆生成器，但当前只核 VMem | 至少在另一种公开 memory consumer 上复现诊断关系 |

最高上限在 Higher 与 Stronger，但均是机制判断，尚无数据。没有 8 分维度，不满足 Strong Accept。

### 6.5 Paradigm-shift probe

| 探针 | 判断 | 理由 |
|---|---|---|
| First Principles | Yes | 明确挑战“选对历史 + 全局汇总即可让生成器用对证据”的隐含假设 |
| Elephant in the Room | Partial | 检索工作常重点报告选取/最终质量，消费者因果归因较少被单独验收；但尚未系统证明社区普遍回避 |
| Technology Cycle | No | 这个诊断不依赖近两年才出现的新基础能力 |
| Hamming's Rule | Partial | 长程世界一致性重要，但单一 VMem 接口诊断本身不会改变领域优先级 |

总分 4/8：渐进式工作里有第一性原理种子，不应包装成范式革命。

### 6.6 可行性

| 风险 | 等级 | 缓解 |
|---|---|---|
| Compute | 中到高 | 先做一场景/配对 seed 的有界六臂；由真实 S40 耗时决定是否扩展，不承诺论文 GPU 速度适用于本机 |
| Data | 中 | 使用预先冻结的真实回访或可逆轨迹；开发和确认场景分开，不继续只看旧 24 个查询 |
| Engineering | 高 | 插桩只能替换 `context_encoder_embeddings`，必须逐 SHA 核其余条件、cache 内容和 RNG；另一作者审查 |
| Timeline | 中到高 | 先用退出门杀死弱假说；若需要训练新模块且无 GPU，暂停方法线或取得正式计算资源后另立协议 |

### 6.7 最终裁决

- **候选 A（mean→attention/router/geometry-guided routing/source binding/point-cloud update/geometry gate）：Reject and Pivot。** 这些分别被 EasyRef、WorldMem、WorldStereo、SPAD、EpiDiff、PoCo、Spatia、Geometry-as-Context、CorrAdapter 与稀疏路由近邻覆盖；换到 VMem 接口不足以构成方法创新。
- **候选 B（固定检索后的消费者充分性诊断）：Accept with Revisions，worth pursuing pending the validation experiment。** 它有具体隐含假设和可证伪实验，但尚无真实消费者失败、无效果数据，且精确新颖性仍需系统检索。

最先做的三件事：

1. 完成并独立核验真实 S40 声明组件变体 baseline，保存一个自然回访失败；失败不存在就停止。
2. 冻结六臂条件向量与全部相同输入，先跑 A0/A1 influence gate，再决定是否花算力跑其余四臂。
3. 若普通臂显示稳定 headroom，再做完整近邻综述并设计 source-to-region 反事实归因；普通加权已解决则只写强 baseline/诊断，不写创新方法。

## 7. 本报告实际做了什么

本轮读取固定 VMem/S38/S40 源码和记录，应用 Supervisor Handbook 2.2 的“强 baseline→具体失败→根因对照”、2.3 的隐含假设探针，以及 `idea-evaluator` 的 F1/F6、五维、生命周期和可行性门；检索并核对上述正式会议页面/论文。没有加载权重、没有运行模型、没有读取或制造生成结果、没有改主账、没有调用 Claude 模型。
