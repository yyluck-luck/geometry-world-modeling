# S编号与具体试验名称审计（2026-09-12）

审计时间：2026-09-12 07:09 UTC。任务来源：用户要求继续科研，并要求说明文档不要只使用“S数字”，而要在括号中给出具体试验名称；编号保留用于追溯。

## 执行结果

我没有改动任何原始科学数值、模型输出、实验回执、JSON协议或索引脚本。此次只更新解释性 Markdown：在首次出现编号的说明文档前加入统一图例，并另外建立可独立阅读的 `EXPERIMENT_NAME_LEGEND.md`。科研项目主记忆、交接文档、S90报告与Agent审查稿，以及用户快照的对应说明文档均已加注。共覆盖 **45 份**说明性文档（科研项目 26 份、用户快照 19 份；下表保留具体路径）。

图例本身位于：

- `work/S90_proxy_resumable_index/EXPERIMENT_NAME_LEGEND.md`
- `outputs/创新候选逐条核验_S90_2026-09-12/EXPERIMENT_NAME_LEGEND.md`

## 统一的具体试验名称

| 编号 | 具体名称（报告中应写在括号里） | 能支持的结论 | 不能误读成 |
|---|---|---|---|
| **S86** | **单场景四目标几何条件注入基线实验** | 在已见静态场景、四个相关目标上比较历史几何注入方式的真实生成链与 RGB MSE。 | 跨场景、动态长期几何或新方法有效性。
| **S87** | **末端引导强度控制与多步引导必要性反例实验** | 在 S86 缓存上比较末端处理强度和持续多步引导，得到该场景的有限反例。 | GRC 实验、几何真值收益或“多步方法普遍无效”。
| **S88** | **RTMV 相机 JSON 元数据与静态投影数据资格检查** | 核对归档身份、相机元数据和可访问静态文件头。 | RGB-D 配对性能实验或已取得可用深度图。
| **S89** | **RTMV 配对数据 TLS 接续失败审查** | 记录两种传输/TLS 接续尝试及失败边界。 | 数据缺失证明或科学负结果。
| **S90** | **RTMV 归档配对数据恢复与索引协议审查** | 检查受限 Range 传输、成员身份、断点恢复和索引安全条件。 | 新模型效果；512B 文件头不等于可读深度正文。

## 写作规则

1. 首次出现时写成 `S86（单场景四目标几何条件注入基线实验）`，后文可以简写 `S86`。
2. S88、S89、S90 是数据资格/传输/协议审查，统一使用“检查”“审查”“接续”，避免把它们写成模型性能实验。
3. S87 的“反例”只针对当前已见场景和当前 RGB MSE 观测；报告必须保留目标22变差和重影仍在的限制。
4. 具体名称是解释性标签，不是新的科学结论；不得因为改名而提高创新性或完成度。
5. 后续新增试验应同时给出编号、具体名称、输入、主要指标、失败判据和限制，避免出现只有编号、读者无法判断性质的描述。

## 已更新的说明文档清单

下表最后五列依次为 S86/S87/S88/S89/S90 在该文件中的出现次数。出现次数仅用于审计，不代表试验重复次数或有效样本量。

| 范围 | 文件 | S86/S87/S88/S89/S90出现次数 |
|---|---|---:|
| 科研项目 | `RESEARCH_MEMORY.md` | 21/17/10/10/14 |
| 科研项目 | `docs/RESEARCH_HANDOFF_CURRENT.md` | 20/16/10/10/8 |
| 科研项目 | `work/S90_proxy_resumable_index/DIALOGUE_CLAIM_AUDIT.md` | 6/6/3/2/7 |
| 科研项目 | `work/S90_proxy_resumable_index/DSH_GRC_REVIEW_PROMPT.md` | 4/2/2/1/5 |
| 科研项目 | `work/S90_proxy_resumable_index/REPORT_PROGRESS_UPDATE_20260912.md` | 5/2/3/1/6 |
| 科研项目 | `work/S90_proxy_resumable_index/ROOT_PROBE_SELF_REVIEW.md` | 4/1/2/2/3 |
| 科研项目 | `work/S90_proxy_resumable_index/SCOPE.md` | 4/1/2/3/5 |
| 科研项目 | `work/S90_proxy_resumable_index/YESTERDAY_HYPOTHESES_AND_INNOVATION_UPDATE_20260912.md` | 4/1/2/1/4 |
| 科研项目 | `work/S90_proxy_resumable_index/agents/advisor_oral_brief_20260912.md` | 7/5/2/1/7 |
| 科研项目 | `work/S90_proxy_resumable_index/agents/crc_and_causal_conditions_addendum.md` | 4/1/2/1/4 |
| 科研项目 | `work/S90_proxy_resumable_index/agents/gate0_contract_review_20260912.md` | 5/2/2/1/8 |
| 科研项目 | `work/S90_proxy_resumable_index/agents/grc_architecture_review.md` | 8/4/2/1/4 |
| 科研项目 | `work/S90_proxy_resumable_index/agents/grc_real_experiment_freeze_checklist.md` | 4/2/2/1/4 |
| 科研项目 | `work/S90_proxy_resumable_index/agents/handoff_consistency_audit_20260912.md` | 4/1/2/2/17 |
| 科研项目 | `work/S90_proxy_resumable_index/agents/index_chain_review_round3_20260912.md` | 4/1/7/8/7 |
| 科研项目 | `work/S90_proxy_resumable_index/agents/index_protocol_review.md` | 4/1/6/8/10 |
| 科研项目 | `work/S90_proxy_resumable_index/agents/index_protocol_review_round2.md` | 4/1/2/2/5 |
| 科研项目 | `work/S90_proxy_resumable_index/agents/innovation_next_gate_20260912.md` | 7/4/2/1/3 |
| 科研项目 | `work/S90_proxy_resumable_index/agents/math_audit.md` | 4/4/2/1/11 |
| 科研项目 | `work/S90_proxy_resumable_index/agents/math_test_reproduction.md` | 4/1/2/1/4 |
| 科研项目 | `work/S90_proxy_resumable_index/agents/pasted_text_fact_check.md` | 5/3/3/2/3 |
| 科研项目 | `work/S90_proxy_resumable_index/agents/prior_code_audit.md` | 4/1/2/1/4 |
| 科研项目 | `work/S90_proxy_resumable_index/agents/reviewer_verdict.md` | 11/8/2/1/8 |
| 科研项目 | `work/S90_proxy_resumable_index/agents/threshold_consumer_loss_crc_review.md` | 4/1/2/1/4 |
| 科研项目 | `work/S90_proxy_resumable_index/agents/yesterday_hypotheses_matrix_20260912.md` | 4/2/2/1/3 |
| 科研项目 | `work/S90_proxy_resumable_index/agents/yesterday_progress_audit_20260912.md` | 5/7/3/1/12 |
| 用户快照 | `DIALOGUE_CLAIM_AUDIT.md` | 6/6/3/2/7 |
| 用户快照 | `README.md` | 4/2/2/1/3 |
| 用户快照 | `REPORT_PROGRESS_UPDATE_20260912.md` | 5/2/3/1/6 |
| 用户快照 | `YESTERDAY_HYPOTHESES_AND_INNOVATION_UPDATE_20260912.md` | 4/1/2/1/4 |
| 用户快照 | `agents/advisor_oral_brief_20260912.md` | 7/5/2/1/7 |
| 用户快照 | `agents/crc_and_causal_conditions_addendum.md` | 4/1/2/1/4 |
| 用户快照 | `agents/grc_architecture_review.md` | 8/4/2/1/4 |
| 用户快照 | `agents/grc_real_experiment_freeze_checklist.md` | 4/2/2/1/4 |
| 用户快照 | `agents/index_protocol_review.md` | 4/1/6/8/10 |
| 用户快照 | `agents/math_audit.md` | 4/4/2/1/11 |
| 用户快照 | `agents/math_test_reproduction.md` | 4/1/2/1/4 |
| 用户快照 | `agents/pasted_text_fact_check.md` | 5/3/3/2/3 |
| 用户快照 | `agents/prior_code_audit.md` | 4/1/2/1/4 |
| 用户快照 | `agents/reviewer_verdict.md` | 11/8/2/1/8 |
| 用户快照 | `agents/threshold_consumer_loss_crc_review.md` | 4/1/2/1/4 |
| 用户快照 | `agents/yesterday_hypotheses_matrix_20260912.md` | 4/2/2/1/3 |
| 用户快照 | `agents/yesterday_progress_audit_20260912.md` | 5/7/3/1/12 |
| 用户快照 | `project_evidence/RESEARCH_MEMORY.md` | 20/16/10/10/8 |
| 用户快照 | `project_evidence/docs/RESEARCH_HANDOFF_CURRENT.md` | 20/16/10/10/8 |

## 未改动范围

没有批量改写 S86/S87 原始结果目录、tar 传输回执、JSON 合同、Python 实验/索引脚本、二进制数组、PDF 或截图。它们仍保留原编号和原始内容；需要向新读者解释时，应从本审计报告或统一图例进入。若以后直接把某个原始结果文件交给老师，建议在其上层 README 引用本图例，而不是改写科学回执。

## 验证

- 用 `rg` 扫描目标项目主记忆、当前交接、S90说明目录和用户快照，确认包含 S86–S90 的说明文档都已包含 `EXPERIMENT_NAME_LEGEND_20260912_BEGIN` 标记。
- 重新读取统一图例，确认五个编号均有唯一具体名称，且 S88–S90明确标为数据/协议工作。
- 未运行模型、未下载新数据、未更改科学数值；本次产物是文档可读性和交接准确性更新，不是新实验结果。
