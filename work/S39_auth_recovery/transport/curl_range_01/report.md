# S39：一次系统 curl 的 HF→签名 CDN 有界探测

实际执行 UTC：2026-09-07T04:13:40.801864+00:00 至 2026-09-07T04:13:41.456307+00:00；报告记录：2026-09-07T04:14:41.071744+00:00。北京时间为 UTC+8。

**结果：第一腿 Hugging Face resolve 入口发生 TLS 连接错误，未取得目标 HTTP 响应和签名 CDN 地址；第二腿未执行。系统 curl 尚不能作为已证成功的原 VMem 下载替代通道。**

## 做了什么

读已有原 VMem attempt1/2 回执和脱敏日志：Xet attempt1 留有12条 TLS handshake EOF；HTTP attempt2 的实际堆栈是 httpx 经代理 start_tls 后的 `SSL UNEXPECTED_EOF_WHILE_READING`。在此基础上更换为现有系统 curl 8.7.1（SecureTransport/LibreSSL3.3.6）作一个小探测，不重发多GB下载。

[源码](probe.py)和[协议](protocol.json)在04:13:16 UTC先保存并绑定SHA，随后只运行一次。官方 SDK1.30.0以offline模式正常消费已授权凭据并生成固定原URL，实际HTTP由curl执行。第一腿HEAD仅发往 `huggingface.co`；只有返回原 revision/SHA/size一致的签名Location，才允许第二腿对官方CDN GET `bytes=0-65535`。签名URL和HF认证头只在内存与curl stdin配置中；CDN不带HF bearer。未保存raw headers、raw stderr、token、用户名或签名query。

两个预定腿都保持正常TLS验证、当前已知进程代理 `http://127.0.0.1:7897`，不自动重定向或重试；curl每腿15秒、外控20秒。Range原定上限65536 B，未启动时实际为0 B。没有改系统代理或科学环境。

## 真实回执

| 项目 | 结果 |
|---|---|
| 实际curl发送尝试 | 1，HF入口HEAD |
| 目标host | huggingface.co |
| curl exit | 35 |
| 净化错误类别 | TLS_CONNECTION_ERROR |
| 目标HTTP状态 | 无，curl http_code=000 |
| 实际耗时 | 0.653901秒 |
| 响应正文 | 0 B |
| 连接过程头状态序列 | [200]，不能作为HF目标HTTP200 |
| ssl_verify_result | 1；在失败握手下不足以断言证书本身有错 |
| 固定revision/LFS/size元数据 | 没有取得；回执的matches=false表示未通过比较，不是证明原件不匹配 |
| 签名CDN地址 | 未取得，未保存 |
| CDN Range | 未执行 |

[真实receipt](receipt.json)保留执行时点和净化字段。发送了认证头不等于服务已验证账户；本次没有HTTP401/403证据。未取得原件身份也不改写已授权的事实。

## 可以和不可以得出的结论

本次确认：在该时点、既有代理和系统curl路径下，HF入口连接未成功；换到curl没有立即解除问题。由于前置入口失败，**签名CDN可达性仍未测到**。这不是CDN失败证据，也不能从一次失败判定整个网络不可用或账号失效。与之前不同时间的SDK/Xet结果不能形成严格的TLS后端因果对照。

按照预先门槛直接收口，没有补发同一次请求，没有轮换更多客户端，没有禁用TLS。根任务继续处理真实资源状态；本子任务没有观察、停止或更改CLIP/VAE下载，也没有干预原VMem失败目录。模型加载、推理、科学实验、浏览器操作、多GB下载均为0。

源码和协议是执行前保存的实际文件，不是事后转录；只新增本目录产物，旧attempt1/2日志与之前VAE探测均保持。
