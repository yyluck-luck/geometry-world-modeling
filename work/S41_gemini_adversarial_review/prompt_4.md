# Gemini 第四轮：近邻压死测试

> 发送边界：以下内容由 Codex 通过用户已登录的 Gemini 网页发送。用户已授权使用 Gemini。此文件记录发送的研究问题；Gemini 输出只作为待独立核验的外部意见。

请基于下面已经核验的新事实，纠正你上一答并做第四轮“近邻压死测试”。不要为保留想法而勉强发明方法，也不要重复宽泛建议。

源码事实：VMem 每张历史图只保存一个未 L2 归一化的 1024 维全局 CLIP 向量；N 个向量 mean 后得到一个 `[1024]` 向量，再 repeat 成 `[num_cameras, 1, 1024]`。cross-attention 的 K/V 长度为 1；现有接口没有 CLIP patch tokens，也没有 Surfel 到来源像素/patch 的 provenance。因此你上一答的“直接按 Surfel 可见性 mask CLIP token”当前不可实现，且 attention map 不能归因到历史帧。

请重点核对这些正式近邻：SPAD（CVPR 2024，epipolar cross-view attention + Plücker）；EpiDiff（CVPR 2024，latent feature 的 localized epipolar cross-attention）；Context as Memory（SIGGRAPH Asia 2025，FOV 检索 + 历史帧沿时间维 concat）；WorldMem（NeurIPS 2025，frame/pose/time state-aware memory attention）；WorldStereo（CVPR 2026，global-geometric memory 与 spatial-stereo memory，3D correspondence 约束 attention receptive field）；Spatia（CVPR 2026，可更新 point-cloud spatial memory + visual SLAM）；Geometry-as-context（CVPR 2026）；PoCo / Rethinking Position Embedding as Context Controller（CVPR 2026，多参考关联的 side-info RoPE）。只使用你能给出正式会议页、DOI 或 arXiv 的来源；不确定细节就写未核实。

输出不超过 1600 中文字：

1. 明确撤回或保留上一答中的哪些主张；
2. 用“输入/状态/更新/读出”四轴说明上述工作中最接近的 4 项如何覆盖普通 geometry-guided routing；
3. 这些近邻之后，VMem 的 global-mean 问题还剩哪个最窄、可证伪、尚不能宣称新颖的研究问题；
4. 给最多 5 臂的诊断顺序，先区分 cross-attention 有无作用、global bottleneck、来源身份丢失、concat 主导；如无法同信息就明确写信息不同；
5. 列出会立即否决方向的结果；
6. 一句裁决：现在是基线调试、可研究的新问题，还是已有机制覆盖。

当前没有真实 VMem 视频结果；不要声称创新成立、不要建议训练大模型、不要把普通 attention/router/epipolar mask 换名。

