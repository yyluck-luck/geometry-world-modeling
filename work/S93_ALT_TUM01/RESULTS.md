# ALT-TUM-01 结果：TUM `freiburg1_xyz`

## 做了什么

我只使用 TUM Computer Vision Group 的官方下载页和格式页，选择 `freiburg1_xyz` 做最小资格检查。没有下载 448 MB 的 TGZ，也没有下载完整 RGB/Depth 电影。

实际保存了：

- 官方下载页和格式页的可达性回执；
- 完整 `rgbd_dataset_freiburg1_xyz-groundtruth.txt`，201,100 bytes，3000 条位姿；
- RGB AVI 的 0–65,535 字节前缀；
- Depth AVI 的 0–65,535 字节前缀；
- TGZ 的 0–65,535 字节前缀。

## 真实核验结果

GT 文件可读，第一条和最后一条记录均为八列 `timestamp tx ty tz qx qy qz qw`，时间范围约 30.0896 s。官方格式页明确说明 RGB/Depth PNG 是 640×480、RGB 为 8-bit、Depth 为 16-bit，并且已预配准；depth 缩放因子为 5000，0 表示缺失。官方也给出相机轨迹的时间戳、平移和四元数格式。

RGB 与 Depth AVI 的 64 KiB 前缀能确认服务器返回了 MPEG-4 AVI 容器头（640×480），但它们不是完整电影，也没有从这两个前缀中提取出带原始时间戳的 RGB/Depth PNG 帧。因此不能声称已经取得真实的同步 RGB-D 帧对。

## Gate0 结论

**GATE0_NOT_PASSED**。TUM 是一个有希望的候选数据源，但本轮只证明了官方入口和 GT 文本可达，未证明当前本地已有可用于模型评分的 RGB-D 帧对、相机内参绑定和冻结场景划分。按照停止规则，不启动 S91，不把这个候选写成实验数据已就绪。

许可方面，抓取的官方下载页和格式页没有发现明确的 license 条款；因此只能记录官方来源，不能替用户作许可承诺。正式论文使用前需核对 TUM 当前使用条件或向导师确认。

## 来源

- 官方下载页：<https://cvg.cit.tum.de/data/datasets/rgbd-dataset/download>
- 官方文件格式页：<https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats>

## 下一步

如果继续，只允许做一次小规模、可审计的帧级取样：保留原始时间戳，分别解码至少一对 RGB PNG 和 Depth PNG，并把对应 GT pose、内参、单位和 SHA 写入新的 receipt。完成前不进入未来几何误差实验。
