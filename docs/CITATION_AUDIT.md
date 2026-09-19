# 七篇文献独立核验

核验时点：2026-09-05 22:37:54（北京时间，UTC+8）。核验输入仅为 `docs/LITERATURE_VERIFIED.md`；没有读取其引用的本地审计报告、实验结果或研究日志，也没有据其“已核实”声明直接下结论。采用完整标题检索并打开一手来源；对 I3DM 额外进行了作者＋关键词＋年份、核心关键词＋会议检索。以下状态仅覆盖书目身份和方法描述，不代表复现实验、新颖性、课程完成度或本机可运行性审查。

总体：7/7 的书目及核心方法描述为 **VERIFIED**。没有发现必须更正的 **METADATA_MISMATCH** 或 **OVERCLAIM**。I3DM 的正式会议去向仍为 **INCONCLUSIVE**，与原文保留 arXiv 身份的写法一致。

## 1. VMem — VERIFIED

核对一致：Runjia Li、Philip Torr、Andrea Vedaldi、Tomas Jakab；*VMem: Consistent Interactive Video Scene Generation with Surfel-Indexed View Memory*；ICCV 2025；arXiv 首版 2025-06-23、v3 2025-08-14。[版本记录](https://arxiv.org/abs/2506.18903v3)、[作者项目及 ICCV BibTeX](https://v-mem.github.io/)。

原论文 §3.1 支持：用 surfel 索引观察过它的历史帧；渲染索引后选择参考帧；匹配 surfel 后合并帧索引、丢弃新 surfel。几何主要用于检索，准确几何不能直接保证生成收益，这一限定合理。[论文 §3.1](https://arxiv.org/html/2506.18903v3#S3.SS1)。

独立查看固定版本代码，确认 `merge_surfels` 追加来源时间索引，`pointmap_to_surfels` 通过 `conf_thresh` 和深度阈值过滤；其 CUT3R 推理还调用 `scene.clean_pointcloud()`。因此原文说既有来源关联、confidence 阈值和清理成立。[固定 pipeline](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/modeling/pipeline.py)、[固定 surfel_inference](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/extern/CUT3R/surfel_inference.py)。

可选精确化：若讲实现细节，把“通过目标视角可见的面片”写为“通过新目标相机组的平均位姿渲染可见 surfel”。原文作为高层概述可保留；不要将匹配时合并来源索引误述为更新旧 surfel 位置。

## 2. CUT3R — VERIFIED

核对一致：Qianqian Wang、Yifei Zhang、Aleksander Holynski、Alexei A. Efros、Angjoo Kanazawa；*Continuous 3D Perception Model with Persistent State*；CVPR 2025 Oral；arXiv 首版 2025-01-21。[原始记录](https://arxiv.org/abs/2501.12387)、[作者项目](https://cut3r.github.io/)。

作者项目明确：输入图像持续更新状态，输出共同坐标系的点图与相机参数；revisiting 先遍历全部图像，再冻结最终状态重新读取，因此与只见过去上下文的 online 设置不同。原文比较准确，没有把两种设置混为一谈。[方法与 Online vs. Revisiting](https://cut3r.github.io/)。

附带确认：官方 README 区分 224 linear 中间检查点和 512 DPT 最终检查点，并说明默认编码器并行处理导致内存随帧数增长。[官方检查点与推理说明](https://github.com/CUT3R/CUT3R#download-checkpoints)。本核验未运行 CPU/MPS，也未验证文档后半段 RoPE fallback 的逐行差异。

## 3. Spann3R — VERIFIED

核对一致：Hengyi Wang、Lourdes Agapito；*3D Reconstruction with Spatial Memory*；3DV 2025，78–89；arXiv 首版 2024-08-28。3DV 与预印本年份区分正确，不能改为 ECCV 2024。[作者项目与正式 BibTeX](https://hengyiwang.github.io/projects/spanner)、[arXiv 记录](https://arxiv.org/abs/2408.16061)。

外部空间记忆、查询过去三维信息、直接预测共同坐标系点图、无需优化式全局对齐，均有原始摘要与方法说明支持。原文没有把它包装成视频生成系统。[作者方法说明](https://hengyiwang.github.io/projects/spanner)。

无需更正；若需解释“全局”，可补为“初始帧坐标系”，避免被理解为已知的真实世界坐标系。

## 4. ElasticFusion — VERIFIED

核对一致：Thomas Whelan、Stefan Leutenegger、Renato F. Salas-Moreno、Ben Glocker、Andrew J. Davison；*ElasticFusion: Dense SLAM Without A Pose Graph*；RSS 2015；DOI 10.15607/RSS.2015.XI.001。会议网页省略了若干中间名，论文首页支持原文使用的完整形式；没有混入后续期刊版。[RSS 官方记录](https://www.roboticsproceedings.org/rss11/p01.html)、[RSS 官方论文](https://roboticsproceedings.org/rss11/p01.pdf)。

官方摘要直接支持 RGB-D、增量 surfel 地图、frame-to-model 跟踪、windowed fusion、非刚性表面修正。将其作为在线融合与纠正的先例成立；原文没有把简单均值更新称为完整 ElasticFusion 复现。[RSS 摘要](https://www.roboticsproceedings.org/rss11/p01.html)。

访问说明：作者网站 PDF 在本次打开时返回工具 `Internal Error`；RSS 官方论文可访问。这是访问错误，不是论文缺失，也不能据此判断作者链接永久失效。建议优先链接 RSS 官方 PDF。

## 5. Probabilistic Surfel Fusion — VERIFIED

核对一致：Chanoh Park、Soohwan Kim、Peyman Moghadam、Clinton Fookes、Sridha Sridharan；*Probabilistic Surfel Fusion for Dense LiDAR Mapping*；ICCV Workshops 2017，Multiview Relationships in 3D Data；arXiv:1709.01265。[作者提交记录](https://arxiv.org/abs/1709.01265)、[第一作者发表页](https://copark86.github.io/publication/2017-10-29-surfelfusion)。

一手摘要支持考虑表面分辨率与测量不确定性的关联，以及 Bayesian filtering 融合；与 LiDAR 距离、光束入射角相关的噪声是建模条件。原文没有把该传感器模型直接等同于学习模型或生成内容错误。[原论文](https://arxiv.org/abs/1709.01265)。

访问说明：CVF 条目的直接打开返回 `Internal Error`；搜索返回的官方条目 BibTeX 含 `Workshops`，作者主页及 arXiv Comments 也独立确认 workshop 身份。CVF 页面上方的通用 ICCV 标题不能作为“主会”的依据。

## 6. TUM RGB-D — VERIFIED

核对一致：Jürgen Sturm、Nikolas Engelhard、Felix Endres、Wolfram Burgard、Daniel Cremers；*A Benchmark for the Evaluation of RGB-D SLAM Systems*；IROS 2012。作者 PDF 首页支持完整作者名单，TUM 官方书目支持会议年份。[作者论文](https://jsturm.de/publications/data/sturm12iros.pdf)、[官方书目](https://cvg.cit.tum.de/research/vslam?key=sturm12iros)。

Kinect RGB/深度、动捕轨迹参考，以及“深度并非无噪表面真值”均成立；官方当前页面确实标注默认数据 CC BY 4.0、随附代码 BSD-2-Clause，除非另有标注。[数据与许可](https://cvg.cit.tum.de/data/datasets/rgbd-dataset)。

建议补一句限定：**“回投点云同时包含深度、轨迹与标定误差，动捕轨迹也不是无误差的三维表面真值。”** 原论文 §IV-C 明确指出，动捕位姿不能直接用于生成或评估高精度场景三维模型；这加强原文的测量参考边界，不构成现有表述的错误。[论文 §IV-C，第 5 页](https://jsturm.de/publications/data/sturm12iros.pdf#page=5)。

## 7. I3DM — VERIFIED；正式会议去向 INCONCLUSIVE

核对一致：Jia Li、Han Yan、Yihang Chen、Siqi Li、Xibin Song、Yifu Wang、Jianfei Cai、Tien-Tsin Wong、Pan Ji；*I3DM: Implicit 3D-aware Memory Retrieval and Injection for Consistent Video Scene Generation*；arXiv:2603.23413，2026；首版 2026-03-24、v2 2026-07-31。[版本与作者](https://arxiv.org/abs/2603.23413v2)。

方法描述准确：借助预训练前馈 NVS 模型的中间特征评分检索，隐式对齐历史内容并用可靠区域作为生成条件，绕开显式三维重建。将其列为可靠区域处理和三维感知检索的相关先例合理；不能由此推导其已解决全部遮挡。[作者项目](https://riga2.github.io/i3dm/)。

正式会议信息未核实到：项目仍标 `Arxiv, 2026`，第一作者主页仍归为 `Preprints`。保留原文“本轮没有核实到正式会议录用信息”；不能改成“尚未录用”或“从未发表”。[第一作者主页](https://riga2.github.io/)。

## 使用边界

上述核验支持“相关机制已有先例”，不能独立证明候选方法有新颖性或无新颖性。关于本机实验、生成质量、RoPE 实现差异、是否完成课程要求及真实导师交流等，应由对应运行记录或人工事实另行核验。本核验未引入定量性能结论，未改动原文或研究代码。
