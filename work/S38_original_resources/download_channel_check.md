# S38：原 VMem 下载通道的限定本地排障

记录 UTC：2026-09-07T03:19:24.066Z。作者 `/root/s14_feature_extractor`。本轮只做文件元数据检查、项目记录检索和离线 CLI 帮助查询。

**结论：两轮限定扫描均未发现原 VMem 文件或相关临时文件，没有可观察的增长文件；现有允许证据也未确认可直接使用的已授权 CLI 通道。** 这不等于“整台电脑没有文件”或“所有下载途径均失效”。浏览器页面的实际访问权限已由根任务确认，本轮没有否定它。

## 文件在哪里查、查到了什么

扫描范围仅为：

- `/Users/rocket/Downloads`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling`（包含项目 data 与本机项目环境）
- `/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip`

使用目录遍历和匹配条目的 stat/lstat，不打开候选文件正文，不跟随目录符号链接。匹配规则覆盖 `vmem_weights.pth`、浏览器常见的 `vmem_weights (数字).pth` 及其附加后缀、任意 `.crdownload` 文件、`.download` 目录，以及以已记录原对象 SHA `675dc486a02ea06ecf8b6ab0cf4ef88c92298751b2daacf9f65c59871fcb7fe4` 开头的文件名。后者只按名称找，不把名称当完整内容哈希。

| 根目录 | 第一轮 UTC | 第二轮 UTC | 两轮候选数 |
|---|---|---|---:|
| Downloads | 03:16:46.307666–03:16:46.711997 | 03:18:05.617918–03:18:05.996869 | 0 / 0 |
| 项目 ROOT | 03:16:46.712027–03:16:47.418096 | 03:18:05.996889–03:18:06.299806 | 0 / 0 |
| 当前 WS | 03:16:47.418120–03:16:47.532392 | 03:18:06.299840–03:18:06.416337 | 0 / 0 |

日期均为 2026-09-07；北京时间为 UTC+8，即 11:16:46–11:18:06。两轮开始相隔约 79.31 秒，中间做文档与 CLI 检查，没有阻塞等待。三处扫描均完整结束、没有访问错误或扫描上限截断；不保存不相关文件名。项目文件数从 93,518 增至 93,529，但匹配候选始终为 0；并行研究产物的增加不是 VMem 下载进度。

没有可供逐次比较大小的候选，因此结论是“在范围内未观察到增长的目标文件”，不是确认浏览器完全没有后台网络活动。浏览器私有缓存、沙箱临时区、其他目录和未知临时命名不在本轮范围内。旧 [访问与预下载回执](access_and_pre_download.json) 给出原目标大小 5,056,346,672 B 及上述 SHA；本轮没有目标文件可做完整校验。

## 已有工具和授权通道

PATH 中找到 `/usr/bin/curl`、`/opt/homebrew/bin/wget`、`/usr/local/bin/git`、`/opt/homebrew/bin/python3`；未找到 PATH 可调用的 `hf`、`huggingface-cli` 或 `aria2c`。这只是当前 PATH 结果。

项目 `.venv-cut3r/bin/hf` 和 `.venv-cut3r/bin/huggingface-cli` 实际存在。对前者只执行了：

```text
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 HF_HUB_DISABLE_IMPLICIT_TOKEN=1 PYTHONDONTWRITEBYTECODE=1 .venv-cut3r/bin/hf download --help
```

命令 exit 0，用时约 1.15 秒。其帮助支持指定仓库、单文件、固定 revision、local-dir 和 max-workers，足以承担将来明确路径的下载工作；**没有执行 download，没有调用登录/账户查询，没有查看 token**。保存的原始帮助在配套 receipt 中，不在命令里提供任何凭据。项目既有记录显示 Hugging Face Hub 0.36.2；本轮没有重新导入科学模型或改包。

[旧 S23 访问回执](../S23_generator_access_followup/receipt.json) 于 2026-09-06T14:00:17+00:00 记录 `LocalTokenNotFoundError`，没有 HTTP 请求。这是过去的状态，不是本轮对当前凭据的测量。当前浏览器访问已获准来自根任务的实际页面观察；没有证据能把浏览器会话自动转移给 CLI。本轮不读取 credential 文件、环境中的凭据值、cookie、浏览器配置或私有网络状态，也不通过 `whoami` 探测账户，所以**当前 CLI 授权状态保持未验证**，不谎称它已授权或确认没有凭据。

项目已有下载脚本面向 CUT3R/TUM，已成功使用的公开下载能力不能代替原 VMem 受限对象的当前访问证据。HTTP 客户端的存在同样不补齐授权。没有借助浏览器私有状态提取链接/认证信息，也没有读取 Codex 或 browser-use 内部源码。

## 收口与下一步

根任务报告的浏览器 Download、文档化 downloadMedia 无落盘，以及 Chrome `ERR_CONNECTION_CLOSED`，本轮没有重新执行。已保存的 Download 点击回执只说明动作曾返回，不能据此认定 5 GB 下载开始或完成。

本轮可交接的结果是：**文件落盘尚未被证实；项目 HF CLI 可用，但授权直连仍未证实。** 继续获取应由根任务在既有授权范围内使用平台正式支持的下载或账户流程；只有实际路径出现并且增长/最终大小可观察，才进入下载验收。这里不提出读取凭据或重发大下载的变通办法，也不因为文件缺失重跑旧科学实验。

配套 [receipt](download_channel_check.receipt.json) 保存两轮真实时间、范围、计数、CLI 帮助及读集。新增网络请求、模型载荷下载/读取、数据/GT读取、账号操作、网络修改、软件安装和科学实验均为 0。未改主账、既有协议或之前的 S38 VAE 追溯文件。
