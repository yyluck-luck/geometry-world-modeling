# S90 索引协议修正后跟进审查：超时、重定向身份与崩溃窗口

审查日期：2026-09-12（Asia/Shanghai）  
网络边界：未发起网络请求；只执行了本地 Python/fixture 测试。  
对象：`work/S90_proxy_resumable_index/index_rtmv_resumable.py` 当前版本。

## 已确认的修正

1. **seed 绑定可用。** `seed_members()` 已删除对 S89 历史计划中不存在的 `archive_commit` 字段的硬比较，改为检查 URL path 的 `/resolve/<commit>/<archive_name>` 后缀。本地绑定 smoke test：

   ```text
   SEED_PASS 8 12605440 12605440
   ```

   即返回 8 个 seed 成员，最后一个 `00000/00134.depth.exr` 的下一个 header offset 与冻结 `start_offset` 一致。

2. **checkpoint archive identity 已写入 state。** 首次 state 保存 archive name、commit、bytes、scene；resume 会比较这四项并重新派生 seed，seed 前缀篡改会被拒绝。

3. **链和空扫描路径可编译。** `python3 -m py_compile` 通过；空扫描链本地测试返回 `CHAIN_EMPTY_PASS`。

4. **终端零块已部分处理。** `verify_checkpoint_headers()` 会验证无 `tar_member` 的成功请求确实是 512 个零字节并且状态为 `FIRST_ZERO_TAR_BLOCK`；普通请求仍要求 tar member。

## 本轮发现的剩余缺口

### A. `TimeoutExpired` 仍然未结构化处理（REVISE）

`request_header()` 第 242--259 行直接调用 `subprocess.run(..., timeout=...)`，没有捕获 `subprocess.TimeoutExpired`。本地 monkeypatch 测试得到：

```text
TIMEOUT_EXCEPTION TimeoutExpired Command '['curl']' timed out after 1 seconds
```

因此超时会直接抛到 `main()` 外层循环，最后只形成简短的：

```json
{"offset": <offset>, "error": "Command ... timed out ..."}
```

它没有统一的 elapsed、body bytes/hash、是否存在 partial body、超时限制和安全 stderr 字段；也没有保证把仍存在的 `.part` 文件按 512B上限清理/标记。

最小安全修正建议：在 `request_header()` 内以 `try/except subprocess.TimeoutExpired` 包围 `subprocess.run`；读取当前 `.part`（若存在），若大于 512B 删除，否则记录其 hash；生成 `kind: "timeout"`、`timeout_seconds`、`started_utc`、`completed_utc`、`elapsed_seconds`、`offset`、`body_bytes`、`partial_body_discarded` 的结构化 JSON，再按现有错误通道抛出。不要把异常对象的完整 command 或可能含 query token 的 URL 写入回执。

### B. 最终重定向身份仍未记录/约束完整（REVISE）

curl 使用 `-L`，并检查最终 HTTP 206、TLS verify=0 和 Content-Range；这是传输完整性的一部分。但命令没有 `%{url_effective}` 输出，代码也没有 `url_effective` 字段或最终 host/scheme allowlist。当前 resume 只检查绑定 URL 的 path 后缀，不检查 host；理论上带有正确 path 的非预期 host 仍会通过绑定检查。S89/S88 本地 SHA 降低了本地篡改风险，但不能替代协议自描述。

最小安全修正建议：在计划中固定允许的初始 host（`huggingface.co`），若允许 CDN，再固定允许的 CDN host 列表；curl `-w` 同时输出 `%{url_effective}`，解析并记录脱敏后的 scheme/host/path。要求最终 scheme 为 HTTPS，host 属于 allowlist，path 对应固定 commit/name；否则将请求标为 transport failure。签名 query 必须继续脱敏。

### C. 崩溃窗口语义：诚实但仍是 at-least-once

当前每个普通 header 成功后才把 `successful_requests` 和 `members` 写入 checkpoint；如果进程在 `request_header()` 完成、`persist()` 前崩溃，磁盘 checkpoint 仍指向旧 offset，而 header 文件可能已存在。重启会重新请求同一 offset，文件名可能被覆盖，产生一次重复网络请求。计划已明确：

```text
checkpoint_policy = at-least-once until crash-window reconciliation is implemented
```

这是诚实的当前语义，没有把它错误宣传成 exactly-once。若不实现 reconciliation，报告必须保留 at-least-once；若要修正，最小方案是在每个 final header 文件写入后使用独立 receipt/offset+hash journal，并在启动时扫描 `.bin` 与 journal，只有 offset、body hash、tar 解码、plan/code/archive identity 全部一致时才把记录补回 checkpoint。仅凭残留 `.bin` 不足以证明请求已完成。

### D. 终端 zero offset 仍缺少链绑定（REVISE）

零块 body/hash 已校验，但当前链校验未明确要求 terminal-zero record 的 offset 等于：

- 若扫描区为空：`plan.start_offset`；
- 否则：最后一个扫描成员的 `next_header_offset`。

建议在 `verify_member_chain()` 先计算 `expected_terminal_offset`，要求零块请求只能是 `successful_requests` 的最后一项、状态为 `FIRST_ZERO_TAR_BLOCK`，且 `request.offset == expected_terminal_offset`；同时要求 `state.next_header_offset` 仍等于该 terminal offset。这样能避免“对齐的零块放在错误位置”被接受。

## 最小离线验收矩阵

网络执行前仍应补充以下 fixtures：

- normal one-member chain：通过；
- zero block at exact next offset：通过并可 resume no-op；
- zero block at wrong aligned offset：拒绝；
- no-tar-member request in the middle：拒绝；
- TimeoutExpired with no part / <=512B part / >512B part：三者均结构化、清理规则明确；
- redirect final host outside allowlist：拒绝；
- crash-window residual header without reconciliation journal：明确按 at-least-once 重试，不自动视为已成功。

## 结论

当前版本比上一轮明显更安全：seed 绑定、seed 前缀比较、archive identity state、空链和基本 zero-body 校验均已得到本地证据支持。但由于超时回执、最终重定向身份和 terminal-zero offset 仍不完整，本审查结论保持：

**REVISE；不建议现在发起网络索引。**

即使这些工程缺口修复，索引产物仍只说明可读取归档前缀的 tar headers；它不构成 RGB-D 配对样本、未来几何真值、GRC 方法验证或科学结果。
