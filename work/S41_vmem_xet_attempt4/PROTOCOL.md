# VMem 官方 Xet attempt4 草案

目的：在 attempt3 因 1800 秒外部时限终止、手工 HTTP Range 又在 CDN 连接层收到 0 字节后，使用一个新的官方 Xet 传输完成原 VMem 权重。

固定条件：

- 官方 `huggingface_hub` CLI 1.30.0 与严格固定的 `hf_xet` 1.6.0；
- 固定官方端点 `HF_ENDPOINT=https://huggingface.co`，并显式关闭 offline/debug 模式；
- 仓库 `liguang0115/vmem`；固定 revision `ac5921080a57f5a634f4b9acbbc8f3db67c9d113`；
- 文件 `vmem_weights.pth`；期望 5,056,346,672 bytes；
- 完整 SHA-256 `675dc486a02ea06ecf8b6ab0cf4ef88c92298751b2daacf9f65c59871fcb7fe4`；
- 新目录 `data/vmem_recovery/xet_attempt4_01`，不写 canonical 目录；
- 单 worker、Xet 固定下载并发 1、文件并发 1；每个 wrapped Xet request 初始请求 1 次、最多再重试 5 次，这不是 whole-file restart；
- 总预算 5,400 秒从官方 CLI child 启动时开始计时，覆盖下载与完整文件 SHA；失败后的进程组清理可在预算之外额外占用最多 15 秒；外层不自动重启；
- 不假设保留的 3.48 GB 或 Xet cache 会复用。

启动门：attempt3 必须是已清理的 `TIMED_OUT`；Range recovery 必须是终态失败；CLIP/VAE 伴随组件回执必须完整；canonical 与 attempt4 目标均不存在；剩余磁盘至少为目标大小加 2 GiB；独立源码审查通过。

成功门：目标在完整哈希前后保持稳定，大小与完整 SHA 同时匹配。CLI exit 0、临时文件增长或部分下载均不算成功。

证据边界：这是资源获取，不是模型加载、视频生成、质量实验或创新验证。成功后仍须执行 S39 冻结、双审和有界加载。
