# S40 真实保存量读回工具：准备协议

这是 `readback.py` 的源码准备，尚未运行。S40 实际两批生成尚未发生；本目录没有实际输出或 PASS 回执。必须先完成不同作者源码审，再由根任务把真实 S40 manifest SHA、外控终态 receipt SHA 和路径交给本工具。当前不执行空 case，也不以合成模型证明真实效果。

旧 `work/S35_generation_integration/executed_results_readback.py` 固定人工合同、两个合成路径、人工异常、特定选图 `[0,2,4,1]` 与计数。因此仅参考其 codec/事件字段，不执行或直接套用。新读回不写死载荷数量、文件大小、真实选图 IDs 或 NMS 阈值；按实际档案完整枚举。两批、原 576 图、每批 8 输出、1→5→9 历史、每批50 Euler步是 S40 的原运行合同要求，不是从人工测试迁移的观测值。

## 验收范围

1. 新生成 manifest 必须是真实 S40 FROZEN、具名 ft-mse variant，218源域和四个新源码版本匹配；两份 S40 批准须绑定同 core。输入锚点是调用者给定的 manifest 文件 SHA 与真实外控 receipt SHA。核外控→worker→archive/trace/summary 的已有 SHA 链。runtime_loading 另纳入本次实际读回快照；它不是重新加载。没有重复原权重哈希、原照片/GT读取或运行 S40 gate（该门会读取原照片）。
2. 全 archive 物理文件集合必须等于原 manifest 完整集合，每个文件的 size/SHA 与实际内容一致。Tensor 用同一流式读取同时重算正文 SHA 和包含 dtype/shape 的 canonical SHA；再核侧车、各事件引用和独立事件链。只读8MiB块；已经核过的相同文件只查 stat，终点全部再核 size/mtime/ctime/device/inode 未变。Trace 所有真正带 blob 的载荷也核完整内容；没有 blob 的 descriptor 只作元数据，不能说完整原值重建。
3. 不借用 producer 的 ID>0 断言替代实际值比较。每批核实际 `samples_z` 对应保留槽→cache latent、真实全部 target CLIP 行→cache embedding、原目标相机/K→cache；核原旧缓存保持、cache→map后相同，并将第一批完整5行的 latent/embedding/c2w/K/像素与第二批 context 当时的 cache 逐值比较。
4. 第二批真实 `context_time_indices` 解码后，按其真实顺序核 cache 每个被选行→context_info 堆叠行，且至少有生成ID1–4。latent/embedding/像素等要求同 dtype、同 shape、原始 bits 完全相同。仅小相机/K允许原入口实际发生的 float64→float32：用 NumPy `astype('<f4')` 后再按 bits 比，不把这种转换冒充原 bytes 同一；不放宽误差容差。
5. 核 context latent/embedding→实际 get_cond 入参；context 相机→原 translation 输入→其原保存输出→get_cond相机入参；K同理。核 get_cond 真输出的 c/uc、相机、K、mask→实际 sampler_input；再核被选 latent 等于 sampler `cond.replace` 前4通道，原context标志通道为1。这样验证保存证据确实走到生成器入口，不只停在候选ID或context缓存。没有重算均值CLIP、Plücker、随机数或原模型；condition内部数学正确性不属于此核验。
6. 核两链顺序与闭合、每批各50个原Euler观察调用、真实shape、原5→14 K/5→9 depth计数、summary与实际事件一致。这里比较的是保存量和原调用记录，不能独立证明实际Gauss/renderer数学、视频质量、长程一致性或方法创新。

## 资源与命令

建议根任务沿已有外控运行：CPU1、300秒、2GiB RSS、新out目录。脚本自身也检查300秒 deadline；父外控负责RSS与整树终止。实际容量尚未量测，超限只保留失败，不自动扩大或删载荷。NumPy1.26.4为既有科学环境工具，延迟到首个已校验保存数组才导入；不导入 Torch/模型/原codec/renderer。NumPy memmap只读，不改源数组或权重。

```sh
S40_ROOT='/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling'
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
"$S40_ROOT/.venv-cut3r/bin/python" -B "$S40_ROOT/work/S40_result_readback/readback.py" \
  --manifest '<真实S40 manifest绝对路径>' --manifest-sha256 '<实际SHA>' \
  --execution-directory '<真实S40外控目录>' --launch-receipt-sha256 '<实际receiptSHA>' \
  --out "$S40_ROOT/work/S40_result_readback/executed_01" --seconds 300
```

输出 `report.json` 是完整比较清单与实际选图/文件/事件统计，`receipt.json` 记录实际时点、输入SHA、失败或窄范围通过。成功名限定 `PASS_SAVED_S40_IDENTITIES_AND_CACHE_CONSUMPTION_ONLY`；不能称生成质量已过。失败目录和部分核验身份保留，不覆盖旧目录。当前这些实际输出均未生成。

来源按固定 S35/S40 源码读取：S20 `_tensor_bytes` 与 trace `GenerationBatch`；S35 archive `_tree/_tensor/finalize`；integrator `_cache_tree/context_returned/commit_cache/condition/sampler`；原 VMem pipeline `get_context_info/get_cond/_generate_frames_for_trajectory` 和 util `do_sample`。具体SHA在准备回执；没有重读泛文献或重跑成功套件。
