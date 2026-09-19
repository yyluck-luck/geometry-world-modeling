# 最新科研进展

更新时间UTC：2026-09-06T20:50:23.707580+00:00；北京时间UTC+8。

**已找到有效的基线改进：在优化时约束整体尺寸漂移，三个可评分片段的深度都比“不优化”和“事后恢复尺寸”更准。独立数值复核已经通过。**

| 固定片段 | 不优化 | 原400步 | 事后恢复尺度 | 优化中约束尺度 |
|---|---:|---:|---:|---:|
| fr2_desk_j1 | NA | NA | NA | NA |
| fr2_desk_j2 | 11.49% | 40.01% | 12.33% | **10.82%** |
| fr1_xyz_j1 | 13.21% | 17.46% | 13.20% | **12.64%** |
| fr1_xyz_j2 | 10.16% | 19.31% | 10.21% | **9.05%** |

表中是深度平均相对误差，越低越好。另两项指标RMSE与δ1也同时改善。第一窗缺相机配对，保留缺失、不换片段，全部四窗均值仍为NA。这些是两个已使用场景的短片段和给定真实相机条件，不能称跨场景盲测。

本轮S32实际让16张实拍照片进模型，S32/S33合计做了2400次新优化；S33旧48分数原样保留，加入新16行形成完整64行。不同作者检查了评分、同一起点和每一步保存记录；完整结果及照片都在本机，不是模拟数据。

**下一步回到proposal主线：固定旧地图，再加入4张照片，检查原地图、渲染和参考照片票权的实际变化。** 已确定最小八帧方案，尚未实现或运行；完整默认选图和生成仍需合法历史状态及生成资源。

- [打开本轮完整文件夹：16张照片、图、评分、日志](</Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/S33_尺度约束四条件与真实照片_2026-09-07/先读我.md>)
- [S33完整科研报告](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/S33_RESULTS.md>)
- [接手用记忆](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/RESEARCH_MEMORY.md>)与[每一步时间账](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/RESEARCH_LOG.md>)
- [下一项消费者实验设计与停止规则](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S33_next_decision/review.md>)

严格区分已有方法和创新：这次先记为普通基线加固，尚未达到PhD深度/CCF A论文的最终目标。科研技能、原文排查、并行分工及实际流程检查均有记录；最近一次30分钟实查晚10.34秒，已保留异常。
