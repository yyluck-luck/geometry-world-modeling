# Round 15-G：condition 5 的低成本路线审查（2026-09-19）

本文件是可行性与证据边界审查。按本轮要求，我没有运行模型、下载权重或启动 GEN3C 服务；也没有修改任何已有文件。仓库内的源码、既有回执和公开来源逐项核对后，下面把“已经测到的事实”“静态可达性”和“尚未测量的设计”分开。

## 先给结论

**按项目原来的严格定义，condition 5 仍不能用零 GPU 完成：它要求在冻结权重下测到行为后果。** GEN3C 的无权重 stub 可以测到服务器层的状态不一致与请求准入，但它没有冻结的生成权重；因此严格说它是一个新的、较窄的“released server-contract consequence”证据，而不是冻结模型的外部效度证据。

同时，GEN3C 确实有一个不需要改 released source 的测试 seam。可以在 released `CosmosBaseModel` 上挂一个很小的 inner stub，执行“第一次 seed 成功 → 第二次 seed 在清 cache 后失败 → 外层仍放行 inference”的控制流。这个测试的 GPU-hours 是 **0**，证据强度是“服务器 wrapper/API 层的可复现行为”，不是图片质量或网络数值。项目当前只有静态审查，尚未执行这个 stub，所以这一项现在仍应标为 **UNMEASURED**。

VMem 的“retrieval-set-differs”路线已经有真实冻结组件/权重的离散输出证据：既有 zero-diffusion census 在 14 个成功窗口中发现 8 个 CONTENT、4 个 PERMUTATION、2 个 NULL；也就是 12/14 个窗口的 padded retrieval IDs 发生变化，slot 0 在 14/14 个窗口相同。这可以支持一个明确限定的 condition 5：**selector 输出改变**。它不能单独支持“生成帧改变”或跨场景外部效度；后一个较强结论由已有真实生成结果 `clean − leaked = +0.245 dB`（14 窗口、两 seed，6/14 正向）支持。复用已封存 census 不增加 GPU-hours；从 JSON 读回是审计既有证据，不能称为重新执行了 selector。

因此，最小可审证据包可以是“GEN3C wrapper-state consequence + VMem selector-output consequence”，总新增 GPU-hours 为 **0**；但要把两者写成同一层面的“冻结模型行为”，审稿人很可能拒绝。若主张必须是两个 released generator 都在真实权重下产生了 downstream consequence，则至少需要一次真实 GPU 运行；GEN3C 公开资料没有给出可诚实换算的运行时，不能编一个 GPU-hour 数字。

## 1. 已核对的代码事实

### VMem

上游仓库是 [runjiali-rl/vmem](https://github.com/runjiali-rl/vmem)，核对的 public commit 是 `39291e4f272f6b4f270691d930926ab5930f942e`。项目中的三份副本

- `work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py`
- `work/S17_cpu_preflight/original/modeling/pipeline.py`
- `work/S102_gate0_3dmatch/adapter_v1/sources/vmem_pipeline.py`

SHA-256 都是 `90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e`，`cmp` 为逐字节相同。上游文件的可定位链接是 [pipeline.py@39291e4f](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/modeling/pipeline.py)。

核对结果：

- `pipeline.py:1249` 调用 `get_context_info(target_c2ws, use_non_maximum_suppression)`。
- `:1263` 执行 `torch.cat([context_c2ws, target_c2ws])`。
- `:1265` 执行 `get_translation_scaling_factor(all_c2ws)`。
- `:180` 在 `initialize` 中执行 `self.c2ws = [c2w]`；`:1297` 在生成帧回写时执行 `self.c2ws.append(...)`。没有 setter/property setter，也没有第三个 assignment/append 写点。严格记录一个容易被口语掩盖的细节：`:1360` 的 `self.c2ws.pop()` 是 `undo` 的删除性 mutation，不是新的写入来源。
- `:674` 定义 `is_second_step = len(self.pil_frames) == 5`。NMS 开启时，`:682-700` 只有在这个五帧条件下才赋 `initial_threshold`；NMS 关闭时 `:704-705` 无条件写 `1e8`；随后 `:707-708` 无条件读取。项目报告已经核对 `reset()` 不清理 `initial_threshold`（[TECHNICAL_REPORT_20260918.md:125-129](../../docs/report/TECHNICAL_REPORT_20260918.md#L125-L129)）。

所以原 HIT 的 static diagnosis 是成立的；它本身还不是 condition 5。

### GEN3C

上游仓库是 [nv-tlabs/GEN3C](https://github.com/nv-tlabs/GEN3C)，核对的 commit 是 `db2ffe12ced12ddafcec5e0422ee46ce8520746b`。下面所有 GEN3C 行号都指向这个 commit：

- [`gui/api/server.py:43-91`](https://github.com/nv-tlabs/GEN3C/blob/db2ffe12ced12ddafcec5e0422ee46ce8520746b/gui/api/server.py#L43-L91) 从环境变量建立 `ServerSettings`；`:77-84` 只在 debug 或 `cosmos/cosmos-predict1` 间选择内置 class；`:87-91` 实例化它。
- [`gui/api/server_base.py:30-60`](https://github.com/nv-tlabs/GEN3C/blob/db2ffe12ced12ddafcec5e0422ee46ce8520746b/gui/api/server_base.py#L30-L60) 的 `InferenceModel` 创建外层 `self.model_seeded = False`；`:121-131` 的 `request_inference` 只检查这个外层 flag，然后建立 task。
- [`gui/api/server_cosmos_base.py:32-71`](https://github.com/nv-tlabs/GEN3C/blob/db2ffe12ced12ddafcec5e0422ee46ce8520746b/gui/api/server_cosmos_base.py#L32-L71) 的 `CosmosBaseModel.seed_model` 每次 seed 都执行 `:53` `self.model.clear_cache()`，再通过 `:57-70` 调 inner `seed_model_from_values`，只有调用返回后才在 `:71` 把外层 `self.model_seeded` 设为 true。注意 `:51-52` 的 `if self.pose_history_w2c` 只包住日志；cache clear 与两个 history clear 仍在 `:53-55` 无条件发生。
- [`cosmos_predict1/diffusion/inference/gen3c_persistent.py:130-134`](https://github.com/nv-tlabs/GEN3C/blob/db2ffe12ced12ddafcec5e0422ee46ce8520746b/cosmos_predict1/diffusion/inference/gen3c_persistent.py#L130-L134) 初始化 inner `cache=None` 和 `model_was_seeded=False`。`:206-210` 对多帧 seed 在缺少 depth 或 mask 时抛 `NotImplementedError`；这是 `n>1` 的分支，不能误写成所有 seed 都无条件抛错。`:292-312` 的 inference 随后调用 `self.cache.render_cache(...)`。`:551-554` 的 `clear_cache` 把 `cache` 设为 None，并把 `model_was_seeded` 设为 false。
- 重要更正：在这个 commit 中，`model_was_seeded` 只有初始化和 clear 的写入，源码内没有看到把它设为 true 或读取它作 gate。真正可观测的不一致是“outer `InferenceModel.model_seeded=True`，inner `cache=None`”；inner flag 是生命周期线索，不是实际 admission guard。
- [`gui/api/server.py:123-176`](https://github.com/nv-tlabs/GEN3C/blob/db2ffe12ced12ddafcec5e0422ee46ce8520746b/gui/api/server.py#L123-L176) 的 `/request-inference` 与 `/seed-model` 分别调用外层方法；seed 异常被捕获为 HTTP 400，inference 只要外层 flag 为 true 就走 `:141`，成功排队后返回 202。
- [`gui/api/server_cosmos.py:49-96`](https://github.com/nv-tlabs/GEN3C/blob/db2ffe12ced12ddafcec5e0422ee46ce8520746b/gui/api/server_cosmos.py#L49-L96) 才会在普通 `CosmosModel` 路径中导入/构造真实 `Gen3cPersistentModel` 或多 GPU adapter。

## 2. GEN3C 的注入 seam：能否不改 released source？

答案分三层。

**第一层：released debug seam 存在，但不能复现这个 HIT。** `server.py:77-80` 在 `GEN3C_API_DEBUG=1` 时选 `DebugInferenceModel`。[`gui/api/server_debug.py:22-55`](https://github.com/nv-tlabs/GEN3C/blob/db2ffe12ced12ddafcec5e0422ee46ce8520746b/gui/api/server_debug.py#L22-L55) 明确写成无 checkpoint、无 CUDA 的 deterministic in-memory model；GUI README 的 [lines 38-45](https://github.com/nv-tlabs/GEN3C/blob/db2ffe12ced12ddafcec5e0422ee46ce8520746b/gui/README.md#L38-L45) 也明确给出 `GEN3C_API_DEBUG=1 python ./api/debug_api_check.py`。但这个 Debug class 直接继承 `InferenceModel`、在 `:30` 把外层 flag 设为 true，`:49-55` 的 seed 只设置外层 flag，没有 `clear_cache`、`model_was_seeded` 或 3D cache。因此 API_DEBUG 能验证 HTTP 序列化和通用 request/response，不能验证 Cosmos cache HIT。

**第二层：wrapper-level stub 可以不改 source。** `CosmosBaseModel` 没有在自己的 `__init__` 中构造 inner model（只调用父类）；真实 `CosmosModel` 才在 `server_cosmos.py:66-96` 绑定 `self.model`。因此测试 harness 可以导入 released modules，构造 `CosmosBaseModel`（`InferenceModel` 虽用了 `@abstractmethod` 标记，但 class 本身没有继承 `ABC`，Python 不会阻止这种构造），给它设置 `pose_history_w2c=[]`、`intrinsics_history=[]` 和一个 stub 的 `model` 属性，然后调用 released 的 `CosmosBaseModel.seed_model` 和 `InferenceModel.request_inference`。stub 只需实现：

1. `clear_cache()`：把自己的 `cache` 置为 None；
2. `seed_model_from_values(...)`：第一次返回一个合法的最小 seed result，第二次抛出一个受控 exception；
3. 为 admission 检查提供 `frames_per_batch`；若要让失败 task 继续走到真实 cache seam，再提供 `inference_on_cameras`，在 `cache is None` 时抛出或记录；
4. 测试数据是小 NumPy 数组，不需 torch 权重。

建议的未执行断言是：

`seed A success` → outer `model_seeded=True`；

`seed B`（至少两帧，depth/mask 缺失）→ `clear_cache` 已发生、seed exception 传播、外层 flag 仍为 true；

随后调用 released `request_inference` → 返回 asyncio task（即“admitted”），同时 stub 的 cache 仍为 None。若让 task 运行，预期在 `render_cache` 对应 seam 失败；也可以取消 task，只测 admission，避免把 stub 的后续细节误当成生成结果。

**第三层：HTTP route integration 需要 test-time 注入，不是生产 config。** `server.py:70-71` 的 `model` 是 module-global，route 在 `:137-141`、`:168` 动态读它。harness 可以先用官方 `GEN3C_API_DEBUG=1` 启动 TestClient，再在测试时把 `server.model` 替换为 wrapper+stub，POST released serialization：seed A、seed B、inference；预期 seed B 为 400，后一个 inference 为 202。这样不改 released source，但这是 test-time global mutation。普通 factory 没有 arbitrary class path/plugin：若坚持“未经 harness 变更、直接由公开配置选择自定义 stub”，答案是 **否**，需要 monkeypatch/module substitution 或给 factory 加 patch。这个差别应在报告中写清楚。

## 3. 这个 stub 证明什么，不证明什么？

它可以证明：

- 在固定 commit 的 released wrapper 中，清 cache 与设置 outer admission flag 之间存在非原子的顺序；
- 一个失败的多帧 seed 可以发生在 outer flag 写入之前，但发生在 inner cache 已清空之后；
- released admission gate 只看 outer flag，所以请求可以在“inner resource 已清空”的状态下被接受；
- 这个结论是可重复的 CPU control-flow 事实，和 diffusion 网络输出无关。

它不能证明：

- GEN3C 的真实 CUDA `Gen3cPersistentModel` 在所有真实输入上会产生同样的 downstream exception；
- 任何视频像素、PSNR、感知质量、3D 一致性或 camera control 变化；
- 真实模型权重下的外部效度；
- `model_was_seeded` 是一个实际 gate（本 commit 的源码检查反而显示它不是）。

因此结果标签应是 `GEN3C_SERVER_STATE_ADMISSION_STUB`，而不是 `GEN3C_GENERATION_BEHAVIOUR`。

## 4. 审稿人会接受 stub 当 condition 5 吗？

有公开的 software-systems precedent，但它支持的是较窄的 claim。

- Schmitz et al., **“Model-based fault injection for testing gray-box systems”**, *The Journal of Logical and Algebraic Methods in Programming* 103 (2019) 31–45, DOI [10.1016/j.jlamp.2018.10.003](https://doi.org/10.1016/j.jlamp.2018.10.003), accepted PDF [exact URL](https://hh.diva-portal.org/smash/get/diva2:1266512/FULLTEXT01.pdf)。论文明确用 mocking 把带故障的 executable model 作为组件替换到 larger SUT；SUT 在该故障行为下失败就是 top-level failure witness，而真实组件实现甚至可以不可用。这个先例直接支持“有精确 interface、故障模型和 witness 的 wrapper-level consequence”。
- Meiklejohn et al., **“Service-Level Fault Injection Testing”**, *ACM Symposium on Cloud Computing (SoCC ’21)* (2021), DOI [10.1145/3472883.3487005](https://doi.org/10.1145/3472883.3487005), [作者 PDF](https://christophermeiklejohn.com/publications/filibuster-socc-2021.pdf)。FILIBUSTER 在本地测试中注入远程服务 failure，并在不做 live-production chaos 的情况下找出真实 bug；它证明的是服务边界的 resilience/control-flow consequence，不是被替换服务的业务输出质量。
- Marinescu & Candea, **“Efficient Testing of Recovery Code Using Fault Injection”**, *ACM Transactions on Computer Systems* 29(4) (2011), DOI [10.1145/2063509.2063511](https://doi.org/10.1145/2063509.2063511)。它把 fault injection 放在 application/library boundary，测试 recovery code，说明边界替换可以是严肃的系统行为测量。

所以：

- 做 server/runtime/robustness 评审时，stub 证据可以被接受为“released wrapper admits an inconsistent state”，尤其是还提供 clean-control（失败 seed 后 outer flag 被清零、请求返回 400）。
- 做 world-model/ML condition 5 评审时，若把它写成“GEN3C 的生成行为已被实验证明”，大概率会被拒绝为“只跑了代码路径”。必须把 claim 限定到 server contract，并把 VMem selector 证据和 GEN3C wrapper 证据分层。

## 5. VMem：不生成 pixels 的 retrieval-set 路线

项目报告 [TECHNICAL_REPORT_20260918.md:186-189](../../docs/report/TECHNICAL_REPORT_20260918.md#L186-L189) 和 [LEAK_REGIME_CENSUS.json](../../docs/report/bundle/LEAK_REGIME_CENSUS.json) 给出：

- 16 个 panel attempts 中 14 个成功，scene_13/scene_14 的 window 0 各有一个 `IndexError`，不是静默当作分数；
- 成功的 14 个窗口：NULL=2、PERMUTATION=4、CONTENT=8；
- `raw/padded retrieval IDs`、threshold、`c2ws` 等离散输出被保存；12/14 的 padded context IDs 改变，2/14 不变；
- slot 0 在 14/14 相同，因为 `pipeline.py:710-711` 先加入 `sorted_frames[0]`，不经过 threshold；
- JSON 的 `reads_ground_truth=false`，zero diffusion，没有 target decode。因而它是 selector/intermediate evidence，不是图像质量 evidence。

这里有一个容易丢失的 provenance 边界：这个 census 当时是 **真实冻结权重 + CUDA retrieval measurement**，脚本 `work/S103_selector_free_baseline/leak_regime_census.py:93-96,107-149,206-225` 使用 `device='cuda'`，只是跳过 diffusion。现在在 CPU 上读取封存 JSON 可以复查 ID 关系，但不能说 CPU 重新执行了 `get_context_info`；JSON 没有完整 candidate feature/surfel-distance 输入，不能从零重建 selector。

因此对 Q2 的回答是：

- **可以满足一个窄定义的 VMem condition 5：retrieval policy output differs。** 最好预先把 outcome 写成 ordered/padded frame IDs、multiset/order 分层和 threshold provenance。
- **不能以此声称生成帧不同。** 这一 stronger claim 需要 frozen generator。项目已有 14-window、two-seed 的真实 panel，报告记录 `memory_nms_on_clean − memory_nms_on (leaked) = +0.245 dB`，SD 0.711，6/14 正向（[TECHNICAL_REPORT_20260918.md:202-224](../../docs/report/TECHNICAL_REPORT_20260918.md#L202-L224)）。那是 downstream pixel evidence，但 panel 是 exposed finite case study，不是 held-out generalization。
- “retrieval set differs” 对 selector/mechanism paper 可以算行为后果；对 end-to-end generative-model paper，多数 reviewer 会把它称为 intermediate output，要求至少一个 pixel/latent/consumer witness。最安全写法是“两种 consequence types：GEN3C server admission；VMem selector output”，不要把它们包装成同一强度的 generator-quality result。

## 6. 小 checkpoint、许可和 CPU 路线

### VMem

没有查到 released small/distilled VMem video variant。作者 README 只有一个 `liguang0115/vmem` model-card route，并要求 Hugging Face 登录/填写访问信息（[README@39291e4f lines 42-57](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/README.md#L42-L57)）。项目盘点的已知文件是：

- `vmem_weights.pth`: 5,056,346,672 B（4.709 GiB）；
- 指定 CUT3R 512 DPT: 3,173,761,006 B（2.956 GiB）；
- OpenCLIP ViT-H: 3,944,517,836 B（约 3.67 GiB）；
- VAE 大小/身份当时仍不确定。

已知文件在没有 VAE 前约 11.34 GiB；磁盘大小不是 VRAM。报告 [S17_FULL_VIDEO_BASELINE_FEASIBILITY.md:47-57](../../docs/S17_FULL_VIDEO_BASELINE_FEASIBILITY.md#L47-L57) 还核对了 576×576、T=8、50 steps 和 attention 中间量风险。项目已有 H800 **无数据模型加载**回执峰值 7.884 GB，但这不是完整 forward 的 VRAM 预算。

代码仓库的 `LICENSE` 是 **MIT**；权重 model-card 的使用/许可条件不能从公开 README 确认，且 access 是 gated。没有证据可以把 `cut3r_224_linear_4.pth` 叫作 VMem small variant；它是不同模型 head。结论：不能诚实承诺 8–12 GB consumer GPU，也没有公开 distilled route 可把 condition 5 变成便宜实验。

### GEN3C

公开 release 给出的模型是 **GEN3C-Cosmos-7B**（[README@db2ffe12 lines 56-69](https://github.com/nv-tlabs/GEN3C/blob/db2ffe12ced12ddafcec5e0422ee46ce8520746b/README.md#L56-L69)），没有另一个 released small/distilled video checkpoint。README 的单 GPU 示例是 121-frame generation（`:84-95`），完整 offloading 的最大观测显存约 **43 GB**（`:142-155`）；因此普通 24 GB consumer card 没有被 release 证据支持，48 GB 级别才是“可能”而非已验证。源码是 Apache-2.0，模型是 NVIDIA Open Model License（`:274-281`）。README 没有给出可用于预算的单序列 wall-clock；不能从“7B”自行推导 GPU-hours。README 提到的 Lyra static/dynamic 3DGS decoder 是另一项发布物，不是 GEN3C 的小视频 checkpoint。

### CPU-only inference

- **GEN3C real model：不具备可接受的 unmodified CPU route。** wrapper 的 `CosmosBaseModel.run_inference` 在 `server_cosmos_base.py:159-162` 无条件创建 `torch.cuda.Event`；真实 `Gen3cPersistentModel` 还依赖 CUDA/Cosmos/MoGe。CPU stub 可以测 wrapper admission，不能测 real inference。没有真实 CPU runtime 可报告。
- **VMem：原 released source 也不是“代码有 device 参数就等于支持 CPU”。** [S17 feasibility report lines 34-45](../../docs/S17_FULL_VIDEO_BASELINE_FEASIBILITY.md#L34-L45) 指出原 `do_sample`/attention 有 CUDA/FLASH 绑定；要做 CPU 需要经过审查的 device/backend adaptation，属于 source variant。历史上该项目的声明 `ft-mse` VAE 变体在 CPU FP32/8 threads、576²、50 steps 的单条 50-step chain 记录为 1469.889 s（约 24.5 min；[S76_RELATIVE_CAMERA_RESPONSE_RESULT.md:5](../../docs/S76_RELATIVE_CAMERA_RESPONSE_RESULT.md#L5)），S70 的三臂原始 elapsed 为 4439.1515 s（每臂约 24.6 min；`work/S70_fixed_context_generation/generation_verification_01/receipt.json:1983`）。这些是组件变体/固定 context 的真实测量，不是本轮 exact original interactive retrieval 的保证。把一个 window 的 clean/leaked、两 seed 共四条生成粗略规划为 2–4 wall-clock hours 是预算估计，不是已测结果；完整 scene rebuild/400-step alignment 可能更慢，不能预先承诺。

## 7. 最小证据包与成本

### E1：零 GPU、GEN3C wrapper consequence（推荐的最小新实验）

只用 released commit `db2ffe12...` 的 `CosmosBaseModel`/父类和一个 test-time stub，不改 source：

1. 记录源 SHA、stub interface 和预期状态转移；
2. seed A 成功，确认 outer flag=true；
3. seed B 使用至少两帧并省略 depth/mask，使 released inner seam 抛错；确认 cache 已先清空、seed API 的 400；
4. inference 立即提交；确认 outer gate 接受 task/HTTP 202，同时 inner cache=None；
5. clean-control：让失败路径显式清外层 flag，随后 inference 必须被拒绝（400），以证明不是“任何失败都能排队”。

保存 stdout/exception type、outer/inner state before-after、HTTP status（若做 route tier）、source/stub hashes。不要把 stub 产生的 debug image 当作生成质量。

**成本：** 0 GPU-hours；stub 负载是小 NumPy/asyncio，计划上是秒到分钟、少于 1 wall-clock day，但本轮没有执行，所以不写实测耗时。E1 成功后可把 GEN3C 的窄条件标为 `MEASURED_SERVER_CONTRACT_CONSEQUENCE`，同时保留 `frozen_weight_generation_consequence=UNMEASURED`。

### E2：零新增 GPU、VMem selector witness

不重新跑模型，封存并引用已有：

- source commit/SHA 和三副本 byte identity；
- 14/16 census accounting、2 errors、12/14 ID differences、NULL/PERMUTATION/CONTENT counts；
- ordered padded IDs、threshold=primed percentile vs leaked (1e8)、slot0 invariant；
- zero-diffusion/no-GT/no-target-decode scope；
- existing downstream +0.245 dB table as a separate stronger but exposed finite-panel result.

**成本：** 新 GPU-hours=0；JSON readback 的 wall time 可以是分钟级，但它是 archival audit，不是 new selector run。

### E3：若 reviewer 坚持两个真实 generator 都要 frozen-weight downstream consequence

- VMem：本项目已有真实 frozen generator panel，因此新增 GPU-hours=0；若 reviewer 要求新鲜重测，最低是一个窄窗口的 clean/leaked paired run，至少两个 seed，四个 forwards，再加 deterministic/order control。项目没有在本轮核出这一组新鲜 H800 wall-time，所以不报伪造的 GPU-hour。
- GEN3C：需要真实 `CosmosModel`/persistent cache 和至少一次正常 seed + 一次失败 seed + inference attempt；README 只证明 43 GB 级显存需求和单 GPU 命令，不提供 runtime。最低是一个符合 48 GB 级别条件的 GPU allocation；**精确 GPU-hours 在已核对证据中是 UNKNOWN**。若只观察真实 cache failure 而不生成视频，仍应写成 runtime fault consequence；若要 image/quality，需要完整有效 seed 和真实 frame generation。
- CPU fallback 不能替代 E3：VMem 的 CPU 历史数值属于 declared component variant，GEN3C unmodified CPU route 不成立。

### Q4 的直白回答

若 condition 5 继续坚持“冻结权重下的 downstream behavior”，答案是：**不能在零 GPU 下完成一个跨系统、同强度的 condition 5。** 最便宜的真实 VMem 像素证据项目已经有，新增 GPU-hours 为 0；若从头做，当前证据只足以给出上述四-forward/窗口设计，不能给出确切 GPU-hours。GEN3C 的真实冻结权重最低需要一次可装下约 43 GB 的 GPU 运行，公开资料没有 runtime，故最低 GPU-hours 不能诚实量化。若接受“server-contract consequence”这一窄定义，则 GEN3C E1 的最低成本回到 0 GPU-hours。

## 8. 来源清单（精确标题、版本与 URL）

### 论文

1. Runjia Li, Philip Torr, Andrea Vedaldi, Tomas Jakab, **“VMem: Consistent Interactive Video Scene Generation with Surfel-Indexed View Memory”**, arXiv:2506.18903, [https://arxiv.org/abs/2506.18903](https://arxiv.org/abs/2506.18903).
2. Xuanchi Ren et al., **“GEN3C: 3D-Informed World-Consistent Video Generation with Precise Camera Control”**, arXiv:2503.03751, [https://arxiv.org/abs/2503.03751](https://arxiv.org/abs/2503.03751).
3. Wojciech Mostowski et al., **“Model-based fault injection for testing gray-box systems”**, DOI:10.1016/j.jlamp.2018.10.003, [https://doi.org/10.1016/j.jlamp.2018.10.003](https://doi.org/10.1016/j.jlamp.2018.10.003), accepted PDF [https://hh.diva-portal.org/smash/get/diva2:1266512/FULLTEXT01.pdf](https://hh.diva-portal.org/smash/get/diva2:1266512/FULLTEXT01.pdf).
4. Paul D. Marinescu and George Candea, **“Efficient Testing of Recovery Code Using Fault Injection”**, DOI:10.1145/2063509.2063511, [https://doi.org/10.1145/2063509.2063511](https://doi.org/10.1145/2063509.2063511).
5. Christopher S. Meiklejohn et al., **“Service-Level Fault Injection Testing”**, SoCC ’21, DOI:10.1145/3472883.3487005, [https://doi.org/10.1145/3472883.3487005](https://doi.org/10.1145/3472883.3487005), [https://christophermeiklejohn.com/publications/filibuster-socc-2021.pdf](https://christophermeiklejohn.com/publications/filibuster-socc-2021.pdf).

### 代码与项目证据

- VMem upstream commit [39291e4f272f6b4f270691d930926ab5930f942e](https://github.com/runjiali-rl/vmem/tree/39291e4f272f6b4f270691d930926ab5930f942e); `modeling/pipeline.py` lines 180, 674-708, 1249, 1263-1265, 1297, 1360; repository `LICENSE` (MIT) and `README.md` lines 42-57.
- GEN3C commit [db2ffe12ced12ddafcec5e0422ee46ce8520746b](https://github.com/nv-tlabs/GEN3C/tree/db2ffe12ced12ddafcec5e0422ee46ce8520746b); `gui/api/server.py`, `server_base.py`, `server_cosmos_base.py`, `server_cosmos.py`, `server_debug.py`, `gui/README.md`, and `cosmos_predict1/diffusion/inference/gen3c_persistent.py` at the line ranges linked above. `README.md:56-69,84-95,142-155,274-281` gives the 7B checkpoint, single-GPU command, 43 GB full-offload observation, Apache-2.0 source license and NVIDIA Open Model License.
- Local VMem result report: `docs/report/TECHNICAL_REPORT_20260918.md:186-189,202-224,254-275`.
- Local census artifact: `docs/report/bundle/LEAK_REGIME_CENSUS.json:1-42`.
- Local feasibility and runtime evidence: `docs/S17_FULL_VIDEO_BASELINE_FEASIBILITY.md:15-20,34-57`; `docs/S76_RELATIVE_CAMERA_RESPONSE_RESULT.md:5-7`; `work/S70_fixed_context_generation/PROTOCOL.md:13-27`; `work/S70_fixed_context_generation/generation_verification_01/receipt.json:1769-1984`.

No claim in this file upgrades `new_method_validated=false` or `novelty_authorization=NONE`.

