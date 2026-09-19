# 三维记忆怎样影响世界模型：从几何更新到参考选择的证据边界

## 摘要

相机回到同一个房间，生成画面还能否保留原来的门窗和家具，是三维记忆需要回答的实际问题。本综述围绕几何估计、历史参考选择和生成一致性的关系，合并三个独立检索视角及一组针对性补充，从29项已核验材料中选取25项进行比较。VMem 用粗几何选择历史照片，而 AnchorWeave 将多个局部几何渲染作为生成条件，因此同一种几何偏差可能在两条路径中产生不同影响。[[1]](https://arxiv.org/html/2506.18903v3)[[2]](https://arxiv.org/html/2602.14941v1)经典融合、近期状态更新和评价研究共同提示：应分别测量记忆内容、来源关联、参考选择及生成结果，不能用一个较好的误差数字代替整条链。项目 S6 的同环境组件结果为这种区分提供了局部实例；它尚未形成跨场景或视频生成证据。本综述据此整理已有方法、相互制约的实验条件，以及本机条件下可以继续核查的问题，不宣称已经发现创新空白。

## 1. 同一次回访包含哪些不同问题

“模型记住了房间”至少包含三件事：它估计的空间结构是否接近观察、它能否取回适合当前视角的历史信息、它生成的新画面是否与旧画面相容。CUT3R 主要输出三维点和相机参数，VMem 则利用几何索引选择参考照片并驱动生成；两者的成功标准因此不同。[[3]](https://arxiv.org/html/2501.12387v1)[[1]](https://arxiv.org/html/2506.18903v3)本综述把**来源关联**具体理解为“这个记忆点记录了哪些照片曾看见它”，把**参考支持**理解为“选出的照片能覆盖当前查询中的多少可见内容”。支持充分可能有帮助，但它不是生成画面的质量分数。

研究问题沿用搜索前固定的任务书：

- **RQ1：** 现有方法怎样表示和更新跨帧记忆？几何错误在什么条件下可能影响关联或参考选择，已有证据到哪一层？
- **RQ2：** 几何更准确是否伴随更好的检索与生成一致性？怎样的消融和评价能区分这三种结果？
- **RQ3：** 只有 M3 Max／64GB、没有远程 GPU 时，哪些可复核工作能支撑有边界的研究结果，还缺哪些验证？

下文先区分研究干预的位置，再讨论几何写入、生成条件和评价过程。最后把文献与已完成的 S6 组件实验对照，回答这三个问题。本文中的“可能影响”属于待检验的机制推论；作者论文的结果、项目实测和后续建议分别注明。已有论文摘要中的“首次”“最优”等措辞不直接作为本综述的判断。

## 2. 检索范围、筛选与版本

本轮资料检索发生于北京时间2026-09-05深夜至2026-09-06凌晨。最早有秒级记录的查询为23:56:54；主流分支完成来源读取至00:05:51，融合分支的证据截止为00:08:52，针对性补充在00:15:45记录前完成。评价分支部分后续资源核对没有独立秒级记录，其归档时点为00:28:57。因此，本综述采用**2026-09-06 00:28:57作为资料归档截止上界**，不将它误写为每个查询发生的时刻，也不把中断间隔计作研究工时。串行合成阶段没有新增网络搜索。之后独立引用审查于01:01:21—01:08:23重新访问原始来源，25条存在、两处限定已补清；23篇读取相关全文段落，ElasticFusion与EM-Fusion限官方原文索引摘录，详见[独立引用审查](LITERATURE_SYNTHESIS_V2_CITATION_AUDIT.md)。

三个独立分支分别检索“世界模型×空间记忆”“surfel／TSDF融合×位姿与关联不确定性”“相机可控视频×一致性评价”，均先广搜，再依据命中的方法名和引用网络缩小范围。补充查询涉及 uncertainty、reference view selection、coverage 和 decision stability。经典融合与测量基准向前追溯至2012年，学习几何和世界模型主要覆盖2024—2026年。每项材料先核标题与作者，再核所用主张对应的原文位置；作者项目和官方仓库仅用于核查资源及版本状态。详细查询和链接见[主流证据](literature_v2/MAINSTREAM_EVIDENCE.md)、[融合证据](literature_v2/FUSION_EVIDENCE.md)、[评价证据](literature_v2/EVALUATION_EVIDENCE.md)和[补充证据](literature_v2/TARGETED_EVIDENCE.md)。

四组共有29个不同题名，未发现重复论文；正文纳入25项。DFusion、NeuralFusion因本轮全文访问深度有限且相关论点已有较直接证据，STream3R和MV-DUSt3R+因对本问题的增量较小，留在证据池而不进入正文书目。WorldConsist未确认对应的原始论文，不引用。LSM-World采用2026-08-27的v2，GeCo采用2026-08-19的v5；不混用旧题名、旧摘要或后续可变网站的规模数字。上述范围是一份问题导向的研究综述，并非对所有世界模型、SLAM方法或引用网络的穷尽检索。

## 3. 按干预位置组织证据

本文把每项工作按**主要研究干预的对象**归入一类，而不按“有没有记忆”或“是否显式几何”重复分类。CUT3R 的持续状态服务于几何估计，VMem 的几何索引服务于影像生成，WorldScore 的几何估计则服务于评分；同样出现点图，含义并不相同。[[3]](https://arxiv.org/html/2501.12387v1)[[1]](https://arxiv.org/html/2506.18903v3)[[4]](https://arxiv.org/html/2504.00983v2)这种分类覆盖本次纳入语料的三种角色；跨角色联系在讨论部分单列，不把一篇论文重复算作多项独立证据。

表1：三类工作观察不同输出，任何一类的成功都不能替代另外两类的验证。

| 主要干预对象 | 本文归入的工作 | 能直接观察什么 | 不能自动推出什么 |
|---|---|---|---|
| 用于估计几何的状态或地图 | CUT3R[[3]](https://arxiv.org/html/2501.12387v1)；ElasticFusion[[5]](https://thomaswhelan.ie/Whelan15rss.pdf)；概率surfel融合[[6]](https://openaccess.thecvf.com/content_ICCV_2017_workshops/papers/w35/Park_Probabilistic_Surfel_Fusion_ICCV_2017_paper.pdf)；EM-Fusion[[7]](https://openaccess.thecvf.com/content_ICCV_2019/papers/Strecke_EM-Fusion_Dynamic_Object-Level_SLAM_With_Probabilistic_Data_Association_ICCV_2019_paper.pdf)；BundleFusion[[8]](https://vcai.mpi-inf.mpg.de/projects/MZ/Papers/arXiv2016_BF/paper.pdf)；Spann3R[[9]](https://arxiv.org/html/2408.16061v1)；TTT3R[[10]](https://arxiv.org/html/2509.26645v4)；FILT3R[[11]](https://arxiv.org/html/2603.18493v1) | 深度、地图、位姿、几何写入或关联 | 生成参考选对了、视频质量改善 |
| 用于生成影像的条件或世界状态 | VMem[[1]](https://arxiv.org/html/2506.18903v3)；AnchorWeave[[2]](https://arxiv.org/html/2602.14941v1)；SPMem[[12]](https://arxiv.org/html/2506.05284v1)；Spatia[[13]](https://arxiv.org/html/2512.15716v1)；MosaicMem[[14]](https://arxiv.org/html/2603.17117v1)；GIM-World[[15]](https://arxiv.org/html/2606.02436v1)；LSM-World[[16]](https://arxiv.org/html/2606.09828v2)；PERSIST[[17]](https://arxiv.org/html/2603.03482v2)；WorldTrace[[18]](https://arxiv.org/html/2608.07408v1)；FreeScale[[19]](https://openaccess.thecvf.com/content/CVPR2026/html/Jiang_FreeScale_Scaling_3D_Scenes_via_Certainty-Aware_Free-View_Generation_CVPR_2026_paper.html) | 生成控制、外观、回访与条件设计的效果 | 中间几何误差是唯一原因 |
| 用于独立观察和评价输出的过程 | TUM RGB-D[[20]](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/tools)；WorldScore[[4]](https://arxiv.org/html/2504.00983v2)；MEt3R[[21]](https://arxiv.org/html/2501.06336v2)；GeCo[[22]](https://arxiv.org/html/2512.22274v5)；SysCON3D[[23]](https://arxiv.org/html/2605.18754v1)；WorldRoamBench[[24]](https://arxiv.org/html/2606.31672v1)；WorldExam[[25]](https://arxiv.org/html/2608.02603v1) | 外部测量差异或特定一致性代理 | 指标已覆盖所有失败模式 |

FreeScale主要面向新视角生成与逐场景重建的数据扩增，PERSIST主要面向有三维监督的体素世界；它们被纳入第二类是因为干预生成条件或世界状态，**不是**因为它们与历史照片驱动的导航属于同一评测任务。[[19]](https://openaccess.thecvf.com/content/CVPR2026/html/Jiang_FreeScale_Scaling_3D_Scenes_via_Certainty-Aware_Free-View_Generation_CVPR_2026_paper.html)[[17]](https://arxiv.org/html/2603.03482v2)本表没有用空格宣称研究空白：下文说“未建立某段联系”，只表示本次查到的限定证据尚不能支持该断言。

## 4. 几何写入：平均、关联和坐标修正解决不同错误

经典系统已经把融合与定位一起处理：ElasticFusion维护带权重的surfel并融合观察，BundleFusion则在相机位姿更新后撤销旧融合、重新整合深度；后者解决的是坐标变换变化，不能由“再平均一次”替代。[[5]](https://thomaswhelan.ie/Whelan15rss.pdf)[[8]](https://vcai.mpi-inf.mpg.de/projects/MZ/Papers/arXiv2016_BF/paper.pdf)由此得到的研究推论是，平均能够减小某些重复测量噪声，并不意味着它能纠正把两个不同表面合并、把相机放错位置、或保留错误来源身份的问题。因此，“加入平均更新”本身不足以构成新机制。

关联错误也不等同于深度数值偏差：Park等的概率surfel融合在LiDAR中利用几何及不确定性处理对应，EM-Fusion则估计像素属于对象还是背景的概率，避免动态物体被融合进背景。[[6]](https://openaccess.thecvf.com/content_ICCV_2017_workshops/papers/w35/Park_Probabilistic_Surfel_Fusion_ICCV_2017_paper.pdf)[[7]](https://openaccess.thecvf.com/content_ICCV_2019/papers/Strecke_EM-Fusion_Dynamic_Object-Level_SLAM_With_Probabilistic_Data_Association_ICCV_2019_paper.pdf)二者分别支持“邻域大小和噪声方向会影响匹配”及“错误归属会污染地图”，但LiDAR噪声、合成动态刚体与CUT3R学习点图的误差分布不同。它们提示本项目应分开测位置与来源身份，不能直接提供学习几何误差影响视频的证据。

学习式记忆也已有多种更新方案：Spann3R将几何和视觉特征保存在外部记忆中供重建读取，TTT3R则根据匹配统计调节CUT3R内部token的写入幅度；FILT3R进一步维护token方差，用递推增益混合旧状态和候选状态。[[9]](https://arxiv.org/html/2408.16061v1)[[10]](https://arxiv.org/html/2509.26645v4)[[11]](https://arxiv.org/html/2603.18493v1)这里的token是模型压缩后的特征，不能把其方差直接解释为“这个三维点误差有多少毫米”。TTT3R附录A.2的额外微调变体存在位姿改善而深度变差，不能将此归给冻结权重的主方法，FILT3R也报告固定平均对照与完整方法在整体轨迹误差、局部旋转误差上各有取舍；这些结果要求同时看不同输出，而不是用单个最优数值概括记忆能力。[[10]](https://arxiv.org/html/2509.26645v4)[[11]](https://arxiv.org/html/2603.18493v1)

## 5. 从记忆到生成：索引、投影和潜在状态的不同路径

VMem与AnchorWeave都借助几何找到相关历史，但前者用surfel可见性投票取RGB参考，后者把逐帧局部点云渲染为多个anchor，再由生成网络融合这些条件。[[1]](https://arxiv.org/html/2506.18903v3)[[2]](https://arxiv.org/html/2602.14941v1)因此，VMem中的小位置变化只有在改变可见性、来源集合或排序时才可能传到选帧；AnchorWeave的投影偏差则可直接进入条件图像。这是从方法结构作出的推论，尚不是测得的误差传播曲线。FreeScale已用可靠几何的共享可见性建立certainty-aware view graph，与AnchorWeave的覆盖检索一起说明“几何加置信度选视图”有直接近邻，但它们的任务和选择对象仍需分别比较。[[19]](https://openaccess.thecvf.com/content/CVPR2026/html/Jiang_FreeScale_Scaling_3D_Scenes_via_Certainty-Aware_Free-View_Generation_CVPR_2026_paper.html)[[2]](https://arxiv.org/html/2602.14941v1)

表2：相近方法改变的对象不同，比较前应先固定任务、参考预算和生成器。

| 方法 | 记忆与读出 | 论文中相关消融 | 对本问题的证据边界 |
|---|---|---|---|
| VMem[[1]](https://arxiv.org/html/2506.18903v3) | 粗surfel索引→历史RGB参考 | 时间、相机距离、FOV与surfel检索 | 检索策略比较；未独立改变几何误差幅值 |
| AnchorWeave[[2]](https://arxiv.org/html/2602.14941v1) | 独立局部点云→多个渲染anchor | 全局/局部、条件融合、anchor数 | 全局/局部同时改变单/多anchor |
| Spatia[[13]](https://arxiv.org/html/2512.15716v1) | 静态点云投影＋历史参考帧 | 两种条件的2×2组合、点云密度 | 密度变化不是固定密度的坐标精度变化 |
| GIM-World[[15]](https://arxiv.org/html/2606.02436v1) | 历史压缩为固定memory tokens | 几何监督位置、相同预算历史剪枝 | 几何特征监督不是实测深度精度 |
| LSM-World[[16]](https://arxiv.org/html/2606.09828v2) | 显式3D latent tokens→latent投影 | RGB/latent缓存、深度来源、动态过滤 | 换重建器未同时测真实depth误差 |

SPMem用TSDF融合静态几何，并保留近期帧与稀疏历史帧补运动和细节；Spatia同样结合静态空间条件与历史参考，但对两类条件做了更直接的组合消融。[[12]](https://arxiv.org/html/2506.05284v1)[[13]](https://arxiv.org/html/2512.15716v1)Spatia的Table4中，仅加入参考帧时LPIPS_C由0.379变为0.393，二者联合才降至0.213；这个局部反例提醒我们，参考内容与生成器怎样使用它同样重要。LSM-World把缓存从RGB搬到latent空间，GIM-World则在训练时以几何特征监督隐式记忆、推理时移除几何teacher，进一步说明改进可以发生在条件表示或学习目标上，并非都依靠修正点坐标。[[16]](https://arxiv.org/html/2606.09828v2)[[15]](https://arxiv.org/html/2606.02436v1)

动态场景会改变“应该记住什么”的定义：LSM-World过滤动态对象、明确不跨chunk保存其状态，PERSIST却在有三维监督的体素环境中学习世界状态演化；二者不能按一个长期一致性数字直接排名。[[16]](https://arxiv.org/html/2606.09828v2)[[17]](https://arxiv.org/html/2603.03482v2)MosaicMem尝试用3D patch及不同warping方式兼顾相机和动态表现，其消融出现“相机更准但视觉及记忆指标更差”的取舍；WorldTrace则从另一侧指出，某些模型即使存有历史，也会因temporal RoPE地址超出训练范围而读不到它。[[14]](https://arxiv.org/html/2603.17117v1)[[18]](https://arxiv.org/html/2608.07408v1)前者是条件对齐的取舍，后者是注意力读取的限制，都约束了“长期遗忘主要来自几何存错”这一单因解释。

## 6. 评价：测量真值、共同可见区域和回访控制

TUM RGB-D提供外部动作捕捉轨迹与Kinect深度测量，WorldScore则从生成视频重新估计位姿、深度并计算一致性；前者有独立测量参照，后者衡量生成结果在评测模型下能否自洽。[[20]](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/tools)[[4]](https://arxiv.org/html/2504.00983v2)两者都需要说明尺度、对齐和有效范围。一个生成世界可能与某张参考照片不同但内部相容，反过来，低重投影残差也可能只来自少数易匹配区域。因此，残差必须与共同覆盖、自身覆盖和失败率一起报告，不能把未计分区域默认为正确。

MEt3R通过学习点图对齐图像特征，GeCo则结合光流残余运动与深度结构信息，试图补充共同可见区域和遮挡变化的不同线索；两者测的都不是单图是否好看。[[21]](https://arxiv.org/html/2501.06336v2)[[22]](https://arxiv.org/html/2512.22274v5)SysCON3D对包括神经几何骨干在内的评测环节进行压力测试，发现不合理图像组合也可能得到虚构支持，这限制了仅依赖MEt3R一类学习几何分数的解释。[[23]](https://arxiv.org/html/2605.18754v1)[[21]](https://arxiv.org/html/2501.06336v2)不过，SysCON3D采用的传统重建也会受弱纹理、重复结构及低重叠影响，GeCo对真实动态物体的运动也有误罚风险；合理做法是用已知错位、遮挡及干净图对校验评测器，并记录失败，而不是把另一种估计器提升为无误差真值。[[23]](https://arxiv.org/html/2605.18754v1)[[22]](https://arxiv.org/html/2512.22274v5)

回访比较还要先确认相机真的回来了：WorldRoamBench按从视频估计的观察—回访动作转折分段，再对齐两段估计点云，WorldExam在返回窗口中寻找估计位姿最接近初始视角的帧，再分别报告控制和外观。[[24]](https://arxiv.org/html/2606.31672v1)[[25]](https://arxiv.org/html/2608.02603v1)前者的点云对齐可能吸收一部分整体位姿偏差，后者仍受相机估计和残余视差影响，二者各有代价。与WorldScore对控制、质量、动态分项评分的设计结合看，回访应至少分开“有没有到原位置”“共同区域是否保留”“画面质量如何”；仅按对称帧号或只比较首末图不足以解释失败原因。[[4]](https://arxiv.org/html/2504.00983v2)[[25]](https://arxiv.org/html/2608.02603v1)

表3：根据上述方法整理的评价检查项；这是研究者建议。指标互补，支持代理与生成效果之间仍需要实际生成实验。

| 评价层 | 应固定或同时报告的内容 | 不能省略的边界 |
|---|---|---|
| 深度／位姿 | 测量来源、尺度、对齐、共同mask、覆盖 | 低误差可能只覆盖少量像素 |
| 来源／参考选择 | 候选历史、参考数量、NMS、来源身份、覆盖并集 | 换图不等于选得更好；覆盖不等于语义充分 |
| 生成回访 | 相同初图与控制、实际相机返回、外观与几何分项 | 位置偏差和记忆失败不能混算 |
| 评测器本身 | 干净与受控异常样例、有效支持、失败数量 | 学习几何和传统重建均非无误差裁判 |

## 7. 证据能连接到哪里：与本项目S6对照

综合消融时，最需要保留的是实验实际改变了什么。VMem比较检索规则，AnchorWeave的全局/局部对比却同时从单个全局anchor变成多个局部anchor，不能将后者的PSNR差全部归给几何更准。[[1]](https://arxiv.org/html/2506.18903v3)[[2]](https://arxiv.org/html/2602.14941v1)类似地，Spatia的点云密度消融改变信息量，LSM-World的depth-source消融替换重建器但没有同时报告真实depth误差；后者在三种来源下的WorldScore均值为70.36、69.66、69.13，后两项分别低0.70和1.23分，原表未给统计区间。[[13]](https://arxiv.org/html/2512.15716v1)[[16]](https://arxiv.org/html/2606.09828v2)这些结果允许“生成器能容忍一定几何差异”的解释，却不能建立“误差减少多少，生成质量就增加多少”的函数关系。AnchorWeave中简单平均较差的对象是anchor条件融合，也不能当作surfel坐标平均的直接反证。

S6保留了VMem式历史选帧这一中间层，同时使用CUT3R学习几何，因此它能检查二者衔接后的局部行为，范围仍小于完整VMem生成系统。[[1]](https://arxiv.org/html/2506.18903v3)[[3]](https://arxiv.org/html/2501.12387v1)在已冻结的同一TUM环境、8张测试查询、stride8设置中，平均位置更新相对首写使4/8次查询换图，支持代理由91.907%到93.272%，但最近预测姿态4图为93.472%。共同像素MAE由367.526降至347.882毫米，同时自身覆盖由8.804%降至8.096%，共同区域平均仅占有效目标2.749%。这些数值已由3453项独立检查核对；检查次数不是独立样本数，审查也没有重新运行模型、渲染和NMS全过程。[项目结果](S6_RESULTS.md)；[独立审查](S6_INDEPENDENT_AUDIT.md)。

S6的stride12中支持提高而共同像素MAE变差，与TTT3R额外微调变体、FILT3R固定EMA消融中不同指标可能不同向的现象相容，但这些方法改变的对象和数据条件不同，不能据此断言共同根因。[[10]](https://arxiv.org/html/2509.26645v4)[[11]](https://arxiv.org/html/2603.18493v1)本地变化全部集中于B1，B2不换图，且有一次换图后的支持下降；更新位置还改变后续关联及地图点数，最近姿态对照又没有相同NMS，因此尚未拆开位置、来源和选择规则。可以得到的局部观察是“更新规则会改变参考选择，几何与支持并不总同向”，不能得到“平均更新普遍优越”或“视频已经改善”。[项目逐查询及覆盖结果](S6_RESULTS.md)。

## 8. 本机可做的下一步及尚未回答的问题

第一项可检验工作是把写入与读出分开。Park等的概率surfel融合关心对应关系，VMem关心基于可见表面的历史投票，因此可以在新的预先固定协议中分别考察：保持来源与关联不变时只改位置、固定同一位置规则时更换关联轨迹，以及允许在线关联一起变化的完整更新。跨关联轨迹同时改变点的分区、点数及出生属性，不能称为只改来源；纯来源标签干预需另立固定同一地图身份的设计。[[6]](https://openaccess.thecvf.com/content_ICCV_2017_workshops/papers/w35/Park_Probabilistic_Surfel_Fusion_ICCV_2017_paper.pdf)[[1]](https://arxiv.org/html/2506.18903v3)同一候选池、4帧预算和NMS下，再与最近位姿及均匀历史比较，才更容易识别收益来自哪里。这是依据机制提出的诊断建议，不是已经验证的改进，也未被本次检索确认为无人做过。

第二项工作是扩大独立场景并校验评价。TUM提供可用于本机离线评分的外部测量，SysCON3D说明评测器需要显式失败和异常对照；结合二者，优先级应是另取独立环境、冻结开发／测试划分，并报告低覆盖、遮挡和失败样例，而非增加同一个房间的时间块来抬高样本数。[[20]](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/tools)[[23]](https://arxiv.org/html/2605.18754v1)若借鉴GeCo的人工形变或WorldExam的回访位置选择，应单列为新增诊断，不能修改S6旧协议；人工异常也不能冒充自然生成错误。[[22]](https://arxiv.org/html/2512.22274v5)[[25]](https://arxiv.org/html/2608.02603v1)

第三项工作才是有条件的端到端比较。TTT3R和FILT3R虽然不需要测试时重训模型，仍依赖特定CUT3R权重和运行环境；公开代码不等于当前224 linear检查点或MPS可以直接复现其表格。[[10]](https://arxiv.org/html/2509.26645v4)[[11]](https://arxiv.org/html/2603.18493v1)同样，MEt3R与GeCo的官方环境以CUDA为主，不能把作者GPU计时当作Mac预算。[[21]](https://arxiv.org/html/2501.06336v2)[[22]](https://arxiv.org/html/2512.22274v5)当前可先完成源码、权重接口及小规模成本核查；只有真正得到生成视频后，才按相同初图、相机、种子和参考预算，使用WorldScore的分项思路与WorldRoamBench的实际回访检查评价生成效果。[[4]](https://arxiv.org/html/2504.00983v2)[[24]](https://arxiv.org/html/2606.31672v1)

本轮也存在公开资源边界：SPMem当前已有官方代码，而AnchorWeave在写作时使用其重实现；因此比较对象须跟随版本记录，不能沿用“仍未开源”的旧描述。[[12]](https://arxiv.org/html/2506.05284v1)[[2]](https://arxiv.org/html/2602.14941v1)GIM-World项目页本次未能打开，WorldExam仓库读取时尚未见完整可执行评价实现；论文中的可验证主张与可复现资源是两件事。[[15]](https://arxiv.org/html/2606.02436v1)[[25]](https://arxiv.org/html/2608.02603v1)还有预训练数据是否包含当前TUM序列、动态物体长期状态、严格历史条件下的跨场景生成，都未由本项目或本轮证据解决。

## 9. 对三个研究问题的回答

**RQ1。** 记忆既可以是几何估计状态，也可以是生成参考索引、显式投影条件或潜在世界状态。VMem与AnchorWeave说明，几何进入生成的路径不同，错误需要经过的中间环节也不同；概率surfel融合与EM-Fusion则提供了关联不确定性和错误归属的条件性证据。[[1]](https://arxiv.org/html/2506.18903v3)[[2]](https://arxiv.org/html/2602.14941v1)[[6]](https://openaccess.thecvf.com/content_ICCV_2017_workshops/papers/w35/Park_Probabilistic_Surfel_Fusion_ICCV_2017_paper.pdf)[[7]](https://openaccess.thecvf.com/content_ICCV_2019/papers/Strecke_EM-Fusion_Dynamic_Object-Level_SLAM_With_Probabilistic_Data_Association_ICCV_2019_paper.pdf)对本项目，位置变化可能通过关联、遮挡及排序影响选图，但还不能把某个深度残差归因为唯一原因。

**RQ2。** 现有证据不支持把几何、参考支持与生成一致性视为同一个量。Spatia与LSM-World分别检验条件组合、密度和深度来源，MEt3R与WorldExam又分别观察跨视图相容性和回访执行；它们需要组合使用，并保留各自条件。[[13]](https://arxiv.org/html/2512.15716v1)[[16]](https://arxiv.org/html/2606.09828v2)[[21]](https://arxiv.org/html/2501.06336v2)[[25]](https://arxiv.org/html/2608.02603v1)S6中几何和支持不同向的敏感性结果进一步限制了本地结论，但并未补上视频生成一层。[S6结果与边界](S6_RESULTS.md)。

**RQ3。** 本机已经能够支持真实模型输出后的地图、支持和测量复算；继续工作的可审查价值，应来自可重现的机制诊断和明确的适用边界。TTT3R与FILT3R使泛称“置信度写入”面临已有近邻，AnchorWeave与FreeScale也使泛称“可靠几何检索”不足以确立新颖性。[[10]](https://arxiv.org/html/2509.26645v4)[[11]](https://arxiv.org/html/2603.18493v1)[[2]](https://arxiv.org/html/2602.14941v1)[[19]](https://openaccess.thecvf.com/content/CVPR2026/html/Jiang_FreeScale_Scaling_3D_Scenes_via_Certainty-Aware_Free-View_Generation_CVPR_2026_paper.html)新的研究主张仍需固定因素对照、独立场景和实际生成验证；本次综述提供的是这张证据关系图及其限制，而非创新性结论。

## 参考文献

[1] Runjia Li, Philip Torr, Andrea Vedaldi, et al., "VMem: Consistent Interactive Video Scene Generation with Surfel-Indexed View Memory," ICCV, 2025.

[2] Zun Wang, Han Lin, Jaehong Yoon, et al., "AnchorWeave: World-Consistent Video Generation with Retrieved Local Spatial Memories," arXiv:2602.14941v1, 2026.

[3] Qianqian Wang, Yifei Zhang, Aleksander Holynski, et al., "Continuous 3D Perception Model with Persistent State," CVPR, 2025.

[4] Haoyi Duan, Hong-Xing Yu, Sirui Chen, et al., "WorldScore: A Unified Evaluation Benchmark for World Generation," ICCV, 2025.

[5] Thomas Whelan, Stefan Leutenegger, Renato F. Salas-Moreno, et al., "ElasticFusion: Dense SLAM Without A Pose Graph," Robotics: Science and Systems, 2015.

[6] Chanoh Park, Soohwan Kim, Peyman Moghadam, et al., "Probabilistic Surfel Fusion for Dense LiDAR Mapping," ICCV Workshops, 2017.

[7] Michael Strecke, Jörg Stückler, "EM-Fusion: Dynamic Object-Level SLAM With Probabilistic Data Association," ICCV, 2019.

[8] Angela Dai, Matthias Nießner, Michael Zollhöfer, et al., "BundleFusion: Real-Time Globally Consistent 3D Reconstruction Using On-the-Fly Surface Reintegration," ACM Transactions on Graphics, 36(3), Article 24, 2017.

[9] Hengyi Wang, Lourdes Agapito, "3D Reconstruction with Spatial Memory," 3DV, 2025.

[10] Xingyu Chen, Yue Chen, Yuliang Xiu, et al., "TTT3R: 3D Reconstruction as Test-Time Training," ICLR, 2026.

[11] Seonghyun Jin, Jong Chul Ye, "FILT3R: Latent State Adaptive Kalman Filter for Streaming 3D Reconstruction," arXiv:2603.18493v1, 2026.

[12] Tong Wu, Shuai Yang, Ryan Po, et al., "Video World Models with Long-term Spatial Memory," NeurIPS, 2025.

[13] Jinjing Zhao, Fangyun Wei, Zhening Liu, et al., "Spatia: Video Generation with Updatable Spatial Memory," CVPR, 2026.

[14] Wei Yu, Runjia Qian, Yumeng Li, et al., "MosaicMem: Hybrid Spatial Memory for Controllable Video World Models," arXiv:2603.17117v1, 2026.

[15] Zhengxuan Wei, Xu Guo, Xinghui Li, et al., "Geometry-Aware Implicit Memory for Video World Models," arXiv:2606.02436v1, 2026.

[16] Weijie Wang, Haoyu Zhao, Yifan Yang, et al., "Latent Spatial Memory for Video World Models," arXiv:2606.09828v2, 2026.

[17] Samuel Garcin, Thomas Walker, Steven McDonagh, et al., "Beyond Pixel Histories: World Models with Persistent 3D State," arXiv:2603.03482v2, 2026.

[18] Xindi Wu, Sven Elflein, James Lucas, et al., "Addressable Memory for Video World Models," arXiv:2608.07408v1, 2026.

[19] Chenhan Jiang, Yu Chen, Qingwen Zhang, et al., "FreeScale: Scaling 3D Scenes via Certainty-Aware Free-View Generation," CVPR, 2026.

[20] Jürgen Sturm, Nikolas Engelhard, Felix Endres, et al., "A Benchmark for the Evaluation of RGB-D SLAM Systems," IROS, 2012.

[21] Mohammad Asim, Christopher Wewer, Thomas Wimmer, et al., "MEt3R: Measuring Multi-View Consistency in Generated Images," CVPR, 2025.

[22] Leslie Gu, Junhwa Hur, Charles Herrmann, et al., "GeCo: Evaluating Geometric Consistency for Video Generation via Motion and Structure," arXiv:2512.22274v5, 2026.

[23] Soumava Paul, Prakhar Kaushik, Alan Yuille, "Can These Views Be One Scene? Evaluating Multiview 3D Consistency when 3D Foundation Models Hallucinate," arXiv:2605.18754v1, 2026.

[24] Ting-Bing Xu, Jiacheng Sui, Zhe Gao, et al., "WorldRoamBench: An Open-World Benchmark for Long-Horizon Stability of Interactive World Models," arXiv:2606.31672v1, 2026.

[25] Yuxue Yang, Shuyao Shang, Jiahe Wang, et al., "WorldExam: Benchmarking World Models from Apparent Appearance to Inherent Reactivity," arXiv:2608.02603v1, 2026.


