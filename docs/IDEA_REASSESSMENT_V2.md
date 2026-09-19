# 构想重评：先结束过强主张，再检验机制

本评议在S6结果与3453项独立核验之后形成。使用Supervisor-Skills的idea-evaluator早期否决规则；新候选的主要贡献是评价与机制诊断，因此按该skill的路由交由benchmark-paper-template审查。两个判断不能混为“整个项目失败”或“已经找到新方法”。

## 1. 初步定位

原强主张可概括为：“把首次写入的地图位置改为逐帧平均，就能得到普遍更准确的几何、更好的参考和更好的世界模型。”这是方法型主张，三个效果需要分别得到证据。S6只比较了固定组件的几何与参考支持，没有运行生成器。

下面是真实检索、完整方法核对后使用的最近工作，不以标题相似断定重复。论文版本与具体段落见literature_v2中的证据表。

| 最近工作（标题、作者、年份） | 对象与机制 | 与原均值比较/新重放候选的关系 |
|---|---|---|
| ElasticFusion: Dense SLAM Without A Pose Graph；Whelan、Leutenegger、Salas-Moreno、Glocker、Davison，2015 | surfel融合、地图优化与形变 | 点位置融合本身已有长期研究；不等于生成参考选择 [原文](https://thomaswhelan.ie/Whelan15rss.pdf) |
| VMem: Consistent Interactive Video Scene Generation with Surfel-Indexed View Memory；Li、Torr、Vedaldi、Jakab，2025 | 来源集合、几何可见投票与NMS选历史RGB | 本项目直接使用其选帧核心；来源记录不是新发明 [原文](https://arxiv.org/html/2506.18903v3) |
| Spatia: Video Generation with Updatable Spatial Memory；Zhao、Wei、Liu、Zhang、Xu、Lu，2025 | 可更新空间记忆、投影及参考条件 | 已做模块组合消融；新候选拟把干预粒度下移到固定观测的关联事件 [原文](https://arxiv.org/html/2512.15716v1) |
| AnchorWeave: World-Consistent Video Generation with Retrieved Local Spatial Memories；Wang、Lin、Yoon、Cho、Zhang、Bansal，2026 | 局部几何记忆、覆盖检索和多anchor条件 | 已处理全局融合问题；其平均条件消融不是坐标均值，新候选不得混淆 [原文](https://arxiv.org/html/2602.14941v1) |
| Latent Spatial Memory for Video World Models；Wang等10位作者，2026 | 潜在三维空间记忆，比较不同深度来源 | 换估计器同时改变多种误差；固定原预测并重放事件是一种不同粒度的诊断设计，尚未证明文献空白 [原文](https://arxiv.org/html/2606.09828v2) |

## 2. 致命问题：CRITICAL，仅针对原强主张

**核心机制被现有对照限制。** idea-evaluator规定，若中心改善主张已被自身数据中的简单对照追平或超过，应直接Reject and Pivot，不再用分数或乐观阈值装饰结论。S3主测试参考完全不变；S6主设置均值支持93.271907%仍低于最近预测姿态4图的93.471823%，稀疏设置支持上升时共同像素MAE却从441.308变为447.767mm。S6只有8张测试查询、同一个环境；这些证据足以拒绝本项目目前的无条件优越性表述，不能用于证明“平均在所有地方无效”。[S3结果](S3_RESULTS.md)、[S6结果及限制](S6_RESULTS.md)。

原强主张包含未测试的视频效果，不能把这一部分伪称已经被数据直接证伪；它目前没有证据。几何误差仅在共同覆盖的稀疏像素上计算，自身覆盖下降，也不允许用一个误差均值代替整体几何质量。

## 7. 判定：Reject and Pivot

结束“简单平均是一种普遍更好世界模型方法”的故事，不作五维打分，不提供延续该强主张的辩护。保留所有代码、负结果和实际观察。后续转向一个不同的问题：固定同一批观测后，最终位置、关联轨迹和读出规则分别怎样改变参考决策？这属于尚未完成的新机制评价，不借旧主张的拒绝预先判定它成功或失败。

候选A/B/C及各自五项近邻、最小实验、失败路线见 [独立候选评议](NOVELTY_CANDIDATE_REVIEW.md)。本机算力已有实际成功证据；学生可投入小时数和独立研究能力没有已核信息，不虚构评分，也不把自动执行时间当学习工时。
