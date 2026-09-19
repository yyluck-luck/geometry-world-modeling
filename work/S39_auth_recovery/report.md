# S39：正式 HF 认证通道核验

记录 UTC：2026-09-07T03:44:30.594Z；北京时间为 UTC+8。作者 `/root/s14_feature_extractor`。本轮只读本机帮助、版本记录和 3 处 HF 官方文档。

**当前官方 HF CLI 已提供可借已登录网页完成的 device 登录。项目内 0.36.2 的实际帮助没有该新接口，应在隔离的新 CLI 中核实后使用。根任务正在处理这一步；本子任务未安装或登录。**

| 路径 | 已确认的支持 | 本机边界 |
|---|---|---|
| 新版 CLI + 浏览器 device flow | 当前指南显示 `hf auth login` 提供浏览器登录；CLI 给 URL/短码，网页批准后保存授权。agent 示例是 `hf auth login --format agent`。 | 以隔离新版本的实际帮助为准，不把新参数加到旧 CLI。 |
| fine-grained 模型只读 token | 官方文档支持把读取权限限定到一个已获准的 gated 模型；本任务可限定 `liguang0115/vmem`。 | 项目旧 CLI 已确认支持 `--token`，由正规凭据机制提供，不输出原值。 |

来源：[官方 CLI 认证章节](https://huggingface.co/docs/huggingface_hub/en/guides/cli#hf-auth-login)、[官方 User access tokens](https://huggingface.co/docs/hub/en/security-tokens)。这些是方法存在的证据，不是本机认证已成功。

## 本机实际帮助与版本差别

实际执行 `.venv-cut3r/bin/hf auth login --help`，exit 0，返回：

```text
auth login [-h] [--token TOKEN] [--add-to-git-credential]
```

包 METADATA 明确为 `huggingface_hub 0.36.2`。本轮没有假设旧版本支持 `--web`、`--device`、`--format agent` 或新版 `--force`。已读官方认证章节未给 device 登录的最低引入版本，因此记为**未确定**。根任务隔离核新版，项目科学环境保持原版本。

## 两种正规的授权方式

[官方 OAuth 文档](https://huggingface.co/docs/hub/en/oauth) 明确支持 device code：CLI 发起正式服务流程，浏览器输入短码并批准，服务向 CLI 发放授权。它无需读取浏览器 cookie 或私有会话。文档区分 `gated-repos`（已获准的公开 gated 仓库）和 `read-repos`（个人仓库）；当前 CLI 实际申请范围应以其授权页面为准。本轮没有假定 device 授权天然只覆盖一个模型，也未猜 CLI scope 参数。

token 备用流程可按官方设置页的 Access Tokens → New token → fine-grained，限定指定模型读取权限。仅下载不需要 write 或 git credential helper。由官方 CLI/SDK 正常消费合法凭据即可；这里未创建或查看任何 token。[官方模型专用 token 示例](https://huggingface.co/docs/hub/en/security-tokens#best-practices)

## 执行判断

用户已授权原 VMem 访问与必要科研获取。S38 某次“只查文件和帮助，不做账户查询”的子任务范围，不是永久禁止正常认证的规则。官方 CLI 正常使用其保存的合法凭据，以及有必要的账户状态核验，与抽取私有浏览器会话不同。官方指南提供 `hf auth whoami`；本轮未执行它，根任务可在授权恢复流程中使用并只留必要状态。[官方 CLI 账户核验](https://huggingface.co/docs/huggingface_hub/en/guides/cli#hf-auth-whoami)

下一步由根任务核隔离 CLI 的实际帮助，再用正式 device 流程连接已有网页账号。随后是否能访问固定 revision、是否落盘及完整 SHA 都须真实验收。此前 401 没有在本轮重试；当前网页获准事实保持。

## 留痕

实际读取仅上述 3 个文档 URL：第一轮打开三处，第二轮继续读 token/OAuth 正文；共 5 次 open、2 个网页工具调用，没有第四个文档。工具调用 UTC、原始本地帮助及读集在 [receipt.json](receipt.json)。网页工具未暴露原始 HTTP 状态或传输字节，不编造 HTTP 200。

新增登录、账户查询、凭据创建/读取、浏览器操作、OAuth 注册/发起、模型下载、软件安装、科学实验和主账修改均为 0。根任务并行安装/UI 的进度另有回执，不计作本子任务已完成的动作。
