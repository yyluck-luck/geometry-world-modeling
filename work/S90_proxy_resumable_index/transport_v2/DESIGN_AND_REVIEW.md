# S90 transport_v2：302重定向最小安全补丁

时间：2026-09-12（Asia/Shanghai）。本目录是独立运行目录，原 `index_01` 不修改。

## 触发问题

S90 `index_01` 在偏移 `12605440` 使用一次 512 字节 Range 时收到 HTTP 302。代理返回的重定向说明正文标记为 1034 字节，`curl --max-filesize 512` 在跟随重定向前停止，结果为 `curl 56`、0 正文、0 新头。不能通过放大上限或下载归档来绕过这个边界。

## 最小方案

1. 对冻结 Hugging Face canonical URL 发一个 `HEAD` 请求，关闭自动跟随（`--max-redirs 0`、没有 `-L`），只保留响应头中的 `Location`，并要求 HEAD 没有正文。
2. 解析 `Location` 为 HTTPS URL；最终 host 必须在原计划 allowlist，且必须与起始 host 不同。查询参数只用于请求，不写入明文回执。
3. 对解析后的同一个最终 URL直接发一条 512 字节 Range（`bytes=offset-offset+511`），不再让 curl 自动跟随重定向；TLS 校验仍要求为 0，最终有效 host 必须等于 Location 的 host。
4. 保持原计划的代理、连接/请求时间、单次/总头部预算、无重试、`--max-filesize 512`、tar-header-only payload policy。任何非 302/非 206、host变化、TLS失败、Range不精确、正文非512字节或重复成员都会停止并留下结构化失败回执。

该过程最多可能取得一个 512 字节 tar header；不会请求 JSON、RGB、depth 正文，也不会运行模型。它不改变 Gate0 资格和科学结论。

## 离线审查

`python3 -m py_compile transport_v2/index_rtmv_transport_v2.py transport_v2/test_transport_v2.py` 通过；`python3 transport_v2/test_transport_v2.py` 输出 `S90_TRANSPORT_V2_OFFLINE_PASS`。fixture 检查了：

- 两阶段调用确实是 HEAD + 直接最终 host，均没有 `-L`；第二阶段仅有 512 字节 Range。
- 解析的最终 host 必须与直接请求的有效 host一致，TLS/HTTP/Content-Range/正文大小检查仍在。
- HEAD 若意外产生正文会拒绝，不把重定向正文当作 tar header。

网络执行前的剩余事实：网络代理、CDN签名和服务器是否接受 HEAD 只能由一次有界真实请求确认。若失败，保留 `RECEIPT.json`，不重试盲发、不扩大预算。

补充安全边界：HEAD 探测也设置 `--max-filesize 512`；服务端若错误发送正文，最多留下受限临时片段并立即删除，且不会把它当作归档头。
