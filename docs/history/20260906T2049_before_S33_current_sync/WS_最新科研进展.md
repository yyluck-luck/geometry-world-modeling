# 最新科研进展

更新时间UTC：2026-09-06T20:10:08.793675+00:00（北京时间UTC+8）。

**已完成四个固定片段的真实推理和三种对照，发现普通整体尺度恢复在两个片段上已经很有效。** 因此先检验优化为何让整体尺寸漂移，再从普通方法仍解决不了的问题提出创新。

| 固定片段 | 不优化的起点 | 原400步 | 恢复整体尺度 |
|---|---:|---:|---:|
| fr2_desk_j1 | NA | NA | NA |
| fr2_desk_j2 | 11.49% | 40.01% | 12.33% |
| fr1_xyz_j1 | 13.21% | 17.46% | 13.20% |
| fr1_xyz_j2 | 10.16% | 19.31% | 10.21% |

表中是深度平均相对误差，越低越好。第一窗缺相机配对，保留缺失不换片段，全部四窗均值仍为NA。恢复尺度后不同指标有好有坏，不能称已经统一胜出。

本轮16张真实照片实际进模型、3个可用窗各做400次优化；完整48行评分及1200步保存记录通过不同作者数值复核。完整视频尚未运行，没有把普通尺度处理称为创新方法。

S33已实际完成三个新400步，主评分中三窗AbsRel/RMSE/δ1均优于各自零步和事后k；新AbsRel为10.82468/12.63547/9.05079%。完整64行=旧48原样导入+新16，缺窗16NA保留。独立数值复核准备中，主结果尚不作为独立核验完成。 [本轮主结果与边界](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/S33_RESULTS.md>)。上表仍是已封存S32结果；完整四条件图/交付正在整理。

- [S32完整交付文件夹：16照片、图、分数及全部记录](</Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/S32_新片段三对照与真实照片_2026-09-07/先读我.md>)
- [S32完整实验结果、失败记录和实际时间](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/S32_RESULTS.md>)
- [16张真实照片的已有文件夹](</Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/S32A_四个新片段真实推理_2026-09-07/先读我.md>)
- [接手用科研记忆](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/RESEARCH_MEMORY.md>)
- [逐步北京时间日志](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/RESEARCH_LOG.md>)
- [下一实验：假设、普通强对照、反例、停止规则](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S32_next_decision/review.md>)

遵循Supervisor02_Idea_Generation、idea-evaluator和本地Claude科学批判技能，分工执行、检索、独立审查与记录。PhD深度/CCF A投稿质量仍为目标，尚未达到。
