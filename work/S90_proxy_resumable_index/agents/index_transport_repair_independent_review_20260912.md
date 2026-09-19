# S90 传输修正独立复审

复审时间：2026-09-12（Asia/Shanghai）  
边界：只读代码、计划和离线测试；未发起网络请求、未访问新归档正文。  
复审对象：

- `index_rtmv_resumable.py`
- `INDEX_PLAN.json`
- `agents/index_transport_repair_20260912.md`
- `agents/test_index_transport_repair.py`

结论：**REVISE（主要修正有效，但仍有可复现性和 INFLIGHT 语义缺口，不建议网络执行）**。

## 已独立复现并通过的部分

命令：

```text
python3 -m py_compile index_rtmv_resumable.py agents/test_index_transport_repair.py
python3 agents/test_index_transport_repair.py
```

输出：

```text
S90_TRANSPORT_REPAIR_OFFLINE_PASS
```

另外重新调用本地 seed 和空链检查，输出：

```text
SEED_PASS 8 12605440 12605440
CHAIN_EMPTY_PASS
HOST_ALLOW True False
```

因此以下修正有本地证据支持：

- `TimeoutExpired` 被转换为结构化 `kind=timeout` 回执，并删除残留 `.part`；测试覆盖了 700B 残留。
- curl 使用 `%{url_effective}`，记录 `url_effective`/`final_host`，最终 scheme 必须为 HTTPS，host 必须匹配计划中的 `huggingface.co` 或 `*.hf.co`。
- `INFLIGHT.json` 采用原子写入，恢复时验证文件名、512B 长度、hash 和 tar member；零块可以恢复为终止状态。
- 普通 seed 链、空扫描链和计划中的 archive identity 可在本地加载。
- 当前本地 SHA-256：
  - `index_rtmv_resumable.py`: `3d5549a4bf040822ec5a229d849c123320d3ebb12aa87fe9c7baed41887156f6`
  - `INDEX_PLAN.json`: `f68c5cfc60dcc0f2f994ebb1e87fdd8ec416e6d56a689d840207e199f3473944`

## 独立发现的剩余风险

### 1. INFLIGHT 没有绑定 plan/code/archive identity（MAJOR）

checkpoint 本身比较了 `plan_sha256`、`code_sha256` 和 `archive_identity`，但 `reconcile_inflight()` 只读取：

- `offset`
- `body`
- `body_sha256`
- `record`

journal 没有保存并验证 `plan_sha256`、`code_sha256`、archive commit/name/bytes/scene。当前 output 目录策略和 checkpoint hash 降低了误用风险，但一个残留、跨运行复制或手工替换的 INFLIGHT 文件仍可能在 checkpoint 通过后被尝试恢复。body/tar header 能证明本地文件一致，不能证明该文件来自当前冻结的请求上下文。

最小修正：写 INFLIGHT 时加入 `plan_sha256`、`code_sha256`、完整 archive identity、schema version；恢复时先 exact compare，任何缺失或不相等直接拒绝。不要从 journal 临时放宽任何 allowlist。

### 2. `record` 与 journal 顶层字段没有全量交叉验证（MAJOR）

`reconcile_inflight()` 验证了顶层 `offset` 和 body hash，但没有明确要求：

```text
record.offset == inflight.offset
record.body == inflight.body
record.body_sha256 == inflight.body_sha256
record.length == 512
record.kind == range_header
```

一个不一致的 record 可能被提交；普通非零成员最终大多会被 `verify_member_chain()` 捕获，但 zero record 的链约束较弱。建议在恢复前做上述交叉检查，并要求 zero record 不含 `tar_member`。

### 3. stale INFLIGHT 与终端状态的边界（MINOR/MAJOR）

主流程在 resume 时先调用 `reconcile_inflight()`，再执行后面的 `selected_development_view`/`SCENE_BOUNDARY`/`FIRST_ZERO_TAR_BLOCK` no-op 判断。若 checkpoint 已是终端状态但残留 journal 内容不匹配，当前会尝试恢复或报错；若内容恰好匹配则删除。这种行为可接受，但应在代码或 schema 明确：终端状态只允许与已提交成功请求完全匹配的残留 journal，其他 journal 一律拒绝，不能继续扫描。

### 4. redirect allowlist 的范围需要保持显式

`host_allowed()` 的 `*.hf.co` 会允许任意 hf.co 子域，包括未来未预期的子域；这是计划中明确写出的 allowlist，当前不算隐藏放宽。若研究记录要求“只允许本次已观察 CDN”，建议将 `us.aws.cdn.hf.co` 作为冻结 host，或保留 wildcard 但在回执中披露。当前测试只证明允许的 CDN 和明显外部 host 的结果。

### 5. bound URL 仍是 path 后缀检查，而非完整 URL 身份

seed/resume 对 S89 URL 检查 `urlparse(...).path.endswith('/resolve/<commit>/<archive>')`，没有要求 scheme/host 为初始计划 host。传输阶段最终 host 有 allowlist，且绑定文件 SHA 固定，风险有限；但独立协议审查仍建议对初始 URL 做 exact canonical URL 检查，并将初始 URL 的 scheme/host/path 写入 archive identity。

### 6. 崩溃窗口仍需保持 at-least-once 表述

`INFLIGHT` 能恢复常见“请求完成但 checkpoint 尚未 persist”的窗口，且 final header 内容不同时拒绝覆盖。但网络请求可能在进程崩溃前已经完成、journal 尚未原子落盘，重启仍可能重新请求同一 offset。因此当前计划写的 `at-least-once network semantics` 是正确的；不能在报告中写 exactly-once。

## 修改建议的最小顺序

1. 给 INFLIGHT 增加并校验计划/代码/archive identity 绑定。
2. 恢复时 exact 校验 record 与顶层 offset/body/hash/length/kind，zero 记录单独约束。
3. 增加终端状态 + stale INFLIGHT fixtures，确保只允许已提交匹配 journal。
4. 对初始 bound URL 使用 canonical scheme/host/path exact 检查。
5. 重新运行现有三个离线测试，再补充上述篡改测试；完成后才能考虑一次严格预算的网络 header 请求。

## 科学边界

即使上述工程修正全部通过，所得最多是有限 RTMV tar 前缀的 header 可读性和候选文件名索引。它不等于 RGB-D 配对数据已取得，不等于未来几何真值可用，也不等于 GRC/GRC-Pilot 的方法或科学假设得到验证。
