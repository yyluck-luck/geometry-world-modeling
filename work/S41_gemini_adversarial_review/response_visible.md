# Gemini 第三轮可见回答

> 保存边界：以下内容由 Gemini Pro Extended 页面可访问性树中实际可见文本人工转录并整理 Markdown；页面不支持正文导出，因此不声称与 DOM 字节完全相同。它是外部模型建议，不是论文事实、源码事实或实验结果。引用和机制须另行核验。

作为严格的审稿人，我在此对你的研究切入点进行设计审查。你的假设明确：在基于 Surfel 选出正确历史帧 ID 的前提下，VMem 在 `get_cond` 中对选中的 CLIP embedding 进行平均操作，导致了回访时实例/局部细节的丢失。

请注意区分：代码逻辑（求平均、拼接 latent）是已知事实；求平均导致细节丢失是待验假设；模型如何分配通道权重则是机制推论。

## 1. 最可能推翻假设的 5 个替代解释

1. 通道责任错位：局部细节可能主要依赖 concat 通道，而不是 CLIP cross-attention；修改 CLIP 聚合因此可能没有收益。
2. VAE 压缩与时序衰减：高频信息可能已经在 VAE 或自回归过程中退化，语义条件无法恢复。
3. Plücker 射线或 mask 对齐误差：即使选图正确，pose/K 与射线编码的对齐误差也可能产生模糊。
4. 多视角光度不一致：几何重叠的历史图仍可能有光照、模糊或遮挡变化，任一单帧也无法提供目标细节。
5. 预训练输入分布：模型可能习惯平滑全局的 CLIP 条件，非平滑聚合可能偏离训练分布并被忽略。

## 2. 建议的六臂干预矩阵

回答声称固定历史 ID、pose、latent、seed 等，不增加参数，并保持输入 U-Net 的 token 序列长度：

1. 原始 mean；
2. 仅取 Surfel 重叠率最高的单帧；
3. 仅取最远或最老单帧；
4. 对 N 个 embedding 按维度 max pooling；
5. CLIP embedding 全零或空条件；
6. 每个去噪 timestep 从 N 帧随机抽一个 embedding。

## 3. 证据与退出条件

回答建议保存回访区域二值 mask、六臂生成视频、逐帧差异图，以及 cross-attention map。它给出三个退出条件：

- 全零 CLIP 与 mean 无差异：这条 cross-attention 通路可能不承担被测细节，应退出该切口；
- mean 与单帧均模糊：mean 不是核心原因，应转查 concat/latent 或几何 mask；
- 真实原始 baseline 不出现预期细节丢失：回到真实失败观察。

## 4. 回答列出的近邻工作

回答只列出 `StreamingT2V`，称其为 CVPR 2025、arXiv:2403.14773，并给出 [arXiv 链接](https://arxiv.org/abs/2403.14773)。回答称它以文本和过去连续 16 帧为输入，以首段锚点帧高维特征作为静态 appearance memory，并在注意力层并行读出；再把 VMem 的 Surfel 历史 ID 硬选择视为区别。这些具体描述待正式论文逐项核验。

## 5. 回答对“实质新意”的判断

回答把 Transformer、router、MLP 加权或 token 筛选判为普通组件替换；它建议一种无参数的“geometry-guided token masking/routing”，用 Surfel 投影深度或射线视角解析得到每个视角 CLIP token 的可见性概率，再屏蔽 cross-attention。该建议尚未证明 VMem 的 CLIP embedding 具有可对应 Surfel/像素的空间 token，因此暂不能当作可实现机制或创新。

## 6. 回答的 reviewer verdict

回答认为当前仍像聚合瓶颈调试，尚缺 cross-attention 与 concat 责任的排他性消融，也缺少把三维几何可见性与潜空间读取建立明确映射的机制核心。
