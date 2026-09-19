# S20：原视频保存函数的人工编解码测试

**本机已经真实写出并读回一个 4 帧、32×32 的 H.264 视频。这里只验证视频保存软件是否能工作：输入是程序创建的红、绿、蓝、黄四张色块，没有使用模型、实拍照片或 GT。不是 VMem 模型视频生成结果。**

视频：[SYNTHETIC_four_colors.mp4](../work/S20_codec_smoke/attempt1/SYNTHETIC_four_colors.mp4)。文件大小 1,685 B，SHA-256 `6428b46605271a9df3f651204bee6d861cc6446d385b53fe89519b2dcd1c125c`。没有挑选帧，四帧全部写入、全部读回。

2026-09-06 UTC 12:48:26.335278–12:48:28.862674（北京时间 20:48:26–20:48:28）实际运行。worker 总时长 **2.527408 秒**，其中保存调用耗时 **0.002563 秒**；这些是极小人工输入的时间，不可外推长视频或模型成本。macOS worker 自报峰值 RSS **366,952,448 B**；外部监控含启动/退出共 **2.824766 秒**，采样进程树峰值 **366,985,216 B**，42 次采样。自报峰值与外部采样的测量口径不同。预定 60 秒、1 GiB 限制通过。

测试使用固定 VMem 提交 `39291e4f272f6b4f270691d930926ab5930f942e` 中 `utils/util.py` 第 863–870 行的原 `save_video`，通过 AST 抽出完整单函数，未重导入整个 pipeline。原文件 SHA-256 `0b71dcf6d4a43109d785f49d9c6def37b1256c4d189ab9438bfb185f3099f013` 与 S18 已固定身份相同；抽出原文 SHA `b4e7536ba0f7866436038734b2e1cd7b7d8232b53c01f51133ba385107ec5bae`。另确认 S20 隔离副本该函数的 AST 全等。原文保存在 [original_save_video.py](../work/S20_codec_smoke/attempt1/original_save_video.py)，没有重新实现或修改编码参数。

实际调用链为：人工 `uint8 [4,3,32,32]` tensor → 原 `save_video` 的轴变换 → `torchvision.io.write_video` → PyAV/FFmpeg 的 `libx264` 编码。保持原参数 `crf=23, preset=slow`，使用原默认 `fps=10`。之后用 PyAV 重新打开 MP4，解码成 RGB24 验证。写入与读取均使用 PyAV，因此这里不声称是不同编解码实现的独立复现。

| 预先固定的检查 | 实际结果 |
|---|---|
| 4 帧、每帧 32×32×3 | 全部一致 |
| H.264，10 fps | 一致 |
| 时间戳依次为 0、0.1、0.2、0.3 秒，容差 10⁻⁶ 秒 | 一致；PTS 为 0、1024、2048、3072，time base 为 1/10240 |
| 解码颜色分别最接近固定的红、绿、蓝、黄色 | 顺序 0、1、2、3，全部正确 |
| 每帧均值 RGB 的单通道误差 ≤15 | 最大误差 3 |
| 四帧不能全部重复，进一步要求四帧 SHA 各异 | 四帧各异 |

输入 RGB 分别为 `[220,30,30]`、`[30,220,30]`、`[30,30,220]`、`[220,220,30]`；解码均值分别为 `[218,30,30]`、`[28,219,30]`、`[27,30,217]`、`[218,217,28]`。像素不是逐位相同，这与有损 H.264 压缩相符，预定协议也没有要求逐位相同。输入和完整解码帧分别保存为人工 NPZ，不能将这些数组混入真实数据集。

实际环境是 `.venv-cut3r` 的 Torch 2.7.0、torchvision 0.22.0、NumPy 1.26.4，加 S20 overlay 的 PyAV 14.2.0、imageio-ffmpeg 0.6.0，并按要求加入已有 S17C overlay；已检查包版本和来源路径。CPU 使用 8 个 Torch 线程，seed 0。原 writer 使用 PyAV 链接的 FFmpeg 库，实际 `libavcodec=61.19.100`、`libavformat=61.7.100`。另对 imageio-ffmpeg 0.6.0 自带的 `ffmpeg-macos-aarch64-v7.1 -version` 做了真实可执行性探针，返回 0、版本 7.1；它不是原 writer 调用的编码后端，不能混为同一条链路。

实际共 36 项软件与来源检查通过，不是 36 次模型实验或质量指标。没有修改旧环境、旧源码、results 目录或封存结果；模型权重读取、模型构造、推理、原照片解码、GT 读取均为 0。没有发生网络或受保护数据访问尝试。

此次 codec 尝试没有运行失败。stderr 保留 torchvision 0.22 给出的视频 API 弃用警告，当前实际调用仍成功；本轮为保持原作者调用，没有迁移到其他库。准备时还读取到另一个任务的 `S20_environment/import_smoke_v2.json` 为失败，原因是完整 pipeline 导入时 sklearn/joblib 的 subprocess 被其审计规则拦截。该历史状态被本轮合同绑定并保留，但 codec 只导入所需编解码模块，不能用本次成功覆盖或宣称该完整导入检查已经成功；是否后续解决由主任务另记。

证据入口：[预定合同](../work/S20_codec_smoke/contract.json)、[实际运行回执](../work/S20_codec_smoke/attempt1/run_metadata.json)、[外部资源监控](../work/S20_codec_smoke/caller_receipt.json)、[原始 stderr](../work/S20_codec_smoke/worker.stderr.txt)、[汇总文件身份](../work/S20_codec_smoke/receipt.json)。本轮继续应用本地 Claude scientific-critical-thinking 的范围是分清软件可用性、人工输入和模型效果，没有调用 Claude 模型。下一完整视频实验仍需要合法可用的原主模型、原 VAE 和其他已核依赖；本次只关闭小型视频保存与读回这个软件缺项。
