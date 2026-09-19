# 最新科研进展

更新时间UTC：2026-09-06T22:07:46.319799+00:00；北京时间UTC+8。

**这轮真做了800步优化和三次原地图渲染，结果与独立复核都已完成。** 固定前四张照片对应的旧深度，再用后四张照片比较三种普通处理。

| 条件 | 后四帧平均深度相对误差（越低越好） |
|---|---:|
| 不优化 | 4.6059% |
| 普通优化400步 | 4.3474% |
| 加入已有尺度约束400步 | 4.3221% |

普通优化已经提供大部分改善，额外约束只改善0.0253个百分点；相较不优化，第八张照片在两个优化条件下的深度相对误差仍略差。因此当前不能把尺度约束算作创新。地图和渲染确实变化，但三组候选照片仍完全相同；渲染焦距也不同，不能据此说视频更好。这里只用了一个已见短片段，且给定了真实相机。

**下一步回到完整生成：用第一批真正生成的图片，帮助生成第二批图片，检查缓存是否被实际用上。** 已有具体两批实验协议；当前缺可核实的原VMem主权重和原指定VAE，尚未启动。资源缺口与本机实际运行能力分开记录，不伪造缓存、不改用其他模型冒充原复现。

- [8张真实照片、结果图及全部日志](</Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/S34_固定旧地图三条件与真实照片_2026-09-07/先读我.md>)：220文件，8张原始照片、12行评分、两幅图、全部优化日志和复核回执。
- [S34完整报告](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/S34_RESULTS.md>)；[下一决策及源码依据](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S34_next_decision/decision.md>)；[最新有界资源检查](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S34_resource_refresh/report.md>)。
- [当前科研记忆](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/RESEARCH_MEMORY.md>)与[实际时间账](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/RESEARCH_LOG.md>)。

按照Supervisor第2章、本地Claude科学批判与idea-evaluator收束被证据削弱的方向。新方法和PhD/CCF A质量目标仍未达到；这一轮完成的是有真实证据的基线与问题排查。
