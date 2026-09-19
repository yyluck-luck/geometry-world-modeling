# 技术报告引用独立核验

核验开始：2026-09-05 22:49，Asia/Shanghai；审计文件完成记录：2026-09-05T22:53:34.796799+08:00。范围快照实际保存于 2026-09-05T22:52:12.567463+08:00；未把该时间解释为写作耗时。

对象：`docs/TECHNICAL_REPORT.md` 的 Introduction、Related work、References。另核对 3.3 的 TUM 官方格式说明及 3.5 的 TUM 精度限制引用。报告仍在补写；本文件不认证随后新增的文字，也不认证本地实验、统计数字、代码正确性或生成视频效果。

按项目要求读取了研究连续性文件，但没有把项目记忆、旧引用审计或写作者的研究推理当作文献证据；本次从报告引用句独立访问作者页面、作者提交的论文、会议或数据集官方来源。未读取旧 `CITATION_AUDIT.md` 或 `LITERATURE_VERIFIED.md` 来决定核验结果。部分会议 PDF 抓取失败时，使用足以支撑相应主张的官方摘要、作者项目页和 arXiv 正文；不能把本次工作描述成七篇论文全部逐页精读。

范围快照 SHA-256：`69048d13c5f691bc1ce375ad46f17b6e22570c9603f1d988719ad0f7f7541a2d`。对应整份报告当时的 SHA-256：`a82926f2e7954c88c656fe1707950e6678650d85c8b26402b1166ddbe16439d5`。审计中间材料保存在当前 Codex 工作区的 `work/report-citation-audit/`；只有前述章节属于冻结核验范围。

## 结论

七项书目元数据和下列具体方法主张均为 **VERIFIED**。未发现 **METADATA_MISMATCH**，未发现已确定的 **OVERCLAIM**；核验范围内没有因关键证据缺失而判为 **INCONCLUSIVE** 的项。这个结论只针对逐项列出的事实，不等同于对报告全文、方法创新性或实验真实性的背书。

有一处建议把引用归属写得更清楚，见文末。它是消除歧义的措辞建议，不是认定原句虚假。

## 逐项证据

| 编号 | 书目信息 | 方法主张 | 核验结果 |
|---|---|---|---|
| [1] VMem | 题名、前三作者顺序、ICCV 2025、25690–25699 与作者 BibTeX 一致；论文链接明确为 arXiv v3 | 历史视图与 surfel 的来源索引关联；从目标相机渲染索引后选参考帧；匹配后加入新视图索引 | VERIFIED |
| [2] CUT3R | 题名、前三作者顺序、CVPR 2025 与作者项目及会议页面一致 | 持续更新的递归状态、公共坐标系 pointmaps 与相机信息；online 与 revisiting 区别 | VERIFIED |
| [3] Spann3R | 题名、两位作者、3DV 2025、78–89 一致；2024 是预印本年份 | 外部空间记忆；首帧坐标系 pointmaps；不依赖优化式全局对齐 | VERIFIED |
| [4] ElasticFusion | 题名、作者顺序、RSS 2015、DOI 一致 | RGB-D 增量建图中的 frame-to-model tracking、窗口内 surfel 融合及非刚性表面修正 | VERIFIED |
| [5] Probabilistic Surfel Fusion | 题名、前三作者顺序、ICCV Workshops 2017 一致 | 关联考虑表面分辨率及测量不确定性；以 Bayesian filtering 融合观测 | VERIFIED |
| [6] I3DM | 题名、前三作者顺序、arXiv:2603.23413、2026、v2 一致；未赋予会议 venue | 预训练 FF-NVS 中间特征给历史视图评分；对齐历史内容；以可靠区域条件化生成 | VERIFIED |
| [7] TUM RGB-D benchmark | 题名、前三作者顺序、IROS 2012 一致 | Kinect RGB-D 与 motion-capture 轨迹的来源；格式、标定建议及高精度表面评测限制 | VERIFIED |

### [1] VMem

报告题名为 “VMem: Consistent Interactive Video Scene Generation with Surfel-Indexed View Memory”。作者页顺序是 Runjia Li、Philip Torr、Andrea Vedaldi、Tomas Jakab；报告前三人后使用 et al. 正确。作者给出的会议 BibTeX 明确列出 ICCV 2025 与页码 25690–25699。[作者项目及 BibTeX](https://v-mem.github.io/)

Introduction 首段及 Related work 2.1 的方法概括得到正文 3.1 支持：surfel 保存观察它的历史视图索引，读取时从目标视角渲染并汇总来源；写入时匹配既有 surfel，加入当前索引并丢弃匹配的新 surfel。报告没有把这段描述成位置平均更新。[论文 v3，Section 3.1](https://arxiv.org/html/2506.18903v3#S3.SS1)

2.1 关于清理和筛选的句子是**源码事实**，不能只归因于论文摘要。本次还独立取回报告指定 revision 的公开源码：`extern/CUT3R/surfel_inference.py` 第 197 行调用点云清理；`modeling/pipeline.py` 第 871–872 行按深度分位值和置信度阈值形成有效掩码。来源足以支持“存在过滤”，但不支持“已测出完整过滤后的自然错误率”。[指定版本的清理调用](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/extern/CUT3R/surfel_inference.py#L197)、[指定版本的筛选](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/modeling/pipeline.py#L871)

### [2] CUT3R

“Continuous 3D Perception Model with Persistent State”的作者页及会议页面确认前三位作者为 Qianqian Wang、Yifei Zhang、Aleksander Holynski，发表为 CVPR 2025。报告未填页码不构成错误。[作者项目](https://cut3r.github.io/)、[CVPR 官方记录](https://cvpr.thecvf.com/virtual/2025/poster/34897)

Introduction 与 2.2 的递归状态、统一坐标系点图及相机输出可由作者方法概述支撑。2.2 对 online/revisiting 的区分也准确：后者先处理全序列，冻结最终状态，再重新处理同一批图像；所以后者拥有第一次在线预测时没有的后续上下文。该定义可在论文 4.4 和作者页面同名小节直接找到。[正文 Section 4.4](https://arxiv.org/html/2501.12387v1#S4.SS4)、[作者的 Online vs. Revisiting 说明](https://cut3r.github.io/)

### [3] Spann3R

“3D Reconstruction with Spatial Memory”的作者为 Hengyi Wang 和 Lourdes Agapito。作者项目 BibTeX 明确为 3DV 2025、78–89；arXiv 首次提交是 2024-08-28，因此报告把会议年份写为 2025、把另一个链接标为 2024 preprint 是正确区分。[作者项目及 BibTeX](https://hengyiwang.github.io/projects/spanner)、[预印本记录](https://arxiv.org/abs/2408.16061)

Introduction 和 2.2 的三个技术点均在作者摘要及 Pipeline 说明出现：外部空间记忆、统一于初始帧坐标系的逐帧点图、无需优化式全局对齐。这里的“globally aligned”指坐标表示与预测目标，不能额外引申为任何序列都无漂移；报告当前没有作此引申。[作者方法说明](https://hengyiwang.github.io/projects/spanner)

### [4] ElasticFusion

“ElasticFusion: Dense SLAM Without A Pose Graph”的 RSS 2015 记录确认作者顺序、题名和 DOI `10.15607/RSS.2015.XI.001`。会议页面将第三作者排作 Renato Salas Moreno，而报告使用 R. F. Salas-Moreno；作者本人公开资料确认完整姓名含 F，这属于姓名展开及连字符差异，未发现作者身份或顺序错误。不要与作者顺序不同的 2016 IJRR 扩展论文混淆。[RSS 正式记录](https://www.roboticsproceedings.org/rss11/p01.html)、[第三作者公开履历](https://www.renatosalas.com/assets/docs/renato_cv-web.pdf)

Related work 2.3 的 frame-to-model tracking、windowed surfel fusion、non-rigid correction 与 RSS 官方摘要直接相符。本项验证这些具体机制；并不把 ElasticFusion 直接等同于 Park 等人的概率测量模型。[RSS 官方摘要](https://www.roboticsproceedings.org/rss11/p01.html)

### [5] Probabilistic Surfel Fusion

“Probabilistic Surfel Fusion for Dense LiDAR Mapping”的 arXiv 作者栏确认 Chanoh Park、Soohwan Kim、Peyman Moghadam 位列前三。作者提交记录与第一作者页面均明确是 2017 ICCV 的 Multiview Relationships in 3D Data workshop。报告写 ICCV Workshops 正确，不能删去 Workshops 后改成主会论文。[作者提交记录](https://arxiv.org/abs/1709.01265)、[第一作者会议记录](https://copark86.github.io/publication/2017-10-29-surfelfusion)

2.3 关于关联考虑表面分辨率及光束方向测量不确定性、通过 Bayesian filtering 进行融合的表述均由摘要直接支撑。报告没有把该完整系统说成简单逐帧均值。[作者提交的摘要](https://arxiv.org/abs/1709.01265)

### [6] I3DM

“I3DM: Implicit 3D-aware Memory Retrieval and Injection for Consistent Video Scene Generation”的前三作者是 Jia Li、Han Yan、Yihang Chen。v2 记录注明 2026-07-31 修订；作者项目仍标 Arxiv, 2026。报告当前将其列作 arXiv:2603.23413、2026，未猜测会议 venue，符合能取得的一手记录。[arXiv v2](https://arxiv.org/abs/2603.23413v2)、[作者项目](https://riga2.github.io/i3dm/)

Introduction 与 2.1 的表述与 v2 摘要对应：用预训练 FF-NVS 模型中间特征评分和检索历史帧，对历史内容进行隐式目标视角对齐，并根据可靠对齐区域条件化生成。报告没有声称本项目已复现或在性能上超过 I3DM。[v2 摘要](https://arxiv.org/abs/2603.23413v2)

### [7] TUM benchmark

“A Benchmark for the Evaluation of RGB-D SLAM Systems”的作者顺序 Jürgen Sturm、Nikolas Engelhard、Felix Endres 等及 IROS 2012 由官方书目确认。作者论文的介绍和数据章节明确区分 Kinect 彩色/深度观测与 motion-capture 相机轨迹，支持报告对数据来源的描述。[官方书目](https://cvg.cit.tum.de/research/vslam?key=sturm12iros)、[作者提供的论文](https://jsturm.de/publications/data/sturm12iros.pdf)

另查 3.3：官方格式页明确规定 PNG 深度除以 5000 得米、0 无数据；提供 ROS-default 内参 525/525/319.5/239.5；建议在预配准深度上使用 ROS-default 参数且不再去畸变；深度尺度已经预校正。报告所述与说明一致。这只确认处理规范，不验证本地适配器的实际执行。[官方格式和标定说明](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats)

另查 3.5：作者论文 Section VI.C（PDF 第 5 页）明确提醒，motion-capture 位姿不能直接生成或评估高精度三维场景模型；报告将其作为表面一致性评测的限制，引用准确。该限制不是对任何本地误差数值的解释或验证。[论文 Section VI.C](https://jsturm.de/publications/data/sturm12iros.pdf#page=5)

## 一处建议及审计边界

Introduction 第二段把 ElasticFusion 和 probabilistic surfel fusion 合并在一句中，容易让读者以为两篇都以同一种 uncertainty-aware fusion 为核心。当前可按“两个先例共同覆盖这些机制”理解，因此不记为已确定的 OVERCLAIM。建议改为：

> ElasticFusion updates surfel maps through repeated observations [4], while probabilistic surfel fusion explicitly models measurement uncertainty during association and fusion [5].

2.1 关于清理、置信度和深度筛选，可在原句后就近加入上面的两个指定版本源码链接，便于读者区分论文级概括和源码检查。

“这些基础机制本身不足以构成新颖性”是报告根据先例作出的有限综合判断，文献确实证明这些基础机制已经存在；这不是对整个研究领域进行穷尽检索后的新颖性证明或否定。本审计也不证明本地实验的完整性、可复现性、统计独立性、自然错误频率或端到端生成效果。最终新增 Results、Discussion、Conclusion 若包含新文献事实，应对新增句另作核验。
