# S78 导师汇报 PDF：证据与配图盘点（只读）

盘点时间：2026-09-10（由 `/root/artifact_inventory` 完成）。本文件只列出已经存在、可核对的材料；没有复制图片、没有运行模型、没有修改主账。目标是让主报告作者在给导师的 PDF 中把 **真实输入、模型生成、缓存重算、保存量几何分析** 分开陈述。

## 1. Proposal 的可引用来源

| 用途 | 绝对路径 | 已核事实 |
|---|---|---|
| 原始 proposal PDF | `/Users/rocket/Desktop/HKUST IT/ip-/Yiyang_LIU_Proposal.pdf` | A4、1 页、311,136 B，创建时间为 2026-08-26；项目目标是：先做强基线与失败刻画，再选择一个聚焦的几何一致性机制，最后做公平评测。 |
| 可检索文本版 | `/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/Yiyang_LIU_Proposal.txt` | 已核到目标、14 周计划与交付要求；不能把计划中的第 6–12 周工作写成已经完成。 |

Proposal 的主线应被保留为：**baseline characterization -> failure analysis -> one falsifiable mechanism -> fair evaluation**。截至本盘点，项目处于“强基线、受控诊断和问题筛选”阶段；`NO_METHOD_SELECTED / novelty_authorization=NONE / new_method_validated=false`。

## 2. 已完成测试数据和证据：建议在正文用一张总表

| 证据层 | 数据与实际执行 | 可对导师说的结果 | 不能说什么 |
|---|---|---|---|
| S21 强基线 | TUM Freiburg2 desk，真实 RGB 的 300 帧、10.436629 s；CUT3R 与 TTT3R 均实际运行。 | TTT3R 的位置 ATE RMSE 为 2.847830 cm，低于 CUT3R 的 8.253931 cm。 | 不是本项目方法，也不是完整 VMem 视频。 |
| S24 更强基线 | TUM Freiburg1 xyz，798 RGB 中 796 个严格 20 ms 配对，26.572059 s；CUT3R/TTT3R/FILT3R 各实际跑完 796 帧。 | FILT3R 的 ATE/RPE 指标均最好：2.90258 cm、0.63883 cm、0.362990 度。 | 已见场景、单次运行；不能称未见测试、跨场景泛化或世界模型视频质量。 |
| S70 真正的生成基线 | VMem + 声明的 `sd-vae-ft-mse` 组件变体；A0/A1/B 三臂各 4 目标、每张 50 采样步，实际生成总 4439.151532 s。 | A0=A1 精确重放；B 平均全图 RGB MSE 0.125288663，A 为 0.131166668，预注册的“较高几何支持 A 更好”事件为 false。 | B 与 A 同时改变历史内容、顺序、槽位等；不能作单一记忆机制因果归因，也不能将 MSE 当几何正确性。 |
| S72/S74 真实相机对照 | 同一 TUM fr2_desk 实拍历史 19 到目标 20–23；638 个保存匹配。S74 固定把相机标签 20<->23、21<->22 互换。 | 对真实照片，四组配对错误标签残差中位数均上升（105.66、35.39、40.81、93.93 px），说明此观测量可区分这一个错误标签。 | 不能证明标定真实、对应点都正确，或生成图相机正确。 |
| S75 缓存 VAE 检查 | 五个真实历史输入（12/13/14/18/19）各一次实际 VAE decode，17.499437 s。 | 粗结构可还原；MSE 0.00236–0.00449，接受匹配的中位位移约 0.47–0.54 px。 | 31.52%–51.83% 原图特征匹配，且最大偏差 50–481 px；不能排除 VAE/消费者分布问题。 |
| S76 相对相机干预 | 复用 S70 A0，加固定局部 +5 度 yaw，四目标各 50 步，新增实际生成 1469.889 s。 | 保存匹配中，按预定相机变换 H 的误差中位数低于“原地不动”假设；目标 20–23 的共同视野配对差为 53.279、51.421、46.099、46.221 px。 | 目标 23 仅 6 个共同视野匹配且存在明显构图破坏；不能称相机校准、全图刚体正确或机制创新。 |
| S77 保存匹配反证 | 已有 S73 生成匹配的固定错误相机标签算术；无新图片、特征、depth、模型或生成。 | A0/B 在目标 20/21 对错误标签更差，却在 22/23 对错误标签更接近：A0 中位差 +110.83、+41.93、-41.60、-114.82 px；B 为 +111.15、+41.70、-41.06、-118.92 px。 | 这是反证：不能把“生成图服从请求相机”作为当前方法/创新依据；也不定位根因。 |
| 动态记忆下一步可行性 | Perception Test、Ego4D FHO、Phys-AD 仅做文档/metadata 屏幕。 | Perception Test 是最有希望的真实相机录制候选，但完整“早期状态—无关事件—未来结果”样例尚未认证。 | 没有完成动态视频实验、没有下载/解码该数据集的视频，也没有动态预测模型结果。 |

### S77 状态提醒

`execution_01/receipt.json` 和独立标准库复算已存在并显示 `PASS_S77_INDEPENDENT_STDLIB_ARITHMETIC`，但本盘点时目录内未找到独立的 `ROOT_RESULT_ACCEPTANCE.json`。主报告应写成“保存匹配诊断及独立算术复核完成”，并在最终排版前由主作者确认是否有后续 root 验收记录；不要把它包装成新模型实验。

## 3. 可放进导师 PDF 的图：优先顺序、图注和真实含义

这些图都应在图注显式标注“真实输入”或“模型生成”，并在正文使用一张表说明数据规模和限制。不要让视觉效果替代指标。

| 优先级 | 文件（绝对路径） | 推荐图题 / 真实含义 | 使用边界 |
|---:|---|---|---|
| 1 | `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S24_reporting_v2/s24_all_frame_errors.png` | **Figure: Strong real-data geometric baselines on TUM fr1_xyz.** 三种已有方法在全部 796 帧和 795 个相邻对上的全量曲线。 | 是真实 RGB 数据的已跑强基线；不要从曲线把误差直接归因于“记忆遗忘”。 |
| 2 | `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S70_fixed_context_generation/visuals_01/S70_all_targets_contact_sheet.png` | **Figure: Same four real references and three VMem conditions (A0/A1/B).** 每个目标的真实参考与模型生成结果；展示可见的取景差。 | 清楚标注：4 张 reference 为真实照片，12 张 A0/A1/B 为模型生成；不是一段连续真实视频。 |
| 3 | `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S76_relative_camera_response/visuals_01/ALL_FOUR_TARGET_PAIRS.png` | **Figure: Bounded response to a fixed +5 degree camera yaw.** 左右是同条件下原请求与相机转动后生成的配对图。 | 全部为模型生成图；S76 只支持有限“方向响应”，目标 22/23 的变形和低匹配必须在正文写出。 |
| 4 | `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S75_vae_history_roundtrip/visuals_01/ALL_FIVE_PAIRS.png` | **Figure: Five real historical inputs and their cached VAE reconstructions.** 左为实拍参考、右为 VAE decode。 | 右侧不是真实照片，不是视频生成；图应配 S75 的匹配率和长尾误差表。 |
| 5 | `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S72_fixed_requested_geometry/visuals_01/S72_all4_real_controls.png` | **Figure: Epipolar diagnostic on four real-photo pairs.** 真实历史 19 到真实目标 20–23 的几何观测对照。 | 仅显示抽样匹配，且目标 23 有异常；适合解释“为何不能轻易宣称相机正确”。 |
| 附录 | `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/results/S2_rgbd_qa/trajectory_and_depth.png` | **Data appendix: TUM RGB-D input and trajectory/depth QA.** | 是数据准备/QC图，不是模型结果。 |
| 附录 | `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S24_reporting_v2/s24_real_residual_photos.png` | **Data appendix: Real RGB frames at large residual locations.** | 事后用于解释性检查；不构成失效根因或独立样本。 |

### 图像文件身份（供最终打包读回）

| 图 | SHA-256 |
|---|---|
| S24 全曲线 | `8f9f2340946035bc30f23959fd9fae6d63bc0dcaf2238e8c7038e7b5d768d9d0` |
| S70 总览 | `c0561736e76d66b7bd827a25651e7cde8f8229d5b54eedbf109980d50bf07e7e` |
| S75 五组 VAE | `51bb321e881e66554a7470c7e8054da0497eb1668effb97258c1dc2085f779b9` |
| S76 四组相机响应 | `cbcde6fbf3f8a877219bab8f750e0ce16f72a2e2db5196112be1c63e71245f48` |

## 4. 不应放入正文，或必须避免的错误说法

1. 不把 S70/S76/S77 任何生成图称作“真实照片”或“真实视频”。其中仅 S70 的四张 reference、S72 的照片、S75 左侧处理后参考和 TUM 数据 QA 图来自真实拍摄。
2. 不用 `work/S15A_*`、`work/S15B_*` 的 `artificial_*`/`fake_case` 图片证明真实世界问题；它们是人工或合成诊断。
3. 不把 S75 的重建右图称作“原图”或“新视频帧”；它是已有 latent 的 VAE 解码。
4. 不为 S77 生成示意“结果图”。S77 只有保存二维匹配上的 F/极线残差算术；最合适的呈现是一个四目标数值表，且必须报告 22/23 的负差。
5. 不把 S24/S21 轨迹图写成 VMem 端到端视频质量评测；它们是已有 CUT3R/TTT3R/FILT3R 的学习式几何基线。
6. 不把 S74 对真实图片的标签敏感性、S76 的有限方向响应，写成“相机标定准确”“全图几何正确”或“创新方法成功”。
7. 不把 Perception Test/Ego4D/Phys-AD 文档屏幕、Coffee Martini 的已看前缀，写成已完成动态状态记忆实验。

## 5. 建议的导师汇报 PDF 结构（约 9–12 页，含附录）

1. **项目目标与当前位置（1 页）**：引用 proposal 的五个目标；给出一条状态线：基线/诊断已完成，机制尚未选择。
2. **真实数据与实验边界（1 页）**：TUM fr2_desk、fr1_xyz、每个阶段的数据单位、已见场景、M3 Max 本机 CPU、无远程 GPU。放输入 QA 小图或附录引用。
3. **强基线结论（1–2 页）**：S21/S24 表与 S24 全曲线。核心信息：先确认强基线 FILT3R，再谈研究空白。
4. **VMem 真实生成基线及负结果（2 页）**：S70 表 + contact sheet。说明 A0/A1 的精确重放，以及几何支持没有直接带来更低 MSE。
5. **相机/几何诊断的逐步收缩（2 页）**：S72/S74/S75/S76/S77 的一张合并表。先是真实照片观测，再是缓存 VAE，再是生成相对响应，最后给出 S77 反证。这里最重要的是结论边界，而不是把每个诊断说成贡献。
6. **创新问题与下一项可证伪实验（1 页）**：从“固定预算下，早期物体特定状态是否会被最近事件挤掉”提出假设；同时列出强简单 baseline（identity + compact state tracker）和失败条件。
7. **资源、风险与导师希望决定的事项（1 页）**：请求 GPU/存储、讨论最适合的动态真实数据和允许的基线范围；说明当前 VMem 静态多视角接口不能代替时间预测。
8. **附录（2–4 页）**：完整指标、资源用量、独立复核状态、原始图和运行证据路径。把 SHA/命令放在这里，不放主叙事。

## 6. 最少的可追溯证据清单

正文只需要引用阶段名称和简短证据编号。以下 SHA 可放附录的“reproducibility receipt”表：

| 阶段 | 主报告/接收证据 | SHA-256 |
|---|---|---|
| S21 | `docs/S21_RESULTS.md` | `fa742fa6d3bdd39a941caf7bc8042d78df56022169a14a9fc639c71f455b42ce` |
| S24 | `docs/S24_RESULTS.md` | `f05dfd63e1dd4fda9e6a46e8980c84750504301343e04dfe17d7338618858243` |
| S70 | `work/S70_fixed_context_generation/ROOT_RESULT_ACCEPTANCE.json` | `749d24f6599fbca2843c34bf9f3bd465952b3ceebd43c483dbdf49d76a3e0989` |
| S74 | `work/S74_wrong_pose_control/ROOT_RESULT_ACCEPTANCE.json` | `b041b71783fb66dd492153eb630325de4c24483d146ca0db92129e71467bfff9` |
| S75 | `work/S75_vae_history_roundtrip/ROOT_RESULT_ACCEPTANCE.json` | `853579efb5b1994f7f4a47600a8cf81fbb630dde825ff67e7c3afbeedd00a29c` |
| S76 | `work/S76_relative_camera_response/ROOT_RESULT_ACCEPTANCE.json` | `dfc73df22bf4d890587ad05c31223b8910fa2f1a467cef813827eecb4910f600` |
| S77 | `work/S77_generated_wrong_pose_control/execution_01/receipt.json` | `6092b1db7bdce3961f29ec5ba74ff9a0c946bf56de8be823012e5961d4161b9e` |

S70/S76 的生成命令、S77 的保存量算术命令都已固化在各自 `ROOT_*_BINDING.json` 或 `EXTERNAL_EXECUTION_01.json`。导师汇报中无需贴完整命令；最终可复现附录只列“冻结源哈希、数据身份、执行回执、独立复核回执”。

## 7. 给主报告作者的最终核对

- 用文档中最晚的 `ROOT_RESULT_ACCEPTANCE.json` / 独立回执更新每一阶段状态；不从旧 `RESEARCH_HANDOFF_CURRENT.md` 的历史小节抽取“当前状态”。
- 逐张图在 LaTeX 中附上来源、图像类型（real/model-generated/VAE decode/diagnostic plot）与阶段限制。
- 对 S70/S76 的图，使用原文件并按版面等比缩放；不要裁切掉 target 22/23 的失败图。
- 所有表中明确“单场景、已见数据、一次随机实现、不是外部复现”的适用范围。
- 结论页必须写出：当前最有价值的结果是一个可证伪的失败与诊断链，而不是已经验证的创新算法。
