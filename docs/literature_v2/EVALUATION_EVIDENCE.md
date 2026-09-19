# 评价方法分支：已核验证据

记录：2026-09-06T00:28:57.252298+08:00。检索开始：2026-09-05 23:57:04（Asia/Shanghai）。本文件是给综述使用的证据表，不是综述正文，也不代表任何新增实验已经执行。

## 检索与核验

先读项目 AGENTS、研究记忆、最新日志和任务书；采用 deep-research 的两轮检索与两步核验。第一步核对标题作者存在；第二步对照原文的具体方法、条件和局限。七项均通过，但 VERIFIED 仅说明转述与原文相符，不代表原论文已被本项目复现。

查询时点：前两轮有实际读钟，后续查询未单独读钟，只记顺序与时间区间。六份全文快照实际下载于 2026-09-06 00:05:08–00:05:09，SHA256及UTC时间见JSON。中断后的保存时点不冒充持续工作时长。

### 1-wide

2026-09-05T15:57:04Z


- `camera controlled video generation geometric consistency benchmark reconstruction evaluation WorldScore`
- `world models spatial consistency evaluation benchmark camera trajectory occlusion`
- `TUM RGB D benchmark ground truth evaluation relative pose error absolute trajectory error official`

发现：发现 WorldScore、TUM 官方工具、WorldExam、WorldRoamBench，收窄至评测模型、回访和遮挡。

### 2-narrow

2026-09-05T15:57:22Z


- `WorldConsist benchmark world video generation geometric consistency official paper`
- `WorldScore Duan Yu 3D consistency reprojection error DUSt3R occlusion camera control`
- `WorldExam Yang Shang scene revisit 3D consistency camera control benchmark paper`
- `WorldRoamBench long horizon stability memory action decoupled benchmark`

发现：发现 GeCo、相似名称 WCS；WorldRoamBench 明确提出控制误差会混淆回访。

### 2-verification

实际发生于第二轮后、2026-09-06 00:05 源快照前；未单独读钟，不补造秒级时点。


- `"WorldConsist" benchmark`
- `"GeCo" "Geometric Consistency" video arxiv`
- `"World Consistency Score: A Unified Metric for Video Generation Quality"`
- `"A Benchmark for the Evaluation of RGB-D SLAM Systems" Sturm Engelhard Endres Burgard Cremers`

发现：核对 GeCo 题名和作者；WCS 摘要写实验蓝图，不应作为已完成大规模实验证据。TUM 标题作者核对通过。

### 3-citation-chain

实际发生于第二轮后、2026-09-06 00:05 源快照前；未单独读钟。


- `"WorldConsist" VMem`
- `"MEt3R" metric multi view consistency authors`
- `"WorldScore" "DROID" camera`
- `"WorldExam" "Scene Revisit" reconstruction`

发现：补齐 MEt3R；发现直接批评神经几何评测器的 SysCON3D 原始论文。

### 3-existence-and-resource-check

实际发生于第二轮后、2026-09-06 00:05 源快照前；未单独读钟。


- `"WorldScore: A Unified Evaluation Benchmark" arxiv`
- `"Can These Views Be One Scene" Paul Kaushik Yuille`
- `"WorldConsist" "benchmark" video`
- `"MEt3R" "github"`

发现：确认 SysCON3D 作者页面、论文与代码；MEt3R 官方 CUDA/PyTorch3D 依赖；WorldConsist 精确名称仍未确认。

## 七项核心证据

每项中“可做”和“建议”属于本轮研究设计判断；文献主张由链接支持。

### E1 · A Benchmark for the Evaluation of RGB-D SLAM Systems

作者：Jürgen Sturm, Nikolas Engelhard, Felix Endres, Wolfram Burgard, Daniel Cremers。版本：IROS 2012; official dataset documentation checked at retrieval。

核验：存在 VERIFIED（[来源](https://jsturm.de/publications/data/sturm12iros.pdf), [来源](https://cvg.cit.tum.de/data/datasets/rgbd-dataset)）；主张匹配 VERIFIED（[原文](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/tools)，Evaluation; Absolute Trajectory Error; Relative Pose Error）。

TUM 提供 Kinect RGB-D 与外部动作捕捉相机轨迹；ATE 对齐后比较整条轨迹位置，RPE 比较指定间隔的相对运动，官方提供离线脚本。

方法签名：`RGB-D + mocap trajectory → timestamp association → alignment / pose-pair comparison → ATE / RPE`。

真值使用：轨迹参考来自外部 mocap；Kinect depth 是测量。[官方格式说明](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats)规定 PNG 深度除5000、0为无效、深度尺度已预先修正。

条件/消融：原论文39段、两个室内环境。项目当前仅fr1_xyz，分成时间块不等于跨场景。要分开标注尺度校准与测试图。

局限/版本：ATE/RPE不评估记忆来源关联、选帧、生成画面。全序列拟合尺度与首帧校准属于不同协议；不能事后替换旧主指标。

本机条件：官方离线脚本及已有本地TUM数据可支持CPU级评分；需要另建版本固定的补充协议。

支持：RQ2: 外部几何/位姿参照；RQ3: 本机公开测量诊断。关系：与E2/E3的无场景GT自一致性不同。

### E2 · WorldScore: A Unified Evaluation Benchmark for World Generation

作者：Haoyi Duan, Hong-Xing Yu, Sirui Chen, Li Fei-Fei, Jiajun Wu。版本：ICCV 2025; full text arXiv:2504.00983v2。

核验：存在 VERIFIED（[来源](https://openaccess.thecvf.com/content/ICCV2025/html/Duan_WorldScore_A_Unified_Evaluation_Benchmark_for_World_Generation_ICCV_2025_paper.html), [来源](https://arxiv.org/abs/2504.00983)）；主张匹配 VERIFIED（[原文](https://arxiv.org/html/2504.00983v2)，3.3; C.1-C.3; C.8-C.9; D）。

把控制、质量、动态分开；静态3D一致性用DROID-SLAM优化后共同可见点的重投影残差；相机控制对照给定轨迹并拟合平移尺度。

方法签名：`initial scene + next-scene prompt + trajectory → generated video → DROID-SLAM pose/depth + other estimators → separate scores`。

真值使用：给定轨迹是控制目标，不是生成场景的外部三维真值；3D分数是重建自一致性代理。

条件/消融：3000例（2000 static/1000 dynamic），室内/室外、真实感/风格化；人类偏好验证。

局限/版本：共同可见区域外的错误可能遗漏；分数依赖SLAM与经验归一化边界。arXiv摘要元数据写19模型，而同v2正文与CVF写20，引用实验规模应注明以正文为准。

本机条件：官方代码https://github.com/haoyi-duan/WorldScore 已确认；未在本机安装运行全套，不能把公开实现当MPS兼容证据。

支持：RQ2: 控制/几何/外观分别评价；RQ3: 可借用维度与公开任务。关系：E4补其遮挡盲点；E6/E7增加回访诊断。

### E3 · MEt3R: Measuring Multi-View Consistency in Generated Images

作者：Mohammad Asim, Christopher Wewer, Thomas Wimmer, Bernt Schiele, Jan Eric Lenssen。版本：CVPR 2025; inspected arXiv:2501.06336v2; repository has subsequent options。

核验：存在 VERIFIED（[来源](https://arxiv.org/abs/2501.06336), [来源](https://vip.mpi-inf.mpg.de/met3r/)）；主张匹配 VERIFIED（[原文](https://arxiv.org/html/2501.06336v2)，3; experiments; Appendix C）。

无需给定相机位姿：DUSt3R点图把DINO/FeatUp特征投影到共同视角，再比较特征；目标是跨视图一致性而非单图真实感。

方法签名：`image pair → DUSt3R geometry → feature warping + overlap → symmetric feature disagreement`。

真值使用：不需要成对生成图GT或输入位姿；依赖学习几何和特征。

条件/消融：论文比较不同新视角/视频生成方法，包含RealEstate10K；图像质量与一致性分开。

局限/版本：共同支持域、骨干与特征影响分数；E5提供失效测试，不能把论文的稳健性宣称无限外推。当前官方README默认backbone=mast3r，论文基础描述是DUSt3R，复现必须固定配置。

本机条件：官方https://github.com/mohammadasim98/met3r 明列CUDA>=11.3、PyTorch3D>=0.7.5，测试CUDA11.8；未验证Mac，不能承诺开箱即用。

支持：RQ2: 生成一致性可独立于图像质量；RQ3: 可设计低成本图对诊断但需适配。关系：E4指出细微变形敏感性不足；E5直接检查其骨干与聚合失效。

### E4 · GeCo: Evaluating Geometric Consistency for Video Generation via Motion and Structure

作者：Leslie Gu, Junhwa Hur, Charles Herrmann, Fangneng Zhan, Todd Zickler, Deqing Sun, Hanspeter Pfister。版本：arXiv:2512.22274v5, revised 2026-08-19; v1 title was A Differentiable Geometric Consistency Metric for Video Generation。

核验：存在 VERIFIED（[来源](https://arxiv.org/abs/2512.22274), [来源](https://geco-geoconsistency.github.io/)）；主张匹配 VERIFIED（[原文](https://arxiv.org/html/2512.22274v5)，3.1; 4.1-4.3; 6; B.1）。

光流残余运动检测可共同看见表面的变形；深度重投影补遮挡前后结构变化，两者融合为逐像素诊断图。

方法签名：`static video → UFM flow + VGGT depth/pose → motion + structure maps → fused geometric error`。

真值使用：WarpBench人工TPS位移、OccluBench合成遮挡编辑用于已知异常校验；TartanAir v2比较预测与GT几何，DL3DV给真实视频噪声底。

条件/消融：显式做运动/结构消融、预测/GT几何与噪声实验；GeCo-Eval四类静态场景。

局限/版本：真实物体运动可被误罚；估计器误差仍存在。OccluBench IoU/F1使用逐图最优阈值，是诊断上界式设置，不是固定阈值部署结果。指导生成用H200且增加耗时，不能外推Mac。

本机条件：https://github.com/ShixuanGu/GeCo 已公开UFM/VGGT实现，README测试CUDA12.8。此分支没有运行。

支持：RQ2: 几何/可见性评价分解；RQ3: 可借鉴已知异常校验。关系：互补E2/E3；与E5共同要求审查评测骨干。

### E5 · Can These Views Be One Scene? Evaluating Multiview 3D Consistency when 3D Foundation Models Hallucinate

作者：Soumava Paul, Prakhar Kaushik, Alan Yuille。版本：arXiv:2605.18754v1, 2026-05-18; preprint。

核验：存在 VERIFIED（[来源](https://arxiv.org/abs/2605.18754), [来源](https://mvp18.github.io/3d-consistency-metrics/)）；主张匹配 VERIFIED（[原文](https://arxiv.org/html/2605.18754v1)，3.1-3.2; 4-7; F; L.3-L.4）。

SysCON3D发现学习骨干可给无关场景/噪声虚构几何支持；分解骨干、残差和聚合，并用COLMAP注册、密集支持和失败信息交叉评价。

方法签名：`controlled corruptions → backbone / residual / aggregation ablation; SfM+MVS → support × agreement × coverage; human comparison`。

真值使用：无真实场景GT的指标，已知人工扰动提供排序参照；人类研究把3D一致性、真实感、与输入合理性分开。

条件/消融：Mip-NeRF360受控扰动；真实NVS比较含DL3DV24场景、Mip-NeRF3609场景；11人959对比较，K=3/6/9。

局限/版本：COLMAP也会因弱纹理、重复结构、低重叠失败；差输出全失败时排序粗糙。受控噪声压力测试不是自然视频生成失败率。论文高相关属于有限模型/场景排序，不是普遍定理。

本机条件：https://github.com/mvp18/3DConsistency-metrics 有代码和SysCON3D清单；官方神经环境为CUDA，论文COLMAP约5分钟/RTX3090；不能把这个时间用于本机预算。

支持：RQ1: 学习几何支持不自动可信；RQ2: 不可循环地用同一模型证明自己；RQ3: 失败也应进入分母。关系：对E3的直接反证；约束E4/E6/E7学习重建指标的解释。

### E6 · WorldRoamBench: An Open-World Benchmark for Long-Horizon Stability of Interactive World Models

作者：Ting-Bing Xu, Jiacheng Sui, Zhe Gao, Kewei Shi, Wenjin Yang, Zhicheng Liu, Zhaoxu Sun, Mingchao Sun, Hongyu Pan, Fan Jiang, Mu Xu, Qi Fan, Yong Li, Baoquan Chen。版本：arXiv:2606.31672v1, 2026-06-30; website is later mutable snapshot。

核验：存在 VERIFIED（[来源](https://arxiv.org/abs/2606.31672), [来源](https://worldroam.amap.com/)）；主张匹配 VERIFIED（[原文](https://arxiv.org/html/2606.31672v1)，3.4; F.1; H）。

固定对称帧会混合回访记忆与动作误差；按实际转向点分段、重建并对齐两段点云，再分别量化保留与新增但无旧支持的几何。

方法签名：`video + action → executed transition → depth/pose clouds → semantic/depth filtering → registration → retention/anti-hallucination`。

真值使用：动作指令辅助定位；几何来自估计而非外部扫描GT，最近邻距离阈值随场景对角线缩放。

条件/消融：v1为600+例、10–60秒、室内/自然/城市及第一/第三视角；网站后续写1000+，不能混算。

局限/版本：点云对齐可能吸收整体位姿偏差；未观察到的真实新表面不应自动解释为幻觉。分割/深度过滤改变计分范围，需报告保留率。仅借鉴设计不宣称已复现。

本机条件：可在本机复用已有点图做事先固定的补充诊断；完整官方模型/VLM依赖未在此分支核验运行。

支持：RQ2: 排除回访相机误差混淆；RQ3: 逐段报告优于仅首末帧。关系：比E2增加长时记忆；E7采用位姿最近的回访图，二者干预位置不同。

### E7 · WorldExam: Benchmarking World Models from Apparent Appearance to Inherent Reactivity

作者：Yuxue Yang, Shuyao Shang, Jiahe Wang, Zitong Zhou, Liang Tan, Junhan Zeng, Ruizhi Li, Junyan Li, Yu Liu, Xiao Yang, Yong Li, Jun Zhu, Hongsheng Li, Tieniu Tan, Lue Fan, Zhaoxiang Zhang。版本：arXiv:2608.02603v1, 2026-08-03; preprint。

核验：存在 VERIFIED（[来源](https://arxiv.org/abs/2608.02603), [来源](https://worldexam.github.io/)）；主张匹配 VERIFIED（[原文](https://arxiv.org/html/2608.02603v1)，3, Static-Scene Track: Camera Control; Scene Revisit; General metrics）。

回访须同时满足相机返回和场景保留；在返回时间窗找估计位姿最近的图，分别报告返回成功和PSNR/LPIPS/SSIM，再组合。

方法签名：`outgoing + inverse control → recovered poses → nearest revisit frame → camera success + appearance score`。

真值使用：初始RGB是回访外观参照；相机/几何由VGGT-Ω估计，不是外部GT；3D一致性改用其几何往返投影。

条件/消融：1474例、8任务、20模型；静态/动态互动分轨，避免把不支持互动的接口当等价任务。

局限/版本：近似回到原位仍可能有视差，外观差不唯一归因记忆；学习位姿质量影响选图。2026-09-06读取官方GitHub仅README和teaser图，不能说评测代码已完整开源。

本机条件：https://github.com/YuxueYang1204/worldexam 仓库存在，但读取时未见可执行评测实现。

支持：RQ2: 回访双条件与控制接口分层；RQ3: 可借鉴逐项呈现。关系：E6用云对齐，E7用位姿选回访帧；都依赖估计几何；扩展E2质量/控制区分。

## 未纳入与盲点

- WorldConsist：UNVERIFIABLE。三次精确名称检索未确认对应原始论文/基准，不引用；不声称不存在。
- World Consistency Score: A Unified Metric for Video Generation Quality：VERIFIED metadata/abstract only, excluded from core。作者Akshat Rakheja, Aarsh Ashdhir, Aryan Bhattacharjee, Vanshika Sharma已确认；摘要把验证描述为blueprint，不以其证明已实测的优越性。 [检索到的主源](https://arxiv.org/abs/2508.00144)
- Quantitative Video World Model Evaluation for Geometric-Consistency：candidate only, excluded。与本轮覆盖重叠；未完成双步全文核验，不用于主张。 [检索到的主源](https://arxiv.org/abs/2605.15185)

没有核实某个统一公开benchmark可直接把三维误差、来源关联错误、检索排序、生成质量串成单因素因果链；本轮核心评价方法大多从生成图/视频开始评分，未观察内部检索。

未确认被测模型预训练是否包含当前TUM序列；跨时间块不能解决训练污染或跨场景泛化。

动态世界和长期物体状态并非本项目当前静态照片组件实验已覆盖内容。

完整视频生成仍未发生；公开示例不能冒充本项目生成。

## 给父任务的可执行建议（尚未执行）

- 保持S0-S6旧协议和结果。新增评价必须另行冻结：输入、尺度规则、掩码、采样、阈值、失败处理、主次指标。
- 先利用现有真实RGB-D，另取明确不同环境/序列作为场景级留出；调参只用开发场景。若仍只有fr1_xyz，只称同场景诊断。
- 外部测量深度/位姿仅供封存选择后的评分；若输入GT位姿/尺度，单列oracle条件。训练和测试边界与查询写回政策单独记录。
- 成对比较使用共同有效像素以免挑掉难点；同时公布每法自身覆盖、共同覆盖、无效与遮挡数量。深度残差、边界/遮挡分层与相机差分别报告。
- 选帧变化只表示结果不同。另用事先固定的独立可见性参照量化历史参考支持；固定候选池、帧数、NMS等，单独消融几何更新和检索规则，加入相同预算的最近位姿/均匀历史基线。
- 给评测器增加干净图对、重复图、已知局部错位/遮挡编辑等正负对照；重复图可一致但没有新视角覆盖，因此同时报告视点变化，避免把静止当漫游成功。这属于人工诊断，单列。
- 有真实生成视频后才做相同初图/相机/种子/预算的成对实验，分别报告相机执行、共同可见几何、回访外观与主观质量；回访先查实际位姿，不能只按帧号配对。
- 本机优先复算已有数组和TUM官方离线轨迹指标；MEt3R/GeCo/WorldScore/COLMAP完整分数仅在依赖与小样本预算实测后采用，不把CUDA论文计时当Mac可运行性证明。

评测逻辑：TUM给外部测量参照；WorldScore把控制、几何、外观拆开；MEt3R给图对一致性；GeCo补可见性与形变；SysCON3D审查评测器；WorldRoamBench与WorldExam检查返回旧位置。它们互补，不能用其中一个分数替代整个“几何—关联—选帧—生成”证据链。

## 复核记录

完整机器可读证据与查询记录：[EVALUATION_EVIDENCE.json](EVALUATION_EVIDENCE.json)。原文快照在当前工作区 `work/evaluation_sources/`；主源URL和SHA256写入JSON，项目账本由父任务统一追加。
