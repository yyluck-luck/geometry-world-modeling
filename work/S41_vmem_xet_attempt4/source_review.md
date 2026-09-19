# S41 VMem Xet Attempt 4 独立源码审查

审查完成时间：2026-09-07T05:37:17+00:00（Asia/Shanghai：2026-09-07T13:37:17+08:00）

## Verdict

**PASS_SOURCE_REVIEW_NOT_EXECUTED**

本审查通过下列固定源码和协议的一次有界资源下载尝试：

- `download_attempt4.py`：`a708d23cc0b64c8b3f5a23d427a6414a12fe1e1fb935beb8726b3e698102aa15`
- `PROTOCOL.md`：`ba6b7befbbb4c0c4f94d958cd832c4b73d39cdc18de1a87badf10f431d2ddbea`

任一文件发生变化都会使本 PASS 失效，必须重新审查。该 PASS 只说明源码和协议满足一次执行的静态门，不说明下载已经开始、权重已经完整、模型已经加载或科学实验已经运行。

## 逐项审查

### 1. 前序终态和进程组

PASS。启动前代码要求 Attempt 3 的 repo、revision、expected bytes、expected SHA 与当前目标逐字段一致，状态必须是 `TIMED_OUT`，receipt 中 child/group 必须为 false，并再次用 `os.killpg(pgid, 0)` 要求旧进程组实际不存在。

HTTP Range recovery 也必须属于相同 repo/revision/size/SHA，状态必须是 `FAILED_RETAIN_UNVERIFIED_CANDIDATE`，接收 Range 字节必须为 0，且 canonical/source partial 都未修改。当前只读检查中 Attempt 3 的 PGID 84800 没有可见成员。

### 2. 唯一输出与 canonical 隔离

PASS。证据目录固定为 `work/S41_vmem_xet_attempt4/execution_01`，通过 `mkdir(exist_ok=False)` 防止覆盖；下载目录固定为 `data/vmem_recovery/xet_attempt4_01`，要求不存在后再独占创建。当前两目录均不存在。

命令的 `--local-dir` 只指向新的 recovery 目录。canonical `data/vmem_original/vmem_weights.pth` 只被用于存在性拒绝门，没有写入、移动、链接或删除路径。当前 canonical 不存在。

### 3. 官方 CLI、版本和固定身份

PASS。执行文件固定为隔离环境内的 `cli-env/bin/hf`；该 wrapper 明确调用同一隔离环境的 Python。代码在下载前实际执行并严格比较 `hf --version == 1.30.0`，并通过同一隔离 Python 严格比较 `hf-xet == 1.6.0`。本次本地只读版本检查分别得到 `1.30.0` 和 `1.6.0`。

下载命令固定 repo `liguang0115/vmem`、filename `vmem_weights.pth`、revision `ac5921080a57f5a634f4b9acbbc8f3db67c9d113`。期望大小 5,056,346,672 bytes 与 SHA-256 `675dc486a02ea06ecf8b6ab0cf4ef88c92298751b2daacf9f65c59871fcb7fe4` 来自已审读的固定 helper。环境显式覆盖 `HF_ENDPOINT=https://huggingface.co`、`HF_HUB_OFFLINE=0`、`HF_DEBUG=0`，不会继承另一个 Hub endpoint 或离线/debug 状态。

### 4. 并发与重试语义

PASS。CLI `--max-workers 1`，Xet fixed download concurrency 为 1，文件并发为 1，高性能模式关闭。`HF_XET_CLIENT_RETRY_MAX_ATTEMPTS=5` 在协议和 receipt 中被准确表述为：每个 wrapped Xet request 有 1 次初始请求和最多 5 次请求级重试；它不是 whole-file restart。外层没有循环或自动重新启动整个下载。

### 5. 5400 秒总预算与完整 SHA

PASS。计时从官方 CLI child 启动前立即设置 `start` 开始。下载监控循环每次迭代检查同一 `BUDGET=5400`；CLI exit 0 后，完整文件 SHA 循环继续使用同一 `start`，并在最后一块处理完、重新 stat 后再做一次 deadline 检查。因此不能在下载耗尽预算后另获一段未计时的 SHA 时间。

协议准确说明 precheck 不在这 5400 秒内，下载和完整 SHA 在内；失败后的 SIGTERM/SIGKILL 清理最多可额外使用 15 秒。

### 6. 完整身份成功门

PASS。CLI exit 0 仅允许进入校验，不会直接标成功。目标必须存在；程序对整个目标做 SHA-256，并比较哈希前后的 size、mtime_ns、inode、ctime_ns。只有文件稳定、大小精确、完整 SHA 精确三者同时成立，状态才是 `VERIFIED_COMPLETE_ORIGINAL_WEIGHT`，返回码才可能为 0。其余身份结果均返回 1。

### 7. 信号、错误与清理

PASS。child 使用 `start_new_session=True`，其 PID 同时作为进程组 ID 保存。单次 wrapper SIGTERM 被转成 `ExternalTermination`，进入异常路径并标记 `INTERRUPTED`。进入 `finally` 后先忽略第二次 SIGTERM，避免清理和终态回执被重复信号打断；随后对整个 child PGID 依次尝试 SIGTERM（5 秒）和 SIGKILL（10 秒），并轮询、reap leader、记录信号和最终 child/group 状态。

只要 child 或 group 仍存活，原状态会保存在 `status_before_cleanup_failure`，最终状态强制变为 `CLEANUP_FAILED`。reader 最多 join 1 秒；最后原子替换终态 receipt。SIGKILL、断电、磁盘故障等不可捕获情况不在保证范围内，这是系统边界，不影响本次静态 PASS。

### 8. Python 控制流

PASS。AST 解析成功。precheck/下载/哈希异常统一进入 `except BaseException`，形成 `TIMED_OUT`、`INTERRUPTED` 或 `FAILED` 并返回 1。CLI 非零分支先写 `DOWNLOAD_FAILED`，return 1 仍会执行 `finally`。成功或身份不匹配分支的 return 也会执行同一 `finally`；`finally` 本身没有 return，不会覆盖 try/except 的返回值。终态和进程组字段在最终返回前保存。

## 非阻断限制

- 如果 CLI 已生成完整命名的目标、但随后 SHA 超时或身份不符，该文件会留在专用 recovery 目录；它必须继续由 receipt 状态门控，不能仅按文件名交给 S39。
- Companion 文件在此处核对 receipt 状态、当前存在性和大小，并要求 receipt 内 actual SHA 等于 expected SHA；本脚本不会再次读取约 4.3 GB 伴随组件重算 SHA。它复用的是先前完整校验事实。
- 源码读取前序 JSON 后再单独读取其 bytes 记录 SHA，没有把 receipt 当作加密签名。项目约定终态 receipt 只追加/不修改；若这些输入被外部改写，本次执行证据必须重新审查。
- 本 PASS 由外部启动者按双 SHA 执行；launcher 不自行读取 `source_review.json`。启动者必须在启动前再次匹配本审查的两个 SHA，且只启动一次。

## 审查边界

- 没有启动下载或网络请求。
- 没有导入或运行候选 launcher 的 `main()`。
- 没有读取、打印或复制 token/credential 文件。
- 没有运行模型、生成视频或执行科学实验。
- 没有修改主账或既有证据；只新增本审查的两个文件。

