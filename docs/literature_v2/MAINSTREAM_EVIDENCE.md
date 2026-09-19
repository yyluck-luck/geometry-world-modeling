# 主流方法证据簿（第二轮，独立检索分支）

记录时间：2026-09-05 16:29:39 UTC（Asia/Shanghai 为 2026-09-06 00:29:39）。本次完成的来源检索为本地 2026-09-05 23:56:54 至 2026-09-06 00:05:51，随后因用户消息中断并恢复整理。此处不虚构工作时长。

本文件是供父任务合并的核验证据，不是综述正文，也不评价 S6。冻结问题见 [研究任务书](../LITERATURE_RESEARCH_BRIEF_V2.md)。已读项目 AGENTS、研究记忆和最新日志，以及 deep-research 的主规范、search-strategy、citation-protocol。只查公开原论文与作者资源。完整可处理记录见 [MAINSTREAM_EVIDENCE.json](MAINSTREAM_EVIDENCE.json)。

## 证据等级和范围

两步核验：先确认完整标题和作者，再核对所用机制、表格和实验条件。下列 10 项为 VERIFIED，意思是限定断言与原文相符，不是实验已复现。8 项核心方法加 2 项边界补充，不以篇数替代覆盖。本分支采用两个主查询模式：核心机制×任务，以及实际发现的引用网络；未宣称独立完成整个领域的三篇/子方向覆盖。

## 可用于最近工作对照的重点

| 工作 | 对照所需方法签名 | 可以支持的层次 | 必须保留的条件 |
|---|---|---|---|
| [VMEM](https://arxiv.org/html/2506.18903v3) | 粗surfel几何索引＋历史RGB/相机库 | 给出检索策略→生成指标消融；不提供改善点误差必改善生成的证据。 | RealEstate10K及Tanks-and-Temples的cycle trajectories；返回路径为原路逆行。 |
| [ANCHORWEAVE](https://arxiv.org/html/2602.14941v1) | 逐帧局部point cloud及pose；放入共同世界坐标但各自独立保存 | 有局部/全局和控制器消融，但几何与anchor数量的交织需明确。 | Table3随K=1/2/4同时增加参考预算（最多6/12/24帧），不是固定预算检索策略比较。 |
| [SPATIA](https://arxiv.org/html/2512.15716v1) | 静态场景point cloud＋历史参考帧 | 2×2消融和密度结果可指导分开评估各层；不能用密度代表误差。 | 空间记忆消融在WorldScore子集闭环；密度实验在RealEstate测试集与GT视频成对比较。 |
| [GIMWORLD](https://arxiv.org/html/2606.02436v1) | 固定数量implicit memory tokens | 同预算pruning及监督位置消融是可参考的区分设计。 | 前置context不是单图起步；合成UE5视频不是实际RGB-D测量。 |
| [LSMWORLD](https://arxiv.org/html/2606.09828v2) | 世界坐标中的3D latent tokens | 最近直接检查depth source的相关工作，但不隔离来源关联/选帧中介。 | depth-source表没有同时给出独立真实depth误差，不能把它当深度精度与生成质量的量化单调函数。 |

优先审查的边界：AnchorWeave 的全局/局部对比同时改变单/多 anchor，不能当作只改善几何的试验；其“平均”消融是 anchor 条件融合，不是 surfel 坐标平均。VMem 主要用粗几何找到历史 RGB，粗几何的小改动未必跨过最终排序的边界。这两点是不同机制，不能互相替代证据。

## 逐项核验

### VMEM · VMem: Consistent Interactive Video Scene Generation with Surfel-Indexed View Memory

作者：Runjia Li, Philip Torr, Andrea Vedaldi, Tomas Jakab。

首次公开：2025-06-23；本次主张版本：2506.18903v3（2025-08-14）；发表信息：ICCV 2025。角色：core。

来源：[arXiv 元数据](https://arxiv.org/abs/2506.18903)；[原文](https://arxiv.org/html/2506.18903v3)；[作者/正式资源 1](https://v-mem.github.io/)；[作者/正式资源 2](https://github.com/runjiali-rl/vmem)。

核验：**VERIFIED**。第一步：arXiv元数据、CVF论文和作者项目页的完整标题与四位作者相符。 第二步：已查§3.1、§4.1–4.4、Table4、Appendix C/D；以下主张与对应原文相符。

方法签名：粗surfel几何索引＋历史RGB/相机库。写入：CUT3R等估计点图；距离及法线阈值匹配，匹配时增加来源帧集合并丢弃新surfel；否则新建。 读取：从目标块平均pose渲染带来源的可见surfels；按像素覆盖投票并做pose NMS后选参考帧。 生成器/输出：SEVA；主实验为LoRA微调K=4、M=4。。

可用断言：

- 几何在这里主要负责选择历史RGB，不直接充当最终场景颜色渲染；作者明确提出只需足以选对参考的粗几何。（§1, §3.1；[原文](https://arxiv.org/html/2506.18903v3)）
- Table4在K=4时比较Temporal、Camera Distance、FOV、VMem，VMem的PSNR=14.82，camera-distance=13.27；这支持该评测中检索策略对生成的作用。（§4.4, Table4；[原文](https://arxiv.org/html/2506.18903v3)）
- K=17时VMem的rotation distance=0.892高于camera-distance=0.821；不能说所有指标全面最好。（Table4；[原文](https://arxiv.org/html/2506.18903v3)）
- 官方论文桥接包含冻结用户相机、冻结旧深度的优化过程，独立CUT3R前向不能直接等同该步骤。（Appendix C；[原文](https://arxiv.org/html/2506.18903v3)）

条件和局限：

- RealEstate10K及Tanks-and-Temples的cycle trajectories；返回路径为原路逆行。
- K=4与K=17属于不同生成器配置；12倍速度数字包含上下文减少及LoRA适配，不能归为surfel更新规则的单因素效果。
- Appendix D承认轨迹简单、遮挡有限，低层图像相似指标不等同真实多视图一致性。
- 本文未找到对连续几何误差幅值→来源关联→最终选帧→视频质量的独立剂量消融；这是本轮检索范围陈述。

RQ 支持：

- RQ1：直接给出关联、写入、渲染选帧机制。
- RQ2：给出检索策略→生成指标消融；不提供改善点误差必改善生成的证据。
- RQ3：论文代码可定位组件；生成/微调成本与CPU组件核验分开。

跨工作关系：

- 使用CUT3R几何和SEVA生成；论文讨论Gen3C、WorldMem、StarGen作为相邻方法。
- 与AnchorWeave不同：保存surfels是为了取RGB参考，而后者渲染多个局部点云作为生成条件。

资源边界：已核官方项目和仓库存在；未下载或运行其生成权重。

### CUT3R · Continuous 3D Perception Model with Persistent State

作者：Qianqian Wang, Yifei Zhang, Aleksander Holynski, Alexei A. Efros, Angjoo Kanazawa。

首次公开：2025-01-21；本次主张版本：2501.12387v1（2025-01-21）；发表信息：CVPR 2025。角色：core。

来源：[arXiv 元数据](https://arxiv.org/abs/2501.12387)；[原文](https://arxiv.org/html/2501.12387v1)；[作者/正式资源 1](https://cut3r.github.io/)；[作者/正式资源 2](https://github.com/CUT3R/CUT3R)。

核验：**VERIFIED**。第一步：作者项目、CVF论文及arXiv完整标题和五位作者一致。 第二步：核对Abstract、state update/readout、作者项目Online vs Revisiting和论文Limitations。

方法签名：固定的学习潜在state tokens。写入：每张RGB图像tokens与state交互，递归更新state。 读取：由图像/state读出pointmaps和camera；虚拟相机raymap可查询未观察结构。 生成器/输出：几何回归网络，非视频扩散生成器。。

可用断言：

- 模型提供在线共同坐标pointmaps与相机预测；动态/静态图像流及照片集合均为论文任务。（Abstract, Method；[原文](https://arxiv.org/html/2501.12387v1)）
- 作者revisiting设置先看全序列，再冻结最终state重算同序列；该设置有全序列上下文。（作者项目页State Analysis；[原文](https://arxiv.org/html/2501.12387v1)）
- 作者承认无global alignment时极长序列可漂移，远离已有视角的确定性结构预测可能模糊。（Limitations；[原文](https://arxiv.org/html/2501.12387v1)）

条件和局限：

- 在线前向与看完全部数据后的revisiting是不同上下文条件。
- 论文几何任务结果不含surfel历史参考选择或视频生成质量。
- 学习state更新能力不保证逐帧误差单调下降。
- 本轮不将论文最终模型精度等同本项目224 linear中间检查点。

RQ 支持：

- RQ1：提供学习几何和隐式持续状态的上游。
- RQ2：只到重建/相机层，不能独立支持生成因果链。
- RQ3：官方代码/权重入口允许组件实验；硬件兼容性须本机另验。

跨工作关系：

- 被VMem与SPMem作为上游几何来源；AnchorWeave采用后继TTT3R线索。

资源边界：官方项目和仓库存在；本分支未运行模型。

### SPMEM · Video World Models with Long-term Spatial Memory

作者：Tong Wu, Shuai Yang, Ryan Po, Yinghao Xu, Ziwei Liu, Dahua Lin, Gordon Wetzstein。

首次公开：2025-06-05；本次主张版本：2506.05284v1（2025-06-05）；发表信息：NeurIPS 2025。角色：core。

来源：[arXiv 元数据](https://arxiv.org/abs/2506.05284)；[原文](https://arxiv.org/html/2506.05284v1)；[作者/正式资源 1](https://spmem.github.io/)；[作者/正式资源 2](https://github.com/spmem/spmem)；[作者/正式资源 3](https://proceedings.neurips.cc/paper_files/paper/2025/file/467655d26fcc207bca08915dc91964c6-Paper-Conference.pdf)。

核验：**VERIFIED**。第一步：arXiv及NeurIPS官方论文完整标题/作者一致。 第二步：核对§3.2公式2、§4.4、作者项目及当前仓库README。

方法签名：静态全局point cloud/TSDF＋近期working frames＋稀疏episodic frames。写入：论文用CUT3R在线点图，TSDF标准加权平均融合静态结构。 读取：几何渲染作为空间条件，近期帧负责运动连续性，稀疏历史帧补细节。 生成器/输出：CogVideoX框架。

可用断言：

- TSDF更新公式是既有加权平均；论文三种记忆各承担空间、短期动态和远期细节角色。（§3.2 Eq2；[原文](https://arxiv.org/html/2506.05284v1)）
- 移除working/episodic memory的生成消融支持两者作用，不能直接推出TSDF更准确必导致更好检索。（§4.4, Figure5；[原文](https://arxiv.org/html/2506.05284v1)）
- 截至本轮官方spmem/spmem公开了推理、训练、TSDF目录及数据/权重链接；当前README列出Depth-Anything-3依赖。（官方仓库README；[原文](https://arxiv.org/html/2506.05284v1)）

条件和局限：

- 数据构建时Mega-SaM处理完整视频；推理阶段论文用CUT3R。训练标注与在线输入需区分。
- 静态点云并不保存动态对象的完整演化状态。
- 论文关于TSDF抑制动态内容的描述不是任意动态/位姿误差条件的保证。
- AnchorWeave写作时称SPMem未开源，不能据此断言2026-09仍未开源。
- NeurIPS2025会议信息优先于当前仓库BibTeX中year=2026的出版年字段；引用时明确所指版本。

RQ 支持：

- RQ1：已有将多次估计融合为静态记忆的直接先例。
- RQ2：模块消融检验生成条件互补；尚非关联/检索分层因果实验。
- RQ3：官方资源已公开，未验证本机推理或链接可下载性。

跨工作关系：

- 不是Spatia（2512.15716）；两者标题和作者均不同。
- AnchorWeave对其作CogVideoX重实现，后者比较不等于运行当前官方代码。

资源边界：仓库/资源链接已读；未下载权重，未审查实际推理代码与论文的一致性。

### SPATIA · Spatia: Video Generation with Updatable Spatial Memory

作者：Jinjing Zhao, Fangyun Wei, Zhening Liu, Hongyang Zhang, Chang Xu, Yan Lu。

首次公开：2025-12-17；本次主张版本：2512.15716v1（2025-12-17）；发表信息：CVPR 2026（存在官方CVF论文）。角色：core。

来源：[arXiv 元数据](https://arxiv.org/abs/2512.15716)；[原文](https://arxiv.org/html/2512.15716v1)；[作者/正式资源 1](https://zhaojingjing713.github.io/Spatia/)；[作者/正式资源 2](https://openaccess.thecvf.com/content/CVPR2026/papers/Zhao_Spatia_Video_Generation_with_Updatable_Spatial_Memory_CVPR_2026_paper.pdf)。

核验：**VERIFIED**。第一步：arXiv标题/六位作者匹配，CVF正式论文存在。 第二步：以下数值按arXiv v1核对§3.1/3.2、Table4/5/7；未逐字比较CVF版全部数值。

方法签名：静态场景point cloud＋历史参考帧。写入：MapAnything估计/更新全局场景，排除动态实体；点云可体素化降采样。 读取：渲染目标相机轨迹的场景视频＋空间重合参考帧。 生成器/输出：Wan2.2与ControlNet。

可用断言：

- Table4有scene projection和reference frames的2×2消融：仅参考帧LPIPS_C=0.393，基线0.379；二者联合0.213。（Table4；[原文](https://arxiv.org/html/2512.15716v1)）
- 体素尺寸0.01→0.07米时PSNR18.58→15.97，支持该数据上密度/细粒度条件的作用。（Table7；[原文](https://arxiv.org/html/2512.15716v1)）
- 密度实验改变采样信息量，不是同密度下几何坐标准确性的消融。（Table7的实验操作；此为证据解释；[原文](https://arxiv.org/html/2512.15716v1)）

条件和局限：

- 空间记忆消融在WorldScore子集闭环；密度实验在RealEstate测试集与GT视频成对比较。
- 参考数、生成器条件、动态静态分离是多个可改变因素。
- 局部指标并非所有模块单独加上都改善；不能忽略参考帧单独的负例。
- 存在跨帧平均/更新功能本身已不是新的研究问题。

RQ 支持：

- RQ1：显式更新和参考帧同时存在的近邻方法。
- RQ2：2×2消融和密度结果可指导分开评估各层；不能用密度代表误差。
- RQ3：已定位论文/项目；本分支未核权重可下载性和MPS运行。

跨工作关系：

- 与SPMem不同；被AnchorWeave与LSM-World讨论。

资源边界：论文全文可读；只确认项目URL在论文中，未进行本机复现。

### ANCHORWEAVE · AnchorWeave: World-Consistent Video Generation with Retrieved Local Spatial Memories

作者：Zun Wang, Han Lin, Jaehong Yoon, Jaemin Cho, Yue Zhang, Mohit Bansal。

首次公开：2026-02-16；本次主张版本：2602.14941v1（2026-02-16）；发表信息：arXiv预印本；未另确认会议接收。角色：core-nearest。

来源：[arXiv 元数据](https://arxiv.org/abs/2602.14941)；[原文](https://arxiv.org/html/2602.14941v1)；[作者/正式资源 1](https://zunwang1.github.io/AnchorWeave)。

核验：**VERIFIED**。第一步：完整标题查询后，arXiv与作者项目的六位作者一致。 第二步：核对§3.2–3.5、§4.1/4.3、Table2/3、Appendix A/B/C；下面保留具体对照条件。

方法签名：逐帧局部point cloud及pose；放入共同世界坐标但各自独立保存。写入：TTT3R估计新帧局部几何；新生成帧追加到记忆库，避免单一全局融合。 读取：每8帧chunk以FOV预筛，再贪心增加可见覆盖，最多K=4局部anchor；多anchor attention与pose-guided fusion。 生成器/输出：CogVideoX-I2V-5B和Wan2.2-TI2V-5B；训练新增控制器。

可用断言：

- 直接把跨视图depth/pose不一致造成全局融合条件污染作为动机；局部记忆在生成条件端共同处理差异。（Abstract, §3.2；[原文](https://arxiv.org/html/2602.14941v1)）
- Table2全局/局部条件PSNR=16.31/20.96；同时全局条件为单anchor、局部为multi-anchor，因此不是只改变几何误差的单因素结论。（Table2, §4.3；[原文](https://arxiv.org/html/2602.14941v1)）
- Figure5/§4.3中简单平均的是多个anchor条件；pose-conditioned fusion更好，不能当作surfel坐标均值融合失败的直接证据。（Figure5, §4.3；[原文](https://arxiv.org/html/2602.14941v1)）
- 定量主测500视频，每视频70帧中49为target、剩余21为可检索history；这为partial-revisit条件，未保证21帧时间均早于49帧。（§4.1；[原文](https://arxiv.org/html/2602.14941v1)）
- 训练写明8×H100约一天；正文控制器在前90%去噪步骤使用，附录写80%，存在待澄清实现差异。（§4.1, Appendix A.1；[原文](https://arxiv.org/html/2602.14941v1)）

条件和局限：

- Table3随K=1/2/4同时增加参考预算（最多6/12/24帧），不是固定预算检索策略比较。
- Context-as-Memory、SPMem为作者重实现；后者使用TTT3R＋CogVideoX，勿称当前官方模型结果。
- Appendix B正文称首rendered frame优先，伪代码初始化P_latest；具体初始anchor实现需查代码。
- 没有由本文已查表格隔离“几何误差本身→来源关联→选帧→生成”的全部中介变量。
- 公开项目展示three×81-frame轨迹是作者生成案例；本轮未观看/复现全部视频。
- Table2 SSIM列按53.45/67.27呈现，Table3按0.6145/0.6435/0.6727；数字引用须保留原表尺度或明确归一化。

RQ 支持：

- RQ1：当前最贴近几何误差、记忆结构与检索联合设计的工作。
- RQ2：有局部/全局和控制器消融，但几何与anchor数量的交织需明确。
- RQ3：新模型训练明显超出单机组件诊断规模；可先复核贪心检索与输入控制。

跨工作关系：

- 与VMem同做几何辅助检索，但把局部renderings作为直接条件。
- 明确引用Spatia、SPMem、TTT3R；不等同于验证surfel均值更新。

资源边界：作者项目存在Code按钮；跟进Code的最后一次工具调用被中断，未把具体仓库或权重可用状态记为已核实。

### MOSAICMEM · MosaicMem: Hybrid Spatial Memory for Controllable Video World Models

作者：Wei Yu, Runjia Qian, Yumeng Li, Liquan Wang, Songheng Yin, Sri Siddarth Chakaravarthy P, Dennis Anthony, Yang Ye, Yidi Li, Weiwei Wan, Animesh Garg。

首次公开：2026-03-17；本次主张版本：2603.17117v1（2026-03-17）；发表信息：arXiv预印本；未另确认会议接收。角色：core。

来源：[arXiv 元数据](https://arxiv.org/abs/2603.17117)；[原文](https://arxiv.org/html/2603.17117v1)。

核验：**VERIFIED**。第一步：完整标题查询并以arXiv核对十一位作者。 第二步：核对Abstract、§2、§3、§4.2，尤其保留两个warping分支的不同表现。

方法签名：带3D位置的patch记忆。写入：将patch提升到3D保存，用patch-and-compose提供对齐条件。 读取：针对查询视角取patch并组合；Warped Latent和Warped RoPE补对齐。 生成器/输出：视频扩散＋PRoPE相机条件。

可用断言：

- 作者同时处理相机遵循、历史复用和动态变化；显式3D patch与原生成条件结合。（Abstract, §2；[原文](https://arxiv.org/html/2603.17117v1)）
- §4.2报告Warped Latent的相机运动更准，但视觉和memory retrieval弱于Warped RoPE；后者又在自回归图像边缘重复生成新物体。（§4.2；[原文](https://arxiv.org/html/2603.17117v1)）
- 大相机运动会使单独Mosaic Memory检索不到足够patch，不能把有3D索引等同有充分条件。（§4.2；[原文](https://arxiv.org/html/2603.17117v1)）

条件和局限：

- 数据含UE5、游戏、真实第一人称和Sekai；depth/pose以DA3或VIPE估计并过滤低质项。
- 估计几何标注不是完全无噪真值。
- 这里memory retrieval性能由其生成评测定义，不能直接等同离散top-K帧ID正确率。
- 非官方Rust搜索结果自称synthetic scaffold，不作为官方实现或实验证据。

RQ 支持：

- RQ1：3D patch而非整帧或全局surface的记忆路线。
- RQ2：相机控制较好但其它质量较差的明确取舍，反对单指标代替全部结果。
- RQ3：公开论文可读；本轮未确认官方代码/权重和本机可行性。

跨工作关系：

- 与AnchorWeave都利用局部对齐；前者重点patch组合和动态能力，后者保留逐帧局部点云并多anchor条件融合。

资源边界：只核实论文；没有采用搜索结果中的非官方Rust项目。

### GIMWORLD · Geometry-Aware Implicit Memory for Video World Models

作者：Zhengxuan Wei, Xu Guo, Xinghui Li, Xunzhi Xiang, Min Wei, Yiran Zhu, Qiulin Wang, Xintao Wang, Pengfei Wan, Xiangwang Hou, Qi Fan。

首次公开：2026-06-01；本次主张版本：2606.02436v1（2026-06-01）；发表信息：arXiv预印本；未另确认会议接收。角色：core。

来源：[arXiv 元数据](https://arxiv.org/abs/2606.02436)；[原文](https://arxiv.org/html/2606.02436v1)；[作者/正式资源 1](https://gim-world.github.io/)。

核验：**VERIFIED**。第一步：完整标题查询，arXiv作者字段与正文署名一致。 第二步：核对§3.2–3.5、§4.1、Table1/2/3/4；只使用表内与条件相符的数值。

方法签名：固定数量implicit memory tokens。写入：轻量encoder把带pose的历史压缩为state；训练用可由camera查询的head对齐VGGT几何特征。 读取：几何teacher/head推理时丢弃；GP互信息贪心历史pruning限制编码成本。 生成器/输出：记忆encoder/geometry head/backbone联合训练。

可用断言：

- Table2的memory geometry监督将Reproj.58.80→81.70，而MSE0.0628→0.0614，改善幅度因指标而不同。（Table2；[原文](https://arxiv.org/html/2606.02436v1)）
- Table3在K=200相同预算下比较Uniform、Camera FPS、MI greedy，明确把历史选择规则单独作为实验因素。（Table3；[原文](https://arxiv.org/html/2606.02436v1)）
- 训练/测试为MIND的100第一人称及100第三人称UE5片段，按50/50拆分，每个评测片段前约四分之一作为context。（§4.1；[原文](https://arxiv.org/html/2606.02436v1)）

条件和局限：

- 前置context不是单图起步；合成UE5视频不是实际RGB-D测量。
- Table1的第一人称translation RPE，Context-as-Memory0.0235低于GIM0.0247，因此不能写全面最优。
- 几何feature监督不是测量级depth精度提升的直接证明。
- 正文Table2段落将0.4823称作比较起点，那是Geometry Forcing行；无geometry行为0.5028。引用数值应按表格辨别。
- 项目URL被web工具判为不可安全打开；没有绕过，论文核验不受影响，代码/权重不宣称可用。

RQ 支持：

- RQ1：几何可约束隐式记忆，非必须维护显式点图。
- RQ2：同预算pruning及监督位置消融是可参考的区分设计。
- RQ3：全文与评测定义可读；本轮未确认可运行资源。

跨工作关系：

- 不同于VMem/AnchorWeave在推理时依赖显式几何；GIM将几何知识在训练时压入latent memory。

资源边界：arXiv全文可读；作者项目打开失败，未核代码/权重。

### LSMWORLD · Latent Spatial Memory for Video World Models

作者：Weijie Wang, Haoyu Zhao, Yifan Yang, Feng Chen, Zeyu Zhang, Yefei He, Zicheng Duan, Donny Y. Chen, Yuqing Yang, Bohan Zhuang。

首次公开：2026-06-08；本次主张版本：2606.09828v2（2026-08-27）；发表信息：arXiv预印本；未另确认会议接收。角色：core。

来源：[arXiv 元数据](https://arxiv.org/abs/2606.09828)；[原文](https://arxiv.org/html/2606.09828v2)；[作者/正式资源 1](https://microsoft.github.io/LatentSpatialMemory/)；[作者/正式资源 2](https://github.com/microsoft/LatentSpatialMemory)。

核验：**VERIFIED**。第一步：完整标题查询并核对arXiv十位作者，v2页及项目称LSM-World。 第二步：核对v2 §4、§5.3 Table3/4、Limitations和当前官方README。 纠正：搜索索引摘要仍称Mirage；以2026-08-27 v2的LSM-World为准，不混用v1名称与v2消融。

方法签名：世界坐标中的3D latent tokens。写入：将原生VAE网格latent按depth反投影；过滤动态/天空后跨chunk写入。 读取：直接在latent分辨率投影/warp，供ControlNet-style branch使用。 生成器/输出：Wan2.2-TI2V-5B＋side branch及LoRA。

可用断言：

- Table3保持backbone/training，RGB-cache替换相对latent-cache降低WorldScore平均70.36→67.71；测试的是表示和条件路径。（§5.3 Table3；[原文](https://arxiv.org/html/2606.09828v2)）
- Table4只换depth source，DA3/MapAnything/UniDepth平均70.36/69.66/69.13；作者称变化温和，支持对若干重建器的鲁棒性。（§5.3 Table4；[原文](https://arxiv.org/html/2606.09828v2)）
- 去掉dynamic filter大幅降低其3D/photo consistency；论文明确不会跨chunk保存动态actor状态。（Table3, Limitations；[原文](https://arxiv.org/html/2606.09828v2)）

条件和局限：

- depth-source表没有同时给出独立真实depth误差，不能把它当深度精度与生成质量的量化单调函数。
- 缓存效率倍数为特定模型/设置的作者测量，不是M3 Max实测。
- 只能支持静态场景结构记忆的主要收益，不支持完整动态世界状态持久性。
- 当前README列出训练及依赖自有vace/lora checkpoint的推理入口；未证实权重已可直接下载。

RQ 支持：

- RQ1：显式3D索引可承载latent特征，更新/读取与RGB点云不同。
- RQ2：最近直接检查depth source的相关工作，但不隔离来源关联/选帧中介。
- RQ3：当前代码可浏览；训练或端到端推理没有本机证据。

跨工作关系：

- 项目/论文比较Spatia、Voyager、Gen3C、VMem；代码致谢Spatia。
- 不同于GIM固定隐式state，LSM仍有显式3D坐标和depth-guided读写。

资源边界：官方仓库及训练/推理命令可读；未下载checkpoint、未执行。

### PERSIST · Beyond Pixel Histories: World Models with Persistent 3D State

作者：Samuel Garcin, Thomas Walker, Steven McDonagh, Tim Pearce, Hakan Bilen, Tianyu He, Kaixin Wang, Jiang Bian。

首次公开：2026-03-03；本次主张版本：2603.03482v2（2026-06-03）；发表信息：ICML 2026（作者项目标注）。角色：boundary-complement。

来源：[arXiv 元数据](https://arxiv.org/abs/2603.03482)；[原文](https://arxiv.org/html/2603.03482v2)；[作者/正式资源 1](https://francelico.github.io/persist.github.io/)；[作者/正式资源 2](https://github.com/francelico/PERSIST)。

核验：**VERIFIED**。第一步：初始搜索别名PERSIST后校正为arXiv完整标题，八位作者匹配项目。 第二步：核对模型分解、作者项目实验域和Appendix E限制。

方法签名：随动作演化的3D voxel latent world。写入：world-frame模型预测3D状态演化，camera模型预测相机。 读取：将3D world latents投影给pixel生成模型。 生成器/输出：world/camera/pixel多阶段世界模型。

可用断言：

- 在Minecraft-inspired voxel环境中模拟3D状态，有长期稳定及用户研究证据。（作者项目, Experiments；[原文](https://arxiv.org/html/2603.03482v2)）
- 训练依赖ground-truth 3D监督；作者限制部分明确此条件限制可用数据域。（Appendix E；[原文](https://arxiv.org/html/2603.03482v2)）
- 作者仍报告长时间生成质量衰退，归因为训练真值条件与推理自预测条件的差异。（Appendix E；[原文](https://arxiv.org/html/2603.03482v2)）

条件和局限：

- 体素模拟器及3D监督条件；不能直接迁移为真实单目照片世界生成已解决。
- 完整动态世界state方法不等同于以生成图像估计静态surfel记忆。

RQ 支持：

- RQ1：拓宽记忆表示到主动演化3D状态。
- RQ2：结果有数据域及监督前提，不能归因于单一融合规则。
- RQ3：代码公开；本轮未运行或核验MPS。

跨工作关系：

- 与LSM静态cache形成任务边界对照；不作为本项目直接同设定baseline。

资源边界：作者项目和官方仓库已查；未运行。

### WORLDTRACE · Addressable Memory for Video World Models

作者：Xindi Wu, Sven Elflein, James Lucas, Olga Russakovsky, Laura Leal-Taixé, Despoina Paschalidou, Jonathan Lorraine, Aljoša Ošep。

首次公开：2026-08-07；本次主张版本：2608.07408v1（2026-08-07）；发表信息：arXiv预印本；NVIDIA页称ICML/F2S workshop，未认定ICML主会。角色：boundary-counterexample。

来源：[arXiv 元数据](https://arxiv.org/abs/2608.07408)；[原文](https://arxiv.org/html/2608.07408v1)；[作者/正式资源 1](https://research.nvidia.com/publication/2026-08_addressable-memory-video-world-models)。

核验：**VERIFIED**。第一步：完整标题和八位作者由arXiv及NVIDIA原作者机构页面核对。 第二步：核对Abstract、方法与Appendix H.1；仅用与评测架构相关的机制断言。

方法签名：固定预算KV-cache summaries/landmarks。写入：Field在去RoPE相位空间压缩；Landmark保存检测到的scene-entry痕迹。 读取：给summary槽分配训练范围内的虚拟temporal RoPE位置以恢复attention寻址。 生成器/输出：不重训的autoregressive video backbone。

可用断言：

- 在被测架构中，超过训练范围的temporal RoPE可使已经缓存的内容难以读到；直接平均旋转后keys还会混入不兼容相位。（Abstract, §2–3；[原文](https://arxiv.org/html/2608.07408v1)）
- 模型只改变cache内容/虚拟位置，不修改权重；依赖temporal RoPE和已知local attention window。（Appendix H.1；[原文](https://arxiv.org/html/2608.07408v1)）
- 固定槽数仍有损；Landmark未捕获的场景、超过槽数的旧场景不可保证重访回忆。（Appendix H.1；[原文](https://arxiv.org/html/2608.07408v1)）

条件和局限：

- 针对KV-attention读写；不是对VMem surfel索引错误的实证。
- 作者实测A100 80GB，不能据training-free推断M3可完整运行。
- 这里只证明非几何机制也会造成长期遗忘，不支持所有video model的失败均来自RoPE。
- 另有Closed-Loop标题workshop稿，不与本次arXiv版本混记。

RQ 支持：

- RQ1：记忆失败可能来自读出地址而非几何存储本身。
- RQ2：保留内容与成功读出应分开测，是对几何单因解释的边界反例。
- RQ3：可复核数学/小型cache实验；完整生成未验证本机。

跨工作关系：

- 作为显式几何路线外的反例补充，不占最接近三维记忆方法排名。

资源边界：原论文和机构页可读；未下载代码/权重或执行。

## 实际查询记录

### 2026-09-05 15:56:54 UTC · wide

- 查询：geometry aware world model persistent spatial memory video generation VMem CUT3R 2025 2026
- 查询：world models long term 3D spatial memory camera controlled video 2026
- 查询：VMem consistent interactive video scene generation spatial memory CUT3R

### 2026-09-05 15:57:12 UTC · narrow-title-verification

- 查询："Continuous 3D Perception Model with Persistent State" CUT3R
- 查询："Latent Spatial Memory for Video World Models" Wang
- 查询："Geometry-Aware Implicit Memory for Video World Models"
- 查询："MosaicMem: Hybrid Spatial Memory for Controllable Video World Models"

### 2026-09-05 15:57:29 UTC · narrow-citation-and-recency

- 查询："PERSIST: World Models with Persistent 3D State"
- 查询："Addressable Memory for Video World Models"
- 查询："Video World Models with Long-term Spatial Memory" Spatia
- 查询："VMem" "Gen3C" memory 2026

### 2026-09-05 15:58:02 UTC · claim-verification-fulltext

- 打开：https://arxiv.org/html/2506.18903
- 打开：https://arxiv.org/html/2501.12387
- 打开：https://arxiv.org/html/2506.05284
- 打开：https://arxiv.org/html/2606.09828
- 打开：https://arxiv.org/html/2606.02436
- 打开：https://arxiv.org/html/2603.17117
- 打开：https://arxiv.org/html/2603.03482
- 打开：https://arxiv.org/html/2608.07408

### 2026-09-05 15:58:43 UTC · blindspot-and-falsification

- 查询："Spatia: Video Generation with Updatable Spatial Memory"
- 查询："AnchorWeave: World-Consistent Video Generation with Retrieved Local Spatial Memories"
- 查询："VMem" "geometry" "noise"
- 查询："CUT3R" "persistent" "2026" memory

### 2026-09-05 15:59:11 UTC · claim-verification-fulltext

- 打开：https://arxiv.org/html/2512.15716
- 打开：https://arxiv.org/html/2602.14941

### 2026-09-05 16:05:51 UTC · resource-and-version-check

- 打开：https://arxiv.org/abs/{corpus_ids}
- 打开：https://microsoft.github.io/LatentSpatialMemory/
- 打开：https://spmem.github.io/
- 打开：https://gim-world.github.io/
- 说明：GIM project page web safety error; no bypass attempted. Followed official code/project links for LSM, SPMem, AnchorWeave.

后续聚焦核对（发生在上述完整来源读取窗口内，未为每次 find/open 单独保存秒数）：VMem §4.4 / Appendix C,D；CUT3R Limitations；SPMem §3.2 / §4.4；LSM §5.3 / Table3,4；GIM §3.2–3.5 / §4.1 / Table1–4；MosaicMem §4.2；PERSIST Appendix E；WorldTrace Appendix H.1；AnchorWeave §4.1/4.3 / Appendix A,B,C；Spatia §4.2 / Table4,5,7。arXiv十项标题/作者/版本元数据另通过公开abs页面读取交叉核对；不是新数据库检索。

## 未采用的线索、访问限制和盲点

- 第三方文章、HuggingFace AI摘要、alphaXiv解读、聚合榜单：仅用作发现线索；机制和数值只据原论文/官方作者资源。
- AbdelStark/mosaicmem Rust项目：搜索结果自称synthetic scaffold，非官方实现，不作为真实模型复现证据。
- WorldDirector、FILT3R、TTT3R、Gen3C、Voyager、WorldMem、StarGen、Context-as-Memory：本分支仅作已发现/被引线索，未完成独立两步主张核验，不使用它们的独立技术断言；相邻或评价分支可另核。TTT3R作为AnchorWeave论文声明的上游归属可描述。
- LSM-World搜索索引Mirage名称：保留版本差异；细节及Table3/4来自v2，不混用名称。
- AnchorWeave正文90%与附录80%去噪控制范围：原文不一致，未选择某值作为已定实现。
- GIM项目页：web返回不可安全打开；未绕过。论文全文仍可验证限定主张。
- 未核实权重下载和MPS执行：有代码链接不等于checkpoint可下载、依赖齐全、Apple设备可运行。

- 尚未在所有核心代码中逐行核对paper-to-code差异。
- 尚未对引用图作完整前向/后向计量；只沿实际发现的高相关链条追踪。
- 没有检索到完整四段因果实验不等于这种工作不存在。
- 近期工作多为arXiv预印本，会议身份未核的明确保留未核状态。

不能把“本轮未找到完整几何—关联—选帧—生成因果链”写成“无人研究过”。本证据簿已记录最近工作中的部分消融，以及不能连接到另一层结果的具体理由。

