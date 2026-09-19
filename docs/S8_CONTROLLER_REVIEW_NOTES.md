# S8 本机预测控制器：运行前实现审查说明

新增入口是 `scripts/run_s8_sequence.py`。它接受新场景清单，顺序启动三次**原封不动的** `scripts/run_s6_cut3r.py`，每次24张RGB，前20张写入状态，后4张只查询。没有执行模型、下载数据或权重，没有修改旧实验、旧源码或研究账本。本文件描述实现；它不是S8实验协议，也不是S8模型运行结果。

## 必需参数与输入合同

七个参数均必填：`--manifest --protocol --repo --data --checkpoint --signed-rope-check --output`。资源上限不提供放宽开关：每块900秒、采样RSS预算16 GiB、CPU 8线程、seed 0。输出目录必须全新，包括已有空目录和失效符号链接也会被拒绝。

`--protocol` 可以是完整JSON文件，或Markdown文件中恰好一个 `s8-controller-json` 围栏。必须包含下面全部字段。可以另外保存研究假设、场景选择、评分规则等字段；这些额外研究字段会归档，但本控制器只执行预测阶段。

```s8-controller-json
{
  "schema": "s8-controller-v1",
  "stage": "S8",
  "block_count": 3,
  "frames_per_block": 24,
  "history_count": 20,
  "query_count": 4,
  "splits": ["test", "test", "test"],
  "device": "cpu",
  "cpu_threads": 8,
  "seed": 0,
  "dtype": "float32",
  "runner_sha256": "cc3ae6fd6243ce3531e540dc8c70ef61af0e868c919c7232a16616cf750ba292",
  "base_runner_sha256": "efb3c8b72ada668818d4211e6d5bb4aa357a3404778cf29d849f8551160bf923",
  "checkpoint_sha256": "7a7d83e47f822e040980c8f5aff4c15aa94366d469d3ceae51fa30cc2f62327d",
  "checkpoint_bytes": 2994205002,
  "commit": "8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf",
  "adapter_sha256": "6939dcead1b87e920eafce9aae47c1cc9a46b7a651ef816b3f521c779582152e",
  "timeout_seconds_per_block": 900,
  "max_rss_bytes": 17179869184,
  "depth_sent_to_model": false,
  "query_updates_state": false
}
```

清单顶层必需 `protocol_sha256`、`runner_sha256`、`blocks`；`dataset`可选。先冻结完整协议，再把协议字节SHA256写入清单，最后冻结清单。避免协议和清单互相声明SHA而形成循环。控制器首次读取后立即把原始字节和两份当前SHA写入全新结果目录，并在推理前、每块前后重新核对原件。独立的运行前冻结事件/登记文件仍由研究主流程保存；控制器不会冒称运行开始时的快照已经证明更早的预注册。

每个block必须包含 `block`、`split`、`frames`；ID依次0、1、2。split由冻结协议的三项`splits`决定，控制器不强制把新块当开发集；S8新场景模板全部为test，禁止使用新场景调参，原fr1 B0才是已有开发集。每个frame必须包含 `frame`、`rgb: {timestamp, path}`、`depth: {timestamp, path}`、`rgb_sha256`、`depth_sha256`；frame依次0至23。时间戳为有限数值，路径是相对 `--data` 的规范POSIX路径。允许额外保留 `match_index` 等选帧身份，但不会再读取或比较S3/S5历史清单。

同名的协议/清单声明必须相等（各自的schema可不同）。额外的来源文件SHA等字段会原样归档；若它们没有本合同定义的校验对象，不将“保存了声明”冒称“独立验证了来源”。

## 实際检查与失败行为

- 每块RGB时间严格递增；全72张RGB和全72份depth分别禁止实际路径、inode、SHA或时间戳重复。复制同一文件另起名字、硬链接和跨块复用都会被拒绝。RGB与depth不得是同一实际文件。当前合同适合一个新序列的三段不重复片段；若要多个序列共享时间戳，必须另立明确合同，不能静默放宽。
- 拒绝绝对路径、`..`、Windows路径、非规范路径以及指向数据根目录外的符号链接。所有RGB/depth核字节SHA。控制器没有导入PIL或深度读取器，也不解码depth；模型命令行只有RGB列表。深度字节完整性检查不构成测量评分。
- 校验固定CUT3R commit与干净tracked源码，并拒绝`src`中的非tracked或符号链接Python文件。保存95个实际上游Python源文件SHA；每块后核模型所载入的4个关键模块路径/SHA。源码快照包含控制器、S6 runner、原base runner、RoPE适配器和固定commit的完整源码tar。
- 核原权重2994205002字节及固定SHA、同目录`download_manifest.json`的verified_download状态、signed-RoPE报告与适配器SHA。原runner内部仍再次核权重，安全反序列化并要求所有权重key匹配。每块结果再次核CPU/线程/seed/架构、748443655参数、224 linear具体head、输入尺寸、加载权重身份与保存的runner SHA。
- 全部输入要求官方预处理后为`[1,3,224,224]`。这轮接口兼容当前TUM横向RGB约定，没有宣称任意图像比例或任意模型。参数、输入、保存数组FP32；官方encoder的RoPE内部Q/K转FP16，不能称全部算子纯FP32。
- 实际重新打开每块NPZ，要求恰好24×7=168数组，固定keys/shape/float32、全部有限，并逐值重算min/max与原记录核对。三块必须合计504数组。7种字段为self/other pointmap、self/other confidence、预测rgb、camera_pose、camera_c2w。`rgb`字段是模型保存的预测输出，不把它当新视角视频。
- 四处view flags都须符合历史20/query4；核25份状态快照的记录、固定历史锚点20、两个状态字段×4条query共8项，要求shape/dtype/finite/逐值相等/差0/同一tensor SHA。状态张量本身未归档，因此这里只验证原runner运行内审计记录和源码合同，不宣称新做了状态张量独立复算。
- 每块单独新进程且前一块通过全部核验后才启动下一块。每0.5秒采样进程RSS，超过16 GiB或900秒就终止该进程组，10秒后仍未结束则强制终止。RSS采样失败时停止；结束后核进程自身记录的peak RSS以发现采样间超限。这是采样软预算，不是操作系统硬内存上限；采样值覆盖模型主进程，不累加后代RSS。固定runner目前不另开模型子进程。
- 非零退出、预检失败、状态或数组核验失败、KeyboardInterrupt、SIGTERM都会保留已生成目录、日志、事件、失败traceback；运行中的模型进程组会清理，剩余块不启动。只要进程仍能执行清理，就不会删除失败证据；无法对SIGKILL/断电作出清理保证。

每块的命令、PID、开始/结束时间、RSS时间序列、实际模型metadata、数组核验、状态记录及SHA均归档。最外层`sequence_metadata.json`只有全部三块通过才有`ok=true`、`phase=complete`和`arrays_verified=504`。

## 无模型验证

新增 `tests/test_s8_sequence.py`：验证有效72输入、越界/不规范/符号链接路径、跨块RGB/depth重复、复制和硬链接别名、乱序/非有限时间戳、协议/runner/文件SHA、数量/split、历史与query规则、状态记录缺失/哈希改变、实际数组schema/finite/统计、全新输出与失败保留、真实轻量子进程的超时/RSS终止。测试数据是人工字节和小数组，不是新场景实验。

另用只读方式检查一块已归档S6结果的168份实际数组与8条状态记录均能通过新验证器，证明验证器与未修改runner的实际保存格式兼容。没有再推理，没有覆盖旧NPZ或metadata。当前固定上游95份Python源文件清洁性检查通过，S6/base/adapter三份SHA均保持上列原值。

可在项目内运行：`.venv-cut3r/bin/python -m unittest discover -s tests -p test_s8_sequence.py -v`。该命令不执行模型。实际S8新场景推理仍须等待新协议、新清单和主流程运行前审查完成。
