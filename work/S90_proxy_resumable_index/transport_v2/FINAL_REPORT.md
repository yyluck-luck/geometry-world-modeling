# S90 transport_v2 实际执行回执

时间：2026-09-12（Asia/Shanghai）。原 `index_01` 未修改。

## 补丁与审查

新目录使用独立计划和独立输出。补丁先发不跟随跳转的 `HEAD`（`--max-redirs 0`、无 `-L`、`--max-filesize 512`，不保存响应正文），只解析 `Location`；Location 必须是 HTTPS 且 host 在 `huggingface.co`/`us.aws.cdn.hf.co` allowlist，随后对解析出的同一最终 host 直接发一个 `Range: bytes=12605440-12605951`。Range 阶段仍 TLS 校验、无重试、`--max-filesize 512`，只有精确 512B、HTTP 206、精确 Content-Range 才能提交 tar header；HEAD 意外产生正文会被拒绝。原计划连接/请求超时、代理、64/256头预算、300秒墙时限均未扩大。

离线核验：`python3 -m py_compile index_rtmv_transport_v2.py test_transport_v2.py` 与 `python3 test_transport_v2.py` 均通过，输出 `S90_TRANSPORT_V2_OFFLINE_PASS`。

最终代码（含HEAD正文512B上限，未再联网）SHA-256：`5c935082d7b93df76bfe126e76772e4931786e988ff357889d5a5a1f2bd366ee`；index_03实际执行版本SHA-256为 `7e91cd9934ab44f1a190653c6c5965084f0350d4843a921d0d9b633164d166eb`；计划 SHA-256：`fa02e07d97988189b6340d36cb5de7f5fdc440086494444d5116ce6e7a057e52`。

## 两次独立、有界真实尝试

`index_02` 首次仅执行 HEAD 阶段，没有进入 Range：HTTP `302`、TLS verify `0`、curl return `18`、保存正文 `0` 字节；stderr 为 `transfer closed with 1032 bytes remaining to read`。响应头声明重定向说明体 `content-length: 1034`；未解析并使用 Location，也未发归档 Range。

仅在 HEAD 命令加入 `--ignore-content-length` 后，独立 `index_03` 再次尝试：curl return `35`、HTTP code `0`、TLS verify `1`、保存正文 `0` 字节；stderr 为 `LibreSSL SSL_connect: SSL_ERROR_SYSCALL in connection to huggingface.co:443`。仍未得到 Location，未进入 Range。

两个 checkpoint/receipt 均为 `STOPPED_TRANSPORT`，`complete_view_ids=[]`，`image_or_depth_payloads_requested=0`，`json_payloads_requested=0`，`downloaded_header_bytes=0`。没有取得新的 header 或 body，没有 RGB-D 配对，没有通过 Gate0，也没有模型或科学实验运行。

证据：`index_02/RECEIPT.json`、`index_02/CHECKPOINT.json`、`index_03/RECEIPT.json`、`index_03/CHECKPOINT.json`。

后续停止重复请求；等待新的官方可达入口或另一合规数据集。Gate0 仍阻断。
