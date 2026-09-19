# Bounded acquisition repair 最终独立复审（record schema 修正后）

复审时间：2026-09-12（Asia/Shanghai）  
边界：只读本地代码、计划和 fixtures；未联网、未发起任何归档请求。

结论：**PASS（工程协议范围内）**。

## 独立验证结果

执行：

```text
python3 -m py_compile index_rtmv_resumable.py agents/test_index_transport_repair.py
python3 agents/test_index_transport_repair.py
```

结果：

```text
S90_TRANSPORT_REPAIR_OFFLINE_PASS
```

另行执行当前绑定检查：

```text
SEED_PASS 8 12605440 12605440
CANONICAL_PASS
```

## 已核验项目

- `TimeoutExpired` 产生结构化回执并清理残留 `.part`；
- INFLIGHT 顶层 schema、plan SHA、code SHA、archive identity 全部绑定；
- 内嵌 transport record 的 schema、kind、length、offset、body 和 hash 交叉校验；
- terminal-zero 正确 offset、中间 zero、错误 stale journal、已提交 journal 去重；
- canonical RTMV HTTPS source URL 的完整路径，并拒绝 query/fragment；
- final URL 的 HTTPS 和 host allowlist；
- seed 8 个成员及 probe 到新扫描 offset 的衔接；
- Python 静态编译和离线回归测试。

## 仍需保留的语义边界

计划的网络语义仍是 **at-least-once**。INFLIGHT journal 能恢复常见 checkpoint 崩溃窗口，但不能宣称网络 exactly-once。首次实际网络执行仍需使用冻结的 plan/code hash、严格请求/字节/时间预算，并保存真实回执。

该 PASS 只针对传输与可恢复索引工程协议，不代表已获得 RGB-D 配对真值，不代表 Gate 0 数据资格通过，也不代表 GRC-Memory/GRC-Pilot 方法或科学假设已验证。
