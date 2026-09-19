# S41 Gemini 第三轮建议独立核验

核验结论：**`PASS_WITH_CORRECTIONS`。** Gemini 的回答适合作为反驳清单和控制组候选，但不能直接冻结成“同信息、同计算”的六臂实验，也不能把“geometry-guided CLIP token masking”当作当前 VMem 已有接口或已成立的创新。

本次只阅读正式论文、已保存论文文本、本地固定 VMem 源码及 OpenCLIP 2.30.0 源码；没有加载模型、没有生成视频、没有读取实验答案、没有修改研究主账。

## 1. StreamingT2V 逐项核验

正式身份已核：*StreamingT2V: Consistent, Dynamic, and Extendable Long Video Generation from Text* 是 CVPR 2025 正式论文，页码 2568–2577；arXiv 标识确为 `2403.14773`。

- [CVF 正式论文页](https://openaccess.thecvf.com/content/CVPR2025/html/Henschel_StreamingT2V_Consistent_Dynamic_and_Extendable_Long_Video_Generation_from_Text_CVPR_2025_paper.html)
- [CVF 正式 PDF](https://openaccess.thecvf.com/content/CVPR2025/papers/Henschel_StreamingT2V_Consistent_Dynamic_and_Extendable_Long_Video_Generation_from_Text_CVPR_2025_paper.pdf)
- [arXiv:2403.14773](https://arxiv.org/abs/2403.14773)

| Gemini 说法 | 原文核验 | 判定 |
|---|---|---|
| StreamingT2V 是 CVPR 2025，arXiv:2403.14773 | CVF 正式页和 arXiv 标识均对应同一论文。 | **采纳** |
| 输入“过去连续 16 帧” | 主文 §4 明确：一次生成 `F=16` 帧，但 CAM 短期条件只使用前一段最后 `F_cond=8` 帧；补充材料表 A.7 也写 `Q=16, K/V=8`。首段本身有 16 帧不等于后续读取过去 16 帧。 | **拒绝并更正为过去 8 帧** |
| 首段锚点作为静态 appearance memory | 主文 §4.2 使用“very first chunk”的固定 anchor frame；补充材料说明训练时从首 16 帧随机抽一张，推理时是固定锚点。它是一张图的 1024 维 CLIP image token，经 MLP 扩成 16 tokens，不是把首段 16 帧全部存为外观记忆。 | **限定采纳** |
| “在注意力层并行读出” | CAM 是在每个空间位置独立进行 temporal cross-attention：当前 16 帧特征作 query，前一段 8 帧特征作 K/V。APM 则先将图像与文本条件混合成同一个 `x_cross`，再供原 cross-attention 使用。论文没有描述两个记忆库的“并行读出”。 | **拒绝该表述** |

与 VMem 的有效区别应写成：StreamingT2V 的 CAM 更新为“始终保留前一段最后 8 帧”，APM 长期状态为“首段一张固定锚点”；VMem 则由目标视角下可见的 Surfel 给历史帧投票并硬选 ID，再读取这些帧的 latent 和全局 CLIP 向量。两者任务、状态和读出都不同。只核一个近邻论文不足以证明新颖性。

## 2. VMem 的 CLIP 真实形状和语义粒度

固定源码给出的路径是：

1. `CLIPConditioner` 把每张图 bicubic resize 到 `224×224`，调用 OpenCLIP `ViT-H-14` 的 `encode_image`。
2. OpenCLIP 该模型的输出维度是 1024，patch size 为 14，视觉主干宽度是 1280。`encode_image(normalize=False)` 返回视觉主干的 pooled 输出；默认 `output_tokens=False`。
3. 因而 VMem 每张图实际保存一个未做 L2 normalize 的全局向量 `e_i ∈ R^1024`，不是 256 个局部 patch tokens。
4. `get_cond` 对选中的 `[N,1024]` 向量沿帧维求 mean，得到 `[1024]`，随后 repeat 成 `[num_cameras,1,1024]` 交给 cross-attention。序列长度只有 1。

这带来一个重要修正：原 VMem cross-attention 的 K/V 长度为 1，沿 K/V 维的 softmax 恒为 1。该通道仍可通过 value projection 影响生成，但原始“attention map”不能区分历史帧或局部 patch；保存它无法证明模型关注了哪张历史图。更合适的诊断是保存各干预条件的向量身份、范数、与 mean 的余弦/差值，以及固定输入下的模型输出差异。

## 3. Surfel 能否直接映射到 CLIP token

**当前接口不能直接映射。** 原因有三层：

- 保存的 `encoder_embeddings` 已经只有每图一个 1024 维全局向量，局部 token 信息已经丢失。
- `Surfel` 对象只保存 position、normal、radius、可选 color；当前构造没有写入原始像素坐标。另有 `surfel_to_timestep`，它只记录该 Surfel 对应哪些来源帧 ID。
- 目标视角渲染只返回目标像素上的 `surfel_index_map`、depth 和 cosine；它没有给出“这个可见 Surfel 在某个来源图的哪个 14×14 patch”。

OpenCLIP ViT-H/14 内部确实有 `16×16=256` 个 patch 位置，但这些内部 token 是 1280 维，且经过 32 层全局 self-attention 后已包含全图上下文；它们不是独立局部像素描述。若要使用它们，至少要：

1. 改 CLIP conditioner 暴露内部 patch tokens；
2. 将 1280 维 token 投影/适配到 VMem 期望的 1024 维；
3. 把目标可见 Surfel 重投影到每个来源相机，并进行来源视角的 z-buffer/遮挡检查，才能建立来源 patch mask；或在建图时新增可审计的像素 provenance；
4. 证明新条件分布不只是让冻结生成器偏离训练分布。

因此它不是“现成的无参数遮罩”。如果把 `256N` 个 token 直接送进 U-Net，cross-attention 的 K/V 长度会从 1 增至 `256N`，计算量和模型接口都改变；如果先 masked-pool 回一个 1024 维 token，U-Net 计算可以保持不变，但 CLIP 读出、特征分布及几何桥接仍已改变。几何打分若没有不确定性校准，也应称 score/mask，不应称“可见性概率”。

## 4. 六臂是否同信息、同计算

六臂都可以做到“新增可训练参数为 0”，前五臂也可以保持 U-Net 收到一个 1024 维 token。但这不等于同信息、同计算。

| 臂 | 实际访问的 CLIP 信息 | U-Net token / 参数 | 额外差别 | 核验结论 |
|---|---|---|---|---|
| 1. mean | 全部 N 张的全局向量 | 1 token / 0 参数 | `O(ND)` mean reduction | **原始基线，采纳** |
| 2. Surfel 重叠最高单帧 | 只保留 1/N 的图像语义；另用几何分数选帧 | 1 token / 0 参数 | 信息量减少，选择规则不同 | **可作单帧诊断，不能称同信息对照** |
| 3. 最远“或”最老单帧 | 只保留 1/N | 1 token / 0 参数 | “最远”和“最老”是两种不同规则，必须运行前二选一；前者需位姿距离，后者需时间索引 | **当前定义含糊，冻结前拒绝；明确后只作负控制** |
| 4. 按维 max | 访问全部 N 张 | 1 token / 0 参数 | 也是 `O(ND)` 量级，但运算与 mean 不同；输出范数、逐维来源和训练分布可能明显改变 | **可作 all-information stress baseline；必须保存范数/分布，不能称精确同计算** |
| 5. 全零 | 不含任何历史图像语义 | 1 token / 0 参数 | 只保留同形状和下游算力 | **有价值的通路必要性负控制，明确不是同信息臂** |
| 6. 每个去噪 timestep 随机选一张 | 每一步只看 1/N；整个轨迹可能接触多张 | 每步 1 token / 0 参数 | 当前 `get_cond` 在采样前只算一次静态条件；该臂需要修改 sampler 接口，并新增随机调度。若共用 RNG 还会改变扩散噪声。 | **拒绝纳入主六臂因果矩阵；只能另立动态压力测试** |

若保留第 6 臂，必须用独立 RNG、提前生成并哈希完整帧选择 schedule，证明采样噪声字节不变，并用多个 schedule 估计方差。即便这样，它仍不是同信息或同接口的主对照。

最清楚的报告方式是分层，而不是声称六臂完全公平：

- **原始/all-information 聚合压力测试**：mean 与 max（可再加入普通 norm-matched 全 N 加权基线）；
- **信息删除负控制**：最高重叠单帧、预先明确的 oldest 单帧、zero；
- **动态条件实验**：逐 timestep 随机切换，单独协议和随机性核验。

所有臂可以固定同一历史 ID 集合、latents、pose/K、VAE、初始 noise、扩散噪声及 U-Net 权重；但必须如实报告“被送入 cross-attention 的信息”不同。评价区域 mask 必须在查看各臂生成结果前由固定规则生成；否则会产生看过结果后挑区域的偏差。

## 5. 采纳 / 拒绝表

| 建议 | 决定 | 理由与下一条件 |
|---|---|---|
| 五个替代解释 | **采纳为反证清单** | 都能推翻“mean 是核心原因”，应在真实失败出现后逐项排查。 |
| zero 条件 | **采纳为负控制** | 可测这条全局 cross-attention 通路是否在当前样例产生可检测影响。 |
| 单帧条件 | **限定采纳** | 只作信息删除/责任诊断；不能与 mean 宣称同信息。 |
| dimension-wise max | **限定采纳** | 只作全 N 聚合压力测试；保存输出范数、余弦、数值范围及下游差异。 |
| 每 timestep 随机切换 | **主矩阵拒绝** | 改变静态条件接口并新增随机性；若以后做，须另立协议。 |
| 保存 cross-attention map | **按原提议拒绝** | 原序列长度为 1，权重图不能归因到来源帧或 patch。 |
| StreamingT2V 作为一个近邻 | **限定采纳** | 论文正式且相关；其正确输入是前段 8 帧加首段固定锚点，不是过去 16 帧。一个近邻不能完成新颖性检索。 |
| geometry-guided token masking 已可实现 | **拒绝** | 当前 VMem 只有全局 token，且没有来源像素 provenance；需新建 CLIP-token/几何桥接。 |
| geometry-guided token masking 已具有实质新意 | **拒绝/未判定** | 尚无真实 mean 失败、无接口、无强邻近工作排除、无结果。它目前只是待证机制方向。 |
| “先跑真实原 baseline；无失败则退出” | **采纳** | 符合强基线 → 自然失败 → 根因 → 方法的研究顺序。 |

最终判定：Gemini 成功提供了有用的反证和负控制，但违反了提示中“每臂写清同信息、同计算”的要求。当前能采用的是诊断结构，不能采用“六臂公平”或“token masking 创新成立”的结论。下一科学门槛仍是先完成真实 VMem 两批生成，确认自然回访失败，再冻结分层干预协议。
