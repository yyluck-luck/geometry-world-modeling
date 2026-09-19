# S26：已知相机约束用于在线几何的有界近邻核查

记录日：2026-09-06。精确完成时点、访问清单和本地文件 SHA 见同目录 `sources.json`。本轮只读手册、源码审计文字和原论文；0 模型、0 GA、0 真实预测数组 / GT 读取。S26 评分器与其协议保持不改。

**结论：拒绝把“加相机条件”“用已知 pose 做 BA / GA”“相机损失回传共享网络”“ray 差异控制状态更新”单独当新方法。** 原文已经覆盖这些做法。保留的问题是：**在原 VMem 已固定全部相机和旧 depth 的条件下，是否仍存在可归因、会传到 Surfel / 可见性消费者的几何失败，而且普通输出空间优化不足以解决？** 这不是已发现的失败，更不是已证明的创新；本轮不据此启动新分支。

## 1. 先把真正的 baseline 放回比较

按 Supervisor 2.2 的“强 baseline → 失败归类 → 根因 → 针对模块”顺序，不能先挑相机模块再寻找失败。当前原实现把请求相机传给 GA，硬冻结全部 pose 和旧 depth prefix；focal、新 depth、pairwise 变换等仍由原优化器处理。输入目标是 anchor0 self/conf_self 与其余 other/conf；最终 world pointmap 由优化后的 depth/focal/pp 和固定相机重建。它没有直接消费 raw camera_pose；非首帧 self-depth 也不是这份 GA 的目标。证据为 [S25 原代码路径审计](../S25_consumer_relevance/consumer_relevance.md)，固定 VMem commit `39291e4f272f6b4f270691d930926ab5930f942e`。

所以，“图像-only 网络未在前端接收相机”与“整个 pipeline 没利用相机”是两件事。前者仍可能留下问题；后者在原 VMem 中已不成立。网络里的 S/M 每次重放全部历史时重新建立，也不能写成跨生成 chunk 持久 state；外层 Surfel 等历史才持续。旧 Surfel 正常 merge 不覆写坐标的已否决路线不重开。

## 2. 五个最近原论文：四轴核对

本表只核作用对象、机制、输入粒度、setting；不搬论文榜单作本项目效果证据。版本和作者在 `sources.json` 中可查。

| 原论文 | 作用对象与机制 | 输入粒度 / setting | 与已 preset pose + old depth 的 VMem 关系 |
|---|---|---|---|
| **G-CUT3R**，Khafizov 等，2025；§3.2–3.4 | 模态专用编码器将 camera/depth 先验经 zero-conv 融入 CUT3R decoder；影响 pointmap、pose 及递归状态。[原文](https://arxiv.org/html/2508.11379v2#S3.SS2) | 顺序 RGB；每视图可有 K、pose、稠密/稀疏 depth+mask。需要训练扩展网络。 | 它在前端融合先验，VMem 在网络后硬约束几何；层次不同。但“相机指导 CUT3R state/pointmap”本身已有近邻。新增旧 prefix 场景不是充分机制创新。 |
| **Pow3R**，Jang 等，CVPR 2025；§3.1–3.3 | K 的 ray patch、depth+mask 进入 encoder；相对 pose 嵌入 decoder CLS；预测成对 pointmap。[原文](https://arxiv.org/html/2503.17316v1#S3.SS2) | 两张图及任意辅助模态；相对平移归一化，输出有尺度歧义；不是持续在线地图。 | 相比 VMem，有前端条件和两视图粒度差异；仍须把它给出的几何接入同一受约束消费者再比较。只把 pose 编成 token 不新；不能直接替代当前米制条件协议。 |
| **MapAnything**，Keetha 等，2025；§3–3.3 | 联合编码可选几何输入，以 rays、ray depth、pose、全局 metric scale 分解场景；多视图 attention 传播信息。[原文](https://arxiv.org/html/2509.13414v1#S3) | N 视图；各模态可仅存在于部分视图；支持 central camera ray 表示。不是本项目的 streaming S/M 写入规则。 | “所有 pose + 部分 depth 可用”的输入模式已被支持；已知相机改善几何不是新 setting。其 ray depth 和我们的 z-depth 需明确转换；更换 backbone 的收益不能归给记忆机制。 |
| **TCO: Learning 3D Reconstruction with Priors in Test Time**，Zhou 等，CVPR 2026；§3.2–3.4 | 对 pose/K/depth 输出施加先验惩罚，加跨视图渲染兼容目标；冻结 encoder/heads，以 LoRA 调整共享 decoder。[原文](https://arxiv.org/html/2604.03878v1#S3.SS2) | 多视图集合，测试时优化网络；实验 backbone 为 VGGT / π³；没有验证本项目的旧 prefix 固定 GA→Surfel 链。 | **最直接排重项**：“已知相机经共享表示改善未知几何”已明确提出。它的先验软惩罚和尺度处理不等于 VMem 硬冻结；换成 state 变量或保留原 GA 仍须证明具体新机制。 |
| **RayMap3R**，Wang 等，2026；§3.1–3.5 | 同一旧 state 上比较 image 主支与 ray-only 支；差异经 attention 映到 state gate，抑制动态内容，并处理 reset 尺度与轨迹平滑。[原文](https://arxiv.org/html/2603.20588v1#S3.SS3) | RGB stream；辅助 rays 来自主支**预测 pose**；双支推理无反传。目标为动态场景。 | 把辅助支改用已知控制相机，是输入来源变化；“ray-query→差异→gate”已不是新机制。静态结构变更、合法新物体、模型幻觉不能因差异大就一律当动态噪声。 |

几个易误读处：TCO 用输出惩罚求解，不承诺预测 pose 逐位等于先验；它的深度约束含尺度/平移对齐，几何评测也有自己的对齐协议，不能移植来美化本项目 raw-meter 主表。其 renderer / 网络适配不是免费操作。G-CUT3R 是训练后的架构扩展，不是将未训练编码器插入当前 CUT 即可生效。RayMap3R 的辅助相机是预测量，不是外部已知控制量。这些机制差别是真实差别，尚不等于我们的新颖性。

## 3. 致命缺陷先行：当前判决

对“把已知相机反馈到 pointmap / state 就是创新”的宽泛版本，`idea-evaluator` F1 检测问“比单个最近工作新增什么”。TCO 和 G-CUT3R 已分别覆盖测试时约束及前端融合；RayMap3R 覆盖 ray 差异门控。此版本没有特定新增机制，判 **Reject and Pivot**，不再用五维高分装饰。

第二个风险是 F9：目前没有本轮已核的实际消费者失败，不能先决定改 state，再将任意非零误差当动机。这里保留的是待测问题，未宣称被数据反证，也未替它评分。现阶段最有价值的是完成真实强基线，并核错误到底剩在哪个被消费的量。判决只拒绝上述泛化方法叙事，不等于证明所有相机约束研究无价值。

## 4. 最便宜的 control 与逐级否决条件（均未执行）

1. **现在的最低成本门：完成已安排的 S26 原消费者评分。** 复用已存三基线 heads、共同相机、共同 old depth、原 400 iter GA，不添加新前向。看新4的同分母 raw-meter depth 及给定约束保真；old4 不混进主均值。只完成运行或出现数值差异都不等于发现机制失败。8 张已见 GT、约 0.236 秒片段只能给兼容与局部组件线索。
2. **源码级 no-op 对照：** 对原 GA 最终点 `X=T·(d K⁻¹u)`，保持同一 T、K、d，仅再把它投到该像素的同一射线，不会提供新几何证据；精确算术下是恒等。这是参数化事实，不是本轮执行的测试。若“新方法”只是这种后置重写，应立即否决；更改 K、d、可见性或 mask 后就不是 no-op，须另列真实改变与代价。
3. **有实际失败才允许下一步对照：** 先将拟议方法与原 GA、同输入的普通输出空间受约束优化相比；固定相机 / 旧 depth / 分辨率 / 全有效 GT 分母，分别统计网络、适配、GA 的实际成本。不能额外给候选传感器 depth、真实 K 或更多迭代却宣称同条件胜出。普通输出优化已解决同一错误，则拒绝“必须改在线 state”解释。若收益只在未被消费者读取的 pose/self head，或只来自删远点/低conf点，拒绝 proposal 依据。
4. **升级为机制前的必要门：** 需要预先选定的更长自然事件 / 独立新数据，证明该错误改变 Surfel 候选、可见性或 context；需保留全部方法与失败帧。只能在定位后选合适控制，不能在本报告中虚构一个“受约束 GA 已失败”的阈值。若正常片段缺可归因的持续问题，停止此片段的机制实验，既不造噪声刷收益，也不为已写 adapter 强行续跑。

即使未来某个 state 干预有效，还必须排除普通相机条件、TCO式共享表示优化、ray门控、额外预算和更强 backbone。完整生成实验目前资源未齐，本轮没有启动、下载权重或用其他生成器代替原模型。CPU 代码诊断与已有 heads→GA 可在本机推进；论文中的训练、LoRA+可微渲染或双支网络在这台 M3 Max 上的兼容 / 成本未验证，不能承诺直接可跑。

## 5. 本轮真正执行的 skill 步骤

- 全文读 Supervisor handbook `02_Idea_Generation/2.2_想Idea的思路_更高更快更强.md`：按现有最强 baseline 与错误根因顺序，选择“更高”的消费者终点，拒绝以无关 pose 代理获益代替主线。
- 读 `idea-evaluator/SKILL.md` 与 `references/fatal-flaws.md`：执行 F1 检索与 F9 缺少真实失败的前门；通用方法版本已拒绝，因此没有伪造生命周期、五维得分或颠覆性结论。
- 延续本会话已读的 Claude 本地 `sci-scientific-critical-thinking/SKILL.md`：区分构念、已知控制、软/硬约束、计算混杂、已见数据和因果可解释性。没有调用 Claude 模型或 CLI。

这是五篇原文方法节的限范围核查，含2026近邻；不是完整综述。检索没有发现完全相同消费者链的论文，不构成“学界未做过”的证据。主账和 S26 冻结文件由父任务维护，本报告只交付有依据的排重与下一门。
