# S6 输入桥接设计审查：学习深度到 surfel 检索

2026-09-05 的有界源码设计审查。**未启动 S6，未修改 S3，未声称该桥接已通过或改善检索。** 已有 S4–S5 是独立 CUT3R 推理与几何诊断，不能把其原始 NPZ 直接称作 VMem 的 surfel 输入。

## 建议的最小下一步

先做一个明确命名的 **“CUT3R 自视深度＋固定标定＋预测位姿的检索部件实验”**：用自视点图的 Z、裁剪后的已知相机内参构造针孔射线上的点，再用预测位姿放入同一块坐标系；前 20 帧建图，后 4 帧只查。这样可以复用 S3 的深度到 surfel 数学及已验证的匹配/完整选帧核心，不需要先引入全局优化器或声称自视点图、共同坐标点图与位姿天然一致。

这个方案有一个必须明说的建模选择：它保留 `self` 的 Z，重建 X/Y，**不是直接使用 CUT3R 原始 `self` XYZ，也不是 VMem 完整重建**。如果要保留原始 XYZ，另写点图入口并单独评估其投影与内参一致性，不能悄悄混用两种定义。

## 固定 VMem 实际做了什么

来源为 `runjiali-rl/vmem@39291e4f272f6b4f270691d930926ab5930f942e`，与项目 `vendor/provenance.json` 一致。

1. **模型与输入。** Pipeline 指定加载 `cut3r_512_dpt_4_64.pth`，`run_inference_from_pil` 默认 size=512。它使用 VMem 仓库内的 CUT3R fork，而本机已运行的是独立官方仓库提交 `8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf` 的 224 linear 中间检查点。[模型加载](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/modeling/pipeline.py#L86)。
2. **组织与优化。** Fork 将首帧与每个后续帧组成星形配对；全局优化器消费首帧的 `pts3d_in_self_view/conf_self` 和后帧的 `pts3d_in_other_view/conf`。随后 `compute_global_alignment(init='mst', ...)` 优化场景，不是直接返回 raw other。已有相机轨迹通过 `preset_pose` 固定；已有深度可以 `preset_depth` 固定。这里的相机轨迹是生成/输入流程提供的轨迹，不能自动等同于 TUM mocap。[调用链](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/extern/CUT3R/surfel_inference.py#L293)，[配对输入字段](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/extern/CUT3R/cloud_opt/dust3r_opt/base_opt.py#L132)。
3. **点与内参。** 最终 `scene.get_pts3d()` 将优化后的深度按优化后的 focal/principal point 反投影，再经优化/固定后的相机位姿变到世界系。初始化包含从点图估计焦距，默认主点从图像中心开始；不能把原始 head 的 `camera_c2w`、TUM 原图 K 和优化后的世界点随意拼接。[准备输出](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/extern/CUT3R/surfel_inference.py#L175)，[深度到世界点](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/extern/CUT3R/cloud_opt/dust3r_opt/optimizer.py#L251)。
4. **清理。** `clean_pointcloud` 使用同一场景的 K、world-to-camera、深度和点图，将投到其他观测表面前方、同时相对低置信的点置信度压低。默认 `tol=0.001,bad_conf=0`，不是删除/平均点位置，也不是经校准的正确概率。该步骤在返回 confidence 前执行。[清理实现](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/extern/CUT3R/cloud_opt/dust3r_opt/base_opt.py#L581)。
5. **构建 surfel。** 场景点图、深度和已清理的置信度先双线性缩小（配置 `shrink_factor=0.05`），焦距按同一比例缩小。邻接右/下点的差向量产生法向，法向按“相机到点”的方向翻向；只保留 confidence≥1 且 depth≤0.999 分位的像素。半径是 `0.5*z / focal / (0.2+0.8*abs(cos))`。代码旁边写“95 percentile”，实际执行的是 0.999。末行/末列法向保持零，退化点和 NaN 行为需要单独核对，不能擅自将自己的更强过滤称原版。[缩小与调用](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/modeling/pipeline.py#L982)，[surfel 公式](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/modeling/pipeline.py#L832)。

构建时传给 surfel 法向翻向的是输入轨迹经 Y/Z 翻轴后的姿态；清理阶段内部使用的是 scene 相机。正常路径通过 preset_pose 使其受同一轨迹约束，这个对应也不能在新桥接中省略。已有记忆时原流程只追加新 target 帧；重新优化/清理旧帧不等于旧 surfel 位置随后被更新。

## 独立 224 与 fork 的具体边界

| 项目 | 已运行的独立 CUT3R | 固定 VMem 调用 |
|---|---|---|
| 模型 | 224 linear 中间检查点；实际 `LinearPts3dPose` | 配置 512 DPT 文件；未在本机加载该文件 |
| 点/位姿 | self、other、pose 由不同预测分支给出；不存在强制 `other=pose×self` 恒等式 | 用首帧 self/后帧 other 约束全局场景，再由 depth/K/pose 重建一致点图 |
| 相机内参 | raw NPZ 不含最终估计/优化 K | 场景提供 focal、pp |
| 清理/优化 | 未经过 fork 的 global alignment/clean | 两者均在 surfel 之前 |
| 本机适配 | 外部 signed-RoPE＋blocking 输入搬运，保留源码 | fork 的 PyTorch RoPE fallback 被注释；不能直接复用现有导入环境 |

本轮逐文件核对：两仓库的 `linear_head.py` 哈希相同（`c52a465d...efa424`），`dpt_head.py` 也相同（`7368f698...00310`）；`model.py` 与 `pos_embed.py` 不同。因此“独立版与 fork 的 head 源文件一定不同”是错误概括。真正已知差别是**实际选用的头、检查点、模型源码版本和下游处理链**。未加载 VMem 512 权重，不推断其实际性能。

## S6 数据流与严格留出

建议冻结三个块、每块原 24 图，仍用 B0 开发、B1/B2 测试；不得按 S5 分数换图。S3 的历史结果保持不动，所有 S6 输入和基线都在新目录、同一 224 裁剪视野下运行。

**严格版本需要新的 query 状态规则。** S5 后四帧均 `update=True`，所以第 21–23 帧的预测可见此前 query RGB 的潜在状态；仅不写 surfel 并不能消除这一点。若 S6 要求所有记忆都只含前 20 帧，应在新的、独立记录的推理中使用前 20 帧 `update=True`、后 4 帧 `update=False`，所有 `reset=False`，每块新进程。当前帧 RGB 仍用于估计查询位姿，但不会写回潜在状态。不要使用只处理 ray-map 的 `inference_step`。前 20 帧输出应与 S5 在适当数值容差内一致，作为实现核验；不能覆盖 S5。

建图器只接收帧 0–19，写入来源 ID 仅为 0–19；第 20 次写入后冻结 surfel 数量、位置、法向、半径和来源。查询 20–23 前后比较记忆哈希，任何改变均视为接口错误。即使运行跨视图清理，也只能读当前历史前缀，不得加入 query 的预测或实测深度。用全部 20 张历史事后清理再重放写入，会给早期写入未来历史信息，应标为离线历史控制，不能冒充原在线顺序。

## 坐标、尺度与条件分工

主支路建议定义 `Q_i=inv(P_0)@P_i`，其中 P 是预测 camera_c2w；在块首相机的光学坐标系中，`X_i=Q_i @ backproject(Z_self_i,K_crop)`。半径和相机平移使用同一模型单位。不得直接把 raw other 当成该 X，也不得用 other 的 confidence 去筛 self 的深度而不说明对应关系；此入口配对 `Z_self/conf_self`。

**GT 只评分的主支路不得把 S5 的深度校准比例带回建图或选帧。** 如果需要稳定尺度，可用第一张预测正 Z 的中位数定义纯预测的无量纲单位，同时等比缩放点、深度、相机平移和半径；位置合并阈值也由该单位下的半径产生。原版位姿距离中的 translation weight=0.1 随此变为无量纲设置，必须冻结并报告，不能称原版米制配置完全复现。尺度、场景初始旋转和 GT 对齐只能在选帧完成后的评分副本中使用，不回写模型输入或记忆。

建议区分下列条件，不能混报：

| 条件 | 建图/检索可读信息 | 解释 |
|---|---|---|
| 主条件：预测深度＋预测姿态 | RGB 预测、固定相机标定；无 mocap/实测深度 | 符合 GT 只评分；包含深度与位姿的联合错误 |
| 可选诊断控制：同预测深度＋GT 姿态 | 明确允许历史和 query GT 姿态，以及将其平移换到模型单位所需的校准 | **oracle 条件**，违反“所有支路 GT 只评分”的字面限制，必须另列协议；有助定位位姿影响，但不可当实际系统结果 |
| 测量基线 | 历史 Kinect 深度＋GT 姿态 | 测量参照；在同一裁剪、采样、半径、检索视野下新跑，不直接搬 S3 分数来比较 |

因此可以分开做预测点＋GT 姿态控制与全预测姿态，但 GT 控制须显式承认额外信息。若坚持所有输入条件都 GT 只评分，就不运行该控制；只保留 GT 在独立评分端。不要为制造“纯位姿消融”悄悄用全轨迹 Umeyama/ICP 或 query 深度拟合尺度。

`K_crop` 应由原图标定按实际 640×480→299×224 和 crop[37,0,261,224] 变换，分别处理 x/y 比例及像素中心约定；不能沿用原图 K，也不能简单假定 fx=fy。S3 现有 selector 写死了 640×480 的 K 缩放，不能直接套到方形 224 输出。新接口应显式接收裁剪尺寸和 K，例如统一到 160×160 的检索网格；保留原版 focal×0.65 的更宽检索视野与居中主点近似，并记录该近似。所有比较条件使用同一渲染视野；GT 支持评分仍限实际可观测裁剪区域，宽视野不产生不存在的参考支持。

## 可运行的实施顺序与停点

1. **先核验桥接。** 新模块显式输入 predicted depth、confidence、crop K、predicted optical c2w，构造世界点、邻域法向、半径及 source ID；不修改 S3 文件。对合成平面验证反投影/坐标翻轴/法向/半径；对保存 raw 输出检查有限值、正深度、单位和稀疏采样映射。cropped stride、边界判定和半径随采样比例的处理必须事前冻结，不可照抄 VMem 的 0.05 缩小后宣称密度等价。
2. **先接已验证的检索控制。** 比较 `first_write/frame_mean`，同输入、同 4 帧上下文和 NMS；frame_mean 仍只是简单控制。主过滤先明确为局部有效性＋选定的预测 confidence/depth 规则，不能叫完整 VMem baseline。记录每帧剔除原因、写入数、合并数、存量、来源及最终选择；不能只展示变好样例。
3. **清理作为独立因素。** 若接固定 `clean_pointcloud`，使用与本桥接定义一致的预测 K、位姿、点、深度和 confidence，仅历史前缀可见；核对它只是降置信。另列“未清理/此前缀清理”，先验证语义，避免同时改变更新规则、点密度、内参和清理后将总变化归因于均值更新。全局优化器并非第一版桥接的必要条件，未接入时必须明确排除完整 VMem 复现声明。
4. **独立评分后再解释。** 选帧逻辑结束并封存结果之后，才用 GT 相机及历史/query 实测深度构造固定支持 mask。同一查询、同一支持 mask 比较两种记忆，另报 recent4、预测位姿 nearest4 和全历史支持上界；query depth 不参与建图、清理、阈值、候选排序或 NMS。几何误差与参考支持覆盖分开报告，换帧不自动等于变差，更不等于视频质量下降。

最初 S6 可继续只用本机与当前 224 模型。它会把“真实学习估计→存储→选帧”接起来，仍不会自动补齐 512 DPT、fork 全局对齐/原版完整清理、gated 视频生成或新方法创新性。未核验坐标/单位/留出不变量前不进入大规模扫参；本文件不构成已完成这些步骤的证据。
