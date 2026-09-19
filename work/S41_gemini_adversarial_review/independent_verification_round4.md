# S41 · Gemini 第四轮独立核验

- 核验时间：2026-09-07 13:45 CST（UTC+08:00）
- 核验对象：`prompt_4.md`（SHA-256 `26c6356316e2fef61f6181b85db45859a33f2cfccd183448d686980d1d368d77`）、`response_4_visible.md`（SHA-256 `492205850b40a0700b12c005c67998a16eed003b435ca3dee8d805b0e6cde1f4`）
- 方法：只读本地固定 VMem 源码、VMem/WorldMem 本地论文正文和正式会议/作者原始页面；没有加载模型、没有生成视频、没有运行任何实验，也没有修改主研究账。
- 回答裁决：**`PASS_WITH_CORRECTIONS`**。

Gemini 的大方向是对的：撤回当前接口无法实现的 CLIP token 几何 mask，把问题降为基线消费者诊断，并拒绝把普通几何路由包装成创新。但回答包含一个关键架构误称、漏掉三个会进一步压缩创新空间的近邻，而且五臂中 `source sequence` 不是公平或干净的因果干预。其结论可以保留，实验表和措辞不能原样采用。

## 1. 逐项采纳 / 纠正 / 拒绝

| Gemini 主张 | 裁决 | 独立核验结果 |
|---|---|---|
| 撤回 Surfel-visible CLIP token mask | **采纳** | 当前 conditioner 每图只返回一个 1024 维 OpenCLIP `encode_image` 全局向量，没有 patch token；当前 Surfel 也没有来源像素/patch provenance。 |
| 普通 geometry-guided routing 已很拥挤 | **采纳但补全近邻** | SPAD、EpiDiff、WorldStereo、Spatia 均支持此判断；WorldMem、Context-as-Memory、PoCo 使 generic multi-token/source-ID/history-concat 方案更难主张新颖。 |
| VMem 是“global CLIP cross-attention + spatial latent concat” | **拒绝** | 历史 latent 不在 `concat`；它通过 `replace` 在每次 denoiser 调用前钳入输入。`concat` 只有一位输入 mask 和六通道 Plücker。 |
| mean / zero / single 三臂可先诊断 | **有条件采纳** | 三者可保持网络权重、随机噪声、输出形状和 denoiser 次数相同，但它们的信息量不同；single 必须预先固定来源规则，并控制或至少报告向量范数。 |
| `[N,1024]` sequence 是来源身份上界 | **拒绝作为主矩阵；仅可作后续 OOD 压力测试** | 数学接口能接收多 token，但它把单 key 广播变成 query-dependent 多 key 选择，增加 cross-attention 计算，且没有 source ID/pose side information。发布接口只构造 K/V=1；没有训练代码证明 checkpoint 学过 K/V>1。 |
| mismatched scene 只改风格即可否决 mean 的局部身份问题 | **拒绝该强退出结论** | 它可测通路的粗粒度语义敏感性，但“只改风格”不能证明 mean 没有损失实例信息；无关向量还引入场景分布与范数差异。 |
| 当前仍是基线架构调试 | **采纳** | 尚无真实 VMem baseline 回访失败、CLIP 通路因果效应或任何方法增益。 |

## 2. VMem 四条条件通路的源码纠错

固定源码快照：

- `modeling/pipeline.py` SHA-256 `680da1c14db8a6780a37fca3a8bac5bb59f0aa7d395db96d4360b352eb7f2255`
- `modeling/network.py` SHA-256 `9ed21c2d804734d7ca2d81b1e596858835ca70a4a04abb9b5540b872515d4c9b`
- `modeling/sampling.py` SHA-256 `dc07ca0ba571ba5fb48f9856515d2cb7dea25254008a6f8b315538817f352b24`
- `modeling/modules/transformer.py` SHA-256 `5f0d152a2f6464076cb0ee5aca725b3445420a5f37ac571d3daa77e580e65764`
- `modeling/modules/conditioner.py` SHA-256 `b79eb0cf4d94345a720a9a844c7daa6206b0a9234d714b7f9f23a9571c7c5fc1`

| 条件键 | 实际内容与构造 | 真正消费位置 | 能否称“spatial latent concat” |
|---|---|---|---|
| `crossattn` | `conditioner.py:36–39` 调用 OpenCLIP `encode_image`；`pipeline.py:1124–1125` 对 K 个全局向量求 mean；`1150` 复制为 `[num_cameras,1,1024]` | `network.py:233` 作为 `y`；`transformer.py:53–75,96–110` 形成 cross-attention K/V | 否；这是单个全局 token |
| `replace` | `pipeline.py:1143–1156` 给历史 VAE latent 补一位值为 1 的 mask，目标为零；历史槽保存真实 latent | `sampling.py:179–185` 在每次 denoiser 调用前执行 `input=input*(1-mask)+x*mask` | **这才是历史 spatial latent 通路**，但操作是 replacement/clamping，不是 concat |
| `concat` | `pipeline.py:1158–1172` 只拼接输入帧 mask（1 通道）与 Plücker（6 通道） | `network.py:229` 与当前 noisy latent 按 channel 拼接；4+7 对应 `network.py:20–31` 的 `in_channels=11` | 否；没有历史 latent |
| `dense_vector` | `pipeline.py:1173–1174` 再次传入同一 Plücker 图 | `network.py:234` 作为 `dense_y`；`layers.py:108–133` 经 1×1 conv 形成空间 scale/shift | 否；这是 dense camera-ray condition |

因此正确的问题是：**单个 global CLIP token 是否对真实回访输出有作用，以及它是否被 `replace` 历史 latent 与两条 Plücker 相机条件压过。** 不能再写“concat latent 主导”。若真要测 `concat`，应只改变其输入 mask 或 Plücker分量，并与 `dense_vector` 中重复的 Plücker 分开做因子消融；否则无法归因。

### K/V=1 与 sequence 的本质差别

`transformer.py:63–74` 的注意力实现本身接受任意 context 长度，所以把条件改成 `[num_cameras,N,1024]` 在张量接口上可实现；无条件分支也必须同步扩为同一 N，否则 CFG 批拼接会失败。但当 K/V 长度为 1 时，softmax 只有一个元素，权重恒为 1；cross-attention 输出是同一个 value projection 向每个 query 广播，不能根据 query 在历史来源间选择。改成 N 个 token 后，注意力首次获得 query-dependent source mixing，计算/显存中的 cross-attention K/V 项随 N 增长，行为类别也发生变化。

发布仓库只有 inference 路径；该路径始终先 mean 再构造长度 1。VMem 正文只确认 K=4、M=4 的 LoRA 微调，没有提供本核验可见的训练代码来逐批证明训练 context 长度。因此最严谨的说法是：**sequence 臂相对发布 checkpoint/interface 是未验证、很可能分布外的结构性干预；不能无证据写成“已绝对证明训练时只见 K/V=1”，也不能用其成败归因 mean。** 此外，原 cross-attention 没有给这些 N 个向量附加 source ID、pose 或时间；它保留的是 N 个内容向量，而不是可寻址的来源身份。

## 3. Gemini 点名四项工作的正式源核验

| 工作与正式状态 | 输入 | 状态 | 更新 | 读出 | 对 Gemini 的核验 |
|---|---|---|---|---|---|
| [SPAD, CVPR 2024, pp.10026–10038](https://openaccess.thecvf.com/content/CVPR2024/html/Kant_SPAD_Spatially_Aware_Multi-View_Diffusers_CVPR_2024_paper.html) | 文本或单图、目标相机、多视图扩散特征 | 同一次生成中的多视图空间 feature maps；不是长期 memory bank | 微调加入的跨视图模块；无在线长期记忆写入 | epipolar-constrained cross-view attention；Plücker ray 作为位置编码 | **基本正确**。它覆盖“几何限制空间跨视图注意力”，不覆盖长期回访记忆。 |
| [EpiDiff, CVPR 2024, pp.9784–9794](https://openaccess.thecvf.com/content/CVPR2024/html/Huang_EpiDiff_Enhancing_Multi-View_Synthesis_via_Localized_Epipolar-Constrained_Diffusion_CVPR_2024_paper.html) | 单图、相机、邻近视图 latent/features | 邻近视图的局部 feature maps；不是持久历史缓存 | 冻结基础扩散模型，训练新增 epipolar module；无运行时记忆更新 | localized epipolar attention 在邻近视图 feature maps 间交互 | **基本正确**。覆盖局部对极读出，不是 VMem 的 memory consumer。 |
| [WorldStereo, CVPR 2026, pp.40327–40339](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_WorldStereo_Bridging_Camera-Guided_Video_Generation_and_Scene_Reconstruction_via_3D_CVPR_2026_paper.html) | 历史/参考帧、目标/参考相机、pointmaps、3D cache | incrementally updated point-cloud GGM + 2D reference memory bank/SSM | 新视频进入 bank，点云增量更新与对齐；SSM 分支从头训练 | 先按 3D FOV 检索；独立编码参考，将 target-reference latent 水平拼接并加 pointmap latent；每对只在自己的 `H×2W` 范围 attention | **正确但 Gemini 过度简写**。它不是一个现成 mask，而是有专门训练的 target-reference 分支；直接压死普通“3D correspondence routing”新意。 |
| [Spatia, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/papers/Zhao_Spatia_Video_Generation_with_Updatable_Spatial_Memory_CVPR_2026_paper.pdf) | 条件图/已生成视频、相机轨迹、历史参考 | 持久 scene point cloud + previous clip/reference frames | 以 visual SLAM 把新旧帧更新进点云，显式分离静态空间记忆与动态内容 | 按目标轨迹渲染 2D point-cloud sequence，并取空间重叠参考帧条件生成 | **基本正确**。点云更新、投影条件和长期回访均已有直接近邻。 |

四项合起来足以否决“普通 geometry-guided routing 是新方法”，但 SPAD/EpiDiff 只能作为基本算子近邻；真正接近长期 memory consumer 的是 WorldStereo/Spatia 以及 Gemini 漏掉的下列工作。

## 4. 三个漏项是否改变裁决

| 漏项 | 正式证据与关键机制 | 对当前想法的影响 |
|---|---|---|
| [WorldMem, NeurIPS 2025 Main, DOI 10.52202/085713-1659](https://proceedings.neurips.cc/paper_files/paper/2025/hash/470629a47e2d65ce0606c40055df5d26-Abstract-Conference.html) | memory unit 绑定 visual frame tokens、pose、timestamp；按 FOV/时间检索；当前 flattened features 查询拼接的 memory tokens，并把相对 state embedding 加到 Q/K | 最直接覆盖“保留多来源并让 query 读取”的方向。它说明 raw CLIP sequence 缺的正是 state/source binding 与相应训练。 |
| [Context-as-Memory, SIGGRAPH Asia 2025, DOI 10.1145/3757377.3763833](https://doi.org/10.1145/3757377.3763833)；[arXiv 2506.03141](https://arxiv.org/abs/2506.03141) | 历史帧直接作为 memory；按相机 FOV overlap 检索；在输入的 frame dimension 拼接 context 与待预测帧，并专门微调可变历史条件 | 是“不做 global mean、直接消费历史帧”的强近邻/强基线，也证明 frame-sequence 接口通常需要训练适配。 |
| [PoCo, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/papers/Huang_Rethinking_Position_Embedding_as_a_Context_Controller_for_Multi-Reference_and_CVPR_2026_paper.pdf) | 在多参考/多镜头生成中，以 reference identifier 等 side information 扩展 RoPE，让 Q-K 关联受到显式来源控制 | 任务不同，但“多个相似参考会混淆，需显式 source side-info”已有直接机制先例；普通 source tag/positional binding 很难作为核心创新。 |

这些漏项**不改变** Gemini“当前只是基线调试”的总裁决，却使其更加严格：`[N,1024]` raw sequence、source ID、frame-dimension concat 都不能再被当作自然的新方法。剩余可研究问题只能收窄为消费者充分性与可寻址性诊断，而且仍需真实失败和跨模型证据才可能上升为“新问题”。

## 5. Gemini 原五臂的可实现性与公平性

共同可固定项应包括：同一 K 个历史 ID/顺序及其已编码数组、`replace`、`concat`、`dense_vector`、camera/K、初始 noise tensor、RNG 前后状态、sampler/CFG/steps、模型/VAE/decoder 和评估 mask。即使这些全固定，也不代表各臂“同信息”。

| 臂 | 可实现性 | 信息公平 | 计算公平 | 能回答什么 / 不能回答什么 |
|---|---|---|---|---|
| mean | 直接已有 | 参考条件 | 参考计算 | exact replay 基线；必须先逐值复现。 |
| zero CLIP | 简单；令 conditional `crossattn` 为同形状零 | **不同：删除全部 CLIP 信息** | shape、参数、denoiser 次数与主要 FLOPs相同 | 干净的 CLIP 通路 causal negative control；不能当性能算法。 |
| fixed single source | 简单；仍输出 `[C,1,1024]` | **不同：仅保留一来源**；选择规则不可看输出，需报告/控制 norm | 下游基本相同 | 若不同来源产生稳定差异，说明 global token 通路有来源内容敏感性；仍不能证明局部 source-to-region 对齐。 |
| source sequence | 张量上可行；`c`/`uc` 都要扩为 `[C,N,1024]` | **不同：保留 N 个未平均向量，信息更多** | **不同：K/V 长度与 attention 成本增加** | 只能作 OOD architecture upper bound。成功可能来自新增 query-dependent selector；失败可能来自 checkpoint 未适配。两者都不能单独判 mean。 |
| mismatched scene | 可用同一 encoder 的固定无关图向量实现 | **不同：替换为外部场景语义** | 若保持单 token，计算基本相同 | 粗测语义/风格敏感性；需预先固定图、匹配或报告 norm。style-only 结果不是 mean 局部身份假说的充分否证。 |

原五臂全部保持 `replace`/`concat`/`dense_vector` 不变，所以它们**不能直接区分哪条非 CLIP 通路主导**。将 mismatched scene 说成“保持 concat 历史 latent”再次暴露了同一架构混称。

## 6. 建议采用的最多五臂、按门执行的最小诊断

这不是一次性全跑矩阵；前一门失败就停止，避免在无效假说上消耗本机 CPU 时间。

1. **Gate 0：真实自然失败。** 先完成冻结组件的原 baseline 两批闭环，核第二批实际消费第一批 `samples_z`；在看任何替代结果之前冻结场景、轨迹、seed、历史 IDs、回访区域和失败指标。若没有稳定自然失败，整个方向停止。
2. **A0 exact mean replay。** 保存所有条件张量、noise 与输出 hash。不能复现原 baseline 就先修接线，不能做科学比较。
3. **A1 zero crossattn。** 只把 conditional global token 置零，其余逐值相同。A1≈A0 即停止 CLIP/mean 路线；这已足够说明当前指标下没有 CLIP 因果效应，无需 sequence。
4. **A2 / A3 两个预声明 single-source。** 在生成前按固定几何支持规则选择“最高支持”与“最低支持”来源；仍为单 token。先匹配到 A0 mean 的 L2 norm，并保存原始 norm/缩放系数；若出现信号，后续再用 raw norm 做稳健性复核。它们信息不同，但下游 shape/计算相同。A2 与 A3 没有稳定方向性差异，则没有来源可寻址证据。
5. **A4 `replace`-permutation 负对照。** 对 K 个历史 `replace` latent 槽做预声明循环置换，mask、Plücker、global mean、noise 全部保持原值。它保留相同 latent 多重集、shape 和计算，只破坏 latent 与相机/时间槽的绑定；若造成远大于 A2/A3 的退化，说明主要可寻址历史证据位于 `replace` 路径，而不是 global mean。该臂是故意错配的机制压力测试，不能作为性能方法。

这五臂优先覆盖“CLIP 是否有作用 → global token 是否对来源内容敏感 → spatial history 的 latent-to-pose 绑定是否更强”。若之后必须区分 `concat` 与 `dense_vector`，另立一个小型 2×2 相机条件消融：分别固定另一条而移除 `concat` 中的 mask/Plücker或 `dense_vector` 中的 Plücker；这属于新的 OOD 诊断，不能塞进上述五臂后声称同信息。

`source sequence` 和 mismatched scene 均移到 Gate 1/2 通过后的附加 sanity/upper-bound，不进入最小主矩阵。

## 7. 可执行的退出条件与科学边界

- 原 baseline 没有预注册的真实回访失败：**停止该问题**。
- A0 不能 exact replay：**停止归因，先修接线**。
- A1 与 A0 的配对输出在预注册数值容差、回访区域指标和人工盲看中均无稳定差异：**停止 CLIP mean 方法线**。
- A2/A3 只产生全图色调漂移，或差异不随预声明的几何支持关系改变：**不宣称 source identity/addressability**。
- A4 的效应显著大于 A2/A3：将主要解释转向 `replace` latent-to-camera 绑定；不能把它写成 concat 或 CLIP mean 创新。
- sequence 只有在改变 K/V 长度后才改善：只能记录为未训练接口的 upper bound；在训练适配、同计算强基线以及 WorldMem/PoCo/Context-as-Memory 对照前，**不算算法收益或新颖性**。
- 任一效果只在一个场景/seed、向量 norm 未控制、或以相机服从/视觉质量下降换取回访相似度：**拒绝中心机制解释**。

当前证据只能支持：**宽泛方法 `REJECT AND PIVOT`；窄问题 `BASELINE DIAGNOSTIC / ACCEPT WITH REVISIONS`；Gemini 第四轮回答 `PASS_WITH_CORRECTIONS`。** 真实模型加载次数、真实生成视频数和已验证性能改善数在本核验中均为 0。

