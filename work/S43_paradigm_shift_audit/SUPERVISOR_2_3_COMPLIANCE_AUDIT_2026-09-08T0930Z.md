# Supervisor-Skills 2.3 严格遵循审计

- 审计时间：2026-09-08T09:30:27Z（北京时间17:30:27）
- 本地技能仓库commit：`207bc6f7a1aa107e544099c2c7cc86816fba9628`
- 重点文档SHA-256：`c4a0022cad1bfeb09301d3b78e16f2197693bd170d613e6a2be5e45c73266b59`
- 对象：`INNOVATION_NORTH_STAR_V2.md`
- 结论：`COMPLIANT_AS_A_RESEARCH_DECISION_PROCESS; SCIENTIFIC_NOVELTY_NOT_YET_ESTABLISHED`
- 新模型运行：`0`

## 1. 第一性原理

技能要求不要先拿现成方案找问题，而要回到任务目的并拆隐含假设。

本项目回到的原始目的不是“让模型拥有更大的memory”，而是：历史证据必须使长时世界生成更真实、更一致，并且其作用能够被追责。

当前被检验的隐藏假设是：

> `stored/retrieved/addressable` 可以近似代表 `actually used/correctly localized/beneficial`。

GeoCausal把该假设拆成`Store → Select → Address → Influence → Localization → Benefit`，并要求用matched intervention与独立自然重访reference检验，符合第一性原理路线。

未完成边界：目前没有真实S48 arm，因此隐藏假设尚未被数据推翻。

## 2. 房间里的大象

技能要求直面主流benchmark容易回避的真实痛点与极端失败。

本项目选择的大象是：长期视频论文可以报告整体质量、检索命中或重访一致性，但这些指标可能无法说明某条被选中历史证据是否真的改变输出、改变了哪里、帮助还是伤害。

V2冻结五种候选反直觉现象：

1. 检索正确但没有实际作用；
2. 有作用但落在错误位置；
3. 几何位置正确但净收益为负；
4. 单来源收益随共同来源集合变号；
5. 总体分数掩盖来源责任断裂。

未完成边界：这些目前是corner-case hypotheses，不是观察到的真实规律。

## 3. 技术周期前瞻

技能要求思考新底层能力是否允许重新定义问题。

当前技术窗口是：VMem、Spatia、WorldStereo等系统开始暴露显式3D记忆、来源索引、目标几何和多条appearance-conditioning路径。过去隐式长上下文很难逐来源干预；显式来源身份现在使“memory accountability”成为可执行实验。

这只说明问题现在可研究，不自动证明问题或方法新颖。若第二架构没有稳定source ID，V2禁止外推成通用世界模型定律。

## 4. Hamming重要问题

技能要求把精力放在一旦解决会真正改变能力边界的问题。

重要问题表述为：

> 一个长期交互世界模型在普通运行时，能否知道某条历史证据会帮助、无效还是伤害下一次生成，并在不看未来真值的条件下采取正确动作？

它的重要性来自长期交互：记忆不断累积后，少量有害或错位证据可能持续传播。它仍需真实失败率、伤害量和跨架构复验支撑；若事件罕见或普通gate已完全解决，则降级，不靠“大问题”措辞保住论文。

## 5. 与2.2“更高、更快、更强、更省、更广”的保底结合

| 维度 | 当前可执行目标 | 失败/降级条件 |
|---|---|---|
| Higher | 降低独立自然重访reference loss，并保持相机服从 | 只改善内部一致性，不改善真实端点 |
| Faster | 用生成前学生替代昂贵全路径因果教师 | 学生推理成本或额外采样抵消收益 |
| Stronger | 跨scene、seed、source、动态/遮挡条件保持校准 | 只记住已见scene/source |
| Cheaper | 在固定重观察与采样预算下减少无效/有害memory消费 | 优势只来自更多test-time compute |
| Broader | 在第二个stable-source架构重复责任断裂 | 只暴露VMem global-mean semantic实现bug |

当前只有Higher/Stronger的测量目标，五维结果均未建立。

## 6. 方案否决记录证明流程没有“护题”

1. 普通coverage greedy因COVRAG/I3DM/AnchorWeave/VMem等近邻被否决；
2. PC-DPM hard shared weights因consumer专业化数学反例与统一attention基线被否决；
3. generic stale-memory reject/refresh因GaME、Spatia、WorldMM、WorldCraft、SPMEM被否决；
4. Address分层、reference-based scoring、hierarchical evaluation分别被MomentSeeker、Ref4D、Hi3DEval占据，不能单独称创新。

这符合技能所要求的“不要拿斧头找木头”：方法名字可以被删除，真实问题必须由baseline失败留下。

## 7. 当前不满足2.3的地方

- 没有多场景真实自然失败；
- 没有Influence/Localization/Benefit因果结果；
- 没有证明这些断裂是领域大象而非单一实现bug；
- 没有方法胜过强基线；
- 没有第二架构复验；
- 没有资格使用`first/novel/paradigm shift/PhD-level/CCF-A-level achieved`。

因此“严格遵循skill”当前只意味着研究决策过程合规，不意味着已经产生颠覆式创新。

## 8. 下一步必须做的事

1. 完成C1/C2合法baseline cohort，先盲态确认P0自然失败；
2. S48 V6经过两名不同作者fresh审查后，只在P0通过时执行；
3. 用F00/F10/F01/F11、两类edit、same-path zero、sham、negative/positive control测P1/P2；
4. 用pairwise/factorial replacement测P3来源交互；
5. P0–P3任何一项失败就缩小或终止方法；
6. 只有存活后才实现independent/hard-share/soft-consistency/per-source-token/trust-gate/unified-attention等强对照。

## 9. 一手入口

- Supervisor-Skills 2.3：<https://github.com/HKUSTDial/Supervisor-Skills/blob/main/handbook/02_Idea_Generation/2.3_%E8%BF%9B%E9%98%B6_%E5%A6%82%E4%BD%95%E5%81%9A%E9%A2%A0%E8%A6%86%E5%BC%8F%E5%88%9B%E6%96%B0.md>
- Supervisor-Skills 2.2：<https://github.com/HKUSTDial/Supervisor-Skills/blob/main/handbook/02_Idea_Generation/2.2_%E6%83%B3Idea%E7%9A%84%E6%80%9D%E8%B7%AF_%E6%9B%B4%E9%AB%98%E6%9B%B4%E5%BF%AB%E6%9B%B4%E5%BC%BA.md>
- 创新北极星V2：`work/S43_paradigm_shift_audit/INNOVATION_NORTH_STAR_V2.md`
- 独立碰撞审查：`work/S43_paradigm_shift_audit/PC_DPM_NOVELTY_COLLISION_REVIEW_V1.md`

