# 最新科研进展

更新UTC：2026-09-06T18:00:25.259254+00:00；北京时间=UTC+8。

**现在确认了两个具体问题。** 其一，修复梯度后深度真的更新了，但真实误差83.34%→87.48%，程序loss反而更低；其二，初始化中的约0.173倍尺度确实缩小了全部深度，单独改变公共平移不影响这一关系。

S28实际做了800步地图优化；S29另做两个初始化、没有优化或传感器评分。独立复核都已完成。真实照片、代码、原始数值与时间回执已留存；这些是组件证据，尚未生成新视频或证明新算法。

下一步S30准备比较：保留原预测的初始尺度后，继续同样400步优化是否能得到更准确的深度。两方都使用修好的梯度，评分规则预先固定。当前尚未运行S30。

- [S29完整文件夹：报告、实拍、逐像素核验与源码](</Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/S29_初始化尺度的真实证据_2026-09-07/先读我.md>)
- [S29初始化尺度的完整真实结果](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/S29_RESULTS.md>)
- [S28报告、图、4张真实照片与逐步记录](</Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/S28_梯度修复负结果与下一步_2026-09-07/先读我.md>)
- [此前796帧强基线](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/S24_RESULTS.md>)
- [项目当前记忆](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/RESEARCH_MEMORY.md>)
- [每步时间记录](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/RESEARCH_LOG.md>)

按Supervisor第2章“基线→失败→根因→方法”继续，使用本地Claude科学批判技能、官方原文/源码检索及并行实现和审查。普通工程修复不算论文创新；PhD研究深度/CCF A投稿质量的最终目标仍未完成。
