# Bounded acquisition repair 最终独立复审

复审时间：2026-09-12（Asia/Shanghai）  
边界：只读本地代码、计划和离线 fixtures；未联网、未发起任何归档请求。

结论：**REVISE（核心目标已通过；仅剩一个 record schema 的轻量协议缺口）**。

## 已通过的独立检查

运行结果：

```text
python3 -m py_compile index_rtmv_resumable.py agents/test_index_transport_repair.py
S90_TRANSPORT_REPAIR_OFFLINE_PASS
SEED_PASS 8 12605440 12605440
CANONICAL_PASS
```

当前 fixtures 已覆盖并通过：

- `TimeoutExpired` 结构化回执与残留 `.part` 清理；
- INFLIGHT 计划 SHA、代码 SHA、archive identity 绑定；
- offset/body/hash/`kind=range_header`/`length=512` 的 record 交叉检查；
- zero journal 首次恢复、已提交 journal 去重、错误 offset stale journal；
- terminal zero offset 和中间 zero 拒绝；
- canonical RTMV 初始 URL 的完整 path 检查；
- query/fragment 初始 URL 拒绝；
- 顶层 INFLIGHT schema 精确检查；
- final host allowlist 基本检查。

## 唯一剩余缺口

`reconcile_inflight()` 当前没有要求内嵌 transport record 的 schema 为：

```text
s90-transport-receipt-v2
```

离线构造 `record.schema="WRONG"`，保持 offset、body、hash、kind 和 length 全部正确，当前仍返回接受：

```text
WRONG_RECORD_SCHEMA_ACCEPTED
```

这不会改变 header bytes、offset 链或 archive identity，但会使 receipt schema 失去严格协议意义。最小修正：在现有条件中增加：

```python
or record.get("schema") != "s90-transport-receipt-v2"
```

并将该 malformed record 加入测试；之后重新运行全部离线测试。

## 语义边界

计划仍正确声明网络语义为 at-least-once。INFLIGHT 能修复常见 checkpoint 崩溃窗口，但不能保证网络层 exactly-once。当前复审没有发起网络请求。

即使该轻量缺口补齐，bounded acquisition 仍只验证有限 tar header 索引协议，不证明取得合格 RGB-D 配对数据、不提供未来几何真值，也不验证 GRC-Memory/GRC-Pilot 科学假设。
