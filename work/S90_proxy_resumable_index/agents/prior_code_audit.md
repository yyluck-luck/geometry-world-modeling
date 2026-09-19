# S90 近邻官方代码核验：GRC-Memory 的可复用组件、边界与新颖性影响

<!-- EXPERIMENT_NAME_LEGEND_20260912_BEGIN -->
> **S编号与具体试验名称说明（2026-09-12更新）**  
> 文档中的 `S86`–`S90` 是项目内部阶段编号，保留它们是为了让结果、日志和回执可以追溯；括号内是给新读者看的具体名称。编号不是论文术语、结果等级或“实验成功”的标志。S88–S90主要是数据资格/传输与协议审查，不能误读成模型性能实验。
>
> - **S86（单场景四目标几何条件注入基线实验）**：在一个已见静态场景、四个相关目标上，比较历史几何注入方式的真实生成链和RGB误差。
> - **S87（末端引导强度控制与多步引导必要性反例实验）**：复用S86缓存，比较末端处理强度与持续多步引导；它只检验该已见场景的有限反例，不验证GRC或长期几何收益。
> - **S88（RTMV相机JSON元数据与静态投影数据资格检查）**：核对归档身份、相机元数据和可访问的静态文件头；不是RGB-D配对性能实验。
> - **S89（RTMV配对数据TLS接续失败审查）**：记录两种TLS/传输接续尝试及其失败边界；失败本身不等于数据缺失或科学负结果。
> - **S90（RTMV归档配对数据恢复与索引协议审查）**：检查受限Range传输、归档成员身份、断点恢复和索引安全条件；已恢复的512B文件头不等于取得可用深度正文。
>
> 后续报告首次出现编号时应同时写成“**S86（单场景四目标几何条件注入基线实验）**”这类形式；后文可使用编号，但不要只写编号来替代试验名称。
<!-- EXPERIMENT_NAME_LEGEND_20260912_END -->


**核验时间：** 2026-09-11 18:11:46 +0800  
**核验性质：** 固定 commit 的源代码静态审计；没有下载数据、模型权重或运行 GPU 推理。因此本文只报告“代码明确实现了什么”，不把代码存在、仓库可克隆或环境声明当作实验结果。

## 1. 审计对象与可复现锚点

| 对象 | 官方远程仓库 | 固定 commit（本地浅克隆） | 主张/论文入口 | 当前可复现边界 |
|---|---|---|---|---|
| Conformal Risk Control | <https://github.com/aangelopoulos/conformal-risk> | `3eff946390a8f188b1e5ab700fce21a66a215e7c` | README 的 CRC 论文链接；ICLR 2024 版本 | `core/get_lhat.py` 可读；示例依赖数据和环境，未运行 |
| FisherRF | <https://github.com/JiangWenPL/FisherRF> | `b74732812b295189f230a192418375f56cec3bd6` | README `FisherRF: Active View Selection and Uncertainty Quantification...` | 选择器和不确定性代码可读；CUDA 子模块/数据/权重未初始化 |
| Neural Visibility Field (NVF) | <https://github.com/GaTech-RL2/nvf_cvpr24> | `be6b583adde3a99f7bb0f638fed96ab2ead2f310` | README 说明 CVPR 2024 NVF | visibility/entropy 代码可读；README 要求 CUDA 11.7、RTX 3090 等，未运行 |
| FisherRF-active-mapping | <https://github.com/JiangWenPL/FisherRF-active-mapping> | `8b196cd22b1f4030f205778ad14b23fbd796c3b7` | README 的 Gibson/HM3D active mapping | 路径规划和 Hessian 评分可读；Habitat、GPU 数据环境未运行 |

四个 clone 都是 shallow clone；FisherRF 和 active-mapping 的 submodule 行带有未初始化标记（`git submodule status` 的前导 `-`）。所以本审计不声称已复现任一论文的数值。

## 2. Conformal Risk Control：能支持的部分与不能支持的部分

### 2.1 实际代码行为

官方核心函数 [`conformal-risk/core/get_lhat.py`](../innovation_agent/sources/conformal-risk/core/get_lhat.py) 的注释和实现位于第 4--12 行：

* 输入是一个二维 `calib_loss_table`，行是校准样本，列是候选 `lambda`；第 9 行取样本数，第 10 行对每一列求均值。
* 第 11 行使用 `n/(n+1)` 和 `B/(n+1)` 的有限样本修正，找到一个列索引；第 12 行返回**一个全局的** `lambdas[lhat_idx]`。
* README 第 12--18 行把目标写成有界、随 `lambda` 单调的损失，并明确目标是新测试点上的期望损失 `E[L_{n+1}(lambda_hat)] <= alpha`。README 第 34--36 行把 `risk_histogram.py` 作为完整实验入口。
* 例子 [`qa/risk_histogram.py`](../innovation_agent/sources/conformal-risk/qa/risk_histogram.py) 第 39--66 行再次显示：先构造 `[样本, lambda]` 的损失表，再切分 calibration/validation，最后以单一 `lambda_hat` 评估验证集。

### 2.2 对 GRC-Memory 的直接影响

原始想法中的 `q_i = Q_{1-alpha}(r_i)` 不能直接由这个官方实现得到：`r_i` 是每条历史的三维几何证据，而 CRC 代码需要一个**标量、可定义上界 B、且对决策参数单调的集合/决策损失表**。它也不提供每条候选记忆的条件风险保证。

可保留的严谨用法是：先定义一个只使用目标时刻之前信息的记忆策略族 `pi_lambda`，在按场景/时间隔离的 calibration trajectories 上计算同一策略在固定预算下的标量未来几何损失 `L_t(lambda)`，然后把 CRC 作为选择全局运行点 `lambda_hat` 的外层工具。这样使用时，必须把结论写成交换性假设下的**边际/期望风险控制**，不能写成“每个候选记忆的风险上界”或“选择后仍自动有效”。

**判定：** CRC 是方法学基线/校准包装器，不是 GRC 的新颖性本身。若只把 `get_lhat` 接到几何分数后面，没有未来状态损失、prospective split 和选择后评估，不能宣称风险校准记忆选择成立。

## 3. FisherRF：信息效用和不确定性先例

### 3.1 实际实现

在 [`FisherRF/active/H_reg.py`](../innovation_agent/sources/FisherRF/active/H_reg.py)：

* 第 24--57 行先取得已有训练相机和候选相机，对每个训练视图渲染并反向传播，累积每个参数的梯度量 `H_train`。
* 第 62--75 行对每个候选相机同样计算 `H_candidates`。
* 第 77--90 行循环 `num_views` 次，以
  `sum(cur_H * reciprocal(H_train + reg_lambda))`
  为 acquisition score，选取分数最大的视图，并把其 `H` 加入 `H_train`。这是一个逐步的 Fisher/Hessian 风格主动**视图采集**规则，不是对历史帧做未来世界状态监督。
* 单视图路径第 97--128 行也只是计算候选视图分数后排序返回。

不确定性可视化位于 [`FisherRF/render_uncertainty.py`](../innovation_agent/sources/FisherRF/render_uncertainty.py) 第 83--130、145--182 行：它对渲染图像反向传播，累积每个 Gaussian 的梯度量，按深度着色形成 uncertainty map 并保存 `.npz`。代码没有几何真值风险、未来帧误差、校准集或 conformal 选择。

README 第 1--3 行把项目定位为 “Active View Selection and Uncertainty Quantification for Radiance Fields”；第 58--60 行把 active mapping 明确指向另一个仓库。

### 3.2 对 GRC-Memory 的判定

FisherRF 可以作为“信息效用”基线，或作为候选 `u_i` 的一个先验特征；但是下列说法均不被代码支持：

1. Fisher 分数等于历史记忆对未来状态的预测信息；
2. Fisher 分数经过校准就是几何风险；
3. 逐个加入视图的贪心规则在 GRC 的联合风险目标上有 `1-1/e` 保证。

如果 GRC 只是在 Fisher 分数上加一个风险惩罚，贡献会更像已有 active view selection 的任务迁移；必须实证显示“历史记忆选择 + held-out future geometry loss + fixed budget”带来独立效果。

**建议：** 纳入强基线（Fisher/EIG-style utility），但不要复制其 CUDA 训练系统作为当前本机主线；先在已有匹配特征/几何真值上实现同定义的轻量分数。

## 4. Neural Visibility Field：可见性证据的已有覆盖

### 4.1 实际实现

在 [`nvf_cvpr24/nvf/visibility/visibility.py`](../innovation_agent/sources/nvf_cvpr24/nvf/visibility/visibility.py)：

* 第 153--211 行的 `fov_visibility` 将 3D 点变换到每个相机坐标系，检查深度范围和投影是否落在图像边界，得到相机-点的 FOV mask。
* 第 213--238 行的 `get_visibility` 对通过 FOV 的点沿射线计算场密度/opacity，并跨相机累积，返回 `1 - opacity` 形式的可见性量。

在 [`nvf_cvpr24/nvf/uncertainty/entropy_renderers.py`](../innovation_agent/sources/nvf_cvpr24/nvf/uncertainty/entropy_renderers.py)：

* 第 4--39 行定义 `VisibilityEntropyRenderer` 的可见性调制密度；
* 第 42--72 行把可见和不可见成分组织成 GMM；
* 第 114--160 行从 density、visibility、RGB 和 RGB variance 计算等效密度与熵。

入口 [`nvf_cvpr24/eval.py`](../innovation_agent/sources/nvf_cvpr24/eval.py) 第 41--70 行在 `method == 'NVF'` 时打开 `use_visibility`、`use_rgb_variance` 和 `VisibilityEntropyRenderer`。

README 第 2--6 行和第 10--38 行说明其是 CVPR 2024 的不确定性驱动主动建图方法，并要求 Ubuntu 20.04、RTX 3090、CUDA 11.7 以及 nerfacc/tiny-cuda-nn 等依赖。

### 4.2 对 GRC-Memory 的判定

“可见性冲突”作为几何证据已经有明确先例；“visibility + uncertainty”不能单独作为新颖性。NVF 没有历史记忆池、长期时序更新、未来状态预测、固定 token/显存预算或风险校准，因此 GRC 仍可能在**决策对象和评价目标**上区分，但不能把可见性模块本身写成新贡献。

**建议：** 可借鉴 `fov_visibility` 的定义作为 feature/controlled baseline，并单独报告它与重投影误差、深度残差的相关性；不要直接把 NVF 的 entropy 当作已校准 `q_i`。由于环境和 CUDA 要求，当前本机只能做公式/小单元测试，不能声称复现 NVF 结果。

## 5. FisherRF-active-mapping：与历史记忆任务的距离

README 第 1--9、29--81 行说明该仓库针对 Gibson/HM3D 室内环境、Habitat 导航和 active mapping，实验依赖 Docker、NVIDIA runtime、16 CPU/48 GB 内存配置以及 GPU 数据集。

代码中最接近选择目标的部分是 [`models/SLAM/gaussian.py`](../innovation_agent/sources/FisherRF-active-mapping/models/SLAM/gaussian.py)：

* 第 1296--1306 行累加 keyframe 的 Hessian 得到 `H_train`；第 1312--1335 行对候选 pose 计算 `cur_H * reciprocal(H_train + 0.1)` 的分数并返回候选 pose。
* 第 1134--1294 行的 `global_planning` 先取训练历史的逆 Hessian（第 1144--1156 行），在不确定点的上分位区域采样中心、DBSCAN 聚类（第 1184--1225 行），再对可导航候选相机计算 Hessian acquisition score（第 1239--1273 行）。
* 第 1350--1412 行的 DFS 规划将每一步的 Hessian score 累加，在固定深度内选路径。
* 第 1463--1525 行的 `compute_Hessian` 对候选 pose 渲染并反向传播，返回每个点的梯度/opacity 量；它没有 future ground-truth loss 或 calibration。

因此它解决的是“下一台相机/下一段导航路径去哪里采集信息”，不是“已有历史帧哪些应留在 world-model memory 中”。把它作为 GRC 的直接方法会产生任务错位。

**建议：** 只作为 active-view/path-planning 的外部对照或消融（若数据协议允许）；不把其导航/DBSCAN/Hessian 代码并入 GRC-Memory 的主方法。

## 6. 交叉新颖性审查结论

这四个固定版本已经覆盖了 GRC 草案中四个容易被审稿人指出的已有组件：

| GRC 草案组件 | 近邻代码覆盖 | 能否直接称新 |
|---|---|---|
| Fisher/信息增益式 utility | FisherRF `H_reg.py`；active-mapping Hessian | 不能；应做强 baseline |
| visibility/uncertainty feature | NVF `visibility.py` 与 entropy renderer | 不能；只能作为证据特征/基线 |
| conformal 风险控制 | CRC `get_lhat.py` | 不能；只能在正确的有界单调决策损失上复用 |
| 历史记忆对未来几何状态的安全价值、固定预算、prospective calibration | 四个仓库均未实现 | 这是目前唯一仍可能形成独立问题定义的组合，但尚未被本项目真实数据验证 |

所以“GRC-Memory 一定是 8/10 新颖性”没有代码证据。更准确的当前表述是：**候选的新问题定义**，其差异点是 decision object（历史 memory set）和 held-out future-state loss，而不是 Fisher、visibility 或 conformal 任一单模块。是否构成独立方法贡献，要由后续同预算、同场景、时间隔离、几何真值和强 baseline 实验决定。

## 7. 采纳、基线、暂缓与拒绝清单

### 采纳（但需改写）

1. CRC 的“全局运行点校准”思想：只在策略族 `pi_lambda`、bounded monotone loss、scene/time-held-out calibration 都明确定义后采用。
2. NVF 的 FOV/可见性几何定义：作为输入 feature 或诊断，不把其 entropy 当作风险真值。
3. Fisher 的信息效用分数：作为同计算预算下的强 baseline，明确它衡量的是模型参数敏感性/视图信息，不是未来位置误差。

### 基线

* 最近邻/时间窗口、随机 memory、Fisher-style utility、visibility-only、depth/reprojection-only、简单线性 risk score。
* 如果实现了 GRC 的 greedy selector，必须加入 exact enumeration（小规模 k）作为选择上限，并测试非子模性。

### 暂缓

* NVF/FisherRF 的完整 CUDA 训练和 active mapping：当前无远程 GPU、数据和 submodule，不应在本机伪造“复现成功”。
* 任何需要直接使用真实未来帧来计算测试时 utility 的实现：会产生 target leakage，应改为 past/query-only surrogate。

### 拒绝的表述

* “把深度、uncertainty、Fisher 和 conformal 拼起来就自动新颖”；
* “`q_i` 是每条记忆的 conformal 条件风险上界”；
* “贪心选择有 `1-1/e` 保证”，除非在本任务中证明对应 utility 的单调子模性和约束条件；
* “代码仓库已复现论文结果”。本审计没有运行任何 GPU 模型或论文数据。

## 8. 给主线实验的最小要求

在进入大模型/大数据前，先用已有可读的 RGB-D/相机配对构造一个小型、可重复的时序协议：

1. 所有候选记忆分数只用目标之前的观测计算；
2. 固定记忆预算、随机种子、目标相机轨迹和生成/匹配预算；
3. 对每个候选报告重投影、深度、可见性三个标量及未来位置误差；
4. 与 Fisher-only、NVF-visibility-only、random、最近邻和 exact-oracle 对比；
5. 按 scene/time 做 calibration/test 分离，报告边际风险、选择后分布和跨场景变化；
6. 若“低历史几何风险 -> 低未来位置误差”的关系不成立，停止把 GRC-Memory 写成方法，保留为负结果/诊断。

**最终状态：** 近邻代码审计完成；没有新方法验证，没有论文级结论，没有 GPU 复现实验。
