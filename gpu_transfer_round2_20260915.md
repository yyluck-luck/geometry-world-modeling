# GPU transfer round 2 — 2026-09-15

检查时间：2026-09-15 13:08:43（Asia/Shanghai；UTC 05:08:43）。

## 检查结果

依据现有传输状态回执 `work/S101_env_bootstrap/WEIGHT_TRANSFER_STATUS_20260915.json`（最近一次状态检查 UTC 05:06:36），远端目录为 `/home/yliutz/gwm_weights_20260915`，VMem 权重仍未完成：

| 文件 | 本地字节数 | 最近已记录远端字节数 | 状态 |
|---|---:|---:|---|
| `vmem_weights.pth` | 5,056,346,672 | 2,666,233,856 | 部分传输 |
| `cut3r_512_dpt_4_64.pth` | 3,173,761,006 | 3,173,761,006 | 字节数完整；已有 SHA-256：`45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103` |
| `open_clip_model.safetensors` | 3,944,517,836 | 3,944,517,836 | 字节数完整；远端哈希待核 |
| `diffusion_pytorch_model.safetensors` | 334,643,276 | 334,643,276 | 字节数完整；远端哈希待核 |
| `config.json` | 547 | 547 | 字节数完整；远端哈希待核 |

本轮使用只读 SSH 统计尝试重新取得远端字节数，但认证返回 `Permission denied (publickey,password,keyboard-interactive)`，因此没有把旧字节数冒充为本轮实时读数。现有本机 SSH 会话 PID 28665 仍保持 TCP established，但本轮没有接管、写入或提交任何远端作业。

## 科研边界

传输未能确认完成；没有计算远端哈希，没有加载模型，没有读取数据或未来 GT，没有运行模型或正式 GRC。下一步只能在认证恢复后读取远端精确字节数；只有五个文件的字节数和 SHA-256 全部与本地一致，才允许进入无数据 model-load smoke。

