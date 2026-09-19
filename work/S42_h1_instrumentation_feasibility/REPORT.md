# S42 H1：A0 / A0R / A1 最小影响门插桩可行性审计

审计时间：2026-09-07T06:11:58Z。裁决：**READY_FOR_SOURCE_PREPARATION**。

这个裁决只表示：现有冻结源码与 S40 完整保存设计已经给出了实现直接 sampler 重放所需的接口，下一步可以编写并独立审查插桩源码。它不表示 S40 已运行，不表示 exact replay 已通过，也不表示 CLIP 支路影响、自然失败或创新已经成立。当前审计没有加载模型、运行前向、生成视频、读取尚未生成的数组或修改研究主账。

## 1. 最小门到底比较什么

为避免把 S40 整条路线再跑三遍，三项身份固定如下：

| 标签 | 定义 | 新增 sampler 调用 | 科学用途 |
|---|---|---:|---|
| `A0` | 通过 S40 完整 readback 的预注册目标 batch；使用其实际 mean CLIP 条件和已保存输出 | 0 | factual baseline 与所有重放输入的唯一来源 |
| `A0R` | 从 A0 保存的 sampler-entry 数组和 RNG 状态直接重放 sampler，再用同一 VAE 解码 | 1 | exact replay 守卫；不用于宣称改善 |
| `A1` | 从同一 A0 bundle 重放，只把 conditional `c.crossattn` 变成同 shape/dtype/device 的零张量 | 1 | CLIP 条件支路移除的因果负对照 |

这里把根协议里的 “A0 exact mean replay” 展开为 **S40 factual A0 + A0R replay guard**。只有 A0R 逐字节复现 A0，A1 才允许启动。这样最小新增计算是两个 sampler 调用和两个 VAE decode，不重新运行检索、CLIP、VAE encode、几何重建、缓存写入或地图更新。

A0 必须先满足三个外部门：

1. S40 的具名组件变体、两批路线和 full archive 已完成，且 `work/S40_result_readback/readback.py` 给出 `PASS_SAVED_S40_IDENTITIES_AND_CACHE_CONSUMPTION_ONLY`；
2. 自然回访失败、batch、target slot、区域、主指标、相机服从门和 seed 已在查看 A0R/A1 输出前冻结；
3. 该失败没有先被错误 pose/K、无有效回访、未消费生成历史或缓存接线失败解释。

## 2. 冻结源码给出的实际通路

### 2.1 条件形成与消费

固定隔离源码 `modeling/pipeline.py` 的 `get_cond`：

- 对选中历史图的 `encoder_embeddings` 沿来源帧维求 mean；
- 把该 1024 维全局向量复制成每个 camera 一个 token，作为 `c.crossattn`；
- 把 `uc.crossattn` 明确建成 `zeros_like(c.crossattn)`；
- 把逐帧历史 latent 加 mask channel 后放入 `c.replace`；
- 把输入帧 mask 与 Plücker 拼成 `c.concat`；
- 把同一 Plücker 放入 `c.dense_vector` 和 `uc.dense_vector`。

`VMemWrapper.forward` 把 `concat` 与扩散输入按 channel 拼接，把 `crossattn` 作为网络 `y`，把 `dense_vector` 作为 `dense_y`。`DiscreteDenoiser` 则在每个 denoising callback 前用 `replace` 的 mask 把 context 槽换回固定历史 latent。因此 A1 只能称 **全局 CLIP 条件支路移除**，不能称“无记忆”：逐帧 latent、mask 和两条 Plücker 条件全部仍在。

### 2.2 为什么必须保存 noise 之外的 RNG

`utils/util.py::do_sample` 先以 `torch.randn` 生成初始 `noise`，再进入 sampler。`EulerEDMSampler.sampler_step` 在每个步骤仍调用 `torch.randn_like(x)`；而 `sigma_hat = sigma * (gamma + 1) + 1e-6`，即使 `s_churn=0`，也不能只根据代码假定这次随机 draw 对数值严格无效。

因此仅复用 seed 或初始 noise 都不够。重放必须使用 **A0 sampler-entry 时已经完成初始 noise 抽样之后** 的 Torch CPU RNG state，并同时保存/恢复 Python 与 NumPy legacy state。S35 的 full archive 在调用实际 sampler 前同步保存了 noise、sampler inputs 和这三类 RNG；S20 trace 在同一边界另有 `sampler_enter` 记录，可作交叉身份检查。

## 3. A0 replay bundle：必须逐项冻结的内容

bundle 只能从已经通过 S40 readback 的一个预注册 batch 派生，并绑定 S40 manifest、worker receipt、archive manifest、trace 尾哈希、readback report 与全部源码/权重 SHA。它应以只增不改的 manifest 列出下表中的每一项；每个 tensor 保存 dtype、shape、C-order bytes SHA 和来源事件序号。

| 类别 | A0 中的权威来源 | A0R 的用法 | A1 的用法 | 必须检查 |
|---|---|---|---|---|
| `selected_context_ids` | `context_output.context_time_indices`，并由 batch begin/cache commit/readback 三方一致 | 不调用检索；仅作 bundle 身份与顺序断言 | 完全相同 | 一维整数、无重复、每项指向 `cache_before` 合法行 |
| `cache_before.latents` | `context_output.cache.latents[id]` | 与 materialized context latent 和 `c.replace` 对应槽逐字节核对；不写入 live pipeline | 完全相同 | selected row → context row → replace 前四 channel 链条一致 |
| `cache_before.encoder_embeddings` | `context_output.cache.encoder_embeddings[id]` | 与 context embedding 及最终 mean `c.crossattn` 的来源关系核对；不重新 encode/mean | 完全相同 | 行顺序、shape、dtype、SHA；只作 provenance，不重新计算条件 |
| `cache_before.c2ws/Ks` | `context_output.cache` | 与 context/translation/get_cond/sampler 链条核对 | 完全相同 | readback 已许可的小型 FP64→FP32 cast 必须单独标明，其余逐字节 |
| `cache_before.pil_frames`、Surfel/map | context 与 map archive | 只保留 SHA/来源身份证明；不解码、不渲染、不检索 | 完全相同 | 不把它们送回 VMem 以免重新检索或更新地图 |
| `noise` | full archive `sampler_input.noise`，位于 sampler 真正调用前 | 每臂从冻结 bytes 新建独立 clone | 完全相同的新 clone | `(8,4,72,72)`、CPU FP32、输入 SHA 相同；允许 sampler 只修改本臂 clone |
| `scale` | `sampler_input.inputs.scale` | 原值原类型复用 | 完全相同 | Python scalar 与 tensor 不得互换 |
| `c.crossattn` | `sampler_input.inputs.cond.crossattn` | 原 bytes | 唯一改变：`zeros_like` | 预期 `(8,1,1024)`；实际 shape/dtype 优先；A1 全零 |
| `c.replace` | sampler input | 原 bytes、独立 clone | 原 bytes、独立 clone | 预期 `(8,5,72,72)`；context 槽前四 channel 对应历史 latent，第五 channel 为 1 |
| `c.concat` | sampler input | 原 bytes、独立 clone | 原 bytes、独立 clone | 预期 `(8,7,72,72)`；1 mask + 6 Plücker |
| `c.dense_vector` | sampler input | 原 bytes、独立 clone | 原 bytes、独立 clone | 预期 `(8,6,72,72)`；与 concat 的 Plücker 六 channel 逐字节一致 |
| `uc.crossattn` | sampler input | 原 bytes | 原 bytes，不重建 | 源码要求为零；A0/A0R/A1 三者 SHA 相同 |
| `uc.replace/concat/dense_vector` | sampler input | 全部原 bytes | 全部原 bytes | 每项三臂相同；`uc.dense_vector` 与 `c.dense_vector` 数值相同 |
| sampler `c2w/K/input_frame_mask` | sampler input | 原 bytes、独立 clone | 原 bytes、独立 clone | 不重新调用 `get_translation_scaling_factor` 或 `get_cond`；mask 顺序与 slots/IDs 相同 |
| sampler-entry RNG | full archive `sampler_input.rng`，并与 S20 `sampler_enter.rng` 核对 | 调用前恢复 | 调用前恢复同一状态 | Python tuple、NumPy legacy tuple、Torch CPU uint8 state 均须类型保真反序列化 |
| sampler-return RNG | A0 full archive `sampler_output.rng` | 作为 expected post-state | 只记录，不要求等于 A0 | A0R 必须逐项等于 A0；A1 因 draw 数/shape 相同，预期 Torch state 也应相同 |
| `samples_z` 与 decoded `samples` | A0 `sampler_output` / `sample_output` | exact replay 比较目标 | 影响与失败相关性比较 | 不把重新 encode 的 latent 当作 `samples_z` |

`condition_output` 与 `sampler_input` 都已由 S40 readback 设计为逐 tensor 对照。replay bundle 应以 **实际 sampler input** 为执行权威，同时保留 `condition_output → sampler_input` 的 SHA 证明；绝不能从 cache 再调用 `get_cond` 重建条件，因为 `get_cond` 会原地修改 camera tensor，并重新计算 mean/Plücker，引入新的对象状态与数值路径。

Full archive 对 Python/NumPy RNG 保存了 tuple/list 类型标签。bundle 提取器必须按归档树的 `kind` 恢复原容器类型；当前 readback 的便捷 metadata 视图会把 tuple 和 list 都转成 list，不能直接拿该视图调用 `random.setstate` 或 `numpy.random.set_state`。

## 4. 唯一允许的运行路径

### 4.1 只加载模型，不启动原两批路线

复用 S40 的资源 gate 和 `runtime_adapter.create_runtime` 加载同一具名权重、CPU/FP32 pipeline、sampler 和 VAE；**不要**调用 `run_original`、`Navigator`、`initialize`、`turn_left/right`、`get_context_info`、`get_cond`、`encode_image`、`encode_vae_image` 或 `construct_and_store_scene`。

runner 直接使用：

- `pipeline.model_wrapper`；
- `pipeline.denoiser`；
- `pipeline.sampler[0]`；
- `pipeline.vae.decode`。

它复刻 `do_sample` 中 sampler 之后的路径：在 `torch.inference_mode()` 且 CPU autocast disabled 的环境下，构造同一 `denoiser(model, input, sigma, cond, num_frames=8)` closure，用冻结 noise、scale、c/uc、c2w/K/mask 调用 sampler；在捕获 sampler-return RNG 后，以同一 `decoding_t=1` 解码返回 latent。这里不调用 `do_sample` 本身，因为该函数会先重新执行 `torch.randn` 生成一份新 noise。

### 4.2 每臂的不可变顺序

每个重放臂执行相同的事务：

1. 从 bundle bytes 新建所有 tensor；禁止沿用上一臂被 sampler 原地修改过的 noise。
2. 检查每项 shape/dtype/device/byte SHA；记录 live pipeline cache/map/global_step 的开始指纹。
3. 保存当前 ambient Python/NumPy/Torch RNG；把三者恢复到 A0 sampler-entry 状态。
4. 在恢复 RNG 后不执行任何随机 draw、编码、检索或条件重建，立即调用 sampler。
5. sampler 返回后立即捕获三类 RNG 与 `samples_z`，之后才调用 VAE decode。
6. 保存 decoded tensor；确认 c/uc/c2w/K/mask 均未变，cache/map/global_step 指纹未变。
7. 恢复进入本臂前的 ambient RNG，以免审计程序污染外部状态。

顺序固定为 `A0R → exact gate → A1`。A0R 未通过时，外层 supervisor 必须停止，不得为了得到 A1 图像而继续。

### 4.3 不重新检索、不更新 cache 的强制门

最安全的实现不是“把旧 cache 填回 pipeline 再请求一次”，而是把 S40 已经 materialize 的 sampler 输入直接送到 sampler。为防止隐藏路径误用：

- 对 `get_context_info`、`get_cond`、两个 encode 函数、`construct_and_store_scene`、Navigator 操作安装 fail-fast counter；任一调用即失败；
- live pipeline 在模型加载后保持未初始化空 cache；保存 `pil_frames/latents/encoder_embeddings/c2ws/Ks/surfel_depths/surfel_Ks/surfels/surfel_to_timestep/global_step` 的运行前后指纹；
- 冻结 S40 cache 只在独立的只读 provenance 对象中按 ID 验证来源，不赋给 live pipeline；
- 不执行 target PIL 转换、CLIP 编码、VAE re-encode、append loop、Surfel render/NMS 或 GA；
- 每个输出只写入该臂独占的新目录，不覆盖 A0/S40 原件。

这使 `R/L/G/U` 中的检索结果、逐帧 latent、相机/Plücker、mask 和随机过程保持不变；A1 的唯一代码级差异是 `c.crossattn`。

## 5. A0R exact replay 门

CPU/FP32 主实验使用 **零容差、逐字节门**。A0R 必须同时满足：

1. 调用前所有 sampler inputs 与 A0 描述符逐字节一致；
2. 50 个 Euler step 完成，denoiser/model 调用计数与 A0 trace 约束一致；
3. A0R `samples_z` 与 A0 `sampler_output` / `sample_output.samples_z` 的 dtype、shape、C-order bytes SHA 完全相同；
4. A0R decoded float tensor 与 A0 `sample_output.samples` 逐字节相同；若另存 PNG，只比较解码后像素值，PNG 容器 bytes 不作为必要条件；
5. sampler-return 的 Python、NumPy、Torch CPU RNG state 与 A0 同边界状态完全相同；
6. 除 noise 的本臂工作 clone 外，所有输入条件未修改，live cache/map/global_step 未改变；
7. 没有任何被禁止的检索、编码或更新调用。

任一项失败，状态只能是 `FAILED_EXACT_REPLAY_NO_CAUSAL_INTERPRETATION`。不得看过 A0R/A1 后把“exact”改成临时挑选的 epsilon，也不得用 seed 相同、视觉相似或 LPIPS 很小替代逐字节复现。若 CPU 固定算子确实无法逐字节稳定，必须在不读取 A1 输出的前提下另立协议版本，以独立重复的 A0 replay 预先估计数值门；旧失败和改版原因保留。

A0R 通过只证明直接 sampler 重放接线与 frozen execution 在当前具名变体、当前机器和当前软件栈上可复现；它不证明模型正确或 baseline 有自然失败。

## 6. A1 到底改 `c` 还是也改 `uc`

**只替换 conditional `c.crossattn`；`uc` 整个字典逐字节复用。**

源码依据是：

1. `get_cond` 直接令 `uc_crossattn = torch.zeros_like(c_crossattn)`；因此 A0 的 `uc.crossattn` 已经是零。
2. CFG 的 `prepare_inputs` 对每个条件键按 batch 维拼接 `torch.cat((uc[k], c[k]), 0)`，随后用 `uncond + scale * (cond - uncond)` 合成。把 A1 的 `c.crossattn` 置零会消除 CLIP 在 conditional 与 unconditional 半支之间的差异，而其他条件分支保持原样。
3. 若把 `uc.crossattn` 换成非原值，就同时干预 unconditional/negative 分支；这不再是根协议定义的 zero-CLIP 路径效应。

实现上可以对 `c.crossattn` 使用 `zeros_like`，但 receipt 必须把 delta 写成：

`changed = {c.crossattn}; unchanged = {c.replace, c.concat, c.dense_vector, all uc keys, noise, RNG, c2w, K, mask, scale}`。

“把 c 和 uc 都 zero”在当前源码上数值上会碰巧得到同一 `uc`，但审计记录仍应写清只有 conditional tensor 被指定为干预对象，并断言输入 A0 的 `uc.crossattn` 原本已经全零。A1 是删信息的因果负对照，不是同信息性能 baseline，也不把算术 mean、CLIP 全局编码器和整条 cross-attention 路径进一步区分开。

## 7. A1 通过后允许说什么

- 若 A0R 不通过：停止；没有 A1 因果结论。
- 若 A0R 通过而 A1 与 A0 在 `samples_z` 和 decoded output 上逐字节相同：当前 case 没有检测到 CLIP 支路输出影响，停止 mean 路线。
- 若 A1 与 A0 不同：只说明 cross-attention 条件支路对输出有影响。
- 只有 A1 同时改变了预注册自然失败的主结果，且方向、相机服从与整体质量代价均按冻结规则报告，才称对该失败有 relevance。
- A1 改善不能单独归因到算术 mean；它仍混淆 mean、全局 CLIP 粒度和整条 conditional cross-attention 路径。

输出差异的第一层门可使用 tensor byte identity，因为 A0R 已把 replay noise floor 固定为零；自然失败是否改善仍使用 Gate 0 预注册的科学主判据，不能用看过 A1 后挑出的图、crop 或 metric。

## 8. CPU 与 MPS 边界

### CPU

当前方案只对 **CPU / FP32 / 8 threads** 给出 READY：

- S40 runtime factory 构造 `VMemPipeline(..., device='cpu', dtype=torch.float32)`，并断言模型、VAE、CLIP 和 Surfel 模型参数均为 CPU FP32；
- 隔离版 `do_sample` 只允许 CPU 或 CUDA，CPU 下 autocast disabled；
- S40 full archive 保存了 Torch CPU RNG state，足以恢复 sampler 的所有已知随机 draw；
- A0R 必须保留 S40 的线程数、Torch/NumPy/依赖版本与 model/VAE hashes，不能为了通过 replay 临时改成单线程或 deterministic algorithm 模式。

### MPS

**MPS 对 exact replay 是 BLOCKED / OUT OF SCOPE**：

- 当前 S40 runtime 明确拒绝非 CPU FP32 参数；
- 隔离版 `do_sample` 明确只接受 CPU/CUDA；
- S40 trace 创建时没有请求 `rng_devices=('mps',)`，因此 factual A0 没有 MPS sampler-entry state；
- 即使把 tensor 搬到 MPS，跨后端数值也不能与 CPU A0 作逐字节 exact replay。

将来若为速度准备 MPS，必须另立具名 backend 变体、保存 MPS RNG、重新做组件/算子兼容与自己的 A0/A0R 门；它不能替代本次 CPU 因果对照，也不能与 CPU 差异解释为 CLIP 作用。

## 9. 失败与部分产物怎样保存

源实现应复用 S40 的外层监督思想，但使用新的独占目录和 schema：

- parent 在科学 import 前核 manifest、bundle、源文件、权重、S40 readback 与 case-freeze SHA；
- fresh worker 只加载一次 runtime，按 `A0R → gate → A1` 执行；不得自动重试、换后端、换线程、降分辨率或重新生成 bundle；
- parent 继续轮询进程树 RSS、总时限、磁盘和子进程，超限时 TERM/KILL 整个进程组；
- worker 在每臂开始前先落 `input_manifest`、数组描述符、RNG 边界与状态 `STARTED`，成功后追加 output SHA 和 counters；
- Python 异常保存原异常类型、消息、traceback、当前 phase、最后完整事件、RNG/cache 指纹和已写文件清单；
- hard kill/disk failure 允许保留 hash-chain prefix 和外控 termination receipt，不能把 prefix 写成 COMPLETE；
- A0R mismatch 保存两侧 tensor 描述符、首个不同比特/最大差异的诊断，但不启动 A1；
- A1 failure 保存为 `FAILED_OR_PARTIAL_A1`，A0/A0R 原件不删除；
- 每份输出使用 exclusive create 与最终 inventory/hash，绝不覆盖 S40 archive 或上一臂。

不应把 activation 全量保存为默认要求；最小证据是 sampler 输入、sampler 输出、decoded tensor、RNG 边界、调用计数、cache/map 前后指纹和失败前缀。这样控制磁盘，同时足以判断介入边界。

## 10. 实现前必须补齐的源码件

现有文件足以开始编写，但以下都尚未实现或执行：

1. **bundle freezer/readback**：只从通过的 S40 full archive 选择一个已冻结 batch，类型保真恢复 RNG，并生成 source-bound immutable manifest；
2. **direct sampler runner**：绕开 `do_sample` 的初始随机 noise、禁止检索/编码/cache 更新、逐臂重置 RNG 和 clone tensors；
3. **H1 external supervisor/archive**：fresh worker、CPU/RSS/time/disk 门、partial failure 保存和不可覆写 inventory；
4. **exact replay verifier**：A0↔A0R inputs/outputs/RNG/cache 的逐字节核验，失败时强制阻断 A1；
5. **独立源审与冻结批准**：先审 AST/call graph、唯一 delta、数组来源和失败路径，再绑定实际 S40 bundle core；
6. **执行前外部事实**：S39/S40 真实链成功、S40 readback PASS、有效自然失败及 case/metric/camera gate 已冻结。

其中 1–5 是下一阶段可自主完成的 source preparation；第 6 项当前仍是执行阻塞条件。不得用人工数组或 synthetic fixture 冒充未来 A0 bundle，也不为“测试插桩”提前运行模型。

## 11. 最终裁决

**READY_FOR_SOURCE_PREPARATION**，限定 CPU/FP32。

理由是：S40 已设计并独立审过 full archive 和 readback 链，能够保存实际 sampler-entry noise、全部 c/uc 条件、camera/K/mask、cache provenance、samples/samples_z 与 CPU RNG；VMem sampler 可以在不调用检索、条件重建和 cache 更新的情况下直接重放；源码也明确了 A1 只改变 conditional crossattn 的干净边界。

**尚不可执行科学实验。** 当前缺实际 S40 PASS bundle、冻结自然失败/camera gate、replay 生产源码及独立审查。MPS 不属于本 exact replay 方案。即使未来 A0R/A1 完成，H1 通过也只是消费者通路影响诊断，不是 mean 有害、新方法有效或 PhD/CCF A 创新证据。

## 12. 绑定的只读证据

- `work/S20_environment/isolated_vmem_source/modeling/pipeline.py` — `680da1c14db8a6780a37fca3a8bac5bb59f0aa7d395db96d4360b352eb7f2255`
- `work/S20_environment/isolated_vmem_source/modeling/modules/conditioner.py` — `b79eb0cf4d94345a720a9a844c7daa6206b0a9234d714b7f9f23a9571c7c5fc1`
- `work/S20_environment/isolated_vmem_source/modeling/network.py` — `9ed21c2d804734d7ca2d81b1e596858835ca70a4a04abb9b5540b872515d4c9b`
- `work/S20_environment/isolated_vmem_source/modeling/sampling.py` — `dc07ca0ba571ba5fb48f9856515d2cb7dea25254008a6f8b315538817f352b24`
- `work/S20_environment/isolated_vmem_source/utils/util.py` — `30a97451f7a895e99ab881e97249f564e6b97eca2b5ea4d8f83953c26c4cf65e`
- `work/S35_generation_integration/launch_original.py` — `8744cb8959cded2394c1471c660dd84f929b5ae24ac97e81379304aed0be702e`
- `work/S35_generation_integration/runtime_factory.py` — `a7f812717c053b401433bac423ba0a63028a9dc1874b1cba3c4fbca6c276e3d0`
- `work/S35_generation_integration/integrate_original.py` — `adf819e1cda3de4f830d2c3e5776664591607a0109d50f59cdc1addeb684b0ec`
- `work/S35_generation_integration/archive_outputs.py` — `eaee634f055d39a68fcad352de2b6365ce5b529b5b2e62789aa7a56204497486`
- `src/s20_generation_trace.py` — `daf841dbcb635417865ba8287ad305bbdf6105181fd39e169be2e666e1bfbc57`
- `work/S40_declared_variant_generation/launch_generation.py` — `8ade694bc750f9693fc461257437af7b919b0c46755fc0eef2e21096d31e8860`
- `work/S40_declared_variant_generation/runtime_adapter.py` — `d26f7e8990fd218273361c04484c8c0ea499a693486fd7bb040e3b03306a79c4`
- `work/S40_declared_variant_generation/PROTOCOL_DRAFT.md` — `2c026b3dff79ca9155e5ad86a8c539b6597b6be7ed73b2c407b3d83ce75d7ced`
- `work/S40_result_readback/readback.py` — `4c7a4208c4a67b003bae7b5574b48ce44d6034797bf2e9c5ab021e4d04e4cbf6`
- `work/S41_gemini_adversarial_review/primary_retrieval_and_root_review.md` — `fd07dfc743f9a0c3f350f5d719936b74d5d902f3f10910c1a0b30b8ecda4059a`
- `work/S41_gemini_adversarial_review/root_review_incremental_v3.json` — `71c45f94280be496e8ae4450ad4569bbf8c5788a072ee3054865465eddc1d198`

