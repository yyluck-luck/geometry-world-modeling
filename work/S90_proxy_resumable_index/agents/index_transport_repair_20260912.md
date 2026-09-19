# S90（RTMV归档配对数据恢复与索引协议审查）最小传输修正

日期：2026-09-12（本地离线修正）

## 修正内容

1. **超时结构化回执**：在 `subprocess.run` 内捕获 `TimeoutExpired`，记录
   `kind=timeout`、offset、实际耗时、限时、超时前正文长度与 SHA-256，并删除残留
   `.part` 文件，同时归类为 `STOPPED_TRANSPORT`。这样超时不再退化成只有 offset
   的外层错误。
2. **最终重定向身份**：记录 curl 的 `url_effective` 与 `final_host`；只接受 HTTPS，
   且最终主机必须匹配计划中的 `huggingface.co` 或本次冻结探针实际看到的
   `us.aws.cdn.hf.co`。初始 URL 还必须精确匹配冻结的 HTTPS
   `/datasets/TontonTremblay/RTMV/resolve/<commit>/abc.tar` 路径。计划把允许主机写入
   `INDEX_PLAN.json`，不得从响应临时放宽。
3. **崩溃窗口**：请求成功、checkpoint 写入前先写原子 `INFLIGHT.json`。恢复时验证
   plan/code SHA、归档身份、offset、文件名、长度、哈希和 tar 头，再提交一次并删除
   journal；若 checkpoint 已经提交，则验证匹配后只删除 journal。成功头文件若已存在
   且内容不同，直接拒绝覆盖。
   这关闭了常见的“成功但未落盘”窗口，同时仍诚实保留极小的 at-least-once 网络语义。
4. **终端 zero offset**：已有链检查继续要求 zero block 位于期望的下一个 header offset，
   且只能是成功请求的最后一项；恢复 journal 对 zero block 单独提交终止状态。

## 离线验证

以下测试没有访问网络：

```text
python3 -m py_compile work/S90_proxy_resumable_index/index_rtmv_resumable.py work/S90_proxy_resumable_index/agents/test_index_transport_repair.py
python3 work/S90_proxy_resumable_index/agents/test_index_transport_repair.py
S90_TRANSPORT_REPAIR_OFFLINE_PASS
```

测试覆盖：700 B 超时残留被删除且回执结构完整；zero block journal 恢复只提交一次；
已提交 zero 的孤儿 journal 不重复追加；offset 错位的 stale terminal journal 被拒绝；
malformed kind/length 的 receipt 被拒绝；canonical RTMV URL 通过；允许的
`us.aws.cdn.hf.co` 通过，未允许主机拒绝。

## 当前边界

这只是数据获取协议的工程修正，不是 S91R 或 GRC-Pilot 的科学结果。仍需 root Agent
独立复审代码和计划哈希后，才可考虑一次符合字节、请求数和时间预算的有界网络索引；Gate 0
仍负责判断数据是否具备正式实验资格。

## 独立复审命令

```bash
cd /Users/rocket/Desktop/HKUST\ IT/ip-/geometry-world-modeling
python3 -m py_compile work/S90_proxy_resumable_index/index_rtmv_resumable.py
python3 - <<'PY'
# 复现本报告中三项离线断言；不得替换为真实 URL 或放宽 allowlist。
PY
```
