# S64 相机与评分最小复用

完成 UTC：2026-09-08T22:04:49.414857+00:00。作者 `/root/c2_v9_recovery_author`。仅旧源码/协议核查；0 S64 新档案、张量、RGB、模型、评分或看图。本文为下一步定位，不代表 S64 已完整结束。

**可最小复用：保留已经成功的数值函数，用一个薄的 S64 身份/读取适配层接入；不要复制整套 C1 正式入口。** V12 的 `selected_event_captures`、`CameraTensorStore`、`decode_selected_cameras` 和 `evaluate_numeric_guard` 可保留原解码与相机数学；S46 的 `score_frames(frames,np)`、不同实现的 `recompute_frames(frames,np)` 保留原字节和数学。原文件不改，新源经既有独立核验后一次执行，无需重跑旧矩阵。

**必须替换的绑定。** C1 worker 的 `verify_upstream`、V3 wrapper 的 `FIXED_UPSTREAM/validate_contract`、复算 I/O 的 `load_primary_chain` 固定了旧 C1 路径/SHA/schema、S45 完整读回、C1 盲态与已消费 attempt，不能直接运行。新适配层须绑定实际 S64 manifest、row=`C2_UNIT_REPAIRED_S64`、VAE 与 `retrieval_variant`、outer/worker/commit、实际单位票、postrun report/receipt/不同作者结果复核，以及新的相机结果、九帧身份和独立输出目录；未来 SHA 只从实际产物取得。原 kernel 返回的 `row=C1`、`row_status`、blind/cohort 标签是旧元数据，不能作为 S64 报告结论：只复用其数值字段，外层明确探索性工程变体、`eligible_for_original_cohort=false`。旧 S42 三行及阈值保持，S64 不补 C2 行。

**必要实际读取。** 相机：两次 `batch_input.target_c2ws/target_Ks[:4]`；两次 `cache_commit.cache.c2ws/Ks`（5、9 项），按原 descriptor/SHA/尺寸/finite 规则读小数组，实际去重数量由新元数据决定，不硬填 C1 的 11 份/1584 B。ID0 权威锚为第二次 cache commit；原 yaw `[0,1.25,2.5,3.75,5,3.75,2.5,1.25,0]`、左乘 Y 旋转、固定 K、batch→cache、跨批连续性及 ID8→0 全部保持 `max_abs≤1e−6`。这是原存储相机的请求检查，不能把 get_cond 转换后的 CV 矩阵混入。

像素：仅第二次 `cache_commit.cache.pil_frames[id].pixels`，按 ID0–8 导出九项 `id/tensor_descriptor_sha256/tensor_body_sha256/blob` 元数据，再逐文件核实际 uint8[576,576,3] 正文，九帧逻辑总量 8,957,952 B；不用 PNG、其他 occurrence 或 FP32 sample 替代。当前 postrun 不输出 C1 接口的九项权威表，也不核每个 archive body；下一步补这份元数据表即可，不重复全档案遍历。主分数仍为固定 M_outer4 的 ID0/8 float64 MSE、PSNR，严格 `>0.01`；四区域、全图、1/7、2/6、3/5 诊断与复制退化守卫原样保留，不新增指标。

**最短顺序：** 实际终态与 postrun 独立核收 → 固定九帧元数据/新身份及已有数学来源 → 仅相机正文验证与不同作者结果核验 → 同一冻结数学机器评分一次 → 从封存主结果和同九帧独立复算（全部既定 metric、floathex/分母/event 精确核对）→ 结果核收后才全九帧查看。相机失败保留 `NO_VALID_REVISIT`，不当作回访损害。评分前如实记录是否已看图、已算分、是否用正文选择指标；postrun 会读 RGB，不能写“未读像素”或重建旧 cohort 盲态。当前仅工程与探索性描述；数值相机通过不证明画面服从，分数不证明记忆原因、方法收益或创新。

## 固定来源清单

以下均相对项目根目录；本次只读整文件核 SHA。C1 wrapper/复算 I/O 供读取与发布接线参考，不能按旧绑定直接执行。

| 文件与入口 | SHA-256 |
|---|---|
| `work/S45B_c1_numeric_camera_guard_supervised_v12/camera_guard.py`：843/860 选择，955 store，1129 数学，1202 解码 | `02114d4a845bd83e3dcd35f663bf64f2a75eb5fb17fc0f3515b84222bd51281f` |
| `work/S45B_c1_numeric_camera_guard_supervised_v12/supervise_camera_guard.py`：既有外部退出/完整输出参考 | `179184084bbaabf5e5c7c6f6332f7a44f8292dcbeda993370642d585cfd6380c` |
| `work/S46_c1_blind_scoring_preparation/score_c1_blind_candidate.py`：70 `score_frames` | `ada2ba80eceebe83a514fd929c6cc82b69669e6525e261ff4729064f2bac3f1a` |
| `work/S46_c1_blind_scoring_wrapper_v3/score_c1_blind_wrapper.py`：172 同 FD 像素读取，313 核身份加载 math | `3c8f931da47403cd5b249a6680790107136ffea0267f871679e77e7b27150463` |
| `work/S46_c1_blind_scoring_preparation/recompute_c1_independent_candidate.py`：`recompute_frames` | `9373fd035b18ccc81dc848e18612f906a7d32a44cd1c7d2903eb67b7627e9b8f` |
| `work/S46_c1_blind_scoring_preparation/C1_independent_recompute/recompute_c1_io.py`：188 `compare_math`；同 FD 快照/不覆盖发布参考 | `37b5f837b1c2b7645cc4420a9d498a57bf070668936c5c3eb84147094ba4aaeb` |
| `work/S42_baseline_failure_preregistration/PROTOCOL.md`：第 3–6 节原数学与边界 | `89fb44e0b77a85a66fe611cd2f885fed0288229cbb027e04da25fc0631507b3f` |

评分数学树 SHA 保持 `9bee0abe9392e04e061adb7cf8b39297d7730e7045ed856486f1e03ee8d82812`。以上不是新评分协议或运行票；本次仅此一份文档，后续纠正另建文件。
