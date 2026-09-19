# 几何记忆研究：七篇核心文献核查与本机交付范围

核查日期：2026-09-05（北京时间）；检索截止时点：22:21:10。本文只核查与本项目直接相关的七篇工作，作为实验设计和报告写作的依据。它不是穷尽性综述，也没有证明候选方法具有新颖性。论文声称的效果与本项目实测结果分别表述。

## 研究问题与核查方法

本轮围绕三个问题展开：已有方法究竟把什么存入记忆；几何纠正、来源关联和可靠性判断哪些已经存在；在没有远程 NVIDIA GPU 的条件下，本项目能交付什么可验证的研究结果。

检索沿三条线进行：视频生成中的历史视图检索，连续三维重建与传统 surfel 融合，以及 RGB-D 数据和评测依据。先搜索标题与作者，再打开作者项目页、原始论文、会议页面或官方代码核对内容。没有使用博客、转载笔记或搜索摘要支持性能结论。部分 CVF 页面直接打开返回 403，改用可访问的作者论文或 arXiv，并保留会议链接用于书目定位。采用本地 `deep-research` 技能的引用核验和反向检查原则，但按本轮七篇的范围串行核查，不将此工作称为系统综述。

所有下述论文的存在、作者和本文引用的核心内容均已核实；没有抄录排行榜数字，没有复现七篇论文，也没有覆盖所有 2026 年世界模型工作。2026 年补充的 I3DM 是本轮找到的一篇直接相关工作，不称为整个领域的最新工作。

## 已核实的论文

### 1. VMem：用粗几何找到历史参考画面

**书目**：Runjia Li, Philip Torr, Andrea Vedaldi, Tomas Jakab. *VMem: Consistent Interactive Video Scene Generation with Surfel-Indexed View Memory*. ICCV 2025；arXiv 首版 2025-06-23，已核查版本 v3（2025-08-14）。[作者提交的论文与版本信息](https://arxiv.org/abs/2506.18903v3)，[会议论文](https://openaccess.thecvf.com/content/ICCV2025/papers/Li_VMem_Consistent_Interactive_Video_Scene_Generation_with_Surfel-Indexed_View_Memory_ICCV_2025_paper.pdf)。

它将过去的图像与观测过相同表面的小面片（surfel）关联，通过目标视角可见的面片检索历史图像，作为后续生成的上下文。这里的三维几何主要用于索引；不应未经实验就假设更精细的地图一定让生成结果更好。论文的写入规则已描述匹配后合并来源索引，固定代码也已有清理与过滤。[固定版本代码](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/modeling/pipeline.py)，详细代码证据见本项目 `docs/BASELINE_AUDIT.md`。

**对本项目的约束**：surfel 记忆、来源帧 ID、confidence 阈值均不能单独称为新增贡献。要研究的是错误是否穿过既有清理，进入索引后是否影响最终选帧，以及纠正后能否恢复有用上下文。只观察到位置误差不能替代后两个问题。

### 2. CUT3R：持续更新的三维感知状态

**书目**：Qianqian Wang, Yifei Zhang, Aleksander Holynski, Alexei A. Efros, Angjoo Kanazawa. *Continuous 3D Perception Model with Persistent State*. CVPR 2025（Oral）；arXiv:2501.12387，首版 2025-01-21。[作者项目与正式书目信息](https://cut3r.github.io/)，[原始论文](https://arxiv.org/abs/2501.12387)。

CUT3R 随输入图像更新内部状态，输出共同坐标系下的点图及相机信息。作者还区分在线处理与看完完整序列后的重访读取；后者拥有额外上下文，不能作为严格在线方法的同条件结果。[作者对状态、在线及重访设置的说明](https://cut3r.github.io/)。

**重叠与区别**：CUT3R 的持续状态服务于几何估计，VMem 的外部 surfel 索引服务于参考图像检索；二者不属于同一个记忆对象。独立 CUT3R 推理可以给本项目补上“真实图像经学习模型得到几何”的证据，但它不等于 VMem 完整生成流程，也不自动包含 VMem fork 后续采用的相同清理、对齐和写入参数。[官方代码](https://github.com/CUT3R/CUT3R)。

### 3. Spann3R：从外部空间记忆预测全局点图

**书目**：Hengyi Wang, Lourdes Agapito. *3D Reconstruction with Spatial Memory*. 3DV 2025，pp. 78–89；其 arXiv 预印本是 2024 年，首版 2024-08-28。**不能把它写成 ECCV 2024。**[作者项目的会议 BibTeX](https://hengyiwang.github.io/projects/spanner)，[2024 年预印本](https://arxiv.org/abs/2408.16061)。

Spann3R 维护外部空间记忆，将过去的三维信息用于下一张图像的全局点图预测，避免逐图对坐标系再进行优化式全局对齐。与 CUT3R 一样，它直接针对重建；与 VMem 不同，它的主要输出不是用于视频生成的历史帧列表。[论文摘要](https://arxiv.org/abs/2408.16061)，[作者方法说明及代码入口](https://hengyiwang.github.io/projects/spanner)。

**对本项目的约束**：不能把“加入长期三维记忆”本身当成研究空白；需要明确讨论的是估计器状态、外部几何索引，还是生成器的上下文。若未来替换估计器，要把它与写入策略的变化分开做对照。

### 4. ElasticFusion：传统 RGB-D 系统早已持续融合与修正 surfel

**书目**：Thomas Whelan, Stefan Leutenegger, Renato F. Salas-Moreno, Ben Glocker, Andrew J. Davison. *ElasticFusion: Dense SLAM Without A Pose Graph*. Robotics: Science and Systems（RSS）2015；DOI:10.15607/RSS.2015.XI.001。[会议官方记录](https://www.roboticsproceedings.org/rss11/p01.html)，[作者提供的论文](https://thomaswhelan.ie/Whelan15rss.pdf)。这里指 2015 年 RSS 论文，未混用后续期刊扩展版的题名和作者顺序。

该系统从 RGB-D 观测持续构建 surfel 地图，结合帧到模型跟踪、窗口化融合与非刚性表面修正处理地图一致性。它说明三维表面元素的在线融合和纠正并非新问题。[会议官方摘要](https://www.roboticsproceedings.org/rss11/p01.html)。

**重叠与区别**：ElasticFusion 追求测得场景的几何和定位一致性；本项目目前研究供生成器使用的粗几何索引。不能从几何重建收益直接推出视频生成收益。简单 surfel 均值更新适合作为基础对照，不能包装成新的融合原理；本项目的简单实现也不能称为完整复现 ElasticFusion。

### 5. Probabilistic Surfel Fusion：不确定性感知融合已有明确先例

**书目**：Chanoh Park, Soohwan Kim, Peyman Moghadam, Clinton Fookes, Sridha Sridharan. *Probabilistic Surfel Fusion for Dense LiDAR Mapping*. ICCV Workshops 2017，Multiview Relationships in 3D Data；arXiv:1709.01265。应写 **Workshops**，不能写作 ICCV 主会论文。[作者提交版本与 workshop 信息](https://arxiv.org/abs/1709.01265)，[CVF 会议条目](https://openaccess.thecvf.com/content_ICCV_2017_workshops/w35/html/Park_Probabilistic_Surfel_Fusion_ICCV_2017_paper.html)。

该工作在多视角 LiDAR 地图中考虑测量不确定性进行 surfel 关联，并以贝叶斯过滤进行融合。传感器噪声和空间分辨率是其关联模型的重要条件。[原始论文](https://arxiv.org/abs/1709.01265)。

**对本项目的约束**：用 confidence、uncertainty 或 Bayesian fusion 命名，不会自动产生新颖性。深度传感器噪声、神经几何估计误差和生成内容错误也并非同一种误差来源。若将传统融合移入 VMem，需要证明接口选择与额外收益，并与简单更新、公平写入预算和原版清理比较。

### 6. TUM RGB-D：用于真实测量回放，不提供无噪表面真值

**书目**：Jürgen Sturm, Nikolas Engelhard, Felix Endres, Wolfram Burgard, Daniel Cremers. *A Benchmark for the Evaluation of RGB-D SLAM Systems*. IEEE/RSJ International Conference on Intelligent Robots and Systems（IROS）2012。[TUM 官方书目](https://cvg.cit.tum.de/research/vslam?key=sturm12iros)，[第一作者提供的原文](https://jsturm.de/publications/data/sturm12iros.pdf)。

数据包含 Kinect 彩色图像与深度测量，以及由运动捕捉系统取得的相机轨迹。TUM 的 ground-truth 轨迹可以检验位姿；深度图仍是传感器测量。官方当前页面注明数据默认 CC BY 4.0、随附代码 BSD-2-Clause，除非另有标注，并要求引用论文。[数据内容、引用及许可](https://cvg.cit.tum.de/data/datasets/rgbd-dataset)。

**对本项目的约束**：由这些深度图回投出的点云应称“测量参考”，不能称为无噪几何真值；其缺测、同步与遮挡需分别报告。测量回放能验证记忆接口和观测一致性，不能单独说明 CUT3R 的自然错误率。评估几何变化时不应在测试数据上重新调阈值，也不能把被过滤掉的困难像素从分母悄悄删除。

### 7. I3DM：2026 年直接相关的隐式三维记忆路线

**书目**：Jia Li, Han Yan, Yihang Chen, Siqi Li, Xibin Song, Yifu Wang, Jianfei Cai, Tien-Tsin Wong, Pan Ji. *I3DM: Implicit 3D-aware Memory Retrieval and Injection for Consistent Video Scene Generation*. arXiv:2603.23413，2026；首版 2026-03-24，核查版本 v2（2026-07-31）。作者页面标注 Arxiv 2026；本轮没有核实到正式会议录用信息。[版本与作者](https://arxiv.org/abs/2603.23413v2)，[作者项目](https://riga2.github.io/i3dm/)。

它用预训练前馈新视角合成模型的中间特征衡量历史视图相关性，并将对齐后的可靠区域用于生成条件。与 VMem 的显式 surfel 索引相比，它选择绕开显式三维重建；两条路线都关注重访时的参考信息。[作者对检索与注入机制的说明](https://riga2.github.io/i3dm/)。

**对本项目的约束**：可靠区域、几何误差累积和三维感知检索已经是直接相关工作讨论的问题。I3DM 的存在使“首次考虑记忆可靠性”不可接受；但作者对显式几何缺点的概括也不能替代本项目对 VMem 的逐实例证据。这里没有复核其全部实验表格，因此不转述具体优势数字或宣称它已解决所有遮挡问题。

## 七篇工作放在同一条研究链里

| 层次 | 对应工作 | 主要维护或提供什么 | 本项目应区分的评测问题 |
|---|---|---|---|
| 观测与参考 | TUM RGB-D | 彩色、深度测量与轨迹参考 | 时间、坐标、缺测和测量噪声是否处理正确 |
| 从图像估计几何 | CUT3R、Spann3R | 内部状态或外部空间特征记忆 | 在相同观测条件下，几何估计误差是什么 |
| 几何地图融合 | ElasticFusion、Probabilistic Surfel Fusion | 可融合与修正的表面模型 | 新观测是否改善几何，代价和条件是什么 |
| 为生成选择/注入记忆 | VMem、I3DM | 显式几何索引或隐式三维相关性 | 最终取出的参考信息是否更有用，生成是否改善 |

这不是简单的性能排名。CUT3R 和 Spann3R 改善的是上游几何输出；ElasticFusion 和概率 surfel 融合说明可更新地图有成熟先例；VMem 与 I3DM 则把三维信息用于生成上下文。在这条链上，几何更准确、选帧发生变化、检索更好、视频更一致是四个不同命题，不能互相替代。

## 对本机课程项目的范围建议

建议当前交付主题为：**《用于世界模型的几何视图记忆：可复现诊断与轻量更新对照》**。这是针对现有资源的研究范围建议，不意味着已替用户变更提交的 proposal 或已获得导师认可。

可以在本机形成完整、可审核的这一范围内的成果：固定上游代码与数据出处；保留合成实验及负结果；运行真实 RGB-D 测量回放；实现一个清楚定义的轻量更新原型；用相同输入、相同上下文数量和明确预算做对照；把逐实例日志、图片、结果表、复现入口和报告一起交付。若实测显示简单更新无收益，报告应保留它，并解释收益为什么没有传到选帧。负结果也可以构成严谨的课程分析，是否满足原评分约定仍须对照原 proposal。

在设计上，首先固定开发集规则，再锁定测试片段或场景。至少区分不更新位置、简单累计均值、一个合理稳健更新方案；如做拒绝策略，需要匹配写入数量的对照。统计几何残留、地图大小、接受率、最终参考帧以及独立定义的可见覆盖，不通过删掉困难区域换取表面改善。若只跑同一序列的不同时间片，应明确它是序列内验证，不能写成跨场景泛化。

完整 VMem 视频推理、经过相同上游清理的生成闭环、重访视频质量及大范围泛化需要另外的实测证据。截止本轮核查，不能将本机几何/检索原型称为完成了这些实验。真实导师会议、用户实际学习投入和最终提交也不能由程序运行记录替代。

## CUT3R 小规模 CPU/MPS 推理可行性补充

给定本机 M3 Max、64 GB，项目当前 Torch 可用 MPS、不可用 CUDA，**小规模 CUT3R 推理值得实际尝试，但目前这里只完成代码层面的可行性审查**。MPS 是 Apple GPU 后端，设备检查通过不保证整条应用的每个算子和依赖均兼容。[与本地 Torch 版本对应的 PyTorch 2.7 MPS 文档](https://docs.pytorch.org/docs/2.7/notes/mps.html)。

官方 CUT3R 提供 224 linear 中间检查点和 512 DPT 最终检查点。224 模型适合先验证接口，不能冒充论文最终模型。官方还说明其默认编码器批量处理会随帧数增加而增长内存；不要由持久状态的概念推断整个演示程序内存恒定。[官方模型与推理说明](https://github.com/CUT3R/CUT3R#download-checkpoints)。

发现了一个会直接影响本机启动的差异：VMem 固定提交内 `extern/CUT3R/src/croco/models/pos_embed.py` 把纯 PyTorch `RoPE2D` 类整段注释掉。CUDA 扩展不可导入时，它会打印 fallback 提示，却没有定义对应类；独立 CUT3R 官方版本有可执行的 fallback。[VMem 内的固定文件](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/extern/CUT3R/src/croco/models/pos_embed.py)，[独立官方文件](https://github.com/CUT3R/CUT3R/blob/main/src/croco/models/pos_embed.py)。因此，不能把该 fork 的启动失败直接当成 CUT3R 全部版本都无法在本机运行的证明。

建议先固定独立 CUT3R 源码版本，保留许可与哈希，以 2–4 张真实图像、224 模型、FP32、关闭梯度、CPU 完成最小推理；确认输出为有限值并保存点图、位姿、置信度和耗时。随后在相同输入尝试 MPS，与 CPU 比较数值和结果，再扩大到 8–16 帧。分辨率和帧数是逐级增加的实验参数，不能事先保证速度和峰值内存。纯推理优先减少不使用的训练/可视化依赖，遇到不支持的运算要记录具体失败及任何代码改动。关闭的 CUDA autocast 上下文和实际调用 CUDA 算子是两回事，应以执行测试决定兼容性。

独立 CUT3R 结果若成功，只能记为“真实图像的学习式三维估计已跑通”。后续还要单独对齐 VMem fork 的预处理、清理、几何尺度、来源编号与阈值。VMem 的视频生成权重仍有其访问要求及 CUDA 路径；拥有或成功运行 CUT3R 权重不会自动解除这些条件。本轮文献工作没有下载任何模型权重。

## 本轮问题的回答

1. **已有方法记住了什么？** 已分别存在重建状态、外部空间特征、可更新表面模型以及供生成器使用的历史视图。项目必须说明它修改的是哪一层。
2. **哪些机制已经存在？** 三维记忆、来源关联、几何融合、不确定性和可靠区域处理均有先例。简单均值、稳健更新和门控应先作为对照或候选实现；这七篇核查不能证明新方法成立。
3. **本机能诚实交付什么？** 能推进有原型、有真实测量、有对照、有复现包的几何/检索研究，并尝试小规模学习式几何估计。视频生成质量与完整闭环需要单独完成实际运行和验证；报告应清楚标出它们的状态。
