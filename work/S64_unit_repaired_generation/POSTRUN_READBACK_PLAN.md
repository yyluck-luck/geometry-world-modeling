# S64 结束后一次工程读回草案

本次只回答：**新的单位修复变体是否实际越过旧 C2 的第二次检索失败，进入真实条件计算，并完成两批输出？** 另报告第一批噪声、缓存和输出是否与旧 V9 逐位相同。后者是结果前提出的诊断预期，不是启动、生成成功或重试门。

作者 `/root/c2_v9_recovery_author`。这些新文件独立于已冻结生产 18 项；不改变原模型、生产来源、执行目录或失败记录。作者阶段只查源码、旧 V9 JSON 元数据和编译，不读 S64 运行产物、张量或 RGB 正文。交付状态为待不同作者源码核验的草案；实际读取仍由 root 在真实终态之后执行。

## 最小复用与执行顺序

1. root 先核实际外部返回，取得已经产生的 manifest、external receipt、terminal commit 三个 SHA。脚本固定 S64 的既有目录，只接受这三个真实 SHA；没有预填未来值。外部非零、timeout、失败终态或缺少文件时，在任何科学正文读取之前停止。
2. 核外部 argv/PID、parent/worker/watchdog/commit 相互绑定与目录身份、实际 221 项 source SHA、VAE 和 retrieval variant、resource consumption。直接 AST 抽取已冻结 S64 `collect_unit_receipts` 原函数，重读真实单位票并要求 worker/commit 绑定的实际 SHA 集合一致。正常两批恰一份真实单位调用票；第一批 history=1 跳过 renderer，不能以安装票代替调用。
3. 先读 archive/trace JSON 元数据：链哈希、capture begin/complete、完整两批 trace、文件清单和尺寸。新档案要求完整；旧 V9 的 partial/caller_failure 保持原样。按 capture name/occurrence 定位，不把旧 seq 当新 seq。
4. 原 `render_input → render_output → retrieval_output → context_output(第二次)` 必须位于第一批 map commit 后。接续 S40 已核过的数值检查块，逐个懒读被实际检查引用的 tensor：真实四类 cache → 四个合法且唯一的第二批 ID → `get_cond` 实参 → condition output → sampler 实参 → 两批 samples/retained cache。核两批各 50 次 Euler、history 1/5/9、retained IDs 1–8、实际 target encoding 与新 latent/embedding、相机/K，并核跨批四类 cache 不变。第二批 ID 不预定为 B0/S63 的 `[0,2,4,1]`。
5. 单独比较旧 V9 与新 S64 第一次 sampler/sample/cache 的 27 项身份。无论声明相等与否，都核实际文件正文 SHA；将差异写入 report，不据差异改变 engineering PASS、删结果或重跑。
6. 保存 `report.json` 和包含逐文件实际读入清单的 `receipt.json`。失败保留输出目录与异常；root 的外部执行记录保留源加载/进程层失败。脚本沿用 S40 固定 300 秒内部预算，外部采用既有 readback 监督方式给予有限上限，不自动延长或重试。

## 有界文件与正文范围

| 范围 | 必要输入及解释 |
|---|---|
| S64 终态与科学身份 | `review_attachment_01/manifest.json`；`external_launch_01/receipt.json` 及其 stdout/stderr；`execution_01` 的 parent/worker/watchdog/started/provisional/commit；source identities；runtime loading；实际 `retrieval_unit_call_*.json`。正文只为 JSON/日志/源码。 |
| S64 档案元数据 | `archive/manifest.json`、`archive/events.jsonl`、`trace/events.jsonl`、`observation_summary.json`；文件名和尺寸盘点。不会全扫所有科学 blob 正文。 |
| 工程消费的数值正文 | 两次 context/batch/translation/condition/sampler/sample/cache/map 的**检查实际引用字段**；真实 image encoder 输入/输出。每次使用前核事件 descriptor、manifest descriptor、dtype/shape/nbytes、descriptor SHA 与实际 body SHA。复用 S40 bitwise 数值比较；仅原小 camera/K 的 FP64→FP32 gather 转换允许显式标记。 |
| RGB 正文 | 两批 FP32 `sample_output.samples`（各 31,850,496 B）、真实 encode_image 输入，以及 prefix 中旧/新各四个 uint8 保留帧像素（各 995,328 B；按实际 blob 去重）。这些都是 RGB 正文读取，**不是 0 RGB**。只重哈希或作数值对应，不用 PIL/codec，不绘图、不显示，不判断画质。 |
| 旧 V9 prefix | 固定 archive manifest/events SHA。occurrence0：seq34 `sampler_input.noise`；seq38 `samples_z/samples`；seq44 五份 `c2ws/Ks/latents/encoder_embeddings` 和 `pil_frames[1:5].pixels`。共 27 项内容身份，不比较必变的时间、事件链 SHA、路径或 PNG 封装。 |
| 不进入正文范围 | 模型权重、原始照片文件、目标答案、surfel geometry/depth payload、RNG state、未引用的 trace/blob、PNG 文件。map 中 surfel_Ks/depths 只核原有长度元数据。没有 model/renderer/get_cond 重算。 |

读入票分别列出 `unique_verified_payload_bytes`、`unique_verified_RGB_body_bytes` 与每个文件的原始 SHA/尺寸/状态；数字代表已核的唯一正文文件字节，不能冒充底层磁盘 I/O 总量。未读科学文件仅可称清单/尺寸核验，不称全部 archive 正文已通过。图像显示次数固定为 0，质量状态为 `NOT_EVALUATED`。

## 复用来源与明确改动

`POSTRUN_READBACK_DRAFT.py` 从 S40 读回固定字节中 AST 抽取纯 helper 和 `run` 后半段数值消费检查，不执行 S40 原入口、模型或全档案正文遍历。数值块只省掉原五张 RGB 的 cross-cache 冗余比较；其四类数值 cache 连续性保留，prefix 四张生成 RGB 另核实际正文。移除不适用的“trace 未保存 blob 数”输出字段，并将 scope 明确为选择性正文核验。

| 来源 | 固定 SHA-256 | 用途 |
|---|---|---|
| `work/S40_result_readback/readback.py` | `d4c22504569ad1fb1fcc74ea1da83b4f244f4de803f5d0fadc16e8da06777933` | 已有 Reader、trace 状态机及缓存消费数值检查；执行时从核 SHA 的相同字节抽取。 |
| `work/S64_unit_repaired_generation/launch_generation.py` | `2998383f07bd9437440b24f465ef5624d7291890b8f750c9b6ce2795c33bfb35` | 原 unit receipt 收集函数与终态字段。 |
| `work/S64_unit_repaired_generation/AUTHOR_DELIVERY.json` | `d418449ac50228dabbe2c1aac1281c775ecc3e2c61a8c09af1c228116aa10e17` | 与生产作者最终身份关联；本草案未加入生产来源。 |
| `work/S60_c2_v9_failure_audit/audit_terminal.py` | `7fb26c2d32272299d8a5fc3d696184b2b9191d175cfed8859c7b41dd31a9d574` | 已有 outer/commit/watchdog 读回路线参考；不导入这个会顶层执行的旧脚本。 |
| `work/S64_unit_repaired_generation/SCIENTIFIC_IDENTITY_REVIEW.md` | `1181c272e818156658da7fcaf67391c79c1a55bfa630a0eb4bdeef9f28e12476` | 第一批 prefix 的结果前预期与差异解释边界。 |
| `results/S47B_C2_confirmation_generation_v9/archive/manifest.json` | `7cfd56b59924fb3c603a3eb54c34f387db8439c72fc4a6fe08e3097dcf659b4c` | 旧 prefix 来源，保持 partial。 |
| `results/S47B_C2_confirmation_generation_v9/archive/events.jsonl` | `b51b39e1772a7a2cbc0221bc0846d95cd3b7c8b21f8978ddbbd0f1d2443f6ef7` | 旧 capture 定位；作者只读其元数据。 |

C1 的 `work/S45_c1_result_readback/readback.py`、C2 的 `work/S58_c2_result_readback/readback.py` 提供原复用路线参考；它们绑定旧行和旧来源数量，不能直接把标签改成 S64 当成已核身份。后续相机/主评分仍应按已有 S45B/S46 方案另作明确 S64 绑定，本脚本不提前评分或显示新图。

调用参数为 `--manifest-sha256`、`--external-receipt-sha256`、`--terminal-commit-sha256`、`--out`。root 只在真实完成且本草案经过不同作者源码核验后，用实际值执行一次；输出必须是全新目录。`--compile-only` 只核固定来源和 AST，不读任何 S64 结果。

若实际两批通过，这只证明常规工程变体恢复了该次执行和消费链。旧 V9 失败保留，S64 不补原 cohort；第一批相同不构成随机状态完全恢复或因果证明，第一批不同也不能直接归因于 hook。画质、相机服从、新方法和跨场景结论均未由此建立。完成可靠基线后，应回到一个有明确近邻、机制差别和否证条件的新问题，不能把更多读回检查当创新。
