# S9 已见查询的组件耗时诊断：执行前协议

本文只规定准备工作与后续一次运行。只有根任务完成独立审查，另写 `status=approved_for_execution` 的执行冻结文件后才能运行。编写时没有产生耗时结果，也不据此预言瓶颈或加速空间。

## 问题与结论边界

测量现有 CPU 检索实现的时间主要花在 surfel 渲染、票数/候选配额，还是姿态距离排序与完整 NMS。该诊断不开发或测试增量算法，不改变选图规则。

固定使用已经查看和分析过的 S7、S8 两次运行。每次运行均取 stride8、A0P0、三个块、每块最后四个查询，共 **24 个已见查询**。S7 的 B0 原为 development，这次也纳入软件诊断。它们不是新场景测试；五次重复也不产生 120 个独立查询。不得把本次耗时称为完整 VMem、视频生成或模型推理耗时，不比较两个场景的质量优劣。

## 固定输入

- `results/S7_event_replay` 和 `results/S8_event_replay_v2`；两者必须已有 `status=completed`、`phase=complete`。
- 每个阶段的 `run_metadata.json`、`records.json`。
- 每块的 `block{b}_stride8/A0P0.npz`、`A0P0_sources.json`、`predicted_poses.npz`、`prediction_only_selection.json`，及 query20–23 的 `query{q}_A0P0_render.npz`。
- 共 52 个文件，执行前逐一绑定 SHA。每个案例文件还必须与旧运行 `sealed_files` 的 SHA 相同。输入原文件保持不变；新输出保存同字节快照。

只解码上述已经保存的地图、预测相机位姿和渲染缓冲 NPZ。不得加载原 RGB/depth PNG、GT 轨迹、模型权重、原始预测模型 NPZ 或其他案例；不重新选样、建图、优化几何或测量支持率。读取 records 中的已保存 ID 用于核对，不重算其中的质量指标。

初始化沿用未改的 `s6_memory_bridge.make_selector`，历史仅前 20 帧，width=height=160，4 张上下文图。继承原 focal×0.65、居中主点、初始 NMS 阈值和姿态转换。保存的 map/sources 必须重建为相同数组/计数/来源及相同 memory digest。上下文 latent/embedding 继续使用该组件包装器的小占位数组，因此包装部分不是完整模型中的搬运成本。

七个沿用的 `src` 文件还须分别匹配 S7 与 S8 旧元数据中的运行时源码 SHA，不能仅在新的 S9 冻结中给改过的实现重新命名为原实现。

## 计时口径

使用 `time.perf_counter_ns` 测量主进程墙钟时间。只在原 `RetrievalKernel.get_context_info` 的 AST 中插入六次读钟与对应计时变量；剥离这些节点后 AST 必须与冻结原方法完全相同。保存原方法、插桩方法及其 SHA。不用另写的追踪实现替代原 NMS 做性能测量。

| 项目 | 开始、结束与包含工作 |
|---|---|
| `renderer_ns` | 包围原 `render_surfels_to_image` 调用：包括 surfel 数组构造、几何变换、可见性判断、面片覆盖和深度缓冲；也包括既有 ObservedKernel 的返回值记录。每次调用都新执行。 |
| `votes_allocation_ns` | 包围原 `process_retrieved_spatial_information`：可见像素筛选、沿来源的票数累计/归一化、候选配额分配及返回排序；不将配额成本藏进其他项。 |
| `sort_nms_ns` | 从原 `candidates=[]` 到 `context_time_indices` 产生：包含按配额展开候选、姿态距离、原默认 FP32 argsort、完整阈值 NMS/放宽/后备逻辑及最终索引 tensor。当前调用配额 n=min(14,来源数)，每个入选来源仅出现一次；不将展开语句结构误写成本轮有实际重复。 |
| `total_ns` | 一次插桩 `get_context_info` 调用的外部墙钟时间；不含预先构建的查询 tensor，不含读文件与验证。 |
| `other_ns` | `total_ns` 减上述三项；包括相机平均/变换、K 准备、上下文包装、方法调用和插桩间隙开销。不得称纯算法第四组件。 |

总时间是插桩后时间。计时标记、Python 调用及既有 observer 都有开销；不做事后减开销，不把这一轮称为未插桩基线性能。`sort_nms_ns` 已覆盖距离计算，不仅是一个 sort 调用。

计时外工作：库导入、输入 hash/快照、数组解码、内存对象与 kernel 初始化、阈值初始化、查询 tensor 构造、每次输出回归、追踪、文件保存。初始化墙钟另记，不混入三个组件。总运行预算仍包括这些工作。

## 调度与环境

同一进程、同一 CPU，Python 顺序执行。固定顺序为 S7→S8；每阶段 B0→B1→B2；每块 query20→21→22→23。先完整预热 1 轮，再完整测量 5 轮，合计 144 次原始检索调用，其中 24 次预热、120 次用于描述性统计。顺序预先固定，不按已见耗时重排，不选择最快一次，不增补重复直到获得好看的结果。

使用现有本机环境；Torch intra-op 与 inter-op 都固定为 8，默认 dtype 必须为 FP32，以保留原排序行为；kernel 几何 tensor 仍为 FP64。在导入数值库前设置 OMP/MKL/OpenBLAS/vecLib/NumExpr 的线程环境为 8，并记录实际 Torch 设置、Python/NumPy/Torch 版本和平台。环境变量不等于已验证所有底层库实际启动八条线程，因此不作后者保证。没有 GPU 计时，也不调用模型构造或加载。

不得同时主动启动另一项计算任务；记录运行时由外部调度可能产生的资源竞争属于本机环境局限。无需为此重新运行旧模型或其他实验。

## 零输出差异门

每个预热和测量调用结束后，在计时外检查三个渲染数组的 dtype/shape/每个值与封存 NPZ 一致。比较原 wrapper 完整 `official_trace`（票权、候选配额、有序 ID、覆盖率、阈值等），并调用未改 `decision_trace` 与封存 official 全追踪逐值相同，包含候选展开、FP32 距离、完整排序、每次阈值比较与 fallback。

为复用未改 wrapper 的诊断字段，验证期间临时让其 getter 返回**刚刚这次执行的结果**；不会重渲染，也不会把封存参考结果当成执行结果。该临时包装不进入任何计时区间，结束后恢复原插桩方法。

通过标准严格为数组逐值相等和 JSON 数值/结构相等。不得将相近但不等称为“零差异”。旧独立审计的 `atol=1e-9`、`rtol=1e-10` 仅作为固定诊断背景，不用于放宽本次门槛；失败后不得自动放宽或把近似通过写作完全一致。

每次都通过才保留该条为完成记录。任一差异立即结束，保存实际不一致渲染/追踪以及已有计时，标记失败；部分数据不能用于宣称瓶颈已验证。最后再次核输入和所用源码 SHA，核内存地图 digest 未变。只有完整 144 调用和全部回归通过才写 `status=completed`。

## 资源预算与失败保留

从新输出目录创建后的运行起点计，总预算 300 秒，包含初始化、预热、测量和校验。Unix 墙钟 alarm 与每查询前后检查共同守护。原生库可能延迟 Python 信号处理；因此这是软守卫，不称硬实时限制。主进程 `ru_maxrss` 峰值上限 16 GiB，每次查询前后检查；没有硬 OS 内存上限，也不包含操作系统其他进程的内存。

输出目录必须全新，不能位于旧 S7/S8 目录或源码/数据/文稿目录内。失败目录、部分 JSONL、异常与真实时间保留，不覆盖重试。脚本不联网、不启子进程；Python I/O 守卫禁止原 data 文件、非清单 results、图像/权重读入，以及输出目录外的写入。这不是 OS 沙箱；范围保证同时依赖已审源码与固定入口。

## 输出与呈现

`run_metadata.json` 记录真实开始/初始化/完成时间、状态、预算、环境、源码/输入 SHA、完整顺序和局限；`profile_source.zip`、`sealed_profile_inputs.zip` 保留源与输入快照；`timings.jsonl` 保留全部完成调用及 warmup 标记；每查询的初次回归证据、插桩 AST 原文保存。

完成后 `summary.json` 分别报告 S7、S8、合并组的描述性均值/中位数/最小/最大/总和，以及用时间总和计算的组件份额；另外列出每查询五次的中位数。不得把重复次数用于独立样本显著性推断，不从耗时占比直接推出可实现的加速比。耗时必须先测后报。

## 执行冻结格式

另存 JSON，不在本准备阶段生成 `approved_for_execution`。字段：`schema="s9-component-profile-freeze-v1"`、`status="approved_for_execution"`、实际 `frozen_utc`、本协议 `protocol_sha256`、`execution_source_sha256`、`input_sha256`。后两项均为 project-relative 路径→SHA；源码键必须精确等于 runner 的 `SOURCE_NAMES`（含本 runner、七个沿用源文件及 provenance/license），输入键必须精确等于 `expected_inputs` 的 52 文件。冻结必须早于运行，脚本拒绝缺失/不匹配冻结。

运行入口：`profile_s9_components.py --s7 <S7目录> --s8 <S8目录> --protocol <本协议> --freeze <审核后冻结JSON> --output <全新目录>`。本机正式路径限定为上述两个旧结果目录，不接受替换其他实验来扩大范围。

```s9-profile-json
{
  "schema": "s9-component-profile-v1",
  "stages": ["S7", "S8"],
  "blocks": [0, 1, 2],
  "queries": [20, 21, 22, 23],
  "stride": 8,
  "arm": "A0P0",
  "width": 160,
  "history_count": 20,
  "context_count": 4,
  "warmup_rounds": 1,
  "measured_rounds": 5,
  "order": "stage_then_block_then_query",
  "device": "cpu",
  "torch_threads": 8,
  "torch_interop_threads": 8,
  "wall_budget_seconds": 300,
  "peak_rss_budget_bytes": 17179869184,
  "resource_limit": "soft",
  "exact_output_gate": true,
  "diagnostic_atol": 1e-9,
  "diagnostic_rtol": 1e-10,
  "raw_pixels_allowed": false,
  "gt_allowed": false,
  "model_loading_allowed": false
}
```
