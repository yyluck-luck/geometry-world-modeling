# 综述 V2 独立引用审查

审查对象：`docs/LITERATURE_SYNTHESIS_V2.md`，SHA256 `9ea14026624575d994209a2f43eda7032c68cc5ee4b96510783319aba9cde75d`。

网络核验起止：**2026-09-06 01:01:21—01:08:23（Asia/Shanghai）**，来自实际读钟。项目文件阅读早于第一次读钟，未补造开始秒数；该区间不计作学生学习工时。遵循 [citation-protocol.md](../vendor/research_skill_reference/citation-protocol.md)。审查者使用独立上下文，先核题名/作者，再读原始来源中被引用的内容；此前四组证据只作线索，不以其 VERIFIED 标签作证明。未调用 Claude 模型。

## 结论和范围

**25/25 条确认存在；23 条所用主张通过，2 条 MINOR，需补清限定。未发现虚构文献、数字抄错或 MAJOR 误引。** 两处必须修改为：TTT3R 的负向例子来自“额外微调变体”；WorldRoamBench 的分段依据是“从视频估计的动作转折”。具体替换见下文。此结论仅覆盖综述用到的主张，不证明原论文结果已经复现。

成功打开23篇的全文载体，并阅读其引用对应段落/表格；**这不等于通读23篇所有内容**。ElasticFusion与EM-Fusion直接全文打开失败，已把访问深度降为**官方原文索引摘录**：相关方法段落足以支持本文概述，故主张等级仍是有限范围的VERIFIED；不能说这两篇已经独立全文审查。PAYWALL按协议指存在但只有不足以支持主张的元数据；这里拿到了所用方法段落，且失败不一定是付费墙。

没有重新审查29项池中被排除的4项、证明检索穷尽性、重建旧查询时点、复算S6或运行公开仓库。本次新增的是引用复核，不增加综述语料或改动实验。综述原00:28:57语料归档上界保留；应另记本次01:01—01:08的审查时间，不能把独立复核写成“没有新增网络访问”。

## 逐条核验

表中原文定位是已实际读到的章节/表；作者顺序与题名已逐条核对。完整题名、被引用作者、版本和主源见配套JSON。

| 编号 | 文献／实际读取版本 | 主张等级 | 已核对的用途与边界 |
|---|---|---|---|
| 1 | [VMem](https://arxiv.org/html/2506.18903v3)；2506.18903v3，2025-08-14；ICCV 2025 | VERIFIED | **§3.1、§4.4 Table 4**。surfel保存看见它的历史帧索引，目标视角可见性投票与NMS选择RGB参考；Table 4确实对比时间、相机距离、FOV和surfel规则。 仅验证方法与检索规则消融；小坐标改变何时传到选帧是综述标明的结构推论。 |
| 2 | [AnchorWeave](https://arxiv.org/html/2602.14941v1)；2602.14941v1，2026-02-16 | VERIFIED | **§3.2–3.4；§4.3 Table 2、Figure 5；Table 1脚注**。逐帧局部点云、贪心新增覆盖检索和多anchor条件成立。全局设置使用单anchor，局部设置使用多anchor；简单平均消融发生在anchor条件融合。 Table 2不能独立归因几何精度；其SPMem重实现是写作时资源状态。 |
| 3 | [CUT3R](https://arxiv.org/html/2501.12387v1)；2501.12387v1，2025-01-21；CVPR 2025 | VERIFIED | **§3.1–3.4**。持续token状态输出self/world点图和相机pose；raymap可只读查询。分阶段224/512训练有明确说明。 综述没有把本地224 linear冒充论文512 DPT系统；实际实验正确性不在本审查范围。 |
| 4 | [WorldScore](https://arxiv.org/html/2504.00983v2)；2504.00983v2，2025-11-29；ICCV 2025 | VERIFIED | **§3.3；Appendix C.1–C.3**。控制、质量、动态分项成立；DROID-SLAM估计相机与depth，3D一致性比较共可见像素重投影。 输入相机轨迹是控制目标；生成内容没有外部场景3D真值，不能把自洽评分当测量精度。 |
| 5 | [ElasticFusion](https://www.roboticsproceedings.org/rss11/p01.html)；RSS 2015 原论文 | VERIFIED；仅官方摘录 | **§III 原论文官方索引摘录；RSS会议记录**。官方摘录明确surfel含位置、法向、颜色、权重、半径和时间；采用已有surfel初始化/深度融合规则，颜色沿相同移动平均方案，联合frame-to-model跟踪。 直接PDF打开失败，访问深度降为官方原文索引的相关段落；未独立通读其全文或核全部实验。当前综述所用概述有直接摘录支持。 |
| 6 | [概率surfel融合](https://arxiv.org/pdf/1709.01265)；arXiv:1709.01265 PDF；ICCV Workshops 2017 | VERIFIED | **§4.1–4.3，Figure 5，Algorithm 1**。PDF确认LiDAR位置/法向不确定性；octree候选后分别用表面距离和沿法向标准化距离匹配，噪声方向影响可接受匹配。 不是CUT3R误差模型，也不是生成结果。CVF PDF 403后arXiv PDF首次打开成功，后续重复请求超时不抹去已读取内容。 |
| 7 | [EM-Fusion](https://openaccess.thecvf.com/content_ICCV_2019/papers/Strecke_EM-Fusion_Dynamic_Object-Level_SLAM_With_Probabilistic_Data_Association_ICCV_2019_paper.pdf)；ICCV 2019；arXiv:1904.11781元数据 | VERIFIED；仅官方摘录 | **Figure 1；§3 原论文官方索引摘录；作者项目搜索结果**。原始Figure 1说明像素对对象/背景的关联概率进入E/M步骤，去除关联概率产生错误写入地图的伪影。 CVF PDF 403、arXiv PDF超时、项目直开错误；访问深度降为官方原文索引摘录及作者元数据。没有借此前分支标签声称独立读取完整消融表。 |
| 8 | [BundleFusion](https://vcai.mpi-inf.mpg.de/projects/MZ/Papers/arXiv2016_BF/paper.pdf)；ACM TOG 36(3), Article 24，2017 | VERIFIED | **作者托管PDF首页、§3与§5**。作者、刊物和年份匹配。全局位姿优化之后，在旧pose撤销RGB-D融合并在新pose重新融合，文本明确。 重建/定位系统，不是视频记忆检索；再融合与当前位置均值的区别属于有依据的方法比较。 |
| 9 | [Spann3R](https://arxiv.org/html/2408.16061)；2408.16061v1，2024-08-28；3DV 2025 | VERIFIED | **§3.1–3.2；作者官方仓库**。memory key/value编码已预测点图和几何/视觉特征，外部记忆供后续几何读出，综述用途匹配。 原文链接未写版本，当前解析到v1；建议显式固定v1，官方2025检查点更新不是同一训练版本。 |
| 10 | [TTT3R](https://arxiv.org/html/2509.26645)；2509.26645v4，2026-03-03；ICLR 2026 | MINOR | **§3.3；Appendix A.2；官方README**。主方法根据对齐匹配置信度调整CUT3R token写入，冻结权重；附录A.2明确额外微调使pose变好而video-depth变差。官方README采用512 DPT 4–64权重/CUDA。 §4未说明负向例子来自额外微调，邻近training-free描述容易产生误读；须补“额外微调变体”。同时固定实际读取v4。 |
| 11 | [FILT3R](https://arxiv.org/html/2603.18493v1)；2603.18493v1，2026-03-19 | VERIFIED | **§3 Eq.5；§4.8(iii)；Appendix A.3 Table 7；Appendix C**。per-token方差与Kalman式增益成立。固定EMAβ=0.05的TUM-800 ATE 0.049低于full 0.057，但RPE-r 0.658高于0.362；depth AbsRel 0.093高于0.089。 是latent近似方差，非毫米误差。该固定EMA与完整方法确有多指标取舍，未支持普遍优越。 |
| 12 | [SPMem](https://arxiv.org/html/2506.05284v1)；2506.05284v1，2025-06-05；NeurIPS 2025 | VERIFIED | **§3.2 Eq.2；官方项目及spmem/spmem仓库**。TSDF静态融合、近期working frames及稀疏episodic frames均有原文支持；官方仓库当前含infer.py、infer_stream.py、models和tsdf。 仅确认代码公开与结构，未运行或证明Mac可用。仓库BibTeX year写2026但会议标NeurIPS 2025，原会议出版源确认2025，不混改。 |
| 13 | [Spatia](https://arxiv.org/html/2512.15716v1)；2512.15716v1，2025-12-17；CVPR 2026 | VERIFIED | **§3；§4.2 Tables 4–7**。Table 4四行分别为两条件皆无、仅投影、仅参考、联合；LPIPS_C=0.379、0.295、0.393、0.213。综述三处数字和方向均准确。 是在WorldScore子集的闭环协议；参考单独增加使一个指标变差不是所有指标均退化，正文已限定LPIPS_C。 |
| 14 | [MosaicMem](https://arxiv.org/html/2603.17117v1)；2603.17117v1，2026-03-17 | VERIFIED | **§2.2–2.3；§4.2，Table 1**。3D patch检索和warped RoPE/warped latent均存在；§4.2明确warped latent相机更准确，但视觉和memory指标不如warped RoPE。 不是几何噪声幅度单因素实验；综述称条件对齐取舍恰当。 |
| 15 | [GIM-World](https://arxiv.org/html/2606.02436v1)；2606.02436v1，2026-06-01 | VERIFIED | **§3.2–3.5；Tables 2–3**。固定memory tokens、VGGT几何特征监督、推理移除teacher/head、K=200相同预算三种history pruning均直接支持。 特征监督不等于实测depth更准。gim-world.github.io本次直开仍失败，仅核论文，不推断资源不存在。 |
| 16 | [LSM-World](https://arxiv.org/html/2606.09828v2)；2606.09828v2，2026-08-27 | VERIFIED | **§4.4；Tables 3–4；Limitations**。v2题名与作者匹配；latent 3D缓存、动态过滤和跨chunk动态状态限制明确。DA3/MapAnything/UniDepth的Avg依次70.36/69.66/69.13。 原表没有配套真实depth误差或统计区间；“差异较小”只可指这次报告的点估计跨度，不是等效性检验。搜索摘要曾返回Mirage旧名称，已排除，采用固定v2正文。 |
| 17 | [PERSIST](https://arxiv.org/html/2603.03482v2)；2603.03482v2，2026-06-03 | VERIFIED | **§4–5；§7；Luanti数据设置**。持续latent 3D状态与环境演化成立；明确依赖训练时GT 3D监督，使用Luanti体素环境。 不等同自然RGB历史照片任务；综述已说明任务差异。 |
| 18 | [WorldTrace](https://arxiv.org/html/2608.07408v1)；2608.07408v1，2026-08-07 | VERIFIED | **§2.1–2.2；摘要**。存储KV但超训练范围temporal RoPE偏移妨碍读取、旋转相位中直接压缩还会损坏信息，均为论文讨论和分析对象。 限论文分析的相关模型/配置；正文使用“某些模型”，没有扩大为所有遗忘的唯一原因。 |
| 19 | [FreeScale](https://arxiv.org/html/2604.10512v1)；2604.10512v1，2026-04-12；CVPR 2026 | VERIFIED | **§4.1.2–4.2；作者项目页**。certainty voxel grid、visibility加权IoU view graph、扩增NVS训练数据和逐场景重建均匹配；作者项目确认CVPR 2026。 CVF链接403，改读arXiv原文及作者页。certainty来自小且不透明高斯的启发式代理，不是校准置信概率；正文没有此额外主张。 |
| 20 | [TUM RGB-D](https://jsturm.de/publications/data/sturm12iros.pdf)；IROS 2012 作者PDF及官方数据页 | VERIFIED | **原论文首页、§III；官方dataset页面**。标题、五作者匹配；Kinect RGB-D与外部motion capture轨迹成立。 原tools URL超时，数据主页及作者PDF成功。Kinect depth仍是传感器测量，综述没有冒充无误差扫描真值。 |
| 21 | [MEt3R](https://arxiv.org/html/2501.06336v2)；2501.06336v2，2026-02-21；CVPR 2025 | VERIFIED | **§3；Appendix C；官方README**。学习pointmaps对齐特征并在overlap mask上比较，目标是跨视图一致性；README要求CUDA≥11.3，测试CUDA11.8。 修订版日期2026不改变CVPR2025会议年；不是单图质量指标或Mac运行证据。 |
| 22 | [GeCo](https://arxiv.org/html/2512.22274v5)；2512.22274v5，2026-08-19 | VERIFIED | **§3；§6 Limitations；官方README**。残余运动与depth结构互补；真实动态内容可误罚明确见§6；官方测试环境Linux/CUDA12.8。 使用指定v5新题名；没有把静态场景假设扩大为通用动态视频指标。 |
| 23 | [SysCON3D](https://arxiv.org/html/2605.18754v1)；2605.18754v1，2026-05-18 | VERIFIED | **摘要；§4–7；Discussion**。对无关场景、重复图和噪声，神经几何可产生虚构支持；传统COLMAP会因弱纹理、重复和低重叠失败，原文均明确。 压力测试不等于自然视频错误发生率；综述没有宣称COLMAP无误差或把重复图一概当视觉不一致。 |
| 24 | [WorldRoamBench](https://arxiv.org/html/2606.31672v1)；2606.31672v1，2026-06-30 | MINOR | **§3.4；Appendix F.1**。由WorldCompass估计动作并映射/平滑pseudo-label定位观察→回访转折；估计depth/pose生成两段点云并RANSAC/ICP对齐。 “按实际转向分段”省略估计步骤，且transition包括平移动作转换，不只转向；改成“按从视频估计的观察—回访动作转折分段”。 |
| 25 | [WorldExam](https://arxiv.org/html/2608.02603v1)；2608.02603v1，2026-08-03 | VERIFIED | **§4.1 Scene Revisit；官方仓库**。返回窗口选估计pose距离最近帧；平移/旋转分别定义距离和成功阈值，再评价PSNR/LPIPS/SSIM。仓库当前仅README和teaser.png。 并非外部真值相机返回；正文已用估计位姿并提醒残余视差。仓库状态是审查时点快照，不代表未来。 |

## 必须补清的两处

**C1 · TTT3R，§4及§7。** 原句“TTT3R的附录存在位姿改善而深度变差的设置”字面不假，但省略了干预对象。Appendix A.2说的是引入该更新规则后继续微调，并非冻结权重主方法的直接结果。[原文v4，A.2](https://arxiv.org/html/2509.26645v4)

建议替换：

> TTT3R附录A.2的额外微调变体出现位姿改善而深度变差；这一现象来自训练设置变化，不能归给冻结权重的主方法。

§7若继续把它与S6并列，应写“TTT3R额外微调变体、FILT3R固定EMA消融”，继续保留“不同干预不能推断共同根因”。

**C2 · WorldRoamBench，§6。** 原句“按实际转向分段”容易被读成外部真实动作边界。F.1先由WorldCompass估计动作，再映射、平滑伪标签，寻找观察到回访的稳定转折；它也不只处理旋转。[原文v1，F.1](https://arxiv.org/html/2606.31672v1)

建议替换：

> WorldRoamBench按从视频估计的观察—回访动作转折分段，再对齐两段估计点云。

## 数字与近邻句检查

- **Spatia Table 4：通过。** 无条件、仅投影、仅参考、联合的LPIPS_C依次0.379、0.295、0.393、0.213。综述引用无→仅参考→联合的三个值正确；这里只能说单个LPIPS_C指标，并非仅参考让全部指标变差。[原文](https://arxiv.org/html/2512.15716v1)
- **LSM-World Table 4：通过。** 三种depth来源的WorldScore Avg为70.36、69.66、69.13。没有配套的真实depth误差或统计区间，“差异较小”只能描述表内点估计。可改为“分别低0.70与1.23分，未给出统计区间”，避免暗示等效性。[原文v2](https://arxiv.org/html/2606.09828v2)
- **AnchorWeave：通过。** 单个全局anchor与多个局部anchor同时变化；简单平均的对象是条件融合。综述已正确限制这两点，不能将其用作surfel坐标平均的直接反证。[原文](https://arxiv.org/html/2602.14941v1)
- **FILT3R：通过。** 固定EMA可降低全局ATE而增加局部旋转误差；不是所有指标都领先。token方差不等于物理三维误差，综述已有正确限定。[原文](https://arxiv.org/html/2603.18493v1)
- **WorldRoamBench与WorldExam：推论需保留。** 云配准能吸收整体位置偏差；按估计pose选择回访帧仍有估计误差和残余视差。这些是方法结构带来的评价限制，不是本项目测得的误差比例。[WorldRoamBench](https://arxiv.org/html/2606.31672v1)、[WorldExam](https://arxiv.org/html/2608.02603v1)
- **S6段落：未重新数值核验。** 其证据指向本地结果与独立审查，正文没有让文献替代本地证明；本审查不能给3453检查数或S6结果再次盖章。§8关联轨迹修改后的文字已重读，仍明确是未执行建议。

## 版本和资源复核

建议把Spann3R动态链接固定为[2408.16061v1](https://arxiv.org/html/2408.16061v1)，TTT3R固定为[2509.26645v4](https://arxiv.org/html/2509.26645v4)。LSM-World已正确使用2026-08-27的v2；搜索摘要曾返回旧框架名Mirage，本审查没有用它覆盖v2的LSM-World。GeCo已正确使用2026-08-19的v5新题名。MEt3R链接为2026修订v2，会议仍是CVPR2025，二者不冲突。

SPMem官方仓库实际含推理、训练、模型和TSDF目录，因此“已有官方代码”成立；AnchorWeave论文的SPMem重实现标记仍属于它写作时的事实。[SPMem官方仓库](https://github.com/spmem/spmem) 本次未执行代码。TTT3R与FILT3R所依赖的512 DPT 4–64-view权重、MEt3R与GeCo的CUDA环境可核实，不能据此保证224 linear或MPS复现。[TTT3R](https://github.com/Inception3D/TTT3R)、[FILT3R Appendix C](https://arxiv.org/html/2603.18493v1)、[MEt3R](https://github.com/mohammadasim98/met3r)、[GeCo](https://github.com/ShixuanGu/GeCo)

WorldExam仓库本次根目录只见README和teaser.png，未见可执行评价实现；GIM-World项目页直开仍失败，论文可读。前者是时点快照，后者只说明访问失败，均不能说论文不存在。[WorldExam官方仓库](https://github.com/YuxueYang1204/worldexam)、[GIM-World论文](https://arxiv.org/html/2606.02436v1)

TUM原tools页超时，但作者PDF与官方数据主页成功，可为采集/测量主张补更直接链接。[TUM原论文](https://jsturm.de/publications/data/sturm12iros.pdf)、[TUM数据主页](https://cvg.cit.tum.de/data/datasets/rgbd-dataset)

## 访问失败的明确记录

- ElasticFusion：作者PDF与RSS PDF的直接open多次超时/内部错误；后续官方RSS索引返回§III中surfel属性与融合原文。**降级为相关官方摘录审查**，不混用2016 IJRR扩展版。
- EM-Fusion：CVF PDF 403，arXiv PDF超时，作者项目直开错误；CVF原文索引返回Figure 1和§3，作者/论文元数据匹配。**降级为相关官方摘录审查**，未独立读取Room4完整表。
- Park：CVF PDF 403；arXiv PDF首次成功打开9页并读匹配方法，后续重复查询超时。采用已成功的原文读取，不伪称所有请求都成功。
- FreeScale：CVF正式页403；arXiv v1全文和作者项目成功，方法与CVPR2026信息可核。
- TUM：tools页超时；作者8页PDF、官方数据主页成功。
- GIM-World：项目页失败；论文v1全文成功，资源可用性单独保留不确定。

配套机器可读记录：[LITERATURE_SYNTHESIS_V2_CITATION_AUDIT.json](LITERATURE_SYNTHESIS_V2_CITATION_AUDIT.json)。本审查只新建这两份文件；综述、协议、实验与主账本由父任务处理。


父任务后续定点澄清：FUSION_EVIDENCE的ATE_orig与本审查的ATE是原表不同对齐列，两个数值均正确；见 [指标口径记录](literature_v2/FILT3R_METRIC_CLARIFICATION.md)。原审查范围与等级不变。
