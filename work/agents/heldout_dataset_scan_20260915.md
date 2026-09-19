# Held-out RGB-D + pose 数据入口初筛（2026-09-15）

**任务边界。** 本文件只做公开官方页面和许可/字段的初筛，不下载大包、不把任何候选数据送入 GRC，也不把“可下载”当成“已获得合法 held-out 测试集”。正式使用前仍需完成项目内部的 Gate0：核对本机历史访问记录、方法选择记录、文件 SHA、序列级划分、时间戳配对、相机参数、深度单位、许可文本和独立审计。

## 1. 最优近期入口：TUM RGB-D（不同于已经使用的 fr1/fr2 development 序列）

官方主页：<https://cvg.cit.tum.de/data/datasets/rgbd-dataset>

官方下载页：<https://cvg.cit.tum.de/data/datasets/rgbd-dataset/download>

官方格式/标定页：<https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats>

官方主页明确提供 Kinect 彩色图、深度图和高精度 motion-capture ground-truth trajectory；数据为 30 Hz、640×480，轨迹由 100 Hz 动捕系统获得。官方许可说明：除另有说明外，TUM RGB-D 数据采用 CC BY 4.0，附带源代码采用 BSD-2-Clause。使用时仍需保留原作者引用和 CC BY 归属信息。

官方格式页给出可直接用于本项目 Gate0 的字段：带时间戳 RGB PNG（640×480、8-bit）、深度 PNG（640×480、16-bit）；RGB 与 depth 已由 OpenNI 预配准；深度值比例为 5000（5000 表示 1 m，0 表示缺失）。Ground-truth 每行是 `timestamp tx ty tz qx qy qz qw`，包含相机在固定世界坐标中的位置和单位四元数。官方还说明 ROS bag 可同时包含 RGB、depth、camera info、point clouds 和 world-to-Kinect ground truth transform。Freiburg 3 的官方 RGB 内参为 `fx=535.4, fy=539.2, cx=320.1, cy=247.6`，并说明 Freiburg 3 图像已去畸变；深度比例校正为 1.000。

**适合作为候选 held-out 序列（尚未证明未见）：**

* `freiburg3_long_office_household`：官方描述为带纹理和结构的 household/office 大环路，起终点重叠，87.09 s，轨迹长 21.455 m；下载项同时列出 TGZ、ground-truth、RGB 和 depth。
* `freiburg3_structure_texture_far`：彩色塑料结构和带海报的强纹理，31.55 s，轨迹长 5.884 m；官方同时列出 ground-truth、RGB、depth。
* `freiburg3_structure_texture_near`：近距离同类结构，36.91 s，轨迹长 5.050 m；官方同时列出 ground-truth、RGB、depth。
* `freiburg3_cabinet`：低纹理/低结构的办公台座环绕，38.58 s，轨迹长 8.111 m；官方同时列出 ground-truth、RGB、depth。
* `freiburg3_large_cabinet`：大柜体环绕，33.98 s，轨迹长 11.954 m；官方同时列出 ground-truth、RGB、depth。
* `freiburg3_teddy`：不同高度两圈环绕，80.79 s，轨迹长 19.807 m；官方同时列出 ground-truth、RGB、depth。
* `freiburg2_pioneer_slam`：机器人通过桌子/容器/墙组成的迷宫并闭合多个环，155.72 s，轨迹长 40.380 m；官方列出 ground-truth、RGB、depth，并另有激光/里程计信息。

这些序列比官方标为 `*_validation` 的条目更适合当前任务，因为下载页写明 validation 序列没有 ground truth，只能用在线工具评测；因此不要把 validation 名称误读为可用的 pose-GT 测试集。以上候选仍需内部审计：若过去已被 S86–S102 读取、用于调参或被模型选择，必须降级为 development/seen。

**本项目历史曝光的即时修正。** 现有 `docs/S8_DATA_SOURCE_REVIEW.md`、`docs/S14_NEW_SCENE_IDENTITY_AUDIT.md` 和对应 receipt 已经保存过 TUM 下载页 HTML/候选元数据，并把 `freiburg3_long_office_household`、`freiburg3_structure_texture_far` 写入过场景计划。因而这两个序列至少属于 `metadata_seen`，不能在没有更细历史审计的情况下被宣称为“完全未见 held-out”。当前记录显示没有请求压缩包或读取其图像数组，但“是否用元数据影响了场景/协议选择”仍需按日志逐项判断；若有影响，必须降为 development。下载页本身也包含其它 fr3 条目的元数据，因此 `cabinet`、`large_cabinet`、`teddy` 等候选同样不能仅凭尚未下载就通过 held-out 门。最保守做法是：把已有 TUM 页面元数据全部登记为 `metadata_seen`，只在新数据源或经独立审计证明未参与选择的序列上申请 Gate0。

## 2. ScanNet：字段完整，但许可和取得流程需要机构确认

官方页面：<https://www.scan-net.org/ScanNet/>

官方 Sens 格式：<https://www.scan-net.org/ScanNet/SensReader/>

官方说明 ScanNet 是 RGB-D 视频数据集，包含 2.5 million views、1500+ scans，并带 3D camera poses、表面重建和语义标注。下载需要填写 ScanNet Terms of Use，并用机构邮箱发给官方组邮箱；因此它不是当前可以直接假定“已合法取得”的数据。官方 SensReader 说明 `.sens` 每帧含时间戳、color、depth 和 camera-to-world pose；同时有 color/depth intrinsic calibration、分辨率和 depth shift（通常 1000，将米转换为 ushort）。

**建议状态：** `LICENSE_REVIEW_REQUIRED / NO_DOWNLOAD_YET`。只有收到并保存官方许可文本、完成机构用途核对，且确认场景未参与方法选择后，才可进入 Gate0。ScanNet 可作为跨数据集确认，但不应在许可未核对时用于正式实验。

## 3. ICL-NUIM：字段、GT 与公开许可已由官方页面核实

官方页面：<https://www.doc.ic.ac.uk/~ahanda/VaFRIC/iclnuim.html>

官方说明 living-room 场景提供 depth maps、camera poses 和 3D surface ground truth；office 场景提供 trajectory data 但没有显式 3D model。页面给出 4 条 living-room handheld trajectories（`lr kt0`–`lr kt3`），每条有 RGB-D 图像、TUM-compatible PNG、TUM pose 格式和全局位姿文件，帧率 30 Hz；同时提供带合成传感器噪声版本。它很适合在不依赖神经模型的情况下验证“几何风险→未来深度/位姿”的可证伪机制，并可作为真实 TUM 之外的跨场景/跨域对照。

官方页面 License 段明确写明数据以 Creative Commons 3.0（CC BY 3.0）发布，并链接到 Creative Commons 条款；这足以记录为公开研究使用许可证据，但仍需保存页面快照、数据包内 README/许可文件（若有）和下载包 SHA。由于项目已经读过该官方页面元数据，ICL 只能作为 `data_access_heldout_pending` 候选，不能宣称 zero-metadata-exposure；正式使用前仍需独立审计研究用途、署名和派生结果分发边界。

## 4. Bonn RGB-D Dynamic Dataset：真实动态遮挡强，但许可与坐标适配仍未过门

官方页面：<https://www.ipb.uni-bonn.de/data/rgbd-dynamic-dataset/>

官方页面说明该数据集含 24 条动态序列和 2 条静态序列；每个场景提供 OptiTrack Prime 13 记录的传感器 ground-truth pose，并提供静态环境的 Leica BLK360 激光点云。RGB-D 序列采用 TUM RGB-D 格式，深度已注册到 RGB；官方页面给出 RGB 内参 `fx=542.822841, fy=542.576870, cx=315.593520, cy=237.756098` 及畸变参数，并给出从传感器坐标到激光 GT 坐标的变换说明。页面列出 `rgbd_bonn_static_close_far`（1.0 GB）和多个动态序列的直接下载入口。

**科学价值：** 动态人物/盒子遮挡、物体移动和静态对照，正好可用于 proposal 的遮挡重访和长时程几何一致性压力测试；但它不能自动成为“不同物理房间”的证明。当前项目的 S14 审计已将 Bonn 标为来源候选、保守合组，且记录了页面元数据和许可缺口；因此只能登记为 `metadata_seen / LICENSE_UNRESOLVED / HELDOUT_PENDING`。页面邀请科研使用并要求引用 ReFusion 论文，但当前可见页面未给出独立数据许可全文，代码许可证不能替代数据许可证。正式使用前必须保存包内 README/许可、下载包 SHA、历史访问审计和配对/GT 适配回执。不要把 OptiTrack pose 与激光点云坐标变换混作“RGB-D 光学 c2w”而跳过坐标验证。

本次通过官方页面尝试访问 `rgbd_bonn_static_close_far.zip` 时，网页检索器返回 `Unsupported content-type: application/zip`；未保存、解压或读取该压缩包。这只说明当前检索接口不承载 ZIP，不等于官方链接失效或数据不可取得。

## 5. Replica：可渲染和可复现实验有价值，但需要逐项读取仓库 LICENSE

官方仓库：<https://github.com/facebookresearch/Replica-Dataset>

官方 README 说明 Replica 提供 AI Habitat 导出，可用于机器学习任务；ReplicaRenderer 可根据程序化轨迹无 UI 渲染，也可在服务器 headless 运行。README 提供 `download.sh` 下载方式并指向仓库 LICENSE，但当前初筛没有把该 LICENSE 的具体限制复制进本报告，因此不能在 Gate0 之前宣称许可已确认。另一个科学边界是：Replica 常用于程序化渲染/仿真，必须明确这是 synthetic/rendered RGB-D+pose，不得与真实 Kinect 观测混写；若用它做 held-out，场景和轨迹必须在方法冻结之后才生成/选择。

**建议状态：** `LICENSE_TEXT_AND_RENDER_PROTOCOL_REQUIRED`。可作为合成机制压力测试或复现性测试，不应单独支撑“真实世界”结论。

## 6. 建议的取得顺序与 Gate0 规则

1. **先审 TUM 非 validation 的候选序列**：因为官方 CC BY 4.0、RGB/depth/pose/内参/格式最完整，且可以按序列划分。优先 `freiburg3_long_office_household`（长环路）+ `freiburg3_structure_texture_far`（强纹理）+ `freiburg3_cabinet`（低纹理）形成有机制差异的最小集合。是否 held-out 只由项目历史审计决定，不能由序列名称决定。
2. **若需要跨域证据，再审 ICL-NUIM**：先拿到官方许可文本/README，再固定合成噪声版本、场景和轨迹划分；把它标为 synthetic。
3. **若需要更大规模真实场景，再申请 ScanNet**：先完成 Terms of Use 和机构邮箱流程，保存审批证据；未获批前不下载、不运行。
4. **Replica 只作补充**：将场景、轨迹和渲染器版本写入冻结协议，把 synthetic 结果与实测 RGB-D 分开汇报。

### Gate0 必须记录的字段

`dataset_id, source_url, license_text_url_or_file, permission_status, scene_or_sequence_id, historical_access_audit, RGB_SHA256, depth_SHA256, pose_SHA256, timestamp_alignment_rule, intrinsics_source, extrinsics_source, depth_unit, invalid_depth_rule, frame_count, train_dev_test_role, method_selection_exposure, heldout_decision, independent_reviewer, decision_time`。

任何一个身份、许可、时间戳、RGB-depth-pose 配对或历史暴露字段缺失，都只可进入资格审计，不得进入正式 GRC 方法实验。此文件没有下载数据，也没有产生任何实验结果。
