# S93-FrameProbe（TUM `freiburg1_xyz` 帧级最小取样）

时间：2026-09-12 Asia/Shanghai。目的：在不下载整套 448 MB TGZ、且总媒体下载不超过 10 MB 的情况下，验证是否能得到至少一对**可解码、16-bit depth、保留原始时间戳并能绑定 GT pose** 的 RGB-D 帧。

## 冻结边界

- 只使用官方 TUM RGB-D 电影入口和已有官方 ground-truth 文本。
- 允许媒体总下载预算为 10,000,000 bytes；本次实际媒体字节为 RGB 8,059,298 + depth 1,048,576 = 9,107,874 bytes。
- 不把 AVI 的固定 30 fps 计数器当作原始 TUM 时间戳。
- 不把 MPEG-4 解码出的灰度/彩色图当作原始 16-bit depth PNG。
- 只有同时满足 RGB PNG、16-bit depth PNG、原始时间戳配对、GT pose、内参/单位绑定，才允许 Gate0 通过。

## 取样动作

1. 已有 RGB AVI 64 KiB 探针不足以解码；因一次 `curl --range -65536:` 参数格式不符合 curl 语法，产生了一个完整 RGB AVI（8,059,298 bytes）。该文件保留并明确标注为 `unintended`，不作为“有界随机访问”成功证据。
2. 在剩余预算内请求 depth AVI 的前 1,048,576 bytes（HTTP 206）。
3. 使用 ffprobe/ffmpeg 仅检查容器、第一帧和像素格式；不运行模型，不计算几何误差。
