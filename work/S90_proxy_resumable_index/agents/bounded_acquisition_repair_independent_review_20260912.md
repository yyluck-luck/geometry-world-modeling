# Bounded acquisition repair 独立复审

复审时间：2026-09-12（Asia/Shanghai）  
边界：只读本地代码、计划和离线 fixtures；未联网、未发起任何归档请求。  
审查对象：当前 `index_rtmv_resumable.py`、`INDEX_PLAN.json`、传输修正说明和 `agents/test_index_transport_repair.py`。

结论：**REVISE**。INFLIGHT 身份绑定和 terminal-zero 链约束已有实质改进，但当前代码存在一个会阻止启动的 canonical URL 回归，且 record 交叉校验仍不完整。

## 1. 离线复现结果

已运行：

```text
python3 -m py_compile index_rtmv_resumable.py agents/test_index_transport_repair.py
python3 agents/test_index_transport_repair.py
```

输出：

```text
S90_TRANSPORT_REPAIR_OFFLINE_PASS
```

这证明已有 fixture 覆盖了 timeout 回执、零块 journal 首次恢复、已提交 journal 去重、错误 offset stale journal 和 host allowlist 的基本路径。

另外独立运行 seed/空链及 terminal fixtures：

```text
CHAIN_EMPTY_PASS
zero_wrong REJECT RuntimeError zero tar block is not at the expected chain offset
zero_middle REJECT RuntimeError a non-terminal successful request lacks a tar member
```

## 2. 关键阻塞：canonical source URL 路径写错（CRITICAL）

当前 `assert_canonical_source_url()` 第 48 行使用：

```python
expected_path = f"/resolve/{plan['archive_commit']}/{plan['archive_name']}"
```

但实际已绑定的 S89 URL 是：

```text
https://huggingface.co/datasets/TontonTremblay/RTMV/resolve/<commit>/abc.tar
```

它的 path 包含 `/datasets/TontonTremblay/RTMV/` 前缀。因此当前最新代码的本地 `seed_members(plan)` 直接失败：

```text
RuntimeError: source URL is not the frozen canonical HTTPS archive URL
```

这不是网络错误，而是代码和现有冻结回执/计划的 schema 不一致；修复前不能启动 acquisition。最小修正是将数据集前缀作为冻结计划字段并要求完整 URL exact match，或在代码中构造正确的完整 canonical path：

```text
/datasets/TontonTremblay/RTMV/resolve/<commit>/<archive_name>
```

推荐把完整 `source_url` 放入计划并用 `parsed.scheme/hostname/path/query/fragment` 与其逐项比较，避免再次手写漏掉前缀。

## 3. INFLIGHT 身份绑定：已修正但仍需 record 完整交叉校验

当前 journal 已写入并检查：

- `plan_sha256`
- `code_sha256`
- `archive_identity`（name/commit/bytes/scene）
- offset、body 名、body hash、record

这部分方向正确，能阻止不同计划或代码版本的 journal 被静默恢复。

但 `reconcile_inflight()` 目前只显式比较：

```text
record.offset == inflight.offset
record.body == inflight.body
record.body_sha256 == inflight.body_sha256
```

它没有要求：

- `record.length == 512`
- `record.schema == s90-transport-receipt-v2`
- `record.kind == range_header`
- `record.offset` 为 512 对齐且在 archive 范围内
- zero body 时 `record` 不含 `tar_member`
- regular body 时 `record.length == 512` 且 `record.tar_member.header_offset == offset`

离线构造一个 body/hash/offset 正确、但 `kind="WRONG"`、`length=999` 的 zero journal，当前仍可被接受：

```text
MALFORMED_RECORD_ACCEPTED WRONG 999
```

后续普通 checkpoint 校验可能暴露部分问题，但 journal 恢复本身不应先写入不合约的 record。建议在 `reconcile_inflight()` 开头拒绝所有上述不一致，再执行 persist。

## 4. terminal-zero 与 stale fixtures

当前 `verify_member_chain()` 已加入：

- 无 tar-member 请求只能是最后一项；
- 状态必须是 `FIRST_ZERO_TAR_BLOCK`；
- zero offset 必须等于 `plan.start_offset` 或最后扫描成员的 next offset；
- `state.next_header_offset` 必须等于该 zero offset。

独立 wrong-offset 和 middle-zero fixtures 均按预期拒绝，说明这部分修正有效。

现有传输测试也覆盖了：首次 zero journal 恢复、已提交 zero journal 不重复追加、错误 offset 的 stale terminal journal 拒绝。建议再增加一个“正确 offset 但错误 `record.kind/length/tar_member`” fixture，以防止本报告第 3 节的缺口回归。

## 5. 代码/计划 hash 与 crash-window 语义

checkpoint resume 会比较 `state.plan_sha256` 和当前 `INDEX_PLAN.json` SHA，也比较 `state.code_sha256` 和当前脚本 SHA；INFLIGHT 也已经绑定相同值。这是必要的版本门控。

计划仍诚实地保留：

```text
at-least-once network semantics
```

INFLIGHT 只能关闭“请求完成且 journal 已写入但 checkpoint 尚未提交”的常见窗口；若进程在 journal 原子落盘前崩溃，可能重新请求相同 offset。因此不能报告 exactly-once。

## 6. 修正顺序

1. 先修正 canonical source URL 的完整数据集路径，并用本地 `seed_members(plan)` smoke test 证明返回 8 个 seed 成员。
2. 为 `reconcile_inflight()` 增加 record schema/kind/length/offset 对齐、zero/regular 分支和 tar header offset 校验。
3. 增加 malformed-record、正确 zero offset 错误 record、regular record hash/offset 不一致的离线 fixtures。
4. 重新运行全部离线测试和 py_compile，仍不得联网。

## 7. 科学边界

即使上述工程问题全部修复，bounded acquisition 也只是在有限预算下索引 tar headers。它不等于 RGB-D 配对数据资格通过，不等于有未来几何真值，更不等于 GRC-Memory/GRC-Pilot 已验证。
