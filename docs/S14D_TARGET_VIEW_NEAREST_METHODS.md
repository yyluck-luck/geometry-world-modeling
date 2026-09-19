# S14D：目标视角诊断的近邻与输入边界

本轮是有限原文与官方代码核查，**没有新增数值实验、选图、模型运行或新颖性认证**。S14C 已否定的“历史质心越分散，两场景选图就都越差”版本继续停止。接续问题只能是：给定同样历史和目标相机，目标区域中的几何矛盾是否提供普通覆盖与传统一致性检查以外的信息。当前只是待操作化的探索假设。

## 四项最相关已有机制

| 原始工作 | 已有机制与实际读取位置 | 检索时可用的目标信息 | 本项目必须面对的基线 | 仍可证伪的差别 |
|---|---|---|---|---|
| Schönberger、Zheng、Pollefeys、Frahm，**Pixelwise View Selection for Unstructured Multi-View Stereo**，ECCV 2016 | 逐像素光度/几何视图选择；三角化、分辨率、入射角先验；前后向重投影误差参与深度/法向推断。实读作者 PDF §4.2/4.5，及 COLMAP `ComputeGeomConsistencyCost`。 | 传统 MVS 的参考图已经存在；有相机、源图与参考图像，深度/法向是推断变量。不能把参考图的光度或预测深度直接当作尚未生成目标的可用输入。 | 只在历史图之间做普通前后向重投影/深度一致性，再把可靠度投到目标视角；单独保留仅相机与来源数基线。这个几何分量的移植不是完整 COLMAP 复现。 | 若所谓联合冲突增益被同信息的普通 MVS 一致性解释，就保留基线，不成立新机制。 [作者原文](https://demuc.de/papers/schoenberger2016mvs.pdf)、[固定代码](https://github.com/colmap/colmap/blob/c2da617eadeb86aa0af9fa1cdb58c87839b6e5fd/src/colmap/mvs/patch_match_cuda.cu#L601) |
| Minseok Joo 等，**Retrieve What's Missing: Coverage-Maximizing Retrieval for Consistent Long Video Generation（COVRAG）**，2026 v1 预印本 | 源预测深度投向目标网格，最近像素命中置 1；上下文覆盖取 OR，再贪心增加尚未覆盖的像素。实读 §4.1–4.2、附录 A.4。 | 历史 RGB/预测深度、历史/目标相机；算法输入没有目标 RGB 或目标深度。A.4 用历史窗口预测平移与给定 metric/GT 轨迹的比值对齐尺度，再缩放目标位姿。 | 同历史几何、同像素网格、同候选/四图约束的 any-hit 覆盖；若未来比较选图，含独立 top-k 和残余覆盖贪心。改用 CUT3R 的版本须称“按定义实现的组件基线”，不称作者完整系统复现。 | 相同覆盖是否仍包含错面/遮挡导致的虚假支持；新增量须超出普通深度次序与 MVS 过滤，不能以换覆盖名称成立。 [§4](https://arxiv.org/html/2606.02479v1#S4)、[尺度接口](https://arxiv.org/html/2606.02479v1) |
| Jia Li 等，**I3DM: Implicit 3D-aware Memory Retrieval and Injection for Consistent Video Scene Generation**，2026 v2 预印本 | 冻结 LVSM 浅层特征配可训练 CNN，得到目标 patch 的负不确定度；逐 patch 最大值聚合、选择互补整帧，含最后帧 anchor。实读 §3.2、补充 §2，并核官方检索函数。 | 推理：candidate+last 的 RGB/相机及 target rays。训练 CNN 则使用合成目标与真实目标 RGB 的 MSE。附录明确展示的目标照片不参与检索；官方 `data_target_batch` 也没有 image。 | 同信息的单图可靠度/软覆盖聚合基线；若使用学习模块必须匹配目标监督、预训练与计算预算。只对比无学习覆盖，不能宣称胜过 I3DM。 | 四张整图之间的相互作用是否超出每候选与 anchor 的预测可靠度；还须排除普通 pairwise 一致性。 [原文](https://arxiv.org/html/2603.23413v2#S3.SS2)、[附录](https://arxiv.org/html/2603.23413v2)、[固定代码](https://github.com/Riga2/I3DM/blob/895033d098a683ad49ed945a8524dea327895fe4/scripts/frame_memory_retrieval.py#L166) |
| Runjia Li、Philip Torr、Andrea Vedaldi、Tomas Jakab，**VMem**，2025 | 将带来源索引的 surfel 从目标视角渲染，来源票数检索并做姿态 NMS；本地固定 pipeline 有 z-buffer。实读 §3.1 及已有 vendor 源码。 | 历史已观测/生成图的三维记忆与给定目标相机；完成一轮生成后才加入新图。 | 保留现有 G/P 固定动作，给所有诊断相同历史、目标相机与预算；比较中不能偷偷放松 NMS 或增加候选数。 | 目标视角或遮挡本身已有先例；必须定位来源投票在既定错误类型下缺少的额外信息。 [原文](https://arxiv.org/html/2506.18903v3#S3.SS1)、本地 `vendor/vmem_snapshot/modeling/pipeline.py` |

**覆盖、可见性与正确性须分开。** COVRAG §4.1 的已读定义是 any-hit 二值栅格，没有对目标实测深度核真；多源深度撞同一像素仍置 1。其覆盖有空间价值，但不能直接当作“这个像素真的未遮挡”的答案。加入 z-buffer 能处理给定几何中的近远次序；未观测遮挡物、共享深度偏差或错误位姿仍可使多张图一致地出错。此处是从定义作出的限制分析，不是本项目已经测得 COVRAG 失败。

## 当前数据接口和公平对照

生成新的目标图之前，真实目标 RGB 不存在。可部署的目标条件应来自给定轨迹/相机，且必须与历史预测几何对齐。COVRAG 的外部轨迹尺度对齐合同应明列，不能省略成“只需无尺度深度”。普通 MVS 使用已存在参考图像的接口与生成前目标不同。

本项目 `RESEARCH_MEMORY.md` 已明确：S7/S8 查询位姿依赖已见 query RGB。本轮读 `scripts/run_s7_replay.py:69–97`、`run_s12_matched_budget.py:208–235,324–331` 和 S8 输入合同，确认旧预测姿态文件被复用到 query 距离计算；未解码预测数组、原图或 GT。故新档案诊断即使完全不读 query depth/RGB，也只能称**给定旧估计 query 位姿的条件分析**，不能声称已移除上游 query RGB 依赖。更完整的输入数据流应由专门接口审计落定。

建议下一协议先固定 G/P 四图，不先开发选择器。普通量至少区分：①来源数/相机位姿；②目标 any-hit 覆盖与重叠；③历史图间 MVS 式前后向/深度一致性，投到目标的可检验区域。真正候选若是④目标区域的跨图冲突，必须说明它比③多观察了什么。所有方法共享历史图、深度、置信、坐标、网格、缺失值规则及候选信息；额外 pair、渲染、预训练或监督算入成本。未来真的选四图时，再为 residual coverage、软覆盖聚合等保持同一可行集合并独立计价。

可推翻预测：在覆盖与普通一致性相近的比较中，候选冲突仍应揭示额外的实测支持损失；若只是把上述量重新加权、效果完全由普通过滤解释、只靠删难像素/增信息/调已见阈值成立，则停止本版本新方法主张。S7/S8 的 24 个相关 query 只能检查可辨识性和反例；在它们上面找到相关也不是未见验证或因果证明。当前连新冲突定义都未冻结，因此不预告它会成功。

## 官方代码可得性与实际读取

- COLMAP 官方代码固定 commit `c2da617eadeb86aa0af9fa1cdb58c87839b6e5fd`；读 `patch_match_cuda.cu:601–670`，实现取源深度、投回参考像素、返回截断欧式重投影误差。没有编译或运行 COLMAP。
- 从 [I3DM 官方项目页](https://riga2.github.io/i3dm/) 的 Codes 链接核到 `Riga2/I3DM`，固定 commit `895033d098a683ad49ed945a8524dea327895fe4`；读 `readme.md`、`scripts/frame_memory_retrieval.py`、`scripts/eval_re10k.py`。检索接口直接使用 CUDA/BF16；没有下载权重/数据或运行它，不凭 README 保证本机 MPS 可用。
- I3DM 论文画布初始化为 0；已读代码初始化为 −∞，比较 `max(current,candidate).mean()`。初始化规则有实际差别，复现时必须绑定选用版本；尚未运行，不能宣称数值等价或定为作者错误。
- 六个定点搜索后仍未核到 COVRAG 作者代码链接；结论仅为“本次未找到”，不等于不存在。原文定义足够做透明的组件基线，仍需标明实现出处。
- 公开 HTTP 有两次 TLS EOF：第一次 `eval_re10k.py` 后续重试成功；`wan_scene_decoder_retrieval_occ.py` 未取得。本轮不依赖未取得文件作内部模型实现判断。失败回执保留。

## 技能与执行范围

实际读取 Supervisor `idea-evaluator/SKILL.md` 和 `references/fatal-flaws.md`：对已经数据反驳的 S14C 限定命题执行 Reject and Pivot；本轮只执行新方向的 F1/F6 前置近邻与可验证性核查，尚无具体新算法可作完整五维立项评估，不补乐观分数。四个最近工作按机制、对象和可用输入比较，不以题目相似或未搜到当重复/首创证明。

实际读取本地 Claude `sci-scientific-critical-thinking/SKILL.md`：应用构念效度、输入混杂、共享错误反例、探索与验证区分。该技能的默认图示建议已考虑；此任务是有界对照表和接口核查，表格已足够，没有为工具数量生成图、调用 Claude 模型或 CLI。

证据目录为 `work/S14D_nearest_methods/`，复用原文快照与哈希列于 `local_primary_reads.json`；新网络访问含时间、URL、大小、SHA 和失败回执。六个查询分两批，原始返回存 `web_search_receipts.json`，定点打开另存 `web_open_receipts.json`。本报告不是大综述、完整算法审计、正式预注册或真实效果报告。
