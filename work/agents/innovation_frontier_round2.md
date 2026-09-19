# 创新前沿检索 Round 2：历史几何风险能否预测未来几何误差？

- **检索时间**：2026-09-12（Asia/Shanghai）
- **执行目的**：对 GRC-Memory 候选做第二轮审稿式反证，重点检查 2025--2026 原始论文是否已经定义或实验证明了：
  `observation-level calibrated geometric risk -> externally supplied, held-out future RGB-D/pose reference error`。
- **证据边界**：本文件是原文近邻审查，不是新颖性证明，也没有运行这些论文代码。当前项目仍为 `new_method_validated=false`、`novelty_authorization=NONE`。分类只使用三类：**已覆盖、部分覆盖、尚无证据**。
- **检索来源**：原始 arXiv HTML/摘要、CVF Open Access、NeurIPS/OpenReview 或出版社原始页面；没有把搜索摘要当作实验结果。

## 1. 先固定被审查的完整命题

被审查的不是“有几何记忆”“有不确定性”或“选择较少帧”这些宽泛表述，而是下面的联合命题：

> 在显式、可寻址的历史观测中，使用**经过独立校准的观测级几何风险**选择固定预算的历史项；历史项经过同一 world-model 的完整消费路径后，风险排序能够在未参与选择的未来查询上预测或降低 RGB-D/相机位姿误差，并且结论在公平计算/存储预算和 source identity（究竟是哪条历史项造成变化）下成立。

因此，以下事实分别归类，不能因为单项相似就宣布整个命题已被覆盖或已被证明。

## 2. 已覆盖：不能单独作为 GRC-Memory 的创新

### 2.1 几何记忆、长期记忆、固定/压缩记忆

- **Video World Models with Long-term Spatial Memory (2025)**：已经把长期空间记忆、几何绑定的存储/检索和长期回访一致性作为核心问题。仅说“用几何长期记忆维持长时一致性”已被覆盖。原文：https://arxiv.org/abs/2506.05284
- **Spatia: Video Generation with Updatable Spatial Memory (CVPR 2026)**：使用可迭代更新的 3D 点云记忆、场景投影和空间相关参考帧；闭环回到初始视角并用 PSNR/SSIM/LPIPS/Match Accuracy 衡量一致性。持久空间记忆和闭环回访评价已被覆盖。原文：https://openaccess.thecvf.com/content/CVPR2026/papers/Zhao_Spatia_Video_Generation_with_Updatable_Spatial_Memory_CVPR_2026_paper.pdf
- **MosaicMem (2026)**：把历史 patch 提升到 3D 进行定位和定向检索，并用 patch-and-compose 让应保持的内容与应变化的内容分离。空间定位检索和动态/静态内容的记忆混合已被覆盖。原文：https://arxiv.org/abs/2603.17117
- **RELIC (2025)**：把相对动作和绝对相机姿态编码进压缩历史 latent/KV memory，报告长时空间检索和一致性。相机感知的长期记忆已被覆盖。原文：https://arxiv.org/abs/2512.04040
- **Memorize When Needed (2026)**：提出独立 memory branch、每帧 cross-attention、camera-aware gating，决定有历史参考时才使用记忆。按“相关帧才写入/使用记忆”和相机门控本身不能作为新颖性。原文：https://arxiv.org/abs/2604.18215
- **Latent Spatial Memory / Mirage (2026)**：把 latent token 通过深度反投影放入持久 3D cache，在 latent 空间直接查询新视角；论文报告生成速度和 memory footprint 改善。latent/显式空间记忆表示差异已被覆盖。原文：https://arxiv.org/abs/2606.09828

### 2.2 一般意义的选择、遗忘、预算或不确定性

- **GIM-World (2026)**：在历史编码前进行信息引导的 pruning，并使用固定大小 memory token；“固定容量下保留信息量更高的历史”已有明确实例。原文：https://arxiv.org/abs/2606.02436
- **MemoNav (CVPR 2024)**：STM/LTM/working-memory 和 forgetting module 已覆盖“保留 informative history”这一宽泛机制。原文：https://openaccess.thecvf.com/content/CVPR2024/html/Li_MemoNav_Working_Memory_Model_for_Visual_Navigation_CVPR_2024_paper.html
- **WorldMM (CVPR 2026)**：用多种时间尺度和多种记忆模态的自适应检索，说明 query-dependent memory selection 已在长视频推理中出现；但它不是几何 world-model 评价。原文：https://openaccess.thecvf.com/content/CVPR2026/papers/Yeo_WorldMM_Dynamic_Multimodal_Memory_Agent_for_Long_Video_Reasoning_CVPR_2026_paper.pdf
- **World Models That Know When They Don't Know / C3 (2025/2026)**：对生成视频输出做 latent-space、subpatch-level calibrated uncertainty，并映射到 RGB 不可信区域，同时做 OOD 检测。校准不确定性和未来帧置信度已被覆盖；它校准的是**模型输出**，不是历史观测条目风险。原文：https://arxiv.org/abs/2512.05927
- **Long-Context State-Space Video World Models (ICCV 2025)**：以 SSM + 局部因果注意力维持长时状态，使用 spatial retrieval/reasoning 评价长期记忆。长上下文状态记忆和未来空间检索指标已被覆盖。原文：https://openaccess.thecvf.com/content/ICCV2025/html/Po_Long-Context_State-Space_Video_World_Models_ICCV_2025_paper.html

这些工作意味着下面几句话不能单独当贡献：

1. “我们加入一个 geometry-aware memory”；
2. “我们用 confidence/uncertainty 做记忆选择”；
3. “我们加入 forgetting/gating/pruning”；
4. “我们把固定预算和未来一致性放在一起”；
5. “我们用 RGB-D/深度或重投影误差评价空间记忆”。

## 3. 部分覆盖：最接近，但没有覆盖完整联合命题

### 3.1 GIM-World：最危险的直接近邻

GIM-World 的原文方法明确写出：

- 历史由 `(frame, camera pose)` 组成；
- 先用 pose-time Gaussian-process kernel 计算信息增益，再贪心 pruning；
- 训练时用 camera-queryable geometry head 让固定大小 memory 回答几何查询；
- 评价包含 memory quality、relative pose error 和 normalized dense reprojection score。

这已经覆盖了“历史选择 + 几何监督 + 固定容量 + 未来/回访几何指标”的大部分表面结构。它仍未在原文方法和摘要证据中覆盖：

- 每个**观测条目**的几何风险上界或 conformal/校准保证；
- 该风险是否预测**独立、未用于选择的未来 RGB-D/pose 答案**；
- source identity 的删除/替换干预，或完整消费路径的增量效应；
- 在 GPU cache、host memory、forward 次数和选择时间都固定后的风险—收益比较。

**审稿结论**：GRC 不能把“information-guided pruning + geometry supervision”重新命名为新方法；可保留的差异只能是可证伪的评价问题和证据合同。原文（含方法和实验段落）：https://arxiv.org/html/2606.02436v1

### 3.2 C3：校准了视频输出，但对象和目标不同

C3 训练可校准的未来视频不确定性，并在 RGB 子 patch 定位不可信区域；它直接压力测试“calibrated uncertainty”这一词。但 C3 的不确定性是**输出帧的 latent/pixel uncertainty**，不是历史帧重投影/深度/可见性风险，也没有把历史条目在固定 memory budget 下选择后再用独立 RGB-D/pose 真值验证。

**审稿结论**：若 GRC 只写“引入校准 uncertainty”，属于已覆盖；若能证明历史几何证据的校准值在完整 memory consumer 中预测未来几何误差，仍是不同问题，但目前没有证据证明它成立。

### 3.3 OUGS 与近期 active-view uncertainty：不确定性驱动视图选择已成熟

**OUGS: Active View Selection via Object-aware Uncertainty Estimation in 3DGS (2025/2026)** 从 3D Gaussian 的位置、尺度、旋转和外观参数传播协方差，生成空间 uncertainty map，用 object mask 选择 next-best views，并用 AUSE 等方法校准预测误差。

它已经覆盖：物理几何参数的不确定性、uncertainty-driven view selection、预算下的重建质量评价。它没有把被选历史送入生成 world-model，也没有以独立未来 RGB-D/pose 的 source-level 结果验证历史风险。

**审稿结论**：GRC 的“由几何误差构造选择分数”不能单独称新；真正尚未被其覆盖的部分是历史记忆条目→完整生成消费者→未来状态误差这条链。原文：https://onlinelibrary.wiley.com/doi/10.1111/cgf.70363

### 3.4 动态/混合记忆工作：覆盖了相关性检索，但不是几何风险校准

**Out of Sight but Not Out of Mind / HyDRA (2026)** 用时空 relevance-driven retrieval 处理遮挡后动态主体重新出现；**Memorize When Needed** 用每帧 cross-attention 和 camera-aware gating；**MosaicMem** 用空间定位和动态内容修复。这些工作表明“只保留相关历史”已有多种形式。

它们没有提供 observation-level calibrated geometry-risk 对独立未来 RGB-D/pose loss 的预测性，也没有 source identity 的因果/反事实验证。

原文：
- https://arxiv.org/abs/2603.25716
- https://arxiv.org/abs/2604.18215
- https://arxiv.org/abs/2603.17117

## 4. 尚无证据：本轮检索没有找到完整联合定义

截至 2026-09-12，本轮查到的原始论文中，没有找到同时满足下面全部条件的工作：

1. 选择单位是**历史观测/记忆 item**，不是生成输出、参数、查询标签或整段 latent state；
2. 风险来自重投影、深度、可见性等**历史几何证据**，并在独立校准集上得到可复查的风险上界；
3. 预算固定且公平核算（帧/token、GPU cache、host memory、选择时间、forward 次数）；
4. 选择后通过同一 world-model 的**完整消费路径**生成未来；
5. 评价目标是未参与选择的独立 RGB-D 与相机位姿真值，而非只做当前重建、闭环初视角或检索成功率；
6. 同时报告 mean loss、worst-tail/CVaR、重投影/coverage 和 source identity 的 paired effect；
7. 对比 recent/random/pose/coverage/depth/confidence/MI-GP/强空间记忆基线，并做噪声 replay、placebo 与跨轨迹复现。

这只是“在已检索原始来源中尚无证据”，不是对全世界文献的绝对不存在证明；也不代表 GRC 候选已成立。它仅说明候选问题仍有一个可能独立的**实验性空白**。

## 5. 最小可证伪实验（数据门通过后才能运行）

这个实验的目的不是证明 GRC 有效，而是尽快把候选判成成立或失败。

### 5.1 数据和信息隔离

- 优先使用通过授权获取的一组 3RScan reference/rescan，或另一套具有完整 RGB、16-bit depth、时间同步、内参 K、6DoF pose 和场景划分的数据。
- 分成 calibration history、selection history、future query 三部分。任何 future depth/pose/RGB 答案都不能参与风险阈值、分位数、调参或候选排序。
- 至少 5 条独立轨迹，每条至少 3 个 future query；固定随机种子、动作/相机轨迹、生成步数和其他历史项。

### 5.2 选择和基线

固定主预算 `k=4`，敏感性 `k=2,8`。在同一候选池比较：

1. recent/sliding-window；
2. random（固定 seed，重复）；
3. pose-distance；
4. coverage/visibility；
5. depth-only；
6. model confidence-only；
7. GIM-World 风格 pose-time GP/MI pruning；
8. risk-only（历史几何风险）；
9. utility-only（不允许偷看 future answer 的 proxy）；
10. risk + utility（候选 GRC）。

每种方法记录被选 frame ID、source provenance、token/帧数、GPU cache、host memory、选择时间、forward 次数以及实际送入消费者的内容；不能把“忘记的节点仍留在地图”当作已释放内存。

### 5.3 指标和判断

对每个 future query 报告：

- 全体 paired mean AbsRel；
- worst-5% error mass 和 CVaR95；
- RGB-D 重投影误差、coverage；
- 相机平移/旋转误差；
- 同一 source identity 的删除/替换增量，固定干预前外生条件但让目标 source 的所有后代自然重算；
- replay noise 分布和 95% CI；
- 端到端 latency、GPU/host memory、bytes 和 forward 次数。

### 5.4 预先写好的 kill criteria

出现下列任一项时，停止 GRC 方法主张，只保留诊断/benchmark 结果：

- selection 看到了 future answer 或用 future query 调阈值；
- risk 分数在 held-out trajectories 上不比 pose/MI/confidence 更能预测未来几何误差；
- mean 或 tail 改善只来自更多 token、更多计算或场景身份泄漏；
- source-level effect 小于固定 replay noise，或无法定位到被选 source；
- 3RScan/其他数据只有 metadata、没有合法且可验证的 RGB-D/pose frame bodies；
- GIM-World 风格 pruning 或强空间记忆基线在相同预算下已匹配全部收益。

### 5.5 最小通过条件（仍不等于论文录用）

只有在至少 5 条独立轨迹 × 3 个未来查询上，历史风险分箱对未来 loss 具有预注册的单调关系，并且 risk+utility 在相同 budget/capacity 下相对最强 baseline 的 mean 和 tail paired improvement 超过 replay-noise CI，同时 source identity 可复核，才有资格重新审查“方法贡献”而不是仅“测量问题”。

## 6. 本轮审稿式裁决

- **已覆盖**：几何长期记忆、动态/空间检索、forgetting/gating/pruning、固定容量、生成输出不确定性校准、闭环或重投影评价。
- **部分覆盖**：GIM-World（最接近：历史 pruning + geometry supervision + future geometric metrics）、C3（calibrated video uncertainty 但对象不同）、OUGS（物理 uncertainty 驱动视图选择但消费者不同）、HyDRA/Memorize/MosaicMem（相关历史检索但没有风险校准和未来 RGB-D/pose source-level 验证）。
- **尚无证据**：完整的“历史观测级校准几何风险 → 固定预算、完整消费路径下独立未来 RGB-D/pose 误差”的联合定义与证据合同。

**最终决定**：GRC-Memory 仍只能作为候选研究问题；不授权“新方法已成立”的表述。S93 TUM frame probe 失败和 S94 3RScan Gate0 未通过期间，不运行 S91 正式 pilot，不用合成图、metadata 或旧 S91R-C 描述性相关性替代真实 future RGB-D/pose 验证。
