# S11 既有地图变体的渲染正确性回归协议（待审查执行稿）

记录：2026-09-05 21:53:46 UTC。S10 已完成及交付。本稿只准备更宽的既有输入回归，没有冻结新执行，也没有执行候选、读入新数组或进行计时。待根任务及独立审查确认后，另写执行冻结再运行。

## 问题和范围

检查冻结的 S10 NumPy 批量像素循环在更多**已有**地图变体上是否与原输出完全相同。不开发候选、不改变原排序、投票或 NMS；也不再次测速度。

完整条件域固定为 S7、S8 两个来源 × 各三块 × 两档 stride（8、12）× 四地图（A0P0、A0P1、A1P0、A1P1）× 四查询（20–23），共 192 条原 renderer 条件。仍只有两个物理场景、24 个相关查询，S7 含开发数据；地图变体与重复查询不是新场景、新独立样本或未见泛化。

其中 stride8/A0P0 的 24 条已由 S10 成功运行并逐次核验。本阶段绑定其初始 correctness/candidate 的 24 份真实数组与 trace，同时封存 S10 全部 336 次调用的记录和 672 文件，核成功状态、目录范围、清单及两份通过审计。这 24 条不再执行 renderer。新执行是剩余 **168 条 candidate 完整 get_context_info，分属 42 地图**，每条一次、零预热、零 original renderer 调用。

## 固定源、环境和加载

新入口 `scripts/run_s11_renderer_regression.py` 内含 S11 loader。其余 12 个 S10 源文件全部与原执行冻结相同，不修改任何旧 helper。候选 SHA 固定为 `3e079d0bbbaed962b24bce599a5cf7198b6bbc2891ac3c91761f4ea5c4f0e521`；S10 执行冻结 SHA 固定为 `db22d71b37c9a44ece98008f8ff422886a7bdc604efd79d6f0000b55f1532204`。

loader 仅拓宽 S9 的地图/stride 路径：从保存的地图、来源、24 帧预测相机和原选图 trace 重建同样的 Memory/Surfel 与 selector，逐数组核地图加载的 shape/dtype/C bytes 和 memory digest。每图仍 20 历史、4 只读查询、width160、原相机坐标转换、原 NMS 初始阈值及原小型占位上下文数组。完整 get_context_info 必须保持原函数身份；仅绑定冻结候选，并复用 S10 相同 observer。通过未改 S9 validate_output 产生完整核对 trace，不再调用 renderer。

固定本机 CPU、Python 3.12.14、NumPy 2.3.5、Torch 2.7.0、SciPy 1.16.2；Torch intra/inter-op 均 8 线程，环境线程变量设 8，默认排序 dtype 为 float32，原内部几何路径不变。原 S9/S10 helper 的加载、诊断与 guard 复用不代表 S11 是此前已审核的执行；S11 新 loader/域由新审查负责。

## 冻结及可访问输入

CLI：`--protocol --freeze --output` 三项必填。S7/S8 与 S10 历史来源目录固定为项目内既有目录，不开放重新选样或替换来源。

执行冻结必须在运行开始前存在，schema 为 `s11-renderer-regression-freeze-v1`，status 为 `approved_for_execution`，并含：

- `frozen_utc`、`protocol_sha256`、固定 `s10_freeze_sha256`。
- `execution_source_sha256`：精确 13 个源码/许可项，即 S10 原 12 项加新 S11 入口。
- `input_sha256`：精确 316 文件。两 run 的 metadata/records 共 4 文件；12 个 case 各含 4 地图、4 来源、1 predicted_poses、1 selection、16 原渲染，共 26 文件。先核 SHA 及原 case 封存，再允许 NPZ 解码。
- `s10_evidence_sha256`：精确 682 文件，即 S10 8 个顶层记录/归档、全部 672 调用文件、两份成功审计 verification。S10 的 52 原输入必须与新 316 文件的相应子集完全相同。
- 非空 `review_evidence_sha256`：根任务指定的新执行前审查及设计证据，只读 SHA 绑定。

封存完成后才导入 NumPy/Torch、读取 NPZ、绑定候选。先重新核 24 条继承输出与原 S7/S8 参考，再初始化和执行 168 条新增条件。旧完整 records 是封存证据，只消费本回归所需选图字段，不打开原 GT 轨迹、不解码 RGB/depth PNG、不重新计算测量、不运行模型或下载。

复用 S9 Python I/O guard 禁网络、子进程、原图/权重、未列举 data/results 文件读取及新输出之外的写入。这不是操作系统沙盒或全新环境。执行末复核全部输入、源、继承证据、审查文件和协议/冻结 SHA 不变。

## 固定调度、输出门和失败处理

顺序为 stage → block → stride → arm → query。完整 schedule 保留 192 条及 inherited/new 标记；新增调用跳过且仅跳过 stride8/A0P0，固定 168 条，无失败后选样、重复尝试、热身或筛除。

每条新增条件调用前保存初始状态身份；调用后先保存实际三个 render 数组与原始返回有序 ID/票权/次数，再调用完整诊断。所有数组与各自封存原参考要求 shape、dtype、C 顺序字节相同，**包括正负零，零容差**。official_trace、完整 NMS 步骤和有序 ID 逐值相同，不只比较最后照片集合。每条成功 trace 保存真实 state_after，逐项与初始 state_identity 比较；末尾再检查全部实例。

新输出目录在出现时即拒绝，禁止放入旧结果/原源码、数据、文档目录中。任何门失败立即终止，实际数组、已写 trace、failure.json、invocations 和失败 metadata 保留；失败目录不覆盖，不输出完整覆盖成功。若 renderer 已返回而后续 selector 失败，也保存该次实际数组；没有返回时不把上次数组当作本次输出。

输出包含：`schedule.json`、`inherited_coverage.json`、168 次 `calls/<label>/render.npz` 与 `trace.json`、`invocations.jsonl`、`initial_state_identities.json`、`renderer_transformation.json`、完整 192 条 `coverage.json`、336 新调用文件清单、无耗时指标的 `summary.json`、`run_metadata.json`。源/协议/执行冻结、316 输入、682 继承证据、新审查文件分别归档到四个 ZIP；每个 ZIP 写入后核精确成员、CRC、SHA 和原件不变。

## 资源与结论门槛

总运行预算 600 秒、峰值 RSS 16 GiB，通过 wall alarm 与间隔 RSS 检查执行软守卫。只保存用于预算的总 wall 时长与实际 UTC、峰值；**不加单次性能时钟，不输出速度或比值**。其他本机进程不受本脚本控制。

完整 PASS 必须是继承 24 条逐字节再核通过、新增 168 条实际调用全部通过、192 条 coverage 无缺失/重复、所有输入与状态不变。结果只扩大冻结候选对已有地图变体的软件一致性证据；不证明所有输入等价、不证明科研创新、不宣称完整 VMem、视频质量或速度结果。根任务计划的来源变化补充设计单独列域和冻结，不在本 192 条中伪造或混入额外条件。

## 最小准备检查

只执行语法/--help/纯调度与路径计数检查；不得在执行冻结前加载任何实际 NPZ、执行候选、模型或性能实验。准备记录与执行冻结另存，不能把准备检查称为真实数据通过。

## 机器合同

```s11-regression-json
{
  "schema": "s11-renderer-regression-v1",
  "stages": [
    "S7",
    "S8"
  ],
  "blocks": [
    0,
    1,
    2
  ],
  "strides": [
    8,
    12
  ],
  "arms": [
    "A0P0",
    "A0P1",
    "A1P0",
    "A1P1"
  ],
  "queries": [
    20,
    21,
    22,
    23
  ],
  "width": 160,
  "history_count": 20,
  "context_count": 4,
  "full_conditions": 192,
  "inherited_conditions": 24,
  "new_candidate_invocations": 168,
  "new_candidate_maps": 42,
  "inherited_rule": "stride8_A0P0_all_24_from_S10_correctness_candidate",
  "order": "stage_then_block_then_stride_then_arm_then_query",
  "device": "cpu",
  "torch_threads": 8,
  "torch_interop_threads": 8,
  "versions": {
    "python": "3.12.14",
    "numpy": "2.3.5",
    "torch": "2.7.0",
    "scipy": "1.16.2"
  },
  "wall_budget_seconds": 600,
  "peak_rss_budget_bytes": 17179869184,
  "resource_limit": "soft",
  "exact_C_bytes_gate": true,
  "exact_complete_trace_gate": true,
  "warmup_calls": 0,
  "performance_timing": false,
  "original_renderer_calls": 0,
  "raw_pixels_allowed": false,
  "gt_allowed": false,
  "model_loading_allowed": false
}
```
