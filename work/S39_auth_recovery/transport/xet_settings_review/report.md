# S39：Xet 并发与重试参数来源复核

记录时间：2026-09-07T04:18:31.097754+00:00（UTC）。这是配置来源审查，未启动下载或新增传输探测。此前 curl 失败记录保持原样。

本机隔离环境为 `huggingface_hub 1.30.0`、`hf_xet 1.6.0`。推荐下一步先等当前 CLIP 终态，再为同一原 VMem 权重做一次单独、低并发尝试；是否改善 TLS 尚未验证。

## 已核参数与版本边界

| 参数 | 本轮确认的意义 |
|---|---|
| `HF_XET_FIXED_DOWNLOAD_CONCURRENCY=1` | 官方当前 Xet 文档说明该别名把 initial/min/max 下载并发都固定为 1；本机二进制含同名字符串。 |
| `HF_XET_DATA_MAX_CONCURRENT_FILE_DOWNLOADS=1` | 同时下载文件数上限；与单文件内部并发不同。 |
| `HF_XET_CLIENT_RETRY_MAX_ATTEMPTS=1` | 源码含义为至多一次重试，即首次请求加一次重试。 |
| `HF_XET_HIGH_PERFORMANCE=0` | 此次不要启用提高并发与缓冲的高性能预设。 |
| `HF_HUB_DISABLE_XET=0` | 新进程回到 Xet 路径，不能继承上次 HTTP 尝试的禁用设置。 |

依据：[官方 Xet 设置](https://huggingface.co/docs/hub/en/xet/using-xet-storage)。仅针对未来新进程设置，现有下载不受改动。

旧 [Hub 环境变量页](https://huggingface.co/docs/huggingface_hub/en/package_reference/environment_variables) 列 `HF_XET_NUM_CONCURRENT_RANGE_GETS`（每文件 range 并发），但已装 1.6.0 二进制没有该完整字面量。本轮不能确认旧名在本版本生效；字面量缺失本身也不能严格证明不存在动态别名。因此本次采用有当前文档和本机字面量双重证据的 fixed 参数。

## 重试不能替代外层截止时间

[v1.6.0 官方 retry_wrapper.rs](https://raw.githubusercontent.com/huggingface/xet-core/v1.6.0/xet_client/src/cas_client/retry_wrapper.rs) 的 `take(max_attempts)` 限制重试延迟数；其测试明确设置 3 后总请求为 4。`MAX_ATTEMPTS=1` 不等于只请求一次。该配置按请求包装器生效，不能限制整个多 range 文件只有一次额外网络请求。

更关键的是，当前官方文档把 `HF_XET_CLIENT_RETRY_MAX_DURATION` 描述为请求重试总时间，而同版本源码在此包装器中将它传给 `max_delay`。源码测试把 60 秒配置得到 3、9、27、60、60 秒退避，已足以否定其作为累计时间硬上限的解释。本轮不设置它来假装保障任务截止；父任务应在启动前独立记录一个进程总时限，且不自动重开失败进程。

本机 `huggingface_hub/file_download.py` 的普通 HTTP 下载显式关闭异常重试（仅指定 HTTP 408/429 状态重试）；`_http.py` 的通用默认重试数是另一个 Python 层设置，不能拿来代表 Xet 内部配置。这与已观察 HTTP 尝试迅速因 ConnectError 结束相容，但不能单凭代码确定所有失败根因。

## 唯一下一步和证据边界

等待当前 CLIP 终态，保持已有代理和官方授权缓存，保留同一 repo/revision/期望 SHA，再由父任务按以上参数启动至多一个有总时限的 VMem 进程。全量完成后依旧必须核完整大小和 SHA。Xet 重建可能缓存后才落盘，不能仅因临时文件仍为 0 字节就断言没收流。

VAE 已完成和 CLIP 实际收流是父任务提供的既有观察，新连接 TLS EOF 也是真实观察；间歇或并发问题只是待证解释。低并发目前是可追溯的排障条件改变，不是科学实验结果或已证修复。本轮没有读取凭据、改变系统代理、触碰 CLIP 进程、安装环境或改主账。

父任务随后确认：后续单次尝试外控总时限为 1800 秒；先等 CLIP 终态，观察到明确新传输错误后再判断。这仍是计划，尚未执行。
