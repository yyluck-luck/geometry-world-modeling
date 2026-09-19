# 融合视角证据台账（第二轮，供父任务综合）

证据汇整时点：2026-09-06 00:08:52 +08:00；最终写入/核查：2026-09-06T00:17:14.963804+08:00。检索始于23:56:55，跨午夜继续。完整实际查询、访问边界、书目与机器可读条目见 [FUSION_EVIDENCE.json](FUSION_EVIDENCE.json)。这是文献证据采集，不是综述正文，也不是本地复现。

## 范围与核验

已读项目AGENTS、记忆、最新日志、固定任务书和deep-research技能及检索/引用规范。先独立广搜，再按首轮方法名窄搜；父任务提示后补查TTT3R/FILT3R。8项核心、2项补充。每项分别核对完整标题/作者与原文主张，均以作者论文、官方论文库或项目为依据；没有凭未检到而宣称不存在。未读取S6指标、未改实验协议或主记忆。

## 逐项证据

### F01 · ElasticFusion: Dense SLAM Without A Pose Graph

**Thomas Whelan; Stefan Leutenegger; Renato F. Salas-Moreno; Ben Glocker; Andrew J. Davison · 2015 · Robotics: Science and Systems (RSS) · VERIFIED**

存在核验：[书目/作者页](https://thomaswhelan.ie/)。主张核验：[原文](https://thomaswhelan.ie/Whelan15rss.pdf)，定位 §III; §IV–VI; §VII。读取深度：作者PDF下载成功并抽取全文。

- 方法签名：RGB-D → 带位置/法向/颜色/权重/半径的surfels；活动/非活动窗口；frame-to-model配准；局部和全局回环触发非刚性地图变形。
- 可用发现：经典surfels已维护权重并采用移动平均融合；简单均值不是新机制。 融合并非孤立动作，系统同步处理配准、回环和模型形变。
- 条件：房间尺度RGB-D密集SLAM；实验评价重建和轨迹。
- 局限：本证据不能证明平均能修复错误关联，也不支持任何生成质量或历史选帧结论。RSS版与2016 IJRR扩展版须分开。
- 跨工作关系：ElasticFusion调整surfel地图，BundleFusion修正位姿后撤销并重融合TSDF。
- 对项目的推论：若仅比较first-write与frame_mean，应标为既有融合思想的组件诊断；不能称置信度、过滤或回环从未存在。

### F02 · Probabilistic Surfel Fusion for Dense LiDAR Mapping

**Chanoh Park; Soohwan Kim; Peyman Moghadam; Clinton Fookes; Sridha Sridharan · 2017 · ICCV Workshops · VERIFIED**

存在核验：[书目/作者页](https://openaccess.thecvf.com/content_ICCV_2017_workshops/w35/html/Park_Probabilistic_Surfel_Fusion_ICCV_2017_paper.html)。主张核验：[原文](https://openaccess.thecvf.com/content_ICCV_2017_workshops/papers/w35/Park_Probabilistic_Surfel_Fusion_ICCV_2017_paper.pdf)，定位 §3.2; §4, Fig.3; §4.1–4.3; §5。读取深度：CVF PDF下载并读取方法全文。

- 方法签名：稀疏ellipsoid地图做ICP定位，稠密disk地图做融合；位置/法向不确定性；octree候选后用几何/不确定性对应，再Bayesian更新。
- 可用发现：球形搜索半径过小会漏匹配，过大则降低表面分辨率。 入射角、距离和邻域退化使位置及法向噪声具有方向性。
- 条件：有扫描线结构的LiDAR；模拟与真实数据；估计位姿后融合。
- 局限：LiDAR噪声模型不能直接当作CUT3R误差分布；文中位置协方差主要为测量噪声变换，不能说其完整传播任意相机位姿后验。
- 跨工作关系：Park处理surfel对应与分辨率，EM-Fusion处理像素到不同对象/背景的软关联。
- 对项目的推论：同一像素格/搜索球内的两个点不能由接近程度本身 断言属于同一物理表面；此处是研究推论，需本地边界/遮挡分组验证。

### F03 · EM-Fusion: Dynamic Object-Level SLAM With Probabilistic Data Association

**Michael Strecke; Jörg Stückler · 2019 · ICCV · VERIFIED**

存在核验：[书目/作者页](https://emfusion.is.tue.mpg.de/)。主张核验：[原文](https://openaccess.thecvf.com/content_ICCV_2019/papers/Strecke_EM-Fusion_Dynamic_Object-Level_SLAM_With_Probabilistic_Data_Association_ICCV_2019_paper.pdf)，定位 Fig.1; §3.1–3.3; Fig.3; §4 Table3。读取深度：CVF PDF下载成功，读取方法、消融、失败条件。

- 方法签名：对象/背景各自TSDF；EM估计像素所属对象概率；关联概率进入直接SDF配准与地图融合权重；实例分割初始化对象。
- 可用发现：去除关联概率时，动态物体深度可错误写进背景，形成轨迹伪影（Fig.1）。 Room4消融对大部分对象影响较小，rocking Horse的AT-RMSE为9.12cm（无关联）与3.57cm（完整方法），不能称对所有对象均大幅改善。
- 条件：动态刚体对象RGB-D SLAM；Room4消融为合成场景。
- 局限：大面积未检测物体仍可能导致失败；对象探测/分割是条件；不是静态学习点图或视频生成实验。
- 跨工作关系：在均值/加权更新前先解决关联；方法不同，不能只比较融合后误差。
- 对项目的推论：最有力的反例是错误表面归属会污染地图；项目目前需要独立测量表面/来源关联，不能从深度MAE自动推断。

### F04 · DFusion: Denoised TSDF Fusion of Multiple Depth Maps with Sensor Pose Noises

**Zhaofeng Niu; Yuichiro Fujimoto; Masayuki Kanbara; Taishi Sawabe; Hirokazu Kato · 2022 · Sensors 22(4):1631 · VERIFIED**

存在核验：[书目/作者页](https://pubmed.ncbi.nlm.nih.gov/35214532/)。主张核验：[原文](https://pmc.ncbi.nlm.nih.gov/articles/PMC8879644/)，定位 Abstract; §1 Fig.1; fusion/denoising method description。读取深度：原文索引返回长段方法内容；直接PMC访问遇到验证页/SSL失败，未完成本地全文下载。

- 方法签名：带位姿的depth先经RoutedFusion式模块形成TSDF，再用3D U-Net式模块去噪；训练同时加入深度与位姿扰动。
- 可用发现：融合中位姿旋转/平移误差是区别于深度噪声的误差源。 已有学习方法专门尝试同时抑制两类噪声；不能宣称此前只关注深度。
- 条件：有GT深度/位姿的合成监督及真实场景测试；声明限于本次实际可读的原文方法/摘要。
- 局限：不沿用作者的first/earliest新颖性措辞；未核本次不可读的具体表格数值；不能等同恢复正确位姿或正确来源身份。
- 跨工作关系：DFusion在融合体上学习去噪，BundleFusion直接重新估计位姿并撤销旧融合。
- 对项目的推论：至少把深度误差、相机变换误差、错误匹配分成不同干预，否则归因不清。

### F05 · BundleFusion: Real-Time Globally Consistent 3D Reconstruction Using On-the-Fly Surface Reintegration

**Angela Dai; Matthias Nießner; Michael Zollhöfer; Shahram Izadi; Christian Theobalt · 2017 · ACM Transactions on Graphics 36(3), Article 24 · VERIFIED**

存在核验：[书目/作者页](https://graphics.stanford.edu/projects/bundlefusion/)。主张核验：[原文](https://vcai.mpi-inf.mpg.de/projects/MZ/Papers/arXiv2016_BF/paper.pdf)，定位 Abstract; system overview; §4 Global Pose Alignment; surface reintegration。读取深度：作者项目+论文原文索引核验；非本地运行。

- 方法签名：全历史稀疏/稠密对应优化相机位姿；RGB-D帧在旧位姿de-integrate，再按更新位姿re-integrate到体积。
- 可用发现：持续重估位姿可以与撤销旧融合配合，而不是仅在当前位置多平均一次。
- 条件：同步标定RGB-D流；面向扫描、重建和跟踪；作者项目提供场景数据及校准。
- 局限：本项目未运行该系统；其生成地图/轨迹指标不能替代来源选帧或生成质量。
- 跨工作关系：与ElasticFusion的地图形变代表两种不同的一致性修正手段。
- 对项目的推论：如果根因在位姿，位置平均未必够；可先做冻结预测pose/替代pose的诊断，而非直接发明复杂gate。

### F06 · 3D Reconstruction with Spatial Memory

**Hengyi Wang; Lourdes Agapito · 2025 · 3DV 2025 · VERIFIED**

存在核验：[书目/作者页](https://arxiv.org/abs/2408.16061)。主张核验：[原文](https://arxiv.org/html/2408.16061)，定位 §3; §4.3 Table3/Fig.6; §4.4; appendix Table4。读取深度：arXiv HTML全文方法/消融/局限；官方release notes核版本。

- 方法签名：DUSt3R系图像编码/双decoder；外部working+long-term spatial memory；融合几何与视觉特征供后续pointmap读出；attention clipping。
- 可用发现：Table3检验长期记忆及attention clipping；小attention权重遇到几何离群值仍可能干扰读出。 持续向前、多房间、闭环时可能失败；§4.4建议更结构化记忆或BA校正几何后写回。 附录Table4比较offline重建的view-selection置信度函数。
- 条件：论文版主要5帧224训练；官方2025-02-25 v1.01另以10帧/15数据集训练，不能将版本数字混用。
- 局限：选view用于重建过程，不能当作生成模型历史参考检索；长期记忆有益也不等于不再漂移。
- 跨工作关系：Spann3R改外部feature memory；TTT3R改CUT3R内部recurrent state写入幅度。
- 对项目的推论：已有几何参与记忆检索和写回思想；差异须落实到显式点-来源关联与下游参考选择的可测机制。

### F07 · TTT3R: 3D Reconstruction as Test-Time Training

**Xingyu Chen; Yue Chen; Yuliang Xiu; Andreas Geiger; Anpei Chen · 2026 · ICLR 2026 · VERIFIED**

存在核验：[书目/作者页](https://arxiv.org/abs/2509.26645)。主张核验：[原文](https://arxiv.org/html/2509.26645)，定位 §3.3 Eq.7–8; §4; §5; Appendix A.1–A.3。读取深度：原文HTML与官方项目/代码元数据；已读方法/评测/局限/附录消融。

- 方法签名：冻结CUT3R，用state-query/image-key匹配统计的sigmoid导出每token更新率；前向时控制候选state与旧state的混合，无测试时模型参数微调。
- 可用发现：置信度引导的CUT3R状态更新已有非常直接的先例。 作者明确仅缓解遗忘；附录微调改善pose却降低depth，单个指标进步不可推广。
- 条件：主要为公开CUT3R 512 DPT 4–64-view权重；长序列depth/pose/reconstruction；官方安装CUDA；重置变体必须单独标注。
- 局限：是潜在token更新，不是外部Octree点位置更新；未提供历史生成参考检索与视频质量证据；本机224 linear结果不可直接对齐其表格。
- 跨工作关系：FILT3R把即时attention gate改为递推不确定性控制的Kalman式增益。
- 对项目的推论：若下一步提GeoTrust式写入gate，必须先与此training-free baseline比较；当前S6不构成该比较。

### F08 · FILT3R: Latent State Adaptive Kalman Filter for Streaming 3D Reconstruction

**Seonghyun Jin; Jong Chul Ye · 2026 · arXiv:2603.18493v1（2026-03-19）；作者项目标ECCV2026，本轮未独立核会议录 · VERIFIED**

存在核验：[书目/作者页](https://arxiv.org/abs/2603.18493)。主张核验：[原文](https://arxiv.org/html/2603.18493v1)，定位 §3 Eq.3–10; §4.1; §4.8(iii); Appendix A.2/C。读取深度：arXiv v1全文方法/协议/消融/适用边界。

- 方法签名：冻结CUT3R候选state；每token保留一个方差，固定标量measurement noise；候选token时变差经EMA归一化生成process noise；Kalman式gain决定混合并递推方差。
- 可用发现：同backbone、只改在线update；增加固定EMA、reset、固定Q、无方差递推等消融。 TUM-800固定EMA可有更低ATEorig（0.078 vs 0.107），却更差RPE-r（0.658 vs 0.362）；不得称其所有指标均最好。
- 条件：cut3r_512_dpt_4_64.pth；长前缀数百至1000帧；开发集选超参数后跨任务冻结；Appendix C列scale/alignment规则。
- 局限：不确定性是token空间近似，非校准的物理点/pose误差概率；实际q_min/gain clamp形成非零gain下限，不能套用理想q=0时1/t衰减称永不遗忘；候选state本身含历史，不能把原CUT3R简单说成只记一帧。
- 跨工作关系：同属冻结backbone的潜在state更新；较TTT3R显式传播token方差。
- 对项目的推论：置信度/不确定性加权记忆属于已有近邻；可探索来源身份与选帧的额外因果问题，但其差异不是已被证明的新颖性。

## 补充证据

### B01 · NeuralFusion: Online Depth Fusion in Latent Space

Silvan Weder; Johannes L. Schönberger; Marc Pollefeys; Martin R. Oswald，2021，CVPR。核验 **VERIFIED**：[存在](https://openaccess.thecvf.com/content/CVPR2021/html/Weder_NeuralFusion_Online_Depth_Fusion_in_Latent_Space_CVPR_2021_paper.html)、[原文](https://openaccess.thecvf.com/content/CVPR2021/papers/Weder_NeuralFusion_Online_Depth_Fusion_in_Latent_Space_CVPR_2021_paper.pdf)（Abstract; §1）。先在latent feature volume融合，translator转为可显示TSDF；有已知相机标定。 TSDF平均是传统常用技术；离群值和薄几何存在困难；预过滤面临accuracy/completeness权衡。 只据已读原文支持方法与噪声/outlier范围；不声称已核位姿噪声消融。 纳入补充原因：与DFusion互补，但当前最接近问题的8项核心优先保留两项2026状态更新论文。

### B02 · STream3R: Scalable Sequential 3D Reconstruction with Causal Transformer

Yushi Lan; Yihang Luo; Fangzhou Hong; Shangchen Zhou; Honghua Chen; Zhaoyang Lyu; Shuai Yang; Bo Dai; Chen Change Loy; Xingang Pan，2026，ICLR 2026（作者项目）；本次读取arXiv v1 2025-08-14。核验 **VERIFIED**：[存在](https://arxiv.org/abs/2508.10893)、[原文](https://arxiv.org/html/2508.10893)（§4.2; §5; §6）。causal transformer + 历史KV cache，输出世界/相机pointmaps和pose。 不同于固定大小recurrent state，其保存过去特征供因果注意力使用。 §6自己承认error accumulation/drifting及deterministic regression限制。 不能说causal attention消除漂移；本文重建/NVS提法不能当作漫游视频生成历史检索实证。 纳入补充原因：用于架构覆盖与防止最新工作只报优点；F07/F08更直接贴近写入规则。

## 已得到的反证与待补链条

- 数学边界（研究者推论）：平均只有在被合并样本代表同一目标且偏差结构合适时才可望减噪；它不能由代数形式保证纠正错误表面身份、系统性pose偏差或历史来源集合。
- 证据分层：F01–F05主要到几何/跟踪；F06含重建用view selection；F07–F08到depth/pose/reconstruction。均不能填补本项目'来源关联→生成参考选帧→视频质量'证据链。
- 反向检验：滤波过强可能压低全局轨迹误差同时伤害局部运动；应同时报告accuracy/completeness、局部/全局pose和覆盖，不能挑一个较好数值。
- 后续建议不是实验结论：若本地资源有限，先审查公开training-free更新源码与本地checkpoint接口差异，再预注册适配运行；不自动下载新模型或重跑本次冻结S6。

## 检索、访问与排除记录

- **1，2026-09-05T15:56:55Z**：`surfel TSDF fusion uncertain camera poses data association failure probabilistic fusion`；`learned online 3D reconstruction memory fusion Spann3R uncertainty 2025 2026`；`ElasticFusion RoutedFusion NeuralFusion weighted average depth fusion errors`。发现经典概率融合、EM-Fusion、DFusion、Spann3R及STream3R；二手博客仅作线索。
- **2，2026-09-05T15:57:18Z**：`"ElasticFusion: Dense SLAM Without A Pose Graph" Whelan fusion weighted average`；`"NeuralFusion: Online Depth Fusion in Latent Space" Weder`；`"DFusion: Denoised TSDF Fusion of Multiple Depth Maps with Sensor Pose Noises"`；`"BundleFusion: Real-time Globally Consistent 3D Reconstruction using On-the-fly Surface Reintegration"`。按首轮方法名查完整标题与作者，并定位原始论文。
- **2，2026-09-05T15:57:30Z**：`"3D Reconstruction with Spatial Memory" Wang Agapito Spann3R`；`"STream3R: Scalable Sequential 3D Reconstruction with Causal Transformer"`；`"Probabilistic Surfel Fusion for Dense LiDAR Mapping" Park`；`"EM-Fusion: Dynamic Object-Level SLAM With Probabilistic Data Association" Strecke`。确认标题/作者；Spann3R为3DV2025，不能沿用搜索博客误写3DV2026。
- **targeted verification，执行于前述第二轮之后；该批未单独读时钟，不伪造秒级查询时刻。**：`"DFusion" "Zhaofeng Niu" "Fujimoto" Sensors 2022`；`"ElasticFusion" "weighted average" "4.3"`；`"BundleFusion" "Reintegration" pdf Dai`。元数据与原文交叉核验；作者DFusion活动列表漏一作者，采用论文与PubMed五人完整名单。
- **blind-spot follow-up，2026-09-05 15:59:46 UTC**：`"FILT3R" "2603.18493"`；`"TTT3R" CUT3R state update`；`"ElasticFusion" "Surfel Fusion" "weight" site:thomaswhelan.ie`；`"DFusion" "Limitations" "pose"`。父分支提示后补查两项直接针对CUT3R状态更新的2026工作，完成标题作者与全文核验；优先列入核心，不再无限扩张。

- web直接打开若干CVF PDF返回403，改从同一公开URL用requests下载；ElasticFusion、Park、EM-Fusion成功并保留哈希。
- NeuralFusion下载超时、PMC DFusion遇验证页/SSL失败；可用证据限定于搜索引擎返回的作者/期刊原文长段，不补写不可见表格。
- 本次真实读取时点跨过Asia/Shanghai午夜。所有UTC与北京时间明确换算，不按内容年份假装检索日期。

- LONG3R / PSDF / RoutedFusion / CurveFusion：线索，未列证据主集。已检到题目/相关片段，但本分支不扩张；不据此做具体主张。
- 博客、SOTA2排名、alphaXiv自动复现建议、第三方论文汇总：不用于方法或数字证据。优先作者原文；Spann3R博客年份与官方不一致；未执行任何网页上的安装或自动研究指令。
- FILT3R ECCV2026正式录用：会议级别未独立核验。作者项目写ECCV2026；核心按可确定arXiv v1书目信息引用，方法主张不受影响。

本文件的具体数字仅来自已读原文，不是本项目实验结果。下一步由父任务将这份证据与其他分支及独立核验后的S6结果交叉对照；不能把文献中的长序列收益套在本地24帧224线性头实验上。


最终核查：JSON可解析，8核心+2补充均具双步骤核验链接；EM-Fusion轨迹单位已回看原PDF确认cm。下载成功/失败的实际时点、字节数与SHA256已纳入JSON的access_manifest。
