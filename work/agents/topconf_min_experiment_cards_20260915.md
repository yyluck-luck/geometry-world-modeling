# 顶会精读后的最小创新实验卡

审查日期：2026-09-15（Asia/Shanghai）  
审查身份：独立审稿式子任务；不代表论文复现或新颖性授权。  
当前状态：`new_method_validated=false`，`novelty_authorization=NONE`。

## 1. 选取的两个最接近工作

### Card V：ViewRope（Geometry-Aware Rotary Position Embedding for Consistent Video World Model）

**原文问题定义。** ViewRope 将长时程相机控制视频中的空间漂移归因于 screen-space
位置编码与 projective geometry 不匹配，特别关注“离开后回到原视角”的 loop closure。
它的目标是让注意力在不同时间的 token 之间恢复同一三维内容，而不是仅按图像平面邻近性
关联。论文同时提出 Geometry-Aware Frame-Sparse Attention 和 ViewBench。

**核心假设。** 在相机运动已校准时，patch 的 viewing-ray 相对几何比 `(x,y,t)` 局部性
更能预测跨时间的物理对应；按几何相关性选少量历史帧，在固定稀疏 attention 预算下应保留
回访一致性。该假设不是“风险校准能预测未来损失”，所以它是 SOCF/FGB-Future 的强
baseline/反证近邻，而不是我们方法的组成模块。

**算法步骤（原文机制摘要）。**

1. 用每个 patch 的相机内外参计算 viewing ray；
2. 将 ray 关系通过旋转变换注入 Q/K attention（保留原 RoPE 的互补通道）；
3. 估计 frame/block relevance，选 top-k 历史帧做 sparse attention；
4. 用 camera-controlled 长序列和 rotate-away–rotate-back 轨迹测试 loop closure。

**论文预算/评价事实（用于设计对照，不冒称本项目结果）。** 原文报告 WAN 2.2 TI2V-5B
骨干；ViewBench 训练集约 1k+ 序列/约 500k 帧，另有 600 条不重叠评测轨迹；稀疏设置
使用 top-k=5，并在 61 帧上训练 6k steps、201 帧上训练 2k steps；评价包括 PSNR、
SSIM、LPIPS 和 loop-closure error (LCE)，并有 random/exclude-selected 反事实选择。
这些是 ViewRope 的原文设置，不是我们已运行的资源或结果。

**与本项目的精确差异。** ViewRope 学习/使用 attention 内的 ray 几何相关性，选择单位
主要是历史帧；SOCF 只允许历史观测的风险与来源竞争特征，目标是预测未来 RGB-D/pose
损失并允许 abstain。FGB-Future 则把“未来状态效用、source provenance、固定真实 slot/成本”
写成共同评价合同。不能以“我们也选择几何相关帧”作为贡献。

**本项目最小对照。** 在同一 held-out 数据、同一 VMem consumer、同一候选池和 `k=4`
下实现一个 ray/pose relevance baseline（仅历史输入）；若合法 checkpoint 和接口可得，
再报告 ViewRope checkpoint 的独立结果。若 backbone、tokenizer 或生成步数不同，必须标为
跨系统参考，不能作为公平胜负。

### Card S：Spatia（Video Generation with Updatable Spatial Memory，CVPR 2026）

**原文问题定义。** Spatia 面向可交互长时视频生成，维护可迭代更新的 3D point-cloud
spatial memory；后续视频使用历史生成帧、参考帧、camera path 和 target scene video
tokens，以降低长期空间漂移。

**核心假设。** 用新生成帧持续更新显式场景记忆，并以场景投影作为生成条件，能够支持
多轮相机轨迹和回访的一致性；显式 3D memory 的更新比只依赖短上下文更稳定。该假设
覆盖了“updatable spatial memory + geometry-conditioned generation”，因此 GRC 不能把
这些宽泛部件重新命名为创新。

**算法步骤（原文机制摘要）。**

1. 从初始图像估计初始 3D scene point cloud；
2. 根据用户相机轨迹和参考条件生成第一段视频；
3. 用已生成帧通过 MapAnything 更新 spatial memory；
4. 将参考帧、上一段视频、场景投影和新 camera path 输入下一轮生成；
5. 循环更新并评价视频/回访空间一致性。

**论文预算/评价事实（用于风险审计）。** 原文以 Wan2.2 5B 为骨干，使用 ControlNet
和 LoRA 两阶段训练；报告的训练设置包括 64× AMD MI250 GPU、batch size 64，默认第一
轮生成 81 帧。该规模不能在本机 M3 上复现，SuperPod 上也必须先核验权重、代码许可和
显存；本项目不能把“读取论文或加载 checkpoint”称为 Spatia 实验。

**与本项目的精确差异。** Spatia 的核心是显式 point-cloud 更新和生成条件；SOCF/FGB-
Future 的核心是**历史-only 风险是否预报独立未来状态的增量损失**，并要求 source-level
replace/delete、固定 slot/token/forward 成本和 calibration/test 隔离。Spatia 可作为
updatable-memory 强 baseline 或跨系统参考，不是简单的 selector 对照。

**本项目最小对照。** 若有可验证 checkpoint，只在同一 held-out query 上做 inference-only
回访测试，同时单独记录 Spatia 的 point-cloud、token、显存和时延；若无法对齐 VMem 的
backbone/预算，则只报告“外部强基线参考”，不纳入 SOCF 的公平显著性比较。若无合法
checkpoint，保留文献对照和一个可运行的显式 3D-memory baseline，不编造 Spatia 数值。

## 2. SOCF / FGB-Future 一页可执行对照表

| 项目 | FGB-Future（先做的新评价问题） | SOCF（可选 companion method） | ViewRope 对照 | Spatia 对照 |
|---|---|---|---|---|
| 核心问题 | 固定真实记忆预算下，历史风险能否预测未见未来 RGB-D/pose loss？ | 稀疏 source-conflict 风险能否校准并指导 update/abstain？ | 几何 ray relevance 是否改善回访 LCE？ | 更新 3D memory 是否改善迭代生成回访？ |
| 选择/状态单位 | 历史观测或 memory item；`k=2,4,8` | 候选 item + conflict 区域；`k=2,4,8` | 历史帧/attention block；原文 top-k=5 | 点云/参考帧/生成 clip；原文闭环更新 |
| 允许输入 | 仅 calibration/development 的历史 RGB-D、K、pose、时间戳和历史几何 | 同左；禁止 future RGB/depth/pose/mask | 相机 ray、历史帧和模型 attention | 历史生成帧、点云更新和 camera path |
| 未来目标 | test future RGB-D、pose、reprojection、tail/CVaR | 同左 + source overwrite/conflict | ViewBench LCE/PSNR 等，不能替代 RGB-D/pose | 视频/空间一致性，需另核 future GT |
| 最小数据 | ≥5 条合法 held-out 轨迹，每条≥3 query；独立 calibration split | 与 FGB 相同 | 论文已有独立 ViewBench；本项目不能把已见 TUM 当作它 | 论文训练规模不等于本项目 test |
| 公平预算 | 同候选池、同 `k`、token/字节、显存、选择时间、forward、生成步数；全量记账 | 同 FGB；abstain 不能偷偷减少评估成本 | 若不同 backbone/训练，标为非公平参考 | 5B/ControlNet 与 VMem 不同则不作直接胜负 |
| 最小作业 | recent、uniform、random、多 seed、pose、coverage、depth、confidence、MI/GP、SOCF | calibration → test 风险预测 → consumer inference → source replay | ray/pose relevance + random/exclude-selected | inference-only（有权重时）或显式 3D-memory 简化基线 |
| 主要判据 | paired future mean AbsRel、Delta1、CVaR/worst-5%、reprojection、coverage、成本 | conflict AUROC/AUPRC、校准覆盖率、paired future gain、abstain 代价 | 仅作已知 geometry relevance 强基线 | 仅作 updatable spatial-memory 强基线 |
| 进入下一阶段门槛 | 数据/隔离/预算/复核全通过；最强 selector 的未来收益方向可重复 | AUROC 比最强非 SOCF 基线至少 +0.05；`k=4` future mean AbsRel 至少相对改善 1%，轨迹 bootstrap 95% CI 不跨 0；source replay IoU≥0.5 | 若 SOCF 只达到 ViewRope/ray baseline，停止方法主张 | 若仅 point-cloud/coverage 改善而 pose/depth 不改善，停止方法主张 |
| Kill criteria | future 泄漏、只改善当前重建、跨场景不稳定、成本不等或所有方法不分辨 | 风险不能预测 conflict、校准失败、无 future gain、simple overlap 同效、完整生成无一致改善 | 缺 checkpoint/许可、指标不兼容、不同 backbone 不能硬比较 | 缺 checkpoint/许可、显存不可复现、只读论文/加载无 forward |
| 允许结论 | “评价问题和协议是否可测”；负结果也可保留 | “在该数据和预算下风险预测/方法是否成立” | “已知近邻 baseline 结果” | “已知近邻 baseline 结果” |

## 3. SuperPod 最小运行顺序

1. **环境与权限 smoke test（无 GT）**：核验节点、GPU、CUDA、容器、git commit、权重
   SHA、许可证、显存和一个不含 future body 的 dry-run；连接成功不算科研结果。
2. **Gate0**：对新的 RGB-D、K、pose、时间戳、单位和 split 做完整 manifest；不是
   `HELD_OUT_TEST` 就停止，不能提交 GRC。
3. **FGB-Baseline**：先跑统一 consumer 的 recent/random/pose/coverage/depth/confidence/
   MI-GP，预测封存后才读 future GT；保存所有失败和成本账本。
4. **SOCF-Calibrate**：只在 calibration split 拟合 conflict 风险；test 只做冻结后的
   预测和 abstain/update；先检查 AUROC/覆盖率，再决定是否接完整生成。
5. **Source-Intervention Replay**：固定 seed、其它记忆、轨迹和预算，只替换一个 item；
   复核预测 conflict 区域与实际 provenance 改变，再读取 future GT。
6. **ViewRope/Spatia 对照**：仅在代码、权重和许可核验后执行；无法对齐时保留为外部
   近邻参考，不能把异构结果写成公平比较。

任何一个 Gate、泄漏检查、budget 检查或独立复核失败，均停止方法化叙事；不通过增加
agent、修改聚合或更换指标追求阳性。全部输出写入新的冻结目录，并同步主账和交接入口。

## 4. 审稿式总判定

ViewRope 是最接近的**几何相关历史选择/回访评价**近邻；Spatia 是最接近的**可更新
显式 3D memory/完整生成**近邻。两者都压缩了“geometry-aware memory”这一宽泛创新
空间。当前唯一未被这些工作直接覆盖、但尚未证实的联合问题是：

> 历史-only、经过独立校准的观测级风险，能否在固定真实 memory/compute budget 下预报
> 完整 world-model consumer 对未见未来 RGB-D/pose 的有符号增量损失，并在 source-level
> intervention 和公平强基线下保持收益。

这仍是候选的新评价问题/机制假设，不是已成立的创新或论文贡献。

## 原始来源

- [ViewRope 原文（arXiv:2602.07854）](https://arxiv.org/abs/2602.07854)
- [Spatia（CVPR 2026 Open Access）](https://openaccess.thecvf.com/content/CVPR2026/papers/Zhao_Spatia_Video_Generation_with_Updatable_Spatial_Memory_CVPR_2026_paper.pdf)
- [GIM-World（arXiv:2606.02436）](https://arxiv.org/abs/2606.02436)
- [Geometry-as-context（CVPR 2026 Open Access）](https://openaccess.thecvf.com/content/CVPR2026/html/Hu_Geometry-as-context_Modulating_Explicit_3D_in_Scene-consistent_Video_Generation_to_Geometry_Context_CVPR_2026_paper.html)

本轮事实来自原始页面/论文段落的定向核验；没有运行 ViewRope 或 Spatia 的模型，也没有
将其论文指标改写成项目结果。

