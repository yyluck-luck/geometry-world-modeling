# 交接同步审计：S93 帧探针、S94 评价合同与 S94 3RScan

审计时间：2026-09-12 17:18:56（Asia/Shanghai）  
审计范围：只读比较项目主账与用户快照；未下载数据、未修改实验结果、未提交数据集许可。

## 审计对象

- 主项目：`/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling`
- 用户快照：`/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/创新候选逐条核验_S90_2026-09-12`
- 核对的主账文件：`RESEARCH_MEMORY.md`、`RESEARCH_LOG.md`、`work/S90_proxy_resumable_index/REPORT_PROGRESS_UPDATE_20260912.md`、`work/S90_proxy_resumable_index/EXPERIMENT_NAME_LEGEND.md`
- 核对的本轮证据目录：`work/S93_ALT_TUM01/frame_probe/`、`work/S94_evaluation_contract_review/`、`work/S94_ALT_3RSCAN01/`
- 快照索引：`UPDATE_INDEX_20260912.json`、`SOURCE_MANIFEST.json`

## 结论总览

| 项目 | 主项目证据 | 主账记录 | 用户快照 | 审计结论 |
|---|---|---|---|---|
| S93-FrameProbe（TUM 帧级资格探针） | 已存在，含结果、回执、ffprobe/ffmpeg 日志和验证 JSON | `RESEARCH_MEMORY.md`、`RESEARCH_LOG.md`、进度报告、术语表均已有相应摘要 | 主要文本、PNG、日志和验证脚本已存在；两个大媒体文件被有意排除 | **部分同步；文件本体基本齐，快照索引和主进度报告仍不完整** |
| S94（未来几何风险评价合同审查） | 已存在，含 `EVALUATION_CONTRACT.md/.json`、漏洞修复、离线验证脚本 | `RESEARCH_MEMORY.md`、`RESEARCH_LOG.md`、进度报告、术语表已有摘要 | **未发现任何 S94 evaluation contract 文件** | **主项目已记录；用户快照完全缺失** |
| S94 ALT-3RSCAN-01（3RScan 官方资格门） | 已存在，含协议、结果、Gate0 JSON、3RScan 元数据、ZIP 头尾探针与回执 | **未发现对应的 S94 3RScan 条目** | **未发现任何 S94 3RScan 文件或索引条目** | **尚未同步到主账与快照** |

## 已确认的科学边界

这次审计没有把同步状态当成科学结果。主项目里记录的 S93 结论仍是 `GATE0_NOT_PASSED`：Depth AVI 解码为 8-bit RGB 视频而非可用于几何评分的 16-bit depth，且没有可追溯到 TUM GT 的绝对帧时间；一次负 Range 语法还导致 RGB AVI 完整误下载，该文件只应作为失败审计证据。S94 评价合同是 `PROTOCOL_ONLY / NOT_RUN`，只说明以后如何公平测试，不说明 GRC-Memory 已有效。S94 ALT-3RSCAN-01 是 `CONDITIONAL_CANDIDATE / GATE0_NOT_PASSED`：元数据和归档目录支持继续资格审查，但完整 RGB、16-bit depth、pose、`_info.txt`、许可和帧级同步均未在本机验证，因此不允许启动 S91。

## 详细缺口清单

### A. 主项目主账

1. `RESEARCH_MEMORY.md` 已记录 S93-FrameProbe 和 S94 评价合同，但没有 S94 ALT-3RSCAN-01 的专门条目；需要追加 3RScan 的条件性资格结论、证据路径、许可边界和“正式 Gate0 未通过”。
2. `RESEARCH_LOG.md` 已记录 S93-FrameProbe/S94 评价合同事件，但没有看到 S94 3RScan 资格探针完成事件；需要用真实记录时间追加，不要回写成实验执行时间。
3. `work/S90_proxy_resumable_index/REPORT_PROGRESS_UPDATE_20260912.md` 已写 S93-FrameProbe 和 S94 评价合同，但没有 3RScan 段落；需要补充“优先替代候选但不切换正式实验”的结论。
4. `work/S90_proxy_resumable_index/EXPERIMENT_NAME_LEGEND.md` 已有 S93-FrameProbe 和通用 S94 评价合同条目，但没有具体名称“**S94 ALT-3RSCAN-01（3RScan 官方元数据、最小归档片段与 RGB-D 资格检查）**”；建议新增独立条目，避免用户只看到 S 编号。

### B. 用户快照

1. `S94_ALT_3RSCAN01/` 整个目录缺失。应同步协议、结果、Gate0 JSON、`3RScan.json`、ZIP 头/尾片段、解析脚本和 receipts。不要同步完整 3RScan 压缩包。
2. `S94_evaluation_contract_review/` 整个目录缺失。应同步 Markdown、JSON、验证脚本和漏洞修复说明；可以排除 Python `__pycache__`。
3. S93 帧探针的可复查小文件已在快照，但 `depth_movie_prefix_1MiB.bin` 与 `rgb_movie_full_unintended.bin` 未同步。排除完整误下载媒体是合理的，但快照 README 或索引必须说明这是**有意排除的大文件**，而不是漏拷贝。完整文件仍在主项目，仅用于失败审计。
4. `UPDATE_INDEX_20260912.json` 没有 S93 `frame_probe` 子文件和 S94 两个目录的条目；即使文件已经拷贝，也应更新索引中的相对路径、字节数和 SHA-256，否则接手者无法验证快照是否完整。
5. 快照中的 `REPORT_PROGRESS_UPDATE_20260912.md`、`EXPERIMENT_NAME_LEGEND.md` 和 `RESEARCH_MEMORY.md` 是旧版本：它们没有本轮 S93-FrameProbe/S94 追加内容或至少没有 3RScan 内容。同步文件后必须重新计算索引 SHA，避免“目录已更新但主文仍旧”的混合状态。
6. `SOURCE_MANIFEST.json` 也需要检查是否加入 S94 证据；当前仅从检索结果看不到 S94/3RScan 路径，建议与 `UPDATE_INDEX_20260912.json` 一并重建或明确其覆盖范围。

## 推荐同步顺序（给主 Agent）

1. 先在主项目追加 S94 ALT-3RSCAN-01 的 `RESEARCH_MEMORY.md`、`RESEARCH_LOG.md`、进度报告和实验名称图例；明确其状态仍为 `CONDITIONAL_CANDIDATE_GATE0_NOT_PASSED`。
2. 将 `work/S94_ALT_3RSCAN01/` 和 `work/S94_evaluation_contract_review/` 复制到快照，排除 `__pycache__`，不复制完整数据包。
3. 将 S93 `frame_probe` 的文本、验证 JSON、脚本、日志和小 PNG 保持同步；大媒体文件可以不复制，但在快照 README/索引中标注“主项目保留、快照有意排除”。
4. 同步主账快照后重建 `UPDATE_INDEX_20260912.json` 与 `SOURCE_MANIFEST.json`，逐项保存相对路径、字节数、SHA-256，并运行一个只读存在性/哈希检查。
5. 更新 `RESEARCH_ACCURACY_CURRENT.md` 或交接总览时，只写“资格审查和协议已完成”；不要把 3RScan 元数据、ZIP 中央目录成员数或评价合同写成模型实验、Gate0 通过、方法有效性或新颖性证明。

## 审计判定

`HANDOFF_SYNC_STATUS = INCOMPLETE`。

原因不是科研结果缺失，而是本轮新增的 S94 3RScan 资格证据尚未进入主账和用户快照，S94 评价合同尚未进入用户快照，S93 帧探针的快照索引和报告版本也尚未完全跟上。完成上述同步并通过 SHA/存在性复核后，才能把本轮交接称为完整；在此之前，接手的 AI 可能只看到旧进度，错误地重复 TUM 探针或把 3RScan 误当成已通过 Gate0。

