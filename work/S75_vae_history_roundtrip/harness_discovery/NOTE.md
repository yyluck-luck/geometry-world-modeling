# 本地 harness 能力检查

实际检查区间UTC：2026-09-09T08:28:28.527823+00:00 至 2026-09-09T08:29:51.438555+00:00。这是只读工具/技能发现，不是新实验，未安装软件、运行模型或更改基础设施。

**建议把“harness”理解为负责组织、限制、记录和核验实验的一套执行工具。用户没有指定某个同名产品。当前项目已有可用的实验harness，优先使用现有组成，暂不新增框架。**

## 发现与边界

| 位置/对象 | 实际发现 | 可用性判断 |
|---|---|---|
| 当前可调用工具名称/描述 | `ALL_TOOLS` 搜索harness无匹配 | 没有可直接调用的同名工具；不能据此声称全机不存在。 |
| `/Users/rocket/.codex/skills` 与 `/Users/rocket/.claude/skills` | 文件名和SKILL.md限定搜索。harness出现于paper-writer、skill-creator的普通用语，以及PPT技能历史示例路径。 | 这些不是新安装的实验执行器。 |
| `/Users/rocket/.claude/skills/swarm-orchestration/SKILL.md` | 已全文读取。技能给出agentic-flow多agent协调，要求agentic-flow v1.5.11+、Node18+。 | 当前PATH未找到 `agentic-flow`；没有执行技能中的npx，避免擅自下载/启动另一个模型工作流。技能文件存在不等于依赖已安装或能力已验证。 |
| `/Users/rocket/.claude/skills/_lionelsimai-collection-source/skills/ai-experiment-tracker/SKILL.md` | 已全文读取，frontmatter version1.0；内容为需求、分析、草稿、复核通用模板。 | 无具体runner、监控、存储或API实现，不能称现成跟踪系统。 |
| 项目 `.venv-cut3r` + S20/S17C overlays 包元数据 | 限定名称harness/lm-eval/inspect-ai/hydra/mlflow/wandb/sacred/ray/optuna/pytest，未命中。 | 只是该解释器及两个overlay范围，不是全机包审计。未导入科学模型包或读凭据。 |
| 常见global Node目录 | `/usr/local/lib/node_modules`存在，直接条目为openclaw/corepack/npm；另外两处预定目录不存在。 | 未发现直接同名harness/agentic/eval条目；没有深入无关openclaw配置或启动它。 |

## 当前项目可直接用的执行组成

`work/S75_vae_history_roundtrip/observe_decode.py` 是实际可运行的本地实验观察器：先检查root独立源审及精确文件SHA，只允许新建执行目录，用项目venv启动；记录实际PID/argv/时间、stdout/stderr/退出码，每0.5秒检查存活进程树RSS，超过180秒或采样RSS阈值终止进程组；通过既有research_log追加主账。**采样RSS不是瞬时硬内存保证**，任何描述应保留该限制。

本次只读其源码与external回执标量字段：S75外部回执记录2026-09-09T08:17:14.953014Z启动，17.499437167018186秒、return0。这里仅核实执行器已有真实使用证据，不替root验收科学结果。

冻结 `CONTRACT.json` 与 `ROOT_SOURCE_REVIEW.json` 给出数据/算法/版本/预算约束；worker保留逐项输入与输出SHA、实际decode进度和所有逐图结果。S70的 `verify_generation.py` 第288–320行给出精确重放、原始数组差别、实际50步进度、readonly产物的独立检查，是已存在的验证harness部件。没有为此次工具发现重新执行它。

S75目前发现 `independent_review_01/BINDING.json`，没有据文件名推断完整复核已完成。初次假设目录 `independent_result_01/*.py` 的读取因无匹配失败，随后文件清单定位到真实目录；此失败不属于实验失败。

## 如何辅助本轮

继续用现有观察器执行有界实际实验，用不同作者验证保存量，用专职检索agent寻找能改变下一实验决策的近邻/反例。这些组件已经覆盖当前最重要的harness需求：固定任务、控制执行、监视资源、保存全部结果、验证与交接。后续只有明确缺失（例如大量任务队列、跨机器恢复）才值得比较新框架。本次没有建立自动恢复/重试或新调度器，也不把基础设施本身算作算法创新。
