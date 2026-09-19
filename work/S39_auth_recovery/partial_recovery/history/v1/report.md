# 原 VMem 片段恢复：仅源码准备，未运行

完成时间：2026-09-07T04:55:10.338996+00:00（UTC）。本轮未发网络请求、未读活跃权重内容、未改动或终止当前下载，也未改其 1800 秒预算。

## 来源结论

本机官方 `huggingface_hub 1.30.0` 的 `file_download.py:1930–2005` 明确每次使用 UUID 临时名、以 `wb` 打开，并在 finally 删除临时路径。现有硬链接能在原临时路径删除后保住 inode，但下一次 CLI 不会据此自动续接该路径。`xet_get` 当前调用 `group.start_download_file`；本轮已读接口未提供可承诺复用任意现存文件偏移的选项。Xet 的内部块缓存另属不同机制，没有核到它保证复用这份硬链片段的证据。

本机 `http_get:325–473` 有显式 `resume_size`，但服务器忽略 Range 返回 200 时会截断本地数据并回退整文件，而且流内重试会随进展重置。为保留原片段和一次尝试边界，本准备不直接调用该函数。使用官方 `get_hf_file_metadata:1578–1651` 获取固定身份与下载位置；其 `retry_on_errors=False` 在 `utils/_http.py:698–746` 确实关闭状态及异常重试，并在离开 Hub 的跳转前返回元数据。

这些是实际本机源码审读，完整路径和 SHA 在 receipt.json。没有新增网页检索，也没有把 TLS 通路可用性视作已验证。

## 恢复合同

`recover_partial.py` 导入不做 I/O，只有显式命令执行才启动。执行时依次检查：

1. attempt3 回执必须是未验证终态，原 repo/revision/大小/SHA 匹配；child/group 都明确结束，再用 PGID 的信号 0 确认组不存在。当前 live 状态会在打开片段或访问网络之前被拒绝。
2. 只读已登记 inode 的硬链接，将其独立复制到新目录；复制期间核 inode、大小、mtime、ctime 稳定。原硬链接不修改。片段的 SHA 只是复制记录，`st_size` 不证明整个前缀已经写全，稀疏洞或未写范围仍可能存在。
3. 需要补字节时，由官方 SDK 正常消费已授权 HF_HOME。Bearer 只允许发送到 `https://huggingface.co`；元数据最多三次 HEAD（含同主机重定向），不重试。严格比对原固定 revision、5,056,346,672 字节及原 LFS SHA。
4. CDN 使用另一个无认证、无 cookie 状态的客户端，仅持官方元数据返回的 HTTPS 签名位置，做一次剩余区间 GET，不跟重定向。必须是 206、精确起止/总量的 Content-Range、identity 编码；声明长度和实际收到字节数都必须相符。200、403、416、错区间或短体即失败，不自动整文件重下。
5. 追加后对整个文件重新算 SHA 并核哈希期间文件稳定。只有大小与 `675dc486a02ea06ecf8b6ab0cf4ef88c92298751b2daacf9f65c59871fcb7fe4` 同时匹配才在新目录生成 `vmem_weights.pth`。不覆盖 canonical 模型路径。若片段已是全尺寸，则先只做本地全 SHA 核验，不花网络。

新执行总时限包括复制、元数据、传输和最终 SHA，使用单进程真实计时和 SIGALRM。失败保留 `candidate.unverified.part` 及回执；不凭新尾部成功掩盖旧前缀损坏，SHA 失败后单纯再补相同尾部不会解决问题。所有异常只记录类型/内部代码，不记录外部异常正文、认证头或带签名 query 的 URL。

## 未来命令，不是本轮执行记录

须先完成其他作者静态审查，并等 attempt3 实际终态。目录必须尚不存在：

```sh
'/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S39_auth_recovery/cli-env/bin/python' \
  '/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S39_auth_recovery/partial_recovery/recover_partial.py' \
  --execute --seconds 1800 \
  --output '/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/data/vmem_recovery/attempt3_range_candidate_01'
```

脚本 SHA：`c796752d5ce8fec6b08491cc52d91e5c04d75e7c7dfcd3bbc51fe6f1dd6800e3`。本轮仅 AST 解析通过，没有 import、人工运行测试、认证请求、Range 请求或大载荷下载。此方案是可审查的条件性资源恢复方法，不是已证可用通路；前次 httpx/curl 新连接 TLS 失败仍然构成现实不确定性。成功与否只能由后续真实请求和完整 SHA 决定。
