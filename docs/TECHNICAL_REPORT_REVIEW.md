# 技术报告预审记录

范围：课程阶段性技术报告TECHNICAL_REPORT.md，不按新算法顶会论文评判，不代表导师认可或原项目已经完成。采用本机pre-submission-reviewer技能的逻辑、语法、格式、图表、词汇检查，先读取全部正文及技能引用规则，再对照S0/S1/S3实际数据。引用句另有fresh-context独立核验；此审查由主任务执行。

## 结论

未发现需作废当前部件报告的CRITICAL问题，未发现新的未处理MAJOR证据问题。发现3处MINOR清晰度问题并已修正。作为本地阶段报告可交人类审阅；原proposal的学习式估计、完整视频和课程活动依然需要各自证据。

## 逻辑与文字

| 检查发现（修订前） | 严重性 | 已落实的修改 |
|---|---|---|
| “when a stored surfel position is changed”只给抽象问题，具体办公室例子较晚出现 | MINOR | 在Introduction加入围绕办公室桌子的相机例子，4.4用按时序最早的测试查询回接，真实最终索引[12,0,4,13]。不根据表现挑选例子。 |
| “ElasticFusion and probabilistic surfel fusion ... uncertainty-aware fusion”可能混淆不确定性机制的归属 | MINOR | 按独立引用审查拆为ElasticFusion重复观测更新与概率融合显式不确定性建模两句归属，并补VMem源码链接。 |
| “Figure 1. Unmodified measurements...”等图注先写设置，主要发现不够直接 | MINOR | 三图说明分别先写主设置支持不变、换图依赖条件、地图数量/预测覆盖下降，再列分母与限制。 |

six-paragraph Introduction包含背景、既有工作、问题、难点、方法、实际交付。交付均指向对应实验章节。主结果报告0/8换图、0百分点支持差，同时保留MAE约260mm、共同像素3.908%、采样敏感性和不利条件。没有将4,544检查、144行或72条件称作独立实验样本。两条记忆规则后续匹配可以不同，因此报告不作固定对应的单因素位置归因。nearest_pose4还取消NMS，正文明确这一点。

## 语法与篇章

依据G1–G6检查冠词、主谓、时态、句子复杂度、限制性从句和被动表达，未发现影响意义的明确语法错误。Results以表格当前事实为主，实际执行日期明确；不存在需要虚构实验叙事的时态修补。Discussion中“... summaries, yet ...”已拆为两句，属于G4可读性修订，不是科学结论变化。

## 格式与图表

本报告为Markdown技术正文，不适用LaTeX宏、页数上限、公式编号检查。3张图已逐张目视检查，PNG供预览，对应PDF保留矢量文字和标记。图形采用颜色与点形区分，图注交代同一环境/相机复用/支持定义。真实输入照片用于中文报告时保留TUM来源说明。未把原始照片这种本来是栅格的数据误判为图表质量问题。

## 全文词汇扫描

完整扫描记录results/report_vocabulary_scan.json，未发现连接句子的em-dash。初次发现“non-rigid surface correction”“do not demonstrate superior video generation”“yet”各1处。第一项是ElasticFusion的技术术语，保留；第二项本身是否定过强结论，仍改为better；第三项拆句。没有性能宣传、新颖性夸张或三次以上重复禁词。扫描范围是全文，不是抽样。

## 检索补查与范围

再次检索了“surfel indexed view memory video generation”和“3D reconstruction surfel memory uncertainty fusion”。原报告的VMem、I3DM、CUT3R、Spann3R及融合先例覆盖本次部件对照的直接定位。另有可扩展阅读如[SurfelNeRF, CVPR2023](https://openaccess.thecvf.com/content/CVPR2023/html/Gao_SurfelNeRF_Neural_Surfel_Radiance_Fields_for_Online_Photorealistic_Reconstruction_of_CVPR_2023_paper.html)和[EGG-Fusion预印本](https://arxiv.org/abs/2512.01296)，涉及不同的表面表示/渲染目标；本次检索仅用于范围判断，未据摘要引用其性能数值。报告本来不宣称穷尽文献或平均更新具有新颖性，故不将这些扩展阅读冒充已复现实验基线。

## 最终评价

阶段性报告完整度8/10，CRITICAL 0、未处理MAJOR 0、已修正MINOR 3。可用于阶段研究讨论；不标记为原项目已具备最终提交资格。当前剩余工作是公开标注的实验证据，不通过润色把它们隐藏。
