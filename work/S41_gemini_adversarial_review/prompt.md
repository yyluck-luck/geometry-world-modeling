# Gemini 第三轮反驳审查提示

你是一个严格的 CVPR/ICCV/NeurIPS 审稿人。以下是当前真实研究状态，请只做反驳性设计审查，不要虚构实验、接口或引用。

目标：真实 VMem 基线跑通后，诊断“几何选图正确时，VMem 把多张历史图的 CLIP embedding 直接平均，是否会丢失回访时的实例/局部细节”。

已核源码事实：Surfel 几何只负责选历史 frame IDs；`get_cond` 把选中的 CLIP embedding 求平均进入 cross-attention；concat 通道是历史 latent 和 mask/Plücker；没有 Surfel 颜色注入；`samples_z` 是未来帧 latent。当前未生成真实视频、未验证失败。

约束：先固定相同历史 IDs 与顺序、latent、pose/K、noise/seed、VAE 和算力，只替换 cross-attention embedding 聚合。普通 mean、nearest、anchor、norm-matched weighted 都是基线，不能作为创新。

请输出：

1. 最可能推翻这个假设的 5 个解释；
2. 最便宜但严谨的干预矩阵，不超过 6 臂，并写清每臂保持相同的信息量、参数和计算；
3. 每项必须保存的证据，以及失败和退出条件；
4. 与近年最相近正式论文的“输入、状态、更新、读出”四轴区别。只列你能给出可核正式 URL、DOI 或 arXiv 的论文；不确定就写不确定；
5. 如果 mean 确实失败，什么机制才可能具有实质新意，什么只是普通 attention 或 router；
6. 一句 reviewer verdict：现在离可投稿方法还缺什么。

不要建议 Surfel 颜色注入、不存在的 KV 接口、用 GT 选择权重、改模型后再声称相同输入，或把组件替换当创新。明确区分源码事实、机制推论和待实验假设。
