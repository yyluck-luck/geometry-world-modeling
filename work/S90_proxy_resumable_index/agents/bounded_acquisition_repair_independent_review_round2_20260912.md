# Bounded acquisition repair 第二轮独立复审

复审时间：2026-09-12（Asia/Shanghai）  
边界：只读本地代码、计划与 fixtures；未联网、未发起任何归档请求。

结论：**REVISE（核心问题已修复；仅剩两个低风险协议严谨性缺口）**。

## 离线复现

运行：

```text
python3 -m py_compile index_rtmv_resumable.py agents/test_index_transport_repair.py
python3 agents/test_index_transport_repair.py
```

结果：

```text
S90_TRANSPORT_REPAIR_OFFLINE_PASS
```

重新调用当前本地 seed/canonical 检查：

```text
SEED_PASS 8 12605440 12605440
CANONICAL_PASS
```

其中 canonical URL 使用实际绑定的完整 RTMV 路径：

```text
https://huggingface.co/datasets/TontonTremblay/RTMV/resolve/<commit>/abc.tar
```

## 已确认修复

1. `assert_canonical_source_url()` 已补上 `/datasets/TontonTremblay/RTMV/`，当前 seed 不再因路径缺失而失败。
2. INFLIGHT 已绑定 `plan_sha256`、`code_sha256` 和 archive identity（name/commit/bytes/scene）。
3. INFLIGHT 恢复现在交叉检查 offset、body、body hash、`kind=range_header` 和 `length=512`；错误 kind/length fixture 会拒绝。
4. terminal-zero 链已检查终端位置；错误 offset 和中间 zero fixture 会拒绝。
5. timeout、URL effective/final host allowlist、重复 zero journal、stale offset journal 均有离线测试。
6. 计划继续明确 at-least-once 网络语义，没有错误宣称 exactly-once。

## 剩余问题

### 1. canonical URL 仍未拒绝 query/fragment（MINOR）

当前 helper 检查 scheme、hostname 和 path，但未要求 `parsed.query == ""`、`parsed.fragment == ""`。因此形式上以下 URL 仍会通过路径检查：

```text
https://huggingface.co/datasets/TontonTremblay/RTMV/resolve/<commit>/abc.tar?unexpected=1
https://huggingface.co/datasets/TontonTremblay/RTMV/resolve/<commit>/abc.tar#fragment
```

S89 文件由冻结 SHA 绑定，且当前真实 URL 没有 query/fragment，因此本轮不会改变实际运行结果；但如果函数的语义是“canonical exact URL”，应明确拒绝 query 和 fragment，或将完整 source URL（含空 query/fragment）纳入计划并逐项比较。

### 2. INFLIGHT 顶层 schema 未显式校验（MINOR）

`reconcile_inflight()` 校验了 identity 与 record 字段，但没有要求：

```text
inflight["schema"] == "s90-inflight-v1"
```

因此一个顶层 schema 名称被篡改、但其余字段仍一致的 journal 仍可能恢复。当前 plan/code/archive SHA 和临时目录策略显著降低风险，且不影响 tar header 本身；为保证回执协议可审计，建议增加 exact schema check。

## 结论与建议

严格按协议审查，结论保持 **REVISE（minor）**。修正顺序很小：

1. canonical helper 增加 query/fragment 为空检查；
2. `reconcile_inflight()` 增加 INFLIGHT schema exact check；
3. 各增加一个离线 fixture，重新运行现有测试。

如果项目负责人把冻结 S89 SHA、当前空 query/fragment 以及 plan/code/archive identity 视为充分边界，则可以在报告中写成 **PASS with two minor hardening notes**；但在这两个条件未明确写入代码前，我不建议把结论简化为完全 PASS。

## 科学边界

即使工程协议达到 PASS，也只说明在固定请求预算内能安全索引 tar headers；不等于取得合格 RGB-D 配对数据、不等于未来几何真值可用，也不等于 GRC 方法得到科学验证。
