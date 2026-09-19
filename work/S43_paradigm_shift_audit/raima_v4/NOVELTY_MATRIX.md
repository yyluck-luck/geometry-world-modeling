# RAIMA V4 新颖性与强基线矩阵

- 状态：`SOURCE_ONLY_LITERATURE_BOUNDARY`
- 方法状态：`NO_METHOD_SELECTED`
- 新颖性授权：`NONE`
- 模型运行：`0`
- 文献规则：正式会议页面优先；arXiv 明确标为预印本；未检索到相同交集不证明首创

## 1. 结论

下列近邻已经覆盖 3D memory、可更新 memory、回环评价、retrieval 与 influence 错位、reference 视频评价、逐证据干预、counterfactual arbitration 和 generic attribution。RAIMA 当前只能保留为一个窄的 measurement specialization：

> `ordinary-selected stable runtime source × enumerated appearance consumer × pre-outcome 3D support × in-distribution matched intervention × never-conditioned real reference`

这五项的交集不是靠拼接就成为创新。只有真实确认数据显示一个稳定、重要、跨 scene 和至少两个 host 的现象，并且强基线无法解释或修复，才允许重新审查 novelty。当前没有方法，也没有方法增益。

## 2. 逐项碰撞

| 近邻 | 状态与一手来源 | 已占据内容 | RAIMA 禁止表述 | 必须保留的强对照或差异 |
|---|---|---|---|---|
| WorldTrace / LoopBench | 2026 预印本，<https://arxiv.org/abs/2608.07408> | KV storage 与 addressability 分层、virtual position、长 detour 后 episodic recall、training-free cache 修复 | 首次分离 storage/addressability；首次视频 memory 回环 benchmark | 直接视频基线；RAIMA 只能增加 ordinary-selected single-source 与 reference 后果 |
| ReWorld | 2026 预印本，<https://arxiv.org/abs/2608.23565> | fixed-budget KV、pose-indexed landmarks、palindrome return、分钟级 out-and-back recall | pose retrieval、固定 budget、palindrome route 是新意 | 用相同 return 任务比较；整体回环分数不能替代 source responsibility |
| MBench | 2026 预印本，<https://arxiv.org/abs/2606.00793> | entity/environment/causal consistency 和 12 子维度的真实长视频 memory benchmark | 首个 world-model memory benchmark 或层级 taxonomy | 证明 runtime source intervention 对 MBench 类整体指标有增量诊断价值 |
| E3C | 2026 预印本，<https://arxiv.org/abs/2605.26316> | point-cloud 3D memory、per-point appearance、view-aligned conditioning 和 scene editing | 首次编辑 3D memory 并观察视频变化 | matched zero、负控、双 support、never-conditioned reference 必须提供额外证据 |
| What-If World | 2026 预印本，<https://arxiv.org/abs/2605.27589> | 单物理变量成对 prompt/video，揭示单视频评价盲点 | 首次 paired intervention world-model evaluation | 区别必须来自内部 source、consumer、3D support 与 reference utility |
| Scalable Influence and Fact Tracing | ICLR 2025，<https://proceedings.iclr.cc/paper_files/paper/2025/hash/65798a76cc176c29b6bfefe84b0a03ff-Abstract-Conference.html> | retrieval 找相关事实与 influence 找改变预测的样本可错位 | 首次发现 retrieval 不等于 causal influence | RAIMA 要证明视频 runtime/3D/reference 联合现象，而不是重复 gap 叙事 |
| ARC-JSD | ICLR 2026，<https://proceedings.iclr.cc/paper_files/paper/2026/hash/ed67dff7cb96e7e86c4d91c0d5db49bb-Abstract-Conference.html> | 无微调/梯度/替代模型的 context attribution，并定位 attention heads/MLP | generic context attribution 或 layer localization 是方法创新 | hidden-state probe 只能作 output intervention 的辅助诊断 |
| The Attribution Blind Spot | 2026 预印本，<https://arxiv.org/abs/2605.26778> | output consistency 不能认证 context-governed generation；内部信号也不认证单条来源 | 输出不变证明没用 memory；内部 divergence 证明用了特定 source | 保留 V3 的 Observable Influence 降级措辞 |
| Outputs of generative diffusion models are often unattributable | Nature Communications 2026，<https://www.nature.com/articles/s41467-026-75667-5> | 以训练单元 omission/ablatable ensemble 定义 Counterfactual Radius；训练规模扩大时冗余可让单个来源难以归因，并显示相似度不能替代 counterfactual attribution | 单来源低影响、相似度不等于因果、counterfactual omission attribution 本身新 | 该工作不审 runtime memory 或视频 consumer；RAIMA 幸存边界仅是 ordinary-selected runtime source、枚举 consumer、3D localization 与 never-conditioned reference signed utility 的联合测量 |
| CUE-R | 2026 预印本，<https://arxiv.org/abs/2604.05467> | per-evidence REMOVE/REPLACE/DUPLICATE、operational utility、trace divergence、非加性交互 | 逐 item 干预、operation utility 或 source interaction 本身新 | 视频连续输出、稳定 source identity 与 3D/reference 合同需显示额外价值 |
| TetherMem | 2026 预印本，<https://arxiv.org/abs/2608.26902> | frozen video generator 的 query/region/age memory routing；普通一致性/运动指标会漏掉 under-progression | 普通视频指标漏记忆伤害；普通 query/region/age gate 新 | 任一 future router 必须胜过 TetherMem 式 routing |
| CF-RAG | ICLR 2026，<https://proceedings.iclr.cc/paper_files/paper/2026/hash/1c078897dc08d46091d0d361d9955c6b-Abstract-Conference.html> | counterfactual query 与 parallel evidence arbitration | generic counterfactual evidence arbitration 新 | future set arbitration 必须有视频特有机制和更简单 gate 对照 |
| CoRM-RAG | 2026 预印本/相关 SIGIR DOI，<https://arxiv.org/abs/2605.01302> | relevance-robustness gap、counterfactual risk、Evidence Critic、risk abstention | relevance 不是 utility 或轻量 critic 新 | future critic 必须证明相对于 score/age/pose/reliability gate 的增量 |
| Ref4D-VideoBench | CVPR 2026，<https://openaccess.thecvf.com/content/CVPR2026/html/Wei_Ref4D-VideoBench_Four-Dimensional_Reference-Based_Evaluation_of_Text-to-Video_Generative_Models_CVPR_2026_paper.html> | 600 reference videos、12 metrics、四维 fine-grained 视频评价 | reference-based video evaluation 新 | 证明 source intervention 提供 reference benchmark 不含的责任证据 |
| Hi3DEval | NeurIPS 2025 Datasets & Benchmarks，<https://proceedings.neurips.cc/paper_files/paper/2025/hash/42ffaddcc6edc9fb05ff9f9b49fca700-Abstract-Datasets_and_Benchmarks_Track.html> | object/part/material 的 hierarchical 3D evaluation 与 hybrid 3D/video representation | hierarchical 或 geometry-aware evaluation 新 | source-conditioned intervention 与 reference consequence 必须有增量构念效度 |
| Spatia | CVPR 2026，<https://openaccess.thecvf.com/content/CVPR2026/papers/Zhao_Spatia_Video_Generation_with_Updatable_Spatial_Memory_CVPR_2026_paper.pdf> | 持续更新 3D point-cloud memory、SLAM update、2D projection conditioning、camera control | updatable 3D spatial memory、dynamic/static separation 或显式相机控制新 | Spatia 及其多条件路径是强基线；RAIMA 只审具体 source 的作用与后果 |
| Plenoptic Video Generation / PlenopticDreamer | CVPR 2026，<https://openaccess.thecvf.com/content/CVPR2026/papers/Fu_Plenoptic_Video_Generation_CVPR_2026_paper.pdf> | 多历史视频时空 memory、3D FoV retrieval、random retrieval 与 context 数量消融 | random context control、context-count ablation 或 3D FoV retrieval 新 | 其整体消融不能替代 single-source/consumer/support/reference 联合审计，但必须作对照 |
| GIM-World | 2026 预印本，<https://arxiv.org/abs/2606.02436> | fixed-size implicit memory、camera-queryable geometry head、3D teacher、information pruning | geometry-aware implicit memory、camera-queryable geometry 或 pruning 新 | RAIMA 限定显式稳定 source；不能把 geometry-aware memory 当方法贡献 |
| Compression and Retrieval / CaR | 2026 预印本，<https://arxiv.org/abs/2606.23105> | viewpoint positional encoding、attention retrieval、轻量 context compression | learned viewpoint retrieval 或 compressed retrieval 新 | future method 必须比较这些简单 retrieval/compression baselines |
| Addressing divergent representations from causal interventions | ICLR 2026，<https://proceedings.iclr.cc/paper_files/paper/2026/hash/133e588e1429f9f1e25b215da145580e-Abstract-Conference.html> | 常见内部干预可能产生 OOD representation，甚至激活 dormant behavior | 任意 source drop/scramble 的输出差都是真实 source effect | primary 只接受 in-distribution matched replacement/edit，加 distribution-shift 和 intervention-validity gate |
| Causality in Video Diffusers is Separable from Denoising | CVPR 2026，<https://openaccess.thecvf.com/content/CVPR2026/html/Bai_Causality_in_Video_Diffusers_is_Separable_from_Denoising_CVPR_2026_paper.html> | 先做层/步机制 probe，再按可重复规律分离时序推理与逐帧渲染 | “先 probe 后设计”本身是创新 | 仅学习研究顺序：真实定位瓶颈后再设计方法 |

## 3. OOD 干预的硬边界

ICLR 2026 的 divergent-representation 工作不直接证明 VMem 的 source edit 一定 OOD，但它给出一个必须防守的替代解释：删除、置零或乱序 source 可能激活模型自然运行不会访问的路径。

因此 RAIMA V4 规定：

1. primary treatment 必须是结果前注册的 in-distribution、source-coherent matched edit 或 matched replacement；
2. dose zero 经过相同 decode、edit API、clip、round、encode、consumer 和 generation 路径；
3. source 数量、shape、layout、顺序、position、RNG 和非目标初态完全一致；
4. intervention-validity 与 distribution-shift receipt 未通过时，该 cell 不是阴性或阳性，而是 `TECHNICAL_MISSING`，并阻断 scene；
5. drop、delete、unmatched zero 与 scramble 只作 stress tests，不能进入 AOIG、SEM、RCSU 或 primary union；
6. 若未来 S48 V7 无法构造自然分布匹配的干预，停止 primary causal interpretation。

## 4. 只有什么结果才值得重启方法研究

必须同时满足：

- 20-scene V4 composite gate 通过；
- AOIG/SEM/RCSU 中至少一个预注册 endpoint 跨 scene 稳定，且 practical floor 超过 replay/reference uncertainty；
- ordinary retrieval/return metrics、WorldTrace/LoopBench、TetherMem、Spatia、PlenopticDreamer、GIM-World/CaR、简单 pose/age/reliability gate 与统一 attention 不能解释或修复；
- 第二个 stable-source host 用同一 contract 复现；
- 测量相对 Ref4D/Hi3DEval/MBench 类指标有 held-out 增量诊断价值；
- 方法只针对仍存活的具体失败，并做容量、信息和计算匹配的公平消融。

在这些条件前，RAIMA 是待验证 measurement candidate。不得给 routing、critic、refresh、cache、shared provenance 或 arbitration 方法命名。

## 5. 检索边界

本矩阵绑定 V3 两份实时碰撞补充：SHA256 `91c300c4365dbae1ea0715d159b1248c88cf159e2949e7aa13267a9e0ec77550` 与 `7885ff52ba98ad3db3aa7430de714acb8da9da1d03bc33bcfbb1224246efafdd`。它们及本矩阵可以否决宽泛主张，不能证明剩余交集首创。正式投稿前仍需按最终方法和 benchmark 重新做系统检索及独立引用核验。
