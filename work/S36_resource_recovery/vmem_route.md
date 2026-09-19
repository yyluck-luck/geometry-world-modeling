# S36：原 VMem 权重的新增官方路线核查

**本轮未找到新的、可核为原 `675dc486…` 权重且可公开取得的正式下载／迁移路线。** 新查的作者仓库 issue、评论、仓库功能、实时 Releases 页面和 HF 模型社区均没有给出这样的入口。没有重新请求 S34 的六个元数据 URL，也没有探测旧 gated 权重载荷。

直接请求实际时间为 **2026-09-06 23:55:58.938782–23:56:55.844200 UTC**，即北京时间 **2026-09-07 07:55:58–07:56:55**。3 个限定检索查询已用完；另用了 5/6 个小页面／API 请求，全部 HTTP 200。每个直接请求限 20 秒／256 KiB、只试一次、禁止重定向；实际正文共 **275,331 B**，检索工具返回内容与查询信息的保存 JSON 为 **34,320 B**，可计量接收／保存载荷合计 **309,651 B**，低于 2 MiB。未加载网页附件、图片或视频。

## 本次新增原始来源

| 原始来源 | 实际覆盖 | 发现及边界 |
|---|---|---|
| [作者仓库全部状态 issue 列表](https://api.github.com/repos/runjiali-rl/vmem/issues?state=all&per_page=100) | 返回16个 issue＋1个 PR，17项少于单页100上限；逐条读取标题与正文。 | 没有正式权重公开下载／迁移说明。PR 15 是宽高问题，不是模型分发。只覆盖此时公开 API 可见条目，不包括已删除或非公开内容。 |
| [作者仓库 issue comments](https://api.github.com/repos/runjiali-rl/vmem/issues/comments?per_page=100) | 20条评论，等于17项元数据的 comment 数总和；其中11条由仓库 OWNER `runjiali-rl` 发布。 | 全部评论已读；未见指定原权重、ModelScope、Drive 或另一正式载荷入口。社区发帖不自动当作者发布渠道承诺。 |
| [仓库功能元数据](https://api.github.com/repos/runjiali-rl/vmem) | HTTP 200，`has_discussions=false`。 | 该仓库没有启用 GitHub Discussions，无需假称读取了不存在的 discussion 内容。 |
| [当前 Releases 网页](https://github.com/runjiali-rl/vmem/releases) | HTTP 200，正文明确显示没有 release。 | 本次是实际取得页面，补上 S34 Releases API 的 TLS 未决项；不是引用 S25 的四天前 Web 缓存。未发现发布资产或下载说明。 |
| [原 HF 模型社区](https://huggingface.co/api/models/liguang0115/vmem/discussions?p=0) | HTTP 200，`discussions=[]`、`count=0`。 | 原模型社区也没有公开讨论中的迁移说明；此请求不是模型文件获取。 |

3 个搜索查询限定作者 GitHub 的 issues、discussions 和替代入口关键词。工具主要返回已有 README／app 源码与不相关仓库，未提供新路线。不相关结果没有打开；检索缓存的抓取时间不能当实时发布状态。当前 README／项目页的已知链接只从固定源码和 S34 保存证据继承，没有为了再次得到同一答案重复请求。

## 最接近的作者说明仍不解决权重获取

作者在 **2025-07-15** 的 [issue 4 回复](https://github.com/runjiali-rl/vmem/issues/4#issuecomment-3071392338) 解释在线 demo 的预算问题，并提出可以代跑样例。这是历史服务意愿，不是新的公开权重地址，也不能据此假定今天仍提供服务。本任务没有联系作者、发送照片、申请权限或代替用户提交资料。

其余作者回复涉及安装、评估间隔、生成轨迹和尺度等问题，没有给出新载荷。它们不能用来推断主文件已可公开下载；本任务也没有扩展成新的科学实验或创新结论。

## 同一权重与可取得性的判定

本次要找的对象仍是既有基线：`liguang0115/vmem` 的 `vmem_weights.pth`，参考 revision `ac5921080a57f5a634f4b9acbbc8f3db67c9d113`，**5,056,346,672 B**，发布 LFS SHA-256：

`675dc486a02ea06ecf8b6ab0cf4ef88c92298751b2daacf9f65c59871fcb7fe4`

这些是 S34 已核的参考身份，本轮没有重新拉取同一模型 metadata。新来源没有给出候选对象，因此：**新路线的相同权重身份未确证；新路线的载荷可取得性未确证；本机没有通过本任务取得任何模型文件。** 原 `gated=auto` metadata 可见仍不能算载荷可得。没有使用不明镜像或其他权重顶替，也未读取 token、登录或触发账号条件。

此有界路线检索已完成并停止。剩余一个页面额度不为凑数消耗，也不重复成功软件测试。原文件访问条件或原作者正式迁移信息发生实质变化后，才有新的获取依据；当前证据不支持启动原完整生成。父任务并行处理指定 VAE 的身份路线，本报告不替它预写结论，不修改 canonical ledger 或总目标状态。

逐请求时间、HTTP、正文大小／SHA、检索原结果和来源覆盖见 [receipt.json](receipt.json) 与 `vmem/` 下的小型来源快照。失败计数为0，仅对本轮五次直接 HTTP；不将此前 TLS 或401记录抹掉。
