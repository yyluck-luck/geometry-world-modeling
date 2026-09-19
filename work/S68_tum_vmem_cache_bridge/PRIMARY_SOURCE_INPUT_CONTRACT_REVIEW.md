# S68原文定点核查：参考输入与查询信息边界

记录UTC：2026-09-09T01:05:48.754962+00:00。root实际使用web检索及作者HTML，未调用Gemini或Claude模型。本次为接口/问题边界核查，不进行新的方法评分。

| 方向与原文 | 本次实际读取范围与可用事实 | 对当前决策的限制 |
|---|---|---|
| 最近邻：[VMem](https://arxiv.org/html/2506.18903v1)，Li等，ICCV2025；正式身份另核[作者项目](https://v-mem.github.io/) | §3.1–3.2：按未来相机查询历史，再把所选照片和相机交给生成器。 | 旧S8读取目标照片估计查询相机，不等于此无目标图像的生成输入合同。五来源编码只是已有部件的接线。 |
| 简单替代：[WorldStereo](https://arxiv.org/html/2603.02049v1)，Zhang等，CVPR2026；正式PDF由[CVF](https://openaccess.thecvf.com/content/CVPR2026/papers/Zhang_WorldStereo_Bridging_Camera-Guided_Video_Generation_and_Scene_Reconstruction_via_3D_CVPR_2026_paper.pdf)检索命中 | §3.3：3D视野重叠选择，各参考独立编码，参考/目标成对注意力。 | 分来源保存latent或几何选择都已有先例；桥接不能称新方法。 |
| 可迁移的信息合同：[Mem-World](https://arxiv.org/html/2606.18960v1)，Zheng等，2026-06-17预印本；本轮未核正式录用 | §3.1–3.2及算法1：未来腕部相机由动作、正向运动学及标定推得；含时间/任务属性的surfel分别渲染并检索。 | 可迁移的是明确查询相机来自哪些允许输入。机器人动作、标定多视角和动态标签不是本项目单相机照片自动拥有的信息；不将其成绩移植成本项目收益。 |

三篇都提供明确输入条件，不能只比较“选了四张图”这一表面行为。root推断：旧固定集合可用于已见、事后条件化的生成对照；真正目标图像不可见的在线选择须另立相机输入合同。该推断不是三篇论文对本项目的实验结论。

Mem-World为本轮新检索近邻，进一步限制普通动态surfel/时间权重的创新主张；目前没有提出这样的新方法，也没有据未检出结果声称首创。只阅读上述方法相关范围，不声称完整论文/全部补充实验已核。WorldStereo正式PDF本轮为检索命中，不冒称下载全文。

检索词：VMem video memory camera pose paper；WorldStereo reference field camera；GEN3C camera cache ICCV2025。最后一条检索词含待核会议名，实际CVF结果明确GEN3C为CVPR2025；只作元数据纠正，不据此新增方法精读。工具目录未发现已连接的独立Scholar/Consensus接口，本轮使用web主来源；未调用Google Scholar，不声称用过。早期vendor/VMem README大小写猜测路径被zsh拒绝，随后rg定位实际vendor/vmem_snapshot与已固定isolated源码，无文件变更或实验影响。

当前仍NO_METHOD_SELECTED / novelty_authorization=NONE / new_method_validated=false。本轮数据桥接只需原组件源码和固定权重，不需要重复Gemini概念咨询；已授权Gemini接口并未被判为不可用。
