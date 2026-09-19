# ALT-TUM-01：真实 TUM RGB-D 近邻检索与最小公平实验协议

- 检索日期：2026-09-12（Asia/Shanghai）
- 任务边界：围绕真实 TUM RGB-D 或相似 RGB-D 数据，检查近年顶会/顶级会议工作是否已经覆盖长期几何、视角/关键帧选择、风险敏感评价；只做文献和官方代码审查，不下载数据、不运行论文代码、不宣称 GRC-Memory 已有创新。
- 与 S92 的去重：不重复 S92 已记录的 Conformal Risk Training（NeurIPS 2025）、Active anytime-valid risk controlling prediction sets（NeurIPS 2024）、MemoNav（CVPR 2024）、Maximizing the Value of Predictions in Control（NeurIPS 2025）。

## 1. 数据事实与 TUM 的适用边界

TUM RGB-D 官方数据页说明：数据包含同步的 RGB、depth 和相机轨迹；彩色/深度图像以 30 Hz、640×480 记录，轨迹由 100 Hz 高精度运动捕捉系统获得，并提供用于评估视觉里程计/SLAM 的相机轨迹标准。官方页面还明确给出 CC BY 4.0 数据许可和评价工具入口：

- 官方数据与 benchmark：[TUM RGB-D SLAM Dataset and Benchmark](https://cvg.cit.tum.de/data/datasets/rgbd-dataset)
- 原始 benchmark 论文：Sturm et al., *A Benchmark for the Evaluation of RGB-D SLAM Systems*, IROS 2012（官方页面列出论文和 BibTeX）。

这使 TUM 适合做 **RGB-D 配对、时间切分、未来深度误差、相机轨迹误差**；但不能默认把 TUM 当作高质量全场景 3D mesh ground truth。RTG-SLAM 的官方论文补充材料明确写道，TUM-RGBD 的 3D model 质量较低，因而不适合评估 geometry accuracy；该文把 TUM 主要用于 tracking/time/memory，而将 geometry accuracy 放在 Replica/ScanNet++ 等有相应几何评价条件的数据上。

因此 ALT-TUM-01 的安全定位是：**用 TUM 验证历史记忆选择是否预测未来 RGB-D 几何和轨迹误差；不用 TUM 的低质量三维模型声称完整表面重建质量。**

## 2. 近邻一：CVPR 2024 RGB-D SLAM 统一 benchmark

**论文**：Hua and Wang, “Benchmarking Implicit Neural Representation and Geometric Rendering in Real-Time RGB-D SLAM,” CVPR 2024。

- 官方 CVPR 页面：[CVPR Open Access record](https://openaccess.thecvf.com/content/CVPR2024/html/Hua_Benchmarking_Implicit_Neural_Representation_and_Geometric_Rendering_in_Real-Time_RGB-D_CVPR_2024_paper.html)
- 官方 PDF：[CVPR paper PDF](https://openaccess.thecvf.com/content/CVPR2024/papers/Hua_Benchmarking_Implicit_Neural_Representation_and_Geometric_Rendering_in_Real-Time_RGB-D_CVPR_2024_paper.pdf)
- 作者项目页：[NeRF-SLAM benchmark project](https://vlis2022.github.io/nerf-slam-benchmark/)

论文贡献是建立统一的 RGB-D SLAM benchmark，系统比较 implicit neural representation 与 geometric rendering 的设计选择，并强调公平评价协议。它覆盖了不同表征、渲染函数、mapping/localization 设计，核心指标包括 tracking、mapping、rendering、accuracy/completion 等。

**对 GRC 的压力：**“提出一个新的几何评价协议”本身已有直接近邻；GRC 不能只说有 geometry-aware score。GRC 必须把研究对象从“表示/渲染模块”变成“历史观测记忆选择”，并且在同一 world-model consumer、同一候选池、同一记忆预算下比较。

**与 GRC 的精确差异：**

- benchmark 选择的是 INR、rendering function 和 SLAM design；GRC 选择的是历史 RGB-D observation item。
- benchmark 主要评价当前 mapping/localization/rendering；GRC 必须评价未参与选择的独立 future RGB-D/pose。
- benchmark 的公平协议思想可直接复用，但它不提供 source-identity intervention、未来信息增量或风险校准记忆。

## 3. 近邻二：GS-SLAM（CVPR 2024）

**论文**：Yan et al., “GS-SLAM: Dense Visual SLAM with 3D Gaussian Splatting,” CVPR 2024 Highlight。

- 官方项目页：[GS-SLAM](https://gs-slam.github.io/)
- 官方论文 PDF：[CVPR paper PDF](https://openaccess.thecvf.com/content/CVPR2024/papers/Yan_GS-SLAM_Dense_Visual_SLAM_with_3D_Gaussian_Splatting_CVPR_2024_paper.pdf)
- 官方项目页说明：该系统在 TUM-RGBD 上报告 tracking 结果，并使用 coarse-to-fine 方式选择可靠 3D Gaussians。

GS-SLAM 的关键机制包括：3D Gaussian scene representation、RGB-D differentiable rendering、adaptive Gaussian expansion，以及用于 pose estimation 的 coarse-to-fine reliable Gaussian selection。它在 TUM-RGBD 和 Replica 上报告 tracking/mapping/rendering 结果。

**对 GRC 的压力：**“可靠几何元素选择”已经有近邻。若 GRC 仅把历史帧按 confidence/reprojection error 排序并保留 top-k，审稿人可能认为这是把 GS-SLAM 的 reliable primitive selection 改成 frame-level gating。

**与 GRC 的精确差异：**

- GS-SLAM 选择的是当前地图中的 Gaussian primitives/pixels，以提高当前 pose optimization；GRC 选择跨时间的历史观测，目标是未来几何状态。
- GS-SLAM 没有把历史 item 的风险校准为独立 future geometry 的预测上界。
- GS-SLAM 的 TUM 结果主要验证 tracking/rendering；GRC 若使用 TUM，应另外报告未来深度 AbsRel、reprojection error 和 pose error，避免把当前 tracking 优化误称 future prediction。

## 4. 近邻三：Photo-SLAM（CVPR 2024）

**论文**：Huang et al., “Photo-SLAM: Real-time Simultaneous Localization and Photorealistic Mapping for Monocular, Stereo, and RGB-D Cameras,” CVPR 2024。

- 官方代码：[HuajianUP/Photo-SLAM](https://github.com/HuajianUP/Photo-SLAM)
- 官方论文 PDF：[CVPR paper PDF](https://openaccess.thecvf.com/content/CVPR2024/papers/Huang_Photo-SLAM_Real-time_Simultaneous_Localization_and_Photorealistic_Mapping_for_Monocular_Stereo_CVPR_2024_paper.pdf)
- 官方代码明确提供 TUM RGB-D 下载脚本、RGB-D evaluation scripts、EVO-based trajectory evaluation，并说明部分 TUM 序列需要按照 camera.yaml 进行去畸变。

Photo-SLAM 的实验重点是实时 localization、photorealistic mapping 和 rendering efficiency。官方代码 README 还说明每个序列运行五次以降低系统非确定性影响，并提供结果日志格式。

**对 GRC 的压力与可复用点：**

- 压力：TUM 上的单序列结果可能依赖相机畸变处理、配置文件、平台和随机性；GRC 必须锁定 intrinsics、distortion handling、frame association、seed/noise 和重复次数。
- 可复用：五次重复和日志化 evaluation pipeline 可成为 ALT-TUM-01 的工程基线；但 GRC 还需要历史集合的 paired intervention，而非只对最终地图评分。

**与 GRC 的精确差异：**

- Photo-SLAM 的输入通常是连续 RGB-D 流，目标是 SLAM/map/rendering；GRC 的实验要把历史候选集合显式暴露给同一个 consumer。
- Photo-SLAM 没有比较 risk-only、utility-only、risk+utility 的记忆选择策略，也没有 source-identity 替换/删除实验。
- 不能用 Photo-SLAM 的 PSNR/SSIM/LPIPS 结果代替未来几何误差；GRC 的主指标应是未来 depth AbsRel、reprojection error、ATE/RPE，渲染指标只作为辅助。

## 5. 近邻四：RTG-SLAM（SIGGRAPH 2024）

**论文**：Peng et al., “RTG-SLAM: Real-time 3D Reconstruction at Scale Using Gaussian Splatting,” ACM SIGGRAPH Conference Papers 2024。

- 官方代码：[MisEty/RTG-SLAM](https://github.com/MisEty/RTG-SLAM)
- 官方论文 PDF：[RTG-SLAM PDF](https://gapszju.github.io/RTG-SLAM/static/pdfs/RTG-SLAM_arxiv.pdf)

RTG-SLAM 在在线 RGB-D 重建中按照当前帧的 newly observed、large color error、large depth error 像素增添 Gaussians，并区分 stable/unstable Gaussians，只优化和渲染不稳定部分。论文补充材料给出 TUM-RGBD 的 FPS 和 memory cost，但明确指出 TUM-RGBD 的低质量 3D model 使 geometry accuracy 不可行；因此几何 accuracy 主要在 Replica/ScanNet++ 评估。

**对 GRC 的压力：**RTG-SLAM 已把“几何/颜色误差驱动的在线选择”和“稳定/不稳定记忆状态”用于真实 RGB-D 流。GRC 不能把“按历史几何误差保留记忆”单独包装成全新机制。

**与 GRC 的精确差异：**

- RTG-SLAM 选择的是当前地图中的 Gaussian update/render budget；GRC 选择历史 observation item 并预测未来 world state。
- RTG-SLAM 的 error signal 用于当前重建稳定性，不是校准后的未来风险上界。
- RTG-SLAM 明确展示了 TUM 的 geometry-evaluation limitation；ALT-TUM-01 必须把 TUM 的几何真值限定为未来帧 RGB-D/pose，而不把 TUM 3D model 当高质量表面真值。

## 6. 近邻五：MASt3R-SLAM（CVPR 2025）

**论文**：Murai, Dexheimer, and Davison, “MASt3R-SLAM: Real-Time Dense SLAM with 3D Reconstruction Priors,” CVPR 2025。

- 官方代码：[rmurai0610/MASt3R-SLAM](https://github.com/rmurai0610/MASt3R-SLAM)
- 官方项目页：[MASt3R-SLAM project](https://edexheim.github.io/mast3r-slam/)
- 官方论文 PDF：[CVPR 2025 PDF](https://openaccess.thecvf.com/content/CVPR2025/papers/Murai_MASt3R-SLAM_Real-Time_Dense_SLAM_with_3D_Reconstruction_Priors_CVPR_2025_paper.pdf)

MASt3R-SLAM 使用 MASt3R/DUSt3R 类 two-view 3D reconstruction prior，通过 pointmap matching、local fusion、loop closure 和 global optimization 进行实时 dense SLAM；官方代码提供 TUM-RGBD 下载和 calibrated/no-calib evaluation scripts。

**对 GRC 的压力：**强 two-view 3D prior 可以从相邻/检索帧中得到强几何证据；如果 GRC 的风险估计只依赖单帧 reprojection/depth residual，而不与强 pointmap/matching baseline 比较，审稿人会怀疑所谓 geometry risk 只是弱特征质量的替代指标。

**与 GRC 的精确差异：**

- MASt3R-SLAM 重点是 pose/pointmap/loop-closure estimation；GRC 重点是长期历史记忆选择。
- MASt3R-SLAM 的 retrieval/matching 可作为强 `geometry-aware retrieval` baseline，但它没有固定记忆预算下的 calibrated future-risk selection。
- 必须报告 GPU/host memory、候选历史数量、检索时间和 consumer 运行时间，否则不能与 GRC 的固定预算比较。

## 7. TUM 的数据泄漏与评价风险清单

ALT-TUM-01 不应把“有 RGB-D+pose”直接当作无泄漏。至少冻结以下规则：

1. **时间切分**：历史候选来自前缀 `t <= T`; future evaluation 来自严格后缀 `t > T+gap`。future RGB、depth、pose 只能在最终评分阶段读取。
2. **风险校准独立**：风险分位数、阈值和任何 normalization 只能由 calibration sequences 计算，不能用目标序列 future depth/pose。
3. **source identity 保留**：每个 memory item 必须有 sequence、timestamp、frame id；删除/替换实验必须保持相同候选池、相同噪声、相同生成步数。
4. **序列级 split**：不能在同一序列的相邻帧同时调参和报告结果；至少将 sequence 划分为 calibration / selection-development / held-out evaluation。
5. **相机模型固定**：明确 fr1/fr2/fr3 的 intrinsics、distortion、RGB-depth association 和 depth scale；Photo-SLAM 官方代码说明部分 TUM 序列需要去畸变。
6. **不把 self-revisit 当独立未来**：重复看到同一桌面/办公室区域不能当作独立 world-state generalization；要报告视角、时间间隔和 scene overlap。
7. **TUM geometry limitation**：不使用低质量 TUM 3D model 计算高可信 mesh accuracy；使用 paired future depth、reprojection 和 trajectory metrics，并把 mesh accuracy 作为不可用/辅助项明确写出。
8. **消费路径固定**：GRC 与 recent/random/coverage/confidence/pose-distance/CVaR-risk 基线必须使用同一个 world-model consumer、同一个历史 token/frame budget 和同一个推理随机性设置。
9. **重复实验**：参考 Photo-SLAM 的五次重复原则，至少固定多个 seeds/noise replay；报告 paired mean、median、worst-10%/CVaR 与 bootstrap 区间。
10. **容量记账**：同时记录 GPU cache、CPU/host memory、历史 token、检索时间和总推理时间；不能只报告 GPU 显存。

## 8. ALT-TUM-01 的最小公平 baseline

### 数据与任务

- 数据：TUM RGB-D 官方 benchmark。
- 先选静态序列 `fr1/desk`、`fr2/xyz`、`fr3/office`，再单独报告动态序列，避免把动态物体失效和长期几何风险混为一谈。
- 每个序列切成 `history prefix`、`calibration window`、`held-out future suffix`；future suffix 只用于评价。
- 候选池固定为前缀中的 N 个历史 RGB-D frames，槽位预算 `k` 取预注册值（例如 k=4/8/16），所有方法使用相同 N、k 和 consumer。

### 选择器

1. `Recent-k`：最近 k 帧。
2. `Uniform-k`：按时间均匀采样。
3. `Random-k`：固定 seed 的随机采样。
4. `PoseCoverage-k`：用历史相机位姿/视角覆盖最大化。
5. `Appearance/Confidence-k`：仅用 RGB similarity 或模型 confidence。
6. `ReprojectionRisk-k`：按历史重投影误差排序。
7. `DepthRisk-k`：按历史 RGB-D 深度不一致排序。
8. `CVaR-Risk-k`：同一历史风险分数下做尾部风险排序，作为风险敏感但非 GRC 的基线。
9. `GeometryUtility-k`：仅最大化历史几何信息增益或 coverage，测试“utility-only”。
10. `GRC candidate`：校准几何风险 + utility + 固定 cost；只有 Gate0 通过后才能运行和验收。
11. `Oracle-future`：读取 future 仅作为上界/诊断，不进入正式方法比较，不报告为可部署方法。

### 指标

- 未来深度：AbsRel、RMSE、δ<1.25、valid-depth coverage。
- 几何一致性：future reprojection error、depth edge/normal consistency（若数据和实现支持）。
- 相机：ATE、RPE（使用 TUM 官方 ground-truth trajectory 评价工具）。
- 视觉质量：PSNR/SSIM/LPIPS 仅作为辅助，不能代替几何主指标。
- 风险：全体 paired mean、median、worst-10%、CVaR@0.9；同时报告改善比例和恶化质量，防止 S91R/S92 中“多数像素改善但均值变差”的重复误判。
- 成本：GPU cache、CPU/host memory、历史帧/token 数、selection latency、end-to-end latency。
- 统计：sequence-level paired bootstrap；不得把单帧/单像素当作独立跨场景证据。

## 9. 对 GRC 候选的审稿式结论

- `risk-aware selection` 已被 conformal/sequential risk-control 和 RGB-D/SLAM 的 error-driven selection 分别覆盖；它不能单独构成创新。
- `memory/forgetting/gating` 已被视觉导航和 SLAM map update 近邻覆盖；普通 learned gate 不够。
- TUM 的真正可保留研究问题是：**在真实同步 RGB-D 与相机轨迹上，历史几何风险是否能在固定 observation budget 下预测独立 future RGB-D/pose 的增量收益，并在 capacity-matched consumer 中优于 recent/uniform/coverage/confidence/CVaR baselines？**
- 当前状态：`candidate / novelty UNKNOWN / not validated`。ALT-TUM-01 只能先完成数据资格、协议和可复现实验框架；不能提前称为 PhD/CCF-A 方法。

## 10. 本轮证据结论

本轮检索得到的最有价值事实不是某个“新模块”，而是两个约束：

1. CVPR 2024 benchmark 说明公平协议本身已是研究对象，GRC 必须证明未来几何收益而非再造一个 benchmark。
2. RTG-SLAM 官方补充明确暴露 TUM 3D geometry ground-truth limitation；ALT-TUM-01 必须以 future RGB-D/pose 评价长期几何，而不能把 TUM mesh accuracy 当作强证据。

以上内容仅是检索与实验协议输入，尚未下载、运行或验证任何近邻方法。 
