# learning_research 阅读与本项目的实际改变

本轮接续记录日期：2026-09-08。逐文件身份见 `learning_research_tracked_file_coverage.json`，外链范围与实际记录时间见 `learning_research_external_coverage.json`。此文是阅读总结，不是原文备份或新方法成果。

## 已经读完什么

固定仓库 [pengsida/learning_research](https://github.com/pengsida/learning_research/tree/6fdbcdfe24167feb7164d5625a477c75bd118040) 的 **4 个跟踪文件全文已读**：README、changelog、getting_started_in_research、getting_advanced_in_research。它们以研究能力、项目推进和资源索引为主，许多实质建议放在 Notion 外链。

本轮继续读完下面 **8 个核心外链的可见文字**。Idea、失败分析和 Research Project 的折叠项已经展开读取。网页内另链的论文、视频、课程、图片和附件不因此算读完；不是“整个 Notion 网站全部读完”。此前保存的 `*_rendered.txt` 只是折叠状态文本，不能当展开全文的备份。此次展开阅读的直接证据是本会话 CUA 页面返回，范围记录是阅读回执，不伪造全文哈希。

| 已读页面 | 作者的主要建议 | 对本项目的落实 |
|---|---|---|
| [Research Project](https://pengsida.notion.site/Research-Project-b43507ef26d044bd888ac29f4736e116) | 先建立重要问题与技术挑战的结构，再搜索可能的解法、实验、分析、展示 | 让“基线到底失败在哪里”决定方法；不按审查文件数量推进论文进度 |
| [如何提出 idea](https://pengsida.notion.site/idea-da6ce171c13846b7a7ffaa7473ffa6ea) | 从有价值的目标、新场景和现有技术的实质困难出发；不要先迷恋一个方法再替它找问题 | 不保护已经被近邻或反例否决的共享权重、普通 gate、geometry routing；没有合格方法就如实保留空位 |
| [分析实验不 work](https://pengsida.notion.site/work-1aee6e718de6472f834d13da8f4ff097) | 同时看成功与失败；拆小问题；依次排查代码、参数、数据和机制；分析失败本身不等于新想法 | C2 收到终止信号是运行失败；C1 守卫错误是工程失败；二者都不能算算法失败证据 |
| [针对技术问题设计 solution](https://pengsida.notion.site/solution-997f611cd2e24ef1a62210ff099948e2) | 找其他领域是否遇到同一种技术困难；组合解法前先理解原因和假设 | 用 ICML 的历史条件与竞争解释实验思路完善判断，不能把别人的工具改名为我们的方法 |
| [给定 Idea，设计探索性实验](https://pengsida.notion.site/Idea-849f6606e5fb49b5b73a3778de64e43e) | 减少一个实验同时探索的问题和技术困难；简化设定时保留关键挑战 | 先测一条已选择来源的实际消费作用；不同时改模型结构、相机、来源和评价标准 |
| [怎么做实验记录](https://pengsida.notion.site/caf34717f4c046c69ee7e14ea953c46f) | 目的、设置、正负结果、分析、下一步 | 延续本机 append-only 主账；每个实验记录下一判断，不只堆运行日志 |
| [探索性实验应遵循最小可行性](https://pengsida.notion.site/2863fe292ff180759413f51ed1d1fdc3) | 在投入复杂系统前，先用少量资源验证核心前提；保证可重复，不追求完美系统 | 不扩展已经不适合本机的完整 RAIMA 确认队列；先完成当前 C1/C2 可信基线和一个可否决的判别 |
| [基于第一性原理设计方法](https://pengsida.notion.site/e5cc4f108cc4414d82abbf7b8e31dfae) | 从强方法的失败反推本质原因，再寻找解决该原因的技术 | 对“历史被选中就有用”的默认假设逐级检查；由机制需要决定数学工具，不先加模块 |

Research Project 三组表已展开；Idea 主折叠及后续 11 个 Open、失败分析 15 个 Open 已展开到无剩余可见 Open。其余五页在读取时没有待展开的正文。计数只是当时界面观察，不是网站固定版本。

## 采纳建议时保留判断

这些材料是作者的经验指导，不是统计或数学定理。页面中“旧技术没有提升空间”“可行性必须二元”之类表述不机械照搬：旧工具也可能解决一个新的重要问题；小样本实验也可能因噪声或识别不足得到不确定结论。不能为了得到明确答案删控制、改阈值，或把一个成功例子直接升级为完整方法验证。页面中的商业史例子没有另行核实，本项目不引用其数字。

Supervisor handbook 2.2 的强基线→失败→根因和 2.3 的隐藏假设、第一性原理保持主流程；pengsida 材料补充如何缩小实验和提高判断效率。本地 Claude skills 用于检索与科学批判，没有调用 Claude 模型。

## 对当前创新路线的决定

以“回到同一间房间，历史照片为什么没有帮助恢复同一细节”作为容易理解的目标。先验不足时不能断言存在该失败。VMem 的语义均值支路与保留来源的 latent 支路都是已知路径；当前未测实质冲突、空间定位或真实收益。

下一份实验必须能够区分四种解释：语义路径在当前条件下作用很弱；语义只改变全局外观；两路确有与相对几何相关的共同作用；最终差异只是后续采样/解码的非线性。新的 S55 建议仅增加同一起始状态的首个去噪输出记录，帮助定位解释，不能单靠它选新方法。

冻结新方法前仍需强近邻四轴比较、明确假设和可推翻预测、公平基线、独立真实参考与可完成的预算。`NO_METHOD_SELECTED`、`new_method_validated=false`。阅读使研究判断更清楚，但不增加经验证原创贡献数量。
