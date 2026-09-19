# S39：新授权会话下的原 VAE 两次小探测

实际探测 UTC：2026-09-07T03:54:38.297892+00:00 至 2026-09-07T03:54:39.206658+00:00；报告记录 UTC：2026-09-07T03:55:43.342229+00:00。北京时间为 UTC+8。作者 `/root/s14_feature_extractor`。

**结论：官方 SDK 已正常构造认证头，但两次连接均发生 `ConnectError`，未收到 HTTP 响应。此次没有新的 401/403 或权限判决，也未取得原 VAE 配置与权重身份；原来源关系保持 `UNKNOWN`。** 这不能证明原件已不可获取或不存在，不能据此认定应改用替代 VAE。

## 实际请求与结果

使用隔离官方 `huggingface_hub 1.30.0` 的 `build_hf_headers(token=True)` / `get_session()`，按正规流程消费新授权凭据；没有直接打开 credential 文件，也不检查或保存凭据值。根任务报告的 device 登录成功是本次新条件；本子任务没有重复登录或账户查询。

| 对象 | 固定公开来源 | 实际结果 | 耗时 |
|---|---|---|---:|
| 原 `vae/config.json` | [原 repo 固定 raw 配置](https://huggingface.co/stabilityai/stable-diffusion-2-1-base/raw/5ede9e4bf3e3fd1cb0ef2f7a3fff13ee514fdf06/vae/config.json) | `ConnectError`；HTTP状态无；正文0 B | 0.412164秒 |
| 原参数文件/LFS元数据 | [原 repo 固定 revision API](https://huggingface.co/api/models/stabilityai/stable-diffusion-2-1-base/revision/5ede9e4bf3e3fd1cb0ef2f7a3fff13ee514fdf06)，请求参数 `blobs=true` | `ConnectError`；HTTP状态无；正文0 B | 0.479813秒 |

两次都固定 revision `5ede9e4bf3e3fd1cb0ef2f7a3fff13ee514fdf06`。请求钩子记录两次认证头存在；这仅证明发送尝试采用认证，不代表服务器已经收到或验证其权限。连接失败的更底层原因没有在本轮进一步判断，不补写为已确诊 TLS、代理拒绝或 token 失效。

## 严格范围

- 官方 SDK 通过 `HF_HOME=/Users/rocket/.cache/huggingface-research-s39` 正常消费合法凭据；该路径是配置，不是本 agent 手工读取的 credential 内容。
- 仅进程使用根任务已确认的既有代理 `http://127.0.0.1:7897`；没有改系统网络、代理设置或科学环境。
- 两次 GET 发送尝试，无循环重试、无重定向。每次硬期限20秒、响应上限256KiB；实际各不到0.5秒，无响应正文。
- 不调用 `hf_hub_download`，避免额外 HEAD/GET 或权重载荷；元数据 API 即使成功也只选 VAE 文件条目。本次未取到任何条目。
- 错误仅保留异常类、状态和计时，不保存可能带凭据或带查询 URL 的异常文本。无用户名、token、cookie、浏览器信息。

最初在联网前发现旧 `configure_http_backend` 名称不适用于1.30.0，产生一次 ImportError；随后检查新公开 SDK 的 `set_client_factory/get_session` API 并采用它。该准备错误发生时网络尝试为0，不与后续连接失败混淆。

## 对原件和变体分支的影响

此次配置 SHA、原权重 LFS SHA、原 Git blob 和原发布 revision 的服务端核验均未取得；没有把 S38 未认证的旧401当作新授权状态。此前社区/官方 ft-mse 的 `a1d993…` 关系也没有因此接通原 SD2.1 来源。

按既定优先级，若以后取得可信原件，优先恢复原件；当前应保持来源未知并由根任务结合正在进行的官方下载与连接条件作下一步判断。本子任务的两次额度已用完，停止探测，不启动变体、不下载 VAE、不动 S35 gate。模型/科学实验、浏览器操作、额外大下载均为0。

逐项时点、实际请求路径、认证头存在标志与范围见 [JSON回执](original_vae_authenticated_probe.json)。原 VMem 活跃下载由根任务独立管理，本次没有查看或干预其进程。
