# 最新科研进展

更新UTC：2026-09-06T19:35:24.670761+00:00；北京时间=UTC+8。

**完成了两项关键验证：优化器把较准确的起点改差了；简单恢复整体尺度可以补救一部分，但还不够。**

| 同一组真实照片的深度结果 | 平均相对误差（低更好） |
|---|---:|
| 不优化的起点 | **5.04%** |
| 原400步优化后 | 42.38% |
| 再做普通整体尺度恢复 | **11.57%** |

S30实际做了两组各400步本机几何优化；S31复用保存结果，只从预测自己的起点计算一个比例，没有用真实深度调比例。两项都完成不同公式复核，完整分数、失败、时间和源码已记录。

S32A已按时间规则固定四个新片段、实际跑完16张真实照片的模型推理，约50秒，全部预测已保存核验。B仍待执行：保留同起点的零步/原400步/单比例恢复三个对照；一窗缺相机，保留NA不替换。上表是此前S31原四帧结果，新片段还没有深度分数；尚无新算法或完整视频结论。

- [S32A本轮：16张新片段照片的真实推理与时间](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/S32_A_RESULTS.md>)
- [S31文件夹：照片、六端点对照表、源码与复核](</Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/S31_尺度恢复后仍输给起点_2026-09-07/先读我.md>)
- [S31完整报告：三对照、分解和实际复核](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/S31_RESULTS.md>)
- [S30文件夹：4张实拍、两图、完整分数和800步记录](</Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/S30_优化损坏准确起点的真实证据_2026-09-07/先读我.md>)
- [此前796帧强基线](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/S24_RESULTS.md>)
- [当前科研记忆和明确下一步](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/RESEARCH_MEMORY.md>)
- [每一步的北京时间记录](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/RESEARCH_LOG.md>)

Supervisor第2章和本地Claude科研skills用于“强基线→失败→原因→方法”，并行实现、源码审查、原文检索和独立数学复核。PhD深度/CCF A投稿质量仍是目标，尚未达到。S31简明快照已完成，附4张原始实拍及完整对照与复核。
