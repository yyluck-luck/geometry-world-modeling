# 已提交地图与重新标定：四篇原方法排重（SOURCE ONLY）

**结论：目前只能保留为 baseline 消费者的一致性检查，不能把“内参改变后同步旧地图／查询缓存”立为创新。** 最强近邻已经覆盖联合标定与地图优化、旧贡献撤销后重融合、Surfel 变形，以及按变化量分配更新预算。本轮不读取 S24/S26/S26B 预测数组、GT 或分数，不运行模型、GA、生成或数值诊断；不预判 S26B 是否出现变化或伤害。项目状态只从规定的连续性文档恢复，非结果分析。

起点是已有 [VMem 源码审计](../S26_commit_consistency_source/audit.md)：固定 VMem commit `39291e4f272f6b4f270691d930926ab5930f942e` 中，旧 depth/pose 固定、focal 仍优化，旧 Surfel 通常不覆写；`surfel_Ks.extend` 累计每轮全部历史估计。它证明路径可能存在，不证明失败已发生。原始关系 `X=R[d(u−cx)/f,d(v−cy)/f,d]+t` 说明固定 depth/pose 不等于固定 world point。

## 原文与最近机制

| 工作、已读位置 | 原方法明确做了什么 | 与 VMem 线索的差别及排重意义 |
|---|---|---|
| **BAD SLAM: Bundle Adjusted Direct RGB-D SLAM**，Thomas Schöps、Torsten Sattler、Marc Pollefeys，CVPR 2019；[原论文](https://openaccess.thecvf.com/content_CVPR_2019/papers/Schops_BAD_SLAM_Bundle_Adjusted_Direct_RGB-D_SLAM_CVPR_2019_paper.pdf)，§3.1–3.3、Alg.1。 | 全部关键帧共享内参；可选优化彩色/深度相机标定及深度形变。交替步骤更新 Surfel 法向、位置/描述子、关键帧 pose、内参，并合并/清理地图。 | **最近的标定＋稠密地图近邻。** “内参步固定其他变量”仅指该交替步骤，不能误读为地图永久固定。它用 RGB-D 测量和可更新 Surfel；本项目是给定 pose、冻结旧估计 depth、每帧 focal 与生成记忆。对象/设置不同，但“联合内参和地图”已不是新机制。 |
| **BundleFusion: Real-time Globally Consistent 3D Reconstruction using On-the-fly Surface Re-integration**，Angela Dai、Matthias Nießner、Michael Zollhöfer、Shahram Izadi、Christian Theobalt，TOG 2017；[原论文 v3](https://arxiv.org/pdf/1604.01093v3)，§5.1–5.3；[作者项目](https://graphics.stanford.edu/projects/bundlefusion/)。 | 每帧保留 RGB-D、地图当前使用的 integrated pose 与最新 optimized pose。旧 pose 下撤销 TSDF 贡献，新 pose 下重融合。按两种 pose 的加权差排序，每个新输入帧修复前 10 帧。 | **最近的“已提交量≠最新估计”近邻。** 不仅重建旧地图，按差异优先分配有限更新量也已有。这里更新的是 pose 与体素 TSDF，不能声称它已实现本项目的在线 focal 更新；但仅把 pose 改成 focal、TSDF 改成 Surfel 不足证明实质创新。 |
| **ElasticFusion: Dense SLAM Without A Pose Graph**，Thomas Whelan、Stefan Leutenegger、Renato F. Salas-Moreno、Ben Glocker、Andrew J. Davison，RSS 2015；[原论文](https://roboticsproceedings.org/rss11/p01.pdf)，§III–IV、Eq.8–10、Alg.1。 | RGB-D Surfel 地图分活动/非活动区。回环约束驱动变形图，实际变换旧 Surfel 的位置与法向；时间关联防止不同扫描经过不恰当地绑在一起。 | **最近的持久 Surfel 修正近邻。** 它通过变形维护地图一致性；所读公式把 K 作为投影/反投影参数，没有给出在线 K 的优化变量。不能把“所有 Surfel 随内参自动正确更新”归给它，也不能把“旧 Surfel 应可修改”当本项目新意。 |
| **Direct Sparse Odometry**，Jakob Engel、Vladlen Koltun、Daniel Cremers，arXiv 2016；[原论文](https://arxiv.org/pdf/1607.02565)，§1.2、§2.1.1–2.3、Fig.5、§4.4。 | 活动窗口联合优化全局内参向量 c、相机 pose、点的逆深度；旧 pose/点被边缘化。§4.4 的展示重建由里程计积累，没有回环整合。 | **在线自标定的基本对照。** 它不是保持全部旧稠密地图可更新的系统，不能当作已解决 VMem 持久地图。但联合考虑内参/深度/pose 的依赖关系已经明确，不能只把三者联动命名为新方法。 |

作者代码的直接交叉核查：BAD SLAM 固定 commit `c66bdc841658cc04f9feae229c746b32f4284102`，[`direct_ba_alternating.cc:465`](https://github.com/ETH3D/badslam/blob/c66bdc841658cc04f9feae229c746b32f4284102/applications/badslam/src/badslam/direct_ba_alternating.cc#L465) 调用几何优化，[:584](https://github.com/ETH3D/badslam/blob/c66bdc841658cc04f9feae229c746b32f4284102/applications/badslam/src/badslam/direct_ba_alternating.cc#L584) 后执行内参优化，611–616 写回相机参数，623–624 通知内参更新。所读作者 [README 的版本说明](https://github.com/ETH3D/badslam/blob/c66bdc841658cc04f9feae229c746b32f4284102/README.md#differences-to-the-paper) 明确公开版本有重构和残差变化，因此这只是实现结构交叉核验，**没有声称源码逐值复现论文**。另三仓库只核来源/commit 元数据，未完成函数级代码审计；它们的机制判断来自上述原论文方法，不来自搜索摘要或第三方综述。

## 对当前线索的判定与下一道门

以下是本轮分析，不是论文结论或已发生的实验结果。

1. **普通工程问题先处理。** 历史 `K` 快照若本应是一帧一份却重复加权，首先是缓存契约问题；如果原作者有意做时间平滑，须比较该语义的效果，不能凭 `extend` 就判 bug。当前帧索引缓存、撤销同步和地图/标定版本一致提交均是必要工程对照，不是论文贡献。
2. **几何更新也先用常规对照。** 比较仅冻结旧 focal（新 focal 仍可优化）、共同标定、用当前条件重建旧地图、按来源撤销/重融合或变形。VMem 原 `preset_focal` 会冻结整栈，不能误作只冻结旧帧。新增时间/RSS/存储及真实修改的地图量要计入成本；BundleFusion 已排除了泛泛“优先更新变化最大的旧帧”新意。
3. **先问更新是否有害，再问如何干预。** 旧 focal/world 变化可能修正旧错误，也可能不改变可见性或选图。未来保存输出只支持局部变化量；必须继续核真实已提交 Surfel、同一查询的深度/可见索引、来源投票和 context IDs，最后核生成一致性。只改善自由相机 ATE 或看见 pointmap 变化，均不足支持原 proposal。
4. **实质研究问题仅作为待证假设。** 在上述控制仍失败时，才研究：生成的、相互依赖的新观测是否会使“接受当前最优标定并更新地图”与“保留历史生成条件”发生不可由普通重建解决的冲突；是否需要新目标/表示，并能在相同信息和预算下改善完整生成。四篇论文的测量/任务设置不同仅是差异，**不是这个剩余问题已成立或无人研究的证据**。当前不提出具体新机制、不据此批准 S/M 干预。

应用 Supervisor `handbook/02_Idea_Generation` 的 baseline→失败→根因路线、2.3 的问题优先原则；再用 `idea-evaluator` 的致命缺陷门：**F1，泛化方案与已有机制重叠，阻断其新方法主张；F9 风险，若在重要自然失败和消费者伤害未证前先定同步机制，就会变成给方案找问题。** 后者是流程风险，不能把待验证误写成数据已否决。本地 Claude `sci-scientific-critical-thinking` 用于区分构念（几何变化≠伤害）、混杂（新约束/初始化/方法改变）和外推（8 帧组件≠完整生成）。这不是完整候选评分：**泛化“同步地图”方案 Reject and Pivot；具体 VMem 一致性检查保留为诊断。** 若普通修复解决问题，就按 baseline 修复收束，不为追求新颖而增加包装。

## 检索记录

本轮 2026-09-06 UTC / 2026-09-07 北京时间，实际 URL、访问时间、SHA 和失败保存在 [retrieval_receipt.json](retrieval_receipt.json)；网页方法阅读补记及查询组见 [source_notes.json](source_notes.json)。本地保留 BAD SLAM、BundleFusion、ElasticFusion 原 PDF/文本和 3 个 BAD SLAM 作者源码。DSO PDF 本地下载两次 SSL 失败，但网页工具成功打开并阅读原 PDF 方法；无本地 PDF 字节封存，不伪称下载成功。搜索出现的第三方说明未用于方法结论。此为有界四篇排重，未穷尽整个领域，也不是最新工作全覆盖。主账由 root 汇总，本 agent 未修改。
