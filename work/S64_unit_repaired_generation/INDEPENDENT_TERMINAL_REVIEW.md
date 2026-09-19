# S64 独立终态元数据核验

结论：PASS，仅限真实终态与元数据；后续正文读回仍待执行。核验者 `/root/c2_v9_source_primary`，源码作者 `/root/c2_v9_recovery_author`，执行者 `/root`。本次最终核验 2026-09-08T22:22:39.336676+00:00 至 2026-09-08T22:22:39.492631+00:00。

外部实际运行 2026-09-08T21:28:11.696408+00:00 至 2026-09-08T22:13:40.726069+00:00，2729.029596 秒，return 0、未超时，实际 stdout/stderr 均空。parent/worker/watchdog/start/provisional/commit 哈希链、冻结控制文件身份、9 项生产源与 221 项来源均一致；两个根失败路径不存在，登记的 7 个 PID 在 2026-09-08T22:22:39.488676+00:00 已全部退出。

加载记录与 worker/commit 的 7 项资源消费票一致，每项计数 1；真实单位调用票仅 1 张，绑定同一 manifest、hook、S61 adapter 和原 renderer。票内记录 515 个点、正深度 515 个、长度单位 5.19512286700774e-06；这里没有读取几何正文重算这些数值。

独立重算 JSON 事件哈希链：trace 327 事件，两批均完成、各 50 次 denoiser 回调，保留 ID 1–4 与 5–8；archive 102 事件、50 对完整捕获，6,698 个文件存在且大小共 229,336,164 字节。正文哈希未读。第二批上下文 ID 的元数据是 `[0,2,4,1]`，实际张量逐值消费仍须读回验证。

只读取源码、回执、日志和档案 JSON 元数据；科学张量、RGB、模型权重正文读取均为 0，模型/renderer/adapter/后处理运行均为 0。通过不代表画质好、原 C2 完成、新方法成立或原 cohort 被补齐。可继续既定的一次正文读回，不新增实验条件。

- JSON SHA256：`fa4957941b37f68478e04bc831f4a58fa2edc73f61246459f3e3dab02195a019`
- manifest SHA256：`34c2bad90c5627b6e9742fe65f8c8b4a1ff76da730a2c0d87bbcedcc38b28619`
- external receipt SHA256：`8ebe2376785626c538831201486ea3d9773df94ebab462dfa725f1d2ad948e2c`
- terminal commit SHA256：`ebb1f0b3d7c311c5eb8cf9bb6dea37db194c5255477841477a4aec03565e1f55`
