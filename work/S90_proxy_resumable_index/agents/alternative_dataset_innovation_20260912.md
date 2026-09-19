# 替代数据路线审查：支持“历史几何风险 → 未来几何误差”的候选数据集

- **记录时间**：2026-09-12（Asia/Shanghai；网页检索实际完成于本轮）
- **任务性质**：英文官方资料检索与数据合同审查；没有下载数据、没有运行模型、没有产生实验结果。
- **当前科学边界**：S91（未来几何风险增量预测试验，GRC-Pilot）仍为 `BLOCKED_ON_GATE0`。本文件只决定哪些数据集值得进入新的预注册 Gate0，不把替代数据的存在当作 S91 已通过。
- **原始研究问题**：在只使用历史 RGB-D/几何、时间戳、相机和冻结模型状态的条件下，历史几何风险是否能预测**独立未来查询**的 3D 位置误差或声明过的相机深度误差？

## 1. 采用的资格合同

一个候选集只有在满足下列条件后，才可能进入正式实验：

1. 每个历史候选同时具有 RGB（或可明确声明的观测）、深度/几何、时间顺序和相机内外参；
2. 未来查询在输入封存后才读取；未来 RGB/深度/位姿/误差不能进入选择器；
3. 至少能按**场景或序列**预先分出 3 个独立测试单元，不能把同一场景切成多个窗口后冒充 3 个场景；
4. 每个测试单元至少有 6 个历史候选和 3 个未来查询，且未来深度/3D真值可评分；
5. 能在本机有限磁盘和 CPU 预算下先完成一个小的、可复查的资格检查；
6. 许可、下载方式和数据处理限制能被记录。若许可条款不清，不能作为默认正式集。

S91 既定选择器、预算公平性和停止规则仍适用：`random-k`、`recent-k`、`nearest-pose-k`、`coverage-k`、`utility-only`、`confidence-only`、`risk-only`、`risk+utility` 和 `worldmem-style` 必须共享候选池、k、消费者、随机数和总成本核算。

## 2. 候选比较（证据先于评分）

评分为审查排序，不是实验结果：

- **配对与相机**：是否有同步/可对齐 RGB、深度、内参、外参/轨迹；
- **独立未来**：能否在预注册规则下得到真正未来查询和跨场景测试；
- **动态/长时性**：是否接近 proposal 的动态 3D/4D 与长期记忆问题；
- **本机成本**：先做小试验的下载、解码和存储门槛；
- **许可与可复现性**：官方许可、下载步骤、是否依赖申请或登录。

| 候选 | 官方事实与字段 | 独立未来/场景可行性 | 本机成本与许可风险 | 与 proposal 的判断 | 审查分数 |
|---|---|---|---|---|---:|
| **TUM RGB-D** | 官方说明为 Kinect RGB-D，30 Hz、640×480，mocap 轨迹 100 Hz；官方格式给出已注册 RGB/深度、时间戳、相机轨迹格式 `timestamp tx ty tz qx qy qz qw`；CC BY 4.0（代码 BSD-2-Clause）。[数据总页](https://cvg.cit.tum.de/data/datasets/rgbd-dataset) [文件格式](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats) | 序列级拆分容易预注册；`fr1/desk`、`fr2/xyz` 等短序列可提供 ≥6 历史和 ≥3 后续查询，但多数场景静态，动态世界结论范围有限。 | 官方下载页列出单序列约 0.36–2.39 GB；可先只下载 3–6 个序列。许可清楚、入口稳定。 | **最适合低成本真实数据 Gate0 和基线校准**；不能单独证明长期动态 4D。 | **4.4/5** |
| **Bonn RGB-D Dynamic** | 官方称 24 个动态序列加 2 个静态序列；OptiTrack 传感器真值位姿；深度已注册到 RGB；提供完整/子采样真值点云和 TUM 兼容格式；单序列约 236–516 MB，全集 16.4 GB。[官方页面](https://www.ipb.uni-bonn.de/data/rgbd-dynamic-dataset/) | 24 个动态序列可做序列级留出；未来帧有深度和轨迹，能测动态遮挡/物体运动造成的风险。需核对每条序列的场景身份和动态对象是否出现在点云真值中。 | 可从单条 236–326 MB 序列开始；官方页面未在可见正文中给出明确数据许可证，正式发布前必须记录许可确认。4 GB 全点云不适合作为首步下载。 | **最贴近“几何风险在动态场景中伤害未来”的真实验证**；比 TUM 更有解释力，但数据许可和真值点云定义需单独 Gate0。 | **4.3/5** |
| **Dynamic Replica (CVPR 2023)** | 官方 repo 说明 524 个视频、145,200 个立体帧，含左右相机内外参、深度、实例/前景掩码、光流和长期轨迹；train/valid/test/real 分割；解压大小 train 1.8 TB、test 328 GB、valid 106 GB、real 152 MB。[官方项目](https://dynamic-stereo.github.io/) [官方代码/数据说明](https://github.com/facebookresearch/dynamic_stereo) | 明确有 train/valid/test，适合严格跨视频划分；但它是**双目动态视频**，不是单 Kinect 式 RGB-D。可将左相机 RGB+深度作为观测，但要在协议中声明输入/立体来源。 | 数据需先接受 Dynamic Replica License；完整 splits 远超本机合理存储，real split 仅 152 MB 但须确认其字段覆盖和是否足够多场景。官方评估说明高分辨率需要 32 GB GPU；本项目无远程 GPU，不应跑官方模型训练。 | **动态性和独立 split 最强的补充压力测试**；适合下载少量 real/小子集做数据合同审查，不能把 1.8 TB 计划当作本机路线。 | **3.9/5** |
| **PointOdyssey (ICCV 2023)** | 官方页面给出 159 个合成视频、平均 2,000 帧、约 20 万帧；含 RGB、深度、实例分割、法向、相机内参/外参、2D/3D 点轨迹，部分场景含多同步视角；Google Drive/Hugging Face 可下载。[官方项目](https://pointodyssey.com/) | 长视频天然可构造历史/未来，但官方项目页没有在可见摘要中承诺独立 train/val/test 场景划分；必须自行按视频/场景预注册留出，避免同源渲染泄漏。合成运动和渲染真值不能替代真实传感器结果。 | 下载入口公开，但体量与具体分片需访问后核对；无真实采集许可问题，需遵守仓库/数据条款。 | **低成本长时机制和代码管线压力测试**；适合先测 S91 风险指标是否有预测性，结论只能标记 synthetic。 | **3.8/5** |
| **ScanNet** | 官方称 1500+ 扫描、250 万 RGB-D views；每个 `.sens` 流含压缩 RGB、深度、相机位姿和其他数据；官方 exporter 可导出颜色、深度、位姿、内参。[主页](https://www.scan-net.org/ScanNet/) [Sens格式](https://www.scan-net.org/ScanNet/SensReader/) [Exporter](https://www.scan-net.org/ScanNet/SensReader/python/) | 场景数足够做 scene-level split，未来视角/帧有深度和位姿；主要是静态室内扫描，不直接覆盖动态 4D。 | 下载需填写 Terms of Use 并用 institutional email 发给官方；体量和审批未知。当前不能把“网页可见”当作已获得访问权。 | **最强的静态跨场景规模验证候选**，但不适合本机立即推进，也不能解决动态 world modeling 的全部问题。 | **3.6/5** |
| **Replica（18 个室内重建）** | 官方仓库提供 18 个高质量室内重建、稠密几何/纹理/语义；SDK 支持按程序轨迹 headless 渲染。它不是原始 RGB-D 时间流，可由渲染器产生 RGB/深度/位姿。[官方仓库](https://github.com/facebookresearch/Replica-Dataset) | 可预注册跨场景、跨相机轨迹；未来查询真值由 mesh/渲染器得到，但历史与未来来自同一静态 mesh，不能称真实未见传感器未来。 | `download.sh` 可下载；研究条款限定研究/教育和非商业使用。完整 SDK 编译需要 Pangolin/Eigen，渲染器环境成本中等。 | **非常适合验证投影、风险计算、future leakage 和选择器实现**；只能作为 synthetic oracle/debug，不应单独支持真实方法结论。 | **3.4/5** |
| **ScanNet++** | 1006 场景；官方默认下载约 1.5 TB，iPhone RGB 视频、对齐 LiDAR 深度、ARKit pose/intrinsic；NVS split 856/50/50，但 test 不提供 scan data。[官方文档](https://scannetpp.mlsg.cit.tum.de/scannetpp/documentation) | 有明确 scene split；然而 NVS test 缺 scan/depth，无法直接把 test 当深度未来真值。可在 train/val 做内部验证，但会损失独立性。 | 1.5 TB 默认下载（高分辨率可到 9 TB），明显超出本机低成本路线；许可/访问流程需另核。 | **目前不推荐**，除非获得算力和存储；不能因“1006 scenes”就把它写成可立即实验数据。 | **2.8/5** |

## 3. 审查式排序与决定

### 首选：TUM RGB-D + Bonn Dynamic 的双层真实路线

1. **TUM 小样本资格门（建议候选名称：`ALT-TUM-01（TUM真实RGB-D未来深度误差资格试验）`）**：先下载 3–6 条短序列，按序列预注册 3 条测试单元；从每条序列前段选历史，封存后段作为未来。只做数据字段、时间顺序、相机投影、深度有效率和未来误差定义，不先声称 GRC 有效。
2. **Bonn 动态确认门（建议候选名称：`ALT-BONN-01（Bonn动态RGB-D风险到未来误差试验）`）**：若 TUM 通过字段门，选 3–6 条动态序列，保留完整的遮挡/人和物体运动，先检查每条的 depth/RGB 注册、轨迹和动态点云真值。只要动态点云真值不能对应未来像素，立即降级为 camera-z-depth outcome，而不是硬算 3D object error。
3. 两者都必须在读未来答案前冻结 `k`、历史/未来窗口、选择器列表、成本预算、风险定义和停止规则。不能从 TUM 结果挑出最有利窗口再迁移到 Bonn。

### 第二层：Dynamic Replica / PointOdyssey 机制压力测试

- 用于检验“长时/动态/遮挡”是否让风险指标比最近帧或 pose-only 选择更有预测性；只报告 synthetic 或 stereo-derived 标签。
- Dynamic Replica 的完整官方 split 不适合本机；若 `real`/单小分片无法给出 ≥3 独立场景和 ≥6 历史候选，则停止，不通过削弱合同来凑样本。
- PointOdyssey 的多视角子集必须明确哪些视角属于同一渲染场景；不能把同一场景的视角拆到 train/test 后称未见场景。

### 第三层：Replica / ScanNet 用于边界和规模

- Replica 用于几何投影、遮挡、future leakage 和选择器代码的可重复 oracle；不作为真实传感器主结果。
- ScanNet 若日后获得合规访问，可做静态跨场景规模验证；目前下载审批不确定，不应让它阻塞 TUM/Bonn 的小试验。
- ScanNet++ 目前明确受 1.5 TB 起始存储限制，不应在本机无外部资源时列为主路线。

## 4. 哪些候选真正能回答当前第一轮假设？

| 假设证据层 | 最合适数据 | 能回答什么 | 不能回答什么 |
|---|---|---|---|
| 真实、低成本、相机/深度配对 | TUM | 历史几何残差是否预测后续相机 z-depth / 3D 投影误差；静态场景下的选择器公平对照 | 长期动态 4D、复杂物体状态变化 |
| 真实、动态、未来深度 | Bonn | 遮挡/人和物运动下风险与未来深度误差的关系 | 若点云真值不含动态对象，则不能声称动态 3D object truth |
| 合成长视频、显式 split | Dynamic Replica | 长时动态和跨视频泛化；可做机制反例 | 本机存储和 GPU 约束；双目协议不是原始 RGB-D |
| 合成长视频、多模态 | PointOdyssey | 长时历史/未来、轨迹级 risk 的快速可控检查 | 官方摘要未给出足够明确的独立 scene split；不能支持真实世界结论 |
| 真实、规模大、静态场景 | ScanNet | 规模化跨场景静态新视角深度评估 | 下载审批和存储；不等于动态 world model |
| 可控渲染 oracle | Replica | 算法投影与反事实选择器的单元测试 | 真实采集、传感器噪声、动态场景 |

## 5. 结论（仅对数据路线，不是方法结论）

- **最实际的替代 Gate0** 是先用 TUM，再用 Bonn 动态序列；两者字段和时间结构最容易写出可审计的历史/未来合同。
- **最有创新判别价值** 是 Bonn：如果风险→未来误差在动态遮挡条件下仍比 pose-only/recent 强，才有理由继续 GRC-Memory；如果只在静态 TUM 成立，不足以支撑 proposal 的动态 4D 叙事。
- **最适合低成本机制调试** 是 Replica 和 PointOdyssey，但这两者的结果必须单独标为 synthetic；不能与真实数据平均成一个数字。
- **最不应立即投入本机存储** 是 ScanNet++ 和 Dynamic Replica 完整 splits；它们的规模事实反而说明当前要申请算力/存储，而不是偷偷缩短数据合同。
- 任何替代数据集都必须新建数据来源 receipt、许可记录、独立场景清单和 preflight manifest；不能改写 RTMV S90/S91 的历史结果，也不能把“数据可获得”写成“GRC 方法已验证”。

## 6. 检索证据索引（原始入口）

1. TUM RGB-D 总页：<https://cvg.cit.tum.de/data/datasets/rgbd-dataset>
2. TUM 文件格式：<https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats>
3. TUM 下载页：<https://cvg.cit.tum.de/data/datasets/rgbd-dataset/download>
4. Bonn RGB-D Dynamic：<https://www.ipb.uni-bonn.de/data/rgbd-dynamic-dataset/>
5. Dynamic Replica 项目页：<https://dynamic-stereo.github.io/>
6. Dynamic Stereo 官方代码与下载说明：<https://github.com/facebookresearch/dynamic_stereo>
7. PointOdyssey 官方项目页：<https://pointodyssey.com/>
8. ScanNet 官方主页：<https://www.scan-net.org/ScanNet/>
9. ScanNet Sens 格式：<https://www.scan-net.org/ScanNet/SensReader/>
10. ScanNet Python exporter：<https://www.scan-net.org/ScanNet/SensReader/python/>
11. Replica 官方仓库：<https://github.com/facebookresearch/Replica-Dataset>
12. ScanNet++ 官方文档：<https://scannetpp.mlsg.cit.tum.de/scannetpp/documentation>

**证据限制**：本轮只做官方网页/官方仓库检索，未下载任何数据或接受任何许可协议；上述“适合度”是研究设计判断，不是运行结果。

## 7. 补充发现：3RScan 与 ARKitScenes 值得单独保留

### 3RScan（ICCV 2019 / RIO 数据路线）

官方工具仓库把 3RScan 描述为 478 个自然变化室内环境、1482 个重建/快照；每条序列有对齐 RGB-D、纹理 mesh、6DoF 相机姿态和内参，同一环境不同扫描之间还有全局变换、稳定实例 ID 及发生变化对象的变换真值。仓库公开的 split 文件当前可数到 train 385、val 47、test 46 个 scan ID；这些是 scan 级清单，不能直接当作 478 个相互独立环境，仍需按 `3RScan.json` 的 reference/scans 分组。[官方工具仓库](https://github.com/WaldJohannaU/3RScan) 官方文档说明下载需填写 Terms of Use，且测试集只能在最终系统上报告，不能反复调参。[官方文档](https://vmnavab26.in.tum.de/3RScan/documentation.php)

**审查判断**：这是目前概念上最接近“长期几何记忆”和“未来世界状态”的公开候选：它不只是连续帧，还把同一环境的自然变化和对象级变换显式记录下来。它仍有两个必须先解决的识别限制：

- 同一环境的 repeated scan 如果跨 train/test 混用，会产生严重场景/对象泄漏；必须按 environment/reference group 做留出，而不是按单个 scanId 随机切分。
- 它是 RGB-D 扫描序列和离散重扫，不是长时间连续视频；主结果应分别标成“重扫后几何变化预测”或“序列内未来深度误差”，不能直接写成连续 4D world model。

**建议候选名称**：`ALT-3RSCAN-01（自然变化环境的长期几何风险试验）`。在许可获批且先完成 environment-group manifest 后，3RScan 的优先级可高于 ScanNet；如果本机只能小规模运行，先选择 3 个环境组、每组一个历史序列和一个未来重扫，严格保留未见环境组。

### ARKitScenes（Apple，真实移动 RGB-D）

官方仓库提供低分辨率 RGB、毫米深度 PNG、每帧相机内参和带时间戳的 `.traj`（轴角+平移）；数据按 Training/Validation 及 video_id CSV 管理，可按 video_id 只下载指定样本。官方 3DOD 低分辨率子集总量约 623.4 GB，但下载脚本允许只选具体 video_id 和资产类型。[官方 DATA.md](https://github.com/apple/ARKitScenes/blob/main/DATA.md)

**审查判断**：它比 ScanNet++ 更容易做“只取少量 video_id”的本机资格试验，且是真实移动 RGB-D 序列，适合验证长序列内未来深度误差。不过公开 CSV 主要是 train/val；如果使用 validation 作为最终测试，需要预先冻结 video_id、不能看未来答案调参，并将结论限定为 holdout video，不轻易称官方 test 泛化。数据有 timestamp 对齐、confidence 和移动设备 ARKit 位姿误差，需在 Gate0 单独测对齐/漂移。

**建议候选名称**：`ALT-ARKIT-01（移动RGB-D长序列未来误差试验）`。只有在少量 video_id 下载后确认每个视频有 ≥6 历史、≥3 未来帧且深度有效率达阈值，才进入正式实验；否则降级为字段解析测试。

### 补充排序修正

按“长期几何问题相关性”而非“立刻可下载”排序：**3RScan > Bonn Dynamic ≈ TUM > ARKitScenes > Dynamic Replica > PointOdyssey > ScanNet > Replica oracle > ScanNet++**。按“本机低成本启动”排序：**TUM > Bonn 单序列 > ARKitScenes 单 video_id（若可访问） > PointOdyssey 小分片 > Replica > 3RScan/ScanNet/Dynamic Replica 全量 > ScanNet++**。这两个排序不可混成一个总分。

3RScan 和 ARKitScenes 的加入只是检索后的候选扩展；本轮仍没有下载、许可接受或科学实验，不改变 `S91 BLOCKED_ON_GATE0`。

### Matterport3D（静态 RGB-D 视角补充）

官方仓库说明包含 90 个 building-scale properties、颜色/深度图、相机姿态和 textured meshes；下载必须用 institutional email 签 Terms of Use 后等待官方提供权限。[官方仓库](https://github.com/niessner/Matterport) 数据组织页还明确每个颜色/深度图和 camera-to-world 矩阵的关系。[数据组织](https://github.com/matterport/3d-dataset-tools/blob/master/data_organization.md)

它适合做静态 wide-baseline/view-coverage 对照，但没有自然时间轴或动态重扫；因此最多作为“未来查询=新视角”的静态基线，不应替代 TUM/Bonn/3RScan 的时间未来合同。由于访问审批和许可受限，本轮不列入本机首选。
