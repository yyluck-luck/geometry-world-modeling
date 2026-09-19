# S41 VMem HTTP Range 恢复失败独立诊断

审查完成时间：2026-09-07T05:25:39+00:00（Asia/Shanghai：2026-09-07T13:25:39+08:00）

## 结论

本次 HTTP Range 恢复失败在 **CDN 连接建立层**，不是身份核验、Range 状态检查、正文传输、文件拼接或完整 SHA 校验层。官方 SDK 已成功取得固定 revision 的元数据，并核对 commit、文件大小和 LFS SHA；随后独立 HTTP 客户端尝试连接 `us.aws.cdn.hf.co`，在收到任何 HTTP 状态之前抛出 `ConnectError`，接收字节为 0。

现有证据不能把这个 `ConnectError` 再精确归因到 DNS、代理 CONNECT、TCP 还是 TLS 子层，因为执行器有意没有保存第三方异常详情。本项目较早的 Xet 和 curl 回执分别记录过 `tls handshake eof` 与 curl 35，这使“当前代理/网络到 HF 存储端的 TLS 路径不稳定”成为较强解释，但仍是跨回执推断，不能改写成本次异常的直接实证。

**不建议立即用相同的 CDN Range 方法再试。** 原因有两个：同一网络路径已经在多个独立回执中快速失败；而且 Xet 产生的 3.48 GB 文件虽然不是文件系统稀疏文件，仍没有官方前缀哈希或 SDK 语义证明它等于原权重的连续 `[0, 3479430365)` 前缀。当前恢复器的全文件 SHA 门会安全地拒绝错误拼接，但不能让未证明的前缀变成已证明前缀。

下一条最小且不同的合法路径是：**重新运行官方 `huggingface_hub 1.30.0 + hf_xet 1.6.0` 的 Xet 下载到新的临时目标，固定 repo/revision/expected size/expected SHA，单进程、低并发，并把总时限提高到至少 3600 秒，建议 5400 秒；完成后只以 5,056,346,672 bytes 和完整 SHA-256 `675dc486...7fe4` 发布。** Attempt 3 的终止原因是外部 1800 秒预算，不是该回执记录到的传输错误；它在 1800 秒前形成了 3,479,430,365 bytes，按表观速率线性估计完整重建约需 2616 秒。这个估计只用于资源预算，不是成功保证。

## 分层证据

| 层 | 实际证据 | 判定 |
|---|---|---|
| Attempt 3 终态 | 1800.2388 秒达到外部 deadline；发出 SIGTERM；child exit -15；child/group 均不再存活 | **实证：人为预算终止**，不能据此称 Xet 自己失败 |
| 官方身份/认证 | HTTP Range 回执记录 HF `HEAD 302`；随后 `official_metadata_identity_verified=true`；未发生 OAuth refresh | **实证：本次身份与元数据门通过** |
| CDN Range 请求 | 计划字节 `3479430365-5056346671`；host `us.aws.cdn.hf.co`；不发送 Bearer；不跟随 redirect | **实证：请求已进入连接尝试** |
| HTTP 响应 | Range 事件没有 `http_status`；`received_range_bytes=0` | **实证：未取得 HTTP 响应/正文** |
| 异常 | `error_type=ConnectError`；外部异常详情未保存 | **实证：连接建立失败**；DNS/代理/TCP/TLS 四者不能进一步区分 |
| 拼接与完整校验 | 没有追加 Range 字节，没有进入完整文件 SHA 成功门，没有正式输出文件 | **实证：未拼接、未完成、未发布** |

## 保留文件状态

审查时只读重算了两份文件的 SHA-256：

| 文件 | 字节 | inode / link | SHA-256 | 能说明什么 |
|---|---:|---|---|---|
| `data/vmem_recovery/attempt3_live_partial.link` | 3,479,430,365 | inode 261890270，nlink 2 | `211f3b5dc27d1ce9d38567a3d9da46269e7e62471ec26f4e40be6bff9f077e0b` | Attempt 3 保留物当前稳定可读 |
| `data/vmem_recovery/http_recovery_01/candidate.unverified.part` | 3,479,430,365 | inode 261895836，nlink 1 | `211f3b5dc27d1ce9d38567a3d9da46269e7e62471ec26f4e40be6bff9f077e0b` | 恢复候选与当前保留物逐字节一致；本次网络没有追加数据 |

两个文件开头均被本机 `file` 识别为 Zip archive，并有 `PK` local-header magic。它只能证明格式开头像 PyTorch zip 容器，不能证明内容来自目标 revision。

保留物占用块数 6,795,768，约等于其逻辑大小向块边界取整，所以 **没有观察到明显稀疏洞**。这仍不证明 Xet 一定按连续前缀顺序重建，也不提供官方 prefix checksum。两份文件都必须保留 `unverified` 标签，不能传给模型加载器。

原临时路径仍与保留链接共享同一 inode；正式目标 `data/vmem_original/vmem_weights.pth` 不存在。回执还明确记录 `canonical_target_modified=false`、`source_partial_modified=false`。

## 本地缓存判断

隔离 `HF_HOME=/Users/rocket/.cache/huggingface-research-s39` 的 Xet 目录只有日志和空的 `staging/` 目录，整个隔离缓存约 44 KiB；没有观察到可复用的内容寻址数据块。官方包说明 Xet支持 chunk cache，但“能力存在”不等于“本次已缓存”。因此下一次下载不能在计划或进度中声称会复用这 3.48 GB。

安装源码显示 `huggingface_hub` 为每次下载生成新的 UUID `.incomplete` 临时文件，并在普通失败清理中删除；Attempt 3 的文件之所以还在，是提前创建了 hard link 且 SIGTERM 中断了常规清理。新的 `hf download` 不会按当前可见源码自动把这个 hard link 当作续传输入。

## 是否重试同法

### 现在不重试相同 HTTP Range

同法重试只有在以下至少一个外部条件明确改变后才有诊断价值：

1. 使用不同且先经小请求验证的网络/代理路径；或
2. 获得目标对象的权威 prefix checksum，证明 3.48 GB 是连续前缀；或
3. HF 的 CDN 连接状态发生可观测变化。

即使将来满足连接条件，Range 恢复也必须继续要求 `206`、精确 `Content-Range`、identity encoding、精确尾长和最终完整 SHA。不能把 `200` 当兼容回退，也不能在原候选上盲目追加。

### 推荐的下一路径

1. 保留现有两份 3.48 GB 文件与失败回执，只读、不加载。
2. 先做一个新的外控计划和源码审查；不要直接复用 1800 秒脚本。
3. 用官方 SDK/Xet、固定 revision、单文件、单进程、低并发，写入新的唯一目录；建议 5400 秒总时限，至少 3600 秒。
4. 新任务不要宣称 partial/cache reuse；按“可能从零重建”预算磁盘和时间。
5. 成功门只接受精确大小和完整 SHA；失败则保留独立回执及错误类别，不覆盖现有失败。
6. 只有通过成功门后，才把验证文件交给 S39 freeze/load；加载成功仍不等于生成成功。

这条路径与刚失败的“signed CDN URL + 手工 HTTP Range”不同，回到作者仓库的官方 Xet 数据路径。它也比再跑相同 Range 更符合当前实证：Attempt 3 曾持续产生本地数据，而三次普通 HTTP/curl 路径均在连接早期失败。

## 明确区分实证与推断

**实证：** 元数据门通过；Range 收到 0 bytes；异常类型是 `ConnectError`；两份保留文件同大小同 SHA；正式目标不存在；隔离 Xet cache 没有可见 chunk；Attempt 3 因 1800 秒外部 deadline 被 SIGTERM。

**推断：** 当前网络/代理到 HF 存储端的 TLS 路径可能不稳定；Attempt 3 的表观速率若近似保持，完整 Xet 重建约 43.6 分钟；3.48 GB 文件很可能包含有用数据，但是否为权威连续前缀没有证明；5400 秒 Xet 重试更可能越过原 deadline，但不保证成功。

## 审查边界

- 没有发起网络请求或下载。
- 没有读取、打印或复制 credential/token 文件。
- 没有运行任何模型或科研实验。
- 没有修改正式权重、保留 partial、失败回执或主账。
- 只新增本目录内的独立诊断文档与机器可读收据。

