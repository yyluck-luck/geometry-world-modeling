# S93-FrameProbe 结果：Gate0 仍未通过

## 实际取得

- RGB AVI：8,059,298 bytes，完整文件（由于一次错误的负 range 语法意外下载；已保留原始回执并不把它包装成随机访问成功）。SHA256 `1820b52939af2a2e7afdf78f6398cfbc7816399c8809b3836a9ba8da9bef8022`。
- Depth AVI：1,048,576 bytes，HTTP 206 前缀。SHA256 `784e8bd7fc1b59e4ae2c76f347058aac1ab63cc59524c7d753eaa32ec8df8173`。
- 总媒体字节：9,107,874，低于 10,000,000 byte 上限。
- GT：官方文本 201,100 bytes，3000 条 pose；首个绝对时间戳 `1305031098.6659`，末个 `1305031128.7555`。

## 真实解码检查

- RGB AVI 可被 ffprobe 识别为 640×480 MPEG-4/FMP4、`time_base=1/30`；第一帧可解码为 640×480 PNG。
- Depth 前缀可被 ffprobe 识别为 640×480 MPEG-4/FMP4、`time_base=1/30`；第一帧可解码，但输出是 `RGB`、8-bit PNG（不是 16-bit depth PNG）。
- 两个 AVI 的帧时间只有从 0 开始的相对 PTS（第一帧 `pts_time=0.000000`），未发现与 TUM GT 绝对 Unix 时间戳对应的元数据。用“第 0 帧 + 30 fps”去对齐 GT 会是假设，协议禁止把它称为原始时间映射。

## 判定

**GATE0_NOT_PASSED / STOP_FRAME_PROBE**。

本次证明了媒体容器可解码，但没有得到合格的原始 RGB-D 帧对：depth 是有损 MPEG-4 8-bit 视频，不保留官方 16-bit depth PNG 数值；同时缺少 RGB/depth 原始时间戳到 GT pose 的绑定。因此不启动 S91，也不把这次结果当作几何实验或方法负结果。

## 最小缺口

必须从官方 TGZ/BAG 或其他合规镜像取得至少一对原始 RGB PNG + 16-bit depth PNG，并保留文件时间戳/association 映射；同时绑定 Freiburg 相机内参、depth scale=5000 和对应 GT pose。若不能获得这些字段，应转向另一个明确提供同步 RGB-D PNG 与 pose 的数据源（例如通过正式许可获取的 3RScan 子集）。

## 预算与错误说明

原计划是做帧级小样本，而不是下载完整媒体。RGB 文件虽然使本次两媒体合计 9,107,874 bytes 小于 10,000,000 bytes，但它本身是完整 8,059,298-byte AVI，超出了“只取少量帧/不下载完整电影”的意图。原因是首次尝试使用了 `curl --range -65536:`；curl 将其视为无效范围并在 `-L` 下下载了完整响应。该错误已停止，不再补发网络请求；完整文件仅作为失败审计证据，不能当作合规的随机帧取得。
