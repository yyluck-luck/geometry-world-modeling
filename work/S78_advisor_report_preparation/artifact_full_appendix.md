# S78 导师汇报附录：已有实验、回执、数表与图片的逐项证据目录

生成时间：2026-09-10（北京时间）。本文件为撰写导师汇报的**证据索引**，不是新的实验，也不改变任何既有账目。

## 阅读规则

- 下文 `R/` 一律展开为绝对根目录：`/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/`。因此每个 `R/...` 都是项目中可直接定位的绝对路径。
- “真实输入”指 TUM RGB-D 数据集的真实相机照片/其正式轨迹，或用户提供的输入参考图；“模型生成图”指 VMem 采样后输出的 PNG；“保存量分析”不重新运行神经模型或图像生成器。
- 回执中的 `checks` 是文件身份、结构或算术检查条数，**不是**独立科研样本数。单一连续 TUM 片段中的帧/目标也不能写成独立场景数。
- 导师 PDF 中只嵌入标为“建议可用”的紧凑图、数表和报告；不要附模型权重、巨大 NPZ、私有 Harness 状态、密钥或逐帧原始张量。可在电子附件中保留 `receipt.json`、`metrics.json` 和 `ROOT_*ACCEPTANCE.json` 供复核。
- 全局科学状态仍是 `NO_METHOD_SELECTED`、`novelty_authorization=NONE`、`new_method_validated=false`。因此只能报告“完成了什么、看到了什么、下一步怎样证伪”，不可说已验证新方法、已复现完整 VMem 视频系统、已达到 PhD/CCF-A 论文结论。

## 一页总索引（建议放在附录开头）

| 编号 | 证据类型 | 是否真实模型执行 | 最适合的导师汇报定位 | 不可越过的边界 |
|---|---|---:|---|---|
| S21–S24 | 三个已有 3D 基线在真实 TUM 序列上的轨迹/深度评分 | 是 | 已完成的强基线与失败特征 | 非 VMem、非学生新方法、单场景已见数据 |
| S40/B0/C1 | VMem 声明变体两批生成与预注册窄评分 | S40/C1 是；B0 是保存图评分 | 原流程真实运行和“严重回访”事件未触发 | 不能由单一 MSE 证明几何/视频质量 |
| 原 C2 | 中断/失败的确认运行 | 未完成 | 负结果与工程诊断 | 无完整输出、无评分、不可配图称结果 |
| S64/S66 | C2 之后的单位修复工程变体与其保存图评分 | S64 是；S66 否 | 工程恢复已能闭合，不替代原 C2 | 不可与原 C2 或 S70 指标混作方法提升 |
| S67–S69 | 投影、真实参考编码、相机条件接口 | S68/S69 是；S67 否 | 后续受控实验的输入/观察器核验 | 没有视频质量或创新收益 |
| S70–S73 | 固定历史 A/A 重放/B 的生成、局部特征与真实对照 | S70 是；其余否 | 一个可追溯的固定集合观察与混杂诊断 | A/B 同时改变内容、顺序、槽位和缩放；不可作因果结论 |
| S74/S77 | 故意错误标签的几何敏感性算术 | 否 | 观察器标签敏感性/反例 | 非相机标定、非生成质量、非方法验证 |
| S75 | 五张真实历史缓存的 VAE 解码回环 | 是（仅 VAE 解码） | 编码缓存的有限保真性检查 | 非 VMem 采样、非视频、不归因于一个模块 |
| S76 | 沿 S70 A0 的单臂 +5° 真实生成和独立评分 | 是 | 有限匹配子集的相对方向响应 | 图均为模型生成；目标 23 弱；不代表全图相机正确 |

---

## A. 已有强基线：S21–S24

### S21｜300 帧真实序列基线（CUT3R / TTT3R）

| 项 | 已保存事实 |
|---|---|
| 原始/真实输入 | TUM RGB-D `freiburg2_desk`；2,965 个 RGB 时间戳可形成 2,257 个配对，取首 300 个、严格 20 ms RGB/轨迹配对、stride 1，覆盖 10.436629 s。推理仅 RGB（crop、512），GT 只在封存预测后评分。 |
| 实际运行 | CPU 8 线程，seed 0。CUT3R 531.001 s、峰值 12.642 GiB；TTT3R 524.731 s、峰值 12.229 GiB。该运行时间不适合宣称速度排序。 |
| 主数值 | ATE RMSE：CUT3R **8.253931 cm**，TTT3R **2.847830 cm**；相邻 RPE 平移：7.313548 / 5.258895 mm；相邻 RPE 旋转：0.316854 / 0.283595°。五段位置 RMSE（cm）：CUT 3.646/4.903/9.467/7.807/12.359，TTT 2.500/2.551/3.378/2.948/2.774。 |
| 原始预测与回执 | `R/results/S21_baseline/{cut3r,ttt3r}/frame_{0000..0299}.npz`；`R/results/S21_baseline/{cut3r,ttt3r}/receipt.json`；`R/results/S21_baseline/compatibility.json`；冻结输入 `R/work/S21_baseline_preparation/run_manifest.json`。 |
| 数表 | `R/results/S21_baseline/scoring/metrics.json`；`R/results/S21_baseline/scoring/{cut3r,ttt3r}_per_frame.csv`；对齐数组位于同一 `scoring/` 目录。 |
| 建议可用图 | 主图：`R/work/S21_reporting_v2/s21_all_frame_errors.png`（300 帧全段误差曲线）；附录图：`R/work/S21_reporting_v2/s21_real_residual_photos.png`（评分后选择的真实输入照片与残差，不能作因果图）。同名 `.pdf/.svg` 可用于 LaTeX。 |
| 可公开表述 | “在一个真实、已见的 TUM desk 轨迹上完成两种现有强基线的 300 帧运行；TTT3R 在该轨迹的 ATE/RPE 数字较低，且可看到 CUT3R 在后段误差升高。” |
| 禁止表述 | “提出/验证了新记忆方法”“复现了 VMem 视频”“跨场景泛化”“仅由这些结果推出遗忘机制”。 |

主报告：`R/docs/S21_RESULTS.md`。

### S22｜共享精度下 FILT3R 的第三个已有基线

| 项 | 已保存事实 |
|---|---|
| 原始/真实输入 | 完全复用 S21 封存的 `freiburg2_desk` 300 帧与评分口径，不是新数据或新场景。 |
| 实际运行 | FILT3R 实际 453.178 s、峰值 9.687 GiB、299 次 gain update。运行前为 CPU 兼容恢复 CUT3R q/k FP16；因此是“共享精度兼容配置”，不是无修改原始 CPU 路径。 |
| 主数值 | ATE RMSE：CUT 8.253931、TTT 2.847830、FILT **1.858154 cm**；RPE 平移：7.313548/5.258895/**4.931686 mm**；RPE 旋转：0.316854/0.283595/**0.276512°**。FILT 五段位置 RMSE（cm）：0.951/1.438/1.843/2.436/2.228。 |
| 回执/数表 | `R/results/S22_filt_shared_precision/filt3r/receipt.json`；`R/results/S22_filt_shared_precision/compatibility.json`；`R/results/S22_filt_shared_precision/scoring/metrics.json`。旧 CPU 精度不兼容记录仍在 `R/results/S22_filt_baseline/compatibility.json`。 |
| 图 | 不单独占正文主图；同 S21 的曲线可作为三方法背景。若需机制附注，放协议而非图：`R/docs/S22_FILT_SHARED_PRECISION_PROTOCOL.md`。 |
| 可公开表述 | “在相同真实片段和统一评分下，补充第三个公开基线；FILT3R 在该片段数值最低。报告已保留 CPU 精度兼容调整。” |
| 禁止表述 | “FILT3R 是本项目创新”或“统一精度条件证明了所有实现/硬件上的绝对排名”。 |

主报告：`R/docs/S22_RESULTS.md`。

### S23｜S21 已封存预测的真实深度与远距离尾部诊断

| 项 | 已保存事实 |
|---|---|
| 输入类型 | 复用三种方法合计 900 份已保存预测；**0 次新模型运行**。300 RGB 中 278 帧能与深度在 20 ms 内一一配对，22 帧无深度。 |
| 实际耗时 | 主诊断 25.339 s（外部 25.491 s，峰值 720 MiB）；距离分层 10.375 s。 |
| 主数值 | 有效网格深度像素 38,832,167。AbsRel：CUT 4.6235%、TTT 3.2608%、FILT 3.0618%；delta1：96.8647%、97.8470%、97.7772%；逐帧 RMSE：0.392691/0.325125/0.340982 m；全像素 RMSE：0.436553/0.343055/0.374948 m。 |
| 关键尾部数值 | 距离占比 `(0,2]/(2,4]/(4,8]/>8m` = 62.5663/31.1447/5.2618/1.0271%。对应 RMSE：CUT .0922/.3117/.9328/3.2609，TTT .0575/.2442/.8834/2.3346，FILT .0584/.2263/.8480/2.8710 m；FILT 的 `>8m` 像素只占 1.0271%，却占其总平方误差 60.2210%。 |
| 证据/数表 | `R/results/S23_geometry_diagnostic/metrics.json`、`receipt.json`、`gt_receipt.json`、`{cut3r,ttt3r,filt3r}_frames.json`。 |
| 建议可用图 | 正文图：`R/work/S23_reporting/s23_full_curves.png`（三方法全程深度诊断）；补充图：`R/work/S23_reporting/s23_depth_tail.png`（远距尾部）；谨慎附录：`R/work/S23_reporting/s23_real_depth_example.png`（真实 RGB/传感器深度/预测深度，帧 220 为评分后选择）。 |
| 可公开表述 | “用同一批封存预测做了真实深度后验诊断；远距离的少量像素对平方误差有明显影响，提示后续分析应分开看整体平均和尾部。” |
| 禁止表述 | “证明某一方法的 memory failure 原因”或“新方法已经解决尾部问题”。S23 是后验诊断、单场景、同作者第二实现，不是外部完整复现。 |

主报告：`R/docs/S23_RESULTS.md`。

### S24｜796 帧真实序列扩展与长时距诊断

| 项 | 已保存事实 |
|---|---|
| 原始/真实输入 | TUM `freiburg1_xyz`，798 RGB 中 796 帧严格 20 ms 匹配，跨度 26.572059 s。CUT3R/TTT3R/FILT3R 真正各运行 796 帧；CPU 8 线程、seed 0、DPT/512 输入后 384×512 输出。 |
| 实际运行 | CUT：前向/归档 1440.739 s、外部 1458.107 s、20.024 GiB；TTT：1422.230/1440.455 s、19.589 GiB；FILT：1230.847/1249.361 s、17.053 GiB。 |
| 主数值 | ATE RMSE：CUT **12.24063 cm**、TTT **9.68646 cm**、FILT **2.90258 cm**；相邻 RPE 平移 1.44291/1.58145/.63883 cm；旋转 .748409/.688018/.362990°；比例 .607028/.707204/.996851。 |
| 长时距数值 | 1 s（766 对）/5 s（645 对）平移 RPE：CUT 15.38041/18.30833 cm，TTT 10.72119/12.64820，FILT 3.48247/4.07539；旋转 RPE：CUT 6.038581/8.759028°，TTT 3.871503/4.543077，FILT 1.522748/1.655700。 |
| 预测/回执/表 | `R/results/S24_baseline_expansion/{cut3r,ttt3r,filt3r}/frame_{0000..0795}.npz` 与各自 `receipt.json`；`R/results/S24_baseline_expansion/scoring/metrics.json`；长时距 `R/results/S24_horizon_diagnostic/{metrics.json,all_pairs.csv,one_second_bins.csv,receipt.json,input_seal.json}`。 |
| 建议可用图 | 建议正文首选：`R/work/S24_reporting_v2/s24_all_frame_errors.png`（796 帧全段基线曲线）。可在附录加入 `R/results/S24_horizon_diagnostic/{translation_m_all_pairs.png,rotation_deg_all_pairs.png}`。`R/work/S24_reporting_v2/s24_real_residual_photos.png` 是评分后挑选的真实照片，只作阅读辅助。 |
| 可公开表述 | “将强基线扩至一个约 26.6 秒真实片段；FILT3R 在这一个固定片段的轨迹和 1/5 秒时距指标都最低。该结果奠定接下来寻找剩余问题、而非立刻造新模块的依据。” |
| 禁止表述 | “三种方法代表当前全部 SOTA”“单场景验证长程世界模型”“由 FILT 优势推出本项目创新”。单次运行、已见场景、无跨数据集外部复现。 |

主报告：`R/docs/S24_RESULTS.md`。

---

## B. VMem 原流程、预注册评分与未完成 C2：S40、B0、C1、C2

### S40｜声明组件变体的两批真实生成

| 项 | 已保存事实 |
|---|---|
| 原始输入 | 一张用户提供的输入参考图 `R/results/S40_declared_variant_generation/visual_qa_all9/input_reference_changi.jpg`。它可被称为“输入参考照片”，**不是** TUM 实验照片，也不是生成结果。 |
| 实际执行 | 2026-09-07 11:16:51.205659Z–12:02:29.221978Z，外部 2737.983865 s，return 0，树峰值 25,862,127,616 B，327 条追踪事件。两批均 50 步，模型调用 100 次、解码 2 次；batch 1 选择 `[0]`，batch 2 选择 `[0,2,4,1]`，历史闭合到 1→5→9。 |
| 组件边界 | VMem 与声明的 `stabilityai/sd-vae-ft-mse` 组件变体实际加载；原 SD2.1 VAE 精确身份仍未知。因此不能称“精确原版 VMem 复现”。 |
| 回执/档案 | `R/work/S40_declared_variant_generation/execution_01/{receipt.json,worker_receipt.json}`；`R/results/S40_declared_variant_generation/{observation_summary.json,runtime_loading.json}`；原始归档清单 `R/work/S40_declared_variant_generation/archive/manifest.json`。 |
| 图 | `R/results/S40_declared_variant_generation/visual_qa_all9/S40_input_plus_all9_contact_sheet.png`。九格里 1 张为输入参考、8 张为**模型生成帧**；按文件名 `frame_00_requested_yaw_0.00.png` 至 `frame_08_requested_yaw_0.00.png` 可逐一定位。九帧短 yaw 回环不能称视频。 |
| 可公开表述 | “已在本机完成一次两批、8 张输出的 VMem 声明变体运行并封存随机/组件/输出证据；其质量和长程几何结论仍需独立评分。” |
| 禁止表述 | “图是真实照片”“已验证摄像机轨迹正确”“已解决长程一致性”或“实验已证明创新”。 |

### B0｜S40 保存像素的预注册窄范围评分与独立复算

| 项 | 已保存事实 |
|---|---|
| 输入/执行类型 | 仅对 S40 的保存像素评分，**没有新生成**。主评分 2026-09-07 15:47:16.970195Z；另一个作者随后独立数值复算完成。 |
| 预注册主数值 | 四个固定区域、147,456 像素/442,368 RGB 标量；MSE **0.005278160708699555**，PSNR **22.77517390576968**。严格事件 `MSE > 0.01` 为 **false**。全帧 MSE .004389557… 只是诊断，非主终点。 |
| 回执/数表 | 主：`R/work/S42_baseline_failure_preregistration/B0_score_attempt_01/report.json`；独立：`R/work/S42_baseline_failure_preregistration/B0_independent_recompute/execution_01/{report.json,receipt.json}`。 |
| 图 | 不建议主文放 B0 原图；如需要追溯，使用 S40 contact sheet，且图注明确“保存图、非真实照片”。 |
| 可公开表述 | “预先冻结的‘严重回访差异’窄 MSE 事件没有触发；这个负结果防止我们把没有观察到的严重事件写成既定失败。” |
| 禁止表述 | “模型没有任何错误”“画质好”“几何正确”“因此无需继续 C1/C2”。 |

### C1｜独立确认生成与同一窄范围事件

| 项 | 已保存事实 |
|---|---|
| 原始输入 | `jesus.jpg`（文件身份由执行清单固定）和 S40 控制；这不是 TUM 序列。 |
| 实际生成 | 2026-09-07 18:03:49.459683Z–18:48:33.738498Z，return 0；两批、各 50 步、输出 9 张（输入预处理图 1 张 + 8 张模型生成图）。 |
| 主数值 | 输入 ID 0 与回访 ID 8 的固定区域：MSE **0.00464396063251803**，PSNR **23.331114704908824**，严格 `> .01` 事件为 **false**；147,456 像素/442,368 RGB 标量。 |
| 回执/数表 | 生成：`R/work/S44_C1_confirmation_generation/execution_01/receipt.json`；评分：`R/work/S46_c1_blind_scoring_preparation/C1_score_attempt_01/report.json`；独立复算：`R/work/S46_c1_blind_scoring_preparation/C1_independent_recompute/execution_01/{report.json,receipt.json}`。 |
| 图 | `R/results/S44_C1_confirmation_generation/visual_qa_all9/C1_all9_contact_sheet.png`；`frame_00` 为真实输入的预处理版本，`frame_01..08` 为模型生成的请求 yaw 帧，另有 `VISUAL_QA_OBSERVATION.json` 和 manifest。导师 PDF 若加入，必须以“小型工程核验图”而非自然数据集结果展示。 |
| 可公开表述 | “第二个输入上，预先同一严重回访事件也未触发；这限制了原本想把它作为主要 failure trigger 的路线。” |
| 禁止表述 | “C1 证明整体无失败”或“2 次 false 已证明相机/视频可靠”。 |

### 原 C2｜中断和失败保留，不作为成图结果

| 项 | 已保存事实 |
|---|---|
| V8 | `R/work/resumption_20260908/C2_V8_RESUMPTION_OBSERVATION.json`：2026-09-08 14:01:04Z 收到 SIGTERM，第一批只到 23/50；没有完整第一批，更没有第二批或质量评价。 |
| V9 | `R/work/resumption_20260909/C2_V9_EXTERNAL_LAUNCH/receipt.json`：2026-09-08 16:45:42.636402Z–17:08:45.362273Z，1382.725772 s，return 1。第一批结束后，第二批导航在空检索结果索引处 `IndexError`；第二批采样未启动。 |
| 可公开表述 | “原 C2 确认流程未完成，记录显示故障发生在第二批开始前的空检索路径；保留为可复现工程负结果。” |
| 禁止表述 | “C2 的输出很差/很好”“三项原协议已完成”“C2 失败证明了某种科学原因”。不可附局部或残缺图当作视频结果。 |

工程诊断主报告：`R/docs/S60_C2_FAILURE_AND_UNIT_DIAGNOSIS.md`；创新/科学边界：`R/docs/INNOVATION_GUIDANCE_CURRENT.md`。

---

## C. 单位修复与保存图评分：S64、S66

### S64｜非原 C2 的工程单位修复变体

| 项 | 已保存事实 |
|---|---|
| 原始输入与设置 | `living_room.jpg`，seed 44，CPU 8 线程 FP32、576；左 5 帧再右 5 帧 yaw、2×50 步。用 VMem + 声明的 ft-mse VAE；采用“严格正 z 的中位数”单位语义。 |
| 实际生成 | 2026-09-08 21:28:11.696408Z–22:13:40.726069Z，2729.029596 s，return 0。100 次模型调用、2 次解码、2 个 scene，历史 1→5→9；保存 8 张生成 + 1 张输入。 |
| 回执/核验 | `R/work/S64_unit_repaired_generation/{execution_01,external_launch_01}/receipt.json`；`R/work/S64_unit_repaired_generation/postrun_readback_01/{report.json,receipt.json}`（205 项检查）；独立审阅 `R/work/S64_unit_repaired_generation/INDEPENDENT_POSTRUN_RESULT_REVIEW.md`。 |
| 图 | `R/results/S64_unit_repaired_generation/visual_qa_all9/S64_all9_contact_sheet.png`，图中第 0 张为输入、其余八张都是模型生成。 |
| 可公开表述 | “原 C2 未完成后，以明确不同的单位语义做了一个工程修复变体，运行成功并通过保存量读回。” |
| 禁止表述 | “修复即解决原 C2”“S64 直接对比 C1/C2 得到方法提升”“其图是真实照片”。 |

主报告：`R/docs/S64_UNIT_REPAIRED_GENERATION.md`。

### S65｜可观测性、数学反例与新颖性排重（无实验图/无模型结果）

| 项 | 已保存事实 |
|---|---|
| 输入/执行类型 | 文献、源码接口和符号数学审阅；没有真实视频、模型加载、图像生成、真实数据评分或新数表。 |
| 已保存资料 | `R/work/S65_observability_triage/S65_BEGINNER_RESEARCH_NOTE.md`、`ROOT_MATH_DERIVATION.md`、`ROOT_EXACT_COUNTEREXAMPLE.json`、`PRIMARY_MATH_REVIEW.md` 及 `ROOT_WEB*` 来源范围记录。 |
| 图 | 无。不要为了“看起来有创新”把符号示意图包装成实验图。 |
| 可公开表述 | “在提出方法前，先做可观测性/近邻排重：普通 attention、source tag、几何 gate 和简单加权已有相近工作；因此当前不把它们作为本项目贡献。” |
| 禁止表述 | “S65 已验证新算法”“数学反例等于真实视频证据”“理论笔记已产生实验收益”。 |

### S66｜S64 保存图的固定相机/像素评分

| 项 | 已保存事实 |
|---|---|
| 输入/执行类型 | 只读取 S64 的九张保存图和单独相机条件数组，**不重新跑模型**。主评分 2026-09-08 23:32:36–23:32:36.228Z；独立复算 23:33:02.851–23:33:03Z。 |
| 主数值 | 0→8 固定区域 MSE **0.0006382446123931144**，PSNR **31.950128425132405**，严格 `>.01` 事件 false。全帧 .000914694351664958 仅诊断。相机条件单独 11 数组、1,584 B。 |
| 回执/数表 | `R/work/S66_s64_camera_scoring/score_01/{report.json,receipt.json}`；`R/work/S66_s64_camera_scoring/recompute_01/{report.json,receipt.json}`；独立审阅 `R/work/S66_s64_camera_scoring/CAMERA_INDEPENDENT_RESULT_REVIEW.md`。 |
| 图 | 与 S64 共用 `S64_all9_contact_sheet.png`；不要将这个像素 MSE 与 S70 的真实目标参考 MSE 放在同一可比较柱图。 |
| 可公开表述 | “在工程变体的非常窄固定终点上，保存图像评分经另一实现一致复算；该终点没有触发既定阈值。” |
| 禁止表述 | “工程变体优于/替代原 C2”“分数说明画面自然或几何正确”“与 S70/其他任务指标可直接横比”。 |

主报告：`R/docs/S66_FIXED_SCORE_AND_VISUAL_RESULT.md`。

---

## D. 输入、观察器和条件接口：S67–S69

### S67｜平移查询下投影变化、集合不变的保存量干预

| 项 | 已保存事实 |
|---|---|
| 输入/执行类型 | 五个已有源、515 个保存点的数值干预；不读取 RGB 正文，不重新生成/检索/训练模型。 |
| 实际运行 | 2026-09-09 00:59:29.452768Z–00:59:34.517464Z，5.064598 s，return 0；1,496 份数值文件、1,631,256 B。独立检查于 08:05:49–08:05:49.925 完成。 |
| 主数值 | 纯旋转历史投影最大差 3.33e-16；新平移查询最大 **57.9713 px**、中位 **7.5179 px**，514/515 >1e-6。检索权重 L1 变化 .0268168，但每源 quota 均 1，最终 ID 都为 `[0,2,4,1]`；5 个回传缓存数组位级一致。 |
| 回执/表 | `R/work/S67_translated_query_diagnostic/{execution_01,external_01}/receipt.json`；`R/work/S67_translated_query_diagnostic/ROOT_FINAL_RESULT_ACCEPTANCE.json`；`R/work/S67_translated_query_diagnostic/INDEPENDENT_RESULT_REVIEW.md`。 |
| 建议可用图 | `R/work/S67_translated_query_diagnostic/figures/S67_projection_changes_context_unchanged.png`（解释“投影能变但固定 quota/排序仍不变”的诊断；非质量图）。 |
| 可公开表述 | “在一个固定数值案例中，查询投影明显变化，而固定筛选规则返回的集合未变。这揭示了当前接口可能缺少区分力，值得成为后续强基线设计约束。” |
| 禁止表述 | “515 个独立视频样本”“自然遮挡失败”“证明任何生成质量变化/创新”。 |

主报告：`R/docs/S67_TRANSLATED_QUERY_RESULT.md`。

### S68｜五张真实 TUM 历史照片的实际编码缓存

| 项 | 已保存事实 |
|---|---|
| 原始/真实输入 | TUM `freiburg2_desk` 的真实 PNG，帧 12/13/14/18/19，均 640×480，合计 2,625,997 B；仅这五张编码，目标 20–23 RGB 正文没有进入本次编码。 |
| 实际模型执行 | 2026-09-09 09:12:53.263956Z–09:13:11.908300Z，外部 18.644267 s、return 0；CPU 8 线程 FP32。每图生成 latent `[4,72,72]`、CLIP `[1024]` 与两组 3×3 K；五个 NPZ 20 数组，共 440,740 B。 |
| 回执/接受 | `R/work/S68_tum_vmem_cache_bridge/{INPUTS.json,PROTOCOL.md,execution_01/receipt.json,external_01/receipt.json,INDEPENDENT_RESULT_REVIEW.md,ROOT_FINAL_RESULT_ACCEPTANCE.json}`。 |
| 图 | 不建议把 latent 或未观看的原始照片作为成果图。它的价值是可审计的真实输入接口，不是视觉结果。 |
| 可公开表述 | “已将五张真实历史照片实际喂入原代码的编码组件并封存缓存，独立核验了来源、结构、有限值和内参变换；为后续公平条件对照准备真实输入。” |
| 禁止表述 | “已生成视频/评分”“138 个样本”“精确原 VMem 复现”。组件仍为 ft-mse 变体，原 SD2.1 VAE 身份未知。 |

主报告：`R/docs/S68_REAL_REFERENCE_CACHE_RESULT.md`。

### S69｜两组真实历史照片的相机条件组装

| 项 | 已保存事实 |
|---|---|
| 输入 | S68 的真 TUM 缓存，A=`[19,18,13,12]`、B=`[19,18,14,13]`，目标 20–23。帧号来自同一连续序列，不是九个独立场景。 |
| 实际模型执行 | 调用原模型条件组装函数，执行 **1.3630646 s**；独立实现核验约 .264 s；无新图像编码、无采样生成。 |
| 主数值 | A 自然尺度 27.322040557861328，B 26.265939712524414；目标方向最大差 9.54e-7；按本组尺度归一后的 moment 最大差 1.95e-7；外观均值替换公式最大误差 2.38e-7；独立 ray 最大误差 7.44e-6。150 个结构/身份、40 个数值检查通过。 |
| 回执/接受 | `R/work/S69_tum_camera_conditioning/{execution_01,external_01,independent_external_01}/receipt.json`；`INDEPENDENT_RESULT_REVIEW.md`；`ROOT_FINAL_RESULT_ACCEPTANCE.json`；`ROOT_REPORT_ACCEPTANCE.json`。 |
| 图 | 无建议正文成图。S69 应用一张小的“实验条件表”，而不是产生视觉图。 |
| 可公开表述 | “换完整历史集合 A→B 时，原条件组装实际改变内部自然尺度，虽目标方向/归一化 moment 基本不变；因此后面的 A/B 图差不能简化解释为只换一张照片内容。” |
| 禁止表述 | “证明尺度导致画质问题”“单独控制了历史内容”“相机已物理标定”。近似 K、无去畸变、内容/顺序/槽位仍混杂。 |

主报告：`R/docs/S69_CAMERA_CONDITIONING_RESULT.md`。其中 `GEMINI_FACTCHECK.md` 是辅助模型意见及事实纠正记录，**不可**当作科学原始证据或引用来源。

---

## E. 固定集合真实生成、观察器和对照：S70–S73

### S70｜A/A 重放/B 三臂固定上下文真实生成

| 项 | 已保存事实 |
|---|---|
| 原始/真实输入 | S68/69 的真实 `freiburg2_desk` 历史与目标：A0/A1=`[19,18,13,12]`，B=`[19,18,14,13]`，目标 20–23。目标参考图为四张真实 TUM 照片；A0/A1/B 12 张是模型生成输出。 |
| 实际模型执行 | 三臂各四目标、各 50 步；2026-09-09 03:01:00.645176Z–04:14:59.796816Z，4439.151532 s、return 0、进程树峰值 17,863,704,576 B。A1 与 A0 精确重放。 |
| 主数值 | 四目标的 A0/B MSE：20 .084402763/.085639751，21 .148325563/.139261226，22 .164819270/.153864158，23 .127119075/.122389515；平均 .131166668/.125288663，`B-A=-.005878005`。A1 与 A0 位级一致。43 个比较和 36 个参考映射像素核验完成。 |
| 回执/数表 | `R/work/S70_fixed_context_generation/{execution_01,external_01,scoring_01}/receipt.json`；`R/work/S70_fixed_context_generation/ROOT_RESULT_ACCEPTANCE.json`；`R/work/S70_fixed_context_generation/scoring_01/reference_{20..23}.png` 及评分表。 |
| 建议可用图 | `R/work/S70_fixed_context_generation/visuals_01/S70_all_targets_contact_sheet.png`（4 个真实参考、A0/A1/B 输出；图注要逐格标注 4 real + 12 model-generated）。同目录的 individual target PNG 适合附录。 |
| 可公开表述 | “在一个已见固定片段上完成 A/A 精确重放/B 三臂的真实采样；B 的平均像素 MSE 略低，但 A/B 同时改变历史内容、顺序、相机归一化、latent 槽位和全局外观条件。” |
| 禁止表述 | “几何支持较高反而更差”“B 证明选图机制有效”“MSE 是几何正确性/视觉质量”“四个目标代表泛化场景”。这是非盲、已见固定目标。 |

主报告：`R/docs/S70_FIXED_CONTEXT_RESULT.md`。

### S71｜S70 保存图的局部匹配/构图诊断

| 项 | 已保存事实 |
|---|---|
| 输入/执行类型 | 读取 S70 的 16 张保存 PNG，**无新模型调用**；2026-09-09 05:07:33.358327Z–05:07:34.814371Z，1.456041 s、7,219,446 B。 |
| 主数值 | 真实参考-A / 真实参考-B 的互匹配数、位移中位数、RANSAC 内点：目标 20 为 180/190、39.49/43.07 px、93/117；21 为 122/78、107.86/115.83、48/28；22 为 25/23、200.69/196.77、11/10；23 为 3/7、373/297、无可用拟合。A-A 重放四对位置差为 0。独立标准库复算 305 项，最大差 1.36e-13 px。 |
| 证据/图 | `R/work/S71_s70_framing_diagnosis/{execution_01,external_01}/receipt.json`、`ROOT_RESULT_ACCEPTANCE.json`；图 `R/work/S71_s70_framing_diagnosis/visuals_02/S71_all8_feature_pairs.png`。 |
| 可公开表述 | “在固定特征观察器下，S70 生成图中的局部匹配位置与真实参考有明显差异；但 target 23 的有效匹配过少，结果只适合作为构图/观察器诊断。” |
| 禁止表述 | “相机一定错误”“已定位根代码 bug”“该数值等于相机误差”。 |

主报告：`R/docs/S71_FRAMING_DIAGNOSIS_RESULT.md`。数据集 errata：`R/work/S72_fixed_requested_geometry/S71_DATASET_ERRATA.md`（S71 早期误将标定适用到 fr1 的记录已纠正，现用真实 fr2 desk 理解）。

### S72｜真实照片之间的固定几何观察器对照

| 项 | 已保存事实 |
|---|---|
| 原始/真实输入 | `freiburg2_desk` 的真实历史 19 和真实目标 20–23，读取 5 个已有 PNG（2,305,568 压缩 B）与相机 K；无新模型、无图像生成。 |
| 实际运行 | 外部记录约 1.955583 s；独立核验 125 项。 |
| 主数值 | 目标 20/21/22/23 的匹配数 M=323/160/80/75；中位重投影残差 1.34/3.16/1.41/4.22 px，p95 4.19/6.14/3.36/121.10 px，≤5px 比例 95.36/85.62/96.25/58.67%。覆盖为 15/15、13/13、9/9、13/10。 |
| 回执/图 | `R/work/S72_fixed_requested_geometry/{execution_01,external_01,independent_external_01}/receipt.json`；`ROOT_RESULT_ACCEPTANCE.json`；图 `R/work/S72_fixed_requested_geometry/visuals_01/S72_all4_real_controls.png`。该图是**真实照片对**及抽样匹配，不是模型生成。 |
| 可公开表述 | “在相同观察器下，真实相邻照片通常有较低残差；这为阅读 S73 的生成图诊断提供一个必要的局部参照。” |
| 禁止表述 | “这完成了相机标定/GT 物理验证”“与 S70 图的内容完全一一对应”。近似 ROS K、无去畸变、像素中心等仍有限制；20–23 也是同一轨迹。 |

主报告：`R/docs/S72_REAL_CONTROL_RESULT.md`。

### S73｜生成图在同一固定几何观察器下的保存量检查

| 项 | 已保存事实 |
|---|---|
| 输入/执行类型 | 复用 S70 的 A0/B 8 张生成 PNG 与 S72 真实对照；不新生成。固定源真实历史 19、1,239 anchor features；只重新计算匹配/几何。成功运行外部 2026-09-09 07:35:18.832Z–07:35:19.894Z，1.062418 s。初次 `execution_01/external_01` 的 cv2 import 失败保留，成功结果为 `execution_02/external_02`。 |
| 主数值 | 20：真实 323 匹配、≤10px 315；A0 249、median 21.655、≤10 0；B 275、27.668、0。21：真实 160/3.162/157；A0 195/75.693/0；B 241/64.210/0。22：真实 80/1.412/77；A0 86/146.125/0；B 38/124.604/0。23：真实 75/4.225/63；A0 38/210.102/0；B 28/224.644/0。共同支持仅 92/48/6/0，所有四目标事件均为 UNKNOWN。 |
| 回执/图 | `R/work/S73_generated_fixed_geometry/{execution_02,external_02}/receipt.json`；`ROOT_RESULT_ACCEPTANCE.json`；独立核验最大误差 6.6791e-13，见同目录 `INDEPENDENT_RESULT_REVIEW.md`；图 `R/work/S73_generated_fixed_geometry/visuals_01/S73_support_and_error.png`。 |
| 可公开表述 | “在固定近似观察器中，S70 生成图的可接受匹配全部超过 10px，而同一观察器在部分真实照片对上较低；结果提示存在值得进一步隔离的构图/内容/相机混杂。” |
| 禁止表述 | “每像素错误”“严格不遵守相机”“已经找到 memory 机制”。弱/不共支持匹配、内容差异、近似 K 和未去畸变都足以限制因果解释。 |

主报告：`R/docs/S73_GENERATED_GEOMETRY_RESULT.md`。

---

## F. 反例控制、VAE 回环和相对相机响应：S74–S77

### S74｜真实对照的错误相机标签敏感性

| 项 | 已保存事实 |
|---|---|
| 输入/执行类型 | 复用 S72 的 638 个真实对应点；固定错误映射 20↔23、21↔22。无 RGB 再读、无 feature rematch、无神经模型。 |
| 实际运行 | 外部 .196519 s，worker .13068 s；独立算术复算通过。 |
| 主数值 | 正确/错误标签残差中位数（px）：20→23 为 1.341619/107.736411（Δ+105.664575，322 正/1 负/0 零）；21→22 为 3.162289/38.875584（+35.394241，157/3/0）；22→21 为 1.411655/42.094455（+40.807063，80/0/0）；23→20 为 4.224642/98.670903（+93.931676，71/4/0）。四事件为 true，只有 8 个点负差。 |
| 回执/数据 | `R/work/S74_wrong_pose_control/{CONTRACT.json,geometry_separation.json,execution_01/receipt.json,external_01/receipt.json,independent_result_01/receipt.json,ROOT_RESULT_ACCEPTANCE.json}`。 |
| 图 | 没有独立图。导师 PDF 可放四行小表，标题为“错误标签的观察器敏感性（真实控制）”。 |
| 可公开表述 | “对同一真实对应点故意置换标签会显著增大该固定观察器的残差，说明这个观察器至少能区分这组标签。” |
| 禁止表述 | “完成标定”“证明 S70 的图相机一定错误”“证明新方法有效”。 |

主报告：`R/docs/S74_WRONG_POSE_CONTROL_RESULT.md`。

### S75｜五张真实历史缓存的 VAE 解码回环

| 项 | 已保存事实 |
|---|---|
| 原始/真实输入 | S68 已缓存的真实 TUM 历史 12/13/14/18/19；仅通过 ft-mse VAE 解码，未重新编码、未运行 CLIP、未跑 VMem 采样。 |
| 实际模型执行 | 5 次真实解码，外部 2026-09-09 08:17:14.953014Z–08:17:32.452432Z，17.499437 s，return 0。 |
| 主数值 | 每图 MSE/MAE：12 .0030294796/.0351155172，13 .0023554933/.0315610440，14 .0040734555/.0386592239，18 .0044893037/.0400692812，19 .0040323075/.0380160334。互匹配比例 38.31/51.83/33.66/31.54/31.52%；匹配中位位移 .538384/.473497/.538518/.523430/.498168 px；每图 >10px 离群点 2/4/7/4/8，最大 50.308/174.481/453.504/454.078/480.846 px。 |
| 回执/图 | `R/work/S75_vae_history_roundtrip/{execution_01,external_01}/receipt.json`、`INDEPENDENT_RESULT_REVIEW.md`、`ROOT_RESULT_ACCEPTANCE.json`；图 `R/work/S75_vae_history_roundtrip/visuals_01/ALL_FIVE_PAIRS.png`（每对均为真实源图与 VAE 重建图，重建图不是实拍照片）。 |
| 可公开表述 | “真实历史缓存经一次实际 VAE 解码可以保留粗粒度外观；但特征匹配比例不高且保留大离群尾部，不能把缓存当作无损图像。” |
| 禁止表述 | “验证 VMem 视频稳定”“VAE 是 S70 问题唯一原因”“解码分数直接代表生成 latent 兼容”。 |

主报告：`R/docs/S75_VAE_HISTORY_ROUNDTRIP_RESULT.md`。

### S76｜单独 +5° 查询的相对相机响应

| 项 | 已保存事实 |
|---|---|
| 输入与设计 | 重用已验收 S70 A0，固定历史 `[19,18,13,12]`、模型、相机中心、K、外观条件和实际随机流，仅产生 +5° yaw 的四个新目标图。不是学生新方法，也不是多随机种子方差估计。 |
| 实际模型执行 | 2026-09-09 09:17:34.579246Z–09:42:04.467919Z，1469.888697 s，return 0，4 个新输出、各 50 步。独立生成核验 308/308 项；随后保存图评分 2.648151 s，独立评分核验 19,823/19,823 项。 |
| 主数值 | 目标 20/21/22/23 的全匹配 M/N=304/1281、254/1172、89/651、10/727；共同匹配 C/Nc=302/1272、254/1160、88/632、6/681。`identity-H` 的配对中位数：53.274/51.421/38.173/5.622 px；共同支持：53.279/51.421/46.099/46.221 px。预先的 all-4 事件均 true，但目标 23 仅 10/6 点，且全匹配为 5 正/5 负、H 中位 102.651 px。 |
| 回执/数表 | `R/work/S76_relative_camera_response/{execution_01,external_01,scoring_01,scoring_external_01}/receipt.json`；`ROOT_GENERATION_ACCEPTANCE.json`、`ROOT_RESULT_ACCEPTANCE.json`；评分 PNG 位于 `scoring_01/{A0_target_{20..23}.png,yaw_plus5_target_{20..23}.png}`。 |
| 建议可用图 | `R/work/S76_relative_camera_response/visuals_01/ALL_FOUR_TARGET_PAIRS.png`。**八张全是模型生成图**，不应写“真实照片”；20/21 有较可读的局部布局，22 模糊变形，23 构图/场景变化大。 |
| 可公开表述 | “在一个冻结历史和实际随机流的单臂干预下，匹配子集显示有限方向响应；同时目标 23 的少量/不一致匹配使结论必须限定到观察到的子集。” |
| 禁止表述 | “完整画面相机正确”“严格 H 等变”“相机可控世界模型”“创新成立”。 |

主报告：`R/docs/S76_RELATIVE_CAMERA_RESPONSE_RESULT.md`。

### S77｜生成图错误相机标签的算术反例

| 项 | 已保存事实 |
|---|---|
| 输入/执行类型 | 使用 S73/S70 已保存的生成图匹配坐标/ID 与 S74 真实行；固定 20↔23、21↔22，不读 depth、不产生新图、不重新特征匹配或运行神经模型。 |
| 实际运行 | `R/work/S77_generated_wrong_pose_control/EXTERNAL_EXECUTION_01.json`：2026-09-09 10:07:57.123–10:07:57.198，.075228 s、return 0；独立标准库算术在 10:11:41.775984–10:11:41.816158，.040184 s、25,109 检查 PASS。 |
| 主数值 | A0 四目标 Δ：110.834792、41.927424、-41.597221、-114.821347；B：111.153679、41.696979、-41.064979、-118.924658。两生成臂 all-4 都 false；目标 23 原共同支持为空，二级 all-4 为 null。复用的真实行保持 S74 正敏感结果。 |
| 回执/资料 | `R/work/S77_generated_wrong_pose_control/{CONTRACT.json,EXTERNAL_EXECUTION_01.json,execution_01/receipt.json,source_review_01/,independent_result_01/execution_01/receipt.json}`。S77 目录**没有**独立 `ROOT_RESULT_ACCEPTANCE.json`，不能在 PDF 声称“根验收通过”。 |
| 图 | 无图。建议仅把它作为附录“反例/负诊断”四行表，说明生成图的固定匹配并未像真实对照一样显示同一标签敏感性。 |
| 可公开表述 | “固定保存匹配的错误标签算术在生成臂上未稳定复现 S74 真实对照的模式；该负结果进一步说明不能把现有观察器结果升级为相机或方法结论。” |
| 禁止表述 | “证明生成相机错误的唯一原因”“已验证预测状态创新”“独立最终验收”。Gemini 输出仅是辅助咨询，见 `gemini_predictive_state_01/`，不可作为实验数据。 |

---

## G. PDF 选图与引用建议（不复制大图）

### 适合正文的最小图组

1. **研究基础（图 1）**：`R/work/S24_reporting_v2/s24_all_frame_errors.png`。说明：三个现有基线在真实 796 帧上的轨迹误差；图注限定“单一已见 TUM 序列”。
2. **问题诊断（图 2）**：`R/work/S23_reporting/s23_depth_tail.png`。说明：远距离尾部对误差的影响；不写成记忆机制。
3. **受控输入结构（可选图 3）**：`R/work/S72_fixed_requested_geometry/visuals_01/S72_all4_real_controls.png`。说明：真实照片对的固定观察器，且要注明近似 K、无去畸变。
4. **固定集合生成观察（图 4）**：`R/work/S70_fixed_context_generation/visuals_01/S70_all_targets_contact_sheet.png`。明确 4 张真实目标参考 + 12 张模型生成图。
5. **有限相对响应（附录而非封面）**：`R/work/S76_relative_camera_response/visuals_01/ALL_FOUR_TARGET_PAIRS.png`。八张均为模型生成；加上 target 23 警示。

### 只宜放技术附录的图

- S21 `s21_real_residual_photos.png`、S23 `s23_real_depth_example.png`、S24 `s24_real_residual_photos.png`：均有评分后选择偏差，适合解释数据而非证明主张。
- S40/C1/S64 contact sheet：单次工程运行/输入类型不同，不能与 TUM 主实验同列。
- S71 `S71_all8_feature_pairs.png` 与 S73 `S73_support_and_error.png`：观察器诊断，不要被误解为绝对相机标定。
- S75 `ALL_FIVE_PAIRS.png`：真实输入与 VAE 重建并列，要清楚标注重建不是实拍。
- S67 图：数值接口敏感性，不表现图像质量。

### 不可称为“真实照片”的材料

1. S40：除了 `input_reference_changi.jpg` 以外的 8 帧，均为模型生成。
2. C1：除 frame 00 的预处理输入以外，frame 01–08 为模型生成。
3. S64/S66：除 frame 00 输入外，8 帧为模型生成。
4. S70：A0/A1/B 共 12 张为模型生成；仅 `scoring_01/reference_20..23.png` 为真实 TUM 目标照片。
5. S76：所有 8 张配对图均为模型生成；它们没有真实照片格。
6. S75：左侧（或源侧）可为真实历史照片，VAE 恢复侧是模型解码输出，不能称实拍。

## H. 建议导师报告的证据附件结构

1. 主文只保留 proposal 问题、S24/S23 强基线、S40→C2 的诚实负结果、S68–S76 的受控诊断、以及“尚未选定方法”的决策。
2. 附录 A：S21/S22/S24 的完整数表与回执路径；附录 B：S40/B0/C1/C2/S64 的运行状态表；附录 C：S67–S77 的合同、核验和边界表。
3. 电子压缩包用每阶段的 `docs/S*_RESULT*.md`、`metrics.json`、`receipt.json`、`ROOT_*ACCEPTANCE.json`、一张 PNG；不要打包模型权重、逐帧 NPZ 或用户输入照片的多余副本。
4. 每个数字表下用一句限制语：数据集/是否新模型执行/是否独立核验/不能得出的结论。这样比夸张“创新”更能让导师评估下一步是否值得给 GPU。

## I. 最小完整来源清单

- Proposal 原件：`/Users/rocket/Desktop/HKUST IT/ip-/Yiyang_LIU_Proposal.pdf`；工作文本提取：`/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/Yiyang_LIU_Proposal.txt`。
- 当前总交接：`R/docs/RESEARCH_HANDOFF_CURRENT.md`。
- 原则与时间账：`R/RESEARCH_PRINCIPLES.md`、`R/RESEARCH_MEMORY.md`、`R/RESEARCH_LOG.md`、`R/research_events.jsonl`。
- 附录生成前应只核验主报告与关键接受票，而不要再跑任何模型。推荐最小 SHA/回读入口：S24 `R/results/S24_baseline_expansion/scoring/metrics.json`，S40 `R/work/S40_declared_variant_generation/execution_01/receipt.json`，S70 `R/work/S70_fixed_context_generation/ROOT_RESULT_ACCEPTANCE.json`，S76 `R/work/S76_relative_camera_response/ROOT_RESULT_ACCEPTANCE.json`，及本目录的 `artifact_inventory_agent.md`。
