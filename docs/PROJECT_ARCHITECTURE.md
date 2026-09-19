# Geometry-aware World Modeling：科研项目文件架构

> **实验编号说明（给新读者）**：本文保留项目内部编号以便追溯；首次出现时应写成“编号（具体试验名称）”。统一名称见 [`work/S90_proxy_resumable_index/EXPERIMENT_NAME_LEGEND.md`](../work/S90_proxy_resumable_index/EXPERIMENT_NAME_LEGEND.md)：S86（单场景四目标几何条件注入基线实验）、S87（末端引导强度控制与多步引导必要性反例实验）、S88（RTMV相机JSON元数据与静态投影数据资格检查）、S89（RTMV配对数据TLS接续失败审查）、S90（RTMV归档配对数据恢复与索引协议审查）。S88–S90是数据资格、传输和协议审查，不是模型性能实验；编号也不表示实验成功。


本项目按“来源—代码—实验—结果—审查—报告—交付”分层。原始文件保留，实验结果不可覆盖。

## 目录职责

- proposal/：原始 proposal、研究问题、计划与版本说明（proposal 原件只读）。
- src/：可复用源码、实验脚本与评分器。
- configs/：环境、模型、数据和实验配置。
- data/：原始数据、缓存和经过说明的派生数据；每个数据集需有来源与许可记录。
- results/：按实验批次保存原始输出、日志、指标和可复算文件。
- docs/：交接、研究原则、研究日志、方法说明、文献与审查记录。
- reports/：阶段报告、论文草稿和图表源文件。
- figures/：可复用图形及其生成脚本。
- deliverables/：导师汇报、连续阅读版和最终交付清单。
- vendor/：第三方源码、版本、许可证和 provenance。
- work/：批次级临时工作区与冻结协议；完成后不得删除。
- .venv*：本地环境，不作为科研证据。

## 证据规则

代码可运行、模型可加载、保存数据可读、指标可复算、独立审查通过、端到端科学结论分别记录；任何一项不能替代另一项。每个批次必须关联 protocol、manifest、result receipt 和 review。

## 当前入口

- 最新状态：RESEARCH_HANDOFF_CURRENT.md
- proposal 进度：PROPOSAL_PROGRESS_CURRENT.md
- 研究原则：RESEARCH_PRINCIPLES.md
- 最新批次：S89（见交接文档顶部）

外部用户目录中的报告不移动，交付目录通过清单记录其绝对来源路径与 SHA，避免复制后失去 provenance。
