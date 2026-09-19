# 从这里看项目

我们在研究：AI怎样利用旧照片记住房间，并为下一视角挑选合适的参考。

现在已经完成真实照片、真实模型和记忆选图实验。最新一轮发现：移动三维点的效果，取决于此前照片怎样被归到这些点上；有时两种影响一正一负，最后的选图看起来完全没变。这比只比较“平均前后谁分数高”更能说明原因。

先看工作区outputs/新一轮研究结果中的中文结果报告、最新文献综述和真实结果表。outputs/研究机制图里有可编辑Draw.io、运行前假设设计PDF及LaTeX源。真实照片在outputs/实验用的真实照片_72张，ip-目录有同名入口；每张是原始相机照片的逐字节副本。

证据位置：docs/S7_RESULTS.md与S7_INDEPENDENT_AUDIT.md；上一轮docs/S6_RESULTS.md与S6_INDEPENDENT_AUDIT.md。25篇综述在docs/LITERATURE_SYNTHESIS_V2.md，创新候选及失败条件在NOVELTY_CANDIDATE_REVIEW.md、IDEA_REASSESSMENT_V2.md。简单平均已有前人且效果不稳定，不把它重新命名成发明。

最新实验已通过独立复算；仍只有一个环境、12个不同查询，主测试8个，尚未完成真实新视角视频生成。36秒旧演示是72张已观察照片和预测深度的并排回放。下一步应在另一个独立场景检验发现，再决定能否形成方法贡献。

本地记忆：RESEARCH_MEMORY.md是当前状态，RESEARCH_LOG.md列真实时间、动作、发现与下一步，research_events.jsonl只追加原始事件。自动运行不计作你的学生工时或导师会议。
