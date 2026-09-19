# PC-DPM 条件式创新评估 V2

- 评估时间：2026-09-08（Asia/Shanghai）
- 使用框架：`idea-evaluator`（fatal flaw first；Higher/Faster/Stronger/Cheaper/Broader；paradigm-shift；能力与资源匹配）
- 研究类型：`Innovative Technique + Measurement/Benchmark` 混合；当前先做 measurement，方法贡献尚未获授权
- 当前裁决：`ACCEPT_WITH_REVISIONS_PENDING_DECISIVE_VALIDATION`
- 新颖性授权：`NONE`
- 数据边界：只使用已审源码事实、现有baseline状态和一手文献；没有新增模型运行或方法增益

## 1. 第一印象

**论文类型：** 若六级合同揭示跨模型稳定盲点，是 Novel Problem/Setting；只有共享 provenance 机制在强基线上产生 held-out 增量时，才升级为 Novel Method。

**一句话故事：** 现有生成记忆系统常把“存下并检索到历史”当成成功，但同一来源可能在 semantic 与 latent consumer 中失去共同身份；PC-DPM 让所有 appearance consumer 使用同一来源 provenance，并只在独立真实 reference 证明该来源有益时接受它。

## 2. Fatal-flaw audit

| # | Flaw | Severity | 当前证据 | 防线与否决条件 |
|---|---|---|---|---|
| F1 | 最近工作已占据双记忆、多路径条件、reference-order/concept binding、per-reference identity、source-aware attention mask、camera gate、几何attention、3D-FoV检索、global-state retrieval和逐证据utility；如果贡献只是“两个memory path + source ID + gate”，会被判组件拼接 | MAJOR | [Dual-Granularity Memory, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Wang_Dual-Granularity_Memory_for_Efficient_Video_Generation_CVPR_2026_paper.html)、[Movie Weaver, CVPR 2025](https://openaccess.thecvf.com/content/CVPR2025/papers/Liang_Movie_Weaver_Tuning-Free_Multi-Concept_Video_Personalization_with_Anchored_Prompts_CVPR_2025_paper.pdf)、[Video Alchemist, CVPR 2025](https://openaccess.thecvf.com/content/CVPR2025/papers/Chen_Multi-subject_Open-set_Personalization_in_Video_Generation_CVPR_2025_paper.pdf)、[Geometry-as-context, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Hu_Geometry-as-context_Modulating_Explicit_3D_in_Scene-consistent_Video_Generation_to_Geometry_CVPR_2026_paper.html)、[VRAG, NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/e32310c3acb058d563a6a9e54d0e9000-Abstract-Conference.html)、[Saber, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/papers/Zhou_Scaling_Zero-Shot_Reference-to-Video_Generation_CVPR_2026_paper.pdf)、[WorldStereo, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_WorldStereo_Bridging_Camera-Guided_Video_Generation_and_Scene_Reconstruction_via_3D_CVPR_2026_paper.html)、[Spatia, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/papers/Zhao_Spatia_Video_Generation_with_Updatable_Spatial_Memory_CVPR_2026_paper.pdf) | 差别必须同时落在object（单个ordinary-selected source）、mechanism（跨consumer共享source provenance）、granularity（逐source/target几何权重）和setting（可交互生成世界模型）。M1/M2/M3若显示reference-order/source token、camera/source mask、token数、global state或普通geometry attention已解释增益，删除方法主张 |
| F2 | 当前 C1/C2 没有同步、从未进入 memory 的真实目标视角 reference，因而 signed Benefit 可能不可识别 | MAJOR | B0/C1 的返回图不是独立答案；S48 G6 默认关闭 | Influence/Localization 可先作机制诊断；Benefit 必须换到有 sensor timestamp、camera/K/depth、instance identity 和同步多视角 reference 的 CAL 数据。得不到 reference 时降级为 measurement，不训练 accept/reject |

当前没有“用户数据已经反驳核心机制”的 CRITICAL：B0 只有一行且未出现严重事件，C1 尚未盲评分，C2 尚未生成。它们既不支持也不反驳 PC-DPM。

## 3. 生命周期与能力匹配

| 项目 | 判断 | 实际含义 |
|---|---|---|
| 研究生命周期 | Frontier Exploration → Measurement → Innovative Technique | 必须先证明自然失败和跨 consumer 冲突，不能直接训练方法 |
| 当前用户阶段 | MSc 新手，本机自主推进 | 适合严格小 pilot、源码审计和冻结协议；大规模训练需要后续 GPU/合作资源 |
| 本机资源匹配 | 小型 CPU baseline/因果 pilot 勉强可行，完整跨 scene 训练不匹配 | 先用冻结 backbone 和最小 adapter；P0–P3 不通过就不申请额外算力 |
| 预估风险 | 工程高、数据高、计算中高、统计中 | 用 G0–G7 顺序门将昂贵工作放在最后 |

## 4. 五维评分

所有未被真实结果支持的高分均标为 mechanism-based。

| 维度 | 分数 / 10 | 证据与解释 | 必须验证的实验 |
|---|---:|---|---|
| Higher | 7 | mechanism-based：若 consumer 对同一 source 的身份失配确实造成重访错误，共享 provenance 可能提高局部 fidelity；尚无方法结果 | M0–M3 在 held-out scene 的逐 source paired loss，排除参数/token 增量 |
| Faster | 3 | per-source semantic token 与双路 coupling 大概率增加而非减少计算；不应把速度当主卖点 | 报告 latency、VRAM、token 数和参数增量；容量匹配 |
| Stronger | 8 | mechanism-based：同一 source 跨 consumer 的一致约束，有明确机会提高跨视角、跨路径鲁棒性，并可由 F10/F01 反事实识别 | 两 edit family、两 seed、每 sign/target 全过；跨 scene 与第二类 consumer 复现 |
| Cheaper | 4 | 在线轻量 gate 可能便宜，但离线 source-level causal teacher 和同步多视角数据昂贵 | 与普通 gate 比总训练/标注/推理成本；报告 causal-label amortization |
| Broader | 6 | 可推广到 source ID 稳定且 consumer 可枚举的 retrieval generator；对纯隐状态模型不成立 | 至少在 VMem 外的第二类显式 memory consumer 复现 |

最高潜力是 **Stronger、Higher、Broader**。当前只有机制论证，没有实证，不能据分数称“达到顶会水平”。

## 5. Paradigm-shift probe

| 问题 | 当前答案 | 理由 |
|---|---|---|
| 隐藏假设 | Yes | 挑战“retrieved source 已经等价于被正确且有益地消费” |
| 领域里的大象 | Yes | 长时一致性论文常给整体画质/重访指标，却很少逐 source 证明影响、位置和收益 |
| 技术周期 | Partial | 显式 3D memory 与长视频模型让 source-level 审计可做，但方法也快速拥挤 |
| Hamming rule | Yes, conditional | 若能可靠发现并减少 selected-but-harmful memory，评价和方法设计都会改变；若现象不普遍，则影响有限 |

三项条件式 Yes 表明它有颠覆潜力；潜力来自问题定义和可否证证据链，不来自命名。

## 6. 决定性验证顺序

1. **P0：** C1/C2 完成相机守卫和盲评；没有稳定自然失败就停止当前路线。
2. **P1：** S48 V5 通过 fresh review 后，测试 F10/F01 是否出现可重复跨 consumer 冲突；没有就删除 dual-path 根因。
3. **P2：** `edit − matched zero-edit` 的直接效应在每个 sign/target 上超过 replay/negative，并在三类 placebo 下局部化；失败就删除 geometry-provenance 核心。
4. **P3：** 合资格同步真实 reference 给出逐 source signed Benefit；不可识别就只保留 measurement。
5. **P4：** 只有 P0–P3 跨 scene 成立，才执行 M0–M5；M3/M4 必须胜容量匹配 token、geometry attention、context 控制和普通 gate。

## 7. 最终裁决

**Accept with Revisions，等待决定性验证。** 该想法值得继续做最便宜的否证实验，因为它提出了一个具体隐藏假设、一个源码可定位机制和可杀死它的预测；它还不是 Strong Accept，因为 signed Benefit 数据不可用、自然失败尚未完成、核心机制没有模型实证，而且CVPR/NeurIPS近邻已占据“双记忆、参考来源绑定、camera gate、global-state retrieval”叙事。

任何 P0–P3 失败，都应按表中动作降级或停止；不得通过换阈值、挑 scene 或只展示漂亮视频保住 PC-DPM。
