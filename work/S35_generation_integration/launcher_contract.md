# S35 原两批生成的有限外层启动器

状态：仅源码准备，尚未执行启动器、metadata gate、人工接口测试或任何生成。本文不改变原 S20 控制、不提供替代权重、不把准备通过当成模型可用。`archive_outputs.py` 保持既定原件。

## 调用及唯一执行路径

正式运行前，root 将本脚本及 gate/factory/integrator/archive/S20 源码纳入同一冻结 manifest；来源与审查内容由 `resource_gate.py` 的最终合同约束，不另复制一份易漂移的资源白名单。CLI：

```text
"/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/.venv-cut3r/bin/python" -B "/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S35_generation_integration/launch_original.py" --manifest ABSOLUTE_FROZEN_MANIFEST --manifest-sha256 EXACT_SHA --execution-directory ABSOLUTE_NEW_CALLER_DIRECTORY
```

参数中的示意路径/SHA不是可运行的资源，不创建虚假的成功 manifest。`execution-directory` 和 manifest 指定的 `output_root` 必须是不同的全新目录；后者的父目录须已存在。输出绝不续写旧实验。终态后无重试、续批、换模型或自动扩预算。

父进程只有标准库顶层 import。先核 manifest 冻结 SHA、固定 runtime、launcher 自 SHA，再调用共享 `check_manifest(..., metadata_only=True)`：检查所有必需组件路径/大小/身份字段、VAE 来源元数据、完整源码域、小源码 SHA、输入/config/审查路径等。它不读权重或图片字节，不加载科学库或模型；审查回执正文和真正全部内容 SHA 留给子进程。缺件或任何前置失败写 `NOT_READY_BEFORE_SCIENTIFIC_IMPORT`，不创建 worker、不把此状态称 PASS。

仅 metadata 条件齐备后，父进程使用已安装 psutil 监控，不安装/下载新依赖；固定原虚拟环境启动 fresh 子进程，固定 PYTHONPATH 次序为当前接线目录、ROOT/src、S20 overlay、S17C overlay。隐藏的 worker 入口还核原父PID、manifest/源码SHA、output_root对应的本次 launch ticket，拒绝误把内部入口直接当无外控运行器。子进程再由原 factory 加入 S20 隔离源码/CUT3R 路径；同一个 worker 运行初始化、左转、右转，第二批不重新加载/播种。

子进程先调用且只调用一次完整 `check_manifest`。全部源/输入/审查核心绑定先核，原五组件逐份完整 SHA 一次核；通过前不 import TraceWriter/NumPy/Torch/PIL/integrator/runtime。之后 `validate_gate` 只复核小源码/manifest 与权重 stat，不重复哈希 GB 权重。完整 SHA 开始、加载、初始化及第一批都计入第一阶段 1800 秒。

`run_original(create_runtime, *, resource_gate, check_resource_gate, create_trace, create_archive, source_manifest, evidence_kind='recorded_execution')` 使用实际稳定签名；三个 factory 均接 validated gate。source_manifest 仅显式指定实际 S20 pipeline 路径及完整冻结 source_identities。Trace 写 `output_root/trace`，完整 archive 写 `output_root/archive`，factory 使用原 `output_root/runtime_cwd`。archive 必需名称只核实际供给的基础产物覆盖，不能替代原始数值、模型、NMS或质量的独立核验。

原入口正常返回后，保存实际 `observation_summary`，调用 archive 的 COMPLETE 关闭并绑定 trace SHA。原 trace 已由 integrator 关闭。出现异常尽力保留 failure/archive 前缀，worker 写非零退出和终态；运行时 factory 失败也归入部分失败。原对象不序列化到 worker JSON，完整张量/PIL 由被动 archive 接线保存，不追加模型/编码/采样/渲染。

## 资源预算与真实批次边界

- 原 CPU FP32、8 线程；同 worker 两批，每批 1800 秒，累计 3600 秒；第一批包括完整内容校验和加载。启动器无额外科学计算。
- 每 0.5 秒轮询整个已发现进程树 RSS，45 GiB 上限；跟踪 PID 与创建时间，已发现的重父化子进程仍计入。读取失败不按 0 内存放行，而终止并记失败。
- 启动前与每轮检查输出盘剩余空间至少 10 GiB。该门只避免低于此余量，不是预计完整档案必能放下的承诺。
- 只有原 `trace/events.jsonl` 的真实第一条合法 `batch_complete` 才切到第二预算：增量校验 seq/previous/SHA、记录模式、manifest 身份、对应原 batch_begin/cache_commit/map_commit，并要求真正保留 ID1–4、history5。批 ID 可为任意原字符串，不假定它叫“1”。第二批对应 ID5–8/history9。stdout、样本返回、archive close 都不能续时。
- 第二阶段 monotonic 起点取首次读到完成事件之前、上一次 trace.poll 开始的 monotonic 时刻（第一轮用 worker 启动计时 t0），保守地不晚于真正完成事件；不依赖可跳变的墙钟 UTC。正常最多提前一轮，但若系统调度/大日志解析延迟，提前量可能更大；原事件 UTC 和观测计时都会保留。
- 第二批完成后仍受同一第二阶段和累计上限约束，归档最终封存没有另加预算。完整产物封存的复制、PNG、hash 开销属于实际进程资源。

这是采样式外控，0.5 秒是目标轮询间隔，不是实时操作系统保证；maximum_poll_gap_seconds 记录连续 RSS/disk 采样完成时点之差，包含期间的日志解析、采样、休眠及调度耗时，瞬时 RSS 峰值可能落在采样之间。发现越限立即进入终止，不再科学续跑；SIGTERM 后最多2秒，再 SIGKILL/等待并记录仍存活对象，清理时间单列，不能把超限运行追认为预算内成功。没有抬高资源上限来消除失败。

正常退出也核是否留下已发现的活动子进程；有则终止并标失败。可捕获 SIGTERM/SIGINT 进入失败清理，保留 worker returncode、kill 行为、survivor/wait 错误和原输出。父进程被不可捕获 SIGKILL、宿主断电或磁盘不可写时，无法保证最终回执或所有清理发生；已有输出不删，不能在下次启动自动补写成功。

## 回执与主张边界

caller 目录保存 metadata gate、单次完整资源 gate、worker stdout/stderr、每轮监控 JSONL、worker 终态及外层终态。只接受同 manifest/launcher SHA 的 worker 回执。worker 的最佳状态是 `ORIGINAL_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW`；父进程只有在两条完成边界、关闭的无失败 trace、0退出且无越限/残留子进程时才写 `COMPLETED_EXTERNAL_RUN_PENDING_INDEPENDENT_REVIEW`。两者均显式 `scientific_status=NOT_EVALUATED`，没有 `technicalPASS`。

本小型 trace 读取器只用于资源预算边界，不校验所有 tensor/槽位、真实模型调用、物理意义或闭环因果。后续不同作者仍须按原合同核完整真实原始产物、组件加载、两批缓存消费及各项实测要求；正常 archive/trace/进程返回无法单独代替它。

本轮验证仅标准库 AST parse/compile、源码/元数据阅读与身份记录。没有执行缺件门或正向模型；没有人工、真实数组、GT、照片、权重、NPZ读取，也没有调用外部服务。后续 root 将组织一次必要的新接口人工验证及独立源码审，且仍不得升格成原模型实验。
