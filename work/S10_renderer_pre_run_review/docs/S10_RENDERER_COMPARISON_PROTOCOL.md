# S10：保持原输出的 CPU 渲染工程对照（执行前草稿）

本文件在新对照执行前制定。本对照工具尚未在24个真实查询上运行正确性检查或计时，没有候选速度结果；独立人工边界检查的实际进度另见 `S10_RENDERER_EDGE_AUDIT.md`。须由根任务审查候选实现、边界 fixture 与本对照工具后，另存批准执行的冻结 JSON。不得由 runner 自动批准自身。

## 目的与已知信息

S9 已完成的组件诊断用于选择本轮工作对象。因此 S10 是基于已经看过的结果设计的工程实验。目标是比较原始 renderer 与只批量处理 polygon 覆盖/z-buffer 内层循环的 NumPy 候选，在维持原输出时的完整选图组件耗时。普通向量化按工程优化报告，不以此自称新算法创新。

只使用 S9 同一组 24 个已见查询：S7/S8 各三块、每块 query20–23，A0P0、stride8、160×160、20 历史和 4 个选图结果。S7 包含原 development 块；两个场景、六张地图和重复调用不能称新的泛化验证。S9 的历史计时只作为设计依据，**不充当 S10 的原版对照时间**。S10 会在同一进程中重新测双方。

## 输入与程序冻结

严格使用 `docs/S9_COMPONENT_PROFILE_EXECUTION_FREEZE.json` 中的同 52 文件，且新冻结 `input_sha256` 必须逐键逐值相同；旧冻结文件 SHA 固定为 `8e9c0a84cea827cf11d01f793e21ce46a9c2ce579206cc6678d3d006805fa9cd`。

这 52 文件包括 S7/S8 的 run_metadata/records，六个 stride8 案例的 A0P0 地图、来源、预测 poses、保存选择 JSON，以及 24 份原渲染 NPZ。复用冻结 S9 helper 核旧 completed gate、每案例 sealed_files、原 src SHA、地图 digest、原有序 IDs 和初始化阈值。不得扩展到其他 arms/stride，或根据正确性/速度结果换查询。

不读取 RGB/depth PNG、GT、模型权重或原模型预测 NPZ，不重新选样、建图或评分。新输出保存 52 份输入原字节快照和完整执行源码快照。旧 S7/S8/S9 源码、结果、协议与失败目录均不修改。

冻结的源码集合为 runner 的 `SOURCE_NAMES`：S9 原十项（其 helper 脚本、七 src、provenance/license）加 `scripts/run_s10_renderer_comparison.py` 和 `src/s10_vectorized_renderer.py`，共十二项。十个沿用文件还须与 S9 旧冻结 SHA 相同。协议与两份执行冻结在结束前再次校验。

## 两个方法的唯一差异

A=`original`：`RetrievalKernel.render_surfels_to_image`。

B=`candidate`：新模块 `s10_vectorized_renderer.renderer_function()` 返回的同签名未绑定函数。参数必须包括 `self, surfels, poses, focal_lengths, principal_points, image_width, image_height, disk_resolution=16`，返回同三个数组。候选不承担 observer 的 `last_render` 记录；比较 runner 为 A/B 包装**完全同一份** observer 代码。

保持候选以外的原 `get_context_info`、投票/归一化/候选配额、姿态距离、FP32 排序、NMS 阈值与全部后备分支不变。没有 S9 的六读钟 AST 插桩；计时入口是原来未插桩的完整 `get_context_info`。不以替换追踪函数或删除 NMS 获得速度变化。

每个方法有六个独立 block kernel。B 从已初始化 A 数据深复制，双方的地图、来源、history poses/K、dummy latent/embedding、query tensor、阈值初始化指纹必须一致，kernel 不共享可变实例。候选不得缓存旧查询结果、利用保存参考数组、跳过新输入计算或修改输入。每调用外检查原数据状态指纹，结束后再检查所有内存状态和磁盘 SHA。

候选的投影计算、面片遍历与遮挡顺序、16 边形、strict comparison、边界、浮点缓冲语义由根任务的实现和边界测试审查负责。本 runner 不开发候选实现，也不据有限真实回归声称覆盖全部几何边界。

## 正确性先于计时比较

第一阶段对 24 个查询均运行 A 和 B，共 48 次。该阶段不记录性能用 `elapsed_ns`。每次的三张真实返回数组须与旧保存缓冲的 shape/dtype/每个值严格相等，另比较C顺序原数组bytes，区分正零与负零；完整原 wrapper trace 和官方 decision_trace 与原封存 JSON 逐值相等，覆盖票权、候选配额、距离排序、每步 NMS/阈值放宽/后备和最终有序 ID。

只有这完整 48 次通过后才允许进入预热。失败立即结束本次执行并保留新目录；不得挑掉失败查询、放宽容差，或转为只比较最终 ID。判据继承 S9 的精确数值相等并新增三数组逐字节门，不把近似相等写成零差异；不新增浮点容差。

继承的 `np.array_equal` 本身不区分 +0 与 −0；本轮新增 C 顺序原数组 bytes 比较补齐该区别，因此强制三数组逐字节一致。每次实际内容 SHA 另存供独立复核。

随后预热和所有测量调用也逐次经过同一回归门。调用方法与验证参考彼此分开：验证仅在两次配对调用完成后进行，不进入计时区间。为复用未改诊断 wrapper，验证临时 getter 只返回**刚刚产生的当前方法结果**，不会读取参考输出代替执行；验证后恢复 getter。

## 调度、先后顺序与公平性

固定查询顺序：S7→S8，每阶段 B0→B1→B2，每块 query20→21→22→23。query_index 因此固定为 0–23。每个配对先执行两个完整调用，再做任何输出验证、hash 和保存，避免在 A 与 B 之间插入一套验证工作。

初始正确性 1 轮；完整预热 1 轮；完整测量 5 轮。每轮每查询都配对 A/B。共 168 对、336 次调用：正确性 48、预热 48、测量 240（120 对），各方法总计 168 次。

对每阶段从 0 开始编号的 round_index，使用预先规则 `(query_index + round_index) % 2 == 0` 则 AB，否则 BA。五个测量轮依次为 0–4。每轮整体 AB/BA 各 12 对；120 测量对总体 AB/BA 各 60 对。五为奇数，**单查询只能 3/2 或 2/3**，不能写成单查询完全各半；相邻查询相反，多轮自动交替。另报告 AB/BA 分组结果检查顺序影响，不按事后结果更换调度。

两方法均使用相同版本、相同线程、预初始化查询 tensor 和小型占位上下文数据。连续重复是受控软件计时负载，不估计实际产品中重复查询的频率。不得并行主动启动其他模型/实验；本机系统和用户其他进程仍可能竞争资源，不能声称已控制整台机器。

## 耗时定义与环境

用外层两次 `time.perf_counter_ns` 包住每次未插桩 `kernel.get_context_info(case['target'])`。计时包括完整相机准备、renderer、投票/候选配额、排序/NMS 和组件上下文包装。两方法的 observer 包装相同，保留其开销；不扣除时钟/调度开销。

输入解码、工厂构造、深复制、绑定、冻结 hash、输出验证、输入状态指纹、压缩与保存均在该区间外。初始化总墙钟单列。两调用之间不保存/验证；两个方法都是同样的排除规则。该包装使用小占位 latent/embedding，不能解释为完整 VMem 的上下文搬运、生成或端到端延迟。

固定本机 CPU，Python 顺序执行。Python 3.12.14，NumPy 2.3.5，Torch 2.7.0，SciPy 1.16.2；版本不符拒绝执行。Torch intra-op/inter-op 均 8，默认 FP32 距离排序、原 kernel FP64 几何 tensor。导入数值库前设置 OMP/MKL/OpenBLAS/vecLib/NumExpr 线程环境为 8，记录实际 Torch 设置与版本；环境变量不保证每个底层库实际启用八条线程。无 GPU 路径、模型构造或权重加载。

## 资源与失败保存

新输出目录创建后计总墙钟预算 600 秒，含初始化、正确性、预热、测量、验证与证据保存。Unix 墙钟 alarm 与配对前后预算检查是软守卫，原生代码可能推迟信号处理；主进程 `ru_maxrss` 上限 16 GiB，同样是检查式软守卫，不是硬 OS 内存隔离。不得突破预算后增加轮次或报告部分成功速度。

只能使用全新目录，不能在旧 S7/S8/S9 结果或保护的源码、数据、文稿目录下写入。脚本复用 S9 Python I/O 守卫，拒绝图片/权重、未列出的原 results/data、网络和子进程；只允许新输出中的写入。这不是 OS 沙箱，仍依赖已审固定代码入口。

若某调用或回归失败，完成当前配对中已经返回的实际渲染缓冲保存，保留异常、已有调用记录和未完成诊断；不把失败调用当作完整 trace PASS。已经成功返回的每调用至少保留实际三数组与返回 ID/票数/配额；正常完成时每次还保存完整官方 trace。只有全部 336 调用通过、672 份逐次 render/trace 文件齐备且原数据不变，才写 completed。部分计时不得用于速度结论。

## 逐次证据与描述性汇总

`schedule.json` 保存预定顺序。`invocations.jsonl` 每调用保存 phase、round、query_index、方法、先后位置、elapsed_ns（初始正确性为 null）、回归状态与 render/trace 的路径及 SHA。每次的 `calls/<phase>/round<r>/<query>/<method>/render.npz` 都保存实际三个缓冲，而非只保留一个复用参考；`trace.json` 保存实际数组形状/dtype/内容 SHA、返回 ID、原始票数/配额和完整 official_trace/decision_trace。最后 `call_artifact_manifest.json` 核 336+336 文件。

`run_metadata.json` 包含真实时间、状态、预算、环境、输入/源码/冻结 SHA、初始全正确性通过时刻和测量开始时刻。`comparison_source.zip` 保存所用源与冻结；`sealed_comparison_inputs.zip` 保存同 52 输入。

`renderer_transformation.json` 保存候选工厂实际生成的原/新函数原文、NumPy 版本、源码 SHA 和只替换一处内层循环的 AST 回执；这些身份必须与新执行冻结一致。该结构回执与边界回归一起支持改动范围，不代替无限输入上的形式化正确性证明。

主比值预定为全部 120 测量对的 `sum(original_ns) / sum(candidate_ns)`，先对整数纳秒求和；同时列每方法均值/中位数/范围、每查询五次中位数与其中位数比值，以及逐配对比值。分别列 S7、S8、合并、AB、BA。统计描述与原始记录保留，预热和正确性不进入速度汇总，不挑最快一轮，也不将重复当独立样本做显著性推断。是否更快及幅度必须运行后才能报告；不从本对照推出质量改进或论文新颖性。

## 新执行冻结字段

JSON：`schema="s10-renderer-comparison-freeze-v1"`，`status="approved_for_execution"`，实际 `frozen_utc`，`protocol_sha256`，`s9_freeze_sha256`，精确十二项 `execution_source_sha256` 和精确同旧 S9 的 52 项 `input_sha256`（均 project-relative 路径→SHA）。根任务可额外绑定实现/边界 fixture/独立审查证据；不得省略正确性审查后直接自行批准。

CLI：`run_s10_renderer_comparison.py --s7 <旧S7目录> --s8 <旧S8目录> --s9-freeze <旧S9冻结> --protocol <本协议> --freeze <新审核冻结> --output <全新目录>`。本准备阶段仅运行 help、语法和纯静态调度/合同检查。

```s10-comparison-json
{
  "schema": "s10-renderer-comparison-v1",
  "stages": ["S7", "S8"],
  "blocks": [0, 1, 2],
  "queries": [20, 21, 22, 23],
  "stride": 8,
  "arm": "A0P0",
  "width": 160,
  "history_count": 20,
  "context_count": 4,
  "correctness_rounds": 1,
  "warmup_rounds": 1,
  "measured_rounds": 5,
  "methods": ["original", "candidate"],
  "query_order": "stage_then_block_then_query",
  "pair_order": "AB_if_query_index_plus_round_index_is_even_else_BA",
  "device": "cpu",
  "torch_threads": 8,
  "torch_interop_threads": 8,
  "versions": {"python": "3.12.14", "numpy": "2.3.5", "torch": "2.7.0", "scipy": "1.16.2"},
  "wall_budget_seconds": 600,
  "peak_rss_budget_bytes": 17179869184,
  "resource_limit": "soft",
  "exact_output_gate": true,
  "raw_pixels_allowed": false,
  "gt_allowed": false,
  "model_loading_allowed": false,
  "saved_render_for_every_completed_call": true
}
```
