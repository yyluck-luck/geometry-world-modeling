# VMem 官方资源入口复核

**本轮没有发现新增、由作者明确提供且可核身份的公开替代权重入口。** 当前成功读取的官方 README 和项目页没有链接 ModelScope、Google Drive 或其他网盘权重；Hugging Face 公开元数据仍指向同一份受限主权重。本轮没有访问模型载荷端点、下载权重、登录或提交资料。

直接 HTTP 查验区间：2026-09-06 14:47:48–14:48:33 UTC（北京时间 22:47:48–22:48:33）。报告实际写入时间见 receipt.json。每个直接 URL 只请求一次，限制响应最多 1 MiB，不跟随重定向、不加载页面图片/视频/脚本。7 次直接 GET 中 3 次成功，4 次因 TLS EOF 未获得 HTTP 状态；另有 1 次 Web 搜索（3 个查询）和 1 次 Releases 页面读取。

## 成功核实的来源

| 来源 | 本轮证据 | 对入口的判断 |
|---|---|---|
| [作者当前 README](https://github.com/runjiali-rl/vmem#readme)／[README API](https://api.github.com/repos/runjiali-rl/vmem/readme?ref=main) | HTTP 200。Git blob `637d70af6b7243a4573da7c05d1a3ad3fdc09059`；解码后 3,233 B，SHA-256 `43024fe529340c4c0ff938c38cc99027b82eb0b56653f2baa0406092231850ba`。与本地固定 commit `39291e4f272f6b4f270691d930926ab5930f942e` 的 README 逐字节相同。 | 仍说明先完成 HF 身份认证、再填写访问信息。权重链接仍为 `liguang0115/vmem`，没有新增替代主权重或 VAE 链接。 |
| [作者项目页](https://v-mem.github.io/) | HTTP 200，25,101 B，SHA-256 `2f9c318c93e13330c867e12a57076c75cb6b5ada81287119c1a10884677b9d30`。提取并检查全部 href 与绝对链接。 | 页面仍指向作者 GitHub 和既有 HF Space，没有新的 ModelScope／Drive 权重入口。展示视频和在线 demo 均不是可下载权重证据。 |
| [作者模型公开元数据](https://huggingface.co/api/models/liguang0115/vmem?blobs=true) | HTTP 200，931 B，响应 SHA-256 `bf140f67d04f89fa0305e4608813380c0dd0b210bbe7d7140edaa83ce48761dd`；`gated=auto`、`private=false`。 | 元数据公开不等于模型载荷匿名可取。模型 revision、大小和 LFS SHA 与 S17 记录相同，没有新增文件或替代载荷。 |

原主生成权重的身份本轮经公开 API 再核：

| 字段 | 当前发布元数据 |
|---|---|
| 仓库／文件 | `liguang0115/vmem`／`vmem_weights.pth` |
| revision | `ac5921080a57f5a634f4b9acbbc8f3db67c9d113` |
| 对象大小 | `5,056,346,672 B` |
| 发布 LFS SHA-256 | `675dc486a02ea06ecf8b6ab0cf4ef88c92298751b2daacf9f65c59871fcb7fe4` |
| 访问条件 | `gated=auto`；本轮未请求权重文件 |

该 SHA 是发布者 LFS 元数据，**不是本轮下载文件后计算的 SHA**。以上三个小页面的响应 SHA 则是本机对实际接收字节计算所得。

## 未成功或时效有限的来源

以下各请求只尝试一次，均保留 TLS `UNEXPECTED_EOF_WHILE_READING`，不把连接错误解释成删除、权限变化或没有替代资源：

- [GitHub main commit API](https://api.github.com/repos/runjiali-rl/vmem/commits/main)：本轮没有重新核实整个远端 main 的 commit；只有当前 README 的成功逐字节核对。
- [GitHub Releases API](https://api.github.com/repos/runjiali-rl/vmem/releases?per_page=100)：本轮 live API 未得结果。随后一次 [Releases 网页](https://github.com/runjiali-rl/vmem/releases) 读取显示没有 release，但工具标为四天前抓取；不能用缓存保证这四天内没有新增。
- [HF 模型页](https://huggingface.co/liguang0115/vmem) 与 [该模型卡的公开 README 文本入口](https://huggingface.co/liguang0115/vmem/raw/main/README.md)：本轮直接 HTTP 均未成功。Web 搜索返回模型卡及原访问条件，但标为上月抓取，只作辅助证据。

限定于上述作者来源的搜索没有给出可用新入口。搜索还返回无关仓库和第三方页面，这些没有被当成作者授权资源。API 自动列出的使用该模型的其他 Space，也不自动构成作者提供的公开权重镜像。

## 与已有记录的关系

已先读 S17 可行性报告及增补、S23 访问回执，避免重复。原主权重匿名 401、原 VAE 入口匿名 401 属于此前证据；本轮没有重请求它们，也没有再调用 token=True 或读取本地 token。原 VAE 的当前可用性和完整对象身份没有新证据。当前资料没有提供可替代原 VAE 的作者入口，不能把其他 VAE 或其他生成器称作原始 VMem 复现。

S17 增补已经确认 CPU 原生 FLASH 的小型数值检查；本轮没有重复依赖安装、算子测试或模型前向。现有 CUT3R 组件成功和本次公开元数据访问，均不等于完整视频生成成功。

**本次有界入口复核到此结束。** 没有新资源可供下载；由于部分最新页面连接失败和 Web 缓存限制，也不声称穷尽所有官方渠道或永久不可用。不将资源缺项扩写成整个研究项目被阻断，不更改主账或总目标状态。

全部请求时间、失败、页面快照、输入/输出身份见 [receipt.json](receipt.json)、[http_observations.json](http_observations.json)、[web_observations.json](web_observations.json)。
