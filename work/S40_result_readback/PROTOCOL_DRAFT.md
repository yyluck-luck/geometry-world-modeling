# S40 真实保存量读回工具：v3.3 执行协议

S40 唯一真实两批生成已经返回并通过两份独立终态小证据复核。第一次受控读回 `supervision_01/executed_01` 在首次成功 NumPy 映射比较、视觉解码/人工查看和质量评分前失败：实际第一批 `context_time_indices` 是原源码固定的 Python `[0]` 列表，而旧读回器把它误传给只接受 tensor descriptor 的 `Reader.array`。失败前已按协议流式读取并哈希 5,916 个文件、244,804,717 字节，其中包括 1,951 个 archive tensor `.bin` 正文（226,619,164 字节）与 9 个 archive PNG 正文（5,698,754 字节）；这些字节读取只验证文件身份，不等于成功映射张量、解码/查看图像或评价质量。失败目录与回执永久保留；它是读回表示错误，不是模型、生成或科学假设失败。v3.3修复已观察到的批次表示分支，并按攻击审查加强容器类型、scalar标签和值、tensor descriptor来源及全等绑定；必须先完成不同作者源码审，再更新并复核外层监督器，之后才可在全新的 `supervision_02/executed_02` 执行。不得以合成模型证明真实效果。

旧 `work/S35_generation_integration/executed_results_readback.py` 固定人工合同、两个合成路径、人工异常、特定选图 `[0,2,4,1]` 与计数。因此仅参考其 codec/事件字段，不执行或直接套用。新读回不写死载荷数量、文件大小、真实选图 IDs 或 NMS 阈值；按实际档案完整枚举。两批、原 576 图、每批 8 输出、1→5→9 历史、每批50 Euler步是 S40 的原运行合同要求，不是从人工测试迁移的观测值。

## 验收范围

1. 新生成 manifest 必须是真实 S40 FROZEN、具名 ft-mse variant，218源域和四个新源码版本匹配；两份 S40 批准须绑定同 core。输入锚点是调用者给定的 manifest 文件 SHA 与真实外控 receipt SHA。核外控→worker→archive/trace/summary 的已有 SHA 链。runtime_loading 另纳入本次实际读回快照；它不是重新加载。没有重复原权重哈希、原照片/GT读取或运行 S40 gate（该门会读取原照片）。
2. 全 archive 物理文件集合必须等于原 manifest 完整集合，每个文件的 size/SHA 与实际内容一致。Tensor 用同一流式读取同时重算正文 SHA 和包含 dtype/shape 的 canonical SHA；再核侧车、各事件引用和独立事件链。metadata解码把原始`kind=tensor`节点标成内部`TensorDescriptor`，PIL图像的pixels子节点也按同一路径标记；普通归档dict即使字段逐字相同也没有这个来源标记。任何用于数值比较的输入必须带该标记，并与此前登记的完整 descriptor 全等，不能只复用一个已登记 blob 路径。只读8MiB块；已经核过的相同文件只查 stat，终点全部再核 size/mtime/ctime/device/inode 未变。Trace 所有真正带 blob 的载荷也核完整内容；没有 blob 的 descriptor 只作元数据，不能说完整原值重建。
3. 不借用 producer 的 ID>0 断言替代实际值比较。每批核 `sampler_output.output`→全部 `sample_output.samples_z`→对应保留槽→cache latent；用捕获的真实 metadata.batch_id 选出同批目标 `encode_image_input/output`，核 samples 全部目标行（包括 padding）→实际 encoder 输入→实际 encoder 返回→commit 全部目标 embedding→cache。每批此调用按固定原目标代码应唯一，但初始化等 batch_id=None 编码另按真实记录计数，不写死全程共3次。原目标相机/K→cache；核原旧缓存保持、cache→map后相同，并将第一批完整5行的 latent/embedding/c2w/K/像素与第二批 context 当时的 cache 逐值比较。
4. 原源码存在两种实际 `context_time_indices` 表示，并按批次严格校验：metadata解码必须保留原 `list` 与 `tuple` 的区别，且每个 `scalar` 的type标签必须与JSON值的精确Python类型一致。第一批必须是逐标量保存的 Python 整数列表 `[0]`，tuple与bool均不能通过；第二批必须仍是已完成完整descriptor/正文哈希校验的 tensor，再读成一维整数向量。不得把任意 list 当 tensor，也不得把第二批 tensor 放宽成 list。按第二批真实顺序核 cache 每个被选行→context_info 堆叠行，且至少有生成ID1–4。latent/embedding/像素等要求同 dtype、同 shape、原始 bits 完全相同。仅小相机/K允许原入口实际发生的 float64→float32：用 NumPy `astype('<f4')` 后再按 bits 比，不把这种转换冒充原 bytes 同一；不放宽误差容差。
5. 核 context latent/embedding→实际 get_cond 入参；context 相机及全部 batch target 相机分别对应原 translation 输入的前缀/后缀，其原保存相机输出→get_cond；全部K的context/target前后缀同理。另核 translation 输出标量→get_cond args[3]，Torch/NumPy单元素用原dtype原bits、Python float用64位打包比较，不重算缩放公式。核 get_cond 真输出的 c/uc、相机、K、mask→实际 sampler_input；再核被选 latent 等于 sampler `cond.replace` 前4通道，原context标志通道为1。没有重算均值CLIP、Plücker、随机数或原模型；condition内部数学正确性不属于此核验。
6. 除两条hashchain，trace另核单一session、两个唯一非重叠batch、每批 batch_begin→sample_call→sampler_enter→sampler_return→sample_return→cache_commit→map_commit→batch_complete 顺序、denoiser callback归属/连续编号/返回计数、唯一最终session_end且之后无事件。所有批内archive关键capture的metadata.batch_id须对同一trace批；context_output在原batch创建前，其对应另由真实顺序/所选数组与trace描述符验证。每批各50个原Euler观察调用、真实shape、原5→14 K/5→9 depth计数、summary与实际事件一致。这里比较的是保存量和原调用记录，不能独立证明实际GA/renderer数学、视频质量、长程一致性或方法创新。

## 资源与命令

执行前根任务必须另绑定并实际使用已有外控：CPU1、300秒、2GiB进程树RSS、新out目录。脚本的300秒只是协作tick，不能抢占JSON解析或阻塞I/O；CPU线程环境、总时间和整树RSS需由实际外控配置/观察/终止。NumPy memmap降低大数组复制，但JSON/事件列表驻留内存，峰值未实测，不能称静态预算已经通过。超限保留失败，不自动扩大或删载荷。NumPy1.26.4延迟到首个已校验保存数组才导入；不导入 Torch/模型/原codec/renderer。

下面仅是交给外控的worker命令参数，不是已经实施RSS/整树时限的完整启动器；不得单独运行此示例后声称2GiB已经受控。

```sh
S40_ROOT='/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling'
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
"$S40_ROOT/.venv-cut3r/bin/python" -B "$S40_ROOT/work/S40_result_readback/readback.py" \
  --manifest '<真实S40 manifest绝对路径>' --manifest-sha256 '<实际SHA>' \
  --execution-directory '<真实S40外控目录>' --launch-receipt-sha256 '<实际receiptSHA>' \
  --out "$S40_ROOT/work/S40_result_readback/executed_02" --seconds 300
```

输出 `report.json` 是完整比较清单与实际选图/文件/事件统计，`receipt.json` 记录实际时点、输入SHA、失败或窄范围通过。成功名限定 `PASS_SAVED_S40_IDENTITIES_AND_CACHE_CONSUMPTION_ONLY`；不能称生成质量已过。失败目录和部分核验身份保留，不覆盖旧目录。`executed_01` 只有失败 receipt、没有 report；任何未来结果只能写入新的 `executed_02`。

来源按固定 S35/S40 源码读取：S20 `_tensor_bytes` 与 trace `GenerationBatch`；S35 archive `_tree/_tensor/finalize`；integrator `_cache_tree/context_returned/commit_cache/condition/sampler`；原 VMem pipeline `get_context_info/get_cond/_generate_frames_for_trajectory` 和 util `do_sample`。具体SHA在准备回执；没有重读泛文献或重跑成功套件。

v2修订依据：`source_review_v1.json` 的R1/R2与资源边界。原源码/协议/准备回执/独立初审完整留在 `history_v1_before_bridge_review/`；初审不是结果失败，本次修改没有执行任何保存数组或模拟case。

v3修订依据：实际 `executed_01/receipt.json` 的 TypeError、archive `context_output` occurrence 0/1 元数据，以及原冻结 pipeline 第632/753行。旧 v2 源码可由 `history_v1_before_bridge_review/readback.py` 与 `readback.py.v2.diff` 重建，其精确 SHA 也由 `source_review_v2.json` 和两个 attempt01 回执绑定。首次 v3 审查 `source_review_v3.json` 以 `REVISION_REQUIRED` 阻断了“读取像素前失败”这一过窄表述，本版已按 attempt01 receipt 的实际 identity 集合修正；第二份攻击审 `source_review_v3_adversarial.json` 又阻断了list/tuple折叠、scalar标签未核和descriptor仅按路径复用；v3.2复审 `source_review_v3_2.json` 进一步指出完整字段相同的普通dict仍可能冒充tensor来源。v3.3用受控descriptor类型关闭该来源歧义，并修正一个不等式错误消息，数值条件未变。各次源码修改与协议纠正期间均未额外读取 tensor/blob/image 正文，也未运行读回、模型、gate、评分或生成；这不改变 attempt01 本身已经完成的文件正文流式哈希读取。
