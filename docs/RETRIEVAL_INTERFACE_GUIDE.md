# 本项目的检索接口与实际使用记录

当前用途是寻找并核实原论文、定位外链正文和保存可复查来源。检索命中、下载成功、全文读完和论文结论可迁移，是四个不同状态。

| 需求 | 优先接口 | 实际情况与边界 |
|---|---|---|
| 找论文和核正式发表状态 | 内置 web 搜索/打开；官方 PMLR、CVF、OpenReview、NeurIPS proceedings | 本轮实际核到两篇 ICML 2025 正式 PMLR 页面与 PDF；agent 记录了精读章节和下载失败 |
| 已知论文题名、作者、arXiv ID/版本 | arXiv 公共 Atom API | 本机小脚本已真实查询成功，保存原 XML 和回执；不用密钥。元数据中的 journal_ref 仍是作者填写，不能代替正式会议信息 |
| Notion 等动态页面和折叠正文 | 官方可访问页面；普通获取只返回壳时，用现有 CUA 浏览器展开并读取 | 先前 HTTP 200 只有网页壳；当前 8 个核心外链可见正文已读。折叠状态快照不当全文 |
| 请另一模型反驳想法 | 用户已授权的 Gemini 网页，通过 CUA | 本轮实际选择 3.1 Pro / Extended 并取得原答；原答另存，引用和数学仍独立核实 |
| 本地已有证据 | 项目论文账、保存 PDF/文本、精确文件搜索 | 先检查旧结论、撤回与已有近邻，避免反复搜同一篇并计作新阅读 |

## 已实际跑通的一次公开查询

工具：`scripts/retrieve_arxiv_metadata.py`，只查询公开元数据。实际在 2026-09-08 14:12:58–14:13:15 UTC（北京时间22:12:58–22:13:15）执行题名检索，HTTP 200，返回 1 条 `History-Guided Video Diffusion`，arXiv `2502.06764v2`。3078字节响应已保存，结果回执见 [实际查询](../work/S54_priority_repository_reading/sources/arxiv_api_history_guidance/receipt.json)。arXiv 年份是预印本信息；正式 ICML 2025 身份另从 [PMLR](https://proceedings.mlr.press/v267/song25b.html) 核实。

以后可使用下面的命令，但输出目录每次必须是新目录，避免覆盖旧证据：

```sh
cd '/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling'
python3 scripts/retrieve_arxiv_metadata.py 'ti:"History-Guided Video Diffusion"' --output work/new_arxiv_query --max-results 3
```

脚本保存 `response.xml` 和 `receipt.json`；出现失败会保存错误及实际时间，不自动循环重试。需要新查询时先查本地结果，按 [arXiv 官方使用说明](https://info.arxiv.org/help/api/user-manual.html) 限速和缓存；这不是多线程爬虫。HTTP 成功而零条结果也明确记录，不能补造论文。

## 本地 Claude 检索技能如何使用

已读取 `/Users/rocket/.claude/skills/sci-research-lookup/SKILL.md` 与 `/Users/rocket/.claude/skills/sci-exa-search/SKILL.md`，采用“先选合适接口、优先原始来源、保存检索结果与失败”的做法。当前检查未发现 Parallel/Exa/OpenRouter 凭据或对应已配置入口，因此本轮没有冒称使用这些付费服务；也没有为用技能而安装、购买或调用 Claude。内置检索、公共 API 和可见浏览器是已实际可用的路线。

Gemini 的 Google One 网页访问与绘图仓库内第三方图片 API 是不同服务。本轮只使用已授权网页，不把网页登录视为获得该仓库 API 的权限或额度。

## 每条文献的最低记录

记题名、作者、正式 venue/年份及来源 URL、预印本版本、检索时间、实际阅读章节、原文支持的结论、迁移到本项目还欠哪些假设。保存原文与失败请求；不把 AI 回答当论文证据，不把附近工作检索未命中当原创性证明。
