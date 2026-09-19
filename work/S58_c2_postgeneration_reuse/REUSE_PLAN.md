# C2 V9 生成后的最小复用路线

**本文件只做接续准备，不代表 V9 已完成，也不授权提前读 C2 像素。** root 于 2026-09-08T16:45:42.636402Z 启动 V9，执行会话 43876、supervisor PID20689；此处只读已封存源码、清单、启动记录和 C1 已完成链的文本。尚无本计划认可的 V9 完整终态。未来终态、档案、读回和评分 SHA 均未填写，不用虚构值或旧 C1 值代替。

## 先固定已经存在的身份

| 对象 | 当前真实值 |
|---|---|
| V9 工作目录 | `work/S47B_c2_confirmation_generation_v9` |
| V9 输出目录 | `results/S47B_C2_confirmation_generation_v9` |
| V9 manifest | `review_attachment_01/manifest.json`，SHA `caa6d7c04d7784e731165e05c07ff4e358322d14c8e76f08c2337b7f4dc641ac` |
| manifest schema/status | `s47-c2-confirmation-two-batch-v1` / `FROZEN_C2_BASELINE_CONFIRMATION_TWO_BATCH_EXECUTION` |
| C2 输入 | `living_room.jpg`，seed44，输入 SHA `e9d718849d2ddbe5dda7ed3fa80df7d93e99f2d509b07a46019818c2e188d278` |
| 源码域 | C1 为 218；V9 为 **219**。214 项公共路径保持，C1 的四个行专属项换成 C2 的五个，其中新增 `create_launch_authorization.py`。 |

V9 的五个行专属 SHA、C1 可复用源码与模板的当前完整 SHA 均在 [SOURCE_IDENTITIES_READ.json](SOURCE_IDENTITIES_READ.json) 指向的真实清单/源码中。只读清单不是源码审查 PASS；无需给未来输出提前生成哈希模板。

## 固定执行顺序

1. **真实外部退出与 V9 终态核验。** 保留活动会话直到实际返回；先读外部观测回执、V9 内层 parent/worker、commit/watchdog 与档案/trace 元数据，沿已有要求完成不同作者终态核验。任一缺失/失败保持失败，不评分，不重用 V8 或 V9 已消耗尝试。
2. **保存量读回并复核结果。** 复用 S45→S40 v3.3 reader 与监督器，确认原两批 `1→5→9`、每批 50 步、第一批生成历史被第二批实际选择和消费、完整身份与档案。它会哈希/映射保存量和像素身份，但不看图、不算画质。
3. **相机数值条件核对并复核结果。** 复用 S45B V12 的实际完整正向路径，比较原始请求 `c2w/K` 与计划及 cache/batch 绑定，保持原 `1e-6` 容差。该项只证明保存的输入相机条件；不证明画面运动或光学正确。
4. **唯一主评分、结果复核、不同数学实现复算。** 用相机结果复核确认的九个权威 RGB 身份绑定 S46 模板，经原有不同作者源审和真实评分前未看图声明，执行薄 wrapper 一次；随后用独立 kernel/I/O 复算全部原定数值并复核。
5. **评分后完整九帧导出与看图。** 复用 C1 导出器的逐字节 PNG 验证和 3×3 全帧展示，ID0 标真实输入预处理，ID1–8 标模型生成。保存首次看图时点与所有帧；不挑图。
6. **单独汇总 S42 三行。** 仅在三行均技术有效后填真实完整 cohort；B0/C1 已为 false，因此原至少 2/3 事件逻辑不可达，C2 结果不得改变原阈值或分母。任何读回/数值无效都保留无效状态；不是补一个事件布尔值就可完成 cohort。

## 必需的少量适配

所有适配另放新行目录，不改 C1、S40、V8、V9 原文件或已使用票据。保持 `work/<行目录>` 的原目录深度，否则现有 `ROOT=HERE.parents[1]` 等定位会错；独立复算子目录保留原层级。以下是身份/兼容性修改，数值算法不改。

| 已完成的源 | C2 最小修改；保留的实现 |
|---|---|
| [S45 readback.py](../S45_c1_result_readback/readback.py)、[supervise_readback.py](../S45_c1_result_readback/supervise_readback.py) | 行目录/输出/manifest、五个 C2 pins、C1 schema/status→真实 C2 字段；在 S40 `run()` 的唯一源码数量断言把 218 改为 219，不能假装纯标签替换。继续证明其余派生 AST 与固定 [S40 v3.3 reader](../S40_result_readback/readback.py) 相同；保留 `Reader.descriptor/tree/metadata/array`、`trace_sequence` 与全部跨批字节比较。监督器的 `validate_generation_inputs` 适配下述 V9 外层终态，而非忽略它。 |
| [S45B V12 camera_guard.py](../S45B_c1_numeric_camera_guard_supervised_v12/camera_guard.py)、[supervise_camera_guard.py](../S45B_c1_numeric_camera_guard_supervised_v12/supervise_camera_guard.py) | 只改行路径、manifest/source/上游读回身份、固定标签、真实作者与绑定记录；`verify_upstream` 对应 C2 的 derivation_policy.row/schema/status。复用 `selected_event_captures`、`CameraTensorStore`、`decode_selected_cameras`、`expected_pose`、`evaluate_numeric_guard` 及现有监督完整路径。原 yaw `[0,1.25,2.5,3.75,5,3.75,2.5,1.25,0]`、K 恒定和容差保持。只读取相机描述符允许的小数组，不为这一步打开 RGB。 |
| [S46 模板与 bind_identity_only.py](../S46_c1_blind_scoring_preparation/bind_identity_only.py) | 模板固定行身份改为 C2/living_room/seed44；新的归档 tensors、score attempt、scorer、源审、相机复核路径及 SHA 全来自实际完成记录。保留 binder 的结果字段拒绝、九个 ID、八个上游 record、只填身份功能。`frozen_math` 不含行名，故其子树和 SHA `9bee0abe9392e04e061adb7cf8b39297d7730e7045ed856486f1e03ee8d82812` 可以原样保留。 |
| [S46 wrapper V3](../S46_c1_blind_scoring_wrapper_v3/score_c1_blind_wrapper.py)、[主 kernel](../S46_c1_blind_scoring_preparation/score_c1_blind_candidate.py) | 更新 `FIXED_UPSTREAM` 为真实 C2 终态、读回、相机结果审查；同步模板/schema/行/输出与源码 pins，保持 `validate_pixel_descriptors`、`validate_contract`、`validate_numeric_review`、`validate_blindness`、同 FD 消费与发布。kernel 仅改 C1 的输出行/状态标签，不动计算；其 `cohort_status=INCOMPLETE_C2_STILL_REQUIRED` 不能机械保留到 C2 或直接改成成功，C2 行结果应明确“待三行技术有效汇总”。主 kernel CLI 仍只做合成自检，正式评分必须走 wrapper。外部调用复用 [C1 固定非阻塞锁调用](../resumption_20260908/run_s46_c1_reviewed.py) 的单次模式，不能绕开锁。 |
| [独立 kernel](../S46_c1_blind_scoring_preparation/recompute_c1_independent_candidate.py)、[薄 I/O](../S46_c1_blind_scoring_preparation/C1_independent_recompute/recompute_c1_io.py) | 保留独立加减乘求和顺序、精确 floathex/计数/事件比较；只改 C2 行标签、主分数/contract/binding/九帧路径及新 source SHA。仍不导入主 scorer/wrapper；沿原 binder 的 recompute 模式绑定真实已封存主分数，再以外部独立源审绑定，避免 review 与 binding 自循环。旧 kernel/source SHA 是历史基线，行标签改后需计算新 whole-file SHA，不能冒用旧 hash。 |
| [export_c1_visual_qa.py](../../scripts/export_c1_visual_qa.py) | 仅改实际已封存 C2 score/report/contract 身份、输出路径和 seed44/行标题；保留按九个权威 raw RGB 身份读图、逐帧 PNG 解码字节相等和不裁数据的全帧接触表。评分与复算前不执行。 |

源审只看这批明确差异与原实现复用证明；如有必要运行原有有限普通自检一次，不扩出新版本链、测试矩阵或治理框架。旧 C1 审查可作为复用依据，不能直接授予变更后的 C2 路径与 SHA 执行权。

## V9 终态比 C1 多出的兼容性边界

C1 的 `execution_01/receipt.json` 是其外部 launcher 的完整终态。V9 同名文件只是**派生 parent 回执**；[V9 launch_generation.py](../S47B_c2_confirmation_generation_v9/launch_generation.py) 的 `_run_supervisor` 还要求以下既有证据，接续器必须保留这些要求，而非重新设计一套门：

- `work/resumption_20260909/C2_V9_EXTERNAL_LAUNCH/receipt.json` 的真实外部 returncode=0，结合原开始记录；不能只看 parent 内部 returncode。
- `execution_01/supervisor_terminal_commit.json`：schema `s47-c2-external-supervisor-terminal-commit-v2`；status `COMMIT_CANDIDATE_REQUIRES_OUTER_RETURN_AND_NO_ROOT_FAILURE`；outcome `RUN_RETURNED_PENDING_INDEPENDENT_REVIEW`、parent_returncode=0、`standalone_success=false`；manifest/launcher、parent/worker/watchdog SHA、execution/output 身份逐项对应实际文件。
- 同目录 `watchdog_receipt.json`：`WATCHDOG_CONFIRMED_REGISTERED_DESCENDANTS_GONE`，cleanup_complete、all_registered_descendants_gone、supervisor_completed_protocol、canonical_execution_identity_at_close 均真，supervisor_liveness_lost=false，worker returncode 与实际 worker 相同且为 0。
- V9 工作根的 `.execution_01.supervisor_failure.json` 和 `.execution_01.watchdog_failure.json` 都缺席，原路径身份现场核实；只有 provisional 或 leftover commit 都不能通过。
- parent 的实际 schema/status 是 `s47-c2-confirmation-launch-v1` / `C2_BASELINE_EXTERNAL_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW`；worker 为 `s47-c2-confirmation-worker-v1` / `C2_BASELINE_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW`。保留一次 factory/一次 full-resource、worker_spawned、source_unchanged、无 limit_exceeded/遗留后代等原检查。
- worker 的 `scientific_consumption_binding.all_required_resources_consumed=true` 且 output_identity 对应；loading 使用 `PASS_S47_C2_DECLARED_VARIANT_COMPONENT_LOADING_ONLY`；完整 `ARCHIVE_COMPLETE`、两批闭合 trace、summary 的实际 SHA 仍由 worker 回执绑定。

对应既有只读实现是 [generation_gate.py](../S47B_c2_confirmation_generation_v9/generation_gate.py) 的 `read_frozen`、`require_successful_prepare_bundle`、`require_published_attachment`、`require_successful_authorization_attempt`、`require_launch_authorization`、`LaunchControlLease.validate`；终态项来自 launcher 的实际收尾分支。复核这些已发布材料即可，不重跑正式 gate/full-resource/model/launch，也不重新创建授权。读回 terminal binding 应保留上述 C2 外部观测/commit/watchdog 引用作为既有 V9 完成证据，再进入原 S45 读回链。

## 数值与盲态不能顺便改变

主比较仍是 ID0 对 ID8、M_outer4 四个原定 192×192 区域，总 147456 像素/442368 RGB 标量；uint8 转 float64 后每区除 255，再按原序求平方和与全域平均；严格 MSE>0.01，相等不算事件。R1–R4、full-frame、1_7/2_6/3_5 均只作原诊断，不能替代主比较。保留原复制退化检查。独立复算精确核主项加八个诊断记录及 event/equality/row_status，不新增事后容差。

C2 评分前声明只描述当前真实访问历史：V8 已进行过 partial runtime，但不能据它伪称 V9 结果已见或未见；V9 的任何读取须据实际记录区分哈希/数值与人看图。B0/C1 已看图、已评分，不能重新赋予它们盲态。若 C2 在评分前已被实际展示，应如实保留偏离，不填写虚假 blindness PASS。

S57 的原观察器已被另一作者发现漏掉 pipeline 的 y/z 轴转换，root 正在安排有源码依据的独立纠正。**本计划不改冻结 S57，也不采用其旧标签作 C2 有效性条件。** S45B 的请求 pose/K 数值核对与渲染画面坐标分析是不同对象；不得把 S57 的修正擅自写入原相机数值计划或 S42 评分。

本子任务到此结束：仅交付最小复用清单和当前真实源码身份；没有 C2 payload 读取、模型、执行或绑定创建，没有 V9/S57 修改。root 负责后续实际终态、有限源码适配、精确绑定和主账。
