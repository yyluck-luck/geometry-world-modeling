# S12想法审查：普通覆盖互补选图能否作为新方法

## 1. 第一印象

评估的是本轮由研究助手提出的候选C0，用户没有声称已经发明它：**给每张历史图估计对目标视角的覆盖，每次选择新增覆盖最多的一张，固定四张预算，希望减少参考图之间的重复。** 预期论文类型是Novel Method，研究范式是计算实验；当前不包含新的覆盖估计器、可靠性机制、误差保证或消费者适配。

动机在直觉上合理，但方法故事已被直接近邻覆盖。S7/S8的负结果和条件差异只能说明值得检查选图机制，尚未运行C0，不能把它判成“已被本地数据击败”。本次拒绝依据是当前方法贡献不足，而非编造其未运行的实验表现。

使用HKUSTDial/Supervisor-Skills的idea-evaluator，按先致命缺陷、再决定是否评分的顺序。证据包括五篇定点原文及已有结果的公平对照审查；本次不是新的全领域综述。

## 2. 致命缺陷与近邻原文

| 缺陷 | 严重性 | 具体依据 | 处理 |
|---|---|---|---|
| F1：当前C0描述没有超出最近方法的可辨识贡献 | CRITICAL，仅针对把这条普通贪心规则作为论文新方法的版本 | 检测规则要求说清相对最近工作的新增内容。目标条件覆盖、边际增益贪心、固定少量历史图预算均已有直接实现；当前没有另一个明确研究轴可供验证。补引文、把K改成4或给普通规则起名字不能修复这一版本。 | 不为本版本编造辩护；需要改变研究主张或机制后，另行评价。 |

CRITICAL是对当前唯一贡献的研究判断：补实验或润色不能把已知规则本身变成新方法，加入新的机制则应视为另一个版本重新评价。它不因“尚未测试”自动触发，也不来自对用户工期或资源期限的臆测。

这里的判断不是“实现逐字相同”，也不是断言任何显式几何方法都无新意。不同工作仍有输入表示、是否强制最后帧、查询单位和消费者差异；当前C0没有提出为何这些差异构成可证实贡献。下面按实际对象与机制比较，而非按标题相似就宣布重复。

| 已核工作、作者与年份 | 对象／机制／粒度／设定 | 与C0的关系 |
|---|---|---|
| *Retrieve What's Missing: Coverage-Maximizing Retrieval for Consistent Long Video Generation*；Minseok Joo、Dogyun Park、Taehoon Lee、Kyujin Lee、Hyunwoo J. Kim，2026（COVRAG预印本） | 历史帧；扣除已有覆盖后取最大新增覆盖；深度投影的二值目标像素；记忆条件视频生成。[§4.2/Algorithm1](https://arxiv.org/html/2606.02479v1#S4.SS2) | 已直接实现C0的核心联合选择思路。其具体检索数与上下文不同，不能把预算差异当作新算法。 |
| *I3DM: Implicit 3D-aware Memory Retrieval and Injection for Consistent Video Scene Generation*；Jia Li、Han Yan、Yihang Chen、Siqi Li、Xibin Song、Yifu Wang、Jianfei Cai、Tien-Tsin Wong、Pan Ji，2026（v2预印本） | 整张历史帧；patch置信边际覆盖贪心；学习式隐式证据；三张检索帧加最后帧。[§3.2与补充§2](https://arxiv.org/html/2603.23413v2#S3.SS2) | 固定总四张也有直接近邻。其置信估计与注入是具体机制，C0当前没有对应新增内容。 |
| *AnchorWeave: World-Consistent Video Generation with Retrieved Local Spatial Memories*；Zun Wang、Han Lin、Jaehong Yoon、Jaemin Cho、Yue Zhang、Mohit Bansal，2026（预印本） | 历史局部空间记忆；新增可见覆盖贪心；局部点云／目标轨迹块；渲染anchor clips条件生成。[§3.3与附录B](https://arxiv.org/html/2602.14941v1#S3.SS3) | 已有显式几何互补检索，不能简单声称“把覆盖换为三维就首次”。其片段消费者与C0的原图设定不同，需新增证据才能主张有价值差异。 |
| *BoostMVSNeRFs: Boosting MVS-based NeRFs to Generalizable View Synthesis in Large-scale Scenes*；Chih-Hai Su、Chih-Yao Hu、Shr-Ruei Tsai、Jie-Ying Lee、Chin-Yang Lin、Yu-Lun Liu，2024（SIGGRAPH） | 多视图代价体；maximum coverage贪心；软二维可见性；新视角合成。[§3.4](https://arxiv.org/html/2407.15848v1#S3.SS4) | 是较早的邻近机制先例；选择单位是代价体，不等于四张不同照片，因此不宣布与C0完整重复。 |
| *VMem: Consistent Interactive Video Scene Generation with Surfel-Indexed View Memory*；Runjia Li、Philip Torr、Andrea Vedaldi、Tomas Jakab，2025（ICCV） | 历史图；目标可见来源投票与姿态NMS；surfel到像素；交互视频生成。[§3.1](https://arxiv.org/html/2506.18903v3#S3.SS1) | 原基线已有可见性和多样性。它在所读流程中没有边际覆盖扣除，但只补普通覆盖贪心仍须面对前四篇。 |

本轮实际15条查询、五篇核心原文和44份文件身份记录见[定点文献核查](S12_COVERAGE_NOVELTY_SCOUT.md)。I3DM已核当前v2；未核接收的工作只称预印本。未得到全文的其他线索不用于方法判断；未声称检索穷尽全领域。论文的生成性能不转写成本机收益。

## 7. 结论与先做的三件事

**Reject and Pivot：不把当前普通覆盖贪心C0作为论文新方法开发。** 这个结论只否定本版本的创新定位，保留它作为已知基线的用途。依据技能的CRITICAL短路规则，不继续打五维分、计算虚构研究周期或装饰性评估颠覆潜力。

1. 将普通二值／软覆盖贪心列为后续新方法必须面对的基线；本轮不因论文存在就宣称已在本机复现，也不增加一个新算法名字。
2. 先完成同候选数量诊断的独立设计/实现审查，再冻结并运行：来源14与姿态14都经过相同NMS、输出4张，再用同一实测支持评分。现有全20姿态对照的作用边界见[已有证据审查](S12_EXISTING_EVIDENCE_AUDIT.md)，新实验合同见[同候选数量协议](S12_MATCHED_BUDGET_PROTOCOL.md)。该诊断不作为C0的辩护或胜出证据。
3. 只有识别出具体、可复核的失败条件，才能提出新的机制；再检查其相对上述近邻的新增内容，并设计能推翻主张的实验。完整VMem／视频质量尚未验证，支持率改善不能替代消费者收益。若拟用GT枚举最优四张，它也只能是知道答案后的上限分析。

用户已授权继续本机研究。当前可执行的是小范围组件分析；没有用自动运行时长推算学生能力、每周投入、会议或老师评价，也不承诺论文接收。
