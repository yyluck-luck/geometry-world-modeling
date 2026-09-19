# 可合法候选 held-out 数据方案复核（2026-09-15）

## 任务与证据边界

本轮针对“在不读取/下载未核许可的大包前，找一个与 proposal 匹配的 RGB-D + 相机 pose + 时间索引数据源”检索官方一手页面。检索时间锚点为 **2026-09-15 02:26:13 +08:00**。没有下载任何数据包、没有读取图像/深度数组、没有运行模型，也没有把候选数据送入 GRC。

本报告优先选择许可清楚且可以按单场景下载的来源，同时把“公开链接”“允许学术使用”“含 pose”“含真实时间戳”“在本项目中未见”分开记录。当前项目历史检索中，`rg -i "scenenn|scenenet" docs work RESEARCH_MEMORY.md RESEARCH_LOG.md` 只发现论文/背景文字，没有发现 SceneNN 数据文件、场景 ID、Google Drive 数据下载记录或模型输出；这不是完整的访问证明，仍需在 Gate0 由独立审计复核浏览器/下载历史。

## 候选 A：SceneNN（最接近“清楚许可 + 单场景下载”）

官方作者仓库：<https://github.com/hkust-vgd/scenenn>

官方仓库的关键原文事实：

* 数据集是 100+ 个室内 RGB-D 场景；仓库通过 Google Drive 提供数据，并说明可用脚本下载“几个指定场景”而不是只能下载全集。
* 每个场景目录包含 `trajectory.log`（camera pose, local-to-world）、`oni/<scene>.oni` 原始 RGB-D 视频和 `intrinsic/asus.ini` 或 `kinect2.ini` 内参；单场景包含 raw RGB-D 时约 1 GB，只有 mesh/annotation 约 100–200 MB。
* 官方说明 ONI 播放工具可把 raw RGB-D 提取为 16-bit depth，深度单位为 millimeter；`trajectory.log` 每个块由帧索引加 4×4 camera-to-world 矩阵组成；内参格式是针孔矩阵 `[fx,0,cx;0,fy,cy;0,0,1]`。
* 官方仓库许可原文为：数据集可免费用于 educational and research use；如作商业用途需事先联系作者。需保留 SceneNN 3DV 2016 引用。

**为什么匹配 proposal：** SceneNN 的场景序列、逐帧 RGB-D、相机到世界位姿、内参和遮挡/室内布局，可用于长时程重访、遮挡恢复及未来几何误差评价。它还来自 HKUST Vision & Graphics Group 的官方作者仓库，获取路径比二手镜像更可追溯。

**关键阻断：时间戳尚未被官方 README 证明。** 官方仓库明确写的是 `trajectory.log` 的 frame index，而不是 Unix/秒级时间戳；ONI 文件通常包含视频帧时间元数据，但这一点不能凭 OpenNI 常识替代原始数据核验。若本项目必须报告 RGB-depth-pose 的真实时间配对，必须在下载单个场景后先检查 ONI 解码器是否能导出原始帧 timestamp，或找到数据发布者对帧率/同步规则的明确说明。若只能得到帧索引，Gate0 应标记 `timestamp_status=UNVERIFIED`，暂不能作为正式 held-out。

**许可判断：** `EDUCATIONAL_RESEARCH_ALLOWED_BY_OFFICIAL_REPO`，但这不是 CC BY，也没有在当前页面承诺任意公开再分发。论文中可报告派生指标和图表时，要保留原始引用并遵循页面条件；不要把数据包复制到公开仓库。

**held-out 判断：** `PENDING_INTERNAL_EXPOSURE_AUDIT`。本地搜索没有数据文件或下载记录，但历史元数据/论文暴露与方法选择影响仍需独立审计；不能因为仓库是 HKUST 作者仓库就宣称未见。

## 候选 B：SceneNet RGB-D（许可明确，但属于 synthetic，资产链较复杂）

官方代码仓库：<https://github.com/dyson-robotics-lab/SceneNetRGB-D>

官方研究组页面：<https://www.imperial.ac.uk/dyson-robotics-lab/downloads/scenenet-rgb-d-software/>

官方仓库说明 pipeline 会随机生成场景、生成 camera trajectory，再渲染 RGB、depth 和 instance mask；官方页面称可产生 perfect camera poses and depth，用于光流、相机位姿和几何视觉实验。README 明确写明 SceneNet RGB-D 仅限 non-commercial use，并要求遵守仓库 `LICENSE.txt` 和官方 terms。仓库运行还需要 ShapeNet Core（注册）和 SceneNet layouts/textures；因此第三方资产许可必须一起核对。

它适合作为**冻结后生成的 synthetic held-out 压力测试**：在方法与阈值冻结后，由固定随机种子产生未见场景/轨迹，时间可由生成器的帧率协议显式定义，pose、depth 和相机内参由渲染器输出。它不能单独证明真实 Kinect 世界的泛化，也不能与 TUM/SceneNN 实测 RGB-D 结果混合汇报。官方许可虽然清楚到“非商业”，但资产注册和条款链使它不如 SceneNN 适合作为近期第一选择。

## 候选 C：7-Scenes 与 TUM 的排除/降级结论

7-Scenes 官方页面：<https://www.microsoft.com/en-us/research/project/rgb-d-dataset-7-scenes/>

7-Scenes 的官方页面确认每帧有 RGB、depth 和 camera-to-world pose，且每个序列约 500–1000 帧；但同一页面明确 RGB 与 depth camera **未标定**，只能给 depth camera 的默认内参。因此它不能直接满足本项目要求的 RGB-depth 像素几何评价，除非另立标定适配合同。已有 S14 审计也已排除它的当前像素支持评分，故不再重复下载。

TUM RGB-D 官方许可虽然最清楚（CC BY 4.0），但本项目 S8/S14 已保存下载页 HTML 并将部分 fr3 序列纳入候选/场景计划；相关条目至少属于 `metadata_seen`。在历史审计完成前，不能把它们当作全新 held-out。官方 `*_validation` 条目还没有 ground-truth 下载，不可误作 pose-GT 测试集。

## 建议的可执行方案

**首选：SceneNN 单场景，先做资格检查，再决定是否下载约 1 GB raw ONI。** 该方案满足教育/研究许可和单场景小规模获取，但必须先解决 ONI timestamp 字段。若 ONI 只能提供连续帧索引而没有可验证时间信息，则将 SceneNN 降级为“几何/位姿机制诊断”，不进入正式的 proposal 时间配对评价。

**备选：SceneNet RGB-D 在冻结后生成一个 synthetic held-out。** 需在 `method_freeze_sha` 之后固定随机种子、布局 split、ShapeNet/SceneNet 资产版本和帧率，把输出标为 synthetic；这是可执行的几何因果单元测试，不替代真实世界证据。

## Gate0 manifest 模板（只可在数据获得后填写）

```json
{
  "manifest_version": "S102-GATE0-20260915",
  "dataset_id": "scenenn",
  "official_source_url": "https://github.com/hkust-vgd/scenenn",
  "scene_id": "<single_scene_id>",
  "license_status": "EDUCATIONAL_RESEARCH_ALLOWED_BY_OFFICIAL_REPO",
  "license_text_sha256": "<sha256-of-saved-license-or-README>",
  "access_status": "NOT_ACQUIRED",
  "heldout_status": "PENDING_INTERNAL_EXPOSURE_AUDIT",
  "method_freeze_sha256": "<GRC-freeze-hash-or-NONE>",
  "rgb_artifact_sha256": "<sha256>",
  "depth_artifact_sha256": "<sha256>",
  "pose_artifact_sha256": "<sha256>",
  "intrinsics_artifact_sha256": "<sha256>",
  "rgb_depth_pairing": "<verified-after-acquisition>",
  "pose_frame_convention": "camera_to_world",
  "timestamp_source": "ONI_metadata_or_frame_index",
  "timestamp_status": "UNVERIFIED",
  "depth_unit": "millimeter",
  "invalid_depth_rule": "<verified-from-decoder>",
  "frame_count": null,
  "split_role": "HELD_OUT_TEST_PENDING",
  "historical_exposure_audit": "REQUIRED",
  "prediction_sealed_before_gt": false,
  "independent_reviewer": "<agent-or-person>",
  "gate0_decision": "BLOCKED_UNTIL_TIMESTAMP_AND_EXPOSURE_AUDIT"
}
```

## 明确停止条件

在以下任一条件出现时，不把 SceneNN 或其它候选送入正式 GRC：

1. 许可文本无法保存或与数据包条件冲突；
2. RGB、depth 与 pose 的帧索引无法一一对应；
3. ONI/元数据没有可复核 timestamp，而协议又要求真实时间配对；
4. `trajectory.log` 的坐标方向、单位或参考帧无法用官方说明和小样本检查确认；
5. 历史记录显示场景已参与方法选择、阈值选择或协议调整；
6. 预测未封存就读取未来 depth/pose GT；
7. 独立复核无法从原始文件和 SHA 重算 manifest。

## 本轮结论

SceneNN 是目前检索到的“官方仓库许可清楚、可按场景获取、RGB-D + 相机位姿字段明确、与 proposal 遮挡/重访问题相符”的最现实候选；但它的官方文档只保证 `trajectory.log` 的 frame index，没有充分证明真实时间戳。因此现在的科学结论是 **`PROMISING_BUT_BLOCKED`**，不是已获得 held-out，也不是已通过 GRC Gate0。SceneNet 可作为冻结后 synthetic 备选；TUM/7-Scenes 的 metadata_seen/标定边界必须保留。

本轮网络检索中读取了 SceneNN、SceneNet RGB-D、7-Scenes 官方页面；未下载大包、未读取图像/深度、未产生模型或方法结果。

