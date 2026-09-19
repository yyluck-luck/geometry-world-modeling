# 最新科研进展

更新UTC：2026-09-06T18:27:03.841698+00:00；北京时间=UTC+8。

**真实实验发现：原本较准确的深度，被优化器越改越差。** 保留原预测尺度时，初始平均相对深度误差5.04%，400步后42.38%；程序的loss却从7.16降到0.01064。另一初始尺度臂83.34%→87.47%，同样变差。

本轮确实在本机做了两组各400步几何优化，复用真实照片的已有预测，没有再次运行神经网络。不同作者已复核全部16条评分、66个初态张量和800步记录，最大数值差只有2.22e-16。四帧已经用于探索，给定相机使用真值；还不能据此宣称新方法、跨场景效果或视频生成成功。

下一步先用保存结果区分“整体缩小”与“不同位置的变化”，只从预测自身起点求一个尺度，不按真值调参。S31仍在准备，尚未执行；普通尺度修正若已能解决问题，就作为工程基线。

- [S30完整文件夹：4张实拍、图、16条评分和800步记录](</Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/S30_优化损坏准确起点的真实证据_2026-09-07/先读我.md>)
- [S30完整报告：真实数据、运行时间和复核](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/S30_RESULTS.md>)
- [S29报告、4张原始实拍和完整核验](</Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/S29_初始化尺度的真实证据_2026-09-07/先读我.md>)
- [S28图、4张实拍与逐步记录](</Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/S28_梯度修复负结果与下一步_2026-09-07/先读我.md>)
- [此前796帧强基线](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/S24_RESULTS.md>)
- [项目当前记忆](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/RESEARCH_MEMORY.md>)
- [每步时间记录](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/RESEARCH_LOG.md>)

按Supervisor第2章“基线→失败→根因→方法”推进，使用本地Claude科学批判技能、官方原文与源码检索、并行实现和审查。PhD研究深度/CCF A投稿质量仍是目标，尚未达到。S30结果图和实拍快照已完成。
