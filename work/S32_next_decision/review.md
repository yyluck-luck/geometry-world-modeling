# S32 后的唯一下一决策：检验普通的配对尺度约束是否已经足够

**建议只增加一个普通工程对照：在当前每窗同一 C2a 初态之后，固定三条配对变换的「有效尺度几何均值」，其余原优化变量继续训练 400 步。** 这直接阻止三个配对变换一起缩小，保留它们之间的尺度差异。它与已封存的零步、自由尺度 400 步、自由尺度 400 步后一个公共 k 并列；不先加焦距冻结、逐帧先验、分层修正或新模型。本文件只提交可执行设计，尚未实现或执行这个对照。

本轮实际仅读已保存 JSON/JSONL、原源码和三篇原论文，保存量摘录见 [evidence_excerpt.json](evidence_excerpt.json)，来源、时间与 SHA 见 [sources.json](sources.json) 和 [completion_receipt.json](completion_receipt.json)。没有读取 NPZ、RGB/传感器深度图片，没有新推理、MST、反传、GA 或评分。主评分 PASS 是被引用的已有结果；本文没有代替另一个作者正在进行的数值复核。

## 1. 基线失败应怎样重述

下列均为每窗四帧等权均值。AbsRel 越小越好，RMSE 单位米；不是将像素混合后重算的指标。

| 固定窗口 | 零步 AbsRel | 自由 400 步 | 自由 400 步 + 自身 k | 零步 → k 后 RMSE |
|---|---:|---:|---:|---:|
| fr2_desk_j1 | NA | NA | NA | NA：缺给定相机关联 |
| fr2_desk_j2 | 11.494393% | 40.005808% | 12.330714% | 0.241984 → 0.271505 |
| fr1_xyz_j1 | 13.205083% | 17.458343% | **13.197833%** | 0.193070 → **0.194184** |
| fr1_xyz_j2 | 10.164119% | 19.305820% | 10.207059% | 0.115626 → 0.115930 |

原始 [metrics.json](../../results/S32_consumer_scoring/metrics.json) SHA `975ad404667a24032ca3c3c5bcfa61fc70dc1f38ef3dd14391df9c4dd2b0bbbf`；**评分**合同 SHA `091ab3c69fd62c50a57d3ce12f7b404abff370d8fb229381e103a2db4fc2e722`，不要将它误称 B 生产合同。既定 4 窗、12 组、48 行完整保留：36 行评分、12 行 NA。

证据支持三件事：①自由 400 步在三个可用窗均增大 AbsRel 和 RMSE；②普通 k 后处理在两个 fr1 窗几乎回到零步水平；③fr1_j1 的 AbsRel 比零步微低 0.007250 个百分点，但 RMSE 增大约 1.11 mm、δ1 从 0.953968 降至 0.951555，不能称全指标胜出，也不能说三个窗全部仍输零步。fr1_j2 的 δ1 反而略高于零步，完整指标须并列保留。像素数不提供独立样本量，这些微小差别没有统计显著性结论。

S32 不能继续支撑「普通公共尺度恢复普遍无效，因此需要复杂非均匀修复」这一版本的动机。保存分解的共同 log-change 平方和比例分别为 fr2_j2 **97.911841%**、fr1_j1 **98.835902%**、fr1_j2 **92.431859%**；非均匀 RMS log-change 分别约 0.06016、0.00553、0.03109。它们描述预测变化，**不是 GT 误差解释率，不是物理形状损坏比例**。fr1_j1 是应主动保留的反例。

## 2. 先从源码确定最小可干预对象

以下行号对应实际冻结 VMem 源，commit `39291e4f272f6b4f270691d930926ab5930f942e`；运行路径为 `work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R/`，源 SHA 随本文绑定。

- [cloud_opt/dust3r_opt/optimizer.py:102](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R/cloud_opt/dust3r_opt/optimizer.py:102>) 的 `preset_pose` 冻结相机，并在 121 行令 `norm_pw_scale=False`。这不是所有米制变量都受固定相机充分约束的证明。
- [base_opt.py:266–285](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R/cloud_opt/dust3r_opt/base_opt.py:266>)：有效配对尺度是原始最后一列的 exp 乘公共归一因子；关闭归一时因子为 1。此尺度乘整个 3×4 变换，包含旋转和编码平移解码后的平移。**不能只改旋转的缩放、遗漏平移，也不能把尺度列和整条 pose 参数一起冻结。**
- [base_opt.py:227–234](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R/cloud_opt/dust3r_opt/base_opt.py:227>)：同一个 `norm_pw_scale` 布尔还控制 adaptors。因此本对照不直接翻转该布尔，也不把默认 `base_scale=0.5` 引入单位初态。
- [optimizer.py:251–288](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R/cloud_opt/dust3r_opt/optimizer.py:251>)：可训练 depth/focal 经给定 pose 反投影成 world points，与配对 Sim(3) 后的冻结目标比较，目标是加权逐点欧氏范数和。焦距仍自由，只有它造成多少误差尚未干预证明。

保存轨迹显示三窗都存在共同缩小，但还不是因果结论：

| 窗口 | 配对有效尺度末值（3 条） | 全预测几何平均 D400/D0 | 焦距初末变化范围 |
|---|---|---:|---|
| fr2_j2 | 0.639469 / 0.639262 / 0.640440 | 0.662360 | 394.89–400.66 → 398.16–415.20 px |
| fr1_j1 | 0.944122 / 0.943699 / 0.943442 | 0.950357 | 362.57–366.33 → 363.84–370.17 px |
| fr1_j2 | 0.877835 / 0.877859 / 0.878501 | 0.897054 | 366.33–400.66 → 376.88–394.00 px |

三条尺度初值都近 1，实际数值有 FP32 差异，不应硬改成 1。当前证据优先指向检查公共尺度模式；焦距同时变化不意味着它是主因。即使共同尺度被阻止，平移、相对边尺度与焦距仍可能通过其他方向减小残差。给定非共心相机时，本对照改变约束集合，**不是已证明保持物理解等价的纯坐标规范变换**。

## 3. 三篇最近相关机制：排除换名创新

此表是本次定向排查的三篇原文，不声称覆盖全领域或证明任何复现排行榜。原文均已通过 web 实际打开；Scal3R 还绑定先前存档。四轴为对象、机制、粒度、设置。

| 原工作 | 已读机制与四轴 | 本任务的实际差别与排除 |
|---|---|---|
| **DUSt3R: Geometric 3D Vision Made Easy**；Shuzhe Wang、Vincent Leroy、Yohann Cabon、Boris Chidlovskii、Jerome Revaud；CVPR 2024 | 多图 pointmap 对齐；加权 3D 残差、配对位姿和尺度；edge scale 乘积约束防止零尺度解；未知相机重建设置。原 §3.4 与作者 `get_pw_norm_scale_factor` 源码已核。 | 固定公共 log-scale 与其尺度规范直接相邻，是**普通强控制**。这里改为同一已知相机/米制头初态的几何均值，仅用于隔离下游优化自由度，不能称首次解决尺度坍缩。[原文](https://arxiv.org/html/2312.14132v3#S3.S4) · [作者源码](https://raw.githubusercontent.com/naver/dust3r/main/dust3r/cloud_opt/base_opt.py) |
| **Scal3R: Learning Efficient Multi-Relative Pose Query for Scalable Online 3D Reconstruction**；Chin-Yang Lin 等；2026-09-03 arXiv v1 | 长序列在线重建；冻结骨干、非对称查询 token、多参考相对姿态与 PGO；局部几何/相机关系；自由姿态、长程在线设置。读 §3.1–3.4、4.1。 | 已覆盖「保护局部几何、优化姿态」的广义想法。我们三窗均固定真实相机、只约 0.1 秒，不构成其长序列 pose-head 退化复现；当前干预也不是一个新的姿态学习机制。[原文](https://arxiv.org/html/2609.04201v1#S3) |
| **LASER: Layer-wise Scale Alignment for Training-Free Streaming 4D Reconstruction**；Tianye Ding、Yiming Xie、Yiqing Liang、Moitreya Chatterjee、Pedro Miraldo、Huaizu Jiang；arXiv v1 2025-12-15 | 离线模型转流式；窗口 Sim(3) 注册后按深度层 IRLS 尺度、层图跨窗口/时间传播；layer 粒度；重叠预测窗口、低视差深度错位。此次补读 §3.1–3.2，超出先前摘要检索范围。 | 「整体尺度不能消除所有变化」已经有近邻实质方法；S32 尚未展示跨窗口分层错位，也未证明需复杂残差修正。不能用 LASER 的动机替当前三个短窗推断物理根因。[原文](https://arxiv.org/html/2512.13680v1#S3) |

当前作者 DUSt3R `preset_pose` 也关闭归一；因此不把这个设置描述为 VMem 独有的漏写 bug。[作者 optimizer](https://raw.githubusercontent.com/naver/dust3r/main/dust3r/cloud_opt/optimizer.py) 的当前 main 是访问日快照，不冒充固定历史 commit。所有 method 声称来自方法原文/代码，未采用搜索摘要推导。

## 4. 唯一候选对照的可执行合同

**待证假设：** 在三个现有给定相机小窗中，允许配对尺度的共同模式收缩，是自由 400 步导致共同深度缩小的重要可干预路径；仅移除这个模式能减小深度共同缩小，而且是否超过「零步」及「原 400 步 + k」必须另外比较。这个假设没有预设它是唯一根因或能带来精度收益。

只在每窗原 MST 返回、第一次 Adam 之前安装实例级归一因子。令 `ell = scene.pw_poses[:, -1]`，立即保存独立副本 `m0 = ell.detach().mean().clone()`；候选因子为：

```python
factor = (m0 - scene.pw_poses[:, -1].mean()).exp()
```

原 `get_pw_scale()` 继续将 `exp(ell)` 乘这个因子；原 `get_pw_poses()` 继续缩放整个 3×4 变换。有效 `mean(log(scale))` 被约束在 `m0`，三条尺度的相对比率可训练。`m0` 只来自本窗初态，不是 GT、S32 已见收益或固定 1.0/0.5；不增加新 trainable 参数、不投影深度、不改变 Adam 的步数/学习率/动量。**不要 detach 当前 mean**：那会改成数值归一但错误的梯度路由。原始 ell 的均值可能随 Adam 漂移，执行门验证的是有效尺度的均值，不是误要求 raw mean 逐字固定。

一个新候选、三个新 400 步足够；不重跑已通过的 S32 自由臂或 A 推理。既有三个对照整表原样导入；另增候选的完整 4 窗 × 4 行，缺 pose 的 fr2_j1 仍 NA，不替换、不插值。对照表新增一列后总为 **4 条件 × 4 窗 × 4 帧 = 64 行，其中预期 48 可评分、16 NA**；原 S32 的 48 行仍独立保留，不能悄悄改变其分母。整窗失败则该新条件四行全 NA，不能只评分幸存初态。

实施前需要的门限/观察仅如下：

1. 复用正式 S32 A 24 头、12 个 star 消费张量、允许给定 optical c2w、原 PIL/固定来源、seed/CPU8/FP32。每窗重新 MST 只为在原代码路径建立新的 optimizer；开始训练前，33 项原参数/buffer 的名字、shape、dtype、flags、bytes 与对应 S32 初态全匹配，值域/schema/完整集合不得空通过。若不匹配保留失败，不擅自重新跑自由臂来抹平不一致。
2. 安装 factor 前后，原参数对象/值和 decoded 初态、有效配对变换、原 loss 逐值一致；利用既有 getter 边界的两次无更新 forward，避免再加一个重复场景评价。`m0` 分别保存标量和值来源，因子初值为 FP32 的 1；实际兼容仍待验证，源码代数不是数值通过回执。
3. 继承已修 depth getter，所有原 trainable depth 的 400 次梯度均 finite 且非 None；相机、pp、原不可训练 adaptor/目标/权重不变，focal 与 pair R/T 仍可更新。每步保存原已有 trace，并增加 raw log-scale mean、实际 factor、有效 scale mean 和三条有效 scale。预冻 `abs(mean(log(effective_scale))-m0) <= 1e-5`，以及保持相对 scale 比例的 FP32 数值核验 `atol=rtol=1e-5`。这些是实现门，不是科学胜负阈值。
4. 同 400 Adam、lr=.01、linear；不挑最优中间步，不用 sensor GT 停步。预计继承每窗 403 原 objective forward（400 + getter 边界 2 + 末端 1）、3 PnP、1 MST、1 clean；只在源码能保持这一计数时冻结。原欧氏残差/clean/backprojection 数学不改，独立目标复算使用**有效**配对矩阵，不能从 raw ell 错解另一个目标。
5. 全部固定窗的新终态及输入身份封存后，才沿原评分规则读 GT，保留全部 AbsRel、RMSE、δ1 与无效/缺失统计。只新增候选终点评分，旧三条件的既有分数按 SHA 原样引用。保存完整初末 depth/focal/world/有效 pair state，便于下游消费者追踪；本轮不增加候选的第二种评分后处理或逐帧 k。

建议上限沿已成功的 S32：每可用窗 CPU8、120 秒、4 GiB RSS，顺序 3 窗共 1200 Adam/反传、3 MST/9 PnP、3 clean、0 新网络；评分 120 秒/2 GiB，0 模型。旧 GA 实耗每窗约 24.4–25.0 秒，仅是预算依据，不保证新运行时间。派生 `run_consumer.py` 的 MST 后观察边界与冻结 S28/S30 observer 即可；本文件没有生成执行脚本或直接启动任务。

## 5. 反证、最强反例与停止规则

**机制与精度分开判。** 若有效尺度约束通过，但三个窗中任一窗的 `abs(mean(log(D400/D0)))` 未减少，便否定「该单模式干预在这三窗一概足够抑制共同深度偏移」的强版本；若减小共同变化却不改善误差，只能称干预改变尺度路径，不能称修好了消费者。小于评分数值复核分辨率的差别不作科学胜负。

精度表必须同时比较零步及既有普通 k；不能只拿坏的自由终点作标靶。分别列每窗差值及三窗等权描述均值，不以总体均值隐藏一窗变差。若新候选不能同时优于两个强对照的 AbsRel/RMSE，结论是当前优化没有展示稳定净收益；若指标混合即记混合。任何微小胜出都不升级为泛化、显著性或创新。**无论结果如何，本轮只跑这个固定版本一次；不在这三窗继续调 m0、prior 权重、focal 冻结组合或步数。**

最强反例是：真实的初始化尺度本来有偏差，给定相机的非零基线支持必要尺度修正；锁住初态反而阻碍正确解。另一个反例是深度通过自由平移/focal/相对尺度或点图的不一致继续变形，此时共同 pair scale 不是充分解释。先验保留模型尺度也不能赋予它真实米制保证。fr1_j1 的普通 k 已接近零步，是现成强竞争者，不应将其微小剩余差距包装成重要问题。

**与 proposal 的退出边界：** 若普通尺度约束足够，先记录为工程基线加固；下一研究价值必须来自真实 old4→new4、提交地图/可见性/选图或生成消费者仍未解决的问题。若不够，也只得到「这一常规机制不充分」，不能立即跳到新模块命名。此任务的四帧窗时间跨度为 0.0969–0.1025 秒、仅两个已使用场景、给定 GT 相机条件。它既不能证明跨 chunk 持久记忆失效，也不能承诺长视频收益或 CCF A 水平。

## 6. Skill 决策落点

按 [Supervisor handbook 2.2](</Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/Supervisor-Skills/handbook/02_Idea_Generation/2.2_想Idea的思路_更高更快更强.md>) 的实际步骤：采用更强零步/k 基线 → 将失败归为共同缩小与非均匀变化 → 用源码选择一个可干预自由度 → 先验证普通机制是否足够。没有把 idea-evaluator 当生成器。

应用 [idea-evaluator](</Users/rocket/.codex/skills/idea-evaluator/SKILL.md>) 和 [fatal-flaws](</Users/rocket/.codex/skills/idea-evaluator/references/fatal-flaws.md>)，对「单尺度约束就是新方法且已满足论文创新」这个**投稿版本**给出：

- **First impression：** 暂不成立；它当前只是必要的强工程对照。
- **Fatal flaws：F1 CRITICAL。** DUSt3R 已有同类公共配对尺度约束；现方案没有新的机制差别。对原先「普通尺度恢复普遍不够」的强动机，S32 也给出两窗接近起点的反证，不能用先前 common4 的更差结果覆盖它。
- **Verdict：Reject and Pivot。** 拒绝这个创新叙事，不给虚构创新分或靠更多短窗恢复该主张。上面的单变量诊断只服务 baseline failure 定位，不属于被拒投稿版本的“效果保证”。

本地 Claude [科学批判技能](</Users/rocket/.claude/skills/sci-scientific-critical-thinking/SKILL.md>) 用于核因果/相关、普通强对照、反例、完整缺失分母和外部有效性。下一候选是基于已见开发结果产生的探索性干预；即使未来先封存后评分，也不会因此变成历史 GT 未见的盲测。
