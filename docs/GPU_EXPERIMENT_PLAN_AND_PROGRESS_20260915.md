# Geometry-aware World Modeling：S0至今实验总控与 SuperPod GPU计划

更新时间：2026-09-15（记录时间以 `RESEARCH_LOG.md` 和各实验回执为准）

## 先给初学者的结论

本轮新增两条并行路径：Gemini 通过用户已打开的浏览器窗口做独立 Gate0 实现/防泄漏审查；SuperPod 先运行不读数据的模型加载 smoke。Gemini 建议与本项目验证器一致：拆开 pre-run/post-run、明确区分 S103 两种历史含义、把未来数据隔离落实到运行时、并在 dispatch 前对 staged artifact 重新计算 SHA-256。它是外部建议，不是 Gate0 通过证据。

目前不是“所有实验已经完成”，而是**旧批次的基线、失败诊断和资格审查已经有大量实证；真正依赖完整 VMem 神经 forward 的跨场景实验还没有开始**。这次已经验证学校 SuperPod 能分配 NVIDIA H800；正确的 job 584006 还验证了远端 torch 2.5.1+cu121 与 CUDA 矩阵运算。两次更早的 smoke job 因附加 Python 打印引号错误失败，因此它们只保留为失败记录。

正式 GRC-Memory 仍需要独立测试数据。ICL-NUIM `lr0` 已下载（711,444,709 bytes，SHA256 `4eca8c2e9f77c1bd7436c746d22ea6144b8c01fe9bc29a84e734186823f1f1ad`），但在冻结前已经看过部分官方 GT 元数据，因此标为 `development/data-access-held-out candidate`，不能宣称零暴露盲测。包内文本映射子门已通过：RGB/depth/association 为 ID 0–1508，pose 为 ID 1–1508，明确丢弃 association ID 0 后剩余 1508 对一一对应；整体 Gate0 仍因时间语义、单位、内参、坐标约定、split 和 GT 隔离未全部冻结而阻断。

## 原 proposal 的验收链

1. **问题与文献**：长时程相机运动、物体运动、稀疏观察、遮挡和重访导致几何不一致。
2. **强基线**：先复现 VMem/CUT3R 等已有组件，记录输入、权重、时间和失败。
3. **失败分类**：分开深度/姿态漂移、可见性、记忆更新、检索和生成器重影。
4. **方法**：只保留能被强基线推翻的候选，不把普通 gating、confidence、warp 或后处理改名为创新。
5. **评价**：同候选池、同记忆槽位、同 token/显存/forward 预算，跨场景比较 RGB-D、pose、重投影、尾部风险和成本。
6. **交付**：独立复核、失败边界、可复现实验、报告和演示。

## S0至当前的实际实验账本

内部编号保留用于追溯；括号中的名称是给汇报使用的具体试验名。已接受的旧结果不为“看起来完整”而盲目重跑。

| 批次 | 具体试验名称 | 实际状态 | 证据和边界 |
|---|---|---|---|
| S0–S7 | 记忆恢复、固定事件控制、渲染器/保存接口诊断 | 已完成本机实验与复核 | 主要是协议、缓存、组件和合成/局部控制；不等于完整视频或新方法 |
| S8–S20 | TUM/Bonn 数据入口、时间戳/相机/深度资格审计，CUT3R/VMem 接口准备 | 大部分已完成，失败保留 | 多处许可、同步、光学坐标和缺测问题被发现；不能把数据入口当性能结果 |
| S21–S22 | 300 帧 CUT3R/TTT3R/FILT3R 几何轨迹基线 | 已完成 | 位置 RMSE 是已有方法的基线比较；不等于生成世界模型创新 |
| S34–S40 | VMem 权重、依赖和下载恢复 | 已完成若干可复用组件，主权重身份/完整性曾受阻 | 当前仍要在 H800 重新验证实际模型 forward 和权重身份 |
| S48–S70 | 固定历史、相机响应、几何输入、真实 VMem 生成链路 | 已完成多轮真实局部生成/组件计算 | S70 三臂 50 步真实生成保留；原 SD2.1 VAE 身份 UNKNOWN，结果不是外部精确复现 |
| S71–S81 | 生成匹配、错误相机标签、VAE 往返、传感器深度/重投影诊断 | 已完成并独立复核 | 生成图仍有重影；匹配与传感器评分有覆盖/不同步/近似 K 限制 |
| S82–S85 | 历史几何预测、固定相机优化、固定几何投影消费者 | 已完成局部真实/离线组件实验 | 预测拟合或投影一致不等于真实物理几何正确，也不等于生成改善 |
| S86（单场景四目标几何条件注入基线实验） | G0/Gpaste/Gterminal/Gguide 50 步对照 | 已完成 | Gguide RGB MSE 较低但 20–23 仍有重影、涂抹和形状模糊；不能宣称三维精度提升 |
| S87（末端引导强度控制与多步引导必要性反例实验） | 强度 .5/.75/1 与末端控制 | 已完成 | `.75` 的局部反例否定“本例必须多步引导”；不证明 GRC 或泛化 |
| S88（RTMV 相机 JSON 元数据与静态投影数据资格检查） | 官方 JSON/相机字段和静态投影入口审计 | 已完成，非性能实验 | 只取得部分元数据，未取得完整动态序列 |
| S89（RTMV 配对数据 TLS 接续失败审查） | 归档 Range/TLS 接续与失败复核 | 已完成，失败保留 | 没有新 RGB/EXR 正文，不能称为数据实验 |
| S90（RTMV 归档配对数据恢复与索引协议审查） | 归档索引、许可证和配对协议 | 已完成审查 | 仍未形成独立 RGB-D/pose 测试集 |
| S91（正式 GRC-Memory 评估） | 固定预算风险校准记忆选择 | **阻断** | 开发数据来源身份混杂；必须等 Gate0 通过 |
| S92–S98 | 研究交接、数据资格、固定未来窗口、相机/深度配对审计 | 已完成准备与复核 | TUM fr1/fr2 标为 `DEVELOPMENT_SEEN`；窗口可行性不能变成 held-out |
| S99（固定改写预算几何更新对照） | 低不一致度/随机/confidence 的同块更新 | 已完成已见缓存重算 | 低 D 对 confidence 的优势未稳定；停止该主张 |
| S100（固定上下文同幅度成对替换诊断） | 同背景、同候选池的 low-D vs confidence | 已完成已见缓存重算 | 144 次消费者重渲染，平均收益接近 0 且有背景反号；仅为机制线索 |
| S101（学校 GPU 迁移与运行合同） | SSH、Slurm、资源和实验合同 | **准备完成，GPU probe 已实际验证** | `slogin-02`、Slurm 23.02.6、账号 `mscitspod2026`、`normal`；job 584006 在 `dgx-21` 返回 H800 81559 MiB、driver 580.159.03、Python 3.10.21、torch 2.5.1+cu121、CUDA 可用；VMem forward 尚未开始 |
| S103-GeoDiag（历史预测几何扰动分解诊断） | support/identity/context 变化分解 | **本机已完成** | 72 条封存预测记录，H_support/H_depth 未通过，`MECHANISM_UNRESOLVED` |

### H800 环境依赖审计补充

依赖探针 job `584098` 已在 `dgx-09` 的 `normal` 分区以 1 GPU、4 秒、退出码 0 完成。该隔离环境可直接运行 `torch 2.5.1+cu121` 和 `numpy 2.2.6`；`diffusers`、`transformers`、`accelerate`、`opencv-python`、`imageio`、`scipy` 尚未安装。首次探针 `584095` 的括号错误已保留为失败记录。证据：`work/agents/gpu_dependency_probe_20260915.md`。因此下一步是建立可复现的依赖安装/容器方案并重新做 import 回执，仍不读取数据或运行 VMem。

随后对服务器已有环境做了只读复查：Anaconda3 模块下的 `base` 环境（Python 3.11.5）实际可在 H800 计算节点通过 CUDA/PyTorch smoke，并可导入 torch 2.7.0+cu126、transformers 4.48.3、accelerate 1.4.0、scipy 1.11.1、imageio 2.31.1、torchvision 0.22.0+cu126、Pillow 9.4.0 和 cv2 4.11.0；唯一明确缺失的是 `diffusers`。个人 `torch` 环境（Python 3.10.21）则仍缺 scipy、diffusers、transformers、accelerate、cv2、imageio。`geometry` 环境在 conda 清单中存在，但其预期 `bin/python` 路径不存在，不能直接使用。共享 base 与项目精确 pin 仍有 NumPy/SciPy/Pillow 版本差异，因此状态只能记为 `PREPARATION_SMOKE_PASS`，下一步仍需隔离、锁版本并做项目级 import smoke。

## H800 上要执行的正式实验

这些是缺失的 GPU 研究实验，按顺序提交；前一步失败就停止方法主张，但保留失败结果。

| 实验名称 | 做什么 | 关键输出 | 预计 H800 时间 |
|---|---|---|---:|
| S102（未见 RGB-D/相机资格门） | 检查 RGB/depth 一对一、时间/帧身份、K、pose、深度单位、SHA、许可和 GT 隔离 | `GATE0_RESULT.json`、逐帧 manifest | 0.5–1 天 |
| S103-VMemBase（跨场景 VMem 长时程基线复现） | 在冻结场景上真正运行 VMem，记录神经 forward 和长时程输出 | prediction seal、视频、环境和成本回执 | 1–2 天 |
| S104（固定预算记忆强基线比较） | k=2/4/8 下比较 recent、random、pose、coverage、confidence、persistent、utility-only | 同预算选择表、RGB-D/pose/重投影指标 | 1 天 |
| S105（GRC-Memory 风险校准选择） | 只让 selector 读历史几何风险，预测未来 RGB-D/pose 损失 | 风险校准、主指标、置信区间、失败样例 | 1–2 天 |
| S106（遮挡重访压力测试） | 人/物体遮挡后重新出现，测合法前缀、风险和未来恢复 | 重访分层、遮挡长度曲线、尾部错误 | 1 天 |
| S107（源级反事实记忆干预） | 固定噪声和其他条件，只替换/删除一条记忆 | 有符号未来效应、replay-noise 控制 | 1–2 天 |
| S108（尾部风险与支持定位） | worst-5%、CVaR95、重投影和 coverage，定位收益来自何处 | 尾部表、空间热图、支持分母 | 0.5–1 天 |
| S109（多 seed 与资源审计） | 至少 3 个 seed，记录 GPU 显存、I/O、forward、延迟、失败 | 复现包、成本曲线和最终统计 | 1 天 |

预计总历时：**已有权重和依赖可直接使用时约 7–10 个工作日；若需重新下载/适配 VMem 权重或数据约 10–14 个工作日**。这是工程历时估计，不是论文录用概率，也不是学生工时证明。H800 不会缩短数据资格、近邻排重和审稿验证时间。

## 当前创新判断

宽泛的“几何感知记忆”“固定预算选择”“confidence 校准”已有近邻，不能直接作为贡献。当前只保留两个窄候选：

1. **SOCF（Sparse Occlusion Competition Future-utility calibration）**：在稀疏遮挡/重访条件下，用历史可见几何风险预测未来 RGB-D/pose 效用；必须超过同预算强基线，且在跨场景和尾部指标上稳定。
2. **FGB-Future（Future Geometry Benefit evaluation）**：把“历史记忆是否帮助独立未来几何状态”定义成固定真实记忆预算下的新评价问题；贡献首先是可复查的评价协议，只有在近邻差异和真实结果成立时才能升级为方法论文。

两者当前审稿式综合约 6.8–7.1/10，主要扣分来自近邻风险、数据独立性和完整 forward 尚未验证。当前科学状态必须保持：`new_method_validated=false`、`novelty_authorization=NONE`。真正能让老师眼前一亮的证据不是名字，而是：同候选/同预算、未来答案隔离、跨场景、尾部风险和单记忆反事实都同时成立。

## 当前下一步

1. 读取 ICL-NUIM 下载回执并做结构资格审计；不把 `lr0` 写成零暴露盲测。
2. 修复一次无引号错误的 CUDA/PyTorch smoke，随后上传最小代码和合同，不上传私钥或 OpenRouter 凭据。
3. 先执行 Gate0，再运行跨场景 VMem 基线；Gate0 失败时只完成开发/诊断，不提交 GRC 主张。
4. 每个作业保存命令、commit、数据 SHA、seed、GPU、显存、wall time、prediction seal、GT 后评分和独立复核。

所有实验的详细原始证据仍以项目 `RESEARCH_LOG.md`、`RESEARCH_MEMORY.md`、`docs/RESEARCH_HANDOFF_CURRENT.md` 和各 S 目录为准。本文件是面向导师汇报和 GPU 接手的总览，不覆盖旧结果。

## 2026-09-16 13:53 Gate0 进展补充

S102 的机器可检查部分已显著推进：scene13 单个明确暴露的 development window、预测/评分清单、command-camera 来源、评分器、独立重算实现、188 文件源清单、运行时/权重/镜像绑定和精确计算节点隔离均已形成。Slurm 589826 在 dgx-09 通过了 exact boundary probe；该作业不加载模型、不做 forward、不打开未来 outcome。

`S103-VMemBase-scene13-w001-v1` 的 v4 候选校验了 216 个非审查 artifact，仍为 `BLOCKED_INDEPENDENT_REVIEWS_ONLY`。当前不能运行 S103；只剩两项真实人工/独立判断：3DMatch adapter 接受和不同作者对冻结 protocol 的批准。两项通过后还要重新得到零错误 `PRE_RUN_READY` 并生成 formal launch guard，才可执行表中的 S103。S104–S109 顺序与证据边界不变。

SuperPOD 调度依据：HKUST ITSC 官方说明要求集群作业通过 Slurm，并用 `sinfo`、`sbatch`、`squeue` 和 `scontrol` 管理作业；本项目按该流程提交短 smoke 和后续 GPU 作业：<https://itso.hkust.edu.hk/services/academic-teaching-support/high-performance-computing/superpod/slurm>。

## 2026-09-16 18:43 v5 修正

旧 v4 在正式 forward 前被静态审计否决：history/query 内参变换不一致。已修复为八帧共用单次 resize/crop K 变换，并以新 predictor/runtime/boundary 重新冻结。替代隔离 job 590696 在 dgx-27 完成；v5 仍严格阻塞在两项独立审查，真实 formal bundle 未生成，S103 尚未运行。该修复避免产生一批相机条件错误但表面可评分的无效 GPU 结果。


---

## 2026-09-18 收尾：GPU 计划执行完毕，队列清空

本节补记 09-16 之后的全部 GPU 活动。**计划中的诊断序列已跑完，结论已封版，队列为空，不再申请生成。**

| job | 内容 | 扩散 | 结果 |
|---|---|---|---|
| 595599 | 跨臂状态隔离的顺序不变性门禁 | 无 | 11/11 PASS，含非空洞性自检 |
| 595614 | 泄漏后果普查（全面板） | 无 | NULL 2 / PERM 4 / CONTENT 8；slot-0 在 14/14 不变 |
| 595625 | 禁用分支对 `initial_threshold` 免疫性 | 无 | 6/6 PASS |
| 595887 | 干净 NMS-on 臂 | 有，28 次 | 见下表；NULL 窗口字节同一性闸门通过 |
| 595891 | REFILL 修复臂 | 有，24 次 | −0.032 dB |
| 595902 | INPLACE 修复臂（主） | 有，16 次 | **−0.016 dB，未达 +0.20 dB，丢弃** |

窗口级对照（种子先折叠）：`nms_off − static` **+0.242**；`nms_on_clean − static` −0.485；
`nms_on_clean − nms_off` −0.726。泄漏分层：NULL +0.000 / PERM −0.015 / CONTENT +0.436。

**三条零扩散门禁全部先于生成执行**，这是本轮与早期批次最大的方法差异：隔离例程在花任何生成预算之前
被证明有效且非空洞，泄漏后果在花任何生成预算之前被纯元数据普查确定，封存臂的可复用性在重跑之前被
证明。由此把外部裁定估算的 84–88 次生成降到实际 28 次。

后续的评价器资格审查（`work/S110_evaluator_qualification/`）与支持集审计全部为零生成 CPU 工作。

**当前 GPU 待办：无。** 唯一可能重启生成的是 T1-5 的位姿可识别性门禁，尚未授权。
`new_method_validated=false`；`novelty_authorization=NONE`。
