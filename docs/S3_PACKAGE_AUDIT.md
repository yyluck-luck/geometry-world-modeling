# S3 复现包独立离线核验

记录：2026-09-05 23:16:18 Asia/Shanghai（15:16:18 UTC，实际时钟）。本次仅核验 `outputs/科研复现包_S3.zip` 的固定快照，不代表之后生成的 S4/S5 包已经通过。独立任务只新增本审查文档，没有改动主项目源码、原始数据、模型权重或实验结果。

## 结论

**包内 S0–S3 代码及已保存结果可以在指定现有环境离线检查：51 项单元测试、4,444 项保存结果验证通过；重新生成的五份分析 CSV 与包内版本逐字节相同。** 但旧包的英文报告含 27 个指回原电脑绝对路径的链接，报告浏览不具备完整可移植性，需修正打包副本后用新文件名发布。

原始 TUM 图像/归档、CUT3R 权重及官方完整源码 checkout 不在包内，对应数据真实性复查、真实数据重跑及模型推理均为 **SKIP**，不是通过。未创建新环境或离线安装依赖；使用用户指定的主项目现有 `.venv/bin/python`。

## 固定归档与独立解压

- ZIP：`/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/科研复现包_S3.zip`。
- 大小：17,604,887 字节。
- SHA256：`e116a4fda54637524e33c28d762715a8fdaf0e4c20fcbf093adcd550c276db60`。
- 包内 manifest 创建时间：2026-09-05 15:10:11.362337 UTC。
- 安全检查与解压：15:13:28.965644–15:13:29.107843 UTC。
- 独立核验目录：`/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/s3_package_audit_20260905T151328Z/`，其中的 `geometry-world-modeling/` 为解压项目。

430 个归档成员全部 CRC 通过，没有越出新目录的成员路径或符号链接。`PACKAGE_MANIFEST.json` 的 429 条文件记录全部匹配实际大小和 SHA256，没有缺失、哈希错误或未登记的额外文件。此检查在执行任何包内脚本之前完成。

原验证器会写入指定实验目录的 `verification.json`。本任务只在解压副本执行，并先把包内旧验证记录保存为核验目录的 `original_packaged_verification.json`。主项目的原验证记录保持不动；其余分析新输出放在核验目录 `regenerated_analysis/`，未覆盖包内旧图表。

## 实际执行结果

所有命令的工作目录均为新的解压项目，使用解释器 `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/.venv/bin/python`，移除外部 `PYTHONPATH`，没有调用下载脚本或网络工具。

| 检查 | UTC 时间 | 结果 |
|---|---|---|
| `-m unittest discover -s tests -v` | 15:14:27.847914–15:14:29.582009 | 51 项通过，退出码 0 |
| `scripts/validate_rgbd_outputs.py`，不提供 `--data` | 15:14:27.853279–15:14:31.064507 | 4,444 项通过，0 错误，退出码 0 |
| `scripts/analyze_rgbd_experiment.py`，新分析目录 | 15:16:04.395082–15:16:05.606126 | 分析完成，退出码 0 |
| 六个 S0–S3 入口的 `--help` 导入检查 | 完成于 15:16:06.081717 | 六项均退出码 0、无 stderr |

离线验证重算了全部 18 案例、72 个配对查询条件和 144 个查询条件×宽度记录，并核对 S2/S3 各 44 个运行时源码归档文件、24 帧 QA 记录、选择清单和保存深度统计。它明确输出 `raw_data_verification.status="not_requested"`，其通过只表示保存证据内部一致。本报告将原始数据核验归类为 SKIP。不能把这次 4,444 项写成原先含数据检查的 4,544 项全验证，也不能算新增研究样本。

分析从解压包内记录重新生成 3 幅 PNG、3 份 PDF、5 份 CSV、汇总 JSON 与说明。五份 CSV：`query_geometry.csv`、`query_retrieval.csv`、`query_resolution_stability.csv`、`case_summary.csv`、`split_summary.csv` 均与包内原版本逐字节一致。本轮确认图表资源可生成，没有重复进行视觉内容审稿。

六个入口为 `run_memory_pilot.py`、`run_retrieval_pilot.py`、`run_rgbd_qa.py`、`run_rgbd_experiment.py`、`analyze_rgbd_experiment.py` 和 `validate_rgbd_outputs.py`。对应配置、固定 VMem 快照与许可证在包内，相关源码/AST 测试通过。`--help` 能运行不等于重新完成真实数据实验；本轮未重跑完整 S0/S1 配置或 S2/S3 原图实验。

## 必要修复与外部资源边界

1. **修复打包副本中的报告链接。** 扫描 README 与顶层 docs Markdown 的本地 Markdown 链接，发现 27 个，全部位于 `docs/TECHNICAL_REPORT.md`，全部以 `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/` 开头，包含三张图、协议、结果、代码和 README。虽然在原电脑上目标可能存在，它们都越出解压快照；新机器会断链，本机也会跳回主项目。应只在构包 payload 内把项目内 Markdown 目标转成相对当前文档的路径，再生成内容 manifest。不要全局改写历史 JSON 中的绝对路径，它们是来源与执行位置的记录。主任务已收到此项并计划在新包修复，本审查不提前宣称新包通过。

2. **明确 CUT3R 不是包内完整离线运行资源。** 官方 checkout 位于原工作区 `work/cut3r-local`，不包含在包内；运行需要另外获取官方源码并 checkout 固定提交 `8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf`、安装独立 CUT3R 依赖、取得原始输入图像和约 2.99 GB 权重。包内准备说明保留来源，但旧 `scripts/run_cut3r_pair.py` 的默认 repo 指向原工作区，且直接读取 `inference_inputs.json` 的历史绝对 `image.path`；仅改 `--repo` 不会迁移图像路径。应给新机器一个明确的设置说明或接收 `--repo`/`--data` 的新入口，用固定文件名与 SHA 重定位输入，保留历史 manifest。`run_cut3r_local.py` 的显式 `--repo`、`--images` 和 `--checkpoint` 可用于此类新入口。

3. **清楚列出本轮未验证项。** 原始 TUM 归档和图像不在包内，因此未重算归档/图像哈希或重新建图；模型检查点和官方 checkout 不在包内，因此未导入完整 CUT3R 或运行模型；虚拟环境和 wheels 不在包内，因此新机器安装及依赖可获得性没有做离线验证。这些缺省不影响本次已保存 S3 证据核查，但必须与“完整端到端复现”区分。

## 审计记录位置

独立核验目录保留：

- `audit_extraction.json`：ZIP 身份、安全解压与真实时间。
- `package_manifest_audit.json`：429 条包内内容哈希结果。
- `tests.log`、`tests_run.json`：完整 51 项测试输出、命令与起止时间。
- `validator.log`、`validator_run.json`：离线 4,444 项验证执行记录。
- `original_packaged_verification.json`：未被本轮覆盖的旧验证记录副本。
- `markdown_links_audit.json`：27 个不可移植链接的逐项清单。
- `analysis.log`、`analysis_run.json`、`regenerated_analysis/`：新分析输出及 CSV 比较。
- `resources_audit.json`：入口导入结果和明确跳过的外部资源。

本审查证明固定旧包的可检查部分可运行，并指出它的移植限制；不改变 S3 的负结果、原有实验指标或证据边界。
