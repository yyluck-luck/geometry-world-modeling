# SOCF / FGB-Future：顶会近邻差异矩阵与 SuperPod 最小证伪实验

审查日期：2026-09-15（Asia/Shanghai）  
审查身份：独立创新审查子任务。本文不是新颖性证明，也不是 GPU 结果。  
状态：`new_method_validated=false`，`novelty_authorization=NONE`。

## 1. 当前证据决定的创新边界

原 proposal 的核心是长时程动态 3D/4D 世界建模中的几何一致性。S99 停止了“低历史
几何不一致度平均优于 confidence”的简单解释；S100 的收益均值接近零并且出现少量
背景反号；S103 显示 low/conf 的输出差异极稀疏，主要集中在少量 provenance 变化
像素，支持变化比例很低。由此，下面两条主张已经不能使用：

1. “加一个 geometry-aware memory 就是新方法”；
2. “把几何风险、utility、context interaction 和 top-k 组合起来就自动新颖”。

可继续检验的窄问题只有：历史-only 的风险/遮挡竞争证据，是否能在固定真实 memory
预算下预测**未见未来** RGB-D/pose 误差，并让完整 consumer 优于公平基线。若答案是否定，
应保留负结果，不能通过换名字、换截断或增加模块恢复方法主张。

## 2. 最近顶会和原始论文的差异矩阵

以下“已覆盖”只表示原文已经公开了相应机制或评价维度，不表示我们复现了它们；
“尚未覆盖”只表示本次定向审查没有看到完整联合命题，不是对全领域不存在的证明。

| 工作（年份/状态） | 选择或记忆单位与机制 | 目标/评价 | 与 SOCF / FGB-Future 的重叠 | 仍可主张的差异（必须实验证明） | 主要拒稿风险 |
|---|---|---|---|---|---|
| **GIM-World**，2026 预印本 | 帧+相机 pose；GP/MI 条件 pruning；固定 memory token；几何 head | memory quality、相对位姿和几何一致性 | 已覆盖固定容量、几何记忆、集合条件选择 | 观测级风险是否经 calibration 预测独立 future RGB-D/pose loss；source-level replace/delete；同 token/显存/forward 的完整 consumer 成本 | 只是把 MI/GP 换名为 geometry risk；future 泄漏；未超过其几何 memory baseline |
| **Video World Models with Long-term Spatial Memory**，2025 预印本 | 显式几何长期空间记忆、存储/检索、回访 | 长时视频质量和空间一致性 | 已覆盖长期空间 memory 和回访任务 | 将“历史条目风险 → 未见未来状态收益”作为独立评价合同，而不是再做一套 memory 模块 | 被判为已有空间记忆的增量组合 |
| **Spatia**，CVPR 2026 | 可更新 3D point-cloud memory、MapAnything 更新、参考帧与 camera path 条件 | 迭代视频、回访和 RGB/空间一致性 | 已覆盖 updatable spatial memory、完整生成闭环 | 选择器只读历史、固定真实 slot/算力；source intervention 对未来 RGB-D/pose 的 paired effect | 只在 renderer/reconstruction 上改善，完整生成无一致方向 |
| **Geometry-as-context**，CVPR 2026 | 显式 3D 场景作为生成 context，迭代估计/渲染/恢复 | scene-consistent video generation | 已覆盖几何 context 和生成一致性 | 不依赖未来答案的观测级风险校准，且在相同生成 consumer 内比较 selector | 将 context 注入误写成未来风险选择贡献 |
| **WorldStereo**，CVPR 2026 | global-geometric 与 spatial-stereo 3D memory，3D 对应约束注意力 | camera-guided video + 3D reconstruction | 已覆盖几何 memory 和多视角一致性 | 以 future-state loss 和来源级干预定义 memory item 的增量价值 | 被认为是现有 3D memory/attention 的重新组合 |
| **ViewRope**，2026 预印本/ICLR WM workshop | camera-ray geometry RoPE；geometry-aware frame-sparse attention | 长时回访、loop closure 和稀疏注意力效率 | 已直接覆盖“几何重要历史帧选择” | SOCF 只能主张 source-conflict 风险预测与 abstention，不能主张“几何选帧”本身 | selector 与 ViewRope 的 relevance/稀疏注意力等价 |
| **WorldMM**，CVPR 2026 | episodic/semantic/visual 多模态、多时间尺度 memory；自适应迭代 retrieval | 长视频问答准确率和 latency | 覆盖自适应 retrieval、动态 memory budget | 未来几何真值、RGB-D/pose、source provenance 和 world-model consumer 的固定成本评价 | 跨任务迁移不成立；只证明 QA utility |
| **SplaTAM** 官方实现（代码强基线） | overlap/visibility keyframe 选择、深度/光度 tracking loss、Gaussian map 更新 | SLAM/重建精度与效率 | overlap/visibility gate 是 SOCF 的直接替代解释 | 在同候选池、同 source-block/slot、同 forward 成本下比较 future loss；不能把 S100 当作 SplaTAM 复现 | budget 单位不一致，或把 overlap 先验误称新颖性 |
| **CUE-R**，2026 预印本 | REMOVE/REPLACE/DUPLICATE 的有符号证据干预及联合删除 | RAG 回答/grounding/置信变化 | 已覆盖有符号替换和多证据交互的实验思想 | 几何来源、遮挡 consumer、独立 RGB-D/pose 未来目标与固定真实 budget | “反事实”只是普通消融；未控制随机性和上下文长度 |
| **Utility-Oriented Visual Evidence Selection**，2026 预印本 | 单候选 utility 代理、KL/helpfulness 分数、top-k | 多模态问答 utility | 已覆盖 utility-based selection | 不是单项 KL，而是历史-only 风险对未来几何状态损失的可校准预测 | utility 代理与真实未来损失不一致，或 top-k 没有集合条件 |

**矩阵结论：** “geometry + memory + fixed budget”“context-dependent selection”与“有符号
干预”均有直接或部分近邻。SOCF 只有在 source-conflict 风险能跨轨迹预测未来损失、
并在真实完整 consumer 中用 abstention 带来稳定收益时才有方法候选资格；FGB-Future
更适合先作为新评价问题/benchmark，因为它不依赖一个尚未验证的 selector。

## 3. SuperPod 最小证伪实验（拿到服务器后执行）

### 3.1 固定输入和预算

运行前建立机器可读 `GPU_RUN_MANIFEST.json`，填写实际 SuperPod 节点/GPU、CUDA、容器、
git commit、数据许可和权重 SHA；未知字段不能猜。使用一个完全合法的
`HELD_OUT_TEST` 数据集，至少 5 条此前未用于方法选择的轨迹，每条至少 3 个未来 query。
另设独立 `CALIBRATION_ONLY` 轨迹，不能让 test future RGB/depth/pose 进入 selector 或
阈值。

固定主预算 `k=4`，敏感性 `k=2,8`；预算同时记录：memory slots、输入 token/字节、GPU
显存峰值、选择时间、forward 次数、生成步数和 wall time。所有方法共享候选池、相机轨迹、
随机种子、生成器和输出分辨率。`source-block` 数量不能冒充 `k`，oracle 只作上界。

### 3.2 三个最小作业

**Job 0 — FGB-Baseline（完整 consumer 基线）**

- 方法：recent/sliding、uniform、random（预先冻结多个 seed）、pose-distance、
  coverage/visibility、depth-only、confidence、GIM-World 风格 MI/GP；SOCF 暂不参与
  校准。
- 每条 test 轨迹运行 3 个未来 query；先封存预测，再读取 future GT 评分。
- 主要读数：future RGB-D AbsRel、Delta1、pose/reprojection error、worst-5%/CVaR、
  coverage、source overwrite rate、显存和时延。
- 证伪用途：若所有基线在统一 consumer/预算下都无法稳定区分，先停止开发方法，检查
  proposal 的评价目标是否可测。

**Job 1 — SOCF-Calibrate（历史-only 冲突风险预测）**

- 在 calibration 轨迹计算候选的投影重叠、深度 margin、可见性边界和 provenance 竞争
  特征，拟合风险区间/概率；不读 calibration future 的答案以外的 test 信息。
- 在 test 上只输出预测 conflict 概率与 abstain/update 决策；不允许用 future mask、
  future depth 或 future RGB 选候选。
- 先做不接生成器的预测检验：source overwrite 的 AUROC/AUPRC、名义覆盖率与实际覆盖率。
- 若风险预测通过，再在同一 consumer 中接入 `k=2/4/8`，与 Job 0 的 confidence、
  overlap/visibility、MI/GP 逐项比较。

**Job 2 — Source-Intervention Replay（源级最小反事实）**

- 对每条轨迹预先抽取有限数量候选，固定 query、seed、其它记忆、生成步数和预算；只
  delete/replace 一个历史 item。
- 在 prediction seal 后读取 future GT；保存 source provenance 改变的像素、预测 conflict
  区域和 paired future loss 差。
- 该作业只检验 SOCF 的机制链，不用来事后挑选正例或扩展 selector。

### 3.3 预注册成功和停止条件

SOCF 至少要同时满足以下条件才允许进入下一轮完整视频实验：

1. test 上 conflict 风险的 AUROC 高于 strongest non-SOCF baseline 至少 0.05，且在名义
   0.9/0.8 覆盖率下实际覆盖率均在 ±0.05 内；否则停止“风险可预测”主张。
2. `k=4` 主预算下，SOCF 相对最强基线的 paired future mean AbsRel 改善达到至少 1%
   相对值，且按轨迹 bootstrap 的 95% 区间不跨 0；若 mean 无改善但 tail/CVaR 也无改善，
   停止方法主张。`k=2,8` 仅作预注册敏感性，不择优汇报。
3. coverage、source overwrite、reprojection 和完整 RGB/深度输出方向不能互相矛盾；若
   只有 coverage 改善而 future depth/pose 变差，判为失败。
4. Source-intervention replay 中，预测 conflict 区域与实际 provenance 改变有预先固定
   的空间重叠阈值（建议 IoU≥0.5；若数据分辨率不适用，运行前写明替代阈值），且 paired
   loss 方向在至少 2/3 轨迹上同向；否则停止“机制解释”。
5. 去掉 calibration、conflict 或 abstention 任一模块后应出现可解释的退化；若 simple
   overlap/visibility gate 达到相同结果，SOCF 降级为已知基线。

FGB-Future 作为 benchmark 只有在所有输入身份、许可、未来隔离、预算核算和独立复核
通过后才可报告。若没有任何 selector 超过 recent/random，benchmark 仍可作为负结果/评价
审计，但不能声称证明 GRC 有效。

## 4. 审稿式差异评分

| 候选 | 新颖性潜力 | 科学价值 | 可证伪性 | SuperPod 成本 | 近邻风险 | 当前 verdict |
|---|---:|---:|---:|---:|---:|---|
| SOCF（方法候选） | 7.0/10 | 8.0/10 | 8.5/10 | 5.5/10 | 7.0/10（高） | 先做 Job 1/2；预测或 replay 失败即停止 |
| FGB-Future（新评价问题） | 7.5/10 | 8.5/10 | 9.0/10 | 6.0/10 | 6.5/10（中高） | 先冻结数据/预算/runner，再决定 companion method |

这些是“如果完整证据成功”的潜力分，不是当前成果分。当前证据分为：proposal 问题
和失败诊断较扎实；独立方法贡献尚未验证；`new_method_validated=false`。

## 5. 给导师/后续 agent 的一句话

目前最值得投入 GPU 的不是继续堆一个 GRC 模块，而是用统一固定预算回答：**历史-only
几何风险能否预测未见未来 RGB-D/pose 的 source-conflict 与误差，并在完整 world-model
consumer 中超过 confidence、overlap、pose、MI/GP 和 recent 等基线？** 这条链任一点失败，
就应停止方法化叙事，把结果保留为严格的负诊断或评价协议。

## 6. 本轮原始来源（用于差异核验）

- [GIM-World, arXiv:2606.02436](https://arxiv.org/abs/2606.02436)
- [Video World Models with Long-term Spatial Memory, arXiv:2506.05284](https://arxiv.org/abs/2506.05284)
- [Spatia, CVPR 2026 Open Access](https://openaccess.thecvf.com/content/CVPR2026/papers/Zhao_Spatia_Video_Generation_with_Updatable_Spatial_Memory_CVPR_2026_paper.pdf)
- [Geometry-as-context, CVPR 2026 Open Access](https://openaccess.thecvf.com/content/CVPR2026/html/Hu_Geometry-as-context_Modulating_Explicit_3D_in_Scene-consistent_Video_Generation_to_Geometry_Context_CVPR_2026_paper.html)
- [WorldStereo, CVPR 2026 Open Access](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_WorldStereo_Bridging_Camera-Guided_Video_Generation_and_Scene_Reconstruction_via_3D_CVPR_2026_paper.html)
- [WorldMM, CVPR 2026 Open Access](https://openaccess.thecvf.com/content/CVPR2026/html/Yeo_WorldMM_Dynamic_Multimodal_Memory_Agent_for_Long_Video_Reasoning_CVPR_2026_paper.html)
- [ViewRope, arXiv:2602.07854](https://arxiv.org/abs/2602.07854)
- [CUE-R, arXiv:2604.05467](https://arxiv.org/abs/2604.05467)
- [Utility-Oriented Visual Evidence Selection, arXiv:2605.13277](https://arxiv.org/abs/2605.13277)
- [SplaTAM official repository](https://github.com/google-research/SplaTAM)

本轮通过 CVF/Open Access 与 arXiv 原始页面定位和核对机制描述；没有运行这些论文的模型，
也没有把网页摘要或搜索片段当作性能证据。检索事实仍需在正式论文稿件中逐条回到原文段落
和固定版本代码复核。
