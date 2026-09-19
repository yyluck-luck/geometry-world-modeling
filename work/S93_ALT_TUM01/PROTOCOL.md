# ALT-TUM-01：TUM RGB-D 单序列最小资格协议

**状态：PARTIAL_ACCESS_ONLY / GATE0_NOT_PASSED**  
**记录时间：2026-09-12（Asia/Shanghai）；网络请求时间以 receipts/probe_manifest.json 为准**

## 目的

为几何风险—未来状态实验寻找合规、可审计的 RGB-D 与相机真值来源。只检查官方 TUM RGB-D 入口的 `freiburg1_xyz` 单序列；不下载整套数据，不把电影容器头部当作图像帧，不启动 S91。

## 固定资格条件

1. **RGB**：必须能取得带时间戳的 640×480 8-bit RGB PNG 帧。
2. **Depth**：必须能取得与 RGB 配对的 640×480 16-bit depth PNG 帧；官方格式说明 depth 值按 5000 缩放，5000 表示 1 m，0 表示缺失。
3. **时间戳配对**：RGB 与 depth 的时间戳须能与同一时刻匹配，并保留原始文件名/时间戳。
4. **相机真值**：须有与帧时间对应的 ground-truth pose，格式为 `timestamp tx ty tz qx qy qz qw`；单位为秒和米，位姿来自固定世界坐标系的相机光学中心。
5. **相机模型**：须明确使用的内参/畸变与 Freiburg 版本；不能用默认参数代替已知标定而不记录。
6. **场景划分**：开发、校准、测试序列必须在实验前冻结；同一序列的历史与未来不能被误称为跨场景。
7. **许可**：官方页面必须给出可用于本研究的许可/使用条件，或由导师确认；当前页面未在抓取内容中发现明确 license 条款，因此仅记录来源，不宣称许可已确认。
8. **完整性**：正式 Gate0 还需要至少一组可解码 RGB 帧、一组可解码 depth 帧、同帧时间戳、GT pose 和可复核 SHA；本次 64 KiB 电影片段只作传输/容器可达性探针。

## 最小预算

- 官方页面与格式页：完整 HTML，记录 SHA。
- ground-truth 文本：允许完整下载（约 201 KiB）。
- archive/RGB movie/depth movie：每个最多请求字节 `0–65535`（64 KiB），不请求整文件。
- 单次请求 `curl --max-time 20`；不重复盲试。
- 完整 archive 约 448,204,271 B，RGB movie 约 8,059,298 B，depth movie 约 8,022,164 B；这些总大小来自 HTTP `Content-Range`，不是本地已下载量。

## 停止规则

若官方入口重定向、TLS、Range、正文解析或许可出现问题，保留回执并停止；若只有媒体容器头而无可解码、带时间戳的 RGB/depth 帧，也停止 Gate0，不进行未来几何评分。

## 预期输出

- `receipts/probe_manifest.json`：URL、时间、状态码、Content-Range、下载字节、SHA256。
- `downloads/freiburg1_xyz-groundtruth.txt`：真实 GT 文本及 SHA。
- `GATE0_RESULT.json`：逐项 PASS/FAIL/UNKNOWN。
- `RESULTS.md`：面向初学者的结论和边界。
